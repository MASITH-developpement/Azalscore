-- ============================================================================
-- AZALS - SCRIPT DE MIGRATION PRODUCTION
-- ============================================================================
-- ENVIRONNEMENT: Production (données à préserver)
-- ACTION: Migration sécurisée BIGINT → UUID
-- PROCESSUS: Transactionnel, réversible, avec backup
-- ============================================================================

-- PRÉAMBULE: Ce script est un TEMPLATE
-- Adapter les noms de tables/colonnes selon les besoins réels détectés
-- ============================================================================

BEGIN;

-- 1. ACTIVER LES EXTENSIONS REQUISES
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. CRÉER UNE TABLE DE MAPPING POUR LA TRAÇABILITÉ
-- ============================================================================
CREATE TABLE IF NOT EXISTS _migration_uuid_mapping (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    old_bigint_value BIGINT,
    new_uuid_value UUID NOT NULL DEFAULT gen_random_uuid(),
    migrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(table_name, column_name, old_bigint_value)
);

-- 3. FONCTION DE MIGRATION GÉNÉRIQUE
-- ============================================================================
CREATE OR REPLACE FUNCTION migrate_column_to_uuid(
    p_table_name TEXT,
    p_column_name TEXT,
    p_is_pk BOOLEAN DEFAULT FALSE
) RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER := 0;
    v_temp_col TEXT;
    v_sql TEXT;
BEGIN
    v_temp_col := p_column_name || '_uuid_new';

    -- Vérifier si la colonne existe et est BIGINT
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = p_table_name
        AND column_name = p_column_name
        AND data_type IN ('bigint', 'integer')
    ) THEN
        RAISE NOTICE 'Colonne %.% n''est pas BIGINT, ignorée', p_table_name, p_column_name;
        RETURN 0;
    END IF;

    -- Ajouter colonne UUID temporaire
    v_sql := format('ALTER TABLE %I ADD COLUMN IF NOT EXISTS %I UUID', p_table_name, v_temp_col);
    EXECUTE v_sql;

    -- Générer les UUID et enregistrer le mapping
    v_sql := format('
        WITH mapping AS (
            INSERT INTO _migration_uuid_mapping (table_name, column_name, old_bigint_value, new_uuid_value)
            SELECT %L, %L, %I, gen_random_uuid()
            FROM %I
            WHERE %I IS NOT NULL
            ON CONFLICT (table_name, column_name, old_bigint_value) DO NOTHING
            RETURNING old_bigint_value, new_uuid_value
        )
        UPDATE %I t
        SET %I = m.new_uuid_value
        FROM mapping m
        WHERE t.%I = m.old_bigint_value',
        p_table_name, p_column_name, p_column_name,
        p_table_name, p_column_name,
        p_table_name, v_temp_col, p_column_name
    );
    EXECUTE v_sql;

    GET DIAGNOSTICS v_count = ROW_COUNT;

    RAISE NOTICE 'Migré %.%: % lignes', p_table_name, p_column_name, v_count;

    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- 4. FONCTION POUR FINALISER LA MIGRATION D'UNE COLONNE
-- ============================================================================
CREATE OR REPLACE FUNCTION finalize_uuid_migration(
    p_table_name TEXT,
    p_column_name TEXT,
    p_is_pk BOOLEAN DEFAULT FALSE
) RETURNS VOID AS $$
DECLARE
    v_temp_col TEXT;
    v_old_col TEXT;
    v_constraint_name TEXT;
BEGIN
    v_temp_col := p_column_name || '_uuid_new';
    v_old_col := p_column_name || '_old_bigint';

    -- Vérifier que la colonne temporaire existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = p_table_name
        AND column_name = v_temp_col
    ) THEN
        RAISE NOTICE 'Colonne temporaire %.% inexistante, ignorée', p_table_name, v_temp_col;
        RETURN;
    END IF;

    -- Renommer l'ancienne colonne (backup)
    EXECUTE format('ALTER TABLE %I RENAME COLUMN %I TO %I', p_table_name, p_column_name, v_old_col);

    -- Renommer la nouvelle colonne
    EXECUTE format('ALTER TABLE %I RENAME COLUMN %I TO %I', p_table_name, v_temp_col, p_column_name);

    -- Si c'est une PK, recréer la contrainte
    IF p_is_pk THEN
        v_constraint_name := p_table_name || '_pkey';
        EXECUTE format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I', p_table_name, v_constraint_name);
        EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I PRIMARY KEY (%I)', p_table_name, v_constraint_name, p_column_name);
    END IF;

    -- Ajouter NOT NULL et DEFAULT
    EXECUTE format('ALTER TABLE %I ALTER COLUMN %I SET NOT NULL', p_table_name, p_column_name);
    EXECUTE format('ALTER TABLE %I ALTER COLUMN %I SET DEFAULT gen_random_uuid()', p_table_name, p_column_name);

    RAISE NOTICE 'Finalisé %.%', p_table_name, p_column_name;
