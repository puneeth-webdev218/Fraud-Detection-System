"""Database module"""
from .db_connection import DatabaseConnection, DatabaseConfig, get_connection
from .table_manager import TableManager, setup_database
from .data_inserter import DataInserter
from .fraud_db_manager import FraudDetectionDatabaseManager, setup_fraud_db

# For backward compatibility
get_db_connection = get_connection

__all__ = [
    'DatabaseConnection',
    'DatabaseConfig', 
    'get_connection',
    'get_db_connection',
    'TableManager',
    'setup_database',
    'DataInserter',
    'FraudDetectionDatabaseManager',
    'setup_fraud_db'
]
