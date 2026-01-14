"""
AZALS MODULE 13 - Point de Vente (POS)
=======================================
Modèles SQLAlchemy pour le système de caisse.

Benchmark: Square, Lightspeed, Shopify POS, Toast
Target: POS enterprise intégré ERP avec mode offline
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.types import JSON, UniversalUUID
from app.db import Base

# ============================================================================
# ENUMS
# ============================================================================

class POSTerminalStatus(str, enum.Enum):
    """Statuts terminal."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    IN_USE = "IN_USE"


class POSSessionStatus(str, enum.Enum):
    """Statuts session caisse."""
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    SUSPENDED = "SUSPENDED"


class POSTransactionStatus(str, enum.Enum):
    """Statuts transaction."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    VOIDED = "VOIDED"


class PaymentMethodType(str, enum.Enum):
    """Types de paiement."""
    CASH = "CASH"
    CARD = "CARD"
    CHECK = "CHECK"
    GIFT_CARD = "GIFT_CARD"
    STORE_CREDIT = "STORE_CREDIT"
    MOBILE_PAYMENT = "MOBILE_PAYMENT"
    VOUCHER = "VOUCHER"
    SPLIT = "SPLIT"
    OTHER = "OTHER"


class DiscountType(str, enum.Enum):
    """Types de remise."""
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"
    ITEM_FREE = "ITEM_FREE"


# ============================================================================
# MODÈLES CONFIGURATION
# ============================================================================

class POSStore(Base):
    """Point de vente / Magasin."""
    __tablename__ = "pos_stores"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Informations
    code: Mapped[str | None] = mapped_column(String(20), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Adresse
    address_line1: Mapped[str | None] = mapped_column(String(255))
    address_line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str | None] = mapped_column(String(2), default="FR")
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))

    # Configuration
    timezone: Mapped[str | None] = mapped_column(String(50), default="Europe/Paris")
    currency: Mapped[str | None] = mapped_column(String(3), default="EUR")
    default_tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=20.00)

    # Horaires
    opening_hours: Mapped[dict | None] = mapped_column(JSON)  # {"mon": {"open": "09:00", "close": "19:00"}, ...}

    # Paramètres
    settings: Mapped[dict | None] = mapped_column(JSON)  # Options diverses

    # Statut
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_store_code', 'tenant_id', 'code', unique=True),
    )


class POSTerminal(Base):
    """Terminal de caisse."""
    __tablename__ = "pos_terminals"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    store_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_stores.id"), nullable=False)

    # Identification
    terminal_id: Mapped[str | None] = mapped_column(String(50), nullable=False)  # Identifiant unique du terminal
    name: Mapped[str | None] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Hardware
    device_type: Mapped[str | None] = mapped_column(String(50))  # ipad, android, desktop, dedicated
    device_id: Mapped[str | None] = mapped_column(String(255))  # Identifiant hardware unique
    printer_ip: Mapped[str | None] = mapped_column(String(50))
    drawer_ip: Mapped[str | None] = mapped_column(String(50))

    # Statut
    status: Mapped[str | None] = mapped_column(Enum(POSTerminalStatus), default=POSTerminalStatus.INACTIVE)
    last_ping: Mapped[datetime | None] = mapped_column(DateTime)
    last_sync: Mapped[datetime | None] = mapped_column(DateTime)

    # Session courante
    current_session_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    # Configuration
    settings: Mapped[dict | None] = mapped_column(JSON)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_terminal_id', 'tenant_id', 'terminal_id', unique=True),
        Index('idx_pos_terminal_store', 'tenant_id', 'store_id'),
    )


class POSUser(Base):
    """Utilisateur POS (caissier)."""
    __tablename__ = "pos_users"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Lien utilisateur système
    user_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # FK vers users si applicable

    # Informations
    employee_code: Mapped[str | None] = mapped_column(String(20), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=False)
    pin_code: Mapped[str | None] = mapped_column(String(10))  # Code PIN pour connexion rapide

    # Droits
    can_open_drawer: Mapped[bool | None] = mapped_column(Boolean, default=True)
    can_void_transaction: Mapped[bool | None] = mapped_column(Boolean, default=False)
    can_give_discount: Mapped[bool | None] = mapped_column(Boolean, default=False)
    max_discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=0)
    can_refund: Mapped[bool | None] = mapped_column(Boolean, default=False)
    can_close_session: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_manager: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Magasins autorisés
    allowed_store_ids: Mapped[dict | None] = mapped_column(JSON)  # [1, 2, 3]

    # Statut
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_user_code', 'tenant_id', 'employee_code', unique=True),
    )


# ============================================================================
# MODÈLES SESSION
# ============================================================================

class POSSession(Base):
    """Session de caisse."""
    __tablename__ = "pos_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    terminal_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_terminals.id"), nullable=False)

    # Numéro de session
    session_number: Mapped[str | None] = mapped_column(String(50), nullable=False)

    # Utilisateur
    opened_by_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_users.id"), nullable=False)
    closed_by_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_users.id"))

    # Statut
    status: Mapped[str | None] = mapped_column(Enum(POSSessionStatus), default=POSSessionStatus.OPEN)

    # Fond de caisse
    opening_cash: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    opening_note: Mapped[str | None] = mapped_column(Text)

    # Clôture
    expected_cash: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))  # Calculé
    actual_cash: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))  # Compté
    cash_difference: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))  # Écart
    closing_note: Mapped[str | None] = mapped_column(Text)

    # Totaux calculés
    total_sales: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    total_refunds: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    total_discounts: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    total_tax: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    transaction_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Par mode de paiement
    cash_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    card_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    check_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    voucher_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    other_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)

    # Dates
    opened_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_session_number', 'tenant_id', 'session_number', unique=True),
        Index('idx_pos_session_terminal', 'tenant_id', 'terminal_id'),
        Index('idx_pos_session_date', 'tenant_id', 'opened_at'),
    )


class CashMovement(Base):
    """Mouvement de caisse (entrée/sortie)."""
    __tablename__ = "pos_cash_movements"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_sessions.id"), nullable=False)

    # Type
    movement_type: Mapped[str | None] = mapped_column(String(20), nullable=False)  # IN, OUT

    # Montant
    amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False)

    # Motif
    reason: Mapped[str | None] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Utilisateur
    performed_by_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_users.id"), nullable=False)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_cash_mov_session', 'tenant_id', 'session_id'),
    )


# ============================================================================
# MODÈLES TRANSACTION
# ============================================================================

class POSTransaction(Base):
    """Transaction POS (vente)."""
    __tablename__ = "pos_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_sessions.id"), nullable=False)

    # Numéro de ticket
    receipt_number: Mapped[str | None] = mapped_column(String(50), nullable=False)
    receipt_sequence: Mapped[int] = mapped_column(Integer)

    # Statut
    status: Mapped[str | None] = mapped_column(Enum(POSTransactionStatus), default=POSTransactionStatus.PENDING)

    # Client (optionnel)
    customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # FK vers customers
    customer_name: Mapped[str | None] = mapped_column(String(255))
    customer_email: Mapped[str | None] = mapped_column(String(255))
    customer_phone: Mapped[str | None] = mapped_column(String(50))

    # Vendeur
    cashier_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_users.id"), nullable=False)
    salesperson_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_users.id"))

    # Montants
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    discount_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    tax_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False, default=0)

    # Paiement
    amount_paid: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    amount_due: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    change_given: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)

    # Remise globale
    discount_type: Mapped[str | None] = mapped_column(Enum(DiscountType))
    discount_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    discount_reason: Mapped[str | None] = mapped_column(String(255))

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)
    internal_notes: Mapped[str | None] = mapped_column(Text)

    # Référence
    original_transaction_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # Pour retours/échanges
    ecommerce_order_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # Lien commande web

    # Synchronisation
    is_synced: Mapped[bool | None] = mapped_column(Boolean, default=True)
    offline_id: Mapped[str | None] = mapped_column(String(100))  # ID généré offline

    # Dates
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime)
    voided_by_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_users.id"))
    void_reason: Mapped[str | None] = mapped_column(String(255))

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_trans_receipt', 'tenant_id', 'receipt_number', unique=True),
        Index('idx_pos_trans_session', 'tenant_id', 'session_id'),
        Index('idx_pos_trans_date', 'tenant_id', 'created_at'),
        Index('idx_pos_trans_customer', 'tenant_id', 'customer_id'),
    )


class POSTransactionLine(Base):
    """Ligne de transaction POS."""
    __tablename__ = "pos_transaction_lines"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    transaction_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_transactions.id"), nullable=False)

    # Numéro de ligne
    line_number: Mapped[int | None] = mapped_column(Integer, default=1)

    # Produit
    product_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # FK vers products
    variant_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    sku: Mapped[str | None] = mapped_column(String(100))
    barcode: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str | None] = mapped_column(String(255), nullable=False)

    # Quantité
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 3), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), default="unit")

    # Prix
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False)
    original_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))  # Prix avant remise

    # Remise ligne
    discount_type: Mapped[str | None] = mapped_column(Enum(DiscountType))
    discount_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    discount_reason: Mapped[str | None] = mapped_column(String(255))

    # Taxes
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=20.00)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)

    # Total
    line_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False)

    # Vendeur sur la ligne (si différent)
    salesperson_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_users.id"))

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)

    # Retour
    is_return: Mapped[bool | None] = mapped_column(Boolean, default=False)
    return_reason: Mapped[str | None] = mapped_column(String(255))

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_line_trans', 'tenant_id', 'transaction_id'),
        Index('idx_pos_line_product', 'tenant_id', 'product_id'),
    )


class POSPayment(Base):
    """Paiement sur transaction POS."""
    __tablename__ = "pos_payments"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    transaction_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_transactions.id"), nullable=False)

    # Type de paiement
    payment_method: Mapped[str | None] = mapped_column(Enum(PaymentMethodType), nullable=False)
    payment_method_name: Mapped[str | None] = mapped_column(String(100))  # Détail (ex: "Visa", "Mastercard")

    # Montant
    amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3), default="EUR")

    # Détails carte
    card_type: Mapped[str | None] = mapped_column(String(20))
    card_last4: Mapped[str | None] = mapped_column(String(4))
    card_auth_code: Mapped[str | None] = mapped_column(String(50))
    card_transaction_id: Mapped[str | None] = mapped_column(String(100))

    # Détails chèque
    check_number: Mapped[str | None] = mapped_column(String(50))
    check_bank: Mapped[str | None] = mapped_column(String(100))

    # Détails carte cadeau
    gift_card_number: Mapped[str | None] = mapped_column(String(100))

    # Rendu monnaie (pour espèces)
    amount_tendered: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    change_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))

    # Statut
    status: Mapped[str | None] = mapped_column(String(20), default="COMPLETED")  # COMPLETED, PENDING, FAILED, REFUNDED
    error_message: Mapped[str | None] = mapped_column(Text)

    # Référence externe
    external_id: Mapped[str | None] = mapped_column(String(255))

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_payment_trans', 'tenant_id', 'transaction_id'),
    )


# ============================================================================
# MODÈLES RAPPORT
# ============================================================================

class POSDailyReport(Base):
    """Rapport journalier (Z-Report)."""
    __tablename__ = "pos_daily_reports"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    store_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_stores.id"), nullable=False)

    # Date
    report_date: Mapped[datetime] = mapped_column(DateTime)
    report_number: Mapped[str | None] = mapped_column(String(50), nullable=False)

    # Périodes
    first_transaction_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_transaction_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Totaux
    gross_sales: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    net_sales: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    total_discounts: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    total_refunds: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    total_tax: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)

    # Transactions
    transaction_count: Mapped[int | None] = mapped_column(Integer, default=0)
    items_sold: Mapped[int | None] = mapped_column(Integer, default=0)
    average_transaction: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)

    # Par mode de paiement
    cash_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    card_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    check_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    other_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)

    # Caisse
    opening_cash: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    closing_cash: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    cash_movements_in: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    cash_movements_out: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)

    # Écarts
    expected_cash: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    actual_cash: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    cash_variance: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)

    # Détails par TVA
    tax_breakdown: Mapped[dict | None] = mapped_column(JSON)  # {"20": {"base": 1000, "tax": 200}, "5.5": {...}}

    # Détails par catégorie
    category_breakdown: Mapped[dict | None] = mapped_column(JSON)

    # Sessions incluses
    session_ids: Mapped[dict | None] = mapped_column(JSON)

    # Généré par
    generated_by_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_users.id"))
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_report_date', 'tenant_id', 'store_id', 'report_date', unique=True),
    )


# ============================================================================
# MODÈLES PRODUIT POS
# ============================================================================

class POSProductQuickKey(Base):
    """Raccourci clavier produit (favorites)."""
    __tablename__ = "pos_quick_keys"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    store_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_stores.id"))

    # Position
    page: Mapped[int | None] = mapped_column(Integer, default=1)
    position: Mapped[int] = mapped_column(Integer)  # 1-20 par page

    # Produit
    product_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    variant_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    # Affichage
    label: Mapped[str | None] = mapped_column(String(50))
    color: Mapped[str | None] = mapped_column(String(20), default="#1976D2")
    icon: Mapped[str | None] = mapped_column(String(50))
    image_url: Mapped[str | None] = mapped_column(String(500))

    # Prix personnalisé (optionnel)
    custom_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_quickkey_pos', 'tenant_id', 'store_id', 'page', 'position', unique=True),
    )


class POSHoldTransaction(Base):
    """Transaction en attente."""
    __tablename__ = "pos_hold_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_sessions.id"), nullable=False)

    # Identification
    hold_number: Mapped[str | None] = mapped_column(String(50), nullable=False)
    hold_name: Mapped[str | None] = mapped_column(String(100))  # Nom du client ou référence

    # Données
    transaction_data: Mapped[dict] = mapped_column(JSON)  # Snapshot complet

    # Client
    customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    customer_name: Mapped[str | None] = mapped_column(String(255))

    # Utilisateur
    held_by_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_users.id"), nullable=False)

    # État
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)

    # Expiration
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_hold_session', 'tenant_id', 'session_id'),
    )


# ============================================================================
# MODÈLES SYNCHRONISATION OFFLINE
# ============================================================================

class POSOfflineQueue(Base):
    """File d'attente synchronisation offline."""
    __tablename__ = "pos_offline_queue"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    terminal_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("pos_terminals.id"), nullable=False)

    # Type d'opération
    operation_type: Mapped[str | None] = mapped_column(String(50))  # TRANSACTION, PAYMENT, CASH_MOVEMENT

    # Données
    transaction_data: Mapped[dict] = mapped_column(JSON)
    offline_id: Mapped[str | None] = mapped_column(String(100))

    # Statut sync
    is_synced: Mapped[bool | None] = mapped_column(Boolean, default=False)
    sync_attempts: Mapped[int | None] = mapped_column(Integer, default=0)
    sync_error: Mapped[str | None] = mapped_column(Text)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_offline_synced', 'tenant_id', 'is_synced'),
    )
