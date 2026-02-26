"""
Exceptions métier Resources / Réservation
=========================================
"""


class ResourceError(Exception):
    """Exception de base du module Resources."""
    pass


# ============== Location Exceptions ==============

class LocationNotFoundError(ResourceError):
    """Localisation non trouvée."""
    pass


class LocationDuplicateError(ResourceError):
    """Code localisation déjà existant."""
    pass


class LocationValidationError(ResourceError):
    """Erreur de validation localisation."""
    pass


# ============== Amenity Exceptions ==============

class AmenityNotFoundError(ResourceError):
    """Équipement non trouvé."""
    pass


class AmenityDuplicateError(ResourceError):
    """Code équipement déjà existant."""
    pass


# ============== Resource Exceptions ==============

class ResourceNotFoundError(ResourceError):
    """Ressource non trouvée."""
    pass


class ResourceDuplicateError(ResourceError):
    """Code ressource déjà existant."""
    pass


class ResourceValidationError(ResourceError):
    """Erreur de validation ressource."""
    pass


class ResourceUnavailableError(ResourceError):
    """Ressource non disponible."""
    pass


class ResourceInMaintenanceError(ResourceError):
    """Ressource en maintenance."""
    pass


# ============== Booking Exceptions ==============

class BookingNotFoundError(ResourceError):
    """Réservation non trouvée."""
    pass


class BookingValidationError(ResourceError):
    """Erreur de validation réservation."""
    pass


class BookingStateError(ResourceError):
    """Transition d'état réservation invalide."""
    pass


class BookingConflictError(ResourceError):
    """Conflit de réservation."""
    pass


class BookingCapacityExceededError(ResourceError):
    """Capacité dépassée."""
    pass


class BookingDurationError(ResourceError):
    """Durée de réservation invalide."""
    pass


class BookingAdvanceError(ResourceError):
    """Délai de réservation non respecté."""
    pass


class BookingAccessDeniedError(ResourceError):
    """Accès à la réservation refusé."""
    pass


class BookingApprovalRequiredError(ResourceError):
    """Approbation requise pour la réservation."""
    pass


class BookingAlreadyCheckedInError(ResourceError):
    """Déjà enregistré."""
    pass


class BookingNotCheckedInError(ResourceError):
    """Non enregistré."""
    pass


# ============== BlockedSlot Exceptions ==============

class BlockedSlotNotFoundError(ResourceError):
    """Créneau bloqué non trouvé."""
    pass


class BlockedSlotValidationError(ResourceError):
    """Erreur de validation créneau bloqué."""
    pass


# ============== Waitlist Exceptions ==============

class WaitlistEntryNotFoundError(ResourceError):
    """Entrée liste d'attente non trouvée."""
    pass


class WaitlistValidationError(ResourceError):
    """Erreur de validation liste d'attente."""
    pass


class WaitlistExpiredError(ResourceError):
    """Entrée liste d'attente expirée."""
    pass


# ============== Recurrence Exceptions ==============

class RecurrenceValidationError(ResourceError):
    """Erreur de validation récurrence."""
    pass


class RecurrenceConflictError(ResourceError):
    """Conflit dans la série récurrente."""
    pass
