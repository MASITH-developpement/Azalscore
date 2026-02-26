"""
Router API - Module Integrations (GAP-086)

Endpoints REST pour la gestion des intégrations.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .models import ConnectionStatus, SyncStatus, ConnectorType, SyncDirection
from .schemas import (
    ConnectionCreate, ConnectionUpdate, ConnectionResponse,
    ConnectionList, ConnectionListItem,
    EntityMappingCreate, EntityMappingUpdate, EntityMappingResponse,
    SyncJobCreate, SyncJobResponse, SyncJobList, SyncJobListItem,
    SyncLogResponse, SyncLogList,
    ConflictResolveRequest, ConflictResponse, ConflictList,
    WebhookCreate, WebhookResponse,
    ConnectionHealthResponse, IntegrationStatsResponse,
    ConnectorDefinitionResponse,
    ConnectionFilters, SyncJobFilters,
    AutocompleteResponse, AutocompleteItem
)
from .repository import (
    ConnectionRepository, EntityMappingRepository, SyncJobRepository,
    SyncLogRepository, ConflictRepository, WebhookRepository
)
from .service import CONNECTOR_DEFINITIONS
from .exceptions import (
    ConnectionNotFoundError, ConnectionDuplicateError,
    EntityMappingNotFoundError, SyncJobNotFoundError, SyncJobRunningError,
    ConflictNotFoundError
)

router = APIRouter(prefix="/integrations", tags=["Integrations"])


# ============== Connector Definitions ==============

@router.get("/connectors", response_model=List[ConnectorDefinitionResponse])
async def list_connectors(
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.connector.read")
):
    """Lister les connecteurs disponibles."""
    return [
        ConnectorDefinitionResponse(
            connector_type=d.connector_type.value,
            name=d.name,
            description=d.description,
            auth_type=d.auth_type.value,
            base_url=d.base_url,
            supported_entities=[e.value for e in d.supported_entities],
            supported_directions=[s.value for s in d.supported_directions],
            required_fields=d.required_fields,
            optional_fields=d.optional_fields,
            oauth_authorize_url=d.oauth_authorize_url,
            rate_limit_per_minute=d.rate_limit_per_minute,
            icon_url=d.icon_url,
            documentation_url=d.documentation_url
        )
        for d in CONNECTOR_DEFINITIONS.values()
    ]


@router.get("/connectors/{connector_type}", response_model=ConnectorDefinitionResponse)
async def get_connector(
    connector_type: str,
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.connector.read")
):
    """Obtenir un connecteur."""
    from .service import ConnectorType as CT
    try:
        ct = CT(connector_type)
    except ValueError:
        raise HTTPException(status_code=404, detail="Connecteur non trouvé")

    definition = CONNECTOR_DEFINITIONS.get(ct)
    if not definition:
        raise HTTPException(status_code=404, detail="Connecteur non trouvé")

    return ConnectorDefinitionResponse(
        connector_type=definition.connector_type.value,
        name=definition.name,
        description=definition.description,
        auth_type=definition.auth_type.value,
        base_url=definition.base_url,
        supported_entities=[e.value for e in definition.supported_entities],
        supported_directions=[s.value for s in definition.supported_directions],
        required_fields=definition.required_fields,
        optional_fields=definition.optional_fields,
        oauth_authorize_url=definition.oauth_authorize_url,
        rate_limit_per_minute=definition.rate_limit_per_minute,
        icon_url=definition.icon_url,
        documentation_url=definition.documentation_url
    )


# ============== Connections ==============

@router.get("/connections", response_model=ConnectionList)
async def list_connections(
    search: Optional[str] = Query(None, min_length=2),
    connector_type: Optional[List[ConnectorType]] = Query(None),
    status: Optional[List[ConnectionStatus]] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.connection.read")
):
    """Lister les connexions."""
    filters = ConnectionFilters(
        search=search, connector_type=connector_type, status=status, is_active=is_active
    )
    repo = ConnectionRepository(db, current_user.tenant_id)
    items, total = repo.list(filters, page, page_size, sort_by, sort_dir)

    return ConnectionList(
        items=[ConnectionListItem(
            id=c.id,
            code=c.code,
            name=c.name,
            connector_type=c.connector_type,
            status=c.status,
            is_active=c.is_active,
            last_connected_at=c.last_connected_at
        ) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/connections/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_connections(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.connection.read")
):
    """Autocomplete connexions."""
    repo = ConnectionRepository(db, current_user.tenant_id)
    results = repo.autocomplete(q, limit)
    return AutocompleteResponse(items=[AutocompleteItem(**r) for r in results])


@router.get("/connections/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.connection.read")
):
    """Obtenir une connexion."""
    repo = ConnectionRepository(db, current_user.tenant_id)
    connection = repo.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connexion non trouvée")
    return connection


@router.post("/connections", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    data: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.connection.create")
):
    """Créer une connexion."""
    repo = ConnectionRepository(db, current_user.tenant_id)

    if data.code and repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail="Code connexion déjà existant")

    connection = repo.create(data.model_dump(), current_user.id)
    return connection


@router.put("/connections/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: UUID,
    data: ConnectionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.connection.update")
):
    """Mettre à jour une connexion."""
    repo = ConnectionRepository(db, current_user.tenant_id)
    connection = repo.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connexion non trouvée")

    connection = repo.update(connection, data.model_dump(exclude_unset=True), current_user.id)
    return connection


@router.post("/connections/{connection_id}/test", response_model=ConnectionHealthResponse)
async def test_connection(
    connection_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.connection.update")
):
    """Tester une connexion."""
    repo = ConnectionRepository(db, current_user.tenant_id)
    connection = repo.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connexion non trouvée")

    # Simulation de test (en production: appel API réel)
    import random
    is_healthy = random.random() > 0.1  # 90% de succès simulé
    response_time = random.randint(50, 500)

    if is_healthy:
        repo.update_status(connection, ConnectionStatus.CONNECTED)
    else:
        repo.update_status(connection, ConnectionStatus.ERROR, "Test connection failed")

    return ConnectionHealthResponse(
        connection_id=connection.id,
        is_healthy=is_healthy,
        last_check_at=datetime.utcnow(),
        response_time_ms=response_time,
        success_rate_24h=95.0 if is_healthy else 80.0,
        total_requests_24h=100,
        last_error=None if is_healthy else "Test connection failed",
        consecutive_errors=0 if is_healthy else 1
    )


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.connection.delete")
):
    """Supprimer une connexion (soft delete)."""
    repo = ConnectionRepository(db, current_user.tenant_id)
    connection = repo.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connexion non trouvée")

    repo.soft_delete(connection, current_user.id)


# ============== Entity Mappings ==============

@router.get("/connections/{connection_id}/mappings", response_model=List[EntityMappingResponse])
async def list_entity_mappings(
    connection_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.mapping.read")
):
    """Lister les mappings d'une connexion."""
    conn_repo = ConnectionRepository(db, current_user.tenant_id)
    if not conn_repo.exists(connection_id):
        raise HTTPException(status_code=404, detail="Connexion non trouvée")

    repo = EntityMappingRepository(db, current_user.tenant_id)
    return repo.get_by_connection(connection_id)


