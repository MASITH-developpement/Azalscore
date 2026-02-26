"""
Tests for WMS Module
====================

Tests unitaires pour le module WMS (Warehouse Management System).
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.modules.production.wms.service import (
    WMSService,
    Warehouse,
    Location,
    LocationStock,
    StockMovement,
    InventoryCount,
    WavePick,
    LocationType,
    MovementType,
    MovementStatus,
    CountStatus,
    WaveStatus,
)


# ========================
# SERVICE INIT TESTS
# ========================

class TestWMSServiceInit:
    """Tests d'initialisation du service."""

    def test_init_with_valid_tenant(self):
        """Test initialisation avec tenant valide."""
        service = WMSService(db=MagicMock(), tenant_id="tenant-123")
        assert service.tenant_id == "tenant-123"

    def test_init_without_tenant_raises(self):
        """Test que l'initialisation sans tenant échoue."""
        with pytest.raises(ValueError, match="tenant_id is required"):
            WMSService(db=MagicMock(), tenant_id="")


# ========================
# WAREHOUSE TESTS
# ========================

class TestWarehouseManagement:
    """Tests de gestion des entrepôts."""

    @pytest.fixture
    def service(self):
        return WMSService(db=MagicMock(), tenant_id="tenant-123")

    @pytest.mark.asyncio
    async def test_create_warehouse(self, service):
        """Test création d'entrepôt."""
        warehouse = await service.create_warehouse(
            code="WH-001",
            name="Entrepôt Principal",
            address="123 Rue Test"
        )

        assert warehouse.id is not None
        assert warehouse.tenant_id == "tenant-123"
        assert warehouse.code == "WH-001"
        assert warehouse.name == "Entrepôt Principal"
        assert warehouse.address == "123 Rue Test"
        assert warehouse.is_active is True

    @pytest.mark.asyncio
    async def test_get_warehouse(self, service):
        """Test récupération d'entrepôt."""
        created = await service.create_warehouse(
            code="WH-002",
            name="Entrepôt Test"
        )

        warehouse = await service.get_warehouse(created.id)
        assert warehouse is not None
        assert warehouse.code == "WH-002"

    @pytest.mark.asyncio
    async def test_get_warehouse_other_tenant(self, service):
        """Test isolation tenant pour entrepôt."""
        created = await service.create_warehouse(
            code="WH-003",
            name="Test"
        )

        # Simuler un autre tenant
        service2 = WMSService(db=MagicMock(), tenant_id="other-tenant")
        service2._warehouses = service._warehouses

        warehouse = await service2.get_warehouse(created.id)
        assert warehouse is None

    @pytest.mark.asyncio
    async def test_list_warehouses(self, service):
        """Test liste des entrepôts."""
        await service.create_warehouse(code="WH-A", name="A")
        await service.create_warehouse(code="WH-B", name="B")

        warehouses = await service.list_warehouses()
        assert len(warehouses) == 2

    @pytest.mark.asyncio
    async def test_list_warehouses_by_active_status(self, service):
        """Test liste des entrepôts par statut actif."""
        w1 = await service.create_warehouse(code="WH-ACTIVE", name="Active")
        w2 = await service.create_warehouse(code="WH-INACTIVE", name="Inactive")
        w2.is_active = False

        active = await service.list_warehouses(is_active=True)
        assert len(active) == 1
        assert active[0].code == "WH-ACTIVE"


# ========================
# LOCATION TESTS
# ========================

