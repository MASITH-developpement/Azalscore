"""
Tests for MES Module
====================

Tests unitaires pour le module MES (Manufacturing Execution System).
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.modules.production.mes.service import (
    MESService,
    Workstation,
    WorkstationStatus,
    ProductionOperation,
    OperationStatus,
    TimeEntry,
    QualityCheck,
    Downtime,
    DowntimeReason,
    CheckResult,
    OEEMetrics,
)


# ========================
# SERVICE INIT TESTS
# ========================

class TestMESServiceInit:
    """Tests d'initialisation du service."""

    def test_init_with_valid_tenant(self):
        """Test initialisation avec tenant valide."""
        service = MESService(db=MagicMock(), tenant_id="tenant-123")
        assert service.tenant_id == "tenant-123"

    def test_init_without_tenant_raises(self):
        """Test que l'initialisation sans tenant échoue."""
        with pytest.raises(ValueError, match="tenant_id is required"):
            MESService(db=MagicMock(), tenant_id="")


# ========================
# WORKSTATION TESTS
# ========================

class TestWorkstationManagement:
    """Tests de gestion des postes de travail."""

    @pytest.fixture
    def service(self):
        return MESService(db=MagicMock(), tenant_id="tenant-123")

    @pytest.mark.asyncio
    async def test_create_workstation(self, service):
        """Test création de poste."""
        ws = await service.create_workstation(
            code="WS-001",
            name="Poste Assemblage 1",
            workstation_type="assembly",
            location="Hall A",
            capacity_per_hour=50.0
        )

        assert ws.id is not None
        assert ws.tenant_id == "tenant-123"
        assert ws.code == "WS-001"
        assert ws.status == WorkstationStatus.OFFLINE
        assert ws.capacity_per_hour == 50.0

    @pytest.mark.asyncio
    async def test_get_workstation(self, service):
        """Test récupération de poste."""
        created = await service.create_workstation(
            code="WS-002",
            name="Test",
            workstation_type="machine"
        )

        ws = await service.get_workstation(created.id)
        assert ws is not None
        assert ws.code == "WS-002"

    @pytest.mark.asyncio
    async def test_get_workstation_by_code(self, service):
        """Test récupération par code."""
        await service.create_workstation(
            code="UNIQUE-CODE",
            name="Test",
            workstation_type="manual"
        )

        ws = await service.get_workstation_by_code("UNIQUE-CODE")
        assert ws is not None
        assert ws.code == "UNIQUE-CODE"

    @pytest.mark.asyncio
    async def test_list_workstations(self, service):
        """Test liste des postes."""
        await service.create_workstation(code="WS-A", name="A", workstation_type="assembly")
        await service.create_workstation(code="WS-B", name="B", workstation_type="machine")

        workstations = await service.list_workstations()
        assert len(workstations) == 2

    @pytest.mark.asyncio
    async def test_list_workstations_by_type(self, service):
        """Test liste par type."""
        await service.create_workstation(code="WS-A", name="A", workstation_type="assembly")
        await service.create_workstation(code="WS-B", name="B", workstation_type="machine")

        assembly = await service.list_workstations(workstation_type="assembly")
        assert len(assembly) == 1
        assert assembly[0].code == "WS-A"

    @pytest.mark.asyncio
    async def test_list_workstations_by_status(self, service):
        """Test liste par statut."""
        ws1 = await service.create_workstation(code="WS-A", name="A", workstation_type="test")
        ws2 = await service.create_workstation(code="WS-B", name="B", workstation_type="test")
        ws2.status = WorkstationStatus.RUNNING

        running = await service.list_workstations(status=WorkstationStatus.RUNNING)
        assert len(running) == 1
        assert running[0].code == "WS-B"

    @pytest.mark.asyncio
    async def test_update_workstation_status(self, service):
        """Test mise à jour statut."""
        ws = await service.create_workstation(
            code="WS-001",
            name="Test",
            workstation_type="test"
        )

        updated = await service.update_workstation_status(
            ws.id,
            status=WorkstationStatus.RUNNING,
            operator_id="OP-001"
        )

        assert updated.status == WorkstationStatus.RUNNING
        assert updated.current_operator_id == "OP-001"


# ========================
# OPERATION TESTS
# ========================

