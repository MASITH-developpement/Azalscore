"""
Tests pour le module Catégorisation Automatique.
=================================================

Tests unitaires et d'intégration pour CategorizationService et Router.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.finance.auto_categorization.service import (
    CategorizationService,
    CategorizationResult,
    CategorySuggestion,
    CategorizationRule,
    Transaction,
    TransactionType,
    RuleType,
    MatchConfidence,
    DefaultPatterns,
)
from app.modules.finance.auto_categorization.router import (
    router,
    get_categorization_service,
)
from app.core.dependencies_v2 import get_saas_context


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def tenant_id() -> str:
    """ID de tenant pour les tests."""
    return "tenant-test-categorization-001"


@pytest.fixture
def mock_db():
    """Session de base de données mockée."""
    return MagicMock()


@pytest.fixture
def service(mock_db, tenant_id):
    """Service de catégorisation pour les tests."""
    return CategorizationService(db=mock_db, tenant_id=tenant_id)


@pytest.fixture
def mock_service():
    """Service mocké pour les tests de router."""
    service = MagicMock(spec=CategorizationService)
    service.categorize_transaction = AsyncMock(return_value=CategorizationResult(
        success=True,
        transaction_id="trans-001",
        auto_applied=False,
        suggestions=[
            CategorySuggestion(
                account_code="641100",
                account_name="Salaires bruts",
                category="salary",
                confidence=95.0,
                match_confidence=MatchConfidence.HIGH,
                rule_id="rule-001",
                rule_name="Salaires",
                reason="Règle: Salaires",
            ),
        ],
        confidence=95.0,
        match_confidence=MatchConfidence.HIGH,
    ))
    service.categorize_batch = AsyncMock(return_value=[
        CategorizationResult(success=True, transaction_id="trans-001", suggestions=[]),
        CategorizationResult(success=True, transaction_id="trans-002", suggestions=[]),
    ])
    service.list_rules = AsyncMock(return_value=[])
    service.create_rule = AsyncMock()
    service.update_rule = AsyncMock()
    service.delete_rule = AsyncMock(return_value=True)
    service.get_stats = AsyncMock(return_value={
        "total_rules": 10,
        "active_rules": 8,
        "auto_apply_rules": 5,
        "most_used_rules": [],
    })
    return service


@pytest.fixture
def mock_context():
    """Contexte SaaS mocké."""
    context = MagicMock()
    context.tenant_id = "test-tenant-cat-123"
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

    test_app.dependency_overrides[get_categorization_service] = override_service
    test_app.dependency_overrides[get_saas_context] = override_context
    return test_app


@pytest.fixture
def client(app):
    """Client de test."""
    return TestClient(app)


@pytest.fixture
def sample_transaction():
    """Transaction de test."""
    return Transaction(
        id="trans-001",
        label="Virement Salaire JANVIER 2024",
        amount=Decimal("-3000.00"),
        date=datetime.now(),
        transaction_type=TransactionType.DEBIT,
    )


@pytest.fixture
def sample_rule():
    """Règle de test."""
    return CategorizationRule(
        id="rule-001",
        tenant_id="test-tenant",
        name="Test Rule",
        rule_type=RuleType.KEYWORD,
        keywords=["salaire"],
        account_code="641100",
        category="salary",
        priority=100,
        is_active=True,
        auto_apply=True,
    )


# =============================================================================
# TESTS SERVICE - INITIALISATION
# =============================================================================


class TestServiceInit:
    """Tests d'initialisation du service."""

    def test_init_with_tenant_id(self, mock_db, tenant_id):
        """Test initialisation avec tenant_id."""
        service = CategorizationService(db=mock_db, tenant_id=tenant_id)
        assert service.tenant_id == tenant_id
        assert service.db == mock_db

    def test_init_requires_tenant_id(self, mock_db):
        """Test que tenant_id est obligatoire."""
        with pytest.raises(ValueError, match="tenant_id est obligatoire"):
            CategorizationService(db=mock_db, tenant_id="")

    def test_default_thresholds(self, service):
        """Test seuils par défaut."""
        assert service.HIGH_CONFIDENCE_THRESHOLD == 90
        assert service.MEDIUM_CONFIDENCE_THRESHOLD == 70
        assert service.AUTO_APPLY_THRESHOLD == 95


# =============================================================================
# TESTS SERVICE - CATÉGORISATION
# =============================================================================


