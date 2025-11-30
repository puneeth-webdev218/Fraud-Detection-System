# 🗄️ Database Setup & Configuration Guide

## Overview

This guide walks you through setting up PostgreSQL, pgAdmin, and loading your fraud detection data into a working database on port 5432.

---

## Prerequisites

- **PostgreSQL 13+** (NOT installed yet - we'll install it)
- **pgAdmin 4** (optional but recommended for GUI access)
- Python 3.9+ with `psycopg2` library
- IEEE-CIS dataset (optional - for real data)

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Install PostgreSQL
1. Go to: https://www.postgresql.org/download/windows/
2. Download **PostgreSQL 15** installer
3. Run installer and follow steps:
   - **Installation Directory**: Use default (C:\Program Files\PostgreSQL\15)
   - **Port**: Keep as **5432** ✓
   - **Superuser Password**: Set something you'll remember (e.g., `postgres123`)
   - **Locale**: Default
4. Click **Finish**
5. Verify installation:
   ```powershell
   psql --version
   # Should show: psql (PostgreSQL) 15.x
   ```

### Step 2: Run Database Setup
```powershell
cd "c:\Users\puneeth nagaraj\Downloads\db lab project\DRAGNN-FraudDB"
python db_setup.py
```

When prompted:
- Enter the superuser password you set in Step 1

Script will:
- ✓ Create `fraud_detection` database
- ✓ Create `fraud_user` with password `fraud_password123`
- ✓ Load schema (5 tables)
- ✓ Verify connection

### Step 3: (Optional) Load Real Data
```powershell
# Download IEEE-CIS dataset to data/raw/ first
# Then run:
python load_data_to_db.py 50000
```

That's it! Database is ready.

---

## Detailed Configuration

### PostgreSQL Installation (Windows)

#### Download
1. Visit: https://www.postgresql.org/download/windows/
2. Choose version **15.x** (Latest LTS)
3. Download installer

#### Install
1. Run `postgresql-15.x-windows-x86_64.exe`
2. Choose installation directory (keep default is fine)
3. **Important Settings**:
   - Port: **5432** (MUST be this)
   - Superuser password: Something strong (you'll need this)
   - Data directory: Default is fine
4. Click through remaining steps
5. **Start service**: Check "Launch Stack Builder" - this is optional

#### Verify
```powershell
# Open PowerShell and run:
psql --version
# OR
Get-Service postgresql-x64-15 | Select-Object Status
# Should show: Running
```

---

### Database Setup Script

#### What it does:
```
db_setup.py
├── Get superuser password from you
├── Test superuser connection
├── Create 'fraud_detection' database
├── Create 'fraud_user' with password
├── Grant all privileges
├── Load schema from database/schema/create_tables.sql
├── Create 5 tables:
│   ├── account
│   ├── merchant
│   ├── device
│   ├── transaction
│   └── shared_device
└── Verify everything works
```

#### Run it:
```powershell
python db_setup.py
```

#### Output:
```
██████████████████████████████████████████████████████████
  PostgreSQL Database Setup
██████████████████████████████████████████████████████████

============================================================
PostgreSQL Superuser Authentication
============================================================

Enter the PostgreSQL 'postgres' superuser password
(set during PostgreSQL installation)

Password: ****

Testing superuser connection...
✓ Superuser authentication successful

Creating database...
  ✓ Created database 'fraud_detection'

Creating user...
  ✓ Created user 'fraud_user'
  ✓ Granted privileges to 'fraud_user'

Loading schema...
  ✓ Loaded schema from create_tables.sql

  Created tables:
    - account
    - device
    - merchant
    - shared_device
    - transaction

Verifying connection...
  ✓ Connected to PostgreSQL
    PostgreSQL 15.2 on x86_64-pc-windows, compiled by ...

============================================================
✅ Database Setup Complete!
============================================================

📋 Connection Details:
  Host: localhost
  Port: 5432
  Database: fraud_detection
  User: fraud_user
  Password: fraud_password123

🚀 Next Steps:
...
```

---

## Data Loading

### Automated Data Loading

After installing PostgreSQL and running `db_setup.py`:

```powershell
# Load first 50,000 rows
python load_data_to_db.py 50000

# Load all rows (590K+, takes 10-15 minutes)
python load_data_to_db.py

# Load specific amount
python load_data_to_db.py 100000
```

#### What it does:
- Reads IEEE-CIS CSV files from `data/raw/`
- Extracts unique accounts, merchants, devices
- Populates all 5 tables
- Detects shared devices
- Shows progress with progress bars

#### Output:
```
Loading data from data/raw/train_transaction.csv...
✓ Loaded 50000 rows

Inserting accounts...
Processing accounts: 100%|██████████| 5432/5432 [00:12<00:00, 423.45it/s]
✓ Inserted 5432 accounts

Inserting merchants...
Processing merchants: 100%|██████████| 1203/1203 [00:03<00:00, 412.56it/s]
✓ Inserted 1203 merchants

Inserting devices...
Processing devices: 100%|██████████| 4129/4129 [00:09<00:00, 482.15it/s]
✓ Inserted 4129 devices

Inserting transactions...
Processing transactions: 100%|████████| 50000/50000 [00:45<00:00, 1105.34it/s]
✓ Inserted 50000 transactions

Inserting shared device relationships...
Finding shared devices: 100%|████████| 4129/4129 [00:08<00:00, 523.12it/s]
✓ Inserted 892 shared device records

📊 Data Verification:
  ✓ account: 5,432 rows
  ✓ merchant: 1,203 rows
  ✓ device: 4,129 rows
  ✓ transaction: 50,000 rows
  ✓ shared_device: 892 rows

  📈 Fraud Statistics:
     - Total transactions: 50,000
     - Fraudulent: 1,203 (2.41%)
     - Legitimate: 48,797
```

### Get IEEE-CIS Dataset

1. Create Kaggle account (free): https://www.kaggle.com
2. Go to: https://www.kaggle.com/c/ieee-fraud-detection/data
3. Accept competition rules
4. Download:
   - `train_transaction.csv` (500+ MB)
   - `train_identity.csv` (100+ MB)
5. Extract to: `data/raw/`

---

## pgAdmin Setup (Optional but Recommended)

### Install pgAdmin
1. Download: https://www.pgadmin.org/download/pgadmin-4-windows/
2. Run installer
3. Set master password (remember it!)

### Connect to Database
1. Open browser → http://localhost:5050
2. Login with email/password you created
3. Click **"Add New Server"**
4. Fill in:
   ```
   Name: Fraud Detection
   Hostname: localhost
   Port: 5432
   Username: fraud_user
   Password: fraud_password123
   Save password: ✓
   ```
5. Click **Save**

### View Tables
- Left sidebar: **Servers** → **Fraud Detection** → **Databases** → **fraud_detection** → **Schemas** → **public** → **Tables**
- Click any table to see data
- Right-click for SQL operations

### Example Queries
```sql
-- View all accounts with fraud statistics
SELECT account_id, risk_score, fraud_flag, country, created_at 
FROM account 
ORDER BY risk_score DESC 
LIMIT 20;

-- Find shared devices (possible fraud rings)
SELECT d.device_id, COUNT(DISTINCT sd.account_id_1) as account_count
FROM device d
JOIN shared_device sd ON d.device_id = sd.device_id
GROUP BY d.device_id
ORDER BY account_count DESC
LIMIT 10;

-- Fraud rate by merchant
SELECT m.merchant_id, m.category, m.fraud_rate, COUNT(t.transaction_id) as transaction_count
FROM merchant m
LEFT JOIN transaction t ON m.merchant_id = t.merchant_id
GROUP BY m.merchant_id, m.category, m.fraud_rate
ORDER BY m.fraud_rate DESC
LIMIT 20;

-- High-risk transactions
SELECT t.transaction_id, t.account_id, t.merchant_id, t.amount, t.is_fraud
FROM transaction t
WHERE t.amount > (SELECT AVG(amount) * 3 FROM transaction)
AND t.is_fraud = 1
ORDER BY t.amount DESC
LIMIT 20;
```

---

## Connection Strings for Different Tools

### Python (psycopg2)
```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="fraud_detection",
    user="fraud_user",
    password="fraud_password123"
)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM transaction")
print(cursor.fetchone())
cursor.close()
conn.close()
```

### Python (SQLAlchemy)
```python
from sqlalchemy import create_engine

engine = create_engine(
    'postgresql://fraud_user:fraud_password123@localhost:5432/fraud_detection'
)

# Using pandas
import pandas as pd
df = pd.read_sql("SELECT * FROM transaction LIMIT 100", engine)
```

### Python (psycopg2 with Context Manager)
```python
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'fraud_detection',
    'user': 'fraud_user',
    'password': 'fraud_password123'
}

with psycopg2.connect(**DB_CONFIG) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM account LIMIT 10")
        for row in cur.fetchall():
            print(row)
```

### Command Line (psql)
```powershell
psql -U fraud_user -d fraud_detection -h localhost -p 5432

# Then in psql:
fraud_detection=# SELECT * FROM transaction LIMIT 5;
fraud_detection=# \dt  -- List all tables
fraud_detection=# \d transaction  -- Describe table
fraud_detection=# \q  -- Quit
```

---

## Troubleshooting

### Issue: "psql command not found"

**Solution 1: Add PostgreSQL to PATH**
```powershell
# Run this in PowerShell:
$path = "C:\Program Files\PostgreSQL\15\bin"
[Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";$path", "User")

# Restart PowerShell and try again:
psql --version
```

**Solution 2: Use full path**
```powershell
"C:\Program Files\PostgreSQL\15\bin\psql.exe" --version
```

### Issue: "Connection refused" or "Could not connect"

**Check if PostgreSQL is running:**
```powershell
Get-Service postgresql-x64-15 | Select-Object Status
# Should show: Running

# If not running, start it:
Start-Service postgresql-x64-15
```

### Issue: "Port 5432 already in use"

**Find and stop what's using it:**
```powershell
# Find process using port 5432
netstat -ano | findstr :5432

# Kill process (replace PID with actual PID):
taskkill /PID <PID> /F

# Or reconfigure PostgreSQL to use different port during installation
```

### Issue: "Password authentication failed"

**The password you need:**
- Superuser password: What you set during PostgreSQL installation
- fraud_user password: `fraud_password123` (set by db_setup.py)

**Reset fraud_user password:**
```powershell
# Connect as superuser first
psql -U postgres -h localhost

# Then in psql:
ALTER USER fraud_user WITH PASSWORD 'fraud_password123';
\q
```

### Issue: Can't find IEEE-CIS data files

**Files needed:**
- `data/raw/train_transaction.csv` (from Kaggle)
- `data/raw/train_identity.csv` (from Kaggle)

**If missing, script will:**
1. Show warning message
2. Still create tables (empty)
3. Tell you how to download

**Download steps:**
1. Go to: https://www.kaggle.com/c/ieee-fraud-detection/data
2. Accept competition rules
3. Download the CSV files
4. Extract to `data/raw/` folder

### Issue: "Protocol error" or other connection errors

**Check configuration:**
```powershell
# Test connection manually
psql -U fraud_user -d fraud_detection -h localhost -p 5432

# Should ask for password, then show:
# fraud_detection=>
```

**If fails:**
1. Check PostgreSQL is running: `Get-Service postgresql-x64-15`
2. Check port is correct: `netstat -ano | findstr :5432`
3. Re-run `db_setup.py` to recreate user/database

---

## Verification Checklist

After setup, verify everything works:

- [ ] PostgreSQL installed: `psql --version`
- [ ] PostgreSQL running: `Get-Service postgresql-x64-15`
- [ ] Database created: `psql -U postgres -l | findstr fraud_detection`
- [ ] fraud_user created: `psql -U postgres -c "\du" | findstr fraud_user`
- [ ] Can connect: `psql -U fraud_user -d fraud_detection -h localhost`
- [ ] Tables exist: `psql -U fraud_user -d fraud_detection -c "\dt"`
- [ ] Tables have data (if loaded): `psql -U fraud_user -d fraud_detection -c "SELECT COUNT(*) FROM transaction"`
- [ ] pgAdmin can connect (optional)
- [ ] Dashboard can query database (coming soon)

---

## Next Steps

### 1. Run the Dashboard
```powershell
streamlit run src/visualization/advanced_dashboard.py
```
Then open http://localhost:8501

### 2. Explore Database
```powershell
# Start interactive psql
psql -U fraud_user -d fraud_detection
```

### 3. Load More Data
```powershell
# Load all 590K transactions (takes ~15 min)
python load_data_to_db.py
```

### 4. Query from Python
```python
import psycopg2
conn = psycopg2.connect(host='localhost', port=5432,
                        database='fraud_detection',
                        user='fraud_user',
                        password='fraud_password123')
```

---

## File Reference

| File | Purpose |
|------|---------|
| `db_setup.py` | One-click database setup |
| `load_data_to_db.py` | Load IEEE-CIS data into database |
| `database/schema/create_tables.sql` | Database schema definition |
| `src/database/connection.py` | Python database connection helper |
| `src/database/setup_db.py` | Database operations (if exists) |
| `src/config/config.py` | Configuration file |
| `data/raw/` | Folder for IEEE-CIS CSV files |

---

## Ports Overview

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| PostgreSQL | 5432 | N/A | Database server |
| pgAdmin | 5050 | http://localhost:5050 | GUI management |
| Streamlit Dashboard | 8501 | http://localhost:8501 | Fraud analysis UI |
| SSH (optional) | 22 | N/A | Remote access |

---

## Support

### Common Commands

```powershell
# Check if service is running
Get-Service postgresql-x64-15

# Start service
Start-Service postgresql-x64-15

# Stop service
Stop-Service postgresql-x64-15

# Connect to database
psql -U fraud_user -d fraud_detection -h localhost -p 5432

# List all databases
psql -U fraud_user -l

# Dump database to file
pg_dump -U fraud_user -d fraud_detection > backup.sql

# Restore database from file
psql -U fraud_user -d fraud_detection < backup.sql
```

### Need Help?

1. Check **POSTGRES_QUICKSTART.md** for quick reference
2. Check PostgreSQL docs: https://www.postgresql.org/docs/
3. Check pgAdmin docs: https://www.pgadmin.org/docs/
4. Run `db_setup.py` again if needed

---

## Environment Variables (Optional)

Create `.env` file in project root:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fraud_detection
DB_USER=fraud_user
DB_PASSWORD=fraud_password123
DB_SSLMODE=disable
```

Then in Python:
```python
from dotenv import load_dotenv
import os

load_dotenv()
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
# etc.
```

---

## Security Notes

⚠️ **For production:**
- Change `DB_PASSWORD` to something stronger
- Don't commit `.env` file to git
- Use SSL/TLS connections
- Restrict network access
- Regular backups
- Monitor access logs

✓ **For development:** Current setup is fine

---

**Last Updated**: 2024  
**PostgreSQL Version**: 15+  
**Python Version**: 3.9+
