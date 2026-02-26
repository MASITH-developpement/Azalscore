"""
Tests unitaires pour le service Currency.
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock

from sqlalchemy.orm import Session

from app.modules.currency.service import (
    CurrencyService, create_currency_service,
    ISO_4217_CURRENCIES, MAJOR_CURRENCIES
)
from app.modules.currency.models import (
    Currency, ExchangeRate, CurrencyConfig,
    RateSource, RateType, ConversionMethod, GainLossType
)
from app.modules.currency.exceptions import (
    CurrencyNotFoundError, CurrencyAlreadyExistsError,
    ExchangeRateNotFoundError, InvalidExchangeRateError,
    SameCurrencyConversionError, RateToleranceExceededError
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock de la session DB."""
    db = Mock(spec=Session)
    db.query.return_value.filter.return_value = Mock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


@pytest.fixture
def tenant_id():
    """Tenant ID de test."""
    return str(uuid4())


@pytest.fixture
def service(mock_db, tenant_id):
    """Service Currency pour les tests."""
    # Creer le service avec des mocks
    svc = CurrencyService(db=mock_db, tenant_id=tenant_id)
    return svc


@pytest.fixture
def mock_currency():
    """Devise mock."""
    currency = Mock(spec=Currency)
    currency.id = uuid4()
    currency.tenant_id = str(uuid4())
    currency.code = "EUR"
    currency.name = "Euro"
    currency.symbol = "\u20ac"
    currency.decimals = 2
    currency.is_enabled = True
    currency.is_default = True
    currency.is_reporting = True
    currency.status = "active"
    return currency


@pytest.fixture
def mock_rate():
    """Taux de change mock."""
    rate = Mock(spec=ExchangeRate)
    rate.id = uuid4()
    rate.tenant_id = str(uuid4())
    rate.base_currency_code = "EUR"
    rate.quote_currency_code = "USD"
    rate.rate = Decimal("1.0850")
    rate.inverse_rate = Decimal("0.921659")
    rate.rate_date = date.today()
    rate.rate_type = RateType.SPOT.value
    rate.source = RateSource.ECB.value
    rate.is_manual = False
    rate.is_interpolated = False
    return rate


@pytest.fixture
def mock_config():
    """Configuration mock."""
    config = Mock(spec=CurrencyConfig)
    config.id = uuid4()
    config.tenant_id = str(uuid4())
    config.default_currency_code = "EUR"
    config.reporting_currency_code = "EUR"
    config.primary_rate_source = RateSource.ECB.value
    config.auto_update_rates = True
    config.update_frequency_hours = 24
    config.conversion_method = ConversionMethod.DIRECT.value
    config.pivot_currency_code = "EUR"
    config.allow_triangulation = True
    config.track_exchange_gains = True
    config.rate_tolerance_percent = Decimal("5.00")
    config.require_rate_approval = False
    config.api_keys = {}
    return config


# ============================================================================
# TESTS ISO 4217
# ============================================================================

class TestISO4217:
    """Tests pour les devises ISO 4217."""

    def test_major_currencies_defined(self):
        """Les devises majeures sont definies."""
        assert "EUR" in MAJOR_CURRENCIES
        assert "USD" in MAJOR_CURRENCIES
        assert "GBP" in MAJOR_CURRENCIES
        assert "CHF" in MAJOR_CURRENCIES
        assert "JPY" in MAJOR_CURRENCIES

    def test_iso_currencies_complete(self):
        """Les devises ISO sont completes."""
        assert len(ISO_4217_CURRENCIES) >= 40
        for code, info in ISO_4217_CURRENCIES.items():
            assert len(code) == 3
            assert "name" in info
            assert "symbol" in info
            assert "decimals" in info
            assert info["decimals"] >= 0
            assert info["decimals"] <= 4

    def test_euro_properties(self):
        """L'euro a les bonnes proprietes."""
        eur = ISO_4217_CURRENCIES["EUR"]
        assert eur["name"] == "Euro"
        assert eur["symbol"] == "\u20ac"
        assert eur["decimals"] == 2
        assert eur["numeric"] == "978"

    def test_jpy_no_decimals(self):
        """Le yen n'a pas de decimales."""
        jpy = ISO_4217_CURRENCIES["JPY"]
        assert jpy["decimals"] == 0


