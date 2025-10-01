#!/usr/bin/env python3
"""
Generate a long-lived Google Drive token for production use
This script helps create a token that won't expire quickly
"""

import os
import json
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def generate_long_lived_token():
    """Generate a long-lived token with proper scopes and settings"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    print("=== Google Drive Long-Lived Token Generator ===")
    print("This script will generate a token that lasts longer and has proper refresh capabilities")
    print()
    
    # Try to load credentials
    credentials_info = None
    
    # Method 1: Try environment variable
    oauth_credentials = os.getenv('GOOGLE_OAUTH_CREDENTIALS')
    if oauth_credentials:
        print("✓ Found OAuth credentials in environment variable")
        try:
            credentials_info = json.loads(oauth_credentials)
        except Exception as e:
            print(f"✗ Error parsing environment credentials: {e}")
    
    # Method 2: Try local credentials file
    if not credentials_info:
        credentials_paths = ['credentials.json', 'backend/credentials.json']
        for cred_path in credentials_paths:
            if os.path.exists(cred_path):
                print(f"✓ Found credentials file: {cred_path}")
                try:
                    with open(cred_path, 'r') as f:
                        credentials_info = json.load(f)
                    break
                except Exception as e:
                    print(f"✗ Error reading credentials file: {e}")
    
    if not credentials_info:
        print("✗ No OAuth credentials found!")
        print("Please ensure you have either:")
        print("1. GOOGLE_OAUTH_CREDENTIALS environment variable set")
        print("2. credentials.json file in current directory or backend/")
        return False
    
    try:
        # Check if this is a web application or installed app
        if 'web' in credentials_info:
            print("✓ Web application credentials detected")
            print("Generating OAuth URL for manual completion...")
            
            flow = Flow.from_client_config(
                credentials_info,
                scopes=SCOPES,
                redirect_uri='http://localhost:8080'
            )
            
            # Generate authorization URL with specific parameters for long-lived token
            auth_url, state = flow.authorization_url(
                access_type='offline',  # This is crucial for getting refresh token
                include_granted_scopes='true',
                prompt='consent',  # Force consent to ensure refresh token
                state='long_lived_token'
            )
            
            print("\n" + "="*60)
            print("STEP 1: Complete OAuth Flow")
            print("="*60)
            print(f"Visit this URL in your browser:")
            print(f"{auth_url}")
            print("\nIMPORTANT: Make sure to complete the entire flow and grant all permissions!")
            print("="*60)
            
            # Get authorization code from user
            print("\nSTEP 2: Get Authorization Code")
            print("After completing OAuth, you'll be redirected to a page that may show an error.")
            print("Look at the URL in your browser - it should contain 'code=' followed by a long string.")
            print("Copy everything after 'code=' until the next '&' or end of URL.")
            print()
            
            auth_code = input("Enter the authorization code: ").strip()
            
            if not auth_code:
                print("✗ No authorization code provided")
                return False
            
            # Exchange authorization code for token
            print("Exchanging authorization code for token...")
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            
        else:
            print("✓ Installed application credentials detected")
            print("Running local server for OAuth...")
            
            flow = InstalledAppFlow.from_client_config(
                credentials_info, SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Verify the token has refresh capability
        if not creds.refresh_token:
            print("⚠️  WARNING: No refresh token received!")
            print("This token will expire and require manual re-authentication.")
            print("Make sure you completed the OAuth flow with 'prompt=consent'")
        else:
            print("✓ Refresh token received - this token can be automatically refreshed")
        
        # Save token to file
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
            "universe_domain": getattr(creds, 'universe_domain', 'googleapis.com'),
            "account": getattr(creds, 'account', ''),
            "expiry": creds.expiry.isoformat() if creds.expiry else None
        }
        
        with open('token.json', 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print(f"\n✓ Token saved to token.json")
        print(f"✓ Token expires: {creds.expiry}")
        print(f"✓ Has refresh token: {bool(creds.refresh_token)}")
        
        # Test the token
        print("\nTesting token...")
        try:
            from googleapiclient.discovery import build
            service = build('drive', 'v3', credentials=creds)
            
            # Test API call
            results = service.files().list(pageSize=1, fields="files(id, name)").execute()
            print("✓ Token test successful - API call worked")
            
            # Test refresh capability
            if creds.refresh_token:
                print("Testing token refresh...")
                creds.refresh(Request())
                print("✓ Token refresh test successful")
            
        except Exception as e:
            print(f"✗ Token test failed: {e}")
            return False
        
        print("\n" + "="*60)
        print("SUCCESS: Long-lived token generated!")
        print("="*60)
        print("This token should work for production deployment.")
        print("The token will automatically refresh when needed.")
        print("\nFor Render deployment:")
        print("1. Copy the contents of token.json")
        print("2. Set it as GOOGLE_OAUTH_TOKEN environment variable in Render")
        print("3. Deploy your application")
        
        return True
        
    except Exception as e:
        print(f"✗ Error generating token: {e}")
        return False

if __name__ == "__main__":
    success = generate_long_lived_token()
    if success:
        print("\n✓ Token generation completed successfully!")
    else:
        print("\n✗ Token generation failed!")
        exit(1)
