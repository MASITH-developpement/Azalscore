-- AZALS - ROLLBACK Migration Guardian Module
-- Annule la creation du systeme GUARDIAN de correction automatique gouvernee

DO $$
BEGIN
    -- Drop views first
    DROP VIEW IF EXISTS v_guardian_stats;
    DROP VIEW IF EXISTS v_guardian_pending_validations;
    DROP VIEW IF EXISTS v_guardian_pending_errors;

    -- Drop triggers
    DROP TRIGGER IF EXISTS trigger_guardian_config_updated ON guardian_config;
    DROP TRIGGER IF EXISTS trigger_guardian_rules_updated ON guardian_correction_rules;
    DROP TRIGGER IF EXISTS trigger_guardian_registry_protect ON guardian_correction_registry;

    -- Drop functions
    DROP FUNCTION IF EXISTS guardian_update_timestamp();
    DROP FUNCTION IF EXISTS guardian_registry_protect_immutable();

    -- Drop indexes for guardian_config
    DROP INDEX IF EXISTS idx_guardian_config_tenant;

    -- Drop indexes for guardian_alerts
    DROP INDEX IF EXISTS idx_guardian_alerts_unread;
    DROP INDEX IF EXISTS idx_guardian_alerts_tenant_created;
    DROP INDEX IF EXISTS idx_guardian_alerts_resolved;
    DROP INDEX IF EXISTS idx_guardian_alerts_read;
    DROP INDEX IF EXISTS idx_guardian_alerts_severity;
    DROP INDEX IF EXISTS idx_guardian_alerts_type;
    DROP INDEX IF EXISTS idx_guardian_alerts_tenant;
    DROP INDEX IF EXISTS idx_guardian_alerts_uid;

    -- Drop indexes for guardian_correction_tests
    DROP INDEX IF EXISTS idx_guardian_tests_result;
    DROP INDEX IF EXISTS idx_guardian_tests_correction;
    DROP INDEX IF EXISTS idx_guardian_tests_tenant;

    -- Drop indexes for guardian_correction_rules
    DROP INDEX IF EXISTS idx_guardian_rules_trigger;
    DROP INDEX IF EXISTS idx_guardian_rules_active;
    DROP INDEX IF EXISTS idx_guardian_rules_tenant;
    DROP INDEX IF EXISTS idx_guardian_rules_uid;

    -- Drop foreign key from error_detections
    ALTER TABLE IF EXISTS guardian_error_detections
        DROP CONSTRAINT IF EXISTS fk_guardian_error_correction;

    -- Drop indexes for guardian_correction_registry
    DROP INDEX IF EXISTS idx_guardian_registry_requires_validation;
    DROP INDEX IF EXISTS idx_guardian_registry_severity_module;
    DROP INDEX IF EXISTS idx_guardian_registry_env_status;
    DROP INDEX IF EXISTS idx_guardian_registry_tenant_created;
    DROP INDEX IF EXISTS idx_guardian_registry_module;
    DROP INDEX IF EXISTS idx_guardian_registry_severity;
    DROP INDEX IF EXISTS idx_guardian_registry_status;
    DROP INDEX IF EXISTS idx_guardian_registry_env;
    DROP INDEX IF EXISTS idx_guardian_registry_created;
    DROP INDEX IF EXISTS idx_guardian_registry_tenant;
    DROP INDEX IF EXISTS idx_guardian_registry_uid;

    -- Drop indexes for guardian_error_detections
    DROP INDEX IF EXISTS idx_guardian_errors_request;
    DROP INDEX IF EXISTS idx_guardian_errors_correlation;
    DROP INDEX IF EXISTS idx_guardian_errors_error_code;
    DROP INDEX IF EXISTS idx_guardian_errors_module_type;
    DROP INDEX IF EXISTS idx_guardian_errors_severity_env;
    DROP INDEX IF EXISTS idx_guardian_errors_tenant_detected;
    DROP INDEX IF EXISTS idx_guardian_errors_processed;
    DROP INDEX IF EXISTS idx_guardian_errors_module;
    DROP INDEX IF EXISTS idx_guardian_errors_env;
    DROP INDEX IF EXISTS idx_guardian_errors_type;
    DROP INDEX IF EXISTS idx_guardian_errors_source;
    DROP INDEX IF EXISTS idx_guardian_errors_severity;
    DROP INDEX IF EXISTS idx_guardian_errors_tenant;
    DROP INDEX IF EXISTS idx_guardian_errors_uid;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS guardian_config CASCADE;
    DROP TABLE IF EXISTS guardian_alerts CASCADE;
    DROP TABLE IF EXISTS guardian_correction_tests CASCADE;
    DROP TABLE IF EXISTS guardian_correction_rules CASCADE;
    DROP TABLE IF EXISTS guardian_correction_registry CASCADE;
    DROP TABLE IF EXISTS guardian_error_detections CASCADE;

    -- Drop ENUM types (after tables that use them)
    DROP TYPE IF EXISTS guardian_environment;
    DROP TYPE IF EXISTS guardian_test_result;
    DROP TYPE IF EXISTS guardian_correction_action;
    DROP TYPE IF EXISTS guardian_correction_status;
    DROP TYPE IF EXISTS guardian_error_type;
    DROP TYPE IF EXISTS guardian_error_source;
    DROP TYPE IF EXISTS guardian_error_severity;

    RAISE NOTICE 'Migration 028_guardian_module rolled back successfully';
END $$;
