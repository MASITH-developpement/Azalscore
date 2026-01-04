-- ============================================================================
-- AZALS MODULE T7 - MODULE WEB TRANSVERSE
-- Migration: 013_web_module.sql
-- Description: Tables pour la configuration des composants web
-- ============================================================================

-- ============================================================================
-- ENUMS
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE theme_mode AS ENUM (
        'LIGHT', 'DARK', 'SYSTEM', 'HIGH_CONTRAST'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE widget_type AS ENUM (
        'KPI', 'CHART', 'TABLE', 'LIST', 'CALENDAR', 'MAP', 'GAUGE', 'TIMELINE', 'CUSTOM'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE widget_size AS ENUM (
        'SMALL', 'MEDIUM', 'LARGE', 'WIDE', 'TALL', 'FULL'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE component_category AS ENUM (
        'LAYOUT', 'NAVIGATION', 'FORMS', 'DATA_DISPLAY', 'FEEDBACK', 'CHARTS', 'ACTIONS'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE menu_type AS ENUM (
        'MAIN', 'SIDEBAR', 'TOOLBAR', 'CONTEXT', 'FOOTER'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE page_type AS ENUM (
        'DASHBOARD', 'LIST', 'FORM', 'DETAIL', 'REPORT', 'CUSTOM'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- TABLE: THÈMES
-- ============================================================================

CREATE TABLE IF NOT EXISTS web_themes (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Mode de base
    mode theme_mode DEFAULT 'LIGHT',

    -- Couleurs principales
    primary_color VARCHAR(20) DEFAULT '#1976D2',
    secondary_color VARCHAR(20) DEFAULT '#424242',
    accent_color VARCHAR(20) DEFAULT '#82B1FF',
    error_color VARCHAR(20) DEFAULT '#FF5252',
    warning_color VARCHAR(20) DEFAULT '#FB8C00',
    success_color VARCHAR(20) DEFAULT '#4CAF50',
    info_color VARCHAR(20) DEFAULT '#2196F3',

    -- Couleurs de fond
    background_color VARCHAR(20) DEFAULT '#FFFFFF',
    surface_color VARCHAR(20) DEFAULT '#FAFAFA',
    card_color VARCHAR(20) DEFAULT '#FFFFFF',

    -- Couleurs de texte
    text_primary VARCHAR(20) DEFAULT '#212121',
    text_secondary VARCHAR(20) DEFAULT '#757575',
    text_disabled VARCHAR(20) DEFAULT '#9E9E9E',

    -- Typographie
    font_family VARCHAR(200) DEFAULT '''Roboto'', sans-serif',
    font_size_base VARCHAR(10) DEFAULT '14px',

    -- Bordures et ombres
    border_radius VARCHAR(10) DEFAULT '4px',
    box_shadow VARCHAR(200),

    -- Configuration complète
    full_config JSONB,

    -- État
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    is_system BOOLEAN DEFAULT false,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    CONSTRAINT uq_web_themes_tenant_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS ix_web_themes_tenant ON web_themes(tenant_id);
CREATE INDEX IF NOT EXISTS ix_web_themes_default ON web_themes(tenant_id, is_default);

-- ============================================================================
-- TABLE: WIDGETS
-- ============================================================================

CREATE TABLE IF NOT EXISTS web_widgets (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Type et taille
    widget_type widget_type NOT NULL,
    default_size widget_size DEFAULT 'MEDIUM',

    -- Source de données
    data_source VARCHAR(200),
    data_query JSONB,
    refresh_interval INTEGER DEFAULT 60,

    -- Configuration affichage
    display_config JSONB,
    chart_config JSONB,

    -- Permissions
    required_permission VARCHAR(100),
    visible_roles JSONB,

    -- État
    is_active BOOLEAN DEFAULT true,
    is_system BOOLEAN DEFAULT false,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    CONSTRAINT uq_web_widgets_tenant_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS ix_web_widgets_tenant ON web_widgets(tenant_id);
CREATE INDEX IF NOT EXISTS ix_web_widgets_type ON web_widgets(tenant_id, widget_type);

-- ============================================================================
-- TABLE: DASHBOARDS
-- ============================================================================

CREATE TABLE IF NOT EXISTS web_dashboards (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Type et layout
    page_type page_type DEFAULT 'DASHBOARD',
    layout_type VARCHAR(50) DEFAULT 'grid',
    columns INTEGER DEFAULT 4,

    -- Widgets configuration
    widgets_config JSONB,

    -- Filtres par défaut
    default_filters JSONB,
    date_range VARCHAR(50),

    -- Permissions
    visible_roles JSONB,
    editable_roles JSONB,

    -- État
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT false,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    owner_id INTEGER,

    CONSTRAINT uq_web_dashboards_tenant_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS ix_web_dashboards_tenant ON web_dashboards(tenant_id);
CREATE INDEX IF NOT EXISTS ix_web_dashboards_default ON web_dashboards(tenant_id, is_default);
CREATE INDEX IF NOT EXISTS ix_web_dashboards_owner ON web_dashboards(tenant_id, owner_id);

-- ============================================================================
-- TABLE: ÉLÉMENTS DE MENU
-- ============================================================================

CREATE TABLE IF NOT EXISTS web_menu_items (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Type de menu
    menu_type menu_type DEFAULT 'MAIN',

    -- Identification
    code VARCHAR(50) NOT NULL,
    label VARCHAR(200) NOT NULL,
    icon VARCHAR(100),

    -- Navigation
    route VARCHAR(500),
    external_url VARCHAR(500),
    target VARCHAR(20) DEFAULT '_self',

    -- Hiérarchie
    parent_id INTEGER REFERENCES web_menu_items(id) ON DELETE CASCADE,
    sort_order INTEGER DEFAULT 0,

    -- Permissions
    required_permission VARCHAR(100),
    visible_roles JSONB,

    -- Badge
    badge_source VARCHAR(200),
    badge_color VARCHAR(20),

    -- État
    is_active BOOLEAN DEFAULT true,
    is_separator BOOLEAN DEFAULT false,
    is_expanded BOOLEAN DEFAULT false,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_web_menu_tenant_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS ix_web_menu_tenant ON web_menu_items(tenant_id);
CREATE INDEX IF NOT EXISTS ix_web_menu_type ON web_menu_items(tenant_id, menu_type);
CREATE INDEX IF NOT EXISTS ix_web_menu_parent ON web_menu_items(tenant_id, parent_id);

-- ============================================================================
-- TABLE: COMPOSANTS UI
-- ============================================================================

CREATE TABLE IF NOT EXISTS web_ui_components (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Catégorie
    category component_category NOT NULL,

    -- Configuration
    props_schema JSONB,
    default_props JSONB,
    template TEXT,

    -- Styles
    styles TEXT,
    css_classes JSONB,

    -- État
    is_active BOOLEAN DEFAULT true,
    is_system BOOLEAN DEFAULT false,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    CONSTRAINT uq_web_components_tenant_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS ix_web_components_tenant ON web_ui_components(tenant_id);
CREATE INDEX IF NOT EXISTS ix_web_components_category ON web_ui_components(tenant_id, category);

-- ============================================================================
-- TABLE: PRÉFÉRENCES UTILISATEUR
-- ============================================================================

CREATE TABLE IF NOT EXISTS web_user_preferences (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL,

    -- Thème
    theme_id INTEGER REFERENCES web_themes(id),
    theme_mode theme_mode DEFAULT 'SYSTEM',

    -- Layout
    sidebar_collapsed BOOLEAN DEFAULT false,
    sidebar_mini BOOLEAN DEFAULT false,
    toolbar_dense BOOLEAN DEFAULT false,

    -- Dashboard
    default_dashboard_id INTEGER REFERENCES web_dashboards(id),
    dashboard_auto_refresh BOOLEAN DEFAULT true,

    -- Table preferences
    table_density VARCHAR(20) DEFAULT 'default',
    table_page_size INTEGER DEFAULT 25,

    -- Accessibilité
    font_size VARCHAR(20) DEFAULT 'medium',
    high_contrast BOOLEAN DEFAULT false,
    reduced_motion BOOLEAN DEFAULT false,

    -- Langue et région
    language VARCHAR(5) DEFAULT 'fr',
    date_format VARCHAR(20) DEFAULT 'DD/MM/YYYY',
    time_format VARCHAR(20) DEFAULT '24h',
    timezone VARCHAR(50) DEFAULT 'Europe/Paris',

    -- Notifications UI
    show_tooltips BOOLEAN DEFAULT true,
    sound_enabled BOOLEAN DEFAULT true,
    desktop_notifications BOOLEAN DEFAULT false,

    -- Personnalisation
    custom_shortcuts JSONB,
    favorite_widgets JSONB,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_web_prefs_tenant_user UNIQUE (tenant_id, user_id)
);

CREATE INDEX IF NOT EXISTS ix_web_prefs_tenant ON web_user_preferences(tenant_id);
CREATE INDEX IF NOT EXISTS ix_web_prefs_user ON web_user_preferences(tenant_id, user_id);

-- ============================================================================
-- TABLE: RACCOURCIS CLAVIER
-- ============================================================================

CREATE TABLE IF NOT EXISTS web_shortcuts (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Combinaison de touches
    key_combination VARCHAR(100) NOT NULL,
    key_code VARCHAR(50),

    -- Action
    action_type VARCHAR(50) NOT NULL,
    action_value VARCHAR(500),

    -- Contexte
    context VARCHAR(100) DEFAULT 'global',

    -- État
    is_active BOOLEAN DEFAULT true,
    is_system BOOLEAN DEFAULT false,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_web_shortcuts_tenant_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS ix_web_shortcuts_tenant ON web_shortcuts(tenant_id);
CREATE INDEX IF NOT EXISTS ix_web_shortcuts_context ON web_shortcuts(tenant_id, context);

-- ============================================================================
-- TABLE: PAGES PERSONNALISÉES
-- ============================================================================

CREATE TABLE IF NOT EXISTS web_custom_pages (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    slug VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,

    -- Type et contenu
    page_type page_type DEFAULT 'CUSTOM',
    content TEXT,
    template VARCHAR(100),
    data_source VARCHAR(200),

    -- Layout
    layout VARCHAR(50) DEFAULT 'default',
    show_sidebar BOOLEAN DEFAULT true,
    show_toolbar BOOLEAN DEFAULT true,

    -- SEO
    meta_title VARCHAR(200),
    meta_description VARCHAR(500),

    -- Permissions
    required_permission VARCHAR(100),
    visible_roles JSONB,

    -- État
    is_active BOOLEAN DEFAULT true,
    is_published BOOLEAN DEFAULT false,
    published_at TIMESTAMP,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    CONSTRAINT uq_web_pages_tenant_slug UNIQUE (tenant_id, slug)
);

CREATE INDEX IF NOT EXISTS ix_web_pages_tenant ON web_custom_pages(tenant_id);
CREATE INDEX IF NOT EXISTS ix_web_pages_slug ON web_custom_pages(tenant_id, slug);
CREATE INDEX IF NOT EXISTS ix_web_pages_type ON web_custom_pages(tenant_id, page_type);

-- ============================================================================
-- TRIGGERS UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION update_web_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_web_themes_updated ON web_themes;
CREATE TRIGGER trg_web_themes_updated
    BEFORE UPDATE ON web_themes
    FOR EACH ROW EXECUTE FUNCTION update_web_timestamp();

DROP TRIGGER IF EXISTS trg_web_widgets_updated ON web_widgets;
CREATE TRIGGER trg_web_widgets_updated
    BEFORE UPDATE ON web_widgets
    FOR EACH ROW EXECUTE FUNCTION update_web_timestamp();

DROP TRIGGER IF EXISTS trg_web_dashboards_updated ON web_dashboards;
CREATE TRIGGER trg_web_dashboards_updated
    BEFORE UPDATE ON web_dashboards
    FOR EACH ROW EXECUTE FUNCTION update_web_timestamp();

DROP TRIGGER IF EXISTS trg_web_menu_updated ON web_menu_items;
CREATE TRIGGER trg_web_menu_updated
    BEFORE UPDATE ON web_menu_items
    FOR EACH ROW EXECUTE FUNCTION update_web_timestamp();

DROP TRIGGER IF EXISTS trg_web_components_updated ON web_ui_components;
CREATE TRIGGER trg_web_components_updated
    BEFORE UPDATE ON web_ui_components
    FOR EACH ROW EXECUTE FUNCTION update_web_timestamp();

DROP TRIGGER IF EXISTS trg_web_prefs_updated ON web_user_preferences;
CREATE TRIGGER trg_web_prefs_updated
    BEFORE UPDATE ON web_user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_web_timestamp();

DROP TRIGGER IF EXISTS trg_web_shortcuts_updated ON web_shortcuts;
CREATE TRIGGER trg_web_shortcuts_updated
    BEFORE UPDATE ON web_shortcuts
    FOR EACH ROW EXECUTE FUNCTION update_web_timestamp();

DROP TRIGGER IF EXISTS trg_web_pages_updated ON web_custom_pages;
CREATE TRIGGER trg_web_pages_updated
    BEFORE UPDATE ON web_custom_pages
    FOR EACH ROW EXECUTE FUNCTION update_web_timestamp();

-- ============================================================================
-- DONNÉES INITIALES - THÈMES
-- ============================================================================

INSERT INTO web_themes (tenant_id, code, name, description, mode, is_default, is_system)
VALUES
    ('SYSTEM', 'light', 'Thème Clair', 'Thème par défaut AZALS', 'LIGHT', true, true),
    ('SYSTEM', 'dark', 'Thème Sombre', 'Thème sombre pour réduire la fatigue oculaire', 'DARK', false, true),
    ('SYSTEM', 'high-contrast', 'Contraste Élevé', 'Thème accessibilité haute visibilité', 'HIGH_CONTRAST', false, true)
ON CONFLICT (tenant_id, code) DO NOTHING;

-- ============================================================================
-- DONNÉES INITIALES - WIDGETS SYSTÈME
-- ============================================================================

INSERT INTO web_widgets (tenant_id, code, name, widget_type, default_size, is_system)
VALUES
    ('SYSTEM', 'kpi-treasury', 'KPI Trésorerie', 'KPI', 'MEDIUM', true),
    ('SYSTEM', 'kpi-revenue', 'KPI Chiffre d''Affaires', 'KPI', 'MEDIUM', true),
    ('SYSTEM', 'kpi-margin', 'KPI Marge', 'KPI', 'MEDIUM', true),
    ('SYSTEM', 'chart-cashflow', 'Graphique Flux de Trésorerie', 'CHART', 'LARGE', true),
    ('SYSTEM', 'table-alerts', 'Alertes Récentes', 'TABLE', 'WIDE', true),
    ('SYSTEM', 'calendar-deadlines', 'Échéances', 'CALENDAR', 'LARGE', true),
    ('SYSTEM', 'gauge-performance', 'Jauge Performance', 'GAUGE', 'SMALL', true),
    ('SYSTEM', 'timeline-activity', 'Activité Récente', 'TIMELINE', 'TALL', true)
ON CONFLICT (tenant_id, code) DO NOTHING;

-- ============================================================================
-- DONNÉES INITIALES - RACCOURCIS SYSTÈME
-- ============================================================================

INSERT INTO web_shortcuts (tenant_id, code, name, key_combination, action_type, action_value, context, is_system)
VALUES
    ('SYSTEM', 'search', 'Recherche globale', 'Ctrl+K', 'execute', 'openSearch', 'global', true),
    ('SYSTEM', 'home', 'Accueil', 'Ctrl+H', 'navigate', '/', 'global', true),
    ('SYSTEM', 'dashboard', 'Dashboard', 'Ctrl+D', 'navigate', '/dashboard', 'global', true),
    ('SYSTEM', 'new', 'Nouveau', 'Ctrl+N', 'execute', 'createNew', 'global', true),
    ('SYSTEM', 'save', 'Sauvegarder', 'Ctrl+S', 'execute', 'save', 'form', true),
    ('SYSTEM', 'cancel', 'Annuler', 'Escape', 'execute', 'cancel', 'form', true),
    ('SYSTEM', 'help', 'Aide', 'F1', 'execute', 'openHelp', 'global', true),
    ('SYSTEM', 'refresh', 'Rafraîchir', 'F5', 'execute', 'refresh', 'global', true)
ON CONFLICT (tenant_id, code) DO NOTHING;

-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE web_themes IS 'Configuration des thèmes visuels';
COMMENT ON TABLE web_widgets IS 'Définitions des widgets de dashboard';
COMMENT ON TABLE web_dashboards IS 'Configuration des tableaux de bord';
COMMENT ON TABLE web_menu_items IS 'Éléments de navigation et menus';
COMMENT ON TABLE web_ui_components IS 'Composants UI réutilisables';
COMMENT ON TABLE web_user_preferences IS 'Préférences utilisateur pour l''interface';
COMMENT ON TABLE web_shortcuts IS 'Raccourcis clavier personnalisables';
COMMENT ON TABLE web_custom_pages IS 'Pages personnalisées CMS';

-- ============================================================================
-- FIN MIGRATION T7
-- ============================================================================
