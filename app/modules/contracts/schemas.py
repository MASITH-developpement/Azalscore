"""
AZALS MODULE CONTRACTS - Schemas Pydantic
==========================================

Schemas de validation pour le module de gestion des contrats.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# ============================================================================
# ENUMS (repris des models pour schemas)
# ============================================================================

class ContractTypeEnum(str, Enum):
    SALES = "sales"
    PURCHASE = "purchase"
    SERVICE = "service"
    SUBSCRIPTION = "subscription"
    LICENSE = "license"
    DISTRIBUTION = "distribution"
    FRANCHISE = "franchise"
    AGENCY = "agency"
    RESELLER = "reseller"
    PARTNERSHIP = "partnership"
    JOINT_VENTURE = "joint_venture"
    CONSORTIUM = "consortium"
    AFFILIATE = "affiliate"
    NDA = "nda"
    NON_COMPETE = "non_compete"
    NON_SOLICITATION = "non_solicitation"
    LEASE = "lease"
    SUBLEASE = "sublease"
    REAL_ESTATE = "real_estate"
    EMPLOYMENT = "employment"
    CONSULTING = "consulting"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"
    MAINTENANCE = "maintenance"
    SLA = "sla"
    SUPPORT = "support"
    WARRANTY = "warranty"
    RENTAL = "rental"
    LEASING = "leasing"
    FRAMEWORK = "framework"
    MASTER = "master"
    OTHER = "other"


class ContractStatusEnum(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    IN_NEGOTIATION = "in_negotiation"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PENDING_SIGNATURE = "pending_signature"
    PARTIALLY_SIGNED = "partially_signed"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ON_HOLD = "on_hold"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    RENEWED = "renewed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class PartyRoleEnum(str, Enum):
    CONTRACTOR = "contractor"
    CLIENT = "client"
    SUPPLIER = "supplier"
    PARTNER = "partner"
    EMPLOYER = "employer"
    EMPLOYEE = "employee"
    LICENSOR = "licensor"
    LICENSEE = "licensee"
    LANDLORD = "landlord"
    TENANT = "tenant"
    GUARANTOR = "guarantor"
    BENEFICIARY = "beneficiary"
    AGENT = "agent"
    PRINCIPAL = "principal"


class PartyTypeEnum(str, Enum):
    COMPANY = "company"
    INDIVIDUAL = "individual"
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"


class RenewalTypeEnum(str, Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    NEGOTIATED = "negotiated"
    EVERGREEN = "evergreen"
    NONE = "none"


class BillingFrequencyEnum(str, Enum):
    ONE_TIME = "one_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    BIMONTHLY = "bimonthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    CUSTOM = "custom"


class AmendmentTypeEnum(str, Enum):
    EXTENSION = "extension"
    MODIFICATION = "modification"
    PRICING = "pricing"
    SCOPE = "scope"
    PARTIES = "parties"
    TERMINATION = "termination"
    RENEWAL = "renewal"
    ADDENDUM = "addendum"
    ASSIGNMENT = "assignment"
    OTHER = "other"


class ObligationTypeEnum(str, Enum):
    PAYMENT = "payment"
    DELIVERY = "delivery"
    PERFORMANCE = "performance"
    REPORTING = "reporting"
    COMPLIANCE = "compliance"
    AUDIT = "audit"
    RENEWAL_NOTICE = "renewal_notice"
    TERMINATION_NOTICE = "termination_notice"
    CONFIDENTIALITY = "confidentiality"
    INSURANCE = "insurance"
    WARRANTY = "warranty"
    MILESTONE = "milestone"
    REVIEW = "review"
    OTHER = "other"


class ObligationStatusEnum(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    WAIVED = "waived"
    CANCELLED = "cancelled"


class AlertTypeEnum(str, Enum):
    EXPIRY = "expiry"
    RENEWAL_NOTICE = "renewal_notice"
    OBLIGATION_DUE = "obligation_due"
    MILESTONE_DUE = "milestone_due"
    PAYMENT_DUE = "payment_due"
    REVIEW_REQUIRED = "review_required"
    PRICE_REVISION = "price_revision"
    COMPLIANCE_CHECK = "compliance_check"
    SIGNATURE_PENDING = "signature_pending"
    CUSTOM = "custom"


class AlertPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DELEGATED = "delegated"
    ESCALATED = "escalated"


class ClauseTypeEnum(str, Enum):
    STANDARD = "standard"
    LEGAL = "legal"
    CUSTOM = "custom"
    OPTIONAL = "optional"
    NEGOTIATED = "negotiated"


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class BaseSchema(BaseModel):
    """Schema de base avec configuration commune."""
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class TimestampMixin(BaseModel):
    """Mixin pour les timestamps d'audit."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AuditMixin(TimestampMixin):
    """Mixin complet pour l'audit."""
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    version: int = 1


