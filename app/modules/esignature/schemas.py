"""
AZALS MODULE ESIGNATURE - Schemas Pydantic
==========================================

Schemas de validation pour la signature electronique.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict


# =============================================================================
# ENUMS (copies pour Pydantic)
# =============================================================================

class SignatureProvider(str, Enum):
    INTERNAL = "internal"
    YOUSIGN = "yousign"
    DOCUSIGN = "docusign"
    HELLOSIGN = "hellosign"
    ADOBE_SIGN = "adobe_sign"


class SignatureLevel(str, Enum):
    SIMPLE = "simple"
    ADVANCED = "advanced"
    QUALIFIED = "qualified"


class EnvelopeStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    VOIDED = "voided"


class SignerStatus(str, Enum):
    PENDING = "pending"
    NOTIFIED = "notified"
    VIEWED = "viewed"
    SIGNED = "signed"
    DECLINED = "declined"
    DELEGATED = "delegated"
    EXPIRED = "expired"


class DocumentType(str, Enum):
    CONTRACT = "contract"
    INVOICE = "invoice"
    QUOTE = "quote"
    PURCHASE_ORDER = "purchase_order"
    NDA = "nda"
    EMPLOYMENT = "employment"
    AMENDMENT = "amendment"
    MANDATE = "mandate"
    GDPR_CONSENT = "gdpr_consent"
    LEASE = "lease"
    LOAN = "loan"
    POLICY = "policy"
    OTHER = "other"


class FieldType(str, Enum):
    SIGNATURE = "signature"
    INITIALS = "initials"
    DATE = "date"
    TEXT = "text"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DROPDOWN = "dropdown"
    ATTACHMENT = "attachment"
    COMPANY_STAMP = "company_stamp"


class AuthMethod(str, Enum):
    EMAIL = "email"
    SMS_OTP = "sms_otp"
    EMAIL_OTP = "email_otp"
    ID_VERIFICATION = "id_verification"
    KNOWLEDGE_BASED = "knowledge_based"
    TWO_FACTOR = "two_factor"


class TemplateCategory(str, Enum):
    SALES = "sales"
    HR = "hr"
    LEGAL = "legal"
    FINANCE = "finance"
    PROCUREMENT = "procurement"
    OPERATIONS = "operations"
    CUSTOM = "custom"


class AuditEventType(str, Enum):
    CREATED = "created"
    SENT = "sent"
    VIEWED = "viewed"
    SIGNED = "signed"
    DECLINED = "declined"
    DELEGATED = "delegated"
    REMINDER_SENT = "reminder_sent"
    DOWNLOADED = "downloaded"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    COMPLETED = "completed"
    VOIDED = "voided"


# =============================================================================
# CONFIG SCHEMAS
# =============================================================================

class ESignatureConfigBase(BaseModel):
    """Schema de base pour la configuration."""
    default_provider: SignatureProvider = SignatureProvider.INTERNAL
    default_signature_level: SignatureLevel = SignatureLevel.SIMPLE
    default_expiry_days: int = Field(default=30, ge=1, le=365)
    max_expiry_days: int = Field(default=90, ge=1, le=365)
    auto_reminders_enabled: bool = True
    reminder_interval_days: int = Field(default=3, ge=1, le=30)
    max_reminders: int = Field(default=5, ge=0, le=20)
    notify_on_view: bool = True
    notify_on_sign: bool = True
    notify_on_complete: bool = True
    notify_on_decline: bool = True
    require_auth_before_view: bool = False
    allow_decline: bool = True
    allow_delegation: bool = True
    require_approval_before_send: bool = False


class ESignatureConfigCreate(ESignatureConfigBase):
    """Creation de configuration."""
    company_logo_url: Optional[str] = None
    primary_color: str = Field(default="#1976D2", pattern=r"^#[0-9A-Fa-f]{6}$")
    email_footer: Optional[str] = None


class ESignatureConfigUpdate(BaseModel):
    """Mise a jour de configuration."""
    default_provider: Optional[SignatureProvider] = None
    default_signature_level: Optional[SignatureLevel] = None
    default_expiry_days: Optional[int] = Field(None, ge=1, le=365)
    max_expiry_days: Optional[int] = Field(None, ge=1, le=365)
    auto_reminders_enabled: Optional[bool] = None
    reminder_interval_days: Optional[int] = Field(None, ge=1, le=30)
    max_reminders: Optional[int] = Field(None, ge=0, le=20)
    company_logo_url: Optional[str] = None
    primary_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    email_footer: Optional[str] = None
    notify_on_view: Optional[bool] = None
    notify_on_sign: Optional[bool] = None
    notify_on_complete: Optional[bool] = None
    notify_on_decline: Optional[bool] = None
    require_auth_before_view: Optional[bool] = None
    allow_decline: Optional[bool] = None
    allow_delegation: Optional[bool] = None
    require_approval_before_send: Optional[bool] = None


class ESignatureConfigResponse(ESignatureConfigBase):
    """Reponse configuration."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    company_logo_url: Optional[str] = None
    primary_color: str = "#1976D2"
    email_footer: Optional[str] = None
    auto_archive_days: int = 365
    retention_years: int = 10
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None


