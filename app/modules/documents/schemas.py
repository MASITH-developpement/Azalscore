"""
AZALS MODULE - Documents (GED) - Schemas
=========================================

Schemas Pydantic pour la validation et la serialisation.
"""
from __future__ import annotations


from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import (
    AccessLevel,
    AuditAction,
    CompressionStatus,
    DocumentStatus,
    DocumentType,
    FileCategory,
    LinkEntityType,
    RetentionPolicy,
    ShareType,
    WorkflowStatus,
)


# =============================================================================
# SCHEMAS DOSSIER
# =============================================================================

class FolderBase(BaseModel):
    """Base pour les dossiers."""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')
    icon: Optional[str] = Field(None, max_length=50)


class FolderCreate(FolderBase):
    """Creation d'un dossier."""
    parent_id: Optional[UUID] = None
    default_access_level: AccessLevel = AccessLevel.VIEW
    inherit_permissions: bool = True
    retention_policy: RetentionPolicy = RetentionPolicy.NONE
    retention_days: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class FolderUpdate(BaseModel):
    """Mise a jour d'un dossier."""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    default_access_level: Optional[AccessLevel] = None
    inherit_permissions: Optional[bool] = None
    retention_policy: Optional[RetentionPolicy] = None
    retention_days: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class FolderResponse(FolderBase):
    """Reponse dossier."""
    id: UUID
    tenant_id: str
    parent_id: Optional[UUID] = None
    path: str
    level: int
    is_system: bool
    is_template: bool
    default_access_level: AccessLevel
    inherit_permissions: bool
    retention_policy: RetentionPolicy
    retention_days: Optional[int] = None
    document_count: int
    subfolder_count: int
    total_size: int
    metadata: Dict[str, Any]
    tags: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    version: int


class FolderSummary(BaseModel):
    """Resume dossier (pour les listes)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    path: str
    level: int
    parent_id: Optional[UUID] = None
    document_count: int
    subfolder_count: int
    total_size: int
    color: Optional[str] = None
    icon: Optional[str] = None
    is_system: bool


class FolderTree(BaseModel):
    """Arbre de dossiers."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    path: str
    level: int
    children: List["FolderTree"] = Field(default_factory=list)
    document_count: int
    color: Optional[str] = None
    icon: Optional[str] = None


# =============================================================================
# SCHEMAS DOCUMENT
# =============================================================================

class DocumentBase(BaseModel):
    """Base pour les documents."""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=255)
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Creation d'un document."""
    folder_id: Optional[UUID] = None
    document_type: DocumentType = DocumentType.FILE
    category: FileCategory = FileCategory.DOCUMENT
    retention_policy: RetentionPolicy = RetentionPolicy.NONE
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class DocumentUpdate(BaseModel):
    """Mise a jour d'un document."""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    title: Optional[str] = None
    description: Optional[str] = None
    folder_id: Optional[UUID] = None
    category: Optional[FileCategory] = None
    status: Optional[DocumentStatus] = None
    retention_policy: Optional[RetentionPolicy] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class DocumentResponse(DocumentBase):
    """Reponse document complete."""
    id: UUID
    tenant_id: str
    code: str
    folder_id: Optional[UUID] = None
    document_type: DocumentType
    status: DocumentStatus
    category: FileCategory

    # Fichier
    file_extension: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: int

    # Stockage
    storage_path: Optional[str] = None
    storage_provider: str
    checksum: Optional[str] = None

    # Versioning
    current_version: int
    is_latest: bool
    original_document_id: Optional[UUID] = None

    # Workflow
    workflow_status: WorkflowStatus
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None

    # Verrouillage
    is_locked: bool
    locked_by: Optional[UUID] = None
    locked_at: Optional[datetime] = None

    # Compression
    compression_status: CompressionStatus
    compressed_size: Optional[int] = None
    compression_ratio: Optional[float] = None

    # Retention
    retention_policy: RetentionPolicy
    retention_until: Optional[datetime] = None

    # Preview
    preview_available: bool
    thumbnail_path: Optional[str] = None

    # Metadonnees
    metadata: Dict[str, Any]
    tags: List[str]
    custom_fields: Dict[str, Any]

    # Statistiques
    view_count: int
    download_count: int
    share_count: int
    last_accessed_at: Optional[datetime] = None

    # Audit
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    version: int


