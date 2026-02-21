"""
AZALS MODULE EVENTS - Repository
=================================

Couche d'acces aux donnees avec isolation tenant automatique.
Utilise le pattern Repository pour encapsuler les requetes.
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_, desc
from sqlalchemy.orm import Session, joinedload

from app.core.repository import BaseRepository

from .models import (
    Event,
    EventCheckIn,
    EventCertificate,
    EventCertificateTemplate,
    EventDiscountCode,
    EventEvaluation,
    EventEvaluationForm,
    EventInvitation,
    EventRegistration,
    EventSequence,
    EventSession,
    EventSpeakerAssignment,
    EventSponsor,
    EventTicketType,
    EventWaitlist,
    SessionAttendance,
    SessionSpeaker,
    Speaker,
    Venue,
    VenueRoom,
    EventStatus,
    RegistrationStatus,
)

logger = logging.getLogger(__name__)


# ============================================================================
# REPOSITORY LIEUX
# ============================================================================

class VenueRepository(BaseRepository[Venue]):
    """Repository pour les lieux."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, Venue, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(Venue).filter(
            Venue.tenant_id == self.tenant_id,
            Venue.deleted_at.is_(None)
        )

    def find_by_code(self, code: str) -> Optional[Venue]:
        """Recherche lieu par code."""
        return self._base_query().filter(Venue.code == code).first()

    def list_active(
        self,
        city: Optional[str] = None,
        venue_type: Optional[str] = None,
        min_capacity: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Venue], int]:
        """Liste les lieux actifs."""
        query = self._base_query().filter(Venue.is_active == True)

        if city:
            query = query.filter(Venue.city.ilike(f"%{city}%"))
        if venue_type:
            query = query.filter(Venue.venue_type == venue_type)
        if min_capacity:
            query = query.filter(Venue.total_capacity >= min_capacity)

        total = query.count()
        items = query.order_by(Venue.name).offset(skip).limit(limit).all()

        return items, total

    def get_with_rooms(self, venue_id: UUID) -> Optional[Venue]:
        """Recupere lieu avec ses salles."""
        return self._base_query().filter(
            Venue.id == venue_id
        ).options(joinedload(Venue.rooms)).first()


class VenueRoomRepository(BaseRepository[VenueRoom]):
    """Repository pour les salles."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, VenueRoom, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(VenueRoom).filter(
            VenueRoom.tenant_id == self.tenant_id
        )

    def list_by_venue(
        self,
        venue_id: UUID,
        is_active: bool = True
    ) -> List[VenueRoom]:
        """Liste les salles d'un lieu."""
        return self._base_query().filter(
            VenueRoom.venue_id == venue_id,
            VenueRoom.is_active == is_active
        ).order_by(VenueRoom.name).all()

    def find_by_capacity(
        self,
        venue_id: UUID,
        min_capacity: int,
        configuration: str = "theater"
    ) -> List[VenueRoom]:
        """Trouve les salles par capacite."""
        capacity_field = f"capacity_{configuration}"
        if hasattr(VenueRoom, capacity_field):
            return self._base_query().filter(
                VenueRoom.venue_id == venue_id,
                VenueRoom.is_active == True,
                getattr(VenueRoom, capacity_field) >= min_capacity
            ).all()
        return []


# ============================================================================
# REPOSITORY EVENEMENTS
# ============================================================================

