"""
AZALS MODULE - Appointments - Exceptions
=========================================

Exceptions metier pour le module Rendez-vous.
"""
from __future__ import annotations


from typing import List, Optional


class AppointmentError(Exception):
    """Exception de base du module Appointments."""

    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(message)


# ============================================================================
# RENDEZ-VOUS
# ============================================================================

class AppointmentNotFoundError(AppointmentError):
    """Rendez-vous non trouve."""

    def __init__(self, message: str = "Appointment not found"):
        super().__init__(message, code="APPOINTMENT_NOT_FOUND")


class AppointmentConflictError(AppointmentError):
    """Conflit de planning."""

    def __init__(
        self,
        message: str = "Time slot not available",
        conflicts: Optional[List[str]] = None
    ):
        super().__init__(message, code="APPOINTMENT_CONFLICT")
        self.conflicts = conflicts or []


class AppointmentStateError(AppointmentError):
    """Transition d'etat invalide."""

    def __init__(self, message: str = "Invalid state transition"):
        super().__init__(message, code="APPOINTMENT_STATE_ERROR")


class AppointmentValidationError(AppointmentError):
    """Erreur de validation."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, code="APPOINTMENT_VALIDATION_ERROR")


class AppointmentDuplicateError(AppointmentError):
    """Code rendez-vous deja existant."""

    def __init__(self, message: str = "Appointment code already exists"):
        super().__init__(message, code="APPOINTMENT_DUPLICATE")


class AppointmentAlreadyConfirmedError(AppointmentError):
    """Rendez-vous deja confirme."""

    def __init__(self, message: str = "Appointment already confirmed"):
        super().__init__(message, code="APPOINTMENT_ALREADY_CONFIRMED")


class AppointmentAlreadyCancelledError(AppointmentError):
    """Rendez-vous deja annule."""

    def __init__(self, message: str = "Appointment already cancelled"):
        super().__init__(message, code="APPOINTMENT_ALREADY_CANCELLED")


class AppointmentNotCancellableError(AppointmentError):
    """Rendez-vous non annulable (delai depasse)."""

    def __init__(self, message: str = "Appointment cannot be cancelled"):
        super().__init__(message, code="APPOINTMENT_NOT_CANCELLABLE")


# ============================================================================
# TYPE DE RENDEZ-VOUS
# ============================================================================

class TypeNotFoundError(AppointmentError):
    """Type de rendez-vous non trouve."""

    def __init__(self, message: str = "Appointment type not found"):
        super().__init__(message, code="TYPE_NOT_FOUND")


class TypeDuplicateError(AppointmentError):
    """Code type deja existant."""

    def __init__(self, message: str = "Type code already exists"):
        super().__init__(message, code="TYPE_DUPLICATE")


class TypeInUseError(AppointmentError):
    """Type utilise par des rendez-vous."""

    def __init__(self, message: str = "Type is in use and cannot be deleted"):
        super().__init__(message, code="TYPE_IN_USE")


# ============================================================================
# RESSOURCE
# ============================================================================

class ResourceNotFoundError(AppointmentError):
    """Ressource non trouvee."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code="RESOURCE_NOT_FOUND")


class ResourceDuplicateError(AppointmentError):
    """Code ressource deja existant."""

    def __init__(self, message: str = "Resource code already exists"):
        super().__init__(message, code="RESOURCE_DUPLICATE")


class ResourceNotAvailableError(AppointmentError):
    """Ressource non disponible."""

    def __init__(self, message: str = "Resource not available"):
        super().__init__(message, code="RESOURCE_NOT_AVAILABLE")


class ResourceInUseError(AppointmentError):
    """Ressource utilisee par des rendez-vous."""

    def __init__(self, message: str = "Resource is in use and cannot be deleted"):
        super().__init__(message, code="RESOURCE_IN_USE")


# ============================================================================
# CRENEAUX
# ============================================================================

class SlotNotAvailableError(AppointmentError):
    """Creneau non disponible."""

    def __init__(self, message: str = "Time slot not available"):
        super().__init__(message, code="SLOT_NOT_AVAILABLE")


class NoSlotsAvailableError(AppointmentError):
    """Aucun creneau disponible."""

    def __init__(self, message: str = "No slots available"):
        super().__init__(message, code="NO_SLOTS_AVAILABLE")


# ============================================================================
# RESERVATION
# ============================================================================

class BookingNotAllowedError(AppointmentError):
    """Reservation non autorisee."""

    def __init__(self, message: str = "Booking not allowed"):
        super().__init__(message, code="BOOKING_NOT_ALLOWED")


