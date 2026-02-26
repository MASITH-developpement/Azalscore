"""
AZALS MODULE M2 - Service Finance
=================================

Service métier pour la comptabilité et la trésorerie.
"""
from __future__ import annotations


import logging
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from .models import (
    Account,
    AccountType,
    BankAccount,
    BankStatement,
    BankStatementLine,
    BankTransaction,
    BankTransactionType,
    CashFlowCategory,
    CashForecast,
    EntryStatus,
    FinancialReport,
    FiscalPeriod,
    FiscalYear,
    FiscalYearStatus,
    ForecastPeriod,
    Journal,
    JournalEntry,
    JournalEntryLine,
    JournalType,
    ReconciliationStatus,
)
from .schemas import (
    AccountCreate,
    AccountUpdate,
    BalanceSheetItem,
    BankAccountCreate,
    BankAccountUpdate,
    BankStatementCreate,
    BankTransactionCreate,
    CashFlowCategoryCreate,
    CashForecastCreate,
    CashForecastUpdate,
    EntryCreate,
    EntryUpdate,
    FinanceDashboard,
    FinancialReportCreate,
    FiscalYearCreate,
    IncomeStatement,
    IncomeStatementItem,
    JournalCreate,
    JournalUpdate,
    TrialBalance,
)

logger = logging.getLogger(__name__)


