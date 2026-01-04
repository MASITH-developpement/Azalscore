-- ============================================================================
-- AZALS MODULE T8 - SITE WEB OFFICIEL
-- Migration: 014_website_module.sql
-- Date: 2026-01-03
-- ============================================================================

-- ============================================================================
-- ENUMS
-- ============================================================================

CREATE TYPE page_type AS ENUM (
    'LANDING', 'PRODUCT', 'PRICING', 'ABOUT', 'CONTACT',
    'BLOG', 'DOCUMENTATION', 'LEGAL', 'CUSTOM'
);

CREATE TYPE publish_status AS ENUM (
    'DRAFT', 'PENDING_REVIEW', 'PUBLISHED', 'ARCHIVED'
);

CREATE TYPE content_type AS ENUM (
    'ARTICLE', 'NEWS', 'CASE_STUDY', 'TESTIMONIAL',
    'FAQ', 'TUTORIAL', 'RELEASE_NOTE'
);

CREATE TYPE form_category AS ENUM (
    'CONTACT', 'DEMO_REQUEST', 'QUOTE_REQUEST',
    'SUPPORT', 'NEWSLETTER', 'FEEDBACK'
);

CREATE TYPE submission_status AS ENUM (
    'NEW', 'READ', 'REPLIED', 'CLOSED', 'SPAM'
);

CREATE TYPE media_type AS ENUM (
    'IMAGE', 'VIDEO', 'DOCUMENT', 'AUDIO'
);


-- ============================================================================
-- TABLES
-- ============================================================================

-- Pages du site
CREATE TABLE site_pages (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    slug VARCHAR(255) NOT NULL,
    page_type page_type NOT NULL DEFAULT 'CUSTOM',

    -- Contenu
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(500),
    content TEXT,
    excerpt TEXT,

    -- Médias
    featured_image VARCHAR(500),
    hero_video VARCHAR(500),

    -- SEO
    meta_title VARCHAR(255),
    meta_description TEXT,
    meta_keywords VARCHAR(500),
    canonical_url VARCHAR(500),
    og_image VARCHAR(500),

    -- Structure
    template VARCHAR(100) DEFAULT 'default',
    layout_config JSONB,
    sections JSONB,

    -- Publication
    status publish_status DEFAULT 'DRAFT',
    published_at TIMESTAMP,

    -- Navigation
    parent_id INTEGER REFERENCES site_pages(id),
    sort_order INTEGER DEFAULT 0,
    show_in_menu BOOLEAN DEFAULT TRUE,
    show_in_footer BOOLEAN DEFAULT FALSE,

    -- Langue
    language VARCHAR(5) DEFAULT 'fr',
    translations JSONB,

    -- Statistiques
    view_count INTEGER DEFAULT 0,

    -- Flags
    is_homepage BOOLEAN DEFAULT FALSE,
    is_system BOOLEAN DEFAULT FALSE,
    requires_auth BOOLEAN DEFAULT FALSE,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER
);

-- Index site_pages
CREATE INDEX idx_site_pages_tenant ON site_pages(tenant_id);
CREATE INDEX idx_site_pages_slug ON site_pages(tenant_id, slug);
CREATE INDEX idx_site_pages_type ON site_pages(tenant_id, page_type);
CREATE INDEX idx_site_pages_status ON site_pages(tenant_id, status);
CREATE UNIQUE INDEX idx_site_pages_homepage ON site_pages(tenant_id) WHERE is_homepage = TRUE;


-- Articles de blog
CREATE TABLE blog_posts (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    slug VARCHAR(255) NOT NULL,
    content_type content_type DEFAULT 'ARTICLE',

    -- Contenu
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(500),
    content TEXT,
    excerpt TEXT,

    -- Médias
    featured_image VARCHAR(500),
    gallery JSONB,

    -- SEO
    meta_title VARCHAR(255),
    meta_description TEXT,
    meta_keywords VARCHAR(500),

    -- Catégorisation
    category VARCHAR(100),
    tags JSONB,

    -- Auteur
    author_id INTEGER,
    author_name VARCHAR(255),
    author_avatar VARCHAR(500),
    author_bio TEXT,

    -- Publication
    status publish_status DEFAULT 'DRAFT',
    published_at TIMESTAMP,

    -- Langue
    language VARCHAR(5) DEFAULT 'fr',
    translations JSONB,

    -- Engagement
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,

    -- Temps de lecture
    reading_time INTEGER,

    -- Flags
    is_featured BOOLEAN DEFAULT FALSE,
    is_pinned BOOLEAN DEFAULT FALSE,
    allow_comments BOOLEAN DEFAULT TRUE,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER
);

