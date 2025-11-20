# 📊 Data Loading & Graph Construction Guide

## Overview

This guide explains how to load the IEEE-CIS fraud detection dataset, process it, insert it into PostgreSQL, and build a heterogeneous graph for GNN training.

---

## Pipeline Overview

```
IEEE-CIS CSV Files
        ↓
   Data Loader (preprocessing)
        ↓
   Processed CSVs
        ↓
   Database Inserter
        ↓
   PostgreSQL Database
        ↓
   Graph Builder
        ↓
Heterogeneous Graph (PyTorch Geometric)
```

---

## Step 1: Download Dataset

### Option A: Kaggle CLI
```powershell
# Configure Kaggle API
mkdir $env:USERPROFILE\.kaggle
# Place kaggle.json in C:\Users\<YourName>\.kaggle\

# Download dataset
kaggle competitions download -c ieee-fraud-detection -p data/raw/

# Extract
cd data/raw
Expand-Archive ieee-fraud-detection.zip -DestinationPath .
```

### Option B: Manual Download
1. Visit: https://www.kaggle.com/c/ieee-fraud-detection/data
2. Download `train_transaction.csv` and `train_identity.csv`
3. Place in `data/raw/` directory

---

## Step 2: Load Data into Database

### Basic Usage

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run data loading pipeline (full dataset)
python src/preprocessing/load_data.py
```

### With Sample (for testing)

```powershell
# Load only 10,000 transactions for quick testing
python src/preprocessing/load_data.py --sample 10000
```

### Advanced Options

```powershell
# Skip processing (use existing CSV files)
python src/preprocessing/load_data.py --skip-processing

# Skip database insertion (only process CSV files)
python src/preprocessing/load_data.py --skip-insertion

# Custom batch size for insertion
python src/preprocessing/load_data.py --batch-size 10000

# Combine options
python src/preprocessing/load_data.py --sample 50000 --batch-size 5000
```

---

## Step 3: Verify Data Quality

```powershell
# Run comprehensive data verification
python src/preprocessing/verify_data.py
```

**Checks performed:**
- Table row counts
- Referential integrity (foreign keys)
- Data value ranges
- Fraud distribution
- NULL value checks
- Duplicate detection
- Shared device patterns

---

## Step 4: Build Graph Structure

```powershell
# Build heterogeneous graph from database
python src/graph/build_graph.py
```

**Graph Structure Created:**

### Node Types
- **Account Nodes**: User accounts with risk scores
- **Merchant Nodes**: Merchants with fraud rates
- **Device Nodes**: Devices with sharing patterns

### Edge Types
- **account → merchant** (transacts_with): Transaction relationships
- **account → device** (uses): Device usage
- **account ↔ device** (shares): Shared device patterns

### Node Features

**Account Features (5 dimensions):**
- risk_score
- total_transactions (log-scaled)
- total_amount (log-scaled)
- account_age_days (log-scaled)
- fraud_flag

**Merchant Features (4 dimensions):**
- fraud_rate
- total_transactions (log-scaled)
- avg_transaction_amount (log-scaled)
- risk_level_encoded (0-3)

**Device Features (5 dimensions):**
- fraud_rate
- total_users (log-scaled)
- total_transactions (log-scaled)
- is_shared (binary)
- risk_score

### Edge Features

**Transaction Edges:**
- transaction_amount (log-scaled)
- transaction_hour (0-23)
- transaction_day_of_week (0-6)

**Shared Device Edges:**
- transaction_count (log-scaled)
- fraud_count (log-scaled)

---

## Module Structure

### `src/preprocessing/data_loader.py`

**Class: `DataLoader`**

Main class for loading and processing IEEE-CIS dataset.

**Key Methods:**
- `load_csv_files()` - Load transaction and identity CSVs
- `merge_datasets()` - Merge transaction with identity data
- `extract_account_data()` - Create account aggregations
- `extract_merchant_data()` - Create merchant aggregations
- `extract_device_data()` - Create device aggregations
- `extract_transaction_data()` - Clean transaction records
- `extract_shared_device_data()` - Identify device sharing patterns
- `process_dataset()` - Main processing pipeline

**Example Usage:**
```python
from src.preprocessing.data_loader import DataLoader

