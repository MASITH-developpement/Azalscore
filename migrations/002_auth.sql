-- AZALS - Migration Authentification
-- Création de la table users avec isolation multi-tenant

-- Table users : authentification avec isolation par tenant
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'DIRIGEANT',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index sur tenant_id pour isolation
CREATE INDEX idx_users_tenant_id ON users(tenant_id);

-- Index sur email pour login rapide
CREATE INDEX idx_users_email ON users(email);

-- Index composite pour requêtes tenant + email
CREATE INDEX idx_users_tenant_email ON users(tenant_id, email);

-- Contrainte : tenant_id non vide
ALTER TABLE users ADD CONSTRAINT users_tenant_id_not_empty 
    CHECK (length(trim(tenant_id)) > 0);

-- Contrainte : email non vide et format basique
ALTER TABLE users ADD CONSTRAINT users_email_not_empty 
    CHECK (length(trim(email)) > 0 AND email LIKE '%@%');

-- Contrainte : role valide
ALTER TABLE users ADD CONSTRAINT users_role_valid 
    CHECK (role IN ('DIRIGEANT'));

-- Contrainte : is_active booléen (0 ou 1)
ALTER TABLE users ADD CONSTRAINT users_is_active_bool 
    CHECK (is_active IN (0, 1));

-- Commentaires pour documentation
COMMENT ON TABLE users IS 'Utilisateurs avec authentification JWT et isolation multi-tenant stricte.';
COMMENT ON COLUMN users.tenant_id IS 'Identifiant du tenant. Un user appartient à UN SEUL tenant.';
COMMENT ON COLUMN users.email IS 'Email unique pour login.';
COMMENT ON COLUMN users.password_hash IS 'Hash bcrypt du mot de passe.';
COMMENT ON COLUMN users.role IS 'Rôle utilisateur. Pour l''instant uniquement DIRIGEANT.';
COMMENT ON COLUMN users.is_active IS 'Compte actif (1) ou désactivé (0).';
