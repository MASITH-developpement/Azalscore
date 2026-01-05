"""
AZALS MODULE M5 - Modèles Inventaire
=====================================

Modèles SQLAlchemy pour la gestion des stocks et logistique.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Text, Boolean, ForeignKey,
    Integer, Numeric, Date, Enum as SQLEnum, Index, UniqueConstraint
)
from app.core.types import UniversalUUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class ProductType(str, enum.Enum):
    """Types de produit."""
    STOCKABLE = "STOCKABLE"
    CONSUMABLE = "CONSUMABLE"
    SERVICE = "SERVICE"


class ProductStatus(str, enum.Enum):
    """Statuts produit."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DISCONTINUED = "DISCONTINUED"
    BLOCKED = "BLOCKED"


class WarehouseType(str, enum.Enum):
    """Types d'entrepôt."""
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
    TRANSIT = "TRANSIT"
    VIRTUAL = "VIRTUAL"


class LocationType(str, enum.Enum):
    """Types d'emplacement."""
    STORAGE = "STORAGE"
    RECEIVING = "RECEIVING"
    SHIPPING = "SHIPPING"
    PRODUCTION = "PRODUCTION"
    QUALITY = "QUALITY"
    VIRTUAL = "VIRTUAL"


class MovementType(str, enum.Enum):
    """Types de mouvement de stock."""
    IN = "IN"
    OUT = "OUT"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"
    PRODUCTION = "PRODUCTION"
    RETURN = "RETURN"
    SCRAP = "SCRAP"


class MovementStatus(str, enum.Enum):
    """Statuts de mouvement."""
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class InventoryStatus(str, enum.Enum):
    """Statuts d'inventaire."""
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    VALIDATED = "VALIDATED"
    CANCELLED = "CANCELLED"


class LotStatus(str, enum.Enum):
    """Statuts de lot."""
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"


class ValuationMethod(str, enum.Enum):
    """Méthodes de valorisation."""
    FIFO = "FIFO"
    LIFO = "LIFO"
    AVG = "AVG"
    STANDARD = "STANDARD"


class PickingStatus(str, enum.Enum):
    """Statuts de préparation."""
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


# ============================================================================
# CATÉGORIES DE PRODUITS
# ============================================================================

class ProductCategory(Base):
    """Catégorie de produits."""
    __tablename__ = "inventory_categories"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(UniversalUUID(), ForeignKey("inventory_categories.id"), nullable=True)

    # Configuration par défaut
    default_valuation = Column(SQLEnum(ValuationMethod), default=ValuationMethod.AVG)
    default_account_id = Column(UniversalUUID(), nullable=True)

    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='unique_category_code'),
        Index('idx_categories_tenant', 'tenant_id'),
        Index('idx_categories_parent', 'tenant_id', 'parent_id'),
    )


# ============================================================================
# ENTREPÔTS ET EMPLACEMENTS
# ============================================================================

class Warehouse(Base):
    """Entrepôt."""
    __tablename__ = "inventory_warehouses"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(SQLEnum(WarehouseType), default=WarehouseType.INTERNAL)

    # Adresse
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    postal_code = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), default="France")

    # Contact
    manager_name = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)

    # Configuration
    is_default = Column(Boolean, default=False)
    allow_negative = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='unique_warehouse_code'),
        Index('idx_warehouses_tenant', 'tenant_id'),
    )


