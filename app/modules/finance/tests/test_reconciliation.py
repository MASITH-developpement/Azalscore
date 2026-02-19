"""
Tests pour le module de réconciliation bancaire IA.
===================================================

Tests unitaires et d'intégration pour ReconciliationService et Router.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.finance.reconciliation.service import (
    ReconciliationService,
    ReconciliationConfig,
    MatchSuggestion,
    MatchType,
    MatchConfidence,
    ReconciliationResult,
)
from app.modules.finance.reconciliation.router import (
    router,
    get_reconciliation_service,
)
from app.core.dependencies_v2 import get_saas_context


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def tenant_id() -> str:
    """ID de tenant pour les tests."""
    return "tenant-test-001"


@pytest.fixture
def mock_db():
    """Session de base de données mockée."""
    db = MagicMock()
    db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None
    return db


@pytest.fixture
def config():
    """Configuration de test."""
    return ReconciliationConfig(
        auto_match_threshold=95,
        amount_tolerance_percent=Decimal("0.01"),
        date_window_days=5,
    )


@pytest.fixture
def service(mock_db, tenant_id, config):
    """Service de réconciliation pour les tests."""
    return ReconciliationService(db=mock_db, tenant_id=tenant_id, config=config)


@pytest.fixture
def mock_service():
    """Service mocké pour les tests de router."""
    service = MagicMock(spec=ReconciliationService)
    service.get_match_suggestions = AsyncMock(return_value=[])
    service.auto_reconcile = AsyncMock(return_value=ReconciliationResult(success=True))
    service.manual_reconcile = AsyncMock(return_value=ReconciliationResult(success=True, matched_count=1))
    service.undo_reconciliation = AsyncMock(return_value=ReconciliationResult(success=True, matched_count=1))
    service.get_stats = AsyncMock()
    return service


@pytest.fixture
def mock_context():
    """Contexte SaaS mocké."""
    context = MagicMock()
    context.tenant_id = "test-tenant-123"
    context.user_id = uuid4()
    return context


@pytest.fixture
def app(mock_service, mock_context):
    """Application FastAPI de test."""
    test_app = FastAPI()
    test_app.include_router(router)

    async def override_service():
        return mock_service

    async def override_context():
        return mock_context

    test_app.dependency_overrides[get_reconciliation_service] = override_service
    test_app.dependency_overrides[get_saas_context] = override_context
    return test_app


@pytest.fixture
def client(app):
    """Client de test."""
    return TestClient(app)


# =============================================================================
# TESTS SERVICE - INITIALISATION
# =============================================================================


class TestServiceInit:
    """Tests d'initialisation du service."""

    def test_init_with_tenant_id(self, mock_db, tenant_id):
        """Test initialisation avec tenant_id."""
        service = ReconciliationService(db=mock_db, tenant_id=tenant_id)
        assert service.tenant_id == tenant_id
        assert service.db == mock_db

    def test_init_requires_tenant_id(self, mock_db):
        """Test que tenant_id est obligatoire."""
        with pytest.raises(ValueError, match="tenant_id est obligatoire"):
            ReconciliationService(db=mock_db, tenant_id="")

    def test_init_with_custom_config(self, mock_db, tenant_id, config):
        """Test initialisation avec configuration custom."""
        service = ReconciliationService(db=mock_db, tenant_id=tenant_id, config=config)
        assert service.config.auto_match_threshold == 95


# =============================================================================
# TESTS SERVICE - SCORING
# =============================================================================


