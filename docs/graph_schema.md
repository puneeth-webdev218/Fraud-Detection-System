# 🕸️ Graph Schema Documentation

## Heterogeneous Graph Structure

This document describes the graph structure used for fraud detection with Graph Neural Networks (GNN).

---

## Graph Overview

The fraud detection system uses a **heterogeneous graph** with multiple node types and edge types to capture complex relationships between accounts, merchants, and devices.

### Node Types (3)
1. **Account Nodes** - User accounts
2. **Merchant Nodes** - Businesses/merchants
3. **Device Nodes** - Devices used for transactions

### Edge Types (3)
1. **account → merchant** (transacts_with)
2. **account → device** (uses)
3. **account ↔ device** (shares)

---

## Node Features

### Account Nodes

**Feature Vector Dimension:** 5

| Index | Feature | Type | Description | Preprocessing |
|-------|---------|------|-------------|---------------|
| 0 | risk_score | float | Account fraud risk (0-1) | Standardized |
| 1 | total_transactions | float | Total transaction count | Log-scaled + Standardized |
| 2 | total_amount | float | Total transaction amount | Log-scaled + Standardized |
| 3 | account_age_days | float | Account age in days | Log-scaled + Standardized |
| 4 | fraud_flag | binary | Has committed fraud | 0 or 1 |

**Label:** `fraud_flag` (binary classification target)

**Example:**
```python
# Access account features
account_features = graph['account'].x
# Shape: [num_accounts, 5]

# Access account labels
account_labels = graph['account'].y
# Shape: [num_accounts]
```

---

### Merchant Nodes

**Feature Vector Dimension:** 4

| Index | Feature | Type | Description | Preprocessing |
|-------|---------|------|-------------|---------------|
| 0 | fraud_rate | float | Merchant fraud rate (0-1) | Standardized |
| 1 | total_transactions | float | Total transactions processed | Log-scaled + Standardized |
| 2 | avg_transaction_amount | float | Average transaction value | Log-scaled + Standardized |
| 3 | risk_level_encoded | int | Risk level (0=LOW, 1=MED, 2=HIGH, 3=CRIT) | Encoded |

**Example:**
```python
merchant_features = graph['merchant'].x
# Shape: [num_merchants, 4]
```

---

### Device Nodes

**Feature Vector Dimension:** 5

| Index | Feature | Type | Description | Preprocessing |
|-------|---------|------|-------------|---------------|
| 0 | fraud_rate | float | Device fraud rate (0-1) | Standardized |
| 1 | total_users | float | Number of unique users | Log-scaled + Standardized |
| 2 | total_transactions | float | Total transactions | Log-scaled + Standardized |
| 3 | is_shared | binary | Used by multiple accounts | 0 or 1 |
| 4 | risk_score | float | Device risk score (0-1) | Standardized |

**Example:**
```python
device_features = graph['device'].x
# Shape: [num_devices, 5]
```

---

## Edge Features

### Transaction Edges (account → merchant)

**Type:** `('account', 'transacts_with', 'merchant')`

**Feature Vector Dimension:** 3

| Index | Feature | Type | Description | Preprocessing |
|-------|---------|------|-------------|---------------|
| 0 | transaction_amount | float | Transaction value | Log-scaled + Standardized |
| 1 | transaction_hour | int | Hour of day (0-23) | Standardized |
| 2 | transaction_day_of_week | int | Day of week (0-6) | Standardized |

**Edge Label:** `is_fraud` (binary - fraud or legitimate)

**Example:**
```python
# Access transaction edges
edge_index = graph['account', 'transacts_with', 'merchant'].edge_index
# Shape: [2, num_transactions]
# [0, :] = source (account indices)
# [1, :] = target (merchant indices)

# Access edge features
edge_features = graph['account', 'transacts_with', 'merchant'].edge_attr
# Shape: [num_transactions, 3]

# Access edge labels
edge_labels = graph['account', 'transacts_with', 'merchant'].edge_label
# Shape: [num_transactions]
```

---

### Device Usage Edges (account → device)

**Type:** `('account', 'uses', 'device')`

**Feature Vector Dimension:** 1

| Index | Feature | Type | Description | Preprocessing |
|-------|---------|------|-------------|---------------|
| 0 | transaction_amount | float | Transaction value | Log-scaled |

**Example:**
```python
edge_index = graph['account', 'uses', 'device'].edge_index
edge_features = graph['account', 'uses', 'device'].edge_attr
# Shape: [num_device_usage, 1]
```

---

### Shared Device Edges (account ↔ device)

**Type:** `('account', 'shares', 'device')`

