"""
Tests pour le module Finance Integration.

Coverage:
- Service: mappings, sync, validation
- Router: tous les endpoints
- Validation: tenant isolation
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.modules.finance.integration.service import (
    FinanceIntegrationService,
    IntegrationMapping,
    SyncResult,
    SyncDirection,
    SyncStatus,
    MappingType,
    TransactionType,
    FinanceTransaction,
    AccountingEntry,
    DefaultMappings,
)
from app.modules.finance.integration.router import router


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
    return "tenant-integ-test-123"


@pytest.fixture
def service(db_session, tenant_id):
    """Service d'intégration."""
    return FinanceIntegrationService(db=db_session, tenant_id=tenant_id)


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

    from app.modules.finance.integration.router import (
        get_integration_service,
        get_saas_context,
    )

    test_app.dependency_overrides[get_integration_service] = override_service
    test_app.dependency_overrides[get_saas_context] = override_context

    return test_app


@pytest.fixture
def client(app):
    """Client de test."""
    return TestClient(app)


@pytest.fixture
def sample_transaction(tenant_id):
    """Transaction financière de test."""
    return FinanceTransaction(
        id="tx-test-001",
        tenant_id=tenant_id,
        transaction_type=TransactionType.PAYMENT,
        date=datetime.now(),
        amount=Decimal("150.00"),
        currency="EUR",
        description="Paiement fournisseur",
        bank_account="current_account",
        category="purchases",
        reference="PAY-001",
    )


@pytest.fixture
def sample_entry(tenant_id):
    """Écriture comptable de test."""
    return AccountingEntry(
        id="entry-test-001",
        tenant_id=tenant_id,
        journal_code="BQ",
        date=datetime.now(),
        reference="BQ-001",
        description="Écriture test",
        debit_account="607000",
        credit_account="512100",
        amount=Decimal("150.00"),
        currency="EUR",
    )


# =============================================================================
# TESTS SERVICE - INITIALIZATION
# =============================================================================


class TestServiceInit:
    """Tests d'initialisation du service."""

    def test_init_with_tenant_id(self, db_session, tenant_id):
        """Service s'initialise avec tenant_id."""
        service = FinanceIntegrationService(db=db_session, tenant_id=tenant_id)
        assert service.tenant_id == tenant_id

    def test_init_requires_tenant_id(self, db_session):
        """Service requiert tenant_id."""
        with pytest.raises(ValueError, match="tenant_id est requis"):
            FinanceIntegrationService(db=db_session, tenant_id="")

    def test_init_creates_default_mappings(self, service):
        """Les mappings par défaut sont créés."""
        # Vérifier qu'il y a des mappings
        assert len(service._mappings) > 0


# =============================================================================
# TESTS SERVICE - MAPPINGS
# =============================================================================


class TestMappings:
    """Tests de gestion des mappings."""

    @pytest.mark.asyncio
    async def test_create_mapping(self, service):
        """Création d'un mapping."""
        mapping = await service.create_mapping(
            mapping_type=MappingType.ACCOUNT,
            source_code="custom_account",
            target_code="614000",
            source_system="finance",
            target_system="accounting",
            description="Compte personnalisé",
        )

        assert mapping.source_code == "custom_account"
        assert mapping.target_code == "614000"
        assert mapping.mapping_type == MappingType.ACCOUNT

    @pytest.mark.asyncio
    async def test_get_mapping(self, service):
        """Récupération d'un mapping."""
        await service.create_mapping(
            mapping_type=MappingType.ACCOUNT,
            source_code="test_get",
            target_code="999000",
            source_system="finance",
            target_system="accounting",
        )

        mapping = await service.get_mapping(
            MappingType.ACCOUNT,
            "test_get",
            "finance",
        )

        assert mapping is not None
        assert mapping.target_code == "999000"

    @pytest.mark.asyncio
    async def test_list_mappings(self, service):
        """Liste des mappings."""
        mappings = await service.list_mappings()
        assert len(mappings) > 0

    @pytest.mark.asyncio
    async def test_list_mappings_by_type(self, service):
        """Liste filtrée par type."""
        mappings = await service.list_mappings(mapping_type=MappingType.ACCOUNT)
        assert all(m.mapping_type == MappingType.ACCOUNT for m in mappings)

    @pytest.mark.asyncio
    async def test_delete_mapping(self, service):
        """Suppression d'un mapping."""
        mapping = await service.create_mapping(
            mapping_type=MappingType.ACCOUNT,
            source_code="to_delete",
            target_code="000000",
            source_system="finance",
            target_system="accounting",
        )

        success = await service.delete_mapping(mapping.id)
        assert success

        # Vérifier suppression
        result = await service.get_mapping(
            MappingType.ACCOUNT,
            "to_delete",
            "finance",
        )
        assert result is None

    def test_resolve_mapping(self, service):
        """Résolution d'un mapping."""
        # current_account devrait être mappé par défaut
        target = service.resolve_mapping(
            MappingType.ACCOUNT,
            "current_account",
        )
        assert target == "512100"

    def test_resolve_mapping_not_found(self, service):
        """Mapping non trouvé."""
        target = service.resolve_mapping(
            MappingType.ACCOUNT,
            "nonexistent_account",
        )
        assert target is None