class TestScoring:
    """Tests de l'algorithme de scoring."""

    def test_extract_reference_facture(self, service):
        """Test extraction référence facture."""
        ref = service._extract_reference("Paiement FAC-2024001 client")
        assert ref is not None
        assert "FAC" in ref or "2024001" in ref

    def test_extract_reference_virement(self, service):
        """Test extraction référence virement."""
        ref = service._extract_reference("VIR-123456 fournisseur")
        assert ref is not None
        assert "VIR" in ref or "123456" in ref

    def test_extract_reference_numero_long(self, service):
        """Test extraction numéro long."""
        ref = service._extract_reference("Transaction 1234567890")
        assert ref == "1234567890"

    def test_extract_reference_none(self, service):
        """Test extraction sans référence."""
        ref = service._extract_reference("Achat divers")
        assert ref is None or len(ref) >= 6

    def test_label_similarity_identical(self, service):
        """Test similarité labels identiques."""
        score = service._calculate_label_similarity(
            "Paiement facture client ABC",
            "Paiement facture client ABC",
        )
        assert score == 1.0

    def test_label_similarity_partial(self, service):
        """Test similarité labels partiels."""
        score = service._calculate_label_similarity(
            "Paiement facture ABC",
            "Règlement facture ABC SAS",
        )
        assert 0.3 < score < 0.8

    def test_label_similarity_different(self, service):
        """Test similarité labels différents."""
        score = service._calculate_label_similarity(
            "Virement bancaire",
            "Achat fournitures bureau",
        )
        assert score < 0.3

    def test_label_similarity_empty(self, service):
        """Test similarité avec texte vide."""
        assert service._calculate_label_similarity("", "test") == 0.0
        assert service._calculate_label_similarity("test", "") == 0.0


# =============================================================================
# TESTS SERVICE - SUGGESTIONS
# =============================================================================


class TestSuggestions:
    """Tests de génération de suggestions."""

    @pytest.mark.asyncio
    async def test_get_suggestions_no_pending_lines(self, service, mock_db):
        """Test suggestions sans lignes en attente."""
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        suggestions = await service.get_match_suggestions(
            bank_account_id=uuid4(),
            limit=10,
        )

        assert suggestions == []

    @pytest.mark.asyncio
    async def test_get_suggestions_no_candidates(self, service, mock_db):
        """Test suggestions sans écritures candidates."""
        # Mock ligne bancaire
        bank_line = MagicMock()
        bank_line.date = datetime.now()
        bank_line.credit = Decimal("100")
        bank_line.debit = Decimal("0")
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [bank_line]

        # Mock pas d'écritures
        mock_db.query.return_value.filter.return_value.first.return_value = None

        suggestions = await service.get_match_suggestions(
            bank_account_id=uuid4(),
            limit=10,
        )

        # Pas de suggestions car pas de candidates
        assert suggestions == []


# =============================================================================
# TESTS SERVICE - AUTO-RECONCILIATION
# =============================================================================


class TestAutoReconcile:
    """Tests de l'auto-réconciliation."""

    @pytest.mark.asyncio
    async def test_auto_reconcile_dry_run(self, service):
        """Test auto-réconciliation en dry run."""
        with patch.object(service, 'get_match_suggestions', new_callable=AsyncMock) as mock_suggestions:
            mock_suggestions.return_value = [
                MatchSuggestion(
                    id="sugg-1",
                    bank_line_id=uuid4(),
                    entry_line_id=uuid4(),
                    score=98,
                    confidence=MatchConfidence.HIGH,
                    match_type=MatchType.EXACT,
                    reasons=["Test"],
                ),
            ]

            result = await service.auto_reconcile(
                bank_account_id=uuid4(),
                dry_run=True,
            )

            assert result.success is True
            assert result.matched_count == 0  # Dry run = pas de match effectif
            assert result.suggested_count == 1

    @pytest.mark.asyncio
    async def test_auto_reconcile_no_suggestions(self, service):
        """Test auto-réconciliation sans suggestions."""
        with patch.object(service, 'get_match_suggestions', new_callable=AsyncMock) as mock_suggestions:
            mock_suggestions.return_value = []

            result = await service.auto_reconcile(
                bank_account_id=uuid4(),
            )

            assert result.success is True
            assert result.matched_count == 0


# =============================================================================
# TESTS ROUTER
# =============================================================================


