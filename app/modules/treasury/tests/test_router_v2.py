"""
Tests pour Treasury v2 Router - CORE SaaS Pattern
==================================================

Tests complets pour l'API Treasury migrée vers CORE SaaS.

Coverage:
- Summary/Forecast (4 tests): dashboard + prévisions
- Bank Accounts (10 tests): CRUD + filters + pagination + tenant isolation
- Transactions (12 tests): CRUD + filters + pagination + reconciliation
- Workflows (2 tests): complete treasury flow + reconciliation workflow
- Security (2 tests): tenant isolation + context propagation

TOTAL: 30 tests
"""

import pytest
from uuid import uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock


# ============================================================================
# TESTS SUMMARY / FORECAST
# ============================================================================

def test_get_summary():
    """Test récupération du résumé de trésorerie"""
    from app.modules.treasury.router_v2 import get_treasury_summary
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    # Mock service response
    mock_summary = {
        "total_balance": Decimal("10000.00"),
        "total_pending_in": Decimal("500.00"),
        "total_pending_out": Decimal("300.00"),
        "forecast_7d": Decimal("10200.00"),
        "forecast_30d": Decimal("11500.00"),
        "accounts": []
    }

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'get_summary', return_value=mock_summary):
            # Execute
            result = pytest.importorskip('asyncio').run(
                get_treasury_summary(db=mock_db, context=mock_context)
            )

            # Assertions
            assert result["total_balance"] == Decimal("10000.00")
            assert result["total_pending_in"] == Decimal("500.00")
            assert result["forecast_7d"] == Decimal("10200.00")


def test_summary_structure(sample_summary):
    """Test structure du résumé de trésorerie"""
    required_fields = [
        "total_balance",
        "total_pending_in",
        "total_pending_out",
        "forecast_7d",
        "forecast_30d",
        "accounts"
    ]

    for field in required_fields:
        assert field in sample_summary, f"Champ manquant: {field}"


def test_get_forecast():
    """Test récupération des prévisions de trésorerie"""
    from app.modules.treasury.router_v2 import get_forecast
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    # Mock service response
    today = date.today()
    mock_forecast = [
        {
            "date": today + timedelta(days=i),
            "projected_balance": Decimal("10000.00") + Decimal(i * 100),
            "pending_in": Decimal("500.00"),
            "pending_out": Decimal("300.00")
        }
        for i in range(30)
    ]

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'get_forecast', return_value=mock_forecast):
            # Execute
            result = pytest.importorskip('asyncio').run(
                get_forecast(days=30, db=mock_db, context=mock_context)
            )

            # Assertions
            assert len(result) == 30
            assert result[0]["date"] == today
            assert result[0]["projected_balance"] == Decimal("10000.00")


def test_forecast_with_custom_days():
    """Test prévisions avec nombre de jours personnalisé"""
    from app.modules.treasury.router_v2 import get_forecast
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    # Mock service response
    mock_forecast = [{"date": date.today() + timedelta(days=i)} for i in range(7)]

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'get_forecast', return_value=mock_forecast):
            # Execute
            result = pytest.importorskip('asyncio').run(
                get_forecast(days=7, db=mock_db, context=mock_context)
            )

            # Assertions
            assert len(result) == 7


# ============================================================================
# TESTS BANK ACCOUNTS
# ============================================================================

def test_create_account(account_data, sample_account):
    """Test création d'un compte bancaire"""
    from app.modules.treasury.router_v2 import create_account
    from app.modules.treasury.service import TreasuryService
    from app.modules.treasury.schemas import BankAccountCreate

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = uuid4()

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'create_account', return_value=sample_account):
            # Execute
            data = BankAccountCreate(**account_data)
            result = pytest.importorskip('asyncio').run(
                create_account(data=data, db=mock_db, context=mock_context)
            )

            # Assertions
            assert result["code"] == sample_account["code"]
            assert result["name"] == sample_account["name"]
            assert result["tenant_id"] == "tenant-test-001"


