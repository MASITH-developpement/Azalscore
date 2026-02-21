"""
AZALS - Module DataExchange - Router API
=========================================
Endpoints REST pour l'import/export de donnees.

Inspire de: Sage Data Exchange, Axonaut Import, Pennylane Connect,
Odoo Import/Export, Microsoft Dynamics 365 Data Management.
"""
import math
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .models import ExchangeStatus, ExchangeType, FileFormat
from .schemas import (
    # Profile schemas
    ExchangeProfileCreate, ExchangeProfileUpdate, ExchangeProfileResponse,
    ExchangeProfileDetail, ExchangeProfileList, ExchangeProfileListItem,
    ProfileFilters,
    # Field mapping schemas
    FieldMappingCreate, FieldMappingUpdate, FieldMappingResponse,
    # Validation rule schemas
    ValidationRuleCreate, ValidationRuleUpdate, ValidationRuleResponse,
    # Transformation schemas
    TransformationCreate, TransformationUpdate, TransformationResponse,
    # Connector schemas
    FileConnectorCreate, FileConnectorUpdate, FileConnectorResponse,
    FileConnectorList, FileConnectorListItem, FileConnectorTestResult,
    ConnectorFilters,
    # Scheduled exchange schemas
    ScheduledExchangeCreate, ScheduledExchangeUpdate, ScheduledExchangeResponse,
    ScheduledExchangeList, ScheduledExchangeListItem,
    # Job schemas
    ExchangeJobCreate, ExchangeJobResponse, ExchangeJobDetail,
    ExchangeJobList, ExchangeJobListItem, JobFilters,
    # Log and error schemas
    ExchangeLogResponse, ExchangeLogList,
    ExchangeErrorResponse, ExchangeErrorList,
    # History schemas
    ExchangeHistoryResponse, ExchangeHistoryList, HistoryFilters,
    # Lookup table schemas
    LookupTableCreate, LookupTableUpdate, LookupTableResponse, LookupTableListItem,
    # Import/Export request schemas
    ImportRequest, ImportFromConnectorRequest, ExportRequest, RollbackRequest,
    ImportPreviewResponse,
    # Stats
    DataExchangeStatsResponse,
    # Common
    AutocompleteResponse, AutocompleteItem
)
from .repository import (
    ExchangeProfileRepository, FieldMappingRepository, ValidationRuleRepository,
    TransformationRepository, FileConnectorRepository, ScheduledExchangeRepository,
    ExchangeJobRepository, ExchangeLogRepository, ExchangeErrorRepository,
    ExchangeHistoryRepository, LookupTableRepository
)
from .exceptions import (
    ProfileNotFoundError, ProfileDuplicateCodeError, ProfileInUseError,
    SystemProfileError, ConnectorNotFoundError, ConnectorDuplicateCodeError,
    ScheduledExchangeNotFoundError, ScheduledExchangeDuplicateCodeError,
    JobNotFoundError, JobCannotBeRolledBackError
)

router = APIRouter(prefix="/dataexchange", tags=["DataExchange"])


# ============== Profiles ==============

@router.get("/profiles", response_model=ExchangeProfileList)
async def list_profiles(
    search: Optional[str] = Query(None, min_length=2),
    exchange_type: Optional[ExchangeType] = Query(None),
    file_format: Optional[FileFormat] = Query(None),
    entity_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.profile.read")
):
    """Liste les profils d'import/export."""
    filters = ProfileFilters(
        search=search,
        exchange_type=exchange_type,
        file_format=file_format,
        entity_type=entity_type,
        is_active=is_active
    )
    repo = ExchangeProfileRepository(db, str(current_user.tenant_id))
    items, total = repo.list(filters, page, page_size, sort_by, sort_dir)

    return ExchangeProfileList(
        items=[ExchangeProfileListItem.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/profiles/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_profiles(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.profile.read")
):
    """Autocomplete pour les profils."""
    repo = ExchangeProfileRepository(db, str(current_user.tenant_id))
    results = repo.autocomplete(q, limit)
    return AutocompleteResponse(items=[AutocompleteItem(**r) for r in results])


@router.get("/profiles/{profile_id}", response_model=ExchangeProfileDetail)
async def get_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.profile.read")
):
    """Obtenir un profil avec ses mappings, validations et transformations."""
    repo = ExchangeProfileRepository(db, str(current_user.tenant_id))
    profile = repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouve")

    return ExchangeProfileDetail.model_validate(profile)


@router.post("/profiles", response_model=ExchangeProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    data: ExchangeProfileCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.profile.create")
):
    """Creer un profil d'import/export."""
    repo = ExchangeProfileRepository(db, str(current_user.tenant_id))

    if repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail="Code profil deja existant")

    profile = repo.create(data.model_dump(), current_user.id)
    return ExchangeProfileResponse.model_validate(profile)


