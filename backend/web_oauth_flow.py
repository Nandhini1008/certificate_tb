#!/usr/bin/env python3
"""
Web-based OAuth flow for Google Drive
"""

import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def create_web_oauth_flow():
    """Create a web-based OAuth flow with proper redirect URI"""
    
    print("Creating Web OAuth Flow")
    print("=" * 30)
    
    # OAuth scopes
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    # Get credentials from environment variable
    oauth_credentials = os.getenv('GOOGLE_OAUTH_CREDENTIALS')
    if not oauth_credentials:
        print("ERROR: GOOGLE_OAUTH_CREDENTIALS environment variable not set")
        return None
    
    try:
        credentials_info = json.loads(oauth_credentials)
        
        # Ensure we have web credentials
        if 'web' not in credentials_info:
            print("ERROR: Web credentials not found in GOOGLE_OAUTH_CREDENTIALS")
            print("Make sure your credentials have 'web' section with redirect_uris")
            return None
        
        # Create flow with explicit redirect URI
        flow = Flow.from_client_config(
            credentials_info, 
            scopes=SCOPES,
            redirect_uri='http://localhost:8080'  # Explicit redirect URI
        )
        
        # Generate OAuth URL
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        print("SUCCESS: Web OAuth URL generated")
        print(f"Redirect URI: http://localhost:8080")
        print(f"OAuth URL: {auth_url}")
        
        # Check if redirect_uri is in the URL
        if 'redirect_uri=' in auth_url:
            print("✓ redirect_uri parameter found in URL")
        else:
            print("❌ redirect_uri parameter MISSING from URL")
        
        return auth_url
        
    except Exception as e:
        print(f"ERROR: Failed to create web OAuth flow: {e}")
        return None

if __name__ == "__main__":
    create_web_oauth_flow()
