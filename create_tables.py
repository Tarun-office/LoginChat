import os
import django
import pymysql

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_project.settings')
django.setup()

# Import Django settings
from django.conf import settings

def create_tables():
    """Create all necessary database tables manually"""
    print("Creating database tables manually...")
    
    # Connect to database
    try:
        conn = pymysql.connect(
            host=settings.DATABASES['default']['HOST'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            database=settings.DATABASES['default']['NAME'],
            port=int(settings.DATABASES['default']['PORT']),
            ssl={'ca': ''}  # Empty string disables SSL verification
        )
        
        print("Connected to database successfully!")
        
        cursor = conn.cursor()
        
        # Create tables
        tables = [
            # Django system tables
            """
            CREATE TABLE IF NOT EXISTS django_migrations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                app VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                applied DATETIME(6) NOT NULL
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS django_content_type (
                id INT AUTO_INCREMENT PRIMARY KEY,
                app_label VARCHAR(100) NOT NULL,
                model VARCHAR(100) NOT NULL,
                UNIQUE(app_label, model)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS django_admin_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                action_time DATETIME(6) NOT NULL,
                object_id LONGTEXT NULL,
                object_repr VARCHAR(200) NOT NULL,
                action_flag SMALLINT UNSIGNED NOT NULL,
                change_message LONGTEXT NOT NULL,
                content_type_id INT NULL,
                user_id INT NOT NULL,
                INDEX(content_type_id),
                INDEX(user_id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS django_session (
                session_key VARCHAR(40) PRIMARY KEY,
                session_data LONGTEXT NOT NULL,
                expire_date DATETIME(6) NOT NULL,
                INDEX(expire_date)
            )
            """,
            
            # Auth tables
            """
            CREATE TABLE IF NOT EXISTS auth_permission (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                content_type_id INT NOT NULL,
                codename VARCHAR(100) NOT NULL,
                UNIQUE(content_type_id, codename),
                INDEX(content_type_id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS auth_group (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(150) NOT NULL UNIQUE
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS auth_group_permissions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                group_id INT NOT NULL,
                permission_id INT NOT NULL,
                UNIQUE(group_id, permission_id),
                INDEX(group_id),
                INDEX(permission_id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS auth_user (
                id INT AUTO_INCREMENT PRIMARY KEY,
                password VARCHAR(128) NOT NULL,
                last_login DATETIME(6) NULL,
                is_superuser TINYINT(1) NOT NULL,
                username VARCHAR(150) NOT NULL UNIQUE,
                first_name VARCHAR(150) NOT NULL,
                last_name VARCHAR(150) NOT NULL,
                email VARCHAR(254) NOT NULL,
                is_staff TINYINT(1) NOT NULL,
                is_active TINYINT(1) NOT NULL,
                date_joined DATETIME(6) NOT NULL
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS auth_user_groups (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                group_id INT NOT NULL,
                UNIQUE(user_id, group_id),
                INDEX(user_id),
                INDEX(group_id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS auth_user_user_permissions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                permission_id INT NOT NULL,
                UNIQUE(user_id, permission_id),
                INDEX(user_id),
                INDEX(permission_id)
            )
            """,
            
            # Custom app tables
            """
            CREATE TABLE IF NOT EXISTS user_auth_otp (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(254) NOT NULL,
                otp VARCHAR(6) NOT NULL,
                created_at DATETIME(6) NOT NULL
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS user_auth_userprofile (
                id INT AUTO_INCREMENT PRIMARY KEY,
                age INT NOT NULL,
                profession VARCHAR(20) NOT NULL,
                business_name VARCHAR(100) NULL,
                company_name VARCHAR(100) NULL,
                services_provided VARCHAR(200) NULL,
                school_name VARCHAR(100) NULL,
                bio LONGTEXT NOT NULL,
                hobbies VARCHAR(200) NOT NULL,
                username VARCHAR(30) NOT NULL UNIQUE,
                profile_image VARCHAR(100) NULL,
                card_image1 VARCHAR(100) NULL,
                card_image2 VARCHAR(100) NULL,
                card_image3 VARCHAR(100) NULL,
                card_image4 VARCHAR(100) NULL,
                last_active DATETIME(6) NOT NULL,
                created_at DATETIME(6) NOT NULL,
                updated_at DATETIME(6) NOT NULL,
                user_id INT NOT NULL UNIQUE,
                INDEX(user_id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS user_auth_message (
                id INT AUTO_INCREMENT PRIMARY KEY,
                content LONGTEXT NOT NULL,
                created_at DATETIME(6) NOT NULL,
                updated_at DATETIME(6) NOT NULL,
                is_edited TINYINT(1) NOT NULL,
                is_seen TINYINT(1) NOT NULL,
                is_delivered TINYINT(1) NOT NULL,
                seen_at DATETIME(6) NULL,
                delivered_at DATETIME(6) NULL,
                receiver_id INT NOT NULL,
                sender_id INT NOT NULL,
                INDEX(receiver_id),
                INDEX(sender_id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS user_auth_conversation (
                id INT AUTO_INCREMENT PRIMARY KEY,
                updated_at DATETIME(6) NOT NULL,
                last_message_id INT NULL UNIQUE,
                INDEX(last_message_id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS user_auth_conversation_participants (
                id INT AUTO_INCREMENT PRIMARY KEY,
                conversation_id INT NOT NULL,
                user_id INT NOT NULL,
                UNIQUE(conversation_id, user_id),
                INDEX(conversation_id),
                INDEX(user_id)
            )
            """
        ]
        
        # Execute each table creation query
        for table_query in tables:
            print(f"Executing: {table_query[:60]}...")
            cursor.execute(table_query)
        
        # Add foreign key constraints
        constraints = [
            """
            ALTER TABLE django_admin_log
            ADD CONSTRAINT django_admin_log_content_type_id_fk
            FOREIGN KEY (content_type_id) REFERENCES django_content_type(id)
            """,
            
            """
            ALTER TABLE django_admin_log
            ADD CONSTRAINT django_admin_log_user_id_fk
            FOREIGN KEY (user_id) REFERENCES auth_user(id)
            """,
            
            """
            ALTER TABLE auth_permission
            ADD CONSTRAINT auth_permission_content_type_id_fk
            FOREIGN KEY (content_type_id) REFERENCES django_content_type(id)
            """,
            
            """
            ALTER TABLE auth_group_permissions
            ADD CONSTRAINT auth_group_permissions_group_id_fk
            FOREIGN KEY (group_id) REFERENCES auth_group(id)
            """,
            
            """
            ALTER TABLE auth_group_permissions
            ADD CONSTRAINT auth_group_permissions_permission_id_fk
            FOREIGN KEY (permission_id) REFERENCES auth_permission(id)
            """,
            
            """
            ALTER TABLE auth_user_groups
            ADD CONSTRAINT auth_user_groups_user_id_fk
            FOREIGN KEY (user_id) REFERENCES auth_user(id)
            """,
            
            """
            ALTER TABLE auth_user_groups
            ADD CONSTRAINT auth_user_groups_group_id_fk
            FOREIGN KEY (group_id) REFERENCES auth_group(id)
            """,
            
            """
            ALTER TABLE auth_user_user_permissions
            ADD CONSTRAINT auth_user_user_permissions_user_id_fk
            FOREIGN KEY (user_id) REFERENCES auth_user(id)
            """,
            
            """
            ALTER TABLE auth_user_user_permissions
            ADD CONSTRAINT auth_user_user_permissions_permission_id_fk
            FOREIGN KEY (permission_id) REFERENCES auth_permission(id)
            """,
            
            """
            ALTER TABLE user_auth_userprofile
            ADD CONSTRAINT user_auth_userprofile_user_id_fk
            FOREIGN KEY (user_id) REFERENCES auth_user(id)
            """,
            
            """
            ALTER TABLE user_auth_message
            ADD CONSTRAINT user_auth_message_receiver_id_fk
            FOREIGN KEY (receiver_id) REFERENCES auth_user(id)
            """,
            
            """
            ALTER TABLE user_auth_message
            ADD CONSTRAINT user_auth_message_sender_id_fk
            FOREIGN KEY (sender_id) REFERENCES auth_user(id)
            """,
            
            """
            ALTER TABLE user_auth_conversation
            ADD CONSTRAINT user_auth_conversation_last_message_id_fk
            FOREIGN KEY (last_message_id) REFERENCES user_auth_message(id)
            """,
            
            """
            ALTER TABLE user_auth_conversation_participants
            ADD CONSTRAINT user_auth_conversation_participants_conversation_id_fk
            FOREIGN KEY (conversation_id) REFERENCES user_auth_conversation(id)
            """,
            
            """
            ALTER TABLE user_auth_conversation_participants
            ADD CONSTRAINT user_auth_conversation_participants_user_id_fk
            FOREIGN KEY (user_id) REFERENCES auth_user(id)
            """
        ]
        
        # Try to add constraints, but don't fail if they already exist
        for constraint in constraints:
            try:
                print(f"Adding constraint: {constraint[:60]}...")
                cursor.execute(constraint)
            except Exception as e:
                print(f"Constraint error (may already exist): {e}")
        
        # Commit changes
        conn.commit()
        print("All tables created successfully!")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False

if __name__ == "__main__":
    success = create_tables()
    if success:
        print("Database tables created successfully!")
    else:
        print("Failed to create database tables.")