class TestCategorization:
    """Tests de catégorisation."""

    @pytest.mark.asyncio
    async def test_categorize_transaction_success(self, service, sample_transaction):
        """Test catégorisation réussie."""
        result = await service.categorize_transaction(sample_transaction)
        assert result.success is True
        assert result.transaction_id == sample_transaction.id

    @pytest.mark.asyncio
    async def test_categorize_transaction_with_suggestions(self, service, sample_transaction):
        """Test catégorisation avec suggestions."""
        result = await service.categorize_transaction(sample_transaction)
        assert result.success is True
        assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    async def test_categorize_batch(self, service):
        """Test catégorisation par lot."""
        transactions = [
            Transaction(
                id=f"trans-{i}",
                label=f"Transaction {i}",
                amount=Decimal("100.00"),
                date=datetime.now(),
                transaction_type=TransactionType.DEBIT,
            )
            for i in range(3)
        ]
        results = await service.categorize_batch(transactions)
        assert len(results) == 3
        assert all(r.success for r in results)


# =============================================================================
# TESTS SERVICE - PATTERN MATCHING
# =============================================================================


class TestPatternMatching:
    """Tests de matching de patterns."""

    def test_match_pattern_simple(self, service):
        """Test matching pattern simple."""
        assert service._match_pattern("Virement Salaire", r"salaire")
        assert service._match_pattern("VIREMENT SALAIRE", r"salaire")  # Case insensitive

    def test_match_pattern_regex(self, service):
        """Test matching pattern regex."""
        assert service._match_pattern("Facture EDF 12345", r"edf|engie")
        assert service._match_pattern("Facture ENGIE 67890", r"edf|engie")

    def test_match_pattern_no_match(self, service):
        """Test pattern sans correspondance."""
        assert not service._match_pattern("Achat divers", r"salaire")

    def test_match_pattern_invalid_regex(self, service):
        """Test pattern regex invalide."""
        assert not service._match_pattern("Test", r"[invalid")

    def test_default_patterns_salary(self, service):
        """Test patterns salaire."""
        transaction = Transaction(
            id="test",
            label="Virement salaire janvier",
            amount=Decimal("-3000"),
            date=datetime.now(),
            transaction_type=TransactionType.DEBIT,
        )
        suggestions = service._match_default_patterns(transaction)
        assert any(s.category == "salary" for s in suggestions)

    def test_default_patterns_bank_fees(self, service):
        """Test patterns frais bancaires."""
        transaction = Transaction(
            id="test",
            label="Commission de compte frais bancaires",
            amount=Decimal("-15"),
            date=datetime.now(),
            transaction_type=TransactionType.DEBIT,
        )
        suggestions = service._match_default_patterns(transaction)
        assert any(s.category == "bank_fees" for s in suggestions)

    def test_default_patterns_energy(self, service):
        """Test patterns énergie."""
        transaction = Transaction(
            id="test",
            label="Prlv EDF Entreprise",
            amount=Decimal("-250"),
            date=datetime.now(),
            transaction_type=TransactionType.DEBIT,
        )
        suggestions = service._match_default_patterns(transaction)
        assert any(s.category == "energy" for s in suggestions)


# =============================================================================
# TESTS SERVICE - ÉVALUATION DES RÈGLES
# =============================================================================


class TestRuleEvaluation:
    """Tests d'évaluation des règles."""

    def test_evaluate_rule_keyword_match(self, service, sample_transaction, sample_rule):
        """Test évaluation règle avec mot-clé."""
        score = service._evaluate_rule(sample_transaction, sample_rule)
        assert score > 0

    def test_evaluate_rule_type_mismatch(self, service, sample_transaction, sample_rule):
        """Test évaluation règle type incorrect."""
        sample_rule.transaction_type = TransactionType.CREDIT
        score = service._evaluate_rule(sample_transaction, sample_rule)
        assert score == 0  # Type incorrect

    def test_evaluate_rule_pattern(self, service, sample_transaction):
        """Test évaluation règle pattern."""
        rule = CategorizationRule(
            id="test",
            tenant_id="test",
            name="Test",
            rule_type=RuleType.PATTERN,
            pattern=r"salaire",
            transaction_type=TransactionType.DEBIT,
            account_code="641100",
        )
        score = service._evaluate_rule(sample_transaction, rule)
        assert score > 50  # Bonus pour match pattern

    def test_evaluate_rule_amount_range(self, service, sample_transaction):
        """Test évaluation règle plage de montant."""
        rule = CategorizationRule(
            id="test",
            tenant_id="test",
            name="Test",
            rule_type=RuleType.AMOUNT_RANGE,
            amount_min=Decimal("2000"),
            amount_max=Decimal("4000"),
            account_code="641100",
        )
        score = service._evaluate_rule(sample_transaction, rule)
        assert score > 0  # 3000 est dans la plage


# =============================================================================
# TESTS SERVICE - GESTION DES RÈGLES
# =============================================================================


