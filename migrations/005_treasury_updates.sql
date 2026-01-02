-- Migration 005: Ajout colonnes manquantes pour Treasury
-- Version idempotente PostgreSQL/SQLite

-- Pour PostgreSQL : vérifier existence avant ajout
DO $$ 
BEGIN
    -- Ajouter user_id si n'existe pas
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'treasury_forecasts' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE treasury_forecasts ADD COLUMN user_id INTEGER;
        RAISE NOTICE 'Colonne user_id ajoutée';
    ELSE
        RAISE NOTICE 'Colonne user_id déjà présente';
    END IF;
    
    -- Ajouter red_triggered si n'existe pas
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'treasury_forecasts' AND column_name = 'red_triggered'
    ) THEN
        ALTER TABLE treasury_forecasts ADD COLUMN red_triggered INTEGER DEFAULT 0;
        RAISE NOTICE 'Colonne red_triggered ajoutée';
    ELSE
        RAISE NOTICE 'Colonne red_triggered déjà présente';
    END IF;
END $$;

-- Index (idempotent)
CREATE INDEX IF NOT EXISTS idx_treasury_red ON treasury_forecasts(tenant_id, red_triggered);
