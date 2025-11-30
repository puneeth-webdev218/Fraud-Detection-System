"""
PostgreSQL Database Connection Module
Handles all database operations for fraud detection system
"""

import psycopg2
from psycopg2 import sql, Error
import logging
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database Configuration from environment or defaults
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'fraud_detection'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'your_password')
}


class DatabaseConnection:
    """Manage PostgreSQL database connections and operations"""
    
    def __init__(self, config=None):
        """
        Initialize with custom or default config
        
        Args:
            config (dict): Database configuration dictionary
        """
        self.config = config or DB_CONFIG
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Establish connection to PostgreSQL"""
        try:
            self.connection = psycopg2.connect(**self.config)
            self.cursor = self.connection.cursor()
            logger.info("✔ PostgreSQL connected successfully")
            return True
        except Error as e:
            logger.error(f"✗ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("✔ Disconnected from PostgreSQL")
    
    def execute_query(self, query, params=None):
        """Execute single query"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            logger.info(f"✔ Query executed successfully")
            return True
        except Error as e:
            logger.error(f"✗ Query execution failed: {e}")
            self.connection.rollback()
            return False
    
    def fetch_all(self, query, params=None):
        """Execute query and fetch all results"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"✗ Fetch failed: {e}")
            return None
    
    def fetch_one(self, query, params=None):
        """Execute query and fetch one result"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        except Error as e:
            logger.error(f"✗ Fetch failed: {e}")
            return None
    
    def bulk_insert(self, query, data_list):
        """Bulk insert multiple rows"""
        try:
            count = 0
            for data in data_list:
                self.cursor.execute(query, data)
                count += 1
            
            self.connection.commit()
            logger.info(f"✔ Inserted {count} rows")
            return count
        except Error as e:
            logger.error(f"✗ Bulk insert failed: {e}")
            self.connection.rollback()
            return 0


# Global connection instance
db = DatabaseConnection()


if __name__ == "__main__":
    # Test connection
    if db.connect():
        print("✔ Connection test passed")
        version = db.fetch_one("SELECT version();")
        if version:
            print(f"✔ PostgreSQL version: {version[0][:50]}...")
        db.disconnect()
