import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_project.settings')
django.setup()

from user_auth.models import OTP
from django.utils import timezone

def list_recent_otps():
    """List all OTPs created in the last hour"""
    one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
    recent_otps = OTP.objects.filter(created_at__gte=one_hour_ago).order_by('-created_at')
    
    if recent_otps.exists():
        print(f"Found {recent_otps.count()} OTPs created in the last hour:")
        for otp in recent_otps:
            print(f"Email: {otp.email}, OTP: {otp.otp}, Created: {otp.created_at}")
    else:
        print("No OTPs found in the last hour.")

if __name__ == "__main__":
    list_recent_otps()