class TestOperationManagement:
    """Tests de gestion des opérations."""

    @pytest.fixture
    async def service_with_workstation(self):
        service = MESService(db=MagicMock(), tenant_id="tenant-123")
        ws = await service.create_workstation(
            code="WS-001",
            name="Test",
            workstation_type="assembly",
            capacity_per_hour=60.0
        )
        return service, ws

    @pytest.mark.asyncio
    async def test_create_operation(self, service_with_workstation):
        """Test création d'opération."""
        service, ws = service_with_workstation

        op = await service.create_operation(
            workstation_id=ws.id,
            order_id="ORD-001",
            product_id="PROD-001",
            operation_code="OP10",
            operation_name="Assemblage",
            planned_qty=100
        )

        assert op.id is not None
        assert op.tenant_id == "tenant-123"
        assert op.status == OperationStatus.PENDING
        assert op.planned_qty == 100

    @pytest.mark.asyncio
    async def test_start_operation(self, service_with_workstation):
        """Test démarrage d'opération."""
        service, ws = service_with_workstation

        op = await service.create_operation(
            workstation_id=ws.id,
            order_id="ORD-001",
            product_id="PROD-001",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=50
        )

        started = await service.start_operation(
            op.id,
            operator_id="OP-001",
            setup_time=15.0
        )

        assert started.status == OperationStatus.RUNNING
        assert started.operator_id == "OP-001"
        assert started.setup_time == 15.0
        assert started.actual_start is not None

        # Check workstation updated
        ws_updated = await service.get_workstation(ws.id)
        assert ws_updated.status == WorkstationStatus.RUNNING
        assert ws_updated.current_operation_id == op.id

    @pytest.mark.asyncio
    async def test_pause_operation(self, service_with_workstation):
        """Test pause d'opération."""
        service, ws = service_with_workstation

        op = await service.create_operation(
            workstation_id=ws.id,
            order_id="ORD-001",
            product_id="PROD-001",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=50
        )
        await service.start_operation(op.id, operator_id="OP-001")

        paused = await service.pause_operation(op.id, notes="Pause déjeuner")

        assert paused.status == OperationStatus.PAUSED

        ws_updated = await service.get_workstation(ws.id)
        assert ws_updated.status == WorkstationStatus.PAUSED

    @pytest.mark.asyncio
    async def test_resume_operation(self, service_with_workstation):
        """Test reprise d'opération."""
        service, ws = service_with_workstation

        op = await service.create_operation(
            workstation_id=ws.id,
            order_id="ORD-001",
            product_id="PROD-001",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=50
        )
        await service.start_operation(op.id, operator_id="OP-001")
        await service.pause_operation(op.id)

        resumed = await service.resume_operation(op.id)

        assert resumed.status == OperationStatus.RUNNING

    @pytest.mark.asyncio
    async def test_complete_operation(self, service_with_workstation):
        """Test fin d'opération."""
        service, ws = service_with_workstation

        op = await service.create_operation(
            workstation_id=ws.id,
            order_id="ORD-001",
            product_id="PROD-001",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=100
        )
        await service.start_operation(op.id, operator_id="OP-001")

        completed = await service.complete_operation(
            op.id,
            produced_qty=98,
            scrap_qty=2
        )

        assert completed.status == OperationStatus.COMPLETED
        assert completed.produced_qty == 98
        assert completed.scrap_qty == 2
        assert completed.actual_end is not None

        ws_updated = await service.get_workstation(ws.id)
        assert ws_updated.status == WorkstationStatus.IDLE
        assert ws_updated.current_operation_id is None

    @pytest.mark.asyncio
    async def test_report_production(self, service_with_workstation):
        """Test déclaration partielle."""
        service, ws = service_with_workstation

        op = await service.create_operation(
            workstation_id=ws.id,
            order_id="ORD-001",
            product_id="PROD-001",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=100
        )
        await service.start_operation(op.id, operator_id="OP-001")

        await service.report_production(op.id, quantity=30, scrap_qty=1)
        await service.report_production(op.id, quantity=40, scrap_qty=2)

        op_updated = await service.get_operation(op.id)
        assert op_updated.produced_qty == 70
        assert op_updated.scrap_qty == 3

    @pytest.mark.asyncio
    async def test_list_operations(self, service_with_workstation):
        """Test liste des opérations."""
        service, ws = service_with_workstation

        await service.create_operation(
            workstation_id=ws.id,
            order_id="ORD-001",
            product_id="P1",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=50
        )
        await service.create_operation(
            workstation_id=ws.id,
            order_id="ORD-002",
            product_id="P2",
            operation_code="OP20",
            operation_name="Test 2",
            planned_qty=100
        )

        operations = await service.list_operations()
        assert len(operations) == 2

    @pytest.mark.asyncio
    async def test_list_operations_by_workstation(self, service_with_workstation):
        """Test liste par poste."""
        service, ws = service_with_workstation

        await service.create_operation(
            workstation_id=ws.id,
            order_id="ORD-001",
            product_id="P1",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=50
        )

        operations = await service.list_operations(workstation_id=ws.id)
        assert len(operations) == 1


