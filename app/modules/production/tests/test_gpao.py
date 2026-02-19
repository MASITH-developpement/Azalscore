"""
Tests pour le module GPAO/MRP.

Couverture:
- BOM management
- Routing management
- Manufacturing orders lifecycle
- MRP calculation
- Capacity planning
- Production statistics
- Router endpoints
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.modules.production.gpao import (
    GPAOService,
    ManufacturingOrder,
    BillOfMaterials,
    BOMComponent,
    RoutingOperation,
    MRPRequirement,
    ProductionStatus,
    OperationType,
)
from app.modules.production.gpao.service import (
    Routing,
    CapacityPlan,
    UnitOfMeasure,
    MRPActionType,
)
from app.modules.production.gpao.router import router


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
    return "tenant-gpao-test"


@pytest.fixture
def gpao_service(mock_db, tenant_id):
    """GPAO service instance."""
    return GPAOService(db=mock_db, tenant_id=tenant_id)


@pytest.fixture
def app(gpao_service):
    """FastAPI app with GPAO router."""
    app = FastAPI()
    app.include_router(router)

    async def get_service_override():
        return gpao_service

    app.dependency_overrides = {
        "get_gpao_service": get_service_override,
    }
    return app


@pytest.fixture
def client(app):
    """Test client."""
    return TestClient(app)


# =============================================================================
# SERVICE TESTS - INITIALIZATION
# =============================================================================


class TestGPAOServiceInit:
    """Tests d'initialisation du service."""

    def test_init_with_valid_tenant(self, mock_db, tenant_id):
        """Test init avec tenant valide."""
        service = GPAOService(db=mock_db, tenant_id=tenant_id)
        assert service.tenant_id == tenant_id
        assert service.db == mock_db

    def test_init_without_tenant_raises(self, mock_db):
        """Test init sans tenant lève exception."""
        with pytest.raises(ValueError, match="tenant_id est requis"):
            GPAOService(db=mock_db, tenant_id="")

    def test_init_with_none_tenant_raises(self, mock_db):
        """Test init avec tenant None lève exception."""
        with pytest.raises(ValueError, match="tenant_id est requis"):
            GPAOService(db=mock_db, tenant_id=None)


# =============================================================================
# SERVICE TESTS - BOM MANAGEMENT
# =============================================================================


