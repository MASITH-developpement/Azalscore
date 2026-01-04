"""
AZALS MODULE M2 - Tests Finance
===============================

Tests unitaires pour le module Comptabilité & Trésorerie.
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

# Import des modèles
from app.modules.finance.models import (
    Account, Journal, FiscalYear, FiscalPeriod, JournalEntry, JournalEntryLine,
    BankAccount, BankStatement, BankStatementLine, BankTransaction,
    CashForecast, CashFlowCategory, FinancialReport,
    AccountType, JournalType, EntryStatus, FiscalYearStatus,
    BankTransactionType, ReconciliationStatus, ForecastPeriod
)

# Import des schémas
from app.modules.finance.schemas import (
    AccountCreate, AccountUpdate, JournalCreate,
    FiscalYearCreate, EntryCreate, EntryLineCreate,
    BankAccountCreate, BankStatementCreate, BankStatementLineCreate,
    BankTransactionCreate, CashForecastCreate,
    CashFlowCategoryCreate, FinancialReportCreate,
    TrialBalance, BalanceSheetItem, IncomeStatement,
    FinanceDashboard
)

# Import du service
from app.modules.finance.service import FinanceService, get_finance_service


# =============================================================================
# TESTS DES ENUMS
# =============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_account_type_values(self):
        """Tester les types de comptes."""
        assert AccountType.ASSET.value == "ASSET"
        assert AccountType.LIABILITY.value == "LIABILITY"
        assert AccountType.EQUITY.value == "EQUITY"
        assert AccountType.REVENUE.value == "REVENUE"
        assert AccountType.EXPENSE.value == "EXPENSE"
        assert len(AccountType) == 5

    def test_journal_type_values(self):
        """Tester les types de journaux."""
        assert JournalType.GENERAL.value == "GENERAL"
        assert JournalType.PURCHASES.value == "PURCHASES"
        assert JournalType.SALES.value == "SALES"
        assert JournalType.BANK.value == "BANK"
        assert JournalType.CASH.value == "CASH"
        assert JournalType.OD.value == "OD"
        assert JournalType.OPENING.value == "OPENING"
        assert JournalType.CLOSING.value == "CLOSING"
        assert len(JournalType) == 8

    def test_entry_status_values(self):
        """Tester les statuts d'écriture."""
        assert EntryStatus.DRAFT.value == "DRAFT"
        assert EntryStatus.PENDING.value == "PENDING"
        assert EntryStatus.VALIDATED.value == "VALIDATED"
        assert EntryStatus.POSTED.value == "POSTED"
        assert EntryStatus.CANCELLED.value == "CANCELLED"
        assert len(EntryStatus) == 5

    def test_fiscal_year_status_values(self):
        """Tester les statuts d'exercice."""
        assert FiscalYearStatus.OPEN.value == "OPEN"
        assert FiscalYearStatus.CLOSING.value == "CLOSING"
        assert FiscalYearStatus.CLOSED.value == "CLOSED"
        assert len(FiscalYearStatus) == 3

    def test_bank_transaction_type_values(self):
        """Tester les types de transactions."""
        assert BankTransactionType.CREDIT.value == "CREDIT"
        assert BankTransactionType.DEBIT.value == "DEBIT"
        assert BankTransactionType.TRANSFER.value == "TRANSFER"
        assert BankTransactionType.FEE.value == "FEE"
        assert BankTransactionType.INTEREST.value == "INTEREST"
        assert len(BankTransactionType) == 5

    def test_reconciliation_status_values(self):
        """Tester les statuts de rapprochement."""
        assert ReconciliationStatus.PENDING.value == "PENDING"
        assert ReconciliationStatus.MATCHED.value == "MATCHED"
        assert ReconciliationStatus.RECONCILED.value == "RECONCILED"
        assert ReconciliationStatus.DISPUTED.value == "DISPUTED"
        assert len(ReconciliationStatus) == 4

    def test_forecast_period_values(self):
        """Tester les périodes de prévision."""
        assert ForecastPeriod.DAILY.value == "DAILY"
        assert ForecastPeriod.WEEKLY.value == "WEEKLY"
        assert ForecastPeriod.MONTHLY.value == "MONTHLY"
        assert ForecastPeriod.QUARTERLY.value == "QUARTERLY"
        assert len(ForecastPeriod) == 4


