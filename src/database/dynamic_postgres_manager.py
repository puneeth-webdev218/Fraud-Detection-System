"""
Dynamic PostgreSQL Manager for Fraud Detection System
Handles connection, table creation, and batch insertion of transactions
"""

import psycopg2
from psycopg2.extras import execute_values
from psycopg2 import Error as PostgresError
import pandas as pd
import logging
from typing import Dict, Tuple, Optional
from pathlib import Path
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class PostgreSQLManager:
    """
    Manages PostgreSQL connections, table creation, and data insertion
    for dynamic fraud detection transaction loading
    """
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None
    ):
        """
        Initialize PostgreSQL Manager
        
        Args:
            host: Database host (default from .env DB_HOST)
            port: Database port (default from .env DB_PORT)
            database: Database name (default from .env DB_NAME)
            user: Database user (default from .env DB_USER)
            password: Database password (default from .env DB_PASSWORD)
        """
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.port = port or int(os.getenv('DB_PORT', 5432))
        self.database = database or os.getenv('DB_NAME', 'fraud_detection')
        self.user = user or os.getenv('DB_USER', 'postgres')
        self.password = password or os.getenv('DB_PASSWORD', '')
        
        self.connection = None
        self.cursor = None
    
    def connect(self) -> bool:
        """
        Establish connection to PostgreSQL database
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.connection.cursor()
            logger.info(f"✓ Connected to PostgreSQL @ {self.host}:{self.port}/{self.database}")
            return True
        except PostgresError as e:
            logger.error(f"✗ Connection failed: {e}")
            return False
    
    def disconnect(self) -> bool:
        """
        Close database connection
        
        Returns:
            True if disconnected successfully
        """
        try:
            # Close cursor first to flush any pending operations
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            # Then close connection
            if self.connection:
                self.connection.close()
                self.connection = None
            logger.info("✓ Disconnected from database")
            return True
        except PostgresError as e:
            logger.error(f"✗ Disconnect failed: {e}")
            return False
    
    def reset_transactions_table(self) -> bool:
        """
        Clear all data from transactions table (TRUNCATE CASCADE)
        Keeps table structure intact, removes only data
        Cascades to dependent tables (fraud_predictions, etc.)
        
        Returns:
            True if reset successful, False otherwise
        """
        try:
            if not self.connection:
                logger.error("✗ No database connection")
                return False
            
            # Use CASCADE to handle foreign key constraints
            self.cursor.execute("TRUNCATE TABLE transactions CASCADE;")
            self.connection.commit()
            logger.info("✓ Database reset")
            return True
        
        except PostgresError as e:
            logger.error(f"✗ Reset failed: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def create_transactions_table(self) -> bool:
        """
        Create transactions table if it doesn't exist
        WITHOUT status column initially (for two-phase processing)
        
        Returns:
            True if table created or already exists
        """
        try:
            if not self.connection:
                logger.error("✗ No database connection")
                return False
            
            # Create table WITHOUT status column initially (Phase 1: raw data)
            create_table_query = """
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id BIGINT PRIMARY KEY,
                account_id INTEGER,
                merchant_id INTEGER,
                device_id INTEGER,
                amount DECIMAL(10,2),
                timestamp TIMESTAMP,
                fraud_flag BOOLEAN,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            self.cursor.execute(create_table_query)
            self.connection.commit()
            logger.info("✓ Transactions table ready (Phase 1: raw data)")
            
            # Create indexes for performance
            self._create_indexes()
            
            return True
        
        except PostgresError as e:
            logger.error(f"✗ Table creation failed: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def _add_status_column_if_needed(self) -> None:
        """Add status column to existing transactions table if it doesn't exist"""
        try:
            # Check if status column exists
            self.cursor.execute(
                """SELECT column_name FROM information_schema.columns 
                   WHERE table_name = 'transactions' AND column_name = 'status';"""
            )
            if not self.cursor.fetchone():
                # Column doesn't exist, add it
                self.cursor.execute(
                    "ALTER TABLE transactions ADD COLUMN status VARCHAR(20);"
                )
                self.connection.commit()
                logger.info("✓ Added status column to transactions table")
        except PostgresError as e:
            # Column may already exist or table doesn't exist yet
            logger.debug(f"Status column migration info: {e}")
    
    def _create_indexes(self) -> None:
        """Create performance indexes on transactions table"""
        try:
            indexes = [
                ("idx_transactions_fraud", "fraud_flag"),
                ("idx_transactions_account", "account_id"),
                ("idx_transactions_timestamp", "timestamp"),
                ("idx_transactions_amount", "amount"),
                ("idx_transactions_status", "status")
            ]
            
            for idx_name, column in indexes:
                try:
                    self.cursor.execute(
                        f"CREATE INDEX IF NOT EXISTS {idx_name} ON transactions({column});"
                    )
                except PostgresError:
                    pass  # Index may already exist
            
            self.connection.commit()
            logger.info("✓ Indexes created")
        except PostgresError as e:
            logger.warning(f"⚠ Index creation warning: {e}")
    
    def insert_transactions_batch(
        self,
        df: pd.DataFrame,
        column_mapping: Dict[str, str] = None
    ) -> Tuple[int, int]:
        """
        Bulk insert transactions into database
        
        Args:
            df: DataFrame with transaction data
            column_mapping: Optional mapping of DataFrame columns to table columns
                          e.g., {'trans_id': 'transaction_id', 'amt': 'amount'}
        
        Returns:
            Tuple of (inserted_count, skipped_count)
        """
        try:
            if not self.connection or df is None or df.empty:
                logger.error("✗ Invalid connection or empty DataFrame")
                return 0, 0
            
            # Apply column mapping if provided
            if column_mapping:
                df = df.rename(columns=column_mapping)
            
            # Required columns
            required_cols = [
                'transaction_id', 'account_id', 'merchant_id', 'device_id',
                'amount', 'timestamp', 'fraud_flag'
            ]
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.error(f"✗ Missing columns: {missing_cols}")
                return 0, 0
            
            # Select and prepare data
            insert_df = df[required_cols].copy()
            
            # Convert fraud_flag to integer (0 or 1) if it's boolean
            if insert_df['fraud_flag'].dtype == 'bool':
                insert_df['fraud_flag'] = insert_df['fraud_flag'].astype(int)
            elif insert_df['fraud_flag'].dtype == 'object':
                # Handle string 'True'/'False'
                insert_df['fraud_flag'] = insert_df['fraud_flag'].map({
                    'True': 1, 'False': 0, True: 1, False: 0,
                    'true': 1, 'false': 0, 1: 1, 0: 0
                }).astype(int)
            else:
                insert_df['fraud_flag'] = insert_df['fraud_flag'].astype(int)
            
            # Phase 1: Insert raw data WITHOUT status column
            # Status will be added in Phase 2 after GNN processing
            records = [tuple(row) for row in insert_df.values]
            
            # SQL insert with ON CONFLICT handling (NO status - Phase 1: raw data only)
            insert_query = """
            INSERT INTO transactions 
            (transaction_id, account_id, merchant_id, device_id, amount, timestamp, fraud_flag)
            VALUES %s
            ON CONFLICT (transaction_id) DO NOTHING;
            """
            
            # Batch insert in chunks of 1000
            batch_size = 1000
            total_inserted = 0
            
            # Convert integer fraud_flag to boolean and execute batches without individual commits
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                # Convert fraud_flag (position 6) from int to boolean
                batch_with_bool = [
                    (row[0], row[1], row[2], row[3], row[4], row[5], bool(row[6]), row[7])
                    for row in batch
                ]
                try:
                    execute_values(self.cursor, insert_query, batch_with_bool)
                    total_inserted += len(batch_with_bool)
                except PostgresError as e:
                    self.connection.rollback()
                    logger.error(f"✗ Batch insert failed: {e}")
                    return 0, len(records)
            
            # Single final commit after ALL inserts complete
            self.connection.commit()
            logger.info(f"✓ All {total_inserted} transactions committed to database")
            
            skipped = len(records) - total_inserted
            logger.info(f"✓ Insertion complete: {total_inserted} inserted, {skipped} skipped")
            
            return total_inserted, skipped
        
        except Exception as e:
            logger.error(f"✗ Batch insertion failed: {e}")
            if self.connection:
                self.connection.rollback()
            return 0, len(df) if df is not None else 0
    
    def get_transaction_count(self) -> int:
        """
        Get total number of transactions in database
        
        Returns:
            Count of transactions
        """
        try:
            self.cursor.execute("SELECT COUNT(*) FROM transactions;")
            count = self.cursor.fetchone()[0]
            return count
        except PostgresError as e:
            logger.warning(f"⚠ Count query failed: {e}")
            return 0
    
    def get_fraud_stats(self) -> Dict:
        """
        Get fraud statistics from transactions table
        
        Returns:
            Dictionary with fraud statistics
        """
        try:
            query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN fraud_flag::integer = 1 THEN 1 ELSE 0 END) as fraud_count,
                ROUND(SUM(CASE WHEN fraud_flag::integer = 1 THEN 1 ELSE 0 END)::numeric / 
                      COUNT(*) * 100, 2) as fraud_rate,
                AVG(amount) as avg_amount,
                MIN(amount) as min_amount,
                MAX(amount) as max_amount
            FROM transactions;
            """
            
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            
            return {
                'total': result[0] or 0,
                'fraud_count': result[1] or 0,
                'fraud_rate': float(result[2]) if result[2] else 0.0,
                'avg_amount': float(result[3]) if result[3] else 0.0,
                'min_amount': float(result[4]) if result[4] else 0.0,
                'max_amount': float(result[5]) if result[5] else 0.0,
            }
        except PostgresError as e:
            logger.warning(f"⚠ Stats query failed: {e}")
            return {
                'total': 0, 'fraud_count': 0, 'fraud_rate': 0.0,
                'avg_amount': 0.0, 'min_amount': 0.0, 'max_amount': 0.0
            }
    
    def get_transactions_with_status(self, limit: int = 1000) -> pd.DataFrame:
        """
        Get transactions from database with status column
        Returns gracefully if status column doesn't exist yet (Phase 1)
        
        Args:
            limit: Maximum number of rows to fetch
        
        Returns:
            DataFrame with transaction data including status from database (if available)
        """
        try:
            # Try to query with status column first (Phase 2)
            query_with_status = f"""
            SELECT transaction_id, account_id, merchant_id, device_id, 
                   amount, timestamp, fraud_flag, status
            FROM transactions
            ORDER BY transaction_id DESC
            LIMIT {limit};
            """
            
            try:
                df = pd.read_sql_query(query_with_status, self.connection)
                logger.info(f"✓ Retrieved {len(df)} transactions from database (with status)")
                return df
            except:
                # If status column doesn't exist, return Phase 1 data (no status)
                logger.info("ℹ Status column not yet available (Phase 1 data)")
                return self.get_transactions_phase1(limit)
                
        except PostgresError as e:
            logger.warning(f"⚠ Query failed: {e}")
            return pd.DataFrame()
    
    def get_transaction_by_search(self, search_type: str, search_value: int) -> pd.DataFrame:
        """
        Get transactions by search criteria (account, merchant, or device) with status from DB
        Returns gracefully if status column doesn't exist yet (Phase 1)
        
        Args:
            search_type: 'account_id', 'merchant_id', or 'device_id'
            search_value: The ID value to search for
        
        Returns:
            DataFrame with matching transactions (including status if available)
        """
        try:
            if search_type not in ['account_id', 'merchant_id', 'device_id']:
                logger.error(f"✗ Invalid search type: {search_type}")
                return pd.DataFrame()
            
            # Try with status first
            query_with_status = f"""
            SELECT transaction_id, account_id, merchant_id, device_id, 
                   amount, timestamp, fraud_flag, status
            FROM transactions
            WHERE {search_type} = %s
            ORDER BY timestamp DESC;
            """
            
            try:
                df = pd.read_sql_query(query_with_status, self.connection, params=(search_value,))
                logger.info(f"✓ Retrieved {len(df)} transactions for {search_type}={search_value}")
                return df
            except:
                # If status doesn't exist (Phase 1), query without status
                query_no_status = f"""
                SELECT transaction_id, account_id, merchant_id, device_id, 
                       amount, timestamp, fraud_flag
                FROM transactions
                WHERE {search_type} = %s
                ORDER BY timestamp DESC;
                """
                df = pd.read_sql_query(query_no_status, self.connection, params=(search_value,))
                logger.info(f"✓ Retrieved {len(df)} Phase 1 transactions for {search_type}={search_value}")
                return df
                
        except PostgresError as e:
            logger.warning(f"⚠ Search query failed: {e}")
            return pd.DataFrame()
    
    def add_status_column_and_update(self) -> bool:
        """
        PHASE 2: Add status column to transactions table and populate with GNN results
        This is called AFTER GNN processing to mark transactions based on fraud_flag
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.connection or not self.cursor:
                logger.error("✗ Database not connected")
                return False
            
            # Step 1: Add status column if it doesn't exist
            alter_query = """
            ALTER TABLE transactions
            ADD COLUMN IF NOT EXISTS status VARCHAR(20);
            """
            self.cursor.execute(alter_query)
            logger.info("✓ Status column added/verified")
            
            # Step 2: Update all transactions with status based on fraud_flag
            # 1 -> 'FRAUD', 0 -> 'OK'
            update_query = """
            UPDATE transactions
            SET status = CASE 
                WHEN fraud_flag::integer = 1 THEN 'FRAUD'
                ELSE 'OK'
            END
            WHERE status IS NULL;
            """
            self.cursor.execute(update_query)
            rows_updated = self.cursor.rowcount
            
            # Step 3: Commit the changes
            self.connection.commit()
            logger.info(f"✓ Phase 2 Complete: {rows_updated} transactions updated with status")
            
            return True
            
        except PostgresError as e:
            logger.error(f"✗ Phase 2 failed: {e}")
            if self.connection:
                self.connection.rollback()
            return False
        except Exception as e:
            logger.error(f"✗ Unexpected error in Phase 2: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_transactions_phase1(self, limit: int = 1000) -> pd.DataFrame:
        """
        Get transactions as they exist in Phase 1 (without status column)
        For visualization: shows raw data before GNN processing
        
        Args:
            limit: Maximum number of rows to fetch
        
        Returns:
            DataFrame with transaction data (without status)
        """
        try:
            query = f"""
            SELECT transaction_id, account_id, merchant_id, device_id, 
                   amount, timestamp, fraud_flag
            FROM transactions
            ORDER BY transaction_id DESC
            LIMIT {limit};
            """
            
            df = pd.read_sql_query(query, self.connection)
            logger.info(f"✓ Retrieved {len(df)} Phase 1 transactions (raw data)")
            return df
        except PostgresError as e:
            logger.warning(f"⚠ Phase 1 query failed: {e}")
            return pd.DataFrame()


# Convenience functions
def connect_to_postgresql(
    host: str = None,
    port: int = None,
    database: str = None,
    user: str = None,
    password: str = None
) -> Optional[PostgreSQLManager]:
    """
    Create and connect PostgreSQL manager
    
    Args:
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password
    
    Returns:
        Connected PostgreSQLManager instance or None if connection failed
    """
    manager = PostgreSQLManager(host, port, database, user, password)
    if manager.connect():
        return manager
    return None


def create_transactions_table_if_not_exists(manager: PostgreSQLManager) -> bool:
    """
    Create transactions table if not exists
    
    Args:
        manager: PostgreSQLManager instance
    
    Returns:
        True if successful
    """
    if not manager:
        logger.error("✗ Invalid manager")
        return False
    
    return manager.create_transactions_table()


def insert_processed_dataframe(
    manager: PostgreSQLManager,
    df: pd.DataFrame,
    column_mapping: Dict[str, str] = None
) -> Tuple[int, int]:
    """
    Insert processed DataFrame into transactions table
    
    Args:
        manager: PostgreSQLManager instance
        df: DataFrame with transaction data
        column_mapping: Optional column mapping
    
    Returns:
        Tuple of (inserted_count, skipped_count)
    """
    if not manager:
        logger.error("✗ Invalid manager")
        return 0, 0
    
    return manager.insert_transactions_batch(df, column_mapping)


def reset_database(manager: PostgreSQLManager) -> bool:
    """
    Reset database - clear all transaction data
    
    Args:
        manager: PostgreSQLManager instance
    
    Returns:
        True if reset successful
    """
    if not manager:
        logger.error("✗ Invalid manager")
        return False
    
    return manager.reset_transactions_table()

