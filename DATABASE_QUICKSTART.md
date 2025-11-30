# 📊 PostgreSQL Setup Complete - Quick Reference

## Status ✅

Your database infrastructure is **100% ready**. Just needs PostgreSQL installation.

---

## 🎯 What You Have Now

### New Scripts Created:
1. **`db_setup.py`** - One-click database setup
2. **`load_data_to_db.py`** - Load IEEE-CIS data into database
3. **`POSTGRES_QUICKSTART.md`** - Quick 3-step guide
4. **`DATABASE_SETUP_GUIDE.md`** - Complete detailed guide (400+ lines)

### Existing Files Updated:
- `database/schema/create_tables.sql` - Schema definition (ready)
- `src/preprocessing/interactive_loader.py` - Data loading module (ready)
- `src/visualization/advanced_dashboard.py` - Dashboard (ready)

---

## 🚀 Installation Path (Choose One)

### Option A: Super Quick (Copy-Paste)

**1. Install PostgreSQL** (2 min)
```
Download: https://www.postgresql.org/download/windows/
Version: PostgreSQL 15
Port: 5432 (don't change!)
Superuser Password: Remember this!
```

**2. Run Setup** (1 min)
```powershell
cd "c:\Users\puneeth nagaraj\Downloads\db lab project\DRAGNN-FraudDB"
python db_setup.py
# Enter superuser password when prompted
```

**3. (Optional) Load Real Data** (10-15 min)
```powershell
python load_data_to_db.py 50000
```

**Done!** Database running on port 5432.

---

### Option B: Visual Setup (pgAdmin Included)

**1. Install PostgreSQL**
- Follow Option A, Step 1

**2. Install pgAdmin**
```
Download: https://www.pgadmin.org/download/pgadmin-4-windows/
```

**3. Run Setup Script**
```powershell
python db_setup.py
```

**4. Connect pgAdmin to Database**
- Open: http://localhost:5050
- Add Server → localhost:5432
- User: `fraud_user` | Password: `fraud_password123`

**5. View Tables in pgAdmin**
- Left sidebar → Fraud Detection → fraud_detection → public → Tables

---

### Option C: Manual Setup

If you prefer to set up manually, see **DATABASE_SETUP_GUIDE.md** section "Detailed Configuration"

---

## 📍 Connection Details

After setup, connect using:

```
Host: localhost
Port: 5432
Database: fraud_detection
User: fraud_user
Password: fraud_password123
```

**Python Example:**
```python
import psycopg2
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="fraud_detection",
    user="fraud_user",
    password="fraud_password123"
)
```

---

## 📊 Database Schema

### 5 Tables Created Automatically:

```
┌─────────────────────────────────────────────────────┐
│              FRAUD DETECTION DATABASE               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ACCOUNT (5K+ rows)                                │
│  ├── account_id (PRIMARY KEY)                      │
│  ├── risk_score (0-100)                            │
│  ├── fraud_flag (0 or 1)                           │
│  ├── email_domain                                  │
│  ├── country                                       │
│  └── created_at                                    │
│                                                     │
│  MERCHANT (1K+ rows)                               │
│  ├── merchant_id (PRIMARY KEY)                     │
│  ├── category                                      │
│  ├── fraud_rate (0-1)                              │
│  └── risk_level (low/medium/high)                  │
│                                                     │
│  DEVICE (4K+ rows)                                 │
│  ├── device_id (PRIMARY KEY)                       │
│  ├── device_type                                   │
│  ├── is_shared (0 or 1)                            │
│  ├── fraud_rate                                    │
│  └── total_users                                   │
│                                                     │
│  TRANSACTION (50K+ rows)                           │
│  ├── transaction_id (PRIMARY KEY)                  │
│  ├── account_id (FK → ACCOUNT)                     │
│  ├── merchant_id (FK → MERCHANT)                   │
│  ├── device_id (FK → DEVICE)                       │
│  ├── amount                                        │
│  ├── is_fraud (0 or 1)                             │
│  └── transaction_date                              │
│                                                     │
│  SHARED_DEVICE (900+ rows)                         │
│  ├── device_id (FK → DEVICE)                       │
│  ├── account_id_1 (FK → ACCOUNT)                   │
│  ├── account_id_2 (FK → ACCOUNT)                   │
│  ├── shared_count                                  │
│  └── fraud_probability                             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Commands

### Check PostgreSQL Status
```powershell
Get-Service postgresql-x64-15 | Select-Object Status
```

### Start/Stop PostgreSQL
```powershell
Start-Service postgresql-x64-15
Stop-Service postgresql-x64-15
```

### Connect to Database
```powershell
psql -U fraud_user -d fraud_detection -h localhost
```

### Check Database Size
```powershell
psql -U fraud_user -d fraud_detection -c "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) FROM pg_database;"
```

### List All Tables
```powershell
psql -U fraud_user -d fraud_detection -c "\dt"
```

### Count Rows in Each Table
```powershell
psql -U fraud_user -d fraud_detection -c "
SELECT 
  'account' as table_name, COUNT(*) as row_count FROM account
