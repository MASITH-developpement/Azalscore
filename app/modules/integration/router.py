"""
AZALS MODULE GAP-086 - Router Integration
==========================================

Endpoints REST pour la gestion des integrations.
"""
from __future__ import annotations


import math
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .exceptions import (
    ConnectionDuplicateError,
    ConnectionNotFoundError,
    ConflictAlreadyResolvedError,
    ConflictNotFoundError,
    MappingDuplicateError,
    MappingNotFoundError,
    SyncConfigDuplicateError,
    SyncConfigNotFoundError,
    SyncExecutionNotFoundError,
    SyncExecutionRunningError,
    WebhookDuplicateError,
    WebhookNotFoundError,
)
from .models import (
    AuthType,
    ConflictResolution,
    ConnectionStatus,
    ConnectorType,
    EntityType,
    HealthStatus,
    SyncDirection,
    SyncMode,
    SyncStatus,
    WebhookDirection,
)
from .repository import (
    ConnectionRepository,
    DataMappingRepository,
    ExecutionLogRepository,
    SyncConfigurationRepository,
    SyncConflictRepository,
    SyncExecutionRepository,
    WebhookLogRepository,
    WebhookRepository,
)
from .schemas import (
    AutocompleteResponse,
    AutocompleteItem,
    ConflictFilters,
    ConflictResolveRequest,
    ConnectionCreate,
    ConnectionFilters,
    ConnectionHealthResponse,
    ConnectionList,
    ConnectionListItem,
    ConnectionResponse,
    ConnectionStatsResponse,
    ConnectionUpdate,
    ConnectorDefinitionList,
    ConnectorDefinitionResponse,
    DataMappingCreate,
    DataMappingList,
    DataMappingResponse,
    DataMappingUpdate,
    ExecutionLogList,
    ExecutionLogResponse,
    IntegrationStatsResponse,
    SyncConfigurationCreate,
    SyncConfigurationList,
    SyncConfigurationListItem,
    SyncConfigurationResponse,
    SyncConfigurationUpdate,
    SyncConflictList,
    SyncConflictResponse,
    SyncExecutionCreate,
    SyncExecutionFilters,
    SyncExecutionList,
    SyncExecutionListItem,
    SyncExecutionResponse,
    WebhookInboundCreate,
    WebhookList,
    WebhookLogList,
    WebhookLogResponse,
    WebhookOutboundCreate,
    WebhookResponse,
    WebhookTestRequest,
    WebhookTestResponse,
    WebhookUpdate,
)
from .service import CONNECTOR_DEFINITIONS, IntegrationService

router = APIRouter(prefix="/integration", tags=["Integration"])


# ============================================================================
# HELPERS
# ============================================================================

def get_service(db: Session, tenant_id: str) -> IntegrationService:
    """Cree une instance du service."""
    return IntegrationService(db, str(tenant_id))


# ============================================================================
# CONNECTOR DEFINITIONS
# ============================================================================

@router.get("/connectors", response_model=ConnectorDefinitionList)
async def list_connectors(
    category: str | None = Query(None),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.connector.read")
):
    """Liste les connecteurs disponibles."""
    connectors = list(CONNECTOR_DEFINITIONS.values())

    if category:
        connectors = [c for c in connectors if c.category == category]

    items = [
        ConnectorDefinitionResponse(
            id=UUID(int=0),  # ID fictif car definitions statiques
            connector_type=c.connector_type.value,
            name=c.name,
            display_name=c.display_name,
            description=c.description,
            category=c.category,
            icon_url=c.icon_url,
            logo_url=c.logo_url,
            color=c.color,
            auth_type=c.auth_type,
            base_url=c.base_url,
            api_version=c.api_version,
            oauth_authorize_url=c.oauth_authorize_url,
            oauth_token_url=c.oauth_token_url,
            oauth_scopes=c.oauth_scopes,
            oauth_pkce_required=c.oauth_pkce_required,
            required_fields=c.required_fields,
            optional_fields=c.optional_fields,
            supported_entities=[e.value for e in c.supported_entities],
            supported_directions=[d.value for d in c.supported_directions],
            rate_limit_requests=c.rate_limit_requests,
            rate_limit_daily=c.rate_limit_daily,
            supports_webhooks=c.supports_webhooks,
            webhook_events=c.webhook_events,
            documentation_url=c.documentation_url,
            setup_guide_url=c.setup_guide_url,
            is_active=True,
            is_beta=c.is_beta,
            is_premium=c.is_premium
        )
        for c in sorted(connectors, key=lambda x: x.display_name)
    ]

    return ConnectorDefinitionList(items=items, total=len(items))


