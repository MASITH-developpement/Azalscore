#!/bin/bash
# ============================================================================
# AZALSCORE - Initialisation PostgreSQL pour Docker
# ============================================================================
# Ce script est exécuté automatiquement lors du premier démarrage de PostgreSQL

set -e

echo "=== Initialisation AZALSCORE PostgreSQL ==="

# Créer les extensions nécessaires
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Extension UUID
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    -- Extension crypto
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";

    -- Extension pour les index avancés (optionnel)
    CREATE EXTENSION IF NOT EXISTS "btree_gin";

    -- Afficher les extensions installées
    SELECT extname, extversion FROM pg_extension;
EOSQL

echo "=== Extensions PostgreSQL installées ==="

# Optimisations pour la production
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Créer un schéma dédié si nécessaire
    CREATE SCHEMA IF NOT EXISTS azals;

    -- Accorder les permissions
    GRANT ALL ON SCHEMA azals TO $POSTGRES_USER;
    GRANT ALL ON ALL TABLES IN SCHEMA azals TO $POSTGRES_USER;
    ALTER DEFAULT PRIVILEGES IN SCHEMA azals GRANT ALL ON TABLES TO $POSTGRES_USER;

    -- Afficher la configuration
    SHOW server_version;
EOSQL

echo "=== Configuration AZALSCORE terminée ==="
