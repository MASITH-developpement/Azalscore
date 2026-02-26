"""
Tests pour le module Traceability (Lots et Numéros de Série).

Couverture:
- Lot management
- Serial number management
- Traceability movements
- Expiry tracking
- Recall management
- Statistics
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.modules.production.traceability import (
    TraceabilityService,
    Lot,
    SerialNumber,
    TraceabilityMovement,
    LotStatus,
    SerialStatus,
    MovementType,
)
from app.modules.production.traceability.service import (
    TraceabilityChain,
    RecallReport,
)
from app.modules.production.traceability.router import router


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
    return "tenant-trace-test"


@pytest.fixture
def trace_service(mock_db, tenant_id):
    """Traceability service instance."""
    return TraceabilityService(db=mock_db, tenant_id=tenant_id)


# =============================================================================
# SERVICE TESTS - INITIALIZATION
# =============================================================================


class TestTraceabilityServiceInit:
    """Tests d'initialisation du service."""

    def test_init_with_valid_tenant(self, mock_db, tenant_id):
        """Test init avec tenant valide."""
        service = TraceabilityService(db=mock_db, tenant_id=tenant_id)
        assert service.tenant_id == tenant_id
        assert service.db == mock_db

    def test_init_without_tenant_raises(self, mock_db):
        """Test init sans tenant lève exception."""
        with pytest.raises(ValueError, match="tenant_id est requis"):
            TraceabilityService(db=mock_db, tenant_id="")

    def test_init_with_none_tenant_raises(self, mock_db):
        """Test init avec tenant None lève exception."""
        with pytest.raises(ValueError, match="tenant_id est requis"):
            TraceabilityService(db=mock_db, tenant_id=None)


# =============================================================================
# SERVICE TESTS - LOT MANAGEMENT
# =============================================================================


