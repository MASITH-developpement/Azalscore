-- Migration 004: Table Trésorerie
-- Prévisions de trésorerie avec déclenchement RED

CREATE TABLE IF NOT EXISTS treasury_forecasts (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    opening_balance INTEGER NOT NULL,
    inflows INTEGER NOT NULL,
    outflows INTEGER NOT NULL,
    forecast_balance INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Index pour isolation tenant
CREATE INDEX IF NOT EXISTS idx_treasury_tenant ON treasury_forecasts(tenant_id);

-- Index pour récupération chronologique
CREATE INDEX IF NOT EXISTS idx_treasury_created ON treasury_forecasts(created_at DESC);

-- Index composite pour requêtes optimales
CREATE INDEX IF NOT EXISTS idx_treasury_tenant_created ON treasury_forecasts(tenant_id, created_at DESC);
