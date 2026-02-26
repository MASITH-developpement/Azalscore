"""
Exceptions metier - Module Commissions (GAP-041)

Exceptions specifiques au module de gestion des commissions.
"""


class CommissionError(Exception):
    """Exception de base du module Commissions."""

    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code or "COMMISSION_ERROR"
        self.details = details or {}


# ============================================================================
# EXCEPTIONS PLANS
# ============================================================================

class PlanNotFoundError(CommissionError):
    """Plan de commission non trouve."""

    def __init__(self, plan_id: str = None, code: str = None):
        message = f"Plan de commission non trouve"
        if plan_id:
            message = f"Plan de commission '{plan_id}' non trouve"
        if code:
            message = f"Plan de commission avec code '{code}' non trouve"
        super().__init__(message, "PLAN_NOT_FOUND")


class PlanDuplicateError(CommissionError):
    """Code plan deja existant."""

    def __init__(self, code: str):
        super().__init__(
            f"Un plan avec le code '{code}' existe deja",
            "PLAN_DUPLICATE"
        )


class PlanInvalidStateError(CommissionError):
    """Etat du plan invalide pour l'operation."""

    def __init__(self, current_state: str, required_states: list = None):
        message = f"Plan dans un etat invalide: {current_state}"
        if required_states:
            message += f". Etats requis: {', '.join(required_states)}"
        super().__init__(message, "PLAN_INVALID_STATE")


class PlanActivationError(CommissionError):
    """Erreur lors de l'activation d'un plan."""

    def __init__(self, reason: str):
        super().__init__(
            f"Impossible d'activer le plan: {reason}",
            "PLAN_ACTIVATION_ERROR"
        )


class PlanValidationError(CommissionError):
    """Erreur de validation du plan."""

    def __init__(self, errors: list):
        super().__init__(
            f"Validation du plan echouee: {'; '.join(errors)}",
            "PLAN_VALIDATION_ERROR",
            {"errors": errors}
        )


class TierConfigurationError(CommissionError):
    """Erreur de configuration des paliers."""

    def __init__(self, message: str):
        super().__init__(message, "TIER_CONFIGURATION_ERROR")


# ============================================================================
# EXCEPTIONS ASSIGNMENTS
# ============================================================================

class AssignmentNotFoundError(CommissionError):
    """Attribution non trouvee."""

    def __init__(self, assignment_id: str = None):
        message = "Attribution non trouvee"
        if assignment_id:
            message = f"Attribution '{assignment_id}' non trouvee"
        super().__init__(message, "ASSIGNMENT_NOT_FOUND")


class AssignmentDuplicateError(CommissionError):
    """Attribution deja existante."""

    def __init__(self, assignee_id: str, plan_id: str):
        super().__init__(
            f"Attribution deja existante pour ce beneficiaire et ce plan",
            "ASSIGNMENT_DUPLICATE",
            {"assignee_id": assignee_id, "plan_id": plan_id}
        )


class AssignmentOverlapError(CommissionError):
    """Chevauchement de periodes d'attribution."""

    def __init__(self, message: str = None):
        super().__init__(
            message or "Les periodes d'attribution se chevauchent",
            "ASSIGNMENT_OVERLAP"
        )


# ============================================================================
# EXCEPTIONS TRANSACTIONS
# ============================================================================

class TransactionNotFoundError(CommissionError):
    """Transaction non trouvee."""

    def __init__(self, transaction_id: str = None):
        message = "Transaction non trouvee"
        if transaction_id:
            message = f"Transaction '{transaction_id}' non trouvee"
        super().__init__(message, "TRANSACTION_NOT_FOUND")


class TransactionDuplicateError(CommissionError):
    """Transaction deja enregistree."""

    def __init__(self, source_type: str, source_id: str):
        super().__init__(
            f"Transaction deja enregistree pour {source_type} '{source_id}'",
            "TRANSACTION_DUPLICATE",
            {"source_type": source_type, "source_id": source_id}
        )


class TransactionLockedError(CommissionError):
    """Transaction verrouillee (commission deja calculee/payee)."""

    def __init__(self, transaction_id: str):
        super().__init__(
            f"Transaction '{transaction_id}' verrouillee - commission deja traitee",
            "TRANSACTION_LOCKED"
        )


class TransactionValidationError(CommissionError):
    """Erreur de validation de transaction."""

    def __init__(self, errors: list):
        super().__init__(
            f"Validation de la transaction echouee: {'; '.join(errors)}",
            "TRANSACTION_VALIDATION_ERROR",
            {"errors": errors}
        )


# ============================================================================
# EXCEPTIONS CALCULS
# ============================================================================

class CalculationNotFoundError(CommissionError):
    """Calcul de commission non trouve."""

    def __init__(self, calculation_id: str = None):
        message = "Calcul de commission non trouve"
        if calculation_id:
            message = f"Calcul de commission '{calculation_id}' non trouve"
        super().__init__(message, "CALCULATION_NOT_FOUND")