class EventRepository(BaseRepository[Event]):
    """Repository pour les evenements."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, Event, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(Event).filter(
            Event.tenant_id == self.tenant_id,
            Event.deleted_at.is_(None)
        )

    def find_by_code(self, code: str) -> Optional[Event]:
        """Recherche evenement par code."""
        return self._base_query().filter(Event.code == code).first()

    def find_by_slug(self, slug: str) -> Optional[Event]:
        """Recherche evenement par slug."""
        return self._base_query().filter(Event.slug == slug).first()

    def list_events(
        self,
        status: Optional[EventStatus] = None,
        event_type: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        is_public: Optional[bool] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Event], int]:
        """Liste les evenements avec filtres."""
        query = self._base_query().filter(Event.is_active == True)

        if status:
            query = query.filter(Event.status == status)
        if event_type:
            query = query.filter(Event.event_type == event_type)
        if from_date:
            query = query.filter(Event.start_date >= from_date)
        if to_date:
            query = query.filter(Event.end_date <= to_date)
        if is_public is not None:
            query = query.filter(Event.is_public == is_public)
        if category:
            query = query.filter(Event.category == category)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Event.title.ilike(search_term),
                    Event.code.ilike(search_term),
                    Event.description.ilike(search_term)
                )
            )

        total = query.count()
        items = query.order_by(desc(Event.start_date)).offset(skip).limit(limit).all()

        return items, total

    def list_upcoming(self, limit: int = 10) -> List[Event]:
        """Liste les evenements a venir."""
        today = date.today()
        return self._base_query().filter(
            Event.is_active == True,
            Event.start_date >= today,
            Event.status.in_([EventStatus.PUBLISHED, EventStatus.REGISTRATION_OPEN])
        ).order_by(Event.start_date).limit(limit).all()

    def list_ongoing(self) -> List[Event]:
        """Liste les evenements en cours."""
        today = date.today()
        return self._base_query().filter(
            Event.is_active == True,
            Event.start_date <= today,
            Event.end_date >= today,
            Event.status == EventStatus.IN_PROGRESS
        ).all()

    def get_with_relations(self, event_id: UUID) -> Optional[Event]:
        """Recupere evenement avec toutes ses relations."""
        return self._base_query().filter(
            Event.id == event_id
        ).options(
            joinedload(Event.venue),
            joinedload(Event.room),
            joinedload(Event.sessions),
            joinedload(Event.ticket_types),
            joinedload(Event.sponsors),
            joinedload(Event.speakers)
        ).first()

    def generate_code(self) -> str:
        """Genere un code unique EVT-YYYY-XXXX."""
        current_year = datetime.utcnow().year

        sequence = self.db.query(EventSequence).filter(
            EventSequence.tenant_id == self.tenant_id,
            EventSequence.year == current_year,
            EventSequence.prefix == "EVT"
        ).with_for_update().first()

        if not sequence:
            sequence = EventSequence(
                tenant_id=self.tenant_id,
                year=current_year,
                prefix="EVT",
                last_number=0
            )
            self.db.add(sequence)
            self.db.flush()

        sequence.last_number += 1
        return f"EVT-{current_year}-{sequence.last_number:04d}"

    def update_counters(self, event_id: UUID) -> None:
        """Met a jour les compteurs de l'evenement."""
        event = self.get_by_id(event_id)
        if not event:
            return

        registrations = self.db.query(EventRegistration).filter(
            EventRegistration.event_id == event_id,
            EventRegistration.deleted_at.is_(None)
        ).all()

        event.registered_count = len(registrations)
        event.confirmed_count = sum(
            1 for r in registrations
            if r.status in [RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN, RegistrationStatus.ATTENDED]
        )
        event.waitlist_count = sum(
            1 for r in registrations if r.status == RegistrationStatus.WAITLISTED
        )
        event.checkin_count = sum(
            1 for r in registrations
            if r.status in [RegistrationStatus.CHECKED_IN, RegistrationStatus.ATTENDED]
        )
        event.cancelled_count = sum(
            1 for r in registrations
            if r.status in [RegistrationStatus.CANCELLED, RegistrationStatus.REFUNDED]
        )

        self.db.commit()


# ============================================================================
# REPOSITORY INTERVENANTS
# ============================================================================

