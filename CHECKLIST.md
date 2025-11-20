# ✅ Setup Checklist

Use this checklist to track your progress through the setup process.

---

## Phase 1: Environment Setup ⚙️

- [ ] **Python 3.9+ installed**
  - Run: `python --version`
  - Should show: Python 3.9 or higher

- [ ] **Virtual environment created**
  - Run: `python -m venv venv`
  - Directory `venv/` should exist

- [ ] **Virtual environment activated**
  - Run: `.\venv\Scripts\Activate.ps1` (Windows)
  - Prompt should show `(venv)`

- [ ] **pip upgraded**
  - Run: `python -m pip install --upgrade pip`

---

## Phase 2: Dependencies Installation 📦

- [ ] **PyTorch installed**
  - Run: `pip install torch torchvision torchaudio`
  - Verify: `python -c "import torch; print(torch.__version__)"`

- [ ] **PyTorch Geometric installed**
  - Run: `pip install torch-scatter torch-sparse torch-cluster -f https://data.pyg.org/whl/torch-2.1.0+cpu.html`
  - Run: `pip install torch-geometric`
  - Verify: `python -c "import torch_geometric; print(torch_geometric.__version__)"`

- [ ] **Other dependencies installed**
  - Run: `pip install -r requirements.txt`
  - Should complete without errors

---

## Phase 3: PostgreSQL Setup 🗄️

- [ ] **PostgreSQL installed**
  - Download from: https://www.postgresql.org/download/
  - Version: 13 or higher

- [ ] **PostgreSQL service running**
  - Run: `Get-Service postgresql*`
  - Status should be "Running"
  - If not: `Start-Service postgresql-x64-13`

- [ ] **Can connect to PostgreSQL**
  - Run: `psql -U postgres -h localhost`
  - Should prompt for password

---

## Phase 4: Configuration ⚙️

- [ ] **`.env` file created**
  - Run: `cp .env.example .env`
  - File should exist in project root

- [ ] **Database credentials configured**
  - Edit `.env` file
  - Set: `DB_PASSWORD=your_password`
  - Set: `DB_USER=postgres`
  - Set: `DB_HOST=localhost`

- [ ] **Optional: Kaggle API configured**
  - Set: `KAGGLE_USERNAME=your_username`
  - Set: `KAGGLE_KEY=your_api_key`
  - Place `kaggle.json` in `~/.kaggle/` (if using Kaggle CLI)

---

## Phase 5: Database Creation 🏗️

- [ ] **Database setup script executed**
  - Run: `python src/database/setup_db.py`
  - Should show: "✓ Database setup completed successfully!"

- [ ] **Database 'fraud_detection' created**
  - Verify: Can connect to database

- [ ] **All tables created (5 tables)**
  - [ ] `account` table exists
  - [ ] `merchant` table exists
  - [ ] `device` table exists
  - [ ] `transaction` table exists
  - [ ] `shared_device` table exists

- [ ] **Views created (3 views)**
  - [ ] `high_risk_accounts` view
  - [ ] `suspicious_merchants` view
  - [ ] `device_sharing_stats` view

- [ ] **Triggers created**
  - [ ] `trg_update_account_stats`
  - [ ] `trg_update_merchant_stats`
  - [ ] `trg_update_device_stats`

---

## Phase 6: Dataset Download 📊

- [ ] **Dataset source identified**
  - URL: https://www.kaggle.com/c/ieee-fraud-detection/data
  - Dataset: IEEE-CIS Fraud Detection

- [ ] **Dataset downloaded**
  - Option A: Kaggle CLI (`kaggle competitions download -c ieee-fraud-detection`)
  - Option B: Manual download from website

- [ ] **Dataset files extracted**
  - [ ] `train_transaction.csv` (in `data/raw/`)
  - [ ] `train_identity.csv` (in `data/raw/`)
  - [ ] `test_transaction.csv` (optional)
  - [ ] `test_identity.csv` (optional)

- [ ] **Dataset files verified**
  - Check file sizes (should be ~100MB+ for transaction file)
  - Open and preview first few rows

---

## Phase 7: Verification ✅

- [ ] **Verification script passes**
  - Run: `python verify_setup.py`
  - All tests should pass

- [ ] **Configuration test passes**
  - Run: `python -c "from src.config.config import config; config.print_config()"`
  - Should display configuration

- [ ] **Database connection test passes**
  - Run: `python -c "from src.database.connection import db; db.test_connection()"`
  - Should show: "✓ Database connection successful!"

- [ ] **Table count queries work**
  - Run: `python -c "from src.database.connection import db; print(db.get_table_count('account'))"`
  - Should return: 0 (or number of rows if data loaded)

---

## Phase 8: Data Loading (Next Steps) 🚀

- [ ] **Data preprocessing script ready**
  - File exists: `src/preprocessing/load_data.py`

- [ ] **Ready to load data**
  - All previous checkboxes completed
  - Dataset files in correct location

---

## Troubleshooting Log 📝

Use this section to note any issues encountered:

**Issue 1:**
- Problem: 
- Solution: 
- Status: 

**Issue 2:**
- Problem: 
- Solution: 
- Status: 

**Issue 3:**
- Problem: 
- Solution: 
- Status: 

---

## Quick Reference Commands 🔧

### Activate Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### Test Database Connection
```powershell
python -c "from src.database.connection import db; db.test_connection()"
```

### Check Table Counts
```powershell
python -c "from src.database.connection import db; print('Accounts:', db.get_table_count('account')); print('Transactions:', db.get_table_count('transaction'))"
```

### Run Verification
```powershell
python verify_setup.py
```

### View Configuration
```powershell
python -c "from src.config.config import config; config.print_config()"
```

---

## System Requirements Check 💻

- [ ] **OS**: Windows 10/11, Linux, or macOS
- [ ] **Python**: 3.9 or higher
- [ ] **RAM**: 8GB minimum, 16GB recommended
- [ ] **Disk Space**: 5GB minimum for dataset and models
- [ ] **PostgreSQL**: Version 13 or higher
- [ ] **Internet**: For downloading dependencies and dataset

---

## Completion Status

**Phase 1**: ☐ Environment Setup
**Phase 2**: ☐ Dependencies Installation
**Phase 3**: ☐ PostgreSQL Setup
**Phase 4**: ☐ Configuration
**Phase 5**: ☐ Database Creation
**Phase 6**: ☐ Dataset Download
**Phase 7**: ☐ Verification
**Phase 8**: ☐ Ready for Data Loading

---

## Sign-off

**Setup completed by:** _________________

**Date:** _________________

**Time taken:** _________________

**Notes:** 
_________________________________________________
_________________________________________________
_________________________________________________

---

**Next Step:** Run `python src/preprocessing/load_data.py` (to be created)

---

**Last Updated:** November 20, 2025
