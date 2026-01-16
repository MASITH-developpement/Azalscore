"""
AZALS MODULE M5 - Schémas Inventaire
=====================================

Schémas Pydantic pour la gestion des stocks et logistique.
"""


import json
import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import (
    InventoryStatus,
    LocationType,
    LotStatus,
    MovementStatus,
    MovementType,
    PickingStatus,
    ProductStatus,
    ProductType,
    ValuationMethod,
    WarehouseType,
)

# ============================================================================
# CATÉGORIES
# ============================================================================

class CategoryCreate(BaseModel):
    """Création d'une catégorie."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    parent_id: UUID | None = None
    default_valuation: ValuationMethod = ValuationMethod.AVG
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    """Mise à jour d'une catégorie."""
    name: str | None = None
    description: str | None = None
    parent_id: UUID | None = None
    default_valuation: ValuationMethod | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryResponse(CategoryCreate):
    """Réponse catégorie."""
    id: UUID
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ENTREPÔTS
# ============================================================================

class WarehouseCreate(BaseModel):
    """Création d'un entrepôt."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    warehouse_type: WarehouseType = Field(default=WarehouseType.INTERNAL, alias="type")
    address_line1: str | None = None
    address_line2: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str = "France"
    manager_name: str | None = None
    phone: str | None = None
    email: str | None = None
    is_default: bool = False
    allow_negative: bool = False
    notes: str | None = None


class WarehouseUpdate(BaseModel):
    """Mise à jour d'un entrepôt."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    name: str | None = None
    warehouse_type: WarehouseType | None = Field(default=None, alias="type")
    address_line1: str | None = None
    address_line2: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str | None = None
    manager_name: str | None = None
    phone: str | None = None
    email: str | None = None
    is_default: bool | None = None
    allow_negative: bool | None = None
    notes: str | None = None
    is_active: bool | None = None


class WarehouseResponse(WarehouseCreate):
    """Réponse entrepôt."""
    id: UUID
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime



# ============================================================================
# EMPLACEMENTS
# ============================================================================

class LocationCreate(BaseModel):
    """Création d'un emplacement."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    location_type: LocationType = Field(default=LocationType.STORAGE, alias="type")
    aisle: str | None = None
    rack: str | None = None
    level: str | None = None
    position: str | None = None
    max_weight_kg: Decimal | None = None
    max_volume_m3: Decimal | None = None
    is_default: bool = False
    requires_lot: bool = False
    requires_serial: bool = False
    barcode: str | None = None
    notes: str | None = None


class LocationUpdate(BaseModel):
    """Mise à jour d'un emplacement."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    name: str | None = None
    location_type: LocationType | None = Field(default=None, alias="type")
    aisle: str | None = None
    rack: str | None = None
    level: str | None = None
    position: str | None = None
    max_weight_kg: Decimal | None = None
    max_volume_m3: Decimal | None = None
    is_default: bool | None = None
    requires_lot: bool | None = None
    requires_serial: bool | None = None
    barcode: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class LocationResponse(LocationCreate):
    """Réponse emplacement."""
    id: UUID
    warehouse_id: UUID
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime



# ============================================================================
# PRODUITS
# ============================================================================

