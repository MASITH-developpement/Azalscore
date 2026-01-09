"""
AZALS MODULE M2A - Schemas Comptabilité Automatisée
====================================================

Schemas Pydantic pour la validation et sérialisation des données.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator


# ============================================================================
# ENUMS (pour Pydantic)
# ============================================================================

class DocumentTypeEnum(str, Enum):
    INVOICE_RECEIVED = "INVOICE_RECEIVED"
    INVOICE_SENT = "INVOICE_SENT"
    EXPENSE_NOTE = "EXPENSE_NOTE"
    CREDIT_NOTE_RECEIVED = "CREDIT_NOTE_RECEIVED"
    CREDIT_NOTE_SENT = "CREDIT_NOTE_SENT"
    QUOTE = "QUOTE"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    DELIVERY_NOTE = "DELIVERY_NOTE"
    BANK_STATEMENT = "BANK_STATEMENT"
    OTHER = "OTHER"


class DocumentStatusEnum(str, Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    ANALYZED = "ANALYZED"
    PENDING_VALIDATION = "PENDING_VALIDATION"
    VALIDATED = "VALIDATED"
    ACCOUNTED = "ACCOUNTED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"


class DocumentSourceEnum(str, Enum):
    EMAIL = "EMAIL"
    UPLOAD = "UPLOAD"
    MOBILE_SCAN = "MOBILE_SCAN"
    API = "API"
    BANK_SYNC = "BANK_SYNC"
    INTERNAL = "INTERNAL"


class ConfidenceLevelEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"


class PaymentStatusEnum(str, Enum):
    UNPAID = "UNPAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    OVERPAID = "OVERPAID"
    CANCELLED = "CANCELLED"


class BankConnectionStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REQUIRES_ACTION = "REQUIRES_ACTION"
    ERROR = "ERROR"
    DISCONNECTED = "DISCONNECTED"


class ReconciliationStatusEnum(str, Enum):
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    PARTIAL = "PARTIAL"
    MANUAL = "MANUAL"
    UNMATCHED = "UNMATCHED"


class AlertTypeEnum(str, Enum):
    DOCUMENT_UNREADABLE = "DOCUMENT_UNREADABLE"
    MISSING_INFO = "MISSING_INFO"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    DUPLICATE_SUSPECTED = "DUPLICATE_SUSPECTED"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    TAX_ERROR = "TAX_ERROR"
    OVERDUE_PAYMENT = "OVERDUE_PAYMENT"
    CASH_FLOW_WARNING = "CASH_FLOW_WARNING"
    RECONCILIATION_ISSUE = "RECONCILIATION_ISSUE"


class AlertSeverityEnum(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ViewTypeEnum(str, Enum):
    DIRIGEANT = "DIRIGEANT"
    ASSISTANTE = "ASSISTANTE"
    EXPERT_COMPTABLE = "EXPERT_COMPTABLE"


class SyncTypeEnum(str, Enum):
    MANUAL = "MANUAL"
    SCHEDULED = "SCHEDULED"
    ON_DEMAND = "ON_DEMAND"


class SyncStatusEnum(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EmailInboxTypeEnum(str, Enum):
    INVOICES = "INVOICES"
    EXPENSE_NOTES = "EXPENSE_NOTES"
    GENERAL = "GENERAL"


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class BaseSchema(BaseModel):
    """Schema de base avec configuration commune."""

    class Config:
        from_attributes = True
        populate_by_name = True
        use_enum_values = True


# ============================================================================
# DOCUMENT SCHEMAS
# ============================================================================

class DocumentBase(BaseSchema):
    """Base pour les documents."""
    document_type: DocumentTypeEnum
    source: DocumentSourceEnum
    reference: Optional[str] = None
    document_date: Optional[date] = None
    due_date: Optional[date] = None
    partner_name: Optional[str] = None
    partner_tax_id: Optional[str] = None
    amount_untaxed: Optional[Decimal] = None
    amount_tax: Optional[Decimal] = None
    amount_total: Optional[Decimal] = None
    currency: str = "EUR"
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class DocumentCreate(DocumentBase):
    """Création d'un document (upload)."""
    original_filename: Optional[str] = None
    email_from: Optional[str] = None
    email_subject: Optional[str] = None


