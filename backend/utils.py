import secrets
import string
from datetime import datetime

def generate_certificate_id() -> str:
    """Generate a unique certificate ID in format TBS-YYYYMMDD-XXXXXX"""
    date_str = datetime.now().strftime('%Y%m%d')
    random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"TBS-{date_str}-{random_suffix}"

def generate_template_id() -> str:
    """Generate a unique template ID in format TPL-YYYYMMDD-XXXXXX"""
    date_str = datetime.now().strftime('%Y%m%d')
    random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"TPL-{date_str}-{random_suffix}"
