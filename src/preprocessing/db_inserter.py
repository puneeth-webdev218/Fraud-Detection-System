"""
Database Insertion Module
Handles efficient bulk insertion of processed data into PostgreSQL
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import logging
from tqdm import tqdm
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.config import config
from src.database.connection import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_PATH / 'db_insertion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabaseInserter:
    """
    Handles bulk insertion of data into PostgreSQL database
    """
    
    def __init__(self, batch_size: int = 5000):
        self.batch_size = batch_size
        self.processed_data_path = config.DATA_PROCESSED_PATH
    
    def prepare_account_data(self, df: pd.DataFrame) -> List[tuple]:
        """Prepare account data for insertion"""
        df = df.copy()
        
        # Handle NaN values
        df = df.replace({np.nan: None})
        
        records = []
        for _, row in df.iterrows():
            record = (
                row['account_id'],
                row.get('creation_date', pd.Timestamp('now')),
                row.get('email_domain'),
                row.get('country'),
                float(row.get('risk_score', 0.0)),
                int(row.get('total_transactions', 0)),
                float(row.get('total_amount', 0.0)),
                bool(row.get('fraud_flag', False)),
                row.get('last_transaction_date'),
                int(row.get('account_age_days', 0)) if pd.notna(row.get('account_age_days')) else 0
            )
            records.append(record)
        
        return records
    
    def prepare_merchant_data(self, df: pd.DataFrame) -> List[tuple]:
        """Prepare merchant data for insertion"""
        df = df.copy()
        df = df.replace({np.nan: None})
        
        records = []
        for _, row in df.iterrows():
            record = (
                row['merchant_id'],
                row.get('merchant_name'),
                row.get('merchant_category'),
                row.get('country'),
                int(row.get('total_transactions', 0)),
                int(row.get('total_fraud_transactions', 0)),
                float(row.get('fraud_rate', 0.0)),
                float(row.get('avg_transaction_amount', 0.0)),
                str(row.get('risk_level', 'LOW'))
            )
            records.append(record)
        
        return records
    
    def prepare_device_data(self, df: pd.DataFrame) -> List[tuple]:
        """Prepare device data for insertion"""
        df = df.copy()
        df = df.replace({np.nan: None})
        
        records = []
        for _, row in df.iterrows():
            record = (
                row['device_id'],
                row.get('device_type'),
                row.get('device_info'),
                row.get('os_id'),
                row.get('browser_id'),
                row.get('screen_resolution'),
                int(row.get('total_users', 0)),
                int(row.get('total_transactions', 0)),
                int(row.get('fraud_transactions', 0)),
                float(row.get('fraud_rate', 0.0)),
                bool(row.get('is_shared', False)),
                float(row.get('risk_score', 0.0))
            )
            records.append(record)
        
        return records
    
    def prepare_transaction_data(self, df: pd.DataFrame) -> List[tuple]:
        """Prepare transaction data for insertion"""
        df = df.copy()
        df = df.replace({np.nan: None})
        
        records = []
        for _, row in df.iterrows():
            record = (
                row['transaction_id'],
                row['account_id'],
                row['merchant_id'],
                row.get('device_id'),
                row['transaction_date'],
                float(row['transaction_amount']),
                row.get('product_category'),
                row.get('card_type'),
                row.get('card_category'),
                row.get('transaction_type'),
                row.get('addr_country'),
                int(row['transaction_hour']) if pd.notna(row.get('transaction_hour')) else None,
                int(row['transaction_day_of_week']) if pd.notna(row.get('transaction_day_of_week')) else None,
                int(row['transaction_day_of_month']) if pd.notna(row.get('transaction_day_of_month')) else None,
                row.get('email_domain'),
                row.get('distance_from_last_txn'),
                row.get('time_since_last_txn'),
                bool(row['is_fraud'])
            )
            records.append(record)
        
        return records
    
    def prepare_shared_device_data(self, df: pd.DataFrame) -> List[tuple]:
        """Prepare shared device data for insertion"""
        df = df.copy()
        df = df.replace({np.nan: None})
        
        records = []
        for _, row in df.iterrows():
            record = (
                row['device_id'],
                row['account_id'],
                row.get('first_seen', pd.Timestamp('now')),
                row.get('last_seen', pd.Timestamp('now')),
                int(row.get('transaction_count', 1)),
                int(row.get('fraud_count', 0))
            )
            records.append(record)
        
        return records
    
    def insert_accounts(self, records: List[tuple]) -> int:
        """Insert account records in batches"""
        logger.info(f"Inserting {len(records):,} account records...")
        
        query = """
            INSERT INTO account (
                account_id, creation_date, email_domain, country, 
                risk_score, total_transactions, total_amount, 
                fraud_flag, last_transaction_date, account_age_days
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_id) DO NOTHING
        """
        
        inserted = 0
        for i in tqdm(range(0, len(records), self.batch_size), desc="Accounts"):
            batch = records[i:i + self.batch_size]
            try:
                db.execute_batch(query, batch, page_size=self.batch_size)
                inserted += len(batch)
            except Exception as e:
                logger.error(f"Error inserting account batch: {e}")
                continue
        
        logger.info(f"✓ Inserted {inserted:,} accounts")
        return inserted
    
    def insert_merchants(self, records: List[tuple]) -> int:
        """Insert merchant records in batches"""
        logger.info(f"Inserting {len(records):,} merchant records...")
        
        query = """
            INSERT INTO merchant (
                merchant_id, merchant_name, merchant_category, country,
                total_transactions, total_fraud_transactions, fraud_rate,
                avg_transaction_amount, risk_level
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (merchant_id) DO NOTHING
        """
        
        inserted = 0
        for i in tqdm(range(0, len(records), self.batch_size), desc="Merchants"):
            batch = records[i:i + self.batch_size]
            try:
                db.execute_batch(query, batch, page_size=self.batch_size)
                inserted += len(batch)
            except Exception as e:
                logger.error(f"Error inserting merchant batch: {e}")
                continue
        
        logger.info(f"✓ Inserted {inserted:,} merchants")
        return inserted
    
    def insert_devices(self, records: List[tuple]) -> int:
        """Insert device records in batches"""
        logger.info(f"Inserting {len(records):,} device records...")
        
        query = """
            INSERT INTO device (
                device_id, device_type, device_info, os_id, browser_id,
                screen_resolution, total_users, total_transactions,
                fraud_transactions, fraud_rate, is_shared, risk_score
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (device_id) DO NOTHING
        """
        
        inserted = 0
        for i in tqdm(range(0, len(records), self.batch_size), desc="Devices"):
            batch = records[i:i + self.batch_size]
            try:
                db.execute_batch(query, batch, page_size=self.batch_size)
                inserted += len(batch)
            except Exception as e:
                logger.error(f"Error inserting device batch: {e}")
                continue
        
        logger.info(f"✓ Inserted {inserted:,} devices")
        return inserted
    
    def insert_transactions(self, records: List[tuple]) -> int:
        """Insert transaction records in batches (disable triggers temporarily)"""
        logger.info(f"Inserting {len(records):,} transaction records...")
        
        # Disable triggers for faster bulk insert
        logger.info("Disabling triggers for bulk insert...")
        disable_triggers = """
            ALTER TABLE transaction DISABLE TRIGGER trg_update_account_stats;
            ALTER TABLE transaction DISABLE TRIGGER trg_update_merchant_stats;
            ALTER TABLE transaction DISABLE TRIGGER trg_update_device_stats;
        """
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(disable_triggers)
        except Exception as e:
            logger.warning(f"Could not disable triggers: {e}")
        
        query = """
            INSERT INTO transaction (
                transaction_id, account_id, merchant_id, device_id,
                transaction_date, transaction_amount, product_category,
                card_type, card_category, transaction_type, addr_country,
                transaction_hour, transaction_day_of_week, transaction_day_of_month,
                email_domain, distance_from_last_txn, time_since_last_txn, is_fraud
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (transaction_id) DO NOTHING
        """
        
        inserted = 0
        for i in tqdm(range(0, len(records), self.batch_size), desc="Transactions"):
            batch = records[i:i + self.batch_size]
            try:
                db.execute_batch(query, batch, page_size=self.batch_size)
                inserted += len(batch)
            except Exception as e:
                logger.error(f"Error inserting transaction batch at {i}: {e}")
                continue
        
        # Re-enable triggers
        logger.info("Re-enabling triggers...")
        enable_triggers = """
            ALTER TABLE transaction ENABLE TRIGGER trg_update_account_stats;
            ALTER TABLE transaction ENABLE TRIGGER trg_update_merchant_stats;
            ALTER TABLE transaction ENABLE TRIGGER trg_update_device_stats;
        """
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(enable_triggers)
        except Exception as e:
            logger.warning(f"Could not re-enable triggers: {e}")
        
        logger.info(f"✓ Inserted {inserted:,} transactions")
        return inserted
    
    def insert_shared_devices(self, records: List[tuple]) -> int:
        """Insert shared device records in batches"""
        logger.info(f"Inserting {len(records):,} shared device records...")
        
        query = """
            INSERT INTO shared_device (
                device_id, account_id, first_seen, last_seen,
                transaction_count, fraud_count
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (device_id, account_id) DO UPDATE SET
                last_seen = EXCLUDED.last_seen,
                transaction_count = EXCLUDED.transaction_count,
                fraud_count = EXCLUDED.fraud_count
        """
        
        inserted = 0
        for i in tqdm(range(0, len(records), self.batch_size), desc="Shared Devices"):
            batch = records[i:i + self.batch_size]
            try:
                db.execute_batch(query, batch, page_size=self.batch_size)
                inserted += len(batch)
            except Exception as e:
                logger.error(f"Error inserting shared device batch: {e}")
                continue
        
        logger.info(f"✓ Inserted {inserted:,} shared device records")
        return inserted
    
    def load_from_csv(self, filename: str) -> pd.DataFrame:
        """Load processed CSV file"""
        filepath = self.processed_data_path / filename
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        logger.info(f"Loading {filename}...")
        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df):,} rows")
        return df
    
    def insert_all_data(self) -> Dict[str, int]:
        """
        Main insertion pipeline - loads and inserts all data
        
        Returns:
            Dictionary of table names and row counts inserted
        """
        logger.info("=" * 70)
        logger.info("Starting database insertion pipeline")
        logger.info("=" * 70)
        
        results = {}
        
        # 1. Insert Accounts (must be first - referenced by transactions)
        try:
            accounts_df = self.load_from_csv('accounts.csv')
            account_records = self.prepare_account_data(accounts_df)
            results['accounts'] = self.insert_accounts(account_records)
        except Exception as e:
            logger.error(f"Failed to insert accounts: {e}")
            results['accounts'] = 0
        
        # 2. Insert Merchants (must be before transactions)
        try:
            merchants_df = self.load_from_csv('merchants.csv')
            merchant_records = self.prepare_merchant_data(merchants_df)
            results['merchants'] = self.insert_merchants(merchant_records)
        except Exception as e:
            logger.error(f"Failed to insert merchants: {e}")
            results['merchants'] = 0
        
        # 3. Insert Devices (must be before transactions)
        try:
            devices_df = self.load_from_csv('devices.csv')
            device_records = self.prepare_device_data(devices_df)
            results['devices'] = self.insert_devices(device_records)
        except Exception as e:
            logger.error(f"Failed to insert devices: {e}")
            results['devices'] = 0
        
        # 4. Insert Transactions (references accounts, merchants, devices)
        try:
            transactions_df = self.load_from_csv('transactions.csv')
            transaction_records = self.prepare_transaction_data(transactions_df)
            results['transactions'] = self.insert_transactions(transaction_records)
        except Exception as e:
            logger.error(f"Failed to insert transactions: {e}")
            results['transactions'] = 0
        
        # 5. Insert Shared Devices (references devices and accounts)
        try:
            shared_devices_df = self.load_from_csv('shared_devices.csv')
            shared_device_records = self.prepare_shared_device_data(shared_devices_df)
            results['shared_devices'] = self.insert_shared_devices(shared_device_records)
        except Exception as e:
            logger.error(f"Failed to insert shared devices: {e}")
            results['shared_devices'] = 0
        
        logger.info("=" * 70)
        logger.info("Database insertion complete!")
        logger.info("=" * 70)
        
        return results
    
    def verify_insertion(self) -> None:
        """Verify data was inserted correctly"""
        logger.info("\nVerifying data insertion...")
        
        tables = ['account', 'merchant', 'device', 'transaction', 'shared_device']
        
        for table in tables:
            try:
                count = db.get_table_count(table)
                logger.info(f"  ✓ {table}: {count:,} rows")
            except Exception as e:
                logger.error(f"  ✗ {table}: Error - {e}")
        
        # Check fraud statistics
        try:
            fraud_stats = db.execute_query("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) as fraud_count,
                    ROUND(AVG(CASE WHEN is_fraud THEN 1.0 ELSE 0.0 END) * 100, 2) as fraud_percentage
                FROM transaction
            """)
            
            if fraud_stats:
                stats = fraud_stats[0]
                logger.info(f"\nFraud Statistics:")
                logger.info(f"  Total transactions: {stats['total']:,}")
                logger.info(f"  Fraud transactions: {stats['fraud_count']:,}")
                logger.info(f"  Fraud rate: {stats['fraud_percentage']}%")
        except Exception as e:
            logger.error(f"Error getting fraud statistics: {e}")


if __name__ == "__main__":
    inserter = DatabaseInserter(batch_size=5000)
    
    # Insert all data
    results = inserter.insert_all_data()
    
    # Display results
    print("\n" + "=" * 70)
    print("Insertion Summary:")
    print("=" * 70)
    for table, count in results.items():
        print(f"  {table}: {count:,} rows inserted")
    
    # Verify
    inserter.verify_insertion()