class TestLotManagement:
    """Tests de gestion des lots."""

    @pytest.mark.asyncio
    async def test_create_lot(self, trace_service):
        """Test création lot."""
        lot = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit Test",
            quantity=Decimal("100"),
        )

        assert lot.id is not None
        assert lot.tenant_id == trace_service.tenant_id
        assert lot.lot_number.startswith("LOT-")
        assert lot.initial_quantity == Decimal("100")
        assert lot.current_quantity == Decimal("100")
        assert lot.status == LotStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_create_lot_with_expiry(self, trace_service):
        """Test création lot avec date d'expiration."""
        expiry = date.today() + timedelta(days=30)

        lot = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit Périssable",
            quantity=Decimal("50"),
            expiry_date=expiry,
        )

        assert lot.expiry_date == expiry
        assert lot.is_expired is False
        assert lot.days_until_expiry == 30

    @pytest.mark.asyncio
    async def test_lot_is_expired(self, trace_service):
        """Test détection lot expiré."""
        # Lot expiré hier
        lot = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit Expiré",
            quantity=Decimal("10"),
            expiry_date=date.today() - timedelta(days=1),
        )

        assert lot.is_expired is True
        assert lot.days_until_expiry == -1

    @pytest.mark.asyncio
    async def test_get_lot(self, trace_service):
        """Test récupération lot."""
        lot = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )

        retrieved = await trace_service.get_lot(lot.id)

        assert retrieved is not None
        assert retrieved.id == lot.id

    @pytest.mark.asyncio
    async def test_get_lot_by_number(self, trace_service):
        """Test récupération lot par numéro."""
        lot = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )

        retrieved = await trace_service.get_lot_by_number(lot.lot_number)

        assert retrieved is not None
        assert retrieved.lot_number == lot.lot_number

    @pytest.mark.asyncio
    async def test_consume_lot(self, trace_service):
        """Test consommation lot."""
        lot = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )

        consumed = await trace_service.consume_lot(
            lot_id=lot.id,
            quantity=Decimal("30"),
        )

        assert consumed.current_quantity == Decimal("70")
        assert consumed.consumed_quantity == Decimal("30")

    @pytest.mark.asyncio
    async def test_consume_lot_exceeds_quantity(self, trace_service):
        """Test consommation dépassant quantité."""
        lot = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("50"),
        )

        with pytest.raises(ValueError, match="Quantité insuffisante"):
            await trace_service.consume_lot(
                lot_id=lot.id,
                quantity=Decimal("100"),
            )

    @pytest.mark.asyncio
    async def test_consume_lot_full_consumption(self, trace_service):
        """Test consommation totale lot."""
        lot = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("50"),
        )

        consumed = await trace_service.consume_lot(
            lot_id=lot.id,
            quantity=Decimal("50"),
        )

        assert consumed.current_quantity == Decimal("0")
        assert consumed.status == LotStatus.CONSUMED

    @pytest.mark.asyncio
    async def test_transfer_lot_partial(self, trace_service):
        """Test transfert partiel lot."""
        lot = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
            location_id="loc-1",
        )

        transferred = await trace_service.transfer_lot(
            lot_id=lot.id,
            quantity=Decimal("40"),
            to_location_id="loc-2",
        )

        # Nouveau lot créé pour la partie transférée
        assert transferred.location_id == "loc-2"
        assert transferred.current_quantity == Decimal("40")

        # Ancien lot réduit
        original = await trace_service.get_lot(lot.id)
        assert original.current_quantity == Decimal("60")

    @pytest.mark.asyncio
    async def test_transfer_lot_full(self, trace_service):
        """Test transfert total lot."""
        lot = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
            location_id="loc-1",
        )

        transferred = await trace_service.transfer_lot(
            lot_id=lot.id,
            quantity=Decimal("100"),
            to_location_id="loc-2",
        )

        assert transferred.id == lot.id  # Même lot
        assert transferred.location_id == "loc-2"

    @pytest.mark.asyncio
    async def test_quarantine_lot(self, trace_service):
        """Test mise en quarantaine."""
        lot = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )

        quarantined = await trace_service.quarantine_lot(
            lot_id=lot.id,
            reason="Contrôle qualité",
        )

        assert quarantined.status == LotStatus.QUARANTINE
        assert "Quarantaine" in quarantined.notes

    @pytest.mark.asyncio
    async def test_release_lot(self, trace_service):
        """Test libération de quarantaine."""
        lot = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )
        await trace_service.quarantine_lot(lot.id, "Test")

        released = await trace_service.release_lot(lot.id)

        assert released.status == LotStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_list_lots(self, trace_service):
        """Test liste des lots."""
        await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit 1",
            quantity=Decimal("100"),
        )
        await trace_service.create_lot(
            product_id="prod-2",
            product_name="Produit 2",
            quantity=Decimal("200"),
        )

        lots = await trace_service.list_lots()

        assert len(lots) == 2

    @pytest.mark.asyncio
    async def test_list_lots_filter_by_product(self, trace_service):
        """Test filtre lots par produit."""
        await trace_service.create_lot(
            product_id="target-prod",
            product_name="Target",
            quantity=Decimal("100"),
        )
        await trace_service.create_lot(
            product_id="other-prod",
            product_name="Other",
            quantity=Decimal("100"),
        )

        lots = await trace_service.list_lots(product_id="target-prod")

        assert len(lots) == 1
        assert lots[0].product_id == "target-prod"

    @pytest.mark.asyncio
    async def test_check_expiring_lots(self, trace_service):
        """Test lots expirant bientôt."""
        # Lot expire dans 10 jours
        await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
            expiry_date=date.today() + timedelta(days=10),
        )
        # Lot expire dans 60 jours
        await trace_service.create_lot(
            product_id="prod-2",
            product_name="Produit 2",
            quantity=Decimal("100"),
            expiry_date=date.today() + timedelta(days=60),
        )

        expiring = await trace_service.check_expiring_lots(days=30)

        assert len(expiring) == 1


# =============================================================================
# SERVICE TESTS - SERIAL NUMBER MANAGEMENT
# =============================================================================


