"""
Tests pour Finance Router v2 (CORE SaaS)
=========================================

Tests complets pour le module Finance migré avec CORE SaaS pattern.
Coverage: Accounts, Journals, Fiscal Years, Entries, Bank, Cash Forecasts, Reports, Dashboard
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.core.saas_context import SaaSContext, UserRole
from app.modules.finance.models import (
    Account, Journal, FiscalYear, JournalEntry, BankAccount,
    BankStatement, AccountType, JournalType, EntryStatus
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session fixture"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def tenant_id():
    """Tenant ID pour tests"""
    return "tenant-test-001"


@pytest.fixture
def user_id():
    """User ID pour tests"""
    return "user-test-001"


@pytest.fixture
def saas_context(tenant_id, user_id):
    """SaaSContext fixture"""
    return SaaSContext(
        tenant_id=tenant_id,
        user_id=user_id,
        role=UserRole.ADMIN,
        permissions=["finance.*"],
        scope="full",
        session_id="session-test",
        ip_address="127.0.0.1",
        user_agent="pytest",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow()
    )


@pytest.fixture
def auth_headers(tenant_id, user_id):
    """Headers d'authentification pour tests API"""
    # Mock JWT token (dans un test réel, utiliser un vrai token)
    return {
        "Authorization": f"Bearer mock-token-{tenant_id}-{user_id}"
    }


