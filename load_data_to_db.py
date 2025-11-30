#!/usr/bin/env python3
"""
Load IEEE-CIS fraud detection data into PostgreSQL database.
Populates ACCOUNT, MERCHANT, DEVICE, TRANSACTION, and SHARED_DEVICE tables.
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import logging
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, host='localhost', port=5432, database='fraud_detection', 
                 user='fraud_user', password='fraud_password123'):
        """Initialize database connection."""
        self.conn = None
        self.cursor = None
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
    
    def connect(self):
        """Connect to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.cursor = self.conn.cursor()
            logger.info("✓ Connected to PostgreSQL database")
            return True
        except psycopg2.Error as e:
            logger.error(f"✗ Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("✓ Disconnected from database")
    
    def clear_tables(self):
        """Clear existing data from all tables (in correct order due to FKs)."""
        logger.info("Clearing existing tables...")
        try:
            # Order matters due to foreign keys
            tables = ['shared_device', 'transaction', 'device', 'merchant', 'account']
            for table in tables:
                self.cursor.execute(f"DELETE FROM {table};")
            self.conn.commit()
            logger.info("✓ Tables cleared")
        except psycopg2.Error as e:
            logger.error(f"✗ Error clearing tables: {e}")
            self.conn.rollback()
    
    def load_ieee_cis_data(self, filepath=None, nrows=None):
        """Load IEEE-CIS CSV files."""
        if filepath is None:
            filepath = Path('data/raw/train_transaction.csv')
        
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            logger.info("Please download from: https://www.kaggle.com/c/ieee-fraud-detection/data")
            return None
        
        logger.info(f"Loading data from {filepath}...")
        df = pd.read_csv(filepath, nrows=nrows)
        logger.info(f"✓ Loaded {len(df)} rows")
        return df
    
    def insert_accounts(self, transactions_df):
        """Extract and insert unique accounts."""
        logger.info("Inserting accounts...")
        
        # Extract unique accounts with features
        account_data = []
        for account_id in tqdm(transactions_df['card_1'].dropna().unique(), desc="Processing accounts"):
            account_txns = transactions_df[transactions_df['card_1'] == account_id]
            
            fraud_count = (account_txns['isFraud'] == 1).sum()
            total_count = len(account_txns)
            fraud_rate = fraud_count / total_count if total_count > 0 else 0
            
            # Calculate risk score (0-100)
            risk_score = int(min(100, fraud_rate * 100 + (fraud_count * 2)))
            fraud_flag = 1 if fraud_rate > 0.1 else 0
            
            # Extract email domain if available
            email_domain = 'unknown'
            device_info = account_txns['DeviceInfo'].iloc[0] if 'DeviceInfo' in account_txns else 'unknown'
            if isinstance(device_info, str) and '@' in device_info:
                email_domain = device_info.split('@')[-1]
            
            country = account_txns['addr1'].iloc[0] if 'addr1' in account_txns else 'US'
            country = 'US' if pd.isna(country) else str(int(country))
            
            created_at = account_txns['TransactionDT'].min() if 'TransactionDT' in account_txns else 0
            
            account_data.append((
                int(account_id),
                risk_score,
                fraud_flag,
                email_domain,
                country,
                datetime.now() - timedelta(days=30)
            ))
        
        # Batch insert
        sql = """INSERT INTO account (account_id, risk_score, fraud_flag, email_domain, country, created_at)
                 VALUES (%s, %s, %s, %s, %s, %s)
                 ON CONFLICT (account_id) DO NOTHING"""
        
        execute_batch(self.cursor, sql, account_data, page_size=1000)
        self.conn.commit()
        logger.info(f"✓ Inserted {len(account_data)} accounts")
    
    def insert_merchants(self, transactions_df):
        """Extract and insert unique merchants."""
        logger.info("Inserting merchants...")
        
        merchant_data = []
        for merchant_id in tqdm(transactions_df['merchant_id'].dropna().unique(), desc="Processing merchants"):
            merchant_txns = transactions_df[transactions_df['merchant_id'] == merchant_id]
            
            fraud_count = (merchant_txns['isFraud'] == 1).sum()
            total_count = len(merchant_txns)
            fraud_rate = fraud_count / total_count if total_count > 0 else 0
            
            # Categorize risk level
            if fraud_rate > 0.2:
                risk_level = 'high'
            elif fraud_rate > 0.1:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            # Extract category from product code
            category = 'electronics'  # default
            
            merchant_data.append((
                int(merchant_id),
                category,
                round(fraud_rate, 4),
                risk_level
            ))
        
        sql = """INSERT INTO merchant (merchant_id, category, fraud_rate, risk_level)
                 VALUES (%s, %s, %s, %s)
                 ON CONFLICT (merchant_id) DO NOTHING"""
        
        execute_batch(self.cursor, sql, merchant_data, page_size=1000)
        self.conn.commit()
        logger.info(f"✓ Inserted {len(merchant_data)} merchants")
    
    def insert_devices(self, transactions_df):
        """Extract and insert unique devices."""
        logger.info("Inserting devices...")
        
        device_data = []
        for device_id in tqdm(transactions_df['device_id'].dropna().unique(), desc="Processing devices"):
            device_txns = transactions_df[transactions_df['device_id'] == device_id]
            
            fraud_count = (device_txns['isFraud'] == 1).sum()
            total_count = len(device_txns)
            fraud_rate = fraud_count / total_count if total_count > 0 else 0
            
            unique_accounts = device_txns['card_1'].nunique()
            is_shared = 1 if unique_accounts > 1 else 0
            
            device_type = 'mobile'  # default
            
            device_data.append((
                int(device_id),
                device_type,
                is_shared,
                round(fraud_rate, 4),
                unique_accounts
            ))
        
        sql = """INSERT INTO device (device_id, device_type, is_shared, fraud_rate, total_users)
                 VALUES (%s, %s, %s, %s, %s)
                 ON CONFLICT (device_id) DO NOTHING"""
        
        execute_batch(self.cursor, sql, device_data, page_size=1000)
        self.conn.commit()
        logger.info(f"✓ Inserted {len(device_data)} devices")
    
    def insert_transactions(self, transactions_df):
        """Insert transaction records."""
        logger.info("Inserting transactions...")
        
        transaction_data = []
        for idx, row in tqdm(transactions_df.iterrows(), total=len(transactions_df), desc="Processing transactions"):
            try:
                txn_id = f"TXN_{int(row.get('TransactionID', idx)):010d}"
                account_id = int(row.get('card_1', 0))
                merchant_id = int(row.get('merchant_id', 0))
                device_id = int(row.get('device_id', 0))
                amount = float(row.get('TransactionAmt', 0))
                is_fraud = int(row.get('isFraud', 0))
                
                # Convert TransactionDT to datetime (seconds since epoch)
                txn_dt = row.get('TransactionDT', 0)
                if isinstance(txn_dt, (int, float)):
                    transaction_date = datetime.fromtimestamp(txn_dt)
                else:
                    transaction_date = datetime.now()
                
                transaction_data.append((
                    txn_id,
                    account_id,
                    merchant_id,
                    device_id,
                    amount,
                    is_fraud,
                    transaction_date
                ))
                
                # Insert in batches
                if len(transaction_data) >= 5000:
                    sql = """INSERT INTO transaction (transaction_id, account_id, merchant_id, device_id, amount, is_fraud, transaction_date)
                             VALUES (%s, %s, %s, %s, %s, %s, %s)
                             ON CONFLICT (transaction_id) DO NOTHING"""
                    execute_batch(self.cursor, sql, transaction_data, page_size=1000)
                    self.conn.commit()
                    transaction_data = []
            except Exception as e:
                logger.warning(f"Skipping row {idx}: {e}")
                continue
        
        # Insert remaining
        if transaction_data:
            sql = """INSERT INTO transaction (transaction_id, account_id, merchant_id, device_id, amount, is_fraud, transaction_date)
                     VALUES (%s, %s, %s, %s, %s, %s, %s)
                     ON CONFLICT (transaction_id) DO NOTHING"""
            execute_batch(self.cursor, sql, transaction_data, page_size=1000)
            self.conn.commit()
        
        logger.info(f"✓ Inserted {len(transaction_data)} transactions")
    
    def insert_shared_devices(self, transactions_df):
        """Insert shared device relationships."""
        logger.info("Inserting shared device relationships...")
        
        shared_device_data = []
        device_counts = {}
        
        # Find devices used by multiple accounts
        for device_id in tqdm(transactions_df['device_id'].dropna().unique(), desc="Finding shared devices"):
            accounts = transactions_df[transactions_df['device_id'] == device_id]['card_1'].unique()
            
            if len(accounts) > 1:
                device_counts[device_id] = accounts
                
                # Create pairs for first two accounts
                for i in range(min(2, len(accounts))):
                    for j in range(i+1, min(3, len(accounts))):
                        acc1 = int(accounts[i])
                        acc2 = int(accounts[j])
                        shared_count = len(transactions_df[
                            (transactions_df['device_id'] == device_id) &
                            ((transactions_df['card_1'] == acc1) | (transactions_df['card_1'] == acc2))
                        ])
                        fraud_count = len(transactions_df[
                            (transactions_df['device_id'] == device_id) &
                            ((transactions_df['card_1'] == acc1) | (transactions_df['card_1'] == acc2)) &
                            (transactions_df['isFraud'] == 1)
                        ])
                        fraud_prob = fraud_count / shared_count if shared_count > 0 else 0
                        
                        shared_device_data.append((
                            int(device_id),
                            acc1,
                            acc2,
                            shared_count,
                            round(fraud_prob, 4)
                        ))
        
        if shared_device_data:
            sql = """INSERT INTO shared_device (device_id, account_id_1, account_id_2, shared_count, fraud_probability)
                     VALUES (%s, %s, %s, %s, %s)
                     ON CONFLICT (device_id, account_id_1, account_id_2) DO NOTHING"""
            execute_batch(self.cursor, sql, shared_device_data, page_size=1000)
            self.conn.commit()
        
        logger.info(f"✓ Inserted {len(shared_device_data)} shared device records")
    
    def verify_data(self):
        """Verify data was loaded correctly."""
        logger.info("\n📊 Data Verification:")
        
        sql_counts = {
            'account': "SELECT COUNT(*) FROM account",
            'merchant': "SELECT COUNT(*) FROM merchant",
            'device': "SELECT COUNT(*) FROM device",
            'transaction': "SELECT COUNT(*) FROM transaction",
            'shared_device': "SELECT COUNT(*) FROM shared_device"
        }
        
        for table, sql in sql_counts.items():
            self.cursor.execute(sql)
            count = self.cursor.fetchone()[0]
            print(f"  ✓ {table.capitalize()}: {count:,} rows")
        
        # Fraud statistics
        self.cursor.execute("SELECT COUNT(*) FROM transaction WHERE is_fraud = 1")
        fraud_count = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM transaction")
        total = self.cursor.fetchone()[0]
        fraud_rate = (fraud_count / total * 100) if total > 0 else 0
        print(f"\n  📈 Fraud Statistics:")
        print(f"     - Total transactions: {total:,}")
        print(f"     - Fraudulent: {fraud_count:,} ({fraud_rate:.2f}%)")
        print(f"     - Legitimate: {total - fraud_count:,}")
    
    def run(self, nrows=None, clear_first=True):
        """Main ETL pipeline."""
        try:
            # Connect to database
            if not self.connect():
                return False
            
            # Clear existing data
            if clear_first:
                self.clear_tables()
            
            # Load data
            df = self.load_ieee_cis_data(nrows=nrows)
            if df is None or df.empty:
                logger.warning("No data to load. Please download IEEE-CIS dataset.")
                return False
            
            # Standardize columns
            self._standardize_columns(df)
            
            # Load into database
            self.insert_accounts(df)
            self.insert_merchants(df)
            self.insert_devices(df)
            self.insert_transactions(df)
            self.insert_shared_devices(df)
            
            # Verify
            self.verify_data()
            
            logger.info("\n✅ Data load completed successfully!")
            return True
        
        except Exception as e:
            logger.error(f"✗ Error: {e}")
            return False
        finally:
            self.disconnect()
    
    def _standardize_columns(self, df):
        """Standardize column names for IEEE-CIS dataset."""
        column_mapping = {
            'isFraud': 'is_fraud',
            'TransactionAmt': 'transaction_amount',
            'TransactionDT': 'transaction_dt',
            'DeviceInfo': 'device_info'
        }
        df.rename(columns=column_mapping, inplace=True)
        return df


if __name__ == '__main__':
    import sys
    
    print("\n" + "="*60)
    print("IEEE-CIS Fraud Detection Data Loader")
    print("="*60 + "\n")
    
    # Get number of rows from command line
    nrows = None
    if len(sys.argv) > 1:
        try:
            nrows = int(sys.argv[1])
            logger.info(f"Loading {nrows} rows...")
        except ValueError:
            logger.warning("Invalid row count. Loading all data...")
    else:
        nrows = 50000  # Default to first 50k for faster loading
        logger.info(f"Using default: {nrows} rows. Use 'python load_data_to_db.py <nrows>' for different amount")
    
    # Run loader
    loader = DataLoader()
    success = loader.run(nrows=nrows, clear_first=True)
    
    if success:
        print("\n✅ Ready to use with dashboard!")
        print("\nNext steps:")
        print("  1. Open pgAdmin: http://localhost:5050")
        print("  2. Connect to: localhost:5432 (fraud_user)")
        print("  3. Run dashboard: streamlit run src/visualization/advanced_dashboard.py")
    else:
        print("\n⚠️  Check PostgreSQL is running and database is configured")
        print("   Run: python setup_postgres.py")
