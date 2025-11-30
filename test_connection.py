#!/usr/bin/env python
"""Test PostgreSQL connection and setup database"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_connection():
    """Test database connection"""
    print("=" * 60)
    print("Testing PostgreSQL Connection")
    print("=" * 60)
    
    try:
        from src.database.db_connection import DatabaseConnection
        
        print("\n1️⃣  Loading configuration from .env...")
        db = DatabaseConnection()
        print("   ✅ Configuration loaded")
        
        print("\n2️⃣  Connecting to PostgreSQL...")
        if db.connect():
            print("   ✅ Connection successful!")
            
            # Get connection info
            print("\n3️⃣  Connection Details:")
            if db.connection:
                print(f"   - Host: {db.connection.info.host}")
                print(f"   - Port: {db.connection.info.port}")
                print(f"   - Database: {db.connection.info.dbname}")
                print(f"   - User: {db.connection.info.user}")
            
            # Test simple query
            print("\n4️⃣  Testing query execution...")
            result = db.execute("SELECT version();")
            if result:
                print("   ✅ Query executed successfully")
                row = db.fetchone()
                if row:
                    print(f"   - PostgreSQL Version: {row[0].split(',')[0]}")
            
            db.disconnect()
            print("\n✅ All tests passed! Database connection is working.\n")
            return True
        else:
            print("   ❌ Connection failed!")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def setup_database():
    """Setup database tables"""
    print("\n" + "=" * 60)
    print("Setting Up Database Tables")
    print("=" * 60)
    
    try:
        from src.database.fraud_db_manager import FraudDetectionDatabaseManager
        
        print("\n1️⃣  Initializing database manager...")
        db = FraudDetectionDatabaseManager()
        print("   ✅ Manager initialized")
        
        print("\n2️⃣  Setting up database (creating tables)...")
        if db.setup():
            print("   ✅ Database setup successful!")
            
            print("\n3️⃣  Database Summary:")
            db.print_summary()
            
            db.disconnect()
            print("\n✅ Database is ready to use!\n")
            return True
        else:
            print("   ❌ Database setup failed!")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test connection first
    if not test_connection():
        print("\n⚠️  Connection test failed. Check your .env credentials.")
        sys.exit(1)
    
    # If connection works, setup database
    if not setup_database():
        print("\n⚠️  Database setup failed.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 All done! Your database is ready to use.")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Open pgAdmin (http://localhost:5050)")
    print("2. Check the 'fraud_detection' database")
    print("3. Run your fraud detection pipeline")
    print("4. Data will automatically save to PostgreSQL")
    print("\nFor help, see:")
    print("- POSTGRESQL_QUICK_INTEGRATION.md")
    print("- POSTGRESQL_INTEGRATION_GUIDE.md")