class Location(Base):
    """Emplacement de stockage."""
    __tablename__ = "inventory_locations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    warehouse_id = Column(UniversalUUID(), ForeignKey("inventory_warehouses.id"), nullable=False)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(SQLEnum(LocationType), default=LocationType.STORAGE)

    # Hiérarchie (allée/rangée/niveau)
    aisle = Column(String(20), nullable=True)
    rack = Column(String(20), nullable=True)
    level = Column(String(20), nullable=True)
    position = Column(String(20), nullable=True)

    # Capacité
    max_weight_kg = Column(Numeric(10, 2), nullable=True)
    max_volume_m3 = Column(Numeric(10, 3), nullable=True)

    # Configuration
    is_default = Column(Boolean, default=False)
    requires_lot = Column(Boolean, default=False)
    requires_serial = Column(Boolean, default=False)

    barcode = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    warehouse = relationship("Warehouse", foreign_keys=[warehouse_id])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'warehouse_id', 'code', name='unique_location_code'),
        Index('idx_locations_tenant', 'tenant_id'),
        Index('idx_locations_warehouse', 'tenant_id', 'warehouse_id'),
        Index('idx_locations_barcode', 'tenant_id', 'barcode'),
    )


# ============================================================================
# PRODUITS
# ============================================================================

class Product(Base):
    """Produit/Article."""
    __tablename__ = "inventory_products"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(100), nullable=False)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(SQLEnum(ProductType), default=ProductType.STOCKABLE)
    status = Column(SQLEnum(ProductStatus), default=ProductStatus.DRAFT)

    # Classification
    category_id = Column(UniversalUUID(), ForeignKey("inventory_categories.id"), nullable=True)

    # Codes
    barcode = Column(String(100), nullable=True)
    ean13 = Column(String(13), nullable=True)
    sku = Column(String(100), nullable=True)
    manufacturer_code = Column(String(100), nullable=True)

    # Unités
    unit = Column(String(20), default="UNIT")
    purchase_unit = Column(String(20), nullable=True)
    purchase_unit_factor = Column(Numeric(10, 4), default=1)
    sale_unit = Column(String(20), nullable=True)
    sale_unit_factor = Column(Numeric(10, 4), default=1)

    # Prix et coûts
    standard_cost = Column(Numeric(15, 4), default=0)
    average_cost = Column(Numeric(15, 4), default=0)
    last_purchase_price = Column(Numeric(15, 4), nullable=True)
    sale_price = Column(Numeric(15, 4), nullable=True)
    currency = Column(String(3), default="EUR")

    # Valorisation
    valuation_method = Column(SQLEnum(ValuationMethod), default=ValuationMethod.AVG)

    # Stock
    min_stock = Column(Numeric(15, 4), default=0)
    max_stock = Column(Numeric(15, 4), nullable=True)
    reorder_point = Column(Numeric(15, 4), nullable=True)
    reorder_quantity = Column(Numeric(15, 4), nullable=True)
    lead_time_days = Column(Integer, default=0)

    # Dimensions
    weight_kg = Column(Numeric(10, 4), nullable=True)
    volume_m3 = Column(Numeric(10, 6), nullable=True)
    length_cm = Column(Numeric(10, 2), nullable=True)
    width_cm = Column(Numeric(10, 2), nullable=True)
    height_cm = Column(Numeric(10, 2), nullable=True)

    # Suivi
    track_lot = Column(Boolean, default=False)
    track_serial = Column(Boolean, default=False)
    track_expiry = Column(Boolean, default=False)
    expiry_warning_days = Column(Integer, default=30)

    # Entrepôt par défaut
    default_warehouse_id = Column(UniversalUUID(), ForeignKey("inventory_warehouses.id"), nullable=True)
    default_location_id = Column(UniversalUUID(), ForeignKey("inventory_locations.id"), nullable=True)

    # Fournisseur principal
    default_supplier_id = Column(UniversalUUID(), nullable=True)

    # Comptabilité
    stock_account_id = Column(UniversalUUID(), nullable=True)
    expense_account_id = Column(UniversalUUID(), nullable=True)
    income_account_id = Column(UniversalUUID(), nullable=True)

    # Métadonnées
    tags = Column(JSONB, default=list)
    custom_fields = Column(JSONB, default=dict)
    image_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)
    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("ProductCategory", foreign_keys=[category_id])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='unique_product_code'),
        Index('idx_products_tenant', 'tenant_id'),
        Index('idx_products_category', 'tenant_id', 'category_id'),
        Index('idx_products_status', 'tenant_id', 'status'),
        Index('idx_products_barcode', 'tenant_id', 'barcode'),
        Index('idx_products_sku', 'tenant_id', 'sku'),
    )