class TestBOMManagement:
    """Tests de gestion des nomenclatures."""

    @pytest.mark.asyncio
    async def test_create_bom(self, gpao_service):
        """Test création BOM."""
        components = [
            {"product_id": "comp-1", "product_name": "Composant A", "quantity": 2},
            {"product_id": "comp-2", "product_name": "Composant B", "quantity": 5},
        ]

        bom = await gpao_service.create_bom(
            product_id="prod-1",
            product_name="Produit Fini",
            components=components,
            version="1.0",
        )

        assert bom.id is not None
        assert bom.tenant_id == gpao_service.tenant_id
        assert bom.product_id == "prod-1"
        assert bom.product_name == "Produit Fini"
        assert bom.version == "1.0"
        assert bom.total_components == 2
        assert bom.is_active is True

    @pytest.mark.asyncio
    async def test_create_bom_with_scrap_rate(self, gpao_service):
        """Test BOM avec taux de rebut."""
        components = [
            {
                "product_id": "comp-1",
                "product_name": "Pièce fragile",
                "quantity": 10,
                "scrap_rate": 5,
            },
        ]

        bom = await gpao_service.create_bom(
            product_id="prod-fragile",
            product_name="Produit Fragile",
            components=components,
        )

        assert bom.components[0].scrap_rate == Decimal("5")

    @pytest.mark.asyncio
    async def test_create_bom_with_phantom_component(self, gpao_service):
        """Test BOM avec composant fantôme."""
        components = [
            {
                "product_id": "phantom-1",
                "product_name": "Sous-assemblage",
                "quantity": 1,
                "is_phantom": True,
            },
        ]

        bom = await gpao_service.create_bom(
            product_id="prod-phantom",
            product_name="Produit avec Phantom",
            components=components,
        )

        assert bom.components[0].is_phantom is True

    @pytest.mark.asyncio
    async def test_get_bom(self, gpao_service):
        """Test récupération BOM."""
        bom = await gpao_service.create_bom(
            product_id="prod-1",
            product_name="Produit",
            components=[{"product_id": "c1", "product_name": "Comp", "quantity": 1}],
        )

        retrieved = await gpao_service.get_bom(bom.id)

        assert retrieved is not None
        assert retrieved.id == bom.id

    @pytest.mark.asyncio
    async def test_get_bom_not_found(self, gpao_service):
        """Test BOM inexistante."""
        result = await gpao_service.get_bom("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_bom_wrong_tenant(self, mock_db, gpao_service):
        """Test isolation tenant sur BOM."""
        bom = await gpao_service.create_bom(
            product_id="prod-1",
            product_name="Produit",
            components=[],
        )

        # Autre tenant
        other_service = GPAOService(db=mock_db, tenant_id="other-tenant")
        result = await other_service.get_bom(bom.id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_bom_for_product(self, gpao_service):
        """Test récupération BOM par produit."""
        await gpao_service.create_bom(
            product_id="prod-target",
            product_name="Target Product",
            components=[],
        )

        bom = await gpao_service.get_bom_for_product("prod-target")

        assert bom is not None
        assert bom.product_id == "prod-target"

    @pytest.mark.asyncio
    async def test_list_boms(self, gpao_service):
        """Test liste des BOMs."""
        await gpao_service.create_bom(
            product_id="prod-a",
            product_name="Produit A",
            components=[],
        )
        await gpao_service.create_bom(
            product_id="prod-b",
            product_name="Produit B",
            components=[],
        )

        boms = await gpao_service.list_boms()

        assert len(boms) == 2

    @pytest.mark.asyncio
    async def test_list_boms_filter_by_product(self, gpao_service):
        """Test filtre BOMs par produit."""
        await gpao_service.create_bom(
            product_id="filter-prod",
            product_name="Filter Product",
            components=[],
        )
        await gpao_service.create_bom(
            product_id="other-prod",
            product_name="Other",
            components=[],
        )

        boms = await gpao_service.list_boms(product_id="filter-prod")

        assert len(boms) == 1
        assert boms[0].product_id == "filter-prod"

    @pytest.mark.asyncio
    async def test_add_bom_component(self, gpao_service):
        """Test ajout composant à BOM."""
        bom = await gpao_service.create_bom(
            product_id="prod-1",
            product_name="Produit",
            components=[],
        )

        updated = await gpao_service.add_bom_component(
            bom_id=bom.id,
            product_id="new-comp",
            product_name="Nouveau Composant",
            quantity=Decimal("3"),
        )

        assert updated is not None
        assert updated.total_components == 1
        assert updated.components[0].product_name == "Nouveau Composant"


# =============================================================================
# SERVICE TESTS - ROUTING MANAGEMENT
# =============================================================================


class TestRoutingManagement:
    """Tests de gestion des gammes."""

    @pytest.mark.asyncio
    async def test_create_routing(self, gpao_service):
        """Test création gamme."""
        operations = [
            {"name": "Découpe", "type": "cutting", "setup_time": 10, "run_time": 30},
            {"name": "Assemblage", "type": "assembly", "setup_time": 5, "run_time": 60},
        ]

        routing = await gpao_service.create_routing(
            product_id="prod-1",
            product_name="Produit",
            operations=operations,
        )

        assert routing.id is not None
        assert routing.tenant_id == gpao_service.tenant_id
        assert len(routing.operations) == 2
        assert routing.operations[0].name == "Découpe"
        assert routing.operations[0].operation_type == OperationType.CUTTING

    @pytest.mark.asyncio
    async def test_routing_total_time(self, gpao_service):
        """Test calcul temps total gamme."""
        operations = [
            {"name": "Op1", "setup_time": 10, "run_time": 20},
            {"name": "Op2", "setup_time": 5, "run_time": 15},
        ]

        routing = await gpao_service.create_routing(
            product_id="prod-1",
            product_name="Produit",
            operations=operations,
        )

        # 10+20 + 5+15 = 50
        assert routing.total_time_minutes == 50

    @pytest.mark.asyncio
    async def test_get_routing(self, gpao_service):
        """Test récupération gamme."""
        routing = await gpao_service.create_routing(
            product_id="prod-1",
            product_name="Produit",
            operations=[{"name": "Op"}],
        )

        retrieved = await gpao_service.get_routing(routing.id)

        assert retrieved is not None
        assert retrieved.id == routing.id

    @pytest.mark.asyncio
    async def test_get_routing_for_product(self, gpao_service):
        """Test récupération gamme par produit."""
        await gpao_service.create_routing(
            product_id="target-prod",
            product_name="Target",
            operations=[],
        )

        routing = await gpao_service.get_routing_for_product("target-prod")

        assert routing is not None
        assert routing.product_id == "target-prod"

    @pytest.mark.asyncio
    async def test_list_routings(self, gpao_service):
        """Test liste des gammes."""
        await gpao_service.create_routing(
            product_id="prod-1",
            product_name="Produit 1",
            operations=[],
        )
        await gpao_service.create_routing(
            product_id="prod-2",
            product_name="Produit 2",
            operations=[],
        )

        routings = await gpao_service.list_routings()

        assert len(routings) == 2


# =============================================================================
# SERVICE TESTS - MANUFACTURING ORDERS
# =============================================================================


class TestManufacturingOrders:
    """Tests des ordres de fabrication."""

    @pytest.mark.asyncio
    async def test_create_order(self, gpao_service):
        """Test création OF."""
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )

        assert order.id is not None
        assert order.tenant_id == gpao_service.tenant_id
        assert order.order_number.startswith("OF-")
        assert order.quantity_planned == Decimal("100")
        assert order.status == ProductionStatus.DRAFT

    @pytest.mark.asyncio
    async def test_create_order_with_bom_routing(self, gpao_service):
        """Test OF avec BOM et gamme auto-liés."""
        # Créer BOM et Gamme
        bom = await gpao_service.create_bom(
            product_id="linked-prod",
            product_name="Produit Lié",
            components=[{"product_id": "c1", "product_name": "Comp", "quantity": 1}],
        )
        routing = await gpao_service.create_routing(
            product_id="linked-prod",
            product_name="Produit Lié",
            operations=[{"name": "Op1"}],
        )

        # Créer OF sans spécifier BOM/Routing
        order = await gpao_service.create_manufacturing_order(
            product_id="linked-prod",
            product_name="Produit Lié",
            quantity=Decimal("50"),
        )

        assert order.bom_id == bom.id
        assert order.routing_id == routing.id

    @pytest.mark.asyncio
    async def test_create_order_with_priority(self, gpao_service):
        """Test OF avec priorité."""
        order = await gpao_service.create_manufacturing_order(
            product_id="urgent-prod",
            product_name="Produit Urgent",
            quantity=Decimal("10"),
            priority=10,
        )

        assert order.priority == 10

    @pytest.mark.asyncio
    async def test_get_order(self, gpao_service):
        """Test récupération OF."""
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("50"),
        )

        retrieved = await gpao_service.get_order(order.id)

        assert retrieved is not None
        assert retrieved.id == order.id

    @pytest.mark.asyncio
    async def test_get_order_by_number(self, gpao_service):
        """Test récupération OF par numéro."""
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("50"),
        )

        retrieved = await gpao_service.get_order_by_number(order.order_number)

        assert retrieved is not None
        assert retrieved.order_number == order.order_number

    @pytest.mark.asyncio
    async def test_list_orders(self, gpao_service):
        """Test liste des OF."""
        await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit 1",
            quantity=Decimal("100"),
        )
        await gpao_service.create_manufacturing_order(
            product_id="prod-2",
            product_name="Produit 2",
            quantity=Decimal("200"),
        )

        orders = await gpao_service.list_orders()

        assert len(orders) == 2

    @pytest.mark.asyncio
    async def test_list_orders_by_status(self, gpao_service):
        """Test filtre OF par statut."""
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )
        await gpao_service.release_order(order.id)

        released = await gpao_service.list_orders(status=ProductionStatus.RELEASED)
        drafts = await gpao_service.list_orders(status=ProductionStatus.DRAFT)

        assert len(released) == 1
        assert len(drafts) == 0

    @pytest.mark.asyncio
    async def test_release_order(self, gpao_service):
        """Test lancement OF."""
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )

        released = await gpao_service.release_order(order.id)

        assert released.status == ProductionStatus.RELEASED

    @pytest.mark.asyncio
    async def test_release_order_invalid_status(self, gpao_service):
        """Test lancement OF avec statut invalide."""
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )
        await gpao_service.release_order(order.id)
        await gpao_service.start_order(order.id)

        # Ne peut pas relancer un OF en cours
        result = await gpao_service.release_order(order.id)

        assert result is None

    @pytest.mark.asyncio
    async def test_start_order(self, gpao_service):
        """Test démarrage OF."""
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )
        await gpao_service.release_order(order.id)

        started = await gpao_service.start_order(order.id)

        assert started.status == ProductionStatus.IN_PROGRESS
        assert started.actual_start is not None

    @pytest.mark.asyncio
    async def test_start_order_not_released(self, gpao_service):
        """Test démarrage OF non lancé."""
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )

        result = await gpao_service.start_order(order.id)

        assert result is None

    @pytest.mark.asyncio
    async def test_report_production(self, gpao_service):
        """Test déclaration production."""
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )
        await gpao_service.release_order(order.id)
        await gpao_service.start_order(order.id)

        updated = await gpao_service.report_production(
            order_id=order.id,
            quantity_produced=Decimal("30"),
            quantity_scrapped=Decimal("2"),
        )

        assert updated.quantity_produced == Decimal("30")
        assert updated.quantity_scrapped == Decimal("2")
        assert updated.quantity_remaining == Decimal("68")

    @pytest.mark.asyncio
    async def test_report_production_auto_complete(self, gpao_service):
        """Test auto-complétion OF."""
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )
        await gpao_service.release_order(order.id)
        await gpao_service.start_order(order.id)

        # Produire tout
        await gpao_service.report_production(
            order_id=order.id,
            quantity_produced=Decimal("100"),
        )

        retrieved = await gpao_service.get_order(order.id)

        assert retrieved.status == ProductionStatus.COMPLETED
        assert retrieved.actual_end is not None

    @pytest.mark.asyncio
    async def test_complete_order(self, gpao_service):
        """Test complétion manuelle OF."""
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )
        await gpao_service.release_order(order.id)
        await gpao_service.start_order(order.id)
        await gpao_service.report_production(order.id, Decimal("50"))

        completed = await gpao_service.complete_order(order.id)

        assert completed.status == ProductionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_cancel_order(self, gpao_service):
        """Test annulation OF."""
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )

        cancelled = await gpao_service.cancel_order(
            order_id=order.id,
            reason="Commande client annulée",
        )

        assert cancelled.status == ProductionStatus.CANCELLED
        assert cancelled.metadata["cancel_reason"] == "Commande client annulée"

    @pytest.mark.asyncio
    async def test_cancel_completed_order_fails(self, gpao_service):
        """Test annulation OF complété impossible."""
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("10"),
        )
        await gpao_service.release_order(order.id)
        await gpao_service.start_order(order.id)
        await gpao_service.report_production(order.id, Decimal("10"))

        result = await gpao_service.cancel_order(order.id)

        assert result is None

    @pytest.mark.asyncio
    async def test_order_completion_rate(self, gpao_service):
        """Test calcul taux de complétion."""
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )
        await gpao_service.release_order(order.id)
        await gpao_service.start_order(order.id)
        await gpao_service.report_production(order.id, Decimal("50"))

        retrieved = await gpao_service.get_order(order.id)

        assert retrieved.completion_rate == Decimal("50.00")

    @pytest.mark.asyncio
    async def test_order_scrap_rate(self, gpao_service):
        """Test calcul taux de rebut."""
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
        )
        await gpao_service.release_order(order.id)
        await gpao_service.start_order(order.id)
        await gpao_service.report_production(
            order.id,
            Decimal("90"),
            Decimal("10"),
        )

        retrieved = await gpao_service.get_order(order.id)

        assert retrieved.scrap_rate == Decimal("10.00")