# =============================================================================
# TESTS SERVICE - SYNC TO ACCOUNTING
# =============================================================================


class TestSyncToAccounting:
    """Tests de synchronisation vers comptabilité."""

    @pytest.mark.asyncio
    async def test_sync_single_transaction(self, service, sample_transaction):
        """Synchronisation d'une transaction."""
        result = await service.sync_to_accounting([sample_transaction])

        assert result.success
        assert result.status == SyncStatus.COMPLETED
        assert result.records_processed == 1
        assert result.records_created == 1
        assert len(result.entries) == 1

    @pytest.mark.asyncio
    async def test_sync_multiple_transactions(self, service, tenant_id):
        """Synchronisation de plusieurs transactions."""
        transactions = [
            FinanceTransaction(
                id=f"tx-{i}",
                tenant_id=tenant_id,
                transaction_type=TransactionType.PAYMENT,
                date=datetime.now(),
                amount=Decimal("100.00"),
                currency="EUR",
                description=f"Transaction {i}",
            )
            for i in range(5)
        ]

        result = await service.sync_to_accounting(transactions)

        assert result.success
        assert result.records_processed == 5
        assert result.records_created == 5

    @pytest.mark.asyncio
    async def test_sync_skips_different_tenant(self, service, tenant_id):
        """Transactions d'un autre tenant ignorées."""
        tx = FinanceTransaction(
            id="tx-other",
            tenant_id="other-tenant",
            transaction_type=TransactionType.PAYMENT,
            date=datetime.now(),
            amount=Decimal("100.00"),
            currency="EUR",
            description="Other tenant",
        )

        result = await service.sync_to_accounting([tx])

        assert result.records_skipped == 1
        assert result.records_created == 0

    @pytest.mark.asyncio
    async def test_sync_generates_correct_entry(self, service, sample_transaction):
        """Entrée comptable correctement générée."""
        result = await service.sync_to_accounting([sample_transaction])

        entry = result.entries[0]
        assert entry.journal_code == "BQ"
        assert entry.amount == sample_transaction.amount
        assert entry.source_transaction_id == sample_transaction.id


# =============================================================================
# TESTS SERVICE - SYNC FROM ACCOUNTING
# =============================================================================


class TestSyncFromAccounting:
    """Tests d'import depuis comptabilité."""

    @pytest.mark.asyncio
    async def test_import_entry(self, service, sample_entry):
        """Import d'une écriture."""
        result = await service.sync_from_accounting([sample_entry])

        assert result.success
        assert result.status == SyncStatus.COMPLETED
        assert result.records_processed == 1
        assert result.records_created == 1

    @pytest.mark.asyncio
    async def test_import_multiple_entries(self, service, tenant_id):
        """Import de plusieurs écritures."""
        entries = [
            AccountingEntry(
                id=f"entry-{i}",
                tenant_id=tenant_id,
                journal_code="BQ",
                date=datetime.now(),
                reference=f"REF-{i}",
                description=f"Écriture {i}",
                debit_account="512100",
                credit_account="411000",
                amount=Decimal("200.00"),
                currency="EUR",
            )
            for i in range(3)
        ]

        result = await service.sync_from_accounting(entries)

        assert result.success
        assert result.records_created == 3


# =============================================================================
# TESTS SERVICE - INVOICE PAYMENT
# =============================================================================


class TestInvoicePayment:
    """Tests de synchronisation des paiements factures."""

    @pytest.mark.asyncio
    async def test_sync_invoice_payment(self, service):
        """Synchronisation d'un paiement."""
        result = await service.sync_invoice_payment(
            invoice_id="inv-001",
            payment_amount=Decimal("500.00"),
            payment_date=datetime.now(),
            payment_method="bank_transfer",
        )

        assert result.success
        assert len(result.entries) == 1
        assert result.entries[0].description.startswith("Règlement")


# =============================================================================
# TESTS SERVICE - VALIDATION
# =============================================================================


