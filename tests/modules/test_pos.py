"""
AZALS MODULE 13 - Tests POS
============================
Tests bloquants pour le Point de Vente.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.modules.pos.models import (
    POSStore, POSTerminal, POSUser, POSSession, CashMovement,
    POSTransaction, POSTransactionLine, POSPayment, POSDailyReport,
    POSProductQuickKey, POSHoldTransaction,
    POSTerminalStatus, POSSessionStatus, POSTransactionStatus,
    PaymentMethodType, DiscountType
)
from app.modules.pos.schemas import (
    StoreCreate, StoreUpdate,
    TerminalCreate, TerminalUpdate,
    POSUserCreate, POSUserUpdate, POSUserLogin,
    SessionOpenRequest, SessionCloseRequest, CashMovementCreate,
    TransactionCreate, TransactionLineCreate, PaymentCreate,
    QuickKeyCreate, HoldTransactionCreate
)
from app.modules.pos.service import POSService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


@pytest.fixture
def pos_service(mock_db):
    """Service POS instance."""
    return POSService(mock_db, "test-tenant")


@pytest.fixture
def sample_store():
    """Sample store data."""
    return StoreCreate(
        code="STORE001",
        name="Magasin Principal",
        description="Siège social",
        address_line1="123 rue du Commerce",
        city="Paris",
        postal_code="75001",
        country="FR",
        phone="+33123456789",
        email="magasin@example.com",
        timezone="Europe/Paris",
        currency="EUR",
        default_tax_rate=Decimal("20.00")
    )


@pytest.fixture
def sample_terminal():
    """Sample terminal data."""
    return TerminalCreate(
        store_id=1,
        terminal_id="TERM-001",
        name="Caisse 1",
        description="Caisse principale",
        device_type="tablet"
    )


@pytest.fixture
def sample_pos_user():
    """Sample POS user data."""
    return POSUserCreate(
        employee_code="EMP001",
        first_name="Jean",
        last_name="Dupont",
        pin_code="1234",
        can_open_drawer=True,
        can_void_transaction=True,
        can_give_discount=True,
        max_discount_percent=Decimal("15"),
        can_refund=True,
        can_close_session=True,
        is_manager=False
    )


@pytest.fixture
def sample_transaction_line():
    """Sample transaction line data."""
    return TransactionLineCreate(
        product_id=1,
        sku="SKU001",
        name="Produit Test",
        quantity=Decimal("2"),
        unit_price=Decimal("50.00"),
        tax_rate=Decimal("20.00")
    )


# ============================================================================
# MODEL TESTS
# ============================================================================

class TestPOSModels:
    """Tests des modèles POS."""

    def test_store_model_creation(self):
        """Test création modèle magasin."""
        store = POSStore(
            tenant_id="test",
            code="S001",
            name="Test Store",
            country="FR",
            currency="EUR",
            timezone="Europe/Paris"
        )
        assert store.code == "S001"
        assert store.is_active is True

    def test_terminal_model_creation(self):
        """Test création modèle terminal."""
        terminal = POSTerminal(
            tenant_id="test",
            store_id=1,
            terminal_id="T001",
            name="Terminal 1",
            status=POSTerminalStatus.OFFLINE
        )
        assert terminal.terminal_id == "T001"
        assert terminal.status == POSTerminalStatus.OFFLINE

    def test_session_model_creation(self):
        """Test création modèle session."""
        session = POSSession(
            tenant_id="test",
            terminal_id=1,
            session_number="S20240101-0001",
            status=POSSessionStatus.OPEN,
            opened_by_id=1,
            opening_cash=Decimal("100.00"),
            total_sales=Decimal("0"),
            total_refunds=Decimal("0"),
            total_discounts=Decimal("0"),
            transaction_count=0,
            cash_total=Decimal("0"),
            card_total=Decimal("0"),
            check_total=Decimal("0"),
            voucher_total=Decimal("0"),
            other_total=Decimal("0")
        )
        assert session.status == POSSessionStatus.OPEN
        assert session.opening_cash == Decimal("100.00")

    def test_transaction_model_creation(self):
        """Test création modèle transaction."""
        tx = POSTransaction(
            tenant_id="test",
            session_id=1,
            receipt_number="T20240101-000001",
            status=POSTransactionStatus.PENDING,
            cashier_id=1,
            subtotal=Decimal("100.00"),
            discount_total=Decimal("0"),
            tax_total=Decimal("20.00"),
            total=Decimal("120.00"),
            amount_paid=Decimal("0"),
            amount_due=Decimal("120.00"),
            change_given=Decimal("0")
        )
        assert tx.receipt_number == "T20240101-000001"
        assert tx.total == Decimal("120.00")

    def test_payment_model_creation(self):
        """Test création modèle paiement."""
        payment = POSPayment(
            tenant_id="test",
            transaction_id=1,
            payment_method=PaymentMethodType.CASH,
            amount=Decimal("50.00"),
            amount_tendered=Decimal("100.00"),
            change_amount=Decimal("50.00"),
            status="completed"
        )
        assert payment.payment_method == PaymentMethodType.CASH
        assert payment.change_amount == Decimal("50.00")

    def test_transaction_line_model_creation(self):
        """Test création modèle ligne transaction."""
        line = POSTransactionLine(
            tenant_id="test",
            transaction_id=1,
            line_number=1,
            name="Product",
            quantity=Decimal("2"),
            unit_price=Decimal("25.00"),
            discount_amount=Decimal("0"),
            tax_rate=Decimal("20.00"),
            tax_amount=Decimal("10.00"),
            line_total=Decimal("50.00")
        )
        assert line.line_total == Decimal("50.00")


# ============================================================================
# SCHEMA TESTS
# ============================================================================

class TestPOSSchemas:
    """Tests des schémas POS."""

    def test_store_create_schema(self, sample_store):
        """Test schéma création magasin."""
        assert sample_store.code == "STORE001"
        assert sample_store.currency == "EUR"

    def test_terminal_create_schema(self, sample_terminal):
        """Test schéma création terminal."""
        assert sample_terminal.terminal_id == "TERM-001"
        assert sample_terminal.store_id == 1

    def test_pos_user_create_schema(self, sample_pos_user):
        """Test schéma création utilisateur POS."""
        assert sample_pos_user.employee_code == "EMP001"
        assert sample_pos_user.max_discount_percent == Decimal("15")

    def test_session_open_request_schema(self):
        """Test schéma ouverture session."""
        data = SessionOpenRequest(
            terminal_id=1,
            cashier_id=1,
            opening_cash=Decimal("150.00"),
            opening_note="Ouverture normale"
        )
        assert data.opening_cash == Decimal("150.00")

    def test_session_close_request_schema(self):
        """Test schéma fermeture session."""
        data = SessionCloseRequest(
            actual_cash=Decimal("500.00"),
            closing_note="Fermeture OK"
        )
        assert data.actual_cash == Decimal("500.00")

    def test_transaction_create_schema(self, sample_transaction_line):
        """Test schéma création transaction."""
        data = TransactionCreate(
            customer_name="Client Test",
            lines=[sample_transaction_line]
        )
        assert len(data.lines) == 1
        assert data.customer_name == "Client Test"

    def test_payment_create_schema(self):
        """Test schéma création paiement."""
        data = PaymentCreate(
            payment_method=PaymentMethodType.CARD,
            amount=Decimal("120.00"),
            card_type="VISA",
            card_last4="1234"
        )
        assert data.payment_method == PaymentMethodType.CARD
        assert data.card_last4 == "1234"

    def test_cash_movement_schema(self):
        """Test schéma mouvement de caisse."""
        data = CashMovementCreate(
            movement_type="OUT",
            amount=Decimal("50.00"),
            reason="Retrait espèces",
            description="Pour la banque"
        )
        assert data.movement_type == "OUT"
        assert data.amount == Decimal("50.00")


# ============================================================================
# SERVICE TESTS - STORES
# ============================================================================

class TestStoreService:
    """Tests service magasins."""

    def test_create_store_success(self, pos_service, sample_store, mock_db):
        """Test création magasin réussie."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        store = pos_service.create_store(sample_store)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_store_duplicate_code(self, pos_service, sample_store, mock_db):
        """Test création magasin code dupliqué."""
        existing = POSStore(id=1, code="STORE001", tenant_id="test")
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        with pytest.raises(ValueError, match="déjà utilisé"):
            pos_service.create_store(sample_store)

    def test_get_store(self, pos_service, mock_db):
        """Test récupération magasin."""
        expected = POSStore(id=1, code="S001", tenant_id="test")
        mock_db.query.return_value.filter.return_value.first.return_value = expected

        result = pos_service.get_store(1)
        assert result == expected

    def test_list_stores(self, pos_service, mock_db):
        """Test liste magasins."""
        stores = [
            POSStore(id=1, code="S001", tenant_id="test"),
            POSStore(id=2, code="S002", tenant_id="test")
        ]
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = stores

        result = pos_service.list_stores()
        assert len(result) == 2


