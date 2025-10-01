#!/usr/bin/env python3
"""
Comprehensive Google Drive authentication setup script
This script helps set up Google Drive authentication for both local development and production deployment
"""

import os
import json
import sys
from pathlib import Path

def check_environment():
    """Check the current environment and available files"""
    print("=== Google Drive Authentication Setup ===")
    print()
    
    # Check current directory
    print(f"Current directory: {os.getcwd()}")
    
    # Check for existing files
    files_to_check = [
        'token.json',
        'credentials.json',
        'backend/credentials.json',
        'backend/token.json'
    ]
    
    print("\nChecking for existing files:")
    for file_path in files_to_check:
        exists = os.path.exists(file_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path}")
    
    # Check environment variables
    print("\nChecking environment variables:")
    env_vars = [
        'GOOGLE_OAUTH_TOKEN',
        'GOOGLE_OAUTH_CREDENTIALS',
        'ENVIRONMENT'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        status = "✓" if value else "✗"
        print(f"  {status} {var}: {'Set' if value else 'Not set'}")
    
    return True

def setup_local_development():
    """Setup for local development"""
    print("\n=== Local Development Setup ===")
    
    # Check if credentials.json exists
    credentials_paths = ['credentials.json', 'backend/credentials.json']
    credentials_file = None
    
    for path in credentials_paths:
        if os.path.exists(path):
            credentials_file = path
            break
    
    if not credentials_file:
        print("✗ No credentials.json file found!")
        print("Please download your OAuth credentials from Google Cloud Console:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Select your project")
        print("3. Go to APIs & Services → Credentials")
        print("4. Create OAuth 2.0 Client ID (Web application)")
        print("5. Download the JSON file and save as 'credentials.json'")
        return False
    
    print(f"✓ Found credentials file: {credentials_file}")
    
    # Check if token.json exists
    token_file = 'token.json'
    if os.path.exists(token_file):
        print(f"✓ Found existing token file: {token_file}")
        
        # Check if token is valid
        try:
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            
            if 'refresh_token' in token_data and token_data['refresh_token']:
                print("✓ Token has refresh capability")
                return True
            else:
                print("⚠️  Token doesn't have refresh capability - will need to regenerate")
        except Exception as e:
            print(f"⚠️  Error reading token file: {e}")
    
    # Generate new token
    print("\nGenerating new token...")
    try:
        from generate_long_lived_token import generate_long_lived_token
        success = generate_long_lived_token()
        if success:
            print("✓ Token generation successful!")
            return True
        else:
            print("✗ Token generation failed!")
            return False
    except Exception as e:
        print(f"✗ Error generating token: {e}")
        return False

def setup_production_deployment():
    """Setup for production deployment on Render"""
    print("\n=== Production Deployment Setup ===")
    
    # Check if token.json exists
    if not os.path.exists('token.json'):
        print("✗ No token.json file found!")
        print("Please run local development setup first to generate a token.")
        return False
    
    print("✓ Found token.json file")
    
    # Read token data
    try:
        with open('token.json', 'r') as f:
            token_data = json.load(f)
        
        print("Token information:")
        print(f"  - Has refresh token: {bool(token_data.get('refresh_token'))}")
        print(f"  - Expires: {token_data.get('expiry', 'Unknown')}")
        print(f"  - Scopes: {token_data.get('scopes', [])}")
        
        # Format token for environment variable
        token_json = json.dumps(token_data, separators=(',', ':'))
        
        print("\n" + "="*60)
        print("RENDER DEPLOYMENT INSTRUCTIONS")
        print("="*60)
        print("1. Go to your Render dashboard")
        print("2. Select your backend service")
        print("3. Go to Environment tab")
        print("4. Add/Update the following environment variable:")
        print()
        print("Variable: GOOGLE_OAUTH_TOKEN")
        print("Value:")
        print(token_json)
        print()
        print("5. Save the environment variable")
        print("6. Redeploy your service")
        print("="*60)
        
        # Also save to a file for easy copying
        with open('render_token.txt', 'w') as f:
            f.write(token_json)
        
        print(f"\n✓ Token data also saved to 'render_token.txt' for easy copying")
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading token file: {e}")
        return False

def test_authentication():
    """Test the authentication setup"""
    print("\n=== Testing Authentication ===")
    
    try:
        from robust_google_drive_service import RobustGoogleDriveService
        
        print("Initializing Google Drive service...")
        drive_service = RobustGoogleDriveService()
        
        if drive_service.is_authenticated():
            print("✓ Authentication successful!")
            
            # Get status
            status = drive_service.get_auth_status()
            print("\nAuthentication status:")
            for key, value in status.items():
                print(f"  - {key}: {value}")
            
            # Test API call
            print("\nTesting API call...")
            try:
                from googleapiclient.discovery import build
                service = build('drive', 'v3', credentials=drive_service.credentials)
                results = service.files().list(pageSize=1, fields="files(id, name)").execute()
                print("✓ API call successful!")
                return True
            except Exception as e:
                print(f"✗ API call failed: {e}")
                return False
        else:
            print("✗ Authentication failed!")
            return False
            
    except Exception as e:
        print(f"✗ Error testing authentication: {e}")
        return False

def main():
    """Main setup function"""
    print("Google Drive Authentication Setup Tool")
    print("=====================================")
    
    # Check environment
    check_environment()
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Setup for local development")
    print("2. Setup for production deployment")
    print("3. Test current authentication")
    print("4. All of the above")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    success = True
    
    if choice in ['1', '4']:
        success &= setup_local_development()
    
    if choice in ['2', '4']:
        success &= setup_production_deployment()
    
    if choice in ['3', '4']:
        success &= test_authentication()
    
    if success:
        print("\n✓ Setup completed successfully!")
    else:
        print("\n✗ Setup completed with some issues.")
        print("Please check the error messages above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
