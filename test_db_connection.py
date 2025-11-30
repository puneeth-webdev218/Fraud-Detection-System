"""
Test PostgreSQL Connection
Run this to verify database connectivity
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    """Test PostgreSQL connection with proper error handling"""
    
    # Get credentials from environment
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    database = os.getenv('DB_NAME', 'fraud_detection')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', '')
    
    print("\n" + "="*60)
    print("PostgreSQL Connection Test")
    print("="*60)
    print(f"\nAttempting to connect to:")
    print(f"  Host:     {host}")
    print(f"  Port:     {port}")
    print(f"  Database: {database}")
    print(f"  User:     {user}")
    
    try:
        connection = psycopg2.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password
        )
        
        cursor = connection.cursor()
        print("\n✔ PostgreSQL connected successfully")
        
        # Get version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✔ PostgreSQL version: {version[0][:60]}...")
        
        # List tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print(f"\n✔ Tables in database ({len(tables)} found):")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} rows")
        
        cursor.close()
        connection.close()
        
        print("\n" + "="*60)
        print("✔ Connection test PASSED")
        print("="*60 + "\n")
        return True
    
    except psycopg2.OperationalError as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check PostgreSQL is running: Get-Service postgresql-x64-15")
        print("  2. Check credentials in .env file")
        print("  3. Verify database exists: psql -U postgres -l")
        print("  4. Verify user exists: psql -U postgres -c '\\du'")
        return False
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
