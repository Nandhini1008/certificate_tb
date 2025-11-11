from pymongo import MongoClient
from typing import List, Optional, Dict, Any
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import asyncio
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
        # Make authentication non-blocking to allow server to start
        try:
            self.drive_service = RobustGoogleDriveService()
            if not self.drive_service.is_authenticated():
                print("[WARNING] Google Drive service not authenticated!")
                print("[WARNING] Please check your GOOGLE_OAUTH_TOKEN environment variable")
                print("[WARNING] Template uploads will fail, but listing templates will work")
                self.drive_service = None
            else:
                print("[SUCCESS] Google Drive service authenticated successfully")
        except Exception as e:
            print(f"[WARNING] Google Drive service initialization failed: {e}")
            print("[WARNING] Template uploads will fail, but listing templates will work")
            self.drive_service = None

    async def upload_template(self, file, template_name: str, description: str = "") -> str:
        """Upload a template image and save metadata"""
        # Check if Google Drive service is available
        if not self.drive_service:
            raise ValueError("Google Drive service is not available. Please check your GOOGLE_OAUTH_TOKEN environment variable.")
        
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
        try:
            # Count templates first for debugging
            count = self.templates.count_documents({})
            print(f"[TEMPLATE SERVICE] Found {count} templates in database")
            
            # Fetch all templates
            templates = list(self.templates.find({}, {"_id": 0}))
            print(f"[TEMPLATE SERVICE] Returning {len(templates)} templates")
            
            # Log template IDs for debugging
            if templates:
                template_ids = [t.get("template_id", "NO_ID") for t in templates]
                print(f"[TEMPLATE SERVICE] Template IDs: {template_ids}")
            else:
                print("[TEMPLATE SERVICE] WARNING: No templates found in database")
            
            return templates
        except Exception as e:
            print(f"[TEMPLATE SERVICE] ERROR listing templates: {e}")
            import traceback
            traceback.print_exc()
            raise

