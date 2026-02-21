"""
Schémas Pydantic Referral / Parrainage
=======================================
- Validation stricte
- Types correspondant exactement au frontend
"""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ============== Énumérations ==============

class ProgramStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    ARCHIVED = "archived"


class RewardType(str, Enum):
    CASH = "cash"
    CREDIT = "credit"
    DISCOUNT_PERCENT = "discount_percent"
    DISCOUNT_AMOUNT = "discount_amount"
    FREE_PRODUCT = "free_product"
    FREE_SERVICE = "free_service"
    POINTS = "points"
    GIFT_CARD = "gift_card"
    CUSTOM = "custom"


class RewardTrigger(str, Enum):
    SIGNUP = "signup"
    FIRST_PURCHASE = "first_purchase"
    PURCHASE_AMOUNT = "purchase_amount"
    SUBSCRIPTION = "subscription"
    MILESTONE = "milestone"
    MANUAL = "manual"


class ReferralStatus(str, Enum):
    PENDING = "pending"
    CLICKED = "clicked"
    SIGNED_UP = "signed_up"
    CONVERTED = "converted"
    QUALIFIED = "qualified"
    REWARDED = "rewarded"
    EXPIRED = "expired"
    REJECTED = "rejected"
    FRAUDULENT = "fraudulent"


class PayoutStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class FraudReason(str, Enum):
    SELF_REFERRAL = "self_referral"
    SAME_IP = "same_ip"
    SAME_DEVICE = "same_device"
    SAME_PAYMENT = "same_payment"
    VELOCITY = "velocity"
    PATTERN = "pattern"
    MANUAL_FLAG = "manual_flag"


# ============== RewardTier Schemas ==============

class RewardTierBase(BaseModel):
    """Base RewardTier."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    min_referrals: int = Field(default=0, ge=0)
    max_referrals: Optional[int] = Field(None, ge=0)
    min_conversion_amount: Decimal = Field(default=Decimal("0"), ge=0)
    referrer_reward_type: RewardType = RewardType.CREDIT
    referrer_reward_value: Decimal = Field(default=Decimal("0"), ge=0)
    referrer_reward_description: str = Field(default="", max_length=500)
    referee_reward_type: RewardType = RewardType.DISCOUNT_PERCENT
    referee_reward_value: Decimal = Field(default=Decimal("0"), ge=0)
    referee_reward_description: str = Field(default="", max_length=500)
    max_uses: Optional[int] = Field(None, ge=1)
    priority: int = Field(default=0, ge=0)


class RewardTierCreate(RewardTierBase):
    """Création RewardTier."""
    pass


class RewardTierUpdate(BaseModel):
    """Mise à jour RewardTier."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    min_referrals: Optional[int] = Field(None, ge=0)
    max_referrals: Optional[int] = Field(None, ge=0)
    min_conversion_amount: Optional[Decimal] = Field(None, ge=0)
    referrer_reward_type: Optional[RewardType] = None
    referrer_reward_value: Optional[Decimal] = Field(None, ge=0)
    referrer_reward_description: Optional[str] = None
    referee_reward_type: Optional[RewardType] = None
    referee_reward_value: Optional[Decimal] = Field(None, ge=0)
    referee_reward_description: Optional[str] = None
    max_uses: Optional[int] = Field(None, ge=1)
    priority: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class RewardTierResponse(RewardTierBase):
    """Réponse RewardTier."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    program_id: UUID
    current_uses: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============== ReferralProgram Schemas ==============

class ReferralProgramBase(BaseModel):
    """Base ReferralProgram."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    require_conversion: bool = True
    conversion_window_days: int = Field(default=30, ge=1)
    min_conversion_amount: Decimal = Field(default=Decimal("0"), ge=0)
    max_referrals_per_referrer: Optional[int] = Field(None, ge=1)
    max_total_referrals: Optional[int] = Field(None, ge=1)
    multi_level_enabled: bool = False
    max_levels: int = Field(default=1, ge=1, le=10)
    level_commission_rates: List[Decimal] = Field(default_factory=list)
    total_budget: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    allow_self_referral: bool = False
    require_unique_email: bool = True
    require_unique_device: bool = True
    eligible_user_segments: List[str] = Field(default_factory=list)
    terms_conditions: str = Field(default="", max_length=50000)
    tags: List[str] = Field(default_factory=list)
    extra_data: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()

    @model_validator(mode='after')
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError('end_date must be after start_date')
        return self