# ============================================================================
# CONTRACT CATEGORY SCHEMAS
# ============================================================================

class ContractCategoryBase(BaseSchema):
    """Base pour categorie de contrat."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    color: Optional[str] = "#3B82F6"
    icon: Optional[str] = None
    sort_order: int = 0
    default_contract_type: Optional[ContractTypeEnum] = None
    default_duration_months: Optional[int] = None
    default_renewal_type: Optional[RenewalTypeEnum] = None
    default_billing_frequency: Optional[BillingFrequencyEnum] = None
    approval_required: bool = True
    min_approval_amount: Optional[Decimal] = Decimal("0")
    is_active: bool = True


class ContractCategoryCreate(ContractCategoryBase):
    """Creation de categorie."""
    pass


class ContractCategoryUpdate(BaseSchema):
    """Mise a jour de categorie."""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    default_contract_type: Optional[ContractTypeEnum] = None
    default_duration_months: Optional[int] = None
    default_renewal_type: Optional[RenewalTypeEnum] = None
    default_billing_frequency: Optional[BillingFrequencyEnum] = None
    approval_required: Optional[bool] = None
    min_approval_amount: Optional[Decimal] = None
    is_active: Optional[bool] = None


class ContractCategoryResponse(ContractCategoryBase, AuditMixin):
    """Reponse categorie."""
    id: UUID


# ============================================================================
# CONTRACT TEMPLATE SCHEMAS
# ============================================================================

class ContractTemplateBase(BaseSchema):
    """Base pour template de contrat."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    contract_type: ContractTypeEnum
    category_id: Optional[UUID] = None
    content: Optional[str] = None
    header_content: Optional[str] = None
    footer_content: Optional[str] = None
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    variables: List[Dict[str, Any]] = Field(default_factory=list)
    language: str = "fr"
    default_duration_months: Optional[int] = None
    default_renewal_type: Optional[RenewalTypeEnum] = None
    default_payment_terms_days: int = 30
    default_clauses: List[UUID] = Field(default_factory=list)
    requires_signature: bool = True
    requires_witness: bool = False
    requires_notarization: bool = False
    tags: List[str] = Field(default_factory=list)
    version_number: str = "1.0"
    is_active: bool = True
    is_default: bool = False


class ContractTemplateCreate(ContractTemplateBase):
    """Creation de template."""
    pass


class ContractTemplateUpdate(BaseSchema):
    """Mise a jour de template."""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    contract_type: Optional[ContractTypeEnum] = None
    category_id: Optional[UUID] = None
    content: Optional[str] = None
    header_content: Optional[str] = None
    footer_content: Optional[str] = None
    sections: Optional[List[Dict[str, Any]]] = None
    variables: Optional[List[Dict[str, Any]]] = None
    language: Optional[str] = None
    default_duration_months: Optional[int] = None
    default_renewal_type: Optional[RenewalTypeEnum] = None
    default_payment_terms_days: Optional[int] = None
    default_clauses: Optional[List[UUID]] = None
    requires_signature: Optional[bool] = None
    requires_witness: Optional[bool] = None
    requires_notarization: Optional[bool] = None
    tags: Optional[List[str]] = None
    version_number: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class ContractTemplateResponse(ContractTemplateBase, AuditMixin):
    """Reponse template."""
    id: UUID


# ============================================================================
# CLAUSE TEMPLATE SCHEMAS
# ============================================================================

class ClauseTemplateBase(BaseSchema):
    """Base pour template de clause."""
    code: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    content: str
    clause_type: ClauseTypeEnum = ClauseTypeEnum.STANDARD
    section: Optional[str] = None
    contract_template_id: Optional[UUID] = None
    is_mandatory: bool = False
    is_negotiable: bool = True
    risk_level: str = "low"
    sort_order: int = 0
    variables: List[Dict[str, Any]] = Field(default_factory=list)
    compliance_tags: List[str] = Field(default_factory=list)
    jurisdiction: Optional[str] = None
    language: str = "fr"
    is_active: bool = True


class ClauseTemplateCreate(ClauseTemplateBase):
    """Creation de clause template."""
    pass


class ClauseTemplateUpdate(BaseSchema):
    """Mise a jour de clause template."""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    clause_type: Optional[ClauseTypeEnum] = None
    section: Optional[str] = None
    is_mandatory: Optional[bool] = None
    is_negotiable: Optional[bool] = None
    risk_level: Optional[str] = None
    sort_order: Optional[int] = None
    variables: Optional[List[Dict[str, Any]]] = None
    compliance_tags: Optional[List[str]] = None
    jurisdiction: Optional[str] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None


