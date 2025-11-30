"""
Integration Example: Using PostgreSQL Database with Fraud Detection Pipeline

This example shows how to integrate the database manager into your pipeline
"""

import pandas as pd
import logging
from src.database.fraud_db_manager import FraudDetectionDatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_fraud_detection_with_database(input_csv: str, output_csv: str = None):
    """
    Complete pipeline: Load data → Run detection → Save to PostgreSQL
    
    Args:
        input_csv: Path to input CSV file
        output_csv: Path to save processed CSV (optional)
    """
    
    logger.info("\n" + "="*70)
    logger.info("FRAUD DETECTION PIPELINE WITH POSTGRESQL")
    logger.info("="*70)
    
    # Step 1: Initialize database
    logger.info("\n[STEP 1] Initializing Database Connection...")
    db_manager = FraudDetectionDatabaseManager()
    
    if not db_manager.setup():
        logger.error("Failed to setup database. Pipeline aborted.")
        return False
    
    try:
        # Step 2: Load input data
        logger.info("\n[STEP 2] Loading Input Data...")
        if not pd.io.common.file_exists(input_csv):
            logger.error(f"Input file not found: {input_csv}")
            return False
        
        df = pd.read_csv(input_csv)
        logger.info(f"✓ Loaded {len(df)} records from {input_csv}")
        
        # Step 3: Data preprocessing
        logger.info("\n[STEP 3] Preprocessing Data...")
        # (Your preprocessing code here)
        
        # Step 4: Fraud detection / prediction
        logger.info("\n[STEP 4] Running Fraud Detection...")
        # (Your fraud detection model code here)
        # Example: Add a fraud_flag column
        if 'isFraud' in df.columns:
            df['fraud_flag'] = df['isFraud']
        else:
            df['fraud_flag'] = 0  # Default if not present
        
        logger.info(f"✓ Fraud detection complete")
        
        # Step 5: Save to CSV (optional)
        if output_csv:
            logger.info(f"\n[STEP 5] Saving Results to CSV...")
            df.to_csv(output_csv, index=False)
            logger.info(f"✓ Results saved to {output_csv}")
        
        # Step 6: Insert into PostgreSQL
        logger.info(f"\n[STEP 6] Inserting Results into PostgreSQL...")
        
        # Define column mapping (adjust based on your DataFrame column names)
        column_mapping = {
            'TransactionID': 'TransactionID',  # or your ID column
            'account_id': 'card_1',             # Card/Account ID
            'merchant_id': 'merchant_id',
            'device_id': 'device_id',
            'amount': 'TransactionAmt',
            'timestamp': 'TransactionDT',       # or your timestamp column
            'fraud_flag': 'fraud_flag'
        }
        
        # Insert into database
        success = db_manager.insert_results(df, column_mapping)
        
        if success:
            logger.info("✓ Data inserted into PostgreSQL successfully")
            
            # Step 7: Show summary
            logger.info("\n[STEP 7] Database Summary...")
            db_manager.print_summary()
            
            logger.info("\n" + "="*70)
            logger.info("✓ PIPELINE COMPLETE!")
            logger.info("="*70)
            logger.info("\nNext: Open pgAdmin and view the 'fraud_detection' database")
            logger.info("      Tables: 'transactions' and 'fraud_predictions'")
            logger.info("="*70 + "\n")
            
            return True
        else:
            logger.error("Failed to insert data into PostgreSQL")
            return False
    
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        return False
    
    finally:
        # Always disconnect
        logger.info("Closing database connection...")
        db_manager.disconnect()


def example_with_sample_data():
    """
    Example showing how to use the database manager with sample data
    """
    
    logger.info("\n" + "="*70)
    logger.info("FRAUD DETECTION DATABASE - SAMPLE DATA EXAMPLE")
    logger.info("="*70)
    
    # Create sample DataFrame
    sample_data = {
        'TransactionID': ['TXN_001', 'TXN_002', 'TXN_003', 'TXN_004', 'TXN_005'],
        'card_1': ['ACC_001', 'ACC_002', 'ACC_001', 'ACC_003', 'ACC_004'],
        'merchant_id': ['M001', 'M002', 'M001', 'M003', 'M004'],
        'device_id': ['DEV_001', 'DEV_002', 'DEV_001', 'DEV_003', 'DEV_004'],
        'TransactionAmt': [150.50, 75.25, 200.00, 50.75, 300.25],
        'TransactionDT': ['2024-01-01 10:00', '2024-01-01 11:00', '2024-01-01 12:00', 
                          '2024-01-01 13:00', '2024-01-01 14:00'],
        'fraud_flag': [0, 1, 0, 1, 0]
    }
    
    df = pd.DataFrame(sample_data)
    
    logger.info(f"\n[SAMPLE DATA] Created {len(df)} sample records\n")
    
    # Initialize database manager
    db_manager = FraudDetectionDatabaseManager()
    
    if not db_manager.setup():
        logger.error("Failed to setup database")
        return False
    
    try:
        # Insert data
        logger.info("Inserting sample data into PostgreSQL...")
        
        column_mapping = {
            'TransactionID': 'TransactionID',
            'account_id': 'card_1',
            'merchant_id': 'merchant_id',
            'device_id': 'device_id',
            'amount': 'TransactionAmt',
            'timestamp': 'TransactionDT',
            'fraud_flag': 'fraud_flag'
        }
        
        success = db_manager.insert_results(df, column_mapping)
        
        if success:
            # Show results
            logger.info("\n[RESULTS] Data successfully inserted!")
            db_manager.print_summary()
            
            # Query sample data
            logger.info("Sample data in database:")
            logger.info(df.to_string(index=False))
            
            logger.info("\n[NEXT STEPS]")
            logger.info("  1. Open pgAdmin: http://localhost:5050")
            logger.info("  2. Connect to 'fraud_detection' database")
            logger.info("  3. Query: SELECT * FROM transactions LIMIT 10;")
            
            return True
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return False
    
    finally:
        db_manager.disconnect()


if __name__ == "__main__":
    # Run example with sample data
    example_with_sample_data()
    
    # Alternatively, run with your actual pipeline:
    # run_fraud_detection_with_database('data/raw/train_transaction.csv', 'data/processed/results.csv')
