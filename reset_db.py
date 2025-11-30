#!/usr/bin/env python
"""Reset the fraud_detection database"""

import psycopg2
from psycopg2 import sql

conn = psycopg2.connect(
    dbname='fraud_detection',
    user='postgres',
    password='#puneeth123*',
    host='localhost',
    port=5432
)
cur = conn.cursor()

try:
    # Drop tables if they exist
    cur.execute("DROP TABLE IF EXISTS fraud_predictions CASCADE;")
    print("✅ Dropped fraud_predictions table")
    cur.execute("DROP TABLE IF EXISTS transactions CASCADE;")
    print("✅ Dropped transactions table")
    conn.commit()
    print("✅ Database reset successful - Tables removed")
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
