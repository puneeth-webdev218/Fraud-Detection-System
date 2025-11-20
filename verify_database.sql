-- =====================================================
-- PostgreSQL Database Verification Script
-- Run this in psql or pgAdmin Query Tool
-- =====================================================

-- Connect to database
\c fraud_detection

-- 1. Check all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- 2. Check row counts for each table
SELECT 
    'account' as table_name, 
    COUNT(*) as row_count 
FROM account
UNION ALL
SELECT 'merchant', COUNT(*) FROM merchant
UNION ALL
SELECT 'device', COUNT(*) FROM device
UNION ALL
SELECT 'transaction', COUNT(*) FROM transaction
UNION ALL
SELECT 'shared_device', COUNT(*) FROM shared_device;

-- 3. Check transaction fraud distribution
SELECT 
    is_fraud,
    COUNT(*) as count,
    ROUND(COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM transaction) * 100, 2) as percentage
FROM transaction
GROUP BY is_fraud;

-- 4. Sample transactions
SELECT 
    transaction_id,
    account_id,
    merchant_id,
    transaction_amount,
    transaction_date,
    is_fraud
FROM transaction
ORDER BY transaction_date DESC
LIMIT 10;

-- 5. High-risk accounts
SELECT 
    account_id,
    total_transactions,
    total_amount,
    risk_score,
    fraud_flag
FROM account
WHERE risk_score > 0.5
ORDER BY risk_score DESC
LIMIT 10;

-- 6. Merchant fraud rates
SELECT 
    merchant_id,
    total_transactions,
    total_fraud_transactions,
    fraud_rate,
    risk_level
FROM merchant
ORDER BY fraud_rate DESC;

-- 7. Shared devices
SELECT 
    device_id,
    total_users,
    total_transactions,
    fraud_rate,
    is_shared
FROM device
WHERE total_users > 1
ORDER BY fraud_rate DESC
LIMIT 10;

-- 8. Check foreign key relationships
SELECT 
    COUNT(DISTINCT t.account_id) as accounts_with_transactions,
    COUNT(DISTINCT t.merchant_id) as merchants_with_transactions,
    COUNT(DISTINCT t.device_id) as devices_with_transactions
FROM transaction t;

-- 9. Data quality checks
SELECT 
    'NULL account_id' as check_type,
    COUNT(*) as count
FROM transaction WHERE account_id IS NULL
UNION ALL
SELECT 'NULL merchant_id', COUNT(*) FROM transaction WHERE merchant_id IS NULL
UNION ALL
SELECT 'NULL device_id', COUNT(*) FROM transaction WHERE device_id IS NULL
UNION ALL
SELECT 'NULL amount', COUNT(*) FROM transaction WHERE transaction_amount IS NULL
UNION ALL
SELECT 'Negative amount', COUNT(*) FROM transaction WHERE transaction_amount < 0;

-- 10. Database size
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'fraud_detection';
