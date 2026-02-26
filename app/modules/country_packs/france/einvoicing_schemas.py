"""
AZALS - Schémas E-Invoicing France 2026
========================================

Schémas Pydantic pour l'API de facturation électronique.
Multi-tenant avec intégration aux données financières.
"""
from __future__ import annotations


import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# ENUMS POUR SCHEMAS
# =============================================================================

class PDPProviderType(str, enum.Enum):
    """Types de providers PDP."""
    CHORUS_PRO = "chorus_pro"
    PPF = "ppf"
    YOOZ = "yooz"
    DOCAPOSTE = "docaposte"
    SAGE = "sage"
    CEGID = "cegid"
    GENERIX = "generix"
    EDICOM = "edicom"
    BASWARE = "basware"
    CUSTOM = "custom"


class EInvoiceStatus(str, enum.Enum):
    """Statuts de facture électronique."""
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    RECEIVED = "RECEIVED"
    ACCEPTED = "ACCEPTED"
    REFUSED = "REFUSED"
    PAID = "PAID"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"


class EInvoiceDirection(str, enum.Enum):
    """Direction de la facture."""
    OUTBOUND = "OUTBOUND"
    INBOUND = "INBOUND"


class EInvoiceFormat(str, enum.Enum):
    """Formats supportés."""
    FACTURX_MINIMUM = "FACTURX_MINIMUM"
    FACTURX_BASIC = "FACTURX_BASIC"
    FACTURX_EN16931 = "FACTURX_EN16931"
    FACTURX_EXTENDED = "FACTURX_EXTENDED"
    UBL_21 = "UBL_21"
    CII_D16B = "CII_D16B"


class CompanySizeType(str, enum.Enum):
    """Taille d'entreprise pour obligations."""
    GE = "GE"
    ETI = "ETI"
    PME = "PME"
    MICRO = "MICRO"


class EReportingType(str, enum.Enum):
    """Types d'e-reporting."""
    B2C_DOMESTIC = "B2C_DOMESTIC"
    B2C_EXPORT = "B2C_EXPORT"
    B2B_INTERNATIONAL = "B2B_INTERNATIONAL"


# =============================================================================
# CONFIGURATION PDP SCHEMAS
# =============================================================================

class PDPConfigBase(BaseModel):
    """Base pour configuration PDP."""
    provider: PDPProviderType
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    api_url: str = Field(..., min_length=1, max_length=500)
    token_url: str | None = Field(None, max_length=500)
    scope: str | None = Field(None, max_length=255)
    siret: str | None = Field(None, pattern=r"^\d{14}$")
    siren: str | None = Field(None, pattern=r"^\d{9}$")
    tva_number: str | None = Field(None, max_length=20)
    company_size: CompanySizeType = CompanySizeType.PME
    is_active: bool = True
    is_default: bool = False
    test_mode: bool = True
    timeout_seconds: int = Field(30, ge=5, le=120)
    retry_count: int = Field(3, ge=0, le=10)
    webhook_url: str | None = Field(None, max_length=500)
    preferred_format: EInvoiceFormat = EInvoiceFormat.FACTURX_EN16931
    generate_pdf: bool = True
    provider_options: dict[str, Any] = Field(default_factory=dict)
    custom_endpoints: dict[str, str] = Field(default_factory=dict)


class PDPConfigCreate(PDPConfigBase):
    """Création de configuration PDP."""
    client_id: str | None = Field(None, max_length=255)
    client_secret: str | None = Field(None, max_length=500)
    certificate_ref: str | None = Field(None, max_length=255)
    private_key_ref: str | None = Field(None, max_length=255)
    webhook_secret: str | None = Field(None, max_length=255)


class PDPConfigUpdate(BaseModel):
    """Mise à jour configuration PDP."""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    api_url: str | None = Field(None, min_length=1, max_length=500)
    token_url: str | None = Field(None, max_length=500)
    client_id: str | None = Field(None, max_length=255)
    client_secret: str | None = Field(None, max_length=500)
    scope: str | None = Field(None, max_length=255)
    siret: str | None = Field(None, pattern=r"^\d{14}$")
    siren: str | None = Field(None, pattern=r"^\d{9}$")
    tva_number: str | None = Field(None, max_length=20)
    company_size: CompanySizeType | None = None
    is_active: bool | None = None
    is_default: bool | None = None
    test_mode: bool | None = None
    timeout_seconds: int | None = Field(None, ge=5, le=120)
    retry_count: int | None = Field(None, ge=0, le=10)
    webhook_url: str | None = Field(None, max_length=500)
    webhook_secret: str | None = Field(None, max_length=255)
    preferred_format: EInvoiceFormat | None = None
    generate_pdf: bool | None = None
    provider_options: dict[str, Any] | None = None
    custom_endpoints: dict[str, str] | None = None


