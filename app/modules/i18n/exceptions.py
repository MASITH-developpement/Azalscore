"""
AZALSCORE Module I18N - Exceptions
===================================

Exceptions metier specifiques au module I18N.
"""

from typing import Optional


class I18NBaseException(Exception):
    """Exception de base pour le module I18N."""

    def __init__(self, message: str, code: str = "I18N_ERROR", details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


# ============================================================================
# LANGUAGE EXCEPTIONS
# ============================================================================

class LanguageNotFoundError(I18NBaseException):
    """Langue non trouvee."""

    def __init__(self, identifier: str):
        super().__init__(
            message=f"Language not found: {identifier}",
            code="LANGUAGE_NOT_FOUND",
            details={"identifier": identifier}
        )


class LanguageDuplicateError(I18NBaseException):
    """Code langue deja utilise."""

    def __init__(self, code: str):
        super().__init__(
            message=f"Language code already exists: {code}",
            code="LANGUAGE_DUPLICATE",
            details={"code": code}
        )


class LanguageValidationError(I18NBaseException):
    """Erreur de validation langue."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="LANGUAGE_VALIDATION_ERROR",
            details={"field": field} if field else {}
        )


class LanguageDeleteError(I18NBaseException):
    """Impossible de supprimer la langue."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Cannot delete language: {reason}",
            code="LANGUAGE_DELETE_ERROR",
            details={"reason": reason}
        )


class DefaultLanguageRequiredError(I18NBaseException):
    """Une langue par defaut est requise."""

    def __init__(self):
        super().__init__(
            message="A default language is required",
            code="DEFAULT_LANGUAGE_REQUIRED"
        )


# ============================================================================
# NAMESPACE EXCEPTIONS
# ============================================================================

class NamespaceNotFoundError(I18NBaseException):
    """Namespace non trouve."""

    def __init__(self, identifier: str):
        super().__init__(
            message=f"Namespace not found: {identifier}",
            code="NAMESPACE_NOT_FOUND",
            details={"identifier": identifier}
        )


class NamespaceDuplicateError(I18NBaseException):
    """Code namespace deja utilise."""

    def __init__(self, code: str):
        super().__init__(
            message=f"Namespace code already exists: {code}",
            code="NAMESPACE_DUPLICATE",
            details={"code": code}
        )


class NamespaceNotEditableError(I18NBaseException):
    """Namespace systeme non modifiable."""

    def __init__(self, code: str):
        super().__init__(
            message=f"Namespace is not editable: {code}",
            code="NAMESPACE_NOT_EDITABLE",
            details={"code": code}
        )


# ============================================================================
# TRANSLATION KEY EXCEPTIONS
# ============================================================================

class TranslationKeyNotFoundError(I18NBaseException):
    """Cle de traduction non trouvee."""

    def __init__(self, identifier: str):
        super().__init__(
            message=f"Translation key not found: {identifier}",
            code="TRANSLATION_KEY_NOT_FOUND",
            details={"identifier": identifier}
        )


class TranslationKeyDuplicateError(I18NBaseException):
    """Cle de traduction deja existante."""

    def __init__(self, namespace: str, key: str):
        super().__init__(
            message=f"Translation key already exists: {namespace}.{key}",
            code="TRANSLATION_KEY_DUPLICATE",
            details={"namespace": namespace, "key": key}
        )


class TranslationKeyValidationError(I18NBaseException):
    """Erreur de validation cle."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="TRANSLATION_KEY_VALIDATION_ERROR",
            details={"field": field} if field else {}
        )


# ============================================================================
# TRANSLATION EXCEPTIONS
# ============================================================================

class TranslationNotFoundError(I18NBaseException):
    """Traduction non trouvee."""

    def __init__(self, key: str, language: str):
        super().__init__(
            message=f"Translation not found for key '{key}' in language '{language}'",
            code="TRANSLATION_NOT_FOUND",
            details={"key": key, "language": language}
        )


class TranslationDuplicateError(I18NBaseException):
    """Traduction deja existante."""

    def __init__(self, key_id: str, language_id: str):
        super().__init__(
            message="Translation already exists for this key and language",
            code="TRANSLATION_DUPLICATE",
            details={"key_id": key_id, "language_id": language_id}
        )


class TranslationValidationError(I18NBaseException):
    """Erreur de validation traduction."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="TRANSLATION_VALIDATION_ERROR",
            details={"field": field} if field else {}
        )


