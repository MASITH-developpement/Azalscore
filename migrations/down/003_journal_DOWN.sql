-- AZALS - ROLLBACK Migration JOURNAL
-- Annule la creation du journal APPEND-ONLY avec protections UPDATE/DELETE

DO $$
BEGIN
    -- Drop triggers first (prevent_update and prevent_delete)
    DROP TRIGGER IF EXISTS trigger_prevent_journal_update ON journal_entries;
    DROP TRIGGER IF EXISTS trigger_prevent_journal_delete ON journal_entries;

    -- Drop functions
    DROP FUNCTION IF EXISTS prevent_journal_update();
    DROP FUNCTION IF EXISTS prevent_journal_delete();

    -- Drop indexes
    DROP INDEX IF EXISTS idx_journal_tenant_id;
    DROP INDEX IF EXISTS idx_journal_user_id;
    DROP INDEX IF EXISTS idx_journal_tenant_user;
    DROP INDEX IF EXISTS idx_journal_created_at;

    -- Drop the table
    DROP TABLE IF EXISTS journal_entries CASCADE;

    RAISE NOTICE 'Migration 003_journal rolled back successfully';
END $$;
