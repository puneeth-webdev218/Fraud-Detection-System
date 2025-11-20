# 📊 Entity-Relationship Diagram

## Database Schema Overview

This document describes the Entity-Relationship structure for the Fraud Detection Database.

---

## **Entities and Attributes**

### **1. ACCOUNT**
Represents user accounts in the system.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| account_id | VARCHAR(50) | Unique account identifier | PRIMARY KEY |
| creation_date | TIMESTAMP | Account creation timestamp | NOT NULL |
| email_domain | VARCHAR(100) | Domain of user email | - |
| country | VARCHAR(50) | User's country | - |
| risk_score | DECIMAL(5,4) | Calculated fraud risk (0-1) | 0 <= x <= 1 |
| total_transactions | INTEGER | Total number of transactions | DEFAULT 0 |
| total_amount | DECIMAL(12,2) | Total transaction amount | DEFAULT 0.00 |
| fraud_flag | BOOLEAN | Has committed fraud | DEFAULT FALSE |
| last_transaction_date | TIMESTAMP | Most recent transaction | - |
| account_age_days | INTEGER | Account age in days | - |
| created_at | TIMESTAMP | Record creation timestamp | DEFAULT NOW |
| updated_at | TIMESTAMP | Record update timestamp | DEFAULT NOW |

**Indexes:**
- `idx_account_risk_score` on `risk_score DESC`
- `idx_account_fraud_flag` on `fraud_flag`
- `idx_account_email_domain` on `email_domain`
- `idx_account_country` on `country`

---

### **2. MERCHANT**
Represents merchants/businesses accepting transactions.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| merchant_id | VARCHAR(50) | Unique merchant identifier | PRIMARY KEY |
| merchant_name | VARCHAR(200) | Merchant name | - |
| merchant_category | VARCHAR(100) | Business category | - |
| country | VARCHAR(50) | Merchant country | - |
| total_transactions | INTEGER | Total transactions processed | DEFAULT 0 |
| total_fraud_transactions | INTEGER | Fraudulent transactions | DEFAULT 0 |
| fraud_rate | DECIMAL(5,4) | Fraud rate (0-1) | - |
| avg_transaction_amount | DECIMAL(12,2) | Average transaction value | - |
| risk_level | VARCHAR(20) | Risk category | LOW/MEDIUM/HIGH/CRITICAL |
| created_at | TIMESTAMP | Record creation timestamp | DEFAULT NOW |
| updated_at | TIMESTAMP | Record update timestamp | DEFAULT NOW |

**Indexes:**
- `idx_merchant_category` on `merchant_category`
- `idx_merchant_fraud_rate` on `fraud_rate DESC`
- `idx_merchant_risk_level` on `risk_level`

---

### **3. DEVICE**
Represents devices used for transactions.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| device_id | VARCHAR(50) | Unique device identifier | PRIMARY KEY |
| device_type | VARCHAR(50) | Type of device | - |
| device_info | VARCHAR(200) | Device information | - |
| os_id | VARCHAR(50) | Operating system ID | - |
| browser_id | VARCHAR(50) | Browser ID | - |
| screen_resolution | VARCHAR(50) | Screen resolution | - |
| total_users | INTEGER | Number of users | DEFAULT 0 |
| total_transactions | INTEGER | Total transactions | DEFAULT 0 |
| fraud_transactions | INTEGER | Fraudulent transactions | DEFAULT 0 |
| fraud_rate | DECIMAL(5,4) | Device fraud rate | - |
| is_shared | BOOLEAN | Multiple users flag | DEFAULT FALSE |
| risk_score | DECIMAL(5,4) | Device risk score (0-1) | 0 <= x <= 1 |
| created_at | TIMESTAMP | Record creation timestamp | DEFAULT NOW |
| updated_at | TIMESTAMP | Record update timestamp | DEFAULT NOW |

**Indexes:**
- `idx_device_type` on `device_type`
- `idx_device_shared` on `is_shared`
- `idx_device_fraud_rate` on `fraud_rate DESC`
- `idx_device_risk_score` on `risk_score DESC`

---

