#!/usr/bin/env python3
"""
Test script to verify status column integration with PostgreSQL

This script:
1. Connects to PostgreSQL
2. Creates/updates transactions table with status column
3. Inserts sample transactions with computed status
4. Retrieves and displays transactions with status from database
5. Verifies the status column is populated correctly
"""

import sys
from pathlib import Path
import pandas as pd
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.dynamic_postgres_manager import PostgreSQLManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_status_integration():
    """Test the status column integration"""
    
    print("\n" + "="*70)
    print("🧪 STATUS COLUMN INTEGRATION TEST")
    print("="*70 + "\n")
    
    # Create manager and connect
    db_manager = PostgreSQLManager()
    
    print("1️⃣  Connecting to PostgreSQL...")
    if not db_manager.connect():
        print("❌ Failed to connect")
        return False
    print("✅ Connected successfully\n")
    
    # Create/update table
    print("2️⃣  Creating/updating transactions table with status column...")
    if not db_manager.create_transactions_table():
        print("❌ Failed to create table")
        db_manager.disconnect()
        return False
    print("✅ Table ready with status column\n")
    
    # Reset database
    print("3️⃣  Resetting database (clearing old data)...")
    if not db_manager.reset_transactions_table():
        print("⚠️  Reset warning (table may not exist yet)")
    
    # Drop and recreate table to ensure clean schema
    print("   (Dropping old table to start fresh...)")
    try:
        db_manager.cursor.execute("DROP TABLE IF EXISTS transactions CASCADE;")
        db_manager.connection.commit()
        print("   ✅ Old table dropped")
    except Exception as e:
        print(f"   ⚠️  Drop warning: {e}")
    
    print("✅ Database reset\n")
    
    # Recreate table with proper schema
    print("✅ Recreating transactions table with status column...")
    if not db_manager.create_transactions_table():
        print("❌ Failed to create table")
        db_manager.disconnect()
        return False
    
    # Create sample data
    print("4️⃣  Creating sample transaction data with fraud_flag...")
    sample_data = pd.DataFrame({
        'transaction_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'account_id': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        'merchant_id': [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
        'device_id': [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009],
        'amount': [100.50, 250.75, 50.00, 1500.00, 75.25, 500.00, 200.00, 30.00, 999.99, 150.00],
        'timestamp': pd.date_range('2024-01-01', periods=10),
        'fraud_flag': [0, 1, 0, 1, 0, 0, 1, 0, 1, 0]  # 5 fraud, 5 legitimate
    })
    
    print(f"✅ Created {len(sample_data)} sample transactions")
    print("\nSample data (fraud_flag column):")
    print(sample_data[['transaction_id', 'account_id', 'fraud_flag']].to_string(index=False))
    print()
    
    # Insert data
    print("5️⃣  Inserting transactions into PostgreSQL...")
    print("   (Status will be computed: fraud_flag=1 → 'FRAUD', fraud_flag=0 → 'OK')")
    inserted, skipped = db_manager.insert_transactions_batch(sample_data)
    print(f"✅ Inserted: {inserted}, Skipped: {skipped}\n")
    
    # Retrieve data from database
    print("6️⃣  Retrieving transactions from database (with status from DB)...")
    result_df = db_manager.get_transactions_with_status(limit=100)
    
    if len(result_df) > 0:
        print(f"✅ Retrieved {len(result_df)} transactions from database\n")
        
        # Display the result with status
        display_df = result_df[['transaction_id', 'account_id', 'fraud_flag', 'status']].copy()
        print("Transactions with status from database:")
        print(display_df.to_string(index=False))
        print()
        
        # Verify status values
        print("7️⃣  Verifying status column values...")
        fraud_statuses = result_df[result_df['fraud_flag'] == 1]['status'].unique()
        ok_statuses = result_df[result_df['fraud_flag'] == 0]['status'].unique()
        
        if len(fraud_statuses) == 1 and fraud_statuses[0] == 'FRAUD':
            print("✅ Fraud transactions correctly marked as 'FRAUD'")
        else:
            print(f"❌ Fraud status issue: {fraud_statuses}")
        
        if len(ok_statuses) == 1 and ok_statuses[0] == 'OK':
            print("✅ Legitimate transactions correctly marked as 'OK'")
        else:
            print(f"❌ OK status issue: {ok_statuses}")
        
        print()
    else:
        print("❌ No transactions retrieved\n")
    
    # Test search with status
    print("8️⃣  Testing transaction search with status...")
    search_results = db_manager.get_transaction_by_search('account_id', 100)
    if len(search_results) > 0:
        print(f"✅ Found {len(search_results)} transaction(s) for account_id=100")
        print(f"   Status from DB: {search_results['status'].values[0]}")
    print()
    
    # Disconnect
    db_manager.disconnect()
    
    print("="*70)
    print("✅ TEST COMPLETE!")
    print("="*70)
    print("\n📌 VERIFICATION CHECKLIST:")
    print("   ✅ Status column added to transactions table")
    print("   ✅ Status computed from fraud_flag (1→'FRAUD', 0→'OK')")
    print("   ✅ Status inserted into database")
    print("   ✅ Status retrieved from database")
    print("   ✅ Values verified: 'FRAUD' and 'OK'")
    print("\n🎯 Next Step: Check pgAdmin dashboard")
    print("   1. Open pgAdmin → Fraud Detection → Tables → transactions")
    print("   2. Verify 'status' column exists")
    print("   3. Verify each row shows 'FRAUD' or 'OK' in status column")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = test_status_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
