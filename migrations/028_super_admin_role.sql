-- ============================================================================
-- AZALS - MIGRATION 028: Super Admin Role et Permissions
-- Création du rôle système super_admin avec toutes les permissions
-- ============================================================================

-- Version: 1.0.0
-- Date: 2026-01-08
-- Module: T0 - IAM (Sécurité)

BEGIN;

-- ============================================================================
-- TABLE: iam_system_init_log
-- Journal des initialisations système (append-only)
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_system_init_log (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    -- Opération
    operation VARCHAR(100) NOT NULL,  -- CREATOR_INIT, ROLE_SEED, etc.
    entity_type VARCHAR(50) NOT NULL,  -- USER, ROLE, PERMISSION
    entity_id INTEGER,
    entity_code VARCHAR(100),

    -- Contexte d'exécution
    executed_by VARCHAR(100) NOT NULL DEFAULT 'bootstrap',  -- bootstrap, migration, admin
    execution_mode VARCHAR(50) NOT NULL DEFAULT 'cli',  -- cli, api, migration
    ip_address VARCHAR(50),

    -- Détails
    details JSONB,
    justification TEXT,

    -- Sécurité
    checksum VARCHAR(64),  -- SHA-256 pour intégrité

    -- Timestamp (immutable)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche rapide
CREATE INDEX IF NOT EXISTS idx_system_init_tenant ON iam_system_init_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_system_init_operation ON iam_system_init_log(operation);
CREATE INDEX IF NOT EXISTS idx_system_init_created ON iam_system_init_log(created_at);

-- Bloquer les UPDATE et DELETE sur cette table (append-only)
CREATE OR REPLACE FUNCTION prevent_system_init_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'La table iam_system_init_log est en lecture seule (append-only). Les modifications ne sont pas autorisées.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS prevent_system_init_update ON iam_system_init_log;
CREATE TRIGGER prevent_system_init_update
    BEFORE UPDATE OR DELETE ON iam_system_init_log
    FOR EACH ROW EXECUTE FUNCTION prevent_system_init_modification();


-- ============================================================================
-- Ajout de colonnes pour la protection des rôles système
-- ============================================================================

-- Ajouter is_protected si elle n'existe pas (protection contre modification)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'iam_roles' AND column_name = 'is_protected'
    ) THEN
        ALTER TABLE iam_roles ADD COLUMN is_protected BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

-- Ajouter is_deletable si elle n'existe pas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'iam_roles' AND column_name = 'is_deletable'
    ) THEN
        ALTER TABLE iam_roles ADD COLUMN is_deletable BOOLEAN NOT NULL DEFAULT TRUE;
    END IF;
END $$;

-- Ajouter max_assignments pour limiter le nombre d'utilisateurs avec ce rôle
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'iam_roles' AND column_name = 'max_assignments'
    ) THEN
        ALTER TABLE iam_roles ADD COLUMN max_assignments INTEGER DEFAULT NULL;
    END IF;
END $$;


-- ============================================================================
-- Ajout de colonnes pour la protection des utilisateurs système
-- ============================================================================

-- Ajouter is_system_account si elle n'existe pas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'iam_users' AND column_name = 'is_system_account'
    ) THEN
        ALTER TABLE iam_users ADD COLUMN is_system_account BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

-- Ajouter is_protected pour empêcher la rétrogradation
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'iam_users' AND column_name = 'is_protected'
    ) THEN
        ALTER TABLE iam_users ADD COLUMN is_protected BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

-- Ajouter created_via pour traçabilité
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'iam_users' AND column_name = 'created_via'
    ) THEN
        ALTER TABLE iam_users ADD COLUMN created_via VARCHAR(50) DEFAULT 'api';
    END IF;
END $$;


-- ============================================================================
-- TRIGGER: Protection des rôles système
-- ============================================================================

CREATE OR REPLACE FUNCTION protect_system_roles()
RETURNS TRIGGER AS $$
BEGIN
    -- Empêcher la modification des rôles protégés
    IF OLD.is_protected = TRUE THEN
        IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'Impossible de supprimer le rôle système protégé: %', OLD.code;
        END IF;

        -- Autoriser uniquement la mise à jour de is_active
        IF TG_OP = 'UPDATE' THEN
            IF OLD.code != NEW.code OR
               OLD.level != NEW.level OR
               OLD.is_system != NEW.is_system OR
               OLD.is_protected != NEW.is_protected OR
               OLD.is_assignable != NEW.is_assignable THEN
                RAISE EXCEPTION 'Impossible de modifier les propriétés du rôle système protégé: %', OLD.code;
            END IF;
        END IF;
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS protect_system_roles_trigger ON iam_roles;
CREATE TRIGGER protect_system_roles_trigger
    BEFORE UPDATE OR DELETE ON iam_roles
    FOR EACH ROW EXECUTE FUNCTION protect_system_roles();


