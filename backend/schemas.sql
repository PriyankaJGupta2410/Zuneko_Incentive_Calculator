CREATE TABLE uploaded_files (
  id CHAR(36) PRIMARY KEY,
  file_name VARCHAR(255),
  file_type VARCHAR(50),
  uploaded_at DATETIME,
  total_records INT DEFAULT 0,
  invalid_rows_count INT DEFAULT 0,
  invalid_rows JSON DEFAULT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sales_transactions (
  id CHAR(36) PRIMARY KEY,
  employee_id VARCHAR(50),
  branch VARCHAR(100),
  role VARCHAR(50),
  vehicle_model VARCHAR(100),
  vehicle_type VARCHAR(50),
  quantity INT,
  sale_date DATE,
  upload_file_id CHAR(36),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (upload_file_id) REFERENCES uploaded_files(id)
);

CREATE TABLE structured_rules (
    id VARCHAR(36) PRIMARY KEY,
    rule_id VARCHAR(50),
    role VARCHAR(50),
    vehicle_type VARCHAR(50),
    min_units INT,
    max_units INT,
    incentive_amount_inr FLOAT,
    bonus_per_unit_inr FLOAT,
    valid_from DATE,
    valid_to DATE,
    rule_type VARCHAR(50),
    upload_file_id VARCHAR(36),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_file_id) REFERENCES uploaded_files(id)
);

CREATE TABLE ad_hoc_rules (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()), -- UUID for each row
    scheme_id INT NOT NULL,                    -- group multiple rows under same scheme
    scheme_name VARCHAR(255) NOT NULL,
    conditions TEXT NOT NULL,                 -- incentive condition
    role VARCHAR(255) NOT NULL,                -- eligible roles
    bonus_amount VARCHAR(50),                  -- numeric, "Variable" or "1.5x base"
    validity_from DATE NOT NULL,
    validity_to DATE NOT NULL,
    notes TEXT,
    upload_file_id CHAR(36) NOT NULL,          -- FK to uploaded_files
    created_at DATETIME NOT NULL,
    CONSTRAINT fk_upload_file FOREIGN KEY (upload_file_id)
        REFERENCES uploaded_files(id)
        ON DELETE CASCADE
);

CREATE TABLE incentive_calculations (
    id CHAR(36) PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    total_incentive DOUBLE NOT NULL,
    structured_incentive DOUBLE NOT NULL,
    ad_hoc_incentive DOUBLE NOT NULL,
    calculation_date DATETIME NOT NULL,
    details LONGTEXT NOT NULL,
    created_at DATETIME NOT NULL
);
