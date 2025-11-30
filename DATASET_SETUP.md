# IEEE-CIS Fraud Detection Dataset Setup

## 📥 Quick Setup Guide

Your dashboard now supports loading the **real IEEE-CIS Fraud Detection dataset** from Kaggle!

---

## Step 1: Download the Dataset

### Option A: Direct Download (Recommended)
1. Go to: https://www.kaggle.com/c/ieee-fraud-detection/data
2. Click **"Download All"** button (requires Kaggle account)
3. Wait for files to download (~2 GB)
4. Extract the ZIP file

### Option B: Using Kaggle CLI
```powershell
# Install Kaggle CLI
pip install kaggle

# Download dataset
kaggle competitions download -c ieee-fraud-detection

# Extract
Expand-Archive ieee-fraud-detection.zip -DestinationPath data\raw\
```

### Option C: Manual Download
1. Create Kaggle account at: https://www.kaggle.com
2. Go to competition: https://www.kaggle.com/c/ieee-fraud-detection/data
3. Download each file individually:
   - `train_transaction.csv` (590 MB)
   - `train_identity.csv` (168 MB)

---

## Step 2: Extract Files

Extract the dataset files to the `data/raw/` folder:

```
DRAGNN-FraudDB/
└── data/
    └── raw/
        ├── train_transaction.csv     (590,540 rows × 394 columns)
        ├── train_identity.csv        (144,233 rows × 41 columns)
        ├── test_transaction.csv
        ├── test_identity.csv
        └── .gitkeep
```

---

## Step 3: Verify Files

Check that files are in place:

```powershell
# Check file sizes
Get-ChildItem "data\raw\" | Format-Table Name, Length, LastWriteTime

# Expected output:
# train_transaction.csv  ~590 MB
# train_identity.csv     ~168 MB
```

---

## Step 4: Use in Dashboard

### Via Web Interface
1. Open dashboard: http://localhost:8501
2. Click **"Real Dataset"** tab in sidebar
3. Set transaction count (e.g., 5000)
4. Click **"📥 Load Real IEEE-CIS Data"**
5. Wait for load (5-30 seconds depending on count)
6. Dashboard updates with real fraud data!

### Via Python Code

```python
from src.preprocessing.interactive_loader import InteractiveDataLoader

# Initialize loader
loader = InteractiveDataLoader()

# Load 10,000 real transactions
transactions, identity = loader.load_ieee_cis_data(n_transactions=10000)

# Merge transaction and identity data
merged = loader.merge_transaction_identity(transactions, identity)

print(f"Loaded {len(merged):,} transactions")
print(f"Fraud cases: {merged['isFraud'].sum()}")
```

---

## 📊 Dataset Information

### Train Transaction Data
- **Rows:** 590,540 transactions
- **Columns:** 394 (including ID, amount, card, address, fraud label)
- **Date Range:** Jan 1 - Dec 31, 2017
- **File Size:** ~590 MB

### Train Identity Data
- **Rows:** 144,233 records
- **Columns:** 41 (device info, ID types, device features)
- **File Size:** ~168 MB

### Key Columns
```
transaction_id      - Unique transaction identifier
isFraud             - Fraud label (0=legitimate, 1=fraud)
TransactionAmt      - Transaction amount in USD
TransactionDT       - Time delta from reference point
ProductCD           - Product code (e.g., W, H, S, C, R)
card1-card6         - Credit card fields
addr1-addr2         - Address fields
P_emaildomain       - Purchaser email domain
R_emaildomain       - Recipient email domain
DeviceType          - Desktop or mobile
DeviceInfo          - Device identifier
```

---

## ⚠️ Troubleshooting

### "File not found" error
**Problem:** Files not in correct location
**Solution:**
```powershell
# Copy files to correct location
Copy-Item "path\to\downloaded\train_transaction.csv" "data\raw\"
Copy-Item "path\to\downloaded\train_identity.csv" "data\raw\"
```