class TestRouter:
    """Tests des endpoints REST."""

    def test_get_suggestions(self, client, mock_service):
        """Test endpoint suggestions."""
        mock_service.get_match_suggestions.return_value = []

        response = client.get(
            "/v3/finance/reconciliation/suggestions",
            params={"bank_account_id": str(uuid4())},
        )

        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert "total" in data

    def test_get_suggestions_with_options(self, client, mock_service):
        """Test endpoint suggestions avec options."""
        mock_service.get_match_suggestions.return_value = []

        response = client.get(
            "/v3/finance/reconciliation/suggestions",
            params={
                "bank_account_id": str(uuid4()),
                "limit": 20,
                "min_score": 70,
            },
        )

        assert response.status_code == 200

    def test_auto_reconcile(self, client, mock_service):
        """Test endpoint auto-réconciliation."""
        mock_service.auto_reconcile.return_value = ReconciliationResult(
            success=True,
            matched_count=5,
            auto_matched_count=5,
        )

        response = client.post(
            "/v3/finance/reconciliation/auto",
            json={
                "bank_account_id": str(uuid4()),
                "min_score": 95,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["matched_count"] == 5

    def test_auto_reconcile_dry_run(self, client, mock_service):
        """Test endpoint auto-réconciliation dry run."""
        mock_service.auto_reconcile.return_value = ReconciliationResult(
            success=True,
            matched_count=0,
            suggested_count=3,
        )

        response = client.post(
            "/v3/finance/reconciliation/auto",
            json={
                "bank_account_id": str(uuid4()),
                "dry_run": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["matched_count"] == 0
        assert data["suggested_count"] == 3

    def test_manual_reconcile(self, client, mock_service):
        """Test endpoint réconciliation manuelle."""
        response = client.post(
            "/v3/finance/reconciliation/manual",
            json={
                "bank_line_id": str(uuid4()),
                "entry_line_id": str(uuid4()),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["matched_count"] == 1

    def test_undo_reconciliation(self, client, mock_service):
        """Test endpoint annulation."""
        response = client.post(
            "/v3/finance/reconciliation/undo",
            json={
                "bank_line_id": str(uuid4()),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_stats(self, client, mock_service):
        """Test endpoint statistiques."""
        from app.modules.finance.reconciliation.service import ReconciliationStats

        mock_service.get_stats.return_value = ReconciliationStats(
            total_bank_lines=100,
            reconciled_lines=75,
            pending_lines=25,
        )

        response = client.get(
            "/v3/finance/reconciliation/stats",
            params={"bank_account_id": str(uuid4())},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_bank_lines"] == 100
        assert data["reconciled_lines"] == 75
        assert data["reconciliation_rate"] == 75.0

    def test_health_check(self, client):
        """Test health check."""
        response = client.get("/v3/finance/reconciliation/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "features" in data


# =============================================================================
# TESTS VALIDATION
# =============================================================================


class TestValidation:
    """Tests de validation des requêtes."""

    def test_suggestions_missing_account(self, client):
        """Test suggestions sans compte."""
        response = client.get("/v3/finance/reconciliation/suggestions")
        assert response.status_code == 422

    def test_auto_reconcile_invalid_score(self, client, mock_service):
        """Test auto-réconciliation score invalide."""
        response = client.post(
            "/v3/finance/reconciliation/auto",
            json={
                "bank_account_id": str(uuid4()),
                "min_score": 150,  # > 100
            },
        )
        assert response.status_code == 422

    def test_manual_reconcile_missing_fields(self, client, mock_service):
        """Test réconciliation manuelle champs manquants."""
        response = client.post(
            "/v3/finance/reconciliation/manual",
            json={
                "bank_line_id": str(uuid4()),
                # entry_line_id manquant
            },
        )
        assert response.status_code == 422


# =============================================================================
# TESTS CONFIGURATION
# =============================================================================


class TestConfiguration:
    """Tests de la configuration."""

    def test_default_config(self):
        """Test configuration par défaut."""
        config = ReconciliationConfig()
        assert config.auto_match_threshold == 95
        assert config.date_window_days == 5

    def test_custom_config(self):
        """Test configuration personnalisée."""
        config = ReconciliationConfig(
            auto_match_threshold=90,
            date_window_days=10,
            amount_tolerance_percent=Decimal("0.02"),
        )
        assert config.auto_match_threshold == 90
        assert config.date_window_days == 10
        assert config.amount_tolerance_percent == Decimal("0.02")


# =============================================================================
# TESTS MATCH TYPES
# =============================================================================


class TestMatchTypes:
    """Tests des types de correspondance."""

    def test_match_confidence_levels(self):
        """Test niveaux de confiance."""
        assert MatchConfidence.HIGH.value == "high"
        assert MatchConfidence.MEDIUM.value == "medium"
        assert MatchConfidence.LOW.value == "low"
        assert MatchConfidence.VERY_LOW.value == "very_low"

    def test_match_types(self):
        """Test types de match."""
        assert MatchType.EXACT.value == "exact"
        assert MatchType.FUZZY.value == "fuzzy"
        assert MatchType.PATTERN.value == "pattern"
        assert MatchType.REFERENCE.value == "reference"
