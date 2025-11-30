# Dynamic Fraud Detection Pipeline Guide

## Overview

The Dynamic Fraud Detection Pipeline allows you to load any number of transactions from the dataset, run fraud detection analysis, and automatically insert the results into PostgreSQL. The pipeline is interactive, efficient, and production-ready.

## Features

✅ **Dynamic Loading**: Load 100, 1000, 5000, or any number of transactions
✅ **Automatic Fraud Detection**: Fraud prediction runs on loaded data
✅ **PostgreSQL Integration**: Automatic table creation and data insertion
✅ **Duplicate Handling**: ON CONFLICT support - safe to re-run
✅ **Performance Optimized**: Bulk insertion in 1000-row batches
✅ **Real-time Feedback**: Detailed progress logs and statistics
✅ **pgAdmin Ready**: View results immediately in pgAdmin interface

## Quick Start

### Method 1: Interactive Mode (Recommended)

```bash
python dynamic_fraud_loader.py
```

This will prompt you to enter the number of transactions:

```
================================================================================
DYNAMIC TRANSACTION LOADER
================================================================================

How many transactions would you like to load?
Enter a number (e.g., 100, 1000, 10000):

> 1000
```

### Method 2: Command Line with Specific Count

```bash
# Load 500 transactions
python dynamic_fraud_loader.py --rows 500

# Load 10,000 transactions
python dynamic_fraud_loader.py --rows 10000

# Load from custom dataset
python dynamic_fraud_loader.py --rows 1000 --dataset data/raw/custom_transactions.csv
```

## Usage Examples

### Example 1: Load 1000 Transactions

```bash
$ python dynamic_fraud_loader.py --rows 1000

================================================================================
DYNAMIC FRAUD DETECTION PIPELINE
================================================================================

📊 Loading 1,000 transactions from dataset...
✓ Loaded 1,000 transactions
  ├─ Fraud cases: 21
  ├─ Amount range: $1.90 - $3,247.91
  └─ Avg amount: $152.41

🔍 Processing transactions for fraud detection...
✓ Processed 1,000 transactions
  ├─ Fraud cases: 21
  ├─ Fraud rate: 2.10%
  └─ Ready for database insertion

🗄️  Connecting to PostgreSQL database...
✓ Connected to PostgreSQL

📋 Setting up database table...
✓ Transactions table ready

📥 Inserting transactions into database...
✓ Database updated successfully!
  ├─ Inserted: 1,000
  └─ Skipped:  0

📊 Database Statistics:
  ├─ Total transactions: 1,025
  ├─ Fraudulent cases: 23
  ├─ Fraud rate: 2.24%
  ├─ Avg amount: $152.35
  ├─ Min amount: $1.90
  └─ Max amount: $3,247.91

================================================================================
✅ PIPELINE COMPLETED SUCCESSFULLY!
================================================================================

✔ Database updated — view in pgAdmin

  Open pgAdmin: http://localhost:5050
  Query: SELECT * FROM transactions LIMIT 10;
  Expected rows: 1,025

================================================================================
```

### Example 2: Run with Different Datasets

```bash
# Use custom dataset path
python dynamic_fraud_loader.py --rows 500 --dataset data/raw/ieee_fraud_2024.csv
```

## Database Schema

The pipeline automatically creates a `transactions` table with the following structure:

```sql
CREATE TABLE transactions (
    transaction_id BIGINT PRIMARY KEY,
    account_id INTEGER,
    merchant_id INTEGER,
    device_id INTEGER,
    amount DECIMAL(10,2),
    timestamp TIMESTAMP,
    fraud_flag INTEGER (0=legitimate, 1=fraudulent),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Performance Indexes

The following indexes are automatically created for optimal query performance:

```sql
CREATE INDEX idx_transactions_fraud ON transactions(fraud_flag);
CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX idx_transactions_amount ON transactions(amount);
```

## Workflow

```
User Input (e.g., 1000)
    ↓
📊 Load 1000 rows from dataset
    ↓
🔍 Process & Fraud Detection
    ↓
🗄️  Connect to PostgreSQL
    ↓
📋 Create transactions table (if not exists)
    ↓
📥 Bulk insert 1000 transactions
    ↓
✅ Display Statistics
    ↓
✔ Database updated — view in pgAdmin
```

## Configuration

### Environment Variables

The pipeline reads database credentials from your `.env` file:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fraud_detection
DB_USER=postgres
DB_PASSWORD=your_password
```

### Command Line Arguments

```bash
python dynamic_fraud_loader.py [--rows NUM] [--dataset PATH]

Options:
  --rows NUM          Number of transactions to load (default: prompt user)
  --dataset PATH      Path to CSV dataset (default: data/raw/train_transaction.csv)
  --help              Show help message
```

## API Usage (Programmatic)

You can also use the pipeline programmatically in your own code:

```python
from dynamic_fraud_loader import DynamicFraudDetectionPipeline

# Create pipeline instance
pipeline = DynamicFraudDetectionPipeline()

# Run with 5000 transactions
success = pipeline.run(num_rows=5000)

if success:
    print("✔ Transactions inserted successfully!")
```

### Advanced Usage

```python
from dynamic_fraud_loader import DynamicFraudDetectionPipeline
from src.database.dynamic_postgres_manager import PostgreSQLManager

# Create pipeline
pipeline = DynamicFraudDetectionPipeline()

# Load transactions
df = pipeline.load_transactions(1000)

# Process for fraud detection
processed_df = pipeline.process_transactions(df)

# Connect and insert manually
pipeline.connect_database()
pipeline.setup_database()
inserted, skipped = pipeline.insert_to_database()

# Get statistics
pipeline.show_database_stats()

# Cleanup
pipeline.disconnect()
```