class TranslationLengthError(I18NBaseException):
    """Traduction trop longue."""

    def __init__(self, key: str, max_length: int, actual_length: int):
        super().__init__(
            message=f"Translation exceeds max length ({actual_length} > {max_length})",
            code="TRANSLATION_LENGTH_ERROR",
            details={
                "key": key,
                "max_length": max_length,
                "actual_length": actual_length
            }
        )


# ============================================================================
# IMPORT/EXPORT EXCEPTIONS
# ============================================================================

class ImportFormatError(I18NBaseException):
    """Format d'import non supporte ou invalide."""

    def __init__(self, format: str, reason: Optional[str] = None):
        super().__init__(
            message=f"Invalid import format: {format}. {reason or ''}",
            code="IMPORT_FORMAT_ERROR",
            details={"format": format, "reason": reason}
        )


class ImportParseError(I18NBaseException):
    """Erreur de parsing fichier d'import."""

    def __init__(self, line: Optional[int] = None, reason: Optional[str] = None):
        super().__init__(
            message=f"Error parsing import file{f' at line {line}' if line else ''}: {reason or 'Unknown error'}",
            code="IMPORT_PARSE_ERROR",
            details={"line": line, "reason": reason}
        )


class ExportError(I18NBaseException):
    """Erreur lors de l'export."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Export error: {reason}",
            code="EXPORT_ERROR",
            details={"reason": reason}
        )


# ============================================================================
# AUTO-TRANSLATION EXCEPTIONS
# ============================================================================

class AutoTranslationError(I18NBaseException):
    """Erreur de traduction automatique."""

    def __init__(self, provider: str, reason: str):
        super().__init__(
            message=f"Auto-translation failed ({provider}): {reason}",
            code="AUTO_TRANSLATION_ERROR",
            details={"provider": provider, "reason": reason}
        )


class AutoTranslationProviderError(I18NBaseException):
    """Provider de traduction non disponible."""

    def __init__(self, provider: str):
        super().__init__(
            message=f"Translation provider not available: {provider}",
            code="TRANSLATION_PROVIDER_ERROR",
            details={"provider": provider}
        )


class AutoTranslationQuotaError(I18NBaseException):
    """Quota de traduction automatique depasse."""

    def __init__(self, provider: str):
        super().__init__(
            message=f"Translation quota exceeded for provider: {provider}",
            code="TRANSLATION_QUOTA_ERROR",
            details={"provider": provider}
        )


# ============================================================================
# CACHE EXCEPTIONS
# ============================================================================

class CacheInvalidationError(I18NBaseException):
    """Erreur d'invalidation du cache."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Cache invalidation failed: {reason}",
            code="CACHE_INVALIDATION_ERROR",
            details={"reason": reason}
        )


# ============================================================================
# GLOSSARY EXCEPTIONS
# ============================================================================

class GlossaryTermNotFoundError(I18NBaseException):
    """Terme de glossaire non trouve."""

    def __init__(self, term: str):
        super().__init__(
            message=f"Glossary term not found: {term}",
            code="GLOSSARY_TERM_NOT_FOUND",
            details={"term": term}
        )


class GlossaryTermDuplicateError(I18NBaseException):
    """Terme de glossaire deja existant."""

    def __init__(self, term: str, language: str):
        super().__init__(
            message=f"Glossary term already exists: '{term}' ({language})",
            code="GLOSSARY_TERM_DUPLICATE",
            details={"term": term, "language": language}
        )


# ============================================================================
# JOB EXCEPTIONS
# ============================================================================

class TranslationJobNotFoundError(I18NBaseException):
    """Job de traduction non trouve."""

    def __init__(self, job_id: str):
        super().__init__(
            message=f"Translation job not found: {job_id}",
            code="TRANSLATION_JOB_NOT_FOUND",
            details={"job_id": job_id}
        )


class TranslationJobInProgressError(I18NBaseException):
    """Un job de traduction est deja en cours."""

    def __init__(self):
        super().__init__(
            message="A translation job is already in progress",
            code="TRANSLATION_JOB_IN_PROGRESS"
        )


class TranslationJobCancelledError(I18NBaseException):
    """Le job de traduction a ete annule."""

    def __init__(self, job_id: str):
        super().__init__(
            message=f"Translation job was cancelled: {job_id}",
            code="TRANSLATION_JOB_CANCELLED",
            details={"job_id": job_id}
        )
