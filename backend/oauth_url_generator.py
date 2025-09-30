#!/usr/bin/env python3
"""
Generate OAuth URL for Google Drive authentication
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

def generate_oauth_url():
    """Generate OAuth URL for Google Drive"""
    
    print("Generating OAuth URL for Google Drive")
    print("=" * 40)
    
    # OAuth scopes
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    # Get credentials from environment variable
    oauth_credentials = os.getenv('GOOGLE_OAUTH_CREDENTIALS')
    if not oauth_credentials:
        print("ERROR: GOOGLE_OAUTH_CREDENTIALS environment variable not set")
        return None
    
    try:
        credentials_info = json.loads(oauth_credentials)
        flow = InstalledAppFlow.from_client_config(credentials_info, SCOPES)
        
        # Generate OAuth URL
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        print("SUCCESS: OAuth URL generated!")
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
        print("4. Copy the authorization code from the redirect URL")
        print("5. The token will be saved automatically")
        print()
        print("=" * 60)
        
        return auth_url
        
    except Exception as e:
        print(f"ERROR: Failed to generate OAuth URL: {e}")
        return None

if __name__ == "__main__":
    generate_oauth_url()
