"""
AZALS MODULE EVENTS - Router API
=================================

API REST pour la gestion des evenements.
Tous les endpoints sont securises et isoles par tenant.
"""
from __future__ import annotations


from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User

from .exceptions import (
    CertificateAlreadyIssuedException,
    CertificateNotEligibleException,
    CheckInAlreadyDoneException,
    CheckInNotAllowedException,
    CheckInNotFoundException,
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
from .models import EventStatus, RegistrationStatus
from .schemas import (
    CertificateIssue,
    CertificateResponse,
    CheckInCreate,
    CheckInResponse,
    CheckInStats,
    DiscountCodeApply,
    DiscountCodeCreate,
    DiscountCodeResponse,
    DiscountCodeResult,
    EventAgenda,
    EventCreate,
    EventDashboard,
    EventList,
    EventListItem,
    EventResponse,
    EventStats,
    EventUpdate,
    EvaluationResponse,
    EvaluationStats,
    EvaluationSubmit,
    GlobalEventStats,
    InvitationCreate,
    InvitationResponse,
    RegistrationCreate,
    RegistrationList,
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
)
from .service_impl import get_events_service

router = APIRouter(prefix="/events", tags=["Events (Gestion d'evenements)"])


# ============================================================================
# HELPERS
# ============================================================================

def _handle_exception(e: Exception):
    """Convertit les exceptions metier en reponses HTTP."""
    if isinstance(e, EventNotFoundException):
        raise HTTPException(status_code=404, detail=str(e))
    elif isinstance(e, (EventCodeExistsException, RegistrationDuplicateException, SpeakerAlreadyAssignedException)):
        raise HTTPException(status_code=409, detail=str(e))
    elif isinstance(e, (RegistrationClosedException, EventCapacityException, TicketSoldOutException)):
        raise HTTPException(status_code=400, detail=str(e))
    elif isinstance(e, (EventStatusException, RegistrationStatusException)):
        raise HTTPException(status_code=422, detail=str(e))
    elif isinstance(e, (VenueNotFoundException, SpeakerNotFoundException, SessionNotFoundException,
                       TicketTypeNotFoundException, RegistrationNotFoundException,
                       CheckInNotFoundException, InvitationNotFoundException,
                       DiscountCodeNotFoundException)):
        raise HTTPException(status_code=404, detail=str(e))
    elif isinstance(e, (CheckInAlreadyDoneException, CertificateAlreadyIssuedException)):
        raise HTTPException(status_code=409, detail=str(e))
    elif isinstance(e, (CheckInNotAllowedException, CertificateNotEligibleException,
                       InvitationExpiredException)):
        raise HTTPException(status_code=400, detail=str(e))
    else:
        raise HTTPException(status_code=500, detail="Erreur interne")


# ============================================================================
# LIEUX
# ============================================================================

@router.post("/venues", response_model=VenueResponse, status_code=201)
def create_venue(
    data: VenueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer un nouveau lieu."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.create_venue(data)
    except Exception as e:
        _handle_exception(e)


@router.get("/venues", response_model=list[VenueResponse])
def list_venues(
    city: str | None = None,
    venue_type: str | None = None,
    min_capacity: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les lieux."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    venues, _ = service.list_venues(city, venue_type, min_capacity, skip, limit)
    return venues


@router.get("/venues/{venue_id}", response_model=VenueWithRoomsResponse)
def get_venue(
    venue_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer un lieu avec ses salles."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    venue = service.get_venue_with_rooms(venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail="Lieu non trouve")
    return venue


@router.put("/venues/{venue_id}", response_model=VenueResponse)
def update_venue(
    venue_id: UUID,
    data: VenueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour un lieu."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.update_venue(venue_id, data)
    except Exception as e:
        _handle_exception(e)


@router.delete("/venues/{venue_id}", status_code=204)
def delete_venue(
    venue_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un lieu."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    if not service.delete_venue(venue_id):
        raise HTTPException(status_code=404, detail="Lieu non trouve")


@router.post("/venues/{venue_id}/rooms", response_model=VenueRoomResponse, status_code=201)
def create_room(
    venue_id: UUID,
    data: VenueRoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer une salle dans un lieu."""
    try:
        data.venue_id = venue_id
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.create_room(data)
    except Exception as e:
        _handle_exception(e)


@router.get("/venues/{venue_id}/rooms", response_model=list[VenueRoomResponse])
def list_rooms(
    venue_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les salles d'un lieu."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    return service.list_rooms(venue_id)


# ============================================================================
# EVENEMENTS
# ============================================================================

@router.post("", response_model=EventResponse, status_code=201)
def create_event(
    data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer un nouvel evenement."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.create_event(data)
    except Exception as e:
        _handle_exception(e)


@router.get("", response_model=EventList)
def list_events(
    status: EventStatus | None = None,
    event_type: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    is_public: bool | None = None,
    category: str | None = None,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les evenements."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    events, total = service.list_events(
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
    return EventList(items=events, total=total, page=skip // limit + 1, page_size=limit)


@router.get("/stats", response_model=GlobalEventStats)
def get_global_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer les statistiques globales des evenements."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    return service.get_global_stats()


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer un evenement."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    event = service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Evenement non trouve")
    return event


@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: UUID,
    data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour un evenement."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.update_event(event_id, data)
    except Exception as e:
        _handle_exception(e)


@router.delete("/{event_id}", status_code=204)
def delete_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un evenement."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    if not service.delete_event(event_id):
        raise HTTPException(status_code=404, detail="Evenement non trouve")


@router.post("/{event_id}/publish", response_model=EventResponse)
def publish_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Publier un evenement."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.publish_event(event_id)
    except Exception as e:
        _handle_exception(e)


@router.post("/{event_id}/open-registration", response_model=EventResponse)
def open_registration(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ouvrir les inscriptions."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.open_registration(event_id)
    except Exception as e:
        _handle_exception(e)


@router.post("/{event_id}/close-registration", response_model=EventResponse)
def close_registration(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fermer les inscriptions."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.close_registration(event_id)
    except Exception as e:
        _handle_exception(e)


@router.post("/{event_id}/start", response_model=EventResponse)
def start_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Demarrer un evenement."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.start_event(event_id)
    except Exception as e:
        _handle_exception(e)


@router.post("/{event_id}/complete", response_model=EventResponse)
def complete_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Terminer un evenement."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.complete_event(event_id)
    except Exception as e:
        _handle_exception(e)


@router.post("/{event_id}/cancel", response_model=EventResponse)
def cancel_event(
    event_id: UUID,
    reason: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Annuler un evenement."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.cancel_event(event_id, reason)
    except Exception as e:
        _handle_exception(e)


@router.get("/{event_id}/dashboard", response_model=EventDashboard)
def get_event_dashboard(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer le dashboard complet d'un evenement."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.get_event_dashboard(event_id)
    except Exception as e:
        _handle_exception(e)


@router.get("/{event_id}/stats", response_model=EventStats)
def get_event_stats(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer les statistiques d'un evenement."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.get_event_stats(event_id)
    except Exception as e:
        _handle_exception(e)


@router.get("/{event_id}/agenda", response_model=EventAgenda)
def get_event_agenda(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer l'agenda de l'evenement."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.get_agenda(event_id)
    except Exception as e:
        _handle_exception(e)


# ============================================================================
# INTERVENANTS
# ============================================================================

@router.post("/speakers", response_model=SpeakerResponse, status_code=201)
def create_speaker(
    data: SpeakerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer un intervenant."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    return service.create_speaker(data)


@router.get("/speakers", response_model=list[SpeakerResponse])
def list_speakers(
    search: str | None = None,
    is_internal: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les intervenants."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    speakers, _ = service.list_speakers(search, is_internal, skip, limit)
    return speakers


@router.get("/speakers/{speaker_id}", response_model=SpeakerResponse)
def get_speaker(
    speaker_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer un intervenant."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    speaker = service.get_speaker(speaker_id)
    if not speaker:
        raise HTTPException(status_code=404, detail="Intervenant non trouve")
    return speaker


@router.put("/speakers/{speaker_id}", response_model=SpeakerResponse)
def update_speaker(
    speaker_id: UUID,
    data: SpeakerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour un intervenant."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.update_speaker(speaker_id, data)
    except Exception as e:
        _handle_exception(e)


@router.post("/{event_id}/speakers", response_model=SpeakerAssignmentResponse, status_code=201)
def assign_speaker(
    event_id: UUID,
    data: SpeakerAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Affecter un intervenant a un evenement."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.assign_speaker_to_event(event_id, data)
    except Exception as e:
        _handle_exception(e)


@router.get("/{event_id}/speakers", response_model=list[SpeakerAssignmentResponse])
def list_event_speakers(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les intervenants d'un evenement."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    return service.list_event_speakers(event_id)


# ============================================================================
# SESSIONS
# ============================================================================

@router.post("/{event_id}/sessions", response_model=SessionResponse, status_code=201)
def create_session(
    event_id: UUID,
    data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer une session."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.create_session(event_id, data)
    except Exception as e:
        _handle_exception(e)


@router.get("/{event_id}/sessions", response_model=list[SessionResponse])
def list_sessions(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les sessions d'un evenement."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    return service.list_sessions(event_id)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer une session."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvee")
    return session


@router.put("/sessions/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: UUID,
    data: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour une session."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.update_session(session_id, data)
    except Exception as e:
        _handle_exception(e)


# ============================================================================
# BILLETTERIE
# ============================================================================

@router.post("/{event_id}/ticket-types", response_model=TicketTypeResponse, status_code=201)
def create_ticket_type(
    event_id: UUID,
    data: TicketTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer un type de billet."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.create_ticket_type(event_id, data)
    except Exception as e:
        _handle_exception(e)


@router.get("/{event_id}/ticket-types", response_model=list[TicketTypeResponse])
def list_ticket_types(
    event_id: UUID,
    available_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les types de billets."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    return service.list_ticket_types(event_id, available_only)


@router.put("/ticket-types/{ticket_type_id}", response_model=TicketTypeResponse)
def update_ticket_type(
    ticket_type_id: UUID,
    data: TicketTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour un type de billet."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.update_ticket_type(ticket_type_id, data)
    except Exception as e:
        _handle_exception(e)


# ============================================================================
# INSCRIPTIONS
# ============================================================================

@router.post("/{event_id}/registrations", response_model=RegistrationResponse, status_code=201)
def register(
    event_id: UUID,
    data: RegistrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Inscrire un participant."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.register(event_id, data)
    except Exception as e:
        _handle_exception(e)


@router.get("/{event_id}/registrations", response_model=RegistrationList)
def list_registrations(
    event_id: UUID,
    status: RegistrationStatus | None = None,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les inscriptions d'un evenement."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    registrations, total = service.list_registrations(
        event_id, status, search, skip, limit
    )
    return RegistrationList(
        items=registrations,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/registrations/{registration_id}", response_model=RegistrationResponse)
def get_registration(
    registration_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer une inscription."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    registration = service.get_registration(registration_id)
    if not registration:
        raise HTTPException(status_code=404, detail="Inscription non trouvee")
    return registration


@router.get("/registrations/by-number/{reg_number}", response_model=RegistrationResponse)
def get_registration_by_number(
    reg_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer une inscription par numero."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    registration = service.get_registration_by_number(reg_number)
    if not registration:
        raise HTTPException(status_code=404, detail="Inscription non trouvee")
    return registration


@router.put("/registrations/{registration_id}", response_model=RegistrationResponse)
def update_registration(
    registration_id: UUID,
    data: RegistrationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour une inscription."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.update_registration(registration_id, data)
    except Exception as e:
        _handle_exception(e)


@router.post("/registrations/{registration_id}/confirm", response_model=RegistrationResponse)
def confirm_registration(
    registration_id: UUID,
    payment_reference: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Confirmer une inscription."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.confirm_registration(registration_id, payment_reference)
    except Exception as e:
        _handle_exception(e)


@router.post("/registrations/{registration_id}/cancel", response_model=RegistrationResponse)
def cancel_registration(
    registration_id: UUID,
    reason: str | None = Query(None),
    refund: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Annuler une inscription."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.cancel_registration(registration_id, reason, refund)
    except Exception as e:
        _handle_exception(e)


# ============================================================================
# CHECK-IN
# ============================================================================

@router.post("/{event_id}/checkin", response_model=CheckInResponse)
def check_in(
    event_id: UUID,
    data: CheckInCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enregistrer un check-in."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.check_in(event_id, data)
    except Exception as e:
        _handle_exception(e)


@router.get("/{event_id}/checkin/stats", response_model=CheckInStats)
def get_checkin_stats(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer les statistiques de check-in."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.get_checkin_stats(event_id)
    except Exception as e:
        _handle_exception(e)


# ============================================================================
# SPONSORS
# ============================================================================

@router.post("/{event_id}/sponsors", response_model=SponsorResponse, status_code=201)
def add_sponsor(
    event_id: UUID,
    data: SponsorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ajouter un sponsor."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.add_sponsor(event_id, data)
    except Exception as e:
        _handle_exception(e)


@router.get("/{event_id}/sponsors", response_model=list[SponsorResponse])
def list_sponsors(
    event_id: UUID,
    level: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les sponsors d'un evenement."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    return service.list_sponsors(event_id, level)


@router.put("/sponsors/{sponsor_id}", response_model=SponsorResponse)
def update_sponsor(
    sponsor_id: UUID,
    data: SponsorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour un sponsor."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.update_sponsor(sponsor_id, data)
    except Exception as e:
        _handle_exception(e)


# ============================================================================
# CODES PROMO
# ============================================================================

@router.post("/{event_id}/discount-codes", response_model=DiscountCodeResponse, status_code=201)
def create_discount_code(
    event_id: UUID,
    data: DiscountCodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer un code promo."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.create_discount_code(event_id, data)
    except Exception as e:
        _handle_exception(e)


@router.get("/{event_id}/discount-codes", response_model=list[DiscountCodeResponse])
def list_discount_codes(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les codes promo d'un evenement."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    return service.list_discount_codes(event_id)


@router.post("/{event_id}/discount-codes/apply", response_model=DiscountCodeResult)
def apply_discount_code(
    event_id: UUID,
    data: DiscountCodeApply,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Appliquer un code promo."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    return service.apply_discount_code(event_id, data)


# ============================================================================
# CERTIFICATS
# ============================================================================

@router.post("/{event_id}/certificates", response_model=CertificateResponse, status_code=201)
def issue_certificate(
    event_id: UUID,
    data: CertificateIssue,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Emettre un certificat."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.issue_certificate(event_id, data)
    except Exception as e:
        _handle_exception(e)


@router.get("/certificates/verify/{verification_code}", response_model=CertificateResponse)
def verify_certificate(
    verification_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verifier un certificat."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    certificate = service.verify_certificate(verification_code)
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificat non trouve")
    return certificate


# ============================================================================
# EVALUATIONS
# ============================================================================

@router.post("/{event_id}/evaluations", response_model=EvaluationResponse, status_code=201)
def submit_evaluation(
    event_id: UUID,
    data: EvaluationSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soumettre une evaluation."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.submit_evaluation(event_id, data)
    except Exception as e:
        _handle_exception(e)


@router.get("/{event_id}/evaluations/stats", response_model=EvaluationStats)
def get_evaluation_stats(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer les statistiques d'evaluation."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.get_evaluation_stats(event_id)
    except Exception as e:
        _handle_exception(e)


# ============================================================================
# INVITATIONS
# ============================================================================

@router.post("/{event_id}/invitations", response_model=InvitationResponse, status_code=201)
def send_invitation(
    event_id: UUID,
    data: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Envoyer une invitation."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.send_invitation(event_id, data)
    except Exception as e:
        _handle_exception(e)


@router.get("/{event_id}/invitations", response_model=list[InvitationResponse])
def list_invitations(
    event_id: UUID,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les invitations d'un evenement."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    return service.list_invitations(event_id, status)


@router.post("/invitations/{invitation_code}/accept", response_model=InvitationResponse)
def accept_invitation(
    invitation_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accepter une invitation."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.accept_invitation(invitation_code)
    except Exception as e:
        _handle_exception(e)


# ============================================================================
# WAITLIST
# ============================================================================

@router.post("/{event_id}/waitlist", response_model=WaitlistResponse, status_code=201)
def add_to_waitlist(
    event_id: UUID,
    data: WaitlistEntry,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ajouter a la liste d'attente."""
    try:
        service = get_events_service(db, current_user.tenant_id, current_user.id)
        return service.add_to_waitlist(event_id, data)
    except Exception as e:
        _handle_exception(e)


@router.get("/{event_id}/waitlist", response_model=list[WaitlistResponse])
def list_waitlist(
    event_id: UUID,
    ticket_type_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister la liste d'attente."""
    service = get_events_service(db, current_user.tenant_id, current_user.id)
    return service.list_waitlist(event_id, ticket_type_id)
