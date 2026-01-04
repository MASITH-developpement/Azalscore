"""
AZALS MODULE 13 - POS Schemas
==============================
Schémas Pydantic pour validation et sérialisation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field

from .models import (
    POSTerminalStatus, POSSessionStatus, POSTransactionStatus,
    PaymentMethodType, DiscountType
)


# ============================================================================
# STORE SCHEMAS
# ============================================================================

class StoreBase(BaseModel):
    """Base magasin."""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "FR"
    phone: Optional[str] = None
    email: Optional[str] = None
    timezone: str = "Europe/Paris"
    currency: str = "EUR"
    default_tax_rate: Decimal = Decimal("20.00")
    opening_hours: Optional[dict] = None
    is_active: bool = True


class StoreCreate(StoreBase):
    """Création magasin."""
    pass


class StoreUpdate(BaseModel):
    """Mise à jour magasin."""
    name: Optional[str] = None
    description: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    opening_hours: Optional[dict] = None
    is_active: Optional[bool] = None


class StoreResponse(StoreBase):
    """Réponse magasin."""
    id: int
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# TERMINAL SCHEMAS
# ============================================================================

class TerminalBase(BaseModel):
    """Base terminal."""
    terminal_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    device_type: Optional[str] = None
    device_id: Optional[str] = None
    printer_ip: Optional[str] = None
    drawer_ip: Optional[str] = None


class TerminalCreate(TerminalBase):
    """Création terminal."""
    store_id: int


class TerminalUpdate(BaseModel):
    """Mise à jour terminal."""
    name: Optional[str] = None
    description: Optional[str] = None
    device_type: Optional[str] = None
    printer_ip: Optional[str] = None
    drawer_ip: Optional[str] = None
    status: Optional[POSTerminalStatus] = None


class TerminalResponse(TerminalBase):
    """Réponse terminal."""
    id: int
    tenant_id: str
    store_id: int
    status: POSTerminalStatus
    last_ping: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    current_session_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# POS USER SCHEMAS
# ============================================================================

class POSUserBase(BaseModel):
    """Base utilisateur POS."""
    employee_code: str = Field(..., min_length=1, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    pin_code: Optional[str] = None
    can_open_drawer: bool = True
    can_void_transaction: bool = False
    can_give_discount: bool = False
    max_discount_percent: Decimal = Decimal("0")
    can_refund: bool = False
    can_close_session: bool = False
    is_manager: bool = False
    allowed_store_ids: Optional[List[int]] = None


class POSUserCreate(POSUserBase):
    """Création utilisateur POS."""
    user_id: Optional[int] = None


class POSUserUpdate(BaseModel):
    """Mise à jour utilisateur POS."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    pin_code: Optional[str] = None
    can_open_drawer: Optional[bool] = None
    can_void_transaction: Optional[bool] = None
    can_give_discount: Optional[bool] = None
    max_discount_percent: Optional[Decimal] = None
    can_refund: Optional[bool] = None
    can_close_session: Optional[bool] = None
    is_manager: Optional[bool] = None
    allowed_store_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None


class POSUserResponse(POSUserBase):
    """Réponse utilisateur POS."""
    id: int
    tenant_id: str
    user_id: Optional[int] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class POSUserLogin(BaseModel):
    """Login utilisateur POS."""
    employee_code: str
    pin_code: Optional[str] = None


# ============================================================================
# SESSION SCHEMAS
# ============================================================================

class SessionOpenRequest(BaseModel):
    """Ouverture de session."""
    terminal_id: int
    cashier_id: int
    opening_cash: Decimal = Field(..., ge=0)
    opening_note: Optional[str] = None


class SessionCloseRequest(BaseModel):
    """Fermeture de session."""
    actual_cash: Decimal = Field(..., ge=0)
    closing_note: Optional[str] = None


class SessionResponse(BaseModel):
    """Réponse session."""
    id: int
    tenant_id: str
    terminal_id: int
    session_number: str
    status: POSSessionStatus
    opened_by_id: int
    closed_by_id: Optional[int] = None
    opening_cash: Decimal
    expected_cash: Optional[Decimal] = None
    actual_cash: Optional[Decimal] = None
    cash_difference: Optional[Decimal] = None
    total_sales: Decimal
    total_refunds: Decimal
    total_discounts: Decimal
    transaction_count: int
    cash_total: Decimal
    card_total: Decimal
    check_total: Decimal
    opened_at: datetime
    closed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CashMovementCreate(BaseModel):
    """Mouvement de caisse."""
    movement_type: str = Field(..., pattern="^(IN|OUT)$")
    amount: Decimal = Field(..., gt=0)
    reason: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CashMovementResponse(BaseModel):
    """Réponse mouvement caisse."""
    id: int
    session_id: int
    movement_type: str
    amount: Decimal
    reason: str
    description: Optional[str] = None
    performed_by_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# TRANSACTION SCHEMAS
