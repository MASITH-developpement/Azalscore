"""
AZALSCORE Finance Currency Service
===================================

Service de gestion des devises et taux de change.

Fonctionnalités:
- Récupération taux BCE (Banque Centrale Européenne)
- Cache intelligent des taux
- Conversion multi-devises
- Calcul gains/pertes de change
"""
from __future__ import annotations


import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional, Dict
from uuid import uuid4

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# =============================================================================
# TYPES
# =============================================================================


class RateSource(str, Enum):
    """Source des taux de change."""

    ECB = "ecb"  # Banque Centrale Européenne
    MANUAL = "manual"  # Saisie manuelle
    CACHE = "cache"  # Depuis le cache
    FALLBACK = "fallback"  # Taux de secours


class RoundingMode(str, Enum):
    """Mode d'arrondi."""

    HALF_UP = "half_up"  # Standard
    HALF_DOWN = "half_down"
    FLOOR = "floor"
    CEILING = "ceiling"


@dataclass
class ExchangeRate:
    """Taux de change."""

    id: str
    base_currency: str  # Devise source (ex: EUR)
    target_currency: str  # Devise cible (ex: USD)
    rate: Decimal  # Taux (ex: 1.0850)
    inverse_rate: Decimal  # Taux inverse (ex: 0.9217)
    date: date  # Date du taux
    source: RateSource = RateSource.ECB
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CurrencyConversion:
    """Résultat de conversion."""

    id: str
    source_amount: Decimal
    source_currency: str
    target_amount: Decimal
    target_currency: str
    rate_used: Decimal
    rate_date: date
    rate_source: RateSource
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConversionResult:
    """Résultat complet de conversion."""

    success: bool
    conversion: Optional[CurrencyConversion] = None
    error: Optional[str] = None


@dataclass
class ExchangeGainLoss:
    """Gain ou perte de change."""

    original_amount: Decimal
    original_currency: str
    original_rate: Decimal
    current_rate: Decimal
    base_currency: str
    gain_loss: Decimal  # Positif = gain, Négatif = perte
    gain_loss_percent: Decimal


# =============================================================================
# DEVISES SUPPORTÉES
# =============================================================================


class SupportedCurrencies:
    """Devises supportées avec leurs informations."""

    CURRENCIES = {
        "EUR": {"name": "Euro", "symbol": "€", "decimals": 2},
        "USD": {"name": "Dollar américain", "symbol": "$", "decimals": 2},
        "GBP": {"name": "Livre sterling", "symbol": "£", "decimals": 2},
        "CHF": {"name": "Franc suisse", "symbol": "CHF", "decimals": 2},
        "JPY": {"name": "Yen japonais", "symbol": "¥", "decimals": 0},
        "CAD": {"name": "Dollar canadien", "symbol": "CA$", "decimals": 2},
        "AUD": {"name": "Dollar australien", "symbol": "A$", "decimals": 2},
        "CNY": {"name": "Yuan chinois", "symbol": "¥", "decimals": 2},
        "INR": {"name": "Roupie indienne", "symbol": "₹", "decimals": 2},
        "BRL": {"name": "Real brésilien", "symbol": "R$", "decimals": 2},
        "MXN": {"name": "Peso mexicain", "symbol": "MX$", "decimals": 2},
        "PLN": {"name": "Zloty polonais", "symbol": "zł", "decimals": 2},
        "SEK": {"name": "Couronne suédoise", "symbol": "kr", "decimals": 2},
        "NOK": {"name": "Couronne norvégienne", "symbol": "kr", "decimals": 2},
        "DKK": {"name": "Couronne danoise", "symbol": "kr", "decimals": 2},
        "CZK": {"name": "Couronne tchèque", "symbol": "Kč", "decimals": 2},
        "HUF": {"name": "Forint hongrois", "symbol": "Ft", "decimals": 0},
        "RON": {"name": "Leu roumain", "symbol": "lei", "decimals": 2},
        "BGN": {"name": "Lev bulgare", "symbol": "лв", "decimals": 2},
        "HRK": {"name": "Kuna croate", "symbol": "kn", "decimals": 2},
        "TRY": {"name": "Livre turque", "symbol": "₺", "decimals": 2},
        "RUB": {"name": "Rouble russe", "symbol": "₽", "decimals": 2},
        "ZAR": {"name": "Rand sud-africain", "symbol": "R", "decimals": 2},
        "MAD": {"name": "Dirham marocain", "symbol": "DH", "decimals": 2},
        "TND": {"name": "Dinar tunisien", "symbol": "DT", "decimals": 3},
        "XOF": {"name": "Franc CFA BCEAO", "symbol": "CFA", "decimals": 0},
        "XAF": {"name": "Franc CFA BEAC", "symbol": "FCFA", "decimals": 0},
    }

    @classmethod
    def is_supported(cls, currency: str) -> bool:
        """Vérifie si une devise est supportée."""
        return currency.upper() in cls.CURRENCIES

    @classmethod
    def get_info(cls, currency: str) -> Optional[dict]:
        """Retourne les informations d'une devise."""
        return cls.CURRENCIES.get(currency.upper())

    @classmethod
    def get_decimals(cls, currency: str) -> int:
        """Retourne le nombre de décimales pour une devise."""
        info = cls.get_info(currency)
        return info["decimals"] if info else 2


