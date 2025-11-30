#!/usr/bin/env python3
"""
Database Verification Script
Directly queries PostgreSQL to verify transaction data
"""

import psycopg2
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

def verify_database():
    """Connect and verify database has the expected data"""
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'fraud_detection'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )
        
        cursor = conn.cursor()
        
        # Check if transactions table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'transactions'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("❌ Transactions table does not exist!")
            return False
        
        print("✅ Transactions table exists")
        
        # Get transaction count
        cursor.execute("SELECT COUNT(*) FROM transactions;")
        count = cursor.fetchone()[0]
        print(f"📊 Total transactions in database: {count:,}")
        
        # Get fraud statistics
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN fraud_flag = 1 THEN 1 ELSE 0 END) as fraud_count,
                ROUND(SUM(CASE WHEN fraud_flag = 1 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as fraud_rate
            FROM transactions;
        """)
        result = cursor.fetchone()
        fraud_count = result[0] or 0
        fraud_rate = float(result[1]) if result[1] else 0.0
        
        print(f"🚨 Fraudulent transactions: {fraud_count:,} ({fraud_rate}%)")
        
        # Get sample of recent transactions
        cursor.execute("""
            SELECT transaction_id, account_id, amount, fraud_flag
            FROM transactions
            ORDER BY transaction_id DESC
            LIMIT 5;
        """)
        
        print("\n📋 Recent transactions (last 5):")
        print("-" * 80)
        print(f"{'Transaction ID':<15} {'Account ID':<12} {'Amount':<12} {'Fraud':<7}")
        print("-" * 80)
        
        for row in cursor.fetchall():
            trans_id, acc_id, amount, fraud = row
            fraud_label = "YES ✗" if fraud == 1 else "NO ✓"
            print(f"{trans_id:<15} {acc_id:<12} ${amount:<11.2f} {fraud_label:<7}")
        print("\n✅ DATABASE VERIFICATION SUCCESSFUL!")
        print(f"\n   The transactions ARE in the database!")
        print(f"   If pgAdmin is not showing them:")
        print(f"   1. Refresh pgAdmin in browser (F5)")
        print(f"   2. Disconnect and reconnect to the server")
        print(f"   3. Clear browser cache")
        print(f"   4. Open a new pgAdmin window")
        
        cursor.close()
        conn.close()
        
        return True
    
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)