class ClauseTemplateResponse(ClauseTemplateBase, AuditMixin):
    """Reponse clause template."""
    id: UUID


# ============================================================================
# CONTRACT PARTY SCHEMAS
# ============================================================================

class ContractPartyBase(BaseSchema):
    """Base pour partie contractante."""
    party_type: PartyTypeEnum = PartyTypeEnum.COMPANY
    role: PartyRoleEnum
    name: str = Field(..., min_length=1, max_length=255)
    legal_name: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    registration_number: Optional[str] = None
    vat_number: Optional[str] = None
    legal_form: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    state: Optional[str] = None
    country_code: str = "FR"
    representative_name: Optional[str] = None
    representative_title: Optional[str] = None
    representative_email: Optional[str] = None
    representative_phone: Optional[str] = None
    is_signatory: bool = True
    signatory_name: Optional[str] = None
    signatory_title: Optional[str] = None
    signatory_email: Optional[str] = None
    sort_order: int = 0
    is_primary: bool = False
    notes: Optional[str] = None


class ContractPartyCreate(ContractPartyBase):
    """Creation de partie."""
    pass


class ContractPartyUpdate(BaseSchema):
    """Mise a jour de partie."""
    party_type: Optional[PartyTypeEnum] = None
    role: Optional[PartyRoleEnum] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    legal_name: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    registration_number: Optional[str] = None
    vat_number: Optional[str] = None
    legal_form: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    state: Optional[str] = None
    country_code: Optional[str] = None
    representative_name: Optional[str] = None
    representative_title: Optional[str] = None
    representative_email: Optional[str] = None
    representative_phone: Optional[str] = None
    is_signatory: Optional[bool] = None
    signatory_name: Optional[str] = None
    signatory_title: Optional[str] = None
    signatory_email: Optional[str] = None
    sort_order: Optional[int] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None


class ContractPartyResponse(ContractPartyBase):
    """Reponse partie."""
    id: UUID
    contract_id: UUID
    has_signed: bool = False
    signed_at: Optional[datetime] = None
    signature_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================================
# CONTRACT LINE SCHEMAS
# ============================================================================

class ContractLineBase(BaseSchema):
    """Base pour ligne de contrat."""
    line_number: int
    reference: Optional[str] = None
    description: str
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    is_service: bool = True
    quantity: Decimal = Decimal("1")
    unit: Optional[str] = None
    unit_price: Decimal = Decimal("0")
    currency: str = "EUR"
    discount_percent: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("20.00")
    is_recurring: bool = False
    billing_frequency: Optional[BillingFrequencyEnum] = None
    billing_start_date: Optional[date] = None
    billing_end_date: Optional[date] = None
    billing_day: Optional[int] = None
    price_revision_enabled: bool = False
    price_revision_index: Optional[str] = None
    delivery_date: Optional[date] = None
    delivery_address: Optional[str] = None
    sla_id: Optional[UUID] = None
    response_time_hours: Optional[int] = None
    resolution_time_hours: Optional[int] = None
    accounting_code: Optional[str] = None
    cost_center: Optional[str] = None
    analytic_axis: Optional[Dict[str, Any]] = None
    status: str = "active"
    is_active: bool = True
    sort_order: int = 0
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


class ContractLineCreate(ContractLineBase):
    """Creation de ligne."""
    pass


class ContractLineUpdate(BaseSchema):
    """Mise a jour de ligne."""
    line_number: Optional[int] = None
    reference: Optional[str] = None
    description: Optional[str] = None
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    is_service: Optional[bool] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    currency: Optional[str] = None
    discount_percent: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    is_recurring: Optional[bool] = None
    billing_frequency: Optional[BillingFrequencyEnum] = None
    billing_start_date: Optional[date] = None
    billing_end_date: Optional[date] = None
    billing_day: Optional[int] = None
    price_revision_enabled: Optional[bool] = None
    price_revision_index: Optional[str] = None
    delivery_date: Optional[date] = None
    delivery_address: Optional[str] = None
    sla_id: Optional[UUID] = None
    response_time_hours: Optional[int] = None
    resolution_time_hours: Optional[int] = None
    accounting_code: Optional[str] = None
    cost_center: Optional[str] = None
    analytic_axis: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


class ContractLineResponse(ContractLineBase, AuditMixin):
    """Reponse ligne."""
    id: UUID
    contract_id: UUID
    subtotal: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    delivered_quantity: Decimal = Decimal("0")
    next_billing_date: Optional[date] = None
    last_billed_date: Optional[date] = None
    original_price: Optional[Decimal] = None
    last_revision_date: Optional[date] = None