class DocumentSummary(BaseModel):
    """Resume document (pour les listes)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    title: Optional[str] = None
    document_type: DocumentType
    status: DocumentStatus
    category: FileCategory
    file_extension: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: int
    folder_id: Optional[UUID] = None
    current_version: int
    is_locked: bool
    preview_available: bool
    thumbnail_path: Optional[str] = None
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None


class DocumentList(BaseModel):
    """Liste paginee de documents."""
    items: List[DocumentSummary]
    total: int
    page: int = 1
    page_size: int = 20
    pages: int = 1


# =============================================================================
# SCHEMAS UPLOAD
# =============================================================================

class UploadRequest(BaseModel):
    """Requete d'upload."""
    folder_id: Optional[UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    category: FileCategory = FileCategory.DOCUMENT
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    retention_policy: RetentionPolicy = RetentionPolicy.NONE


class UploadResponse(BaseModel):
    """Reponse d'upload."""
    document_id: UUID
    code: str
    name: str
    file_size: int
    mime_type: Optional[str] = None
    checksum: str
    storage_path: str
    version: int
    created_at: datetime


class ChunkUploadInit(BaseModel):
    """Initialisation upload par chunks."""
    filename: str
    file_size: int
    mime_type: Optional[str] = None
    chunk_size: int = Field(default=5242880, ge=1048576)  # 5MB par defaut, min 1MB
    folder_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChunkUploadInitResponse(BaseModel):
    """Reponse initialisation upload par chunks."""
    upload_id: str
    chunk_size: int
    total_chunks: int
    expires_at: datetime


class ChunkUploadComplete(BaseModel):
    """Completion upload par chunks."""
    upload_id: str
    parts: List[Dict[str, Any]]  # [{"part_number": 1, "etag": "..."}]


# =============================================================================
# SCHEMAS VERSION
# =============================================================================

class VersionCreate(BaseModel):
    """Creation d'une nouvelle version."""
    change_summary: Optional[str] = Field(None, max_length=500)
    change_type: str = Field(default="MINOR", pattern=r'^(MINOR|MAJOR|REVISION)$')


class VersionResponse(BaseModel):
    """Reponse version."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    version_number: int
    file_size: int
    checksum: Optional[str] = None
    change_summary: Optional[str] = None
    change_type: Optional[str] = None
    created_at: datetime
    created_by: Optional[UUID] = None


# =============================================================================
# SCHEMAS PARTAGE
# =============================================================================

class ShareCreate(BaseModel):
    """Creation d'un partage."""
    share_type: ShareType
    access_level: AccessLevel = AccessLevel.VIEW

    # Destinataire (selon share_type)
    user_id: Optional[UUID] = None
    role: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None  # Pour partage externe

    # Options
    can_download: bool = True
    can_print: bool = True
    can_share: bool = False
    notify_on_access: bool = False

    # Validite
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    # Lien (pour PUBLIC)
    generate_link: bool = False
    link_password: Optional[str] = None
    link_max_downloads: Optional[int] = None


class ShareUpdate(BaseModel):
    """Mise a jour d'un partage."""
    access_level: Optional[AccessLevel] = None
    can_download: Optional[bool] = None
    can_print: Optional[bool] = None
    can_share: Optional[bool] = None
    notify_on_access: Optional[bool] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None


class ShareResponse(BaseModel):
    """Reponse partage."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: Optional[UUID] = None
    folder_id: Optional[UUID] = None
    share_type: ShareType
    access_level: AccessLevel

    shared_with_user_id: Optional[UUID] = None
    shared_with_role: Optional[str] = None
    shared_with_department: Optional[str] = None
    shared_with_email: Optional[str] = None

    share_link: Optional[str] = None
    share_link_expires_at: Optional[datetime] = None
    share_link_download_count: int = 0

    can_download: bool
    can_print: bool
    can_share: bool

    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool

    created_at: datetime
    created_by: Optional[UUID] = None


class ShareLinkAccess(BaseModel):
    """Acces via lien de partage."""
    password: Optional[str] = None


# =============================================================================
# SCHEMAS LIEN ENTITE
# =============================================================================

class DocumentLinkCreate(BaseModel):
    """Creation d'un lien document-entite."""
    entity_type: LinkEntityType
    entity_id: UUID
    entity_code: Optional[str] = Field(None, max_length=100)
    link_type: str = Field(default="attachment", max_length=50)
    is_primary: bool = False
    description: Optional[str] = Field(None, max_length=500)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentLinkResponse(BaseModel):
    """Reponse lien document-entite."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    entity_type: LinkEntityType
    entity_id: UUID
    entity_code: Optional[str] = None
    link_type: str
    is_primary: bool
    description: Optional[str] = None
    metadata: Dict[str, Any]
    created_at: datetime
    created_by: Optional[UUID] = None


# =============================================================================
# SCHEMAS COMMENTAIRE
# =============================================================================

class CommentCreate(BaseModel):
    """Creation d'un commentaire."""
    content: str = Field(..., min_length=1)
    parent_id: Optional[UUID] = None
    page_number: Optional[int] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    mentions: List[UUID] = Field(default_factory=list)


class CommentUpdate(BaseModel):
    """Mise a jour d'un commentaire."""
    content: Optional[str] = None
    is_resolved: Optional[bool] = None


class CommentResponse(BaseModel):
    """Reponse commentaire."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    parent_id: Optional[UUID] = None
    content: str
    is_resolved: bool
    page_number: Optional[int] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    mentions: List[UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None

    # Computed
    replies: List["CommentResponse"] = Field(default_factory=list)


# =============================================================================
# SCHEMAS TAG
# =============================================================================

class TagCreate(BaseModel):
    """Creation d'un tag."""
    name: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = Field(None, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')
    description: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[UUID] = None


class TagUpdate(BaseModel):
    """Mise a jour d'un tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = None
    description: Optional[str] = None


class TagResponse(BaseModel):
    """Reponse tag."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    name: str
    slug: str
    color: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    document_count: int
    created_at: datetime


# =============================================================================
# SCHEMAS CATEGORIE
# =============================================================================

class CategoryCreate(BaseModel):
    """Creation d'une categorie."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=7)
    parent_id: Optional[UUID] = None
    default_retention: RetentionPolicy = RetentionPolicy.NONE
    required_metadata: List[str] = Field(default_factory=list)
    allowed_extensions: List[str] = Field(default_factory=list)
    max_file_size: Optional[int] = None


class CategoryUpdate(BaseModel):
    """Mise a jour d'une categorie."""
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    default_retention: Optional[RetentionPolicy] = None
    required_metadata: Optional[List[str]] = None
    allowed_extensions: Optional[List[str]] = None
    max_file_size: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    """Reponse categorie."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    code: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[UUID] = None
    level: int
    default_retention: RetentionPolicy
    required_metadata: List[str]
    allowed_extensions: List[str]
    max_file_size: Optional[int] = None
    document_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# =============================================================================
# SCHEMAS AUDIT
# =============================================================================

class AuditResponse(BaseModel):
    """Reponse audit."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: Optional[UUID] = None
    folder_id: Optional[UUID] = None
    document_code: Optional[str] = None
    document_name: Optional[str] = None
    action: AuditAction
    description: Optional[str] = None
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    ip_address: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    created_at: datetime


class AuditList(BaseModel):
    """Liste paginee d'audits."""
    items: List[AuditResponse]
    total: int
    page: int = 1
    page_size: int = 50
    pages: int = 1


# =============================================================================
# SCHEMAS RECHERCHE
# =============================================================================

class SearchQuery(BaseModel):
    """Requete de recherche."""
    query: str = Field(..., min_length=1, max_length=500)
    folder_id: Optional[UUID] = None
    include_subfolders: bool = True
    document_types: List[DocumentType] = Field(default_factory=list)
    categories: List[FileCategory] = Field(default_factory=list)
    statuses: List[DocumentStatus] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    extensions: List[str] = Field(default_factory=list)
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    created_by: Optional[UUID] = None
    full_text: bool = False  # Recherche dans le contenu


class SearchResult(BaseModel):
    """Resultat de recherche."""
    document: DocumentSummary
    score: float = 1.0
    highlights: List[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    """Reponse de recherche."""
    items: List[SearchResult]
    total: int
    query: str
    took_ms: int


# =============================================================================
# SCHEMAS STATISTIQUES
# =============================================================================

class StorageStats(BaseModel):
    """Statistiques de stockage."""
    total_documents: int
    total_folders: int
    total_size: int
    used_quota: int
    max_quota: Optional[int] = None
    usage_percent: float

    # Par categorie
    by_category: Dict[str, int]
    by_extension: Dict[str, int]
    by_status: Dict[str, int]

    # Activite
    uploads_today: int
    downloads_today: int
    shares_today: int


class DocumentStats(BaseModel):
    """Statistiques d'un document."""
    view_count: int
    download_count: int
    share_count: int
    comment_count: int
    version_count: int
    last_accessed_at: Optional[datetime] = None
    last_modified_at: datetime
    created_at: datetime


# =============================================================================
# SCHEMAS OPERATIONS BATCH
# =============================================================================

class BatchMoveRequest(BaseModel):
    """Requete de deplacement en lot."""
    document_ids: List[UUID] = Field(..., min_length=1)
    target_folder_id: Optional[UUID] = None


class BatchDeleteRequest(BaseModel):
    """Requete de suppression en lot."""
    document_ids: List[UUID] = Field(..., min_length=1)
    permanent: bool = False


class BatchTagRequest(BaseModel):
    """Requete d'ajout de tags en lot."""
    document_ids: List[UUID] = Field(..., min_length=1)
    tags: List[str] = Field(..., min_length=1)
    replace: bool = False  # Remplacer les tags existants


class BatchOperationResult(BaseModel):
    """Resultat d'operation en lot."""
    success_count: int
    failed_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# SCHEMAS CONFIGURATION
# =============================================================================

class StorageConfigUpdate(BaseModel):
    """Mise a jour configuration stockage."""
    enable_versioning: Optional[bool] = None
    enable_compression: Optional[bool] = None
    compression_threshold: Optional[int] = None
    enable_thumbnails: Optional[bool] = None
    enable_preview: Optional[bool] = None
    enable_ocr: Optional[bool] = None
    default_retention: Optional[RetentionPolicy] = None
    trash_retention_days: Optional[int] = None


class StorageConfigResponse(BaseModel):
    """Reponse configuration stockage."""
    model_config = ConfigDict(from_attributes=True)

    provider: str
    max_storage_bytes: Optional[int] = None
    max_file_size_bytes: Optional[int] = None
    used_storage_bytes: int
    enable_versioning: bool
    enable_compression: bool
    compression_threshold: int
    enable_thumbnails: bool
    enable_preview: bool
    enable_ocr: bool
    default_retention: RetentionPolicy
    trash_retention_days: int


# Resolve forward references
FolderTree.model_rebuild()
CommentResponse.model_rebuild()
