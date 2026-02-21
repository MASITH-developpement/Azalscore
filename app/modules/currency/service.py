"""
AZALS MODULE - CURRENCY: Service
=================================

Service complet de gestion multi-devises.

FONCTIONNALITES:
- Gestion des devises ISO 4217
- Taux de change manuels et automatiques
- Integration API BCE, OpenExchange, Fixer
- Conversion avec triangulation
- Calcul gains/pertes de change
- Reevaluation periodique
- Rapports et alertes

INSPIRATIONS CONCURRENTIELLES:
- Sage: Taux manuels, ecarts de change
- Odoo: API BCE, historique complet, triangulation EUR
- Microsoft Dynamics 365: Multi-devises avancees, pivot
- Pennylane: Conversion temps reel
- Axonaut: Simplicite d'usage
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN, ROUND_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
import httpx

from sqlalchemy.orm import Session

from .models import (
    Currency, ExchangeRate, CurrencyConfig, ExchangeGainLoss,
    CurrencyRevaluation, CurrencyConversionLog, RateAlert,
    CurrencyStatus, RateSource, RateType, ConversionMethod,
    GainLossType, RevaluationStatus
)
from .repository import (
    CurrencyRepository, ExchangeRateRepository, CurrencyConfigRepository,
    ExchangeGainLossRepository, CurrencyRevaluationRepository,
    CurrencyConversionLogRepository, RateAlertRepository
)
from .schemas import (
    ConversionResult, ConversionRequest, RateHistoryItem,
    ExchangeGainLossSummary, RevaluationPreview
)
from .exceptions import (
    CurrencyNotFoundError, CurrencyDisabledError, CurrencyAlreadyExistsError,
    ExchangeRateNotFoundError, InvalidExchangeRateError, SameCurrencyConversionError,
    NoConversionPathError, TriangulationFailedError, RateToleranceExceededError,
    RateAPIError, RateAPIUnavailableError, ConfigNotFoundError
)


logger = logging.getLogger(__name__)


# ============================================================================
# DEVISES ISO 4217 PRINCIPALES
# ============================================================================

ISO_4217_CURRENCIES = {
    "EUR": {"name": "Euro", "symbol": "\u20ac", "decimals": 2, "numeric": "978", "countries": ["FR", "DE", "IT", "ES"]},
    "USD": {"name": "Dollar americain", "symbol": "$", "decimals": 2, "numeric": "840", "countries": ["US"]},
    "GBP": {"name": "Livre sterling", "symbol": "\u00a3", "decimals": 2, "numeric": "826", "countries": ["GB"]},
    "CHF": {"name": "Franc suisse", "symbol": "CHF", "decimals": 2, "numeric": "756", "countries": ["CH"]},
    "JPY": {"name": "Yen japonais", "symbol": "\u00a5", "decimals": 0, "numeric": "392", "countries": ["JP"]},
    "CAD": {"name": "Dollar canadien", "symbol": "CA$", "decimals": 2, "numeric": "124", "countries": ["CA"]},
    "AUD": {"name": "Dollar australien", "symbol": "A$", "decimals": 2, "numeric": "036", "countries": ["AU"]},
    "CNY": {"name": "Yuan chinois", "symbol": "\u00a5", "decimals": 2, "numeric": "156", "countries": ["CN"]},
    "INR": {"name": "Roupie indienne", "symbol": "\u20b9", "decimals": 2, "numeric": "356", "countries": ["IN"]},
    "BRL": {"name": "Real bresilien", "symbol": "R$", "decimals": 2, "numeric": "986", "countries": ["BR"]},
    "MXN": {"name": "Peso mexicain", "symbol": "MX$", "decimals": 2, "numeric": "484", "countries": ["MX"]},
    "RUB": {"name": "Rouble russe", "symbol": "\u20bd", "decimals": 2, "numeric": "643", "countries": ["RU"]},
    "KRW": {"name": "Won sud-coreen", "symbol": "\u20a9", "decimals": 0, "numeric": "410", "countries": ["KR"]},
    "SGD": {"name": "Dollar singapourien", "symbol": "S$", "decimals": 2, "numeric": "702", "countries": ["SG"]},
    "HKD": {"name": "Dollar hongkongais", "symbol": "HK$", "decimals": 2, "numeric": "344", "countries": ["HK"]},
    "NOK": {"name": "Couronne norvegienne", "symbol": "kr", "decimals": 2, "numeric": "578", "countries": ["NO"]},
    "SEK": {"name": "Couronne suedoise", "symbol": "kr", "decimals": 2, "numeric": "752", "countries": ["SE"]},
    "DKK": {"name": "Couronne danoise", "symbol": "kr", "decimals": 2, "numeric": "208", "countries": ["DK"]},
    "PLN": {"name": "Zloty polonais", "symbol": "z\u0142", "decimals": 2, "numeric": "985", "countries": ["PL"]},
    "CZK": {"name": "Couronne tcheque", "symbol": "K\u010d", "decimals": 2, "numeric": "203", "countries": ["CZ"]},
    "HUF": {"name": "Forint hongrois", "symbol": "Ft", "decimals": 0, "numeric": "348", "countries": ["HU"]},
    "RON": {"name": "Leu roumain", "symbol": "lei", "decimals": 2, "numeric": "946", "countries": ["RO"]},
    "BGN": {"name": "Lev bulgare", "symbol": "\u043b\u0432", "decimals": 2, "numeric": "975", "countries": ["BG"]},
    "TRY": {"name": "Livre turque", "symbol": "\u20ba", "decimals": 2, "numeric": "949", "countries": ["TR"]},
    "ZAR": {"name": "Rand sud-africain", "symbol": "R", "decimals": 2, "numeric": "710", "countries": ["ZA"]},
    "MAD": {"name": "Dirham marocain", "symbol": "MAD", "decimals": 2, "numeric": "504", "countries": ["MA"]},
    "TND": {"name": "Dinar tunisien", "symbol": "DT", "decimals": 3, "numeric": "788", "countries": ["TN"]},
    "XOF": {"name": "Franc CFA BCEAO", "symbol": "CFA", "decimals": 0, "numeric": "952", "countries": ["SN", "CI"]},
    "XAF": {"name": "Franc CFA BEAC", "symbol": "FCFA", "decimals": 0, "numeric": "950", "countries": ["CM", "GA"]},
    "AED": {"name": "Dirham emirien", "symbol": "AED", "decimals": 2, "numeric": "784", "countries": ["AE"]},
    "SAR": {"name": "Riyal saoudien", "symbol": "SAR", "decimals": 2, "numeric": "682", "countries": ["SA"]},
    "NZD": {"name": "Dollar neo-zelandais", "symbol": "NZ$", "decimals": 2, "numeric": "554", "countries": ["NZ"]},
    "THB": {"name": "Baht thailandais", "symbol": "\u0e3f", "decimals": 2, "numeric": "764", "countries": ["TH"]},
    "IDR": {"name": "Roupie indonesienne", "symbol": "Rp", "decimals": 0, "numeric": "360", "countries": ["ID"]},
    "MYR": {"name": "Ringgit malaisien", "symbol": "RM", "decimals": 2, "numeric": "458", "countries": ["MY"]},
    "PHP": {"name": "Peso philippin", "symbol": "\u20b1", "decimals": 2, "numeric": "608", "countries": ["PH"]},
    "VND": {"name": "Dong vietnamien", "symbol": "\u20ab", "decimals": 0, "numeric": "704", "countries": ["VN"]},
    "ILS": {"name": "Shekel israelien", "symbol": "\u20aa", "decimals": 2, "numeric": "376", "countries": ["IL"]},
    "EGP": {"name": "Livre egyptienne", "symbol": "EGP", "decimals": 2, "numeric": "818", "countries": ["EG"]},
    "NGN": {"name": "Naira nigerien", "symbol": "\u20a6", "decimals": 2, "numeric": "566", "countries": ["NG"]},
    "ARS": {"name": "Peso argentin", "symbol": "ARS", "decimals": 2, "numeric": "032", "countries": ["AR"]},
    "CLP": {"name": "Peso chilien", "symbol": "CLP", "decimals": 0, "numeric": "152", "countries": ["CL"]},
    "COP": {"name": "Peso colombien", "symbol": "COP", "decimals": 0, "numeric": "170", "countries": ["CO"]},
    "PEN": {"name": "Sol peruvien", "symbol": "S/", "decimals": 2, "numeric": "604", "countries": ["PE"]},
}

MAJOR_CURRENCIES = ["EUR", "USD", "GBP", "CHF", "JPY", "CAD", "AUD", "CNY"]


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class CurrencyService:
    """
    Service de gestion multi-devises.

    Responsabilites:
    - CRUD devises
    - Gestion des taux de change
    - Conversion avec strategies (direct, triangulation)
    - Calcul des ecarts de change
    - Reevaluation periodique
    - Integration APIs externes
    """

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

        # Repositories
        self.currency_repo = CurrencyRepository(db, tenant_id)
        self.rate_repo = ExchangeRateRepository(db, tenant_id)
        self.config_repo = CurrencyConfigRepository(db, tenant_id)
        self.gain_loss_repo = ExchangeGainLossRepository(db, tenant_id)
        self.revaluation_repo = CurrencyRevaluationRepository(db, tenant_id)
        self.log_repo = CurrencyConversionLogRepository(db, tenant_id)
        self.alert_repo = RateAlertRepository(db, tenant_id)

        # Cache local
        self._config_cache: Optional[CurrencyConfig] = None

    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    def get_config(self) -> CurrencyConfig:
        """Recupere la configuration du tenant."""
        if not self._config_cache:
            self._config_cache = self.config_repo.get_or_create()
        return self._config_cache

    def update_config(self, data: Dict[str, Any], updated_by: UUID = None) -> CurrencyConfig:
        """Met a jour la configuration."""
        config = self.get_config()
        config = self.config_repo.update(config, data, updated_by)
        self._config_cache = config
        return config

    def get_default_currency(self) -> Currency:
        """Recupere la devise par defaut."""
        currency = self.currency_repo.get_default()
        if not currency:
            config = self.get_config()
            currency = self.currency_repo.get_by_code(config.default_currency_code)
        if not currency:
            raise CurrencyNotFoundError(currency_code="EUR")
        return currency

    def get_reporting_currency(self) -> Currency:
        """Recupere la devise de reporting."""
        currency = self.currency_repo.get_reporting()
        if not currency:
            config = self.get_config()
            currency = self.currency_repo.get_by_code(config.reporting_currency_code)
        if not currency:
            return self.get_default_currency()
        return currency

    # ========================================================================
    # GESTION DES DEVISES
    # ========================================================================

    def get_currency(self, code: str) -> Currency:
        """Recupere une devise par code."""
        currency = self.currency_repo.get_by_code(code)
        if not currency:
            raise CurrencyNotFoundError(currency_code=code)
        return currency

    def list_currencies(
        self,
        enabled_only: bool = True,
        include_major: bool = True
    ) -> List[Currency]:
        """Liste les devises."""
        if enabled_only:
            return self.currency_repo.list_enabled()
        items, _ = self.currency_repo.list()
        return items

    def create_currency(
        self,
        code: str,
        name: str,
        symbol: str,
        decimals: int = 2,
        created_by: UUID = None,
        **kwargs
    ) -> Currency:
        """Cree une devise."""
        code = code.upper()
        if self.currency_repo.exists(code):
            raise CurrencyAlreadyExistsError(code)

        data = {
            "code": code,
            "name": name,
            "symbol": symbol,
            "decimals": decimals,
            "is_enabled": True,
            **kwargs
        }

        return self.currency_repo.create(data, created_by)

    def enable_currency(self, code: str, updated_by: UUID = None) -> Currency:
        """Active une devise."""
        currency = self.get_currency(code)
        return self.currency_repo.update(currency, {"is_enabled": True}, updated_by)

    def disable_currency(self, code: str, updated_by: UUID = None) -> Currency:
        """Desactive une devise."""
        currency = self.get_currency(code)

        # Verifier que ce n'est pas la devise par defaut ou de reporting
        config = self.get_config()
        if currency.code == config.default_currency_code:
            from .exceptions import DefaultCurrencyCannotBeDisabledError
            raise DefaultCurrencyCannotBeDisabledError(code)
        if currency.code == config.reporting_currency_code:
            from .exceptions import ReportingCurrencyCannotBeDisabledError
            raise ReportingCurrencyCannotBeDisabledError(code)

        return self.currency_repo.update(currency, {"is_enabled": False}, updated_by)

    def set_default_currency(self, code: str, updated_by: UUID = None) -> Currency:
        """Definit la devise par defaut."""
        currency = self.get_currency(code)
        self.currency_repo.set_default(currency, updated_by)
        self.update_config({"default_currency_code": code}, updated_by)
        return currency

    def set_reporting_currency(self, code: str, updated_by: UUID = None) -> Currency:
        """Definit la devise de reporting."""
        currency = self.get_currency(code)
        self.currency_repo.set_reporting(currency, updated_by)
        self.update_config({"reporting_currency_code": code}, updated_by)
        return currency

    def initialize_iso_currencies(self, created_by: UUID = None) -> int:
        """Initialise les devises ISO 4217."""
        created = 0
        for code, info in ISO_4217_CURRENCIES.items():
            if not self.currency_repo.exists(code):
                self.currency_repo.create({
                    "code": code,
                    "name": info["name"],
                    "symbol": info["symbol"],
                    "decimals": info["decimals"],
                    "numeric_code": info["numeric"],
                    "country_codes": info["countries"],
                    "is_major": code in MAJOR_CURRENCIES,
                    "is_enabled": code in MAJOR_CURRENCIES,
                    "status": CurrencyStatus.ACTIVE.value
                }, created_by)
                created += 1
        self.db.commit()
        return created

    # ========================================================================
    # TAUX DE CHANGE
    # ========================================================================

    def get_rate(
        self,
        base: str,
        quote: str,
        rate_date: date = None,
        allow_inverse: bool = True,
        allow_triangulation: bool = True
    ) -> Optional[ExchangeRate]:
        """
        Recupere le taux de change.

        Strategies:
        1. Taux direct (base/quote)
        2. Taux inverse (quote/base)
        3. Triangulation via devise pivot
        """
        base = base.upper()
        quote = quote.upper()
        rate_date = rate_date or date.today()

        # Meme devise
        if base == quote:
            return self._create_unity_rate(base, rate_date)

        # Taux direct
        rate = self.rate_repo.get_rate(base, quote, rate_date)
        if rate:
            return rate

        # Taux inverse
        if allow_inverse:
            inverse = self.rate_repo.get_rate(quote, base, rate_date)
            if inverse:
                return self._invert_rate(inverse)

        # Triangulation
        if allow_triangulation:
            config = self.get_config()
            if config.allow_triangulation:
                return self._triangulate(base, quote, rate_date, config.pivot_currency_code)

        return None

    def _create_unity_rate(self, currency: str, rate_date: date) -> ExchangeRate:
        """Cree un taux unitaire (meme devise)."""
        rate = ExchangeRate()
        rate.id = uuid4()
        rate.tenant_id = self.tenant_id
        rate.base_currency_code = currency
        rate.quote_currency_code = currency
        rate.rate = Decimal("1")
        rate.inverse_rate = Decimal("1")
        rate.rate_date = rate_date
        rate.rate_type = RateType.SPOT.value
        rate.source = RateSource.MANUAL.value
        return rate

    def _invert_rate(self, rate: ExchangeRate) -> ExchangeRate:
        """Inverse un taux de change."""
        inverted = ExchangeRate()
        inverted.id = uuid4()
        inverted.tenant_id = self.tenant_id
        inverted.base_currency_code = rate.quote_currency_code
        inverted.quote_currency_code = rate.base_currency_code
        inverted.rate = rate.inverse_rate or (Decimal("1") / rate.rate)
        inverted.inverse_rate = rate.rate
        inverted.rate_date = rate.rate_date
        inverted.rate_type = rate.rate_type
        inverted.source = rate.source
        return inverted

    def _triangulate(
        self,
        base: str,
        quote: str,
        rate_date: date,
        pivot: str = "EUR"
    ) -> Optional[ExchangeRate]:
        """Triangulation via devise pivot."""
        pivot = pivot.upper()
        if base == pivot or quote == pivot:
            return None

        # base -> pivot
        rate_base_pivot = self.get_rate(base, pivot, rate_date, allow_triangulation=False)
        if not rate_base_pivot:
            return None

        # pivot -> quote
        rate_pivot_quote = self.get_rate(pivot, quote, rate_date, allow_triangulation=False)
        if not rate_pivot_quote:
            return None

        # Calculer le taux combine
        combined_rate = rate_base_pivot.rate * rate_pivot_quote.rate

        triangulated = ExchangeRate()
        triangulated.id = uuid4()
        triangulated.tenant_id = self.tenant_id
        triangulated.base_currency_code = base
        triangulated.quote_currency_code = quote
        triangulated.rate = combined_rate.quantize(Decimal("0.000000000001"))
        triangulated.inverse_rate = (Decimal("1") / combined_rate).quantize(Decimal("0.000000000001"))
        triangulated.rate_date = rate_date
        triangulated.rate_type = RateType.SPOT.value
        triangulated.source = RateSource.MANUAL.value
        triangulated.is_interpolated = True

        return triangulated

    def set_rate(
        self,
        base: str,
        quote: str,
        rate: Decimal,
        rate_date: date = None,
        rate_type: RateType = RateType.SPOT,
        source: RateSource = RateSource.MANUAL,
        created_by: UUID = None
    ) -> ExchangeRate:
        """Definit un taux de change."""
        base = base.upper()
        quote = quote.upper()
        rate_date = rate_date or date.today()

        if base == quote:
            raise SameCurrencyConversionError(base)

        if rate <= 0:
            raise InvalidExchangeRateError("Le taux doit etre positif")

        # Verifier la tolerance
        config = self.get_config()
        existing = self.rate_repo.get_latest_rate(base, quote)
        if existing and config.rate_tolerance_percent:
            variation = abs((rate - existing.rate) / existing.rate * 100)
            if variation > config.rate_tolerance_percent:
                self._create_rate_alert(
                    base, quote, existing.rate, rate, variation,
                    config.rate_tolerance_percent, "threshold"
                )
                if config.require_rate_approval:
                    raise RateToleranceExceededError(
                        str(existing.rate), str(rate),
                        str(variation), str(config.rate_tolerance_percent)
                    )

        # Recuperer les IDs des devises
        base_currency = self.get_currency(base)
        quote_currency = self.get_currency(quote)

        return self.rate_repo.upsert(
            base, quote, rate_date, rate, source, rate_type, created_by
        )

    def list_rates(
        self,
        base: str = None,
        rate_date: date = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ExchangeRate], int]:
        """Liste les taux de change."""
        from .schemas import ExchangeRateFilters
        filters = ExchangeRateFilters(
            base_currency=base,
            date_from=rate_date,
            date_to=rate_date
        )
        return self.rate_repo.list(filters, page, page_size)

    def get_rate_history(
        self,
        base: str,
        quote: str,
        start_date: date,
        end_date: date = None
    ) -> List[RateHistoryItem]:
        """Historique des taux."""
        end_date = end_date or date.today()
        rates = self.rate_repo.get_history(base, quote, start_date, end_date)

        history = []
        prev_rate = None
        for rate in reversed(rates):
            variation = None
            if prev_rate:
                variation = ((rate.rate - prev_rate) / prev_rate * 100).quantize(
                    Decimal("0.01")
                )
            history.append(RateHistoryItem(
                rate_date=rate.rate_date,
                rate=rate.rate,
                rate_type=RateType(rate.rate_type),
                source=RateSource(rate.source),
                variation_percent=variation
            ))
            prev_rate = rate.rate

        return history

    def _create_rate_alert(
        self,
        base: str,
        quote: str,
        old_rate: Decimal,
        new_rate: Decimal,
        variation: Decimal,
        threshold: Decimal,
        alert_type: str
    ):
        """Cree une alerte de taux."""
        severity = "warning" if variation < threshold * 2 else "critical"
        self.alert_repo.create({
            "base_currency_code": base,
            "quote_currency_code": quote,
            "alert_type": alert_type,
            "severity": severity,
            "old_rate": old_rate,
            "new_rate": new_rate,
            "variation_percent": variation,
            "threshold_percent": threshold,
            "title": f"Variation {base}/{quote}: {variation:.2f}%",
            "message": f"Le taux {base}/{quote} a varie de {variation:.2f}% "
                       f"(seuil: {threshold}%): {old_rate} -> {new_rate}"
        })

    # ========================================================================
    # CONVERSION
    # ========================================================================

    def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        rate_date: date = None,
        rate_type: RateType = RateType.SPOT,
        log_conversion: bool = False,
        document_type: str = None,
        document_id: UUID = None
    ) -> ConversionResult:
        """
        Convertit un montant d'une devise a une autre.
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        rate_date = rate_date or date.today()

        # Meme devise
        if from_currency == to_currency:
            return ConversionResult(
                original_amount=amount,
                original_currency=from_currency,
                converted_amount=amount,
                target_currency=to_currency,
                exchange_rate=Decimal("1"),
                inverse_rate=Decimal("1"),
                rate_date=rate_date,
                rate_source=RateSource.MANUAL,
                rate_type=rate_type,
                conversion_method=ConversionMethod.DIRECT
            )

        # Obtenir le taux
        rate = self.get_rate(from_currency, to_currency, rate_date)
        if not rate:
            raise ExchangeRateNotFoundError(from_currency, to_currency, str(rate_date))

        # Convertir
        converted = amount * rate.rate

        # Arrondir selon la devise cible
        target_info = ISO_4217_CURRENCIES.get(to_currency, {"decimals": 2})
        decimals = target_info["decimals"]
        if decimals > 0:
            quantize_str = "0." + "0" * decimals
        else:
            quantize_str = "1"

        converted_rounded = converted.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
        rounding_diff = converted - converted_rounded

        # Determiner la methode
        method = ConversionMethod.DIRECT
        pivot = None
        if rate.is_interpolated:
            method = ConversionMethod.TRIANGULATION
            config = self.get_config()
            pivot = config.pivot_currency_code

        result = ConversionResult(
            original_amount=amount,
            original_currency=from_currency,
            converted_amount=converted_rounded,
            target_currency=to_currency,
            exchange_rate=rate.rate,
            inverse_rate=rate.inverse_rate or (Decimal("1") / rate.rate),
            rate_date=rate.rate_date,
            rate_source=RateSource(rate.source),
            rate_type=RateType(rate.rate_type),
            conversion_method=method,
            pivot_currency=pivot,
            rounding_difference=rounding_diff.quantize(Decimal("0.000001"))
        )

        # Logger si demande
        if log_conversion:
            self.log_repo.create({
                "original_amount": amount,
                "original_currency_code": from_currency,
                "converted_amount": converted_rounded,
                "target_currency_code": to_currency,
                "exchange_rate": rate.rate,
                "rate_date": rate.rate_date,
                "rate_source": rate.source,
                "rate_type": rate.rate_type,
                "conversion_method": method.value,
                "pivot_currency_code": pivot,
                "rounding_difference": rounding_diff,
                "document_type": document_type,
                "document_id": document_id
            })

        return result

    def convert_to_reporting(
        self,
        amount: Decimal,
        currency: str,
        rate_date: date = None
    ) -> ConversionResult:
        """Convertit vers la devise de reporting."""
        config = self.get_config()
        return self.convert(amount, currency, config.reporting_currency_code, rate_date)

    def convert_multiple(
        self,
        amounts: List[Dict[str, Any]],
        target_currency: str,
        rate_date: date = None
    ) -> Tuple[List[ConversionResult], Decimal]:
        """
        Convertit plusieurs montants vers une devise cible.
        Retourne les conversions individuelles et le total.
        """
        conversions = []
        total = Decimal("0")

        for item in amounts:
            result = self.convert(
                Decimal(str(item["amount"])),
                item["currency"],
                target_currency,
                rate_date
            )
            conversions.append(result)
            total += result.converted_amount

        return conversions, total

    # ========================================================================
    # GAINS ET PERTES DE CHANGE
    # ========================================================================

    def calculate_exchange_gain_loss(
        self,
        document_type: str,
        document_id: UUID,
        original_amount: Decimal,
        original_currency: str,
        booking_rate: Decimal,
        settlement_rate: Decimal,
        booking_date: date,
        settlement_date: date = None,
        created_by: UUID = None
    ) -> ExchangeGainLoss:
        """
        Calcule et enregistre le gain ou la perte de change.
        """
        config = self.get_config()
        reporting = config.reporting_currency_code

        # Calculer les montants
        booking_amount = (original_amount * booking_rate).quantize(Decimal("0.01"))
        settlement_amount = (original_amount * settlement_rate).quantize(Decimal("0.01"))
        gain_loss = settlement_amount - booking_amount

        return self.gain_loss_repo.create({
            "document_type": document_type,
            "document_id": document_id,
            "gain_loss_type": GainLossType.REALIZED.value if settlement_date else GainLossType.UNREALIZED.value,
            "original_amount": original_amount,
            "original_currency_code": original_currency.upper(),
            "booking_rate": booking_rate,
            "settlement_rate": settlement_rate,
            "booking_amount": booking_amount,
            "settlement_amount": settlement_amount,
            "reporting_currency_code": reporting,
            "gain_loss_amount": gain_loss,
            "is_gain": gain_loss > 0,
            "booking_date": booking_date,
            "settlement_date": settlement_date
        }, created_by)

    def get_gain_loss_summary(
        self,
        start_date: date,
        end_date: date
    ) -> ExchangeGainLossSummary:
        """Resume des gains/pertes sur une periode."""
        summary = self.gain_loss_repo.get_summary(start_date, end_date)
        config = self.get_config()

        return ExchangeGainLossSummary(
            period_start=start_date,
            period_end=end_date,
            currency=config.reporting_currency_code,
            **summary
        )

    # ========================================================================
    # REEVALUATION
    # ========================================================================

    def preview_revaluation(
        self,
        revaluation_date: date,
        currencies: List[str] = None
    ) -> RevaluationPreview:
        """
        Apercu d'une reevaluation.
        Simule les gains/pertes latents sans les enregistrer.
        """
        config = self.get_config()

        # TODO: Recuperer les postes ouverts (factures, creances, dettes)
        # en devises etrangeres et calculer les ecarts

        documents = []
        total_gain = Decimal("0")
        total_loss = Decimal("0")

        # Simulation placeholder
        return RevaluationPreview(
            revaluation_date=revaluation_date,
            currencies=currencies or [],
            documents=documents,
            total_gain=total_gain,
            total_loss=abs(total_loss),
            net_amount=total_gain + total_loss,
            document_count=len(documents)
        )

    def create_revaluation(
        self,
        name: str,
        revaluation_date: date,
        period: str,
        currencies: List[str] = None,
        created_by: UUID = None
    ) -> CurrencyRevaluation:
        """
        Cree une reevaluation.
        """
        config = self.get_config()

        # Verifier qu'il n'y a pas deja une reevaluation pour la periode
        existing = self.revaluation_repo.get_for_period(period)
        if existing:
            from .exceptions import RevaluationAlreadyExistsError
            raise RevaluationAlreadyExistsError(period)

        # Apercu
        preview = self.preview_revaluation(revaluation_date, currencies)

        return self.revaluation_repo.create({
            "name": name,
            "revaluation_date": revaluation_date,
            "period": period,
            "currencies_revalued": currencies or [],
            "base_currency_code": config.reporting_currency_code,
            "total_gain": preview.total_gain,
            "total_loss": preview.total_loss,
            "net_amount": preview.net_amount,
            "document_count": preview.document_count
        }, created_by)

    def post_revaluation(
        self,
        revaluation_id: UUID,
        journal_entry_id: UUID,
        posted_by: UUID
    ) -> CurrencyRevaluation:
        """Comptabilise une reevaluation."""
        revaluation = self.revaluation_repo.get_by_id(revaluation_id)
        if not revaluation:
            from .exceptions import RevaluationNotFoundError
            raise RevaluationNotFoundError()

        return self.revaluation_repo.post(revaluation, journal_entry_id, posted_by)

    # ========================================================================
    # API EXTERNE - RECUPERATION DES TAUX
    # ========================================================================

    async def fetch_rates_from_ecb(
        self,
        rate_date: date = None,
        created_by: UUID = None
    ) -> int:
        """
        Recupere les taux depuis l'API de la BCE.
        Les taux BCE sont toujours bases sur EUR.
        """
        rate_date = rate_date or date.today()
        url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()

            # Parser le XML
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)

            # Namespace ECB
            ns = {'gesmes': 'http://www.gesmes.org/xml/2002-08-01',
                  'eurofxref': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}

            rates_saved = 0
            for cube in root.findall('.//eurofxref:Cube[@currency]', ns):
                currency = cube.get('currency')
                rate_str = cube.get('rate')

                if currency and rate_str:
                    rate = Decimal(rate_str)
                    self.rate_repo.upsert(
                        "EUR", currency, rate_date, rate,
                        RateSource.ECB, RateType.CLOSING, created_by
                    )
                    rates_saved += 1

            # Mettre a jour la config
            self.update_config({
                "last_rate_update": datetime.utcnow(),
                "next_rate_update": datetime.utcnow() + timedelta(hours=24)
            })

            logger.info(f"[CURRENCY] BCE: {rates_saved} taux importes")
            return rates_saved

        except httpx.HTTPError as e:
            logger.error(f"[CURRENCY] Erreur API BCE: {e}")
            raise RateAPIUnavailableError("ECB")

    async def fetch_rates_from_openexchange(
        self,
        api_key: str,
        base: str = "USD",
        rate_date: date = None,
        created_by: UUID = None
    ) -> int:
        """
        Recupere les taux depuis Open Exchange Rates.
        Le plan gratuit utilise USD comme base.
        """
        rate_date = rate_date or date.today()
        url = f"https://openexchangerates.org/api/latest.json?app_id={api_key}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()

            data = response.json()
            rates = data.get("rates", {})

            rates_saved = 0
            for currency, rate_value in rates.items():
                if currency != base:
                    rate = Decimal(str(rate_value))
                    self.rate_repo.upsert(
                        base, currency, rate_date, rate,
                        RateSource.OPENEXCHANGE, RateType.SPOT, created_by
                    )
                    rates_saved += 1

            logger.info(f"[CURRENCY] OpenExchange: {rates_saved} taux importes")
            return rates_saved

        except httpx.HTTPError as e:
            logger.error(f"[CURRENCY] Erreur API OpenExchange: {e}")
            raise RateAPIUnavailableError("OpenExchange")

    async def fetch_rates_from_fixer(
        self,
        api_key: str,
        base: str = "EUR",
        symbols: List[str] = None,
        rate_date: date = None,
        created_by: UUID = None
    ) -> int:
        """
        Recupere les taux depuis Fixer.io.
        """
        rate_date = rate_date or date.today()
        url = f"http://data.fixer.io/api/latest?access_key={api_key}&base={base}"
        if symbols:
            url += f"&symbols={','.join(symbols)}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()

            data = response.json()
            if not data.get("success"):
                raise RateAPIError("Fixer", data.get("error", {}).get("info", "Erreur inconnue"))

            rates = data.get("rates", {})

            rates_saved = 0
            for currency, rate_value in rates.items():
                if currency != base:
                    rate = Decimal(str(rate_value))
                    self.rate_repo.upsert(
                        base, currency, rate_date, rate,
                        RateSource.FIXER, RateType.SPOT, created_by
                    )
                    rates_saved += 1

            logger.info(f"[CURRENCY] Fixer: {rates_saved} taux importes")
            return rates_saved

        except httpx.HTTPError as e:
            logger.error(f"[CURRENCY] Erreur API Fixer: {e}")
            raise RateAPIUnavailableError("Fixer")

    async def auto_update_rates(self, created_by: UUID = None) -> int:
        """
        Met a jour automatiquement les taux selon la source configuree.
        """
        config = self.get_config()

        if not config.auto_update_rates:
            return 0

        source = RateSource(config.primary_rate_source)

        try:
            if source == RateSource.ECB:
                return await self.fetch_rates_from_ecb(created_by=created_by)
            elif source == RateSource.OPENEXCHANGE:
                api_key = config.api_keys.get("openexchange")
                if api_key:
                    return await self.fetch_rates_from_openexchange(api_key, created_by=created_by)
            elif source == RateSource.FIXER:
                api_key = config.api_keys.get("fixer")
                if api_key:
                    return await self.fetch_rates_from_fixer(api_key, created_by=created_by)

        except RateAPIError:
            # Essayer la source de fallback
            fallback = config.fallback_rate_source
            if fallback and fallback != config.primary_rate_source:
                logger.warning(f"[CURRENCY] Fallback vers {fallback}")
                config.primary_rate_source = fallback
                return await self.auto_update_rates(created_by)

        return 0

    # ========================================================================
    # FORMATAGE
    # ========================================================================

    def format_amount(
        self,
        amount: Decimal,
        currency: str,
        locale: str = "fr_FR"
    ) -> str:
        """Formate un montant avec sa devise."""
        info = ISO_4217_CURRENCIES.get(currency.upper(), {"symbol": currency, "decimals": 2})

        decimals = info["decimals"]
        if decimals > 0:
            quantize_str = "0." + "0" * decimals
        else:
            quantize_str = "1"

        rounded = amount.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)

        if locale.startswith("fr"):
            # Format francais: 1 234,56 EUR
            formatted = f"{rounded:,.{decimals}f}".replace(",", " ").replace(".", ",")
            return f"{formatted} {info['symbol']}"
        else:
            # Format anglais: EUR 1,234.56
            formatted = f"{rounded:,.{decimals}f}"
            return f"{info['symbol']}{formatted}"


# ============================================================================
# FACTORY
# ============================================================================

def create_currency_service(db: Session, tenant_id: str) -> CurrencyService:
    """Cree une instance du service Currency."""
    return CurrencyService(db=db, tenant_id=tenant_id)