class TestSerialNumberManagement:
    """Tests de gestion des numéros de série."""

    @pytest.mark.asyncio
    async def test_create_serial(self, trace_service):
        """Test création numéro de série."""
        serial = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
        )

        assert serial.id is not None
        assert serial.tenant_id == trace_service.tenant_id
        assert serial.serial_number.startswith("SN-")
        assert serial.status == SerialStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_create_serial_with_custom_number(self, trace_service):
        """Test création avec numéro personnalisé."""
        serial = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
            serial_number="CUSTOM-12345",
        )

        assert serial.serial_number == "CUSTOM-12345"

    @pytest.mark.asyncio
    async def test_create_serial_with_warranty(self, trace_service):
        """Test série avec garantie."""
        serial = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
            warranty_months=24,
        )

        assert serial.warranty_end is not None
        assert serial.is_under_warranty is True

    @pytest.mark.asyncio
    async def test_create_serial_batch(self, trace_service):
        """Test création lot de séries."""
        serials = await trace_service.create_serial_batch(
            product_id="prod-1",
            product_name="Produit",
            quantity=5,
            prefix="BATCH",
        )

        assert len(serials) == 5
        assert all(s.serial_number.startswith("BATCH-") for s in serials)

    @pytest.mark.asyncio
    async def test_get_serial(self, trace_service):
        """Test récupération série."""
        serial = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
        )

        retrieved = await trace_service.get_serial(serial.id)

        assert retrieved is not None
        assert retrieved.id == serial.id

    @pytest.mark.asyncio
    async def test_get_serial_by_number(self, trace_service):
        """Test récupération par numéro."""
        serial = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
            serial_number="FIND-ME-123",
        )

        retrieved = await trace_service.get_serial_by_number("FIND-ME-123")

        assert retrieved is not None
        assert retrieved.serial_number == "FIND-ME-123"

    @pytest.mark.asyncio
    async def test_sell_serial(self, trace_service):
        """Test vente série."""
        serial = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
        )

        sold = await trace_service.sell_serial(
            serial_id=serial.id,
            customer_id="cust-1",
            customer_name="Client Test",
        )

        assert sold.status == SerialStatus.SOLD
        assert sold.customer_id == "cust-1"
        assert sold.customer_name == "Client Test"

    @pytest.mark.asyncio
    async def test_sell_serial_not_available(self, trace_service):
        """Test vente série non disponible."""
        serial = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
        )
        await trace_service.sell_serial(serial.id, "cust-1", "Client")

        # Tenter de revendre
        result = await trace_service.sell_serial(serial.id, "cust-2", "Autre")

        assert result is None

    @pytest.mark.asyncio
    async def test_return_serial(self, trace_service):
        """Test retour série."""
        serial = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
        )
        await trace_service.sell_serial(serial.id, "cust-1", "Client")

        returned = await trace_service.return_serial(
            serial_id=serial.id,
            location_id="loc-retour",
            reason="Défectueux",
        )

        assert returned.status == SerialStatus.RETURNED
        assert returned.location_id == "loc-retour"

    @pytest.mark.asyncio
    async def test_mark_defective(self, trace_service):
        """Test marquer défectueux."""
        serial = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
        )

        defective = await trace_service.mark_defective(
            serial_id=serial.id,
            reason="Panne moteur",
        )

        assert defective.status == SerialStatus.DEFECTIVE
        assert "Panne moteur" in defective.notes

    @pytest.mark.asyncio
    async def test_list_serials(self, trace_service):
        """Test liste séries."""
        await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit 1",
        )
        await trace_service.create_serial(
            product_id="prod-2",
            product_name="Produit 2",
        )

        serials = await trace_service.list_serials()

        assert len(serials) == 2

    @pytest.mark.asyncio
    async def test_list_serials_by_status(self, trace_service):
        """Test filtre séries par statut."""
        serial1 = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
        )
        await trace_service.sell_serial(serial1.id, "cust", "Client")

        await trace_service.create_serial(
            product_id="prod-2",
            product_name="Produit 2",
        )

        available = await trace_service.list_serials(status=SerialStatus.AVAILABLE)
        sold = await trace_service.list_serials(status=SerialStatus.SOLD)

        assert len(available) == 1
        assert len(sold) == 1


# =============================================================================
# SERVICE TESTS - TRACEABILITY
# =============================================================================


