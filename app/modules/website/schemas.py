"""
AZALS MODULE T8 - Schémas Site Web
===================================

Schémas Pydantic pour l'API du site web.
"""


import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    subtitle: str | None = None
    content: str | None = None
    excerpt: str | None = None
    featured_image: str | None = None
    hero_video: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    meta_keywords: str | None = None
    canonical_url: str | None = None
    og_image: str | None = None
    template: str = "default"
    layout_config: dict[str, Any] | None = None
    sections: list[dict[str, Any]] | None = None
    parent_id: int | None = None
    sort_order: int = 0
    show_in_menu: bool = True
    show_in_footer: bool = False
    language: str = "fr"
    is_homepage: bool = False
    requires_auth: bool = False


class SitePageUpdate(BaseModel):
    """Mise à jour d'une page."""
    slug: str | None = None
    page_type: str | None = None
    title: str | None = None
    subtitle: str | None = None
    content: str | None = None
    excerpt: str | None = None
    featured_image: str | None = None
    hero_video: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    meta_keywords: str | None = None
    canonical_url: str | None = None
    og_image: str | None = None
    template: str | None = None
    layout_config: dict[str, Any] | None = None
    sections: list[dict[str, Any]] | None = None
    parent_id: int | None = None
    sort_order: int | None = None
    show_in_menu: bool | None = None
    show_in_footer: bool | None = None
    language: str | None = None
    requires_auth: bool | None = None


