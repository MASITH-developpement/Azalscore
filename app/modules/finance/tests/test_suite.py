"""
Tests pour le module Finance Suite (orchestrateur).

Coverage:
- Service: dashboard, modules, config, alerts, workflows
- Router: tous les endpoints
- Validation: tenant isolation
"""

import pytest
from decimal import Decimal
from datetime import datetime, date
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.modules.finance.suite.service import (
    FinanceSuiteService,
    FinanceDashboard,
    ModuleStatus,
    SuiteConfig,
    AlertSeverity,
    WorkflowType,
    WorkflowStatus,
    FinanceAlert,
    WorkflowInstance,
    FINANCE_MODULES,
)
from app.modules.finance.suite.router import router


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def db_session():
    """Session de base de données mockée."""
    return MagicMock()


@pytest.fixture
def tenant_id():
    """ID tenant de test."""
    return "tenant-suite-test-123"


@pytest.fixture
def service(db_session, tenant_id):
    """Service Finance Suite."""
    return FinanceSuiteService(db=db_session, tenant_id=tenant_id)


@pytest.fixture
def app(service, tenant_id):
    """Application FastAPI de test."""
    from app.core.saas_context import SaaSContext

    test_app = FastAPI()
    test_app.include_router(router)

    def override_service():
        return service

    def override_context():
        return SaaSContext(tenant_id=tenant_id)

    from app.modules.finance.suite.router import (
        get_suite_service,
        get_saas_context,
    )

    test_app.dependency_overrides[get_suite_service] = override_service
    test_app.dependency_overrides[get_saas_context] = override_context

    return test_app


@pytest.fixture
def client(app):
    """Client de test."""
    return TestClient(app)


# =============================================================================
# TESTS SERVICE - INITIALIZATION
# =============================================================================


class TestServiceInit:
    """Tests d'initialisation du service."""

    def test_init_with_tenant_id(self, db_session, tenant_id):
        """Service s'initialise avec tenant_id."""
        service = FinanceSuiteService(db=db_session, tenant_id=tenant_id)
        assert service.tenant_id == tenant_id

    def test_init_requires_tenant_id(self, db_session):
        """Service requiert tenant_id."""
        with pytest.raises(ValueError, match="tenant_id est requis"):
            FinanceSuiteService(db=db_session, tenant_id="")


# =============================================================================
# TESTS SERVICE - DASHBOARD
# =============================================================================


class TestDashboard:
    """Tests du tableau de bord."""

    @pytest.mark.asyncio
    async def test_get_dashboard(self, service):
        """Récupération du dashboard."""
        dashboard = await service.get_dashboard()

        assert dashboard.tenant_id == service.tenant_id
        assert dashboard.current_balance > 0
        assert isinstance(dashboard.modules_status, dict)

    @pytest.mark.asyncio
    async def test_dashboard_has_all_fields(self, service):
        """Dashboard contient tous les champs."""
        dashboard = await service.get_dashboard()

        assert hasattr(dashboard, "current_balance")
        assert hasattr(dashboard, "available_balance")
        assert hasattr(dashboard, "invoices_pending")
        assert hasattr(dashboard, "active_cards")
        assert hasattr(dashboard, "alerts")


# =============================================================================
# TESTS SERVICE - MODULES
# =============================================================================


