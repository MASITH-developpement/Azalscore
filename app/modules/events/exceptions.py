"""
AZALS MODULE EVENTS - Exceptions
================================

Exceptions personnalisees pour le module Events.
"""

from typing import Any, Optional


class EventsBaseException(Exception):
    """Exception de base pour le module Events."""

    def __init__(
        self,
        message: str,
        code: str = "EVENTS_ERROR",
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


# ============================================================================
# EVENEMENTS
# ============================================================================

class EventNotFoundException(EventsBaseException):
    """Evenement non trouve."""

    def __init__(self, event_id: str):
        super().__init__(
            message=f"Evenement non trouve: {event_id}",
            code="EVENT_NOT_FOUND",
            details={"event_id": event_id}
        )


class EventCodeExistsException(EventsBaseException):
    """Code evenement deja existant."""

    def __init__(self, code: str):
        super().__init__(
            message=f"Un evenement avec le code '{code}' existe deja",
            code="EVENT_CODE_EXISTS",
            details={"code": code}
        )


class EventStatusException(EventsBaseException):
    """Erreur de statut evenement."""

    def __init__(self, current_status: str, action: str):
        super().__init__(
            message=f"Impossible d'effectuer '{action}' sur un evenement au statut '{current_status}'",
            code="EVENT_INVALID_STATUS",
            details={"current_status": current_status, "action": action}
        )


class EventDatesException(EventsBaseException):
    """Erreur de dates evenement."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="EVENT_INVALID_DATES"
        )


class EventCapacityException(EventsBaseException):
    """Erreur de capacite evenement."""

    def __init__(self, event_id: str, current: int, max_capacity: int):
        super().__init__(
            message=f"Capacite maximale atteinte pour l'evenement ({current}/{max_capacity})",
            code="EVENT_CAPACITY_REACHED",
            details={"event_id": event_id, "current": current, "max_capacity": max_capacity}
        )


# ============================================================================
# INSCRIPTIONS
# ============================================================================

class RegistrationNotFoundException(EventsBaseException):
    """Inscription non trouvee."""

    def __init__(self, registration_id: str):
        super().__init__(
            message=f"Inscription non trouvee: {registration_id}",
            code="REGISTRATION_NOT_FOUND",
            details={"registration_id": registration_id}
        )


class RegistrationClosedException(EventsBaseException):
    """Inscriptions fermees."""

    def __init__(self, event_id: str):
        super().__init__(
            message="Les inscriptions sont fermees pour cet evenement",
            code="REGISTRATION_CLOSED",
            details={"event_id": event_id}
        )


class RegistrationDuplicateException(EventsBaseException):
    """Inscription en double."""

    def __init__(self, email: str, event_id: str):
        super().__init__(
            message=f"Une inscription existe deja pour {email} sur cet evenement",
            code="REGISTRATION_DUPLICATE",
            details={"email": email, "event_id": event_id}
        )


class RegistrationStatusException(EventsBaseException):
    """Erreur de statut inscription."""

    def __init__(self, current_status: str, action: str):
        super().__init__(
            message=f"Impossible d'effectuer '{action}' sur une inscription au statut '{current_status}'",
            code="REGISTRATION_INVALID_STATUS",
            details={"current_status": current_status, "action": action}
        )


class RegistrationApprovalRequired(EventsBaseException):
    """Approbation requise pour inscription."""

    def __init__(self, event_id: str):
        super().__init__(
            message="Cette inscription necessite une approbation",
            code="REGISTRATION_APPROVAL_REQUIRED",
            details={"event_id": event_id}
        )


# ============================================================================
# BILLETTERIE
# ============================================================================

class TicketTypeNotFoundException(EventsBaseException):
    """Type de billet non trouve."""

    def __init__(self, ticket_type_id: str):
        super().__init__(
            message=f"Type de billet non trouve: {ticket_type_id}",
            code="TICKET_TYPE_NOT_FOUND",
            details={"ticket_type_id": ticket_type_id}
        )


class TicketSoldOutException(EventsBaseException):
    """Billets epuises."""

    def __init__(self, ticket_type_id: str, name: str):
        super().__init__(
            message=f"Le billet '{name}' est epuise",
            code="TICKET_SOLD_OUT",
            details={"ticket_type_id": ticket_type_id, "name": name}
        )


class TicketSalesNotOpenException(EventsBaseException):
    """Vente de billets non ouverte."""

    def __init__(self, ticket_type_id: str):
        super().__init__(
            message="La vente de ce type de billet n'est pas encore ouverte",
            code="TICKET_SALES_NOT_OPEN",
            details={"ticket_type_id": ticket_type_id}
        )


class TicketSalesClosedException(EventsBaseException):
    """Vente de billets fermee."""

    def __init__(self, ticket_type_id: str):
        super().__init__(
            message="La vente de ce type de billet est fermee",
            code="TICKET_SALES_CLOSED",
            details={"ticket_type_id": ticket_type_id}
        )


class TicketQuantityException(EventsBaseException):
    """Erreur de quantite de billets."""

    def __init__(self, requested: int, min_qty: int, max_qty: int):
        super().__init__(
            message=f"Quantite invalide. Min: {min_qty}, Max: {max_qty}, Demande: {requested}",
            code="TICKET_INVALID_QUANTITY",
            details={"requested": requested, "min": min_qty, "max": max_qty}
        )


# ============================================================================
# CODES PROMO
# ============================================================================

class DiscountCodeNotFoundException(EventsBaseException):
    """Code promo non trouve."""

    def __init__(self, code: str):
        super().__init__(
            message=f"Code promo invalide: {code}",
            code="DISCOUNT_CODE_NOT_FOUND",
            details={"code": code}
        )


class DiscountCodeExpiredException(EventsBaseException):
    """Code promo expire."""

    def __init__(self, code: str):
        super().__init__(
            message=f"Le code promo '{code}' a expire",
            code="DISCOUNT_CODE_EXPIRED",
            details={"code": code}
        )


class DiscountCodeExhaustedException(EventsBaseException):
    """Code promo epuise."""

    def __init__(self, code: str):
        super().__init__(
            message=f"Le code promo '{code}' a atteint sa limite d'utilisation",
            code="DISCOUNT_CODE_EXHAUSTED",
            details={"code": code}
        )


class DiscountCodeInactiveException(EventsBaseException):
    """Code promo inactif."""

    def __init__(self, code: str):
        super().__init__(
            message=f"Le code promo '{code}' n'est pas actif",
            code="DISCOUNT_CODE_INACTIVE",
            details={"code": code}
        )


class DiscountCodeNotApplicableException(EventsBaseException):
    """Code promo non applicable."""

    def __init__(self, code: str, reason: str):
        super().__init__(
            message=f"Le code promo '{code}' n'est pas applicable: {reason}",
            code="DISCOUNT_CODE_NOT_APPLICABLE",
            details={"code": code, "reason": reason}
        )


# ============================================================================
# SESSIONS
# ============================================================================

class SessionNotFoundException(EventsBaseException):
    """Session non trouvee."""

    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session non trouvee: {session_id}",
            code="SESSION_NOT_FOUND",
            details={"session_id": session_id}
        )


class SessionCapacityException(EventsBaseException):
    """Capacite session atteinte."""

    def __init__(self, session_id: str, title: str):
        super().__init__(
            message=f"La session '{title}' a atteint sa capacite maximale",
            code="SESSION_CAPACITY_REACHED",
            details={"session_id": session_id, "title": title}
        )


class SessionConflictException(EventsBaseException):
    """Conflit d'horaire session."""

    def __init__(self, session_ids: list[str]):
        super().__init__(
            message="Conflit d'horaire entre les sessions selectionnees",
            code="SESSION_TIME_CONFLICT",
            details={"session_ids": session_ids}
        )


# ============================================================================
# INTERVENANTS
# ============================================================================

class SpeakerNotFoundException(EventsBaseException):
    """Intervenant non trouve."""

    def __init__(self, speaker_id: str):
        super().__init__(
            message=f"Intervenant non trouve: {speaker_id}",
            code="SPEAKER_NOT_FOUND",
            details={"speaker_id": speaker_id}
        )


class SpeakerAlreadyAssignedException(EventsBaseException):
    """Intervenant deja assigne."""

    def __init__(self, speaker_id: str, event_id: str):
        super().__init__(
            message="Cet intervenant est deja assigne a cet evenement",
            code="SPEAKER_ALREADY_ASSIGNED",
            details={"speaker_id": speaker_id, "event_id": event_id}
        )


# ============================================================================
# LIEUX
# ============================================================================

class VenueNotFoundException(EventsBaseException):
    """Lieu non trouve."""

    def __init__(self, venue_id: str):
        super().__init__(
            message=f"Lieu non trouve: {venue_id}",
            code="VENUE_NOT_FOUND",
            details={"venue_id": venue_id}
        )


class RoomNotFoundException(EventsBaseException):
    """Salle non trouvee."""

    def __init__(self, room_id: str):
        super().__init__(
            message=f"Salle non trouvee: {room_id}",
            code="ROOM_NOT_FOUND",
            details={"room_id": room_id}
        )


class VenueUnavailableException(EventsBaseException):
    """Lieu non disponible."""

    def __init__(self, venue_id: str, date_str: str):
        super().__init__(
            message=f"Le lieu n'est pas disponible pour la date demandee: {date_str}",
            code="VENUE_UNAVAILABLE",
            details={"venue_id": venue_id, "date": date_str}
        )


# ============================================================================
# CHECK-IN
# ============================================================================

class CheckInNotFoundException(EventsBaseException):
    """Check-in non trouve."""

    def __init__(self, identifier: str):
        super().__init__(
            message=f"Aucune inscription trouvee pour: {identifier}",
            code="CHECKIN_NOT_FOUND",
            details={"identifier": identifier}
        )


class CheckInAlreadyDoneException(EventsBaseException):
    """Check-in deja effectue."""

    def __init__(self, registration_id: str):
        super().__init__(
            message="Cette inscription a deja ete enregistree",
            code="CHECKIN_ALREADY_DONE",
            details={"registration_id": registration_id}
        )


class CheckInNotAllowedException(EventsBaseException):
    """Check-in non autorise."""

    def __init__(self, registration_id: str, reason: str):
        super().__init__(
            message=f"Check-in non autorise: {reason}",
            code="CHECKIN_NOT_ALLOWED",
            details={"registration_id": registration_id, "reason": reason}
        )


# ============================================================================
# CERTIFICATS
# ============================================================================

class CertificateNotFoundException(EventsBaseException):
    """Certificat non trouve."""

    def __init__(self, certificate_id: str):
        super().__init__(
            message=f"Certificat non trouve: {certificate_id}",
            code="CERTIFICATE_NOT_FOUND",
            details={"certificate_id": certificate_id}
        )


class CertificateAlreadyIssuedException(EventsBaseException):
    """Certificat deja emis."""

    def __init__(self, registration_id: str):
        super().__init__(
            message="Un certificat a deja ete emis pour cette inscription",
            code="CERTIFICATE_ALREADY_ISSUED",
            details={"registration_id": registration_id}
        )


class CertificateNotEligibleException(EventsBaseException):
    """Non eligible au certificat."""

    def __init__(self, registration_id: str, reason: str):
        super().__init__(
            message=f"Non eligible au certificat: {reason}",
            code="CERTIFICATE_NOT_ELIGIBLE",
            details={"registration_id": registration_id, "reason": reason}
        )


# ============================================================================
# EVALUATIONS
# ============================================================================

class EvaluationNotFoundException(EventsBaseException):
    """Evaluation non trouvee."""

    def __init__(self, evaluation_id: str):
        super().__init__(
            message=f"Evaluation non trouvee: {evaluation_id}",
            code="EVALUATION_NOT_FOUND",
            details={"evaluation_id": evaluation_id}
        )


class EvaluationAlreadySubmittedException(EventsBaseException):
    """Evaluation deja soumise."""

    def __init__(self, registration_id: str, evaluation_type: str):
        super().__init__(
            message="Une evaluation a deja ete soumise",
            code="EVALUATION_ALREADY_SUBMITTED",
            details={"registration_id": registration_id, "type": evaluation_type}
        )


class EvaluationDeadlinePassedException(EventsBaseException):
    """Delai d'evaluation depasse."""

    def __init__(self, event_id: str):
        super().__init__(
            message="Le delai pour soumettre une evaluation est depasse",
            code="EVALUATION_DEADLINE_PASSED",
            details={"event_id": event_id}
        )


# ============================================================================
# INVITATIONS
# ============================================================================

class InvitationNotFoundException(EventsBaseException):
    """Invitation non trouvee."""

    def __init__(self, identifier: str):
        super().__init__(
            message=f"Invitation non trouvee: {identifier}",
            code="INVITATION_NOT_FOUND",
            details={"identifier": identifier}
        )


class InvitationExpiredException(EventsBaseException):
    """Invitation expiree."""

    def __init__(self, invitation_code: str):
        super().__init__(
            message="Cette invitation a expire",
            code="INVITATION_EXPIRED",
            details={"invitation_code": invitation_code}
        )


class InvitationAlreadyUsedException(EventsBaseException):
    """Invitation deja utilisee."""

    def __init__(self, invitation_code: str):
        super().__init__(
            message="Cette invitation a deja ete utilisee",
            code="INVITATION_ALREADY_USED",
            details={"invitation_code": invitation_code}
        )


# ============================================================================
# PAIEMENT
# ============================================================================

class PaymentFailedException(EventsBaseException):
    """Echec du paiement."""

    def __init__(self, registration_id: str, reason: str):
        super().__init__(
            message=f"Echec du paiement: {reason}",
            code="PAYMENT_FAILED",
            details={"registration_id": registration_id, "reason": reason}
        )


class RefundNotAllowedException(EventsBaseException):
    """Remboursement non autorise."""

    def __init__(self, registration_id: str, reason: str):
        super().__init__(
            message=f"Remboursement non autorise: {reason}",
            code="REFUND_NOT_ALLOWED",
            details={"registration_id": registration_id, "reason": reason}
        )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'EventsBaseException',
    # Evenements
    'EventNotFoundException',
    'EventCodeExistsException',
    'EventStatusException',
    'EventDatesException',
    'EventCapacityException',
    # Inscriptions
    'RegistrationNotFoundException',
    'RegistrationClosedException',
    'RegistrationDuplicateException',
    'RegistrationStatusException',
    'RegistrationApprovalRequired',
    # Billetterie
    'TicketTypeNotFoundException',
    'TicketSoldOutException',
    'TicketSalesNotOpenException',
    'TicketSalesClosedException',
    'TicketQuantityException',
    # Codes promo
    'DiscountCodeNotFoundException',
    'DiscountCodeExpiredException',
    'DiscountCodeExhaustedException',
    'DiscountCodeInactiveException',
    'DiscountCodeNotApplicableException',
    # Sessions
    'SessionNotFoundException',
    'SessionCapacityException',
    'SessionConflictException',
    # Intervenants
    'SpeakerNotFoundException',
    'SpeakerAlreadyAssignedException',
    # Lieux
    'VenueNotFoundException',
    'RoomNotFoundException',
    'VenueUnavailableException',
    # Check-in
    'CheckInNotFoundException',
    'CheckInAlreadyDoneException',
    'CheckInNotAllowedException',
    # Certificats
    'CertificateNotFoundException',
    'CertificateAlreadyIssuedException',
    'CertificateNotEligibleException',
    # Evaluations
    'EvaluationNotFoundException',
    'EvaluationAlreadySubmittedException',
    'EvaluationDeadlinePassedException',
    # Invitations
    'InvitationNotFoundException',
    'InvitationExpiredException',
    'InvitationAlreadyUsedException',
    # Paiement
    'PaymentFailedException',
    'RefundNotAllowedException',
]
