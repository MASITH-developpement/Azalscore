-- AZALS - ROLLBACK Migration IAM MODULE
-- Annule la creation des tables de gestion des identites et acces (IAM)

DO $$
BEGIN
    -- Drop triggers first
    DROP TRIGGER IF EXISTS update_iam_users_updated_at ON iam_users;
    DROP TRIGGER IF EXISTS update_iam_roles_updated_at ON iam_roles;
    DROP TRIGGER IF EXISTS update_iam_groups_updated_at ON iam_groups;

    -- Drop functions (only if not used by other tables)
    -- Note: update_updated_at_column may be used elsewhere, drop only if safe
    DROP FUNCTION IF EXISTS cleanup_expired_tokens();
    -- DROP FUNCTION IF EXISTS update_updated_at_column(); -- Potentially shared

    -- Drop indexes for iam_rate_limits
    DROP INDEX IF EXISTS idx_rate_limit_key;
    DROP INDEX IF EXISTS idx_rate_limit_blocked;

    -- Drop indexes for iam_audit_logs
    DROP INDEX IF EXISTS idx_iam_audit_tenant;
    DROP INDEX IF EXISTS idx_iam_audit_action;
    DROP INDEX IF EXISTS idx_iam_audit_entity;
    DROP INDEX IF EXISTS idx_iam_audit_actor;
    DROP INDEX IF EXISTS idx_iam_audit_created;

    -- Drop indexes for iam_password_history
    DROP INDEX IF EXISTS idx_password_history_user;

    -- Drop indexes for iam_invitations
    DROP INDEX IF EXISTS idx_iam_invitations_tenant;
    DROP INDEX IF EXISTS idx_iam_invitations_email;
    DROP INDEX IF EXISTS idx_iam_invitations_token;
    DROP INDEX IF EXISTS idx_iam_invitations_status;

    -- Drop indexes for iam_token_blacklist
    DROP INDEX IF EXISTS idx_token_blacklist_jti;
    DROP INDEX IF EXISTS idx_token_blacklist_expires;

    -- Drop indexes for iam_sessions
    DROP INDEX IF EXISTS idx_iam_sessions_tenant;
    DROP INDEX IF EXISTS idx_iam_sessions_user;
    DROP INDEX IF EXISTS idx_iam_sessions_token;
    DROP INDEX IF EXISTS idx_iam_sessions_status;
    DROP INDEX IF EXISTS idx_iam_sessions_expires;

    -- Drop indexes for iam_group_roles
    DROP INDEX IF EXISTS idx_group_roles_tenant;

    -- Drop indexes for iam_user_groups
    DROP INDEX IF EXISTS idx_user_groups_tenant;
    DROP INDEX IF EXISTS idx_user_groups_user;
    DROP INDEX IF EXISTS idx_user_groups_group;

    -- Drop indexes for iam_role_permissions
    DROP INDEX IF EXISTS idx_role_permissions_tenant;
    DROP INDEX IF EXISTS idx_role_permissions_role;

    -- Drop indexes for iam_user_roles
    DROP INDEX IF EXISTS idx_user_roles_tenant;
    DROP INDEX IF EXISTS idx_user_roles_user;
    DROP INDEX IF EXISTS idx_user_roles_role;

    -- Drop indexes for iam_groups
    DROP INDEX IF EXISTS idx_iam_groups_tenant;

    -- Drop indexes for iam_permissions
    DROP INDEX IF EXISTS idx_iam_permissions_tenant;
    DROP INDEX IF EXISTS idx_iam_permissions_module;
    DROP INDEX IF EXISTS idx_iam_permissions_code;

    -- Drop indexes for iam_roles
    DROP INDEX IF EXISTS idx_iam_roles_tenant;
    DROP INDEX IF EXISTS idx_iam_roles_code;
    DROP INDEX IF EXISTS idx_iam_roles_level;

    -- Drop indexes for iam_users
    DROP INDEX IF EXISTS idx_iam_users_tenant;
    DROP INDEX IF EXISTS idx_iam_users_email;
    DROP INDEX IF EXISTS idx_iam_users_active;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS iam_rate_limits CASCADE;
    DROP TABLE IF EXISTS iam_audit_logs CASCADE;
    DROP TABLE IF EXISTS iam_password_history CASCADE;
    DROP TABLE IF EXISTS iam_password_policies CASCADE;
    DROP TABLE IF EXISTS iam_invitations CASCADE;
    DROP TABLE IF EXISTS iam_token_blacklist CASCADE;
    DROP TABLE IF EXISTS iam_sessions CASCADE;
    DROP TABLE IF EXISTS iam_group_roles CASCADE;
    DROP TABLE IF EXISTS iam_user_groups CASCADE;
    DROP TABLE IF EXISTS iam_role_permissions CASCADE;
    DROP TABLE IF EXISTS iam_user_roles CASCADE;
    DROP TABLE IF EXISTS iam_groups CASCADE;
    DROP TABLE IF EXISTS iam_permissions CASCADE;
    DROP TABLE IF EXISTS iam_roles CASCADE;
    DROP TABLE IF EXISTS iam_users CASCADE;

    RAISE NOTICE 'Migration 006_iam_module rolled back successfully';
END $$;