class ReferralProgramCreate(ReferralProgramBase):
    """Création ReferralProgram."""
    tiers: List[RewardTierCreate] = Field(default_factory=list)


class ReferralProgramUpdate(BaseModel):
    """Mise à jour ReferralProgram."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[ProgramStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    require_conversion: Optional[bool] = None
    conversion_window_days: Optional[int] = Field(None, ge=1)
    min_conversion_amount: Optional[Decimal] = Field(None, ge=0)
    max_referrals_per_referrer: Optional[int] = Field(None, ge=1)
    max_total_referrals: Optional[int] = Field(None, ge=1)
    multi_level_enabled: Optional[bool] = None
    max_levels: Optional[int] = Field(None, ge=1, le=10)
    level_commission_rates: Optional[List[Decimal]] = None
    total_budget: Optional[Decimal] = Field(None, ge=0)
    allow_self_referral: Optional[bool] = None
    require_unique_email: Optional[bool] = None
    require_unique_device: Optional[bool] = None
    terms_conditions: Optional[str] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[Dict[str, Any]] = None


class ReferralProgramResponse(ReferralProgramBase):
    """Réponse ReferralProgram."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    status: ProgramStatus
    current_total_referrals: int = 0
    spent_budget: Decimal = Decimal("0")
    total_clicks: int = 0
    total_signups: int = 0
    total_conversions: int = 0
    total_rewards_paid: Decimal = Decimal("0")
    tiers: List[RewardTierResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    is_deleted: bool = False
    version: int = 1


class ReferralProgramListItem(BaseModel):
    """Item léger pour listes."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    status: ProgramStatus
    start_date: Optional[date]
    end_date: Optional[date]
    total_referrals: int = 0
    total_conversions: int = 0
    conversion_rate: Decimal = Decimal("0")
    created_at: datetime


# ============== ReferralCode Schemas ==============

class ReferralCodeBase(BaseModel):
    """Base ReferralCode."""
    code: str = Field(..., min_length=2, max_length=50)
    short_url: Optional[str] = Field(None, max_length=255)
    max_uses: Optional[int] = Field(None, ge=1)
    expires_at: Optional[datetime] = None
    custom_message: str = Field(default="", max_length=1000)
    extra_data: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()


class ReferralCodeCreate(ReferralCodeBase):
    """Création ReferralCode."""
    program_id: UUID
    referrer_id: UUID


class ReferralCodeUpdate(BaseModel):
    """Mise à jour ReferralCode."""
    short_url: Optional[str] = None
    max_uses: Optional[int] = Field(None, ge=1)
    expires_at: Optional[datetime] = None
    custom_message: Optional[str] = None
    is_active: Optional[bool] = None
    extra_data: Optional[Dict[str, Any]] = None


class ReferralCodeResponse(ReferralCodeBase):
    """Réponse ReferralCode."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    program_id: UUID
    referrer_id: UUID
    total_clicks: int = 0
    total_signups: int = 0
    total_conversions: int = 0
    total_earnings: Decimal = Decimal("0")
    current_uses: int = 0
    is_active: bool = True
    created_at: datetime
    last_used_at: Optional[datetime] = None


class ReferralCodeListItem(BaseModel):
    """Item léger pour listes."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    program_id: UUID
    referrer_id: UUID
    total_clicks: int = 0
    total_conversions: int = 0
    is_active: bool = True
    created_at: datetime


# ============== Referral Schemas ==============

class ReferralBase(BaseModel):
    """Base Referral."""
    referee_email: str = Field(default="", max_length=255)
    referee_name: str = Field(default="", max_length=255)
    ip_address: str = Field(default="", max_length=45)
    user_agent: str = Field(default="", max_length=1000)
    device_fingerprint: str = Field(default="", max_length=255)
    utm_source: str = Field(default="", max_length=100)
    utm_medium: str = Field(default="", max_length=100)
    utm_campaign: str = Field(default="", max_length=100)
    landing_page: str = Field(default="", max_length=2000)
    notes: str = Field(default="", max_length=5000)
    extra_data: Dict[str, Any] = Field(default_factory=dict)


class ReferralCreate(ReferralBase):
    """Création Referral."""
    program_id: UUID
    referral_code_id: UUID
    referrer_id: UUID
    referee_id: Optional[UUID] = None


class ReferralUpdate(BaseModel):
    """Mise à jour Referral."""
    referee_id: Optional[UUID] = None
    referee_email: Optional[str] = None
    referee_name: Optional[str] = None
    status: Optional[ReferralStatus] = None
    conversion_order_id: Optional[UUID] = None
    conversion_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class ReferralResponse(ReferralBase):
    """Réponse Referral."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    program_id: UUID
    referral_code_id: UUID
    referrer_id: UUID
    referee_id: Optional[UUID]
    status: ReferralStatus
    click_timestamp: Optional[datetime]
    signup_timestamp: Optional[datetime]
    conversion_timestamp: Optional[datetime]
    qualification_timestamp: Optional[datetime]
    conversion_order_id: Optional[UUID]
    conversion_amount: Decimal = Decimal("0")
    level: int = 1
    parent_referral_id: Optional[UUID]
    fraud_score: Decimal = Decimal("0")
    fraud_flags: List[str] = []
    is_suspicious: bool = False
    referrer_reward_id: Optional[UUID]
    referee_reward_id: Optional[UUID]
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]


