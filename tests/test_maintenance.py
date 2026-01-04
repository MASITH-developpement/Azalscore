"""
AZALS MODULE M8 - Tests Maintenance (GMAO)
==========================================

Tests unitaires pour la gestion de maintenance.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

# Import des modèles
from app.modules.maintenance.models import (
    Equipment, EquipmentCategory, Location,
    MaintenancePlan, MaintenanceTask,
    WorkOrder, WorkOrderLabor, WorkOrderPart,
    FailureReport, SparePart, SparePartStock,
    MeterReading, MaintenanceLog,
    EquipmentStatus, CriticalityLevel, MaintenanceType,
    FrequencyUnit, WorkOrderStatus, WorkOrderPriority,
    FailureSeverity, FailureType
)

# Import des schémas
from app.modules.maintenance.schemas import (
    EquipmentCreate, EquipmentUpdate, EquipmentCategoryCreate,
    MaintenancePlanCreate, MaintenanceTaskCreate,
    WorkOrderCreate, WorkOrderUpdate, WorkOrderLaborCreate, WorkOrderPartCreate,
    FailureReportCreate, SparePartCreate, SparePartStockUpdate,
    MeterReadingCreate, MaintenanceLogCreate,
    MaintenanceDashboard, EquipmentKPIs
)

# Import du service
from app.modules.maintenance.service import MaintenanceService, get_maintenance_service


# =============================================================================
# TESTS DES ENUMS
# =============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_equipment_status_values(self):
        """Tester les statuts d'équipement."""
        assert EquipmentStatus.OPERATIONAL.value == "OPERATIONAL"
        assert EquipmentStatus.MAINTENANCE.value == "MAINTENANCE"
        assert EquipmentStatus.BREAKDOWN.value == "BREAKDOWN"
        assert EquipmentStatus.DECOMMISSIONED.value == "DECOMMISSIONED"
        assert len(EquipmentStatus) >= 4

    def test_criticality_level_values(self):
        """Tester les niveaux de criticité."""
        assert CriticalityLevel.LOW.value == "LOW"
        assert CriticalityLevel.MEDIUM.value == "MEDIUM"
        assert CriticalityLevel.HIGH.value == "HIGH"
        assert CriticalityLevel.CRITICAL.value == "CRITICAL"
        assert len(CriticalityLevel) == 4

    def test_maintenance_type_values(self):
        """Tester les types de maintenance."""
        assert MaintenanceType.PREVENTIVE.value == "PREVENTIVE"
        assert MaintenanceType.CORRECTIVE.value == "CORRECTIVE"
        assert MaintenanceType.PREDICTIVE.value == "PREDICTIVE"
        assert MaintenanceType.CONDITION_BASED.value == "CONDITION_BASED"
        assert len(MaintenanceType) >= 4

    def test_work_order_status_values(self):
        """Tester les statuts d'ordre de travail."""
        assert WorkOrderStatus.DRAFT.value == "DRAFT"
        assert WorkOrderStatus.PLANNED.value == "PLANNED"
        assert WorkOrderStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert WorkOrderStatus.COMPLETED.value == "COMPLETED"
        assert len(WorkOrderStatus) >= 4

    def test_work_order_priority_values(self):
        """Tester les priorités."""
        assert WorkOrderPriority.LOW.value == "LOW"
        assert WorkOrderPriority.NORMAL.value == "NORMAL"
        assert WorkOrderPriority.HIGH.value == "HIGH"
        assert WorkOrderPriority.EMERGENCY.value == "EMERGENCY"
        assert len(WorkOrderPriority) == 4

    def test_failure_severity_values(self):
        """Tester les niveaux de sévérité de panne."""
        assert FailureSeverity.MINOR.value == "MINOR"
        assert FailureSeverity.MAJOR.value == "MAJOR"
        assert FailureSeverity.CRITICAL.value == "CRITICAL"
        assert len(FailureSeverity) >= 3


