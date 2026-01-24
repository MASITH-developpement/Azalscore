# AZALS - Scripts de Rollback des Migrations

Ce répertoire contient les scripts DOWN (rollback) pour chaque migration UP.

## Convention de nommage

- UP: `XXX_nom_module.sql`
- DOWN: `XXX_nom_module_DOWN.sql`

## Utilisation

```bash
# Rollback une migration spécifique
psql -d azals -f migrations/down/XXX_nom_module_DOWN.sql

# Rollback multiple (ordre inverse!)
psql -d azals -f migrations/down/003_journal_DOWN.sql
psql -d azals -f migrations/down/002_auth_DOWN.sql
psql -d azals -f migrations/down/001_multi_tenant_DOWN.sql
```

## ATTENTION

1. **Perte de données**: Les rollbacks suppriment des tables et leurs données
2. **Ordre**: Toujours exécuter dans l'ordre INVERSE des migrations UP
3. **Backup**: TOUJOURS faire un backup avant rollback en production
4. **Test**: Tester en staging AVANT production

## Template de rollback

```sql
-- AZALS - ROLLBACK Migration [NOM]
-- Annule [DESCRIPTION]
-- ATTENTION: [AVERTISSEMENTS]

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'TABLE_NAME') THEN
        -- Supprimer les politiques RLS
        DROP POLICY IF EXISTS policy_name ON table_name;

        -- Supprimer les triggers
        DROP TRIGGER IF EXISTS trigger_name ON table_name;

        -- Supprimer les fonctions
        DROP FUNCTION IF EXISTS function_name();

        -- Supprimer les contraintes
        ALTER TABLE table_name DROP CONSTRAINT IF EXISTS constraint_name;

        -- Supprimer les index
        DROP INDEX IF EXISTS index_name;

        -- Supprimer la table
        DROP TABLE table_name;

        RAISE NOTICE 'Migration XXX_name rolled back successfully';
    ELSE
        RAISE NOTICE 'Table table_name does not exist, nothing to rollback';
    END IF;
END $$;
```

## État des rollbacks

| Migration | DOWN créé | Testé |
|-----------|-----------|-------|
| 001_multi_tenant | ✅ | ❌ |
| 002_auth | ✅ | ❌ |
| 003_journal | ❌ | ❌ |
| ... | ❌ | ❌ |

## TODO P0-5

Créer les scripts DOWN pour toutes les migrations avant mise en production.
Priorité haute: migrations 003-010 (core modules).
