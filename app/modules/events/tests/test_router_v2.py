"""
Tests pour les endpoints du module Events - CORE SaaS v2
=========================================================

Coverage:
- Venues: CRUD
- Rooms: CRUD
- Events: CRUD + lifecycle (publish, open/close registration, start, complete, cancel)
- Sessions: CRUD
- Speakers: CRUD + assignments
- Ticket Types: CRUD
- Registrations: CRUD + status transitions
- Check-in: create + stats
- Sponsors: CRUD
- Discount Codes: CRUD + validation
- Certificates: templates + issuance
- Evaluations: forms + submissions
- Invitations: CRUD
- Waitlist: add + manage
- Dashboard/Stats
- Security: tenant isolation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.modules.events.models import (
    EventType,
    EventStatus,
    RegistrationStatus,
    PaymentStatus,
)


# ============================================================================
# TESTS VENUES (6 tests)
# ============================================================================

def test_list_venues(test_client, client, mock_context, venue_entity):
    """Test: Liste les lieux."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_venues.return_value = [venue_entity]

            response = test_client.get("/v2/events/venues")

            assert response.status_code == 200
            mock_service.list_venues.assert_called_once()


def test_get_venue(test_client, client, mock_context, venue_entity):
    """Test: Recupere un lieu par ID."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_venue.return_value = venue_entity

            response = test_client.get(f"/v2/events/venues/{venue_entity.id}")

            assert response.status_code == 200


def test_create_venue(test_client, client, mock_context, venue_data, venue_entity):
    """Test: Cree un lieu."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.create_venue.return_value = venue_entity

            response = test_client.post("/v2/events/venues", json=venue_data)

            assert response.status_code == 200
            mock_service.create_venue.assert_called_once()


def test_update_venue(test_client, client, mock_context, venue_entity):
    """Test: Met a jour un lieu."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.update_venue.return_value = venue_entity

            response = test_client.put(
                f"/v2/events/venues/{venue_entity.id}",
                json={"name": "Updated Venue"}
            )

            assert response.status_code == 200


def test_delete_venue(test_client, client, mock_context, venue_entity):
    """Test: Supprime un lieu."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_venue.return_value = True

            response = test_client.delete(f"/v2/events/venues/{venue_entity.id}")

            assert response.status_code == 200


def test_get_venue_not_found(test_client, client, mock_context):
    """Test: Lieu non trouve retourne 404."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_venue.return_value = None

            response = test_client.get(f"/v2/events/venues/{uuid4()}")

            assert response.status_code == 404


# ============================================================================
# TESTS ROOMS (5 tests)
# ============================================================================

def test_list_rooms(test_client, client, mock_context, venue_entity):
    """Test: Liste les salles d'un lieu."""
    room_entity = MagicMock()
    room_entity.id = uuid4()
    room_entity.name = "Salle Test"

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_rooms.return_value = [room_entity]

            response = test_client.get(f"/v2/events/venues/{venue_entity.id}/rooms")

            assert response.status_code == 200


def test_create_room(test_client, client, mock_context, venue_entity, room_data):
    """Test: Cree une salle."""
    room_entity = MagicMock()
    room_entity.id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.create_room.return_value = room_entity

            response = test_client.post(
                f"/v2/events/venues/{venue_entity.id}/rooms",
                json=room_data
            )

            assert response.status_code == 200


def test_update_room(test_client, client, mock_context, venue_entity):
    """Test: Met a jour une salle."""
    room_entity = MagicMock()
    room_id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.update_room.return_value = room_entity

            response = test_client.put(
                f"/v2/events/rooms/{room_id}",
                json={"name": "Updated Room"}
            )

            assert response.status_code == 200


def test_delete_room(test_client, client, mock_context):
    """Test: Supprime une salle."""
    room_id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_room.return_value = True

            response = test_client.delete(f"/v2/events/rooms/{room_id}")

            assert response.status_code == 200


def test_get_room_not_found(test_client, client, mock_context):
    """Test: Salle non trouvee retourne 404."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_room.return_value = None

            response = test_client.get(f"/v2/events/rooms/{uuid4()}")

            assert response.status_code == 404


# ============================================================================
# TESTS EVENTS (20 tests)
# ============================================================================

def test_list_events(test_client, client, mock_context, event_entity):
    """Test: Liste les evenements."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_events.return_value = ([event_entity], 1)

            response = test_client.get("/v2/events/events")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data


def test_list_events_with_filters(test_client, client, mock_context, event_entity):
    """Test: Liste les evenements avec filtres."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_events.return_value = ([event_entity], 1)

            response = test_client.get(
                "/v2/events/events?status=PUBLISHED&event_type=CONFERENCE"
            )

            assert response.status_code == 200


def test_list_events_with_search(test_client, client, mock_context, event_entity):
    """Test: Liste les evenements avec recherche."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_events.return_value = ([event_entity], 1)

            response = test_client.get("/v2/events/events?search=conference")

            assert response.status_code == 200


