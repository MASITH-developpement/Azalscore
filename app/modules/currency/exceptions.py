"""
AZALS MODULE - CURRENCY: Exceptions
===================================

Exceptions metier pour la gestion multi-devises.
"""


class CurrencyError(Exception):
    """Exception de base du module Currency."""
    pass


# ============================================================================
# CURRENCY EXCEPTIONS
# ============================================================================

class CurrencyNotFoundError(CurrencyError):
    """Devise non trouvee."""
    def __init__(self, currency_code: str = None, currency_id: str = None):
        self.currency_code = currency_code
        self.currency_id = currency_id
        message = f"Devise non trouvee: {currency_code or currency_id}"
        super().__init__(message)


class CurrencyAlreadyExistsError(CurrencyError):
    """Devise deja existante."""
    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        super().__init__(f"La devise {currency_code} existe deja")


class CurrencyDisabledError(CurrencyError):
    """Devise desactivee."""
    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        super().__init__(f"La devise {currency_code} est desactivee")


class CurrencyValidationError(CurrencyError):
    """Erreur de validation devise."""
    pass


class InvalidCurrencyCodeError(CurrencyError):
    """Code devise invalide."""
    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        super().__init__(f"Code devise invalide: {currency_code}")


class DefaultCurrencyCannotBeDisabledError(CurrencyError):
    """La devise par defaut ne peut etre desactivee."""
    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        super().__init__(f"Impossible de desactiver la devise par defaut: {currency_code}")


class ReportingCurrencyCannotBeDisabledError(CurrencyError):
    """La devise de reporting ne peut etre desactivee."""
    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        super().__init__(f"Impossible de desactiver la devise de reporting: {currency_code}")


# ============================================================================
# EXCHANGE RATE EXCEPTIONS
# ============================================================================

class ExchangeRateNotFoundError(CurrencyError):
    """Taux de change non trouve."""
    def __init__(self, base: str = None, quote: str = None, rate_date: str = None):
        self.base = base
        self.quote = quote
        self.rate_date = rate_date
        message = f"Taux de change non trouve: {base}/{quote}"
        if rate_date:
            message += f" au {rate_date}"
        super().__init__(message)


class ExchangeRateAlreadyExistsError(CurrencyError):
    """Taux de change deja existant."""
    def __init__(self, base: str, quote: str, rate_date: str):
        self.base = base
        self.quote = quote
        self.rate_date = rate_date
        super().__init__(f"Taux {base}/{quote} deja existant pour le {rate_date}")


class ExchangeRateLockedError(CurrencyError):
    """Taux de change verrouille."""
    def __init__(self, rate_id: str = None):
        self.rate_id = rate_id
        super().__init__("Ce taux de change est verrouille et ne peut etre modifie")


class InvalidExchangeRateError(CurrencyError):
    """Taux de change invalide."""
    def __init__(self, message: str = "Taux de change invalide"):
        super().__init__(message)


class SameCurrencyConversionError(CurrencyError):
    """Tentative de conversion vers la meme devise."""
    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        super().__init__(f"Conversion impossible: meme devise source et cible ({currency_code})")


class RateToleranceExceededError(CurrencyError):
    """Variation de taux depassant le seuil de tolerance."""
    def __init__(self, old_rate: str, new_rate: str, variation: str, threshold: str):
        self.old_rate = old_rate
        self.new_rate = new_rate
        self.variation = variation
        self.threshold = threshold
        super().__init__(
            f"Variation de taux ({variation}%) depasse le seuil ({threshold}%): "
            f"{old_rate} -> {new_rate}"
        )


# ============================================================================
# CONVERSION EXCEPTIONS
# ============================================================================

class ConversionError(CurrencyError):
    """Erreur de conversion."""
    pass


class NoConversionPathError(CurrencyError):
    """Aucun chemin de conversion trouve."""
    def __init__(self, from_currency: str, to_currency: str):
        self.from_currency = from_currency
        self.to_currency = to_currency
        super().__init__(
            f"Aucun chemin de conversion trouve entre {from_currency} et {to_currency}"
        )


class TriangulationFailedError(CurrencyError):
    """Echec de la triangulation."""
    def __init__(self, from_currency: str, to_currency: str, pivot: str):
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.pivot = pivot
        super().__init__(
            f"Echec triangulation {from_currency} -> {pivot} -> {to_currency}"
        )


class RoundingError(CurrencyError):
    """Erreur d'arrondi."""
    pass


# ============================================================================
# GAIN/LOSS EXCEPTIONS
# ============================================================================

class GainLossNotFoundError(CurrencyError):
    """Gain/perte non trouve."""
    pass


class GainLossAlreadyPostedError(CurrencyError):
    """Gain/perte deja comptabilise."""
    def __init__(self, gain_loss_id: str):
        self.gain_loss_id = gain_loss_id
        super().__init__("Ce gain/perte de change est deja comptabilise")


class GainLossValidationError(CurrencyError):
    """Erreur de validation gain/perte."""
    pass


# ============================================================================
# REVALUATION EXCEPTIONS
# ============================================================================

class RevaluationNotFoundError(CurrencyError):
    """Reevaluation non trouvee."""
    pass


class RevaluationAlreadyExistsError(CurrencyError):
    """Reevaluation deja existante pour la periode."""
    def __init__(self, period: str):
        self.period = period
        super().__init__(f"Une reevaluation existe deja pour la periode {period}")


class RevaluationAlreadyPostedError(CurrencyError):
    """Reevaluation deja comptabilisee."""
    pass


class RevaluationCancelledError(CurrencyError):
    """Reevaluation annulee."""
    pass


class RevaluationValidationError(CurrencyError):
    """Erreur de validation reevaluation."""
    pass


class NoItemsToRevalueError(CurrencyError):
    """Aucun element a reevaluer."""
    pass


# ============================================================================
# API EXCEPTIONS
# ============================================================================

class RateAPIError(CurrencyError):
    """Erreur API taux de change."""
    def __init__(self, source: str, message: str, status_code: int = None):
        self.source = source
        self.status_code = status_code
        super().__init__(f"Erreur API {source}: {message}")


class RateAPIQuotaExceededError(RateAPIError):
    """Quota API depasse."""
    def __init__(self, source: str):
        super().__init__(source, "Quota API depasse")


class RateAPIAuthenticationError(RateAPIError):
    """Erreur authentification API."""
    def __init__(self, source: str):
        super().__init__(source, "Erreur d'authentification")


class RateAPIUnavailableError(RateAPIError):
    """API indisponible."""
    def __init__(self, source: str):
        super().__init__(source, "Service temporairement indisponible")


# ============================================================================
# CONFIG EXCEPTIONS
# ============================================================================

class ConfigNotFoundError(CurrencyError):
    """Configuration non trouvee."""
    pass


class ConfigAlreadyExistsError(CurrencyError):
    """Configuration deja existante pour ce tenant."""
    pass


class InvalidConfigError(CurrencyError):
    """Configuration invalide."""
    pass


# ============================================================================
# AUTHORIZATION EXCEPTIONS
# ============================================================================

class CurrencyPermissionDeniedError(CurrencyError):
    """Permission refusee."""
    def __init__(self, action: str):
        self.action = action
        super().__init__(f"Permission refusee pour l'action: {action}")


class RateApprovalRequiredError(CurrencyError):
    """Approbation requise pour ce taux."""
    pass
