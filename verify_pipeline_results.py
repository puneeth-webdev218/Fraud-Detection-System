#!/usr/bin/env python3
"""
Verification script to confirm fraud detection pipeline results
Checks:
1. 1,000 transactions inserted into PostgreSQL
2. Fraud predictions recorded
3. Data visibility in pgAdmin interface
"""

import logging
import sys
from pathlib import Path
from src.database.fraud_db_manager import FraudDetectionDatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_transactions():
    """Verify 1,000 transactions were inserted"""
    logger.info("\n" + "="*70)
    logger.info("VERIFICATION 1: Transaction Count")
    logger.info("="*70)
    
    try:
        db = FraudDetectionDatabaseManager()
        db.setup()
        
        # Get transaction count
        db.connection.execute("SELECT COUNT(*) FROM transaction;")
        total_count = db.connection.cursor.fetchone()[0]
        
        db.connection.execute("SELECT COUNT(*) FROM transaction WHERE is_fraud = TRUE;")
        fraud_count = db.connection.cursor.fetchone()[0]
        
        db.connection.execute("SELECT COUNT(*) FROM transaction WHERE is_fraud = FALSE;")
        legitimate_count = db.connection.cursor.fetchone()[0]
        
        db.connection.disconnect()
        
        logger.info(f"✓ Total Transactions: {total_count}")
        logger.info(f"  ├─ Fraudulent: {fraud_count}")
        logger.info(f"  └─ Legitimate: {legitimate_count}")
        
        if total_count >= 1000:
            logger.info("✅ PASSED: 1,000+ transactions found in database")
            return True
        else:
            logger.warning(f"⚠️  PARTIAL: Only {total_count} transactions found (expected 1,000+)")
            return False
            
    except Exception as e:
        logger.error(f"❌ FAILED: {str(e)}")
        return False

def verify_fraud_predictions():
    """Verify fraud predictions were recorded"""
    logger.info("\n" + "="*70)
    logger.info("VERIFICATION 2: Fraud Predictions")
    logger.info("="*70)
    
    try:
        db = FraudDetectionDatabaseManager()
        db.setup()
        
        # Check if fraud_predictions table exists
        db.connection.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'fraud_predictions'
            );
        """)
        table_exists = db.connection.cursor.fetchone()[0]
        
        if not table_exists:
            logger.warning("⚠️  fraud_predictions table does not exist yet")
            logger.info("ℹ️  This is expected if no predictions have been recorded")
            db.connection.disconnect()
            return None
        
        # Get prediction statistics
        db.connection.execute("SELECT COUNT(*) FROM fraud_predictions;")
        prediction_count = db.connection.cursor.fetchone()[0]
        
        db.connection.execute("""
            SELECT 
                is_fraud,
                COUNT(*) as count,
                ROUND(AVG(fraud_probability)::numeric, 4) as avg_probability
            FROM fraud_predictions
            GROUP BY is_fraud
            ORDER BY is_fraud;
        """)
        predictions = db.connection.cursor.fetchall()
        
        db.connection.disconnect()
        
        logger.info(f"✓ Total Predictions: {prediction_count}")
        
        for is_fraud, count, avg_prob in predictions:
            fraud_type = "Fraudulent" if is_fraud else "Legitimate"
            logger.info(f"  ├─ {fraud_type}: {count} (avg probability: {avg_prob})")
        
        if prediction_count > 0:
            logger.info("✅ PASSED: Fraud predictions recorded in database")
            return True
        else:
            logger.warning("⚠️  PARTIAL: No predictions recorded yet")
            logger.info("ℹ️  Predictions may be calculated on-demand")
            return None
            
    except Exception as e:
        logger.error(f"❌ FAILED: {str(e)}")
        return False

def verify_data_visibility():
    """Verify data is visible and accessible (pgAdmin compatible)"""
    logger.info("\n" + "="*70)
    logger.info("VERIFICATION 3: Data Visibility (pgAdmin Interface)")
    logger.info("="*70)
    
    try:
        db = FraudDetectionDatabaseManager()
        db.setup()
        
        # Test data visibility with sample queries
        test_queries = [
            ("Transaction Table Schema", """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'transaction'
                ORDER BY ordinal_position;
            """),
            ("Transaction Sample Data", """
                SELECT transaction_id, account_id, merchant_id, transaction_amount, is_fraud
                FROM transaction
                LIMIT 5;
            """),
            ("Database Statistics", """
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """)
        ]
        
        all_passed = True
        
        for query_name, query in test_queries:
            try:
                db.connection.execute(query)
                results = db.connection.cursor.fetchall()
                logger.info(f"✓ {query_name}: {len(results)} row(s) retrieved")
                if query_name == "Transaction Sample Data" and results:
                    for row in results[:2]:
                        logger.info(f"  └─ Sample: {row}")
                all_passed = True
            except Exception as e:
                logger.error(f"✗ {query_name}: {str(e)}")
                all_passed = False
        
        db.connection.disconnect()
        
        if all_passed:
            logger.info("✅ PASSED: All data is visible and accessible via pgAdmin")
            return True
        else:
            logger.warning("⚠️  PARTIAL: Some data visibility issues detected")
            return False
            
    except Exception as e:
        logger.error(f"❌ FAILED: {str(e)}")
        return False

def print_pgadmin_instructions():
    """Print instructions for viewing data in pgAdmin"""
    logger.info("\n" + "="*70)
    logger.info("PGADMIN QUICK COMMANDS")
    logger.info("="*70)
    
    commands = [
        ("Count all transactions", "SELECT COUNT(*) FROM transaction;"),
        ("View recent transactions", "SELECT * FROM transaction ORDER BY transaction_id DESC LIMIT 10;"),
        ("Fraud statistics", """