class TestLocationManagement:
    """Tests de gestion des emplacements."""

    @pytest.fixture
    def service(self):
        return WMSService(db=MagicMock(), tenant_id="tenant-123")

    @pytest.mark.asyncio
    async def test_create_location(self, service):
        """Test création d'emplacement."""
        warehouse = await service.create_warehouse(code="WH", name="Test")

        location = await service.create_location(
            warehouse_id=warehouse.id,
            code="A-01-01",
            name="Allée A, Rack 1, Niveau 1",
            location_type=LocationType.BIN,
            aisle="A",
            rack="01",
            level="01"
        )

        assert location.id is not None
        assert location.tenant_id == "tenant-123"
        assert location.code == "A-01-01"
        assert location.location_type == LocationType.BIN
        assert location.full_code == "A-01-01"

    @pytest.mark.asyncio
    async def test_location_full_code(self, service):
        """Test code complet de l'emplacement."""
        warehouse = await service.create_warehouse(code="WH", name="Test")

        location = await service.create_location(
            warehouse_id=warehouse.id,
            code="LOC",
            name="Test",
            location_type=LocationType.BIN,
            aisle="B",
            rack="02",
            level="03",
            position="04"
        )

        assert location.full_code == "B-02-03-04"

    @pytest.mark.asyncio
    async def test_get_location(self, service):
        """Test récupération d'emplacement."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        created = await service.create_location(
            warehouse_id=warehouse.id,
            code="LOC-1",
            name="Test",
            location_type=LocationType.SHELF
        )

        location = await service.get_location(created.id)
        assert location is not None
        assert location.code == "LOC-1"

    @pytest.mark.asyncio
    async def test_get_location_by_code(self, service):
        """Test récupération par code."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        await service.create_location(
            warehouse_id=warehouse.id,
            code="UNIQUE-CODE",
            name="Test",
            location_type=LocationType.BIN
        )

        location = await service.get_location_by_code(warehouse.id, "UNIQUE-CODE")
        assert location is not None
        assert location.code == "UNIQUE-CODE"

    @pytest.mark.asyncio
    async def test_list_locations(self, service):
        """Test liste des emplacements."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        await service.create_location(
            warehouse_id=warehouse.id,
            code="L1",
            name="Loc 1",
            location_type=LocationType.BIN
        )
        await service.create_location(
            warehouse_id=warehouse.id,
            code="L2",
            name="Loc 2",
            location_type=LocationType.SHELF
        )

        locations = await service.list_locations(warehouse.id)
        assert len(locations) == 2

    @pytest.mark.asyncio
    async def test_list_locations_by_type(self, service):
        """Test liste des emplacements par type."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        await service.create_location(
            warehouse_id=warehouse.id,
            code="BIN-1",
            name="Bin",
            location_type=LocationType.BIN
        )
        await service.create_location(
            warehouse_id=warehouse.id,
            code="RECV-1",
            name="Receiving",
            location_type=LocationType.RECEIVING
        )

        bins = await service.list_locations(warehouse.id, location_type=LocationType.BIN)
        assert len(bins) == 1
        assert bins[0].code == "BIN-1"

    @pytest.mark.asyncio
    async def test_update_location(self, service):
        """Test mise à jour d'emplacement."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        location = await service.create_location(
            warehouse_id=warehouse.id,
            code="L1",
            name="Original",
            location_type=LocationType.BIN
        )

        updated = await service.update_location(
            location.id,
            name="Updated",
            is_pickable=False
        )

        assert updated.name == "Updated"
        assert updated.is_pickable is False


# ========================
# STOCK & MOVEMENT TESTS
# ========================

class TestStockMovements:
    """Tests de mouvements de stock."""

    @pytest.fixture
    async def service_with_location(self):
        service = WMSService(db=MagicMock(), tenant_id="tenant-123")
        warehouse = await service.create_warehouse(code="WH", name="Test")
        location = await service.create_location(
            warehouse_id=warehouse.id,
            code="LOC-1",
            name="Emplacement 1",
            location_type=LocationType.BIN
        )
        return service, warehouse, location

    @pytest.mark.asyncio
    async def test_receive_stock(self, service_with_location):
        """Test réception de stock."""
        service, warehouse, location = service_with_location

        movement = await service.receive(
            location_id=location.id,
            product_id="PROD-001",
            quantity=100,
            reference="PO-123"
        )

        assert movement.id is not None
        assert movement.movement_type == MovementType.RECEIPT
        assert movement.quantity == 100
        assert movement.status == MovementStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_receive_updates_stock(self, service_with_location):
        """Test que la réception met à jour le stock."""
        service, warehouse, location = service_with_location

        await service.receive(
            location_id=location.id,
            product_id="PROD-001",
            quantity=50
        )

        stock = await service.get_stock(location.id, "PROD-001")
        assert stock is not None
        assert stock.quantity == 50

    @pytest.mark.asyncio
    async def test_transfer_stock(self, service_with_location):
        """Test transfert de stock."""
        service, warehouse, location = service_with_location

        # Create second location
        location2 = await service.create_location(
            warehouse_id=warehouse.id,
            code="LOC-2",
            name="Emplacement 2",
            location_type=LocationType.BIN
        )

        # Receive stock first
        await service.receive(
            location_id=location.id,
            product_id="PROD-001",
            quantity=100
        )

        # Transfer
        movement = await service.transfer(
            from_location_id=location.id,
            to_location_id=location2.id,
            product_id="PROD-001",
            quantity=30
        )

        assert movement.movement_type == MovementType.TRANSFER

        # Check stocks
        stock1 = await service.get_stock(location.id, "PROD-001")
        stock2 = await service.get_stock(location2.id, "PROD-001")
        assert stock1.quantity == 70
        assert stock2.quantity == 30

    @pytest.mark.asyncio
    async def test_pick_stock(self, service_with_location):
        """Test prélèvement de stock."""
        service, warehouse, location = service_with_location

        await service.receive(
            location_id=location.id,
            product_id="PROD-001",
            quantity=50
        )

        movement = await service.pick(
            location_id=location.id,
            product_id="PROD-001",
            quantity=20,
            reference="SO-001"
        )

        assert movement.movement_type == MovementType.PICK

        stock = await service.get_stock(location.id, "PROD-001")
        assert stock.quantity == 30

    @pytest.mark.asyncio
    async def test_adjust_stock(self, service_with_location):
        """Test ajustement de stock."""
        service, warehouse, location = service_with_location

        await service.receive(
            location_id=location.id,
            product_id="PROD-001",
            quantity=100
        )

        movement = await service.adjust(
            location_id=location.id,
            product_id="PROD-001",
            quantity=-10,
            notes="Ajustement inventaire"
        )

        assert movement.movement_type == MovementType.ADJUSTMENT

        stock = await service.get_stock(location.id, "PROD-001")
        assert stock.quantity == 90

    @pytest.mark.asyncio
    async def test_get_location_stock(self, service_with_location):
        """Test récupération du stock d'un emplacement."""
        service, warehouse, location = service_with_location

        await service.receive(location_id=location.id, product_id="P1", quantity=10)
        await service.receive(location_id=location.id, product_id="P2", quantity=20)

        stocks = await service.get_location_stock(location.id)
        assert len(stocks) == 2

    @pytest.mark.asyncio
    async def test_get_product_stock(self, service_with_location):
        """Test récupération du stock d'un produit."""
        service, warehouse, location = service_with_location

        location2 = await service.create_location(
            warehouse_id=warehouse.id,
            code="LOC-2",
            name="Loc 2",
            location_type=LocationType.BIN
        )

        await service.receive(location_id=location.id, product_id="P1", quantity=50)
        await service.receive(location_id=location2.id, product_id="P1", quantity=30)

        stocks = await service.get_product_stock("P1")
        assert len(stocks) == 2
        total = sum(s.quantity for s in stocks)
        assert total == 80

    @pytest.mark.asyncio
    async def test_list_movements(self, service_with_location):
        """Test liste des mouvements."""
        service, warehouse, location = service_with_location

        await service.receive(location_id=location.id, product_id="P1", quantity=10)
        await service.receive(location_id=location.id, product_id="P2", quantity=20)

        movements = await service.list_movements()
        assert len(movements) == 2

    @pytest.mark.asyncio
    async def test_list_movements_by_type(self, service_with_location):
        """Test liste des mouvements par type."""
        service, warehouse, location = service_with_location

        location2 = await service.create_location(
            warehouse_id=warehouse.id,
            code="LOC-2",
            name="Loc 2",
            location_type=LocationType.BIN
        )

        await service.receive(location_id=location.id, product_id="P1", quantity=100)
        await service.transfer(
            from_location_id=location.id,
            to_location_id=location2.id,
            product_id="P1",
            quantity=30
        )

        receipts = await service.list_movements(movement_type=MovementType.RECEIPT)
        assert len(receipts) == 1

        transfers = await service.list_movements(movement_type=MovementType.TRANSFER)
        assert len(transfers) == 1


