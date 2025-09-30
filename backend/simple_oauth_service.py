#!/usr/bin/env python3
"""
Simple OAuth Google Drive service that handles the flow properly
"""

import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.auth.transport.requests import Request
from typing import Optional, Dict, Any
import io

class SimpleOAuthGoogleDriveService:
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
        """Authenticate using OAuth"""
        try:
            print("[AUTH] Starting OAuth authentication...")
            
            # Get credentials from environment variable
            oauth_credentials = os.getenv('GOOGLE_OAUTH_CREDENTIALS')
            if not oauth_credentials:
                print("[ERROR] GOOGLE_OAUTH_CREDENTIALS environment variable not set")
                self.service = None
                return
            
            # Load existing token if available
            token_file = 'backend/token.json'
            creds = None
            if os.path.exists(token_file):
                print("[AUTH] Loading existing token...")
                creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
            else:
                # Try to load from environment variable
                token_env = os.getenv('GOOGLE_OAUTH_TOKEN')
                if token_env:
                    print("[AUTH] Loading token from environment...")
                    token_data = json.loads(token_env)
                    creds = Credentials.from_authorized_user_info(token_data)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    print("[AUTH] Refreshing expired token...")
                    creds.refresh(Request())
                else:
                    print("[AUTH] Starting OAuth flow...")
                    credentials_info = json.loads(oauth_credentials)
                    flow = InstalledAppFlow.from_client_config(credentials_info, self.SCOPES)
                    
                    # Generate OAuth URL (InstalledAppFlow uses localhost:8080 by default)
                    auth_url, _ = flow.authorization_url(
                        prompt='consent'
                    )
                    print(f"[OAUTH] Complete OAuth by visiting: {auth_url}")
                    print("[OAUTH] After completing OAuth, restart the service")
                    
                    # For now, we can't complete the flow automatically
                    self.service = None
                    return
                
                # Save credentials
                if not os.path.exists('backend'):
                    os.makedirs('backend')
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('drive', 'v3', credentials=creds)
            print("[SUCCESS] OAuth authentication successful")
            
        except Exception as e:
            print(f"[ERROR] OAuth authentication failed: {e}")
            self.service = None

    def setup_folders(self):
        """Setup required folders in Google Drive"""
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
            file['image_url'] = file.get('webViewLink', '')
            
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