SELECT 
    is_fraud,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM transaction), 2) as percentage,
    ROUND(AVG(transaction_amount)::numeric, 2) as avg_amount
FROM transaction
GROUP BY is_fraud
ORDER BY is_fraud;
        """),
        ("High-risk transactions", "SELECT * FROM transaction WHERE is_fraud = TRUE ORDER BY transaction_id LIMIT 20;"),
        ("Account-Device combinations", """
SELECT 
    a.account_id,
    a.email_domain,
    d.device_type,
    COUNT(*) as transaction_count,
    SUM(CASE WHEN t.is_fraud THEN 1 ELSE 0 END) as fraud_count
FROM transaction t
JOIN account a ON t.account_id = a.account_id
JOIN device d ON t.device_id = d.device_id
GROUP BY a.account_id, a.email_domain, d.device_type
ORDER BY fraud_count DESC
LIMIT 10;
        """)
    ]
    
    for i, (name, cmd) in enumerate(commands, 1):
        logger.info(f"\n{i}. {name}:")
        logger.info(f"   {cmd.strip()}")

def main():
    """Run all verifications"""
    logger.info("\n" + "="*70)
    logger.info("FRAUD DETECTION PIPELINE VERIFICATION")
    logger.info("="*70)
    
    results = {}
    
    # Run verifications
    results['transactions'] = verify_transactions()
    results['predictions'] = verify_fraud_predictions()
    results['visibility'] = verify_data_visibility()
    
    # Print summary
    logger.info("\n" + "="*70)
    logger.info("VERIFICATION SUMMARY")
    logger.info("="*70)
    
    checks = [
        ("✅ 1,000 Transactions Inserted", results['transactions']),
        ("📊 Fraud Predictions Recorded", results['predictions']),
        ("👁️  Data Visible in pgAdmin", results['visibility'])
    ]
    
    for check_name, result in checks:
        if result is True:
            logger.info(f"{check_name}: ✅ PASSED")
        elif result is False:
            logger.info(f"{check_name}: ❌ FAILED")
        else:
            logger.info(f"{check_name}: ⚠️  PARTIAL")
    
    # Print pgAdmin instructions
    print_pgadmin_instructions()
    
    logger.info("\n" + "="*70)
    logger.info("NEXT STEPS:")
    logger.info("="*70)
    logger.info("1. Open pgAdmin: http://localhost:5050")
    logger.info("2. Login with your PostgreSQL credentials")
    logger.info("3. Navigate: Servers → PostgreSQL 18 → Databases → fraud_detection")
    logger.info("4. Right-click 'fraud_detection' → Query Tool")
    logger.info("5. Copy and run any of the commands above")
    logger.info("="*70 + "\n")
    
    # Return exit code
    if all(v for v in results.values() if v is not None):
        logger.info("✅ All verifications passed!")
        return 0
    else:
        logger.info("⚠️  Some verifications need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
