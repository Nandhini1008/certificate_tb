#!/usr/bin/env python3
"""
Test script for Tech Buddy Space Certificate API
"""

import requests
import json
import time
import os
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_api_connection():
    """Test if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"✓ API is running: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ API connection failed: {e}")
        return False

def test_template_upload():
    """Test template upload"""
    print("\nTesting template upload...")
    
    # Create a simple test image
    from PIL import Image, ImageDraw, ImageFont
    
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 750, 550], outline='black', width=2)
    draw.text((400, 300), "TEST CERTIFICATE", fill='black', anchor='mm')
    
    # Save test image
    test_image_path = "test_template.png"
    img.save(test_image_path)
    
    try:
        with open(test_image_path, 'rb') as f:
            files = {'file': ('test_template.png', f, 'image/png')}
            data = {
                'template_name': 'Test Template',
                'description': 'Test certificate template'
            }
            response = requests.post(f"{API_BASE_URL}/api/templates/upload", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Template uploaded: {result['template_id']}")
            os.remove(test_image_path)
            return result['template_id']
        else:
            print(f"✗ Template upload failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Template upload error: {e}")
        return None

def test_placeholder_configuration(template_id):
    """Test placeholder configuration"""
    print("\nTesting placeholder configuration...")
    
    placeholders = [
        {
            "key": "student_name",
            "x": 400,
            "y": 300,
            "font": "PlayfairDisplay-Bold.ttf",
            "font_size": 48,
            "color": "#0b2a4a"
        },
        {
            "key": "course_name",
            "x": 400,
            "y": 380,
            "font": "PlayfairDisplay-Bold.ttf",
            "font_size": 36,
            "color": "#0b2a4a"
        },
        {
            "key": "date",
            "x": 200,
            "y": 500,
            "font": "PlayfairDisplay-Bold.ttf",
            "font_size": 24,
            "color": "#0b2a4a"
        }
    ]
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/templates/{template_id}/placeholders",
            json=placeholders
        )
        
        if response.status_code == 200:
            print("✓ Placeholders configured successfully")
            return True
        else:
            print(f"✗ Placeholder configuration failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Placeholder configuration error: {e}")
        return False

def test_certificate_generation(template_id):
    """Test certificate generation"""
    print("\nTesting certificate generation...")
    
    data = {
        "template_id": template_id,
        "student_name": "John Doe",
        "course_name": "Career Catalyst – 9 Day Program",
        "date_str": "2025-07-10"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/certificates/generate", json=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Certificate generated: {result['certificate_id']}")
            return result['certificate_id']
        else:
            print(f"✗ Certificate generation failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Certificate generation error: {e}")
        return None

def test_certificate_verification(certificate_id):
    """Test certificate verification"""
    print("\nTesting certificate verification...")
    
    try:
        # Test API endpoint
        response = requests.get(f"{API_BASE_URL}/api/certificates/{certificate_id}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Certificate retrieved: {result['student_name']}")
            
            # Test student details endpoint
            student_response = requests.get(f"{API_BASE_URL}/api/students")
            if student_response.status_code == 200:
                print("✓ Student details endpoint accessible")
            
            # Test public verification page
            verify_response = requests.get(f"{API_BASE_URL}/verify/{certificate_id}")
            if verify_response.status_code == 200:
                print("✓ Public verification page accessible")
                return True
            else:
                print(f"✗ Public verification page failed: {verify_response.status_code}")
                return False
        else:
            print(f"✗ Certificate retrieval failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Certificate verification error: {e}")
        return False

def test_certificate_revocation(certificate_id):
    """Test certificate revocation"""
    print("\nTesting certificate revocation...")
    
    data = {"reason": "Test revocation"}
    
    try:
        response = requests.put(f"{API_BASE_URL}/api/certificates/{certificate_id}/revoke", json=data)
        
        if response.status_code == 200:
            print("✓ Certificate revoked successfully")
            return True
        else:
            print(f"✗ Certificate revocation failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Certificate revocation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Tech Buddy Space API Test Suite")
    print("=" * 50)
    
    # Test API connection
    if not test_api_connection():
        print("\n❌ Cannot connect to API. Make sure the backend is running.")
        return
    
    # Test template upload
    template_id = test_template_upload()
    if not template_id:
        print("\n❌ Template upload failed. Stopping tests.")
        return
    
    # Test placeholder configuration
    if not test_placeholder_configuration(template_id):
        print("\n⚠️ Placeholder configuration failed, but continuing...")
    
    # Test certificate generation
    certificate_id = test_certificate_generation(template_id)
    if not certificate_id:
        print("\n❌ Certificate generation failed. Stopping tests.")
        return
    
    # Test certificate verification
    if not test_certificate_verification(certificate_id):
        print("\n⚠️ Certificate verification failed.")
    
    # Test certificate revocation
    if not test_certificate_revocation(certificate_id):
        print("\n⚠️ Certificate revocation failed.")
    
    print("\n" + "=" * 50)
    print("✅ Test suite completed!")
    print(f"\nGenerated certificate ID: {certificate_id}")
    print(f"Verification URL: {API_BASE_URL}/verify/{certificate_id}")

if __name__ == "__main__":
    main()
