import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# # Load Excel data
# df = pd.read_excel("career.xlsx")

# Gmail credentials - Use environment variables
import os
EMAIL = os.getenv("SMTP_USER", "")
PASSWORD = os.getenv("SMTP_PASS", "")

if not EMAIL or not PASSWORD:
    raise ValueError("SMTP_USER and SMTP_PASS environment variables are required")

# Gmail SMTP setup
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
server.starttls()
server.login(EMAIL, PASSWORD)

# # Loop through Excel data
# for index, row in df.iterrows():
name = "nandy"
recipient = "nandhiniprakashofficial@gmail.com"
#"jayaneshdhanakkotti@gmail.com"

    # Create the email
message = MIMEMultipart("alternative")
message["Subject"] = "🎉 Welcome to TechBuddySpace!"
message["From"] = EMAIL
message["To"] = recipient

# Email body
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
              <h2 style="margin-top: 0; color: #333;">🎉 Welcome to the Buddy Gang!</h2>
              <p style="font-size: 16px;">Hi {name}</strong>,</p>

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
                But <strong>nah, this is different</strong>. This is <strong>for students, by students</strong>, and we’re building a real space where your learning is our only agenda.
              </p>

              <p style="font-size: 16px; line-height: 1.6;">By the end of these 9 days, you’ll not only <strong>learn</strong> but also <strong>do</strong>:</p>
              
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
                Let’s show the world what students can build <strong>together 💪</strong>
              </p>

              <p style="font-size: 16px; line-height: 1.6;"><strong>Stay tuned</strong> – you’ll get Day 1 details shortly. Don’t miss a single day of this amazing ride!</p>

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
          <a href="mailto:{EMAIL}" style="color: #888; text-decoration: none;">
            📧 <span style="text-decoration: underline;">Email</span>
          </a>
        </td>
        <td style="padding: 0 12px;">
          <a href="tel:+919600338406" style="color: #888; text-decoration: none;">
            📞 <span style="text-decoration: underline;">+91 9600338406</span>
          </a>
        </td>
        <td style="padding: 0 12px;">
          <a href="https://tech-buddy-space.vercel.app/" target="_blank" style="color: #888; text-decoration: none;">
            🌐 <span style="text-decoration: underline;">Website</span>
          </a>
        </td>
        <td style="padding: 0 12px;">
          <a href="https://instagram.com/techbuddyspace" target="_blank" style="color: #888; text-decoration: none;">
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

# Attach HTML
message.attach(MIMEText(html, "html"))

# Send the email
try:
    server.sendmail(EMAIL, recipient, message.as_string())
    print(f"✅ Sent to {name} <{recipient}>")
except Exception as e:
    print(f"❌ Failed to send to {recipient}: {e}")

# Close server
server.quit()