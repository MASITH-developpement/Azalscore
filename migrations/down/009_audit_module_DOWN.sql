-- AZALS - ROLLBACK Migration AUDIT MODULE
-- Annule la creation du systeme d'audit centralise et benchmarks

DO $$
BEGIN
    -- Drop views first
    DROP VIEW IF EXISTS v_active_sessions;
    DROP VIEW IF EXISTS v_audit_stats;

    -- Drop triggers
    DROP TRIGGER IF EXISTS trigger_update_audit_benchmarks ON audit_benchmarks;
    DROP TRIGGER IF EXISTS trigger_update_audit_compliance ON audit_compliance_checks;
    DROP TRIGGER IF EXISTS trigger_update_audit_retention ON audit_retention_rules;
    DROP TRIGGER IF EXISTS trigger_update_audit_dashboards ON audit_dashboards;

    -- Drop function
    DROP FUNCTION IF EXISTS update_audit_updated_at();

    -- Drop indexes for audit_dashboards
    DROP INDEX IF EXISTS idx_dashboards_tenant;
    DROP INDEX IF EXISTS idx_dashboards_owner;

    -- Drop indexes for audit_exports
    DROP INDEX IF EXISTS idx_exports_tenant;
    DROP INDEX IF EXISTS idx_exports_status;
    DROP INDEX IF EXISTS idx_exports_requested;

    -- Drop indexes for audit_retention_rules
    DROP INDEX IF EXISTS idx_retention_tenant;
    DROP INDEX IF EXISTS idx_retention_table;

    -- Drop indexes for audit_compliance_checks
    DROP INDEX IF EXISTS idx_compliance_tenant;
    DROP INDEX IF EXISTS idx_compliance_framework;
    DROP INDEX IF EXISTS idx_compliance_status;

    -- Drop indexes for audit_benchmark_results
    DROP INDEX IF EXISTS idx_results_tenant;
    DROP INDEX IF EXISTS idx_results_benchmark;
    DROP INDEX IF EXISTS idx_results_started;

    -- Drop indexes for audit_benchmarks
    DROP INDEX IF EXISTS idx_benchmarks_tenant;
    DROP INDEX IF EXISTS idx_benchmarks_type;

    -- Drop indexes for audit_metric_values
    DROP INDEX IF EXISTS idx_metric_values_tenant;
    DROP INDEX IF EXISTS idx_metric_values_metric;
    DROP INDEX IF EXISTS idx_metric_values_code;
    DROP INDEX IF EXISTS idx_metric_values_period;

    -- Drop indexes for audit_metric_definitions
    DROP INDEX IF EXISTS idx_metrics_tenant;

    -- Drop indexes for audit_sessions
    DROP INDEX IF EXISTS idx_sessions_tenant;
    DROP INDEX IF EXISTS idx_sessions_user;
    DROP INDEX IF EXISTS idx_sessions_active;
    DROP INDEX IF EXISTS idx_sessions_session;

    -- Drop indexes for audit_logs
    DROP INDEX IF EXISTS idx_audit_tenant;
    DROP INDEX IF EXISTS idx_audit_tenant_created;
    DROP INDEX IF EXISTS idx_audit_module_action;
    DROP INDEX IF EXISTS idx_audit_entity;
    DROP INDEX IF EXISTS idx_audit_user;
    DROP INDEX IF EXISTS idx_audit_level;
    DROP INDEX IF EXISTS idx_audit_category;
    DROP INDEX IF EXISTS idx_audit_retention;
    DROP INDEX IF EXISTS idx_audit_request;
    DROP INDEX IF EXISTS idx_audit_created;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS audit_dashboards CASCADE;
    DROP TABLE IF EXISTS audit_exports CASCADE;
    DROP TABLE IF EXISTS audit_retention_rules CASCADE;
    DROP TABLE IF EXISTS audit_compliance_checks CASCADE;
    DROP TABLE IF EXISTS audit_benchmark_results CASCADE;
    DROP TABLE IF EXISTS audit_benchmarks CASCADE;
    DROP TABLE IF EXISTS audit_metric_values CASCADE;
    DROP TABLE IF EXISTS audit_metric_definitions CASCADE;
    DROP TABLE IF EXISTS audit_sessions CASCADE;
    DROP TABLE IF EXISTS audit_logs CASCADE;

    -- Drop ENUM types
    DROP TYPE IF EXISTS compliance_framework;
    DROP TYPE IF EXISTS retention_policy;
    DROP TYPE IF EXISTS benchmark_status;
    DROP TYPE IF EXISTS metric_type;
    DROP TYPE IF EXISTS audit_category;
    DROP TYPE IF EXISTS audit_level;
    DROP TYPE IF EXISTS audit_action;

    RAISE NOTICE 'Migration 009_audit_module rolled back successfully';
END $$;