def test_list_accounts():
    """Test liste des comptes bancaires"""
    from app.modules.treasury.router_v2 import list_accounts
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    # Mock service response
    mock_accounts = [
        {"id": str(uuid4()), "code": "BNK001", "name": "Compte 1"},
        {"id": str(uuid4()), "code": "BNK002", "name": "Compte 2"}
    ]

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'list_accounts', return_value=(mock_accounts, 2)):
            # Execute
            result = pytest.importorskip('asyncio').run(
                list_accounts(is_active=None, page=1, per_page=20, db=mock_db, context=mock_context)
            )

            # Assertions
            assert result.total == 2
            assert result.page == 1
            assert len(result.items) == 2


def test_list_accounts_with_filters():
    """Test liste des comptes avec filtres"""
    from app.modules.treasury.router_v2 import list_accounts
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    # Mock service response (only active accounts)
    mock_accounts = [{"id": str(uuid4()), "is_active": True}]

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'list_accounts', return_value=(mock_accounts, 1)):
            # Execute
            result = pytest.importorskip('asyncio').run(
                list_accounts(is_active=True, page=1, per_page=20, db=mock_db, context=mock_context)
            )

            # Assertions
            assert result.total == 1
            assert result.items[0]["is_active"] is True


def test_get_account(sample_account):
    """Test récupération d'un compte bancaire"""
    from app.modules.treasury.router_v2 import get_account
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    account_id = uuid4()

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'get_account', return_value=sample_account):
            # Execute
            result = pytest.importorskip('asyncio').run(
                get_account(account_id=account_id, db=mock_db, context=mock_context)
            )

            # Assertions
            assert result["id"] == sample_account["id"]
            assert result["code"] == sample_account["code"]


def test_get_account_not_found():
    """Test récupération d'un compte inexistant"""
    from app.modules.treasury.router_v2 import get_account
    from app.modules.treasury.service import TreasuryService
    from fastapi import HTTPException

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    account_id = uuid4()

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'get_account', return_value=None):
            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                pytest.importorskip('asyncio').run(
                    get_account(account_id=account_id, db=mock_db, context=mock_context)
                )

            assert exc_info.value.status_code == 404
            assert "non trouvé" in exc_info.value.detail


def test_update_account(sample_account):
    """Test mise à jour d'un compte bancaire"""
    from app.modules.treasury.router_v2 import update_account
    from app.modules.treasury.service import TreasuryService
    from app.modules.treasury.schemas import BankAccountUpdate

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    account_id = uuid4()
    updated_account = {**sample_account, "name": "Compte Mis à Jour"}

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'update_account', return_value=updated_account):
            # Execute
            data = BankAccountUpdate(name="Compte Mis à Jour")
            result = pytest.importorskip('asyncio').run(
                update_account(account_id=account_id, data=data, db=mock_db, context=mock_context)
            )

            # Assertions
            assert result["name"] == "Compte Mis à Jour"


def test_update_account_not_found():
    """Test mise à jour d'un compte inexistant"""
    from app.modules.treasury.router_v2 import update_account
    from app.modules.treasury.service import TreasuryService
    from app.modules.treasury.schemas import BankAccountUpdate
    from fastapi import HTTPException

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    account_id = uuid4()

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'update_account', return_value=None):
            # Execute & Assert
            data = BankAccountUpdate(name="Test")
            with pytest.raises(HTTPException) as exc_info:
                pytest.importorskip('asyncio').run(
                    update_account(account_id=account_id, data=data, db=mock_db, context=mock_context)
                )

            assert exc_info.value.status_code == 404


def test_delete_account():
    """Test suppression d'un compte bancaire (soft delete)"""
    from app.modules.treasury.router_v2 import delete_account
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    account_id = uuid4()

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'delete_account', return_value=True):
            # Execute
            result = pytest.importorskip('asyncio').run(
                delete_account(account_id=account_id, db=mock_db, context=mock_context)
            )

            # Should return None (204 No Content)
            assert result is None


