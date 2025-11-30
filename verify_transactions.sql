-- PostgreSQL Query to Verify Transaction Data
-- Run this directly in pgAdmin Query Tool to verify data

-- 1. Check if transactions table exists
SELECT EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name = 'transactions'
) AS "Table Exists?";

-- 2. Count all transactions
SELECT COUNT(*) AS "Total Transactions" FROM transactions;

-- 3. Fraud statistics
SELECT 
    fraud_flag,
    COUNT(*) as "Count",
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM transactions) * 100, 2) as "Percentage (%)"
FROM transactions
GROUP BY fraud_flag
ORDER BY fraud_flag;

-- 4. Show first 10 transactions
SELECT * FROM transactions LIMIT 10;

-- 5. Show last 10 inserted transactions
SELECT * FROM transactions ORDER BY transaction_id DESC LIMIT 10;

-- 6. Fraud rate overall
SELECT 
    COUNT(*) as "Total Transactions",
    SUM(CASE WHEN fraud_flag = 1 THEN 1 ELSE 0 END) as "Fraudulent Count",
    ROUND(SUM(CASE WHEN fraud_flag = 1 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as "Fraud Rate (%)",
    AVG(amount) as "Avg Amount",
    MIN(amount) as "Min Amount",
    MAX(amount) as "Max Amount"
FROM transactions;

-- 7. Distribution by amount
SELECT 
    CASE
        WHEN amount < 50 THEN 'Under $50'
        WHEN amount < 100 THEN '$50-$100'
        WHEN amount < 500 THEN '$100-$500'
        WHEN amount < 1000 THEN '$500-$1000'
        ELSE 'Over $1000'
    END as "Amount Range",
    COUNT(*) as "Count",
    SUM(CASE WHEN fraud_flag = 1 THEN 1 ELSE 0 END) as "Frauds"
FROM transactions
GROUP BY "Amount Range"
ORDER BY 
    CASE
        WHEN amount < 50 THEN 1
        WHEN amount < 100 THEN 2
        WHEN amount < 500 THEN 3
        WHEN amount < 1000 THEN 4
        ELSE 5
    END;

-- 8. Check if transactions are being inserted
SELECT 'Transactions are in database! ✓' as "Status";