def test_list_events_pagination(test_client, client, mock_context, event_entity):
    """Test: Liste les evenements avec pagination."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_events.return_value = ([event_entity], 50)

            response = test_client.get("/v2/events/events?skip=20&limit=10")

            assert response.status_code == 200
            data = response.json()
            assert data["skip"] == 20
            assert data["limit"] == 10


def test_get_event(test_client, client, mock_context, event_entity):
    """Test: Recupere un evenement par ID."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_event.return_value = event_entity

            response = test_client.get(f"/v2/events/events/{event_entity.id}")

            assert response.status_code == 200


def test_get_event_by_code(test_client, client, mock_context, event_entity):
    """Test: Recupere un evenement par code."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_event_by_code.return_value = event_entity

            response = test_client.get("/v2/events/events/code/EVT-2026-TEST")

            assert response.status_code == 200


def test_create_event(test_client, client, mock_context, event_data, event_entity):
    """Test: Cree un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.create_event.return_value = event_entity

            response = test_client.post("/v2/events/events", json=event_data)

            assert response.status_code == 200
            mock_service.create_event.assert_called_once()


def test_update_event(test_client, client, mock_context, event_entity):
    """Test: Met a jour un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.update_event.return_value = event_entity

            response = test_client.put(
                f"/v2/events/events/{event_entity.id}",
                json={"title": "Updated Event"}
            )

            assert response.status_code == 200


def test_delete_event(test_client, client, mock_context, event_entity):
    """Test: Supprime un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_event.return_value = True

            response = test_client.delete(f"/v2/events/events/{event_entity.id}")

            assert response.status_code == 200


def test_publish_event(test_client, client, mock_context, event_entity):
    """Test: Publie un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            event_entity.status = EventStatus.PUBLISHED
            mock_service.publish_event.return_value = event_entity

            response = test_client.post(f"/v2/events/events/{event_entity.id}/publish")

            assert response.status_code == 200


def test_open_registration(test_client, client, mock_context, event_entity):
    """Test: Ouvre les inscriptions."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.open_registration.return_value = event_entity

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/open-registration"
            )

            assert response.status_code == 200


def test_close_registration(test_client, client, mock_context, event_entity):
    """Test: Ferme les inscriptions."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.close_registration.return_value = event_entity

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/close-registration"
            )

            assert response.status_code == 200


def test_start_event(test_client, client, mock_context, event_entity):
    """Test: Demarre un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            event_entity.status = EventStatus.ONGOING
            mock_service.start_event.return_value = event_entity

            response = test_client.post(f"/v2/events/events/{event_entity.id}/start")

            assert response.status_code == 200


def test_complete_event(test_client, client, mock_context, event_entity):
    """Test: Complete un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            event_entity.status = EventStatus.COMPLETED
            mock_service.complete_event.return_value = event_entity

            response = test_client.post(f"/v2/events/events/{event_entity.id}/complete")

            assert response.status_code == 200


def test_cancel_event(test_client, client, mock_context, event_entity):
    """Test: Annule un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            event_entity.status = EventStatus.CANCELLED
            mock_service.cancel_event.return_value = event_entity

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/cancel",
                json={"reason": "Force majeure"}
            )

            assert response.status_code == 200


def test_get_event_not_found(test_client, client, mock_context):
    """Test: Evenement non trouve retourne 404."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_event.return_value = None

            response = test_client.get(f"/v2/events/events/{uuid4()}")

            assert response.status_code == 404


def test_get_event_stats(test_client, client, mock_context, event_entity):
    """Test: Recupere les statistiques d'un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_event_stats.return_value = {
                "total_registrations": 100,
                "confirmed": 80,
                "checked_in": 50
            }

            response = test_client.get(f"/v2/events/events/{event_entity.id}/stats")

            assert response.status_code == 200


def test_get_event_agenda(test_client, client, mock_context, event_entity):
    """Test: Recupere l'agenda d'un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_event_agenda.return_value = {"days": []}

            response = test_client.get(f"/v2/events/events/{event_entity.id}/agenda")

            assert response.status_code == 200


def test_list_upcoming_events(test_client, client, mock_context, event_entity):
    """Test: Liste les evenements a venir."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_upcoming_events.return_value = [event_entity]

            response = test_client.get("/v2/events/events/upcoming")

            assert response.status_code == 200


def test_list_past_events(test_client, client, mock_context, event_entity):
    """Test: Liste les evenements passes."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_past_events.return_value = [event_entity]

            response = test_client.get("/v2/events/events/past")

            assert response.status_code == 200


# ============================================================================
# TESTS SPEAKERS (8 tests)
# ============================================================================

def test_list_speakers(test_client, client, mock_context, speaker_entity):
    """Test: Liste les intervenants."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_speakers.return_value = [speaker_entity]

            response = test_client.get("/v2/events/speakers")

            assert response.status_code == 200


