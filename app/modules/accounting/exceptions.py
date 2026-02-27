"""
AZALS MODULE ACCOUNTING - Exceptions
=====================================

Exceptions metier specifiques au module de comptabilite.
"""

from typing import Optional, List
from uuid import UUID


class AccountingError(Exception):
    """Exception de base du module Accounting."""

    def __init__(self, message: str, tenant_id: Optional[UUID] = None):
        self.message = message
        self.tenant_id = tenant_id
        super().__init__(self.message)


# ============================================================================
# FISCAL YEAR ERRORS
# ============================================================================

class FiscalYearNotFoundError(AccountingError):
    """Exercice fiscal non trouve."""

    def __init__(self, fiscal_year_id: Optional[str] = None, message: Optional[str] = None):
        self.fiscal_year_id = fiscal_year_id
        msg = message or f"Exercice fiscal {fiscal_year_id} non trouve"
        super().__init__(msg)


class FiscalYearClosedError(AccountingError):
    """Exercice fiscal clos, modifications interdites."""

    def __init__(self, fiscal_year_id: Optional[str] = None, message: Optional[str] = None):
        self.fiscal_year_id = fiscal_year_id
        msg = message or f"L'exercice fiscal {fiscal_year_id} est clos"
        super().__init__(msg)


class FiscalYearOverlapError(AccountingError):
    """Chevauchement de dates entre exercices fiscaux."""

    def __init__(self, start_date: str, end_date: str, message: Optional[str] = None):
        self.start_date = start_date
        self.end_date = end_date
        msg = message or f"Chevauchement detecte pour la periode {start_date} - {end_date}"
        super().__init__(msg)


# ============================================================================
# ACCOUNT ERRORS
# ============================================================================

class AccountNotFoundError(AccountingError):
    """Compte comptable non trouve."""

    def __init__(self, account_id: Optional[str] = None, account_code: Optional[str] = None):
        self.account_id = account_id
        self.account_code = account_code
        identifier = account_code or account_id
        super().__init__(f"Compte comptable {identifier} non trouve")


class AccountCodeDuplicateError(AccountingError):
    """Code de compte deja existant."""

    def __init__(self, account_code: str):
        self.account_code = account_code
        super().__init__(f"Le code de compte {account_code} existe deja")


class AccountNotEditableError(AccountingError):
    """Compte non modifiable (mouvements existants)."""

    def __init__(self, account_code: str, reason: Optional[str] = None):
        self.account_code = account_code
        self.reason = reason
        msg = f"Le compte {account_code} n'est pas modifiable"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class AccountTypeError(AccountingError):
    """Type de compte invalide pour l'operation."""

    def __init__(self, account_code: str, expected_type: str, actual_type: str):
        self.account_code = account_code
        self.expected_type = expected_type
        self.actual_type = actual_type
        super().__init__(
            f"Le compte {account_code} est de type {actual_type}, "
            f"attendu: {expected_type}"
        )


# ============================================================================
# JOURNAL ENTRY ERRORS
# ============================================================================

class JournalEntryNotFoundError(AccountingError):
    """Ecriture comptable non trouvee."""

    def __init__(self, entry_id: Optional[str] = None, entry_number: Optional[str] = None):
        self.entry_id = entry_id
        self.entry_number = entry_number
        identifier = entry_number or entry_id
        super().__init__(f"Ecriture comptable {identifier} non trouvee")


class JournalEntryValidationError(AccountingError):
    """Erreur de validation de l'ecriture comptable."""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        self.errors = errors or []
        super().__init__(message)


class JournalEntryUnbalancedError(AccountingError):
    """Ecriture comptable non equilibree."""

    def __init__(self, debit_total: str, credit_total: str):
        self.debit_total = debit_total
        self.credit_total = credit_total
        super().__init__(
            f"L'ecriture n'est pas equilibree: "
            f"debit={debit_total}, credit={credit_total}"
        )


class JournalEntryLockedError(AccountingError):
    """Ecriture comptable verrouillee."""

    def __init__(self, entry_number: Optional[str] = None, reason: Optional[str] = None):
        self.entry_number = entry_number
        self.reason = reason
        msg = f"L'ecriture {entry_number} est verrouillee"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class JournalEntryStateError(AccountingError):
    """Transition d'etat invalide pour l'ecriture."""

    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Transition impossible de {current_status} vers {target_status}"
        )


# ============================================================================
# CACHE ERRORS (pour gestion specifique du cache)
# ============================================================================

class AccountingCacheError(AccountingError):
    """Erreur de cache non critique."""
    pass