class CalculationError(CommissionError):
    """Erreur lors du calcul de commission."""

    def __init__(self, reason: str, details: dict = None):
        super().__init__(
            f"Erreur de calcul de commission: {reason}",
            "CALCULATION_ERROR",
            details
        )


class CalculationAlreadyExistsError(CommissionError):
    """Calcul deja effectue pour cette periode."""

    def __init__(self, sales_rep_id: str, period: str):
        super().__init__(
            f"Calcul deja effectue pour {sales_rep_id} sur la periode {period}",
            "CALCULATION_EXISTS"
        )


class CalculationLockedError(CommissionError):
    """Calcul verrouille (deja approuve/paye)."""

    def __init__(self, calculation_id: str, status: str):
        super().__init__(
            f"Calcul '{calculation_id}' verrouille (statut: {status})",
            "CALCULATION_LOCKED"
        )


class NoPlanApplicableError(CommissionError):
    """Aucun plan applicable pour le commercial/transaction."""

    def __init__(self, sales_rep_id: str = None, transaction_id: str = None):
        details = {}
        if sales_rep_id:
            details["sales_rep_id"] = sales_rep_id
        if transaction_id:
            details["transaction_id"] = transaction_id
        super().__init__(
            "Aucun plan de commission applicable trouve",
            "NO_PLAN_APPLICABLE",
            details
        )


# ============================================================================
# EXCEPTIONS PERIODES
# ============================================================================

class PeriodNotFoundError(CommissionError):
    """Periode non trouvee."""

    def __init__(self, period_id: str = None, code: str = None):
        message = "Periode de commissionnement non trouvee"
        if period_id:
            message = f"Periode '{period_id}' non trouvee"
        if code:
            message = f"Periode avec code '{code}' non trouvee"
        super().__init__(message, "PERIOD_NOT_FOUND")


class PeriodDuplicateError(CommissionError):
    """Code periode deja existant."""

    def __init__(self, code: str):
        super().__init__(
            f"Une periode avec le code '{code}' existe deja",
            "PERIOD_DUPLICATE"
        )


class PeriodLockedError(CommissionError):
    """Periode verrouillee (cloturee)."""

    def __init__(self, period_id: str):
        super().__init__(
            f"Periode '{period_id}' verrouillee - cloturee",
            "PERIOD_LOCKED"
        )


class PeriodOverlapError(CommissionError):
    """Chevauchement de periodes."""

    def __init__(self, start_date: str, end_date: str):
        super().__init__(
            f"Chevauchement avec une periode existante ({start_date} - {end_date})",
            "PERIOD_OVERLAP"
        )


# ============================================================================
# EXCEPTIONS RELEVES
# ============================================================================

class StatementNotFoundError(CommissionError):
    """Releve non trouve."""

    def __init__(self, statement_id: str = None, number: str = None):
        message = "Releve de commission non trouve"
        if statement_id:
            message = f"Releve '{statement_id}' non trouve"
        if number:
            message = f"Releve numero '{number}' non trouve"
        super().__init__(message, "STATEMENT_NOT_FOUND")


class StatementAlreadyPaidError(CommissionError):
    """Releve deja paye."""

    def __init__(self, statement_id: str):
        super().__init__(
            f"Releve '{statement_id}' deja paye",
            "STATEMENT_ALREADY_PAID"
        )


class StatementGenerationError(CommissionError):
    """Erreur lors de la generation du releve."""

    def __init__(self, reason: str):
        super().__init__(
            f"Erreur de generation du releve: {reason}",
            "STATEMENT_GENERATION_ERROR"
        )


# ============================================================================
# EXCEPTIONS AJUSTEMENTS
# ============================================================================

class AdjustmentNotFoundError(CommissionError):
    """Ajustement non trouve."""

    def __init__(self, adjustment_id: str = None):
        message = "Ajustement non trouve"
        if adjustment_id:
            message = f"Ajustement '{adjustment_id}' non trouve"
        super().__init__(message, "ADJUSTMENT_NOT_FOUND")


class AdjustmentNotPendingError(CommissionError):
    """Ajustement pas en attente de validation."""

    def __init__(self, adjustment_id: str, status: str):
        super().__init__(
            f"Ajustement '{adjustment_id}' n'est pas en attente (statut: {status})",
            "ADJUSTMENT_NOT_PENDING"
        )


class AdjustmentValidationError(CommissionError):
    """Erreur de validation d'ajustement."""

    def __init__(self, errors: list):
        super().__init__(
            f"Validation de l'ajustement echouee: {'; '.join(errors)}",
            "ADJUSTMENT_VALIDATION_ERROR",
            {"errors": errors}
        )