class TestRuleManagement:
    """Tests de gestion des règles."""

    @pytest.mark.asyncio
    async def test_create_rule(self, service, sample_rule):
        """Test création de règle."""
        created = await service.create_rule(sample_rule)
        assert created.id is not None
        assert created.tenant_id == service.tenant_id

    @pytest.mark.asyncio
    async def test_list_rules(self, service):
        """Test listing des règles."""
        rules = await service.list_rules()
        assert isinstance(rules, list)

    @pytest.mark.asyncio
    async def test_list_rules_default_rules_loaded(self, service):
        """Test que les règles par défaut sont chargées."""
        rules = await service.list_rules()
        assert len(rules) > 0

    @pytest.mark.asyncio
    async def test_update_rule(self, service):
        """Test mise à jour de règle."""
        # D'abord créer une règle
        rules = await service.list_rules()
        if rules:
            updated = await service.update_rule(rules[0].id, {"priority": 200})
            assert updated is not None
            assert updated.priority == 200

    @pytest.mark.asyncio
    async def test_delete_rule(self, service, sample_rule):
        """Test suppression de règle."""
        created = await service.create_rule(sample_rule)
        deleted = await service.delete_rule(created.id)
        assert deleted is True

    @pytest.mark.asyncio
    async def test_get_stats(self, service):
        """Test statistiques."""
        stats = await service.get_stats()
        assert "total_rules" in stats
        assert "active_rules" in stats


# =============================================================================
# TESTS SERVICE - UTILITAIRES
# =============================================================================


class TestUtilities:
    """Tests des utilitaires."""

    def test_get_account_name(self, service):
        """Test récupération nom de compte."""
        name = service._get_account_name("641100")
        assert "Salaires" in name

    def test_get_account_name_unknown(self, service):
        """Test récupération nom de compte inconnu."""
        name = service._get_account_name("999999")
        assert "999999" in name

    def test_get_match_confidence_high(self, service):
        """Test niveau de confiance élevé."""
        assert service._get_match_confidence(95) == MatchConfidence.HIGH

    def test_get_match_confidence_medium(self, service):
        """Test niveau de confiance moyen."""
        assert service._get_match_confidence(75) == MatchConfidence.MEDIUM

    def test_get_match_confidence_low(self, service):
        """Test niveau de confiance bas."""
        assert service._get_match_confidence(55) == MatchConfidence.LOW

    def test_get_match_confidence_suggested(self, service):
        """Test niveau de confiance suggéré."""
        assert service._get_match_confidence(40) == MatchConfidence.SUGGESTED

    def test_deduplicate_and_sort(self, service):
        """Test déduplication et tri."""
        suggestions = [
            CategorySuggestion(account_code="641100", account_name="Salaires", confidence=80.0),
            CategorySuggestion(account_code="641100", account_name="Salaires", confidence=90.0),
            CategorySuggestion(account_code="627100", account_name="Frais bancaires", confidence=70.0),
        ]
        result = service._deduplicate_and_sort(suggestions)
        assert len(result) == 2
        assert result[0].confidence == 90.0  # Le plus confiant en premier


# =============================================================================
# TESTS ROUTER
# =============================================================================


