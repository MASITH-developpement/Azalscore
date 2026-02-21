"""
AZALS MODULE HR_VAULT - Exceptions
====================================

Exceptions personnalisees pour le module coffre-fort RH.
"""

from typing import Any, Optional


class HRVaultException(Exception):
    """Exception de base pour le module HR Vault."""

    def __init__(
        self,
        message: str,
        code: str = "HR_VAULT_ERROR",
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


# ============================================================================
# EXCEPTIONS - DOCUMENTS
# ============================================================================

class DocumentNotFoundException(HRVaultException):
    """Document non trouve."""

    def __init__(self, document_id: str, details: Optional[dict] = None):
        super().__init__(
            message=f"Document non trouve: {document_id}",
            code="DOCUMENT_NOT_FOUND",
            details=details or {"document_id": document_id},
        )


class DocumentAlreadyExistsException(HRVaultException):
    """Document deja existant."""

    def __init__(self, reference: str, details: Optional[dict] = None):
        super().__init__(
            message=f"Un document avec cette reference existe deja: {reference}",
            code="DOCUMENT_ALREADY_EXISTS",
            details=details or {"reference": reference},
        )


class DocumentDeletedException(HRVaultException):
    """Document supprime."""

    def __init__(self, document_id: str):
        super().__init__(
            message=f"Ce document a ete supprime: {document_id}",
            code="DOCUMENT_DELETED",
            details={"document_id": document_id},
        )


class InvalidDocumentTypeException(HRVaultException):
    """Type de document invalide."""

    def __init__(self, document_type: str):
        super().__init__(
            message=f"Type de document invalide: {document_type}",
            code="INVALID_DOCUMENT_TYPE",
            details={"document_type": document_type},
        )


class DocumentIntegrityException(HRVaultException):
    """Integrite du document compromise."""

    def __init__(self, document_id: str, expected_hash: str, actual_hash: str):
        super().__init__(
            message=f"L'integrite du document {document_id} est compromise",
            code="DOCUMENT_INTEGRITY_ERROR",
            details={
                "document_id": document_id,
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
            },
        )


# ============================================================================
# EXCEPTIONS - CHIFFREMENT
# ============================================================================

class EncryptionException(HRVaultException):
    """Erreur de chiffrement."""

    def __init__(self, message: str = "Erreur lors du chiffrement"):
        super().__init__(
            message=message,
            code="ENCRYPTION_ERROR",
        )


class DecryptionException(HRVaultException):
    """Erreur de dechiffrement."""

    def __init__(self, message: str = "Erreur lors du dechiffrement"):
        super().__init__(
            message=message,
            code="DECRYPTION_ERROR",
        )


class EncryptionKeyNotFoundException(HRVaultException):
    """Cle de chiffrement non trouvee."""

    def __init__(self, key_id: str):
        super().__init__(
            message=f"Cle de chiffrement non trouvee: {key_id}",
            code="ENCRYPTION_KEY_NOT_FOUND",
            details={"key_id": key_id},
        )


class EncryptionKeyExpiredException(HRVaultException):
    """Cle de chiffrement expiree."""

    def __init__(self, key_id: str):
        super().__init__(
            message=f"La cle de chiffrement a expire: {key_id}",
            code="ENCRYPTION_KEY_EXPIRED",
            details={"key_id": key_id},
        )


# ============================================================================
# EXCEPTIONS - ACCES
# ============================================================================

class AccessDeniedException(HRVaultException):
    """Acces refuse."""

    def __init__(
        self,
        user_id: str,
        document_id: str,
        action: str,
        reason: Optional[str] = None,
    ):
        super().__init__(
            message=f"Acces refuse pour l'action {action} sur le document {document_id}",
            code="ACCESS_DENIED",
            details={
                "user_id": user_id,
                "document_id": document_id,
                "action": action,
                "reason": reason,
            },
        )


class InsufficientPermissionsException(HRVaultException):
    """Permissions insuffisantes."""

    def __init__(self, required_permission: str, user_role: str):
        super().__init__(
            message=f"Permission {required_permission} requise (role actuel: {user_role})",
            code="INSUFFICIENT_PERMISSIONS",
            details={
                "required_permission": required_permission,
                "user_role": user_role,
            },
        )


class VaultNotActivatedException(HRVaultException):
    """Coffre-fort non active."""

    def __init__(self, employee_id: str):
        super().__init__(
            message=f"Le coffre-fort n'est pas active pour cet employe: {employee_id}",
            code="VAULT_NOT_ACTIVATED",
            details={"employee_id": employee_id},
        )


# ============================================================================
# EXCEPTIONS - CONSENTEMENT
# ============================================================================

class ConsentRequiredException(HRVaultException):
    """Consentement requis."""

    def __init__(self, consent_type: str):
        super().__init__(
            message=f"Le consentement '{consent_type}' est requis pour cette action",
            code="CONSENT_REQUIRED",
            details={"consent_type": consent_type},
        )


class ConsentRevokedException(HRVaultException):
    """Consentement revoque."""

    def __init__(self, consent_type: str, revoked_at: str):
        super().__init__(
            message=f"Le consentement '{consent_type}' a ete revoque le {revoked_at}",
            code="CONSENT_REVOKED",
            details={"consent_type": consent_type, "revoked_at": revoked_at},
        )


# ============================================================================
# EXCEPTIONS - SIGNATURE
# ============================================================================

class SignatureException(HRVaultException):
    """Erreur de signature."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="SIGNATURE_ERROR",
            details=details,
        )


class SignatureAlreadyCompletedException(HRVaultException):
    """Document deja signe."""

    def __init__(self, document_id: str):
        super().__init__(
            message=f"Ce document est deja signe: {document_id}",
            code="SIGNATURE_ALREADY_COMPLETED",
            details={"document_id": document_id},
        )


class SignatureExpiredException(HRVaultException):
    """Demande de signature expiree."""

    def __init__(self, document_id: str, expired_at: str):
        super().__init__(
            message=f"La demande de signature a expire pour le document {document_id}",
            code="SIGNATURE_EXPIRED",
            details={"document_id": document_id, "expired_at": expired_at},
        )


# ============================================================================
# EXCEPTIONS - RGPD
# ============================================================================

class GDPRRequestNotFoundException(HRVaultException):
    """Demande RGPD non trouvee."""

    def __init__(self, request_id: str):
        super().__init__(
            message=f"Demande RGPD non trouvee: {request_id}",
            code="GDPR_REQUEST_NOT_FOUND",
            details={"request_id": request_id},
        )


class GDPRRequestAlreadyProcessedException(HRVaultException):
    """Demande RGPD deja traitee."""

    def __init__(self, request_id: str, processed_at: str):
        super().__init__(
            message=f"Cette demande RGPD a deja ete traitee: {request_id}",
            code="GDPR_REQUEST_ALREADY_PROCESSED",
            details={"request_id": request_id, "processed_at": processed_at},
        )


class GDPRExportExpiredException(HRVaultException):
    """Export RGPD expire."""

    def __init__(self, request_id: str, expired_at: str):
        super().__init__(
            message=f"L'export RGPD a expire pour la demande {request_id}",
            code="GDPR_EXPORT_EXPIRED",
            details={"request_id": request_id, "expired_at": expired_at},
        )


# ============================================================================
# EXCEPTIONS - RETENTION
# ============================================================================

class RetentionPeriodActiveException(HRVaultException):
    """Periode de conservation active."""

    def __init__(self, document_id: str, retention_end_date: str):
        super().__init__(
            message=f"Le document {document_id} ne peut pas etre supprime (conservation jusqu'au {retention_end_date})",
            code="RETENTION_PERIOD_ACTIVE",
            details={
                "document_id": document_id,
                "retention_end_date": retention_end_date,
            },
        )


# ============================================================================
# EXCEPTIONS - FICHIER
# ============================================================================

class FileNotFoundException(HRVaultException):
    """Fichier non trouve sur le stockage."""

    def __init__(self, storage_path: str):
        super().__init__(
            message=f"Fichier non trouve: {storage_path}",
            code="FILE_NOT_FOUND",
            details={"storage_path": storage_path},
        )


class FileSizeLimitException(HRVaultException):
    """Taille de fichier depassee."""

    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            message=f"La taille du fichier ({file_size} octets) depasse la limite ({max_size} octets)",
            code="FILE_SIZE_LIMIT_EXCEEDED",
            details={"file_size": file_size, "max_size": max_size},
        )


class InvalidFileTypeException(HRVaultException):
    """Type de fichier non autorise."""

    def __init__(self, mime_type: str, allowed_types: list[str]):
        super().__init__(
            message=f"Type de fichier non autorise: {mime_type}",
            code="INVALID_FILE_TYPE",
            details={"mime_type": mime_type, "allowed_types": allowed_types},
        )


class StorageException(HRVaultException):
    """Erreur de stockage."""

    def __init__(self, message: str, operation: str):
        super().__init__(
            message=message,
            code="STORAGE_ERROR",
            details={"operation": operation},
        )


# ============================================================================
# EXCEPTIONS - EMPLOYE
# ============================================================================

class EmployeeNotFoundException(HRVaultException):
    """Employe non trouve."""

    def __init__(self, employee_id: str):
        super().__init__(
            message=f"Employe non trouve: {employee_id}",
            code="EMPLOYEE_NOT_FOUND",
            details={"employee_id": employee_id},
        )


class EmployeeNotActiveException(HRVaultException):
    """Employe inactif."""

    def __init__(self, employee_id: str):
        super().__init__(
            message=f"Cet employe n'est plus actif: {employee_id}",
            code="EMPLOYEE_NOT_ACTIVE",
            details={"employee_id": employee_id},
        )


# ============================================================================
# EXCEPTIONS - CATEGORIE
# ============================================================================

class CategoryNotFoundException(HRVaultException):
    """Categorie non trouvee."""

    def __init__(self, category_id: str):
        super().__init__(
            message=f"Categorie non trouvee: {category_id}",
            code="CATEGORY_NOT_FOUND",
            details={"category_id": category_id},
        )


class CategoryAlreadyExistsException(HRVaultException):
    """Categorie deja existante."""

    def __init__(self, code: str):
        super().__init__(
            message=f"Une categorie avec ce code existe deja: {code}",
            code="CATEGORY_ALREADY_EXISTS",
            details={"category_code": code},
        )


class CategoryInUseException(HRVaultException):
    """Categorie utilisee."""

    def __init__(self, category_id: str, documents_count: int):
        super().__init__(
            message=f"La categorie {category_id} est utilisee par {documents_count} documents",
            code="CATEGORY_IN_USE",
            details={"category_id": category_id, "documents_count": documents_count},
        )
