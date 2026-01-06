-- AZALS - Migration 2FA pour table users
-- Ajout des colonnes TOTP pour authentification à deux facteurs

-- Ajouter les colonnes 2FA si elles n'existent pas
DO $$
BEGIN
    -- totp_secret : Secret TOTP encodé base32
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'users' AND column_name = 'totp_secret') THEN
        ALTER TABLE users ADD COLUMN totp_secret VARCHAR(32) NULL;
    END IF;

    -- totp_enabled : 0=disabled, 1=enabled
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'users' AND column_name = 'totp_enabled') THEN
        ALTER TABLE users ADD COLUMN totp_enabled INTEGER NOT NULL DEFAULT 0;
    END IF;

    -- totp_verified_at : Date première vérification
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'users' AND column_name = 'totp_verified_at') THEN
        ALTER TABLE users ADD COLUMN totp_verified_at TIMESTAMP NULL;
    END IF;

    -- backup_codes : Codes de secours JSON
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'users' AND column_name = 'backup_codes') THEN
        ALTER TABLE users ADD COLUMN backup_codes TEXT NULL;
    END IF;
END $$;

-- Commentaires
COMMENT ON COLUMN users.totp_secret IS 'Secret TOTP encodé base32 pour 2FA';
COMMENT ON COLUMN users.totp_enabled IS '2FA activé (1) ou désactivé (0)';
COMMENT ON COLUMN users.totp_verified_at IS 'Date de première vérification 2FA';
COMMENT ON COLUMN users.backup_codes IS 'Codes de secours 2FA en JSON';
