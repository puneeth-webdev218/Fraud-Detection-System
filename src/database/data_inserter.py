"""
PostgreSQL Data Insertion Module
Handles inserting fraud detection results into database
"""

import logging
import pandas as pd
from typing import List, Tuple, Optional
from src.database.db_connection import DatabaseConnection

logger = logging.getLogger(__name__)

# SQL queries for inserting data
INSERT_TRANSACTION_SQL = """
INSERT INTO transactions (transaction_id, account_id, merchant_id, device_id, amount, timestamp, fraud_flag)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (transaction_id) DO NOTHING;
"""

INSERT_FRAUD_PREDICTION_SQL = """
INSERT INTO fraud_predictions (transaction_id, fraud_probability, fraud_flag, gnn_risk_score, model_version)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (transaction_id) DO UPDATE SET
    fraud_probability = EXCLUDED.fraud_probability,
    fraud_flag = EXCLUDED.fraud_flag,
    gnn_risk_score = EXCLUDED.gnn_risk_score,
    model_version = EXCLUDED.model_version,
    updated_at = CURRENT_TIMESTAMP;
"""


class DataInserter:
    """Handles inserting fraud detection results into database"""
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize data inserter
        
        Args:
            db_connection: DatabaseConnection object
        """
        self.db = db_connection
    
    def insert_transaction(self, transaction_id: str, account_id: str, merchant_id: str,
                          device_id: str, amount: float, timestamp: str, fraud_flag: int) -> bool:
        """
        Insert single transaction into database
        
        Args:
            transaction_id: Unique transaction ID
            account_id: Account ID
            merchant_id: Merchant ID
            device_id: Device ID
            amount: Transaction amount
            timestamp: Transaction timestamp
            fraud_flag: Fraud label (0 or 1)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            params = (transaction_id, account_id, merchant_id, device_id, amount, timestamp, fraud_flag)
            
            if not self.db.execute(INSERT_TRANSACTION_SQL, params):
                logger.error(f"Failed to insert transaction: {transaction_id}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"✗ Error inserting transaction: {e}")
            return False
    
    def insert_transactions_batch(self, df: pd.DataFrame, 
                                  column_mapping: Optional[dict] = None) -> Tuple[int, int]:
        """
        Insert multiple transactions from DataFrame into database
        
        Args:
            df: DataFrame with transaction data
            column_mapping: Dict mapping DataFrame columns to DB columns
                           Default: {
                               'TransactionID': 'transaction_id',
                               'card_1': 'account_id',
                               'merchant_id': 'merchant_id',
                               'device_id': 'device_id',
                               'TransactionAmt': 'amount',
                               'TransactionDT': 'timestamp',
                               'isFraud': 'fraud_flag'
                           }
        
        Returns:
            Tuple of (inserted_count, skipped_count)
        """
        # Default column mapping
        if column_mapping is None:
            column_mapping = {
                'TransactionID': 'transaction_id',
                'card_1': 'account_id',
                'merchant_id': 'merchant_id',
                'device_id': 'device_id',
                'TransactionAmt': 'amount',
                'TransactionDT': 'timestamp',
                'isFraud': 'fraud_flag'
            }
        
        logger.info(f"Inserting {len(df)} transactions into database...")
        
        inserted_count = 0
        skipped_count = 0
        
        try:
            for idx, row in df.iterrows():
                try:
                    # Extract values from row using column mapping
                    transaction_id = str(row.get(column_mapping['TransactionID'], f"TXN_{idx}"))
                    account_id = str(row.get(column_mapping['account_id'], "UNKNOWN"))
                    merchant_id = str(row.get(column_mapping['merchant_id'], "UNKNOWN"))
                    device_id = str(row.get(column_mapping['device_id'], "UNKNOWN"))
                    amount = float(row.get(column_mapping['amount'], 0.0))
                    timestamp = str(row.get(column_mapping['timestamp'], ""))
                    fraud_flag = int(row.get(column_mapping['fraud_flag'], 0))
                    
                    # Insert transaction
                    if self.insert_transaction(transaction_id, account_id, merchant_id,
                                              device_id, amount, timestamp, fraud_flag):
                        inserted_count += 1
                    else:
                        skipped_count += 1
                    
                    # Progress indicator
                    if (idx + 1) % 1000 == 0:
                        logger.info(f"  Processed {idx + 1}/{len(df)} rows...")
                
                except Exception as e:
                    logger.warning(f"Skipping row {idx}: {e}")
                    skipped_count += 1
                    continue
            
            # Commit all changes
            if not self.db.commit():
                logger.error("Failed to commit transaction batch")
                return (inserted_count, skipped_count + len(df) - inserted_count)
            
            logger.info(f"✓ Inserted {inserted_count} transactions, skipped {skipped_count}")
            
            return (inserted_count, skipped_count)
        
        except Exception as e:
            logger.error(f"✗ Batch insert failed: {e}")
            self.db.rollback()
            return (inserted_count, skipped_count + len(df) - inserted_count)
    
    def insert_fraud_prediction(self, transaction_id: str, fraud_probability: float,
                               fraud_flag: int, gnn_risk_score: float = None,
                               model_version: str = "v1.0") -> bool:
        """
        Insert fraud prediction into database
        
        Args:
            transaction_id: Unique transaction ID
            fraud_probability: Probability of fraud (0-1)
            fraud_flag: Fraud prediction (0 or 1)
            gnn_risk_score: GNN model risk score
            model_version: Model version used for prediction
        
        Returns:
            True if successful, False otherwise
        """
        try:
            params = (transaction_id, fraud_probability, fraud_flag, gnn_risk_score, model_version)
            
            if not self.db.execute(INSERT_FRAUD_PREDICTION_SQL, params):
                logger.error(f"Failed to insert prediction: {transaction_id}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"✗ Error inserting prediction: {e}")
            return False
    
    def insert_fraud_predictions_batch(self, df: pd.DataFrame,
                                      column_mapping: Optional[dict] = None) -> Tuple[int, int]:
        """
        Insert multiple predictions from DataFrame into database
        
        Args:
            df: DataFrame with prediction data
            column_mapping: Dict mapping DataFrame columns to DB columns
        
        Returns:
            Tuple of (inserted_count, skipped_count)
        """
        if column_mapping is None:
            column_mapping = {
                'transaction_id': 'transaction_id',
                'fraud_probability': 'fraud_probability',
                'fraud_flag': 'fraud_flag',
                'gnn_risk_score': 'gnn_risk_score',
                'model_version': 'model_version'
            }
        
        logger.info(f"Inserting {len(df)} predictions into database...")
        
        inserted_count = 0
        skipped_count = 0
        
        try:
            for idx, row in df.iterrows():
                try:
                    transaction_id = str(row.get(column_mapping['transaction_id'], f"TXN_{idx}"))
                    fraud_probability = float(row.get(column_mapping['fraud_probability'], 0.0))
                    fraud_flag = int(row.get(column_mapping['fraud_flag'], 0))
                    gnn_risk_score = float(row.get(column_mapping['gnn_risk_score'], 0.0))
                    model_version = str(row.get(column_mapping['model_version'], "v1.0"))
                    
                    if self.insert_fraud_prediction(transaction_id, fraud_probability,
                                                   fraud_flag, gnn_risk_score, model_version):
                        inserted_count += 1
                    else:
                        skipped_count += 1
                    
                    if (idx + 1) % 1000 == 0:
                        logger.info(f"  Processed {idx + 1}/{len(df)} rows...")
                
                except Exception as e:
                    logger.warning(f"Skipping row {idx}: {e}")
                    skipped_count += 1
                    continue
            
            if not self.db.commit():
                logger.error("Failed to commit prediction batch")
                return (inserted_count, skipped_count + len(df) - inserted_count)
            
            logger.info(f"✓ Inserted {inserted_count} predictions, skipped {skipped_count}")
            
            return (inserted_count, skipped_count)
        
        except Exception as e:
            logger.error(f"✗ Batch insert failed: {e}")
            self.db.rollback()
            return (inserted_count, skipped_count + len(df) - inserted_count)
    
    def get_insertion_summary(self) -> dict:
        """
        Get summary of inserted data
        
        Returns:
            Dictionary with summary statistics
        """
        try:
            summary = {}
            
            # Count transactions
            self.db.execute("SELECT COUNT(*) FROM transactions;")
            result = self.db.fetchone()
            summary['total_transactions'] = result[0] if result else 0
            
            # Count fraudulent transactions
            self.db.execute("SELECT COUNT(*) FROM transactions WHERE fraud_flag = 1;")
            result = self.db.fetchone()
            summary['fraudulent_transactions'] = result[0] if result else 0
            
            # Count predictions
            self.db.execute("SELECT COUNT(*) FROM fraud_predictions;")
            result = self.db.fetchone()
            summary['total_predictions'] = result[0] if result else 0
            
            return summary
        except Exception as e:
            logger.error(f"✗ Error getting summary: {e}")
            return {}


if __name__ == "__main__":
    # Example usage
    from src.database.db_connection import DatabaseConnection, DatabaseConfig
    
    print("\n" + "="*60)
    print("Testing Data Insertion")
    print("="*60 + "\n")
    
    config = DatabaseConfig()
    db = DatabaseConnection(config)
    
    if db.connect():
        inserter = DataInserter(db)
        
        # Test single insertion
        success = inserter.insert_transaction(
            transaction_id="TEST_001",
            account_id="ACC_001",
            merchant_id="MERCH_001",
            device_id="DEV_001",
            amount=100.50,
            timestamp="2024-01-01 10:00:00",
            fraud_flag=0
        )
        db.commit()
        
        if success:
            print("✓ Single transaction inserted successfully")
        
        # Show summary
        summary = inserter.get_insertion_summary()
        print(f"\nDatabase Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        db.disconnect()
    else:
        print("✗ Connection failed!")
    
    print("\n" + "="*60)