# =============================================================================
# TESTS DES MODÈLES
# =============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_equipment_model(self):
        """Tester le modèle Equipment."""
        equipment = Equipment(
            tenant_id="test-tenant",
            code="EQ001",
            name="Compresseur",
            status=EquipmentStatus.OPERATIONAL,
            criticality=CriticalityLevel.HIGH
        )
        assert equipment.code == "EQ001"
        assert equipment.status == EquipmentStatus.OPERATIONAL
        assert equipment.criticality == CriticalityLevel.HIGH

    def test_maintenance_plan_model(self):
        """Tester le modèle MaintenancePlan."""
        plan = MaintenancePlan(
            tenant_id="test-tenant",
            code="MP001",
            name="Plan préventif mensuel",
            type=MaintenanceType.PREVENTIVE,
            frequency_value=1,
            frequency_unit=FrequencyUnit.MONTH
        )
        assert plan.code == "MP001"
        assert plan.type == MaintenanceType.PREVENTIVE

    def test_work_order_model(self):
        """Tester le modèle WorkOrder."""
        wo = WorkOrder(
            tenant_id="test-tenant",
            number="WO-2026-001",
            equipment_id=uuid4(),
            type=MaintenanceType.CORRECTIVE,
            priority=WorkOrderPriority.HIGH
        )
        assert wo.number == "WO-2026-001"
        assert wo.type == MaintenanceType.CORRECTIVE
        assert wo.status == WorkOrderStatus.DRAFT

    def test_failure_report_model(self):
        """Tester le modèle FailureReport."""
        failure = FailureReport(
            tenant_id="test-tenant",
            number="FR-2026-001",
            equipment_id=uuid4(),
            severity=FailureSeverity.MAJOR,
            description="Fuite d'huile"
        )
        assert failure.number == "FR-2026-001"
        assert failure.severity == FailureSeverity.MAJOR

    def test_spare_part_model(self):
        """Tester le modèle SparePart."""
        part = SparePart(
            tenant_id="test-tenant",
            code="SP001",
            name="Filtre à huile",
            min_stock=Decimal("5"),
            unit_cost=Decimal("25")
        )
        assert part.code == "SP001"
        assert part.min_stock == Decimal("5")


# =============================================================================
# TESTS DES SCHÉMAS
# =============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_equipment_create_schema(self):
        """Tester le schéma EquipmentCreate."""
        data = EquipmentCreate(
            code="EQ001",
            name="Machine CNC",
            criticality=CriticalityLevel.HIGH,
            purchase_date=date(2020, 1, 1),
            purchase_cost=Decimal("50000")
        )
        assert data.code == "EQ001"
        assert data.criticality == CriticalityLevel.HIGH

    def test_work_order_create_schema(self):
        """Tester le schéma WorkOrderCreate."""
        data = WorkOrderCreate(
            equipment_id=uuid4(),
            type=MaintenanceType.PREVENTIVE,
            priority=WorkOrderPriority.NORMAL,
            description="Maintenance mensuelle",
            planned_start=datetime.utcnow()
        )
        assert data.type == MaintenanceType.PREVENTIVE

    def test_failure_report_create_schema(self):
        """Tester le schéma FailureReportCreate."""
        data = FailureReportCreate(
            equipment_id=uuid4(),
            severity=FailureSeverity.CRITICAL,
            description="Arrêt complet machine",
            failure_type=FailureType.MECHANICAL
        )
        assert data.severity == FailureSeverity.CRITICAL


# =============================================================================
# TESTS DU SERVICE - ÉQUIPEMENTS
# =============================================================================

