"""
AZALS MODULE M5 - Schémas Inventaire
=====================================

Schémas Pydantic pour la gestion des stocks et logistique.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID
import json

from .models import (
    ProductType, ProductStatus, WarehouseType, LocationType,
    MovementType, MovementStatus, InventoryStatus, LotStatus,
    ValuationMethod, PickingStatus
)


# ============================================================================
# CATÉGORIES
# ============================================================================

class CategoryCreate(BaseModel):
    """Création d'une catégorie."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    default_valuation: ValuationMethod = ValuationMethod.AVG
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    """Mise à jour d'une catégorie."""
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    default_valuation: Optional[ValuationMethod] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryCreate):
    """Réponse catégorie."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ENTREPÔTS
# ============================================================================

class WarehouseCreate(BaseModel):
    """Création d'un entrepôt."""
    model_config = ConfigDict(protected_namespaces=())

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    type: WarehouseType = WarehouseType.INTERNAL
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: str = "France"
    manager_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_default: bool = False
    allow_negative: bool = False
    notes: Optional[str] = None


class WarehouseUpdate(BaseModel):
    """Mise à jour d'un entrepôt."""
    model_config = ConfigDict(protected_namespaces=())

    name: Optional[str] = None
    type: Optional[WarehouseType] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    manager_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_default: Optional[bool] = None
    allow_negative: Optional[bool] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class WarehouseResponse(WarehouseCreate):
    """Réponse entrepôt."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# EMPLACEMENTS
# ============================================================================

class LocationCreate(BaseModel):
    """Création d'un emplacement."""
    model_config = ConfigDict(protected_namespaces=())

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    type: LocationType = LocationType.STORAGE
    aisle: Optional[str] = None
    rack: Optional[str] = None
    level: Optional[str] = None
    position: Optional[str] = None
    max_weight_kg: Optional[Decimal] = None
    max_volume_m3: Optional[Decimal] = None
    is_default: bool = False
    requires_lot: bool = False
    requires_serial: bool = False
    barcode: Optional[str] = None
    notes: Optional[str] = None


class LocationUpdate(BaseModel):
    """Mise à jour d'un emplacement."""
    model_config = ConfigDict(protected_namespaces=())

    name: Optional[str] = None
    type: Optional[LocationType] = None
    aisle: Optional[str] = None
    rack: Optional[str] = None
    level: Optional[str] = None
    position: Optional[str] = None
    max_weight_kg: Optional[Decimal] = None
    max_volume_m3: Optional[Decimal] = None
    is_default: Optional[bool] = None
    requires_lot: Optional[bool] = None
    requires_serial: Optional[bool] = None
    barcode: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class LocationResponse(LocationCreate):
    """Réponse emplacement."""
    id: UUID
    warehouse_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PRODUITS
# ============================================================================

class ProductCreate(BaseModel):
    """Création d'un produit."""
    model_config = ConfigDict(protected_namespaces=())

    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    type: ProductType = ProductType.STOCKABLE
    category_id: Optional[UUID] = None
    barcode: Optional[str] = None
    ean13: Optional[str] = None
    sku: Optional[str] = None
    unit: str = "UNIT"
    purchase_unit: Optional[str] = None
    purchase_unit_factor: Decimal = Decimal("1")
    sale_unit: Optional[str] = None
    sale_unit_factor: Decimal = Decimal("1")
    standard_cost: Decimal = Decimal("0")
    sale_price: Optional[Decimal] = None
    currency: str = "EUR"
    valuation_method: ValuationMethod = ValuationMethod.AVG
    min_stock: Decimal = Decimal("0")
    max_stock: Optional[Decimal] = None
    reorder_point: Optional[Decimal] = None
    reorder_quantity: Optional[Decimal] = None
    lead_time_days: int = 0
    weight_kg: Optional[Decimal] = None
    volume_m3: Optional[Decimal] = None
    length_cm: Optional[Decimal] = None
    width_cm: Optional[Decimal] = None
    height_cm: Optional[Decimal] = None
    track_lot: bool = False
    track_serial: bool = False
    track_expiry: bool = False
    expiry_warning_days: int = 30
    default_warehouse_id: Optional[UUID] = None
    default_location_id: Optional[UUID] = None
    default_supplier_id: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    notes: Optional[str] = None


