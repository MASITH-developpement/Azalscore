-- AZALS - PostgreSQL Production Initialization
-- =============================================
-- Execute lors du premier demarrage du container PostgreSQL
-- Configure les extensions et les parametres de securite

-- Extensions necessaires
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Configuration des parametres de securite
ALTER SYSTEM SET log_connections = 'on';
ALTER SYSTEM SET log_disconnections = 'on';
ALTER SYSTEM SET log_statement = 'ddl';
ALTER SYSTEM SET log_duration = 'on';
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s

-- Performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Connexions
ALTER SYSTEM SET max_connections = 200;

-- Checkpoint tuning
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';

-- Vacuum tuning
ALTER SYSTEM SET autovacuum = 'on';
ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1;
ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05;

SELECT pg_reload_conf();

-- Schema pour isolation multi-tenant (optionnel)
-- CREATE SCHEMA IF NOT EXISTS tenant_data;
