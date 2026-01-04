"""
AZALS MODULE 13 - Point de Vente (POS)
=======================================
Modèles SQLAlchemy pour le système de caisse.

Benchmark: Square, Lightspeed, Shopify POS, Toast
Target: POS enterprise intégré ERP avec mode offline
"""

import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Enum, JSON, Float, Numeric, Index, BigInteger
)
from sqlalchemy.orm import relationship
from app.core.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class POSTerminalStatus(str, enum.Enum):
    """Statuts terminal."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"


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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Informations
    code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Adresse
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(2), default="FR")
    phone = Column(String(50))
    email = Column(String(255))

    # Configuration
    timezone = Column(String(50), default="Europe/Paris")
    currency = Column(String(3), default="EUR")
    default_tax_rate = Column(Numeric(5, 2), default=20.00)

    # Horaires
    opening_hours = Column(JSON)  # {"mon": {"open": "09:00", "close": "19:00"}, ...}

    # Paramètres
    settings = Column(JSON)  # Options diverses

    # Statut
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_store_code', 'tenant_id', 'code', unique=True),
    )


class POSTerminal(Base):
    """Terminal de caisse."""
    __tablename__ = "pos_terminals"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("pos_stores.id"), nullable=False)

    # Identification
    terminal_id = Column(String(50), nullable=False)  # Identifiant unique du terminal
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Hardware
    device_type = Column(String(50))  # ipad, android, desktop, dedicated
    device_id = Column(String(255))  # Identifiant hardware unique
    printer_ip = Column(String(50))
    drawer_ip = Column(String(50))

    # Statut
    status = Column(Enum(POSTerminalStatus), default=POSTerminalStatus.INACTIVE)
    last_ping = Column(DateTime)
    last_sync = Column(DateTime)

    # Session courante
    current_session_id = Column(Integer)

    # Configuration
    settings = Column(JSON)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_terminal_id', 'tenant_id', 'terminal_id', unique=True),
        Index('idx_pos_terminal_store', 'tenant_id', 'store_id'),
    )


class POSUser(Base):
    """Utilisateur POS (caissier)."""
    __tablename__ = "pos_users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Lien utilisateur système
    user_id = Column(Integer)  # FK vers users si applicable

    # Informations
    employee_code = Column(String(20), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    pin_code = Column(String(10))  # Code PIN pour connexion rapide

    # Droits
    can_open_drawer = Column(Boolean, default=True)
    can_void_transaction = Column(Boolean, default=False)
    can_give_discount = Column(Boolean, default=False)
    max_discount_percent = Column(Numeric(5, 2), default=0)
    can_refund = Column(Boolean, default=False)
    can_close_session = Column(Boolean, default=False)
    is_manager = Column(Boolean, default=False)

    # Magasins autorisés
    allowed_store_ids = Column(JSON)  # [1, 2, 3]

    # Statut
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_user_code', 'tenant_id', 'employee_code', unique=True),
    )


# ============================================================================
# MODÈLES SESSION
# ============================================================================

class POSSession(Base):
    """Session de caisse."""
    __tablename__ = "pos_sessions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    terminal_id = Column(Integer, ForeignKey("pos_terminals.id"), nullable=False)

    # Numéro de session
    session_number = Column(String(50), nullable=False)

    # Utilisateur
    opened_by_id = Column(Integer, ForeignKey("pos_users.id"), nullable=False)
    closed_by_id = Column(Integer, ForeignKey("pos_users.id"))

    # Statut
    status = Column(Enum(POSSessionStatus), default=POSSessionStatus.OPEN)

    # Fond de caisse
    opening_cash = Column(Numeric(15, 2), nullable=False, default=0)
    opening_note = Column(Text)

    # Clôture
    expected_cash = Column(Numeric(15, 2))  # Calculé
    actual_cash = Column(Numeric(15, 2))  # Compté
    cash_difference = Column(Numeric(15, 2))  # Écart
    closing_note = Column(Text)

    # Totaux calculés
    total_sales = Column(Numeric(15, 2), default=0)
    total_refunds = Column(Numeric(15, 2), default=0)
    total_discounts = Column(Numeric(15, 2), default=0)
    total_tax = Column(Numeric(15, 2), default=0)
    transaction_count = Column(Integer, default=0)

    # Par mode de paiement
    cash_total = Column(Numeric(15, 2), default=0)
    card_total = Column(Numeric(15, 2), default=0)
    check_total = Column(Numeric(15, 2), default=0)
    other_total = Column(Numeric(15, 2), default=0)

    # Dates
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_session_number', 'tenant_id', 'session_number', unique=True),
        Index('idx_pos_session_terminal', 'tenant_id', 'terminal_id'),
        Index('idx_pos_session_date', 'tenant_id', 'opened_at'),
    )


class CashMovement(Base):
    """Mouvement de caisse (entrée/sortie)."""
    __tablename__ = "pos_cash_movements"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("pos_sessions.id"), nullable=False)

    # Type
    movement_type = Column(String(20), nullable=False)  # IN, OUT

    # Montant
    amount = Column(Numeric(15, 2), nullable=False)

    # Motif
    reason = Column(String(100), nullable=False)
    description = Column(Text)

    # Utilisateur
    performed_by_id = Column(Integer, ForeignKey("pos_users.id"), nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_cash_mov_session', 'tenant_id', 'session_id'),
    )


# ============================================================================
# MODÈLES TRANSACTION
# ============================================================================

class POSTransaction(Base):
    """Transaction POS (vente)."""
    __tablename__ = "pos_transactions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("pos_sessions.id"), nullable=False)

    # Numéro de ticket
    receipt_number = Column(String(50), nullable=False)
    receipt_sequence = Column(Integer, nullable=False)

    # Statut
    status = Column(Enum(POSTransactionStatus), default=POSTransactionStatus.PENDING)

    # Client (optionnel)
    customer_id = Column(Integer)  # FK vers customers
    customer_name = Column(String(255))
    customer_email = Column(String(255))
    customer_phone = Column(String(50))

    # Vendeur
    cashier_id = Column(Integer, ForeignKey("pos_users.id"), nullable=False)
    salesperson_id = Column(Integer, ForeignKey("pos_users.id"))

    # Montants
    subtotal = Column(Numeric(15, 2), nullable=False, default=0)
    discount_total = Column(Numeric(15, 2), default=0)
    tax_total = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), nullable=False, default=0)

    # Paiement
    amount_paid = Column(Numeric(15, 2), default=0)
    amount_due = Column(Numeric(15, 2), default=0)
    change_given = Column(Numeric(15, 2), default=0)

    # Remise globale
    discount_type = Column(Enum(DiscountType))
    discount_value = Column(Numeric(15, 2))
    discount_reason = Column(String(255))

    # Notes
    notes = Column(Text)
    internal_notes = Column(Text)

    # Référence
    original_transaction_id = Column(Integer)  # Pour retours/échanges
    ecommerce_order_id = Column(Integer)  # Lien commande web

    # Synchronisation
    is_synced = Column(Boolean, default=True)
    offline_id = Column(String(100))  # ID généré offline

    # Dates
    completed_at = Column(DateTime)
    voided_at = Column(DateTime)
    voided_by_id = Column(Integer, ForeignKey("pos_users.id"))
    void_reason = Column(String(255))

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_trans_receipt', 'tenant_id', 'receipt_number', unique=True),
        Index('idx_pos_trans_session', 'tenant_id', 'session_id'),
        Index('idx_pos_trans_date', 'tenant_id', 'created_at'),
        Index('idx_pos_trans_customer', 'tenant_id', 'customer_id'),
    )


class POSTransactionLine(Base):
    """Ligne de transaction POS."""
    __tablename__ = "pos_transaction_lines"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    transaction_id = Column(Integer, ForeignKey("pos_transactions.id"), nullable=False)

    # Produit
    product_id = Column(Integer)  # FK vers products
    variant_id = Column(Integer)
    sku = Column(String(100))
    barcode = Column(String(100))
    name = Column(String(255), nullable=False)

    # Quantité
    quantity = Column(Numeric(15, 3), nullable=False)
    unit = Column(String(20), default="unit")

    # Prix
    unit_price = Column(Numeric(15, 2), nullable=False)
    original_price = Column(Numeric(15, 2))  # Prix avant remise

    # Remise ligne
    discount_type = Column(Enum(DiscountType))
    discount_value = Column(Numeric(15, 2))
    discount_amount = Column(Numeric(15, 2), default=0)
    discount_reason = Column(String(255))

    # Taxes
    tax_rate = Column(Numeric(5, 2), default=20.00)
    tax_amount = Column(Numeric(15, 2), default=0)

    # Total
    line_total = Column(Numeric(15, 2), nullable=False)

    # Vendeur sur la ligne (si différent)
    salesperson_id = Column(Integer, ForeignKey("pos_users.id"))

    # Notes
    notes = Column(Text)

    # Retour
    is_return = Column(Boolean, default=False)
    return_reason = Column(String(255))

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_line_trans', 'tenant_id', 'transaction_id'),
        Index('idx_pos_line_product', 'tenant_id', 'product_id'),
    )


class POSPayment(Base):
    """Paiement sur transaction POS."""
    __tablename__ = "pos_payments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    transaction_id = Column(Integer, ForeignKey("pos_transactions.id"), nullable=False)

    # Type de paiement
    payment_method = Column(Enum(PaymentMethodType), nullable=False)
    payment_method_name = Column(String(100))  # Détail (ex: "Visa", "Mastercard")

    # Montant
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EUR")

    # Détails carte
    card_type = Column(String(20))
    card_last4 = Column(String(4))
    card_auth_code = Column(String(50))
    card_transaction_id = Column(String(100))

    # Détails chèque
    check_number = Column(String(50))
    check_bank = Column(String(100))

    # Détails carte cadeau
    gift_card_number = Column(String(100))

    # Rendu monnaie (pour espèces)
    amount_tendered = Column(Numeric(15, 2))
    change_amount = Column(Numeric(15, 2))

    # Statut
    status = Column(String(20), default="COMPLETED")  # COMPLETED, PENDING, FAILED, REFUNDED
    error_message = Column(Text)

    # Référence externe
    external_id = Column(String(255))

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_payment_trans', 'tenant_id', 'transaction_id'),
    )


# ============================================================================
# MODÈLES RAPPORT
# ============================================================================

class POSDailyReport(Base):
    """Rapport journalier (Z-Report)."""
    __tablename__ = "pos_daily_reports"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("pos_stores.id"), nullable=False)

    # Date
    report_date = Column(DateTime, nullable=False)
    report_number = Column(String(50), nullable=False)

    # Périodes
    first_transaction_at = Column(DateTime)
    last_transaction_at = Column(DateTime)

    # Totaux
    gross_sales = Column(Numeric(15, 2), default=0)
    net_sales = Column(Numeric(15, 2), default=0)
    total_discounts = Column(Numeric(15, 2), default=0)
    total_refunds = Column(Numeric(15, 2), default=0)
    total_tax = Column(Numeric(15, 2), default=0)

    # Transactions
    transaction_count = Column(Integer, default=0)
    items_sold = Column(Integer, default=0)
    average_transaction = Column(Numeric(15, 2), default=0)

    # Par mode de paiement
    cash_total = Column(Numeric(15, 2), default=0)
    card_total = Column(Numeric(15, 2), default=0)
    check_total = Column(Numeric(15, 2), default=0)
    other_total = Column(Numeric(15, 2), default=0)

    # Caisse
    opening_cash = Column(Numeric(15, 2), default=0)
    closing_cash = Column(Numeric(15, 2), default=0)
    cash_movements_in = Column(Numeric(15, 2), default=0)
    cash_movements_out = Column(Numeric(15, 2), default=0)

    # Écarts
    expected_cash = Column(Numeric(15, 2), default=0)
    actual_cash = Column(Numeric(15, 2), default=0)
    cash_variance = Column(Numeric(15, 2), default=0)

    # Détails par TVA
    tax_breakdown = Column(JSON)  # {"20": {"base": 1000, "tax": 200}, "5.5": {...}}

    # Détails par catégorie
    category_breakdown = Column(JSON)

    # Sessions incluses
    session_ids = Column(JSON)

    # Généré par
    generated_by_id = Column(Integer, ForeignKey("pos_users.id"))
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_report_date', 'tenant_id', 'store_id', 'report_date', unique=True),
    )


# ============================================================================
# MODÈLES PRODUIT POS
# ============================================================================

class POSProductQuickKey(Base):
    """Raccourci clavier produit (favorites)."""
    __tablename__ = "pos_quick_keys"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("pos_stores.id"))

    # Position
    page = Column(Integer, default=1)
    position = Column(Integer, nullable=False)  # 1-20 par page

    # Produit
    product_id = Column(Integer)
    variant_id = Column(Integer)

    # Affichage
    label = Column(String(50))
    color = Column(String(20), default="#1976D2")
    icon = Column(String(50))
    image_url = Column(String(500))

    # Prix personnalisé (optionnel)
    custom_price = Column(Numeric(15, 2))

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_quickkey_pos', 'tenant_id', 'store_id', 'page', 'position', unique=True),
    )


class POSHoldTransaction(Base):
    """Transaction en attente."""
    __tablename__ = "pos_hold_transactions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    terminal_id = Column(Integer, ForeignKey("pos_terminals.id"), nullable=False)

    # Identification
    hold_number = Column(String(50), nullable=False)
    hold_name = Column(String(100))  # Nom du client ou référence

    # Données
    transaction_data = Column(JSON, nullable=False)  # Snapshot complet

    # Client
    customer_id = Column(Integer)
    customer_name = Column(String(255))

    # Utilisateur
    held_by_id = Column(Integer, ForeignKey("pos_users.id"), nullable=False)

    # Expiration
    expires_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_hold_terminal', 'tenant_id', 'terminal_id'),
    )


# ============================================================================
# MODÈLES SYNCHRONISATION OFFLINE
# ============================================================================

class POSOfflineQueue(Base):
    """File d'attente synchronisation offline."""
    __tablename__ = "pos_offline_queue"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    terminal_id = Column(Integer, ForeignKey("pos_terminals.id"), nullable=False)

    # Type d'opération
    operation_type = Column(String(50), nullable=False)  # TRANSACTION, PAYMENT, CASH_MOVEMENT

    # Données
    payload = Column(JSON, nullable=False)
    offline_id = Column(String(100), nullable=False)

    # Statut sync
    sync_status = Column(String(20), default="PENDING")  # PENDING, SYNCED, FAILED
    sync_attempts = Column(Integer, default=0)
    sync_error = Column(Text)
    synced_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_pos_offline_status', 'tenant_id', 'sync_status'),
        Index('idx_pos_offline_id', 'tenant_id', 'offline_id', unique=True),
    )