### Very slow loading
**Problem:** Loading too many transactions at once
**Solution:**
- Start with smaller count (e.g., 1000 rows)
- Gradually increase to see performance
- Max recommended: 50,000 for smooth dashboard

### Memory issues
**Problem:** Computer running slow with large dataset
**Solution:**
- Reduce loaded transaction count
- Close other applications
- Use preset buttons (smaller counts)

### Import errors
**Problem:** Missing dependencies
**Solution:**
```powershell
# Install requirements
pip install -r requirements.txt

# Or install specific packages
pip install pandas numpy streamlit plotly
```

---

## 🎯 Loading Strategies

### Fast Exploration (5-10 seconds)
- Load 1,000-5,000 transactions
- Use **Quick Load** or **Real Dataset** tab

### Detailed Analysis (20-30 seconds)
- Load 20,000-50,000 transactions
- All visualizations show rich patterns

### Full Dataset (1-2 minutes)
- Load 100,000+ transactions (requires patience)
- Complete fraud picture
- May require 4+ GB RAM

### Memory-Efficient (Best Practice)
```python
# Load in batches
loader = InteractiveDataLoader()

for batch_size in [10000, 20000, 50000]:
    txns = loader.load_ieee_cis_data(n_transactions=batch_size)
    # Process batch
    results.append(process_batch(txns))
```

---

## 🔄 Switching Between Data Sources

You can easily switch between synthetic and real data:

### Dashboard Method
1. **Quick Load tab** → Click preset (synthetic)
2. **Real Dataset tab** → Load real data
3. **Custom tab** → Synthetic with custom count

### Code Method
```python
from src.preprocessing.interactive_loader import InteractiveDataLoader

loader = InteractiveDataLoader()

# Load synthetic
synthetic = loader.generate_synthetic_transactions(5000)

# Load real
real, identity = loader.load_ieee_cis_data(5000)

# They have same structure!
print(synthetic.columns)
print(real.columns)
```

---

## 📈 What You Can Do Now

### With Real Data
✅ Analyze actual fraud patterns (5% fraud rate)  
✅ Identify real high-risk accounts and merchants  
✅ See actual temporal trends in fraud  
✅ Detect real device fraud patterns  
✅ Train models on realistic data  
✅ Test your fraud detection algorithms  

### Before vs After
| Aspect | Synthetic | Real IEEE-CIS |
|--------|-----------|---------------|
| Realism | Moderate | High |
| Fraud Rate | 5% (constant) | ~3.5% (variable) |
| Patterns | Random | Realistic patterns |
| Size | Up to 50K | Up to 590K |
| Use Case | Testing/Demo | Production |

---

## 🚀 Next Steps

1. ✅ Download dataset from Kaggle
2. ✅ Extract to `data/raw/` folder
3. ✅ Open dashboard: http://localhost:8501
4. ✅ Click **"Real Dataset"** tab
5. ✅ Load and explore real fraud patterns

---

## 📚 Learn More

### Kaggle Competition
- https://www.kaggle.com/c/ieee-fraud-detection/
- View solutions, kernels, discussions
- Download other useful datasets

### IEEE-CIS Fraud Detection
- Research paper and documentation
- Feature engineering tips
- Model benchmarks

### Streamlit Documentation
- Dashboard customization
- Interactive features
- Deployment options

---

## 💡 Pro Tips

### For Best Performance
1. Start with 5,000 transactions to test
2. Check load time (should be <10 seconds)
3. Gradually increase count
4. Monitor memory usage in Task Manager

### For Better Insights
1. Load 20,000+ for patterns
2. Use multiple load sizes for comparison
3. Check fraud trends over time
4. Identify device sharing patterns

### For Model Training
1. Load full 590K dataset (one-time)
2. Save to processed folder
3. Train models on full dataset
4. Use dashboard for evaluation

---

**Dataset Status:** Ready to use! 🎉  
**Dashboard Status:** ✅ Supports both synthetic and real data  
**Next Action:** Download files and click "Load Real IEEE-CIS Data" button
