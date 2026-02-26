"""
Tests pour le module Prévision Trésorerie.
==========================================

Tests unitaires et d'intégration pour CashForecastService et Router.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.finance.cash_forecast.service import (
    CashForecastService,
    ForecastPeriod,
    ForecastEntry,
    ForecastResult,
    ForecastGranularity,
    ScenarioType,
    CashAlert,
    AlertSeverity,
    AlertType,
    RecurringItem,
)
from app.modules.finance.cash_forecast.router import (
    router,
    get_cash_forecast_service,
)
from app.core.dependencies_v2 import get_saas_context


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def tenant_id() -> str:
    """ID de tenant pour les tests."""
    return "tenant-test-forecast-001"


@pytest.fixture
def mock_db():
    """Session de base de données mockée."""
    db = MagicMock()
    return db


@pytest.fixture
def service(mock_db, tenant_id):
    """Service de prévision pour les tests."""
    return CashForecastService(db=mock_db, tenant_id=tenant_id)


@pytest.fixture
def mock_service():
    """Service mocké pour les tests de router."""
    service = MagicMock(spec=CashForecastService)
    service.generate_forecast = AsyncMock(return_value=ForecastResult(
        success=True,
        tenant_id="test-tenant",
        current_balance=Decimal("50000.00"),
        forecasts=[
            ForecastPeriod(
                id="forecast-001",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
                scenario=ScenarioType.BASE,
                granularity=ForecastGranularity.DAILY,
                total_inflows=Decimal("15000.00"),
                total_outflows=Decimal("12000.00"),
                net_change=Decimal("3000.00"),
                min_balance=Decimal("45000.00"),
                max_balance=Decimal("55000.00"),
                avg_balance=Decimal("50000.00"),
                confidence=85.0,
                entries=[],
            ),
        ],
        alerts=[],
        summary={
            "period_days": 30,
            "health_status": "good",
        },
    ))
    service.get_cash_position = AsyncMock(return_value={
        "total_balance": "50000.00",
        "date": date.today().isoformat(),
        "accounts": [],
    })
    service.get_alert_summary = AsyncMock(return_value={
        "total_alerts": 0,
        "critical": 0,
        "warning": 0,
        "info": 0,
        "alerts": [],
    })
    service.simulate_transaction = AsyncMock(return_value=ForecastResult(
        success=True,
        tenant_id="test-tenant",
        current_balance=Decimal("50000.00"),
        forecasts=[],
        alerts=[],
        summary={},
    ))
    return service


@pytest.fixture
def mock_context():
    """Contexte SaaS mocké."""
    context = MagicMock()
    context.tenant_id = "test-tenant-forecast-123"
    context.user_id = uuid4()
    return context


@pytest.fixture
def app(mock_service, mock_context):
    """Application FastAPI de test."""
    test_app = FastAPI()
    test_app.include_router(router)

    async def override_service():
        return mock_service

    async def override_context():
        return mock_context

    test_app.dependency_overrides[get_cash_forecast_service] = override_service
    test_app.dependency_overrides[get_saas_context] = override_context
    return test_app


@pytest.fixture
def client(app):
    """Client de test."""
    return TestClient(app)


# =============================================================================
# TESTS SERVICE - INITIALISATION
# =============================================================================


class TestServiceInit:
    """Tests d'initialisation du service."""

    def test_init_with_tenant_id(self, mock_db, tenant_id):
        """Test initialisation avec tenant_id."""
        service = CashForecastService(db=mock_db, tenant_id=tenant_id)
        assert service.tenant_id == tenant_id
        assert service.db == mock_db

    def test_init_requires_tenant_id(self, mock_db):
        """Test que tenant_id est obligatoire."""
        with pytest.raises(ValueError, match="tenant_id est obligatoire"):
            CashForecastService(db=mock_db, tenant_id="")

    def test_init_with_custom_thresholds(self, mock_db, tenant_id):
        """Test initialisation avec seuils personnalisés."""
        service = CashForecastService(
            db=mock_db,
            tenant_id=tenant_id,
            low_balance_threshold=Decimal("10000"),
            critical_balance_threshold=Decimal("2000"),
        )
        assert service.low_balance_threshold == Decimal("10000")
        assert service.critical_balance_threshold == Decimal("2000")

    def test_default_thresholds(self, service):
        """Test seuils par défaut."""
        assert service.low_balance_threshold == Decimal("5000")
        assert service.critical_balance_threshold == Decimal("1000")