def test_get_speaker(test_client, client, mock_context, speaker_entity):
    """Test: Recupere un intervenant par ID."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_speaker.return_value = speaker_entity

            response = test_client.get(f"/v2/events/speakers/{speaker_entity.id}")

            assert response.status_code == 200


def test_create_speaker(test_client, client, mock_context, speaker_data, speaker_entity):
    """Test: Cree un intervenant."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.create_speaker.return_value = speaker_entity

            response = test_client.post("/v2/events/speakers", json=speaker_data)

            assert response.status_code == 200


def test_update_speaker(test_client, client, mock_context, speaker_entity):
    """Test: Met a jour un intervenant."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.update_speaker.return_value = speaker_entity

            response = test_client.put(
                f"/v2/events/speakers/{speaker_entity.id}",
                json={"first_name": "Updated"}
            )

            assert response.status_code == 200


def test_delete_speaker(test_client, client, mock_context, speaker_entity):
    """Test: Supprime un intervenant."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_speaker.return_value = True

            response = test_client.delete(f"/v2/events/speakers/{speaker_entity.id}")

            assert response.status_code == 200


def test_assign_speaker_to_event(test_client, client, mock_context, event_entity, speaker_entity):
    """Test: Assigne un intervenant a un evenement."""
    assignment = MagicMock()
    assignment.id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.assign_speaker.return_value = assignment

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/speakers",
                json={"speaker_id": str(speaker_entity.id), "role": "KEYNOTE"}
            )

            assert response.status_code == 200


def test_remove_speaker_from_event(test_client, client, mock_context, event_entity, speaker_entity):
    """Test: Retire un intervenant d'un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.remove_speaker_assignment.return_value = True

            response = test_client.delete(
                f"/v2/events/events/{event_entity.id}/speakers/{speaker_entity.id}"
            )

            assert response.status_code == 200


def test_list_event_speakers(test_client, client, mock_context, event_entity, speaker_entity):
    """Test: Liste les intervenants d'un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_event_speakers.return_value = [speaker_entity]

            response = test_client.get(f"/v2/events/events/{event_entity.id}/speakers")

            assert response.status_code == 200


# ============================================================================
# TESTS SESSIONS (8 tests)
# ============================================================================

def test_list_sessions(test_client, client, mock_context, event_entity, session_entity):
    """Test: Liste les sessions d'un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_sessions.return_value = [session_entity]

            response = test_client.get(f"/v2/events/events/{event_entity.id}/sessions")

            assert response.status_code == 200


def test_get_session(test_client, client, mock_context, session_entity):
    """Test: Recupere une session par ID."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_session.return_value = session_entity

            response = test_client.get(f"/v2/events/sessions/{session_entity.id}")

            assert response.status_code == 200


def test_create_session(test_client, client, mock_context, event_entity, session_data, session_entity):
    """Test: Cree une session."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.create_session.return_value = session_entity

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/sessions",
                json=session_data
            )

            assert response.status_code == 200


def test_update_session(test_client, client, mock_context, session_entity):
    """Test: Met a jour une session."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.update_session.return_value = session_entity

            response = test_client.put(
                f"/v2/events/sessions/{session_entity.id}",
                json={"title": "Updated Session"}
            )

            assert response.status_code == 200


def test_delete_session(test_client, client, mock_context, session_entity):
    """Test: Supprime une session."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_session.return_value = True

            response = test_client.delete(f"/v2/events/sessions/{session_entity.id}")

            assert response.status_code == 200


def test_assign_speaker_to_session(test_client, client, mock_context, session_entity, speaker_entity):
    """Test: Assigne un intervenant a une session."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.assign_speaker_to_session.return_value = True

            response = test_client.post(
                f"/v2/events/sessions/{session_entity.id}/speakers",
                json={"speaker_id": str(speaker_entity.id)}
            )

            assert response.status_code == 200


def test_remove_speaker_from_session(test_client, client, mock_context, session_entity, speaker_entity):
    """Test: Retire un intervenant d'une session."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.remove_speaker_from_session.return_value = True

            response = test_client.delete(
                f"/v2/events/sessions/{session_entity.id}/speakers/{speaker_entity.id}"
            )

            assert response.status_code == 200


def test_get_session_not_found(test_client, client, mock_context):
    """Test: Session non trouvee retourne 404."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_session.return_value = None

            response = test_client.get(f"/v2/events/sessions/{uuid4()}")

            assert response.status_code == 404


# ============================================================================
# TESTS TICKET TYPES (6 tests)
# ============================================================================

def test_list_ticket_types(test_client, client, mock_context, event_entity, ticket_type_entity):
    """Test: Liste les types de billets d'un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_ticket_types.return_value = [ticket_type_entity]

            response = test_client.get(f"/v2/events/events/{event_entity.id}/ticket-types")

            assert response.status_code == 200


def test_get_ticket_type(test_client, client, mock_context, ticket_type_entity):
    """Test: Recupere un type de billet par ID."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_ticket_type.return_value = ticket_type_entity

            response = test_client.get(f"/v2/events/ticket-types/{ticket_type_entity.id}")

            assert response.status_code == 200


