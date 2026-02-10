-- AZALS - ROLLBACK Migration M2A - Comptabilite Automatisee
-- Annule la creation des tables pour l'automatisation comptable

DO $$
BEGIN
    -- Drop triggers first
    DROP TRIGGER IF EXISTS tr_accounting_user_preferences_updated ON accounting_user_preferences;
    DROP TRIGGER IF EXISTS tr_accounting_reconciliation_rules_updated ON accounting_reconciliation_rules;
    DROP TRIGGER IF EXISTS tr_accounting_synced_transactions_updated ON accounting_synced_transactions;
    DROP TRIGGER IF EXISTS tr_accounting_synced_accounts_updated ON accounting_synced_bank_accounts;
    DROP TRIGGER IF EXISTS tr_accounting_bank_connections_updated ON accounting_bank_connections;
    DROP TRIGGER IF EXISTS tr_accounting_documents_updated ON accounting_documents;

    -- Drop function
    DROP FUNCTION IF EXISTS update_accounting_updated_at();

    -- ============================================================================
    -- Drop indexes for accounting_dashboard_metrics
    -- ============================================================================
    DROP INDEX IF EXISTS idx_dashboard_metrics_date;
    DROP INDEX IF EXISTS idx_dashboard_metrics_tenant;

    -- ============================================================================
    -- Drop indexes for accounting_email_processing_logs
    -- ============================================================================
    DROP INDEX IF EXISTS idx_email_logs_status;
    DROP INDEX IF EXISTS idx_email_logs_inbox;
    DROP INDEX IF EXISTS idx_email_logs_tenant;

    -- ============================================================================
    -- Drop indexes for accounting_email_inboxes
    -- ============================================================================
    DROP INDEX IF EXISTS idx_email_inbox_tenant;
    DROP INDEX IF EXISTS idx_email_inbox_address;

    -- ============================================================================
    -- Drop indexes for accounting_bank_sync_sessions
    -- ============================================================================
    DROP INDEX IF EXISTS idx_bank_sync_status;
    DROP INDEX IF EXISTS idx_bank_sync_connection;
    DROP INDEX IF EXISTS idx_bank_sync_tenant;

    -- ============================================================================
    -- Drop indexes for accounting_user_preferences
    -- ============================================================================
    DROP INDEX IF EXISTS idx_user_prefs_tenant_user_view;

    -- ============================================================================
    -- Drop indexes for accounting_tax_configurations
    -- ============================================================================
    DROP INDEX IF EXISTS idx_tax_config_country;
    DROP INDEX IF EXISTS idx_tax_config_tenant;

    -- ============================================================================
    -- Drop indexes for accounting_chart_mappings
    -- ============================================================================
    DROP INDEX IF EXISTS idx_chart_mappings_tenant_universal;
    DROP INDEX IF EXISTS idx_chart_mappings_tenant;

    -- ============================================================================
    -- Drop indexes for accounting_universal_chart
    -- ============================================================================
    DROP INDEX IF EXISTS idx_universal_chart_type;
    DROP INDEX IF EXISTS idx_universal_chart_parent;
    DROP INDEX IF EXISTS idx_universal_chart_code;

    -- ============================================================================
    -- Drop indexes for accounting_alerts
    -- ============================================================================
    DROP INDEX IF EXISTS idx_alerts_entity;
    DROP INDEX IF EXISTS idx_alerts_tenant_unresolved;
    DROP INDEX IF EXISTS idx_alerts_tenant_type;
    DROP INDEX IF EXISTS idx_alerts_tenant;

    -- ============================================================================
    -- Drop indexes for accounting_reconciliation_history
    -- ============================================================================
    DROP INDEX IF EXISTS idx_recon_history_document;
    DROP INDEX IF EXISTS idx_recon_history_transaction;
    DROP INDEX IF EXISTS idx_recon_history_tenant;

    -- ============================================================================
    -- Drop indexes for accounting_reconciliation_rules
    -- ============================================================================
    DROP INDEX IF EXISTS idx_recon_rules_tenant_active;
    DROP INDEX IF EXISTS idx_recon_rules_tenant;

    -- ============================================================================
    -- Drop indexes for accounting_synced_transactions
    -- ============================================================================
    DROP INDEX IF EXISTS idx_synced_trans_external;
    DROP INDEX IF EXISTS idx_synced_trans_reconciliation;
    DROP INDEX IF EXISTS idx_synced_trans_date;
    DROP INDEX IF EXISTS idx_synced_trans_account;
    DROP INDEX IF EXISTS idx_synced_trans_tenant;

    -- ============================================================================
    -- Drop indexes for accounting_synced_bank_accounts
    -- ============================================================================
    DROP INDEX IF EXISTS idx_synced_accounts_external;
    DROP INDEX IF EXISTS idx_synced_accounts_connection;
    DROP INDEX IF EXISTS idx_synced_accounts_tenant;

    -- ============================================================================
    -- Drop indexes for accounting_bank_connections
    -- ============================================================================
    DROP INDEX IF EXISTS idx_bank_conn_tenant_connection;
    DROP INDEX IF EXISTS idx_bank_conn_tenant_status;
    DROP INDEX IF EXISTS idx_bank_conn_tenant;

    -- ============================================================================
    -- Drop indexes for accounting_auto_entries
    -- ============================================================================
    DROP INDEX IF EXISTS idx_auto_entries_tenant_review;
    DROP INDEX IF EXISTS idx_auto_entries_tenant_confidence;
    DROP INDEX IF EXISTS idx_auto_entries_tenant_doc;

    -- ============================================================================
    -- Drop indexes for accounting_ai_classifications
    -- ============================================================================
    DROP INDEX IF EXISTS idx_ai_class_tenant_confidence;
    DROP INDEX IF EXISTS idx_ai_class_tenant_doc;

    -- ============================================================================
    -- Drop indexes for accounting_ocr_results
    -- ============================================================================
    DROP INDEX IF EXISTS idx_ocr_results_tenant_doc;

    -- ============================================================================
    -- Drop indexes for accounting_documents
    -- ============================================================================
    DROP INDEX IF EXISTS idx_accounting_docs_reference;
    DROP INDEX IF EXISTS idx_accounting_docs_file_hash;
    DROP INDEX IF EXISTS idx_accounting_docs_tenant_payment;
    DROP INDEX IF EXISTS idx_accounting_docs_tenant_partner;
    DROP INDEX IF EXISTS idx_accounting_docs_tenant_date;
    DROP INDEX IF EXISTS idx_accounting_docs_tenant_type;
    DROP INDEX IF EXISTS idx_accounting_docs_tenant_status;
    DROP INDEX IF EXISTS idx_accounting_docs_tenant;

    -- ============================================================================
    -- Drop tables in reverse order of dependencies
    -- ============================================================================
    DROP TABLE IF EXISTS accounting_dashboard_metrics CASCADE;
    DROP TABLE IF EXISTS accounting_email_processing_logs CASCADE;
    DROP TABLE IF EXISTS accounting_email_inboxes CASCADE;
    DROP TABLE IF EXISTS accounting_bank_sync_sessions CASCADE;
    DROP TABLE IF EXISTS accounting_user_preferences CASCADE;
    DROP TABLE IF EXISTS accounting_tax_configurations CASCADE;
    DROP TABLE IF EXISTS accounting_chart_mappings CASCADE;
    DROP TABLE IF EXISTS accounting_universal_chart CASCADE;
    DROP TABLE IF EXISTS accounting_alerts CASCADE;
    DROP TABLE IF EXISTS accounting_reconciliation_history CASCADE;
    DROP TABLE IF EXISTS accounting_reconciliation_rules CASCADE;
    DROP TABLE IF EXISTS accounting_synced_transactions CASCADE;
    DROP TABLE IF EXISTS accounting_synced_bank_accounts CASCADE;
    DROP TABLE IF EXISTS accounting_bank_connections CASCADE;
    DROP TABLE IF EXISTS accounting_auto_entries CASCADE;
    DROP TABLE IF EXISTS accounting_ai_classifications CASCADE;
    DROP TABLE IF EXISTS accounting_ocr_results CASCADE;
    DROP TABLE IF EXISTS accounting_documents CASCADE;

    -- ============================================================================
    -- Drop ENUM types (after tables that use them)
    -- ============================================================================
    DROP TYPE IF EXISTS alert_type;
    DROP TYPE IF EXISTS payment_status;
    DROP TYPE IF EXISTS bank_connection_status;
    DROP TYPE IF EXISTS confidence_level;
    DROP TYPE IF EXISTS document_source;
    DROP TYPE IF EXISTS document_status;
    DROP TYPE IF EXISTS document_type;

    RAISE NOTICE 'Migration 031_automated_accounting_module rolled back successfully';
END $$;
