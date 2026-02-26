"""
AZALS MODULE ASSETS - Modeles SQLAlchemy
=========================================

Gestion des Immobilisations pour AZALSCORE ERP.
Fonctionnalites inspirees de: Sage, Odoo, Microsoft Dynamics 365, Pennylane, Axonaut.

Fonctionnalites:
- Gestion du cycle de vie complet des actifs
- Calcul des amortissements (lineaire, degressif, unites de production, SOFTY)
- Suivi maintenance et garantie
- Cessions et mises au rebut
- Inventaire physique avec codes-barres/QR
- Valorisation et reporting comptable
- Conformite PCG, IFRS, CGI
- Integration assurance
- Gestion multi-sites et transferts
"""

import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.types import JSONB, UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class AssetType(str, enum.Enum):
    """Types d'immobilisations selon le PCG."""
    # Immobilisations incorporelles (compte 20)
    INTANGIBLE_GOODWILL = "INTANGIBLE_GOODWILL"  # Fonds commercial (207)
    INTANGIBLE_PATENT = "INTANGIBLE_PATENT"  # Brevets (205)
    INTANGIBLE_LICENSE = "INTANGIBLE_LICENSE"  # Licences (205)
    INTANGIBLE_SOFTWARE = "INTANGIBLE_SOFTWARE"  # Logiciels (205)
    INTANGIBLE_TRADEMARK = "INTANGIBLE_TRADEMARK"  # Marques (206)
    INTANGIBLE_RD = "INTANGIBLE_RD"  # Frais R&D (203)
    INTANGIBLE_OTHER = "INTANGIBLE_OTHER"  # Autres incorporelles

    # Immobilisations corporelles (compte 21)
    TANGIBLE_LAND = "TANGIBLE_LAND"  # Terrains (211)
    TANGIBLE_BUILDING = "TANGIBLE_BUILDING"  # Constructions (213)
    TANGIBLE_TECHNICAL = "TANGIBLE_TECHNICAL"  # Installations techniques (215)
    TANGIBLE_INDUSTRIAL = "TANGIBLE_INDUSTRIAL"  # Materiel industriel (2154)
    TANGIBLE_TRANSPORT = "TANGIBLE_TRANSPORT"  # Materiel de transport (2182)
    TANGIBLE_OFFICE = "TANGIBLE_OFFICE"  # Materiel de bureau (2183)
    TANGIBLE_IT = "TANGIBLE_IT"  # Materiel informatique (2183)
    TANGIBLE_FURNITURE = "TANGIBLE_FURNITURE"  # Mobilier (2184)
    TANGIBLE_FIXTURE = "TANGIBLE_FIXTURE"  # Agencements (2181)
    TANGIBLE_TOOLS = "TANGIBLE_TOOLS"  # Outillage (2155)
    TANGIBLE_OTHER = "TANGIBLE_OTHER"  # Autres corporelles

    # Immobilisations financieres (compte 26-27)
    FINANCIAL_PARTICIPATION = "FINANCIAL_PARTICIPATION"  # Participations (261)
    FINANCIAL_LOAN = "FINANCIAL_LOAN"  # Prets (274)
    FINANCIAL_DEPOSIT = "FINANCIAL_DEPOSIT"  # Depots et cautionnements (275)
    FINANCIAL_OTHER = "FINANCIAL_OTHER"  # Autres financieres

    # Immobilisations en cours
    IN_PROGRESS = "IN_PROGRESS"  # Immobilisations en cours (23)


class DepreciationMethod(str, enum.Enum):
    """Methodes d'amortissement."""
    LINEAR = "LINEAR"  # Lineaire
    DECLINING_BALANCE = "DECLINING_BALANCE"  # Degressif fiscal
    UNITS_OF_PRODUCTION = "UNITS_OF_PRODUCTION"  # Unites de production/oeuvre
    SUM_OF_YEARS_DIGITS = "SUM_OF_YEARS_DIGITS"  # SOFTY (Sum Of Years Digits)
    EXCEPTIONAL = "EXCEPTIONAL"  # Exceptionnel
    NONE = "NONE"  # Non amortissable (terrains)


