"""
Service Events / Événements - GAP-066

Gestion des événements:
- Création et planification
- Inscriptions et billetterie
- Sessions et agenda
- Intervenants et sponsors
- Check-in et présences
- Communication participants
- Badges et certificats
- Analytics événementiels
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class EventType(str, Enum):
    """Type d'événement."""
    CONFERENCE = "conference"
    SEMINAR = "seminar"
    WORKSHOP = "workshop"
    WEBINAR = "webinar"
    MEETUP = "meetup"
    TRADESHOW = "tradeshow"
    TRAINING = "training"
    NETWORKING = "networking"
    PARTY = "party"
    OTHER = "other"


class EventStatus(str, Enum):
    """Statut d'un événement."""
    DRAFT = "draft"
    PUBLISHED = "published"
    REGISTRATION_OPEN = "registration_open"
    REGISTRATION_CLOSED = "registration_closed"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"


class EventFormat(str, Enum):
    """Format de l'événement."""
    IN_PERSON = "in_person"
    VIRTUAL = "virtual"
    HYBRID = "hybrid"


class TicketType(str, Enum):
    """Type de billet."""
    FREE = "free"
    PAID = "paid"
    DONATION = "donation"
    INVITATION = "invitation"


class RegistrationStatus(str, Enum):
    """Statut d'inscription."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    WAITLISTED = "waitlisted"
    CHECKED_IN = "checked_in"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class SessionType(str, Enum):
    """Type de session."""
    KEYNOTE = "keynote"
    PRESENTATION = "presentation"
    PANEL = "panel"
    WORKSHOP = "workshop"
    BREAK = "break"
    NETWORKING = "networking"
    REGISTRATION = "registration"


class SpeakerRole(str, Enum):
    """Rôle d'un intervenant."""
    SPEAKER = "speaker"
    MODERATOR = "moderator"
    PANELIST = "panelist"
    HOST = "host"
    TRAINER = "trainer"


class SponsorLevel(str, Enum):
    """Niveau de sponsor."""
    PLATINUM = "platinum"
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    PARTNER = "partner"
    MEDIA = "media"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Venue:
    """Lieu de l'événement."""
    id: str
    name: str
    address: str
    city: str
    country: str
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity: int = 0
    rooms: List[str] = field(default_factory=list)
    amenities: List[str] = field(default_factory=list)
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class TicketCategory:
    """Catégorie de billet."""
    id: str
    event_id: str
    name: str
    description: Optional[str] = None
    ticket_type: TicketType = TicketType.PAID
    price: Decimal = Decimal("0")
    currency: str = "EUR"
    quantity_available: int = 0
    quantity_sold: int = 0
    max_per_order: int = 10
    sales_start: Optional[datetime] = None
    sales_end: Optional[datetime] = None
    is_visible: bool = True
    requires_approval: bool = False
    includes_sessions: List[str] = field(default_factory=list)
    perks: List[str] = field(default_factory=list)


@dataclass
class Event:
    """Un événement."""
    id: str
    tenant_id: str
    title: str
    slug: str
    description: str
    event_type: EventType
    format: EventFormat = EventFormat.IN_PERSON
    status: EventStatus = EventStatus.DRAFT
    start_datetime: datetime = field(default_factory=datetime.now)
    end_datetime: Optional[datetime] = None
    timezone: str = "Europe/Paris"
    venue: Optional[Venue] = None
    virtual_platform: Optional[str] = None
    virtual_link: Optional[str] = None
    registration_open: bool = False
    registration_deadline: Optional[datetime] = None
    max_attendees: Optional[int] = None
    waitlist_enabled: bool = True
    ticket_categories: List[TicketCategory] = field(default_factory=list)
    cover_image_url: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    contact_email: Optional[str] = None
    organizer_name: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    registration_count: int = 0
    checkin_count: int = 0
    revenue_total: Decimal = Decimal("0")
    is_public: bool = True
    require_approval: bool = False
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None