class DocumentUpdate(BaseSchema):
    """Mise à jour d'un document."""
    reference: Optional[str] = None
    document_date: Optional[date] = None
    due_date: Optional[date] = None
    partner_name: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class DocumentValidate(BaseSchema):
    """Validation d'un document par l'expert."""
    validation_notes: Optional[str] = None
    # Corrections manuelles optionnelles
    corrected_amount_untaxed: Optional[Decimal] = None
    corrected_amount_tax: Optional[Decimal] = None
    corrected_amount_total: Optional[Decimal] = None
    corrected_account_code: Optional[str] = None


class DocumentReject(BaseSchema):
    """Rejet d'un document."""
    rejection_reason: str = Field(..., min_length=5, max_length=500)


class DocumentResponse(DocumentBase):
    """Réponse document."""
    id: UUID
    tenant_id: str
    status: DocumentStatusEnum
    payment_status: PaymentStatusEnum
    original_filename: Optional[str] = None
    file_path: Optional[str] = None
    received_at: datetime
    processed_at: Optional[datetime] = None

    # OCR & IA
    ocr_confidence: Optional[Decimal] = None
    ai_confidence: Optional[ConfidenceLevelEnum] = None
    ai_confidence_score: Optional[Decimal] = None
    ai_suggested_account: Optional[str] = None

    # Paiement
    amount_paid: Decimal = Decimal("0")
    amount_remaining: Optional[Decimal] = None

    # Validation
    requires_validation: bool = False
    validated_by: Optional[UUID] = None
    validated_at: Optional[datetime] = None

    # Écriture comptable
    journal_entry_id: Optional[UUID] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseSchema):
    """Liste de documents avec pagination."""
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentDetailResponse(DocumentResponse):
    """Détail complet d'un document."""
    ocr_raw_text: Optional[str] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    validation_notes: Optional[str] = None

    # Relations
    ocr_results: List["OCRResultResponse"] = Field(default_factory=list)
    ai_classifications: List["AIClassificationResponse"] = Field(default_factory=list)
    auto_entries: List["AutoEntryResponse"] = Field(default_factory=list)


# ============================================================================
# OCR SCHEMAS
# ============================================================================

class ExtractedField(BaseSchema):
    """Champ extrait par OCR."""
    value: Any
    confidence: Decimal
    bounding_box: Optional[Dict[str, float]] = None


class OCRResultCreate(BaseSchema):
    """Création d'un résultat OCR."""
    document_id: UUID
    ocr_engine: str
    ocr_version: Optional[str] = None
    raw_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    extracted_fields: Dict[str, ExtractedField]
    overall_confidence: Optional[Decimal] = None
    processing_time_ms: Optional[int] = None
    image_quality_score: Optional[Decimal] = None
    page_count: int = 1


class OCRResultResponse(BaseSchema):
    """Réponse résultat OCR."""
    id: UUID
    document_id: UUID
    ocr_engine: str
    overall_confidence: Optional[Decimal] = None
    extracted_fields: Dict[str, Any]
    processing_time_ms: Optional[int] = None
    image_quality_score: Optional[Decimal] = None
    page_count: int
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    created_at: datetime


# ============================================================================
# AI CLASSIFICATION SCHEMAS
# ============================================================================

class TaxRateDetail(BaseSchema):
    """Détail d'un taux de TVA."""
    rate: Decimal
    amount: Decimal
    confidence: Decimal


