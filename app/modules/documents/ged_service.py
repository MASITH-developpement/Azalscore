"""
AZALS MODULE - Documents (GED) - Service Principal
===================================================

Service metier pour la Gestion Electronique de Documents.
Fonctionnalites completes: upload, versioning, partage, recherche, archivage.

Inspire de: Sage, Axonaut, Pennylane, Odoo, Microsoft Dynamics 365, SharePoint
"""
from __future__ import annotations


import hashlib
import io
import logging
import mimetypes
import os
import secrets
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from .exceptions import (
    DocumentAlreadyExistsError,
    DocumentLockedError,
    DocumentNotFoundError,
    DocumentRetentionError,
    DocumentStatusError,
    DocumentVersionError,
    FileCorruptedError,
    FileSizeLimitError,
    FileTypeNotAllowedError,
    FileUploadError,
    FolderAlreadyExistsError,
    FolderCircularReferenceError,
    FolderNotEmptyError,
    FolderNotFoundError,
    FolderSystemError,
    PermissionDeniedError,
    ShareDownloadLimitError,
    ShareExpiredError,
    ShareInvalidPasswordError,
    ShareNotFoundError,
    StorageQuotaExceededError,
)
from .models import (
    AccessLevel,
    AuditAction,
    CompressionStatus,
    Document,
    DocumentAudit,
    DocumentCategory,
    DocumentComment,
    DocumentLink,
    DocumentShare,
    DocumentStatus,
    DocumentTag,
    DocumentType,
    DocumentVersion,
    FileCategory,
    Folder,
    FolderPermission,
    LinkEntityType,
    RetentionPolicy,
    ShareType,
    StorageConfig,
    WorkflowStatus,
)
from .repository import (
    AuditRepository,
    CategoryRepository,
    CommentRepository,
    DocumentRepository,
    FolderRepository,
    LinkRepository,
    SequenceRepository,
    ShareRepository,
    StorageConfigRepository,
    TagRepository,
    VersionRepository,
)
from .schemas import (
    BatchOperationResult,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    DocumentLinkCreate,
    DocumentLinkResponse,
    DocumentResponse,
    DocumentUpdate,
    FolderCreate,
    FolderResponse,
    FolderTree,
    FolderUpdate,
    SearchQuery,
    SearchResponse,
    SearchResult,
    ShareCreate,
    ShareResponse,
    ShareUpdate,
    StorageStats,
    TagCreate,
    TagResponse,
    UploadResponse,
    VersionResponse,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTES
# =============================================================================

# Extensions autorisees par defaut
DEFAULT_ALLOWED_EXTENSIONS = {
    # Documents
    ".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt",
    # Tableurs
    ".xls", ".xlsx", ".ods", ".csv",
    # Presentations
    ".ppt", ".pptx", ".odp",
    # Images
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
    # Archives
    ".zip", ".rar", ".7z", ".tar", ".gz",
    # Audio/Video
    ".mp3", ".wav", ".mp4", ".avi", ".mkv", ".mov",
    # Autres
    ".json", ".xml", ".html", ".htm", ".eml", ".msg"
}

# Extensions dangereuses (jamais autorisees)
DANGEROUS_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".msi", ".dll",
    ".scr", ".pif", ".vbs", ".js", ".jar", ".ps1"
}

# Mapping extension -> categorie
EXTENSION_CATEGORY_MAP = {
    ".pdf": FileCategory.DOCUMENT,
    ".doc": FileCategory.DOCUMENT,
    ".docx": FileCategory.DOCUMENT,
    ".odt": FileCategory.DOCUMENT,
    ".rtf": FileCategory.DOCUMENT,
    ".txt": FileCategory.DOCUMENT,
    ".xls": FileCategory.SPREADSHEET,
    ".xlsx": FileCategory.SPREADSHEET,
    ".ods": FileCategory.SPREADSHEET,
    ".csv": FileCategory.DATA,
    ".ppt": FileCategory.PRESENTATION,
    ".pptx": FileCategory.PRESENTATION,
    ".odp": FileCategory.PRESENTATION,
    ".jpg": FileCategory.IMAGE,
    ".jpeg": FileCategory.IMAGE,
    ".png": FileCategory.IMAGE,
    ".gif": FileCategory.IMAGE,
    ".bmp": FileCategory.IMAGE,
    ".svg": FileCategory.IMAGE,
    ".webp": FileCategory.IMAGE,
    ".mp3": FileCategory.AUDIO,
    ".wav": FileCategory.AUDIO,
    ".mp4": FileCategory.VIDEO,
    ".avi": FileCategory.VIDEO,
    ".mkv": FileCategory.VIDEO,
    ".mov": FileCategory.VIDEO,
    ".zip": FileCategory.ARCHIVE,
    ".rar": FileCategory.ARCHIVE,
    ".7z": FileCategory.ARCHIVE,
    ".json": FileCategory.DATA,
    ".xml": FileCategory.DATA,
}

# Taille max par defaut (100 MB)
DEFAULT_MAX_FILE_SIZE = 100 * 1024 * 1024


# =============================================================================
# SERVICE GED
# =============================================================================

