"""
AZALS MODULE T8 - Modèles Site Web
===================================

Modèles SQLAlchemy pour le site web officiel.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime,
    ForeignKey, Enum, Float, Integer
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.types import UniversalUUID, JSON


# ============================================================================
# ENUMS
# ============================================================================

class PageType(str, enum.Enum):
    """Types de pages du site."""
    LANDING = "LANDING"
    PRODUCT = "PRODUCT"
    PRICING = "PRICING"
    ABOUT = "ABOUT"
    CONTACT = "CONTACT"
    BLOG = "BLOG"
    DOCUMENTATION = "DOCUMENTATION"
    LEGAL = "LEGAL"
    CUSTOM = "CUSTOM"


class PublishStatus(str, enum.Enum):
    """Statuts de publication."""
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class ContentType(str, enum.Enum):
    """Types de contenu blog."""
    ARTICLE = "ARTICLE"
    NEWS = "NEWS"
    CASE_STUDY = "CASE_STUDY"
    TESTIMONIAL = "TESTIMONIAL"
    FAQ = "FAQ"
    TUTORIAL = "TUTORIAL"
    RELEASE_NOTE = "RELEASE_NOTE"


class FormCategory(str, enum.Enum):
    """Catégories de formulaire."""
    CONTACT = "CONTACT"
    DEMO_REQUEST = "DEMO_REQUEST"
    QUOTE_REQUEST = "QUOTE_REQUEST"
    SUPPORT = "SUPPORT"
    NEWSLETTER = "NEWSLETTER"
    FEEDBACK = "FEEDBACK"


class SubmissionStatus(str, enum.Enum):
    """Statuts des soumissions."""
    NEW = "NEW"
    READ = "READ"
    REPLIED = "REPLIED"
    CLOSED = "CLOSED"
    SPAM = "SPAM"


class MediaType(str, enum.Enum):
    """Types de médias."""
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    AUDIO = "AUDIO"


# ============================================================================
# MODÈLES
# ============================================================================

class SitePage(Base):
    """Pages du site web."""
    __tablename__ = "site_pages"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    slug = Column(String(255), nullable=False, index=True)
    page_type = Column(Enum(PageType), nullable=False, default=PageType.CUSTOM)

    # Contenu
    title = Column(String(255), nullable=False)
    subtitle = Column(String(500))
    content = Column(Text)
    excerpt = Column(Text)

    # Médias
    featured_image = Column(String(500))
    hero_video = Column(String(500))

    # SEO
    meta_title = Column(String(255))
    meta_description = Column(Text)
    meta_keywords = Column(String(500))
    canonical_url = Column(String(500))
    og_image = Column(String(500))

    # Structure
    template = Column(String(100), default="default")
    layout_config = Column(JSON)
    sections = Column(JSON)  # Sections de la page

    # Publication
    status = Column(Enum(PublishStatus), default=PublishStatus.DRAFT)
    published_at = Column(DateTime)

    # Navigation
    parent_id = Column(UniversalUUID(), ForeignKey("site_pages.id"))
    sort_order = Column(Integer, default=0)
    show_in_menu = Column(Boolean, default=True)
    show_in_footer = Column(Boolean, default=False)

    # Langue
    language = Column(String(5), default="fr")
    translations = Column(JSON)  # {lang: page_id}

    # Statistiques
    view_count = Column(Integer, default=0)

    # Flags
    is_homepage = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)
    requires_auth = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())

    # Relations
    children = relationship("SitePage", backref="parent", remote_side=[id])


class BlogPost(Base):
    """Articles de blog."""
    __tablename__ = "blog_posts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    slug = Column(String(255), nullable=False, index=True)
    content_type = Column(Enum(ContentType), default=ContentType.ARTICLE)

    # Contenu
    title = Column(String(255), nullable=False)
    subtitle = Column(String(500))
    content = Column(Text)
    excerpt = Column(Text)

    # Médias
    featured_image = Column(String(500))
    gallery = Column(JSON)  # [{"url": "...", "caption": "..."}]

    # SEO
    meta_title = Column(String(255))
    meta_description = Column(Text)
    meta_keywords = Column(String(500))

    # Catégorisation
    category = Column(String(100), index=True)
    tags = Column(JSON)  # ["tag1", "tag2"]

    # Auteur
    author_id = Column(UniversalUUID())
    author_name = Column(String(255))
    author_avatar = Column(String(500))
    author_bio = Column(Text)

    # Publication
    status = Column(Enum(PublishStatus), default=PublishStatus.DRAFT)
    published_at = Column(DateTime)

    # Langue
    language = Column(String(5), default="fr")
    translations = Column(JSON)

    # Engagement
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)

    # Temps de lecture estimé (minutes)
    reading_time = Column(Integer)

    # Flags
    is_featured = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    allow_comments = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())


class Testimonial(Base):
    """Témoignages clients."""
    __tablename__ = "testimonials"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Client
    client_name = Column(String(255), nullable=False)
    client_title = Column(String(255))
    client_company = Column(String(255))
    client_logo = Column(String(500))
    client_avatar = Column(String(500))

    # Témoignage
    quote = Column(Text, nullable=False)
    full_testimonial = Column(Text)

    # Contexte
    industry = Column(String(100))
    use_case = Column(String(255))
    modules_used = Column(JSON)  # ["M1", "M3", "M5"]

    # Métriques
    metrics = Column(JSON)  # [{"label": "ROI", "value": "+35%"}]

    # Médias
    video_url = Column(String(500))
    case_study_url = Column(String(500))

    # Publication
    status = Column(Enum(PublishStatus), default=PublishStatus.DRAFT)
    published_at = Column(DateTime)

    # Notation
    rating = Column(Integer)  # 1-5

    # Affichage
    sort_order = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    show_on_homepage = Column(Boolean, default=False)

    # Langue
    language = Column(String(5), default="fr")

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())


class ContactSubmission(Base):
    """Soumissions de formulaires de contact."""
    __tablename__ = "contact_submissions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Catégorie
    form_category = Column(Enum(FormCategory), nullable=False)

    # Contact
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50))
    company = Column(String(255))
    job_title = Column(String(255))

    # Message
    subject = Column(String(255))
    message = Column(Text)

    # Contexte
    source_page = Column(String(500))
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    referrer = Column(String(500))

    # Intérêts
    interested_modules = Column(JSON)  # ["M1", "M5"]
    company_size = Column(String(50))  # "1-10", "11-50", etc.
    timeline = Column(String(100))
    budget = Column(String(100))

    # Données additionnelles
    custom_fields = Column(JSON)

    # Statut
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.NEW)

    # Assignation
    assigned_to = Column(UniversalUUID())

    # Réponse
    response = Column(Text)
    responded_at = Column(DateTime)
    responded_by = Column(UniversalUUID())

    # Suivi
    notes = Column(Text)
    follow_up_date = Column(DateTime)

    # Consentements
    consent_marketing = Column(Boolean, default=False)
    consent_newsletter = Column(Boolean, default=False)
    consent_privacy = Column(Boolean, default=True)

    # Anti-spam
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    honeypot = Column(String(100))  # Anti-spam

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NewsletterSubscriber(Base):
    """Abonnés newsletter."""
    __tablename__ = "newsletter_subscribers"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Contact
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    company = Column(String(255))

    # Préférences
    language = Column(String(5), default="fr")
    interests = Column(JSON)  # ["product_updates", "blog", "events"]
    frequency = Column(String(50), default="weekly")  # daily, weekly, monthly

    # Statut
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Tokens
    verification_token = Column(String(255))
    unsubscribe_token = Column(String(255))

    # Dates
    verified_at = Column(DateTime)
    unsubscribed_at = Column(DateTime)
    last_email_sent = Column(DateTime)

    # Source
    source = Column(String(100))  # form, import, api
    source_page = Column(String(500))

    # Statistiques
    emails_received = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)

    # Consentement
    gdpr_consent = Column(Boolean, default=False)
    consent_date = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SiteMedia(Base):
    """Médiathèque du site."""
    __tablename__ = "site_media"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Fichier
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255))
    media_type = Column(Enum(MediaType), nullable=False)
    mime_type = Column(String(100))

    # Stockage
    url = Column(String(500), nullable=False)
    storage_path = Column(String(500))
    file_size = Column(Integer)  # bytes

    # Dimensions (images/vidéos)
    width = Column(Integer)
    height = Column(Integer)
    duration = Column(Integer)  # secondes (vidéo/audio)

    # Optimisation
    thumbnail_url = Column(String(500))
    optimized_url = Column(String(500))

    # Métadonnées
    alt_text = Column(String(255))
    title = Column(String(255))
    description = Column(Text)
    caption = Column(Text)

    # Organisation
    folder = Column(String(255), default="/")
    tags = Column(JSON)

    # Utilisation
    usage_count = Column(Integer, default=0)
    used_in = Column(JSON)  # [{"type": "page", "id": 1}]

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())


class SiteSEO(Base):
    """Configuration SEO globale."""
    __tablename__ = "site_seo"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Meta globales
    site_title = Column(String(255))
    site_description = Column(Text)
    site_keywords = Column(String(500))

    # Open Graph
    og_site_name = Column(String(255))
    og_default_image = Column(String(500))
    og_locale = Column(String(10), default="fr_FR")

    # Twitter
    twitter_card = Column(String(50), default="summary_large_image")
    twitter_site = Column(String(100))
    twitter_creator = Column(String(100))

    # Vérifications
    google_site_verification = Column(String(255))
    bing_site_verification = Column(String(255))

    # Schema.org
    organization_schema = Column(JSON)
    local_business_schema = Column(JSON)

    # Robots
    robots_txt = Column(Text)
    sitemap_url = Column(String(500))

    # Analytics
    google_analytics_id = Column(String(50))
    google_tag_manager_id = Column(String(50))
    facebook_pixel_id = Column(String(50))

    # Autres scripts
    head_scripts = Column(Text)
    body_scripts = Column(Text)

    # 301 Redirects
    redirects = Column(JSON)  # [{"from": "/old", "to": "/new"}]

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID())


class SiteAnalytics(Base):
    """Données analytics agrégées."""
    __tablename__ = "site_analytics"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Période
    date = Column(DateTime, nullable=False, index=True)
    period = Column(String(20), default="daily")  # daily, weekly, monthly

    # Trafic
    page_views = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    sessions = Column(Integer, default=0)

    # Comportement
    bounce_rate = Column(Float)
    avg_session_duration = Column(Integer)  # secondes
    pages_per_session = Column(Float)

    # Sources
    traffic_sources = Column(JSON)  # {"organic": 100, "direct": 50}
    referrers = Column(JSON)  # {"google.com": 80}

    # Géographie
    countries = Column(JSON)  # {"FR": 500, "BE": 100}
    cities = Column(JSON)

    # Appareils
    devices = Column(JSON)  # {"desktop": 60, "mobile": 35}
    browsers = Column(JSON)

    # Pages populaires
    top_pages = Column(JSON)  # [{"url": "/", "views": 100}]

    # Conversions
    form_submissions = Column(Integer, default=0)
    newsletter_signups = Column(Integer, default=0)
    demo_requests = Column(Integer, default=0)

    # Blog
    blog_views = Column(Integer, default=0)
    top_posts = Column(JSON)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
