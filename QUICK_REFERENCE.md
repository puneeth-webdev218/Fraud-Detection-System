# Dynamic Fraud Detection - Quick Reference Card

## 🚀 Start Here

### 3 Ways to Use:

#### Option 1: Interactive Menu (Easiest)
```bash
python quickstart_interactive.py
```
→ Choose from menu → Load data → View results

#### Option 2: Command Line (Fastest)
```bash
python dynamic_fraud_loader.py --rows 1000
```
→ Specify count → Auto-loads → Shows statistics

#### Option 3: Program (Most Flexible)
```python
from dynamic_fraud_loader import DynamicFraudDetectionPipeline
pipeline = DynamicFraudDetectionPipeline()
pipeline.run(num_rows=1000)
```

---

## 📋 Common Tasks

### Load 100 Transactions
```bash
python dynamic_fraud_loader.py --rows 100
```

### Load 1000 Transactions
```bash
python dynamic_fraud_loader.py --rows 1000
```

### Load 5000 Transactions
```bash
python dynamic_fraud_loader.py --rows 5000
```

### Use Custom Dataset
```bash
python dynamic_fraud_loader.py --rows 1000 --dataset path/to/data.csv
```

---

## 🗄️ View Results in pgAdmin

1. Open: **http://localhost:5050**
2. Navigate: **Servers → PostgreSQL → fraud_detection → Tables → transactions**
3. Right-click → **View/Edit Data**

Or run queries:
```sql
-- See all transactions
SELECT * FROM transactions LIMIT 20;

-- Fraud summary
SELECT fraud_flag, COUNT(*) FROM transactions GROUP BY fraud_flag;

-- High-risk transactions
SELECT * FROM transactions WHERE amount > 1000 ORDER BY amount DESC;
```

---

## 📊 What Happens

```
Input: N transactions
  ↓
Load from dataset
  ↓
Run fraud detection
  ↓
Insert to PostgreSQL
  ↓
Display: ✔ Database updated — view in pgAdmin
```

---

## ⚡ Expected Performance

| Rows | Time |
|------|------|
| 100  | ~0.2s |
| 500  | ~0.3s |
| 1000 | ~0.6s |
| 5000 | ~2.7s |

---

## ✅ Database Schema

```
Table: transactions
├─ transaction_id (BIGINT) - Unique ID
├─ account_id (INTEGER) - Account reference
├─ merchant_id (INTEGER) - Merchant reference
├─ device_id (INTEGER) - Device reference
├─ amount (DECIMAL) - Transaction amount
├─ timestamp (TIMESTAMP) - When occurred
├─ fraud_flag (INTEGER) - 0=legitimate, 1=fraud
└─ processed_at (TIMESTAMP) - When inserted
```

**Indexes**: fraud_flag, account_id, timestamp, amount

---

## 🔧 Configuration

Edit `.env`:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fraud_detection
DB_USER=postgres
DB_PASSWORD=your_password
```

---

## ❌ Troubleshooting

**Error: "Connection failed"**
- Check PostgreSQL is running
- Verify .env has correct credentials
- Test: `psql -h localhost -U postgres`

**Error: "Dataset not found"**
- Ensure `data/raw/train_transaction.csv` exists
- Or use `--dataset` flag with correct path

**Error: "Permission denied"**
- Update DB_USER and DB_PASSWORD in .env
- Ensure user has database access

---

## 📚 Documentation

- **DYNAMIC_LOADING_GUIDE.md** - Complete guide
- **DYNAMIC_LOADING_README.md** - Quick start
- **dynamic_fraud_loader.py** - Source code
- **quickstart_interactive.py** - Interactive menu

---

## 💡 Pro Tips

✅ Start with 100 transactions first
✅ Re-run same count - duplicates are skipped safely
✅ Load different counts to see trends
✅ Use pgAdmin to explore the data
✅ Schedule regular loads with Task Scheduler

---

## 🎯 Next Steps

1. `python quickstart_interactive.py` - Run interactive menu
2. Select option 2 - Custom load
3. Enter: `1000`
4. Wait for "✔ Database updated — view in pgAdmin"
5. Open pgAdmin and explore!

---

**Status**: ✅ Production Ready
**Version**: 1.0.0
**Last Updated**: 2025-11-30