-- Index blog_posts
CREATE INDEX idx_blog_posts_tenant ON blog_posts(tenant_id);
CREATE INDEX idx_blog_posts_slug ON blog_posts(tenant_id, slug);
CREATE INDEX idx_blog_posts_category ON blog_posts(tenant_id, category);
CREATE INDEX idx_blog_posts_status ON blog_posts(tenant_id, status);
CREATE INDEX idx_blog_posts_published ON blog_posts(tenant_id, published_at DESC);


-- Témoignages
CREATE TABLE testimonials (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Client
    client_name VARCHAR(255) NOT NULL,
    client_title VARCHAR(255),
    client_company VARCHAR(255),
    client_logo VARCHAR(500),
    client_avatar VARCHAR(500),

    -- Témoignage
    quote TEXT NOT NULL,
    full_testimonial TEXT,

    -- Contexte
    industry VARCHAR(100),
    use_case VARCHAR(255),
    modules_used JSONB,
    metrics JSONB,

    -- Médias
    video_url VARCHAR(500),
    case_study_url VARCHAR(500),

    -- Publication
    status publish_status DEFAULT 'DRAFT',
    published_at TIMESTAMP,

    -- Notation
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),

    -- Affichage
    sort_order INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE,
    show_on_homepage BOOLEAN DEFAULT FALSE,

    -- Langue
    language VARCHAR(5) DEFAULT 'fr',

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER
);

-- Index testimonials
CREATE INDEX idx_testimonials_tenant ON testimonials(tenant_id);
CREATE INDEX idx_testimonials_industry ON testimonials(tenant_id, industry);
CREATE INDEX idx_testimonials_status ON testimonials(tenant_id, status);


