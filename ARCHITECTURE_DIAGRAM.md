# DRAGNN-FraudDB: Two-Table Architecture Diagram

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DRAGNN-FraudDB System                               │
│                       (Two-Phase Workflow)                                  │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Streamlit Dashboard    │
                    │  (src/visualization/)    │
                    └──────────────┬───────────┘
                                   │
                    ┌──────────────┴───────────┐
                    │                          │
            ┌───────▼──────────┐     ┌────────▼─────────┐
            │  Phase 1 Button  │     │  Phase 2 Button  │
            │  "Load Txns"     │     │  "Do Predictions"│
            └───────┬──────────┘     └────────┬─────────┘
                    │                         │
        ┌───────────┴──────┐     ┌────────────┴───────────┐
        │                  │     │                        │
   ┌────▼─────────────┐    │     │    ┌──────────────────▼────┐
   │ Data Loader      │◄───┘     │    │ GNN Processing        │
   │ (Generate/Load)  │          │    │ (Simulate)            │
   └────┬─────────────┘          │    └──────────────────┬────┘
        │                         │                      │
        │                         │    ┌─────────────────▼────┐
        │                    ┌────▼────▼─────────────────┐    │
        │                    │  Data Preparation         │    │
        │                    │  (Column mapping)         │    │
        │                    └────┬────────────┬─────────┘    │
        │                         │            │               │
        │                    ┌────▼──┐    ┌───▼──────┐        │
        │                    │ rename │    │ rename   │        │
        │                    │ columns │    │ columns  │        │
        │                    │add IDs  │    │add status│        │
        │                    └────┬──┘    └───┬──────┘        │
        │                         │            │               │
┌───────┴──────────┐   ┌──────────▼─────┐    │    ┌──────────▼─────┐
│ PostgreSQL DB    │   │ PostgreSQL DB   │    │    │ PostgreSQL DB   │
│  (localhost:     │   │  (localhost:    │    │    │  (localhost:    │
│   5432)          │   │   5432)         │    │    │   5432)         │
│                  │   │                 │    │    │                 │
├──────────────────┤   ├─────────────────┤    │    ├─────────────────┤
│ transactions     │   │fraud_predictions│    │    │ (Both visible   │
│  (Phase 1)       │   │  (Phase 2)      │    │    │  in pgAdmin)    │
│                  │   │                 │    │    │                 │
│ 7 columns:       │   │ 8 columns:      │    │    │                 │
│ - tr_id          │   │ - tr_id         │    │    │                 │
│ - account_id     │   │ - account_id    │    │    │                 │
│ - merchant_id    │   │ - merchant_id   │    │    │                 │
│ - device_id      │   │ - device_id     │    │    │                 │
│ - amount         │   │ - amount        │    │    │                 │
│ - timestamp      │   │ - timestamp     │    │    │                 │
│ - fraud_flag     │   │ - fraud_flag    │    │    │                 │
│                  │   │ - status ✓      │◄───┘    │                 │
│ RAW DATA         │   │                 │         │ ENRICHED DATA   │
│ NO STATUS        │   │ WITH STATUS     │         │ WITH STATUS     │
└────┬─────────────┘   └─────────────────┘         └─────────────────┘
     │                                                    │
     │  insert_                                   insert_
     │  transactions_batch()                   fraud_predictions_batch()
     │  (7 columns, no status)                 (8 columns, with status)
     │                                                    │
     │  Console: "✅ PHASE 1                            │
     │  COMPLETE — {N}                    Console: "✅ PHASE 2
     │  raw transactions"                 COMPLETE — {N}
     │                                    predictions"
     │
     └────────────────────────────────────────────────────┐
                                                         │
                    ┌────────────────────────────────────┘
                    │
            ┌───────▼──────────────┐
            │  Dashboard Display   │
            │  (Queries fraud_     │
            │   predictions only)  │
            │                      │
            │  Shows:              │
            │  • Fraud stats       │
            │  • Trends            │
            │  • Transactions      │
            │  • Predictions       │
            └──────────────────────┘
```

---

## Data Flow Diagram

```
Memory Data                Database Tables              Dashboard
─────────────              ───────────────              ──────────

  Users         Step 1       Phase 1 Table              Dashboard
 Generate      ─────────►    transactions              Displays
 or Load                      (7 columns)              Fraud Stats
                              NO STATUS                    │
                                                           │
                              ┌─────────────┐             │
                              │ tr_id: 1001 │ ◄───────────┤
                              │ amt: $150   │ (queriesF2) │
                              │ fraud_flag:0│             │
                              └─────────────┘             │
                                                           │
                           Step 2                          │
                          ─────────►   Phase 2 Table      │
                      (GNN Processing) fraud_predictions  │
                                       (8 columns)        │
                                       WITH STATUS        │
                                                           │
                                       ┌─────────────────┐ │
                                       │ tr_id: 1001     │ │
                                       │ amt: $150       │ │
                                       │ fraud_flag: 0   │ │
                                       │ status: "OK" ◄──┼─┘
                                       └─────────────────┘
