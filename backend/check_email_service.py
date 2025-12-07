"""
Quick script to check if email service is properly initialized
Run this AFTER restarting the backend server
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from src.smtp.service import get_email_service
from src.settings import settings

print("=" * 60)
print("   EMAIL SERVICE STATUS CHECK")
print("=" * 60)
print()

# Check settings
print("1. SMTP Configuration from .env:")
print(f"   Host:     {settings.SMTP_HOST}")
print(f"   Port:     {settings.SMTP_PORT}")
print(f"   Username: {settings.SMTP_USERNAME}")
print(f"   Password: {'*' * len(settings.SMTP_PASSWORD) if settings.SMTP_PASSWORD else 'NOT SET'}")
print(f"   Use TLS:  {settings.SMTP_USE_TLS}")
print(f"   Sender:   {settings.SMTP_SENDER_EMAIL}")
print()

# Check if service is initialized
print("2. Email Service Status:")
service = get_email_service()
if service:
    print("   ✅ Email service IS initialized")
    print(f"   Sender: {service.sender_email}")
    print(f"   Name:   {service.sender_name}")
    print()
    print("3. Test Email Send:")
    print("   Sending test email to test@example.com...")
    try:
        result = service.send_email(
            to_email="test@example.com",
            subject="Test from Freedom AI Analysis",
            body="Email service is working correctly!"
        )
        if result:
            print("   ✅ Test email sent successfully!")
        else:
            print("   ❌ Test email failed to send")
    except Exception as e:
        print(f"   ❌ Error sending test email: {e}")
else:
    print("   ❌ Email service is NOT initialized")
    print()
    print("   Possible reasons:")
    print("   - Backend server not restarted after .env update")
    print("   - SMTP credentials missing or incorrect")
    print("   - Email service initialization failed during startup")
    print()
    print("   Solution: Restart the backend server using restart_server.bat")

print()
print("=" * 60)
