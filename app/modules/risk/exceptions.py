"""
Exceptions Risk Management - GAP-075
=====================================
"""


class RiskError(Exception):
    """Exception de base pour le module Risk."""
    pass


# ============== RiskMatrix Exceptions ==============

class RiskMatrixNotFoundError(RiskError):
    """Matrice de risques non trouvée."""
    def __init__(self, matrix_id: str):
        self.matrix_id = matrix_id
        super().__init__(f"Matrice de risques non trouvée: {matrix_id}")


class RiskMatrixDuplicateError(RiskError):
    """Code matrice déjà utilisé."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Code matrice déjà utilisé: {code}")


class RiskMatrixValidationError(RiskError):
    """Erreur de validation matrice."""
    def __init__(self, message: str):
        super().__init__(message)


class RiskMatrixInUseError(RiskError):
    """Matrice utilisée par des risques."""
    def __init__(self, matrix_id: str, risk_count: int):
        self.matrix_id = matrix_id
        self.risk_count = risk_count
        super().__init__(f"Matrice utilisée par {risk_count} risque(s)")


class DefaultMatrixRequiredError(RiskError):
    """Impossible de désactiver la seule matrice par défaut."""
    def __init__(self):
        super().__init__("Une matrice par défaut est requise")


# ============== Risk Exceptions ==============

class RiskNotFoundError(RiskError):
    """Risque non trouvé."""
    def __init__(self, risk_id: str):
        self.risk_id = risk_id
        super().__init__(f"Risque non trouvé: {risk_id}")


class RiskDuplicateError(RiskError):
    """Code risque déjà utilisé."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Code risque déjà utilisé: {code}")


class RiskValidationError(RiskError):
    """Erreur de validation risque."""
    def __init__(self, message: str):
        super().__init__(message)


class RiskStateError(RiskError):
    """Erreur de transition d'état risque."""
    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Transition non autorisée: {current_status} -> {target_status}"
        )


class RiskClosedError(RiskError):
    """Risque déjà clôturé."""
    def __init__(self, risk_id: str):
        self.risk_id = risk_id
        super().__init__(f"Risque déjà clôturé: {risk_id}")


class RiskHasActiveActionsError(RiskError):
    """Risque avec actions actives."""
    def __init__(self, risk_id: str, action_count: int):
        self.risk_id = risk_id
        self.action_count = action_count
        super().__init__(
            f"Impossible de clôturer: {action_count} action(s) active(s)"
        )


class RiskAccessDeniedError(RiskError):
    """Accès au risque refusé."""
    def __init__(self, risk_id: str):
        self.risk_id = risk_id
        super().__init__(f"Accès refusé au risque: {risk_id}")


class RiskCircularReferenceError(RiskError):
    """Référence circulaire détectée."""
    def __init__(self, risk_id: str, parent_id: str):
        self.risk_id = risk_id
        self.parent_id = parent_id
        super().__init__(f"Référence circulaire détectée: {risk_id} -> {parent_id}")


# ============== Control Exceptions ==============

class ControlNotFoundError(RiskError):
    """Contrôle non trouvé."""
    def __init__(self, control_id: str):
        self.control_id = control_id
        super().__init__(f"Contrôle non trouvé: {control_id}")


class ControlDuplicateError(RiskError):
    """Code contrôle déjà utilisé."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Code contrôle déjà utilisé: {code}")


class ControlValidationError(RiskError):
    """Erreur de validation contrôle."""
    def __init__(self, message: str):
        super().__init__(message)


class ControlInactiveError(RiskError):
    """Contrôle désactivé."""
    def __init__(self, control_id: str):
        self.control_id = control_id
        super().__init__(f"Contrôle désactivé: {control_id}")


# ============== MitigationAction Exceptions ==============

class ActionNotFoundError(RiskError):
    """Action non trouvée."""
    def __init__(self, action_id: str):
        self.action_id = action_id
        super().__init__(f"Action non trouvée: {action_id}")


class ActionDuplicateError(RiskError):
    """Code action déjà utilisé."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Code action déjà utilisé: {code}")


class ActionValidationError(RiskError):
    """Erreur de validation action."""
    def __init__(self, message: str):
        super().__init__(message)


class ActionStateError(RiskError):
    """Erreur de transition d'état action."""
    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Transition non autorisée: {current_status} -> {target_status}"
        )


class ActionCompletedError(RiskError):
    """Action déjà terminée."""
    def __init__(self, action_id: str):
        self.action_id = action_id
        super().__init__(f"Action déjà terminée: {action_id}")


class ActionCancelledError(RiskError):
    """Action annulée."""
    def __init__(self, action_id: str):
        self.action_id = action_id
        super().__init__(f"Action annulée: {action_id}")


class ActionProgressError(RiskError):
    """Erreur de progression action."""
    def __init__(self, message: str):
        super().__init__(message)


# ============== RiskIndicator Exceptions ==============

class IndicatorNotFoundError(RiskError):
    """Indicateur non trouvé."""
    def __init__(self, indicator_id: str):
        self.indicator_id = indicator_id
        super().__init__(f"Indicateur non trouvé: {indicator_id}")


class IndicatorDuplicateError(RiskError):
    """Code indicateur déjà utilisé."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Code indicateur déjà utilisé: {code}")


class IndicatorValidationError(RiskError):
    """Erreur de validation indicateur."""
    def __init__(self, message: str):
        super().__init__(message)


class IndicatorThresholdError(RiskError):
    """Erreur de configuration des seuils."""
    def __init__(self, message: str):
        super().__init__(message)


class IndicatorInactiveError(RiskError):
    """Indicateur désactivé."""
    def __init__(self, indicator_id: str):
        self.indicator_id = indicator_id
        super().__init__(f"Indicateur désactivé: {indicator_id}")


# ============== RiskAssessment Exceptions ==============

class AssessmentNotFoundError(RiskError):
    """Évaluation non trouvée."""
    def __init__(self, assessment_id: str):
        self.assessment_id = assessment_id
        super().__init__(f"Évaluation non trouvée: {assessment_id}")


class AssessmentValidationError(RiskError):
    """Erreur de validation évaluation."""
    def __init__(self, message: str):
        super().__init__(message)


class AssessmentAlreadyValidatedError(RiskError):
    """Évaluation déjà validée."""
    def __init__(self, assessment_id: str):
        self.assessment_id = assessment_id
        super().__init__(f"Évaluation déjà validée: {assessment_id}")


# ============== RiskIncident Exceptions ==============

class IncidentNotFoundError(RiskError):
    """Incident non trouvé."""
    def __init__(self, incident_id: str):
        self.incident_id = incident_id
        super().__init__(f"Incident non trouvé: {incident_id}")


class IncidentDuplicateError(RiskError):
    """Code incident déjà utilisé."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Code incident déjà utilisé: {code}")


class IncidentValidationError(RiskError):
    """Erreur de validation incident."""
    def __init__(self, message: str):
        super().__init__(message)


class IncidentStateError(RiskError):
    """Erreur de transition d'état incident."""
    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Transition non autorisée: {current_status} -> {target_status}"
        )


class IncidentClosedError(RiskError):
    """Incident déjà clôturé."""
    def __init__(self, incident_id: str):
        self.incident_id = incident_id
        super().__init__(f"Incident déjà clôturé: {incident_id}")


class IncidentNotResolvedError(RiskError):
    """Incident non résolu."""
    def __init__(self, incident_id: str):
        self.incident_id = incident_id
        super().__init__(f"L'incident doit être résolu avant clôture: {incident_id}")
