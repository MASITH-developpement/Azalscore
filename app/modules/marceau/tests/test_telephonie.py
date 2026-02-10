"""
Tests pour le service telephonie Marceau.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.marceau.modules.telephonie.service import TelephonyService
from app.modules.marceau.models import MarceauConversation, MarceauAction


class TestTelephonyService:
    """Tests du service telephonie."""

    @pytest.fixture
    def mock_db(self):
        """Mock de la session DB."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.count.return_value = 0
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Instance du service avec mocks."""
        return TelephonyService("tenant-test", mock_db)

    @pytest.mark.asyncio
    async def test_handle_incoming_call(self, service, mock_db):
        """Test de la gestion d'un appel entrant."""
        # Configuration mock
        service.config = MagicMock()
        service.config.telephony_config = {"working_hours": {"start": "09:00", "end": "18:00"}}

        data = {
            "caller_phone": "+33612345678",
            "caller_name": "Jean Dupont",
            "asterisk_call_id": "1234567890.1",
        }

        result = await service._handle_incoming_call(data, [])

        assert result["success"] is True
        assert "conversation_id" in result
        assert "greeting" in result
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_quote_missing_fields(self, service):
        """Test creation devis avec champs manquants."""
        service.config = MagicMock()

        data = {
            "customer_name": "Jean Dupont",
            # phone et description manquants
        }

        result = await service._create_quote_from_call(data, [])

        assert result["success"] is False
        assert "missing_fields" in result
        assert "phone" in result["missing_fields"]
        assert "description" in result["missing_fields"]

    @pytest.mark.asyncio
    async def test_schedule_appointment_no_zone(self, service, mock_db):
        """Test planification RDV sans zone de service."""
        service.config = MagicMock()
        service.config.integrations = {}

        # Mock geocodage retourne des coords
        with patch.object(service, '_geocode_address', new_callable=AsyncMock) as mock_geo:
            mock_geo.return_value = {"lat": 48.8566, "lng": 2.3522}

            # Mock zone retourne None (pas de zone)
            with patch.object(service, '_find_service_zone', new_callable=AsyncMock) as mock_zone:
                mock_zone.return_value = None

                data = {
                    "address": "123 Rue de Paris, 75001",
                    "description": "Reparation urgente",
                }

                result = await service._schedule_appointment(data, [])

                assert result["success"] is False
                assert "n'intervenons pas" in result["error"]

    @pytest.mark.asyncio
    async def test_transfer_call(self, service, mock_db):
        """Test transfert d'appel."""
        conversation_id = str(uuid.uuid4())

        # Mock conversation existante
        mock_conv = MagicMock(spec=MarceauConversation)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_conv

        data = {
            "target": "+33612345678",
            "reason": "Demande technique",
            "conversation_id": conversation_id,
        }

        result = await service._transfer_call(data, [])

        assert result["success"] is True
        assert result["transferred_to"] == "+33612345678"

    @pytest.mark.asyncio
    async def test_end_call(self, service, mock_db):
        """Test fin d'appel."""
        conversation_id = str(uuid.uuid4())

        # Mock conversation existante
        mock_conv = MagicMock(spec=MarceauConversation)
        mock_conv.started_at = datetime.utcnow()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_conv

        # Mock config
        service.config = MagicMock()
        service.config.total_conversations = 0

        with patch(
            'app.modules.marceau.modules.telephonie.service.get_or_create_marceau_config'
        ) as mock_config:
            mock_config.return_value = service.config

            data = {
                "conversation_id": conversation_id,
                "outcome": "information_provided",
                "transcript": "Test transcript",
            }

            result = await service._end_call(data, [])

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_generate_greeting_with_customer(self, service):
        """Test generation message d'accueil avec client connu."""
        customer = {"name": "Jean Dupont", "id": str(uuid.uuid4())}

        greeting = await service._generate_greeting("Jean", customer)

        assert "Jean Dupont" in greeting
        assert "bienvenue" in greeting.lower()

    @pytest.mark.asyncio
    async def test_generate_greeting_without_customer(self, service):
        """Test generation message d'accueil sans client."""
        greeting = await service._generate_greeting(None, None)

        assert "bienvenue" in greeting.lower()
        assert "comment" in greeting.lower()