class TestTraceability:
    """Tests de traçabilité."""

    @pytest.mark.asyncio
    async def test_get_lot_movements(self, trace_service):
        """Test historique lot."""
        lot = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )
        await trace_service.consume_lot(lot.id, Decimal("30"))

        movements = await trace_service.get_lot_movements(lot.id)

        assert len(movements) == 2  # Receipt + Consumption
        types = [m.movement_type for m in movements]
        assert MovementType.RECEIPT in types
        assert MovementType.CONSUMPTION in types

    @pytest.mark.asyncio
    async def test_get_serial_movements(self, trace_service):
        """Test historique série."""
        serial = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
        )
        await trace_service.sell_serial(serial.id, "cust", "Client")

        movements = await trace_service.get_serial_movements(serial.id)

        assert len(movements) == 2  # Production + Sale
        types = [m.movement_type for m in movements]
        assert MovementType.PRODUCTION in types
        assert MovementType.SALE in types

    @pytest.mark.asyncio
    async def test_get_traceability_chain_lot(self, trace_service):
        """Test chaîne traçabilité lot."""
        lot = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )
        await trace_service.consume_lot(lot.id, Decimal("30"))

        chain = await trace_service.get_traceability_chain(lot_id=lot.id)

        assert chain is not None
        assert chain.product_id == "prod-1"
        assert len(chain.upstream) > 0  # Receipt
        assert len(chain.downstream) > 0  # Consumption

    @pytest.mark.asyncio
    async def test_get_traceability_chain_serial(self, trace_service):
        """Test chaîne traçabilité série."""
        serial = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
        )
        await trace_service.sell_serial(serial.id, "cust", "Client")

        chain = await trace_service.get_traceability_chain(serial_id=serial.id)

        assert chain is not None
        assert chain.serial_id == serial.id


# =============================================================================
# SERVICE TESTS - RECALL MANAGEMENT
# =============================================================================


class TestRecallManagement:
    """Tests de gestion des rappels."""

    @pytest.mark.asyncio
    async def test_initiate_recall_lots(self, trace_service):
        """Test rappel lots."""
        lot1 = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )
        lot2 = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("50"),
        )

        report = await trace_service.initiate_recall(
            lot_ids=[lot1.id, lot2.id],
            reason="Contamination",
        )

        assert len(report.affected_lots) == 2
        assert report.total_quantity == Decimal("150")
        assert report.reason == "Contamination"

        # Vérifier statut lots
        recalled_lot = await trace_service.get_lot(lot1.id)
        assert recalled_lot.status == LotStatus.RECALLED

    @pytest.mark.asyncio
    async def test_initiate_recall_serials(self, trace_service):
        """Test rappel séries."""
        serial1 = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
        )
        await trace_service.sell_serial(serial1.id, "cust-1", "Client 1")

        serial2 = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
        )
        await trace_service.sell_serial(serial2.id, "cust-2", "Client 2")

        report = await trace_service.initiate_recall(
            serial_ids=[serial1.id, serial2.id],
            reason="Défaut de fabrication",
        )

        assert len(report.affected_serials) == 2
        assert len(report.customers_affected) == 2

        # Vérifier statut séries
        recalled_serial = await trace_service.get_serial(serial1.id)
        assert recalled_serial.status == SerialStatus.RECALLED

    @pytest.mark.asyncio
    async def test_recall_lot_with_serials(self, trace_service):
        """Test rappel lot avec séries associées."""
        lot = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("10"),
        )
        serial = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
            lot_id=lot.id,
        )

        report = await trace_service.initiate_recall(
            lot_ids=[lot.id],
            reason="Rappel complet",
        )

        # Le lot ET la série sont rappelés
        assert lot.lot_number in report.affected_lots
        assert serial.serial_number in report.affected_serials


# =============================================================================
# SERVICE TESTS - STATISTICS
# =============================================================================