# ============================================================================
# CONTRACT CLAUSE SCHEMAS
# ============================================================================

class ContractClauseBase(BaseSchema):
    """Base pour clause de contrat."""
    title: str = Field(..., min_length=1, max_length=255)
    content: str
    clause_type: ClauseTypeEnum = ClauseTypeEnum.STANDARD
    section: Optional[str] = None
    template_id: Optional[UUID] = None
    is_from_template: bool = False
    is_negotiable: bool = True
    negotiation_status: str = "accepted"
    negotiation_notes: Optional[str] = None
    is_mandatory: bool = False
    risk_level: str = "low"
    compliance_tags: List[str] = Field(default_factory=list)
    requires_legal_review: bool = False
    sort_order: int = 0
    is_active: bool = True


class ContractClauseCreate(ContractClauseBase):
    """Creation de clause."""
    pass


class ContractClauseUpdate(BaseSchema):
    """Mise a jour de clause."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    clause_type: Optional[ClauseTypeEnum] = None
    section: Optional[str] = None
    is_negotiable: Optional[bool] = None
    negotiation_status: Optional[str] = None
    negotiation_notes: Optional[str] = None
    is_mandatory: Optional[bool] = None
    risk_level: Optional[str] = None
    compliance_tags: Optional[List[str]] = None
    requires_legal_review: Optional[bool] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ContractClauseResponse(ContractClauseBase, AuditMixin):
    """Reponse clause."""
    id: UUID
    contract_id: UUID
    original_content: Optional[str] = None
    modification_history: List[Dict[str, Any]] = Field(default_factory=list)
    modified_by_party_id: Optional[UUID] = None
    legal_reviewed: bool = False
    legal_reviewer_id: Optional[UUID] = None
    legal_review_date: Optional[datetime] = None
    legal_review_notes: Optional[str] = None


# ============================================================================
# CONTRACT OBLIGATION SCHEMAS
# ============================================================================

class ContractObligationBase(BaseSchema):
    """Base pour obligation contractuelle."""
    code: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    obligation_type: ObligationTypeEnum
    responsible_party_id: Optional[UUID] = None
    responsible_user_id: Optional[UUID] = None
    responsible_name: Optional[str] = None
    due_date: Optional[date] = None
    reminder_date: Optional[date] = None
    grace_period_days: int = 0
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    recurrence_interval: int = 1
    recurrence_end_date: Optional[date] = None
    amount: Optional[Decimal] = None
    currency: str = "EUR"
    alert_days_before: int = 30
    evidence_required: bool = False
    penalty_on_breach: Optional[Decimal] = None
    priority: str = "medium"
    is_critical: bool = False
    notes: Optional[str] = None


class ContractObligationCreate(ContractObligationBase):
    """Creation d'obligation."""
    pass


class ContractObligationUpdate(BaseSchema):
    """Mise a jour d'obligation."""
    code: Optional[str] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    obligation_type: Optional[ObligationTypeEnum] = None
    responsible_party_id: Optional[UUID] = None
    responsible_user_id: Optional[UUID] = None
    responsible_name: Optional[str] = None
    due_date: Optional[date] = None
    reminder_date: Optional[date] = None
    grace_period_days: Optional[int] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    recurrence_interval: Optional[int] = None
    recurrence_end_date: Optional[date] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    alert_days_before: Optional[int] = None
    evidence_required: Optional[bool] = None
    penalty_on_breach: Optional[Decimal] = None
    priority: Optional[str] = None
    is_critical: Optional[bool] = None
    notes: Optional[str] = None


class ContractObligationResponse(ContractObligationBase, AuditMixin):
    """Reponse obligation."""
    id: UUID
    contract_id: UUID
    status: ObligationStatusEnum = ObligationStatusEnum.PENDING
    next_due_date: Optional[date] = None
    last_completed_date: Optional[date] = None
    occurrences_completed: int = 0
    completed_at: Optional[datetime] = None
    completed_by: Optional[UUID] = None
    completion_notes: Optional[str] = None
    alert_sent: bool = False
    alert_sent_at: Optional[datetime] = None
    evidence_document_id: Optional[UUID] = None


class ObligationCompleteRequest(BaseSchema):
    """Requete pour completer une obligation."""
    completion_notes: Optional[str] = None
    evidence_document_id: Optional[UUID] = None


# ============================================================================
# CONTRACT MILESTONE SCHEMAS
# ============================================================================