# =============================================================================
# TAUX PAR DÉFAUT (FALLBACK)
# =============================================================================


class DefaultRates:
    """Taux par défaut pour le fallback."""

    # Taux approximatifs EUR -> X (à mettre à jour régulièrement)
    EUR_RATES = {
        "USD": Decimal("1.0850"),
        "GBP": Decimal("0.8550"),
        "CHF": Decimal("0.9450"),
        "JPY": Decimal("162.50"),
        "CAD": Decimal("1.4750"),
        "AUD": Decimal("1.6550"),
        "CNY": Decimal("7.8500"),
        "INR": Decimal("90.50"),
        "BRL": Decimal("5.3500"),
        "MXN": Decimal("18.75"),
        "PLN": Decimal("4.3200"),
        "SEK": Decimal("11.45"),
        "NOK": Decimal("11.65"),
        "DKK": Decimal("7.4600"),
        "CZK": Decimal("25.35"),
        "HUF": Decimal("395.00"),
        "RON": Decimal("4.9750"),
        "BGN": Decimal("1.9560"),
        "TRY": Decimal("35.50"),
        "MAD": Decimal("10.85"),
        "XOF": Decimal("655.957"),  # Parité fixe
        "XAF": Decimal("655.957"),  # Parité fixe
    }


# =============================================================================
# SERVICE PRINCIPAL
# =============================================================================