class PDPConfigResponse(PDPConfigBase):
    """Réponse configuration PDP."""
    id: UUID
    tenant_id: str
    has_credentials: bool = False
    has_certificate: bool = False
    last_sync_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PDPConfigListResponse(BaseModel):
    """Liste de configurations PDP."""
    items: list[PDPConfigResponse]
    total: int


# =============================================================================
# FACTURE ELECTRONIQUE SCHEMAS
# =============================================================================

class VATBreakdownItem(BaseModel):
    """Détail TVA par taux."""
    rate: Decimal = Field(..., ge=0, le=100)
    base_amount: Decimal
    tax_amount: Decimal


class EInvoiceLineCreate(BaseModel):
    """Ligne de facture pour e-invoicing."""
    description: str
    quantity: Decimal = Field(default=Decimal("1"))
    unit: str = "C62"  # Code UN/ECE
    unit_price: Decimal
    discount_percent: Decimal = Field(default=Decimal("0"))
    vat_rate: Decimal = Field(default=Decimal("20"))
    vat_category: str = "S"  # Standard rate
    item_code: str | None = None
    item_name: str | None = None


class EInvoiceParty(BaseModel):
    """Partie (vendeur/acheteur) pour e-invoicing."""
    name: str
    siret: str | None = Field(None, pattern=r"^\d{14}$")
    siren: str | None = Field(None, pattern=r"^\d{9}$")
    vat_number: str | None = None
    routing_id: str | None = None  # ID routage PDP/PPF
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country_code: str = "FR"
    email: str | None = None
    phone: str | None = None


class EInvoiceCreateFromSource(BaseModel):
    """Création e-invoice depuis document source existant."""
    source_type: str = Field(..., pattern=r"^(INVOICE|CREDIT_NOTE|PURCHASE_INVOICE)$")
    source_id: UUID
    pdp_config_id: UUID | None = None
    format: EInvoiceFormat = EInvoiceFormat.FACTURX_EN16931
    generate_pdf: bool = True
    auto_submit: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class EInvoiceCreateManual(BaseModel):
    """Création manuelle d'e-invoice."""
    direction: EInvoiceDirection
    invoice_number: str = Field(..., min_length=1, max_length=100)
    invoice_type: str = Field(default="380")  # 380=Invoice, 381=Credit Note
    format: EInvoiceFormat = EInvoiceFormat.FACTURX_EN16931
    issue_date: date
    due_date: date | None = None
    currency: str = Field(default="EUR", max_length=3)
    seller: EInvoiceParty
    buyer: EInvoiceParty
    lines: list[EInvoiceLineCreate] = Field(..., min_length=1)
    payment_terms: str | None = None
    payment_means_code: str = "30"  # Credit transfer
    notes: str | None = None
    pdp_config_id: UUID | None = None
    generate_pdf: bool = True
    auto_submit: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class EInvoiceResponse(BaseModel):
    """Réponse facture électronique."""
    id: UUID
    tenant_id: str
    direction: EInvoiceDirection
    invoice_number: str
    invoice_type: str
    format: EInvoiceFormat
    status: EInvoiceStatus
    lifecycle_status: str | None = None
    issue_date: date
    due_date: date | None = None
    currency: str
    total_ht: Decimal
    total_tva: Decimal
    total_ttc: Decimal
    vat_breakdown: dict[str, Decimal]
    seller_name: str | None = None
    seller_siret: str | None = None
    buyer_name: str | None = None
    buyer_siret: str | None = None
    transaction_id: str | None = None
    ppf_id: str | None = None
    pdp_id: str | None = None
    source_type: str | None = None
    source_invoice_id: UUID | None = None
    is_valid: bool
    validation_errors: list[str]
    validation_warnings: list[str]
    last_error: str | None = None
    submission_date: datetime | None = None
    pdp_config_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EInvoiceDetailResponse(EInvoiceResponse):
    """Réponse détaillée avec XML et événements."""
    xml_content: str | None = None
    xml_hash: str | None = None
    pdf_storage_ref: str | None = None
    lifecycle_events: list["LifecycleEventResponse"] = []
    metadata: dict[str, Any] = {}


class EInvoiceListResponse(BaseModel):
    """Liste paginée de factures électroniques."""
    items: list[EInvoiceResponse]
    total: int
    page: int
    page_size: int


