#!/usr/bin/env python3
"""
Complete PostgreSQL + pgAdmin Setup for Fraud Detection Database
This script automates:
1. Database creation
2. User setup
3. Schema loading
4. Connection verification
5. pgAdmin instructions
"""

import psycopg2
from psycopg2 import sql
import os
import sys
from pathlib import Path
from getpass import getpass
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Configuration
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
DB_NAME = "fraud_detection"
DB_USER = "fraud_user"
DB_PASSWORD = "fraud_password123"

def create_database():
    """Create fraud_detection database"""
    try:
        # Connect as superuser
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database="postgres"
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        if cur.fetchone():
            print(f"✓ Database '{DB_NAME}' already exists")
        else:
            cur.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"✓ Created database '{DB_NAME}'")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        sys.exit(1)

def create_user():
    """Create fraud_user with appropriate permissions"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database="postgres"
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if user exists
        cur.execute(f"SELECT 1 FROM pg_user WHERE usename = '{DB_USER}'")
        if cur.fetchone():
            print(f"✓ User '{DB_USER}' already exists")
        else:
            cur.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}'")
            print(f"✓ Created user '{DB_USER}'")
        
        # Grant privileges
        cur.execute(f"ALTER ROLE {DB_USER} SET client_encoding TO 'utf8'")
        cur.execute(f"ALTER ROLE {DB_USER} SET default_transaction_isolation TO 'read committed'")
        cur.execute(f"ALTER ROLE {DB_USER} SET default_transaction_deferrable TO on")
        cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER}")
        
        print(f"✓ Granted privileges to '{DB_USER}'")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Error creating user: {e}")
        sys.exit(1)

def load_schema():
    """Load database schema from SQL file"""
    try:
        schema_file = Path(__file__).parent / "database" / "schema" / "create_tables.sql"
        
        if not schema_file.exists():
            print(f"✗ Schema file not found: {schema_file}")
            sys.exit(1)
        
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
        
        cur.execute(schema_sql)
        conn.commit()
        
        print(f"✓ Loaded schema from {schema_file.name}")
        
        # List created tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print(f"\n✓ Created tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Error loading schema: {e}")
        sys.exit(1)

def verify_connection():
    """Verify database connection"""
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
        print(f"\n✓ Connected to PostgreSQL:")
        print(f"  {version}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Error verifying connection: {e}")
        sys.exit(1)

def main():
    """Main setup flow"""
    print("=" * 60)
    print("PostgreSQL Fraud Detection Database Setup")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Host: {POSTGRES_HOST}")
    print(f"  Port: {POSTGRES_PORT}")
    print(f"  Superuser: {POSTGRES_USER}")
    print(f"  Database: {DB_NAME}")
    print(f"  DB User: {DB_USER}")
    print("\nStep 1: Creating database...")
    create_database()
    
    print("\nStep 2: Creating user...")
    create_user()
    
    print("\nStep 3: Loading schema...")
    load_schema()
    
    print("\nStep 4: Verifying connection...")
    verify_connection()
    
    print("\n" + "=" * 60)
    print("✓ Setup Complete!")
    print("=" * 60)
    print("\nYou can now:")
    print("1. Connect via pgAdmin to localhost:5432")
    print("   Username: fraud_user")
    print("   Password: fraud_password123")
    print("\n2. Load data using Python:")
    print("   python -c 'from src.database.setup_db import load_data; load_data()'")
    print("\n3. Run the dashboard:")
    print("   streamlit run src/visualization/advanced_dashboard.py")
    print("\nConfiguration saved in .env file")

if __name__ == "__main__":
    main()
