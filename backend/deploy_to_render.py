#!/usr/bin/env python3
"""
Deploy Google Drive authentication to Render
This script helps prepare and deploy the authentication fix to Render
"""

import os
import json
import sys
from pathlib import Path

def check_token_file():
    """Check if token.json exists and is valid"""
    token_file = 'token.json'
    
    if not os.path.exists(token_file):
        print("✗ token.json file not found!")
        print("Please run 'python setup_google_drive_auth.py' first to generate a token.")
        return False
    
    try:
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        print("✓ token.json file found and valid")
        print(f"   - Has refresh token: {bool(token_data.get('refresh_token'))}")
        print(f"   - Expires: {token_data.get('expiry', 'Unknown')}")
        print(f"   - Scopes: {token_data.get('scopes', [])}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading token.json: {e}")
        return False

def generate_render_environment():
    """Generate environment variable for Render"""
    try:
        with open('token.json', 'r') as f:
            token_data = json.load(f)
        
        # Format token for environment variable
        token_json = json.dumps(token_data, separators=(',', ':'))
        
        # Save to file for easy copying
        with open('render_environment.txt', 'w') as f:
            f.write("GOOGLE_OAUTH_TOKEN=" + token_json)
        
        print("✓ Environment variable generated")
        print("✓ Saved to 'render_environment.txt'")
        
        return token_json
        
    except Exception as e:
        print(f"✗ Error generating environment variable: {e}")
        return None

def check_render_files():
    """Check if all necessary files are present for Render deployment"""
    required_files = [
        'robust_google_drive_service.py',
        'services.py',
        'main.py',
        'requirements.txt'
    ]
    
    print("\nChecking required files for Render deployment:")
    all_present = True
    
    for file_path in required_files:
        exists = os.path.exists(file_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path}")
        if not exists:
            all_present = False
    
    return all_present

def generate_render_yaml():
    """Generate render.yaml configuration"""
    yaml_content = """services:
  - type: web
    name: certificatetb-backend
    env: python
    plan: free
    buildCommand: |
      python -m pip install --upgrade pip
      python -m pip install --no-cache-dir -r requirements.txt
    startCommand: |
      python main.py
    envVars:
      - key: MONGODB_URL
        sync: false
      - key: ENVIRONMENT
        value: production
      - key: BASE_URL
        sync: false
      - key: GOOGLE_OAUTH_TOKEN
        sync: false
    healthCheckPath: /health
    autoDeploy: true
    branch: main
    rootDir: backend
"""
    
    with open('render.yaml', 'w') as f:
        f.write(yaml_content)
    
    print("✓ render.yaml configuration generated")

def main():
    """Main deployment function"""
    print("Render Deployment Preparation")
    print("============================")
    
    # Check token file
    if not check_token_file():
        sys.exit(1)
    
    # Generate environment variable
    token_json = generate_render_environment()
    if not token_json:
        sys.exit(1)
    
    # Check required files
    if not check_render_files():
        print("\n✗ Some required files are missing!")
        print("Please ensure all files are present before deploying.")
        sys.exit(1)
    
    # Generate render.yaml
    generate_render_yaml()
    
    print("\n" + "="*60)
    print("RENDER DEPLOYMENT INSTRUCTIONS")
    print("="*60)
    print("1. Commit all changes to your Git repository")
    print("2. Push to your main branch")
    print("3. Go to your Render dashboard")
    print("4. Select your backend service")
    print("5. Go to Environment tab")
    print("6. Add/Update the GOOGLE_OAUTH_TOKEN environment variable")
    print("7. Copy the value from 'render_environment.txt'")
    print("8. Save and redeploy")
    print()
    print("Environment variable value:")
    print("GOOGLE_OAUTH_TOKEN=" + token_json[:100] + "...")
    print("(Full value saved to 'render_environment.txt')")
    print("="*60)
    
    print("\n✓ Deployment preparation complete!")
    print("✓ All files are ready for Render deployment")
    print("✓ Environment variable is prepared")

if __name__ == "__main__":
    main()
