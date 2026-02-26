"""
Fixtures pour les tests du module Appointments.

Utilise les fixtures globales de app/conftest.py.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta, date, time


@pytest.fixture(scope="function")
def tenant_a_id() -> str:
    """ID du tenant A pour les tests."""
    return f"tenant-a-{uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def tenant_b_id() -> str:
    """ID du tenant B pour les tests d'isolation."""
    return f"tenant-b-{uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def user_id() -> str:
    """ID d'utilisateur pour les tests."""
    return str(uuid4())


@pytest.fixture(scope="function")
def employee_id() -> str:
    """ID d'employe pour les tests."""
    return str(uuid4())


@pytest.fixture(scope="function")
def appointment_type_data() -> dict:
    """Donnees pour creer un type de rendez-vous."""
    return {
        "code": f"TYPE-{uuid4().hex[:8]}",
        "name": "Consultation Standard",
        "description": "Consultation de 30 minutes",
        "category": "Commercial",
        "default_duration_minutes": 30,
        "buffer_before_minutes": 5,
        "buffer_after_minutes": 5,
        "default_mode": "IN_PERSON",
        "booking_mode": "INSTANT",
        "min_notice_hours": 24,
        "max_advance_days": 60,
        "is_active": True,
        "is_public": True,
    }


@pytest.fixture(scope="function")
def resource_data() -> dict:
    """Donnees pour creer une ressource."""
    return {
        "code": f"RES-{uuid4().hex[:8]}",
        "name": "Salle de reunion A",
        "description": "Grande salle avec projecteur",
        "resource_type": "ROOM",
        "capacity": 10,
        "location": "Batiment A, Etage 2",
        "amenities": ["projector", "whiteboard", "video_conf"],
        "is_available": True,
        "is_active": True,
    }


@pytest.fixture(scope="function")
def appointment_data() -> dict:
    """Donnees pour creer un rendez-vous."""
    start = datetime.utcnow() + timedelta(days=7, hours=10)
    return {
        "code": f"RDV-{uuid4().hex[:8]}",
        "title": "Reunion commerciale",
        "description": "Presentation du produit",
        "mode": "IN_PERSON",
        "priority": "NORMAL",
        "start_datetime": start,
        "end_datetime": start + timedelta(hours=1),
        "duration_minutes": 60,
        "contact_name": "Jean Dupont",
        "contact_email": "jean.dupont@example.com",
        "contact_phone": "+33612345678",
        "location": "Bureau Paris",
    }


@pytest.fixture(scope="function")
def attendee_data() -> dict:
    """Donnees pour creer un participant."""
    return {
        "name": "Marie Martin",
        "email": "marie.martin@example.com",
        "phone": "+33698765432",
        "role": "REQUIRED",
    }


@pytest.fixture(scope="function")
def reminder_data() -> dict:
    """Donnees pour creer un rappel."""
    return {
        "reminder_type": "EMAIL",
        "minutes_before": 1440,  # 24h
        "recipient_type": "attendee",
        "subject": "Rappel: Votre rendez-vous demain",
        "message": "N'oubliez pas votre rendez-vous demain.",
    }


@pytest.fixture(scope="function")
def availability_data() -> dict:
    """Donnees pour creer une disponibilite."""
    return {
        "availability_type": "BLOCKED",
        "date_start": date.today() + timedelta(days=14),
        "date_end": date.today() + timedelta(days=14),
        "time_start": time(9, 0),
        "time_end": time(12, 0),
        "reason": "Reunion equipe",
    }


@pytest.fixture(scope="function")
def working_hours_data() -> dict:
    """Donnees pour creer des horaires de travail."""
    return {
        "day_of_week": 0,  # Lundi
        "is_working": True,
        "start_time": time(9, 0),
        "end_time": time(18, 0),
        "breaks": [
            {"start": "12:00", "end": "13:00"}
        ],
    }