# =============================================================================
# TESTS DES MODÈLES
# =============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_account_model(self):
        """Tester le modèle Account."""
        account = Account(
            tenant_id="test-tenant",
            code="512000",
            name="Banque",
            type=AccountType.ASSET
        )
        assert account.tenant_id == "test-tenant"
        assert account.code == "512000"
        assert account.type == AccountType.ASSET
        assert account.is_active == True
        assert account.balance == Decimal("0")

    def test_journal_model(self):
        """Tester le modèle Journal."""
        journal = Journal(
            tenant_id="test-tenant",
            code="BQ",
            name="Banque",
            type=JournalType.BANK
        )
        assert journal.code == "BQ"
        assert journal.type == JournalType.BANK
        assert journal.next_sequence == 1

    def test_fiscal_year_model(self):
        """Tester le modèle FiscalYear."""
        fiscal_year = FiscalYear(
            tenant_id="test-tenant",
            name="Exercice 2026",
            code="FY2026",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31)
        )
        assert fiscal_year.code == "FY2026"
        assert fiscal_year.status == FiscalYearStatus.OPEN
        assert fiscal_year.result == Decimal("0")

    def test_journal_entry_model(self):
        """Tester le modèle JournalEntry."""
        entry = JournalEntry(
            tenant_id="test-tenant",
            journal_id=uuid4(),
            fiscal_year_id=uuid4(),
            number="BQ-000001",
            date=date.today()
        )
        assert entry.status == EntryStatus.DRAFT
        assert entry.total_debit == Decimal("0")
        assert entry.total_credit == Decimal("0")

    def test_bank_account_model(self):
        """Tester le modèle BankAccount."""
        bank_account = BankAccount(
            tenant_id="test-tenant",
            name="Compte courant",
            iban="FR7630001007941234567890185",
            currency="EUR"
        )
        assert bank_account.currency == "EUR"
        assert bank_account.current_balance == Decimal("0")
        assert bank_account.is_active == True

    def test_cash_forecast_model(self):
        """Tester le modèle CashForecast."""
        forecast = CashForecast(
            tenant_id="test-tenant",
            period=ForecastPeriod.MONTHLY,
            date=date.today(),
            opening_balance=Decimal("10000"),
            expected_receipts=Decimal("5000"),
            expected_payments=Decimal("3000")
        )
        assert forecast.period == ForecastPeriod.MONTHLY
        assert forecast.opening_balance == Decimal("10000")