class AIClassificationCreate(BaseSchema):
    """Création d'une classification IA."""
    document_id: UUID
    model_name: str
    model_version: Optional[str] = None
    document_type_predicted: Optional[DocumentTypeEnum] = None
    document_type_confidence: Optional[Decimal] = None
    vendor_name: Optional[str] = None
    vendor_confidence: Optional[Decimal] = None
    invoice_number: Optional[str] = None
    invoice_number_confidence: Optional[Decimal] = None
    invoice_date: Optional[date] = None
    invoice_date_confidence: Optional[Decimal] = None
    due_date: Optional[date] = None
    due_date_confidence: Optional[Decimal] = None
    amount_untaxed: Optional[Decimal] = None
    amount_untaxed_confidence: Optional[Decimal] = None
    amount_tax: Optional[Decimal] = None
    amount_tax_confidence: Optional[Decimal] = None
    amount_total: Optional[Decimal] = None
    amount_total_confidence: Optional[Decimal] = None
    tax_rates: Optional[List[TaxRateDetail]] = None
    suggested_account_code: Optional[str] = None
    suggested_account_confidence: Optional[Decimal] = None
    suggested_journal_code: Optional[str] = None
    suggested_journal_confidence: Optional[Decimal] = None
    expense_category: Optional[str] = None
    expense_category_confidence: Optional[Decimal] = None
    overall_confidence: ConfidenceLevelEnum
    overall_confidence_score: Decimal
    classification_reasons: Optional[List[str]] = None


class AIClassificationResponse(BaseSchema):
    """Réponse classification IA."""
    id: UUID
    document_id: UUID
    model_name: str
    overall_confidence: ConfidenceLevelEnum
    overall_confidence_score: Decimal

    # Extractions principales
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    amount_total: Optional[Decimal] = None

    # Suggestions comptables
    suggested_account_code: Optional[str] = None
    suggested_journal_code: Optional[str] = None
    expense_category: Optional[str] = None

    # Apprentissage
    was_corrected: bool = False
    created_at: datetime


class AIClassificationCorrection(BaseSchema):
    """Correction d'une classification IA (apprentissage)."""
    corrected_account_code: Optional[str] = None
    corrected_journal_code: Optional[str] = None
    corrected_expense_category: Optional[str] = None
    correction_feedback: Optional[str] = None


# ============================================================================
# AUTO ENTRY SCHEMAS
# ============================================================================

class ProposedEntryLine(BaseSchema):
    """Ligne d'écriture proposée."""
    account_code: str
    account_name: Optional[str] = None
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    label: Optional[str] = None


class AutoEntryCreate(BaseSchema):
    """Création d'une écriture automatique."""
    document_id: UUID
    confidence_level: ConfidenceLevelEnum
    confidence_score: Decimal
    entry_template: Optional[str] = None
    accounting_rules_applied: Optional[List[str]] = None
    proposed_lines: List[ProposedEntryLine]


class AutoEntryResponse(BaseSchema):
    """Réponse écriture automatique."""
    id: UUID
    document_id: UUID
    journal_entry_id: Optional[UUID] = None
    confidence_level: ConfidenceLevelEnum
    confidence_score: Decimal
    proposed_lines: List[ProposedEntryLine]
    auto_validated: bool
    requires_review: bool
    is_posted: bool
    created_at: datetime


class AutoEntryValidate(BaseSchema):
    """Validation d'une écriture automatique."""
    approved: bool
    modified_lines: Optional[List[ProposedEntryLine]] = None
    modification_reason: Optional[str] = None


# ============================================================================
# BANK CONNECTION SCHEMAS
# ============================================================================

class BankConnectionCreate(BaseSchema):
    """Création d'une connexion bancaire."""
    provider: str
    institution_id: str
    institution_name: str
    institution_logo_url: Optional[str] = None


class BankConnectionResponse(BaseSchema):
    """Réponse connexion bancaire."""
    id: UUID
    institution_id: str
    institution_name: str
    institution_logo_url: Optional[str] = None
    provider: str
    status: BankConnectionStatusEnum
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    consent_expires_at: Optional[datetime] = None
    linked_accounts: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime


class BankConnectionListResponse(BaseSchema):
    """Liste des connexions bancaires."""
    items: List[BankConnectionResponse]
    total: int


# ============================================================================
# SYNCED ACCOUNT SCHEMAS
# ============================================================================

class SyncedAccountResponse(BaseSchema):
    """Réponse compte synchronisé."""
    id: UUID
    connection_id: UUID
    external_account_id: str
    account_name: str
    account_number_masked: Optional[str] = None
    iban_masked: Optional[str] = None
    account_type: Optional[str] = None
    balance_current: Optional[Decimal] = None
    balance_available: Optional[Decimal] = None
    balance_currency: str = "EUR"
    balance_updated_at: Optional[datetime] = None
    is_sync_enabled: bool = True
    bank_account_id: Optional[UUID] = None  # Lien vers compte interne
    created_at: datetime


class SyncedAccountLink(BaseSchema):
    """Liaison compte synchronisé vers compte interne."""
    bank_account_id: UUID


# ============================================================================
# SYNCED TRANSACTION SCHEMAS
# ============================================================================

class SyncedTransactionResponse(BaseSchema):
    """Réponse transaction synchronisée."""
    id: UUID
    synced_account_id: UUID
    transaction_date: date
    value_date: Optional[date] = None
    amount: Decimal
    currency: str = "EUR"
    description: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    ai_category: Optional[str] = None
    reconciliation_status: ReconciliationStatusEnum
    matched_document_id: Optional[UUID] = None
    match_confidence: Optional[Decimal] = None
    created_at: datetime


