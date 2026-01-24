-- AZALS - ROLLBACK Migration: Unique constraint (tenant_id, email)
-- Restaure l'unicité globale sur email (comportement pré-P1-5)

DO $$
BEGIN
    -- Supprimer l'index unique composite
    DROP INDEX IF EXISTS idx_users_tenant_email_unique;

    -- Recréer l'ancien index unique sur email seul
    -- ATTENTION: Peut échouer si des doublons email existent entre tenants
    CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);

    RAISE NOTICE 'Migration 035_unique_tenant_email rolled back successfully';
EXCEPTION
    WHEN unique_violation THEN
        RAISE WARNING 'Rollback failed: duplicate emails exist across tenants';
        RAISE;
END $$;
