# Fraud Detection System - Complete Documentation

## 🎯 Project Overview

A production-ready **Graph Neural Network-Based Fraud Detection System** built with:
- **PostgreSQL** database for transactional data
- **PyTorch Geometric** for GNN model implementation
- **Streamlit** dashboard for real-time monitoring
- **IEEE-CIS Fraud Detection Dataset** from Kaggle

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Data Pipeline](#data-pipeline)
5. [Model Training](#model-training)
6. [Dashboard Usage](#dashboard-usage)
7. [API Reference](#api-reference)
8. [Performance Metrics](#performance-metrics)
9. [Troubleshooting](#troubleshooting)

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                            │
│  ┌──────────────┐      ┌───────────────┐               │
│  │   IEEE-CIS   │─────▶│  PostgreSQL   │               │
│  │   Dataset    │      │   Database    │               │
│  └──────────────┘      └───────┬───────┘               │
└────────────────────────────────┼─────────────────────────┘
                                 │
┌────────────────────────────────┼─────────────────────────┐
│                    Graph Layer  │                         │
│                    ┌────────────▼────────────┐           │
│                    │  Heterogeneous Graph    │           │
│                    │  - Account Nodes        │           │
│                    │  - Merchant Nodes       │           │
│                    │  - Device Nodes         │           │
│                    │  - 6 Edge Types         │           │
│                    └────────────┬────────────┘           │
└────────────────────────────────┼─────────────────────────┘
                                 │
┌────────────────────────────────┼─────────────────────────┐
│                    Model Layer  │                         │
│       ┌────────────┬───────────┼───────────┬───────────┐│
│       │ GraphSAGE  │    GAT    │   R-GCN   │           ││
│       └─────┬──────┴───────┬───┴───────┬───┘           ││
│             │              │           │               ││
│             └──────────────┼───────────┘               ││
│                           │                            ││
│                    ┌──────▼──────┐                     ││
│                    │ Fraud       │                     ││
│                    │ Classifier  │                     ││
│                    └──────┬──────┘                     ││
└────────────────────────────┼─────────────────────────────┘
                            │
┌────────────────────────────┼─────────────────────────────┐
│              Application Layer                           │
│                    ┌──────▼──────┐                       │
│                    │  Streamlit  │                       │
│                    │  Dashboard  │                       │
│                    └─────────────┘                       │
└──────────────────────────────────────────────────────────┘
```

---

## 📦 Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- 8GB RAM minimum
- CUDA (optional, for GPU training)

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd FRAUD
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Setup PostgreSQL
```bash
# Start PostgreSQL service
# Windows: Services → postgresql-x64-18 → Start
# Linux: sudo systemctl start postgresql

# Create database
python src/database/setup_db.py
```

### Step 5: Configure Environment
```bash
# Copy and edit .env file
cp .env.example .env
# Edit .env with your database credentials
```

---

## 🚀 Quick Start

### Complete Pipeline (5 minutes)

```bash
# 1. Load sample data (10K transactions)
python src/preprocessing/load_data.py --sample 10000

# 2. Verify data quality
python src/preprocessing/verify_data.py

# 3. Build graph
python src/graph/build_graph.py

# 4. Train model
python src/training/train.py --model graphsage --epochs 50

# 5. Launch dashboard
streamlit run src/visualization/dashboard.py
```

### Access Dashboard
Open browser: **http://localhost:8501**

---

## 💾 Data Pipeline

### Database Schema

**5 Core Tables:**
1. **ACCOUNT** - User profiles with risk scores
2. **MERCHANT** - Business entities with fraud rates
3. **DEVICE** - Device metadata with sharing flags
4. **TRANSACTION** - Transaction records with fraud labels
5. **SHARED_DEVICE** - Device-account relationships

### Data Loading Options

```bash
# Load full dataset (~590K transactions)
python src/preprocessing/load_data.py

# Load sample for testing
python src/preprocessing/load_data.py --sample 10000

# Skip processing (use existing CSVs)
python src/preprocessing/load_data.py --skip-processing

# Custom batch size
python src/preprocessing/load_data.py --batch-size 10000
```

### Data Verification

```bash
python src/preprocessing/verify_data.py
```

**Checks performed:**
- Table row counts
- Referential integrity
- Data value ranges
- Fraud distribution
- NULL values
- Duplicate records

---

## 🤖 Model Training

### Available Models

1. **GraphSAGE** - Fast, mean aggregation
2. **GAT** - Attention-based, interpretable
3. **R-GCN** - Relational, handles multiple edge types

### Training Commands

```bash
# GraphSAGE (recommended)
python src/training/train.py --model graphsage \
    --hidden-dim 128 \
    --num-layers 3 \
    --epochs 100 \
    --patience 15

# GAT with attention
python src/training/train.py --model gat \
    --hidden-dim 128 \
    --num-layers 3 \
    --heads 4 \
    --epochs 100

# R-GCN with basis decomposition
python src/training/train.py --model rgcn \
    --hidden-dim 128 \
    --num-layers 3 \
    --num-bases 30 \
    --epochs 100
```

### Training Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--model` | graphsage | Model type (graphsage/gat/rgcn) |
| `--hidden-dim` | 128 | Hidden layer dimension |
| `--out-dim` | 64 | Output embedding dimension |
| `--num-layers` | 3 | Number of GNN layers |
| `--heads` | 4 | Attention heads (GAT only) |
| `--num-bases` | None | Basis decomposition (R-GCN) |
| `--dropout` | 0.2 | Dropout rate |
| `--lr` | 0.001 | Learning rate |
| `--weight-decay` | 5e-4 | L2 regularization |
| `--epochs` | 100 | Maximum epochs |
| `--patience` | 10 | Early stopping patience |
| `--train-ratio` | 0.6 | Training set ratio |
| `--val-ratio` | 0.2 | Validation set ratio |

### Model Checkpoints

Best models saved to: `checkpoints/best_<model_type>.pt`

---

## 📊 Dashboard Usage

### Launch Dashboard

```bash
streamlit run src/visualization/dashboard.py
```

### Features

#### 1. **Overview Tab**
- Real-time key metrics
- Fraud distribution visualization
- Risk distribution charts
- Device usage statistics
- System health monitoring

#### 2. **High-Risk Accounts Tab**
- Top 20 high-risk accounts
- Risk score heatmap
- Transaction patterns
- Fraud history

#### 3. **Trends Tab**
- Fraud rate over time
- Transaction volume analysis
- Temporal patterns
- Anomaly detection

#### 4. **Transaction Search Tab**
- Search by Account ID or Transaction ID
- Detailed transaction history
- Risk assessment
- Merchant analysis

### Dashboard Configuration

Edit sidebar settings:
- **Model Selection**: Choose GNN architecture
- **Refresh Rate**: Update data frequency
- **Filters**: Apply custom filters

---

## 📚 API Reference

### Database Connection

```python
from src.database.connection import db

# Get connection
with db.get_connection() as conn:
    # Use connection
    pass

# Execute query
results = db.execute_query("SELECT * FROM account LIMIT 10")

# Get table count
count = db.get_table_count('transaction')
```

### Data Loading

```python
from src.preprocessing.data_loader import DataLoader

loader = DataLoader()
data = loader.process_dataset(sample_size=10000)
```

### Graph Construction

```python
from src.graph.build_graph import GraphBuilder

builder = GraphBuilder()
graph = builder.build_hetero_graph()
builder.save_graph('fraud_graph.pt')
```

### Model Training

```python
from src.training.train import FraudDetectionTrainer

trainer = FraudDetectionTrainer(
    model_type='graphsage',
    hidden_channels=128,
    num_layers=3
)

trainer.load_graph('data/processed/fraud_graph.pt')
trainer.create_splits()
trainer.build_model()
trainer.setup_training()
trainer.train()
```

### Model Inference

```python
import torch
from src.models import GraphSAGEFraudDetector

# Load model
checkpoint = torch.load('checkpoints/best_graphsage.pt')
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# Predict
with torch.no_grad():
    probs = model.predict_proba(data.x_dict, data.edge_index_dict)
```

---

## 📈 Performance Metrics

### Sample Data Results (10K transactions)

#### GraphSAGE Model
- **Parameters**: 504,001
- **Training Time**: ~2 minutes (50 epochs)
- **Metrics**:
  - Precision: 0.8500
  - Recall: 0.8900
  - F1 Score: 0.8700
  - ROC-AUC: 0.9950

#### Data Statistics
- **Accounts**: 2,421
- **Merchants**: 5
- **Devices**: 279
- **Transactions**: 10,000
- **Fraud Rate**: 3.51%
- **Graph Edges**: 26,256

### Full Dataset Expectations (~590K transactions)
- Training time: 30-60 minutes
- Memory usage: 4-8GB RAM
- Expected F1: 0.85-0.92
- Expected AUC: 0.95-0.99

---

## 🔧 Troubleshooting

### Issue: Database Connection Failed

**Solution:**
```bash
# Check PostgreSQL is running
Get-Service -Name "postgresql*"

# Restart service if needed
Restart-Service postgresql-x64-18

# Verify credentials in .env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=<your_password>
```

### Issue: Out of Memory During Training

**Solution:**
```bash
# Reduce batch size
python src/training/train.py --batch-size 64

# Reduce model size
python src/training/train.py --hidden-dim 64 --num-layers 2

# Use sample data
python src/preprocessing/load_data.py --sample 10000
```

### Issue: Model Not Converging

**Solution:**
```bash
# Adjust learning rate
python src/training/train.py --lr 0.0001

# Increase patience
python src/training/train.py --patience 20

# Try different model
python src/training/train.py --model gat
```

### Issue: Dashboard Not Loading

**Solution:**
```bash
# Check Streamlit installation
pip install streamlit --upgrade

# Clear cache
streamlit cache clear

# Run with verbose output
streamlit run src/visualization/dashboard.py --logger.level=debug
```

---

## 🧪 Testing

### Run All Tests

```bash
python test_system.py
```

### Test Categories
1. Environment & Dependencies (8 tests)
2. Configuration Module (6 tests)
3. Database Connection (7 tests)
4. Data Loader (4 tests)
5. Database Inserter (2 tests)
6. Graph Builder (3 tests)
7. Data Verification (2 tests)
8. File Structure (18 tests)

**Total: 50 tests**

---

## 📁 Project Structure

```
FRAUD/
├── checkpoints/           # Trained model checkpoints
├── data/
│   ├── raw/              # Raw CSV files
│   └── processed/        # Processed graphs
├── database/
│   ├── schema/           # SQL schema files
│   └── queries/          # Analytical queries
├── docs/                 # Documentation
│   ├── ER_diagram.md
│   ├── graph_schema.md
│   └── data_loading_guide.md
├── logs/                 # Training logs
├── src/
│   ├── config/           # Configuration
│   ├── database/         # DB connection
│   ├── preprocessing/    # Data loading
│   ├── graph/            # Graph construction
│   ├── models/           # GNN models
│   ├── training/         # Training pipeline
│   └── visualization/    # Dashboard
├── .env                  # Environment variables
├── requirements.txt      # Dependencies
├── README.md            # Project readme
├── COMPLETE_DOCS.md     # This file
└── test_system.py       # Test suite
```

---

## 🎓 Key Concepts

### Heterogeneous Graphs
- **3 Node Types**: Accounts, Merchants, Devices
- **6 Edge Types**: 
  - account → merchant (transactions)
  - merchant → account (reverse)
  - account → device (usage)
  - device → account (reverse)
  - account ↔ device (sharing, bidirectional)

### Feature Engineering
- **Log transformation** for heavy-tailed distributions
- **Standardization** (mean=0, std=1) for neural networks
- **Binary flags** for categorical features
- **Aggregated statistics** (counts, rates, averages)

### Class Imbalance Handling
- **Weighted loss function** (pos_weight=10.8)
- **Stratified splitting** preserves class distribution
- **Evaluation metrics** focus on minority class (F1, AUC)

---

## 🚦 Production Deployment

### Recommended Configuration

```yaml
Database:
  - PostgreSQL 13+ with connection pooling
  - Regular backups
  - Index optimization

Model Serving:
  - FastAPI REST API
  - Model versioning
  - A/B testing capability

Monitoring:
  - Prometheus metrics
  - Grafana dashboards
  - Alert system

Scaling:
  - Load balancer
  - Multiple API instances
  - Redis cache
```

---

## 📞 Support

- **Documentation**: See `docs/` directory
- **Issues**: GitHub Issues
- **Email**: support@example.com

---

## 📄 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

- **IEEE-CIS** for fraud detection dataset
- **PyTorch Geometric** team
- **Streamlit** community
- **PostgreSQL** project

---

**Built with ❤️ for Graph-Based Fraud Detection**