class CurrencyService:
    """
    Service de gestion des devises et taux de change.

    Fournit:
    - Récupération des taux de change (BCE ou fallback)
    - Conversion entre devises
    - Historique des taux
    - Calcul des gains/pertes de change

    Usage:
        service = CurrencyService(db, tenant_id)

        # Obtenir un taux
        rate = await service.get_rate("USD", "EUR")

        # Convertir un montant
        result = await service.convert(
            amount=Decimal("1000"),
            from_currency="USD",
            to_currency="EUR"
        )
    """

    # Devise de base par défaut
    BASE_CURRENCY = "EUR"

    # Cache TTL en minutes
    CACHE_TTL_MINUTES = 60

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        base_currency: str = "EUR",
    ):
        """
        Initialise le service de devises.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant (obligatoire)
            base_currency: Devise de base (défaut: EUR)
        """
        if not tenant_id:
            raise ValueError("tenant_id est obligatoire")

        self.db = db
        self.tenant_id = tenant_id
        self.base_currency = base_currency.upper()

        # Cache des taux
        self._rates_cache: Dict[str, ExchangeRate] = {}
        self._cache_timestamp: Optional[datetime] = None

        self._logger = logging.LoggerAdapter(
            logger,
            extra={"tenant_id": tenant_id, "service": "CurrencyService"},
        )

    # =========================================================================
    # RÉCUPÉRATION DES TAUX
    # =========================================================================

    async def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate_date: Optional[date] = None,
    ) -> Optional[ExchangeRate]:
        """
        Récupère le taux de change entre deux devises.

        Args:
            from_currency: Devise source
            to_currency: Devise cible
            rate_date: Date du taux (défaut: aujourd'hui)

        Returns:
            ExchangeRate ou None si non trouvé
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        rate_date = rate_date or date.today()

        # Même devise = taux 1
        if from_currency == to_currency:
            return ExchangeRate(
                id=str(uuid4()),
                base_currency=from_currency,
                target_currency=to_currency,
                rate=Decimal("1"),
                inverse_rate=Decimal("1"),
                date=rate_date,
                source=RateSource.CACHE,
            )

        # Vérifier le cache
        cache_key = f"{from_currency}_{to_currency}"
        if self._is_cache_valid() and cache_key in self._rates_cache:
            cached = self._rates_cache[cache_key]
            if cached.date == rate_date:
                return cached

        # Essayer de récupérer depuis l'API BCE
        rate = await self._fetch_ecb_rate(from_currency, to_currency, rate_date)

        if rate:
            self._rates_cache[cache_key] = rate
            return rate

        # Fallback sur les taux par défaut
        return self._get_fallback_rate(from_currency, to_currency, rate_date)

    async def get_rates_for_date(
        self,
        rate_date: date,
        currencies: Optional[list[str]] = None,
    ) -> list[ExchangeRate]:
        """
        Récupère tous les taux pour une date.

        Args:
            rate_date: Date des taux
            currencies: Liste de devises (défaut: toutes)

        Returns:
            Liste de ExchangeRate
        """
        if currencies is None:
            currencies = list(SupportedCurrencies.CURRENCIES.keys())

        rates = []
        for currency in currencies:
            if currency != self.base_currency:
                rate = await self.get_rate(self.base_currency, currency, rate_date)
                if rate:
                    rates.append(rate)

        return rates

    async def _fetch_ecb_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate_date: date,
    ) -> Optional[ExchangeRate]:
        """Récupère un taux depuis l'API BCE."""
        # NOTE: Phase 2 - Appel API BCE eurofxref-daily.xml
        return None

    def _get_fallback_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate_date: date,
    ) -> Optional[ExchangeRate]:
        """Retourne un taux de fallback."""
        rate = None

        if from_currency == "EUR" and to_currency in DefaultRates.EUR_RATES:
            rate = DefaultRates.EUR_RATES[to_currency]
        elif to_currency == "EUR" and from_currency in DefaultRates.EUR_RATES:
            rate = Decimal("1") / DefaultRates.EUR_RATES[from_currency]
        elif from_currency in DefaultRates.EUR_RATES and to_currency in DefaultRates.EUR_RATES:
            # Cross rate via EUR
            rate_from = DefaultRates.EUR_RATES[from_currency]
            rate_to = DefaultRates.EUR_RATES[to_currency]
            rate = rate_to / rate_from

        if rate is None:
            return None

        return ExchangeRate(
            id=str(uuid4()),
            base_currency=from_currency,
            target_currency=to_currency,
            rate=rate.quantize(Decimal("0.000001")),
            inverse_rate=(Decimal("1") / rate).quantize(Decimal("0.000001")),
            date=rate_date,
            source=RateSource.FALLBACK,
        )

    def _is_cache_valid(self) -> bool:
        """Vérifie si le cache est encore valide."""
        if not self._cache_timestamp:
            return False
        age = datetime.utcnow() - self._cache_timestamp
        return age.total_seconds() < self.CACHE_TTL_MINUTES * 60

    # =========================================================================
    # CONVERSION
    # =========================================================================

    async def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        rate_date: Optional[date] = None,
        rounding: RoundingMode = RoundingMode.HALF_UP,
    ) -> ConversionResult:
        """
        Convertit un montant d'une devise à une autre.

        Args:
            amount: Montant à convertir
            from_currency: Devise source
            to_currency: Devise cible
            rate_date: Date du taux (défaut: aujourd'hui)
            rounding: Mode d'arrondi

        Returns:
            ConversionResult
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        rate_date = rate_date or date.today()

        self._logger.info(
            f"Conversion: {amount} {from_currency} -> {to_currency}",
            extra={"amount": str(amount), "from": from_currency, "to": to_currency},
        )

        try:
            # Validation devises
            if not SupportedCurrencies.is_supported(from_currency):
                return ConversionResult(
                    success=False,
                    error=f"Devise non supportée: {from_currency}",
                )

            if not SupportedCurrencies.is_supported(to_currency):
                return ConversionResult(
                    success=False,
                    error=f"Devise non supportée: {to_currency}",
                )

            # Récupérer le taux
            rate = await self.get_rate(from_currency, to_currency, rate_date)
            if not rate:
                return ConversionResult(
                    success=False,
                    error=f"Taux non disponible pour {from_currency}/{to_currency}",
                )

            # Calculer le montant converti
            converted = amount * rate.rate

            # Arrondir selon le nombre de décimales de la devise cible
            decimals = SupportedCurrencies.get_decimals(to_currency)
            quantize_str = "0." + "0" * decimals if decimals > 0 else "1"
            converted = converted.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)

            conversion = CurrencyConversion(
                id=str(uuid4()),
                source_amount=amount,
                source_currency=from_currency,
                target_amount=converted,
                target_currency=to_currency,
                rate_used=rate.rate,
                rate_date=rate_date,
                rate_source=rate.source,
            )

            return ConversionResult(success=True, conversion=conversion)

        except Exception as e:
            self._logger.error(f"Erreur conversion: {e}", exc_info=True)
            return ConversionResult(success=False, error=str(e))

    async def convert_batch(
        self,
        conversions: list[dict],
    ) -> list[ConversionResult]:
        """
        Convertit plusieurs montants.

        Args:
            conversions: Liste de dict avec amount, from_currency, to_currency

        Returns:
            Liste de ConversionResult
        """
        results = []
        for conv in conversions:
            result = await self.convert(
                amount=Decimal(str(conv["amount"])),
                from_currency=conv["from_currency"],
                to_currency=conv["to_currency"],
                rate_date=conv.get("rate_date"),
            )
            results.append(result)
        return results

    # =========================================================================
    # GAINS/PERTES DE CHANGE
    # =========================================================================

    async def calculate_exchange_gain_loss(
        self,
        original_amount: Decimal,
        original_currency: str,
        original_rate: Decimal,
        current_date: Optional[date] = None,
    ) -> Optional[ExchangeGainLoss]:
        """
        Calcule le gain ou la perte de change.

        Args:
            original_amount: Montant original
            original_currency: Devise originale
            original_rate: Taux au moment de l'opération
            current_date: Date de calcul (défaut: aujourd'hui)

        Returns:
            ExchangeGainLoss ou None
        """
        current_date = current_date or date.today()
        original_currency = original_currency.upper()

        # Récupérer le taux actuel
        current_rate_obj = await self.get_rate(
            original_currency,
            self.base_currency,
            current_date,
        )

        if not current_rate_obj:
            return None

        current_rate = current_rate_obj.rate

        # Calculer les valeurs en devise de base
        original_base_value = original_amount * original_rate
        current_base_value = original_amount * current_rate

        # Gain/perte
        gain_loss = current_base_value - original_base_value

        # Pourcentage
        if original_base_value != 0:
            gain_loss_percent = (gain_loss / original_base_value) * 100
        else:
            gain_loss_percent = Decimal("0")

        return ExchangeGainLoss(
            original_amount=original_amount,
            original_currency=original_currency,
            original_rate=original_rate,
            current_rate=current_rate,
            base_currency=self.base_currency,
            gain_loss=gain_loss.quantize(Decimal("0.01")),
            gain_loss_percent=gain_loss_percent.quantize(Decimal("0.01")),
        )

    # =========================================================================
    # GESTION DES TAUX MANUELS
    # =========================================================================

    async def set_manual_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate: Decimal,
        rate_date: Optional[date] = None,
    ) -> ExchangeRate:
        """
        Définit un taux de change manuel.

        Args:
            from_currency: Devise source
            to_currency: Devise cible
            rate: Taux de change
            rate_date: Date du taux

        Returns:
            ExchangeRate créé
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        rate_date = rate_date or date.today()

        exchange_rate = ExchangeRate(
            id=str(uuid4()),
            base_currency=from_currency,
            target_currency=to_currency,
            rate=rate,
            inverse_rate=(Decimal("1") / rate).quantize(Decimal("0.000001")),
            date=rate_date,
            source=RateSource.MANUAL,
        )

        # Mettre en cache
        cache_key = f"{from_currency}_{to_currency}"
        self._rates_cache[cache_key] = exchange_rate
        self._cache_timestamp = datetime.utcnow()

        self._logger.info(
            f"Taux manuel défini: {from_currency}/{to_currency} = {rate}",
            extra={"rate": str(rate), "date": rate_date.isoformat()},
        )

        return exchange_rate

    # =========================================================================
    # INFORMATIONS DEVISES
    # =========================================================================

    def get_supported_currencies(self) -> list[dict]:
        """Retourne la liste des devises supportées."""
        return [
            {
                "code": code,
                "name": info["name"],
                "symbol": info["symbol"],
                "decimals": info["decimals"],
            }
            for code, info in SupportedCurrencies.CURRENCIES.items()
        ]

    def get_currency_info(self, currency: str) -> Optional[dict]:
        """Retourne les informations d'une devise."""
        info = SupportedCurrencies.get_info(currency)
        if info:
            return {
                "code": currency.upper(),
                "name": info["name"],
                "symbol": info["symbol"],
                "decimals": info["decimals"],
            }
        return None

    def format_amount(
        self,
        amount: Decimal,
        currency: str,
        include_symbol: bool = True,
    ) -> str:
        """
        Formate un montant avec sa devise.

        Args:
            amount: Montant
            currency: Code devise
            include_symbol: Inclure le symbole

        Returns:
            Montant formaté
        """
        info = SupportedCurrencies.get_info(currency)
        if not info:
            return f"{amount} {currency}"

        decimals = info["decimals"]
        quantize_str = "0." + "0" * decimals if decimals > 0 else "1"
        formatted = amount.quantize(Decimal(quantize_str))

        if include_symbol:
            symbol = info["symbol"]
            # Position du symbole (avant ou après)
            if currency in ["EUR", "GBP", "USD", "JPY", "CNY", "INR"]:
                return f"{symbol}{formatted}"
            else:
                return f"{formatted} {symbol}"
        else:
            return str(formatted)