# ============================================================================
# STOCK PAR EMPLACEMENT
# ============================================================================

class StockLevel(Base):
    """Niveau de stock par produit/emplacement."""
    __tablename__ = "inventory_stock_levels"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    product_id = Column(UniversalUUID(), ForeignKey("inventory_products.id"), nullable=False)
    warehouse_id = Column(UniversalUUID(), ForeignKey("inventory_warehouses.id"), nullable=False)
    location_id = Column(UniversalUUID(), ForeignKey("inventory_locations.id"), nullable=True)

    # Quantités
    quantity_on_hand = Column(Numeric(15, 4), default=0)
    quantity_reserved = Column(Numeric(15, 4), default=0)
    quantity_available = Column(Numeric(15, 4), default=0)
    quantity_incoming = Column(Numeric(15, 4), default=0)
    quantity_outgoing = Column(Numeric(15, 4), default=0)

    # Valorisation
    total_value = Column(Numeric(15, 2), default=0)
    average_cost = Column(Numeric(15, 4), default=0)

    last_movement_at = Column(DateTime, nullable=True)
    last_count_at = Column(DateTime, nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", foreign_keys=[product_id])
    warehouse = relationship("Warehouse", foreign_keys=[warehouse_id])
    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'product_id', 'warehouse_id', 'location_id',
                         name='unique_stock_level'),
        Index('idx_stock_levels_tenant', 'tenant_id'),
        Index('idx_stock_levels_product', 'tenant_id', 'product_id'),
        Index('idx_stock_levels_warehouse', 'tenant_id', 'warehouse_id'),
    )


# ============================================================================
# LOTS ET NUMÉROS DE SÉRIE
# ============================================================================

class Lot(Base):
    """Lot de produit."""
    __tablename__ = "inventory_lots"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    product_id = Column(UniversalUUID(), ForeignKey("inventory_products.id"), nullable=False)
    number = Column(String(100), nullable=False)
    status = Column(SQLEnum(LotStatus), default=LotStatus.AVAILABLE)

    # Dates
    production_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    reception_date = Column(Date, nullable=True)

    # Origine
    supplier_id = Column(UniversalUUID(), nullable=True)
    supplier_lot = Column(String(100), nullable=True)
    purchase_order_id = Column(UniversalUUID(), nullable=True)

    # Quantités
    initial_quantity = Column(Numeric(15, 4), default=0)
    current_quantity = Column(Numeric(15, 4), default=0)

    # Coût
    unit_cost = Column(Numeric(15, 4), nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", foreign_keys=[product_id])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'product_id', 'number', name='unique_lot_number'),
        Index('idx_lots_tenant', 'tenant_id'),
        Index('idx_lots_product', 'tenant_id', 'product_id'),
        Index('idx_lots_expiry', 'tenant_id', 'expiry_date'),
        Index('idx_lots_status', 'tenant_id', 'status'),
    )


class SerialNumber(Base):
    """Numéro de série."""
    __tablename__ = "inventory_serial_numbers"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    product_id = Column(UniversalUUID(), ForeignKey("inventory_products.id"), nullable=False)
    lot_id = Column(UniversalUUID(), ForeignKey("inventory_lots.id"), nullable=True)
    number = Column(String(100), nullable=False)
    status = Column(SQLEnum(LotStatus), default=LotStatus.AVAILABLE)

    # Localisation actuelle
    warehouse_id = Column(UniversalUUID(), ForeignKey("inventory_warehouses.id"), nullable=True)
    location_id = Column(UniversalUUID(), ForeignKey("inventory_locations.id"), nullable=True)

    # Origine
    supplier_id = Column(UniversalUUID(), nullable=True)
    purchase_order_id = Column(UniversalUUID(), nullable=True)
    reception_date = Column(Date, nullable=True)

    # Client (si vendu)
    customer_id = Column(UniversalUUID(), nullable=True)
    sale_order_id = Column(UniversalUUID(), nullable=True)
    sale_date = Column(Date, nullable=True)

    # Garantie
    warranty_end_date = Column(Date, nullable=True)

    unit_cost = Column(Numeric(15, 4), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", foreign_keys=[product_id])
    lot = relationship("Lot", foreign_keys=[lot_id])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'product_id', 'number', name='unique_serial_number'),
        Index('idx_serials_tenant', 'tenant_id'),
        Index('idx_serials_product', 'tenant_id', 'product_id'),
        Index('idx_serials_status', 'tenant_id', 'status'),
    )