# ========================
# OPERATION METRICS TESTS
# ========================

class TestOperationMetrics:
    """Tests des métriques d'opération."""

    def test_good_qty(self):
        """Test quantité conforme."""
        op = ProductionOperation(
            id="op-1",
            tenant_id="t1",
            workstation_id="ws-1",
            order_id="ord-1",
            product_id="p1",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=100,
            produced_qty=95,
            scrap_qty=5
        )
        assert op.good_qty == 90

    def test_yield_rate(self):
        """Test taux de rendement."""
        op = ProductionOperation(
            id="op-1",
            tenant_id="t1",
            workstation_id="ws-1",
            order_id="ord-1",
            product_id="p1",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=100,
            produced_qty=100,
            scrap_qty=10
        )
        assert op.yield_rate == 90.0

    def test_completion_rate(self):
        """Test taux de complétion."""
        op = ProductionOperation(
            id="op-1",
            tenant_id="t1",
            workstation_id="ws-1",
            order_id="ord-1",
            product_id="p1",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=100,
            produced_qty=80,
            scrap_qty=0
        )
        assert op.completion_rate == 80.0

    def test_total_time(self):
        """Test temps total."""
        op = ProductionOperation(
            id="op-1",
            tenant_id="t1",
            workstation_id="ws-1",
            order_id="ord-1",
            product_id="p1",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=100,
            setup_time=15.0,
            run_time=45.0
        )
        assert op.total_time == 60.0


# ========================
# QUALITY CHECK TESTS
# ========================

class TestQualityChecks:
    """Tests des contrôles qualité."""

    @pytest.fixture
    def service(self):
        return MESService(db=MagicMock(), tenant_id="tenant-123")

    @pytest.mark.asyncio
    async def test_create_quality_check(self, service):
        """Test création de contrôle."""
        check = await service.create_quality_check(
            operation_id="op-1",
            workstation_id="ws-1",
            check_type="dimension",
            check_name="Longueur",
            expected_value="100mm"
        )

        assert check.id is not None
        assert check.result == CheckResult.PENDING

    @pytest.mark.asyncio
    async def test_record_quality_check_pass(self, service):
        """Test enregistrement contrôle OK."""
        check = await service.create_quality_check(
            operation_id="op-1",
            workstation_id="ws-1",
            check_type="dimension",
            check_name="Longueur",
            expected_value="100mm"
        )

        recorded = await service.record_quality_check(
            check.id,
            actual_value="100mm",
            result=CheckResult.PASS,
            checked_by="OP-001"
        )

        assert recorded.result == CheckResult.PASS
        assert recorded.checked_at is not None

    @pytest.mark.asyncio
    async def test_record_quality_check_fail(self, service):
        """Test enregistrement contrôle NOK."""
        check = await service.create_quality_check(
            operation_id="op-1",
            workstation_id="ws-1",
            check_type="dimension",
            check_name="Longueur",
            expected_value="100mm"
        )

        recorded = await service.record_quality_check(
            check.id,
            actual_value="95mm",
            result=CheckResult.FAIL,
            checked_by="OP-001",
            notes="Hors tolérance"
        )

        assert recorded.result == CheckResult.FAIL
        assert recorded.notes == "Hors tolérance"

    @pytest.mark.asyncio
    async def test_list_quality_checks(self, service):
        """Test liste des contrôles."""
        await service.create_quality_check(
            operation_id="op-1",
            workstation_id="ws-1",
            check_type="visual",
            check_name="Aspect"
        )
        await service.create_quality_check(
            operation_id="op-1",
            workstation_id="ws-1",
            check_type="dimension",
            check_name="Largeur"
        )

        checks = await service.list_quality_checks(operation_id="op-1")
        assert len(checks) == 2


