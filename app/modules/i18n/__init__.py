"""
AZALSCORE Module I18N - Internationalisation
==============================================

Module complet d'internationalisation pour AZALSCORE ERP.

Fonctionnalites:
- Gestion des langues par tenant
- Traductions par cle avec namespaces
- Gestion des pluriels (ICU MessageFormat)
- Formats regionaux (dates, nombres, devises)
- Traduction automatique (OpenAI, Google, DeepL)
- Import/Export (JSON, PO, XLIFF, CSV)
- Cache des traductions
- Interface de traduction inline
- Dashboard couverture traduction
- Glossaire de termes

Inspire des meilleures pratiques de:
- Odoo (PO files, module translations)
- SAP (UI5 i18n, resource bundles)
- Microsoft Dynamics 365 (multi-language, translation service)

Usage:
    from app.modules.i18n import I18NService, router

    # Dans un endpoint
    service = I18NService(db, tenant_id)
    text = service.t("button.save", "fr")
    formatted = service.format_currency(Decimal("1234.56"), "EUR", "fr")

    # Bundle pour frontend
    bundle = service.get_bundle("fr", "common")
"""

from .models import (
    Language,
    LanguageStatus,
    TranslationNamespace,
    TranslationKey,
    TranslationScope,
    Translation,
    TranslationStatus,
    TranslationJob,
    TranslationJobStatus,
    TranslationImportExport,
    ImportExportFormat,
    TranslationCache,
    Glossary,
    DateFormatType,
    NumberFormatType,
)

from .schemas import (
    LanguageCreate,
    LanguageUpdate,
    LanguageResponse,
    LanguageList,
    NamespaceCreate,
    NamespaceUpdate,
    NamespaceResponse,
    TranslationKeyCreate,
    TranslationKeyUpdate,
    TranslationKeyResponse,
    TranslationCreate,
    TranslationUpdate,
    TranslationResponse,
    TranslationBundle,
    TranslationDashboard,
    LanguageStats,
    CoverageReport,
    InlineTranslationRequest,
    InlineTranslationResponse,
    AutoTranslateRequest,
    ImportRequest,
    ExportRequest,
    GlossaryCreate,
    GlossaryUpdate,
    GlossaryResponse,
)

from .repository import (
    LanguageRepository,
    NamespaceRepository,
    TranslationKeyRepository,
    TranslationRepository,
    CacheRepository,
    GlossaryRepository,
    TranslationJobRepository,
)

from .service import I18NService, create_i18n_service

from .router import router

from .exceptions import (
    I18NBaseException,
    LanguageNotFoundError,
    LanguageDuplicateError,
    LanguageDeleteError,
    NamespaceNotFoundError,
    NamespaceDuplicateError,
    TranslationKeyNotFoundError,
    TranslationKeyDuplicateError,
    TranslationNotFoundError,
    TranslationLengthError,
    ImportFormatError,
    ImportParseError,
    ExportError,
    AutoTranslationError,
    AutoTranslationProviderError,
    GlossaryTermNotFoundError,
    GlossaryTermDuplicateError,
)

__all__ = [
    # Models
    "Language",
    "LanguageStatus",
    "TranslationNamespace",
    "TranslationKey",
    "TranslationScope",
    "Translation",
    "TranslationStatus",
    "TranslationJob",
    "TranslationJobStatus",
    "TranslationImportExport",
    "ImportExportFormat",
    "TranslationCache",
    "Glossary",
    "DateFormatType",
    "NumberFormatType",
    # Schemas
    "LanguageCreate",
    "LanguageUpdate",
    "LanguageResponse",
    "LanguageList",
    "NamespaceCreate",
    "NamespaceUpdate",
    "NamespaceResponse",
    "TranslationKeyCreate",
    "TranslationKeyUpdate",
    "TranslationKeyResponse",
    "TranslationCreate",
    "TranslationUpdate",
    "TranslationResponse",
    "TranslationBundle",
    "TranslationDashboard",
    "LanguageStats",
    "CoverageReport",
    "InlineTranslationRequest",
    "InlineTranslationResponse",
    "AutoTranslateRequest",
    "ImportRequest",
    "ExportRequest",
    "GlossaryCreate",
    "GlossaryUpdate",
    "GlossaryResponse",
    # Repositories
    "LanguageRepository",
    "NamespaceRepository",
    "TranslationKeyRepository",
    "TranslationRepository",
    "CacheRepository",
    "GlossaryRepository",
    "TranslationJobRepository",
    # Service
    "I18NService",
    "create_i18n_service",
    # Router
    "router",
    # Exceptions
    "I18NBaseException",
    "LanguageNotFoundError",
    "LanguageDuplicateError",
    "LanguageDeleteError",
    "NamespaceNotFoundError",
    "NamespaceDuplicateError",
    "TranslationKeyNotFoundError",
    "TranslationKeyDuplicateError",
    "TranslationNotFoundError",
    "TranslationLengthError",
    "ImportFormatError",
    "ImportParseError",
    "ExportError",
    "AutoTranslationError",
    "AutoTranslationProviderError",
    "GlossaryTermNotFoundError",
    "GlossaryTermDuplicateError",
]
