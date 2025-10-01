from pymongo import MongoClient
from typing import List, Optional, Dict, Any
import os
import uuid
from datetime import datetime
import secrets
import string
from PIL import Image, ImageDraw, ImageFont
import qrcode
from io import BytesIO

from models import Template, Certificate, Placeholder
from utils import generate_certificate_id
from robust_google_drive_service import RobustGoogleDriveService

class TemplateService:
    def __init__(self, db):
        self.db = db
        self.templates = db.templates
        # Use robust service for all environments - no fallback
        self.drive_service = RobustGoogleDriveService()
        if not self.drive_service.is_authenticated():
            print("[ERROR] Google Drive service not authenticated!")
            print("[ERROR] Please check your GOOGLE_OAUTH_TOKEN environment variable")
            raise Exception("Google Drive authentication failed - check your OAuth token")

    async def upload_template(self, file, template_name: str, description: str = "") -> str:
        """Upload a template image and save metadata"""
        # Generate template ID
        template_id = f"TPL-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
        
        # Validate file extension
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['png', 'jpg', 'jpeg']:
            raise ValueError("Only PNG, JPG, and JPEG files are allowed")
        
        # Read file content
        content = await file.read()
        
        # Upload to Google Drive
        file_name = f"{template_id}.{file_extension}"
        drive_result = self.drive_service.upload_from_bytes(
            content, file_name, "templates"
        )
        
        if not drive_result:
            raise ValueError("Failed to upload template to Google Drive. Please check your Google Drive credentials.")
        
        # Save to database with Google Drive URL
        template_data = {
            "template_id": template_id,
            "name": template_name,
            "description": description,
            "image_path": drive_result['image_url'],  # Direct image URL for frontend display
            "drive_file_id": drive_result['id'],  # Store Drive file ID for future operations
            "placeholders": [],
            "uploaded_at": datetime.now()
        }
        
        self.templates.insert_one(template_data)
        return template_id

    async def set_placeholders(self, template_id: str, placeholders: List[Placeholder]):
        """Set placeholder positions for a template"""
        result = self.templates.update_one(
            {"template_id": template_id},
            {"$set": {"placeholders": [p.dict() for p in placeholders]}}
        )
        
        if result.matched_count == 0:
            raise ValueError("Template not found")

    async def get_template(self, template_id: str) -> Optional[Dict]:
        """Get template by ID"""
        return self.templates.find_one({"template_id": template_id}, {"_id": 0})

    async def list_templates(self) -> List[Dict]:
        """List all templates"""
        return list(self.templates.find({}, {"_id": 0}))

