"""
Data Loading and Preprocessing Module
Handles IEEE-CIS dataset loading, cleaning, and database insertion
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging
from datetime import datetime
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
        logging.FileHandler(config.LOG_PATH / 'data_loading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataLoader:
    """
    Handles loading and preprocessing of IEEE-CIS fraud detection dataset
    """
    
    def __init__(self):
        self.raw_data_path = config.DATA_RAW_PATH
        self.processed_data_path = config.DATA_PROCESSED_PATH
        self.batch_size = 10000
        
    def load_csv_files(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load transaction and identity CSV files
        
        Returns:
            Tuple of (transaction_df, identity_df)
        """
        logger.info("Loading CSV files...")
        
        # Load transaction data
        transaction_file = self.raw_data_path / 'train_transaction.csv'
        if not transaction_file.exists():
            raise FileNotFoundError(f"Transaction file not found: {transaction_file}")
        
        logger.info(f"Reading transaction file: {transaction_file.name}")
        transaction_df = pd.read_csv(transaction_file)
        logger.info(f"Loaded {len(transaction_df):,} transactions")
        
        # Load identity data
        identity_file = self.raw_data_path / 'train_identity.csv'
        if not identity_file.exists():
            logger.warning(f"Identity file not found: {identity_file}")
            identity_df = pd.DataFrame()
        else:
            logger.info(f"Reading identity file: {identity_file.name}")
            identity_df = pd.read_csv(identity_file)
            logger.info(f"Loaded {len(identity_df):,} identity records")
        
        return transaction_df, identity_df
    
    def merge_datasets(self, transaction_df: pd.DataFrame, identity_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge transaction and identity datasets
        
        Args:
            transaction_df: Transaction data
            identity_df: Identity data
        
        Returns:
            Merged DataFrame
        """
        logger.info("Merging transaction and identity data...")
        
        if identity_df.empty:
            logger.warning("Identity dataset is empty, using only transaction data")
            return transaction_df
        
        merged_df = transaction_df.merge(
            identity_df,
            on='TransactionID',
            how='left'
        )
        
        logger.info(f"Merged dataset shape: {merged_df.shape}")
        return merged_df
    
    def extract_account_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract and aggregate account-level data
        
        Args:
            df: Merged transaction/identity DataFrame
        
        Returns:
            Account DataFrame
        """
        logger.info("Extracting account data...")
        
        # Create account_id from card identifiers
        df['account_id'] = df['card1'].astype(str) + '_' + df['card2'].fillna('0').astype(str)
        
        # Aggregate account statistics
        account_stats = df.groupby('account_id').agg({
            'TransactionID': 'count',
            'TransactionAmt': ['sum', 'mean'],
            'isFraud': ['sum', 'mean'],
            'TransactionDT': ['min', 'max']
        }).reset_index()
        
        # Flatten column names
        account_stats.columns = [
            'account_id', 'total_transactions', 'total_amount', 
            'avg_amount', 'fraud_count', 'fraud_rate', 
            'first_transaction', 'last_transaction'
        ]
        
        # Add email domain if available
        if 'P_emaildomain' in df.columns:
            email_domain = df.groupby('account_id')['P_emaildomain'].first()
            account_stats = account_stats.merge(
                email_domain.reset_index(), 
                on='account_id', 
                how='left'
            )
            account_stats.rename(columns={'P_emaildomain': 'email_domain'}, inplace=True)
        else:
            account_stats['email_domain'] = None
        
        # Add country if available
        if 'addr1' in df.columns:
            account_stats['country'] = df.groupby('account_id')['addr1'].first().values
        else:
            account_stats['country'] = None
        
        # Calculate risk score (normalized fraud rate)
        account_stats['risk_score'] = account_stats['fraud_rate'].clip(0, 1)
        
        # Calculate account age
        account_stats['account_age_days'] = (
            account_stats['last_transaction'] - account_stats['first_transaction']
        ) / (3600 * 24)  # Convert seconds to days
        
        # Set fraud flag
        account_stats['fraud_flag'] = account_stats['fraud_count'] > 0
        
        # Add timestamps
        account_stats['creation_date'] = pd.to_datetime('now')
        account_stats['last_transaction_date'] = pd.to_datetime('now')
        
        logger.info(f"Extracted {len(account_stats):,} accounts")
        return account_stats
    
    def extract_merchant_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract and aggregate merchant-level data
        
        Args:
            df: Merged DataFrame
        
        Returns:
            Merchant DataFrame
        """
        logger.info("Extracting merchant data...")
        
        # Use ProductCD as merchant identifier
        df['merchant_id'] = 'M_' + df['ProductCD'].astype(str)
        
        merchant_stats = df.groupby('merchant_id').agg({
            'TransactionID': 'count',
            'TransactionAmt': ['sum', 'mean'],
            'isFraud': ['sum', 'mean']
        }).reset_index()
        
        merchant_stats.columns = [
            'merchant_id', 'total_transactions', 'total_amount',
            'avg_transaction_amount', 'total_fraud_transactions', 'fraud_rate'
        ]
        
        # Add merchant category from ProductCD
        merchant_stats['merchant_category'] = df.groupby('merchant_id')['ProductCD'].first().values
        merchant_stats['merchant_name'] = 'Merchant_' + merchant_stats['merchant_id']
        
        # Add country if available
        if 'addr1' in df.columns:
            merchant_stats['country'] = df.groupby('merchant_id')['addr1'].first().values
        else:
            merchant_stats['country'] = None
        
        # Assign risk level based on fraud rate
        merchant_stats['risk_level'] = pd.cut(
            merchant_stats['fraud_rate'],
            bins=[-0.01, 0.05, 0.15, 0.30, 1.0],
            labels=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        )
        
        logger.info(f"Extracted {len(merchant_stats):,} merchants")
        return merchant_stats
    
    def extract_device_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract device-level data
        
        Args:
            df: Merged DataFrame
        
        Returns:
            Device DataFrame
        """
        logger.info("Extracting device data...")
        
        # Create device_id from device info
        device_cols = ['DeviceInfo', 'DeviceType']
        available_cols = [col for col in device_cols if col in df.columns]
        
        if 'DeviceInfo' in df.columns:
            df['device_id'] = 'D_' + df['DeviceInfo'].fillna('unknown').astype(str)
        else:
            df['device_id'] = 'D_unknown'
        
        device_stats = df.groupby('device_id').agg({
            'TransactionID': 'count',
            'isFraud': ['sum', 'mean'],
            'card1': 'nunique'  # Number of unique users
        }).reset_index()
        
        device_stats.columns = [
            'device_id', 'total_transactions', 
            'fraud_transactions', 'fraud_rate', 'total_users'
        ]
        
        # Add device type
        if 'DeviceType' in df.columns:
            device_stats['device_type'] = df.groupby('device_id')['DeviceType'].first().values
        else:
            device_stats['device_type'] = 'unknown'
        
        # Device info
        if 'DeviceInfo' in df.columns:
            device_stats['device_info'] = df.groupby('device_id')['DeviceInfo'].first().values
        else:
            device_stats['device_info'] = None
        
        # OS and Browser IDs
        for col in ['id_30', 'id_31']:
            if col in df.columns:
                col_name = 'os_id' if col == 'id_30' else 'browser_id'
                device_stats[col_name] = df.groupby('device_id')[col].first().values
            else:
                col_name = 'os_id' if col == 'id_30' else 'browser_id'
                device_stats[col_name] = None
        
        # Screen resolution
        if 'id_33' in df.columns:
            device_stats['screen_resolution'] = df.groupby('device_id')['id_33'].first().values
        else:
            device_stats['screen_resolution'] = None
        
        # Mark shared devices (used by multiple accounts)
        device_stats['is_shared'] = device_stats['total_users'] > 1
        
        # Risk score
        device_stats['risk_score'] = device_stats['fraud_rate'].clip(0, 1)
        
        logger.info(f"Extracted {len(device_stats):,} devices")
        logger.info(f"Shared devices: {device_stats['is_shared'].sum():,}")
        
        return device_stats
    
    def extract_transaction_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract and clean transaction data
        
        Args:
            df: Merged DataFrame
        
        Returns:
            Transaction DataFrame
        """
        logger.info("Extracting transaction data...")
        
        # Create IDs
        df['transaction_id'] = 'T_' + df['TransactionID'].astype(str)
        df['account_id'] = df['card1'].astype(str) + '_' + df['card2'].fillna('0').astype(str)
        df['merchant_id'] = 'M_' + df['ProductCD'].astype(str)
        
        if 'DeviceInfo' in df.columns:
            df['device_id'] = 'D_' + df['DeviceInfo'].fillna('unknown').astype(str)
        else:
            df['device_id'] = 'D_unknown'
        
        # Select and rename columns
        transaction_cols = {
            'transaction_id': 'transaction_id',
            'account_id': 'account_id',
            'merchant_id': 'merchant_id',
            'device_id': 'device_id',
            'TransactionAmt': 'transaction_amount',
            'ProductCD': 'product_category',
            'isFraud': 'is_fraud',
        }
        
        transactions = df[list(transaction_cols.keys())].copy()
        transactions.rename(columns=transaction_cols, inplace=True)
        
        # Add card information
        if 'card4' in df.columns:
            transactions['card_type'] = df['card4']
        else:
            transactions['card_type'] = None
            
        if 'card6' in df.columns:
            transactions['card_category'] = df['card6']
        else:
            transactions['card_category'] = None
        
        # Add geographic info
        if 'addr1' in df.columns:
            transactions['addr_country'] = df['addr1']
        else:
            transactions['addr_country'] = None
        
        # Add email domain
        if 'P_emaildomain' in df.columns:
            transactions['email_domain'] = df['P_emaildomain']
        else:
            transactions['email_domain'] = None
        
        # Add transaction type
        transactions['transaction_type'] = df['ProductCD'] if 'ProductCD' in df.columns else None
        
        # Add timestamp (convert TransactionDT to datetime)
        if 'TransactionDT' in df.columns:
            # TransactionDT is seconds from a reference date
            reference_date = pd.Timestamp('2017-12-01')
            transactions['transaction_date'] = reference_date + pd.to_timedelta(df['TransactionDT'], unit='s')
            
            # Extract time features
            transactions['transaction_hour'] = transactions['transaction_date'].dt.hour
            transactions['transaction_day_of_week'] = transactions['transaction_date'].dt.dayofweek
            transactions['transaction_day_of_month'] = transactions['transaction_date'].dt.day
        else:
            transactions['transaction_date'] = pd.Timestamp('now')
            transactions['transaction_hour'] = None
            transactions['transaction_day_of_week'] = None
            transactions['transaction_day_of_month'] = None
        
        # Distance and time features (simplified - would need actual calculation)
        transactions['distance_from_last_txn'] = None
        transactions['time_since_last_txn'] = None
        
        logger.info(f"Extracted {len(transactions):,} transactions")
        logger.info(f"Fraud transactions: {transactions['is_fraud'].sum():,} ({transactions['is_fraud'].mean()*100:.2f}%)")
        
        return transactions
    
    def extract_shared_device_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract device sharing patterns
        
        Args:
            df: Merged DataFrame
        
        Returns:
            Shared device DataFrame
        """
        logger.info("Extracting shared device data...")
        
        # Create IDs
        df['account_id'] = df['card1'].astype(str) + '_' + df['card2'].fillna('0').astype(str)
        
        if 'DeviceInfo' in df.columns:
            df['device_id'] = 'D_' + df['DeviceInfo'].fillna('unknown').astype(str)
        else:
            df['device_id'] = 'D_unknown'
        
        # Group by device and account
        shared_device = df.groupby(['device_id', 'account_id']).agg({
            'TransactionID': 'count',
            'isFraud': 'sum',
            'TransactionDT': ['min', 'max']
        }).reset_index()
        
        shared_device.columns = [
            'device_id', 'account_id', 'transaction_count',
            'fraud_count', 'first_seen_dt', 'last_seen_dt'
        ]
        
        # Convert timestamps
        reference_date = pd.Timestamp('2017-12-01')
        shared_device['first_seen'] = reference_date + pd.to_timedelta(shared_device['first_seen_dt'], unit='s')
        shared_device['last_seen'] = reference_date + pd.to_timedelta(shared_device['last_seen_dt'], unit='s')
        
        # Remove temporary columns
        shared_device.drop(['first_seen_dt', 'last_seen_dt'], axis=1, inplace=True)
        
        # Filter only shared devices (multiple accounts)
        device_counts = shared_device.groupby('device_id').size()
        shared_devices_ids = device_counts[device_counts > 1].index
        shared_device = shared_device[shared_device['device_id'].isin(shared_devices_ids)]
        
        logger.info(f"Found {len(shared_device):,} device-account pairs")
        logger.info(f"Unique shared devices: {shared_device['device_id'].nunique():,}")
        
        return shared_device
    
    def save_processed_data(self, dataframes: Dict[str, pd.DataFrame]) -> None:
        """
        Save processed dataframes to CSV files
        
        Args:
            dataframes: Dictionary of {name: dataframe}
        """
        logger.info("Saving processed data to CSV files...")
        
        for name, df in dataframes.items():
            filepath = self.processed_data_path / f'{name}.csv'
            df.to_csv(filepath, index=False)
            logger.info(f"Saved {name}: {len(df):,} rows to {filepath.name}")
    
    def process_dataset(self, sample_size: Optional[int] = None) -> Dict[str, pd.DataFrame]:
        """
        Main processing pipeline
        
        Args:
            sample_size: Optional number of transactions to sample (for testing)
        
        Returns:
            Dictionary of processed dataframes
        """
        logger.info("=" * 70)
        logger.info("Starting data processing pipeline")
        logger.info("=" * 70)
        
        # Load data
        transaction_df, identity_df = self.load_csv_files()
        
        # Sample if requested
        if sample_size:
            logger.info(f"Sampling {sample_size:,} transactions for testing")
            transaction_df = transaction_df.sample(n=min(sample_size, len(transaction_df)), random_state=42)
            if not identity_df.empty:
                identity_df = identity_df[identity_df['TransactionID'].isin(transaction_df['TransactionID'])]
        
        # Merge datasets
        merged_df = self.merge_datasets(transaction_df, identity_df)
        
        # Extract data for each table
        accounts = self.extract_account_data(merged_df)
        merchants = self.extract_merchant_data(merged_df)
        devices = self.extract_device_data(merged_df)
        transactions = self.extract_transaction_data(merged_df)
        shared_devices = self.extract_shared_device_data(merged_df)
        
        processed_data = {
            'accounts': accounts,
            'merchants': merchants,
            'devices': devices,
            'transactions': transactions,
            'shared_devices': shared_devices
        }
        
        # Save to CSV
        self.save_processed_data(processed_data)
        
        logger.info("=" * 70)
        logger.info("Data processing complete!")
        logger.info("=" * 70)
        
        return processed_data


if __name__ == "__main__":
    loader = DataLoader()
    
    # Process with sample for testing (remove sample_size for full dataset)
    processed_data = loader.process_dataset(sample_size=50000)
    
    print("\nProcessed data summary:")
    for name, df in processed_data.items():
        print(f"  {name}: {len(df):,} rows")