# =============================================================================
# TESTS SERVICE - GÉNÉRATION PRÉVISION
# =============================================================================


class TestForecastGeneration:
    """Tests de génération de prévision."""

    @pytest.mark.asyncio
    async def test_generate_forecast_success(self, service):
        """Test génération prévision réussie."""
        result = await service.generate_forecast(days=30)
        assert result.success is True
        assert result.tenant_id == service.tenant_id
        assert len(result.forecasts) == 1
        assert result.current_balance > 0

    @pytest.mark.asyncio
    async def test_generate_forecast_multiple_scenarios(self, service):
        """Test génération avec plusieurs scénarios."""
        result = await service.generate_forecast(
            days=30,
            scenarios=[ScenarioType.BASE, ScenarioType.PESSIMISTIC],
        )
        assert result.success is True
        assert len(result.forecasts) == 2

        scenarios = [f.scenario for f in result.forecasts]
        assert ScenarioType.BASE in scenarios
        assert ScenarioType.PESSIMISTIC in scenarios

    @pytest.mark.asyncio
    async def test_generate_forecast_respects_max_days(self, service):
        """Test que la limite de jours est respectée."""
        result = await service.generate_forecast(days=500)  # > MAX_DAYS
        assert result.success is True
        for forecast in result.forecasts:
            assert (forecast.end_date - forecast.start_date).days <= 365

    @pytest.mark.asyncio
    async def test_generate_forecast_granularity_daily(self, service):
        """Test prévision granularité journalière."""
        result = await service.generate_forecast(
            days=7,
            granularity=ForecastGranularity.DAILY,
        )
        assert result.success is True
        # Devrait avoir environ 7-8 entrées
        if result.forecasts:
            assert len(result.forecasts[0].entries) >= 7

    @pytest.mark.asyncio
    async def test_generate_forecast_granularity_weekly(self, service):
        """Test prévision granularité hebdomadaire."""
        result = await service.generate_forecast(
            days=28,
            granularity=ForecastGranularity.WEEKLY,
        )
        assert result.success is True
        if result.forecasts:
            # 28 jours = 4 semaines
            assert len(result.forecasts[0].entries) <= 5

    @pytest.mark.asyncio
    async def test_generate_forecast_granularity_monthly(self, service):
        """Test prévision granularité mensuelle."""
        result = await service.generate_forecast(
            days=90,
            granularity=ForecastGranularity.MONTHLY,
        )
        assert result.success is True
        if result.forecasts:
            # 90 jours = ~3 mois
            assert len(result.forecasts[0].entries) <= 4


# =============================================================================
# TESTS SERVICE - SCÉNARIOS
# =============================================================================


class TestScenarios:
    """Tests des scénarios de prévision."""

    def test_scenario_factors_defined(self, service):
        """Test que les facteurs de scénario sont définis."""
        assert ScenarioType.BASE in service.SCENARIO_FACTORS
        assert ScenarioType.OPTIMISTIC in service.SCENARIO_FACTORS
        assert ScenarioType.PESSIMISTIC in service.SCENARIO_FACTORS
        assert ScenarioType.STRESS in service.SCENARIO_FACTORS

    def test_base_scenario_neutral(self, service):
        """Test que le scénario base est neutre."""
        factors = service.SCENARIO_FACTORS[ScenarioType.BASE]
        assert factors["inflows"] == Decimal("1.0")
        assert factors["outflows"] == Decimal("1.0")

    def test_optimistic_scenario_factors(self, service):
        """Test facteurs scénario optimiste."""
        factors = service.SCENARIO_FACTORS[ScenarioType.OPTIMISTIC]
        assert factors["inflows"] > Decimal("1.0")  # Plus d'encaissements
        assert factors["outflows"] < Decimal("1.0")  # Moins de décaissements

    def test_pessimistic_scenario_factors(self, service):
        """Test facteurs scénario pessimiste."""
        factors = service.SCENARIO_FACTORS[ScenarioType.PESSIMISTIC]
        assert factors["inflows"] < Decimal("1.0")
        assert factors["outflows"] > Decimal("1.0")

    def test_stress_scenario_factors(self, service):
        """Test facteurs scénario stress."""
        factors = service.SCENARIO_FACTORS[ScenarioType.STRESS]
        assert factors["inflows"] < Decimal("0.7")  # Fort impact
        assert factors["outflows"] > Decimal("1.2")


