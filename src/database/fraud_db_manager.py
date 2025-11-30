"""
Unified PostgreSQL Database Manager
Combines connection, table management, and data insertion
"""

import logging
import pandas as pd
from typing import Optional, Tuple
from src.database.db_connection import DatabaseConnection, DatabaseConfig
from src.database.table_manager import TableManager
from src.database.data_inserter import DataInserter

logger = logging.getLogger(__name__)


class FraudDetectionDatabaseManager:
    """
    Main database manager for fraud detection pipeline
    Handles all PostgreSQL operations
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database manager
        
        Args:
            config: DatabaseConfig object. If None, creates from env vars
        """
        self.config = config or DatabaseConfig()
        self.connection = None
        self.table_manager = None
        self.data_inserter = None
        self.is_ready = False
    
    def setup(self) -> bool:
        """
        Setup database connection and create tables
        
        Returns:
            True if setup successful, False otherwise
        """
        logger.info("\n" + "="*60)
        logger.info("Setting Up Fraud Detection Database")
        logger.info("="*60 + "\n")
        
        try:
            # Step 1: Connect to database
            logger.info(f"Step 1: Connecting to {self.config}")
            self.connection = DatabaseConnection(self.config)
            
            if not self.connection.connect():
                logger.error("✗ Failed to connect to database")
                return False
            
            logger.info("✓ Connected to database")
            
            # Step 2: Create table manager and tables
            logger.info("\nStep 2: Creating tables...")
            self.table_manager = TableManager(self.connection)
            
            if not self.table_manager.create_all_tables():
                logger.error("✗ Failed to create tables")
                self.connection.disconnect()
                return False
            
            # Step 3: Create data inserter
            logger.info("\nStep 3: Initializing data inserter...")
            self.data_inserter = DataInserter(self.connection)
            logger.info("✓ Data inserter initialized")
            
            self.is_ready = True
            logger.info("\n" + "="*60)
            logger.info("✓ Database Setup Complete!")
            logger.info("="*60 + "\n")
            
            return True
        
        except Exception as e:
            logger.error(f"✗ Setup failed: {e}")
            return False
    
    def insert_results(self, df: pd.DataFrame, column_mapping: Optional[dict] = None) -> bool:
        """
        Insert fraud detection results into database
        
        Args:
            df: DataFrame with results
            column_mapping: Column mapping (optional)
        
        Returns:
            True if insertion successful, False otherwise
        """
        if not self.is_ready:
            logger.error("Database not ready. Call setup() first.")
            return False
        
        if df.empty:
            logger.warning("DataFrame is empty. Nothing to insert.")
            return False
        
        logger.info(f"\n{'='*60}")
        logger.info("Inserting Fraud Detection Results")
        logger.info(f"{'='*60}\n")
        
        try:
            # Insert transactions
            inserted, skipped = self.data_inserter.insert_transactions_batch(df, column_mapping)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✓ Data Insertion Complete!")
            logger.info(f"{'='*60}")
            logger.info(f"  Inserted: {inserted}")
            logger.info(f"  Skipped:  {skipped}")
            logger.info(f"  Total:    {inserted + skipped}\n")
            
            return True
        
        except Exception as e:
            logger.error(f"✗ Insertion failed: {e}")
            return False
    
    def insert_predictions(self, df: pd.DataFrame, column_mapping: Optional[dict] = None) -> bool:
        """
        Insert fraud predictions into database
        
        Args:
            df: DataFrame with predictions
            column_mapping: Column mapping (optional)
        
        Returns:
            True if insertion successful, False otherwise
        """
        if not self.is_ready:
            logger.error("Database not ready. Call setup() first.")
            return False
        
        if df.empty:
            logger.warning("DataFrame is empty. Nothing to insert.")
            return False
        
        logger.info(f"\n{'='*60}")
        logger.info("Inserting Fraud Predictions")
        logger.info(f"{'='*60}\n")
        
        try:
            inserted, skipped = self.data_inserter.insert_fraud_predictions_batch(df, column_mapping)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✓ Prediction Insertion Complete!")
            logger.info(f"{'='*60}")
            logger.info(f"  Inserted: {inserted}")
            logger.info(f"  Skipped:  {skipped}")
            logger.info(f"  Total:    {inserted + skipped}\n")
            
            return True
        
        except Exception as e:
            logger.error(f"✗ Prediction insertion failed: {e}")
            return False
    
    def get_summary(self) -> dict:
        """
        Get database summary
        
        Returns:
            Dictionary with database statistics
        """
        if not self.is_ready:
            logger.warning("Database not ready")
            return {}
        
        return self.data_inserter.get_insertion_summary()
    
    def print_summary(self):
        """Print database summary to console"""
        summary = self.get_summary()
        
        if not summary:
            logger.warning("No summary available")
            return
        
        logger.info("\n" + "="*60)
        logger.info("Database Summary")
        logger.info("="*60)
        
        for key, value in summary.items():
            # Format key name
            formatted_key = key.replace('_', ' ').title()
            logger.info(f"  {formatted_key}: {value:,}")
        
        logger.info("="*60 + "\n")
    
    def get_table_info(self, table_name: str) -> dict:
        """
        Get information about a table
        
        Args:
            table_name: Name of the table
        
        Returns:
            Dictionary with table information
        """
        if not self.is_ready:
            logger.warning("Database not ready")
            return {}
        
        return self.table_manager.get_table_info(table_name)
    
    def get_row_count(self, table_name: str) -> int:
        """
        Get row count for a table
        
        Args:
            table_name: Name of the table
        
        Returns:
            Number of rows in table
        """
        if not self.is_ready:
            logger.warning("Database not ready")
            return 0
        
        return self.table_manager.get_row_count(table_name)
    
    def disconnect(self):
        """Disconnect from database"""
        if self.connection:
            self.connection.disconnect()
            self.is_ready = False
    
    def __enter__(self):
        """Context manager entry"""
        self.setup()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Helper function for easy setup
def setup_fraud_db(config: Optional[DatabaseConfig] = None) -> Optional[FraudDetectionDatabaseManager]:
    """
    Setup fraud detection database
    
    Args:
        config: DatabaseConfig object. If None, creates from env vars
    
    Returns:
        FraudDetectionDatabaseManager object if successful, None otherwise
    """
    db_manager = FraudDetectionDatabaseManager(config)
    if db_manager.setup():
        return db_manager
    return None


if __name__ == "__main__":
    # Test setup
    print("\n" + "="*70)
    print("  Fraud Detection Database Manager - Test")
    print("="*70)
    
    # Setup with context manager
    with FraudDetectionDatabaseManager() as db:
        if db.is_ready:
            print("\n✓ Database is ready!")
            
            # Show summary
            db.print_summary()
            
            # Show table info
            print("Transactions Table Structure:")
            info = db.get_table_info("transactions")
            for col in info.get('columns', []):
                print(f"  - {col['name']}: {col['type']}")
        else:
            print("\n✗ Database setup failed!")
    
    print("="*70)
