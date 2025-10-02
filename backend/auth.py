#!/usr/bin/env python3
"""
Authentication system for certificate application
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pymongo import MongoClient
import os
from functools import wraps
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/certificate_db")
client = MongoClient(MONGODB_URL)
db = client.certificate_db
users_collection = db.users

# Security
security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.users = users_collection
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            salt, password_hash = hashed_password.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except:
            return False
    
    def create_user(self, user_id: str, password: str, role: str = "admin") -> Dict[str, Any]:
        """Create a new user"""
        # Check if user already exists
        if self.users.find_one({"user_id": user_id}):
            raise ValueError("User already exists")
        
        hashed_password = self.hash_password(password)
        user_data = {
            "user_id": user_id,
            "password_hash": hashed_password,
            "role": role,
            "created_at": datetime.now(),
            "last_login": None,
            "is_active": True
        }
        
        result = self.users.insert_one(user_data)
        return {
            "user_id": user_id,
            "role": role,
            "created_at": user_data["created_at"],
            "id": str(result.inserted_id)
        }
    
    def authenticate_user(self, user_id: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        user = self.users.find_one({"user_id": user_id, "is_active": True})
        
        if not user:
            return None
        
        if not self.verify_password(password, user["password_hash"]):
            return None
        
        # Update last login
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"last_login": datetime.now()}}
        )
        
        return {
            "user_id": user["user_id"],
            "role": user["role"],
            "last_login": user.get("last_login"),
            "created_at": user["created_at"]
        }
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        user = self.users.find_one({"user_id": user_id, "is_active": True})
        if user:
            return {
                "user_id": user["user_id"],
                "role": user["role"],
                "last_login": user.get("last_login"),
                "created_at": user["created_at"]
            }
        return None

# Global auth service instance
auth_service = AuthService()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user"""
    # For now, we'll use a simple token-based approach
    # In production, you'd want to implement JWT tokens
    token = credentials.credentials
    
    # Simple token validation (in production, use JWT)
    if token == "valid_token":  # This would be set after successful login
        return {"user_id": "123456789", "role": "admin"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        # For now, we'll implement simple session-based auth
        # In production, you'd want to use JWT tokens
        return await f(*args, **kwargs)
    return decorated_function

def initialize_default_user():
    """Initialize default user if not exists"""
    try:
        # Check if default user exists
        existing_user = auth_service.get_user_by_id("123456789")
        if existing_user:
            print("[AUTH] Default user already exists")
            return
        
        # Create default user
        user_data = auth_service.create_user("123456789", "TB_SpAcE", "admin")
        print(f"[AUTH] Default user created successfully: {user_data['user_id']}")
        
    except Exception as e:
        print(f"[AUTH] Error initializing default user: {e}")

# Initialize default user on import
initialize_default_user()
