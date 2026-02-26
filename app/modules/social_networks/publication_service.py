"""
AZALS MODULE - Publications Réseaux Sociaux - Service
=====================================================

Logique métier pour la création, programmation et publication
sur les réseaux sociaux avec tracking des leads.

IMPORTANT: Filtre tenant_id sur CHAQUE requête (AZA-TENANT)
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from .models import MarketingPlatform
from .publication_models import (
    SocialCampaign, SocialPost, SocialLead, PostTemplate, PublishingSlot,
    PostStatus, PostType, CampaignStatus, LeadStatus, LeadSource
)
from .publication_schemas import (
    CampaignCreate, CampaignUpdate, CampaignStats,
    PostCreate, PostUpdate, PostScheduleRequest,
    LeadCreate, LeadUpdate, LeadInteraction, LeadConvertRequest,
    TemplateCreate, TemplateUpdate, TemplateRenderRequest, TemplateRenderResponse,
    PublishingSlotCreate,
    PlatformPerformance, LeadFunnel, ContentSuggestion
)

logger = logging.getLogger(__name__)


class PublicationService:
    """Service de gestion des publications et leads sociaux."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ============================================================
    # CAMPAGNES
    # ============================================================

    def _campaign_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(SocialCampaign).filter(
            SocialCampaign.tenant_id == self.tenant_id
        )

    def list_campaigns(
        self,
        status: Optional[CampaignStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SocialCampaign]:
        """Liste les campagnes avec filtres."""
        query = self._campaign_query()

        if status:
            query = query.filter(SocialCampaign.status == status)

        return query.order_by(
            SocialCampaign.created_at.desc()
        ).offset(offset).limit(limit).all()

    def get_campaign(self, campaign_id: UUID) -> Optional[SocialCampaign]:
        """Récupère une campagne par ID."""
        return self._campaign_query().filter(
            SocialCampaign.id == str(campaign_id)
        ).first()

    def create_campaign(self, data: CampaignCreate, user_id: Optional[str] = None) -> SocialCampaign:
        """Crée une nouvelle campagne."""
        campaign = SocialCampaign(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data.model_dump()
        )

        # Générer UTM par défaut si non fourni
        if not campaign.utm_campaign:
            campaign.utm_campaign = self._generate_utm_slug(data.name)

        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)

        logger.info(f"[SOCIAL] Campagne créée: {campaign.name} (tenant={self.tenant_id})")
        return campaign

    def update_campaign(
        self,
        campaign_id: UUID,
        data: CampaignUpdate
    ) -> Optional[SocialCampaign]:
        """Met à jour une campagne."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)

        self.db.commit()
        self.db.refresh(campaign)

        logger.info(f"[SOCIAL] Campagne mise à jour: {campaign.name}")
        return campaign

    def delete_campaign(self, campaign_id: UUID) -> bool:
        """Supprime une campagne (et ses posts associés)."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return False

        self.db.delete(campaign)
        self.db.commit()

        logger.info(f"[SOCIAL] Campagne supprimée: {campaign_id}")
        return True

    def get_campaign_stats(
        self,
        campaign_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> CampaignStats:
        """Calcule les statistiques d'une campagne."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campagne non trouvée")

        if not start_date:
            start_date = campaign.start_date or campaign.created_at.date()
        if not end_date:
            end_date = campaign.end_date or date.today()

        # Posts publiés
        posts = self.db.query(SocialPost).filter(
            and_(
                SocialPost.tenant_id == self.tenant_id,
                SocialPost.campaign_id == str(campaign_id),
                SocialPost.status == PostStatus.PUBLISHED
            )
        ).all()

        # Leads générés
        leads = self.db.query(SocialLead).filter(
            and_(
                SocialLead.tenant_id == self.tenant_id,
                SocialLead.campaign_id == str(campaign_id)
            )
        ).all()

        leads_converted = len([l for l in leads if l.status == LeadStatus.WON])

        total_impressions = sum(p.impressions or 0 for p in posts)
        total_clicks = sum(p.clicks or 0 for p in posts)
        total_engagement = sum(
            (p.likes or 0) + (p.comments or 0) + (p.shares or 0)
            for p in posts
        )

        cost_per_lead = (
            campaign.actual_spend / len(leads)
            if leads and campaign.actual_spend > 0
            else Decimal("0")
        )

        conversion_rate = (
            Decimal(leads_converted) / Decimal(len(leads)) * 100
            if leads
            else Decimal("0")
        )

        return CampaignStats(
            campaign_id=campaign_id,
            period_start=start_date,
            period_end=end_date,
            posts_published=len(posts),
            impressions=total_impressions,
            reach=sum(p.reach or 0 for p in posts),
            clicks=total_clicks,
            engagement=total_engagement,
            leads_generated=len(leads),
            leads_converted=leads_converted,
            cost_per_lead=cost_per_lead,
            conversion_rate=conversion_rate
        )

    # ============================================================
    # PUBLICATIONS
    # ============================================================

    def _post_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(SocialPost).filter(
            SocialPost.tenant_id == self.tenant_id
        )

    def list_posts(
        self,
        status: Optional[PostStatus] = None,
        campaign_id: Optional[UUID] = None,
        platform: Optional[MarketingPlatform] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SocialPost]:
        """Liste les publications avec filtres."""
        query = self._post_query()

        if status:
            query = query.filter(SocialPost.status == status)
        if campaign_id:
            query = query.filter(SocialPost.campaign_id == str(campaign_id))
        if platform:
            # JSON contient la plateforme
            query = query.filter(
                SocialPost.platforms.contains([platform.value])
            )
        if start_date:
            query = query.filter(SocialPost.created_at >= start_date)
        if end_date:
            query = query.filter(SocialPost.created_at <= end_date)

        return query.order_by(
            SocialPost.scheduled_at.desc().nullsfirst(),
            SocialPost.created_at.desc()
        ).offset(offset).limit(limit).all()

    def get_post(self, post_id: UUID) -> Optional[SocialPost]:
        """Récupère une publication par ID."""
        return self._post_query().filter(
            SocialPost.id == str(post_id)
        ).first()

    def create_post(self, data: PostCreate, user_id: Optional[str] = None) -> SocialPost:
        """Crée une nouvelle publication."""
        post_data = data.model_dump()
        campaign_id = post_data.pop('campaign_id', None)

        post = SocialPost(
            tenant_id=self.tenant_id,
            created_by=user_id,
            campaign_id=str(campaign_id) if campaign_id else None,
            **post_data
        )

        # Générer UTM automatiquement
        if not post.utm_source:
            post.utm_source = "social"
        if not post.utm_medium:
            post.utm_medium = "organic"

        # Si programmé, passer en status SCHEDULED
        if post.scheduled_at:
            post.status = PostStatus.SCHEDULED

        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)

        # Mettre à jour le compteur de la campagne
        if post.campaign_id:
            self._update_campaign_post_count(UUID(post.campaign_id))

        logger.info(f"[SOCIAL] Post créé: {post.id} (tenant={self.tenant_id})")
        return post

    def update_post(self, post_id: UUID, data: PostUpdate) -> Optional[SocialPost]:
        """Met à jour une publication."""
        post = self.get_post(post_id)
        if not post:
            return None

        # Empêcher modification si déjà publié
        if post.status == PostStatus.PUBLISHED:
            logger.warning(f"[SOCIAL] Tentative de modification d'un post publié: {post_id}")
            raise ValueError("Impossible de modifier une publication déjà publiée")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(post, field, value)

        # Mettre à jour le statut si programmation
        if post.scheduled_at and post.status == PostStatus.DRAFT:
            post.status = PostStatus.SCHEDULED

        self.db.commit()
        self.db.refresh(post)

        logger.info(f"[SOCIAL] Post mis à jour: {post_id}")
        return post

    def delete_post(self, post_id: UUID) -> bool:
        """Supprime une publication."""
        post = self.get_post(post_id)
        if not post:
            return False

        campaign_id = post.campaign_id
        self.db.delete(post)
        self.db.commit()

        if campaign_id:
            self._update_campaign_post_count(UUID(campaign_id))

        logger.info(f"[SOCIAL] Post supprimé: {post_id}")
        return True

    def schedule_post(self, data: PostScheduleRequest) -> SocialPost:
        """Programme une publication."""
        post = self.get_post(data.post_id)
        if not post:
            raise ValueError("Publication non trouvée")

        if post.status not in [PostStatus.DRAFT, PostStatus.SCHEDULED]:
            raise ValueError("Seuls les brouillons peuvent être programmés")

        post.scheduled_at = data.scheduled_at
        post.status = PostStatus.SCHEDULED

        if data.platforms:
            post.platforms = [p.value for p in data.platforms]

        self.db.commit()
        self.db.refresh(post)

        logger.info(f"[SOCIAL] Post programmé: {post.id} pour {data.scheduled_at}")
        return post

    async def publish_post(self, post_id: UUID, platforms: Optional[List[MarketingPlatform]] = None) -> SocialPost:
        """Publie immédiatement une publication."""
        post = self.get_post(post_id)
        if not post:
            raise ValueError("Publication non trouvée")

        if post.status == PostStatus.PUBLISHED:
            raise ValueError("Publication déjà publiée")

        target_platforms = platforms or [MarketingPlatform(p) for p in post.platforms]

        post.status = PostStatus.PUBLISHING
        self.db.commit()

        external_ids = {}
        errors = []

        for platform in target_platforms:
            try:
                # Publication via les clients API
                external_id = await self._publish_to_platform(post, platform)
                if external_id:
                    external_ids[platform.value] = external_id
            except Exception as e:
                errors.append(f"{platform.value}: {str(e)}")
                logger.error(f"[SOCIAL] Erreur publication {platform.value}: {e}")

        if external_ids:
            post.status = PostStatus.PUBLISHED
            post.published_at = datetime.utcnow()
            post.external_ids = external_ids
        else:
            post.status = PostStatus.FAILED
            post.last_error = "; ".join(errors)

        self.db.commit()
        self.db.refresh(post)

        logger.info(f"[SOCIAL] Post publié: {post.id} sur {list(external_ids.keys())}")
        return post

    async def _publish_to_platform(self, post: SocialPost, platform: MarketingPlatform) -> Optional[str]:
        """Publie sur une plateforme spécifique."""
        from .api_clients import (
            MetaBusinessClient, LinkedInClient
        )
        from .config_service import ConfigService

        config_service = ConfigService(self.db, self.tenant_id)
        config = config_service.get_config(platform)

        if not config or not config.access_token:
            raise ValueError(f"Plateforme {platform.value} non configurée")

        content = post.content
        link = post.tracking_url if post.link_url else None
        media = post.media_urls

        if platform in [MarketingPlatform.META_FACEBOOK, MarketingPlatform.META_INSTAGRAM]:
            async with MetaBusinessClient(
                access_token=config.access_token,
                account_id=config.account_id
            ) as client:
                return await client.create_post(
                    content=content,
                    link=link,
                    media_urls=media,
                    platform="instagram" if platform == MarketingPlatform.META_INSTAGRAM else "facebook"
                )

        elif platform == MarketingPlatform.LINKEDIN:
            async with LinkedInClient(
                access_token=config.access_token
            ) as client:
                return await client.create_post(
                    content=content,
                    link=link,
                    media_urls=media
                )

        # TODO: Autres plateformes
        return None

    def get_scheduled_posts(self, before: Optional[datetime] = None) -> List[SocialPost]:
        """Récupère les posts programmés à publier."""
        query = self._post_query().filter(
            SocialPost.status == PostStatus.SCHEDULED
        )

        if before:
            query = query.filter(SocialPost.scheduled_at <= before)

        return query.order_by(SocialPost.scheduled_at).all()

    def duplicate_post(self, post_id: UUID) -> SocialPost:
        """Duplique une publication."""
        original = self.get_post(post_id)
        if not original:
            raise ValueError("Publication non trouvée")

        new_post = SocialPost(
            tenant_id=self.tenant_id,
            campaign_id=original.campaign_id,
            title=f"{original.title} (copie)" if original.title else None,
            content=original.content,
            post_type=original.post_type,
            media_urls=original.media_urls,
            thumbnail_url=original.thumbnail_url,
            link_url=original.link_url,
            link_title=original.link_title,
            link_description=original.link_description,
            platforms=original.platforms,
            hashtags=original.hashtags,
            mentions=original.mentions,
            utm_source=original.utm_source,
            utm_medium=original.utm_medium,
            utm_campaign=original.utm_campaign,
            status=PostStatus.DRAFT
        )

        self.db.add(new_post)
        self.db.commit()
        self.db.refresh(new_post)

        return new_post

    # ============================================================
    # LEADS
    # ============================================================

    def _lead_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(SocialLead).filter(
            SocialLead.tenant_id == self.tenant_id
        )

    def list_leads(
        self,
        status: Optional[LeadStatus] = None,
        source: Optional[LeadSource] = None,
        campaign_id: Optional[UUID] = None,
        assigned_to: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SocialLead]:
        """Liste les leads avec filtres."""
        query = self._lead_query()

        if status:
            query = query.filter(SocialLead.status == status)
        if source:
            query = query.filter(SocialLead.source == source)
        if campaign_id:
            query = query.filter(SocialLead.campaign_id == str(campaign_id))
        if assigned_to:
            query = query.filter(SocialLead.assigned_to == assigned_to)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    SocialLead.email.ilike(search_pattern),
                    SocialLead.first_name.ilike(search_pattern),
                    SocialLead.last_name.ilike(search_pattern),
                    SocialLead.company.ilike(search_pattern)
                )
            )

        return query.order_by(
            SocialLead.created_at.desc()
        ).offset(offset).limit(limit).all()

    def get_lead(self, lead_id: UUID) -> Optional[SocialLead]:
        """Récupère un lead par ID."""
        return self._lead_query().filter(
            SocialLead.id == str(lead_id)
        ).first()

    def create_lead(self, data: LeadCreate) -> SocialLead:
        """Crée un nouveau lead."""
        lead_data = data.model_dump()
        campaign_id = lead_data.pop('campaign_id', None)
        post_id = lead_data.pop('post_id', None)

        lead = SocialLead(
            tenant_id=self.tenant_id,
            campaign_id=str(campaign_id) if campaign_id else None,
            post_id=str(post_id) if post_id else None,
            **lead_data
        )

        # Score initial basé sur les informations fournies
        lead.score = self._calculate_lead_score(lead)

        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)

        # Mettre à jour les compteurs
        if lead.campaign_id:
            self._update_campaign_lead_count(UUID(lead.campaign_id))

        logger.info(f"[SOCIAL] Lead créé: {lead.email or lead.id} (tenant={self.tenant_id})")
        return lead

    def update_lead(self, lead_id: UUID, data: LeadUpdate) -> Optional[SocialLead]:
        """Met à jour un lead."""
        lead = self.get_lead(lead_id)
        if not lead:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lead, field, value)

        # Recalculer le score si des infos importantes ont changé
        if any(f in update_data for f in ['email', 'company', 'budget_range', 'interest']):
            lead.score = self._calculate_lead_score(lead)

        self.db.commit()
        self.db.refresh(lead)

        logger.info(f"[SOCIAL] Lead mis à jour: {lead_id}")
        return lead

    def delete_lead(self, lead_id: UUID) -> bool:
        """Supprime un lead."""
        lead = self.get_lead(lead_id)
        if not lead:
            return False

        campaign_id = lead.campaign_id
        self.db.delete(lead)
        self.db.commit()

        if campaign_id:
            self._update_campaign_lead_count(UUID(campaign_id))

        return True

    def add_lead_interaction(self, lead_id: UUID, interaction: LeadInteraction) -> SocialLead:
        """Ajoute une interaction avec un lead."""
        lead = self.get_lead(lead_id)
        if not lead:
            raise ValueError("Lead non trouvé")

        interactions = lead.interactions or []
        interactions.append({
            "timestamp": datetime.utcnow().isoformat(),
            **interaction.model_dump()
        })
        lead.interactions = interactions
        lead.last_interaction_at = datetime.utcnow()

        # Mettre à jour le statut si c'est un premier contact
        if lead.status == LeadStatus.NEW and interaction.type in ['email', 'call']:
            lead.status = LeadStatus.CONTACTED

        self.db.commit()
        self.db.refresh(lead)

        return lead

    async def convert_lead(self, data: LeadConvertRequest) -> Dict:
        """Convertit un lead en contact/opportunité."""
        lead = self.get_lead(data.lead_id)
        if not lead:
            raise ValueError("Lead non trouvé")

        result = {"lead_id": str(lead.id)}

        if data.create_contact:
            # Créer un contact dans le module CRM
            contact_id = await self._create_contact_from_lead(lead)
            lead.contact_id = contact_id
            result["contact_id"] = contact_id

        if data.create_opportunity:
            # Créer une opportunité commerciale
            opportunity_id = await self._create_opportunity_from_lead(
                lead, data.opportunity_value
            )
            lead.opportunity_id = opportunity_id
            result["opportunity_id"] = opportunity_id

        lead.status = LeadStatus.WON
        lead.converted_at = datetime.utcnow()

        if data.notes:
            lead.notes = (lead.notes or "") + f"\n\nConversion: {data.notes}"

        self.db.commit()
        self.db.refresh(lead)

        # Mettre à jour les compteurs de campagne
        if lead.campaign_id:
            self._update_campaign_conversion_count(UUID(lead.campaign_id))

        logger.info(f"[SOCIAL] Lead converti: {lead.id}")
        return result

    def get_lead_funnel(self, campaign_id: Optional[UUID] = None) -> LeadFunnel:
        """Calcule l'entonnoir de conversion des leads."""
        query = self._lead_query()

        if campaign_id:
            query = query.filter(SocialLead.campaign_id == str(campaign_id))

        leads = query.all()

        funnel = LeadFunnel(
            total_leads=len(leads),
            new=len([l for l in leads if l.status == LeadStatus.NEW]),
            contacted=len([l for l in leads if l.status == LeadStatus.CONTACTED]),
            qualified=len([l for l in leads if l.status == LeadStatus.QUALIFIED]),
            proposal=len([l for l in leads if l.status == LeadStatus.PROPOSAL]),
            negotiation=len([l for l in leads if l.status == LeadStatus.NEGOTIATION]),
            won=len([l for l in leads if l.status == LeadStatus.WON]),
            lost=len([l for l in leads if l.status == LeadStatus.LOST])
        )

        if funnel.total_leads > 0:
            funnel.conversion_rate = Decimal(funnel.won) / Decimal(funnel.total_leads) * 100

        return funnel

    def _calculate_lead_score(self, lead: SocialLead) -> int:
        """Calcule le score de qualification d'un lead."""
        score = 0

        # Points pour les informations de contact
        if lead.email:
            score += 20
            if lead.email.endswith(('.com', '.fr', '.eu')):
                score += 5
        if lead.phone:
            score += 15

        # Points pour les informations entreprise
        if lead.company:
            score += 15
        if lead.job_title:
            score += 10
            if any(t in lead.job_title.lower() for t in ['directeur', 'manager', 'responsable', 'ceo', 'dg']):
                score += 10

        # Points pour l'intérêt exprimé
        if lead.interest:
            score += 10

        # Points pour le budget
        if lead.budget_range:
            score += 10
            if 'k' in lead.budget_range.lower() or '000' in lead.budget_range:
                score += 5

        # Points pour le timeline
        if lead.timeline:
            score += 5
            if any(t in lead.timeline.lower() for t in ['urgent', 'immédiat', '1 mois', '3 mois']):
                score += 10

        return min(score, 100)

    async def _create_contact_from_lead(self, lead: SocialLead) -> str:
        """Crée un contact CRM à partir d'un lead."""
        # TODO: Intégration avec le module contacts
        from app.modules.contacts.service import ContactService

        contact_service = ContactService(self.db, self.tenant_id)

        contact_data = {
            "email": lead.email,
            "phone": lead.phone,
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "company": lead.company,
            "job_title": lead.job_title,
            "source": f"social_{lead.source.value}",
            "notes": f"Lead converti depuis {lead.source.value}"
        }

        contact = contact_service.create(contact_data)
        return str(contact.id)

    async def _create_opportunity_from_lead(
        self,
        lead: SocialLead,
        value: Optional[Decimal] = None
    ) -> str:
        """Crée une opportunité commerciale à partir d'un lead."""
        # TODO: Intégration avec le module commercial
        # Pour l'instant, retourne un ID fictif
        return f"OPP-{lead.id[:8]}"

    # ============================================================
    # TEMPLATES
    # ============================================================

    def _template_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(PostTemplate).filter(
            PostTemplate.tenant_id == self.tenant_id
        )

    def list_templates(
        self,
        category: Optional[str] = None,
        active_only: bool = True,
        limit: int = 50
    ) -> List[PostTemplate]:
        """Liste les templates."""
        query = self._template_query()

        if category:
            query = query.filter(PostTemplate.category == category)
        if active_only:
            query = query.filter(PostTemplate.is_active == True)

        return query.order_by(PostTemplate.usage_count.desc()).limit(limit).all()

    def get_template(self, template_id: UUID) -> Optional[PostTemplate]:
        """Récupère un template par ID."""
        return self._template_query().filter(
            PostTemplate.id == str(template_id)
        ).first()

    def create_template(self, data: TemplateCreate, user_id: Optional[str] = None) -> PostTemplate:
        """Crée un nouveau template."""
        template = PostTemplate(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data.model_dump()
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        logger.info(f"[SOCIAL] Template créé: {template.name}")
        return template

    def update_template(self, template_id: UUID, data: TemplateUpdate) -> Optional[PostTemplate]:
        """Met à jour un template."""
        template = self.get_template(template_id)
        if not template:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        self.db.commit()
        self.db.refresh(template)

        return template

    def render_template(self, data: TemplateRenderRequest) -> TemplateRenderResponse:
        """Rend un template avec les variables fournies."""
        template = self.get_template(data.template_id)
        if not template:
            raise ValueError("Template non trouvé")

        content = template.content_template
        warnings = []

        # Remplacer les variables
        for var in template.variables:
            var_name = var.get('name') if isinstance(var, dict) else var.name
            placeholder = f"{{{var_name}}}"

            if placeholder in content:
                value = data.variables.get(var_name, "")
                if not value and var.get('required', False):
                    warnings.append(f"Variable requise manquante: {var_name}")
                    value = var.get('default_value', f"[{var_name}]")
                content = content.replace(placeholder, value)

        # Incrémenter le compteur d'utilisation
        template.usage_count += 1
        self.db.commit()

        return TemplateRenderResponse(
            content=content,
            hashtags=template.suggested_hashtags or [],
            platforms=data.platforms or [MarketingPlatform(p) for p in template.recommended_platforms],
            warnings=warnings
        )

    def delete_template(self, template_id: UUID) -> bool:
        """Supprime un template."""
        template = self.get_template(template_id)
        if not template:
            return False

        self.db.delete(template)
        self.db.commit()

        return True

    # ============================================================
    # CALENDRIER & CRÉNEAUX
    # ============================================================

    def get_publishing_slots(
        self,
        platform: Optional[MarketingPlatform] = None
    ) -> List[PublishingSlot]:
        """Récupère les créneaux de publication."""
        query = self.db.query(PublishingSlot).filter(
            PublishingSlot.tenant_id == self.tenant_id
        )

        if platform:
            query = query.filter(PublishingSlot.platform == platform)

        return query.order_by(
            PublishingSlot.day_of_week,
            PublishingSlot.hour
        ).all()

    def create_publishing_slot(self, data: PublishingSlotCreate) -> PublishingSlot:
        """Crée un créneau de publication."""
        slot = PublishingSlot(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )

        self.db.add(slot)
        self.db.commit()
        self.db.refresh(slot)

        return slot

    def get_optimal_publish_time(
        self,
        platform: MarketingPlatform,
        preferred_date: Optional[date] = None
    ) -> Optional[datetime]:
        """Trouve le meilleur moment pour publier."""
        if not preferred_date:
            preferred_date = date.today()

        day_of_week = preferred_date.weekday()

        # Chercher un créneau optimal pour ce jour
        slot = self.db.query(PublishingSlot).filter(
            and_(
                PublishingSlot.tenant_id == self.tenant_id,
                PublishingSlot.platform == platform,
                PublishingSlot.day_of_week == day_of_week,
                PublishingSlot.is_optimal == True
            )
        ).order_by(PublishingSlot.avg_engagement.desc()).first()

        if slot:
            return datetime.combine(preferred_date, datetime.min.time().replace(
                hour=slot.hour, minute=slot.minute
            ))

        # Sinon, retourner des heures par défaut selon la plateforme
        default_hours = {
            MarketingPlatform.LINKEDIN: 9,
            MarketingPlatform.META_FACEBOOK: 12,
            MarketingPlatform.META_INSTAGRAM: 18,
            MarketingPlatform.TWITTER: 10
        }

        hour = default_hours.get(platform, 12)
        return datetime.combine(preferred_date, datetime.min.time().replace(hour=hour))

    def get_calendar_view(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """Vue calendrier des publications."""
        posts = self._post_query().filter(
            and_(
                SocialPost.scheduled_at >= start_date,
                SocialPost.scheduled_at <= end_date
            )
        ).all()

        # Grouper par jour
        calendar = {}
        current = start_date
        while current <= end_date:
            calendar[current.isoformat()] = {
                "date": current,
                "posts": []
            }
            current += timedelta(days=1)

        for post in posts:
            if post.scheduled_at:
                day_key = post.scheduled_at.date().isoformat()
                if day_key in calendar:
                    calendar[day_key]["posts"].append(post)

        return list(calendar.values())

    # ============================================================
    # ANALYTICS
    # ============================================================

    def get_platform_performance(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[PlatformPerformance]:
        """Analyse la performance par plateforme."""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        posts = self._post_query().filter(
            and_(
                SocialPost.status == PostStatus.PUBLISHED,
                SocialPost.published_at >= start_date,
                SocialPost.published_at <= end_date
            )
        ).all()

        # Agréger par plateforme
        platform_stats = {}

        for post in posts:
            for platform_str in post.platforms:
                platform = MarketingPlatform(platform_str)
                if platform not in platform_stats:
                    platform_stats[platform] = {
                        "posts_count": 0,
                        "impressions": 0,
                        "reach": 0,
                        "clicks": 0,
                        "engagement": 0,
                        "best_engagement": 0,
                        "best_post_id": None
                    }

                stats = platform_stats[platform]
                stats["posts_count"] += 1
                stats["impressions"] += post.impressions or 0
                stats["reach"] += post.reach or 0
                stats["clicks"] += post.clicks or 0

                engagement = (post.likes or 0) + (post.comments or 0) + (post.shares or 0)
                stats["engagement"] += engagement

                if engagement > stats["best_engagement"]:
                    stats["best_engagement"] = engagement
                    stats["best_post_id"] = post.id

        result = []
        for platform, stats in platform_stats.items():
            avg_rate = Decimal("0")
            if stats["impressions"] > 0:
                avg_rate = Decimal(stats["engagement"]) / Decimal(stats["impressions"]) * 100

            result.append(PlatformPerformance(
                platform=platform,
                posts_count=stats["posts_count"],
                total_impressions=stats["impressions"],
                total_reach=stats["reach"],
                total_clicks=stats["clicks"],
                total_engagement=stats["engagement"],
                avg_engagement_rate=avg_rate,
                best_post_id=UUID(stats["best_post_id"]) if stats["best_post_id"] else None
            ))

        return result

    async def generate_content_suggestions(
        self,
        topic: str,
        platforms: List[MarketingPlatform],
        count: int = 3
    ) -> List[ContentSuggestion]:
        """Génère des suggestions de contenu via IA."""
        # TODO: Intégration avec Marceau/IA
        # Pour l'instant, retourne des suggestions basiques

        suggestions = []

        base_hashtags = {
            MarketingPlatform.LINKEDIN: ["#ERP", "#SaaS", "#GestionEntreprise", "#PME"],
            MarketingPlatform.META_FACEBOOK: ["#erp", "#gestion", "#entreprise"],
            MarketingPlatform.META_INSTAGRAM: ["#business", "#entrepreneur", "#gestion"],
            MarketingPlatform.TWITTER: ["#ERP", "#SaaS", "#Tech"]
        }

        for i in range(count):
            hashtags = []
            for p in platforms:
                hashtags.extend(base_hashtags.get(p, []))

            suggestions.append(ContentSuggestion(
                title=f"Suggestion {i+1}: {topic}",
                content=f"Découvrez comment AZALSCORE peut transformer votre gestion d'entreprise avec notre solution ERP complète. {topic}",
                hashtags=list(set(hashtags)),
                best_platforms=platforms,
                relevance_score=Decimal("0.8") - Decimal(i) * Decimal("0.1")
            ))

        return suggestions

    # ============================================================
    # HELPERS
    # ============================================================

    def _generate_utm_slug(self, name: str) -> str:
        """Génère un slug UTM à partir d'un nom."""
        slug = re.sub(r'[^a-z0-9]+', '-', name.lower())
        slug = slug.strip('-')
        return slug[:50]

    def _update_campaign_post_count(self, campaign_id: UUID):
        """Met à jour le compteur de posts d'une campagne."""
        campaign = self.get_campaign(campaign_id)
        if campaign:
            count = self._post_query().filter(
                SocialPost.campaign_id == str(campaign_id)
            ).count()
            campaign.total_posts = count
            self.db.commit()

    def _update_campaign_lead_count(self, campaign_id: UUID):
        """Met à jour le compteur de leads d'une campagne."""
        campaign = self.get_campaign(campaign_id)
        if campaign:
            count = self._lead_query().filter(
                SocialLead.campaign_id == str(campaign_id)
            ).count()
            campaign.total_leads = count
            self.db.commit()

    def _update_campaign_conversion_count(self, campaign_id: UUID):
        """Met à jour le compteur de conversions d'une campagne."""
        campaign = self.get_campaign(campaign_id)
        if campaign:
            count = self._lead_query().filter(
                and_(
                    SocialLead.campaign_id == str(campaign_id),
                    SocialLead.status == LeadStatus.WON
                )
            ).count()
            campaign.total_conversions = count
            self.db.commit()
