"""
Pytest fixtures for accounting module tests.

Provides reusable test fixtures following CORE SaaS v2 patterns:
- Test client configuration
- Mock SaaSContext with tenant isolation
- Sample data dictionaries for all entities
- Helper utilities for assertions
"""

import pytest
from datetime import datetime, date, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient

from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext, UserRole
from app.main import app


# ===========================
# Client and Auth
# ===========================

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def tenant_id():
    """Test tenant ID."""
    return "tenant-test-001"


@pytest.fixture
def user_id():
    """Test user ID."""
    return "user-test-001"


@pytest.fixture
def auth_headers():
    """Authentication headers for requests."""
    return {"Authorization": "Bearer test-token"}


# ===========================
# SaaSContext Mock
# ===========================

@pytest.fixture(autouse=True)
def mock_saas_context(monkeypatch, tenant_id, user_id):
    """
    Mock SaaSContext for all tests.

    Automatically applied to all tests via autouse=True.
    Provides a tenant-scoped admin context with full permissions.
    """
    def mock_get_context():
        return SaaSContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=UserRole.ADMIN,
            permissions={"accounting.*"},
            scope="tenant",
            session_id="session-test",
            ip_address="127.0.0.1",
            user_agent="pytest",
            correlation_id="test-correlation"
        )

    from app.modules.accounting import router_v2
    monkeypatch.setattr(router_v2, "get_saas_context", mock_get_context)
    return mock_get_context


# ===========================
# Fiscal Year Fixtures
# ===========================

@pytest.fixture
def sample_fiscal_year_data():
    """Base fiscal year data for creation."""
    return {
        "name": "Exercice 2024",
        "code": "FY2024",
        "start_date": str(date(2024, 1, 1)),
        "end_date": str(date(2024, 12, 31)),
        "status": "OPEN"
    }


@pytest.fixture
def sample_fiscal_year(sample_fiscal_year_data, tenant_id):
    """Complete fiscal year entity with metadata."""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        **sample_fiscal_year_data,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_fiscal_year_closed(sample_fiscal_year):
    """Closed fiscal year for testing lifecycle."""
    return {
        **sample_fiscal_year,
        "status": "CLOSED",
        "closed_at": datetime.now().isoformat()
    }


# ===========================
# Chart of Accounts Fixtures
# ===========================

@pytest.fixture
def sample_account_data():
    """Base account data for creation."""
    return {
        "number": "401000",
        "name": "Fournisseurs",
        "type": "LIABILITY",
        "class": "4",
        "description": "Compte fournisseurs généraux",
        "is_active": True
    }


@pytest.fixture
def sample_account(sample_account_data, tenant_id):
    """Complete account entity with metadata."""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        **sample_account_data,
        "balance": 0.0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_accounts_list(tenant_id):
    """List of multiple accounts for testing filters."""
    accounts = []
    account_configs = [
        ("512000", "Banque", "ASSET", "5"),
        ("401000", "Fournisseurs", "LIABILITY", "4"),
        ("707000", "Ventes", "REVENUE", "7"),
        ("601000", "Achats", "EXPENSE", "6"),
    ]

    for number, name, acc_type, acc_class in account_configs:
        accounts.append({
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "number": number,
            "name": name,
            "type": acc_type,
            "class": acc_class,
            "is_active": True,
            "balance": 0.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })

    return accounts


# ===========================
# Journal Entry Fixtures
# ===========================

@pytest.fixture
def sample_journal_entry_line():
    """Single journal entry line."""
    return {
        "account_id": str(uuid4()),
        "account_number": "512000",
        "label": "Paiement fournisseur",
        "debit": 1000.0,
        "credit": 0.0
    }


@pytest.fixture
def sample_journal_entry_data(sample_journal_entry_line):
    """Base journal entry data for creation."""
    return {
        "date": str(date.today()),
        "journal_code": "BQ",
        "reference": "BQ2024-001",
        "description": "Paiement fournisseur XYZ",
        "fiscal_year_id": str(uuid4()),
        "period": 1,
        "status": "DRAFT",
        "lines": [
            sample_journal_entry_line,
            {
                "account_id": str(uuid4()),
                "account_number": "401000",
                "label": "Paiement fournisseur",
                "debit": 0.0,
                "credit": 1000.0
            }
        ]
    }


@pytest.fixture
def sample_journal_entry(sample_journal_entry_data, tenant_id):
    """Complete journal entry entity with metadata."""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        **sample_journal_entry_data,
        "total_debit": 1000.0,
        "total_credit": 1000.0,
        "is_balanced": True,
        "created_by": "user-test-001",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_journal_entry_posted(sample_journal_entry):
    """Posted journal entry for testing workflows."""
    return {
        **sample_journal_entry,
        "status": "POSTED",
        "posted_at": datetime.now().isoformat(),
        "posted_by": "user-test-001"
    }