class ContractMilestoneBase(BaseSchema):
    """Base pour jalon contractuel."""
    code: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_date: date
    due_date_tolerance_days: int = 0
    deliverables: List[Dict[str, Any]] = Field(default_factory=list)
    acceptance_criteria: Optional[str] = None
    payment_amount: Optional[Decimal] = None
    payment_percentage: Optional[Decimal] = None
    payment_currency: str = "EUR"
    requires_approval: bool = True
    responsible_user_id: Optional[UUID] = None
    responsible_name: Optional[str] = None
    depends_on_milestone_id: Optional[UUID] = None
    alert_days_before: int = 14
    sort_order: int = 0
    notes: Optional[str] = None


class ContractMilestoneCreate(ContractMilestoneBase):
    """Creation de jalon."""
    pass


class ContractMilestoneUpdate(BaseSchema):
    """Mise a jour de jalon."""
    code: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_date: Optional[date] = None
    due_date_tolerance_days: Optional[int] = None
    deliverables: Optional[List[Dict[str, Any]]] = None
    acceptance_criteria: Optional[str] = None
    payment_amount: Optional[Decimal] = None
    payment_percentage: Optional[Decimal] = None
    payment_currency: Optional[str] = None
    requires_approval: Optional[bool] = None
    responsible_user_id: Optional[UUID] = None
    responsible_name: Optional[str] = None
    depends_on_milestone_id: Optional[UUID] = None
    alert_days_before: Optional[int] = None
    sort_order: Optional[int] = None
    notes: Optional[str] = None


class ContractMilestoneResponse(ContractMilestoneBase, AuditMixin):
    """Reponse jalon."""
    id: UUID
    contract_id: UUID
    actual_date: Optional[date] = None
    status: str = "pending"
    progress_percentage: int = 0
    completed_at: Optional[datetime] = None
    completed_by: Optional[UUID] = None
    payment_triggered: bool = False
    invoice_id: Optional[UUID] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None


class MilestoneCompleteRequest(BaseSchema):
    """Requete pour completer un jalon."""
    actual_date: Optional[date] = None
    notes: Optional[str] = None
    trigger_payment: bool = False


# ============================================================================
# CONTRACT AMENDMENT SCHEMAS
# ============================================================================

class ContractAmendmentBase(BaseSchema):
    """Base pour avenant."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    amendment_type: AmendmentTypeEnum
    reason: Optional[str] = None
    justification: Optional[str] = None
    effective_date: date
    expiry_date: Optional[date] = None
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    content: Optional[str] = None
    value_change: Optional[Decimal] = None
    new_total_value: Optional[Decimal] = None
    currency: str = "EUR"
    new_end_date: Optional[date] = None
    new_duration_months: Optional[int] = None
    requires_approval: bool = True
    requires_signature: bool = True
    notes: Optional[str] = None


class ContractAmendmentCreate(ContractAmendmentBase):
    """Creation d'avenant."""
    pass


class ContractAmendmentUpdate(BaseSchema):
    """Mise a jour d'avenant."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    amendment_type: Optional[AmendmentTypeEnum] = None
    reason: Optional[str] = None
    justification: Optional[str] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    changes: Optional[List[Dict[str, Any]]] = None
    content: Optional[str] = None
    value_change: Optional[Decimal] = None
    new_total_value: Optional[Decimal] = None
    currency: Optional[str] = None
    new_end_date: Optional[date] = None
    new_duration_months: Optional[int] = None
    requires_approval: Optional[bool] = None
    requires_signature: Optional[bool] = None
    notes: Optional[str] = None


class ContractAmendmentResponse(ContractAmendmentBase, AuditMixin):
    """Reponse avenant."""
    id: UUID
    contract_id: UUID
    amendment_number: int
    amendment_code: Optional[str] = None
    status: ContractStatusEnum = ContractStatusEnum.DRAFT
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    all_parties_signed: bool = False
    signed_at: Optional[datetime] = None
    document_id: Optional[UUID] = None
    signed_document_id: Optional[UUID] = None
    signing_parties: List[Dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# CONTRACT DOCUMENT SCHEMAS
# ============================================================================

class ContractDocumentBase(BaseSchema):
    """Base pour document contrat."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    document_type: str = "contract"
    is_confidential: bool = False
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    is_public: bool = False
    notes: Optional[str] = None


class ContractDocumentCreate(ContractDocumentBase):
    """Creation de document."""
    file_path: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    amendment_id: Optional[UUID] = None


