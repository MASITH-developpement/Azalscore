"""
AZALS MODULE - Réseaux Sociaux - Schémas Pydantic
=================================================
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .models import MarketingPlatform


# === Schémas de base ===

class SocialMetricsBase(BaseModel):
    """Schéma de base pour les métriques."""
    platform: MarketingPlatform
    metrics_date: date = Field(default_factory=date.today)

    # Métriques communes
    impressions: int = 0
    clicks: int = 0
    reach: int = 0
    engagement: int = 0
    followers: int = 0

    # Taux
    ctr: Decimal = Decimal("0")
    engagement_rate: Decimal = Decimal("0")
    bounce_rate: Decimal = Decimal("0")
    conversion_rate: Decimal = Decimal("0")

    # Analytics
    sessions: int = 0
    users: int = 0
    pageviews: int = 0
    avg_session_duration: Decimal = Decimal("0")
    conversions: int = 0

    # Publicité
    cost: Decimal = Decimal("0")
    cpc: Decimal = Decimal("0")
    cpm: Decimal = Decimal("0")
    roas: Decimal = Decimal("0")

    # SEO
    avg_position: Decimal = Decimal("0")

    # Local
    calls: int = 0
    directions: int = 0
    reviews_count: int = 0
    rating: Decimal = Decimal("0")

    # Vidéo
    views: int = 0
    watch_time: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    subscribers: int = 0

    notes: Optional[str] = None


class SocialMetricsCreate(SocialMetricsBase):
    """Schéma pour créer des métriques."""
    pass


class SocialMetricsUpdate(BaseModel):
    """Schéma pour mettre à jour des métriques (tous les champs optionnels)."""
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    reach: Optional[int] = None
    engagement: Optional[int] = None
    followers: Optional[int] = None

    ctr: Optional[Decimal] = None
    engagement_rate: Optional[Decimal] = None
    bounce_rate: Optional[Decimal] = None
    conversion_rate: Optional[Decimal] = None

    sessions: Optional[int] = None
    users: Optional[int] = None
    pageviews: Optional[int] = None
    avg_session_duration: Optional[Decimal] = None
    conversions: Optional[int] = None

    cost: Optional[Decimal] = None
    cpc: Optional[Decimal] = None
    cpm: Optional[Decimal] = None
    roas: Optional[Decimal] = None

    avg_position: Optional[Decimal] = None

    calls: Optional[int] = None
    directions: Optional[int] = None
    reviews_count: Optional[int] = None
    rating: Optional[Decimal] = None

    views: Optional[int] = None
    watch_time: Optional[int] = None
    likes: Optional[int] = None
    shares: Optional[int] = None
    comments: Optional[int] = None
    subscribers: Optional[int] = None

    notes: Optional[str] = None


class SocialMetricsResponse(SocialMetricsBase):
    """Schéma de réponse avec ID et timestamps."""
    id: UUID
    tenant_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# === Schémas pour saisie rapide par plateforme ===

class GoogleAnalyticsInput(BaseModel):
    """Saisie simplifiée Google Analytics."""
    metrics_date: date = Field(default_factory=date.today)
    sessions: int = 0
    users: int = 0
    pageviews: int = 0
    bounce_rate: Decimal = Field(default=Decimal("0"), description="Taux de rebond (%)")
    avg_session_duration: Decimal = Field(default=Decimal("0"), description="Durée moyenne (secondes)")
    conversions: int = 0
    conversion_rate: Decimal = Field(default=Decimal("0"), description="Taux de conversion (%)")
    notes: Optional[str] = None


class GoogleAdsInput(BaseModel):
    """Saisie simplifiée Google Ads."""
    metrics_date: date = Field(default_factory=date.today)
    impressions: int = 0
    clicks: int = 0
    cost: Decimal = Field(default=Decimal("0"), description="Coût total (€)")
    conversions: int = 0
    ctr: Decimal = Field(default=Decimal("0"), description="CTR (%)")
    cpc: Decimal = Field(default=Decimal("0"), description="CPC moyen (€)")
    roas: Decimal = Field(default=Decimal("0"), description="ROAS")
    notes: Optional[str] = None


class GoogleSearchConsoleInput(BaseModel):
    """Saisie simplifiée Google Search Console."""
    metrics_date: date = Field(default_factory=date.today)
    impressions: int = 0
    clicks: int = 0
    ctr: Decimal = Field(default=Decimal("0"), description="CTR (%)")
    avg_position: Decimal = Field(default=Decimal("0"), description="Position moyenne")
    notes: Optional[str] = None


class GoogleMyBusinessInput(BaseModel):
    """Saisie simplifiée Google My Business."""
    metrics_date: date = Field(default_factory=date.today)
    views: int = Field(default=0, description="Vues de la fiche")
    clicks: int = Field(default=0, description="Clics vers le site")
    calls: int = Field(default=0, description="Appels téléphoniques")
    directions: int = Field(default=0, description="Demandes d'itinéraire")
    reviews_count: int = Field(default=0, description="Nombre total d'avis")
    rating: Decimal = Field(default=Decimal("0"), description="Note moyenne (sur 5)")
    notes: Optional[str] = None


class MetaBusinessInput(BaseModel):
    """Saisie simplifiée Meta Business (Facebook/Instagram)."""
    metrics_date: date = Field(default_factory=date.today)
    platform: MarketingPlatform = MarketingPlatform.META_FACEBOOK
    reach: int = Field(default=0, description="Portée")
    impressions: int = 0
    engagement: int = Field(default=0, description="Engagements (likes, comments, shares)")
    clicks: int = 0
    followers: int = Field(default=0, description="Nombre d'abonnés")
    cost: Decimal = Field(default=Decimal("0"), description="Budget pub dépensé (€)")
    ctr: Decimal = Field(default=Decimal("0"), description="CTR (%)")
    cpm: Decimal = Field(default=Decimal("0"), description="CPM (€)")
    notes: Optional[str] = None


class LinkedInInput(BaseModel):
    """Saisie simplifiée LinkedIn."""
    metrics_date: date = Field(default_factory=date.today)
    followers: int = Field(default=0, description="Abonnés page")
    impressions: int = 0
    clicks: int = 0
    engagement: int = Field(default=0, description="Engagements")
    engagement_rate: Decimal = Field(default=Decimal("0"), description="Taux d'engagement (%)")
    reach: int = Field(default=0, description="Visiteurs uniques")
    notes: Optional[str] = None


class SolocalInput(BaseModel):
    """Saisie simplifiée Solocal (PagesJaunes)."""
    metrics_date: date = Field(default_factory=date.today)
    impressions: int = Field(default=0, description="Vues de la fiche")
    clicks: int = Field(default=0, description="Clics vers le site")
    calls: int = Field(default=0, description="Appels")
    directions: int = Field(default=0, description="Demandes d'itinéraire")
    reviews_count: int = Field(default=0, description="Nombre d'avis")
    rating: Decimal = Field(default=Decimal("0"), description="Note (sur 5)")
    notes: Optional[str] = None


# === Schéma récapitulatif ===

class MarketingSummary(BaseModel):
    """Récapitulatif marketing toutes plateformes."""
    date: date
    total_spend: Decimal = Decimal("0")
    total_conversions: int = 0
    total_impressions: int = 0
    total_clicks: int = 0
    overall_ctr: Decimal = Decimal("0")
    estimated_roi: Decimal = Decimal("0")

    google_analytics: Optional[dict] = None
    google_ads: Optional[dict] = None
    google_search_console: Optional[dict] = None
    google_my_business: Optional[dict] = None
    meta_facebook: Optional[dict] = None
    meta_instagram: Optional[dict] = None
    linkedin: Optional[dict] = None
    solocal: Optional[dict] = None
