"""
Centralized configuration management for Tech Buddy Space Certificate System
All configuration values are read from environment variables
"""

import os
from typing import List, Optional

def _get_base_url() -> str:
    """Get BASE_URL with proper defaults"""
    base_url = os.getenv("BASE_URL", "")
    if not base_url:
        # Only use localhost default in development
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env == "development":
            port = int(os.getenv("PORT", "8000"))
            base_url = f"http://localhost:{port}"
        else:
            raise ValueError("BASE_URL environment variable is required for non-development environments")
    return base_url

def _get_frontend_url() -> str:
    """Get FRONTEND_URL with proper defaults"""
    frontend_url = os.getenv("FRONTEND_URL", "")
    if not frontend_url:
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env == "development":
            port = int(os.getenv("FRONTEND_PORT", "5173"))
            frontend_url = f"http://localhost:{port}"
    return frontend_url

def _get_mongodb_url() -> str:
    """Get MONGODB_URL - REQUIRED"""
    mongodb_url = os.getenv("MONGODB_URL", "")
    if not mongodb_url:
        raise ValueError("MONGODB_URL environment variable is required")
    return mongodb_url

class Config:
    """Application configuration from environment variables"""
    
    # ============================================
    # Server Configuration
    # ============================================
    PORT: int = int(os.getenv("PORT", "8000"))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "5173"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    TESTING_MODE: bool = os.getenv("TESTING_MODE", "true").lower() == "true"
    IS_PRODUCTION: bool = ENVIRONMENT == "production"
    
    # ============================================
    # API URLs and Base URLs
    # ============================================
    BASE_URL: str = _get_base_url()
    FRONTEND_URL: str = _get_frontend_url()
    PUBLIC_BACKEND_URL: str = os.getenv("PUBLIC_BACKEND_URL", BASE_URL)
    PUBLIC_FRONTEND_URL: str = os.getenv("PUBLIC_FRONTEND_URL", FRONTEND_URL)
    
    # ============================================
    # CORS Configuration
    # ============================================
    @staticmethod
    def get_cors_origins() -> List[str]:
        """Get list of allowed CORS origins"""
        origins = [
            Config.PUBLIC_FRONTEND_URL,
            Config.PUBLIC_BACKEND_URL,
            Config.FRONTEND_URL,
            f"http://localhost:{Config.FRONTEND_PORT}",
            f"http://127.0.0.1:{Config.FRONTEND_PORT}",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        
        # Add production URLs from environment variables (if set)
        production_frontend = os.getenv("PRODUCTION_FRONTEND_URL", "")
        production_backend = os.getenv("PRODUCTION_BACKEND_URL", "")
        if production_frontend:
            origins.append(production_frontend)
        if production_backend:
            origins.append(production_backend)
        
        # Add additional origins from environment
        additional_origins = os.getenv("CORS_ADDITIONAL_ORIGINS", "")
        if additional_origins:
            origins.extend([origin.strip() for origin in additional_origins.split(",") if origin.strip()])
        
        # Remove duplicates and empty strings
        return list(set([origin for origin in origins if origin]))
    
    # ============================================
    # Database Configuration
    # ============================================
    MONGODB_URL: str = _get_mongodb_url()
    
    # ============================================
    # Email Configuration (SMTP)
    # ============================================
    # For Render: Use Mailgun or SendGrid SMTP relay instead of Gmail
    # Mailgun SMTP: smtp.mailgun.org (port 587)
    # SendGrid SMTP: smtp.sendgrid.net (port 587)
    # Gmail SMTP: smtp.gmail.com (port 587) - BLOCKED on Render
    # SMTP defaults - all from environment variables (no hardcoded values)
    _env_check = os.getenv("ENVIRONMENT", "development").lower()
    if _env_check == "development":
        # Localhost development - use environment variables with empty defaults
        _smtp_user_default = os.getenv("SMTP_USER", "")
        _smtp_pass_default = os.getenv("SMTP_PASS", "")
        _smtp_host_default = os.getenv("SMTP_HOST", "smtp.gmail.com")
        _contact_email_default = os.getenv("CONTACT_EMAIL", "")
        _contact_phone_default = os.getenv("CONTACT_PHONE", "")
        _website_url_default = os.getenv("WEBSITE_URL", "")
        _instagram_url_default = os.getenv("INSTAGRAM_URL", "")
    else:
        # Production - all values must come from environment variables
        _smtp_user_default = os.getenv("SMTP_USER", "")
        _smtp_pass_default = os.getenv("SMTP_PASS", "")
        _smtp_host_default = os.getenv("SMTP_HOST", "smtp.mailgun.org")
        _contact_email_default = os.getenv("CONTACT_EMAIL", "")
        _contact_phone_default = os.getenv("CONTACT_PHONE", "")
        _website_url_default = os.getenv("WEBSITE_URL", "")
        _instagram_url_default = os.getenv("INSTAGRAM_URL", "")
    
    SMTP_USER: str = os.getenv("SMTP_USER", _smtp_user_default)
    SMTP_PASS: str = os.getenv("SMTP_PASS", _smtp_pass_default)
    SMTP_HOST: str = os.getenv("SMTP_HOST", _smtp_host_default)
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    
    # Contact information
    CONTACT_EMAIL: str = os.getenv("CONTACT_EMAIL", _contact_email_default)
    CONTACT_PHONE: str = os.getenv("CONTACT_PHONE", _contact_phone_default)
    WEBSITE_URL: str = os.getenv("WEBSITE_URL", _website_url_default)
    INSTAGRAM_URL: str = os.getenv("INSTAGRAM_URL", _instagram_url_default)
    
    # ============================================
    # SMTP Microservice Configuration
    # ============================================
    # URL of the SMTP microservice (exposed via ngrok when running locally)
    # Example: https://xxxx-xxxx-xxxx.ngrok-free.app
    SMTP_SERVICE_URL: Optional[str] = os.getenv("SMTP_SERVICE_URL", "")
    
    # ============================================
    # Google Drive / OAuth Configuration
    # ============================================
    GOOGLE_OAUTH_TOKEN: Optional[str] = os.getenv("GOOGLE_OAUTH_TOKEN")
    GOOGLE_OAUTH_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_OAUTH_CREDENTIALS")
    
    # ============================================
    # Helper Methods
    # ============================================
    @staticmethod
    def get_verify_url(certificate_id: str) -> str:
        """Get verification URL for a certificate"""
        return f"{Config.PUBLIC_BACKEND_URL}/verify/{certificate_id}"
    
    @staticmethod
    def print_config():
        """Print current configuration (without sensitive data)"""
        print("=" * 60)
        print("Application Configuration")
        print("=" * 60)
        print(f"Environment: {Config.ENVIRONMENT}")
        print(f"Port: {Config.PORT}")
        print(f"Base URL: {Config.BASE_URL}")
        print(f"Frontend URL: {Config.FRONTEND_URL}")
        print(f"Public Backend URL: {Config.PUBLIC_BACKEND_URL}")
        print(f"Public Frontend URL: {Config.PUBLIC_FRONTEND_URL}")
        print(f"Testing Mode: {Config.TESTING_MODE}")
        print(f"CORS Origins: {Config.get_cors_origins()}")
        print(f"MongoDB: {Config.MONGODB_URL.split('@')[1] if '@' in Config.MONGODB_URL else 'Configured'}")
        print(f"SMTP Host: {Config.SMTP_HOST}:{Config.SMTP_PORT}")
        print(f"Contact Email: {Config.CONTACT_EMAIL}")
        print("=" * 60)

# Create a global config instance
config = Config()