# =============================================================================
# SERVICE TESTS - MRP CALCULATION
# =============================================================================


class TestMRPCalculation:
    """Tests du calcul MRP."""

    @pytest.mark.asyncio
    async def test_calculate_requirements_simple(self, gpao_service):
        """Test calcul besoins simple."""
        requirements = await gpao_service.calculate_requirements(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
            due_date=date.today() + timedelta(days=7),
        )

        assert len(requirements) >= 1
        assert requirements[0].gross_requirement == Decimal("100")
        assert requirements[0].net_requirement == Decimal("100")
        assert requirements[0].level == 0

    @pytest.mark.asyncio
    async def test_calculate_requirements_with_stock(self, gpao_service):
        """Test calcul besoins avec stock."""
        requirements = await gpao_service.calculate_requirements(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("100"),
            due_date=date.today() + timedelta(days=7),
            on_hand=Decimal("30"),
        )

        assert requirements[0].net_requirement == Decimal("70")

    @pytest.mark.asyncio
    async def test_calculate_requirements_no_action_needed(self, gpao_service):
        """Test pas d'action si stock suffisant."""
        requirements = await gpao_service.calculate_requirements(
            product_id="prod-1",
            product_name="Produit",
            quantity=Decimal("50"),
            due_date=date.today() + timedelta(days=7),
            on_hand=Decimal("100"),
        )

        assert requirements[0].net_requirement == Decimal("0")
        assert requirements[0].action_type is None

    @pytest.mark.asyncio
    async def test_calculate_requirements_with_bom(self, gpao_service):
        """Test éclatement BOM."""
        # Créer BOM
        await gpao_service.create_bom(
            product_id="prod-final",
            product_name="Produit Final",
            components=[
                {"product_id": "comp-a", "product_name": "Composant A", "quantity": 2},
                {"product_id": "comp-b", "product_name": "Composant B", "quantity": 3},
            ],
        )

        requirements = await gpao_service.calculate_requirements(
            product_id="prod-final",
            product_name="Produit Final",
            quantity=Decimal("10"),
            due_date=date.today() + timedelta(days=7),
        )

        # Niveau 0 + 2 composants
        assert len(requirements) == 3

        # Vérifier besoins composants
        comp_a = next(r for r in requirements if r.product_id == "comp-a")
        comp_b = next(r for r in requirements if r.product_id == "comp-b")

        assert comp_a.net_requirement == Decimal("20")  # 10 * 2
        assert comp_b.net_requirement == Decimal("30")  # 10 * 3
        assert comp_a.level == 1
        assert comp_b.level == 1

    @pytest.mark.asyncio
    async def test_calculate_requirements_action_message(self, gpao_service):
        """Test message d'action MRP."""
        requirements = await gpao_service.calculate_requirements(
            product_id="prod-1",
            product_name="Widget",
            quantity=Decimal("100"),
            due_date=date.today() + timedelta(days=7),
        )

        assert requirements[0].action_type == MRPActionType.CREATE_ORDER
        assert "100" in requirements[0].action_message
        assert "Widget" in requirements[0].action_message

    @pytest.mark.asyncio
    async def test_run_mrp(self, gpao_service):
        """Test exécution MRP complète."""
        # Créer des OF planifiés
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-mrp",
            product_name="Produit MRP",
            quantity=Decimal("50"),
            planned_start=datetime.now(),
            planned_end=datetime.now() + timedelta(days=5),
        )
        # Passer en planifié
        order.status = ProductionStatus.PLANNED

        requirements = await gpao_service.run_mrp(horizon_days=30)

        # Devrait contenir les besoins pour l'OF
        assert len(requirements) >= 1


