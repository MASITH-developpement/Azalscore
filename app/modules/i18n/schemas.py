"""
AZALSCORE Module I18N - Schemas Pydantic
=========================================

Schemas de validation pour l'API REST.
"""
from __future__ import annotations


from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# ENUMS (re-export pour schema)
# ============================================================================

from .models import (
    LanguageStatus,
    TranslationScope,
    TranslationStatus,
    DateFormatType,
    NumberFormatType,
    ImportExportFormat,
    TranslationJobStatus,
)


# ============================================================================
# LANGUE - SCHEMAS
# ============================================================================

class LanguageBase(BaseModel):
    """Schema de base pour une langue."""
    code: str = Field(..., min_length=2, max_length=10, description="Code langue (ISO)")
    name: str = Field(..., min_length=1, max_length=100)
    native_name: str = Field(..., min_length=1, max_length=100)
    locale: Optional[str] = Field(None, max_length=20)
    rtl: bool = False
    date_format: DateFormatType = DateFormatType.DMY
    date_separator: str = "/"
    time_format_24h: bool = True
    number_format: NumberFormatType = NumberFormatType.SPACE_COMMA
    decimal_separator: str = ","
    thousands_separator: str = " "
    currency_code: str = "EUR"
    currency_symbol: str = "EUR"
    currency_position: str = "after"
    first_day_of_week: int = Field(1, ge=0, le=6)
    flag_emoji: Optional[str] = None
    flag_url: Optional[str] = None


class LanguageCreate(LanguageBase):
    """Schema creation langue."""
    is_default: bool = False
    is_fallback: bool = False
    sort_order: int = 0


class LanguageUpdate(BaseModel):
    """Schema mise a jour langue."""
    name: Optional[str] = None
    native_name: Optional[str] = None
    locale: Optional[str] = None
    rtl: Optional[bool] = None
    date_format: Optional[DateFormatType] = None
    date_separator: Optional[str] = None
    time_format_24h: Optional[bool] = None
    number_format: Optional[NumberFormatType] = None
    decimal_separator: Optional[str] = None
    thousands_separator: Optional[str] = None
    currency_code: Optional[str] = None
    currency_symbol: Optional[str] = None
    currency_position: Optional[str] = None
    first_day_of_week: Optional[int] = None
    flag_emoji: Optional[str] = None
    flag_url: Optional[str] = None
    status: Optional[LanguageStatus] = None
    is_default: Optional[bool] = None
    is_fallback: Optional[bool] = None
    sort_order: Optional[int] = None


class LanguageResponse(LanguageBase):
    """Schema reponse langue."""
    id: UUID
    tenant_id: str
    status: LanguageStatus
    is_default: bool
    is_fallback: bool
    sort_order: int
    translation_coverage: Decimal
    total_keys: int
    translated_keys: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    version: int

    class Config:
        from_attributes = True