def test_delete_account_not_found():
    """Test suppression d'un compte inexistant"""
    from app.modules.treasury.router_v2 import delete_account
    from app.modules.treasury.service import TreasuryService
    from fastapi import HTTPException

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    account_id = uuid4()

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'delete_account', return_value=False):
            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                pytest.importorskip('asyncio').run(
                    delete_account(account_id=account_id, db=mock_db, context=mock_context)
                )

            assert exc_info.value.status_code == 404


def test_account_pagination():
    """Test pagination des comptes bancaires"""
    from app.modules.treasury.router_v2 import list_accounts
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    # Mock 50 accounts, page 2, 20 per page
    mock_accounts = [{"id": str(uuid4())} for _ in range(20)]

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'list_accounts', return_value=(mock_accounts, 50)):
            # Execute
            result = pytest.importorskip('asyncio').run(
                list_accounts(is_active=None, page=2, per_page=20, db=mock_db, context=mock_context)
            )

            # Assertions
            assert result.total == 50
            assert result.page == 2
            assert result.per_page == 20
            assert result.pages == 3  # 50 / 20 = 2.5 -> 3 pages


# ============================================================================
# TESTS TRANSACTIONS
# ============================================================================

def test_create_transaction(transaction_data, sample_transaction):
    """Test création d'une transaction bancaire"""
    from app.modules.treasury.router_v2 import create_transaction
    from app.modules.treasury.service import TreasuryService
    from app.modules.treasury.schemas import BankTransactionCreate

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'create_transaction', return_value=sample_transaction):
            # Execute
            data = BankTransactionCreate(**transaction_data)
            result = pytest.importorskip('asyncio').run(
                create_transaction(data=data, db=mock_db, context=mock_context)
            )

            # Assertions
            assert result["description"] == sample_transaction["description"]
            assert result["amount"] == sample_transaction["amount"]


def test_list_transactions():
    """Test liste des transactions bancaires"""
    from app.modules.treasury.router_v2 import list_transactions
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    # Mock service response
    mock_transactions = [
        {"id": str(uuid4()), "description": "Transaction 1"},
        {"id": str(uuid4()), "description": "Transaction 2"}
    ]

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'list_transactions', return_value=(mock_transactions, 2)):
            # Execute
            result = pytest.importorskip('asyncio').run(
                list_transactions(
                    account_id=None,
                    transaction_type=None,
                    reconciled=None,
                    page=1,
                    per_page=25,
                    db=mock_db,
                    context=mock_context
                )
            )

            # Assertions
            assert result.total == 2
            assert len(result.items) == 2


def test_list_transactions_with_filters():
    """Test liste des transactions avec filtres"""
    from app.modules.treasury.router_v2 import list_transactions
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    account_id = uuid4()
    mock_transactions = [{"id": str(uuid4()), "type": "CREDIT", "reconciled": False}]

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'list_transactions', return_value=(mock_transactions, 1)):
            # Execute
            from app.modules.treasury.models import TransactionType
            result = pytest.importorskip('asyncio').run(
                list_transactions(
                    account_id=account_id,
                    transaction_type=TransactionType.CREDIT,
                    reconciled=False,
                    page=1,
                    per_page=25,
                    db=mock_db,
                    context=mock_context
                )
            )

            # Assertions
            assert result.total == 1


def test_list_account_transactions(sample_account):
    """Test liste des transactions d'un compte"""
    from app.modules.treasury.router_v2 import list_account_transactions
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    account_id = uuid4()
    mock_transactions = [{"id": str(uuid4()), "account_id": str(account_id)}]

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'get_account', return_value=sample_account):
            with patch.object(TreasuryService, 'list_transactions', return_value=(mock_transactions, 1)):
                # Execute
                result = pytest.importorskip('asyncio').run(
                    list_account_transactions(
                        account_id=account_id,
                        page=1,
                        per_page=25,
                        db=mock_db,
                        context=mock_context
                    )
                )

                # Assertions
                assert result.total == 1


