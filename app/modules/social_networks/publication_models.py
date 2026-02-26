"""
AZALS MODULE - Publications Réseaux Sociaux - Modèles
=====================================================

Gestion des publications pour la génération de leads :
- Publications multi-plateformes
- Campagnes marketing
- Tracking des leads générés
- Templates de contenus

IMPORTANT: tenant_id obligatoire sur chaque entité (AZA-TENANT)
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum as SQLEnum, ForeignKey,
    Integer, JSON, Numeric, String, Text, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.db import Base
from .models import MarketingPlatform


class PostStatus(str, Enum):
    """Statut d'une publication."""
    DRAFT = "draft"                    # Brouillon
    SCHEDULED = "scheduled"            # Programmée
    PUBLISHING = "publishing"          # En cours de publication
    PUBLISHED = "published"            # Publiée
    FAILED = "failed"                  # Échec
    ARCHIVED = "archived"              # Archivée


class PostType(str, Enum):
    """Type de publication."""
    TEXT = "text"                      # Texte simple
    IMAGE = "image"                    # Image + texte
    VIDEO = "video"                    # Vidéo
    CAROUSEL = "carousel"              # Carrousel d'images
    LINK = "link"                      # Partage de lien
    STORY = "story"                    # Story (24h)
    REEL = "reel"                      # Reel/Short


class CampaignStatus(str, Enum):
    """Statut d'une campagne."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class LeadStatus(str, Enum):
    """Statut d'un lead."""
    NEW = "new"                        # Nouveau lead
    CONTACTED = "contacted"            # Contacté
    QUALIFIED = "qualified"            # Qualifié
    PROPOSAL = "proposal"              # Proposition envoyée
    NEGOTIATION = "negotiation"        # En négociation
    WON = "won"                        # Converti en client
    LOST = "lost"                      # Perdu
    NURTURING = "nurturing"            # En nurturing


class LeadSource(str, Enum):
    """Source du lead."""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    GOOGLE_ADS = "google_ads"
    WEBSITE = "website"
    REFERRAL = "referral"
    ORGANIC = "organic"
    OTHER = "other"


# ============================================================
# CAMPAGNES
# ============================================================

class SocialCampaign(Base):
    """
    Campagne marketing multi-plateformes.
    Regroupe plusieurs publications avec un objectif commun.
    """
    __tablename__ = "social_campaigns"

    # === Tenant (OBLIGATOIRE) ===
    tenant_id = Column(String(255), nullable=False, index=True)

    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    created_by = Column(String(255), nullable=True)  # User ID

    # === Identification ===
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False)

    # === Période ===
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # === Objectifs ===
    objective = Column(String(100), nullable=True)  # awareness, engagement, leads, traffic
    target_audience = Column(Text, nullable=True)  # Description cible
    target_leads = Column(Integer, default=0)  # Objectif leads
    target_impressions = Column(Integer, default=0)
    budget = Column(Numeric(12, 2), default=0)

    # === Plateformes ciblées ===
    platforms = Column(JSON, default=list)  # Liste de MarketingPlatform

    # === Tracking ===
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)

    # === KPIs réalisés ===
    total_posts = Column(Integer, default=0)
    total_impressions = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    total_leads = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    actual_spend = Column(Numeric(12, 2), default=0)

    # === Relations ===
    posts = relationship("SocialPost", back_populates="campaign", cascade="all, delete-orphan")
    leads = relationship("SocialLead", back_populates="campaign")

    __table_args__ = (
        Index('ix_social_campaigns_tenant_status', 'tenant_id', 'status'),
    )

    def __repr__(self):
        return f"<SocialCampaign {self.name}>"


# ============================================================
# PUBLICATIONS
# ============================================================