class ProductUpdate(BaseModel):
    """Mise à jour d'un produit."""
    model_config = ConfigDict(protected_namespaces=())

    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[ProductType] = None
    status: Optional[ProductStatus] = None
    category_id: Optional[UUID] = None
    barcode: Optional[str] = None
    ean13: Optional[str] = None
    sku: Optional[str] = None
    unit: Optional[str] = None
    purchase_unit: Optional[str] = None
    purchase_unit_factor: Optional[Decimal] = None
    sale_unit: Optional[str] = None
    sale_unit_factor: Optional[Decimal] = None
    standard_cost: Optional[Decimal] = None
    sale_price: Optional[Decimal] = None
    valuation_method: Optional[ValuationMethod] = None
    min_stock: Optional[Decimal] = None
    max_stock: Optional[Decimal] = None
    reorder_point: Optional[Decimal] = None
    reorder_quantity: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    weight_kg: Optional[Decimal] = None
    volume_m3: Optional[Decimal] = None
    track_lot: Optional[bool] = None
    track_serial: Optional[bool] = None
    track_expiry: Optional[bool] = None
    expiry_warning_days: Optional[int] = None
    default_warehouse_id: Optional[UUID] = None
    default_location_id: Optional[UUID] = None
    default_supplier_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    image_url: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    """Réponse produit."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: UUID
    code: str
    name: str
    description: Optional[str]
    type: ProductType
    status: ProductStatus
    category_id: Optional[UUID]
    barcode: Optional[str]
    ean13: Optional[str]
    sku: Optional[str]
    unit: str
    standard_cost: Decimal
    average_cost: Decimal
    sale_price: Optional[Decimal]
    currency: str
    valuation_method: ValuationMethod
    min_stock: Decimal
    max_stock: Optional[Decimal]
    reorder_point: Optional[Decimal]
    lead_time_days: int
    weight_kg: Optional[Decimal]
    track_lot: bool
    track_serial: bool
    track_expiry: bool
    tags: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class ProductList(BaseModel):
    """Liste de produits."""
    items: List[ProductResponse]
    total: int


# ============================================================================
# NIVEAUX DE STOCK
# ============================================================================

class StockLevelResponse(BaseModel):
    """Réponse niveau de stock."""
    id: UUID
    product_id: UUID
    warehouse_id: UUID
    location_id: Optional[UUID]
    quantity_on_hand: Decimal
    quantity_reserved: Decimal
    quantity_available: Decimal
    quantity_incoming: Decimal
    quantity_outgoing: Decimal
    total_value: Decimal
    average_cost: Decimal
    last_movement_at: Optional[datetime]
    last_count_at: Optional[datetime]
    updated_at: datetime

    class Config:
        from_attributes = True


class StockByProduct(BaseModel):
    """Stock agrégé par produit."""
    product_id: UUID
    product_code: str
    product_name: str
    total_on_hand: Decimal
    total_reserved: Decimal
    total_available: Decimal
    total_value: Decimal
    warehouses: List[Dict[str, Any]]


# ============================================================================
# LOTS
# ============================================================================

class LotCreate(BaseModel):
    """Création d'un lot."""
    product_id: UUID
    number: str = Field(..., min_length=1, max_length=100)
    production_date: Optional[date] = None
    expiry_date: Optional[date] = None
    reception_date: Optional[date] = None
    supplier_id: Optional[UUID] = None
    supplier_lot: Optional[str] = None
    initial_quantity: Decimal
    unit_cost: Optional[Decimal] = None
    notes: Optional[str] = None


