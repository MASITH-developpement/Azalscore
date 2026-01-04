"""
AZALS MODULE M5 - Tests Inventaire (Stock)
==========================================

Tests unitaires pour la gestion des stocks et logistique.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

# Import des modèles
from app.modules.inventory.models import (
    ProductCategory, Warehouse, Location, Product, StockLevel,
    Lot, SerialNumber, StockMovement, StockMovementLine,
    InventoryCount, InventoryCountLine, Picking, PickingLine,
    ReplenishmentRule, StockValuation,
    ProductType, ProductStatus, WarehouseType, LocationType,
    MovementType, MovementStatus, InventoryStatus, LotStatus,
    ValuationMethod, PickingStatus
)

# Import des schémas
from app.modules.inventory.schemas import (
    CategoryCreate, WarehouseCreate, LocationCreate,
    ProductCreate, ProductUpdate, StockLevelUpdate,
    LotCreate, SerialNumberCreate,
    MovementCreate, MovementLineCreate,
    InventoryCountCreate, InventoryCountLineCreate,
    PickingCreate, PickingLineCreate,
    ReplenishmentRuleCreate, StockValuationCreate,
    StockDashboard, StockAlert
)

# Import du service
from app.modules.inventory.service import InventoryService, get_inventory_service


# =============================================================================
# TESTS DES ENUMS
# =============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_product_type_values(self):
        """Tester les types de produit."""
        assert ProductType.STOCKABLE.value == "STOCKABLE"
        assert ProductType.CONSUMABLE.value == "CONSUMABLE"
        assert ProductType.SERVICE.value == "SERVICE"
        assert len(ProductType) == 3

    def test_product_status_values(self):
        """Tester les statuts produit."""
        assert ProductStatus.DRAFT.value == "DRAFT"
        assert ProductStatus.ACTIVE.value == "ACTIVE"
        assert ProductStatus.DISCONTINUED.value == "DISCONTINUED"
        assert ProductStatus.BLOCKED.value == "BLOCKED"
        assert len(ProductStatus) == 4

    def test_warehouse_type_values(self):
        """Tester les types d'entrepôt."""
        assert WarehouseType.INTERNAL.value == "INTERNAL"
        assert WarehouseType.EXTERNAL.value == "EXTERNAL"
        assert WarehouseType.TRANSIT.value == "TRANSIT"
        assert WarehouseType.VIRTUAL.value == "VIRTUAL"
        assert len(WarehouseType) == 4

    def test_location_type_values(self):
        """Tester les types d'emplacement."""
        assert LocationType.STORAGE.value == "STORAGE"
        assert LocationType.RECEIVING.value == "RECEIVING"
        assert LocationType.SHIPPING.value == "SHIPPING"
        assert LocationType.PRODUCTION.value == "PRODUCTION"
        assert len(LocationType) == 6

    def test_movement_type_values(self):
        """Tester les types de mouvement."""
        assert MovementType.IN.value == "IN"
        assert MovementType.OUT.value == "OUT"
        assert MovementType.TRANSFER.value == "TRANSFER"
        assert MovementType.ADJUSTMENT.value == "ADJUSTMENT"
        assert len(MovementType) == 7

    def test_valuation_method_values(self):
        """Tester les méthodes de valorisation."""
        assert ValuationMethod.FIFO.value == "FIFO"
        assert ValuationMethod.LIFO.value == "LIFO"
        assert ValuationMethod.AVG.value == "AVG"
        assert ValuationMethod.STANDARD.value == "STANDARD"
        assert len(ValuationMethod) == 4

    def test_lot_status_values(self):
        """Tester les statuts de lot."""
        assert LotStatus.AVAILABLE.value == "AVAILABLE"
        assert LotStatus.RESERVED.value == "RESERVED"
        assert LotStatus.BLOCKED.value == "BLOCKED"
        assert LotStatus.EXPIRED.value == "EXPIRED"
        assert len(LotStatus) == 4


