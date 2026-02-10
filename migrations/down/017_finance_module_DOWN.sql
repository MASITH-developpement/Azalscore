-- AZALS - ROLLBACK Migration FINANCE MODULE
-- Annule la creation du module finance comptabilite+tresorerie (M2)

DO $$
BEGIN
    -- Drop triggers
    DROP TRIGGER IF EXISTS set_updated_at_accounts ON accounts;
    DROP TRIGGER IF EXISTS set_updated_at_journals ON journals;
    DROP TRIGGER IF EXISTS set_updated_at_fiscal_years ON fiscal_years;
    DROP TRIGGER IF EXISTS set_updated_at_journal_entries ON journal_entries;
    DROP TRIGGER IF EXISTS set_updated_at_bank_accounts ON bank_accounts;
    DROP TRIGGER IF EXISTS set_updated_at_cash_forecasts ON cash_forecasts;

    -- Drop indexes for financial_reports
    DROP INDEX IF EXISTS idx_reports_tenant;
    DROP INDEX IF EXISTS idx_reports_type;
    DROP INDEX IF EXISTS idx_reports_fiscal_year;
    DROP INDEX IF EXISTS idx_reports_dates;

    -- Drop indexes for cash_flow_categories
    DROP INDEX IF EXISTS idx_cashflow_tenant;
    DROP INDEX IF EXISTS idx_cashflow_type;

    -- Drop indexes for cash_forecasts
    DROP INDEX IF EXISTS idx_forecasts_tenant;
    DROP INDEX IF EXISTS idx_forecasts_date;
    DROP INDEX IF EXISTS idx_forecasts_period;

    -- Drop indexes for bank_transactions
    DROP INDEX IF EXISTS idx_transactions_tenant;
    DROP INDEX IF EXISTS idx_transactions_bank;
    DROP INDEX IF EXISTS idx_transactions_date;
    DROP INDEX IF EXISTS idx_transactions_type;

    -- Drop indexes for bank_statement_lines
    DROP INDEX IF EXISTS idx_statement_lines_statement;
    DROP INDEX IF EXISTS idx_statement_lines_tenant;
    DROP INDEX IF EXISTS idx_statement_lines_status;

    -- Drop indexes for bank_statements
    DROP INDEX IF EXISTS idx_statements_tenant;
    DROP INDEX IF EXISTS idx_statements_bank;
    DROP INDEX IF EXISTS idx_statements_date;

    -- Drop indexes for bank_accounts
    DROP INDEX IF EXISTS idx_bank_accounts_tenant;
    DROP INDEX IF EXISTS idx_bank_accounts_active;

    -- Drop indexes for journal_entry_lines
    DROP INDEX IF EXISTS idx_entry_lines_entry;
    DROP INDEX IF EXISTS idx_entry_lines_account;
    DROP INDEX IF EXISTS idx_entry_lines_tenant;
    DROP INDEX IF EXISTS idx_entry_lines_partner;

    -- Drop indexes for journal_entries
    DROP INDEX IF EXISTS idx_entries_tenant;
    DROP INDEX IF EXISTS idx_entries_journal;
    DROP INDEX IF EXISTS idx_entries_fiscal_year;
    DROP INDEX IF EXISTS idx_entries_date;
    DROP INDEX IF EXISTS idx_entries_status;

    -- Drop indexes for fiscal_periods
    DROP INDEX IF EXISTS idx_fiscal_periods_year;
    DROP INDEX IF EXISTS idx_fiscal_periods_tenant;

    -- Drop indexes for fiscal_years
    DROP INDEX IF EXISTS idx_fiscal_years_tenant;
    DROP INDEX IF EXISTS idx_fiscal_years_dates;
    DROP INDEX IF EXISTS idx_fiscal_years_status;

    -- Drop indexes for journals
    DROP INDEX IF EXISTS idx_journals_tenant;
    DROP INDEX IF EXISTS idx_journals_type;

    -- Drop indexes for accounts
    DROP INDEX IF EXISTS idx_accounts_tenant;
    DROP INDEX IF EXISTS idx_accounts_type;
    DROP INDEX IF EXISTS idx_accounts_parent;
    DROP INDEX IF EXISTS idx_accounts_code;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS financial_reports CASCADE;
    DROP TABLE IF EXISTS cash_flow_categories CASCADE;
    DROP TABLE IF EXISTS cash_forecasts CASCADE;
    DROP TABLE IF EXISTS bank_transactions CASCADE;
    DROP TABLE IF EXISTS bank_statement_lines CASCADE;
    DROP TABLE IF EXISTS bank_statements CASCADE;
    DROP TABLE IF EXISTS bank_accounts CASCADE;
    DROP TABLE IF EXISTS journal_entry_lines CASCADE;
    DROP TABLE IF EXISTS journal_entries CASCADE;
    DROP TABLE IF EXISTS fiscal_periods CASCADE;
    DROP TABLE IF EXISTS fiscal_years CASCADE;
    DROP TABLE IF EXISTS journals CASCADE;
    DROP TABLE IF EXISTS accounts CASCADE;

    -- Drop ENUM types
    DROP TYPE IF EXISTS forecast_period;
    DROP TYPE IF EXISTS reconciliation_status;
    DROP TYPE IF EXISTS bank_transaction_type;
    DROP TYPE IF EXISTS fiscal_year_status;
    DROP TYPE IF EXISTS entry_status;
    DROP TYPE IF EXISTS journal_type;
    DROP TYPE IF EXISTS account_type;

    RAISE NOTICE 'Migration 017_finance_module rolled back successfully';
END $$;