# ============================================================================
# EXCEPTIONS CLAWBACKS
# ============================================================================

class ClawbackNotFoundError(CommissionError):
    """Clawback non trouve."""

    def __init__(self, clawback_id: str = None):
        message = "Clawback non trouve"
        if clawback_id:
            message = f"Clawback '{clawback_id}' non trouve"
        super().__init__(message, "CLAWBACK_NOT_FOUND")


class ClawbackNotEligibleError(CommissionError):
    """Transaction non eligible au clawback."""

    def __init__(self, reason: str):
        super().__init__(
            f"Transaction non eligible au clawback: {reason}",
            "CLAWBACK_NOT_ELIGIBLE"
        )


class ClawbackAlreadyAppliedError(CommissionError):
    """Clawback deja applique."""

    def __init__(self, clawback_id: str):
        super().__init__(
            f"Clawback '{clawback_id}' deja applique",
            "CLAWBACK_ALREADY_APPLIED"
        )


class ClawbackPeriodExpiredError(CommissionError):
    """Periode de clawback expiree."""

    def __init__(self, transaction_date: str, clawback_days: int):
        super().__init__(
            f"Periode de clawback expiree (transaction du {transaction_date}, delai {clawback_days} jours)",
            "CLAWBACK_PERIOD_EXPIRED"
        )


# ============================================================================
# EXCEPTIONS WORKFLOW
# ============================================================================

class WorkflowNotFoundError(CommissionError):
    """Workflow non trouve."""

    def __init__(self, workflow_id: str = None):
        message = "Workflow non trouve"
        if workflow_id:
            message = f"Workflow '{workflow_id}' non trouve"
        super().__init__(message, "WORKFLOW_NOT_FOUND")


class WorkflowInvalidActionError(CommissionError):
    """Action workflow invalide."""

    def __init__(self, action: str, current_status: str):
        super().__init__(
            f"Action '{action}' invalide pour le statut '{current_status}'",
            "WORKFLOW_INVALID_ACTION"
        )


class WorkflowUnauthorizedError(CommissionError):
    """Utilisateur non autorise pour cette action workflow."""

    def __init__(self, user_id: str = None):
        super().__init__(
            "Vous n'etes pas autorise a effectuer cette action",
            "WORKFLOW_UNAUTHORIZED"
        )


class WorkflowAlreadyCompletedError(CommissionError):
    """Workflow deja termine."""

    def __init__(self, workflow_id: str):
        super().__init__(
            f"Workflow '{workflow_id}' deja termine",
            "WORKFLOW_ALREADY_COMPLETED"
        )


# ============================================================================
# EXCEPTIONS TEAM
# ============================================================================

class TeamMemberNotFoundError(CommissionError):
    """Membre equipe non trouve."""

    def __init__(self, member_id: str = None, employee_id: str = None):
        message = "Membre d'equipe non trouve"
        if member_id:
            message = f"Membre '{member_id}' non trouve"
        if employee_id:
            message = f"Membre avec employee_id '{employee_id}' non trouve"
        super().__init__(message, "TEAM_MEMBER_NOT_FOUND")


class TeamHierarchyError(CommissionError):
    """Erreur de hierarchie d'equipe."""

    def __init__(self, message: str):
        super().__init__(message, "TEAM_HIERARCHY_ERROR")


class CircularHierarchyError(CommissionError):
    """Reference circulaire dans la hierarchie."""

    def __init__(self):
        super().__init__(
            "Reference circulaire detectee dans la hierarchie",
            "CIRCULAR_HIERARCHY"
        )


# ============================================================================
# EXCEPTIONS INTEGRATION
# ============================================================================

class PayrollIntegrationError(CommissionError):
    """Erreur d'integration paie."""

    def __init__(self, reason: str):
        super().__init__(
            f"Erreur d'integration avec la paie: {reason}",
            "PAYROLL_INTEGRATION_ERROR"
        )


class ExportError(CommissionError):
    """Erreur d'export."""

    def __init__(self, format: str, reason: str):
        super().__init__(
            f"Erreur d'export {format}: {reason}",
            "EXPORT_ERROR"
        )


# ============================================================================
# EXCEPTIONS AUTHORIZATION
# ============================================================================

class UnauthorizedAccessError(CommissionError):
    """Acces non autorise."""

    def __init__(self, resource: str = None):
        message = "Acces non autorise"
        if resource:
            message = f"Acces non autorise a la ressource '{resource}'"
        super().__init__(message, "UNAUTHORIZED_ACCESS")


class InsufficientPermissionsError(CommissionError):
    """Permissions insuffisantes."""

    def __init__(self, required_permission: str = None):
        message = "Permissions insuffisantes"
        if required_permission:
            message = f"Permission requise: {required_permission}"
        super().__init__(message, "INSUFFICIENT_PERMISSIONS")
