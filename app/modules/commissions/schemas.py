"""
Schemas Pydantic - Module Commissions (GAP-041)

Schemas de validation et serialisation pour l'API REST.
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator


# ============================================================================
# ENUMS
# ============================================================================

class CommissionBasis(str, Enum):
    REVENUE = "revenue"
    REVENUE_TTC = "revenue_ttc"
    MARGIN = "margin"
    MARGIN_PERCENT = "margin_percent"
    GROSS_PROFIT = "gross_profit"
    VOLUME = "volume"
    CONTRACT_VALUE = "contract_value"
    NEW_BUSINESS = "new_business"
    UPSELL = "upsell"
    RENEWAL = "renewal"
    COLLECTED = "collected"


class TierType(str, Enum):
    FLAT = "flat"
    PROGRESSIVE = "progressive"
    RETROACTIVE = "retroactive"
    REGRESSIVE = "regressive"
    STEPPED = "stepped"


class CommissionStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CALCULATED = "calculated"
    APPROVED = "approved"
    DISPUTED = "disputed"
    ADJUSTED = "adjusted"
    VALIDATED = "validated"
    PAID = "paid"
    CANCELLED = "cancelled"
    CLAWBACK = "clawback"


class PlanStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class PaymentFrequency(str, Enum):
    IMMEDIATE = "immediate"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    ON_PAYMENT = "on_payment"
    ON_DELIVERY = "on_delivery"


class PeriodType(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    CUSTOM = "custom"


class AdjustmentType(str, Enum):
    BONUS = "bonus"
    PENALTY = "penalty"
    CORRECTION = "correction"
    CLAWBACK = "clawback"
    ADVANCE = "advance"
    GUARANTEE = "guarantee"
    OVERRIDE = "override"
    SPIFF = "spiff"


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


# ============================================================================
# SCHEMAS TIERS (PALIERS)
# ============================================================================

class CommissionTierBase(BaseModel):
    """Schema de base pour un palier."""
    tier_number: int = Field(..., ge=1)
    name: Optional[str] = Field(None, max_length=100)
    min_value: Decimal = Field(default=Decimal("0"), ge=0)
    max_value: Optional[Decimal] = Field(None, ge=0)
    rate: Decimal = Field(..., ge=0, le=100)
    fixed_amount: Decimal = Field(default=Decimal("0"), ge=0)
    tier_bonus: Decimal = Field(default=Decimal("0"), ge=0)

    @model_validator(mode='after')
    def validate_range(self):
        if self.max_value is not None and self.min_value >= self.max_value:
            raise ValueError("max_value doit etre superieur a min_value")
        return self


class CommissionTierCreate(CommissionTierBase):
    pass


class CommissionTierUpdate(BaseModel):
    tier_number: Optional[int] = Field(None, ge=1)
    name: Optional[str] = Field(None, max_length=100)
    min_value: Optional[Decimal] = Field(None, ge=0)
    max_value: Optional[Decimal] = Field(None, ge=0)
    rate: Optional[Decimal] = Field(None, ge=0, le=100)
    fixed_amount: Optional[Decimal] = Field(None, ge=0)
    tier_bonus: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CommissionTierResponse(CommissionTierBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    plan_id: UUID
    is_active: bool = True
    created_at: datetime


# ============================================================================
# SCHEMAS ACCELERATEURS
# ============================================================================

class AcceleratorBase(BaseModel):
    """Schema de base pour un accelerateur."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    threshold_type: str = Field(..., pattern="^(quota_percent|absolute_amount|growth_percent|rank|streak)$")
    threshold_value: Decimal = Field(..., ge=0)
    threshold_operator: str = Field(default=">=", pattern="^(>=|>|=|<|<=)$")
    multiplier: Decimal = Field(default=Decimal("1"), ge=0)
    bonus_amount: Decimal = Field(default=Decimal("0"), ge=0)
    bonus_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    is_cumulative: bool = False
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    max_applications: Optional[int] = Field(None, ge=1)
    max_bonus_amount: Optional[Decimal] = Field(None, ge=0)
    priority: int = Field(default=100, ge=1)


