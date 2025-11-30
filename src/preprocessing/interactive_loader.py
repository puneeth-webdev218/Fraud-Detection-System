"""
Interactive Data Loading Module
Allows users to specify the number of transactions to load at runtime
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import logging
import sys
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.config import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InteractiveDataLoader:
    """
    Interactive data loader that allows users to select the number of transactions
    to load at runtime. Supports both synthetic demo data and real CSV files.
    """
    
    def __init__(self):
        self.raw_data_path = config.DATA_RAW_PATH
        self.processed_data_path = config.DATA_PROCESSED_PATH
    
    # ========================================================================
    # SYNTHETIC DATA GENERATION
    # ========================================================================
    
    def generate_synthetic_transactions(self, n_transactions: int = 1000) -> pd.DataFrame:
        """
        Generate synthetic transaction data for demonstration
        
        Args:
            n_transactions: Number of transactions to generate
            
        Returns:
            DataFrame with synthetic transactions
        """
        logger.info(f"Generating {n_transactions:,} synthetic transactions...")
        
        np.random.seed(42)
        
        # Adaptive account/merchant/device counts based on transaction volume
        n_accounts = min(500, max(10, n_transactions // 25))
        n_merchants = min(250, max(10, n_transactions // 50))
        n_devices = min(300, max(10, n_transactions // 33))
        
        # Generate transaction data
        dates = [datetime.now() - timedelta(days=np.random.randint(0, 365)) 
                 for _ in range(n_transactions)]
        
        transactions = pd.DataFrame({
            'transaction_id': range(1, n_transactions + 1),
            'account_id': np.random.randint(1, n_accounts + 1, n_transactions),
            'merchant_id': np.random.randint(1, n_merchants + 1, n_transactions),
            'device_id': np.random.randint(1, n_devices + 1, n_transactions),
            'transaction_amount': np.random.lognormal(3.5, 1.5, n_transactions),
            'transaction_date': dates,
        })
        
        # Fraud labels (5% fraud rate)
        is_fraud = np.random.binomial(1, 0.05, n_transactions).astype(bool)
        
        # Fraudulent transactions tend to be larger
        fraud_indices = np.where(is_fraud)[0]
        for idx in fraud_indices:
            transactions.loc[idx, 'transaction_amount'] *= np.random.uniform(2, 5)
        
        transactions['is_fraud'] = is_fraud
        
        logger.info(f"Generated {n_transactions:,} transactions with {is_fraud.sum()} frauds ({is_fraud.sum()/len(transactions)*100:.2f}%)")
        
        return transactions
    
    # ========================================================================
    # REAL DATA LOADING
    # ========================================================================
    
    def load_csv_with_limit(self, filepath: str, nrows: int = None, **kwargs) -> pd.DataFrame:
        """
        Load CSV file with optional row limit
        
        Args:
            filepath: Path to CSV file
            nrows: Number of rows to load (None = all rows)
            **kwargs: Additional pandas read_csv arguments
            
        Returns:
            DataFrame with limited rows
        """
        logger.info(f"Loading CSV file: {filepath}")
        
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        try:
            df = pd.read_csv(file_path, nrows=nrows, **kwargs)
            logger.info(f"Loaded {len(df):,} rows from {file_path.name}")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV: {str(e)}")
            raise
    
    def load_ieee_cis_data(self, n_transactions: int = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load IEEE-CIS dataset with optional transaction limit
        
        Args:
            n_transactions: Number of transactions to load (None = all)
            
        Returns:
            Tuple of (transactions_df, identity_df)
        """
        logger.info(f"Loading IEEE-CIS dataset (limit: {n_transactions or 'all'} transactions)...")
        
        # Load transaction data
        transaction_file = self.raw_data_path / 'train_transaction.csv'
        
        if not transaction_file.exists():
            logger.error(f"Transaction file not found: {transaction_file}")
            logger.info("Falling back to synthetic data generation...")
            return self.generate_synthetic_transactions(n_transactions or 1000), pd.DataFrame()
        
        try:
            transactions = self.load_csv_with_limit(
                str(transaction_file),
                nrows=n_transactions
            )
            logger.info(f"Loaded {len(transactions):,} transactions")
        except Exception as e:
            logger.warning(f"Failed to load real data: {str(e)}")
            logger.info("Falling back to synthetic data generation...")
            return self.generate_synthetic_transactions(n_transactions or 1000), pd.DataFrame()
        
        # Load identity data (same limit)
        identity_file = self.raw_data_path / 'train_identity.csv'
        
        if not identity_file.exists():
            logger.warning(f"Identity file not found: {identity_file}")
            identity = pd.DataFrame()
        else:
            try:
                identity = self.load_csv_with_limit(
                    str(identity_file),
                    nrows=n_transactions
                )
                logger.info(f"Loaded {len(identity):,} identity records")
            except Exception as e:
                logger.warning(f"Failed to load identity data: {str(e)}")
                identity = pd.DataFrame()
        
        return transactions, identity
    
    # ========================================================================
    # DATA MERGING AND AGGREGATION
    # ========================================================================
    
    def merge_transaction_identity(self, transactions: pd.DataFrame, 
                                  identity: pd.DataFrame) -> pd.DataFrame:
        """
        Merge transaction and identity datasets and standardize column names
        
        Args:
            transactions: Transaction DataFrame
            identity: Identity DataFrame
            
        Returns:
            Merged DataFrame with standardized columns
        """
        logger.info("Merging transaction and identity data...")
        
        # Standardize column names for IEEE-CIS data
        transactions = self._standardize_columns(transactions)
        
        if identity.empty:
            logger.info("Identity data is empty, using transactions only")
            return transactions
        
        # Merge if identity data exists
        try:
            merged = transactions.merge(identity, on='transaction_id', how='left')
            logger.info(f"Merged dataset shape: {merged.shape}")
        except KeyError:
            logger.warning("Could not merge on transaction_id, using transactions only")
            merged = transactions
        
        return merged
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize IEEE-CIS column names to match expected format
        
        Args:
            df: DataFrame with IEEE-CIS columns
            
        Returns:
            DataFrame with standardized column names
        """
        logger.info("Standardizing column names...")
        
        # Column mapping from IEEE-CIS to standardized names
        column_mapping = {
            'TransactionID': 'transaction_id',
            'isFraud': 'is_fraud',
            'TransactionAmt': 'transaction_amount',
            'TransactionDT': 'transaction_date',
            'ProductCD': 'product_code',
            'card1': 'card_1',
            'card2': 'card_2',
            'card3': 'card_3',
            'card4': 'card_4',
            'card5': 'card_5',
            'card6': 'card_6',
            'addr1': 'address_1',
            'addr2': 'address_2',
            'P_emaildomain': 'purchaser_email_domain',
            'R_emaildomain': 'recipient_email_domain',
            'DeviceType': 'device_type',
            'DeviceInfo': 'device_info',
        }
        
        # Rename columns that exist in the dataframe
        rename_dict = {old: new for old, new in column_mapping.items() if old in df.columns}
        df = df.rename(columns=rename_dict)
        
        # Create synthetic columns if missing (for compatibility)
        if 'account_id' not in df.columns:
            # Use card1 as proxy for account identifier
            if 'card_1' in df.columns:
                df['account_id'] = df['card_1']
            else:
                df['account_id'] = range(len(df))
        
        if 'merchant_id' not in df.columns:
            # Create synthetic merchant_id from available data
            if 'product_code' in df.columns:
                df['merchant_id'] = df['product_code'].astype('category').cat.codes + 1
            else:
                df['merchant_id'] = np.random.randint(1, 101, len(df))
        
        if 'device_id' not in df.columns:
            # Use device_info as proxy or create synthetic
            if 'device_info' in df.columns:
                df['device_id'] = df['device_info'].astype('category').cat.codes + 1
            else:
                df['device_id'] = np.random.randint(1, 51, len(df))
        
        # Ensure transaction_date is datetime
        if 'transaction_date' in df.columns:
            if df['transaction_date'].dtype != 'datetime64[ns]':
                try:
                    df['transaction_date'] = pd.to_datetime(df['transaction_date'], unit='s')
                except:
                    df['transaction_date'] = datetime.now()
        else:
            df['transaction_date'] = datetime.now()
        
        logger.info(f"Standardized columns. Final shape: {df.shape}")
        
        return df
    
    def extract_account_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract account-level features from transactions
        
        Args:
            df: Transaction DataFrame
            
        Returns:
            Account features DataFrame
        """
        logger.info("Extracting account features...")
        
        account_stats = df.groupby('account_id').agg({
            'transaction_id': 'count',
            'is_fraud': ['sum', 'mean'],
            'transaction_amount': ['sum', 'mean', 'std', 'min', 'max']
        }).round(4)
        
        account_stats.columns = ['total_transactions', 'fraud_count', 'fraud_rate',
                                'total_amount', 'avg_amount', 'std_amount', 
                                'min_amount', 'max_amount']
        
        # Calculate risk score
        account_stats['risk_score'] = (
            account_stats['fraud_rate'] * 0.5 +
            (account_stats['avg_amount'] / account_stats['avg_amount'].max()) * 0.3 +
            (account_stats['fraud_count'] / account_stats['fraud_count'].max()) * 0.2
        )
        
        logger.info(f"Extracted features for {len(account_stats):,} accounts")
        
        return account_stats.reset_index()
    
    def extract_merchant_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract merchant-level features from transactions
        
        Args:
            df: Transaction DataFrame
            
        Returns:
            Merchant features DataFrame
        """
        logger.info("Extracting merchant features...")
        
        merchant_stats = df.groupby('merchant_id').agg({
            'transaction_id': 'count',
            'is_fraud': ['sum', 'mean'],
            'transaction_amount': ['sum', 'mean']
        }).round(4)
        
        merchant_stats.columns = ['total_transactions', 'fraud_count', 'fraud_rate',
                                 'total_amount', 'avg_amount']
        
        logger.info(f"Extracted features for {len(merchant_stats):,} merchants")
        
        return merchant_stats.reset_index()
    
    def extract_device_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract device-level features from transactions
        
        Args:
            df: Transaction DataFrame
            
        Returns:
            Device features DataFrame
        """
        logger.info("Extracting device features...")
        
        device_stats = df.groupby('device_id').agg({
            'account_id': 'nunique',
            'transaction_id': 'count',
            'is_fraud': ['sum', 'mean'],
            'transaction_amount': 'mean'
        }).round(4)
        
        device_stats.columns = ['unique_accounts', 'total_transactions', 
                               'fraud_count', 'fraud_rate', 'avg_amount']
        
        # Mark suspicious devices (used by multiple accounts)
        device_stats['is_suspicious'] = device_stats['unique_accounts'] > 3
        
        logger.info(f"Extracted features for {len(device_stats):,} devices")
        logger.info(f"Suspicious devices: {device_stats['is_suspicious'].sum()}")
        
        return device_stats.reset_index()
    
    # ========================================================================
    # PIPELINE EXECUTION
    # ========================================================================
    
    def load_and_process_data(self, n_transactions: int = 1000, 
                             use_synthetic: bool = True) -> dict:
        """
        Complete data loading and processing pipeline
        
        Args:
            n_transactions: Number of transactions to load/generate
            use_synthetic: Whether to use synthetic data (True) or real data (False)
            
        Returns:
            Dictionary with processed data:
            {
                'transactions': DataFrame,
                'accounts': DataFrame,
                'merchants': DataFrame,
                'devices': DataFrame,
                'stats': dict
            }
        """
        logger.info(f"Starting data pipeline: {n_transactions:,} transactions, synthetic={use_synthetic}")
        
        # Load data
        if use_synthetic:
            transactions = self.generate_synthetic_transactions(n_transactions)
        else:
            transactions, identity = self.load_ieee_cis_data(n_transactions)
            if not identity.empty:
                transactions = self.merge_transaction_identity(transactions, identity)
        
        # Extract features
        accounts = self.extract_account_features(transactions)
        merchants = self.extract_merchant_features(transactions)
        devices = self.extract_device_features(transactions)
        
        # Calculate statistics
        stats = {
            'total_transactions': len(transactions),
            'total_fraud': transactions['is_fraud'].sum(),
            'fraud_rate': (transactions['is_fraud'].sum() / len(transactions)) * 100,
            'unique_accounts': transactions['account_id'].nunique(),
            'unique_merchants': transactions['merchant_id'].nunique(),
            'unique_devices': transactions['device_id'].nunique(),
            'total_amount': transactions['transaction_amount'].sum(),
            'avg_amount': transactions['transaction_amount'].mean(),
            'loaded_at': datetime.now()
        }
        
        logger.info(f"Pipeline complete: {stats}")
        
        return {
            'transactions': transactions,
            'accounts': accounts,
            'merchants': merchants,
            'devices': devices,
            'stats': stats
        }
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_data_summary(self, df: pd.DataFrame) -> dict:
        """
        Get summary statistics for a dataset
        
        Args:
            df: Transaction DataFrame
            
        Returns:
            Dictionary with summary stats
        """
        return {
            'total_rows': len(df),
            'total_fraud': df['is_fraud'].sum() if 'is_fraud' in df.columns else 0,
            'fraud_rate': (df['is_fraud'].sum() / len(df) * 100) if 'is_fraud' in df.columns else 0,
            'accounts': df['account_id'].nunique() if 'account_id' in df.columns else 0,
            'merchants': df['merchant_id'].nunique() if 'merchant_id' in df.columns else 0,
            'devices': df['device_id'].nunique() if 'device_id' in df.columns else 0,
            'amount_total': df['transaction_amount'].sum() if 'transaction_amount' in df.columns else 0,
            'amount_mean': df['transaction_amount'].mean() if 'transaction_amount' in df.columns else 0,
            'columns': list(df.columns)
        }


# Convenience functions for direct use
def load_data_interactive(n_transactions: int = 1000, use_synthetic: bool = True) -> dict:
    """
    Convenience function to load and process data
    
    Args:
        n_transactions: Number of transactions to load
        use_synthetic: Use synthetic data
        
    Returns:
        Dictionary with processed data
    """
    loader = InteractiveDataLoader()
    return loader.load_and_process_data(n_transactions, use_synthetic)


def generate_demo_transactions(n_transactions: int = 1000) -> pd.DataFrame:
    """
    Convenience function to generate synthetic transactions
    
    Args:
        n_transactions: Number of transactions to generate
        
    Returns:
        DataFrame with synthetic transactions
    """
    loader = InteractiveDataLoader()
    return loader.generate_synthetic_transactions(n_transactions)
