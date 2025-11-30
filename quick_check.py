#!/usr/bin/env python3
"""Quick check of database state"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432'),
    database=os.getenv('DB_NAME', 'fraud_detection'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD')
)

cursor = conn.cursor()

print("\n" + "="*70)
print("DATABASE STATE CHECK")
print("="*70)

# Check transaction table
cursor.execute("SELECT COUNT(*) FROM transaction;")
total = cursor.fetchone()[0]
print(f"\n✓ Total Transactions: {total}")

cursor.execute("SELECT COUNT(*) FROM transaction WHERE is_fraud = TRUE;")
fraud = cursor.fetchone()[0]
print(f"  ├─ Fraudulent: {fraud}")

cursor.execute("SELECT COUNT(*) FROM transaction WHERE is_fraud = FALSE;")
legit = cursor.fetchone()[0]
print(f"  └─ Legitimate: {legit}")

# Check if fraud_predictions exists
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'fraud_predictions'
    );
""")
exists = cursor.fetchone()[0]
print(f"\n✓ fraud_predictions table exists: {exists}")

if exists:
    cursor.execute("SELECT COUNT(*) FROM fraud_predictions;")
    pred_count = cursor.fetchone()[0]
    print(f"  └─ Total Predictions: {pred_count}")

# Check other tables
cursor.execute("""
    SELECT tablename FROM pg_tables 
    WHERE schemaname = 'public' 
    ORDER BY tablename;
""")
tables = cursor.fetchall()
print(f"\n✓ All tables in database:")
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
    count = cursor.fetchone()[0]
    print(f"  ├─ {table[0]}: {count} rows")

# Check last 5 transaction IDs
cursor.execute("SELECT transaction_id, account_id, is_fraud FROM transaction ORDER BY transaction_id DESC LIMIT 5;")
print(f"\n✓ Last 5 Transactions:")
for row in cursor.fetchall():
    print(f"  ├─ ID: {row[0]}, Account: {row[1]}, Fraud: {row[2]}")

cursor.close()
conn.close()
print("\n" + "="*70 + "\n")
