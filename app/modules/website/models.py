"""
AZALS MODULE T8 - Modèles Site Web
===================================

Modèles SQLAlchemy pour le site web officiel.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db import Base
from app.core.types import JSON, UniversalUUID
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional

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
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    slug: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)
    page_type: Mapped[Optional[str]] = mapped_column(Enum(PageType), nullable=False, default=PageType.CUSTOM)

    # Contenu
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(String(500))
    content: Mapped[Optional[str]] = mapped_column(Text)
    excerpt: Mapped[Optional[str]] = mapped_column(Text)

    # Médias
    featured_image: Mapped[Optional[str]] = mapped_column(String(500))
    hero_video: Mapped[Optional[str]] = mapped_column(String(500))

    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(255))
    meta_description: Mapped[Optional[str]] = mapped_column(Text)
    meta_keywords: Mapped[Optional[str]] = mapped_column(String(500))
    canonical_url: Mapped[Optional[str]] = mapped_column(String(500))
    og_image: Mapped[Optional[str]] = mapped_column(String(500))

    # Structure
    template: Mapped[Optional[str]] = mapped_column(String(100), default="default")
    layout_config: Mapped[Optional[dict]] = mapped_column(JSON)
    sections: Mapped[Optional[dict]] = mapped_column(JSON)  # Sections de la page

    # Publication
    status: Mapped[Optional[str]] = mapped_column(Enum(PublishStatus), default=PublishStatus.DRAFT)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Navigation
    parent_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("site_pages.id"))
    sort_order: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    show_in_menu: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    show_in_footer: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Langue
    language: Mapped[Optional[str]] = mapped_column(String(5), default="fr")
    translations: Mapped[Optional[dict]] = mapped_column(JSON)  # {lang: page_id}

    # Statistiques
    view_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Flags
    is_homepage: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_system: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    requires_auth: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    # Relations
    children = relationship("SitePage", backref="parent", remote_side=[id])


class BlogPost(Base):
    """Articles de blog."""
    __tablename__ = "blog_posts"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    slug: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)
    content_type: Mapped[Optional[str]] = mapped_column(Enum(ContentType), default=ContentType.ARTICLE)

    # Contenu
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(String(500))
    content: Mapped[Optional[str]] = mapped_column(Text)
    excerpt: Mapped[Optional[str]] = mapped_column(Text)

    # Médias
    featured_image: Mapped[Optional[str]] = mapped_column(String(500))
    gallery: Mapped[Optional[dict]] = mapped_column(JSON)  # [{"url": "...", "caption": "..."}]

    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(255))
    meta_description: Mapped[Optional[str]] = mapped_column(Text)
    meta_keywords: Mapped[Optional[str]] = mapped_column(String(500))

    # Catégorisation
    category: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON)  # ["tag1", "tag2"]

    # Auteur
    author_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    author_name: Mapped[Optional[str]] = mapped_column(String(255))
    author_avatar: Mapped[Optional[str]] = mapped_column(String(500))
    author_bio: Mapped[Optional[str]] = mapped_column(Text)

    # Publication
    status: Mapped[Optional[str]] = mapped_column(Enum(PublishStatus), default=PublishStatus.DRAFT)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Langue
    language: Mapped[Optional[str]] = mapped_column(String(5), default="fr")
    translations: Mapped[Optional[dict]] = mapped_column(JSON)

    # Engagement
    view_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    like_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    share_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    comment_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Temps de lecture estimé (minutes)
    reading_time: Mapped[Optional[int]] = mapped_column(Integer)

    # Flags
    is_featured: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_pinned: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    allow_comments: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())


class Testimonial(Base):
    """Témoignages clients."""
    __tablename__ = "testimonials"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Client
    client_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    client_title: Mapped[Optional[str]] = mapped_column(String(255))
    client_company: Mapped[Optional[str]] = mapped_column(String(255))
    client_logo: Mapped[Optional[str]] = mapped_column(String(500))
    client_avatar: Mapped[Optional[str]] = mapped_column(String(500))

    # Témoignage
    quote: Mapped[str] = mapped_column(Text)
    full_testimonial: Mapped[Optional[str]] = mapped_column(Text)

    # Contexte
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    use_case: Mapped[Optional[str]] = mapped_column(String(255))
    modules_used: Mapped[Optional[dict]] = mapped_column(JSON)  # ["M1", "M3", "M5"]

    # Métriques
    metrics: Mapped[Optional[dict]] = mapped_column(JSON)  # [{"label": "ROI", "value": "+35%"}]

    # Médias
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    case_study_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Publication
    status: Mapped[Optional[str]] = mapped_column(Enum(PublishStatus), default=PublishStatus.DRAFT)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Notation
    rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5

    # Affichage
    sort_order: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    is_featured: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    show_on_homepage: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Langue
    language: Mapped[Optional[str]] = mapped_column(String(5), default="fr")

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())


class ContactSubmission(Base):
    """Soumissions de formulaires de contact."""
    __tablename__ = "contact_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Catégorie
    form_category: Mapped[Optional[str]] = mapped_column(Enum(FormCategory), nullable=False)

    # Contact
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    company: Mapped[Optional[str]] = mapped_column(String(255))
    job_title: Mapped[Optional[str]] = mapped_column(String(255))

    # Message
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    message: Mapped[Optional[str]] = mapped_column(Text)

    # Contexte
    source_page: Mapped[Optional[str]] = mapped_column(String(500))
    utm_source: Mapped[Optional[str]] = mapped_column(String(100))
    utm_medium: Mapped[Optional[str]] = mapped_column(String(100))
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(100))
    referrer: Mapped[Optional[str]] = mapped_column(String(500))

    # Intérêts
    interested_modules: Mapped[Optional[dict]] = mapped_column(JSON)  # ["M1", "M5"]
    company_size: Mapped[Optional[str]] = mapped_column(String(50))  # "1-10", "11-50", etc.
    timeline: Mapped[Optional[str]] = mapped_column(String(100))
    budget: Mapped[Optional[str]] = mapped_column(String(100))

    # Données additionnelles
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON)

    # Statut
    status: Mapped[Optional[str]] = mapped_column(Enum(SubmissionStatus), default=SubmissionStatus.NEW)

    # Assignation
    assigned_to: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    # Réponse
    response: Mapped[Optional[str]] = mapped_column(Text)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    responded_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    # Suivi
    notes: Mapped[Optional[str]] = mapped_column(Text)
    follow_up_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Consentements
    consent_marketing: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    consent_newsletter: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    consent_privacy: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    # Anti-spam
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    honeypot: Mapped[Optional[str]] = mapped_column(String(100))  # Anti-spam

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NewsletterSubscriber(Base):
    """Abonnés newsletter."""
    __tablename__ = "newsletter_subscribers"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Contact
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    company: Mapped[Optional[str]] = mapped_column(String(255))

    # Préférences
    language: Mapped[Optional[str]] = mapped_column(String(5), default="fr")
    interests: Mapped[Optional[dict]] = mapped_column(JSON)  # ["product_updates", "blog", "events"]
    frequency: Mapped[Optional[str]] = mapped_column(String(50), default="weekly")  # daily, weekly, monthly

    # Statut
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    is_verified: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Tokens
    verification_token: Mapped[Optional[str]] = mapped_column(String(255))
    unsubscribe_token: Mapped[Optional[str]] = mapped_column(String(255))

    # Dates
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    unsubscribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_email_sent: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Source
    source: Mapped[Optional[str]] = mapped_column(String(100))  # form, import, api
    source_page: Mapped[Optional[str]] = mapped_column(String(500))

    # Statistiques
    emails_received: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    emails_opened: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    emails_clicked: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Consentement
    gdpr_consent: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    consent_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SiteMedia(Base):
    """Médiathèque du site."""
    __tablename__ = "site_media"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Fichier
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    original_name: Mapped[Optional[str]] = mapped_column(String(255))
    media_type: Mapped[Optional[str]] = mapped_column(Enum(MediaType), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))

    # Stockage
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)  # bytes

    # Dimensions (images/vidéos)
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    duration: Mapped[Optional[int]] = mapped_column(Integer)  # secondes (vidéo/audio)

    # Optimisation
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    optimized_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Métadonnées
    alt_text: Mapped[Optional[str]] = mapped_column(String(255))
    title: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    caption: Mapped[Optional[str]] = mapped_column(Text)

    # Organisation
    folder: Mapped[Optional[str]] = mapped_column(String(255), default="/")
    tags: Mapped[Optional[dict]] = mapped_column(JSON)

    # Utilisation
    usage_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    used_in: Mapped[Optional[dict]] = mapped_column(JSON)  # [{"type": "page", "id": 1}]

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())


class SiteSEO(Base):
    """Configuration SEO globale."""
    __tablename__ = "site_seo"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Meta globales
    site_title: Mapped[Optional[str]] = mapped_column(String(255))
    site_description: Mapped[Optional[str]] = mapped_column(Text)
    site_keywords: Mapped[Optional[str]] = mapped_column(String(500))

    # Open Graph
    og_site_name: Mapped[Optional[str]] = mapped_column(String(255))
    og_default_image: Mapped[Optional[str]] = mapped_column(String(500))
    og_locale: Mapped[Optional[str]] = mapped_column(String(10), default="fr_FR")

    # Twitter
    twitter_card: Mapped[Optional[str]] = mapped_column(String(50), default="summary_large_image")
    twitter_site: Mapped[Optional[str]] = mapped_column(String(100))
    twitter_creator: Mapped[Optional[str]] = mapped_column(String(100))

    # Vérifications
    google_site_verification: Mapped[Optional[str]] = mapped_column(String(255))
    bing_site_verification: Mapped[Optional[str]] = mapped_column(String(255))

    # Schema.org
    organization_schema: Mapped[Optional[dict]] = mapped_column(JSON)
    local_business_schema: Mapped[Optional[dict]] = mapped_column(JSON)

    # Robots
    robots_txt: Mapped[Optional[str]] = mapped_column(Text)
    sitemap_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Analytics
    google_analytics_id: Mapped[Optional[str]] = mapped_column(String(50))
    google_tag_manager_id: Mapped[Optional[str]] = mapped_column(String(50))
    facebook_pixel_id: Mapped[Optional[str]] = mapped_column(String(50))

    # Autres scripts
    head_scripts: Mapped[Optional[str]] = mapped_column(Text)
    body_scripts: Mapped[Optional[str]] = mapped_column(Text)

    # 301 Redirects
    redirects: Mapped[Optional[dict]] = mapped_column(JSON)  # [{"from": "/old", "to": "/new"}]

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())


class SiteAnalytics(Base):
    """Données analytics agrégées."""
    __tablename__ = "site_analytics"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Période
    date: Mapped[datetime] = mapped_column(DateTime index=True)
    period: Mapped[Optional[str]] = mapped_column(String(20), default="daily")  # daily, weekly, monthly

    # Trafic
    page_views: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    unique_visitors: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    sessions: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Comportement
    bounce_rate: Mapped[Optional[float]] = mapped_column(Float)
    avg_session_duration: Mapped[Optional[int]] = mapped_column(Integer)  # secondes
    pages_per_session: Mapped[Optional[float]] = mapped_column(Float)

    # Sources
    traffic_sources: Mapped[Optional[dict]] = mapped_column(JSON)  # {"organic": 100, "direct": 50}
    referrers: Mapped[Optional[dict]] = mapped_column(JSON)  # {"google.com": 80}

    # Géographie
    countries: Mapped[Optional[dict]] = mapped_column(JSON)  # {"FR": 500, "BE": 100}
    cities: Mapped[Optional[dict]] = mapped_column(JSON)

    # Appareils
    devices: Mapped[Optional[dict]] = mapped_column(JSON)  # {"desktop": 60, "mobile": 35}
    browsers: Mapped[Optional[dict]] = mapped_column(JSON)

    # Pages populaires
    top_pages: Mapped[Optional[dict]] = mapped_column(JSON)  # [{"url": "/", "views": 100}]

    # Conversions
    form_submissions: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    newsletter_signups: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    demo_requests: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Blog
    blog_views: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    top_posts: Mapped[Optional[dict]] = mapped_column(JSON)

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