class SyncedTransactionListResponse(BaseSchema):
    """Liste de transactions synchronisées."""
    items: List[SyncedTransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    # Agrégats
    total_credits: Decimal = Decimal("0")
    total_debits: Decimal = Decimal("0")


# ============================================================================
# BANK SYNC SESSION SCHEMAS
# ============================================================================

class BankSyncTrigger(BaseSchema):
    """Déclenchement d'une synchronisation bancaire."""
    connection_id: Optional[UUID] = None  # Si None, sync toutes les connexions
    sync_type: SyncTypeEnum = SyncTypeEnum.MANUAL
    sync_from_date: Optional[date] = None
    sync_to_date: Optional[date] = None


class BankSyncSessionResponse(BaseSchema):
    """Réponse session de synchronisation."""
    id: UUID
    connection_id: UUID
    sync_type: SyncTypeEnum
    status: SyncStatusEnum
    sync_from_date: Optional[date] = None
    sync_to_date: Optional[date] = None
    accounts_synced: int = 0
    transactions_fetched: int = 0
    transactions_new: int = 0
    reconciliations_auto: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    created_at: datetime


# ============================================================================
# RECONCILIATION SCHEMAS
# ============================================================================

class ReconciliationRuleCreate(BaseSchema):
    """Création d'une règle de rapprochement."""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    match_criteria: Dict[str, Any]
    auto_reconcile: bool = False
    min_confidence: Decimal = Decimal("90")
    default_account_code: Optional[str] = None
    default_tax_code: Optional[str] = None
    priority: int = 0


class ReconciliationRuleUpdate(BaseSchema):
    """Mise à jour d'une règle de rapprochement."""
    name: Optional[str] = None
    description: Optional[str] = None
    match_criteria: Optional[Dict[str, Any]] = None
    auto_reconcile: Optional[bool] = None
    min_confidence: Optional[Decimal] = None
    is_active: Optional[bool] = None


class ReconciliationRuleResponse(BaseSchema):
    """Réponse règle de rapprochement."""
    id: UUID
    name: str
    description: Optional[str] = None
    match_criteria: Dict[str, Any]
    auto_reconcile: bool
    min_confidence: Decimal
    default_account_code: Optional[str] = None
    priority: int
    is_active: bool
    times_matched: int
    last_matched_at: Optional[datetime] = None
    created_at: datetime


class ManualReconciliation(BaseSchema):
    """Rapprochement manuel."""
    transaction_id: UUID
    document_id: Optional[UUID] = None
    entry_line_id: Optional[UUID] = None


class ReconciliationHistoryResponse(BaseSchema):
    """Réponse historique rapprochement."""
    id: UUID
    transaction_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    reconciliation_type: str
    confidence_score: Optional[Decimal] = None
    transaction_amount: Optional[Decimal] = None
    document_amount: Optional[Decimal] = None
    difference: Optional[Decimal] = None
    is_cancelled: bool = False
    created_at: datetime


# ============================================================================
# ALERT SCHEMAS
# ============================================================================

class AlertCreate(BaseSchema):
    """Création d'une alerte."""
    alert_type: AlertTypeEnum
    severity: AlertSeverityEnum = AlertSeverityEnum.WARNING
    title: str = Field(..., min_length=5, max_length=255)
    message: str = Field(..., min_length=10)
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    target_roles: List[str] = Field(default_factory=lambda: ["EXPERT_COMPTABLE"])
    expires_at: Optional[datetime] = None


class AlertResponse(BaseSchema):
    """Réponse alerte."""
    id: UUID
    alert_type: AlertTypeEnum
    severity: AlertSeverityEnum
    title: str
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    is_read: bool = False
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime


class AlertResolve(BaseSchema):
    """Résolution d'une alerte."""
    resolution_notes: Optional[str] = None


class AlertListResponse(BaseSchema):
    """Liste d'alertes."""
    items: List[AlertResponse]
    total: int
    unread_count: int
    critical_count: int


# ============================================================================
# DASHBOARD SCHEMAS (VUE DIRIGEANT)
# ============================================================================

class CashPositionResponse(BaseSchema):
    """Position de trésorerie actuelle."""
    total_balance: Decimal
    available_balance: Decimal
    currency: str = "EUR"
    accounts: List[Dict[str, Any]]
    last_sync_at: Optional[datetime] = None
    freshness_score: Decimal  # 0-100


class CashForecastItem(BaseSchema):
    """Élément de prévision de trésorerie."""
    date: date
    opening_balance: Decimal
    expected_receipts: Decimal
    expected_payments: Decimal
    expected_closing: Decimal


class CashForecastResponse(BaseSchema):
    """Prévision de trésorerie."""
    current_balance: Decimal
    forecast_items: List[CashForecastItem]
    period_start: date
    period_end: date
    warning_threshold: Optional[Decimal] = None
    alert_threshold: Optional[Decimal] = None


class InvoicesSummary(BaseSchema):
    """Résumé des factures."""
    # À payer
    to_pay_count: int
    to_pay_amount: Decimal
    overdue_to_pay_count: int
    overdue_to_pay_amount: Decimal

    # À encaisser
    to_collect_count: int
    to_collect_amount: Decimal
    overdue_to_collect_count: int
    overdue_to_collect_amount: Decimal


class ResultSummary(BaseSchema):
    """Résultat estimé."""
    revenue: Decimal
    expenses: Decimal
    result: Decimal
    period: str  # "MONTH", "QUARTER", "YEAR"
    period_start: date
    period_end: date


class DirigeantDashboard(BaseSchema):
    """Dashboard complet vue Dirigeant."""
    cash_position: CashPositionResponse
    cash_forecast: CashForecastResponse
    invoices_summary: InvoicesSummary
    result_summary: ResultSummary
    alerts: List[AlertResponse]  # Alertes critiques uniquement
    data_freshness: Decimal  # Score global 0-100
    last_updated: datetime


# ============================================================================
# DASHBOARD SCHEMAS (VUE ASSISTANTE)
# ============================================================================

class DocumentCountsByStatus(BaseSchema):
    """Comptage documents par statut."""
    received: int = 0
    processing: int = 0
    analyzed: int = 0
    pending_validation: int = 0
    validated: int = 0
    accounted: int = 0
    rejected: int = 0
    error: int = 0


class DocumentCountsByType(BaseSchema):
    """Comptage documents par type."""
    invoice_received: int = 0
    invoice_sent: int = 0
    expense_note: int = 0
    credit_note_received: int = 0
    credit_note_sent: int = 0
    quote: int = 0
    purchase_order: int = 0
    other: int = 0


class AssistanteDashboard(BaseSchema):
    """Dashboard vue Assistante."""
    total_documents: int
    documents_by_status: DocumentCountsByStatus
    documents_by_type: DocumentCountsByType
    recent_documents: List[DocumentResponse]
    alerts: List[AlertResponse]  # Alertes "pièce illisible", "info manquante"
    last_updated: datetime


# ============================================================================
# DASHBOARD SCHEMAS (VUE EXPERT-COMPTABLE)
# ============================================================================

class ValidationQueueItem(BaseSchema):
    """Élément de la file de validation."""
    document: DocumentResponse
    ai_classification: Optional[AIClassificationResponse] = None
    auto_entry: Optional[AutoEntryResponse] = None
    alerts: List[AlertResponse] = Field(default_factory=list)


class ValidationQueueResponse(BaseSchema):
    """File de validation expert-comptable."""
    items: List[ValidationQueueItem]
    total: int
    high_priority_count: int  # Confiance faible
    medium_priority_count: int
    low_priority_count: int


class AIPerformanceStats(BaseSchema):
    """Statistiques de performance IA."""
    total_processed: int
    auto_validated_count: int
    auto_validated_rate: Decimal  # %
    corrections_count: int
    corrections_rate: Decimal  # %
    average_confidence: Decimal
    by_document_type: Dict[str, Dict[str, Any]]


class ReconciliationStats(BaseSchema):
    """Statistiques de rapprochement."""
    total_transactions: int
    matched_auto: int
    matched_manual: int
    unmatched: int
    match_rate: Decimal  # %


class ExpertComptableDashboard(BaseSchema):
    """Dashboard vue Expert-comptable."""
    validation_queue: ValidationQueueResponse
    ai_performance: AIPerformanceStats
    reconciliation_stats: ReconciliationStats
    unresolved_alerts: List[AlertResponse]
    periods_status: List[Dict[str, Any]]  # Statut des périodes comptables
    last_updated: datetime


# ============================================================================
# USER PREFERENCES SCHEMAS
# ============================================================================

class WidgetConfig(BaseSchema):
    """Configuration d'un widget."""
    widget_id: str
    position: int
    enabled: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)