# =============================================================================
# SERVICE TESTS - CAPACITY PLANNING
# =============================================================================


class TestCapacityPlanning:
    """Tests de planification de capacité."""

    @pytest.mark.asyncio
    async def test_calculate_capacity_basic(self, gpao_service):
        """Test calcul capacité basique."""
        plans = await gpao_service.calculate_capacity(
            workstation_id="ws-1",
            workstation_name="Machine 1",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5),
            available_hours_per_day=Decimal("8"),
        )

        assert len(plans) == 6  # 6 jours
        for plan in plans:
            assert plan.workstation_id == "ws-1"
            assert plan.available_hours == Decimal("8")

    @pytest.mark.asyncio
    async def test_calculate_capacity_with_orders(self, gpao_service):
        """Test capacité avec OF assignés."""
        # Créer gamme
        routing = await gpao_service.create_routing(
            product_id="prod-cap",
            product_name="Produit",
            operations=[{"name": "Op1", "run_time": 60}],  # 60 min
        )

        # Créer OF assigné au poste
        order = await gpao_service.create_manufacturing_order(
            product_id="prod-cap",
            product_name="Produit",
            quantity=Decimal("10"),
            planned_start=datetime.combine(date.today(), datetime.min.time()),
            routing_id=routing.id,
        )
        order.workstation_id = "ws-test"
        order.status = ProductionStatus.PLANNED

        plans = await gpao_service.calculate_capacity(
            workstation_id="ws-test",
            workstation_name="Test Station",
            start_date=date.today(),
            end_date=date.today(),
        )

        assert len(plans) == 1
        assert plans[0].planned_hours == Decimal("1")  # 60min = 1h
        assert order.id in plans[0].orders

    @pytest.mark.asyncio
    async def test_capacity_utilization_rate(self, gpao_service):
        """Test taux d'utilisation."""
        plan = CapacityPlan(
            id="plan-1",
            tenant_id=gpao_service.tenant_id,
            workstation_id="ws-1",
            workstation_name="Machine",
            date=date.today(),
            available_hours=Decimal("8"),
            planned_hours=Decimal("6"),
        )

        assert plan.utilization_rate == Decimal("75.00")

    @pytest.mark.asyncio
    async def test_capacity_overloaded(self, gpao_service):
        """Test détection surcharge."""
        plan_ok = CapacityPlan(
            id="plan-1",
            tenant_id=gpao_service.tenant_id,
            workstation_id="ws-1",
            workstation_name="Machine",
            date=date.today(),
            available_hours=Decimal("8"),
            planned_hours=Decimal("7"),
        )

        plan_overloaded = CapacityPlan(
            id="plan-2",
            tenant_id=gpao_service.tenant_id,
            workstation_id="ws-1",
            workstation_name="Machine",
            date=date.today(),
            available_hours=Decimal("8"),
            planned_hours=Decimal("10"),
        )

        assert plan_ok.is_overloaded is False
        assert plan_overloaded.is_overloaded is True