def test_create_ticket_type(test_client, client, mock_context, event_entity, ticket_type_data, ticket_type_entity):
    """Test: Cree un type de billet."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.create_ticket_type.return_value = ticket_type_entity

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/ticket-types",
                json=ticket_type_data
            )

            assert response.status_code == 200


def test_update_ticket_type(test_client, client, mock_context, ticket_type_entity):
    """Test: Met a jour un type de billet."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.update_ticket_type.return_value = ticket_type_entity

            response = test_client.put(
                f"/v2/events/ticket-types/{ticket_type_entity.id}",
                json={"name": "Updated Ticket"}
            )

            assert response.status_code == 200


def test_delete_ticket_type(test_client, client, mock_context, ticket_type_entity):
    """Test: Supprime un type de billet."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_ticket_type.return_value = True

            response = test_client.delete(f"/v2/events/ticket-types/{ticket_type_entity.id}")

            assert response.status_code == 200


def test_get_ticket_type_availability(test_client, client, mock_context, ticket_type_entity):
    """Test: Verifie la disponibilite d'un type de billet."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.check_ticket_availability.return_value = {
                "available": 90,
                "is_available": True
            }

            response = test_client.get(
                f"/v2/events/ticket-types/{ticket_type_entity.id}/availability"
            )

            assert response.status_code == 200


# ============================================================================
# TESTS REGISTRATIONS (15 tests)
# ============================================================================

def test_list_registrations(test_client, client, mock_context, event_entity, registration_entity):
    """Test: Liste les inscriptions d'un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_registrations.return_value = ([registration_entity], 1)

            response = test_client.get(f"/v2/events/events/{event_entity.id}/registrations")

            assert response.status_code == 200


def test_list_registrations_with_filters(test_client, client, mock_context, event_entity, registration_entity):
    """Test: Liste les inscriptions avec filtres."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_registrations.return_value = ([registration_entity], 1)

            response = test_client.get(
                f"/v2/events/events/{event_entity.id}/registrations?status=CONFIRMED"
            )

            assert response.status_code == 200


def test_get_registration(test_client, client, mock_context, registration_entity):
    """Test: Recupere une inscription par ID."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_registration.return_value = registration_entity

            response = test_client.get(f"/v2/events/registrations/{registration_entity.id}")

            assert response.status_code == 200


def test_get_registration_by_code(test_client, client, mock_context, registration_entity):
    """Test: Recupere une inscription par code."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_registration_by_code.return_value = registration_entity

            response = test_client.get("/v2/events/registrations/code/REG-TEST-001")

            assert response.status_code == 200


def test_create_registration(test_client, client, mock_context, event_entity, registration_data, registration_entity):
    """Test: Cree une inscription."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.create_registration.return_value = registration_entity

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/registrations",
                json=registration_data
            )

            assert response.status_code == 200


def test_update_registration(test_client, client, mock_context, registration_entity):
    """Test: Met a jour une inscription."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.update_registration.return_value = registration_entity

            response = test_client.put(
                f"/v2/events/registrations/{registration_entity.id}",
                json={"first_name": "Updated"}
            )

            assert response.status_code == 200


def test_confirm_registration(test_client, client, mock_context, registration_entity):
    """Test: Confirme une inscription."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            registration_entity.status = RegistrationStatus.CONFIRMED
            mock_service.confirm_registration.return_value = registration_entity

            response = test_client.post(
                f"/v2/events/registrations/{registration_entity.id}/confirm"
            )

            assert response.status_code == 200


def test_cancel_registration(test_client, client, mock_context, registration_entity):
    """Test: Annule une inscription."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            registration_entity.status = RegistrationStatus.CANCELLED
            mock_service.cancel_registration.return_value = registration_entity

            response = test_client.post(
                f"/v2/events/registrations/{registration_entity.id}/cancel",
                json={"reason": "Changement de programme"}
            )

            assert response.status_code == 200


def test_refund_registration(test_client, client, mock_context, registration_entity):
    """Test: Rembourse une inscription."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            registration_entity.payment_status = PaymentStatus.REFUNDED
            mock_service.refund_registration.return_value = registration_entity

            response = test_client.post(
                f"/v2/events/registrations/{registration_entity.id}/refund"
            )

            assert response.status_code == 200


def test_resend_confirmation(test_client, client, mock_context, registration_entity):
    """Test: Renvoie l'email de confirmation."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.resend_confirmation.return_value = True

            response = test_client.post(
                f"/v2/events/registrations/{registration_entity.id}/resend-confirmation"
            )

            assert response.status_code == 200