class EInvoiceSubmitResponse(BaseModel):
    """Réponse de soumission au PDP."""
    einvoice_id: UUID
    transaction_id: str | None = None
    ppf_id: str | None = None
    pdp_id: str | None = None
    status: EInvoiceStatus
    message: str | None = None
    submitted_at: datetime


class EInvoiceStatusUpdate(BaseModel):
    """Mise à jour de statut."""
    status: EInvoiceStatus
    lifecycle_status: str | None = None
    message: str | None = None
    actor: str | None = None
    source: str | None = None  # PPF, PDP, WEBHOOK, MANUAL


# =============================================================================
# LIFECYCLE EVENT SCHEMAS
# =============================================================================

class LifecycleEventCreate(BaseModel):
    """Création d'événement lifecycle."""
    status: str
    actor: str | None = None
    message: str | None = None
    source: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class LifecycleEventResponse(BaseModel):
    """Réponse événement lifecycle."""
    id: UUID
    einvoice_id: UUID
    status: str
    timestamp: datetime
    actor: str | None = None
    message: str | None = None
    source: str | None = None
    details: dict[str, Any]

    model_config = {"from_attributes": True}


# =============================================================================
# E-REPORTING SCHEMAS
# =============================================================================

class EReportingLineCreate(BaseModel):
    """Ligne de données e-reporting."""
    date: date
    description: str
    amount_ht: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    category: str | None = None


class EReportingCreate(BaseModel):
    """Création soumission e-reporting."""
    period: str = Field(..., pattern=r"^\d{4}-\d{2}$")  # YYYY-MM
    reporting_type: EReportingType
    lines: list[EReportingLineCreate] = Field(default_factory=list)
    pdp_config_id: UUID | None = None


class EReportingResponse(BaseModel):
    """Réponse e-reporting."""
    id: UUID
    tenant_id: str
    period: str
    reporting_type: str
    status: str
    total_ht: Decimal
    total_tva: Decimal
    total_ttc: Decimal
    transaction_count: int
    vat_breakdown: dict[str, Decimal]
    submission_id: str | None = None
    ppf_reference: str | None = None
    submitted_at: datetime | None = None
    response_at: datetime | None = None
    errors: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EReportingListResponse(BaseModel):
    """Liste e-reporting."""
    items: list[EReportingResponse]
    total: int


class EReportingSubmitResponse(BaseModel):
    """Réponse soumission e-reporting."""
    ereporting_id: UUID
    submission_id: str | None = None
    ppf_reference: str | None = None
    status: str
    message: str | None = None
    submitted_at: datetime


# =============================================================================
# STATISTIQUES SCHEMAS
# =============================================================================

class EInvoiceStatsResponse(BaseModel):
    """Statistiques e-invoicing."""
    period: str
    outbound_total: int
    outbound_sent: int
    outbound_delivered: int
    outbound_accepted: int
    outbound_refused: int
    outbound_errors: int
    inbound_total: int
    inbound_received: int
    inbound_accepted: int
    inbound_refused: int
    outbound_amount_ttc: Decimal
    inbound_amount_ttc: Decimal
    ereporting_submitted: int
    ereporting_amount: Decimal

    model_config = {"from_attributes": True}


class EInvoiceStatsSummary(BaseModel):
    """Résumé des statistiques."""
    current_month: EInvoiceStatsResponse | None = None
    previous_month: EInvoiceStatsResponse | None = None
    year_to_date: dict[str, int | Decimal] = Field(default_factory=dict)


# =============================================================================
# VALIDATION SCHEMAS
# =============================================================================

class ValidationResult(BaseModel):
    """Résultat de validation."""
    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    profile: str | None = None
    format: EInvoiceFormat | None = None


class EInvoiceValidateRequest(BaseModel):
    """Demande de validation."""
    xml_content: str | None = None
    einvoice_id: UUID | None = None
    validate_business_rules: bool = True
    validate_schema: bool = True


# =============================================================================
# WEBHOOK SCHEMAS
# =============================================================================

class PDPWebhookPayload(BaseModel):
    """Payload webhook PDP."""
    event_type: str
    invoice_id: str | None = None
    ppf_id: str | None = None
    pdp_id: str | None = None
    status: str | None = None
    lifecycle_status: str | None = None
    timestamp: datetime
    actor: str | None = None
    message: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    signature: str | None = None


class WebhookResponse(BaseModel):
    """Réponse webhook."""
    received: bool
    processed: bool
    message: str | None = None


# =============================================================================
# DASHBOARD SCHEMAS
# =============================================================================

