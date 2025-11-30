"""
Insert Data into PostgreSQL Database
Use this to insert transaction data and predictions
"""

import psycopg2
from psycopg2 import Error
import pandas as pd
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataInserter:
    """Handle data insertion into PostgreSQL"""
    
    def __init__(self, db_config=None):
        """Initialize with database configuration"""
        if db_config is None:
            db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5432)),
                'database': os.getenv('DB_NAME', 'fraud_detection'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', '')
            }
        
        self.db_config = db_config
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.cursor = self.connection.cursor()
            logger.info("✔ Connected to PostgreSQL")
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
    
    def insert_transactions(self, df, batch_size=100):
        """
        Insert transactions from DataFrame
        
        Args:
            df (pd.DataFrame): DataFrame with transaction data
            batch_size (int): Number of rows to insert per commit
            
        Returns:
            int: Number of rows inserted
        """
        if not self.cursor:
            logger.error("Not connected to database")
            return 0
        
        insert_query = """
        INSERT INTO transactions 
        (transaction_id, account_id, merchant_id, device_id, amount, timestamp, is_fraud)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (transaction_id) DO NOTHING;
        """
        
        try:
            inserted = 0
            for idx, row in df.iterrows():
                try:
                    self.cursor.execute(insert_query, (
                        str(row.get('TransactionID', f'TXN_{idx}')),
                        str(row.get('account_id', '')),
                        str(row.get('merchant_id', '')),
                        str(row.get('device_id', '')),
                        float(row.get('TransactionAmt', 0)),
                        str(row.get('timestamp', '')),
                        int(row.get('isFraud', 0))
                    ))
                    inserted += 1
                    
                    # Commit in batches
                    if inserted % batch_size == 0:
                        self.connection.commit()
                        logger.info(f"Inserted {inserted} rows...")
                
                except Exception as e:
                    logger.warning(f"Row {idx} insert failed: {e}")
                    continue
            
            # Final commit
            self.connection.commit()
            logger.info(f"✔ Successfully inserted {inserted} transactions")
            return inserted
        
        except Error as e:
            logger.error(f"✗ Insert failed: {e}")
            self.connection.rollback()
            return 0
    
    def insert_prediction(self, transaction_id, fraud_probability, fraud_flag, 
                         model_name="GNN", confidence=None):
        """
        Insert a single fraud prediction
        
        Args:
            transaction_id (str): Transaction ID
            fraud_probability (float): Fraud probability (0-1)
            fraud_flag (int): Fraud flag (0 or 1)
            model_name (str): Name of the model
            confidence (float): Model confidence score
            
        Returns:
            bool: True if successful
        """
        if not self.cursor:
            logger.error("Not connected to database")
            return False
        
        insert_query = """
        INSERT INTO fraud_predictions 
        (transaction_id, fraud_probability, fraud_flag, model_name, confidence)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
        """
        
        try:
            self.cursor.execute(insert_query, (
                transaction_id,
                fraud_probability,
                fraud_flag,
                model_name,
                confidence
            ))
            self.connection.commit()
            return True
        
        except Error as e:
            logger.error(f"✗ Insert prediction failed: {e}")
            self.connection.rollback()
            return False
    
    def insert_predictions_batch(self, predictions_df, batch_size=100):
        """
        Insert multiple fraud predictions from DataFrame
        
        Args:
            predictions_df (pd.DataFrame): DataFrame with predictions
            batch_size (int): Batch size for commits
            
        Returns:
            int: Number of predictions inserted
        """
        if not self.cursor:
            logger.error("Not connected to database")
            return 0
        
        insert_query = """
        INSERT INTO fraud_predictions 
        (transaction_id, fraud_probability, fraud_flag, model_name)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
        """
        
        try:
            inserted = 0
            for idx, row in predictions_df.iterrows():
                try:
                    self.cursor.execute(insert_query, (
                        str(row.get('transaction_id', f'TXN_{idx}')),
                        float(row.get('fraud_probability', 0)),
                        int(row.get('fraud_flag', 0)),
                        str(row.get('model_name', 'GNN'))
                    ))
                    inserted += 1
                    
                    if inserted % batch_size == 0:
                        self.connection.commit()
                        logger.info(f"Inserted {inserted} predictions...")
                
                except Exception as e:
                    logger.warning(f"Prediction {idx} insert failed: {e}")
                    continue
            
            self.connection.commit()
            logger.info(f"✔ Successfully inserted {inserted} predictions")
            return inserted
        
        except Error as e:
            logger.error(f"✗ Bulk insert predictions failed: {e}")
            self.connection.rollback()
            return 0
    
    def get_fraud_statistics(self):
        """Get fraud statistics from database"""
        if not self.cursor:
            return None
        
        try:
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as frauds,
                    ROUND(100.0 * SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) / 
                        NULLIF(COUNT(*), 0), 2) as fraud_rate
                FROM transactions;
            """)
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'total_transactions': result[0],
                    'fraud_count': result[1],
                    'fraud_rate': result[2]
                }
            return None
        
        except Error as e:
            logger.error(f"✗ Error getting statistics: {e}")
            return None


def main():
    """Example usage"""
    
    print("\n" + "="*60)
    print("Data Insertion Tool")
    print("="*60 + "\n")
    
    # Initialize inserter
    inserter = DataInserter()
    
    if not inserter.connect():
        print("Failed to connect to database")
        return False
    
    try:
        # Example: Load and insert transaction data
        # csv_file = 'path/to/transactions.csv'
        # if os.path.exists(csv_file):
        #     df = pd.read_csv(csv_file)
        #     inserter.insert_transactions(df)
        # else:
        #     print(f"CSV file not found: {csv_file}")
        
        # Get statistics
        stats = inserter.get_fraud_statistics()
        if stats:
            print("\nFraud Statistics:")
            print(f"  Total Transactions: {stats['total_transactions']}")
            print(f"  Fraud Count: {stats['fraud_count']}")
            print(f"  Fraud Rate: {stats['fraud_rate']}%")
        
        return True
    
    finally:
        inserter.disconnect()


if __name__ == "__main__":
    main()
