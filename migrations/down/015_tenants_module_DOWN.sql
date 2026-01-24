-- AZALS - ROLLBACK Migration TENANTS MODULE
-- Annule la creation du module de gestion des tenants (T9)

DO $$
BEGIN
    -- Drop triggers
    DROP TRIGGER IF EXISTS update_tenants_updated_at ON tenants;
    DROP TRIGGER IF EXISTS update_tenant_subscriptions_updated_at ON tenant_subscriptions;
    DROP TRIGGER IF EXISTS update_tenant_modules_updated_at ON tenant_modules;
    DROP TRIGGER IF EXISTS update_tenant_settings_updated_at ON tenant_settings;
    DROP TRIGGER IF EXISTS update_tenant_onboarding_updated_at ON tenant_onboarding;

    -- Drop indexes for tenant_onboarding
    DROP INDEX IF EXISTS idx_tenant_onboarding_tenant;

    -- Drop indexes for tenant_settings
    DROP INDEX IF EXISTS idx_tenant_settings_tenant;

    -- Drop indexes for tenant_events
    DROP INDEX IF EXISTS idx_tenant_events_tenant;
    DROP INDEX IF EXISTS idx_tenant_events_type;
    DROP INDEX IF EXISTS idx_tenant_events_created;

    -- Drop indexes for tenant_usage
    DROP INDEX IF EXISTS idx_tenant_usage_tenant;
    DROP INDEX IF EXISTS idx_tenant_usage_date;
    DROP INDEX IF EXISTS idx_tenant_usage_period;

    -- Drop indexes for tenant_invitations
    DROP INDEX IF EXISTS idx_tenant_invitations_token;
    DROP INDEX IF EXISTS idx_tenant_invitations_email;
    DROP INDEX IF EXISTS idx_tenant_invitations_status;

    -- Drop indexes for tenant_modules
    DROP INDEX IF EXISTS idx_tenant_modules_tenant;
    DROP INDEX IF EXISTS idx_tenant_modules_code;
    DROP INDEX IF EXISTS idx_tenant_modules_status;

    -- Drop indexes for tenant_subscriptions
    DROP INDEX IF EXISTS idx_tenant_subscriptions_tenant;
    DROP INDEX IF EXISTS idx_tenant_subscriptions_active;

    -- Drop indexes for tenants
    DROP INDEX IF EXISTS idx_tenants_id;
    DROP INDEX IF EXISTS idx_tenants_status;
    DROP INDEX IF EXISTS idx_tenants_plan;
    DROP INDEX IF EXISTS idx_tenants_country;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS tenant_onboarding CASCADE;
    DROP TABLE IF EXISTS tenant_settings CASCADE;
    DROP TABLE IF EXISTS tenant_events CASCADE;
    DROP TABLE IF EXISTS tenant_usage CASCADE;
    DROP TABLE IF EXISTS tenant_invitations CASCADE;
    DROP TABLE IF EXISTS tenant_modules CASCADE;
    DROP TABLE IF EXISTS tenant_subscriptions CASCADE;
    DROP TABLE IF EXISTS tenants CASCADE;

    -- Drop ENUM types
    DROP TYPE IF EXISTS invitation_status;
    DROP TYPE IF EXISTS module_status;
    DROP TYPE IF EXISTS billing_cycle;
    DROP TYPE IF EXISTS subscription_plan;
    DROP TYPE IF EXISTS tenant_status;

    RAISE NOTICE 'Migration 015_tenants_module rolled back successfully';
END $$;