# =============================================================================
# TESTS SERVICE - ALERTES
# =============================================================================


class TestAlerts:
    """Tests de génération d'alertes."""

    def test_generate_alerts_empty_forecasts(self, service):
        """Test alertes avec prévisions vides."""
        alerts = service._generate_alerts([])
        assert alerts == []

    def test_generate_alerts_low_balance(self, service):
        """Test alerte solde bas."""
        forecast = ForecastPeriod(
            id="test",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            min_balance=Decimal("3000"),  # Sous le seuil de 5000
            min_balance_date=date.today() + timedelta(days=15),
        )
        alerts = service._generate_alerts([forecast])
        assert len(alerts) > 0
        assert any(a.type == AlertType.LOW_BALANCE for a in alerts)

    def test_generate_alerts_critical_balance(self, service):
        """Test alerte solde critique."""
        forecast = ForecastPeriod(
            id="test",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            min_balance=Decimal("500"),  # Sous le seuil critique de 1000
            min_balance_date=date.today() + timedelta(days=10),
        )
        alerts = service._generate_alerts([forecast])
        assert len(alerts) > 0
        assert any(a.severity == AlertSeverity.CRITICAL for a in alerts)

    def test_generate_alerts_negative_balance(self, service):
        """Test alerte solde négatif."""
        forecast = ForecastPeriod(
            id="test",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            min_balance=Decimal("-1000"),
            min_balance_date=date.today() + timedelta(days=20),
            entries=[
                ForecastEntry(
                    date=date.today() + timedelta(days=20),
                    closing_balance=Decimal("-1000"),
                ),
            ],
        )
        alerts = service._generate_alerts([forecast])
        assert len(alerts) > 0
        assert any(a.type == AlertType.NEGATIVE_BALANCE for a in alerts)


# =============================================================================
# TESTS SERVICE - UTILITAIRES
# =============================================================================