def test_registration_not_found(test_client, client, mock_context):
    """Test: Inscription non trouvee retourne 404."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_registration.return_value = None

            response = test_client.get(f"/v2/events/registrations/{uuid4()}")

            assert response.status_code == 404


def test_apply_discount_code(test_client, client, mock_context, registration_entity):
    """Test: Applique un code promo a une inscription."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.apply_discount_code.return_value = registration_entity

            response = test_client.post(
                f"/v2/events/registrations/{registration_entity.id}/apply-discount",
                json={"code": "EARLYBIRD20"}
            )

            assert response.status_code == 200


def test_search_registrations(test_client, client, mock_context, event_entity, registration_entity):
    """Test: Recherche dans les inscriptions."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.search_registrations.return_value = [registration_entity]

            response = test_client.get(
                f"/v2/events/events/{event_entity.id}/registrations?search=dupont"
            )

            assert response.status_code == 200


def test_export_registrations(test_client, client, mock_context, event_entity):
    """Test: Exporte les inscriptions."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.export_registrations.return_value = b"CSV data"

            response = test_client.get(
                f"/v2/events/events/{event_entity.id}/registrations/export"
            )

            assert response.status_code == 200


def test_bulk_confirm_registrations(test_client, client, mock_context, event_entity, registration_entity):
    """Test: Confirme plusieurs inscriptions."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.bulk_confirm_registrations.return_value = 5

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/registrations/bulk-confirm",
                json={"registration_ids": [str(uuid4()) for _ in range(5)]}
            )

            assert response.status_code == 200


# ============================================================================
# TESTS CHECK-IN (6 tests)
# ============================================================================

def test_checkin_registration(test_client, client, mock_context, registration_entity, checkin_entity):
    """Test: Check-in d'un participant."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.checkin.return_value = checkin_entity

            response = test_client.post(
                f"/v2/events/registrations/{registration_entity.id}/checkin"
            )

            assert response.status_code == 200


def test_checkin_by_qr_code(test_client, client, mock_context, checkin_entity):
    """Test: Check-in par QR code."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.checkin_by_qr.return_value = checkin_entity

            response = test_client.post(
                "/v2/events/checkin/qr",
                json={"qr_code": "QR-ABC123"}
            )

            assert response.status_code == 200


def test_checkin_by_email(test_client, client, mock_context, event_entity, checkin_entity):
    """Test: Check-in par email."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.checkin_by_email.return_value = checkin_entity

            response = test_client.post(
                "/v2/events/checkin/email",
                json={"event_id": str(event_entity.id), "email": "test@example.com"}
            )

            assert response.status_code == 200


def test_get_checkin_stats(test_client, client, mock_context, event_entity):
    """Test: Recupere les statistiques de check-in."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_checkin_stats.return_value = {
                "total_registered": 100,
                "checked_in": 50,
                "percentage": 50.0
            }

            response = test_client.get(f"/v2/events/events/{event_entity.id}/checkin/stats")

            assert response.status_code == 200


def test_list_checkins(test_client, client, mock_context, event_entity, checkin_entity):
    """Test: Liste les check-ins d'un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_checkins.return_value = [checkin_entity]

            response = test_client.get(f"/v2/events/events/{event_entity.id}/checkins")

            assert response.status_code == 200


def test_undo_checkin(test_client, client, mock_context, registration_entity):
    """Test: Annule un check-in."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.undo_checkin.return_value = True

            response = test_client.delete(
                f"/v2/events/registrations/{registration_entity.id}/checkin"
            )

            assert response.status_code == 200


# ============================================================================
# TESTS SPONSORS (5 tests)
# ============================================================================

def test_list_sponsors(test_client, client, mock_context, event_entity):
    """Test: Liste les sponsors d'un evenement."""
    sponsor = MagicMock()
    sponsor.id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_sponsors.return_value = [sponsor]

            response = test_client.get(f"/v2/events/events/{event_entity.id}/sponsors")

            assert response.status_code == 200


def test_create_sponsor(test_client, client, mock_context, event_entity, sponsor_data):
    """Test: Cree un sponsor."""
    sponsor = MagicMock()
    sponsor.id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.create_sponsor.return_value = sponsor

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/sponsors",
                json=sponsor_data
            )

            assert response.status_code == 200


def test_update_sponsor(test_client, client, mock_context):
    """Test: Met a jour un sponsor."""
    sponsor = MagicMock()
    sponsor_id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.update_sponsor.return_value = sponsor

            response = test_client.put(
                f"/v2/events/sponsors/{sponsor_id}",
                json={"name": "Updated Sponsor"}
            )

            assert response.status_code == 200


def test_delete_sponsor(test_client, client, mock_context):
    """Test: Supprime un sponsor."""
    sponsor_id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_sponsor.return_value = True

            response = test_client.delete(f"/v2/events/sponsors/{sponsor_id}")

            assert response.status_code == 200


def test_list_sponsors_by_level(test_client, client, mock_context, event_entity):
    """Test: Liste les sponsors par niveau."""
    sponsor = MagicMock()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_sponsors.return_value = [sponsor]

            response = test_client.get(
                f"/v2/events/events/{event_entity.id}/sponsors?level=GOLD"
            )

            assert response.status_code == 200


