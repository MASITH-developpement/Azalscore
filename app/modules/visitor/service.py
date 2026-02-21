"""
Module Visitor Management - GAP-079

Gestion des visiteurs:
- Pré-enregistrement
- Check-in / Check-out
- Badges visiteurs
- Hôtes et notifications
- Accords de confidentialité
- Rapports de visite
- Intégration contrôle d'accès
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
import secrets


# ============== Énumérations ==============

class VisitorType(str, Enum):
    """Type de visiteur."""
    GUEST = "guest"
    CONTRACTOR = "contractor"
    DELIVERY = "delivery"
    INTERVIEW = "interview"
    CLIENT = "client"
    VENDOR = "vendor"
    GOVERNMENT = "government"
    VIP = "vip"


class VisitStatus(str, Enum):
    """Statut de la visite."""
    SCHEDULED = "scheduled"
    PRE_REGISTERED = "pre_registered"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    DENIED = "denied"


class BadgeType(str, Enum):
    """Type de badge."""
    VISITOR = "visitor"
    CONTRACTOR = "contractor"
    TEMPORARY = "temporary"
    ESCORT_REQUIRED = "escort_required"
    VIP = "vip"


class DocumentType(str, Enum):
    """Type de document requis."""
    ID_CARD = "id_card"
    PASSPORT = "passport"
    DRIVER_LICENSE = "driver_license"
    NDA = "nda"
    SAFETY_BRIEFING = "safety_briefing"
    HEALTH_DECLARATION = "health_declaration"


class AccessLevel(str, Enum):
    """Niveau d'accès."""
    LOBBY = "lobby"
    RESTRICTED = "restricted"
    GENERAL = "general"
    FULL = "full"


# ============== Data Classes ==============