class SpeakerRepository(BaseRepository[Speaker]):
    """Repository pour les intervenants."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, Speaker, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(Speaker).filter(
            Speaker.tenant_id == self.tenant_id,
            Speaker.deleted_at.is_(None)
        )

    def find_by_email(self, email: str) -> Optional[Speaker]:
        """Recherche intervenant par email."""
        return self._base_query().filter(Speaker.email == email).first()

    def list_active(
        self,
        search: Optional[str] = None,
        is_internal: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Speaker], int]:
        """Liste les intervenants actifs."""
        query = self._base_query().filter(Speaker.is_active == True)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Speaker.first_name.ilike(search_term),
                    Speaker.last_name.ilike(search_term),
                    Speaker.email.ilike(search_term),
                    Speaker.company.ilike(search_term)
                )
            )
        if is_internal is not None:
            query = query.filter(Speaker.is_internal == is_internal)

        total = query.count()
        items = query.order_by(Speaker.last_name, Speaker.first_name).offset(skip).limit(limit).all()

        return items, total

    def list_by_topic(self, topic: str) -> List[Speaker]:
        """Liste les intervenants par sujet."""
        return self._base_query().filter(
            Speaker.is_active == True,
            Speaker.topics.contains([topic])
        ).all()


class SpeakerAssignmentRepository(BaseRepository[EventSpeakerAssignment]):
    """Repository pour les affectations intervenant-evenement."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, EventSpeakerAssignment, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(EventSpeakerAssignment).filter(
            EventSpeakerAssignment.tenant_id == self.tenant_id
        )

    def find_by_event_speaker(
        self,
        event_id: UUID,
        speaker_id: UUID
    ) -> Optional[EventSpeakerAssignment]:
        """Trouve une affectation par evenement et intervenant."""
        return self._base_query().filter(
            EventSpeakerAssignment.event_id == event_id,
            EventSpeakerAssignment.speaker_id == speaker_id
        ).first()

    def list_by_event(
        self,
        event_id: UUID,
        confirmed_only: bool = False
    ) -> List[EventSpeakerAssignment]:
        """Liste les affectations d'un evenement."""
        query = self._base_query().filter(
            EventSpeakerAssignment.event_id == event_id
        )
        if confirmed_only:
            query = query.filter(EventSpeakerAssignment.is_confirmed == True)

        return query.options(
            joinedload(EventSpeakerAssignment.speaker)
        ).order_by(EventSpeakerAssignment.display_order).all()

    def list_by_speaker(self, speaker_id: UUID) -> List[EventSpeakerAssignment]:
        """Liste les affectations d'un intervenant."""
        return self._base_query().filter(
            EventSpeakerAssignment.speaker_id == speaker_id
        ).options(joinedload(EventSpeakerAssignment.event)).all()


# ============================================================================
# REPOSITORY SESSIONS
# ============================================================================

class SessionRepository(BaseRepository[EventSession]):
    """Repository pour les sessions."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, EventSession, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(EventSession).filter(
            EventSession.tenant_id == self.tenant_id
        )

    def list_by_event(
        self,
        event_id: UUID,
        include_cancelled: bool = False
    ) -> List[EventSession]:
        """Liste les sessions d'un evenement."""
        query = self._base_query().filter(EventSession.event_id == event_id)

        if not include_cancelled:
            query = query.filter(EventSession.is_cancelled == False)

        return query.options(
            joinedload(EventSession.speakers).joinedload(SessionSpeaker.event_assignment).joinedload(EventSpeakerAssignment.speaker)
        ).order_by(EventSession.session_date, EventSession.start_time, EventSession.display_order).all()

    def list_by_track(self, event_id: UUID, track: str) -> List[EventSession]:
        """Liste les sessions d'un parcours."""
        return self._base_query().filter(
            EventSession.event_id == event_id,
            EventSession.track == track,
            EventSession.is_cancelled == False
        ).order_by(EventSession.session_date, EventSession.start_time).all()

    def get_agenda(self, event_id: UUID) -> dict[str, List[EventSession]]:
        """Recupere l'agenda groupe par jour."""
        sessions = self.list_by_event(event_id)
        agenda = {}

        for session in sessions:
            day = session.session_date.isoformat()
            if day not in agenda:
                agenda[day] = []
            agenda[day].append(session)

        return agenda

    def get_tracks(self, event_id: UUID) -> List[str]:
        """Recupere les parcours d'un evenement."""
        result = self.db.query(EventSession.track).filter(
            EventSession.event_id == event_id,
            EventSession.track.isnot(None),
            EventSession.is_cancelled == False
        ).distinct().all()

        return [r[0] for r in result if r[0]]


