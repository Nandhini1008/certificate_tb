#!/usr/bin/env python3
"""
OAuth callback handler for Render deployment
"""

import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def handle_oauth_callback(authorization_code: str):
    """Handle OAuth callback and save token"""
    
    print("Handling OAuth Callback")
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
        
        # Create flow with same redirect URI
        flow = Flow.from_client_config(
            credentials_info, 
            scopes=SCOPES,
            redirect_uri='http://localhost:8080'
        )
        
        # Exchange authorization code for token
        flow.fetch_token(code=authorization_code)
        creds = flow.credentials
        
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
        
        # Save to token.json
        with open('backend/token.json', 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print("SUCCESS: Token saved to backend/token.json")
        print(f"Token expires: {creds.expiry}")
        
        return token_data
        
    except Exception as e:
        print(f"ERROR: Failed to handle OAuth callback: {e}")
        return None

if __name__ == "__main__":
    # Test with a sample authorization code
    code = input("Enter authorization code: ").strip()
    if code:
        handle_oauth_callback(code)