class TestRouter:
    """Tests des endpoints REST."""

    def test_categorize_transaction(self, client, mock_service):
        """Test endpoint catégorisation."""
        response = client.post(
            "/v3/finance/auto-categorization/categorize",
            json={
                "id": "trans-001",
                "label": "Virement Salaire",
                "amount": "-3000.00",
                "date": "2024-01-15",
                "transaction_type": "debit",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "suggestions" in data

    def test_categorize_transaction_invalid_type(self, client, mock_service):
        """Test endpoint catégorisation type invalide."""
        response = client.post(
            "/v3/finance/auto-categorization/categorize",
            json={
                "id": "trans-001",
                "label": "Test",
                "amount": "100.00",
                "date": "2024-01-15",
                "transaction_type": "invalid",
            },
        )

        assert response.status_code == 400

    def test_categorize_batch(self, client, mock_service):
        """Test endpoint catégorisation lot."""
        response = client.post(
            "/v3/finance/auto-categorization/batch",
            json={
                "transactions": [
                    {
                        "id": "trans-001",
                        "label": "Transaction 1",
                        "amount": "100.00",
                        "date": "2024-01-15",
                        "transaction_type": "debit",
                    },
                    {
                        "id": "trans-002",
                        "label": "Transaction 2",
                        "amount": "200.00",
                        "date": "2024-01-15",
                        "transaction_type": "credit",
                    },
                ],
                "auto_apply": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_list_rules(self, client, mock_service):
        """Test endpoint listing règles."""
        response = client.get("/v3/finance/auto-categorization/rules")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_rule(self, client, mock_service):
        """Test endpoint création règle."""
        mock_service.create_rule.return_value = CategorizationRule(
            id="new-rule",
            tenant_id="test",
            name="Nouvelle règle",
            rule_type=RuleType.KEYWORD,
            keywords=["test"],
            account_code="641100",
        )

        response = client.post(
            "/v3/finance/auto-categorization/rules",
            json={
                "name": "Nouvelle règle",
                "rule_type": "keyword",
                "keywords": ["test"],
                "account_code": "641100",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Nouvelle règle"

    def test_delete_rule(self, client, mock_service):
        """Test endpoint suppression règle."""
        response = client.delete("/v3/finance/auto-categorization/rules/rule-001")

        assert response.status_code == 204

    def test_delete_rule_not_found(self, client, mock_service):
        """Test endpoint suppression règle inexistante."""
        mock_service.delete_rule.return_value = False

        response = client.delete("/v3/finance/auto-categorization/rules/nonexistent")

        assert response.status_code == 404

    def test_get_stats(self, client, mock_service):
        """Test endpoint statistiques."""
        response = client.get("/v3/finance/auto-categorization/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_rules" in data
        assert "active_rules" in data

    def test_get_patterns(self, client):
        """Test endpoint patterns par défaut."""
        response = client.get("/v3/finance/auto-categorization/patterns")

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) > 0

    def test_health_check(self, client):
        """Test health check."""
        response = client.get("/v3/finance/auto-categorization/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "finance-auto-categorization"


# =============================================================================
# TESTS ENUMS
# =============================================================================


class TestEnums:
    """Tests des enums."""

    def test_rule_types(self):
        """Test types de règles."""
        assert RuleType.KEYWORD.value == "keyword"
        assert RuleType.PATTERN.value == "pattern"
        assert RuleType.AMOUNT_RANGE.value == "amount_range"
        assert RuleType.VENDOR.value == "vendor"
        assert RuleType.IBAN.value == "iban"
        assert RuleType.COMBINED.value == "combined"

    def test_transaction_types(self):
        """Test types de transaction."""
        assert TransactionType.DEBIT.value == "debit"
        assert TransactionType.CREDIT.value == "credit"

    def test_match_confidence(self):
        """Test niveaux de confiance."""
        assert MatchConfidence.HIGH.value == "high"
        assert MatchConfidence.MEDIUM.value == "medium"
        assert MatchConfidence.LOW.value == "low"
        assert MatchConfidence.SUGGESTED.value == "suggested"


# =============================================================================
# TESTS DEFAULT PATTERNS
# =============================================================================


class TestDefaultPatterns:
    """Tests des patterns par défaut."""

    def test_salary_patterns_defined(self):
        """Test patterns salaire définis."""
        assert len(DefaultPatterns.SALARY) > 0

    def test_rent_patterns_defined(self):
        """Test patterns loyer définis."""
        assert len(DefaultPatterns.RENT) > 0

    def test_bank_fees_patterns_defined(self):
        """Test patterns frais bancaires définis."""
        assert len(DefaultPatterns.BANK_FEES) > 0

    def test_account_mapping_defined(self):
        """Test mapping comptes défini."""
        assert "salary" in DefaultPatterns.ACCOUNT_MAPPING
        assert "rent" in DefaultPatterns.ACCOUNT_MAPPING
        assert "bank_fees" in DefaultPatterns.ACCOUNT_MAPPING


# =============================================================================
# TESTS DATA CLASSES
# =============================================================================


class TestDataClasses:
    """Tests des classes de données."""

    def test_transaction_creation(self):
        """Test création Transaction."""
        trans = Transaction(
            id="test-001",
            label="Test transaction",
            amount=Decimal("100.00"),
            date=datetime.now(),
            transaction_type=TransactionType.DEBIT,
        )
        assert trans.id == "test-001"
        assert trans.transaction_type == TransactionType.DEBIT

    def test_categorization_rule_creation(self):
        """Test création CategorizationRule."""
        rule = CategorizationRule(
            id="rule-001",
            tenant_id="test",
            name="Test rule",
            rule_type=RuleType.KEYWORD,
        )
        assert rule.id == "rule-001"
        assert rule.is_active is True

    def test_category_suggestion_creation(self):
        """Test création CategorySuggestion."""
        suggestion = CategorySuggestion(
            account_code="641100",
            account_name="Salaires",
            confidence=90.0,
        )
        assert suggestion.account_code == "641100"

    def test_categorization_result_success(self):
        """Test CategorizationResult succès."""
        result = CategorizationResult(
            success=True,
            transaction_id="trans-001",
            suggestions=[],
        )
        assert result.success is True

    def test_categorization_result_failure(self):
        """Test CategorizationResult échec."""
        result = CategorizationResult(
            success=False,
            error="Erreur de traitement",
        )
        assert result.success is False
        assert result.error is not None