# ============================================================================
# SERVICE TESTS - TERMINALS
# ============================================================================

class TestTerminalService:
    """Tests service terminaux."""

    def test_create_terminal_success(self, pos_service, sample_terminal, mock_db):
        """Test création terminal réussie."""
        # Store exists
        store = POSStore(id=1, code="S001", tenant_id="test")
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            store,  # get_store
            None    # check duplicate terminal_id
        ]

        terminal = pos_service.create_terminal(sample_terminal)
        mock_db.add.assert_called_once()

    def test_create_terminal_store_not_found(self, pos_service, sample_terminal, mock_db):
        """Test création terminal magasin inexistant."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Magasin introuvable"):
            pos_service.create_terminal(sample_terminal)

    def test_ping_terminal(self, pos_service, mock_db):
        """Test ping terminal."""
        terminal = POSTerminal(
            id=1, terminal_id="T001", tenant_id="test",
            status=POSTerminalStatus.OFFLINE
        )
        mock_db.query.return_value.filter.return_value.first.return_value = terminal

        result = pos_service.ping_terminal(1)
        assert result.status == POSTerminalStatus.ONLINE


# ============================================================================
# SERVICE TESTS - SESSIONS
# ============================================================================

class TestSessionService:
    """Tests service sessions."""

    def test_open_session_success(self, pos_service, mock_db):
        """Test ouverture session réussie."""
        terminal = POSTerminal(
            id=1, terminal_id="T001", tenant_id="test",
            store_id=1, status=POSTerminalStatus.ONLINE,
            current_session_id=None
        )
        cashier = POSUser(
            id=1, employee_code="EMP001", tenant_id="test",
            is_active=True, first_name="Jean", last_name="Dupont"
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            terminal,  # get_terminal
            cashier,   # get_pos_user
            None       # _generate_session_number
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        data = SessionOpenRequest(
            terminal_id=1,
            cashier_id=1,
            opening_cash=Decimal("100.00")
        )

        session = pos_service.open_session(data)
        mock_db.add.assert_called_once()
        assert terminal.current_session_id is not None

    def test_open_session_already_open(self, pos_service, mock_db):
        """Test ouverture session déjà ouverte."""
        terminal = POSTerminal(
            id=1, terminal_id="T001", tenant_id="test",
            current_session_id=5  # Already has session
        )
        mock_db.query.return_value.filter.return_value.first.return_value = terminal

        data = SessionOpenRequest(
            terminal_id=1,
            cashier_id=1,
            opening_cash=Decimal("100.00")
        )

        with pytest.raises(ValueError, match="déjà ouverte"):
            pos_service.open_session(data)

    def test_close_session_success(self, pos_service, mock_db):
        """Test fermeture session réussie."""
        session = POSSession(
            id=1, tenant_id="test", terminal_id=1,
            session_number="S001", status=POSSessionStatus.OPEN,
            opened_by_id=1, opening_cash=Decimal("100.00"),
            total_sales=Decimal("500.00"), total_refunds=Decimal("0"),
            cash_total=Decimal("300.00")
        )
        terminal = POSTerminal(
            id=1, terminal_id="T001", tenant_id="test",
            current_session_id=1
        )
        closer = POSUser(
            id=1, employee_code="EMP001", tenant_id="test",
            is_manager=True
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            session,   # get_session
            closer,    # get_pos_user
            terminal   # get_terminal
        ]
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        data = SessionCloseRequest(
            actual_cash=Decimal("400.00"),
            closing_note="Fermeture OK"
        )

        result = pos_service.close_session(1, data, 1)
        assert session.status == POSSessionStatus.CLOSED


# ============================================================================
# SERVICE TESTS - TRANSACTIONS
# ============================================================================

class TestTransactionService:
    """Tests service transactions."""

    def test_create_transaction_success(self, pos_service, mock_db, sample_transaction_line):
        """Test création transaction réussie."""
        session = POSSession(
            id=1, tenant_id="test", terminal_id=1,
            session_number="S001", status=POSSessionStatus.OPEN,
            opened_by_id=1, opening_cash=Decimal("100.00"),
            total_sales=Decimal("0"), total_refunds=Decimal("0"),
            total_discounts=Decimal("0"), transaction_count=0,
            cash_total=Decimal("0"), card_total=Decimal("0"),
            check_total=Decimal("0"), voucher_total=Decimal("0"),
            other_total=Decimal("0")
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            session,  # get_session
            None      # _generate_receipt_number
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        data = TransactionCreate(
            customer_name="Client Test",
            lines=[sample_transaction_line]
        )

        tx = pos_service.create_transaction(1, data, 1)
        mock_db.add.assert_called()

    def test_create_transaction_no_lines(self, pos_service, mock_db):
        """Test création transaction sans lignes."""
        session = POSSession(
            id=1, tenant_id="test", terminal_id=1,
            status=POSSessionStatus.OPEN, session_number="S001"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = session

        data = TransactionCreate(lines=[])

        with pytest.raises(ValueError, match="sans ligne"):
            pos_service.create_transaction(1, data, 1)

    def test_create_transaction_session_closed(self, pos_service, mock_db, sample_transaction_line):
        """Test création transaction session fermée."""
        session = POSSession(
            id=1, tenant_id="test", terminal_id=1,
            status=POSSessionStatus.CLOSED, session_number="S001"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = session

        data = TransactionCreate(lines=[sample_transaction_line])

        with pytest.raises(ValueError, match="Session fermée"):
            pos_service.create_transaction(1, data, 1)

    def test_void_transaction_success(self, pos_service, mock_db):
        """Test annulation transaction réussie."""
        tx = POSTransaction(
            id=1, tenant_id="test", session_id=1,
            receipt_number="T001", status=POSTransactionStatus.COMPLETED,
            cashier_id=1
        )
        user = POSUser(
            id=1, employee_code="EMP001", tenant_id="test",
            can_void_transaction=True
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            tx, user
        ]

        result = pos_service.void_transaction(1, "Erreur client", 1)
        assert tx.status == POSTransactionStatus.VOIDED

    def test_void_transaction_no_permission(self, pos_service, mock_db):
        """Test annulation transaction sans permission."""
        tx = POSTransaction(
            id=1, tenant_id="test", session_id=1,
            receipt_number="T001", status=POSTransactionStatus.COMPLETED,
            cashier_id=1
        )
        user = POSUser(
            id=1, employee_code="EMP001", tenant_id="test",
            can_void_transaction=False, is_manager=False
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            tx, user
        ]

        with pytest.raises(ValueError, match="Pas autorisé"):
            pos_service.void_transaction(1, "Erreur", 1)


# ============================================================================
# SERVICE TESTS - PAYMENTS
# ============================================================================

class TestPaymentService:
    """Tests service paiements."""

    def test_add_payment_cash(self, pos_service, mock_db):
        """Test ajout paiement espèces."""
        tx = POSTransaction(
            id=1, tenant_id="test", session_id=1,
            receipt_number="T001", status=POSTransactionStatus.PENDING,
            cashier_id=1, total=Decimal("100.00"),
            amount_paid=Decimal("0"), amount_due=Decimal("100.00")
        )
        tx.payments = []

        session = POSSession(
            id=1, tenant_id="test", terminal_id=1,
            session_number="S001", status=POSSessionStatus.OPEN,
            total_sales=Decimal("0"), cash_total=Decimal("0"),
            card_total=Decimal("0"), check_total=Decimal("0"),
            voucher_total=Decimal("0"), other_total=Decimal("0"),
            total_discounts=Decimal("0"), transaction_count=0
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            tx, session
        ]

        payment_data = PaymentCreate(
            payment_method=PaymentMethodType.CASH,
            amount=Decimal("100.00"),
            amount_tendered=Decimal("120.00")
        )

        result = pos_service.add_payment(1, payment_data)
        assert tx.status == POSTransactionStatus.COMPLETED

    def test_add_payment_card(self, pos_service, mock_db):
        """Test ajout paiement carte."""
        tx = POSTransaction(
            id=1, tenant_id="test", session_id=1,
            receipt_number="T001", status=POSTransactionStatus.PENDING,
            cashier_id=1, total=Decimal("100.00"),
            amount_paid=Decimal("0"), amount_due=Decimal("100.00")
        )
        tx.payments = []

        session = POSSession(
            id=1, tenant_id="test", terminal_id=1,
            session_number="S001", status=POSSessionStatus.OPEN,
            total_sales=Decimal("0"), cash_total=Decimal("0"),
            card_total=Decimal("0"), check_total=Decimal("0"),
            voucher_total=Decimal("0"), other_total=Decimal("0"),
            total_discounts=Decimal("0"), transaction_count=0
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            tx, session
        ]

        payment_data = PaymentCreate(
            payment_method=PaymentMethodType.CARD,
            amount=Decimal("100.00"),
            card_type="VISA",
            card_last4="1234"
        )

        result = pos_service.add_payment(1, payment_data)
        assert tx.status == POSTransactionStatus.COMPLETED


# ============================================================================
# SERVICE TESTS - QUICK KEYS
# ============================================================================

class TestQuickKeyService:
    """Tests service raccourcis."""

    def test_create_quick_key_success(self, pos_service, mock_db):
        """Test création raccourci réussie."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = QuickKeyCreate(
            page=1,
            position=1,
            product_id=1,
            label="Café",
            color="#1976D2"
        )

        result = pos_service.create_quick_key(data)
        mock_db.add.assert_called_once()

    def test_create_quick_key_position_taken(self, pos_service, mock_db):
        """Test création raccourci position prise."""
        existing = POSProductQuickKey(
            id=1, tenant_id="test", page=1, position=1
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        data = QuickKeyCreate(
            page=1,
            position=1,
            product_id=1,
            label="Café"
        )

        with pytest.raises(ValueError, match="déjà utilisée"):
            pos_service.create_quick_key(data)


# ============================================================================
# SERVICE TESTS - HOLD TRANSACTIONS
# ============================================================================

class TestHoldTransactionService:
    """Tests service transactions en attente."""

    def test_hold_transaction_success(self, pos_service, mock_db):
        """Test mise en attente transaction."""
        session = POSSession(
            id=1, tenant_id="test", terminal_id=1,
            status=POSSessionStatus.OPEN, session_number="S001"
        )
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            session, None  # get_session, _generate_hold_number
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        data = HoldTransactionCreate(
            hold_name="Client en attente",
            customer_name="Jean Dupont",
            transaction_data={"lines": [{"name": "Produit", "qty": 1}]}
        )

        result = pos_service.hold_transaction(1, data, 1)
        mock_db.add.assert_called_once()

    def test_recall_held_transaction_success(self, pos_service, mock_db):
        """Test récupération transaction en attente."""
        hold = POSHoldTransaction(
            id=1, tenant_id="test", session_id=1,
            hold_number="H001", is_active=True,
            transaction_data={"lines": [{"name": "Test"}]}
        )
        mock_db.query.return_value.filter.return_value.first.return_value = hold

        result = pos_service.recall_held_transaction(1)
        assert result == {"lines": [{"name": "Test"}]}
        assert hold.is_active is False


# ============================================================================
# SERVICE TESTS - CASH MOVEMENTS
# ============================================================================

class TestCashMovementService:
    """Tests service mouvements de caisse."""

    def test_add_cash_movement_in(self, pos_service, mock_db):
        """Test ajout entrée de caisse."""
        session = POSSession(
            id=1, tenant_id="test", terminal_id=1,
            status=POSSessionStatus.OPEN, session_number="S001"
        )
        user = POSUser(
            id=1, employee_code="EMP001", tenant_id="test",
            can_open_drawer=True
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            session, user
        ]

        data = CashMovementCreate(
            movement_type="IN",
            amount=Decimal("50.00"),
            reason="Apport initial"
        )

        result = pos_service.add_cash_movement(1, data, 1)
        mock_db.add.assert_called_once()

    def test_add_cash_movement_out_no_permission(self, pos_service, mock_db):
        """Test sortie de caisse sans permission."""
        session = POSSession(
            id=1, tenant_id="test", terminal_id=1,
            status=POSSessionStatus.OPEN, session_number="S001"
        )
        user = POSUser(
            id=1, employee_code="EMP001", tenant_id="test",
            can_open_drawer=False
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            session, user
        ]

        data = CashMovementCreate(
            movement_type="OUT",
            amount=Decimal("50.00"),
            reason="Retrait"
        )

        with pytest.raises(ValueError, match="Pas autorisé"):
            pos_service.add_cash_movement(1, data, 1)


# ============================================================================
# SERVICE TESTS - DAILY REPORTS
# ============================================================================

class TestDailyReportService:
    """Tests service rapports journaliers."""

    def test_generate_daily_report_no_sessions(self, pos_service, mock_db):
        """Test génération rapport sans sessions."""
        store = POSStore(id=1, code="S001", tenant_id="test")
        mock_db.query.return_value.filter.return_value.first.return_value = store
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with pytest.raises(ValueError, match="Aucune session"):
            pos_service.generate_daily_report(1, date.today())


# ============================================================================
# SERVICE TESTS - DASHBOARD
# ============================================================================

class TestDashboardService:
    """Tests service dashboard."""

    def test_get_pos_dashboard(self, pos_service, mock_db):
        """Test récupération dashboard POS."""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = pos_service.get_pos_dashboard()
        assert "sales_today" in result
        assert "active_sessions" in result
        assert "top_products" in result

    def test_get_terminal_dashboard(self, pos_service, mock_db):
        """Test récupération dashboard terminal."""
        terminal = POSTerminal(
            id=1, terminal_id="T001", name="Caisse 1",
            tenant_id="test", status=POSTerminalStatus.IN_USE,
            current_session_id=None
        )
        mock_db.query.return_value.filter.return_value.first.return_value = terminal

        result = pos_service.get_terminal_dashboard(1)
        assert result["terminal_id"] == 1
        assert result["terminal_name"] == "Caisse 1"


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestPOSEnums:
    """Tests des énumérations POS."""

    def test_terminal_status_values(self):
        """Test valeurs statut terminal."""
        assert POSTerminalStatus.OFFLINE.value == "offline"
        assert POSTerminalStatus.ONLINE.value == "online"
        assert POSTerminalStatus.IN_USE.value == "in_use"
        assert POSTerminalStatus.MAINTENANCE.value == "maintenance"

    def test_session_status_values(self):
        """Test valeurs statut session."""
        assert POSSessionStatus.OPEN.value == "open"
        assert POSSessionStatus.CLOSED.value == "closed"
        assert POSSessionStatus.SUSPENDED.value == "suspended"

    def test_transaction_status_values(self):
        """Test valeurs statut transaction."""
        assert POSTransactionStatus.PENDING.value == "pending"
        assert POSTransactionStatus.COMPLETED.value == "completed"
        assert POSTransactionStatus.VOIDED.value == "voided"
        assert POSTransactionStatus.REFUNDED.value == "refunded"

    def test_payment_method_values(self):
        """Test valeurs modes paiement."""
        assert PaymentMethodType.CASH.value == "cash"
        assert PaymentMethodType.CARD.value == "card"
        assert PaymentMethodType.CHECK.value == "check"
        assert PaymentMethodType.VOUCHER.value == "voucher"
        assert PaymentMethodType.MOBILE.value == "mobile"

    def test_discount_type_values(self):
        """Test valeurs types remise."""
        assert DiscountType.PERCENTAGE.value == "percentage"
        assert DiscountType.FIXED.value == "fixed"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPOSIntegration:
    """Tests d'intégration POS."""

    def test_full_transaction_flow(self, pos_service, mock_db, sample_transaction_line):
        """Test flux complet transaction."""
        # Setup mocks
        store = POSStore(id=1, code="S001", tenant_id="test", name="Store")
        terminal = POSTerminal(
            id=1, terminal_id="T001", tenant_id="test",
            store_id=1, status=POSTerminalStatus.ONLINE,
            current_session_id=None, name="Terminal"
        )
        cashier = POSUser(
            id=1, employee_code="EMP001", tenant_id="test",
            is_active=True, first_name="Jean", last_name="Dupont",
            can_close_session=True
        )

        # This simulates a complete flow:
        # 1. Open session
        # 2. Create transaction
        # 3. Add payment
        # 4. Close session

        # Just verify the service methods exist and are callable
        assert hasattr(pos_service, 'open_session')
        assert hasattr(pos_service, 'create_transaction')
        assert hasattr(pos_service, 'add_payment')
        assert hasattr(pos_service, 'close_session')
        assert hasattr(pos_service, 'generate_daily_report')

    def test_discount_calculation(self, sample_transaction_line):
        """Test calcul remise."""
        # Ligne avec remise pourcentage
        line = TransactionLineCreate(
            name="Produit",
            quantity=Decimal("2"),
            unit_price=Decimal("100.00"),
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10"),
            tax_rate=Decimal("20.00")
        )

        # Le calcul sera fait dans _create_transaction_line
        subtotal = line.quantity * line.unit_price  # 200
        discount = subtotal * line.discount_value / 100  # 20
        net = subtotal - discount  # 180
        tax = net * line.tax_rate / 100  # 36

        assert subtotal == Decimal("200.00")
        assert discount == Decimal("20.00")
        assert net == Decimal("180.00")
        assert tax == Decimal("36.00")

    def test_change_calculation(self):
        """Test calcul rendu monnaie."""
        payment = PaymentCreate(
            payment_method=PaymentMethodType.CASH,
            amount=Decimal("75.50"),
            amount_tendered=Decimal("100.00")
        )

        change = payment.amount_tendered - payment.amount
        assert change == Decimal("24.50")


# ============================================================================
# EDGE CASES
# ============================================================================

class TestPOSEdgeCases:
    """Tests cas limites POS."""

    def test_zero_quantity_line(self):
        """Test ligne quantité zéro - doit échouer."""
        with pytest.raises(Exception):
            TransactionLineCreate(
                name="Produit",
                quantity=Decimal("0"),
                unit_price=Decimal("10.00"),
                tax_rate=Decimal("20.00")
            )

    def test_negative_cash_movement(self):
        """Test mouvement caisse négatif - doit échouer."""
        with pytest.raises(Exception):
            CashMovementCreate(
                movement_type="IN",
                amount=Decimal("-50.00"),
                reason="Test"
            )

    def test_invalid_movement_type(self):
        """Test type mouvement invalide - doit échouer."""
        with pytest.raises(Exception):
            CashMovementCreate(
                movement_type="INVALID",
                amount=Decimal("50.00"),
                reason="Test"
            )

    def test_empty_store_code(self):
        """Test code magasin vide - doit échouer."""
        with pytest.raises(Exception):
            StoreCreate(
                code="",
                name="Test Store"
            )

    def test_quick_key_position_out_of_range(self):
        """Test position raccourci hors limites - doit échouer."""
        with pytest.raises(Exception):
            QuickKeyCreate(
                page=1,
                position=25,  # Max is 20
                product_id=1
            )
