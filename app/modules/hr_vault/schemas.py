"""
AZALS MODULE HR_VAULT - Schemas Pydantic
==========================================

Schemas pour la validation des donnees du coffre-fort RH.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .models import (
    AlertType,
    EncryptionAlgorithm,
    GDPRRequestStatus,
    GDPRRequestType,
    RetentionPeriod,
    SignatureStatus,
    VaultAccessRole,
    VaultAccessType,
    VaultDocumentStatus,
    VaultDocumentType,
)


# ============================================================================
# SCHEMAS - CATEGORIES
# ============================================================================

class VaultCategoryBase(BaseModel):
    """Schema de base pour les categories."""
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)
    default_retention: RetentionPeriod = RetentionPeriod.FIVE_YEARS
    requires_signature: bool = False
    is_confidential: bool = True
    visible_to_employee: bool = True
    sort_order: int = 0


class VaultCategoryCreate(VaultCategoryBase):
    """Schema de creation de categorie."""
    pass


class VaultCategoryUpdate(BaseModel):
    """Schema de mise a jour de categorie."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)
    default_retention: Optional[RetentionPeriod] = None
    requires_signature: Optional[bool] = None
    is_confidential: Optional[bool] = None
    visible_to_employee: Optional[bool] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class VaultCategoryResponse(VaultCategoryBase):
    """Schema de reponse pour les categories."""
    id: UUID
    tenant_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    version: int
    documents_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHEMAS - DOCUMENTS
# ============================================================================

class VaultDocumentBase(BaseModel):
    """Schema de base pour les documents."""
    model_config = ConfigDict(populate_by_name=True)

    document_type: VaultDocumentType
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    reference: Optional[str] = Field(None, max_length=100)

    # Dates
    document_date: Optional[date] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None

    # Paie
    pay_period: Optional[str] = Field(None, max_length=20)
    gross_salary: Optional[Decimal] = Field(None, ge=0)
    net_salary: Optional[Decimal] = Field(None, ge=0)

    # Conservation
    retention_period: RetentionPeriod = RetentionPeriod.FIFTY_YEARS

    # Confidentialite
    is_confidential: bool = True
    confidentiality_level: int = Field(1, ge=1, le=5)
    visible_to_employee: bool = True

    # Metadonnees
    tags: list[str] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class VaultDocumentCreate(VaultDocumentBase):
    """Schema de creation de document."""
    employee_id: UUID
    category_id: Optional[UUID] = None
    notify_employee: bool = True
    requires_signature: bool = False


class VaultDocumentUpdate(BaseModel):
    """Schema de mise a jour de document."""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    reference: Optional[str] = Field(None, max_length=100)
    category_id: Optional[UUID] = None

    document_date: Optional[date] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None

    is_confidential: Optional[bool] = None
    confidentiality_level: Optional[int] = Field(None, ge=1, le=5)
    visible_to_employee: Optional[bool] = None

    tags: Optional[list[str]] = None
    custom_fields: Optional[dict[str, Any]] = None


class VaultDocumentResponse(VaultDocumentBase):
    """Schema de reponse pour les documents."""
    id: UUID
    tenant_id: str
    employee_id: UUID
    category_id: Optional[UUID] = None

    # Fichier
    file_name: str
    file_size: int
    mime_type: str
    is_encrypted: bool

    # Integrite
    file_hash: str

    # Statut
    status: VaultDocumentStatus

    # Signature
    signature_status: SignatureStatus
    signed_at: Optional[datetime] = None

    # Conservation
    retention_end_date: Optional[date] = None

    # Notification
    employee_notified: bool
    notification_sent_at: Optional[datetime] = None
    employee_viewed: bool
    first_viewed_at: Optional[datetime] = None

    # Audit
    is_active: bool
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: datetime
    version: int

    # Relations
    category_name: Optional[str] = None
    employee_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VaultDocumentSummary(BaseModel):
    """Resume compact d'un document."""
    id: UUID
    document_type: VaultDocumentType
    title: str
    file_name: str
    file_size: int
    document_date: Optional[date] = None
    status: VaultDocumentStatus
    signature_status: SignatureStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VaultDocumentUpload(BaseModel):
    """Schema pour l'upload de document."""
    employee_id: UUID
    document_type: VaultDocumentType
    title: str
    category_id: Optional[UUID] = None
    description: Optional[str] = None
    reference: Optional[str] = None
    document_date: Optional[date] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    pay_period: Optional[str] = None
    gross_salary: Optional[Decimal] = None
    net_salary: Optional[Decimal] = None
    notify_employee: bool = True
    requires_signature: bool = False
    tags: list[str] = Field(default_factory=list)


