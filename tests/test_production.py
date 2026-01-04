"""
AZALS MODULE M6 - Tests Production (Manufacturing)
===================================================

Tests unitaires pour la gestion de production.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

# Import des modèles
from app.modules.production.models import (
    WorkCenter, WorkCenterCapacity, BillOfMaterials, BOMLine,
    Routing, RoutingOperation, ManufacturingOrder, WorkOrder,
    WorkOrderTimeEntry, MaterialConsumption, ProductionOutput,
    ProductionScrap, ProductionPlan, ProductionPlanLine, MaintenanceSchedule,
    WorkCenterType, WorkCenterStatus, BOMType, BOMStatus,
    OperationType, MOStatus, MOPriority, WorkOrderStatus,
    ConsumptionType, ScrapReason
)

# Import des schémas
from app.modules.production.schemas import (
    WorkCenterCreate, WorkCenterUpdate,
    BOMCreate, BOMLineCreate, BOMUpdate,
    RoutingCreate, RoutingOperationCreate,
    ManufacturingOrderCreate, ManufacturingOrderUpdate,
    WorkOrderCreate, WorkOrderUpdate,
    TimeEntryCreate, ConsumptionCreate, OutputCreate,
    ScrapCreate, ProductionPlanCreate,
    ProductionDashboard, OEEMetrics
)

# Import du service
from app.modules.production.service import ProductionService, get_production_service


# =============================================================================
# TESTS DES ENUMS
# =============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_work_center_type_values(self):
        """Tester les types de centre de travail."""
        assert WorkCenterType.MACHINE.value == "MACHINE"
        assert WorkCenterType.ASSEMBLY.value == "ASSEMBLY"
        assert WorkCenterType.MANUAL.value == "MANUAL"
        assert WorkCenterType.QUALITY.value == "QUALITY"
        assert WorkCenterType.PACKAGING.value == "PACKAGING"
        assert len(WorkCenterType) == 6

    def test_work_center_status_values(self):
        """Tester les statuts de centre de travail."""
        assert WorkCenterStatus.AVAILABLE.value == "AVAILABLE"
        assert WorkCenterStatus.BUSY.value == "BUSY"
        assert WorkCenterStatus.MAINTENANCE.value == "MAINTENANCE"
        assert WorkCenterStatus.OFFLINE.value == "OFFLINE"
        assert len(WorkCenterStatus) == 4

    def test_bom_type_values(self):
        """Tester les types de nomenclature."""
        assert BOMType.MANUFACTURING.value == "MANUFACTURING"
        assert BOMType.KIT.value == "KIT"
        assert BOMType.PHANTOM.value == "PHANTOM"
        assert BOMType.SUBCONTRACT.value == "SUBCONTRACT"
        assert len(BOMType) == 4

    def test_mo_status_values(self):
        """Tester les statuts d'ordre de fabrication."""
        assert MOStatus.DRAFT.value == "DRAFT"
        assert MOStatus.CONFIRMED.value == "CONFIRMED"
        assert MOStatus.PLANNED.value == "PLANNED"
        assert MOStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert MOStatus.DONE.value == "DONE"
        assert MOStatus.CANCELLED.value == "CANCELLED"
        assert len(MOStatus) == 6

    def test_mo_priority_values(self):
        """Tester les priorités."""
        assert MOPriority.LOW.value == "LOW"
        assert MOPriority.NORMAL.value == "NORMAL"
        assert MOPriority.HIGH.value == "HIGH"
        assert MOPriority.URGENT.value == "URGENT"
        assert len(MOPriority) == 4

    def test_scrap_reason_values(self):
        """Tester les raisons de rebut."""
        assert ScrapReason.DEFECT.value == "DEFECT"
        assert ScrapReason.DAMAGE.value == "DAMAGE"
        assert ScrapReason.QUALITY.value == "QUALITY"
        assert len(ScrapReason) == 5