class SitePageResponse(BaseModel):
    """Réponse page."""
    id: int
    tenant_id: str
    slug: str
    page_type: str
    title: str
    subtitle: str | None
    content: str | None
    excerpt: str | None
    featured_image: str | None
    hero_video: str | None
    meta_title: str | None
    meta_description: str | None
    meta_keywords: str | None
    canonical_url: str | None
    og_image: str | None
    template: str
    layout_config: dict[str, Any] | None
    sections: list[dict[str, Any]] | None
    status: str
    published_at: datetime | None
    parent_id: int | None
    sort_order: int
    show_in_menu: bool
    show_in_footer: bool
    language: str
    translations: dict[str, int] | None
    view_count: int
    is_homepage: bool
    is_system: bool
    requires_auth: bool
    created_at: datetime
    updated_at: datetime
    created_by: int | None

    @field_validator("layout_config", "sections", "translations", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# BLOG
# ============================================================================

class BlogPostCreate(BaseModel):
    """Création d'un article."""
    slug: str = Field(..., min_length=1, max_length=255)
    content_type: str = "ARTICLE"
    title: str = Field(..., min_length=1, max_length=255)
    subtitle: str | None = None
    content: str | None = None
    excerpt: str | None = None
    featured_image: str | None = None
    gallery: list[dict[str, Any]] | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    meta_keywords: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    author_name: str | None = None
    author_avatar: str | None = None
    author_bio: str | None = None
    language: str = "fr"
    reading_time: int | None = None
    is_featured: bool = False
    is_pinned: bool = False
    allow_comments: bool = True


class BlogPostUpdate(BaseModel):
    """Mise à jour d'un article."""
    slug: str | None = None
    content_type: str | None = None
    title: str | None = None
    subtitle: str | None = None
    content: str | None = None
    excerpt: str | None = None
    featured_image: str | None = None
    gallery: list[dict[str, Any]] | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    meta_keywords: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    author_name: str | None = None
    author_avatar: str | None = None
    author_bio: str | None = None
    language: str | None = None
    reading_time: int | None = None
    is_featured: bool | None = None
    is_pinned: bool | None = None
    allow_comments: bool | None = None


class BlogPostResponse(BaseModel):
    """Réponse article."""
    id: int
    tenant_id: str
    slug: str
    content_type: str
    title: str
    subtitle: str | None
    content: str | None
    excerpt: str | None
    featured_image: str | None
    gallery: list[dict[str, Any]] | None
    meta_title: str | None
    meta_description: str | None
    meta_keywords: str | None
    category: str | None
    tags: list[str] | None
    author_id: int | None
    author_name: str | None
    author_avatar: str | None
    author_bio: str | None
    status: str
    published_at: datetime | None
    language: str
    translations: dict[str, int] | None
    view_count: int
    like_count: int
    share_count: int
    comment_count: int
    reading_time: int | None
    is_featured: bool
    is_pinned: bool
    allow_comments: bool
    created_at: datetime
    updated_at: datetime
    created_by: int | None

    @field_validator("gallery", "tags", "translations", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    model_config = ConfigDict(from_attributes=True)


class BlogPostListResponse(BaseModel):
    """Liste d'articles."""
    id: int
    slug: str
    content_type: str
    title: str
    excerpt: str | None
    featured_image: str | None
    category: str | None
    tags: list[str] | None
    author_name: str | None
    status: str
    published_at: datetime | None
    view_count: int
    reading_time: int | None
    is_featured: bool
    is_pinned: bool

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TESTIMONIALS
# ============================================================================

class TestimonialCreate(BaseModel):
    """Création d'un témoignage."""
    client_name: str = Field(..., min_length=1, max_length=255)
    client_title: str | None = None
    client_company: str | None = None
    client_logo: str | None = None
    client_avatar: str | None = None
    quote: str = Field(..., min_length=10)
    full_testimonial: str | None = None
    industry: str | None = None
    use_case: str | None = None
    modules_used: list[str] | None = None
    metrics: list[dict[str, Any]] | None = None
    video_url: str | None = None
    case_study_url: str | None = None
    rating: int | None = Field(None, ge=1, le=5)
    sort_order: int = 0
    is_featured: bool = False
    show_on_homepage: bool = False
    language: str = "fr"


class TestimonialUpdate(BaseModel):
    """Mise à jour d'un témoignage."""
    client_name: str | None = None
    client_title: str | None = None
    client_company: str | None = None
    client_logo: str | None = None
    client_avatar: str | None = None
    quote: str | None = None
    full_testimonial: str | None = None
    industry: str | None = None
    use_case: str | None = None
    modules_used: list[str] | None = None
    metrics: list[dict[str, Any]] | None = None
    video_url: str | None = None
    case_study_url: str | None = None
    rating: int | None = Field(None, ge=1, le=5)
    sort_order: int | None = None
    is_featured: bool | None = None
    show_on_homepage: bool | None = None


class TestimonialResponse(BaseModel):
    """Réponse témoignage."""
    id: int
    tenant_id: str
    client_name: str
    client_title: str | None
    client_company: str | None
    client_logo: str | None
    client_avatar: str | None
    quote: str
    full_testimonial: str | None
    industry: str | None
    use_case: str | None
    modules_used: list[str] | None
    metrics: list[dict[str, Any]] | None
    video_url: str | None
    case_study_url: str | None
    status: str
    published_at: datetime | None
    rating: int | None
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

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CONTACT
# ============================================================================

class ContactSubmissionCreate(BaseModel):
    """Création d'une soumission de contact."""
    form_category: str
    first_name: str | None = None
    last_name: str | None = None
    email: str = Field(..., min_length=5, max_length=255)
    phone: str | None = None
    company: str | None = None
    job_title: str | None = None
    subject: str | None = None
    message: str | None = None
    source_page: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    interested_modules: list[str] | None = None
    company_size: str | None = None
    timeline: str | None = None
    budget: str | None = None
    custom_fields: dict[str, Any] | None = None
    consent_marketing: bool = False
    consent_newsletter: bool = False
    consent_privacy: bool = True


class ContactSubmissionUpdate(BaseModel):
    """Mise à jour d'une soumission."""
    status: str | None = None
    assigned_to: int | None = None
    response: str | None = None
    notes: str | None = None
    follow_up_date: datetime | None = None


class ContactSubmissionResponse(BaseModel):
    """Réponse soumission."""
    id: int
    tenant_id: str
    form_category: str
    first_name: str | None
    last_name: str | None
    email: str
    phone: str | None
    company: str | None
    job_title: str | None
    subject: str | None
    message: str | None
    source_page: str | None
    utm_source: str | None
    utm_medium: str | None
    utm_campaign: str | None
    referrer: str | None
    interested_modules: list[str] | None
    company_size: str | None
    timeline: str | None
    budget: str | None
    custom_fields: dict[str, Any] | None
    status: str
    assigned_to: int | None
    response: str | None
    responded_at: datetime | None
    responded_by: int | None
    notes: str | None
    follow_up_date: datetime | None
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

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# NEWSLETTER
# ============================================================================

class NewsletterSubscribeRequest(BaseModel):
    """Inscription newsletter."""
    email: str = Field(..., min_length=5, max_length=255)
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    language: str = "fr"
    interests: list[str] | None = None
    frequency: str = "weekly"
    source: str | None = None
    source_page: str | None = None
    gdpr_consent: bool = True


class NewsletterUnsubscribeRequest(BaseModel):
    """Désinscription newsletter."""
    token: str


class NewsletterSubscriberResponse(BaseModel):
    """Réponse abonné."""
    id: int
    email: str
    first_name: str | None
    last_name: str | None
    company: str | None
    language: str
    interests: list[str] | None
    frequency: str
    is_active: bool
    is_verified: bool
    verified_at: datetime | None
    source: str | None
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

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# MEDIA
# ============================================================================

class SiteMediaCreate(BaseModel):
    """Création d'un média."""
    filename: str = Field(..., min_length=1, max_length=255)
    original_name: str | None = None
    media_type: str
    mime_type: str | None = None
    url: str = Field(..., min_length=1, max_length=500)
    storage_path: str | None = None
    file_size: int | None = None
    width: int | None = None
    height: int | None = None
    duration: int | None = None
    thumbnail_url: str | None = None
    optimized_url: str | None = None
    alt_text: str | None = None
    title: str | None = None
    description: str | None = None
    caption: str | None = None
    folder: str = "/"
    tags: list[str] | None = None


class SiteMediaUpdate(BaseModel):
    """Mise à jour d'un média."""
    alt_text: str | None = None
    title: str | None = None
    description: str | None = None
    caption: str | None = None
    folder: str | None = None
    tags: list[str] | None = None


class SiteMediaResponse(BaseModel):
    """Réponse média."""
    id: int
    tenant_id: str
    filename: str
    original_name: str | None
    media_type: str
    mime_type: str | None
    url: str
    storage_path: str | None
    file_size: int | None
    width: int | None
    height: int | None
    duration: int | None
    thumbnail_url: str | None
    optimized_url: str | None
    alt_text: str | None
    title: str | None
    description: str | None
    caption: str | None
    folder: str
    tags: list[str] | None
    usage_count: int
    created_at: datetime
    updated_at: datetime

    @field_validator("tags", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SEO
# ============================================================================

class SiteSEOUpdate(BaseModel):
    """Mise à jour SEO."""
    site_title: str | None = None
    site_description: str | None = None
    site_keywords: str | None = None
    og_site_name: str | None = None
    og_default_image: str | None = None
    og_locale: str | None = None
    twitter_card: str | None = None
    twitter_site: str | None = None
    twitter_creator: str | None = None
    google_site_verification: str | None = None
    bing_site_verification: str | None = None
    organization_schema: dict[str, Any] | None = None
    local_business_schema: dict[str, Any] | None = None
    robots_txt: str | None = None
    sitemap_url: str | None = None
    google_analytics_id: str | None = None
    google_tag_manager_id: str | None = None
    facebook_pixel_id: str | None = None
    head_scripts: str | None = None
    body_scripts: str | None = None
    redirects: list[dict[str, str]] | None = None


class SiteSEOResponse(BaseModel):
    """Réponse SEO."""
    id: int
    tenant_id: str
    site_title: str | None
    site_description: str | None
    site_keywords: str | None
    og_site_name: str | None
    og_default_image: str | None
    og_locale: str | None
    twitter_card: str | None
    twitter_site: str | None
    twitter_creator: str | None
    google_site_verification: str | None
    bing_site_verification: str | None
    organization_schema: dict[str, Any] | None
    local_business_schema: dict[str, Any] | None
    robots_txt: str | None
    sitemap_url: str | None
    google_analytics_id: str | None
    google_tag_manager_id: str | None
    facebook_pixel_id: str | None
    head_scripts: str | None
    body_scripts: str | None
    redirects: list[dict[str, str]] | None
    updated_at: datetime

    @field_validator("organization_schema", "local_business_schema", "redirects", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ANALYTICS
# ============================================================================

class SiteAnalyticsResponse(BaseModel):
    """Réponse analytics."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True, from_attributes=True)

    id: int
    tenant_id: str
    analytics_date: datetime = Field(..., alias="date")
    period: str
    page_views: int
    unique_visitors: int
    sessions: int
    bounce_rate: float | None
    avg_session_duration: int | None
    pages_per_session: float | None
    traffic_sources: dict[str, int] | None
    referrers: dict[str, int] | None
    countries: dict[str, int] | None
    cities: dict[str, int] | None
    devices: dict[str, int] | None
    browsers: dict[str, int] | None
    top_pages: list[dict[str, Any]] | None
    form_submissions: int
    newsletter_signups: int
    demo_requests: int
    blog_views: int
    top_posts: list[dict[str, Any]] | None

    @field_validator("traffic_sources", "referrers", "countries", "cities",
                     "devices", "browsers", "top_pages", "top_posts", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v


class AnalyticsDashboardResponse(BaseModel):
    """Dashboard analytics."""
    period: str
    total_page_views: int
    total_unique_visitors: int
    total_sessions: int
    avg_bounce_rate: float | None
    total_form_submissions: int
    total_newsletter_signups: int
    total_demo_requests: int
    total_blog_views: int
    traffic_by_source: dict[str, int]
    top_pages: list[dict[str, Any]]
    top_posts: list[dict[str, Any]]
    daily_stats: list[dict[str, Any]]


# ============================================================================
# PUBLICATION
# ============================================================================

class PublishRequest(BaseModel):
    """Demande de publication."""
    publish: bool = True
    schedule_at: datetime | None = None


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
    parent_id: int | None
    children: list[SiteMenuItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


SiteMenuItemResponse.model_rebuild()


# ============================================================================
# PUBLIC SITE CONFIG
# ============================================================================

class PublicSiteConfigResponse(BaseModel):
    """Configuration publique du site."""
    site_title: str
    site_description: str | None
    og_image: str | None
    menu: list[SiteMenuItemResponse]
    footer_pages: list[SiteMenuItemResponse]
    analytics_enabled: bool
    language: str
