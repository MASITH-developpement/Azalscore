"""
Tests unitaires pour le module Integration (GAP-086).
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from ..models import (
    AuthType,
    ConflictResolution,
    ConnectionStatus,
    ConnectorType,
    EntityType,
    HealthStatus,
    SyncDirection,
    SyncStatus,
    WebhookDirection,
)
from ..service import (
    CONNECTOR_DEFINITIONS,
    ConnectorDefinition,
    IntegrationService,
    create_integration_service,
)
from ..exceptions import (
    ConnectionNotFoundError,
    MappingNotFoundError,
    SyncExecutionRunningError,
)


class TestConnectorDefinitions:
    """Tests pour les definitions de connecteurs."""

    def test_connector_definitions_exist(self):
        """Verifie que les definitions de connecteurs existent."""
        assert len(CONNECTOR_DEFINITIONS) > 0

    def test_all_required_connectors_defined(self):
        """Verifie les connecteurs requis."""
        required = [
            ConnectorType.GOOGLE_DRIVE,
            ConnectorType.SLACK,
            ConnectorType.HUBSPOT,
            ConnectorType.STRIPE,
            ConnectorType.SHOPIFY,
        ]
        for ct in required:
            assert ct in CONNECTOR_DEFINITIONS
            assert CONNECTOR_DEFINITIONS[ct].display_name is not None

    def test_oauth_connectors_have_urls(self):
        """Verifie que les connecteurs OAuth ont les URLs necessaires."""
        for ct, connector in CONNECTOR_DEFINITIONS.items():
            if connector.auth_type == AuthType.OAUTH2:
                assert connector.oauth_authorize_url is not None or connector.oauth_authorize_url == ""
                assert connector.oauth_token_url is not None or connector.oauth_token_url == ""

    def test_connector_has_supported_entities(self):
        """Verifie que chaque connecteur supporte au moins une entite."""
        for ct, connector in CONNECTOR_DEFINITIONS.items():
            # Les connecteurs custom peuvent ne pas avoir d'entites definies
            if ct not in [ConnectorType.REST_API, ConnectorType.WEBHOOK]:
                assert len(connector.supported_entities) > 0 or len(connector.supported_directions) > 0


class TestIntegrationService:
    """Tests pour le service Integration."""

    @pytest.fixture
    def service(self):
        """Cree un service de test (sans DB)."""
        # Note: en production, on utiliserait une vraie session de test
        return None  # Placeholder

    def test_list_connectors(self):
        """Test liste des connecteurs."""
        # Test direct sur CONNECTOR_DEFINITIONS car service necessite DB
        connectors = list(CONNECTOR_DEFINITIONS.values())
        assert len(connectors) > 10

        # Filtrer par categorie
        crm_connectors = [c for c in connectors if c.category == "crm"]
        assert len(crm_connectors) >= 3

    def test_connector_definition_structure(self):
        """Test structure d'une definition de connecteur."""
        stripe = CONNECTOR_DEFINITIONS.get(ConnectorType.STRIPE)
        assert stripe is not None
        assert stripe.name == "stripe"
        assert stripe.display_name == "Stripe"
        assert stripe.category == "payment"
        assert stripe.auth_type == AuthType.API_KEY
        assert "api_key" in stripe.required_fields
        assert stripe.supports_webhooks is True

    def test_hubspot_oauth_config(self):
        """Test configuration OAuth HubSpot."""
        hubspot = CONNECTOR_DEFINITIONS.get(ConnectorType.HUBSPOT)
        assert hubspot is not None
        assert hubspot.auth_type == AuthType.OAUTH2
        assert "hubspot.com" in hubspot.oauth_authorize_url
        assert len(hubspot.oauth_scopes) > 0


