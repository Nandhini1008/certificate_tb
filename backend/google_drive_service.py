import os
import io
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from typing import Optional, Dict, Any
import json

class GoogleDriveService:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        self.service = None
        self.shared_drive_id = "1IfyPr0GFO8XglciH1VkPyl3xm7E-ZYo_"  # Get from shared drive URL
        self.folder_id = "1IfyPr0GFO8XglciH1VkPyl3xm7E-ZYo_"  # Same as shared drive ID

        # Create subfolder IDs
        self.certificates_folder_id = "19R5c4KLLHfGO113B9nQ9ZkMzKTrG3y17"
        self.templates_folder_id = "1epDPzPPTaF0975OybgTfCFh0GPVHaC2E"
        self.qr_folder_id = "14ksmps_CqB2SVX6EofPj-mVr2yhgADbR"
        self.shared_drive_id = None  # Will be set if using shared drive
        
        # Create subfolder ID
        
        self.authenticate()
        self.setup_folders()
    
    def authenticate(self):
        """Authenticate with Google Drive API using Service Account or OAuth"""
        # Try Service Account from environment variable first (for Render deployment)
        service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        if service_account_json:
            try:
                print("🔑 Using Service Account authentication from environment variable...")
                service_account_info = json.loads(service_account_json)
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info, scopes=self.SCOPES)
                self.service = build('drive', 'v3', credentials=credentials)
                print("✅ Service Account authentication successful")
                return
            except Exception as e:
                print(f"❌ Service Account authentication from environment failed: {e}")
        
        # Try Service Account from file (for local development)
        service_account_paths = [
            'backend/service_account_key.json',
            'service_account_key.json',
            os.path.join(os.path.dirname(__file__), 'service_account_key.json')
        ]
        
        for path in service_account_paths:
            if os.path.exists(path):
                try:
                    print(f"🔑 Using Service Account authentication from {path}...")
                    credentials = service_account.Credentials.from_service_account_file(
                        path, scopes=self.SCOPES)
                    self.service = build('drive', 'v3', credentials=credentials)
                    print("✅ Service Account authentication successful")
                    return
                except Exception as e:
                    print(f"❌ Service Account authentication failed from {path}: {e}")
                    continue
        
        # Fallback to OAuth
        try:
            print("🔑 Using OAuth authentication...")
            creds = None
            token_file = 'token.json'
            
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
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
                        raise FileNotFoundError("No credentials.json found in expected locations")
                
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('drive', 'v3', credentials=creds)
            print("✅ OAuth authentication successful")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            print("⚠️ Google Drive service will not be available")
            self.service = None
    
    def setup_folders(self):
        """Create subfolders for certificates, templates, and QR codes"""
        if not self.service:
            print("⚠️ Google Drive service not available, skipping folder setup")
            return
            
        try:
            # Check if subfolders exist, create if not
            self.certificates_folder_id = self.get_or_create_folder("certificates")
            self.templates_folder_id = self.get_or_create_folder("templates")
            self.qr_folder_id = self.get_or_create_folder("qr_codes")
            
            print(f"✅ Google Drive folders setup complete:")
            print(f"   Certificates: {self.certificates_folder_id}")
            print(f"   Templates: {self.templates_folder_id}")
            print(f"   QR Codes: {self.qr_folder_id}")
            
        except Exception as e:
            print(f"❌ Error setting up Google Drive folders: {e}")
    
    def get_or_create_folder(self, folder_name: str) -> str:
        """Get or create a folder in the main Google Drive folder"""
        try:
            # Search for existing folder
            query = f"name='{folder_name}' and parents in '{self.folder_id}' and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])
            
            if items:
                return items[0]['id']
            else:
                # Create new folder
                file_metadata = {
                    'name': folder_name,
                    'parents': [self.folder_id],
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()
                return folder.get('id')
                
        except Exception as e:
            print(f"❌ Error creating folder {folder_name}: {e}")
            return None
    
    def upload_file(self, file_path: str, file_name: str, folder_type: str = "certificates") -> Optional[Dict[str, Any]]:
        """Upload a file to Google Drive"""
        if not self.service:
            print("❌ Google Drive service not available")
            return None
            
        try:
            # Get the appropriate folder ID
            folder_id = None
            if folder_type == "certificates":
                folder_id = self.certificates_folder_id
            elif folder_type == "templates":
                folder_id = self.templates_folder_id
            elif folder_type == "qr":
                folder_id = self.qr_folder_id
            
            if not folder_id:
                print(f"❌ Folder not found for type: {folder_type}")
                return None
            
            # Read file content
            with open(file_path, 'rb') as file:
                file_content = file.read()
            
            # Create file metadata
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            # Upload file
            media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype='image/png')
            
            # Use shared drive if available
            if self.shared_drive_id:
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink, webContentLink',
                    supportsAllDrives=True
                ).execute()
            else:
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
            
            return {
                'id': file.get('id'),
                'webViewLink': file.get('webViewLink'),
                'webContentLink': file.get('webContentLink'),
                'image_url': f"https://drive.google.com/thumbnail?id={file.get('id')}&sz=w1000",  # Thumbnail URL for better CORS
                'name': file_name
            }
            
        except Exception as e:
            print(f"❌ Error uploading file {file_name}: {e}")
            return None
    
    def upload_from_bytes(self, file_bytes: bytes, file_name: str, folder_type: str = "certificates") -> Optional[Dict[str, Any]]:
        """Upload file from bytes to Google Drive"""
        if not self.service:
            print("❌ Google Drive service not available")
            return None
            
        import time
        import ssl
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Get the appropriate folder ID
                folder_id = None
                if folder_type == "certificates":
                    folder_id = self.certificates_folder_id
                elif folder_type == "templates":
                    folder_id = self.templates_folder_id
                elif folder_type == "qr":
                    folder_id = self.qr_folder_id
                
                if not folder_id:
                    print(f"❌ Folder not found for type: {folder_type}")
                    return None
                
                # Create file metadata
                file_metadata = {
                    'name': file_name,
                    'parents': [folder_id]
                }
                
                # Determine MIME type based on file extension
                if file_name.lower().endswith('.png'):
                    mime_type = 'image/png'
                elif file_name.lower().endswith(('.jpg', '.jpeg')):
                    mime_type = 'image/jpeg'
                else:
                    mime_type = 'image/png'  # Default
                
                # Upload file
                media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type)
                
                # Use shared drive if available
                if self.shared_drive_id:
                    file = self.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id, webViewLink, webContentLink',
                        supportsAllDrives=True
                    ).execute()
                else:
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
                
                return {
                    'id': file.get('id'),
                    'webViewLink': file.get('webViewLink'),
                    'webContentLink': file.get('webContentLink'),
                    'image_url': f"https://drive.google.com/thumbnail?id={file.get('id')}&sz=w1000",  # Thumbnail URL for better CORS
                    'name': file_name
                }
                
            except (ssl.SSLError, ConnectionError, Exception) as e:
                print(f"❌ Attempt {attempt + 1} failed uploading file {file_name}: {e}")
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"❌ All attempts failed for file {file_name}")
                    return None
    
    def delete_file(self, file_id: str) -> bool:
        """Delete a file from Google Drive"""
        if not self.service:
            print("❌ Google Drive service not available")
            return False
            
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            print(f"❌ Error deleting file {file_id}: {e}")
            return False
    
    def get_file_url(self, file_id: str) -> str:
        """Get public URL for a file"""
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=w0"
    
    def get_download_url(self, file_id: str) -> str:
        """Get direct download URL for a file"""
        return f"https://drive.google.com/uc?export=download&id={file_id}"