class ContractDocumentUpdate(BaseSchema):
    """Mise a jour de document."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    document_type: Optional[str] = None
    is_confidential: Optional[bool] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    notes: Optional[str] = None


class ContractDocumentResponse(ContractDocumentBase):
    """Reponse document."""
    id: UUID
    contract_id: UUID
    amendment_id: Optional[UUID] = None
    file_path: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    checksum: Optional[str] = None
    version_number: int = 1
    is_latest_version: bool = True
    previous_version_id: Optional[UUID] = None
    is_signed: bool = False
    signature_request_id: Optional[str] = None
    signed_at: Optional[datetime] = None
    signed_document_path: Optional[str] = None
    status: str = "draft"
    access_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    created_by: Optional[UUID] = None


# ============================================================================
# CONTRACT ALERT SCHEMAS
# ============================================================================

class ContractAlertBase(BaseSchema):
    """Base pour alerte contrat."""
    alert_type: AlertTypeEnum
    priority: AlertPriorityEnum = AlertPriorityEnum.MEDIUM
    title: str = Field(..., min_length=1, max_length=255)
    message: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    due_date: date
    trigger_date: Optional[date] = None
    recipients: List[Dict[str, Any]] = Field(default_factory=list)
    notify_owner: bool = True
    notify_parties: bool = False
    send_channels: List[str] = Field(default_factory=lambda: ["email", "in_app"])
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    action_required: bool = True
    auto_dismiss_days: Optional[int] = None
    notes: Optional[str] = None


class ContractAlertCreate(ContractAlertBase):
    """Creation d'alerte."""
    pass


class ContractAlertUpdate(BaseSchema):
    """Mise a jour d'alerte."""
    alert_type: Optional[AlertTypeEnum] = None
    priority: Optional[AlertPriorityEnum] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    message: Optional[str] = None
    due_date: Optional[date] = None
    trigger_date: Optional[date] = None
    recipients: Optional[List[Dict[str, Any]]] = None
    notify_owner: Optional[bool] = None
    notify_parties: Optional[bool] = None
    send_channels: Optional[List[str]] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    action_required: Optional[bool] = None
    auto_dismiss_days: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ContractAlertResponse(ContractAlertBase):
    """Reponse alerte."""
    id: UUID
    contract_id: UUID
    is_sent: bool = False
    sent_at: Optional[datetime] = None
    notification_count: int = 0
    last_notification_at: Optional[datetime] = None
    next_alert_date: Optional[date] = None
    is_acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[UUID] = None
    acknowledgement_notes: Optional[str] = None
    action_taken: Optional[str] = None
    action_date: Optional[datetime] = None
    status: str = "pending"
    is_active: bool = True
    created_at: Optional[datetime] = None


class AlertAcknowledgeRequest(BaseSchema):
    """Requete pour acquitter une alerte."""
    notes: Optional[str] = None
    action_taken: Optional[str] = None


# ============================================================================
# CONTRACT APPROVAL SCHEMAS
# ============================================================================

class ContractApprovalBase(BaseSchema):
    """Base pour approbation."""
    level: int
    level_name: Optional[str] = None
    approver_id: UUID
    approver_name: Optional[str] = None
    approver_email: Optional[str] = None
    approver_role: Optional[str] = None
    due_date: Optional[datetime] = None


class ContractApprovalCreate(ContractApprovalBase):
    """Creation d'approbation."""
    amendment_id: Optional[UUID] = None


class ContractApprovalResponse(ContractApprovalBase):
    """Reponse approbation."""
    id: UUID
    contract_id: UUID
    amendment_id: Optional[UUID] = None
    delegated_from_id: Optional[UUID] = None
    delegation_reason: Optional[str] = None
    status: ApprovalStatusEnum = ApprovalStatusEnum.PENDING
    decision: Optional[str] = None
    decision_date: Optional[datetime] = None
    comments: Optional[str] = None
    rejection_reason: Optional[str] = None
    approved_with_conditions: bool = False
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    reminder_sent: bool = False
    reminder_count: int = 0
    escalated: bool = False
    escalated_to_id: Optional[UUID] = None
    escalation_reason: Optional[str] = None
    escalation_date: Optional[datetime] = None
    notification_sent: bool = False
    notification_sent_at: Optional[datetime] = None
    sort_order: int = 0
    created_at: Optional[datetime] = None


class ApprovalDecisionRequest(BaseSchema):
    """Requete pour decision d'approbation."""
    decision: str = Field(..., pattern="^(approved|rejected)$")
    comments: Optional[str] = None
    rejection_reason: Optional[str] = None
    conditions: Optional[List[Dict[str, Any]]] = None


class ApprovalDelegateRequest(BaseSchema):
    """Requete pour deleguer une approbation."""
    delegate_to_id: UUID
    reason: Optional[str] = None


# ============================================================================
# CONTRACT MAIN SCHEMAS
# ============================================================================

