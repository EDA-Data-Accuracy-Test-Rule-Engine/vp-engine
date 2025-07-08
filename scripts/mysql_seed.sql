-- MySQL Seed Data for VP Engine Testing
-- This script creates tables with intentional data quality issues for validation testing

-- Create employees table
CREATE TABLE employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(10) UNIQUE,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20),
    hire_date DATE,
    department VARCHAR(50),
    salary DECIMAL(10,2),
    age INT,
    status VARCHAR(20),
    manager_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create departments table
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dept_code VARCHAR(10) UNIQUE,
    dept_name VARCHAR(100) NOT NULL,
    budget DECIMAL(15,2),
    head_count INT,
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create projects table
CREATE TABLE projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_code VARCHAR(20) UNIQUE,
    project_name VARCHAR(200),
    start_date DATE,
    end_date DATE,
    budget DECIMAL(12,2),
    status VARCHAR(30),
    department_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- Seed departments data (clean data)
INSERT INTO departments (dept_code, dept_name, budget, head_count, location) VALUES
('IT', 'Information Technology', 500000.00, 25, 'Ho Chi Minh City'),
('HR', 'Human Resources', 200000.00, 8, 'Ha Noi'),
('FIN', 'Finance', 300000.00, 12, 'Ho Chi Minh City'),
('MKT', 'Marketing', 250000.00, 15, 'Ha Noi'),
('OPS', 'Operations', 400000.00, 20, 'Da Nang');

-- Seed employees data with INTENTIONAL quality issues for testing
INSERT INTO employees (employee_id, first_name, last_name, email, phone, hire_date, department, salary, age, status, manager_id) VALUES
	-- Valid records
	('EMP001', 'Nguyen', 'Van A', 'nguyenvana@vpbank.com', '0901234567', '2023-01-15', 'IT', 15000.00, 28, 'Active', NULL),
	('EMP002', 'Tran', 'Thi B', 'tranthib@vpbank.com', '0902345678', '2023-02-01', 'HR', 12000.00, 32, 'Active', 1),
	('EMP003', 'Le', 'Van C', 'levanc@vpbank.com', '0903456789', '2023-03-10', 'FIN', 18000.00, 35, 'Active', NULL),
	-- NULL values in required fields (should fail null_check)
	('EMP004', NULL, 'Thi D', 'tranthid@vpbank.com', '0904567890', '2023-04-05', 'MKT', 14000.00, 29, 'Active', 3),
	('EMP005', 'Pham', NULL, 'phamvane@vpbank.com', '0905678901', '2023-05-12', 'OPS', NULL, 31, 'Active', NULL),
	('EMP006', 'Vo', 'Van F', NULL, '0906789012', '2023-06-18', 'IT', 16000.00, 27, 'Active', 1),
	-- Invalid email formats (should fail regex_check)
	('EMP007', 'Dang', 'Thi G', 'dangthig.invalid.email', '0907890123', '2023-07-20', 'HR', 13000.00, 30, 'Active', 2),
	('EMP008', 'Bui', 'Van H', 'buivanh@', '0908901234', '2023-08-15', 'FIN', 17000.00, 33, 'Active', 3),
	('EMP009', 'Hoang', 'Thi I', '@vpbank.com', '0909012345', '2023-09-10', 'MKT', 15500.00, 26, 'Active', NULL),
	-- Duplicate email addresses (should fail duplicate_check)
	('EMP010', 'Luu', 'Van J', 'nguyenvana@vpbank.com', '0910123456', '2023-10-05', 'OPS', 14500.00, 29, 'Active', NULL),
	('EMP011', 'Do', 'Thi K', 'tranthib@vpbank.com', '0911234567', '2023-11-12', 'IT', 16500.00, 31, 'Active', 1),
	-- Invalid age ranges (should fail range_check)
	('EMP012', 'Trinh', 'Van L', 'trinhvanl@vpbank.com', '0912345678', '2023-12-01', 'HR', 13500.00, 15, 'Active', 2), -- Too young
	('EMP013', 'Mai', 'Thi M', 'maithim@vpbank.com', '0913456789', '2024-01-15', 'FIN', 19000.00, 75, 'Active', 3), -- Too old
	('EMP014', 'Ngo', 'Van N', 'ngovann@vpbank.com', '0914567890', '2024-02-20', 'MKT', 14800.00, -5, 'Active', NULL), -- Negative age
	-- Invalid phone numbers (should fail regex_check)
	('EMP015', 'Cao', 'Thi O', 'caothio@vpbank.com', '123456', '2024-03-10', 'OPS', 15200.00, 28, 'Active', NULL), -- Too short
	('EMP016', 'Dinh', 'Van P', 'dinhvanp@vpbank.com', 'invalid-phone', '2024-04-05', 'IT', 16800.00, 30, 'Active', 1),
	-- Invalid departments (should fail enum validation)
	('EMP017', 'Ly', 'Thi Q', 'lythiq@vpbank.com', '0917890123', '2024-05-15', 'INVALID_DEPT', 15800.00, 32, 'Active', NULL),
	('EMP018', 'Tang', 'Van R', 'tangvanr@vpbank.com', '0918901234', '2024-06-20', 'NON_EXISTENT', 17200.00, 29, 'Active', 2),
	-- Invalid salary ranges (should fail range_check)
	('EMP019', 'Vu', 'Thi S', 'vuthis@vpbank.com', '0919012345', '2024-07-10', 'HR', -1000.00, 31, 'Active', 2), -- Negative salary
	('EMP020', 'Ha', 'Van T', 'havant@vpbank.com', '0920123456', '2024-08-15', 'FIN', 99999.99, 28, 'Active', 3); -- Max salary

-- Seed projects data
INSERT INTO projects (project_code, project_name, start_date, end_date, budget, status, department_id) VALUES
('PRJ001', 'Digital Banking Platform', '2024-01-01', '2024-12-31', 2000000.00, 'In Progress', 1),
('PRJ002', 'HR Management System', '2024-03-01', '2024-09-30', 800000.00, 'Planning', 2),
('PRJ003', 'Financial Analytics Dashboard', '2024-02-15', '2024-11-15', 1500000.00, 'In Progress', 3),
('PRJ004', 'Marketing Automation', '2024-04-01', '2024-10-31', 1200000.00, 'Not Started', 4),
('PRJ005', 'Operations Optimization', '2024-05-01', '2025-02-28', 1800000.00, 'Planning', 5);

-- Create indexes for better performance
CREATE INDEX idx_employees_email ON employees(email);
CREATE INDEX idx_employees_department ON employees(department);
CREATE INDEX idx_employees_status ON employees(status);
CREATE INDEX idx_projects_status ON projects(status);

-- Display summary of created data
SELECT 'Data seeding completed successfully for MySQL!' as message;
SELECT CONCAT('Total employees created: ', COUNT(*)) as summary FROM employees;
SELECT CONCAT('Total departments created: ', COUNT(*)) as summary FROM departments;
SELECT CONCAT('Total projects created: ', COUNT(*)) as summary FROM projects;