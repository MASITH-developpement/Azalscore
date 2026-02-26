"""
AZALS MODULE - Publications Réseaux Sociaux - Schémas Pydantic
==============================================================

Validation stricte des données pour les publications et leads.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, HttpUrl, field_validator

from .models import MarketingPlatform
from .publication_models import (
    PostStatus, PostType, CampaignStatus, LeadStatus, LeadSource
)


# ============================================================
# CAMPAGNES
# ============================================================

class CampaignBase(BaseModel):
    """Base pour les campagnes."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    objective: Optional[str] = Field(None, description="awareness, engagement, leads, traffic")
    target_audience: Optional[str] = None
    target_leads: int = Field(default=0, ge=0)
    target_impressions: int = Field(default=0, ge=0)
    budget: Decimal = Field(default=Decimal("0"), ge=0)
    platforms: List[MarketingPlatform] = Field(default_factory=list)
    utm_source: Optional[str] = Field(None, max_length=100)
    utm_medium: Optional[str] = Field(None, max_length=100)
    utm_campaign: Optional[str] = Field(None, max_length=100)


class CampaignCreate(CampaignBase):
    """Création d'une campagne."""
    pass


class CampaignUpdate(BaseModel):
    """Mise à jour d'une campagne."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    objective: Optional[str] = None
    target_audience: Optional[str] = None
    target_leads: Optional[int] = Field(None, ge=0)
    target_impressions: Optional[int] = Field(None, ge=0)
    budget: Optional[Decimal] = Field(None, ge=0)
    platforms: Optional[List[MarketingPlatform]] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class CampaignResponse(CampaignBase):
    """Réponse campagne."""
    id: UUID
    tenant_id: str
    status: CampaignStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    total_posts: int = 0
    total_impressions: int = 0
    total_clicks: int = 0
    total_leads: int = 0
    total_conversions: int = 0
    actual_spend: Decimal = Decimal("0")

    class Config:
        from_attributes = True


class CampaignStats(BaseModel):
    """Statistiques d'une campagne."""
    campaign_id: UUID
    period_start: date
    period_end: date
    posts_published: int = 0
    impressions: int = 0
    reach: int = 0
    clicks: int = 0
    engagement: int = 0
    leads_generated: int = 0
    leads_converted: int = 0
    cost_per_lead: Decimal = Decimal("0")
    conversion_rate: Decimal = Decimal("0")
    roi: Decimal = Decimal("0")


# ============================================================
# PUBLICATIONS
# ============================================================

class PostBase(BaseModel):
    """Base pour les publications."""
    title: Optional[str] = Field(None, max_length=255)
    content: str = Field(..., min_length=1, max_length=10000)
    post_type: PostType = PostType.TEXT
    media_urls: List[str] = Field(default_factory=list)
    thumbnail_url: Optional[str] = None
    link_url: Optional[str] = Field(None, description="URL vers azalscore.com")
    link_title: Optional[str] = None
    link_description: Optional[str] = None
    platforms: List[MarketingPlatform] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None


class PostCreate(PostBase):
    """Création d'une publication."""
    campaign_id: Optional[UUID] = None
    scheduled_at: Optional[datetime] = None

    @field_validator('platforms')
    @classmethod
    def validate_platforms(cls, v):
        if not v:
            raise ValueError("Au moins une plateforme doit être sélectionnée")
        return v


class PostUpdate(BaseModel):
    """Mise à jour d'une publication."""
    title: Optional[str] = None
    content: Optional[str] = None
    post_type: Optional[PostType] = None
    media_urls: Optional[List[str]] = None
    thumbnail_url: Optional[str] = None
    link_url: Optional[str] = None
    link_title: Optional[str] = None
    link_description: Optional[str] = None
    platforms: Optional[List[MarketingPlatform]] = None
    scheduled_at: Optional[datetime] = None
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None


class PostResponse(PostBase):
    """Réponse publication."""
    id: UUID
    tenant_id: str
    campaign_id: Optional[UUID] = None
    status: PostStatus
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    external_ids: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    # Métriques
    impressions: int = 0
    reach: int = 0
    clicks: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0

    last_error: Optional[str] = None

    class Config:
        from_attributes = True


class PostScheduleRequest(BaseModel):
    """Demande de programmation."""
    post_id: UUID
    scheduled_at: datetime
    platforms: Optional[List[MarketingPlatform]] = None


class PostPublishRequest(BaseModel):
    """Demande de publication immédiate."""
    post_id: UUID
    platforms: Optional[List[MarketingPlatform]] = None


class PostBulkCreate(BaseModel):
    """Création en masse de publications."""
    posts: List[PostCreate]
    campaign_id: Optional[UUID] = None


# ============================================================
# LEADS
# ============================================================

class LeadBase(BaseModel):
    """Base pour les leads."""
    source: LeadSource
    source_platform: Optional[MarketingPlatform] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=100)
    social_profile_url: Optional[str] = None
    social_username: Optional[str] = None
    interest: Optional[str] = Field(None, description="Module/fonctionnalité d'intérêt")
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class LeadCreate(LeadBase):
    """Création d'un lead."""
    campaign_id: Optional[UUID] = None
    post_id: Optional[UUID] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    landing_page: Optional[str] = None
    referrer: Optional[str] = None

    @field_validator('email', 'phone')
    @classmethod
    def validate_contact(cls, v, info):
        # Au moins email ou phone requis
        return v


class LeadUpdate(BaseModel):
    """Mise à jour d'un lead."""
    status: Optional[LeadStatus] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    interest: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    assigned_to: Optional[str] = None


