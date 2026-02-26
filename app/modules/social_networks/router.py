"""
AZALS MODULE - Réseaux Sociaux - Router API
===========================================

Endpoints pour l'administration des métriques marketing.
Accessible via: Administration > Réseaux Sociaux
"""
from __future__ import annotations


import logging
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_tenant_id

from .models import MarketingPlatform, SocialNetworkMetrics
from .schemas import (
    GoogleAnalyticsInput, GoogleAdsInput, GoogleSearchConsoleInput,
    GoogleMyBusinessInput, MetaBusinessInput, LinkedInInput, SolocalInput,
    SocialMetricsResponse, SocialMetricsUpdate, MarketingSummary
)
from .config_schemas import (
    PlatformConfigCreate, PlatformConfigUpdate, PlatformConfigResponse,
    OAuthInitRequest, OAuthInitResponse, OAuthCallbackRequest, OAuthCallbackResponse,
    SyncRequest, SyncResponse, PlatformStatus, AllPlatformsStatus
)
from .service import SocialNetworksService
from .config_service import ConfigService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/social-networks", tags=["Administration - Réseaux Sociaux"])


# === Dépendances pour les services ===

def get_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> SocialNetworksService:
    return SocialNetworksService(db, tenant_id)


def get_config_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> ConfigService:
    return ConfigService(db, tenant_id)


# === Endpoints de consultation ===

@router.get("/metrics", response_model=List[SocialMetricsResponse])
async def list_metrics(
    platform: Optional[MarketingPlatform] = Query(None, description="Filtrer par plateforme"),
    start_date: Optional[date] = Query(None, description="Date de début"),
    end_date: Optional[date] = Query(None, description="Date de fin"),
    limit: int = Query(100, le=500),
    service: SocialNetworksService = Depends(get_service)
):
    """
    Liste les métriques des réseaux sociaux.
    Filtres optionnels par plateforme et période.
    """
    return service.get_metrics(platform, start_date, end_date, limit)


