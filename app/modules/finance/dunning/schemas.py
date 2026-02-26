"""
AZALS MODULE - Dunning (Relances Impayés): Schemas
===================================================

Schémas Pydantic pour la gestion des relances impayés.
"""
from __future__ import annotations


from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# ENUMS AS LITERALS
# ============================================================================

DunningLevelTypeEnum = Literal[
    "REMINDER",
    "FIRST_NOTICE",
    "SECOND_NOTICE",
    "FORMAL_NOTICE",
    "FINAL_NOTICE",
    "COLLECTION",
]

DunningChannelEnum = Literal["EMAIL", "SMS", "LETTER", "PHONE", "REGISTERED"]

DunningStatusEnum = Literal[
    "PENDING", "SENT", "DELIVERED", "READ", "FAILED", "CANCELLED"
]

CampaignStatusEnum = Literal[
    "DRAFT", "SCHEDULED", "RUNNING", "COMPLETED", "PAUSED", "CANCELLED"
]

PaymentPromiseStatusEnum = Literal[
    "PENDING", "KEPT", "BROKEN", "PARTIAL", "CANCELLED"
]


# ============================================================================
# DUNNING LEVEL
# ============================================================================


class DunningLevelCreate(BaseModel):
    """Création d'un niveau de relance."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    level_type: DunningLevelTypeEnum
    sequence: int = Field(1, ge=1, le=99)
    days_after_due: int = Field(7, ge=0)
    days_before_next: Optional[int] = Field(None, ge=1)
    channels: list[DunningChannelEnum] = ["EMAIL"]
    primary_channel: DunningChannelEnum = "EMAIL"
    block_orders: bool = False
    add_fees: bool = False
    fee_amount: Optional[Decimal] = None
    fee_percentage: Optional[Decimal] = None
    apply_late_interest: bool = False
    late_interest_rate: Optional[Decimal] = None
    fixed_recovery_fee: Optional[Decimal] = Field(default=Decimal("40.00"))
    require_approval: bool = False


class DunningLevelUpdate(BaseModel):
    """Mise à jour d'un niveau de relance."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    days_after_due: Optional[int] = Field(None, ge=0)
    days_before_next: Optional[int] = Field(None, ge=1)
    channels: Optional[list[DunningChannelEnum]] = None
    primary_channel: Optional[DunningChannelEnum] = None
    block_orders: Optional[bool] = None
    add_fees: Optional[bool] = None
    fee_amount: Optional[Decimal] = None
    fee_percentage: Optional[Decimal] = None
    apply_late_interest: Optional[bool] = None
    late_interest_rate: Optional[Decimal] = None
    fixed_recovery_fee: Optional[Decimal] = None
    require_approval: Optional[bool] = None
    is_active: Optional[bool] = None


class DunningLevelResponse(BaseModel):
    """Réponse niveau de relance."""
    id: UUID
    tenant_id: str
    code: str
    name: str
    level_type: DunningLevelTypeEnum
    sequence: int
    days_after_due: int
    days_before_next: Optional[int] = None
    channels: list[str]
    primary_channel: DunningChannelEnum
    block_orders: bool
    add_fees: bool
    fee_amount: Optional[Decimal] = None
    fee_percentage: Optional[Decimal] = None
    apply_late_interest: bool
    late_interest_rate: Optional[Decimal] = None
    fixed_recovery_fee: Optional[Decimal] = None
    require_approval: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# DUNNING TEMPLATE
# ============================================================================


class DunningTemplateCreate(BaseModel):
    """Création d'un template de relance."""
    level_id: UUID
    channel: DunningChannelEnum
    language: str = Field("fr", max_length=5)
    subject: Optional[str] = Field(None, max_length=500)
    body: str = Field(..., min_length=1)
    is_default: bool = False


class DunningTemplateUpdate(BaseModel):
    """Mise à jour d'un template."""
    subject: Optional[str] = Field(None, max_length=500)
    body: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class DunningTemplateResponse(BaseModel):
    """Réponse template de relance."""
    id: UUID
    tenant_id: str
    level_id: UUID
    channel: DunningChannelEnum
    language: str
    subject: Optional[str] = None
    body: str
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# DUNNING RULE
# ============================================================================


class DunningRuleCreate(BaseModel):
    """Création d'une règle de relance."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: int = Field(100, ge=1)
    conditions: dict = Field(default_factory=dict)
    start_level_id: Optional[UUID] = None
    min_amount: Optional[Decimal] = None
    grace_days: int = Field(0, ge=0)
    exclude_weekends: bool = True
    exclude_holidays: bool = True
    auto_send: bool = True
    require_approval: bool = False
    is_default: bool = False


class DunningRuleUpdate(BaseModel):
    """Mise à jour d'une règle."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1)
    conditions: Optional[dict] = None
    start_level_id: Optional[UUID] = None
    min_amount: Optional[Decimal] = None
    grace_days: Optional[int] = Field(None, ge=0)
    exclude_weekends: Optional[bool] = None
    exclude_holidays: Optional[bool] = None
    auto_send: Optional[bool] = None
    require_approval: Optional[bool] = None
    is_active: Optional[bool] = None