class TestUtilities:
    """Tests des méthodes utilitaires."""

    def test_calculate_forecast_confidence_short_term(self, service):
        """Test calcul confiance court terme."""
        entries = [ForecastEntry(date=date.today(), confidence=90.0)]
        confidence = service._calculate_forecast_confidence(
            entries, days=7, scenario=ScenarioType.BASE
        )
        assert confidence > 80

    def test_calculate_forecast_confidence_long_term(self, service):
        """Test calcul confiance long terme (pénalité)."""
        entries = [ForecastEntry(date=date.today(), confidence=90.0)]
        confidence = service._calculate_forecast_confidence(
            entries, days=180, scenario=ScenarioType.BASE
        )
        assert confidence < 90  # Pénalité pour long terme

    def test_calculate_forecast_confidence_stress_scenario(self, service):
        """Test calcul confiance scénario stress."""
        entries = [ForecastEntry(date=date.today(), confidence=90.0)]
        confidence = service._calculate_forecast_confidence(
            entries, days=30, scenario=ScenarioType.STRESS
        )
        # Pénalité pour scénario stress
        base_confidence = service._calculate_forecast_confidence(
            entries, days=30, scenario=ScenarioType.BASE
        )
        assert confidence < base_confidence

    def test_build_summary(self, service):
        """Test construction du résumé."""
        forecasts = [
            ForecastPeriod(
                id="test",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
                scenario=ScenarioType.BASE,
                total_inflows=Decimal("10000"),
                total_outflows=Decimal("8000"),
                net_change=Decimal("2000"),
                min_balance=Decimal("45000"),
                max_balance=Decimal("55000"),
                avg_balance=Decimal("50000"),
                confidence=85.0,
            ),
        ]
        summary = service._build_summary(forecasts, [])

        assert "period_days" in summary
        assert "total_inflows" in summary
        assert "health_status" in summary
        assert summary["health_status"] == "good"

    def test_is_recurring_in_period_monthly(self, service):
        """Test récurrence mensuelle."""
        item = RecurringItem(
            id="test",
            name="Test",
            amount=Decimal("100"),
            frequency="monthly",
            next_date=date.today() + timedelta(days=15),
            is_inflow=False,
        )
        # Période qui inclut next_date
        assert service._is_recurring_in_period(
            item,
            date.today(),
            date.today() + timedelta(days=30),
        )

    def test_is_recurring_outside_period(self, service):
        """Test récurrence hors période."""
        item = RecurringItem(
            id="test",
            name="Test",
            amount=Decimal("100"),
            frequency="monthly",
            next_date=date.today() + timedelta(days=60),
            is_inflow=False,
        )
        # Période avant next_date
        assert not service._is_recurring_in_period(
            item,
            date.today(),
            date.today() + timedelta(days=30),
        )


# =============================================================================
# TESTS SERVICE - MÉTHODES PUBLIQUES
# =============================================================================