```

---

## Phase Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                     Phase 1 vs Phase 2                          │
├─────────────────────────────────────────────────────────────────┤

PHASE 1: Load Transactions (Raw Data)

  Input:  CSV/API data
          │
  Process: rename columns
           add missing IDs
           │
  Insert:  7 columns to 'transactions' table
           NO STATUS COLUMN
           │
  Output:  ┌────────────────────┐
           │ Original Data      │
           │ - tr_id: 1001      │
           │ - account_id: 42   │
           │ - amount: $150.50  │
           │ - fraud_flag: 0    │
           │ (NO status)        │
           └────────────────────┘
           
  Console: ✅ PHASE 1 COMPLETE — 1000 raw transactions stored
           Table: 'transactions' (raw data, no status)
           Columns: tr_id, account_id, merchant_id, device_id, amount, timestamp, fraud_flag

─────────────────────────────────────────────────────────────────

PHASE 2: Do Predictions (ML Processing)

  Input:  Data from memory
          │
  Process: GNN Analysis (Fraud Detection Model)
           Add status based on fraud_flag:
           - fraud_flag = 1 → status = "FRAUD"
           - fraud_flag = 0 → status = "OK"
           │
  Insert:  8 columns to 'fraud_predictions' table
           WITH STATUS COLUMN
           │
  Output:  ┌────────────────────┐
           │ Enriched Data      │
           │ - tr_id: 1001      │
           │ - account_id: 42   │
           │ - amount: $150.50  │
           │ - fraud_flag: 0    │
           │ - status: "OK" ✓   │
           └────────────────────┘
           
  Console: ✅ PHASE 2 COMPLETE — 1000 predictions stored
           Table: 'fraud_predictions' (enriched with GNN status)
           Columns: tr_id, account_id, merchant_id, device_id, amount, timestamp, fraud_flag, status

─────────────────────────────────────────────────────────────────
```

---

## Table Schema Comparison

```
TRANSACTIONS TABLE (Phase 1)
════════════════════════════════════════════════════════════════

Column          Type              Purpose
──────────────────────────────────────────────────────────────
transaction_id  BIGINT PRIMARY    Unique transaction identifier
account_id      INTEGER           Account performing transaction
merchant_id     INTEGER           Merchant receiving transaction
device_id       INTEGER           Device used for transaction
amount          DECIMAL           Transaction amount ($)
timestamp       TIMESTAMP         When transaction occurred
fraud_flag      BOOLEAN           Original fraud label (0/1)
processed_at    TIMESTAMP         When inserted into database

Total Columns: 7 (+ metadata)
Status Column: NONE
Purpose: STORE RAW INCOMING DATA


FRAUD_PREDICTIONS TABLE (Phase 2)
════════════════════════════════════════════════════════════════

Column          Type              Purpose
──────────────────────────────────────────────────────────────
transaction_id  BIGINT PRIMARY    Same as Phase 1
account_id      INTEGER           Same as Phase 1
merchant_id     INTEGER           Same as Phase 1
device_id       INTEGER           Same as Phase 1
amount          DECIMAL           Same as Phase 1
timestamp       TIMESTAMP         Same as Phase 1
fraud_flag      BOOLEAN           Same as Phase 1
status          VARCHAR(20)       ← NEW: "FRAUD" or "OK"
processed_at    TIMESTAMP         When inserted into database

Total Columns: 8 (+ metadata)
Status Column: YES - "FRAUD" or "OK" (uppercase)
Purpose: STORE ML PREDICTIONS WITH STATUS


KEY DIFFERENCE: STATUS COLUMN
════════════════════════════════════════════════════════════════

transactions        fraud_predictions
────────────────    ────────────────────
✗ No status         ✓ Has status
                    ✓ Status = "FRAUD" (fraud_flag=1)
                    ✓ Status = "OK" (fraud_flag=0)
                    
Raw incoming data   Enriched with ML predictions
                    
Unchanged original  Post-processing classification
```

---

## Database Query Examples

### Phase 1: Check Raw Data
```sql
-- Count transactions in Phase 1 table
SELECT COUNT(*) FROM transactions;
-- Result: 1000 rows

-- See structure
SELECT * FROM transactions LIMIT 5;
-- Result: 5 rows with 7 columns (no status)

-- See if status column exists
SELECT COUNT(*) FROM transactions WHERE status = 'FRAUD';
-- Error: column "status" does not exist ✓ (as expected)
```

