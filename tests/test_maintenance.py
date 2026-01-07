"""
AZALS MODULE M8 - Tests Maintenance (GMAO)
==========================================

Tests unitaires pour la gestion de maintenance.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Import des modèles
from app.modules.maintenance.models import (
    Asset, AssetMeter, MeterReading,
    MaintenancePlan, MaintenancePlanTask,
    MaintenanceWorkOrder, WorkOrderTask, WorkOrderLabor, WorkOrderPart,
    Failure, SparePart, SparePartStock, PartRequest, MaintenanceContract,
    AssetCategory, AssetStatus, AssetCriticality,
    MaintenanceType, WorkOrderStatus, WorkOrderPriority,
    FailureType, PartRequestStatus, ContractType, ContractStatus
)

# Import des schémas
from app.modules.maintenance.schemas import (
    AssetCreate, AssetUpdate,
    MeterCreate, MeterReadingCreate,
    MaintenancePlanCreate, MaintenancePlanUpdate, PlanTaskCreate,
    WorkOrderCreate, WorkOrderUpdate, WorkOrderComplete,
    WorkOrderLaborCreate, WorkOrderPartCreate,
    FailureCreate, FailureUpdate,
    SparePartCreate, SparePartUpdate,
    PartRequestCreate,
    ContractCreate, ContractUpdate,
    MaintenanceDashboard,
    AssetCategoryEnum, AssetStatusEnum, AssetCriticalityEnum,
    MaintenanceTypeEnum, WorkOrderStatusEnum, WorkOrderPriorityEnum,
    FailureTypeEnum
)

# Import du service
from app.modules.maintenance.service import MaintenanceService, get_maintenance_service


# =============================================================================
# TESTS DES ENUMS
# =============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_asset_status_values(self):
        """Tester les statuts d'actif."""
        assert AssetStatus.ACTIVE.value == "ACTIVE"
        assert AssetStatus.INACTIVE.value == "INACTIVE"
        assert AssetStatus.IN_MAINTENANCE.value == "IN_MAINTENANCE"
        assert AssetStatus.UNDER_REPAIR.value == "UNDER_REPAIR"
        assert AssetStatus.DISPOSED.value == "DISPOSED"
        assert len(AssetStatus) >= 5

    def test_asset_criticality_values(self):
        """Tester les niveaux de criticité."""
        assert AssetCriticality.LOW.value == "LOW"
        assert AssetCriticality.MEDIUM.value == "MEDIUM"
        assert AssetCriticality.HIGH.value == "HIGH"
        assert AssetCriticality.CRITICAL.value == "CRITICAL"
        assert len(AssetCriticality) == 4

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
        assert WorkOrderStatus.CLOSED.value == "CLOSED"
        assert len(WorkOrderStatus) >= 5

    def test_work_order_priority_values(self):
        """Tester les priorités."""
        assert WorkOrderPriority.LOW.value == "LOW"
        assert WorkOrderPriority.MEDIUM.value == "MEDIUM"
        assert WorkOrderPriority.HIGH.value == "HIGH"
        assert WorkOrderPriority.EMERGENCY.value == "EMERGENCY"
        assert len(WorkOrderPriority) >= 4

    def test_failure_type_values(self):
        """Tester les types de panne."""
        assert FailureType.MECHANICAL.value == "MECHANICAL"
        assert FailureType.ELECTRICAL.value == "ELECTRICAL"
        assert FailureType.ELECTRONIC.value == "ELECTRONIC"
        assert len(FailureType) >= 3

    def test_asset_category_values(self):
        """Tester les catégories d'actifs."""
        assert AssetCategory.MACHINE.value == "MACHINE"
        assert AssetCategory.EQUIPMENT.value == "EQUIPMENT"
        assert AssetCategory.VEHICLE.value == "VEHICLE"
        assert len(AssetCategory) >= 3