# ========================
# DOWNTIME TESTS
# ========================

class TestDowntime:
    """Tests des arrêts."""

    @pytest.fixture
    async def service_with_workstation(self):
        service = MESService(db=MagicMock(), tenant_id="tenant-123")
        ws = await service.create_workstation(
            code="WS-001",
            name="Test",
            workstation_type="machine"
        )
        return service, ws

    @pytest.mark.asyncio
    async def test_report_downtime(self, service_with_workstation):
        """Test déclaration d'arrêt."""
        service, ws = service_with_workstation

        dt = await service.report_downtime(
            workstation_id=ws.id,
            reason=DowntimeReason.BREAKDOWN,
            description="Panne moteur",
            reported_by="OP-001"
        )

        assert dt.id is not None
        assert dt.reason == DowntimeReason.BREAKDOWN
        assert dt.end_time is None

        ws_updated = await service.get_workstation(ws.id)
        assert ws_updated.status == WorkstationStatus.BREAKDOWN

    @pytest.mark.asyncio
    async def test_report_maintenance_downtime(self, service_with_workstation):
        """Test arrêt maintenance."""
        service, ws = service_with_workstation

        dt = await service.report_downtime(
            workstation_id=ws.id,
            reason=DowntimeReason.MAINTENANCE_SCHEDULED
        )

        ws_updated = await service.get_workstation(ws.id)
        assert ws_updated.status == WorkstationStatus.MAINTENANCE

    @pytest.mark.asyncio
    async def test_resolve_downtime(self, service_with_workstation):
        """Test résolution d'arrêt."""
        service, ws = service_with_workstation

        dt = await service.report_downtime(
            workstation_id=ws.id,
            reason=DowntimeReason.BREAKDOWN
        )

        resolved = await service.resolve_downtime(dt.id, resolved_by="TECH-001")

        assert resolved.end_time is not None
        assert resolved.duration_minutes is not None
        assert resolved.resolved_by == "TECH-001"

        ws_updated = await service.get_workstation(ws.id)
        assert ws_updated.status == WorkstationStatus.IDLE

    @pytest.mark.asyncio
    async def test_list_downtimes(self, service_with_workstation):
        """Test liste des arrêts."""
        service, ws = service_with_workstation

        await service.report_downtime(
            workstation_id=ws.id,
            reason=DowntimeReason.BREAKDOWN
        )
        dt2 = await service.report_downtime(
            workstation_id=ws.id,
            reason=DowntimeReason.CHANGEOVER
        )
        await service.resolve_downtime(dt2.id)

        all_dt = await service.list_downtimes(workstation_id=ws.id)
        assert len(all_dt) == 2

        active = await service.list_downtimes(workstation_id=ws.id, active_only=True)
        assert len(active) == 1

    @pytest.mark.asyncio
    async def test_list_downtimes_by_reason(self, service_with_workstation):
        """Test liste par raison."""
        service, ws = service_with_workstation

        await service.report_downtime(workstation_id=ws.id, reason=DowntimeReason.BREAKDOWN)
        await service.report_downtime(workstation_id=ws.id, reason=DowntimeReason.CHANGEOVER)

        breakdowns = await service.list_downtimes(reason=DowntimeReason.BREAKDOWN)
        assert len(breakdowns) == 1


# ========================
# OEE & STATISTICS TESTS
# ========================

