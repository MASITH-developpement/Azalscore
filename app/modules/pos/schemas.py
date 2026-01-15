"""
AZALS MODULE 13 - POS Schemas
==============================
Schémas Pydantic pour validation et sérialisation.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from .models import DiscountType, PaymentMethodType, POSSessionStatus, POSTerminalStatus, POSTransactionStatus

# ============================================================================
# STORE SCHEMAS
# ============================================================================

class StoreBase(BaseModel):
    """Base magasin."""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str = "FR"
    phone: str | None = None
    email: str | None = None
    timezone: str = "Europe/Paris"
    currency: str = "EUR"
    default_tax_rate: Decimal = Decimal("20.00")
    opening_hours: dict | None = None
    is_active: bool = True


class StoreCreate(StoreBase):
    """Création magasin."""
    pass


class StoreUpdate(BaseModel):
    """Mise à jour magasin."""
    name: str | None = None
    description: str | None = None
    address_line1: str | None = None
    city: str | None = None
    postal_code: str | None = None
    phone: str | None = None
    email: str | None = None
    opening_hours: dict | None = None
    is_active: bool | None = None


class StoreResponse(StoreBase):
    """Réponse magasin."""
    id: int
    tenant_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


# ============================================================================
# TERMINAL SCHEMAS
# ============================================================================

class TerminalBase(BaseModel):
    """Base terminal."""
    terminal_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    device_type: str | None = None
    device_id: str | None = None
    printer_ip: str | None = None
    drawer_ip: str | None = None


class TerminalCreate(TerminalBase):
    """Création terminal."""
    store_id: int


class TerminalUpdate(BaseModel):
    """Mise à jour terminal."""
    name: str | None = None
    description: str | None = None
    device_type: str | None = None
    printer_ip: str | None = None
    drawer_ip: str | None = None
    status: POSTerminalStatus | None = None


class TerminalResponse(TerminalBase):
    """Réponse terminal."""
    id: int
    tenant_id: str
    store_id: int
    status: POSTerminalStatus
    last_ping: datetime.datetime | None = None
    last_sync: datetime.datetime | None = None
    current_session_id: int | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ============================================================================
# POS USER SCHEMAS
# ============================================================================

class POSUserBase(BaseModel):
    """Base utilisateur POS."""
    employee_code: str = Field(..., min_length=1, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    pin_code: str | None = None
    can_open_drawer: bool = True
    can_void_transaction: bool = False
    can_give_discount: bool = False
    max_discount_percent: Decimal = Decimal("0")
    can_refund: bool = False
    can_close_session: bool = False
    is_manager: bool = False
    allowed_store_ids: list[int] | None = None


class POSUserCreate(POSUserBase):
    """Création utilisateur POS."""
    user_id: int | None = None


class POSUserUpdate(BaseModel):
    """Mise à jour utilisateur POS."""
    first_name: str | None = None
    last_name: str | None = None
    pin_code: str | None = None
    can_open_drawer: bool | None = None
    can_void_transaction: bool | None = None
    can_give_discount: bool | None = None
    max_discount_percent: Decimal | None = None
    can_refund: bool | None = None
    can_close_session: bool | None = None
    is_manager: bool | None = None
    allowed_store_ids: list[int] | None = None
    is_active: bool | None = None


class POSUserResponse(POSUserBase):
    """Réponse utilisateur POS."""
    id: int
    tenant_id: str
    user_id: int | None = None
    is_active: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class POSUserLogin(BaseModel):
    """Login utilisateur POS."""
    employee_code: str
    pin_code: str | None = None


# ============================================================================
# SESSION SCHEMAS
# ============================================================================

class SessionOpenRequest(BaseModel):
    """Ouverture de session."""
    terminal_id: int
    cashier_id: int
    opening_cash: Decimal = Field(..., ge=0)
    opening_note: str | None = None


class SessionCloseRequest(BaseModel):
    """Fermeture de session."""
    actual_cash: Decimal = Field(..., ge=0)
    closing_note: str | None = None


class SessionResponse(BaseModel):
    """Réponse session."""
    id: int
    tenant_id: str
    terminal_id: int
    session_number: str
    status: POSSessionStatus
    opened_by_id: int
    closed_by_id: int | None = None
    opening_cash: Decimal
    expected_cash: Decimal | None = None
    actual_cash: Decimal | None = None
    cash_difference: Decimal | None = None
    total_sales: Decimal
    total_refunds: Decimal
    total_discounts: Decimal
    transaction_count: int
    cash_total: Decimal
    card_total: Decimal
    check_total: Decimal
    opened_at: datetime.datetime
    closed_at: datetime.datetime | None = None

    model_config = {"from_attributes": True}


class CashMovementCreate(BaseModel):
    """Mouvement de caisse."""
    movement_type: str = Field(..., pattern="^(IN|OUT)$")
    amount: Decimal = Field(..., gt=0)
    reason: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class CashMovementResponse(BaseModel):
    """Réponse mouvement caisse."""
    id: int
    session_id: int
    movement_type: str
    amount: Decimal
    reason: str
    description: str | None = None
    performed_by_id: int
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ============================================================================
# TRANSACTION SCHEMAS
# ============================================================================

class TransactionLineCreate(BaseModel):
    """Création ligne transaction."""
    product_id: int | None = None
    variant_id: int | None = None
    sku: str | None = None
    barcode: str | None = None
    name: str = Field(..., min_length=1, max_length=255)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = None
    discount_reason: str | None = None
    tax_rate: Decimal = Decimal("20.00")
    salesperson_id: int | None = None
    notes: str | None = None
    is_return: bool = False
    return_reason: str | None = None


class TransactionLineResponse(BaseModel):
    """Réponse ligne transaction."""
    id: int
    product_id: int | None = None
    variant_id: int | None = None
    sku: str | None = None
    name: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal
    is_return: bool

    model_config = {"from_attributes": True}


class PaymentCreate(BaseModel):
    """Création paiement."""
    payment_method: PaymentMethodType
    amount: Decimal = Field(..., gt=0)
    amount_tendered: Decimal | None = None  # Pour espèces
    card_type: str | None = None
    card_last4: str | None = None
    card_auth_code: str | None = None
    check_number: str | None = None
    check_bank: str | None = None
    gift_card_number: str | None = None


class PaymentResponse(BaseModel):
    """Réponse paiement."""
    id: int
    payment_method: PaymentMethodType
    amount: Decimal
    amount_tendered: Decimal | None = None
    change_amount: Decimal | None = None
    card_type: str | None = None
    card_last4: str | None = None
    status: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    """Création transaction."""
    customer_id: int | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    salesperson_id: int | None = None
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = None
    discount_reason: str | None = None
    notes: str | None = None
    lines: list[TransactionLineCreate]
    payments: list[PaymentCreate] | None = None


class TransactionResponse(BaseModel):
    """Réponse transaction."""
    id: int
    tenant_id: str
    session_id: int
    receipt_number: str
    status: POSTransactionStatus
    customer_id: int | None = None
    customer_name: str | None = None
    cashier_id: int
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    change_given: Decimal
    lines: list[TransactionLineResponse] = []
    payments: list[PaymentResponse] = []
    completed_at: datetime.datetime | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """Liste transactions."""
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# QUICK KEY SCHEMAS
# ============================================================================

class QuickKeyCreate(BaseModel):
    """Création raccourci."""
    store_id: int | None = None
    page: int = 1
    position: int = Field(..., ge=1, le=20)
    product_id: int | None = None
    variant_id: int | None = None
    label: str | None = None
    color: str = "#1976D2"
    icon: str | None = None
    image_url: str | None = None
    custom_price: Decimal | None = None


class QuickKeyResponse(BaseModel):
    """Réponse raccourci."""
    id: int
    page: int
    position: int
    product_id: int | None = None
    label: str | None = None
    color: str
    icon: str | None = None
    image_url: str | None = None
    custom_price: Decimal | None = None

    model_config = {"from_attributes": True}


# ============================================================================
# HOLD TRANSACTION SCHEMAS
# ============================================================================

class HoldTransactionCreate(BaseModel):
    """Mise en attente transaction."""
    hold_name: str | None = None
    customer_id: int | None = None
    customer_name: str | None = None
    transaction_data: dict


class HoldTransactionResponse(BaseModel):
    """Réponse transaction en attente."""
    id: int
    hold_number: str
    hold_name: str | None = None
    customer_name: str | None = None
    transaction_data: dict
    held_by_id: int
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ============================================================================
# REPORT SCHEMAS
# ============================================================================

class DailyReportResponse(BaseModel):
    """Réponse rapport journalier."""
    id: int
    store_id: int
    report_date: datetime.datetime
    report_number: str
    gross_sales: Decimal
    net_sales: Decimal
    total_discounts: Decimal
    total_refunds: Decimal
    total_tax: Decimal
    transaction_count: int
    items_sold: int
    average_transaction: Decimal
    cash_total: Decimal
    card_total: Decimal
    check_total: Decimal
    opening_cash: Decimal
    closing_cash: Decimal
    cash_variance: Decimal
    tax_breakdown: dict | None = None
    generated_at: datetime.datetime

    model_config = {"from_attributes": True}


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class POSDashboard(BaseModel):
    """Dashboard POS."""
    # Aujourd'hui
    sales_today: Decimal
    transactions_today: int
    average_transaction_today: Decimal
    items_sold_today: int

    # Sessions actives
    active_sessions: int
    active_terminals: int

    # Par mode de paiement
    cash_today: Decimal
    card_today: Decimal
    other_today: Decimal

    # Top produits
    top_products: list[dict]

    # Dernières transactions
    recent_transactions: list[dict]


class TerminalDashboard(BaseModel):
    """Dashboard terminal."""
    terminal_id: int
    terminal_name: str
    session_status: POSSessionStatus | None = None
    session_id: int | None = None
    cashier_name: str | None = None
    sales_this_session: Decimal
    transactions_this_session: int
    last_transaction: dict | None = None