@router.get("/mappings/{mapping_id}", response_model=EntityMappingResponse)
async def get_entity_mapping(
    mapping_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.mapping.read")
):
    """Obtenir un mapping."""
    repo = EntityMappingRepository(db, current_user.tenant_id)
    mapping = repo.get_by_id(mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouvé")
    return mapping


@router.post("/mappings", response_model=EntityMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_entity_mapping(
    data: EntityMappingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.mapping.create")
):
    """Créer un mapping."""
    conn_repo = ConnectionRepository(db, current_user.tenant_id)
    if not conn_repo.exists(data.connection_id):
        raise HTTPException(status_code=404, detail="Connexion non trouvée")

    repo = EntityMappingRepository(db, current_user.tenant_id)
    if data.code and repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail="Code mapping déjà existant")

    mapping = repo.create(data.model_dump(), current_user.id)
    return mapping


@router.put("/mappings/{mapping_id}", response_model=EntityMappingResponse)
async def update_entity_mapping(
    mapping_id: UUID,
    data: EntityMappingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.mapping.update")
):
    """Mettre à jour un mapping."""
    repo = EntityMappingRepository(db, current_user.tenant_id)
    mapping = repo.get_by_id(mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouvé")

    mapping = repo.update(mapping, data.model_dump(exclude_unset=True), current_user.id)
    return mapping


# ============== Sync Jobs ==============

@router.get("/sync-jobs", response_model=SyncJobList)
async def list_sync_jobs(
    connection_id: Optional[UUID] = Query(None),
    status: Optional[List[SyncStatus]] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.sync.read")
):
    """Lister les jobs de synchronisation."""
    filters = SyncJobFilters(connection_id=connection_id, status=status)
    repo = SyncJobRepository(db, current_user.tenant_id)
    items, total = repo.list(filters, page, page_size)

    return SyncJobList(
        items=[SyncJobListItem(
            id=j.id,
            connection_id=j.connection_id,
            entity_mapping_id=j.entity_mapping_id,
            direction=j.direction,
            status=j.status,
            total_records=j.total_records,
            processed_records=j.processed_records,
            failed_records=j.failed_records,
            started_at=j.started_at,
            completed_at=j.completed_at
        ) for j in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/sync-jobs/{job_id}", response_model=SyncJobResponse)
async def get_sync_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.sync.read")
):
    """Obtenir un job de synchronisation."""
    repo = SyncJobRepository(db, current_user.tenant_id)
    job = repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    return job


@router.post("/sync-jobs", response_model=SyncJobResponse, status_code=status.HTTP_201_CREATED)
async def create_sync_job(
    data: SyncJobCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.sync.create")
):
    """Créer et démarrer un job de synchronisation."""
    conn_repo = ConnectionRepository(db, current_user.tenant_id)
    connection = conn_repo.get_by_id(data.connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connexion non trouvée")

    if connection.status != ConnectionStatus.CONNECTED.value:
        raise HTTPException(status_code=400, detail="Connexion non active")

    mapping_repo = EntityMappingRepository(db, current_user.tenant_id)
    mapping = mapping_repo.get_by_id(data.entity_mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouvé")

    job_repo = SyncJobRepository(db, current_user.tenant_id)

    # Vérifier qu'il n'y a pas de job en cours
    running = job_repo.get_running_for_connection(data.connection_id)
    if running:
        raise HTTPException(status_code=409, detail="Un job est déjà en cours pour cette connexion")

    job = job_repo.create(data.model_dump(), current_user.id)
    return job


@router.post("/sync-jobs/{job_id}/start", response_model=SyncJobResponse)
async def start_sync_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.sync.execute")
):
    """Démarrer un job de synchronisation."""
    repo = SyncJobRepository(db, current_user.tenant_id)
    job = repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")

    if job.status == SyncStatus.RUNNING.value:
        raise HTTPException(status_code=409, detail="Job déjà en cours")

    job = repo.start(job)
    return job


@router.post("/sync-jobs/{job_id}/cancel", response_model=SyncJobResponse)
async def cancel_sync_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.sync.execute")
):
    """Annuler un job de synchronisation."""
    repo = SyncJobRepository(db, current_user.tenant_id)
    job = repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")

    job = repo.cancel(job)
    return job


@router.get("/sync-jobs/{job_id}/logs", response_model=SyncLogList)
async def get_sync_logs(
    job_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.sync.read")
):
    """Obtenir les logs d'un job."""
    job_repo = SyncJobRepository(db, current_user.tenant_id)
    if not job_repo.get_by_id(job_id):
        raise HTTPException(status_code=404, detail="Job non trouvé")

    repo = SyncLogRepository(db, current_user.tenant_id)
    items, total = repo.get_by_job(job_id, limit, offset)

    return SyncLogList(items=items, total=total)


# ============== Conflicts ==============

@router.get("/conflicts", response_model=ConflictList)
async def list_conflicts(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.conflict.read")
):
    """Lister les conflits en attente."""
    repo = ConflictRepository(db, current_user.tenant_id)
    items = repo.get_pending(limit)
    total = repo.get_pending_count()

    return ConflictList(items=items, total=total)


@router.get("/conflicts/{conflict_id}", response_model=ConflictResponse)
async def get_conflict(
    conflict_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.conflict.read")
):
    """Obtenir un conflit."""
    repo = ConflictRepository(db, current_user.tenant_id)
    conflict = repo.get_by_id(conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflit non trouvé")
    return conflict


@router.post("/conflicts/{conflict_id}/resolve", response_model=ConflictResponse)
async def resolve_conflict(
    conflict_id: UUID,
    data: ConflictResolveRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.conflict.resolve")
):
    """Résoudre un conflit."""
    repo = ConflictRepository(db, current_user.tenant_id)
    conflict = repo.get_by_id(conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflit non trouvé")

    if conflict.resolved_at:
        raise HTTPException(status_code=400, detail="Conflit déjà résolu")

    conflict = repo.resolve(
        conflict,
        data.resolution.value,
        data.resolved_data or {},
        current_user.id
    )
    return conflict


# ============== Webhooks ==============

@router.get("/connections/{connection_id}/webhooks", response_model=List[WebhookResponse])
async def list_webhooks(
    connection_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.webhook.read")
):
    """Lister les webhooks d'une connexion."""
    conn_repo = ConnectionRepository(db, current_user.tenant_id)
    if not conn_repo.exists(connection_id):
        raise HTTPException(status_code=404, detail="Connexion non trouvée")

    repo = WebhookRepository(db, current_user.tenant_id)
    return repo.get_by_connection(connection_id)


@router.post("/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: WebhookCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.webhook.create")
):
    """Créer un webhook."""
    conn_repo = ConnectionRepository(db, current_user.tenant_id)
    if not conn_repo.exists(data.connection_id):
        raise HTTPException(status_code=404, detail="Connexion non trouvée")

    repo = WebhookRepository(db, current_user.tenant_id)

    # Vérifier unicité du path
    existing = repo.get_by_path(data.endpoint_path)
    if existing:
        raise HTTPException(status_code=409, detail="Chemin webhook déjà utilisé")

    # Générer secret
    import secrets
    webhook_data = data.model_dump()
    webhook_data["secret_key"] = secrets.token_urlsafe(32)

    webhook = repo.create(webhook_data, current_user.id)
    return webhook


# ============== Stats ==============

@router.get("/stats", response_model=IntegrationStatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integrations.stats.read")
):
    """Obtenir les statistiques d'intégration."""
    conn_repo = ConnectionRepository(db, current_user.tenant_id)
    connections, total_connections = conn_repo.list(page_size=1000)

    job_repo = SyncJobRepository(db, current_user.tenant_id)
    jobs, total_jobs = job_repo.list(page_size=1000)

    conflict_repo = ConflictRepository(db, current_user.tenant_id)
    pending_conflicts = conflict_repo.get_pending_count()

    # Compter par type
    by_type = {}
    for c in connections:
        by_type[c.connector_type] = by_type.get(c.connector_type, 0) + 1

    # Stats dernières 24h
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_jobs = [j for j in jobs if j.created_at and j.created_at > yesterday]

    return IntegrationStatsResponse(
        tenant_id=current_user.tenant_id,
        total_connections=total_connections,
        active_connections=len([c for c in connections if c.is_active and c.status == ConnectionStatus.CONNECTED.value]),
        total_sync_jobs=total_jobs,
        pending_conflicts=pending_conflicts,
        syncs_last_24h=len(recent_jobs),
        records_synced_last_24h=sum(j.processed_records or 0 for j in recent_jobs),
        failed_syncs_last_24h=len([j for j in recent_jobs if j.status == SyncStatus.FAILED.value]),
        by_connector_type=by_type
    )
