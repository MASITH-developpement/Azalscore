-- AZALS - Migration: Unique constraint (tenant_id, email) sur users
-- ===================================================================
-- SÉCURITÉ P1-5: Garantit l'unicité email PAR TENANT (pas globale)
-- Permet le même email dans des tenants différents
--
-- PRÉ-REQUIS: Supprimer l'ancienne contrainte unique sur email seul

-- ============================================================================
-- 1. SUPPRIMER L'ANCIENNE CONTRAINTE UNIQUE SUR EMAIL
-- ============================================================================

-- Supprimer l'index unique existant sur email (si existe)
DROP INDEX IF EXISTS ix_users_email;
DROP INDEX IF EXISTS users_email_key;

-- Supprimer la contrainte unique si elle existe
DO $$
BEGIN
    -- Essayer de supprimer la contrainte (nom peut varier)
    ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_key;
EXCEPTION
    WHEN undefined_object THEN
        -- Contrainte n'existe pas, continuer
        NULL;
END $$;

-- ============================================================================
-- 2. CRÉER LA NOUVELLE CONTRAINTE UNIQUE COMPOSITE
-- ============================================================================

-- Créer un index unique composite sur (tenant_id, email)
-- Cet index garantit l'unicité et optimise les recherches
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_tenant_email_unique
    ON users (tenant_id, email);

-- Alternative: Contrainte explicite (commentée car l'index unique suffit)
-- ALTER TABLE users ADD CONSTRAINT uq_users_tenant_email
--     UNIQUE (tenant_id, email);

-- ============================================================================
-- 3. VÉRIFICATION
-- ============================================================================

DO $$
DECLARE
    idx_exists BOOLEAN;
BEGIN
    -- Vérifier que l'index existe
    SELECT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'users'
        AND indexname = 'idx_users_tenant_email_unique'
    ) INTO idx_exists;

    IF idx_exists THEN
        RAISE NOTICE 'Migration 035: Unique constraint (tenant_id, email) created successfully';
    ELSE
        RAISE WARNING 'Migration 035: Index creation may have failed';
    END IF;
END $$;

-- ============================================================================
-- DOCUMENTATION
-- ============================================================================

COMMENT ON INDEX idx_users_tenant_email_unique IS
    'P1-5: Garantit unicité email par tenant. '
    'Permet le même email dans différents tenants (multi-tenant SaaS).';
