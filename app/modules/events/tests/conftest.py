"""
Configuration pytest et fixtures communes pour les tests Events
================================================================
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, date, timedelta
from uuid import uuid4
from decimal import Decimal

from app.core.saas_context import SaaSContext, UserRole

from app.modules.events.models import (
    Venue,
    VenueRoom,
    Event,
    Speaker,
    EventSpeakerAssignment,
    EventSession,
    EventTicketType,
    EventRegistration,
    EventCheckIn,
    EventSponsor,
    EventDiscountCode,
    EventCertificateTemplate,
    EventCertificate,
    EventEvaluationForm,
    EventEvaluation,
    EventInvitation,
    EventWaitlist,
    EventType,
    EventStatus,
    EventFormat,
    TicketType,
    RegistrationStatus,
    PaymentStatus,
    SessionType,
    SpeakerRole,
    SponsorLevel,
    CertificateType,
    EvaluationStatus,
)


# ============================================================================
# FIXTURES HERITEES DU CONFTEST GLOBAL
# ============================================================================
# Les fixtures suivantes sont heritees de app/conftest.py:
# - tenant_id, user_id, user_uuid
# - db_session, test_db_session
# - test_client (avec headers auto-injectes)
# - mock_auth_global (autouse=True)
# - saas_context


@pytest.fixture
def client(test_client):
    """
    Alias pour test_client (compatibilite avec anciens tests).

    Le test_client du conftest global ajoute deja les headers requis.
    """
    return test_client


@pytest.fixture
def auth_headers(tenant_id):
    """Headers d'authentification avec tenant ID."""
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": tenant_id
    }


@pytest.fixture(scope="function")
def clean_database(db_session):
    """Nettoyer la base apres chaque test."""
    yield
    db_session.rollback()


@pytest.fixture
def mock_context(tenant_id, user_id):
    """Fixture pour le contexte SaaS mocke."""
    context = MagicMock(spec=SaaSContext)
    context.tenant_id = tenant_id
    context.user_id = user_id
    context.roles = [UserRole.ADMIN]
    context.permissions = ["events.*"]
    return context


# ============================================================================
# FIXTURES DONNEES VENUES
# ============================================================================

@pytest.fixture
def sample_venue(db_session, tenant_id):
    """Fixture pour un lieu de test"""
    venue = Venue(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Centre de Conferences Paris",
        address="123 Avenue des Champs-Elysees",
        city="Paris",
        postal_code="75008",
        country="France",
        capacity=500,
        is_active=True,
        amenities=["wifi", "parking", "restaurant"]
    )
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    return venue


@pytest.fixture
def sample_room(db_session, tenant_id, sample_venue):
    """Fixture pour une salle de test"""
    room = VenueRoom(
        id=uuid4(),
        tenant_id=tenant_id,
        venue_id=sample_venue.id,
        name="Salle Eiffel",
        capacity=100,
        floor="1er etage",
        amenities=["projecteur", "tableau_blanc", "climatisation"]
    )
    db_session.add(room)
    db_session.commit()
    db_session.refresh(room)
    return room


@pytest.fixture
def venue_data():
    """Donnees de test pour creation lieu"""
    return {
        "name": "Nouveau Centre",
        "address": "456 Rue de la Paix",
        "city": "Lyon",
        "postal_code": "69001",
        "country": "France",
        "capacity": 300
    }


@pytest.fixture
def room_data(sample_venue):
    """Donnees de test pour creation salle"""
    return {
        "venue_id": str(sample_venue.id),
        "name": "Salle Bellecour",
        "capacity": 50,
        "floor": "RDC"
    }


# ============================================================================
# FIXTURES DONNEES EVENTS
# ============================================================================