**Feature Vector Dimension:** 2

| Index | Feature | Type | Description | Preprocessing |
|-------|---------|------|-------------|---------------|
| 0 | transaction_count | float | Number of transactions | Log-scaled |
| 1 | fraud_count | float | Number of fraud cases | Log-scaled |

**Note:** These edges are **bidirectional** (account→device and device→account)

**Example:**
```python
edge_index = graph['account', 'shares', 'device'].edge_index
edge_features = graph['account', 'shares', 'device'].edge_attr
# Shape: [num_shared_edges * 2, 2]  # Bidirectional
```

---

## Graph Statistics (Example)

Based on IEEE-CIS full dataset:

```
Node Types:
  • Accounts: ~290,000
  • Merchants: ~50
  • Devices: ~150,000

Edge Types:
  • Transactions: ~590,000
  • Device Usage: ~450,000
  • Shared Devices: ~80,000 (bidirectional)

Labels:
  • Fraud Accounts: ~10,000 (3.4%)
  • Fraud Transactions: ~20,000 (3.5%)

Feature Dimensions:
  • Account: 5
  • Merchant: 4
  • Device: 5
  • Transaction Edge: 3
  • Device Usage Edge: 1
  • Shared Device Edge: 2
```

---

## Graph Construction Process

### 1. Node ID Mapping

Each node type has a mapping from database IDs to graph indices:

```python
node_mappings = {
    'account': {'acc_1': 0, 'acc_2': 1, ...},
    'merchant': {'M_W': 0, 'M_C': 1, ...},
    'device': {'D_xyz': 0, 'D_abc': 1, ...}
}
```

**Saved to:** `data/processed/node_mappings.pkl`

### 2. Feature Normalization

All numerical features are:
1. **Log-scaled** (if needed): `log1p(x)` to handle large values
2. **Standardized**: `(x - mean) / std` to have mean=0, std=1
3. **Clipped**: Remove extreme outliers

Binary features (fraud_flag, is_shared) are kept as 0/1.

### 3. Edge Construction

**Transaction Edges:**
```python
# For each transaction:
src = account_mapping[account_id]
dst = merchant_mapping[merchant_id]
edge_index.append([src, dst])
```

**Device Usage Edges:**
```python
# For each transaction with device:
src = account_mapping[account_id]
dst = device_mapping[device_id]
edge_index.append([src, dst])
```

**Shared Device Edges (Bidirectional):**
```python
# For each shared device pair:
src = account_mapping[account_id]
dst = device_mapping[device_id]
edge_index.append([src, dst])  # account → device
edge_index.append([dst, src])  # device → account
```

---

## Message Passing Semantics

### GNN Message Passing

The heterogeneous graph enables different message passing schemes:

1. **Account aggregates from Merchants:**
   - Learn merchant fraud patterns
   - Aggregate transaction features
   
2. **Account aggregates from Devices:**
   - Learn device risk patterns
   - Detect shared device usage

3. **Bidirectional Device Sharing:**
   - Accounts share information through shared devices
   - Detect fraud rings using same devices

### Example Message Flow

```
    Merchant_A (high fraud)
          ↓ (transaction edge)
    Account_X  ←→  Device_Y (shared)
          ↓ (transaction edge)        ↑
    Merchant_B                   Account_Z
    
Account_X receives:
  - Fraud signals from Merchant_A
  - Shared device patterns from Account_Z via Device_Y
  - Risk information from Device_Y
```

---

## Graph Loading Example

```python
import torch
from pathlib import Path

# Load graph
graph = torch.load('data/processed/fraud_graph.pt')

# Access node features
account_x = graph['account'].x          # [N_acc, 5]
merchant_x = graph['merchant'].x        # [N_mer, 4]
device_x = graph['device'].x            # [N_dev, 5]

# Access labels
account_y = graph['account'].y          # [N_acc]

# Access edges
txn_edge_index = graph['account', 'transacts_with', 'merchant'].edge_index
txn_edge_attr = graph['account', 'transacts_with', 'merchant'].edge_attr
txn_edge_label = graph['account', 'transacts_with', 'merchant'].edge_label

# Print shapes
print(f"Accounts: {graph['account'].x.shape}")
print(f"Merchants: {graph['merchant'].x.shape}")
print(f"Devices: {graph['device'].x.shape}")
print(f"Transaction edges: {txn_edge_index.shape}")
```

---

## Graph Modifications for Training

### Train/Val/Test Split

