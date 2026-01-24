-- AZALS - ROLLBACK Migration Beta Tenant Fields
-- Annule l'ajout des champs pour la gestion des tenants beta

DO $$
BEGIN
    -- ============================================================================
    -- Drop composite indexes first
    -- ============================================================================
    DROP INDEX IF EXISTS idx_users_tenant_must_change;
    DROP INDEX IF EXISTS idx_tenants_environment_status;

    -- ============================================================================
    -- Drop columns from users table
    -- ============================================================================
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'users' AND column_name = 'password_changed_at') THEN
        ALTER TABLE users DROP COLUMN password_changed_at;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'users' AND column_name = 'must_change_password') THEN
        -- Drop constraint first
        ALTER TABLE users DROP CONSTRAINT IF EXISTS users_must_change_password_bool;
        -- Drop index
        DROP INDEX IF EXISTS idx_users_must_change_password;
        -- Drop column
        ALTER TABLE users DROP COLUMN must_change_password;
    END IF;

    -- ============================================================================
    -- Drop columns from tenants table
    -- ============================================================================
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'tenants' AND column_name = 'environment') THEN
        -- Drop constraint first
        ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_environment_valid;
        -- Drop index
        DROP INDEX IF EXISTS idx_tenants_environment;
        -- Drop column
        ALTER TABLE tenants DROP COLUMN environment;
    END IF;

    RAISE NOTICE 'Migration 033_beta_tenant_fields rolled back successfully';
END $$;