# ============================================================================
# SCHEMAS - VERSIONS
# ============================================================================

class VaultDocumentVersionResponse(BaseModel):
    """Schema de reponse pour les versions de document."""
    id: UUID
    document_id: UUID
    version_number: int
    file_name: str
    file_size: int
    file_hash: str
    change_reason: Optional[str] = None
    created_at: datetime
    created_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHEMAS - ACCES
# ============================================================================

class VaultAccessLogResponse(BaseModel):
    """Schema de reponse pour les logs d'acces."""
    id: UUID
    document_id: UUID
    employee_id: UUID
    accessed_by: UUID
    access_role: VaultAccessRole
    access_type: VaultAccessType
    access_date: datetime
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    success: bool
    error_message: Optional[str] = None

    # Relations
    document_title: Optional[str] = None
    accessed_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VaultAccessPermissionCreate(BaseModel):
    """Schema de creation de permission."""
    user_id: Optional[UUID] = None
    role: Optional[VaultAccessRole] = None
    employee_id: Optional[UUID] = None
    document_type: Optional[VaultDocumentType] = None
    category_id: Optional[UUID] = None

    can_view: bool = False
    can_download: bool = False
    can_print: bool = False
    can_upload: bool = False
    can_edit: bool = False
    can_delete: bool = False
    can_share: bool = False
    can_sign: bool = False

    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class VaultAccessPermissionResponse(VaultAccessPermissionCreate):
    """Schema de reponse pour les permissions."""
    id: UUID
    tenant_id: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHEMAS - CONSENTEMENT
# ============================================================================

class VaultConsentCreate(BaseModel):
    """Schema de creation de consentement."""
    employee_id: UUID
    consent_type: str = Field(..., max_length=50)
    consent_version: str = Field(..., max_length=20)
    given: bool = True


class VaultConsentResponse(BaseModel):
    """Schema de reponse pour le consentement."""
    id: UUID
    tenant_id: str
    employee_id: UUID
    consent_type: str
    consent_version: str
    given: bool
    given_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHEMAS - RGPD
# ============================================================================

class VaultGDPRRequestCreate(BaseModel):
    """Schema de creation de demande RGPD."""
    employee_id: UUID
    request_type: GDPRRequestType
    request_description: Optional[str] = None
    document_types: list[VaultDocumentType] = Field(default_factory=list)
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class VaultGDPRRequestResponse(BaseModel):
    """Schema de reponse pour les demandes RGPD."""
    id: UUID
    tenant_id: str
    employee_id: UUID
    request_code: str
    request_type: GDPRRequestType
    status: GDPRRequestStatus
    request_description: Optional[str] = None
    document_types: list[VaultDocumentType] = Field(default_factory=list)
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    requested_at: datetime
    due_date: date
    processed_at: Optional[datetime] = None
    processed_by: Optional[UUID] = None
    response_details: Optional[str] = None
    download_count: int = 0

    # Relations
    employee_name: Optional[str] = None
    processed_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VaultGDPRRequestProcess(BaseModel):
    """Schema pour traiter une demande RGPD."""
    status: GDPRRequestStatus
    response_details: Optional[str] = None


# ============================================================================
# SCHEMAS - ALERTES
# ============================================================================

