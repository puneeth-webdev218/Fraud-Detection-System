"""Quick Database Verification"""
from src.database.connection import db

print("\n" + "="*50)
print(" FRAUD DETECTION DATABASE VERIFICATION")
print("="*50 + "\n")

# Table counts
tables = ['account', 'merchant', 'device', 'transaction', 'shared_device']
print("TABLE ROW COUNTS:")
for t in tables:
    count = db.execute_query(f"SELECT COUNT(*) FROM {t}")[0]['count']
    print(f"  {t:15s}: {count:,} rows")

# Fraud distribution
print("\nFRAUD DISTRIBUTION:")
fraud_stats = db.execute_query("""
    SELECT 
        CASE WHEN is_fraud THEN 'Fraud' ELSE 'Legitimate' END as type,
        COUNT(*) as count,
        ROUND(COUNT(*)::NUMERIC * 100.0 / (SELECT COUNT(*) FROM transaction), 2) as pct
    FROM transaction
    GROUP BY is_fraud
""")
for row in fraud_stats:
    print(f"  {row['type']:12s}: {row['count']:,} ({row['pct']}%)")

# Sample data
print("\nSAMPLE TRANSACTIONS (Latest 5):")
samples = db.execute_query("""
    SELECT transaction_id, account_id, transaction_amount, is_fraud
    FROM transaction 
    ORDER BY transaction_date DESC 
    LIMIT 5
""")
for row in samples:
    status = "⚠️ FRAUD" if row['is_fraud'] else "✓ OK"
    print(f"  ID: {row['transaction_id']}, Amount: ${row['transaction_amount']:.2f}, Status: {status}")

print("\n" + "="*50)
print(" ✓ DATABASE IS OPERATIONAL")
print("="*50 + "\n")