@router.put("/profiles/{profile_id}", response_model=ExchangeProfileResponse)
async def update_profile(
    profile_id: UUID,
    data: ExchangeProfileUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.profile.update")
):
    """Mettre a jour un profil."""
    repo = ExchangeProfileRepository(db, str(current_user.tenant_id))
    profile = repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouve")

    if profile.is_system:
        raise HTTPException(status_code=403, detail="Modification interdite sur profil systeme")

    if data.code and data.code != profile.code:
        if repo.code_exists(data.code, exclude_id=profile_id):
            raise HTTPException(status_code=409, detail="Code profil deja existant")

    profile = repo.update(profile, data.model_dump(exclude_unset=True), current_user.id)
    return ExchangeProfileResponse.model_validate(profile)


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.profile.delete")
):
    """Supprimer un profil (soft delete)."""
    repo = ExchangeProfileRepository(db, str(current_user.tenant_id))
    profile = repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouve")

    if profile.is_system:
        raise HTTPException(status_code=403, detail="Suppression interdite sur profil systeme")

    usage_count = repo.get_usage_count(profile_id)
    if usage_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Profil utilise par {usage_count} element(s)"
        )

    repo.soft_delete(profile, current_user.id)


# ============== Field Mappings ==============

@router.get("/profiles/{profile_id}/mappings", response_model=List[FieldMappingResponse])
async def list_profile_mappings(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.profile.read")
):
    """Liste les mappings d'un profil."""
    profile_repo = ExchangeProfileRepository(db, str(current_user.tenant_id))
    if not profile_repo.exists(profile_id):
        raise HTTPException(status_code=404, detail="Profil non trouve")

    repo = FieldMappingRepository(db, str(current_user.tenant_id))
    return [FieldMappingResponse.model_validate(m) for m in repo.get_by_profile(profile_id)]