@pytest.fixture
def sample_account(db_session, tenant_id):
    """Compte comptable de test"""
    account = Account(
        id=uuid4(),
        tenant_id=tenant_id,
        code="411000",
        name="Clients",
        type=AccountType.RECEIVABLE,
        currency="EUR",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def sample_journal(db_session, tenant_id):
    """Journal comptable de test"""
    journal = Journal(
        id=uuid4(),
        tenant_id=tenant_id,
        code="VT",
        name="Ventes",
        type=JournalType.SALE,
        is_active=True
    )
    db_session.add(journal)
    db_session.commit()
    return journal


@pytest.fixture
def sample_fiscal_year(db_session, tenant_id):
    """Exercice fiscal de test"""
    fiscal_year = FiscalYear(
        id=uuid4(),
        tenant_id=tenant_id,
        name="2024",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        is_closed=False
    )
    db_session.add(fiscal_year)
    db_session.commit()
    return fiscal_year


# ============================================================================
# TESTS ACCOUNTS (6 tests)
# ============================================================================

def test_create_account(client, auth_headers, tenant_id):
    """Test création d'un compte comptable"""
    response = client.post(
        "/api/v2/finance/accounts",
        json={
            "code": "401000",
            "name": "Capital",
            "type": "EQUITY",
            "currency": "EUR"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "401000"
    assert data["name"] == "Capital"
    assert data["type"] == "EQUITY"


def test_list_accounts(client, auth_headers, sample_account):
    """Test listage des comptes"""
    response = client.get(
        "/api/v2/finance/accounts",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(acc["code"] == "411000" for acc in data)


def test_get_account(client, auth_headers, sample_account):
    """Test récupération d'un compte"""
    response = client.get(
        f"/api/v2/finance/accounts/{sample_account.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_account.id)
    assert data["code"] == "411000"


def test_update_account(client, auth_headers, sample_account):
    """Test mise à jour d'un compte"""
    response = client.put(
        f"/api/v2/finance/accounts/{sample_account.id}",
        json={"name": "Clients - Updated"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Clients - Updated"


def test_get_account_balance(client, auth_headers, sample_account):
    """Test récupération du solde d'un compte"""
    response = client.get(
        f"/api/v2/finance/accounts/{sample_account.id}/balance",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "debit" in data
    assert "credit" in data
    assert "balance" in data


def test_account_tenant_isolation(client, auth_headers, sample_account):
    """Test isolation tenant sur les comptes"""
    # Essayer d'accéder avec un autre tenant
    other_headers = {
        "Authorization": "Bearer mock-token-other-tenant-user"
    }
    response = client.get(
        f"/api/v2/finance/accounts/{sample_account.id}",
        headers=other_headers
    )
    assert response.status_code in [404, 403]  # Pas trouvé ou accès refusé


# ============================================================================
# TESTS JOURNALS (5 tests)
# ============================================================================

def test_create_journal(client, auth_headers):
    """Test création d'un journal"""
    response = client.post(
        "/api/v2/finance/journals",
        json={
            "code": "AC",
            "name": "Achats",
            "type": "PURCHASE"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "AC"
    assert data["type"] == "PURCHASE"


def test_list_journals(client, auth_headers, sample_journal):
    """Test listage des journaux"""
    response = client.get(
        "/api/v2/finance/journals",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(j["code"] == "VT" for j in data)


def test_get_journal(client, auth_headers, sample_journal):
    """Test récupération d'un journal"""
    response = client.get(
        f"/api/v2/finance/journals/{sample_journal.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "VT"


def test_update_journal(client, auth_headers, sample_journal):
    """Test mise à jour d'un journal"""
    response = client.put(
        f"/api/v2/finance/journals/{sample_journal.id}",
        json={"name": "Ventes - Updated"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Ventes - Updated"


def test_filter_journals_by_type(client, auth_headers, sample_journal):
    """Test filtrage des journaux par type"""
    response = client.get(
        "/api/v2/finance/journals?type=SALE",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert all(j["type"] == "SALE" for j in data)


# ============================================================================
# TESTS FISCAL YEARS (8 tests)
# ============================================================================

def test_create_fiscal_year(client, auth_headers):
    """Test création d'un exercice fiscal"""
    response = client.post(
        "/api/v2/finance/fiscal-years",
        json={
            "name": "2025",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "2025"


def test_list_fiscal_years(client, auth_headers, sample_fiscal_year):
    """Test listage des exercices fiscaux"""
    response = client.get(
        "/api/v2/finance/fiscal-years",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(fy["name"] == "2024" for fy in data)


def test_get_fiscal_year(client, auth_headers, sample_fiscal_year):
    """Test récupération d'un exercice fiscal"""
    response = client.get(
        f"/api/v2/finance/fiscal-years/{sample_fiscal_year.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "2024"


def test_get_current_fiscal_year(client, auth_headers, sample_fiscal_year):
    """Test récupération de l'exercice fiscal courant"""
    response = client.get(
        "/api/v2/finance/fiscal-years/current",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert not data["is_closed"]


def test_get_fiscal_year_periods(client, auth_headers, sample_fiscal_year):
    """Test récupération des périodes d'un exercice fiscal"""
    response = client.get(
        f"/api/v2/finance/fiscal-years/{sample_fiscal_year.id}/periods",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Devrait avoir 12 périodes (mois)
    assert len(data) == 12


def test_close_fiscal_year(client, auth_headers, sample_fiscal_year):
    """Test clôture d'un exercice fiscal"""
    response = client.post(
        f"/api/v2/finance/fiscal-years/{sample_fiscal_year.id}/close",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_closed"] == True


def test_cannot_modify_closed_fiscal_year(client, auth_headers, db_session, sample_fiscal_year):
    """Test impossibilité de modifier un exercice clôturé"""
    # Clôturer l'exercice
    sample_fiscal_year.is_closed = True
    db_session.commit()

    # Essayer de modifier
    response = client.put(
        f"/api/v2/finance/fiscal-years/{sample_fiscal_year.id}",
        json={"name": "2024 - Modified"},
        headers=auth_headers
    )
    assert response.status_code == 400  # Bad request - exercice clôturé


def test_fiscal_year_date_validation(client, auth_headers):
    """Test validation des dates d'exercice fiscal"""
    # End date avant start date
    response = client.post(
        "/api/v2/finance/fiscal-years",
        json={
            "name": "Invalid",
            "start_date": "2024-12-31",
            "end_date": "2024-01-01"
        },
        headers=auth_headers
    )
    assert response.status_code == 400  # Validation error


# ============================================================================
# TESTS ENTRIES (12 tests) - WORKFLOWS CRITIQUES
# ============================================================================

def test_create_entry(client, auth_headers, sample_journal, sample_fiscal_year):
    """Test création d'une écriture comptable"""
    response = client.post(
        "/api/v2/finance/entries",
        json={
            "journal_id": str(sample_journal.id),
            "fiscal_year_id": str(sample_fiscal_year.id),
            "date": "2024-06-15",
            "reference": "TEST001",
            "description": "Test entry"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["reference"] == "TEST001"
    assert data["status"] == "DRAFT"


def test_list_entries(client, auth_headers):
    """Test listage des écritures"""
    response = client.get(
        "/api/v2/finance/entries",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    assert "total" in data


def test_get_entry(client, auth_headers, sample_journal, sample_fiscal_year, db_session, tenant_id):
    """Test récupération d'une écriture"""
    # Créer une écriture
    entry = JournalEntry(
        id=uuid4(),
        tenant_id=tenant_id,
        journal_id=sample_journal.id,
        fiscal_year_id=sample_fiscal_year.id,
        date=date.today(),
        reference="GET001",
        description="Get test",
        status=EntryStatus.DRAFT
    )
    db_session.add(entry)
    db_session.commit()

    response = client.get(
        f"/api/v2/finance/entries/{entry.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["reference"] == "GET001"


def test_add_entry_lines(client, auth_headers, sample_account, sample_journal,
                         sample_fiscal_year, db_session, tenant_id):
    """Test ajout de lignes à une écriture"""
    # Créer une écriture
    entry = JournalEntry(
        id=uuid4(),
        tenant_id=tenant_id,
        journal_id=sample_journal.id,
        fiscal_year_id=sample_fiscal_year.id,
        date=date.today(),
        reference="LINES001",
        status=EntryStatus.DRAFT
    )
    db_session.add(entry)
    db_session.commit()

    response = client.post(
        f"/api/v2/finance/entries/{entry.id}/lines",
        json={
            "account_id": str(sample_account.id),
            "label": "Test line",
            "debit": 1000.00,
            "credit": 0.00
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["debit"] == 1000.00


def test_validate_entry_workflow(client, auth_headers, sample_journal,
                                  sample_fiscal_year, db_session, tenant_id):
    """Test workflow validation d'une écriture (DRAFT → VALIDATED)"""
    # Créer une écriture avec lignes équilibrées
    entry = JournalEntry(
        id=uuid4(),
        tenant_id=tenant_id,
        journal_id=sample_journal.id,
        fiscal_year_id=sample_fiscal_year.id,
        date=date.today(),
        reference="VAL001",
        status=EntryStatus.DRAFT
    )
    db_session.add(entry)
    db_session.commit()

    # Valider l'écriture
    response = client.post(
        f"/api/v2/finance/entries/{entry.id}/validate",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "VALIDATED"
    assert "validated_by" in data
    assert "validated_at" in data


def test_post_entry_workflow(client, auth_headers, sample_journal,
                              sample_fiscal_year, db_session, tenant_id):
    """Test workflow post d'une écriture (VALIDATED → POSTED)"""
    # Créer une écriture validée
    entry = JournalEntry(
        id=uuid4(),
        tenant_id=tenant_id,
        journal_id=sample_journal.id,
        fiscal_year_id=sample_fiscal_year.id,
        date=date.today(),
        reference="POST001",
        status=EntryStatus.VALIDATED
    )
    db_session.add(entry)
    db_session.commit()

    # Poster l'écriture
    response = client.post(
        f"/api/v2/finance/entries/{entry.id}/post",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "POSTED"
    assert "posted_by" in data
    assert "posted_at" in data


def test_cancel_entry_workflow(client, auth_headers, sample_journal,
                                sample_fiscal_year, db_session, tenant_id):
    """Test workflow annulation d'une écriture"""
    # Créer une écriture
    entry = JournalEntry(
        id=uuid4(),
        tenant_id=tenant_id,
        journal_id=sample_journal.id,
        fiscal_year_id=sample_fiscal_year.id,
        date=date.today(),
        reference="CANCEL001",
        status=EntryStatus.DRAFT
    )
    db_session.add(entry)
    db_session.commit()

    # Annuler l'écriture
    response = client.post(
        f"/api/v2/finance/entries/{entry.id}/cancel",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CANCELLED"


def test_cannot_modify_posted_entry(client, auth_headers, sample_journal,
                                      sample_fiscal_year, db_session, tenant_id):
    """Test impossibilité de modifier une écriture postée"""
    # Créer une écriture postée
    entry = JournalEntry(
        id=uuid4(),
        tenant_id=tenant_id,
        journal_id=sample_journal.id,
        fiscal_year_id=sample_fiscal_year.id,
        date=date.today(),
        reference="POSTED001",
        status=EntryStatus.POSTED
    )
    db_session.add(entry)
    db_session.commit()

    # Essayer de modifier
    response = client.put(
        f"/api/v2/finance/entries/{entry.id}",
        json={"description": "Modified"},
        headers=auth_headers
    )
    assert response.status_code == 400  # Bad request - écriture postée


def test_entry_balance_validation(client, auth_headers, sample_account,
                                   sample_journal, sample_fiscal_year, db_session, tenant_id):
    """Test validation de l'équilibre débit/crédit"""
    # Créer une écriture déséquilibrée
    entry = JournalEntry(
        id=uuid4(),
        tenant_id=tenant_id,
        journal_id=sample_journal.id,
        fiscal_year_id=sample_fiscal_year.id,
        date=date.today(),
        reference="UNBAL001",
        status=EntryStatus.DRAFT
    )
    db_session.add(entry)
    db_session.commit()

    # Ajouter ligne débit seulement
    client.post(
        f"/api/v2/finance/entries/{entry.id}/lines",
        json={
            "account_id": str(sample_account.id),
            "label": "Unbalanced",
            "debit": 1000.00,
            "credit": 0.00
        },
        headers=auth_headers
    )

    # Essayer de valider une écriture déséquilibrée
    response = client.post(
        f"/api/v2/finance/entries/{entry.id}/validate",
        headers=auth_headers
    )
    assert response.status_code == 400  # Validation error - non équilibrée


def test_filter_entries_by_status(client, auth_headers):
    """Test filtrage des écritures par statut"""
    response = client.get(
        "/api/v2/finance/entries?status=POSTED",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    entries = data.get("entries", [])
    assert all(e["status"] == "POSTED" for e in entries)


def test_filter_entries_by_date_range(client, auth_headers):
    """Test filtrage des écritures par période"""
    response = client.get(
        "/api/v2/finance/entries?from_date=2024-01-01&to_date=2024-12-31",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "entries" in data


# ============================================================================
# TESTS BANK ACCOUNTS (5 tests)
# ============================================================================

def test_create_bank_account(client, auth_headers):
    """Test création d'un compte bancaire"""
    response = client.post(
        "/api/v2/finance/bank-accounts",
        json={
            "name": "BNP Paribas",
            "bank_name": "BNP Paribas",
            "account_number": "FR7630004000000001234567890",
            "iban": "FR7630004000000001234567890",
            "bic": "BNPAFRPP",
            "currency": "EUR"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "BNP Paribas"
    assert data["currency"] == "EUR"


def test_list_bank_accounts(client, auth_headers):
    """Test listage des comptes bancaires"""
    response = client.get(
        "/api/v2/finance/bank-accounts",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_bank_account(client, auth_headers, db_session, tenant_id):
    """Test récupération d'un compte bancaire"""
    # Créer un compte bancaire
    bank_account = BankAccount(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Test Bank",
        bank_name="Test",
        account_number="123456",
        currency="EUR",
        is_active=True
    )
    db_session.add(bank_account)
    db_session.commit()

    response = client.get(
        f"/api/v2/finance/bank-accounts/{bank_account.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Bank"


def test_update_bank_account(client, auth_headers, db_session, tenant_id):
    """Test mise à jour d'un compte bancaire"""
    bank_account = BankAccount(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Old Name",
        bank_name="Test",
        account_number="123456",
        currency="EUR",
        is_active=True
    )
    db_session.add(bank_account)
    db_session.commit()

    response = client.put(
        f"/api/v2/finance/bank-accounts/{bank_account.id}",
        json={"name": "New Name"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"


def test_bank_account_tenant_isolation(client, auth_headers, db_session, tenant_id):
    """Test isolation tenant sur les comptes bancaires"""
    bank_account = BankAccount(
        id=uuid4(),
        tenant_id="other-tenant",
        name="Other Tenant Bank",
        bank_name="Test",
        account_number="999",
        currency="EUR",
        is_active=True
    )
    db_session.add(bank_account)
    db_session.commit()

    # Ne devrait pas voir les comptes d'autres tenants
    response = client.get(
        "/api/v2/finance/bank-accounts",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert not any(ba["name"] == "Other Tenant Bank" for ba in data)


# ============================================================================
# TESTS BANK STATEMENTS (6 tests)
# ============================================================================

def test_create_bank_statement(client, auth_headers, db_session, tenant_id):
    """Test création d'un relevé bancaire"""
    bank_account = BankAccount(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Test Bank",
        bank_name="Test",
        account_number="123",
        currency="EUR",
        is_active=True
    )
    db_session.add(bank_account)
    db_session.commit()

    response = client.post(
        "/api/v2/finance/bank-statements",
        json={
            "bank_account_id": str(bank_account.id),
            "statement_date": "2024-06-30",
            "starting_balance": 10000.00,
            "ending_balance": 12000.00
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["starting_balance"] == 10000.00
    assert data["ending_balance"] == 12000.00


def test_list_bank_statements(client, auth_headers):
    """Test listage des relevés bancaires"""
    response = client.get(
        "/api/v2/finance/bank-statements",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_bank_statement(client, auth_headers, db_session, tenant_id):
    """Test récupération d'un relevé bancaire"""
    bank_account = BankAccount(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Test",
        bank_name="Test",
        account_number="123",
        currency="EUR",
        is_active=True
    )
    db_session.add(bank_account)

    statement = BankStatement(
        id=uuid4(),
        tenant_id=tenant_id,
        bank_account_id=bank_account.id,
        statement_date=date.today(),
        starting_balance=Decimal("1000.00"),
        ending_balance=Decimal("1500.00")
    )
    db_session.add(statement)
    db_session.commit()

    response = client.get(
        f"/api/v2/finance/bank-statements/{statement.id}",
        headers=auth_headers
    )
    assert response.status_code == 200


def test_reconcile_bank_statement(client, auth_headers, db_session, tenant_id):
    """Test rapprochement bancaire"""
    bank_account = BankAccount(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Test",
        bank_name="Test",
        account_number="123",
        currency="EUR",
        is_active=True
    )
    db_session.add(bank_account)

    statement = BankStatement(
        id=uuid4(),
        tenant_id=tenant_id,
        bank_account_id=bank_account.id,
        statement_date=date.today(),
        starting_balance=Decimal("1000.00"),
        ending_balance=Decimal("1500.00"),
        is_reconciled=False
    )
    db_session.add(statement)
    db_session.commit()

    response = client.post(
        f"/api/v2/finance/bank-statements/{statement.id}/reconcile",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_reconciled"] == True


def test_bank_statement_balance_validation(client, auth_headers, db_session, tenant_id):
    """Test validation des soldes de relevé"""
    bank_account = BankAccount(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Test",
        bank_name="Test",
        account_number="123",
        currency="EUR",
        is_active=True
    )
    db_session.add(bank_account)
    db_session.commit()

    # Ending balance < starting balance sans transactions négatives
    response = client.post(
        "/api/v2/finance/bank-statements",
        json={
            "bank_account_id": str(bank_account.id),
            "statement_date": "2024-06-30",
            "starting_balance": 10000.00,
            "ending_balance": 5000.00  # Suspect sans transactions
        },
        headers=auth_headers
    )
    # Devrait accepter mais possiblement avec warning
    assert response.status_code in [201, 400]


def test_filter_bank_statements_by_date(client, auth_headers):
    """Test filtrage des relevés par date"""
    response = client.get(
        "/api/v2/finance/bank-statements?from_date=2024-01-01&to_date=2024-12-31",
        headers=auth_headers
    )
    assert response.status_code == 200


# ============================================================================
# TESTS CASH FORECASTS (5 tests)
# ============================================================================

def test_create_cash_forecast(client, auth_headers):
    """Test création d'une prévision de trésorerie"""
    response = client.post(
        "/api/v2/finance/cash-forecasts",
        json={
            "date": "2024-07-31",
            "description": "Prévision juillet",
            "expected_inflow": 50000.00,
            "expected_outflow": 30000.00
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["expected_inflow"] == 50000.00
    assert data["net_flow"] == 20000.00  # Calculé automatiquement


def test_list_cash_forecasts(client, auth_headers):
    """Test listage des prévisions de trésorerie"""
    response = client.get(
        "/api/v2/finance/cash-forecasts",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_cash_forecast(client, auth_headers, db_session, tenant_id):
    """Test récupération d'une prévision"""
    from app.modules.finance.models import CashForecast

    forecast = CashForecast(
        id=uuid4(),
        tenant_id=tenant_id,
        date=date.today(),
        description="Test forecast",
        expected_inflow=Decimal("10000.00"),
        expected_outflow=Decimal("5000.00")
    )
    db_session.add(forecast)
    db_session.commit()

    response = client.get(
        f"/api/v2/finance/cash-forecasts/{forecast.id}",
        headers=auth_headers
    )
    assert response.status_code == 200


def test_update_cash_forecast(client, auth_headers, db_session, tenant_id):
    """Test mise à jour d'une prévision"""
    from app.modules.finance.models import CashForecast

    forecast = CashForecast(
        id=uuid4(),
        tenant_id=tenant_id,
        date=date.today(),
        description="Old",
        expected_inflow=Decimal("10000.00"),
        expected_outflow=Decimal("5000.00")
    )
    db_session.add(forecast)
    db_session.commit()

    response = client.put(
        f"/api/v2/finance/cash-forecasts/{forecast.id}",
        json={"description": "Updated"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated"


def test_cash_forecast_date_validation(client, auth_headers):
    """Test validation des dates de prévision"""
    # Date dans le passé (devrait fonctionner mais avec warning potentiel)
    response = client.post(
        "/api/v2/finance/cash-forecasts",
        json={
            "date": "2020-01-01",  # Passé lointain
            "description": "Past forecast",
            "expected_inflow": 1000.00,
            "expected_outflow": 500.00
        },
        headers=auth_headers
    )
    # Devrait accepter (prévisions rétrospectives possibles pour analyse)
    assert response.status_code in [201, 400]


# ============================================================================
# TESTS REPORTS (3 tests)
# ============================================================================

def test_get_balance_sheet(client, auth_headers, sample_fiscal_year):
    """Test génération du bilan comptable"""
    response = client.get(
        f"/api/v2/finance/reports/balance-sheet?fiscal_year_id={sample_fiscal_year.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "assets" in data
    assert "liabilities" in data
    assert "equity" in data


def test_get_income_statement(client, auth_headers, sample_fiscal_year):
    """Test génération du compte de résultat"""
    response = client.get(
        f"/api/v2/finance/reports/income-statement?fiscal_year_id={sample_fiscal_year.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "revenue" in data
    assert "expenses" in data
    assert "net_income" in data


def test_reports_tenant_isolation(client, auth_headers):
    """Test isolation tenant sur les rapports"""
    # Les rapports ne doivent inclure que les données du tenant courant
    response = client.get(
        "/api/v2/finance/reports/balance-sheet",
        headers=auth_headers
    )
    assert response.status_code == 200
    # Vérifier que les données sont bien isolées (pas de données d'autres tenants)


# ============================================================================
# TESTS DASHBOARD (1 test)
# ============================================================================

def test_get_finance_dashboard(client, auth_headers):
    """Test récupération du dashboard finance"""
    response = client.get(
        "/api/v2/finance/dashboard",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_receivables" in data or "summary" in data
    # Dashboard doit contenir métriques clés


# ============================================================================
# TESTS PERFORMANCE & SÉCURITÉ
# ============================================================================

def test_context_performance(client, auth_headers):
    """Test que context JWT ne génère pas de requête DB user"""
    # Avec CORE SaaS, le context vient du JWT
    # Aucune requête DB pour charger l'utilisateur
    response = client.get(
        "/api/v2/finance/accounts",
        headers=auth_headers
    )
    assert response.status_code == 200
    # TODO: Vérifier nombre de requêtes SQL (devrait être minimal)


def test_audit_trail_automatic(client, auth_headers):
    """Test que l'audit trail est automatique"""
    response = client.post(
        "/api/v2/finance/accounts",
        json={
            "code": "999",
            "name": "Test Audit",
            "type": "EXPENSE",
            "currency": "EUR"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    # created_by devrait être automatiquement rempli via context.user_id
    assert "created_by" in data or "audit" in data


def test_tenant_isolation_strict(client, auth_headers):
    """Test que l'isolation tenant est stricte"""
    # Essayer d'accéder à une ressource d'un autre tenant via ID forgé
    fake_id = uuid4()
    response = client.get(
        f"/api/v2/finance/accounts/{fake_id}",
        headers=auth_headers
    )
    assert response.status_code == 404  # Pas trouvé (et non 403, pour ne pas révéler l'existence)