class ContractBase(BaseSchema):
    """Base pour contrat."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    reference: Optional[str] = None
    contract_type: ContractTypeEnum = ContractTypeEnum.SERVICE
    category_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    parent_contract_id: Optional[UUID] = None
    master_contract_id: Optional[UUID] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    special_conditions: Optional[str] = None
    effective_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_months: Optional[int] = None
    duration_days: Optional[int] = None
    is_indefinite: bool = False
    renewal_type: RenewalTypeEnum = RenewalTypeEnum.MANUAL
    renewal_notice_days: int = 90
    auto_renewal_term_months: int = 12
    max_renewals: Optional[int] = None
    renewal_price_increase_percent: Optional[Decimal] = None
    total_value: Decimal = Decimal("0")
    currency: str = "EUR"
    billing_frequency: BillingFrequencyEnum = BillingFrequencyEnum.MONTHLY
    payment_terms_days: int = 30
    payment_method: Optional[str] = None
    price_revision_enabled: bool = False
    price_revision_index: Optional[str] = None
    price_revision_date: Optional[date] = None
    price_revision_cap_percent: Optional[Decimal] = None
    late_payment_rate: Decimal = Decimal("0.05")
    penalty_clause_enabled: bool = False
    penalty_percentage: Optional[Decimal] = None
    penalty_max_amount: Optional[Decimal] = None
    deposit_amount: Optional[Decimal] = None
    guarantee_type: Optional[str] = None
    guarantee_amount: Optional[Decimal] = None
    termination_notice_days: int = 90
    early_termination_penalty: Optional[Decimal] = None
    requires_approval: bool = True
    requires_signature: bool = True
    signature_method: Optional[str] = None
    owner_id: Optional[UUID] = None
    owner_name: Optional[str] = None
    team_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    gdpr_compliant: bool = True
    data_processing_agreement: bool = False
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    dispute_resolution: Optional[str] = None
    confidentiality_level: str = "standard"
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    external_reference: Optional[str] = None


class ContractCreate(ContractBase):
    """Creation de contrat."""
    parties: Optional[List[ContractPartyCreate]] = None
    lines: Optional[List[ContractLineCreate]] = None
    clauses: Optional[List[ContractClauseCreate]] = None


class ContractUpdate(BaseSchema):
    """Mise a jour de contrat."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    reference: Optional[str] = None
    contract_type: Optional[ContractTypeEnum] = None
    category_id: Optional[UUID] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    special_conditions: Optional[str] = None
    effective_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_months: Optional[int] = None
    duration_days: Optional[int] = None
    is_indefinite: Optional[bool] = None
    renewal_type: Optional[RenewalTypeEnum] = None
    renewal_notice_days: Optional[int] = None
    auto_renewal_term_months: Optional[int] = None
    max_renewals: Optional[int] = None
    renewal_price_increase_percent: Optional[Decimal] = None
    total_value: Optional[Decimal] = None
    currency: Optional[str] = None
    billing_frequency: Optional[BillingFrequencyEnum] = None
    payment_terms_days: Optional[int] = None
    payment_method: Optional[str] = None
    price_revision_enabled: Optional[bool] = None
    price_revision_index: Optional[str] = None
    price_revision_date: Optional[date] = None
    price_revision_cap_percent: Optional[Decimal] = None
    late_payment_rate: Optional[Decimal] = None
    penalty_clause_enabled: Optional[bool] = None
    penalty_percentage: Optional[Decimal] = None
    penalty_max_amount: Optional[Decimal] = None
    deposit_amount: Optional[Decimal] = None
    guarantee_type: Optional[str] = None
    guarantee_amount: Optional[Decimal] = None
    termination_notice_days: Optional[int] = None
    early_termination_penalty: Optional[Decimal] = None
    requires_approval: Optional[bool] = None
    requires_signature: Optional[bool] = None
    signature_method: Optional[str] = None
    owner_id: Optional[UUID] = None
    owner_name: Optional[str] = None
    team_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    gdpr_compliant: Optional[bool] = None
    data_processing_agreement: Optional[bool] = None
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    dispute_resolution: Optional[str] = None
    confidentiality_level: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    external_reference: Optional[str] = None


class ContractResponse(ContractBase, AuditMixin):
    """Reponse contrat complete."""
    id: UUID
    contract_number: str
    status: ContractStatusEnum = ContractStatusEnum.DRAFT
    status_reason: Optional[str] = None
    status_changed_at: Optional[datetime] = None
    status_changed_by: Optional[UUID] = None
    created_date: date
    signed_date: Optional[datetime] = None
    renewal_count: int = 0
    next_renewal_date: Optional[date] = None
    last_price_revision_date: Optional[date] = None
    deposit_received: bool = False
    termination_reason: Optional[str] = None
    termination_date: Optional[date] = None
    termination_by: Optional[UUID] = None
    approval_status: Optional[str] = None
    current_approver_id: Optional[UUID] = None
    approval_level: int = 0
    approved_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    signature_request_id: Optional[str] = None
    all_parties_signed: bool = False
    main_document_id: Optional[UUID] = None
    signed_document_id: Optional[UUID] = None
    compliance_status: Optional[str] = None
    compliance_notes: Optional[str] = None
    last_compliance_check: Optional[datetime] = None
    total_invoiced: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    amendment_count: int = 0

    # Relations embarquees (optionnel)
    parties: Optional[List[ContractPartyResponse]] = None
    lines: Optional[List[ContractLineResponse]] = None


