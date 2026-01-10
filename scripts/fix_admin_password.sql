-- AZALS - Script SQL pour corriger le mot de passe admin
-- ========================================================
--
-- Usage avec Docker:
--   docker exec -i azals_postgres psql -U azals_user -d azals < scripts/fix_admin_password.sql
--
-- Usage avec psql direct:
--   psql -U azals_user -d azals -f scripts/fix_admin_password.sql
--
-- HASH BCRYPT pour 'admin123': $2b$12$XJy6xKFpHE3ERfOcpAIDLenQReVMSNsxwoETGG.ZK/6.yzrpuQkVe

-- Afficher l'état actuel
SELECT 'ÉTAT AVANT MISE À JOUR:' as info;
SELECT id, email, is_active, role, LEFT(password_hash, 30) as hash_preview
FROM users WHERE email = 'admin@azals.local';

-- Créer ou mettre à jour l'utilisateur admin
-- (INSERT ON CONFLICT pour gérer les deux cas)
INSERT INTO users (
    id,
    tenant_id,
    email,
    password_hash,
    role,
    is_active,
    totp_enabled,
    must_change_password,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'default',
    'admin@azals.local',
    '$2b$12$XJy6xKFpHE3ERfOcpAIDLenQReVMSNsxwoETGG.ZK/6.yzrpuQkVe',
    'DIRIGEANT',
    1,
    0,
    0,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE SET
    password_hash = '$2b$12$XJy6xKFpHE3ERfOcpAIDLenQReVMSNsxwoETGG.ZK/6.yzrpuQkVe',
    is_active = 1,
    totp_enabled = 0,
    must_change_password = 0,
    updated_at = NOW();

-- Afficher l'état après mise à jour
SELECT 'ÉTAT APRÈS MISE À JOUR:' as info;
SELECT id, email, is_active, role, LEFT(password_hash, 30) as hash_preview
FROM users WHERE email = 'admin@azals.local';

SELECT '=====================================' as separator;
SELECT 'IDENTIFIANTS DE CONNEXION:' as info;
SELECT 'Email: admin@azals.local' as identifiant;
SELECT 'Mot de passe: admin123' as identifiant;
SELECT '=====================================' as separator;