class AssetStatus(str, enum.Enum):
    """Statuts de l'immobilisation."""
    DRAFT = "DRAFT"  # Brouillon
    ORDERED = "ORDERED"  # Commandee
    RECEIVED = "RECEIVED"  # Recue (pas encore en service)
    IN_SERVICE = "IN_SERVICE"  # En service
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"  # En maintenance
    OUT_OF_SERVICE = "OUT_OF_SERVICE"  # Hors service temporaire
    FULLY_DEPRECIATED = "FULLY_DEPRECIATED"  # Totalement amortie
    DISPOSED = "DISPOSED"  # Cedee
    SCRAPPED = "SCRAPPED"  # Mise au rebut
    TRANSFERRED = "TRANSFERRED"  # Transferee (intra-groupe)
    STOLEN = "STOLEN"  # Volee
    DESTROYED = "DESTROYED"  # Detruite


class DisposalType(str, enum.Enum):
    """Types de sortie/cession."""
    SALE = "SALE"  # Vente
    SCRAP = "SCRAP"  # Mise au rebut
    DONATION = "DONATION"  # Don
    THEFT = "THEFT"  # Vol
    DESTRUCTION = "DESTRUCTION"  # Destruction
    TRANSFER_INTRAGROUP = "TRANSFER_INTRAGROUP"  # Transfert intra-groupe
    EXCHANGE = "EXCHANGE"  # Echange
    LOSS = "LOSS"  # Perte


class MovementType(str, enum.Enum):
    """Types de mouvement sur l'actif."""
    ACQUISITION = "ACQUISITION"  # Acquisition initiale
    IMPROVEMENT = "IMPROVEMENT"  # Amelioration/composant
    REVALUATION_UP = "REVALUATION_UP"  # Reevaluation a la hausse
    REVALUATION_DOWN = "REVALUATION_DOWN"  # Reevaluation a la baisse
    IMPAIRMENT = "IMPAIRMENT"  # Depreciation
    IMPAIRMENT_REVERSAL = "IMPAIRMENT_REVERSAL"  # Reprise depreciation
    DEPRECIATION = "DEPRECIATION"  # Amortissement
    DISPOSAL = "DISPOSAL"  # Cession
    TRANSFER = "TRANSFER"  # Transfert
    SPLIT = "SPLIT"  # Scission
    MERGE = "MERGE"  # Fusion


class MaintenanceType(str, enum.Enum):
    """Types de maintenance."""
    PREVENTIVE = "PREVENTIVE"  # Maintenance preventive
    CORRECTIVE = "CORRECTIVE"  # Maintenance corrective
    PREDICTIVE = "PREDICTIVE"  # Maintenance predictive
    REGULATORY = "REGULATORY"  # Controle reglementaire
    CALIBRATION = "CALIBRATION"  # Etalonnage
    INSPECTION = "INSPECTION"  # Inspection
    UPGRADE = "UPGRADE"  # Mise a niveau


class MaintenanceStatus(str, enum.Enum):
    """Statuts de maintenance."""
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    OVERDUE = "OVERDUE"


class InventoryStatus(str, enum.Enum):
    """Statuts d'inventaire."""
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    VALIDATED = "VALIDATED"
    CANCELLED = "CANCELLED"


