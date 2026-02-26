"""
AZALS MODULE - Publications Réseaux Sociaux - Router API
========================================================

Endpoints pour la création et gestion de publications
afin de générer des leads vers azalscore.com.

Routes préfixées: /api/v3/social/publications
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_tenant_id, get_current_user

from .models import MarketingPlatform
from .publication_models import PostStatus, CampaignStatus, LeadStatus, LeadSource
from .publication_schemas import (
    # Campagnes
    CampaignCreate, CampaignUpdate, CampaignResponse, CampaignStats,
    # Publications
    PostCreate, PostUpdate, PostResponse, PostScheduleRequest, PostPublishRequest, PostBulkCreate,
    # Leads
    LeadCreate, LeadUpdate, LeadResponse, LeadInteraction, LeadConvertRequest, LeadBulkAction, LeadFunnel,
    # Templates
    TemplateCreate, TemplateUpdate, TemplateResponse, TemplateRenderRequest, TemplateRenderResponse,
    # Calendrier
    PublishingSlotCreate, PublishingSlotResponse, CalendarView, WeeklySchedule,
    # Analytics
    PlatformPerformance, ContentSuggestion
)
from .publication_service import PublicationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/social/publications", tags=["Réseaux Sociaux - Publications & Leads"])


# === Dépendance pour le service ===

def get_publication_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> PublicationService:
    return PublicationService(db, tenant_id)


# ============================================================
# CAMPAGNES
# ============================================================

@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[CampaignStatus] = Query(None, description="Filtrer par statut"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Liste les campagnes marketing.

    Les campagnes regroupent plusieurs publications avec un objectif commun
    (génération de leads, notoriété, engagement).
    """
    return service.list_campaigns(status=status, limit=limit, offset=offset)


