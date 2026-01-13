"""
AZALS MODULE T8 - Modèles Site Web
===================================

Modèles SQLAlchemy pour le site web officiel.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.types import JSON, UniversalUUID
from app.db import Base

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

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    slug: Mapped[str | None] = mapped_column(String(255), nullable=False, index=True)
    page_type: Mapped[str | None] = mapped_column(Enum(PageType), nullable=False, default=PageType.CUSTOM)

    # Contenu
    title: Mapped[str | None] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str | None] = mapped_column(Text)
    excerpt: Mapped[str | None] = mapped_column(Text)

    # Médias
    featured_image: Mapped[str | None] = mapped_column(String(500))
    hero_video: Mapped[str | None] = mapped_column(String(500))

    # SEO
    meta_title: Mapped[str | None] = mapped_column(String(255))
    meta_description: Mapped[str | None] = mapped_column(Text)
    meta_keywords: Mapped[str | None] = mapped_column(String(500))
    canonical_url: Mapped[str | None] = mapped_column(String(500))
    og_image: Mapped[str | None] = mapped_column(String(500))

    # Structure
    template: Mapped[str | None] = mapped_column(String(100), default="default")
    layout_config: Mapped[dict | None] = mapped_column(JSON)
    sections: Mapped[dict | None] = mapped_column(JSON)  # Sections de la page

    # Publication
    status: Mapped[str | None] = mapped_column(Enum(PublishStatus), default=PublishStatus.DRAFT)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Navigation
    parent_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("site_pages.id"))
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)
    show_in_menu: Mapped[bool | None] = mapped_column(Boolean, default=True)
    show_in_footer: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Langue
    language: Mapped[str | None] = mapped_column(String(5), default="fr")
    translations: Mapped[dict | None] = mapped_column(JSON)  # {lang: page_id}

    # Statistiques
    view_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Flags
    is_homepage: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_system: Mapped[bool | None] = mapped_column(Boolean, default=False)
    requires_auth: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    # Relations
    children = relationship("SitePage", backref="parent", remote_side=[id])


class BlogPost(Base):
    """Articles de blog."""
    __tablename__ = "blog_posts"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    slug: Mapped[str | None] = mapped_column(String(255), nullable=False, index=True)
    content_type: Mapped[str | None] = mapped_column(Enum(ContentType), default=ContentType.ARTICLE)

    # Contenu
    title: Mapped[str | None] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str | None] = mapped_column(Text)
    excerpt: Mapped[str | None] = mapped_column(Text)

    # Médias
    featured_image: Mapped[str | None] = mapped_column(String(500))
    gallery: Mapped[dict | None] = mapped_column(JSON)  # [{"url": "...", "caption": "..."}]

    # SEO
    meta_title: Mapped[str | None] = mapped_column(String(255))
    meta_description: Mapped[str | None] = mapped_column(Text)
    meta_keywords: Mapped[str | None] = mapped_column(String(500))

    # Catégorisation
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    tags: Mapped[dict | None] = mapped_column(JSON)  # ["tag1", "tag2"]

    # Auteur
    author_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    author_name: Mapped[str | None] = mapped_column(String(255))
    author_avatar: Mapped[str | None] = mapped_column(String(500))
    author_bio: Mapped[str | None] = mapped_column(Text)

    # Publication
    status: Mapped[str | None] = mapped_column(Enum(PublishStatus), default=PublishStatus.DRAFT)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Langue
    language: Mapped[str | None] = mapped_column(String(5), default="fr")
    translations: Mapped[dict | None] = mapped_column(JSON)

    # Engagement
    view_count: Mapped[int | None] = mapped_column(Integer, default=0)
    like_count: Mapped[int | None] = mapped_column(Integer, default=0)
    share_count: Mapped[int | None] = mapped_column(Integer, default=0)
    comment_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Temps de lecture estimé (minutes)
    reading_time: Mapped[int | None] = mapped_column(Integer)

    # Flags
    is_featured: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_pinned: Mapped[bool | None] = mapped_column(Boolean, default=False)
    allow_comments: Mapped[bool | None] = mapped_column(Boolean, default=True)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())


class Testimonial(Base):
    """Témoignages clients."""
    __tablename__ = "testimonials"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Client
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=False)
    client_title: Mapped[str | None] = mapped_column(String(255))
    client_company: Mapped[str | None] = mapped_column(String(255))
    client_logo: Mapped[str | None] = mapped_column(String(500))
    client_avatar: Mapped[str | None] = mapped_column(String(500))

    # Témoignage
    quote: Mapped[str] = mapped_column(Text)
    full_testimonial: Mapped[str | None] = mapped_column(Text)

    # Contexte
    industry: Mapped[str | None] = mapped_column(String(100))
    use_case: Mapped[str | None] = mapped_column(String(255))
    modules_used: Mapped[dict | None] = mapped_column(JSON)  # ["M1", "M3", "M5"]

    # Métriques
    metrics: Mapped[dict | None] = mapped_column(JSON)  # [{"label": "ROI", "value": "+35%"}]

    # Médias
    video_url: Mapped[str | None] = mapped_column(String(500))
    case_study_url: Mapped[str | None] = mapped_column(String(500))

    # Publication
    status: Mapped[str | None] = mapped_column(Enum(PublishStatus), default=PublishStatus.DRAFT)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Notation
    rating: Mapped[int | None] = mapped_column(Integer)  # 1-5

    # Affichage
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)
    is_featured: Mapped[bool | None] = mapped_column(Boolean, default=False)
    show_on_homepage: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Langue
    language: Mapped[str | None] = mapped_column(String(5), default="fr")

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())


class ContactSubmission(Base):
    """Soumissions de formulaires de contact."""
    __tablename__ = "contact_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Catégorie
    form_category: Mapped[str | None] = mapped_column(Enum(FormCategory), nullable=False)

    # Contact
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    company: Mapped[str | None] = mapped_column(String(255))
    job_title: Mapped[str | None] = mapped_column(String(255))

    # Message
    subject: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str | None] = mapped_column(Text)

    # Contexte
    source_page: Mapped[str | None] = mapped_column(String(500))
    utm_source: Mapped[str | None] = mapped_column(String(100))
    utm_medium: Mapped[str | None] = mapped_column(String(100))
    utm_campaign: Mapped[str | None] = mapped_column(String(100))
    referrer: Mapped[str | None] = mapped_column(String(500))

    # Intérêts
    interested_modules: Mapped[dict | None] = mapped_column(JSON)  # ["M1", "M5"]
    company_size: Mapped[str | None] = mapped_column(String(50))  # "1-10", "11-50", etc.
    timeline: Mapped[str | None] = mapped_column(String(100))
    budget: Mapped[str | None] = mapped_column(String(100))

    # Données additionnelles
    custom_fields: Mapped[dict | None] = mapped_column(JSON)

    # Statut
    status: Mapped[str | None] = mapped_column(Enum(SubmissionStatus), default=SubmissionStatus.NEW)

    # Assignation
    assigned_to: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    # Réponse
    response: Mapped[str | None] = mapped_column(Text)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime)
    responded_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    # Suivi
    notes: Mapped[str | None] = mapped_column(Text)
    follow_up_date: Mapped[datetime | None] = mapped_column(DateTime)

    # Consentements
    consent_marketing: Mapped[bool | None] = mapped_column(Boolean, default=False)
    consent_newsletter: Mapped[bool | None] = mapped_column(Boolean, default=False)
    consent_privacy: Mapped[bool | None] = mapped_column(Boolean, default=True)

    # Anti-spam
    ip_address: Mapped[str | None] = mapped_column(String(50))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    honeypot: Mapped[str | None] = mapped_column(String(100))  # Anti-spam

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NewsletterSubscriber(Base):
    """Abonnés newsletter."""
    __tablename__ = "newsletter_subscribers"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Contact
    email: Mapped[str | None] = mapped_column(String(255), nullable=False, index=True)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    company: Mapped[str | None] = mapped_column(String(255))

    # Préférences
    language: Mapped[str | None] = mapped_column(String(5), default="fr")
    interests: Mapped[dict | None] = mapped_column(JSON)  # ["product_updates", "blog", "events"]
    frequency: Mapped[str | None] = mapped_column(String(50), default="weekly")  # daily, weekly, monthly

    # Statut
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Tokens
    verification_token: Mapped[str | None] = mapped_column(String(255))
    unsubscribe_token: Mapped[str | None] = mapped_column(String(255))

    # Dates
    verified_at: Mapped[datetime | None] = mapped_column(DateTime)
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_email_sent: Mapped[datetime | None] = mapped_column(DateTime)

    # Source
    source: Mapped[str | None] = mapped_column(String(100))  # form, import, api
    source_page: Mapped[str | None] = mapped_column(String(500))

    # Statistiques
    emails_received: Mapped[int | None] = mapped_column(Integer, default=0)
    emails_opened: Mapped[int | None] = mapped_column(Integer, default=0)
    emails_clicked: Mapped[int | None] = mapped_column(Integer, default=0)

    # Consentement
    gdpr_consent: Mapped[bool | None] = mapped_column(Boolean, default=False)
    consent_date: Mapped[datetime | None] = mapped_column(DateTime)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SiteMedia(Base):
    """Médiathèque du site."""
    __tablename__ = "site_media"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Fichier
    filename: Mapped[str | None] = mapped_column(String(255), nullable=False)
    original_name: Mapped[str | None] = mapped_column(String(255))
    media_type: Mapped[str | None] = mapped_column(Enum(MediaType), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100))

    # Stockage
    url: Mapped[str | None] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(500))
    file_size: Mapped[int | None] = mapped_column(Integer)  # bytes

    # Dimensions (images/vidéos)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    duration: Mapped[int | None] = mapped_column(Integer)  # secondes (vidéo/audio)

    # Optimisation
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    optimized_url: Mapped[str | None] = mapped_column(String(500))

    # Métadonnées
    alt_text: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    caption: Mapped[str | None] = mapped_column(Text)

    # Organisation
    folder: Mapped[str | None] = mapped_column(String(255), default="/")
    tags: Mapped[dict | None] = mapped_column(JSON)

    # Utilisation
    usage_count: Mapped[int | None] = mapped_column(Integer, default=0)
    used_in: Mapped[dict | None] = mapped_column(JSON)  # [{"type": "page", "id": 1}]

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())


class SiteSEO(Base):
    """Configuration SEO globale."""
    __tablename__ = "site_seo"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Meta globales
    site_title: Mapped[str | None] = mapped_column(String(255))
    site_description: Mapped[str | None] = mapped_column(Text)
    site_keywords: Mapped[str | None] = mapped_column(String(500))

    # Open Graph
    og_site_name: Mapped[str | None] = mapped_column(String(255))
    og_default_image: Mapped[str | None] = mapped_column(String(500))
    og_locale: Mapped[str | None] = mapped_column(String(10), default="fr_FR")

    # Twitter
    twitter_card: Mapped[str | None] = mapped_column(String(50), default="summary_large_image")
    twitter_site: Mapped[str | None] = mapped_column(String(100))
    twitter_creator: Mapped[str | None] = mapped_column(String(100))

    # Vérifications
    google_site_verification: Mapped[str | None] = mapped_column(String(255))
    bing_site_verification: Mapped[str | None] = mapped_column(String(255))

    # Schema.org
    organization_schema: Mapped[dict | None] = mapped_column(JSON)
    local_business_schema: Mapped[dict | None] = mapped_column(JSON)

    # Robots
    robots_txt: Mapped[str | None] = mapped_column(Text)
    sitemap_url: Mapped[str | None] = mapped_column(String(500))

    # Analytics
    google_analytics_id: Mapped[str | None] = mapped_column(String(50))
    google_tag_manager_id: Mapped[str | None] = mapped_column(String(50))
    facebook_pixel_id: Mapped[str | None] = mapped_column(String(50))

    # Autres scripts
    head_scripts: Mapped[str | None] = mapped_column(Text)
    body_scripts: Mapped[str | None] = mapped_column(Text)

    # 301 Redirects
    redirects: Mapped[dict | None] = mapped_column(JSON)  # [{"from": "/old", "to": "/new"}]

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())


class SiteAnalytics(Base):
    """Données analytics agrégées."""
    __tablename__ = "site_analytics"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Période
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    period: Mapped[str | None] = mapped_column(String(20), default="daily")  # daily, weekly, monthly

    # Trafic
    page_views: Mapped[int | None] = mapped_column(Integer, default=0)
    unique_visitors: Mapped[int | None] = mapped_column(Integer, default=0)
    sessions: Mapped[int | None] = mapped_column(Integer, default=0)

    # Comportement
    bounce_rate: Mapped[float | None] = mapped_column(Float)
    avg_session_duration: Mapped[int | None] = mapped_column(Integer)  # secondes
    pages_per_session: Mapped[float | None] = mapped_column(Float)

    # Sources
    traffic_sources: Mapped[dict | None] = mapped_column(JSON)  # {"organic": 100, "direct": 50}
    referrers: Mapped[dict | None] = mapped_column(JSON)  # {"google.com": 80}

    # Géographie
    countries: Mapped[dict | None] = mapped_column(JSON)  # {"FR": 500, "BE": 100}
    cities: Mapped[dict | None] = mapped_column(JSON)

    # Appareils
    devices: Mapped[dict | None] = mapped_column(JSON)  # {"desktop": 60, "mobile": 35}
    browsers: Mapped[dict | None] = mapped_column(JSON)

    # Pages populaires
    top_pages: Mapped[dict | None] = mapped_column(JSON)  # [{"url": "/", "views": 100}]

    # Conversions
    form_submissions: Mapped[int | None] = mapped_column(Integer, default=0)
    newsletter_signups: Mapped[int | None] = mapped_column(Integer, default=0)
    demo_requests: Mapped[int | None] = mapped_column(Integer, default=0)

    # Blog
    blog_views: Mapped[int | None] = mapped_column(Integer, default=0)
    top_posts: Mapped[dict | None] = mapped_column(JSON)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