class UserPreferencesCreate(BaseSchema):
    """Création préférences utilisateur."""
    view_type: ViewTypeEnum
    dashboard_widgets: List[WidgetConfig] = Field(default_factory=list)
    default_period: str = "MONTH"
    list_columns: List[str] = Field(default_factory=list)
    default_filters: Dict[str, Any] = Field(default_factory=dict)
    alert_preferences: Dict[str, bool] = Field(default_factory=dict)


class UserPreferencesUpdate(BaseSchema):
    """Mise à jour préférences."""
    dashboard_widgets: Optional[List[WidgetConfig]] = None
    default_period: Optional[str] = None
    list_columns: Optional[List[str]] = None
    default_filters: Optional[Dict[str, Any]] = None
    alert_preferences: Optional[Dict[str, bool]] = None


class UserPreferencesResponse(BaseSchema):
    """Réponse préférences utilisateur."""
    id: UUID
    user_id: UUID
    view_type: ViewTypeEnum
    dashboard_widgets: List[WidgetConfig]
    default_period: str
    list_columns: List[str]
    default_filters: Dict[str, Any]
    alert_preferences: Dict[str, bool]
    last_accessed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# EMAIL INBOX SCHEMAS
# ============================================================================

class EmailInboxCreate(BaseSchema):
    """Création boîte email."""
    email_address: str
    email_type: EmailInboxTypeEnum
    auto_process: bool = True
    provider: Optional[str] = None
    provider_config: Optional[Dict[str, Any]] = None


