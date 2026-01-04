-- ============================================================================
-- AZALS MODULE T0 - MIGRATION IAM
-- Création des tables pour la gestion des identités et accès
-- ============================================================================

-- Version: 1.0.0
-- Date: 2026-01-03
-- Module: T0 - IAM

BEGIN;

-- ============================================================================
-- TABLE: iam_users
-- Utilisateurs avec profil étendu
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_users (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    -- Identifiants
    email VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,

    -- Profil
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(200),
    phone VARCHAR(50),
    avatar_url VARCHAR(500),
    locale VARCHAR(10) NOT NULL DEFAULT 'fr',
    timezone VARCHAR(50) NOT NULL DEFAULT 'Europe/Paris',

    -- Fonction/Poste
    job_title VARCHAR(200),
    department VARCHAR(200),
    employee_id VARCHAR(50),

    -- Statut
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    lock_reason VARCHAR(500),
    locked_at TIMESTAMP,
    locked_until TIMESTAMP,

    -- Sécurité
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    last_failed_login TIMESTAMP,
    password_changed_at TIMESTAMP,
    must_change_password BOOLEAN NOT NULL DEFAULT FALSE,

    -- MFA
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_type VARCHAR(20),
    mfa_secret VARCHAR(255),
    mfa_backup_codes TEXT,

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    last_login_at TIMESTAMP,
    last_login_ip VARCHAR(50),

    -- Contraintes
    CONSTRAINT uq_iam_user_tenant_email UNIQUE (tenant_id, email)
);

CREATE INDEX IF NOT EXISTS idx_iam_users_tenant ON iam_users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_iam_users_email ON iam_users(email);
CREATE INDEX IF NOT EXISTS idx_iam_users_active ON iam_users(tenant_id, is_active);

