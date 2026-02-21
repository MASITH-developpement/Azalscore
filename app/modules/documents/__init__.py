"""
AZALS MODULE - Documents (GED)
==============================

Module complet de Gestion Electronique de Documents.

Fonctionnalites:
----------------
- Upload/download fichiers avec chunking
- Dossiers hierarchiques
- Metadonnees personnalisables
- Versioning documents
- Recherche full-text
- Partage et permissions
- Liens avec entites (factures, contrats, etc.)
- Previsualisation
- Compression/archivage
- Retention et purge
- Audit trail acces
- Tags et categories

Generation documentaire:
------------------------
- Templates avec placeholders
- Generation PDF, DOCX, HTML
- Fusion de donnees (mail merge)
- Conditions et boucles
- Multi-langues
- Archivage

Usage:
------
    from app.modules.documents import get_ged_service, GEDService
    from app.modules.documents.schemas import FolderCreate, DocumentUpdate

    # Creer le service
    service = get_ged_service(db, tenant_id, user_id)

    # Creer un dossier
    folder = service.create_folder(FolderCreate(name="Documents"))

    # Upload un document
    result = service.upload_document(
        file_content=content,
        filename="rapport.pdf",
        folder_id=folder.id
    )

    # Rechercher
    results = service.search(SearchQuery(query="rapport"))

API REST:
---------
    - POST   /documents/folders           - Creer un dossier
    - GET    /documents/folders           - Lister les dossiers
    - GET    /documents/folders/{id}      - Recuperer un dossier
    - PUT    /documents/folders/{id}      - Modifier un dossier
    - DELETE /documents/folders/{id}      - Supprimer un dossier

    - POST   /documents/upload            - Uploader un document
    - GET    /documents                   - Lister les documents
    - GET    /documents/{id}              - Recuperer un document
    - PUT    /documents/{id}              - Modifier un document
    - DELETE /documents/{id}              - Supprimer un document
    - GET    /documents/{id}/download     - Telecharger un document

    - POST   /documents/{id}/versions     - Nouvelle version
    - GET    /documents/{id}/versions     - Lister les versions

    - POST   /documents/{id}/shares       - Creer un partage
    - POST   /documents/{id}/links        - Lier a une entite

    - POST   /documents/search            - Rechercher
    - GET    /documents/stats             - Statistiques

Inspire de: Sage, Axonaut, Pennylane, Odoo, Microsoft Dynamics 365, SharePoint
"""

# =============================================================================
# IMPORTS SERVICE GENERATION (existant)
# =============================================================================

from .service import (
    # Enumerations
    DocumentFormat,
    TemplateType,
    TemplateStatus,
    GenerationStatus,
    PlaceholderType,

    # Formats
    DATE_FORMATS,
    NUMBER_LOCALE,

    # Data classes
    Placeholder,
    TemplateSection,
    Template,
    GeneratedDocument,
    MergeJob,
    DocumentSignature,

    # Service
    DocumentService,
    create_document_service,
)

# =============================================================================
# IMPORTS SERVICE GED (nouveau)
# =============================================================================

from .ged_service import (
    GEDService,
    get_ged_service,
)

from .models import (
    # Enums
    DocumentStatus,
    DocumentType,
    FileCategory,
    AccessLevel,
    ShareType,
    LinkEntityType,
    RetentionPolicy,
    AuditAction,
    CompressionStatus,
    WorkflowStatus,

    # Models
    Folder,
    Document,
    DocumentVersion,
    DocumentShare,
    FolderPermission,
    DocumentLink,
    DocumentComment,
    DocumentTag,
    DocumentCategory,
    DocumentAudit,
    DocumentSequence,
    StorageConfig,
)

from .schemas import (
    # Dossiers
    FolderCreate,
    FolderUpdate,
    FolderResponse,
    FolderSummary,
    FolderTree,

    # Documents
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentSummary,
    DocumentList,

    # Upload
    UploadRequest,
    UploadResponse,
    ChunkUploadInit,
    ChunkUploadInitResponse,
    ChunkUploadComplete,

    # Versions
    VersionCreate,
    VersionResponse,

    # Partage
    ShareCreate,
    ShareUpdate,
    ShareResponse,
    ShareLinkAccess,

    # Liens
    DocumentLinkCreate,
    DocumentLinkResponse,

    # Commentaires
    CommentCreate,
    CommentUpdate,
    CommentResponse,

    # Tags et Categories
    TagCreate,
    TagResponse,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,

    # Audit
    AuditResponse,
    AuditList,

    # Recherche
    SearchQuery,
    SearchResult,
    SearchResponse,

    # Stats
    StorageStats,
    DocumentStats,

    # Batch
    BatchMoveRequest,
    BatchDeleteRequest,
    BatchTagRequest,
    BatchOperationResult,

    # Config
    StorageConfigUpdate,
    StorageConfigResponse,
)

