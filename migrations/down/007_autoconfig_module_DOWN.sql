-- AZALS - ROLLBACK Migration AUTOCONFIG MODULE
-- Annule la creation des tables de configuration automatique par fonction

DO $$
BEGIN
    -- Drop triggers first
    DROP TRIGGER IF EXISTS update_job_profiles_updated_at ON autoconfig_job_profiles;
    DROP TRIGGER IF EXISTS update_autoconfig_rules_updated_at ON autoconfig_rules;

    -- Drop indexes for autoconfig_logs
    DROP INDEX IF EXISTS idx_autoconfig_logs_tenant;
    DROP INDEX IF EXISTS idx_autoconfig_logs_action;
    DROP INDEX IF EXISTS idx_autoconfig_logs_user;
    DROP INDEX IF EXISTS idx_autoconfig_logs_created;

    -- Drop indexes for autoconfig_rules
    DROP INDEX IF EXISTS idx_autoconfig_rules_tenant;
    DROP INDEX IF EXISTS idx_autoconfig_rules_priority;

    -- Drop indexes for autoconfig_offboarding
    DROP INDEX IF EXISTS idx_offboarding_tenant;
    DROP INDEX IF EXISTS idx_offboarding_status;
    DROP INDEX IF EXISTS idx_offboarding_departure;

    -- Drop indexes for autoconfig_onboarding
    DROP INDEX IF EXISTS idx_onboarding_tenant;
    DROP INDEX IF EXISTS idx_onboarding_status;
    DROP INDEX IF EXISTS idx_onboarding_start;

    -- Drop indexes for autoconfig_permission_overrides
    DROP INDEX IF EXISTS idx_overrides_tenant;
    DROP INDEX IF EXISTS idx_overrides_user;
    DROP INDEX IF EXISTS idx_overrides_status;
    DROP INDEX IF EXISTS idx_overrides_expires;

    -- Drop indexes for autoconfig_profile_assignments
    DROP INDEX IF EXISTS idx_profile_assignments_tenant;
    DROP INDEX IF EXISTS idx_profile_assignments_user;
    DROP INDEX IF EXISTS idx_profile_assignments_active;

    -- Drop indexes for autoconfig_job_profiles
    DROP INDEX IF EXISTS idx_job_profiles_tenant;
    DROP INDEX IF EXISTS idx_job_profiles_level;
    DROP INDEX IF EXISTS idx_job_profiles_priority;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS autoconfig_logs CASCADE;
    DROP TABLE IF EXISTS autoconfig_rules CASCADE;
    DROP TABLE IF EXISTS autoconfig_offboarding CASCADE;
    DROP TABLE IF EXISTS autoconfig_onboarding CASCADE;
    DROP TABLE IF EXISTS autoconfig_permission_overrides CASCADE;
    DROP TABLE IF EXISTS autoconfig_profile_assignments CASCADE;
    DROP TABLE IF EXISTS autoconfig_job_profiles CASCADE;

    RAISE NOTICE 'Migration 007_autoconfig_module rolled back successfully';
END $$;