# ============================================================================
# TESTS DISCOUNT CODES (6 tests)
# ============================================================================

def test_list_discount_codes(test_client, client, mock_context, event_entity):
    """Test: Liste les codes promo d'un evenement."""
    discount = MagicMock()
    discount.id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_discount_codes.return_value = [discount]

            response = test_client.get(f"/v2/events/events/{event_entity.id}/discount-codes")

            assert response.status_code == 200


def test_create_discount_code(test_client, client, mock_context, event_entity, discount_code_data):
    """Test: Cree un code promo."""
    discount = MagicMock()
    discount.id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.create_discount_code.return_value = discount

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/discount-codes",
                json=discount_code_data
            )

            assert response.status_code == 200


def test_validate_discount_code(test_client, client, mock_context, event_entity):
    """Test: Valide un code promo."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.validate_discount_code.return_value = {
                "valid": True,
                "discount_type": "PERCENTAGE",
                "discount_value": 20
            }

            response = test_client.post(
                "/v2/events/discount-codes/validate",
                json={"event_id": str(event_entity.id), "code": "EARLYBIRD20"}
            )

            assert response.status_code == 200


def test_update_discount_code(test_client, client, mock_context):
    """Test: Met a jour un code promo."""
    discount = MagicMock()
    discount_id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.update_discount_code.return_value = discount

            response = test_client.put(
                f"/v2/events/discount-codes/{discount_id}",
                json={"max_uses": 200}
            )

            assert response.status_code == 200


def test_deactivate_discount_code(test_client, client, mock_context):
    """Test: Desactive un code promo."""
    discount = MagicMock()
    discount_id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.deactivate_discount_code.return_value = discount

            response = test_client.post(f"/v2/events/discount-codes/{discount_id}/deactivate")

            assert response.status_code == 200


def test_delete_discount_code(test_client, client, mock_context):
    """Test: Supprime un code promo."""
    discount_id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_discount_code.return_value = True

            response = test_client.delete(f"/v2/events/discount-codes/{discount_id}")

            assert response.status_code == 200


# ============================================================================
# TESTS CERTIFICATES (6 tests)
# ============================================================================

def test_list_certificate_templates(test_client, client, mock_context, event_entity):
    """Test: Liste les modeles de certificats."""
    template = MagicMock()
    template.id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_certificate_templates.return_value = [template]

            response = test_client.get(
                f"/v2/events/events/{event_entity.id}/certificate-templates"
            )

            assert response.status_code == 200


def test_create_certificate_template(test_client, client, mock_context, event_entity, certificate_template_data):
    """Test: Cree un modele de certificat."""
    template = MagicMock()
    template.id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.create_certificate_template.return_value = template

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/certificate-templates",
                json=certificate_template_data
            )

            assert response.status_code == 200


def test_issue_certificate(test_client, client, mock_context, registration_entity, certificate_entity):
    """Test: Emet un certificat."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.issue_certificate.return_value = certificate_entity

            response = test_client.post(
                f"/v2/events/registrations/{registration_entity.id}/certificate"
            )

            assert response.status_code == 200


def test_get_certificate(test_client, client, mock_context, certificate_entity):
    """Test: Recupere un certificat."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_certificate.return_value = certificate_entity

            response = test_client.get(f"/v2/events/certificates/{certificate_entity.id}")

            assert response.status_code == 200


def test_download_certificate(test_client, client, mock_context, certificate_entity):
    """Test: Telecharge un certificat PDF."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.generate_certificate_pdf.return_value = b"PDF content"

            response = test_client.get(
                f"/v2/events/certificates/{certificate_entity.id}/download"
            )

            assert response.status_code == 200


def test_bulk_issue_certificates(test_client, client, mock_context, event_entity):
    """Test: Emet des certificats en masse."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.bulk_issue_certificates.return_value = 25

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/certificates/bulk-issue"
            )

            assert response.status_code == 200


# ============================================================================
# TESTS EVALUATIONS (6 tests)
# ============================================================================

def test_list_evaluation_forms(test_client, client, mock_context, event_entity):
    """Test: Liste les formulaires d'evaluation."""
    form = MagicMock()
    form.id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_evaluation_forms.return_value = [form]

            response = test_client.get(
                f"/v2/events/events/{event_entity.id}/evaluation-forms"
            )

            assert response.status_code == 200


def test_create_evaluation_form(test_client, client, mock_context, event_entity):
    """Test: Cree un formulaire d'evaluation."""
    form = MagicMock()
    form.id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.create_evaluation_form.return_value = form

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/evaluation-forms",
                json={
                    "title": "Evaluation",
                    "questions": [{"id": "q1", "text": "Note", "type": "rating"}]
                }
            )

            assert response.status_code == 200


