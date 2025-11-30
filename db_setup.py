#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script
Automates: database creation, user setup, schema loading, and verification
"""

import psycopg2
from psycopg2 import sql
import sys
from pathlib import Path
from getpass import getpass

# Configuration
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_SUPERUSER = "postgres"
DB_NAME = "fraud_detection"
DB_USER = "fraud_user"
DB_PASSWORD = "fraud_password123"

def get_superuser_password():
    """Get PostgreSQL superuser password."""
    print("\n" + "="*60)
    print("PostgreSQL Superuser Authentication")
    print("="*60)
    print("\nEnter the PostgreSQL 'postgres' superuser password")
    print("(set during PostgreSQL installation)")
    
    password = getpass("\nPassword: ")
    return password

def test_superuser_connection(superuser_password):
    """Test connection as superuser."""
    print("\nTesting superuser connection...")
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_SUPERUSER,
            password=superuser_password,
            database="postgres"
        )
        conn.close()
        print("✓ Superuser authentication successful")
        return True
    except psycopg2.OperationalError as e:
        print(f"✗ Connection failed: {e}")
        print("  - Is PostgreSQL running on port 5432?")
        print("  - Is the password correct?")
        return False

def create_database(superuser_password):
    """Create fraud_detection database"""
    print("\nCreating database...")
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_SUPERUSER,
            password=superuser_password,
            database="postgres"
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        if cur.fetchone():
            print(f"  Database '{DB_NAME}' already exists")
        else:
            cur.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"  ✓ Created database '{DB_NAME}'")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        return False

def create_user(superuser_password):
    """Create fraud_user with appropriate permissions"""
    print("\nCreating user...")
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_SUPERUSER,
            password=superuser_password,
            database="postgres"
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if user exists
        cur.execute(f"SELECT 1 FROM pg_user WHERE usename = '{DB_USER}'")
        if cur.fetchone():
            print(f"  User '{DB_USER}' already exists")
            # Update password
            cur.execute(f"ALTER USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}'")
            print(f"  ✓ Updated password for '{DB_USER}'")
        else:
            cur.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}'")
            print(f"  ✓ Created user '{DB_USER}'")
        
        # Grant privileges
        cur.execute(f"ALTER ROLE {DB_USER} SET client_encoding TO 'utf8'")
        cur.execute(f"ALTER ROLE {DB_USER} SET default_transaction_isolation TO 'read committed'")
        cur.execute(f"ALTER ROLE {DB_USER} SET default_transaction_deferrable TO on")
        cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER}")
        print(f"  ✓ Granted privileges to '{DB_USER}'")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Error creating user: {e}")
        return False

def load_schema():
    """Load database schema from SQL file"""
    print("\nLoading schema...")
    try:
        schema_file = Path(__file__).parent / "database" / "schema" / "create_tables.sql"
        
        if not schema_file.exists():
            print(f"✗ Schema file not found: {schema_file}")
            return False
        
        # Connect as fraud_user
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        
        # Read and execute schema
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Execute each statement
        statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
        for statement in statements:
            cur.execute(statement)
        
        conn.commit()
        print(f"  ✓ Loaded schema from {schema_file.name}")
        
        # List created tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        print(f"\n  Created tables:")
        for table in tables:
            print(f"    - {table[0]}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Error loading schema: {e}")
        return False

def verify_connection():
    """Verify database connection"""
    print("\nVerifying connection...")
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        
        # Test query
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        print(f"  ✓ Connected to PostgreSQL")
        print(f"    {version}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Error verifying connection: {e}")
        return False

def print_summary():
    """Print setup summary and next steps"""
    print("\n" + "="*60)
    print("✅ Database Setup Complete!")
    print("="*60)
    
    print("\n📋 Connection Details:")
    print(f"  Host: {POSTGRES_HOST}")
    print(f"  Port: {POSTGRES_PORT}")
    print(f"  Database: {DB_NAME}")
    print(f"  User: {DB_USER}")
    print(f"  Password: {DB_PASSWORD}")
    
    print("\n🚀 Next Steps:")
    
    print("\n1. Optional - Install pgAdmin:")
    print("   Download: https://www.pgadmin.org/download/pgadmin-4-windows/")
    print("   Then add server with above credentials")
    
    print("\n2. Load IEEE-CIS Data (optional):")
    print("   python load_data_to_db.py 50000")
    print("   (First download dataset to data/raw/)")
    
    print("\n3. Run Dashboard:")
    print("   streamlit run src/visualization/advanced_dashboard.py")
    print("   Then open http://localhost:8501")
    
    print("\n📍 Access Endpoints:")
    print(f"  - PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}")
    print("  - pgAdmin: http://localhost:5050")
    print("  - Dashboard: http://localhost:8501")
    
    print("\n" + "="*60 + "\n")

def main():
    """Main setup flow"""
    print("\n" + "█"*60)
    print("  PostgreSQL Database Setup")
    print("█"*60)
    
    # Get superuser password
    superuser_password = get_superuser_password()
    
    # Test connection
    if not test_superuser_connection(superuser_password):
        return 1
    
    # Create database
    if not create_database(superuser_password):
        return 1
    
    # Create user
    if not create_user(superuser_password):
        return 1
    
    # Load schema
    if not load_schema():
        return 1
    
    # Verify
    if not verify_connection():
        return 1
    
    # Summary
    print_summary()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
