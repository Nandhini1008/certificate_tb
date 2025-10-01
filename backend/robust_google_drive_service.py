#!/usr/bin/env python3
"""
Robust Google Drive service with proper token management and refresh logic
Fixes token expiry issues and eliminates repeated manual authentication
"""

import os
import json
import time
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.auth.transport.requests import Request
from typing import Optional, Dict, Any
import io

class RobustGoogleDriveService:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        self.service = None
        self.credentials = None
        self.folders = {
            "certificates": None,
            "templates": None,
            "qr_codes": None
        }
        self.token_file = 'token.json'
        self.credentials_file = 'credentials.json'
        self.authenticate()
        if self.service:
            self.setup_folders()

    def authenticate(self):
        """Robust authentication with proper token management"""
        try:
            print("[AUTH] Starting robust Google Drive authentication...")
            
            # Try multiple authentication methods in order of preference
            creds = None
            
            # Method 1: Try loading from environment variable (for Render)
            creds = self._load_from_environment()
            
            # Method 2: Try loading from token file
            if not creds:
                creds = self._load_from_token_file()
            
            # Method 3: Try refreshing existing token
            if creds and creds.expired and creds.refresh_token:
                print("[AUTH] Token expired, attempting refresh...")
                try:
                    creds.refresh(Request())
                    print("[AUTH] Token refreshed successfully")
                    # Save refreshed token
                    self._save_token(creds)
                except Exception as e:
                    print(f"[AUTH] Token refresh failed: {e}")
                    creds = None
            
            # Method 4: Try OAuth flow if no valid credentials
            if not creds or not creds.valid:
                print("[AUTH] No valid credentials found, attempting OAuth flow...")
                creds = self._perform_oauth_flow()
            
            if creds and creds.valid:
                self.credentials = creds
                self.service = build('drive', 'v3', credentials=creds)
                print("[SUCCESS] Google Drive authentication successful")
                
                # Save token for future use
                self._save_token(creds)
            else:
                print("[ERROR] All authentication methods failed")
                self.service = None
                
        except Exception as e:
            print(f"[ERROR] Authentication failed: {e}")
            self.service = None

    def _load_from_environment(self) -> Optional[Credentials]:
        """Load credentials from environment variables (for Render)"""
        try:
            # Try GOOGLE_OAUTH_TOKEN first (complete token)
            token_env = os.getenv('GOOGLE_OAUTH_TOKEN')
            if token_env:
                print("[AUTH] Loading token from GOOGLE_OAUTH_TOKEN environment variable...")
                token_data = json.loads(token_env)
                creds = Credentials.from_authorized_user_info(token_data, self.SCOPES)
                if creds and creds.valid:
                    print("[AUTH] Token from environment is valid")
                    return creds
                elif creds and creds.expired and creds.refresh_token:
                    print("[AUTH] Token from environment is expired but refreshable")
                    return creds
                else:
                    print("[AUTH] Token from environment is invalid")
                    return None
            
            # Try GOOGLE_OAUTH_CREDENTIALS (OAuth client config)
            oauth_credentials = os.getenv('GOOGLE_OAUTH_CREDENTIALS')
            if oauth_credentials:
                print("[AUTH] OAuth credentials found in environment")
                # This will be handled in OAuth flow
                return None
                
        except Exception as e:
            print(f"[AUTH] Error loading from environment: {e}")
        
        return None

    def _load_from_token_file(self) -> Optional[Credentials]:
        """Load credentials from token.json file"""
        try:
            if os.path.exists(self.token_file):
                print(f"[AUTH] Loading token from {self.token_file}...")
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
                if creds and creds.valid:
                    print("[AUTH] Token from file is valid")
                    return creds
                elif creds and creds.expired and creds.refresh_token:
                    print("[AUTH] Token from file is expired but refreshable")
                    return creds
                else:
                    print("[AUTH] Token from file is invalid")
                    return None
        except Exception as e:
            print(f"[AUTH] Error loading from token file: {e}")
        
        return None

    def _perform_oauth_flow(self) -> Optional[Credentials]:
        """Perform OAuth flow to get new credentials"""
        try:
            # Try environment OAuth credentials first
            oauth_credentials = os.getenv('GOOGLE_OAUTH_CREDENTIALS')
            if oauth_credentials:
                print("[AUTH] Using OAuth credentials from environment...")
                credentials_info = json.loads(oauth_credentials)
                return self._run_oauth_flow(credentials_info)
            
            # Try local credentials file
            credentials_paths = [self.credentials_file, f'backend/{self.credentials_file}']
            for cred_path in credentials_paths:
                if os.path.exists(cred_path):
                    print(f"[AUTH] Using local credentials from {cred_path}")
                    with open(cred_path, 'r') as f:
                        credentials_info = json.load(f)
                    return self._run_oauth_flow(credentials_info)
            
            print("[ERROR] No OAuth credentials found")
            return None
            
        except Exception as e:
            print(f"[ERROR] OAuth flow failed: {e}")
            return None

    def _run_oauth_flow(self, credentials_info: dict) -> Optional[Credentials]:
        """Run the actual OAuth flow"""
        try:
            # Check if this is a web application or installed app
            if 'web' in credentials_info:
                # Web application - use Flow
                flow = Flow.from_client_config(
                    credentials_info,
                    scopes=self.SCOPES,
                    redirect_uri='http://localhost:8080'
                )
                
                # Generate authorization URL
                auth_url, _ = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true',
                    prompt='consent'
                )
                
                print(f"[OAUTH] Complete OAuth flow by visiting this URL:")
                print(f"[OAUTH] {auth_url}")
                print("[OAUTH] After completing OAuth, restart the service")
                print("[OAUTH] The token will be saved automatically")
                
                # For production, we can't complete the flow automatically
                # Return None to indicate manual intervention needed
                return None
                
            else:
                # Installed application - use InstalledAppFlow
                flow = InstalledAppFlow.from_client_config(
                    credentials_info, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
                return creds
                
        except Exception as e:
            print(f"[ERROR] OAuth flow execution failed: {e}")
            return None

    def _save_token(self, creds: Credentials):
        """Save credentials to token file"""
        try:
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            print(f"[AUTH] Token saved to {self.token_file}")
        except Exception as e:
            print(f"[WARNING] Could not save token: {e}")

    def refresh_token_if_needed(self):
        """Refresh token if it's expired or about to expire"""
        if not self.credentials:
            return False
        
        try:
            # Check if token is expired or will expire in the next 5 minutes
            if self.credentials.expired or (self.credentials.expiry and 
                self.credentials.expiry <= datetime.utcnow() + timedelta(minutes=5)):
                
                if self.credentials.refresh_token:
                    print("[AUTH] Refreshing expired token...")
                    self.credentials.refresh(Request())
                    self._save_token(self.credentials)
                    self.service = build('drive', 'v3', credentials=self.credentials)
                    print("[AUTH] Token refreshed successfully")
                    return True
                else:
                    print("[AUTH] Token expired and no refresh token available")
                    return False
        except Exception as e:
            print(f"[AUTH] Token refresh failed: {e}")
            return False
        
        return True

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
            # Refresh token if needed before making API calls
            self.refresh_token_if_needed()
            
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
            # Refresh token if needed before making API calls
            if not self.refresh_token_if_needed():
                print("[ERROR] Token refresh failed, cannot upload file")
                return None
            
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
            # Refresh token if needed before making API calls
            if not self.refresh_token_if_needed():
                print("[ERROR] Token refresh failed, cannot delete file")
                return False
            
            self.service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Error deleting file {file_id}: {e}")
            return False

    def get_folder_id(self, folder_type: str) -> Optional[str]:
        """Get folder ID based on type"""
        return self.folders.get(folder_type)

    def is_authenticated(self) -> bool:
        """Check if service is properly authenticated"""
        return self.service is not None and self.credentials is not None

    def get_auth_status(self) -> Dict[str, Any]:
        """Get detailed authentication status"""
        status = {
            "authenticated": self.is_authenticated(),
            "service_available": self.service is not None,
            "credentials_available": self.credentials is not None,
            "token_valid": False,
            "token_expiry": None,
            "refresh_token_available": False
        }
        
        if self.credentials:
            status["token_valid"] = self.credentials.valid
            status["token_expiry"] = self.credentials.expiry.isoformat() if self.credentials.expiry else None
            status["refresh_token_available"] = bool(self.credentials.refresh_token)
        
        return status
