"""
AZALS MODULE - Documents (GED) - Exceptions
============================================

Exceptions personnalisees pour le module documents.
"""
from __future__ import annotations


from typing import Any, Dict, Optional


class DocumentException(Exception):
    """Exception de base pour le module documents."""

    def __init__(
        self,
        message: str,
        code: str = "DOCUMENT_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


# =============================================================================
# EXCEPTIONS DOCUMENT
# =============================================================================

class DocumentNotFoundError(DocumentException):
    """Document non trouve."""

    def __init__(self, document_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Document non trouve: {document_id}",
            code="DOCUMENT_NOT_FOUND",
            details={"document_id": document_id}
        )


class DocumentAlreadyExistsError(DocumentException):
    """Document existe deja."""

    def __init__(self, name: str, folder_id: Optional[str] = None):
        super().__init__(
            message=f"Un document avec le nom '{name}' existe deja dans ce dossier",
            code="DOCUMENT_ALREADY_EXISTS",
            details={"name": name, "folder_id": folder_id}
        )


class DocumentLockedError(DocumentException):
    """Document verrouille."""

    def __init__(self, document_id: str, locked_by: str):
        super().__init__(
            message=f"Le document est verrouille par un autre utilisateur",
            code="DOCUMENT_LOCKED",
            details={"document_id": document_id, "locked_by": locked_by}
        )


class DocumentVersionError(DocumentException):
    """Erreur de version (conflit)."""

    def __init__(self, document_id: str, expected_version: int, actual_version: int):
        super().__init__(
            message="Conflit de version: le document a ete modifie",
            code="DOCUMENT_VERSION_CONFLICT",
            details={
                "document_id": document_id,
                "expected_version": expected_version,
                "actual_version": actual_version
            }
        )


class DocumentStatusError(DocumentException):
    """Operation non permise pour ce statut."""

    def __init__(self, document_id: str, status: str, operation: str):
        super().__init__(
            message=f"Operation '{operation}' non permise pour un document en statut '{status}'",
            code="DOCUMENT_INVALID_STATUS",
            details={
                "document_id": document_id,
                "status": status,
                "operation": operation
            }
        )


class DocumentRetentionError(DocumentException):
    """Document sous retention."""

    def __init__(self, document_id: str, retention_until: str):
        super().__init__(
            message=f"Le document est sous retention jusqu'au {retention_until}",
            code="DOCUMENT_UNDER_RETENTION",
            details={
                "document_id": document_id,
                "retention_until": retention_until
            }
        )


# =============================================================================
# EXCEPTIONS DOSSIER
# =============================================================================

class FolderNotFoundError(DocumentException):
    """Dossier non trouve."""

    def __init__(self, folder_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Dossier non trouve: {folder_id}",
            code="FOLDER_NOT_FOUND",
            details={"folder_id": folder_id}
        )


class FolderAlreadyExistsError(DocumentException):
    """Dossier existe deja."""

    def __init__(self, name: str, parent_id: Optional[str] = None):
        super().__init__(
            message=f"Un dossier avec le nom '{name}' existe deja",
            code="FOLDER_ALREADY_EXISTS",
            details={"name": name, "parent_id": parent_id}
        )


class FolderNotEmptyError(DocumentException):
    """Dossier non vide."""

    def __init__(self, folder_id: str, document_count: int, subfolder_count: int):
        super().__init__(
            message="Le dossier n'est pas vide",
            code="FOLDER_NOT_EMPTY",
            details={
                "folder_id": folder_id,
                "document_count": document_count,
                "subfolder_count": subfolder_count
            }
        )


class FolderSystemError(DocumentException):
    """Operation interdite sur dossier systeme."""

    def __init__(self, folder_id: str, operation: str):
        super().__init__(
            message=f"Operation '{operation}' interdite sur un dossier systeme",
            code="FOLDER_SYSTEM_PROTECTED",
            details={"folder_id": folder_id, "operation": operation}
        )


class FolderCircularReferenceError(DocumentException):
    """Reference circulaire detectee."""

    def __init__(self, folder_id: str, target_id: str):
        super().__init__(
            message="Deplacement impossible: creerait une reference circulaire",
            code="FOLDER_CIRCULAR_REFERENCE",
            details={"folder_id": folder_id, "target_id": target_id}
        )


# =============================================================================
# EXCEPTIONS FICHIER
# =============================================================================

class FileTypeNotAllowedError(DocumentException):
    """Type de fichier non autorise."""

    def __init__(self, extension: str, allowed: list):
        super().__init__(
            message=f"Type de fichier '{extension}' non autorise",
            code="FILE_TYPE_NOT_ALLOWED",
            details={"extension": extension, "allowed_types": allowed}
        )


class FileSizeLimitError(DocumentException):
    """Fichier trop volumineux."""

    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            message=f"Fichier trop volumineux ({file_size} bytes, max: {max_size} bytes)",
            code="FILE_SIZE_LIMIT_EXCEEDED",
            details={"file_size": file_size, "max_size": max_size}
        )


class FileUploadError(DocumentException):
    """Erreur lors de l'upload."""

    def __init__(self, filename: str, reason: str):
        super().__init__(
            message=f"Erreur lors de l'upload du fichier '{filename}': {reason}",
            code="FILE_UPLOAD_ERROR",
            details={"filename": filename, "reason": reason}
        )


class FileDownloadError(DocumentException):
    """Erreur lors du telechargement."""

    def __init__(self, document_id: str, reason: str):
        super().__init__(
            message=f"Erreur lors du telechargement: {reason}",
            code="FILE_DOWNLOAD_ERROR",
            details={"document_id": document_id, "reason": reason}
        )


