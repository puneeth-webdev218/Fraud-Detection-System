"""
Create Tables in PostgreSQL Database
Run this once to set up the database schema
"""

import psycopg2
from psycopg2 import Error
import os
from dotenv import load_dotenv

load_dotenv()

def create_tables():
    """Create all required tables in PostgreSQL"""
    
    # Get database credentials
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', 5432)
    database = os.getenv('DB_NAME', 'fraud_detection')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', '')
    
    print("\n" + "="*60)
    print("Creating Database Tables")
    print("="*60 + "\n")
    
    try:
        connection = psycopg2.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password
        )
        
        cursor = connection.cursor()
        
        # 1. Transactions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id VARCHAR PRIMARY KEY,
            account_id VARCHAR NOT NULL,
            merchant_id VARCHAR NOT NULL,
            device_id VARCHAR,
            amount FLOAT,
            timestamp VARCHAR,
            is_fraud INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(transaction_id)
        );
        """)
        print("✔ Created 'transactions' table")
        
        # 2. Accounts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id VARCHAR PRIMARY KEY,
            risk_score FLOAT DEFAULT 0,
            fraud_flag INT DEFAULT 0,
            email_domain VARCHAR,
            country VARCHAR,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        print("✔ Created 'accounts' table")
        
        # 3. Merchants table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS merchants (
            merchant_id VARCHAR PRIMARY KEY,
            category VARCHAR,
            fraud_rate FLOAT DEFAULT 0,
            risk_level VARCHAR,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        print("✔ Created 'merchants' table")
        
        # 4. Devices table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            device_id VARCHAR PRIMARY KEY,
            device_type VARCHAR,
            is_shared INT DEFAULT 0,
            fraud_rate FLOAT DEFAULT 0,
            total_users INT DEFAULT 1,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        print("✔ Created 'devices' table")
        
        # 5. Fraud Predictions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fraud_predictions (
            prediction_id SERIAL PRIMARY KEY,
            transaction_id VARCHAR NOT NULL,
            fraud_probability FLOAT,
            fraud_flag INT,
            model_name VARCHAR DEFAULT 'GNN',
            confidence FLOAT,
            created_at TIMESTAMP DEFAULT NOW(),
            FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
        );
        """)
        print("✔ Created 'fraud_predictions' table")
        
        # 6. Create indexes for faster queries
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transaction_fraud 
        ON transactions(is_fraud);
        """)
        print("✔ Created index on transactions.is_fraud")
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_prediction_fraud 
        ON fraud_predictions(fraud_flag);
        """)
        print("✔ Created index on fraud_predictions.fraud_flag")
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_account_risk 
        ON accounts(risk_score);
        """)
        print("✔ Created index on accounts.risk_score")
        
        # Commit changes
        connection.commit()
        
        print("\n" + "="*60)
        print("✔ All tables created successfully!")
        print("="*60 + "\n")
        
        # Show summary
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print("Tables created:")
        for table in tables:
            print(f"  • {table[0]}")
        
        cursor.close()
        connection.close()
        
        return True
    
    except Error as e:
        print(f"✗ Error creating tables: {e}")
        return False
    
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = create_tables()
    exit(0 if success else 1)
