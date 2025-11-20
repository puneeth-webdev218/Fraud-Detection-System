"""
Main Data Loading Script
Orchestrates the complete data loading pipeline:
1. Load and process IEEE-CIS dataset
2. Insert processed data into PostgreSQL database
3. Verify data integrity
"""

import sys
from pathlib import Path
import argparse
import logging
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.config import config
from src.preprocessing.data_loader import DataLoader
from src.preprocessing.db_inserter import DatabaseInserter
from src.database.connection import db

# Configure logging
log_file = config.LOG_PATH / f'load_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_prerequisites() -> bool:
    """
    Check if all prerequisites are met before starting
    
    Returns:
        True if all checks pass, False otherwise
    """
    logger.info("Checking prerequisites...")
    
    checks_passed = True
    
    # Check if database is accessible
    logger.info("  - Checking database connection...")
    if not db.test_connection():
        logger.error("    ✗ Database connection failed")
        checks_passed = False
    else:
        logger.info("    ✓ Database connection successful")
    
    # Check if required tables exist
    logger.info("  - Checking database tables...")
    required_tables = ['account', 'merchant', 'device', 'transaction', 'shared_device']
    for table in required_tables:
        try:
            db.get_table_count(table)
            logger.info(f"    ✓ Table '{table}' exists")
        except Exception as e:
            logger.error(f"    ✗ Table '{table}' not found: {e}")
            checks_passed = False
    
    # Check if raw data files exist
    logger.info("  - Checking dataset files...")
    required_files = ['train_transaction.csv', 'train_identity.csv']
    for filename in required_files:
        filepath = config.DATA_RAW_PATH / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            logger.info(f"    ✓ Found {filename} ({size_mb:.1f} MB)")
        else:
            logger.error(f"    ✗ File not found: {filename}")
            logger.error(f"      Expected location: {filepath}")
            checks_passed = False
    
    # Check if processed data directory exists
    if not config.DATA_PROCESSED_PATH.exists():
        logger.info(f"  - Creating processed data directory...")
        config.DATA_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f"    ✓ Created {config.DATA_PROCESSED_PATH}")
    
    return checks_passed


def display_summary(results: dict) -> None:
    """
    Display summary of data loading results
    
    Args:
        results: Dictionary with processing and insertion results
    """
    print("\n" + "=" * 70)
    print("DATA LOADING SUMMARY")
    print("=" * 70)
    
    if 'processed' in results:
        print("\n📊 Data Processing:")
        for table, count in results['processed'].items():
            print(f"  • {table.capitalize()}: {count:,} rows processed")
    
    if 'inserted' in results:
        print("\n💾 Database Insertion:")
        for table, count in results['inserted'].items():
            print(f"  • {table.capitalize()}: {count:,} rows inserted")
    
    # Query database for verification
    print("\n✅ Database Verification:")
    tables = ['account', 'merchant', 'device', 'transaction', 'shared_device']
    for table in tables:
        try:
            count = db.get_table_count(table)
            print(f"  • {table.capitalize()}: {count:,} rows")
        except Exception as e:
            print(f"  • {table.capitalize()}: Error - {e}")
    
    # Fraud statistics
    try:
        fraud_stats = db.execute_query("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) as fraud_count,
                ROUND(AVG(CASE WHEN is_fraud THEN 1.0 ELSE 0.0 END) * 100, 2) as fraud_rate
            FROM transaction
        """)
        
        if fraud_stats:
            stats = fraud_stats[0]
            print(f"\n📈 Fraud Statistics:")
            print(f"  • Total Transactions: {stats['total']:,}")
            print(f"  • Fraud Cases: {stats['fraud_count']:,}")
            print(f"  • Fraud Rate: {stats['fraud_rate']}%")
    except Exception as e:
        logger.warning(f"Could not retrieve fraud statistics: {e}")
    
    print("\n" + "=" * 70)
    print("✓ Data loading pipeline completed successfully!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Verify data quality: python src/preprocessing/verify_data.py")
    print("  2. Build graph: python src/graph/build_graph.py")
    print("  3. Train model: python src/training/train.py")
    print("=" * 70 + "\n")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Load and process IEEE-CIS fraud detection dataset'
    )
    parser.add_argument(
        '--sample',
        type=int,
        default=None,
        help='Sample size for testing (default: None = full dataset)'
    )
    parser.add_argument(
        '--skip-processing',
        action='store_true',
        help='Skip data processing and only insert existing CSV files'
    )
    parser.add_argument(
        '--skip-insertion',
        action='store_true',
        help='Skip database insertion (only process and save CSV files)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=5000,
        help='Batch size for database insertion (default: 5000)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("FRAUD DETECTION SYSTEM - DATA LOADING PIPELINE")
    print("=" * 70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Log File: {log_file}")
    print("=" * 70 + "\n")
    
    # Check prerequisites
    logger.info("=" * 70)
    logger.info("STEP 1: Checking Prerequisites")
    logger.info("=" * 70)
    
    if not check_prerequisites():
        logger.error("\n✗ Prerequisites check failed!")
        logger.error("Please ensure:")
        logger.error("  1. PostgreSQL is running")
        logger.error("  2. Database 'fraud_detection' exists (run: python src/database/setup_db.py)")
        logger.error("  3. Dataset files are in data/raw/ directory")
        sys.exit(1)
    
    logger.info("\n✓ All prerequisites met!\n")
    
    results = {}
    
    # Step 2: Process Data
    if not args.skip_processing:
        logger.info("=" * 70)
        logger.info("STEP 2: Processing Dataset")
        logger.info("=" * 70)
        
        try:
            loader = DataLoader()
            processed_data = loader.process_dataset(sample_size=args.sample)
            
            results['processed'] = {
                name: len(df) for name, df in processed_data.items()
            }
            
            logger.info("\n✓ Data processing completed successfully!\n")
            
        except Exception as e:
            logger.error(f"\n✗ Data processing failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)
    else:
        logger.info("Skipping data processing (using existing CSV files)")
    
    # Step 3: Insert into Database
    if not args.skip_insertion:
        logger.info("=" * 70)
        logger.info("STEP 3: Inserting Data into Database")
        logger.info("=" * 70)
        
        try:
            inserter = DatabaseInserter(batch_size=args.batch_size)
            insertion_results = inserter.insert_all_data()
            
            results['inserted'] = insertion_results
            
            logger.info("\n✓ Database insertion completed successfully!\n")
            
            # Verify insertion
            logger.info("=" * 70)
            logger.info("STEP 4: Verifying Data Integrity")
            logger.info("=" * 70)
            
            inserter.verify_insertion()
            
        except Exception as e:
            logger.error(f"\n✗ Database insertion failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)
    else:
        logger.info("Skipping database insertion")
    
    # Display summary
    display_summary(results)
    
    logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Log saved to: {log_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n✗ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n✗ Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