class FileCorruptedError(DocumentException):
    """Fichier corrompu (checksum invalide)."""

    def __init__(self, document_id: str, expected_checksum: str, actual_checksum: str):
        super().__init__(
            message="Le fichier est corrompu (checksum invalide)",
            code="FILE_CORRUPTED",
            details={
                "document_id": document_id,
                "expected_checksum": expected_checksum,
                "actual_checksum": actual_checksum
            }
        )


# =============================================================================
# EXCEPTIONS STOCKAGE
# =============================================================================

class StorageQuotaExceededError(DocumentException):
    """Quota de stockage depasse."""

    def __init__(self, used: int, quota: int, required: int):
        super().__init__(
            message="Quota de stockage depasse",
            code="STORAGE_QUOTA_EXCEEDED",
            details={
                "used_bytes": used,
                "quota_bytes": quota,
                "required_bytes": required
            }
        )


class StorageProviderError(DocumentException):
    """Erreur du provider de stockage."""

    def __init__(self, provider: str, operation: str, reason: str):
        super().__init__(
            message=f"Erreur stockage ({provider}): {reason}",
            code="STORAGE_PROVIDER_ERROR",
            details={
                "provider": provider,
                "operation": operation,
                "reason": reason
            }
        )


class StorageConfigError(DocumentException):
    """Configuration stockage invalide."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Configuration stockage invalide: {reason}",
            code="STORAGE_CONFIG_ERROR",
            details={"reason": reason}
        )


# =============================================================================
# EXCEPTIONS PARTAGE
# =============================================================================

class ShareNotFoundError(DocumentException):
    """Partage non trouve."""

    def __init__(self, share_id: str):
        super().__init__(
            message=f"Partage non trouve: {share_id}",
            code="SHARE_NOT_FOUND",
            details={"share_id": share_id}
        )


class ShareExpiredError(DocumentException):
    """Lien de partage expire."""

    def __init__(self, share_id: str, expired_at: str):
        super().__init__(
            message="Le lien de partage a expire",
            code="SHARE_EXPIRED",
            details={"share_id": share_id, "expired_at": expired_at}
        )


class ShareInvalidPasswordError(DocumentException):
    """Mot de passe de partage invalide."""

    def __init__(self, share_id: str):
        super().__init__(
            message="Mot de passe invalide",
            code="SHARE_INVALID_PASSWORD",
            details={"share_id": share_id}
        )


class ShareDownloadLimitError(DocumentException):
    """Limite de telechargements atteinte."""

    def __init__(self, share_id: str, max_downloads: int):
        super().__init__(
            message="Limite de telechargements atteinte",
            code="SHARE_DOWNLOAD_LIMIT",
            details={"share_id": share_id, "max_downloads": max_downloads}
        )


# =============================================================================
# EXCEPTIONS PERMISSIONS
# =============================================================================

class PermissionDeniedError(DocumentException):
    """Permission refusee."""

    def __init__(self, resource_type: str, resource_id: str, action: str):
        super().__init__(
            message=f"Permission refusee pour {action} sur {resource_type}",
            code="PERMISSION_DENIED",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action
            }
        )


class InsufficientAccessLevelError(DocumentException):
    """Niveau d'acces insuffisant."""

    def __init__(self, required: str, current: str):
        super().__init__(
            message=f"Niveau d'acces insuffisant (requis: {required}, actuel: {current})",
            code="INSUFFICIENT_ACCESS_LEVEL",
            details={"required": required, "current": current}
        )


# =============================================================================
# EXCEPTIONS WORKFLOW
# =============================================================================

class WorkflowError(DocumentException):
    """Erreur workflow."""

    def __init__(self, document_id: str, reason: str):
        super().__init__(
            message=f"Erreur workflow: {reason}",
            code="WORKFLOW_ERROR",
            details={"document_id": document_id, "reason": reason}
        )


class WorkflowTransitionError(DocumentException):
    """Transition workflow non autorisee."""

    def __init__(self, document_id: str, current_status: str, target_status: str):
        super().__init__(
            message=f"Transition de '{current_status}' vers '{target_status}' non autorisee",
            code="WORKFLOW_TRANSITION_ERROR",
            details={
                "document_id": document_id,
                "current_status": current_status,
                "target_status": target_status
            }
        )


# =============================================================================
# EXCEPTIONS COMPRESSION/ARCHIVAGE
# =============================================================================

class CompressionError(DocumentException):
    """Erreur de compression."""

    def __init__(self, document_id: str, reason: str):
        super().__init__(
            message=f"Erreur de compression: {reason}",
            code="COMPRESSION_ERROR",
            details={"document_id": document_id, "reason": reason}
        )


class ArchiveError(DocumentException):
    """Erreur d'archivage."""

    def __init__(self, reason: str, documents: list = None):
        super().__init__(
            message=f"Erreur d'archivage: {reason}",
            code="ARCHIVE_ERROR",
            details={"reason": reason, "documents": documents or []}
        )


# =============================================================================
# EXCEPTIONS RECHERCHE
# =============================================================================

class SearchError(DocumentException):
    """Erreur de recherche."""

    def __init__(self, query: str, reason: str):
        super().__init__(
            message=f"Erreur de recherche: {reason}",
            code="SEARCH_ERROR",
            details={"query": query, "reason": reason}
        )


class IndexingError(DocumentException):
    """Erreur d'indexation."""

    def __init__(self, document_id: str, reason: str):
        super().__init__(
            message=f"Erreur d'indexation: {reason}",
            code="INDEXING_ERROR",
            details={"document_id": document_id, "reason": reason}
        )
