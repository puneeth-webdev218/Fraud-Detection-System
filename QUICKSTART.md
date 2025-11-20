# 🚀 Quick Start Guide

This guide will help you get the Fraud Detection System up and running quickly.

---

## ⚡ Quick Installation (5 Steps)

### **Step 1: Create & Activate Virtual Environment**

```powershell
# Navigate to project
cd C:\Users\Pavan\FRAUD

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **Step 2: Install Dependencies**

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install PyTorch (CPU version)
pip install torch torchvision torchaudio

# Install PyTorch Geometric
pip install torch-scatter torch-sparse torch-cluster -f https://data.pyg.org/whl/torch-2.1.0+cpu.html
pip install torch-geometric

# Install other dependencies
pip install -r requirements.txt
```

⏱️ **Estimated time: 5-10 minutes**

### **Step 3: Configure Environment**

```powershell
# Copy environment template
cp .env.example .env

# Edit with your PostgreSQL password
# Use notepad or any text editor
notepad .env
```

**Update these values in `.env`:**
```
DB_PASSWORD=your_postgres_password
KAGGLE_USERNAME=your_username  # Optional
KAGGLE_KEY=your_api_key  # Optional
```

### **Step 4: Setup Database**

```powershell
# Make sure PostgreSQL is running
Get-Service postgresql*

# If not running, start it:
# Start-Service postgresql-x64-13

# Create database and tables
python src/database/setup_db.py
```

**Expected Output:**
```
✓ Database 'fraud_detection' created successfully
✓ All tables created successfully
```

### **Step 5: Verify Installation**

```powershell
# Run verification script
python verify_setup.py
```

**You should see:**
```
✓ All tests passed! System is ready.
```

---

## 📊 Download Dataset

### **Option A: Kaggle CLI (Faster)**

```powershell
# Configure Kaggle (one-time setup)
mkdir $env:USERPROFILE\.kaggle
# Place your kaggle.json in C:\Users\<YourName>\.kaggle\

# Download dataset
kaggle competitions download -c ieee-fraud-detection -p data/raw/

# Extract files
cd data/raw
Expand-Archive -Path ieee-fraud-detection.zip -DestinationPath .
```

### **Option B: Manual Download**

1. Visit: https://www.kaggle.com/c/ieee-fraud-detection/data
2. Download: `train_transaction.csv` and `train_identity.csv`
3. Place in: `C:\Users\Pavan\FRAUD\data\raw\`

---

## 🎯 Next Steps

Once setup is complete, you can proceed with:

### **1. Load Data into Database**
```powershell
python src/preprocessing/load_data.py
```
This will:
- Read CSV files
- Clean and transform data
- Load into PostgreSQL tables
- Create indexes

⏱️ **Time: 10-20 minutes depending on dataset size**

### **2. Build Graph Structure**
```powershell
python src/graph/build_graph.py
```
This will:
- Extract data from database
- Create heterogeneous graph
- Save graph structure

⏱️ **Time: 5-10 minutes**

### **3. Train GNN Model**
```powershell
python src/training/train.py
```
This will:
- Load graph data
- Train GNN model
- Evaluate performance
- Save checkpoints

⏱️ **Time: 30-60 minutes (depends on hardware)**

### **4. Launch Dashboard**
```powershell
streamlit run src/visualization/dashboard.py
```
Opens interactive dashboard at: http://localhost:8501

---

## 🔍 Quick Checks

### Check Database Tables
```powershell
python -c "from src.database.connection import db; print(db.get_table_count('transaction'))"
```

### Check Configuration
```powershell
python -c "from src.config.config import config; config.print_config()"
```

### Test Database Connection
```powershell
python -c "from src.database.connection import db; db.test_connection()"
```

---

## 📁 Project Structure Overview

```
FRAUD/
├── data/
│   ├── raw/              ← Place IEEE-CIS dataset here
│   └── processed/        ← Processed data (auto-generated)
├── database/
│   ├── schema/           ← SQL table definitions
│   └── queries/          ← Analytical queries
├── src/
│   ├── config/           ← Configuration management
│   ├── database/         ← DB connection & utilities
│   ├── preprocessing/    ← Data cleaning & loading
│   ├── graph/            ← Graph construction
│   ├── models/           ← GNN models
│   ├── training/         ← Training pipeline
│   └── visualization/    ← Dashboard & plots
├── checkpoints/          ← Model checkpoints
├── logs/                 ← System logs
└── docs/                 ← Documentation
```

---

## 🐛 Common Issues & Quick Fixes

### Issue: "Cannot import module 'src'"
```powershell
# Solution: Install in development mode
pip install -e .
```

### Issue: "psycopg2 not found"
```powershell
# Solution: Install binary version
pip install psycopg2-binary
```

### Issue: "torch-scatter installation failed"
```powershell
# Solution: Use PyG wheel URL
pip install torch-scatter -f https://data.pyg.org/whl/torch-2.1.0+cpu.html
```

### Issue: "Database connection refused"
```powershell
# Check if PostgreSQL is running
Get-Service postgresql*

# Start if needed
Start-Service postgresql-x64-13
```

---

## 📚 Learn More

- **Full Installation Guide**: See `docs/INSTALL.md`
- **Database Schema**: See `docs/ER_diagram.md`
- **Graph Structure**: See `docs/graph_schema.md`
- **API Documentation**: Coming soon

---

## ✅ Pre-flight Checklist

Before proceeding with data loading:

- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] `.env` file configured
- [ ] PostgreSQL running
- [ ] Database created (run `setup_db.py`)
- [ ] Tables exist (5 tables: account, merchant, device, transaction, shared_device)
- [ ] Dataset downloaded to `data/raw/`
- [ ] Verification script passes all tests

---

## 🎓 Workflow Summary

```
1. Setup Environment
   ↓
2. Create Database
   ↓
3. Download Dataset
   ↓
4. Load Data → PostgreSQL
   ↓
5. Build Graph
   ↓
6. Train GNN Model
   ↓
7. Evaluate & Visualize
```

---

## 💡 Tips

- **Use GPU**: If available, update PyTorch installation for CUDA support
- **Monitor Resources**: Database loading can be memory-intensive
- **Check Logs**: All operations log to `logs/` directory
- **Incremental Testing**: Verify each step before proceeding
- **Backup Data**: Keep original CSV files safe

---

**Ready to start?** Run: `python verify_setup.py` ✨

**Need help?** Check `docs/INSTALL.md` for detailed troubleshooting.

---

**Last Updated:** November 20, 2025