# ============================================================================
# MOUVEMENTS DE STOCK
# ============================================================================

class StockMovement(Base):
    """Mouvement de stock."""
    __tablename__ = "inventory_movements"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    number = Column(String(50), nullable=False)
    type = Column(SQLEnum(MovementType), nullable=False)
    status = Column(SQLEnum(MovementStatus), default=MovementStatus.DRAFT)

    # Date
    movement_date = Column(DateTime, nullable=False)

    # Origine/Destination
    from_warehouse_id = Column(UniversalUUID(), ForeignKey("inventory_warehouses.id"), nullable=True)
    from_location_id = Column(UniversalUUID(), ForeignKey("inventory_locations.id"), nullable=True)
    to_warehouse_id = Column(UniversalUUID(), ForeignKey("inventory_warehouses.id"), nullable=True)
    to_location_id = Column(UniversalUUID(), ForeignKey("inventory_locations.id"), nullable=True)

    # Référence
    reference_type = Column(String(50), nullable=True)  # purchase_order, sale_order, production_order
    reference_id = Column(UniversalUUID(), nullable=True)
    reference_number = Column(String(100), nullable=True)

    reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Totaux
    total_items = Column(Integer, default=0)
    total_quantity = Column(Numeric(15, 4), default=0)
    total_value = Column(Numeric(15, 2), default=0)

    created_by = Column(UniversalUUID(), nullable=True)
    confirmed_by = Column(UniversalUUID(), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'number', name='unique_movement_number'),
        Index('idx_movements_tenant', 'tenant_id'),
        Index('idx_movements_type', 'tenant_id', 'type'),
        Index('idx_movements_status', 'tenant_id', 'status'),
        Index('idx_movements_date', 'tenant_id', 'movement_date'),
        Index('idx_movements_reference', 'tenant_id', 'reference_type', 'reference_id'),
    )