@router.post("/campaigns", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    data: CampaignCreate,
    service: PublicationService = Depends(get_publication_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Crée une nouvelle campagne marketing.

    Une campagne permet de :
    - Regrouper des publications par objectif
    - Suivre les performances globales
    - Tracker les leads générés
    - Mesurer le ROI
    """
    user_id = current_user.get("id") if current_user else None
    return service.create_campaign(data, user_id=user_id)


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    service: PublicationService = Depends(get_publication_service)
):
    """Récupère une campagne par son ID."""
    campaign = service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campagne non trouvée")
    return campaign


@router.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    data: CampaignUpdate,
    service: PublicationService = Depends(get_publication_service)
):
    """Met à jour une campagne."""
    campaign = service.update_campaign(campaign_id, data)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campagne non trouvée")
    return campaign


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: UUID,
    service: PublicationService = Depends(get_publication_service)
):
    """Supprime une campagne et ses publications associées."""
    deleted = service.delete_campaign(campaign_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Campagne non trouvée")
    return {"status": "deleted", "id": str(campaign_id)}


@router.get("/campaigns/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: UUID,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Récupère les statistiques détaillées d'une campagne.

    Inclut : posts publiés, impressions, clics, leads générés,
    taux de conversion, coût par lead.
    """
    try:
        return service.get_campaign_stats(campaign_id, start_date, end_date)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# PUBLICATIONS
# ============================================================

@router.get("/posts", response_model=List[PostResponse])
async def list_posts(
    status: Optional[PostStatus] = Query(None, description="Filtrer par statut"),
    campaign_id: Optional[UUID] = Query(None, description="Filtrer par campagne"),
    platform: Optional[MarketingPlatform] = Query(None, description="Filtrer par plateforme"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Liste les publications avec filtres.

    Statuts possibles : draft, scheduled, publishing, published, failed, archived
    """
    return service.list_posts(
        status=status,
        campaign_id=campaign_id,
        platform=platform,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )


@router.post("/posts", response_model=PostResponse, status_code=201)
async def create_post(
    data: PostCreate,
    service: PublicationService = Depends(get_publication_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Crée une nouvelle publication.

    La publication peut être :
    - En brouillon (draft) pour édition ultérieure
    - Programmée (scheduled) avec une date/heure
    - Publiée immédiatement via l'endpoint /publish

    Le tracking UTM est généré automatiquement pour mesurer les conversions.
    """
    user_id = current_user.get("id") if current_user else None
    return service.create_post(data, user_id=user_id)


@router.post("/posts/bulk", response_model=List[PostResponse], status_code=201)
async def create_posts_bulk(
    data: PostBulkCreate,
    service: PublicationService = Depends(get_publication_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Crée plusieurs publications en une fois.

    Utile pour programmer une série de posts pour une campagne.
    """
    user_id = current_user.get("id") if current_user else None
    posts = []
    for post_data in data.posts:
        if data.campaign_id and not post_data.campaign_id:
            post_data.campaign_id = data.campaign_id
        post = service.create_post(post_data, user_id=user_id)
        posts.append(post)
    return posts


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    service: PublicationService = Depends(get_publication_service)
):
    """Récupère une publication par son ID."""
    post = service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Publication non trouvée")
    return post


@router.put("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: UUID,
    data: PostUpdate,
    service: PublicationService = Depends(get_publication_service)
):
    """
    Met à jour une publication.

    Note: Les publications déjà publiées ne peuvent pas être modifiées.
    """
    try:
        post = service.update_post(post_id, data)
        if not post:
            raise HTTPException(status_code=404, detail="Publication non trouvée")
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: UUID,
    service: PublicationService = Depends(get_publication_service)
):
    """Supprime une publication."""
    deleted = service.delete_post(post_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Publication non trouvée")
    return {"status": "deleted", "id": str(post_id)}


@router.post("/posts/{post_id}/schedule", response_model=PostResponse)
async def schedule_post(
    post_id: UUID,
    scheduled_at: datetime = Query(..., description="Date et heure de publication"),
    platforms: Optional[List[MarketingPlatform]] = Query(None),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Programme une publication pour une date/heure spécifique.

    La publication sera automatiquement envoyée aux plateformes
    sélectionnées à l'heure programmée.
    """
    try:
        data = PostScheduleRequest(
            post_id=post_id,
            scheduled_at=scheduled_at,
            platforms=platforms
        )
        return service.schedule_post(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/posts/{post_id}/publish", response_model=PostResponse)
async def publish_post(
    post_id: UUID,
    platforms: Optional[List[MarketingPlatform]] = Query(None),
    background_tasks: BackgroundTasks = None,
    service: PublicationService = Depends(get_publication_service)
):
    """
    Publie immédiatement une publication sur les plateformes sélectionnées.

    Si aucune plateforme n'est spécifiée, utilise celles définies dans le post.
    """
    try:
        post = await service.publish_post(post_id, platforms)
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/posts/{post_id}/duplicate", response_model=PostResponse)
async def duplicate_post(
    post_id: UUID,
    service: PublicationService = Depends(get_publication_service)
):
    """
    Duplique une publication existante.

    Crée une copie en mode brouillon que vous pouvez modifier et reprogrammer.
    """
    try:
        return service.duplicate_post(post_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# LEADS
# ============================================================

@router.get("/leads", response_model=List[LeadResponse])
async def list_leads(
    status: Optional[LeadStatus] = Query(None, description="Filtrer par statut"),
    source: Optional[LeadSource] = Query(None, description="Filtrer par source"),
    campaign_id: Optional[UUID] = Query(None, description="Filtrer par campagne"),
    assigned_to: Optional[str] = Query(None, description="Filtrer par commercial"),
    search: Optional[str] = Query(None, description="Recherche email, nom, entreprise"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Liste les leads générés via les réseaux sociaux.

    Statuts du funnel : new → contacted → qualified → proposal → negotiation → won/lost
    """
    return service.list_leads(
        status=status,
        source=source,
        campaign_id=campaign_id,
        assigned_to=assigned_to,
        search=search,
        limit=limit,
        offset=offset
    )


@router.post("/leads", response_model=LeadResponse, status_code=201)
async def create_lead(
    data: LeadCreate,
    service: PublicationService = Depends(get_publication_service)
):
    """
    Enregistre un nouveau lead.

    Le score de qualification est calculé automatiquement selon
    les informations fournies (email, entreprise, budget, etc.).
    """
    return service.create_lead(data)


@router.get("/leads/funnel", response_model=LeadFunnel)
async def get_lead_funnel(
    campaign_id: Optional[UUID] = Query(None, description="Filtrer par campagne"),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Récupère l'entonnoir de conversion des leads.

    Affiche la répartition par statut et le taux de conversion global.
    """
    return service.get_lead_funnel(campaign_id)


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    service: PublicationService = Depends(get_publication_service)
):
    """Récupère un lead par son ID."""
    lead = service.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead non trouvé")
    return lead


@router.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    data: LeadUpdate,
    service: PublicationService = Depends(get_publication_service)
):
    """
    Met à jour un lead.

    Le score est recalculé automatiquement si des informations
    importantes sont modifiées.
    """
    lead = service.update_lead(lead_id, data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead non trouvé")
    return lead


@router.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: UUID,
    service: PublicationService = Depends(get_publication_service)
):
    """Supprime un lead."""
    deleted = service.delete_lead(lead_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Lead non trouvé")
    return {"status": "deleted", "id": str(lead_id)}


@router.post("/leads/{lead_id}/interactions", response_model=LeadResponse)
async def add_lead_interaction(
    lead_id: UUID,
    interaction: LeadInteraction,
    service: PublicationService = Depends(get_publication_service)
):
    """
    Ajoute une interaction avec un lead.

    Types : email, call, meeting, note

    Le statut passe automatiquement à 'contacted' lors du premier contact.
    """
    try:
        return service.add_lead_interaction(lead_id, interaction)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/leads/{lead_id}/convert")
async def convert_lead(
    lead_id: UUID,
    create_contact: bool = Query(True, description="Créer un contact CRM"),
    create_opportunity: bool = Query(False, description="Créer une opportunité commerciale"),
    opportunity_value: Optional[float] = Query(None, description="Valeur de l'opportunité"),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Convertit un lead en client.

    Peut créer automatiquement :
    - Un contact dans le CRM
    - Une opportunité commerciale
    """
    try:
        data = LeadConvertRequest(
            lead_id=lead_id,
            create_contact=create_contact,
            create_opportunity=create_opportunity,
            opportunity_value=opportunity_value
        )
        return await service.convert_lead(data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/leads/bulk-action")
async def bulk_action_leads(
    data: LeadBulkAction,
    service: PublicationService = Depends(get_publication_service)
):
    """
    Effectue une action en masse sur plusieurs leads.

    Actions possibles : assign, tag, status, delete
    """
    updated = 0
    errors = []

    for lead_id in data.lead_ids:
        try:
            lead = service.get_lead(lead_id)
            if not lead:
                errors.append(f"Lead {lead_id} non trouvé")
                continue

            if data.action == "assign":
                lead.assigned_to = data.value
            elif data.action == "tag":
                tags = lead.tags or []
                if data.value not in tags:
                    tags.append(data.value)
                    lead.tags = tags
            elif data.action == "status":
                lead.status = LeadStatus(data.value)
            elif data.action == "delete":
                service.delete_lead(lead_id)
                updated += 1
                continue

            service.db.commit()
            updated += 1

        except Exception as e:
            errors.append(f"Lead {lead_id}: {str(e)}")

    return {
        "updated": updated,
        "total": len(data.lead_ids),
        "errors": errors
    }


# ============================================================
# TEMPLATES
# ============================================================

@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    category: Optional[str] = Query(None, description="promo, event, tips, testimonial"),
    active_only: bool = Query(True),
    limit: int = Query(50, le=100),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Liste les templates de publication.

    Les templates permettent de créer rapidement des posts
    avec un contenu pré-formaté et des hashtags suggérés.
    """
    return service.list_templates(category=category, active_only=active_only, limit=limit)


@router.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(
    data: TemplateCreate,
    service: PublicationService = Depends(get_publication_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Crée un nouveau template de publication.

    Utilisez des variables comme {product}, {feature}, {benefit}
    qui seront remplacées lors du rendu.
    """
    user_id = current_user.get("id") if current_user else None
    return service.create_template(data, user_id=user_id)


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    service: PublicationService = Depends(get_publication_service)
):
    """Récupère un template par son ID."""
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    service: PublicationService = Depends(get_publication_service)
):
    """Met à jour un template."""
    template = service.update_template(template_id, data)
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: UUID,
    service: PublicationService = Depends(get_publication_service)
):
    """Supprime un template."""
    deleted = service.delete_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return {"status": "deleted", "id": str(template_id)}


@router.post("/templates/{template_id}/render", response_model=TemplateRenderResponse)
async def render_template(
    template_id: UUID,
    variables: dict = {},
    platforms: Optional[List[MarketingPlatform]] = Query(None),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Rend un template avec les variables fournies.

    Retourne le contenu prêt à être publié avec les hashtags suggérés.
    """
    try:
        data = TemplateRenderRequest(
            template_id=template_id,
            variables=variables,
            platforms=platforms
        )
        return service.render_template(data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# CALENDRIER
# ============================================================

@router.get("/calendar", response_model=List[CalendarView])
async def get_calendar_view(
    start_date: date = Query(..., description="Date de début"),
    end_date: date = Query(..., description="Date de fin"),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Vue calendrier des publications programmées.

    Affiche les posts par jour avec les créneaux optimaux suggérés.
    """
    return service.get_calendar_view(start_date, end_date)


@router.get("/slots", response_model=List[PublishingSlotResponse])
async def get_publishing_slots(
    platform: Optional[MarketingPlatform] = Query(None),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Liste les créneaux de publication optimaux.

    Basés sur les performances historiques de vos publications.
    """
    return service.get_publishing_slots(platform)


@router.post("/slots", response_model=PublishingSlotResponse, status_code=201)
async def create_publishing_slot(
    data: PublishingSlotCreate,
    service: PublicationService = Depends(get_publication_service)
):
    """Crée un créneau de publication personnalisé."""
    return service.create_publishing_slot(data)


@router.get("/optimal-time")
async def get_optimal_publish_time(
    platform: MarketingPlatform,
    preferred_date: Optional[date] = Query(None),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Suggère le meilleur moment pour publier.

    Basé sur l'historique d'engagement de vos publications.
    """
    optimal = service.get_optimal_publish_time(platform, preferred_date)
    return {
        "platform": platform.value,
        "suggested_datetime": optimal.isoformat() if optimal else None,
        "day": optimal.strftime("%A") if optimal else None,
        "time": optimal.strftime("%H:%M") if optimal else None
    }


# ============================================================
# ANALYTICS
# ============================================================

@router.get("/analytics/platforms", response_model=List[PlatformPerformance])
async def get_platform_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Analyse la performance par plateforme.

    Compare les impressions, engagements et leads générés
    sur chaque réseau social.
    """
    return service.get_platform_performance(start_date, end_date)


@router.post("/analytics/suggestions", response_model=List[ContentSuggestion])
async def get_content_suggestions(
    topic: str = Query(..., description="Sujet du contenu"),
    platforms: List[MarketingPlatform] = Query(..., description="Plateformes cibles"),
    count: int = Query(3, ge=1, le=10, description="Nombre de suggestions"),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Génère des suggestions de contenu via IA.

    Propose des posts optimisés pour chaque plateforme
    avec hashtags et meilleur moment de publication.
    """
    return await service.generate_content_suggestions(topic, platforms, count)


# ============================================================
# WEBHOOK POUR TRACKING
# ============================================================

@router.post("/webhook/track")
async def track_conversion(
    utm_source: Optional[str] = None,
    utm_medium: Optional[str] = None,
    utm_campaign: Optional[str] = None,
    utm_content: Optional[str] = None,
    email: Optional[str] = None,
    event: str = Query(..., description="visit, signup, demo, purchase"),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Webhook pour tracker les conversions depuis le site web.

    Appelé par le site azalscore.com lors des événements de conversion.
    Permet d'attribuer les leads aux publications d'origine.
    """
    # Enregistrer l'événement
    logger.info(
        f"[TRACK] Event={event} UTM: source={utm_source}, medium={utm_medium}, "
        f"campaign={utm_campaign}, content={utm_content}, email={email}"
    )

    # Si c'est un signup avec email, créer ou mettre à jour le lead
    if event == "signup" and email:
        # Chercher un lead existant
        existing = service._lead_query().filter(
            service.db.query(service._lead_query().model).email == email
        ).first()

        if not existing:
            # Créer un nouveau lead
            lead_data = LeadCreate(
                source=LeadSource.WEBSITE,
                email=email,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                utm_content=utm_content
            )
            lead = service.create_lead(lead_data)
            return {"status": "lead_created", "lead_id": str(lead.id)}
        else:
            return {"status": "lead_exists", "lead_id": str(existing.id)}

    return {"status": "tracked", "event": event}


# ============================================================
# STATUTS ET ENUMS (pour l'UI)
# ============================================================

@router.get("/enums")
async def get_enums():
    """
    Retourne les valeurs possibles pour les enums.

    Utile pour construire les formulaires frontend.
    """
    return {
        "post_status": [s.value for s in PostStatus],
        "post_type": [t.value for t in PostType],
        "campaign_status": [s.value for s in CampaignStatus],
        "lead_status": [s.value for s in LeadStatus],
        "lead_source": [s.value for s in LeadSource],
        "platforms": [
            {"id": p.value, "name": p.name.replace("_", " ").title()}
            for p in MarketingPlatform
        ]
    }