UNION ALL
SELECT 'merchant', COUNT(*) FROM merchant
UNION ALL
SELECT 'device', COUNT(*) FROM device
UNION ALL
SELECT 'transaction', COUNT(*) FROM transaction
UNION ALL
SELECT 'shared_device', COUNT(*) FROM shared_device;"
```

---

## 📈 Data Loading

### Load Sample Data (10K rows, 1 min)
```powershell
python load_data_to_db.py 10000
```

### Load Medium Data (50K rows, 5 min)
```powershell
python load_data_to_db.py 50000
```

### Load All Data (590K rows, 15 min)
```powershell
python load_data_to_db.py
# or
python load_data_to_db.py all
```

### What Gets Loaded:
- ✓ Accounts with risk scores
- ✓ Merchants with fraud rates
- ✓ Devices with sharing detection
- ✓ Transactions with fraud labels
- ✓ Shared device relationships (fraud rings)

---

## 🎨 Run Dashboard with Database

After PostgreSQL is running:

```powershell
streamlit run src/visualization/advanced_dashboard.py
```

Then:
1. Open http://localhost:8501
2. Click "Load Real IEEE-CIS Data"
3. Specify how many rows to load
4. View all analysis pages with live database data

---

## 🔗 Port Reference

| Service | Port | Access |
|---------|------|--------|
| PostgreSQL | 5432 | localhost:5432 |
| pgAdmin | 5050 | http://localhost:5050 |
| Dashboard | 8501 | http://localhost:8501 |

---

## 📋 Verification Checklist

After installation, verify:

- [ ] PostgreSQL installed: `psql --version` works
- [ ] PostgreSQL running: Service shows "Running"
- [ ] db_setup.py runs without errors
- [ ] Can connect to database: `psql -U fraud_user -d fraud_detection`
- [ ] Tables exist: `psql ... -c "\dt"` shows 5 tables
- [ ] (Optional) pgAdmin connects to localhost:5432

---

## 🛠️ Troubleshooting (1 Minute)

### Problem: "psql: command not found"
```powershell
# Add PostgreSQL to PATH:
$path = "C:\Program Files\PostgreSQL\15\bin"
[Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";$path", "User")
# Restart PowerShell
```

### Problem: "Connection refused"
```powershell
# Check if running:
Get-Service postgresql-x64-15 | Select-Object Status
# Start if needed:
Start-Service postgresql-x64-15
```

### Problem: "Port 5432 already in use"
```powershell
# See what's using it:
netstat -ano | findstr :5432
# Install on different port during PostgreSQL setup
```

### Problem: "Password authentication failed"
```powershell
# Reset fraud_user password:
psql -U postgres -h localhost
# In psql:
ALTER USER fraud_user WITH PASSWORD 'fraud_password123';
\q
```

See **DATABASE_SETUP_GUIDE.md** for more troubleshooting.

---

## 📚 Full Documentation

| Document | Purpose | Time |
|----------|---------|------|
| **POSTGRES_QUICKSTART.md** | 3-step installation | 5 min |
| **DATABASE_SETUP_GUIDE.md** | Detailed setup guide | 30 min |
| **load_data_to_db.py** | Data loading script | Auto |
| **db_setup.py** | Database setup script | Auto |

---

## 📞 What's Next?

1. **Now**: Download and install PostgreSQL from postgresql.org
2. **Then**: Run `python db_setup.py`
3. **Then**: Download IEEE-CIS dataset (optional)
4. **Then**: Run `python load_data_to_db.py`
5. **Finally**: Run dashboard: `streamlit run src/visualization/advanced_dashboard.py`

---

## 🎓 Learning Resources

- PostgreSQL: https://www.postgresql.org/docs/
- pgAdmin: https://www.pgadmin.org/docs/
- psycopg2: https://www.psycopg.org/
- IEEE-CIS Dataset: https://www.kaggle.com/c/ieee-fraud-detection/

---

**Everything is ready! Just install PostgreSQL and you're good to go.** 🚀
