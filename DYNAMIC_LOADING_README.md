# Dynamic Fraud Detection - New Feature

## What's New? 🚀

The fraud detection project now supports **dynamic transaction loading**! Load any number of transactions (100, 1000, 5000, etc.) and automatically insert them into PostgreSQL with fraud detection.

## Quick Start - 3 Ways to Use

### 1️⃣ Interactive Mode (Easiest)

```bash
python quickstart_interactive.py
```

Provides a menu-driven interface to:
- Run demo with 100 transactions
- Load custom number
- View database statistics
- Access documentation

### 2️⃣ Direct Command Line

```bash
# Load 1000 transactions
python dynamic_fraud_loader.py --rows 1000

# Load 5000 transactions
python dynamic_fraud_loader.py --rows 5000
```

### 3️⃣ Programmatic (Python Code)

```python
from dynamic_fraud_loader import DynamicFraudDetectionPipeline

pipeline = DynamicFraudDetectionPipeline()
pipeline.run(num_rows=1000)
```

## What Happens?

```
✅ Load N transactions from dataset
✅ Run fraud detection analysis
✅ Connect to PostgreSQL
✅ Create transactions table (if needed)
✅ Bulk insert all N transactions
✅ Show statistics
✅ "✔ Database updated — view in pgAdmin"
```

## Example Output

```
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

🗄️  Connecting to PostgreSQL database...
✓ Connected to PostgreSQL

📋 Setting up database table...
✓ Transactions table ready

📥 Inserting transactions into database...
✓ Insertion complete: 1,000 inserted, 0 skipped

📊 Database Statistics:
  ├─ Total transactions: 1,025
  ├─ Fraudulent cases: 23
  ├─ Fraud rate: 2.24%
  ├─ Avg amount: $152.35

✅ PIPELINE COMPLETED SUCCESSFULLY!

✔ Database updated — view in pgAdmin
```

## Files Created

| File | Purpose |
|------|---------|
| `dynamic_fraud_loader.py` | Main CLI script for loading transactions |
| `quickstart_interactive.py` | Interactive menu-driven interface |
| `src/database/dynamic_postgres_manager.py` | PostgreSQL connection and insertion logic |
| `DYNAMIC_LOADING_GUIDE.md` | Complete documentation |

## Key Features

✅ **Dynamic Loading**: Load ANY number of transactions (100, 1000, 10000, etc.)
✅ **Automatic Fraud Detection**: Runs on loaded data
✅ **PostgreSQL Integration**: Direct database insertion
✅ **Duplicate Handling**: ON CONFLICT - safe to re-run
✅ **Performance Optimized**: Bulk insertion in 1000-row batches
✅ **Real-time Feedback**: Progress logs and statistics
✅ **pgAdmin Ready**: View results immediately
✅ **No Manual Steps**: Fully automated

## Database Schema

Automatically creates `transactions` table:

```sql
CREATE TABLE transactions (
    transaction_id BIGINT PRIMARY KEY,
    account_id INTEGER,
    merchant_id INTEGER,
    device_id INTEGER,
    amount DECIMAL(10,2),
    timestamp TIMESTAMP,
    fraud_flag INTEGER (0=legitimate, 1=fraud),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Plus 4 performance indexes for fast queries.

## View Results in pgAdmin

1. Open: http://localhost:5050
2. Navigate: Servers → PostgreSQL → fraud_detection → Tables
3. Right-click `transactions` table → View Data
4. See all loaded transactions with fraud predictions

## Common Commands

```bash
# Interactive menu
python quickstart_interactive.py

# Load 500 transactions
python dynamic_fraud_loader.py --rows 500

# Load 2000 transactions
python dynamic_fraud_loader.py --rows 2000

# Custom dataset
python dynamic_fraud_loader.py --rows 1000 --dataset data/raw/custom.csv
```

## SQL Queries to Try

```sql
-- Total fraud summary
SELECT fraud_flag, COUNT(*) FROM transactions GROUP BY fraud_flag;

-- High-risk transactions
SELECT * FROM transactions WHERE amount > 1000 ORDER BY amount DESC;

-- Recent transactions
SELECT * FROM transactions ORDER BY processed_at DESC LIMIT 10;

-- Fraud rate by account
SELECT account_id, 
       COUNT(*) as total,
       SUM(fraud_flag) as fraud_count,
       ROUND(AVG(fraud_flag) * 100, 2) as fraud_rate
FROM transactions
GROUP BY account_id
HAVING SUM(fraud_flag) > 0
ORDER BY fraud_rate DESC;
```

## Configuration

Edit your `.env` file:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fraud_detection
DB_USER=postgres
DB_PASSWORD=your_password
```

## Performance

| Rows | Total Time |
|------|-----------|
| 500  | ~0.3s     |
| 1000 | ~0.6s     |
| 2000 | ~1.1s     |
| 5000 | ~2.7s     |

*Approximate times - varies by system*

## FAQ

**Q: Can I load the same transactions twice?**
A: Yes! The pipeline uses ON CONFLICT handling - duplicates are skipped automatically.

**Q: Can I use a different dataset?**
A: Yes! Use the `--dataset` parameter with any CSV file.

**Q: How do I view the data?**
A: Open pgAdmin at http://localhost:5050 and browse the transactions table.

**Q: Can I load millions of transactions?**
A: Yes, but may take longer. Start with smaller batches first.

**Q: What if something goes wrong?**
A: Check the error messages and your PostgreSQL connection. See DYNAMIC_LOADING_GUIDE.md for troubleshooting.

## Next Steps

1. ✅ Run interactive script: `python quickstart_interactive.py`
2. ✅ Load your first batch of transactions
3. ✅ View results in pgAdmin
4. ✅ Run SQL queries to analyze fraud
5. ✅ Schedule regular loads with Windows Task Scheduler

## Documentation

For complete details, see:
- **DYNAMIC_LOADING_GUIDE.md** - Complete guide with examples
- **dynamic_fraud_loader.py** - Source code with docstrings
- **src/database/dynamic_postgres_manager.py** - Database module API

## Support

If you encounter issues:
1. Check that PostgreSQL is running
2. Verify `.env` file has correct credentials
3. Ensure `data/raw/train_transaction.csv` exists
4. See DYNAMIC_LOADING_GUIDE.md troubleshooting section

---

**Status**: ✅ Production Ready
**Version**: 1.0.0
**Last Updated**: 2025-11-30
