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

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, BinaryIO
from uuid import uuid4
import hashlib
import mimetypes
import os


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class StorageBackend(str, Enum):
    """Backends de stockage supportés."""
    LOCAL = "local"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"
    MINIO = "minio"


class FileStatus(str, Enum):
    """Statut d'un fichier."""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    QUARANTINED = "quarantined"


class UploadStatus(str, Enum):
    """Statut d'un upload chunked."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AccessLevel(str, Enum):
    """Niveau d'accès aux fichiers."""
    PRIVATE = "private"
    INTERNAL = "internal"
    PUBLIC = "public"


class ScanStatus(str, Enum):
    """Statut du scan antivirus."""
    PENDING = "pending"
    SCANNING = "scanning"
    CLEAN = "clean"
    INFECTED = "infected"
    ERROR = "error"


class CompressionType(str, Enum):
    """Types de compression."""
    NONE = "none"
    GZIP = "gzip"
    BZIP2 = "bzip2"
    LZ4 = "lz4"
    ZSTD = "zstd"


# ============================================================================
# DATA CLASSES
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
class FileMetadata:
    """Métadonnées d'un fichier."""
    id: str
    tenant_id: str
    filename: str
    original_filename: str
    extension: str
    mime_type: str
    size: int
    compressed_size: Optional[int] = None
    checksum_md5: str = ""
    checksum_sha256: str = ""
    storage_path: str = ""
    storage_backend: StorageBackend = StorageBackend.LOCAL
    status: FileStatus = FileStatus.ACTIVE
    access_level: AccessLevel = AccessLevel.PRIVATE
    version: int = 1
    parent_version_id: Optional[str] = None
    is_latest: bool = True
    compression: CompressionType = CompressionType.NONE
    deduplicated: bool = False
    dedup_reference_id: Optional[str] = None
    scan_status: ScanStatus = ScanStatus.PENDING
    scan_result: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    uploaded_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    accessed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


@dataclass
class ChunkedUpload:
    """Upload en plusieurs parties."""
    id: str
    tenant_id: str
    filename: str
    total_size: int
    chunk_size: int
    total_chunks: int
    uploaded_chunks: Set[int] = field(default_factory=set)
    status: UploadStatus = UploadStatus.INITIATED
    storage_backend: StorageBackend = StorageBackend.LOCAL
    upload_key: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    initiated_by: Optional[str] = None
    initiated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))


@dataclass
class ChunkInfo:
    """Information sur un chunk."""
    chunk_number: int
    size: int
    checksum: str
    uploaded_at: datetime = field(default_factory=datetime.now)


@dataclass
class StorageQuota:
    """Quota de stockage par tenant."""
    tenant_id: str
    max_storage_bytes: int
    max_files: int
    used_storage_bytes: int = 0
    file_count: int = 0
    warning_threshold: float = 0.8
    blocked: bool = False
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def usage_percent(self) -> float:
        if self.max_storage_bytes == 0:
            return 0.0
        return self.used_storage_bytes / self.max_storage_bytes

    @property
    def remaining_bytes(self) -> int:
        return max(0, self.max_storage_bytes - self.used_storage_bytes)

    @property
    def is_warning(self) -> bool:
        return self.usage_percent >= self.warning_threshold

    @property
    def is_exceeded(self) -> bool:
        return self.used_storage_bytes >= self.max_storage_bytes


@dataclass
class SignedUrl:
    """URL signée pour accès temporaire."""
    url: str
    file_id: str
    method: str  # GET, PUT
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FileVersion:
    """Version d'un fichier."""
    version_id: str
    file_id: str
    version_number: int
    size: int
    checksum: str
    storage_path: str
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    comment: Optional[str] = None