class TestValidation:
    """Tests de validation."""

    @pytest.mark.asyncio
    async def test_validate_balance(self, service):
        """Validation de l'équilibre."""
        result = await service.validate_balance(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 12, 31),
        )

        assert result.is_valid
        assert "finance_total" in result.details
        assert "accounting_total" in result.details

    @pytest.mark.asyncio
    async def test_validate_entries_valid(self, service, sample_entry):
        """Validation d'écritures valides."""
        result = await service.validate_entries([sample_entry])

        assert result.is_valid
        assert result.details["entries_checked"] == 1

    @pytest.mark.asyncio
    async def test_validate_entries_invalid(self, service, tenant_id):
        """Validation d'écritures invalides."""
        invalid_entry = AccountingEntry(
            id="invalid-001",
            tenant_id=tenant_id,
            journal_code="",
            date=datetime.now(),
            reference="",
            description="",
            debit_account="",
            credit_account="",
            amount=Decimal("-100"),  # Montant négatif
            currency="EUR",
        )

        result = await service.validate_entries([invalid_entry])

        assert not result.is_valid
        assert len(result.errors) > 0


# =============================================================================
# TESTS SERVICE - HISTORY & STATS
# =============================================================================


class TestHistoryAndStats:
    """Tests historique et statistiques."""

    @pytest.mark.asyncio
    async def test_get_sync_history(self, service, sample_transaction):
        """Récupération de l'historique."""
        # Effectuer une sync
        await service.sync_to_accounting([sample_transaction])

        history = await service.get_sync_history()
        assert len(history) >= 1

    @pytest.mark.asyncio
    async def test_get_sync_result(self, service, sample_transaction):
        """Récupération d'un résultat spécifique."""
        result = await service.sync_to_accounting([sample_transaction])

        retrieved = await service.get_sync_result(result.sync_id)
        assert retrieved is not None
        assert retrieved.sync_id == result.sync_id

    @pytest.mark.asyncio
    async def test_get_integration_stats(self, service, sample_transaction):
        """Statistiques d'intégration."""
        await service.sync_to_accounting([sample_transaction])

        stats = await service.get_integration_stats()
        assert stats["total_syncs"] >= 1
        assert "mappings_count" in stats


# =============================================================================
# TESTS DEFAULT MAPPINGS
# =============================================================================


class TestDefaultMappings:
    """Tests des mappings par défaut."""

    def test_bank_accounts_defined(self):
        """Comptes bancaires définis."""
        assert "current_account" in DefaultMappings.BANK_ACCOUNTS
        assert "cash" in DefaultMappings.BANK_ACCOUNTS

    def test_journals_defined(self):
        """Journaux définis."""
        assert TransactionType.PAYMENT in DefaultMappings.JOURNALS
        assert TransactionType.RECEIPT in DefaultMappings.JOURNALS

    def test_categories_defined(self):
        """Catégories définies."""
        assert "revenue" in DefaultMappings.CATEGORIES
        assert "purchases" in DefaultMappings.CATEGORIES
        assert "bank_fees" in DefaultMappings.CATEGORIES


# =============================================================================
# TESTS ROUTER
# =============================================================================


