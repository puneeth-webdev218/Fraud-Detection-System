# 🔍 Graph Neural Network–Based Fraud Detection System

## Project Overview
A comprehensive fraud detection system that combines database-driven transaction analysis with Graph Neural Networks (GNN) to identify fraudulent financial transactions by analyzing relationships between accounts, devices, and merchants.

## 🎯 Key Features
- **Database-Driven Architecture**: PostgreSQL-based storage for structured transaction data
- **Graph Neural Networks**: Advanced GNN models (GraphSAGE/GAT/R-GCN) for relational fraud detection
- **Real-time Analysis**: Fraud risk scoring and pattern detection
- **Interactive Dashboard**: Streamlit-based visualization and analytics
- **IEEE-CIS Dataset**: Using real-world anonymized transaction data

## 📊 Dataset
**IEEE-CIS Fraud Detection Dataset**
- Anonymized online transaction data
- User identity and device metadata
- Transaction amounts, card details, timestamps
- Fraud labels for supervised learning

## 🏗️ Project Structure
```
FRAUD/
├── data/                      # Raw and processed datasets
│   ├── raw/                   # Original IEEE-CIS data
│   └── processed/             # Cleaned and transformed data
├── database/                  # Database related files
│   ├── schema/                # SQL schema definitions
│   ├── migrations/            # Database migration scripts
│   └── queries/               # Common SQL queries
├── src/                       # Source code
│   ├── config/                # Configuration files
│   ├── database/              # Database connection & utilities
│   ├── preprocessing/         # Data cleaning & transformation
│   ├── graph/                 # Graph construction modules
│   ├── models/                # GNN model architectures
│   ├── training/              # Training & evaluation pipelines
│   └── visualization/         # Dashboard & plotting utilities
├── notebooks/                 # Jupyter notebooks for exploration
├── tests/                     # Unit and integration tests
├── docs/                      # Documentation
│   ├── ER_diagram.md          # Entity-Relationship diagram
│   └── graph_schema.md        # Graph structure documentation
├── checkpoints/               # Model checkpoints
├── logs/                      # Training and system logs
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md                  # This file
```

## 🗄️ Database Schema

### Core Tables
- **ACCOUNT**: User account metadata and risk profiles
- **MERCHANT**: Merchant information and categories
- **DEVICE**: Device records and metadata
- **TRANSACTION**: Transaction records with fraud labels
- **SHARED_DEVICE**: Device-sharing patterns between accounts

## 🔧 Technology Stack
| Component | Technology |
|-----------|-----------|
| Database | PostgreSQL |
| ML Framework | PyTorch, PyTorch Geometric |
| Graph Processing | NetworkX, DGL |
| Visualization | Streamlit, Plotly, Matplotlib |
| Data Processing | Pandas, NumPy |
| Environment | Python 3.9+ |

## 📋 Prerequisites
- Python 3.9 or higher
- PostgreSQL 13 or higher
- 8GB+ RAM recommended
- GPU (optional but recommended for training)

## 🚀 Quick Start

### 1. Clone and Setup Environment
```bash
cd FRAUD
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
```

### 2. Configure Database
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your PostgreSQL credentials
# Then create database
python src/database/setup_db.py
```

### 3. Load Data
```bash
# Download IEEE-CIS dataset (place in data/raw/)
# Then run preprocessing
python src/preprocessing/load_data.py
```

### 4. Build Graph
```bash
python src/graph/build_graph.py
```

### 5. Train Model
```bash
python src/training/train.py --config src/config/train_config.yaml
```

### 6. Launch Dashboard
```bash
streamlit run src/visualization/dashboard.py
```

## 📈 Evaluation Metrics
- **Precision**: Accuracy of fraud predictions
- **Recall**: Coverage of actual fraud cases
- **F1-Score**: Harmonic mean of precision and recall
- **ROC-AUC**: Area under ROC curve
- **Comparison**: Baseline vs GNN performance

## 🎯 Expected Outcomes
1. ✅ Functional PostgreSQL database with fraud transaction records
2. ✅ GNN-based fraud classification model
3. ✅ Interactive dashboard with:
   - Fraud cluster visualization
   - Risk score trends
   - Network relationship maps
   - Real-time transaction monitoring

## 📚 Documentation
- [Database Schema](docs/ER_diagram.md)
- [Graph Structure](docs/graph_schema.md)
- [Model Architecture](docs/model_architecture.md)
- [API Reference](docs/api_reference.md)

## 🤝 Contributing
This is an academic/research project. For modifications or improvements, please document your changes thoroughly.

## 📝 License
MIT License - See LICENSE file for details

## 👥 Authors
- Project for fraud detection research using GNNs

## 🔗 References
- IEEE-CIS Fraud Detection Dataset (Kaggle)
- PyTorch Geometric Documentation
- Graph Neural Networks for Fraud Detection (Research Papers)

---
**Status**: 🚧 Under Active Development
**Last Updated**: November 20, 2025
