"""
AZALS MODULE - Auto-Enrichment - Router
========================================

Endpoints API pour l'enrichissement automatique.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission, get_saas_context, get_saas_core
from app.core.models import User

from .models import EnrichmentProvider, EnrichmentStatus, EntityType, LookupType
from .schemas import (
    AddressSuggestion,
    EnrichmentAcceptRequest,
    EnrichmentAcceptResponse,
    EnrichmentHistoryResponse,
    EnrichmentLookupRequest,
    EnrichmentLookupResponse,
    EnrichmentStatsResponse,
)
from .service import get_enrichment_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enrichment", tags=["Auto-Enrichment"])


# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_service(request: Request, db: Session = Depends(get_db)):
    """Factory pour EnrichmentService avec tenant isolation."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant non identifie")
    return get_enrichment_service(db, tenant_id)


# ============================================================================
# LOOKUP ENDPOINTS
# ============================================================================

@router.post("/lookup", response_model=EnrichmentLookupResponse)
async def lookup_enrichment(
    data: EnrichmentLookupRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recherche d'enrichissement depuis les APIs externes.

    Supporte:
    - **SIRET/SIREN**: Lookup entreprises francaises (INSEE)
    - **address**: Autocomplete adresses francaises (API Adresse gouv.fr)
    - **barcode**: Lookup produits par code-barres (Open Food/Beauty/Pet Facts)

    L'enrichissement est mis en cache pour eviter les appels redondants.
    """
    service = get_service(request, db)

    try:
        result = await service.enrich(
            lookup_type=data.lookup_type,
            lookup_value=data.lookup_value,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            user_id=current_user.id,
        )

        return EnrichmentLookupResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.exception(f"[ENRICHMENT] Erreur lookup: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la recherche")


@router.get("/address/suggestions", response_model=list[AddressSuggestion])
async def get_address_suggestions(
    q: str = Query(
        ...,
        min_length=3,
        max_length=200,
        description="Texte de recherche d'adresse"
    ),
    limit: int = Query(5, ge=1, le=10, description="Nombre max de suggestions"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Autocomplete d'adresses francaises.

    Utilise l'API Adresse du gouvernement francais.
    Retourne jusqu'a 10 suggestions ordonnees par pertinence.
    """
    service = get_service(request, db)

    try:
        result = await service.enrich(
            lookup_type=LookupType.ADDRESS,
            lookup_value=q,
            entity_type=EntityType.CONTACT,
            user_id=current_user.id,
        )

        if result.get("success"):
            suggestions = result.get("suggestions", [])[:limit]
            return [AddressSuggestion(**s) for s in suggestions]

        return []

    except Exception as e:
        logger.exception(f"[ENRICHMENT] Erreur suggestions adresse: {e}")
        return []


@router.get("/siret/{siret}", response_model=EnrichmentLookupResponse)
async def lookup_siret(
    siret: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recherche entreprise par SIRET.

    Le SIRET doit etre compose de 14 chiffres.
    Les espaces sont automatiquement retires.
    """
    service = get_service(request, db)

    try:
        result = await service.enrich(
            lookup_type=LookupType.SIRET,
            lookup_value=siret,
            entity_type=EntityType.CONTACT,
            user_id=current_user.id,
        )

        return EnrichmentLookupResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/barcode/{barcode}", response_model=EnrichmentLookupResponse)
async def lookup_barcode(
    barcode: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recherche produit par code-barres.

    Supporte EAN-8, EAN-13, UPC-A, UPC-E.
    Essaie successivement Open Food Facts, Open Beauty Facts, Open Pet Food Facts.
    """
    service = get_service(request, db)

    try:
        result = await service.enrich(
            lookup_type=LookupType.BARCODE,
            lookup_value=barcode,
            entity_type=EntityType.PRODUCT,
            user_id=current_user.id,
        )

        return EnrichmentLookupResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/risk/{identifier}", response_model=EnrichmentLookupResponse)
async def analyze_risk(
    identifier: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = require_permission("enrichment.risk_analysis"),
):
    """
    Analyse de risque entreprise via Pappers.

    Retourne:
    - **Score de risque** (0-100): 100 = tres fiable, 0 = risque maximum
    - **Niveau**: low, medium, elevated, high
    - **Cotation Banque de France** (si disponible)
    - **Procedures collectives** en cours ou passees
    - **Alertes** et recommandations

    L'identifiant peut etre un SIREN (9 chiffres) ou SIRET (14 chiffres).

    Note: API gratuite limitee a ~100 req/mois.
    """
    service = get_service(request, db)

    try:
        result = await service.enrich(
            lookup_type=LookupType.RISK,
            lookup_value=identifier,
            entity_type=EntityType.CONTACT,
            user_id=current_user.id,
        )

        return EnrichmentLookupResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# ACCEPT/REJECT ENDPOINT
# ============================================================================

@router.post("/{history_id}/accept", response_model=EnrichmentAcceptResponse)
async def accept_enrichment(
    history_id: UUID,
    data: EnrichmentAcceptRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accepte ou rejette les donnees enrichies.

    Enregistre la decision de l'utilisateur pour l'audit.
    """
    service = get_service(request, db)

    try:
        history = service.accept_enrichment(
            history_id=history_id,
            accepted_fields=data.accepted_fields,
            rejected_fields=data.rejected_fields,
            user_id=current_user.id,
        )

        return EnrichmentAcceptResponse(
            message="Decision enregistree",
            history_id=str(history.id),
            action=history.action.value,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# HISTORY ENDPOINTS
# ============================================================================

@router.get("/history", response_model=list[EnrichmentHistoryResponse])
async def get_enrichment_history(
    entity_type: Optional[EntityType] = Query(None, description="Filtrer par type d'entite"),
    entity_id: Optional[UUID] = Query(None, description="Filtrer par ID d'entite"),
    provider: Optional[EnrichmentProvider] = Query(None, description="Filtrer par provider"),
    status: Optional[EnrichmentStatus] = Query(None, description="Filtrer par statut"),
    limit: int = Query(50, ge=1, le=200, description="Nombre max de resultats"),
    offset: int = Query(0, ge=0, description="Offset pour pagination"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recupere l'historique des enrichissements.

    Permet de voir toutes les tentatives d'enrichissement avec leur statut.
    """
    service = get_service(request, db)

    history, total = service.get_history(
        entity_type=entity_type,
        entity_id=entity_id,
        provider=provider,
        status=status,
        limit=limit,
        offset=offset,
    )

    return [EnrichmentHistoryResponse.from_orm_custom(h) for h in history]


@router.get("/history/{history_id}", response_model=EnrichmentHistoryResponse)
async def get_enrichment_by_id(
    history_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recupere un enrichissement specifique par son ID.
    """
    service = get_service(request, db)

    history, total = service.get_history(limit=1)

    # Rechercher par ID
    from .models import EnrichmentHistory
    tenant_id = getattr(request.state, "tenant_id", None)

    history_item = db.query(EnrichmentHistory).filter(
        EnrichmentHistory.id == history_id,
        EnrichmentHistory.tenant_id == tenant_id,
    ).first()

    if not history_item:
        raise HTTPException(status_code=404, detail="Enrichissement non trouve")

    return EnrichmentHistoryResponse.from_orm_custom(history_item)


# ============================================================================
# STATS ENDPOINT
# ============================================================================

@router.get("/stats", response_model=EnrichmentStatsResponse)
async def get_enrichment_stats(
    days: int = Query(30, ge=1, le=365, description="Nombre de jours a analyser"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Statistiques d'enrichissement.

    Retourne les metriques d'utilisation sur la periode specifiee.
    """
    service = get_service(request, db)
    stats = service.get_stats(days=days)
    return EnrichmentStatsResponse(**stats)


# ============================================================================
# RISK ALERTS ENDPOINT (COCKPIT)
# ============================================================================

@router.get("/risk/alerts", response_model=list[dict])
async def get_risk_alerts(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = require_permission("enrichment.risk_analysis"),
):
    """
    Recupere les partenaires a risque eleve pour le Cockpit.

    Retourne les analyses de risque recentes avec niveau elevated ou high.
    Utilise pour les alertes du tableau de bord.
    """
    from .models import EnrichmentHistory
    from datetime import timedelta

    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant non identifie")

    # Recuperer les analyses de risque des 30 derniers jours
    cutoff_date = datetime.utcnow() - timedelta(days=30)

    risk_analyses = db.query(EnrichmentHistory).filter(
        EnrichmentHistory.tenant_id == tenant_id,
        EnrichmentHistory.lookup_type == LookupType.RISK,
        EnrichmentHistory.status == EnrichmentStatus.SUCCESS,
        EnrichmentHistory.created_at >= cutoff_date,
    ).order_by(EnrichmentHistory.created_at.desc()).all()

    # Filtrer et formater les alertes
    alerts = []
    seen_identifiers = set()

    for analysis in risk_analyses:
        # Ne garder que la plus recente par identifiant
        if analysis.lookup_value in seen_identifiers:
            continue
        seen_identifiers.add(analysis.lookup_value)

        # Extraire les donnees de risque
        response_data = analysis.response_data or {}
        enriched_fields = analysis.enriched_fields or {}

        level = response_data.get("level", "low")

        # Seulement les risques eleves
        if level not in ("elevated", "high"):
            continue

        alerts.append({
            "id": str(analysis.id),
            "identifier": analysis.lookup_value,
            "partner_name": enriched_fields.get("name", response_data.get("company_name", "Entreprise inconnue")),
            "score": response_data.get("score", 0),
            "level": level,
            "level_label": response_data.get("level_label", level.capitalize()),
            "alerts": response_data.get("alerts", []),
            "recommendation": response_data.get("recommendation", ""),
            "analyzed_at": analysis.created_at.isoformat() if analysis.created_at else None,
        })

    return alerts


# ============================================================================
# INTERNAL SCORING ENDPOINT
# ============================================================================

@router.get("/score/internal/{customer_id}", response_model=EnrichmentLookupResponse)
async def get_internal_score(
    customer_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Calcule le score de risque interne d'un client.

    Basé sur l'historique dans AZALSCORE:
    - Ancienneté du compte
    - Historique de paiement
    - Factures en retard
    - Volume de commandes

    Fonctionne pour tous les types de clients:
    - Particuliers
    - Professionnels
    - Donneurs d'ordre

    Args:
        customer_id: UUID du client

    Returns:
        Score (0-100), niveau de risque, facteurs et recommandations
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant non identifié")

    try:
        # Valider l'UUID
        try:
            PyUUID(customer_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="ID client invalide")

        # Créer le provider de scoring interne
        provider = InternalScoringProvider(tenant_id, db)

        # Calculer le score
        result = await provider.lookup("internal_score", customer_id)

        if not result.success:
            return EnrichmentLookupResponse(
                success=False,
                enriched_fields={},
                confidence=0.0,
                source="internal_scoring",
                cached=False,
                history_id=None,
                suggestions=[],
                error=result.error,
            )

        # Mapper les champs
        enriched_fields = provider.map_to_entity("contact", result.data)

        # Enregistrer dans l'historique
        from .models import EnrichmentHistory, EnrichmentProvider, EnrichmentStatus

        history = EnrichmentHistory(
            tenant_id=tenant_id,
            entity_type=EntityType.CONTACT,
            entity_id=PyUUID(customer_id),
            lookup_type=LookupType.INTERNAL_SCORE,
            lookup_value=customer_id,
            provider=EnrichmentProvider.INSEE,  # Utiliser INSEE comme placeholder
            status=EnrichmentStatus.SUCCESS,
            response_data=result.data,
            enriched_fields=enriched_fields,
            confidence_score=result.confidence,
            api_response_time_ms=result.response_time_ms,
            cached=False,
            created_by=current_user.id,
        )
        db.add(history)
        db.commit()

        return EnrichmentLookupResponse(
            success=True,
            enriched_fields=enriched_fields,
            confidence=result.confidence,
            source="internal_scoring",
            cached=False,
            history_id=str(history.id),
            suggestions=[],
            error=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[INTERNAL_SCORING] Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from .providers.internal_scoring import InternalScoringProvider