class TestModules:
    """Tests de gestion des modules."""

    @pytest.mark.asyncio
    async def test_list_modules(self, service):
        """Liste des modules."""
        modules = await service.list_modules()
        assert len(modules) == len(FINANCE_MODULES)

    @pytest.mark.asyncio
    async def test_get_module(self, service):
        """Récupération d'un module."""
        module = await service.get_module("reconciliation")

        assert module is not None
        assert module.name == "reconciliation"
        assert module.status == ModuleStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_module_not_found(self, service):
        """Module non trouvé."""
        module = await service.get_module("nonexistent")
        assert module is None

    @pytest.mark.asyncio
    async def test_get_module_health(self, service):
        """Health check d'un module."""
        health = await service.get_module_health("currency")

        assert health["module"] == "currency"
        assert health["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_suite_health(self, service):
        """Health check global."""
        health = await service.get_suite_health()

        assert health["suite"] == "finance"
        assert health["status"] == "healthy"
        assert health["modules_total"] == len(FINANCE_MODULES)


# =============================================================================
# TESTS SERVICE - CONFIGURATION
# =============================================================================


class TestConfiguration:
    """Tests de configuration."""

    @pytest.mark.asyncio
    async def test_get_config(self, service):
        """Récupération de la config."""
        config = await service.get_config()

        assert config.tenant_id == service.tenant_id
        assert config.default_currency == "EUR"

    @pytest.mark.asyncio
    async def test_update_config(self, service):
        """Mise à jour de la config."""
        config = await service.update_config(
            default_currency="USD",
            fiscal_year_start_month=4,
        )

        assert config.default_currency == "USD"
        assert config.fiscal_year_start_month == 4

    @pytest.mark.asyncio
    async def test_update_config_partial(self, service):
        """Mise à jour partielle."""
        original = await service.get_config()
        original_currency = original.default_currency

        await service.update_config(auto_reconciliation_enabled=False)

        config = await service.get_config()
        assert config.default_currency == original_currency  # Non modifié
        assert config.auto_reconciliation_enabled is False


# =============================================================================
# TESTS SERVICE - ALERTS
# =============================================================================


class TestAlerts:
    """Tests des alertes."""

    @pytest.mark.asyncio
    async def test_create_alert(self, service):
        """Création d'une alerte."""
        alert = await service.create_alert(
            severity=AlertSeverity.WARNING,
            module="cash_forecast",
            title="Solde faible prévu",
            message="Le solde prévu dans 30 jours est inférieur au seuil",
        )

        assert alert.severity == AlertSeverity.WARNING
        assert alert.module == "cash_forecast"
        assert not alert.acknowledged

    @pytest.mark.asyncio
    async def test_list_alerts(self, service):
        """Liste des alertes."""
        await service.create_alert(
            severity=AlertSeverity.INFO,
            module="test",
            title="Test",
            message="Message test",
        )

        alerts = await service.list_alerts()
        assert len(alerts) >= 1

    @pytest.mark.asyncio
    async def test_list_alerts_by_severity(self, service):
        """Filtrage par sévérité."""
        await service.create_alert(
            severity=AlertSeverity.CRITICAL,
            module="test",
            title="Critical",
            message="Message",
        )

        alerts = await service.list_alerts(severity=AlertSeverity.CRITICAL)
        assert all(a.severity == AlertSeverity.CRITICAL for a in alerts)

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, service):
        """Acquittement d'une alerte."""
        alert = await service.create_alert(
            severity=AlertSeverity.WARNING,
            module="test",
            title="To acknowledge",
            message="Message",
        )

        success = await service.acknowledge_alert(alert.id, "user-123")
        assert success

        alerts = await service.list_alerts(acknowledged=True)
        assert any(a.id == alert.id for a in alerts)

    @pytest.mark.asyncio
    async def test_get_alert_summary(self, service):
        """Résumé des alertes."""
        await service.create_alert(
            severity=AlertSeverity.ERROR,
            module="test",
            title="Error",
            message="Error message",
        )

        summary = await service.get_alert_summary()
        assert "total_alerts" in summary
        assert "by_severity" in summary


# =============================================================================
# TESTS SERVICE - WORKFLOWS
# =============================================================================


class TestWorkflows:
    """Tests des workflows."""

    @pytest.mark.asyncio
    async def test_start_workflow(self, service):
        """Démarrage d'un workflow."""
        workflow = await service.start_workflow(
            workflow_type=WorkflowType.INVOICE_PROCESSING,
            data={"invoice_id": "inv-001"},
            created_by="user-123",
        )

        assert workflow.workflow_type == WorkflowType.INVOICE_PROCESSING
        assert workflow.status == WorkflowStatus.IN_PROGRESS
        assert workflow.current_step == 1

    @pytest.mark.asyncio
    async def test_get_workflow(self, service):
        """Récupération d'un workflow."""
        created = await service.start_workflow(
            workflow_type=WorkflowType.PAYMENT_APPROVAL,
            data={},
        )

        workflow = await service.get_workflow(created.id)
        assert workflow is not None
        assert workflow.id == created.id

    @pytest.mark.asyncio
    async def test_list_workflows(self, service):
        """Liste des workflows."""
        await service.start_workflow(
            workflow_type=WorkflowType.RECONCILIATION,
            data={},
        )

        workflows = await service.list_workflows()
        assert len(workflows) >= 1

    @pytest.mark.asyncio
    async def test_advance_workflow(self, service):
        """Avancement d'un workflow."""
        workflow = await service.start_workflow(
            workflow_type=WorkflowType.RECONCILIATION,
            data={},
        )
        initial_step = workflow.current_step

        advanced = await service.advance_workflow(workflow.id)
        assert advanced.current_step == initial_step + 1

    @pytest.mark.asyncio
    async def test_complete_workflow(self, service):
        """Completion d'un workflow."""
        workflow = await service.start_workflow(
            workflow_type=WorkflowType.RECONCILIATION,  # 2 étapes
            data={},
        )

        # Avancer jusqu'à completion
        for _ in range(workflow.total_steps):
            workflow = await service.advance_workflow(workflow.id)

        assert workflow.status == WorkflowStatus.COMPLETED
        assert workflow.completed_at is not None

    @pytest.mark.asyncio
    async def test_cancel_workflow(self, service):
        """Annulation d'un workflow."""
        workflow = await service.start_workflow(
            workflow_type=WorkflowType.EXPENSE_REPORT,
            data={},
        )

        success = await service.cancel_workflow(workflow.id, "Test cancellation")
        assert success

        cancelled = await service.get_workflow(workflow.id)
        assert cancelled.status == WorkflowStatus.CANCELLED


