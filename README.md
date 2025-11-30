# 🔍 Fraud Detection System - Graph Neural Networks

## Project Overview
A comprehensive fraud detection system that combines database-driven transaction analysis with Graph Neural Networks (GNN) to identify fraudulent financial transactions by analyzing relationships between accounts, devices, and merchants.

## 🎯 Key Features
- **Interactive Dashboard**: Real-time fraud monitoring with Streamlit
- **Dynamic Data Loading**: Load N transactions at runtime without code changes
- **Real IEEE-CIS Dataset**: Support for real-world fraud detection data
- **Graph Neural Networks**: Advanced GNN models (GraphSAGE/GAT/R-GCN)
- **Multi-Page Analytics**: 7 specialized analysis dashboards
- **Automatic Fallback**: Seamless transition to synthetic data if real data unavailable
- **Two-Phase Pipeline**: Live ML → Database integration demo (NEW) ⭐
- **Dual-Table Architecture**: Separate tables for raw data and predictions (NEW) ⭐⭐

---

## 🎯 Two-Table Workflow (LATEST - Most Important Feature!)

**The system now uses TWO separate database tables to demonstrate a clear ML pipeline:**

### Phase 1: Load Transactions (Raw Data)
```
Button: "📤 Load Transactions (Phase 1)"
↓
Action: Insert raw transactions to 'transactions' table
↓
Schema: 7 columns (NO status)
┌─────────────────────────────────┐
│ transactions Table (RAW)        │
├─────────────────────────────────┤
│ • transaction_id (BIGINT PK)   │
│ • account_id (INTEGER)         │
│ • merchant_id (INTEGER)        │
│ • device_id (INTEGER)          │
│ • amount (DECIMAL)             │
│ • timestamp (TIMESTAMP)        │
│ • fraud_flag (BOOLEAN)         │
│ → NO status column yet         │
└─────────────────────────────────┘
Console: "✅ PHASE 1 COMPLETE — X raw transactions stored"
```

### Phase 2: Do Predictions (ML Processing)
```
Button: "🧠 Do Predictions (Phase 2)"
↓
Action: Run GNN analysis & insert to 'fraud_predictions' table
↓
Schema: 8 columns (WITH status)
┌─────────────────────────────────┐
│ fraud_predictions Table (GNN)   │
├─────────────────────────────────┤
│ • transaction_id (BIGINT PK)   │
│ • account_id (INTEGER)         │
│ • merchant_id (INTEGER)        │
│ • device_id (INTEGER)          │
│ • amount (DECIMAL)             │
│ • timestamp (TIMESTAMP)        │
│ • fraud_flag (BOOLEAN)         │
│ • status (VARCHAR) ← NEW! ✓    │
│   (FRAUD or OK)               │
└─────────────────────────────────┘
Console: "✅ PHASE 2 COMPLETE — X predictions saved"
```

### Why Two Tables?

| Aspect | Single Table (Old) | Dual Table (New) |
|--------|-------------------|-----------------|
| **Clarity** | ❌ Status appears suddenly | ✅ Phase 1 shows raw, Phase 2 shows enriched |
| **Workflow** | ❌ Unclear what's happening | ✅ Crystal clear ML pipeline |
| **Education** | ❌ Hard to understand | ✅ Perfect for learning |
| **pgAdmin** | ❌ One table, confusing | ✅ Two separate tables, easy to understand |
| **Data Auditing** | ❌ Original data lost | ✅ Both versions available |

**In pgAdmin, you'll see:**
```
Databases → postgres → Schemas → public → Tables
├── transactions       (7 columns, raw data, NO status)
└── fraud_predictions  (8 columns, with status = FRAUD/OK)
```

### Getting Started with Two-Table Workflow

1. **Start Dashboard:**
   ```bash
   streamlit run src/visualization/advanced_dashboard.py
   ```

2. **Load Demo Data:**
   - Sidebar → "Generate Demo Data" → Enter 1000 → Click button