@router.get("/metrics/{metrics_id}", response_model=SocialMetricsResponse)
async def get_metrics(
    metrics_id: UUID,
    service: SocialNetworksService = Depends(get_service)
):
    """Récupère une entrée de métriques par son ID."""
    metrics = service.get_metrics_by_id(metrics_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Métriques non trouvées")
    return metrics


@router.get("/summary", response_model=MarketingSummary)
async def get_summary(
    metrics_date: Optional[date] = Query(None, description="Date (défaut: aujourd'hui)"),
    service: SocialNetworksService = Depends(get_service)
):
    """
    Récapitulatif marketing toutes plateformes confondues.
    Retourne les totaux et détails par plateforme.
    """
    return service.get_summary(metrics_date)


@router.get("/platforms")
async def list_platforms():
    """Liste des plateformes marketing supportées."""
    return {
        "platforms": [
            {"id": p.value, "name": p.name.replace("_", " ").title()}
            for p in MarketingPlatform
        ]
    }


# === Endpoints de saisie par plateforme ===

@router.post("/google-analytics", response_model=SocialMetricsResponse)
async def save_google_analytics(
    data: GoogleAnalyticsInput,
    service: SocialNetworksService = Depends(get_service)
):
    """
    Enregistre les métriques Google Analytics.

    Métriques : sessions, utilisateurs, pages vues, taux de rebond,
    durée moyenne de session, conversions.
    """
    metrics = service.save_google_analytics(data)
    service.sync_to_prometheus(data.metrics_date)
    return metrics


@router.post("/google-ads", response_model=SocialMetricsResponse)
async def save_google_ads(
    data: GoogleAdsInput,
    service: SocialNetworksService = Depends(get_service)
):
    """
    Enregistre les métriques Google Ads.

    Métriques : impressions, clics, coût, conversions, CTR, CPC, ROAS.
    """
    metrics = service.save_google_ads(data)
    service.sync_to_prometheus(data.metrics_date)
    return metrics


@router.post("/google-search-console", response_model=SocialMetricsResponse)
async def save_google_search_console(
    data: GoogleSearchConsoleInput,
    service: SocialNetworksService = Depends(get_service)
):
    """
    Enregistre les métriques Google Search Console.

    Métriques : impressions, clics, CTR, position moyenne.
    """
    metrics = service.save_google_search_console(data)
    service.sync_to_prometheus(data.metrics_date)
    return metrics


@router.post("/google-my-business", response_model=SocialMetricsResponse)
async def save_google_my_business(
    data: GoogleMyBusinessInput,
    service: SocialNetworksService = Depends(get_service)
):
    """
    Enregistre les métriques Google My Business.

    Métriques : vues, clics, appels, itinéraires, avis, note.
    """
    metrics = service.save_google_my_business(data)
    service.sync_to_prometheus(data.metrics_date)
    return metrics


@router.post("/meta", response_model=SocialMetricsResponse)
async def save_meta_business(
    data: MetaBusinessInput,
    service: SocialNetworksService = Depends(get_service)
):
    """
    Enregistre les métriques Meta Business (Facebook ou Instagram).

    Spécifiez platform=meta_facebook ou platform=meta_instagram.
    Métriques : portée, impressions, engagement, clics, abonnés, budget pub.
    """
    metrics = service.save_meta_business(data)
    service.sync_to_prometheus(data.metrics_date)
    return metrics


@router.post("/linkedin", response_model=SocialMetricsResponse)
async def save_linkedin(
    data: LinkedInInput,
    service: SocialNetworksService = Depends(get_service)
):
    """
    Enregistre les métriques LinkedIn.

    Métriques : abonnés, impressions, clics, engagement, visiteurs.
    """
    metrics = service.save_linkedin(data)
    service.sync_to_prometheus(data.metrics_date)
    return metrics


@router.post("/solocal", response_model=SocialMetricsResponse)
async def save_solocal(
    data: SolocalInput,
    service: SocialNetworksService = Depends(get_service)
):
    """
    Enregistre les métriques Solocal (PagesJaunes).

    Métriques : vues fiche, clics, appels, itinéraires, avis, note.
    """
    metrics = service.save_solocal(data)
    service.sync_to_prometheus(data.metrics_date)
    return metrics


# === Endpoints de modification/suppression ===

@router.put("/metrics/{metrics_id}", response_model=SocialMetricsResponse)
async def update_metrics(
    metrics_id: UUID,
    data: SocialMetricsUpdate,
    service: SocialNetworksService = Depends(get_service)
):
    """Met à jour des métriques existantes."""
    metrics = service.update_metrics(metrics_id, data)
    if not metrics:
        raise HTTPException(status_code=404, detail="Métriques non trouvées")

    service.sync_to_prometheus(metrics.metrics_date)
    return metrics


@router.delete("/metrics/{metrics_id}")
async def delete_metrics(
    metrics_id: UUID,
    service: SocialNetworksService = Depends(get_service)
):
    """Supprime une entrée de métriques."""
    deleted = service.delete_metrics(metrics_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Métriques non trouvées")
    return {"status": "deleted", "id": str(metrics_id)}


# === Synchronisation Prometheus ===

@router.post("/sync-prometheus")
async def sync_prometheus(
    metrics_date: Optional[date] = Query(None, description="Date à synchroniser"),
    service: SocialNetworksService = Depends(get_service)
):
    """
    Synchronise les métriques de la base de données vers Prometheus/Grafana.
    Utile après une mise à jour manuelle ou pour forcer le rafraîchissement.
    """
    service.sync_to_prometheus(metrics_date)
    return {
        "status": "ok",
        "message": f"Métriques synchronisées pour {metrics_date or date.today()}"
    }


# ============================================================
# CONFIGURATION DES PLATEFORMES
# ============================================================

@router.get("/config/status", response_model=AllPlatformsStatus)
async def get_all_platforms_status(
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Récupère le statut de toutes les plateformes marketing.
    Indique si elles sont configurées, connectées, et leur dernier état de sync.
    """
    return config_service.get_all_platforms_status()


@router.get("/config/{platform}", response_model=PlatformStatus)
async def get_platform_config(
    platform: MarketingPlatform,
    config_service: ConfigService = Depends(get_config_service)
):
    """Récupère le statut et la configuration d'une plateforme."""
    return config_service.get_platform_status(platform)


@router.post("/config/{platform}", response_model=PlatformStatus)
async def save_platform_config(
    platform: MarketingPlatform,
    data: PlatformConfigCreate,
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Crée ou met à jour la configuration d'une plateforme.

    Pour les plateformes avec clé API simple (Solocal), fournir api_key.
    Pour les plateformes OAuth (Google, Meta, LinkedIn), utiliser /config/oauth/init.
    """
    config_service.create_or_update_config(platform, data)
    return config_service.get_platform_status(platform)


@router.put("/config/{platform}", response_model=PlatformStatus)
async def update_platform_config(
    platform: MarketingPlatform,
    data: PlatformConfigUpdate,
    config_service: ConfigService = Depends(get_config_service)
):
    """Met à jour la configuration d'une plateforme existante."""
    config = config_service.get_config(platform)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")

    config_service.create_or_update_config(platform, data)
    return config_service.get_platform_status(platform)


@router.delete("/config/{platform}")
async def delete_platform_config(
    platform: MarketingPlatform,
    config_service: ConfigService = Depends(get_config_service)
):
    """Supprime la configuration d'une plateforme."""
    deleted = config_service.delete_config(platform)
    if not deleted:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return {"status": "deleted", "platform": platform.value}


# === OAuth ===

@router.post("/config/oauth/init", response_model=OAuthInitResponse)
async def init_oauth(
    request: OAuthInitRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Initialise le flux OAuth pour une plateforme.
    Retourne l'URL d'autorisation où rediriger l'utilisateur.
    """
    try:
        result = config_service.init_oauth(request.platform, request.redirect_uri)
        return OAuthInitResponse(
            auth_url=result["auth_url"],
            state=result["state"],
            platform=request.platform
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/config/oauth/callback", response_model=OAuthCallbackResponse)
async def oauth_callback(
    request: OAuthCallbackRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Traite le callback OAuth après autorisation de l'utilisateur.
    Échange le code contre des tokens d'accès.
    """
    return await config_service.handle_oauth_callback(
        request.platform,
        request.code,
        request.state
    )


# === Synchronisation automatique ===

@router.post("/sync", response_model=SyncResponse)
async def sync_platform_metrics(
    request: SyncRequest,
    config_service: ConfigService = Depends(get_config_service),
    service: SocialNetworksService = Depends(get_service)
):
    """
    Synchronise les métriques depuis les APIs des plateformes.

    Si platform est spécifié, synchronise uniquement cette plateforme.
    Sinon, synchronise toutes les plateformes configurées.
    """
    date_from = date.fromisoformat(request.date_from) if request.date_from else None
    date_to = date.fromisoformat(request.date_to) if request.date_to else None

    if request.platform:
        # Sync une seule plateforme
        result = await config_service.sync_platform(request.platform, date_from, date_to)

        # Sync vers Prometheus après
        if result["success"]:
            service.sync_to_prometheus(date_to or date.today())

        return SyncResponse(
            success=result["success"],
            platform=request.platform,
            message="Synchronisation terminée" if result["success"] else result.get("error", "Erreur"),
            records_synced=result.get("records", 0),
            errors=[result["error"]] if not result["success"] else []
        )
    else:
        # Sync toutes les plateformes
        results = await config_service.sync_all_platforms(date_from, date_to)

        # Sync vers Prometheus après
        if results["total_records"] > 0:
            service.sync_to_prometheus(date_to or date.today())

        return SyncResponse(
            success=results["platforms_failed"] == 0,
            message=f"{results['platforms_synced']} plateforme(s) synchronisée(s)",
            records_synced=results["total_records"],
            errors=results["errors"]
        )


@router.post("/sync/{platform}", response_model=SyncResponse)
async def sync_single_platform(
    platform: MarketingPlatform,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    config_service: ConfigService = Depends(get_config_service),
    service: SocialNetworksService = Depends(get_service)
):
    """Synchronise les métriques d'une plateforme spécifique."""
    result = await config_service.sync_platform(platform, date_from, date_to)

    if result["success"]:
        service.sync_to_prometheus(date_to or date.today())

    return SyncResponse(
        success=result["success"],
        platform=platform,
        message="Synchronisation terminée" if result["success"] else result.get("error", "Erreur"),
        records_synced=result.get("records", 0),
        errors=[result["error"]] if not result["success"] else []
    )


@router.post("/test-connection/{platform}")
async def test_platform_connection(
    platform: MarketingPlatform,
    config_service: ConfigService = Depends(get_config_service)
):
    """Teste la connexion à une plateforme."""
    from .api_clients import (
        GoogleAnalyticsClient, GoogleAdsClient, GoogleSearchConsoleClient,
        GoogleMyBusinessClient, MetaBusinessClient, LinkedInClient, SolocalClient
    )

    config = config_service.get_config(platform)
    if not config:
        raise HTTPException(status_code=404, detail="Plateforme non configurée")

    # Mapping plateforme -> client
    client_map = {
        MarketingPlatform.GOOGLE_ANALYTICS: GoogleAnalyticsClient,
        MarketingPlatform.GOOGLE_ADS: GoogleAdsClient,
        MarketingPlatform.GOOGLE_SEARCH_CONSOLE: GoogleSearchConsoleClient,
        MarketingPlatform.GOOGLE_MY_BUSINESS: GoogleMyBusinessClient,
        MarketingPlatform.META_FACEBOOK: MetaBusinessClient,
        MarketingPlatform.META_INSTAGRAM: MetaBusinessClient,
        MarketingPlatform.LINKEDIN: LinkedInClient,
        MarketingPlatform.SOLOCAL: SolocalClient,
    }

    client_class = client_map.get(platform)
    if not client_class:
        raise HTTPException(status_code=400, detail="Plateforme non supportée pour les tests")

    async with client_class(
        access_token=config.access_token,
        refresh_token=config.refresh_token,
        api_key=config.api_key,
        api_secret=config.api_secret,
        account_id=config.account_id,
        property_id=config.property_id,
    ) as client:
        connected = await client.test_connection()

        if connected:
            try:
                account_info = await client.get_account_info()
                return {
                    "status": "connected",
                    "platform": platform.value,
                    "account_info": account_info
                }
            except Exception:
                return {"status": "connected", "platform": platform.value}
        else:
            return {"status": "disconnected", "platform": platform.value}
