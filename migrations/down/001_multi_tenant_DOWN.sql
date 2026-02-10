-- AZALS - ROLLBACK Migration Multi-Tenant
-- Annule la création de la table items
-- ATTENTION: Perte de données si table contient des enregistrements!

-- Vérifier que la table existe avant suppression
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'items') THEN
        -- Supprimer les politiques RLS si existantes
        DROP POLICY IF EXISTS tenant_isolation_policy ON items;

        -- Supprimer les contraintes
        ALTER TABLE items DROP CONSTRAINT IF EXISTS items_tenant_id_not_empty;

        -- Supprimer les index
        DROP INDEX IF EXISTS idx_items_tenant_created;
        DROP INDEX IF EXISTS idx_items_tenant_id;

        -- Désactiver RLS
        ALTER TABLE items DISABLE ROW LEVEL SECURITY;

        -- Supprimer la table
        DROP TABLE items;

        RAISE NOTICE 'Migration 001_multi_tenant rolled back successfully';
    ELSE
        RAISE NOTICE 'Table items does not exist, nothing to rollback';
    END IF;
END $$;
