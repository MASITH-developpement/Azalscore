"""
Tests pour le router API Currency.
"""

import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.modules.currency.router import router, get_currency_service
from app.modules.currency.service import CurrencyService
from app.modules.currency.models import (
    Currency, ExchangeRate, CurrencyConfig,
    RateSource, RateType, CurrencyStatus
)
from app.modules.currency.schemas import ConversionResult, ConversionMethod


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_current_user():
    """Mock utilisateur courant."""
    user = Mock()
    user.id = uuid4()
    user.tenant_id = uuid4()
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_service():
    """Mock du service Currency."""
    service = Mock(spec=CurrencyService)
    service.tenant_id = str(uuid4())
    return service


@pytest.fixture
def app(mock_service, mock_current_user):
    """Application FastAPI de test."""
    app = FastAPI()
    app.include_router(router)

    # Override des dependencies
    def override_get_current_user():
        return mock_current_user

    def override_get_currency_service():
        return mock_service

    def override_require_permission(permission):
        return None

    from app.core.dependencies import get_current_user
    from app.core.dependencies_v2 import require_permission

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_currency_service] = override_get_currency_service
    app.dependency_overrides[require_permission] = lambda p: override_require_permission

    return app


@pytest.fixture
def client(app):
    """Client de test."""
    return TestClient(app)


# ============================================================================
# TESTS CURRENCIES ENDPOINTS
# ============================================================================

class TestCurrenciesEndpoints:
    """Tests des endpoints devises."""

    def test_list_currencies(self, client, mock_service):
        """GET /currencies."""
        mock_currencies = [
            Mock(
                id=uuid4(),
                code="EUR",
                name="Euro",
                symbol="\u20ac",
                decimals=2,
                is_enabled=True,
                is_default=True,
                is_reporting=True,
                is_major=True,
                status=CurrencyStatus.ACTIVE.value
            ),
            Mock(
                id=uuid4(),
                code="USD",
                name="Dollar",
                symbol="$",
                decimals=2,
                is_enabled=True,
                is_default=False,
                is_reporting=False,
                is_major=True,
                status=CurrencyStatus.ACTIVE.value
            )
        ]

        mock_service.currency_repo.list.return_value = (mock_currencies, 2)

        response = client.get("/currencies")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_get_currency(self, client, mock_service):
        """GET /currencies/{code}."""
        mock_currency = Mock(spec=Currency)
        mock_currency.id = uuid4()
        mock_currency.tenant_id = str(uuid4())
        mock_currency.code = "EUR"
        mock_currency.name = "Euro"
        mock_currency.symbol = "\u20ac"
        mock_currency.decimals = 2
        mock_currency.is_enabled = True
        mock_currency.is_default = True
        mock_currency.is_reporting = True
        mock_currency.status = CurrencyStatus.ACTIVE.value

        mock_service.get_currency.return_value = mock_currency

        response = client.get("/currencies/EUR")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "EUR"

    def test_get_currency_not_found(self, client, mock_service):
        """GET /currencies/{code} - non trouve."""
        from app.modules.currency.exceptions import CurrencyNotFoundError

        mock_service.get_currency.side_effect = CurrencyNotFoundError("XYZ")

        response = client.get("/currencies/XYZ")

        assert response.status_code == 404

    def test_create_currency(self, client, mock_service, mock_current_user):
        """POST /currencies."""
        mock_currency = Mock(spec=Currency)
        mock_currency.id = uuid4()
        mock_currency.tenant_id = str(mock_current_user.tenant_id)
        mock_currency.code = "CHF"
        mock_currency.name = "Franc suisse"
        mock_currency.symbol = "CHF"
        mock_currency.decimals = 2

        mock_service.create_currency.return_value = mock_currency

        response = client.post("/currencies", json={
            "code": "CHF",
            "name": "Franc suisse",
            "symbol": "CHF",
            "decimals": 2
        })

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "CHF"

    def test_create_currency_duplicate(self, client, mock_service):
        """POST /currencies - devise existante."""
        from app.modules.currency.exceptions import CurrencyAlreadyExistsError

        mock_service.create_currency.side_effect = CurrencyAlreadyExistsError("EUR")

        response = client.post("/currencies", json={
            "code": "EUR",
            "name": "Euro",
            "symbol": "\u20ac",
            "decimals": 2
        })

        assert response.status_code == 409

    def test_enable_currency(self, client, mock_service):
        """POST /currencies/{code}/enable."""
        mock_currency = Mock(spec=Currency)
        mock_currency.code = "GBP"
        mock_currency.is_enabled = True

        mock_service.enable_currency.return_value = mock_currency

        response = client.post("/currencies/GBP/enable")

        assert response.status_code == 200

    def test_disable_currency(self, client, mock_service):
        """POST /currencies/{code}/disable."""
        mock_currency = Mock(spec=Currency)
        mock_currency.code = "GBP"
        mock_currency.is_enabled = False

        mock_service.disable_currency.return_value = mock_currency

        response = client.post("/currencies/GBP/disable")

        assert response.status_code == 200


