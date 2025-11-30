"""
PostgreSQL Database Connection Module
Handles all database connectivity and configuration
"""

import psycopg2
from psycopg2 import sql, Error
import logging
from typing import Optional
import os
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class DatabaseConfig:
    """Database configuration from environment variables or defaults"""
    
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.database = os.getenv('DB_NAME', 'fraud_detection')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'your_password')
        self.sslmode = os.getenv('DB_SSLMODE', 'prefer')
    
    def get_connection_params(self):
        """Return connection parameters as dictionary"""
        return {
            'host': self.host,
            'port': int(self.port),
            'database': self.database,
            'user': self.user,
            'password': self.password,
            'sslmode': self.sslmode
        }
    
    def __str__(self):
        """String representation (without password)"""
        return f"PostgreSQL @ {self.user}@{self.host}:{self.port}/{self.database}"


class DatabaseConnection:
    """Manages PostgreSQL connection lifecycle"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database connection
        
        Args:
            config: DatabaseConfig object. If None, creates new one from env vars
        """
        self.config = config or DatabaseConfig()
        self.connection = None
        self.cursor = None
    
    def connect(self) -> bool:
        """
        Establish connection to PostgreSQL
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = psycopg2.connect(**self.config.get_connection_params())
            self.cursor = self.connection.cursor()
            logger.info(f"✓ Connected to {self.config}")
            return True
        except Error as e:
            logger.error(f"✗ Connection failed: {e}")
            return False
    
    def disconnect(self) -> bool:
        """
        Close connection to PostgreSQL
        
        Returns:
            True if disconnection successful, False otherwise
        """
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("✓ Disconnected from database")
            return True
        except Error as e:
            logger.error(f"✗ Disconnection failed: {e}")
            return False
    
    def execute(self, query: str, params: tuple = None) -> bool:
        """
        Execute SQL query
        
        Args:
            query: SQL query string
            params: Tuple of parameters for parameterized query
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return True
        except Error as e:
            logger.error(f"✗ Query execution failed: {e}")
            logger.error(f"  Query: {query}")
            return False
    
    def executemany(self, query: str, params_list: list) -> bool:
        """
        Execute multiple SQL queries
        
        Args:
            query: SQL query string
            params_list: List of tuples with parameters
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.executemany(query, params_list)
            return True
        except Error as e:
            logger.error(f"✗ Batch execution failed: {e}")
            logger.error(f"  Query: {query}")
            return False
    
    def fetchall(self):
        """Fetch all results from cursor"""
        try:
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"✗ Fetch failed: {e}")
            return []
    
    def fetchone(self):
        """Fetch one result from cursor"""
        try:
            return self.cursor.fetchone()
        except Error as e:
            logger.error(f"✗ Fetch failed: {e}")
            return None
    
    def commit(self) -> bool:
        """
        Commit transaction
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.connection.commit()
            logger.info("✓ Changes committed to database")
            return True
        except Error as e:
            logger.error(f"✗ Commit failed: {e}")
            return False
    
    def rollback(self) -> bool:
        """
        Rollback transaction
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.connection.rollback()
            logger.warning("⚠ Transaction rolled back")
            return True
        except Error as e:
            logger.error(f"✗ Rollback failed: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to database"""
        return self.connection is not None and not self.connection.closed
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is not None:
            self.rollback()
        self.disconnect()


def get_connection(config: Optional[DatabaseConfig] = None) -> Optional[DatabaseConnection]:
    """
    Factory function to get database connection
    
    Args:
        config: DatabaseConfig object. If None, creates new one from env vars
    
    Returns:
        DatabaseConnection object if successful, None otherwise
    """
    db = DatabaseConnection(config)
    if db.connect():
        return db
    return None


if __name__ == "__main__":
    # Test connection
    print("\n" + "="*60)
    print("Testing PostgreSQL Connection")
    print("="*60 + "\n")
    
    config = DatabaseConfig()
    print(f"Configuration: {config}")
    print(f"Parameters: {config.get_connection_params()}\n")
    
    db = DatabaseConnection(config)
    if db.connect():
        print("✓ Connection successful!")
        
        # Test query
        if db.execute("SELECT version()"):
            version = db.fetchone()
            if version:
                print(f"\nPostgreSQL Version:\n  {version[0]}\n")
        
        db.disconnect()
    else:
        print("✗ Connection failed!")
    
    print("="*60)