# ============================================================================
# REPOSITORY BILLETTERIE
# ============================================================================

class TicketTypeRepository(BaseRepository[EventTicketType]):
    """Repository pour les types de billets."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, EventTicketType, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(EventTicketType).filter(
            EventTicketType.tenant_id == self.tenant_id
        )

    def find_by_code(self, event_id: UUID, code: str) -> Optional[EventTicketType]:
        """Recherche type de billet par code."""
        return self._base_query().filter(
            EventTicketType.event_id == event_id,
            EventTicketType.code == code
        ).first()

    def list_by_event(
        self,
        event_id: UUID,
        available_only: bool = False
    ) -> List[EventTicketType]:
        """Liste les types de billets d'un evenement."""
        query = self._base_query().filter(EventTicketType.event_id == event_id)

        if available_only:
            now = datetime.utcnow()
            query = query.filter(
                EventTicketType.is_available == True,
                EventTicketType.is_visible == True,
                or_(
                    EventTicketType.sales_start_date.is_(None),
                    EventTicketType.sales_start_date <= now
                ),
                or_(
                    EventTicketType.sales_end_date.is_(None),
                    EventTicketType.sales_end_date >= now
                )
            )

        return query.order_by(EventTicketType.display_order).all()

    def decrement_quantity(self, ticket_type_id: UUID, quantity: int = 1) -> bool:
        """Decremente la quantite disponible."""
        ticket_type = self.get_by_id(ticket_type_id)
        if not ticket_type:
            return False

        if ticket_type.quantity_available is not None:
            remaining = ticket_type.quantity_available - ticket_type.quantity_sold - ticket_type.quantity_reserved
            if remaining < quantity:
                return False

        ticket_type.quantity_sold += quantity
        self.db.commit()
        return True


# ============================================================================
# REPOSITORY INSCRIPTIONS
# ============================================================================

