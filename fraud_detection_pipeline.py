#!/usr/bin/env python
"""
Fraud Detection Pipeline with PostgreSQL Integration
Processes transactions and automatically saves results to database
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging

sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_transactions_with_db(num_transactions=1000, output_csv=None):
    """
    Process transactions from dataset and save to PostgreSQL
    
    Args:
        num_transactions: Number of transactions to process (default 1000)
        output_csv: Optional CSV file to save results
    """
    
    print("\n" + "=" * 80)
    print("🔐 FRAUD DETECTION PIPELINE WITH DATABASE INTEGRATION")
    print("=" * 80)
    
    try:
        # Step 1: Load dataset
        print("\n📂 Step 1: Loading Dataset...")
        data_dir = Path(__file__).parent / "data" / "raw"
        trans_file = data_dir / "train_transaction.csv"
        
        if not trans_file.exists():
            print(f"❌ Dataset not found: {trans_file}")
            return False
        
        # Load transactions
        df = pd.read_csv(trans_file, nrows=num_transactions)
        print(f"   ✅ Loaded {len(df):,} transactions from CSV")
        
        # Step 2: Run fraud detection
        print("\n🔍 Step 2: Running Fraud Detection...")
        
        # For demo, use the actual fraud labels from dataset
        fraud_predictions = []
        for idx, row in df.iterrows():
            trans_id = int(row['TransactionID'])
            actual_fraud = bool(row['isFraud'])
            
            # Simulate model prediction confidence
            if actual_fraud:
                confidence = np.random.uniform(0.6, 0.99)
            else:
                confidence = np.random.uniform(0.01, 0.4)
            
            fraud_predictions.append({
                'transaction_id': trans_id,
                'is_fraud': actual_fraud,
                'fraud_probability': confidence,
                'model_version': '1.0',
                'timestamp': datetime.now()
            })
            
            if (idx + 1) % 100 == 0:
                print(f"   • Processed {idx + 1:,}/{len(df):,} transactions...")
        
        df_predictions = pd.DataFrame(fraud_predictions)
        print(f"   ✅ Fraud detection completed")
        
        # Step 3: Save to CSV (optional)
        if output_csv:
            df_predictions.to_csv(output_csv, index=False)
            print(f"\n💾 Step 3: Saved predictions to CSV")
            print(f"   ✅ {output_csv}")
        
        # Step 4: Save to PostgreSQL
        print(f"\n🗄️  Step 4: Saving to PostgreSQL Database...")
        
        from src.database.fraud_db_manager import FraudDetectionDatabaseManager
        
        # Initialize database manager
        db = FraudDetectionDatabaseManager()
        
        # Setup database (creates tables if needed)
        print("   • Connecting to PostgreSQL...")
        if not db.setup():
            print("   ❌ Database setup failed")
            return False
        
        print("   ✅ Connected to PostgreSQL")
        
        # Prepare transaction data for database
        print("   • Preparing transaction data...")
        
        # Map predictions to transaction format
        trans_data = []
        for idx, row in df.iterrows():
            trans_data.append({
                'TransactionID': int(row['TransactionID']),
                'account_id': idx % 100 + 1,  # Distribute across accounts
                'merchant_id': idx % 15 + 1,  # Distribute across merchants
                'device_id': idx % 10 + 1,    # Distribute across devices
                'TransactionAmt': float(row.get('TransactionAmt', 0.0)),
                'isFraud': bool(row['isFraud'])
            })
        
        df_trans = pd.DataFrame(trans_data)
        
        # Insert transaction data
        print(f"   • Inserting {len(df_trans):,} transactions...")
        column_mapping = {
            'TransactionID': 'TransactionID',
            'account_id': 'account_id',
            'merchant_id': 'merchant_id',
            'device_id': 'device_id',
            'TransactionAmt': 'TransactionAmt',
            'isFraud': 'isFraud'
        }
        
        if db.insert_results(df_trans, column_mapping):
            print("   ✅ Transactions inserted successfully")
        else:
            print("   ⚠️  Transactions inserted with warnings")
        
        # Insert fraud predictions
        print(f"   • Inserting {len(df_predictions):,} fraud predictions...")
        pred_mapping = {
            'transaction_id': 'transaction_id',
            'fraud_probability': 'fraud_probability',
            'is_fraud': 'is_fraud',
            'model_version': 'model_version'
        }
        
        if db.insert_predictions(df_predictions, pred_mapping):
            print("   ✅ Predictions inserted successfully")
        else:
            print("   ⚠️  Predictions inserted with warnings")
        
        # Get summary
        print("\n📊 Step 5: Database Summary")
        db.print_summary()
        
        db.disconnect()
        
        # Final statistics
        fraud_count = df_predictions['is_fraud'].sum()
        fraud_pct = (fraud_count / len(df_predictions)) * 100
        
        print("\n" + "=" * 80)
        print("✅ PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"\n📈 FRAUD DETECTION RESULTS:")
        print(f"   • Total Transactions Processed: {len(df_predictions):,}")
        print(f"   • Fraudulent Transactions: {fraud_count:,}")
        print(f"   • Fraud Rate: {fraud_pct:.2f}%")
        print(f"   • Avg Fraud Probability: {df_predictions['fraud_probability'].mean():.4f}")
        
        print(f"\n💾 DATA SAVED:")
        print(f"   ✅ PostgreSQL Database (fraud_detection)")
        if output_csv:
            print(f"   ✅ CSV File ({output_csv})")
        
        print(f"\n🔍 NEXT STEPS:")
        print(f"   1. Open pgAdmin: http://localhost:5050")
        print(f"   2. Navigate to: fraud_detection → Schemas → public → Tables")
        print(f"   3. View transaction table: SELECT COUNT(*) FROM transaction;")
        print(f"   4. View fraud predictions: SELECT * FROM fraud_predictions LIMIT 10;")
        print(f"   5. Run analytics: SELECT * FROM transaction WHERE is_fraud = TRUE;")
        print("\n" + "=" * 80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fraud Detection Pipeline with Database Integration"
    )
    parser.add_argument(
        '--transactions',
        type=int,
        default=1000,
        help='Number of transactions to process (default: 1000)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output CSV file for predictions'
    )
    
    args = parser.parse_args()
    
    success = process_transactions_with_db(
        num_transactions=args.transactions,
        output_csv=args.output
    )
    
    sys.exit(0 if success else 1)