# =============================================================================
# PROVIDER CREDENTIAL SCHEMAS
# =============================================================================

class ProviderCredentialCreate(BaseModel):
    """Creation de credentials provider."""
    provider: SignatureProvider
    environment: str = Field(default="production", pattern=r"^(production|sandbox)$")
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    account_id: Optional[str] = None
    user_id: Optional[str] = None
    private_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    webhook_url: Optional[str] = None


class ProviderCredentialUpdate(BaseModel):
    """Mise a jour credentials."""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    account_id: Optional[str] = None
    user_id: Optional[str] = None
    private_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    webhook_url: Optional[str] = None
    is_active: Optional[bool] = None


class ProviderCredentialResponse(BaseModel):
    """Reponse credentials (sans secrets)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    provider: SignatureProvider
    environment: str
    account_id: Optional[str] = None
    user_id: Optional[str] = None
    webhook_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    last_verified_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# =============================================================================
# TEMPLATE SCHEMAS
# =============================================================================

class TemplateFieldBase(BaseModel):
    """Champ de template."""
    field_type: FieldType
    page: int = Field(ge=1)
    x_position: float = Field(ge=0, le=100)
    y_position: float = Field(ge=0, le=100)
    width: float = Field(default=150, ge=10)
    height: float = Field(default=50, ge=10)
    signer_role: Optional[str] = Field(None, max_length=50)
    label: Optional[str] = Field(None, max_length=255)
    placeholder: Optional[str] = Field(None, max_length=255)
    tooltip: Optional[str] = Field(None, max_length=500)
    is_required: bool = True
    is_read_only: bool = False
    validation_regex: Optional[str] = Field(None, max_length=500)
    min_length: Optional[int] = Field(None, ge=0)
    max_length: Optional[int] = Field(None, ge=1)
    options: Optional[List[str]] = None
    tab_order: int = Field(default=0, ge=0)


class TemplateFieldCreate(TemplateFieldBase):
    """Creation champ template."""
    pass


class TemplateFieldResponse(TemplateFieldBase):
    """Reponse champ template."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    template_id: UUID
    created_at: datetime


class SignerRoleSchema(BaseModel):
    """Role signataire dans un template."""
    role: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    order: int = Field(default=1, ge=1)
    is_required: bool = True
    auth_method: AuthMethod = AuthMethod.EMAIL
    allow_delegation: bool = True


class MergeFieldSchema(BaseModel):
    """Champ de fusion pour template."""
    name: str = Field(..., max_length=100)
    label: str = Field(..., max_length=255)
    field_type: str = Field(default="text", pattern=r"^(text|number|date|email|phone)$")
    is_required: bool = False
    default_value: Optional[str] = None