class LanguageList(BaseModel):
    """Liste paginee de langues."""
    items: List[LanguageResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# NAMESPACE - SCHEMAS
# ============================================================================

class NamespaceBase(BaseModel):
    """Schema de base pour un namespace."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    module_code: Optional[str] = None


class NamespaceCreate(NamespaceBase):
    """Schema creation namespace."""
    is_system: bool = False
    is_editable: bool = True


class NamespaceUpdate(BaseModel):
    """Schema mise a jour namespace."""
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    module_code: Optional[str] = None
    is_editable: Optional[bool] = None


class NamespaceResponse(NamespaceBase):
    """Schema reponse namespace."""
    id: UUID
    tenant_id: str
    is_system: bool
    is_editable: bool
    total_keys: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class NamespaceList(BaseModel):
    """Liste paginee de namespaces."""
    items: List[NamespaceResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# CLE DE TRADUCTION - SCHEMAS
# ============================================================================

class TranslationKeyBase(BaseModel):
    """Schema de base pour une cle de traduction."""
    key: str = Field(..., min_length=1, max_length=255)
    namespace_id: UUID
    scope: TranslationScope = TranslationScope.TENANT
    description: Optional[str] = None
    context: Optional[str] = None
    screenshot_url: Optional[str] = None
    supports_plural: bool = False
    plural_forms: List[str] = []
    parameters: List[str] = []
    max_length: Optional[int] = None
    tags: List[str] = []


class TranslationKeyCreate(TranslationKeyBase):
    """Schema creation cle."""
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    entity_field: Optional[str] = None
    # Traductions initiales
    translations: Dict[str, str] = {}


class TranslationKeyUpdate(BaseModel):
    """Schema mise a jour cle."""
    description: Optional[str] = None
    context: Optional[str] = None
    screenshot_url: Optional[str] = None
    supports_plural: Optional[bool] = None
    plural_forms: Optional[List[str]] = None
    parameters: Optional[List[str]] = None
    max_length: Optional[int] = None
    tags: Optional[List[str]] = None


class TranslationKeyResponse(TranslationKeyBase):
    """Schema reponse cle."""
    id: UUID
    tenant_id: str
    entity_type: Optional[str]
    entity_id: Optional[UUID]
    entity_field: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    version: int

    class Config:
        from_attributes = True


class TranslationKeyWithTranslations(TranslationKeyResponse):
    """Schema cle avec ses traductions."""
    translations: Dict[str, "TranslationResponse"] = {}


class TranslationKeyList(BaseModel):
    """Liste paginee de cles."""
    items: List[TranslationKeyResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# TRADUCTION - SCHEMAS
# ============================================================================

class TranslationBase(BaseModel):
    """Schema de base pour une traduction."""
    value: str = Field(..., min_length=1)
    plural_values: Dict[str, str] = {}


class TranslationCreate(TranslationBase):
    """Schema creation traduction."""
    translation_key_id: UUID
    language_id: UUID
    status: TranslationStatus = TranslationStatus.DRAFT
    translator_notes: Optional[str] = None


class TranslationUpdate(BaseModel):
    """Schema mise a jour traduction."""
    value: Optional[str] = None
    plural_values: Optional[Dict[str, str]] = None
    status: Optional[TranslationStatus] = None
    translator_notes: Optional[str] = None
    reviewer_notes: Optional[str] = None


class TranslationBulkUpdate(BaseModel):
    """Mise a jour en masse."""
    translations: Dict[str, str]  # {key: value}
    language_code: str
    namespace_code: str
    status: TranslationStatus = TranslationStatus.DRAFT


class TranslationResponse(TranslationBase):
    """Schema reponse traduction."""
    id: UUID
    tenant_id: str
    translation_key_id: UUID
    language_id: UUID
    language_code: str
    status: TranslationStatus
    is_machine_translated: bool
    machine_translation_provider: Optional[str]
    machine_translation_confidence: Optional[Decimal]
    validated_by: Optional[UUID]
    validated_at: Optional[datetime]
    translator_notes: Optional[str]
    reviewer_notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    version: int

    class Config:
        from_attributes = True


class TranslationList(BaseModel):
    """Liste paginee de traductions."""
    items: List[TranslationResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# TRADUCTION INLINE - SCHEMAS
# ============================================================================

class InlineTranslationRequest(BaseModel):
    """Requete de traduction inline."""
    key: str
    namespace: str = "common"
    language: str
    value: str
    create_if_missing: bool = True


class InlineTranslationResponse(BaseModel):
    """Reponse traduction inline."""
    key: str
    namespace: str
    language: str
    value: str
    created: bool
    updated: bool


# ============================================================================
# BUNDLE DE TRADUCTIONS
# ============================================================================

class TranslationBundle(BaseModel):
    """Bundle de traductions pour le frontend."""
    language: str
    namespace: str
    translations: Dict[str, Any]  # Peut inclure pluriels
    generated_at: datetime
    key_count: int


class TranslationBundleRequest(BaseModel):
    """Requete de bundle."""
    language: str
    namespaces: List[str] = ["common"]


# ============================================================================
# TRADUCTION AUTOMATIQUE - SCHEMAS
# ============================================================================

class AutoTranslateRequest(BaseModel):
    """Requete de traduction automatique."""
    source_language_code: str
    target_language_codes: List[str]
    namespace_codes: Optional[List[str]] = None
    scope: Optional[TranslationScope] = None
    provider: str = "openai"  # google, deepl, azure, openai
    model: Optional[str] = None
    overwrite_existing: bool = False


class TranslationJobResponse(BaseModel):
    """Schema reponse job de traduction."""
    id: UUID
    tenant_id: str
    source_language_id: Optional[UUID]
    target_language_ids: List[UUID]
    namespace_ids: List[UUID]
    provider: str
    model: Optional[str]
    status: TranslationJobStatus
    total_keys: int
    processed_keys: int
    failed_keys: int
    progress_percent: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class TranslationJobList(BaseModel):
    """Liste de jobs."""
    items: List[TranslationJobResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# IMPORT/EXPORT - SCHEMAS
# ============================================================================

class ImportRequest(BaseModel):
    """Requete d'import."""
    format: ImportExportFormat
    language_codes: Optional[List[str]] = None
    namespace_codes: Optional[List[str]] = None
    overwrite_existing: bool = False
    mark_as_validated: bool = False


class ExportRequest(BaseModel):
    """Requete d'export."""
    format: ImportExportFormat
    language_codes: List[str]
    namespace_codes: Optional[List[str]] = None
    include_empty: bool = False
    include_metadata: bool = False


class ImportExportResponse(BaseModel):
    """Schema reponse import/export."""
    id: UUID
    tenant_id: str
    operation: str
    format: ImportExportFormat
    file_name: Optional[str]
    file_url: Optional[str]
    file_size: Optional[int]
    language_codes: List[str]
    namespace_codes: List[str]
    status: str
    total_keys: int
    processed_keys: int
    new_keys: int
    updated_keys: int
    skipped_keys: int
    error_keys: int
    errors: List[Dict[str, Any]]
    created_by: Optional[UUID]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# GLOSSAIRE - SCHEMAS
# ============================================================================

class GlossaryBase(BaseModel):
    """Schema de base pour un terme de glossaire."""
    source_term: str = Field(..., min_length=1, max_length=255)
    source_language_code: str = Field(..., min_length=2, max_length=10)
    translations: Dict[str, str] = {}
    term_type: Optional[str] = None
    do_not_translate: bool = False
    definition: Optional[str] = None
    usage_notes: Optional[str] = None
    tags: List[str] = []


class GlossaryCreate(GlossaryBase):
    """Schema creation glossaire."""
    pass


class GlossaryUpdate(BaseModel):
    """Schema mise a jour glossaire."""
    translations: Optional[Dict[str, str]] = None
    term_type: Optional[str] = None
    do_not_translate: Optional[bool] = None
    definition: Optional[str] = None
    usage_notes: Optional[str] = None
    tags: Optional[List[str]] = None


class GlossaryResponse(GlossaryBase):
    """Schema reponse glossaire."""
    id: UUID
    tenant_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class GlossaryList(BaseModel):
    """Liste paginee de glossaire."""
    items: List[GlossaryResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# STATISTIQUES & DASHBOARD
# ============================================================================

class LanguageStats(BaseModel):
    """Statistiques d'une langue."""
    language_code: str
    language_name: str
    total_keys: int
    translated_keys: int
    missing_keys: int
    needs_review: int
    machine_translated: int
    coverage_percent: float


class TranslationDashboard(BaseModel):
    """Dashboard couverture traduction."""
    total_languages: int
    active_languages: int
    total_keys: int
    total_translations: int
    overall_coverage: float
    languages_stats: List[LanguageStats]
    recent_activity: List[Dict[str, Any]]
    pending_reviews: int
    machine_translated_pending: int


class CoverageReport(BaseModel):
    """Rapport de couverture detaille."""
    language_code: str
    namespaces: List[Dict[str, Any]]
    # [{"namespace": "common", "total": 100, "translated": 95, "coverage": 95.0}]
    missing_keys: List[str]
    needs_review: List[str]


# ============================================================================
# FILTRES
# ============================================================================

class LanguageFilters(BaseModel):
    """Filtres pour les langues."""
    search: Optional[str] = None
    status: Optional[List[LanguageStatus]] = None
    is_default: Optional[bool] = None
    rtl: Optional[bool] = None


class TranslationKeyFilters(BaseModel):
    """Filtres pour les cles."""
    search: Optional[str] = None
    namespace_id: Optional[UUID] = None
    namespace_code: Optional[str] = None
    scope: Optional[TranslationScope] = None
    tags: Optional[List[str]] = None
    has_translation: Optional[bool] = None
    language_code: Optional[str] = None
    entity_type: Optional[str] = None


class TranslationFilters(BaseModel):
    """Filtres pour les traductions."""
    search: Optional[str] = None
    language_code: Optional[str] = None
    namespace_code: Optional[str] = None
    status: Optional[List[TranslationStatus]] = None
    is_machine_translated: Optional[bool] = None


# ============================================================================
# BULK OPERATIONS
# ============================================================================

class BulkDeleteRequest(BaseModel):
    """Requete suppression en masse."""
    ids: List[UUID]
    hard: bool = False


class BulkResult(BaseModel):
    """Resultat operation en masse."""
    success: int
    errors: List[Dict[str, Any]]


# ============================================================================
# AUTOCOMPLETE
# ============================================================================

class AutocompleteItem(BaseModel):
    """Item autocomplete."""
    id: str
    code: str
    name: str
    label: str


class AutocompleteResponse(BaseModel):
    """Reponse autocomplete."""
    items: List[AutocompleteItem]


# ============================================================================
# FORMATAGE
# ============================================================================

class FormatRequest(BaseModel):
    """Requete de formatage."""
    language_code: str
    value: Any
    format_type: str  # date, number, currency, percent


class FormatResponse(BaseModel):
    """Reponse formatage."""
    original: Any
    formatted: str
    language_code: str
    format_type: str


# Update forward references
TranslationKeyWithTranslations.model_rebuild()