# =============================================================================
# TESTS DES MODÈLES
# =============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_asset_model(self):
        """Tester le modèle Asset."""
        asset = Asset(
            tenant_id=1,
            asset_code="EQ001",
            name="Compresseur",
            category=AssetCategory.MACHINE,
            status=AssetStatus.ACTIVE,
            criticality=AssetCriticality.HIGH
        )
        assert asset.asset_code == "EQ001"
        assert asset.status == AssetStatus.ACTIVE
        assert asset.criticality == AssetCriticality.HIGH

    def test_maintenance_plan_model(self):
        """Tester le modèle MaintenancePlan."""
        plan = MaintenancePlan(
            tenant_id=1,
            plan_code="MP001",
            name="Plan préventif mensuel",
            maintenance_type=MaintenanceType.PREVENTIVE,
            trigger_type="TIME",
            frequency_value=1,
            frequency_unit="MONTH"
        )
        assert plan.plan_code == "MP001"
        assert plan.maintenance_type == MaintenanceType.PREVENTIVE

    def test_work_order_model(self):
        """Tester le modèle MaintenanceWorkOrder."""
        wo = MaintenanceWorkOrder(
            tenant_id=1,
            wo_number="WO-202601-001",
            title="Maintenance préventive",
            asset_id=1,
            maintenance_type=MaintenanceType.CORRECTIVE,
            priority=WorkOrderPriority.HIGH,
            status=WorkOrderStatus.DRAFT
        )
        assert wo.wo_number == "WO-202601-001"
        assert wo.maintenance_type == MaintenanceType.CORRECTIVE
        assert wo.status == WorkOrderStatus.DRAFT

    def test_failure_model(self):
        """Tester le modèle Failure."""
        failure = Failure(
            tenant_id=1,
            failure_number="FL-202601-001",
            asset_id=1,
            failure_type=FailureType.MECHANICAL,
            description="Fuite d'huile détectée",
            failure_date=datetime.utcnow()
        )
        assert failure.failure_number == "FL-202601-001"
        assert failure.failure_type == FailureType.MECHANICAL

    def test_spare_part_model(self):
        """Tester le modèle SparePart."""
        part = SparePart(
            tenant_id=1,
            part_code="SP001",
            name="Filtre à huile",
            unit="PCE",
            min_stock_level=Decimal("5"),
            unit_cost=Decimal("25")
        )
        assert part.part_code == "SP001"
        assert part.min_stock_level == Decimal("5")


# =============================================================================
# TESTS DES SCHÉMAS
# =============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_asset_create_schema(self):
        """Tester le schéma AssetCreate."""
        data = AssetCreate(
            asset_code="EQ001",
            name="Machine CNC",
            category=AssetCategoryEnum.MACHINE,
            criticality=AssetCriticalityEnum.HIGH,
            purchase_date=date(2020, 1, 1),
            purchase_cost=Decimal("50000")
        )
        assert data.asset_code == "EQ001"
        assert data.criticality == AssetCriticalityEnum.HIGH

    def test_work_order_create_schema(self):
        """Tester le schéma WorkOrderCreate."""
        data = WorkOrderCreate(
            title="Maintenance mensuelle préventive",
            asset_id=1,
            maintenance_type=MaintenanceTypeEnum.PREVENTIVE,
            priority=WorkOrderPriorityEnum.MEDIUM,
            description="Maintenance mensuelle",
            scheduled_start_date=datetime.utcnow()
        )
        assert data.maintenance_type == MaintenanceTypeEnum.PREVENTIVE

    def test_failure_create_schema(self):
        """Tester le schéma FailureCreate."""
        data = FailureCreate(
            asset_id=1,
            failure_type=FailureTypeEnum.MECHANICAL,
            description="Arrêt complet machine - moteur grillé",
            failure_date=datetime.utcnow()
        )
        assert data.failure_type == FailureTypeEnum.MECHANICAL

    def test_maintenance_plan_create_schema(self):
        """Tester le schéma MaintenancePlanCreate."""
        data = MaintenancePlanCreate(
            plan_code="MP001",
            name="Plan préventif mensuel",
            maintenance_type=MaintenanceTypeEnum.PREVENTIVE,
            trigger_type="TIME",
            frequency_value=1,
            frequency_unit="MONTH"
        )
        assert data.plan_code == "MP001"
        assert data.maintenance_type == MaintenanceTypeEnum.PREVENTIVE

    def test_spare_part_create_schema(self):
        """Tester le schéma SparePartCreate."""
        data = SparePartCreate(
            part_code="SP001",
            name="Filtre à huile",
            unit="PCE",
            unit_cost=Decimal("25"),
            min_stock_level=Decimal("5")
        )
        assert data.part_code == "SP001"
        assert data.unit_cost == Decimal("25")


