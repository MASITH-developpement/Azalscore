-- ============================================================================
-- AZALS - Migration 033 : Champs Beta Tenant
-- ============================================================================
-- Version: 1.0.0
-- Date: 2026-01-10
-- Description: Ajoute les champs nécessaires pour la gestion des tenants beta
--              et le changement de mot de passe obligatoire
-- ============================================================================

-- ============================================================================
-- TABLE: tenants - Ajout du champ environment
-- ============================================================================
-- Permet de distinguer les environnements (beta, production, staging, etc.)

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tenants' AND column_name = 'environment'
    ) THEN
        ALTER TABLE tenants ADD COLUMN environment VARCHAR(20) DEFAULT 'production';

        -- Contrainte: valeurs autorisées uniquement
        ALTER TABLE tenants ADD CONSTRAINT tenants_environment_valid
            CHECK (environment IN ('beta', 'production', 'staging', 'development'));

        -- Index pour filtrer par environnement
        CREATE INDEX IF NOT EXISTS idx_tenants_environment ON tenants(environment);

        RAISE NOTICE 'Colonne tenants.environment ajoutée avec succès';
    ELSE
        RAISE NOTICE 'Colonne tenants.environment existe déjà';
    END IF;
END $$;

-- ============================================================================
-- TABLE: users - Ajout du champ must_change_password
-- ============================================================================
-- Indique si l'utilisateur doit changer son mot de passe au prochain login

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'must_change_password'
    ) THEN
        ALTER TABLE users ADD COLUMN must_change_password INTEGER DEFAULT 0 NOT NULL;

        -- Contrainte: valeur booléenne uniquement (0 ou 1)
        ALTER TABLE users ADD CONSTRAINT users_must_change_password_bool
            CHECK (must_change_password IN (0, 1));

        -- Index pour identifier rapidement les utilisateurs devant changer leur mot de passe
        CREATE INDEX IF NOT EXISTS idx_users_must_change_password ON users(must_change_password);

        RAISE NOTICE 'Colonne users.must_change_password ajoutée avec succès';
    ELSE
        RAISE NOTICE 'Colonne users.must_change_password existe déjà';
    END IF;
END $$;

-- ============================================================================
-- TABLE: users - Ajout du champ password_changed_at
-- ============================================================================
-- Trace la date du dernier changement de mot de passe (conformité sécurité)

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'password_changed_at'
    ) THEN
        ALTER TABLE users ADD COLUMN password_changed_at TIMESTAMP NULL;

        RAISE NOTICE 'Colonne users.password_changed_at ajoutée avec succès';
    ELSE
        RAISE NOTICE 'Colonne users.password_changed_at existe déjà';
    END IF;
END $$;

-- ============================================================================
-- INDEX COMPOSITES pour performances multi-tenant beta
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_tenants_environment_status ON tenants(environment, status);
CREATE INDEX IF NOT EXISTS idx_users_tenant_must_change ON users(tenant_id, must_change_password);

-- ============================================================================
-- FIN DE LA MIGRATION
-- ============================================================================