class StockMovementLine(Base):
    """Ligne de mouvement de stock."""
    __tablename__ = "inventory_movement_lines"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    movement_id = Column(UniversalUUID(), ForeignKey("inventory_movements.id"), nullable=False)

    line_number = Column(Integer, nullable=False)
    product_id = Column(UniversalUUID(), ForeignKey("inventory_products.id"), nullable=False)

    # Quantités
    quantity = Column(Numeric(15, 4), nullable=False)
    unit = Column(String(20), default="UNIT")

    # Lot/Série
    lot_id = Column(UniversalUUID(), ForeignKey("inventory_lots.id"), nullable=True)
    serial_id = Column(UniversalUUID(), ForeignKey("inventory_serial_numbers.id"), nullable=True)

    # Emplacements spécifiques (si différent du mouvement parent)
    from_location_id = Column(UniversalUUID(), ForeignKey("inventory_locations.id"), nullable=True)
    to_location_id = Column(UniversalUUID(), ForeignKey("inventory_locations.id"), nullable=True)

    # Valorisation
    unit_cost = Column(Numeric(15, 4), nullable=True)
    total_cost = Column(Numeric(15, 2), nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    movement = relationship("StockMovement", foreign_keys=[movement_id])
    product = relationship("Product", foreign_keys=[product_id])
    lot = relationship("Lot", foreign_keys=[lot_id])

    __table_args__ = (
        Index('idx_movement_lines_movement', 'movement_id'),
        Index('idx_movement_lines_tenant', 'tenant_id'),
        Index('idx_movement_lines_product', 'tenant_id', 'product_id'),
    )


# ============================================================================
# INVENTAIRES PHYSIQUES
# ============================================================================

class InventoryCount(Base):
    """Inventaire physique."""
    __tablename__ = "inventory_counts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    number = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    status = Column(SQLEnum(InventoryStatus), default=InventoryStatus.DRAFT)

    # Périmètre
    warehouse_id = Column(UniversalUUID(), ForeignKey("inventory_warehouses.id"), nullable=True)
    location_id = Column(UniversalUUID(), ForeignKey("inventory_locations.id"), nullable=True)
    category_id = Column(UniversalUUID(), ForeignKey("inventory_categories.id"), nullable=True)

    # Dates
    planned_date = Column(Date, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Résumé
    total_items = Column(Integer, default=0)
    counted_items = Column(Integer, default=0)
    discrepancy_items = Column(Integer, default=0)
    total_discrepancy_value = Column(Numeric(15, 2), default=0)

    notes = Column(Text, nullable=True)

    created_by = Column(UniversalUUID(), nullable=True)
    validated_by = Column(UniversalUUID(), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'number', name='unique_count_number'),
        Index('idx_counts_tenant', 'tenant_id'),
        Index('idx_counts_status', 'tenant_id', 'status'),
        Index('idx_counts_warehouse', 'tenant_id', 'warehouse_id'),
    )


class InventoryCountLine(Base):
    """Ligne d'inventaire physique."""
    __tablename__ = "inventory_count_lines"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    count_id = Column(UniversalUUID(), ForeignKey("inventory_counts.id"), nullable=False)

    product_id = Column(UniversalUUID(), ForeignKey("inventory_products.id"), nullable=False)
    location_id = Column(UniversalUUID(), ForeignKey("inventory_locations.id"), nullable=True)
    lot_id = Column(UniversalUUID(), ForeignKey("inventory_lots.id"), nullable=True)

    # Quantités
    theoretical_quantity = Column(Numeric(15, 4), default=0)
    counted_quantity = Column(Numeric(15, 4), nullable=True)
    discrepancy = Column(Numeric(15, 4), nullable=True)

    # Valorisation
    unit_cost = Column(Numeric(15, 4), nullable=True)
    discrepancy_value = Column(Numeric(15, 2), nullable=True)

    counted_at = Column(DateTime, nullable=True)
    counted_by = Column(UniversalUUID(), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    count = relationship("InventoryCount", foreign_keys=[count_id])
    product = relationship("Product", foreign_keys=[product_id])

    __table_args__ = (
        Index('idx_count_lines_count', 'count_id'),
        Index('idx_count_lines_tenant', 'tenant_id'),
        Index('idx_count_lines_product', 'tenant_id', 'product_id'),
    )


# ============================================================================
# PRÉPARATION DE COMMANDES (PICKING)
# ============================================================================

class Picking(Base):
    """Préparation de commande."""
    __tablename__ = "inventory_pickings"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    number = Column(String(50), nullable=False)
    type = Column(SQLEnum(MovementType), default=MovementType.OUT)
    status = Column(SQLEnum(PickingStatus), default=PickingStatus.PENDING)

    # Entrepôt
    warehouse_id = Column(UniversalUUID(), ForeignKey("inventory_warehouses.id"), nullable=False)

    # Référence
    reference_type = Column(String(50), nullable=True)  # sale_order, purchase_order, transfer
    reference_id = Column(UniversalUUID(), nullable=True)
    reference_number = Column(String(100), nullable=True)

    # Dates
    scheduled_date = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Assignation
    assigned_to = Column(UniversalUUID(), nullable=True)

    # Totaux
    total_lines = Column(Integer, default=0)
    picked_lines = Column(Integer, default=0)

    priority = Column(String(20), default="NORMAL")
    notes = Column(Text, nullable=True)

    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'number', name='unique_picking_number'),
        Index('idx_pickings_tenant', 'tenant_id'),
        Index('idx_pickings_status', 'tenant_id', 'status'),
        Index('idx_pickings_assigned', 'tenant_id', 'assigned_to'),
        Index('idx_pickings_reference', 'tenant_id', 'reference_type', 'reference_id'),
    )