# =============================================================================
# TESTS DU SERVICE - ACTIFS
# =============================================================================

class TestMaintenanceServiceAssets:
    """Tests du service Maintenance - Actifs."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return MaintenanceService(mock_db, tenant_id=1, user_id=1)

    def test_create_asset(self, service, mock_db):
        """Tester la création d'un actif."""
        data = AssetCreate(
            asset_code="EQ001",
            name="Compresseur",
            category=AssetCategoryEnum.MACHINE,
            criticality=AssetCriticalityEnum.HIGH
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_asset(data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result.asset_code == "EQ001"

    def test_get_asset(self, service, mock_db):
        """Tester la récupération d'un actif."""
        mock_asset = MagicMock(spec=Asset)
        mock_asset.id = 1
        mock_asset.asset_code = "EQ001"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_asset

        result = service.get_asset(1)

        assert result.id == 1
        assert result.asset_code == "EQ001"

    def test_list_assets(self, service, mock_db):
        """Tester la liste des actifs."""
        mock_assets = [MagicMock(spec=Asset), MagicMock(spec=Asset)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_assets

        assets, total = service.list_assets()

        assert total == 2
        assert len(assets) == 2

    def test_update_asset(self, service, mock_db):
        """Tester la mise à jour d'un actif."""
        mock_asset = MagicMock(spec=Asset)
        mock_asset.id = 1
        mock_asset.name = "Old Name"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_asset

        data = AssetUpdate(name="New Name")
        result = service.update_asset(1, data)

        mock_db.commit.assert_called_once()
        assert result is not None

    def test_delete_asset(self, service, mock_db):
        """Tester la suppression d'un actif (soft delete)."""
        mock_asset = MagicMock(spec=Asset)
        mock_asset.id = 1

        mock_db.query.return_value.filter.return_value.first.return_value = mock_asset

        result = service.delete_asset(1)

        assert result is True
        assert mock_asset.status == AssetStatus.DISPOSED


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
        return MaintenanceService(mock_db, tenant_id=1, user_id=1)

    def test_create_work_order(self, service, mock_db):
        """Tester la création d'un ordre de travail."""
        data = WorkOrderCreate(
            title="Réparation urgente compresseur",
            asset_id=1,
            maintenance_type=MaintenanceTypeEnum.CORRECTIVE,
            priority=WorkOrderPriorityEnum.HIGH,
            description="Réparation urgente"
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        # Mock pour le générateur de numéro
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = service.create_work_order(data)

        mock_db.add.assert_called()
        assert result.title == "Réparation urgente compresseur"

    def test_start_work_order(self, service, mock_db):
        """Tester le démarrage d'un OT."""
        mock_wo = MagicMock(spec=MaintenanceWorkOrder)
        mock_wo.status = WorkOrderStatus.APPROVED
        mock_wo.asset = MagicMock()

        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_wo

        result = service.start_work_order(1)

        assert mock_wo.status == WorkOrderStatus.IN_PROGRESS
        assert mock_wo.actual_start_date is not None

    def test_complete_work_order(self, service, mock_db):
        """Tester la clôture d'un OT."""
        mock_wo = MagicMock(spec=MaintenanceWorkOrder)
        mock_wo.status = WorkOrderStatus.IN_PROGRESS
        mock_wo.actual_start_date = datetime.utcnow() - timedelta(hours=2)
        mock_wo.asset = MagicMock()

        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_wo
        mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("0")

        data = WorkOrderComplete(
            completion_notes="Travail terminé avec succès"
        )
        result = service.complete_work_order(1, data)

        assert mock_wo.status == WorkOrderStatus.COMPLETED
        assert mock_wo.completion_notes == "Travail terminé avec succès"

    def test_add_labor_entry(self, service, mock_db):
        """Tester l'ajout d'une entrée de main d'oeuvre."""
        mock_wo = MagicMock(spec=MaintenanceWorkOrder)
        mock_wo.actual_labor_hours = Decimal("0")

        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_wo

        data = WorkOrderLaborCreate(
            technician_id=1,
            work_date=date.today(),
            hours_worked=Decimal("4"),
            hourly_rate=Decimal("50"),
            work_description="Remplacement filtre"
        )
        result = service.add_labor_entry(1, data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_add_part_used(self, service, mock_db):
        """Tester l'ajout d'une pièce utilisée."""
        mock_wo = MagicMock(spec=MaintenanceWorkOrder)

        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_wo

        data = WorkOrderPartCreate(
            part_description="Filtre à huile",
            quantity_used=Decimal("2"),
            unit="PCE",
            unit_cost=Decimal("25")
        )
        result = service.add_part_used(1, data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


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
        return MaintenanceService(mock_db, tenant_id=1, user_id=1)

    def test_create_failure(self, service, mock_db):
        """Tester le signalement d'une panne."""
        data = FailureCreate(
            asset_id=1,
            failure_type=FailureTypeEnum.MECHANICAL,
            description="Moteur grillé - arrêt complet",
            failure_date=datetime.utcnow(),
            production_stopped=True
        )

        mock_asset = MagicMock(spec=Asset)
        mock_asset.status = AssetStatus.ACTIVE

        # Mock pour le générateur de numéro
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_asset
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_failure(data)

        mock_db.add.assert_called()
        assert result.asset_id == 1

    def test_get_failure(self, service, mock_db):
        """Tester la récupération d'une panne."""
        mock_failure = MagicMock(spec=Failure)
        mock_failure.id = 1
        mock_failure.failure_number = "FL-202601-001"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_failure

        result = service.get_failure(1)

        assert result.id == 1
        assert result.failure_number == "FL-202601-001"

    def test_list_failures(self, service, mock_db):
        """Tester la liste des pannes."""
        mock_failures = [MagicMock(spec=Failure), MagicMock(spec=Failure)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_failures

        failures, total = service.list_failures()

        assert total == 2
        assert len(failures) == 2


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
        return MaintenanceService(mock_db, tenant_id=1, user_id=1)

    def test_create_maintenance_plan(self, service, mock_db):
        """Tester la création d'un plan."""
        data = MaintenancePlanCreate(
            plan_code="MP001",
            name="Plan préventif mensuel",
            maintenance_type=MaintenanceTypeEnum.PREVENTIVE,
            trigger_type="TIME",
            frequency_value=1,
            frequency_unit="MONTH"
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_maintenance_plan(data)

        mock_db.add.assert_called()
        assert result.plan_code == "MP001"

    def test_get_maintenance_plan(self, service, mock_db):
        """Tester la récupération d'un plan."""
        mock_plan = MagicMock(spec=MaintenancePlan)
        mock_plan.id = 1
        mock_plan.plan_code = "MP001"

        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_plan

        result = service.get_maintenance_plan(1)

        assert result.id == 1
        assert result.plan_code == "MP001"

    def test_list_maintenance_plans(self, service, mock_db):
        """Tester la liste des plans."""
        mock_plans = [MagicMock(spec=MaintenancePlan)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.options.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_plans

        plans, total = service.list_maintenance_plans()

        assert total == 1
        assert len(plans) == 1


# =============================================================================
# TESTS DU SERVICE - PIÈCES DE RECHANGE
# =============================================================================

class TestMaintenanceServiceSpareParts:
    """Tests du service Maintenance - Pièces de rechange."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return MaintenanceService(mock_db, tenant_id=1, user_id=1)

    def test_create_spare_part(self, service, mock_db):
        """Tester la création d'une pièce."""
        data = SparePartCreate(
            part_code="SP001",
            name="Filtre à huile",
            unit="PCE",
            unit_cost=Decimal("25"),
            min_stock_level=Decimal("5")
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_spare_part(data)

        mock_db.add.assert_called_once()
        assert result.part_code == "SP001"

    def test_get_spare_part(self, service, mock_db):
        """Tester la récupération d'une pièce."""
        mock_part = MagicMock(spec=SparePart)
        mock_part.id = 1
        mock_part.part_code = "SP001"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_part

        result = service.get_spare_part(1)

        assert result.id == 1
        assert result.part_code == "SP001"

    def test_list_spare_parts(self, service, mock_db):
        """Tester la liste des pièces."""
        mock_parts = [MagicMock(spec=SparePart), MagicMock(spec=SparePart)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_parts

        parts, total = service.list_spare_parts()

        assert total == 2
        assert len(parts) == 2


# =============================================================================
# TESTS DU SERVICE - CONTRATS
# =============================================================================

class TestMaintenanceServiceContracts:
    """Tests du service Maintenance - Contrats."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return MaintenanceService(mock_db, tenant_id=1, user_id=1)

    def test_create_contract(self, service, mock_db):
        """Tester la création d'un contrat."""
        data = ContractCreate(
            contract_code="MC001",
            name="Contrat maintenance annuel",
            contract_type=ContractType.FULL_SERVICE,
            vendor_id=1,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365)
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_contract(data)

        mock_db.add.assert_called_once()
        assert result.contract_code == "MC001"

    def test_get_contract(self, service, mock_db):
        """Tester la récupération d'un contrat."""
        mock_contract = MagicMock(spec=MaintenanceContract)
        mock_contract.id = 1
        mock_contract.contract_code = "MC001"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        result = service.get_contract(1)

        assert result.id == 1
        assert result.contract_code == "MC001"


# =============================================================================
# TESTS DU SERVICE - DASHBOARD
# =============================================================================

class TestMaintenanceServiceDashboard:
    """Tests du service Maintenance - Dashboard."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return MaintenanceService(mock_db, tenant_id=1, user_id=1)

    def test_get_dashboard(self, service, mock_db):
        """Tester le dashboard maintenance."""
        # Mock toutes les requêtes de comptage
        mock_db.query.return_value.filter.return_value.scalar.return_value = 5

        result = service.get_dashboard()

        assert isinstance(result, MaintenanceDashboard)
        assert result.assets_total == 5


# =============================================================================
# TESTS FACTORY
# =============================================================================

class TestFactory:
    """Tests de la factory."""

    def test_get_maintenance_service(self):
        """Tester la factory."""
        mock_db = MagicMock()
        service = get_maintenance_service(mock_db, tenant_id=1, user_id=1)

        assert isinstance(service, MaintenanceService)
        assert service.tenant_id == 1
        assert service.user_id == 1


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

    def test_downtime_calculation(self):
        """Tester le calcul du temps d'arrêt."""
        start_time = datetime(2026, 1, 1, 8, 0, 0)
        end_time = datetime(2026, 1, 1, 12, 30, 0)

        delta = end_time - start_time
        downtime_hours = Decimal(str(delta.total_seconds() / 3600))

        assert downtime_hours == Decimal("4.5")


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
