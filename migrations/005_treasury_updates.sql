-- Migration 005: Ajout colonnes manquantes pour Treasury
-- Ajout user_id et red_triggered

-- Ajouter user_id (nullable temporairement pour données existantes)
ALTER TABLE treasury_forecasts 
ADD COLUMN IF NOT EXISTS user_id INTEGER;

-- Ajouter red_triggered
ALTER TABLE treasury_forecasts 
ADD COLUMN IF NOT EXISTS red_triggered BOOLEAN DEFAULT FALSE;

-- Ajouter la foreign key sur user_id
ALTER TABLE treasury_forecasts 
ADD CONSTRAINT fk_treasury_user 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Index sur red_triggered
CREATE INDEX IF NOT EXISTS idx_treasury_red ON treasury_forecasts(tenant_id, red_triggered);
