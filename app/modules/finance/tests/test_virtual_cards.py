"""
Tests pour le module Virtual Cards.

Coverage:
- Service: création, blocage, limites, transactions
- Router: tous les endpoints
- Validation: tenant isolation, limites, statuts
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.modules.finance.virtual_cards.service import (
    VirtualCardService,
    VirtualCard,
    CardTransaction,
    CardStatus,
    CardType,
    CardLimitType,
    TransactionStatus,
    DeclineReason,
    CardLimit,
)
from app.modules.finance.virtual_cards.router import router


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def db_session():
    """Session de base de données mockée."""
    return MagicMock()


@pytest.fixture
def tenant_id():
    """ID tenant de test."""
    return "tenant-vc-test-123"


@pytest.fixture
def service(db_session, tenant_id):
    """Service de cartes virtuelles."""
    return VirtualCardService(db=db_session, tenant_id=tenant_id)


@pytest.fixture
def app(service, tenant_id):
    """Application FastAPI de test."""
    from app.core.saas_context import SaaSContext

    test_app = FastAPI()
    test_app.include_router(router)

    def override_service():
        return service

    def override_context():
        return SaaSContext(tenant_id=tenant_id)

    from app.modules.finance.virtual_cards.router import (
        get_virtual_card_service,
        get_saas_context,
    )

    test_app.dependency_overrides[get_virtual_card_service] = override_service
    test_app.dependency_overrides[get_saas_context] = override_context

    return test_app


@pytest.fixture
def client(app):
    """Client de test."""
    return TestClient(app)


# =============================================================================
# TESTS SERVICE - INITIALIZATION
# =============================================================================


class TestServiceInit:
    """Tests d'initialisation du service."""

    def test_init_with_tenant_id(self, db_session, tenant_id):
        """Service s'initialise avec tenant_id."""
        service = VirtualCardService(db=db_session, tenant_id=tenant_id)
        assert service.tenant_id == tenant_id

    def test_init_requires_tenant_id(self, db_session):
        """Service requiert tenant_id."""
        with pytest.raises(ValueError, match="tenant_id est requis"):
            VirtualCardService(db=db_session, tenant_id="")

    def test_init_none_tenant_id(self, db_session):
        """Service rejette tenant_id None."""
        with pytest.raises(ValueError):
            VirtualCardService(db=db_session, tenant_id=None)


# =============================================================================
# TESTS SERVICE - CARD CREATION
# =============================================================================


class TestCardCreation:
    """Tests de création de cartes."""

    @pytest.mark.asyncio
    async def test_create_standard_card(self, service):
        """Création d'une carte standard."""
        result = await service.create_card(
            holder_name="John Doe",
            card_type=CardType.STANDARD,
        )

        assert result.success
        assert result.card is not None
        assert result.card.holder_name == "John Doe"
        assert result.card.card_type == CardType.STANDARD
        assert result.card.status == CardStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_create_card_with_limits(self, service):
        """Création avec limites."""
        result = await service.create_card(
            holder_name="Jane Doe",
            limit_per_transaction=Decimal("100"),
            limit_daily=Decimal("500"),
            limit_monthly=Decimal("5000"),
        )

        assert result.success
        card = result.card
        assert len(card.limits) == 3

        # Vérifier les limites
        limit_types = [l.limit_type for l in card.limits]
        assert CardLimitType.PER_TRANSACTION in limit_types
        assert CardLimitType.DAILY in limit_types
        assert CardLimitType.MONTHLY in limit_types

    @pytest.mark.asyncio
    async def test_create_single_use_card(self, service):
        """Création d'une carte à usage unique."""
        result = await service.create_card(
            holder_name="Single User",
            card_type=CardType.SINGLE_USE,
        )

        assert result.success
        assert result.card.card_type == CardType.SINGLE_USE
        assert result.card.expires_at is not None  # Auto-expiration

    @pytest.mark.asyncio
    async def test_create_card_with_merchant_categories(self, service):
        """Création avec catégories MCC."""
        result = await service.create_card(
            holder_name="Category User",
            merchant_categories=["5411", "5812"],
        )

        assert result.success
        assert "5411" in result.card.merchant_categories
        assert "5812" in result.card.merchant_categories

    @pytest.mark.asyncio
    async def test_card_number_format(self, service):
        """Format du numéro de carte."""
        result = await service.create_card(holder_name="Format Test")

        card = result.card
        assert len(card.card_number_full) == 16
        assert card.card_number_full.startswith("453223")  # BIN
        assert "**** **** ****" in card.masked_number

    @pytest.mark.asyncio
    async def test_card_cvv_format(self, service):
        """Format du CVV."""
        result = await service.create_card(holder_name="CVV Test")

        assert len(result.card.cvv) == 3
        assert result.card.cvv.isdigit()

    @pytest.mark.asyncio
    async def test_card_expiry_format(self, service):
        """Format de la date d'expiration."""
        result = await service.create_card(holder_name="Expiry Test")

        card = result.card
        assert 1 <= card.expiry_month <= 12
        assert card.expiry_year >= datetime.now().year
        assert "/" in card.expiry_date


