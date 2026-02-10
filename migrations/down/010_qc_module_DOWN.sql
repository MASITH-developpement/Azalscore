-- AZALS - ROLLBACK Migration QC MODULE
-- Annule la creation du systeme de controle qualite central

DO $$
BEGIN
    -- Drop views first
    DROP VIEW IF EXISTS v_qc_module_summary;
    DROP VIEW IF EXISTS v_qc_critical_alerts;
    DROP VIEW IF EXISTS v_qc_modules_pending;

    -- Drop triggers
    DROP TRIGGER IF EXISTS trigger_update_qc_rules ON qc_rules;
    DROP TRIGGER IF EXISTS trigger_update_qc_module_registry ON qc_module_registry;
    DROP TRIGGER IF EXISTS trigger_update_qc_dashboards ON qc_dashboards;
    DROP TRIGGER IF EXISTS trigger_update_qc_templates ON qc_templates;

    -- Drop function
    DROP FUNCTION IF EXISTS update_qc_updated_at();

    -- Drop indexes for qc_templates
    DROP INDEX IF EXISTS idx_qc_templates_tenant;
    DROP INDEX IF EXISTS idx_qc_templates_category;

    -- Drop indexes for qc_dashboards
    DROP INDEX IF EXISTS idx_qc_dashboards_tenant;
    DROP INDEX IF EXISTS idx_qc_dashboards_owner;

    -- Drop indexes for qc_alerts
    DROP INDEX IF EXISTS idx_qc_alerts_tenant;
    DROP INDEX IF EXISTS idx_qc_alerts_unresolved;
    DROP INDEX IF EXISTS idx_qc_alerts_severity;
    DROP INDEX IF EXISTS idx_qc_alerts_module;

    -- Drop indexes for qc_metrics
    DROP INDEX IF EXISTS idx_qc_metrics_tenant;
    DROP INDEX IF EXISTS idx_qc_metrics_date;
    DROP INDEX IF EXISTS idx_qc_metrics_module;

    -- Drop indexes for qc_test_runs
    DROP INDEX IF EXISTS idx_test_runs_tenant;
    DROP INDEX IF EXISTS idx_test_runs_module;
    DROP INDEX IF EXISTS idx_test_runs_type;
    DROP INDEX IF EXISTS idx_test_runs_started;

    -- Drop indexes for qc_check_results
    DROP INDEX IF EXISTS idx_check_results_tenant;
    DROP INDEX IF EXISTS idx_check_results_validation;
    DROP INDEX IF EXISTS idx_check_results_status;
    DROP INDEX IF EXISTS idx_check_results_category;

    -- Drop indexes for qc_validations
    DROP INDEX IF EXISTS idx_validations_tenant;
    DROP INDEX IF EXISTS idx_validations_module;
    DROP INDEX IF EXISTS idx_validations_status;
    DROP INDEX IF EXISTS idx_validations_started;

    -- Drop indexes for qc_module_registry
    DROP INDEX IF EXISTS idx_module_registry_tenant;
    DROP INDEX IF EXISTS idx_module_registry_status;
    DROP INDEX IF EXISTS idx_module_registry_type;

    -- Drop indexes for qc_rules
    DROP INDEX IF EXISTS idx_qc_rules_tenant;
    DROP INDEX IF EXISTS idx_qc_rules_category;
    DROP INDEX IF EXISTS idx_qc_rules_active;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS qc_templates CASCADE;
    DROP TABLE IF EXISTS qc_dashboards CASCADE;
    DROP TABLE IF EXISTS qc_alerts CASCADE;
    DROP TABLE IF EXISTS qc_metrics CASCADE;
    DROP TABLE IF EXISTS qc_test_runs CASCADE;
    DROP TABLE IF EXISTS qc_check_results CASCADE;
    DROP TABLE IF EXISTS qc_validations CASCADE;
    DROP TABLE IF EXISTS qc_module_registry CASCADE;
    DROP TABLE IF EXISTS qc_rules CASCADE;

    -- Drop ENUM types
    DROP TYPE IF EXISTS validation_phase;
    DROP TYPE IF EXISTS test_type;
    DROP TYPE IF EXISTS module_status;
    DROP TYPE IF EXISTS qc_check_status;
    DROP TYPE IF EXISTS qc_rule_severity;
    DROP TYPE IF EXISTS qc_rule_category;

    RAISE NOTICE 'Migration 010_qc_module rolled back successfully';
END $$;