class PickingLine(Base):
    """Ligne de préparation."""
    __tablename__ = "inventory_picking_lines"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    picking_id = Column(UniversalUUID(), ForeignKey("inventory_pickings.id"), nullable=False)

    product_id = Column(UniversalUUID(), ForeignKey("inventory_products.id"), nullable=False)
    location_id = Column(UniversalUUID(), ForeignKey("inventory_locations.id"), nullable=True)

    # Quantités
    quantity_demanded = Column(Numeric(15, 4), nullable=False)
    quantity_picked = Column(Numeric(15, 4), default=0)
    unit = Column(String(20), default="UNIT")

    # Lot/Série
    lot_id = Column(UniversalUUID(), ForeignKey("inventory_lots.id"), nullable=True)
    serial_id = Column(UniversalUUID(), ForeignKey("inventory_serial_numbers.id"), nullable=True)

    is_picked = Column(Boolean, default=False)
    picked_at = Column(DateTime, nullable=True)
    picked_by = Column(UniversalUUID(), nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    picking = relationship("Picking", foreign_keys=[picking_id])
    product = relationship("Product", foreign_keys=[product_id])

    __table_args__ = (
        Index('idx_picking_lines_picking', 'picking_id'),
        Index('idx_picking_lines_tenant', 'tenant_id'),
        Index('idx_picking_lines_product', 'tenant_id', 'product_id'),
    )


# ============================================================================
# RÉAPPROVISIONNEMENT
# ============================================================================

class ReplenishmentRule(Base):
    """Règle de réapprovisionnement."""
    __tablename__ = "inventory_replenishment_rules"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    product_id = Column(UniversalUUID(), ForeignKey("inventory_products.id"), nullable=False)
    warehouse_id = Column(UniversalUUID(), ForeignKey("inventory_warehouses.id"), nullable=True)

    # Seuils
    min_stock = Column(Numeric(15, 4), nullable=False)
    max_stock = Column(Numeric(15, 4), nullable=True)
    reorder_point = Column(Numeric(15, 4), nullable=False)
    reorder_quantity = Column(Numeric(15, 4), nullable=False)

    # Fournisseur préféré
    supplier_id = Column(UniversalUUID(), nullable=True)
    lead_time_days = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", foreign_keys=[product_id])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'product_id', 'warehouse_id', name='unique_replenishment_rule'),
        Index('idx_replenishment_tenant', 'tenant_id'),
        Index('idx_replenishment_product', 'tenant_id', 'product_id'),
    )


# ============================================================================
# VALORISATION DES STOCKS
# ============================================================================

class StockValuation(Base):
    """Valorisation des stocks."""
    __tablename__ = "inventory_valuations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    valuation_date = Column(Date, nullable=False)
    warehouse_id = Column(UniversalUUID(), ForeignKey("inventory_warehouses.id"), nullable=True)

    # Totaux
    total_products = Column(Integer, default=0)
    total_quantity = Column(Numeric(15, 4), default=0)
    total_value = Column(Numeric(15, 2), default=0)

    # Par méthode
    value_fifo = Column(Numeric(15, 2), default=0)
    value_lifo = Column(Numeric(15, 2), default=0)
    value_avg = Column(Numeric(15, 2), default=0)
    value_standard = Column(Numeric(15, 2), default=0)

    # Détails
    details = Column(JSONB, default=list)

    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_valuations_tenant', 'tenant_id'),
        Index('idx_valuations_date', 'tenant_id', 'valuation_date'),
        Index('idx_valuations_warehouse', 'tenant_id', 'warehouse_id'),
    )