class GEDService:
    """
    Service principal de Gestion Electronique de Documents.

    PRINCIPES:
    - Isolation totale par tenant_id
    - Soft delete systematique
    - Audit trail complet
    - Versioning automatique
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        storage_path: Optional[str] = None,
        user_id: Optional[UUID] = None,
        user_email: Optional[str] = None
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.user_email = user_email

        # Repositories
        self.folders = FolderRepository(db, tenant_id)
        self.documents = DocumentRepository(db, tenant_id)
        self.versions = VersionRepository(db, tenant_id)
        self.shares = ShareRepository(db, tenant_id)
        self.links = LinkRepository(db, tenant_id)
        self.comments = CommentRepository(db, tenant_id)
        self.audit = AuditRepository(db, tenant_id)
        self.sequences = SequenceRepository(db, tenant_id)
        self.tags = TagRepository(db, tenant_id)
        self.categories = CategoryRepository(db, tenant_id)
        self.storage_config = StorageConfigRepository(db, tenant_id)

        # Configuration stockage
        self.storage_path = Path(storage_path) if storage_path else Path(f"/data/documents/{tenant_id}")
        self.storage_path.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # GESTION DES DOSSIERS
    # =========================================================================

    def create_folder(
        self,
        data: FolderCreate,
        user_id: Optional[UUID] = None
    ) -> FolderResponse:
        """Cree un nouveau dossier."""
        user_id = user_id or self.user_id

        # Verifier le parent
        parent = None
        parent_path = ""
        if data.parent_id:
            parent = self.folders.get_by_id(data.parent_id)
            if not parent:
                raise FolderNotFoundError(str(data.parent_id))
            parent_path = parent.path

        # Verifier unicite du nom
        existing = self.folders.find_by_name_in_parent(data.name, data.parent_id)
        if existing:
            raise FolderAlreadyExistsError(data.name, str(data.parent_id))

        # Creer le dossier
        folder = Folder(
            tenant_id=self.tenant_id,
            parent_id=data.parent_id,
            name=data.name,
            path=f"{parent_path}/{data.name}",
            level=parent.level + 1 if parent else 0,
            description=data.description,
            color=data.color,
            icon=data.icon,
            default_access_level=data.default_access_level,
            inherit_permissions=data.inherit_permissions,
            retention_policy=data.retention_policy,
            retention_days=data.retention_days,
            extra_data=data.metadata,  # Colonne renommee extra_data
            tags=data.tags,
            created_by=user_id
        )

        self.db.add(folder)
        self.db.commit()
        self.db.refresh(folder)

        # Mettre a jour stats parent
        if parent:
            self.folders.update_stats(parent.id)

        # Audit
        self._log_action(
            AuditAction.CREATE,
            folder_id=folder.id,
            description=f"Dossier cree: {folder.path}"
        )

        return FolderResponse.model_validate(folder)

    def get_folder(self, folder_id: UUID) -> Optional[FolderResponse]:
        """Recupere un dossier par ID."""
        folder = self.folders.get_by_id(folder_id)
        if not folder:
            return None
        return FolderResponse.model_validate(folder)

    def list_folders(
        self,
        parent_id: Optional[UUID] = None
    ) -> List[FolderResponse]:
        """Liste les sous-dossiers d'un dossier."""
        folders = self.folders.get_children(parent_id)
        return [FolderResponse.model_validate(f) for f in folders]

    def get_folder_tree(
        self,
        root_id: Optional[UUID] = None
    ) -> List[FolderTree]:
        """Recupere l'arbre des dossiers."""
        folders = self.folders.get_tree(root_id)

        # Construire l'arbre
        folder_map = {f.id: f for f in folders}
        tree = []

        for folder in folders:
            node = FolderTree(
                id=folder.id,
                name=folder.name,
                path=folder.path,
                level=folder.level,
                document_count=folder.document_count,
                color=folder.color,
                icon=folder.icon,
                children=[]
            )

            if folder.parent_id and folder.parent_id in folder_map:
                # Trouver le parent dans tree et ajouter ce node
                # (structure simplifiee ici)
                pass
            else:
                tree.append(node)

        return tree

    def update_folder(
        self,
        folder_id: UUID,
        data: FolderUpdate,
        user_id: Optional[UUID] = None
    ) -> Optional[FolderResponse]:
        """Met a jour un dossier."""
        folder = self.folders.get_by_id(folder_id)
        if not folder:
            return None

        if folder.is_system:
            raise FolderSystemError(str(folder_id), "update")

        old_path = folder.path
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(folder, field, value)

        folder.updated_by = user_id or self.user_id
        folder.version += 1

        # Si le nom a change, mettre a jour les chemins
        if data.name and data.name != folder.name:
            parent_path = "/".join(folder.path.split("/")[:-1])
            self.folders.update_path_recursive(folder_id, parent_path)

        self.db.commit()
        self.db.refresh(folder)

        # Audit
        self._log_action(
            AuditAction.UPDATE,
            folder_id=folder.id,
            description=f"Dossier modifie: {folder.path}",
            old_value={"path": old_path},
            new_value={"path": folder.path}
        )

        return FolderResponse.model_validate(folder)

    def delete_folder(
        self,
        folder_id: UUID,
        force: bool = False,
        user_id: Optional[UUID] = None
    ) -> bool:
        """Supprime un dossier (soft delete)."""
        folder = self.folders.get_by_id(folder_id)
        if not folder:
            return False

        if folder.is_system:
            raise FolderSystemError(str(folder_id), "delete")

        # Verifier si vide (sauf si force)
        if not force:
            doc_count, subfolder_count = self.folders.get_descendants_count(folder_id)
            if doc_count > 0 or subfolder_count > 0:
                raise FolderNotEmptyError(str(folder_id), doc_count, subfolder_count)

        folder.deleted_at = datetime.utcnow()
        folder.deleted_by = user_id or self.user_id
        folder.is_active = False

        self.db.commit()

        # Audit
        self._log_action(
            AuditAction.DELETE,
            folder_id=folder.id,
            description=f"Dossier supprime: {folder.path}"
        )

        return True

    def move_folder(
        self,
        folder_id: UUID,
        target_folder_id: Optional[UUID],
        user_id: Optional[UUID] = None
    ) -> FolderResponse:
        """Deplace un dossier."""
        folder = self.folders.get_by_id(folder_id)
        if not folder:
            raise FolderNotFoundError(str(folder_id))

        if folder.is_system:
            raise FolderSystemError(str(folder_id), "move")

        # Verifier le target
        target = None
        target_path = ""
        if target_folder_id:
            target = self.folders.get_by_id(target_folder_id)
            if not target:
                raise FolderNotFoundError(str(target_folder_id))
            target_path = target.path

            # Verifier reference circulaire
            if target.path.startswith(folder.path):
                raise FolderCircularReferenceError(str(folder_id), str(target_folder_id))

        old_path = folder.path
        old_parent_id = folder.parent_id

        # Mettre a jour
        folder.parent_id = target_folder_id
        self.folders.update_path_recursive(folder_id, target_path)

        # Mettre a jour stats
        if old_parent_id:
            self.folders.update_stats(old_parent_id)
        if target_folder_id:
            self.folders.update_stats(target_folder_id)

        self.db.refresh(folder)

        # Audit
        self._log_action(
            AuditAction.MOVE,
            folder_id=folder.id,
            description=f"Dossier deplace: {old_path} -> {folder.path}"
        )

        return FolderResponse.model_validate(folder)

    # =========================================================================
    # GESTION DES DOCUMENTS - UPLOAD
    # =========================================================================

    def upload_document(
        self,
        file_content: Union[bytes, BinaryIO],
        filename: str,
        folder_id: Optional[UUID] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[FileCategory] = None,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
        retention_policy: RetentionPolicy = RetentionPolicy.NONE,
        user_id: Optional[UUID] = None
    ) -> UploadResponse:
        """
        Upload un nouveau document.

        Args:
            file_content: Contenu du fichier (bytes ou file-like)
            filename: Nom du fichier original
            folder_id: Dossier de destination
            title: Titre du document
            description: Description
            category: Categorie de fichier
            tags: Tags
            metadata: Metadonnees personnalisees
            retention_policy: Politique de retention
            user_id: Utilisateur
        """
        user_id = user_id or self.user_id

        # Lire le contenu si file-like
        if hasattr(file_content, 'read'):
            content = file_content.read()
        else:
            content = file_content

        # Validation extension
        extension = Path(filename).suffix.lower()
        if extension in DANGEROUS_EXTENSIONS:
            raise FileTypeNotAllowedError(extension, list(DEFAULT_ALLOWED_EXTENSIONS))

        config = self.storage_config.get_or_create()
        if config.max_file_size_bytes and len(content) > config.max_file_size_bytes:
            raise FileSizeLimitError(len(content), config.max_file_size_bytes)

        # Quota
        if config.max_storage_bytes:
            if config.used_storage_bytes + len(content) > config.max_storage_bytes:
                raise StorageQuotaExceededError(
                    config.used_storage_bytes,
                    config.max_storage_bytes,
                    len(content)
                )

        # Verifier le dossier
        folder = None
        if folder_id:
            folder = self.folders.get_by_id(folder_id)
            if not folder:
                raise FolderNotFoundError(str(folder_id))

        # Calculer checksum
        checksum = hashlib.sha256(content).hexdigest()

        # Generer code
        code = self.sequences.get_next_code("DOC")

        # Determiner categorie
        if not category:
            category = EXTENSION_CATEGORY_MAP.get(extension, FileCategory.OTHER)

        # Determiner MIME type
        mime_type, _ = mimetypes.guess_type(filename)

        # Stocker le fichier
        storage_path = self._store_file(content, code, extension)

        # Creer le document
        document = Document(
            tenant_id=self.tenant_id,
            code=code,
            folder_id=folder_id,
            document_type=DocumentType.FILE,
            status=DocumentStatus.ACTIVE,
            category=category,
            name=filename,
            title=title or filename,
            description=description,
            file_extension=extension,
            mime_type=mime_type,
            file_size=len(content),
            storage_path=str(storage_path),
            storage_provider="local",
            checksum=checksum,
            current_version=1,
            is_latest=True,
            retention_policy=retention_policy,
            metadata=metadata or {},
            tags=tags or [],
            created_by=user_id
        )

        # Calculer retention
        if retention_policy != RetentionPolicy.NONE:
            document.retention_until = self._calculate_retention_date(retention_policy)

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        # Creer version initiale
        version = DocumentVersion(
            tenant_id=self.tenant_id,
            document_id=document.id,
            version_number=1,
            file_size=len(content),
            storage_path=str(storage_path),
            checksum=checksum,
            change_summary="Version initiale",
            change_type="MAJOR",
            created_by=user_id
        )
        self.db.add(version)

        # Mettre a jour stats dossier
        if folder:
            self.folders.update_stats(folder.id)

        # Mettre a jour quota
        self.storage_config.update_used_storage(len(content))

        self.db.commit()

        # Audit
        self._log_action(
            AuditAction.CREATE,
            document_id=document.id,
            document_code=code,
            document_name=filename,
            description=f"Document uploade: {filename}"
        )

        return UploadResponse(
            document_id=document.id,
            code=code,
            name=filename,
            file_size=len(content),
            mime_type=mime_type,
            checksum=checksum,
            storage_path=str(storage_path),
            version=1,
            created_at=document.created_at
        )

    def _store_file(
        self,
        content: bytes,
        code: str,
        extension: str
    ) -> Path:
        """Stocke un fichier sur le systeme de fichiers."""
        # Structure: /data/documents/{tenant_id}/{YYYY}/{MM}/{code}{ext}
        today = datetime.utcnow()
        dir_path = self.storage_path / str(today.year) / f"{today.month:02d}"
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / f"{code}{extension}"
        with open(file_path, "wb") as f:
            f.write(content)

        return file_path

    def _calculate_retention_date(self, policy: RetentionPolicy) -> datetime:
        """Calcule la date de fin de retention."""
        now = datetime.utcnow()
        if policy == RetentionPolicy.SHORT:
            return now + timedelta(days=365)
        elif policy == RetentionPolicy.MEDIUM:
            return now + timedelta(days=365 * 3)
        elif policy == RetentionPolicy.LONG:
            return now + timedelta(days=365 * 5)
        elif policy == RetentionPolicy.LEGAL:
            return now + timedelta(days=365 * 10)
        elif policy == RetentionPolicy.PERMANENT:
            return now + timedelta(days=365 * 100)
        return now

    # =========================================================================
    # GESTION DES DOCUMENTS - CRUD
    # =========================================================================

    def get_document(
        self,
        document_id: UUID,
        log_access: bool = True
    ) -> Optional[DocumentResponse]:
        """Recupere un document par ID."""
        document = self.documents.get_by_id(document_id)
        if not document:
            return None

        if log_access and self.user_id:
            self.documents.increment_view_count(document_id, self.user_id)
            self._log_action(
                AuditAction.READ,
                document_id=document.id,
                document_code=document.code,
                document_name=document.name
            )

        return DocumentResponse.model_validate(document)

    def get_document_by_code(self, code: str) -> Optional[DocumentResponse]:
        """Recupere un document par code."""
        document = self.documents.find_by_code(code)
        if not document:
            return None
        return DocumentResponse.model_validate(document)

    def list_documents(
        self,
        folder_id: Optional[UUID] = None,
        include_subfolders: bool = False,
        status: Optional[DocumentStatus] = None,
        category: Optional[FileCategory] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[DocumentResponse], int]:
        """Liste les documents."""
        skip = (page - 1) * page_size
        documents, total = self.documents.list_by_folder(
            folder_id=folder_id,
            include_subfolders=include_subfolders,
            skip=skip,
            limit=page_size,
            status=status,
            category=category
        )

        return [DocumentResponse.model_validate(d) for d in documents], total

    def update_document(
        self,
        document_id: UUID,
        data: DocumentUpdate,
        user_id: Optional[UUID] = None
    ) -> Optional[DocumentResponse]:
        """Met a jour les metadonnees d'un document."""
        document = self.documents.get_by_id(document_id)
        if not document:
            return None

        # Verifier verrouillage
        if document.is_locked and document.locked_by != (user_id or self.user_id):
            raise DocumentLockedError(str(document_id), str(document.locked_by))

        old_values = {
            "name": document.name,
            "title": document.title,
            "folder_id": str(document.folder_id) if document.folder_id else None
        }

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(document, field, value)

        document.updated_by = user_id or self.user_id
        document.version += 1

        self.db.commit()
        self.db.refresh(document)

        # Audit
        self._log_action(
            AuditAction.UPDATE,
            document_id=document.id,
            document_code=document.code,
            document_name=document.name,
            old_value=old_values,
            new_value=update_data
        )

        return DocumentResponse.model_validate(document)

    def delete_document(
        self,
        document_id: UUID,
        permanent: bool = False,
        user_id: Optional[UUID] = None
    ) -> bool:
        """Supprime un document."""
        document = self.documents.get_by_id(document_id)
        if not document:
            return False

        # Verifier retention
        if document.retention_until and document.retention_until > datetime.utcnow():
            raise DocumentRetentionError(
                str(document_id),
                document.retention_until.isoformat()
            )

        if permanent:
            # Supprimer le fichier
            if document.storage_path:
                try:
                    Path(document.storage_path).unlink(missing_ok=True)
                except Exception as e:
                    logger.error(f"Erreur suppression fichier: {e}")

            # Mettre a jour quota
            self.storage_config.update_used_storage(-document.file_size)

            # Supprimer en base
            self.db.delete(document)
            self.db.commit()

            action = AuditAction.DELETE
        else:
            # Soft delete
            document.deleted_at = datetime.utcnow()
            document.deleted_by = user_id or self.user_id
            document.is_active = False
            document.status = DocumentStatus.DELETED

            self.db.commit()

            action = AuditAction.ARCHIVE

        # Mettre a jour stats dossier
        if document.folder_id:
            self.folders.update_stats(document.folder_id)

        # Audit
        self._log_action(
            action,
            document_id=document.id,
            document_code=document.code,
            document_name=document.name,
            description="Suppression permanente" if permanent else "Suppression (corbeille)"
        )

        return True

    def restore_document(
        self,
        document_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[DocumentResponse]:
        """Restaure un document supprime."""
        document = self.db.query(Document).filter(
            Document.tenant_id == self.tenant_id,
            Document.id == document_id,
            Document.deleted_at.isnot(None)
        ).first()

        if not document:
            return None

        document.deleted_at = None
        document.deleted_by = None
        document.is_active = True
        document.status = DocumentStatus.ACTIVE

        self.db.commit()
        self.db.refresh(document)

        # Mettre a jour stats dossier
        if document.folder_id:
            self.folders.update_stats(document.folder_id)

        # Audit
        self._log_action(
            AuditAction.RESTORE,
            document_id=document.id,
            document_code=document.code,
            document_name=document.name
        )

        return DocumentResponse.model_validate(document)

    # =========================================================================
    # TELECHARGEMENT
    # =========================================================================

    def download_document(
        self,
        document_id: UUID,
        version: Optional[int] = None,
        user_id: Optional[UUID] = None
    ) -> Tuple[bytes, str, str]:
        """
        Telecharge un document.

        Returns:
            Tuple (content, filename, mime_type)
        """
        document = self.documents.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(str(document_id))

        # Version specifique?
        if version and version != document.current_version:
            doc_version = self.versions.get_version(document_id, version)
            if not doc_version:
                raise DocumentNotFoundError(
                    str(document_id),
                    f"Version {version} non trouvee"
                )
            storage_path = doc_version.storage_path
            checksum = doc_version.checksum
        else:
            storage_path = document.storage_path
            checksum = document.checksum

        # Lire le fichier
        if not storage_path or not Path(storage_path).exists():
            raise DocumentNotFoundError(str(document_id), "Fichier non trouve")

        with open(storage_path, "rb") as f:
            content = f.read()

        # Verifier integrite
        actual_checksum = hashlib.sha256(content).hexdigest()
        if checksum and actual_checksum != checksum:
            raise FileCorruptedError(str(document_id), checksum, actual_checksum)

        # Stats
        self.documents.increment_download_count(document_id)

        # Audit
        self._log_action(
            AuditAction.DOWNLOAD,
            document_id=document.id,
            document_code=document.code,
            document_name=document.name,
            metadata={"version": version or document.current_version}
        )

        return content, document.name, document.mime_type or "application/octet-stream"

    # =========================================================================
    # VERSIONING
    # =========================================================================

    def upload_new_version(
        self,
        document_id: UUID,
        file_content: Union[bytes, BinaryIO],
        change_summary: Optional[str] = None,
        change_type: str = "MINOR",
        user_id: Optional[UUID] = None
    ) -> VersionResponse:
        """Upload une nouvelle version d'un document."""
        user_id = user_id or self.user_id

        document = self.documents.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(str(document_id))

        # Verifier verrouillage
        if document.is_locked and document.locked_by != user_id:
            raise DocumentLockedError(str(document_id), str(document.locked_by))

        # Lire le contenu
        if hasattr(file_content, 'read'):
            content = file_content.read()
        else:
            content = file_content

        # Quota
        config = self.storage_config.get_or_create()
        size_delta = len(content) - document.file_size
        if config.max_storage_bytes and size_delta > 0:
            if config.used_storage_bytes + size_delta > config.max_storage_bytes:
                raise StorageQuotaExceededError(
                    config.used_storage_bytes,
                    config.max_storage_bytes,
                    size_delta
                )

        # Calculer checksum
        checksum = hashlib.sha256(content).hexdigest()

        # Stocker le fichier
        new_version_number = document.current_version + 1
        storage_path = self._store_file(
            content,
            f"{document.code}_v{new_version_number}",
            document.file_extension or ""
        )

        # Creer la version
        version = DocumentVersion(
            tenant_id=self.tenant_id,
            document_id=document_id,
            version_number=new_version_number,
            file_size=len(content),
            storage_path=str(storage_path),
            checksum=checksum,
            change_summary=change_summary,
            change_type=change_type,
            created_by=user_id
        )
        self.db.add(version)

        # Mettre a jour le document
        document.current_version = new_version_number
        document.file_size = len(content)
        document.storage_path = str(storage_path)
        document.checksum = checksum
        document.updated_by = user_id
        document.version += 1

        # Mettre a jour quota
        self.storage_config.update_used_storage(size_delta)

        self.db.commit()
        self.db.refresh(version)

        # Audit
        self._log_action(
            AuditAction.VERSION,
            document_id=document.id,
            document_code=document.code,
            document_name=document.name,
            description=f"Nouvelle version {new_version_number}",
            metadata={"version": new_version_number, "change_type": change_type}
        )

        return VersionResponse.model_validate(version)

    def get_versions(
        self,
        document_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[VersionResponse], int]:
        """Liste les versions d'un document."""
        skip = (page - 1) * page_size
        versions, total = self.versions.get_versions(document_id, skip, page_size)
        return [VersionResponse.model_validate(v) for v in versions], total

    def restore_version(
        self,
        document_id: UUID,
        version_number: int,
        user_id: Optional[UUID] = None
    ) -> DocumentResponse:
        """Restaure une ancienne version comme version courante."""
        document = self.documents.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(str(document_id))

        version = self.versions.get_version(document_id, version_number)
        if not version:
            raise DocumentNotFoundError(str(document_id), f"Version {version_number} non trouvee")

        # Creer une nouvelle version avec le contenu de l'ancienne
        with open(version.storage_path, "rb") as f:
            content = f.read()

        new_version = self.upload_new_version(
            document_id,
            content,
            change_summary=f"Restauration de la version {version_number}",
            change_type="REVISION",
            user_id=user_id
        )

        self.db.refresh(document)
        return DocumentResponse.model_validate(document)

    # =========================================================================
    # VERROUILLAGE
    # =========================================================================

    def lock_document(
        self,
        document_id: UUID,
        reason: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> DocumentResponse:
        """Verrouille un document."""
        user_id = user_id or self.user_id
        document = self.documents.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(str(document_id))

        if document.is_locked:
            if document.locked_by == user_id:
                return DocumentResponse.model_validate(document)
            raise DocumentLockedError(str(document_id), str(document.locked_by))

        document.is_locked = True
        document.locked_by = user_id
        document.locked_at = datetime.utcnow()
        document.lock_reason = reason

        self.db.commit()
        self.db.refresh(document)

        # Audit
        self._log_action(
            AuditAction.LOCK,
            document_id=document.id,
            document_code=document.code,
            document_name=document.name
        )

        return DocumentResponse.model_validate(document)

    def unlock_document(
        self,
        document_id: UUID,
        force: bool = False,
        user_id: Optional[UUID] = None
    ) -> DocumentResponse:
        """Deverrouille un document."""
        user_id = user_id or self.user_id
        document = self.documents.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(str(document_id))

        if not document.is_locked:
            return DocumentResponse.model_validate(document)

        if document.locked_by != user_id and not force:
            raise DocumentLockedError(str(document_id), str(document.locked_by))

        document.is_locked = False
        document.locked_by = None
        document.locked_at = None
        document.lock_reason = None

        self.db.commit()
        self.db.refresh(document)

        # Audit
        self._log_action(
            AuditAction.UNLOCK,
            document_id=document.id,
            document_code=document.code,
            document_name=document.name
        )

        return DocumentResponse.model_validate(document)

    # =========================================================================
    # PARTAGE
    # =========================================================================

    def create_share(
        self,
        document_id: UUID,
        data: ShareCreate,
        user_id: Optional[UUID] = None
    ) -> ShareResponse:
        """Cree un partage."""
        document = self.documents.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(str(document_id))

        share = DocumentShare(
            tenant_id=self.tenant_id,
            document_id=document_id,
            share_type=data.share_type,
            access_level=data.access_level,
            shared_with_user_id=data.user_id,
            shared_with_role=data.role,
            shared_with_department=data.department,
            shared_with_email=data.email,
            can_download=data.can_download,
            can_print=data.can_print,
            can_share=data.can_share,
            notify_on_access=data.notify_on_access,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            created_by=user_id or self.user_id
        )

        # Generer lien si demande
        if data.generate_link or data.share_type == ShareType.PUBLIC:
            share.share_link = secrets.token_urlsafe(32)
            share.share_link_expires_at = data.valid_until
            share.share_link_max_downloads = data.link_max_downloads
            if data.link_password:
                share.share_link_password = hashlib.sha256(
                    data.link_password.encode()
                ).hexdigest()

        self.db.add(share)

        # Mettre a jour compteur
        document.share_count += 1

        self.db.commit()
        self.db.refresh(share)

        # Audit
        self._log_action(
            AuditAction.SHARE,
            document_id=document.id,
            document_code=document.code,
            document_name=document.name,
            description=f"Partage {data.share_type.value} cree"
        )

        return ShareResponse.model_validate(share)

    def get_share_by_link(
        self,
        share_link: str,
        password: Optional[str] = None
    ) -> Tuple[ShareResponse, DocumentResponse]:
        """Accede a un document via lien de partage."""
        share = self.shares.get_by_link(share_link)
        if not share:
            raise ShareNotFoundError(share_link)

        # Verifier expiration
        if share.share_link_expires_at and share.share_link_expires_at < datetime.utcnow():
            raise ShareExpiredError(str(share.id), share.share_link_expires_at.isoformat())

        # Verifier mot de passe
        if share.share_link_password:
            if not password:
                raise ShareInvalidPasswordError(str(share.id))
            hashed = hashlib.sha256(password.encode()).hexdigest()
            if hashed != share.share_link_password:
                raise ShareInvalidPasswordError(str(share.id))

        # Verifier limite telechargements
        if share.share_link_max_downloads:
            if share.share_link_download_count >= share.share_link_max_downloads:
                raise ShareDownloadLimitError(str(share.id), share.share_link_max_downloads)

        document = self.documents.get_by_id(share.document_id)
        if not document:
            raise DocumentNotFoundError(str(share.document_id))

        return ShareResponse.model_validate(share), DocumentResponse.model_validate(document)

    def revoke_share(
        self,
        share_id: UUID,
        user_id: Optional[UUID] = None
    ) -> bool:
        """Revoque un partage."""
        share = self.shares.get_by_id(share_id)
        if not share:
            return False

        share.is_active = False
        share.revoked_at = datetime.utcnow()
        share.revoked_by = user_id or self.user_id

        self.db.commit()

        # Audit
        self._log_action(
            AuditAction.UNSHARE,
            document_id=share.document_id,
            description="Partage revoque"
        )

        return True

    # =========================================================================
    # LIENS AVEC ENTITES
    # =========================================================================

    def link_to_entity(
        self,
        document_id: UUID,
        data: DocumentLinkCreate,
        user_id: Optional[UUID] = None
    ) -> DocumentLinkResponse:
        """Lie un document a une entite."""
        document = self.documents.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(str(document_id))

        # Verifier si lien existe deja
        existing = self.links.find_link(document_id, data.entity_type, data.entity_id)
        if existing:
            return DocumentLinkResponse.model_validate(existing)

        link = DocumentLink(
            tenant_id=self.tenant_id,
            document_id=document_id,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            entity_code=data.entity_code,
            link_type=data.link_type,
            is_primary=data.is_primary,
            description=data.description,
            extra_data=data.metadata,  # Colonne renommee extra_data
            created_by=user_id or self.user_id
        )

        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)

        return DocumentLinkResponse.model_validate(link)

    def get_entity_documents(
        self,
        entity_type: LinkEntityType,
        entity_id: UUID
    ) -> List[DocumentResponse]:
        """Recupere les documents lies a une entite."""
        documents = self.documents.list_by_entity(entity_type, entity_id)
        return [DocumentResponse.model_validate(d) for d in documents]

    def unlink_from_entity(
        self,
        document_id: UUID,
        entity_type: LinkEntityType,
        entity_id: UUID
    ) -> bool:
        """Supprime le lien entre un document et une entite."""
        link = self.links.find_link(document_id, entity_type, entity_id)
        if not link:
            return False

        self.db.delete(link)
        self.db.commit()
        return True

    # =========================================================================
    # RECHERCHE
    # =========================================================================

    def search(
        self,
        query: SearchQuery,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResponse:
        """Recherche dans les documents."""
        import time
        start = time.time()

        skip = (page - 1) * page_size

        filters = {}
        if query.document_types:
            filters["document_type"] = query.document_types[0]  # Simplifie
        if query.categories:
            filters["category"] = query.categories[0]
        if query.statuses:
            filters["status"] = query.statuses[0]
        if query.tags:
            filters["tags"] = query.tags
        if query.extensions:
            filters["extensions"] = query.extensions
        if query.min_size:
            filters["min_size"] = query.min_size
        if query.max_size:
            filters["max_size"] = query.max_size
        if query.created_from:
            filters["created_from"] = query.created_from
        if query.created_to:
            filters["created_to"] = query.created_to
        if query.created_by:
            filters["created_by"] = query.created_by

        documents, total = self.documents.search(
            query_text=query.query,
            folder_id=query.folder_id,
            include_content=query.full_text,
            filters=filters,
            skip=skip,
            limit=page_size
        )

        results = []
        from .schemas import DocumentSummary
        for doc in documents:
            results.append(SearchResult(
                document=DocumentSummary.model_validate(doc),
                score=1.0,
                highlights=[]
            ))

        took_ms = int((time.time() - start) * 1000)

        return SearchResponse(
            items=results,
            total=total,
            query=query.query,
            took_ms=took_ms
        )

    # =========================================================================
    # COMMENTAIRES
    # =========================================================================

    def add_comment(
        self,
        document_id: UUID,
        data: CommentCreate,
        user_id: Optional[UUID] = None
    ) -> CommentResponse:
        """Ajoute un commentaire."""
        document = self.documents.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(str(document_id))

        comment = DocumentComment(
            tenant_id=self.tenant_id,
            document_id=document_id,
            parent_id=data.parent_id,
            content=data.content,
            page_number=data.page_number,
            position_x=data.position_x,
            position_y=data.position_y,
            mentions=[str(m) for m in data.mentions],
            created_by=user_id or self.user_id
        )

        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)

        return CommentResponse.model_validate(comment)

    def get_comments(
        self,
        document_id: UUID
    ) -> List[CommentResponse]:
        """Liste les commentaires d'un document."""
        comments = self.comments.get_document_comments(document_id)
        return [CommentResponse.model_validate(c) for c in comments]

    def delete_comment(
        self,
        comment_id: UUID,
        user_id: Optional[UUID] = None
    ) -> bool:
        """Supprime un commentaire."""
        return self.comments.delete(comment_id, soft=True)

    # =========================================================================
    # TAGS ET CATEGORIES
    # =========================================================================

    def create_tag(
        self,
        data: TagCreate,
        user_id: Optional[UUID] = None
    ) -> TagResponse:
        """Cree un tag."""
        slug = data.name.lower().replace(" ", "-")
        existing = self.tags.find_by_slug(slug)
        if existing:
            return TagResponse.model_validate(existing)

        tag = DocumentTag(
            tenant_id=self.tenant_id,
            name=data.name,
            slug=slug,
            color=data.color,
            description=data.description,
            parent_id=data.parent_id,
            created_by=user_id or self.user_id
        )

        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)

        return TagResponse.model_validate(tag)

    def get_tags(self) -> List[TagResponse]:
        """Liste les tags."""
        tags, _ = self.tags.list_all()
        return [TagResponse.model_validate(t) for t in tags]

    def create_category(
        self,
        data: CategoryCreate,
        user_id: Optional[UUID] = None
    ) -> CategoryResponse:
        """Cree une categorie."""
        existing = self.categories.find_by_code(data.code)
        if existing:
            raise DocumentAlreadyExistsError(data.code)

        category = DocumentCategory(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            icon=data.icon,
            color=data.color,
            parent_id=data.parent_id,
            default_retention=data.default_retention,
            required_metadata=data.required_metadata,
            allowed_extensions=data.allowed_extensions,
            max_file_size=data.max_file_size,
            created_by=user_id or self.user_id
        )

        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)

        return CategoryResponse.model_validate(category)

    def get_categories(self) -> List[CategoryResponse]:
        """Liste les categories."""
        categories = self.categories.get_active()
        return [CategoryResponse.model_validate(c) for c in categories]

    # =========================================================================
    # OPERATIONS EN LOT
    # =========================================================================

    def batch_move(
        self,
        document_ids: List[UUID],
        target_folder_id: Optional[UUID],
        user_id: Optional[UUID] = None
    ) -> BatchOperationResult:
        """Deplace plusieurs documents."""
        success_count = 0
        failed_count = 0
        errors = []

        for doc_id in document_ids:
            try:
                document = self.documents.get_by_id(doc_id)
                if document:
                    document.folder_id = target_folder_id
                    document.updated_by = user_id or self.user_id
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append({"document_id": str(doc_id), "error": "Document non trouve"})
            except Exception as e:
                failed_count += 1
                errors.append({"document_id": str(doc_id), "error": str(e)})

        self.db.commit()

        return BatchOperationResult(
            success_count=success_count,
            failed_count=failed_count,
            errors=errors
        )

    def batch_delete(
        self,
        document_ids: List[UUID],
        permanent: bool = False,
        user_id: Optional[UUID] = None
    ) -> BatchOperationResult:
        """Supprime plusieurs documents."""
        success_count = 0
        failed_count = 0
        errors = []

        for doc_id in document_ids:
            try:
                if self.delete_document(doc_id, permanent=permanent, user_id=user_id):
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append({"document_id": str(doc_id), "error": "Document non trouve"})
            except Exception as e:
                failed_count += 1
                errors.append({"document_id": str(doc_id), "error": str(e)})

        return BatchOperationResult(
            success_count=success_count,
            failed_count=failed_count,
            errors=errors
        )

    def batch_tag(
        self,
        document_ids: List[UUID],
        tags: List[str],
        replace: bool = False,
        user_id: Optional[UUID] = None
    ) -> BatchOperationResult:
        """Ajoute des tags a plusieurs documents."""
        success_count = 0
        failed_count = 0
        errors = []

        for doc_id in document_ids:
            try:
                document = self.documents.get_by_id(doc_id)
                if document:
                    if replace:
                        document.tags = tags
                    else:
                        existing = set(document.tags or [])
                        existing.update(tags)
                        document.tags = list(existing)
                    document.updated_by = user_id or self.user_id
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append({"document_id": str(doc_id), "error": "Document non trouve"})
            except Exception as e:
                failed_count += 1
                errors.append({"document_id": str(doc_id), "error": str(e)})

        self.db.commit()

        return BatchOperationResult(
            success_count=success_count,
            failed_count=failed_count,
            errors=errors
        )

    # =========================================================================
    # ARCHIVAGE ET COMPRESSION
    # =========================================================================

    def archive_documents(
        self,
        document_ids: List[UUID],
        archive_name: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> UploadResponse:
        """Archive plusieurs documents dans un ZIP."""
        user_id = user_id or self.user_id

        # Creer archive en memoire
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for doc_id in document_ids:
                try:
                    content, filename, _ = self.download_document(doc_id, user_id=user_id)
                    zip_file.writestr(filename, content)
                except Exception as e:
                    logger.error(f"Erreur archivage document {doc_id}: {e}")

        zip_buffer.seek(0)
        zip_content = zip_buffer.read()

        # Upload l'archive
        if not archive_name:
            archive_name = f"archive_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"

        return self.upload_document(
            file_content=zip_content,
            filename=archive_name,
            category=FileCategory.ARCHIVE,
            user_id=user_id
        )

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def get_storage_stats(self) -> StorageStats:
        """Recupere les statistiques de stockage."""
        stats = self.documents.get_statistics()
        config = self.storage_config.get_or_create()

        folder_count = self.db.query(Folder).filter(
            Folder.tenant_id == self.tenant_id,
            Folder.deleted_at.is_(None)
        ).count()

        usage_percent = 0.0
        if config.max_storage_bytes and config.max_storage_bytes > 0:
            usage_percent = (config.used_storage_bytes / config.max_storage_bytes) * 100

        # Activite du jour
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        uploads_today = self.db.query(DocumentAudit).filter(
            DocumentAudit.tenant_id == self.tenant_id,
            DocumentAudit.action == AuditAction.CREATE,
            DocumentAudit.created_at >= today_start
        ).count()

        downloads_today = self.db.query(DocumentAudit).filter(
            DocumentAudit.tenant_id == self.tenant_id,
            DocumentAudit.action == AuditAction.DOWNLOAD,
            DocumentAudit.created_at >= today_start
        ).count()

        shares_today = self.db.query(DocumentAudit).filter(
            DocumentAudit.tenant_id == self.tenant_id,
            DocumentAudit.action == AuditAction.SHARE,
            DocumentAudit.created_at >= today_start
        ).count()

        return StorageStats(
            total_documents=stats["total_count"],
            total_folders=folder_count,
            total_size=stats["total_size"],
            used_quota=config.used_storage_bytes,
            max_quota=config.max_storage_bytes,
            usage_percent=usage_percent,
            by_category={str(k): v for k, v in stats["by_category"].items()},
            by_extension=stats["by_extension"],
            by_status={str(k): v for k, v in stats["by_status"].items()},
            uploads_today=uploads_today,
            downloads_today=downloads_today,
            shares_today=shares_today
        )

    # =========================================================================
    # AUDIT
    # =========================================================================

    def _log_action(
        self,
        action: AuditAction,
        document_id: Optional[UUID] = None,
        folder_id: Optional[UUID] = None,
        document_code: Optional[str] = None,
        document_name: Optional[str] = None,
        description: Optional[str] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """Enregistre une action d'audit."""
        try:
            self.audit.log_action(
                action=action,
                user_id=self.user_id,
                user_email=self.user_email,
                document_id=document_id,
                folder_id=folder_id,
                document_code=document_code,
                document_name=document_name,
                description=description,
                old_value=old_value,
                new_value=new_value,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Erreur audit: {e}")

    def get_audit_history(
        self,
        document_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List["AuditResponse"], int]:
        """Recupere l'historique d'audit d'un document."""
        from .schemas import AuditResponse
        skip = (page - 1) * page_size
        audits, total = self.audit.get_document_history(document_id, skip, page_size)
        return [AuditResponse.model_validate(a) for a in audits], total

    # =========================================================================
    # MAINTENANCE
    # =========================================================================

    def purge_deleted_documents(
        self,
        older_than_days: int = 30
    ) -> int:
        """Purge les documents supprimes depuis plus de X jours."""
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        documents = self.documents.get_deleted_for_purge(cutoff_date)

        count = 0
        for doc in documents:
            try:
                # Supprimer le fichier
                if doc.storage_path:
                    Path(doc.storage_path).unlink(missing_ok=True)

                # Mettre a jour quota
                self.storage_config.update_used_storage(-doc.file_size)

                # Supprimer en base
                self.db.delete(doc)
                count += 1
            except Exception as e:
                logger.error(f"Erreur purge document {doc.id}: {e}")

        self.db.commit()
        return count

    def apply_retention_policy(self) -> int:
        """Applique les politiques de retention (archive les documents expires)."""
        documents = self.documents.get_pending_retention(datetime.utcnow())

        count = 0
        for doc in documents:
            try:
                doc.status = DocumentStatus.ARCHIVED
                doc.purge_scheduled_at = datetime.utcnow() + timedelta(days=30)
                count += 1
            except Exception as e:
                logger.error(f"Erreur retention document {doc.id}: {e}")

        self.db.commit()
        return count


# =============================================================================
# FACTORY
# =============================================================================

def get_ged_service(
    db: Session,
    tenant_id: str,
    user_id: Optional[UUID] = None,
    user_email: Optional[str] = None,
    storage_path: Optional[str] = None
) -> GEDService:
    """Factory pour creer un service GED."""
    return GEDService(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        user_email=user_email,
        storage_path=storage_path
    )
