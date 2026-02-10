"""
Configuration pytest pour le module Automated Accounting v2
============================================================

Fixtures réutilisables pour les tests du module.
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock
from uuid import UUID, uuid4

import pytest

from app.core.saas_context import SaaSContext, TenantScope, UserRole


# ============================================================================
# MOCK SAAS CONTEXT
# ============================================================================

@pytest.fixture
def mock_saas_context():
    """Mock SaaSContext pour les tests."""
    return SaaSContext(
        tenant_id="test-tenant-123",
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        role=UserRole.ADMIN,
        permissions={"accounting.document.read", "accounting.document.write"},
        scope=TenantScope.TENANT,
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        correlation_id="test-correlation-id",
        timestamp=datetime.utcnow()
    )


@pytest.fixture
def mock_dirigeant_context():
    """Mock SaaSContext pour un dirigeant."""
    return SaaSContext(
        tenant_id="test-tenant-123",
        user_id=UUID("22345678-1234-5678-1234-567812345678"),
        role=UserRole.DIRIGEANT,
        permissions={"accounting.*"},
        scope=TenantScope.TENANT,
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        correlation_id="test-correlation-id",
        timestamp=datetime.utcnow()
    )


@pytest.fixture
def mock_expert_context():
    """Mock SaaSContext pour un expert-comptable."""
    return SaaSContext(
        tenant_id="test-tenant-123",
        user_id=UUID("32345678-1234-5678-1234-567812345678"),
        role=UserRole.COMPTABLE,
        permissions={"accounting.*"},
        scope=TenantScope.TENANT,
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        correlation_id="test-correlation-id",
        timestamp=datetime.utcnow()
    )


# ============================================================================
# MOCK SERVICES
# ============================================================================

@pytest.fixture
def mock_document_service():
    """Mock DocumentService."""
    service = Mock()
    service.list_documents = Mock(return_value=([], 0))
    service.get_document = Mock(return_value=None)
    service.create_document = Mock()
    service.update_document = Mock()
    service.validate_document = Mock()
    service.reject_document = Mock()
    service.delete_document = Mock(return_value=True)
    service.bulk_validate = Mock(return_value={"validated": 0, "failed": 0})
    service.get_documents_for_validation = Mock(return_value=[])
    service.get_document_stats = Mock(return_value={})
    return service


@pytest.fixture
def mock_dashboard_service():
    """Mock DashboardService."""
    service = Mock()
    service.get_dirigeant_dashboard = Mock()
    service.get_assistante_dashboard = Mock()
    service.get_expert_comptable_dashboard = Mock()
    return service


@pytest.fixture
def mock_bank_service():
    """Mock BankPullService."""
    service = Mock()
    service.get_connections = Mock(return_value=[])
    service.create_connection = Mock()
    service.delete_connection = Mock()
    service.sync_connection = Mock()
    service.sync_all = Mock(return_value=[])
    service.get_synced_accounts = Mock(return_value=[])
    service.get_transactions = Mock(return_value=([], 0))
    return service


@pytest.fixture
def mock_reconciliation_service():
    """Mock ReconciliationService."""
    service = Mock()
    service.auto_reconcile_all = Mock(return_value={"matched": 0, "unmatched": 0})
    service.manual_reconcile = Mock()
    service.get_rules = Mock(return_value=[])
    service.create_rule = Mock()
    service.get_reconciliation_stats = Mock(return_value={})
    return service


@pytest.fixture
def mock_auto_accounting_service():
    """Mock AutoAccountingService."""
    service = Mock()
    service.get_pending_entries = Mock(return_value=([], 0))
    service.validate_entry = Mock()
    return service


# ============================================================================
# DATA FIXTURES
# ============================================================================

@pytest.fixture
def document_data():
    """Document test data."""
    return {
        "id": uuid4(),
        "tenant_id": "test-tenant-123",
        "document_type": "INVOICE_RECEIVED",
        "status": "RECEIVED",
        "source": "UPLOAD",
        "reference": "INV-2024-001",
        "partner_name": "Fournisseur Test",
        "amount_untaxed": Decimal("100.00"),
        "amount_tax": Decimal("20.00"),
        "amount_total": Decimal("120.00"),
        "document_date": date(2024, 1, 15),
        "due_date": date(2024, 2, 15),
        "payment_status": "UNPAID",
        "ai_confidence": "HIGH",
        "ai_confidence_score": Decimal("95.5"),
        "requires_validation": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "received_at": datetime.utcnow()
    }


@pytest.fixture
def bank_connection_data():
    """Bank connection test data."""
    return {
        "id": uuid4(),
        "tenant_id": "test-tenant-123",
        "institution_id": "bnp_paribas",
        "institution_name": "BNP Paribas",
        "provider": "mock",
        "status": "ACTIVE",
        "connection_id": "mock_conn_123",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def transaction_data():
    """Transaction test data."""
    return {
        "id": uuid4(),
        "tenant_id": "test-tenant-123",
        "external_transaction_id": "txn_123",
        "transaction_date": date(2024, 1, 15),
        "amount": Decimal("-120.00"),
        "currency": "EUR",
        "description": "ACHAT FOURNITURES",
        "merchant_name": "AMAZON",
        "reconciliation_status": "PENDING",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def rule_data():
    """Reconciliation rule test data."""
    return {
        "id": uuid4(),
        "tenant_id": "test-tenant-123",
        "name": "Règle Amazon",
        "description": "Auto-rapprochement achats Amazon",
        "match_criteria": {
            "description_patterns": ["amazon"],
            "amount_min": 10,
            "amount_max": 1000
        },
        "auto_reconcile": True,
        "min_confidence": Decimal("85"),
        "default_account_code": "607000",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def alert_data():
    """Alert test data."""
    return {
        "id": uuid4(),
        "tenant_id": "test-tenant-123",
        "alert_type": "LOW_CONFIDENCE",
        "severity": "WARNING",
        "title": "Confiance IA faible",
        "message": "Le document a un score de confiance de 45%",
        "is_read": False,
        "is_resolved": False,
        "created_at": datetime.utcnow()
    }


# ============================================================================
# DASHBOARD DATA FIXTURES
# ============================================================================

@pytest.fixture
def dirigeant_dashboard():
    """Dashboard dirigeant mock data."""
    return {
        "cash_position": {
            "total_balance": Decimal("50000.00"),
            "available_balance": Decimal("48000.00"),
            "currency": "EUR",
            "accounts": [
                {"name": "Compte Courant", "balance": 50000.00, "currency": "EUR"}
            ],
            "last_sync_at": datetime.utcnow(),
            "freshness_score": Decimal("100")
        },
        "cash_forecast": {
            "current_balance": Decimal("50000.00"),
            "forecast_items": [],
            "period_start": date.today(),
            "period_end": date.today(),
            "warning_threshold": Decimal("5000"),
            "alert_threshold": Decimal("0")
        },
        "invoices_summary": {
            "to_pay_count": 5,
            "to_pay_amount": Decimal("15000.00"),
            "overdue_to_pay_count": 2,
            "overdue_to_pay_amount": Decimal("5000.00"),
            "to_collect_count": 8,
            "to_collect_amount": Decimal("25000.00"),
            "overdue_to_collect_count": 1,
            "overdue_to_collect_amount": Decimal("3000.00")
        },
        "result_summary": {
            "revenue": Decimal("100000.00"),
            "expenses": Decimal("75000.00"),
            "result": Decimal("25000.00"),
            "period": "MONTH",
            "period_start": date.today().replace(day=1),
            "period_end": date.today()
        },
        "alerts": [],
        "data_freshness": Decimal("100"),
        "last_updated": datetime.utcnow()
    }


@pytest.fixture
def assistante_dashboard():
    """Dashboard assistante mock data."""
    return {
        "total_documents": 45,
        "documents_by_status": {
            "received": 5,
            "processing": 3,
            "analyzed": 10,
            "pending_validation": 12,
            "validated": 8,
            "accounted": 5,
            "rejected": 2,
            "error": 0
        },
        "documents_by_type": {
            "invoice_received": 20,
            "invoice_sent": 15,
            "expense_note": 8,
            "credit_note_received": 1,
            "credit_note_sent": 1,
            "quote": 0,
            "purchase_order": 0,
            "other": 0
        },
        "recent_documents": [],
        "alerts": [],
        "last_updated": datetime.utcnow()
    }


@pytest.fixture
def expert_dashboard():
    """Dashboard expert mock data."""
    return {
        "validation_queue": {
            "items": [],
            "total": 12,
            "high_priority_count": 3,
            "medium_priority_count": 5,
            "low_priority_count": 4
        },
        "ai_performance": {
            "total_processed": 150,
            "auto_validated_count": 120,
            "auto_validated_rate": Decimal("80.00"),
            "corrections_count": 15,
            "corrections_rate": Decimal("10.00"),
            "average_confidence": Decimal("87.50"),
            "by_document_type": {}
        },
        "reconciliation_stats": {
            "total_transactions": 200,
            "matched_auto": 150,
            "matched_manual": 30,
            "unmatched": 20,
            "match_rate": Decimal("90.00")
        },
        "unresolved_alerts": [],
        "periods_status": [],
        "last_updated": datetime.utcnow()
    }


# ============================================================================
# HELPER ASSERTIONS
# ============================================================================

def assert_response_structure(response, expected_keys):
    """Vérifie que la réponse contient les clés attendues."""
    assert response.status_code == 200
    data = response.json()
    for key in expected_keys:
        assert key in data, f"Key '{key}' not found in response"


def assert_pagination(response, expected_total=None):
    """Vérifie la structure de pagination."""
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    if expected_total is not None:
        assert data["total"] == expected_total


def assert_error_response(response, expected_status, expected_detail=None):
    """Vérifie une réponse d'erreur."""
    assert response.status_code == expected_status
    if expected_detail:
        data = response.json()
        assert "detail" in data
        assert expected_detail in data["detail"]
