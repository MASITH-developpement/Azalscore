-- Migration 005: Ajout colonnes manquantes pour Treasury
-- Ajout user_id et red_triggered

-- Ajouter user_id (nullable temporairement pour données existantes)
ALTER TABLE treasury_forecasts ADD COLUMN user_id INTEGER;

-- Ajouter red_triggered (INTEGER pour compatibilité SQLite: 0=False, 1=True)
ALTER TABLE treasury_forecasts ADD COLUMN red_triggered INTEGER DEFAULT 0;

-- Index sur red_triggered
CREATE INDEX IF NOT EXISTS idx_treasury_red ON treasury_forecasts(tenant_id, red_triggered);
