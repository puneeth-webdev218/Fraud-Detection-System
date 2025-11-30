#!/usr/bin/env python
"""
Complete Fraud Detection Database Setup
Creates all tables with sample data and indexes
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def create_all_tables():
    """Create all tables and insert sample data"""
    print("\n" + "=" * 80)
    print("🔧 COMPLETE FRAUD DETECTION DATABASE SETUP")
    print("=" * 80)
    
    try:
        from src.database.db_connection import DatabaseConnection
        
        db = DatabaseConnection()
        if not db.connect():
            print("❌ Connection failed!")
            return False
        
        print("\n✅ Connected to PostgreSQL")
        
        # List of all SQL statements
        sql_statements = [
            # 1. CREATE ACCOUNT TABLE
            """
            CREATE TABLE IF NOT EXISTS account (
                account_id SERIAL PRIMARY KEY,
                email_domain VARCHAR(255),
                country VARCHAR(100),
                risk_score FLOAT DEFAULT 0.0,
                fraud_flag BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # 2. CREATE MERCHANT TABLE
            """
            CREATE TABLE IF NOT EXISTS merchant (
                merchant_id SERIAL PRIMARY KEY,
                merchant_name VARCHAR(255),
                merchant_category VARCHAR(100),
                country VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # 3. CREATE DEVICE TABLE
            """
            CREATE TABLE IF NOT EXISTS device (
                device_id SERIAL PRIMARY KEY,
                device_type VARCHAR(100),
                risk_score FLOAT DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # 4. CREATE TRANSACTION TABLE
            """
            CREATE TABLE IF NOT EXISTS transaction (
                transaction_id SERIAL PRIMARY KEY,
                account_id INTEGER REFERENCES account(account_id) ON DELETE CASCADE,
                merchant_id INTEGER REFERENCES merchant(merchant_id) ON DELETE CASCADE,
                device_id INTEGER REFERENCES device(device_id) ON DELETE CASCADE,
                transaction_amount DECIMAL(12, 2),
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                transaction_hour INTEGER,
                is_fraud BOOLEAN DEFAULT FALSE,
                card_type VARCHAR(50),
                card_category VARCHAR(50),
                addr_country VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # 5. CREATE SHARED_DEVICE TABLE
            """
            CREATE TABLE IF NOT EXISTS shared_device (
                shared_device_id SERIAL PRIMARY KEY,
                device_id INTEGER REFERENCES device(device_id) ON DELETE CASCADE,
                account_id INTEGER REFERENCES account(account_id) ON DELETE CASCADE,
                transaction_count INTEGER DEFAULT 0,
                fraud_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # CREATE INDEXES
            "CREATE INDEX IF NOT EXISTS idx_account_risk_score ON account(risk_score);",
            "CREATE INDEX IF NOT EXISTS idx_account_fraud_flag ON account(fraud_flag);",
            "CREATE INDEX IF NOT EXISTS idx_account_country ON account(country);",
            "CREATE INDEX IF NOT EXISTS idx_merchant_category ON merchant(merchant_category);",
            "CREATE INDEX IF NOT EXISTS idx_merchant_country ON merchant(country);",
            "CREATE INDEX IF NOT EXISTS idx_device_type ON device(device_type);",
            "CREATE INDEX IF NOT EXISTS idx_device_risk ON device(risk_score);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_account_id ON transaction(account_id);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_merchant_id ON transaction(merchant_id);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_device_id ON transaction(device_id);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_is_fraud ON transaction(is_fraud);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_date ON transaction(transaction_date);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_hour ON transaction(transaction_hour);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_country ON transaction(addr_country);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_card_type ON transaction(card_type);",
            "CREATE INDEX IF NOT EXISTS idx_shared_device_device_id ON shared_device(device_id);",
            "CREATE INDEX IF NOT EXISTS idx_shared_device_account_id ON shared_device(account_id);",
        ]
        
        print("\n📋 Creating Tables...")
        for stmt in sql_statements:
            try:
                db.execute(stmt)
                db.commit()
            except Exception as e:
                if 'already exists' not in str(e).lower():
                    print(f"⚠️  {str(e)[:80]}")
        
        print("   ✅ All tables created successfully!")
        
        # INSERT SAMPLE DATA
        print("\n📝 Inserting Sample Data...")
        
        # Account Data
        account_data = [
            ('gmail.com', 'USA', 0.2, False),
            ('yahoo.com', 'UK', 0.5, False),
            ('hotmail.com', 'USA', 0.8, True),
            ('outlook.com', 'Canada', 0.3, False),
            ('protonmail.com', 'Germany', 0.9, True),
            ('aol.com', 'USA', 0.4, False),
            ('icloud.com', 'USA', 0.1, False),
            ('yandex.com', 'Russia', 0.7, True),
            ('qq.com', 'China', 0.6, False),
            ('163.com', 'China', 0.5, False),
            ('mail.com', 'India', 0.4, False),
            ('rediffmail.com', 'India', 0.6, False),
            ('live.com', 'USA', 0.3, False),
            ('me.com', 'USA', 0.2, False),
            ('zoho.com', 'USA', 0.5, False),
        ]
        
        for email, country, risk, fraud in account_data:
            sql = """
                INSERT INTO account (email_domain, country, risk_score, fraud_flag)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """
            db.execute(sql, (email, country, risk, fraud))
        db.commit()
        print("   ✅ Inserted 15 accounts")
        
        # Merchant Data
        merchant_data = [
            ('Amazon', 'E-commerce', 'USA'),
            ('Walmart', 'Retail', 'USA'),
            ('Best Buy', 'Electronics', 'USA'),
            ('Target', 'Retail', 'USA'),
            ('eBay', 'E-commerce', 'USA'),
            ('Alibaba', 'E-commerce', 'China'),
            ('Flipkart', 'E-commerce', 'India'),
            ('Netflix', 'Streaming', 'USA'),
            ('Spotify', 'Music', 'USA'),
            ('PayPal', 'Payment', 'USA'),
            ('Apple Store', 'Electronics', 'USA'),
            ('Google Play', 'Digital', 'USA'),
            ('Microsoft Store', 'Software', 'USA'),
            ('Steam', 'Gaming', 'USA'),
            ('Uber', 'Transportation', 'USA'),
        ]
        
        for name, category, country in merchant_data:
            sql = """
                INSERT INTO merchant (merchant_name, merchant_category, country)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING;
            """
            db.execute(sql, (name, category, country))
        db.commit()
        print("   ✅ Inserted 15 merchants")
        
        # Device Data
        device_data = [
            ('Mobile', 0.3),
            ('Desktop', 0.2),
            ('Tablet', 0.4),
            ('Unknown', 0.9),
            ('Laptop', 0.25),
            ('VPN', 0.85),
            ('Proxy', 0.90),
            ('TOR', 0.95),
            ('iPhone', 0.15),
            ('Android', 0.35),
        ]
        
        for dtype, risk in device_data:
            sql = """
                INSERT INTO device (device_type, risk_score)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING;
            """
            db.execute(sql, (dtype, risk))
        db.commit()
        print("   ✅ Inserted 10 devices")
        
        # Transaction Data
        transaction_data = [
            (1, 1, 1, 99.99, 14, False, 'Visa', 'Credit', 'USA'),
            (2, 2, 2, 50.00, 10, False, 'Mastercard', 'Debit', 'UK'),
            (3, 3, 3, 1500.00, 3, True, 'Visa', 'Credit', 'USA'),
            (4, 4, 1, 200.00, 22, False, 'Amex', 'Credit', 'Canada'),
            (5, 5, 4, 5000.00, 2, True, 'Visa', 'Credit', 'Germany'),
            (1, 2, 2, 75.50, 18, False, 'Mastercard', 'Debit', 'USA'),
            (2, 3, 1, 300.00, 11, False, 'Visa', 'Credit', 'UK'),
            (3, 4, 3, 2000.00, 4, True, 'Amex', 'Credit', 'USA'),
            (4, 5, 2, 150.00, 20, False, 'Visa', 'Debit', 'Canada'),
            (5, 1, 4, 8000.00, 1, True, 'Mastercard', 'Credit', 'Germany'),
            (6, 6, 1, 45.99, 15, False, 'Visa', 'Credit', 'USA'),
            (7, 7, 2, 120.00, 12, False, 'Mastercard', 'Debit', 'USA'),
            (8, 8, 3, 15.99, 19, False, 'Visa', 'Credit', 'Russia'),
            (9, 9, 1, 9.99, 9, False, 'Mastercard', 'Debit', 'China'),
            (10, 10, 2, 25.00, 17, False, 'Visa', 'Credit', 'China'),
            (11, 11, 5, 89.99, 16, False, 'Visa', 'Credit', 'USA'),
            (12, 12, 6, 29.99, 13, True, 'Mastercard', 'Debit', 'USA'),
            (13, 13, 7, 199.99, 8, True, 'Amex', 'Credit', 'USA'),
            (14, 14, 8, 49.99, 21, False, 'Visa', 'Debit', 'USA'),
            (15, 15, 9, 35.00, 6, False, 'Mastercard', 'Credit', 'India'),
        ]
        
        for acc, mer, dev, amt, hour, fraud, card, cat, country in transaction_data:
            sql = """
                INSERT INTO transaction (account_id, merchant_id, device_id, transaction_amount, 
                                       transaction_hour, is_fraud, card_type, card_category, addr_country)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """
            db.execute(sql, (acc, mer, dev, amt, hour, fraud, card, cat, country))
        db.commit()
        print("   ✅ Inserted 20 transactions")
        
        # Shared Device Data
        shared_device_data = [
            (1, 1, 10, 0),
            (1, 3, 5, 2),
            (2, 2, 8, 1),
            (3, 4, 12, 0),
            (4, 5, 3, 3),
            (1, 6, 7, 0),
            (2, 7, 6, 0),
            (3, 8, 9, 1),
            (1, 9, 4, 0),
            (2, 10, 5, 0),
            (5, 11, 6, 1),
            (6, 12, 4, 2),
            (7, 13, 5, 1),
            (8, 14, 8, 0),
            (9, 15, 3, 0),
        ]
        
        for dev, acc, trans_count, fraud_count in shared_device_data:
            sql = """
                INSERT INTO shared_device (device_id, account_id, transaction_count, fraud_count)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """
            db.execute(sql, (dev, acc, trans_count, fraud_count))
        db.commit()
        print("   ✅ Inserted 15 shared device records")
        
        # GET STATISTICS
        print("\n📊 Database Summary:")
        
        tables = ['account', 'merchant', 'device', 'transaction', 'shared_device']
        for table in tables:
            db.execute(f"SELECT COUNT(*) FROM {table};")
            count = db.fetchone()[0]
            print(f"   • {table:20} : {count:3d} rows")
        
        db.disconnect()
        
        print("\n" + "=" * 80)
        print("✅ DATABASE SETUP COMPLETE!")
        print("=" * 80)
        print("\n🎯 Next Steps:")
        print("   1. Open pgAdmin: http://localhost:5050")
        print("   2. Navigate to: fraud_detection → Schemas → public → Tables")
        print("   3. You should see all 5 tables with data:")
        print("      • account (15 rows)")
        print("      • merchant (15 rows)")
        print("      • device (10 rows)")
        print("      • transaction (20 rows)")
        print("      • shared_device (15 rows)")
        print("\n4. Run analytical queries from analytical_queries.sql")
        print("=" * 80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = create_all_tables()
    sys.exit(0 if success else 1)
