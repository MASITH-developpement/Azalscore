-- AZALS - ROLLBACK Migration Audit Hash Chain
-- Annule l'ajout du hash chaine cryptographique pour le journal d'audit

DO $$
BEGIN
    -- Drop trigger first
    DROP TRIGGER IF EXISTS trigger_calculate_journal_hash ON journal_entries;

    -- Drop functions
    DROP FUNCTION IF EXISTS verify_journal_integrity(VARCHAR);
    DROP FUNCTION IF EXISTS calculate_journal_hash();

    -- Drop indexes for hash columns
    DROP INDEX IF EXISTS idx_journal_previous_hash;
    DROP INDEX IF EXISTS idx_journal_entry_hash;

    -- Drop columns added to journal_entries
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'journal_entries' AND column_name = 'entry_hash') THEN
        ALTER TABLE journal_entries DROP COLUMN entry_hash;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'journal_entries' AND column_name = 'previous_hash') THEN
        ALTER TABLE journal_entries DROP COLUMN previous_hash;
    END IF;

    RAISE NOTICE 'Migration 030_audit_hash_chain rolled back successfully';
END $$;