class SocialPost(Base):
    """
    Publication sur les réseaux sociaux.
    Peut être publiée sur plusieurs plateformes.
    """
    __tablename__ = "social_posts"

    # === Tenant (OBLIGATOIRE) ===
    tenant_id = Column(String(255), nullable=False, index=True)

    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    created_by = Column(String(255), nullable=True)

    # === Campagne (optionnel) ===
    campaign_id = Column(String(36), ForeignKey('social_campaigns.id'), nullable=True)
    campaign = relationship("SocialCampaign", back_populates="posts")

    # === Contenu ===
    title = Column(String(255), nullable=True)  # Titre interne
    content = Column(Text, nullable=False)  # Texte du post
    post_type = Column(SQLEnum(PostType), default=PostType.TEXT, nullable=False)

    # === Médias ===
    media_urls = Column(JSON, default=list)  # URLs des images/vidéos
    thumbnail_url = Column(String(500), nullable=True)

    # === Lien CTA ===
    link_url = Column(String(500), nullable=True)  # Lien vers azalscore.com
    link_title = Column(String(255), nullable=True)
    link_description = Column(Text, nullable=True)

    # === Publication ===
    status = Column(SQLEnum(PostStatus), default=PostStatus.DRAFT, nullable=False)
    platforms = Column(JSON, default=list)  # Plateformes cibles
    scheduled_at = Column(DateTime, nullable=True)  # Date/heure programmée
    published_at = Column(DateTime, nullable=True)  # Date publication réelle

    # === IDs externes (après publication) ===
    external_ids = Column(JSON, default=dict)  # {platform: post_id}

    # === UTM Tracking ===
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    utm_content = Column(String(100), nullable=True)

    # === Hashtags et mentions ===
    hashtags = Column(JSON, default=list)  # Liste de hashtags
    mentions = Column(JSON, default=list)  # @mentions

    # === Métriques (mises à jour périodiquement) ===
    impressions = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    saves = Column(Integer, default=0)

    # === Erreurs ===
    last_error = Column(Text, nullable=True)

    __table_args__ = (
        Index('ix_social_posts_tenant_status', 'tenant_id', 'status'),
        Index('ix_social_posts_scheduled', 'tenant_id', 'scheduled_at'),
    )

    def __repr__(self):
        return f"<SocialPost {self.title or self.id}>"

    @property
    def tracking_url(self) -> str:
        """Génère l'URL avec paramètres UTM."""
        if not self.link_url:
            return ""

        params = []
        if self.utm_source:
            params.append(f"utm_source={self.utm_source}")
        if self.utm_medium:
            params.append(f"utm_medium={self.utm_medium}")
        if self.utm_campaign:
            params.append(f"utm_campaign={self.utm_campaign}")
        if self.utm_content:
            params.append(f"utm_content={self.utm_content}")

        if params:
            separator = "&" if "?" in self.link_url else "?"
            return f"{self.link_url}{separator}{'&'.join(params)}"

        return self.link_url


# ============================================================
# LEADS
# ============================================================