@router.get("/connectors/{connector_type}", response_model=ConnectorDefinitionResponse)
async def get_connector(
    connector_type: str,
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.connector.read")
):
    """Obtenir un connecteur."""
    try:
        ct = ConnectorType(connector_type)
    except ValueError:
        raise HTTPException(status_code=404, detail="Connecteur non trouve")

    c = CONNECTOR_DEFINITIONS.get(ct)
    if not c:
        raise HTTPException(status_code=404, detail="Connecteur non trouve")

    return ConnectorDefinitionResponse(
        id=UUID(int=0),
        connector_type=c.connector_type.value,
        name=c.name,
        display_name=c.display_name,
        description=c.description,
        category=c.category,
        icon_url=c.icon_url,
        logo_url=c.logo_url,
        color=c.color,
        auth_type=c.auth_type,
        base_url=c.base_url,
        api_version=c.api_version,
        oauth_authorize_url=c.oauth_authorize_url,
        oauth_token_url=c.oauth_token_url,
        oauth_scopes=c.oauth_scopes,
        oauth_pkce_required=c.oauth_pkce_required,
        required_fields=c.required_fields,
        optional_fields=c.optional_fields,
        supported_entities=[e.value for e in c.supported_entities],
        supported_directions=[d.value for d in c.supported_directions],
        rate_limit_requests=c.rate_limit_requests,
        rate_limit_daily=c.rate_limit_daily,
        supports_webhooks=c.supports_webhooks,
        webhook_events=c.webhook_events,
        documentation_url=c.documentation_url,
        setup_guide_url=c.setup_guide_url,
        is_active=True,
        is_beta=c.is_beta,
        is_premium=c.is_premium
    )


# ============================================================================
# CONNECTIONS
# ============================================================================

@router.get("/connections", response_model=ConnectionList)
async def list_connections(
    search: str | None = Query(None, min_length=2),
    connector_type: list[ConnectorType] | None = Query(None),
    conn_status: list[ConnectionStatus] | None = Query(None, alias="status"),
    health_status: list[HealthStatus] | None = Query(None),
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.connection.read")
):
    """Liste les connexions."""
    filters = ConnectionFilters(
        search=search,
        connector_type=connector_type,
        status=conn_status,
        health_status=health_status,
        is_active=is_active
    )
    repo = ConnectionRepository(db, current_user.tenant_id)
    items, total = repo.list(filters, page, page_size, sort_by, sort_dir)

    return ConnectionList(
        items=[ConnectionListItem.model_validate(c) for c in items],
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
    _: None = require_permission("integration.connection.read")
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
    _: None = require_permission("integration.connection.read")
):
    """Obtenir une connexion."""
    repo = ConnectionRepository(db, current_user.tenant_id)
    connection = repo.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connexion non trouvee")
    return ConnectionResponse.model_validate(connection)


@router.post("/connections", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    data: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.connection.create")
):
    """Creer une connexion."""
    repo = ConnectionRepository(db, current_user.tenant_id)

    if data.code and repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail="Code connexion deja existant")

    service = get_service(db, current_user.tenant_id)
    try:
        connection = service.create_connection(data.model_dump(), current_user.id)
        return ConnectionResponse.model_validate(connection)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/connections/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: UUID,
    data: ConnectionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.connection.update")
):
    """Mettre a jour une connexion."""
    repo = ConnectionRepository(db, current_user.tenant_id)
    connection = repo.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connexion non trouvee")

    connection = repo.update(connection, data.model_dump(exclude_unset=True), current_user.id)
    return ConnectionResponse.model_validate(connection)


@router.post("/connections/{connection_id}/test", response_model=ConnectionHealthResponse)
async def test_connection(
    connection_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.connection.update")
):
    """Tester une connexion."""
    service = get_service(db, current_user.tenant_id)
    try:
        result = service.test_connection(connection_id)
        return ConnectionHealthResponse(**result)
    except ConnectionNotFoundError:
        raise HTTPException(status_code=404, detail="Connexion non trouvee")