# ============================================================================
# TESTS CONVERSION
# ============================================================================

class TestConversion:
    """Tests pour la conversion de devises."""

    def test_same_currency_conversion(self, service, mock_config):
        """Conversion vers la meme devise retourne le montant inchange."""
        service._config_cache = mock_config
        service.config_repo.get_or_create = Mock(return_value=mock_config)

        result = service.convert(
            amount=Decimal("100"),
            from_currency="EUR",
            to_currency="EUR"
        )

        assert result.original_amount == Decimal("100")
        assert result.converted_amount == Decimal("100")
        assert result.exchange_rate == Decimal("1")
        assert result.conversion_method == ConversionMethod.DIRECT

    def test_conversion_with_rate(self, service, mock_rate, mock_config):
        """Conversion avec taux disponible."""
        service._config_cache = mock_config
        service.config_repo.get_or_create = Mock(return_value=mock_config)
        service.rate_repo.get_rate = Mock(return_value=mock_rate)

        result = service.convert(
            amount=Decimal("100"),
            from_currency="EUR",
            to_currency="USD"
        )

        assert result.original_amount == Decimal("100")
        assert result.original_currency == "EUR"
        assert result.target_currency == "USD"
        assert result.exchange_rate == mock_rate.rate
        expected = (Decimal("100") * mock_rate.rate).quantize(Decimal("0.01"))
        assert result.converted_amount == expected

    def test_conversion_rounding(self, service, mock_rate, mock_config):
        """L'arrondi est correct selon la devise."""
        service._config_cache = mock_config
        service.config_repo.get_or_create = Mock(return_value=mock_config)

        # Taux pour le JPY (0 decimales)
        jpy_rate = Mock(spec=ExchangeRate)
        jpy_rate.rate = Decimal("162.50")
        jpy_rate.inverse_rate = Decimal("0.006154")
        jpy_rate.rate_date = date.today()
        jpy_rate.rate_type = RateType.SPOT.value
        jpy_rate.source = RateSource.ECB.value
        jpy_rate.is_interpolated = False

        service.rate_repo.get_rate = Mock(return_value=jpy_rate)

        result = service.convert(
            amount=Decimal("100"),
            from_currency="EUR",
            to_currency="JPY"
        )

        # JPY n'a pas de decimales
        assert result.converted_amount == Decimal("16250")

    def test_conversion_not_found(self, service, mock_config):
        """Erreur si taux non trouve."""
        service._config_cache = mock_config
        service.config_repo.get_or_create = Mock(return_value=mock_config)
        service.rate_repo.get_rate = Mock(return_value=None)

        with pytest.raises(ExchangeRateNotFoundError):
            service.convert(
                amount=Decimal("100"),
                from_currency="EUR",
                to_currency="XYZ"
            )


# ============================================================================
# TESTS TAUX DE CHANGE
# ============================================================================

