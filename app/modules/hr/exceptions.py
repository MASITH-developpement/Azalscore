"""
AZALS MODULE HR - Exceptions
=============================

Exceptions metier specifiques au module de gestion des ressources humaines.
"""

from typing import Optional, List
from uuid import UUID
from datetime import date


class HRError(Exception):
    """Exception de base du module HR."""

    def __init__(self, message: str, tenant_id: Optional[UUID] = None):
        self.message = message
        self.tenant_id = tenant_id
        super().__init__(self.message)


# ============================================================================
# EMPLOYEE ERRORS
# ============================================================================

class EmployeeNotFoundError(HRError):
    """Employe non trouve."""

    def __init__(self, employee_id: Optional[str] = None, matricule: Optional[str] = None):
        self.employee_id = employee_id
        self.matricule = matricule
        identifier = matricule or employee_id
        super().__init__(f"Employe {identifier} non trouve")


class EmployeeDuplicateError(HRError):
    """Employe deja existant (email ou matricule)."""

    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"Un employe avec {field}={value} existe deja")


class EmployeeInactiveError(HRError):
    """Operation sur un employe inactif."""

    def __init__(self, employee_id: str, status: str):
        self.employee_id = employee_id
        self.status = status
        super().__init__(f"L'employe {employee_id} est inactif (statut: {status})")


# ============================================================================
# CONTRACT ERRORS
# ============================================================================

class ContractNotFoundError(HRError):
    """Contrat de travail non trouve."""

    def __init__(self, contract_id: Optional[str] = None):
        self.contract_id = contract_id
        super().__init__(f"Contrat {contract_id} non trouve")


class ContractOverlapError(HRError):
    """Chevauchement de contrats pour un employe."""

    def __init__(self, employee_id: str, start_date: date, end_date: Optional[date] = None):
        self.employee_id = employee_id
        self.start_date = start_date
        self.end_date = end_date
        super().__init__(
            f"Chevauchement de contrat detecte pour l'employe {employee_id}"
        )


class ContractExpiredError(HRError):
    """Contrat expire."""

    def __init__(self, contract_id: str, expired_at: date):
        self.contract_id = contract_id
        self.expired_at = expired_at
        super().__init__(f"Le contrat {contract_id} a expire le {expired_at}")


# ============================================================================
# LEAVE ERRORS
# ============================================================================

class LeaveRequestNotFoundError(HRError):
    """Demande de conge non trouvee."""

    def __init__(self, leave_id: Optional[str] = None):
        self.leave_id = leave_id
        super().__init__(f"Demande de conge {leave_id} non trouvee")


class LeaveBalanceInsufficientError(HRError):
    """Solde de conges insuffisant."""

    def __init__(self, employee_id: str, leave_type: str, requested: float, available: float):
        self.employee_id = employee_id
        self.leave_type = leave_type
        self.requested = requested
        self.available = available
        super().__init__(
            f"Solde insuffisant pour {leave_type}: "
            f"demande={requested}, disponible={available}"
        )


class LeaveOverlapError(HRError):
    """Chevauchement avec une autre demande de conge."""

    def __init__(self, employee_id: str, start_date: date, end_date: date):
        self.employee_id = employee_id
        self.start_date = start_date
        self.end_date = end_date
        super().__init__(
            f"Chevauchement detecte pour la periode {start_date} - {end_date}"
        )


class LeaveStateError(HRError):
    """Transition d'etat invalide pour la demande de conge."""

    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Transition impossible de {current_status} vers {target_status}"
        )


# ============================================================================
# PAYROLL ERRORS
# ============================================================================

class PayrollPeriodNotFoundError(HRError):
    """Periode de paie non trouvee."""

    def __init__(self, period_id: Optional[str] = None, period: Optional[str] = None):
        self.period_id = period_id
        self.period = period
        identifier = period or period_id
        super().__init__(f"Periode de paie {identifier} non trouvee")


class PayrollPeriodClosedError(HRError):
    """Periode de paie cloturee."""

    def __init__(self, period: str):
        self.period = period
        super().__init__(f"La periode de paie {period} est cloturee")


class PayslipNotFoundError(HRError):
    """Bulletin de paie non trouve."""

    def __init__(self, payslip_id: Optional[str] = None):
        self.payslip_id = payslip_id
        super().__init__(f"Bulletin de paie {payslip_id} non trouve")


class PayslipValidationError(HRError):
    """Erreur de validation du bulletin de paie."""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        self.errors = errors or []
        super().__init__(message)


class PayslipAlreadyValidatedError(HRError):
    """Bulletin de paie deja valide."""

    def __init__(self, payslip_id: str):
        self.payslip_id = payslip_id
        super().__init__(f"Le bulletin {payslip_id} est deja valide")


# ============================================================================
# TRAINING ERRORS
# ============================================================================

class TrainingNotFoundError(HRError):
    """Formation non trouvee."""

    def __init__(self, training_id: Optional[str] = None):
        self.training_id = training_id
        super().__init__(f"Formation {training_id} non trouvee")


class TrainingFullError(HRError):
    """Formation complete (plus de places)."""

    def __init__(self, training_id: str, max_participants: int):
        self.training_id = training_id
        self.max_participants = max_participants
        super().__init__(
            f"La formation {training_id} est complete "
            f"(max: {max_participants} participants)"
        )


class TrainingAlreadyRegisteredError(HRError):
    """Employe deja inscrit a la formation."""

    def __init__(self, employee_id: str, training_id: str):
        self.employee_id = employee_id
        self.training_id = training_id
        super().__init__(
            f"L'employe {employee_id} est deja inscrit a la formation {training_id}"
        )


# ============================================================================
# EVALUATION ERRORS
# ============================================================================

class EvaluationNotFoundError(HRError):
    """Evaluation non trouvee."""

    def __init__(self, evaluation_id: Optional[str] = None):
        self.evaluation_id = evaluation_id
        super().__init__(f"Evaluation {evaluation_id} non trouvee")


class EvaluationStateError(HRError):
    """Transition d'etat invalide pour l'evaluation."""

    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Transition impossible de {current_status} vers {target_status}"
        )


# ============================================================================
# DEPARTMENT/POSITION ERRORS
# ============================================================================

class DepartmentNotFoundError(HRError):
    """Departement non trouve."""

    def __init__(self, department_id: Optional[str] = None):
        self.department_id = department_id
        super().__init__(f"Departement {department_id} non trouve")


class PositionNotFoundError(HRError):
    """Poste non trouve."""

    def __init__(self, position_id: Optional[str] = None):
        self.position_id = position_id
        super().__init__(f"Poste {position_id} non trouve")


# ============================================================================
# CACHE ERRORS
# ============================================================================

class HRCacheError(HRError):
    """Erreur de cache non critique."""
    pass
