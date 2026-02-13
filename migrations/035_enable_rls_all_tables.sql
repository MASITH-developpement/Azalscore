-- AZALS - Migration: Enable RLS on ALL Tenant-Scoped Tables
-- ===========================================================
-- SÉCURITÉ P1: Active Row-Level Security sur TOUTES les tables avec tenant_id
-- Garantit l'isolation multi-tenant au niveau base de données (defense-in-depth)
--
-- PRÉ-REQUIS: L'application DOIT définir app.current_tenant_id avant chaque transaction
-- Exemple: SET LOCAL app.current_tenant_id = 'tenant_xyz';
--
-- NOTE: Ce script est idempotent - peut être relancé sans risque
-- DATE: 2026-02-12
-- AUTEUR: AZALS Security Team

-- ============================================================================
-- 1. FONCTION HELPER (si pas déjà créée)
-- ============================================================================

CREATE OR REPLACE FUNCTION get_current_tenant_id()
RETURNS VARCHAR(255) AS $$
BEGIN
    RETURN COALESCE(
        current_setting('app.current_tenant_id', true),
        ''
    );
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION get_current_tenant_id() IS
    'RLS: Retourne le tenant_id depuis la session PostgreSQL pour l''isolation multi-tenant.';

-- ============================================================================
-- 2. PROCÉDURE POUR ACTIVER RLS SUR UNE TABLE
-- ============================================================================

CREATE OR REPLACE FUNCTION enable_rls_on_table(table_name TEXT)
RETURNS VOID AS $$
DECLARE
    policy_exists BOOLEAN;
BEGIN
    -- Vérifier si la table a une colonne tenant_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND information_schema.columns.table_name = enable_rls_on_table.table_name
        AND column_name = 'tenant_id'
    ) THEN
        RAISE NOTICE 'Table % has no tenant_id column, skipping RLS', table_name;
        RETURN;
    END IF;

    -- Activer RLS sur la table
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);

    -- Supprimer les anciennes politiques si elles existent
    EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_select ON %I', table_name);
    EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_insert ON %I', table_name);
    EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_update ON %I', table_name);
    EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_delete ON %I', table_name);

    -- Créer les nouvelles politiques
    -- SELECT: uniquement les rows du tenant courant
    EXECUTE format(
        'CREATE POLICY tenant_isolation_select ON %I FOR SELECT USING (tenant_id = get_current_tenant_id())',
        table_name
    );

    -- INSERT: tenant_id doit correspondre au tenant courant
    EXECUTE format(
        'CREATE POLICY tenant_isolation_insert ON %I FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id())',
        table_name
    );

    -- UPDATE: uniquement les rows du tenant courant
    EXECUTE format(
        'CREATE POLICY tenant_isolation_update ON %I FOR UPDATE USING (tenant_id = get_current_tenant_id()) WITH CHECK (tenant_id = get_current_tenant_id())',
        table_name
    );

    -- DELETE: uniquement les rows du tenant courant
    EXECUTE format(
        'CREATE POLICY tenant_isolation_delete ON %I FOR DELETE USING (tenant_id = get_current_tenant_id())',
        table_name
    );

    RAISE NOTICE 'RLS enabled on table %', table_name;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 3. ACTIVER RLS SUR TOUTES LES TABLES AVEC TENANT_ID
-- ============================================================================

DO $$
DECLARE
    table_record RECORD;
    tables_processed INT := 0;
    tables_skipped INT := 0;
BEGIN
    RAISE NOTICE '=== Starting RLS activation on all tenant-scoped tables ===';

    -- Parcourir toutes les tables du schéma public avec tenant_id
    FOR table_record IN
        SELECT DISTINCT c.table_name
        FROM information_schema.columns c
        WHERE c.table_schema = 'public'
        AND c.column_name = 'tenant_id'
        AND c.table_name NOT LIKE 'pg_%'
        AND c.table_name NOT IN ('spatial_ref_sys', 'geography_columns', 'geometry_columns')
        ORDER BY c.table_name
    LOOP
        BEGIN
            PERFORM enable_rls_on_table(table_record.table_name);
            tables_processed := tables_processed + 1;
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Failed to enable RLS on table %: %', table_record.table_name, SQLERRM;
            tables_skipped := tables_skipped + 1;
        END;
    END LOOP;

    RAISE NOTICE '=== RLS activation complete: % tables processed, % skipped ===',
        tables_processed, tables_skipped;