class TestStatistics:
    """Tests des statistiques."""

    @pytest.mark.asyncio
    async def test_get_statistics_empty(self, trace_service):
        """Test stats sans données."""
        stats = await trace_service.get_statistics()

        assert stats["total_lots"] == 0
        assert stats["total_serials"] == 0

    @pytest.mark.asyncio
    async def test_get_statistics_with_data(self, trace_service):
        """Test stats avec données."""
        # Créer lots
        lot1 = await trace_service.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
            expiry_date=date.today() + timedelta(days=10),
        )
        await trace_service.create_lot(
            product_id="prod-2",
            product_name="Produit 2",
            quantity=Decimal("50"),
            expiry_date=date.today() - timedelta(days=1),  # Expiré
        )

        # Créer séries
        serial = await trace_service.create_serial(
            product_id="prod-1",
            product_name="Produit",
        )
        await trace_service.sell_serial(serial.id, "cust", "Client")

        await trace_service.create_serial(
            product_id="prod-2",
            product_name="Produit 2",
        )

        stats = await trace_service.get_statistics()

        assert stats["total_lots"] == 2
        assert stats["expired_lots"] == 1
        assert stats["expiring_within_30_days"] == 1
        assert stats["total_serials"] == 2
        assert stats["sold_serials"] == 1
        assert stats["available_serials"] == 1


# =============================================================================
# ROUTER TESTS
# =============================================================================