# ========================
# INVENTORY COUNT TESTS
# ========================

class TestInventoryCounts:
    """Tests de comptage d'inventaire."""

    @pytest.fixture
    def service(self):
        return WMSService(db=MagicMock(), tenant_id="tenant-123")

    @pytest.mark.asyncio
    async def test_create_inventory_count(self, service):
        """Test création de comptage."""
        warehouse = await service.create_warehouse(code="WH", name="Test")

        count = await service.create_inventory_count(
            warehouse_id=warehouse.id,
            name="Inventaire Mensuel"
        )

        assert count.id is not None
        assert count.name == "Inventaire Mensuel"
        assert count.status == CountStatus.SCHEDULED

    @pytest.mark.asyncio
    async def test_start_inventory_count(self, service):
        """Test démarrage de comptage."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        count = await service.create_inventory_count(
            warehouse_id=warehouse.id,
            name="Test"
        )

        started = await service.start_inventory_count(count.id)
        assert started.status == CountStatus.IN_PROGRESS
        assert started.started_at is not None

    @pytest.mark.asyncio
    async def test_record_count(self, service):
        """Test enregistrement d'un comptage."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        location = await service.create_location(
            warehouse_id=warehouse.id,
            code="L1",
            name="Loc",
            location_type=LocationType.BIN
        )

        # Add some stock
        await service.receive(location_id=location.id, product_id="P1", quantity=100)

        count = await service.create_inventory_count(
            warehouse_id=warehouse.id,
            name="Test"
        )
        await service.start_inventory_count(count.id)

        # Record count with variance
        line = await service.record_count(
            count_id=count.id,
            location_id=location.id,
            product_id="P1",
            counted_qty=95
        )

        assert line.expected_qty == 100
        assert line.counted_qty == 95
        assert line.variance == -5

    @pytest.mark.asyncio
    async def test_complete_inventory_count(self, service):
        """Test fin de comptage."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        count = await service.create_inventory_count(
            warehouse_id=warehouse.id,
            name="Test"
        )
        await service.start_inventory_count(count.id)

        completed = await service.complete_inventory_count(count.id)
        assert completed.status == CountStatus.COMPLETED
        assert completed.completed_at is not None

    @pytest.mark.asyncio
    async def test_validate_inventory_count(self, service):
        """Test validation de comptage."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        count = await service.create_inventory_count(
            warehouse_id=warehouse.id,
            name="Test"
        )

        validated = await service.validate_inventory_count(count.id)
        assert validated.status == CountStatus.VALIDATED

    @pytest.mark.asyncio
    async def test_list_inventory_counts(self, service):
        """Test liste des comptages."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        await service.create_inventory_count(warehouse_id=warehouse.id, name="C1")
        await service.create_inventory_count(warehouse_id=warehouse.id, name="C2")

        counts = await service.list_inventory_counts(warehouse_id=warehouse.id)
        assert len(counts) == 2


# ========================
# WAVE PICKING TESTS
# ========================

class TestWavePicking:
    """Tests de vagues de préparation."""

    @pytest.fixture
    def service(self):
        return WMSService(db=MagicMock(), tenant_id="tenant-123")

    @pytest.mark.asyncio
    async def test_create_wave(self, service):
        """Test création de vague."""
        warehouse = await service.create_warehouse(code="WH", name="Test")

        wave = await service.create_wave(
            warehouse_id=warehouse.id,
            name="Vague Matin",
            order_ids=["ORD-001", "ORD-002"]
        )

        assert wave.id is not None
        assert wave.name == "Vague Matin"
        assert wave.status == WaveStatus.DRAFT
        assert len(wave.order_ids) == 2

    @pytest.mark.asyncio
    async def test_add_orders_to_wave(self, service):
        """Test ajout de commandes à une vague."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        wave = await service.create_wave(
            warehouse_id=warehouse.id,
            name="Test",
            order_ids=["ORD-001"]
        )

        updated = await service.add_orders_to_wave(
            wave.id,
            ["ORD-002", "ORD-003"]
        )

        assert len(updated.order_ids) == 3

    @pytest.mark.asyncio
    async def test_release_wave(self, service):
        """Test libération de vague."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        wave = await service.create_wave(
            warehouse_id=warehouse.id,
            name="Test",
            order_ids=["ORD-001", "ORD-002"]
        )

        released = await service.release_wave(wave.id)
        assert released.status == WaveStatus.RELEASED
        assert released.released_at is not None
        assert released.pick_count > 0

    @pytest.mark.asyncio
    async def test_start_wave(self, service):
        """Test démarrage de vague."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        wave = await service.create_wave(
            warehouse_id=warehouse.id,
            name="Test"
        )
        await service.release_wave(wave.id)

        started = await service.start_wave(wave.id)
        assert started.status == WaveStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_complete_wave(self, service):
        """Test fin de vague."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        wave = await service.create_wave(
            warehouse_id=warehouse.id,
            name="Test",
            order_ids=["ORD-001"]
        )
        await service.release_wave(wave.id)
        await service.start_wave(wave.id)

        completed = await service.complete_wave(wave.id)
        assert completed.status == WaveStatus.COMPLETED
        assert completed.completed_at is not None
        assert completed.progress == 100.0

    @pytest.mark.asyncio
    async def test_wave_progress(self, service):
        """Test calcul de progression."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        wave = await service.create_wave(
            warehouse_id=warehouse.id,
            name="Test",
            order_ids=["O1", "O2"]
        )
        await service.release_wave(wave.id)

        wave.picked_count = 5
        assert wave.progress == 50.0

    @pytest.mark.asyncio
    async def test_list_waves(self, service):
        """Test liste des vagues."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        await service.create_wave(warehouse_id=warehouse.id, name="W1")
        await service.create_wave(warehouse_id=warehouse.id, name="W2")

        waves = await service.list_waves(warehouse_id=warehouse.id)
        assert len(waves) == 2


# ========================
# REPLENISHMENT TESTS
# ========================

class TestReplenishment:
    """Tests de réapprovisionnement."""

    @pytest.fixture
    async def service_with_locations(self):
        service = WMSService(db=MagicMock(), tenant_id="tenant-123")
        warehouse = await service.create_warehouse(code="WH", name="Test")
        pick_loc = await service.create_location(
            warehouse_id=warehouse.id,
            code="PICK-1",
            name="Zone Picking",
            location_type=LocationType.BIN
        )
        reserve_loc = await service.create_location(
            warehouse_id=warehouse.id,
            code="RES-1",
            name="Zone Réserve",
            location_type=LocationType.RACK
        )
        return service, warehouse, pick_loc, reserve_loc

    @pytest.mark.asyncio
    async def test_create_replenishment_rule(self, service_with_locations):
        """Test création de règle de réappro."""
        service, warehouse, pick_loc, reserve_loc = service_with_locations

        rule = await service.create_replenishment_rule(
            product_id="PROD-001",
            location_id=pick_loc.id,
            min_qty=10,
            max_qty=100,
            reorder_qty=50,
            source_location_id=reserve_loc.id
        )

        assert rule.id is not None
        assert rule.min_qty == 10
        assert rule.reorder_qty == 50

    @pytest.mark.asyncio
    async def test_check_replenishment_needs(self, service_with_locations):
        """Test vérification des besoins."""
        service, warehouse, pick_loc, reserve_loc = service_with_locations

        await service.create_replenishment_rule(
            product_id="PROD-001",
            location_id=pick_loc.id,
            min_qty=10,
            max_qty=100,
            reorder_qty=50,
            source_location_id=reserve_loc.id
        )

        # Stock below min
        await service.receive(location_id=pick_loc.id, product_id="PROD-001", quantity=5)

        needs = await service.check_replenishment_needs(warehouse.id)
        assert len(needs) == 1
        assert needs[0]["current_qty"] == 5
        assert needs[0]["suggested_qty"] == 50

    @pytest.mark.asyncio
    async def test_execute_replenishment(self, service_with_locations):
        """Test exécution de réappro."""
        service, warehouse, pick_loc, reserve_loc = service_with_locations

        # Stock in reserve
        await service.receive(
            location_id=reserve_loc.id,
            product_id="PROD-001",
            quantity=200
        )

        rule = await service.create_replenishment_rule(
            product_id="PROD-001",
            location_id=pick_loc.id,
            min_qty=10,
            max_qty=100,
            reorder_qty=50,
            source_location_id=reserve_loc.id
        )

        movement = await service.execute_replenishment(rule.id)
        assert movement is not None
        assert movement.movement_type == MovementType.TRANSFER
        assert movement.quantity == 50

        # Check stocks
        pick_stock = await service.get_stock(pick_loc.id, "PROD-001")
        reserve_stock = await service.get_stock(reserve_loc.id, "PROD-001")
        assert pick_stock.quantity == 50
        assert reserve_stock.quantity == 150


# ========================
# STATISTICS TESTS
# ========================

class TestStatistics:
    """Tests des statistiques."""

    @pytest.fixture
    def service(self):
        return WMSService(db=MagicMock(), tenant_id="tenant-123")

    @pytest.mark.asyncio
    async def test_get_statistics(self, service):
        """Test récupération des statistiques."""
        warehouse = await service.create_warehouse(code="WH", name="Test")
        await service.create_location(
            warehouse_id=warehouse.id,
            code="L1",
            name="Loc",
            location_type=LocationType.BIN
        )

        stats = await service.get_statistics(warehouse.id)

        assert stats["warehouse_id"] == warehouse.id
        assert stats["total_locations"] == 1
        assert "movements_by_type" in stats


# ========================
# DATACLASS TESTS
# ========================

class TestDataclasses:
    """Tests des dataclasses."""

    def test_location_stock_available_quantity(self):
        """Test quantité disponible."""
        stock = LocationStock(
            location_id="loc-1",
            product_id="prod-1",
            lot_id=None,
            quantity=100,
            reserved_quantity=25
        )
        assert stock.available_quantity == 75

    def test_wave_progress_empty(self):
        """Test progression vague vide."""
        wave = WavePick(
            id="wave-1",
            tenant_id="t1",
            name="Test",
            warehouse_id="wh-1",
            pick_count=0
        )
        assert wave.progress == 0.0

    def test_wave_progress_partial(self):
        """Test progression vague partielle."""
        wave = WavePick(
            id="wave-1",
            tenant_id="t1",
            name="Test",
            warehouse_id="wh-1",
            pick_count=10,
            picked_count=3
        )
        assert wave.progress == 30.0


# ========================
# ROUTER TESTS
# ========================

class TestWMSRouter:
    """Tests du router WMS."""

    @pytest.fixture
    def mock_service(self):
        return AsyncMock(spec=WMSService)

    @pytest.fixture
    def client(self, mock_service):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.modules.production.wms.router import router, get_wms_service

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_wms_service] = lambda: mock_service
        return TestClient(app)

    def test_create_warehouse_endpoint(self, client, mock_service):
        """Test endpoint création entrepôt."""
        mock_service.create_warehouse.return_value = Warehouse(
            id="wh-1",
            tenant_id="t1",
            code="WH-001",
            name="Test"
        )

        response = client.post(
            "/v3/production/wms/warehouses?tenant_id=t1",
            json={"code": "WH-001", "name": "Test"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "WH-001"

    def test_list_warehouses_endpoint(self, client, mock_service):
        """Test endpoint liste entrepôts."""
        mock_service.list_warehouses.return_value = [
            Warehouse(id="wh-1", tenant_id="t1", code="WH-1", name="W1"),
            Warehouse(id="wh-2", tenant_id="t1", code="WH-2", name="W2")
        ]

        response = client.get("/v3/production/wms/warehouses?tenant_id=t1")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_create_location_endpoint(self, client, mock_service):
        """Test endpoint création emplacement."""
        mock_service.create_location.return_value = Location(
            id="loc-1",
            tenant_id="t1",
            warehouse_id="wh-1",
            code="L1",
            name="Loc 1",
            location_type=LocationType.BIN
        )

        response = client.post(
            "/v3/production/wms/warehouses/wh-1/locations?tenant_id=t1",
            json={"code": "L1", "name": "Loc 1", "location_type": "bin"}
        )

        assert response.status_code == 201

    def test_receive_stock_endpoint(self, client, mock_service):
        """Test endpoint réception."""
        mock_service.receive.return_value = StockMovement(
            id="mov-1",
            tenant_id="t1",
            movement_type=MovementType.RECEIPT,
            product_id="P1",
            quantity=100,
            to_location_id="loc-1",
            status=MovementStatus.COMPLETED
        )

        response = client.post(
            "/v3/production/wms/movements/receive?tenant_id=t1",
            json={
                "location_id": "loc-1",
                "product_id": "P1",
                "quantity": 100
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["movement_type"] == "receipt"

    def test_transfer_stock_endpoint(self, client, mock_service):
        """Test endpoint transfert."""
        mock_service.transfer.return_value = StockMovement(
            id="mov-1",
            tenant_id="t1",
            movement_type=MovementType.TRANSFER,
            product_id="P1",
            quantity=50,
            from_location_id="loc-1",
            to_location_id="loc-2",
            status=MovementStatus.COMPLETED
        )

        response = client.post(
            "/v3/production/wms/movements/transfer?tenant_id=t1",
            json={
                "from_location_id": "loc-1",
                "to_location_id": "loc-2",
                "product_id": "P1",
                "quantity": 50
            }
        )

        assert response.status_code == 201

    def test_create_wave_endpoint(self, client, mock_service):
        """Test endpoint création vague."""
        mock_service.create_wave.return_value = WavePick(
            id="wave-1",
            tenant_id="t1",
            warehouse_id="wh-1",
            name="Vague Test",
            order_ids=["O1", "O2"]
        )

        response = client.post(
            "/v3/production/wms/warehouses/wh-1/waves?tenant_id=t1",
            json={"name": "Vague Test", "order_ids": ["O1", "O2"]}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["order_count"] == 2

    def test_stats_endpoint(self, client, mock_service):
        """Test endpoint statistiques."""
        mock_service.get_statistics.return_value = {
            "warehouse_id": "wh-1",
            "total_locations": 50,
            "pickable_locations": 40,
            "total_movements_today": 25,
            "movements_by_type": {"receipt": 10, "pick": 15},
            "active_waves": 2,
            "total_waves": 5,
            "replenishment_needs": 3
        }

        response = client.get(
            "/v3/production/wms/warehouses/wh-1/stats?tenant_id=t1"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_locations"] == 50


# ========================
# TENANT ISOLATION TESTS
# ========================

class TestTenantIsolation:
    """Tests d'isolation tenant."""

    @pytest.mark.asyncio
    async def test_warehouse_tenant_isolation(self):
        """Test isolation tenant pour entrepôts."""
        service1 = WMSService(db=MagicMock(), tenant_id="tenant-1")
        service2 = WMSService(db=MagicMock(), tenant_id="tenant-2")

        # Share storage for testing
        service2._warehouses = service1._warehouses

        warehouse = await service1.create_warehouse(code="WH", name="Test")

        # Service 2 should not see tenant 1's warehouse
        result = await service2.get_warehouse(warehouse.id)
        assert result is None

        warehouses = await service2.list_warehouses()
        assert len(warehouses) == 0

    @pytest.mark.asyncio
    async def test_location_tenant_isolation(self):
        """Test isolation tenant pour emplacements."""
        service1 = WMSService(db=MagicMock(), tenant_id="tenant-1")
        service2 = WMSService(db=MagicMock(), tenant_id="tenant-2")

        service2._warehouses = service1._warehouses
        service2._locations = service1._locations

        warehouse = await service1.create_warehouse(code="WH", name="Test")
        location = await service1.create_location(
            warehouse_id=warehouse.id,
            code="L1",
            name="Loc",
            location_type=LocationType.BIN
        )

        # Service 2 should not see tenant 1's location
        result = await service2.get_location(location.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_wave_tenant_isolation(self):
        """Test isolation tenant pour vagues."""
        service1 = WMSService(db=MagicMock(), tenant_id="tenant-1")
        service2 = WMSService(db=MagicMock(), tenant_id="tenant-2")

        service2._warehouses = service1._warehouses
        service2._waves = service1._waves

        warehouse = await service1.create_warehouse(code="WH", name="Test")
        wave = await service1.create_wave(
            warehouse_id=warehouse.id,
            name="Test"
        )

        # Service 2 should not see tenant 1's wave
        result = await service2.get_wave(wave.id)
        assert result is None
