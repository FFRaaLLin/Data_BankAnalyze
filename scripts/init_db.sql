CREATE DATABASE IF NOT EXISTS bill_classification DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

USE bill_classification;

CREATE TABLE IF NOT EXISTS unknown_forms (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  transaction_date VARCHAR(32) NOT NULL,
  bank VARCHAR(64) NOT NULL,
  bank_account VARCHAR(128) NOT NULL,
  flow_type VARCHAR(32) NOT NULL,
  counterparty_account VARCHAR(128) NOT NULL,
  transaction_details VARCHAR(512) NOT NULL,
  withdrawals DECIMAL(18,2) NOT NULL DEFAULT 0,
  lodgment DECIMAL(18,2) NOT NULL DEFAULT 0,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  last_error TEXT NULL,
  version INT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_unknown_forms_bank_account (bank_account)
);

CREATE TABLE IF NOT EXISTS sync_tasks (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  task_type VARCHAR(32) NOT NULL DEFAULT 'export',
  status VARCHAR(32) NOT NULL DEFAULT 'created',
  payload JSON NOT NULL,
  callback_payload JSON NULL,
  retry_count INT NOT NULL DEFAULT 0,
  next_retry_at DATETIME NULL,
  error_message TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS classification_results (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  form_id BIGINT NOT NULL,
  category_code VARCHAR(64) NOT NULL,
  category_name VARCHAR(128) NOT NULL,
  reviewer VARCHAR(64) NOT NULL,
  reviewed_at DATETIME NOT NULL,
  confidence DECIMAL(5,4) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uk_classification_form UNIQUE(form_id),
  CONSTRAINT fk_classification_form FOREIGN KEY(form_id) REFERENCES unknown_forms(id)
);

CREATE TABLE IF NOT EXISTS retry_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  task_id BIGINT NOT NULL,
  retry_no INT NOT NULL,
  reason TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_retry_task FOREIGN KEY(task_id) REFERENCES sync_tasks(id)
);
