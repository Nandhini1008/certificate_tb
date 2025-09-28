#!/usr/bin/env python3
"""
Migration script to move data from 'certificates' collection to 'student_details' collection
"""

import os
from pymongo import MongoClient
from datetime import datetime

def migrate_certificates_to_student_details():
    """Migrate certificates collection to student_details collection"""
    
    # MongoDB connection
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/certificatetb")
    client = MongoClient(MONGODB_URL)
    db = client.certificatetb
    
    print("🔄 Starting migration from 'certificates' to 'student_details' collection...")
    
    # Check if certificates collection exists
    if 'certificates' not in db.list_collection_names():
        print("✅ No 'certificates' collection found. Migration not needed.")
        return
    
    # Get all certificates
    certificates = list(db.certificates.find({}))
    print(f"📊 Found {len(certificates)} certificates to migrate")
    
    if not certificates:
        print("✅ No certificates to migrate.")
        return
    
    # Migrate each certificate
    migrated_count = 0
    for cert in certificates:
        # Create student_details document with additional fields
        student_data = {
            "certificate_id": cert.get("certificate_id", ""),
            "template_id": cert.get("template_id", ""),
            "student_name": cert.get("student_name", ""),
            "course_name": cert.get("course_name", ""),
            "date_of_registration": cert.get("date_of_registration", ""),
            "image_path": cert.get("image_path", ""),
            "qr_path": cert.get("qr_path", ""),
            "issued_at": cert.get("issued_at", datetime.now()),
            "verified": cert.get("verified", True),
            "revoked": cert.get("revoked", False),
            "revoked_reason": cert.get("revoked_reason"),
            "revoked_at": cert.get("revoked_at"),
            # New fields with default values
            "student_email": "",
            "student_phone": "",
            "student_id": "",
            "institution": "Tech Buddy Space",
            "grade": "",
            "instructor": "",
            "completion_hours": 0,
            "additional_notes": ""
        }
        
        # Insert into student_details collection
        try:
            db.student_details.insert_one(student_data)
            migrated_count += 1
            print(f"✅ Migrated certificate: {cert.get('certificate_id', 'Unknown')}")
        except Exception as e:
            print(f"❌ Failed to migrate certificate {cert.get('certificate_id', 'Unknown')}: {e}")
    
    print(f"\n🎉 Migration completed! Migrated {migrated_count} out of {len(certificates)} certificates")
    
    # Create indexes for better performance
    print("🔧 Creating indexes...")
    try:
        db.student_details.create_index("certificate_id", unique=True)
        db.student_details.create_index("student_name")
        db.student_details.create_index("course_name")
        db.student_details.create_index("issued_at")
        print("✅ Indexes created successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not create indexes: {e}")
    
    # Ask if user wants to drop the old collection
    response = input("\n❓ Do you want to drop the old 'certificates' collection? (y/N): ")
    if response.lower() in ['y', 'yes']:
        try:
            db.certificates.drop()
            print("✅ Old 'certificates' collection dropped")
        except Exception as e:
            print(f"❌ Failed to drop old collection: {e}")
    else:
        print("ℹ️ Old 'certificates' collection kept for backup")
    
    print("\n✨ Migration completed successfully!")
    print("📝 The system now uses 'student_details' collection for storing certificate data")

if __name__ == "__main__":
    migrate_certificates_to_student_details()