# =============================================================================
# TESTS SERVICE - CARD MANAGEMENT
# =============================================================================


class TestCardManagement:
    """Tests de gestion des cartes."""

    @pytest.mark.asyncio
    async def test_get_card(self, service):
        """Récupération d'une carte."""
        create_result = await service.create_card(holder_name="Get Test")
        card = await service.get_card(create_result.card.id)

        assert card is not None
        assert card.id == create_result.card.id

    @pytest.mark.asyncio
    async def test_get_card_not_found(self, service):
        """Carte non trouvée."""
        card = await service.get_card("nonexistent-id")
        assert card is None

    @pytest.mark.asyncio
    async def test_list_cards(self, service):
        """Liste des cartes."""
        await service.create_card(holder_name="Card 1")
        await service.create_card(holder_name="Card 2")

        cards = await service.list_cards()
        assert len(cards) >= 2

    @pytest.mark.asyncio
    async def test_list_cards_by_status(self, service):
        """Liste filtrée par statut."""
        result = await service.create_card(holder_name="Active Card")
        await service.block_card(result.card.id)

        active_cards = await service.list_cards(status=CardStatus.ACTIVE)
        blocked_cards = await service.list_cards(status=CardStatus.BLOCKED)

        assert all(c.status == CardStatus.ACTIVE for c in active_cards)
        assert all(c.status == CardStatus.BLOCKED for c in blocked_cards)

    @pytest.mark.asyncio
    async def test_list_cards_by_type(self, service):
        """Liste filtrée par type."""
        await service.create_card(holder_name="Standard", card_type=CardType.STANDARD)
        await service.create_card(holder_name="Single", card_type=CardType.SINGLE_USE)

        standard_cards = await service.list_cards(card_type=CardType.STANDARD)
        single_cards = await service.list_cards(card_type=CardType.SINGLE_USE)

        assert all(c.card_type == CardType.STANDARD for c in standard_cards)
        assert all(c.card_type == CardType.SINGLE_USE for c in single_cards)

    @pytest.mark.asyncio
    async def test_block_card(self, service):
        """Blocage d'une carte."""
        result = await service.create_card(holder_name="Block Test")
        success = await service.block_card(result.card.id, reason="Test block")

        assert success
        card = await service.get_card(result.card.id)
        assert card.status == CardStatus.BLOCKED
        assert "block_reason" in card.metadata

    @pytest.mark.asyncio
    async def test_unblock_card(self, service):
        """Déblocage d'une carte."""
        result = await service.create_card(holder_name="Unblock Test")
        await service.block_card(result.card.id)
        success = await service.unblock_card(result.card.id)

        assert success
        card = await service.get_card(result.card.id)
        assert card.status == CardStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_cancel_card(self, service):
        """Annulation d'une carte."""
        result = await service.create_card(holder_name="Cancel Test")
        success = await service.cancel_card(result.card.id, reason="No longer needed")

        assert success
        card = await service.get_card(result.card.id)
        assert card.status == CardStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_update_limits(self, service):
        """Mise à jour des limites."""
        result = await service.create_card(
            holder_name="Limit Update",
            limit_daily=Decimal("500"),
        )

        success = await service.update_limits(
            result.card.id,
            limit_daily=Decimal("1000"),
            limit_monthly=Decimal("10000"),
        )

        assert success
        card = await service.get_card(result.card.id)

        daily_limit = next(
            (l for l in card.limits if l.limit_type == CardLimitType.DAILY),
            None
        )
        assert daily_limit.amount == Decimal("1000")


