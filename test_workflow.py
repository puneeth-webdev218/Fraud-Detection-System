#!/usr/bin/env python
"""Test script for Phase 1 and Phase 2 operations"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.database.dynamic_postgres_manager import PostgreSQLManager
from src.preprocessing.interactive_loader import generate_demo_transactions
import pandas as pd

def test_phase1_and_phase2():
    """Test both phases of the workflow"""
    
    # Generate test data
    print("=" * 60)
    print("🔄 TESTING PHASE 1 AND PHASE 2 WORKFLOW")
    print("=" * 60)
    
    print("\n1️⃣ Generating demo transactions...")
    df = generate_demo_transactions(1000)
    print(f"   ✓ Generated {len(df)} transactions")
    print(f"   Columns: {list(df.columns)[:10]}")
    
    # Rename to match database schema
    print("\n2️⃣ Preparing data for Phase 1...")
    rename_mapping = {
        'transaction_id': 'transaction_id',
        'account_id': 'account_id',
        'merchant_id': 'merchant_id',
        'device_id': 'device_id',
        'transaction_amount': 'amount',
        'transaction_date': 'timestamp',
        'is_fraud': 'fraud_flag'
    }
    
    # Prepare columns if needed
    if 'amount' not in df.columns and 'transaction_amount' in df.columns:
        df = df.rename(columns={'transaction_amount': 'amount'})
    if 'fraud_flag' not in df.columns and 'is_fraud' in df.columns:
        df = df.rename(columns={'is_fraud': 'fraud_flag'})
    if 'timestamp' not in df.columns and 'transaction_date' in df.columns:
        df = df.rename(columns={'transaction_date': 'timestamp'})
    
    # Ensure IDs
    if 'account_id' not in df.columns:
        df['account_id'] = (df['transaction_id'] % 100) + 1
    if 'merchant_id' not in df.columns:
        df['merchant_id'] = (df['transaction_id'] % 15) + 1
    if 'device_id' not in df.columns:
        df['device_id'] = (df['transaction_id'] % 10) + 1
    
    print(f"   ✓ Data prepared")
    
    # Connect to database
    print("\n3️⃣ Connecting to PostgreSQL...")
    db = PostgreSQLManager()
    if not db.connect():
        print("   ❌ Failed to connect")
        return False
    print("   ✓ Connected")
    
    # Phase 1: Create transactions table and insert
    print("\n4️⃣ PHASE 1: Creating transactions table...")
    if not db.create_transactions_table():
        print("   ❌ Failed to create transactions table")
        db.disconnect()
        return False
    print("   ✓ Transactions table created")
    
    print("\n5️⃣ PHASE 1: Inserting raw transactions...")
    inserted, skipped = db.insert_transactions_batch(df)
    print(f"   ✓ Inserted: {inserted}, Skipped: {skipped}")
    
    # Verify Phase 1
    count = db.get_transaction_count()
    print(f"   ✓ Verified: {count} rows in transactions table")
    
    # Phase 2: Create fraud_predictions table
    print("\n6️⃣ PHASE 2: Creating fraud_predictions table...")
    if not db.create_fraud_predictions_table():
        print("   ❌ Failed to create fraud_predictions table")
        db.disconnect()
        return False
    print("   ✓ Fraud_predictions table created")
    
    # Add status column to dataframe
    print("\n7️⃣ PHASE 2: Adding status column (simulating GNN)...")
    df['status'] = df['fraud_flag'].apply(lambda x: 'FRAUD' if x == 1 else 'OK')
    print("   ✓ Status column added")
    
    # Insert to fraud_predictions
    print("\n8️⃣ PHASE 2: Inserting predictions...")
    inserted_pred, skipped_pred = db.insert_fraud_predictions_batch(df)
    print(f"   ✓ Inserted: {inserted_pred}, Skipped: {skipped_pred}")
    
    # Verify Phase 2
    count_pred = db.get_fraud_prediction_count()
    print(f"   ✓ Verified: {count_pred} rows in fraud_predictions table")
    
    # Test queries
    print("\n9️⃣ Testing queries...")
    stats = db.get_fraud_stats()
    print(f"   ✓ Fraud stats: {stats}")
    
    # Get sample data
    sample = db.get_transactions_with_status(limit=5)
    print(f"   ✓ Sample predictions: {len(sample)} rows")
    if len(sample) > 0:
        print(f"     Columns: {list(sample.columns)}")
    
    db.disconnect()
    
    print("\n" + "=" * 60)
    print("✅ PHASE 1 AND PHASE 2 TEST SUCCESSFUL!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    test_phase1_and_phase2()
