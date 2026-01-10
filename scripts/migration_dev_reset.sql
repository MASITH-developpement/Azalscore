-- ============================================================================
-- AZALS - SCRIPT DE MIGRATION DEV/TEST
-- ============================================================================
-- ENVIRONNEMENT: Développement / Test (base jetable)
-- ACTION: DROP CASCADE + Recréation propre
-- ATTENTION: DÉTRUIT TOUTES LES DONNÉES
-- ============================================================================

-- 1. ACTIVER LES EXTENSIONS REQUISES
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Vérification
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pgcrypto') THEN
        RAISE EXCEPTION 'Extension pgcrypto non disponible';
    END IF;
    RAISE NOTICE 'Extensions pgcrypto et uuid-ossp activées';
END $$;

-- 2. SUPPRIMER TOUTES LES TABLES (ordre inverse des FK)
-- ============================================================================
-- Désactiver les contraintes FK temporairement pour un DROP propre
SET session_replication_role = 'replica';

-- Drop toutes les tables du schéma public
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename NOT LIKE 'pg_%'
        ORDER BY tablename
    ) LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
        RAISE NOTICE 'Dropped: %', r.tablename;
    END LOOP;
END $$;

-- Réactiver les contraintes FK
SET session_replication_role = 'origin';

-- 3. VÉRIFICATION POST-SUPPRESSION
-- ============================================================================
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM pg_tables
    WHERE schemaname = 'public'
    AND tablename NOT LIKE 'pg_%';

    IF table_count > 0 THEN
        RAISE WARNING 'Tables restantes: %', table_count;
    ELSE
        RAISE NOTICE 'Base nettoyée - 0 tables restantes';
    END IF;
END $$;

-- 4. MESSAGE FINAL
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'RESET DEV TERMINÉ';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'La base est vide et prête pour create_all()';
    RAISE NOTICE 'Extensions UUID activées: pgcrypto, uuid-ossp';
    RAISE NOTICE '';
    RAISE NOTICE 'Prochaine étape: Redémarrer l application FastAPI';
    RAISE NOTICE 'Les tables seront créées automatiquement avec UUID';
    RAISE NOTICE '============================================================';
END $$;