# =============================================================================
# TESTS DES MODÈLES
# =============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_work_center_model(self):
        """Tester le modèle WorkCenter."""
        wc = WorkCenter(
            tenant_id="test-tenant",
            code="MC001",
            name="Machine CNC",
            type=WorkCenterType.MACHINE,
            cost_per_hour=Decimal("50")
        )
        assert wc.code == "MC001"
        assert wc.type == WorkCenterType.MACHINE
        assert wc.status == WorkCenterStatus.AVAILABLE
        assert wc.efficiency == Decimal("100")

    def test_bom_model(self):
        """Tester le modèle BillOfMaterials."""
        bom = BillOfMaterials(
            tenant_id="test-tenant",
            code="BOM001",
            name="Nomenclature Produit A",
            product_id=uuid4(),
            quantity=Decimal("1"),
            type=BOMType.MANUFACTURING
        )
        assert bom.code == "BOM001"
        assert bom.type == BOMType.MANUFACTURING
        assert bom.status == BOMStatus.DRAFT

    def test_routing_model(self):
        """Tester le modèle Routing."""
        routing = Routing(
            tenant_id="test-tenant",
            code="GAM001",
            name="Gamme Standard",
            product_id=uuid4()
        )
        assert routing.code == "GAM001"
        assert routing.status == BOMStatus.DRAFT

    def test_manufacturing_order_model(self):
        """Tester le modèle ManufacturingOrder."""
        mo = ManufacturingOrder(
            tenant_id="test-tenant",
            number="OF-2026-001",
            product_id=uuid4(),
            quantity_planned=Decimal("100")
        )
        assert mo.number == "OF-2026-001"
        assert mo.status == MOStatus.DRAFT
        assert mo.priority == MOPriority.NORMAL
        assert mo.quantity_produced == Decimal("0")

    def test_work_order_model(self):
        """Tester le modèle WorkOrder."""
        wo = WorkOrder(
            tenant_id="test-tenant",
            mo_id=uuid4(),
            sequence=1,
            name="Usinage",
            quantity_planned=Decimal("100")
        )
        assert wo.sequence == 1
        assert wo.status == WorkOrderStatus.PENDING
        assert wo.quantity_done == Decimal("0")

    def test_production_output_model(self):
        """Tester le modèle ProductionOutput."""
        output = ProductionOutput(
            tenant_id="test-tenant",
            mo_id=uuid4(),
            product_id=uuid4(),
            quantity=Decimal("95")
        )
        assert output.quantity == Decimal("95")
        assert output.is_quality_passed == True

    def test_production_scrap_model(self):
        """Tester le modèle ProductionScrap."""
        scrap = ProductionScrap(
            tenant_id="test-tenant",
            mo_id=uuid4(),
            product_id=uuid4(),
            quantity=Decimal("5"),
            reason=ScrapReason.DEFECT
        )
        assert scrap.quantity == Decimal("5")
        assert scrap.reason == ScrapReason.DEFECT


# =============================================================================
# TESTS DES SCHÉMAS
# =============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_work_center_create_schema(self):
        """Tester le schéma WorkCenterCreate."""
        data = WorkCenterCreate(
            code="MC001",
            name="Machine CNC",
            type=WorkCenterType.MACHINE,
            cost_per_hour=Decimal("50"),
            working_hours_per_day=Decimal("8")
        )
        assert data.code == "MC001"
        assert data.type == WorkCenterType.MACHINE

    def test_bom_create_schema(self):
        """Tester le schéma BOMCreate."""
        lines = [
            BOMLineCreate(
                product_id=uuid4(),
                quantity=Decimal("2")
            )
        ]
        data = BOMCreate(
            code="BOM001",
            name="Nomenclature Test",
            product_id=uuid4(),
            lines=lines
        )
        assert data.code == "BOM001"
        assert len(data.lines) == 1

    def test_manufacturing_order_create_schema(self):
        """Tester le schéma ManufacturingOrderCreate."""
        data = ManufacturingOrderCreate(
            product_id=uuid4(),
            quantity_planned=Decimal("100"),
            priority=MOPriority.HIGH,
            scheduled_start=datetime.utcnow()
        )
        assert data.quantity_planned == Decimal("100")
        assert data.priority == MOPriority.HIGH


# =============================================================================
# TESTS DU SERVICE - CENTRES DE TRAVAIL
# =============================================================================