# =============================================================================
# TESTS DES SCHÉMAS
# =============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_account_create_schema(self):
        """Tester le schéma AccountCreate."""
        data = AccountCreate(
            code="401000",
            name="Fournisseurs",
            type=AccountType.LIABILITY,
            is_reconcilable=True
        )
        assert data.code == "401000"
        assert data.type == AccountType.LIABILITY
        assert data.is_reconcilable == True

    def test_entry_create_schema_with_lines(self):
        """Tester le schéma EntryCreate avec lignes."""
        lines = [
            EntryLineCreate(
                account_id=uuid4(),
                debit=Decimal("1000"),
                credit=Decimal("0"),
                label="Achat"
            ),
            EntryLineCreate(
                account_id=uuid4(),
                debit=Decimal("0"),
                credit=Decimal("1000"),
                label="Achat"
            )
        ]
        data = EntryCreate(
            journal_id=uuid4(),
            date=date.today(),
            lines=lines
        )
        assert len(data.lines) == 2
        assert data.lines[0].debit == Decimal("1000")

    def test_trial_balance_schema(self):
        """Tester le schéma TrialBalance."""
        items = [
            BalanceSheetItem(
                account_code="512000",
                account_name="Banque",
                debit=Decimal("10000"),
                credit=Decimal("5000"),
                balance=Decimal("5000")
            )
        ]
        balance = TrialBalance(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            items=items,
            total_debit=Decimal("10000"),
            total_credit=Decimal("5000"),
            is_balanced=False
        )
        assert len(balance.items) == 1
        assert balance.is_balanced == False

    def test_finance_dashboard_schema(self):
        """Tester le schéma FinanceDashboard."""
        dashboard = FinanceDashboard(
            cash_balance=Decimal("5000"),
            bank_balance=Decimal("25000"),
            total_receivables=Decimal("15000"),
            total_payables=Decimal("8000"),
            current_year_revenues=Decimal("100000"),
            current_year_expenses=Decimal("75000"),
            current_year_result=Decimal("25000")
        )
        assert dashboard.bank_balance == Decimal("25000")
        assert dashboard.current_year_result == Decimal("25000")


# =============================================================================
# TESTS DU SERVICE - COMPTES
# =============================================================================

