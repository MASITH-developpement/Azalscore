"""
AZALS MODULE EVENTS - Service Implementation
=============================================

Service metier complet pour la gestion d'evenements.
Encapsule la logique metier et coordonne les repositories.
"""

import logging
import re
import secrets
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from .exceptions import (
    CheckInAlreadyDoneException,
    CheckInNotAllowedException,
    CheckInNotFoundException,
    CertificateAlreadyIssuedException,
    CertificateNotEligibleException,
    DiscountCodeExpiredException,
    DiscountCodeExhaustedException,
    DiscountCodeInactiveException,
    DiscountCodeNotApplicableException,
    DiscountCodeNotFoundException,
    EventCapacityException,
    EventCodeExistsException,
    EventNotFoundException,
    EventStatusException,
    InvitationExpiredException,
    InvitationNotFoundException,
    RegistrationClosedException,
    RegistrationDuplicateException,
    RegistrationNotFoundException,
    RegistrationStatusException,
    SessionNotFoundException,
    SpeakerAlreadyAssignedException,
    SpeakerNotFoundException,
    TicketSoldOutException,
    TicketTypeNotFoundException,
    VenueNotFoundException,
)
from .models import (
    Event,
    EventCertificate,
    EventCheckIn,
    EventDiscountCode,
    EventEvaluation,
    EventInvitation,
    EventRegistration,
    EventSession,
    EventSpeakerAssignment,
    EventSponsor,
    EventTicketType,
    EventWaitlist,
    EventStatus,
    PaymentStatus,
    RegistrationStatus,
    SessionSpeaker,
    Speaker,
    Venue,
    VenueRoom,
    CertificateType,
    EvaluationStatus,
)
from .repository import (
    CertificateRepository,
    CertificateTemplateRepository,
    CheckInRepository,
    DiscountCodeRepository,
    EvaluationFormRepository,
    EvaluationRepository,
    EventRepository,
    InvitationRepository,
    RegistrationRepository,
    SessionRepository,
    SpeakerAssignmentRepository,
    SpeakerRepository,
    SponsorRepository,
    TicketTypeRepository,
    VenueRepository,
    VenueRoomRepository,
    WaitlistRepository,
)
from .schemas import (
    CheckInCreate,
    CheckInResponse,
    CheckInStats,
    CertificateIssue,
    CertificateResponse,
    DiscountCodeApply,
    DiscountCodeCreate,
    DiscountCodeResponse,
    DiscountCodeResult,
    EventAgenda,
    EventCreate,
    EventDashboard,
    EventResponse,
    EventStats,
    EventUpdate,
    EvaluationStats,
    EvaluationSubmit,
    GlobalEventStats,
    InvitationCreate,
    InvitationResponse,
    RegistrationCreate,
    RegistrationResponse,
    RegistrationUpdate,
    SessionCreate,
    SessionResponse,
    SessionUpdate,
    SpeakerAssignmentCreate,
    SpeakerAssignmentResponse,
    SpeakerCreate,
    SpeakerResponse,
    SpeakerUpdate,
    SponsorCreate,
    SponsorResponse,
    SponsorUpdate,
    TicketTypeCreate,
    TicketTypeResponse,
    TicketTypeUpdate,
    VenueCreate,
    VenueResponse,
    VenueRoomCreate,
    VenueRoomResponse,
    VenueUpdate,
    VenueWithRoomsResponse,
    WaitlistEntry,
    WaitlistResponse,
    AgendaDay,
)

logger = logging.getLogger(__name__)