@pytest.fixture
def sample_journal_entry_validated(sample_journal_entry_posted):
    """Validated journal entry for testing workflows."""
    return {
        **sample_journal_entry_posted,
        "status": "VALIDATED",
        "validated_at": datetime.now().isoformat(),
        "validated_by": "user-test-001"
    }


# ===========================
# Ledger Fixtures
# ===========================

@pytest.fixture
def sample_ledger_entry():
    """Sample ledger entry."""
    return {
        "date": str(date.today()),
        "journal_code": "BQ",
        "reference": "BQ2024-001",
        "description": "Paiement fournisseur XYZ",
        "account_number": "512000",
        "account_name": "Banque",
        "debit": 1000.0,
        "credit": 0.0,
        "balance": 1000.0,
        "journal_entry_id": str(uuid4())
    }


@pytest.fixture
def sample_ledger_data(sample_ledger_entry):
    """Complete ledger response data."""
    return {
        "entries": [sample_ledger_entry],
        "total_debit": 1000.0,
        "total_credit": 0.0,
        "balance": 1000.0,
        "count": 1
    }


# ===========================
# Balance Fixtures
# ===========================

@pytest.fixture
def sample_balance_item():
    """Sample balance item."""
    return {
        "account_number": "512000",
        "account_name": "Banque",
        "account_type": "ASSET",
        "account_class": "5",
        "debit": 10000.0,
        "credit": 5000.0,
        "balance": 5000.0
    }


@pytest.fixture
def sample_balance_data(sample_balance_item):
    """Complete balance response data."""
    return {
        "items": [sample_balance_item],
        "total_debit": 10000.0,
        "total_credit": 5000.0,
        "is_balanced": True,
        "fiscal_year_id": str(uuid4()),
        "period": None,
        "generated_at": datetime.now().isoformat()
    }


# ===========================
# Summary Fixtures
# ===========================

@pytest.fixture
def sample_accounting_summary():
    """Accounting module summary data."""
    return {
        "fiscal_years": {
            "total": 3,
            "open": 1,
            "closed": 2
        },
        "accounts": {
            "total": 150,
            "active": 145,
            "by_type": {
                "ASSET": 50,
                "LIABILITY": 30,
                "EQUITY": 10,
                "REVENUE": 30,
                "EXPENSE": 30
            }
        },
        "journal_entries": {
            "total": 1250,
            "draft": 15,
            "posted": 1200,
            "validated": 35,
            "current_month": 85
        },
        "balance": {
            "total_debit": 1500000.0,
            "total_credit": 1500000.0,
            "is_balanced": True
        }
    }


# ===========================
# Helper Utilities
# ===========================

@pytest.fixture
def assert_fiscal_year_structure():
    """Helper to assert fiscal year response structure."""
    def _assert(data):
        assert "id" in data
        assert "tenant_id" in data
        assert "name" in data
        assert "code" in data
        assert "start_date" in data
        assert "end_date" in data
        assert "status" in data
        assert "created_at" in data
        assert "updated_at" in data
    return _assert


@pytest.fixture
def assert_account_structure():
    """Helper to assert account response structure."""
    def _assert(data):
        assert "id" in data
        assert "tenant_id" in data
        assert "number" in data
        assert "name" in data
        assert "type" in data
        assert "class" in data
        assert "is_active" in data
        assert "balance" in data
        assert "created_at" in data
        assert "updated_at" in data
    return _assert


@pytest.fixture
def assert_journal_entry_structure():
    """Helper to assert journal entry response structure."""
    def _assert(data):
        assert "id" in data
        assert "tenant_id" in data
        assert "date" in data
        assert "journal_code" in data
        assert "reference" in data
        assert "description" in data
        assert "status" in data
        assert "lines" in data
        assert isinstance(data["lines"], list)
        assert "total_debit" in data
        assert "total_credit" in data
        assert "is_balanced" in data
        assert "created_at" in data
        assert "updated_at" in data
    return _assert


@pytest.fixture
def assert_tenant_isolation():
    """Helper to assert tenant isolation in responses."""
    def _assert(data, expected_tenant_id):
        if isinstance(data, dict):
            if "tenant_id" in data:
                assert data["tenant_id"] == expected_tenant_id
            if "items" in data:
                for item in data["items"]:
                    assert item["tenant_id"] == expected_tenant_id
        elif isinstance(data, list):
            for item in data:
                assert item["tenant_id"] == expected_tenant_id
    return _assert
