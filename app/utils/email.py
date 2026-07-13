# app/utils/email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def send_reset_password_email(recipient_email: str, reset_link: str) -> bool:
    """Send reset password link via SMTP (Gmail) if configured, else fallback to console log"""
    # If SMTP is not configured, warn and return False (it will still log to console)
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("⚠️ SMTP_USER and SMTP_PASSWORD are not configured. Unable to send real email.")
        logger.info(f"🔗 DEVELOPER FALLBACK - Reset link: {reset_link}")
        return False

    sender_email = settings.SMTP_FROM or settings.SMTP_USER
    
    # Create message container
    msg = MIMEMultipart()
    msg['From'] = f"CareerLens AI <{sender_email}>"
    msg['To'] = recipient_email
    msg['Subject'] = "Reset Your CareerLens AI Password"
    
    # HTML body matching standard branding
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #020617; color: #f8fafc; padding: 30px; margin: 0;">
        <div style="max-width: 500px; margin: auto; background-color: #0f172a; padding: 25px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.06); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3);">
          <div style="text-align: center; margin-bottom: 20px;">
            <span style="font-size: 28px; font-weight: bold; color: #3b82f6; text-decoration: none;">✦ CareerLens AI</span>
          </div>
          <h2 style="margin-top: 0; color: #ffffff; font-size: 20px; text-align: center;">Password Reset Request</h2>
          <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; text-align: center;">
            We received a request to reset your password. Click the secure button below to create a new password. This link will expire in 15 minutes.
          </p>
          <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" style="background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 12px 24px; font-weight: bold; border-radius: 8px; font-size: 14px; display: inline-block;">Reset Password</a>
          </div>
          <p style="color: #64748b; font-size: 11px; text-align: center; line-height: 1.4;">
            If you did not request this, please ignore this email. Your password will remain unchanged.
          </p>
        </div>
      </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        # Connect to server
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        logger.info(f"📧 Password reset email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send SMTP email: {e}")
        return False