@dataclass
class Speaker:
    """Un intervenant."""
    id: str
    tenant_id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    website_url: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    is_active: bool = True
    total_sessions: int = 0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class EventSession:
    """Une session d'événement."""
    id: str
    event_id: str
    title: str
    description: Optional[str] = None
    session_type: SessionType = SessionType.PRESENTATION
    start_datetime: datetime = field(default_factory=datetime.now)
    end_datetime: Optional[datetime] = None
    duration_minutes: int = 60
    room: Optional[str] = None
    track: Optional[str] = None
    capacity: Optional[int] = None
    speakers: List[Dict[str, Any]] = field(default_factory=list)
    is_bookable: bool = False
    registered_count: int = 0
    attendee_count: int = 0
    materials_url: Optional[str] = None
    recording_url: Optional[str] = None
    live_stream_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    order: int = 0


@dataclass
class Registration:
    """Une inscription."""
    id: str
    event_id: str
    tenant_id: str
    ticket_category_id: str
    attendee_id: Optional[str] = None
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    status: RegistrationStatus = RegistrationStatus.PENDING
    registration_number: str = ""
    qr_code: Optional[str] = None
    ticket_price: Decimal = Decimal("0")
    discount_code: Optional[str] = None
    discount_amount: Decimal = Decimal("0")
    amount_paid: Decimal = Decimal("0")
    payment_status: str = "pending"
    payment_reference: Optional[str] = None
    sessions_registered: List[str] = field(default_factory=list)
    custom_answers: Dict[str, Any] = field(default_factory=dict)
    dietary_requirements: Optional[str] = None
    special_needs: Optional[str] = None
    checked_in_at: Optional[datetime] = None
    checked_in_by: Optional[str] = None
    badge_printed: bool = False
    certificate_issued: bool = False
    notes: Optional[str] = None
    registered_at: datetime = field(default_factory=datetime.now)
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None


@dataclass
class Sponsor:
    """Un sponsor."""
    id: str
    event_id: str
    tenant_id: str
    name: str
    level: SponsorLevel
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    description: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    booth_location: Optional[str] = None
    amount_pledged: Decimal = Decimal("0")
    amount_paid: Decimal = Decimal("0")
    currency: str = "EUR"
    benefits: List[str] = field(default_factory=list)
    order: int = 0
    is_visible: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CheckIn:
    """Enregistrement de check-in."""
    id: str
    registration_id: str
    event_id: str
    session_id: Optional[str] = None
    checked_in_at: datetime = field(default_factory=datetime.now)
    checked_in_by: Optional[str] = None
    method: str = "qr_code"  # qr_code, manual, badge
    location: Optional[str] = None