# =============================================================================
# TESTS SERVICE - TRANSACTIONS
# =============================================================================


class TestTransactions:
    """Tests des transactions."""

    @pytest.mark.asyncio
    async def test_authorize_transaction(self, service):
        """Autorisation de transaction réussie."""
        create_result = await service.create_card(
            holder_name="Transaction Test",
            limit_daily=Decimal("1000"),
        )

        result = await service.authorize_transaction(
            card_id=create_result.card.id,
            amount=Decimal("50"),
            currency="EUR",
            merchant_name="Test Shop",
            merchant_category="5411",
        )

        assert result.success
        assert result.transaction is not None
        assert result.transaction.status == TransactionStatus.APPROVED
        assert result.transaction.authorization_code is not None

    @pytest.mark.asyncio
    async def test_authorize_blocked_card(self, service):
        """Transaction refusée sur carte bloquée."""
        create_result = await service.create_card(holder_name="Blocked TX Test")
        await service.block_card(create_result.card.id)

        result = await service.authorize_transaction(
            card_id=create_result.card.id,
            amount=Decimal("50"),
            currency="EUR",
            merchant_name="Test Shop",
            merchant_category="5411",
        )

        assert not result.success
        assert result.decline_reason == DeclineReason.CARD_BLOCKED

    @pytest.mark.asyncio
    async def test_authorize_over_limit(self, service):
        """Transaction refusée - montant dépasse la limite."""
        create_result = await service.create_card(
            holder_name="Over Limit Test",
            limit_per_transaction=Decimal("100"),
        )

        result = await service.authorize_transaction(
            card_id=create_result.card.id,
            amount=Decimal("150"),
            currency="EUR",
            merchant_name="Test Shop",
            merchant_category="5411",
        )

        assert not result.success
        assert result.decline_reason == DeclineReason.AMOUNT_EXCEEDED

    @pytest.mark.asyncio
    async def test_authorize_insufficient_limit(self, service):
        """Transaction refusée - limite insuffisante."""
        create_result = await service.create_card(
            holder_name="Insufficient Test",
            limit_daily=Decimal("100"),
        )

        # Première transaction OK
        await service.authorize_transaction(
            card_id=create_result.card.id,
            amount=Decimal("80"),
            currency="EUR",
            merchant_name="Shop 1",
            merchant_category="5411",
        )

        # Deuxième transaction échoue
        result = await service.authorize_transaction(
            card_id=create_result.card.id,
            amount=Decimal("50"),
            currency="EUR",
            merchant_name="Shop 2",
            merchant_category="5411",
        )

        assert not result.success
        assert result.decline_reason == DeclineReason.INSUFFICIENT_LIMIT

    @pytest.mark.asyncio
    async def test_authorize_blocked_merchant(self, service):
        """Transaction refusée - marchand bloqué."""
        create_result = await service.create_card(holder_name="Merchant Block Test")
        await service.add_blocked_merchant(create_result.card.id, "Bad Merchant")

        result = await service.authorize_transaction(
            card_id=create_result.card.id,
            amount=Decimal("50"),
            currency="EUR",
            merchant_name="Bad Merchant",
            merchant_category="5411",
        )

        assert not result.success
        assert result.decline_reason == DeclineReason.MERCHANT_RESTRICTED

    @pytest.mark.asyncio
    async def test_single_use_card_exhausted(self, service):
        """Carte à usage unique épuisée."""
        create_result = await service.create_card(
            holder_name="Single Use Test",
            card_type=CardType.SINGLE_USE,
        )

        # Première transaction OK
        result1 = await service.authorize_transaction(
            card_id=create_result.card.id,
            amount=Decimal("50"),
            currency="EUR",
            merchant_name="Shop",
            merchant_category="5411",
        )
        assert result1.success

        # Deuxième transaction échoue
        result2 = await service.authorize_transaction(
            card_id=create_result.card.id,
            amount=Decimal("25"),
            currency="EUR",
            merchant_name="Shop",
            merchant_category="5411",
        )

        assert not result2.success
        assert result2.decline_reason == DeclineReason.SINGLE_USE_EXHAUSTED

    @pytest.mark.asyncio
    async def test_get_transactions(self, service):
        """Récupération des transactions."""
        create_result = await service.create_card(
            holder_name="TX List Test",
            limit_daily=Decimal("1000"),
        )

        await service.authorize_transaction(
            card_id=create_result.card.id,
            amount=Decimal("50"),
            currency="EUR",
            merchant_name="Shop 1",
            merchant_category="5411",
        )

        transactions = await service.get_transactions(card_id=create_result.card.id)
        assert len(transactions) >= 1

    @pytest.mark.asyncio
    async def test_reverse_transaction(self, service):
        """Annulation de transaction."""
        create_result = await service.create_card(
            holder_name="Reverse Test",
            limit_daily=Decimal("1000"),
        )

        auth_result = await service.authorize_transaction(
            card_id=create_result.card.id,
            amount=Decimal("100"),
            currency="EUR",
            merchant_name="Shop",
            merchant_category="5411",
        )

        success = await service.reverse_transaction(
            auth_result.transaction.id,
            reason="Refund",
        )

        assert success

        # Vérifier que les limites sont restaurées
        card = await service.get_card(create_result.card.id)
        daily_limit = next(
            (l for l in card.limits if l.limit_type == CardLimitType.DAILY),
            None
        )
        assert daily_limit.used == Decimal("0")


