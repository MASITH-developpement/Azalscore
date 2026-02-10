-- AZALS - ROLLBACK Migration TREASURY
-- Annule la creation de la table treasury_forecasts pour previsions de tresorerie

DO $$
BEGIN
    -- Drop indexes
    DROP INDEX IF EXISTS idx_treasury_tenant;
    DROP INDEX IF EXISTS idx_treasury_created;
    DROP INDEX IF EXISTS idx_treasury_tenant_created;

    -- Drop the table
    DROP TABLE IF EXISTS treasury_forecasts CASCADE;

    RAISE NOTICE 'Migration 004_treasury rolled back successfully';
END $$;
