-- AZALS - ROLLBACK Migration TREASURY UPDATES
-- Annule l'ajout des colonnes user_id et red_triggered sur treasury_forecasts

DO $$
BEGIN
    -- Drop index first
    DROP INDEX IF EXISTS idx_treasury_red;

    -- Drop columns if they exist
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'treasury_forecasts' AND column_name = 'red_triggered'
    ) THEN
        ALTER TABLE treasury_forecasts DROP COLUMN red_triggered;
        RAISE NOTICE 'Colonne red_triggered supprimee';
    ELSE
        RAISE NOTICE 'Colonne red_triggered inexistante';
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'treasury_forecasts' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE treasury_forecasts DROP COLUMN user_id;
        RAISE NOTICE 'Colonne user_id supprimee';
    ELSE
        RAISE NOTICE 'Colonne user_id inexistante';
    END IF;

    RAISE NOTICE 'Migration 005_treasury_updates rolled back successfully';
END $$;
