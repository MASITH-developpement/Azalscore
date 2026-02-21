"""
Module Storage / Gestion de Fichiers - GAP-059

Gestion avancée des fichiers:
- Multi-backend (local, S3, Azure, GCS)
- Upload chunked pour gros fichiers
- Compression et déduplication
- Versioning des fichiers
- Quotas par tenant
- Scan antivirus
- URLs signées
"""

from .service import (
    # Énumérations
    StorageBackend,
    FileStatus,
    UploadStatus,
    AccessLevel,
    ScanStatus,
    CompressionType,

    # Data classes
    StorageConfig,
    FileMetadata,
    ChunkedUpload,
    ChunkInfo,
    StorageQuota,
    SignedUrl,
    FileVersion,
    BulkOperation,
    StorageStats,

    # Service
    StorageService,
    create_storage_service,
)

__all__ = [
    "StorageBackend",
    "FileStatus",
    "UploadStatus",
    "AccessLevel",
    "ScanStatus",
    "CompressionType",
    "StorageConfig",
    "FileMetadata",
    "ChunkedUpload",
    "ChunkInfo",
    "StorageQuota",
    "SignedUrl",
    "FileVersion",
    "BulkOperation",
    "StorageStats",
    "StorageService",
    "create_storage_service",
]