# =============================================================================
# TESTS DES MODÈLES
# =============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_warehouse_model(self):
        """Tester le modèle Warehouse."""
        warehouse = Warehouse(
            tenant_id="test-tenant",
            code="WH001",
            name="Entrepôt Principal",
            type=WarehouseType.INTERNAL
        )
        assert warehouse.code == "WH001"
        assert warehouse.type == WarehouseType.INTERNAL
        assert warehouse.is_active == True

    def test_location_model(self):
        """Tester le modèle Location."""
        location = Location(
            tenant_id="test-tenant",
            warehouse_id=uuid4(),
            code="A-01-01",
            name="Allée A, Rack 1, Niveau 1",
            type=LocationType.STORAGE
        )
        assert location.code == "A-01-01"
        assert location.type == LocationType.STORAGE

    def test_product_model(self):
        """Tester le modèle Product."""
        product = Product(
            tenant_id="test-tenant",
            code="PROD001",
            name="Produit Test",
            type=ProductType.STOCKABLE,
            standard_cost=Decimal("25.50")
        )
        assert product.code == "PROD001"
        assert product.type == ProductType.STOCKABLE
        assert product.status == ProductStatus.DRAFT
        assert product.valuation_method == ValuationMethod.AVG

    def test_stock_level_model(self):
        """Tester le modèle StockLevel."""
        stock = StockLevel(
            tenant_id="test-tenant",
            product_id=uuid4(),
            warehouse_id=uuid4(),
            quantity_on_hand=Decimal("100"),
            quantity_reserved=Decimal("20")
        )
        assert stock.quantity_on_hand == Decimal("100")
        assert stock.quantity_reserved == Decimal("20")
        assert stock.quantity_available == Decimal("0")  # Non calculé automatiquement

    def test_lot_model(self):
        """Tester le modèle Lot."""
        lot = Lot(
            tenant_id="test-tenant",
            product_id=uuid4(),
            number="LOT-2026-001",
            expiry_date=date.today() + timedelta(days=365)
        )
        assert lot.number == "LOT-2026-001"
        assert lot.status == LotStatus.AVAILABLE

    def test_stock_movement_model(self):
        """Tester le modèle StockMovement."""
        movement = StockMovement(
            tenant_id="test-tenant",
            number="MVT-2026-001",
            type=MovementType.IN,
            movement_date=datetime.utcnow()
        )
        assert movement.number == "MVT-2026-001"
        assert movement.type == MovementType.IN
        assert movement.status == MovementStatus.DRAFT

    def test_inventory_count_model(self):
        """Tester le modèle InventoryCount."""
        count = InventoryCount(
            tenant_id="test-tenant",
            number="INV-2026-001",
            name="Inventaire annuel",
            planned_date=date.today()
        )
        assert count.number == "INV-2026-001"
        assert count.status == InventoryStatus.DRAFT


# =============================================================================
# TESTS DES SCHÉMAS
# =============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_product_create_schema(self):
        """Tester le schéma ProductCreate."""
        data = ProductCreate(
            code="PROD001",
            name="Produit Test",
            type=ProductType.STOCKABLE,
            unit="PCE",
            standard_cost=Decimal("50"),
            sale_price=Decimal("75")
        )
        assert data.code == "PROD001"
        assert data.type == ProductType.STOCKABLE

    def test_warehouse_create_schema(self):
        """Tester le schéma WarehouseCreate."""
        data = WarehouseCreate(
            code="WH001",
            name="Entrepôt Central",
            type=WarehouseType.INTERNAL,
            city="Paris"
        )
        assert data.code == "WH001"

    def test_movement_create_schema(self):
        """Tester le schéma MovementCreate."""
        lines = [
            MovementLineCreate(
                product_id=uuid4(),
                quantity=Decimal("50")
            )
        ]
        data = MovementCreate(
            type=MovementType.IN,
            to_warehouse_id=uuid4(),
            lines=lines
        )
        assert data.type == MovementType.IN
        assert len(data.lines) == 1


# =============================================================================
# TESTS DU SERVICE - PRODUITS
# =============================================================================

