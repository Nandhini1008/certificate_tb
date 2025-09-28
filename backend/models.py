from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

class Placeholder(BaseModel):
    key: str
    x: int
    y: int
    font: str = "fonts/PlayfairDisplay-Bold.ttf"
    font_size: int = 48
    color: str = "#0b2a4a"
    # Rectangle coordinates for precise positioning
    x1: Optional[int] = None
    y1: Optional[int] = None
    x2: Optional[int] = None
    y2: Optional[int] = None
    # Text alignment within rectangle
    text_align: str = "center"  # "center", "left", "right"
    vertical_align: str = "center"  # "center", "top", "bottom"

class Template(BaseModel):
    template_id: str
    name: str
    description: str = ""
    image_path: str
    placeholders: List[Placeholder] = []
    uploaded_at: datetime

class StudentDetails(BaseModel):
    certificate_id: str
    template_id: str
    student_name: str
    course_name: str
    date_of_registration: str
    image_path: str
    qr_path: str
    issued_at: datetime
    verified: bool = True
    revoked: bool = False
    revoked_reason: Optional[str] = None
    revoked_at: Optional[datetime] = None
    student_email: Optional[str] = ""
    student_phone: Optional[str] = ""
    student_id: Optional[str] = ""
    institution: str = "Tech Buddy Space"
    grade: Optional[str] = ""
    instructor: Optional[str] = ""
    completion_hours: int = 0
    additional_notes: Optional[str] = ""

# Keep Certificate for backward compatibility
Certificate = StudentDetails

class TemplateUpload(BaseModel):
    template_name: str
    description: str = ""

class CertificateGeneration(BaseModel):
    template_id: str
    student_name: str
    course_name: str
    date_str: str

class CertificateRevocation(BaseModel):
    reason: str = ""
