"""
AZALS MODULE - Auto-Enrichment - Router
========================================

Endpoints API pour l'enrichissement automatique.
"""
from __future__ import annotations


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
    - **vat_number**: Validation numero TVA UE (VIES)

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
# BODACC ENDPOINTS (Annonces légales)
# ============================================================================

@router.get("/bodacc/{identifier}")
async def check_bodacc(
    identifier: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Vérifie les annonces BODACC pour un SIREN/SIRET.

    Détecte les événements critiques:
    - **Dissolution**: Entreprise dissoute
    - **Liquidation judiciaire**: Procédure de liquidation en cours
    - **Redressement judiciaire**: Procédure de redressement en cours
    - **Radiation**: Entreprise radiée du RCS

    Args:
        identifier: SIREN (9 chiffres) ou SIRET (14 chiffres)

    Returns:
        Analyse de risque basée sur les annonces BODACC officielles
    """
    service = get_service(request, db)

    try:
        result = await service.check_bodacc(identifier)
        return result

    except Exception as e:
        logger.exception(f"[BODACC] Erreur vérification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-combined/{identifier}")
async def get_combined_risk(
    identifier: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyse de risque combinée (INSEE + BODACC + Pappers si disponible).

    Combine les données de plusieurs sources officielles pour une
    analyse de risque complète et fiable.

    Sources vérifiées:
    - **BODACC**: Annonces légales (dissolutions, liquidations, procédures)
    - **INSEE**: Données entreprise (statut, activité)
    - **Pappers**: Données RCS enrichies (si clé API configurée)

    Args:
        identifier: SIREN (9 chiffres) ou SIRET (14 chiffres)

    Returns:
        Score combiné et détails par source
    """
    service = get_service(request, db)

    try:
        result = await service.get_combined_risk_score(identifier)
        return result

    except Exception as e:
        logger.exception(f"[RISK] Erreur analyse combinée: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    from datetime import datetime, timedelta

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


# ============================================================================
# ADMIN - PROVIDER CONFIG ENDPOINTS
# ============================================================================

from .models import EnrichmentProviderConfig, PROVIDER_INFO
from .schemas import (
    ProviderInfoResponse,
    ProviderConfigResponse,
    ProviderConfigCreateRequest,
    ProviderConfigUpdateRequest,
    ProviderTestResult,
    ProvidersListResponse,
)


@router.get("/admin/providers", response_model=ProvidersListResponse)
async def list_provider_configs(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Liste tous les providers avec leur configuration pour ce tenant.

    Retourne:
    - Les providers configures avec leurs parametres
    - Les providers disponibles (non encore configures)
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant non identifie")

    # Recuperer les configs existantes
    configs = db.query(EnrichmentProviderConfig).filter(
        EnrichmentProviderConfig.tenant_id == tenant_id
    ).all()

    # Construire la liste des providers configures
    configured_providers = []
    configured_provider_codes = set()

    for config in configs:
        provider_info = PROVIDER_INFO.get(config.provider, {})
        configured_provider_codes.add(config.provider)

        configured_providers.append(ProviderConfigResponse(
            id=config.id,
            provider=config.provider.value,
            name=provider_info.get("name", config.provider.value),
            description=provider_info.get("description", ""),
            is_enabled=config.is_enabled,
            is_primary=config.is_primary,
            priority=config.priority,
            has_api_key=bool(config.api_key),
            requires_api_key=provider_info.get("requires_api_key", False),
            is_free=provider_info.get("is_free", True),
            country=provider_info.get("country", "UNKNOWN"),
            capabilities=provider_info.get("capabilities", []),
            custom_requests_per_minute=config.custom_requests_per_minute,
            custom_requests_per_day=config.custom_requests_per_day,
            last_success_at=config.last_success_at,
            last_error_at=config.last_error_at,
            last_error_message=config.last_error_message,
            total_requests=config.total_requests,
            total_errors=config.total_errors,
            created_at=config.created_at,
            updated_at=config.updated_at,
        ))

    # Construire la liste des providers disponibles (non configures)
    available_providers = []
    for provider_enum, info in PROVIDER_INFO.items():
        if provider_enum not in configured_provider_codes:
            available_providers.append(ProviderInfoResponse(
                provider=provider_enum.value,
                name=info.get("name", provider_enum.value),
                description=info.get("description", ""),
                requires_api_key=info.get("requires_api_key", False),
                is_free=info.get("is_free", True),
                country=info.get("country", "UNKNOWN"),
                capabilities=info.get("capabilities", []),
                documentation_url=info.get("documentation_url"),
            ))

    return ProvidersListResponse(
        providers=configured_providers,
        available_providers=available_providers,
    )


@router.post("/admin/providers", response_model=ProviderConfigResponse)
async def create_provider_config(
    data: ProviderConfigCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Configure un nouveau provider pour ce tenant.
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant non identifie")

    # Verifier si deja configure
    existing = db.query(EnrichmentProviderConfig).filter(
        EnrichmentProviderConfig.tenant_id == tenant_id,
        EnrichmentProviderConfig.provider == data.provider,
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Provider {data.provider.value} deja configure pour ce tenant"
        )

    # Creer la config
    config = EnrichmentProviderConfig(
        tenant_id=tenant_id,
        provider=data.provider,
        is_enabled=data.is_enabled,
        is_primary=data.is_primary,
        priority=data.priority,
        api_key=data.api_key,
        api_secret=data.api_secret,
        api_endpoint=data.api_endpoint,
        custom_requests_per_minute=data.custom_requests_per_minute,
        custom_requests_per_day=data.custom_requests_per_day,
        config_data=data.config_data or {},
        created_by=current_user.id,
    )

    db.add(config)
    db.commit()
    db.refresh(config)

    provider_info = PROVIDER_INFO.get(config.provider, {})

    return ProviderConfigResponse(
        id=config.id,
        provider=config.provider.value,
        name=provider_info.get("name", config.provider.value),
        description=provider_info.get("description", ""),
        is_enabled=config.is_enabled,
        is_primary=config.is_primary,
        priority=config.priority,
        has_api_key=bool(config.api_key),
        requires_api_key=provider_info.get("requires_api_key", False),
        is_free=provider_info.get("is_free", True),
        country=provider_info.get("country", "UNKNOWN"),
        capabilities=provider_info.get("capabilities", []),
        custom_requests_per_minute=config.custom_requests_per_minute,
        custom_requests_per_day=config.custom_requests_per_day,
        last_success_at=config.last_success_at,
        last_error_at=config.last_error_at,
        last_error_message=config.last_error_message,
        total_requests=config.total_requests,
        total_errors=config.total_errors,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.patch("/admin/providers/{provider_code}", response_model=ProviderConfigResponse)
async def update_provider_config(
    provider_code: str,
    data: ProviderConfigUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Met a jour la configuration d'un provider.
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant non identifie")

    # Trouver le provider
    try:
        provider_enum = EnrichmentProvider(provider_code)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Provider inconnu: {provider_code}")

    config = db.query(EnrichmentProviderConfig).filter(
        EnrichmentProviderConfig.tenant_id == tenant_id,
        EnrichmentProviderConfig.provider == provider_enum,
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")

    # Mettre a jour les champs fournis
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    config.updated_by = current_user.id

    db.commit()
    db.refresh(config)

    provider_info = PROVIDER_INFO.get(config.provider, {})

    return ProviderConfigResponse(
        id=config.id,
        provider=config.provider.value,
        name=provider_info.get("name", config.provider.value),
        description=provider_info.get("description", ""),
        is_enabled=config.is_enabled,
        is_primary=config.is_primary,
        priority=config.priority,
        has_api_key=bool(config.api_key),
        requires_api_key=provider_info.get("requires_api_key", False),
        is_free=provider_info.get("is_free", True),
        country=provider_info.get("country", "UNKNOWN"),
        capabilities=provider_info.get("capabilities", []),
        custom_requests_per_minute=config.custom_requests_per_minute,
        custom_requests_per_day=config.custom_requests_per_day,
        last_success_at=config.last_success_at,
        last_error_at=config.last_error_at,
        last_error_message=config.last_error_message,
        total_requests=config.total_requests,
        total_errors=config.total_errors,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.delete("/admin/providers/{provider_code}")
async def delete_provider_config(
    provider_code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Supprime la configuration d'un provider (retour aux valeurs par defaut).
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant non identifie")

    try:
        provider_enum = EnrichmentProvider(provider_code)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Provider inconnu: {provider_code}")

    config = db.query(EnrichmentProviderConfig).filter(
        EnrichmentProviderConfig.tenant_id == tenant_id,
        EnrichmentProviderConfig.provider == provider_enum,
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")

    db.delete(config)
    db.commit()

    return {"message": f"Configuration {provider_code} supprimee"}


@router.post("/admin/providers/{provider_code}/test", response_model=ProviderTestResult)
async def test_provider_connection(
    provider_code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Teste la connexion a un provider avec sa configuration actuelle.
    """
    import time

    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant non identifie")

    try:
        provider_enum = EnrichmentProvider(provider_code)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Provider inconnu: {provider_code}")

    # Obtenir le service pour ce tenant
    service = get_service(request, db)

    # Obtenir le provider
    provider = service._get_provider(provider_enum)
    if not provider:
        return ProviderTestResult(
            provider=provider_code,
            success=False,
            response_time_ms=0,
            error="Provider non disponible ou desactive",
        )

    # Test selon le type de provider
    start_time = time.time()
    test_value = ""
    test_type = ""

    if provider_enum == EnrichmentProvider.INSEE:
        test_type = "siret"
        test_value = "44306184100047"  # SIRET Google France
    elif provider_enum == EnrichmentProvider.VIES:
        test_type = "vat_number"
        test_value = "FR40303265045"  # TVA Google France
    elif provider_enum == EnrichmentProvider.PAPPERS:
        test_type = "siren"
        test_value = "443061841"  # SIREN Google France
    elif provider_enum == EnrichmentProvider.OPENCORPORATES:
        test_type = "name"
        test_value = "Google"
    elif provider_enum == EnrichmentProvider.ADRESSE_GOUV:
        test_type = "address"
        test_value = "8 rue de londres paris"
    elif provider_enum in (
        EnrichmentProvider.OPENFOODFACTS,
        EnrichmentProvider.OPENBEAUTYFACTS,
        EnrichmentProvider.OPENPETFOODFACTS,
    ):
        test_type = "barcode"
        test_value = "3017620422003"  # Nutella
    else:
        return ProviderTestResult(
            provider=provider_code,
            success=False,
            response_time_ms=0,
            error="Test non implemente pour ce provider",
        )

    try:
        result = await provider.lookup(test_type, test_value)
        response_time = int((time.time() - start_time) * 1000)

        if result.success:
            return ProviderTestResult(
                provider=provider_code,
                success=True,
                response_time_ms=response_time,
                details={
                    "test_type": test_type,
                    "test_value": test_value,
                    "confidence": result.confidence,
                    "cached": result.cached,
                }
            )
        else:
            return ProviderTestResult(
                provider=provider_code,
                success=False,
                response_time_ms=response_time,
                error=result.error or "Echec du test",
            )

    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        return ProviderTestResult(
            provider=provider_code,
            success=False,
            response_time_ms=response_time,
            error=str(e),
        )
