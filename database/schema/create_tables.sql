-- =====================================================
-- Fraud Detection Database Schema
-- PostgreSQL 13+
-- =====================================================

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS shared_device CASCADE;
DROP TABLE IF EXISTS transaction CASCADE;
DROP TABLE IF EXISTS device CASCADE;
DROP TABLE IF EXISTS merchant CASCADE;
DROP TABLE IF EXISTS account CASCADE;

-- =====================================================
-- Table: ACCOUNT
-- Stores user account information and risk profiles
-- =====================================================
CREATE TABLE account (
    account_id VARCHAR(50) PRIMARY KEY,
    creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    email_domain VARCHAR(100),
    country VARCHAR(50),
    risk_score DECIMAL(5, 4) DEFAULT 0.0000,
    total_transactions INTEGER DEFAULT 0,
    total_amount DECIMAL(12, 2) DEFAULT 0.00,
    fraud_flag BOOLEAN DEFAULT FALSE,
    last_transaction_date TIMESTAMP,
    account_age_days INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster lookups
CREATE INDEX idx_account_risk_score ON account(risk_score DESC);
CREATE INDEX idx_account_fraud_flag ON account(fraud_flag);
CREATE INDEX idx_account_email_domain ON account(email_domain);
CREATE INDEX idx_account_country ON account(country);

-- =====================================================
-- Table: MERCHANT
-- Stores merchant/business information
-- =====================================================
CREATE TABLE merchant (
    merchant_id VARCHAR(50) PRIMARY KEY,
    merchant_name VARCHAR(200),
    merchant_category VARCHAR(100),
    country VARCHAR(50),
    total_transactions INTEGER DEFAULT 0,
    total_fraud_transactions INTEGER DEFAULT 0,
    fraud_rate DECIMAL(5, 4) DEFAULT 0.0000,
    avg_transaction_amount DECIMAL(12, 2),
    risk_level VARCHAR(20) CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for merchant analysis
CREATE INDEX idx_merchant_category ON merchant(merchant_category);
CREATE INDEX idx_merchant_fraud_rate ON merchant(fraud_rate DESC);
CREATE INDEX idx_merchant_risk_level ON merchant(risk_level);

-- =====================================================
-- Table: DEVICE
-- Stores device information used for transactions
-- =====================================================
CREATE TABLE device (
    device_id VARCHAR(50) PRIMARY KEY,
    device_type VARCHAR(50),
    device_info VARCHAR(200),
    os_id VARCHAR(50),
    browser_id VARCHAR(50),
    screen_resolution VARCHAR(50),
    total_users INTEGER DEFAULT 0,
    total_transactions INTEGER DEFAULT 0,
    fraud_transactions INTEGER DEFAULT 0,
    fraud_rate DECIMAL(5, 4) DEFAULT 0.0000,
    is_shared BOOLEAN DEFAULT FALSE,
    risk_score DECIMAL(5, 4) DEFAULT 0.0000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for device analysis
CREATE INDEX idx_device_type ON device(device_type);
CREATE INDEX idx_device_shared ON device(is_shared);
CREATE INDEX idx_device_fraud_rate ON device(fraud_rate DESC);
CREATE INDEX idx_device_risk_score ON device(risk_score DESC);

-- =====================================================
-- Table: TRANSACTION
-- Stores individual transaction records
-- =====================================================
CREATE TABLE transaction (
    transaction_id VARCHAR(50) PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    merchant_id VARCHAR(50) NOT NULL,
    device_id VARCHAR(50),
    transaction_date TIMESTAMP NOT NULL,
    transaction_amount DECIMAL(12, 2) NOT NULL,
    product_category VARCHAR(10),
    card_type VARCHAR(50),
    card_category VARCHAR(50),
    transaction_type VARCHAR(50),
    
    -- Geographic information
    addr_country VARCHAR(50),
    
    -- Time-based features
    transaction_hour INTEGER,
    transaction_day_of_week INTEGER,
    transaction_day_of_month INTEGER,
    
    -- Email and identity features
    email_domain VARCHAR(100),
    
    -- Distance features (for fraud detection)
    distance_from_last_txn DECIMAL(12, 2),
    time_since_last_txn INTEGER, -- in seconds
    
    -- Fraud label (TARGET)
    is_fraud BOOLEAN NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_transaction_account FOREIGN KEY (account_id) 
        REFERENCES account(account_id) ON DELETE CASCADE,
    CONSTRAINT fk_transaction_merchant FOREIGN KEY (merchant_id) 
        REFERENCES merchant(merchant_id) ON DELETE CASCADE,
    CONSTRAINT fk_transaction_device FOREIGN KEY (device_id) 
        REFERENCES device(device_id) ON DELETE SET NULL
);

-- Indexes for transaction queries
CREATE INDEX idx_transaction_account ON transaction(account_id);
CREATE INDEX idx_transaction_merchant ON transaction(merchant_id);
CREATE INDEX idx_transaction_device ON transaction(device_id);
CREATE INDEX idx_transaction_date ON transaction(transaction_date DESC);
CREATE INDEX idx_transaction_fraud ON transaction(is_fraud);
CREATE INDEX idx_transaction_amount ON transaction(transaction_amount DESC);
CREATE INDEX idx_transaction_composite ON transaction(account_id, transaction_date);

-- =====================================================
-- Table: SHARED_DEVICE
-- Tracks device sharing between multiple accounts
-- =====================================================
CREATE TABLE shared_device (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    transaction_count INTEGER DEFAULT 1,
    fraud_count INTEGER DEFAULT 0,
    
    -- Foreign Keys
    CONSTRAINT fk_shared_device FOREIGN KEY (device_id) 
        REFERENCES device(device_id) ON DELETE CASCADE,
    CONSTRAINT fk_shared_account FOREIGN KEY (account_id) 
        REFERENCES account(account_id) ON DELETE CASCADE,
    
    -- Unique constraint to prevent duplicates
    CONSTRAINT unique_device_account UNIQUE (device_id, account_id)
);

-- Indexes for shared device analysis
CREATE INDEX idx_shared_device_id ON shared_device(device_id);
CREATE INDEX idx_shared_account_id ON shared_device(account_id);
CREATE INDEX idx_shared_fraud_count ON shared_device(fraud_count DESC);

-- =====================================================
-- Views for Analysis
-- =====================================================

-- View: High-risk accounts
CREATE OR REPLACE VIEW high_risk_accounts AS
SELECT 
    a.account_id,
    a.email_domain,
    a.country,
    a.risk_score,
    a.total_transactions,
    a.total_amount,
    COUNT(t.transaction_id) as fraud_transactions
FROM account a
LEFT JOIN transaction t ON a.account_id = t.account_id AND t.is_fraud = TRUE
WHERE a.risk_score > 0.5 OR a.fraud_flag = TRUE
GROUP BY a.account_id, a.email_domain, a.country, a.risk_score, 
         a.total_transactions, a.total_amount
ORDER BY a.risk_score DESC;

-- View: Suspicious merchants
CREATE OR REPLACE VIEW suspicious_merchants AS
SELECT 
    m.merchant_id,
    m.merchant_name,
    m.merchant_category,
    m.country,
    m.total_transactions,
    m.total_fraud_transactions,
    m.fraud_rate,
    m.risk_level
FROM merchant m
WHERE m.fraud_rate > 0.1 OR m.risk_level IN ('HIGH', 'CRITICAL')
ORDER BY m.fraud_rate DESC;

-- View: Shared device analysis
CREATE OR REPLACE VIEW device_sharing_stats AS
SELECT 
    d.device_id,
    d.device_type,
    d.is_shared,
    COUNT(DISTINCT sd.account_id) as unique_accounts,
    SUM(sd.transaction_count) as total_transactions,
    SUM(sd.fraud_count) as total_fraud,
    CASE 
        WHEN SUM(sd.transaction_count) > 0 
        THEN CAST(SUM(sd.fraud_count) AS DECIMAL) / SUM(sd.transaction_count)
        ELSE 0 
    END as fraud_rate
FROM device d
LEFT JOIN shared_device sd ON d.device_id = sd.device_id
GROUP BY d.device_id, d.device_type, d.is_shared
HAVING COUNT(DISTINCT sd.account_id) > 1
ORDER BY unique_accounts DESC, fraud_rate DESC;

-- =====================================================
-- Functions for automatic updates
-- =====================================================

-- Function to update account statistics
CREATE OR REPLACE FUNCTION update_account_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE account
    SET 
        total_transactions = total_transactions + 1,
        total_amount = total_amount + NEW.transaction_amount,
        last_transaction_date = NEW.transaction_date,
        fraud_flag = CASE 
            WHEN NEW.is_fraud THEN TRUE 
            ELSE fraud_flag 
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE account_id = NEW.account_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for account stats update
DROP TRIGGER IF EXISTS trg_update_account_stats ON transaction;
CREATE TRIGGER trg_update_account_stats
AFTER INSERT ON transaction
FOR EACH ROW
EXECUTE FUNCTION update_account_stats();

-- Function to update merchant statistics
CREATE OR REPLACE FUNCTION update_merchant_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE merchant
    SET 
        total_transactions = total_transactions + 1,
        total_fraud_transactions = total_fraud_transactions + 
            CASE WHEN NEW.is_fraud THEN 1 ELSE 0 END,
        fraud_rate = CASE 
            WHEN total_transactions + 1 > 0 
            THEN CAST(total_fraud_transactions + 
                 CASE WHEN NEW.is_fraud THEN 1 ELSE 0 END AS DECIMAL) / 
                 (total_transactions + 1)
            ELSE 0 
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE merchant_id = NEW.merchant_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for merchant stats update
DROP TRIGGER IF EXISTS trg_update_merchant_stats ON transaction;
CREATE TRIGGER trg_update_merchant_stats
AFTER INSERT ON transaction
FOR EACH ROW
EXECUTE FUNCTION update_merchant_stats();

-- Function to update device statistics
CREATE OR REPLACE FUNCTION update_device_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE device
    SET 
        total_transactions = total_transactions + 1,
        fraud_transactions = fraud_transactions + 
            CASE WHEN NEW.is_fraud THEN 1 ELSE 0 END,
        fraud_rate = CASE 
            WHEN total_transactions + 1 > 0 
            THEN CAST(fraud_transactions + 
                 CASE WHEN NEW.is_fraud THEN 1 ELSE 0 END AS DECIMAL) / 
                 (total_transactions + 1)
            ELSE 0 
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE device_id = NEW.device_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for device stats update
DROP TRIGGER IF EXISTS trg_update_device_stats ON transaction;
CREATE TRIGGER trg_update_device_stats
AFTER INSERT ON transaction
FOR EACH ROW
EXECUTE FUNCTION update_device_stats();

-- =====================================================
-- Sample data validation constraints
-- =====================================================

-- Check constraint for valid risk scores
ALTER TABLE account ADD CONSTRAINT chk_account_risk_score 
    CHECK (risk_score >= 0 AND risk_score <= 1);

ALTER TABLE device ADD CONSTRAINT chk_device_risk_score 
    CHECK (risk_score >= 0 AND risk_score <= 1);

-- Check constraint for positive amounts
ALTER TABLE transaction ADD CONSTRAINT chk_transaction_amount_positive 
    CHECK (transaction_amount >= 0);

-- Check constraint for valid hours
ALTER TABLE transaction ADD CONSTRAINT chk_transaction_hour 
    CHECK (transaction_hour >= 0 AND transaction_hour <= 23);

-- Check constraint for valid day of week
ALTER TABLE transaction ADD CONSTRAINT chk_transaction_day_of_week 
    CHECK (transaction_day_of_week >= 0 AND transaction_day_of_week <= 6);

-- =====================================================
-- Performance optimization
-- =====================================================

-- Analyze tables for query optimization
ANALYZE account;
ANALYZE merchant;
ANALYZE device;
ANALYZE transaction;
ANALYZE shared_device;

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO fraud_app_user;

COMMENT ON TABLE account IS 'Stores user account information and risk profiles';
COMMENT ON TABLE merchant IS 'Stores merchant/business information and fraud statistics';
COMMENT ON TABLE device IS 'Stores device information used for transactions';
COMMENT ON TABLE transaction IS 'Stores individual transaction records with fraud labels';
COMMENT ON TABLE shared_device IS 'Tracks device sharing patterns between accounts';
