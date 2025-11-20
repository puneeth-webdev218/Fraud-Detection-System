"""
Database Connection Module
Handles PostgreSQL database connections and session management
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor, execute_batch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import logging
from pathlib import Path

from ..config.config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Database connection manager for PostgreSQL
    Supports both raw psycopg2 and SQLAlchemy connections
    """
    
    def __init__(self):
        self.db_uri = config.get_database_uri()
        self._connection_pool: Optional[pool.SimpleConnectionPool] = None
        self._engine = None
        self._session_factory = None
    
    def initialize_pool(self, minconn: int = 1, maxconn: int = 10) -> None:
        """
        Initialize connection pool for psycopg2
        
        Args:
            minconn: Minimum number of connections
            maxconn: Maximum number of connections
        """
        try:
            self._connection_pool = pool.SimpleConnectionPool(
                minconn,
                maxconn,
                host=config.DB_HOST,
                port=config.DB_PORT,
                database=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASSWORD
            )
            logger.info(f"Connection pool initialized: {minconn}-{maxconn} connections")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    def initialize_sqlalchemy(self) -> None:
        """Initialize SQLAlchemy engine and session factory"""
        try:
            self._engine = create_engine(
                self.db_uri,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before using
                echo=False  # Set to True for SQL query logging
            )
            self._session_factory = sessionmaker(bind=self._engine)
            logger.info("SQLAlchemy engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize SQLAlchemy: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for psycopg2 connections
        
        Yields:
            psycopg2 connection object
        """
        if self._connection_pool is None:
            self.initialize_pool()
        
        conn = self._connection_pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            self._connection_pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """
        Context manager for database cursors
        
        Args:
            cursor_factory: Cursor type (default: RealDictCursor for dict results)
        
        Yields:
            Database cursor
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Context manager for SQLAlchemy sessions
        
        Yields:
            SQLAlchemy session object
        """
        if self._engine is None:
            self.initialize_sqlalchemy()
        
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dicts
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
        
        Returns:
            List of dictionaries containing query results
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
        
        Returns:
            Number of affected rows
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def execute_batch(self, query: str, data: List[tuple], page_size: int = 1000) -> None:
        """
        Execute batch insert/update operations efficiently
        
        Args:
            query: SQL query with placeholders
            data: List of tuples containing data
            page_size: Number of records to insert per batch
        """
        with self.get_cursor() as cursor:
            execute_batch(cursor, query, data, page_size=page_size)
        logger.info(f"Batch executed: {len(data)} records")
    
    def execute_sql_file(self, file_path: Path) -> None:
        """
        Execute SQL commands from a file
        
        Args:
            file_path: Path to SQL file
        """
        if not file_path.exists():
            raise FileNotFoundError(f"SQL file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql_content)
                logger.info(f"SQL file executed: {file_path.name}")
            finally:
                cursor.close()
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result:
                    logger.info("Database connection successful!")
                    return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get information about a table's columns
        
        Args:
            table_name: Name of the table
        
        Returns:
            List of column information dictionaries
        """
        query = """
            SELECT 
                column_name, 
                data_type, 
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """
        return self.execute_query(query, (table_name,))
    
    def get_table_count(self, table_name: str) -> int:
        """
        Get the number of rows in a table
        
        Args:
            table_name: Name of the table
        
        Returns:
            Number of rows
        """
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def close_all(self) -> None:
        """Close all database connections"""
        if self._connection_pool:
            self._connection_pool.closeall()
            logger.info("All connections closed")
        
        if self._engine:
            self._engine.dispose()
            logger.info("SQLAlchemy engine disposed")


# Create a singleton database connection instance
db = DatabaseConnection()


def get_db_connection():
    """Factory function to get database connection"""
    return db.get_connection()


def get_db_session():
    """Factory function to get SQLAlchemy session"""
    return db.get_session()


if __name__ == "__main__":
    # Test database connection
    print("Testing database connection...")
    
    if db.test_connection():
        print("✓ Database connection successful!")
        
        # Test query
        try:
            result = db.execute_query("SELECT current_database(), current_user, version()")
            print(f"\nDatabase: {result[0]['current_database']}")
            print(f"User: {result[0]['current_user']}")
            print(f"Version: {result[0]['version'][:50]}...")
        except Exception as e:
            print(f"✗ Query test failed: {e}")
    else:
        print("✗ Database connection failed!")
        print("\nMake sure:")
        print("1. PostgreSQL is running")
        print("2. Database 'fraud_detection' exists")
        print("3. Credentials in .env file are correct")