@dataclass
class Location:
    """Lieu/Site."""
    id: str
    tenant_id: str
    name: str
    code: str
    address: str

    # Configuration
    timezone: str = "Europe/Paris"
    reception_email: str = ""
    reception_phone: str = ""

    # Heures d'ouverture
    opening_time: time = field(default_factory=lambda: time(8, 0))
    closing_time: time = field(default_factory=lambda: time(18, 0))
    working_days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])

    # Configuration visiteurs
    require_pre_registration: bool = False
    require_id_check: bool = True
    require_nda: bool = False
    require_host_approval: bool = True
    auto_checkout_hours: int = 12

    # Badge
    badge_printer_id: str = ""
    badge_template: str = ""

    # Capacité
    max_visitors: Optional[int] = None
    current_visitors: int = 0

    is_active: bool = True

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Host:
    """Hôte (employé qui reçoit des visiteurs)."""
    id: str
    tenant_id: str
    user_id: str
    name: str
    email: str
    phone: str = ""

    department: str = ""
    location_id: str = ""

    # Notifications
    notify_on_arrival: bool = True
    notify_on_pre_register: bool = True
    notify_method: str = "email"  # email, sms, push, all

    # Délégation
    delegate_ids: List[str] = field(default_factory=list)

    is_active: bool = True

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VisitorProfile:
    """Profil visiteur (données récurrentes)."""
    id: str
    tenant_id: str
    email: str

    first_name: str = ""
    last_name: str = ""
    company: str = ""
    phone: str = ""

    # Documents
    id_type: str = ""
    id_number: str = ""
    id_expiry: Optional[date] = None
    photo_url: str = ""

    # Préférences
    preferred_language: str = "fr"
    accessibility_needs: str = ""

    # Historique
    total_visits: int = 0
    last_visit: Optional[datetime] = None

    # Listes
    is_blacklisted: bool = False
    blacklist_reason: str = ""
    is_vip: bool = False

    # Accords signés
    nda_signed: bool = False
    nda_signed_at: Optional[datetime] = None
    nda_version: str = ""

    # RGPD
    data_consent: bool = False
    data_consent_at: Optional[datetime] = None
    data_retention_until: Optional[date] = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Visit:
    """Visite."""
    id: str
    tenant_id: str
    visit_number: str

    # Visiteur
    visitor_profile_id: Optional[str] = None
    visitor_first_name: str = ""
    visitor_last_name: str = ""
    visitor_email: str = ""
    visitor_phone: str = ""
    visitor_company: str = ""
    visitor_type: VisitorType = VisitorType.GUEST

    # Hôte
    host_id: str = ""
    host_name: str = ""

    # Lieu
    location_id: str = ""
    location_name: str = ""

    # Période
    scheduled_date: date = field(default_factory=date.today)
    scheduled_start: Optional[time] = None
    scheduled_end: Optional[time] = None

    status: VisitStatus = VisitStatus.SCHEDULED

    # Check-in/out
    checked_in_at: Optional[datetime] = None
    checked_out_at: Optional[datetime] = None
    checked_in_by: str = ""
    checked_out_by: str = ""

    # Badge
    badge_number: str = ""
    badge_type: BadgeType = BadgeType.VISITOR
    badge_printed: bool = False
    badge_returned: bool = False

    # Accès
    access_level: AccessLevel = AccessLevel.LOBBY
    access_areas: List[str] = field(default_factory=list)
    escort_required: bool = False
    escort_id: str = ""

    # Documents
    id_verified: bool = False
    id_type: str = ""
    id_number: str = ""
    documents_signed: List[str] = field(default_factory=list)

    # Équipement
    equipment_issued: List[str] = field(default_factory=list)
    equipment_returned: bool = True

    # Véhicule
    has_vehicle: bool = False
    vehicle_registration: str = ""
    parking_spot: str = ""

    # Objectif
    purpose: str = ""
    meeting_room: str = ""

    # Groupe
    group_id: Optional[str] = None
    is_group_leader: bool = False

    # Notifications
    pre_register_email_sent: bool = False
    arrival_notification_sent: bool = False
    checkout_reminder_sent: bool = False

    # QR Code pour check-in
    qr_code: str = ""
    qr_code_url: str = ""

    notes: str = ""
    internal_notes: str = ""

    # Feedback
    rating: Optional[int] = None
    feedback: str = ""

    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VisitorBadge:
    """Badge visiteur."""
    id: str
    tenant_id: str
    visit_id: str

    badge_number: str = ""
    badge_type: BadgeType = BadgeType.VISITOR

    # Visiteur
    visitor_name: str = ""
    visitor_company: str = ""
    photo_url: str = ""

    # Hôte
    host_name: str = ""

    # Validité
    valid_from: datetime = field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None

    # Accès
    access_level: AccessLevel = AccessLevel.LOBBY
    access_areas: List[str] = field(default_factory=list)

    # QR/Barcode
    qr_code: str = ""
    barcode: str = ""

    # Impression
    printed_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None

    is_active: bool = True