loader = DataLoader()

# Process full dataset
processed_data = loader.process_dataset()

# Process sample
processed_data = loader.process_dataset(sample_size=10000)

# Access individual dataframes
accounts = processed_data['accounts']
transactions = processed_data['transactions']
```

---

### `src/preprocessing/db_inserter.py`

**Class: `DatabaseInserter`**

Handles efficient bulk insertion into PostgreSQL.

**Key Methods:**
- `insert_accounts()` - Insert account records
- `insert_merchants()` - Insert merchant records
- `insert_devices()` - Insert device records
- `insert_transactions()` - Insert transaction records (with triggers disabled)
- `insert_shared_devices()` - Insert shared device relationships
- `insert_all_data()` - Complete insertion pipeline
- `verify_insertion()` - Verify data was inserted correctly

**Example Usage:**
```python
from src.preprocessing.db_inserter import DatabaseInserter

inserter = DatabaseInserter(batch_size=5000)

# Insert all data
results = inserter.insert_all_data()

# Verify
inserter.verify_insertion()
```

---

### `src/preprocessing/load_data.py`

Main orchestration script that combines loading and insertion.

**Command-line Options:**
```
--sample SAMPLE          Sample size for testing
--skip-processing        Skip data processing
--skip-insertion         Skip database insertion
--batch-size SIZE        Batch size for insertion (default: 5000)
```

---

### `src/graph/build_graph.py`

**Class: `GraphBuilder`**

Constructs heterogeneous graph from database.

**Key Methods:**
- `fetch_account_nodes()` - Query account nodes from DB
- `fetch_merchant_nodes()` - Query merchant nodes from DB
- `fetch_device_nodes()` - Query device nodes from DB
- `fetch_transaction_edges()` - Query transaction edges
- `fetch_shared_device_edges()` - Query shared device edges
- `build_account_features()` - Create account feature matrix
- `build_merchant_features()` - Create merchant feature matrix
- `build_device_features()` - Create device feature matrix
- `build_hetero_graph()` - Construct complete graph
- `save_graph()` - Save graph to disk

**Example Usage:**
```python
from src.graph.build_graph import GraphBuilder
import torch

builder = GraphBuilder()

# Build graph
graph_data = builder.build_hetero_graph()

# Access node features
account_features = graph_data['account'].x
account_labels = graph_data['account'].y

# Access edges
txn_edges = graph_data['account', 'transacts_with', 'merchant'].edge_index