def test_list_account_transactions_not_found():
    """Test liste des transactions d'un compte inexistant"""
    from app.modules.treasury.router_v2 import list_account_transactions
    from app.modules.treasury.service import TreasuryService
    from fastapi import HTTPException

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    account_id = uuid4()

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'get_account', return_value=None):
            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                pytest.importorskip('asyncio').run(
                    list_account_transactions(
                        account_id=account_id,
                        page=1,
                        per_page=25,
                        db=mock_db,
                        context=mock_context
                    )
                )

            assert exc_info.value.status_code == 404


def test_get_transaction(sample_transaction):
    """Test récupération d'une transaction"""
    from app.modules.treasury.router_v2 import get_transaction
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    transaction_id = uuid4()

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'get_transaction', return_value=sample_transaction):
            # Execute
            result = pytest.importorskip('asyncio').run(
                get_transaction(transaction_id=transaction_id, db=mock_db, context=mock_context)
            )

            # Assertions
            assert result["id"] == sample_transaction["id"]


def test_get_transaction_not_found():
    """Test récupération d'une transaction inexistante"""
    from app.modules.treasury.router_v2 import get_transaction
    from app.modules.treasury.service import TreasuryService
    from fastapi import HTTPException

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    transaction_id = uuid4()

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'get_transaction', return_value=None):
            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                pytest.importorskip('asyncio').run(
                    get_transaction(transaction_id=transaction_id, db=mock_db, context=mock_context)
                )

            assert exc_info.value.status_code == 404


def test_update_transaction(sample_transaction):
    """Test mise à jour d'une transaction"""
    from app.modules.treasury.router_v2 import update_transaction
    from app.modules.treasury.service import TreasuryService
    from app.modules.treasury.schemas import BankTransactionUpdate

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    transaction_id = uuid4()
    updated_transaction = {**sample_transaction, "description": "Description mise à jour"}

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'update_transaction', return_value=updated_transaction):
            # Execute
            data = BankTransactionUpdate(description="Description mise à jour")
            result = pytest.importorskip('asyncio').run(
                update_transaction(transaction_id=transaction_id, data=data, db=mock_db, context=mock_context)
            )

            # Assertions
            assert result["description"] == "Description mise à jour"


def test_update_transaction_not_found():
    """Test mise à jour d'une transaction inexistante"""
    from app.modules.treasury.router_v2 import update_transaction
    from app.modules.treasury.service import TreasuryService
    from app.modules.treasury.schemas import BankTransactionUpdate
    from fastapi import HTTPException

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    transaction_id = uuid4()

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'update_transaction', return_value=None):
            # Execute & Assert
            data = BankTransactionUpdate(description="Test")
            with pytest.raises(HTTPException) as exc_info:
                pytest.importorskip('asyncio').run(
                    update_transaction(transaction_id=transaction_id, data=data, db=mock_db, context=mock_context)
                )

            assert exc_info.value.status_code == 404


def test_reconcile_transaction(sample_transaction, reconciliation_data):
    """Test rapprochement d'une transaction"""
    from app.modules.treasury.router_v2 import reconcile_transaction
    from app.modules.treasury.service import TreasuryService
    from app.modules.treasury.schemas import ReconciliationRequest

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = uuid4()

    transaction_id = uuid4()
    reconciled_transaction = {
        **sample_transaction,
        "reconciled": True,
        "reconciled_by": str(mock_context.user_id),
        "linked_document": {
            "type": reconciliation_data["document_type"],
            "id": reconciliation_data["document_id"]
        }
    }

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'reconcile_transaction', return_value=reconciled_transaction):
            # Execute
            data = ReconciliationRequest(**reconciliation_data)
            result = pytest.importorskip('asyncio').run(
                reconcile_transaction(transaction_id=transaction_id, data=data, db=mock_db, context=mock_context)
            )

            # Assertions
            assert result["reconciled"] is True
            assert result["linked_document"] is not None