class LotUpdate(BaseModel):
    """Mise à jour d'un lot."""
    status: Optional[LotStatus] = None
    expiry_date: Optional[date] = None
    notes: Optional[str] = None


class LotResponse(BaseModel):
    """Réponse lot."""
    id: UUID
    product_id: UUID
    number: str
    status: LotStatus
    production_date: Optional[date]
    expiry_date: Optional[date]
    reception_date: Optional[date]
    supplier_id: Optional[UUID]
    supplier_lot: Optional[str]
    initial_quantity: Decimal
    current_quantity: Decimal
    unit_cost: Optional[Decimal]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# NUMÉROS DE SÉRIE
# ============================================================================

class SerialCreate(BaseModel):
    """Création d'un numéro de série."""
    product_id: UUID
    number: str = Field(..., min_length=1, max_length=100)
    lot_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    reception_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    unit_cost: Optional[Decimal] = None
    notes: Optional[str] = None


class SerialUpdate(BaseModel):
    """Mise à jour d'un numéro de série."""
    status: Optional[LotStatus] = None
    warehouse_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    warranty_end_date: Optional[date] = None
    notes: Optional[str] = None


class SerialResponse(BaseModel):
    """Réponse numéro de série."""
    id: UUID
    product_id: UUID
    lot_id: Optional[UUID]
    number: str
    status: LotStatus
    warehouse_id: Optional[UUID]
    location_id: Optional[UUID]
    supplier_id: Optional[UUID]
    reception_date: Optional[date]
    customer_id: Optional[UUID]
    sale_date: Optional[date]
    warranty_end_date: Optional[date]
    unit_cost: Optional[Decimal]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# MOUVEMENTS DE STOCK
# ============================================================================

class MovementLineCreate(BaseModel):
    """Création d'une ligne de mouvement."""
    product_id: UUID
    quantity: Decimal
    unit: str = "UNIT"
    lot_id: Optional[UUID] = None
    serial_id: Optional[UUID] = None
    from_location_id: Optional[UUID] = None
    to_location_id: Optional[UUID] = None
    unit_cost: Optional[Decimal] = None
    notes: Optional[str] = None


class MovementLineResponse(MovementLineCreate):
    """Réponse ligne de mouvement."""
    id: UUID
    movement_id: UUID
    line_number: int
    total_cost: Optional[Decimal]
    created_at: datetime

    class Config:
        from_attributes = True


class MovementCreate(BaseModel):
    """Création d'un mouvement."""
    model_config = ConfigDict(protected_namespaces=())

    type: MovementType
    movement_date: datetime
    from_warehouse_id: Optional[UUID] = None
    from_location_id: Optional[UUID] = None
    to_warehouse_id: Optional[UUID] = None
    to_location_id: Optional[UUID] = None
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    reference_number: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    lines: List[MovementLineCreate] = Field(default_factory=list)


class MovementResponse(BaseModel):
    """Réponse mouvement."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: UUID
    number: str
    type: MovementType
    status: MovementStatus
    movement_date: datetime
    from_warehouse_id: Optional[UUID]
    from_location_id: Optional[UUID]
    to_warehouse_id: Optional[UUID]
    to_location_id: Optional[UUID]
    reference_type: Optional[str]
    reference_id: Optional[UUID]
    reference_number: Optional[str]
    reason: Optional[str]
    notes: Optional[str]
    total_items: int
    total_quantity: Decimal
    total_value: Decimal
    confirmed_at: Optional[datetime]
    lines: List[MovementLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MovementList(BaseModel):
    """Liste de mouvements."""
    items: List[MovementResponse]
    total: int


# ============================================================================
# INVENTAIRES PHYSIQUES
# ============================================================================

class CountLineCreate(BaseModel):
    """Création d'une ligne d'inventaire."""
    product_id: UUID
    location_id: Optional[UUID] = None
    lot_id: Optional[UUID] = None
    theoretical_quantity: Decimal = Decimal("0")
    counted_quantity: Optional[Decimal] = None
    notes: Optional[str] = None


class CountLineUpdate(BaseModel):
    """Mise à jour d'une ligne d'inventaire."""
    counted_quantity: Decimal
    notes: Optional[str] = None


class CountLineResponse(BaseModel):
    """Réponse ligne d'inventaire."""
    id: UUID
    count_id: UUID
    product_id: UUID
    location_id: Optional[UUID]
    lot_id: Optional[UUID]
    theoretical_quantity: Decimal
    counted_quantity: Optional[Decimal]
    discrepancy: Optional[Decimal]
    unit_cost: Optional[Decimal]
    discrepancy_value: Optional[Decimal]
    counted_at: Optional[datetime]
    counted_by: Optional[UUID]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class InventoryCountCreate(BaseModel):
    """Création d'un inventaire."""
    name: str = Field(..., min_length=1, max_length=200)
    warehouse_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    planned_date: date
    notes: Optional[str] = None


