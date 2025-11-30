#!/usr/bin/env python3
"""
Quick Start Example: Dynamic Fraud Detection Pipeline
Simple interactive script to get started with dynamic transaction loading
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dynamic_fraud_loader import DynamicFraudDetectionPipeline
import time


def print_banner():
    """Print welcome banner"""
    print("\n")
    print("█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  DYNAMIC FRAUD DETECTION PIPELINE - QUICK START".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    print()


def print_section(title):
    """Print section divider"""
    print("\n" + "─" * 80)
    print(f"  {title}")
    print("─" * 80 + "\n")


def get_user_choice():
    """Get user's choice for demo or custom load"""
    print_section("Choose an Option")
    
    print("1) Run Demo (load 100 transactions)")
    print("2) Load Custom Number (enter any amount)")
    print("3) View Database Statistics")
    print("4) View Documentation")
    print("5) Exit")
    print()
    
    choice = input("Enter choice (1-5): ").strip()
    return choice


def run_demo():
    """Run demo with 100 transactions"""
    print_section("Running Demo - 100 Transactions")
    
    pipeline = DynamicFraudDetectionPipeline()
    success = pipeline.run(100)
    
    if success:
        print("\n✨ Demo completed successfully!")
        print("\nNext Steps:")
        print("  1. Open pgAdmin: http://localhost:5050")
        print("  2. Query: SELECT * FROM transactions LIMIT 10")
        print("  3. Run custom queries on the transactions table")
    
    return success


def load_custom():
    """Load custom number of transactions"""
    print_section("Custom Transaction Load")
    
    while True:
        try:
            num_str = input("Enter number of transactions to load: ").strip()
            
            if not num_str.isdigit():
                print("❌ Please enter a valid number\n")
                continue
            
            num = int(num_str)
            
            if num <= 0:
                print("❌ Number must be greater than 0\n")
                continue
            
            if num > 1000000:
                print("\n⚠️  Large number detected. This may take a while.")
                confirm = input("Continue? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    continue
            
            break
        
        except KeyboardInterrupt:
            print("\n❌ Cancelled")
            return False
        except Exception as e:
            print(f"❌ Error: {e}\n")
    
    print(f"\nLoading {num:,} transactions...\n")
    
    pipeline = DynamicFraudDetectionPipeline()
    success = pipeline.run(num)
    
    if success:
        print("\n✨ Loading completed successfully!")
        print("\nNext Steps:")
        print(f"  1. Open pgAdmin: http://localhost:5050")
        print(f"  2. Check 'transactions' table has {num:,}+ new rows")
        print(f"  3. Run SQL queries to analyze fraud patterns")
    
    return success


def view_database_stats():
    """View current database statistics"""
    print_section("Database Statistics")
    
    try:
        from src.database.dynamic_postgres_manager import PostgreSQLManager
        
        manager = PostgreSQLManager()
        if not manager.connect():
            print("❌ Could not connect to database")
            print("   Please ensure PostgreSQL is running and .env is configured correctly")
            return
        
        total = manager.get_transaction_count()
        stats = manager.get_fraud_stats()
        
        print(f"  📊 Total Transactions:  {total:,}")
        print(f"  🚨 Fraudulent Cases:    {stats['fraud_count']:,}")
        print(f"  📈 Fraud Rate:          {stats['fraud_rate']:.2f}%")
        print(f"  💰 Average Amount:      ${stats['avg_amount']:.2f}")
        print(f"  💵 Min Amount:          ${stats['min_amount']:.2f}")
        print(f"  💴 Max Amount:          ${stats['max_amount']:.2f}")
        
        manager.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Make sure PostgreSQL is running and the fraud_detection database exists")


def view_documentation():
    """Display documentation preview"""
    print_section("Quick Reference Guide")
    
    print("""
COMMAND LINE USAGE:
  # Interactive mode
  python dynamic_fraud_loader.py
  
  # Load specific number
  python dynamic_fraud_loader.py --rows 1000
  
  # Custom dataset
  python dynamic_fraud_loader.py --rows 500 --dataset data/raw/custom.csv

DATABASE SCHEMA:
  Table: transactions
  ├─ transaction_id (BIGINT, PRIMARY KEY)
  ├─ account_id (INTEGER)
  ├─ merchant_id (INTEGER)
  ├─ device_id (INTEGER)
  ├─ amount (DECIMAL)
  ├─ timestamp (TIMESTAMP)
  ├─ fraud_flag (INTEGER: 0=legitimate, 1=fraud)
  └─ processed_at (TIMESTAMP)

USEFUL SQL QUERIES:
  # Fraud summary
  SELECT fraud_flag, COUNT(*) FROM transactions GROUP BY fraud_flag;
  
  # High-risk transactions
  SELECT * FROM transactions WHERE amount > 1000 ORDER BY amount DESC;
  
  # Recent activity
  SELECT * FROM transactions ORDER BY processed_at DESC LIMIT 20;

pgADMIN ACCESS:
  URL: http://localhost:5050
  Database: fraud_detection
  Server: PostgreSQL (localhost:5432)

FEATURES:
  ✅ Load any number of transactions
  ✅ Automatic fraud detection
  ✅ PostgreSQL integration
  ✅ Duplicate handling (ON CONFLICT)
  ✅ Performance optimized
  ✅ Real-time statistics

For complete documentation, see: DYNAMIC_LOADING_GUIDE.md
    """)


def main():
    """Main interactive loop"""
    print_banner()
    
    print("Welcome to the Dynamic Fraud Detection Pipeline!")
    print("This tool helps you load transactions and detect fraud in real-time.")
    print()
    
    while True:
        try:
            choice = get_user_choice()
            
            if choice == '1':
                run_demo()
            
            elif choice == '2':
                load_custom()
            
            elif choice == '3':
                view_database_stats()
            
            elif choice == '4':
                view_documentation()
            
            elif choice == '5':
                print("\n✨ Thank you for using Dynamic Fraud Detection Pipeline!")
                print("   For more info: https://github.com/your-repo/DRAGNN-FraudDB\n")
                break
            
            else:
                print("❌ Invalid choice. Please select 1-5.\n")
            
            input("\nPress Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\n✨ Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
