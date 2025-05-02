import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_project.settings')
django.setup()

# Import Django models and migration utilities
from django.core.management import call_command
from django.db import connection

def setup_database():
    """Set up all necessary database tables"""
    print("Setting up database tables...")
    
    # Check connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            db_version = cursor.fetchone()
            print(f"Connected to MySQL version: {db_version[0]}")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False
    
    # Run migrations
    try:
        print("Running migrations...")
        call_command('makemigrations')
        call_command('migrate')
        print("Migrations completed successfully!")
        return True
    except Exception as e:
        print(f"Error during migrations: {e}")
        return False

if __name__ == "__main__":
    success = setup_database()
    if success:
        print("Database setup completed successfully!")
        
        # Create superuser if requested
        if '--create-superuser' in sys.argv:
            try:
                from django.contrib.auth.models import User
                if not User.objects.filter(is_superuser=True).exists():
                    print("Creating superuser...")
                    User.objects.create_superuser(
                        username='admin',
                        email='admin@example.com',
                        password='adminpassword'
                    )
                    print("Superuser created successfully!")
                else:
                    print("Superuser already exists.")
            except Exception as e:
                print(f"Error creating superuser: {e}")
    else:
        print("Database setup failed.")
