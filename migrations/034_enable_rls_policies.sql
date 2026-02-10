-- AZALS - Migration: Enable RLS Policies
-- =========================================
-- SÉCURITÉ P1: Active les politiques RLS pour defense-in-depth
-- Garantit l'isolation multi-tenant même en cas de bug applicatif
--
-- PRÉ-REQUIS: L'application doit définir app.current_tenant_id avant chaque transaction
-- Exemple: SET LOCAL app.current_tenant_id = 'tenant_xyz';
--
-- NOTE: Cette migration active RLS sur toutes les tables avec tenant_id

-- ============================================================================
-- 1. FONCTION HELPER POUR RÉCUPÉRER LE TENANT COURANT
-- ============================================================================

CREATE OR REPLACE FUNCTION get_current_tenant_id()
RETURNS VARCHAR(255) AS $$
BEGIN
    -- Retourne le tenant_id depuis la variable de session
    -- Si non défini, retourne une chaîne vide (bloque tout accès)
    RETURN COALESCE(
        current_setting('app.current_tenant_id', true),
        ''
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_current_tenant_id() IS
    'Retourne le tenant_id courant depuis la session PostgreSQL. '
    'Utilisé par les politiques RLS pour l''isolation multi-tenant.';

-- ============================================================================
-- 2. POLITIQUES RLS SUR TABLE ITEMS
-- ============================================================================

-- Supprimer l'ancienne politique si elle existe
DROP POLICY IF EXISTS tenant_isolation_policy ON items;

-- Politique de lecture: uniquement les rows du tenant courant
CREATE POLICY tenant_isolation_select ON items
    FOR SELECT
    USING (tenant_id = get_current_tenant_id());

-- Politique d'insertion: tenant_id doit correspondre au tenant courant
CREATE POLICY tenant_isolation_insert ON items
    FOR INSERT
    WITH CHECK (tenant_id = get_current_tenant_id());

-- Politique de mise à jour: uniquement les rows du tenant courant
CREATE POLICY tenant_isolation_update ON items
    FOR UPDATE
    USING (tenant_id = get_current_tenant_id())
    WITH CHECK (tenant_id = get_current_tenant_id());

-- Politique de suppression: uniquement les rows du tenant courant
CREATE POLICY tenant_isolation_delete ON items
    FOR DELETE
    USING (tenant_id = get_current_tenant_id());

-- ============================================================================
-- 3. POLITIQUES RLS SUR TABLE USERS
-- ============================================================================

-- Activer RLS si pas déjà fait
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS users_tenant_isolation_select ON users;
DROP POLICY IF EXISTS users_tenant_isolation_insert ON users;
DROP POLICY IF EXISTS users_tenant_isolation_update ON users;
DROP POLICY IF EXISTS users_tenant_isolation_delete ON users;

CREATE POLICY users_tenant_isolation_select ON users
    FOR SELECT
    USING (tenant_id = get_current_tenant_id());

CREATE POLICY users_tenant_isolation_insert ON users
    FOR INSERT
    WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY users_tenant_isolation_update ON users
    FOR UPDATE
    USING (tenant_id = get_current_tenant_id())
    WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY users_tenant_isolation_delete ON users
    FOR DELETE
    USING (tenant_id = get_current_tenant_id());

-- ============================================================================
-- 4. BYPASS RLS POUR LES SUPERUSERS/ADMINS
-- ============================================================================

-- L'utilisateur de l'application peut contourner RLS pour les opérations admin
-- Cela doit être utilisé avec parcimonie et uniquement pour les opérations système

-- Note: Pour les opérations admin cross-tenant, utiliser:
-- SET LOCAL role = 'azals_admin';
-- ou créer un rôle spécifique avec BYPASSRLS

-- ============================================================================
-- 5. VÉRIFICATION
-- ============================================================================

DO $$
DECLARE
    rls_enabled_items BOOLEAN;
    rls_enabled_users BOOLEAN;
BEGIN
    -- Vérifier que RLS est activé
    SELECT relrowsecurity INTO rls_enabled_items
    FROM pg_class WHERE relname = 'items';

    SELECT relrowsecurity INTO rls_enabled_users
    FROM pg_class WHERE relname = 'users';

    IF rls_enabled_items AND rls_enabled_users THEN
        RAISE NOTICE 'RLS policies enabled successfully on items and users tables';
    ELSE
        RAISE WARNING 'RLS may not be fully enabled. Check table settings.';
    END IF;
END $$;

-- ============================================================================
-- DOCUMENTATION
-- ============================================================================

COMMENT ON POLICY tenant_isolation_select ON items IS
    'RLS: Restreint SELECT aux rows du tenant courant (app.current_tenant_id)';
COMMENT ON POLICY tenant_isolation_insert ON items IS
    'RLS: Vérifie que INSERT utilise le tenant_id courant';
COMMENT ON POLICY tenant_isolation_update ON items IS
    'RLS: Restreint UPDATE aux rows du tenant courant';
COMMENT ON POLICY tenant_isolation_delete ON items IS
    'RLS: Restreint DELETE aux rows du tenant courant';
