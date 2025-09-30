#!/usr/bin/env python3
"""
Hybrid Google Drive service - OAuth for local, Service Account for production
"""

import os
import json
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.auth.transport.requests import Request
from typing import Optional, Dict, Any
import io

class HybridGoogleDriveService:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        self.service = None
        self.folders = {
            "certificates": None,
            "templates": None,
            "qr_codes": None
        }
        self.authenticate()
        self.setup_folders()

    def authenticate(self):
        """Authenticate using OAuth (local) or Service Account (production)"""
        # Check if we're in production (Render)
        if os.getenv('ENVIRONMENT') == 'production':
            self._authenticate_service_account()
        else:
            self._authenticate_oauth()

    def _authenticate_service_account(self):
        """Authenticate using service account (for production)"""
        try:
            # Try environment variable first
            service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if service_account_json:
                print("[AUTH] Using Service Account from environment...")
                service_account_info = json.loads(service_account_json)
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info, scopes=self.SCOPES)
                self.service = build('drive', 'v3', credentials=credentials)
                print("[SUCCESS] Service Account authentication successful")
                return
            
            # Try file
            service_account_paths = [
                'backend/service_account_key.json',
                'service_account_key.json'
            ]
            
            for path in service_account_paths:
                if os.path.exists(path):
                    print(f"[AUTH] Using Service Account from {path}...")
                    credentials = service_account.Credentials.from_service_account_file(
                        path, scopes=self.SCOPES)
                    self.service = build('drive', 'v3', credentials=credentials)
                    print("[SUCCESS] Service Account authentication successful")
                    return
            
            print("[ERROR] No service account credentials found")
            self.service = None
            
        except Exception as e:
            print(f"[ERROR] Service Account authentication failed: {e}")
            self.service = None

    def _authenticate_oauth(self):
        """Authenticate using OAuth (for local development and production)"""
        try:
            print("[AUTH] Using OAuth authentication...")
            creds = None
            token_file = 'token.json'
            
            # Check for existing token
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Try to get credentials from environment variable (for Render)
                    oauth_credentials = os.getenv('GOOGLE_OAUTH_CREDENTIALS')
                    if oauth_credentials:
                        print("[AUTH] Using OAuth credentials from environment...")
                        try:
                            credentials_info = json.loads(oauth_credentials)
                            flow = InstalledAppFlow.from_client_config(
                                credentials_info, self.SCOPES)
                            creds = flow.run_local_server(port=0)
                        except Exception as e:
                            print(f"[ERROR] Failed to use environment OAuth credentials: {e}")
                            print("[WARNING] OAuth requires user interaction - not suitable for production")
                            self.service = None
                            return
                    else:
                        # Try local credentials files
                        credentials_paths = ['credentials.json', 'backend/credentials.json']
                        credentials_found = False
                        
                        for cred_path in credentials_paths:
                            if os.path.exists(cred_path):
                                flow = InstalledAppFlow.from_client_secrets_file(
                                    cred_path, self.SCOPES)
                                creds = flow.run_local_server(port=0)
                                credentials_found = True
                                break
                        
                        if not credentials_found:
                            print("[ERROR] No OAuth credentials found")
                            print("[INFO] For production, use GOOGLE_OAUTH_CREDENTIALS environment variable")
                            self.service = None
                            return
                
                # Save token for future use
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('drive', 'v3', credentials=creds)
            print("[SUCCESS] OAuth authentication successful")
            
        except Exception as e:
            print(f"[ERROR] OAuth authentication failed: {e}")
            self.service = None

    def setup_folders(self):
        """Setup required folders"""
        if not self.service:
            print("[WARNING] Google Drive service not available, skipping folder setup")
            return
        
        try:
            self.folders["certificates"] = self.get_or_create_folder("certificates")
            self.folders["templates"] = self.get_or_create_folder("templates")
            self.folders["qr_codes"] = self.get_or_create_folder("qr_codes")
            
            print("[SUCCESS] Google Drive folders setup complete:")
            for folder_type, folder_id in self.folders.items():
                print(f"   {folder_type.title()}: {folder_id}")
                
        except Exception as e:
            print(f"[ERROR] Error setting up Google Drive folders: {e}")

    def get_or_create_folder(self, folder_name: str) -> str:
        """Get or create a folder in Google Drive"""
        try:
            # Search for existing folder
            query = f"name='{folder_name}' and 'root' in parents and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(
                q=query, 
                fields="files(id, name)"
            ).execute()
            items = results.get('files', [])
            
            if items:
                return items[0]['id']
            else:
                # Create new folder
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()
                return folder.get('id')
                
        except Exception as e:
            print(f"[ERROR] Error creating folder {folder_name}: {e}")
            return None

    def upload_file(self, file_path: str, file_name: str, folder_type: str = "certificates") -> Optional[Dict[str, Any]]:
        """Upload a file to Google Drive"""
        if not self.service:
            print("[ERROR] Google Drive service not available")
            return None
        
        try:
            # Get folder ID
            folder_id = self.folders.get(folder_type)
            if not folder_id:
                print(f"[ERROR] Folder not found for type: {folder_type}")
                return None
            
            # Upload file
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            media = MediaIoBaseUpload(file_path, mimetype='image/png')
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink, webContentLink'
            ).execute()
            
            # Make file publicly accessible
            self.service.permissions().create(
                fileId=file.get('id'),
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()
            
            # Add image_url field for compatibility
            file['image_url'] = file.get('webContentLink', file.get('webViewLink', ''))
            
            return file
            
        except Exception as e:
            print(f"[ERROR] Error uploading file {file_name}: {e}")
            return None

    def upload_from_bytes(self, file_bytes: bytes, file_name: str, folder_type: str = "certificates") -> Optional[Dict[str, Any]]:
        """Upload file from bytes to Google Drive"""
        if not self.service:
            print("[ERROR] Google Drive service not available")
            return None
        
        try:
            # Get folder ID
            folder_id = self.folders.get(folder_type)
            if not folder_id:
                print(f"[ERROR] Folder not found for type: {folder_type}")
                return None
            
            # Upload file
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='image/png')
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink, webContentLink'
            ).execute()
            
            # Make file publicly accessible
            self.service.permissions().create(
                fileId=file.get('id'),
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()
            
            # Add image_url field for compatibility
            file['image_url'] = file.get('webContentLink', file.get('webViewLink', ''))
            
            return file
            
        except Exception as e:
            print(f"[ERROR] Error uploading file {file_name}: {e}")
            return None

    def delete_file(self, file_id: str) -> bool:
        """Delete a file from Google Drive"""
        if not self.service:
            print("[ERROR] Google Drive service not available")
            return False
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Error deleting file {file_id}: {e}")
            return False

    def get_folder_id(self, folder_type: str) -> Optional[str]:
        """Get folder ID based on type"""
        return self.folders.get(folder_type)
