"""
AZALS MODULE - Cache - Router
=============================

Endpoints API pour la gestion du cache applicatif.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.dependencies import get_tenant_id
from app.core.models import User

from .exceptions import (
    CacheAlertAlreadyResolvedError,
    CacheAlertNotFoundError,
    CacheConfigAlreadyExistsError,
    CacheConfigNotFoundError,
    CacheRegionDuplicateError,
    CacheRegionNotFoundError,
    PreloadTaskNotFoundError,
)
from .models import AlertStatus, CacheLevel, InvalidationType
from .schemas import (
    AlertAcknowledgeRequest,
    AlertResolveRequest,
    CacheAlertResponse,
    CacheAuditLogResponse,
    CacheConfigCreate,
    CacheConfigResponse,
    CacheConfigUpdate,
    CacheDashboard,
    CacheEntryList,
    CacheEntryResponse,
    CacheGetResponse,
    CacheMGetResponse,
    CacheMSetRequest,
    CacheRegionCreate,
    CacheRegionResponse,
    CacheRegionUpdate,
    CacheSetRequest,
    CacheStatsAggregated,
    InvalidateByEntityRequest,
    InvalidateByKeyRequest,
    InvalidateByPatternRequest,
    InvalidateByTagRequest,
    InvalidationResponse,
    PreloadRunResponse,
    PreloadTaskCreate,
    PreloadTaskResponse,
    PreloadTaskUpdate,
    PurgeRequest,
    PurgeResponse,
)
from .service import get_cache_service

router = APIRouter(prefix="/cache", tags=["Cache Applicatif"])


def get_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    return get_cache_service(db, tenant_id)


# ============================================================================
# CONFIGURATION
# ============================================================================

@router.post("/config", response_model=CacheConfigResponse, status_code=201)
def create_config(
    data: CacheConfigCreate,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Creer la configuration cache du tenant."""
    try:
        config = service.create_config(data, user_id=current_user.id)
        return config
    except CacheConfigAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/config", response_model=CacheConfigResponse)