class RegistrationRepository(BaseRepository[EventRegistration]):
    """Repository pour les inscriptions."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, EventRegistration, tenant_id)
        self._registration_counter = 0

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(EventRegistration).filter(
            EventRegistration.tenant_id == self.tenant_id,
            EventRegistration.deleted_at.is_(None)
        )

    def find_by_registration_number(self, reg_number: str) -> Optional[EventRegistration]:
        """Recherche par numero d'inscription."""
        return self._base_query().filter(
            EventRegistration.registration_number == reg_number
        ).first()

    def find_by_qr_code(self, qr_code: str) -> Optional[EventRegistration]:
        """Recherche par QR code."""
        return self._base_query().filter(
            EventRegistration.qr_code == qr_code
        ).first()

    def find_by_email_event(self, email: str, event_id: UUID) -> Optional[EventRegistration]:
        """Recherche inscription par email et evenement."""
        return self._base_query().filter(
            EventRegistration.email == email,
            EventRegistration.event_id == event_id
        ).first()

    def list_by_event(
        self,
        event_id: UUID,
        status: Optional[RegistrationStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[EventRegistration], int]:
        """Liste les inscriptions d'un evenement."""
        query = self._base_query().filter(EventRegistration.event_id == event_id)

        if status:
            query = query.filter(EventRegistration.status == status)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    EventRegistration.first_name.ilike(search_term),
                    EventRegistration.last_name.ilike(search_term),
                    EventRegistration.email.ilike(search_term),
                    EventRegistration.registration_number.ilike(search_term),
                    EventRegistration.company.ilike(search_term)
                )
            )

        total = query.count()
        items = query.order_by(desc(EventRegistration.created_at)).offset(skip).limit(limit).all()

        return items, total

    def list_confirmed(self, event_id: UUID) -> List[EventRegistration]:
        """Liste les inscriptions confirmees."""
        return self._base_query().filter(
            EventRegistration.event_id == event_id,
            EventRegistration.status.in_([
                RegistrationStatus.CONFIRMED,
                RegistrationStatus.CHECKED_IN,
                RegistrationStatus.ATTENDED
            ])
        ).all()

    def list_not_checked_in(self, event_id: UUID) -> List[EventRegistration]:
        """Liste les inscriptions non enregistrees."""
        return self._base_query().filter(
            EventRegistration.event_id == event_id,
            EventRegistration.status == RegistrationStatus.CONFIRMED,
            EventRegistration.checked_in == False
        ).all()

    def generate_registration_number(self, event_id: UUID) -> str:
        """Genere un numero d'inscription unique."""
        count = self.db.query(func.count(EventRegistration.id)).filter(
            EventRegistration.event_id == event_id
        ).scalar() or 0

        event = self.db.query(Event).filter(Event.id == event_id).first()
        event_code = event.code if event else "EVT"

        return f"REG-{event_code}-{count + 1:06d}"

    def generate_qr_code(self, registration_number: str) -> str:
        """Genere un QR code unique."""
        import hashlib
        return hashlib.sha256(
            f"{self.tenant_id}:{registration_number}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:32]


# ============================================================================
# REPOSITORY CHECK-IN
# ============================================================================

class CheckInRepository(BaseRepository[EventCheckIn]):
    """Repository pour les check-ins."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, EventCheckIn, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(EventCheckIn).filter(
            EventCheckIn.tenant_id == self.tenant_id
        )

    def list_by_event(
        self,
        event_id: UUID,
        session_id: Optional[UUID] = None
    ) -> List[EventCheckIn]:
        """Liste les check-ins d'un evenement."""
        query = self._base_query().filter(EventCheckIn.event_id == event_id)

        if session_id:
            query = query.filter(EventCheckIn.session_id == session_id)

        return query.order_by(desc(EventCheckIn.checked_at)).all()

    def get_stats(self, event_id: UUID) -> dict[str, Any]:
        """Calcule les statistiques de check-in."""
        checkins = self.list_by_event(event_id)

        # Par heure
        by_hour = {}
        for checkin in checkins:
            hour = checkin.checked_at.strftime("%H:00")
            by_hour[hour] = by_hour.get(hour, 0) + 1

        # Par methode
        by_method = {}
        for checkin in checkins:
            method = checkin.method or "UNKNOWN"
            by_method[method] = by_method.get(method, 0) + 1

        return {
            "total": len(checkins),
            "by_hour": by_hour,
            "by_method": by_method
        }


# ============================================================================
# REPOSITORY SPONSORS
# ============================================================================

class SponsorRepository(BaseRepository[EventSponsor]):
    """Repository pour les sponsors."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, EventSponsor, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(EventSponsor).filter(
            EventSponsor.tenant_id == self.tenant_id
        )

    def list_by_event(
        self,
        event_id: UUID,
        level: Optional[str] = None,
        visible_only: bool = True
    ) -> List[EventSponsor]:
        """Liste les sponsors d'un evenement."""
        query = self._base_query().filter(EventSponsor.event_id == event_id)

        if level:
            query = query.filter(EventSponsor.level == level)
        if visible_only:
            query = query.filter(EventSponsor.is_visible == True)

        return query.order_by(EventSponsor.display_order, EventSponsor.name).all()


# ============================================================================
# REPOSITORY CODES PROMO
# ============================================================================

class DiscountCodeRepository(BaseRepository[EventDiscountCode]):
    """Repository pour les codes promo."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, EventDiscountCode, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(EventDiscountCode).filter(
            EventDiscountCode.tenant_id == self.tenant_id
        )

    def find_by_code(self, event_id: UUID, code: str) -> Optional[EventDiscountCode]:
        """Recherche code promo par code."""
        return self._base_query().filter(
            EventDiscountCode.event_id == event_id,
            EventDiscountCode.code == code.upper()
        ).first()

    def list_by_event(self, event_id: UUID) -> List[EventDiscountCode]:
        """Liste les codes promo d'un evenement."""
        return self._base_query().filter(
            EventDiscountCode.event_id == event_id
        ).order_by(desc(EventDiscountCode.created_at)).all()


# ============================================================================
# REPOSITORY CERTIFICATS
# ============================================================================

class CertificateTemplateRepository(BaseRepository[EventCertificateTemplate]):
    """Repository pour les templates de certificat."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, EventCertificateTemplate, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(EventCertificateTemplate).filter(
            EventCertificateTemplate.tenant_id == self.tenant_id
        )

    def get_default(self, certificate_type: str) -> Optional[EventCertificateTemplate]:
        """Recupere le template par defaut."""
        return self._base_query().filter(
            EventCertificateTemplate.certificate_type == certificate_type,
            EventCertificateTemplate.is_default == True,
            EventCertificateTemplate.is_active == True
        ).first()


class CertificateRepository(BaseRepository[EventCertificate]):
    """Repository pour les certificats."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, EventCertificate, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(EventCertificate).filter(
            EventCertificate.tenant_id == self.tenant_id
        )

    def find_by_registration(self, registration_id: UUID) -> Optional[EventCertificate]:
        """Recherche certificat par inscription."""
        return self._base_query().filter(
            EventCertificate.registration_id == registration_id
        ).first()

    def find_by_verification_code(self, code: str) -> Optional[EventCertificate]:
        """Recherche certificat par code de verification."""
        return self._base_query().filter(
            EventCertificate.verification_code == code
        ).first()

    def generate_number(self, event_id: UUID) -> str:
        """Genere un numero de certificat."""
        count = self.db.query(func.count(EventCertificate.id)).filter(
            EventCertificate.event_id == event_id
        ).scalar() or 0

        return f"CERT-{datetime.utcnow().year}-{count + 1:06d}"

    def generate_verification_code(self, certificate_number: str) -> str:
        """Genere un code de verification."""
        import hashlib
        return hashlib.sha256(
            f"{self.tenant_id}:{certificate_number}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16].upper()


# ============================================================================
# REPOSITORY EVALUATIONS
# ============================================================================

class EvaluationFormRepository(BaseRepository[EventEvaluationForm]):
    """Repository pour les formulaires d'evaluation."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, EventEvaluationForm, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(EventEvaluationForm).filter(
            EventEvaluationForm.tenant_id == self.tenant_id
        )

    def get_default(self, form_type: str) -> Optional[EventEvaluationForm]:
        """Recupere le formulaire par defaut."""
        return self._base_query().filter(
            EventEvaluationForm.form_type == form_type,
            EventEvaluationForm.is_default == True,
            EventEvaluationForm.is_active == True
        ).first()


class EvaluationRepository(BaseRepository[EventEvaluation]):
    """Repository pour les evaluations."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, EventEvaluation, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(EventEvaluation).filter(
            EventEvaluation.tenant_id == self.tenant_id
        )

    def find_by_registration_event(
        self,
        registration_id: UUID,
        event_id: UUID,
        evaluation_type: str = "EVENT"
    ) -> Optional[EventEvaluation]:
        """Recherche evaluation par inscription et evenement."""
        return self._base_query().filter(
            EventEvaluation.registration_id == registration_id,
            EventEvaluation.event_id == event_id,
            EventEvaluation.evaluation_type == evaluation_type
        ).first()

    def get_stats(self, event_id: UUID) -> dict[str, Any]:
        """Calcule les statistiques d'evaluation."""
        evaluations = self._base_query().filter(
            EventEvaluation.event_id == event_id,
            EventEvaluation.evaluation_type == "EVENT"
        ).all()

        if not evaluations:
            return {
                "total_evaluations": 0,
                "average_rating": 0.0,
                "nps_score": 0.0,
                "rating_distribution": {}
            }

        ratings = [float(e.overall_rating) for e in evaluations if e.overall_rating]
        nps_scores = [e.nps_score for e in evaluations if e.nps_score is not None]

        # Distribution des notes
        rating_distribution = {}
        for r in ratings:
            key = int(r)
            rating_distribution[key] = rating_distribution.get(key, 0) + 1

        # NPS score
        nps = 0.0
        if nps_scores:
            promoters = sum(1 for s in nps_scores if s >= 9) / len(nps_scores) * 100
            detractors = sum(1 for s in nps_scores if s <= 6) / len(nps_scores) * 100
            nps = promoters - detractors

        return {
            "total_evaluations": len(evaluations),
            "average_rating": sum(ratings) / len(ratings) if ratings else 0.0,
            "nps_score": nps,
            "rating_distribution": rating_distribution
        }


