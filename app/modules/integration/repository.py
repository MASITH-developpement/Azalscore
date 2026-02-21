"""
AZALS MODULE GAP-086 - Repository Integration
==============================================

Repository avec isolation tenant obligatoire.
Toutes les requetes utilisent _base_query() filtre par tenant_id.
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from .models import (
    Connection,
    ConnectionStatus,
    ConnectorDefinition,
    DataMapping,
    ExecutionLog,
    HealthStatus,
    IntegrationDashboard,
    SyncConfiguration,
    SyncConflict,
    SyncExecution,
    SyncStatus,
    TransformationRule,
    Webhook,
    WebhookDirection,
    WebhookLog,
)
from .schemas import ConnectionFilters, ConflictFilters, SyncExecutionFilters


class ConnectorDefinitionRepository:
    """Repository pour les definitions de connecteurs (global, pas de tenant)."""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, active_only: bool = True) -> list[ConnectorDefinition]:
        """Liste tous les connecteurs."""
        query = self.db.query(ConnectorDefinition)
        if active_only:
            query = query.filter(ConnectorDefinition.is_active == True)
        return query.order_by(ConnectorDefinition.name).all()

    def get_by_type(self, connector_type: str) -> ConnectorDefinition | None:
        """Recupere un connecteur par type."""
        return self.db.query(ConnectorDefinition).filter(
            ConnectorDefinition.connector_type == connector_type
        ).first()

    def get_by_category(self, category: str) -> list[ConnectorDefinition]:
        """Liste les connecteurs par categorie."""
        return self.db.query(ConnectorDefinition).filter(
            ConnectorDefinition.category == category,
            ConnectorDefinition.is_active == True
        ).order_by(ConnectorDefinition.name).all()


class ConnectionRepository:
    """Repository Connection avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base filtree par tenant."""
        query = self.db.query(Connection).filter(Connection.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(Connection.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Connection | None:
        """Recupere une connexion par ID."""
        return self._base_query().options(
            joinedload(Connection.mappings),
            joinedload(Connection.sync_configs),
            joinedload(Connection.webhooks)
        ).filter(Connection.id == id).first()

    def get_by_code(self, code: str) -> Connection | None:
        """Recupere une connexion par code."""
        return self._base_query().filter(Connection.code == code.upper()).first()

    def exists(self, id: UUID) -> bool:
        """Verifie si une connexion existe."""
        return self._base_query().filter(Connection.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        """Verifie si un code existe."""
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
    ) -> tuple[list[Connection], int]:
        """Liste les connexions avec filtres et pagination."""
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
                types = [t.value for t in filters.connector_type]
                query = query.filter(Connection.connector_type.in_(types))
            if filters.status:
                statuses = [s.value for s in filters.status]
                query = query.filter(Connection.status.in_(statuses))
            if filters.health_status:
                healths = [h.value for h in filters.health_status]
                query = query.filter(Connection.health_status.in_(healths))
            if filters.is_active is not None:
                query = query.filter(Connection.is_active == filters.is_active)

        total = query.count()
        sort_col = getattr(Connection, sort_by, Connection.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_by_type(self, connector_type: str, active_only: bool = True) -> list[Connection]:
        """Liste les connexions par type."""
        query = self._base_query().filter(Connection.connector_type == connector_type)
        if active_only:
            query = query.filter(Connection.is_active == True)
        return query.all()

    def get_active(self) -> list[Connection]:
        """Liste les connexions actives et connectees."""
        return self._base_query().filter(
            Connection.is_active == True,
            Connection.status == ConnectionStatus.CONNECTED.value
        ).all()

    def get_with_errors(self) -> list[Connection]:
        """Liste les connexions en erreur."""
        return self._base_query().filter(
            Connection.status == ConnectionStatus.ERROR.value
        ).order_by(desc(Connection.last_error_at)).all()

    def autocomplete(self, prefix: str, limit: int = 10) -> list[dict[str, str]]:
        """Autocomplete pour les connexions."""
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
            {
                "id": str(c.id),
                "code": c.code,
                "name": c.name,
                "label": f"[{c.code}] {c.name}",
                "extra": {"connector_type": c.connector_type, "status": c.status.value}
            }
            for c in results
        ]

    def create(self, data: dict[str, Any], created_by: UUID = None) -> Connection:
        """Cree une connexion."""
        # Generer code si non fourni
        if not data.get('code'):
            data['code'] = self._generate_code(data.get('name', 'CONN'))

        entity = Connection(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def _generate_code(self, name: str) -> str:
        """Genere un code unique."""
        import re
        base = re.sub(r'[^A-Z0-9]', '', name.upper()[:10])
        code = base
        counter = 1
        while self.code_exists(code):
            code = f"{base}_{counter}"
            counter += 1
        return code

    def update(self, entity: Connection, data: dict[str, Any], updated_by: UUID = None) -> Connection:
        """Met a jour une connexion."""
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update_status(
        self,
        entity: Connection,
        status: ConnectionStatus,
        error: str = None
    ) -> Connection:
        """Met a jour le statut."""
        entity.status = status
        if status == ConnectionStatus.CONNECTED:
            entity.last_connected_at = datetime.utcnow()
            entity.consecutive_errors = 0
            entity.last_error = None
            entity.health_status = HealthStatus.HEALTHY
        elif status == ConnectionStatus.ERROR:
            entity.consecutive_errors = (entity.consecutive_errors or 0) + 1
            entity.last_error = error
            entity.last_error_at = datetime.utcnow()
            entity.health_status = HealthStatus.UNHEALTHY if entity.consecutive_errors >= 3 else HealthStatus.DEGRADED
        entity.last_health_check = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update_tokens(
        self,
        entity: Connection,
        access_token: str,
        refresh_token: str = None,
        expires_at: datetime = None,
        scope: str = None
    ) -> Connection:
        """Met a jour les tokens OAuth."""
        entity.access_token = access_token
        if refresh_token:
            entity.refresh_token = refresh_token
        if expires_at:
            entity.token_expires_at = expires_at
        if scope:
            entity.token_scope = scope
        entity.status = ConnectionStatus.CONNECTED
        entity.last_connected_at = datetime.utcnow()
        entity.health_status = HealthStatus.HEALTHY
        entity.consecutive_errors = 0
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update_health_metrics(
        self,
        entity: Connection,
        success_rate: float = None,
        avg_response_time: int = None
    ) -> Connection:
        """Met a jour les metriques de sante."""
        if success_rate is not None:
            entity.success_rate_24h = success_rate
        if avg_response_time is not None:
            entity.avg_response_time_ms = avg_response_time
        entity.last_health_check = datetime.utcnow()
        self.db.commit()
        return entity

    def soft_delete(self, entity: Connection, deleted_by: UUID = None) -> bool:
        """Soft delete."""
        entity.is_deleted = True
        entity.is_active = False
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, entity: Connection) -> Connection:
        """Restaure une connexion supprimee."""
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def count_by_status(self) -> dict[str, int]:
        """Compte les connexions par statut."""
        result = self._base_query().with_entities(
            Connection.status,
            func.count(Connection.id)
        ).group_by(Connection.status).all()
        return {r[0].value if hasattr(r[0], 'value') else r[0]: r[1] for r in result}

    def count_by_type(self) -> dict[str, int]:
        """Compte les connexions par type."""
        result = self._base_query().with_entities(
            Connection.connector_type,
            func.count(Connection.id)
        ).group_by(Connection.connector_type).all()
        return {r[0]: r[1] for r in result}


class DataMappingRepository:
    """Repository DataMapping avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(DataMapping).filter(DataMapping.tenant_id == self.tenant_id)

    def get_by_id(self, id: UUID) -> DataMapping | None:
        return self._base_query().filter(DataMapping.id == id).first()

    def get_by_code(self, code: str) -> DataMapping | None:
        return self._base_query().filter(DataMapping.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(DataMapping.code == code.upper())
        if exclude_id:
            query = query.filter(DataMapping.id != exclude_id)
        return query.count() > 0

    def get_by_connection(self, connection_id: UUID, active_only: bool = True) -> list[DataMapping]:
        query = self._base_query().filter(DataMapping.connection_id == connection_id)
        if active_only:
            query = query.filter(DataMapping.is_active == True)
        return query.all()

    def list(
        self,
        connection_id: UUID = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[DataMapping], int]:
        query = self._base_query()
        if connection_id:
            query = query.filter(DataMapping.connection_id == connection_id)
        total = query.count()
        items = query.order_by(desc(DataMapping.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def create(self, data: dict[str, Any], created_by: UUID = None) -> DataMapping:
        if not data.get('code'):
            data['code'] = self._generate_code(data.get('name', 'MAP'))
        entity = DataMapping(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def _generate_code(self, name: str) -> str:
        import re
        base = re.sub(r'[^A-Z0-9]', '', name.upper()[:10])
        code = base
        counter = 1
        while self.code_exists(code):
            code = f"{base}_{counter}"
            counter += 1
        return code

    def update(self, entity: DataMapping, data: dict[str, Any], updated_by: UUID = None) -> DataMapping:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: DataMapping) -> bool:
        self.db.delete(entity)
        self.db.commit()
        return True


class SyncConfigurationRepository:
    """Repository SyncConfiguration avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(SyncConfiguration).filter(SyncConfiguration.tenant_id == self.tenant_id)

    def get_by_id(self, id: UUID) -> SyncConfiguration | None:
        return self._base_query().options(
            joinedload(SyncConfiguration.connection),
            joinedload(SyncConfiguration.mapping)
        ).filter(SyncConfiguration.id == id).first()

    def get_by_code(self, code: str) -> SyncConfiguration | None:
        return self._base_query().filter(SyncConfiguration.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(SyncConfiguration.code == code.upper())
        if exclude_id:
            query = query.filter(SyncConfiguration.id != exclude_id)
        return query.count() > 0

    def get_by_connection(self, connection_id: UUID) -> list[SyncConfiguration]:
        return self._base_query().filter(
            SyncConfiguration.connection_id == connection_id
        ).all()

    def get_pending_scheduled(self) -> list[SyncConfiguration]:
        """Configurations planifiees a executer."""
        now = datetime.utcnow()
        return self._base_query().filter(
            SyncConfiguration.is_active == True,
            SyncConfiguration.is_paused == False,
            SyncConfiguration.sync_mode == 'scheduled',
            or_(
                SyncConfiguration.next_run_at.is_(None),
                SyncConfiguration.next_run_at <= now
            )
        ).all()

    def list(
        self,
        connection_id: UUID = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[SyncConfiguration], int]:
        query = self._base_query()
        if connection_id:
            query = query.filter(SyncConfiguration.connection_id == connection_id)
        total = query.count()
        items = query.order_by(desc(SyncConfiguration.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def create(self, data: dict[str, Any], created_by: UUID = None) -> SyncConfiguration:
        if not data.get('code'):
            data['code'] = self._generate_code(data.get('name', 'SYNC'))
        entity = SyncConfiguration(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def _generate_code(self, name: str) -> str:
        import re
        base = re.sub(r'[^A-Z0-9]', '', name.upper()[:10])
        code = base
        counter = 1
        while self.code_exists(code):
            code = f"{base}_{counter}"
            counter += 1
        return code

    def update(self, entity: SyncConfiguration, data: dict[str, Any], updated_by: UUID = None) -> SyncConfiguration:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update_execution_stats(
        self,
        entity: SyncConfiguration,
        status: SyncStatus,
        records_synced: int = 0
    ) -> SyncConfiguration:
        entity.last_run_at = datetime.utcnow()
        entity.last_run_status = status
        entity.total_executions += 1
        if status == SyncStatus.COMPLETED:
            entity.successful_executions += 1
        elif status == SyncStatus.FAILED:
            entity.failed_executions += 1
        entity.total_records_synced += records_synced
        self.db.commit()
        return entity

    def update_next_run(self, entity: SyncConfiguration, next_run_at: datetime) -> SyncConfiguration:
        entity.next_run_at = next_run_at
        self.db.commit()
        return entity

    def delete(self, entity: SyncConfiguration) -> bool:
        self.db.delete(entity)
        self.db.commit()
        return True


class SyncExecutionRepository:
    """Repository SyncExecution avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(SyncExecution).filter(SyncExecution.tenant_id == self.tenant_id)

    def get_by_id(self, id: UUID) -> SyncExecution | None:
        return self._base_query().options(
            joinedload(SyncExecution.logs),
            joinedload(SyncExecution.conflicts)
        ).filter(SyncExecution.id == id).first()

    def get_running_for_connection(self, connection_id: UUID) -> SyncExecution | None:
        return self._base_query().filter(
            SyncExecution.connection_id == connection_id,
            SyncExecution.status == SyncStatus.RUNNING.value
        ).first()

    def get_running_for_config(self, config_id: UUID) -> SyncExecution | None:
        return self._base_query().filter(
            SyncExecution.config_id == config_id,
            SyncExecution.status == SyncStatus.RUNNING.value
        ).first()

    def list(
        self,
        filters: SyncExecutionFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "started_at",
        sort_dir: str = "desc"
    ) -> tuple[list[SyncExecution], int]:
        query = self._base_query()

        if filters:
            if filters.connection_id:
                query = query.filter(SyncExecution.connection_id == filters.connection_id)
            if filters.config_id:
                query = query.filter(SyncExecution.config_id == filters.config_id)
            if filters.status:
                statuses = [s.value for s in filters.status]
                query = query.filter(SyncExecution.status.in_(statuses))
            if filters.direction:
                query = query.filter(SyncExecution.direction == filters.direction.value)
            if filters.entity_type:
                query = query.filter(SyncExecution.entity_type == filters.entity_type.value)
            if filters.date_from:
                query = query.filter(SyncExecution.started_at >= filters.date_from)
            if filters.date_to:
                query = query.filter(SyncExecution.started_at <= filters.date_to)

        total = query.count()
        sort_col = getattr(SyncExecution, sort_by, SyncExecution.started_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return items, total

    def get_recent(self, limit: int = 10) -> list[SyncExecution]:
        return self._base_query().order_by(
            desc(SyncExecution.started_at)
        ).limit(limit).all()

    def create(self, data: dict[str, Any]) -> SyncExecution:
        # Generer numero d'execution
        today = datetime.utcnow().strftime('%Y%m%d')
        count = self._base_query().filter(
            SyncExecution.execution_number.like(f'EXE-{today}-%')
        ).count()
        data['execution_number'] = f"EXE-{today}-{count + 1:05d}"
        data['started_at'] = datetime.utcnow()

        entity = SyncExecution(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def start(self, execution: SyncExecution) -> SyncExecution:
        execution.status = SyncStatus.RUNNING
        execution.started_at = datetime.utcnow()
        self.db.commit()
        return execution

    def complete(
        self,
        execution: SyncExecution,
        status: SyncStatus,
        stats: dict[str, int] = None
    ) -> SyncExecution:
        execution.status = status
        execution.completed_at = datetime.utcnow()
        if execution.started_at:
            execution.duration_seconds = (
                execution.completed_at - execution.started_at
            ).total_seconds()

        if stats:
            execution.total_records = stats.get('total', 0)
            execution.processed_records = stats.get('processed', 0)
            execution.created_records = stats.get('created', 0)
            execution.updated_records = stats.get('updated', 0)
            execution.deleted_records = stats.get('deleted', 0)
            execution.skipped_records = stats.get('skipped', 0)
            execution.failed_records = stats.get('failed', 0)

        execution.progress_percent = 100.0
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def update_progress(
        self,
        execution: SyncExecution,
        processed: int,
        total: int,
        current_step: str = None
    ) -> SyncExecution:
        execution.processed_records = processed
        execution.total_records = total
        execution.progress_percent = (processed / total * 100) if total > 0 else 0
        if current_step:
            execution.current_step = current_step
        self.db.commit()
        return execution

    def add_error(self, execution: SyncExecution, error: dict[str, Any]) -> SyncExecution:
        errors = list(execution.errors or [])
        errors.append(error)
        execution.errors = errors
        execution.error_count = len(errors)
        execution.last_error = error.get('message', str(error))
        self.db.commit()
        return execution

    def get_stats_for_period(
        self,
        days: int = 7
    ) -> dict[str, Any]:
        since = datetime.utcnow() - timedelta(days=days)
        query = self._base_query().filter(SyncExecution.started_at >= since)

        total = query.count()
        completed = query.filter(SyncExecution.status == SyncStatus.COMPLETED.value).count()
        failed = query.filter(SyncExecution.status == SyncStatus.FAILED.value).count()

        records = query.with_entities(
            func.sum(SyncExecution.processed_records)
        ).scalar() or 0

        return {
            'total_executions': total,
            'completed': completed,
            'failed': failed,
            'success_rate': (completed / total * 100) if total > 0 else 0,
            'records_synced': records
        }


class ExecutionLogRepository:
    """Repository ExecutionLog avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(ExecutionLog).filter(ExecutionLog.tenant_id == self.tenant_id)

    def get_by_execution(
        self,
        execution_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list[ExecutionLog], int]:
        query = self._base_query().filter(ExecutionLog.execution_id == execution_id)
        total = query.count()
        items = query.order_by(desc(ExecutionLog.timestamp)).offset(offset).limit(limit).all()
        return items, total

    def get_errors(self, execution_id: UUID) -> list[ExecutionLog]:
        return self._base_query().filter(
            ExecutionLog.execution_id == execution_id,
            ExecutionLog.level.in_(['error', 'critical'])
        ).order_by(ExecutionLog.timestamp).all()

    def create(self, data: dict[str, Any]) -> ExecutionLog:
        entity = ExecutionLog(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def create_batch(self, logs: list[dict[str, Any]]) -> int:
        for log_data in logs:
            log = ExecutionLog(tenant_id=self.tenant_id, **log_data)
            self.db.add(log)
        self.db.commit()
        return len(logs)


class SyncConflictRepository:
    """Repository SyncConflict avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(SyncConflict).filter(SyncConflict.tenant_id == self.tenant_id)

    def get_by_id(self, id: UUID) -> SyncConflict | None:
        return self._base_query().filter(SyncConflict.id == id).first()

    def get_pending(self, limit: int = 100) -> list[SyncConflict]:
        return self._base_query().filter(
            SyncConflict.is_resolved == False,
            SyncConflict.is_ignored == False
        ).order_by(SyncConflict.created_at).limit(limit).all()

    def get_pending_count(self) -> int:
        return self._base_query().filter(
            SyncConflict.is_resolved == False,
            SyncConflict.is_ignored == False
        ).count()

    def list(
        self,
        filters: ConflictFilters = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[SyncConflict], int]:
        query = self._base_query()

        if filters:
            if filters.execution_id:
                query = query.filter(SyncConflict.execution_id == filters.execution_id)
            if filters.entity_type:
                query = query.filter(SyncConflict.entity_type == filters.entity_type.value)
            if filters.is_resolved is not None:
                query = query.filter(SyncConflict.is_resolved == filters.is_resolved)

        total = query.count()
        items = query.order_by(desc(SyncConflict.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def create(self, data: dict[str, Any]) -> SyncConflict:
        entity = SyncConflict(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def resolve(
        self,
        conflict: SyncConflict,
        resolution: str,
        resolved_data: dict[str, Any],
        resolved_by: UUID,
        notes: str = None
    ) -> SyncConflict:
        conflict.resolution_strategy = resolution
        conflict.resolved_data = resolved_data
        conflict.resolved_at = datetime.utcnow()
        conflict.resolved_by = resolved_by
        conflict.resolution_notes = notes
        conflict.is_resolved = True
        self.db.commit()
        self.db.refresh(conflict)
        return conflict

    def ignore(self, conflict: SyncConflict, resolved_by: UUID) -> SyncConflict:
        conflict.is_ignored = True
        conflict.resolved_at = datetime.utcnow()
        conflict.resolved_by = resolved_by
        self.db.commit()
        return conflict


class WebhookRepository:
    """Repository Webhook avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(Webhook).filter(Webhook.tenant_id == self.tenant_id)

    def get_by_id(self, id: UUID) -> Webhook | None:
        return self._base_query().filter(Webhook.id == id).first()

    def get_by_code(self, code: str) -> Webhook | None:
        return self._base_query().filter(Webhook.code == code.upper()).first()

    def get_by_path(self, endpoint_path: str) -> Webhook | None:
        return self._base_query().filter(
            Webhook.endpoint_path == endpoint_path,
            Webhook.is_active == True
        ).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(Webhook.code == code.upper())
        if exclude_id:
            query = query.filter(Webhook.id != exclude_id)
        return query.count() > 0

    def path_exists(self, endpoint_path: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(Webhook.endpoint_path == endpoint_path)
        if exclude_id:
            query = query.filter(Webhook.id != exclude_id)
        return query.count() > 0

    def get_by_connection(self, connection_id: UUID) -> list[Webhook]:
        return self._base_query().filter(Webhook.connection_id == connection_id).all()

    def get_inbound_active(self) -> list[Webhook]:
        return self._base_query().filter(
            Webhook.direction == WebhookDirection.INBOUND.value,
            Webhook.is_active == True
        ).all()

    def list(
        self,
        connection_id: UUID = None,
        direction: WebhookDirection = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[Webhook], int]:
        query = self._base_query()
        if connection_id:
            query = query.filter(Webhook.connection_id == connection_id)
        if direction:
            query = query.filter(Webhook.direction == direction.value)

        total = query.count()
        items = query.order_by(desc(Webhook.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def create(self, data: dict[str, Any], created_by: UUID = None) -> Webhook:
        if not data.get('code'):
            data['code'] = self._generate_code(data.get('name', 'WH'))

        # Generer path pour webhook entrant
        if data.get('direction') == WebhookDirection.INBOUND.value and not data.get('endpoint_path'):
            import secrets
            data['endpoint_path'] = f"/webhooks/{secrets.token_urlsafe(16)}"
            data['secret_key'] = secrets.token_urlsafe(32)

        entity = Webhook(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def _generate_code(self, name: str) -> str:
        import re
        base = re.sub(r'[^A-Z0-9]', '', name.upper()[:10])
        code = base
        counter = 1
        while self.code_exists(code):
            code = f"{base}_{counter}"
            counter += 1
        return code

    def update(self, entity: Webhook, data: dict[str, Any], updated_by: UUID = None) -> Webhook:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def record_call(
        self,
        webhook: Webhook,
        success: bool,
        error: str = None
    ) -> Webhook:
        webhook.last_triggered_at = datetime.utcnow()
        webhook.total_calls += 1
        if success:
            webhook.successful_calls += 1
        else:
            webhook.failed_calls += 1
            webhook.last_error = error
            webhook.last_error_at = datetime.utcnow()
        self.db.commit()
        return webhook

    def delete(self, entity: Webhook) -> bool:
        self.db.delete(entity)
        self.db.commit()
        return True


class WebhookLogRepository:
    """Repository WebhookLog avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(WebhookLog).filter(WebhookLog.tenant_id == self.tenant_id)

    def get_by_webhook(
        self,
        webhook_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list[WebhookLog], int]:
        query = self._base_query().filter(WebhookLog.webhook_id == webhook_id)
        total = query.count()
        items = query.order_by(desc(WebhookLog.timestamp)).offset(offset).limit(limit).all()
        return items, total

    def create(self, data: dict[str, Any]) -> WebhookLog:
        entity = WebhookLog(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity


class TransformationRuleRepository:
    """Repository TransformationRule avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(TransformationRule).filter(
            TransformationRule.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> TransformationRule | None:
        return self._base_query().filter(TransformationRule.id == id).first()

    def get_by_code(self, code: str) -> TransformationRule | None:
        return self._base_query().filter(TransformationRule.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(TransformationRule.code == code.upper())
        if exclude_id:
            query = query.filter(TransformationRule.id != exclude_id)
        return query.count() > 0

    def list(self, active_only: bool = True) -> list[TransformationRule]:
        query = self._base_query()
        if active_only:
            query = query.filter(TransformationRule.is_active == True)
        return query.order_by(TransformationRule.name).all()

    def create(self, data: dict[str, Any], created_by: UUID = None) -> TransformationRule:
        entity = TransformationRule(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(
        self,
        entity: TransformationRule,
        data: dict[str, Any],
        updated_by: UUID = None
    ) -> TransformationRule:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: TransformationRule) -> bool:
        if entity.is_system:
            return False
        self.db.delete(entity)
        self.db.commit()
        return True


class IntegrationDashboardRepository:
    """Repository IntegrationDashboard avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(IntegrationDashboard).filter(
            IntegrationDashboard.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> IntegrationDashboard | None:
        return self._base_query().filter(IntegrationDashboard.id == id).first()

    def get_default(self) -> IntegrationDashboard | None:
        return self._base_query().filter(IntegrationDashboard.is_default == True).first()

    def list(self, owner_id: UUID = None) -> list[IntegrationDashboard]:
        query = self._base_query().filter(IntegrationDashboard.is_active == True)
        if owner_id:
            query = query.filter(IntegrationDashboard.owner_id == owner_id)
        return query.order_by(IntegrationDashboard.name).all()

    def create(self, data: dict[str, Any], owner_id: UUID) -> IntegrationDashboard:
        entity = IntegrationDashboard(
            tenant_id=self.tenant_id,
            owner_id=owner_id,
            created_by=owner_id,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(
        self,
        entity: IntegrationDashboard,
        data: dict[str, Any],
        updated_by: UUID = None
    ) -> IntegrationDashboard:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: IntegrationDashboard) -> bool:
        self.db.delete(entity)
        self.db.commit()
        return True