# ============================================================================

class TransactionLineCreate(BaseModel):
    """Création ligne transaction."""
    product_id: Optional[int] = None
    variant_id: Optional[int] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[Decimal] = None
    discount_reason: Optional[str] = None
    tax_rate: Decimal = Decimal("20.00")
    salesperson_id: Optional[int] = None
    notes: Optional[str] = None
    is_return: bool = False
    return_reason: Optional[str] = None


class TransactionLineResponse(BaseModel):
    """Réponse ligne transaction."""
    id: int
    product_id: Optional[int] = None
    variant_id: Optional[int] = None
    sku: Optional[str] = None
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
    amount_tendered: Optional[Decimal] = None  # Pour espèces
    card_type: Optional[str] = None
    card_last4: Optional[str] = None
    card_auth_code: Optional[str] = None
    check_number: Optional[str] = None
    check_bank: Optional[str] = None
    gift_card_number: Optional[str] = None


class PaymentResponse(BaseModel):
    """Réponse paiement."""
    id: int
    payment_method: PaymentMethodType
    amount: Decimal
    amount_tendered: Optional[Decimal] = None
    change_amount: Optional[Decimal] = None
    card_type: Optional[str] = None
    card_last4: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    """Création transaction."""
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    salesperson_id: Optional[int] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[Decimal] = None
    discount_reason: Optional[str] = None
    notes: Optional[str] = None
    lines: List[TransactionLineCreate]
    payments: Optional[List[PaymentCreate]] = None


class TransactionResponse(BaseModel):
    """Réponse transaction."""
    id: int
    tenant_id: str
    session_id: int
    receipt_number: str
    status: POSTransactionStatus
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    cashier_id: int
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    change_given: Decimal
    lines: List[TransactionLineResponse] = []
    payments: List[PaymentResponse] = []
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """Liste transactions."""
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# QUICK KEY SCHEMAS
# ============================================================================

class QuickKeyCreate(BaseModel):
    """Création raccourci."""
    store_id: Optional[int] = None
    page: int = 1
    position: int = Field(..., ge=1, le=20)
    product_id: Optional[int] = None
    variant_id: Optional[int] = None
    label: Optional[str] = None
    color: str = "#1976D2"
    icon: Optional[str] = None
    image_url: Optional[str] = None
    custom_price: Optional[Decimal] = None


class QuickKeyResponse(BaseModel):
    """Réponse raccourci."""
    id: int
    page: int
    position: int
    product_id: Optional[int] = None
    label: Optional[str] = None
    color: str
    icon: Optional[str] = None
    image_url: Optional[str] = None
    custom_price: Optional[Decimal] = None

    model_config = {"from_attributes": True}


# ============================================================================
# HOLD TRANSACTION SCHEMAS
# ============================================================================

class HoldTransactionCreate(BaseModel):
    """Mise en attente transaction."""
    hold_name: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    transaction_data: dict


class HoldTransactionResponse(BaseModel):
    """Réponse transaction en attente."""
    id: int
    hold_number: str
    hold_name: Optional[str] = None
    customer_name: Optional[str] = None
    transaction_data: dict
    held_by_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# REPORT SCHEMAS
# ============================================================================

class DailyReportResponse(BaseModel):
    """Réponse rapport journalier."""
    id: int
    store_id: int
    report_date: datetime
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
    tax_breakdown: Optional[dict] = None
    generated_at: datetime

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
    top_products: List[dict]

    # Dernières transactions
    recent_transactions: List[dict]


class TerminalDashboard(BaseModel):
    """Dashboard terminal."""
    terminal_id: int
    terminal_name: str
    session_status: Optional[POSSessionStatus] = None
    session_id: Optional[int] = None
    cashier_name: Optional[str] = None
    sales_this_session: Decimal
    transactions_this_session: int
    last_transaction: Optional[dict] = None
