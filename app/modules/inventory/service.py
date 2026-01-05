"""
AZALS MODULE M5 - Service Inventaire
=====================================

Logique métier pour la gestion des stocks et logistique.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from uuid import UUID

from .models import (
    ProductCategory, Warehouse, Location, Product, StockLevel,
    Lot, SerialNumber, StockMovement, StockMovementLine,
    InventoryCount, InventoryCountLine, Picking, PickingLine,
    ProductStatus, MovementType, MovementStatus, InventoryStatus,
    LotStatus, PickingStatus
)
from .schemas import (
    CategoryCreate, CategoryUpdate,
    WarehouseCreate, WarehouseUpdate,
    LocationCreate, ProductCreate, ProductUpdate,
    LotCreate, SerialCreate, MovementCreate, MovementLineCreate,
    InventoryCountCreate, CountLineUpdate,
    PickingCreate, PickingLineUpdate
)


class InventoryService:
    """Service de gestion des stocks."""

    def __init__(self, db: Session, tenant_id: str, user_id: Optional[UUID] = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    # ========================================================================
    # CATÉGORIES
    # ========================================================================

    def create_category(self, data: CategoryCreate) -> ProductCategory:
        """Créer une catégorie."""
        category = ProductCategory(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            parent_id=data.parent_id,
            default_valuation=data.default_valuation,
            sort_order=data.sort_order,
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def get_category(self, category_id: UUID) -> Optional[ProductCategory]:
        """Récupérer une catégorie."""
        return self.db.query(ProductCategory).filter(
            ProductCategory.tenant_id == self.tenant_id,
            ProductCategory.id == category_id
        ).first()

    def list_categories(
        self,
        parent_id: Optional[UUID] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ProductCategory], int]:
        """Lister les catégories."""
        query = self.db.query(ProductCategory).filter(
            ProductCategory.tenant_id == self.tenant_id
        )
        if parent_id:
            query = query.filter(ProductCategory.parent_id == parent_id)
        if active_only:
            query = query.filter(ProductCategory.is_active == True)

        total = query.count()
        items = query.order_by(ProductCategory.sort_order).offset(skip).limit(limit).all()
        return items, total

    def update_category(self, category_id: UUID, data: CategoryUpdate) -> Optional[ProductCategory]:
        """Mettre à jour une catégorie."""
        category = self.get_category(category_id)
        if not category:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)

        self.db.commit()
        self.db.refresh(category)
        return category

    # ========================================================================
    # ENTREPÔTS
    # ========================================================================

    def create_warehouse(self, data: WarehouseCreate) -> Warehouse:
        """Créer un entrepôt."""
        warehouse = Warehouse(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(warehouse)

        # Si marqué par défaut, retirer le flag des autres
        if data.is_default:
            self.db.query(Warehouse).filter(
                Warehouse.tenant_id == self.tenant_id,
                Warehouse.id != warehouse.id
            ).update({"is_default": False})

        self.db.commit()
        self.db.refresh(warehouse)

        # Créer un emplacement par défaut
        self._create_default_location(warehouse.id)

        return warehouse

    def _create_default_location(self, warehouse_id: UUID):
        """Créer l'emplacement par défaut d'un entrepôt."""
        location = Location(
            tenant_id=self.tenant_id,
            warehouse_id=warehouse_id,
            code="DEFAULT",
            name="Emplacement par défaut",
            is_default=True,
        )
        self.db.add(location)
        self.db.commit()

    def get_warehouse(self, warehouse_id: UUID) -> Optional[Warehouse]:
        """Récupérer un entrepôt."""
        return self.db.query(Warehouse).filter(
            Warehouse.tenant_id == self.tenant_id,
            Warehouse.id == warehouse_id
        ).first()

    def list_warehouses(
        self,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Warehouse], int]:
        """Lister les entrepôts."""
        query = self.db.query(Warehouse).filter(
            Warehouse.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.filter(Warehouse.is_active == True)

        total = query.count()
        items = query.order_by(Warehouse.name).offset(skip).limit(limit).all()
        return items, total

    def update_warehouse(self, warehouse_id: UUID, data: WarehouseUpdate) -> Optional[Warehouse]:
        """Mettre à jour un entrepôt."""
        warehouse = self.get_warehouse(warehouse_id)
        if not warehouse:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if update_data.get("is_default"):
            self.db.query(Warehouse).filter(
                Warehouse.tenant_id == self.tenant_id,
                Warehouse.id != warehouse_id
            ).update({"is_default": False})

        for field, value in update_data.items():
            setattr(warehouse, field, value)

        self.db.commit()
        self.db.refresh(warehouse)
        return warehouse

    # ========================================================================
    # EMPLACEMENTS
    # ========================================================================

    def create_location(self, warehouse_id: UUID, data: LocationCreate) -> Location:
        """Créer un emplacement."""
        location = Location(
            tenant_id=self.tenant_id,
            warehouse_id=warehouse_id,
            **data.model_dump()
        )
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        return location

    def get_location(self, location_id: UUID) -> Optional[Location]:
        """Récupérer un emplacement."""
        return self.db.query(Location).filter(
            Location.tenant_id == self.tenant_id,
            Location.id == location_id
        ).first()

    def list_locations(
        self,
        warehouse_id: Optional[UUID] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Location], int]:
        """Lister les emplacements."""
        query = self.db.query(Location).filter(
            Location.tenant_id == self.tenant_id
        )
        if warehouse_id:
            query = query.filter(Location.warehouse_id == warehouse_id)
        if active_only:
            query = query.filter(Location.is_active == True)

        total = query.count()
        items = query.order_by(Location.code).offset(skip).limit(limit).all()
        return items, total

    # ========================================================================
    # PRODUITS
    # ========================================================================

    def create_product(self, data: ProductCreate) -> Product:
        """Créer un produit."""
        product = Product(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            **data.model_dump()
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_product(self, product_id: UUID) -> Optional[Product]:
        """Récupérer un produit."""
        return self.db.query(Product).filter(
            Product.tenant_id == self.tenant_id,
            Product.id == product_id
        ).first()

    def get_product_by_code(self, code: str) -> Optional[Product]:
        """Récupérer un produit par code."""
        return self.db.query(Product).filter(
            Product.tenant_id == self.tenant_id,
            Product.code == code
        ).first()

    def list_products(
        self,
        category_id: Optional[UUID] = None,
        status: Optional[ProductStatus] = None,
        search: Optional[str] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Product], int]:
        """Lister les produits."""
        query = self.db.query(Product).filter(
            Product.tenant_id == self.tenant_id
        )

        if category_id:
            query = query.filter(Product.category_id == category_id)
        if status:
            query = query.filter(Product.status == status)
        if active_only:
            query = query.filter(Product.is_active == True)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.code.ilike(search_term),
                    Product.name.ilike(search_term),
                    Product.barcode.ilike(search_term),
                    Product.sku.ilike(search_term)
                )
            )

        total = query.count()
        items = query.order_by(Product.name).offset(skip).limit(limit).all()
        return items, total

    def update_product(self, product_id: UUID, data: ProductUpdate) -> Optional[Product]:
        """Mettre à jour un produit."""
        product = self.get_product(product_id)
        if not product:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)

        self.db.commit()
        self.db.refresh(product)
        return product

    def activate_product(self, product_id: UUID) -> Optional[Product]:
        """Activer un produit."""
        product = self.get_product(product_id)
        if product:
            product.status = ProductStatus.ACTIVE
            self.db.commit()
            self.db.refresh(product)
        return product

    # ========================================================================
    # NIVEAUX DE STOCK
    # ========================================================================

    def get_stock_level(
        self,
        product_id: UUID,
        warehouse_id: UUID,
        location_id: Optional[UUID] = None
    ) -> Optional[StockLevel]:
        """Récupérer le niveau de stock."""
        query = self.db.query(StockLevel).filter(
            StockLevel.tenant_id == self.tenant_id,
            StockLevel.product_id == product_id,
            StockLevel.warehouse_id == warehouse_id
        )
        if location_id:
            query = query.filter(StockLevel.location_id == location_id)
        else:
            query = query.filter(StockLevel.location_id.is_(None))

        return query.first()

    def get_or_create_stock_level(
        self,
        product_id: UUID,
        warehouse_id: UUID,
        location_id: Optional[UUID] = None
    ) -> StockLevel:
        """Récupérer ou créer un niveau de stock."""
        stock = self.get_stock_level(product_id, warehouse_id, location_id)
        if not stock:
            stock = StockLevel(
                tenant_id=self.tenant_id,
                product_id=product_id,
                warehouse_id=warehouse_id,
                location_id=location_id,
            )
            self.db.add(stock)
            self.db.commit()
            self.db.refresh(stock)
        return stock

    def get_product_stock(self, product_id: UUID) -> List[StockLevel]:
        """Récupérer tout le stock d'un produit."""
        return self.db.query(StockLevel).filter(
            StockLevel.tenant_id == self.tenant_id,
            StockLevel.product_id == product_id,
            StockLevel.quantity_on_hand > 0
        ).all()

    def get_warehouse_stock(
        self,
        warehouse_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[StockLevel], int]:
        """Récupérer le stock d'un entrepôt."""
        query = self.db.query(StockLevel).filter(
            StockLevel.tenant_id == self.tenant_id,
            StockLevel.warehouse_id == warehouse_id
        )
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def update_stock_level(
        self,
        product_id: UUID,
        warehouse_id: UUID,
        location_id: Optional[UUID],
        quantity_change: Decimal,
        movement_type: MovementType,
        unit_cost: Optional[Decimal] = None
    ):
        """Mettre à jour le niveau de stock."""
        stock = self.get_or_create_stock_level(product_id, warehouse_id, location_id)

        if movement_type in [MovementType.IN, MovementType.RETURN, MovementType.PRODUCTION]:
            stock.quantity_on_hand += quantity_change
        elif movement_type in [MovementType.OUT, MovementType.SCRAP]:
            stock.quantity_on_hand -= quantity_change
        elif movement_type == MovementType.ADJUSTMENT:
            stock.quantity_on_hand += quantity_change  # Peut être positif ou négatif

        stock.quantity_available = stock.quantity_on_hand - stock.quantity_reserved
        stock.last_movement_at = datetime.utcnow()

        # Recalcul valorisation si coût fourni
        if unit_cost and stock.quantity_on_hand > 0:
            if movement_type == MovementType.IN:
                # Moyenne pondérée
                old_value = stock.total_value
                new_value = quantity_change * unit_cost
                stock.total_value = old_value + new_value
                stock.average_cost = stock.total_value / stock.quantity_on_hand
            else:
                stock.total_value = stock.quantity_on_hand * stock.average_cost

        self.db.commit()

    # ========================================================================
    # LOTS
    # ========================================================================

    def create_lot(self, data: LotCreate) -> Lot:
        """Créer un lot."""
        lot = Lot(
            tenant_id=self.tenant_id,
            product_id=data.product_id,
            number=data.number,
            production_date=data.production_date,
            expiry_date=data.expiry_date,
            reception_date=data.reception_date or date.today(),
            supplier_id=data.supplier_id,
            supplier_lot=data.supplier_lot,
            initial_quantity=data.initial_quantity,
            current_quantity=data.initial_quantity,
            unit_cost=data.unit_cost,
            notes=data.notes,
        )
        self.db.add(lot)
        self.db.commit()
        self.db.refresh(lot)
        return lot

    def get_lot(self, lot_id: UUID) -> Optional[Lot]:
        """Récupérer un lot."""
        return self.db.query(Lot).filter(
            Lot.tenant_id == self.tenant_id,
            Lot.id == lot_id
        ).first()

    def list_lots(
        self,
        product_id: Optional[UUID] = None,
        status: Optional[LotStatus] = None,
        expiring_before: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Lot], int]:
        """Lister les lots."""
        query = self.db.query(Lot).filter(
            Lot.tenant_id == self.tenant_id
        )

        if product_id:
            query = query.filter(Lot.product_id == product_id)
        if status:
            query = query.filter(Lot.status == status)
        if expiring_before:
            query = query.filter(Lot.expiry_date <= expiring_before)

        total = query.count()
        items = query.order_by(Lot.expiry_date).offset(skip).limit(limit).all()
        return items, total

    # ========================================================================
    # NUMÉROS DE SÉRIE
    # ========================================================================

    def create_serial(self, data: SerialCreate) -> SerialNumber:
        """Créer un numéro de série."""
        serial = SerialNumber(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(serial)
        self.db.commit()
        self.db.refresh(serial)
        return serial

    def get_serial(self, serial_id: UUID) -> Optional[SerialNumber]:
        """Récupérer un numéro de série."""
        return self.db.query(SerialNumber).filter(
            SerialNumber.tenant_id == self.tenant_id,
            SerialNumber.id == serial_id
        ).first()

    def get_serial_by_number(self, product_id: UUID, number: str) -> Optional[SerialNumber]:
        """Récupérer un numéro de série par son numéro."""
        return self.db.query(SerialNumber).filter(
            SerialNumber.tenant_id == self.tenant_id,
            SerialNumber.product_id == product_id,
            SerialNumber.number == number
        ).first()

    # ========================================================================
    # MOUVEMENTS DE STOCK
    # ========================================================================

    def _generate_movement_number(self, type: MovementType) -> str:
        """Générer un numéro de mouvement."""
        prefix = {
            MovementType.IN: "IN",
            MovementType.OUT: "OUT",
            MovementType.TRANSFER: "TR",
            MovementType.ADJUSTMENT: "ADJ",
            MovementType.PRODUCTION: "PRD",
            MovementType.RETURN: "RET",
            MovementType.SCRAP: "SCR",
        }.get(type, "MOV")

        count = self.db.query(StockMovement).filter(
            StockMovement.tenant_id == self.tenant_id,
            StockMovement.type == type
        ).count() + 1

        return f"{prefix}-{datetime.now().strftime('%Y%m')}-{count:05d}"

    def create_movement(self, data: MovementCreate) -> StockMovement:
        """Créer un mouvement de stock."""
        movement = StockMovement(
            tenant_id=self.tenant_id,
            number=self._generate_movement_number(data.type),
            type=data.type,
            movement_date=data.movement_date,
            from_warehouse_id=data.from_warehouse_id,
            from_location_id=data.from_location_id,
            to_warehouse_id=data.to_warehouse_id,
            to_location_id=data.to_location_id,
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            reference_number=data.reference_number,
            reason=data.reason,
            notes=data.notes,
            created_by=self.user_id,
        )
        self.db.add(movement)
        self.db.flush()

        # Ajouter les lignes
        total_quantity = Decimal("0")
        total_value = Decimal("0")
        for i, line_data in enumerate(data.lines, 1):
            line = StockMovementLine(
                tenant_id=self.tenant_id,
                movement_id=movement.id,
                line_number=i,
                product_id=line_data.product_id,
                quantity=line_data.quantity,
                unit=line_data.unit,
                lot_id=line_data.lot_id,
                serial_id=line_data.serial_id,
                from_location_id=line_data.from_location_id,
                to_location_id=line_data.to_location_id,
                unit_cost=line_data.unit_cost,
                total_cost=line_data.quantity * (line_data.unit_cost or Decimal("0")),
                notes=line_data.notes,
            )
            self.db.add(line)
            total_quantity += line_data.quantity
            total_value += line.total_cost or Decimal("0")

        movement.total_items = len(data.lines)
        movement.total_quantity = total_quantity
        movement.total_value = total_value

        self.db.commit()
        self.db.refresh(movement)
        return movement

    def get_movement(self, movement_id: UUID) -> Optional[StockMovement]:
        """Récupérer un mouvement."""
        return self.db.query(StockMovement).filter(
            StockMovement.tenant_id == self.tenant_id,
            StockMovement.id == movement_id
        ).first()

    def list_movements(
        self,
        type: Optional[MovementType] = None,
        status: Optional[MovementStatus] = None,
        warehouse_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[StockMovement], int]:
        """Lister les mouvements."""
        query = self.db.query(StockMovement).filter(
            StockMovement.tenant_id == self.tenant_id
        )

        if type:
            query = query.filter(StockMovement.type == type)
        if status:
            query = query.filter(StockMovement.status == status)
        if warehouse_id:
            query = query.filter(
                or_(
                    StockMovement.from_warehouse_id == warehouse_id,
                    StockMovement.to_warehouse_id == warehouse_id
                )
            )
        if date_from:
            query = query.filter(StockMovement.movement_date >= date_from)
        if date_to:
            query = query.filter(StockMovement.movement_date <= date_to)

        total = query.count()
        items = query.order_by(StockMovement.movement_date.desc()).offset(skip).limit(limit).all()
        return items, total

    def confirm_movement(self, movement_id: UUID) -> Optional[StockMovement]:
        """Confirmer un mouvement (impacter les stocks)."""
        movement = self.get_movement(movement_id)
        if not movement or movement.status != MovementStatus.DRAFT:
            return None

        # Récupérer les lignes
        lines = self.db.query(StockMovementLine).filter(
            StockMovementLine.movement_id == movement_id
        ).all()

        # Appliquer chaque ligne
        for line in lines:
            # Sortie de stock source
            if movement.from_warehouse_id:
                from_loc = line.from_location_id or movement.from_location_id
                self.update_stock_level(
                    line.product_id,
                    movement.from_warehouse_id,
                    from_loc,
                    -line.quantity,
                    movement.type,
                    line.unit_cost
                )

            # Entrée en stock destination
            if movement.to_warehouse_id:
                to_loc = line.to_location_id or movement.to_location_id
                self.update_stock_level(
                    line.product_id,
                    movement.to_warehouse_id,
                    to_loc,
                    line.quantity,
                    movement.type,
                    line.unit_cost
                )

            # Mise à jour quantité lot si applicable
            if line.lot_id:
                lot = self.get_lot(line.lot_id)
                if lot:
                    if movement.type in [MovementType.OUT, MovementType.SCRAP]:
                        lot.current_quantity -= line.quantity
                    else:
                        lot.current_quantity += line.quantity

        movement.status = MovementStatus.CONFIRMED
        movement.confirmed_by = self.user_id
        movement.confirmed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(movement)
        return movement

    def cancel_movement(self, movement_id: UUID) -> Optional[StockMovement]:
        """Annuler un mouvement brouillon."""
        movement = self.get_movement(movement_id)
        if not movement or movement.status != MovementStatus.DRAFT:
            return None

        movement.status = MovementStatus.CANCELLED
        self.db.commit()
        self.db.refresh(movement)
        return movement

    # ========================================================================
    # INVENTAIRES PHYSIQUES
    # ========================================================================

    def _generate_count_number(self) -> str:
        """Générer un numéro d'inventaire."""
        count = self.db.query(InventoryCount).filter(
            InventoryCount.tenant_id == self.tenant_id
        ).count() + 1
        return f"INV-{datetime.now().strftime('%Y%m')}-{count:05d}"

    def create_inventory_count(self, data: InventoryCountCreate) -> InventoryCount:
        """Créer un inventaire physique."""
        count = InventoryCount(
            tenant_id=self.tenant_id,
            number=self._generate_count_number(),
            name=data.name,
            warehouse_id=data.warehouse_id,
            location_id=data.location_id,
            category_id=data.category_id,
            planned_date=data.planned_date,
            notes=data.notes,
            created_by=self.user_id,
        )
        self.db.add(count)
        self.db.commit()
        self.db.refresh(count)
        return count

    def get_inventory_count(self, count_id: UUID) -> Optional[InventoryCount]:
        """Récupérer un inventaire."""
        return self.db.query(InventoryCount).filter(
            InventoryCount.tenant_id == self.tenant_id,
            InventoryCount.id == count_id
        ).first()

    def list_inventory_counts(
        self,
        status: Optional[InventoryStatus] = None,
        warehouse_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[InventoryCount], int]:
        """Lister les inventaires."""
        query = self.db.query(InventoryCount).filter(
            InventoryCount.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(InventoryCount.status == status)
        if warehouse_id:
            query = query.filter(InventoryCount.warehouse_id == warehouse_id)

        total = query.count()
        items = query.order_by(InventoryCount.planned_date.desc()).offset(skip).limit(limit).all()
        return items, total

    def start_inventory_count(self, count_id: UUID) -> Optional[InventoryCount]:
        """Démarrer un inventaire (générer les lignes)."""
        count = self.get_inventory_count(count_id)
        if not count or count.status != InventoryStatus.DRAFT:
            return None

        # Récupérer les stocks à inventorier
        query = self.db.query(StockLevel).filter(
            StockLevel.tenant_id == self.tenant_id
        )

        if count.warehouse_id:
            query = query.filter(StockLevel.warehouse_id == count.warehouse_id)
        if count.location_id:
            query = query.filter(StockLevel.location_id == count.location_id)

        stocks = query.all()

        # Créer les lignes
        for stock in stocks:
            product = self.get_product(stock.product_id)
            if count.category_id and product.category_id != count.category_id:
                continue

            line = InventoryCountLine(
                tenant_id=self.tenant_id,
                count_id=count.id,
                product_id=stock.product_id,
                location_id=stock.location_id,
                theoretical_quantity=stock.quantity_on_hand,
                unit_cost=stock.average_cost,
            )
            self.db.add(line)

        count.status = InventoryStatus.IN_PROGRESS
        count.started_at = datetime.utcnow()
        count.total_items = len(stocks)

        self.db.commit()
        self.db.refresh(count)
        return count

    def update_count_line(
        self,
        count_id: UUID,
        line_id: UUID,
        data: CountLineUpdate
    ) -> Optional[InventoryCountLine]:
        """Mettre à jour une ligne d'inventaire."""
        line = self.db.query(InventoryCountLine).filter(
            InventoryCountLine.tenant_id == self.tenant_id,
            InventoryCountLine.id == line_id,
            InventoryCountLine.count_id == count_id
        ).first()

        if not line:
            return None

        line.counted_quantity = data.counted_quantity
        line.discrepancy = data.counted_quantity - line.theoretical_quantity
        line.discrepancy_value = line.discrepancy * (line.unit_cost or Decimal("0"))
        line.counted_at = datetime.utcnow()
        line.counted_by = self.user_id
        if data.notes:
            line.notes = data.notes

        # Mettre à jour les totaux du count
        count = self.get_inventory_count(count_id)
        if count:
            counted = self.db.query(InventoryCountLine).filter(
                InventoryCountLine.count_id == count_id,
                InventoryCountLine.counted_quantity.isnot(None)
            ).count()
            discrepancies = self.db.query(InventoryCountLine).filter(
                InventoryCountLine.count_id == count_id,
                InventoryCountLine.discrepancy != 0
            ).count()
            total_disc = self.db.query(
                func.sum(InventoryCountLine.discrepancy_value)
            ).filter(
                InventoryCountLine.count_id == count_id
            ).scalar() or Decimal("0")

            count.counted_items = counted
            count.discrepancy_items = discrepancies
            count.total_discrepancy_value = total_disc

        self.db.commit()
        self.db.refresh(line)
        return line

    def validate_inventory_count(self, count_id: UUID) -> Optional[InventoryCount]:
        """Valider un inventaire (ajuster les stocks)."""
        count = self.get_inventory_count(count_id)
        if not count or count.status != InventoryStatus.IN_PROGRESS:
            return None

        # Récupérer les lignes avec écart
        lines = self.db.query(InventoryCountLine).filter(
            InventoryCountLine.count_id == count_id,
            InventoryCountLine.discrepancy != 0
        ).all()

        # Créer un mouvement d'ajustement si nécessaire
        if lines:
            movement_lines = []
            for line in lines:
                movement_lines.append(MovementLineCreate(
                    product_id=line.product_id,
                    quantity=abs(line.discrepancy),
                    unit_cost=line.unit_cost,
                    to_location_id=line.location_id if line.discrepancy > 0 else None,
                    from_location_id=line.location_id if line.discrepancy < 0 else None,
                ))

            # Récupérer le warehouse depuis la première ligne de stock
            warehouse_id = None
            if count.warehouse_id:
                warehouse_id = count.warehouse_id
            else:
                first_stock = self.db.query(StockLevel).filter(
                    StockLevel.product_id == lines[0].product_id
                ).first()
                if first_stock:
                    warehouse_id = first_stock.warehouse_id

            if warehouse_id:
                movement_data = MovementCreate(
                    type=MovementType.ADJUSTMENT,
                    movement_date=datetime.utcnow(),
                    from_warehouse_id=warehouse_id,
                    to_warehouse_id=warehouse_id,
                    reference_type="inventory_count",
                    reference_id=count.id,
                    reference_number=count.number,
                    reason="Ajustement suite inventaire",
                    lines=movement_lines
                )
                movement = self.create_movement(movement_data)
                self.confirm_movement(movement.id)

        count.status = InventoryStatus.VALIDATED
        count.completed_at = datetime.utcnow()
        count.validated_by = self.user_id
        count.validated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(count)
        return count

    # ========================================================================
    # PRÉPARATIONS (PICKING)
    # ========================================================================

    def _generate_picking_number(self) -> str:
        """Générer un numéro de préparation."""
        count = self.db.query(Picking).filter(
            Picking.tenant_id == self.tenant_id
        ).count() + 1
        return f"PICK-{datetime.now().strftime('%Y%m')}-{count:05d}"

    def create_picking(self, data: PickingCreate) -> Picking:
        """Créer une préparation de commande."""
        picking = Picking(
            tenant_id=self.tenant_id,
            number=self._generate_picking_number(),
            type=data.type,
            warehouse_id=data.warehouse_id,
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            reference_number=data.reference_number,
            scheduled_date=data.scheduled_date,
            priority=data.priority,
            notes=data.notes,
            created_by=self.user_id,
        )
        self.db.add(picking)
        self.db.flush()

        # Ajouter les lignes
        for line_data in data.lines:
            line = PickingLine(
                tenant_id=self.tenant_id,
                picking_id=picking.id,
                product_id=line_data.product_id,
                location_id=line_data.location_id,
                quantity_demanded=line_data.quantity_demanded,
                unit=line_data.unit,
                lot_id=line_data.lot_id,
                serial_id=line_data.serial_id,
            )
            self.db.add(line)

        picking.total_lines = len(data.lines)

        self.db.commit()
        self.db.refresh(picking)
        return picking

    def get_picking(self, picking_id: UUID) -> Optional[Picking]:
        """Récupérer une préparation."""
        return self.db.query(Picking).filter(
            Picking.tenant_id == self.tenant_id,
            Picking.id == picking_id
        ).first()

    def list_pickings(
        self,
        status: Optional[PickingStatus] = None,
        warehouse_id: Optional[UUID] = None,
        assigned_to: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Picking], int]:
        """Lister les préparations."""
        query = self.db.query(Picking).filter(
            Picking.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(Picking.status == status)
        if warehouse_id:
            query = query.filter(Picking.warehouse_id == warehouse_id)
        if assigned_to:
            query = query.filter(Picking.assigned_to == assigned_to)

        total = query.count()
        items = query.order_by(Picking.scheduled_date).offset(skip).limit(limit).all()
        return items, total

    def assign_picking(self, picking_id: UUID, user_id: UUID) -> Optional[Picking]:
        """Assigner une préparation à un utilisateur."""
        picking = self.get_picking(picking_id)
        if not picking:
            return None

        picking.assigned_to = user_id
        picking.status = PickingStatus.ASSIGNED

        self.db.commit()
        self.db.refresh(picking)
        return picking

    def start_picking(self, picking_id: UUID) -> Optional[Picking]:
        """Démarrer une préparation."""
        picking = self.get_picking(picking_id)
        if not picking:
            return None

        picking.status = PickingStatus.IN_PROGRESS
        picking.started_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(picking)
        return picking

    def pick_line(
        self,
        picking_id: UUID,
        line_id: UUID,
        data: PickingLineUpdate
    ) -> Optional[PickingLine]:
        """Valider une ligne de préparation."""
        line = self.db.query(PickingLine).filter(
            PickingLine.tenant_id == self.tenant_id,
            PickingLine.id == line_id,
            PickingLine.picking_id == picking_id
        ).first()

        if not line:
            return None

        line.quantity_picked = data.quantity_picked
        line.lot_id = data.lot_id or line.lot_id
        line.serial_id = data.serial_id or line.serial_id
        line.is_picked = True
        line.picked_at = datetime.utcnow()
        line.picked_by = self.user_id
        if data.notes:
            line.notes = data.notes

        # Mettre à jour le compteur du picking
        picking = self.get_picking(picking_id)
        if picking:
            picked = self.db.query(PickingLine).filter(
                PickingLine.picking_id == picking_id,
                PickingLine.is_picked == True
            ).count()
            picking.picked_lines = picked

        self.db.commit()
        self.db.refresh(line)
        return line

    def complete_picking(self, picking_id: UUID) -> Optional[Picking]:
        """Terminer une préparation et créer le mouvement de sortie."""
        picking = self.get_picking(picking_id)
        if not picking or picking.status not in [PickingStatus.IN_PROGRESS, PickingStatus.ASSIGNED]:
            return None

        # Récupérer les lignes préparées
        lines = self.db.query(PickingLine).filter(
            PickingLine.picking_id == picking_id,
            PickingLine.is_picked == True
        ).all()

        if not lines:
            return None

        # Créer le mouvement de sortie
        movement_lines = []
        for line in lines:
            movement_lines.append(MovementLineCreate(
                product_id=line.product_id,
                quantity=line.quantity_picked,
                unit=line.unit,
                lot_id=line.lot_id,
                serial_id=line.serial_id,
                from_location_id=line.location_id,
            ))

        movement_data = MovementCreate(
            type=picking.type,
            movement_date=datetime.utcnow(),
            from_warehouse_id=picking.warehouse_id,
            reference_type=picking.reference_type,
            reference_id=picking.reference_id,
            reference_number=picking.reference_number,
            lines=movement_lines
        )
        movement = self.create_movement(movement_data)
        self.confirm_movement(movement.id)

        picking.status = PickingStatus.DONE
        picking.completed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(picking)
        return picking

    # ========================================================================
    # DASHBOARD
    # ========================================================================

    def get_dashboard(self) -> Dict[str, Any]:
        """Récupérer les données du dashboard inventaire."""
        today = date.today()
        week_ago = today - timedelta(days=7)
        warning_date = today + timedelta(days=30)

        # Produits
        total_products = self.db.query(Product).filter(
            Product.tenant_id == self.tenant_id
        ).count()

        active_products = self.db.query(Product).filter(
            Product.tenant_id == self.tenant_id,
            Product.status == ProductStatus.ACTIVE
        ).count()

        # Entrepôts et emplacements
        total_warehouses = self.db.query(Warehouse).filter(
            Warehouse.tenant_id == self.tenant_id,
            Warehouse.is_active == True
        ).count()

        total_locations = self.db.query(Location).filter(
            Location.tenant_id == self.tenant_id,
            Location.is_active == True
        ).count()

        # Valorisation totale
        total_value = self.db.query(
            func.sum(StockLevel.total_value)
        ).filter(
            StockLevel.tenant_id == self.tenant_id
        ).scalar() or Decimal("0")

        # Articles en stock
        items_in_stock = self.db.query(StockLevel).filter(
            StockLevel.tenant_id == self.tenant_id,
            StockLevel.quantity_on_hand > 0
        ).count()

        # Stock bas
        low_stock = self.db.query(StockLevel).join(Product).filter(
            StockLevel.tenant_id == self.tenant_id,
            StockLevel.quantity_on_hand <= Product.min_stock,
            StockLevel.quantity_on_hand > 0
        ).count()

        # Ruptures
        out_of_stock = self.db.query(StockLevel).join(Product).filter(
            StockLevel.tenant_id == self.tenant_id,
            StockLevel.quantity_on_hand <= 0,
            Product.status == ProductStatus.ACTIVE
        ).count()

        # Lots expirant bientôt
        expiring = self.db.query(Lot).filter(
            Lot.tenant_id == self.tenant_id,
            Lot.expiry_date <= warning_date,
            Lot.expiry_date > today,
            Lot.status == LotStatus.AVAILABLE
        ).count()

        # Mouvements
        movements_today = self.db.query(StockMovement).filter(
            StockMovement.tenant_id == self.tenant_id,
            func.date(StockMovement.movement_date) == today
        ).count()

        movements_week = self.db.query(StockMovement).filter(
            StockMovement.tenant_id == self.tenant_id,
            StockMovement.movement_date >= datetime.combine(week_ago, datetime.min.time())
        ).count()

        pending_movements = self.db.query(StockMovement).filter(
            StockMovement.tenant_id == self.tenant_id,
            StockMovement.status == MovementStatus.DRAFT
        ).count()

        # Préparations
        pending_pickings = self.db.query(Picking).filter(
            Picking.tenant_id == self.tenant_id,
            Picking.status == PickingStatus.PENDING
        ).count()

        in_progress_pickings = self.db.query(Picking).filter(
            Picking.tenant_id == self.tenant_id,
            Picking.status == PickingStatus.IN_PROGRESS
        ).count()

        # Inventaires
        pending_counts = self.db.query(InventoryCount).filter(
            InventoryCount.tenant_id == self.tenant_id,
            InventoryCount.status == InventoryStatus.DRAFT
        ).count()

        in_progress_counts = self.db.query(InventoryCount).filter(
            InventoryCount.tenant_id == self.tenant_id,
            InventoryCount.status == InventoryStatus.IN_PROGRESS
        ).count()

        return {
            "total_products": total_products,
            "active_products": active_products,
            "total_warehouses": total_warehouses,
            "total_locations": total_locations,
            "total_stock_value": total_value,
            "total_items_in_stock": items_in_stock,
            "low_stock_products": low_stock,
            "out_of_stock_products": out_of_stock,
            "expiring_soon": expiring,
            "movements_today": movements_today,
            "movements_this_week": movements_week,
            "pending_movements": pending_movements,
            "pending_pickings": pending_pickings,
            "in_progress_pickings": in_progress_pickings,
            "pending_counts": pending_counts,
            "in_progress_counts": in_progress_counts,
        }


def get_inventory_service(db: Session, tenant_id: str, user_id: Optional[UUID] = None) -> InventoryService:
    """Factory pour créer un service inventaire."""
    return InventoryService(db, tenant_id, user_id)
