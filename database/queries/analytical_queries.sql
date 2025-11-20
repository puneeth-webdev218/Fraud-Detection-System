-- =====================================================
-- Common Analytical Queries for Fraud Detection
-- =====================================================

-- Query 1: Get fraud statistics by account
-- =====================================================
SELECT 
    a.account_id,
    a.email_domain,
    a.country,
    COUNT(t.transaction_id) as total_transactions,
    SUM(CASE WHEN t.is_fraud THEN 1 ELSE 0 END) as fraud_transactions,
    SUM(t.transaction_amount) as total_amount,
    AVG(t.transaction_amount) as avg_amount,
    a.risk_score
FROM account a
LEFT JOIN transaction t ON a.account_id = t.account_id
GROUP BY a.account_id, a.email_domain, a.country, a.risk_score
HAVING COUNT(t.transaction_id) > 0
ORDER BY fraud_transactions DESC, risk_score DESC
LIMIT 100;

-- Query 2: Merchant fraud analysis
-- =====================================================
SELECT 
    m.merchant_id,
    m.merchant_name,
    m.merchant_category,
    m.country,
    COUNT(t.transaction_id) as total_transactions,
    SUM(CASE WHEN t.is_fraud THEN 1 ELSE 0 END) as fraud_count,
    ROUND(
        CAST(SUM(CASE WHEN t.is_fraud THEN 1 ELSE 0 END) AS DECIMAL) / 
        COUNT(t.transaction_id) * 100, 2
    ) as fraud_percentage,
    AVG(t.transaction_amount) as avg_transaction_amount
FROM merchant m
LEFT JOIN transaction t ON m.merchant_id = t.merchant_id
GROUP BY m.merchant_id, m.merchant_name, m.merchant_category, m.country
HAVING COUNT(t.transaction_id) > 10
ORDER BY fraud_percentage DESC
LIMIT 50;

-- Query 3: Device sharing patterns
-- =====================================================
SELECT 
    d.device_id,
    d.device_type,
    COUNT(DISTINCT sd.account_id) as shared_accounts,
    SUM(sd.transaction_count) as total_transactions,
    SUM(sd.fraud_count) as total_fraud,
    ROUND(
        CAST(SUM(sd.fraud_count) AS DECIMAL) / 
        NULLIF(SUM(sd.transaction_count), 0) * 100, 2
    ) as fraud_rate
FROM device d
JOIN shared_device sd ON d.device_id = sd.device_id
GROUP BY d.device_id, d.device_type
HAVING COUNT(DISTINCT sd.account_id) > 1
ORDER BY shared_accounts DESC, fraud_rate DESC
LIMIT 100;

-- Query 4: Time-based fraud patterns
-- =====================================================
SELECT 
    transaction_hour,
    COUNT(*) as transaction_count,
    SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) as fraud_count,
    ROUND(
        CAST(SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) AS DECIMAL) / 
        COUNT(*) * 100, 2
    ) as fraud_percentage,
    AVG(transaction_amount) as avg_amount
FROM transaction
WHERE transaction_hour IS NOT NULL
GROUP BY transaction_hour
ORDER BY transaction_hour;

-- Query 5: High-risk account and device combinations
-- =====================================================
SELECT 
    a.account_id,
    d.device_id,
    d.device_type,
    COUNT(t.transaction_id) as transaction_count,
    SUM(CASE WHEN t.is_fraud THEN 1 ELSE 0 END) as fraud_count,
    SUM(t.transaction_amount) as total_amount,
    a.risk_score as account_risk,
    d.risk_score as device_risk
FROM transaction t
JOIN account a ON t.account_id = a.account_id
JOIN device d ON t.device_id = d.device_id
GROUP BY a.account_id, d.device_id, d.device_type, a.risk_score, d.risk_score
HAVING SUM(CASE WHEN t.is_fraud THEN 1 ELSE 0 END) > 0
ORDER BY fraud_count DESC, account_risk DESC
LIMIT 100;

-- Query 6: Geographic fraud patterns
-- =====================================================
SELECT 
    addr_country,
    COUNT(*) as transaction_count,
    SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) as fraud_count,
    ROUND(
        CAST(SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) AS DECIMAL) / 
        COUNT(*) * 100, 2
    ) as fraud_percentage,
    SUM(transaction_amount) as total_amount,
    AVG(transaction_amount) as avg_amount
FROM transaction
WHERE addr_country IS NOT NULL
GROUP BY addr_country
HAVING COUNT(*) > 100
ORDER BY fraud_percentage DESC;

-- Query 7: Card type fraud analysis
-- =====================================================
SELECT 
    card_type,
    card_category,
    COUNT(*) as transaction_count,
    SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) as fraud_count,
    ROUND(
        CAST(SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) AS DECIMAL) / 
        COUNT(*) * 100, 2
    ) as fraud_percentage
FROM transaction
WHERE card_type IS NOT NULL
GROUP BY card_type, card_category
ORDER BY fraud_percentage DESC;

-- Query 8: Suspicious account clusters
-- =====================================================
WITH account_pairs AS (
    SELECT 
        sd1.account_id as account1,
        sd2.account_id as account2,
        COUNT(DISTINCT sd1.device_id) as shared_devices
    FROM shared_device sd1
    JOIN shared_device sd2 ON sd1.device_id = sd2.device_id
    WHERE sd1.account_id < sd2.account_id
    GROUP BY sd1.account_id, sd2.account_id
    HAVING COUNT(DISTINCT sd1.device_id) >= 2
)
SELECT 
    ap.account1,
    ap.account2,
    ap.shared_devices,
    a1.risk_score as risk1,
    a2.risk_score as risk2,
    a1.fraud_flag as fraud1,
    a2.fraud_flag as fraud2
FROM account_pairs ap
JOIN account a1 ON ap.account1 = a1.account_id
JOIN account a2 ON ap.account2 = a2.account_id
ORDER BY ap.shared_devices DESC, a1.risk_score DESC;

-- Query 9: Transaction velocity analysis
-- =====================================================
SELECT 
    account_id,
    DATE(transaction_date) as transaction_day,
    COUNT(*) as daily_transactions,
    SUM(transaction_amount) as daily_amount,
    SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) as daily_fraud
FROM transaction
GROUP BY account_id, DATE(transaction_date)
HAVING COUNT(*) > 5
ORDER BY daily_transactions DESC, daily_fraud DESC
LIMIT 100;

-- Query 10: Email domain risk analysis
-- =====================================================
SELECT 
    a.email_domain,
    COUNT(DISTINCT a.account_id) as account_count,
    COUNT(t.transaction_id) as total_transactions,
    SUM(CASE WHEN t.is_fraud THEN 1 ELSE 0 END) as fraud_transactions,
    ROUND(
        CAST(SUM(CASE WHEN t.is_fraud THEN 1 ELSE 0 END) AS DECIMAL) / 
        NULLIF(COUNT(t.transaction_id), 0) * 100, 2
    ) as fraud_percentage,
    AVG(a.risk_score) as avg_risk_score
FROM account a
LEFT JOIN transaction t ON a.account_id = t.account_id
WHERE a.email_domain IS NOT NULL
GROUP BY a.email_domain
HAVING COUNT(t.transaction_id) > 50
ORDER BY fraud_percentage DESC
LIMIT 50;
