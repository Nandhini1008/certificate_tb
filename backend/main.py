from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # Needed for Render storage
from fastapi.responses import HTMLResponse, FileResponse
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
from datetime import datetime
import json
from bson import ObjectId
import secrets
import string

from models import Template, Certificate, Placeholder
from services import CertificateService, TemplateService, QRService
from utils import generate_certificate_id

app = FastAPI(title="Tech Buddy Space Certificate API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Set to False when allowing all origins
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount static files for Render storage
if os.path.exists("storage"):
    app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/student_details")

# Handle MongoDB connection with proper error handling
try:
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    # Test the connection
    client.admin.command('ping')
    db = client.student_details
    print("[SUCCESS] MongoDB connection established successfully")
except Exception as e:
    print(f"[ERROR] MongoDB connection failed: {e}")
    print("Please check your MONGODB_URL environment variable")
    # For development, you might want to continue without MongoDB
    # For production, you should exit here
    if os.getenv("ENVIRONMENT") == "production":
        raise e

# Create storage directories
os.makedirs("storage/templates", exist_ok=True)
os.makedirs("storage/certificates", exist_ok=True)
os.makedirs("storage/qr", exist_ok=True)
os.makedirs("storage/fonts", exist_ok=True)

# Mount static files
# app.mount("/storage", StaticFiles(directory="storage"), name="storage")  # No longer needed with Google Drive

# Initialize services (with error handling)
try:
    certificate_service = CertificateService(db)
    template_service = TemplateService(db)
    qr_service = QRService()
    print("[SUCCESS] Services initialized successfully")
except Exception as e:
    print(f"[WARNING] Service initialization warning: {e}")
    print("[WARNING] Some features may not work properly")
    # Create dummy services to prevent crashes
    certificate_service = None
    template_service = None
    qr_service = None

# Create indexes for better performance
db.student_details.create_index("certificate_id", unique=True)
db.student_details.create_index("student_name")
db.student_details.create_index("course_name")
db.student_details.create_index("issued_at")
db.templates.create_index("template_id", unique=True)

# API Routes

@app.get("/")
async def root():
    return {"message": "Tech Buddy Space Certificate API", "version": "1.0.1", "status": "running", "oauth": "enabled"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/auth/google")
async def auth_google():
    """Trigger Google OAuth authentication"""
    try:
        # Generate OAuth URL with proper redirect URI
        from oauth_flow_handler import create_oauth_flow
        auth_url = create_oauth_flow()
        
        if auth_url:
            return {
                "status": "oauth_required",
                "message": "OAuth authentication required",
                "auth_url": auth_url,
                "instructions": [
                    "1. Visit the auth_url in your browser",
                    "2. Sign in with your Google account", 
                    "3. Grant permissions for Google Drive access",
                    "4. You'll be redirected to localhost (this will fail - that's expected)",
                    "5. Copy the authorization code from the URL",
                    "6. Visit: https://certificate-tb.onrender.com/auth/callback?code=YOUR_CODE",
                    "7. The token will be saved automatically"
                ]
            }
        else:
            return {"status": "error", "message": "Failed to generate OAuth URL"}
    except Exception as e:
        return {"status": "error", "message": f"Authentication error: {str(e)}"}

@app.get("/auth/callback")
async def auth_callback(code: str = None):
    """Handle OAuth callback and save token"""
    try:
        if not code:
            return {"status": "error", "message": "Authorization code is required"}
        
        # Handle OAuth callback
        from oauth_callback_handler import handle_oauth_callback
        token_data = handle_oauth_callback(code)
        
        if token_data:
            return {
                "status": "success",
                "message": "OAuth token saved successfully!",
                "token_info": {
                    "expires": token_data.get("expiry"),
                    "scopes": token_data.get("scopes")
                }
            }
        else:
            return {"status": "error", "message": "Failed to save OAuth token"}
            
    except Exception as e:
        return {"status": "error", "message": f"Callback error: {str(e)}"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "cors": "enabled"}

@app.get("/api/debug/templates")
async def debug_templates():
    """Debug endpoint to see all templates"""
    try:
        templates = await template_service.list_templates()
        return {
            "count": len(templates),
            "templates": templates,
            "template_ids": [t.get("template_id") for t in templates]
        }
    except Exception as e:
        return {"error": str(e)}

# Template Management
@app.post("/api/templates/upload")
async def upload_template(
    file: UploadFile = File(...),
    template_name: str = Form(...),
    description: str = Form("")
):
    """Upload a certificate template image"""
    try:
        template_id = await template_service.upload_template(file, template_name, description)
        
        # Get the template to return the correct image URL
        template = await template_service.get_template(template_id)
        
        return {
            "template_id": template_id,
            "preview_url": template["image_path"] if template else f"/storage/templates/{template_id}.png",
            "message": "Template uploaded successfully"
        }
    except Exception as e:
        print(f"[ERROR] Upload error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/templates/{template_id}/placeholders")
async def set_placeholders(template_id: str, placeholders_data: List[dict]):
    """Set placeholder positions for a template"""
    try:
        print(f"DEBUG: Received raw data for template {template_id}: {placeholders_data}")
        
        # Convert to Placeholder objects
        placeholders = [Placeholder(**p) for p in placeholders_data]
        
        print(f"DEBUG: Converted placeholders:")
        for p in placeholders:
            print(f"  - {p.key}: x1={p.x1}, y1={p.y1}, x2={p.x2}, y2={p.y2}")
        
        await template_service.set_placeholders(template_id, placeholders)
        return {"message": "Placeholders updated successfully"}
    except Exception as e:
        print(f"DEBUG: Error setting placeholders: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/templates")
async def list_templates():
    """List all templates"""
    try:
        templates = await template_service.list_templates()
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    """Get a specific template by ID"""
    try:
        template = await template_service.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Certificate Generation
@app.post("/api/certificates/generate")
async def generate_certificate(data: dict):
    """Generate a certificate for a student"""
    try:
        print(f"Received data: {data}")  # Debug logging
        
        template_id = data.get("template_id")
        student_name = data.get("student_name")
        course_name = data.get("course_name", "")  # Make course_name optional
        date_str = data.get("date_str")
        
        print(f"Extracted: template_id={template_id}, student_name={student_name}, course_name={course_name}, date_str={date_str}")
        
        if not all([template_id, student_name, date_str]):
            missing = [field for field, value in [("template_id", template_id), ("student_name", student_name), ("date_str", date_str)] if not value]
            raise HTTPException(status_code=422, detail=f"Missing required fields: {missing}")
        
        certificate = await certificate_service.generate_certificate(
            template_id, student_name, course_name, date_str
        )
        return {
            "certificate_id": certificate["certificate_id"],
            "certificate_url": certificate["image_path"],  # Google Drive URL
            "qr_url": certificate["qr_path"]  # Google Drive URL
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating certificate: {e}")  # Debug logging
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/certificates/{certificate_id}")
async def get_certificate(certificate_id: str):
    """Get certificate metadata"""
    try:
        certificate = await certificate_service.get_certificate(certificate_id)
        if not certificate:
            raise HTTPException(status_code=404, detail="Certificate not found")
        return certificate
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/certificates/{certificate_id}/revoke")
async def revoke_certificate(certificate_id: str, reason: str = ""):
    """Revoke a certificate"""
    try:
        await certificate_service.revoke_certificate(certificate_id, reason)
        return {"message": "Certificate revoked successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/certificates/{certificate_id}")
async def delete_certificate(certificate_id: str):
    """Delete a certificate completely"""
    try:
        await certificate_service.delete_certificate(certificate_id)
        return {"message": "Certificate deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/certificates")
async def list_certificates():
    """List all certificates"""
    try:
        certificates = await certificate_service.list_certificates()
        return {"certificates": certificates}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/students")
async def list_students():
    """List all students with their details"""
    try:
        students = await certificate_service.list_certificates()
        return {"students": students}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/students/{certificate_id}")
async def update_student_details(certificate_id: str, student_data: dict):
    """Update student details"""
    try:
        result = db.student_details.update_one(
            {"certificate_id": certificate_id},
            {"$set": student_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Student not found")
        
        return {"message": "Student details updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Public Verification
@app.get("/verify/{certificate_id}", response_class=HTMLResponse)
async def verify_certificate(certificate_id: str):
    """Public verification page for certificates"""
    try:
        # Log verification attempt
        verification_log = {
            "certificate_id": certificate_id,
            "verified_at": datetime.now(),
            "ip_address": "unknown",  # Could be enhanced to get real IP
            "user_agent": "unknown",  # Could be enhanced to get real user agent
            "verification_result": "pending"
        }
        
        certificate = await certificate_service.get_certificate(certificate_id)
        if not certificate:
            # Log failed verification
            verification_log["verification_result"] = "failed"
            verification_log["failure_reason"] = "certificate_not_found"
            db.certificates.insert_one(verification_log)
            
            return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Certificate Verification - Not Found</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-50 min-h-screen flex items-center justify-center">
                <div class="bg-white p-8 rounded-lg shadow-lg text-center">
                    <div class="text-red-500 text-6xl mb-4">[ERROR]</div>
                    <h1 class="text-2xl font-bold text-gray-800 mb-2">Certificate Not Found</h1>
                    <p class="text-gray-600">The certificate you're looking for doesn't exist or has been deleted.</p>
                </div>
            </body>
            </html>
            """)
        
        # Check if certificate is revoked
        if certificate.get("revoked", False):
            # Log revoked verification
            verification_log["verification_result"] = "revoked"
            verification_log["student_name"] = certificate.get("student_name", "")
            verification_log["course_name"] = certificate.get("course_name", "")
            verification_log["revoked_reason"] = certificate.get("revoked_reason", "")
            verification_log["revoked_at"] = certificate.get("revoked_at", "")
            db.certificates.insert_one(verification_log)
            
            return HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Certificate Verification - Revoked</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-50 min-h-screen flex items-center justify-center">
                <div class="bg-white p-8 rounded-lg shadow-lg text-center">
                    <div class="text-red-500 text-6xl mb-4">🚫</div>
                    <h1 class="text-2xl font-bold text-gray-800 mb-2">Certificate Revoked</h1>
                    <p class="text-gray-600">This certificate has been revoked and is no longer valid.</p>
                    <div class="mt-4 p-4 bg-red-50 rounded-lg">
                        <p class="text-sm text-red-700"><strong>Student:</strong> {certificate['student_name']}</p>
                        <p class="text-sm text-red-700"><strong>Course:</strong> {certificate.get('course_name', 'N/A')}</p>
                        <p class="text-sm text-red-700"><strong>Revoked Reason:</strong> {certificate.get('revoked_reason', 'Not specified')}</p>
                    </div>
                </div>
            </body>
            </html>
            """)
        
        # Log successful verification
        verification_log["verification_result"] = "success"
        verification_log["student_name"] = certificate.get("student_name", "")
        verification_log["course_name"] = certificate.get("course_name", "")
        db.certificates.insert_one(verification_log)
        
        # Generate verification page HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Certificate Verification - {certificate['student_name']}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://cdn.tailwindcss.com"></script>
            <script src="https://unpkg.com/framer-motion@10/dist/framer-motion.js"></script>
        </head>
        <body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
            <div class="container mx-auto px-4 py-8">
                <div class="max-w-4xl mx-auto">
                    <div class="bg-white rounded-xl shadow-2xl overflow-hidden">
                        <div class="bg-gradient-to-r from-blue-600 to-indigo-700 p-6 text-white">
                            <h1 class="text-3xl font-bold">Certificate Verification</h1>
                            <p class="text-blue-100">Tech Buddy Space</p>
                        </div>
                        
                        <div class="p-8">
                            <div class="flex items-center justify-center mb-6">
                                <div class="bg-green-100 rounded-full p-4">
                                    <svg class="w-12 h-12 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                                    </svg>
                                </div>
                            </div>
                            
                            <div class="text-center mb-8">
                                <h2 class="text-2xl font-bold text-gray-800 mb-2">Certificate Verified Successfully</h2>
                                <p class="text-gray-600">This certificate is authentic and verified</p>
                            </div>
                            
                            <div class="grid md:grid-cols-2 gap-8">
                                <div class="space-y-4">
                                    <div class="bg-gray-50 p-4 rounded-lg">
                                        <h3 class="font-semibold text-gray-700 mb-2">Student Information</h3>
                                        <p><span class="font-medium">Name:</span> {certificate['student_name']}</p>
                                        <p><span class="font-medium">Course:</span> {certificate['course_name']}</p>
                                        <p><span class="font-medium">Date:</span> {certificate['date_of_registration']}</p>
                                    </div>
                                    
                                    <div class="bg-gray-50 p-4 rounded-lg">
                                        <h3 class="font-semibold text-gray-700 mb-2">Certificate Details</h3>
                                        <p><span class="font-medium">Certificate ID:</span> {certificate['certificate_id']}</p>
                                        <p><span class="font-medium">Issued:</span> {certificate['issued_at'].strftime('%B %d, %Y')}</p>
                                        <p><span class="font-medium">Status:</span> 
                                            <span class="text-green-600 font-semibold">Verified</span>
                                        </p>
                                    </div>
                                </div>
                                
                                <div class="space-y-4">
                                    <div class="bg-gray-50 p-4 rounded-lg">
                                        <h3 class="font-semibold text-gray-700 mb-2">Certificate Preview</h3>
                                        <img src="{certificate['image_path']}" 
                                             alt="Certificate" 
                                             class="w-full h-auto rounded-lg shadow-md">
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-8 text-center">
                                <a href="{certificate['image_path']}" 
                                   download
                                   class="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                    </svg>
                                    Download Certificate
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(html_content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Verification Analytics
@app.get("/api/verification-logs")
async def get_verification_logs():
    """Get verification logs for analytics"""
    try:
        logs = list(db.certificates.find({}, {"_id": 0}).sort("verified_at", -1).limit(100))
        return {"logs": logs, "total": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/verification-stats")
async def get_verification_stats():
    """Get verification statistics"""
    try:
        total_verifications = db.certificates.count_documents({})
        successful_verifications = db.certificates.count_documents({"verification_result": "success"})
        failed_verifications = db.certificates.count_documents({"verification_result": "failed"})
        
        return {
            "total_verifications": total_verifications,
            "successful_verifications": successful_verifications,
            "failed_verifications": failed_verifications,
            "success_rate": (successful_verifications / total_verifications * 100) if total_verifications > 0 else 0
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