class ProductCreate(BaseModel):
    """Création d'un produit."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    product_type: ProductType = Field(default=ProductType.STOCKABLE, alias="type")
    category_id: UUID | None = None
    barcode: str | None = None
    ean13: str | None = None
    sku: str | None = None
    unit: str = "UNIT"
    purchase_unit: str | None = None
    purchase_unit_factor: Decimal = Decimal("1")
    sale_unit: str | None = None
    sale_unit_factor: Decimal = Decimal("1")
    standard_cost: Decimal = Decimal("0")
    sale_price: Decimal | None = None
    currency: str = "EUR"
    valuation_method: ValuationMethod = ValuationMethod.AVG
    min_stock: Decimal = Decimal("0")
    max_stock: Decimal | None = None
    reorder_point: Decimal | None = None
    reorder_quantity: Decimal | None = None
    lead_time_days: int = 0
    weight_kg: Decimal | None = None
    volume_m3: Decimal | None = None
    length_cm: Decimal | None = None
    width_cm: Decimal | None = None
    height_cm: Decimal | None = None
    track_lot: bool = False
    track_serial: bool = False
    track_expiry: bool = False
    expiry_warning_days: int = 30
    default_warehouse_id: UUID | None = None
    default_location_id: UUID | None = None
    default_supplier_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)
    image_url: str | None = None
    notes: str | None = None


class ProductUpdate(BaseModel):
    """Mise à jour d'un produit."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    name: str | None = None
    description: str | None = None
    product_type: ProductType | None = Field(default=None, alias="type")
    status: ProductStatus | None = None
    category_id: UUID | None = None
    barcode: str | None = None
    ean13: str | None = None
    sku: str | None = None
    unit: str | None = None
    purchase_unit: str | None = None
    purchase_unit_factor: Decimal | None = None
    sale_unit: str | None = None
    sale_unit_factor: Decimal | None = None
    standard_cost: Decimal | None = None
    sale_price: Decimal | None = None
    valuation_method: ValuationMethod | None = None
    min_stock: Decimal | None = None
    max_stock: Decimal | None = None
    reorder_point: Decimal | None = None
    reorder_quantity: Decimal | None = None
    lead_time_days: int | None = None
    weight_kg: Decimal | None = None
    volume_m3: Decimal | None = None
    track_lot: bool | None = None
    track_serial: bool | None = None
    track_expiry: bool | None = None
    expiry_warning_days: int | None = None
    default_warehouse_id: UUID | None = None
    default_location_id: UUID | None = None
    default_supplier_id: UUID | None = None
    tags: list[str] | None = None
    image_url: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    """Réponse produit."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True, populate_by_name=True)

    id: UUID
    code: str
    name: str
    description: str | None
    product_type: ProductType = Field(..., alias="type")
    status: ProductStatus
    category_id: UUID | None
    barcode: str | None
    ean13: str | None
    sku: str | None
    unit: str
    standard_cost: Decimal
    average_cost: Decimal
    sale_price: Decimal | None
    currency: str
    valuation_method: ValuationMethod
    min_stock: Decimal
    max_stock: Decimal | None
    reorder_point: Decimal | None
    lead_time_days: int
    weight_kg: Decimal | None
    track_lot: bool
    track_serial: bool
    track_expiry: bool
    tags: list[str]
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class ProductList(BaseModel):
    """Liste de produits."""
    items: list[ProductResponse]
    total: int


# ============================================================================
# NIVEAUX DE STOCK
# ============================================================================

class StockLevelResponse(BaseModel):
    """Réponse niveau de stock."""
    id: UUID
    product_id: UUID
    warehouse_id: UUID
    location_id: UUID | None
    quantity_on_hand: Decimal
    quantity_reserved: Decimal
    quantity_available: Decimal
    quantity_incoming: Decimal
    quantity_outgoing: Decimal
    total_value: Decimal
    average_cost: Decimal
    last_movement_at: datetime.datetime | None
    last_count_at: datetime.datetime | None
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class StockLevelUpdate(BaseModel):
    """Mise à jour niveau de stock."""
    quantity_on_hand: Decimal | None = None
    quantity_reserved: Decimal | None = None
    quantity_incoming: Decimal | None = None
    quantity_outgoing: Decimal | None = None
    last_movement_at: datetime.datetime | None = None
    last_count_at: datetime.datetime | None = None


class StockByProduct(BaseModel):
    """Stock agrégé par produit."""
    product_id: UUID
    product_code: str
    product_name: str
    total_on_hand: Decimal
    total_reserved: Decimal
    total_available: Decimal
    total_value: Decimal
    warehouses: list[dict[str, Any]]


# ============================================================================
# LOTS
# ============================================================================

class LotCreate(BaseModel):
    """Création d'un lot."""
    product_id: UUID
    number: str = Field(..., min_length=1, max_length=100)
    production_date: datetime.date | None = None
    expiry_date: datetime.date | None = None
    reception_date: datetime.date | None = None
    supplier_id: UUID | None = None
    supplier_lot: str | None = None
    initial_quantity: Decimal
    unit_cost: Decimal | None = None
    notes: str | None = None


class LotUpdate(BaseModel):
    """Mise à jour d'un lot."""
    status: LotStatus | None = None
    expiry_date: datetime.date | None = None
    notes: str | None = None


class LotResponse(BaseModel):
    """Réponse lot."""
    id: UUID
    product_id: UUID
    number: str
    status: LotStatus
    production_date: datetime.date | None
    expiry_date: datetime.date | None
    reception_date: datetime.date | None
    supplier_id: UUID | None
    supplier_lot: str | None
    initial_quantity: Decimal
    current_quantity: Decimal
    unit_cost: Decimal | None
    notes: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# NUMÉROS DE SÉRIE
