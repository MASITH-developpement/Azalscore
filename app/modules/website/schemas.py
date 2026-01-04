"""
AZALS MODULE T8 - Schémas Site Web
===================================

Schémas Pydantic pour l'API du site web.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import json


# ============================================================================
# ENUMS
# ============================================================================

class PageType(str):
    LANDING = "LANDING"
    PRODUCT = "PRODUCT"
    PRICING = "PRICING"
    ABOUT = "ABOUT"
    CONTACT = "CONTACT"
    BLOG = "BLOG"
    DOCUMENTATION = "DOCUMENTATION"
    LEGAL = "LEGAL"
    CUSTOM = "CUSTOM"


class PublishStatus(str):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class ContentType(str):
    ARTICLE = "ARTICLE"
    NEWS = "NEWS"
    CASE_STUDY = "CASE_STUDY"
    TESTIMONIAL = "TESTIMONIAL"
    FAQ = "FAQ"
    TUTORIAL = "TUTORIAL"
    RELEASE_NOTE = "RELEASE_NOTE"


class FormCategory(str):
    CONTACT = "CONTACT"
    DEMO_REQUEST = "DEMO_REQUEST"
    QUOTE_REQUEST = "QUOTE_REQUEST"
    SUPPORT = "SUPPORT"
    NEWSLETTER = "NEWSLETTER"
    FEEDBACK = "FEEDBACK"


class SubmissionStatus(str):
    NEW = "NEW"
    READ = "READ"
    REPLIED = "REPLIED"
    CLOSED = "CLOSED"
    SPAM = "SPAM"


class MediaType(str):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    AUDIO = "AUDIO"


# ============================================================================
# PAGES
# ============================================================================

class SitePageCreate(BaseModel):
    """Création d'une page."""
    slug: str = Field(..., min_length=1, max_length=255)
    page_type: str = "CUSTOM"
    title: str = Field(..., min_length=1, max_length=255)
    subtitle: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    hero_video: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    canonical_url: Optional[str] = None
    og_image: Optional[str] = None
    template: str = "default"
    layout_config: Optional[Dict[str, Any]] = None
    sections: Optional[List[Dict[str, Any]]] = None
    parent_id: Optional[int] = None
    sort_order: int = 0
    show_in_menu: bool = True
    show_in_footer: bool = False
    language: str = "fr"
    is_homepage: bool = False
    requires_auth: bool = False


class SitePageUpdate(BaseModel):
    """Mise à jour d'une page."""
    slug: Optional[str] = None
    page_type: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    hero_video: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    canonical_url: Optional[str] = None
    og_image: Optional[str] = None
    template: Optional[str] = None
    layout_config: Optional[Dict[str, Any]] = None
    sections: Optional[List[Dict[str, Any]]] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    show_in_menu: Optional[bool] = None
    show_in_footer: Optional[bool] = None
    language: Optional[str] = None
    requires_auth: Optional[bool] = None