```python
from torch_geometric.transforms import RandomNodeSplit

# Split account nodes
transform = RandomNodeSplit(
    split='train_rest',
    num_val=0.15,
    num_test=0.15
)

graph = transform(graph)

# Access masks
train_mask = graph['account'].train_mask
val_mask = graph['account'].val_mask
test_mask = graph['account'].test_mask
```

### Edge-Level Tasks

For transaction fraud detection (edge classification):

```python
# Get transaction edge labels
edge_labels = graph['account', 'transacts_with', 'merchant'].edge_label

# Split edges for training
num_edges = edge_labels.shape[0]
train_edges = num_edges * 0.7
val_edges = num_edges * 0.15
test_edges = num_edges * 0.15
```

---

## Design Decisions

### Why Heterogeneous Graph?

1. **Different Entity Types**: Accounts, merchants, and devices have different features
2. **Relationship Semantics**: Different edge types capture different relationships
3. **Expressive Power**: GNN can learn type-specific transformations
4. **Scalability**: Can extend with new node/edge types easily

### Why These Features?

**Account Features:**
- `risk_score`: Direct fraud indicator
- `total_transactions`, `total_amount`: Activity patterns
- `account_age_days`: Account maturity
- `fraud_flag`: Ground truth label

**Merchant Features:**
- `fraud_rate`: Merchant reputation
- `total_transactions`: Merchant popularity
- `avg_transaction_amount`: Merchant price range
- `risk_level`: Categorical risk indicator

**Device Features:**
- `fraud_rate`: Device risk
- `total_users`: Sharing indicator
- `is_shared`: Direct sharing flag
- `risk_score`: Computed risk

### Why Log-Scaling?

Transaction amounts and counts have **heavy-tailed distributions**:
- Most transactions: $10-$100
- Some transactions: $10,000+

Log-scaling: `log1p(x) = log(1 + x)` makes distributions more normal and prevents large values from dominating.

### Why Standardization?

Different features have different scales:
- risk_score: [0, 1]
- total_amount: [0, millions]

Standardization ensures all features contribute equally to GNN learning.

---

## Extending the Graph

### Adding New Node Types

```python
# Example: Add Card node type
data['card'].x = card_features
data['account', 'owns', 'card'].edge_index = ownership_edges
```

### Adding New Edge Types

```python
# Example: Add merchant-merchant similarity
data['merchant', 'similar_to', 'merchant'].edge_index = similarity_edges
```

### Adding New Features

```python
# Example: Add temporal features
account_features_extended = torch.cat([
    data['account'].x,
    temporal_features
], dim=1)
```

---

## Performance Considerations

### Memory Usage

**Full Graph:**
- Nodes: ~290K accounts + 50 merchants + 150K devices ≈ 440K nodes
- Edges: ~1.2M edges
- Features: ~440K × 5 float32 values ≈ 9MB
- Total: ~50MB for graph + features

**Optimization:**
- Use `torch.half()` for 16-bit floats (half memory)
- Use mini-batch sampling for large graphs
- Store on GPU if available

### Graph Sampling

For large graphs, use neighbor sampling:

```python
from torch_geometric.loader import NeighborLoader

loader = NeighborLoader(
    graph,
    num_neighbors=[10, 5],  # 2-hop sampling
    batch_size=128,
    input_nodes=('account', train_mask)
)
```

---

## Visualization

### NetworkX Export

```python
import networkx as nx

# Convert to NetworkX (for small subgraphs)
G = nx.DiGraph()

# Add nodes
for i in range(num_accounts):
    G.add_node(f"acc_{i}", type='account')

# Add edges
edge_index = graph['account', 'transacts_with', 'merchant'].edge_index
for i in range(edge_index.shape[1]):
    src, dst = edge_index[:, i]
    G.add_edge(f"acc_{src}", f"mer_{dst}")

# Visualize
import matplotlib.pyplot as plt
nx.draw(G, with_labels=True)
plt.show()
```

---

## Files Generated

```
data/processed/
├── fraud_graph.pt          # Main graph file (HeteroData)
├── node_mappings.pkl       # ID to index mappings
└── graph_stats.pkl         # Graph statistics

# Load files
import torch
import pickle

graph = torch.load('data/processed/fraud_graph.pt')

with open('data/processed/node_mappings.pkl', 'rb') as f:
    mappings = pickle.load(f)

with open('data/processed/graph_stats.pkl', 'rb') as f:
    stats = pickle.load(f)
```

---

## References

- PyTorch Geometric Documentation: https://pytorch-geometric.readthedocs.io/
- Heterogeneous Graphs: https://arxiv.org/abs/1903.07293
- Graph Neural Networks: https://arxiv.org/abs/1901.00596

---

**Last Updated:** November 20, 2025