class VaultAlertResponse(BaseModel):
    """Schema de reponse pour les alertes."""
    id: UUID
    tenant_id: str
    employee_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    alert_type: AlertType
    title: str
    description: Optional[str] = None
    severity: str
    is_read: bool
    read_at: Optional[datetime] = None
    is_dismissed: bool
    action_url: Optional[str] = None
    due_date: Optional[date] = None
    created_at: datetime

    # Relations
    document_title: Optional[str] = None
    employee_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHEMAS - STATISTIQUES
# ============================================================================

class VaultDashboardStats(BaseModel):
    """Statistiques pour le dashboard."""
    total_employees: int = 0
    active_vaults: int = 0
    total_documents: int = 0
    documents_this_month: int = 0

    total_storage_bytes: int = 0
    average_docs_per_employee: float = 0

    pending_signatures: int = 0
    expiring_documents_30d: int = 0
    gdpr_requests_pending: int = 0

    documents_by_type: dict[str, int] = Field(default_factory=dict)
    recent_activity: list[dict] = Field(default_factory=list)


class VaultEmployeeStats(BaseModel):
    """Statistiques pour un employe."""
    employee_id: UUID
    employee_name: str
    vault_activated: bool
    activated_at: Optional[datetime] = None

    total_documents: int = 0
    documents_by_type: dict[str, int] = Field(default_factory=dict)
    total_storage_bytes: int = 0

    last_document_date: Optional[datetime] = None
    last_access_date: Optional[datetime] = None

    pending_signatures: int = 0
    unread_documents: int = 0


class VaultDocumentStats(BaseModel):
    """Statistiques des documents."""
    total_count: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)

    total_size_bytes: int = 0
    average_size_bytes: int = 0

    this_month: int = 0
    this_year: int = 0

    expiring_30d: int = 0
    expiring_90d: int = 0


# ============================================================================
# SCHEMAS - SIGNATURE
# ============================================================================

class VaultSignatureRequest(BaseModel):
    """Schema pour demander une signature."""
    document_id: UUID
    signers: list[dict] = Field(default_factory=list)
    message: Optional[str] = None
    expires_at: Optional[datetime] = None


class VaultSignatureStatus(BaseModel):
    """Statut de signature d'un document."""
    document_id: UUID
    signature_status: SignatureStatus
    signature_request_id: Optional[str] = None
    signed_at: Optional[datetime] = None
    signers: list[dict] = Field(default_factory=list)


# ============================================================================
# SCHEMAS - EXPORT
# ============================================================================

class VaultExportRequest(BaseModel):
    """Schema pour exporter des documents."""
    employee_id: UUID
    document_types: list[VaultDocumentType] = Field(default_factory=list)
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    format: str = "zip"  # zip, pdf_merged


class VaultExportResponse(BaseModel):
    """Reponse d'export."""
    export_id: UUID
    status: str
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    document_count: int = 0
    total_size_bytes: int = 0


# ============================================================================
# SCHEMAS - LISTE ET FILTRES
# ============================================================================

class VaultDocumentFilters(BaseModel):
    """Filtres pour la liste des documents."""
    employee_id: Optional[UUID] = None
    document_type: Optional[VaultDocumentType] = None
    category_id: Optional[UUID] = None
    status: Optional[VaultDocumentStatus] = None
    signature_status: Optional[SignatureStatus] = None

    date_from: Optional[date] = None
    date_to: Optional[date] = None
    pay_period: Optional[str] = None

    search: Optional[str] = None
    tags: Optional[list[str]] = None

    include_deleted: bool = False


class VaultDocumentListResponse(BaseModel):
    """Reponse liste de documents avec pagination."""
    items: list[VaultDocumentResponse]
    total: int
    page: int
    page_size: int
    pages: int


class VaultAccessLogFilters(BaseModel):
    """Filtres pour les logs d'acces."""
    document_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    accessed_by: Optional[UUID] = None
    access_type: Optional[VaultAccessType] = None

    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    success_only: bool = False


class VaultAccessLogListResponse(BaseModel):
    """Reponse liste de logs d'acces."""
    items: list[VaultAccessLogResponse]
    total: int
    page: int
    page_size: int
