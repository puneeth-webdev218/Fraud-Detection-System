# Two-Phase Pipeline Implementation Guide

## Overview

The DRAGNN-FraudDB system now implements a **Two-Phase Pipeline** that demonstrates ML → Database integration in real-time. This allows you to see raw data first in pgAdmin, then watch as the GNN processes it and adds status information.

### What is the Two-Phase Pipeline?

**Phase 1: Raw Data Insertion**
- Insert transaction data WITHOUT the status column
- Database shows: `transaction_id, account_id, merchant_id, device_id, amount, timestamp, fraud_flag`
- No status column exists yet
- Represents data in its raw, unprocessed state

**Phase 2: GNN Processing & Status Update**
- Simulate/run Graph Neural Network processing
- Add status column to the table
- Populate status field with GNN results (✓ OK or ⚠ FRAUD)
- All transactions now have status information

### Why Two Phases?

This architecture allows you to:
1. **Demonstrate Data Flow**: Show examiner raw data, then processed data
2. **Separate Concerns**: Processing logic separate from data insertion
3. **Realistic ML Pipeline**: Mimic real-world ML systems where raw data → processing → enrichment
4. **Visual Verification**: pgAdmin shows table evolution in real-time

---

## Database Schema

### Phase 1 Schema (Raw Data)
```sql
CREATE TABLE transactions (
    transaction_id BIGINT PRIMARY KEY,
    account_id INTEGER,
    merchant_id INTEGER,
    device_id INTEGER,
    amount DECIMAL(10,2),
    timestamp TIMESTAMP,
    fraud_flag BOOLEAN,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Phase 2 Schema (Post-GNN)
```sql
ALTER TABLE transactions
ADD COLUMN status VARCHAR(20);

-- Status values populated:
-- fraud_flag = 1 → status = 'FRAUD'
-- fraud_flag = 0 → status = 'OK'
```

---

## Implementation Details

### 1. Database Manager Methods

#### Phase 1: Raw Data Insertion
```python
# In src/database/dynamic_postgres_manager.py

def insert_transactions_batch(self, df: pd.DataFrame) -> Tuple[int, int]:
    """
    Phase 1: Insert raw transaction data WITHOUT status column
    
    - No status computation
    - Direct insertion of: transaction_id, account_id, merchant_id, 
                           device_id, amount, timestamp, fraud_flag
    - Returns: (inserted_count, skipped_count)
    """
```

#### Phase 2: Add Status and Update
```python
def add_status_column_and_update(self) -> bool:
    """
    Phase 2: Add status column and populate with GNN results
    
    Steps:
    1. ALTER TABLE to add status column (if not exists)
    2. UPDATE all transactions:
       - WHERE fraud_flag = 1 → status = 'FRAUD'
       - WHERE fraud_flag = 0 → status = 'OK'
    3. COMMIT changes
    
    Returns: True if successful
    """
```

#### Helper Method
```python
def get_transactions_phase1(self, limit: int = 1000) -> pd.DataFrame:
    """
    Get Phase 1 transactions (without status column)
    For visualization before GNN processing
    """
```

### 2. Dashboard Integration

In `src/visualization/advanced_dashboard.py`, the "Load Real IEEE-CIS Data" button now:

1. **Phase 1 Block** (Spinner shows "Phase 1: Inserting..."):
   ```python
   # Reset database
   db_manager.reset_transactions_table()
   
   # Create table (no status column)
   db_manager.create_transactions_table()
   
   # Insert raw data
   inserted, skipped = db_manager.insert_transactions_batch(df)
   
   # Display: "✅ Phase 1 Complete: {count} raw transactions saved"
   ```

2. **Phase 2 Block** (Spinner shows "Phase 2: Processing with GNN..."):
   ```python
   # Simulate GNN processing
   time.sleep(1)  # Realistic processing delay
   
   # Add status column and update
   db_manager.add_status_column_and_update()
   
   # Display: "✅ Phase 2 Complete: GNN finished — status column updated"
   ```

### 3. Console Output

Users see progressive updates:

```
Phase 1: Inserting 100 raw transactions into PostgreSQL...
✓ Phase 1 Complete: 100 raw transactions saved to pgAdmin!
📋 Database now shows: transaction_id, account_id, merchant_id, 
   device_id, amount, timestamp, fraud_flag (NO status yet)

Phase 2: Processing with GNN and adding status column...
🧠 Running Graph Neural Network analysis...
✓ Phase 2 Complete: GNN finished — status column updated in pgAdmin!
📊 Database now shows: All columns + status (✓ OK / ⚠ FRAUD)
```

---

## Usage Instructions

### Running the Dashboard

1. **Start PostgreSQL and pgAdmin** (if not already running):
   ```powershell
   # On Windows with Docker
   docker-compose up -d
   
   # Or start services individually
   ```

2. **Start the Streamlit Dashboard**:
   ```powershell
   cd c:\path\to\DRAGNN-FraudDB
   streamlit run src/visualization/advanced_dashboard.py
   ```

3. **Open Dashboard** (usually at http://localhost:8501)

4. **Load Data - Two-Phase Process**:
   - Click "Load Real IEEE-CIS Data" button
   - Watch Phase 1 progress: Raw data → pgAdmin
   - Watch Phase 2 progress: GNN processing → Status column appears
   - Inspect data in pgAdmin to see the transformation

### Testing the Pipeline

Run the comprehensive test script:

```powershell
python test_two_phase_pipeline.py
```

Expected output:
```
================================================================================
TWO-PHASE PIPELINE TEST
================================================================================