# ============================================================================
# REPOSITORY INVITATIONS
# ============================================================================

class InvitationRepository(BaseRepository[EventInvitation]):
    """Repository pour les invitations."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, EventInvitation, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(EventInvitation).filter(
            EventInvitation.tenant_id == self.tenant_id
        )

    def find_by_code(self, code: str) -> Optional[EventInvitation]:
        """Recherche invitation par code."""
        return self._base_query().filter(
            EventInvitation.invitation_code == code
        ).first()

    def find_by_email_event(self, email: str, event_id: UUID) -> Optional[EventInvitation]:
        """Recherche invitation par email et evenement."""
        return self._base_query().filter(
            EventInvitation.email == email,
            EventInvitation.event_id == event_id
        ).first()

    def list_by_event(
        self,
        event_id: UUID,
        status: Optional[str] = None
    ) -> List[EventInvitation]:
        """Liste les invitations d'un evenement."""
        query = self._base_query().filter(EventInvitation.event_id == event_id)

        if status:
            query = query.filter(EventInvitation.status == status)

        return query.order_by(desc(EventInvitation.created_at)).all()

    def generate_code(self) -> str:
        """Genere un code d'invitation unique."""
        import secrets
        return secrets.token_urlsafe(16)


# ============================================================================
# REPOSITORY WAITLIST
# ============================================================================

