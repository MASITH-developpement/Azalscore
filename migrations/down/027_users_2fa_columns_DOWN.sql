-- AZALS - ROLLBACK Migration 2FA Columns
-- Annule l'ajout des colonnes 2FA sur la table users

DO $$
BEGIN
    -- Drop comments first
    COMMENT ON COLUMN users.totp_secret IS NULL;
    COMMENT ON COLUMN users.totp_enabled IS NULL;
    COMMENT ON COLUMN users.totp_verified_at IS NULL;
    COMMENT ON COLUMN users.backup_codes IS NULL;

    -- Drop columns if they exist
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'users' AND column_name = 'backup_codes') THEN
        ALTER TABLE users DROP COLUMN backup_codes;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'users' AND column_name = 'totp_verified_at') THEN
        ALTER TABLE users DROP COLUMN totp_verified_at;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'users' AND column_name = 'totp_enabled') THEN
        ALTER TABLE users DROP COLUMN totp_enabled;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'users' AND column_name = 'totp_secret') THEN
        ALTER TABLE users DROP COLUMN totp_secret;
    END IF;

    RAISE NOTICE 'Migration 027_users_2fa_columns rolled back successfully';
END $$;
