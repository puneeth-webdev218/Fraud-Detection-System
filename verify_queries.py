#!/usr/bin/env python
"""Run analytical queries to verify database setup"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.db_connection import DatabaseConnection

def run_query(query_name, sql_query):
    """Run a query and display results"""
    print("\n" + "="*80)
    print(f"📊 {query_name}")
    print("="*80)
    
    try:
        db = DatabaseConnection()
        if db.connect():
            # Execute query
            db.execute(sql_query)
            results = db.fetchall()
            
            if results:
                # Get column names from cursor description
                columns = [desc[0] for desc in db.cursor.description]
                
                # Create DataFrame for nice display
                df = pd.DataFrame(results, columns=columns)
                
                print(f"\n✅ Query returned {len(df)} rows\n")
                print(df.to_string())
                print(f"\nColumns: {', '.join(columns)}")
            else:
                print("\n⚠️  No results found (tables are empty)")
                print("This is normal if you haven't inserted data yet.")
            
            db.disconnect()
            return True
        else:
            print("❌ Failed to connect to database")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run test queries"""
    print("\n" + "🔍 " * 20)
    print("FRAUD DETECTION DATABASE - QUERY VERIFICATION")
    print("🔍 " * 20)
    
    # Query 1: Simple table count
    query1 = """
    SELECT 
        'transactions' as table_name,
        COUNT(*) as row_count
    FROM transactions
    UNION ALL
    SELECT 
        'fraud_predictions' as table_name,
        COUNT(*) as row_count
    FROM fraud_predictions;
    """
    
    run_query("Query 1: Table Row Counts", query1)
    
    # Query 2: Transactions table structure
    query2 = """
    SELECT 
        column_name,
        data_type,
        is_nullable
    FROM information_schema.columns
    WHERE table_name = 'transactions'
    ORDER BY ordinal_position;
    """
    
    run_query("Query 2: Transactions Table Structure", query2)
    
    # Query 3: Fraud Predictions table structure
    query3 = """
    SELECT 
        column_name,
        data_type,
        is_nullable
    FROM information_schema.columns
    WHERE table_name = 'fraud_predictions'
    ORDER BY ordinal_position;
    """
    
    run_query("Query 3: Fraud Predictions Table Structure", query3)
    
    # Query 4: Database indexes
    query4 = """
    SELECT 
        tablename,
        indexname,
        indexdef
    FROM pg_indexes
    WHERE schemaname = 'public'
    ORDER BY tablename, indexname;
    """
    
    run_query("Query 4: Database Indexes", query4)
    
    # Query 5: Sample transactions (if any exist)
    query5 = """
    SELECT * FROM transactions LIMIT 5;
    """
    
    run_query("Query 5: Sample Transactions (First 5 rows)", query5)
    
    print("\n" + "="*80)
    print("✅ Query verification complete!")
    print("="*80)
    print("\nNext steps:")
    print("1. Insert sample data: python database_integration_example.py")
    print("2. Run analytical queries: python run_queries.py")
    print("3. View in pgAdmin: http://localhost:5050")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