@dataclass
class VisitGroup:
    """Groupe de visiteurs."""
    id: str
    tenant_id: str
    name: str
    description: str

    # Période
    visit_date: date = field(default_factory=date.today)
    start_time: Optional[time] = None
    end_time: Optional[time] = None

    # Hôte
    host_id: str = ""
    host_name: str = ""

    # Lieu
    location_id: str = ""

    # Membres
    member_count: int = 0
    visit_ids: List[str] = field(default_factory=list)

    # Configuration
    require_individual_checkin: bool = True
    shared_purpose: str = ""

    status: VisitStatus = VisitStatus.SCHEDULED

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WatchlistEntry:
    """Entrée de liste de surveillance."""
    id: str
    tenant_id: str

    # Identifiants
    email: Optional[str] = None
    id_number: Optional[str] = None
    name: Optional[str] = None

    # Type
    list_type: str = "blacklist"  # blacklist, watchlist, vip

    # Raison
    reason: str = ""

    # Validité
    valid_from: date = field(default_factory=date.today)
    valid_until: Optional[date] = None

    # Actions
    action: str = "deny"  # deny, alert, escalate

    # Contact
    alert_contacts: List[str] = field(default_factory=list)

    added_by: str = ""

    is_active: bool = True

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VisitorStats:
    """Statistiques des visiteurs."""
    tenant_id: str
    location_id: Optional[str] = None
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)

    # Volume
    total_visits: int = 0
    unique_visitors: int = 0
    current_on_site: int = 0

    # Par statut
    completed_visits: int = 0
    cancelled_visits: int = 0
    no_shows: int = 0

    # Par type
    visits_by_type: Dict[str, int] = field(default_factory=dict)

    # Temps
    avg_visit_duration_minutes: int = 0
    avg_wait_time_minutes: int = 0

    # Performance
    pre_registration_rate: Decimal = Decimal("0")
    on_time_rate: Decimal = Decimal("0")

    # Par jour/heure
    visits_by_day: Dict[str, int] = field(default_factory=dict)
    peak_hours: List[int] = field(default_factory=list)

    # Top hosts
    top_hosts: List[Dict[str, Any]] = field(default_factory=list)

    # Satisfaction
    avg_rating: Decimal = Decimal("0")


# ============== Service Principal ==============