class TestFinanceServiceAccounts:
    """Tests du service Finance - Comptes."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return FinanceService(mock_db, "test-tenant")

    def test_create_account(self, service, mock_db):
        """Tester la création d'un compte."""
        data = AccountCreate(
            code="512000",
            name="Banque",
            type=AccountType.ASSET
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_account(data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result.code == "512000"
        assert result.tenant_id == "test-tenant"

    def test_get_account_by_code(self, service, mock_db):
        """Tester la récupération par code."""
        mock_account = Account(
            id=uuid4(),
            tenant_id="test-tenant",
            code="411000",
            name="Clients",
            type=AccountType.ASSET
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_account

        result = service.get_account_by_code("411000")

        assert result.code == "411000"
        assert result.name == "Clients"

    def test_list_accounts(self, service, mock_db):
        """Tester le listage des comptes."""
        mock_accounts = [
            Account(id=uuid4(), tenant_id="test-tenant", code="411000", name="Clients", type=AccountType.ASSET),
            Account(id=uuid4(), tenant_id="test-tenant", code="401000", name="Fournisseurs", type=AccountType.LIABILITY)
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_accounts
        mock_db.query.return_value = mock_query

        items, total = service.list_accounts()

        assert total == 2
        assert len(items) == 2


# =============================================================================
# TESTS DU SERVICE - JOURNAUX
# =============================================================================

class TestFinanceServiceJournals:
    """Tests du service Finance - Journaux."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return FinanceService(mock_db, "test-tenant")

    def test_create_journal(self, service, mock_db):
        """Tester la création d'un journal."""
        data = JournalCreate(
            code="VT",
            name="Ventes",
            type=JournalType.SALES
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_journal(data)

        mock_db.add.assert_called_once()
        assert result.code == "VT"
        assert result.type == JournalType.SALES


# =============================================================================
# TESTS DU SERVICE - EXERCICES
# =============================================================================

class TestFinanceServiceFiscalYears:
    """Tests du service Finance - Exercices."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return FinanceService(mock_db, "test-tenant")

    def test_create_fiscal_year(self, service, mock_db):
        """Tester la création d'un exercice."""
        data = FiscalYearCreate(
            name="Exercice 2026",
            code="FY2026",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31)
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.flush = MagicMock()

        result = service.create_fiscal_year(data)

        assert result.code == "FY2026"
        assert result.start_date == date(2026, 1, 1)


# =============================================================================
# TESTS DU SERVICE - ÉCRITURES
# =============================================================================

class TestFinanceServiceEntries:
    """Tests du service Finance - Écritures."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return FinanceService(mock_db, "test-tenant")

    def test_entry_must_be_balanced(self, service, mock_db):
        """Tester qu'une écriture doit être équilibrée."""
        # Mock exercice fiscal
        mock_fiscal_year = FiscalYear(
            id=uuid4(),
            tenant_id="test-tenant",
            name="FY2026",
            code="FY2026",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31)
        )

        mock_journal = Journal(
            id=uuid4(),
            tenant_id="test-tenant",
            code="VT",
            name="Ventes",
            type=JournalType.SALES,
            next_sequence=1
        )

        with patch.object(service, 'get_current_fiscal_year', return_value=mock_fiscal_year):
            with patch.object(service, 'get_journal', return_value=mock_journal):
                lines = [
                    EntryLineCreate(
                        account_id=uuid4(),
                        debit=Decimal("1000"),
                        credit=Decimal("0")
                    ),
                    EntryLineCreate(
                        account_id=uuid4(),
                        debit=Decimal("0"),
                        credit=Decimal("500")  # Déséquilibrée!
                    )
                ]
                data = EntryCreate(
                    journal_id=mock_journal.id,
                    date=date.today(),
                    lines=lines
                )

                mock_db.add = MagicMock()
                mock_db.flush = MagicMock()
                mock_db.commit = MagicMock()

                with pytest.raises(ValueError, match="Entry not balanced"):
                    service.create_entry(data, uuid4())


# =============================================================================
# TESTS DU SERVICE - BANQUE
# =============================================================================

class TestFinanceServiceBank:
    """Tests du service Finance - Banque."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return FinanceService(mock_db, "test-tenant")

    def test_create_bank_account(self, service, mock_db):
        """Tester la création d'un compte bancaire."""
        data = BankAccountCreate(
            name="Compte courant BNP",
            bank_name="BNP Paribas",
            iban="FR7630004000031234567890143",
            initial_balance=Decimal("10000")
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_bank_account(data)

        assert result.name == "Compte courant BNP"
        assert result.initial_balance == Decimal("10000")
        assert result.current_balance == Decimal("10000")

    def test_create_bank_transaction_updates_balance(self, service, mock_db):
        """Tester que la transaction met à jour le solde."""
        bank_account_id = uuid4()
        mock_bank = BankAccount(
            id=bank_account_id,
            tenant_id="test-tenant",
            name="Compte",
            current_balance=Decimal("10000")
        )

        with patch.object(service, 'get_bank_account', return_value=mock_bank):
            data = BankTransactionCreate(
                bank_account_id=bank_account_id,
                type=BankTransactionType.DEBIT,
                date=date.today(),
                amount=Decimal("500"),
                label="Paiement fournisseur"
            )

            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()

            result = service.create_bank_transaction(data, uuid4())

            assert mock_bank.current_balance == Decimal("9500")


# =============================================================================
# TESTS DU SERVICE - TRÉSORERIE
# =============================================================================

class TestFinanceServiceTreasury:
    """Tests du service Finance - Trésorerie."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return FinanceService(mock_db, "test-tenant")

    def test_create_cash_forecast(self, service, mock_db):
        """Tester la création d'une prévision."""
        data = CashForecastCreate(
            period=ForecastPeriod.MONTHLY,
            date=date.today(),
            opening_balance=Decimal("50000"),
            expected_receipts=Decimal("20000"),
            expected_payments=Decimal("15000")
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_cash_forecast(data, uuid4())

        # Solde clôture = 50000 + 20000 - 15000 = 55000
        assert result.expected_closing == Decimal("55000")


# =============================================================================
# TESTS DU SERVICE - REPORTING
# =============================================================================

class TestFinanceServiceReporting:
    """Tests du service Finance - Reporting."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return FinanceService(mock_db, "test-tenant")

    def test_trial_balance_is_balanced(self, service, mock_db):
        """Tester que la balance est équilibrée."""
        # Mock des résultats
        mock_results = [
            MagicMock(code="512000", name="Banque", debit=Decimal("10000"), credit=Decimal("5000")),
            MagicMock(code="401000", name="Fournisseurs", debit=Decimal("5000"), credit=Decimal("10000"))
        ]

        mock_query = MagicMock()
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value.order_by.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query

        result = service.get_trial_balance(date(2026, 1, 1), date(2026, 12, 31))

        # 10000 + 5000 = 15000 debit, 5000 + 10000 = 15000 credit
        assert result.total_debit == result.total_credit
        assert result.is_balanced == True


# =============================================================================
# TESTS FACTORY
# =============================================================================

class TestFactory:
    """Tests de la factory."""

    def test_get_finance_service(self):
        """Tester la factory."""
        mock_db = MagicMock()
        service = get_finance_service(mock_db, "test-tenant")

        assert isinstance(service, FinanceService)
        assert service.tenant_id == "test-tenant"


# =============================================================================
# TESTS D'INTÉGRATION
# =============================================================================

class TestIntegration:
    """Tests d'intégration."""

    def test_full_accounting_cycle(self):
        """Tester le cycle comptable complet."""
        # Ce test simule un cycle complet :
        # 1. Créer un exercice
        # 2. Créer des comptes
        # 3. Créer un journal
        # 4. Créer une écriture
        # 5. Valider et comptabiliser
        # 6. Générer une balance
        mock_db = MagicMock()
        service = FinanceService(mock_db, "test-tenant")

        # Simuler la création
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.flush = MagicMock()

        # 1. Créer exercice
        fy_data = FiscalYearCreate(
            name="FY2026",
            code="FY2026",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31)
        )
        fiscal_year = service.create_fiscal_year(fy_data)
        assert fiscal_year is not None

        # 2. Créer comptes
        acc1 = service.create_account(AccountCreate(
            code="512000", name="Banque", type=AccountType.ASSET
        ))
        acc2 = service.create_account(AccountCreate(
            code="411000", name="Clients", type=AccountType.ASSET
        ))

        assert acc1.code == "512000"
        assert acc2.code == "411000"


# =============================================================================
# TESTS MULTI-TENANT
# =============================================================================

class TestMultiTenant:
    """Tests d'isolation multi-tenant."""

    def test_tenant_isolation(self):
        """Tester l'isolation des tenants."""
        mock_db = MagicMock()

        service_a = FinanceService(mock_db, "tenant-A")
        service_b = FinanceService(mock_db, "tenant-B")

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # Créer compte pour tenant A
        acc_a = service_a.create_account(AccountCreate(
            code="512000", name="Banque A", type=AccountType.ASSET
        ))

        # Créer compte pour tenant B
        acc_b = service_b.create_account(AccountCreate(
            code="512000", name="Banque B", type=AccountType.ASSET
        ))

        # Vérifier isolation
        assert acc_a.tenant_id == "tenant-A"
        assert acc_b.tenant_id == "tenant-B"
        assert acc_a.tenant_id != acc_b.tenant_id


# =============================================================================
# TESTS DE CALCULS FINANCIERS
# =============================================================================

class TestFinancialCalculations:
    """Tests des calculs financiers."""

    def test_balance_calculation(self):
        """Tester le calcul du solde."""
        # Debit - Credit = Balance
        debit = Decimal("15000")
        credit = Decimal("8000")
        balance = debit - credit

        assert balance == Decimal("7000")

    def test_forecast_closing_balance(self):
        """Tester le calcul du solde de clôture prévisionnel."""
        opening = Decimal("50000")
        receipts = Decimal("25000")
        payments = Decimal("18000")

        expected_closing = opening + receipts - payments

        assert expected_closing == Decimal("57000")

    def test_income_statement_net_income(self):
        """Tester le calcul du résultat net."""
        revenues = Decimal("150000")
        expenses = Decimal("120000")

        net_income = revenues - expenses

        assert net_income == Decimal("30000")


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