class EInvoiceDashboard(BaseModel):
    """Dashboard e-invoicing."""
    # Configuration
    active_pdp_configs: int
    default_pdp: PDPConfigResponse | None = None

    # Statistiques du mois
    outbound_this_month: int
    inbound_this_month: int
    pending_actions: int
    errors_count: int

    # Dernières factures
    recent_outbound: list[EInvoiceResponse] = []
    recent_inbound: list[EInvoiceResponse] = []
    recent_errors: list[EInvoiceResponse] = []

    # e-Reporting
    ereporting_pending: int
    ereporting_current_period: EReportingResponse | None = None

    # Alertes
    alerts: list[str] = []


# =============================================================================
# BULK OPERATIONS
# =============================================================================

class BulkSubmitRequest(BaseModel):
    """Soumission en masse."""
    einvoice_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    pdp_config_id: UUID | None = None


class BulkSubmitResponse(BaseModel):
    """Résultat soumission en masse."""
    total: int
    submitted: int
    failed: int
    results: list[dict[str, Any]]


class BulkGenerateRequest(BaseModel):
    """Génération en masse depuis documents."""
    source_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    source_type: str = Field(..., pattern=r"^(INVOICE|CREDIT_NOTE|PURCHASE_INVOICE)$")
    format: EInvoiceFormat = EInvoiceFormat.FACTURX_EN16931
    pdp_config_id: UUID | None = None


class BulkGenerateResponse(BaseModel):
    """Résultat génération en masse."""
    total: int
    generated: int
    failed: int
    einvoice_ids: list[UUID]
    errors: list[dict[str, str]]


# =============================================================================
# SEARCH/FILTER SCHEMAS
# =============================================================================

class EInvoiceFilter(BaseModel):
    """Filtres de recherche."""
    direction: EInvoiceDirection | None = None
    status: EInvoiceStatus | None = None
    format: EInvoiceFormat | None = None
    pdp_config_id: UUID | None = None
    date_from: date | None = None
    date_to: date | None = None
    seller_siret: str | None = None
    buyer_siret: str | None = None
    search: str | None = None
    source_type: str | None = None
    has_errors: bool | None = None


# =============================================================================
# INBOUND INVOICE RECEPTION SCHEMAS
# =============================================================================

class InboundInvoiceXML(BaseModel):
    """Réception facture entrante via XML Factur-X."""
    xml_content: str = Field(..., description="Contenu XML Factur-X ou UBL")
    pdf_base64: str | None = Field(None, description="PDF en base64 (optionnel)")
    source_pdp: str | None = Field(None, description="PDP source (ex: PPF, Chorus Pro)")
    ppf_id: str | None = Field(None, description="Référence PPF")
    pdp_id: str | None = Field(None, description="Référence PDP")
    routing_id: str | None = Field(None, description="ID routage destinataire")
    received_at: datetime | None = Field(None, description="Date/heure réception")
    metadata: dict[str, Any] = Field(default_factory=dict)


class InboundInvoiceParsed(BaseModel):
    """Réception facture entrante avec données parsées."""
    invoice_number: str
    invoice_type: str = "380"
    format: EInvoiceFormat = EInvoiceFormat.FACTURX_EN16931
    issue_date: date
    due_date: date | None = None
    currency: str = "EUR"
    seller: EInvoiceParty
    buyer: EInvoiceParty
    lines: list[EInvoiceLineCreate] = Field(default_factory=list)
    total_ht: Decimal
    total_tva: Decimal
    total_ttc: Decimal
    vat_breakdown: dict[str, Decimal] = Field(default_factory=dict)
    xml_content: str | None = None
    pdf_base64: str | None = None
    source_pdp: str | None = None
    ppf_id: str | None = None
    pdp_id: str | None = None
    received_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class InboundInvoiceResponse(BaseModel):
    """Réponse de réception facture entrante."""
    einvoice_id: UUID
    invoice_number: str
    seller_name: str | None
    seller_siret: str | None
    total_ttc: Decimal
    status: EInvoiceStatus
    validation_result: ValidationResult
    message: str
    received_at: datetime


class InboundBatchRequest(BaseModel):
    """Réception en masse de factures entrantes."""
    invoices: list[InboundInvoiceXML] = Field(..., min_length=1, max_length=50)


class InboundBatchResponse(BaseModel):
    """Réponse réception en masse."""
    total: int
    received: int
    failed: int
    results: list[dict[str, Any]]


# Forward reference resolution
EInvoiceDetailResponse.model_rebuild()