class InsuranceStatus(str, enum.Enum):
    """Statuts d'assurance."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"


# ============================================================================
# MODELES - CATEGORIES
# ============================================================================

class AssetCategory(Base):
    """Categorie d'immobilisation."""
    __tablename__ = "asset_categories"
    __table_args__ = (
        Index("idx_asset_cat_tenant", "tenant_id"),
        Index("idx_asset_cat_parent", "parent_id"),
        Index("idx_asset_cat_code", "tenant_id", "code"),
        UniqueConstraint("tenant_id", "code", name="uq_asset_cat_code"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Hierarchie
    parent_id = Column(UniversalUUID(), ForeignKey("asset_categories.id"))

    # Type par defaut
    default_asset_type = Column(SQLEnum(AssetType))
    default_depreciation_method = Column(SQLEnum(DepreciationMethod), default=DepreciationMethod.LINEAR)
    default_useful_life_years = Column(Integer)
    default_useful_life_months = Column(Integer, default=0)

    # Comptes comptables par defaut
    default_asset_account = Column(String(20))  # Compte immobilisation
    default_depreciation_account = Column(String(20))  # Compte amortissement
    default_expense_account = Column(String(20))  # Compte dotation

    # Statut
    is_active = Column(Boolean, default=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(UniversalUUID())
    version = Column(Integer, default=1)

    # Relations
    children = relationship("AssetCategory", backref="parent", remote_side=[id])
    assets = relationship("FixedAsset", back_populates="category")


# ============================================================================
# MODELES - IMMOBILISATIONS
# ============================================================================

class FixedAsset(Base):
    """Immobilisation principale."""
    __tablename__ = "fixed_assets"
    __table_args__ = (
        Index("idx_fixed_asset_tenant", "tenant_id"),
        Index("idx_fixed_asset_code", "tenant_id", "asset_code"),
        Index("idx_fixed_asset_barcode", "tenant_id", "barcode"),
        Index("idx_fixed_asset_status", "tenant_id", "status"),
        Index("idx_fixed_asset_category", "tenant_id", "category_id"),
        Index("idx_fixed_asset_location", "tenant_id", "location_id"),
        Index("idx_fixed_asset_responsible", "tenant_id", "responsible_id"),
        Index("idx_fixed_asset_deleted", "tenant_id", "is_deleted"),
        UniqueConstraint("tenant_id", "asset_code", name="uq_fixed_asset_code"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    asset_code = Column(String(50), nullable=False)
    name = Column(String(300), nullable=False)
    description = Column(Text)

    # Classification
    asset_type = Column(SQLEnum(AssetType), nullable=False)
    category_id = Column(UniversalUUID(), ForeignKey("asset_categories.id"))

    # Hierarchie (composants)
    parent_asset_id = Column(UniversalUUID(), ForeignKey("fixed_assets.id"))
    is_component = Column(Boolean, default=False)  # Est un composant

    # Statut
    status = Column(SQLEnum(AssetStatus), default=AssetStatus.DRAFT)

    # Identification physique
    serial_number = Column(String(100))
    barcode = Column(String(100))
    qr_code = Column(String(500))  # Contenu QR code
    rfid_tag = Column(String(100))
    inventory_number = Column(String(100))  # Numero d'inventaire interne

    # Fabricant
    manufacturer = Column(String(200))
    brand = Column(String(100))
    model = Column(String(200))
    year_manufactured = Column(Integer)

    # Acquisition
    acquisition_date = Column(Date, nullable=False)
    in_service_date = Column(Date)  # Date mise en service
    purchase_order_reference = Column(String(100))
    invoice_reference = Column(String(100))
    invoice_date = Column(Date)

    # Fournisseur
    supplier_id = Column(UniversalUUID())  # Ref procurement.Supplier
    supplier_name = Column(String(200))

    # Couts d'acquisition
    purchase_price = Column(Numeric(18, 2), default=0)  # Prix d'achat HT
    vat_amount = Column(Numeric(18, 2), default=0)  # TVA (si non recuperable)
    transport_cost = Column(Numeric(18, 2), default=0)
    installation_cost = Column(Numeric(18, 2), default=0)
    customs_cost = Column(Numeric(18, 2), default=0)  # Droits de douane
    other_costs = Column(Numeric(18, 2), default=0)
    acquisition_cost = Column(Numeric(18, 2), default=0)  # Cout total

    # Valeur residuelle
    residual_value = Column(Numeric(18, 2), default=0)
    residual_value_percent = Column(Numeric(5, 2))  # % de la valeur d'achat

    # Amortissement
    depreciation_method = Column(SQLEnum(DepreciationMethod), default=DepreciationMethod.LINEAR)
    useful_life_years = Column(Integer, nullable=False)
    useful_life_months = Column(Integer, default=0)
    depreciation_start_date = Column(Date)

    # Pour amortissement degressif
    declining_balance_rate = Column(Numeric(5, 2))  # Coefficient degressif

    # Pour unites de production
    total_units = Column(Numeric(18, 2))  # Nombre total d'unites prevues
    units_produced = Column(Numeric(18, 2), default=0)  # Unites deja produites

    # Valeurs calculees
    accumulated_depreciation = Column(Numeric(18, 2), default=0)
    net_book_value = Column(Numeric(18, 2))  # VNC
    fiscal_accumulated_depreciation = Column(Numeric(18, 2), default=0)  # Si difference comptable/fiscal

    # Depreciation/Impairment
    impairment_amount = Column(Numeric(18, 2), default=0)  # Depreciation actuelle
    recoverable_amount = Column(Numeric(18, 2))  # Valeur recouvrable

    # Reevaluation
    revalued_amount = Column(Numeric(18, 2))
    revaluation_date = Column(Date)
    revaluation_surplus = Column(Numeric(18, 2), default=0)

    # Localisation
    location_id = Column(UniversalUUID())  # Ref site/entrepot
    site_name = Column(String(200))
    building = Column(String(100))
    floor = Column(String(50))
    room = Column(String(100))
    position = Column(String(200))
    gps_latitude = Column(Numeric(10, 7))
    gps_longitude = Column(Numeric(10, 7))

    # Responsable
    responsible_id = Column(UniversalUUID())  # Ref User/Employee
    responsible_name = Column(String(200))
    department_id = Column(UniversalUUID())
    department_name = Column(String(200))
    cost_center = Column(String(50))

    # Analytique
    analytic_account_id = Column(UniversalUUID())
    analytic_tags = Column(JSONB, default=list)

    # Comptes comptables
    asset_account = Column(String(20))  # 21xxxx
    depreciation_account = Column(String(20))  # 28xxxx
    expense_account = Column(String(20))  # 681xxx

    # Garantie
    warranty_start_date = Column(Date)
    warranty_end_date = Column(Date)
    warranty_provider = Column(String(200))
    warranty_terms = Column(Text)
    extended_warranty = Column(Boolean, default=False)

    # Maintenance
    maintenance_contract_id = Column(UniversalUUID())
    last_maintenance_date = Column(Date)
    next_maintenance_date = Column(Date)
    maintenance_frequency_days = Column(Integer)

    # Assurance
    insurance_policy_id = Column(UniversalUUID())
    insured_value = Column(Numeric(18, 2))
    insurance_expiry_date = Column(Date)

    # Cession
    disposal_date = Column(Date)
    disposal_type = Column(SQLEnum(DisposalType))
    disposal_proceeds = Column(Numeric(18, 2))  # Prix de cession
    disposal_costs = Column(Numeric(18, 2))  # Frais de cession
    disposal_gain_loss = Column(Numeric(18, 2))  # Plus/moins-value
    buyer_name = Column(String(200))
    buyer_id = Column(UniversalUUID())

    # Documents et medias
    photo_url = Column(String(500))
    documents = Column(JSONB, default=list)  # Liste de documents

    # Specifications techniques
    specifications = Column(JSONB, default=dict)
    dimensions = Column(String(200))  # LxlxH
    weight = Column(Numeric(12, 3))
    weight_unit = Column(String(10), default="kg")
    power_rating = Column(String(100))
    energy_class = Column(String(20))

    # Compteurs (pour amortissement par usage)
    counter_type = Column(String(50))  # HOURS, KM, CYCLES, etc.
    counter_current = Column(Numeric(18, 2), default=0)
    counter_at_acquisition = Column(Numeric(18, 2), default=0)

    # Indicateurs
    expected_end_of_life = Column(Date)
    condition_rating = Column(Integer)  # 1-5

    # Notes
    notes = Column(Text)
    internal_notes = Column(Text)

    # Tags
    tags = Column(JSONB, default=list)

    # Devises
    currency = Column(String(3), default="EUR")
    original_currency = Column(String(3))  # Si achat en devise etrangere
    exchange_rate = Column(Numeric(12, 6))

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(UniversalUUID())
    version = Column(Integer, default=1)

    # Relations
    category = relationship("AssetCategory", back_populates="assets")
    components = relationship("FixedAsset", backref="parent_asset", remote_side=[id])
    depreciation_schedule = relationship("DepreciationSchedule", back_populates="asset", cascade="all, delete-orphan")
    movements = relationship("AssetMovement", back_populates="asset", cascade="all, delete-orphan")
    maintenances = relationship("AssetMaintenance", back_populates="asset", cascade="all, delete-orphan")
    documents_rel = relationship("AssetDocument", back_populates="asset", cascade="all, delete-orphan")
    inventory_items = relationship("AssetInventoryItem", back_populates="asset")
    insurance_items = relationship("AssetInsuranceItem", back_populates="asset")
    transfers = relationship("AssetTransfer", back_populates="asset")


# ============================================================================
# MODELES - TABLEAU D'AMORTISSEMENT
# ============================================================================

class DepreciationSchedule(Base):
    """Tableau d'amortissement."""
    __tablename__ = "asset_depreciation_schedules"
    __table_args__ = (
        Index("idx_depr_sched_tenant", "tenant_id"),
        Index("idx_depr_sched_asset", "asset_id"),
        Index("idx_depr_sched_period", "period_start", "period_end"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    asset_id = Column(UniversalUUID(), ForeignKey("fixed_assets.id", ondelete="CASCADE"), nullable=False)

    # Periode
    period_number = Column(Integer, nullable=False)  # Annee 1, 2, 3...
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    fiscal_year = Column(Integer)

    # Valeurs d'ouverture
    opening_gross_value = Column(Numeric(18, 2), nullable=False)
    opening_accumulated_depreciation = Column(Numeric(18, 2), nullable=False)
    opening_net_book_value = Column(Numeric(18, 2), nullable=False)

    # Amortissement de la periode
    depreciation_rate = Column(Numeric(8, 4))  # Taux applique
    depreciation_base = Column(Numeric(18, 2))  # Base de calcul
    depreciation_amount = Column(Numeric(18, 2), nullable=False)
    prorata_days = Column(Integer)  # Jours de prorata

    # Amortissement fiscal (si different)
    fiscal_depreciation_amount = Column(Numeric(18, 2))
    deferred_depreciation = Column(Numeric(18, 2))  # Amortissement derogatoire

    # Valeurs de cloture
    closing_accumulated_depreciation = Column(Numeric(18, 2), nullable=False)
    closing_net_book_value = Column(Numeric(18, 2), nullable=False)

    # Statut
    is_posted = Column(Boolean, default=False)  # Comptabilise
    posted_date = Column(DateTime)
    journal_entry_id = Column(UniversalUUID())

    # Ajustements
    adjustment_amount = Column(Numeric(18, 2), default=0)
    adjustment_reason = Column(Text)

    # Notes
    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    asset = relationship("FixedAsset", back_populates="depreciation_schedule")


# ============================================================================
# MODELES - MOUVEMENTS
# ============================================================================

class AssetMovement(Base):
    """Mouvement sur une immobilisation."""
    __tablename__ = "asset_movements"
    __table_args__ = (
        Index("idx_asset_mvt_tenant", "tenant_id"),
        Index("idx_asset_mvt_asset", "asset_id"),
        Index("idx_asset_mvt_date", "movement_date"),
        Index("idx_asset_mvt_type", "movement_type"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    asset_id = Column(UniversalUUID(), ForeignKey("fixed_assets.id", ondelete="CASCADE"), nullable=False)

    # Mouvement
    movement_type = Column(SQLEnum(MovementType), nullable=False)
    movement_date = Column(Date, nullable=False)
    effective_date = Column(Date)  # Date d'effet (peut differer)

    # Reference
    movement_number = Column(String(50))
    reference = Column(String(200))
    description = Column(Text)

    # Montants
    amount = Column(Numeric(18, 2), nullable=False)
    previous_value = Column(Numeric(18, 2))
    new_value = Column(Numeric(18, 2))

    # Quantite (pour split/merge)
    quantity = Column(Numeric(12, 3))

    # Pour transferts
    from_location_id = Column(UniversalUUID())
    to_location_id = Column(UniversalUUID())
    from_responsible_id = Column(UniversalUUID())
    to_responsible_id = Column(UniversalUUID())

    # Comptabilisation
    is_posted = Column(Boolean, default=False)
    journal_entry_id = Column(UniversalUUID())
    debit_account = Column(String(20))
    credit_account = Column(String(20))

    # Justificatifs
    document_reference = Column(String(200))
    documents = Column(JSONB, default=list)

    # Notes
    notes = Column(Text)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(UniversalUUID())
    version = Column(Integer, default=1)

    # Relations
    asset = relationship("FixedAsset", back_populates="movements")


# ============================================================================
# MODELES - MAINTENANCE
# ============================================================================

class AssetMaintenance(Base):
    """Maintenance d'une immobilisation."""
    __tablename__ = "asset_maintenances"
    __table_args__ = (
        Index("idx_asset_maint_tenant", "tenant_id"),
        Index("idx_asset_maint_asset", "asset_id"),
        Index("idx_asset_maint_date", "scheduled_date"),
        Index("idx_asset_maint_status", "status"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    asset_id = Column(UniversalUUID(), ForeignKey("fixed_assets.id", ondelete="CASCADE"), nullable=False)

    # Identification
    maintenance_number = Column(String(50))
    maintenance_type = Column(SQLEnum(MaintenanceType), nullable=False)
    status = Column(SQLEnum(MaintenanceStatus), default=MaintenanceStatus.PLANNED)

    # Description
    title = Column(String(300), nullable=False)
    description = Column(Text)
    work_performed = Column(Text)

    # Planning
    scheduled_date = Column(Date, nullable=False)
    scheduled_end_date = Column(Date)
    actual_start_date = Column(DateTime)
    actual_end_date = Column(DateTime)
    duration_hours = Column(Numeric(8, 2))

    # Intervenant
    technician_id = Column(UniversalUUID())
    technician_name = Column(String(200))
    external_provider_id = Column(UniversalUUID())
    external_provider_name = Column(String(200))

    # Couts
    labor_cost = Column(Numeric(18, 2), default=0)
    parts_cost = Column(Numeric(18, 2), default=0)
    external_cost = Column(Numeric(18, 2), default=0)
    other_cost = Column(Numeric(18, 2), default=0)
    total_cost = Column(Numeric(18, 2), default=0)
    currency = Column(String(3), default="EUR")

    # Pieces utilisees
    parts_used = Column(JSONB, default=list)

    # Compteur a la maintenance
    counter_reading = Column(Numeric(18, 2))

    # Prochaine maintenance
    next_maintenance_date = Column(Date)
    next_maintenance_counter = Column(Numeric(18, 2))

    # Impact sur l'actif
    affects_depreciation = Column(Boolean, default=False)
    capitalized_amount = Column(Numeric(18, 2))  # Si amelioration capitalisee
    extends_useful_life = Column(Boolean, default=False)
    additional_life_months = Column(Integer)

    # Documents
    documents = Column(JSONB, default=list)

    # Notes
    notes = Column(Text)
    internal_notes = Column(Text)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(UniversalUUID())
    version = Column(Integer, default=1)

    # Relations
    asset = relationship("FixedAsset", back_populates="maintenances")


# ============================================================================
# MODELES - DOCUMENTS
# ============================================================================

class AssetDocument(Base):
    """Document associe a une immobilisation."""
    __tablename__ = "asset_documents"
    __table_args__ = (
        Index("idx_asset_doc_tenant", "tenant_id"),
        Index("idx_asset_doc_asset", "asset_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    asset_id = Column(UniversalUUID(), ForeignKey("fixed_assets.id", ondelete="CASCADE"), nullable=False)

    # Document
    document_type = Column(String(50), nullable=False)  # INVOICE, MANUAL, WARRANTY, PHOTO, etc.
    title = Column(String(300), nullable=False)
    description = Column(Text)

    # Fichier
    file_path = Column(String(500))
    file_name = Column(String(255))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    file_hash = Column(String(64))  # SHA256

    # Validite
    valid_from = Column(Date)
    valid_until = Column(Date)
    version_number = Column(String(20))

    # Statut
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    asset = relationship("FixedAsset", back_populates="documents_rel")


# ============================================================================
# MODELES - INVENTAIRE PHYSIQUE
# ============================================================================

class AssetInventory(Base):
    """Session d'inventaire physique des immobilisations."""
    __tablename__ = "asset_inventories"
    __table_args__ = (
        Index("idx_asset_inv_tenant", "tenant_id"),
        Index("idx_asset_inv_date", "inventory_date"),
        Index("idx_asset_inv_status", "status"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    inventory_number = Column(String(50), nullable=False)
    inventory_date = Column(Date, nullable=False)
    description = Column(Text)

    # Perimetre
    location_id = Column(UniversalUUID())
    location_name = Column(String(200))
    category_id = Column(UniversalUUID())
    department_id = Column(UniversalUUID())

    # Statut
    status = Column(SQLEnum(InventoryStatus), default=InventoryStatus.DRAFT)

    # Resultats
    assets_expected = Column(Integer, default=0)
    assets_found = Column(Integer, default=0)
    assets_missing = Column(Integer, default=0)
    assets_unexpected = Column(Integer, default=0)
    assets_condition_issues = Column(Integer, default=0)

    # Responsable
    responsible_id = Column(UniversalUUID())
    responsible_name = Column(String(200))

    # Dates
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    validated_at = Column(DateTime)
    validated_by = Column(UniversalUUID())

    # Notes
    notes = Column(Text)
    findings = Column(Text)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(UniversalUUID())
    version = Column(Integer, default=1)

    # Relations
    items = relationship("AssetInventoryItem", back_populates="inventory", cascade="all, delete-orphan")


class AssetInventoryItem(Base):
    """Ligne d'inventaire pour un actif."""
    __tablename__ = "asset_inventory_items"
    __table_args__ = (
        Index("idx_asset_inv_item_tenant", "tenant_id"),
        Index("idx_asset_inv_item_inv", "inventory_id"),
        Index("idx_asset_inv_item_asset", "asset_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    inventory_id = Column(UniversalUUID(), ForeignKey("asset_inventories.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(UniversalUUID(), ForeignKey("fixed_assets.id"))

    # Actif attendu
    asset_code = Column(String(50))
    asset_name = Column(String(300))
    expected_location = Column(String(200))
    expected_barcode = Column(String(100))

    # Resultat
    found = Column(Boolean)
    actual_location = Column(String(200))
    scanned_barcode = Column(String(100))
    scanned_at = Column(DateTime)
    scanned_by = Column(UniversalUUID())

    # Etat
    condition_rating = Column(Integer)  # 1-5
    condition_notes = Column(Text)
    photo_url = Column(String(500))

    # Ecart
    is_unexpected = Column(Boolean, default=False)  # Trouve mais pas attendu
    location_mismatch = Column(Boolean, default=False)

    # Notes
    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    inventory = relationship("AssetInventory", back_populates="items")
    asset = relationship("FixedAsset", back_populates="inventory_items")


# ============================================================================
# MODELES - ASSURANCE
# ============================================================================

class AssetInsurancePolicy(Base):
    """Police d'assurance pour les immobilisations."""
    __tablename__ = "asset_insurance_policies"
    __table_args__ = (
        Index("idx_asset_ins_tenant", "tenant_id"),
        Index("idx_asset_ins_number", "policy_number"),
        Index("idx_asset_ins_status", "status"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    policy_number = Column(String(100), nullable=False)
    name = Column(String(300), nullable=False)
    description = Column(Text)

    # Assureur
    insurer_name = Column(String(200), nullable=False)
    insurer_contact = Column(String(200))
    insurer_phone = Column(String(50))
    insurer_email = Column(String(200))

    # Couverture
    coverage_type = Column(String(100))  # ALL_RISKS, FIRE, THEFT, etc.
    coverage_description = Column(Text)
    exclusions = Column(Text)

    # Montants
    total_insured_value = Column(Numeric(18, 2))
    deductible_amount = Column(Numeric(18, 2))
    premium_amount = Column(Numeric(18, 2))
    premium_frequency = Column(String(20))  # MONTHLY, QUARTERLY, ANNUAL
    currency = Column(String(3), default="EUR")

    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    renewal_date = Column(Date)

    # Statut
    status = Column(SQLEnum(InsuranceStatus), default=InsuranceStatus.ACTIVE)
    auto_renewal = Column(Boolean, default=False)

    # Documents
    policy_document = Column(String(500))
    documents = Column(JSONB, default=list)

    # Notes
    notes = Column(Text)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(UniversalUUID())
    version = Column(Integer, default=1)

    # Relations
    items = relationship("AssetInsuranceItem", back_populates="policy", cascade="all, delete-orphan")


class AssetInsuranceItem(Base):
    """Actif couvert par une police d'assurance."""
    __tablename__ = "asset_insurance_items"
    __table_args__ = (
        Index("idx_asset_ins_item_tenant", "tenant_id"),
        Index("idx_asset_ins_item_policy", "policy_id"),
        Index("idx_asset_ins_item_asset", "asset_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    policy_id = Column(UniversalUUID(), ForeignKey("asset_insurance_policies.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(UniversalUUID(), ForeignKey("fixed_assets.id"), nullable=False)

    # Valeurs
    insured_value = Column(Numeric(18, 2), nullable=False)
    coverage_start_date = Column(Date)
    coverage_end_date = Column(Date)

    # Notes
    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())

    # Relations
    policy = relationship("AssetInsurancePolicy", back_populates="items")
    asset = relationship("FixedAsset", back_populates="insurance_items")


# ============================================================================
# MODELES - TRANSFERTS
# ============================================================================

class AssetTransfer(Base):
    """Transfert d'immobilisation entre sites/responsables."""
    __tablename__ = "asset_transfers"
    __table_args__ = (
        Index("idx_asset_transfer_tenant", "tenant_id"),
        Index("idx_asset_transfer_asset", "asset_id"),
        Index("idx_asset_transfer_date", "transfer_date"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    asset_id = Column(UniversalUUID(), ForeignKey("fixed_assets.id"), nullable=False)

    # Identification
    transfer_number = Column(String(50), nullable=False)
    transfer_date = Column(Date, nullable=False)

    # Origine
    from_location_id = Column(UniversalUUID())
    from_location_name = Column(String(200))
    from_responsible_id = Column(UniversalUUID())
    from_responsible_name = Column(String(200))
    from_department_id = Column(UniversalUUID())
    from_cost_center = Column(String(50))

    # Destination
    to_location_id = Column(UniversalUUID())
    to_location_name = Column(String(200))
    to_responsible_id = Column(UniversalUUID())
    to_responsible_name = Column(String(200))
    to_department_id = Column(UniversalUUID())
    to_cost_center = Column(String(50))

    # Motif
    reason = Column(Text)

    # Statut
    status = Column(String(20), default="PENDING")  # PENDING, APPROVED, COMPLETED, CANCELLED
    approved_by = Column(UniversalUUID())
    approved_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Signatures
    sender_signature = Column(String(500))  # URL ou base64
    receiver_signature = Column(String(500))

    # Documents
    documents = Column(JSONB, default=list)

    # Notes
    notes = Column(Text)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(UniversalUUID())
    version = Column(Integer, default=1)

    # Relations
    asset = relationship("FixedAsset", back_populates="transfers")


# ============================================================================
# MODELES - EXECUTION AMORTISSEMENTS
# ============================================================================

class DepreciationRun(Base):
    """Execution batch des amortissements."""
    __tablename__ = "asset_depreciation_runs"
    __table_args__ = (
        Index("idx_depr_run_tenant", "tenant_id"),
        Index("idx_depr_run_date", "run_date"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    run_number = Column(String(50), nullable=False)
    run_date = Column(Date, nullable=False)
    description = Column(Text)

    # Periode
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    fiscal_year = Column(Integer)
    period_number = Column(Integer)  # Mois 1-12

    # Resultats
    assets_processed = Column(Integer, default=0)
    total_depreciation = Column(Numeric(18, 2), default=0)
    total_fiscal_depreciation = Column(Numeric(18, 2), default=0)
    errors_count = Column(Integer, default=0)

    # Details
    entries = Column(JSONB, default=list)  # Liste des ecritures generees
    errors = Column(JSONB, default=list)  # Liste des erreurs

    # Statut
    status = Column(String(20), default="DRAFT")  # DRAFT, VALIDATED, POSTED, CANCELLED
    validated_at = Column(DateTime)
    validated_by = Column(UniversalUUID())
    posted_at = Column(DateTime)
    posted_by = Column(UniversalUUID())
    journal_batch_id = Column(UniversalUUID())

    # Notes
    notes = Column(Text)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(UniversalUUID())
    version = Column(Integer, default=1)


# ============================================================================
# MODELES - VALORISATION
# ============================================================================

class AssetValuation(Base):
    """Snapshot de valorisation du parc immobilier."""
    __tablename__ = "asset_valuations"
    __table_args__ = (
        Index("idx_asset_val_tenant", "tenant_id"),
        Index("idx_asset_val_date", "valuation_date"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Date
    valuation_date = Column(Date, nullable=False)
    fiscal_year = Column(Integer)
    period = Column(String(20))  # YYYY-MM ou YYYY

    # Totaux
    total_assets_count = Column(Integer, default=0)
    total_gross_value = Column(Numeric(18, 2), default=0)
    total_accumulated_depreciation = Column(Numeric(18, 2), default=0)
    total_net_book_value = Column(Numeric(18, 2), default=0)
    total_impairment = Column(Numeric(18, 2), default=0)
    total_revaluation_surplus = Column(Numeric(18, 2), default=0)

    # Par type
    by_asset_type = Column(JSONB, default=dict)

    # Par categorie
    by_category = Column(JSONB, default=dict)

    # Par localisation
    by_location = Column(JSONB, default=dict)

    # Par departement
    by_department = Column(JSONB, default=dict)

    # Devise
    currency = Column(String(3), default="EUR")

    # Notes
    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())