class SignatureTemplateBase(BaseModel):
    """Schema de base pour template."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: TemplateCategory = TemplateCategory.CUSTOM
    document_type: DocumentType = DocumentType.OTHER
    default_signature_level: SignatureLevel = SignatureLevel.SIMPLE
    default_expiry_days: int = Field(default=30, ge=1, le=365)
    email_subject: Optional[str] = Field(None, max_length=500)
    email_body: Optional[str] = None
    sms_message: Optional[str] = Field(None, max_length=160)
    signer_roles: List[SignerRoleSchema] = Field(default_factory=list)
    merge_fields: List[MergeFieldSchema] = Field(default_factory=list)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()


class SignatureTemplateCreate(SignatureTemplateBase):
    """Creation template."""
    fields: List[TemplateFieldCreate] = Field(default_factory=list)


class SignatureTemplateUpdate(BaseModel):
    """Mise a jour template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[TemplateCategory] = None
    document_type: Optional[DocumentType] = None
    default_signature_level: Optional[SignatureLevel] = None
    default_expiry_days: Optional[int] = Field(None, ge=1, le=365)
    email_subject: Optional[str] = Field(None, max_length=500)
    email_body: Optional[str] = None
    sms_message: Optional[str] = Field(None, max_length=160)
    signer_roles: Optional[List[SignerRoleSchema]] = None
    merge_fields: Optional[List[MergeFieldSchema]] = None
    is_active: Optional[bool] = None


class SignatureTemplateResponse(SignatureTemplateBase):
    """Reponse template."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    is_active: bool = True
    is_locked: bool = False
    version: int = 1
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    fields: List[TemplateFieldResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None


class SignatureTemplateListItem(BaseModel):
    """Item liste templates."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    category: TemplateCategory
    document_type: DocumentType
    is_active: bool
    usage_count: int
    created_at: datetime


class SignatureTemplateList(BaseModel):
    """Liste paginee templates."""
    items: List[SignatureTemplateListItem]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# SIGNER SCHEMAS
# =============================================================================

class SignerBase(BaseModel):
    """Schema de base signataire."""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=100)
    role: str = Field(default="signer", max_length=50)
    signing_order: int = Field(default=1, ge=1)
    is_required: bool = True
    auth_method: AuthMethod = AuthMethod.EMAIL
    require_id_verification: bool = False
    personal_message: Optional[str] = None


class SignerCreate(SignerBase):
    """Creation signataire."""
    user_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None


class SignerUpdate(BaseModel):
    """Mise a jour signataire."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    signing_order: Optional[int] = Field(None, ge=1)
    auth_method: Optional[AuthMethod] = None
    personal_message: Optional[str] = None


class SignerResponse(SignerBase):
    """Reponse signataire."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    envelope_id: UUID
    status: SignerStatus
    status_message: Optional[str] = None
    notified_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None
    decline_reason: Optional[str] = None
    delegated_to_email: Optional[str] = None
    external_url: Optional[str] = None
    user_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    created_at: datetime


# =============================================================================
# DOCUMENT SCHEMAS
# =============================================================================

class DocumentFieldCreate(BaseModel):
    """Creation champ document."""
    field_type: FieldType
    page: int = Field(ge=1)
    x_position: float = Field(ge=0, le=100)
    y_position: float = Field(ge=0, le=100)
    width: float = Field(default=150, ge=10)
    height: float = Field(default=50, ge=10)
    signer_index: int = Field(default=0, ge=0)  # Index du signataire dans la liste
    name: Optional[str] = Field(None, max_length=100)
    label: Optional[str] = Field(None, max_length=255)
    is_required: bool = True
    options: Optional[List[str]] = None


class DocumentFieldResponse(BaseModel):
    """Reponse champ document."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    signer_id: Optional[UUID] = None
    field_type: FieldType
    page: int
    x_position: float
    y_position: float
    width: float
    height: float
    name: Optional[str] = None
    label: Optional[str] = None
    is_required: bool
    value: Optional[str] = None
    filled_at: Optional[datetime] = None


class EnvelopeDocumentCreate(BaseModel):
    """Creation document dans enveloppe."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    document_order: int = Field(default=1, ge=1)
    # Le fichier sera envoye en multipart