END;
$$ LANGUAGE plpgsql;

-- 5. FONCTION POUR MIGRER UNE FK
-- ============================================================================
CREATE OR REPLACE FUNCTION migrate_fk_to_uuid(
    p_table_name TEXT,
    p_fk_column TEXT,
    p_ref_table TEXT,
    p_ref_column TEXT
) RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER := 0;
    v_temp_col TEXT;
BEGIN
    v_temp_col := p_fk_column || '_uuid_new';

    -- Vérifier si la colonne FK existe et est BIGINT
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = p_table_name
        AND column_name = p_fk_column
        AND data_type IN ('bigint', 'integer')
    ) THEN
        RAISE NOTICE 'FK %.% n''est pas BIGINT, ignorée', p_table_name, p_fk_column;
        RETURN 0;
    END IF;

    -- Ajouter colonne UUID temporaire
    EXECUTE format('ALTER TABLE %I ADD COLUMN IF NOT EXISTS %I UUID', p_table_name, v_temp_col);

    -- Mapper les valeurs via la table de mapping
    EXECUTE format('
        UPDATE %I t
        SET %I = m.new_uuid_value
        FROM _migration_uuid_mapping m
        WHERE m.table_name = %L
        AND m.column_name = %L
        AND t.%I = m.old_bigint_value',
        p_table_name, v_temp_col,
        p_ref_table, p_ref_column,
        p_fk_column
    );

    GET DIAGNOSTICS v_count = ROW_COUNT;

    RAISE NOTICE 'FK migrée %.% → %.%: % lignes', p_table_name, p_fk_column, p_ref_table, p_ref_column, v_count;

    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- 6. EXEMPLE DE MIGRATION (ADAPTER SELON LES BESOINS)
-- ============================================================================
-- IMPORTANT: Ces exemples ne sont à exécuter QUE si des tables BIGINT existent

-- Exemple: Migrer maintenance_assets.id (si nécessaire)
-- SELECT migrate_column_to_uuid('maintenance_assets', 'id', TRUE);

-- Exemple: Migrer les FK qui référencent maintenance_assets.id
-- SELECT migrate_fk_to_uuid('maintenance_asset_components', 'asset_id', 'maintenance_assets', 'id');
-- SELECT migrate_fk_to_uuid('maintenance_work_orders', 'asset_id', 'maintenance_assets', 'id');
-- etc.

-- Exemple: Finaliser après vérification
-- SELECT finalize_uuid_migration('maintenance_assets', 'id', TRUE);
-- SELECT finalize_uuid_migration('maintenance_asset_components', 'asset_id', FALSE);

-- 7. NETTOYAGE POST-MIGRATION (À EXÉCUTER APRÈS VALIDATION)
-- ============================================================================
-- ATTENTION: Ne supprimer les colonnes _old_bigint qu'après validation complète

-- DROP TABLE IF EXISTS _migration_uuid_mapping;
-- ALTER TABLE maintenance_assets DROP COLUMN IF EXISTS id_old_bigint;

-- 8. VÉRIFICATION FINALE
-- ============================================================================
DO $$
DECLARE
    bigint_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO bigint_count
    FROM information_schema.columns c
    JOIN information_schema.table_constraints tc
        ON c.table_name = tc.table_name
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND c.column_name = kcu.column_name
    WHERE tc.constraint_type = 'PRIMARY KEY'
    AND tc.table_schema = 'public'
    AND c.data_type IN ('bigint', 'integer')
    AND c.table_name NOT LIKE 'pg_%'
    AND c.table_name NOT LIKE '_migration%';

    IF bigint_count > 0 THEN
        RAISE WARNING 'ATTENTION: % PK utilisent encore BIGINT/INTEGER', bigint_count;
    ELSE
        RAISE NOTICE 'SUCCÈS: Toutes les PK sont UUID';
    END IF;
END $$;

-- Pour appliquer les changements:
-- COMMIT;

-- Pour annuler en cas de problème:
-- ROLLBACK;

-- Message final
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'SCRIPT DE MIGRATION PRODUCTION CHARGÉ';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Ce script fournit les fonctions de migration sécurisées.';
    RAISE NOTICE '';
    RAISE NOTICE 'ÉTAPES À SUIVRE:';
    RAISE NOTICE '1. Identifier les tables avec BIGINT (voir audit)';
    RAISE NOTICE '2. Appeler migrate_column_to_uuid() pour chaque PK';
    RAISE NOTICE '3. Appeler migrate_fk_to_uuid() pour chaque FK';
    RAISE NOTICE '4. Valider les données migrées';
    RAISE NOTICE '5. Appeler finalize_uuid_migration()';
    RAISE NOTICE '6. COMMIT pour appliquer';
    RAISE NOTICE '';
    RAISE NOTICE 'Table de mapping: _migration_uuid_mapping';
    RAISE NOTICE '============================================================';
END $$;

COMMIT;