class TestRouter:
    """Tests des endpoints."""

    def test_list_mappings(self, client):
        """GET /mappings."""
        response = client.get("/v3/finance/integration/mappings")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_mapping(self, client):
        """POST /mappings."""
        response = client.post(
            "/v3/finance/integration/mappings",
            json={
                "mapping_type": "account",
                "source_code": "new_account",
                "target_code": "888000",
                "source_system": "finance",
                "target_system": "accounting",
                "description": "Test mapping",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["source_code"] == "new_account"
        assert data["target_code"] == "888000"

    def test_delete_mapping(self, client):
        """DELETE /mappings/{id}."""
        # Créer d'abord
        create_response = client.post(
            "/v3/finance/integration/mappings",
            json={
                "mapping_type": "account",
                "source_code": "to_delete",
                "target_code": "000000",
                "source_system": "finance",
                "target_system": "accounting",
            }
        )
        mapping_id = create_response.json()["id"]

        response = client.delete(f"/v3/finance/integration/mappings/{mapping_id}")

        assert response.status_code == 200
        assert response.json()["success"]

    def test_resolve_mapping(self, client):
        """GET /mappings/resolve."""
        response = client.get(
            "/v3/finance/integration/mappings/resolve",
            params={
                "mapping_type": "account",
                "source_code": "current_account",
            }
        )

        assert response.status_code == 200
        assert response.json()["target_code"] == "512100"

    def test_sync_to_accounting(self, client):
        """POST /sync/to-accounting."""
        response = client.post(
            "/v3/finance/integration/sync/to-accounting",
            json={
                "transactions": [
                    {
                        "id": "tx-router-001",
                        "transaction_type": "payment",
                        "date": "2026-02-17T10:00:00",
                        "amount": "250.00",
                        "currency": "EUR",
                        "description": "Test paiement",
                    }
                ],
                "create_entries": True,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["records_created"] == 1

    def test_sync_from_accounting(self, client):
        """POST /sync/from-accounting."""
        response = client.post(
            "/v3/finance/integration/sync/from-accounting",
            json={
                "entries": [
                    {
                        "id": "entry-router-001",
                        "journal_code": "BQ",
                        "date": "2026-02-17T10:00:00",
                        "reference": "BQ-001",
                        "description": "Écriture import",
                        "debit_account": "512100",
                        "credit_account": "411000",
                        "amount": "300.00",
                    }
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"]

    def test_sync_invoice_payment(self, client):
        """POST /sync/invoice-payment."""
        response = client.post(
            "/v3/finance/integration/sync/invoice-payment",
            json={
                "invoice_id": "inv-router-001",
                "payment_amount": "1000.00",
                "payment_date": "2026-02-17T10:00:00",
                "payment_method": "bank_transfer",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert len(data["entries"]) == 1

    def test_validate_balance(self, client):
        """POST /validate/balance."""
        response = client.post(
            "/v3/finance/integration/validate/balance",
            json={
                "start_date": "2026-01-01T00:00:00",
                "end_date": "2026-12-31T23:59:59",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"]

    def test_validate_entries(self, client):
        """POST /validate/entries."""
        response = client.post(
            "/v3/finance/integration/validate/entries",
            json={
                "entries": [
                    {
                        "id": "valid-001",
                        "journal_code": "BQ",
                        "date": "2026-02-17T10:00:00",
                        "reference": "REF-001",
                        "description": "Valid entry",
                        "debit_account": "512100",
                        "credit_account": "411000",
                        "amount": "500.00",
                    }
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"]

    def test_get_history(self, client):
        """GET /history."""
        response = client.get("/v3/finance/integration/history")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_stats(self, client):
        """GET /stats."""
        response = client.get("/v3/finance/integration/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_syncs" in data
        assert "mappings_count" in data

    def test_health_check(self, client):
        """GET /health."""
        response = client.get("/v3/finance/integration/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "sync_to_accounting" in data["features"]


# =============================================================================
# TESTS ENUMS
# =============================================================================


class TestEnums:
    """Tests des enums."""

    def test_sync_direction_values(self):
        """Valeurs de SyncDirection."""
        assert SyncDirection.FINANCE_TO_ACCOUNTING.value == "finance_to_accounting"
        assert SyncDirection.ACCOUNTING_TO_FINANCE.value == "accounting_to_finance"

    def test_sync_status_values(self):
        """Valeurs de SyncStatus."""
        assert SyncStatus.COMPLETED.value == "completed"
        assert SyncStatus.FAILED.value == "failed"

    def test_mapping_type_values(self):
        """Valeurs de MappingType."""
        assert MappingType.ACCOUNT.value == "account"
        assert MappingType.JOURNAL.value == "journal"


# =============================================================================
# TESTS DATACLASSES
# =============================================================================


class TestDataClasses:
    """Tests des dataclasses."""

    def test_integration_mapping_creation(self, tenant_id):
        """Création IntegrationMapping."""
        mapping = IntegrationMapping(
            id="mapping-1",
            tenant_id=tenant_id,
            mapping_type=MappingType.ACCOUNT,
            source_code="test",
            target_code="999000",
            source_system="finance",
            target_system="accounting",
        )

        assert mapping.is_active
        assert mapping.priority == 0

    def test_accounting_entry_creation(self, tenant_id):
        """Création AccountingEntry."""
        entry = AccountingEntry(
            id="entry-1",
            tenant_id=tenant_id,
            journal_code="BQ",
            date=datetime.now(),
            reference="REF",
            description="Test",
            debit_account="512100",
            credit_account="411000",
            amount=Decimal("100"),
            currency="EUR",
        )

        assert entry.amount == Decimal("100")

    def test_finance_transaction_creation(self, tenant_id):
        """Création FinanceTransaction."""
        tx = FinanceTransaction(
            id="tx-1",
            tenant_id=tenant_id,
            transaction_type=TransactionType.PAYMENT,
            date=datetime.now(),
            amount=Decimal("500"),
            currency="EUR",
            description="Test payment",
        )

        assert tx.transaction_type == TransactionType.PAYMENT