# =============================================================================
# TESTS SERVICE - STATISTICS & ALERTS
# =============================================================================


class TestStatisticsAndAlerts:
    """Tests des statistiques et alertes."""

    @pytest.mark.asyncio
    async def test_get_card_stats(self, service):
        """Statistiques d'une carte."""
        create_result = await service.create_card(
            holder_name="Stats Test",
            limit_daily=Decimal("1000"),
        )

        await service.authorize_transaction(
            card_id=create_result.card.id,
            amount=Decimal("50"),
            currency="EUR",
            merchant_name="Shop",
            merchant_category="5411",
        )

        stats = await service.get_card_stats(create_result.card.id)

        assert stats is not None
        assert stats.total_transactions >= 1
        assert stats.approved_transactions >= 1

    @pytest.mark.asyncio
    async def test_spending_alerts(self, service):
        """Alertes de dépassement."""
        create_result = await service.create_card(
            holder_name="Alert Test",
            limit_daily=Decimal("100"),
        )

        # Utiliser 90% de la limite
        await service.authorize_transaction(
            card_id=create_result.card.id,
            amount=Decimal("90"),
            currency="EUR",
            merchant_name="Shop",
            merchant_category="5411",
        )

        alerts = await service.get_spending_alerts(threshold_percent=Decimal("80"))

        assert len(alerts) >= 1
        assert any(a["card_id"] == create_result.card.id for a in alerts)


# =============================================================================
# TESTS ROUTER
# =============================================================================


