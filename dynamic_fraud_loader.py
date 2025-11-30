#!/usr/bin/env python3
"""
Dynamic Fraud Detection Pipeline with PostgreSQL Integration
User-driven transaction loading and automatic database updates

Usage:
    python dynamic_fraud_loader.py
    → Prompts user for number of transactions to load
    → Loads specified rows from dataset
    → Runs fraud detection
    → Automatically inserts into PostgreSQL
    → Displays confirmation with database stats
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import argparse
from typing import Tuple

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.dynamic_postgres_manager import PostgreSQLManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DynamicFraudDetectionPipeline:
    """
    Manages dynamic fraud detection pipeline with PostgreSQL integration
    """
    
    def __init__(self, dataset_path: str = "data/raw/train_transaction.csv"):
        """
        Initialize the pipeline
        
        Args:
            dataset_path: Path to transaction dataset CSV
        """
        self.dataset_path = Path(dataset_path)
        self.db_manager = None
        self.processed_df = None
    
    def load_transactions(self, num_rows: int) -> pd.DataFrame:
        """
        Load specified number of transactions from dataset
        
        Args:
            num_rows: Number of rows to load
        
        Returns:
            DataFrame with transaction data
        """
        logger.info(f"\n📊 Loading {num_rows:,} transactions from dataset...")
        
        if not self.dataset_path.exists():
            logger.error(f"✗ Dataset not found: {self.dataset_path}")
            return None
        
        try:
            # Load specified columns
            df = pd.read_csv(
                self.dataset_path,
                nrows=num_rows,
                usecols=['TransactionID', 'TransactionDT', 'TransactionAmt', 'isFraud']
            )
            
            logger.info(f"✓ Loaded {len(df):,} transactions")
            logger.info(f"  ├─ Fraud cases: {df['isFraud'].sum()}")
            logger.info(f"  ├─ Amount range: ${df['TransactionAmt'].min():.2f} - ${df['TransactionAmt'].max():.2f}")
            logger.info(f"  └─ Avg amount: ${df['TransactionAmt'].mean():.2f}")
            
            return df
            
        except Exception as e:
            logger.error(f"✗ Failed to load dataset: {e}")
            return None
    
    def process_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process transactions for database insertion
        
        Args:
            df: Raw transaction DataFrame
        
        Returns:
            Processed DataFrame ready for insertion
        """
        logger.info(f"\n🔍 Processing transactions for fraud detection...")
        
        if df is None or df.empty:
            logger.error("✗ No data to process")
            return None
        
        try:
            processed = df.copy()
            
            # Rename columns to match database schema
            processed = processed.rename(columns={
                'TransactionID': 'transaction_id',
                'TransactionAmt': 'amount',
                'isFraud': 'fraud_flag',
                'TransactionDT': 'timestamp'
            })
            
            # Generate synthetic IDs for references (in real scenario, would come from data)
            processed['account_id'] = (processed['transaction_id'] % 100) + 1
            processed['merchant_id'] = (processed['transaction_id'] % 15) + 1
            processed['device_id'] = (processed['transaction_id'] % 10) + 1
            
            # Convert timestamp to datetime if needed
            if processed['timestamp'].dtype != 'datetime64[ns]':
                # Create realistic timestamps
                base_date = datetime.now()
                processed['timestamp'] = [
                    base_date - timedelta(hours=abs(int(tid) % 720))
                    for tid in processed['transaction_id']
                ]
            
            # Select relevant columns for insertion
            insert_df = processed[[
                'transaction_id', 'account_id', 'merchant_id', 'device_id',
                'amount', 'timestamp', 'fraud_flag'
            ]].copy()
            
            # Data type conversion
            insert_df['transaction_id'] = insert_df['transaction_id'].astype('int64')
            insert_df['account_id'] = insert_df['account_id'].astype('int32')
            insert_df['merchant_id'] = insert_df['merchant_id'].astype('int32')
            insert_df['device_id'] = insert_df['device_id'].astype('int32')
            insert_df['amount'] = insert_df['amount'].astype('float64')
            insert_df['fraud_flag'] = insert_df['fraud_flag'].astype('bool')
            
            logger.info(f"✓ Processed {len(insert_df):,} transactions")
            logger.info(f"  ├─ Fraud cases: {insert_df['fraud_flag'].sum()}")
            logger.info(f"  ├─ Fraud rate: {insert_df['fraud_flag'].mean()*100:.2f}%")
            logger.info(f"  └─ Ready for database insertion")
            
            self.processed_df = insert_df
            return insert_df
            
        except Exception as e:
            logger.error(f"✗ Processing failed: {e}")
            return None
    
    def connect_database(self) -> bool:
        """
        Connect to PostgreSQL database
        
        Returns:
            True if connection successful
        """
        logger.info(f"\n🗄️  Connecting to PostgreSQL database...")
        
        self.db_manager = PostgreSQLManager()
        
        if not self.db_manager.connect():
            logger.error("✗ Database connection failed")
            return False
        
        logger.info("✓ Connected to PostgreSQL")
        return True
    
    def reset_database(self) -> bool:
        """
        Reset database - clear all old transaction data
        
        Returns:
            True if reset successful
        """
        logger.info(f"\n🧹 Resetting database...")
        
        if not self.db_manager:
            logger.error("✗ No database connection")
            return False
        
        if not self.db_manager.reset_transactions_table():
            logger.error("✗ Failed to reset database")
            return False
        
        logger.info("✓ Database reset")
        return True
    
    def setup_database(self) -> bool:
        """
        Create transactions table if not exists
        
        Returns:
            True if table setup successful
        """
        logger.info(f"\n📋 Setting up database table...")
        
        if not self.db_manager:
            logger.error("✗ No database connection")
            return False
        
        if not self.db_manager.create_transactions_table():
            logger.error("✗ Failed to create transactions table")
            return False
        
        logger.info("✓ Transactions table ready")
        return True
    
    def insert_to_database(self) -> Tuple[int, int]:
        """
        Insert processed transactions into database
        
        Returns:
            Tuple of (inserted_count, skipped_count)
        """
        logger.info(f"\n📥 Inserting transactions into database...")
        
        if not self.db_manager or not self.processed_df is not None:
            logger.error("✗ Pipeline not properly initialized")
            return 0, 0
        
        inserted, skipped = self.db_manager.insert_transactions_batch(self.processed_df)
        
        if inserted > 0:
            # Verify insertion count immediately after commit
            actual_count = self.db_manager.get_transaction_count()
            logger.info(f"✓ Database updated successfully!")
            logger.info(f"  ├─ Inserted: {inserted:,}")
            logger.info(f"  ├─ Skipped:  {skipped:,}")
            logger.info(f"  └─ Verified in DB: {actual_count:,} total transactions")
        
        return inserted, skipped
    
    def show_database_stats(self) -> None:
        """Display current database statistics"""
        if not self.db_manager:
            return
        
        logger.info(f"\n📊 Database Statistics:")
        
        total_count = self.db_manager.get_transaction_count()
        stats = self.db_manager.get_fraud_stats()
        
        logger.info(f"  ├─ Total transactions: {total_count:,}")
        logger.info(f"  ├─ Fraudulent cases: {stats.get('fraud_count', 0)}")
        logger.info(f"  ├─ Fraud rate: {stats.get('fraud_rate', 0):.2f}%")
        logger.info(f"  ├─ Avg amount: ${stats.get('avg_amount', 0):.2f}")
        logger.info(f"  ├─ Min amount: ${stats.get('min_amount', 0):.2f}")
        logger.info(f"  └─ Max amount: ${stats.get('max_amount', 0):.2f}")
    
    def disconnect(self) -> None:
        """Disconnect from database"""
        if self.db_manager:
            self.db_manager.disconnect()
    
    def run(self, num_rows: int) -> bool:
        """
        Run complete pipeline
        
        Args:
            num_rows: Number of transactions to load
        
        Returns:
            True if pipeline completed successfully
        """
        try:
            print("\n" + "="*80)
            print("DYNAMIC FRAUD DETECTION PIPELINE")
            print("="*80)
            
            # Step 1: Load transactions
            df = self.load_transactions(num_rows)
            if df is None:
                return False
            
            # Step 2: Process transactions
            processed_df = self.process_transactions(df)
            if processed_df is None:
                return False
            
            # Step 3: Connect to database
            if not self.connect_database():
                return False
            
            # Step 4: Reset database (clear old data)
            if not self.reset_database():
                return False
            
            # Step 5: Setup database
            if not self.setup_database():
                return False
            
            # Step 6: Insert to database
            inserted, skipped = self.insert_to_database()
            
            # Step 7: Show statistics
            self.show_database_stats()
            
            # Step 8: Verify commit completed and data is visible
            final_count = self.db_manager.get_transaction_count()
            
            # Success message - ONLY after verified commit
            print("\n" + "="*80)
            print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
            print("="*80)
            print(f"\n✔ Database updated — check pgAdmin")
            print(f"\n  {final_count:,} transactions now visible in pgAdmin")
            print(f"  Open pgAdmin: http://localhost:5050")
            print(f"  Navigate to: fraud_detection → transactions")
            print(f"  Test query: SELECT COUNT(*) FROM transactions;")
            print(f"  Expected result: {final_count:,}")
            print("\n" + "="*80 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Pipeline failed: {e}")
            return False
        
        finally:
            self.disconnect()


def get_user_input() -> int:
    """
    Get number of transactions from user
    
    Returns:
        Number of rows to load
    """
    while True:
        try:
            print("\n" + "="*80)
            print("DYNAMIC TRANSACTION LOADER")
            print("="*80)
            print("\nHow many transactions would you like to load?")
            print("Enter a number (e.g., 100, 1000, 10000):")
            
            num_str = input("\n> ").strip()
            
            if not num_str.isdigit():
                print("❌ Please enter a valid number")
                continue
            
            num = int(num_str)
            
            if num <= 0:
                print("❌ Number must be greater than 0")
                continue
            
            if num > 1000000:
                print("⚠️  Large number detected. This may take a while.")
                confirm = input("Continue? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    continue
            
            return num
            
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Dynamic Fraud Detection Pipeline with PostgreSQL Integration'
    )
    parser.add_argument(
        '--rows',
        type=int,
        default=None,
        help='Number of transactions to load (if not provided, user will be prompted)'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default='data/raw/train_transaction.csv',
        help='Path to transaction dataset CSV'
    )
    
    args = parser.parse_args()
    
    # Get number of rows
    num_rows = args.rows if args.rows else get_user_input()
    
    # Create and run pipeline
    pipeline = DynamicFraudDetectionPipeline(args.dataset)
    
    success = pipeline.run(num_rows)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
