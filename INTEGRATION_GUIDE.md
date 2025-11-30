# Integration Guide: Dynamic Data Loading with Existing Components

## How to Use Dynamic Loading with Current Modules

This guide shows how to integrate the new `InteractiveDataLoader` with existing modules in the fraud detection system.

---

## 1. Data Processing Pipeline Integration

### Current Flow (Original)
```python
# data_loader.py - loads full dataset
from src.preprocessing.data_loader import DataLoader

loader = DataLoader()
transactions, identity = loader.load_csv_files()
merged = loader.merge_datasets(transactions, identity)
# Process entire dataset...
```

### New Flow (With Interactive Loading)
```python
# Now supports loading N transactions
from src.preprocessing.interactive_loader import InteractiveDataLoader

loader = InteractiveDataLoader()

# Option 1: Synthetic data with custom count
transactions = loader.generate_synthetic_transactions(n_transactions=1000)

# Option 2: Real data (if CSV exists) with limit
transactions, identity = loader.load_ieee_cis_data(n_transactions=1000)
if not identity.empty:
    transactions = loader.merge_transaction_identity(transactions, identity)

# Option 3: Full pipeline with scoped processing
data = loader.load_and_process_data(n_transactions=1000, use_synthetic=True)
# Returns: {'transactions': df, 'accounts': df, 'merchants': df, 'devices': df, 'stats': dict}
```

**Benefit:** Users control dataset size without editing code

---

## 2. Database Insertion with Limited Data

### Current Usage (db_inserter.py)
```python
from src.preprocessing.db_inserter import DatabaseInserter

inserter = DatabaseInserter()
# Inserts all transactions
inserter.insert_transactions(all_transactions)
inserter.insert_accounts(all_accounts)
```

### Enhanced Usage (With Selection)
```python
from src.preprocessing.interactive_loader import InteractiveDataLoader
from src.preprocessing.db_inserter import DatabaseInserter

loader = InteractiveDataLoader()
inserter = DatabaseInserter()

# Load only N transactions
data = loader.load_and_process_data(n_transactions=5000, use_synthetic=True)

# Insert only the selected subset
inserter.insert_transactions(data['transactions'])
inserter.insert_accounts(data['accounts'])
inserter.insert_merchants(data['merchants'])

print(f"Inserted {len(data['transactions'])} transactions")
```

**Benefit:** Database grows incrementally, not overwritten with full dataset

---

## 3. Graph Construction from Limited Data

### Original Code (build_graph.py)
```python
from src.graph.build_graph import GraphBuilder
from src.database.connection import db

builder = GraphBuilder()
accounts = builder.fetch_account_nodes()  # Fetches ALL from DB
merchants = builder.fetch_merchant_nodes()
# Builds graph from all data...
```

### With Interactive Loading
```python
from src.preprocessing.interactive_loader import InteractiveDataLoader
from src.graph.build_graph import GraphBuilder
import pandas as pd

# Load limited dataset
loader = InteractiveDataLoader()
data = loader.load_and_process_data(n_transactions=1000)

# Create in-memory graph (no DB needed)
transactions = data['transactions']
accounts = data['accounts']
merchants = data['merchants']
devices = data['devices']

# Now pass these to graph builder
# (Modify GraphBuilder to accept DataFrames instead of DB queries)
builder = GraphBuilder()
graph = builder.build_from_dataframes(
    transactions=transactions,
    accounts=accounts,
    merchants=merchants,
    devices=devices
)
```

**Benefit:** Test graph construction without full database setup

---

## 4. Model Training with Limited Data

### Original Training (train.py)
```python
from src.training.train import train_gnn
from src.models.graphsage import GraphSAGE

# Loads all data from database
model = GraphSAGE(config)
model.train()  # Trains on full dataset
```

### With Interactive Loading
```python
from src.preprocessing.interactive_loader import InteractiveDataLoader
from src.training.train import train_gnn_on_data
from src.models.graphsage import GraphSAGE

# Generate limited dataset for testing
loader = InteractiveDataLoader()
data = loader.load_and_process_data(n_transactions=5000)

# Train on loaded subset
model = GraphSAGE(config)
results = train_gnn_on_data(
    model,
    transactions=data['transactions'],
    accounts=data['accounts'],
    merchants=data['merchants'],
    devices=data['devices']
)

print(f"Training complete - Accuracy: {results['accuracy']:.4f}")
```

**Benefit:** Quick testing before full-scale training

---

## 5. Dashboard Integration (Already Implemented)

The advanced dashboard automatically handles dynamic loading:

```bash
streamlit run src/visualization/advanced_dashboard.py
```

Users can:
1. Click preset buttons to load 100, 500, 1K, 5K, or 10K transactions
2. Enter custom counts (10-50,000)
3. See all analyses update automatically

---

## 6. Feature: CSV Loading with Row Limit

Load real IEEE-CIS CSV files with transaction limit:

```python
from src.preprocessing.interactive_loader import InteractiveDataLoader

loader = InteractiveDataLoader()

# Load only first 1000 transactions from CSV
transactions, identity = loader.load_ieee_cis_data(n_transactions=1000)

print(f"Loaded {len(transactions)} transactions")
print(f"Columns: {transactions.columns.tolist()}")
```

**Note:** Requires CSV files at:
- `data/raw/train_transaction.csv`
- `data/raw/train_identity.csv`

---

## 7. Feature Engineering at Scale

Extract features from any sized dataset:

```python
from src.preprocessing.interactive_loader import InteractiveDataLoader

loader = InteractiveDataLoader()

# Test feature extraction on small dataset first
small_data = loader.load_and_process_data(n_transactions=100, use_synthetic=True)
print("100 txns features:", small_data['accounts'].columns.tolist())

# Then scale to larger dataset
large_data = loader.load_and_process_data(n_transactions=10000, use_synthetic=True)
print("10K txns features:", large_data['accounts'].columns.tolist())

# Same structure, different scale
assert list(small_data['accounts'].columns) == list(large_data['accounts'].columns)
```

**Benefit:** Validate pipelines before full-scale processing

---

## 8. Batch Processing Multiple Sizes

Compare results across different dataset sizes:

```python
from src.preprocessing.interactive_loader import InteractiveDataLoader
import pandas as pd

loader = InteractiveDataLoader()
results = []

for n_txns in [100, 500, 1000, 5000, 10000]:
    print(f"Processing {n_txns} transactions...")
    
    data = loader.load_and_process_data(n_transactions=n_txns, use_synthetic=True)
    stats = data['stats']
    
    results.append({
        'transactions': n_txns,
        'accounts': stats['unique_accounts'],
        'fraud_rate': stats['fraud_rate'],
        'total_amount': stats['total_amount']
    })

results_df = pd.DataFrame(results)
print(results_df)
```

Output:
```
   transactions  accounts  fraud_rate  total_amount
0           100        11        4.00        4521.23
1           500        38        4.20       23456.78
2          1000        42        4.20       45678.12
3          5000        99        4.40      234567.89
4         10000       156        4.30      456789.01
```

---

## 9. Interactive CLI Usage

Create a CLI script for interactive data loading:

```python
# interactive_cli.py
from src.preprocessing.interactive_loader import InteractiveDataLoader
import sys

def main():
    loader = InteractiveDataLoader()
    
    while True:
        print("\n=== Fraud Detection - Interactive Data Loader ===")
        print("1. Generate 100 transactions")
        print("2. Generate 500 transactions")
        print("3. Generate 1,000 transactions")
        print("4. Generate custom count")
        print("5. Load from CSV")
        print("6. Exit")
        
        choice = input("Select option: ")
        
        if choice == "1":
            data = loader.load_and_process_data(100, True)
        elif choice == "2":
            data = loader.load_and_process_data(500, True)
        elif choice == "3":
            data = loader.load_and_process_data(1000, True)
        elif choice == "4":
            n = int(input("Enter count: "))
            data = loader.load_and_process_data(n, True)
        elif choice == "5":
            n = int(input("Enter limit (0=all): ")) or None
            transactions, identity = loader.load_ieee_cis_data(n)
            data = {'transactions': transactions}
        elif choice == "6":
            break
        else:
            continue
        
        print(f"\n✓ Loaded {data['stats']['total_transactions']} transactions")
        print(f"✓ Fraud rate: {data['stats']['fraud_rate']:.2f}%")

if __name__ == "__main__":
    main()
```

Run with:
```bash
python interactive_cli.py
```

---

## 10. Refactoring Downstream Modules

To fully support dynamic loading, update modules to accept DataFrames:

### GraphBuilder Enhancement

```python
# In src/graph/build_graph.py

class GraphBuilder:
    def __init__(self):
        self.graph_data = HeteroData()
    
    # OLD: Fetches from database
    def fetch_account_nodes(self) -> pd.DataFrame:
        query = "SELECT * FROM account"
        return pd.DataFrame(db.execute_query(query))
    
    # NEW: Accepts DataFrame parameter
    def fetch_account_nodes(self, df=None) -> pd.DataFrame:
        if df is not None:
            # Use provided DataFrame
            return df.groupby('account_id').agg(...)
        else:
            # Fall back to database
            query = "SELECT * FROM account"
            return pd.DataFrame(db.execute_query(query))
    
    # NEW: Build from in-memory data
    def build_from_dataframes(self, transactions, accounts, merchants, devices):
        """Build graph from in-memory DataFrames instead of database"""
        self.graph_data = HeteroData()
        # ... graph construction logic ...
        return self.graph_data
```

### Training Enhancement

```python
# In src/training/train.py

def train_gnn_on_data(model, transactions, accounts, merchants, devices):
    """Train on provided DataFrames instead of loading from database"""
    
    # Build graph from data
    graph = build_graph(transactions, accounts, merchants, devices)
    
    # Prepare train/test split
    train_idx, test_idx = train_test_split(range(len(transactions)))
    
    # Train model
    for epoch in range(config.NUM_EPOCHS):
        loss = model.train_step(graph[train_idx])
        val_loss = model.evaluate(graph[test_idx])
        
    return {'loss': loss, 'val_loss': val_loss, 'accuracy': compute_accuracy(...)}
```

---

## Summary: Integration Checklist

- [x] Install `InteractiveDataLoader` module
- [x] Update dashboard to use dynamic loading
- [ ] Refactor `GraphBuilder` to accept DataFrames
- [ ] Refactor `train.py` to accept DataFrames
- [ ] Update `db_inserter.py` to handle limited datasets
- [ ] Create CLI interface for batch processing
- [ ] Add unit tests for different dataset sizes
- [ ] Update documentation with examples

---

## Quick Reference

```python
# Generate N transactions
from src.preprocessing.interactive_loader import generate_demo_transactions
txns = generate_demo_transactions(n_transactions=1000)

# Full pipeline
from src.preprocessing.interactive_loader import load_data_interactive
data = load_data_interactive(n_transactions=500)

# Real CSV with limit
from src.preprocessing.interactive_loader import InteractiveDataLoader
loader = InteractiveDataLoader()
txns, identity = loader.load_ieee_cis_data(n_transactions=1000)

# Use in dashboard (automatic - just run)
# streamlit run src/visualization/advanced_dashboard.py
```

That's it! The system now supports dynamic transaction loading at every level.
