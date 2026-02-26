"""
Tests pour le module Delivery Notes.

Couverture:
- Delivery note management
- Picking lists
- Shipments
- Proof of delivery
- Statistics
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.modules.production.delivery import (
    DeliveryService,
    DeliveryNote,
    DeliveryLine,
    PickingList,
    Shipment,
    DeliveryStatus,
    ShipmentStatus,
)
from app.modules.production.delivery.service import PickingStatus
from app.modules.production.delivery.router import router


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def tenant_id():
    """Tenant ID for testing."""
    return "tenant-delivery-test"


@pytest.fixture
def delivery_service(mock_db, tenant_id):
    """Delivery service instance."""
    return DeliveryService(db=mock_db, tenant_id=tenant_id)


@pytest.fixture
def sample_lines():
    """Sample delivery lines."""
    return [
        {"product_id": "prod-1", "product_name": "Produit A", "quantity": 10},
        {"product_id": "prod-2", "product_name": "Produit B", "quantity": 5},
    ]


# =============================================================================
# SERVICE TESTS - INITIALIZATION
# =============================================================================


class TestDeliveryServiceInit:
    """Tests d'initialisation du service."""

    def test_init_with_valid_tenant(self, mock_db, tenant_id):
        """Test init avec tenant valide."""
        service = DeliveryService(db=mock_db, tenant_id=tenant_id)
        assert service.tenant_id == tenant_id
        assert service.db == mock_db

    def test_init_without_tenant_raises(self, mock_db):
        """Test init sans tenant lève exception."""
        with pytest.raises(ValueError, match="tenant_id est requis"):
            DeliveryService(db=mock_db, tenant_id="")


# =============================================================================
# SERVICE TESTS - DELIVERY NOTE MANAGEMENT
# =============================================================================


class TestDeliveryNoteManagement:
    """Tests de gestion des bons de livraison."""

    @pytest.mark.asyncio
    async def test_create_delivery_note(self, delivery_service, sample_lines):
        """Test création BL."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client Test",
            lines=sample_lines,
        )

        assert note.id is not None
        assert note.tenant_id == delivery_service.tenant_id
        assert note.delivery_number.startswith("BL-")
        assert note.status == DeliveryStatus.DRAFT
        assert len(note.lines) == 2
        assert note.total_quantity == Decimal("15")

    @pytest.mark.asyncio
    async def test_create_delivery_note_with_address(self, delivery_service, sample_lines):
        """Test création BL avec adresse."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
            shipping_address="123 Rue Test",
            shipping_city="Paris",
            shipping_postal_code="75001",
        )

        assert note.shipping_address == "123 Rue Test"
        assert note.shipping_city == "Paris"
        assert note.shipping_postal_code == "75001"

    @pytest.mark.asyncio
    async def test_get_delivery_note(self, delivery_service, sample_lines):
        """Test récupération BL."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )

        retrieved = await delivery_service.get_delivery_note(note.id)

        assert retrieved is not None
        assert retrieved.id == note.id

    @pytest.mark.asyncio
    async def test_get_delivery_note_by_number(self, delivery_service, sample_lines):
        """Test récupération BL par numéro."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )

        retrieved = await delivery_service.get_delivery_note_by_number(note.delivery_number)

        assert retrieved is not None
        assert retrieved.delivery_number == note.delivery_number

    @pytest.mark.asyncio
    async def test_list_delivery_notes(self, delivery_service, sample_lines):
        """Test liste des BL."""
        await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client 1",
            lines=sample_lines,
        )
        await delivery_service.create_delivery_note(
            customer_id="cust-2",
            customer_name="Client 2",
            lines=sample_lines,
        )

        notes = await delivery_service.list_delivery_notes()

        assert len(notes) == 2

    @pytest.mark.asyncio
    async def test_list_delivery_notes_by_status(self, delivery_service, sample_lines):
        """Test filtre BL par statut."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )
        await delivery_service.confirm_delivery_note(note.id)

        drafts = await delivery_service.list_delivery_notes(status=DeliveryStatus.DRAFT)
        confirmed = await delivery_service.list_delivery_notes(status=DeliveryStatus.CONFIRMED)

        assert len(drafts) == 0
        assert len(confirmed) == 1

    @pytest.mark.asyncio
    async def test_confirm_delivery_note(self, delivery_service, sample_lines):
        """Test confirmation BL."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )

        confirmed = await delivery_service.confirm_delivery_note(note.id)

        assert confirmed.status == DeliveryStatus.CONFIRMED

    @pytest.mark.asyncio
    async def test_cancel_delivery_note(self, delivery_service, sample_lines):
        """Test annulation BL."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )

        cancelled = await delivery_service.cancel_delivery_note(
            note.id,
            reason="Commande annulée",
        )

        assert cancelled.status == DeliveryStatus.CANCELLED
        assert cancelled.metadata["cancel_reason"] == "Commande annulée"

    @pytest.mark.asyncio
    async def test_delivery_line_remaining(self, delivery_service, sample_lines):
        """Test quantité restante ligne."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )

        line = note.lines[0]
        assert line.quantity_remaining == Decimal("10")
        assert line.is_complete is False


