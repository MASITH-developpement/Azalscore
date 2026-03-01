"""
AZALS MODULE STORAGE - Repository
==================================

Repositories SQLAlchemy pour le module Storage / Gestion de Fichiers.
Conforme aux normes AZALSCORE (isolation tenant, type hints).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session

from .models import (
    StorageFile,
    FileVersionHistory,
    ChunkedUpload,
    ChunkPart,
    StorageQuota,
    BulkOperation,
    StorageBackend,
    FileStatus,
    UploadStatus,
    AccessLevel,
    ScanStatus,
)


class StorageFileRepository:
    """Repository pour les fichiers stockes."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(StorageFile).filter(
            StorageFile.tenant_id == self.tenant_id
        )

    def get_by_id(self, file_id: UUID) -> Optional[StorageFile]:
        """Recupere un fichier par ID."""
        return self._base_query().filter(StorageFile.id == file_id).first()

    def get_by_checksum(self, checksum_sha256: str) -> Optional[StorageFile]:
        """Recupere un fichier par checksum (deduplication)."""
        return self._base_query().filter(
            StorageFile.checksum_sha256 == checksum_sha256,
            StorageFile.status == FileStatus.ACTIVE
        ).first()

    def list(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        status: Optional[FileStatus] = None,
        mime_type: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[StorageFile], int]:
        """Liste les fichiers avec filtres."""
        query = self._base_query()

        if entity_type:
            query = query.filter(StorageFile.entity_type == entity_type)
        if entity_id:
            query = query.filter(StorageFile.entity_id == entity_id)
        if status:
            query = query.filter(StorageFile.status == status)
        if mime_type:
            query = query.filter(StorageFile.mime_type.ilike(f"{mime_type}%"))
        if search:
            query = query.filter(
                or_(
                    StorageFile.filename.ilike(f"%{search}%"),
                    StorageFile.original_filename.ilike(f"%{search}%")
                )
            )

        total = query.count()
        items = query.order_by(desc(StorageFile.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def get_for_entity(self, entity_type: str, entity_id: UUID) -> List[StorageFile]:
        """Recupere tous les fichiers d'une entite."""
        return self._base_query().filter(
            StorageFile.entity_type == entity_type,
            StorageFile.entity_id == entity_id,
            StorageFile.status == FileStatus.ACTIVE,
            StorageFile.is_latest == True
        ).order_by(StorageFile.created_at).all()

    def get_pending_scan(self, limit: int = 100) -> List[StorageFile]:
        """Recupere les fichiers en attente de scan."""
        return self._base_query().filter(
            StorageFile.scan_status == ScanStatus.PENDING,
            StorageFile.status == FileStatus.ACTIVE
        ).limit(limit).all()

    def get_expired(self) -> List[StorageFile]:
        """Recupere les fichiers expires."""
        return self._base_query().filter(
            StorageFile.expires_at <= datetime.utcnow(),
            StorageFile.status == FileStatus.ACTIVE
        ).all()

    def create(self, data: Dict[str, Any]) -> StorageFile:
        """Cree un nouveau fichier."""
        file = StorageFile(tenant_id=self.tenant_id, **data)
        self.db.add(file)
        self.db.commit()
        self.db.refresh(file)
        return file

    def update(self, file: StorageFile, data: Dict[str, Any]) -> StorageFile:
        """Met a jour un fichier."""
        for key, value in data.items():
            if hasattr(file, key) and value is not None:
                setattr(file, key, value)
        file.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(file)
        return file

    def update_scan_status(
        self,
        file: StorageFile,
        status: ScanStatus,
        result: Optional[str] = None
    ) -> StorageFile:
        """Met a jour le statut de scan."""
        file.scan_status = status
        if result:
            file.scan_result = result
        if status == ScanStatus.INFECTED:
            file.status = FileStatus.QUARANTINED
        file.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(file)
        return file

    def archive(self, file: StorageFile) -> StorageFile:
        """Archive un fichier."""
        file.status = FileStatus.ARCHIVED
        file.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(file)
        return file

    def soft_delete(self, file: StorageFile) -> StorageFile:
        """Suppression logique."""
        file.status = FileStatus.DELETED
        file.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(file)
        return file

    def hard_delete(self, file: StorageFile) -> None:
        """Suppression definitive."""
        self.db.delete(file)
        self.db.commit()

    def record_access(self, file: StorageFile) -> StorageFile:
        """Enregistre un acces."""
        file.accessed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(file)
        return file


class FileVersionHistoryRepository:
    """Repository pour l'historique des versions."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(FileVersionHistory).filter(
            FileVersionHistory.tenant_id == self.tenant_id
        )

    def get_by_file(self, file_id: UUID) -> List[FileVersionHistory]:
        """Recupere l'historique d'un fichier."""
        return self._base_query().filter(
            FileVersionHistory.file_id == file_id
        ).order_by(desc(FileVersionHistory.version_number)).all()

    def get_version(self, file_id: UUID, version_number: int) -> Optional[FileVersionHistory]:
        """Recupere une version specifique."""
        return self._base_query().filter(
            FileVersionHistory.file_id == file_id,
            FileVersionHistory.version_number == version_number
        ).first()

    def create(self, data: Dict[str, Any]) -> FileVersionHistory:
        """Cree une nouvelle version."""
        version = FileVersionHistory(tenant_id=self.tenant_id, **data)
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version


class ChunkedUploadRepository:
    """Repository pour les uploads chunked."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(ChunkedUpload).filter(
            ChunkedUpload.tenant_id == self.tenant_id
        )

    def get_by_id(self, upload_id: UUID) -> Optional[ChunkedUpload]:
        """Recupere un upload par ID."""
        return self._base_query().filter(ChunkedUpload.id == upload_id).first()

    def get_expired(self) -> List[ChunkedUpload]:
        """Recupere les uploads expires."""
        return self._base_query().filter(
            ChunkedUpload.expires_at <= datetime.utcnow(),
            ChunkedUpload.status.in_([UploadStatus.INITIATED, UploadStatus.IN_PROGRESS])
        ).all()

    def create(self, data: Dict[str, Any]) -> ChunkedUpload:
        """Cree un nouvel upload."""
        upload = ChunkedUpload(tenant_id=self.tenant_id, **data)
        self.db.add(upload)
        self.db.commit()
        self.db.refresh(upload)
        return upload

    def update_status(self, upload: ChunkedUpload, status: UploadStatus) -> ChunkedUpload:
        """Met a jour le statut."""
        upload.status = status
        if status == UploadStatus.COMPLETED:
            upload.completed_at = datetime.utcnow()
        upload.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(upload)
        return upload

    def delete(self, upload: ChunkedUpload) -> None:
        """Supprime un upload."""
        self.db.delete(upload)
        self.db.commit()


class ChunkPartRepository:
    """Repository pour les parties d'upload."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(ChunkPart).filter(
            ChunkPart.tenant_id == self.tenant_id
        )

    def get_by_upload(self, upload_id: UUID) -> List[ChunkPart]:
        """Recupere les parties d'un upload."""
        return self._base_query().filter(
            ChunkPart.upload_id == upload_id
        ).order_by(ChunkPart.chunk_number).all()

    def get_chunk(self, upload_id: UUID, chunk_number: int) -> Optional[ChunkPart]:
        """Recupere une partie specifique."""
        return self._base_query().filter(
            ChunkPart.upload_id == upload_id,
            ChunkPart.chunk_number == chunk_number
        ).first()

    def count_chunks(self, upload_id: UUID) -> int:
        """Compte les parties uploadees."""
        return self._base_query().filter(ChunkPart.upload_id == upload_id).count()

    def create(self, data: Dict[str, Any]) -> ChunkPart:
        """Cree une nouvelle partie."""
        chunk = ChunkPart(tenant_id=self.tenant_id, **data)
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk


class StorageQuotaRepository:
    """Repository pour les quotas de stockage."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def get(self) -> Optional[StorageQuota]:
        """Recupere le quota du tenant."""
        return self.db.query(StorageQuota).filter(
            StorageQuota.tenant_id == self.tenant_id
        ).first()

    def get_or_create(self) -> StorageQuota:
        """Recupere ou cree le quota."""
        quota = self.get()
        if not quota:
            quota = StorageQuota(tenant_id=self.tenant_id)
            self.db.add(quota)
            self.db.commit()
            self.db.refresh(quota)
        return quota

    def update(self, quota: StorageQuota, data: Dict[str, Any]) -> StorageQuota:
        """Met a jour le quota."""
        for key, value in data.items():
            if hasattr(quota, key) and value is not None:
                setattr(quota, key, value)
        quota.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(quota)
        return quota

    def add_usage(self, size: int) -> StorageQuota:
        """Ajoute de l'utilisation."""
        quota = self.get_or_create()
        quota.used_storage_bytes += size
        quota.file_count += 1
        quota.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(quota)
        return quota

    def remove_usage(self, size: int) -> StorageQuota:
        """Retire de l'utilisation."""
        quota = self.get_or_create()
        quota.used_storage_bytes = max(0, quota.used_storage_bytes - size)
        quota.file_count = max(0, quota.file_count - 1)
        quota.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(quota)
        return quota

    def check_quota(self, additional_size: int) -> bool:
        """Verifie si le quota permet l'ajout."""
        quota = self.get_or_create()
        return (quota.used_storage_bytes + additional_size) <= quota.max_storage_bytes


class BulkOperationRepository:
    """Repository pour les operations en masse."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(BulkOperation).filter(
            BulkOperation.tenant_id == self.tenant_id
        )

    def get_by_id(self, operation_id: UUID) -> Optional[BulkOperation]:
        """Recupere une operation par ID."""
        return self._base_query().filter(BulkOperation.id == operation_id).first()

    def list(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[BulkOperation], int]:
        """Liste les operations."""
        query = self._base_query()
        if status:
            query = query.filter(BulkOperation.status == status)
        total = query.count()
        items = query.order_by(desc(BulkOperation.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def get_pending(self) -> List[BulkOperation]:
        """Recupere les operations en attente."""
        return self._base_query().filter(
            BulkOperation.status == "pending"
        ).order_by(BulkOperation.created_at).all()

    def create(self, data: Dict[str, Any]) -> BulkOperation:
        """Cree une nouvelle operation."""
        operation = BulkOperation(tenant_id=self.tenant_id, **data)
        self.db.add(operation)
        self.db.commit()
        self.db.refresh(operation)
        return operation

    def update_progress(
        self,
        operation: BulkOperation,
        processed: int,
        failed: int,
        errors: Optional[List[str]] = None
    ) -> BulkOperation:
        """Met a jour la progression."""
        operation.processed = processed
        operation.failed = failed
        if errors:
            operation.errors = errors
        self.db.commit()
        self.db.refresh(operation)
        return operation

    def complete(self, operation: BulkOperation) -> BulkOperation:
        """Marque comme complete."""
        operation.status = "completed"
        operation.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(operation)
        return operation

    def fail(self, operation: BulkOperation) -> BulkOperation:
        """Marque comme echoue."""
        operation.status = "failed"
        operation.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(operation)
        return operation
