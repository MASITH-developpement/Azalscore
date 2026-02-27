"""
AZALS MODULE TREASURY - Exceptions
===================================

Exceptions metier specifiques au module de tresorerie.
"""

from typing import Optional
from uuid import UUID
from decimal import Decimal


class TreasuryError(Exception):
    """Exception de base du module Treasury."""

    def __init__(self, message: str, tenant_id: Optional[UUID] = None):
        self.message = message
        self.tenant_id = tenant_id
        super().__init__(self.message)


# ============================================================================
# BANK ACCOUNT ERRORS
# ============================================================================

class BankAccountNotFoundError(TreasuryError):
    """Compte bancaire non trouve."""

    def __init__(self, account_id: Optional[str] = None, iban: Optional[str] = None):
        self.account_id = account_id
        self.iban = iban
        identifier = iban or account_id
        super().__init__(f"Compte bancaire {identifier} non trouve")


class BankAccountInactiveError(TreasuryError):
    """Compte bancaire inactif."""

    def __init__(self, account_id: str):
        self.account_id = account_id
        super().__init__(f"Le compte bancaire {account_id} est inactif")


class BankAccountDuplicateError(TreasuryError):
    """IBAN deja enregistre."""

    def __init__(self, iban: str):
        self.iban = iban
        super().__init__(f"L'IBAN {iban} est deja enregistre")


# ============================================================================
# TRANSACTION ERRORS
# ============================================================================

class TransactionNotFoundError(TreasuryError):
    """Transaction non trouvee."""

    def __init__(self, transaction_id: Optional[str] = None):
        self.transaction_id = transaction_id
        super().__init__(f"Transaction {transaction_id} non trouvee")


class TransactionAlreadyReconciledError(TreasuryError):
    """Transaction deja rapprochee."""

    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id
        super().__init__(f"La transaction {transaction_id} est deja rapprochee")


class TransactionAmountMismatchError(TreasuryError):
    """Montant de transaction ne correspond pas."""

    def __init__(self, expected: Decimal, actual: Decimal):
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Montant incorrect: attendu={expected}, reel={actual}"
        )


# ============================================================================
# RECONCILIATION ERRORS
# ============================================================================

class ReconciliationNotFoundError(TreasuryError):
    """Rapprochement non trouve."""

    def __init__(self, reconciliation_id: Optional[str] = None):
        self.reconciliation_id = reconciliation_id
        super().__init__(f"Rapprochement {reconciliation_id} non trouve")


class ReconciliationUnbalancedError(TreasuryError):
    """Rapprochement non equilibre."""

    def __init__(self, difference: Decimal):
        self.difference = difference
        super().__init__(f"Rapprochement non equilibre: ecart={difference}")


class ReconciliationAlreadyClosedError(TreasuryError):
    """Rapprochement deja cloture."""

    def __init__(self, reconciliation_id: str):
        self.reconciliation_id = reconciliation_id
        super().__init__(f"Le rapprochement {reconciliation_id} est deja cloture")


# ============================================================================
# FORECAST ERRORS
# ============================================================================

class ForecastCalculationError(TreasuryError):
    """Erreur lors du calcul des previsions."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Erreur de calcul des previsions: {reason}")


# ============================================================================
# CACHE ERRORS
# ============================================================================

class TreasuryCacheError(TreasuryError):
    """Erreur de cache non critique."""
    pass