3. **Phase 1 - Load Raw Transactions:**
   - Click "📤 Load Transactions (Phase 1)"
   - ✅ Check console: `"PHASE 1 COMPLETE — 1000 raw transactions stored"`
   - ✅ Check pgAdmin: `transactions` table (7 columns)

4. **Phase 2 - Run GNN Predictions:**
   - Click "🧠 Do Predictions (Phase 2)"
   - ✅ Check console: `"PHASE 2 COMPLETE — 1000 predictions saved"`
   - ✅ Check pgAdmin: `fraud_predictions` table (8 columns with status)

5. **Verify Both Tables in pgAdmin:**
   ```sql
   -- See Phase 1 data (raw)
   SELECT * FROM transactions LIMIT 5;
   
   -- See Phase 2 data (predictions)
   SELECT * FROM fraud_predictions LIMIT 5;
   
   -- Compare fraud counts
   SELECT 
     (SELECT COUNT(*) FROM fraud_predictions WHERE status='FRAUD') as predicted_fraud,
     (SELECT COUNT(*) FROM fraud_predictions WHERE status='OK') as predicted_ok;
   ```

**📖 Full Documentation:**
- **Quick Start**: [QUICKSTART_TWODATA.md](QUICKSTART_TWODATA.md)
- **Architecture**: [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)
- **Detailed Summary**: [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)
- **Completion Report**: [TWO_TABLE_COMPLETION.md](TWO_TABLE_COMPLETION.md)

---

## 🎯 Original Two-Phase Pipeline (Previous Implementation)

The system still features a **Two-Phase Pipeline** demonstrating ML → Database integration:

```
Phase 1: Raw Data → PostgreSQL (immediate insertion)
         ↓
Phase 2: GNN Processing → Status Update (enrichment after processing)
```

**See it in action:**
```bash
streamlit run src/visualization/advanced_dashboard.py
```
Click "Load Real IEEE-CIS Data" → Watch Phase 1 and Phase 2 execute in real-time!

📖 **Documentation**: See [TWO_PHASE_PIPELINE.md](TWO_PHASE_PIPELINE.md) and [TWO_PHASE_VISUAL_GUIDE.md](TWO_PHASE_VISUAL_GUIDE.md)

---
**IEEE-CIS Fraud Detection Dataset**
- 590,540 anonymized transactions
- 144,233 identity records
- User accounts, merchants, devices, and fraud labels
- Real-world fraud patterns and relationships

## 🏗️ Project Structure
```
DRAGNN-FraudDB/
├── data/                          # Dataset storage
│   ├── raw/                       # IEEE-CIS CSV files
│   └── processed/                 # Processed data
├── src/
│   ├── config/                    # Configuration
│   ├── database/                  # Database utilities
│   ├── preprocessing/
│   │   ├── interactive_loader.py  # Dynamic data loading ⭐ NEW
│   │   └── data_loader.py
│   ├── graph/                     # Graph construction
│   ├── models/                    # GNN models
│   ├── training/                  # Training pipelines
│   └── visualization/
│       ├── advanced_dashboard.py  # Main dashboard ⭐ NEW
│       └── simple_dashboard.py
├── docs/                          # Documentation
├── DATASET_SETUP.md              # Dataset configuration guide ⭐ NEW
├── START_HERE.md                 # Quick start guide ⭐ NEW
├── DYNAMIC_LOADING_FEATURE.md    # Feature documentation ⭐ NEW
└── requirements.txt
```

## 🎯 Quick Start

### Option 1: Using Real Dataset
1. Download from: https://www.kaggle.com/c/ieee-fraud-detection/data
2. Extract `train_transaction.csv` and `train_identity.csv` to `data/raw/`
3. Run dashboard:
   ```bash
   streamlit run src/visualization/advanced_dashboard.py
   ```
4. Click "Load Real IEEE-CIS Data" and select transaction count

### Option 2: Using Demo
```bash
python run_demo.py
```

## 📈 Dashboard Features

### 📊 Dashboard Overview
- Real-time metrics (total transactions, fraud rate)
- Fraud distribution pie chart
- Transaction amount statistics

### ⚠️ High-Risk Accounts
- Risk scoring algorithm
- Top fraudulent accounts
- Transaction patterns