### Phase 2: Check Predictions
```sql
-- Count predictions in Phase 2 table
SELECT COUNT(*) FROM fraud_predictions;
-- Result: 1000 rows

-- See structure
SELECT * FROM fraud_predictions LIMIT 5;
-- Result: 5 rows with 8 columns (includes status)

-- Count fraud cases
SELECT COUNT(*) FROM fraud_predictions WHERE status = 'FRAUD';
-- Result: ~500 fraud cases

-- Count legitimate cases
SELECT COUNT(*) FROM fraud_predictions WHERE status = 'OK';
-- Result: ~500 legitimate cases
```

### Comparison: Same Data, Different Schemas
```sql
-- Find same transaction in both tables
SELECT t.transaction_id, t.amount, f.status
FROM transactions t
JOIN fraud_predictions f ON t.transaction_id = f.transaction_id
WHERE t.transaction_id = 1001;

-- Result:
-- tr_id: 1001
-- amount: 150.50
-- status: "OK" (from fraud_predictions)
```

---

## pgAdmin Visualization

```
PostgreSQL Database
└── Databases
    └── postgres
        └── Schemas
            └── public
                └── Tables
                    ├── transactions
                    │   ├── Columns (7)
                    │   │   ├── transaction_id
                    │   │   ├── account_id
                    │   │   ├── merchant_id
                    │   │   ├── device_id
                    │   │   ├── amount
                    │   │   ├── timestamp
                    │   │   └── fraud_flag
                    │   ├── Indexes (4)
                    │   │   ├── idx_transactions_fraud_flag
                    │   │   ├── idx_transactions_account_id
                    │   │   ├── idx_transactions_timestamp
                    │   │   └── idx_transactions_amount
                    │   └── Rows: 1000 (Phase 1)
                    │
                    └── fraud_predictions
                        ├── Columns (8)
                        │   ├── transaction_id
                        │   ├── account_id
                        │   ├── merchant_id
                        │   ├── device_id
                        │   ├── amount
                        │   ├── timestamp
                        │   ├── fraud_flag
                        │   └── status ← NEW
                        ├── Indexes (4)
                        │   ├── idx_fraud_predictions_fraud_flag
                        │   ├── idx_fraud_predictions_account_id
                        │   ├── idx_fraud_predictions_status
                        │   └── idx_fraud_predictions_timestamp
                        └── Rows: 1000 (Phase 2)
```

---

## Component Interaction Flow

```
User Interface (Streamlit)
        ├─ Phase 1 Button
        │  └─ insert_transactions_batch()
        │     └─ PostgreSQL.transactions table
        │        └─ 7 columns, no status
        │
        ├─ Phase 2 Button
        │  └─ insert_fraud_predictions_batch()
        │     └─ PostgreSQL.fraud_predictions table
        │        └─ 8 columns, with status
        │
        └─ Display Data
           └─ get_transactions_with_status()
              └─ Query from fraud_predictions (Phase 2 only)


Database Methods (PostgreSQL Manager)
        ├─ create_transactions_table()
        │  └─ Schema: 7 columns
        │
        ├─ create_fraud_predictions_table()
        │  └─ Schema: 8 columns (includes status)
        │
        ├─ insert_transactions_batch(df)
        │  └─ INSERT 7 columns into transactions
        │
        ├─ insert_fraud_predictions_batch(df)
        │  └─ INSERT 8 columns into fraud_predictions
        │
        └─ Query Methods
           ├─ get_fraud_stats()
           │  └─ SELECT FROM fraud_predictions
           ├─ get_transactions_with_status()
           │  └─ SELECT FROM fraud_predictions
           └─ get_transaction_by_search()
              └─ SELECT FROM fraud_predictions


Data Tables (PostgreSQL)
        ├─ transactions (Phase 1)
        │  ├─ Data: 1000 rows
        │  ├─ Columns: 7
        │  └─ Status: NONE
        │
        └─ fraud_predictions (Phase 2)
           ├─ Data: 1000 rows
           ├─ Columns: 8
           └─ Status: FRAUD/OK
```

---

## Summary

The two-table architecture provides:

✅ **Clarity**: Raw vs Processed data clearly separated
✅ **Transparency**: Both tables visible in pgAdmin
✅ **Education**: Users see before/after ML processing
✅ **Independence**: Phases can run independently
✅ **Verification**: Easy to audit both datasets

Result: **Clear demonstration of a machine learning pipeline** 🚀
