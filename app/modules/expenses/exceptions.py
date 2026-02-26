"""
Exceptions métier - Module Expenses (GAP-084)
"""


class ExpenseError(Exception):
    """Exception de base du module Expenses."""
    pass


class ExpenseReportNotFoundError(ExpenseError):
    """Note de frais non trouvée."""
    pass


class ExpenseReportDuplicateError(ExpenseError):
    """Code note de frais déjà existant."""
    pass


class ExpenseReportValidationError(ExpenseError):
    """Erreur de validation note de frais."""
    pass


class ExpenseReportStateError(ExpenseError):
    """Transition d'état invalide."""
    pass


class ExpenseReportAlreadySubmittedError(ExpenseError):
    """Note de frais déjà soumise."""
    pass


class ExpenseReportNotEditableError(ExpenseError):
    """Note de frais non modifiable."""
    pass


class ExpenseLineNotFoundError(ExpenseError):
    """Ligne de dépense non trouvée."""
    pass


class ExpenseLineValidationError(ExpenseError):
    """Erreur de validation ligne de dépense."""
    pass


class PolicyNotFoundError(ExpenseError):
    """Politique non trouvée."""
    pass


class PolicyDuplicateError(ExpenseError):
    """Code politique déjà existant."""
    pass


class PolicyViolationError(ExpenseError):
    """Violation de politique de dépenses."""
    pass


class ReceiptRequiredError(ExpenseError):
    """Justificatif requis."""
    pass


class MileageCalculationError(ExpenseError):
    """Erreur calcul kilométrique."""
    pass


class ApprovalNotAuthorizedError(ExpenseError):
    """Non autorisé à approuver."""
    pass


class ExportError(ExpenseError):
    """Erreur d'export comptable."""
    pass