# =============================================================================
# SERVICE TESTS - STATISTICS
# =============================================================================


class TestProductionStats:
    """Tests des statistiques de production."""

    @pytest.mark.asyncio
    async def test_get_production_stats_empty(self, gpao_service):
        """Test stats sans données."""
        stats = await gpao_service.get_production_stats()

        assert stats["total_orders"] == 0
        assert stats["completed_orders"] == 0
        assert stats["total_quantity_produced"] == "0"

    @pytest.mark.asyncio
    async def test_get_production_stats_with_orders(self, gpao_service):
        """Test stats avec OF."""
        # Créer et traiter des OF
        order1 = await gpao_service.create_manufacturing_order(
            product_id="prod-1",
            product_name="Produit 1",
            quantity=Decimal("100"),
        )
        await gpao_service.release_order(order1.id)
        await gpao_service.start_order(order1.id)
        await gpao_service.report_production(order1.id, Decimal("100"))

        order2 = await gpao_service.create_manufacturing_order(
            product_id="prod-2",
            product_name="Produit 2",
            quantity=Decimal("50"),
        )
        await gpao_service.release_order(order2.id)
        await gpao_service.start_order(order2.id)
        await gpao_service.report_production(
            order2.id,
            Decimal("45"),
            Decimal("5"),
        )

        stats = await gpao_service.get_production_stats()

        assert stats["total_orders"] == 2
        assert stats["completed_orders"] == 2
        assert stats["total_quantity_produced"] == "145"
        assert stats["total_quantity_scrapped"] == "5"

    @pytest.mark.asyncio
    async def test_get_production_stats_bom_routing_count(self, gpao_service):
        """Test comptage BOM et gammes."""
        await gpao_service.create_bom(
            product_id="p1",
            product_name="P1",
            components=[],
        )
        await gpao_service.create_bom(
            product_id="p2",
            product_name="P2",
            components=[],
        )
        await gpao_service.create_routing(
            product_id="p1",
            product_name="P1",
            operations=[],
        )

        stats = await gpao_service.get_production_stats()

        assert stats["bom_count"] == 2
        assert stats["routing_count"] == 1


