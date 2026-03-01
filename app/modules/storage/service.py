"""
Service Storage / Gestion de Fichiers - GAP-059

Gestion avancée des fichiers et stockage:
- Multi-backend (local, S3, Azure Blob, GCS)
- Chunked upload pour gros fichiers
- Compression et déduplication
- Métadonnées et tags
- Versioning des fichiers
- Quotas par tenant
- Scan antivirus (interface)
- CDN et URLs signées
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4
import hashlib
import mimetypes

from sqlalchemy.orm import Session

from .repository import (
    StorageFileRepository,
    FileVersionHistoryRepository,
    ChunkedUploadRepository,
    ChunkPartRepository,
    StorageQuotaRepository,
    BulkOperationRepository,
)
from .models import (
    StorageBackend,
    FileStatus,
    UploadStatus,
    AccessLevel,
    ScanStatus,
    CompressionType,
)


# ============================================================================
# DATA CLASSES (Configuration)
# ============================================================================

@dataclass
class StorageConfig:
    """Configuration du stockage."""
    backend: StorageBackend
    bucket_name: str
    region: Optional[str] = None
    endpoint_url: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    base_path: str = ""
    cdn_url: Optional[str] = None
    signed_url_expiry: int = 3600
    max_file_size: int = 100 * 1024 * 1024  # 100 MB
    allowed_extensions: Set[str] = field(default_factory=lambda: {
        "pdf", "doc", "docx", "xls", "xlsx", "csv", "txt",
        "jpg", "jpeg", "png", "gif", "svg", "webp",
        "zip", "tar", "gz"
    })
    compression_enabled: bool = True
    compression_type: CompressionType = CompressionType.GZIP
    compression_min_size: int = 1024  # Compresser seulement > 1KB
    deduplication_enabled: bool = True
    versioning_enabled: bool = True
    max_versions: int = 10
    antivirus_enabled: bool = False


@dataclass
class SignedUrl:
    """URL signée pour accès temporaire."""
    url: str
    file_id: str
    method: str  # GET, PUT
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StorageStats:
    """Statistiques de stockage."""
    tenant_id: str
    total_files: int
    total_size: int
    by_extension: Dict[str, int] = field(default_factory=dict)
    by_status: Dict[str, int] = field(default_factory=dict)
    by_access_level: Dict[str, int] = field(default_factory=dict)
    dedup_savings: int = 0
    compression_savings: int = 0
    versions_count: int = 0
    quarantined_count: int = 0
    calculated_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class StorageService:
    """Service de gestion du stockage de fichiers avec persistance SQLAlchemy."""

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        config: Optional[StorageConfig] = None,
        storage_backend: Optional[Any] = None
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.config = config or StorageConfig(
            backend=StorageBackend.LOCAL,
            bucket_name="azalscore-files"
        )
        self.storage_backend = storage_backend  # Backend réel (S3, local, etc.)

        # Repositories
        self.file_repo = StorageFileRepository(db, tenant_id)
        self.version_repo = FileVersionHistoryRepository(db, tenant_id)
        self.upload_repo = ChunkedUploadRepository(db, tenant_id)
        self.chunk_repo = ChunkPartRepository(db, tenant_id)
        self.quota_repo = StorageQuotaRepository(db, tenant_id)
        self.bulk_repo = BulkOperationRepository(db, tenant_id)

    # -------------------------------------------------------------------------
    # Upload simple
    # -------------------------------------------------------------------------

    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        *,
        mime_type: Optional[str] = None,
        access_level: AccessLevel = AccessLevel.PRIVATE,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Optional[Any]:
        """Upload un fichier."""
        # Vérifier quota
        quota = self.quota_repo.get_or_create()
        if quota.blocked or quota.is_exceeded:
            return None

        # Vérifier taille
        file_size = len(file_content)
        if file_size > self.config.max_file_size:
            return None

        # Vérifier extension
        extension = self._get_extension(filename)
        if extension.lower() not in self.config.allowed_extensions:
            return None

        # Calculer checksums
        checksum_md5 = hashlib.md5(file_content).hexdigest()
        checksum_sha256 = hashlib.sha256(file_content).hexdigest()

        # Déduplication
        deduplicated = False
        dedup_ref_id = None
        if self.config.deduplication_enabled:
            existing = self.file_repo.get_by_checksum(checksum_sha256)
            if existing:
                dedup_ref_id = str(existing.id)
                deduplicated = True

        # Compression
        compressed_size = None
        compression = CompressionType.NONE
        if (self.config.compression_enabled and
            file_size >= self.config.compression_min_size and
            not deduplicated):
            compressed_content, compression = self._compress(file_content)
            if compressed_content:
                compressed_size = len(compressed_content)
                file_content = compressed_content

        # Déterminer MIME type
        if not mime_type:
            mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        # Générer chemin de stockage
        file_id = uuid4()
        storage_path = self._generate_storage_path(str(file_id), filename)

        # Préparer données fichier
        file_data = {
            "id": file_id,
            "filename": self._sanitize_filename(filename),
            "original_filename": filename,
            "extension": extension,
            "mime_type": mime_type,
            "size": file_size,
            "compressed_size": compressed_size,
            "checksum_md5": checksum_md5,
            "checksum_sha256": checksum_sha256,
            "storage_path": storage_path,
            "storage_backend": self.config.backend,
            "status": FileStatus.PROCESSING,
            "access_level": access_level,
            "compression": compression,
            "deduplicated": deduplicated,
            "dedup_reference_id": UUID(dedup_ref_id) if dedup_ref_id else None,
            "tags": tags or {},
            "custom_metadata": metadata or {},
            "entity_type": entity_type,
            "entity_id": UUID(entity_id) if entity_id else None,
            "uploaded_by": user_id,
        }

        # Stocker le fichier physiquement si non dédupliqué
        if not deduplicated:
            self._store_content(str(file_id), file_content)

        # Scan antivirus (simulation)
        scan_status = ScanStatus.PENDING
        scan_result = None
        if self.config.antivirus_enabled:
            scan_status, scan_result = self._scan_file(file_content)
            file_data["scan_status"] = scan_status
            file_data["scan_result"] = scan_result

            if scan_status == ScanStatus.INFECTED:
                file_data["status"] = FileStatus.QUARANTINED
            else:
                file_data["status"] = FileStatus.ACTIVE
        else:
            file_data["scan_status"] = ScanStatus.CLEAN
            file_data["status"] = FileStatus.ACTIVE

        # Créer en base
        file_record = self.file_repo.create(file_data)

        # Mettre à jour quota
        if not deduplicated:
            self.quota_repo.add_usage(file_size)

        # Versioning
        if self.config.versioning_enabled:
            self._create_version(file_record, user_id)

        return file_record

    # -------------------------------------------------------------------------
    # Upload chunked
    # -------------------------------------------------------------------------

    def initiate_chunked_upload(
        self,
        filename: str,
        total_size: int,
        chunk_size: int = 5 * 1024 * 1024,  # 5 MB par défaut
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Optional[Any]:
        """Initie un upload en plusieurs parties."""
        # Vérifier quota
        quota = self.quota_repo.get_or_create()
        if quota.blocked:
            return None

        if not self.quota_repo.check_quota(total_size):
            return None

        # Vérifier extension
        extension = self._get_extension(filename)
        if extension.lower() not in self.config.allowed_extensions:
            return None

        # Calculer nombre de chunks
        total_chunks = (total_size + chunk_size - 1) // chunk_size

        upload_data = {
            "filename": filename,
            "total_size": total_size,
            "chunk_size": chunk_size,
            "total_chunks": total_chunks,
            "storage_backend": self.config.backend,
            "metadata": metadata or {},
            "initiated_by": user_id,
            "expires_at": datetime.utcnow() + timedelta(hours=24),
        }

        return self.upload_repo.create(upload_data)

    def upload_chunk(
        self,
        upload_id: str,
        chunk_number: int,
        chunk_data: bytes
    ) -> Optional[Any]:
        """Upload un chunk."""
        upload = self.upload_repo.get_by_id(UUID(upload_id))
        if not upload:
            return None

        if upload.status not in [UploadStatus.INITIATED, UploadStatus.IN_PROGRESS]:
            return None

        if chunk_number < 0 or chunk_number >= upload.total_chunks:
            return None

        # Vérifier taille du chunk
        expected_size = upload.chunk_size
        if chunk_number == upload.total_chunks - 1:
            # Dernier chunk peut être plus petit
            expected_size = upload.total_size - (chunk_number * upload.chunk_size)

        if len(chunk_data) != expected_size:
            return None

        # Calculer checksum
        checksum = hashlib.md5(chunk_data).hexdigest()

        # Créer chunk en base
        chunk_data_record = {
            "upload_id": upload.id,
            "chunk_number": chunk_number,
            "size": len(chunk_data),
            "checksum": checksum,
        }
        chunk_record = self.chunk_repo.create(chunk_data_record)

        # Stocker données du chunk
        chunk_key = f"{upload_id}_{chunk_number}"
        self._store_content(chunk_key, chunk_data)

        # Mettre à jour statut upload
        if upload.status == UploadStatus.INITIATED:
            self.upload_repo.update_status(upload, UploadStatus.IN_PROGRESS)

        return chunk_record

    def complete_chunked_upload(
        self,
        upload_id: str,
        access_level: AccessLevel = AccessLevel.PRIVATE,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[Any]:
        """Complète un upload chunked."""
        upload = self.upload_repo.get_by_id(UUID(upload_id))
        if not upload:
            return None

        # Vérifier que tous les chunks sont uploadés
        chunk_count = self.chunk_repo.count_chunks(upload.id)
        if chunk_count != upload.total_chunks:
            return None

        self.upload_repo.update_status(upload, UploadStatus.COMPLETING)

        # Assembler le fichier
        full_content = b""
        for i in range(upload.total_chunks):
            chunk_key = f"{upload_id}_{i}"
            chunk_content = self._retrieve_content(chunk_key)
            if chunk_content:
                full_content += chunk_content
                # Nettoyer chunk
                self._delete_content(chunk_key)

        # Créer le fichier final
        file_record = self.upload_file(
            full_content,
            upload.filename,
            access_level=access_level,
            entity_type=entity_type,
            entity_id=entity_id,
            tags=tags,
            metadata=upload.metadata,
            user_id=upload.initiated_by
        )

        if file_record:
            self.upload_repo.update_status(upload, UploadStatus.COMPLETED)
        else:
            self.upload_repo.update_status(upload, UploadStatus.FAILED)

        return file_record

    def abort_chunked_upload(self, upload_id: str) -> bool:
        """Annule un upload chunked."""
        upload = self.upload_repo.get_by_id(UUID(upload_id))
        if not upload:
            return False

        # Nettoyer chunks
        for i in range(upload.total_chunks):
            chunk_key = f"{upload_id}_{i}"
            self._delete_content(chunk_key)

        self.upload_repo.update_status(upload, UploadStatus.CANCELLED)

        return True

    # -------------------------------------------------------------------------
    # Récupération de fichiers
    # -------------------------------------------------------------------------

    def get_file(self, file_id: str) -> Optional[Any]:
        """Récupère les métadonnées d'un fichier."""
        file_record = self.file_repo.get_by_id(UUID(file_id))
        if file_record:
            self.file_repo.record_access(file_record)
        return file_record

    def download_file(self, file_id: str) -> Optional[Tuple[bytes, Any]]:
        """Télécharge un fichier."""
        file_record = self.get_file(file_id)
        if not file_record:
            return None

        if file_record.status not in [FileStatus.ACTIVE, FileStatus.ARCHIVED]:
            return None

        # Récupérer contenu
        content_id = str(file_record.dedup_reference_id or file_record.id)
        content = self._retrieve_content(content_id)

        if not content:
            return None

        # Décompresser si nécessaire
        if file_record.compression != CompressionType.NONE:
            content = self._decompress(content, file_record.compression)

        return content, file_record

    def generate_signed_url(
        self,
        file_id: str,
        method: str = "GET",
        expires_in: Optional[int] = None
    ) -> Optional[SignedUrl]:
        """Génère une URL signée pour accès temporaire."""
        file_record = self.get_file(file_id)
        if not file_record:
            return None

        expires_in = expires_in or self.config.signed_url_expiry
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        # Générer URL (simulation ou délégation au backend)
        signature = hashlib.sha256(
            f"{file_id}:{method}:{expires_at.isoformat()}".encode()
        ).hexdigest()[:32]

        base_url = self.config.cdn_url or "https://storage.azalscore.com"
        url = f"{base_url}/{file_record.storage_path}?sig={signature}&exp={int(expires_at.timestamp())}"

        return SignedUrl(
            url=url,
            file_id=file_id,
            method=method,
            expires_at=expires_at
        )

    # -------------------------------------------------------------------------
    # Gestion des fichiers
    # -------------------------------------------------------------------------

    def update_metadata(
        self,
        file_id: str,
        tags: Optional[Dict[str, str]] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
        access_level: Optional[AccessLevel] = None
    ) -> Optional[Any]:
        """Met à jour les métadonnées d'un fichier."""
        file_record = self.file_repo.get_by_id(UUID(file_id))
        if not file_record:
            return None

        update_data = {}
        if tags is not None:
            current_tags = file_record.tags or {}
            current_tags.update(tags)
            update_data["tags"] = current_tags

        if custom_metadata is not None:
            current_meta = file_record.custom_metadata or {}
            current_meta.update(custom_metadata)
            update_data["custom_metadata"] = current_meta

        if access_level is not None:
            update_data["access_level"] = access_level

        if update_data:
            return self.file_repo.update(file_record, update_data)

        return file_record

    def archive_file(self, file_id: str) -> bool:
        """Archive un fichier."""
        file_record = self.file_repo.get_by_id(UUID(file_id))
        if not file_record or file_record.status != FileStatus.ACTIVE:
            return False

        self.file_repo.archive(file_record)
        return True

    def restore_file(self, file_id: str) -> bool:
        """Restaure un fichier archivé."""
        file_record = self.file_repo.get_by_id(UUID(file_id))
        if not file_record or file_record.status != FileStatus.ARCHIVED:
            return False

        self.file_repo.update(file_record, {"status": FileStatus.ACTIVE})
        return True

    def delete_file(self, file_id: str, permanent: bool = False) -> bool:
        """Supprime un fichier."""
        file_record = self.file_repo.get_by_id(UUID(file_id))
        if not file_record:
            return False

        if permanent:
            # Suppression définitive
            if not file_record.deduplicated:
                self._delete_content(str(file_record.id))

            # Mettre à jour quota
            self.quota_repo.remove_usage(file_record.size)

            self.file_repo.hard_delete(file_record)
        else:
            # Soft delete
            self.file_repo.soft_delete(file_record)

        return True

    def copy_file(
        self,
        file_id: str,
        new_filename: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> Optional[Any]:
        """Copie un fichier."""
        result = self.download_file(file_id)
        if not result:
            return None

        content, source = result

        return self.upload_file(
            content,
            new_filename or source.original_filename,
            mime_type=source.mime_type,
            access_level=source.access_level,
            entity_type=entity_type or source.entity_type,
            entity_id=str(entity_id) if entity_id else (str(source.entity_id) if source.entity_id else None),
            tags=dict(source.tags) if source.tags else None,
            metadata=dict(source.custom_metadata) if source.custom_metadata else None,
            user_id=source.uploaded_by
        )

    # -------------------------------------------------------------------------
    # Versioning
    # -------------------------------------------------------------------------

    def upload_new_version(
        self,
        file_id: str,
        file_content: bytes,
        comment: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Optional[Any]:
        """Upload une nouvelle version d'un fichier."""
        if not self.config.versioning_enabled:
            return None

        current = self.file_repo.get_by_id(UUID(file_id))
        if not current:
            return None

        # Marquer version actuelle comme non-latest
        self.file_repo.update(current, {"is_latest": False})

        # Calculer checksums
        checksum_md5 = hashlib.md5(file_content).hexdigest()
        checksum_sha256 = hashlib.sha256(file_content).hexdigest()

        # Créer nouvelle version
        new_id = uuid4()
        new_version = current.version + 1

        file_data = {
            "id": new_id,
            "filename": current.filename,
            "original_filename": current.original_filename,
            "extension": current.extension,
            "mime_type": current.mime_type,
            "size": len(file_content),
            "checksum_md5": checksum_md5,
            "checksum_sha256": checksum_sha256,
            "storage_path": self._generate_storage_path(str(new_id), current.filename),
            "storage_backend": self.config.backend,
            "status": FileStatus.ACTIVE,
            "access_level": current.access_level,
            "version": new_version,
            "parent_version_id": current.id,
            "is_latest": True,
            "tags": dict(current.tags) if current.tags else {},
            "custom_metadata": dict(current.custom_metadata) if current.custom_metadata else {},
            "entity_type": current.entity_type,
            "entity_id": current.entity_id,
            "uploaded_by": user_id,
        }

        # Stocker contenu
        self._store_content(str(new_id), file_content)

        # Créer en base
        new_file = self.file_repo.create(file_data)

        # Créer entrée version
        version_data = {
            "file_id": current.id,
            "version_number": new_version,
            "size": len(file_content),
            "checksum": checksum_sha256,
            "storage_path": new_file.storage_path,
            "created_by": user_id,
            "comment": comment,
        }
        self.version_repo.create(version_data)

        # Limiter versions
        self._cleanup_old_versions(str(current.id))

        # Mettre à jour quota
        self.quota_repo.add_usage(len(file_content))

        return new_file

    def get_versions(self, file_id: str) -> List[Any]:
        """Liste les versions d'un fichier."""
        file_record = self.file_repo.get_by_id(UUID(file_id))
        if not file_record:
            return []

        # Trouver l'ID racine
        root_id = file_record.id
        while True:
            root_record = self.file_repo.get_by_id(root_id)
            if not root_record or not root_record.parent_version_id:
                break
            root_id = root_record.parent_version_id

        return self.version_repo.get_by_file(root_id)

    def restore_version(self, version_id: str, user_id: Optional[str] = None) -> Optional[Any]:
        """Restaure une version spécifique."""
        version_file = self.file_repo.get_by_id(UUID(version_id))
        if not version_file:
            return None

        # Télécharger le contenu de cette version
        content = self._retrieve_content(str(version_file.id))
        if not content:
            return None

        # Trouver le fichier le plus récent (is_latest=True)
        # Suivre la chaîne des versions
        latest = version_file
        all_files, _ = self.file_repo.list(
            entity_type=version_file.entity_type,
            entity_id=version_file.entity_id,
            page_size=1000
        )
        for f in all_files:
            if f.is_latest and (
                f.id == version_file.id or
                f.parent_version_id == version_file.id or
                version_file.parent_version_id == f.parent_version_id
            ):
                latest = f
                break

        # Upload comme nouvelle version
        return self.upload_new_version(
            str(latest.id),
            content,
            comment=f"Restored from version {version_file.version}",
            user_id=user_id
        )

    # -------------------------------------------------------------------------
    # Recherche et listing
    # -------------------------------------------------------------------------

    def list_files(
        self,
        *,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        status: Optional[FileStatus] = None,
        access_level: Optional[AccessLevel] = None,
        extension: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        only_latest: bool = True,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Any], int]:
        """Liste les fichiers avec filtres."""
        return self.file_repo.list(
            entity_type=entity_type,
            entity_id=UUID(entity_id) if entity_id else None,
            status=status,
            search=None,
            page=page,
            page_size=page_size
        )

    def search_files(
        self,
        query: str,
        *,
        entity_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Any], int]:
        """Recherche de fichiers par nom."""
        return self.file_repo.list(
            entity_type=entity_type,
            search=query,
            page=page,
            page_size=page_size
        )

    # -------------------------------------------------------------------------
    # Quotas
    # -------------------------------------------------------------------------

    def get_quota(self) -> Any:
        """Récupère le quota du tenant."""
        return self.quota_repo.get_or_create()

    def set_quota(
        self,
        max_storage_bytes: Optional[int] = None,
        max_files: Optional[int] = None,
        warning_threshold: Optional[float] = None
    ) -> Any:
        """Configure le quota du tenant."""
        quota = self.quota_repo.get_or_create()

        update_data = {}
        if max_storage_bytes is not None:
            update_data["max_storage_bytes"] = max_storage_bytes

        if max_files is not None:
            update_data["max_files"] = max_files

        if warning_threshold is not None:
            update_data["warning_threshold"] = warning_threshold

        if update_data:
            return self.quota_repo.update(quota, update_data)

        return quota

    # -------------------------------------------------------------------------
    # Opérations en masse
    # -------------------------------------------------------------------------

    def bulk_delete(
        self,
        file_ids: List[str],
        permanent: bool = False
    ) -> Any:
        """Suppression en masse."""
        operation = self.bulk_repo.create({
            "operation": "delete",
            "file_ids": file_ids,
            "started_at": datetime.utcnow(),
        })

        processed = 0
        failed = 0
        errors = []

        for file_id in file_ids:
            try:
                if self.delete_file(file_id, permanent):
                    processed += 1
                else:
                    failed += 1
                    errors.append(f"{file_id}: File not found or access denied")
            except Exception as e:
                failed += 1
                errors.append(f"{file_id}: {str(e)}")

        self.bulk_repo.update_progress(operation, processed, failed, errors)
        self.bulk_repo.complete(operation)

        return operation

    def bulk_archive(self, file_ids: List[str]) -> Any:
        """Archivage en masse."""
        operation = self.bulk_repo.create({
            "operation": "archive",
            "file_ids": file_ids,
            "started_at": datetime.utcnow(),
        })

        processed = 0
        failed = 0
        errors = []

        for file_id in file_ids:
            if self.archive_file(file_id):
                processed += 1
            else:
                failed += 1
                errors.append(f"{file_id}: Failed to archive")

        self.bulk_repo.update_progress(operation, processed, failed, errors)
        self.bulk_repo.complete(operation)

        return operation

    def bulk_update_tags(
        self,
        file_ids: List[str],
        tags: Dict[str, str]
    ) -> Any:
        """Mise à jour de tags en masse."""
        operation = self.bulk_repo.create({
            "operation": "update_tags",
            "file_ids": file_ids,
            "started_at": datetime.utcnow(),
        })

        processed = 0
        failed = 0
        errors = []

        for file_id in file_ids:
            if self.update_metadata(file_id, tags=tags):
                processed += 1
            else:
                failed += 1
                errors.append(f"{file_id}: File not found")

        self.bulk_repo.update_progress(operation, processed, failed, errors)
        self.bulk_repo.complete(operation)

        return operation

    # -------------------------------------------------------------------------
    # Statistiques
    # -------------------------------------------------------------------------

    def get_statistics(self) -> StorageStats:
        """Calcule les statistiques de stockage."""
        stats = StorageStats(
            tenant_id=self.tenant_id,
            total_files=0,
            total_size=0
        )

        # Récupérer tous les fichiers
        files, total = self.file_repo.list(page_size=10000)

        for file_record in files:
            if not file_record.is_latest:
                stats.versions_count += 1
                continue

            stats.total_files += 1
            stats.total_size += file_record.size

            # Par extension
            ext = file_record.extension.lower() if file_record.extension else ""
            stats.by_extension[ext] = stats.by_extension.get(ext, 0) + 1

            # Par statut
            status = file_record.status.value if file_record.status else "unknown"
            stats.by_status[status] = stats.by_status.get(status, 0) + 1

            # Par niveau d'accès
            access = file_record.access_level.value if file_record.access_level else "private"
            stats.by_access_level[access] = stats.by_access_level.get(access, 0) + 1

            # Déduplication
            if file_record.deduplicated:
                stats.dedup_savings += file_record.size

            # Compression
            if file_record.compressed_size:
                stats.compression_savings += file_record.size - file_record.compressed_size

            # Quarantaine
            if file_record.status == FileStatus.QUARANTINED:
                stats.quarantined_count += 1

        return stats

    # -------------------------------------------------------------------------
    # Méthodes privées
    # -------------------------------------------------------------------------

    def _generate_storage_path(self, file_id: str, filename: str) -> str:
        """Génère le chemin de stockage."""
        date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
        safe_name = self._sanitize_filename(filename)
        return f"{self.tenant_id}/{date_prefix}/{file_id}/{safe_name}"

    def _sanitize_filename(self, filename: str) -> str:
        """Nettoie un nom de fichier."""
        dangerous = ['/', '\\', '..', '\x00', ':', '*', '?', '"', '<', '>', '|']
        safe = filename
        for char in dangerous:
            safe = safe.replace(char, '_')
        return safe[:255]

    def _get_extension(self, filename: str) -> str:
        """Extrait l'extension d'un fichier."""
        if '.' not in filename:
            return ""
        return filename.rsplit('.', 1)[-1]

    def _compress(self, data: bytes) -> Tuple[Optional[bytes], CompressionType]:
        """Compresse les données."""
        import zlib

        if self.config.compression_type == CompressionType.GZIP:
            compressed = zlib.compress(data, level=6)
            if len(compressed) < len(data):
                return compressed, CompressionType.GZIP

        return None, CompressionType.NONE

    def _decompress(self, data: bytes, compression: CompressionType) -> bytes:
        """Décompresse les données."""
        import zlib

        if compression == CompressionType.GZIP:
            return zlib.decompress(data)

        return data

    def _scan_file(self, content: bytes) -> Tuple[ScanStatus, Optional[str]]:
        """Scanne un fichier pour virus (simulation)."""
        # En production, intégrer ClamAV ou autre
        return ScanStatus.CLEAN, None

    def _create_version(self, file_record: Any, user_id: Optional[str] = None):
        """Crée une entrée de version."""
        version_data = {
            "file_id": file_record.id,
            "version_number": file_record.version if hasattr(file_record, 'version') else 1,
            "size": file_record.size,
            "checksum": file_record.checksum_sha256,
            "storage_path": file_record.storage_path,
            "created_by": user_id,
        }
        self.version_repo.create(version_data)

    def _cleanup_old_versions(self, root_file_id: str):
        """Nettoie les anciennes versions."""
        versions = self.version_repo.get_by_file(UUID(root_file_id))

        if len(versions) <= self.config.max_versions:
            return

        # Trier par numéro de version (déjà triées en desc par le repo)
        versions.sort(key=lambda v: v.version_number)

        # Supprimer les plus anciennes
        to_remove = versions[:-self.config.max_versions]
        for v in to_remove:
            # Supprimer le fichier associé
            self.delete_file(str(v.version_id) if hasattr(v, 'version_id') else str(v.id), permanent=True)

    def _store_content(self, file_id: str, content: bytes):
        """Stocke le contenu du fichier (délégation au backend)."""
        if self.storage_backend:
            self.storage_backend.store(file_id, content)
        # En simulation, le contenu n'est pas persisté en mémoire

    def _retrieve_content(self, file_id: str) -> Optional[bytes]:
        """Récupère le contenu du fichier (délégation au backend)."""
        if self.storage_backend:
            return self.storage_backend.retrieve(file_id)
        # En simulation, retourner None (nécessite un vrai backend)
        return None

    def _delete_content(self, file_id: str):
        """Supprime le contenu du fichier (délégation au backend)."""
        if self.storage_backend:
            self.storage_backend.delete(file_id)


# ============================================================================
# FACTORY
# ============================================================================

def create_storage_service(
    db: Session,
    tenant_id: str,
    config: Optional[StorageConfig] = None,
    storage_backend: Optional[Any] = None
) -> StorageService:
    """Factory pour créer un service de stockage."""
    return StorageService(db, tenant_id, config, storage_backend)