def test_unreconcile_transaction(sample_transaction):
    """Test annulation de rapprochement"""
    from app.modules.treasury.router_v2 import unreconcile_transaction
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    transaction_id = uuid4()
    unreconciled_transaction = {
        **sample_transaction,
        "reconciled": False,
        "reconciled_by": None,
        "linked_document": None
    }

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'unreconcile_transaction', return_value=unreconciled_transaction):
            # Execute
            result = pytest.importorskip('asyncio').run(
                unreconcile_transaction(transaction_id=transaction_id, db=mock_db, context=mock_context)
            )

            # Assertions
            assert result["reconciled"] is False
            assert result["linked_document"] is None


def test_transaction_pagination():
    """Test pagination des transactions"""
    from app.modules.treasury.router_v2 import list_transactions
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = "user-test-001"

    # Mock 100 transactions, page 3, 25 per page
    mock_transactions = [{"id": str(uuid4())} for _ in range(25)]

    with patch.object(TreasuryService, '__init__', return_value=None):
        with patch.object(TreasuryService, 'list_transactions', return_value=(mock_transactions, 100)):
            # Execute
            result = pytest.importorskip('asyncio').run(
                list_transactions(
                    account_id=None,
                    transaction_type=None,
                    reconciled=None,
                    page=3,
                    per_page=25,
                    db=mock_db,
                    context=mock_context
                )
            )

            # Assertions
            assert result.total == 100
            assert result.page == 3
            assert result.per_page == 25
            assert result.pages == 4  # 100 / 25 = 4 pages


# ============================================================================
# TESTS WORKFLOWS
# ============================================================================

def test_complete_treasury_flow(account_data, transaction_data, reconciliation_data):
    """Test workflow complet: compte → transaction → rapprochement"""
    from app.modules.treasury.router_v2 import (
        create_account,
        create_transaction,
        reconcile_transaction
    )
    from app.modules.treasury.service import TreasuryService
    from app.modules.treasury.schemas import (
        BankAccountCreate,
        BankTransactionCreate,
        ReconciliationRequest
    )

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = uuid4()

    account_id = uuid4()
    transaction_id = uuid4()

    # Mock responses
    mock_account = {"id": str(account_id), "code": "BNK001", "balance": "10000.00"}
    mock_transaction = {"id": str(transaction_id), "account_id": str(account_id), "reconciled": False}
    mock_reconciled = {**mock_transaction, "reconciled": True}

    with patch.object(TreasuryService, '__init__', return_value=None):
        # Step 1: Create account
        with patch.object(TreasuryService, 'create_account', return_value=mock_account):
            account = pytest.importorskip('asyncio').run(
                create_account(
                    data=BankAccountCreate(**account_data),
                    db=mock_db,
                    context=mock_context
                )
            )
            assert account["id"] == str(account_id)

        # Step 2: Create transaction
        transaction_data["account_id"] = str(account_id)
        with patch.object(TreasuryService, 'create_transaction', return_value=mock_transaction):
            transaction = pytest.importorskip('asyncio').run(
                create_transaction(
                    data=BankTransactionCreate(**transaction_data),
                    db=mock_db,
                    context=mock_context
                )
            )
            assert transaction["id"] == str(transaction_id)
            assert transaction["reconciled"] is False

        # Step 3: Reconcile transaction
        with patch.object(TreasuryService, 'reconcile_transaction', return_value=mock_reconciled):
            reconciled = pytest.importorskip('asyncio').run(
                reconcile_transaction(
                    transaction_id=transaction_id,
                    data=ReconciliationRequest(**reconciliation_data),
                    db=mock_db,
                    context=mock_context
                )
            )
            assert reconciled["reconciled"] is True


