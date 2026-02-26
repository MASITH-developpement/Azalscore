-- Migration: Add profile fields to users table
-- Date: 2026-02-26
-- Description: Adds name, phone, photo, and api_token columns to users table

-- Add name column
ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(200) NULL;

-- Add phone column
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50) NULL;

-- Add photo column (for base64 or URL)
ALTER TABLE users ADD COLUMN IF NOT EXISTS photo TEXT NULL;

-- Add api_token column with index
ALTER TABLE users ADD COLUMN IF NOT EXISTS api_token VARCHAR(255) NULL;
CREATE INDEX IF NOT EXISTS idx_users_api_token ON users(api_token);

-- Verify columns were added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
AND column_name IN ('name', 'phone', 'photo', 'api_token');
