"""
Email sending utility for Tech Buddy Space
Supports single email and bulk email sending from CSV
"""

import pandas as pd
import smtplib
import ssl
import sys
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
import os

# Gmail credentials - Use environment variables
EMAIL = os.getenv("SMTP_USER", "")
PASSWORD = os.getenv("SMTP_PASS", "")

if not EMAIL or not PASSWORD:
    raise ValueError("SMTP_USER and SMTP_PASS environment variables are required")

# Gmail SMTP setup
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"

# Contact information from config
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", EMAIL)
CONTACT_PHONE = os.getenv("CONTACT_PHONE", "+919600338406")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://tech-buddy-space.vercel.app/")
INSTAGRAM_URL = os.getenv("INSTAGRAM_URL", "https://instagram.com/techbuddyspace")


def get_smtp_server():
    """Get SMTP server connection using STARTTLS only"""
    smtp_timeout = 15
    
    # Try STARTTLS on configured port first, then fallback to 587
    ports_to_try = [SMTP_PORT, 587]
    
    for port in ports_to_try:
        try:
            print(f"[EMAIL] Attempting STARTTLS connection to {SMTP_HOST}:{port}")
            context = ssl.create_default_context()
            server = smtplib.SMTP(SMTP_HOST, port, timeout=smtp_timeout)
            server.starttls(context=context)
            server.login(EMAIL, PASSWORD)
            print(f"[EMAIL] ✅ Successfully connected via STARTTLS ({SMTP_HOST}:{port})")
            return server
            
        except Exception as e:
            print(f"[EMAIL] ❌ STARTTLS connection to port {port} failed: {type(e).__name__}: {e}")
            if 'server' in locals():
                try:
                    server.quit()
                except:
                    pass
            continue
    
    raise ConnectionError(f"Failed to connect to SMTP server via STARTTLS on ports {ports_to_try}")