class VisitorService:
    """Service de gestion des visiteurs."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._locations: Dict[str, Location] = {}
        self._hosts: Dict[str, Host] = {}
        self._profiles: Dict[str, VisitorProfile] = {}
        self._visits: Dict[str, Visit] = {}
        self._badges: Dict[str, VisitorBadge] = {}
        self._groups: Dict[str, VisitGroup] = {}
        self._watchlist: Dict[str, WatchlistEntry] = {}
        self._visit_counter: int = 0

    # ===== Lieux =====

    def create_location(
        self,
        name: str,
        code: str,
        address: str,
        *,
        reception_email: str = "",
        reception_phone: str = "",
        require_pre_registration: bool = False,
        require_id_check: bool = True,
        require_nda: bool = False,
        max_visitors: Optional[int] = None
    ) -> Location:
        """Créer un lieu."""
        location_id = str(uuid.uuid4())

        location = Location(
            id=location_id,
            tenant_id=self.tenant_id,
            name=name,
            code=code,
            address=address,
            reception_email=reception_email,
            reception_phone=reception_phone,
            require_pre_registration=require_pre_registration,
            require_id_check=require_id_check,
            require_nda=require_nda,
            max_visitors=max_visitors
        )

        self._locations[location_id] = location
        return location

    def get_location(self, location_id: str) -> Optional[Location]:
        """Récupérer un lieu."""
        loc = self._locations.get(location_id)
        if loc and loc.tenant_id == self.tenant_id:
            return loc
        return None

    def list_locations(self) -> List[Location]:
        """Lister les lieux."""
        return [
            loc for loc in self._locations.values()
            if loc.tenant_id == self.tenant_id and loc.is_active
        ]

    # ===== Hôtes =====

    def register_host(
        self,
        user_id: str,
        name: str,
        email: str,
        *,
        phone: str = "",
        department: str = "",
        location_id: str = "",
        notify_on_arrival: bool = True
    ) -> Host:
        """Enregistrer un hôte."""
        host_id = str(uuid.uuid4())

        host = Host(
            id=host_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            name=name,
            email=email,
            phone=phone,
            department=department,
            location_id=location_id,
            notify_on_arrival=notify_on_arrival
        )

        self._hosts[host_id] = host
        return host

    def get_host(self, host_id: str) -> Optional[Host]:
        """Récupérer un hôte."""
        host = self._hosts.get(host_id)
        if host and host.tenant_id == self.tenant_id:
            return host
        return None

    def list_hosts(
        self,
        location_id: Optional[str] = None
    ) -> List[Host]:
        """Lister les hôtes."""
        hosts = [
            h for h in self._hosts.values()
            if h.tenant_id == self.tenant_id and h.is_active
        ]

        if location_id:
            hosts = [h for h in hosts if h.location_id == location_id]

        return sorted(hosts, key=lambda x: x.name)

    # ===== Profils visiteurs =====

    def create_or_update_profile(
        self,
        email: str,
        first_name: str,
        last_name: str,
        *,
        company: str = "",
        phone: str = "",
        id_type: str = "",
        id_number: str = ""
    ) -> VisitorProfile:
        """Créer ou mettre à jour un profil visiteur."""
        # Chercher profil existant
        existing = None
        for profile in self._profiles.values():
            if profile.email == email and profile.tenant_id == self.tenant_id:
                existing = profile
                break

        if existing:
            existing.first_name = first_name
            existing.last_name = last_name
            existing.company = company
            existing.phone = phone
            if id_type:
                existing.id_type = id_type
            if id_number:
                existing.id_number = id_number
            existing.updated_at = datetime.utcnow()
            return existing

        profile_id = str(uuid.uuid4())

        profile = VisitorProfile(
            id=profile_id,
            tenant_id=self.tenant_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            company=company,
            phone=phone,
            id_type=id_type,
            id_number=id_number
        )

        self._profiles[profile_id] = profile
        return profile

    def get_profile_by_email(self, email: str) -> Optional[VisitorProfile]:
        """Récupérer un profil par email."""
        for profile in self._profiles.values():
            if profile.email == email and profile.tenant_id == self.tenant_id:
                return profile
        return None

    # ===== Visites =====

    def schedule_visit(
        self,
        location_id: str,
        host_id: str,
        visitor_email: str,
        visitor_first_name: str,
        visitor_last_name: str,
        scheduled_date: date,
        *,
        scheduled_start: Optional[time] = None,
        scheduled_end: Optional[time] = None,
        visitor_company: str = "",
        visitor_phone: str = "",
        visitor_type: VisitorType = VisitorType.GUEST,
        purpose: str = "",
        meeting_room: str = "",
        escort_required: bool = False,
        access_level: AccessLevel = AccessLevel.LOBBY,
        notes: str = "",
        created_by: str = ""
    ) -> Optional[Visit]:
        """Planifier une visite."""
        location = self._locations.get(location_id)
        if not location or location.tenant_id != self.tenant_id:
            return None

        host = self._hosts.get(host_id)
        if not host or host.tenant_id != self.tenant_id:
            return None

        # Vérifier watchlist
        watchlist_check = self.check_watchlist(email=visitor_email)
        if watchlist_check["blocked"]:
            return None

        self._visit_counter += 1
        visit_id = str(uuid.uuid4())
        visit_number = f"VIS-{self._visit_counter:08d}"

        # Générer QR code
        qr_code = secrets.token_urlsafe(16)

        # Créer ou récupérer le profil
        profile = self.create_or_update_profile(
            visitor_email, visitor_first_name, visitor_last_name,
            company=visitor_company, phone=visitor_phone
        )

        visit = Visit(
            id=visit_id,
            tenant_id=self.tenant_id,
            visit_number=visit_number,
            visitor_profile_id=profile.id,
            visitor_first_name=visitor_first_name,
            visitor_last_name=visitor_last_name,
            visitor_email=visitor_email,
            visitor_phone=visitor_phone,
            visitor_company=visitor_company,
            visitor_type=visitor_type,
            host_id=host_id,
            host_name=host.name,
            location_id=location_id,
            location_name=location.name,
            scheduled_date=scheduled_date,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            status=VisitStatus.SCHEDULED,
            access_level=access_level,
            escort_required=escort_required,
            purpose=purpose,
            meeting_room=meeting_room,
            qr_code=qr_code,
            notes=notes,
            created_by=created_by
        )

        self._visits[visit_id] = visit

        # Envoyer notification à l'hôte
        if host.notify_on_pre_register:
            self._send_host_notification(visit, "scheduled")

        return visit

    def pre_register(
        self,
        visit_id: str
    ) -> Optional[Visit]:
        """Pré-enregistrer un visiteur (envoyer invitation)."""
        visit = self._visits.get(visit_id)
        if not visit or visit.tenant_id != self.tenant_id:
            return None

        if visit.status != VisitStatus.SCHEDULED:
            return None

        visit.status = VisitStatus.PRE_REGISTERED
        visit.pre_register_email_sent = True
        visit.updated_at = datetime.utcnow()

        # Envoyer email avec QR code au visiteur
        self._send_visitor_invitation(visit)

        return visit

    def check_in(
        self,
        visit_id: str,
        *,
        checked_in_by: str = "",
        id_verified: bool = False,
        id_type: str = "",
        id_number: str = "",
        photo_url: str = ""
    ) -> Optional[Visit]:
        """Check-in d'un visiteur."""
        visit = self._visits.get(visit_id)
        if not visit or visit.tenant_id != self.tenant_id:
            return None

        if visit.status not in [VisitStatus.SCHEDULED, VisitStatus.PRE_REGISTERED]:
            return None

        now = datetime.utcnow()

        # Vérifier watchlist
        watchlist_check = self.check_watchlist(email=visit.visitor_email)
        if watchlist_check["blocked"]:
            visit.status = VisitStatus.DENIED
            visit.internal_notes = f"Refusé: {watchlist_check['reason']}"
            visit.updated_at = now
            return visit

        # Vérifier capacité
        location = self._locations.get(visit.location_id)
        if location and location.max_visitors:
            if location.current_visitors >= location.max_visitors:
                return None

        visit.status = VisitStatus.CHECKED_IN
        visit.checked_in_at = now
        visit.checked_in_by = checked_in_by
        visit.id_verified = id_verified
        visit.id_type = id_type
        visit.id_number = id_number
        visit.updated_at = now

        # Mettre à jour la capacité
        if location:
            location.current_visitors += 1

        # Générer badge
        badge = self._generate_badge(visit)
        visit.badge_number = badge.badge_number

        # Mettre à jour le profil
        if visit.visitor_profile_id:
            profile = self._profiles.get(visit.visitor_profile_id)
            if profile:
                profile.total_visits += 1
                profile.last_visit = now
                if id_type:
                    profile.id_type = id_type
                if id_number:
                    profile.id_number = id_number

        # Notifier l'hôte
        host = self._hosts.get(visit.host_id)
        if host and host.notify_on_arrival:
            self._send_host_notification(visit, "arrived")
            visit.arrival_notification_sent = True

        return visit

    def check_in_by_qr(
        self,
        qr_code: str,
        checked_in_by: str = ""
    ) -> Optional[Visit]:
        """Check-in par QR code."""
        for visit in self._visits.values():
            if visit.qr_code == qr_code and visit.tenant_id == self.tenant_id:
                return self.check_in(visit.id, checked_in_by=checked_in_by)
        return None

    def check_out(
        self,
        visit_id: str,
        *,
        checked_out_by: str = "",
        rating: Optional[int] = None,
        feedback: str = ""
    ) -> Optional[Visit]:
        """Check-out d'un visiteur."""
        visit = self._visits.get(visit_id)
        if not visit or visit.tenant_id != self.tenant_id:
            return None

        if visit.status != VisitStatus.CHECKED_IN:
            return None

        now = datetime.utcnow()

        visit.status = VisitStatus.CHECKED_OUT
        visit.checked_out_at = now
        visit.checked_out_by = checked_out_by
        visit.badge_returned = True
        visit.rating = rating
        visit.feedback = feedback
        visit.updated_at = now

        # Mettre à jour la capacité
        location = self._locations.get(visit.location_id)
        if location and location.current_visitors > 0:
            location.current_visitors -= 1

        # Désactiver le badge
        for badge in self._badges.values():
            if badge.visit_id == visit_id:
                badge.is_active = False
                badge.returned_at = now

        return visit

    def cancel_visit(
        self,
        visit_id: str,
        reason: str = ""
    ) -> Optional[Visit]:
        """Annuler une visite."""
        visit = self._visits.get(visit_id)
        if not visit or visit.tenant_id != self.tenant_id:
            return None

        if visit.status in [VisitStatus.CHECKED_OUT, VisitStatus.CANCELLED]:
            return None

        visit.status = VisitStatus.CANCELLED
        visit.internal_notes = f"Annulé: {reason}"
        visit.updated_at = datetime.utcnow()

        return visit

    def get_visit(self, visit_id: str) -> Optional[Visit]:
        """Récupérer une visite."""
        visit = self._visits.get(visit_id)
        if visit and visit.tenant_id == self.tenant_id:
            return visit
        return None

    def list_visits(
        self,
        *,
        location_id: Optional[str] = None,
        host_id: Optional[str] = None,
        status: Optional[VisitStatus] = None,
        visit_date: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Visit]:
        """Lister les visites."""
        visits = [
            v for v in self._visits.values()
            if v.tenant_id == self.tenant_id
        ]

        if location_id:
            visits = [v for v in visits if v.location_id == location_id]

        if host_id:
            visits = [v for v in visits if v.host_id == host_id]

        if status:
            visits = [v for v in visits if v.status == status]

        if visit_date:
            visits = [v for v in visits if v.scheduled_date == visit_date]

        if start_date:
            visits = [v for v in visits if v.scheduled_date >= start_date]

        if end_date:
            visits = [v for v in visits if v.scheduled_date <= end_date]

        return sorted(visits, key=lambda x: (x.scheduled_date, x.scheduled_start or time(0, 0)))

    def get_current_visitors(
        self,
        location_id: Optional[str] = None
    ) -> List[Visit]:
        """Récupérer les visiteurs actuellement sur site."""
        visits = [
            v for v in self._visits.values()
            if v.tenant_id == self.tenant_id and v.status == VisitStatus.CHECKED_IN
        ]

        if location_id:
            visits = [v for v in visits if v.location_id == location_id]

        return sorted(visits, key=lambda x: x.checked_in_at or datetime.min)

    def get_expected_visitors(
        self,
        location_id: str,
        visit_date: Optional[date] = None
    ) -> List[Visit]:
        """Récupérer les visiteurs attendus."""
        target_date = visit_date or date.today()

        return [
            v for v in self._visits.values()
            if v.tenant_id == self.tenant_id and
               v.location_id == location_id and
               v.scheduled_date == target_date and
               v.status in [VisitStatus.SCHEDULED, VisitStatus.PRE_REGISTERED]
        ]

    # ===== Badges =====

    def _generate_badge(self, visit: Visit) -> VisitorBadge:
        """Générer un badge pour une visite."""
        badge_id = str(uuid.uuid4())
        badge_number = f"B{secrets.token_hex(4).upper()}"

        badge = VisitorBadge(
            id=badge_id,
            tenant_id=self.tenant_id,
            visit_id=visit.id,
            badge_number=badge_number,
            badge_type=visit.badge_type,
            visitor_name=f"{visit.visitor_first_name} {visit.visitor_last_name}",
            visitor_company=visit.visitor_company,
            host_name=visit.host_name,
            access_level=visit.access_level,
            access_areas=visit.access_areas,
            qr_code=visit.qr_code
        )

        self._badges[badge_id] = badge
        return badge

    def print_badge(
        self,
        visit_id: str
    ) -> Optional[Dict[str, Any]]:
        """Imprimer le badge."""
        visit = self._visits.get(visit_id)
        if not visit or visit.tenant_id != self.tenant_id:
            return None

        for badge in self._badges.values():
            if badge.visit_id == visit_id:
                badge.printed_at = datetime.utcnow()
                visit.badge_printed = True

                return {
                    "badge_id": badge.id,
                    "badge_number": badge.badge_number,
                    "visitor_name": badge.visitor_name,
                    "visitor_company": badge.visitor_company,
                    "host_name": badge.host_name,
                    "valid_until": badge.valid_until.isoformat() if badge.valid_until else None,
                    "qr_code": badge.qr_code
                }

        return None

    # ===== Groupes =====

    def create_group(
        self,
        name: str,
        description: str,
        host_id: str,
        location_id: str,
        visit_date: date,
        *,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        shared_purpose: str = ""
    ) -> Optional[VisitGroup]:
        """Créer un groupe de visiteurs."""
        host = self._hosts.get(host_id)
        if not host or host.tenant_id != self.tenant_id:
            return None

        group_id = str(uuid.uuid4())

        group = VisitGroup(
            id=group_id,
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            host_id=host_id,
            host_name=host.name,
            location_id=location_id,
            visit_date=visit_date,
            start_time=start_time,
            end_time=end_time,
            shared_purpose=shared_purpose
        )

        self._groups[group_id] = group
        return group

    def add_to_group(
        self,
        group_id: str,
        visitor_email: str,
        visitor_first_name: str,
        visitor_last_name: str,
        *,
        visitor_company: str = "",
        is_leader: bool = False
    ) -> Optional[Visit]:
        """Ajouter un visiteur au groupe."""
        group = self._groups.get(group_id)
        if not group or group.tenant_id != self.tenant_id:
            return None

        visit = self.schedule_visit(
            group.location_id,
            group.host_id,
            visitor_email,
            visitor_first_name,
            visitor_last_name,
            group.visit_date,
            scheduled_start=group.start_time,
            scheduled_end=group.end_time,
            visitor_company=visitor_company,
            purpose=group.shared_purpose
        )

        if visit:
            visit.group_id = group_id
            visit.is_group_leader = is_leader
            group.visit_ids.append(visit.id)
            group.member_count += 1

        return visit

    # ===== Watchlist =====

    def add_to_watchlist(
        self,
        list_type: str,
        reason: str,
        *,
        email: Optional[str] = None,
        id_number: Optional[str] = None,
        name: Optional[str] = None,
        action: str = "deny",
        valid_until: Optional[date] = None,
        added_by: str = ""
    ) -> WatchlistEntry:
        """Ajouter une entrée à la watchlist."""
        entry_id = str(uuid.uuid4())

        entry = WatchlistEntry(
            id=entry_id,
            tenant_id=self.tenant_id,
            email=email,
            id_number=id_number,
            name=name,
            list_type=list_type,
            reason=reason,
            action=action,
            valid_until=valid_until,
            added_by=added_by
        )

        self._watchlist[entry_id] = entry

        # Mettre à jour les profils
        if email:
            profile = self.get_profile_by_email(email)
            if profile:
                if list_type == "blacklist":
                    profile.is_blacklisted = True
                    profile.blacklist_reason = reason
                elif list_type == "vip":
                    profile.is_vip = True

        return entry

    def check_watchlist(
        self,
        email: Optional[str] = None,
        id_number: Optional[str] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Vérifier la watchlist."""
        today = date.today()

        for entry in self._watchlist.values():
            if entry.tenant_id != self.tenant_id or not entry.is_active:
                continue

            if entry.valid_until and entry.valid_until < today:
                continue

            matched = False

            if email and entry.email and entry.email.lower() == email.lower():
                matched = True
            if id_number and entry.id_number and entry.id_number == id_number:
                matched = True
            if name and entry.name and entry.name.lower() in name.lower():
                matched = True

            if matched:
                return {
                    "found": True,
                    "list_type": entry.list_type,
                    "action": entry.action,
                    "reason": entry.reason,
                    "blocked": entry.action == "deny"
                }

        return {"found": False, "blocked": False}

    # ===== Notifications (simulation) =====

    def _send_host_notification(self, visit: Visit, event_type: str) -> None:
        """Envoyer une notification à l'hôte."""
        pass  # Implémentation réelle avec service de notification

    def _send_visitor_invitation(self, visit: Visit) -> None:
        """Envoyer une invitation au visiteur."""
        pass  # Implémentation réelle avec service email

    # ===== Statistiques =====

    def get_stats(
        self,
        period_start: date,
        period_end: date,
        location_id: Optional[str] = None
    ) -> VisitorStats:
        """Calculer les statistiques."""
        visits = [
            v for v in self._visits.values()
            if v.tenant_id == self.tenant_id and
               v.scheduled_date >= period_start and
               v.scheduled_date <= period_end
        ]

        if location_id:
            visits = [v for v in visits if v.location_id == location_id]

        # Volumes
        total = len(visits)
        unique_emails = set(v.visitor_email for v in visits)
        unique = len(unique_emails)

        completed = len([v for v in visits if v.status == VisitStatus.CHECKED_OUT])
        cancelled = len([v for v in visits if v.status == VisitStatus.CANCELLED])
        no_shows = len([v for v in visits if v.status == VisitStatus.NO_SHOW])

        # Actuellement sur site
        current = len([
            v for v in self._visits.values()
            if v.tenant_id == self.tenant_id and v.status == VisitStatus.CHECKED_IN
        ])
        if location_id:
            current = len([
                v for v in self._visits.values()
                if v.tenant_id == self.tenant_id and
                   v.status == VisitStatus.CHECKED_IN and
                   v.location_id == location_id
            ])

        # Par type
        by_type: Dict[str, int] = {}
        for v in visits:
            t = v.visitor_type.value
            by_type[t] = by_type.get(t, 0) + 1

        # Durées
        durations = []
        for v in visits:
            if v.checked_in_at and v.checked_out_at:
                duration = (v.checked_out_at - v.checked_in_at).total_seconds() / 60
                durations.append(duration)
        avg_duration = int(sum(durations) / len(durations)) if durations else 0

        # Pre-registration rate
        pre_reg = len([v for v in visits if v.pre_register_email_sent])
        pre_reg_rate = (Decimal(pre_reg) / Decimal(total) * 100) if total > 0 else Decimal("0")

        # Par jour
        by_day: Dict[str, int] = {}
        for v in visits:
            day = v.scheduled_date.isoformat()
            by_day[day] = by_day.get(day, 0) + 1

        # Peak hours
        hour_counts: Dict[int, int] = {}
        for v in visits:
            if v.checked_in_at:
                h = v.checked_in_at.hour
                hour_counts[h] = hour_counts.get(h, 0) + 1
        peak_hours = sorted(hour_counts.keys(), key=lambda x: hour_counts[x], reverse=True)[:3]

        # Top hosts
        host_counts: Dict[str, int] = {}
        for v in visits:
            host_counts[v.host_name] = host_counts.get(v.host_name, 0) + 1
        top_hosts = [
            {"name": name, "count": count}
            for name, count in sorted(host_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # Rating
        ratings = [v.rating for v in visits if v.rating is not None]
        avg_rating = Decimal(str(sum(ratings) / len(ratings))) if ratings else Decimal("0")

        return VisitorStats(
            tenant_id=self.tenant_id,
            location_id=location_id,
            period_start=period_start,
            period_end=period_end,
            total_visits=total,
            unique_visitors=unique,
            current_on_site=current,
            completed_visits=completed,
            cancelled_visits=cancelled,
            no_shows=no_shows,
            visits_by_type=by_type,
            avg_visit_duration_minutes=avg_duration,
            pre_registration_rate=pre_reg_rate,
            visits_by_day=by_day,
            peak_hours=peak_hours,
            top_hosts=top_hosts,
            avg_rating=avg_rating
        )


# ============== Factory ==============

def create_visitor_service(tenant_id: str) -> VisitorService:
    """Factory pour créer une instance du service."""
    return VisitorService(tenant_id)