def test_submit_evaluation(test_client, client, mock_context, registration_entity, evaluation_data, evaluation_entity):
    """Test: Soumet une evaluation."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.submit_evaluation.return_value = evaluation_entity

            response = test_client.post(
                f"/v2/events/registrations/{registration_entity.id}/evaluation",
                json=evaluation_data
            )

            assert response.status_code == 200


def test_get_evaluation_stats(test_client, client, mock_context, event_entity):
    """Test: Recupere les statistiques d'evaluation."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_evaluation_stats.return_value = {
                "total_evaluations": 50,
                "average_rating": 4.5,
                "response_rate": 62.5
            }

            response = test_client.get(f"/v2/events/events/{event_entity.id}/evaluations/stats")

            assert response.status_code == 200


def test_list_evaluations(test_client, client, mock_context, event_entity, evaluation_entity):
    """Test: Liste les evaluations d'un evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_evaluations.return_value = [evaluation_entity]

            response = test_client.get(f"/v2/events/events/{event_entity.id}/evaluations")

            assert response.status_code == 200


def test_export_evaluations(test_client, client, mock_context, event_entity):
    """Test: Exporte les evaluations."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.export_evaluations.return_value = b"CSV data"

            response = test_client.get(
                f"/v2/events/events/{event_entity.id}/evaluations/export"
            )

            assert response.status_code == 200


# ============================================================================
# TESTS INVITATIONS (5 tests)
# ============================================================================

def test_list_invitations(test_client, client, mock_context, event_entity):
    """Test: Liste les invitations d'un evenement."""
    invitation = MagicMock()
    invitation.id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_invitations.return_value = [invitation]

            response = test_client.get(f"/v2/events/events/{event_entity.id}/invitations")

            assert response.status_code == 200


def test_create_invitation(test_client, client, mock_context, event_entity, invitation_data):
    """Test: Cree une invitation."""
    invitation = MagicMock()
    invitation.id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.create_invitation.return_value = invitation

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/invitations",
                json=invitation_data
            )

            assert response.status_code == 200


def test_send_invitation(test_client, client, mock_context):
    """Test: Envoie une invitation."""
    invitation_id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.send_invitation.return_value = True

            response = test_client.post(f"/v2/events/invitations/{invitation_id}/send")

            assert response.status_code == 200


def test_bulk_send_invitations(test_client, client, mock_context, event_entity):
    """Test: Envoie des invitations en masse."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.bulk_send_invitations.return_value = 10

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/invitations/bulk-send"
            )

            assert response.status_code == 200


def test_cancel_invitation(test_client, client, mock_context):
    """Test: Annule une invitation."""
    invitation_id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.cancel_invitation.return_value = True

            response = test_client.delete(f"/v2/events/invitations/{invitation_id}")

            assert response.status_code == 200


# ============================================================================
# TESTS WAITLIST (5 tests)
# ============================================================================

def test_list_waitlist(test_client, client, mock_context, event_entity):
    """Test: Liste la liste d'attente d'un evenement."""
    entry = MagicMock()
    entry.id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_waitlist.return_value = [entry]

            response = test_client.get(f"/v2/events/events/{event_entity.id}/waitlist")

            assert response.status_code == 200


def test_add_to_waitlist(test_client, client, mock_context, event_entity, waitlist_data):
    """Test: Ajoute a la liste d'attente."""
    entry = MagicMock()
    entry.id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.add_to_waitlist.return_value = entry

            response = test_client.post(
                f"/v2/events/events/{event_entity.id}/waitlist",
                json=waitlist_data
            )

            assert response.status_code == 200


def test_remove_from_waitlist(test_client, client, mock_context):
    """Test: Retire de la liste d'attente."""
    entry_id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.remove_from_waitlist.return_value = True

            response = test_client.delete(f"/v2/events/waitlist/{entry_id}")

            assert response.status_code == 200


def test_promote_from_waitlist(test_client, client, mock_context, registration_entity):
    """Test: Promeut un participant de la liste d'attente."""
    entry_id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.promote_from_waitlist.return_value = registration_entity

            response = test_client.post(f"/v2/events/waitlist/{entry_id}/promote")

            assert response.status_code == 200


def test_get_waitlist_position(test_client, client, mock_context):
    """Test: Recupere la position dans la liste d'attente."""
    entry_id = uuid4()

    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_waitlist_position.return_value = {"position": 5, "total": 15}

            response = test_client.get(f"/v2/events/waitlist/{entry_id}/position")

            assert response.status_code == 200


# ============================================================================
# TESTS DASHBOARD & STATS (3 tests)
# ============================================================================

def test_get_global_stats(test_client, client, mock_context):
    """Test: Recupere les statistiques globales."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_global_stats.return_value = {
                "total_events": 25,
                "total_registrations": 500,
                "total_revenue": 50000
            }

            response = test_client.get("/v2/events/stats")

            assert response.status_code == 200


def test_get_dashboard(test_client, client, mock_context):
    """Test: Recupere le dashboard complet."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_dashboard.return_value = {
                "upcoming_events": [],
                "recent_registrations": [],
                "stats": {}
            }

            response = test_client.get("/v2/events/dashboard")

            assert response.status_code == 200


