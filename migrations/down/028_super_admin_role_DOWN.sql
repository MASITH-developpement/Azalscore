-- AZALS - ROLLBACK Migration Super Admin Role
-- Annule la creation du role super_admin et des protections systeme

DO $$
BEGIN
    -- Drop triggers first
    DROP TRIGGER IF EXISTS check_super_admin_assignment_trigger ON iam_user_roles;
    DROP TRIGGER IF EXISTS protect_system_users_trigger ON iam_users;
    DROP TRIGGER IF EXISTS protect_system_roles_trigger ON iam_roles;
    DROP TRIGGER IF EXISTS prevent_system_init_update ON iam_system_init_log;

    -- Drop functions
    DROP FUNCTION IF EXISTS check_super_admin_assignment();
    DROP FUNCTION IF EXISTS protect_system_users();
    DROP FUNCTION IF EXISTS protect_system_roles();
    DROP FUNCTION IF EXISTS prevent_system_init_modification();

    -- Drop indexes for iam_system_init_log
    DROP INDEX IF EXISTS idx_system_init_created;
    DROP INDEX IF EXISTS idx_system_init_operation;
    DROP INDEX IF EXISTS idx_system_init_tenant;

    -- Drop columns added to iam_users
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'iam_users' AND column_name = 'created_via') THEN
        ALTER TABLE iam_users DROP COLUMN created_via;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'iam_users' AND column_name = 'is_protected') THEN
        ALTER TABLE iam_users DROP COLUMN is_protected;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'iam_users' AND column_name = 'is_system_account') THEN
        ALTER TABLE iam_users DROP COLUMN is_system_account;
    END IF;

    -- Drop columns added to iam_roles
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'iam_roles' AND column_name = 'max_assignments') THEN
        ALTER TABLE iam_roles DROP COLUMN max_assignments;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'iam_roles' AND column_name = 'is_deletable') THEN
        ALTER TABLE iam_roles DROP COLUMN is_deletable;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'iam_roles' AND column_name = 'is_protected') THEN
        ALTER TABLE iam_roles DROP COLUMN is_protected;
    END IF;

    -- Drop table
    DROP TABLE IF EXISTS iam_system_init_log CASCADE;

    RAISE NOTICE 'Migration 028_super_admin_role rolled back successfully';
END $$;