from .exceptions import (
    DocumentException,
    DocumentNotFoundError,
    DocumentAlreadyExistsError,
    DocumentLockedError,
    DocumentVersionError,
    DocumentStatusError,
    DocumentRetentionError,
    FolderNotFoundError,
    FolderAlreadyExistsError,
    FolderNotEmptyError,
    FolderSystemError,
    FolderCircularReferenceError,
    FileTypeNotAllowedError,
    FileSizeLimitError,
    FileUploadError,
    FileDownloadError,
    FileCorruptedError,
    StorageQuotaExceededError,
    StorageProviderError,
    StorageConfigError,
    ShareNotFoundError,
    ShareExpiredError,
    ShareInvalidPasswordError,
    ShareDownloadLimitError,
    PermissionDeniedError,
    InsufficientAccessLevelError,
    WorkflowError,
    WorkflowTransitionError,
    CompressionError,
    ArchiveError,
    SearchError,
    IndexingError,
)

from .router import router

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # =========================================================================
    # Service Generation (existant)
    # =========================================================================
    "DocumentFormat",
    "TemplateType",
    "TemplateStatus",
    "GenerationStatus",
    "PlaceholderType",
    "DATE_FORMATS",
    "NUMBER_LOCALE",
    "Placeholder",
    "TemplateSection",
    "Template",
    "GeneratedDocument",
    "MergeJob",
    "DocumentSignature",
    "DocumentService",
    "create_document_service",

    # =========================================================================
    # Service GED (nouveau)
    # =========================================================================
    "GEDService",
    "get_ged_service",

    # =========================================================================
    # Enums
    # =========================================================================
    "DocumentStatus",
    "DocumentType",
    "FileCategory",
    "AccessLevel",
    "ShareType",
    "LinkEntityType",
    "RetentionPolicy",
    "AuditAction",
    "CompressionStatus",
    "WorkflowStatus",

    # =========================================================================
    # Models
    # =========================================================================
    "Folder",
    "Document",
    "DocumentVersion",
    "DocumentShare",
    "FolderPermission",
    "DocumentLink",
    "DocumentComment",
    "DocumentTag",
    "DocumentCategory",
    "DocumentAudit",
    "DocumentSequence",
    "StorageConfig",

    # =========================================================================
    # Schemas
    # =========================================================================
    # Dossiers
    "FolderCreate",
    "FolderUpdate",
    "FolderResponse",
    "FolderSummary",
    "FolderTree",

    # Documents
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentSummary",
    "DocumentList",

    # Upload
    "UploadRequest",
    "UploadResponse",
    "ChunkUploadInit",
    "ChunkUploadInitResponse",
    "ChunkUploadComplete",

    # Versions
    "VersionCreate",
    "VersionResponse",

    # Partage
    "ShareCreate",
    "ShareUpdate",
    "ShareResponse",
    "ShareLinkAccess",

    # Liens
    "DocumentLinkCreate",
    "DocumentLinkResponse",

    # Commentaires
    "CommentCreate",
    "CommentUpdate",
    "CommentResponse",

    # Tags et Categories
    "TagCreate",
    "TagResponse",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",

    # Audit
    "AuditResponse",
    "AuditList",

    # Recherche
    "SearchQuery",
    "SearchResult",
    "SearchResponse",

    # Stats
    "StorageStats",
    "DocumentStats",

    # Batch
    "BatchMoveRequest",
    "BatchDeleteRequest",
    "BatchTagRequest",
    "BatchOperationResult",

    # Config
    "StorageConfigUpdate",
    "StorageConfigResponse",

    # =========================================================================
    # Exceptions
    # =========================================================================
    "DocumentException",
    "DocumentNotFoundError",
    "DocumentAlreadyExistsError",
    "DocumentLockedError",
    "DocumentVersionError",
    "DocumentStatusError",
    "DocumentRetentionError",
    "FolderNotFoundError",
    "FolderAlreadyExistsError",
    "FolderNotEmptyError",
    "FolderSystemError",
    "FolderCircularReferenceError",
    "FileTypeNotAllowedError",
    "FileSizeLimitError",
    "FileUploadError",
    "FileDownloadError",
    "FileCorruptedError",
    "StorageQuotaExceededError",
    "StorageProviderError",
    "StorageConfigError",
    "ShareNotFoundError",
    "ShareExpiredError",
    "ShareInvalidPasswordError",
    "ShareDownloadLimitError",
    "PermissionDeniedError",
    "InsufficientAccessLevelError",
    "WorkflowError",
    "WorkflowTransitionError",
    "CompressionError",
    "ArchiveError",
    "SearchError",
    "IndexingError",

    # =========================================================================
    # Router
    # =========================================================================
    "router",
]
