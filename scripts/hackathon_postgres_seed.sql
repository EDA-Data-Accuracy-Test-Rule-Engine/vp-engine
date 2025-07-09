-- PostgreSQL Seed Data for VP Engine Testing
-- Database mẫu theo yêu cầu Hackathon Challenge
-- This script creates tables with data to test all 5 rule types

-- Drop existing tables if they exist
DROP TABLE IF EXISTS transaction_summary CASCADE;
DROP TABLE IF EXISTS overdue_loan_payments CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS table_b CASCADE;
DROP TABLE IF EXISTS table_a CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- 1. Table cho Rule Type 1: Value Range Testing
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    amount_usd DECIMAL(10,2),
    customer_id INTEGER,
    transaction_date DATE,
    branch_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Table cho Rule Type 2: Value Template Testing  
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    email VARCHAR(100),
    phone VARCHAR(20),
    full_name VARCHAR(100),
    age INTEGER,
    salary DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Table cho Rule Type 3: Data Continuity Testing
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    employee_code VARCHAR(20),
    full_name VARCHAR(100),
    department VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tables cho Rule Type 4: Same Statistical Comparison
CREATE TABLE table_a (
    id SERIAL PRIMARY KEY,
    branch_code VARCHAR(10),
    amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE table_b (
    id SERIAL PRIMARY KEY,
    branch_code VARCHAR(10),
    total DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tables cho Rule Type 5: Different Statistical Comparison
CREATE TABLE overdue_loan_payments (
    contract_nbr VARCHAR(20) PRIMARY KEY,
    overdue_principal_payment DECIMAL(10,2),
    overdue_principal_penalty DECIMAL(10,2),
    overdue_interest_payment DECIMAL(10,2),
    overdue_interest_penalty DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transaction_summary (
    contract_nbr VARCHAR(20) PRIMARY KEY,
    repayment_amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SEED DATA
-- Rule Type 1: Value Range Testing (Amount 100-10000 USD)
INSERT INTO transactions (amount_usd, customer_id, transaction_date, branch_code) VALUES
(500, 1001, '2024-01-15', 'HCM001'),     -- ✅ Valid: Within range
(50, 1002, '2024-01-16', 'HN001'),       -- ❌ Invalid: Below range
(7500, 1003, '2024-01-17', 'DN001'),     -- ✅ Valid: Within range
(15000, 1004, '2024-01-18', 'HCM001'),   -- ❌ Invalid: Above range
(1000, 1005, '2024-01-19', 'HN001'),     -- ✅ Valid: Within range
(25, 1006, '2024-01-20', 'DN001'),       -- ❌ Invalid: Below range
(9999, 1007, '2024-01-21', 'HCM001'),    -- ✅ Valid: Edge case
(10001, 1008, '2024-01-22', 'HN001');    -- ❌ Invalid: Above range

-- Rule Type 2: Value Template Testing
INSERT INTO customers (email, phone, full_name, age, salary) VALUES
('user@example.com', '+84 912345678', 'Nguyen Van A', 25, 15000000),      -- ✅ Valid email & phone
('user@.com', '0912 345 678', 'Tran Thi B', 30, 20000000),               -- ❌ Invalid email, ✅ Valid phone
('valid.email@domain.com', '123456', 'Le Van C', 35, 25000000),          -- ✅ Valid email, ❌ Invalid phone
('invalid-email', '+84987654321', 'Pham Thi D', 28, 18000000),           -- ❌ Invalid email, ✅ Valid phone
('test@company.co.uk', '0901234567', 'Vo Van E', 32, 22000000),          -- ✅ Valid email & phone
('no-at-sign.com', 'not-a-number', 'Hoang Thi F', 29, 19000000),         -- ❌ Invalid email & phone
('good@test.org', '+84 123 456 789', 'Dang Van G', 27, 16000000),        -- ✅ Valid email & phone
('bad@', '090123456789012', 'Bui Thi H', 31, 21000000);                  -- ❌ Invalid email, ❌ Invalid phone (too long)

-- Rule Type 3: Data Continuity Testing (Sequential IDs)
INSERT INTO employees (id, employee_code, full_name, department) VALUES
(1, 'EMP-00001', 'Nguyen Van A', 'IT'),
(2, 'EMP-00002', 'Tran Thi B', 'HR'),
(3, 'EMP-00003', 'Le Van C', 'Finance'),
-- Missing ID 4 - Gap in sequence
(5, 'EMP-00005', 'Pham Thi D', 'Marketing'),
(6, 'EMP-00006', 'Vo Van E', 'Operations'),
(7, 'EMP-00007', 'Hoang Thi F', 'IT'),
-- Missing ID 8 - Another gap
(9, 'EMP-00009', 'Dang Van G', 'HR'),
(10, 'EMP-00010', 'Bui Thi H', 'Finance');

-- Rule Type 4: Same Statistical Comparison (Branch codes should match)
INSERT INTO table_a (branch_code, amount) VALUES
('HCM001', 1000.00),
('HN001', 1500.00),
('DN001', 2000.00),
('CT001', 1200.00),
('HP001', 1800.00);

INSERT INTO table_b (branch_code, total) VALUES
('HCM001', 1000.00),  -- ✅ Matches table_a
('HN001', 1500.00),   -- ✅ Matches table_a  
('DN001', 2000.00),   -- ✅ Matches table_a
('CT001', 1200.00),   -- ✅ Matches table_a
('HCM002', 1300.00);  -- ❌ Extra branch code not in table_a

-- Rule Type 5: Different Statistical Comparison
-- Sum(overdue payments) should equal repayment_amount
INSERT INTO overdue_loan_payments (contract_nbr, overdue_principal_payment, overdue_principal_penalty, overdue_interest_payment, overdue_interest_penalty) VALUES
('50001', 1000, 200, 300, 50),  -- Sum = 1550
('60002', 1200, 250, 400, 60),  -- Sum = 1910  
('70003', 800, 150, 200, 30),   -- Sum = 1180
('80004', 1500, 300, 500, 100), -- Sum = 2400
('90005', 900, 180, 250, 40);   -- Sum = 1370

INSERT INTO transaction_summary (contract_nbr, repayment_amount) VALUES
('50001', 1550),  -- ✅ Matches sum from overdue_loan_payments
('60002', 1910),  -- ✅ Matches sum from overdue_loan_payments
('70003', 1200),  -- ❌ Does not match (should be 1180)
('80004', 2400),  -- ✅ Matches sum from overdue_loan_payments  
('90005', 1400);  -- ❌ Does not match (should be 1370)

-- Create indexes for performance
CREATE INDEX idx_transactions_amount ON transactions(amount_usd);
CREATE INDEX idx_transactions_branch ON transactions(branch_code);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_employees_id ON employees(id);
CREATE INDEX idx_table_a_branch ON table_a(branch_code);
CREATE INDEX idx_table_b_branch ON table_b(branch_code);
CREATE INDEX idx_overdue_contract ON overdue_loan_payments(contract_nbr);
CREATE INDEX idx_summary_contract ON transaction_summary(contract_nbr);

-- Summary information
SELECT 'Hackathon Challenge Database created successfully!' as message;
SELECT 'Rule Type 1 - Transactions: ' || COUNT(*) || ' records' as summary FROM transactions;
SELECT 'Rule Type 2 - Customers: ' || COUNT(*) || ' records' as summary FROM customers;  
SELECT 'Rule Type 3 - Employees: ' || COUNT(*) || ' records (with gaps in sequence)' as summary FROM employees;
SELECT 'Rule Type 4 - Table A: ' || COUNT(*) || ' records' as summary FROM table_a;
SELECT 'Rule Type 4 - Table B: ' || COUNT(*) || ' records' as summary FROM table_b;
SELECT 'Rule Type 5 - Overdue Payments: ' || COUNT(*) || ' records' as summary FROM overdue_loan_payments;
SELECT 'Rule Type 5 - Transaction Summary: ' || COUNT(*) || ' records' as summary FROM transaction_summary;