"""
Data Verification Script
Performs comprehensive data quality checks on loaded database
"""

import sys
from pathlib import Path
import pandas as pd
from typing import Dict, List
import logging

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.connection import db
from src.config.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataVerifier:
    """Verifies data quality in the database"""
    
    def __init__(self):
        self.issues = []
    
    def verify_table_counts(self) -> Dict[str, int]:
        """Check row counts for all tables"""
        logger.info("Checking table row counts...")
        
        tables = ['account', 'merchant', 'device', 'transaction', 'shared_device']
        counts = {}
        
        for table in tables:
            try:
                count = db.get_table_count(table)
                counts[table] = count
                
                if count == 0:
                    self.issues.append(f"Table '{table}' is empty")
                    logger.warning(f"  ⚠ {table}: 0 rows (EMPTY)")
                else:
                    logger.info(f"  ✓ {table}: {count:,} rows")
            except Exception as e:
                self.issues.append(f"Error accessing table '{table}': {e}")
                logger.error(f"  ✗ {table}: Error - {e}")
        
        return counts
    
    def verify_referential_integrity(self) -> None:
        """Check foreign key relationships"""
        logger.info("\nChecking referential integrity...")
        
        # Check transactions reference valid accounts
        query = """
            SELECT COUNT(*) as orphaned
            FROM transaction t
            LEFT JOIN account a ON t.account_id = a.account_id
            WHERE a.account_id IS NULL
        """
        result = db.execute_query(query)
        orphaned = result[0]['orphaned']
        
        if orphaned > 0:
            self.issues.append(f"Found {orphaned} transactions with invalid account_id")
            logger.warning(f"  ⚠ Transactions with invalid account: {orphaned}")
        else:
            logger.info(f"  ✓ All transactions have valid accounts")
        
        # Check transactions reference valid merchants
        query = """
            SELECT COUNT(*) as orphaned
            FROM transaction t
            LEFT JOIN merchant m ON t.merchant_id = m.merchant_id
            WHERE m.merchant_id IS NULL
        """
        result = db.execute_query(query)
        orphaned = result[0]['orphaned']
        
        if orphaned > 0:
            self.issues.append(f"Found {orphaned} transactions with invalid merchant_id")
            logger.warning(f"  ⚠ Transactions with invalid merchant: {orphaned}")
        else:
            logger.info(f"  ✓ All transactions have valid merchants")
        
        # Check transactions reference valid devices
        query = """
            SELECT COUNT(*) as orphaned
            FROM transaction t
            LEFT JOIN device d ON t.device_id = d.device_id
            WHERE t.device_id IS NOT NULL AND d.device_id IS NULL
        """
        result = db.execute_query(query)
        orphaned = result[0]['orphaned']
        
        if orphaned > 0:
            self.issues.append(f"Found {orphaned} transactions with invalid device_id")
            logger.warning(f"  ⚠ Transactions with invalid device: {orphaned}")
        else:
            logger.info(f"  ✓ All transactions have valid devices")
    
    def verify_data_ranges(self) -> None:
        """Check if data values are within expected ranges"""
        logger.info("\nChecking data value ranges...")
        
        # Check risk scores (should be 0-1)
        query = "SELECT COUNT(*) as invalid FROM account WHERE risk_score < 0 OR risk_score > 1"
        result = db.execute_query(query)
        if result[0]['invalid'] > 0:
            self.issues.append(f"Found {result[0]['invalid']} accounts with invalid risk_score")
            logger.warning(f"  ⚠ Invalid account risk scores: {result[0]['invalid']}")
        else:
            logger.info(f"  ✓ All account risk scores are valid (0-1)")
        
        # Check transaction amounts (should be positive)
        query = "SELECT COUNT(*) as invalid FROM transaction WHERE transaction_amount < 0"
        result = db.execute_query(query)
        if result[0]['invalid'] > 0:
            self.issues.append(f"Found {result[0]['invalid']} transactions with negative amounts")
            logger.warning(f"  ⚠ Negative transaction amounts: {result[0]['invalid']}")
        else:
            logger.info(f"  ✓ All transaction amounts are positive")
        
        # Check transaction hours (0-23)
        query = """
            SELECT COUNT(*) as invalid 
            FROM transaction 
            WHERE transaction_hour IS NOT NULL 
            AND (transaction_hour < 0 OR transaction_hour > 23)
        """
        result = db.execute_query(query)
        if result[0]['invalid'] > 0:
            self.issues.append(f"Found {result[0]['invalid']} transactions with invalid hours")
            logger.warning(f"  ⚠ Invalid transaction hours: {result[0]['invalid']}")
        else:
            logger.info(f"  ✓ All transaction hours are valid (0-23)")
    
    def verify_fraud_distribution(self) -> None:
        """Check fraud label distribution"""
        logger.info("\nChecking fraud distribution...")
        
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) as fraud_count,
                ROUND(AVG(CASE WHEN is_fraud THEN 1.0 ELSE 0.0 END) * 100, 4) as fraud_rate
            FROM transaction
        """
        result = db.execute_query(query)
        
        if result:
            stats = result[0]
            logger.info(f"  Total transactions: {stats['total']:,}")
            logger.info(f"  Fraud cases: {stats['fraud_count']:,}")
            logger.info(f"  Fraud rate: {stats['fraud_rate']}%")
            
            # Warn if fraud rate is too low or too high
            if stats['fraud_rate'] < 0.5:
                self.issues.append(f"Unusually low fraud rate: {stats['fraud_rate']}%")
                logger.warning(f"  ⚠ Fraud rate seems low")
            elif stats['fraud_rate'] > 10:
                self.issues.append(f"Unusually high fraud rate: {stats['fraud_rate']}%")
                logger.warning(f"  ⚠ Fraud rate seems high")
            else:
                logger.info(f"  ✓ Fraud rate is within expected range")
    
    def verify_shared_devices(self) -> None:
        """Check shared device patterns"""
        logger.info("\nChecking shared device patterns...")
        
        query = """
            SELECT 
                COUNT(DISTINCT device_id) as shared_devices,
                COUNT(*) as total_pairs,
                AVG(accounts_per_device) as avg_accounts
            FROM (
                SELECT 
                    device_id,
                    COUNT(DISTINCT account_id) as accounts_per_device
                FROM shared_device
                GROUP BY device_id
                HAVING COUNT(DISTINCT account_id) > 1
            ) sub
        """
        result = db.execute_query(query)
        
        if result and result[0]['shared_devices']:
            stats = result[0]
            logger.info(f"  Shared devices: {stats['shared_devices']:,}")
            logger.info(f"  Total device-account pairs: {stats['total_pairs']:,}")
            logger.info(f"  Avg accounts per device: {stats['avg_accounts']:.2f}")
        else:
            logger.info(f"  No shared devices found")
    
    def verify_null_values(self) -> None:
        """Check for unexpected NULL values"""
        logger.info("\nChecking for NULL values in critical fields...")
        
        checks = [
            ("transaction", "account_id", False),
            ("transaction", "merchant_id", False),
            ("transaction", "transaction_amount", False),
            ("transaction", "is_fraud", False),
            ("account", "account_id", False),
            ("merchant", "merchant_id", False),
            ("device", "device_id", False),
        ]
        
        for table, column, nullable in checks:
            query = f"SELECT COUNT(*) as null_count FROM {table} WHERE {column} IS NULL"
            result = db.execute_query(query)
            null_count = result[0]['null_count']
            
            if null_count > 0 and not nullable:
                self.issues.append(f"Found {null_count} NULL values in {table}.{column}")
                logger.warning(f"  ⚠ {table}.{column}: {null_count} NULL values")
            else:
                logger.info(f"  ✓ {table}.{column}: No unexpected NULLs")
    
    def verify_duplicates(self) -> None:
        """Check for duplicate records"""
        logger.info("\nChecking for duplicate records...")
        
        # Check duplicate transaction IDs
        query = """
            SELECT transaction_id, COUNT(*) as count
            FROM transaction
            GROUP BY transaction_id
            HAVING COUNT(*) > 1
        """
        result = db.execute_query(query)
        
        if result:
            self.issues.append(f"Found {len(result)} duplicate transaction IDs")
            logger.warning(f"  ⚠ Duplicate transaction IDs: {len(result)}")
        else:
            logger.info(f"  ✓ No duplicate transaction IDs")
        
        # Check duplicate accounts
        query = """
            SELECT account_id, COUNT(*) as count
            FROM account
            GROUP BY account_id
            HAVING COUNT(*) > 1
        """
        result = db.execute_query(query)
        
        if result:
            self.issues.append(f"Found {len(result)} duplicate account IDs")
            logger.warning(f"  ⚠ Duplicate account IDs: {len(result)}")
        else:
            logger.info(f"  ✓ No duplicate account IDs")
    
    def generate_report(self) -> None:
        """Generate summary report"""
        print("\n" + "=" * 70)
        print("DATA VERIFICATION REPORT")
        print("=" * 70)
        
        if not self.issues:
            print("\n✓ All verification checks passed!")
            print("  Data quality is good.")
        else:
            print(f"\n⚠ Found {len(self.issues)} issue(s):")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
        
        print("\n" + "=" * 70)
    
    def run_all_checks(self) -> bool:
        """
        Run all verification checks
        
        Returns:
            True if all checks pass, False otherwise
        """
        logger.info("=" * 70)
        logger.info("Starting data verification...")
        logger.info("=" * 70)
        
        self.verify_table_counts()
        self.verify_referential_integrity()
        self.verify_data_ranges()
        self.verify_fraud_distribution()
        self.verify_shared_devices()
        self.verify_null_values()
        self.verify_duplicates()
        
        self.generate_report()
        
        return len(self.issues) == 0


def main():
    """Main execution"""
    verifier = DataVerifier()
    
    # Check database connection
    if not db.test_connection():
        logger.error("Cannot connect to database!")
        sys.exit(1)
    
    # Run all checks
    all_passed = verifier.run_all_checks()
    
    if all_passed:
        logger.info("\n✓ Data verification completed successfully!")
        logger.info("\nNext step: python src/graph/build_graph.py")
        sys.exit(0)
    else:
        logger.warning("\n⚠ Data verification completed with issues.")
        logger.warning("Please review the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