class ContractSummaryResponse(BaseSchema):
    """Reponse resume de contrat."""
    id: UUID
    contract_number: str
    title: str
    contract_type: ContractTypeEnum
    status: ContractStatusEnum
    total_value: Decimal
    currency: str
    start_date: Optional[date]
    end_date: Optional[date]
    owner_name: Optional[str]
    party_names: List[str] = Field(default_factory=list)
    days_until_expiry: Optional[int] = None
    days_until_renewal: Optional[int] = None
    created_at: Optional[datetime]


# ============================================================================
# WORKFLOW SCHEMAS
# ============================================================================

class ContractSubmitForApprovalRequest(BaseSchema):
    """Requete pour soumettre pour approbation."""
    approver_id: UUID
    comments: Optional[str] = None


class ContractSignatureRequest(BaseSchema):
    """Requete pour signature."""
    party_id: UUID
    signature_method: Optional[str] = "electronic"


class ContractRecordSignatureRequest(BaseSchema):
    """Requete pour enregistrer une signature."""
    party_id: UUID
    signature_id: str
    signature_ip: Optional[str] = None


class ContractTerminateRequest(BaseSchema):
    """Requete pour resilier un contrat."""
    termination_date: date
    reason: str
    notice_given: bool = True
    penalty_amount: Optional[Decimal] = None


class ContractRenewRequest(BaseSchema):
    """Requete pour renouveler un contrat."""
    new_end_date: date
    new_value: Optional[Decimal] = None
    price_increase_percent: Optional[Decimal] = None
    new_terms: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


# ============================================================================
# FILTER AND LIST SCHEMAS
# ============================================================================

class ContractFilters(BaseSchema):
    """Filtres pour liste de contrats."""
    search: Optional[str] = None
    status: Optional[List[ContractStatusEnum]] = None
    contract_type: Optional[List[ContractTypeEnum]] = None
    category_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    party_id: Optional[UUID] = None
    party_name: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    expiring_within_days: Optional[int] = None
    renewal_due_within_days: Optional[int] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    currency: Optional[str] = None
    tags: Optional[List[str]] = None
    is_recurring: Optional[bool] = None
    requires_renewal_action: Optional[bool] = None


class ContractListResponse(BaseSchema):
    """Reponse liste de contrats."""
    items: List[ContractSummaryResponse]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1


# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class ContractStatsResponse(BaseSchema):
    """Statistiques des contrats."""
    total_contracts: int = 0
    active_contracts: int = 0
    draft_contracts: int = 0
    pending_signature: int = 0
    pending_approval: int = 0
    expired_contracts: int = 0
    terminated_contracts: int = 0
    total_active_value: Decimal = Decimal("0")
    average_contract_value: Decimal = Decimal("0")
    mrr: Decimal = Decimal("0")
    arr: Decimal = Decimal("0")
    expiring_30_days: int = 0
    expiring_60_days: int = 0
    expiring_90_days: int = 0
    renewal_rate: Optional[Decimal] = None
    churn_rate: Optional[Decimal] = None
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)
    overdue_obligations: int = 0
    pending_approvals: int = 0


class ContractDashboardResponse(BaseSchema):
    """Dashboard des contrats."""
    stats: ContractStatsResponse
    upcoming_renewals: List[ContractSummaryResponse] = Field(default_factory=list)
    expiring_soon: List[ContractSummaryResponse] = Field(default_factory=list)
    pending_approvals: List[ContractSummaryResponse] = Field(default_factory=list)
    pending_signatures: List[ContractSummaryResponse] = Field(default_factory=list)
    recent_contracts: List[ContractSummaryResponse] = Field(default_factory=list)
    overdue_obligations: List[ContractObligationResponse] = Field(default_factory=list)
    upcoming_milestones: List[ContractMilestoneResponse] = Field(default_factory=list)
    active_alerts: List[ContractAlertResponse] = Field(default_factory=list)


# ============================================================================
# HISTORY SCHEMA
# ============================================================================

class ContractHistoryResponse(BaseSchema):
    """Reponse historique contrat."""
    id: UUID
    contract_id: UUID
    version_number: int
    action: str
    action_detail: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    user_id: UUID
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
