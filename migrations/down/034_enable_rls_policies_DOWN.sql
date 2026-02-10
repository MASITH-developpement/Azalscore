-- AZALS - ROLLBACK Migration: Enable RLS Policies
-- Désactive les politiques RLS

DO $$
BEGIN
    -- Supprimer les politiques RLS sur items
    DROP POLICY IF EXISTS tenant_isolation_select ON items;
    DROP POLICY IF EXISTS tenant_isolation_insert ON items;
    DROP POLICY IF EXISTS tenant_isolation_update ON items;
    DROP POLICY IF EXISTS tenant_isolation_delete ON items;

    -- Supprimer les politiques RLS sur users
    DROP POLICY IF EXISTS users_tenant_isolation_select ON users;
    DROP POLICY IF EXISTS users_tenant_isolation_insert ON users;
    DROP POLICY IF EXISTS users_tenant_isolation_update ON users;
    DROP POLICY IF EXISTS users_tenant_isolation_delete ON users;

    -- Supprimer la fonction helper
    DROP FUNCTION IF EXISTS get_current_tenant_id();

    -- Note: RLS reste activé sur les tables, mais sans politiques
    -- les superusers peuvent toujours accéder aux données

    RAISE NOTICE 'Migration 034_enable_rls_policies rolled back successfully';
END $$;
