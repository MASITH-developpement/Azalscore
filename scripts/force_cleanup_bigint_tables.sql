-- ============================================================================
-- AZALS - SCRIPT DE NETTOYAGE FORCÉ DES TABLES BIGINT
-- ============================================================================
-- OBJECTIF: Supprimer TOUTES les tables dont la PK utilise BIGINT/INTEGER
-- ENVIRONNEMENT: DEV / TEST uniquement (détruit les données)
-- EXÉCUTER AVANT tout redémarrage de l'application
-- ============================================================================

-- ÉTAPE 0: Activer les extensions UUID
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ÉTAPE 1: Identifier les tables avec PK BIGINT/INTEGER
DO $$
DECLARE
    r RECORD;
    table_count INTEGER := 0;
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'AUDIT DES TABLES AVEC PK BIGINT/INTEGER';
    RAISE NOTICE '============================================================';

    FOR r IN (
        SELECT
            tc.table_name,
            kcu.column_name,
            c.udt_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.columns c
            ON c.table_name = tc.table_name
            AND c.column_name = kcu.column_name
            AND c.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY'
        AND tc.table_schema = 'public'
        AND c.udt_name IN ('int4', 'int8', 'serial', 'bigserial')
        ORDER BY tc.table_name
    ) LOOP
        table_count := table_count + 1;
        RAISE NOTICE '  [BIGINT] %.% (type: %)', r.table_name, r.column_name, r.udt_name;
    END LOOP;

    IF table_count = 0 THEN
        RAISE NOTICE '  Aucune table avec PK BIGINT trouvée - schéma propre!';
    ELSE
        RAISE NOTICE '============================================================';
        RAISE NOTICE 'TOTAL: % table(s) avec PK BIGINT à supprimer', table_count;
        RAISE NOTICE '============================================================';
    END IF;
END $$;

-- ÉTAPE 2: Désactiver temporairement les contraintes FK pour permettre DROP CASCADE
SET session_replication_role = 'replica';

-- ÉTAPE 3: Supprimer les tables maintenance_* (cascade pour dépendances)
-- Ces tables sont les plus susceptibles d'avoir des legacy BIGINT
DROP TABLE IF EXISTS maintenance_kpis CASCADE;
DROP TABLE IF EXISTS maintenance_contracts CASCADE;
DROP TABLE IF EXISTS maintenance_part_requests CASCADE;
DROP TABLE IF EXISTS maintenance_spare_part_stock CASCADE;
DROP TABLE IF EXISTS maintenance_spare_parts CASCADE;
DROP TABLE IF EXISTS maintenance_failure_causes CASCADE;
DROP TABLE IF EXISTS maintenance_failures CASCADE;
DROP TABLE IF EXISTS maintenance_wo_parts CASCADE;
DROP TABLE IF EXISTS maintenance_wo_labor CASCADE;
DROP TABLE IF EXISTS maintenance_wo_tasks CASCADE;
DROP TABLE IF EXISTS maintenance_work_orders CASCADE;
DROP TABLE IF EXISTS maintenance_plan_tasks CASCADE;
DROP TABLE IF EXISTS maintenance_plans CASCADE;
DROP TABLE IF EXISTS maintenance_meter_readings CASCADE;
DROP TABLE IF EXISTS maintenance_asset_meters CASCADE;
DROP TABLE IF EXISTS maintenance_asset_documents CASCADE;
DROP TABLE IF EXISTS maintenance_asset_components CASCADE;
DROP TABLE IF EXISTS maintenance_assets CASCADE;

-- ÉTAPE 4: Supprimer TOUTES les tables restantes avec PK BIGINT
DO $$
DECLARE
    r RECORD;
    drop_count INTEGER := 0;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'SUPPRESSION FORCÉE DES TABLES BIGINT RESTANTES';
    RAISE NOTICE '============================================================';

    FOR r IN (
        SELECT DISTINCT tc.table_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.columns c
            ON c.table_name = tc.table_name
            AND c.column_name = kcu.column_name
        WHERE tc.constraint_type = 'PRIMARY KEY'
        AND tc.table_schema = 'public'
        AND c.udt_name IN ('int4', 'int8', 'serial', 'bigserial')
        AND tc.table_name NOT LIKE 'pg_%'
        AND tc.table_name NOT LIKE '_migration%'
    ) LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.table_name) || ' CASCADE';
        drop_count := drop_count + 1;
        RAISE NOTICE '  [DROP] %', r.table_name;
    END LOOP;

    IF drop_count > 0 THEN
        RAISE NOTICE '';
        RAISE NOTICE 'Supprimé: % table(s) avec PK BIGINT', drop_count;
    END IF;
END $$;

-- ÉTAPE 5: Réactiver les contraintes FK
SET session_replication_role = 'origin';

-- ÉTAPE 6: Vérification finale
DO $$
DECLARE
    bigint_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO bigint_count
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.columns c
        ON c.table_name = tc.table_name
        AND c.column_name = kcu.column_name
    WHERE tc.constraint_type = 'PRIMARY KEY'
    AND tc.table_schema = 'public'
    AND c.udt_name IN ('int4', 'int8', 'serial', 'bigserial')
    AND tc.table_name NOT LIKE 'pg_%';

    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
    IF bigint_count = 0 THEN
        RAISE NOTICE 'SUCCÈS: Toutes les tables BIGINT ont été supprimées';
        RAISE NOTICE 'La base est prête pour recréation avec UUID';
    ELSE
        RAISE WARNING 'ATTENTION: % table(s) BIGINT restante(s)!', bigint_count;
    END IF;
    RAISE NOTICE '============================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'PROCHAINE ÉTAPE: Redémarrer l''application FastAPI';
    RAISE NOTICE 'Les tables seront recréées automatiquement avec UUID';
    RAISE NOTICE '============================================================';
END $$;
