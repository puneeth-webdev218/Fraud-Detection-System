"""
Database Setup Script
Creates the fraud_detection database and all required tables
"""

import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_database():
    """Create the fraud_detection database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (not to specific database)
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (config.DB_NAME,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {config.DB_NAME}")
            logger.info(f"✓ Database '{config.DB_NAME}' created successfully")
        else:
            logger.info(f"✓ Database '{config.DB_NAME}' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to create database: {e}")
        return False


def create_tables():
    """Create all tables using the schema SQL file"""
    try:
        # Connect to the fraud_detection database
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # Read and execute schema SQL file
        schema_file = Path(__file__).parent.parent.parent / 'database' / 'schema' / 'create_tables.sql'
        
        if not schema_file.exists():
            logger.error(f"✗ Schema file not found: {schema_file}")
            return False
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Execute the schema
        cursor.execute(schema_sql)
        conn.commit()
        
        logger.info("✓ All tables created successfully")
        
        # Verify tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        logger.info(f"\nCreated tables ({len(tables)}):")
        for table in tables:
            logger.info(f"  - {table[0]}")
        
        # Verify views
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        views = cursor.fetchall()
        if views:
            logger.info(f"\nCreated views ({len(views)}):")
            for view in views:
                logger.info(f"  - {view[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to create tables: {e}")
        if conn:
            conn.rollback()
        return False


def verify_database():
    """Verify database setup"""
    try:
        from src.database.connection import db
        
        if not db.test_connection():
            logger.error("✗ Database connection failed")
            return False
        
        # Check table counts
        tables = ['account', 'merchant', 'device', 'transaction', 'shared_device']
        
        logger.info("\nTable status:")
        for table in tables:
            try:
                count = db.get_table_count(table)
                logger.info(f"  ✓ {table}: {count} rows")
            except Exception as e:
                logger.error(f"  ✗ {table}: Error - {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Database verification failed: {e}")
        return False


def main():
    """Main setup function"""
    print("=" * 70)
    print("Fraud Detection Database Setup")
    print("=" * 70)
    
    # Step 1: Create database
    print("\n[Step 1/3] Creating database...")
    if not create_database():
        print("\n✗ Setup failed at database creation")
        sys.exit(1)
    
    # Step 2: Create tables
    print("\n[Step 2/3] Creating tables and schema...")
    if not create_tables():
        print("\n✗ Setup failed at table creation")
        sys.exit(1)
    
    # Step 3: Verify setup
    print("\n[Step 3/3] Verifying database setup...")
    if not verify_database():
        print("\n✗ Setup failed at verification")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✓ Database setup completed successfully!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Download IEEE-CIS dataset to data/raw/")
    print("2. Run: python src/preprocessing/load_data.py")
    print("3. Run: python src/graph/build_graph.py")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