### **4. TRANSACTION**
Core entity storing all transaction records.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| transaction_id | VARCHAR(50) | Unique transaction ID | PRIMARY KEY |
| account_id | VARCHAR(50) | Account reference | FOREIGN KEY, NOT NULL |
| merchant_id | VARCHAR(50) | Merchant reference | FOREIGN KEY, NOT NULL |
| device_id | VARCHAR(50) | Device reference | FOREIGN KEY |
| transaction_date | TIMESTAMP | Transaction timestamp | NOT NULL |
| transaction_amount | DECIMAL(12,2) | Transaction value | NOT NULL, >= 0 |
| product_category | VARCHAR(10) | Product category code | - |
| card_type | VARCHAR(50) | Type of card used | - |
| card_category | VARCHAR(50) | Card category | - |
| transaction_type | VARCHAR(50) | Transaction type | - |
| addr_country | VARCHAR(50) | Transaction country | - |
| transaction_hour | INTEGER | Hour of transaction | 0-23 |
| transaction_day_of_week | INTEGER | Day of week | 0-6 |
| transaction_day_of_month | INTEGER | Day of month | 1-31 |
| email_domain | VARCHAR(100) | Email domain | - |
| distance_from_last_txn | DECIMAL(12,2) | Geographic distance | - |
| time_since_last_txn | INTEGER | Time difference (seconds) | - |
| **is_fraud** | **BOOLEAN** | **Fraud label (TARGET)** | **NOT NULL** |
| created_at | TIMESTAMP | Record creation timestamp | DEFAULT NOW |

**Indexes:**
- `idx_transaction_account` on `account_id`
- `idx_transaction_merchant` on `merchant_id`
- `idx_transaction_device` on `device_id`
- `idx_transaction_date` on `transaction_date DESC`
- `idx_transaction_fraud` on `is_fraud`
- `idx_transaction_amount` on `transaction_amount DESC`
- `idx_transaction_composite` on `(account_id, transaction_date)`

---

### **5. SHARED_DEVICE**
Junction table tracking device sharing patterns.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| id | SERIAL | Auto-increment ID | PRIMARY KEY |
| device_id | VARCHAR(50) | Device reference | FOREIGN KEY, NOT NULL |
| account_id | VARCHAR(50) | Account reference | FOREIGN KEY, NOT NULL |
| first_seen | TIMESTAMP | First usage timestamp | DEFAULT NOW |
| last_seen | TIMESTAMP | Last usage timestamp | DEFAULT NOW |
| transaction_count | INTEGER | Number of transactions | DEFAULT 1 |
| fraud_count | INTEGER | Fraud transactions | DEFAULT 0 |

**Constraints:**
- UNIQUE constraint on `(device_id, account_id)`

**Indexes:**
- `idx_shared_device_id` on `device_id`
- `idx_shared_account_id` on `account_id`
- `idx_shared_fraud_count` on `fraud_count DESC`

---

## **Relationships**

### **1. ACCOUNT → TRANSACTION** (1:N)
- **Type:** One-to-Many
- **Relationship:** One account can have many transactions
- **Foreign Key:** `transaction.account_id` → `account.account_id`
- **Delete Rule:** CASCADE (deleting account deletes its transactions)

### **2. MERCHANT → TRANSACTION** (1:N)
- **Type:** One-to-Many
- **Relationship:** One merchant can process many transactions
- **Foreign Key:** `transaction.merchant_id` → `merchant.merchant_id`
- **Delete Rule:** CASCADE (deleting merchant deletes its transactions)

### **3. DEVICE → TRANSACTION** (1:N)
- **Type:** One-to-Many
- **Relationship:** One device can be used for many transactions
- **Foreign Key:** `transaction.device_id` → `device.device_id`
- **Delete Rule:** SET NULL (deleting device nullifies device_id in transactions)

### **4. DEVICE ↔ ACCOUNT** (M:N through SHARED_DEVICE)
- **Type:** Many-to-Many
- **Relationship:** Multiple accounts can share multiple devices
- **Junction Table:** `shared_device`
- **Foreign Keys:**
  - `shared_device.device_id` → `device.device_id`
  - `shared_device.account_id` → `account.account_id`
- **Delete Rules:** CASCADE (deleting either deletes junction records)

