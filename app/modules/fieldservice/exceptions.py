"""
Exceptions métier - Module Field Service (GAP-081)
"""


class FieldServiceError(Exception):
    """Exception de base du module Field Service."""
    pass


class WorkOrderNotFoundError(FieldServiceError):
    """Ordre de travail non trouvé."""
    pass


class WorkOrderDuplicateError(FieldServiceError):
    """Code d'ordre de travail déjà existant."""
    pass


class WorkOrderValidationError(FieldServiceError):
    """Erreur de validation métier."""
    pass


class WorkOrderStateError(FieldServiceError):
    """Transition d'état invalide."""
    pass


class TechnicianNotFoundError(FieldServiceError):
    """Technicien non trouvé."""
    pass


class TechnicianDuplicateError(FieldServiceError):
    """Code technicien déjà existant."""
    pass


class TechnicianValidationError(FieldServiceError):
    """Erreur de validation technicien."""
    pass


class TechnicianUnavailableError(FieldServiceError):
    """Technicien non disponible."""
    pass


class CustomerSiteNotFoundError(FieldServiceError):
    """Site client non trouvé."""
    pass


class CustomerSiteDuplicateError(FieldServiceError):
    """Code site déjà existant."""
    pass


class ServiceZoneNotFoundError(FieldServiceError):
    """Zone de service non trouvée."""
    pass


class ServiceZoneDuplicateError(FieldServiceError):
    """Code zone déjà existant."""
    pass


class SkillNotFoundError(FieldServiceError):
    """Compétence non trouvée."""
    pass


class SkillDuplicateError(FieldServiceError):
    """Code compétence déjà existant."""
    pass


class DispatchError(FieldServiceError):
    """Erreur de dispatch."""
    pass


class SchedulingError(FieldServiceError):
    """Erreur de planification."""
    pass