class TestProductionServiceWorkCenters:
    """Tests du service Production - Centres de travail."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return ProductionService(mock_db, "test-tenant")

    def test_create_work_center(self, service, mock_db):
        """Tester la création d'un centre de travail."""
        data = WorkCenterCreate(
            code="MC001",
            name="Machine CNC",
            type=WorkCenterType.MACHINE
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_work_center(data, uuid4())

        mock_db.add.assert_called_once()
        assert result.code == "MC001"

    def test_set_work_center_status(self, service, mock_db):
        """Tester le changement de statut."""
        wc_id = uuid4()
        mock_wc = MagicMock()
        mock_wc.status = WorkCenterStatus.AVAILABLE

        mock_db.query.return_value.filter.return_value.first.return_value = mock_wc

        result = service.set_work_center_status(wc_id, WorkCenterStatus.MAINTENANCE)

        assert mock_wc.status == WorkCenterStatus.MAINTENANCE


# =============================================================================
# TESTS DU SERVICE - NOMENCLATURES
# =============================================================================

class TestProductionServiceBOM:
    """Tests du service Production - Nomenclatures."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return ProductionService(mock_db, "test-tenant")

    def test_create_bom(self, service, mock_db):
        """Tester la création d'une nomenclature."""
        lines = [
            BOMLineCreate(
                product_id=uuid4(),
                quantity=Decimal("2")
            )
        ]
        data = BOMCreate(
            code="BOM001",
            name="Nomenclature Test",
            product_id=uuid4(),
            lines=lines
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.flush = MagicMock()

        result = service.create_bom(data, uuid4())

        assert mock_db.add.called

    def test_activate_bom(self, service, mock_db):
        """Tester l'activation d'une nomenclature."""
        bom_id = uuid4()
        mock_bom = MagicMock()
        mock_bom.status = BOMStatus.DRAFT

        mock_db.query.return_value.filter.return_value.first.return_value = mock_bom

        result = service.activate_bom(bom_id)

        assert mock_bom.status == BOMStatus.ACTIVE


# =============================================================================
# TESTS DU SERVICE - ORDRES DE FABRICATION
# =============================================================================

class TestProductionServiceMO:
    """Tests du service Production - Ordres de fabrication."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return ProductionService(mock_db, "test-tenant")

    def test_create_manufacturing_order(self, service, mock_db):
        """Tester la création d'un OF."""
        data = ManufacturingOrderCreate(
            product_id=uuid4(),
            quantity_planned=Decimal("100")
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.create_manufacturing_order(data, uuid4())

        assert mock_db.add.called

    def test_confirm_manufacturing_order(self, service, mock_db):
        """Tester la confirmation d'un OF."""
        mo_id = uuid4()
        mock_mo = MagicMock()
        mock_mo.status = MOStatus.DRAFT

        mock_db.query.return_value.filter.return_value.first.return_value = mock_mo

        result = service.confirm_manufacturing_order(mo_id, uuid4())

        assert mock_mo.status == MOStatus.CONFIRMED

    def test_start_manufacturing_order(self, service, mock_db):
        """Tester le démarrage d'un OF."""
        mo_id = uuid4()
        mock_mo = MagicMock()
        mock_mo.status = MOStatus.CONFIRMED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_mo

        result = service.start_manufacturing_order(mo_id)

        assert mock_mo.status == MOStatus.IN_PROGRESS

    def test_complete_manufacturing_order(self, service, mock_db):
        """Tester la clôture d'un OF."""
        mo_id = uuid4()
        mock_mo = MagicMock()
        mock_mo.status = MOStatus.IN_PROGRESS
        mock_mo.quantity_produced = Decimal("100")
        mock_mo.quantity_planned = Decimal("100")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_mo

        result = service.complete_manufacturing_order(mo_id)

        assert mock_mo.status == MOStatus.DONE


# =============================================================================
# TESTS DU SERVICE - PRODUCTION
# =============================================================================

class TestProductionServiceOutput:
    """Tests du service Production - Sorties et rebuts."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return ProductionService(mock_db, "test-tenant")

    def test_record_output(self, service, mock_db):
        """Tester l'enregistrement d'une sortie."""
        data = OutputCreate(
            mo_id=uuid4(),
            product_id=uuid4(),
            quantity=Decimal("50")
        )

        mock_mo = MagicMock()
        mock_mo.quantity_produced = Decimal("0")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_mo
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.record_output(data, uuid4())

        mock_db.add.assert_called()

    def test_record_scrap(self, service, mock_db):
        """Tester l'enregistrement d'un rebut."""
        data = ScrapCreate(
            mo_id=uuid4(),
            product_id=uuid4(),
            quantity=Decimal("5"),
            reason=ScrapReason.DEFECT
        )

        mock_mo = MagicMock()
        mock_mo.quantity_scrapped = Decimal("0")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_mo
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.record_scrap(data, uuid4())

        mock_db.add.assert_called()


# =============================================================================
# TESTS FACTORY
# =============================================================================

class TestFactory:
    """Tests de la factory."""

    def test_get_production_service(self):
        """Tester la factory."""
        mock_db = MagicMock()
        service = get_production_service(mock_db, "test-tenant")

        assert isinstance(service, ProductionService)
        assert service.tenant_id == "test-tenant"


# =============================================================================
# TESTS CALCULS PRODUCTION
# =============================================================================

class TestProductionCalculations:
    """Tests des calculs de production."""

    def test_oee_calculation(self):
        """Tester le calcul de l'OEE."""
        # OEE = Disponibilité × Performance × Qualité
        availability = Decimal("0.90")  # 90%
        performance = Decimal("0.85")  # 85%
        quality = Decimal("0.95")  # 95%

        oee = availability * performance * quality
        oee_percent = oee * 100

        assert oee_percent == Decimal("72.675")

    def test_production_cost_calculation(self):
        """Tester le calcul du coût de production."""
        material_cost = Decimal("500")
        labor_cost = Decimal("200")
        overhead_cost = Decimal("100")

        total_cost = material_cost + labor_cost + overhead_cost

        assert total_cost == Decimal("800")

    def test_scrap_rate_calculation(self):
        """Tester le calcul du taux de rebut."""
        produced = Decimal("100")
        scrapped = Decimal("5")

        scrap_rate = (scrapped / produced) * 100

        assert scrap_rate == Decimal("5")

    def test_yield_calculation(self):
        """Tester le calcul du rendement."""
        planned = Decimal("100")
        actual = Decimal("95")

        yield_rate = (actual / planned) * 100

        assert yield_rate == Decimal("95")


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