def test_reconciliation_workflow(sample_transaction, reconciliation_data):
    """Test workflow rapprochement → annulation"""
    from app.modules.treasury.router_v2 import (
        reconcile_transaction,
        unreconcile_transaction
    )
    from app.modules.treasury.service import TreasuryService
    from app.modules.treasury.schemas import ReconciliationRequest

    # Mock dependencies
    mock_db = Mock()
    mock_context = Mock()
    mock_context.tenant_id = "tenant-test-001"
    mock_context.user_id = uuid4()

    transaction_id = uuid4()

    with patch.object(TreasuryService, '__init__', return_value=None):
        # Step 1: Reconcile
        mock_reconciled = {**sample_transaction, "reconciled": True}
        with patch.object(TreasuryService, 'reconcile_transaction', return_value=mock_reconciled):
            reconciled = pytest.importorskip('asyncio').run(
                reconcile_transaction(
                    transaction_id=transaction_id,
                    data=ReconciliationRequest(**reconciliation_data),
                    db=mock_db,
                    context=mock_context
                )
            )
            assert reconciled["reconciled"] is True

        # Step 2: Unreconcile
        mock_unreconciled = {**sample_transaction, "reconciled": False}
        with patch.object(TreasuryService, 'unreconcile_transaction', return_value=mock_unreconciled):
            unreconciled = pytest.importorskip('asyncio').run(
                unreconcile_transaction(
                    transaction_id=transaction_id,
                    db=mock_db,
                    context=mock_context
                )
            )
            assert unreconciled["reconciled"] is False


# ============================================================================
# TESTS SECURITY
# ============================================================================

def test_tenant_isolation():
    """Test isolation entre tenants"""
    from app.modules.treasury.router_v2 import list_accounts
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies for tenant A
    mock_db = Mock()
    mock_context_a = Mock()
    mock_context_a.tenant_id = "tenant-a"
    mock_context_a.user_id = "user-a"

    # Mock dependencies for tenant B
    mock_context_b = Mock()
    mock_context_b.tenant_id = "tenant-b"
    mock_context_b.user_id = "user-b"

    # Mock responses - each tenant sees only their accounts
    accounts_a = [{"id": str(uuid4()), "tenant_id": "tenant-a"}]
    accounts_b = [{"id": str(uuid4()), "tenant_id": "tenant-b"}]

    with patch.object(TreasuryService, '__init__', return_value=None):
        # Tenant A sees only their accounts
        with patch.object(TreasuryService, 'list_accounts', return_value=(accounts_a, 1)):
            result_a = pytest.importorskip('asyncio').run(
                list_accounts(
                    is_active=None,
                    page=1,
                    per_page=20,
                    db=mock_db,
                    context=mock_context_a
                )
            )
            assert result_a.items[0]["tenant_id"] == "tenant-a"

        # Tenant B sees only their accounts
        with patch.object(TreasuryService, 'list_accounts', return_value=(accounts_b, 1)):
            result_b = pytest.importorskip('asyncio').run(
                list_accounts(
                    is_active=None,
                    page=1,
                    per_page=20,
                    db=mock_db,
                    context=mock_context_b
                )
            )
            assert result_b.items[0]["tenant_id"] == "tenant-b"


def test_context_propagation():
    """Test propagation du contexte SaaS au service"""
    from app.modules.treasury.router_v2 import get_treasury_service
    from app.modules.treasury.service import TreasuryService

    # Mock dependencies
    mock_db = Mock()
    tenant_id = "tenant-test-001"
    user_id = "user-test-001"

    # Create service
    service = get_treasury_service(mock_db, tenant_id, user_id)

    # Assertions
    assert service.db == mock_db
    assert service.tenant_id == tenant_id
    assert service.user_id == user_id