class BookingTooEarlyError(AppointmentError):
    """Reservation trop tot (preavis minimum)."""

    def __init__(self, message: str = "Booking too early, minimum notice required"):
        super().__init__(message, code="BOOKING_TOO_EARLY")


class BookingTooLateError(AppointmentError):
    """Reservation trop tard (fenetre depassee)."""

    def __init__(self, message: str = "Booking too late, booking window exceeded"):
        super().__init__(message, code="BOOKING_TOO_LATE")


class MaxBookingsExceededError(AppointmentError):
    """Nombre maximum de reservations atteint."""

    def __init__(self, message: str = "Maximum bookings exceeded"):
        super().__init__(message, code="MAX_BOOKINGS_EXCEEDED")


# ============================================================================
# PARTICIPANT
# ============================================================================

class AttendeeNotFoundError(AppointmentError):
    """Participant non trouve."""

    def __init__(self, message: str = "Attendee not found"):
        super().__init__(message, code="ATTENDEE_NOT_FOUND")


class AttendeeAlreadyExistsError(AppointmentError):
    """Participant deja present."""

    def __init__(self, message: str = "Attendee already exists"):
        super().__init__(message, code="ATTENDEE_ALREADY_EXISTS")


class MaxAttendeesExceededError(AppointmentError):
    """Nombre maximum de participants atteint."""

    def __init__(self, message: str = "Maximum attendees exceeded"):
        super().__init__(message, code="MAX_ATTENDEES_EXCEEDED")


# ============================================================================
# RAPPEL
# ============================================================================

class ReminderNotFoundError(AppointmentError):
    """Rappel non trouve."""

    def __init__(self, message: str = "Reminder not found"):
        super().__init__(message, code="REMINDER_NOT_FOUND")


class ReminderAlreadySentError(AppointmentError):
    """Rappel deja envoye."""

    def __init__(self, message: str = "Reminder already sent"):
        super().__init__(message, code="REMINDER_ALREADY_SENT")


# ============================================================================
# LISTE D'ATTENTE
# ============================================================================

class WaitlistEntryNotFoundError(AppointmentError):
    """Entree liste d'attente non trouvee."""

    def __init__(self, message: str = "Waitlist entry not found"):
        super().__init__(message, code="WAITLIST_ENTRY_NOT_FOUND")


class WaitlistEntryExpiredError(AppointmentError):
    """Entree liste d'attente expiree."""

    def __init__(self, message: str = "Waitlist entry expired"):
        super().__init__(message, code="WAITLIST_ENTRY_EXPIRED")


# ============================================================================
# SYNCHRONISATION
# ============================================================================

class CalendarSyncError(AppointmentError):
    """Erreur de synchronisation calendrier."""

    def __init__(self, message: str = "Calendar sync error"):
        super().__init__(message, code="CALENDAR_SYNC_ERROR")


class CalendarAuthError(AppointmentError):
    """Erreur d'authentification calendrier."""

    def __init__(self, message: str = "Calendar authentication error"):
        super().__init__(message, code="CALENDAR_AUTH_ERROR")


class CalendarProviderError(AppointmentError):
    """Erreur du fournisseur de calendrier."""

    def __init__(self, message: str = "Calendar provider error"):
        super().__init__(message, code="CALENDAR_PROVIDER_ERROR")


# ============================================================================
# RECURRENCE
# ============================================================================

class RecurrenceError(AppointmentError):
    """Erreur de recurrence."""

    def __init__(self, message: str = "Recurrence error"):
        super().__init__(message, code="RECURRENCE_ERROR")


class InvalidRecurrencePatternError(AppointmentError):
    """Pattern de recurrence invalide."""

    def __init__(self, message: str = "Invalid recurrence pattern"):
        super().__init__(message, code="INVALID_RECURRENCE_PATTERN")


# ============================================================================
# PAIEMENT
# ============================================================================

class PaymentRequiredError(AppointmentError):
    """Paiement requis."""

    def __init__(self, message: str = "Payment required"):
        super().__init__(message, code="PAYMENT_REQUIRED")


class DepositNotPaidError(AppointmentError):
    """Acompte non paye."""

    def __init__(self, message: str = "Deposit not paid"):
        super().__init__(message, code="DEPOSIT_NOT_PAID")


# ============================================================================
# PERMISSIONS
# ============================================================================

class PermissionDeniedError(AppointmentError):
    """Permission refusee."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, code="PERMISSION_DENIED")


class NotOrganizerError(AppointmentError):
    """Non organisateur du rendez-vous."""

    def __init__(self, message: str = "Only organizer can perform this action"):
        super().__init__(message, code="NOT_ORGANIZER")
