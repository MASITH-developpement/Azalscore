-- ============================================================================
-- AZALS MODULE T1 - MIGRATION CONFIGURATION AUTOMATIQUE
-- Création des tables pour la configuration automatique par fonction
-- ============================================================================

-- Version: 1.0.0
-- Date: 2026-01-03
-- Module: T1 - Configuration Automatique

BEGIN;

-- ============================================================================
-- TABLE: autoconfig_job_profiles
-- Profils métier définissant les droits par défaut
-- ============================================================================

CREATE TABLE IF NOT EXISTS autoconfig_job_profiles (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Niveau hiérarchique
    level VARCHAR(20) NOT NULL,
    hierarchy_order INTEGER NOT NULL DEFAULT 5,

    -- Critères de matching
    title_patterns TEXT,
    department_patterns TEXT,

    -- Configuration automatique
    default_roles TEXT NOT NULL,
    default_permissions TEXT,
    default_modules TEXT,

    -- Sécurité
    max_data_access_level INTEGER NOT NULL DEFAULT 5,
    requires_mfa BOOLEAN NOT NULL DEFAULT FALSE,
    requires_training BOOLEAN NOT NULL DEFAULT TRUE,

    -- Configuration
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    priority INTEGER NOT NULL DEFAULT 100,

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    -- Contraintes
    CONSTRAINT uq_job_profile_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_job_profiles_tenant ON autoconfig_job_profiles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_job_profiles_level ON autoconfig_job_profiles(level);
CREATE INDEX IF NOT EXISTS idx_job_profiles_priority ON autoconfig_job_profiles(priority);

-- ============================================================================
-- TABLE: autoconfig_profile_assignments
-- Attribution d'un profil à un utilisateur
-- ============================================================================

CREATE TABLE IF NOT EXISTS autoconfig_profile_assignments (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    -- Relation
    user_id INTEGER NOT NULL,
    profile_id INTEGER NOT NULL REFERENCES autoconfig_job_profiles(id),

    -- Contexte
    job_title VARCHAR(200),
    department VARCHAR(200),
    manager_id INTEGER,

    -- Statut
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_auto BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER,
    revoked_at TIMESTAMP,
    revoked_by INTEGER,
    revocation_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_profile_assignments_tenant ON autoconfig_profile_assignments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_profile_assignments_user ON autoconfig_profile_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_profile_assignments_active ON autoconfig_profile_assignments(tenant_id, is_active);

-- ============================================================================
-- TABLE: autoconfig_permission_overrides
-- Ajustements de permissions
-- ============================================================================

CREATE TABLE IF NOT EXISTS autoconfig_permission_overrides (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    -- Cible
    user_id INTEGER NOT NULL,

    -- Type
    override_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',

    -- Contenu
    added_roles TEXT,
    removed_roles TEXT,
    added_permissions TEXT,
    removed_permissions TEXT,
    added_modules TEXT,
    removed_modules TEXT,

    -- Justification
    reason TEXT NOT NULL,
    business_justification TEXT,

    -- Temporalité
    starts_at TIMESTAMP,
    expires_at TIMESTAMP,

    -- Workflow
    requested_by INTEGER NOT NULL,
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_by INTEGER,
    approved_at TIMESTAMP,
    rejected_by INTEGER,
    rejected_at TIMESTAMP,
    rejection_reason TEXT,

    -- Application
    applied_at TIMESTAMP,
    revoked_at TIMESTAMP,
    revoked_by INTEGER
);

CREATE INDEX IF NOT EXISTS idx_overrides_tenant ON autoconfig_permission_overrides(tenant_id);
CREATE INDEX IF NOT EXISTS idx_overrides_user ON autoconfig_permission_overrides(user_id);
CREATE INDEX IF NOT EXISTS idx_overrides_status ON autoconfig_permission_overrides(status);
CREATE INDEX IF NOT EXISTS idx_overrides_expires ON autoconfig_permission_overrides(expires_at);

-- ============================================================================
-- TABLE: autoconfig_onboarding
-- Processus d'onboarding
-- ============================================================================

CREATE TABLE IF NOT EXISTS autoconfig_onboarding (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    -- Employé
    user_id INTEGER,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),

    -- Poste
    job_title VARCHAR(200) NOT NULL,
    department VARCHAR(200),
    manager_id INTEGER,
    start_date TIMESTAMP NOT NULL,

    -- Profil
    detected_profile_id INTEGER REFERENCES autoconfig_job_profiles(id),
    profile_override INTEGER,

    -- Statut
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    steps_completed TEXT,

    -- Notifications
    welcome_email_sent BOOLEAN NOT NULL DEFAULT FALSE,
    manager_notified BOOLEAN NOT NULL DEFAULT FALSE,
    it_notified BOOLEAN NOT NULL DEFAULT FALSE,

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_onboarding_tenant ON autoconfig_onboarding(tenant_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_status ON autoconfig_onboarding(status);
CREATE INDEX IF NOT EXISTS idx_onboarding_start ON autoconfig_onboarding(start_date);

-- ============================================================================
-- TABLE: autoconfig_offboarding
-- Processus d'offboarding
-- ============================================================================

CREATE TABLE IF NOT EXISTS autoconfig_offboarding (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    -- Employé
    user_id INTEGER NOT NULL,

    -- Départ
    departure_date TIMESTAMP NOT NULL,
    departure_type VARCHAR(50) NOT NULL,

    -- Transfert
    transfer_to_user_id INTEGER,
    transfer_notes TEXT,

    -- Statut
    status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
    steps_completed TEXT,

    -- Actions
    account_deactivated BOOLEAN NOT NULL DEFAULT FALSE,
    access_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    data_archived BOOLEAN NOT NULL DEFAULT FALSE,
    data_deleted BOOLEAN NOT NULL DEFAULT FALSE,

    -- Notifications
    manager_notified BOOLEAN NOT NULL DEFAULT FALSE,
    it_notified BOOLEAN NOT NULL DEFAULT FALSE,
    team_notified BOOLEAN NOT NULL DEFAULT FALSE,

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_offboarding_tenant ON autoconfig_offboarding(tenant_id);
CREATE INDEX IF NOT EXISTS idx_offboarding_status ON autoconfig_offboarding(status);
CREATE INDEX IF NOT EXISTS idx_offboarding_departure ON autoconfig_offboarding(departure_date);

-- ============================================================================
-- TABLE: autoconfig_rules
-- Règles de configuration personnalisables
-- ============================================================================

CREATE TABLE IF NOT EXISTS autoconfig_rules (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Configuration
    condition TEXT NOT NULL,
    action TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    -- Contraintes
    CONSTRAINT uq_autoconfig_rule_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_autoconfig_rules_tenant ON autoconfig_rules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_autoconfig_rules_priority ON autoconfig_rules(priority);

-- ============================================================================
-- TABLE: autoconfig_logs
-- Logs des actions de configuration automatique
-- ============================================================================

CREATE TABLE IF NOT EXISTS autoconfig_logs (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    -- Action
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,

    -- Cible
    user_id INTEGER,

    -- Détails
    old_values TEXT,
    new_values TEXT,
    details TEXT,

    -- Source
    source VARCHAR(50) NOT NULL,
    triggered_by INTEGER,

    -- Résultat
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,

    -- Timestamp
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_autoconfig_logs_tenant ON autoconfig_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_autoconfig_logs_action ON autoconfig_logs(action);
CREATE INDEX IF NOT EXISTS idx_autoconfig_logs_user ON autoconfig_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_autoconfig_logs_created ON autoconfig_logs(created_at);

-- ============================================================================
-- TRIGGERS: updated_at automatique
-- ============================================================================

CREATE TRIGGER IF NOT EXISTS update_job_profiles_updated_at
    BEFORE UPDATE ON autoconfig_job_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER IF NOT EXISTS update_autoconfig_rules_updated_at
    BEFORE UPDATE ON autoconfig_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;

-- ============================================================================
-- FIN MIGRATION T1 CONFIGURATION AUTOMATIQUE
-- ============================================================================
