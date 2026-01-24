-- AZALS - ROLLBACK Migration Authentification
-- Annule la création de la table users
-- ATTENTION: Perte de données si table contient des enregistrements!

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        -- Supprimer les contraintes
        ALTER TABLE users DROP CONSTRAINT IF EXISTS users_is_active_bool;
        ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_valid;
        ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_not_empty;
        ALTER TABLE users DROP CONSTRAINT IF EXISTS users_tenant_id_not_empty;

        -- Supprimer les index
        DROP INDEX IF EXISTS idx_users_tenant_email;
        DROP INDEX IF EXISTS idx_users_email;
        DROP INDEX IF EXISTS idx_users_tenant_id;

        -- Supprimer la table
        DROP TABLE users;

        RAISE NOTICE 'Migration 002_auth rolled back successfully';
    ELSE
        RAISE NOTICE 'Table users does not exist, nothing to rollback';
    END IF;
END $$;