class EnvelopeDocumentResponse(BaseModel):
    """Reponse document."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    envelope_id: UUID
    name: str
    description: Optional[str] = None
    document_order: int
    original_file_name: str
    original_file_size: int
    page_count: Optional[int] = None
    is_signed: bool
    signed_at: Optional[datetime] = None
    fields: List[DocumentFieldResponse] = Field(default_factory=list)
    created_at: datetime


# =============================================================================
# ENVELOPE SCHEMAS
# =============================================================================

class EnvelopeBase(BaseModel):
    """Schema de base enveloppe."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[UUID] = None
    reference_number: Optional[str] = Field(None, max_length=50)
    provider: SignatureProvider = SignatureProvider.INTERNAL
    signature_level: SignatureLevel = SignatureLevel.SIMPLE
    document_type: DocumentType = DocumentType.OTHER
    expires_at: Optional[datetime] = None
    email_subject: Optional[str] = Field(None, max_length=500)
    email_body: Optional[str] = None
    sms_message: Optional[str] = Field(None, max_length=160)
    reminder_enabled: bool = True
    reminder_interval_days: int = Field(default=3, ge=1, le=30)
    callback_url: Optional[str] = None
    redirect_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class EnvelopeCreate(EnvelopeBase):
    """Creation enveloppe."""
    template_id: Optional[UUID] = None
    signers: List[SignerCreate] = Field(..., min_length=1)
    requires_approval: bool = False


class EnvelopeCreateFromTemplate(BaseModel):
    """Creation enveloppe depuis template."""
    template_id: UUID
    name: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    reference_number: Optional[str] = None
    signers: List[SignerCreate] = Field(..., min_length=1)
    merge_values: Dict[str, str] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EnvelopeUpdate(BaseModel):
    """Mise a jour enveloppe (draft uniquement)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    expires_at: Optional[datetime] = None
    email_subject: Optional[str] = Field(None, max_length=500)
    email_body: Optional[str] = None
    reminder_enabled: Optional[bool] = None
    reminder_interval_days: Optional[int] = Field(None, ge=1, le=30)
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class EnvelopeResponse(EnvelopeBase):
    """Reponse enveloppe."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    envelope_number: str
    template_id: Optional[UUID] = None
    status: EnvelopeStatus
    status_message: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    reminder_count: int = 0
    last_reminder_at: Optional[datetime] = None
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    total_signers: int = 0
    signed_count: int = 0
    viewed_count: int = 0
    requires_approval: bool = False
    approval_status: Optional[str] = None
    is_archived: bool = False
    version: int = 1
    documents: List[EnvelopeDocumentResponse] = Field(default_factory=list)
    signers: List[SignerResponse] = Field(default_factory=list)
    created_by: Optional[UUID] = None
    updated_at: Optional[datetime] = None


class EnvelopeListItem(BaseModel):
    """Item liste enveloppes."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    envelope_number: str
    name: str
    status: EnvelopeStatus
    document_type: DocumentType
    provider: SignatureProvider
    total_signers: int
    signed_count: int
    expires_at: Optional[datetime] = None
    created_at: datetime
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reference_type: Optional[str] = None
    reference_number: Optional[str] = None


class EnvelopeList(BaseModel):
    """Liste paginee enveloppes."""
    items: List[EnvelopeListItem]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# ACTION SCHEMAS
# =============================================================================

class SendEnvelopeRequest(BaseModel):
    """Demande d'envoi d'enveloppe."""
    custom_message: Optional[str] = None
    schedule_at: Optional[datetime] = None


class CancelEnvelopeRequest(BaseModel):
    """Demande d'annulation."""
    reason: str = Field(..., min_length=1, max_length=500)
    notify_signers: bool = True


class VoidEnvelopeRequest(BaseModel):
    """Demande d'invalidation."""
    reason: str = Field(..., min_length=1, max_length=500)


class SendReminderRequest(BaseModel):
    """Demande d'envoi de rappel."""
    signer_ids: Optional[List[UUID]] = None  # Si vide, tous les signataires en attente
    custom_message: Optional[str] = None
    channel: str = Field(default="email", pattern=r"^(email|sms)$")


class DeclineRequest(BaseModel):
    """Demande de refus par signataire."""
    reason: str = Field(..., min_length=1, max_length=1000)


class DelegateRequest(BaseModel):
    """Demande de delegation."""
    delegate_email: EmailStr
    delegate_first_name: str = Field(..., min_length=1, max_length=100)
    delegate_last_name: str = Field(..., min_length=1, max_length=100)
    reason: Optional[str] = Field(None, max_length=500)


class ApproveEnvelopeRequest(BaseModel):
    """Approbation avant envoi."""
    comments: Optional[str] = None


class RejectEnvelopeRequest(BaseModel):
    """Rejet avant envoi."""
    reason: str = Field(..., min_length=1, max_length=500)