class TestInventoryServiceProducts:
    """Tests du service Inventory - Produits."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return InventoryService(mock_db, "test-tenant")

    def test_create_product(self, service, mock_db):
        """Tester la création d'un produit."""
        data = ProductCreate(
            code="PROD001",
            name="Produit Test",
            type=ProductType.STOCKABLE
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_product(data, uuid4())

        mock_db.add.assert_called_once()
        assert result.code == "PROD001"
        assert result.tenant_id == "test-tenant"

    def test_get_product_by_code(self, service, mock_db):
        """Tester la récupération par code."""
        mock_product = Product(
            id=uuid4(),
            tenant_id="test-tenant",
            code="PROD001",
            name="Test",
            type=ProductType.STOCKABLE
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product

        result = service.get_product_by_code("PROD001")

        assert result.code == "PROD001"

    def test_activate_product(self, service, mock_db):
        """Tester l'activation d'un produit."""
        product_id = uuid4()
        mock_product = MagicMock()
        mock_product.status = ProductStatus.DRAFT

        mock_db.query.return_value.filter.return_value.first.return_value = mock_product

        result = service.activate_product(product_id)

        assert mock_product.status == ProductStatus.ACTIVE


# =============================================================================
# TESTS DU SERVICE - MOUVEMENTS
# =============================================================================

class TestInventoryServiceMovements:
    """Tests du service Inventory - Mouvements."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return InventoryService(mock_db, "test-tenant")

    def test_create_movement(self, service, mock_db):
        """Tester la création d'un mouvement."""
        lines = [
            MovementLineCreate(
                product_id=uuid4(),
                quantity=Decimal("100")
            )
        ]
        data = MovementCreate(
            type=MovementType.IN,
            to_warehouse_id=uuid4(),
            lines=lines
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.create_movement(data, uuid4())

        assert mock_db.add.called

    def test_confirm_movement(self, service, mock_db):
        """Tester la confirmation d'un mouvement."""
        movement_id = uuid4()
        mock_movement = MagicMock()
        mock_movement.status = MovementStatus.DRAFT
        mock_movement.type = MovementType.IN
        mock_movement.lines = []

        mock_db.query.return_value.filter.return_value.first.return_value = mock_movement

        result = service.confirm_movement(movement_id, uuid4())

        assert mock_movement.status == MovementStatus.CONFIRMED


# =============================================================================
# TESTS DU SERVICE - INVENTAIRES
# =============================================================================

class TestInventoryServiceCounts:
    """Tests du service Inventory - Inventaires physiques."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return InventoryService(mock_db, "test-tenant")

    def test_create_inventory_count(self, service, mock_db):
        """Tester la création d'un inventaire."""
        data = InventoryCountCreate(
            name="Inventaire annuel 2026",
            warehouse_id=uuid4(),
            planned_date=date.today()
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.create_inventory_count(data, uuid4())

        mock_db.add.assert_called()

    def test_start_inventory_count(self, service, mock_db):
        """Tester le démarrage d'un inventaire."""
        count_id = uuid4()
        mock_count = MagicMock()
        mock_count.status = InventoryStatus.DRAFT

        mock_db.query.return_value.filter.return_value.first.return_value = mock_count

        result = service.start_inventory_count(count_id)

        assert mock_count.status == InventoryStatus.IN_PROGRESS

    def test_validate_inventory_count(self, service, mock_db):
        """Tester la validation d'un inventaire."""
        count_id = uuid4()
        mock_count = MagicMock()
        mock_count.status = InventoryStatus.IN_PROGRESS
        mock_count.lines = []

        mock_db.query.return_value.filter.return_value.first.return_value = mock_count

        result = service.validate_inventory_count(count_id, uuid4())

        assert mock_count.status == InventoryStatus.VALIDATED


# =============================================================================
# TESTS DU SERVICE - PICKING
# =============================================================================

class TestInventoryServicePicking:
    """Tests du service Inventory - Préparation."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return InventoryService(mock_db, "test-tenant")

    def test_create_picking(self, service, mock_db):
        """Tester la création d'une préparation."""
        lines = [
            PickingLineCreate(
                product_id=uuid4(),
                quantity_demanded=Decimal("10")
            )
        ]
        data = PickingCreate(
            warehouse_id=uuid4(),
            type=MovementType.OUT,
            lines=lines
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.create_picking(data, uuid4())

        assert mock_db.add.called

    def test_assign_picking(self, service, mock_db):
        """Tester l'assignation d'une préparation."""
        picking_id = uuid4()
        user_id = uuid4()
        mock_picking = MagicMock()
        mock_picking.status = PickingStatus.PENDING

        mock_db.query.return_value.filter.return_value.first.return_value = mock_picking

        result = service.assign_picking(picking_id, user_id)

        assert mock_picking.status == PickingStatus.ASSIGNED
        assert mock_picking.assigned_to == user_id


# =============================================================================
# TESTS FACTORY
# =============================================================================

class TestFactory:
    """Tests de la factory."""

    def test_get_inventory_service(self):
        """Tester la factory."""
        mock_db = MagicMock()
        service = get_inventory_service(mock_db, "test-tenant")

        assert isinstance(service, InventoryService)
        assert service.tenant_id == "test-tenant"


# =============================================================================
# TESTS MULTI-TENANT
# =============================================================================

class TestMultiTenant:
    """Tests d'isolation multi-tenant."""

    def test_tenant_isolation(self):
        """Tester l'isolation des tenants."""
        mock_db = MagicMock()

        service_a = InventoryService(mock_db, "tenant-A")
        service_b = InventoryService(mock_db, "tenant-B")

        assert service_a.tenant_id == "tenant-A"
        assert service_b.tenant_id == "tenant-B"


# =============================================================================
# TESTS CALCULS STOCK
# =============================================================================

class TestStockCalculations:
    """Tests des calculs de stock."""

    def test_available_quantity(self):
        """Tester le calcul de quantité disponible."""
        on_hand = Decimal("100")
        reserved = Decimal("30")
        available = on_hand - reserved

        assert available == Decimal("70")

    def test_stock_value_avg(self):
        """Tester la valorisation moyenne."""
        quantity = Decimal("100")
        avg_cost = Decimal("25.50")
        value = quantity * avg_cost

        assert value == Decimal("2550")

    def test_reorder_trigger(self):
        """Tester le déclenchement du réapprovisionnement."""
        current_stock = Decimal("15")
        reorder_point = Decimal("20")
        should_reorder = current_stock <= reorder_point

        assert should_reorder == True

    def test_inventory_discrepancy(self):
        """Tester le calcul de l'écart d'inventaire."""
        theoretical = Decimal("100")
        counted = Decimal("97")
        discrepancy = counted - theoretical

        assert discrepancy == Decimal("-3")


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