-- ============================================================================
-- TRIGGER: Protection des comptes système
-- ============================================================================

CREATE OR REPLACE FUNCTION protect_system_users()
RETURNS TRIGGER AS $$
BEGIN
    -- Empêcher la modification des comptes protégés
    IF OLD.is_protected = TRUE THEN
        IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'Impossible de supprimer le compte système protégé: %', OLD.email;
        END IF;

        -- Autoriser uniquement certaines mises à jour
        IF TG_OP = 'UPDATE' THEN
            -- Empêcher de retirer la protection ou le statut système
            IF OLD.is_protected = TRUE AND NEW.is_protected = FALSE THEN
                RAISE EXCEPTION 'Impossible de retirer la protection du compte système: %', OLD.email;
            END IF;
            IF OLD.is_system_account = TRUE AND NEW.is_system_account = FALSE THEN
                RAISE EXCEPTION 'Impossible de retirer le statut système du compte: %', OLD.email;
            END IF;
        END IF;
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS protect_system_users_trigger ON iam_users;
CREATE TRIGGER protect_system_users_trigger
    BEFORE UPDATE OR DELETE ON iam_users
    FOR EACH ROW EXECUTE FUNCTION protect_system_users();


-- ============================================================================
-- FONCTION: Vérifier si un utilisateur peut recevoir le rôle super_admin
-- ============================================================================

CREATE OR REPLACE FUNCTION check_super_admin_assignment()
RETURNS TRIGGER AS $$
DECLARE
    role_code VARCHAR(50);
    current_super_admins INTEGER;
    max_allowed INTEGER;
BEGIN
    -- Récupérer le code du rôle
    SELECT code, max_assignments INTO role_code, max_allowed
    FROM iam_roles WHERE id = NEW.role_id;

    -- Vérification spécifique pour super_admin
    IF role_code = 'super_admin' THEN
        -- Compter les super_admins existants pour ce tenant
        SELECT COUNT(*) INTO current_super_admins
        FROM iam_user_roles ur
        JOIN iam_roles r ON ur.role_id = r.id
        WHERE r.code = 'super_admin'
          AND ur.tenant_id = NEW.tenant_id
          AND ur.is_active = TRUE
          AND ur.id != COALESCE(NEW.id, -1);

        -- Vérifier la limite (par défaut 1 pour super_admin)
        IF max_allowed IS NOT NULL AND current_super_admins >= max_allowed THEN
            RAISE EXCEPTION 'Nombre maximum de super_admins atteint (%). Création d''un nouveau super_admin interdite sans action explicite.', max_allowed;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS check_super_admin_assignment_trigger ON iam_user_roles;
CREATE TRIGGER check_super_admin_assignment_trigger
    BEFORE INSERT ON iam_user_roles
    FOR EACH ROW EXECUTE FUNCTION check_super_admin_assignment();


-- ============================================================================
-- COMMENTAIRES DE DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE iam_system_init_log IS
'Journal append-only des initialisations système. Contient l''historique de création des comptes système et rôles fondamentaux.';

COMMENT ON COLUMN iam_roles.is_protected IS
'Si TRUE, le rôle ne peut pas être modifié ou supprimé. Réservé aux rôles système fondamentaux.';

COMMENT ON COLUMN iam_roles.is_deletable IS
'Si FALSE, le rôle ne peut pas être supprimé même par un super_admin.';

COMMENT ON COLUMN iam_roles.max_assignments IS
'Nombre maximum d''utilisateurs pouvant avoir ce rôle. NULL = illimité. Pour super_admin, typiquement 1.';

COMMENT ON COLUMN iam_users.is_system_account IS
'Si TRUE, ce compte est un compte système (créateur, service account). Traitement spécial.';

COMMENT ON COLUMN iam_users.is_protected IS
'Si TRUE, le compte ne peut pas être rétrogradé, supprimé ou modifié de manière critique.';

COMMENT ON COLUMN iam_users.created_via IS
'Source de création du compte: api, cli, migration, bootstrap, invitation.';


COMMIT;

-- ============================================================================
-- FIN MIGRATION 028 - Super Admin Role
-- ============================================================================