class TestMaintenanceServiceEquipment:
    """Tests du service Maintenance - Équipements."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return MaintenanceService(mock_db, "test-tenant")

    def test_create_equipment(self, service, mock_db):
        """Tester la création d'un équipement."""
        data = EquipmentCreate(
            code="EQ001",
            name="Compresseur",
            criticality=CriticalityLevel.HIGH
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_equipment(data, uuid4())

        mock_db.add.assert_called_once()
        assert result.code == "EQ001"

    def test_set_equipment_status(self, service, mock_db):
        """Tester le changement de statut."""
        eq_id = uuid4()
        mock_eq = MagicMock()
        mock_eq.status = EquipmentStatus.OPERATIONAL

        mock_db.query.return_value.filter.return_value.first.return_value = mock_eq

        result = service.set_equipment_status(eq_id, EquipmentStatus.MAINTENANCE)

        assert mock_eq.status == EquipmentStatus.MAINTENANCE


# =============================================================================
# TESTS DU SERVICE - ORDRES DE TRAVAIL
# =============================================================================

class TestMaintenanceServiceWorkOrders:
    """Tests du service Maintenance - Ordres de travail."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return MaintenanceService(mock_db, "test-tenant")

    def test_create_work_order(self, service, mock_db):
        """Tester la création d'un ordre de travail."""
        data = WorkOrderCreate(
            equipment_id=uuid4(),
            type=MaintenanceType.CORRECTIVE,
            priority=WorkOrderPriority.HIGH,
            description="Réparation urgente"
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.create_work_order(data, uuid4())

        mock_db.add.assert_called()

    def test_plan_work_order(self, service, mock_db):
        """Tester la planification."""
        wo_id = uuid4()
        mock_wo = MagicMock()
        mock_wo.status = WorkOrderStatus.DRAFT

        mock_db.query.return_value.filter.return_value.first.return_value = mock_wo

        result = service.plan_work_order(wo_id, datetime.utcnow())

        assert mock_wo.status == WorkOrderStatus.PLANNED

    def test_start_work_order(self, service, mock_db):
        """Tester le démarrage."""
        wo_id = uuid4()
        mock_wo = MagicMock()
        mock_wo.status = WorkOrderStatus.PLANNED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_wo

        result = service.start_work_order(wo_id, uuid4())

        assert mock_wo.status == WorkOrderStatus.IN_PROGRESS

    def test_complete_work_order(self, service, mock_db):
        """Tester la clôture."""
        wo_id = uuid4()
        mock_wo = MagicMock()
        mock_wo.status = WorkOrderStatus.IN_PROGRESS

        mock_db.query.return_value.filter.return_value.first.return_value = mock_wo

        result = service.complete_work_order(wo_id, uuid4())

        assert mock_wo.status == WorkOrderStatus.COMPLETED


# =============================================================================
# TESTS DU SERVICE - PANNES
# =============================================================================

class TestMaintenanceServiceFailures:
    """Tests du service Maintenance - Pannes."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return MaintenanceService(mock_db, "test-tenant")

    def test_report_failure(self, service, mock_db):
        """Tester le signalement d'une panne."""
        data = FailureReportCreate(
            equipment_id=uuid4(),
            severity=FailureSeverity.MAJOR,
            description="Moteur grillé"
        )

        mock_eq = MagicMock()
        mock_eq.status = EquipmentStatus.OPERATIONAL
        mock_db.query.return_value.filter.return_value.first.return_value = mock_eq
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.report_failure(data, uuid4())

        mock_db.add.assert_called()


# =============================================================================
# TESTS DU SERVICE - PLANS DE MAINTENANCE
# =============================================================================

class TestMaintenanceServicePlans:
    """Tests du service Maintenance - Plans."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return MaintenanceService(mock_db, "test-tenant")

    def test_create_maintenance_plan(self, service, mock_db):
        """Tester la création d'un plan."""
        data = MaintenancePlanCreate(
            code="MP001",
            name="Plan préventif mensuel",
            type=MaintenanceType.PREVENTIVE,
            frequency_value=1,
            frequency_unit=FrequencyUnit.MONTH
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_maintenance_plan(data, uuid4())

        mock_db.add.assert_called()


# =============================================================================
# TESTS FACTORY
# =============================================================================

class TestFactory:
    """Tests de la factory."""

    def test_get_maintenance_service(self):
        """Tester la factory."""
        mock_db = MagicMock()
        service = get_maintenance_service(mock_db, "test-tenant")

        assert isinstance(service, MaintenanceService)
        assert service.tenant_id == "test-tenant"


# =============================================================================
# TESTS CALCULS MAINTENANCE
# =============================================================================

class TestMaintenanceCalculations:
    """Tests des calculs de maintenance."""

    def test_mtbf_calculation(self):
        """Tester le calcul du MTBF (Mean Time Between Failures)."""
        total_uptime_hours = Decimal("1000")
        number_of_failures = 5

        mtbf = total_uptime_hours / number_of_failures

        assert mtbf == Decimal("200")

    def test_mttr_calculation(self):
        """Tester le calcul du MTTR (Mean Time To Repair)."""
        total_repair_hours = Decimal("50")
        number_of_repairs = 5

        mttr = total_repair_hours / number_of_repairs

        assert mttr == Decimal("10")

    def test_availability_calculation(self):
        """Tester le calcul de la disponibilité."""
        mtbf = Decimal("200")
        mttr = Decimal("10")

        availability = mtbf / (mtbf + mttr) * 100

        # 200 / 210 * 100 = 95.238...
        assert availability > Decimal("95")

    def test_maintenance_cost(self):
        """Tester le calcul du coût de maintenance."""
        labor_hours = Decimal("5")
        labor_rate = Decimal("50")
        parts_cost = Decimal("200")

        labor_cost = labor_hours * labor_rate
        total_cost = labor_cost + parts_cost

        assert labor_cost == Decimal("250")
        assert total_cost == Decimal("450")


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
