"""
Repository - Module Integrations (GAP-086)

CRITIQUE: Toutes les requêtes filtrées par tenant_id.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session, joinedload

from .models import (
    Connection, EntityMapping, SyncJob, SyncLog, Conflict, Webhook,
    ConnectionStatus, SyncStatus, ConnectorType, SyncDirection
)
from .schemas import ConnectionFilters, SyncJobFilters


class ConnectionRepository:
    """Repository Connection avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(Connection).filter(Connection.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(Connection.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[Connection]:
        return self._base_query().options(
            joinedload(Connection.entity_mappings)
        ).filter(Connection.id == id).first()

    def get_by_code(self, code: str) -> Optional[Connection]:
        return self._base_query().filter(Connection.code == code.upper()).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(Connection.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(Connection.code == code.upper())
        if exclude_id:
            query = query.filter(Connection.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: ConnectionFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[Connection], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    Connection.name.ilike(term),
                    Connection.code.ilike(term),
                    Connection.description.ilike(term)
                ))
            if filters.connector_type:
                query = query.filter(Connection.connector_type.in_([t.value for t in filters.connector_type]))
            if filters.status:
                query = query.filter(Connection.status.in_([s.value for s in filters.status]))
            if filters.is_active is not None:
                query = query.filter(Connection.is_active == filters.is_active)

        total = query.count()
        sort_col = getattr(Connection, sort_by, Connection.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_by_type(self, connector_type: ConnectorType) -> List[Connection]:
        return self._base_query().filter(
            Connection.connector_type == connector_type.value,
            Connection.is_active == True
        ).all()

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, str]]:
        if len(prefix) < 2:
            return []
        query = self._base_query().filter(
            Connection.is_active == True
        ).filter(or_(
            Connection.name.ilike(f"{prefix}%"),
            Connection.code.ilike(f"{prefix}%")
        ))
        results = query.order_by(Connection.name).limit(limit).all()
        return [
            {"id": str(c.id), "code": c.code, "name": c.name, "label": f"[{c.code}] {c.name}"}
            for c in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Connection:
        entity = Connection(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: Connection, data: Dict[str, Any], updated_by: UUID = None) -> Connection:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update_status(
        self,
        entity: Connection,
        status: ConnectionStatus,
        error: str = None
    ) -> Connection:
        entity.status = status.value
        if status == ConnectionStatus.CONNECTED:
            entity.last_connected_at = datetime.utcnow()
            entity.consecutive_errors = 0
            entity.last_error = None
        elif status == ConnectionStatus.ERROR:
            entity.consecutive_errors = (entity.consecutive_errors or 0) + 1
            entity.last_error = error
        entity.last_health_check = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update_tokens(
        self,
        entity: Connection,
        access_token: str,
        refresh_token: str = None,
        expires_at: datetime = None
    ) -> Connection:
        entity.access_token = access_token
        if refresh_token:
            entity.refresh_token = refresh_token
        if expires_at:
            entity.token_expires_at = expires_at
        entity.status = ConnectionStatus.CONNECTED.value
        entity.last_connected_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: Connection, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, entity: Connection) -> Connection:
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        self.db.commit()
        self.db.refresh(entity)
        return entity


class EntityMappingRepository:
    """Repository EntityMapping avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(EntityMapping).filter(EntityMapping.tenant_id == self.tenant_id)

    def get_by_id(self, id: UUID) -> Optional[EntityMapping]:
        return self._base_query().filter(EntityMapping.id == id).first()

    def get_by_code(self, code: str) -> Optional[EntityMapping]:
        return self._base_query().filter(EntityMapping.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(EntityMapping.code == code.upper())
        if exclude_id:
            query = query.filter(EntityMapping.id != exclude_id)
        return query.count() > 0

    def get_by_connection(self, connection_id: UUID) -> List[EntityMapping]:
        return self._base_query().filter(
            EntityMapping.connection_id == connection_id,
            EntityMapping.is_active == True
        ).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> EntityMapping:
        entity = EntityMapping(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: EntityMapping, data: Dict[str, Any], updated_by: UUID = None) -> EntityMapping:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity


class SyncJobRepository:
    """Repository SyncJob avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(SyncJob).filter(SyncJob.tenant_id == self.tenant_id)

    def get_by_id(self, id: UUID) -> Optional[SyncJob]:
        return self._base_query().options(
            joinedload(SyncJob.logs)
        ).filter(SyncJob.id == id).first()

    def list(
        self,
        filters: SyncJobFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[SyncJob], int]:
        query = self._base_query()

        if filters:
            if filters.connection_id:
                query = query.filter(SyncJob.connection_id == filters.connection_id)
            if filters.entity_mapping_id:
                query = query.filter(SyncJob.entity_mapping_id == filters.entity_mapping_id)
            if filters.status:
                query = query.filter(SyncJob.status.in_([s.value for s in filters.status]))
            if filters.direction:
                query = query.filter(SyncJob.direction == filters.direction.value)

        total = query.count()
        sort_col = getattr(SyncJob, sort_by, SyncJob.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_pending_jobs(self) -> List[SyncJob]:
        """Jobs planifiés à exécuter."""
        now = datetime.utcnow()
        return self._base_query().filter(
            SyncJob.status == SyncStatus.PENDING.value,
            or_(
                SyncJob.next_run_at.is_(None),
                SyncJob.next_run_at <= now
            )
        ).all()

    def get_running_for_connection(self, connection_id: UUID) -> Optional[SyncJob]:
        """Vérifier si un job est en cours pour une connexion."""
        return self._base_query().filter(
            SyncJob.connection_id == connection_id,
            SyncJob.status == SyncStatus.RUNNING.value
        ).first()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> SyncJob:
        entity = SyncJob(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def start(self, job: SyncJob) -> SyncJob:
        job.status = SyncStatus.RUNNING.value
        job.started_at = datetime.utcnow()
        job.errors = []
        self.db.commit()
        self.db.refresh(job)
        return job

    def complete(
        self,
        job: SyncJob,
        status: SyncStatus,
        total: int,
        created: int,
        updated: int,
        skipped: int,
        failed: int
    ) -> SyncJob:
        job.status = status.value
        job.completed_at = datetime.utcnow()
        job.total_records = total
        job.processed_records = created + updated + skipped + failed
        job.created_records = created
        job.updated_records = updated
        job.skipped_records = skipped
        job.failed_records = failed
        job.last_sync_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job

    def add_error(self, job: SyncJob, error: Dict[str, Any]) -> SyncJob:
        errors = list(job.errors or [])
        errors.append(error)
        job.errors = errors
        self.db.commit()
        return job

    def cancel(self, job: SyncJob) -> SyncJob:
        if job.status == SyncStatus.RUNNING.value:
            job.status = SyncStatus.CANCELLED.value
            job.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(job)
        return job


class SyncLogRepository:
    """Repository SyncLog avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(SyncLog).filter(SyncLog.tenant_id == self.tenant_id)

    def get_by_job(self, job_id: UUID, limit: int = 100, offset: int = 0) -> Tuple[List[SyncLog], int]:
        query = self._base_query().filter(SyncLog.job_id == job_id)
        total = query.count()
        items = query.order_by(desc(SyncLog.timestamp)).offset(offset).limit(limit).all()
        return items, total

    def create(self, data: Dict[str, Any]) -> SyncLog:
        entity = SyncLog(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def create_batch(self, logs: List[Dict[str, Any]]) -> int:
        for log_data in logs:
            log = SyncLog(tenant_id=self.tenant_id, **log_data)
            self.db.add(log)
        self.db.commit()
        return len(logs)


class ConflictRepository:
    """Repository Conflict avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Conflict).filter(Conflict.tenant_id == self.tenant_id)

    def get_by_id(self, id: UUID) -> Optional[Conflict]:
        return self._base_query().filter(Conflict.id == id).first()

    def get_pending(self, limit: int = 100) -> List[Conflict]:
        return self._base_query().filter(
            Conflict.resolved_at.is_(None)
        ).order_by(Conflict.created_at).limit(limit).all()

    def get_pending_count(self) -> int:
        return self._base_query().filter(Conflict.resolved_at.is_(None)).count()

    def get_by_job(self, job_id: UUID) -> List[Conflict]:
        return self._base_query().filter(Conflict.job_id == job_id).all()

    def create(self, data: Dict[str, Any]) -> Conflict:
        entity = Conflict(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def resolve(
        self,
        conflict: Conflict,
        resolution: str,
        resolved_data: Dict[str, Any],
        resolved_by: UUID
    ) -> Conflict:
        conflict.resolution = resolution
        conflict.resolved_data = resolved_data
        conflict.resolved_at = datetime.utcnow()
        conflict.resolved_by = resolved_by
        self.db.commit()
        self.db.refresh(conflict)
        return conflict


class WebhookRepository:
    """Repository Webhook avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Webhook).filter(Webhook.tenant_id == self.tenant_id)

    def get_by_id(self, id: UUID) -> Optional[Webhook]:
        return self._base_query().filter(Webhook.id == id).first()

    def get_by_path(self, path: str) -> Optional[Webhook]:
        return self._base_query().filter(
            Webhook.endpoint_path == path,
            Webhook.is_active == True
        ).first()

    def get_by_connection(self, connection_id: UUID) -> List[Webhook]:
        return self._base_query().filter(Webhook.connection_id == connection_id).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Webhook:
        entity = Webhook(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def record_received(self, webhook: Webhook) -> Webhook:
        webhook.last_received_at = datetime.utcnow()
        webhook.total_received = (webhook.total_received or 0) + 1
        self.db.commit()
        return webhook