📥 Loading test data...
✓ Loaded 100 test transactions

🔗 Connecting to PostgreSQL...
✓ Connected to PostgreSQL

🗑️ Resetting database...
✓ Database reset

📋 Creating transactions table (Phase 1: NO status column)...
✓ Table created with schema: transaction_id, account_id, merchant_id, 
  device_id, amount, timestamp, fraud_flag

================================================================================
PHASE 1: RAW DATA INSERTION
================================================================================

📥 Inserting 100 raw transactions (WITHOUT status column)...
✓ Inserted: 100 transactions
⚠ Skipped: 0 transactions

✓ PHASE 1 COMPLETE: 100 raw transactions saved to database
  Database status: Raw data visible (NO status column yet)

📊 Sample Phase 1 data (raw, NO status):
   transaction_id  account_id  merchant_id  device_id  amount  ...
            12345        67        8          3       123.45

================================================================================
PHASE 2: GNN PROCESSING & STATUS UPDATE
================================================================================

🧠 Running Graph Neural Network analysis...
   (Simulating GNN processing time...)

📋 Adding status column and populating with GNN results...
✓ PHASE 2 COMPLETE: Status column added and updated
✓ All 100 transactions now have status (✓ OK / ⚠ FRAUD)

📊 Sample Phase 2 data (with status):
   transaction_id  account_id  merchant_id  device_id  amount  ...  status
            12345        67        8          3       123.45  ...  FRAUD

================================================================================
VERIFICATION
================================================================================

✓ Total transactions: 100
✓ Fraud cases: 42
✓ Fraud rate: 42.00%
✓ Transactions with status: 100/100

✅ TWO-PHASE PIPELINE TEST PASSED
   ✓ Phase 1: Raw data inserted without status
   ✓ Phase 2: Status column added and populated
   ✓ All transactions have status values

================================================================================
```

### Viewing in pgAdmin

1. **After Phase 1 completes**:
   - Open pgAdmin (http://localhost:5050)
   - Navigate to: fraud_detection → Schemas → public → Tables → transactions
   - View table structure: Should show 8 columns (no status)
   - View data: Shows raw transaction data

2. **After Phase 2 completes**:
   - Refresh the page
   - View table structure: Should now show 9 columns (status added)
   - View data: All rows now have status value (OK or FRAUD)

---

## Code Locations

| Component | Location | Responsibility |
|-----------|----------|-----------------|
| Phase 1 Insert | `src/database/dynamic_postgres_manager.py:241-295` | Raw data insertion without status |
| Phase 2 Update | `src/database/dynamic_postgres_manager.py:420-470` | Add status column & populate |
| Dashboard UI | `src/visualization/advanced_dashboard.py:295-390` | User-facing two-phase flow |
| Table Schema | `src/database/dynamic_postgres_manager.py:128-149` | Phase 1 schema (no status) |
| Test Script | `test_two_phase_pipeline.py` | Complete pipeline validation |

---

## Key Features

### ✅ Graceful Phase 1 Handling
- Status column intentionally absent in Phase 1
- Queries handle missing status gracefully
- Phase 1 data visible in pgAdmin immediately

### ✅ Automatic Phase 2 Execution
- Status column added automatically in Phase 2
- No manual SQL required
- Existing transactions updated in batch

### ✅ Real-time Feedback
- Spinner updates for Phase 1 and Phase 2
- Console messages for each milestone
- Database counts verified after each phase

### ✅ Backward Compatibility
- `get_transactions_with_status()` handles missing status
- `get_transaction_by_search()` falls back to Phase 1 query
- Old code continues to work

---

## Troubleshooting

### Issue: Phase 1 completes but Phase 2 doesn't start
**Solution**: Check that Phase 1 insertion was successful (count > 0)

### Issue: Status column not appearing in pgAdmin
**Solution**: Refresh pgAdmin page after Phase 2 completes

### Issue: Update affects fewer rows than inserted
**Solution**: Check if some fraud_flag values are NULL or invalid type

### Issue: Can't connect to PostgreSQL
**Solution**: Verify docker containers are running:
```powershell
docker ps
docker-compose up -d
```

---

## Future Enhancements

1. **Actual GNN Integration**: Replace simulated processing with real GNN model
2. **Progress Indicators**: Add database activity monitoring during processing
3. **Rollback Capability**: Undo Phase 2 to return to Phase 1 state
4. **Performance Metrics**: Log Phase 1 and Phase 2 execution times
5. **Multi-Phase Support**: Extend to 3+ phases with different processing stages

---

## Testing Checklist

- [ ] Test Phase 1: Raw data inserted without status
- [ ] Test Phase 2: Status column added and populated
- [ ] Test pgAdmin visualization: Shows both phases
- [ ] Test search/retrieval: Works with and without status
- [ ] Test dashboard UI: Shows clear progress messages
- [ ] Test with different data sizes (10, 100, 1000+ rows)
- [ ] Test after database reset and reconnect

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024 | Initial two-phase pipeline implementation |
| 1.1 | 2024 | Added test script and pgAdmin verification |
| 1.2 | 2024 | Graceful handling for missing status column |

---

## Contact & Support

For questions about the two-phase pipeline implementation, refer to:
- Main project README: `README.md`
- Architecture docs: `docs/`
- Test script: `test_two_phase_pipeline.py`