class WaitlistRepository(BaseRepository[EventWaitlist]):
    """Repository pour la liste d'attente."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, EventWaitlist, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(EventWaitlist).filter(
            EventWaitlist.tenant_id == self.tenant_id
        )

    def find_by_email_event(
        self,
        email: str,
        event_id: UUID,
        ticket_type_id: Optional[UUID] = None
    ) -> Optional[EventWaitlist]:
        """Recherche entree liste d'attente."""
        query = self._base_query().filter(
            EventWaitlist.email == email,
            EventWaitlist.event_id == event_id
        )

        if ticket_type_id:
            query = query.filter(EventWaitlist.ticket_type_id == ticket_type_id)

        return query.first()

    def list_waiting(
        self,
        event_id: UUID,
        ticket_type_id: Optional[UUID] = None
    ) -> List[EventWaitlist]:
        """Liste les personnes en attente."""
        query = self._base_query().filter(
            EventWaitlist.event_id == event_id,
            EventWaitlist.status == "WAITING"
        )

        if ticket_type_id:
            query = query.filter(EventWaitlist.ticket_type_id == ticket_type_id)

        return query.order_by(EventWaitlist.position).all()

    def get_next_position(self, event_id: UUID, ticket_type_id: Optional[UUID] = None) -> int:
        """Recupere la prochaine position dans la liste d'attente."""
        query = self.db.query(func.max(EventWaitlist.position)).filter(
            EventWaitlist.event_id == event_id
        )

        if ticket_type_id:
            query = query.filter(EventWaitlist.ticket_type_id == ticket_type_id)

        max_position = query.scalar()
        return (max_position or 0) + 1


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'VenueRepository',
    'VenueRoomRepository',
    'EventRepository',
    'SpeakerRepository',
    'SpeakerAssignmentRepository',
    'SessionRepository',
    'TicketTypeRepository',
    'RegistrationRepository',
    'CheckInRepository',
    'SponsorRepository',
    'DiscountCodeRepository',
    'CertificateTemplateRepository',
    'CertificateRepository',
    'EvaluationFormRepository',
    'EvaluationRepository',
    'InvitationRepository',
    'WaitlistRepository',
]