class EventsService:
    """
    Service principal pour la gestion des evenements.

    Ce service encapsule toute la logique metier et coordonne
    les differents repositories pour garantir la coherence des donnees.

    Toutes les operations sont isolees par tenant_id.
    """

    def __init__(self, db: Session, tenant_id: str, user_id: Optional[UUID] = None):
        """
        Initialise le service.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant (isolation obligatoire)
            user_id: ID de l'utilisateur courant (optionnel, pour audit)
        """
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

        # Initialisation des repositories
        self._venue_repo = VenueRepository(db, tenant_id)
        self._room_repo = VenueRoomRepository(db, tenant_id)
        self._event_repo = EventRepository(db, tenant_id)
        self._speaker_repo = SpeakerRepository(db, tenant_id)
        self._speaker_assign_repo = SpeakerAssignmentRepository(db, tenant_id)
        self._session_repo = SessionRepository(db, tenant_id)
        self._ticket_repo = TicketTypeRepository(db, tenant_id)
        self._registration_repo = RegistrationRepository(db, tenant_id)
        self._checkin_repo = CheckInRepository(db, tenant_id)
        self._sponsor_repo = SponsorRepository(db, tenant_id)
        self._discount_repo = DiscountCodeRepository(db, tenant_id)
        self._cert_template_repo = CertificateTemplateRepository(db, tenant_id)
        self._certificate_repo = CertificateRepository(db, tenant_id)
        self._eval_form_repo = EvaluationFormRepository(db, tenant_id)
        self._evaluation_repo = EvaluationRepository(db, tenant_id)
        self._invitation_repo = InvitationRepository(db, tenant_id)
        self._waitlist_repo = WaitlistRepository(db, tenant_id)

    # =========================================================================
    # LIEUX ET SALLES
    # =========================================================================

    def create_venue(self, data: VenueCreate) -> VenueResponse:
        """Cree un nouveau lieu."""
        # Verifier unicite du code
        existing = self._venue_repo.find_by_code(data.code)
        if existing:
            raise EventCodeExistsException(data.code)

        venue = Venue(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            **data.model_dump()
        )

        self.db.add(venue)
        self.db.commit()
        self.db.refresh(venue)

        logger.info(f"Venue created: {venue.id}", extra={"tenant_id": self.tenant_id})
        return VenueResponse.model_validate(venue)

    def get_venue(self, venue_id: UUID) -> Optional[VenueResponse]:
        """Recupere un lieu."""
        venue = self._venue_repo.get_by_id(venue_id)
        if venue:
            return VenueResponse.model_validate(venue)
        return None

    def get_venue_with_rooms(self, venue_id: UUID) -> Optional[VenueWithRoomsResponse]:
        """Recupere un lieu avec ses salles."""
        venue = self._venue_repo.get_with_rooms(venue_id)
        if venue:
            return VenueWithRoomsResponse.model_validate(venue)
        return None

    def update_venue(self, venue_id: UUID, data: VenueUpdate) -> Optional[VenueResponse]:
        """Met a jour un lieu."""
        venue = self._venue_repo.get_by_id(venue_id)
        if not venue:
            raise VenueNotFoundException(str(venue_id))

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(venue, field, value)

        venue.version += 1
        self.db.commit()
        self.db.refresh(venue)

        return VenueResponse.model_validate(venue)

    def delete_venue(self, venue_id: UUID) -> bool:
        """Supprime un lieu (soft delete)."""
        venue = self._venue_repo.get_by_id(venue_id)
        if not venue:
            return False

        venue.deleted_at = datetime.utcnow()
        venue.is_active = False
        self.db.commit()
        return True

    def list_venues(
        self,
        city: Optional[str] = None,
        venue_type: Optional[str] = None,
        min_capacity: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[VenueResponse], int]:
        """Liste les lieux."""
        venues, total = self._venue_repo.list_active(
            city=city,
            venue_type=venue_type,
            min_capacity=min_capacity,
            skip=skip,
            limit=limit
        )
        return [VenueResponse.model_validate(v) for v in venues], total

    def create_room(self, data: VenueRoomCreate) -> VenueRoomResponse:
        """Cree une salle dans un lieu."""
        venue = self._venue_repo.get_by_id(data.venue_id)
        if not venue:
            raise VenueNotFoundException(str(data.venue_id))

        room = VenueRoom(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )

        self.db.add(room)
        self.db.commit()
        self.db.refresh(room)

        return VenueRoomResponse.model_validate(room)

    def list_rooms(self, venue_id: UUID) -> List[VenueRoomResponse]:
        """Liste les salles d'un lieu."""
        rooms = self._room_repo.list_by_venue(venue_id)
        return [VenueRoomResponse.model_validate(r) for r in rooms]

    # =========================================================================
    # EVENEMENTS
    # =========================================================================

    def create_event(self, data: EventCreate) -> EventResponse:
        """Cree un nouvel evenement."""
        # Generer le code si non fourni
        code = data.code or self._event_repo.generate_code()

        # Verifier unicite du code
        existing = self._event_repo.find_by_code(code)
        if existing:
            raise EventCodeExistsException(code)

        # Generer le slug
        slug = self._generate_slug(data.title)

        event = Event(
            tenant_id=self.tenant_id,
            code=code,
            slug=slug,
            created_by=self.user_id,
            **data.model_dump(exclude={'code'})
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        logger.info(f"Event created: {event.id}", extra={"tenant_id": self.tenant_id})
        return EventResponse.model_validate(event)

    def get_event(self, event_id: UUID) -> Optional[EventResponse]:
        """Recupere un evenement."""
        event = self._event_repo.get_by_id(event_id)
        if event:
            return EventResponse.model_validate(event)
        return None

    def get_event_by_code(self, code: str) -> Optional[EventResponse]:
        """Recupere un evenement par code."""
        event = self._event_repo.find_by_code(code)
        if event:
            return EventResponse.model_validate(event)
        return None

    def get_event_by_slug(self, slug: str) -> Optional[EventResponse]:
        """Recupere un evenement par slug."""
        event = self._event_repo.find_by_slug(slug)
        if event:
            return EventResponse.model_validate(event)
        return None

    def update_event(self, event_id: UUID, data: EventUpdate) -> EventResponse:
        """Met a jour un evenement."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(event, field, value)

        event.version += 1
        self.db.commit()
        self.db.refresh(event)

        return EventResponse.model_validate(event)

    def delete_event(self, event_id: UUID) -> bool:
        """Supprime un evenement (soft delete)."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            return False

        event.deleted_at = datetime.utcnow()
        event.is_active = False
        self.db.commit()
        return True

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
    ) -> Tuple[List[EventResponse], int]:
        """Liste les evenements."""
        events, total = self._event_repo.list_events(
            status=status,
            event_type=event_type,
            from_date=from_date,
            to_date=to_date,
            is_public=is_public,
            category=category,
            search=search,
            skip=skip,
            limit=limit
        )
        return [EventResponse.model_validate(e) for e in events], total

    def publish_event(self, event_id: UUID) -> EventResponse:
        """Publie un evenement."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        if event.status not in [EventStatus.DRAFT, EventStatus.PLANNED]:
            raise EventStatusException(event.status.value, "publish")

        event.status = EventStatus.PUBLISHED
        event.published_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(event)

        logger.info(f"Event published: {event_id}", extra={"tenant_id": self.tenant_id})
        return EventResponse.model_validate(event)

    def open_registration(self, event_id: UUID) -> EventResponse:
        """Ouvre les inscriptions."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        if event.status not in [EventStatus.PUBLISHED, EventStatus.REGISTRATION_CLOSED]:
            raise EventStatusException(event.status.value, "open_registration")

        event.status = EventStatus.REGISTRATION_OPEN
        event.registration_open = True
        self.db.commit()
        self.db.refresh(event)

        return EventResponse.model_validate(event)

    def close_registration(self, event_id: UUID) -> EventResponse:
        """Ferme les inscriptions."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        event.status = EventStatus.REGISTRATION_CLOSED
        event.registration_open = False
        self.db.commit()
        self.db.refresh(event)

        return EventResponse.model_validate(event)

    def start_event(self, event_id: UUID) -> EventResponse:
        """Demarre un evenement."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        event.status = EventStatus.IN_PROGRESS
        event.registration_open = False
        self.db.commit()
        self.db.refresh(event)

        return EventResponse.model_validate(event)

    def complete_event(self, event_id: UUID) -> EventResponse:
        """Termine un evenement."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        event.status = EventStatus.COMPLETED
        event.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(event)

        # Marquer les non-presences
        self._mark_no_shows(event_id)

        return EventResponse.model_validate(event)

    def cancel_event(self, event_id: UUID, reason: Optional[str] = None) -> EventResponse:
        """Annule un evenement."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        event.status = EventStatus.CANCELLED
        event.cancelled_at = datetime.utcnow()
        event.cancellation_reason = reason
        event.registration_open = False
        self.db.commit()
        self.db.refresh(event)

        return EventResponse.model_validate(event)

    # =========================================================================
    # INTERVENANTS
    # =========================================================================

    def create_speaker(self, data: SpeakerCreate) -> SpeakerResponse:
        """Cree un intervenant."""
        speaker = Speaker(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            **data.model_dump()
        )

        self.db.add(speaker)
        self.db.commit()
        self.db.refresh(speaker)

        return SpeakerResponse.model_validate(speaker)

    def get_speaker(self, speaker_id: UUID) -> Optional[SpeakerResponse]:
        """Recupere un intervenant."""
        speaker = self._speaker_repo.get_by_id(speaker_id)
        if speaker:
            return SpeakerResponse.model_validate(speaker)
        return None

    def update_speaker(self, speaker_id: UUID, data: SpeakerUpdate) -> SpeakerResponse:
        """Met a jour un intervenant."""
        speaker = self._speaker_repo.get_by_id(speaker_id)
        if not speaker:
            raise SpeakerNotFoundException(str(speaker_id))

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(speaker, field, value)

        speaker.version += 1
        self.db.commit()
        self.db.refresh(speaker)

        return SpeakerResponse.model_validate(speaker)

    def list_speakers(
        self,
        search: Optional[str] = None,
        is_internal: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[SpeakerResponse], int]:
        """Liste les intervenants."""
        speakers, total = self._speaker_repo.list_active(
            search=search,
            is_internal=is_internal,
            skip=skip,
            limit=limit
        )
        return [SpeakerResponse.model_validate(s) for s in speakers], total

    def assign_speaker_to_event(
        self,
        event_id: UUID,
        data: SpeakerAssignmentCreate
    ) -> SpeakerAssignmentResponse:
        """Affecte un intervenant a un evenement."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        speaker = self._speaker_repo.get_by_id(data.speaker_id)
        if not speaker:
            raise SpeakerNotFoundException(str(data.speaker_id))

        # Verifier si deja affecte
        existing = self._speaker_assign_repo.find_by_event_speaker(event_id, data.speaker_id)
        if existing:
            raise SpeakerAlreadyAssignedException(str(data.speaker_id), str(event_id))

        assignment = EventSpeakerAssignment(
            tenant_id=self.tenant_id,
            event_id=event_id,
            **data.model_dump()
        )

        self.db.add(assignment)

        # Mettre a jour compteur speaker
        speaker.total_events += 1

        self.db.commit()
        self.db.refresh(assignment)

        return SpeakerAssignmentResponse.model_validate(assignment)

    def list_event_speakers(self, event_id: UUID) -> List[SpeakerAssignmentResponse]:
        """Liste les intervenants d'un evenement."""
        assignments = self._speaker_assign_repo.list_by_event(event_id)
        return [SpeakerAssignmentResponse.model_validate(a) for a in assignments]

    # =========================================================================
    # SESSIONS
    # =========================================================================

    def create_session(self, event_id: UUID, data: SessionCreate) -> SessionResponse:
        """Cree une session."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        session = EventSession(
            tenant_id=self.tenant_id,
            event_id=event_id,
            created_by=self.user_id,
            **data.model_dump(exclude={'speaker_ids'})
        )

        self.db.add(session)
        self.db.flush()

        # Ajouter les speakers
        for speaker_id in data.speaker_ids:
            assignment = self._speaker_assign_repo.find_by_event_speaker(event_id, speaker_id)
            if assignment:
                session_speaker = SessionSpeaker(
                    tenant_id=self.tenant_id,
                    session_id=session.id,
                    event_assignment_id=assignment.id
                )
                self.db.add(session_speaker)

        self.db.commit()
        self.db.refresh(session)

        return SessionResponse.model_validate(session)

    def get_session(self, session_id: UUID) -> Optional[SessionResponse]:
        """Recupere une session."""
        session = self._session_repo.get_by_id(session_id)
        if session:
            return SessionResponse.model_validate(session)
        return None

    def update_session(self, session_id: UUID, data: SessionUpdate) -> SessionResponse:
        """Met a jour une session."""
        session = self._session_repo.get_by_id(session_id)
        if not session:
            raise SessionNotFoundException(str(session_id))

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(session, field, value)

        session.version += 1
        self.db.commit()
        self.db.refresh(session)

        return SessionResponse.model_validate(session)

    def list_sessions(self, event_id: UUID) -> List[SessionResponse]:
        """Liste les sessions d'un evenement."""
        sessions = self._session_repo.list_by_event(event_id)
        return [SessionResponse.model_validate(s) for s in sessions]

    def get_agenda(self, event_id: UUID) -> EventAgenda:
        """Recupere l'agenda de l'evenement."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        agenda_data = self._session_repo.get_agenda(event_id)
        tracks = self._session_repo.get_tracks(event_id)

        days = []
        for day_str, sessions in sorted(agenda_data.items()):
            days.append(AgendaDay(
                date=date.fromisoformat(day_str),
                sessions=[SessionResponse.model_validate(s) for s in sessions]
            ))

        return EventAgenda(
            event_id=event_id,
            event_title=event.title,
            days=days,
            tracks=tracks
        )

    # =========================================================================
    # BILLETTERIE
    # =========================================================================

    def create_ticket_type(self, event_id: UUID, data: TicketTypeCreate) -> TicketTypeResponse:
        """Cree un type de billet."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        existing = self._ticket_repo.find_by_code(event_id, data.code)
        if existing:
            raise EventCodeExistsException(data.code)

        ticket_type = EventTicketType(
            tenant_id=self.tenant_id,
            event_id=event_id,
            **data.model_dump()
        )

        self.db.add(ticket_type)
        self.db.commit()
        self.db.refresh(ticket_type)

        return TicketTypeResponse.model_validate(ticket_type)

    def update_ticket_type(self, ticket_type_id: UUID, data: TicketTypeUpdate) -> TicketTypeResponse:
        """Met a jour un type de billet."""
        ticket_type = self._ticket_repo.get_by_id(ticket_type_id)
        if not ticket_type:
            raise TicketTypeNotFoundException(str(ticket_type_id))

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(ticket_type, field, value)

        self.db.commit()
        self.db.refresh(ticket_type)

        return TicketTypeResponse.model_validate(ticket_type)

    def list_ticket_types(self, event_id: UUID, available_only: bool = False) -> List[TicketTypeResponse]:
        """Liste les types de billets."""
        ticket_types = self._ticket_repo.list_by_event(event_id, available_only=available_only)
        return [TicketTypeResponse.model_validate(t) for t in ticket_types]

    # =========================================================================
    # INSCRIPTIONS
    # =========================================================================

    def register(self, event_id: UUID, data: RegistrationCreate) -> RegistrationResponse:
        """Inscrit un participant."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        # Verifier inscriptions ouvertes
        if not event.registration_open:
            raise RegistrationClosedException(str(event_id))

        # Verifier doublon
        existing = self._registration_repo.find_by_email_event(data.email, event_id)
        if existing:
            raise RegistrationDuplicateException(data.email, str(event_id))

        # Verifier type de billet
        ticket_type = self._ticket_repo.get_by_id(data.ticket_type_id)
        if not ticket_type:
            raise TicketTypeNotFoundException(str(data.ticket_type_id))

        # Verifier disponibilite
        if ticket_type.quantity_available is not None:
            remaining = ticket_type.quantity_available - ticket_type.quantity_sold
            if remaining <= 0:
                if event.waitlist_enabled:
                    return self._add_to_waitlist(event_id, data)
                raise TicketSoldOutException(str(ticket_type.id), ticket_type.name)

        # Verifier capacite evenement
        if event.max_attendees is not None:
            if event.confirmed_count >= event.max_attendees:
                if event.waitlist_enabled:
                    return self._add_to_waitlist(event_id, data)
                raise EventCapacityException(str(event_id), event.confirmed_count, event.max_attendees)

        # Calculer tarification
        ticket_price = ticket_type.price
        discount_amount = Decimal("0.00")

        if data.discount_code:
            result = self._apply_discount(event_id, data.discount_code, ticket_type.id, ticket_price)
            if result.valid:
                discount_amount = result.discount_amount

        tax_amount = Decimal("0.00")
        if ticket_type.tax_rate and not ticket_type.tax_included:
            tax_amount = (ticket_price - discount_amount) * ticket_type.tax_rate / 100

        total_amount = ticket_price - discount_amount + tax_amount

        # Generer numero et QR code
        reg_number = self._registration_repo.generate_registration_number(event_id)
        qr_code = self._registration_repo.generate_qr_code(reg_number)

        # Determiner statut initial
        initial_status = RegistrationStatus.PENDING
        payment_status = PaymentStatus.PENDING

        if event.is_free or total_amount == Decimal("0.00"):
            initial_status = RegistrationStatus.CONFIRMED
            payment_status = PaymentStatus.PAID

        if event.approval_required or ticket_type.requires_approval:
            initial_status = RegistrationStatus.PENDING

        registration = EventRegistration(
            tenant_id=self.tenant_id,
            event_id=event_id,
            ticket_type_id=data.ticket_type_id,
            registration_number=reg_number,
            qr_code=qr_code,
            status=initial_status,
            payment_status=payment_status,
            ticket_price=ticket_price,
            discount_code=data.discount_code,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            currency=ticket_type.currency,
            created_by=self.user_id,
            **data.model_dump(exclude={'ticket_type_id', 'discount_code'})
        )

        self.db.add(registration)

        # Mettre a jour compteurs
        ticket_type.quantity_sold += 1
        self._event_repo.update_counters(event_id)

        self.db.commit()
        self.db.refresh(registration)

        logger.info(f"Registration created: {registration.id}", extra={"tenant_id": self.tenant_id})
        return RegistrationResponse.model_validate(registration)

    def get_registration(self, registration_id: UUID) -> Optional[RegistrationResponse]:
        """Recupere une inscription."""
        registration = self._registration_repo.get_by_id(registration_id)
        if registration:
            return RegistrationResponse.model_validate(registration)
        return None

    def get_registration_by_number(self, reg_number: str) -> Optional[RegistrationResponse]:
        """Recupere une inscription par numero."""
        registration = self._registration_repo.find_by_registration_number(reg_number)
        if registration:
            return RegistrationResponse.model_validate(registration)
        return None

    def get_registration_by_qr(self, qr_code: str) -> Optional[RegistrationResponse]:
        """Recupere une inscription par QR code."""
        registration = self._registration_repo.find_by_qr_code(qr_code)
        if registration:
            return RegistrationResponse.model_validate(registration)
        return None

    def update_registration(self, registration_id: UUID, data: RegistrationUpdate) -> RegistrationResponse:
        """Met a jour une inscription."""
        registration = self._registration_repo.get_by_id(registration_id)
        if not registration:
            raise RegistrationNotFoundException(str(registration_id))

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(registration, field, value)

        registration.version += 1
        self.db.commit()
        self.db.refresh(registration)

        # Mettre a jour compteurs
        self._event_repo.update_counters(registration.event_id)

        return RegistrationResponse.model_validate(registration)

    def confirm_registration(self, registration_id: UUID, payment_reference: Optional[str] = None) -> RegistrationResponse:
        """Confirme une inscription."""
        registration = self._registration_repo.get_by_id(registration_id)
        if not registration:
            raise RegistrationNotFoundException(str(registration_id))

        if registration.status not in [RegistrationStatus.PENDING, RegistrationStatus.WAITLISTED]:
            raise RegistrationStatusException(registration.status.value, "confirm")

        registration.status = RegistrationStatus.CONFIRMED
        registration.payment_status = PaymentStatus.PAID
        registration.payment_reference = payment_reference
        registration.amount_paid = registration.total_amount
        registration.payment_date = datetime.utcnow()

        # Mettre a jour revenus
        event = self._event_repo.get_by_id(registration.event_id)
        if event:
            event.total_revenue += registration.amount_paid

        self.db.commit()
        self.db.refresh(registration)

        # Mettre a jour compteurs
        self._event_repo.update_counters(registration.event_id)

        return RegistrationResponse.model_validate(registration)

    def cancel_registration(
        self,
        registration_id: UUID,
        reason: Optional[str] = None,
        refund: bool = False
    ) -> RegistrationResponse:
        """Annule une inscription."""
        registration = self._registration_repo.get_by_id(registration_id)
        if not registration:
            raise RegistrationNotFoundException(str(registration_id))

        if registration.status in [RegistrationStatus.CANCELLED, RegistrationStatus.REFUNDED]:
            raise RegistrationStatusException(registration.status.value, "cancel")

        registration.status = RegistrationStatus.REFUNDED if refund else RegistrationStatus.CANCELLED
        registration.cancelled_at = datetime.utcnow()
        registration.cancelled_by = self.user_id
        registration.cancellation_reason = reason

        if refund and registration.amount_paid > 0:
            registration.refund_requested = True
            registration.refund_amount = registration.amount_paid
            registration.refund_date = datetime.utcnow()

            # Mettre a jour revenus
            event = self._event_repo.get_by_id(registration.event_id)
            if event:
                event.total_refunds += registration.refund_amount

        # Liberer la place
        ticket_type = self._ticket_repo.get_by_id(registration.ticket_type_id)
        if ticket_type:
            ticket_type.quantity_sold = max(0, ticket_type.quantity_sold - 1)

        self.db.commit()
        self.db.refresh(registration)

        # Promouvoir de la liste d'attente
        self._promote_from_waitlist(registration.event_id, registration.ticket_type_id)

        # Mettre a jour compteurs
        self._event_repo.update_counters(registration.event_id)

        return RegistrationResponse.model_validate(registration)

    def list_registrations(
        self,
        event_id: UUID,
        status: Optional[RegistrationStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[RegistrationResponse], int]:
        """Liste les inscriptions d'un evenement."""
        registrations, total = self._registration_repo.list_by_event(
            event_id=event_id,
            status=status,
            search=search,
            skip=skip,
            limit=limit
        )
        return [RegistrationResponse.model_validate(r) for r in registrations], total

    # =========================================================================
    # CHECK-IN
    # =========================================================================

    def check_in(self, event_id: UUID, data: CheckInCreate) -> CheckInResponse:
        """Enregistre un check-in."""
        # Trouver l'inscription
        registration = None

        if data.registration_id:
            registration = self._registration_repo.get_by_id(data.registration_id)
        elif data.qr_code:
            registration = self._registration_repo.find_by_qr_code(data.qr_code)
        elif data.registration_number:
            registration = self._registration_repo.find_by_registration_number(data.registration_number)

        if not registration:
            raise CheckInNotFoundException(
                str(data.registration_id or data.qr_code or data.registration_number)
            )

        # Verifier evenement
        if str(registration.event_id) != str(event_id):
            raise CheckInNotAllowedException(
                str(registration.id),
                "L'inscription ne correspond pas a cet evenement"
            )

        # Verifier statut
        if registration.status not in [RegistrationStatus.CONFIRMED, RegistrationStatus.PENDING]:
            raise CheckInNotAllowedException(
                str(registration.id),
                f"Statut inscription: {registration.status.value}"
            )

        # Verifier si deja enregistre
        if registration.checked_in and not data.session_id:
            raise CheckInAlreadyDoneException(str(registration.id))

        # Creer le check-in
        checkin = EventCheckIn(
            tenant_id=self.tenant_id,
            event_id=event_id,
            registration_id=registration.id,
            session_id=data.session_id,
            check_in_type="IN",
            method=data.method,
            location=data.location,
            device_id=data.device_id,
            checked_by=self.user_id,
            notes=data.notes
        )

        self.db.add(checkin)

        # Mettre a jour inscription
        if not data.session_id:
            registration.status = RegistrationStatus.CHECKED_IN
            registration.checked_in = True
            registration.checked_in_at = datetime.utcnow()
            registration.checked_in_by = self.user_id
            registration.check_in_method = data.method
            registration.check_in_location = data.location

        self.db.commit()
        self.db.refresh(checkin)

        # Mettre a jour compteurs
        self._event_repo.update_counters(event_id)

        result = CheckInResponse.model_validate(checkin)
        result.registration = RegistrationResponse.model_validate(registration)
        return result

    def get_checkin_stats(self, event_id: UUID) -> CheckInStats:
        """Recupere les statistiques de check-in."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        stats = self._checkin_repo.get_stats(event_id)

        return CheckInStats(
            total_expected=event.confirmed_count,
            checked_in=event.checkin_count,
            remaining=event.confirmed_count - event.checkin_count,
            check_in_rate=event.checkin_count / event.confirmed_count * 100 if event.confirmed_count > 0 else 0,
            by_hour=stats.get("by_hour", {}),
            by_method=stats.get("by_method", {})
        )

    # =========================================================================
    # SPONSORS
    # =========================================================================

    def add_sponsor(self, event_id: UUID, data: SponsorCreate) -> SponsorResponse:
        """Ajoute un sponsor."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        sponsor = EventSponsor(
            tenant_id=self.tenant_id,
            event_id=event_id,
            **data.model_dump()
        )

        self.db.add(sponsor)
        self.db.commit()
        self.db.refresh(sponsor)

        return SponsorResponse.model_validate(sponsor)

    def update_sponsor(self, sponsor_id: UUID, data: SponsorUpdate) -> SponsorResponse:
        """Met a jour un sponsor."""
        sponsor = self._sponsor_repo.get_by_id(sponsor_id)
        if not sponsor:
            raise EventNotFoundException(str(sponsor_id))

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(sponsor, field, value)

        self.db.commit()
        self.db.refresh(sponsor)

        return SponsorResponse.model_validate(sponsor)

    def list_sponsors(self, event_id: UUID, level: Optional[str] = None) -> List[SponsorResponse]:
        """Liste les sponsors d'un evenement."""
        sponsors = self._sponsor_repo.list_by_event(event_id, level=level)
        return [SponsorResponse.model_validate(s) for s in sponsors]

    # =========================================================================
    # CODES PROMO
    # =========================================================================

    def create_discount_code(self, event_id: UUID, data: DiscountCodeCreate) -> DiscountCodeResponse:
        """Cree un code promo."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        existing = self._discount_repo.find_by_code(event_id, data.code)
        if existing:
            raise EventCodeExistsException(data.code)

        discount = EventDiscountCode(
            tenant_id=self.tenant_id,
            event_id=event_id,
            code=data.code.upper(),
            created_by=self.user_id,
            **data.model_dump(exclude={'code'})
        )

        self.db.add(discount)
        self.db.commit()
        self.db.refresh(discount)

        return DiscountCodeResponse.model_validate(discount)

    def apply_discount_code(self, event_id: UUID, data: DiscountCodeApply) -> DiscountCodeResult:
        """Applique un code promo."""
        ticket_type = self._ticket_repo.get_by_id(data.ticket_type_id)
        if not ticket_type:
            raise TicketTypeNotFoundException(str(data.ticket_type_id))

        ticket_price = ticket_type.price * data.quantity
        return self._apply_discount(event_id, data.code, data.ticket_type_id, ticket_price)

    def list_discount_codes(self, event_id: UUID) -> List[DiscountCodeResponse]:
        """Liste les codes promo d'un evenement."""
        codes = self._discount_repo.list_by_event(event_id)
        return [DiscountCodeResponse.model_validate(c) for c in codes]

    # =========================================================================
    # CERTIFICATS
    # =========================================================================

    def issue_certificate(self, event_id: UUID, data: CertificateIssue) -> CertificateResponse:
        """Emet un certificat."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        registration = self._registration_repo.get_by_id(data.registration_id)
        if not registration:
            raise RegistrationNotFoundException(str(data.registration_id))

        # Verifier si deja emis
        existing = self._certificate_repo.find_by_registration(data.registration_id)
        if existing:
            raise CertificateAlreadyIssuedException(str(data.registration_id))

        # Verifier eligibilite
        if registration.status not in [RegistrationStatus.CHECKED_IN, RegistrationStatus.ATTENDED]:
            raise CertificateNotEligibleException(
                str(data.registration_id),
                f"Statut: {registration.status.value}"
            )

        if event.min_attendance_for_certificate and registration.attendance_percentage:
            if registration.attendance_percentage < event.min_attendance_for_certificate:
                raise CertificateNotEligibleException(
                    str(data.registration_id),
                    f"Presence insuffisante: {registration.attendance_percentage}%"
                )

        # Generer certificat
        cert_number = self._certificate_repo.generate_number(event_id)
        verification_code = self._certificate_repo.generate_verification_code(cert_number)

        certificate = EventCertificate(
            tenant_id=self.tenant_id,
            event_id=event_id,
            registration_id=data.registration_id,
            template_id=data.template_id or event.certificate_template_id,
            certificate_number=cert_number,
            certificate_type=CertificateType.ATTENDANCE,
            recipient_name=registration.full_name,
            recipient_email=registration.email,
            event_title=event.title,
            event_date=event.start_date,
            hours_attended=data.hours_attended,
            grade=data.grade,
            additional_info=data.additional_info,
            verification_code=verification_code,
            issued_by=self.user_id
        )

        self.db.add(certificate)

        # Mettre a jour inscription
        registration.certificate_issued = True
        registration.certificate_issued_at = datetime.utcnow()
        registration.certificate_id = certificate.id

        self.db.commit()
        self.db.refresh(certificate)

        return CertificateResponse.model_validate(certificate)

    def verify_certificate(self, verification_code: str) -> Optional[CertificateResponse]:
        """Verifie un certificat."""
        certificate = self._certificate_repo.find_by_verification_code(verification_code)
        if certificate:
            return CertificateResponse.model_validate(certificate)
        return None

    # =========================================================================
    # EVALUATIONS
    # =========================================================================

    def submit_evaluation(self, event_id: UUID, data: EvaluationSubmit) -> EvaluationResponse:
        """Soumet une evaluation."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        # Verifier si deja soumise
        if data.registration_id:
            existing = self._evaluation_repo.find_by_registration_event(
                data.registration_id, event_id, data.evaluation_type
            )
            if existing:
                from .exceptions import EvaluationAlreadySubmittedException
                raise EvaluationAlreadySubmittedException(str(data.registration_id), data.evaluation_type)

        evaluation = EventEvaluation(
            tenant_id=self.tenant_id,
            event_id=event_id,
            status=EvaluationStatus.COMPLETED,
            **data.model_dump()
        )

        self.db.add(evaluation)

        # Mettre a jour inscription
        if data.registration_id:
            registration = self._registration_repo.get_by_id(data.registration_id)
            if registration:
                registration.evaluation_completed = True
                registration.evaluation_completed_at = datetime.utcnow()
                registration.evaluation_id = evaluation.id

        self.db.commit()
        self.db.refresh(evaluation)

        return EvaluationResponse.model_validate(evaluation)

    def get_evaluation_stats(self, event_id: UUID) -> EvaluationStats:
        """Recupere les statistiques d'evaluation."""
        stats = self._evaluation_repo.get_stats(event_id)

        # Calculer taux de reponse
        event = self._event_repo.get_by_id(event_id)
        response_rate = 0.0
        if event and event.checkin_count > 0:
            response_rate = stats["total_evaluations"] / event.checkin_count * 100

        return EvaluationStats(
            total_evaluations=stats["total_evaluations"],
            response_rate=response_rate,
            average_rating=stats["average_rating"],
            nps_score=stats["nps_score"],
            rating_distribution=stats["rating_distribution"]
        )

    # =========================================================================
    # INVITATIONS
    # =========================================================================

    def send_invitation(self, event_id: UUID, data: InvitationCreate) -> InvitationResponse:
        """Envoie une invitation."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        # Verifier si deja invite
        existing = self._invitation_repo.find_by_email_event(data.email, event_id)
        if existing:
            # Retourner l'invitation existante
            return InvitationResponse.model_validate(existing)

        invitation = EventInvitation(
            tenant_id=self.tenant_id,
            event_id=event_id,
            invitation_code=self._invitation_repo.generate_code(),
            status="SENT",
            sent_at=datetime.utcnow(),
            created_by=self.user_id,
            **data.model_dump()
        )

        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)

        # TODO: Envoyer email

        return InvitationResponse.model_validate(invitation)

    def accept_invitation(self, invitation_code: str) -> InvitationResponse:
        """Accepte une invitation."""
        invitation = self._invitation_repo.find_by_code(invitation_code)
        if not invitation:
            raise InvitationNotFoundException(invitation_code)

        if invitation.expires_at and invitation.expires_at < datetime.utcnow():
            raise InvitationExpiredException(invitation_code)

        if invitation.status in ["ACCEPTED", "DECLINED"]:
            from .exceptions import InvitationAlreadyUsedException
            raise InvitationAlreadyUsedException(invitation_code)

        invitation.status = "ACCEPTED"
        invitation.response = "ACCEPTED"
        invitation.responded_at = datetime.utcnow()
        invitation.viewed_at = invitation.viewed_at or datetime.utcnow()

        self.db.commit()
        self.db.refresh(invitation)

        return InvitationResponse.model_validate(invitation)

    def list_invitations(self, event_id: UUID, status: Optional[str] = None) -> List[InvitationResponse]:
        """Liste les invitations d'un evenement."""
        invitations = self._invitation_repo.list_by_event(event_id, status=status)
        return [InvitationResponse.model_validate(i) for i in invitations]

    # =========================================================================
    # WAITLIST
    # =========================================================================

    def add_to_waitlist(self, event_id: UUID, data: WaitlistEntry) -> WaitlistResponse:
        """Ajoute a la liste d'attente."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        # Verifier si deja inscrit
        existing = self._registration_repo.find_by_email_event(data.email, event_id)
        if existing:
            raise RegistrationDuplicateException(data.email, str(event_id))

        # Verifier si deja en attente
        existing_wait = self._waitlist_repo.find_by_email_event(
            data.email, event_id, data.ticket_type_id
        )
        if existing_wait:
            return WaitlistResponse.model_validate(existing_wait)

        position = self._waitlist_repo.get_next_position(event_id, data.ticket_type_id)

        waitlist_entry = EventWaitlist(
            tenant_id=self.tenant_id,
            event_id=event_id,
            position=position,
            status="WAITING",
            **data.model_dump()
        )

        self.db.add(waitlist_entry)

        # Mettre a jour compteur
        event.waitlist_count += 1

        self.db.commit()
        self.db.refresh(waitlist_entry)

        return WaitlistResponse.model_validate(waitlist_entry)

    def list_waitlist(self, event_id: UUID, ticket_type_id: Optional[UUID] = None) -> List[WaitlistResponse]:
        """Liste la liste d'attente."""
        entries = self._waitlist_repo.list_waiting(event_id, ticket_type_id)
        return [WaitlistResponse.model_validate(e) for e in entries]

    # =========================================================================
    # STATISTIQUES ET DASHBOARD
    # =========================================================================

    def get_event_stats(self, event_id: UUID) -> EventStats:
        """Calcule les statistiques d'un evenement."""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(event_id))

        registrations, total = self._registration_repo.list_by_event(event_id, limit=10000)

        stats = EventStats(
            event_id=event_id,
            total_registrations=event.registered_count,
            confirmed_registrations=event.confirmed_count,
            pending_registrations=sum(1 for r in registrations if r.status == RegistrationStatus.PENDING),
            waitlisted=event.waitlist_count,
            checked_in=event.checkin_count,
            no_shows=sum(1 for r in registrations if r.status == RegistrationStatus.NO_SHOW),
            cancelled=event.cancelled_count,
            total_revenue=event.total_revenue,
            total_refunds=event.total_refunds,
            net_revenue=event.total_revenue - event.total_refunds,
        )

        # Capacite
        if event.max_attendees:
            stats.capacity_utilization = event.confirmed_count / event.max_attendees * 100

        # Taux check-in
        if event.confirmed_count > 0:
            stats.check_in_rate = event.checkin_count / event.confirmed_count * 100
            stats.cancellation_rate = event.cancelled_count / event.registered_count * 100 if event.registered_count > 0 else 0

        # Prix moyen
        if event.registered_count > 0:
            stats.average_ticket_price = event.total_revenue / event.registered_count

        # Par type de billet
        for reg in registrations:
            if reg.ticket_type_id:
                key = str(reg.ticket_type_id)
                stats.tickets_by_type[key] = stats.tickets_by_type.get(key, 0) + 1

        # Par jour
        for reg in registrations:
            day = reg.created_at.strftime("%Y-%m-%d")
            stats.registrations_by_day[day] = stats.registrations_by_day.get(day, 0) + 1

        # Par source
        for reg in registrations:
            source = reg.source or "DIRECT"
            stats.registrations_by_source[source] = stats.registrations_by_source.get(source, 0) + 1

        return stats

    def get_event_dashboard(self, event_id: UUID) -> EventDashboard:
        """Recupere le dashboard complet d'un evenement."""
        event_response = self.get_event(event_id)
        if not event_response:
            raise EventNotFoundException(str(event_id))

        stats = self.get_event_stats(event_id)
        checkin_stats = self.get_checkin_stats(event_id)
        evaluation_stats = self.get_evaluation_stats(event_id)

        recent_registrations, _ = self.list_registrations(event_id, limit=10)
        sessions = self.list_sessions(event_id)
        sponsors = self.list_sponsors(event_id)

        # Top sessions (par nombre d'inscrits)
        top_sessions = sorted(sessions, key=lambda s: s.registered_count, reverse=True)[:5]

        return EventDashboard(
            event=event_response,
            stats=stats,
            check_in_stats=checkin_stats,
            evaluation_stats=evaluation_stats,
            recent_registrations=recent_registrations,
            top_sessions=top_sessions,
            sponsors=sponsors
        )

    def get_global_stats(self) -> GlobalEventStats:
        """Recupere les statistiques globales des evenements."""
        today = date.today()

        # Recuperer tous les evenements
        events, total = self._event_repo.list_events(limit=10000)

        stats = GlobalEventStats(
            total_events=total,
            upcoming_events=sum(1 for e in events if e.start_date > today),
            ongoing_events=sum(1 for e in events if e.start_date <= today <= e.end_date),
            completed_events=sum(1 for e in events if e.status == EventStatus.COMPLETED),
            total_registrations=sum(e.registered_count for e in events),
            total_revenue=sum(e.total_revenue for e in events)
        )

        # Par type
        for event in events:
            type_key = event.event_type.value if event.event_type else "OTHER"
            stats.events_by_type[type_key] = stats.events_by_type.get(type_key, 0) + 1

        # Par statut
        for event in events:
            status_key = event.status.value if event.status else "UNKNOWN"
            stats.events_by_status[status_key] = stats.events_by_status.get(status_key, 0) + 1

        # Par mois
        for event in events:
            month_key = event.start_date.strftime("%Y-%m")
            stats.events_by_month[month_key] = stats.events_by_month.get(month_key, 0) + 1
            stats.revenue_by_month[month_key] = stats.revenue_by_month.get(month_key, Decimal("0.00")) + event.total_revenue

        return stats

    # =========================================================================
    # METHODES PRIVEES
    # =========================================================================

    def _generate_slug(self, title: str) -> str:
        """Genere un slug unique."""
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        slug = f"{slug}-{secrets.token_hex(3)}"
        return slug

    def _apply_discount(
        self,
        event_id: UUID,
        code: str,
        ticket_type_id: UUID,
        ticket_price: Decimal
    ) -> DiscountCodeResult:
        """Applique un code promo (methode interne)."""
        discount = self._discount_repo.find_by_code(event_id, code)
        if not discount:
            return DiscountCodeResult(valid=False, message="Code invalide")

        if not discount.is_active:
            return DiscountCodeResult(valid=False, message="Code inactif")

        now = datetime.utcnow()
        if discount.valid_from and discount.valid_from > now:
            return DiscountCodeResult(valid=False, message="Code pas encore valide")

        if discount.valid_until and discount.valid_until < now:
            return DiscountCodeResult(valid=False, message="Code expire")

        if discount.max_uses and discount.uses_count >= discount.max_uses:
            return DiscountCodeResult(valid=False, message="Code epuise")

        # Verifier applicable au type de billet
        if discount.applicable_ticket_types and str(ticket_type_id) not in [str(t) for t in discount.applicable_ticket_types]:
            return DiscountCodeResult(valid=False, message="Code non applicable a ce billet")

        # Calculer reduction
        if discount.discount_type == "PERCENTAGE":
            amount = ticket_price * discount.discount_value / 100
        elif discount.discount_type == "FIXED":
            amount = min(discount.discount_value, ticket_price)
        elif discount.discount_type == "FREE":
            amount = ticket_price
        else:
            amount = Decimal("0.00")

        # Appliquer max
        if discount.max_discount_amount:
            amount = min(amount, discount.max_discount_amount)

        # Incrementer utilisation
        discount.uses_count += 1
        self.db.commit()

        return DiscountCodeResult(
            valid=True,
            discount_amount=amount,
            code_id=discount.id
        )

    def _add_to_waitlist(self, event_id: UUID, data: RegistrationCreate) -> RegistrationResponse:
        """Ajoute a la liste d'attente et retourne une inscription en attente."""
        waitlist_entry = WaitlistEntry(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            ticket_type_id=data.ticket_type_id,
            contact_id=data.contact_id
        )
        waitlist_response = self.add_to_waitlist(event_id, waitlist_entry)

        # Creer une inscription en statut WAITLISTED
        reg_number = self._registration_repo.generate_registration_number(event_id)
        qr_code = self._registration_repo.generate_qr_code(reg_number)

        registration = EventRegistration(
            tenant_id=self.tenant_id,
            event_id=event_id,
            ticket_type_id=data.ticket_type_id,
            registration_number=reg_number,
            qr_code=qr_code,
            status=RegistrationStatus.WAITLISTED,
            payment_status=PaymentStatus.PENDING,
            created_by=self.user_id,
            **data.model_dump(exclude={'ticket_type_id'})
        )

        self.db.add(registration)
        self.db.commit()
        self.db.refresh(registration)

        return RegistrationResponse.model_validate(registration)

    def _promote_from_waitlist(self, event_id: UUID, ticket_type_id: Optional[UUID] = None) -> None:
        """Promeut une personne de la liste d'attente."""
        waiting = self._waitlist_repo.list_waiting(event_id, ticket_type_id)

        if not waiting:
            return

        first = waiting[0]
        first.status = "NOTIFIED"
        first.notified_at = datetime.utcnow()
        first.notification_expires_at = datetime.utcnow() + timedelta(hours=24)

        self.db.commit()

        # TODO: Envoyer notification

    def _mark_no_shows(self, event_id: UUID) -> None:
        """Marque les non-presences."""
        not_checked_in = self._registration_repo.list_not_checked_in(event_id)

        for registration in not_checked_in:
            registration.status = RegistrationStatus.NO_SHOW

        self.db.commit()

        # Mettre a jour compteurs
        self._event_repo.update_counters(event_id)


# ============================================================================
# FACTORY
# ============================================================================

def get_events_service(db: Session, tenant_id: str, user_id: Optional[UUID] = None) -> EventsService:
    """Factory pour creer le service Events."""
    return EventsService(db, tenant_id, user_id)


__all__ = ['EventsService', 'get_events_service']
