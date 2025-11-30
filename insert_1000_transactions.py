#!/usr/bin/env python3
"""
Direct SQL insertion of 1000 transactions to PostgreSQL
Simple and reliable approach bypassing the ORM layer
"""

import psycopg2
from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Connection parameters
conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432'),
    database=os.getenv('DB_NAME', 'fraud_detection'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD')
)

cursor = conn.cursor()

print("\n" + "="*80)
print("DIRECT TRANSACTION INSERTION (1000 rows)")
print("="*80)

# Step 1: Load dataset
logger.info("Loading dataset...")
csv_path = "data/raw/train_transaction.csv"
df = pd.read_csv(csv_path, nrows=1000, usecols=['TransactionID', 'TransactionAmt', 'isFraud'])
logger.info(f"✓ Loaded {len(df)} transactions")

# Step 2: Prepare data for bulk insert
logger.info("Preparing 1000 transactions for insertion...")
transaction_data = []

base_id = 1000  # Start from 1000 to avoid conflicts with existing 20 rows

for idx, row in df.iterrows():
    trans_id = base_id + idx  # Create unique transaction IDs
    account_id = (trans_id % 100) + 1  # Distribute across 1-100
    merchant_id = (trans_id % 15) + 1  # Distribute across 1-15
    device_id = (trans_id % 10) + 1    # Distribute across 1-10
    amount = float(row['TransactionAmt'])
    is_fraud = bool(row['isFraud'])
    trans_date = datetime.now() - timedelta(hours=abs(int(trans_id) % 720))
    card_type = 'debit' if trans_id % 2 == 0 else 'credit'
    
    transaction_data.append((
        trans_id,           # transaction_id
        account_id,         # account_id
        merchant_id,        # merchant_id
        device_id,          # device_id
        amount,             # transaction_amount
        trans_date,         # transaction_date
        card_type,          # card_type
        is_fraud            # is_fraud
    ))

logger.info(f"✓ Prepared {len(transaction_data)} transaction records")

# Step 3: Bulk insert using execute_values for efficiency
try:
    from psycopg2.extras import execute_values
    
    logger.info("Inserting transactions into database...")
    
    sql = """
    INSERT INTO transaction (
        transaction_id, account_id, merchant_id, device_id, 
        transaction_amount, transaction_date, card_type, is_fraud
    ) VALUES %s
    ON CONFLICT (transaction_id) DO NOTHING
    """
    
    execute_values(cursor, sql, transaction_data, page_size=100)
    conn.commit()
    
    logger.info(f"✓ Inserted 1000 transactions successfully")
    
except Exception as e:
    logger.error(f"❌ Insertion failed: {e}")
    conn.rollback()
    cursor.close()
    conn.close()
    exit(1)

# Step 4: Verify insertion
logger.info("Verifying insertion...")

cursor.execute("SELECT COUNT(*) FROM transaction;")
total_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM transaction WHERE is_fraud = TRUE;")
fraud_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM transaction WHERE is_fraud = FALSE;")
legit_count = cursor.fetchone()[0]

cursor.execute("SELECT AVG(transaction_amount) FROM transaction;")
avg_amount = cursor.fetchone()[0]

logger.info(f"\n✓ VERIFICATION RESULTS:")
logger.info(f"  Total Transactions: {total_count}")
logger.info(f"  ├─ Fraudulent: {fraud_count}")
logger.info(f"  ├─ Legitimate: {legit_count}")
logger.info(f"  └─ Avg Amount: ${avg_amount:.2f}")

fraud_rate = (fraud_count / total_count * 100) if total_count > 0 else 0
logger.info(f"\n✓ Fraud Rate: {fraud_rate:.2f}%")

# Step 5: Show sample of newly inserted data
cursor.execute("""
    SELECT transaction_id, account_id, transaction_amount, is_fraud 
    FROM transaction 
    WHERE transaction_id >= 1000 
    ORDER BY transaction_id 
    LIMIT 5;
""")

logger.info(f"\n✓ Sample of Newly Inserted Transactions:")
for row in cursor.fetchall():
    logger.info(f"  ID: {row[0]}, Account: {row[1]}, Amount: ${row[2]:.2f}, Fraud: {row[3]}")

cursor.close()
conn.close()

print("\n" + "="*80)
print("✅ INSERTION COMPLETE!")
print("="*80)
print("\n✓ Check pgAdmin:")
print("  1. Open http://localhost:5050")
print("  2. Query: SELECT COUNT(*) FROM transaction;")
print("  3. Should show 1020 rows (20 initial + 1000 new)")
print("="*80 + "\n")