class InventoryCountResponse(BaseModel):
    """Réponse inventaire."""
    id: UUID
    number: str
    name: str
    status: InventoryStatus
    warehouse_id: Optional[UUID]
    location_id: Optional[UUID]
    category_id: Optional[UUID]
    planned_date: date
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_items: int
    counted_items: int
    discrepancy_items: int
    total_discrepancy_value: Decimal
    notes: Optional[str]
    validated_at: Optional[datetime]
    lines: List[CountLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PRÉPARATIONS
# ============================================================================

class PickingLineCreate(BaseModel):
    """Création d'une ligne de préparation."""
    product_id: UUID
    location_id: Optional[UUID] = None
    quantity_demanded: Decimal
    unit: str = "UNIT"
    lot_id: Optional[UUID] = None
    serial_id: Optional[UUID] = None


class PickingLineUpdate(BaseModel):
    """Mise à jour d'une ligne de préparation."""
    quantity_picked: Decimal
    lot_id: Optional[UUID] = None
    serial_id: Optional[UUID] = None
    notes: Optional[str] = None


class PickingLineResponse(BaseModel):
    """Réponse ligne de préparation."""
    id: UUID
    picking_id: UUID
    product_id: UUID
    location_id: Optional[UUID]
    quantity_demanded: Decimal
    quantity_picked: Decimal
    unit: str
    lot_id: Optional[UUID]
    serial_id: Optional[UUID]
    is_picked: bool
    picked_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PickingCreate(BaseModel):
    """Création d'une préparation."""
    model_config = ConfigDict(protected_namespaces=())

    type: MovementType = MovementType.OUT
    warehouse_id: UUID
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    reference_number: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    priority: str = "NORMAL"
    notes: Optional[str] = None
    lines: List[PickingLineCreate] = Field(default_factory=list)


class PickingResponse(BaseModel):
    """Réponse préparation."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: UUID
    number: str
    type: MovementType
    status: PickingStatus
    warehouse_id: UUID
    reference_type: Optional[str]
    reference_id: Optional[UUID]
    reference_number: Optional[str]
    scheduled_date: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    assigned_to: Optional[UUID]
    total_lines: int
    picked_lines: int
    priority: str
    notes: Optional[str]
    lines: List[PickingLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# VALORISATION
# ============================================================================

class ValuationResponse(BaseModel):
    """Réponse valorisation."""
    id: UUID
    valuation_date: date
    warehouse_id: Optional[UUID]
    total_products: int
    total_quantity: Decimal
    total_value: Decimal
    value_fifo: Decimal
    value_lifo: Decimal
    value_avg: Decimal
    value_standard: Decimal
    details: List[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True

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
    top_products_by_value: List[Dict[str, Any]] = Field(default_factory=list)
    top_products_by_movement: List[Dict[str, Any]] = Field(default_factory=list)

    # Réapprovisionnement
    products_to_reorder: int = 0
    reorder_alerts: List[Dict[str, Any]] = Field(default_factory=list)