class TestPublicMethods:
    """Tests des méthodes publiques additionnelles."""

    @pytest.mark.asyncio
    async def test_get_cash_position(self, service):
        """Test récupération position de trésorerie."""
        result = await service.get_cash_position()
        assert "total_balance" in result
        assert "date" in result

    @pytest.mark.asyncio
    async def test_simulate_transaction_inflow(self, service):
        """Test simulation encaissement."""
        result = await service.simulate_transaction(
            amount=Decimal("5000"),
            transaction_date=date.today() + timedelta(days=10),
            is_inflow=True,
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_simulate_transaction_outflow(self, service):
        """Test simulation décaissement."""
        result = await service.simulate_transaction(
            amount=Decimal("3000"),
            transaction_date=date.today() + timedelta(days=15),
            is_inflow=False,
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_alert_summary(self, service):
        """Test récupération résumé alertes."""
        result = await service.get_alert_summary()
        assert "total_alerts" in result
        assert "critical" in result
        assert "warning" in result


# =============================================================================
# TESTS ROUTER
# =============================================================================


class TestRouter:
    """Tests des endpoints REST."""

    def test_get_forecast(self, client, mock_service):
        """Test endpoint forecast."""
        response = client.get("/v3/finance/cash-forecast/forecast")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "forecasts" in data
        assert "summary" in data

    def test_get_forecast_with_params(self, client, mock_service):
        """Test endpoint forecast avec paramètres."""
        response = client.get(
            "/v3/finance/cash-forecast/forecast",
            params={
                "days": 60,
                "scenarios": "base,pessimistic",
                "granularity": "weekly",
            },
        )

        assert response.status_code == 200

    def test_get_forecast_invalid_scenario(self, client, mock_service):
        """Test endpoint forecast scénario invalide."""
        response = client.get(
            "/v3/finance/cash-forecast/forecast",
            params={"scenarios": "invalid"},
        )

        assert response.status_code == 400
        assert "invalide" in response.json()["detail"].lower()

    def test_get_forecast_invalid_granularity(self, client, mock_service):
        """Test endpoint forecast granularité invalide."""
        response = client.get(
            "/v3/finance/cash-forecast/forecast",
            params={"granularity": "invalid"},
        )

        assert response.status_code == 400

    def test_get_cash_position(self, client, mock_service):
        """Test endpoint position."""
        response = client.get("/v3/finance/cash-forecast/position")

        assert response.status_code == 200
        data = response.json()
        assert "total_balance" in data
        assert "date" in data

    def test_simulate_transaction(self, client, mock_service):
        """Test endpoint simulation."""
        response = client.post(
            "/v3/finance/cash-forecast/simulate",
            json={
                "amount": "5000.00",
                "transaction_date": (date.today() + timedelta(days=10)).isoformat(),
                "is_inflow": True,
            },
        )

        assert response.status_code == 200

    def test_simulate_transaction_invalid_date(self, client, mock_service):
        """Test endpoint simulation date invalide."""
        response = client.post(
            "/v3/finance/cash-forecast/simulate",
            json={
                "amount": "5000.00",
                "transaction_date": "invalid-date",
                "is_inflow": True,
            },
        )

        assert response.status_code == 400

    def test_get_alerts(self, client, mock_service):
        """Test endpoint alertes."""
        response = client.get("/v3/finance/cash-forecast/alerts")

        assert response.status_code == 200
        data = response.json()
        assert "total_alerts" in data
        assert "critical" in data

    def test_get_scenarios(self, client):
        """Test endpoint scénarios."""
        response = client.get("/v3/finance/cash-forecast/scenarios")

        assert response.status_code == 200
        data = response.json()
        assert "scenarios" in data
        assert len(data["scenarios"]) >= 4
        assert data["default"] == "base"

    def test_health_check(self, client):
        """Test health check."""
        response = client.get("/v3/finance/cash-forecast/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "finance-cash-forecast"
        assert "features" in data


# =============================================================================
# TESTS ENUMS
# =============================================================================


class TestEnums:
    """Tests des enums."""

    def test_scenario_types(self):
        """Test types de scénarios."""
        assert ScenarioType.BASE.value == "base"
        assert ScenarioType.OPTIMISTIC.value == "optimistic"
        assert ScenarioType.PESSIMISTIC.value == "pessimistic"
        assert ScenarioType.STRESS.value == "stress"

    def test_granularity_types(self):
        """Test types de granularité."""
        assert ForecastGranularity.DAILY.value == "daily"
        assert ForecastGranularity.WEEKLY.value == "weekly"
        assert ForecastGranularity.MONTHLY.value == "monthly"

    def test_alert_severity(self):
        """Test sévérité des alertes."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_alert_types(self):
        """Test types d'alertes."""
        assert AlertType.LOW_BALANCE.value == "low_balance"
        assert AlertType.NEGATIVE_BALANCE.value == "negative_balance"


# =============================================================================
# TESTS DATA CLASSES
# =============================================================================


class TestDataClasses:
    """Tests des classes de données."""

    def test_forecast_entry_creation(self):
        """Test création ForecastEntry."""
        entry = ForecastEntry(
            date=date.today(),
            opening_balance=Decimal("10000"),
            closing_balance=Decimal("12000"),
            total_inflows=Decimal("3000"),
            total_outflows=Decimal("1000"),
            net_change=Decimal("2000"),
            confidence=90.0,
        )
        assert entry.date == date.today()
        assert entry.net_change == Decimal("2000")

    def test_forecast_period_creation(self):
        """Test création ForecastPeriod."""
        period = ForecastPeriod(
            id="test-001",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            scenario=ScenarioType.BASE,
        )
        assert period.id == "test-001"
        assert period.scenario == ScenarioType.BASE

    def test_cash_alert_creation(self):
        """Test création CashAlert."""
        alert = CashAlert(
            id="alert-001",
            type=AlertType.LOW_BALANCE,
            severity=AlertSeverity.WARNING,
            date=date.today(),
            message="Solde bas",
            amount=Decimal("3000"),
            threshold=Decimal("5000"),
        )
        assert alert.type == AlertType.LOW_BALANCE
        assert alert.severity == AlertSeverity.WARNING

    def test_recurring_item_creation(self):
        """Test création RecurringItem."""
        item = RecurringItem(
            id="rec-001",
            name="Loyer",
            amount=Decimal("2000"),
            frequency="monthly",
            next_date=date.today(),
            is_inflow=False,
        )
        assert item.name == "Loyer"
        assert item.is_inflow is False
