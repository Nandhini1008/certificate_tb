#!/usr/bin/env python3
"""
Fallback Google Drive service for when OAuth is not available
"""

import os
import json
import base64
import hashlib
from typing import Optional, Dict, Any
import io
from datetime import datetime

class FallbackGoogleDriveService:
    def __init__(self):
        self.folders = {
            "certificates": None,
            "templates": None,
            "qr_codes": None
        }
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        print("[INFO] Using fallback Google Drive service")
        print("[WARNING] Files will be stored temporarily - OAuth setup required for persistence")

    def setup_folders(self):
        """Setup virtual folders"""
        try:
            self.folders["certificates"] = self.get_or_create_folder("certificates")
            self.folders["templates"] = self.get_or_create_folder("templates")
            self.folders["qr_codes"] = self.get_or_create_folder("qr_codes")
            
            print("[SUCCESS] Fallback folders setup complete:")
            for folder_type, folder_id in self.folders.items():
                print(f"   {folder_type.title()}: {folder_id}")
                
        except Exception as e:
            print(f"[ERROR] Error setting up fallback folders: {e}")

    def get_or_create_folder(self, folder_name: str) -> str:
        """Create a virtual folder"""
        folder_id = f"fallback_{folder_name}_{hash(folder_name) % 10000}"
        print(f"[INFO] Created virtual folder: {folder_name} (ID: {folder_id})")
        return folder_id

    def upload_file(self, file_path: str, file_name: str, folder_type: str = "certificates") -> Optional[Dict[str, Any]]:
        """Upload a file (fallback simulation)"""
        print(f"[WARNING] Fallback upload simulation: {file_name} to {folder_type}")
        print("[INFO] OAuth setup required for actual Google Drive upload")
        
        # Generate a mock response
        file_id = self._generate_file_id(file_name)
        mock_response = {
            "id": file_id,
            "name": file_name,
            "image_url": f"{self.base_url}/fallback/{folder_type}/{file_name}",
            "webViewLink": f"{self.base_url}/fallback/{folder_type}/{file_name}",
            "webContentLink": f"{self.base_url}/fallback/{folder_type}/{file_name}",
            "fallback": True
        }
        
        print(f"[SUCCESS] Fallback upload successful: {file_name}")
        print(f"[INFO] To enable Google Drive: Complete OAuth authentication")
        return mock_response

    def upload_from_bytes(self, file_bytes: bytes, file_name: str, folder_type: str = "certificates") -> Optional[Dict[str, Any]]:
        """Upload file from bytes (fallback simulation)"""
        print(f"[WARNING] Fallback upload from bytes: {file_name} to {folder_type}")
        print("[INFO] OAuth setup required for actual Google Drive upload")
        
        # Generate a mock response
        file_id = self._generate_file_id(file_name)
        mock_response = {
            "id": file_id,
            "name": file_name,
            "image_url": f"{self.base_url}/fallback/{folder_type}/{file_name}",
            "webViewLink": f"{self.base_url}/fallback/{folder_type}/{file_name}",
            "webContentLink": f"{self.base_url}/fallback/{folder_type}/{file_name}",
            "fallback": True
        }
        
        print(f"[SUCCESS] Fallback upload successful: {file_name}")
        print(f"[INFO] To enable Google Drive: Complete OAuth authentication")
        return mock_response

    def delete_file(self, file_id: str) -> bool:
        """Delete a file (fallback simulation)"""
        print(f"[INFO] Fallback deletion simulation: {file_id}")
        return True

    def get_folder_id(self, folder_type: str) -> Optional[str]:
        """Get folder ID based on type"""
        return self.folders.get(folder_type)

    def _generate_file_id(self, filename: str) -> str:
        """Generate a unique file ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_suffix = hashlib.md5(filename.encode()).hexdigest()[:8]
        return f"FALLBACK-{timestamp}-{hash_suffix}"
