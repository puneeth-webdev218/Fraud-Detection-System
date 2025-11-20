"""
Database Verification Script
Comprehensive checks for fraud_detection database
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.database.connection import db
import pandas as pd
from tabulate import tabulate

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def verify_tables():
    """Check all tables exist"""
    print_section("1. TABLE VERIFICATION")
    
    query = """
    SELECT table_name, 
           (SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_name = t.table_name) as column_count
    FROM information_schema.tables t
    WHERE table_schema = 'public'
    ORDER BY table_name
    """
    
    tables = db.execute_query(query)
    df = pd.DataFrame(tables)
    print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
    
    return [t['table_name'] for t in tables]

def verify_row_counts():
    """Check row counts"""
    print_section("2. ROW COUNTS")
    
    tables = ['account', 'merchant', 'device', 'transaction', 'shared_device']
    counts = []
    
    for table in tables:
        try:
            result = db.execute_query(f"SELECT COUNT(*) as count FROM {table}")
            counts.append({'Table': table, 'Row Count': f"{result[0]['count']:,}"})
        except Exception as e:
            counts.append({'Table': table, 'Row Count': f'ERROR: {str(e)}'})
    
    df = pd.DataFrame(counts)
    print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))

def verify_fraud_distribution():
    """Check fraud distribution"""
    print_section("3. FRAUD DISTRIBUTION")
    
    query = """
    SELECT 
        CASE WHEN is_fraud THEN 'Fraud' ELSE 'Legitimate' END as transaction_type,
        COUNT(*) as count,
        ROUND(COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM transaction) * 100, 2) as percentage
    FROM transaction
    GROUP BY is_fraud
    """
    
    result = db.execute_query(query)
    df = pd.DataFrame(result)
    print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))

def verify_sample_data():
    """Show sample transactions"""
    print_section("4. SAMPLE TRANSACTIONS (Latest 10)")
    
    query = """
    SELECT 
        transaction_id,
        account_id,
        merchant_id,
        ROUND(transaction_amount::NUMERIC, 2) as amount,
        transaction_date,
        CASE WHEN is_fraud THEN 'FRAUD' ELSE 'OK' END as status
    FROM transaction
    ORDER BY transaction_date DESC
    LIMIT 10
    """
    
    result = db.execute_query(query)
    df = pd.DataFrame(result)
    print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))

def verify_high_risk_accounts():
    """Show high-risk accounts"""
    print_section("5. HIGH-RISK ACCOUNTS (Top 10)")
    
    query = """
    SELECT 
        account_id,
        total_transactions,
        ROUND(total_amount::NUMERIC, 2) as total_amount,
        ROUND(risk_score::NUMERIC, 4) as risk_score,
        fraud_flag
    FROM account
    WHERE risk_score > 0.5
    ORDER BY risk_score DESC
    LIMIT 10
    """
    
    result = db.execute_query(query)
    if result:
        df = pd.DataFrame(result)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
    else:
        print("No high-risk accounts found (risk_score > 0.5)")

def verify_merchant_stats():
    """Show merchant statistics"""
    print_section("6. MERCHANT FRAUD RATES")
    
    query = """
    SELECT 
        merchant_id,
        total_transactions,
        total_fraud_transactions,
        ROUND(fraud_rate::NUMERIC, 4) as fraud_rate,
        risk_level
    FROM merchant
    ORDER BY fraud_rate DESC
    """
    
    result = db.execute_query(query)
    df = pd.DataFrame(result)
    print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))

def verify_shared_devices():
    """Show shared device statistics"""
    print_section("7. SHARED DEVICES (Top 10)")
    
    query = """
    SELECT 
        device_id,
        total_users,
        total_transactions,
        fraud_transactions,
        ROUND(fraud_rate::NUMERIC, 4) as fraud_rate,
        is_shared
    FROM device
    WHERE total_users > 1
    ORDER BY fraud_rate DESC
    LIMIT 10
    """
    
    result = db.execute_query(query)
    if result:
        df = pd.DataFrame(result)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
    else:
        print("No shared devices found")

def verify_data_quality():
    """Check data quality issues"""
    print_section("8. DATA QUALITY CHECKS")
    
    checks = []
    
    # NULL checks
    queries = {
        'NULL account_id': "SELECT COUNT(*) FROM transaction WHERE account_id IS NULL",
        'NULL merchant_id': "SELECT COUNT(*) FROM transaction WHERE merchant_id IS NULL",
        'NULL device_id': "SELECT COUNT(*) FROM transaction WHERE device_id IS NULL",
        'NULL amount': "SELECT COUNT(*) FROM transaction WHERE transaction_amount IS NULL",
        'Negative amount': "SELECT COUNT(*) FROM transaction WHERE transaction_amount < 0",
        'Duplicate transaction_id': "SELECT COUNT(*) - COUNT(DISTINCT transaction_id) FROM transaction"
    }
    
    for check_name, query in queries.items():
        result = db.execute_query(query)
        count = result[0]['count']
        status = '✓ OK' if count == 0 else f'✗ ISSUE ({count} records)'
        checks.append({'Check': check_name, 'Status': status})
    
    df = pd.DataFrame(checks)
    print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))

def verify_relationships():
    """Check foreign key relationships"""
    print_section("9. RELATIONSHIP VERIFICATION")
    
    query = """
    SELECT 
        (SELECT COUNT(DISTINCT account_id) FROM transaction) as accounts_in_transactions,
        (SELECT COUNT(*) FROM account) as total_accounts,
        (SELECT COUNT(DISTINCT merchant_id) FROM transaction) as merchants_in_transactions,
        (SELECT COUNT(*) FROM merchant) as total_merchants,
        (SELECT COUNT(DISTINCT device_id) FROM transaction WHERE device_id IS NOT NULL) as devices_in_transactions,
        (SELECT COUNT(*) FROM device) as total_devices
    """
    
    result = db.execute_query(query)
    df = pd.DataFrame(result)
    print(tabulate(df.T, tablefmt='grid'))

def verify_database_size():
    """Check database size"""
    print_section("10. DATABASE SIZE")
    
    query = """
    SELECT 
        pg_size_pretty(pg_database_size('fraud_detection')) as database_size,
        pg_size_pretty(pg_total_relation_size('transaction')) as transaction_table_size,
        pg_size_pretty(pg_total_relation_size('account')) as account_table_size
    """
    
    result = db.execute_query(query)
    df = pd.DataFrame(result)
    print(tabulate(df.T, tablefmt='grid'))

def verify_indexes():
    """Check indexes"""
    print_section("11. INDEX VERIFICATION")
    
    query = """
    SELECT 
        tablename,
        indexname,
        indexdef
    FROM pg_indexes
    WHERE schemaname = 'public'
    ORDER BY tablename, indexname
    """
    
    result = db.execute_query(query)
    if result:
        # Show count by table
        df = pd.DataFrame(result)
        summary = df.groupby('tablename').size().reset_index(name='index_count')
        print(tabulate(summary, headers='keys', tablefmt='grid', showindex=False))

def main():
    """Run all verification checks"""
    print("\n" + "="*70)
    print("  FRAUD DETECTION DATABASE VERIFICATION")
    print("  PostgreSQL Database: fraud_detection")
    print("="*70)
    
    try:
        # Run all checks
        verify_tables()
        verify_row_counts()
        verify_fraud_distribution()
        verify_sample_data()
        verify_high_risk_accounts()
        verify_merchant_stats()
        verify_shared_devices()
        verify_data_quality()
        verify_relationships()
        verify_database_size()
        verify_indexes()
        
        print("\n" + "="*70)
        print("  ✓ DATABASE VERIFICATION COMPLETE")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ ERROR during verification: {str(e)}\n")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
