import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_project.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email_config():
    """Test the email configuration"""
    print("Testing email configuration...")
    
    # Email details
    subject = 'Test Email from Django'
    message = 'This is a test email from your Django application.'
    from_email = settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'noreply@example.com'
    recipient_list = [input("Enter your email address to receive the test: ")]
    
    # Print current email settings
    print("\nCurrent Email Settings:")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    if hasattr(settings, 'EMAIL_HOST'):
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    if hasattr(settings, 'EMAIL_PORT'):
        print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    if hasattr(settings, 'EMAIL_USE_TLS'):
        print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    if hasattr(settings, 'EMAIL_HOST_USER'):
        print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    if hasattr(settings, 'EMAIL_HOST_PASSWORD'):
        print(f"EMAIL_HOST_PASSWORD: {'*' * 8} (hidden)")
    
    # Try to send email
    try:
        print("\nAttempting to send test email...")
        send_mail(subject, message, from_email, recipient_list)
        print("Test email sent successfully!")
        return True
    except Exception as e:
        print(f"\nError sending email: {e}")
        
        # Provide troubleshooting tips
        print("\nTroubleshooting Tips:")
        if 'SMTPAuthenticationError' in str(e):
            print("1. Check that your email and password are correct")
            print("2. If using Gmail, make sure you've created an App Password:")
            print("   - Go to your Google Account > Security > 2-Step Verification > App passwords")
            print("   - Create a new app password for your Django application")
            print("   - Use this app password in your settings instead of your regular password")
            print("3. Make sure 'Less secure app access' is turned on (if using an older Gmail account)")
        elif 'SMTPConnectError' in str(e):
            print("1. Check your internet connection")
            print("2. Verify that the SMTP server address is correct")
            print("3. Make sure your firewall isn't blocking the connection")
        
        return False

if __name__ == "__main__":
    success = test_email_config()
    
    if not success:
        print("\nWould you like to use the console email backend for development? (y/n)")
        choice = input().lower()
        
        if choice == 'y':
            # Update settings to use console backend
            settings_path = os.path.join(settings.BASE_DIR, 'auth_project', 'settings.py')
            
            with open(settings_path, 'r') as f:
                settings_content = f.read()
            
            # Replace email backend settings
            if 'EMAIL_BACKEND = ' in settings_content:
                settings_content = settings_content.replace(
                    "EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'",
                    "EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'"
                )
                
                # Comment out other email settings
                settings_content = settings_content.replace(
                    "EMAIL_HOST = ", "# EMAIL_HOST = "
                )
                settings_content = settings_content.replace(
                    "EMAIL_PORT = ", "# EMAIL_PORT = "
                )
                settings_content = settings_content.replace(
                    "EMAIL_USE_TLS = ", "# EMAIL_USE_TLS = "
                )
                settings_content = settings_content.replace(
                    "EMAIL_HOST_USER = ", "# EMAIL_HOST_USER = "
                )
                settings_content = settings_content.replace(
                    "EMAIL_HOST_PASSWORD = ", "# EMAIL_HOST_PASSWORD = "
                )
                
                with open(settings_path, 'w') as f:
                    f.write(settings_content)
                
                print("\nSettings updated to use console email backend.")
                print("OTPs will now be printed to the console instead of being sent via email.")
            else:
                print("\nCould not find EMAIL_BACKEND setting in settings.py.")
                print("Please manually update your settings to use the console email backend:")
                print("EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'")