@pytest.fixture
def sample_event(db_session, tenant_id, sample_venue, user_id):
    """Fixture pour un evenement de test"""
    event = Event(
        id=uuid4(),
        tenant_id=tenant_id,
        code="EVT-2026-0001",
        title="Conference Tech 2026",
        description="La plus grande conference tech de l'annee",
        event_type=EventType.CONFERENCE,
        format=EventFormat.IN_PERSON,
        status=EventStatus.PUBLISHED,
        venue_id=sample_venue.id,
        start_date=datetime.now() + timedelta(days=30),
        end_date=datetime.now() + timedelta(days=32),
        registration_start=datetime.now() - timedelta(days=10),
        registration_end=datetime.now() + timedelta(days=25),
        max_capacity=500,
        current_registrations=0,
        is_free=False,
        base_price=Decimal("199.00"),
        currency="EUR",
        created_by=user_id
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture
def draft_event(db_session, tenant_id, sample_venue, user_id):
    """Fixture pour un evenement brouillon"""
    event = Event(
        id=uuid4(),
        tenant_id=tenant_id,
        code="EVT-2026-0002",
        title="Atelier Formation",
        event_type=EventType.WORKSHOP,
        format=EventFormat.IN_PERSON,
        status=EventStatus.DRAFT,
        venue_id=sample_venue.id,
        start_date=datetime.now() + timedelta(days=60),
        end_date=datetime.now() + timedelta(days=60),
        max_capacity=30,
        is_free=True,
        created_by=user_id
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture
def event_data(sample_venue):
    """Donnees de test pour creation evenement"""
    return {
        "title": "Nouveau Seminaire",
        "description": "Un seminaire innovant",
        "event_type": "SEMINAR",
        "format": "HYBRID",
        "venue_id": str(sample_venue.id),
        "start_date": (datetime.now() + timedelta(days=45)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=45)).isoformat(),
        "max_capacity": 100,
        "is_free": False,
        "base_price": "149.00",
        "currency": "EUR"
    }


# ============================================================================
# FIXTURES DONNEES SPEAKERS
# ============================================================================

@pytest.fixture
def sample_speaker(db_session, tenant_id):
    """Fixture pour un intervenant de test"""
    speaker = Speaker(
        id=uuid4(),
        tenant_id=tenant_id,
        first_name="Marie",
        last_name="Curie",
        email="marie.curie@example.com",
        title="Dr.",
        company="Institut de Recherche",
        bio="Experte en innovation technologique",
        is_active=True
    )
    db_session.add(speaker)
    db_session.commit()
    db_session.refresh(speaker)
    return speaker


@pytest.fixture
def speaker_data():
    """Donnees de test pour creation intervenant"""
    return {
        "first_name": "Albert",
        "last_name": "Einstein",
        "email": "albert.einstein@example.com",
        "title": "Prof.",
        "company": "Universite",
        "bio": "Expert en physique theorique"
    }


@pytest.fixture
def sample_speaker_assignment(db_session, tenant_id, sample_event, sample_speaker):
    """Fixture pour une assignation intervenant"""
    assignment = EventSpeakerAssignment(
        id=uuid4(),
        tenant_id=tenant_id,
        event_id=sample_event.id,
        speaker_id=sample_speaker.id,
        role=SpeakerRole.KEYNOTE
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment


# ============================================================================
# FIXTURES DONNEES SESSIONS
# ============================================================================

@pytest.fixture
def sample_session(db_session, tenant_id, sample_event, sample_room):
    """Fixture pour une session de test"""
    session = EventSession(
        id=uuid4(),
        tenant_id=tenant_id,
        event_id=sample_event.id,
        room_id=sample_room.id,
        title="Introduction a l'IA",
        description="Comprendre les bases de l'intelligence artificielle",
        session_type=SessionType.PRESENTATION,
        start_time=sample_event.start_date + timedelta(hours=9),
        end_time=sample_event.start_date + timedelta(hours=10, minutes=30),
        max_capacity=100,
        current_attendees=0,
        is_active=True
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.fixture
def session_data(sample_event, sample_room):
    """Donnees de test pour creation session"""
    return {
        "event_id": str(sample_event.id),
        "room_id": str(sample_room.id),
        "title": "Nouvelle Session",
        "description": "Description de la session",
        "session_type": "WORKSHOP",
        "start_time": (sample_event.start_date + timedelta(hours=14)).isoformat(),
        "end_time": (sample_event.start_date + timedelta(hours=16)).isoformat(),
        "max_capacity": 50
    }


# ============================================================================
# FIXTURES DONNEES TICKETS
# ============================================================================

@pytest.fixture
def sample_ticket_type(db_session, tenant_id, sample_event):
    """Fixture pour un type de billet de test"""
    ticket_type = EventTicketType(
        id=uuid4(),
        tenant_id=tenant_id,
        event_id=sample_event.id,
        name="Billet Standard",
        description="Acces complet a la conference",
        ticket_type=TicketType.STANDARD,
        price=Decimal("199.00"),
        currency="EUR",
        quantity_available=200,
        quantity_sold=0,
        max_per_order=5,
        sales_start=datetime.now() - timedelta(days=10),
        sales_end=datetime.now() + timedelta(days=25),
        is_active=True
    )
    db_session.add(ticket_type)
    db_session.commit()
    db_session.refresh(ticket_type)
    return ticket_type


@pytest.fixture
def vip_ticket_type(db_session, tenant_id, sample_event):
    """Fixture pour un billet VIP"""
    ticket_type = EventTicketType(
        id=uuid4(),
        tenant_id=tenant_id,
        event_id=sample_event.id,
        name="Billet VIP",
        description="Acces VIP avec avantages exclusifs",
        ticket_type=TicketType.VIP,
        price=Decimal("499.00"),
        currency="EUR",
        quantity_available=50,
        quantity_sold=0,
        max_per_order=2,
        is_active=True
    )
    db_session.add(ticket_type)
    db_session.commit()
    db_session.refresh(ticket_type)
    return ticket_type


@pytest.fixture
def ticket_type_data(sample_event):
    """Donnees de test pour creation type billet"""
    return {
        "event_id": str(sample_event.id),
        "name": "Early Bird",
        "description": "Tarif reduit pour inscription anticipee",
        "ticket_type": "EARLY_BIRD",
        "price": "149.00",
        "currency": "EUR",
        "quantity_available": 100,
        "max_per_order": 3
    }


# ============================================================================
# FIXTURES DONNEES REGISTRATIONS
# ============================================================================

@pytest.fixture
def sample_registration(db_session, tenant_id, sample_event, sample_ticket_type, user_id):
    """Fixture pour une inscription de test"""
    registration = EventRegistration(
        id=uuid4(),
        tenant_id=tenant_id,
        event_id=sample_event.id,
        ticket_type_id=sample_ticket_type.id,
        registration_code="REG-2026-ABC123",
        first_name="Jean",
        last_name="Dupont",
        email="jean.dupont@example.com",
        phone="+33612345678",
        company="Tech Corp",
        status=RegistrationStatus.CONFIRMED,
        payment_status=PaymentStatus.PAID,
        quantity=1,
        unit_price=Decimal("199.00"),
        total_price=Decimal("199.00"),
        currency="EUR",
        qr_code="QR-ABC123",
        registered_by=user_id
    )
    db_session.add(registration)
    db_session.commit()
    db_session.refresh(registration)
    return registration


@pytest.fixture
def pending_registration(db_session, tenant_id, sample_event, sample_ticket_type, user_id):
    """Fixture pour une inscription en attente"""
    registration = EventRegistration(
        id=uuid4(),
        tenant_id=tenant_id,
        event_id=sample_event.id,
        ticket_type_id=sample_ticket_type.id,
        registration_code="REG-2026-DEF456",
        first_name="Pierre",
        last_name="Martin",
        email="pierre.martin@example.com",
        status=RegistrationStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        quantity=2,
        unit_price=Decimal("199.00"),
        total_price=Decimal("398.00"),
        currency="EUR",
        registered_by=user_id
    )
    db_session.add(registration)
    db_session.commit()
    db_session.refresh(registration)
    return registration


@pytest.fixture
def registration_data(sample_event, sample_ticket_type):
    """Donnees de test pour creation inscription"""
    return {
        "event_id": str(sample_event.id),
        "ticket_type_id": str(sample_ticket_type.id),
        "first_name": "Nouveau",
        "last_name": "Participant",
        "email": "nouveau.participant@example.com",
        "phone": "+33698765432",
        "quantity": 1
    }


# ============================================================================
# FIXTURES DONNEES SPONSORS
# ============================================================================

@pytest.fixture
def sample_sponsor(db_session, tenant_id, sample_event):
    """Fixture pour un sponsor de test"""
    sponsor = EventSponsor(
        id=uuid4(),
        tenant_id=tenant_id,
        event_id=sample_event.id,
        name="Tech Company",
        level=SponsorLevel.GOLD,
        logo_url="https://example.com/logo.png",
        website="https://techcompany.com",
        description="Leader mondial de la tech",
        amount=Decimal("10000.00"),
        is_active=True
    )
    db_session.add(sponsor)
    db_session.commit()
    db_session.refresh(sponsor)
    return sponsor


@pytest.fixture
def sponsor_data(sample_event):
    """Donnees de test pour creation sponsor"""
    return {
        "event_id": str(sample_event.id),
        "name": "New Sponsor",
        "level": "SILVER",
        "website": "https://newsponsor.com",
        "amount": "5000.00"
    }


# ============================================================================
# FIXTURES DONNEES DISCOUNT CODES
# ============================================================================

@pytest.fixture
def sample_discount_code(db_session, tenant_id, sample_event):
    """Fixture pour un code promo de test"""
    discount = EventDiscountCode(
        id=uuid4(),
        tenant_id=tenant_id,
        event_id=sample_event.id,
        code="EARLYBIRD20",
        description="20% de reduction",
        discount_type="PERCENTAGE",
        discount_value=Decimal("20.00"),
        max_uses=100,
        times_used=0,
        valid_from=datetime.now() - timedelta(days=5),
        valid_until=datetime.now() + timedelta(days=20),
        is_active=True
    )
    db_session.add(discount)
    db_session.commit()
    db_session.refresh(discount)
    return discount


@pytest.fixture
def expired_discount_code(db_session, tenant_id, sample_event):
    """Fixture pour un code promo expire"""
    discount = EventDiscountCode(
        id=uuid4(),
        tenant_id=tenant_id,
        event_id=sample_event.id,
        code="EXPIRED50",
        discount_type="PERCENTAGE",
        discount_value=Decimal("50.00"),
        valid_from=datetime.now() - timedelta(days=30),
        valid_until=datetime.now() - timedelta(days=5),
        is_active=True
    )
    db_session.add(discount)
    db_session.commit()
    db_session.refresh(discount)
    return discount


@pytest.fixture
def discount_code_data(sample_event):
    """Donnees de test pour creation code promo"""
    return {
        "event_id": str(sample_event.id),
        "code": "NEWCODE30",
        "description": "30% de reduction",
        "discount_type": "PERCENTAGE",
        "discount_value": "30.00",
        "max_uses": 50,
        "valid_from": datetime.now().isoformat(),
        "valid_until": (datetime.now() + timedelta(days=30)).isoformat()
    }


# ============================================================================
# FIXTURES DONNEES CERTIFICATES
# ============================================================================

@pytest.fixture
def sample_certificate_template(db_session, tenant_id, sample_event):
    """Fixture pour un modele de certificat"""
    template = EventCertificateTemplate(
        id=uuid4(),
        tenant_id=tenant_id,
        event_id=sample_event.id,
        name="Certificat de Participation",
        certificate_type=CertificateType.PARTICIPATION,
        template_html="<html><body>Certificat pour {{name}}</body></html>",
        is_active=True
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


@pytest.fixture
def sample_certificate(db_session, tenant_id, sample_registration, sample_certificate_template, user_id):
    """Fixture pour un certificat de test"""
    certificate = EventCertificate(
        id=uuid4(),
        tenant_id=tenant_id,
        registration_id=sample_registration.id,
        template_id=sample_certificate_template.id,
        certificate_number="CERT-2026-001",
        recipient_name="Jean Dupont",
        issued_at=datetime.now(),
        issued_by=user_id
    )
    db_session.add(certificate)
    db_session.commit()
    db_session.refresh(certificate)
    return certificate


@pytest.fixture
def certificate_template_data(sample_event):
    """Donnees de test pour creation modele certificat"""
    return {
        "event_id": str(sample_event.id),
        "name": "Certificat de Completion",
        "certificate_type": "COMPLETION",
        "template_html": "<html><body>{{name}} a complete</body></html>"
    }


# ============================================================================
# FIXTURES DONNEES EVALUATIONS
# ============================================================================

@pytest.fixture
def sample_evaluation_form(db_session, tenant_id, sample_event):
    """Fixture pour un formulaire d'evaluation"""
    form = EventEvaluationForm(
        id=uuid4(),
        tenant_id=tenant_id,
        event_id=sample_event.id,
        title="Evaluation de la Conference",
        description="Merci de noter votre experience",
        questions=[
            {"id": "q1", "text": "Note globale", "type": "rating", "required": True},
            {"id": "q2", "text": "Commentaires", "type": "text", "required": False}
        ],
        is_active=True
    )
    db_session.add(form)
    db_session.commit()
    db_session.refresh(form)
    return form


@pytest.fixture
def sample_evaluation(db_session, tenant_id, sample_registration, sample_evaluation_form):
    """Fixture pour une evaluation de test"""
    evaluation = EventEvaluation(
        id=uuid4(),
        tenant_id=tenant_id,
        registration_id=sample_registration.id,
        form_id=sample_evaluation_form.id,
        responses={"q1": 5, "q2": "Excellente conference!"},
        overall_rating=5,
        status=EvaluationStatus.SUBMITTED,
        submitted_at=datetime.now()
    )
    db_session.add(evaluation)
    db_session.commit()
    db_session.refresh(evaluation)
    return evaluation


@pytest.fixture
def evaluation_data(sample_registration, sample_evaluation_form):
    """Donnees de test pour creation evaluation"""
    return {
        "registration_id": str(sample_registration.id),
        "form_id": str(sample_evaluation_form.id),
        "responses": {"q1": 4, "q2": "Tres bien"},
        "overall_rating": 4
    }


# ============================================================================
# FIXTURES DONNEES INVITATIONS
# ============================================================================

@pytest.fixture
def sample_invitation(db_session, tenant_id, sample_event, user_id):
    """Fixture pour une invitation de test"""
    invitation = EventInvitation(
        id=uuid4(),
        tenant_id=tenant_id,
        event_id=sample_event.id,
        email="invite@example.com",
        first_name="Invite",
        last_name="Test",
        invitation_code="INV-ABC123",
        sent_at=datetime.now() - timedelta(days=2),
        expires_at=datetime.now() + timedelta(days=14),
        sent_by=user_id
    )
    db_session.add(invitation)
    db_session.commit()
    db_session.refresh(invitation)
    return invitation


@pytest.fixture
def invitation_data(sample_event):
    """Donnees de test pour creation invitation"""
    return {
        "event_id": str(sample_event.id),
        "email": "newinvite@example.com",
        "first_name": "Nouveau",
        "last_name": "Invite"
    }


# ============================================================================
# FIXTURES DONNEES CHECK-IN
# ============================================================================

@pytest.fixture
def sample_checkin(db_session, tenant_id, sample_registration, user_id):
    """Fixture pour un check-in de test"""
    checkin = EventCheckIn(
        id=uuid4(),
        tenant_id=tenant_id,
        registration_id=sample_registration.id,
        checked_in_at=datetime.now(),
        checked_in_by=user_id,
        check_in_method="QR_CODE"
    )
    db_session.add(checkin)
    db_session.commit()
    db_session.refresh(checkin)
    return checkin


@pytest.fixture
def checkin_data(sample_registration):
    """Donnees de test pour check-in"""
    return {
        "registration_id": str(sample_registration.id),
        "check_in_method": "MANUAL"
    }


# ============================================================================
# FIXTURES DONNEES WAITLIST
# ============================================================================

@pytest.fixture
def sample_waitlist_entry(db_session, tenant_id, sample_event, sample_ticket_type):
    """Fixture pour une entree liste d'attente"""
    entry = EventWaitlist(
        id=uuid4(),
        tenant_id=tenant_id,
        event_id=sample_event.id,
        ticket_type_id=sample_ticket_type.id,
        email="waitlist@example.com",
        first_name="Attente",
        last_name="Liste",
        registered_at=datetime.now(),
        position=1
    )
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


@pytest.fixture
def waitlist_data(sample_event, sample_ticket_type):
    """Donnees de test pour liste d'attente"""
    return {
        "event_id": str(sample_event.id),
        "ticket_type_id": str(sample_ticket_type.id),
        "email": "newwaitlist@example.com",
        "first_name": "Nouveau",
        "last_name": "Attente"
    }


# ============================================================================
# FIXTURES ENTITIES MOCK
# ============================================================================

@pytest.fixture
def venue_entity():
    """Entity venue mockee pour tests unitaires."""
    entity = MagicMock(spec=Venue)
    entity.id = uuid4()
    entity.name = "Centre de Test"
    entity.city = "Paris"
    entity.capacity = 500
    entity.is_active = True
    return entity


@pytest.fixture
def event_entity():
    """Entity event mockee pour tests unitaires."""
    entity = MagicMock(spec=Event)
    entity.id = uuid4()
    entity.code = "EVT-2026-TEST"
    entity.title = "Evenement Test"
    entity.event_type = EventType.CONFERENCE
    entity.status = EventStatus.PUBLISHED
    entity.start_date = datetime.now() + timedelta(days=30)
    entity.end_date = datetime.now() + timedelta(days=32)
    return entity


@pytest.fixture
def registration_entity():
    """Entity registration mockee pour tests unitaires."""
    entity = MagicMock(spec=EventRegistration)
    entity.id = uuid4()
    entity.registration_code = "REG-TEST-001"
    entity.email = "test@example.com"
    entity.status = RegistrationStatus.CONFIRMED
    entity.payment_status = PaymentStatus.PAID
    return entity


@pytest.fixture
def session_entity():
    """Entity session mockee pour tests unitaires."""
    entity = MagicMock(spec=EventSession)
    entity.id = uuid4()
    entity.title = "Session Test"
    entity.session_type = SessionType.PRESENTATION
    return entity


@pytest.fixture
def speaker_entity():
    """Entity speaker mockee pour tests unitaires."""
    entity = MagicMock(spec=Speaker)
    entity.id = uuid4()
    entity.first_name = "Test"
    entity.last_name = "Speaker"
    entity.email = "speaker@example.com"
    return entity


@pytest.fixture
def ticket_type_entity():
    """Entity ticket type mockee pour tests unitaires."""
    entity = MagicMock(spec=EventTicketType)
    entity.id = uuid4()
    entity.name = "Standard"
    entity.price = Decimal("199.00")
    entity.quantity_available = 100
    entity.quantity_sold = 10
    return entity


@pytest.fixture
def checkin_entity():
    """Entity check-in mockee pour tests unitaires."""
    entity = MagicMock(spec=EventCheckIn)
    entity.id = uuid4()
    entity.checked_in_at = datetime.now()
    return entity


@pytest.fixture
def certificate_entity():
    """Entity certificate mockee pour tests unitaires."""
    entity = MagicMock(spec=EventCertificate)
    entity.id = uuid4()
    entity.certificate_number = "CERT-TEST-001"
    return entity


@pytest.fixture
def evaluation_entity():
    """Entity evaluation mockee pour tests unitaires."""
    entity = MagicMock(spec=EventEvaluation)
    entity.id = uuid4()
    entity.overall_rating = 5
    entity.status = EvaluationStatus.SUBMITTED
    return entity


# ============================================================================
# FIXTURES HELPERS
# ============================================================================

@pytest.fixture
def assert_response_success():
    """Helper pour asserter une reponse successful"""
    def _assert(response, expected_status=200):
        assert response.status_code == expected_status
        if response.status_code != 204:  # No content
            data = response.json()
            assert data is not None
            return data
    return _assert


@pytest.fixture
def assert_tenant_isolation():
    """Helper pour verifier l'isolation tenant"""
    def _assert(response, tenant_id):
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                for item in data:
                    if "tenant_id" in item:
                        assert item["tenant_id"] == tenant_id
            elif isinstance(data, dict):
                if "items" in data:  # Liste paginee
                    for item in data["items"]:
                        if "tenant_id" in item:
                            assert item["tenant_id"] == tenant_id
                elif "tenant_id" in data:
                    assert data["tenant_id"] == tenant_id
    return _assert