class EmailInboxResponse(BaseSchema):
    """Réponse boîte email."""
    id: UUID
    email_address: str
    email_type: EmailInboxTypeEnum
    is_active: bool
    auto_process: bool
    emails_received: int
    emails_processed: int
    last_email_at: Optional[datetime] = None
    created_at: datetime


class EmailProcessingLogResponse(BaseSchema):
    """Réponse log traitement email."""
    id: UUID
    inbox_id: UUID
    email_id: str
    email_from: Optional[str] = None
    email_subject: Optional[str] = None
    email_received_at: Optional[datetime] = None
    status: str
    attachments_count: int
    attachments_processed: int
    documents_created: List[UUID]
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime


# ============================================================================
# UNIVERSAL CHART SCHEMAS
# ============================================================================

class UniversalChartAccountResponse(BaseSchema):
    """Réponse compte plan universel."""
    id: UUID
    universal_code: str
    name_en: str
    name_fr: str
    account_type: str
    parent_code: Optional[str] = None
    level: int
    country_mappings: Dict[str, str]
    is_active: bool


class ChartMappingCreate(BaseSchema):
    """Création mapping plan comptable."""
    universal_code: str
    local_account_code: str
    priority: int = 0
    conditions: Dict[str, Any] = Field(default_factory=dict)


class ChartMappingResponse(BaseSchema):
    """Réponse mapping."""
    id: UUID
    universal_code: str
    local_account_id: Optional[UUID] = None
    local_account_code: Optional[str] = None
    priority: int
    is_active: bool
    created_at: datetime


# ============================================================================
# TAX CONFIGURATION SCHEMAS
# ============================================================================

class TaxRate(BaseSchema):
    """Taux de taxe."""
    name: str
    rate: Decimal
    account_code: str
    is_default: bool = False


class TaxConfigurationResponse(BaseSchema):
    """Réponse configuration fiscale."""
    id: UUID
    country_code: str
    country_name: str
    tax_type: str
    tax_rates: List[TaxRate]
    is_active: bool
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None


# ============================================================================
# REPORTING SCHEMAS
# ============================================================================

class ReportRequest(BaseSchema):
    """Demande de rapport."""
    report_type: str  # balance, trial_balance, income_statement, balance_sheet
    start_date: date
    end_date: date
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ReportResponse(BaseSchema):
    """Réponse rapport."""
    report_type: str
    name: str
    start_date: date
    end_date: date
    data: Dict[str, Any]
    generated_at: datetime
    generated_by: Optional[UUID] = None


# ============================================================================
# EXPORT SCHEMAS (UNIQUEMENT SI OBLIGATION LÉGALE)
# ============================================================================

class ExportRequest(BaseSchema):
    """Demande d'export (uniquement si obligation légale)."""
    export_type: str  # FEC, AUDIT_TRAIL, etc.
    start_date: date
    end_date: date
    format: str = "CSV"  # CSV, XML, JSON
    legal_requirement: str = Field(..., min_length=10)  # Justification obligatoire


class ExportResponse(BaseSchema):
    """Réponse export."""
    id: UUID
    export_type: str
    status: str
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    legal_requirement: str
    generated_at: datetime
    expires_at: datetime  # Exports auto-supprimés


# ============================================================================
# BULK OPERATIONS SCHEMAS
# ============================================================================

class BulkValidationRequest(BaseSchema):
    """Validation en masse de documents."""
    document_ids: List[UUID] = Field(..., min_length=1, max_length=100)
    validation_notes: Optional[str] = None


class BulkValidationResponse(BaseSchema):
    """Réponse validation en masse."""
    validated_count: int
    failed_count: int
    failed_ids: List[UUID]
    errors: Dict[str, str]  # {document_id: error_message}


# Mise à jour des forward references
DocumentDetailResponse.model_rebuild()
