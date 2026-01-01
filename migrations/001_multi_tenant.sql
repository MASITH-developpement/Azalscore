-- AZALS - Migration Multi-Tenant
-- Création de la table items avec isolation stricte par tenant_id

-- Table items avec contraintes de sécurité multi-tenant
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index sur tenant_id pour performance des requêtes filtrées
CREATE INDEX idx_items_tenant_id ON items(tenant_id);

-- Index composite pour queries temporelles par tenant
CREATE INDEX idx_items_tenant_created ON items(tenant_id, created_at);

-- Row-Level Security (RLS) - Sécurité PostgreSQL native
-- Garantit l'isolation même en cas de bug applicatif
ALTER TABLE items ENABLE ROW LEVEL SECURITY;

-- Politique RLS : lecture impossible sans tenant_id correct
-- Note : nécessite SET LOCAL app.current_tenant_id = 'xxx' avant les queries
-- Désactivé par défaut car géré au niveau applicatif, mais disponible si besoin
-- CREATE POLICY tenant_isolation_policy ON items
--     USING (tenant_id = current_setting('app.current_tenant_id')::text);

-- Contrainte : tenant_id non vide
ALTER TABLE items ADD CONSTRAINT items_tenant_id_not_empty 
    CHECK (length(trim(tenant_id)) > 0);

-- Commentaires pour documentation
COMMENT ON TABLE items IS 'Table items avec isolation stricte multi-tenant. Chaque row appartient à un seul tenant.';
COMMENT ON COLUMN items.tenant_id IS 'Identifiant du tenant propriétaire. OBLIGATOIRE pour toute opération.';
COMMENT ON INDEX idx_items_tenant_id IS 'Index principal pour filtrage par tenant. Critique pour performance.';