class FinanceService:
    """Service pour la gestion financière."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # GESTION DES COMPTES
    # =========================================================================

    def create_account(self, data: AccountCreate) -> Account:
        """Créer un compte comptable."""
        account = Account(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            type=data.account_type,  # Champ réel, pas alias
            parent_id=data.parent_id,
            is_auxiliary=data.is_auxiliary,
            auxiliary_type=data.auxiliary_type,
            is_reconcilable=data.is_reconcilable,
            allow_posting=data.allow_posting
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def get_account(self, account_id: UUID) -> Account | None:
        """Récupérer un compte par ID."""
        return self.db.query(Account).filter(
            Account.id == account_id,
            Account.tenant_id == self.tenant_id
        ).first()

    def get_account_by_code(self, code: str) -> Account | None:
        """Récupérer un compte par code."""
        return self.db.query(Account).filter(
            Account.code == code,
            Account.tenant_id == self.tenant_id
        ).first()

    def list_accounts(
        self,
        account_type: AccountType | None = None,
        parent_id: UUID | None = None,
        is_active: bool = True,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[Account], int]:
        """Lister les comptes avec filtres."""
        query = self.db.query(Account).filter(
            Account.tenant_id == self.tenant_id,
            Account.is_active == is_active
        )

        if account_type:
            query = query.filter(Account.type == account_type)
        if parent_id:
            query = query.filter(Account.parent_id == parent_id)
        if search:
            query = query.filter(
                or_(
                    Account.code.ilike(f"%{search}%"),
                    Account.name.ilike(f"%{search}%")
                )
            )

        total = query.count()
        items = query.order_by(Account.code).offset(skip).limit(limit).all()
        return items, total

    def update_account(self, account_id: UUID, data: AccountUpdate) -> Account | None:
        """Mettre à jour un compte."""
        account = self.get_account(account_id)
        if not account:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(account, field, value)

        self.db.commit()
        self.db.refresh(account)
        return account

    def get_account_balance(
        self,
        account_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None
    ) -> dict:
        """Calculer le solde d'un compte."""
        query = self.db.query(
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label('total_debit'),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label('total_credit')
        ).join(JournalEntry).filter(
            JournalEntryLine.account_id == account_id,
            JournalEntry.tenant_id == self.tenant_id,
            JournalEntry.status == EntryStatus.POSTED
        )

        if start_date:
            query = query.filter(JournalEntry.date >= start_date)
        if end_date:
            query = query.filter(JournalEntry.date <= end_date)

        result = query.first()
        total_debit = result.total_debit or Decimal("0")
        total_credit = result.total_credit or Decimal("0")

        return {
            "debit": total_debit,
            "credit": total_credit,
            "balance": total_debit - total_credit
        }

    # =========================================================================
    # GESTION DES JOURNAUX
    # =========================================================================

    def create_journal(self, data: JournalCreate) -> Journal:
        """Créer un journal comptable."""
        journal = Journal(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            type=data.journal_type,  # Champ réel, pas alias
            default_debit_account_id=data.default_debit_account_id,
            default_credit_account_id=data.default_credit_account_id,
            sequence_prefix=data.sequence_prefix or data.code
        )
        self.db.add(journal)
        self.db.commit()
        self.db.refresh(journal)
        return journal

    def get_journal(self, journal_id: UUID) -> Journal | None:
        """Récupérer un journal par ID."""
        return self.db.query(Journal).filter(
            Journal.id == journal_id,
            Journal.tenant_id == self.tenant_id
        ).first()

    def list_journals(
        self,
        journal_type: JournalType | None = None,
        is_active: bool = True
    ) -> list[Journal]:
        """Lister les journaux."""
        query = self.db.query(Journal).filter(
            Journal.tenant_id == self.tenant_id,
            Journal.is_active == is_active
        )

        if journal_type:
            query = query.filter(Journal.type == journal_type)

        return query.order_by(Journal.code).all()

    def update_journal(self, journal_id: UUID, data: JournalUpdate) -> Journal | None:
        """Mettre à jour un journal."""
        journal = self.get_journal(journal_id)
        if not journal:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(journal, field, value)

        self.db.commit()
        self.db.refresh(journal)
        return journal

    def get_next_entry_number(self, journal_id: UUID, fiscal_year_id: UUID) -> str:
        """Générer le prochain numéro d'écriture."""
        journal = self.get_journal(journal_id)
        if not journal:
            raise ValueError("Journal not found")

        prefix = journal.sequence_prefix or journal.code
        sequence = journal.next_sequence

        # Incrémenter la séquence
        journal.next_sequence += 1
        self.db.commit()

        return f"{prefix}-{sequence:06d}"

    # =========================================================================
    # GESTION DES EXERCICES FISCAUX
    # =========================================================================

    def create_fiscal_year(self, data: FiscalYearCreate) -> FiscalYear:
        """Créer un exercice fiscal."""
        fiscal_year = FiscalYear(
            tenant_id=self.tenant_id,
            name=data.name,
            code=data.code,
            start_date=data.start_date,
            end_date=data.end_date
        )
        self.db.add(fiscal_year)
        self.db.commit()
        self.db.refresh(fiscal_year)

        # Créer les périodes mensuelles
        self._create_fiscal_periods(fiscal_year)

        return fiscal_year

    def _create_fiscal_periods(self, fiscal_year: FiscalYear):
        """Créer les périodes mensuelles pour un exercice."""
        from calendar import monthrange

        current_date = fiscal_year.start_date
        period_number = 1

        while current_date <= fiscal_year.end_date:
            year = current_date.year
            month = current_date.month

            # Dernier jour du mois
            _, last_day = monthrange(year, month)
            end_of_month = date(year, month, last_day)

            # Ne pas dépasser la fin de l'exercice
            period_end = min(end_of_month, fiscal_year.end_date)

            period = FiscalPeriod(
                tenant_id=self.tenant_id,
                fiscal_year_id=fiscal_year.id,
                name=f"Période {period_number:02d} - {current_date.strftime('%B %Y')}",
                number=period_number,
                start_date=current_date,
                end_date=period_end
            )
            self.db.add(period)

            # Passer au mois suivant
            current_date = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

            period_number += 1

        self.db.commit()

    def get_fiscal_year(self, fiscal_year_id: UUID) -> FiscalYear | None:
        """Récupérer un exercice par ID."""
        return self.db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id,
            FiscalYear.tenant_id == self.tenant_id
        ).first()

    def get_current_fiscal_year(self) -> FiscalYear | None:
        """Récupérer l'exercice en cours."""
        today = date.today()
        return self.db.query(FiscalYear).filter(
            FiscalYear.tenant_id == self.tenant_id,
            FiscalYear.start_date <= today,
            FiscalYear.end_date >= today,
            FiscalYear.status == FiscalYearStatus.OPEN
        ).first()

    def list_fiscal_years(self) -> list[FiscalYear]:
        """Lister les exercices."""
        return self.db.query(FiscalYear).filter(
            FiscalYear.tenant_id == self.tenant_id
        ).order_by(FiscalYear.start_date.desc()).all()

    def get_fiscal_periods(self, fiscal_year_id: UUID) -> list[FiscalPeriod]:
        """Récupérer les périodes d'un exercice."""
        return self.db.query(FiscalPeriod).filter(
            FiscalPeriod.fiscal_year_id == fiscal_year_id,
            FiscalPeriod.tenant_id == self.tenant_id
        ).order_by(FiscalPeriod.number).all()

    def close_fiscal_period(self, period_id: UUID, user_id: UUID) -> FiscalPeriod | None:
        """Clôturer une période."""
        logger.info(
            "Closing fiscal period | tenant=%s user=%s period_id=%s",
            self.tenant_id, user_id, period_id
        )
        period = self.db.query(FiscalPeriod).filter(
            FiscalPeriod.id == period_id,
            FiscalPeriod.tenant_id == self.tenant_id
        ).first()

        if not period or period.is_closed:
            logger.warning(
                "Fiscal period not found or already closed | tenant=%s period_id=%s",
                self.tenant_id, period_id
            )
            return None

        # Calculer les totaux
        totals = self.db.query(
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label('total_debit'),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label('total_credit')
        ).join(JournalEntry).filter(
            JournalEntry.tenant_id == self.tenant_id,
            JournalEntry.date >= period.start_date,
            JournalEntry.date <= period.end_date,
            JournalEntry.status == EntryStatus.POSTED
        ).first()

        period.is_closed = True
        period.closed_at = datetime.utcnow()
        period.closed_by = user_id
        period.total_debit = totals.total_debit
        period.total_credit = totals.total_credit

        self.db.commit()
        self.db.refresh(period)
        logger.info(
            "Fiscal period closed | period_id=%s name=%s total_debit=%s total_credit=%s",
            period.id, period.name, period.total_debit, period.total_credit
        )
        return period

    def close_fiscal_year(self, fiscal_year_id: UUID, user_id: UUID) -> FiscalYear | None:
        """Clôturer un exercice."""
        logger.info(
            "Closing fiscal year | tenant=%s user=%s fiscal_year_id=%s",
            self.tenant_id, user_id, fiscal_year_id
        )
        fiscal_year = self.get_fiscal_year(fiscal_year_id)
        if not fiscal_year or fiscal_year.status == FiscalYearStatus.CLOSED:
            logger.warning(
                "Fiscal year not found or already closed | tenant=%s fiscal_year_id=%s",
                self.tenant_id, fiscal_year_id
            )
            return None

        # Vérifier que toutes les périodes sont clôturées
        # SÉCURITÉ: Toujours filtrer par tenant_id
        open_periods = self.db.query(FiscalPeriod).filter(
            FiscalPeriod.tenant_id == self.tenant_id,
            FiscalPeriod.fiscal_year_id == fiscal_year_id,
            not FiscalPeriod.is_closed
        ).count()

        if open_periods > 0:
            raise ValueError(f"{open_periods} période(s) non clôturée(s)")

        # Calculer les totaux
        totals = self.db.query(
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label('total_debit'),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label('total_credit')
        ).join(JournalEntry).filter(
            JournalEntry.fiscal_year_id == fiscal_year_id,
            JournalEntry.status == EntryStatus.POSTED
        ).first()

        fiscal_year.status = FiscalYearStatus.CLOSED
        fiscal_year.closed_at = datetime.utcnow()
        fiscal_year.closed_by = user_id
        fiscal_year.total_debit = totals.total_debit
        fiscal_year.total_credit = totals.total_credit
        fiscal_year.result = totals.total_credit - totals.total_debit

        self.db.commit()
        self.db.refresh(fiscal_year)
        logger.info(
            "Fiscal year closed | fiscal_year_id=%s code=%s result=%s",
            fiscal_year.id, fiscal_year.code, fiscal_year.result
        )
        return fiscal_year

    # =========================================================================
    # GESTION DES ÉCRITURES COMPTABLES
    # =========================================================================

    def create_entry(self, data: EntryCreate, user_id: UUID) -> JournalEntry:
        """Créer une écriture comptable."""
        # Vérifier l'exercice fiscal
        fiscal_year = self.get_current_fiscal_year()
        if not fiscal_year:
            raise ValueError("No open fiscal year found")

        if data.entry_date < fiscal_year.start_date or data.entry_date > fiscal_year.end_date:
            raise ValueError("Date outside current fiscal year")

        # Générer le numéro
        entry_number = self.get_next_entry_number(data.journal_id, fiscal_year.id)

        # Créer l'écriture
        entry = JournalEntry(
            tenant_id=self.tenant_id,
            journal_id=data.journal_id,
            fiscal_year_id=fiscal_year.id,
            number=entry_number,
            date=data.entry_date,  # Champ réel, pas alias
            reference=data.reference,
            description=data.description,
            created_by=user_id
        )
        self.db.add(entry)
        self.db.flush()

        # Créer les lignes
        total_debit = Decimal("0")
        total_credit = Decimal("0")

        for i, line_data in enumerate(data.lines, 1):
            line = JournalEntryLine(
                tenant_id=self.tenant_id,
                entry_id=entry.id,
                line_number=i,
                account_id=line_data.account_id,
                debit=line_data.debit,
                credit=line_data.credit,
                label=line_data.label,
                partner_id=line_data.partner_id,
                partner_type=line_data.partner_type,
                analytic_account=line_data.analytic_account,
                analytic_tags=line_data.analytic_tags
            )
            self.db.add(line)
            total_debit += line_data.debit
            total_credit += line_data.credit

        # Vérifier l'équilibre
        if total_debit != total_credit:
            raise ValueError(f"Entry not balanced: debit={total_debit}, credit={total_credit}")

        entry.total_debit = total_debit
        entry.total_credit = total_credit

        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_entry(self, entry_id: UUID) -> JournalEntry | None:
        """Récupérer une écriture par ID."""
        return self.db.query(JournalEntry).filter(
            JournalEntry.id == entry_id,
            JournalEntry.tenant_id == self.tenant_id
        ).first()

    def list_entries(
        self,
        journal_id: UUID | None = None,
        fiscal_year_id: UUID | None = None,
        status: EntryStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[JournalEntry], int]:
        """Lister les écritures avec filtres."""
        query = self.db.query(JournalEntry).filter(
            JournalEntry.tenant_id == self.tenant_id
        )

        if journal_id:
            query = query.filter(JournalEntry.journal_id == journal_id)
        if fiscal_year_id:
            query = query.filter(JournalEntry.fiscal_year_id == fiscal_year_id)
        if status:
            query = query.filter(JournalEntry.status == status)
        if start_date:
            query = query.filter(JournalEntry.date >= start_date)
        if end_date:
            query = query.filter(JournalEntry.date <= end_date)

        total = query.count()
        items = query.order_by(JournalEntry.date.desc(), JournalEntry.number.desc()).offset(skip).limit(limit).all()
        return items, total

    def update_entry(self, entry_id: UUID, data: EntryUpdate) -> JournalEntry | None:
        """Mettre à jour une écriture (brouillon uniquement)."""
        entry = self.get_entry(entry_id)
        if not entry or entry.status != EntryStatus.DRAFT:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)

        self.db.commit()
        self.db.refresh(entry)
        return entry

    def validate_entry(self, entry_id: UUID, user_id: UUID) -> JournalEntry | None:
        """Valider une écriture."""
        entry = self.get_entry(entry_id)
        if not entry or entry.status != EntryStatus.DRAFT:
            return None

        entry.status = EntryStatus.VALIDATED
        entry.validated_by = user_id
        entry.validated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(entry)
        return entry

    def post_entry(self, entry_id: UUID, user_id: UUID) -> JournalEntry | None:
        """Comptabiliser une écriture."""
        entry = self.get_entry(entry_id)
        if not entry or entry.status not in [EntryStatus.DRAFT, EntryStatus.VALIDATED]:
            return None

        entry.status = EntryStatus.POSTED
        entry.posted_by = user_id
        entry.posted_at = datetime.utcnow()

        if not entry.validated_by:
            entry.validated_by = user_id
            entry.validated_at = datetime.utcnow()

        # Mettre à jour les soldes des comptes
        for line in entry.lines:
            account = self.get_account(line.account_id)
            if account:
                account.balance_debit += line.debit
                account.balance_credit += line.credit
                account.balance = account.balance_debit - account.balance_credit

        self.db.commit()
        self.db.refresh(entry)
        return entry

    def cancel_entry(self, entry_id: UUID) -> JournalEntry | None:
        """Annuler une écriture."""
        entry = self.get_entry(entry_id)
        if not entry or entry.status == EntryStatus.CANCELLED:
            return None

        # Si comptabilisée, reverser les soldes
        if entry.status == EntryStatus.POSTED:
            for line in entry.lines:
                account = self.get_account(line.account_id)
                if account:
                    account.balance_debit -= line.debit
                    account.balance_credit -= line.credit
                    account.balance = account.balance_debit - account.balance_credit

        entry.status = EntryStatus.CANCELLED
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_entry_lines(self, entry_id: UUID) -> list[JournalEntryLine]:
        """Récupérer les lignes d'une écriture."""
        return self.db.query(JournalEntryLine).filter(
            JournalEntryLine.entry_id == entry_id,
            JournalEntryLine.tenant_id == self.tenant_id
        ).order_by(JournalEntryLine.line_number).all()

    # =========================================================================
    # GESTION DES COMPTES BANCAIRES
    # =========================================================================

    def create_bank_account(self, data: BankAccountCreate) -> BankAccount:
        """Créer un compte bancaire."""
        bank_account = BankAccount(
            tenant_id=self.tenant_id,
            name=data.name,
            bank_name=data.bank_name,
            account_number=data.account_number,
            iban=data.iban,
            bic=data.bic,
            account_id=data.account_id,
            journal_id=data.journal_id,
            currency=data.currency,
            initial_balance=data.initial_balance,
            current_balance=data.initial_balance
        )
        self.db.add(bank_account)
        self.db.commit()
        self.db.refresh(bank_account)
        return bank_account

    def get_bank_account(self, bank_account_id: UUID) -> BankAccount | None:
        """Récupérer un compte bancaire par ID."""
        return self.db.query(BankAccount).filter(
            BankAccount.id == bank_account_id,
            BankAccount.tenant_id == self.tenant_id
        ).first()

    def list_bank_accounts(self, is_active: bool = True) -> list[BankAccount]:
        """Lister les comptes bancaires."""
        return self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankAccount.is_active == is_active
        ).order_by(BankAccount.name).all()

    def update_bank_account(self, bank_account_id: UUID, data: BankAccountUpdate) -> BankAccount | None:
        """Mettre à jour un compte bancaire."""
        bank_account = self.get_bank_account(bank_account_id)
        if not bank_account:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bank_account, field, value)

        self.db.commit()
        self.db.refresh(bank_account)
        return bank_account

    # =========================================================================
    # GESTION DES RELEVÉS BANCAIRES
    # =========================================================================

    def create_bank_statement(self, data: BankStatementCreate, user_id: UUID) -> BankStatement:
        """Créer un relevé bancaire."""
        statement = BankStatement(
            tenant_id=self.tenant_id,
            bank_account_id=data.bank_account_id,
            name=data.name,
            reference=data.reference,
            date=data.statement_date,  # Champ réel, pas alias
            start_date=data.start_date,
            end_date=data.end_date,
            opening_balance=data.opening_balance,
            closing_balance=data.closing_balance,
            created_by=user_id
        )
        self.db.add(statement)
        self.db.flush()

        # Créer les lignes
        total_credits = Decimal("0")
        total_debits = Decimal("0")

        for line_data in data.lines:
            line = BankStatementLine(
                tenant_id=self.tenant_id,
                statement_id=statement.id,
                date=line_data.line_date,  # Champ réel, pas alias
                value_date=line_data.value_date,
                label=line_data.label,
                reference=line_data.reference,
                amount=line_data.amount
            )
            self.db.add(line)

            if line_data.amount > 0:
                total_credits += line_data.amount
            else:
                total_debits += abs(line_data.amount)

        statement.total_credits = total_credits
        statement.total_debits = total_debits

        self.db.commit()
        self.db.refresh(statement)
        return statement

    def get_bank_statement(self, statement_id: UUID) -> BankStatement | None:
        """Récupérer un relevé par ID."""
        return self.db.query(BankStatement).filter(
            BankStatement.id == statement_id,
            BankStatement.tenant_id == self.tenant_id
        ).first()

    def list_bank_statements(
        self,
        bank_account_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[BankStatement], int]:
        """Lister les relevés bancaires."""
        query = self.db.query(BankStatement).filter(
            BankStatement.tenant_id == self.tenant_id
        )

        if bank_account_id:
            query = query.filter(BankStatement.bank_account_id == bank_account_id)

        total = query.count()
        items = query.order_by(BankStatement.date.desc()).offset(skip).limit(limit).all()
        return items, total

    def reconcile_statement_line(
        self,
        line_id: UUID,
        entry_line_id: UUID
    ) -> BankStatementLine | None:
        """Rapprocher une ligne de relevé avec une écriture."""
        line = self.db.query(BankStatementLine).filter(
            BankStatementLine.id == line_id,
            BankStatementLine.tenant_id == self.tenant_id
        ).first()

        if not line or line.status == ReconciliationStatus.RECONCILED:
            return None

        line.status = ReconciliationStatus.RECONCILED
        line.matched_entry_line_id = entry_line_id
        line.matched_at = datetime.utcnow()

        # Mettre à jour la ligne d'écriture
        # SÉCURITÉ: Toujours filtrer par tenant_id
        entry_line = self.db.query(JournalEntryLine).filter(
            JournalEntryLine.tenant_id == self.tenant_id,
            JournalEntryLine.id == entry_line_id
        ).first()

        if entry_line:
            entry_line.reconciled_at = datetime.utcnow()
            entry_line.reconcile_ref = f"BANK-{line.statement_id}"

        self.db.commit()
        self.db.refresh(line)
        return line

    # =========================================================================
    # GESTION DES TRANSACTIONS BANCAIRES
    # =========================================================================

    def create_bank_transaction(self, data: BankTransactionCreate, user_id: UUID) -> BankTransaction:
        """Créer une transaction bancaire."""
        transaction = BankTransaction(
            tenant_id=self.tenant_id,
            bank_account_id=data.bank_account_id,
            type=data.transaction_type,  # Champ réel, pas alias
            date=data.transaction_date,  # Champ réel, pas alias
            value_date=data.value_date,
            amount=data.amount,
            label=data.label,
            reference=data.reference,
            partner_name=data.partner_name,
            category=data.category,
            created_by=user_id
        )
        self.db.add(transaction)

        # Mettre à jour le solde du compte
        bank_account = self.get_bank_account(data.bank_account_id)
        if bank_account:
            if data.transaction_type in [BankTransactionType.CREDIT, BankTransactionType.INTEREST]:
                bank_account.current_balance += data.amount
            else:
                bank_account.current_balance -= data.amount

        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def list_bank_transactions(
        self,
        bank_account_id: UUID | None = None,
        transaction_type: BankTransactionType | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[BankTransaction], int]:
        """Lister les transactions bancaires."""
        query = self.db.query(BankTransaction).filter(
            BankTransaction.tenant_id == self.tenant_id
        )

        if bank_account_id:
            query = query.filter(BankTransaction.bank_account_id == bank_account_id)
        if transaction_type:
            query = query.filter(BankTransaction.type == transaction_type)
        if start_date:
            query = query.filter(BankTransaction.date >= start_date)
        if end_date:
            query = query.filter(BankTransaction.date <= end_date)

        total = query.count()
        items = query.order_by(BankTransaction.date.desc()).offset(skip).limit(limit).all()
        return items, total

    # =========================================================================
    # GESTION DE LA TRÉSORERIE
    # =========================================================================

    def create_cash_forecast(self, data: CashForecastCreate, user_id: UUID) -> CashForecast:
        """Créer une prévision de trésorerie."""
        logger.info(
            "Creating cash forecast | tenant=%s user=%s period=%s date=%s opening_balance=%s",
            self.tenant_id, user_id, data.period, data.forecast_date, data.opening_balance
        )
        # Calculer le solde de clôture prévu
        expected_closing = data.opening_balance + data.expected_receipts - data.expected_payments

        forecast = CashForecast(
            tenant_id=self.tenant_id,
            period=data.period,
            date=data.forecast_date,  # Champ réel, pas alias
            opening_balance=data.opening_balance,
            expected_receipts=data.expected_receipts,
            expected_payments=data.expected_payments,
            expected_closing=expected_closing,
            details=data.details,
            created_by=user_id
        )
        self.db.add(forecast)
        self.db.commit()
        self.db.refresh(forecast)
        logger.info(
            "Cash forecast created | forecast_id=%s period=%s expected_closing=%s",
            forecast.id, forecast.period, forecast.expected_closing
        )
        return forecast

    def get_cash_forecast(self, forecast_id: UUID) -> CashForecast | None:
        """Récupérer une prévision par ID."""
        return self.db.query(CashForecast).filter(
            CashForecast.id == forecast_id,
            CashForecast.tenant_id == self.tenant_id
        ).first()

    def list_cash_forecasts(
        self,
        period: ForecastPeriod | None = None,
        start_date: date | None = None,
        end_date: date | None = None
    ) -> list[CashForecast]:
        """Lister les prévisions."""
        query = self.db.query(CashForecast).filter(
            CashForecast.tenant_id == self.tenant_id
        )

        if period:
            query = query.filter(CashForecast.period == period)
        if start_date:
            query = query.filter(CashForecast.date >= start_date)
        if end_date:
            query = query.filter(CashForecast.date <= end_date)

        return query.order_by(CashForecast.date).all()

    def update_cash_forecast(self, forecast_id: UUID, data: CashForecastUpdate) -> CashForecast | None:
        """Mettre à jour une prévision."""
        forecast = self.get_cash_forecast(forecast_id)
        if not forecast:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(forecast, field, value)

        # Recalculer si nécessaire
        if 'actual_receipts' in update_data or 'actual_payments' in update_data:
            if forecast.actual_closing is None:
                forecast.actual_closing = (
                    forecast.opening_balance +
                    forecast.actual_receipts -
                    forecast.actual_payments
                )

        self.db.commit()
        self.db.refresh(forecast)
        return forecast

    # =========================================================================
    # CATÉGORIES DE FLUX
    # =========================================================================

    def create_cash_flow_category(self, data: CashFlowCategoryCreate) -> CashFlowCategory:
        """Créer une catégorie de flux de trésorerie."""
        logger.info(
            "Creating cash flow category | tenant=%s code=%s name=%s is_receipt=%s",
            self.tenant_id, data.code, data.name, data.is_receipt
        )
        category = CashFlowCategory(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            is_receipt=data.is_receipt,
            parent_id=data.parent_id,
            order=data.order,
            default_account_id=data.default_account_id
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        logger.info(
            "Cash flow category created | category_id=%s code=%s",
            category.id, category.code
        )
        return category

    def list_cash_flow_categories(self, is_receipt: bool | None = None) -> list[CashFlowCategory]:
        """Lister les catégories de flux."""
        query = self.db.query(CashFlowCategory).filter(
            CashFlowCategory.tenant_id == self.tenant_id,
            CashFlowCategory.is_active
        )

        if is_receipt is not None:
            query = query.filter(CashFlowCategory.is_receipt == is_receipt)

        return query.order_by(CashFlowCategory.order, CashFlowCategory.code).all()

    # =========================================================================
    # REPORTING FINANCIER
    # =========================================================================

    def get_trial_balance(
        self,
        start_date: date,
        end_date: date,
        fiscal_year_id: UUID | None = None
    ) -> TrialBalance:
        """Générer la balance générale."""
        query = self.db.query(
            Account.code,
            Account.name,
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label('debit'),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label('credit')
        ).outerjoin(
            JournalEntryLine, JournalEntryLine.account_id == Account.id
        ).outerjoin(
            JournalEntry, JournalEntryLine.entry_id == JournalEntry.id
        ).filter(
            Account.tenant_id == self.tenant_id,
            Account.is_active
        )

        # Filtrer par dates et statut
        query = query.filter(
            or_(
                JournalEntry.id.is_(None),
                and_(
                    JournalEntry.date >= start_date,
                    JournalEntry.date <= end_date,
                    JournalEntry.status == EntryStatus.POSTED
                )
            )
        )

        if fiscal_year_id:
            query = query.filter(
                or_(
                    JournalEntry.id.is_(None),
                    JournalEntry.fiscal_year_id == fiscal_year_id
                )
            )

        results = query.group_by(Account.code, Account.name).order_by(Account.code).all()

        items = []
        total_debit = Decimal("0")
        total_credit = Decimal("0")

        for row in results:
            debit = row.debit or Decimal("0")
            credit = row.credit or Decimal("0")
            balance = debit - credit

            if debit != 0 or credit != 0:
                items.append(BalanceSheetItem(
                    account_code=row.code,
                    account_name=row.name,
                    debit=debit,
                    credit=credit,
                    balance=balance
                ))
                total_debit += debit
                total_credit += credit

        return TrialBalance(
            start_date=start_date,
            end_date=end_date,
            items=items,
            total_debit=total_debit,
            total_credit=total_credit,
            is_balanced=(total_debit == total_credit)
        )

    def get_income_statement(
        self,
        start_date: date,
        end_date: date
    ) -> IncomeStatement:
        """Générer le compte de résultat."""
        # Revenus (classe 7)
        revenues_query = self.db.query(
            Account.code,
            Account.name,
            func.coalesce(func.sum(JournalEntryLine.credit - JournalEntryLine.debit), 0).label('amount')
        ).outerjoin(
            JournalEntryLine, JournalEntryLine.account_id == Account.id
        ).outerjoin(
            JournalEntry, JournalEntryLine.entry_id == JournalEntry.id
        ).filter(
            Account.tenant_id == self.tenant_id,
            Account.type == AccountType.REVENUE,
            Account.is_active
        ).filter(
            or_(
                JournalEntry.id.is_(None),
                and_(
                    JournalEntry.date >= start_date,
                    JournalEntry.date <= end_date,
                    JournalEntry.status == EntryStatus.POSTED
                )
            )
        ).group_by(Account.code, Account.name).order_by(Account.code)

        revenues = []
        total_revenues = Decimal("0")

        for row in revenues_query.all():
            amount = row.amount or Decimal("0")
            if amount != 0:
                revenues.append(IncomeStatementItem(
                    category="REVENUE",
                    label=f"{row.code} - {row.name}",
                    amount=amount
                ))
                total_revenues += amount

        # Charges (classe 6)
        expenses_query = self.db.query(
            Account.code,
            Account.name,
            func.coalesce(func.sum(JournalEntryLine.debit - JournalEntryLine.credit), 0).label('amount')
        ).outerjoin(
            JournalEntryLine, JournalEntryLine.account_id == Account.id
        ).outerjoin(
            JournalEntry, JournalEntryLine.entry_id == JournalEntry.id
        ).filter(
            Account.tenant_id == self.tenant_id,
            Account.type == AccountType.EXPENSE,
            Account.is_active
        ).filter(
            or_(
                JournalEntry.id.is_(None),
                and_(
                    JournalEntry.date >= start_date,
                    JournalEntry.date <= end_date,
                    JournalEntry.status == EntryStatus.POSTED
                )
            )
        ).group_by(Account.code, Account.name).order_by(Account.code)

        expenses = []
        total_expenses = Decimal("0")

        for row in expenses_query.all():
            amount = row.amount or Decimal("0")
            if amount != 0:
                expenses.append(IncomeStatementItem(
                    category="EXPENSE",
                    label=f"{row.code} - {row.name}",
                    amount=amount
                ))
                total_expenses += amount

        return IncomeStatement(
            start_date=start_date,
            end_date=end_date,
            revenues=revenues,
            expenses=expenses,
            total_revenues=total_revenues,
            total_expenses=total_expenses,
            net_income=total_revenues - total_expenses
        )

    def create_financial_report(
        self,
        data: FinancialReportCreate,
        user_id: UUID
    ) -> FinancialReport:
        """Générer et sauvegarder un rapport financier."""
        report_data = {}

        if data.report_type == "TRIAL_BALANCE":
            trial_balance = self.get_trial_balance(
                data.start_date,
                data.end_date,
                data.fiscal_year_id
            )
            report_data = trial_balance.model_dump()
        elif data.report_type == "INCOME_STATEMENT":
            income_statement = self.get_income_statement(
                data.start_date,
                data.end_date
            )
            report_data = income_statement.model_dump()

        report = FinancialReport(
            tenant_id=self.tenant_id,
            report_type=data.report_type,
            name=f"{data.report_type} - {data.start_date} to {data.end_date}",
            fiscal_year_id=data.fiscal_year_id,
            period_id=data.period_id,
            start_date=data.start_date,
            end_date=data.end_date,
            data=report_data,
            parameters=data.parameters,
            generated_by=user_id
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def list_financial_reports(
        self,
        report_type: str | None = None,
        fiscal_year_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[FinancialReport], int]:
        """Lister les rapports financiers."""
        query = self.db.query(FinancialReport).filter(
            FinancialReport.tenant_id == self.tenant_id
        )

        if report_type:
            query = query.filter(FinancialReport.report_type == report_type)
        if fiscal_year_id:
            query = query.filter(FinancialReport.fiscal_year_id == fiscal_year_id)

        total = query.count()
        items = query.order_by(FinancialReport.generated_at.desc()).offset(skip).limit(limit).all()
        return items, total

    # =========================================================================
    # DASHBOARD
    # =========================================================================

    def get_dashboard(self) -> FinanceDashboard:
        """Générer le dashboard financier."""
        today = date.today()
        fiscal_year = self.get_current_fiscal_year()

        # Soldes bancaires
        bank_accounts = self.list_bank_accounts()
        bank_balance = sum(acc.current_balance for acc in bank_accounts)

        # Solde caisse (compte 530)
        cash_account = self.get_account_by_code("530000")
        cash_balance = Decimal("0")
        if cash_account:
            balance = self.get_account_balance(cash_account.id)
            cash_balance = balance["balance"]

        # Créances clients (compte 411)
        receivables_account = self.get_account_by_code("411000")
        total_receivables = Decimal("0")
        if receivables_account:
            balance = self.get_account_balance(receivables_account.id)
            total_receivables = balance["balance"]

        # Dettes fournisseurs (compte 401)
        payables_account = self.get_account_by_code("401000")
        total_payables = Decimal("0")
        if payables_account:
            balance = self.get_account_balance(payables_account.id)
            total_payables = abs(balance["balance"])

        # Résultats exercice
        current_year_revenues = Decimal("0")
        current_year_expenses = Decimal("0")

        if fiscal_year:
            income = self.get_income_statement(fiscal_year.start_date, today)
            current_year_revenues = income.total_revenues
            current_year_expenses = income.total_expenses

        # Écritures en attente
        pending_entries = self.db.query(JournalEntry).filter(
            JournalEntry.tenant_id == self.tenant_id,
            JournalEntry.status.in_([EntryStatus.DRAFT, EntryStatus.PENDING])
        ).count()

        # Transactions non rapprochées
        unreconciled = self.db.query(BankStatementLine).filter(
            BankStatementLine.tenant_id == self.tenant_id,
            BankStatementLine.status == ReconciliationStatus.PENDING
        ).count()

        # Prévisions
        forecasts_30 = self.db.query(CashForecast).filter(
            CashForecast.tenant_id == self.tenant_id,
            CashForecast.date <= today + timedelta(days=30),
            CashForecast.date >= today
        ).all()

        forecasts_90 = self.db.query(CashForecast).filter(
            CashForecast.tenant_id == self.tenant_id,
            CashForecast.date <= today + timedelta(days=90),
            CashForecast.date >= today
        ).all()

        forecast_30 = forecasts_30[-1].expected_closing if forecasts_30 else bank_balance + cash_balance
        forecast_90 = forecasts_90[-1].expected_closing if forecasts_90 else bank_balance + cash_balance

        return FinanceDashboard(
            cash_balance=cash_balance,
            bank_balance=bank_balance,
            total_receivables=total_receivables,
            total_payables=total_payables,
            current_year_revenues=current_year_revenues,
            current_year_expenses=current_year_expenses,
            current_year_result=current_year_revenues - current_year_expenses,
            period_revenues=Decimal("0"),  # NOTE: Phase 2 - Calcul période courante
            period_expenses=Decimal("0"),
            period_result=Decimal("0"),
            pending_entries=pending_entries,
            unreconciled_transactions=unreconciled,
            forecast_30_days=forecast_30,
            forecast_90_days=forecast_90
        )


# Import manquant
from datetime import timedelta


def get_finance_service(db: Session, tenant_id: str) -> FinanceService:
    """Factory pour le service Finance."""
    return FinanceService(db, tenant_id)
