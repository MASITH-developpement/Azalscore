"""
AZALS - Module DataExchange - Repository
=========================================
Acces aux donnees avec isolation tenant automatique.

CRITIQUE: Toutes les requetes filtrees par tenant_id.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session, joinedload

from .models import (
    ExchangeProfile, FieldMapping, ValidationRule, Transformation,
    FileConnector, ScheduledExchange, ExchangeJob, ExchangeLog,
    ExchangeError, ExchangeHistory, NotificationConfig, LookupTable,
    ExchangeStatus
)
from .schemas import ProfileFilters, ConnectorFilters, JobFilters, HistoryFilters


class ExchangeProfileRepository:
    """Repository pour les profils d'import/export."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(ExchangeProfile).filter(
            ExchangeProfile.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(ExchangeProfile.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[ExchangeProfile]:
        return self._base_query().options(
            joinedload(ExchangeProfile.field_mappings),
            joinedload(ExchangeProfile.validations),
            joinedload(ExchangeProfile.transformations)
        ).filter(ExchangeProfile.id == id).first()

    def get_by_code(self, code: str) -> Optional[ExchangeProfile]:
        return self._base_query().filter(
            ExchangeProfile.code == code.upper()
        ).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(ExchangeProfile.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(ExchangeProfile.code == code.upper())
        if exclude_id:
            query = query.filter(ExchangeProfile.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: ProfileFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[ExchangeProfile], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    ExchangeProfile.name.ilike(term),
                    ExchangeProfile.code.ilike(term),
                    ExchangeProfile.description.ilike(term)
                ))
            if filters.exchange_type:
                query = query.filter(ExchangeProfile.exchange_type == filters.exchange_type.value)
            if filters.file_format:
                query = query.filter(ExchangeProfile.file_format == filters.file_format.value)
            if filters.entity_type:
                query = query.filter(ExchangeProfile.entity_type == filters.entity_type.value)
            if filters.is_active is not None:
                query = query.filter(ExchangeProfile.is_active == filters.is_active)

        total = query.count()
        sort_col = getattr(ExchangeProfile, sort_by, ExchangeProfile.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, str]]:
        if len(prefix) < 2:
            return []
        query = self._base_query().filter(
            ExchangeProfile.is_active == True
        ).filter(or_(
            ExchangeProfile.name.ilike(f"{prefix}%"),
            ExchangeProfile.code.ilike(f"{prefix}%")
        ))
        results = query.order_by(ExchangeProfile.name).limit(limit).all()
        return [
            {
                "id": str(p.id),
                "code": p.code,
                "name": p.name,
                "label": f"[{p.code}] {p.name}"
            }
            for p in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ExchangeProfile:
        # Extraire les mappings, validations et transformations
        field_mappings_data = data.pop("field_mappings", [])
        validation_rules_data = data.pop("validation_rules", [])
        transformations_data = data.pop("transformations", [])

        # Creer le profil
        profile = ExchangeProfile(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(profile)
        self.db.flush()

        # Creer les mappings
        for mapping_data in field_mappings_data:
            mapping = FieldMapping(
                tenant_id=self.tenant_id,
                profile_id=profile.id,
                **mapping_data
            )
            self.db.add(mapping)

        # Creer les regles de validation
        for rule_data in validation_rules_data:
            rule = ValidationRule(
                tenant_id=self.tenant_id,
                profile_id=profile.id,
                **rule_data
            )
            self.db.add(rule)

        # Creer les transformations
        for transform_data in transformations_data:
            transform = Transformation(
                tenant_id=self.tenant_id,
                profile_id=profile.id,
                **transform_data
            )
            self.db.add(transform)

        self.db.commit()
        self.db.refresh(profile)
        return profile

    def update(
        self,
        profile: ExchangeProfile,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> ExchangeProfile:
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        profile.updated_by = updated_by
        profile.version += 1
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def soft_delete(self, profile: ExchangeProfile, deleted_by: UUID = None) -> bool:
        profile.is_deleted = True
        profile.deleted_at = datetime.utcnow()
        profile.deleted_by = deleted_by
        profile.is_active = False
        self.db.commit()
        return True

    def restore(self, profile: ExchangeProfile) -> ExchangeProfile:
        profile.is_deleted = False
        profile.deleted_at = None
        profile.deleted_by = None
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_usage_count(self, profile_id: UUID) -> int:
        """Compte le nombre d'utilisations du profil."""
        scheduled_count = self.db.query(ScheduledExchange).filter(
            ScheduledExchange.tenant_id == self.tenant_id,
            ScheduledExchange.profile_id == profile_id,
            ScheduledExchange.is_deleted == False
        ).count()

        job_count = self.db.query(ExchangeJob).filter(
            ExchangeJob.tenant_id == self.tenant_id,
            ExchangeJob.profile_id == profile_id
        ).count()

        return scheduled_count + job_count


class FieldMappingRepository:
    """Repository pour les mappings de champs."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(FieldMapping).filter(
            FieldMapping.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[FieldMapping]:
        return self._base_query().filter(FieldMapping.id == id).first()

    def get_by_profile(self, profile_id: UUID) -> List[FieldMapping]:
        return self._base_query().filter(
            FieldMapping.profile_id == profile_id
        ).order_by(FieldMapping.sort_order).all()

    def create(self, data: Dict[str, Any], profile_id: UUID) -> FieldMapping:
        mapping = FieldMapping(
            tenant_id=self.tenant_id,
            profile_id=profile_id,
            **data
        )
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def update(self, mapping: FieldMapping, data: Dict[str, Any]) -> FieldMapping:
        for key, value in data.items():
            if hasattr(mapping, key):
                setattr(mapping, key, value)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def delete(self, mapping: FieldMapping) -> bool:
        self.db.delete(mapping)
        self.db.commit()
        return True

    def bulk_update(self, profile_id: UUID, mappings: List[Dict[str, Any]]) -> List[FieldMapping]:
        """Remplace tous les mappings d'un profil."""
        # Supprimer les anciens
        self._base_query().filter(FieldMapping.profile_id == profile_id).delete()

        # Creer les nouveaux
        result = []
        for mapping_data in mappings:
            mapping = FieldMapping(
                tenant_id=self.tenant_id,
                profile_id=profile_id,
                **mapping_data
            )
            self.db.add(mapping)
            result.append(mapping)

        self.db.commit()
        for m in result:
            self.db.refresh(m)
        return result


class ValidationRuleRepository:
    """Repository pour les regles de validation."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(ValidationRule).filter(
            ValidationRule.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[ValidationRule]:
        return self._base_query().filter(ValidationRule.id == id).first()

    def get_by_profile(self, profile_id: UUID, active_only: bool = True) -> List[ValidationRule]:
        query = self._base_query().filter(ValidationRule.profile_id == profile_id)
        if active_only:
            query = query.filter(ValidationRule.is_active == True)
        return query.order_by(ValidationRule.sort_order).all()

    def create(self, data: Dict[str, Any], profile_id: UUID) -> ValidationRule:
        rule = ValidationRule(
            tenant_id=self.tenant_id,
            profile_id=profile_id,
            **data
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def update(self, rule: ValidationRule, data: Dict[str, Any]) -> ValidationRule:
        for key, value in data.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete(self, rule: ValidationRule) -> bool:
        self.db.delete(rule)
        self.db.commit()
        return True


class TransformationRepository:
    """Repository pour les transformations."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Transformation).filter(
            Transformation.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[Transformation]:
        return self._base_query().filter(Transformation.id == id).first()

    def get_by_profile(self, profile_id: UUID, active_only: bool = True) -> List[Transformation]:
        query = self._base_query().filter(Transformation.profile_id == profile_id)
        if active_only:
            query = query.filter(Transformation.is_active == True)
        return query.order_by(Transformation.sort_order).all()

    def create(self, data: Dict[str, Any], profile_id: UUID) -> Transformation:
        transform = Transformation(
            tenant_id=self.tenant_id,
            profile_id=profile_id,
            **data
        )
        self.db.add(transform)
        self.db.commit()
        self.db.refresh(transform)
        return transform

    def update(self, transform: Transformation, data: Dict[str, Any]) -> Transformation:
        for key, value in data.items():
            if hasattr(transform, key):
                setattr(transform, key, value)
        self.db.commit()
        self.db.refresh(transform)
        return transform

    def delete(self, transform: Transformation) -> bool:
        self.db.delete(transform)
        self.db.commit()
        return True


class FileConnectorRepository:
    """Repository pour les connecteurs de fichiers."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(FileConnector).filter(
            FileConnector.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(FileConnector.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[FileConnector]:
        return self._base_query().filter(FileConnector.id == id).first()

    def get_by_code(self, code: str) -> Optional[FileConnector]:
        return self._base_query().filter(
            FileConnector.code == code.upper()
        ).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(FileConnector.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(FileConnector.code == code.upper())
        if exclude_id:
            query = query.filter(FileConnector.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: ConnectorFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[FileConnector], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    FileConnector.name.ilike(term),
                    FileConnector.code.ilike(term),
                    FileConnector.description.ilike(term)
                ))
            if filters.connector_type:
                query = query.filter(FileConnector.connector_type == filters.connector_type.value)
            if filters.is_active is not None:
                query = query.filter(FileConnector.is_active == filters.is_active)

        total = query.count()
        sort_col = getattr(FileConnector, sort_by, FileConnector.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, str]]:
        if len(prefix) < 2:
            return []
        query = self._base_query().filter(
            FileConnector.is_active == True
        ).filter(or_(
            FileConnector.name.ilike(f"{prefix}%"),
            FileConnector.code.ilike(f"{prefix}%")
        ))
        results = query.order_by(FileConnector.name).limit(limit).all()
        return [
            {
                "id": str(c.id),
                "code": c.code,
                "name": c.name,
                "label": f"[{c.code}] {c.name}"
            }
            for c in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> FileConnector:
        connector = FileConnector(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(connector)
        self.db.commit()
        self.db.refresh(connector)
        return connector

    def update(
        self,
        connector: FileConnector,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> FileConnector:
        for key, value in data.items():
            if hasattr(connector, key):
                setattr(connector, key, value)
        connector.updated_by = updated_by
        connector.version += 1
        self.db.commit()
        self.db.refresh(connector)
        return connector

    def update_status(
        self,
        connector: FileConnector,
        connected: bool,
        error: str = None
    ) -> FileConnector:
        connector.last_connected_at = datetime.utcnow() if connected else connector.last_connected_at
        connector.last_error = error
        if connected:
            connector.consecutive_errors = 0
        else:
            connector.consecutive_errors = (connector.consecutive_errors or 0) + 1
        self.db.commit()
        self.db.refresh(connector)
        return connector

    def soft_delete(self, connector: FileConnector, deleted_by: UUID = None) -> bool:
        connector.is_deleted = True
        connector.deleted_at = datetime.utcnow()
        connector.deleted_by = deleted_by
        connector.is_active = False
        self.db.commit()
        return True

    def get_usage_count(self, connector_id: UUID) -> int:
        return self.db.query(ScheduledExchange).filter(
            ScheduledExchange.tenant_id == self.tenant_id,
            ScheduledExchange.connector_id == connector_id,
            ScheduledExchange.is_deleted == False
        ).count()


class ScheduledExchangeRepository:
    """Repository pour les echanges planifies."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(ScheduledExchange).filter(
            ScheduledExchange.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(ScheduledExchange.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[ScheduledExchange]:
        return self._base_query().options(
            joinedload(ScheduledExchange.profile),
            joinedload(ScheduledExchange.connector)
        ).filter(ScheduledExchange.id == id).first()

    def get_by_code(self, code: str) -> Optional[ScheduledExchange]:
        return self._base_query().filter(
            ScheduledExchange.code == code.upper()
        ).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(ScheduledExchange.code == code.upper())
        if exclude_id:
            query = query.filter(ScheduledExchange.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        is_active: bool = None
    ) -> Tuple[List[ScheduledExchange], int]:
        query = self._base_query()

        if is_active is not None:
            query = query.filter(ScheduledExchange.is_active == is_active)

        total = query.count()
        sort_col = getattr(ScheduledExchange, sort_by, ScheduledExchange.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_due_for_execution(self) -> List[ScheduledExchange]:
        """Recupere les echanges planifies a executer."""
        now = datetime.utcnow()
        return self._base_query().filter(
            ScheduledExchange.is_active == True,
            or_(
                ScheduledExchange.next_run_at.is_(None),
                ScheduledExchange.next_run_at <= now
            )
        ).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ScheduledExchange:
        scheduled = ScheduledExchange(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(scheduled)
        self.db.commit()
        self.db.refresh(scheduled)
        return scheduled

    def update(
        self,
        scheduled: ScheduledExchange,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> ScheduledExchange:
        for key, value in data.items():
            if hasattr(scheduled, key):
                setattr(scheduled, key, value)
        scheduled.updated_by = updated_by
        scheduled.version += 1
        self.db.commit()
        self.db.refresh(scheduled)
        return scheduled

    def record_execution(
        self,
        scheduled: ScheduledExchange,
        status: str,
        next_run_at: datetime = None
    ) -> ScheduledExchange:
        scheduled.last_run_at = datetime.utcnow()
        scheduled.last_run_status = status
        scheduled.run_count = (scheduled.run_count or 0) + 1

        if status == "failed":
            scheduled.failure_count = (scheduled.failure_count or 0) + 1
            scheduled.consecutive_failures = (scheduled.consecutive_failures or 0) + 1

            # Pause si trop d'echecs consecutifs
            if scheduled.consecutive_failures >= scheduled.pause_on_consecutive_failures:
                scheduled.is_active = False
        else:
            scheduled.consecutive_failures = 0

        if next_run_at:
            scheduled.next_run_at = next_run_at

        self.db.commit()
        self.db.refresh(scheduled)
        return scheduled

    def soft_delete(self, scheduled: ScheduledExchange, deleted_by: UUID = None) -> bool:
        scheduled.is_deleted = True
        scheduled.deleted_at = datetime.utcnow()
        scheduled.deleted_by = deleted_by
        scheduled.is_active = False
        self.db.commit()
        return True


class ExchangeJobRepository:
    """Repository pour les jobs d'echange."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(ExchangeJob).filter(
            ExchangeJob.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[ExchangeJob]:
        return self._base_query().options(
            joinedload(ExchangeJob.profile),
            joinedload(ExchangeJob.logs),
            joinedload(ExchangeJob.errors)
        ).filter(ExchangeJob.id == id).first()

    def get_by_reference(self, reference: str) -> Optional[ExchangeJob]:
        return self._base_query().filter(
            ExchangeJob.reference == reference
        ).first()

    def list(
        self,
        filters: JobFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[ExchangeJob], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    ExchangeJob.reference.ilike(term),
                    ExchangeJob.file_name.ilike(term)
                ))
            if filters.exchange_type:
                query = query.filter(ExchangeJob.exchange_type == filters.exchange_type.value)
            if filters.status:
                query = query.filter(ExchangeJob.status.in_([s.value for s in filters.status]))
            if filters.profile_id:
                query = query.filter(ExchangeJob.profile_id == filters.profile_id)
            if filters.triggered_by:
                query = query.filter(ExchangeJob.triggered_by == filters.triggered_by)
            if filters.date_from:
                query = query.filter(ExchangeJob.created_at >= filters.date_from)
            if filters.date_to:
                query = query.filter(ExchangeJob.created_at <= filters.date_to)

        total = query.count()
        sort_col = getattr(ExchangeJob, sort_by, ExchangeJob.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_running_jobs(self) -> List[ExchangeJob]:
        return self._base_query().filter(
            ExchangeJob.status.in_(["pending", "validating", "processing"])
        ).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ExchangeJob:
        job = ExchangeJob(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update(self, job: ExchangeJob, data: Dict[str, Any]) -> ExchangeJob:
        for key, value in data.items():
            if hasattr(job, key):
                setattr(job, key, value)
        job.version += 1
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_progress(
        self,
        job: ExchangeJob,
        processed: int,
        created: int = 0,
        updated: int = 0,
        skipped: int = 0,
        errors: int = 0,
        phase: str = None
    ) -> ExchangeJob:
        job.processed_rows = processed
        job.created_count = created
        job.updated_count = updated
        job.skipped_count = skipped
        job.error_count = errors
        if job.total_rows > 0:
            job.progress_percent = (processed / job.total_rows) * 100
        if phase:
            job.current_phase = phase
        self.db.commit()
        return job

    def start(self, job: ExchangeJob) -> ExchangeJob:
        job.status = ExchangeStatus.PROCESSING.value
        job.started_at = datetime.utcnow()
        job.current_phase = "processing"
        self.db.commit()
        self.db.refresh(job)
        return job

    def complete(self, job: ExchangeJob, status: ExchangeStatus) -> ExchangeJob:
        job.status = status.value
        job.completed_at = datetime.utcnow()
        if job.started_at:
            job.duration_seconds = int((job.completed_at - job.started_at).total_seconds())
        job.current_phase = None
        job.progress_percent = 100
        self.db.commit()
        self.db.refresh(job)
        return job

    def fail(self, job: ExchangeJob, error_message: str, error_details: Dict = None) -> ExchangeJob:
        job.status = ExchangeStatus.FAILED.value
        job.completed_at = datetime.utcnow()
        job.error_message = error_message
        job.error_details = error_details or {}
        if job.started_at:
            job.duration_seconds = int((job.completed_at - job.started_at).total_seconds())
        self.db.commit()
        self.db.refresh(job)
        return job

    def rollback(self, job: ExchangeJob, rolled_back_by: UUID = None) -> ExchangeJob:
        job.status = ExchangeStatus.ROLLED_BACK.value
        job.rolled_back_at = datetime.utcnow()
        job.rolled_back_by = rolled_back_by
        self.db.commit()
        self.db.refresh(job)
        return job


class ExchangeLogRepository:
    """Repository pour les logs d'echange."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(ExchangeLog).filter(
            ExchangeLog.tenant_id == self.tenant_id
        )

    def get_by_job(
        self,
        job_id: UUID,
        limit: int = 100,
        offset: int = 0,
        action_filter: str = None
    ) -> Tuple[List[ExchangeLog], int]:
        query = self._base_query().filter(ExchangeLog.job_id == job_id)

        if action_filter:
            query = query.filter(ExchangeLog.action == action_filter)

        total = query.count()
        items = query.order_by(ExchangeLog.row_number).offset(offset).limit(limit).all()
        return items, total

    def create(self, data: Dict[str, Any]) -> ExchangeLog:
        log = ExchangeLog(tenant_id=self.tenant_id, **data)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def create_batch(self, logs: List[Dict[str, Any]]) -> int:
        for log_data in logs:
            log = ExchangeLog(tenant_id=self.tenant_id, **log_data)
            self.db.add(log)
        self.db.commit()
        return len(logs)

    def get_summary(self, job_id: UUID) -> Dict[str, int]:
        results = self.db.query(
            ExchangeLog.action,
            func.count(ExchangeLog.id)
        ).filter(
            ExchangeLog.tenant_id == self.tenant_id,
            ExchangeLog.job_id == job_id
        ).group_by(ExchangeLog.action).all()

        return {action: count for action, count in results}


class ExchangeErrorRepository:
    """Repository pour les erreurs d'echange."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(ExchangeError).filter(
            ExchangeError.tenant_id == self.tenant_id
        )

    def get_by_job(
        self,
        job_id: UUID,
        limit: int = 100,
        offset: int = 0,
        severity_filter: str = None
    ) -> Tuple[List[ExchangeError], int]:
        query = self._base_query().filter(ExchangeError.job_id == job_id)

        if severity_filter:
            query = query.filter(ExchangeError.severity == severity_filter)

        total = query.count()
        items = query.order_by(ExchangeError.row_number).offset(offset).limit(limit).all()
        return items, total

    def create(self, data: Dict[str, Any]) -> ExchangeError:
        error = ExchangeError(tenant_id=self.tenant_id, **data)
        self.db.add(error)
        self.db.commit()
        self.db.refresh(error)
        return error

    def create_batch(self, errors: List[Dict[str, Any]]) -> int:
        for error_data in errors:
            error = ExchangeError(tenant_id=self.tenant_id, **error_data)
            self.db.add(error)
        self.db.commit()
        return len(errors)

    def get_summary(self, job_id: UUID) -> Dict[str, int]:
        results = self.db.query(
            ExchangeError.severity,
            func.count(ExchangeError.id)
        ).filter(
            ExchangeError.tenant_id == self.tenant_id,
            ExchangeError.job_id == job_id
        ).group_by(ExchangeError.severity).all()

        return {severity: count for severity, count in results}


class ExchangeHistoryRepository:
    """Repository pour l'historique des echanges."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(ExchangeHistory).filter(
            ExchangeHistory.tenant_id == self.tenant_id
        )

    def list(
        self,
        filters: HistoryFilters = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ExchangeHistory], int]:
        query = self._base_query()

        if filters:
            if filters.exchange_type:
                query = query.filter(ExchangeHistory.exchange_type == filters.exchange_type.value)
            if filters.entity_type:
                query = query.filter(ExchangeHistory.entity_type == filters.entity_type)
            if filters.status:
                query = query.filter(ExchangeHistory.status == filters.status.value)
            if filters.date_from:
                query = query.filter(ExchangeHistory.created_at >= filters.date_from)
            if filters.date_to:
                query = query.filter(ExchangeHistory.created_at <= filters.date_to)

        total = query.count()
        items = query.order_by(desc(ExchangeHistory.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def create(self, data: Dict[str, Any]) -> ExchangeHistory:
        history = ExchangeHistory(tenant_id=self.tenant_id, **data)
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def get_stats(self, days: int = 30) -> Dict[str, Any]:
        """Statistiques sur une periode."""
        since = datetime.utcnow() - timedelta(days=days)

        query = self._base_query().filter(ExchangeHistory.created_at >= since)

        total = query.count()
        by_type = dict(query.with_entities(
            ExchangeHistory.exchange_type,
            func.count(ExchangeHistory.id)
        ).group_by(ExchangeHistory.exchange_type).all())

        by_status = dict(query.with_entities(
            ExchangeHistory.status,
            func.count(ExchangeHistory.id)
        ).group_by(ExchangeHistory.status).all())

        total_records = query.with_entities(
            func.sum(ExchangeHistory.total_rows)
        ).scalar() or 0

        return {
            "total_exchanges": total,
            "by_type": by_type,
            "by_status": by_status,
            "total_records": total_records
        }


class NotificationConfigRepository:
    """Repository pour les configurations de notification."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(NotificationConfig).filter(
            NotificationConfig.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(NotificationConfig.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[NotificationConfig]:
        return self._base_query().filter(NotificationConfig.id == id).first()

    def get_by_code(self, code: str) -> Optional[NotificationConfig]:
        return self._base_query().filter(
            NotificationConfig.code == code.upper()
        ).first()

    def list(self, is_active: bool = None) -> List[NotificationConfig]:
        query = self._base_query()
        if is_active is not None:
            query = query.filter(NotificationConfig.is_active == is_active)
        return query.order_by(NotificationConfig.name).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> NotificationConfig:
        config = NotificationConfig(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def update(
        self,
        config: NotificationConfig,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> NotificationConfig:
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        config.updated_by = updated_by
        self.db.commit()
        self.db.refresh(config)
        return config

    def soft_delete(self, config: NotificationConfig, deleted_by: UUID = None) -> bool:
        config.is_deleted = True
        config.deleted_at = datetime.utcnow()
        config.is_active = False
        self.db.commit()
        return True


class LookupTableRepository:
    """Repository pour les tables de correspondance."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(LookupTable).filter(
            LookupTable.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(LookupTable.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[LookupTable]:
        return self._base_query().filter(LookupTable.id == id).first()

    def get_by_code(self, code: str) -> Optional[LookupTable]:
        return self._base_query().filter(
            LookupTable.code == code.upper()
        ).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(LookupTable.code == code.upper())
        if exclude_id:
            query = query.filter(LookupTable.id != exclude_id)
        return query.count() > 0

    def list(self, is_active: bool = None) -> List[LookupTable]:
        query = self._base_query()
        if is_active is not None:
            query = query.filter(LookupTable.is_active == is_active)
        return query.order_by(LookupTable.name).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> LookupTable:
        lookup = LookupTable(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(lookup)
        self.db.commit()
        self.db.refresh(lookup)
        return lookup

    def update(
        self,
        lookup: LookupTable,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> LookupTable:
        for key, value in data.items():
            if hasattr(lookup, key):
                setattr(lookup, key, value)
        lookup.updated_by = updated_by
        lookup.version += 1
        self.db.commit()
        self.db.refresh(lookup)
        return lookup

    def soft_delete(self, lookup: LookupTable, deleted_by: UUID = None) -> bool:
        lookup.is_deleted = True
        lookup.deleted_at = datetime.utcnow()
        lookup.is_active = False
        self.db.commit()
        return True

    def lookup_value(self, code: str, source_value: str) -> Optional[str]:
        """Recherche une valeur dans une table de correspondance."""
        lookup = self.get_by_code(code)
        if not lookup or not lookup.is_active:
            return None

        entries = lookup.entries or {}

        if lookup.case_sensitive:
            return entries.get(source_value, lookup.default_value)
        else:
            source_lower = source_value.lower()
            for key, value in entries.items():
                if key.lower() == source_lower:
                    return value
            return lookup.default_value