# ============================================================================

class SerialCreate(BaseModel):
    """Création d'un numéro de série."""
    product_id: UUID
    number: str = Field(..., min_length=1, max_length=100)
    lot_id: UUID | None = None
    warehouse_id: UUID | None = None
    location_id: UUID | None = None
    supplier_id: UUID | None = None
    reception_date: datetime.date | None = None
    warranty_end_date: datetime.date | None = None
    unit_cost: Decimal | None = None
    notes: str | None = None


class SerialUpdate(BaseModel):
    """Mise à jour d'un numéro de série."""
    status: LotStatus | None = None
    warehouse_id: UUID | None = None
    location_id: UUID | None = None
    warranty_end_date: datetime.date | None = None
    notes: str | None = None


class SerialResponse(BaseModel):
    """Réponse numéro de série."""
    id: UUID
    product_id: UUID
    lot_id: UUID | None
    number: str
    status: LotStatus
    warehouse_id: UUID | None
    location_id: UUID | None
    supplier_id: UUID | None
    reception_date: datetime.date | None
    customer_id: UUID | None
    sale_date: datetime.date | None
    warranty_end_date: datetime.date | None
    unit_cost: Decimal | None
    notes: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# MOUVEMENTS DE STOCK
# ============================================================================

class MovementLineCreate(BaseModel):
    """Création d'une ligne de mouvement."""
    product_id: UUID
    quantity: Decimal
    unit: str = "UNIT"
    lot_id: UUID | None = None
    serial_id: UUID | None = None
    from_location_id: UUID | None = None
    to_location_id: UUID | None = None
    unit_cost: Decimal | None = None
    notes: str | None = None


class MovementLineResponse(MovementLineCreate):
    """Réponse ligne de mouvement."""
    id: UUID
    movement_id: UUID
    line_number: int
    total_cost: Decimal | None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class MovementCreate(BaseModel):
    """Création d'un mouvement."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    movement_type: MovementType = Field(..., alias="type")
    movement_date: datetime.datetime
    from_warehouse_id: UUID | None = None
    from_location_id: UUID | None = None
    to_warehouse_id: UUID | None = None
    to_location_id: UUID | None = None
    reference_type: str | None = None
    reference_id: UUID | None = None
    reference_number: str | None = None
    reason: str | None = None
    notes: str | None = None
    lines: list[MovementLineCreate] = Field(default_factory=list)


class MovementResponse(BaseModel):
    """Réponse mouvement."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True, populate_by_name=True)

    id: UUID
    number: str
    movement_type: MovementType = Field(..., alias="type")
    status: MovementStatus
    movement_date: datetime.datetime
    from_warehouse_id: UUID | None
    from_location_id: UUID | None
    to_warehouse_id: UUID | None
    to_location_id: UUID | None
    reference_type: str | None
    reference_id: UUID | None
    reference_number: str | None
    reason: str | None
    notes: str | None
    total_items: int
    total_quantity: Decimal
    total_value: Decimal
    confirmed_at: datetime.datetime | None
    lines: list[MovementLineResponse] = Field(default_factory=list)
    created_at: datetime.datetime
    updated_at: datetime.datetime



class MovementList(BaseModel):
    """Liste de mouvements."""
    items: list[MovementResponse]
    total: int


# ============================================================================
# INVENTAIRES PHYSIQUES
# ============================================================================

class CountLineCreate(BaseModel):
    """Création d'une ligne d'inventaire."""
    product_id: UUID
    location_id: UUID | None = None
    lot_id: UUID | None = None
    theoretical_quantity: Decimal = Decimal("0")
    counted_quantity: Decimal | None = None
    notes: str | None = None


class CountLineUpdate(BaseModel):
    """Mise à jour d'une ligne d'inventaire."""
    counted_quantity: Decimal
    notes: str | None = None


class CountLineResponse(BaseModel):
    """Réponse ligne d'inventaire."""
    id: UUID
    count_id: UUID
    product_id: UUID
    location_id: UUID | None
    lot_id: UUID | None
    theoretical_quantity: Decimal
    counted_quantity: Decimal | None
    discrepancy: Decimal | None
    unit_cost: Decimal | None
    discrepancy_value: Decimal | None
    counted_at: datetime.datetime | None
    counted_by: UUID | None
    notes: str | None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryCountCreate(BaseModel):
    """Création d'un inventaire."""
    name: str = Field(..., min_length=1, max_length=200)
    warehouse_id: UUID | None = None
    location_id: UUID | None = None
    category_id: UUID | None = None
    planned_date: datetime.date
    notes: str | None = None