## View Results in pgAdmin

Once the pipeline completes successfully:

1. **Open pgAdmin**: http://localhost:5050
2. **Navigate to**: Servers → PostgreSQL → fraud_detection → Schemas → public → Tables
3. **View transactions table**: Right-click → View Data
4. **Run custom queries**:

```sql
-- Total transactions by fraud status
SELECT fraud_flag, COUNT(*) as count FROM transactions GROUP BY fraud_flag;

-- High-risk transactions (amount > $1000)
SELECT * FROM transactions WHERE amount > 1000 ORDER BY amount DESC;

-- Fraud statistics
SELECT 
    COUNT(*) as total,
    SUM(fraud_flag) as fraud_count,
    ROUND(AVG(fraud_flag) * 100, 2) as fraud_rate
FROM transactions;

-- Recent transactions
SELECT * FROM transactions ORDER BY processed_at DESC LIMIT 10;
```

## Performance Metrics

| Rows | Load Time | Process Time | Insert Time | Total Time |
|------|-----------|--------------|-------------|-----------|
| 500  | 0.03s     | 0.02s        | 0.25s       | 0.30s     |
| 1000 | 0.04s     | 0.03s        | 0.50s       | 0.57s     |
| 2000 | 0.05s     | 0.03s        | 1.00s       | 1.08s     |
| 5000 | 0.12s     | 0.07s        | 2.50s       | 2.69s     |

*Times are approximate and may vary based on system performance*

## Duplicate Handling

The pipeline uses `ON CONFLICT (transaction_id) DO NOTHING` to handle duplicates:

- **First Run**: 1000 transactions inserted
- **Second Run (same 1000)**: 0 new inserted, 1000 skipped
- **No errors**: Safe to re-run without data corruption

```
📥 Inserting transactions into database...
✓ Insertion complete: 1000 inserted, 500 skipped
```

## Troubleshooting

### Issue: Connection Failed

**Error**: `✗ Connection failed: could not connect to server`

**Solution**:
1. Verify PostgreSQL is running: `psql --version`
2. Check `.env` file has correct credentials
3. Verify database exists: `psql -l`

```bash
# Quick check
psql -h localhost -U postgres -d fraud_detection -c "SELECT 1;"
```

### Issue: Insufficient Permissions

**Error**: `✗ Connection failed: permission denied for user`

**Solution**: Update `.env` with correct database user:

```bash
DB_USER=postgres
DB_PASSWORD=your_actual_password
```

### Issue: Out of Disk Space

**Error**: `✗ Insertion failed: disk full`

**Solution**: Clean up old data or expand disk space:

```sql
-- Archive old transactions (before date)
CREATE TABLE transactions_archive AS 
SELECT * FROM transactions WHERE processed_at < '2024-01-01';

DELETE FROM transactions WHERE processed_at < '2024-01-01';
```

### Issue: Dataset Not Found

**Error**: `✗ Dataset not found: data/raw/train_transaction.csv`

**Solution**: Verify file path:

```bash
# Check if file exists
ls -la data/raw/train_transaction.csv

# Use absolute path if needed
python dynamic_fraud_loader.py --rows 1000 --dataset C:/path/to/dataset.csv
```

## Best Practices

1. **Start Small**: Test with 100-500 transactions first
2. **Monitor Disk Space**: Large datasets may require significant storage
3. **Schedule Runs**: Use task scheduler for regular updates
4. **Backup Data**: Regular backups before major operations
5. **Verify Results**: Always check pgAdmin after insertion
6. **Use Indexes**: Query performance improves with indexes
7. **Clean Old Data**: Archive historical data periodically

## Advanced Configuration

### Custom Column Mapping

If your dataset has different column names:

```python
from src.database.dynamic_postgres_manager import PostgreSQLManager

manager = PostgreSQLManager()
manager.connect()
manager.create_transactions_table()

# Map your columns to database schema
column_mapping = {
    'id': 'transaction_id',
    'user_id': 'account_id',
    'store_id': 'merchant_id',
    'device': 'device_id',
    'transaction_amount': 'amount',
    'timestamp': 'timestamp',
    'is_fraudulent': 'fraud_flag'
}

inserted, skipped = manager.insert_transactions_batch(df, column_mapping)
```

### Batch Size Configuration

For very large datasets, adjust batch size in `dynamic_postgres_manager.py`:

```python
# In insert_transactions_batch method
batch_size = 5000  # Change from 1000 to 5000
```

## Integration with Other Systems

### Export Results

```sql
-- Export to CSV
COPY (SELECT * FROM transactions) 
TO '/tmp/transactions_export.csv' WITH CSV HEADER;
```

### Connect to Analytics Tools

```python
import psycopg2
import pandas as pd

conn = psycopg2.connect("dbname=fraud_detection user=postgres")
df = pd.read_sql("SELECT * FROM transactions", conn)

# Now use df for analytics, machine learning, etc.
```

## Support & Documentation

- **GitHub Issues**: Report bugs or request features
- **Documentation**: See `DYNAMIC_LOADING_GUIDE.md`
- **Examples**: Check `examples/` directory
- **API Docs**: See docstrings in `dynamic_postgres_manager.py`

## License

This project is licensed under MIT License. See LICENSE file for details.

---

**Last Updated**: 2025-11-30
**Version**: 1.0.0
**Status**: Production Ready ✅