# =============================================================================
# TESTS SERVICE - REPORTING
# =============================================================================


class TestReporting:
    """Tests des rapports."""

    @pytest.mark.asyncio
    async def test_get_finance_summary(self, service):
        """Résumé financier."""
        summary = await service.get_finance_summary(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )

        assert "period" in summary
        assert "cash_flow" in summary
        assert "invoices" in summary

    @pytest.mark.asyncio
    async def test_get_kpis(self, service):
        """KPIs finance."""
        kpis = await service.get_kpis()

        assert "cash_runway_days" in kpis
        assert "dso" in kpis
        assert "dpo" in kpis


# =============================================================================
# TESTS ROUTER
# =============================================================================


class TestRouter:
    """Tests des endpoints."""

    def test_get_dashboard(self, client):
        """GET /dashboard."""
        response = client.get("/v3/finance/suite/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert "current_balance" in data
        assert "modules_status" in data

    def test_list_modules(self, client):
        """GET /modules."""
        response = client.get("/v3/finance/suite/modules")

        assert response.status_code == 200
        modules = response.json()
        assert len(modules) == len(FINANCE_MODULES)

    def test_get_module(self, client):
        """GET /modules/{name}."""
        response = client.get("/v3/finance/suite/modules/currency")

        assert response.status_code == 200
        assert response.json()["name"] == "currency"

    def test_get_module_not_found(self, client):
        """GET /modules/{name} - non trouvé."""
        response = client.get("/v3/finance/suite/modules/nonexistent")
        assert response.status_code == 404

    def test_get_module_health(self, client):
        """GET /modules/{name}/health."""
        response = client.get("/v3/finance/suite/modules/reconciliation/health")

        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_get_config(self, client):
        """GET /config."""
        response = client.get("/v3/finance/suite/config")

        assert response.status_code == 200
        data = response.json()
        assert "default_currency" in data

    def test_update_config(self, client):
        """PUT /config."""
        response = client.put(
            "/v3/finance/suite/config",
            json={
                "default_currency": "GBP",
                "auto_reconciliation_enabled": False,
            }
        )

        assert response.status_code == 200
        assert response.json()["default_currency"] == "GBP"

    def test_list_alerts(self, client):
        """GET /alerts."""
        response = client.get("/v3/finance/suite/alerts")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_alert(self, client):
        """POST /alerts."""
        response = client.post(
            "/v3/finance/suite/alerts",
            json={
                "severity": "warning",
                "module": "test",
                "title": "Test Alert",
                "message": "This is a test alert",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Alert"

    def test_acknowledge_alert(self, client):
        """POST /alerts/{id}/acknowledge."""
        # Créer une alerte
        create_response = client.post(
            "/v3/finance/suite/alerts",
            json={
                "severity": "info",
                "module": "test",
                "title": "To Ack",
                "message": "Message",
            }
        )
        alert_id = create_response.json()["id"]

        response = client.post(
            f"/v3/finance/suite/alerts/{alert_id}/acknowledge",
            json={"user_id": "user-123"},
        )

        assert response.status_code == 200
        assert response.json()["success"]

    def test_get_alert_summary(self, client):
        """GET /alerts/summary."""
        response = client.get("/v3/finance/suite/alerts/summary")

        assert response.status_code == 200
        assert "total_alerts" in response.json()

    def test_list_workflows(self, client):
        """GET /workflows."""
        response = client.get("/v3/finance/suite/workflows")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_start_workflow(self, client):
        """POST /workflows."""
        response = client.post(
            "/v3/finance/suite/workflows",
            json={
                "workflow_type": "invoice_processing",
                "data": {"invoice_id": "inv-001"},
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["workflow_type"] == "invoice_processing"
        assert data["status"] == "in_progress"

    def test_get_workflow(self, client):
        """GET /workflows/{id}."""
        # Créer un workflow
        create_response = client.post(
            "/v3/finance/suite/workflows",
            json={"workflow_type": "payment_approval", "data": {}},
        )
        workflow_id = create_response.json()["id"]

        response = client.get(f"/v3/finance/suite/workflows/{workflow_id}")

        assert response.status_code == 200
        assert response.json()["id"] == workflow_id

    def test_advance_workflow(self, client):
        """POST /workflows/{id}/advance."""
        # Créer un workflow
        create_response = client.post(
            "/v3/finance/suite/workflows",
            json={"workflow_type": "reconciliation", "data": {}},
        )
        workflow_id = create_response.json()["id"]

        response = client.post(f"/v3/finance/suite/workflows/{workflow_id}/advance")

        assert response.status_code == 200
        assert response.json()["current_step"] == 2

    def test_cancel_workflow(self, client):
        """POST /workflows/{id}/cancel."""
        # Créer un workflow
        create_response = client.post(
            "/v3/finance/suite/workflows",
            json={"workflow_type": "expense_report", "data": {}},
        )
        workflow_id = create_response.json()["id"]

        response = client.post(
            f"/v3/finance/suite/workflows/{workflow_id}/cancel",
            json={"reason": "Test cancel"},
        )

        assert response.status_code == 200
        assert response.json()["success"]

    def test_get_summary(self, client):
        """GET /summary."""
        response = client.get(
            "/v3/finance/suite/summary",
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
            }
        )

        assert response.status_code == 200
        assert "cash_flow" in response.json()

    def test_get_kpis(self, client):
        """GET /kpis."""
        response = client.get("/v3/finance/suite/kpis")

        assert response.status_code == 200
        data = response.json()
        assert "cash_runway_days" in data
        assert "dso" in data

    def test_health_check(self, client):
        """GET /health."""
        response = client.get("/v3/finance/suite/health")

        assert response.status_code == 200
        data = response.json()
        assert data["suite"] == "finance"
        assert data["status"] == "healthy"


# =============================================================================
# TESTS ENUMS
# =============================================================================


class TestEnums:
    """Tests des enums."""

    def test_module_status_values(self):
        """Valeurs de ModuleStatus."""
        assert ModuleStatus.ACTIVE.value == "active"
        assert ModuleStatus.DEGRADED.value == "degraded"

    def test_alert_severity_values(self):
        """Valeurs de AlertSeverity."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_workflow_type_values(self):
        """Valeurs de WorkflowType."""
        assert WorkflowType.INVOICE_PROCESSING.value == "invoice_processing"
        assert WorkflowType.PAYMENT_APPROVAL.value == "payment_approval"

    def test_workflow_status_values(self):
        """Valeurs de WorkflowStatus."""
        assert WorkflowStatus.IN_PROGRESS.value == "in_progress"
        assert WorkflowStatus.COMPLETED.value == "completed"


# =============================================================================
# TESTS FINANCE_MODULES
# =============================================================================


class TestFinanceModules:
    """Tests de la constante FINANCE_MODULES."""

    def test_all_modules_defined(self):
        """Tous les modules sont définis."""
        expected = [
            "reconciliation",
            "invoice_ocr",
            "cash_forecast",
            "auto_categorization",
            "currency",
            "virtual_cards",
            "integration",
        ]

        for module in expected:
            assert module in FINANCE_MODULES

    def test_modules_have_required_fields(self):
        """Modules ont tous les champs requis."""
        for name, module in FINANCE_MODULES.items():
            assert module.name == name
            assert module.display_name
            assert module.description
            assert module.endpoint
            assert module.version


# =============================================================================
# TESTS DATACLASSES
# =============================================================================


class TestDataClasses:
    """Tests des dataclasses."""

    def test_finance_dashboard_creation(self, tenant_id):
        """Création FinanceDashboard."""
        dashboard = FinanceDashboard(
            tenant_id=tenant_id,
            generated_at=datetime.now(),
            current_balance=Decimal("10000"),
            available_balance=Decimal("9000"),
            projected_balance_30d=Decimal("12000"),
            pending_entries=5,
            unreconciled_transactions=3,
            invoices_pending=10,
            invoices_overdue=2,
            total_receivable=Decimal("5000"),
            total_payable=Decimal("3000"),
            active_cards=4,
            cards_near_limit=1,
        )

        assert dashboard.current_balance == Decimal("10000")

    def test_suite_config_defaults(self, tenant_id):
        """SuiteConfig avec défauts."""
        config = SuiteConfig(tenant_id=tenant_id)

        assert config.default_currency == "EUR"
        assert config.fiscal_year_start_month == 1
        assert config.auto_reconciliation_enabled is True

    def test_finance_alert_creation(self, tenant_id):
        """Création FinanceAlert."""
        alert = FinanceAlert(
            id="alert-1",
            tenant_id=tenant_id,
            severity=AlertSeverity.WARNING,
            module="test",
            title="Test",
            message="Test message",
        )

        assert not alert.acknowledged
        assert alert.acknowledged_at is None

    def test_workflow_instance_creation(self, tenant_id):
        """Création WorkflowInstance."""
        workflow = WorkflowInstance(
            id="wf-1",
            tenant_id=tenant_id,
            workflow_type=WorkflowType.INVOICE_PROCESSING,
            status=WorkflowStatus.IN_PROGRESS,
            current_step=1,
            total_steps=4,
        )

        assert workflow.completed_at is None