### 📈 Fraud Trends
- Daily fraud rates
- Temporal patterns
- Trend visualization

### 🏪 Merchant Analysis
- Merchant fraud statistics
- High-risk merchants
- Transaction volumes

### 🖥️ Device Intelligence
- Device sharing patterns
- Multi-account detection
- Device-based fraud insights

### 🔎 Transaction Search
- Filter by account, merchant, device
- Detailed transaction lookup
- Fraud probability scoring

### ⚙️ Settings & Help
- Feature documentation
- System information
- Configuration options

## 💻 Dynamic Transaction Loading

**Load any number of transactions at runtime without code changes!**

```bash
streamlit run src/visualization/advanced_dashboard.py
```

In the sidebar:
- Enter desired row count (10-590,000)
- Click "Load Real IEEE-CIS Data"
- All pages instantly update

**Example:**
- Load 1,000 rows: ~2 seconds
- Load 10,000 rows: ~5 seconds
- Load 50,000 rows: ~20 seconds

## 🔧 Technology Stack
| Component | Technology |
|-----------|-----------|
| Framework | Streamlit, PyTorch |
| Graph Processing | PyTorch Geometric, NetworkX |
| Data | Pandas, NumPy |
| Visualization | Plotly, Matplotlib |
| Database | PostgreSQL (optional) |

## 📚 Documentation
- [START_HERE.md](START_HERE.md) - Entry point for new users
- [DATASET_SETUP.md](DATASET_SETUP.md) - Dataset configuration
- [DYNAMIC_LOADING_FEATURE.md](DYNAMIC_LOADING_FEATURE.md) - Feature details
- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - Integration examples
- [QUICK_START_DYNAMIC_LOADING.md](QUICK_START_DYNAMIC_LOADING.md) - Quick reference
- [TWO_PHASE_PIPELINE.md](TWO_PHASE_PIPELINE.md) - Two-phase pipeline guide (NEW) ⭐
- [TWO_PHASE_VISUAL_GUIDE.md](TWO_PHASE_VISUAL_GUIDE.md) - Visual diagrams (NEW) ⭐
- [TWO_PHASE_IMPLEMENTATION_SUMMARY.md](TWO_PHASE_IMPLEMENTATION_SUMMARY.md) - Implementation details (NEW) ⭐

## 🚀 Usage Examples

### Python Integration
```python
from src.preprocessing.interactive_loader import InteractiveDataLoader

loader = InteractiveDataLoader()

# Load 5,000 real transactions
transactions, identity = loader.load_ieee_cis_data(n_transactions=5000)

# Load 1,000 synthetic (demo)
demo_data = loader.generate_synthetic_transactions(1000)
```

### Dashboard
```bash
# Start dashboard
streamlit run src/visualization/advanced_dashboard.py

# Then in UI:
# 1. Set row count in sidebar
# 2. Click "Load Real IEEE-CIS Data"
# 3. Explore 7 analysis pages
```

## ✨ Recent Enhancements
✅ Dynamic transaction loading feature  
✅ Real IEEE-CIS dataset support  
✅ Column standardization for real data  
✅ 7-page interactive dashboard  
✅ Automatic synthetic fallback  
✅ Comprehensive documentation  

## 📊 Project Status
- **Dashboard**: ✅ Fully functional
- **Real Data Loading**: ✅ Working
- **Dynamic Features**: ✅ Implemented
- **GNN Models**: 🚧 In development
- **Database Integration**: 🚧 In development

## 🤝 Contributing
This is an academic/research project. For improvements, please:
1. Document changes thoroughly
2. Test with both synthetic and real data
3. Update relevant documentation

## 📝 License
MIT License - See LICENSE file for details

## 👥 Authors & Contact
Puneeth Nagaraj
- GitHub: https://github.com/puneeth-webdev218

## 🔗 References
- IEEE-CIS Fraud Detection Dataset (Kaggle)
- PyTorch Geometric Documentation
- Streamlit Documentation

---
**Last Updated**: November 30, 2025  
**Status**: 🚀 Production Ready (Dashboard & Data Loading)