class ReferralListItem(BaseModel):
    """Item léger pour listes."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    program_id: UUID
    referrer_id: UUID
    referee_id: Optional[UUID]
    referee_email: str
    status: ReferralStatus
    conversion_amount: Decimal = Decimal("0")
    is_suspicious: bool = False
    created_at: datetime


# ============== Reward Schemas ==============

class RewardCreate(BaseModel):
    """Création Reward."""
    program_id: UUID
    referral_id: UUID
    user_id: UUID
    is_referrer_reward: bool = True
    reward_type: RewardType = RewardType.CREDIT
    reward_value: Decimal = Field(..., ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    description: str = Field(default="", max_length=500)
    expires_at: Optional[datetime] = None
    discount_code: Optional[str] = Field(None, max_length=50)
    product_id: Optional[UUID] = None


class RewardUpdate(BaseModel):
    """Mise à jour Reward."""
    is_claimed: Optional[bool] = None
    discount_code: Optional[str] = None
    credit_transaction_id: Optional[UUID] = None
    payout_id: Optional[UUID] = None


class RewardResponse(BaseModel):
    """Réponse Reward."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    program_id: UUID
    referral_id: UUID
    user_id: UUID
    is_referrer_reward: bool
    reward_type: RewardType
    reward_value: Decimal
    currency: str
    description: str
    is_claimed: bool = False
    claimed_at: Optional[datetime]
    expires_at: Optional[datetime]
    discount_code: Optional[str]
    product_id: Optional[UUID]
    credit_transaction_id: Optional[UUID]
    payout_id: Optional[UUID]
    created_at: datetime


# ============== Payout Schemas ==============

class PayoutCreate(BaseModel):
    """Création Payout."""
    user_id: UUID
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    payment_method: str = Field(..., min_length=1, max_length=50)
    payment_details: Dict[str, Any] = Field(default_factory=dict)
    reward_ids: List[UUID] = Field(default_factory=list)


class PayoutUpdate(BaseModel):
    """Mise à jour Payout."""
    status: Optional[PayoutStatus] = None
    transaction_reference: Optional[str] = None
    failure_reason: Optional[str] = None


class PayoutResponse(BaseModel):
    """Réponse Payout."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    status: PayoutStatus
    payment_method: str
    payment_details: Dict[str, Any]
    processed_at: Optional[datetime]
    transaction_reference: str
    failure_reason: str
    created_at: datetime
    updated_at: Optional[datetime]


# ============== FraudCheck Schemas ==============

class FraudCheckCreate(BaseModel):
    """Création FraudCheck."""
    referral_id: UUID
    check_type: str = Field(..., min_length=1, max_length=50)
    result: str = Field(..., pattern="^(pass|fail|warning)$")
    score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    details: Dict[str, Any] = Field(default_factory=dict)


class FraudCheckResponse(BaseModel):
    """Réponse FraudCheck."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    referral_id: UUID
    check_type: str
    result: str
    score: Decimal
    details: Dict[str, Any]
    created_at: datetime


# ============== Tracking Schemas ==============

class TrackClickRequest(BaseModel):
    """Requête tracking de clic."""
    code: str = Field(..., min_length=2, max_length=50)
    ip_address: str = Field(default="", max_length=45)
    user_agent: str = Field(default="", max_length=1000)
    device_fingerprint: str = Field(default="", max_length=255)
    utm_source: str = Field(default="", max_length=100)
    utm_medium: str = Field(default="", max_length=100)
    utm_campaign: str = Field(default="", max_length=100)
    landing_page: str = Field(default="", max_length=2000)


