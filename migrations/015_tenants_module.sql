-- ============================================================================
-- AZALS MODULE T9 - GESTION DES TENANTS
-- Migration: 015_tenants_module.sql
-- Date: 2026-01-03
-- ============================================================================

-- ============================================================================
-- ENUMS
-- ============================================================================

CREATE TYPE tenant_status AS ENUM (
    'PENDING', 'ACTIVE', 'SUSPENDED', 'CANCELLED', 'TRIAL'
);

CREATE TYPE subscription_plan AS ENUM (
    'STARTER', 'PROFESSIONAL', 'ENTERPRISE', 'CUSTOM'
);

CREATE TYPE billing_cycle AS ENUM (
    'MONTHLY', 'QUARTERLY', 'YEARLY'
);

CREATE TYPE module_status AS ENUM (
    'ACTIVE', 'DISABLED', 'PENDING'
);

CREATE TYPE invitation_status AS ENUM (
    'PENDING', 'ACCEPTED', 'EXPIRED', 'CANCELLED'
);


-- ============================================================================
-- TABLES
-- ============================================================================

-- Tenants (clients)
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) UNIQUE NOT NULL,

    -- Informations entreprise
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    siret VARCHAR(20),
    vat_number VARCHAR(30),

    -- Adresse
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(2) DEFAULT 'FR',

    -- Contact
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    website VARCHAR(255),

    -- Statut et plan
    status tenant_status DEFAULT 'PENDING',
    plan subscription_plan DEFAULT 'STARTER',

    -- Configuration
    timezone VARCHAR(50) DEFAULT 'Europe/Paris',
    language VARCHAR(5) DEFAULT 'fr',
    currency VARCHAR(3) DEFAULT 'EUR',
    date_format VARCHAR(20) DEFAULT 'DD/MM/YYYY',

    -- Limites
    max_users INTEGER DEFAULT 5,
    max_storage_gb INTEGER DEFAULT 10,
    storage_used_gb FLOAT DEFAULT 0,

    -- Branding
    logo_url VARCHAR(500),
    primary_color VARCHAR(7) DEFAULT '#1976D2',
    secondary_color VARCHAR(7) DEFAULT '#424242',

    -- Fonctionnalités
    features JSONB,
    metadata JSONB,

    -- Dates
    trial_ends_at TIMESTAMP,
    activated_at TIMESTAMP,
    suspended_at TIMESTAMP,
    cancelled_at TIMESTAMP,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Index tenants
CREATE INDEX idx_tenants_id ON tenants(tenant_id);
CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_plan ON tenants(plan);
CREATE INDEX idx_tenants_country ON tenants(country);