@dataclass
class DiscountCode:
    """Code de réduction."""
    id: str
    event_id: str
    code: str
    description: Optional[str] = None
    discount_type: str = "percentage"  # percentage, fixed
    discount_value: Decimal = Decimal("0")
    max_uses: Optional[int] = None
    uses_count: int = 0
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    applicable_tickets: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class EventStats:
    """Statistiques d'un événement."""
    event_id: str
    total_registrations: int = 0
    confirmed_registrations: int = 0
    checked_in: int = 0
    no_shows: int = 0
    cancelled: int = 0
    waitlisted: int = 0
    total_revenue: Decimal = Decimal("0")
    tickets_by_category: Dict[str, int] = field(default_factory=dict)
    registrations_by_day: Dict[str, int] = field(default_factory=dict)
    checkins_by_hour: Dict[str, int] = field(default_factory=dict)
    sessions_attendance: Dict[str, int] = field(default_factory=dict)


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class EventService:
    """Service de gestion des événements."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

        # Stockage en mémoire (simulation)
        self._events: Dict[str, Event] = {}
        self._speakers: Dict[str, Speaker] = {}
        self._sessions: Dict[str, EventSession] = {}
        self._registrations: Dict[str, Registration] = {}
        self._sponsors: Dict[str, Sponsor] = {}
        self._checkins: Dict[str, CheckIn] = {}
        self._discount_codes: Dict[str, DiscountCode] = {}

        self._registration_counter = 0

    # -------------------------------------------------------------------------
    # Événements
    # -------------------------------------------------------------------------

    def create_event(
        self,
        title: str,
        description: str,
        event_type: EventType,
        start_datetime: datetime,
        **kwargs
    ) -> Event:
        """Crée un événement."""
        event_id = str(uuid4())
        slug = self._generate_slug(title)

        event = Event(
            id=event_id,
            tenant_id=self.tenant_id,
            title=title,
            slug=slug,
            description=description,
            event_type=event_type,
            start_datetime=start_datetime,
            **kwargs
        )

        self._events[event_id] = event
        return event

    def get_event(self, event_id: str) -> Optional[Event]:
        """Récupère un événement."""
        event = self._events.get(event_id)
        if event and event.tenant_id == self.tenant_id:
            return event
        return None

    def update_event(self, event_id: str, **updates) -> Optional[Event]:
        """Met à jour un événement."""
        event = self.get_event(event_id)
        if not event:
            return None

        for key, value in updates.items():
            if hasattr(event, key):
                setattr(event, key, value)

        event.updated_at = datetime.now()
        return event

    def publish_event(self, event_id: str) -> Optional[Event]:
        """Publie un événement."""
        event = self.get_event(event_id)
        if not event:
            return None

        event.status = EventStatus.PUBLISHED
        event.published_at = datetime.now()
        event.updated_at = datetime.now()
        return event

    def open_registration(self, event_id: str) -> Optional[Event]:
        """Ouvre les inscriptions."""
        event = self.get_event(event_id)
        if not event:
            return None

        event.registration_open = True
        event.status = EventStatus.REGISTRATION_OPEN
        event.updated_at = datetime.now()
        return event

    def close_registration(self, event_id: str) -> Optional[Event]:
        """Ferme les inscriptions."""
        event = self.get_event(event_id)
        if not event:
            return None

        event.registration_open = False
        event.status = EventStatus.REGISTRATION_CLOSED
        event.updated_at = datetime.now()
        return event

    def list_events(
        self,
        *,
        status: Optional[EventStatus] = None,
        event_type: Optional[EventType] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Event], int]:
        """Liste les événements."""
        results = []

        for event in self._events.values():
            if event.tenant_id != self.tenant_id:
                continue
            if status and event.status != status:
                continue
            if event_type and event.event_type != event_type:
                continue
            if from_date and event.start_datetime < from_date:
                continue
            if to_date and event.start_datetime > to_date:
                continue
            results.append(event)

        results.sort(key=lambda x: x.start_datetime, reverse=True)

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size

        return results[start:end], total

    # -------------------------------------------------------------------------
    # Billets
    # -------------------------------------------------------------------------

    def add_ticket_category(
        self,
        event_id: str,
        name: str,
        ticket_type: TicketType = TicketType.PAID,
        price: Decimal = Decimal("0"),
        quantity_available: int = 100,
        **kwargs
    ) -> Optional[TicketCategory]:
        """Ajoute une catégorie de billet."""
        event = self.get_event(event_id)
        if not event:
            return None

        category_id = str(uuid4())

        category = TicketCategory(
            id=category_id,
            event_id=event_id,
            name=name,
            ticket_type=ticket_type,
            price=price,
            quantity_available=quantity_available,
            **kwargs
        )

        event.ticket_categories.append(category)
        return category

    def get_ticket_category(self, event_id: str, category_id: str) -> Optional[TicketCategory]:
        """Récupère une catégorie de billet."""
        event = self.get_event(event_id)
        if not event:
            return None

        for cat in event.ticket_categories:
            if cat.id == category_id:
                return cat
        return None

    def get_available_tickets(self, event_id: str) -> List[TicketCategory]:
        """Liste les billets disponibles."""
        event = self.get_event(event_id)
        if not event:
            return []

        now = datetime.now()
        available = []

        for cat in event.ticket_categories:
            if not cat.is_visible:
                continue
            if cat.sales_start and cat.sales_start > now:
                continue
            if cat.sales_end and cat.sales_end < now:
                continue
            if cat.quantity_sold >= cat.quantity_available:
                continue
            available.append(cat)

        return available

    # -------------------------------------------------------------------------
    # Intervenants
    # -------------------------------------------------------------------------

    def create_speaker(
        self,
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        **kwargs
    ) -> Speaker:
        """Crée un intervenant."""
        speaker_id = str(uuid4())

        speaker = Speaker(
            id=speaker_id,
            tenant_id=self.tenant_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            **kwargs
        )

        self._speakers[speaker_id] = speaker
        return speaker

    def get_speaker(self, speaker_id: str) -> Optional[Speaker]:
        """Récupère un intervenant."""
        speaker = self._speakers.get(speaker_id)
        if speaker and speaker.tenant_id == self.tenant_id:
            return speaker
        return None

    def list_speakers(
        self,
        is_active: bool = True
    ) -> List[Speaker]:
        """Liste les intervenants."""
        return [
            s for s in self._speakers.values()
            if s.tenant_id == self.tenant_id and s.is_active == is_active
        ]

    # -------------------------------------------------------------------------
    # Sessions
    # -------------------------------------------------------------------------

    def create_session(
        self,
        event_id: str,
        title: str,
        session_type: SessionType,
        start_datetime: datetime,
        duration_minutes: int = 60,
        **kwargs
    ) -> Optional[EventSession]:
        """Crée une session."""
        event = self.get_event(event_id)
        if not event:
            return None

        session_id = str(uuid4())

        session = EventSession(
            id=session_id,
            event_id=event_id,
            title=title,
            session_type=session_type,
            start_datetime=start_datetime,
            duration_minutes=duration_minutes,
            end_datetime=start_datetime + timedelta(minutes=duration_minutes),
            **kwargs
        )

        self._sessions[session_id] = session
        return session

    def add_speaker_to_session(
        self,
        session_id: str,
        speaker_id: str,
        role: SpeakerRole = SpeakerRole.SPEAKER
    ) -> Optional[EventSession]:
        """Ajoute un intervenant à une session."""
        session = self._sessions.get(session_id)
        speaker = self.get_speaker(speaker_id)

        if not session or not speaker:
            return None

        session.speakers.append({
            "speaker_id": speaker_id,
            "name": f"{speaker.first_name} {speaker.last_name}",
            "role": role.value
        })

        speaker.total_sessions += 1

        return session

    def list_sessions(
        self,
        event_id: str,
        track: Optional[str] = None
    ) -> List[EventSession]:
        """Liste les sessions d'un événement."""
        results = [
            s for s in self._sessions.values()
            if s.event_id == event_id
        ]

        if track:
            results = [s for s in results if s.track == track]

        results.sort(key=lambda x: (x.start_datetime, x.order))
        return results

    def get_agenda(self, event_id: str) -> Dict[str, List[EventSession]]:
        """Récupère l'agenda groupé par jour."""
        sessions = self.list_sessions(event_id)
        agenda = {}

        for session in sessions:
            day = session.start_datetime.strftime("%Y-%m-%d")
            if day not in agenda:
                agenda[day] = []
            agenda[day].append(session)

        return agenda

    # -------------------------------------------------------------------------
    # Inscriptions
    # -------------------------------------------------------------------------

    def register(
        self,
        event_id: str,
        ticket_category_id: str,
        first_name: str,
        last_name: str,
        email: str,
        **kwargs
    ) -> Optional[Registration]:
        """Inscrit un participant."""
        event = self.get_event(event_id)
        if not event:
            return None

        if not event.registration_open:
            return None

        # Vérifier disponibilité
        category = self.get_ticket_category(event_id, ticket_category_id)
        if not category:
            return None

        if category.quantity_sold >= category.quantity_available:
            if event.waitlist_enabled:
                status = RegistrationStatus.WAITLISTED
            else:
                return None
        else:
            status = RegistrationStatus.PENDING
            category.quantity_sold += 1

        self._registration_counter += 1
        reg_number = f"REG-{event_id[:8].upper()}-{self._registration_counter:06d}"

        registration_id = str(uuid4())

        registration = Registration(
            id=registration_id,
            event_id=event_id,
            tenant_id=self.tenant_id,
            ticket_category_id=ticket_category_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            status=status,
            registration_number=reg_number,
            ticket_price=category.price,
            qr_code=self._generate_qr_code(reg_number),
            **kwargs
        )

        self._registrations[registration_id] = registration

        # Mettre à jour compteur
        event.registration_count += 1

        return registration

    def confirm_registration(
        self,
        registration_id: str,
        payment_reference: Optional[str] = None
    ) -> Optional[Registration]:
        """Confirme une inscription."""
        registration = self._registrations.get(registration_id)
        if not registration or registration.tenant_id != self.tenant_id:
            return None

        registration.status = RegistrationStatus.CONFIRMED
        registration.confirmed_at = datetime.now()
        registration.payment_status = "paid"
        registration.payment_reference = payment_reference
        registration.amount_paid = registration.ticket_price - registration.discount_amount

        # Mettre à jour revenu
        event = self.get_event(registration.event_id)
        if event:
            event.revenue_total += registration.amount_paid

        return registration

    def cancel_registration(
        self,
        registration_id: str,
        refund: bool = False
    ) -> Optional[Registration]:
        """Annule une inscription."""
        registration = self._registrations.get(registration_id)
        if not registration or registration.tenant_id != self.tenant_id:
            return None

        registration.status = RegistrationStatus.REFUNDED if refund else RegistrationStatus.CANCELLED
        registration.cancelled_at = datetime.now()

        # Libérer la place
        event = self.get_event(registration.event_id)
        if event:
            category = self.get_ticket_category(event.id, registration.ticket_category_id)
            if category:
                category.quantity_sold = max(0, category.quantity_sold - 1)

            # Promouvoir de la liste d'attente
            self._promote_from_waitlist(event.id, registration.ticket_category_id)

        return registration

    def _promote_from_waitlist(self, event_id: str, category_id: str):
        """Promeut de la liste d'attente."""
        waitlisted = [
            r for r in self._registrations.values()
            if r.event_id == event_id and
               r.ticket_category_id == category_id and
               r.status == RegistrationStatus.WAITLISTED
        ]

        if waitlisted:
            waitlisted.sort(key=lambda x: x.registered_at)
            first = waitlisted[0]
            first.status = RegistrationStatus.PENDING

    def list_registrations(
        self,
        event_id: str,
        *,
        status: Optional[RegistrationStatus] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Registration], int]:
        """Liste les inscriptions."""
        results = []

        for reg in self._registrations.values():
            if reg.event_id != event_id:
                continue
            if status and reg.status != status:
                continue
            if search:
                search_lower = search.lower()
                if (search_lower not in reg.first_name.lower() and
                    search_lower not in reg.last_name.lower() and
                    search_lower not in reg.email.lower()):
                    continue
            results.append(reg)

        results.sort(key=lambda x: x.registered_at, reverse=True)

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size

        return results[start:end], total

    def get_registration(self, registration_id: str) -> Optional[Registration]:
        """Récupère une inscription."""
        return self._registrations.get(registration_id)

    def get_registration_by_number(self, reg_number: str) -> Optional[Registration]:
        """Récupère par numéro d'inscription."""
        for reg in self._registrations.values():
            if reg.registration_number == reg_number:
                return reg
        return None

    # -------------------------------------------------------------------------
    # Check-in
    # -------------------------------------------------------------------------

    def check_in(
        self,
        registration_id: str,
        checked_in_by: Optional[str] = None,
        session_id: Optional[str] = None,
        method: str = "qr_code"
    ) -> Optional[CheckIn]:
        """Enregistre un check-in."""
        registration = self._registrations.get(registration_id)
        if not registration:
            return None

        if registration.status not in [RegistrationStatus.CONFIRMED, RegistrationStatus.PENDING]:
            return None

        checkin_id = str(uuid4())

        checkin = CheckIn(
            id=checkin_id,
            registration_id=registration_id,
            event_id=registration.event_id,
            session_id=session_id,
            checked_in_by=checked_in_by,
            method=method
        )

        self._checkins[checkin_id] = checkin

        # Mettre à jour registration
        registration.status = RegistrationStatus.CHECKED_IN
        registration.checked_in_at = datetime.now()
        registration.checked_in_by = checked_in_by

        # Mettre à jour compteurs
        event = self.get_event(registration.event_id)
        if event:
            event.checkin_count += 1

        if session_id:
            session = self._sessions.get(session_id)
            if session:
                session.attendee_count += 1

        return checkin

    def check_in_by_qr(
        self,
        qr_code: str,
        checked_in_by: Optional[str] = None
    ) -> Optional[CheckIn]:
        """Check-in par QR code."""
        for reg in self._registrations.values():
            if reg.qr_code == qr_code:
                return self.check_in(reg.id, checked_in_by, method="qr_code")
        return None

    def get_checkin_stats(self, event_id: str) -> Dict[str, Any]:
        """Statistiques de check-in."""
        registrations = [
            r for r in self._registrations.values()
            if r.event_id == event_id
        ]

        confirmed = [r for r in registrations if r.status in [
            RegistrationStatus.CONFIRMED,
            RegistrationStatus.CHECKED_IN
        ]]

        checked_in = [r for r in registrations if r.status == RegistrationStatus.CHECKED_IN]

        return {
            "total_expected": len(confirmed),
            "checked_in": len(checked_in),
            "remaining": len(confirmed) - len(checked_in),
            "check_in_rate": len(checked_in) / len(confirmed) * 100 if confirmed else 0
        }

    # -------------------------------------------------------------------------
    # Sponsors
    # -------------------------------------------------------------------------

    def add_sponsor(
        self,
        event_id: str,
        name: str,
        level: SponsorLevel,
        **kwargs
    ) -> Optional[Sponsor]:
        """Ajoute un sponsor."""
        event = self.get_event(event_id)
        if not event:
            return None

        sponsor_id = str(uuid4())

        # Déterminer ordre selon niveau
        order_map = {
            SponsorLevel.PLATINUM: 1,
            SponsorLevel.GOLD: 2,
            SponsorLevel.SILVER: 3,
            SponsorLevel.BRONZE: 4,
            SponsorLevel.PARTNER: 5,
            SponsorLevel.MEDIA: 6
        }

        sponsor = Sponsor(
            id=sponsor_id,
            event_id=event_id,
            tenant_id=self.tenant_id,
            name=name,
            level=level,
            order=order_map.get(level, 99),
            **kwargs
        )

        self._sponsors[sponsor_id] = sponsor
        return sponsor

    def list_sponsors(
        self,
        event_id: str,
        level: Optional[SponsorLevel] = None
    ) -> List[Sponsor]:
        """Liste les sponsors."""
        results = [
            s for s in self._sponsors.values()
            if s.event_id == event_id and s.is_visible
        ]

        if level:
            results = [s for s in results if s.level == level]

        results.sort(key=lambda x: (x.order, x.name))
        return results

    # -------------------------------------------------------------------------
    # Codes promo
    # -------------------------------------------------------------------------

    def create_discount_code(
        self,
        event_id: str,
        code: str,
        discount_type: str,
        discount_value: Decimal,
        **kwargs
    ) -> Optional[DiscountCode]:
        """Crée un code de réduction."""
        event = self.get_event(event_id)
        if not event:
            return None

        discount_id = str(uuid4())

        discount = DiscountCode(
            id=discount_id,
            event_id=event_id,
            code=code.upper(),
            discount_type=discount_type,
            discount_value=discount_value,
            **kwargs
        )

        self._discount_codes[discount_id] = discount
        return discount

    def apply_discount_code(
        self,
        event_id: str,
        code: str,
        ticket_price: Decimal
    ) -> Tuple[bool, Decimal, Optional[str]]:
        """Applique un code de réduction."""
        code_upper = code.upper()

        for discount in self._discount_codes.values():
            if discount.event_id != event_id:
                continue
            if discount.code != code_upper:
                continue
            if not discount.is_active:
                return False, Decimal("0"), "Code inactif"

            now = datetime.now()
            if discount.valid_from and discount.valid_from > now:
                return False, Decimal("0"), "Code pas encore valide"
            if discount.valid_until and discount.valid_until < now:
                return False, Decimal("0"), "Code expiré"
            if discount.max_uses and discount.uses_count >= discount.max_uses:
                return False, Decimal("0"), "Code épuisé"

            # Calculer réduction
            if discount.discount_type == "percentage":
                amount = ticket_price * discount.discount_value / 100
            else:
                amount = min(discount.discount_value, ticket_price)

            discount.uses_count += 1
            return True, amount, None

        return False, Decimal("0"), "Code invalide"

    # -------------------------------------------------------------------------
    # Statistiques
    # -------------------------------------------------------------------------

    def get_event_stats(self, event_id: str) -> Optional[EventStats]:
        """Génère les statistiques d'un événement."""
        event = self.get_event(event_id)
        if not event:
            return None

        stats = EventStats(event_id=event_id)

        registrations = [
            r for r in self._registrations.values()
            if r.event_id == event_id
        ]

        stats.total_registrations = len(registrations)

        for reg in registrations:
            if reg.status == RegistrationStatus.CONFIRMED:
                stats.confirmed_registrations += 1
            elif reg.status == RegistrationStatus.CHECKED_IN:
                stats.confirmed_registrations += 1
                stats.checked_in += 1
            elif reg.status == RegistrationStatus.NO_SHOW:
                stats.no_shows += 1
            elif reg.status == RegistrationStatus.CANCELLED:
                stats.cancelled += 1
            elif reg.status == RegistrationStatus.WAITLISTED:
                stats.waitlisted += 1

            stats.total_revenue += reg.amount_paid

            # Par catégorie
            cat_name = reg.ticket_category_id
            stats.tickets_by_category[cat_name] = stats.tickets_by_category.get(cat_name, 0) + 1

            # Par jour
            day = reg.registered_at.strftime("%Y-%m-%d")
            stats.registrations_by_day[day] = stats.registrations_by_day.get(day, 0) + 1

        # Check-ins par heure
        for checkin in self._checkins.values():
            if checkin.event_id != event_id:
                continue
            hour = checkin.checked_in_at.strftime("%H:00")
            stats.checkins_by_hour[hour] = stats.checkins_by_hour.get(hour, 0) + 1

        # Présence par session
        for session in self._sessions.values():
            if session.event_id == event_id:
                stats.sessions_attendance[session.id] = session.attendee_count

        return stats

    # -------------------------------------------------------------------------
    # Utilitaires
    # -------------------------------------------------------------------------

    def _generate_slug(self, title: str) -> str:
        """Génère un slug depuis le titre."""
        import re
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return f"{slug}-{uuid4().hex[:6]}"

    def _generate_qr_code(self, registration_number: str) -> str:
        """Génère un QR code (simulation)."""
        import hashlib
        return hashlib.sha256(registration_number.encode()).hexdigest()[:32]


# ============================================================================
# FACTORY
# ============================================================================

def create_event_service(tenant_id: str) -> EventService:
    """Factory pour créer un service d'événements."""
    return EventService(tenant_id)
