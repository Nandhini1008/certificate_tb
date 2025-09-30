#!/usr/bin/env python3
"""
OAuth flow handler with proper redirect URI
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

def create_oauth_flow():
    """Create OAuth flow with proper redirect URI"""
    
    print("Creating OAuth Flow with Proper Redirect URI")
    print("=" * 45)
    
    # OAuth scopes
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    # Get credentials from environment variable
    oauth_credentials = os.getenv('GOOGLE_OAUTH_CREDENTIALS')
    if not oauth_credentials:
        print("ERROR: GOOGLE_OAUTH_CREDENTIALS environment variable not set")
        return None
    
    try:
        credentials_info = json.loads(oauth_credentials)
        
        # Ensure redirect URIs are set
        if 'installed' in credentials_info:
            credentials_info['installed']['redirect_uris'] = [
                'http://localhost:8000',
                'https://certificate-tb.onrender.com',
                'https://certificate-tb.onrender.com/auth/google'
            ]
        elif 'web' in credentials_info:
            credentials_info['web']['redirect_uris'] = [
                'http://localhost:8000',
                'https://certificate-tb.onrender.com',
                'https://certificate-tb.onrender.com/auth/google'
            ]
        
        # Create flow
        flow = InstalledAppFlow.from_client_config(credentials_info, SCOPES)
        
        # Generate OAuth URL with proper redirect URI
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        print("SUCCESS: OAuth URL generated with proper redirect URI")
        print()
        print("=" * 60)
        print("COMPLETE OAUTH FLOW:")
        print("=" * 60)
        print()
        print("1. Visit this URL in your browser:")
        print(f"   {auth_url}")
        print()
        print("2. Sign in with your Google account")
        print("3. Grant permissions for Google Drive access")
        print("4. You'll be redirected to a localhost URL")
        print("5. Copy the authorization code from the URL")
        print("6. The token will be saved automatically")
        print()
        print("=" * 60)
        
        return auth_url
        
    except Exception as e:
        print(f"ERROR: Failed to create OAuth flow: {e}")
        return None

if __name__ == "__main__":
    create_oauth_flow()