-- Soumissions de contact
CREATE TABLE contact_submissions (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Catégorie
    form_category form_category NOT NULL,

    -- Contact
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    company VARCHAR(255),
    job_title VARCHAR(255),

    -- Message
    subject VARCHAR(255),
    message TEXT,

    -- Contexte
    source_page VARCHAR(500),
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    referrer VARCHAR(500),

    -- Intérêts
    interested_modules JSONB,
    company_size VARCHAR(50),
    timeline VARCHAR(100),
    budget VARCHAR(100),

    -- Données additionnelles
    custom_fields JSONB,

    -- Statut
    status submission_status DEFAULT 'NEW',

    -- Assignation
    assigned_to INTEGER,

    -- Réponse
    response TEXT,
    responded_at TIMESTAMP,
    responded_by INTEGER,

    -- Suivi
    notes TEXT,
    follow_up_date TIMESTAMP,

    -- Consentements
    consent_marketing BOOLEAN DEFAULT FALSE,
    consent_newsletter BOOLEAN DEFAULT FALSE,
    consent_privacy BOOLEAN DEFAULT TRUE,

    -- Anti-spam
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    honeypot VARCHAR(100),

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index contact_submissions
CREATE INDEX idx_contact_submissions_tenant ON contact_submissions(tenant_id);
CREATE INDEX idx_contact_submissions_email ON contact_submissions(tenant_id, email);
CREATE INDEX idx_contact_submissions_category ON contact_submissions(tenant_id, form_category);
CREATE INDEX idx_contact_submissions_status ON contact_submissions(tenant_id, status);
CREATE INDEX idx_contact_submissions_created ON contact_submissions(tenant_id, created_at DESC);


-- Abonnés newsletter
CREATE TABLE newsletter_subscribers (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Contact
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company VARCHAR(255),

    -- Préférences
    language VARCHAR(5) DEFAULT 'fr',
    interests JSONB,
    frequency VARCHAR(50) DEFAULT 'weekly',

    -- Statut
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,

    -- Tokens
    verification_token VARCHAR(255),
    unsubscribe_token VARCHAR(255),

    -- Dates
    verified_at TIMESTAMP,
    unsubscribed_at TIMESTAMP,
    last_email_sent TIMESTAMP,

    -- Source
    source VARCHAR(100),
    source_page VARCHAR(500),

    -- Statistiques
    emails_received INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,

    -- Consentement
    gdpr_consent BOOLEAN DEFAULT FALSE,
    consent_date TIMESTAMP,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index newsletter_subscribers
CREATE INDEX idx_newsletter_subscribers_tenant ON newsletter_subscribers(tenant_id);
CREATE INDEX idx_newsletter_subscribers_email ON newsletter_subscribers(tenant_id, email);
CREATE UNIQUE INDEX idx_newsletter_subscribers_unique ON newsletter_subscribers(tenant_id, email);


-- Médiathèque
CREATE TABLE site_media (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Fichier
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255),
    media_type media_type NOT NULL,
    mime_type VARCHAR(100),

    -- Stockage
    url VARCHAR(500) NOT NULL,
    storage_path VARCHAR(500),
    file_size INTEGER,

    -- Dimensions
    width INTEGER,
    height INTEGER,
    duration INTEGER,

    -- Optimisation
    thumbnail_url VARCHAR(500),
    optimized_url VARCHAR(500),

    -- Métadonnées
    alt_text VARCHAR(255),
    title VARCHAR(255),
    description TEXT,
    caption TEXT,

    -- Organisation
    folder VARCHAR(255) DEFAULT '/',
    tags JSONB,

    -- Utilisation
    usage_count INTEGER DEFAULT 0,
    used_in JSONB,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER
);

-- Index site_media
CREATE INDEX idx_site_media_tenant ON site_media(tenant_id);
CREATE INDEX idx_site_media_type ON site_media(tenant_id, media_type);
CREATE INDEX idx_site_media_folder ON site_media(tenant_id, folder);


-- Configuration SEO
CREATE TABLE site_seo (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL UNIQUE,

    -- Meta globales
    site_title VARCHAR(255),
    site_description TEXT,
    site_keywords VARCHAR(500),

    -- Open Graph
    og_site_name VARCHAR(255),
    og_default_image VARCHAR(500),
    og_locale VARCHAR(10) DEFAULT 'fr_FR',

    -- Twitter
    twitter_card VARCHAR(50) DEFAULT 'summary_large_image',
    twitter_site VARCHAR(100),
    twitter_creator VARCHAR(100),

    -- Vérifications
    google_site_verification VARCHAR(255),
    bing_site_verification VARCHAR(255),

    -- Schema.org
    organization_schema JSONB,
    local_business_schema JSONB,

    -- Robots
    robots_txt TEXT,
    sitemap_url VARCHAR(500),

    -- Analytics
    google_analytics_id VARCHAR(50),
    google_tag_manager_id VARCHAR(50),
    facebook_pixel_id VARCHAR(50),

    -- Scripts
    head_scripts TEXT,
    body_scripts TEXT,

    -- Redirects
    redirects JSONB,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by INTEGER
);

-- Index site_seo
CREATE INDEX idx_site_seo_tenant ON site_seo(tenant_id);


-- Analytics
CREATE TABLE site_analytics (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Période
    date TIMESTAMP NOT NULL,
    period VARCHAR(20) DEFAULT 'daily',

    -- Trafic
    page_views INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    sessions INTEGER DEFAULT 0,

    -- Comportement
    bounce_rate FLOAT,
    avg_session_duration INTEGER,
    pages_per_session FLOAT,

    -- Sources
    traffic_sources JSONB,
    referrers JSONB,

    -- Géographie
    countries JSONB,
    cities JSONB,

    -- Appareils
    devices JSONB,
    browsers JSONB,

    -- Pages populaires
    top_pages JSONB,

    -- Conversions
    form_submissions INTEGER DEFAULT 0,
    newsletter_signups INTEGER DEFAULT 0,
    demo_requests INTEGER DEFAULT 0,

    -- Blog
    blog_views INTEGER DEFAULT 0,
    top_posts JSONB,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index site_analytics
CREATE INDEX idx_site_analytics_tenant ON site_analytics(tenant_id);
CREATE INDEX idx_site_analytics_date ON site_analytics(tenant_id, date);
CREATE INDEX idx_site_analytics_period ON site_analytics(tenant_id, period, date);


-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger updated_at pour site_pages
CREATE TRIGGER update_site_pages_updated_at
    BEFORE UPDATE ON site_pages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour blog_posts
CREATE TRIGGER update_blog_posts_updated_at
    BEFORE UPDATE ON blog_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour testimonials
CREATE TRIGGER update_testimonials_updated_at
    BEFORE UPDATE ON testimonials
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour contact_submissions
CREATE TRIGGER update_contact_submissions_updated_at
    BEFORE UPDATE ON contact_submissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour newsletter_subscribers
CREATE TRIGGER update_newsletter_subscribers_updated_at
    BEFORE UPDATE ON newsletter_subscribers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour site_media
CREATE TRIGGER update_site_media_updated_at
    BEFORE UPDATE ON site_media
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour site_seo
CREATE TRIGGER update_site_seo_updated_at
    BEFORE UPDATE ON site_seo
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- DONNÉES INITIALES - Pages système
-- ============================================================================

-- Page d'accueil par défaut (template)
INSERT INTO site_pages (tenant_id, slug, page_type, title, subtitle, content, is_homepage, is_system, status)
VALUES (
    'system',
    'home',
    'LANDING',
    'AZALS - ERP Décisionnel',
    'La plateforme ERP intelligente pour dirigeants',
    '<section class="hero">
        <h1>Prenez des décisions éclairées</h1>
        <p>AZALS centralise vos données critiques et vous aide à piloter votre entreprise en temps réel.</p>
    </section>
    <section class="features">
        <h2>Modules métiers complets</h2>
        <p>11 modules intégrés couvrant tous vos besoins : Trésorerie, Comptabilité, RH, Ventes, Achats...</p>
    </section>
    <section class="cta">
        <h2>Prêt à transformer votre gestion ?</h2>
        <a href="/contact" class="btn">Demander une démo</a>
    </section>',
    TRUE,
    TRUE,
    'PUBLISHED'
);

-- Page Produits
INSERT INTO site_pages (tenant_id, slug, page_type, title, status, is_system, sort_order)
VALUES ('system', 'produits', 'PRODUCT', 'Nos Produits', 'PUBLISHED', TRUE, 1);

-- Page Tarifs
INSERT INTO site_pages (tenant_id, slug, page_type, title, status, is_system, sort_order)
VALUES ('system', 'tarifs', 'PRICING', 'Tarifs', 'PUBLISHED', TRUE, 2);

-- Page À propos
INSERT INTO site_pages (tenant_id, slug, page_type, title, status, is_system, sort_order)
VALUES ('system', 'a-propos', 'ABOUT', 'À propos', 'PUBLISHED', TRUE, 3);

-- Page Contact
INSERT INTO site_pages (tenant_id, slug, page_type, title, status, is_system, sort_order)
VALUES ('system', 'contact', 'CONTACT', 'Contact', 'PUBLISHED', TRUE, 4);

-- Page Blog
INSERT INTO site_pages (tenant_id, slug, page_type, title, status, is_system, sort_order)
VALUES ('system', 'blog', 'BLOG', 'Blog', 'PUBLISHED', TRUE, 5);

-- Page Mentions légales (footer)
INSERT INTO site_pages (tenant_id, slug, page_type, title, status, is_system, show_in_menu, show_in_footer, sort_order)
VALUES ('system', 'mentions-legales', 'LEGAL', 'Mentions légales', 'PUBLISHED', TRUE, FALSE, TRUE, 1);

-- Page CGV (footer)
INSERT INTO site_pages (tenant_id, slug, page_type, title, status, is_system, show_in_menu, show_in_footer, sort_order)
VALUES ('system', 'cgv', 'LEGAL', 'CGV', 'PUBLISHED', TRUE, FALSE, TRUE, 2);

-- Page Politique de confidentialité (footer)
INSERT INTO site_pages (tenant_id, slug, page_type, title, status, is_system, show_in_menu, show_in_footer, sort_order)
VALUES ('system', 'politique-confidentialite', 'LEGAL', 'Politique de confidentialité', 'PUBLISHED', TRUE, FALSE, TRUE, 3);


-- ============================================================================
-- DONNÉES INITIALES - Configuration SEO par défaut
-- ============================================================================

INSERT INTO site_seo (
    tenant_id,
    site_title,
    site_description,
    og_site_name,
    og_locale,
    twitter_card,
    robots_txt,
    organization_schema
) VALUES (
    'system',
    'AZALS - ERP Décisionnel Intelligent',
    'AZALS est la plateforme ERP conçue pour les dirigeants. Centralisez vos données, automatisez vos processus et prenez des décisions éclairées.',
    'AZALS',
    'fr_FR',
    'summary_large_image',
    'User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/',
    '{
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "AZALS",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "description": "ERP Décisionnel pour dirigeants"
    }'::jsonb
);


-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE site_pages IS 'Pages du site web officiel AZALS';
COMMENT ON TABLE blog_posts IS 'Articles de blog et actualités';
COMMENT ON TABLE testimonials IS 'Témoignages et études de cas clients';
COMMENT ON TABLE contact_submissions IS 'Soumissions des formulaires de contact';
COMMENT ON TABLE newsletter_subscribers IS 'Abonnés à la newsletter';
COMMENT ON TABLE site_media IS 'Médiathèque du site (images, vidéos, documents)';
COMMENT ON TABLE site_seo IS 'Configuration SEO globale du site';
COMMENT ON TABLE site_analytics IS 'Données analytics agrégées';