class TestTraceabilityRouter:
    """Tests des endpoints API Traceability."""

    @pytest.fixture
    def mock_service(self):
        """Service mocké."""
        return AsyncMock(spec=TraceabilityService)

    @pytest.fixture
    def test_app(self, mock_service):
        """App de test avec service mocké."""
        app = FastAPI()
        app.include_router(router)

        async def override_service():
            return mock_service

        from app.modules.production.traceability import router as trace_router_module

        app.dependency_overrides[trace_router_module.get_traceability_service] = override_service
        return app

    @pytest.fixture
    def test_client(self, test_app):
        """Client de test."""
        return TestClient(test_app)

    def test_create_lot_endpoint(self, test_client, mock_service):
        """Test endpoint création lot."""
        mock_lot = Lot(
            id="lot-123",
            tenant_id="test-tenant",
            lot_number="LOT-202602-00001",
            product_id="prod-1",
            product_name="Test Product",
            initial_quantity=Decimal("100"),
            current_quantity=Decimal("100"),
        )
        mock_service.create_lot.return_value = mock_lot

        response = test_client.post(
            "/v3/production/traceability/lots",
            json={
                "product_id": "prod-1",
                "product_name": "Test Product",
                "quantity": 100,
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "lot-123"

    def test_list_lots_endpoint(self, test_client, mock_service):
        """Test endpoint liste lots."""
        mock_service.list_lots.return_value = [
            Lot(
                id="lot-1",
                tenant_id="test-tenant",
                lot_number="LOT-1",
                product_id="prod-1",
                product_name="Product 1",
                initial_quantity=Decimal("100"),
                current_quantity=Decimal("80"),
            ),
        ]

        response = test_client.get(
            "/v3/production/traceability/lots",
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_create_serial_endpoint(self, test_client, mock_service):
        """Test endpoint création série."""
        mock_serial = SerialNumber(
            id="serial-123",
            tenant_id="test-tenant",
            serial_number="SN-12345",
            product_id="prod-1",
            product_name="Product",
        )
        mock_service.create_serial.return_value = mock_serial

        response = test_client.post(
            "/v3/production/traceability/serials",
            json={
                "product_id": "prod-1",
                "product_name": "Product",
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 201

    def test_create_serial_batch_endpoint(self, test_client, mock_service):
        """Test endpoint création lot de séries."""
        mock_service.create_serial_batch.return_value = [
            SerialNumber(
                id=f"serial-{i}",
                tenant_id="test-tenant",
                serial_number=f"SN-{i}",
                product_id="prod-1",
                product_name="Product",
            )
            for i in range(3)
        ]

        response = test_client.post(
            "/v3/production/traceability/serials/batch",
            json={
                "product_id": "prod-1",
                "product_name": "Product",
                "quantity": 3,
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data) == 3

    def test_consume_lot_endpoint(self, test_client, mock_service):
        """Test endpoint consommation lot."""
        mock_lot = Lot(
            id="lot-123",
            tenant_id="test-tenant",
            lot_number="LOT-1",
            product_id="prod-1",
            product_name="Product",
            initial_quantity=Decimal("100"),
            current_quantity=Decimal("70"),
        )
        mock_service.consume_lot.return_value = mock_lot

        response = test_client.post(
            "/v3/production/traceability/lots/lot-123/consume",
            json={"quantity": 30},
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200

    def test_sell_serial_endpoint(self, test_client, mock_service):
        """Test endpoint vente série."""
        mock_serial = SerialNumber(
            id="serial-123",
            tenant_id="test-tenant",
            serial_number="SN-12345",
            product_id="prod-1",
            product_name="Product",
            status=SerialStatus.SOLD,
            customer_id="cust-1",
        )
        mock_service.sell_serial.return_value = mock_serial

        response = test_client.post(
            "/v3/production/traceability/serials/serial-123/sell",
            json={"customer_id": "cust-1", "customer_name": "Client"},
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200

    def test_recall_endpoint(self, test_client, mock_service):
        """Test endpoint rappel."""
        mock_report = RecallReport(
            id="recall-123",
            tenant_id="test-tenant",
            reason="Défaut",
            affected_lots=["LOT-1"],
            affected_serials=["SN-1"],
            customers_affected=["cust-1"],
            total_quantity=Decimal("100"),
        )
        mock_service.initiate_recall.return_value = mock_report

        response = test_client.post(
            "/v3/production/traceability/recall",
            json={
                "lot_ids": ["lot-1"],
                "reason": "Défaut",
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["reason"] == "Défaut"

    def test_stats_endpoint(self, test_client, mock_service):
        """Test endpoint statistiques."""
        mock_service.get_statistics.return_value = {
            "total_lots": 10,
            "active_lots": 8,
            "expired_lots": 1,
            "expiring_within_30_days": 2,
            "quarantine_lots": 0,
            "total_serials": 50,
            "available_serials": 30,
            "sold_serials": 18,
            "under_warranty": 45,
            "total_movements": 100,
        }

        response = test_client.get(
            "/v3/production/traceability/stats",
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_lots"] == 10


# =============================================================================
# TENANT ISOLATION TESTS
# =============================================================================


class TestTenantIsolation:
    """Tests d'isolation multi-tenant."""

    @pytest.mark.asyncio
    async def test_lot_tenant_isolation(self, mock_db):
        """Test isolation lots entre tenants."""
        service1 = TraceabilityService(db=mock_db, tenant_id="tenant-1")
        service2 = TraceabilityService(db=mock_db, tenant_id="tenant-2")

        lot = await service1.create_lot(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )

        # Tenant 2 ne voit pas le lot de tenant 1
        result = await service2.get_lot(lot.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_serial_tenant_isolation(self, mock_db):
        """Test isolation séries entre tenants."""
        service1 = TraceabilityService(db=mock_db, tenant_id="tenant-a")
        service2 = TraceabilityService(db=mock_db, tenant_id="tenant-b")

        serial = await service1.create_serial(
            product_id="prod-1",
            product_name="Produit",
        )

        result = await service2.get_serial(serial.id)
        assert result is None


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestDataclasses:
    """Tests des dataclasses."""

    def test_lot_consumed_quantity(self):
        """Test quantité consommée lot."""
        lot = Lot(
            id="l1",
            tenant_id="t1",
            lot_number="LOT-1",
            product_id="p1",
            product_name="Product",
            initial_quantity=Decimal("100"),
            current_quantity=Decimal("70"),
        )

        assert lot.consumed_quantity == Decimal("30")

    def test_lot_days_until_expiry(self):
        """Test jours avant expiration."""
        lot = Lot(
            id="l1",
            tenant_id="t1",
            lot_number="LOT-1",
            product_id="p1",
            product_name="Product",
            initial_quantity=Decimal("100"),
            current_quantity=Decimal("100"),
            expiry_date=date.today() + timedelta(days=15),
        )

        assert lot.days_until_expiry == 15
        assert lot.is_expired is False

    def test_serial_under_warranty(self):
        """Test garantie série."""
        serial = SerialNumber(
            id="s1",
            tenant_id="t1",
            serial_number="SN-1",
            product_id="p1",
            product_name="Product",
            warranty_end=date.today() + timedelta(days=365),
        )

        assert serial.is_under_warranty is True

    def test_serial_warranty_expired(self):
        """Test garantie expirée."""
        serial = SerialNumber(
            id="s1",
            tenant_id="t1",
            serial_number="SN-1",
            product_id="p1",
            product_name="Product",
            warranty_end=date.today() - timedelta(days=1),
        )

        assert serial.is_under_warranty is False