class TestExchangeRates:
    """Tests pour les taux de change."""

    def test_get_rate_direct(self, service, mock_rate, mock_config):
        """Recuperation taux direct."""
        service._config_cache = mock_config
        service.rate_repo.get_rate = Mock(return_value=mock_rate)

        rate = service.get_rate("EUR", "USD")

        assert rate is not None
        assert rate.base_currency_code == "EUR"
        assert rate.quote_currency_code == "USD"

    def test_get_rate_inverse(self, service, mock_rate, mock_config):
        """Recuperation taux inverse."""
        service._config_cache = mock_config

        # Pas de taux direct
        def get_rate_mock(base, quote, rate_date=None):
            if base == "EUR" and quote == "USD":
                return mock_rate
            return None

        service.rate_repo.get_rate = Mock(side_effect=get_rate_mock)

        rate = service.get_rate("USD", "EUR")

        # Devrait retourner le taux inverse
        assert rate is not None

    def test_get_rate_same_currency(self, service, mock_config):
        """Taux pour meme devise = 1."""
        service._config_cache = mock_config

        rate = service.get_rate("EUR", "EUR")

        assert rate is not None
        assert rate.rate == Decimal("1")
        assert rate.base_currency_code == "EUR"
        assert rate.quote_currency_code == "EUR"

    def test_set_rate(self, service, mock_currency, mock_config):
        """Definition d'un taux manuel."""
        service._config_cache = mock_config
        service.config_repo.get_or_create = Mock(return_value=mock_config)
        service.currency_repo.get_by_code = Mock(return_value=mock_currency)
        service.rate_repo.get_latest_rate = Mock(return_value=None)

        mock_new_rate = Mock(spec=ExchangeRate)
        mock_new_rate.rate = Decimal("1.10")
        service.rate_repo.upsert = Mock(return_value=mock_new_rate)

        rate = service.set_rate(
            base="EUR",
            quote="USD",
            rate=Decimal("1.10")
        )

        assert rate is not None
        service.rate_repo.upsert.assert_called_once()

    def test_set_rate_tolerance_exceeded(self, service, mock_currency, mock_rate, mock_config):
        """Alerte si variation depasse le seuil."""
        mock_config.rate_tolerance_percent = Decimal("5.00")
        mock_config.require_rate_approval = True
        service._config_cache = mock_config
        service.config_repo.get_or_create = Mock(return_value=mock_config)
        service.currency_repo.get_by_code = Mock(return_value=mock_currency)

        # Taux existant
        service.rate_repo.get_latest_rate = Mock(return_value=mock_rate)

        # Nouveau taux avec variation > 5%
        new_rate = Decimal("1.20")  # Variation ~10%

        with pytest.raises(RateToleranceExceededError):
            service.set_rate(
                base="EUR",
                quote="USD",
                rate=new_rate
            )


# ============================================================================
# TESTS TRIANGULATION
# ============================================================================

class TestTriangulation:
    """Tests pour la triangulation."""

    def test_triangulation_via_eur(self, service, mock_config):
        """Triangulation via EUR (pivot)."""
        mock_config.allow_triangulation = True
        mock_config.pivot_currency_code = "EUR"
        service._config_cache = mock_config
        service.config_repo.get_or_create = Mock(return_value=mock_config)

        # Taux GBP/EUR et EUR/CHF
        gbp_eur_rate = Mock(spec=ExchangeRate)
        gbp_eur_rate.rate = Decimal("1.17")  # 1 GBP = 1.17 EUR
        gbp_eur_rate.inverse_rate = Decimal("0.8547")
        gbp_eur_rate.rate_date = date.today()
        gbp_eur_rate.rate_type = RateType.SPOT.value
        gbp_eur_rate.source = RateSource.ECB.value

        eur_chf_rate = Mock(spec=ExchangeRate)
        eur_chf_rate.rate = Decimal("0.96")  # 1 EUR = 0.96 CHF
        eur_chf_rate.inverse_rate = Decimal("1.0417")
        eur_chf_rate.rate_date = date.today()
        eur_chf_rate.rate_type = RateType.SPOT.value
        eur_chf_rate.source = RateSource.ECB.value

        call_count = [0]

        def get_rate_mock(base, quote, rate_date=None, allow_inverse=True, allow_triangulation=True):
            call_count[0] += 1
            if base == "GBP" and quote == "EUR":
                return gbp_eur_rate
            if base == "EUR" and quote == "CHF":
                return eur_chf_rate
            return None

        service.get_rate = get_rate_mock

        # Triangulation GBP -> CHF via EUR
        rate = service._triangulate("GBP", "CHF", date.today(), "EUR")

        assert rate is not None
        assert rate.base_currency_code == "GBP"
        assert rate.quote_currency_code == "CHF"
        # GBP/CHF = GBP/EUR * EUR/CHF = 1.17 * 0.96 = 1.1232
        expected_rate = Decimal("1.17") * Decimal("0.96")
        assert rate.rate == expected_rate.quantize(Decimal("0.000000000001"))
        assert rate.is_interpolated == True


# ============================================================================
# TESTS GAINS/PERTES DE CHANGE
# ============================================================================