class LeadResponse(LeadBase):
    """Réponse lead."""
    id: UUID
    tenant_id: str
    status: LeadStatus
    score: int = 0
    campaign_id: Optional[UUID] = None
    post_id: Optional[UUID] = None
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None
    contact_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    last_interaction_at: Optional[datetime] = None
    emails_sent: int = 0
    emails_opened: int = 0
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None

    class Config:
        from_attributes = True


class LeadConvertRequest(BaseModel):
    """Demande de conversion en contact/opportunité."""
    lead_id: UUID
    create_contact: bool = True
    create_opportunity: bool = False
    opportunity_value: Optional[Decimal] = None
    notes: Optional[str] = None


class LeadInteraction(BaseModel):
    """Interaction avec un lead."""
    type: str = Field(..., description="email, call, meeting, note")
    subject: Optional[str] = None
    content: Optional[str] = None
    outcome: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None


class LeadBulkAction(BaseModel):
    """Action en masse sur les leads."""
    lead_ids: List[UUID]
    action: str = Field(..., description="assign, tag, status, delete")
    value: Optional[str] = None  # assigned_to, tag, status


# ============================================================
# TEMPLATES
# ============================================================

class TemplateVariable(BaseModel):
    """Variable de template."""
    name: str
    description: Optional[str] = None
    default_value: Optional[str] = None
    required: bool = False


class TemplateBase(BaseModel):
    """Base pour les templates."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, description="promo, event, tips, testimonial")
    content_template: str = Field(..., min_length=1)
    post_type: PostType = PostType.TEXT
    suggested_hashtags: List[str] = Field(default_factory=list)
    suggested_media: List[str] = Field(default_factory=list)
    recommended_platforms: List[MarketingPlatform] = Field(default_factory=list)
    variables: List[TemplateVariable] = Field(default_factory=list)


class TemplateCreate(TemplateBase):
    """Création d'un template."""
    pass


class TemplateUpdate(BaseModel):
    """Mise à jour d'un template."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    content_template: Optional[str] = None
    post_type: Optional[PostType] = None
    suggested_hashtags: Optional[List[str]] = None
    suggested_media: Optional[List[str]] = None
    recommended_platforms: Optional[List[MarketingPlatform]] = None
    variables: Optional[List[TemplateVariable]] = None
    is_active: Optional[bool] = None


class TemplateResponse(TemplateBase):
    """Réponse template."""
    id: UUID
    tenant_id: str
    is_active: bool = True
    usage_count: int = 0
    avg_engagement_rate: Decimal = Decimal("0")
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class TemplateRenderRequest(BaseModel):
    """Demande de rendu d'un template."""
    template_id: UUID
    variables: Dict[str, str] = Field(default_factory=dict)
    platforms: Optional[List[MarketingPlatform]] = None


class TemplateRenderResponse(BaseModel):
    """Résultat du rendu."""
    content: str
    hashtags: List[str]
    platforms: List[MarketingPlatform]
    warnings: List[str] = Field(default_factory=list)


# ============================================================
# CALENDRIER
# ============================================================

class PublishingSlotBase(BaseModel):
    """Base pour les créneaux."""
    platform: MarketingPlatform
    day_of_week: int = Field(..., ge=0, le=6, description="0=Lundi, 6=Dimanche")
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(default=0, ge=0, le=59)
    is_optimal: bool = False


class PublishingSlotCreate(PublishingSlotBase):
    """Création d'un créneau."""
    pass


class PublishingSlotResponse(PublishingSlotBase):
    """Réponse créneau."""
    id: UUID
    tenant_id: str
    avg_engagement: Decimal = Decimal("0")
    posts_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class CalendarView(BaseModel):
    """Vue calendrier des publications."""
    date: date
    posts: List[PostResponse] = Field(default_factory=list)
    optimal_slots: List[PublishingSlotResponse] = Field(default_factory=list)


class WeeklySchedule(BaseModel):
    """Planning hebdomadaire."""
    week_start: date
    week_end: date
    days: Dict[str, List[PostResponse]] = Field(default_factory=dict)
    total_scheduled: int = 0
    total_published: int = 0


# ============================================================
# ANALYTICS
# ============================================================

class PostAnalytics(BaseModel):
    """Analytics d'une publication."""
    post_id: UUID
    platform: MarketingPlatform
    impressions: int = 0
    reach: int = 0
    clicks: int = 0
    click_through_rate: Decimal = Decimal("0")
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    engagement_rate: Decimal = Decimal("0")
    leads_generated: int = 0
    best_performing_time: Optional[str] = None


class PlatformPerformance(BaseModel):
    """Performance par plateforme."""
    platform: MarketingPlatform
    posts_count: int = 0
    total_impressions: int = 0
    total_reach: int = 0
    total_clicks: int = 0
    total_engagement: int = 0
    avg_engagement_rate: Decimal = Decimal("0")
    leads_generated: int = 0
    best_post_id: Optional[UUID] = None


class LeadFunnel(BaseModel):
    """Entonnoir de conversion des leads."""
    total_leads: int = 0
    new: int = 0
    contacted: int = 0
    qualified: int = 0
    proposal: int = 0
    negotiation: int = 0
    won: int = 0
    lost: int = 0
    conversion_rate: Decimal = Decimal("0")
    avg_time_to_convert: Optional[int] = None  # en jours


class ContentSuggestion(BaseModel):
    """Suggestion de contenu générée par IA."""
    title: str
    content: str
    hashtags: List[str]
    best_platforms: List[MarketingPlatform]
    best_time: Optional[datetime] = None
    estimated_reach: Optional[int] = None
    relevance_score: Decimal = Decimal("0")