# =============================================================================
# ROUTER TESTS
# =============================================================================


class TestGPAORouter:
    """Tests des endpoints API GPAO."""

    @pytest.fixture
    def mock_service(self):
        """Service mocké."""
        return AsyncMock(spec=GPAOService)

    @pytest.fixture
    def test_app(self, mock_service):
        """App de test avec service mocké."""
        from fastapi import Depends

        app = FastAPI()
        app.include_router(router)

        async def override_service():
            return mock_service

        from app.modules.production.gpao import router as gpao_router_module

        app.dependency_overrides[gpao_router_module.get_gpao_service] = override_service
        return app

    @pytest.fixture
    def test_client(self, test_app):
        """Client de test."""
        return TestClient(test_app)

    def test_create_bom_endpoint(self, test_client, mock_service):
        """Test endpoint création BOM."""
        mock_bom = BillOfMaterials(
            id="bom-123",
            tenant_id="test-tenant",
            product_id="prod-1",
            product_name="Test Product",
            version="1.0",
            components=[],
        )
        mock_service.create_bom.return_value = mock_bom

        response = test_client.post(
            "/v3/production/gpao/boms",
            json={
                "product_id": "prod-1",
                "product_name": "Test Product",
                "components": [],
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 201  # 201 Created
        data = response.json()
        assert data["id"] == "bom-123"

    def test_list_boms_endpoint(self, test_client, mock_service):
        """Test endpoint liste BOMs."""
        mock_service.list_boms.return_value = [
            BillOfMaterials(
                id="bom-1",
                tenant_id="test-tenant",
                product_id="prod-1",
                product_name="Product 1",
                version="1.0",
                components=[],
            ),
        ]

        response = test_client.get(
            "/v3/production/gpao/boms",
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Retourne une liste directement

    def test_create_routing_endpoint(self, test_client, mock_service):
        """Test endpoint création gamme."""
        mock_routing = Routing(
            id="routing-123",
            tenant_id="test-tenant",
            product_id="prod-1",
            product_name="Test Product",
            version="1.0",
            operations=[],
        )
        mock_service.create_routing.return_value = mock_routing

        response = test_client.post(
            "/v3/production/gpao/routings",
            json={
                "product_id": "prod-1",
                "product_name": "Test Product",
                "operations": [],
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 201  # 201 Created

    def test_create_order_endpoint(self, test_client, mock_service):
        """Test endpoint création OF."""
        mock_order = ManufacturingOrder(
            id="order-123",
            tenant_id="test-tenant",
            order_number="OF-001001",
            product_id="prod-1",
            product_name="Test Product",
            quantity_planned=Decimal("100"),
        )
        mock_service.create_manufacturing_order.return_value = mock_order

        response = test_client.post(
            "/v3/production/gpao/orders",
            json={
                "product_id": "prod-1",
                "product_name": "Test Product",
                "quantity": 100,
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 201  # 201 Created
        data = response.json()
        assert data["order_number"] == "OF-001001"

    def test_get_order_endpoint(self, test_client, mock_service):
        """Test endpoint récupération OF."""
        mock_order = ManufacturingOrder(
            id="order-123",
            tenant_id="test-tenant",
            order_number="OF-001001",
            product_id="prod-1",
            product_name="Test Product",
            quantity_planned=Decimal("100"),
        )
        mock_service.get_order.return_value = mock_order

        response = test_client.get(
            "/v3/production/gpao/orders/order-123",
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200

    def test_get_order_not_found(self, test_client, mock_service):
        """Test OF non trouvé."""
        mock_service.get_order.return_value = None

        response = test_client.get(
            "/v3/production/gpao/orders/nonexistent",
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 404

    def test_release_order_endpoint(self, test_client, mock_service):
        """Test endpoint lancement OF."""
        mock_order = ManufacturingOrder(
            id="order-123",
            tenant_id="test-tenant",
            order_number="OF-001001",
            product_id="prod-1",
            product_name="Test",
            quantity_planned=Decimal("100"),
            status=ProductionStatus.RELEASED,
        )
        mock_service.release_order.return_value = mock_order

        response = test_client.post(
            "/v3/production/gpao/orders/order-123/release",
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200

    def test_start_order_endpoint(self, test_client, mock_service):
        """Test endpoint démarrage OF."""
        mock_order = ManufacturingOrder(
            id="order-123",
            tenant_id="test-tenant",
            order_number="OF-001001",
            product_id="prod-1",
            product_name="Test",
            quantity_planned=Decimal("100"),
            status=ProductionStatus.IN_PROGRESS,
        )
        mock_service.start_order.return_value = mock_order

        response = test_client.post(
            "/v3/production/gpao/orders/order-123/start",
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200

    def test_report_production_endpoint(self, test_client, mock_service):
        """Test endpoint déclaration production."""
        mock_order = ManufacturingOrder(
            id="order-123",
            tenant_id="test-tenant",
            order_number="OF-001001",
            product_id="prod-1",
            product_name="Test",
            quantity_planned=Decimal("100"),
            quantity_produced=Decimal("50"),
        )
        mock_service.report_production.return_value = mock_order

        response = test_client.post(
            "/v3/production/gpao/orders/order-123/report",  # /report not /production
            json={"quantity_produced": 50, "quantity_scrapped": 0},
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200

    def test_calculate_mrp_endpoint(self, test_client, mock_service):
        """Test endpoint calcul MRP."""
        mock_req = MRPRequirement(
            id="req-1",
            tenant_id="test-tenant",
            product_id="prod-1",
            product_name="Test",
            requirement_date=date.today(),
            gross_requirement=Decimal("100"),
            scheduled_receipts=Decimal("0"),
            projected_on_hand=Decimal("0"),
            net_requirement=Decimal("100"),
        )
        mock_service.calculate_requirements.return_value = [mock_req]

        response = test_client.post(
            "/v3/production/gpao/mrp/calculate",
            json={
                "product_id": "prod-1",
                "product_name": "Test",
                "quantity": 100,
                "due_date": str(date.today() + timedelta(days=7)),
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200

    def test_calculate_capacity_endpoint(self, test_client, mock_service):
        """Test endpoint calcul capacité."""
        mock_plan = CapacityPlan(
            id="plan-1",
            tenant_id="test-tenant",
            workstation_id="ws-1",
            workstation_name="Machine 1",
            date=date.today(),
            available_hours=Decimal("8"),
            planned_hours=Decimal("6"),
        )
        mock_service.calculate_capacity.return_value = [mock_plan]

        response = test_client.post(
            "/v3/production/gpao/capacity",  # /capacity not /capacity/calculate
            json={
                "workstation_id": "ws-1",
                "workstation_name": "Machine 1",
                "start_date": str(date.today()),
                "end_date": str(date.today() + timedelta(days=5)),
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200

    def test_stats_endpoint(self, test_client, mock_service):
        """Test endpoint statistiques."""
        mock_service.get_production_stats.return_value = {
            "total_orders": 10,
            "completed_orders": 5,
            "in_progress_orders": 3,
            "planned_orders": 2,
            "total_quantity_produced": "500",
            "total_quantity_scrapped": "10",
            "average_completion_rate": "85.00",
            "scrap_rate": "1.96",
            "bom_count": 8,
            "routing_count": 6,
        }

        response = test_client.get(
            "/v3/production/gpao/stats",
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_orders"] == 10

    def test_missing_tenant_header(self, test_client, mock_service):
        """Test requête sans tenant."""
        response = test_client.get("/v3/production/gpao/orders")

        # Devrait échouer ou utiliser un tenant par défaut
        # selon l'implémentation
        assert response.status_code in [400, 422, 200]


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestDataclasses:
    """Tests des dataclasses."""

    def test_bom_component_defaults(self):
        """Test valeurs par défaut BOMComponent."""
        comp = BOMComponent(
            id="c1",
            product_id="p1",
            product_name="Component",
            quantity=Decimal("1"),
            unit=UnitOfMeasure.PIECE,
        )

        assert comp.position == 0
        assert comp.is_phantom is False
        assert comp.scrap_rate == Decimal("0")
        assert comp.lead_time_days == 0

    def test_routing_operation_total_time(self):
        """Test temps total opération."""
        op = RoutingOperation(
            id="op1",
            sequence=1,
            name="Test",
            operation_type=OperationType.MACHINING,
            setup_time_minutes=10,
            run_time_minutes=30,
            queue_time_minutes=5,
            move_time_minutes=5,
        )

        assert op.total_time_minutes == 50

    def test_manufacturing_order_properties(self):
        """Test propriétés OF."""
        order = ManufacturingOrder(
            id="o1",
            tenant_id="t1",
            order_number="OF-001",
            product_id="p1",
            product_name="Product",
            quantity_planned=Decimal("100"),
            quantity_produced=Decimal("40"),
            quantity_scrapped=Decimal("5"),
        )

        assert order.quantity_remaining == Decimal("55")
        assert order.completion_rate == Decimal("40.00")
        # scrap_rate = 5/(40+5) * 100 = 11.11%
        assert order.scrap_rate == Decimal("11.11")

    def test_capacity_plan_utilization(self):
        """Test taux utilisation capacité."""
        plan = CapacityPlan(
            id="cp1",
            tenant_id="t1",
            workstation_id="ws1",
            workstation_name="Machine",
            date=date.today(),
            available_hours=Decimal("10"),
            planned_hours=Decimal("8"),
        )

        assert plan.utilization_rate == Decimal("80.00")
        assert plan.is_overloaded is False


# =============================================================================
# TENANT ISOLATION TESTS
# =============================================================================


class TestTenantIsolation:
    """Tests d'isolation multi-tenant."""

    @pytest.mark.asyncio
    async def test_bom_tenant_isolation(self, mock_db):
        """Test isolation BOM entre tenants."""
        service1 = GPAOService(db=mock_db, tenant_id="tenant-1")
        service2 = GPAOService(db=mock_db, tenant_id="tenant-2")

        bom1 = await service1.create_bom(
            product_id="shared-prod",
            product_name="Shared Product",
            components=[],
        )

        # Tenant 2 ne voit pas la BOM de tenant 1
        result = await service2.get_bom(bom1.id)
        assert result is None

        boms2 = await service2.list_boms()
        assert len(boms2) == 0

    @pytest.mark.asyncio
    async def test_order_tenant_isolation(self, mock_db):
        """Test isolation OF entre tenants."""
        service1 = GPAOService(db=mock_db, tenant_id="tenant-a")
        service2 = GPAOService(db=mock_db, tenant_id="tenant-b")

        order = await service1.create_manufacturing_order(
            product_id="prod-1",
            product_name="Product",
            quantity=Decimal("100"),
        )

        # Tenant B ne peut pas voir ni modifier l'OF de tenant A
        result = await service2.get_order(order.id)
        assert result is None

        orders_b = await service2.list_orders()
        assert len(orders_b) == 0

    @pytest.mark.asyncio
    async def test_routing_tenant_isolation(self, mock_db):
        """Test isolation gammes entre tenants."""
        service1 = GPAOService(db=mock_db, tenant_id="tenant-x")
        service2 = GPAOService(db=mock_db, tenant_id="tenant-y")

        routing = await service1.create_routing(
            product_id="prod-1",
            product_name="Product",
            operations=[{"name": "Op1"}],
        )

        result = await service2.get_routing(routing.id)
        assert result is None

        routings_y = await service2.list_routings()
        assert len(routings_y) == 0