class AcceleratorCreate(AcceleratorBase):
    pass


class AcceleratorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    threshold_type: Optional[str] = None
    threshold_value: Optional[Decimal] = Field(None, ge=0)
    multiplier: Optional[Decimal] = Field(None, ge=0)
    bonus_amount: Optional[Decimal] = Field(None, ge=0)
    is_cumulative: Optional[bool] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_active: Optional[bool] = None


class AcceleratorResponse(AcceleratorBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    plan_id: UUID
    is_active: bool = True
    created_at: datetime


# ============================================================================
# SCHEMAS PLANS DE COMMISSION
# ============================================================================

class CommissionPlanBase(BaseModel):
    """Schema de base pour un plan de commission."""
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    basis: CommissionBasis = CommissionBasis.REVENUE
    tier_type: TierType = TierType.FLAT
    payment_frequency: PaymentFrequency = PaymentFrequency.MONTHLY
    quota_period: PeriodType = PeriodType.MONTHLY
    quota_amount: Optional[Decimal] = Field(None, ge=0)
    cap_enabled: bool = False
    cap_amount: Optional[Decimal] = Field(None, ge=0)
    cap_percent: Optional[float] = Field(None, ge=0, le=1000)
    minimum_guaranteed: Decimal = Field(default=Decimal("0"), ge=0)
    minimum_guaranteed_period: Optional[str] = None
    clawback_enabled: bool = True
    clawback_period_days: int = Field(default=90, ge=0, le=730)
    clawback_percent: float = Field(default=100.0, ge=0, le=100)
    trigger_on_invoice: bool = True
    trigger_on_payment: bool = False
    trigger_on_delivery: bool = False
    eligibility_rules: Dict[str, Any] = Field(default_factory=dict)
    apply_to_all_products: bool = True
    included_products: List[str] = Field(default_factory=list)
    excluded_products: List[str] = Field(default_factory=list)
    included_categories: List[str] = Field(default_factory=list)
    excluded_categories: List[str] = Field(default_factory=list)
    apply_to_all_customers: bool = True
    included_customer_segments: List[str] = Field(default_factory=list)
    excluded_customer_segments: List[str] = Field(default_factory=list)
    new_customers_only: bool = False
    effective_from: date
    effective_to: Optional[date] = None
    currency: str = Field(default="EUR", max_length=3)
    priority: int = Field(default=100, ge=1)
    settings: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v

    @model_validator(mode='after')
    def validate_dates(self):
        if self.effective_to and self.effective_from > self.effective_to:
            raise ValueError("effective_to doit etre apres effective_from")
        return self


class CommissionPlanCreate(CommissionPlanBase):
    tiers: List[CommissionTierCreate] = Field(default_factory=list)
    accelerators: List[AcceleratorCreate] = Field(default_factory=list)


class CommissionPlanUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    basis: Optional[CommissionBasis] = None
    tier_type: Optional[TierType] = None
    payment_frequency: Optional[PaymentFrequency] = None
    quota_period: Optional[PeriodType] = None
    quota_amount: Optional[Decimal] = None
    cap_enabled: Optional[bool] = None
    cap_amount: Optional[Decimal] = None
    minimum_guaranteed: Optional[Decimal] = None
    clawback_enabled: Optional[bool] = None
    clawback_period_days: Optional[int] = None
    trigger_on_invoice: Optional[bool] = None
    trigger_on_payment: Optional[bool] = None
    eligibility_rules: Optional[Dict[str, Any]] = None
    apply_to_all_products: Optional[bool] = None
    included_products: Optional[List[str]] = None
    excluded_products: Optional[List[str]] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    priority: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None


class CommissionPlanResponse(CommissionPlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    status: PlanStatus
    tiers: List[CommissionTierResponse] = Field(default_factory=list)
    accelerators: List[AcceleratorResponse] = Field(default_factory=list)
    version: int = 1
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    is_deleted: bool = False


class CommissionPlanListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    basis: CommissionBasis
    tier_type: TierType
    status: PlanStatus
    payment_frequency: PaymentFrequency
    effective_from: date
    effective_to: Optional[date] = None
    tier_count: int = 0
    assignment_count: int = 0
    is_active: bool = True


class CommissionPlanList(BaseModel):
    items: List[CommissionPlanListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# SCHEMAS ATTRIBUTION
# ============================================================================

class AssignmentBase(BaseModel):
    """Schema de base pour une attribution."""
    plan_id: UUID
    assignee_type: str = Field(..., pattern="^(employee|team|territory|role)$")
    assignee_id: UUID
    assignee_name: Optional[str] = Field(None, max_length=255)
    quota_override: Optional[Decimal] = Field(None, ge=0)
    quota_currency: str = Field(default="EUR", max_length=3)
    effective_from: date
    effective_to: Optional[date] = None
    personal_rate_override: Optional[Decimal] = Field(None, ge=0, le=100)
    personal_cap_override: Optional[Decimal] = Field(None, ge=0)


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    quota_override: Optional[Decimal] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None
    personal_rate_override: Optional[Decimal] = None
    personal_cap_override: Optional[Decimal] = None


class AssignmentResponse(AssignmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None


class AssignmentList(BaseModel):
    items: List[AssignmentResponse]
    total: int


# ============================================================================
# SCHEMAS TEAM MEMBER
# ============================================================================

class TeamMemberBase(BaseModel):
    employee_id: UUID
    employee_name: Optional[str] = Field(None, max_length=255)
    employee_email: Optional[str] = Field(None, max_length=255)
    role: str = Field(..., pattern="^(sales_rep|senior_rep|account_executive|team_lead|sales_manager|director|vp)$")
    parent_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    team_name: Optional[str] = Field(None, max_length=100)
    territory: Optional[str] = Field(None, max_length=100)
    override_enabled: bool = False
    override_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    override_basis: CommissionBasis = CommissionBasis.REVENUE
    override_levels: int = Field(default=1, ge=1, le=5)
    default_split_percent: Decimal = Field(default=Decimal("100"), ge=0, le=100)
    start_date: date
    end_date: Optional[date] = None


class TeamMemberCreate(TeamMemberBase):
    pass


class TeamMemberUpdate(BaseModel):
    employee_name: Optional[str] = None
    role: Optional[str] = None
    parent_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    team_name: Optional[str] = None
    territory: Optional[str] = None
    override_enabled: Optional[bool] = None
    override_rate: Optional[Decimal] = None
    override_levels: Optional[int] = None
    default_split_percent: Optional[Decimal] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class TeamMemberResponse(TeamMemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    subordinates_count: int = 0


# ============================================================================
# SCHEMAS TRANSACTIONS
# ============================================================================

class TransactionBase(BaseModel):
    source_type: str = Field(..., pattern="^(invoice|order|contract|subscription|payment)$")
    source_id: UUID
    source_number: Optional[str] = Field(None, max_length=100)
    source_date: date
    sales_rep_id: UUID
    sales_rep_name: Optional[str] = Field(None, max_length=255)
    customer_id: UUID
    customer_name: Optional[str] = Field(None, max_length=255)
    customer_segment: Optional[str] = Field(None, max_length=50)
    is_new_customer: bool = False
    product_id: Optional[UUID] = None
    product_code: Optional[str] = Field(None, max_length=50)
    product_name: Optional[str] = Field(None, max_length=255)
    product_category: Optional[str] = Field(None, max_length=100)
    revenue: Decimal = Field(..., ge=0)
    revenue_ttc: Optional[Decimal] = Field(None, ge=0)
    cost: Decimal = Field(default=Decimal("0"), ge=0)
    margin: Optional[Decimal] = None
    quantity: Decimal = Field(default=Decimal("1"), ge=0)
    currency: str = Field(default="EUR", max_length=3)
    transaction_type: str = Field(default="standard")
    is_recurring: bool = False
    contract_months: Optional[int] = Field(None, ge=1)
    opportunity_id: Optional[UUID] = None
    campaign_id: Optional[UUID] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)


class TransactionCreate(TransactionBase):
    split_config: List[Dict[str, Any]] = Field(default_factory=list)


class TransactionUpdate(BaseModel):
    sales_rep_id: Optional[UUID] = None
    revenue: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    payment_status: Optional[str] = None
    payment_date: Optional[date] = None
    payment_amount: Optional[Decimal] = None
    delivery_status: Optional[str] = None
    delivery_date: Optional[date] = None
    split_config: Optional[List[Dict[str, Any]]] = None
    extra_data: Optional[Dict[str, Any]] = None


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    margin_percent: Optional[Decimal] = None
    payment_status: str = "pending"
    payment_date: Optional[date] = None
    payment_amount: Optional[Decimal] = None
    delivery_status: Optional[str] = None
    delivery_date: Optional[date] = None
    has_split: bool = False
    split_config: List[Dict[str, Any]] = Field(default_factory=list)
    commission_status: str = "pending"
    commission_locked: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class TransactionList(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# SCHEMAS CALCULS
# ============================================================================

class CalculationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    transaction_id: Optional[UUID] = None
    plan_id: UUID
    period_id: Optional[UUID] = None
    sales_rep_id: UUID
    sales_rep_name: Optional[str] = None
    period_start: date
    period_end: date
    basis: str
    base_amount: Decimal
    currency: str = "EUR"
    rate_applied: Optional[Decimal] = None
    tier_applied: Optional[str] = None
    commission_amount: Decimal
    accelerator_bonus: Decimal = Decimal("0")
    accelerators_applied: List[str] = Field(default_factory=list)
    split_percent: Decimal = Decimal("100")
    split_role: Optional[str] = None
    original_amount: Optional[Decimal] = None
    gross_commission: Decimal
    adjustments: Decimal = Decimal("0")
    net_commission: Decimal
    cap_applied: bool = False
    cap_amount: Optional[Decimal] = None
    quota_target: Optional[Decimal] = None
    quota_achieved: Optional[Decimal] = None
    achievement_rate: Optional[Decimal] = None
    calculation_details: Dict[str, Any] = Field(default_factory=dict)
    status: CommissionStatus
    calculated_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    paid_at: Optional[datetime] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    version: int = 1


class CalculationList(BaseModel):
    items: List[CalculationResponse]
    total: int
    page: int
    page_size: int
    pages: int


class CalculationRequest(BaseModel):
    """Demande de calcul de commission."""
    sales_rep_id: UUID
    plan_id: UUID
    period_start: date
    period_end: date
    recalculate: bool = False  # Force recalcul meme si deja calcule


class BulkCalculationRequest(BaseModel):
    """Demande de calcul en masse."""
    period_id: Optional[UUID] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    plan_ids: List[UUID] = Field(default_factory=list)  # Vide = tous les plans
    sales_rep_ids: List[UUID] = Field(default_factory=list)  # Vide = tous les commerciaux
    recalculate: bool = False


# ============================================================================
# SCHEMAS PERIODES
# ============================================================================

class PeriodBase(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    period_type: PeriodType
    start_date: date
    end_date: date
    close_date: Optional[date] = None
    payment_date: Optional[date] = None
    notes: Optional[str] = None


class PeriodCreate(PeriodBase):
    pass


class PeriodUpdate(BaseModel):
    name: Optional[str] = None
    close_date: Optional[date] = None
    payment_date: Optional[date] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class PeriodResponse(PeriodBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    status: str = "open"
    is_locked: bool = False
    total_commissions: Decimal = Decimal("0")
    total_adjustments: Decimal = Decimal("0")
    total_clawbacks: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    transaction_count: int = 0
    calculation_count: int = 0
    calculated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime


class PeriodList(BaseModel):
    items: List[PeriodResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# SCHEMAS RELEVES (STATEMENTS)
# ============================================================================

class StatementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    statement_number: str
    period_id: UUID
    sales_rep_id: UUID
    sales_rep_name: Optional[str] = None
    sales_rep_email: Optional[str] = None
    period_start: date
    period_end: date
    gross_commissions: Decimal = Decimal("0")
    accelerator_bonuses: Decimal = Decimal("0")
    adjustments: Decimal = Decimal("0")
    clawbacks: Decimal = Decimal("0")
    advances: Decimal = Decimal("0")
    net_commission: Decimal
    currency: str = "EUR"
    ytd_commissions: Decimal = Decimal("0")
    ytd_sales: Decimal = Decimal("0")
    ytd_quota_achievement: Optional[Decimal] = None
    transaction_count: int = 0
    calculation_ids: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
    status: CommissionStatus
    generated_at: datetime
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    payment_reference: Optional[str] = None
    payroll_exported: bool = False


class StatementList(BaseModel):
    items: List[StatementResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# SCHEMAS AJUSTEMENTS
# ============================================================================

class AdjustmentBase(BaseModel):
    adjustment_type: AdjustmentType
    sales_rep_id: UUID
    sales_rep_name: Optional[str] = Field(None, max_length=255)
    period_id: Optional[UUID] = None
    effective_date: date
    amount: Decimal  # Peut etre negatif
    currency: str = Field(default="EUR", max_length=3)
    related_calculation_id: Optional[UUID] = None
    related_transaction_id: Optional[UUID] = None
    reason: str = Field(..., min_length=1)
    supporting_documents: List[str] = Field(default_factory=list)


class AdjustmentCreate(AdjustmentBase):
    pass


class AdjustmentUpdate(BaseModel):
    amount: Optional[Decimal] = None
    reason: Optional[str] = None
    supporting_documents: Optional[List[str]] = None


class AdjustmentResponse(AdjustmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    code: str
    status: WorkflowStatus
    requested_by: UUID
    requested_at: datetime
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[UUID] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    statement_id: Optional[UUID] = None
    paid_at: Optional[datetime] = None
    created_at: datetime


class AdjustmentList(BaseModel):
    items: List[AdjustmentResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# SCHEMAS CLAWBACKS
# ============================================================================

class ClawbackBase(BaseModel):
    original_calculation_id: UUID
    original_transaction_id: UUID
    sales_rep_id: UUID
    sales_rep_name: Optional[str] = Field(None, max_length=255)
    clawback_amount: Decimal = Field(..., ge=0)
    clawback_percent: Decimal = Field(default=Decimal("100"), ge=0, le=100)
    currency: str = Field(default="EUR", max_length=3)
    reason: str = Field(..., pattern="^(cancellation|refund|chargeback|return|credit_note|error)$")
    reason_details: Optional[str] = None
    cancellation_date: date
    source_document_type: Optional[str] = None
    source_document_id: Optional[UUID] = None
    source_document_number: Optional[str] = None


class ClawbackCreate(ClawbackBase):
    pass


class ClawbackUpdate(BaseModel):
    clawback_amount: Optional[Decimal] = None
    reason_details: Optional[str] = None
    status: Optional[str] = None
    waiver_reason: Optional[str] = None


class ClawbackResponse(ClawbackBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    code: str
    original_commission: Decimal
    status: str = "pending"
    applied_to_statement_id: Optional[UUID] = None
    applied_at: Optional[datetime] = None
    applied_amount: Optional[Decimal] = None
    remaining_amount: Optional[Decimal] = None
    created_by: Optional[UUID] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime


class ClawbackList(BaseModel):
    items: List[ClawbackResponse]
    total: int


# ============================================================================
# SCHEMAS WORKFLOW
# ============================================================================

class WorkflowAction(BaseModel):
    action: str = Field(..., pattern="^(approve|reject|escalate|request_info)$")
    comments: Optional[str] = None
    next_approver_id: Optional[UUID] = None  # Pour escalade


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    workflow_type: str
    entity_type: str
    entity_id: UUID
    current_step: int
    total_steps: int
    current_approver_role: Optional[str] = None
    current_approver_id: Optional[UUID] = None
    status: WorkflowStatus
    amount: Optional[Decimal] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)
    initiated_at: datetime
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ============================================================================
# SCHEMAS STATISTIQUES & DASHBOARD
# ============================================================================

class SalesRepPerformance(BaseModel):
    sales_rep_id: UUID
    sales_rep_name: str
    period_start: date
    period_end: date
    total_revenue: Decimal = Decimal("0")
    total_margin: Decimal = Decimal("0")
    transaction_count: int = 0
    new_customer_count: int = 0
    quota_target: Optional[Decimal] = None
    quota_achieved: Decimal = Decimal("0")
    achievement_rate: Optional[Decimal] = None
    total_commissions: Decimal = Decimal("0")
    commission_rate_effective: Optional[Decimal] = None
    rank: Optional[int] = None


class TeamPerformance(BaseModel):
    team_id: UUID
    team_name: str
    period_start: date
    period_end: date
    member_count: int = 0
    total_revenue: Decimal = Decimal("0")
    total_margin: Decimal = Decimal("0")
    total_commissions: Decimal = Decimal("0")
    quota_target: Optional[Decimal] = None
    quota_achieved: Decimal = Decimal("0")
    achievement_rate: Optional[Decimal] = None
    top_performer_id: Optional[UUID] = None
    top_performer_name: Optional[str] = None


class CommissionDashboard(BaseModel):
    period_start: date
    period_end: date
    # Totaux
    total_revenue: Decimal = Decimal("0")
    total_commissions: Decimal = Decimal("0")
    total_pending: Decimal = Decimal("0")
    total_approved: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    # Compteurs
    transaction_count: int = 0
    calculation_count: int = 0
    active_plans_count: int = 0
    active_reps_count: int = 0
    # Tendances
    commission_trend: List[Dict[str, Any]] = Field(default_factory=list)
    revenue_trend: List[Dict[str, Any]] = Field(default_factory=list)
    # Top performers
    top_performers: List[SalesRepPerformance] = Field(default_factory=list)
    # Par plan
    by_plan: List[Dict[str, Any]] = Field(default_factory=list)
    # Par statut
    by_status: Dict[str, int] = Field(default_factory=dict)
    # Alertes
    pending_approvals: int = 0
    overdue_payments: int = 0
    disputed_calculations: int = 0


class Leaderboard(BaseModel):
    period_start: date
    period_end: date
    metric: str  # "revenue", "margin", "commissions", "quota_achievement"
    entries: List[SalesRepPerformance]


# ============================================================================
# SCHEMAS FILTRES
# ============================================================================

class PlanFilters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    status: Optional[List[PlanStatus]] = None
    basis: Optional[List[CommissionBasis]] = None
    effective_date: Optional[date] = None
    include_expired: bool = False


class CalculationFilters(BaseModel):
    search: Optional[str] = None
    sales_rep_id: Optional[UUID] = None
    plan_id: Optional[UUID] = None
    period_id: Optional[UUID] = None
    status: Optional[List[CommissionStatus]] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None


class TransactionFilters(BaseModel):
    search: Optional[str] = None
    sales_rep_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    source_type: Optional[str] = None
    commission_status: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_revenue: Optional[Decimal] = None
    max_revenue: Optional[Decimal] = None


# ============================================================================
# SCHEMAS COMMUNS
# ============================================================================

class AutocompleteItem(BaseModel):
    id: str
    code: str
    name: str
    label: str


class AutocompleteResponse(BaseModel):
    items: List[AutocompleteItem]


class BulkActionResult(BaseModel):
    success_count: int
    error_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    created_ids: List[UUID] = Field(default_factory=list)


class ExportRequest(BaseModel):
    format: str = Field(default="csv", pattern="^(csv|xlsx|pdf)$")
    period_id: Optional[UUID] = None
    sales_rep_ids: List[UUID] = Field(default_factory=list)
    include_details: bool = True