class TrackSignupRequest(BaseModel):
    """Requête tracking d'inscription."""
    referral_id: UUID
    referee_id: UUID
    referee_email: str = Field(..., max_length=255)
    referee_name: str = Field(default="", max_length=255)


class TrackConversionRequest(BaseModel):
    """Requête tracking de conversion."""
    referral_id: UUID
    order_id: UUID
    amount: Decimal = Field(..., ge=0)


# ============== Stats Schemas ==============

class ReferralStats(BaseModel):
    """Statistiques de parrainage."""
    tenant_id: UUID
    program_id: Optional[UUID] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None

    # Volume
    total_clicks: int = 0
    total_signups: int = 0
    total_conversions: int = 0
    total_qualified: int = 0

    # Taux
    click_to_signup_rate: Decimal = Decimal("0")
    signup_to_conversion_rate: Decimal = Decimal("0")
    overall_conversion_rate: Decimal = Decimal("0")

    # Valeur
    total_conversion_value: Decimal = Decimal("0")
    average_order_value: Decimal = Decimal("0")
    total_rewards_issued: Decimal = Decimal("0")
    total_rewards_claimed: Decimal = Decimal("0")

    # ROI
    roi: Decimal = Decimal("0")
    cost_per_acquisition: Decimal = Decimal("0")

    # Top performers
    top_referrers: List[Dict[str, Any]] = Field(default_factory=list)

    # Fraude
    fraud_detected: int = 0
    fraud_prevented_value: Decimal = Decimal("0")


class ReferrerProfile(BaseModel):
    """Profil d'un parrain."""
    user_id: UUID
    tenant_id: UUID
    active_codes: List[str] = Field(default_factory=list)
    total_referrals: int = 0
    successful_referrals: int = 0
    pending_referrals: int = 0
    total_earnings: Decimal = Decimal("0")
    pending_earnings: Decimal = Decimal("0")
    paid_earnings: Decimal = Decimal("0")
    referrer_level: int = 1
    referrer_rank: str = ""
    first_referral_date: Optional[date] = None
    last_referral_date: Optional[date] = None
    conversion_rate: Decimal = Decimal("0")


# ============== Pagination ==============

class PaginatedProgramList(BaseModel):
    """Liste paginée ReferralProgram."""
    items: List[ReferralProgramListItem]
    total: int
    page: int
    page_size: int
    pages: int


class PaginatedCodeList(BaseModel):
    """Liste paginée ReferralCode."""
    items: List[ReferralCodeListItem]
    total: int
    page: int
    page_size: int
    pages: int


class PaginatedReferralList(BaseModel):
    """Liste paginée Referral."""
    items: List[ReferralListItem]
    total: int
    page: int
    page_size: int
    pages: int


class PaginatedPayoutList(BaseModel):
    """Liste paginée Payout."""
    items: List[PayoutResponse]
    total: int
    page: int
    page_size: int
    pages: int


# Aliases
ReferralProgramListResponse = PaginatedProgramList
ReferralCodeListResponse = PaginatedCodeList
ReferralListResponse = PaginatedReferralList
PayoutListResponse = PaginatedPayoutList


# ============== Autocomplete ==============

class AutocompleteItem(BaseModel):
    """Item autocomplete."""
    id: str
    code: str
    name: str
    label: str


class AutocompleteResponse(BaseModel):
    """Réponse autocomplete."""
    items: List[AutocompleteItem]


# ============== Filtres ==============

class ProgramFilters(BaseModel):
    """Filtres Program."""
    search: Optional[str] = Field(None, min_length=2)
    status: Optional[List[ProgramStatus]] = None
    tags: Optional[List[str]] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class ReferralFilters(BaseModel):
    """Filtres Referral."""
    search: Optional[str] = Field(None, min_length=2)
    program_id: Optional[UUID] = None
    referrer_id: Optional[UUID] = None
    referee_id: Optional[UUID] = None
    status: Optional[List[ReferralStatus]] = None
    is_suspicious: Optional[bool] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class PayoutFilters(BaseModel):
    """Filtres Payout."""
    user_id: Optional[UUID] = None
    status: Optional[List[PayoutStatus]] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


# ============== Bulk ==============

class BulkResult(BaseModel):
    """Résultat opération en masse."""
    success: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)