class TestRouter:
    """Tests des endpoints."""

    def test_create_card_endpoint(self, client):
        """POST /cards."""
        response = client.post(
            "/v3/finance/virtual-cards/cards",
            json={
                "holder_name": "Test User",
                "card_type": "standard",
                "limit_daily": "500",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["holder_name"] == "Test User"
        assert "card_number_full" in data  # Détails complets retournés

    def test_list_cards_endpoint(self, client):
        """GET /cards."""
        # Créer une carte d'abord
        client.post(
            "/v3/finance/virtual-cards/cards",
            json={"holder_name": "List Test"},
        )

        response = client.get("/v3/finance/virtual-cards/cards")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_card_endpoint(self, client):
        """GET /cards/{card_id}."""
        create_response = client.post(
            "/v3/finance/virtual-cards/cards",
            json={"holder_name": "Get Test"},
        )
        card_id = create_response.json()["id"]

        response = client.get(f"/v3/finance/virtual-cards/cards/{card_id}")

        assert response.status_code == 200
        assert response.json()["id"] == card_id

    def test_get_card_not_found(self, client):
        """GET /cards/{card_id} - non trouvée."""
        response = client.get("/v3/finance/virtual-cards/cards/nonexistent")
        assert response.status_code == 404

    def test_block_card_endpoint(self, client):
        """POST /cards/{card_id}/block."""
        create_response = client.post(
            "/v3/finance/virtual-cards/cards",
            json={"holder_name": "Block Test"},
        )
        card_id = create_response.json()["id"]

        response = client.post(
            f"/v3/finance/virtual-cards/cards/{card_id}/block",
            json={"reason": "Test block"},
        )

        assert response.status_code == 200
        assert response.json()["success"]

    def test_unblock_card_endpoint(self, client):
        """POST /cards/{card_id}/unblock."""
        create_response = client.post(
            "/v3/finance/virtual-cards/cards",
            json={"holder_name": "Unblock Test"},
        )
        card_id = create_response.json()["id"]

        # Bloquer puis débloquer
        client.post(f"/v3/finance/virtual-cards/cards/{card_id}/block")
        response = client.post(f"/v3/finance/virtual-cards/cards/{card_id}/unblock")

        assert response.status_code == 200
        assert response.json()["success"]

    def test_cancel_card_endpoint(self, client):
        """POST /cards/{card_id}/cancel."""
        create_response = client.post(
            "/v3/finance/virtual-cards/cards",
            json={"holder_name": "Cancel Test"},
        )
        card_id = create_response.json()["id"]

        response = client.post(
            f"/v3/finance/virtual-cards/cards/{card_id}/cancel",
            json={"reason": "No longer needed"},
        )

        assert response.status_code == 200
        assert response.json()["success"]

    def test_update_limits_endpoint(self, client):
        """PUT /cards/{card_id}/limits."""
        create_response = client.post(
            "/v3/finance/virtual-cards/cards",
            json={"holder_name": "Limits Test"},
        )
        card_id = create_response.json()["id"]

        response = client.put(
            f"/v3/finance/virtual-cards/cards/{card_id}/limits",
            json={
                "limit_daily": "1000",
                "limit_monthly": "10000",
            }
        )

        assert response.status_code == 200
        assert len(response.json()["limits"]) >= 2

    def test_authorize_transaction_endpoint(self, client):
        """POST /authorize."""
        create_response = client.post(
            "/v3/finance/virtual-cards/cards",
            json={
                "holder_name": "Auth Test",
                "limit_daily": "1000",
            },
        )
        card_id = create_response.json()["id"]

        response = client.post(
            "/v3/finance/virtual-cards/authorize",
            json={
                "card_id": card_id,
                "amount": "50",
                "currency": "EUR",
                "merchant_name": "Test Shop",
                "merchant_category": "5411",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["transaction"]["authorization_code"]

    def test_get_transactions_endpoint(self, client):
        """GET /transactions."""
        response = client.get("/v3/finance/virtual-cards/transactions")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_card_stats_endpoint(self, client):
        """GET /stats/{card_id}."""
        create_response = client.post(
            "/v3/finance/virtual-cards/cards",
            json={"holder_name": "Stats Test"},
        )
        card_id = create_response.json()["id"]

        response = client.get(f"/v3/finance/virtual-cards/stats/{card_id}")

        assert response.status_code == 200
        assert response.json()["card_id"] == card_id

    def test_get_alerts_endpoint(self, client):
        """GET /alerts."""
        response = client.get("/v3/finance/virtual-cards/alerts?threshold=80")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_card_types_endpoint(self, client):
        """GET /card-types."""
        response = client.get("/v3/finance/virtual-cards/card-types")

        assert response.status_code == 200
        types = response.json()
        assert len(types) >= 4
        assert any(t["type"] == "standard" for t in types)

    def test_health_check_endpoint(self, client):
        """GET /health."""
        response = client.get("/v3/finance/virtual-cards/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "card_creation" in data["features"]


# =============================================================================
# TESTS CARD LIMIT
# =============================================================================


class TestCardLimit:
    """Tests de la classe CardLimit."""

    def test_remaining_calculation(self):
        """Calcul du montant restant."""
        limit = CardLimit(
            limit_type=CardLimitType.DAILY,
            amount=Decimal("1000"),
            used=Decimal("300"),
        )

        assert limit.remaining == Decimal("700")

    def test_usage_percent(self):
        """Calcul du pourcentage d'utilisation."""
        limit = CardLimit(
            limit_type=CardLimitType.DAILY,
            amount=Decimal("1000"),
            used=Decimal("250"),
        )

        assert limit.usage_percent == Decimal("25.00")

    def test_remaining_never_negative(self):
        """Remaining ne peut pas être négatif."""
        limit = CardLimit(
            limit_type=CardLimitType.DAILY,
            amount=Decimal("100"),
            used=Decimal("150"),  # Dépassement
        )

        assert limit.remaining == Decimal("0")


# =============================================================================
# TESTS ENUMS
# =============================================================================


class TestEnums:
    """Tests des enums."""

    def test_card_status_values(self):
        """Valeurs de CardStatus."""
        assert CardStatus.ACTIVE.value == "active"
        assert CardStatus.BLOCKED.value == "blocked"
        assert CardStatus.CANCELLED.value == "cancelled"

    def test_card_type_values(self):
        """Valeurs de CardType."""
        assert CardType.STANDARD.value == "standard"
        assert CardType.SINGLE_USE.value == "single_use"
        assert CardType.RECURRING.value == "recurring"

    def test_decline_reason_values(self):
        """Valeurs de DeclineReason."""
        assert DeclineReason.CARD_BLOCKED.value == "card_blocked"
        assert DeclineReason.INSUFFICIENT_LIMIT.value == "insufficient_limit"


# =============================================================================
# TESTS DATACLASSES
# =============================================================================


class TestDataClasses:
    """Tests des dataclasses."""

    def test_virtual_card_masked_number(self):
        """Numéro de carte masqué."""
        card = VirtualCard(
            id="test-id",
            tenant_id="test-tenant",
            card_number="**** **** **** 1234",
            card_number_full="4532230000001234",
            expiry_month=12,
            expiry_year=2029,
            cvv="123",
            holder_name="Test",
            card_type=CardType.STANDARD,
            status=CardStatus.ACTIVE,
        )

        assert card.masked_number == "**** **** **** 1234"

    def test_virtual_card_expiry_date(self):
        """Format date d'expiration."""
        card = VirtualCard(
            id="test-id",
            tenant_id="test-tenant",
            card_number="****",
            card_number_full="1234567890123456",
            expiry_month=3,
            expiry_year=2029,
            cvv="123",
            holder_name="Test",
            card_type=CardType.STANDARD,
            status=CardStatus.ACTIVE,
        )

        assert card.expiry_date == "03/29"

    def test_virtual_card_is_active(self):
        """Vérification carte active."""
        active_card = VirtualCard(
            id="test-id",
            tenant_id="test-tenant",
            card_number="****",
            card_number_full="1234567890123456",
            expiry_month=12,
            expiry_year=2029,
            cvv="123",
            holder_name="Test",
            card_type=CardType.STANDARD,
            status=CardStatus.ACTIVE,
        )

        blocked_card = VirtualCard(
            id="test-id-2",
            tenant_id="test-tenant",
            card_number="****",
            card_number_full="1234567890123456",
            expiry_month=12,
            expiry_year=2029,
            cvv="123",
            holder_name="Test",
            card_type=CardType.STANDARD,
            status=CardStatus.BLOCKED,
        )

        assert active_card.is_active
        assert not blocked_card.is_active

    def test_card_transaction_creation(self):
        """Création CardTransaction."""
        tx = CardTransaction(
            id="tx-1",
            tenant_id="tenant-1",
            card_id="card-1",
            amount=Decimal("100.50"),
            currency="EUR",
            merchant_name="Test Shop",
            merchant_category="5411",
            merchant_country="FR",
            status=TransactionStatus.APPROVED,
        )

        assert tx.amount == Decimal("100.50")
        assert tx.status == TransactionStatus.APPROVED