class InventoryCountResponse(BaseModel):
    """Réponse inventaire."""
    id: UUID
    number: str
    name: str
    status: InventoryStatus
    warehouse_id: UUID | None
    location_id: UUID | None
    category_id: UUID | None
    planned_date: datetime.date
    started_at: datetime.datetime | None
    completed_at: datetime.datetime | None
    total_items: int
    counted_items: int
    discrepancy_items: int
    total_discrepancy_value: Decimal
    notes: str | None
    validated_at: datetime.datetime | None
    lines: list[CountLineResponse] = Field(default_factory=list)
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PRÉPARATIONS
# ============================================================================

class PickingLineCreate(BaseModel):
    """Création d'une ligne de préparation."""
    product_id: UUID
    location_id: UUID | None = None
    quantity_demanded: Decimal
    unit: str = "UNIT"
    lot_id: UUID | None = None
    serial_id: UUID | None = None


class PickingLineUpdate(BaseModel):
    """Mise à jour d'une ligne de préparation."""
    quantity_picked: Decimal
    lot_id: UUID | None = None
    serial_id: UUID | None = None
    notes: str | None = None


class PickingLineResponse(BaseModel):
    """Réponse ligne de préparation."""
    id: UUID
    picking_id: UUID
    product_id: UUID
    location_id: UUID | None
    quantity_demanded: Decimal
    quantity_picked: Decimal
    unit: str
    lot_id: UUID | None
    serial_id: UUID | None
    is_picked: bool
    picked_at: datetime.datetime | None
    notes: str | None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class PickingCreate(BaseModel):
    """Création d'une préparation."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    picking_type: MovementType = Field(default=MovementType.OUT, alias="type")
    warehouse_id: UUID
    reference_type: str | None = None
    reference_id: UUID | None = None
    reference_number: str | None = None
    scheduled_date: datetime.datetime | None = None
    priority: str = "NORMAL"
    notes: str | None = None
    lines: list[PickingLineCreate] = Field(default_factory=list)


class PickingResponse(BaseModel):
    """Réponse préparation."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True, populate_by_name=True)

    id: UUID
    number: str
    picking_type: MovementType = Field(..., alias="type")
    status: PickingStatus
    warehouse_id: UUID
    reference_type: str | None
    reference_id: UUID | None
    reference_number: str | None
    scheduled_date: datetime.datetime | None
    started_at: datetime.datetime | None
    completed_at: datetime.datetime | None
    assigned_to: UUID | None
    total_lines: int
    picked_lines: int
    priority: str
    notes: str | None
    lines: list[PickingLineResponse] = Field(default_factory=list)
    created_at: datetime.datetime
    updated_at: datetime.datetime



# ============================================================================
# VALORISATION
# ============================================================================

class ValuationResponse(BaseModel):
    """Réponse valorisation."""
    id: UUID
    valuation_date: datetime.date
    warehouse_id: UUID | None
    total_products: int
    total_quantity: Decimal
    total_value: Decimal
    value_fifo: Decimal
    value_lifo: Decimal
    value_avg: Decimal
    value_standard: Decimal
    details: list[dict[str, Any]]
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('details', mode='before')
    @classmethod
    def parse_details(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


# ============================================================================
# DASHBOARD
# ============================================================================

class InventoryDashboard(BaseModel):
    """Dashboard Inventaire."""
    # Statistiques générales
    total_products: int = 0
    active_products: int = 0
    total_warehouses: int = 0
    total_locations: int = 0

    # Stock
    total_stock_value: Decimal = Decimal("0")
    total_items_in_stock: int = 0
    low_stock_products: int = 0
    out_of_stock_products: int = 0
    expiring_soon: int = 0

    # Mouvements
    movements_today: int = 0
    movements_this_week: int = 0
    pending_movements: int = 0

    # Préparations
    pending_pickings: int = 0
    in_progress_pickings: int = 0

    # Inventaires
    pending_counts: int = 0
    in_progress_counts: int = 0

    # Top produits
    top_products_by_value: list[dict[str, Any]] = Field(default_factory=list)
    top_products_by_movement: list[dict[str, Any]] = Field(default_factory=list)

    # Réapprovisionnement
    products_to_reorder: int = 0
    reorder_alerts: list[dict[str, Any]] = Field(default_factory=list)