---

## **ER Diagram (Text Representation)**

```
┌─────────────────┐
│     ACCOUNT     │
├─────────────────┤
│ account_id (PK) │───┐
│ creation_date   │   │
│ email_domain    │   │
│ country         │   │
│ risk_score      │   │
│ fraud_flag      │   │
│ ...             │   │
└─────────────────┘   │
                      │
                      │ 1:N
                      │
                      ▼
┌─────────────────┐   ┌───────────────────┐   ┌─────────────────┐
│    MERCHANT     │   │   TRANSACTION     │   │     DEVICE      │
├─────────────────┤   ├───────────────────┤   ├─────────────────┤
│ merchant_id(PK) │◄──┤ transaction_id(PK)│──►│ device_id (PK)  │
│ merchant_name   │1:N│ account_id (FK)   │N:1│ device_type     │
│ category        │   │ merchant_id (FK)  │   │ os_id           │
│ fraud_rate      │   │ device_id (FK)    │   │ is_shared       │
│ risk_level      │   │ amount            │   │ fraud_rate      │
│ ...             │   │ is_fraud (TARGET) │   │ ...             │
└─────────────────┘   │ transaction_date  │   └─────────────────┘
                      │ ...               │            │
                      └───────────────────┘            │
                                                       │
                                                       │ M:N
                                        ┌──────────────┴──────────────┐
                                        │                             │
                                        ▼                             ▼
                                 ┌─────────────────┐         ┌─────────────────┐
                                 │ SHARED_DEVICE   │         │     ACCOUNT     │
                                 ├─────────────────┤         │   (referenced)  │
                                 │ id (PK)         │         └─────────────────┘
                                 │ device_id (FK)  │
                                 │ account_id (FK) │
                                 │ first_seen      │
                                 │ last_seen       │
                                 │ fraud_count     │
                                 └─────────────────┘
```

---

## **Database Triggers**

### **Automatic Statistics Updates**

1. **`trg_update_account_stats`**
   - Fires: AFTER INSERT on `transaction`
   - Updates: `account` statistics (total_transactions, total_amount, fraud_flag)

2. **`trg_update_merchant_stats`**
   - Fires: AFTER INSERT on `transaction`
   - Updates: `merchant` statistics (total_transactions, fraud_rate)

3. **`trg_update_device_stats`**
   - Fires: AFTER INSERT on `transaction`
   - Updates: `device` statistics (total_transactions, fraud_rate)

---

## **Analytical Views**

### **1. high_risk_accounts**
Lists accounts with high fraud risk scores or fraud flags.

### **2. suspicious_merchants**
Shows merchants with high fraud rates or critical risk levels.

### **3. device_sharing_stats**
Analyzes device sharing patterns across multiple accounts.

---

## **Graph Representation Mapping**

### **Node Types:**
1. **Account Nodes** - From `account` table
2. **Merchant Nodes** - From `merchant` table
3. **Device Nodes** - From `device` table

### **Edge Types:**
1. **Account → Transaction → Merchant** (transacts_with)
2. **Account → Transaction → Device** (uses_device)
3. **Account → Shared_Device → Device** (shares_device)

### **Node Features:**
- Account: risk_score, total_transactions, account_age_days, fraud_flag
- Merchant: fraud_rate, total_transactions, risk_level
- Device: fraud_rate, is_shared, total_users

### **Edge Features:**
- Transaction amount
- Transaction timestamp
- Fraud label (target)
- Distance from last transaction
- Time since last transaction

---

## **Data Integrity Rules**

1. **Referential Integrity**: All foreign keys enforced with CASCADE/SET NULL
2. **Domain Constraints**: Risk scores between 0-1, positive amounts
3. **Uniqueness**: No duplicate device-account pairs in `shared_device`
4. **Automatic Updates**: Triggers maintain aggregate statistics
5. **Indexing**: Optimized for fraud detection queries

---

## **Query Optimization Strategy**

- Composite indexes on frequently joined columns
- Separate indexes for filtering (fraud_flag, risk_score)
- Materialized views for complex analytics (can be added as needed)
- Regular ANALYZE updates for query planner

---

**Last Updated:** November 20, 2025