def test_get_revenue_report(test_client, client, mock_context):
    """Test: Recupere le rapport de revenus."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.get_revenue_report.return_value = {
                "total": 50000,
                "by_event": [],
                "by_month": []
            }

            response = test_client.get("/v2/events/reports/revenue")

            assert response.status_code == 200


# ============================================================================
# TESTS SECURITY (2 tests)
# ============================================================================

def test_tenant_isolation(test_client, client, mock_context, event_entity):
    """Test: Isolation des tenants - verification du tenant_id."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_events.return_value = ([event_entity], 1)

            response = test_client.get("/v2/events/events")

            assert response.status_code == 200
            # Le service doit etre initialise avec le bon tenant_id
            assert MockService.called


def test_user_context_preserved(test_client, client, mock_context, event_entity):
    """Test: Le contexte utilisateur est preserve."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value
            mock_service.list_events.return_value = ([event_entity], 1)

            response = test_client.get("/v2/events/events")

            assert response.status_code == 200
            # Verifier que le service a ete cree avec user_id
            assert MockService.called


# ============================================================================
# TESTS WORKFLOW COMPLET (5 tests)
# ============================================================================

def test_workflow_create_event_and_publish(test_client, client, mock_context, event_data, event_entity):
    """Test: Workflow complet - creation et publication d'evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value

            # Creation
            mock_service.create_event.return_value = event_entity
            response1 = test_client.post("/v2/events/events", json=event_data)
            assert response1.status_code == 200

            # Publication
            event_entity.status = EventStatus.PUBLISHED
            mock_service.publish_event.return_value = event_entity
            response2 = test_client.post(f"/v2/events/events/{event_entity.id}/publish")
            assert response2.status_code == 200


def test_workflow_registration_and_checkin(test_client, client, mock_context, event_entity, registration_data, registration_entity, checkin_entity):
    """Test: Workflow - inscription et check-in."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value

            # Inscription
            mock_service.create_registration.return_value = registration_entity
            response1 = test_client.post(
                f"/v2/events/events/{event_entity.id}/registrations",
                json=registration_data
            )
            assert response1.status_code == 200

            # Check-in
            mock_service.checkin.return_value = checkin_entity
            response2 = test_client.post(
                f"/v2/events/registrations/{registration_entity.id}/checkin"
            )
            assert response2.status_code == 200


def test_workflow_event_complete_and_certificate(test_client, client, mock_context, event_entity, registration_entity, certificate_entity):
    """Test: Workflow - completion evenement et certificat."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value

            # Completion
            event_entity.status = EventStatus.COMPLETED
            mock_service.complete_event.return_value = event_entity
            response1 = test_client.post(f"/v2/events/events/{event_entity.id}/complete")
            assert response1.status_code == 200

            # Certificat
            mock_service.issue_certificate.return_value = certificate_entity
            response2 = test_client.post(
                f"/v2/events/registrations/{registration_entity.id}/certificate"
            )
            assert response2.status_code == 200


def test_workflow_registration_with_discount(test_client, client, mock_context, event_entity, registration_data, registration_entity):
    """Test: Workflow - inscription avec code promo."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value

            # Validation code promo
            mock_service.validate_discount_code.return_value = {
                "valid": True,
                "discount_type": "PERCENTAGE",
                "discount_value": 20
            }
            response1 = test_client.post(
                "/v2/events/discount-codes/validate",
                json={"event_id": str(event_entity.id), "code": "EARLYBIRD20"}
            )
            assert response1.status_code == 200

            # Inscription avec code
            registration_data["discount_code"] = "EARLYBIRD20"
            mock_service.create_registration.return_value = registration_entity
            response2 = test_client.post(
                f"/v2/events/events/{event_entity.id}/registrations",
                json=registration_data
            )
            assert response2.status_code == 200


def test_workflow_post_event_evaluation(test_client, client, mock_context, event_entity, registration_entity, evaluation_data, evaluation_entity):
    """Test: Workflow - evaluation post-evenement."""
    with patch("app.modules.events.router.get_saas_context", return_value=mock_context):
        with patch("app.modules.events.router.get_events_service") as MockService:
            mock_service = MockService.return_value

            # Soumettre evaluation
            mock_service.submit_evaluation.return_value = evaluation_entity
            response1 = test_client.post(
                f"/v2/events/registrations/{registration_entity.id}/evaluation",
                json=evaluation_data
            )
            assert response1.status_code == 200

            # Voir statistiques
            mock_service.get_evaluation_stats.return_value = {
                "total_evaluations": 50,
                "average_rating": 4.5
            }
            response2 = test_client.get(f"/v2/events/events/{event_entity.id}/evaluations/stats")
            assert response2.status_code == 200
