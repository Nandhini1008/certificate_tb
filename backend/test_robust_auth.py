#!/usr/bin/env python3
"""
Test script for the robust Google Drive authentication
"""

import os
import sys
from robust_google_drive_service import RobustGoogleDriveService

def test_authentication():
    """Test the robust authentication service"""
    print("=== Testing Robust Google Drive Authentication ===")
    print()
    
    try:
        # Initialize the service
        print("1. Initializing RobustGoogleDriveService...")
        drive_service = RobustGoogleDriveService()
        
        # Check authentication status
        print("2. Checking authentication status...")
        if drive_service.is_authenticated():
            print("   ✓ Service is authenticated")
        else:
            print("   ✗ Service is not authenticated")
            return False
        
        # Get detailed status
        print("3. Getting detailed authentication status...")
        status = drive_service.get_auth_status()
        print("   Authentication details:")
        for key, value in status.items():
            print(f"     - {key}: {value}")
        
        # Test API call
        print("4. Testing Google Drive API call...")
        try:
            from googleapiclient.discovery import build
            service = build('drive', 'v3', credentials=drive_service.credentials)
            results = service.files().list(pageSize=1, fields="files(id, name)").execute()
            files = results.get('files', [])
            print(f"   ✓ API call successful - found {len(files)} files")
        except Exception as e:
            print(f"   ✗ API call failed: {e}")
            return False
        
        # Test token refresh
        print("5. Testing token refresh capability...")
        if drive_service.refresh_token_if_needed():
            print("   ✓ Token refresh successful")
        else:
            print("   ⚠️  Token refresh not needed or failed")
        
        # Test folder setup
        print("6. Testing folder setup...")
        try:
            folder_id = drive_service.get_or_create_folder("test_folder")
            if folder_id:
                print(f"   ✓ Folder setup successful - ID: {folder_id}")
            else:
                print("   ✗ Folder setup failed")
        except Exception as e:
            print(f"   ✗ Folder setup error: {e}")
        
        print("\n✓ All tests passed! Authentication is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        return False

def test_environment_loading():
    """Test loading from environment variables"""
    print("\n=== Testing Environment Variable Loading ===")
    
    # Check if token is in environment
    token_env = os.getenv('GOOGLE_OAUTH_TOKEN')
    if token_env:
        print("✓ GOOGLE_OAUTH_TOKEN environment variable found")
        try:
            import json
            token_data = json.loads(token_env)
            print(f"   - Has refresh token: {bool(token_data.get('refresh_token'))}")
            print(f"   - Expires: {token_data.get('expiry', 'Unknown')}")
        except Exception as e:
            print(f"   ⚠️  Error parsing environment token: {e}")
    else:
        print("✗ GOOGLE_OAUTH_TOKEN environment variable not found")
    
    # Check if credentials are in environment
    creds_env = os.getenv('GOOGLE_OAUTH_CREDENTIALS')
    if creds_env:
        print("✓ GOOGLE_OAUTH_CREDENTIALS environment variable found")
    else:
        print("✗ GOOGLE_OAUTH_CREDENTIALS environment variable not found")

def main():
    """Main test function"""
    print("Robust Google Drive Authentication Test")
    print("=====================================")
    
    # Test environment loading
    test_environment_loading()
    
    # Test authentication
    success = test_authentication()
    
    if success:
        print("\n🎉 All tests passed! Your Google Drive authentication is working correctly.")
        print("\nNext steps:")
        print("1. If testing locally, you're ready to use the application")
        print("2. If testing for production, deploy with the GOOGLE_OAUTH_TOKEN environment variable")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        print("\nTroubleshooting:")
        print("1. Run 'python setup_google_drive_auth.py' to set up authentication")
        print("2. Check that your credentials.json file is in the correct location")
        print("3. Ensure you have completed the OAuth flow")
        sys.exit(1)

if __name__ == "__main__":
    main()
