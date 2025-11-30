# Two-Phase Workflow: Quick Start Guide

## What Changed?

The system now uses **two separate database tables** instead of one:

```
BEFORE (Single Table):
┌─────────────────────┐
│  transactions       │
│  (with status)      │
└─────────────────────┘

AFTER (Dual Table):
┌──────────────────────┐      ┌────────────────────────┐
│  transactions        │      │  fraud_predictions     │
│  (7 columns)         │  →   │  (8 columns + status)  │
│  • No status         │      │  • WITH status column  │
└──────────────────────┘      └────────────────────────┘
   Phase 1: RAW DATA           Phase 2: PREDICTIONS
```

---

## How to Use

### Step 1: Load Data
```
Sidebar → Choose "Generate Demo Data" or "Load Real Dataset"
       → Input count (e.g., 1000 transactions)
       → Click the load button
```
Result: Data loaded into memory

### Step 2: Phase 1 - Load Raw Transactions
```
Sidebar → Click "📤 Load Transactions (Phase 1)"
```
What happens:
- ✅ Inserts data to `transactions` table (7 columns only)
- ✅ No status column yet
- ✅ Console shows: `"✅ PHASE 1 COMPLETE — X raw transactions stored"`

Check pgAdmin:
```
pgAdmin → Databases → postgres → Schemas → public → Tables → transactions
→ Right-click → "View/Edit Data" → First 100 rows
→ See: transaction_id, account_id, merchant_id, device_id, amount, timestamp, fraud_flag
```

### Step 3: Phase 2 - Do Predictions (GNN)
```
Sidebar → Click "🧠 Do Predictions (Phase 2)"
```
What happens:
- 🧠 Simulates GNN processing (neural network analysis)
- ✅ Inserts predictions to `fraud_predictions` table (8 columns WITH status)
- ✅ Status values: "FRAUD" or "OK" (uppercase)
- ✅ Console shows: `"✅ PHASE 2 COMPLETE — X predictions saved"`
- ✅ Console shows: `"Table: 'fraud_predictions' (enriched with GNN status)"`

Check pgAdmin:
```
pgAdmin → Databases → postgres → Schemas → public → Tables → fraud_predictions
→ Right-click → "View/Edit Data" → First 100 rows
→ See: transaction_id, account_id, merchant_id, device_id, amount, timestamp, fraud_flag, status
```

---

## Two Table Comparison

### Phase 1: `transactions` Table (RAW DATA)

| Column | Type | Value |
|--------|------|-------|
| transaction_id | BIGINT | 1, 2, 3, ... |
| account_id | INTEGER | 1-100 |
| merchant_id | INTEGER | 1-15 |
| device_id | INTEGER | 1-10 |
| amount | DECIMAL | $10.50, $250.00, ... |
| timestamp | TIMESTAMP | 2024-01-01 10:30:45 |
| fraud_flag | BOOLEAN | TRUE or FALSE |

✅ **What you see:** Original transaction data exactly as received
❌ **Status column:** DOES NOT EXIST (Phase 1 only)

### Phase 2: `fraud_predictions` Table (PROCESSED DATA)

| Column | Type | Value |
|--------|------|-------|
| transaction_id | BIGINT | 1, 2, 3, ... |
| account_id | INTEGER | 1-100 |
| merchant_id | INTEGER | 1-15 |
| device_id | INTEGER | 1-10 |
| amount | DECIMAL | $10.50, $250.00, ... |
| timestamp | TIMESTAMP | 2024-01-01 10:30:45 |
| fraud_flag | BOOLEAN | TRUE or FALSE |
| **status** | **VARCHAR** | **"FRAUD" or "OK"** ← NEW! |

✅ **What you see:** Transaction data + GNN fraud classification
✅ **Status column:** EXISTS and shows fraud prediction
✅ **Dashboard uses this table** for all displays

---

## Console Output Explanation

### Phase 1 Output:
```
🔄 PHASE 1 START - Inserting 1000 raw transactions...
✅ PHASE 1 COMPLETE — 1000 raw transactions stored in database
   Columns: transaction_id, account_id, merchant_id, device_id, amount, timestamp, fraud_flag
   Table: 'transactions' (raw data, no status)
```

**What it means:**
- 1,000 original transactions inserted
- Inserted into `transactions` table
- No status column added yet
- Ready for Phase 2

### Phase 2 Output:
```
🔄 PHASE 2 START - Running GNN analysis and saving 1000 predictions...
✅ PHASE 2 COMPLETE — 1000 predictions stored in database
   Columns: transaction_id, account_id, merchant_id, device_id, amount, timestamp, fraud_flag, status
   Table: 'fraud_predictions' (enriched with GNN status)
```