-- Abonnements
CREATE TABLE tenant_subscriptions (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Plan
    plan subscription_plan NOT NULL,
    billing_cycle billing_cycle DEFAULT 'MONTHLY',

    -- Prix
    price_monthly FLOAT,
    price_yearly FLOAT,
    discount_percent FLOAT DEFAULT 0,

    -- Période
    starts_at TIMESTAMP NOT NULL,
    ends_at TIMESTAMP,
    next_billing_at TIMESTAMP,

    -- Statut
    is_active BOOLEAN DEFAULT TRUE,
    is_trial BOOLEAN DEFAULT FALSE,
    auto_renew BOOLEAN DEFAULT TRUE,

    -- Paiement
    payment_method VARCHAR(50),
    last_payment_at TIMESTAMP,
    last_payment_amount FLOAT,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index subscriptions
CREATE INDEX idx_tenant_subscriptions_tenant ON tenant_subscriptions(tenant_id);
CREATE INDEX idx_tenant_subscriptions_active ON tenant_subscriptions(tenant_id, is_active);


-- Modules activés
CREATE TABLE tenant_modules (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Module
    module_code VARCHAR(10) NOT NULL,
    module_name VARCHAR(100),
    module_version VARCHAR(20),

    -- Statut
    status module_status DEFAULT 'ACTIVE',

    -- Configuration
    config JSONB,
    limits JSONB,

    -- Dates
    activated_at TIMESTAMP DEFAULT NOW(),
    deactivated_at TIMESTAMP,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index modules
CREATE INDEX idx_tenant_modules_tenant ON tenant_modules(tenant_id);
CREATE INDEX idx_tenant_modules_code ON tenant_modules(tenant_id, module_code);
CREATE INDEX idx_tenant_modules_status ON tenant_modules(tenant_id, status);


-- Invitations
CREATE TABLE tenant_invitations (
    id SERIAL PRIMARY KEY,

    -- Invitation
    token VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,

    -- Tenant cible
    tenant_id VARCHAR(50),
    tenant_name VARCHAR(255),
    plan subscription_plan,

    -- Rôle proposé
    proposed_role VARCHAR(50) DEFAULT 'TENANT_ADMIN',

    -- Statut
    status invitation_status DEFAULT 'PENDING',

    -- Dates
    expires_at TIMESTAMP NOT NULL,
    accepted_at TIMESTAMP,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Index invitations
CREATE INDEX idx_tenant_invitations_token ON tenant_invitations(token);
CREATE INDEX idx_tenant_invitations_email ON tenant_invitations(email);
CREATE INDEX idx_tenant_invitations_status ON tenant_invitations(status);


-- Utilisation
CREATE TABLE tenant_usage (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Période
    date TIMESTAMP NOT NULL,
    period VARCHAR(20) DEFAULT 'daily',

    -- Utilisateurs
    active_users INTEGER DEFAULT 0,
    total_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,

    -- Stockage
    storage_used_gb FLOAT DEFAULT 0,
    files_count INTEGER DEFAULT 0,

    -- API
    api_calls INTEGER DEFAULT 0,
    api_errors INTEGER DEFAULT 0,

    -- Modules
    module_usage JSONB,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index usage
CREATE INDEX idx_tenant_usage_tenant ON tenant_usage(tenant_id);
CREATE INDEX idx_tenant_usage_date ON tenant_usage(tenant_id, date);
CREATE INDEX idx_tenant_usage_period ON tenant_usage(tenant_id, period, date);


-- Événements (audit)
CREATE TABLE tenant_events (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Événement
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    description TEXT,

    -- Acteur
    actor_id INTEGER,
    actor_email VARCHAR(255),
    actor_ip VARCHAR(50),

    -- Audit
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index events
CREATE INDEX idx_tenant_events_tenant ON tenant_events(tenant_id);
CREATE INDEX idx_tenant_events_type ON tenant_events(tenant_id, event_type);
CREATE INDEX idx_tenant_events_created ON tenant_events(tenant_id, created_at DESC);


-- Paramètres
CREATE TABLE tenant_settings (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) UNIQUE NOT NULL,

    -- Sécurité
    two_factor_required BOOLEAN DEFAULT FALSE,
    session_timeout_minutes INTEGER DEFAULT 30,
    password_expiry_days INTEGER DEFAULT 90,
    ip_whitelist JSONB,

    -- Notifications
    notify_admin_on_signup BOOLEAN DEFAULT TRUE,
    notify_admin_on_error BOOLEAN DEFAULT TRUE,
    daily_digest_enabled BOOLEAN DEFAULT TRUE,

    -- Intégrations
    webhook_url VARCHAR(500),
    api_rate_limit INTEGER DEFAULT 1000,

    -- Backup
    auto_backup_enabled BOOLEAN DEFAULT TRUE,
    backup_retention_days INTEGER DEFAULT 30,

    -- Custom
    custom_settings JSONB,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index settings
CREATE INDEX idx_tenant_settings_tenant ON tenant_settings(tenant_id);


-- Onboarding
CREATE TABLE tenant_onboarding (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) UNIQUE NOT NULL,

    -- Étapes
    company_info_completed BOOLEAN DEFAULT FALSE,
    admin_created BOOLEAN DEFAULT FALSE,
    users_invited BOOLEAN DEFAULT FALSE,
    modules_configured BOOLEAN DEFAULT FALSE,
    country_pack_selected BOOLEAN DEFAULT FALSE,
    first_data_imported BOOLEAN DEFAULT FALSE,
    training_completed BOOLEAN DEFAULT FALSE,

    -- Progression
    progress_percent INTEGER DEFAULT 0,
    current_step VARCHAR(50) DEFAULT 'company_info',

    -- Dates
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    -- Audit
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index onboarding
CREATE INDEX idx_tenant_onboarding_tenant ON tenant_onboarding(tenant_id);


-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger updated_at pour tenants
CREATE TRIGGER update_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour tenant_subscriptions
CREATE TRIGGER update_tenant_subscriptions_updated_at
    BEFORE UPDATE ON tenant_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour tenant_modules
CREATE TRIGGER update_tenant_modules_updated_at
    BEFORE UPDATE ON tenant_modules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour tenant_settings
CREATE TRIGGER update_tenant_settings_updated_at
    BEFORE UPDATE ON tenant_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour tenant_onboarding
CREATE TRIGGER update_tenant_onboarding_updated_at
    BEFORE UPDATE ON tenant_onboarding
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- DONNÉES INITIALES - Premier tenant SAS MASITH
-- ============================================================================

-- Créer le tenant MASITH
INSERT INTO tenants (
    tenant_id,
    name,
    legal_name,
    siret,
    country,
    email,
    status,
    plan,
    max_users,
    max_storage_gb,
    created_by
) VALUES (
    'masith',
    'SAS MASITH',
    'SAS MASITH',
    '12345678901234',
    'FR',
    'admin@masith.fr',
    'ACTIVE',
    'ENTERPRISE',
    50,
    100,
    'system'
);

-- Paramètres du tenant MASITH
INSERT INTO tenant_settings (
    tenant_id,
    two_factor_required,
    session_timeout_minutes,
    notify_admin_on_signup,
    auto_backup_enabled
) VALUES (
    'masith',
    FALSE,
    60,
    TRUE,
    TRUE
);

-- Onboarding du tenant MASITH (partiellement complété)
INSERT INTO tenant_onboarding (
    tenant_id,
    company_info_completed,
    admin_created,
    modules_configured,
    country_pack_selected,
    progress_percent,
    current_step
) VALUES (
    'masith',
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    57,
    'users'
);

-- Modules activés pour MASITH (tous les transverses)
INSERT INTO tenant_modules (tenant_id, module_code, module_name, status) VALUES
    ('masith', 'T0', 'IAM - Gestion Utilisateurs', 'ACTIVE'),
    ('masith', 'T1', 'Configuration Automatique', 'ACTIVE'),
    ('masith', 'T2', 'Déclencheurs & Diffusion', 'ACTIVE'),
    ('masith', 'T3', 'Audit & Benchmark', 'ACTIVE'),
    ('masith', 'T4', 'Contrôle Qualité', 'ACTIVE'),
    ('masith', 'T5', 'Packs Pays', 'ACTIVE'),
    ('masith', 'T6', 'Diffusion Périodique', 'ACTIVE'),
    ('masith', 'T7', 'Module Web', 'ACTIVE'),
    ('masith', 'T8', 'Site Web Officiel', 'ACTIVE');

-- Abonnement MASITH
INSERT INTO tenant_subscriptions (
    tenant_id,
    plan,
    billing_cycle,
    starts_at,
    is_active,
    is_trial,
    auto_renew
) VALUES (
    'masith',
    'ENTERPRISE',
    'YEARLY',
    NOW(),
    TRUE,
    FALSE,
    TRUE
);

-- Événement de création
INSERT INTO tenant_events (
    tenant_id,
    event_type,
    event_data,
    description,
    actor_email
) VALUES (
    'masith',
    'tenant.created',
    '{"name": "SAS MASITH", "plan": "ENTERPRISE"}'::jsonb,
    'Création du tenant SAS MASITH - Premier client AZALS',
    'system'
);


-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE tenants IS 'Tenants (clients) de la plateforme AZALS';
COMMENT ON TABLE tenant_subscriptions IS 'Abonnements des tenants';
COMMENT ON TABLE tenant_modules IS 'Modules activés par tenant';
COMMENT ON TABLE tenant_invitations IS 'Invitations à rejoindre un tenant';
COMMENT ON TABLE tenant_usage IS 'Utilisation des ressources par tenant';
COMMENT ON TABLE tenant_events IS 'Journal des événements tenant (audit)';
COMMENT ON TABLE tenant_settings IS 'Paramètres avancés des tenants';
COMMENT ON TABLE tenant_onboarding IS 'Progression de l''onboarding des tenants';