@pytest.fixture(scope="function")
def waitlist_data() -> dict:
    """Donnees pour creer une entree de liste d'attente."""
    return {
        "contact_name": "Pierre Durand",
        "contact_email": "pierre.durand@example.com",
        "contact_phone": "+33611223344",
        "preferred_times": ["morning", "afternoon"],
        "notes": "Prefere les creneaux en debut de semaine",
    }


# ============================================================================
# FIXTURES AVEC DB (si disponible)
# ============================================================================

@pytest.fixture(scope="function")
def appointment_type_tenant_a(db_session, tenant_a_id, user_id, appointment_type_data):
    """Cree un type de rendez-vous pour le tenant A."""
    from app.modules.appointments.models import AppointmentType
    from uuid import uuid4

    apt_type = AppointmentType(
        id=uuid4(),
        tenant_id=tenant_a_id,
        created_by=user_id,
        **appointment_type_data
    )
    db_session.add(apt_type)
    db_session.commit()
    db_session.refresh(apt_type)
    return apt_type


@pytest.fixture(scope="function")
def appointment_type_tenant_b(db_session, tenant_b_id, user_id, appointment_type_data):
    """Cree un type de rendez-vous pour le tenant B."""
    from app.modules.appointments.models import AppointmentType
    from uuid import uuid4

    appointment_type_data["code"] = f"TYPE-B-{uuid4().hex[:8]}"
    apt_type = AppointmentType(
        id=uuid4(),
        tenant_id=tenant_b_id,
        created_by=user_id,
        **appointment_type_data
    )
    db_session.add(apt_type)
    db_session.commit()
    db_session.refresh(apt_type)
    return apt_type


@pytest.fixture(scope="function")
def resource_tenant_a(db_session, tenant_a_id, user_id, resource_data):
    """Cree une ressource pour le tenant A."""
    from app.modules.appointments.models import Resource
    from uuid import uuid4

    resource = Resource(
        id=uuid4(),
        tenant_id=tenant_a_id,
        created_by=user_id,
        **resource_data
    )
    db_session.add(resource)
    db_session.commit()
    db_session.refresh(resource)
    return resource


@pytest.fixture(scope="function")
def resource_tenant_b(db_session, tenant_b_id, user_id, resource_data):
    """Cree une ressource pour le tenant B."""
    from app.modules.appointments.models import Resource
    from uuid import uuid4

    resource_data["code"] = f"RES-B-{uuid4().hex[:8]}"
    resource = Resource(
        id=uuid4(),
        tenant_id=tenant_b_id,
        created_by=user_id,
        **resource_data
    )
    db_session.add(resource)
    db_session.commit()
    db_session.refresh(resource)
    return resource


@pytest.fixture(scope="function")
def appointment_tenant_a(db_session, tenant_a_id, user_id, appointment_data):
    """Cree un rendez-vous pour le tenant A."""
    from app.modules.appointments.models import Appointment, AppointmentStatus
    from uuid import uuid4

    appointment = Appointment(
        id=uuid4(),
        tenant_id=tenant_a_id,
        status=AppointmentStatus.CONFIRMED,
        confirmation_code="CONF1234",
        created_by=user_id,
        organizer_id=user_id,
        **appointment_data
    )
    db_session.add(appointment)
    db_session.commit()
    db_session.refresh(appointment)
    return appointment


@pytest.fixture(scope="function")
def appointment_tenant_b(db_session, tenant_b_id, user_id, appointment_data):
    """Cree un rendez-vous pour le tenant B."""
    from app.modules.appointments.models import Appointment, AppointmentStatus
    from uuid import uuid4

    appointment_data["code"] = f"RDV-B-{uuid4().hex[:8]}"
    appointment = Appointment(
        id=uuid4(),
        tenant_id=tenant_b_id,
        status=AppointmentStatus.CONFIRMED,
        confirmation_code="CONF5678",
        created_by=user_id,
        organizer_id=user_id,
        **appointment_data
    )
    db_session.add(appointment)
    db_session.commit()
    db_session.refresh(appointment)
    return appointment