class TestOEE:
    """Tests OEE."""

    @pytest.fixture
    async def service_with_data(self):
        service = MESService(db=MagicMock(), tenant_id="tenant-123")
        ws = await service.create_workstation(
            code="WS-001",
            name="Test",
            workstation_type="machine",
            capacity_per_hour=60.0
        )

        op = await service.create_operation(
            workstation_id=ws.id,
            order_id="ORD-001",
            product_id="PROD-001",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=100
        )
        await service.start_operation(op.id, operator_id="OP-001")
        await service.complete_operation(op.id, produced_qty=95, scrap_qty=5)

        return service, ws

    @pytest.mark.asyncio
    async def test_calculate_oee(self, service_with_data):
        """Test calcul OEE."""
        service, ws = service_with_data

        now = datetime.utcnow()
        oee = await service.calculate_oee(
            workstation_id=ws.id,
            period_start=now - timedelta(hours=1),
            period_end=now
        )

        assert oee.workstation_id == ws.id
        assert 0 <= oee.availability <= 100
        assert 0 <= oee.performance <= 100
        assert 0 <= oee.quality <= 100
        assert 0 <= oee.oee <= 100

    @pytest.mark.asyncio
    async def test_get_workstation_stats(self, service_with_data):
        """Test statistiques poste."""
        service, ws = service_with_data

        stats = await service.get_workstation_stats(ws.id)

        assert stats["workstation_id"] == ws.id
        assert stats["total_operations"] == 1
        assert stats["completed_operations"] == 1


class TestOperatorStats:
    """Tests statistiques opérateur."""

    @pytest.fixture
    def service(self):
        return MESService(db=MagicMock(), tenant_id="tenant-123")

    @pytest.mark.asyncio
    async def test_get_operator_stats(self, service):
        """Test statistiques opérateur."""
        ws = await service.create_workstation(
            code="WS-001",
            name="Test",
            workstation_type="machine"
        )

        op = await service.create_operation(
            workstation_id=ws.id,
            order_id="ORD-001",
            product_id="PROD-001",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=100
        )
        await service.start_operation(op.id, operator_id="OP-001")
        await service.complete_operation(op.id, produced_qty=100, scrap_qty=0)

        stats = await service.get_operator_stats("OP-001")

        assert stats["operator_id"] == "OP-001"
        assert stats["total_operations"] == 1
        assert stats["total_produced"] == 100


class TestDashboard:
    """Tests tableau de bord."""

    @pytest.fixture
    def service(self):
        return MESService(db=MagicMock(), tenant_id="tenant-123")

    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, service):
        """Test données tableau de bord."""
        await service.create_workstation(code="WS-1", name="A", workstation_type="test")
        await service.create_workstation(code="WS-2", name="B", workstation_type="test")

        dashboard = await service.get_dashboard_data()

        assert "workstations" in dashboard
        assert dashboard["workstations"]["total"] == 2
        assert "operations_today" in dashboard


# ========================
# ROUTER TESTS
# ========================