@router.post("/connections/{connection_id}/refresh-token")
async def refresh_connection_token(
    connection_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.connection.update")
):
    """Rafraichir le token OAuth."""
    service = get_service(db, current_user.tenant_id)
    try:
        success = service.refresh_token(connection_id)
        return {"success": success}
    except ConnectionNotFoundError:
        raise HTTPException(status_code=404, detail="Connexion non trouvee")


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.connection.delete")
):
    """Supprimer une connexion (soft delete)."""
    repo = ConnectionRepository(db, current_user.tenant_id)
    connection = repo.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connexion non trouvee")

    repo.soft_delete(connection, current_user.id)


@router.get("/connections/{connection_id}/stats", response_model=ConnectionStatsResponse)
async def get_connection_stats(
    connection_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.connection.read")
):
    """Statistiques d'une connexion."""
    repo = ConnectionRepository(db, current_user.tenant_id)
    connection = repo.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connexion non trouvee")

    exec_repo = SyncExecutionRepository(db, current_user.tenant_id)
    from .schemas import SyncExecutionFilters
    filters = SyncExecutionFilters(connection_id=connection_id)
    executions, total = exec_repo.list(filters, page_size=1000)

    successful = len([e for e in executions if e.status == SyncStatus.COMPLETED])
    failed = len([e for e in executions if e.status == SyncStatus.FAILED])

    return ConnectionStatsResponse(
        connection_id=connection_id,
        total_executions=total,
        successful_executions=successful,
        failed_executions=failed,
        success_rate=(successful / total * 100) if total > 0 else 0,
        total_records_synced=sum(e.processed_records or 0 for e in executions),
        avg_execution_time_seconds=sum(e.duration_seconds or 0 for e in executions) / total if total > 0 else 0,
        last_execution_at=executions[0].started_at if executions else None,
        executions_last_24h=len([e for e in executions if e.started_at and (datetime.utcnow() - e.started_at).days < 1]),
        records_last_24h=sum(
            e.processed_records or 0
            for e in executions
            if e.started_at and (datetime.utcnow() - e.started_at).days < 1
        )
    )


# ============================================================================
# DATA MAPPINGS
# ============================================================================

