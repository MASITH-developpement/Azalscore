"""
AZALS MODULE - Odoo Import - Models
====================================

Modeles SQLAlchemy pour la configuration et le suivi des imports Odoo.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.core.types import JSON, UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class OdooSyncType(str, enum.Enum):
    """Types de synchronisation disponibles."""
    PRODUCTS = "products"
    CONTACTS = "contacts"
    SUPPLIERS = "suppliers"
    PURCHASE_ORDERS = "purchase_orders"
    SALE_ORDERS = "sale_orders"
    INVOICES = "invoices"
    QUOTES = "quotes"
    ACCOUNTING = "accounting"
    BANK = "bank"
    INTERVENTIONS = "interventions"
    FULL = "full"


class OdooImportStatus(str, enum.Enum):
    """Statut d'une operation d'import."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"  # Certains elements importes avec erreurs
    ERROR = "error"
    CANCELLED = "cancelled"


class OdooAuthMethod(str, enum.Enum):
    """Methode d'authentification Odoo."""
    PASSWORD = "password"  # Odoo 8-18 (username/password)
    API_KEY = "api_key"    # Odoo 14+ (recommande)


class OdooScheduleMode(str, enum.Enum):
    """Mode de planification des imports."""
    DISABLED = "disabled"   # Pas de planification automatique
    CRON = "cron"           # Expression cron (ex: "0 8 * * 1-5")
    INTERVAL = "interval"   # Intervalle en minutes (ex: 60)


# ============================================================================
# MODELS
# ============================================================================

class OdooConnectionConfig(Base):
    """
    Configuration de connexion Odoo par tenant.
    Stocke les parametres de connexion et les preferences de sync.
    """
    __tablename__ = "odoo_connection_configs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    name = Column(String(255), nullable=False)  # Nom de la connexion (ex: "Odoo Production")
    description = Column(Text, nullable=True)

    # Connexion Odoo
    odoo_url = Column(String(500), nullable=False)  # URL de l'instance Odoo
    odoo_database = Column(String(100), nullable=False)  # Nom de la base Odoo
    odoo_version = Column(String(10), nullable=True)  # Version detectee (ex: "17.0")

    # Authentification
    auth_method = Column(
        Enum(OdooAuthMethod, values_callable=lambda x: [e.value for e in x]),
        default=OdooAuthMethod.API_KEY,
        nullable=False
    )
    username = Column(String(255), nullable=False)
    # API key ou password (chiffre via Fernet dans le service)
    encrypted_credential = Column(Text, nullable=True)

    # Options de synchronisation - Donnees de base
    sync_products = Column(Boolean, default=True)
    sync_contacts = Column(Boolean, default=True)
    sync_suppliers = Column(Boolean, default=True)
    # Commandes
    sync_purchase_orders = Column(Boolean, default=False)
    sync_sale_orders = Column(Boolean, default=False)
    # Documents commerciaux
    sync_invoices = Column(Boolean, default=True)
    sync_quotes = Column(Boolean, default=True)
    # Finance
    sync_accounting = Column(Boolean, default=False)
    sync_bank = Column(Boolean, default=False)
    # Services
    sync_interventions = Column(Boolean, default=False)

    # Configuration delta sync
    products_last_sync_at = Column(DateTime, nullable=True)
    contacts_last_sync_at = Column(DateTime, nullable=True)
    suppliers_last_sync_at = Column(DateTime, nullable=True)
    orders_last_sync_at = Column(DateTime, nullable=True)
    accounting_last_sync_at = Column(DateTime, nullable=True)
    bank_last_sync_at = Column(DateTime, nullable=True)

    # Statistiques
    total_imports = Column(Integer, default=0)
    total_products_imported = Column(Integer, default=0)
    total_contacts_imported = Column(Integer, default=0)
    total_suppliers_imported = Column(Integer, default=0)
    total_orders_imported = Column(Integer, default=0)
    total_accounting_entries_imported = Column(Integer, default=0)
    last_error_message = Column(Text, nullable=True)

    # Etat
    is_active = Column(Boolean, default=True)
    is_connected = Column(Boolean, default=False)  # Dernier test de connexion OK
    last_connection_test_at = Column(DateTime, nullable=True)

    # Mapping personnalise (optionnel)
    custom_field_mapping = Column(JSON, default=dict)

    # === PLANIFICATION ===
    schedule_mode = Column(
        Enum(OdooScheduleMode, values_callable=lambda x: [e.value for e in x]),
        default=OdooScheduleMode.DISABLED,
        nullable=False
    )
    # Expression cron si mode='cron' (ex: "0 8 * * 1-5" = 8h lun-ven)
    schedule_cron_expression = Column(String(100), nullable=True)
    # Intervalle en minutes si mode='interval' (ex: 60 = toutes les heures)
    schedule_interval_minutes = Column(Integer, nullable=True)
    # Timezone pour le cron (defaut: Europe/Paris)
    schedule_timezone = Column(String(50), default='Europe/Paris', nullable=False)
    # Pause temporaire de la planification
    schedule_paused = Column(Boolean, default=False, nullable=False)
    # Prochain run planifie (calcule par le scheduler)
    next_scheduled_run = Column(DateTime, nullable=True)
    # Dernier run planifie
    last_scheduled_run = Column(DateTime, nullable=True)
    # Options avancees d'import par type (JSON)
    import_options = Column(JSON, default=dict)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_odoo_config_tenant_name'),
        Index('idx_odoo_config_tenant', 'tenant_id'),
        Index('idx_odoo_config_active', 'tenant_id', 'is_active'),
        Index('idx_odoo_config_schedule', 'is_active', 'schedule_mode', 'schedule_paused'),
    )