**What it means:**
- 1,000 transactions processed by GNN (fraud detection model)
- Results inserted into `fraud_predictions` table
- Status column added: each transaction marked as "FRAUD" or "OK"
- This is the final enriched dataset

---

## Why Two Tables?

### Problem with Single Table:
```
❌ Hard to see the difference between raw and processed data
❌ Unclear what the "before" state was
❌ Status column appears suddenly (confusing workflow)
```

### Solution with Two Tables:
```
✅ Crystal clear: Phase 1 (raw) vs Phase 2 (predictions)
✅ Easy to understand ML pipeline
✅ Can compare identical transaction_ids in both tables
✅ Each table shows exact schema for its phase
```

### Educational Value:
```
Students/Users can see:
1. "Here's the raw data as it comes in" (Phase 1 table)
2. "Here's what the ML model predicted" (Phase 2 table)
3. "The model added fraud risk classification" (status column)
```

---

## Example Workflow

### Sample Data:

**Phase 1: `transactions` table (after "Load Transactions" button)**
```
transaction_id | account_id | merchant_id | device_id | amount   | timestamp           | fraud_flag
──────────────────────────────────────────────────────────────────────────────────────────────────
       1001    |     42     |      5      |     2     | 150.50   | 2024-01-01 10:30:45 |    0
       1002    |     87     |      8      |     1     | 2500.00  | 2024-01-01 10:31:12 |    1
       1003    |     15     |      3      |     4     | 75.25    | 2024-01-01 10:32:00 |    0
```

**Phase 2: `fraud_predictions` table (after "Do Predictions" button)**
```
transaction_id | account_id | merchant_id | device_id | amount   | timestamp           | fraud_flag | status
──────────────────────────────────────────────────────────────────────────────────────────────────────────
       1001    |     42     |      5      |     2     | 150.50   | 2024-01-01 10:30:45 |    0      | OK
       1002    |     87     |      8      |     1     | 2500.00  | 2024-01-01 10:31:12 |    1      | FRAUD
       1003    |     15     |      3      |     4     | 75.25    | 2024-01-01 10:32:00 |    0      | OK
```

**Dashboard Display:** Uses only `fraud_predictions` table above

---

## Common Questions

### Q: Why can't I see Phase 2 data without clicking Phase 1 first?
**A:** Both phases are independent. You can:
- Click Phase 1, then Phase 2 (recommended for demonstration)
- Skip Phase 1 and just click Phase 2 (if you understand the workflow)
- Run Phase 2 multiple times (creates/updates predictions)

### Q: What happens to Phase 1 data when I run Phase 2?
**A:** Phase 1 data stays in the `transactions` table forever. Phase 2 creates a NEW separate table with predictions. They're independent.

### Q: Can I delete Phase 1 data?
**A:** Yes, but it's not recommended as it shows the "before" state. If you want fresh data:
- Reload transactions in memory (data won't be in DB until Phase 1)
- Click Phase 1 again (overwrites `transactions` table)

### Q: Why is the status column uppercase (FRAUD, OK)?
**A:** Uppercase makes it easier to filter and search in SQL and the UI. It's also convention for categorical data.

### Q: Can I see both tables side-by-side?
**A:** Yes! Open pgAdmin in a browser:
- One tab: `transactions` table
- Another tab: `fraud_predictions` table
- Compare them directly

---

## Verification Checklist

After running both phases, verify:

- [ ] Phase 1 complete message shows in console
- [ ] Phase 2 complete message shows in console
- [ ] pgAdmin shows `transactions` table (7 columns)
- [ ] pgAdmin shows `fraud_predictions` table (8 columns)
- [ ] Same `transaction_id` values in both tables
- [ ] `fraud_predictions` has status column with "FRAUD" or "OK" values
- [ ] `transactions` does NOT have status column
- [ ] Dashboard displays fraud statistics correctly

---

## Next Steps

1. **Try it out:** Load demo data → Phase 1 → Phase 2
2. **Explore pgAdmin:** View both tables and compare
3. **Understand the flow:** Raw data → ML processing → Predictions
4. **Experiment:** Try different transaction counts, check performance
5. **Learn:** See how ML pipeline works in practice

---

## Support

If anything doesn't work:
1. Check console output for error messages
2. Verify PostgreSQL is running (`localhost:5432`)
3. Open pgAdmin and check if tables exist
4. Reload the dashboard if needed
5. Check the REFACTORING_SUMMARY.md for technical details

---

**Enjoy exploring the two-phase fraud detection pipeline! 🚀**