@router.get("/connections/{connection_id}/mappings", response_model=DataMappingList)
async def list_mappings(
    connection_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.mapping.read")
):
    """Liste les mappings d'une connexion."""
    conn_repo = ConnectionRepository(db, current_user.tenant_id)
    if not conn_repo.exists(connection_id):
        raise HTTPException(status_code=404, detail="Connexion non trouvee")

    repo = DataMappingRepository(db, current_user.tenant_id)
    items, total = repo.list(connection_id, page, page_size)

    return DataMappingList(
        items=[DataMappingResponse.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/mappings/{mapping_id}", response_model=DataMappingResponse)
async def get_mapping(
    mapping_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.mapping.read")
):
    """Obtenir un mapping."""
    repo = DataMappingRepository(db, current_user.tenant_id)
    mapping = repo.get_by_id(mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouve")
    return DataMappingResponse.model_validate(mapping)


@router.post("/mappings", response_model=DataMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_mapping(
    data: DataMappingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.mapping.create")
):
    """Creer un mapping."""
    conn_repo = ConnectionRepository(db, current_user.tenant_id)
    if not conn_repo.exists(data.connection_id):
        raise HTTPException(status_code=404, detail="Connexion non trouvee")

    repo = DataMappingRepository(db, current_user.tenant_id)
    if data.code and repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail="Code mapping deja existant")

    # Convertir field_mappings en liste de dicts
    mapping_data = data.model_dump()
    mapping_data['field_mappings'] = [fm.model_dump() for fm in data.field_mappings]

    mapping = repo.create(mapping_data, current_user.id)
    return DataMappingResponse.model_validate(mapping)


@router.put("/mappings/{mapping_id}", response_model=DataMappingResponse)
async def update_mapping(
    mapping_id: UUID,
    data: DataMappingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.mapping.update")
):
    """Mettre a jour un mapping."""
    repo = DataMappingRepository(db, current_user.tenant_id)
    mapping = repo.get_by_id(mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouve")

    update_data = data.model_dump(exclude_unset=True)
    if 'field_mappings' in update_data and update_data['field_mappings']:
        update_data['field_mappings'] = [fm.model_dump() for fm in data.field_mappings]

    mapping = repo.update(mapping, update_data, current_user.id)
    return DataMappingResponse.model_validate(mapping)


@router.delete("/mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mapping(
    mapping_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.mapping.delete")
):
    """Supprimer un mapping."""
    repo = DataMappingRepository(db, current_user.tenant_id)
    mapping = repo.get_by_id(mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouve")

    repo.delete(mapping)


# ============================================================================
# SYNC CONFIGURATIONS
# ============================================================================

@router.get("/sync-configs", response_model=SyncConfigurationList)
async def list_sync_configs(
    connection_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.sync.read")
):
    """Liste les configurations de sync."""
    repo = SyncConfigurationRepository(db, current_user.tenant_id)
    items, total = repo.list(connection_id, page, page_size)

    return SyncConfigurationList(
        items=[SyncConfigurationListItem.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/sync-configs/{config_id}", response_model=SyncConfigurationResponse)
async def get_sync_config(
    config_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.sync.read")
):
    """Obtenir une configuration de sync."""
    repo = SyncConfigurationRepository(db, current_user.tenant_id)
    config = repo.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")
    return SyncConfigurationResponse.model_validate(config)


@router.post("/sync-configs", response_model=SyncConfigurationResponse, status_code=status.HTTP_201_CREATED)
async def create_sync_config(
    data: SyncConfigurationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.sync.create")
):
    """Creer une configuration de sync."""
    conn_repo = ConnectionRepository(db, current_user.tenant_id)
    if not conn_repo.exists(data.connection_id):
        raise HTTPException(status_code=404, detail="Connexion non trouvee")

    mapping_repo = DataMappingRepository(db, current_user.tenant_id)
    if not mapping_repo.get_by_id(data.mapping_id):
        raise HTTPException(status_code=404, detail="Mapping non trouve")

    repo = SyncConfigurationRepository(db, current_user.tenant_id)
    if data.code and repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail="Code configuration deja existant")

    config = repo.create(data.model_dump(), current_user.id)
    return SyncConfigurationResponse.model_validate(config)


@router.put("/sync-configs/{config_id}", response_model=SyncConfigurationResponse)
async def update_sync_config(
    config_id: UUID,
    data: SyncConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.sync.update")
):
    """Mettre a jour une configuration de sync."""
    repo = SyncConfigurationRepository(db, current_user.tenant_id)
    config = repo.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")

    config = repo.update(config, data.model_dump(exclude_unset=True), current_user.id)
    return SyncConfigurationResponse.model_validate(config)


@router.delete("/sync-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sync_config(
    config_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.sync.delete")
):
    """Supprimer une configuration de sync."""
    repo = SyncConfigurationRepository(db, current_user.tenant_id)
    config = repo.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")

    repo.delete(config)


# ============================================================================
# SYNC EXECUTIONS
# ============================================================================

@router.get("/executions", response_model=SyncExecutionList)
async def list_executions(
    connection_id: UUID | None = Query(None),
    config_id: UUID | None = Query(None),
    exec_status: list[SyncStatus] | None = Query(None, alias="status"),
    direction: SyncDirection | None = Query(None),
    entity_type: EntityType | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("started_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.sync.read")
):
    """Liste les executions de sync."""
    filters = SyncExecutionFilters(
        connection_id=connection_id,
        config_id=config_id,
        status=exec_status,
        direction=direction,
        entity_type=entity_type
    )
    repo = SyncExecutionRepository(db, current_user.tenant_id)
    items, total = repo.list(filters, page, page_size, sort_by, sort_dir)

    return SyncExecutionList(
        items=[SyncExecutionListItem.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/executions/{execution_id}", response_model=SyncExecutionResponse)
async def get_execution(
    execution_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.sync.read")
):
    """Obtenir une execution."""
    repo = SyncExecutionRepository(db, current_user.tenant_id)
    execution = repo.get_by_id(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution non trouvee")
    return SyncExecutionResponse.model_validate(execution)


@router.post("/executions", response_model=SyncExecutionResponse, status_code=status.HTTP_201_CREATED)
async def start_execution(
    data: SyncExecutionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.sync.execute")
):
    """Demarrer une synchronisation."""
    service = get_service(db, current_user.tenant_id)

    try:
        execution = service.start_sync(
            config_id=data.config_id,
            connection_id=data.connection_id,
            mapping_id=data.mapping_id,
            direction=data.direction,
            triggered_by="manual",
            triggered_by_user=current_user.id,
            force_full_sync=data.force_full_sync
        )
        return SyncExecutionResponse.model_validate(execution)
    except (ConnectionNotFoundError, MappingNotFoundError, SyncConfigNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SyncExecutionRunningError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/executions/{execution_id}/cancel", response_model=SyncExecutionResponse)
async def cancel_execution(
    execution_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.sync.execute")
):
    """Annuler une execution."""
    service = get_service(db, current_user.tenant_id)

    try:
        execution = service.cancel_sync(execution_id)
        return SyncExecutionResponse.model_validate(execution)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/executions/{execution_id}/retry", response_model=SyncExecutionResponse)
async def retry_execution(
    execution_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.sync.execute")
):
    """Relancer une execution echouee."""
    service = get_service(db, current_user.tenant_id)

    try:
        execution = service.retry_sync(execution_id, current_user.id)
        return SyncExecutionResponse.model_validate(execution)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/executions/{execution_id}/logs", response_model=ExecutionLogList)
async def get_execution_logs(
    execution_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.sync.read")
):
    """Obtenir les logs d'une execution."""
    exec_repo = SyncExecutionRepository(db, current_user.tenant_id)
    if not exec_repo.get_by_id(execution_id):
        raise HTTPException(status_code=404, detail="Execution non trouvee")

    repo = ExecutionLogRepository(db, current_user.tenant_id)
    items, total = repo.get_by_execution(execution_id, limit, offset)

    return ExecutionLogList(
        items=[ExecutionLogResponse.model_validate(l) for l in items],
        total=total,
        page=1,
        page_size=limit,
        pages=math.ceil(total / limit) if total > 0 else 0
    )


# ============================================================================
# CONFLICTS
# ============================================================================

@router.get("/conflicts", response_model=SyncConflictList)
async def list_conflicts(
    execution_id: UUID | None = Query(None),
    entity_type: EntityType | None = Query(None),
    is_resolved: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.conflict.read")
):
    """Liste les conflits."""
    filters = ConflictFilters(
        execution_id=execution_id,
        entity_type=entity_type,
        is_resolved=is_resolved
    )
    repo = SyncConflictRepository(db, current_user.tenant_id)
    items, total = repo.list(filters, page, page_size)

    return SyncConflictList(
        items=[SyncConflictResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/conflicts/{conflict_id}", response_model=SyncConflictResponse)
async def get_conflict(
    conflict_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.conflict.read")
):
    """Obtenir un conflit."""
    repo = SyncConflictRepository(db, current_user.tenant_id)
    conflict = repo.get_by_id(conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflit non trouve")
    return SyncConflictResponse.model_validate(conflict)


@router.post("/conflicts/{conflict_id}/resolve", response_model=SyncConflictResponse)
async def resolve_conflict(
    conflict_id: UUID,
    data: ConflictResolveRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.conflict.resolve")
):
    """Resoudre un conflit."""
    service = get_service(db, current_user.tenant_id)

    try:
        conflict = service.resolve_conflict(
            conflict_id,
            data.resolution_strategy,
            data.resolved_data,
            current_user.id,
            data.resolution_notes
        )
        return SyncConflictResponse.model_validate(conflict)
    except ConflictNotFoundError:
        raise HTTPException(status_code=404, detail="Conflit non trouve")
    except ConflictAlreadyResolvedError:
        raise HTTPException(status_code=400, detail="Conflit deja resolu")


# ============================================================================
# WEBHOOKS
# ============================================================================

@router.get("/webhooks", response_model=WebhookList)
async def list_webhooks(
    connection_id: UUID | None = Query(None),
    direction: WebhookDirection | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.webhook.read")
):
    """Liste les webhooks."""
    repo = WebhookRepository(db, current_user.tenant_id)
    items, total = repo.list(connection_id, direction, page, page_size)

    return WebhookList(
        items=[WebhookResponse.model_validate(w) for w in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/webhooks/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.webhook.read")
):
    """Obtenir un webhook."""
    repo = WebhookRepository(db, current_user.tenant_id)
    webhook = repo.get_by_id(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook non trouve")
    return WebhookResponse.model_validate(webhook)


@router.post("/webhooks/inbound", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_inbound_webhook(
    data: WebhookInboundCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.webhook.create")
):
    """Creer un webhook entrant."""
    conn_repo = ConnectionRepository(db, current_user.tenant_id)
    if not conn_repo.exists(data.connection_id):
        raise HTTPException(status_code=404, detail="Connexion non trouvee")

    service = get_service(db, current_user.tenant_id)
    webhook = service.create_inbound_webhook(
        data.connection_id,
        data.name,
        data.subscribed_events,
        current_user.id
    )
    return WebhookResponse.model_validate(webhook)


@router.post("/webhooks/outbound", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_outbound_webhook(
    data: WebhookOutboundCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.webhook.create")
):
    """Creer un webhook sortant."""
    conn_repo = ConnectionRepository(db, current_user.tenant_id)
    if not conn_repo.exists(data.connection_id):
        raise HTTPException(status_code=404, detail="Connexion non trouvee")

    service = get_service(db, current_user.tenant_id)
    webhook = service.create_outbound_webhook(
        data.connection_id,
        data.name,
        data.target_url,
        data.subscribed_events,
        data.headers,
        current_user.id
    )
    return WebhookResponse.model_validate(webhook)


@router.put("/webhooks/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    data: WebhookUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.webhook.update")
):
    """Mettre a jour un webhook."""
    repo = WebhookRepository(db, current_user.tenant_id)
    webhook = repo.get_by_id(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook non trouve")

    webhook = repo.update(webhook, data.model_dump(exclude_unset=True), current_user.id)
    return WebhookResponse.model_validate(webhook)


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.webhook.delete")
):
    """Supprimer un webhook."""
    repo = WebhookRepository(db, current_user.tenant_id)
    webhook = repo.get_by_id(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook non trouve")

    repo.delete(webhook)


@router.post("/webhooks/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    webhook_id: UUID,
    data: WebhookTestRequest | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.webhook.update")
):
    """Tester un webhook sortant."""
    service = get_service(db, current_user.tenant_id)

    try:
        result = service.test_webhook(
            webhook_id,
            data.sample_payload if data else None
        )
        return WebhookTestResponse(**result)
    except WebhookNotFoundError:
        raise HTTPException(status_code=404, detail="Webhook non trouve")


@router.get("/webhooks/{webhook_id}/logs", response_model=WebhookLogList)
async def get_webhook_logs(
    webhook_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.webhook.read")
):
    """Obtenir les logs d'un webhook."""
    webhook_repo = WebhookRepository(db, current_user.tenant_id)
    if not webhook_repo.get_by_id(webhook_id):
        raise HTTPException(status_code=404, detail="Webhook non trouve")

    repo = WebhookLogRepository(db, current_user.tenant_id)
    items, total = repo.get_by_webhook(webhook_id, limit, offset)

    return WebhookLogList(
        items=[WebhookLogResponse.model_validate(l) for l in items],
        total=total,
        page=1,
        page_size=limit,
        pages=math.ceil(total / limit) if total > 0 else 0
    )


# ============================================================================
# WEBHOOK RECEIVER (Public endpoint)
# ============================================================================

@router.post("/webhooks/receive/{endpoint_path:path}")
async def receive_webhook(
    endpoint_path: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Endpoint public pour recevoir les webhooks entrants."""
    # Recuperer le webhook par path
    # Note: en production, il faudrait un mecanisme pour identifier le tenant
    # Ici on simule avec un header X-Tenant-Id ou on cherche dans tous les tenants

    body = await request.body()
    signature = request.headers.get("X-Webhook-Signature", "")
    event_type = request.headers.get("X-Event-Type", "unknown")
    source_ip = request.client.host if request.client else None

    try:
        payload = await request.json()
    except Exception:
        payload = {"raw": body.decode() if body else ""}

    # Pour la demo, on retourne un succes
    return {
        "received": True,
        "endpoint": endpoint_path,
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# STATISTICS
# ============================================================================

@router.get("/stats", response_model=IntegrationStatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("integration.stats.read")
):
    """Obtenir les statistiques d'integration."""
    service = get_service(db, current_user.tenant_id)
    stats = service.get_statistics()
    return IntegrationStatsResponse(**stats)