class OdooImportHistory(Base):
    """
    Historique des operations d'import Odoo.
    Trace chaque synchronisation avec statistiques detaillees.
    """
    __tablename__ = "odoo_import_history"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    config_id = Column(UniversalUUID(), nullable=False, index=True)

    # Type de sync
    sync_type = Column(
        Enum(OdooSyncType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )

    # Statut
    status = Column(
        Enum(OdooImportStatus, values_callable=lambda x: [e.value for e in x]),
        default=OdooImportStatus.PENDING,
        nullable=False
    )

    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Statistiques
    total_records = Column(Integer, default=0)  # Nombre de records Odoo traites
    created_count = Column(Integer, default=0)  # Nouveaux enregistrements
    updated_count = Column(Integer, default=0)  # Enregistrements mis a jour
    skipped_count = Column(Integer, default=0)  # Enregistrements ignores
    error_count = Column(Integer, default=0)    # Erreurs

    # Details
    error_details = Column(JSON, default=list)  # Liste des erreurs detaillees
    import_summary = Column(JSON, default=dict)  # Resume de l'import

    # Parametres utilises
    is_delta_sync = Column(Boolean, default=True)  # Sync incrementale ou complete
    delta_from_date = Column(DateTime, nullable=True)  # Date de debut delta

    # Audit
    triggered_by = Column(UniversalUUID(), nullable=True)  # User qui a lance l'import
    trigger_method = Column(String(50), default="manual")  # manual, scheduled, api

    __table_args__ = (
        Index('idx_import_history_tenant', 'tenant_id'),
        Index('idx_import_history_config', 'config_id'),
        Index('idx_import_history_status', 'tenant_id', 'status'),
        Index('idx_import_history_date', 'tenant_id', 'started_at'),
    )


class OdooFieldMapping(Base):
    """
    Mapping personnalise des champs Odoo vers AZALSCORE.
    Permet de surcharger les mappings par defaut par tenant.
    """
    __tablename__ = "odoo_field_mappings"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    config_id = Column(UniversalUUID(), nullable=False, index=True)

    # Modele source Odoo
    odoo_model = Column(String(100), nullable=False)  # ex: "product.product"

    # Modele cible AZALSCORE
    azals_model = Column(String(100), nullable=False)  # ex: "Product"

    # Mapping des champs (JSON: {odoo_field: azals_field, ...})
    field_mapping = Column(JSON, nullable=False)

    # Transformations (JSON: {field: {type: "transform_type", params: {...}}, ...})
    transformations = Column(JSON, default=dict)

    # Configuration
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)  # Pour gerer plusieurs mappings

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_field_mapping_tenant', 'tenant_id'),
        Index('idx_field_mapping_config', 'config_id'),
        Index('idx_field_mapping_model', 'tenant_id', 'odoo_model'),
        UniqueConstraint('config_id', 'odoo_model', 'azals_model', name='uq_field_mapping'),
    )


# ============================================================================
# MAPPING ODOO PAR DEFAUT
# ============================================================================

DEFAULT_PRODUCT_MAPPING = {
    # Champs obligatoires
    "name": "name",
    "default_code": "sku",

    # Prix
    "list_price": "unit_price",
    "standard_price": "cost_price",

    # Codes
    "barcode": "barcode",

    # Description
    "description": "description",
    "description_sale": "sales_description",

    # Categorie (necessite mapping supplementaire)
    "categ_id": "category_id",

    # Stock (si module stock installe)
    "qty_available": "quantity_in_stock",

    # Poids/dimensions
    "weight": "weight",
    "volume": "volume",

    # Champs ERP (ajoutes pour compatibilite)
    "taxes_id": "tax_id",

    # Flags
    "sale_ok": "is_sellable",
    "purchase_ok": "is_purchasable",
    "active": "is_active",
}

DEFAULT_CONTACT_MAPPING = {
    # Identification
    "name": "name",
    "ref": "reference",
    "vat": "vat_number",

    # Contact
    "email": "email",
    "phone": "phone",
    "mobile": "mobile",
    "website": "website",

    # Adresse
    "street": "address_line1",
    "street2": "address_line2",
    "city": "city",
    "zip": "postal_code",
    "country_id": "country_code",  # Necessite transformation

    # Type
    "is_company": "is_company",
    "company_type": "contact_type",

    # Commercial
    "credit_limit": "credit_limit",
    "property_payment_term_id": "payment_term_id",

    # Flags
    "active": "is_active",
    "customer_rank": "customer_rank",  # Pour identifier les clients
    "supplier_rank": "supplier_rank",  # Pour identifier les fournisseurs
}

DEFAULT_PURCHASE_ORDER_MAPPING = {
    "name": "order_number",
    "date_order": "order_date",
    "partner_id": "supplier_id",
    "date_planned": "expected_delivery_date",
    "amount_total": "total_amount",
    "amount_untaxed": "subtotal_amount",
    "amount_tax": "tax_amount",
    "state": "status",
    "notes": "notes",
}

DEFAULT_MAPPINGS = {
    "product.product": DEFAULT_PRODUCT_MAPPING,
    "res.partner": DEFAULT_CONTACT_MAPPING,
    "purchase.order": DEFAULT_PURCHASE_ORDER_MAPPING,
}
