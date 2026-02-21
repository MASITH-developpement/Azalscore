"""
AZALS MODULE - BUDGET: Exceptions
==================================

Exceptions personnalisees pour le module de gestion budgetaire.

Auteur: AZALSCORE Team
Version: 2.0.0
"""

from typing import Any, Dict, Optional
from uuid import UUID


class BudgetException(Exception):
    """Exception de base pour le module budget."""

    def __init__(
        self,
        message: str,
        code: str = "BUDGET_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class BudgetNotFoundError(BudgetException):
    """Budget non trouve."""

    def __init__(self, budget_id: UUID, message: Optional[str] = None):
        super().__init__(
            message=message or f"Budget non trouve: {budget_id}",
            code="BUDGET_NOT_FOUND",
            details={"budget_id": str(budget_id)}
        )


class BudgetLineNotFoundError(BudgetException):
    """Ligne de budget non trouvee."""

    def __init__(self, line_id: UUID, message: Optional[str] = None):
        super().__init__(
            message=message or f"Ligne de budget non trouvee: {line_id}",
            code="BUDGET_LINE_NOT_FOUND",
            details={"line_id": str(line_id)}
        )


class BudgetCategoryNotFoundError(BudgetException):
    """Categorie budgetaire non trouvee."""

    def __init__(self, category_id: UUID, message: Optional[str] = None):
        super().__init__(
            message=message or f"Categorie budgetaire non trouvee: {category_id}",
            code="BUDGET_CATEGORY_NOT_FOUND",
            details={"category_id": str(category_id)}
        )


class BudgetRevisionNotFoundError(BudgetException):
    """Revision budgetaire non trouvee."""

    def __init__(self, revision_id: UUID, message: Optional[str] = None):
        super().__init__(
            message=message or f"Revision budgetaire non trouvee: {revision_id}",
            code="BUDGET_REVISION_NOT_FOUND",
            details={"revision_id": str(revision_id)}
        )


class BudgetAlreadyExistsError(BudgetException):
    """Budget deja existant."""

    def __init__(self, code: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Un budget avec le code '{code}' existe deja",
            code="BUDGET_ALREADY_EXISTS",
            details={"budget_code": code}
        )


class BudgetStatusError(BudgetException):
    """Erreur de statut du budget."""

    def __init__(
        self,
        budget_id: UUID,
        current_status: str,
        expected_status: str,
        action: str,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or (
                f"Impossible d'effectuer l'action '{action}' sur le budget {budget_id}. "
                f"Statut actuel: {current_status}, attendu: {expected_status}"
            ),
            code="BUDGET_STATUS_ERROR",
            details={
                "budget_id": str(budget_id),
                "current_status": current_status,
                "expected_status": expected_status,
                "action": action
            }
        )


class BudgetNotModifiableError(BudgetException):
    """Budget non modifiable."""

    def __init__(self, budget_id: UUID, status: str, message: Optional[str] = None):
        super().__init__(
            message=message or (
                f"Le budget {budget_id} n'est pas modifiable "
                f"(statut actuel: {status})"
            ),
            code="BUDGET_NOT_MODIFIABLE",
            details={"budget_id": str(budget_id), "status": status}
        )


class BudgetPeriodLockedError(BudgetException):
    """Periode budgetaire verrouillee."""

    def __init__(
        self,
        budget_id: UUID,
        period: str,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"La periode {period} du budget {budget_id} est verrouillee",
            code="BUDGET_PERIOD_LOCKED",
            details={"budget_id": str(budget_id), "period": period}
        )


class BudgetControlViolationError(BudgetException):
    """Violation du controle budgetaire."""

    def __init__(
        self,
        budget_id: UUID,
        budget_line_id: Optional[UUID],
        requested_amount: float,
        available_amount: float,
        threshold_exceeded: str,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or (
                f"Depassement budgetaire detecte. "
                f"Montant demande: {requested_amount}, "
                f"Disponible: {available_amount}"
            ),
            code="BUDGET_CONTROL_VIOLATION",
            details={
                "budget_id": str(budget_id),
                "budget_line_id": str(budget_line_id) if budget_line_id else None,
                "requested_amount": requested_amount,
                "available_amount": available_amount,
                "threshold_exceeded": threshold_exceeded
            }
        )


class BudgetControlWarning(BudgetException):
    """Avertissement de controle budgetaire."""

    def __init__(
        self,
        budget_id: UUID,
        consumption_percent: float,
        threshold_percent: float,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or (
                f"Seuil d'alerte budgetaire atteint: "
                f"{consumption_percent:.1f}% (seuil: {threshold_percent:.1f}%)"
            ),
            code="BUDGET_CONTROL_WARNING",
            details={
                "budget_id": str(budget_id),
                "consumption_percent": consumption_percent,
                "threshold_percent": threshold_percent
            }
        )


class BudgetWorkflowError(BudgetException):
    """Erreur de workflow budgetaire."""

    def __init__(
        self,
        action: str,
        reason: str,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Erreur de workflow ({action}): {reason}",
            code="BUDGET_WORKFLOW_ERROR",
            details={"action": action, "reason": reason}
        )


class BudgetApprovalError(BudgetException):
    """Erreur d'approbation budgetaire."""

    def __init__(
        self,
        budget_id: UUID,
        reason: str,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Erreur d'approbation du budget {budget_id}: {reason}",
            code="BUDGET_APPROVAL_ERROR",
            details={"budget_id": str(budget_id), "reason": reason}
        )


class BudgetRevisionError(BudgetException):
    """Erreur de revision budgetaire."""

    def __init__(
        self,
        budget_id: UUID,
        revision_id: Optional[UUID],
        reason: str,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Erreur de revision: {reason}",
            code="BUDGET_REVISION_ERROR",
            details={
                "budget_id": str(budget_id),
                "revision_id": str(revision_id) if revision_id else None,
                "reason": reason
            }
        )


class BudgetCalculationError(BudgetException):
    """Erreur de calcul budgetaire."""

    def __init__(self, reason: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Erreur de calcul budgetaire: {reason}",
            code="BUDGET_CALCULATION_ERROR",
            details={"reason": reason}
        )


class BudgetImportError(BudgetException):
    """Erreur d'import de budget."""

    def __init__(
        self,
        line_number: Optional[int],
        reason: str,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or (
                f"Erreur d'import ligne {line_number}: {reason}"
                if line_number else f"Erreur d'import: {reason}"
            ),
            code="BUDGET_IMPORT_ERROR",
            details={"line_number": line_number, "reason": reason}
        )


class BudgetExportError(BudgetException):
    """Erreur d'export de budget."""

    def __init__(self, reason: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Erreur d'export: {reason}",
            code="BUDGET_EXPORT_ERROR",
            details={"reason": reason}
        )


class BudgetConsolidationError(BudgetException):
    """Erreur de consolidation budgetaire."""

    def __init__(self, reason: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Erreur de consolidation: {reason}",
            code="BUDGET_CONSOLIDATION_ERROR",
            details={"reason": reason}
        )


class BudgetScenarioError(BudgetException):
    """Erreur de scenario budgetaire."""

    def __init__(
        self,
        scenario_id: Optional[UUID],
        reason: str,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Erreur de scenario: {reason}",
            code="BUDGET_SCENARIO_ERROR",
            details={
                "scenario_id": str(scenario_id) if scenario_id else None,
                "reason": reason
            }
        )


class BudgetValidationError(BudgetException):
    """Erreur de validation des donnees budgetaires."""

    def __init__(
        self,
        field: str,
        reason: str,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Erreur de validation ({field}): {reason}",
            code="BUDGET_VALIDATION_ERROR",
            details={"field": field, "reason": reason}
        )


class InsufficientBudgetError(BudgetException):
    """Budget insuffisant."""

    def __init__(
        self,
        budget_id: UUID,
        budget_line_id: Optional[UUID],
        required: float,
        available: float,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or (
                f"Budget insuffisant. Requis: {required}, Disponible: {available}"
            ),
            code="INSUFFICIENT_BUDGET",
            details={
                "budget_id": str(budget_id),
                "budget_line_id": str(budget_line_id) if budget_line_id else None,
                "required": required,
                "available": available
            }
        )


class BudgetPermissionError(BudgetException):
    """Erreur de permission budgetaire."""

    def __init__(
        self,
        action: str,
        user_id: Optional[UUID],
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Permission refusee pour l'action: {action}",
            code="BUDGET_PERMISSION_ERROR",
            details={
                "action": action,
                "user_id": str(user_id) if user_id else None
            }
        )


class OptimisticLockError(BudgetException):
    """Erreur de conflit de version (optimistic locking)."""

    def __init__(
        self,
        entity_type: str,
        entity_id: UUID,
        expected_version: int,
        actual_version: int,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or (
                f"Conflit de version sur {entity_type} {entity_id}. "
                f"Version attendue: {expected_version}, actuelle: {actual_version}"
            ),
            code="OPTIMISTIC_LOCK_ERROR",
            details={
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "expected_version": expected_version,
                "actual_version": actual_version
            }
        )