class SitePageResponse(BaseModel):
    """Réponse page."""
    id: int
    tenant_id: str
    slug: str
    page_type: str
    title: str
    subtitle: Optional[str]
    content: Optional[str]
    excerpt: Optional[str]
    featured_image: Optional[str]
    hero_video: Optional[str]
    meta_title: Optional[str]
    meta_description: Optional[str]
    meta_keywords: Optional[str]
    canonical_url: Optional[str]
    og_image: Optional[str]
    template: str
    layout_config: Optional[Dict[str, Any]]
    sections: Optional[List[Dict[str, Any]]]
    status: str
    published_at: Optional[datetime]
    parent_id: Optional[int]
    sort_order: int
    show_in_menu: bool
    show_in_footer: bool
    language: str
    translations: Optional[Dict[str, int]]
    view_count: int
    is_homepage: bool
    is_system: bool
    requires_auth: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]

    @field_validator("layout_config", "sections", "translations", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    class Config:
        from_attributes = True


class SitePageListResponse(BaseModel):
    """Liste de pages."""
    id: int
    slug: str
    page_type: str
    title: str
    status: str
    sort_order: int
    show_in_menu: bool
    is_homepage: bool
    view_count: int
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# BLOG
# ============================================================================

class BlogPostCreate(BaseModel):
    """Création d'un article."""
    slug: str = Field(..., min_length=1, max_length=255)
    content_type: str = "ARTICLE"
    title: str = Field(..., min_length=1, max_length=255)
    subtitle: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    gallery: Optional[List[Dict[str, Any]]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    author_name: Optional[str] = None
    author_avatar: Optional[str] = None
    author_bio: Optional[str] = None
    language: str = "fr"
    reading_time: Optional[int] = None
    is_featured: bool = False
    is_pinned: bool = False
    allow_comments: bool = True


class BlogPostUpdate(BaseModel):
    """Mise à jour d'un article."""
    slug: Optional[str] = None
    content_type: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    gallery: Optional[List[Dict[str, Any]]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    author_name: Optional[str] = None
    author_avatar: Optional[str] = None
    author_bio: Optional[str] = None
    language: Optional[str] = None
    reading_time: Optional[int] = None
    is_featured: Optional[bool] = None
    is_pinned: Optional[bool] = None
    allow_comments: Optional[bool] = None


class BlogPostResponse(BaseModel):
    """Réponse article."""
    id: int
    tenant_id: str
    slug: str
    content_type: str
    title: str
    subtitle: Optional[str]
    content: Optional[str]
    excerpt: Optional[str]
    featured_image: Optional[str]
    gallery: Optional[List[Dict[str, Any]]]
    meta_title: Optional[str]
    meta_description: Optional[str]
    meta_keywords: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    author_id: Optional[int]
    author_name: Optional[str]
    author_avatar: Optional[str]
    author_bio: Optional[str]
    status: str
    published_at: Optional[datetime]
    language: str
    translations: Optional[Dict[str, int]]
    view_count: int
    like_count: int
    share_count: int
    comment_count: int
    reading_time: Optional[int]
    is_featured: bool
    is_pinned: bool
    allow_comments: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]

    @field_validator("gallery", "tags", "translations", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    class Config:
        from_attributes = True


class BlogPostListResponse(BaseModel):
    """Liste d'articles."""
    id: int
    slug: str
    content_type: str
    title: str
    excerpt: Optional[str]
    featured_image: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    author_name: Optional[str]
    status: str
    published_at: Optional[datetime]
    view_count: int
    reading_time: Optional[int]
    is_featured: bool
    is_pinned: bool

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    class Config:
        from_attributes = True


# ============================================================================
# TESTIMONIALS
# ============================================================================

class TestimonialCreate(BaseModel):
    """Création d'un témoignage."""
    client_name: str = Field(..., min_length=1, max_length=255)
    client_title: Optional[str] = None
    client_company: Optional[str] = None
    client_logo: Optional[str] = None
    client_avatar: Optional[str] = None
    quote: str = Field(..., min_length=10)
    full_testimonial: Optional[str] = None
    industry: Optional[str] = None
    use_case: Optional[str] = None
    modules_used: Optional[List[str]] = None
    metrics: Optional[List[Dict[str, Any]]] = None
    video_url: Optional[str] = None
    case_study_url: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    sort_order: int = 0
    is_featured: bool = False
    show_on_homepage: bool = False
    language: str = "fr"


class TestimonialUpdate(BaseModel):
    """Mise à jour d'un témoignage."""
    client_name: Optional[str] = None
    client_title: Optional[str] = None
    client_company: Optional[str] = None
    client_logo: Optional[str] = None
    client_avatar: Optional[str] = None
    quote: Optional[str] = None
    full_testimonial: Optional[str] = None
    industry: Optional[str] = None
    use_case: Optional[str] = None
    modules_used: Optional[List[str]] = None
    metrics: Optional[List[Dict[str, Any]]] = None
    video_url: Optional[str] = None
    case_study_url: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    sort_order: Optional[int] = None
    is_featured: Optional[bool] = None
    show_on_homepage: Optional[bool] = None


class TestimonialResponse(BaseModel):
    """Réponse témoignage."""
    id: int
    tenant_id: str
    client_name: str
    client_title: Optional[str]
    client_company: Optional[str]
    client_logo: Optional[str]
    client_avatar: Optional[str]
    quote: str
    full_testimonial: Optional[str]
    industry: Optional[str]
    use_case: Optional[str]
    modules_used: Optional[List[str]]
    metrics: Optional[List[Dict[str, Any]]]
    video_url: Optional[str]
    case_study_url: Optional[str]
    status: str
    published_at: Optional[datetime]
    rating: Optional[int]
    sort_order: int
    is_featured: bool
    show_on_homepage: bool
    language: str
    created_at: datetime
    updated_at: datetime

    @field_validator("modules_used", "metrics", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    class Config:
        from_attributes = True


# ============================================================================
# CONTACT
# ============================================================================

class ContactSubmissionCreate(BaseModel):
    """Création d'une soumission de contact."""
    form_category: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str = Field(..., min_length=5, max_length=255)
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    subject: Optional[str] = None
    message: Optional[str] = None
    source_page: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    interested_modules: Optional[List[str]] = None
    company_size: Optional[str] = None
    timeline: Optional[str] = None
    budget: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    consent_marketing: bool = False
    consent_newsletter: bool = False
    consent_privacy: bool = True


class ContactSubmissionUpdate(BaseModel):
    """Mise à jour d'une soumission."""
    status: Optional[str] = None
    assigned_to: Optional[int] = None
    response: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[datetime] = None


class ContactSubmissionResponse(BaseModel):
    """Réponse soumission."""
    id: int
    tenant_id: str
    form_category: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: str
    phone: Optional[str]
    company: Optional[str]
    job_title: Optional[str]
    subject: Optional[str]
    message: Optional[str]
    source_page: Optional[str]
    utm_source: Optional[str]
    utm_medium: Optional[str]
    utm_campaign: Optional[str]
    referrer: Optional[str]
    interested_modules: Optional[List[str]]
    company_size: Optional[str]
    timeline: Optional[str]
    budget: Optional[str]
    custom_fields: Optional[Dict[str, Any]]
    status: str
    assigned_to: Optional[int]
    response: Optional[str]
    responded_at: Optional[datetime]
    responded_by: Optional[int]
    notes: Optional[str]
    follow_up_date: Optional[datetime]
    consent_marketing: bool
    consent_newsletter: bool
    consent_privacy: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("interested_modules", "custom_fields", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    class Config:
        from_attributes = True


# ============================================================================
# NEWSLETTER
# ============================================================================

class NewsletterSubscribeRequest(BaseModel):
    """Inscription newsletter."""
    email: str = Field(..., min_length=5, max_length=255)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    language: str = "fr"
    interests: Optional[List[str]] = None
    frequency: str = "weekly"
    source: Optional[str] = None
    source_page: Optional[str] = None
    gdpr_consent: bool = True


class NewsletterUnsubscribeRequest(BaseModel):
    """Désinscription newsletter."""
    token: str


class NewsletterSubscriberResponse(BaseModel):
    """Réponse abonné."""
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    company: Optional[str]
    language: str
    interests: Optional[List[str]]
    frequency: str
    is_active: bool
    is_verified: bool
    verified_at: Optional[datetime]
    source: Optional[str]
    emails_received: int
    emails_opened: int
    emails_clicked: int
    created_at: datetime

    @field_validator("interests", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    class Config:
        from_attributes = True


# ============================================================================
# MEDIA
# ============================================================================

class SiteMediaCreate(BaseModel):
    """Création d'un média."""
    filename: str = Field(..., min_length=1, max_length=255)
    original_name: Optional[str] = None
    media_type: str
    mime_type: Optional[str] = None
    url: str = Field(..., min_length=1, max_length=500)
    storage_path: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    optimized_url: Optional[str] = None
    alt_text: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    caption: Optional[str] = None
    folder: str = "/"
    tags: Optional[List[str]] = None


class SiteMediaUpdate(BaseModel):
    """Mise à jour d'un média."""
    alt_text: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    caption: Optional[str] = None
    folder: Optional[str] = None
    tags: Optional[List[str]] = None


class SiteMediaResponse(BaseModel):
    """Réponse média."""
    id: int
    tenant_id: str
    filename: str
    original_name: Optional[str]
    media_type: str
    mime_type: Optional[str]
    url: str
    storage_path: Optional[str]
    file_size: Optional[int]
    width: Optional[int]
    height: Optional[int]
    duration: Optional[int]
    thumbnail_url: Optional[str]
    optimized_url: Optional[str]
    alt_text: Optional[str]
    title: Optional[str]
    description: Optional[str]
    caption: Optional[str]
    folder: str
    tags: Optional[List[str]]
    usage_count: int
    created_at: datetime
    updated_at: datetime

    @field_validator("tags", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    class Config:
        from_attributes = True


# ============================================================================
# SEO
# ============================================================================

class SiteSEOUpdate(BaseModel):
    """Mise à jour SEO."""
    site_title: Optional[str] = None
    site_description: Optional[str] = None
    site_keywords: Optional[str] = None
    og_site_name: Optional[str] = None
    og_default_image: Optional[str] = None
    og_locale: Optional[str] = None
    twitter_card: Optional[str] = None
    twitter_site: Optional[str] = None
    twitter_creator: Optional[str] = None
    google_site_verification: Optional[str] = None
    bing_site_verification: Optional[str] = None
    organization_schema: Optional[Dict[str, Any]] = None
    local_business_schema: Optional[Dict[str, Any]] = None
    robots_txt: Optional[str] = None
    sitemap_url: Optional[str] = None
    google_analytics_id: Optional[str] = None
    google_tag_manager_id: Optional[str] = None
    facebook_pixel_id: Optional[str] = None
    head_scripts: Optional[str] = None
    body_scripts: Optional[str] = None
    redirects: Optional[List[Dict[str, str]]] = None


class SiteSEOResponse(BaseModel):
    """Réponse SEO."""
    id: int
    tenant_id: str
    site_title: Optional[str]
    site_description: Optional[str]
    site_keywords: Optional[str]
    og_site_name: Optional[str]
    og_default_image: Optional[str]
    og_locale: Optional[str]
    twitter_card: Optional[str]
    twitter_site: Optional[str]
    twitter_creator: Optional[str]
    google_site_verification: Optional[str]
    bing_site_verification: Optional[str]
    organization_schema: Optional[Dict[str, Any]]
    local_business_schema: Optional[Dict[str, Any]]
    robots_txt: Optional[str]
    sitemap_url: Optional[str]
    google_analytics_id: Optional[str]
    google_tag_manager_id: Optional[str]
    facebook_pixel_id: Optional[str]
    head_scripts: Optional[str]
    body_scripts: Optional[str]
    redirects: Optional[List[Dict[str, str]]]
    updated_at: datetime

    @field_validator("organization_schema", "local_business_schema", "redirects", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    class Config:
        from_attributes = True


# ============================================================================
# ANALYTICS
# ============================================================================

class SiteAnalyticsResponse(BaseModel):
    """Réponse analytics."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    id: int
    tenant_id: str
    analytics_date: datetime = Field(..., alias="date")
    period: str
    page_views: int
    unique_visitors: int
    sessions: int
    bounce_rate: Optional[float]
    avg_session_duration: Optional[int]
    pages_per_session: Optional[float]
    traffic_sources: Optional[Dict[str, int]]
    referrers: Optional[Dict[str, int]]
    countries: Optional[Dict[str, int]]
    cities: Optional[Dict[str, int]]
    devices: Optional[Dict[str, int]]
    browsers: Optional[Dict[str, int]]
    top_pages: Optional[List[Dict[str, Any]]]
    form_submissions: int
    newsletter_signups: int
    demo_requests: int
    blog_views: int
    top_posts: Optional[List[Dict[str, Any]]]

    @field_validator("traffic_sources", "referrers", "countries", "cities",
                     "devices", "browsers", "top_pages", "top_posts", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    class Config:
        from_attributes = True


class AnalyticsDashboardResponse(BaseModel):
    """Dashboard analytics."""
    period: str
    total_page_views: int
    total_unique_visitors: int
    total_sessions: int
    avg_bounce_rate: Optional[float]
    total_form_submissions: int
    total_newsletter_signups: int
    total_demo_requests: int
    total_blog_views: int
    traffic_by_source: Dict[str, int]
    top_pages: List[Dict[str, Any]]
    top_posts: List[Dict[str, Any]]
    daily_stats: List[Dict[str, Any]]


# ============================================================================
# PUBLICATION
# ============================================================================

class PublishRequest(BaseModel):
    """Demande de publication."""
    publish: bool = True
    schedule_at: Optional[datetime] = None


# ============================================================================
# SITE MENU
# ============================================================================

class SiteMenuItemResponse(BaseModel):
    """Item de menu du site."""
    id: int
    slug: str
    title: str
    page_type: str
    sort_order: int
    parent_id: Optional[int]
    children: List["SiteMenuItemResponse"] = []

    class Config:
        from_attributes = True


SiteMenuItemResponse.model_rebuild()


# ============================================================================
# PUBLIC SITE CONFIG
# ============================================================================

class PublicSiteConfigResponse(BaseModel):
    """Configuration publique du site."""
    site_title: str
    site_description: Optional[str]
    og_image: Optional[str]
    menu: List[SiteMenuItemResponse]
    footer_pages: List[SiteMenuItemResponse]
    analytics_enabled: bool
    language: str