def build_email_html(name: str) -> str:
    """Build the email HTML content"""
    return f"""
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
              <h2 style="margin-top: 0; color: #333;">🎉 Welcome to the Buddy Gang!</h2>
              <p style="font-size: 16px;">Hi {name},</p>

              <p style="font-size: 16px; line-height: 1.6;">
                Welcome to our <strong>Buddy Gang 🧡</strong>!  
                You just unlocked your <strong>One Life Token</strong> by joining the <strong>9-Day Career Catalyst Bootcamp</strong> – and trust us, this isn't another boring webinar or scammy sales pitch.
              </p>

              <p style="font-size: 16px; line-height: 1.6;">
                This is <strong>9 days of pure action</strong> — 9 tasks, 9 lessons, and a transformation that will help you build a <strong>standout profile</strong>, understand your <strong>career path clearly</strong>, and feel <strong>ahead of the crowd</strong>.
              </p>

              <p style="font-size: 16px; line-height: 1.6;">
                We know what you might be thinking:<br/>
                <em>"Oh, another course from some IIT/IIM/Google guy talking about success?"</em><br/>
                But <strong>nah, this is different</strong>. This is <strong>for students, by students</strong>, and we're building a real space where your learning is our only agenda.
              </p>

              <p style="font-size: 16px; line-height: 1.6;">By the end of these 9 days, you'll not only <strong>learn</strong> but also <strong>do</strong>:</p>
              
              <ul style="font-size: 16px; line-height: 1.8; padding-left: 20px;">
                <li>✔ GitHub</li>
                <li>✔ LinkedIn branding</li>
                <li>✔ Resume that gets attention</li>
                <li>✔ Real community support</li>
                <li>✔ No fluff. No overpriced junk. Just results.</li>
              </ul>

              <p style="font-size: 16px; line-height: 1.6;">
                You choosing us over the noise out there means <strong>everything</strong>.<br/>
                <strong>Your success = our success.</strong>
              </p>

              <p style="font-size: 16px; line-height: 1.6;">
                So, thank you for trusting our path, our team, and our mission.<br/>
                Let's show the world what students can build <strong>together 💪</strong>
              </p>

              <p style="font-size: 16px; line-height: 1.6;"><strong>Stay tuned</strong> – you'll get Day 1 details shortly. Don't miss a single day of this amazing ride!</p>

              <!-- CTA Button -->
              <div style="text-align: center; margin: 30px 0;">
                <a href="https://chat.whatsapp.com/CxCK2FEcSeIGavpidafzxX" style="background-color: #25d366; color: white; padding: 14px 28px; border-radius: 6px; text-decoration: none; font-weight: bold;">💬 Join WhatsApp Community</a>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #fafafa; padding: 30px; text-align: center; font-size: 14px; color: #555;">
              <p style="margin: 0 0 10px;">👋 If you have any questions, feel free to <strong>reach out</strong> anytime.</p>
              <p style="margin: 0 0 20px;">Or visit our website to learn more about what we do.</p>

              <!-- Horizontal contact icons with links -->
              <table role="presentation" align="center" cellpadding="0" cellspacing="0" style="margin: 0 auto;">
                <tr>
                  <td style="padding: 0 12px;">
                    <a href="mailto:{CONTACT_EMAIL}" style="color: #888; text-decoration: none;">
                      📧 <span style="text-decoration: underline;">Email</span>
                    </a>
                  </td>
                  <td style="padding: 0 12px;">
                    <a href="tel:{CONTACT_PHONE}" style="color: #888; text-decoration: none;">
                      📞 <span style="text-decoration: underline;">{CONTACT_PHONE}</span>
                    </a>
                  </td>
                  <td style="padding: 0 12px;">
                    <a href="{WEBSITE_URL}" target="_blank" style="color: #888; text-decoration: none;">
                      🌐 <span style="text-decoration: underline;">Website</span>
                    </a>
                  </td>
                  <td style="padding: 0 12px;">
                    <a href="{INSTAGRAM_URL}" target="_blank" style="color: #888; text-decoration: none;">
                      📸 <span style="text-decoration: underline;">Instagram</span>
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin-top: 20px; font-size: 13px; color: #aaa;">© 2025 TechBuddySpace – Made with ❤ by students, for students.</p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def send_single_email(name: str, recipient: str, subject: str = "🎉 Welcome to TechBuddySpace!") -> bool:
    """Send a single email to one recipient"""
    try:
        # Get SMTP server connection
        server = get_smtp_server()
        
        # Create the email
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = EMAIL
        message["To"] = recipient

        # Build email HTML
        html = build_email_html(name)

        # Attach HTML
        message.attach(MIMEText(html, "html"))

        # Send the email
        server.sendmail(EMAIL, recipient, message.as_string())
        print(f"✅ Sent to {name} <{recipient}>")
        
        # Close server
        server.quit()
        return True
        
    except Exception as e:
        print(f"❌ Failed to send to {recipient}: {e}")
        return False


def send_bulk_emails(csv_file_path: str, name_column: str = "name", email_column: str = "email") -> Dict:
    """Send bulk emails from CSV file"""
    try:
        # Load CSV data
        df = pd.read_excel(csv_file_path) if csv_file_path.endswith('.xlsx') else pd.read_csv(csv_file_path)
        
        # Validate columns
        if name_column not in df.columns:
            raise ValueError(f"Column '{name_column}' not found in CSV. Available columns: {list(df.columns)}")
        if email_column not in df.columns:
            raise ValueError(f"Column '{email_column}' not found in CSV. Available columns: {list(df.columns)}")
        
        print(f"📧 Found {len(df)} recipients in CSV file")
        
        # Get SMTP server connection (reuse for all emails)
        server = get_smtp_server()
        
        results = {
            "total": len(df),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        # Send email to each recipient
        for index, row in df.iterrows():
            name = str(row[name_column]).strip()
            recipient = str(row[email_column]).strip()
            
            if not name or not recipient:
                results["failed"] += 1
                results["errors"].append({
                    "row": index + 1,
                    "name": name or "Unknown",
                    "email": recipient or "Unknown",
                    "error": "Name or email is empty"
                })
                continue
            
            try:
                # Create the email
                message = MIMEMultipart("alternative")
                message["Subject"] = "🎉 Welcome to TechBuddySpace!"
                message["From"] = EMAIL
                message["To"] = recipient

                # Build email HTML
                html = build_email_html(name)

                # Attach HTML
                message.attach(MIMEText(html, "html"))

                # Send the email
                server.sendmail(EMAIL, recipient, message.as_string())
                print(f"✅ [{index + 1}/{len(df)}] Sent to {name} <{recipient}>")
                results["successful"] += 1
                
            except Exception as e:
                print(f"❌ [{index + 1}/{len(df)}] Failed to send to {name} <{recipient}>: {e}")
                results["failed"] += 1
                results["errors"].append({
                    "row": index + 1,
                    "name": name,
                    "email": recipient,
                    "error": str(e)
                })
        
        # Close server
        server.quit()
        
        print(f"\n📊 Summary: {results['successful']} successful, {results['failed']} failed out of {results['total']} total")
        return results
        
    except Exception as e:
        print(f"❌ Error processing bulk emails: {e}")
        raise


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="Send emails via SMTP")
    parser.add_argument("--name", type=str, help="Recipient name (for single email)")
    parser.add_argument("--email", type=str, help="Recipient email (for single email)")
    parser.add_argument("--csv", type=str, help="CSV file path (for bulk emails)")
    parser.add_argument("--name-column", type=str, default="name", help="Name column name in CSV (default: 'name')")
    parser.add_argument("--email-column", type=str, default="email", help="Email column name in CSV (default: 'email')")
    parser.add_argument("--subject", type=str, default="🎉 Welcome to TechBuddySpace!", help="Email subject")
    
    args = parser.parse_args()
    
    if args.csv:
        # Bulk email mode
        print(f"📧 Starting bulk email sending from {args.csv}")
        results = send_bulk_emails(args.csv, args.name_column, args.email_column)
        sys.exit(0 if results["failed"] == 0 else 1)
    elif args.name and args.email:
        # Single email mode
        print(f"📧 Sending email to {args.name} <{args.email}>")
        success = send_single_email(args.name, args.email, args.subject)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