@dataclass
class BulkOperation:
    """Opération en masse sur des fichiers."""
    id: str
    tenant_id: str
    operation: str  # copy, move, delete, archive
    file_ids: List[str] = field(default_factory=list)
    target_path: Optional[str] = None
    processed: int = 0
    failed: int = 0
    errors: List[Dict[str, str]] = field(default_factory=list)
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


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
    calculated_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class StorageService:
    """Service de gestion du stockage de fichiers."""

    def __init__(self, tenant_id: str, config: Optional[StorageConfig] = None):
        self.tenant_id = tenant_id
        self.config = config or StorageConfig(
            backend=StorageBackend.LOCAL,
            bucket_name="azalscore-files"
        )

        # Stockage en mémoire (simulation)
        self._files: Dict[str, FileMetadata] = {}
        self._uploads: Dict[str, ChunkedUpload] = {}
        self._chunks: Dict[str, Dict[int, ChunkInfo]] = {}
        self._quotas: Dict[str, StorageQuota] = {}
        self._versions: Dict[str, List[FileVersion]] = {}
        self._dedup_index: Dict[str, str] = {}  # checksum -> file_id
        self._file_content: Dict[str, bytes] = {}  # Simulation stockage

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
    ) -> Optional[FileMetadata]:
        """Upload un fichier."""
        # Vérifier quota
        quota = self._get_or_create_quota()
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
            if checksum_sha256 in self._dedup_index:
                dedup_ref_id = self._dedup_index[checksum_sha256]
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
        file_id = str(uuid4())
        storage_path = self._generate_storage_path(file_id, filename)

        # Créer métadonnées
        file_meta = FileMetadata(
            id=file_id,
            tenant_id=self.tenant_id,
            filename=self._sanitize_filename(filename),
            original_filename=filename,
            extension=extension,
            mime_type=mime_type,
            size=file_size if not deduplicated else 0,
            compressed_size=compressed_size,
            checksum_md5=checksum_md5,
            checksum_sha256=checksum_sha256,
            storage_path=storage_path,
            storage_backend=self.config.backend,
            status=FileStatus.PROCESSING,
            access_level=access_level,
            compression=compression,
            deduplicated=deduplicated,
            dedup_reference_id=dedup_ref_id,
            tags=tags or {},
            custom_metadata=metadata or {},
            entity_type=entity_type,
            entity_id=entity_id,
            uploaded_by=user_id
        )

        # Stocker le fichier (simulation)
        if not deduplicated:
            self._file_content[file_id] = file_content
            self._dedup_index[checksum_sha256] = file_id

        # Scan antivirus (simulation)
        if self.config.antivirus_enabled:
            scan_result = self._scan_file(file_content)
            file_meta.scan_status = scan_result[0]
            file_meta.scan_result = scan_result[1]

            if file_meta.scan_status == ScanStatus.INFECTED:
                file_meta.status = FileStatus.QUARANTINED
            else:
                file_meta.status = FileStatus.ACTIVE
        else:
            file_meta.scan_status = ScanStatus.CLEAN
            file_meta.status = FileStatus.ACTIVE

        self._files[file_id] = file_meta

        # Mettre à jour quota
        self._update_quota(file_size if not deduplicated else 0, 1)

        # Versioning
        if self.config.versioning_enabled:
            self._create_version(file_meta)

        return file_meta

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
    ) -> Optional[ChunkedUpload]:
        """Initie un upload en plusieurs parties."""
        # Vérifier quota
        quota = self._get_or_create_quota()
        if quota.blocked:
            return None

        if total_size + quota.used_storage_bytes > quota.max_storage_bytes:
            return None

        # Vérifier extension
        extension = self._get_extension(filename)
        if extension.lower() not in self.config.allowed_extensions:
            return None

        # Calculer nombre de chunks
        total_chunks = (total_size + chunk_size - 1) // chunk_size

        upload_id = str(uuid4())
        upload = ChunkedUpload(
            id=upload_id,
            tenant_id=self.tenant_id,
            filename=filename,
            total_size=total_size,
            chunk_size=chunk_size,
            total_chunks=total_chunks,
            storage_backend=self.config.backend,
            metadata=metadata or {},
            initiated_by=user_id
        )

        self._uploads[upload_id] = upload
        self._chunks[upload_id] = {}

        return upload

    def upload_chunk(
        self,
        upload_id: str,
        chunk_number: int,
        chunk_data: bytes
    ) -> Optional[ChunkInfo]:
        """Upload un chunk."""
        upload = self._uploads.get(upload_id)
        if not upload or upload.tenant_id != self.tenant_id:
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

        # Stocker chunk
        checksum = hashlib.md5(chunk_data).hexdigest()
        chunk_info = ChunkInfo(
            chunk_number=chunk_number,
            size=len(chunk_data),
            checksum=checksum
        )

        self._chunks[upload_id][chunk_number] = chunk_info
        upload.uploaded_chunks.add(chunk_number)
        upload.status = UploadStatus.IN_PROGRESS

        # Stocker données (simulation)
        chunk_key = f"{upload_id}_{chunk_number}"
        self._file_content[chunk_key] = chunk_data

        return chunk_info

    def complete_chunked_upload(
        self,
        upload_id: str,
        access_level: AccessLevel = AccessLevel.PRIVATE,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[FileMetadata]:
        """Complète un upload chunked."""
        upload = self._uploads.get(upload_id)
        if not upload or upload.tenant_id != self.tenant_id:
            return None

        # Vérifier que tous les chunks sont uploadés
        if len(upload.uploaded_chunks) != upload.total_chunks:
            return None

        upload.status = UploadStatus.COMPLETING

        # Assembler le fichier (simulation)
        full_content = b""
        for i in range(upload.total_chunks):
            chunk_key = f"{upload_id}_{i}"
            full_content += self._file_content.get(chunk_key, b"")
            # Nettoyer chunk
            self._file_content.pop(chunk_key, None)

        # Créer le fichier final
        file_meta = self.upload_file(
            full_content,
            upload.filename,
            access_level=access_level,
            entity_type=entity_type,
            entity_id=entity_id,
            tags=tags,
            metadata=upload.metadata,
            user_id=upload.initiated_by
        )

        if file_meta:
            upload.status = UploadStatus.COMPLETED
            upload.completed_at = datetime.now()
        else:
            upload.status = UploadStatus.FAILED

        return file_meta

    def abort_chunked_upload(self, upload_id: str) -> bool:
        """Annule un upload chunked."""
        upload = self._uploads.get(upload_id)
        if not upload or upload.tenant_id != self.tenant_id:
            return False

        # Nettoyer chunks
        for i in range(upload.total_chunks):
            chunk_key = f"{upload_id}_{i}"
            self._file_content.pop(chunk_key, None)

        upload.status = UploadStatus.CANCELLED
        self._chunks.pop(upload_id, None)

        return True

    # -------------------------------------------------------------------------
    # Récupération de fichiers
    # -------------------------------------------------------------------------

    def get_file(self, file_id: str) -> Optional[FileMetadata]:
        """Récupère les métadonnées d'un fichier."""
        file_meta = self._files.get(file_id)
        if file_meta and file_meta.tenant_id == self.tenant_id:
            file_meta.accessed_at = datetime.now()
            return file_meta
        return None

    def download_file(self, file_id: str) -> Optional[Tuple[bytes, FileMetadata]]:
        """Télécharge un fichier."""
        file_meta = self.get_file(file_id)
        if not file_meta:
            return None

        if file_meta.status not in [FileStatus.ACTIVE, FileStatus.ARCHIVED]:
            return None

        # Récupérer contenu
        content_id = file_meta.dedup_reference_id or file_id
        content = self._file_content.get(content_id)

        if not content:
            return None

        # Décompresser si nécessaire
        if file_meta.compression != CompressionType.NONE:
            content = self._decompress(content, file_meta.compression)

        return content, file_meta

    def generate_signed_url(
        self,
        file_id: str,
        method: str = "GET",
        expires_in: Optional[int] = None
    ) -> Optional[SignedUrl]:
        """Génère une URL signée pour accès temporaire."""
        file_meta = self.get_file(file_id)
        if not file_meta:
            return None

        expires_in = expires_in or self.config.signed_url_expiry
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        # Générer URL (simulation)
        signature = hashlib.sha256(
            f"{file_id}:{method}:{expires_at.isoformat()}".encode()
        ).hexdigest()[:32]

        base_url = self.config.cdn_url or f"https://storage.azalscore.com"
        url = f"{base_url}/{file_meta.storage_path}?sig={signature}&exp={int(expires_at.timestamp())}"

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
    ) -> Optional[FileMetadata]:
        """Met à jour les métadonnées d'un fichier."""
        file_meta = self.get_file(file_id)
        if not file_meta:
            return None

        if tags is not None:
            file_meta.tags.update(tags)

        if custom_metadata is not None:
            file_meta.custom_metadata.update(custom_metadata)

        if access_level is not None:
            file_meta.access_level = access_level

        file_meta.updated_at = datetime.now()

        return file_meta

    def archive_file(self, file_id: str) -> bool:
        """Archive un fichier."""
        file_meta = self.get_file(file_id)
        if not file_meta or file_meta.status != FileStatus.ACTIVE:
            return False

        file_meta.status = FileStatus.ARCHIVED
        file_meta.updated_at = datetime.now()

        return True

    def restore_file(self, file_id: str) -> bool:
        """Restaure un fichier archivé."""
        file_meta = self.get_file(file_id)
        if not file_meta or file_meta.status != FileStatus.ARCHIVED:
            return False

        file_meta.status = FileStatus.ACTIVE
        file_meta.updated_at = datetime.now()

        return True

    def delete_file(self, file_id: str, permanent: bool = False) -> bool:
        """Supprime un fichier."""
        file_meta = self.get_file(file_id)
        if not file_meta:
            return False

        if permanent:
            # Suppression définitive
            if not file_meta.deduplicated:
                self._file_content.pop(file_id, None)
                # Retirer de l'index de déduplication
                if file_meta.checksum_sha256 in self._dedup_index:
                    if self._dedup_index[file_meta.checksum_sha256] == file_id:
                        del self._dedup_index[file_meta.checksum_sha256]

            # Mettre à jour quota
            self._update_quota(-file_meta.size, -1)

            del self._files[file_id]
        else:
            # Soft delete
            file_meta.status = FileStatus.DELETED
            file_meta.updated_at = datetime.now()

        return True

    def copy_file(
        self,
        file_id: str,
        new_filename: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> Optional[FileMetadata]:
        """Copie un fichier."""
        source = self.get_file(file_id)
        if not source:
            return None

        # Récupérer contenu
        result = self.download_file(file_id)
        if not result:
            return None

        content, _ = result

        return self.upload_file(
            content,
            new_filename or source.original_filename,
            mime_type=source.mime_type,
            access_level=source.access_level,
            entity_type=entity_type or source.entity_type,
            entity_id=entity_id or source.entity_id,
            tags=source.tags.copy(),
            metadata=source.custom_metadata.copy(),
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
    ) -> Optional[FileMetadata]:
        """Upload une nouvelle version d'un fichier."""
        if not self.config.versioning_enabled:
            return None

        current = self.get_file(file_id)
        if not current:
            return None

        # Marquer version actuelle comme non-latest
        current.is_latest = False

        # Calculer nouveau checksum
        checksum_sha256 = hashlib.sha256(file_content).hexdigest()

        # Créer nouvelle version
        new_id = str(uuid4())
        new_version = current.version + 1

        new_file = FileMetadata(
            id=new_id,
            tenant_id=self.tenant_id,
            filename=current.filename,
            original_filename=current.original_filename,
            extension=current.extension,
            mime_type=current.mime_type,
            size=len(file_content),
            checksum_md5=hashlib.md5(file_content).hexdigest(),
            checksum_sha256=checksum_sha256,
            storage_path=self._generate_storage_path(new_id, current.filename),
            storage_backend=self.config.backend,
            status=FileStatus.ACTIVE,
            access_level=current.access_level,
            version=new_version,
            parent_version_id=file_id,
            is_latest=True,
            tags=current.tags.copy(),
            custom_metadata=current.custom_metadata.copy(),
            entity_type=current.entity_type,
            entity_id=current.entity_id,
            uploaded_by=user_id
        )

        # Stocker
        self._file_content[new_id] = file_content
        self._files[new_id] = new_file

        # Créer entrée version
        version_entry = FileVersion(
            version_id=new_id,
            file_id=file_id,
            version_number=new_version,
            size=len(file_content),
            checksum=checksum_sha256,
            storage_path=new_file.storage_path,
            created_by=user_id,
            comment=comment
        )

        if file_id not in self._versions:
            self._versions[file_id] = []
        self._versions[file_id].append(version_entry)

        # Limiter versions
        self._cleanup_old_versions(file_id)

        # Mettre à jour quota
        self._update_quota(len(file_content), 1)

        return new_file

    def get_versions(self, file_id: str) -> List[FileVersion]:
        """Liste les versions d'un fichier."""
        file_meta = self.get_file(file_id)
        if not file_meta:
            return []

        # Trouver l'ID racine
        root_id = file_id
        while True:
            root_meta = self._files.get(root_id)
            if not root_meta or not root_meta.parent_version_id:
                break
            root_id = root_meta.parent_version_id

        return self._versions.get(root_id, [])

    def restore_version(self, version_id: str, user_id: Optional[str] = None) -> Optional[FileMetadata]:
        """Restaure une version spécifique."""
        version_file = self._files.get(version_id)
        if not version_file or version_file.tenant_id != self.tenant_id:
            return None

        # Télécharger le contenu de cette version
        content = self._file_content.get(version_id)
        if not content:
            return None

        # Trouver le fichier le plus récent
        latest = version_file
        while True:
            found_newer = False
            for f in self._files.values():
                if f.parent_version_id == latest.id:
                    latest = f
                    found_newer = True
                    break
            if not found_newer:
                break

        # Upload comme nouvelle version
        return self.upload_new_version(
            latest.id,
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
    ) -> Tuple[List[FileMetadata], int]:
        """Liste les fichiers avec filtres."""
        results = []

        for file_meta in self._files.values():
            if file_meta.tenant_id != self.tenant_id:
                continue

            if only_latest and not file_meta.is_latest:
                continue

            if entity_type and file_meta.entity_type != entity_type:
                continue

            if entity_id and file_meta.entity_id != entity_id:
                continue

            if status and file_meta.status != status:
                continue

            if access_level and file_meta.access_level != access_level:
                continue

            if extension and file_meta.extension.lower() != extension.lower():
                continue

            if tags:
                match = True
                for k, v in tags.items():
                    if file_meta.tags.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            results.append(file_meta)

        # Trier par date création décroissante
        results.sort(key=lambda x: x.created_at, reverse=True)

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size

        return results[start:end], total

    def search_files(
        self,
        query: str,
        *,
        entity_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[FileMetadata], int]:
        """Recherche de fichiers par nom."""
        query_lower = query.lower()
        results = []

        for file_meta in self._files.values():
            if file_meta.tenant_id != self.tenant_id:
                continue

            if not file_meta.is_latest:
                continue

            if file_meta.status == FileStatus.DELETED:
                continue

            if entity_type and file_meta.entity_type != entity_type:
                continue

            # Recherche dans nom et tags
            if (query_lower in file_meta.filename.lower() or
                query_lower in file_meta.original_filename.lower() or
                any(query_lower in v.lower() for v in file_meta.tags.values())):
                results.append(file_meta)

        results.sort(key=lambda x: x.created_at, reverse=True)

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size

        return results[start:end], total

    # -------------------------------------------------------------------------
    # Quotas
    # -------------------------------------------------------------------------

    def get_quota(self) -> StorageQuota:
        """Récupère le quota du tenant."""
        return self._get_or_create_quota()

    def set_quota(
        self,
        max_storage_bytes: Optional[int] = None,
        max_files: Optional[int] = None,
        warning_threshold: Optional[float] = None
    ) -> StorageQuota:
        """Configure le quota du tenant."""
        quota = self._get_or_create_quota()

        if max_storage_bytes is not None:
            quota.max_storage_bytes = max_storage_bytes

        if max_files is not None:
            quota.max_files = max_files

        if warning_threshold is not None:
            quota.warning_threshold = warning_threshold

        quota.updated_at = datetime.now()

        return quota

    # -------------------------------------------------------------------------
    # Opérations en masse
    # -------------------------------------------------------------------------

    def bulk_delete(
        self,
        file_ids: List[str],
        permanent: bool = False
    ) -> BulkOperation:
        """Suppression en masse."""
        operation = BulkOperation(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            operation="delete",
            file_ids=file_ids,
            started_at=datetime.now()
        )

        for file_id in file_ids:
            try:
                if self.delete_file(file_id, permanent):
                    operation.processed += 1
                else:
                    operation.failed += 1
                    operation.errors.append({
                        "file_id": file_id,
                        "error": "File not found or access denied"
                    })
            except Exception as e:
                operation.failed += 1
                operation.errors.append({
                    "file_id": file_id,
                    "error": str(e)
                })

        operation.status = "completed"
        operation.completed_at = datetime.now()

        return operation

    def bulk_archive(self, file_ids: List[str]) -> BulkOperation:
        """Archivage en masse."""
        operation = BulkOperation(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            operation="archive",
            file_ids=file_ids,
            started_at=datetime.now()
        )

        for file_id in file_ids:
            if self.archive_file(file_id):
                operation.processed += 1
            else:
                operation.failed += 1
                operation.errors.append({
                    "file_id": file_id,
                    "error": "Failed to archive"
                })

        operation.status = "completed"
        operation.completed_at = datetime.now()

        return operation

    def bulk_update_tags(
        self,
        file_ids: List[str],
        tags: Dict[str, str]
    ) -> BulkOperation:
        """Mise à jour de tags en masse."""
        operation = BulkOperation(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            operation="update_tags",
            file_ids=file_ids,
            started_at=datetime.now()
        )

        for file_id in file_ids:
            if self.update_metadata(file_id, tags=tags):
                operation.processed += 1
            else:
                operation.failed += 1
                operation.errors.append({
                    "file_id": file_id,
                    "error": "File not found"
                })

        operation.status = "completed"
        operation.completed_at = datetime.now()

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

        for file_meta in self._files.values():
            if file_meta.tenant_id != self.tenant_id:
                continue

            if not file_meta.is_latest:
                stats.versions_count += 1
                continue

            stats.total_files += 1
            stats.total_size += file_meta.size

            # Par extension
            ext = file_meta.extension.lower()
            stats.by_extension[ext] = stats.by_extension.get(ext, 0) + 1

            # Par statut
            status = file_meta.status.value
            stats.by_status[status] = stats.by_status.get(status, 0) + 1

            # Par niveau d'accès
            access = file_meta.access_level.value
            stats.by_access_level[access] = stats.by_access_level.get(access, 0) + 1

            # Déduplication
            if file_meta.deduplicated:
                stats.dedup_savings += file_meta.size

            # Compression
            if file_meta.compressed_size:
                stats.compression_savings += file_meta.size - file_meta.compressed_size

            # Quarantaine
            if file_meta.status == FileStatus.QUARANTINED:
                stats.quarantined_count += 1

        return stats

    # -------------------------------------------------------------------------
    # Méthodes privées
    # -------------------------------------------------------------------------

    def _get_or_create_quota(self) -> StorageQuota:
        """Récupère ou crée le quota du tenant."""
        if self.tenant_id not in self._quotas:
            self._quotas[self.tenant_id] = StorageQuota(
                tenant_id=self.tenant_id,
                max_storage_bytes=10 * 1024 * 1024 * 1024,  # 10 GB
                max_files=10000
            )
        return self._quotas[self.tenant_id]

    def _update_quota(self, size_delta: int, count_delta: int):
        """Met à jour le quota."""
        quota = self._get_or_create_quota()
        quota.used_storage_bytes += size_delta
        quota.file_count += count_delta
        quota.updated_at = datetime.now()

    def _generate_storage_path(self, file_id: str, filename: str) -> str:
        """Génère le chemin de stockage."""
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        safe_name = self._sanitize_filename(filename)
        return f"{self.tenant_id}/{date_prefix}/{file_id}/{safe_name}"

    def _sanitize_filename(self, filename: str) -> str:
        """Nettoie un nom de fichier."""
        # Retirer caractères dangereux
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
        # Simulation - en production, utiliser zlib, lz4, etc.
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
        # Ici on simule un scan toujours clean
        return ScanStatus.CLEAN, None

    def _create_version(self, file_meta: FileMetadata):
        """Crée une entrée de version."""
        version = FileVersion(
            version_id=file_meta.id,
            file_id=file_meta.id,
            version_number=file_meta.version,
            size=file_meta.size,
            checksum=file_meta.checksum_sha256,
            storage_path=file_meta.storage_path,
            created_by=file_meta.uploaded_by
        )

        if file_meta.id not in self._versions:
            self._versions[file_meta.id] = []
        self._versions[file_meta.id].append(version)

    def _cleanup_old_versions(self, root_file_id: str):
        """Nettoie les anciennes versions."""
        if root_file_id not in self._versions:
            return

        versions = self._versions[root_file_id]
        if len(versions) <= self.config.max_versions:
            return

        # Trier par numéro de version
        versions.sort(key=lambda v: v.version_number)

        # Supprimer les plus anciennes
        to_remove = versions[:-self.config.max_versions]
        for v in to_remove:
            if v.version_id in self._files:
                self.delete_file(v.version_id, permanent=True)

        self._versions[root_file_id] = versions[-self.config.max_versions:]


# ============================================================================
# FACTORY
# ============================================================================

def create_storage_service(
    tenant_id: str,
    config: Optional[StorageConfig] = None
) -> StorageService:
    """Factory pour créer un service de stockage."""
    return StorageService(tenant_id, config)