class TestExchangeGainLoss:
    """Tests pour les gains/pertes de change."""

    def test_calculate_gain(self, service, mock_config):
        """Calcul d'un gain de change."""
        mock_config.reporting_currency_code = "EUR"
        service._config_cache = mock_config
        service.config_repo.get_or_create = Mock(return_value=mock_config)

        mock_gain_loss = Mock()
        mock_gain_loss.gain_loss_amount = Decimal("50.00")
        mock_gain_loss.is_gain = True
        service.gain_loss_repo.create = Mock(return_value=mock_gain_loss)

        result = service.calculate_exchange_gain_loss(
            document_type="invoice",
            document_id=uuid4(),
            original_amount=Decimal("1000"),
            original_currency="USD",
            booking_rate=Decimal("0.90"),   # 1 USD = 0.90 EUR a la facturation
            settlement_rate=Decimal("0.95"),  # 1 USD = 0.95 EUR au reglement
            booking_date=date.today() - timedelta(days=30),
            settlement_date=date.today()
        )

        # Gain: (1000 * 0.95) - (1000 * 0.90) = 950 - 900 = 50 EUR
        service.gain_loss_repo.create.assert_called_once()
        call_args = service.gain_loss_repo.create.call_args
        data = call_args[0][0]

        assert data["gain_loss_amount"] == Decimal("50.00")
        assert data["is_gain"] == True
        assert data["gain_loss_type"] == GainLossType.REALIZED.value

    def test_calculate_loss(self, service, mock_config):
        """Calcul d'une perte de change."""
        mock_config.reporting_currency_code = "EUR"
        service._config_cache = mock_config
        service.config_repo.get_or_create = Mock(return_value=mock_config)

        mock_gain_loss = Mock()
        service.gain_loss_repo.create = Mock(return_value=mock_gain_loss)

        result = service.calculate_exchange_gain_loss(
            document_type="invoice",
            document_id=uuid4(),
            original_amount=Decimal("1000"),
            original_currency="USD",
            booking_rate=Decimal("0.95"),   # 1 USD = 0.95 EUR a la facturation
            settlement_rate=Decimal("0.90"),  # 1 USD = 0.90 EUR au reglement
            booking_date=date.today() - timedelta(days=30),
            settlement_date=date.today()
        )

        # Perte: (1000 * 0.90) - (1000 * 0.95) = 900 - 950 = -50 EUR
        call_args = service.gain_loss_repo.create.call_args
        data = call_args[0][0]

        assert data["gain_loss_amount"] == Decimal("-50.00")
        assert data["is_gain"] == False


# ============================================================================
# TESTS FORMATAGE
# ============================================================================

class TestFormatting:
    """Tests pour le formatage des montants."""

    def test_format_eur_french(self, service):
        """Formatage EUR en francais."""
        result = service.format_amount(Decimal("1234.56"), "EUR", "fr_FR")
        assert "\u20ac" in result
        # Format: 1 234,56 EUR
        assert "1" in result
        assert "234" in result

    def test_format_usd_english(self, service):
        """Formatage USD en anglais."""
        result = service.format_amount(Decimal("1234.56"), "USD", "en_US")
        assert "$" in result

    def test_format_jpy_no_decimals(self, service):
        """Formatage JPY sans decimales."""
        result = service.format_amount(Decimal("12345.67"), "JPY", "fr_FR")
        # Le JPY n'a pas de decimales
        assert "12346" in result or "12345" in result


# ============================================================================
# TESTS API EXTERNES
# ============================================================================