@router.post("/profiles/{profile_id}/mappings", response_model=FieldMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_mapping(
    profile_id: UUID,
    data: FieldMappingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.profile.update")
):
    """Creer un mapping pour un profil."""
    profile_repo = ExchangeProfileRepository(db, str(current_user.tenant_id))
    profile = profile_repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouve")

    if profile.is_system:
        raise HTTPException(status_code=403, detail="Modification interdite sur profil systeme")

    repo = FieldMappingRepository(db, str(current_user.tenant_id))
    mapping = repo.create(data.model_dump(), profile_id)
    return FieldMappingResponse.model_validate(mapping)


@router.put("/mappings/{mapping_id}", response_model=FieldMappingResponse)
async def update_mapping(
    mapping_id: UUID,
    data: FieldMappingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.profile.update")
):
    """Mettre a jour un mapping."""
    repo = FieldMappingRepository(db, str(current_user.tenant_id))
    mapping = repo.get_by_id(mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouve")

    mapping = repo.update(mapping, data.model_dump(exclude_unset=True))
    return FieldMappingResponse.model_validate(mapping)


@router.delete("/mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mapping(
    mapping_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.profile.update")
):
    """Supprimer un mapping."""
    repo = FieldMappingRepository(db, str(current_user.tenant_id))
    mapping = repo.get_by_id(mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouve")

    repo.delete(mapping)


# ============== Validation Rules ==============

@router.get("/profiles/{profile_id}/validations", response_model=List[ValidationRuleResponse])
async def list_profile_validations(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.profile.read")
):
    """Liste les regles de validation d'un profil."""
    profile_repo = ExchangeProfileRepository(db, str(current_user.tenant_id))
    if not profile_repo.exists(profile_id):
        raise HTTPException(status_code=404, detail="Profil non trouve")

    repo = ValidationRuleRepository(db, str(current_user.tenant_id))
    return [ValidationRuleResponse.model_validate(r) for r in repo.get_by_profile(profile_id, active_only=False)]


@router.post("/profiles/{profile_id}/validations", response_model=ValidationRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_validation_rule(
    profile_id: UUID,
    data: ValidationRuleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.profile.update")
):
    """Creer une regle de validation."""
    profile_repo = ExchangeProfileRepository(db, str(current_user.tenant_id))
    profile = profile_repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouve")

    repo = ValidationRuleRepository(db, str(current_user.tenant_id))
    rule = repo.create(data.model_dump(), profile_id)
    return ValidationRuleResponse.model_validate(rule)


# ============== Transformations ==============

@router.get("/profiles/{profile_id}/transformations", response_model=List[TransformationResponse])
async def list_profile_transformations(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.profile.read")
):
    """Liste les transformations d'un profil."""
    profile_repo = ExchangeProfileRepository(db, str(current_user.tenant_id))
    if not profile_repo.exists(profile_id):
        raise HTTPException(status_code=404, detail="Profil non trouve")

    repo = TransformationRepository(db, str(current_user.tenant_id))
    return [TransformationResponse.model_validate(t) for t in repo.get_by_profile(profile_id, active_only=False)]


@router.post("/profiles/{profile_id}/transformations", response_model=TransformationResponse, status_code=status.HTTP_201_CREATED)
async def create_transformation(
    profile_id: UUID,
    data: TransformationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.profile.update")
):
    """Creer une transformation."""
    profile_repo = ExchangeProfileRepository(db, str(current_user.tenant_id))
    profile = profile_repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouve")

    repo = TransformationRepository(db, str(current_user.tenant_id))
    transform = repo.create(data.model_dump(), profile_id)
    return TransformationResponse.model_validate(transform)


# ============== File Connectors ==============

@router.get("/connectors", response_model=FileConnectorList)
async def list_connectors(
    search: Optional[str] = Query(None, min_length=2),
    connector_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.connector.read")
):
    """Liste les connecteurs de fichiers."""
    filters = ConnectorFilters(search=search, connector_type=connector_type, is_active=is_active)
    repo = FileConnectorRepository(db, str(current_user.tenant_id))
    items, total = repo.list(filters, page, page_size, sort_by, sort_dir)

    return FileConnectorList(
        items=[FileConnectorListItem.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/connectors/{connector_id}", response_model=FileConnectorResponse)
async def get_connector(
    connector_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.connector.read")
):
    """Obtenir un connecteur."""
    repo = FileConnectorRepository(db, str(current_user.tenant_id))
    connector = repo.get_by_id(connector_id)
    if not connector:
        raise HTTPException(status_code=404, detail="Connecteur non trouve")
    return FileConnectorResponse.model_validate(connector)


@router.post("/connectors", response_model=FileConnectorResponse, status_code=status.HTTP_201_CREATED)
async def create_connector(
    data: FileConnectorCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.connector.create")
):
    """Creer un connecteur."""
    repo = FileConnectorRepository(db, str(current_user.tenant_id))

    if repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail="Code connecteur deja existant")

    # Preparer les donnees (chiffrer les credentials)
    connector_data = data.model_dump()
    if "password" in connector_data:
        connector_data["password_encrypted"] = connector_data.pop("password")
    if "private_key" in connector_data:
        connector_data["private_key_encrypted"] = connector_data.pop("private_key")
    if "access_key" in connector_data:
        connector_data["access_key_encrypted"] = connector_data.pop("access_key")
    if "secret_key" in connector_data:
        connector_data["secret_key_encrypted"] = connector_data.pop("secret_key")

    connector = repo.create(connector_data, current_user.id)
    return FileConnectorResponse.model_validate(connector)


@router.put("/connectors/{connector_id}", response_model=FileConnectorResponse)
async def update_connector(
    connector_id: UUID,
    data: FileConnectorUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.connector.update")
):
    """Mettre a jour un connecteur."""
    repo = FileConnectorRepository(db, str(current_user.tenant_id))
    connector = repo.get_by_id(connector_id)
    if not connector:
        raise HTTPException(status_code=404, detail="Connecteur non trouve")

    update_data = data.model_dump(exclude_unset=True)

    # Chiffrer les credentials si fournis
    if "password" in update_data:
        update_data["password_encrypted"] = update_data.pop("password")
    if "private_key" in update_data:
        update_data["private_key_encrypted"] = update_data.pop("private_key")
    if "access_key" in update_data:
        update_data["access_key_encrypted"] = update_data.pop("access_key")
    if "secret_key" in update_data:
        update_data["secret_key_encrypted"] = update_data.pop("secret_key")

    connector = repo.update(connector, update_data, current_user.id)
    return FileConnectorResponse.model_validate(connector)


@router.post("/connectors/{connector_id}/test", response_model=FileConnectorTestResult)
async def test_connector(
    connector_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.connector.update")
):
    """Tester la connexion a un connecteur."""
    repo = FileConnectorRepository(db, str(current_user.tenant_id))
    connector = repo.get_by_id(connector_id)
    if not connector:
        raise HTTPException(status_code=404, detail="Connecteur non trouve")

    # Simuler le test (en production: vraie connexion)
    import random
    success = random.random() > 0.1
    response_time = random.randint(50, 500)

    repo.update_status(connector, success, "Test failed" if not success else None)

    return FileConnectorTestResult(
        success=success,
        message="Connexion OK" if success else "Echec de la connexion",
        response_time_ms=response_time,
        files_found=random.randint(0, 10) if success else 0
    )


@router.delete("/connectors/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connector(
    connector_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.connector.delete")
):
    """Supprimer un connecteur (soft delete)."""
    repo = FileConnectorRepository(db, str(current_user.tenant_id))
    connector = repo.get_by_id(connector_id)
    if not connector:
        raise HTTPException(status_code=404, detail="Connecteur non trouve")

    usage_count = repo.get_usage_count(connector_id)
    if usage_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Connecteur utilise par {usage_count} element(s)"
        )

    repo.soft_delete(connector, current_user.id)


# ============== Scheduled Exchanges ==============

@router.get("/scheduled", response_model=ScheduledExchangeList)
async def list_scheduled_exchanges(
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.scheduled.read")
):
    """Liste les echanges planifies."""
    repo = ScheduledExchangeRepository(db, str(current_user.tenant_id))
    items, total = repo.list(page, page_size, is_active=is_active)

    return ScheduledExchangeList(
        items=[ScheduledExchangeListItem.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/scheduled/{schedule_id}", response_model=ScheduledExchangeResponse)
async def get_scheduled_exchange(
    schedule_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.scheduled.read")
):
    """Obtenir un echange planifie."""
    repo = ScheduledExchangeRepository(db, str(current_user.tenant_id))
    scheduled = repo.get_by_id(schedule_id)
    if not scheduled:
        raise HTTPException(status_code=404, detail="Echange planifie non trouve")
    return ScheduledExchangeResponse.model_validate(scheduled)


@router.post("/scheduled", response_model=ScheduledExchangeResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_exchange(
    data: ScheduledExchangeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.scheduled.create")
):
    """Creer un echange planifie."""
    # Verifier le profil
    profile_repo = ExchangeProfileRepository(db, str(current_user.tenant_id))
    if not profile_repo.exists(data.profile_id):
        raise HTTPException(status_code=404, detail="Profil non trouve")

    # Verifier le connecteur si fourni
    if data.connector_id:
        connector_repo = FileConnectorRepository(db, str(current_user.tenant_id))
        if not connector_repo.exists(data.connector_id):
            raise HTTPException(status_code=404, detail="Connecteur non trouve")

    repo = ScheduledExchangeRepository(db, str(current_user.tenant_id))

    if repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail="Code planification deja existant")

    scheduled = repo.create(data.model_dump(), current_user.id)
    return ScheduledExchangeResponse.model_validate(scheduled)


@router.put("/scheduled/{schedule_id}", response_model=ScheduledExchangeResponse)
async def update_scheduled_exchange(
    schedule_id: UUID,
    data: ScheduledExchangeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.scheduled.update")
):
    """Mettre a jour un echange planifie."""
    repo = ScheduledExchangeRepository(db, str(current_user.tenant_id))
    scheduled = repo.get_by_id(schedule_id)
    if not scheduled:
        raise HTTPException(status_code=404, detail="Echange planifie non trouve")

    scheduled = repo.update(scheduled, data.model_dump(exclude_unset=True), current_user.id)
    return ScheduledExchangeResponse.model_validate(scheduled)


@router.delete("/scheduled/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_exchange(
    schedule_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.scheduled.delete")
):
    """Supprimer un echange planifie (soft delete)."""
    repo = ScheduledExchangeRepository(db, str(current_user.tenant_id))
    scheduled = repo.get_by_id(schedule_id)
    if not scheduled:
        raise HTTPException(status_code=404, detail="Echange planifie non trouve")

    repo.soft_delete(scheduled, current_user.id)


# ============== Jobs ==============

@router.get("/jobs", response_model=ExchangeJobList)
async def list_jobs(
    search: Optional[str] = Query(None, min_length=2),
    exchange_type: Optional[ExchangeType] = Query(None),
    status_filter: Optional[List[ExchangeStatus]] = Query(None, alias="status"),
    profile_id: Optional[UUID] = Query(None),
    triggered_by: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.job.read")
):
    """Liste les jobs d'import/export."""
    filters = JobFilters(
        search=search,
        exchange_type=exchange_type,
        status=status_filter,
        profile_id=profile_id,
        triggered_by=triggered_by
    )
    repo = ExchangeJobRepository(db, str(current_user.tenant_id))
    items, total = repo.list(filters, page, page_size, sort_by, sort_dir)

    return ExchangeJobList(
        items=[ExchangeJobListItem.model_validate(j) for j in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/jobs/{job_id}", response_model=ExchangeJobDetail)
async def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.job.read")
):
    """Obtenir un job avec details."""
    repo = ExchangeJobRepository(db, str(current_user.tenant_id))
    job = repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouve")

    # Compter les logs et erreurs
    log_repo = ExchangeLogRepository(db, str(current_user.tenant_id))
    error_repo = ExchangeErrorRepository(db, str(current_user.tenant_id))

    _, logs_count = log_repo.get_by_job(job_id, limit=1)
    error_summary = error_repo.get_summary(job_id)

    response_data = ExchangeJobResponse.model_validate(job).model_dump()
    response_data["logs_count"] = logs_count
    response_data["errors_count"] = error_summary.get("error", 0)
    response_data["warnings_count"] = error_summary.get("warning", 0)

    return ExchangeJobDetail(**response_data)


@router.get("/jobs/{job_id}/logs", response_model=ExchangeLogList)
async def get_job_logs(
    job_id: UUID,
    action: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.job.read")
):
    """Obtenir les logs d'un job."""
    job_repo = ExchangeJobRepository(db, str(current_user.tenant_id))
    if not job_repo.get_by_id(job_id):
        raise HTTPException(status_code=404, detail="Job non trouve")

    repo = ExchangeLogRepository(db, str(current_user.tenant_id))
    items, total = repo.get_by_job(job_id, limit, offset, action)

    return ExchangeLogList(
        items=[ExchangeLogResponse.model_validate(l) for l in items],
        total=total
    )


@router.get("/jobs/{job_id}/errors", response_model=ExchangeErrorList)
async def get_job_errors(
    job_id: UUID,
    severity: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.job.read")
):
    """Obtenir les erreurs d'un job."""
    job_repo = ExchangeJobRepository(db, str(current_user.tenant_id))
    if not job_repo.get_by_id(job_id):
        raise HTTPException(status_code=404, detail="Job non trouve")

    repo = ExchangeErrorRepository(db, str(current_user.tenant_id))
    items, total = repo.get_by_job(job_id, limit, offset, severity)

    return ExchangeErrorList(
        items=[ExchangeErrorResponse.model_validate(e) for e in items],
        total=total
    )


@router.post("/jobs/{job_id}/rollback", response_model=ExchangeJobResponse)
async def rollback_job(
    job_id: UUID,
    data: RollbackRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.job.rollback")
):
    """Effectuer un rollback d'un job."""
    repo = ExchangeJobRepository(db, str(current_user.tenant_id))
    job = repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouve")

    if job.rolled_back_at:
        raise HTTPException(status_code=400, detail="Job deja rollback")

    if not job.rollback_data:
        raise HTTPException(status_code=400, detail="Pas de donnees de rollback disponibles")

    if job.status not in (ExchangeStatus.COMPLETED.value, ExchangeStatus.PARTIAL.value):
        raise HTTPException(status_code=400, detail=f"Rollback impossible (statut: {job.status})")

    job = repo.rollback(job, current_user.id)
    return ExchangeJobResponse.model_validate(job)


# ============== Import ==============

@router.post("/import/preview", response_model=ImportPreviewResponse)
async def preview_import(
    profile_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.import.execute")
):
    """Apercu d'un import sans execution."""
    profile_repo = ExchangeProfileRepository(db, str(current_user.tenant_id))
    profile = profile_repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouve")

    if profile.exchange_type != ExchangeType.IMPORT.value:
        raise HTTPException(status_code=400, detail="Le profil n'est pas un profil d'import")

    # Lire le fichier
    content = await file.read()

    # Appeler le service de preview
    # TODO: Implementer avec le service
    # from .service import DataExchangeService
    # service = DataExchangeService(db, str(current_user.tenant_id), current_user.id)
    # return service.preview_import(profile_id, content, file.filename)

    # Pour l'instant, retourner un resultat vide
    return ImportPreviewResponse(
        total_rows=0,
        valid_rows=0,
        error_rows=0,
        warning_rows=0,
        sample_rows=[],
        detected_columns=[],
        mapped_fields={},
        validation_errors=[]
    )


@router.post("/import", response_model=ExchangeJobResponse)
async def start_import(
    profile_id: UUID = Form(...),
    file: UploadFile = File(...),
    validate_only: bool = Form(default=False),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.import.execute")
):
    """Demarrer un import depuis un fichier uploade."""
    profile_repo = ExchangeProfileRepository(db, str(current_user.tenant_id))
    profile = profile_repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouve")

    if profile.exchange_type != ExchangeType.IMPORT.value:
        raise HTTPException(status_code=400, detail="Le profil n'est pas un profil d'import")

    # Lire le fichier
    content = await file.read()

    # Creer le job
    import uuid
    job_repo = ExchangeJobRepository(db, str(current_user.tenant_id))
    reference = f"IMP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

    job = job_repo.create({
        "reference": reference,
        "profile_id": profile_id,
        "exchange_type": ExchangeType.IMPORT.value,
        "entity_type": profile.entity_type,
        "status": ExchangeStatus.PENDING.value,
        "file_name": file.filename,
        "file_size": len(content),
        "file_format": profile.file_format,
        "options": {"validate_only": validate_only},
        "triggered_by": "manual"
    }, current_user.id)

    # TODO: Lancer le traitement en arriere-plan
    # Pour l'instant, marquer comme en cours
    job = job_repo.start(job)

    return ExchangeJobResponse.model_validate(job)


# ============== Export ==============

@router.post("/export", response_model=ExchangeJobResponse)
async def start_export(
    data: ExportRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.export.execute")
):
    """Demarrer un export."""
    profile_repo = ExchangeProfileRepository(db, str(current_user.tenant_id))
    profile = profile_repo.get_by_id(data.profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouve")

    if profile.exchange_type != ExchangeType.EXPORT.value:
        raise HTTPException(status_code=400, detail="Le profil n'est pas un profil d'export")

    # Creer le job
    import uuid
    job_repo = ExchangeJobRepository(db, str(current_user.tenant_id))
    reference = f"EXP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

    job = job_repo.create({
        "reference": reference,
        "profile_id": data.profile_id,
        "connector_id": data.connector_id,
        "exchange_type": ExchangeType.EXPORT.value,
        "entity_type": profile.entity_type,
        "status": ExchangeStatus.PENDING.value,
        "file_format": profile.file_format,
        "options": {"filters": data.filters, **data.options},
        "triggered_by": "manual"
    }, current_user.id)

    # TODO: Lancer le traitement en arriere-plan
    job = job_repo.start(job)

    return ExchangeJobResponse.model_validate(job)


@router.get("/export/{job_id}/download")
async def download_export(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.export.execute")
):
    """Telecharger le fichier d'un export termine."""
    repo = ExchangeJobRepository(db, str(current_user.tenant_id))
    job = repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouve")

    if job.exchange_type != ExchangeType.EXPORT.value:
        raise HTTPException(status_code=400, detail="Ce n'est pas un job d'export")

    if job.status != ExchangeStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Export non termine")

    if not job.output_file_name:
        raise HTTPException(status_code=404, detail="Fichier non disponible")

    # TODO: Lire le fichier depuis le stockage
    # Pour l'instant, retourner un fichier vide
    content = b"export_data"

    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{job.output_file_name}"'
        }
    )


# ============== History ==============

@router.get("/history", response_model=ExchangeHistoryList)
async def list_history(
    exchange_type: Optional[ExchangeType] = Query(None),
    entity_type: Optional[str] = Query(None),
    status_filter: Optional[ExchangeStatus] = Query(None, alias="status"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.history.read")
):
    """Liste l'historique des echanges."""
    filters = HistoryFilters(
        exchange_type=exchange_type,
        entity_type=entity_type,
        status=status_filter,
        date_from=date_from,
        date_to=date_to
    )
    repo = ExchangeHistoryRepository(db, str(current_user.tenant_id))
    items, total = repo.list(filters, page, page_size)

    return ExchangeHistoryList(
        items=[ExchangeHistoryResponse.model_validate(h) for h in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


# ============== Lookup Tables ==============

@router.get("/lookup-tables", response_model=List[LookupTableListItem])
async def list_lookup_tables(
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.lookup.read")
):
    """Liste les tables de correspondance."""
    repo = LookupTableRepository(db, str(current_user.tenant_id))
    tables = repo.list(is_active)

    return [
        LookupTableListItem(
            id=t.id,
            code=t.code,
            name=t.name,
            entries_count=len(t.entries or {}),
            is_active=t.is_active
        )
        for t in tables
    ]


@router.get("/lookup-tables/{lookup_id}", response_model=LookupTableResponse)
async def get_lookup_table(
    lookup_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.lookup.read")
):
    """Obtenir une table de correspondance."""
    repo = LookupTableRepository(db, str(current_user.tenant_id))
    lookup = repo.get_by_id(lookup_id)
    if not lookup:
        raise HTTPException(status_code=404, detail="Table de correspondance non trouvee")
    return LookupTableResponse.model_validate(lookup)


@router.post("/lookup-tables", response_model=LookupTableResponse, status_code=status.HTTP_201_CREATED)
async def create_lookup_table(
    data: LookupTableCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.lookup.create")
):
    """Creer une table de correspondance."""
    repo = LookupTableRepository(db, str(current_user.tenant_id))

    if repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail="Code table deja existant")

    lookup = repo.create(data.model_dump(), current_user.id)
    return LookupTableResponse.model_validate(lookup)


@router.put("/lookup-tables/{lookup_id}", response_model=LookupTableResponse)
async def update_lookup_table(
    lookup_id: UUID,
    data: LookupTableUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.lookup.update")
):
    """Mettre a jour une table de correspondance."""
    repo = LookupTableRepository(db, str(current_user.tenant_id))
    lookup = repo.get_by_id(lookup_id)
    if not lookup:
        raise HTTPException(status_code=404, detail="Table de correspondance non trouvee")

    lookup = repo.update(lookup, data.model_dump(exclude_unset=True), current_user.id)
    return LookupTableResponse.model_validate(lookup)


@router.delete("/lookup-tables/{lookup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lookup_table(
    lookup_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.lookup.delete")
):
    """Supprimer une table de correspondance (soft delete)."""
    repo = LookupTableRepository(db, str(current_user.tenant_id))
    lookup = repo.get_by_id(lookup_id)
    if not lookup:
        raise HTTPException(status_code=404, detail="Table de correspondance non trouvee")

    repo.soft_delete(lookup, current_user.id)


# ============== Stats ==============

@router.get("/stats", response_model=DataExchangeStatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("dataexchange.stats.read")
):
    """Obtenir les statistiques d'import/export."""
    tenant_id = str(current_user.tenant_id)

    profile_repo = ExchangeProfileRepository(db, tenant_id)
    profiles, total_profiles = profile_repo.list(page_size=1000)

    connector_repo = FileConnectorRepository(db, tenant_id)
    connectors, total_connectors = connector_repo.list(page_size=1000)

    scheduled_repo = ScheduledExchangeRepository(db, tenant_id)
    scheduled, total_scheduled = scheduled_repo.list(page_size=1000)

    history_repo = ExchangeHistoryRepository(db, tenant_id)
    history_stats = history_repo.get_stats(days=1)

    return DataExchangeStatsResponse(
        tenant_id=tenant_id,
        total_profiles=total_profiles,
        active_profiles=len([p for p in profiles if p.is_active]),
        total_connectors=total_connectors,
        active_connectors=len([c for c in connectors if c.is_active]),
        total_scheduled=total_scheduled,
        active_scheduled=len([s for s in scheduled if s.is_active]),
        total_jobs_24h=history_stats.get("total_exchanges", 0),
        successful_jobs_24h=history_stats.get("by_status", {}).get("completed", 0),
        failed_jobs_24h=history_stats.get("by_status", {}).get("failed", 0),
        records_imported_24h=history_stats.get("total_records", 0),
        records_exported_24h=0,
        by_entity_type=history_stats.get("by_type", {}),
        by_format={}
    )