# =============================================================================
# SERVICE TESTS - PICKING
# =============================================================================


class TestPickingManagement:
    """Tests de gestion du picking."""

    @pytest.mark.asyncio
    async def test_create_picking_list(self, delivery_service, sample_lines):
        """Test création picking."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )
        await delivery_service.confirm_delivery_note(note.id)

        picking = await delivery_service.create_picking_list(note.id)

        assert picking is not None
        assert picking.picking_number.startswith("PICK-")
        assert picking.status == PickingStatus.PENDING
        assert len(picking.lines) == 2

    @pytest.mark.asyncio
    async def test_start_picking(self, delivery_service, sample_lines):
        """Test démarrage picking."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )
        await delivery_service.confirm_delivery_note(note.id)
        picking = await delivery_service.create_picking_list(note.id)

        started = await delivery_service.start_picking(picking.id, "picker-1")

        assert started.status == PickingStatus.IN_PROGRESS
        assert started.assigned_to == "picker-1"
        assert started.started_at is not None

    @pytest.mark.asyncio
    async def test_pick_line(self, delivery_service, sample_lines):
        """Test pick ligne."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )
        await delivery_service.confirm_delivery_note(note.id)
        picking = await delivery_service.create_picking_list(note.id)

        line_id = picking.lines[0].id
        updated = await delivery_service.pick_line(
            picking_id=picking.id,
            line_id=line_id,
            quantity_picked=Decimal("10"),
        )

        assert updated.lines[0].quantity_picked == Decimal("10")
        assert updated.lines[0].picked_at is not None

    @pytest.mark.asyncio
    async def test_complete_picking(self, delivery_service, sample_lines):
        """Test complétion picking."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )
        await delivery_service.confirm_delivery_note(note.id)
        picking = await delivery_service.create_picking_list(note.id)

        # Picker toutes les lignes
        for line in picking.lines:
            await delivery_service.pick_line(
                picking.id,
                line.id,
                line.quantity_to_pick,
            )

        completed = await delivery_service.complete_picking(picking.id)

        assert completed.status == PickingStatus.COMPLETED
        assert completed.completed_at is not None

        # Vérifier que le BL est packed
        updated_note = await delivery_service.get_delivery_note(note.id)
        assert updated_note.status == DeliveryStatus.PACKED

    @pytest.mark.asyncio
    async def test_picking_progress(self, delivery_service, sample_lines):
        """Test progression picking."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )
        await delivery_service.confirm_delivery_note(note.id)
        picking = await delivery_service.create_picking_list(note.id)

        # Picker la première ligne (10/15 = 66.67%)
        await delivery_service.pick_line(
            picking.id,
            picking.lines[0].id,
            Decimal("10"),
        )

        updated = await delivery_service.get_picking_list(picking.id)
        assert updated.progress == Decimal("66.67")


# =============================================================================
# SERVICE TESTS - SHIPPING
# =============================================================================


class TestShippingManagement:
    """Tests de gestion des expéditions."""

    @pytest.mark.asyncio
    async def test_ship_delivery_note(self, delivery_service, sample_lines):
        """Test expédition BL."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )
        await delivery_service.confirm_delivery_note(note.id)

        shipment = await delivery_service.ship(
            note_id=note.id,
            carrier_id="carrier-1",
            carrier_name="Transporteur Test",
            tracking_number="TRACK123456",
        )

        assert shipment is not None
        assert shipment.shipment_number.startswith("SHIP-")
        assert shipment.tracking_number == "TRACK123456"
        assert shipment.status == ShipmentStatus.PICKED_UP
        assert len(shipment.tracking_history) == 1

        # Vérifier le BL
        updated_note = await delivery_service.get_delivery_note(note.id)
        assert updated_note.status == DeliveryStatus.SHIPPED
        assert updated_note.tracking_number == "TRACK123456"

    @pytest.mark.asyncio
    async def test_ship_with_details(self, delivery_service, sample_lines):
        """Test expédition avec détails."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )
        await delivery_service.confirm_delivery_note(note.id)

        shipment = await delivery_service.ship(
            note_id=note.id,
            carrier_id="carrier-1",
            carrier_name="Colissimo",
            tracking_number="8R123456789FR",
            weight_kg=Decimal("5.5"),
            packages_count=2,
            shipping_cost=Decimal("15.90"),
            estimated_delivery=date.today() + timedelta(days=2),
        )

        assert shipment.weight_kg == Decimal("5.5")
        assert shipment.packages_count == 2
        assert shipment.shipping_cost == Decimal("15.90")

    @pytest.mark.asyncio
    async def test_update_shipment_status(self, delivery_service, sample_lines):
        """Test mise à jour statut expédition."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )
        await delivery_service.confirm_delivery_note(note.id)
        shipment = await delivery_service.ship(
            note.id,
            "carrier-1",
            "Carrier",
            "TRACK123",
        )

        updated = await delivery_service.update_shipment_status(
            shipment_id=shipment.id,
            status=ShipmentStatus.IN_TRANSIT,
            location="Centre de tri",
            message="Colis en transit",
        )

        assert updated.status == ShipmentStatus.IN_TRANSIT
        assert len(updated.tracking_history) == 2

    @pytest.mark.asyncio
    async def test_confirm_delivery(self, delivery_service, sample_lines):
        """Test confirmation livraison."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )
        await delivery_service.confirm_delivery_note(note.id)
        shipment = await delivery_service.ship(
            note.id,
            "carrier-1",
            "Carrier",
            "TRACK123",
        )

        delivered = await delivery_service.confirm_delivery(
            shipment_id=shipment.id,
            signature="Jean Dupont",
        )

        assert delivered.status == ShipmentStatus.DELIVERED
        assert delivered.signature == "Jean Dupont"
        assert delivered.actual_delivery is not None

        # Vérifier le BL
        updated_note = await delivery_service.get_delivery_note(note.id)
        assert updated_note.status == DeliveryStatus.DELIVERED

    @pytest.mark.asyncio
    async def test_list_shipments(self, delivery_service, sample_lines):
        """Test liste expéditions."""
        note1 = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client 1",
            lines=sample_lines,
        )
        await delivery_service.confirm_delivery_note(note1.id)
        await delivery_service.ship(note1.id, "c1", "Carrier 1", "T1")

        note2 = await delivery_service.create_delivery_note(
            customer_id="cust-2",
            customer_name="Client 2",
            lines=sample_lines,
        )
        await delivery_service.confirm_delivery_note(note2.id)
        await delivery_service.ship(note2.id, "c2", "Carrier 2", "T2")

        shipments = await delivery_service.list_shipments()

        assert len(shipments) == 2


# =============================================================================
# SERVICE TESTS - RETURNS
# =============================================================================


class TestReturns:
    """Tests des retours."""

    @pytest.mark.asyncio
    async def test_create_return_request(self, delivery_service, sample_lines):
        """Test création demande de retour."""
        note = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )
        await delivery_service.confirm_delivery_note(note.id)
        shipment = await delivery_service.ship(
            note.id,
            "carrier-1",
            "Carrier",
            "TRACK123",
        )
        await delivery_service.confirm_delivery(shipment.id)

        return_req = await delivery_service.create_return_request(
            note_id=note.id,
            reason="Produit endommagé",
            lines=[{"product_id": "prod-1", "quantity": 2}],
        )

        assert return_req is not None
        assert return_req.return_number.startswith("RET-")
        assert return_req.reason == "Produit endommagé"


# =============================================================================
# SERVICE TESTS - STATISTICS
# =============================================================================


class TestStatistics:
    """Tests des statistiques."""

    @pytest.mark.asyncio
    async def test_get_statistics_empty(self, delivery_service):
        """Test stats sans données."""
        stats = await delivery_service.get_statistics()

        assert stats["total_delivery_notes"] == 0
        assert stats["delivered"] == 0

    @pytest.mark.asyncio
    async def test_get_statistics_with_data(self, delivery_service, sample_lines):
        """Test stats avec données."""
        # BL livré
        note1 = await delivery_service.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client 1",
            lines=sample_lines,
            scheduled_date=date.today(),
        )
        await delivery_service.confirm_delivery_note(note1.id)
        shipment = await delivery_service.ship(
            note1.id,
            "carrier",
            "Carrier",
            "T1",
            shipping_cost=Decimal("10"),
        )
        await delivery_service.confirm_delivery(shipment.id)

        # BL en attente
        await delivery_service.create_delivery_note(
            customer_id="cust-2",
            customer_name="Client 2",
            lines=sample_lines,
        )

        stats = await delivery_service.get_statistics()

        assert stats["total_delivery_notes"] == 2
        assert stats["delivered"] == 1
        assert stats["pending"] == 1
        assert stats["total_shipping_cost"] == "10"


# =============================================================================
# ROUTER TESTS
# =============================================================================


class TestDeliveryRouter:
    """Tests des endpoints API Delivery."""

    @pytest.fixture
    def mock_service(self):
        """Service mocké."""
        return AsyncMock(spec=DeliveryService)

    @pytest.fixture
    def test_app(self, mock_service):
        """App de test avec service mocké."""
        app = FastAPI()
        app.include_router(router)

        async def override_service():
            return mock_service

        from app.modules.production.delivery import router as delivery_router_module

        app.dependency_overrides[delivery_router_module.get_delivery_service] = override_service
        return app

    @pytest.fixture
    def test_client(self, test_app):
        """Client de test."""
        return TestClient(test_app)

    def test_create_delivery_note_endpoint(self, test_client, mock_service):
        """Test endpoint création BL."""
        mock_note = DeliveryNote(
            id="note-123",
            tenant_id="test-tenant",
            delivery_number="BL-202602-00001",
            customer_id="cust-1",
            customer_name="Client Test",
            lines=[
                DeliveryLine(
                    id="line-1",
                    product_id="prod-1",
                    product_name="Product",
                    quantity_ordered=Decimal("10"),
                )
            ],
        )
        mock_service.create_delivery_note.return_value = mock_note

        response = test_client.post(
            "/v3/production/delivery/notes",
            json={
                "customer_id": "cust-1",
                "customer_name": "Client Test",
                "lines": [
                    {"product_id": "prod-1", "product_name": "Product", "quantity": 10}
                ],
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["delivery_number"] == "BL-202602-00001"

    def test_list_delivery_notes_endpoint(self, test_client, mock_service):
        """Test endpoint liste BL."""
        mock_service.list_delivery_notes.return_value = [
            DeliveryNote(
                id="note-1",
                tenant_id="test-tenant",
                delivery_number="BL-1",
                customer_id="cust-1",
                customer_name="Client",
                lines=[],
            ),
        ]

        response = test_client.get(
            "/v3/production/delivery/notes",
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_create_picking_endpoint(self, test_client, mock_service):
        """Test endpoint création picking."""
        from app.modules.production.delivery.service import PickingLine

        mock_picking = PickingList(
            id="pick-123",
            tenant_id="test-tenant",
            picking_number="PICK-00001",
            delivery_note_id="note-1",
            delivery_number="BL-1",
            lines=[
                PickingLine(
                    id="pl-1",
                    delivery_line_id="dl-1",
                    product_id="prod-1",
                    product_name="Product",
                    location_id="loc-1",
                    location_name="Stock",
                    quantity_to_pick=Decimal("10"),
                )
            ],
        )
        mock_service.create_picking_list.return_value = mock_picking

        response = test_client.post(
            "/v3/production/delivery/notes/note-1/picking",
            json={},
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 201

    def test_ship_endpoint(self, test_client, mock_service):
        """Test endpoint expédition."""
        mock_shipment = Shipment(
            id="ship-123",
            tenant_id="test-tenant",
            shipment_number="SHIP-00001",
            delivery_note_id="note-1",
            delivery_number="BL-1",
            carrier_id="carrier-1",
            carrier_name="Colissimo",
            tracking_number="8R123456789FR",
        )
        mock_service.ship.return_value = mock_shipment

        response = test_client.post(
            "/v3/production/delivery/notes/note-1/ship",
            json={
                "carrier_id": "carrier-1",
                "carrier_name": "Colissimo",
                "tracking_number": "8R123456789FR",
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 201

    def test_confirm_delivery_endpoint(self, test_client, mock_service):
        """Test endpoint confirmation livraison."""
        mock_shipment = Shipment(
            id="ship-123",
            tenant_id="test-tenant",
            shipment_number="SHIP-00001",
            delivery_note_id="note-1",
            delivery_number="BL-1",
            carrier_id="carrier-1",
            carrier_name="Colissimo",
            tracking_number="8R123456789FR",
            status=ShipmentStatus.DELIVERED,
            actual_delivery=datetime.now(),
            signature="Jean Dupont",
        )
        mock_service.confirm_delivery.return_value = mock_shipment

        response = test_client.post(
            "/v3/production/delivery/shipments/ship-123/deliver",
            json={"signature": "Jean Dupont"},
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200

    def test_stats_endpoint(self, test_client, mock_service):
        """Test endpoint statistiques."""
        mock_service.get_statistics.return_value = {
            "total_delivery_notes": 100,
            "delivered": 80,
            "shipped": 10,
            "pending": 8,
            "cancelled": 2,
            "total_shipments": 90,
            "total_shipping_cost": "1500.00",
            "on_time_deliveries": 75,
            "late_deliveries": 5,
            "on_time_rate": "93.75",
            "total_returns": 3,
        }

        response = test_client.get(
            "/v3/production/delivery/stats",
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_delivery_notes"] == 100


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestDataclasses:
    """Tests des dataclasses."""

    def test_delivery_line_remaining(self):
        """Test quantité restante ligne."""
        line = DeliveryLine(
            id="l1",
            product_id="p1",
            product_name="Product",
            quantity_ordered=Decimal("100"),
            quantity_shipped=Decimal("60"),
        )

        assert line.quantity_remaining == Decimal("40")
        assert line.is_complete is False

    def test_delivery_line_complete(self):
        """Test ligne complète."""
        line = DeliveryLine(
            id="l1",
            product_id="p1",
            product_name="Product",
            quantity_ordered=Decimal("100"),
            quantity_shipped=Decimal("100"),
        )

        assert line.is_complete is True

    def test_delivery_note_totals(self):
        """Test totaux BL."""
        note = DeliveryNote(
            id="n1",
            tenant_id="t1",
            delivery_number="BL-1",
            customer_id="c1",
            customer_name="Client",
            lines=[
                DeliveryLine(
                    id="l1",
                    product_id="p1",
                    product_name="P1",
                    quantity_ordered=Decimal("50"),
                    quantity_shipped=Decimal("50"),
                ),
                DeliveryLine(
                    id="l2",
                    product_id="p2",
                    product_name="P2",
                    quantity_ordered=Decimal("50"),
                    quantity_shipped=Decimal("25"),
                ),
            ],
        )

        assert note.total_quantity == Decimal("100")
        assert note.shipped_quantity == Decimal("75")
        assert note.completion_rate == Decimal("75.00")
        assert note.is_complete is False


# =============================================================================
# TENANT ISOLATION TESTS
# =============================================================================


class TestTenantIsolation:
    """Tests d'isolation multi-tenant."""

    @pytest.mark.asyncio
    async def test_delivery_note_tenant_isolation(self, mock_db, sample_lines):
        """Test isolation BL entre tenants."""
        service1 = DeliveryService(db=mock_db, tenant_id="tenant-1")
        service2 = DeliveryService(db=mock_db, tenant_id="tenant-2")

        note = await service1.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )

        result = await service2.get_delivery_note(note.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_shipment_tenant_isolation(self, mock_db, sample_lines):
        """Test isolation expéditions entre tenants."""
        service1 = DeliveryService(db=mock_db, tenant_id="tenant-a")
        service2 = DeliveryService(db=mock_db, tenant_id="tenant-b")

        note = await service1.create_delivery_note(
            customer_id="cust-1",
            customer_name="Client",
            lines=sample_lines,
        )
        await service1.confirm_delivery_note(note.id)
        shipment = await service1.ship(note.id, "c", "C", "T123")

        result = await service2.get_shipment(shipment.id)
        assert result is None