# =============================================================================
# AUDIT SCHEMAS
# =============================================================================

class AuditEventResponse(BaseModel):
    """Reponse evenement audit."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    envelope_id: UUID
    event_type: AuditEventType
    event_description: Optional[str] = None
    actor_type: str
    actor_email: Optional[str] = None
    actor_name: Optional[str] = None
    ip_address: Optional[str] = None
    document_id: Optional[UUID] = None
    signer_id: Optional[UUID] = None
    event_at: datetime


class AuditTrailResponse(BaseModel):
    """Audit trail complet."""
    envelope_id: UUID
    envelope_number: str
    envelope_name: str
    events: List[AuditEventResponse]
    total_events: int
    first_event_at: datetime
    last_event_at: datetime


# =============================================================================
# CERTIFICATE SCHEMAS
# =============================================================================

class CertificateResponse(BaseModel):
    """Reponse certificat."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    envelope_id: UUID
    certificate_number: str
    certificate_type: str
    file_hash: str
    timestamp_authority: Optional[str] = None
    timestamped_at: Optional[datetime] = None
    valid_from: datetime
    valid_until: Optional[datetime] = None
    is_valid: bool
    verification_url: Optional[str] = None
    verification_code: Optional[str] = None
    generated_at: datetime


# =============================================================================
# STATISTICS SCHEMAS
# =============================================================================

class SignatureStatsResponse(BaseModel):
    """Statistiques signature."""
    tenant_id: str
    period_type: str
    period_start: date
    period_end: date
    envelopes_created: int = 0
    envelopes_sent: int = 0
    envelopes_completed: int = 0
    envelopes_declined: int = 0
    envelopes_expired: int = 0
    envelopes_cancelled: int = 0
    total_signers: int = 0
    signers_signed: int = 0
    signers_declined: int = 0
    avg_completion_hours: Optional[float] = None
    completion_rate: float = 0.0
    by_provider: Dict[str, int] = Field(default_factory=dict)
    by_document_type: Dict[str, int] = Field(default_factory=dict)
    by_signature_level: Dict[str, int] = Field(default_factory=dict)


class DashboardStatsResponse(BaseModel):
    """Stats tableau de bord."""
    tenant_id: str
    today: SignatureStatsResponse
    this_month: SignatureStatsResponse
    pending_envelopes: int
    pending_signatures: int
    expiring_soon: int  # Expirant dans 3 jours
    recent_completions: List[EnvelopeListItem]


# =============================================================================
# WEBHOOK SCHEMAS
# =============================================================================

class WebhookPayload(BaseModel):
    """Payload webhook entrant."""
    provider: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str] = None


class WebhookResponse(BaseModel):
    """Reponse webhook."""
    success: bool
    message: str
    envelope_id: Optional[UUID] = None


# =============================================================================
# FILTER SCHEMAS
# =============================================================================

class EnvelopeFilters(BaseModel):
    """Filtres pour liste enveloppes."""
    search: Optional[str] = Field(None, min_length=2)
    status: Optional[List[EnvelopeStatus]] = None
    provider: Optional[SignatureProvider] = None
    document_type: Optional[DocumentType] = None
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    expires_before: Optional[date] = None
    include_archived: bool = False
    include_deleted: bool = False
    tags: Optional[List[str]] = None


class TemplateFilters(BaseModel):
    """Filtres pour liste templates."""
    search: Optional[str] = Field(None, min_length=2)
    category: Optional[TemplateCategory] = None
    document_type: Optional[DocumentType] = None
    is_active: Optional[bool] = None


# =============================================================================
# COMMON SCHEMAS
# =============================================================================

class DownloadResponse(BaseModel):
    """Reponse telechargement."""
    file_name: str
    file_size: int
    mime_type: str
    download_url: str
    expires_at: datetime


class BulkActionRequest(BaseModel):
    """Action en masse."""
    envelope_ids: List[UUID] = Field(..., min_length=1, max_length=100)
    action: str = Field(..., pattern=r"^(send|cancel|void|remind|archive)$")
    reason: Optional[str] = None


class BulkActionResponse(BaseModel):
    """Reponse action en masse."""
    total: int
    success: int
    failed: int
    errors: Dict[str, str] = Field(default_factory=dict)  # envelope_id -> error message