def get_config(
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Recuperer la configuration cache."""
    config = service.get_config()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration cache non trouvee")
    return config


@router.patch("/config", response_model=CacheConfigResponse)
def update_config(
    data: CacheConfigUpdate,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour la configuration cache."""
    try:
        config = service.update_config(data, user_id=current_user.id)
        return config
    except CacheConfigNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# REGIONS
# ============================================================================

@router.get("/regions", response_model=List[CacheRegionResponse])
def list_regions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Lister les regions cache."""
    items, _ = service.list_regions(skip, limit)
    return items


@router.post("/regions", response_model=CacheRegionResponse, status_code=201)
def create_region(
    data: CacheRegionCreate,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Creer une region cache."""
    try:
        region = service.create_region(data, user_id=current_user.id)
        return region
    except CacheConfigNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CacheRegionDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/regions/{region_id}", response_model=CacheRegionResponse)
def get_region(
    region_id: UUID,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Recuperer une region cache."""
    region = service.get_region(region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region non trouvee")
    return region


@router.patch("/regions/{region_id}", response_model=CacheRegionResponse)
def update_region(
    region_id: UUID,
    data: CacheRegionUpdate,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour une region cache."""
    try:
        region = service.update_region(region_id, data, user_id=current_user.id)
        return region
    except CacheRegionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/regions/{region_id}", status_code=204)
def delete_region(
    region_id: UUID,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Supprimer une region cache."""
    try:
        service.delete_region(region_id, user_id=current_user.id)
    except CacheRegionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# OPERATIONS CACHE
# ============================================================================

@router.get("/entries/{key:path}", response_model=CacheGetResponse)
def get_cache_entry(
    key: str,
    region: Optional[str] = None,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Recuperer une valeur du cache."""
    return service.get(key, region=region)


@router.post("/entries", response_model=dict)
def set_cache_entry(
    data: CacheSetRequest,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Stocker une valeur dans le cache."""
    success = service.set(
        key=data.key,
        value=data.value,
        ttl_seconds=data.ttl_seconds,
        tags=data.tags,
        region=data.region,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
    )
    return {"success": success, "key": data.key}


@router.delete("/entries/{key:path}", status_code=204)
def delete_cache_entry(
    key: str,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Supprimer une entree du cache."""
    service.delete(key)


@router.head("/entries/{key:path}")
def check_cache_entry(
    key: str,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Verifier si une cle existe."""
    if not service.exists(key):
        raise HTTPException(status_code=404, detail="Cle non trouvee")
    return {}


@router.post("/entries/mget", response_model=CacheMGetResponse)
def mget_cache_entries(
    keys: List[str],
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Recuperer plusieurs valeurs du cache."""
    return service.mget(keys)


@router.post("/entries/mset", response_model=dict)
def mset_cache_entries(
    data: CacheMSetRequest,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Stocker plusieurs valeurs dans le cache."""
    count = service.mset(
        items=data.items,
        ttl_seconds=data.ttl_seconds,
        tags=data.tags,
        region=data.region,
    )
    return {"success": True, "count": count}


# ============================================================================
# INVALIDATION
# ============================================================================

@router.post("/invalidate/key", response_model=InvalidationResponse)
def invalidate_by_key(
    data: InvalidateByKeyRequest,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Invalider par cle."""
    return service.invalidate_by_key(data.key, user_id=current_user.id)


@router.post("/invalidate/pattern", response_model=InvalidationResponse)
def invalidate_by_pattern(
    data: InvalidateByPatternRequest,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Invalider par pattern (wildcards: * ?)."""
    return service.invalidate_by_pattern(data.pattern, user_id=current_user.id)


@router.post("/invalidate/tag", response_model=InvalidationResponse)
def invalidate_by_tag(
    data: InvalidateByTagRequest,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Invalider par tag."""
    return service.invalidate_by_tag(data.tag, user_id=current_user.id)


@router.post("/invalidate/entity", response_model=InvalidationResponse)
def invalidate_by_entity(
    data: InvalidateByEntityRequest,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Invalider par entite."""
    return service.invalidate_by_entity(
        data.entity_type,
        data.entity_id,
        user_id=current_user.id
    )


@router.post("/invalidate/all", response_model=InvalidationResponse)
def invalidate_all(
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Invalider tout le cache du tenant."""
    return service.invalidate_all(user_id=current_user.id)


# ============================================================================
# PURGE
# ============================================================================

@router.post("/purge", response_model=PurgeResponse)
def purge_cache(
    data: PurgeRequest,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Purger le cache (supprime les entrees)."""
    return service.purge(
        level=data.level,
        region_code=data.region_code,
        expired_only=data.expired_only,
        user_id=current_user.id
    )


# ============================================================================
# STATISTIQUES
# ============================================================================

@router.get("/stats", response_model=CacheStatsAggregated)
def get_stats(
    level: Optional[CacheLevel] = None,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Recuperer les statistiques du cache."""
    return service.get_stats(level)


# ============================================================================
# PRECHARGEMENT
# ============================================================================

@router.get("/preload", response_model=List[PreloadTaskResponse])
def list_preload_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Lister les taches de prechargement."""
    items, _ = service.list_preload_tasks(skip, limit)
    return items


@router.post("/preload", response_model=PreloadTaskResponse, status_code=201)
def create_preload_task(
    data: PreloadTaskCreate,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Creer une tache de prechargement."""
    task = service.create_preload_task(data, user_id=current_user.id)
    return task


@router.post("/preload/{task_id}/run", response_model=PreloadRunResponse)
def run_preload_task(
    task_id: UUID,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Executer une tache de prechargement."""
    try:
        return service.run_preload_task(task_id, user_id=current_user.id)
    except PreloadTaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# ALERTES
# ============================================================================

@router.get("/alerts", response_model=List[CacheAlertResponse])
def list_alerts(
    status: Optional[AlertStatus] = None,
    limit: int = Query(50, ge=1, le=200),
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Lister les alertes cache."""
    return service.get_active_alerts(limit)


@router.post("/alerts/{alert_id}/acknowledge", response_model=CacheAlertResponse)
def acknowledge_alert(
    alert_id: UUID,
    data: AlertAcknowledgeRequest,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Acquitter une alerte."""
    try:
        return service.acknowledge_alert(
            alert_id,
            user_id=current_user.id,
            notes=data.notes
        )
    except CacheAlertNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/alerts/{alert_id}/resolve", response_model=CacheAlertResponse)
def resolve_alert(
    alert_id: UUID,
    data: AlertResolveRequest,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Resoudre une alerte."""
    try:
        return service.resolve_alert(
            alert_id,
            user_id=current_user.id,
            resolution_notes=data.resolution_notes
        )
    except CacheAlertNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CacheAlertAlreadyResolvedError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/check", response_model=List[CacheAlertResponse])
def check_thresholds(
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Verifier les seuils et generer des alertes."""
    alerts = service.check_thresholds()
    return alerts


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=CacheDashboard)
def get_dashboard(
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Recuperer le dashboard cache."""
    return service.get_dashboard()


# ============================================================================
# AUDIT
# ============================================================================

@router.get("/audit", response_model=List[CacheAuditLogResponse])
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Recuperer les logs d'audit cache."""
    return service.get_audit_logs(skip, limit)