-- ============================================================================
-- TABLE: iam_roles
-- Rôles avec hiérarchie
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_roles (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Hiérarchie
    level INTEGER NOT NULL DEFAULT 5,
    parent_id INTEGER REFERENCES iam_roles(id) ON DELETE SET NULL,

    -- Configuration
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_assignable BOOLEAN NOT NULL DEFAULT TRUE,
    max_users INTEGER,

    -- Séparation des pouvoirs
    incompatible_roles TEXT,
    requires_approval BOOLEAN NOT NULL DEFAULT FALSE,

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    -- Contraintes
    CONSTRAINT uq_iam_role_tenant_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_iam_roles_tenant ON iam_roles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_iam_roles_code ON iam_roles(code);
CREATE INDEX IF NOT EXISTS idx_iam_roles_level ON iam_roles(level);

-- ============================================================================
-- TABLE: iam_permissions
-- Permissions granulaires
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_permissions (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    -- Identification
    code VARCHAR(200) NOT NULL,
    module VARCHAR(50) NOT NULL,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(20) NOT NULL,

    -- Métadonnées
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Configuration
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_dangerous BOOLEAN NOT NULL DEFAULT FALSE,

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Contraintes
    CONSTRAINT uq_iam_permission_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_iam_permissions_tenant ON iam_permissions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_iam_permissions_module ON iam_permissions(module);
CREATE INDEX IF NOT EXISTS idx_iam_permissions_code ON iam_permissions(code);

-- ============================================================================
-- TABLE: iam_groups
-- Groupes d'utilisateurs
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_groups (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Configuration
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    -- Contraintes
    CONSTRAINT uq_iam_group_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_iam_groups_tenant ON iam_groups(tenant_id);

-- ============================================================================
-- TABLE: iam_user_roles
-- Association utilisateurs <-> rôles
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_user_roles (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES iam_users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES iam_roles(id) ON DELETE CASCADE,
    granted_by INTEGER REFERENCES iam_users(id),
    granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Contraintes
    CONSTRAINT uq_user_role_tenant UNIQUE (tenant_id, user_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_user_roles_tenant ON iam_user_roles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_user ON iam_user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON iam_user_roles(role_id);

-- ============================================================================
-- TABLE: iam_role_permissions
-- Association rôles <-> permissions
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_role_permissions (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL REFERENCES iam_roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES iam_permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Contraintes
    CONSTRAINT uq_role_permission_tenant UNIQUE (tenant_id, role_id, permission_id)
);

CREATE INDEX IF NOT EXISTS idx_role_permissions_tenant ON iam_role_permissions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON iam_role_permissions(role_id);

-- ============================================================================
-- TABLE: iam_user_groups
-- Association utilisateurs <-> groupes
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_user_groups (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES iam_users(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES iam_groups(id) ON DELETE CASCADE,
    added_by INTEGER REFERENCES iam_users(id),
    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Contraintes
    CONSTRAINT uq_user_group_tenant UNIQUE (tenant_id, user_id, group_id)
);

CREATE INDEX IF NOT EXISTS idx_user_groups_tenant ON iam_user_groups(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_groups_user ON iam_user_groups(user_id);
CREATE INDEX IF NOT EXISTS idx_user_groups_group ON iam_user_groups(group_id);

-- ============================================================================
-- TABLE: iam_group_roles
-- Association groupes <-> rôles
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_group_roles (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    group_id INTEGER NOT NULL REFERENCES iam_groups(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES iam_roles(id) ON DELETE CASCADE,
    granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Contraintes
    CONSTRAINT uq_group_role_tenant UNIQUE (tenant_id, group_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_group_roles_tenant ON iam_group_roles(tenant_id);

-- ============================================================================
-- TABLE: iam_sessions
-- Sessions utilisateurs
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_sessions (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES iam_users(id) ON DELETE CASCADE,

    -- Token
    token_jti VARCHAR(100) NOT NULL UNIQUE,
    refresh_token_hash VARCHAR(255),

    -- Contexte
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    device_info TEXT,

    -- Statut
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP,
    revoked_reason VARCHAR(200)
);

CREATE INDEX IF NOT EXISTS idx_iam_sessions_tenant ON iam_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_iam_sessions_user ON iam_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_iam_sessions_token ON iam_sessions(token_jti);
CREATE INDEX IF NOT EXISTS idx_iam_sessions_status ON iam_sessions(status);
CREATE INDEX IF NOT EXISTS idx_iam_sessions_expires ON iam_sessions(expires_at);

-- ============================================================================
-- TABLE: iam_token_blacklist
-- Liste noire des tokens révoqués
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_token_blacklist (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    token_jti VARCHAR(100) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    blacklisted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    reason VARCHAR(200)
);

CREATE INDEX IF NOT EXISTS idx_token_blacklist_jti ON iam_token_blacklist(token_jti);
CREATE INDEX IF NOT EXISTS idx_token_blacklist_expires ON iam_token_blacklist(expires_at);

-- ============================================================================
-- TABLE: iam_invitations
-- Invitations utilisateurs
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_invitations (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    -- Destinataire
    email VARCHAR(255) NOT NULL,

    -- Token
    token VARCHAR(255) NOT NULL UNIQUE,

    -- Configuration
    roles_to_assign TEXT,
    groups_to_assign TEXT,

    -- Statut
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    invited_by INTEGER NOT NULL,
    accepted_at TIMESTAMP,
    accepted_user_id INTEGER
);

CREATE INDEX IF NOT EXISTS idx_iam_invitations_tenant ON iam_invitations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_iam_invitations_email ON iam_invitations(email);
CREATE INDEX IF NOT EXISTS idx_iam_invitations_token ON iam_invitations(token);
CREATE INDEX IF NOT EXISTS idx_iam_invitations_status ON iam_invitations(status);

-- ============================================================================
-- TABLE: iam_password_policies
-- Politique de mot de passe par tenant
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_password_policies (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL UNIQUE,

    -- Complexité
    min_length INTEGER NOT NULL DEFAULT 12,
    require_uppercase BOOLEAN NOT NULL DEFAULT TRUE,
    require_lowercase BOOLEAN NOT NULL DEFAULT TRUE,
    require_numbers BOOLEAN NOT NULL DEFAULT TRUE,
    require_special BOOLEAN NOT NULL DEFAULT TRUE,

    -- Historique
    password_history_count INTEGER NOT NULL DEFAULT 5,

    -- Expiration
    password_expires_days INTEGER NOT NULL DEFAULT 90,

    -- Verrouillage
    max_failed_attempts INTEGER NOT NULL DEFAULT 5,
    lockout_duration_minutes INTEGER NOT NULL DEFAULT 30,

    -- Audit
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER
);

-- ============================================================================
-- TABLE: iam_password_history
-- Historique des mots de passe
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_password_history (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_password_history_user ON iam_password_history(tenant_id, user_id);

-- ============================================================================
-- TABLE: iam_audit_logs
-- Logs d'audit IAM
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_audit_logs (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    -- Action
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,

    -- Acteur
    actor_id INTEGER,
    actor_ip VARCHAR(50),
    actor_user_agent VARCHAR(500),

    -- Détails
    old_values TEXT,
    new_values TEXT,
    details TEXT,

    -- Résultat
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,

    -- Timestamp
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_iam_audit_tenant ON iam_audit_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_iam_audit_action ON iam_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_iam_audit_entity ON iam_audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_iam_audit_actor ON iam_audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_iam_audit_created ON iam_audit_logs(created_at);

-- ============================================================================
-- TABLE: iam_rate_limits
-- Rate limiting
-- ============================================================================

CREATE TABLE IF NOT EXISTS iam_rate_limits (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL,
    count INTEGER NOT NULL DEFAULT 1,
    window_start TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    blocked_until TIMESTAMP,

    -- Contraintes
    CONSTRAINT uq_rate_limit_key_action UNIQUE (key, action)
);

CREATE INDEX IF NOT EXISTS idx_rate_limit_key ON iam_rate_limits(key);
CREATE INDEX IF NOT EXISTS idx_rate_limit_blocked ON iam_rate_limits(blocked_until);

-- ============================================================================
-- TRIGGERS: updated_at automatique
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_iam_users_updated_at
    BEFORE UPDATE ON iam_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_iam_roles_updated_at
    BEFORE UPDATE ON iam_roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_iam_groups_updated_at
    BEFORE UPDATE ON iam_groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- CLEANUP: Suppression automatique des tokens expirés
-- ============================================================================

CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    DELETE FROM iam_token_blacklist WHERE expires_at < CURRENT_TIMESTAMP;
    DELETE FROM iam_sessions WHERE expires_at < CURRENT_TIMESTAMP AND status != 'ACTIVE';
    DELETE FROM iam_invitations WHERE expires_at < CURRENT_TIMESTAMP AND status = 'PENDING';
    DELETE FROM iam_rate_limits WHERE blocked_until < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Commentaire pour exécution périodique (cron ou scheduler)
-- SELECT cleanup_expired_tokens();

COMMIT;

-- ============================================================================
-- FIN MIGRATION T0 IAM
-- ============================================================================