class TestMESRouter:
    """Tests du router MES."""

    @pytest.fixture
    def mock_service(self):
        return AsyncMock(spec=MESService)

    @pytest.fixture
    def client(self, mock_service):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.modules.production.mes.router import router, get_mes_service

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_mes_service] = lambda: mock_service
        return TestClient(app)

    def test_create_workstation_endpoint(self, client, mock_service):
        """Test endpoint création poste."""
        mock_service.create_workstation.return_value = Workstation(
            id="ws-1",
            tenant_id="t1",
            code="WS-001",
            name="Test",
            workstation_type="machine"
        )

        response = client.post(
            "/v3/production/mes/workstations?tenant_id=t1",
            json={
                "code": "WS-001",
                "name": "Test",
                "workstation_type": "machine"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "WS-001"

    def test_list_workstations_endpoint(self, client, mock_service):
        """Test endpoint liste postes."""
        mock_service.list_workstations.return_value = [
            Workstation(id="ws-1", tenant_id="t1", code="WS-1", name="A", workstation_type="machine"),
            Workstation(id="ws-2", tenant_id="t1", code="WS-2", name="B", workstation_type="assembly")
        ]

        response = client.get("/v3/production/mes/workstations?tenant_id=t1")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_create_operation_endpoint(self, client, mock_service):
        """Test endpoint création opération."""
        mock_service.create_operation.return_value = ProductionOperation(
            id="op-1",
            tenant_id="t1",
            workstation_id="ws-1",
            order_id="ORD-001",
            product_id="P1",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=100
        )

        response = client.post(
            "/v3/production/mes/operations?tenant_id=t1",
            json={
                "workstation_id": "ws-1",
                "order_id": "ORD-001",
                "product_id": "P1",
                "operation_code": "OP10",
                "operation_name": "Test",
                "planned_qty": 100
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["operation_code"] == "OP10"

    def test_start_operation_endpoint(self, client, mock_service):
        """Test endpoint démarrage."""
        mock_service.start_operation.return_value = ProductionOperation(
            id="op-1",
            tenant_id="t1",
            workstation_id="ws-1",
            order_id="ORD-001",
            product_id="P1",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=100,
            status=OperationStatus.RUNNING,
            operator_id="OP-001"
        )

        response = client.post(
            "/v3/production/mes/operations/op-1/start?tenant_id=t1",
            json={"operator_id": "OP-001", "setup_time": 10.0}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    def test_complete_operation_endpoint(self, client, mock_service):
        """Test endpoint fin opération."""
        mock_service.complete_operation.return_value = ProductionOperation(
            id="op-1",
            tenant_id="t1",
            workstation_id="ws-1",
            order_id="ORD-001",
            product_id="P1",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=100,
            produced_qty=95,
            scrap_qty=5,
            status=OperationStatus.COMPLETED
        )

        response = client.post(
            "/v3/production/mes/operations/op-1/complete?tenant_id=t1",
            json={"produced_qty": 95, "scrap_qty": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["produced_qty"] == 95

    def test_report_downtime_endpoint(self, client, mock_service):
        """Test endpoint arrêt."""
        mock_service.report_downtime.return_value = Downtime(
            id="dt-1",
            tenant_id="t1",
            workstation_id="ws-1",
            operation_id=None,
            reason=DowntimeReason.BREAKDOWN,
            description="Test"
        )

        response = client.post(
            "/v3/production/mes/downtimes?tenant_id=t1",
            json={
                "workstation_id": "ws-1",
                "reason": "breakdown",
                "description": "Test"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["reason"] == "breakdown"

    def test_dashboard_endpoint(self, client, mock_service):
        """Test endpoint tableau de bord."""
        mock_service.get_dashboard_data.return_value = {
            "workstations": {"total": 5, "running": 3, "idle": 1, "down": 1},
            "operations_today": {"total": 10, "completed": 5, "running": 3, "produced_qty": 500},
            "active_downtimes": 1,
            "downtime_by_reason": {"breakdown": 1}
        }

        response = client.get("/v3/production/mes/dashboard?tenant_id=t1")

        assert response.status_code == 200
        data = response.json()
        assert data["workstations"]["total"] == 5


# ========================
# TENANT ISOLATION TESTS
# ========================

class TestTenantIsolation:
    """Tests d'isolation tenant."""

    @pytest.mark.asyncio
    async def test_workstation_tenant_isolation(self):
        """Test isolation tenant pour postes."""
        service1 = MESService(db=MagicMock(), tenant_id="tenant-1")
        service2 = MESService(db=MagicMock(), tenant_id="tenant-2")

        service2._workstations = service1._workstations

        ws = await service1.create_workstation(
            code="WS-001",
            name="Test",
            workstation_type="machine"
        )

        result = await service2.get_workstation(ws.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_operation_tenant_isolation(self):
        """Test isolation tenant pour opérations."""
        service1 = MESService(db=MagicMock(), tenant_id="tenant-1")
        service2 = MESService(db=MagicMock(), tenant_id="tenant-2")

        service2._workstations = service1._workstations
        service2._operations = service1._operations

        ws = await service1.create_workstation(
            code="WS-001",
            name="Test",
            workstation_type="machine"
        )
        op = await service1.create_operation(
            workstation_id=ws.id,
            order_id="ORD-001",
            product_id="P1",
            operation_code="OP10",
            operation_name="Test",
            planned_qty=100
        )

        result = await service2.get_operation(op.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_downtime_tenant_isolation(self):
        """Test isolation tenant pour arrêts."""
        service1 = MESService(db=MagicMock(), tenant_id="tenant-1")
        service2 = MESService(db=MagicMock(), tenant_id="tenant-2")

        service2._workstations = service1._workstations
        service2._downtimes = service1._downtimes

        ws = await service1.create_workstation(
            code="WS-001",
            name="Test",
            workstation_type="machine"
        )
        dt = await service1.report_downtime(
            workstation_id=ws.id,
            reason=DowntimeReason.BREAKDOWN
        )

        result = await service2.get_downtime(dt.id)
        assert result is None
