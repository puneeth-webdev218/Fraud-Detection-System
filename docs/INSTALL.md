# 🚀 Installation & Setup Guide

## Prerequisites

Before starting, ensure you have:

1. **Python 3.9+** installed
2. **PostgreSQL 13+** installed and running
3. **Git** (optional, for version control)
4. **8GB+ RAM** (16GB recommended)
5. **Kaggle Account** (for dataset download)

---

## Step-by-Step Installation

### **Step 1: Environment Setup**

#### Windows (PowerShell):
```powershell
# Navigate to project directory
cd C:\Users\Pavan\FRAUD

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip
```

#### Linux/Mac:
```bash
cd /path/to/FRAUD
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

---

### **Step 2: Install Dependencies**

```powershell
# Install PyTorch (CPU version - adjust for GPU if needed)
pip install torch torchvision torchaudio

# Install PyTorch Geometric dependencies
pip install torch-scatter torch-sparse torch-cluster -f https://data.pyg.org/whl/torch-2.1.0+cpu.html
pip install torch-geometric

# Install remaining dependencies
pip install -r requirements.txt
```

**Note for GPU Support:**
If you have CUDA-enabled GPU, replace `cpu` with your CUDA version (e.g., `cu118` for CUDA 11.8)

---

### **Step 3: PostgreSQL Setup**

#### Install PostgreSQL:
- **Windows**: Download from https://www.postgresql.org/download/windows/
- **Linux**: `sudo apt-get install postgresql postgresql-contrib`
- **Mac**: `brew install postgresql`

#### Start PostgreSQL Service:
```powershell
# Windows (PowerShell as Admin)
Start-Service postgresql-x64-13

# Linux
sudo systemctl start postgresql

# Mac
brew services start postgresql
```

#### Verify PostgreSQL is running:
```powershell
# Windows
Get-Service postgresql*

# Linux/Mac
sudo systemctl status postgresql
```

---

### **Step 4: Configure Environment Variables**

```powershell
# Copy example environment file
cp .env.example .env

# Edit .env file with your settings
notepad .env  # Windows
# or
nano .env     # Linux/Mac
```

**Update the following in `.env`:**
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fraud_detection
DB_USER=postgres
DB_PASSWORD=your_postgres_password

KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key
```

---

### **Step 5: Create Database**

```powershell
# Run database setup script
python src/database/setup_db.py
```

**Expected Output:**
```
======================================================================
Fraud Detection Database Setup
======================================================================

[Step 1/3] Creating database...
✓ Database 'fraud_detection' created successfully

[Step 2/3] Creating tables and schema...
✓ All tables created successfully

Created tables (5):
  - account
  - device
  - merchant
  - shared_device
  - transaction

[Step 3/3] Verifying database setup...
✓ Database connection successful!

Table status:
  ✓ account: 0 rows
  ✓ merchant: 0 rows
  ✓ device: 0 rows
  ✓ transaction: 0 rows
  ✓ shared_device: 0 rows

======================================================================
✓ Database setup completed successfully!
======================================================================
```

---

### **Step 6: Download Dataset**

#### Option A: Using Kaggle API (Recommended)
```powershell
# Configure Kaggle API
# Place kaggle.json in: C:\Users\<YourName>\.kaggle\ (Windows)
# or ~/.kaggle/ (Linux/Mac)

# Download dataset
kaggle competitions download -c ieee-fraud-detection -p data/raw/

# Unzip files
cd data/raw
Expand-Archive -Path ieee-fraud-detection.zip -DestinationPath .
```

#### Option B: Manual Download
1. Visit: https://www.kaggle.com/c/ieee-fraud-detection/data
2. Download all files:
   - `train_transaction.csv`
   - `train_identity.csv`
   - `test_transaction.csv`
   - `test_identity.csv`
3. Place files in `data/raw/` directory

---

### **Step 7: Verify Installation**

```powershell
# Test configuration
python -c "from src.config.config import config; config.print_config()"

# Test database connection
python -c "from src.database.connection import db; db.test_connection()"
```

---

## Troubleshooting

### **Issue: PostgreSQL Connection Error**

**Error:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
1. Verify PostgreSQL is running: `Get-Service postgresql*`
2. Check credentials in `.env` file
3. Test connection: `psql -U postgres -h localhost`

---

### **Issue: PyTorch Installation Error**

**Error:** `Could not find a version that satisfies the requirement torch`

**Solution:**
```powershell
# Install PyTorch separately first
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Then install other dependencies
pip install -r requirements.txt
```

---

### **Issue: PyTorch Geometric Installation Error**

**Error:** `No matching distribution found for torch-scatter`

**Solution:**
```powershell
# Install with explicit wheel URL
pip install torch-scatter torch-sparse torch-cluster -f https://data.pyg.org/whl/torch-2.1.0+cpu.html
```

---

### **Issue: Permission Denied (Windows)**

**Error:** `execution of scripts is disabled on this system`

**Solution:**
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate venv again
.\venv\Scripts\Activate.ps1
```

---

### **Issue: Module Not Found**

**Error:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```powershell
# Install package in development mode
pip install -e .
```

---

## Verification Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed without errors
- [ ] PostgreSQL running
- [ ] `.env` file configured
- [ ] Database created successfully
- [ ] All 5 tables exist in database
- [ ] Dataset files downloaded to `data/raw/`
- [ ] Configuration test passes
- [ ] Database connection test passes

---

## Next Steps

Once installation is complete:

1. **Load Data**: `python src/preprocessing/load_data.py`
2. **Build Graph**: `python src/graph/build_graph.py`
3. **Train Model**: `python src/training/train.py`
4. **Launch Dashboard**: `streamlit run src/visualization/dashboard.py`

---

## Getting Help

If you encounter issues:

1. Check logs in `logs/` directory
2. Verify all prerequisites are met
3. Review error messages carefully
4. Ensure all environment variables are set correctly

---

**Last Updated:** November 20, 2025
