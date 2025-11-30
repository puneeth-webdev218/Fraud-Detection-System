"""
PostgreSQL Table Management Module
Creates and manages database tables
"""

import logging
from typing import Optional
from src.database.db_connection import DatabaseConnection, DatabaseConfig

logger = logging.getLogger(__name__)

# SQL schema definitions
TRANSACTIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    account_id VARCHAR(50),
    merchant_id VARCHAR(50),
    device_id VARCHAR(50),
    amount FLOAT,
    timestamp VARCHAR(50),
    fraud_flag INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Create index for faster queries
TRANSACTIONS_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_transactions_fraud_flag 
ON transactions(fraud_flag);

CREATE INDEX IF NOT EXISTS idx_transactions_account_id 
ON transactions(account_id);

CREATE INDEX IF NOT EXISTS idx_transactions_merchant_id 
ON transactions(merchant_id);

CREATE INDEX IF NOT EXISTS idx_transactions_device_id 
ON transactions(device_id);
"""

FRAUD_PREDICTIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS fraud_predictions (
    prediction_id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) UNIQUE,
    fraud_probability FLOAT,
    fraud_flag INTEGER,
    gnn_risk_score FLOAT,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
);
"""

# Create index for fraud_predictions
FRAUD_PREDICTIONS_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_fraud_predictions_fraud_flag 
ON fraud_predictions(fraud_flag);

CREATE INDEX IF NOT EXISTS idx_fraud_predictions_fraud_probability 
ON fraud_predictions(fraud_probability);

CREATE INDEX IF NOT EXISTS idx_fraud_predictions_created_at 
ON fraud_predictions(created_at);
"""


class TableManager:
    """Manages database table creation and schema"""
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize table manager
        
        Args:
            db_connection: DatabaseConnection object
        """
        self.db = db_connection
    
    def create_transactions_table(self) -> bool:
        """
        Create transactions table if it doesn't exist
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Creating transactions table...")
            
            if not self.db.execute(TRANSACTIONS_TABLE_SQL):
                logger.error("Failed to create transactions table")
                return False
            
            self.db.commit()
            logger.info("✓ Transactions table created/verified")
            
            # Create indexes
            if self._create_indexes("transactions"):
                logger.info("✓ Transactions indexes created")
            
            return True
        except Exception as e:
            logger.error(f"✗ Error creating transactions table: {e}")
            self.db.rollback()
            return False
    
    def create_fraud_predictions_table(self) -> bool:
        """
        Create fraud_predictions table if it doesn't exist
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Creating fraud_predictions table...")
            
            if not self.db.execute(FRAUD_PREDICTIONS_TABLE_SQL):
                logger.error("Failed to create fraud_predictions table")
                return False
            
            self.db.commit()
            logger.info("✓ Fraud predictions table created/verified")
            
            # Create indexes
            if self._create_indexes("fraud_predictions"):
                logger.info("✓ Fraud predictions indexes created")
            
            return True
        except Exception as e:
            logger.error(f"✗ Error creating fraud_predictions table: {e}")
            self.db.rollback()
            return False
    
    def _create_indexes(self, table_name: str) -> bool:
        """
        Create indexes for a table
        
        Args:
            table_name: Name of the table
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if table_name == "transactions":
                index_sql = TRANSACTIONS_INDEX_SQL
            elif table_name == "fraud_predictions":
                index_sql = FRAUD_PREDICTIONS_INDEX_SQL
            else:
                return False
            
            # Execute each index creation separately
            for statement in index_sql.strip().split(';'):
                if statement.strip():
                    if not self.db.execute(statement):
                        logger.warning(f"Index creation warning for {table_name}")
            
            self.db.commit()
            return True
        except Exception as e:
            logger.warning(f"⚠ Index creation failed: {e}")
            return False
    
    def create_all_tables(self) -> bool:
        """
        Create all required tables
        
        Returns:
            True if all tables created successfully, False otherwise
        """
        logger.info("\n" + "="*60)
        logger.info("Creating Database Tables")
        logger.info("="*60)
        
        success = True
        
        if not self.create_transactions_table():
            success = False
        
        if not self.create_fraud_predictions_table():
            success = False
        
        if success:
            logger.info("\n✓ All tables created successfully\n")
        else:
            logger.error("\n✗ Some tables failed to create\n")
        
        return success
    
    def get_table_info(self, table_name: str) -> dict:
        """
        Get information about a table
        
        Args:
            table_name: Name of the table
        
        Returns:
            Dictionary with table info
        """
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position;
        """
        
        if not self.db.execute(query, (table_name,)):
            return {}
        
        columns = self.db.fetchall()
        return {
            'table': table_name,
            'columns': [
                {
                    'name': col[0],
                    'type': col[1],
                    'nullable': col[2]
                }
                for col in columns
            ]
        }
    
    def get_row_count(self, table_name: str) -> int:
        """
        Get row count for a table
        
        Args:
            table_name: Name of the table
        
        Returns:
            Number of rows in table
        """
        query = f"SELECT COUNT(*) FROM {table_name};"
        
        if not self.db.execute(query):
            return 0
        
        result = self.db.fetchone()
        return result[0] if result else 0
    
    def truncate_table(self, table_name: str) -> bool:
        """
        Truncate (clear) a table
        
        Args:
            table_name: Name of the table
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.warning(f"Truncating table: {table_name}")
            query = f"TRUNCATE TABLE {table_name};"
            
            if not self.db.execute(query):
                return False
            
            self.db.commit()
            logger.info(f"✓ Table {table_name} truncated")
            return True
        except Exception as e:
            logger.error(f"✗ Truncate failed: {e}")
            return False


def setup_database(config: Optional[DatabaseConfig] = None) -> Optional[TableManager]:
    """
    Setup database connection and create all tables
    
    Args:
        config: DatabaseConfig object. If None, creates from env vars
    
    Returns:
        TableManager object if successful, None otherwise
    """
    # Create connection
    db = DatabaseConnection(config)
    if not db.connect():
        logger.error("Failed to connect to database")
        return None
    
    # Create tables
    manager = TableManager(db)
    if not manager.create_all_tables():
        logger.error("Failed to create tables")
        db.disconnect()
        return None
    
    return manager


if __name__ == "__main__":
    # Test table creation
    print("\n" + "="*60)
    print("Testing Table Creation")
    print("="*60 + "\n")
    
    config = DatabaseConfig()
    manager = setup_database(config)
    
    if manager:
        print("\n✓ Database setup successful!")
        
        # Show table info
        transactions_info = manager.get_table_info("transactions")
        print(f"\nTransactions Table Structure:")
        for col in transactions_info.get('columns', []):
            print(f"  - {col['name']}: {col['type']}")
        
        # Show row counts
        txn_count = manager.get_row_count("transactions")
        print(f"\nTransactions in database: {txn_count}")
        
        manager.db.disconnect()
    else:
        print("✗ Database setup failed!")
    
    print("\n" + "="*60)
