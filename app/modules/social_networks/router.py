"""
AZALS MODULE - Réseaux Sociaux - Router API
===========================================

Endpoints pour l'administration des métriques marketing.
Accessible via: Administration > Réseaux Sociaux
"""

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
from .service import SocialNetworksService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/social-networks", tags=["Administration - Réseaux Sociaux"])


# === Dépendance pour le service ===

def get_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> SocialNetworksService:
    return SocialNetworksService(db, tenant_id)


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
