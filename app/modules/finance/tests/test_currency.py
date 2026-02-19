"""
Tests pour le module Gestion des Devises.
==========================================

Tests unitaires et d'intégration pour CurrencyService et Router.
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.finance.currency.service import (
    CurrencyService,
    ExchangeRate,
    CurrencyConversion,
    ConversionResult,
    RateSource,
    SupportedCurrencies,
    DefaultRates,
)
from app.modules.finance.currency.router import (
    router,
    get_currency_service,
)
from app.core.dependencies_v2 import get_saas_context


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def tenant_id() -> str:
    """ID de tenant pour les tests."""
    return "tenant-test-currency-001"


@pytest.fixture
def mock_db():
    """Session de base de données mockée."""
    return MagicMock()


@pytest.fixture
def service(mock_db, tenant_id):
    """Service de devises pour les tests."""
    return CurrencyService(db=mock_db, tenant_id=tenant_id)


@pytest.fixture
def mock_service():
    """Service mocké pour les tests de router."""
    service = MagicMock(spec=CurrencyService)
    service.get_rate = AsyncMock(return_value=ExchangeRate(
        id="rate-001",
        base_currency="EUR",
        target_currency="USD",
        rate=Decimal("1.0850"),
        inverse_rate=Decimal("0.9217"),
        date=date.today(),
        source=RateSource.FALLBACK,
    ))
    service.get_rates_for_date = AsyncMock(return_value=[
        ExchangeRate(
            id="rate-001",
            base_currency="EUR",
            target_currency="USD",
            rate=Decimal("1.0850"),
            inverse_rate=Decimal("0.9217"),
            date=date.today(),
            source=RateSource.FALLBACK,
        ),
    ])
    service.convert = AsyncMock(return_value=ConversionResult(
        success=True,
        conversion=CurrencyConversion(
            id="conv-001",
            source_amount=Decimal("100.00"),
            source_currency="EUR",
            target_amount=Decimal("108.50"),
            target_currency="USD",
            rate_used=Decimal("1.0850"),
            rate_date=date.today(),
            rate_source=RateSource.FALLBACK,
        ),
    ))
    service.convert_batch = AsyncMock(return_value=[
        ConversionResult(
            success=True,
            conversion=CurrencyConversion(
                id="conv-001",
                source_amount=Decimal("100.00"),
                source_currency="EUR",
                target_amount=Decimal("108.50"),
                target_currency="USD",
                rate_used=Decimal("1.0850"),
                rate_date=date.today(),
                rate_source=RateSource.FALLBACK,
            ),
        ),
    ])
    service.set_manual_rate = AsyncMock(return_value=ExchangeRate(
        id="rate-manual",
        base_currency="EUR",
        target_currency="USD",
        rate=Decimal("1.1000"),
        inverse_rate=Decimal("0.9091"),
        date=date.today(),
        source=RateSource.MANUAL,
    ))
    service.get_supported_currencies = MagicMock(return_value=[
        {"code": "EUR", "name": "Euro", "symbol": "€", "decimals": 2},
        {"code": "USD", "name": "Dollar américain", "symbol": "$", "decimals": 2},
    ])
    service.get_currency_info = MagicMock(return_value={
        "code": "EUR",
        "name": "Euro",
        "symbol": "€",
        "decimals": 2,
    })
    service.format_amount = MagicMock(return_value="€100.00")
    return service


@pytest.fixture
def mock_context():
    """Contexte SaaS mocké."""
    context = MagicMock()
    context.tenant_id = "test-tenant-currency-123"
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

    test_app.dependency_overrides[get_currency_service] = override_service
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
        service = CurrencyService(db=mock_db, tenant_id=tenant_id)
        assert service.tenant_id == tenant_id
        assert service.db == mock_db

    def test_init_requires_tenant_id(self, mock_db):
        """Test que tenant_id est obligatoire."""
        with pytest.raises(ValueError, match="tenant_id est obligatoire"):
            CurrencyService(db=mock_db, tenant_id="")

    def test_default_base_currency(self, service):
        """Test devise de base par défaut."""
        assert service.base_currency == "EUR"

    def test_custom_base_currency(self, mock_db, tenant_id):
        """Test devise de base personnalisée."""
        service = CurrencyService(db=mock_db, tenant_id=tenant_id, base_currency="USD")
        assert service.base_currency == "USD"


# =============================================================================
# TESTS SERVICE - TAUX DE CHANGE
# =============================================================================


class TestExchangeRates:
    """Tests des taux de change."""

    @pytest.mark.asyncio
    async def test_get_rate_same_currency(self, service):
        """Test taux pour même devise."""
        rate = await service.get_rate("EUR", "EUR")
        assert rate is not None
        assert rate.rate == Decimal("1")
        assert rate.base_currency == "EUR"
        assert rate.target_currency == "EUR"

    @pytest.mark.asyncio
    async def test_get_rate_eur_usd(self, service):
        """Test taux EUR/USD."""
        rate = await service.get_rate("EUR", "USD")
        assert rate is not None
        assert rate.base_currency == "EUR"
        assert rate.target_currency == "USD"
        assert rate.rate > 0

    @pytest.mark.asyncio
    async def test_get_rate_usd_eur(self, service):
        """Test taux USD/EUR (inverse)."""
        rate = await service.get_rate("USD", "EUR")
        assert rate is not None
        assert rate.rate > 0
        assert rate.rate < 1  # USD < EUR

    @pytest.mark.asyncio
    async def test_get_rate_cross_rate(self, service):
        """Test cross rate (ex: USD/GBP via EUR)."""
        rate = await service.get_rate("USD", "GBP")
        assert rate is not None
        assert rate.rate > 0

    @pytest.mark.asyncio
    async def test_get_rate_fallback_source(self, service):
        """Test que la source est fallback."""
        rate = await service.get_rate("EUR", "USD")
        assert rate.source == RateSource.FALLBACK

    @pytest.mark.asyncio
    async def test_get_rates_for_date(self, service):
        """Test récupération tous les taux."""
        rates = await service.get_rates_for_date(date.today())
        assert len(rates) > 0
        assert all(r.base_currency == "EUR" for r in rates)


# =============================================================================
# TESTS SERVICE - CONVERSION
# =============================================================================


class TestConversion:
    """Tests de conversion."""

    @pytest.mark.asyncio
    async def test_convert_eur_to_usd(self, service):
        """Test conversion EUR vers USD."""
        result = await service.convert(
            amount=Decimal("100"),
            from_currency="EUR",
            to_currency="USD",
        )
        assert result.success is True
        assert result.conversion is not None
        assert result.conversion.source_amount == Decimal("100")
        assert result.conversion.source_currency == "EUR"
        assert result.conversion.target_currency == "USD"
        assert result.conversion.target_amount > Decimal("100")

    @pytest.mark.asyncio
    async def test_convert_usd_to_eur(self, service):
        """Test conversion USD vers EUR."""
        result = await service.convert(
            amount=Decimal("100"),
            from_currency="USD",
            to_currency="EUR",
        )
        assert result.success is True
        assert result.conversion.target_amount < Decimal("100")

    @pytest.mark.asyncio
    async def test_convert_same_currency(self, service):
        """Test conversion même devise."""
        result = await service.convert(
            amount=Decimal("100"),
            from_currency="EUR",
            to_currency="EUR",
        )
        assert result.success is True
        assert result.conversion.target_amount == Decimal("100")

    @pytest.mark.asyncio
    async def test_convert_unsupported_currency(self, service):
        """Test conversion devise non supportée."""
        result = await service.convert(
            amount=Decimal("100"),
            from_currency="XXX",
            to_currency="EUR",
        )
        assert result.success is False
        assert "non supportée" in result.error

    @pytest.mark.asyncio
    async def test_convert_batch(self, service):
        """Test conversion par lot."""
        conversions = [
            {"amount": "100", "from_currency": "EUR", "to_currency": "USD"},
            {"amount": "200", "from_currency": "EUR", "to_currency": "GBP"},
        ]
        results = await service.convert_batch(conversions)
        assert len(results) == 2
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_convert_respects_decimals(self, service):
        """Test que les décimales sont respectées."""
        result = await service.convert(
            amount=Decimal("100"),
            from_currency="EUR",
            to_currency="JPY",  # 0 décimales
        )
        assert result.success is True
        # JPY n'a pas de décimales
        assert result.conversion.target_amount == result.conversion.target_amount.quantize(Decimal("1"))


# =============================================================================
# TESTS SERVICE - TAUX MANUELS
# =============================================================================


class TestManualRates:
    """Tests des taux manuels."""

    @pytest.mark.asyncio
    async def test_set_manual_rate(self, service):
        """Test définition taux manuel."""
        rate = await service.set_manual_rate(
            from_currency="EUR",
            to_currency="USD",
            rate=Decimal("1.1000"),
        )
        assert rate is not None
        assert rate.rate == Decimal("1.1000")
        assert rate.source == RateSource.MANUAL

    @pytest.mark.asyncio
    async def test_manual_rate_has_inverse(self, service):
        """Test que le taux inverse est calculé."""
        rate = await service.set_manual_rate(
            from_currency="EUR",
            to_currency="USD",
            rate=Decimal("1.1000"),
        )
        expected_inverse = (Decimal("1") / Decimal("1.1000")).quantize(Decimal("0.000001"))
        assert rate.inverse_rate == expected_inverse


# =============================================================================
# TESTS SERVICE - DEVISES SUPPORTÉES
# =============================================================================


class TestSupportedCurrencies:
    """Tests des devises supportées."""

    def test_eur_supported(self):
        """Test EUR supporté."""
        assert SupportedCurrencies.is_supported("EUR")
        assert SupportedCurrencies.is_supported("eur")

    def test_usd_supported(self):
        """Test USD supporté."""
        assert SupportedCurrencies.is_supported("USD")

    def test_xxx_not_supported(self):
        """Test devise inexistante."""
        assert not SupportedCurrencies.is_supported("XXX")

    def test_get_info(self):
        """Test récupération info devise."""
        info = SupportedCurrencies.get_info("EUR")
        assert info is not None
        assert info["name"] == "Euro"
        assert info["symbol"] == "€"
        assert info["decimals"] == 2

    def test_get_decimals(self):
        """Test récupération décimales."""
        assert SupportedCurrencies.get_decimals("EUR") == 2
        assert SupportedCurrencies.get_decimals("JPY") == 0

    def test_list_currencies(self, service):
        """Test listing devises."""
        currencies = service.get_supported_currencies()
        assert len(currencies) > 0
        assert any(c["code"] == "EUR" for c in currencies)


# =============================================================================
# TESTS SERVICE - FORMATAGE
# =============================================================================


class TestFormatting:
    """Tests de formatage."""

    def test_format_amount_eur(self, service):
        """Test formatage montant EUR."""
        formatted = service.format_amount(Decimal("1234.56"), "EUR")
        assert "€" in formatted
        assert "1234" in formatted

    def test_format_amount_no_symbol(self, service):
        """Test formatage sans symbole."""
        formatted = service.format_amount(Decimal("1234.56"), "EUR", include_symbol=False)
        assert "€" not in formatted
        assert "1234.56" in formatted

    def test_format_amount_jpy_no_decimals(self, service):
        """Test formatage JPY (0 décimales)."""
        formatted = service.format_amount(Decimal("1234"), "JPY")
        assert "." not in formatted or formatted.endswith(".0") is False


# =============================================================================
# TESTS SERVICE - DEFAULT RATES
# =============================================================================


class TestDefaultRates:
    """Tests des taux par défaut."""

    def test_eur_rates_defined(self):
        """Test que les taux EUR sont définis."""
        assert "USD" in DefaultRates.EUR_RATES
        assert "GBP" in DefaultRates.EUR_RATES
        assert "CHF" in DefaultRates.EUR_RATES

    def test_eur_usd_rate_reasonable(self):
        """Test que le taux EUR/USD est raisonnable."""
        rate = DefaultRates.EUR_RATES["USD"]
        assert Decimal("0.8") < rate < Decimal("1.5")

    def test_fixed_rates_correct(self):
        """Test des taux fixes (CFA)."""
        # XOF et XAF ont un taux fixe de 655.957
        assert DefaultRates.EUR_RATES["XOF"] == Decimal("655.957")
        assert DefaultRates.EUR_RATES["XAF"] == Decimal("655.957")


# =============================================================================
# TESTS ROUTER
# =============================================================================


class TestRouter:
    """Tests des endpoints REST."""

    def test_get_rate(self, client, mock_service):
        """Test endpoint taux de change."""
        response = client.get(
            "/v3/finance/currency/rate",
            params={"from_currency": "EUR", "to_currency": "USD"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["base_currency"] == "EUR"
        assert data["target_currency"] == "USD"
        assert "rate" in data

    def test_get_rate_with_date(self, client, mock_service):
        """Test endpoint taux avec date."""
        response = client.get(
            "/v3/finance/currency/rate",
            params={
                "from_currency": "EUR",
                "to_currency": "USD",
                "rate_date": "2024-01-15",
            },
        )

        assert response.status_code == 200

    def test_get_rate_invalid_date(self, client, mock_service):
        """Test endpoint taux date invalide."""
        response = client.get(
            "/v3/finance/currency/rate",
            params={
                "from_currency": "EUR",
                "to_currency": "USD",
                "rate_date": "invalid",
            },
        )

        assert response.status_code == 400

    def test_get_rates(self, client, mock_service):
        """Test endpoint tous les taux."""
        response = client.get("/v3/finance/currency/rates")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_convert(self, client, mock_service):
        """Test endpoint conversion."""
        response = client.post(
            "/v3/finance/currency/convert",
            json={
                "amount": "100.00",
                "from_currency": "EUR",
                "to_currency": "USD",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "target_amount" in data

    def test_convert_batch(self, client, mock_service):
        """Test endpoint conversion lot."""
        response = client.post(
            "/v3/finance/currency/convert-batch",
            json={
                "conversions": [
                    {"amount": "100", "from_currency": "EUR", "to_currency": "USD"},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_set_manual_rate(self, client, mock_service):
        """Test endpoint taux manuel."""
        response = client.post(
            "/v3/finance/currency/rate",
            json={
                "from_currency": "EUR",
                "to_currency": "USD",
                "rate": "1.1000",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["source"] == "manual"

    def test_list_currencies(self, client, mock_service):
        """Test endpoint liste devises."""
        response = client.get("/v3/finance/currency/currencies")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "currencies" in data

    def test_get_currency_info(self, client, mock_service):
        """Test endpoint info devise."""
        response = client.get("/v3/finance/currency/currency/EUR")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "EUR"
        assert "name" in data
        assert "symbol" in data

    def test_get_currency_info_not_found(self, client, mock_service):
        """Test endpoint devise non trouvée."""
        mock_service.get_currency_info.return_value = None

        response = client.get("/v3/finance/currency/currency/XXX")

        assert response.status_code == 404

    def test_format_amount(self, client, mock_service):
        """Test endpoint formatage."""
        response = client.get(
            "/v3/finance/currency/format",
            params={"amount": "100.00", "currency": "EUR"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "formatted" in data

    def test_health_check(self, client):
        """Test health check."""
        response = client.get("/v3/finance/currency/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "finance-currency"


# =============================================================================
# TESTS ENUMS
# =============================================================================


class TestEnums:
    """Tests des enums."""

    def test_rate_sources(self):
        """Test sources de taux."""
        assert RateSource.ECB.value == "ecb"
        assert RateSource.MANUAL.value == "manual"
        assert RateSource.CACHE.value == "cache"
        assert RateSource.FALLBACK.value == "fallback"


# =============================================================================
# TESTS DATA CLASSES
# =============================================================================


class TestDataClasses:
    """Tests des classes de données."""

    def test_exchange_rate_creation(self):
        """Test création ExchangeRate."""
        rate = ExchangeRate(
            id="rate-001",
            base_currency="EUR",
            target_currency="USD",
            rate=Decimal("1.0850"),
            inverse_rate=Decimal("0.9217"),
            date=date.today(),
        )
        assert rate.base_currency == "EUR"
        assert rate.rate == Decimal("1.0850")

    def test_currency_conversion_creation(self):
        """Test création CurrencyConversion."""
        conv = CurrencyConversion(
            id="conv-001",
            source_amount=Decimal("100"),
            source_currency="EUR",
            target_amount=Decimal("108.50"),
            target_currency="USD",
            rate_used=Decimal("1.0850"),
            rate_date=date.today(),
            rate_source=RateSource.FALLBACK,
        )
        assert conv.source_amount == Decimal("100")
        assert conv.target_amount == Decimal("108.50")

    def test_conversion_result_success(self):
        """Test ConversionResult succès."""
        result = ConversionResult(
            success=True,
            conversion=CurrencyConversion(
                id="conv-001",
                source_amount=Decimal("100"),
                source_currency="EUR",
                target_amount=Decimal("108.50"),
                target_currency="USD",
                rate_used=Decimal("1.0850"),
                rate_date=date.today(),
                rate_source=RateSource.FALLBACK,
            ),
        )
        assert result.success is True
        assert result.conversion is not None

    def test_conversion_result_failure(self):
        """Test ConversionResult échec."""
        result = ConversionResult(
            success=False,
            error="Devise non supportée",
        )
        assert result.success is False
        assert result.error is not None