END $$;

-- ============================================================================
-- 4. TABLES EXEMPTÉES (globales par design)
-- ============================================================================

-- Ces tables sont intentionnellement globales et n'ont pas de RLS:
-- - tenants (gestion des tenants eux-mêmes)
-- - commercial_plans (plans tarifaires globaux)
-- - subscription_plans_global (si existant)
-- - ai_learning_data (apprentissage anonymisé cross-tenant)

-- Désactiver RLS sur les tables globales (si activé par erreur)
DO $$
DECLARE
    global_tables TEXT[] := ARRAY[
        'tenants',
        'trial_registrations',
        'ai_learning_data',
        'iam_token_blacklist',
        'iam_rate_limits'
    ];
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY global_tables
    LOOP
        BEGIN
            EXECUTE format('ALTER TABLE %I DISABLE ROW LEVEL SECURITY', tbl);
            RAISE NOTICE 'RLS disabled on global table %', tbl;
        EXCEPTION WHEN undefined_table THEN
            -- Table n'existe pas, ignorer
            NULL;
        END;
    END LOOP;
END $$;

-- ============================================================================
-- 5. VÉRIFICATION
-- ============================================================================

DO $$
DECLARE
    rls_count INT;
    non_rls_count INT;
BEGIN
    -- Compter les tables avec RLS activé
    SELECT COUNT(*) INTO rls_count
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
    AND c.relkind = 'r'
    AND c.relrowsecurity = true;

    -- Compter les tables tenant-scoped sans RLS
    SELECT COUNT(*) INTO non_rls_count
    FROM information_schema.columns ic
    JOIN pg_class c ON c.relname = ic.table_name
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE ic.table_schema = 'public'
    AND ic.column_name = 'tenant_id'
    AND n.nspname = 'public'
    AND c.relrowsecurity = false;

    RAISE NOTICE '=== RLS Status ===';
    RAISE NOTICE 'Tables with RLS enabled: %', rls_count;
    RAISE NOTICE 'Tenant-scoped tables without RLS: %', non_rls_count;

    IF non_rls_count > 0 THEN
        RAISE WARNING 'SECURITY: % tenant-scoped tables do not have RLS enabled!', non_rls_count;
    END IF;
END $$;

-- ============================================================================
-- 6. INDEX POUR PERFORMANCE RLS
-- ============================================================================

-- S'assurer que toutes les colonnes tenant_id sont indexées
DO $$
DECLARE
    table_record RECORD;
    index_name TEXT;
BEGIN
    FOR table_record IN
        SELECT c.table_name
        FROM information_schema.columns c
        WHERE c.table_schema = 'public'
        AND c.column_name = 'tenant_id'
        AND NOT EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE pg_indexes.tablename = c.table_name
            AND pg_indexes.indexdef LIKE '%tenant_id%'
        )
    LOOP
        index_name := table_record.table_name || '_tenant_id_idx';
        BEGIN
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS %I ON %I (tenant_id)',
                index_name,
                table_record.table_name
            );
            RAISE NOTICE 'Created index % on %.tenant_id', index_name, table_record.table_name;
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Failed to create index on %.tenant_id: %',
                table_record.table_name, SQLERRM;
        END;
    END LOOP;
END $$;

-- ============================================================================
-- DOCUMENTATION
-- ============================================================================

COMMENT ON FUNCTION enable_rls_on_table(TEXT) IS
    'Active RLS (Row-Level Security) sur une table avec les politiques standard d''isolation tenant.';

-- Nettoyer la fonction temporaire
-- DROP FUNCTION IF EXISTS enable_rls_on_table(TEXT);
-- Note: On garde la fonction pour pouvoir activer RLS sur de nouvelles tables facilement
