-- ============================================================================
-- AZALS MODULE M2 - FINANCE (Comptabilité + Trésorerie)
-- Migration: 017_finance_module.sql
-- ============================================================================

-- Types enum pour le module Finance
CREATE TYPE account_type AS ENUM ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE');
CREATE TYPE journal_type AS ENUM ('GENERAL', 'PURCHASES', 'SALES', 'BANK', 'CASH', 'OD', 'OPENING', 'CLOSING');
CREATE TYPE entry_status AS ENUM ('DRAFT', 'PENDING', 'VALIDATED', 'POSTED', 'CANCELLED');
CREATE TYPE fiscal_year_status AS ENUM ('OPEN', 'CLOSING', 'CLOSED');
CREATE TYPE bank_transaction_type AS ENUM ('CREDIT', 'DEBIT', 'TRANSFER', 'FEE', 'INTEREST');
CREATE TYPE reconciliation_status AS ENUM ('PENDING', 'MATCHED', 'RECONCILED', 'DISPUTED');
CREATE TYPE forecast_period AS ENUM ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY');

-- ============================================================================
-- PLAN COMPTABLE
-- ============================================================================

-- Table des comptes comptables
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type account_type NOT NULL,
    parent_id UUID REFERENCES accounts(id),
    is_auxiliary BOOLEAN DEFAULT FALSE,
    auxiliary_type VARCHAR(50),
    is_reconcilable BOOLEAN DEFAULT FALSE,
    allow_posting BOOLEAN DEFAULT TRUE,
    balance_debit DECIMAL(15, 2) DEFAULT 0,
    balance_credit DECIMAL(15, 2) DEFAULT 0,
    balance DECIMAL(15, 2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_account_code UNIQUE (tenant_id, code)
);

CREATE INDEX idx_accounts_tenant ON accounts(tenant_id);
CREATE INDEX idx_accounts_type ON accounts(tenant_id, type);
CREATE INDEX idx_accounts_parent ON accounts(tenant_id, parent_id);
CREATE INDEX idx_accounts_code ON accounts(tenant_id, code);

-- ============================================================================
-- JOURNAUX COMPTABLES
-- ============================================================================

CREATE TABLE journals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    type journal_type NOT NULL,
    default_debit_account_id UUID REFERENCES accounts(id),
    default_credit_account_id UUID REFERENCES accounts(id),
    sequence_prefix VARCHAR(20),
    next_sequence INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_journal_code UNIQUE (tenant_id, code)
);

CREATE INDEX idx_journals_tenant ON journals(tenant_id);
CREATE INDEX idx_journals_type ON journals(tenant_id, type);

-- ============================================================================
-- EXERCICES FISCAUX
-- ============================================================================