class TestAPIIntegration:
    """Tests pour l'integration des APIs externes."""

    @pytest.mark.asyncio
    async def test_fetch_ecb_rates(self, service, mock_config):
        """Test recuperation taux BCE."""
        service._config_cache = mock_config

        # Mock httpx response
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01"
                         xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
            <Cube>
                <Cube time="2024-01-15">
                    <Cube currency="USD" rate="1.0850"/>
                    <Cube currency="GBP" rate="0.8550"/>
                    <Cube currency="CHF" rate="0.9450"/>
                </Cube>
            </Cube>
        </gesmes:Envelope>
        """

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.text = mock_xml
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
            mock_client.return_value.__aexit__ = AsyncMock()
            mock_client.return_value.get = AsyncMock(return_value=mock_response)

            service.rate_repo.upsert = Mock()
            service.update_config = Mock()

            rates_saved = await service.fetch_rates_from_ecb()

            assert rates_saved == 3
            assert service.rate_repo.upsert.call_count == 3


# ============================================================================
# TESTS INTEGRATION MULTI-DEVISES
# ============================================================================

class TestMultiCurrencyIntegration:
    """Tests d'integration multi-devises."""

    def test_convert_multiple(self, service, mock_config):
        """Conversion de plusieurs montants."""
        service._config_cache = mock_config
        service.config_repo.get_or_create = Mock(return_value=mock_config)

        # Mocks pour les taux
        usd_rate = Mock(spec=ExchangeRate)
        usd_rate.rate = Decimal("0.92")
        usd_rate.inverse_rate = Decimal("1.0870")
        usd_rate.rate_date = date.today()
        usd_rate.rate_type = RateType.SPOT.value
        usd_rate.source = RateSource.ECB.value
        usd_rate.is_interpolated = False

        gbp_rate = Mock(spec=ExchangeRate)
        gbp_rate.rate = Decimal("1.17")
        gbp_rate.inverse_rate = Decimal("0.8547")
        gbp_rate.rate_date = date.today()
        gbp_rate.rate_type = RateType.SPOT.value
        gbp_rate.source = RateSource.ECB.value
        gbp_rate.is_interpolated = False

        def get_rate_mock(from_curr, to_curr, rate_date=None):
            if from_curr == "USD" and to_curr == "EUR":
                return usd_rate
            if from_curr == "GBP" and to_curr == "EUR":
                return gbp_rate
            if from_curr == "EUR" and to_curr == "EUR":
                return None  # Sera gere comme meme devise
            return None

        service.rate_repo.get_rate = Mock(side_effect=get_rate_mock)

        amounts = [
            {"amount": 100, "currency": "USD"},
            {"amount": 100, "currency": "GBP"},
            {"amount": 100, "currency": "EUR"},
        ]

        conversions, total = service.convert_multiple(amounts, "EUR")

        assert len(conversions) == 3
        # USD: 100 * 0.92 = 92 EUR
        # GBP: 100 * 1.17 = 117 EUR
        # EUR: 100 EUR
        # Total: 92 + 117 + 100 = 309 EUR


# ============================================================================
# TESTS DE REGRESSION
# ============================================================================

class TestRegression:
    """Tests de non-regression."""

    def test_decimal_precision(self, service, mock_rate, mock_config):
        """La precision decimale est conservee."""
        service._config_cache = mock_config
        service.config_repo.get_or_create = Mock(return_value=mock_config)

        # Taux avec beaucoup de decimales
        precise_rate = Mock(spec=ExchangeRate)
        precise_rate.rate = Decimal("1.123456789012")
        precise_rate.inverse_rate = Decimal("0.890109890110")
        precise_rate.rate_date = date.today()
        precise_rate.rate_type = RateType.SPOT.value
        precise_rate.source = RateSource.ECB.value
        precise_rate.is_interpolated = False

        service.rate_repo.get_rate = Mock(return_value=precise_rate)

        result = service.convert(
            amount=Decimal("1000.00"),
            from_currency="EUR",
            to_currency="USD"
        )

        # Le resultat doit etre arrondi a 2 decimales pour USD
        assert result.converted_amount == Decimal("1123.46")

    def test_large_amounts(self, service, mock_rate, mock_config):
        """Les gros montants sont geres correctement."""
        service._config_cache = mock_config
        service.config_repo.get_or_create = Mock(return_value=mock_config)
        service.rate_repo.get_rate = Mock(return_value=mock_rate)

        large_amount = Decimal("999999999999.99")

        result = service.convert(
            amount=large_amount,
            from_currency="EUR",
            to_currency="USD"
        )

        assert result.converted_amount > 0
        assert result.original_amount == large_amount

    def test_small_amounts(self, service, mock_rate, mock_config):
        """Les petits montants sont geres correctement."""
        service._config_cache = mock_config
        service.config_repo.get_or_create = Mock(return_value=mock_config)
        service.rate_repo.get_rate = Mock(return_value=mock_rate)

        small_amount = Decimal("0.01")

        result = service.convert(
            amount=small_amount,
            from_currency="EUR",
            to_currency="USD"
        )

        assert result.converted_amount >= Decimal("0.01")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