class DunningRuleResponse(BaseModel):
    """Réponse règle de relance."""
    id: UUID
    tenant_id: str
    name: str
    description: Optional[str] = None
    priority: int
    conditions: dict
    start_level_id: Optional[UUID] = None
    min_amount: Optional[Decimal] = None
    grace_days: int
    exclude_weekends: bool
    exclude_holidays: bool
    auto_send: bool
    require_approval: bool
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# DUNNING ACTION
# ============================================================================


class DunningActionCreate(BaseModel):
    """Création manuelle d'une action de relance."""
    invoice_id: str
    invoice_number: str
    customer_id: str
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    level_id: UUID
    channel: DunningChannelEnum
    amount_due: Decimal
    due_date: date
    scheduled_at: Optional[datetime] = None
    internal_notes: Optional[str] = None


class DunningActionResponse(BaseModel):
    """Réponse action de relance."""
    id: UUID
    tenant_id: str
    invoice_id: str
    invoice_number: str
    customer_id: str
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    level_id: UUID
    channel: DunningChannelEnum
    campaign_id: Optional[UUID] = None
    amount_due: Decimal
    fees_applied: Decimal
    interest_applied: Decimal
    total_due: Decimal
    due_date: date
    days_overdue: int
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    status: DunningStatusEnum
    error_message: Optional[str] = None
    subject: Optional[str] = None
    payment_received: bool
    payment_amount: Optional[Decimal] = None
    payment_date: Optional[date] = None
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    internal_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DunningActionListResponse(BaseModel):
    """Liste paginée d'actions de relance."""
    items: list[DunningActionResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# DUNNING CAMPAIGN
# ============================================================================


class DunningCampaignCreate(BaseModel):
    """Création d'une campagne de relance."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    level_id: UUID
    scheduled_at: Optional[datetime] = None


class DunningCampaignResponse(BaseModel):
    """Réponse campagne de relance."""
    id: UUID
    tenant_id: str
    name: str
    description: Optional[str] = None
    level_id: UUID
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: CampaignStatusEnum
    total_invoices: int
    total_amount: Decimal
    sent_count: int
    delivered_count: int
    failed_count: int
    paid_count: int
    paid_amount: Decimal
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# PAYMENT PROMISE
# ============================================================================


class PaymentPromiseCreate(BaseModel):
    """Enregistrer une promesse de paiement."""
    invoice_id: str
    customer_id: str
    dunning_action_id: Optional[UUID] = None
    promised_amount: Decimal = Field(..., gt=0)
    promised_date: date
    contact_name: Optional[str] = None
    contact_method: Optional[str] = None
    notes: Optional[str] = None


class PaymentPromiseUpdate(BaseModel):
    """Mise à jour d'une promesse."""
    status: Optional[PaymentPromiseStatusEnum] = None
    actual_amount: Optional[Decimal] = None
    actual_date: Optional[date] = None
    notes: Optional[str] = None


class PaymentPromiseResponse(BaseModel):
    """Réponse promesse de paiement."""
    id: UUID
    tenant_id: str
    invoice_id: str
    customer_id: str
    dunning_action_id: Optional[UUID] = None
    promised_amount: Decimal
    promised_date: date
    status: PaymentPromiseStatusEnum
    actual_amount: Optional[Decimal] = None
    actual_date: Optional[date] = None
    contact_name: Optional[str] = None
    contact_method: Optional[str] = None
    notes: Optional[str] = None
    recorded_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# CUSTOMER DUNNING PROFILE
# ============================================================================


class CustomerDunningProfileCreate(BaseModel):
    """Créer un profil de relance client."""
    customer_id: str
    customer_name: str
    segment: Optional[str] = None
    dunning_blocked: bool = False
    block_reason: Optional[str] = None
    custom_grace_days: Optional[int] = None
    custom_min_amount: Optional[Decimal] = None
    preferred_channel: Optional[DunningChannelEnum] = None
    preferred_language: str = "fr"
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    notes: Optional[str] = None


class CustomerDunningProfileUpdate(BaseModel):
    """Mise à jour profil client."""
    segment: Optional[str] = None
    dunning_blocked: Optional[bool] = None
    block_reason: Optional[str] = None
    custom_grace_days: Optional[int] = None
    custom_min_amount: Optional[Decimal] = None
    preferred_channel: Optional[DunningChannelEnum] = None
    preferred_language: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    notes: Optional[str] = None


class CustomerDunningProfileResponse(BaseModel):
    """Réponse profil client."""
    id: UUID
    tenant_id: str
    customer_id: str
    customer_name: str
    segment: Optional[str] = None
    dunning_blocked: bool
    block_reason: Optional[str] = None
    custom_grace_days: Optional[int] = None
    custom_min_amount: Optional[Decimal] = None
    preferred_channel: Optional[DunningChannelEnum] = None
    preferred_language: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    total_overdue_count: int
    total_overdue_amount: Decimal
    avg_days_to_pay: Optional[int] = None
    last_dunning_date: Optional[date] = None
    last_payment_date: Optional[date] = None
    risk_score: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# ANALYSIS / REPORTS
# ============================================================================


class OverdueInvoice(BaseModel):
    """Facture en retard de paiement."""
    invoice_id: str
    invoice_number: str
    customer_id: str
    customer_name: str
    customer_email: Optional[str] = None
    amount_due: Decimal
    due_date: date
    days_overdue: int
    current_level: Optional[str] = None
    last_dunning_date: Optional[datetime] = None
    dunning_count: int = 0
    has_promise: bool = False


class OverdueAnalysis(BaseModel):
    """Analyse des impayés."""
    total_invoices: int
    total_amount: Decimal
    by_aging: dict[str, dict]  # {"0-30": {"count": 10, "amount": 5000}, ...}
    by_customer: list[dict]
    by_level: dict[str, dict]


class DunningStatistics(BaseModel):
    """Statistiques globales des relances."""
    total_actions: int
    sent_count: int
    delivered_count: int
    failed_count: int
    delivery_rate: float
    total_amount_relanced: Decimal
    total_amount_recovered: Decimal
    recovery_rate: float
    avg_days_to_pay_after_dunning: Optional[float] = None
    by_level: dict[str, dict]
    by_channel: dict[str, dict]


# ============================================================================
# BULK OPERATIONS
# ============================================================================


class BulkDunningRequest(BaseModel):
    """Demande de relance en masse."""
    level_id: UUID
    invoice_ids: Optional[list[str]] = None  # Si None, toutes les factures éligibles
    min_amount: Optional[Decimal] = None
    min_days_overdue: Optional[int] = None
    max_days_overdue: Optional[int] = None
    customer_segments: Optional[list[str]] = None
    exclude_customer_ids: Optional[list[str]] = None
    schedule_at: Optional[datetime] = None  # Si None, envoi immédiat


class BulkDunningResponse(BaseModel):
    """Résultat d'une relance en masse."""
    campaign_id: UUID
    total_invoices: int
    total_amount: Decimal
    scheduled_at: Optional[datetime] = None
    status: CampaignStatusEnum


# ============================================================================
# DEFAULT TEMPLATES
# ============================================================================

DEFAULT_TEMPLATES = {
    "REMINDER": {
        "fr": {
            "EMAIL": {
                "subject": "Rappel de paiement - Facture {invoice_number}",
                "body": """Bonjour {customer_name},

Nous souhaitons vous rappeler que la facture {invoice_number} d'un montant de {amount_due} EUR est arrivée à échéance le {due_date}.

Nous vous remercions de bien vouloir procéder au règlement dans les meilleurs délais.

Si vous avez déjà effectué ce règlement, nous vous prions de ne pas tenir compte de ce message.

Cordialement,
{company_name}""",
            },
            "SMS": {
                "body": "Rappel: Facture {invoice_number} de {amount_due} EUR échue le {due_date}. Merci de régulariser. {company_name}",
            },
        },
    },
    "FIRST_NOTICE": {
        "fr": {
            "EMAIL": {
                "subject": "1ère relance - Facture {invoice_number} impayée",
                "body": """Bonjour {customer_name},

Sauf erreur de notre part, la facture {invoice_number} d'un montant de {amount_due} EUR reste impayée à ce jour, soit {days_overdue} jours après l'échéance du {due_date}.

Nous vous serions reconnaissants de bien vouloir régulariser cette situation dans les plus brefs délais.

En cas de difficultés de paiement, n'hésitez pas à nous contacter pour convenir d'un arrangement.

Cordialement,
{company_name}""",
            },
        },
    },
    "FORMAL_NOTICE": {
        "fr": {
            "EMAIL": {
                "subject": "MISE EN DEMEURE - Facture {invoice_number}",
                "body": """Madame, Monsieur,

Malgré nos précédentes relances, la facture {invoice_number} d'un montant de {amount_due} EUR reste impayée.

Conformément à l'article L441-10 du Code de commerce, nous vous informons que des pénalités de retard et une indemnité forfaitaire de recouvrement de 40 EUR sont désormais applicables.

Montant principal : {amount_due} EUR
Pénalités de retard : {interest_amount} EUR
Indemnité de recouvrement : 40,00 EUR
TOTAL DÛ : {total_due} EUR

Nous vous mettons en demeure de procéder au paiement intégral sous 8 jours.

À défaut, nous serons contraints d'engager une procédure de recouvrement judiciaire sans autre avis.

{company_name}""",
            },
        },
    },
}