CREATE TABLE fiscal_years (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status fiscal_year_status DEFAULT 'OPEN',
    closed_at TIMESTAMP,
    closed_by UUID,
    total_debit DECIMAL(15, 2) DEFAULT 0,
    total_credit DECIMAL(15, 2) DEFAULT 0,
    result DECIMAL(15, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_fiscal_year_code UNIQUE (tenant_id, code)
);

CREATE INDEX idx_fiscal_years_tenant ON fiscal_years(tenant_id);
CREATE INDEX idx_fiscal_years_dates ON fiscal_years(tenant_id, start_date, end_date);
CREATE INDEX idx_fiscal_years_status ON fiscal_years(tenant_id, status);

-- Périodes fiscales (mois)
CREATE TABLE fiscal_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    fiscal_year_id UUID NOT NULL REFERENCES fiscal_years(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    number INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_closed BOOLEAN DEFAULT FALSE,
    closed_at TIMESTAMP,
    closed_by UUID,
    total_debit DECIMAL(15, 2) DEFAULT 0,
    total_credit DECIMAL(15, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fiscal_periods_year ON fiscal_periods(fiscal_year_id);
CREATE INDEX idx_fiscal_periods_tenant ON fiscal_periods(tenant_id);

-- ============================================================================
-- ÉCRITURES COMPTABLES
-- ============================================================================

CREATE TABLE journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    journal_id UUID NOT NULL REFERENCES journals(id),
    fiscal_year_id UUID NOT NULL REFERENCES fiscal_years(id),
    number VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    reference VARCHAR(100),
    description TEXT,
    status entry_status DEFAULT 'DRAFT',
    total_debit DECIMAL(15, 2) DEFAULT 0,
    total_credit DECIMAL(15, 2) DEFAULT 0,
    source_type VARCHAR(50),
    source_id UUID,
    validated_by UUID,
    validated_at TIMESTAMP,
    posted_by UUID,
    posted_at TIMESTAMP,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_entry_number UNIQUE (tenant_id, journal_id, fiscal_year_id, number)
);

CREATE INDEX idx_entries_tenant ON journal_entries(tenant_id);
CREATE INDEX idx_entries_journal ON journal_entries(tenant_id, journal_id);
CREATE INDEX idx_entries_fiscal_year ON journal_entries(tenant_id, fiscal_year_id);
CREATE INDEX idx_entries_date ON journal_entries(tenant_id, date);
CREATE INDEX idx_entries_status ON journal_entries(tenant_id, status);

-- Lignes d'écritures
CREATE TABLE journal_entry_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    entry_id UUID NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    account_id UUID NOT NULL REFERENCES accounts(id),
    debit DECIMAL(15, 2) DEFAULT 0,
    credit DECIMAL(15, 2) DEFAULT 0,
    label TEXT,
    partner_id UUID,
    partner_type VARCHAR(50),
    analytic_account VARCHAR(50),
    analytic_tags JSONB DEFAULT '[]',
    reconcile_ref VARCHAR(50),
    reconciled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_entry_lines_entry ON journal_entry_lines(entry_id);
CREATE INDEX idx_entry_lines_account ON journal_entry_lines(account_id);
CREATE INDEX idx_entry_lines_tenant ON journal_entry_lines(tenant_id);
CREATE INDEX idx_entry_lines_partner ON journal_entry_lines(tenant_id, partner_id, partner_type);

-- ============================================================================
-- COMPTES BANCAIRES
-- ============================================================================

CREATE TABLE bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    bank_name VARCHAR(255),
    account_number VARCHAR(50),
    iban VARCHAR(50),
    bic VARCHAR(20),
    account_id UUID REFERENCES accounts(id),
    journal_id UUID REFERENCES journals(id),
    currency VARCHAR(3) DEFAULT 'EUR',
    initial_balance DECIMAL(15, 2) DEFAULT 0,
    current_balance DECIMAL(15, 2) DEFAULT 0,
    reconciled_balance DECIMAL(15, 2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bank_accounts_tenant ON bank_accounts(tenant_id);
CREATE INDEX idx_bank_accounts_active ON bank_accounts(tenant_id, is_active);

-- ============================================================================
-- RELEVÉS BANCAIRES
-- ============================================================================

CREATE TABLE bank_statements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    bank_account_id UUID NOT NULL REFERENCES bank_accounts(id),
    name VARCHAR(255) NOT NULL,
    reference VARCHAR(100),
    date DATE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    opening_balance DECIMAL(15, 2) NOT NULL,
    closing_balance DECIMAL(15, 2) NOT NULL,
    total_credits DECIMAL(15, 2) DEFAULT 0,
    total_debits DECIMAL(15, 2) DEFAULT 0,
    is_reconciled BOOLEAN DEFAULT FALSE,
    reconciled_at TIMESTAMP,
    reconciled_by UUID,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_statements_tenant ON bank_statements(tenant_id);
CREATE INDEX idx_statements_bank ON bank_statements(bank_account_id);
CREATE INDEX idx_statements_date ON bank_statements(tenant_id, date);

-- Lignes de relevé
CREATE TABLE bank_statement_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    statement_id UUID NOT NULL REFERENCES bank_statements(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    value_date DATE,
    label VARCHAR(500) NOT NULL,
    reference VARCHAR(100),
    amount DECIMAL(15, 2) NOT NULL,
    status reconciliation_status DEFAULT 'PENDING',
    matched_entry_line_id UUID REFERENCES journal_entry_lines(id),
    matched_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_statement_lines_statement ON bank_statement_lines(statement_id);
CREATE INDEX idx_statement_lines_tenant ON bank_statement_lines(tenant_id);
CREATE INDEX idx_statement_lines_status ON bank_statement_lines(tenant_id, status);

-- ============================================================================
-- TRANSACTIONS BANCAIRES
-- ============================================================================

CREATE TABLE bank_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    bank_account_id UUID NOT NULL REFERENCES bank_accounts(id),
    type bank_transaction_type NOT NULL,
    date DATE NOT NULL,
    value_date DATE,
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    label VARCHAR(500) NOT NULL,
    reference VARCHAR(100),
    partner_name VARCHAR(255),
    category VARCHAR(100),
    entry_line_id UUID REFERENCES journal_entry_lines(id),
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_tenant ON bank_transactions(tenant_id);
CREATE INDEX idx_transactions_bank ON bank_transactions(bank_account_id);
CREATE INDEX idx_transactions_date ON bank_transactions(tenant_id, date);
CREATE INDEX idx_transactions_type ON bank_transactions(tenant_id, type);

-- ============================================================================
-- TRÉSORERIE - PRÉVISIONS
-- ============================================================================

CREATE TABLE cash_forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    period forecast_period NOT NULL,
    date DATE NOT NULL,
    opening_balance DECIMAL(15, 2) NOT NULL,
    expected_receipts DECIMAL(15, 2) DEFAULT 0,
    expected_payments DECIMAL(15, 2) DEFAULT 0,
    expected_closing DECIMAL(15, 2) DEFAULT 0,
    actual_receipts DECIMAL(15, 2) DEFAULT 0,
    actual_payments DECIMAL(15, 2) DEFAULT 0,
    actual_closing DECIMAL(15, 2),
    details JSONB DEFAULT '{}',
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_forecasts_tenant ON cash_forecasts(tenant_id);
CREATE INDEX idx_forecasts_date ON cash_forecasts(tenant_id, date);
CREATE INDEX idx_forecasts_period ON cash_forecasts(tenant_id, period);

-- Catégories de flux de trésorerie
CREATE TABLE cash_flow_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_receipt BOOLEAN NOT NULL,
    parent_id UUID REFERENCES cash_flow_categories(id),
    "order" INTEGER DEFAULT 0,
    default_account_id UUID REFERENCES accounts(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_cashflow_code UNIQUE (tenant_id, code)
);

CREATE INDEX idx_cashflow_tenant ON cash_flow_categories(tenant_id);
CREATE INDEX idx_cashflow_type ON cash_flow_categories(tenant_id, is_receipt);

-- ============================================================================
-- RAPPORTS FINANCIERS
-- ============================================================================

CREATE TABLE financial_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    fiscal_year_id UUID REFERENCES fiscal_years(id),
    period_id UUID REFERENCES fiscal_periods(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    data JSONB NOT NULL DEFAULT '{}',
    parameters JSONB DEFAULT '{}',
    generated_by UUID,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pdf_url TEXT,
    excel_url TEXT
);

CREATE INDEX idx_reports_tenant ON financial_reports(tenant_id);
CREATE INDEX idx_reports_type ON financial_reports(tenant_id, report_type);
CREATE INDEX idx_reports_fiscal_year ON financial_reports(tenant_id, fiscal_year_id);
CREATE INDEX idx_reports_dates ON financial_reports(tenant_id, start_date, end_date);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger updated_at pour accounts
CREATE TRIGGER set_updated_at_accounts
    BEFORE UPDATE ON accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour journals
CREATE TRIGGER set_updated_at_journals
    BEFORE UPDATE ON journals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour fiscal_years
CREATE TRIGGER set_updated_at_fiscal_years
    BEFORE UPDATE ON fiscal_years
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour journal_entries
CREATE TRIGGER set_updated_at_journal_entries
    BEFORE UPDATE ON journal_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour bank_accounts
CREATE TRIGGER set_updated_at_bank_accounts
    BEFORE UPDATE ON bank_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour cash_forecasts
CREATE TRIGGER set_updated_at_cash_forecasts
    BEFORE UPDATE ON cash_forecasts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- DONNÉES INITIALES (Plan comptable français simplifié)
-- ============================================================================

-- Note: Les comptes seront créés par le service lors du premier setup du tenant

-- ============================================================================
-- FIN MIGRATION M2 - FINANCE
-- ============================================================================
