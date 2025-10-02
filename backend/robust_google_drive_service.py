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
from typing import Optional, Dict, Any, List
import io

class RobustGoogleDriveService:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        self.service = None
        self.credentials = None
        # Known folder IDs for the certificate system
        self.folders = {
            "certificates": "19R5c4KLLHfGO113B9nQ9ZkMzKTrG3y17",
            "templates": "1epDPzPPTaF0975OybgTfCFh0GPVHaC2E",
            "qr_codes": "14ksmps_CqB2SVX6EofPj-mVr2yhgADbR"
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
                # Build the Google Drive service with timeout configuration
                from googleapiclient.http import build_http
                
                # Create HTTP client with timeout
                http = build_http()
                http.timeout = 120  # 2 minutes timeout
                
                # Build service with credentials only (no custom HTTP client for now)
                self.service = build('drive', 'v3', credentials=creds)
                print("[SUCCESS] Google Drive authentication successful")
                
                # Save token for future use
                self._save_token(creds)
            else:
                print("[ERROR] All authentication methods failed")
                print("[ERROR] Please ensure GOOGLE_OAUTH_TOKEN environment variable is set correctly")
                self.service = None
                
        except Exception as e:
            print(f"[ERROR] Authentication failed: {e}")
            print("[ERROR] Please check your Google Drive credentials and environment variables")
            self.service = None

    def _load_from_environment(self) -> Optional[Credentials]:
        """Load credentials from environment variables (for Render)"""
        try:
            # Try GOOGLE_OAUTH_TOKEN first (complete token)
            token_env = os.getenv('GOOGLE_OAUTH_TOKEN')
            if token_env:
                print("[AUTH] Loading token from GOOGLE_OAUTH_TOKEN environment variable...")
                try:
                    token_data = json.loads(token_env)
                    creds = Credentials.from_authorized_user_info(token_data, self.SCOPES)
                    
                    if creds and creds.valid:
                        print("[AUTH] Token from environment is valid")
                        return creds
                    elif creds and creds.expired and creds.refresh_token:
                        print("[AUTH] Token from environment is expired but refreshable")
                        # Try to refresh immediately
                        try:
                            creds.refresh(Request())
                            print("[AUTH] Token refreshed successfully from environment")
                            return creds
                        except Exception as refresh_error:
                            print(f"[AUTH] Token refresh failed: {refresh_error}")
                            return creds  # Return expired token, will be handled later
                    else:
                        print("[AUTH] Token from environment is invalid")
                        return None
                except json.JSONDecodeError as e:
                    print(f"[AUTH] Invalid JSON in GOOGLE_OAUTH_TOKEN: {e}")
                    return None
                except Exception as e:
                    print(f"[AUTH] Error processing environment token: {e}")
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
        """Verify and setup required folders in Google Drive"""
        if not self.service:
            print("[WARNING] Google Drive service not available, skipping folder setup")
            return
        
        try:
            print("[SETUP] Verifying Google Drive folders...")
            
            # Ensure we have valid credentials before checking folders
            if not self.refresh_token_if_needed():
                print("[ERROR] Cannot verify folders - token refresh failed")
                return
            
            # Verify existing folder IDs are accessible
            verified_folders = {}
            for folder_type, folder_id in self.folders.items():
                if folder_id:
                    try:
                        folder_info = self.service.files().get(
                            fileId=folder_id,
                            fields='id, name, mimeType'
                        ).execute()
                        
                        if folder_info.get('mimeType') == 'application/vnd.google-apps.folder':
                            verified_folders[folder_type] = folder_id
                            print(f"   ✅ {folder_type.title()}: {folder_id} ({folder_info.get('name')})")
                        else:
                            print(f"   ❌ {folder_type.title()}: {folder_id} (Not a folder!)")
                            # Try to create the folder
                            new_folder_id = self.get_or_create_folder(folder_type)
                            if new_folder_id:
                                verified_folders[folder_type] = new_folder_id
                                print(f"   ✅ {folder_type.title()}: Created new folder {new_folder_id}")
                    except Exception as e:
                        print(f"   ❌ {folder_type.title()}: {folder_id} (Error: {e})")
                        # Try to create the folder
                        new_folder_id = self.get_or_create_folder(folder_type)
                        if new_folder_id:
                            verified_folders[folder_type] = new_folder_id
                            print(f"   ✅ {folder_type.title()}: Created new folder {new_folder_id}")
                else:
                    print(f"   ❌ {folder_type.title()}: No folder ID specified")
                    # Try to create the folder
                    new_folder_id = self.get_or_create_folder(folder_type)
                    if new_folder_id:
                        verified_folders[folder_type] = new_folder_id
                        print(f"   ✅ {folder_type.title()}: Created new folder {new_folder_id}")
            
            # Update folders with verified IDs
            self.folders.update(verified_folders)
            
            print("[SUCCESS] Google Drive folders verification complete:")
            for folder_type, folder_id in self.folders.items():
                if folder_id:
                    print(f"   ✅ {folder_type.title()}: {folder_id}")
                else:
                    print(f"   ❌ {folder_type.title()}: NOT ACCESSIBLE")
                    
            # Verify folders are accessible
            self.verify_folders()
                
        except Exception as e:
            print(f"[ERROR] Error setting up Google Drive folders: {e}")
            import traceback
            traceback.print_exc()

    def verify_folders(self):
        """Verify that all folders are accessible"""
        print("[VERIFY] Verifying folder accessibility...")
        
        for folder_type, folder_id in self.folders.items():
            if folder_id:
                try:
                    folder_info = self.service.files().get(
                        fileId=folder_id,
                        fields='id, name, mimeType'
                    ).execute()
                    
                    if folder_info.get('mimeType') == 'application/vnd.google-apps.folder':
                        print(f"   ✅ {folder_type.title()} folder verified: {folder_info.get('name')}")
                    else:
                        print(f"   ❌ {folder_type.title()} is not a folder!")
                        
                except Exception as e:
                    print(f"   ❌ {folder_type.title()} folder verification failed: {e}")
            else:
                print(f"   ❌ {folder_type.title()} folder ID is None")

    def ensure_folders_setup(self):
        """Ensure all required folders are set up before operations"""
        # Check if any folder is missing
        missing_folders = []
        for folder_type, folder_id in self.folders.items():
            if not folder_id:
                missing_folders.append(folder_type)
        
        if missing_folders:
            print(f"[SETUP] Missing folders detected: {missing_folders}")
            print("[SETUP] Re-running folder setup...")
            self.setup_folders()
        else:
            print("[SETUP] All folders are properly set up")

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

    def upload_from_bytes(self, file_bytes: bytes, file_name: str, folder_type: str = "certificates", max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """Upload file from bytes to Google Drive with retry logic and timeout handling"""
        if not self.service:
            print("[ERROR] Google Drive service not available")
            return None
        
        # Refresh token if needed before making API calls
        if not self.refresh_token_if_needed():
            print("[ERROR] Token refresh failed, cannot upload file")
            return None
        
        # Ensure folders are set up before uploading
        self.ensure_folders_setup()
        
        # Map folder types to actual folder names
        folder_mapping = {
            "certificates": "certificates",
            "templates": "templates", 
            "qr": "qr_codes",  # Map "qr" to "qr_codes"
            "qr_codes": "qr_codes"
        }
        
        actual_folder_type = folder_mapping.get(folder_type, folder_type)
        folder_id = self.folders.get(actual_folder_type)
        if not folder_id:
            print(f"[ERROR] Folder not found for type: {folder_type} (mapped to {actual_folder_type})")
            print(f"[DEBUG] Available folders: {list(self.folders.keys())}")
            return None
        
        print(f"[DEBUG] Uploading {file_name} to folder {actual_folder_type} (ID: {folder_id})")
        print(f"[DEBUG] File size: {len(file_bytes)} bytes")
        
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] Upload attempt {attempt + 1}/{max_retries}")
                
                # Upload file with increased timeout
                file_metadata = {
                    'name': file_name,
                    'parents': [folder_id]
                }
                
                # Create media with resumable upload for large files
                media = MediaIoBaseUpload(
                    io.BytesIO(file_bytes), 
                    mimetype='image/png',
                    resumable=True
                )
                
                # Execute upload with timeout
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink, webContentLink'
                ).execute()
                
                print(f"[DEBUG] Upload successful on attempt {attempt + 1}")
                
                # Make file publicly accessible
                try:
                    self.service.permissions().create(
                        fileId=file.get('id'),
                        body={'role': 'reader', 'type': 'anyone'}
                    ).execute()
                    print(f"[DEBUG] File permissions set successfully")
                except Exception as perm_error:
                    print(f"[WARNING] Could not set file permissions: {perm_error}")
                    # Continue anyway, file is still uploaded
                
                # Add image_url field for compatibility with direct image access
                file_id = file.get('id')
                if file_id:
                    # Use thumbnail URL format that works better for display in browsers
                    file['image_url'] = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
                    # Also add download_url for download functionality
                    file['download_url'] = f"https://drive.google.com/uc?id={file_id}&export=download"
                else:
                    file['image_url'] = file.get('webContentLink', file.get('webViewLink', ''))
                    file['download_url'] = file.get('webContentLink', file.get('webViewLink', ''))
                
                print(f"[SUCCESS] File uploaded successfully: {file_name}")
                return file
                
            except Exception as e:
                print(f"[ERROR] Upload attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff: 2, 4, 6 seconds
                    print(f"[DEBUG] Waiting {wait_time} seconds before retry...")
                    import time
                    time.sleep(wait_time)
                else:
                    print(f"[ERROR] All {max_retries} upload attempts failed for {file_name}")
                    return None
        
        return None

    def search_files_by_name(self, file_name: str, folder_type: str = "templates") -> List[Dict[str, Any]]:
        """Search for files by name in a specific folder"""
        if not self.service:
            print("[ERROR] Google Drive service not available")
            return []
        
        try:
            # Refresh token if needed before making API calls
            if not self.refresh_token_if_needed():
                print("[ERROR] Token refresh failed, cannot search files")
                return []
            
            folder_id = self.get_folder_id(folder_type)
            if not folder_id:
                print(f"[ERROR] Folder {folder_type} not found")
                return []
            
            # Search for files with the exact name in the specified folder
            query = f"name='{file_name}' and parents in '{folder_id}' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id,name,mimeType,createdTime,modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            print(f"[SEARCH] Found {len(files)} files matching '{file_name}' in {folder_type} folder")
            return files
            
        except Exception as e:
            print(f"[ERROR] Error searching for files: {e}")
            return []

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