class SocialLead(Base):
    """
    Lead généré via les réseaux sociaux.
    Lié à une publication ou campagne spécifique.
    """
    __tablename__ = "social_leads"

    # === Tenant (OBLIGATOIRE) ===
    tenant_id = Column(String(255), nullable=False, index=True)

    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    # === Source ===
    source = Column(SQLEnum(LeadSource), nullable=False)
    source_platform = Column(SQLEnum(MarketingPlatform), nullable=True)
    campaign_id = Column(String(36), ForeignKey('social_campaigns.id'), nullable=True)
    campaign = relationship("SocialCampaign", back_populates="leads")
    post_id = Column(String(36), ForeignKey('social_posts.id'), nullable=True)

    # === Tracking ===
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    utm_content = Column(String(100), nullable=True)
    landing_page = Column(String(500), nullable=True)
    referrer = Column(String(500), nullable=True)

    # === Contact ===
    email = Column(String(255), nullable=True)  # Index via __table_args__
    phone = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    company = Column(String(255), nullable=True)
    job_title = Column(String(100), nullable=True)

    # === Profil social ===
    social_profile_url = Column(String(500), nullable=True)
    social_username = Column(String(100), nullable=True)
    followers_count = Column(Integer, nullable=True)

    # === Qualification ===
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW, nullable=False)
    score = Column(Integer, default=0)  # Score de qualification 0-100
    interest = Column(String(255), nullable=True)  # Module/fonctionnalité d'intérêt
    budget_range = Column(String(50), nullable=True)  # Fourchette budget
    timeline = Column(String(50), nullable=True)  # Délai projet

    # === Notes et suivi ===
    notes = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    assigned_to = Column(String(255), nullable=True)  # Commercial assigné

    # === Conversion ===
    converted_at = Column(DateTime, nullable=True)
    contact_id = Column(String(36), nullable=True)  # Lien vers Contact CRM
    opportunity_id = Column(String(36), nullable=True)  # Lien vers Opportunité

    # === Engagement ===
    interactions = Column(JSON, default=list)  # Historique interactions
    last_interaction_at = Column(DateTime, nullable=True)
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)

    __table_args__ = (
        Index('ix_social_leads_tenant_status', 'tenant_id', 'status'),
        Index('ix_social_leads_email', 'tenant_id', 'email'),
        Index('ix_social_leads_campaign', 'tenant_id', 'campaign_id'),
    )

    def __repr__(self):
        return f"<SocialLead {self.email or self.id}>"


# ============================================================
# TEMPLATES DE PUBLICATION
# ============================================================

class PostTemplate(Base):
    """
    Template réutilisable pour les publications.
    Facilite la création de contenus récurrents.
    """
    __tablename__ = "social_post_templates"

    # === Tenant (OBLIGATOIRE) ===
    tenant_id = Column(String(255), nullable=False, index=True)

    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    created_by = Column(String(255), nullable=True)

    # === Identification ===
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # promo, event, tips, testimonial
    is_active = Column(Boolean, default=True)

    # === Contenu template ===
    content_template = Column(Text, nullable=False)  # Avec variables {name}, {product}
    post_type = Column(SQLEnum(PostType), default=PostType.TEXT, nullable=False)
    suggested_hashtags = Column(JSON, default=list)
    suggested_media = Column(JSON, default=list)  # URLs par défaut

    # === Plateformes recommandées ===
    recommended_platforms = Column(JSON, default=list)

    # === Variables disponibles ===
    variables = Column(JSON, default=list)  # [{name: "product", description: "Nom du produit"}]

    # === Statistiques d'utilisation ===
    usage_count = Column(Integer, default=0)
    avg_engagement_rate = Column(Numeric(10, 4), default=0)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_post_template_name'),
    )

    def __repr__(self):
        return f"<PostTemplate {self.name}>"


# ============================================================
# CALENDRIER DE PUBLICATION
# ============================================================

class PublishingSlot(Base):
    """
    Créneau de publication optimisé.
    Définit les meilleurs moments pour publier sur chaque plateforme.
    """
    __tablename__ = "social_publishing_slots"

    # === Tenant (OBLIGATOIRE) ===
    tenant_id = Column(String(255), nullable=False, index=True)

    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # === Configuration ===
    platform = Column(SQLEnum(MarketingPlatform), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Lundi, 6=Dimanche
    hour = Column(Integer, nullable=False)  # 0-23
    minute = Column(Integer, default=0)  # 0-59

    # === Performance ===
    is_optimal = Column(Boolean, default=False)  # Basé sur les analytics
    avg_engagement = Column(Numeric(10, 4), default=0)
    posts_count = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'platform', 'day_of_week', 'hour',
                        name='uq_publishing_slot'),
    )

    def __repr__(self):
        days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        return f"<PublishingSlot {self.platform.value} {days[self.day_of_week]} {self.hour}:{self.minute:02d}>"
