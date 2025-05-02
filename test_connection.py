import pymysql

# Connection parameters
host = 'aws.connect.psdb.cloud'
user = 'en8w2fw3mujepftsc8q9'
password = 'pscale_pw_4m29ibA2v2OazZ6UkIS6Y0TLyhR8JBWuBU52VhqO3Mo'
database = 'chatbox'
port = 3306

# Try to connect
try:
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
        ssl={'ca': ''}  # Empty string disables SSL verification
    )
    
    print("Connected successfully!")
    
    # Test a simple query
    with conn.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"Database version: {version[0]}")
    
    # Close connection
    conn.close()
    
except Exception as e:
    print(f"Connection failed: {e}")
