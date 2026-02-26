"""
AZALS MODULE - Réseaux Sociaux - Modèles
========================================
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum as SQLEnum,
    Integer, Numeric, String, Text, UniqueConstraint
)

from app.db import Base


class MarketingPlatform(str, Enum):
    """Plateformes marketing supportées."""
    GOOGLE_ANALYTICS = "google_analytics"
    GOOGLE_ADS = "google_ads"
    GOOGLE_SEARCH_CONSOLE = "google_search_console"
    GOOGLE_MY_BUSINESS = "google_my_business"
    META_FACEBOOK = "meta_facebook"
    META_INSTAGRAM = "meta_instagram"
    LINKEDIN = "linkedin"
    SOLOCAL = "solocal"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"


class SocialNetworkMetrics(Base):
    """
    Métriques des réseaux sociaux et plateformes marketing.
    Une entrée par plateforme par date.
    """
    __tablename__ = "social_network_metrics"

    # Tenant et timestamps
    tenant_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    # Identification
    platform = Column(SQLEnum(MarketingPlatform), nullable=False)
    metrics_date = Column(Date, nullable=False, default=datetime.utcnow().date)

    # === Métriques communes ===
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    engagement = Column(Integer, default=0)
    followers = Column(Integer, default=0)

    # Taux (en pourcentage)
    ctr = Column(Numeric(10, 4), default=0)  # Click-through rate
    engagement_rate = Column(Numeric(10, 4), default=0)
    bounce_rate = Column(Numeric(10, 4), default=0)
    conversion_rate = Column(Numeric(10, 4), default=0)

    # === Métriques spécifiques Analytics ===
    sessions = Column(Integer, default=0)
    users = Column(Integer, default=0)
    pageviews = Column(Integer, default=0)
    avg_session_duration = Column(Numeric(10, 2), default=0)  # en secondes
    conversions = Column(Integer, default=0)

    # === Métriques publicitaires ===
    cost = Column(Numeric(12, 2), default=0)  # en euros
    cpc = Column(Numeric(10, 4), default=0)  # coût par clic
    cpm = Column(Numeric(10, 4), default=0)  # coût pour 1000 impressions
    roas = Column(Numeric(10, 4), default=0)  # Return on Ad Spend

    # === Métriques SEO ===
    avg_position = Column(Numeric(10, 2), default=0)

    # === Métriques locales (GMB, Solocal) ===
    calls = Column(Integer, default=0)
    directions = Column(Integer, default=0)
    reviews_count = Column(Integer, default=0)
    rating = Column(Numeric(3, 2), default=0)  # Note sur 5

    # === Métriques vidéo (YouTube, TikTok) ===
    views = Column(Integer, default=0)
    watch_time = Column(Integer, default=0)  # en secondes
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    subscribers = Column(Integer, default=0)

    # Notes
    notes = Column(Text, nullable=True)

    # Contrainte d'unicité : une seule entrée par plateforme par date par tenant
    __table_args__ = (
        UniqueConstraint('tenant_id', 'platform', 'metrics_date', name='uq_social_metrics_tenant_platform_date'),
    )

    def __repr__(self):
        return f"<SocialNetworkMetrics {self.platform.value} {self.metrics_date}>"


class SocialNetworkConfig(Base):
    """
    Configuration des connexions aux plateformes (pour futur usage API).
    """
    __tablename__ = "social_network_config"

    # Tenant et timestamps
    tenant_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    platform = Column(SQLEnum(MarketingPlatform), nullable=False)
    is_enabled = Column(Boolean, default=True)

    # Credentials (chiffrés en production)
    api_key = Column(String(500), nullable=True)
    api_secret = Column(String(500), nullable=True)
    access_token = Column(String(1000), nullable=True)
    refresh_token = Column(String(1000), nullable=True)

    # Identifiants de compte
    account_id = Column(String(200), nullable=True)
    property_id = Column(String(200), nullable=True)  # GA4 property

    # Statut
    last_sync_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'platform', name='uq_social_config_tenant_platform'),
    )

    def __repr__(self):
        return f"<SocialNetworkConfig {self.platform.value}>"