# Save
builder.save_graph(graph_data)
```

---

## Data Flow

### 1. CSV Processing

**Input:** Raw CSV files
- `train_transaction.csv` (~500K rows)
- `train_identity.csv` (~140K rows)

**Processing:**
1. Load CSV files using pandas
2. Merge transaction with identity data
3. Create aggregations for accounts, merchants, devices
4. Extract relationships and patterns
5. Save processed CSVs to `data/processed/`

**Output:** Processed CSV files
- `accounts.csv`
- `merchants.csv`
- `devices.csv`
- `transactions.csv`
- `shared_devices.csv`

### 2. Database Insertion

**Input:** Processed CSV files

**Process:**
1. Prepare data (handle NaN, type conversion)
2. Insert in order (accounts → merchants → devices → transactions → shared_devices)
3. Use batch insertion for efficiency
4. Disable triggers during bulk insert
5. Re-enable triggers after insertion

**Output:** Populated PostgreSQL database

### 3. Graph Construction

**Input:** PostgreSQL database

**Process:**
1. Query nodes and edges from database
2. Create node ID mappings
3. Build feature matrices
4. Normalize and scale features
5. Create edge indices
6. Assemble HeteroData object

**Output:** `fraud_graph.pt` (PyTorch Geometric graph)

---

## Performance Considerations

### Memory Usage

- **Full Dataset**: ~8GB RAM recommended
- **Sample (10K)**: ~2GB RAM
- **Database**: ~2GB disk space

### Processing Time

| Operation | Full Dataset | 10K Sample |
|-----------|--------------|------------|
| CSV Loading | ~30 seconds | ~5 seconds |
| Processing | ~2 minutes | ~10 seconds |
| DB Insertion | ~15 minutes | ~30 seconds |
| Graph Building | ~3 minutes | ~10 seconds |
| **Total** | **~20 minutes** | **~1 minute** |

### Optimization Tips

1. **Use Sampling for Development**
   ```powershell
   python src/preprocessing/load_data.py --sample 10000
   ```

2. **Increase Batch Size** (if you have more RAM)
   ```powershell
   python src/preprocessing/load_data.py --batch-size 10000
   ```

3. **Skip Steps** (if already done)
   ```powershell
   python src/preprocessing/load_data.py --skip-processing
   ```

4. **Monitor Progress**
   - Check logs in `logs/` directory
   - Watch progress bars in terminal

---

## Troubleshooting

### Issue: "FileNotFoundError: train_transaction.csv"

**Solution:**
```powershell
# Download dataset to data/raw/
cd data/raw
kaggle competitions download -c ieee-fraud-detection
Expand-Archive ieee-fraud-detection.zip -DestinationPath .
```

### Issue: "psycopg2.OperationalError: could not connect"

**Solution:**
1. Check PostgreSQL is running: `Get-Service postgresql*`
2. Verify credentials in `.env` file
3. Test connection: `python -c "from src.database.connection import db; db.test_connection()"`

### Issue: "Table does not exist"

**Solution:**
```powershell
# Create database tables
python src/database/setup_db.py
```

### Issue: "Memory Error during processing"

**Solution:**
```powershell
# Use smaller sample size
python src/preprocessing/load_data.py --sample 50000
```

### Issue: "Slow insertion speed"

**Solution:**
1. Increase batch size: `--batch-size 10000`
2. Disable antivirus temporarily
3. Check PostgreSQL configuration (increase `shared_buffers`)

---

## Files Generated

After running the pipeline, these files will be created:

```
data/processed/
├── accounts.csv                 # Processed account data
├── merchants.csv                # Processed merchant data
├── devices.csv                  # Processed device data
├── transactions.csv             # Processed transaction data
├── shared_devices.csv           # Device sharing patterns
├── fraud_graph.pt              # Heterogeneous graph (PyTorch)
├── node_mappings.pkl           # Node ID to index mappings
└── graph_stats.pkl             # Graph statistics

logs/
├── data_loading_*.log          # Data loading logs
├── db_insertion.log            # Database insertion logs
└── graph_construction.log      # Graph building logs
```

---

## Next Steps

Once data loading and graph construction are complete:

1. **Train GNN Model**
   ```powershell
   python src/training/train.py
   ```

2. **Evaluate Performance**
   ```powershell
   python src/training/evaluate.py
   ```

3. **Launch Dashboard**
   ```powershell
   streamlit run src/visualization/dashboard.py
   ```

---

## API Reference

### Data Loader API

```python
from src.preprocessing.data_loader import DataLoader

loader = DataLoader()

# Process dataset
processed = loader.process_dataset(
    sample_size=None  # Optional: limit number of records
)

# Access processed dataframes
accounts = processed['accounts']
merchants = processed['merchants']
devices = processed['devices']
transactions = processed['transactions']
shared_devices = processed['shared_devices']
```

### Database Inserter API

```python
from src.preprocessing.db_inserter import DatabaseInserter

inserter = DatabaseInserter(batch_size=5000)

# Insert all data
results = inserter.insert_all_data()

# Results dictionary contains row counts
# {'accounts': 10000, 'merchants': 150, ...}
```

### Graph Builder API

```python
from src.graph.build_graph import GraphBuilder

builder = GraphBuilder()

# Build graph
graph = builder.build_hetero_graph()

# Access components
print(graph['account'].x.shape)     # Account features
print(graph['account'].y)           # Account labels
print(graph['account', 'transacts_with', 'merchant'].edge_index.shape)

# Save graph
builder.save_graph(graph, 'my_graph.pt')
```

---

**Last Updated:** November 20, 2025