class CertificateService:
    def __init__(self, db):
        self.db = db
        self.student_details = db.student_details
        self.templates = db.templates
        # Use robust service for all environments - no fallback
        self.drive_service = RobustGoogleDriveService()
        if not self.drive_service.is_authenticated():
            print("[ERROR] Google Drive service not authenticated!")
            print("[ERROR] Please check your GOOGLE_OAUTH_TOKEN environment variable")
            raise Exception("Google Drive authentication failed - check your OAuth token")

    def _calculate_text_position(self, draw, text, font, x1, y1, x2, y2, text_align, vertical_align):
        """Calculate text position within a rectangle based on alignment settings"""
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            # Fallback if textbbox fails
            text_width = len(text) * 10  # Rough estimate
            text_height = 20
        
        # Calculate rectangle dimensions
        rect_width = x2 - x1
        rect_height = y2 - y1
        
        # Horizontal alignment
        if text_align == "left":
            text_x = x1 + 5  # 5px padding from left edge
        elif text_align == "right":
            text_x = x2 - text_width - 5  # 5px padding from right edge
        else:  # center
            text_x = x1 + (rect_width - text_width) // 2
        
        # Vertical alignment
        if vertical_align == "top":
            text_y = y1 + 5  # 5px padding from top edge
        elif vertical_align == "bottom":
            text_y = y2 - text_height - 5  # 5px padding from bottom edge
        else:  # center
            text_y = y1 + (rect_height - text_height) // 2
        
        return text_x, text_y

    async def generate_certificate(self, template_id: str, student_name: str, course_name: str, date_str: str) -> Dict:
        """Generate a certificate with text overlay and QR code"""
        # Get template
        template = self.templates.find_one({"template_id": template_id})
        if not template:
            raise ValueError("Template not found")
        
        # Generate certificate ID
        certificate_id = generate_certificate_id()
        
        # Load template image (handle both local and Google Drive URLs)
        template_path = template["image_path"]
        
        if template_path.startswith(('http://', 'https://')):
            # Google Drive URL - use direct image URL
            import requests
            response = requests.get(template_path)
            template_image = Image.open(BytesIO(response.content))
        else:
            # Local file path
            template_image = Image.open(template_path)
        
        draw = ImageDraw.Draw(template_image)
        
        # Load font (fallback to system fonts if not found)
        try:
            # Try to load PlayfairDisplay font first
            font_large = ImageFont.truetype("storage/fonts/PlayfairDisplay-Bold.ttf", 48)
            font_small = ImageFont.truetype("storage/fonts/PlayfairDisplay-Bold.ttf", 18)
        except:
            try:
                # Try system fonts as fallback
                font_large = ImageFont.truetype("arial.ttf", 48)
                font_small = ImageFont.truetype("arial.ttf", 18)
            except:
                try:
                    # Try other common system fonts
                    font_large = ImageFont.truetype("calibri.ttf", 48)
                    font_small = ImageFont.truetype("calibri.ttf", 18)
                except:
                    # Final fallback to default
                    font_large = ImageFont.load_default()
                    font_small = ImageFont.load_default()
        
        # Get image dimensions for positioning
        img_width, img_height = template_image.size
        print(f"Debug: Image dimensions: {img_width}x{img_height}")
        
        # Define text colors
        text_color = "#0b2a4a"  # Dark blue color
        
        # Use template placeholders for positioning if available
        placeholders = template.get("placeholders", [])
        
        # Scale factor for placeholder coordinates (assuming placeholders were set on a 1000px wide preview)
        # Scale to actual image dimensions
        scale_x = img_width / 1000.0  # Assuming template editor uses 1000px width
        scale_y = img_height / 1000.0  # Assuming template editor uses 1000px height
        print(f"Debug: Scale factors - X: {scale_x}, Y: {scale_y}")
        
        # Find placeholders for each field
        name_placeholder = next((p for p in placeholders if p["key"] == "student_name"), None)
        date_placeholder = next((p for p in placeholders if p["key"] == "date"), None)
        cert_no_placeholder = next((p for p in placeholders if p["key"] == "certificate_no"), None)
        qr_placeholder = next((p for p in placeholders if p["key"] == "qr_code"), None)
        
        print(f"DEBUG: Found placeholders - Name: {name_placeholder is not None}, Date: {date_placeholder is not None}, Cert No: {cert_no_placeholder is not None}")
        if date_placeholder:
            print(f"DEBUG: Date placeholder x1: {date_placeholder.get('x1')}")
        if cert_no_placeholder:
            print(f"DEBUG: Cert No placeholder x1: {cert_no_placeholder.get('x1')}")
        
        # Initialize position variables
        name_x, name_y = 0, 0
        date_x, date_y = 0, 0
        cert_no_x, cert_no_y = 0, 0
        
        # Position 1: Student Name
        if name_placeholder and name_placeholder.get("x1") is not None:
            # Use rectangle coordinates and scale them
            name_x1 = int(name_placeholder["x1"] * scale_x)
            name_y1 = int(name_placeholder["y1"] * scale_y)
            name_x2 = int(name_placeholder["x2"] * scale_x)
            name_y2 = int(name_placeholder["y2"] * scale_y)
            name_font_size = name_placeholder.get("font_size", 48)
            name_color = name_placeholder.get("color", text_color)
            name_align = name_placeholder.get("text_align", "center")
            name_v_align = name_placeholder.get("vertical_align", "center")
            
            # Load appropriate font size
            try:
                name_font = ImageFont.truetype("storage/fonts/PlayfairDisplay-Bold.ttf", name_font_size)
            except:
                try:
                    name_font = ImageFont.truetype("arial.ttf", name_font_size)
                except:
                    name_font = ImageFont.load_default()
            
            # Calculate text position based on alignment
            name_x, name_y = self._calculate_text_position(
                draw, student_name, name_font, name_x1, name_y1, name_x2, name_y2, name_align, name_v_align
            )
            
            # Draw student name with stroke
            for adj in range(-2, 3):
                for adj2 in range(-2, 3):
                    draw.text((name_x + adj, name_y + adj2), student_name, font=name_font, fill="white")
            draw.text((name_x, name_y), student_name, font=name_font, fill=name_color)
        else:
            # Fallback to default positioning
            name_center_x = img_width // 2
            name_center_y = img_height // 2 - 50
            try:
                bbox = draw.textbbox((0, 0), student_name, font=font_large)
                name_text_width = bbox[2] - bbox[0]
                name_text_height = bbox[3] - bbox[1]
                name_x = name_center_x - (name_text_width // 2)
                name_y = name_center_y - (name_text_height // 2)
            except:
                name_x = name_center_x - 100
                name_y = name_center_y - 20
            
            # Draw student name with stroke
            for adj in range(-2, 3):
                for adj2 in range(-2, 3):
                    draw.text((name_x + adj, name_y + adj2), student_name, font=font_large, fill="white")
            draw.text((name_x, name_y), student_name, font=font_large, fill=text_color)
        
        # Position 2: Date
        if date_placeholder and date_placeholder.get("x1") is not None:
            # Use rectangle coordinates and scale them
            date_x1 = int(date_placeholder["x1"] * scale_x)
            date_y1 = int(date_placeholder["y1"] * scale_y)
            date_x2 = int(date_placeholder["x2"] * scale_x)
            date_y2 = int(date_placeholder["y2"] * scale_y)
            date_font_size = date_placeholder.get("font_size", 18)
            date_color = date_placeholder.get("color", text_color)
            date_align = date_placeholder.get("text_align", "left")
            date_v_align = date_placeholder.get("vertical_align", "center")
            
            print(f"DEBUG: Using rectangle coordinates for date: ({date_x1}, {date_y1}) to ({date_x2}, {date_y2})")
            
            # Load appropriate font size
            try:
                date_font = ImageFont.truetype("storage/fonts/PlayfairDisplay-Bold.ttf", date_font_size)
            except:
                try:
                    date_font = ImageFont.truetype("arial.ttf", date_font_size)
                except:
                    date_font = ImageFont.load_default()
            
            # Calculate text position based on alignment
            date_x, date_y = self._calculate_text_position(
                draw, date_str, date_font, date_x1, date_y1, date_x2, date_y2, date_align, date_v_align
            )
            
            print(f"DEBUG: Calculated date position: ({date_x}, {date_y})")
            
            # Draw date with stroke
            for adj in range(-1, 2):
                for adj2 in range(-1, 2):
                    draw.text((date_x + adj, date_y + adj2), date_str, font=date_font, fill="white")
            draw.text((date_x, date_y), date_str, font=date_font, fill=date_color)
        else:
            # Fallback to default positioning
            date_x = 50
            date_y = img_height - 100
            try:
                bbox = draw.textbbox((0, 0), date_str, font=font_small)
                date_text_height = bbox[3] - bbox[1]
                date_y = date_y - (date_text_height // 2)
            except:
                date_y = date_y - 10
            
            # Draw date with stroke
            for adj in range(-1, 2):
                for adj2 in range(-1, 2):
                    draw.text((date_x + adj, date_y + adj2), date_str, font=font_small, fill="white")
            draw.text((date_x, date_y), date_str, font=font_small, fill=text_color)
        
        # Position 3: Certificate Number
        if cert_no_placeholder and cert_no_placeholder.get("x1") is not None:
            # Use rectangle coordinates and scale them
            cert_no_x1 = int(cert_no_placeholder["x1"] * scale_x)
            cert_no_y1 = int(cert_no_placeholder["y1"] * scale_y)
            cert_no_x2 = int(cert_no_placeholder["x2"] * scale_x)
            cert_no_y2 = int(cert_no_placeholder["y2"] * scale_y)
            cert_no_font_size = cert_no_placeholder.get("font_size", 16)
            cert_no_color = cert_no_placeholder.get("color", text_color)
            cert_no_align = cert_no_placeholder.get("text_align", "left")
            cert_no_v_align = cert_no_placeholder.get("vertical_align", "center")
            
            print(f"DEBUG: Using rectangle coordinates for cert_no: ({cert_no_x1}, {cert_no_y1}) to ({cert_no_x2}, {cert_no_y2})")
            
            # Load appropriate font size
            try:
                cert_no_font = ImageFont.truetype("storage/fonts/PlayfairDisplay-Bold.ttf", cert_no_font_size)
            except:
                try:
                    cert_no_font = ImageFont.truetype("arial.ttf", cert_no_font_size)
                except:
                    cert_no_font = ImageFont.load_default()
            
            # Calculate text position based on alignment
            cert_no_x, cert_no_y = self._calculate_text_position(
                draw, certificate_id, cert_no_font, cert_no_x1, cert_no_y1, cert_no_x2, cert_no_y2, cert_no_align, cert_no_v_align
            )
            
            print(f"DEBUG: Calculated cert_no position: ({cert_no_x}, {cert_no_y})")
            print(f"DEBUG: Cert no text: '{certificate_id}', font size: {cert_no_font_size}, color: {cert_no_color}")
            print(f"DEBUG: Cert no alignment: {cert_no_align}, vertical: {cert_no_v_align}")
            
            # Draw certificate number with stroke
            for adj in range(-1, 2):
                for adj2 in range(-1, 2):
                    draw.text((cert_no_x + adj, cert_no_y + adj2), certificate_id, font=cert_no_font, fill="white")
            draw.text((cert_no_x, cert_no_y), certificate_id, font=cert_no_font, fill=cert_no_color)
            print(f"DEBUG: Certificate number drawn at ({cert_no_x}, {cert_no_y})")
        else:
            # Fallback to default positioning for certificate number
            cert_no_x = img_width - 200  # Right side of image
            cert_no_y = img_height - 50  # Bottom of image
            try:
                bbox = draw.textbbox((0, 0), certificate_id, font=font_small)
                cert_no_text_width = bbox[2] - bbox[0]
                cert_no_text_height = bbox[3] - bbox[1]
                cert_no_x = cert_no_x - cert_no_text_width  # Align to right
                cert_no_y = cert_no_y - (cert_no_text_height // 2)
            except:
                cert_no_x = cert_no_x - 100
                cert_no_y = cert_no_y - 10
            
            # Draw certificate number with stroke
            for adj in range(-1, 2):
                for adj2 in range(-1, 2):
                    draw.text((cert_no_x + adj, cert_no_y + adj2), certificate_id, font=font_small, fill="white")
            draw.text((cert_no_x, cert_no_y), certificate_id, font=font_small, fill=text_color)
        
        print(f"Debug: Text positions - Name: ({name_x}, {name_y}), Date: ({date_x}, {date_y}), Cert No: ({cert_no_x}, {cert_no_y})")
        
        # Generate QR code
        # Get the base URL from environment variable or use production URL
        base_url = os.getenv("BASE_URL", "https://certificate-tb.onrender.com")
        verification_url = f"{base_url}/verify/{certificate_id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(verification_url)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Resize QR code
        qr_size = 150
        qr_image = qr_image.resize((qr_size, qr_size))
        
        # Paste QR code on certificate
        if qr_placeholder and qr_placeholder.get("x1") is not None:
            # Use QR placeholder coordinates and scale them
            qr_x = int(qr_placeholder["x1"] * scale_x)
            qr_y = int(qr_placeholder["y1"] * scale_y)
            print(f"Debug: QR code positioned at placeholder ({qr_x}, {qr_y})")
        else:
            # Default position (bottom-right)
            qr_x = template_image.width - qr_size - 50
            qr_y = template_image.height - qr_size - 50
            print(f"Debug: QR code positioned at default ({qr_x}, {qr_y})")
        
        template_image.paste(qr_image, (qr_x, qr_y))
        
        # Save certificate to Google Drive
        certificate_buffer = BytesIO()
        template_image.save(certificate_buffer, format='PNG')
        certificate_buffer.seek(0)
        
        certificate_drive_result = self.drive_service.upload_from_bytes(
            certificate_buffer.getvalue(), f"{certificate_id}.png", "certificates"
        )
        
        if not certificate_drive_result:
            raise ValueError("Failed to upload certificate to Google Drive")
        
        # Save QR code to Google Drive
        qr_buffer = BytesIO()
        qr_image.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        print(f"[DEBUG] Uploading QR code for certificate {certificate_id}")
        print(f"[DEBUG] QR buffer size: {len(qr_buffer.getvalue())} bytes")
        
        qr_drive_result = self.drive_service.upload_from_bytes(
            qr_buffer.getvalue(), f"{certificate_id}.png", "qr"
        )
        
        print(f"[DEBUG] QR upload result: {qr_drive_result}")
        
        if not qr_drive_result:
            print("[ERROR] QR upload returned None or empty result")
            raise ValueError("Failed to upload QR code to Google Drive")
        
        # Save to student_details collection
        student_data = {
            "certificate_id": certificate_id,
            "template_id": template_id,
            "student_name": student_name,
            "course_name": course_name,
            "date_of_registration": date_str,
            "image_path": certificate_drive_result['image_url'],  # Direct image URL for frontend display
            "qr_path": qr_drive_result['image_url'],  # Direct image URL for frontend display
            "drive_certificate_id": certificate_drive_result['id'],  # Store Drive file ID
            "drive_qr_id": qr_drive_result['id'],  # Store Drive file ID
            "issued_at": datetime.now(),
            "verified": True,
            "revoked": False,
            "student_email": "",  # Can be added later
            "student_phone": "",  # Can be added later
            "student_id": "",  # Can be added later
            "institution": "Tech Buddy Space",  # Default institution
            "grade": "",  # Can be added later
            "instructor": "",  # Can be added later
            "completion_hours": 0,  # Can be added later
            "additional_notes": ""  # Can be added later
        }
        
        self.student_details.insert_one(student_data)
        return student_data

    async def get_certificate(self, certificate_id: str) -> Optional[Dict]:
        """Get certificate by ID"""
        cert = self.student_details.find_one({"certificate_id": certificate_id})
        if cert:
            cert["_id"] = str(cert["_id"])
        return cert

    async def list_certificates(self) -> List[Dict]:
        """List all certificates"""
        certs = list(self.student_details.find({}, {"_id": 0}))
        return certs

    async def revoke_certificate(self, certificate_id: str, reason: str = ""):
        """Revoke a certificate"""
        result = self.student_details.update_one(
            {"certificate_id": certificate_id},
            {
                "$set": {
                    "verified": False,
                    "revoked": True,
                    "revoked_reason": reason,
                    "revoked_at": datetime.now()
                }
            }
        )
        
        if result.matched_count == 0:
            raise ValueError("Certificate not found")

    async def delete_certificate(self, certificate_id: str):
        """Delete a certificate completely from database and Google Drive"""
        # Get certificate details first
        certificate = self.student_details.find_one({"certificate_id": certificate_id})
        if not certificate:
            raise ValueError("Certificate not found")
        
        # Delete files from Google Drive
        try:
            if certificate.get("drive_certificate_id"):
                success = self.drive_service.delete_file(certificate["drive_certificate_id"])
                if success:
                    print(f"Deleted certificate image from Google Drive: {certificate['drive_certificate_id']}")
                else:
                    print(f"Warning: Could not delete certificate image from Google Drive")
        except Exception as e:
            print(f"Warning: Could not delete certificate image from Google Drive: {e}")
        
        try:
            if certificate.get("drive_qr_id"):
                success = self.drive_service.delete_file(certificate["drive_qr_id"])
                if success:
                    print(f"Deleted QR code from Google Drive: {certificate['drive_qr_id']}")
                else:
                    print(f"Warning: Could not delete QR code from Google Drive")
        except Exception as e:
            print(f"Warning: Could not delete QR code from Google Drive: {e}")
        
        # Delete from student_details collection
        result = self.student_details.delete_one({"certificate_id": certificate_id})
        
        if result.deleted_count == 0:
            raise ValueError("Certificate not found")
        
        # Also delete verification logs for this certificate
        try:
            verification_result = self.db.certificates.delete_many({"certificate_id": certificate_id})
            print(f"Deleted {verification_result.deleted_count} verification logs for certificate {certificate_id}")
        except Exception as e:
            print(f"Warning: Could not delete verification logs: {e}")

class QRService:
    def __init__(self):
        pass
    
    def generate_qr(self, data: str, size: int = 150) -> Image.Image:
        """Generate QR code image"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        return qr_image.resize((size, size))