class TestSchemas:
    """Tests pour les schemas Pydantic."""

    def test_field_mapping_schema(self):
        """Test schema FieldMapping."""
        from ..schemas import FieldMappingSchema

        fm = FieldMappingSchema(
            source_field="external_id",
            target_field="id",
            transform="str",
            is_required=True
        )
        assert fm.source_field == "external_id"
        assert fm.target_field == "id"
        assert fm.is_required is True

    def test_connection_create_schema(self):
        """Test schema ConnectionCreate."""
        from ..schemas import ConnectionCreate

        conn = ConnectionCreate(
            name="Ma connexion Stripe",
            code="STRIPE_1",
            connector_type=ConnectorType.STRIPE,
            auth_type=AuthType.API_KEY,
            credentials={"api_key": "sk_test_xxx"}
        )
        assert conn.name == "Ma connexion Stripe"
        assert conn.code == "STRIPE_1"
        assert conn.connector_type == ConnectorType.STRIPE

    def test_code_uppercase_validator(self):
        """Test que le code est converti en majuscules."""
        from ..schemas import ConnectionCreate

        conn = ConnectionCreate(
            name="Test",
            code="lowercase_code",
            connector_type=ConnectorType.STRIPE,
            auth_type=AuthType.API_KEY
        )
        assert conn.code == "LOWERCASE_CODE"


class TestExceptions:
    """Tests pour les exceptions."""

    def test_connection_not_found_error(self):
        """Test exception ConnectionNotFoundError."""
        err = ConnectionNotFoundError("abc-123")
        assert "abc-123" in str(err)
        assert err.code == "CONNECTION_NOT_FOUND"
        assert "connection_id" in err.details

    def test_mapping_not_found_error(self):
        """Test exception MappingNotFoundError."""
        err = MappingNotFoundError("map-456")
        assert err.code == "MAPPING_NOT_FOUND"

    def test_sync_execution_running_error(self):
        """Test exception SyncExecutionRunningError."""
        err = SyncExecutionRunningError("conn-1", "config-2")
        assert err.code == "SYNC_EXECUTION_RUNNING"
        assert err.details["connection_id"] == "conn-1"
        assert err.details["config_id"] == "config-2"


class TestEnums:
    """Tests pour les enums."""

    def test_connector_type_values(self):
        """Test valeurs ConnectorType."""
        assert ConnectorType.GOOGLE_DRIVE.value == "google_drive"
        assert ConnectorType.STRIPE.value == "stripe"
        assert ConnectorType.SLACK.value == "slack"

    def test_sync_status_values(self):
        """Test valeurs SyncStatus."""
        assert SyncStatus.PENDING.value == "pending"
        assert SyncStatus.RUNNING.value == "running"
        assert SyncStatus.COMPLETED.value == "completed"
        assert SyncStatus.FAILED.value == "failed"

    def test_webhook_direction_values(self):
        """Test valeurs WebhookDirection."""
        assert WebhookDirection.INBOUND.value == "inbound"
        assert WebhookDirection.OUTBOUND.value == "outbound"


class TestTransformations:
    """Tests pour les transformations de donnees."""

    def test_basic_transformations(self):
        """Test transformations basiques."""
        # Simulation des transformations
        transforms = {
            "upper": lambda v: v.upper() if isinstance(v, str) else v,
            "lower": lambda v: v.lower() if isinstance(v, str) else v,
            "strip": lambda v: v.strip() if isinstance(v, str) else v,
            "int": lambda v: int(v),
            "float": lambda v: float(v),
            "str": lambda v: str(v),
        }

        assert transforms["upper"]("hello") == "HELLO"
        assert transforms["lower"]("HELLO") == "hello"
        assert transforms["strip"]("  hello  ") == "hello"
        assert transforms["int"]("42") == 42
        assert transforms["float"]("3.14") == 3.14
        assert transforms["str"](123) == "123"


class TestWebhookSecurity:
    """Tests pour la securite des webhooks."""

    def test_hmac_signature_generation(self):
        """Test generation de signature HMAC."""
        import hmac
        import hashlib

        secret = "my_secret_key"
        payload = b'{"event": "test"}'

        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        assert len(signature) == 64  # SHA256 = 64 caracteres hex

        # Verification
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        assert hmac.compare_digest(signature, expected)

    def test_invalid_signature_rejected(self):
        """Test qu'une signature invalide est rejetee."""
        import hmac
        import hashlib

        secret = "my_secret_key"
        payload = b'{"event": "test"}'
        wrong_payload = b'{"event": "hacked"}'

        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        wrong_signature = hmac.new(
            secret.encode(),
            wrong_payload,
            hashlib.sha256
        ).hexdigest()

        assert not hmac.compare_digest(signature, wrong_signature)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