# ============================================================================
# TESTS RATES ENDPOINTS
# ============================================================================

class TestRatesEndpoints:
    """Tests des endpoints taux de change."""

    def test_list_rates(self, client, mock_service):
        """GET /currencies/rates."""
        mock_rates = [
            Mock(
                id=uuid4(),
                base_currency_code="EUR",
                quote_currency_code="USD",
                rate=Decimal("1.0850"),
                rate_date=date.today(),
                rate_type=RateType.SPOT.value,
                source=RateSource.ECB.value,
                is_manual=False
            )
        ]

        mock_service.rate_repo.list.return_value = (mock_rates, 1)

        response = client.get("/currencies/rates")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_rate(self, client, mock_service):
        """GET /currencies/rates/{base}/{quote}."""
        mock_rate = Mock(spec=ExchangeRate)
        mock_rate.id = uuid4()
        mock_rate.tenant_id = str(uuid4())
        mock_rate.base_currency_code = "EUR"
        mock_rate.quote_currency_code = "USD"
        mock_rate.base_currency_id = uuid4()
        mock_rate.quote_currency_id = uuid4()
        mock_rate.rate = Decimal("1.0850")
        mock_rate.inverse_rate = Decimal("0.9217")
        mock_rate.rate_date = date.today()
        mock_rate.rate_type = RateType.SPOT.value
        mock_rate.source = RateSource.ECB.value
        mock_rate.is_manual = False
        mock_rate.is_official = True
        mock_rate.is_interpolated = False
        mock_rate.is_locked = False
        mock_rate.version = 1
        mock_rate.created_at = date.today()

        mock_service.get_rate.return_value = mock_rate

        response = client.get("/currencies/rates/EUR/USD")

        assert response.status_code == 200
        data = response.json()
        assert data["base_currency_code"] == "EUR"
        assert data["quote_currency_code"] == "USD"

    def test_get_rate_not_found(self, client, mock_service):
        """GET /currencies/rates/{base}/{quote} - non trouve."""
        mock_service.get_rate.return_value = None

        response = client.get("/currencies/rates/EUR/XYZ")

        assert response.status_code == 404

    def test_create_rate(self, client, mock_service, mock_current_user):
        """POST /currencies/rates."""
        mock_rate = Mock(spec=ExchangeRate)
        mock_rate.id = uuid4()
        mock_rate.base_currency_code = "EUR"
        mock_rate.quote_currency_code = "GBP"
        mock_rate.rate = Decimal("0.8550")

        mock_service.set_rate.return_value = mock_rate

        response = client.post("/currencies/rates", json={
            "base_currency_code": "EUR",
            "quote_currency_code": "GBP",
            "rate": "0.8550",
            "rate_date": str(date.today()),
            "rate_type": "spot",
            "source": "manual"
        })

        assert response.status_code == 201

    def test_get_rate_history(self, client, mock_service):
        """GET /currencies/rates/{base}/{quote}/history."""
        mock_history = [
            Mock(
                rate_date=date.today(),
                rate=Decimal("1.0850"),
                rate_type=RateType.SPOT,
                source=RateSource.ECB,
                variation_percent=Decimal("0.50")
            )
        ]

        mock_service.get_rate_history.return_value = mock_history

        response = client.get(
            f"/currencies/rates/EUR/USD/history?start_date={date.today()}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["base_currency"] == "EUR"
        assert data["quote_currency"] == "USD"


# ============================================================================
# TESTS CONVERSION ENDPOINTS
# ============================================================================

class TestConversionEndpoints:
    """Tests des endpoints de conversion."""

    def test_convert(self, client, mock_service):
        """POST /currencies/convert."""
        mock_result = ConversionResult(
            original_amount=Decimal("100"),
            original_currency="EUR",
            converted_amount=Decimal("108.50"),
            target_currency="USD",
            exchange_rate=Decimal("1.0850"),
            inverse_rate=Decimal("0.9217"),
            rate_date=date.today(),
            rate_source=RateSource.ECB,
            rate_type=RateType.SPOT,
            conversion_method=ConversionMethod.DIRECT
        )

        mock_service.convert.return_value = mock_result

        response = client.post("/currencies/convert", json={
            "amount": "100",
            "from_currency": "EUR",
            "to_currency": "USD"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["original_amount"] == "100"
        assert data["converted_amount"] == "108.50"

    def test_convert_same_currency(self, client, mock_service):
        """POST /currencies/convert - meme devise."""
        mock_result = ConversionResult(
            original_amount=Decimal("100"),
            original_currency="EUR",
            converted_amount=Decimal("100"),
            target_currency="EUR",
            exchange_rate=Decimal("1"),
            inverse_rate=Decimal("1"),
            rate_date=date.today(),
            rate_source=RateSource.MANUAL,
            rate_type=RateType.SPOT,
            conversion_method=ConversionMethod.DIRECT
        )

        mock_service.convert.return_value = mock_result

        response = client.post("/currencies/convert", json={
            "amount": "100",
            "from_currency": "EUR",
            "to_currency": "EUR"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["exchange_rate"] == "1"

    def test_convert_rate_not_found(self, client, mock_service):
        """POST /currencies/convert - taux non trouve."""
        from app.modules.currency.exceptions import ExchangeRateNotFoundError

        mock_service.convert.side_effect = ExchangeRateNotFoundError("EUR", "XYZ")

        response = client.post("/currencies/convert", json={
            "amount": "100",
            "from_currency": "EUR",
            "to_currency": "XYZ"
        })

        assert response.status_code == 404


# ============================================================================
# TESTS CONFIG ENDPOINTS
# ============================================================================

class TestConfigEndpoints:
    """Tests des endpoints de configuration."""

    def test_get_config(self, client, mock_service):
        """GET /currencies/config."""
        mock_config = Mock(spec=CurrencyConfig)
        mock_config.id = uuid4()
        mock_config.tenant_id = str(uuid4())
        mock_config.default_currency_code = "EUR"
        mock_config.reporting_currency_code = "EUR"
        mock_config.primary_rate_source = RateSource.ECB.value
        mock_config.auto_update_rates = True
        mock_config.update_frequency_hours = 24
        mock_config.conversion_method = ConversionMethod.DIRECT.value
        mock_config.pivot_currency_code = "EUR"
        mock_config.allow_triangulation = True
        mock_config.rounding_method = "ROUND_HALF_UP"
        mock_config.rounding_precision = 2
        mock_config.track_exchange_gains = True
        mock_config.allow_manual_rates = True
        mock_config.require_rate_approval = False
        mock_config.rate_tolerance_percent = Decimal("5.00")
        mock_config.notify_rate_changes = True
        mock_config.notification_threshold_percent = Decimal("2.00")
        mock_config.version = 1
        mock_config.created_at = date.today()

        mock_service.get_config.return_value = mock_config

        response = client.get("/currencies/config")

        assert response.status_code == 200
        data = response.json()
        assert data["default_currency_code"] == "EUR"

    def test_update_config(self, client, mock_service, mock_current_user):
        """PUT /currencies/config."""
        mock_config = Mock(spec=CurrencyConfig)
        mock_config.default_currency_code = "USD"

        mock_service.update_config.return_value = mock_config

        response = client.put("/currencies/config", json={
            "default_currency_code": "USD"
        })

        assert response.status_code == 200


# ============================================================================
# TESTS GAINS/LOSSES ENDPOINTS
# ============================================================================

class TestGainsLossesEndpoints:
    """Tests des endpoints gains/pertes."""

    def test_list_gains_losses(self, client, mock_service):
        """GET /currencies/gains-losses."""
        mock_entries = []
        mock_service.gain_loss_repo.list.return_value = (mock_entries, 0)

        response = client.get("/currencies/gains-losses")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_get_gains_losses_summary(self, client, mock_service):
        """GET /currencies/gains-losses/summary."""
        from app.modules.currency.schemas import ExchangeGainLossSummary

        mock_summary = ExchangeGainLossSummary(
            period_start=date.today(),
            period_end=date.today(),
            currency="EUR",
            realized_gains=Decimal("100"),
            realized_losses=Decimal("-50"),
            realized_net=Decimal("50"),
            unrealized_gains=Decimal("30"),
            unrealized_losses=Decimal("-20"),
            unrealized_net=Decimal("10"),
            total_net=Decimal("60"),
            entry_count=5
        )

        mock_service.get_gain_loss_summary.return_value = mock_summary

        response = client.get(
            f"/currencies/gains-losses/summary?start_date={date.today()}&end_date={date.today()}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_net"] == "60"


# ============================================================================
# TESTS ALERTS ENDPOINTS
# ============================================================================

class TestAlertsEndpoints:
    """Tests des endpoints alertes."""

    def test_list_alerts(self, client, mock_service):
        """GET /currencies/alerts."""
        mock_alerts = []
        mock_service.alert_repo.list_unacknowledged.return_value = mock_alerts

        response = client.get("/currencies/alerts")

        assert response.status_code == 200

    def test_mark_alert_read(self, client, mock_service):
        """POST /currencies/alerts/{id}/read."""
        mock_alert = Mock()
        mock_alert.id = uuid4()
        mock_alert.is_read = False

        mock_service.alert_repo.get_by_id.return_value = mock_alert
        mock_service.alert_repo.mark_read.return_value = mock_alert

        response = client.post(f"/currencies/alerts/{mock_alert.id}/read")

        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