class CertificateService:
    def __init__(self, db):
        self.db = db
        self.student_details = db.student_details
        self.templates = db.templates
        # Use robust service for all environments - no fallback
        # Make authentication non-blocking to allow server to start
        try:
            self.drive_service = RobustGoogleDriveService()
            if not self.drive_service.is_authenticated():
                print("[WARNING] Google Drive service not authenticated!")
                print("[WARNING] Please check your GOOGLE_OAUTH_TOKEN environment variable")
                print("[WARNING] Certificate generation will fail, but other operations will work")
                self.drive_service = None
            else:
                print("[SUCCESS] Google Drive service authenticated successfully for CertificateService")
        except Exception as e:
            print(f"[WARNING] Google Drive service initialization failed for CertificateService: {e}")
            print("[WARNING] Certificate generation will fail, but other operations will work")
            self.drive_service = None

    def _calculate_text_position(self, draw, text, font, x1, y1, x2, y2, text_align, vertical_align, device_type="desktop"):
        """Calculate text position within a rectangle based on alignment settings with device-specific padding"""
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
        
        # Device-specific padding for 2000×1414 canvas
        if device_type == "mobile":
            # Adaptive mobile padding that scales better with rectangle size
            # Use smaller minimum padding and cap maximum padding percentage
            padding_x = max(6, min(rect_width * 0.08, rect_width * 0.12))
            padding_y = max(4, min(rect_height * 0.08, rect_height * 0.15))
        elif device_type == "desktop":
            padding_x = max(5, rect_width * 0.05)  # Standard padding for desktop
            padding_y = max(5, rect_height * 0.05)
        else:
            padding_x = max(6, rect_width * 0.06)  # Balanced padding for unknown devices
            padding_y = max(4, rect_height * 0.08)
        
        print(f"Debug: Text positioning - Text: '{text}', Rectangle: ({x1}, {y1}) to ({x2}, {y2})")
        print(f"Debug: Text positioning - Text size: {text_width}x{text_height}, Rectangle size: {rect_width}x{rect_height}")
        print(f"Debug: Text positioning - Padding: X={padding_x:.1f}, Y={padding_y:.1f}")
        
        # Horizontal alignment with proper padding
        if text_align == "left":
            text_x = x1 + padding_x
        elif text_align == "right":
            text_x = x2 - text_width - padding_x
        else:  # center
            text_x = x1 + (rect_width - text_width) // 2
        
        # Vertical alignment with proper padding
        if vertical_align == "top":
            text_y = y1 + padding_y
        elif vertical_align == "bottom":
            text_y = y2 - text_height - padding_y
        else:  # center
            text_y = y1 + (rect_height - text_height) // 2
        
        # Ensure text stays within rectangle bounds with better constraint handling
        text_x = max(x1 + padding_x, min(text_x, x2 - text_width - padding_x))
        text_y = max(y1 + padding_y, min(text_y, y2 - text_height - padding_y))
        
        # Additional alignment refinement for better positioning
        if text_align == "center":
            # Ensure center alignment is truly centered
            text_x = x1 + (rect_width - text_width) // 2
        elif text_align == "right":
            # Ensure right alignment is properly positioned
            text_x = x2 - text_width - padding_x
        elif text_align == "left":
            # Ensure left alignment is properly positioned
            text_x = x1 + padding_x
        
        if vertical_align == "center":
            # Ensure center alignment is truly centered vertically
            text_y = y1 + (rect_height - text_height) // 2
        elif vertical_align == "bottom":
            # Ensure bottom alignment is properly positioned
            text_y = y2 - text_height - padding_y
        elif vertical_align == "top":
            # Ensure top alignment is properly positioned
            text_y = y1 + padding_y
        
        # Final position validation and adjustment
        # Ensure text is properly positioned within rectangle bounds
        text_x = max(x1 + padding_x, min(text_x, x2 - text_width - padding_x))
        text_y = max(y1 + padding_y, min(text_y, y2 - text_height - padding_y))
        
        print(f"Debug: Final text position - X: {text_x}, Y: {text_y}")
        return text_x, text_y


    async def generate_certificate(self, template_id: str, student_name: str, course_name: str, date_str: str, device_type: str = "desktop", extra_fields: Optional[Dict[str, Any]] = None, student_email: Optional[str] = None) -> Dict:
        """Generate a certificate with text overlay and QR code"""
        # Check if Google Drive service is available
        if not self.drive_service:
            raise ValueError("Google Drive service is not available. Please check your GOOGLE_OAUTH_TOKEN environment variable.")
        
        # Get template
        template = self.templates.find_one({"template_id": template_id})
        if not template:
            raise ValueError("Template not found")
        
        # Generate certificate ID
        certificate_id = generate_certificate_id()
        
        # Load template image (handle both local and Google Drive URLs)
        template_path = template["image_path"]
        
        try:
            if template_path.startswith(('http://', 'https://')):
                # Google Drive URL - use direct image URL
                import requests
                response = requests.get(template_path, timeout=30)
                response.raise_for_status()  # Raise exception for HTTP errors
                template_image = Image.open(BytesIO(response.content))
            else:
                # Local file path
                template_image = Image.open(template_path)
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Template image not accessible from Google Drive: {str(e)}. The template may have been deleted from Google Drive.")
        except Exception as e:
            raise ValueError(f"Failed to load template image: {str(e)}")
        
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
        
        # Fixed resolution system: Always work with 2000×1414 pixel canvas
        # No scaling - use raw pixel coordinates as specified
        fixed_canvas_width = 2000
        fixed_canvas_height = 1414
        
        print(f"Debug: Working with fixed canvas size: {fixed_canvas_width}x{fixed_canvas_height}")
        print(f"Debug: Template image size: {img_width}x{img_height}")
        print(f"Debug: Device type: {device_type}")
        print(f"Debug: Using raw pixel coordinates with device-specific adjustments")
        
        # Device-specific adjustments for fixed resolution system
        device_multiplier = 1.0
        if device_type == "mobile":
            device_multiplier = 1.2  # Larger fonts/padding for mobile readability
            print("Debug: Mobile device detected - applying mobile-friendly adjustments")
        elif device_type == "desktop":
            device_multiplier = 1.0  # Standard sizing for desktop
            print("Debug: Desktop device detected - using standard sizing")
        else:
            device_multiplier = 1.05  # Balanced approach for unknown devices
            print("Debug: Unknown device type - using balanced adjustments")
        
        # Find placeholders for each field
        name_placeholder = next((p for p in placeholders if p["key"] == "student_name"), None)
        date_placeholder = next((p for p in placeholders if p["key"] == "date"), None)
        cert_no_placeholder = next((p for p in placeholders if p["key"] == "certificate_no"), None)
        qr_placeholder = next((p for p in placeholders if p["key"] == "qr_code"), None)
        
        print(f"DEBUG: Found placeholders - Name: {name_placeholder is not None}, Date: {date_placeholder is not None}, Cert No: {cert_no_placeholder is not None}, QR: {qr_placeholder is not None}")
        
        if name_placeholder:
            print(f"DEBUG: Name placeholder - x1: {name_placeholder.get('x1')}, y1: {name_placeholder.get('y1')}, x2: {name_placeholder.get('x2')}, y2: {name_placeholder.get('y2')}, font_size: {name_placeholder.get('font_size')}, color: {name_placeholder.get('color')}")
        if date_placeholder:
            print(f"DEBUG: Date placeholder - x1: {date_placeholder.get('x1')}, y1: {date_placeholder.get('y1')}, x2: {date_placeholder.get('x2')}, y2: {date_placeholder.get('y2')}, font_size: {date_placeholder.get('font_size')}, color: {date_placeholder.get('color')}")
        if cert_no_placeholder:
            print(f"DEBUG: Cert No placeholder - x1: {cert_no_placeholder.get('x1')}, y1: {cert_no_placeholder.get('y1')}, x2: {cert_no_placeholder.get('x2')}, y2: {cert_no_placeholder.get('y2')}, font_size: {cert_no_placeholder.get('font_size')}, color: {cert_no_placeholder.get('color')}")
        if qr_placeholder:
            print(f"DEBUG: QR placeholder - x1: {qr_placeholder.get('x1')}, y1: {qr_placeholder.get('y1')}, x2: {qr_placeholder.get('x2')}, y2: {qr_placeholder.get('y2')}")
        
        # Initialize position variables
        name_x, name_y = 0, 0
        date_x, date_y = 0, 0
        cert_no_x, cert_no_y = 0, 0
        
        # Position 1: Student Name
        # Parse color properly first (needed for both if and else blocks)
        name_color = text_color  # Default color
        if name_placeholder and name_placeholder.get("x1") is not None:
            # Use raw pixel coordinates without scaling (fixed 2000×1414 canvas)
            name_x1 = int(name_placeholder["x1"])
            name_y1 = int(name_placeholder["y1"])
            name_x2 = int(name_placeholder["x2"])
            name_y2 = int(name_placeholder["y2"])
            
            # Parse color from placeholder
            raw_color = name_placeholder.get("color", text_color)
            if raw_color and raw_color.startswith("#"):
                name_color = raw_color
            
            # Use font size with device-specific adjustments
            base_font_size = name_placeholder.get("font_size", 48)
            name_font_size = int(base_font_size * device_multiplier)
            print(f"Debug: Name coordinates - Raw: ({name_x1}, {name_y1}) to ({name_x2}, {name_y2})")
            print(f"Debug: Name font size: {name_font_size}, Color: {name_color}")
            name_align = name_placeholder.get("text_align", "center")
            name_v_align = name_placeholder.get("vertical_align", "center")
            
            # Load appropriate font size with better fallback
            name_font = None
            
            # Try multiple font paths with proper error handling
            # Use Radley font first for certificate inputs, then fallbacks
            font_paths = [
                "fonts/radley.ttf",  # Radley font (primary for certificate inputs)
                "fonts/arial.ttf",  # Deployment font (fallback)
                "arial.ttf",  # System Arial
                "Arial.ttf",  # System Arial (capital)
                "C:/Windows/Fonts/arial.ttf",  # Windows Arial
                "C:/Windows/Fonts/calibri.ttf",  # Windows Calibri
                "C:/Windows/Fonts/tahoma.ttf",  # Windows Tahoma
                "/System/Library/Fonts/Arial.ttf",  # macOS Arial
                "/System/Library/Fonts/Helvetica.ttc",  # macOS Helvetica
                "/usr/share/fonts/truetype/arial.ttf",  # Linux Arial
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux DejaVu
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux Liberation
            ]
            
            for font_path in font_paths:
                try:
                    name_font = ImageFont.truetype(font_path, name_font_size)
                    print(f"Debug: Successfully loaded font: {font_path} at size {name_font_size}")
                    break
                except Exception as e:
                    print(f"Debug: Failed to load {font_path}: {e}")
                    continue
            
            if name_font is None:
                # Last resort: use default font with size tracking
                try:
                    name_font = ImageFont.load_default()
                    print(f"Debug: Using default font (requested size: {name_font_size})")
                    # Store the requested size for reference
                    name_font.requested_size = name_font_size
                except Exception as e:
                    print(f"Debug: Complete font loading failure: {e}")
                    name_font = ImageFont.load_default()
                    name_font.requested_size = name_font_size
            
            # Calculate text position based on alignment (fixed resolution with device adjustments)
            name_x, name_y = self._calculate_text_position(
                draw, student_name, name_font, name_x1, name_y1, name_x2, name_y2, name_align, name_v_align, device_type
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
        # Parse color properly first (needed for both if and else blocks)
        date_color = text_color  # Default color
        if date_placeholder and date_placeholder.get("x1") is not None:
            # Use raw pixel coordinates without scaling (fixed 2000×1414 canvas)
            date_x1 = int(date_placeholder["x1"])
            date_y1 = int(date_placeholder["y1"])
            date_x2 = int(date_placeholder["x2"])
            date_y2 = int(date_placeholder["y2"])
            
            # Parse color from placeholder
            raw_date_color = date_placeholder.get("color", text_color)
            if raw_date_color and raw_date_color.startswith("#"):
                date_color = raw_date_color
            
            # Use font size with device-specific adjustments
            base_date_font_size = date_placeholder.get("font_size", 18)
            date_font_size = int(base_date_font_size * device_multiplier)
            print(f"Debug: Date coordinates - Raw: ({date_x1}, {date_y1}) to ({date_x2}, {date_y2})")
            date_align = date_placeholder.get("text_align", "left")
            date_v_align = date_placeholder.get("vertical_align", "center")
            
            print(f"DEBUG: Using rectangle coordinates for date: ({date_x1}, {date_y1}) to ({date_x2}, {date_y2})")
            
            # Load appropriate font size with better fallback
            date_font = None
            
            # Try multiple font paths with proper error handling
            # Use Radley font first for certificate inputs, then fallbacks
            font_paths = [
                "fonts/radley.ttf",  # Radley font (primary for certificate inputs)
                "fonts/arial.ttf",  # Deployment font (fallback)
                "arial.ttf",  # System Arial
                "Arial.ttf",  # System Arial (capital)
                "C:/Windows/Fonts/arial.ttf",  # Windows Arial
                "C:/Windows/Fonts/calibri.ttf",  # Windows Calibri
                "C:/Windows/Fonts/tahoma.ttf",  # Windows Tahoma
                "/System/Library/Fonts/Arial.ttf",  # macOS Arial
                "/System/Library/Fonts/Helvetica.ttc",  # macOS Helvetica
                "/usr/share/fonts/truetype/arial.ttf",  # Linux Arial
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux DejaVu
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux Liberation
            ]
            
            print(f"Debug: Attempting to load date font with size {date_font_size}")
            
            for font_path in font_paths:
                try:
                    date_font = ImageFont.truetype(font_path, date_font_size)
                    print(f"Debug: Successfully loaded date font: {font_path} at size {date_font_size}")
                    break
                except Exception as e:
                    print(f"Debug: Failed to load date font {font_path}: {e}")
                    continue
            
            if date_font is None:
                # Last resort: use default font with size tracking
                try:
                    date_font = ImageFont.load_default()
                    print(f"Debug: Using default date font (requested size: {date_font_size})")
                    date_font.requested_size = date_font_size
                except Exception as e:
                    print(f"Debug: Complete date font loading failure: {e}")
                    date_font = ImageFont.load_default()
                    date_font.requested_size = date_font_size
            
            # Calculate text position based on alignment (fixed resolution with device adjustments)
            date_x, date_y = self._calculate_text_position(
                draw, date_str, date_font, date_x1, date_y1, date_x2, date_y2, date_align, date_v_align, device_type
            )
            
            print(f"DEBUG: Calculated date position: ({date_x}, {date_y})")
            print(f"DEBUG: Date alignment: {date_align}, vertical: {date_v_align}")
            print(f"DEBUG: Date text: '{date_str}', font size: {date_font_size}, color: {date_color}")
            
            # Draw date with stroke (template already has "Date:" label)
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
        # Parse color properly first (needed for both if and else blocks)
        cert_no_color = text_color  # Default color
        if cert_no_placeholder and cert_no_placeholder.get("x1") is not None:
            # Use raw pixel coordinates without scaling (fixed 2000×1414 canvas)
            cert_no_x1 = int(cert_no_placeholder["x1"])
            cert_no_y1 = int(cert_no_placeholder["y1"])
            cert_no_x2 = int(cert_no_placeholder["x2"])
            cert_no_y2 = int(cert_no_placeholder["y2"])
            
            # Parse color from placeholder
            raw_cert_no_color = cert_no_placeholder.get("color", text_color)
            if raw_cert_no_color and raw_cert_no_color.startswith("#"):
                cert_no_color = raw_cert_no_color
            
            # Use font size with device-specific adjustments
            base_cert_no_font_size = cert_no_placeholder.get("font_size", 16)
            cert_no_font_size = int(base_cert_no_font_size * device_multiplier)
            print(f"Debug: Cert No coordinates - Raw: ({cert_no_x1}, {cert_no_y1}) to ({cert_no_x2}, {cert_no_y2})")
            cert_no_align = cert_no_placeholder.get("text_align", "left")
            cert_no_v_align = cert_no_placeholder.get("vertical_align", "center")
            
            print(f"DEBUG: Using rectangle coordinates for cert_no: ({cert_no_x1}, {cert_no_y1}) to ({cert_no_x2}, {cert_no_y2})")
            
            # Load appropriate font size with better fallback
            cert_no_font = None
            
            # Try multiple font paths with proper error handling
            # Use Radley font first for certificate inputs, then fallbacks
            font_paths = [
                "fonts/radley.ttf",  # Radley font (primary for certificate inputs)
                "fonts/arial.ttf",  # Deployment font (fallback)
                "arial.ttf",  # System Arial
                "Arial.ttf",  # System Arial (capital)
                "C:/Windows/Fonts/arial.ttf",  # Windows Arial
                "C:/Windows/Fonts/calibri.ttf",  # Windows Calibri
                "C:/Windows/Fonts/tahoma.ttf",  # Windows Tahoma
                "/System/Library/Fonts/Arial.ttf",  # macOS Arial
                "/System/Library/Fonts/Helvetica.ttc",  # macOS Helvetica
                "/usr/share/fonts/truetype/arial.ttf",  # Linux Arial
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux DejaVu
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux Liberation
            ]
            
            for font_path in font_paths:
                try:
                    cert_no_font = ImageFont.truetype(font_path, cert_no_font_size)
                    print(f"Debug: Successfully loaded cert_no font: {font_path} at size {cert_no_font_size}")
                    break
                except Exception as e:
                    print(f"Debug: Failed to load cert_no font {font_path}: {e}")
                    continue
            
            if cert_no_font is None:
                # Last resort: use default font with size tracking
                try:
                    cert_no_font = ImageFont.load_default()
                    print(f"Debug: Using default cert_no font (requested size: {cert_no_font_size})")
                    cert_no_font.requested_size = cert_no_font_size
                except Exception as e:
                    print(f"Debug: Complete cert_no font loading failure: {e}")
                    cert_no_font = ImageFont.load_default()
                    cert_no_font.requested_size = cert_no_font_size
            
            # Calculate text position based on alignment (fixed resolution with device adjustments)
            cert_no_x, cert_no_y = self._calculate_text_position(
                draw, certificate_id, cert_no_font, cert_no_x1, cert_no_y1, cert_no_x2, cert_no_y2, cert_no_align, cert_no_v_align, device_type
            )
            
            print(f"DEBUG: Calculated cert_no position: ({cert_no_x}, {cert_no_y})")
            print(f"DEBUG: Cert no text: '{certificate_id}', font size: {cert_no_font_size}, color: {cert_no_color}")
            print(f"DEBUG: Cert no alignment: {cert_no_align}, vertical: {cert_no_v_align}")
            
            # Draw certificate number with stroke (template already has "Certificate No:" label)
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
            # Use raw pixel coordinates without scaling (fixed 2000×1414 canvas)
            qr_x = int(qr_placeholder["x1"])
            qr_y = int(qr_placeholder["y1"])
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
            certificate_buffer.getvalue(), f"{certificate_id}.png", "certificates", max_retries=3
        )
        
        if not certificate_drive_result:
            print(f"[ERROR] Failed to upload certificate to Google Drive after retries")
            # Try to save locally as fallback
            try:
                local_path = f"storage/certificates/{certificate_id}.png"
                os.makedirs("storage/certificates", exist_ok=True)
                with open(local_path, "wb") as f:
                    f.write(certificate_buffer.getvalue())
                print(f"[FALLBACK] Certificate saved locally: {local_path}")
                # Use local URL as fallback
                certificate_drive_result = {
                    "id": "local_" + certificate_id,
                    "image_url": f"/storage/certificates/{certificate_id}.png",
                    "webViewLink": f"/storage/certificates/{certificate_id}.png",
                    "webContentLink": f"/storage/certificates/{certificate_id}.png"
                }
            except Exception as fallback_error:
                print(f"[ERROR] Fallback save also failed: {fallback_error}")
                raise ValueError("Failed to upload certificate to Google Drive and fallback save failed")
        
        # Save QR code to Google Drive
        qr_buffer = BytesIO()
        qr_image.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        print(f"[DEBUG] Uploading QR code for certificate {certificate_id}")
        print(f"[DEBUG] QR buffer size: {len(qr_buffer.getvalue())} bytes")
        
        qr_drive_result = self.drive_service.upload_from_bytes(
            qr_buffer.getvalue(), f"{certificate_id}.png", "qr", max_retries=3
        )
        
        print(f"[DEBUG] QR upload result: {qr_drive_result}")
        
        if not qr_drive_result:
            print(f"[ERROR] Failed to upload QR code to Google Drive after retries")
            # Try to save locally as fallback
            try:
                local_qr_path = f"storage/qr/{certificate_id}.png"
                os.makedirs("storage/qr", exist_ok=True)
                with open(local_qr_path, "wb") as f:
                    f.write(qr_buffer.getvalue())
                print(f"[FALLBACK] QR code saved locally: {local_qr_path}")
                # Use local URL as fallback
                qr_drive_result = {
                    "id": "local_qr_" + certificate_id,
                    "image_url": f"/storage/qr/{certificate_id}.png",
                    "webViewLink": f"/storage/qr/{certificate_id}.png",
                    "webContentLink": f"/storage/qr/{certificate_id}.png"
                }
            except Exception as fallback_error:
                print(f"[ERROR] QR fallback save also failed: {fallback_error}")
                # Continue without QR code
                qr_drive_result = None
        
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
            "image_path": certificate_drive_result['image_url'],  # Display URL for frontend
            "image_download_url": certificate_drive_result.get('download_url', certificate_drive_result['image_url']),  # Download URL
            "qr_path": qr_drive_result['image_url'],  # Display URL for frontend
            "qr_download_url": qr_drive_result.get('download_url', qr_drive_result['image_url']),  # Download URL
            "drive_certificate_id": certificate_drive_result['id'],  # Store Drive file ID
            "drive_qr_id": qr_drive_result['id'],  # Store Drive file ID
            "issued_at": datetime.now(),
            "verified": True,
            "revoked": False,
            "student_email": (student_email or ""),
            "student_phone": "",  # Can be added later
            "student_id": "",  # Can be added later
            "institution": "Tech Buddy Space",  # Default institution
            "grade": "",  # Can be added later
            "instructor": "",  # Can be added later
            "completion_hours": 0,  # Can be added later
            "additional_notes": ""  # Can be added later
        }

        # Merge extra CSV fields generically, skipping empty values and reserved keys
        reserved_keys = set(student_data.keys())
        if extra_fields:
            for key, value in extra_fields.items():
                try:
                    if key in reserved_keys:
                        continue
                    if value is None:
                        continue
                    value_str = str(value).strip()
                    if not value_str:
                        continue
                    student_data[key] = value_str
                except Exception:
                    continue

        # Persist
        
        self.student_details.insert_one(student_data)

        # Fire-and-forget email if email is available
        try:
            if student_email:
                download_url = student_data.get("image_download_url", student_data.get("image_path"))
                verify_url = f"https://certificate-tb.onrender.com/verify/{certificate_id}"
                print(f"[EMAIL] Attempting SMTP to {student_email} for {certificate_id}")
                await asyncio.to_thread(self._send_certificate_email_sync,
                    to_email=student_email,
                    student_name=student_name,
                    course_name=course_name,
                    certificate_id=certificate_id,
                    date_str=date_str,
                    download_url=download_url,
                    verify_url=verify_url
                )
            else:
                print("[EMAIL] No student_email provided; skipping send")
        except Exception as e:
            print(f"[WARN] Failed to send certificate email to {student_email}: {e}")

        return student_data

    def _send_certificate_email_sync(self, to_email: str, student_name: str, course_name: str, certificate_id: str, date_str: str, download_url: str, verify_url: str):
        print(f"[EMAIL] Starting email send to {to_email} for {student_name}")
        
        # Gmail credentials from environment or defaults
        email = os.getenv("SMTP_USER", "techbuddyspace@gmail.com")
        password = os.getenv("SMTP_PASS", "cbjg sogl ejyj tkrq")
        
        print(f"[EMAIL] Using SMTP user: {email}")
        
        if not (email and password):
            print("[WARN] SMTP credentials not configured; skipping email send")
            return

        # Gmail SMTP setup (matching send_mail.py pattern)
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(email, password)
            print(f"[EMAIL] Successfully connected to SMTP server")
        except Exception as e:
            print(f"[ERROR] Failed to connect to SMTP server: {e}")
            return

        # Create the email
        message = MIMEMultipart("alternative")
        message["Subject"] = f"🎉 Your Certificate - {course_name}"
        message["From"] = email
        message["To"] = to_email

        # Email body HTML template
        html = f"""
<html>
<body style="font-family: 'Segoe UI', sans-serif; background-color: #f4f4f4; margin: 0; padding: 0;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">

          <!-- Header / Logo -->
          <tr>
            <td style="background-color: #ff6f00; padding: 20px; text-align: center;">
              <img src="https://ik.imagekit.io/jocb2rx3k/TBSPACE.jpg?updatedAt=1752305312016" alt="TechBuddySpace Logo" width="140" style="border-radius: 8px;" />
            </td>
          </tr>

          <!-- Email Body -->
          <tr>
            <td style="padding: 30px; color: #333;">
              <h2 style="margin-top: 0; color: #333;">Hey Buddy, 🎉</h2>

              <p style="font-size: 16px; line-height: 1.6;">
                Congratulations! 🎊 You’ve successfully completed the <strong>Career Catalyst Program</strong> — and you’ve truly earned your certificate!
              </p>

              <p style="font-size: 16px; line-height: 1.6;">
                Your <em>activeness</em>, <strong>eagerness to learn</strong>, <strong>dedication</strong>, and <strong>commitment</strong> to completing every task have been outstanding.
              </p>

              <p style="font-size: 16px; line-height: 1.6;">
                Over the past <strong>9 days of learning</strong>, you’ve consistently shown curiosity, asked meaningful questions, and completed each challenge with excellence.
              </p>

              <p style="font-size: 16px; line-height: 1.6;">
                Out of many participants, only a few truly ace it — and you’re one of them! You deserve a big <strong>Kudos</strong> for your hard work and passion for learning. 🌟
              </p>

              <p style="font-size: 16px; line-height: 1.6;">
                If you ever need any <strong>guidance or help</strong>, feel free to reach out to us anytime. We’re always here to support your journey of growth and innovation.
              </p>

              <p style="font-size: 16px; line-height: 1.6;">
                Keep shining and keep learning! 🚀
              </p>

              <p style="font-size: 16px; margin-top: 30px;">
                <strong>Warm regards,</strong><br>
                <span style="font-weight: bold;">Team TechBuddySpace</span><br>
                <a href="mailto:techbuddyspace@gmail.com" style="color: #2563eb; text-decoration: none;">techbuddyspace@gmail.com</a><br>
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #fafafa; padding: 25px; text-align: center; font-size: 14px; color: #555;">
              <p style="margin: 0 0 15px;">👋 Need help or want to stay connected? Reach out anytime!</p>

              <!-- Social & Contact Icons -->
              <table role="presentation" align="center" cellpadding="0" cellspacing="0" style="margin: 0 auto;">
                <tr>
                  <!-- Website -->
                  <td style="padding: 0 12px;">
                    <a href="https://techbuddyspace.xyz" target="_blank">
                      <img src="https://certificate-tb.onrender.com/static/logo.jpg" alt="Website" width="28" style="vertical-align: middle;" />
                    </a>
                  </td>

                  <!-- Email -->
                  <td style="padding: 0 12px;">
                    <a href="mailto:techbuddyspace@gmail.com">
                      <img src="https://cdn-icons-png.flaticon.com/512/732/732200.png" alt="Email" width="28" style="vertical-align: middle;" />
                    </a>
                  </td>

                  <!-- Phone -->
                  <td style="padding: 0 12px;">
                    <a href="tel:+919600338406">
                      <img src="https://cdn-icons-png.flaticon.com/512/597/597177.png" alt="Call" width="28" style="vertical-align: middle;" />
                    </a>
                  </td>

                  <!-- Instagram -->
                  <td style="padding: 0 12px;">
                    <a href="https://instagram.com/techbuddyspace" target="_blank">
                      <img src="https://cdn-icons-png.flaticon.com/512/174/174855.png" alt="Instagram" width="28" style="vertical-align: middle;" />
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin-top: 20px; font-size: 13px; color: #aaa;">
                © 2025 TechBuddySpace – Made with ❤ by students, for students.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

        # Attach HTML
        message.attach(MIMEText(html, "html"))

        # Try to fetch and attach the certificate image
        try:
            import requests
            print(f"[EMAIL] Attempting to download certificate from: {download_url}")
            resp = requests.get(download_url, timeout=30)
            if resp.ok and resp.content:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(resp.content)
                encoders.encode_base64(part)
                filename = f"{student_name.replace(' ', '_')}_{certificate_id}.png"
                part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                message.attach(part)
                print(f"[EMAIL] Certificate image attached: {filename}")
            else:
                print(f"[EMAIL] Warning: Could not download certificate image (Status: {resp.status_code})")
        except Exception as e:
            print(f"[EMAIL] Info: Could not attach certificate file; sending email without attachment. Reason: {e}")

        # Send the email (matching send_mail.py pattern)
        try:
            server.sendmail(email, to_email, message.as_string())
            print(f"✅ Sent to {student_name} <{to_email}>")
        except Exception as e:
            print(f"❌ Failed to send to {to_email}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Close server (matching send_mail.py pattern)
            try:
                server.quit()
            except:
                pass


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
