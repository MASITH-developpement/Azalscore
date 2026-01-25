"""
AZALS MODULE - ACCOUNTING: Service
===================================

Logique métier pour la gestion comptable.
"""

import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, extract, func, or_
from sqlalchemy.orm import Session, selectinload

from .models import (
    AccountingFiscalYear,
    AccountType,
    ChartOfAccounts,
    EntryStatus,

    FiscalYearStatus,
    AccountingJournalEntry,
    AccountingJournalEntryLine,
)
from .schemas import (
    AccountingSummary,
    BalanceEntry,
    ChartOfAccountsCreate,
    ChartOfAccountsUpdate,
    FiscalYearCreate,
    FiscalYearUpdate,
    JournalEntryCreate,
    JournalEntryUpdate,
    LedgerAccount,
)


class AccountingService:
    """Service pour la gestion comptable."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2

    # ========================================================================
    # FISCAL YEARS
    # ========================================================================

    def create_fiscal_year(self, data: FiscalYearCreate, user_id: UUID) -> AccountingFiscalYear:
        """Créer un exercice comptable."""
        # Vérifier que le code est unique
        existing = self.db.query(AccountingFiscalYear).filter(
            AccountingFiscalYear.tenant_id == self.tenant_id,
            AccountingFiscalYear.code == data.code
        ).first()

        if existing:
            raise ValueError(f"Un exercice avec le code {data.code} existe déjà")

        # Vérifier que end_date > start_date
        if data.end_date <= data.start_date:
            raise ValueError("La date de fin doit être postérieure à la date de début")

        fiscal_year = AccountingFiscalYear(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data.model_dump()
        )

        self.db.add(fiscal_year)
        self.db.commit()
        self.db.refresh(fiscal_year)
        return fiscal_year

    def get_fiscal_year(self, fiscal_year_id: UUID) -> Optional[AccountingFiscalYear]:
        """Récupérer un exercice comptable."""
        return self.db.query(AccountingFiscalYear).filter(
            AccountingFiscalYear.tenant_id == self.tenant_id,
            AccountingFiscalYear.id == fiscal_year_id
        ).first()

    def get_active_fiscal_year(self) -> Optional[AccountingFiscalYear]:
        """Récupérer l'exercice comptable actif."""
        return self.db.query(AccountingFiscalYear).filter(
            AccountingFiscalYear.tenant_id == self.tenant_id,
            AccountingFiscalYear.status == FiscalYearStatus.OPEN,
            FiscalYear.is_active == True
        ).first()

    def list_fiscal_years(
        self,
        status_filter: Optional[FiscalYearStatus] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[AccountingFiscalYear], int]:
        """Lister les exercices comptables."""
        query = self.db.query(AccountingFiscalYear).filter(
            AccountingFiscalYear.tenant_id == self.tenant_id
        )

        if status_filter:
            query = query.filter(AccountingFiscalYear.status == status_filter)

        total = query.count()

        items = query.order_by(desc(FiscalYear.start_date)).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        return items, total

    def update_fiscal_year(self, fiscal_year_id: UUID, data: FiscalYearUpdate) -> Optional[AccountingFiscalYear]:
        """Mettre à jour un exercice comptable."""
        fiscal_year = self.get_fiscal_year(fiscal_year_id)
        if not fiscal_year:
            return None

        # Ne pas permettre modification si clôturé
        if fiscal_year.status != FiscalYearStatus.OPEN:
            raise ValueError("Impossible de modifier un exercice clôturé ou archivé")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(fiscal_year, field, value)

        self.db.commit()
        self.db.refresh(fiscal_year)
        return fiscal_year

    def close_fiscal_year(self, fiscal_year_id: UUID, user_id: UUID) -> AccountingFiscalYear:
        """Clôturer un exercice comptable."""
        fiscal_year = self.get_fiscal_year(fiscal_year_id)
        if not fiscal_year:
            raise ValueError("Exercice comptable non trouvé")

        if fiscal_year.status != FiscalYearStatus.OPEN:
            raise ValueError("Seuls les exercices ouverts peuvent être clôturés")

        # Vérifier que toutes les écritures sont validées
        draft_entries = self.db.query(AccountingJournalEntry).filter(
            AccountingJournalEntry.tenant_id == self.tenant_id,
            AccountingJournalEntry.fiscal_year_id == fiscal_year_id,
            AccountingJournalEntry.status == EntryStatus.DRAFT
        ).count()

        if draft_entries > 0:
            raise ValueError(
                f"{draft_entries} écriture(s) en brouillon doivent être validées avant clôture"
            )

        fiscal_year.status = FiscalYearStatus.CLOSED
        fiscal_year.closed_at = datetime.datetime.utcnow()
        fiscal_year.closed_by = user_id

        self.db.commit()
        self.db.refresh(fiscal_year)
        return fiscal_year

    # ========================================================================
    # CHART OF ACCOUNTS
    # ========================================================================

    def create_account(self, data: ChartOfAccountsCreate, user_id: UUID) -> ChartOfAccounts:
        """Créer un compte comptable."""
        # Vérifier que le numéro de compte est unique
        existing = self.db.query(ChartOfAccounts).filter(
            ChartOfAccounts.tenant_id == self.tenant_id,
            ChartOfAccounts.account_number == data.account_number
        ).first()

        if existing:
            raise ValueError(f"Un compte avec le numéro {data.account_number} existe déjà")

        # Extraire la classe du numéro de compte (premier chiffre)
        account_class = data.account_number[0]

        account = ChartOfAccounts(
            tenant_id=self.tenant_id,
            created_by=user_id,
            account_class=account_class,
            **data.model_dump()
        )

        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def get_account(self, account_number: str) -> Optional[ChartOfAccounts]:
        """Récupérer un compte comptable."""
        return self.db.query(ChartOfAccounts).filter(
            ChartOfAccounts.tenant_id == self.tenant_id,
            ChartOfAccounts.account_number == account_number
        ).first()

    def list_accounts(
        self,
        account_type: Optional[AccountType] = None,
        account_class: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 100
    ) -> Tuple[List[ChartOfAccounts], int]:
        """Lister les comptes comptables."""
        query = self.db.query(ChartOfAccounts).filter(
            ChartOfAccounts.tenant_id == self.tenant_id,
            ChartOfAccounts.is_active == True
        )

        if account_type:
            query = query.filter(ChartOfAccounts.account_type == account_type)

        if account_class:
            query = query.filter(ChartOfAccounts.account_class == account_class)

        if search:
            query = query.filter(
                or_(
                    ChartOfAccounts.account_number.ilike(f"%{search}%"),
                    ChartOfAccounts.account_label.ilike(f"%{search}%")
                )
            )

        total = query.count()

        items = query.order_by(ChartOfAccounts.account_number).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        return items, total

    def update_account(self, account_number: str, data: ChartOfAccountsUpdate) -> Optional[ChartOfAccounts]:
        """Mettre à jour un compte comptable."""
        account = self.get_account(account_number)
        if not account:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(account, field, value)

        self.db.commit()
        self.db.refresh(account)
        return account

    # ========================================================================
    # JOURNAL ENTRIES
    # ========================================================================

    def create_journal_entry(self, data: JournalEntryCreate, user_id: UUID) -> AccountingJournalEntry:
        """Créer une écriture comptable."""
        # Vérifier que l'exercice existe et est ouvert
        fiscal_year = self.get_fiscal_year(data.fiscal_year_id)
        if not fiscal_year:
            raise ValueError("Exercice comptable non trouvé")

        if fiscal_year.status != FiscalYearStatus.OPEN:
            raise ValueError("Impossible de créer une écriture dans un exercice clôturé")

        # Vérifier que la date est dans l'exercice
        if not (fiscal_year.start_date <= data.entry_date <= fiscal_year.end_date):
            raise ValueError(
                f"La date de l'écriture doit être dans l'exercice "
                f"({fiscal_year.start_date.date()} - {fiscal_year.end_date.date()})"
            )

        # Générer le numéro d'écriture
        entry_number = self._generate_entry_number(data.journal_code, data.entry_date)

        # Calculer la période
        period = data.entry_date.strftime("%Y-%m")

        # Calculer les totaux
        total_debit = sum(line.debit for line in data.lines)
        total_credit = sum(line.credit for line in data.lines)
        is_balanced = (total_debit == total_credit)

        # Créer l'écriture
        entry = AccountingJournalEntry(
            tenant_id=self.tenant_id,
            created_by=user_id,
            entry_number=entry_number,
            fiscal_year_id=data.fiscal_year_id,
            period=period,
            total_debit=total_debit,
            total_credit=total_credit,
            is_balanced=is_balanced,
            piece_number=data.piece_number,
            journal_code=data.journal_code,
            journal_label=data.journal_label,
            entry_date=data.entry_date,
            label=data.label,
            document_type=data.document_type,
            document_id=data.document_id,
            currency=data.currency,
            notes=data.notes
        )

        self.db.add(entry)
        self.db.flush()  # Pour obtenir l'ID

        # Créer les lignes
        for idx, line_data in enumerate(data.lines, start=1):
            line = AccountingJournalEntryLine(
                tenant_id=self.tenant_id,
                entry_id=entry.id,
                line_number=idx,
                **line_data.model_dump()
            )
            self.db.add(line)

        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_journal_entry(self, entry_id: UUID) -> Optional[AccountingJournalEntry]:
        """Récupérer une écriture comptable avec ses lignes."""
        return self.db.query(AccountingJournalEntry).options(
            selectinload(AccountingJournalEntry.lines)
        ).filter(
            AccountingJournalEntry.tenant_id == self.tenant_id,
            AccountingJournalEntry.id == entry_id
        ).first()

    def list_journal_entries(
        self,
        fiscal_year_id: Optional[UUID] = None,
        journal_code: Optional[str] = None,
        status_filter: Optional[EntryStatus] = None,
        period: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Tuple[List[AccountingJournalEntry], int]:
        """Lister les écritures comptables."""
        query = self.db.query(AccountingJournalEntry).options(
            selectinload(AccountingJournalEntry.lines)
        ).filter(
            AccountingJournalEntry.tenant_id == self.tenant_id
        )

        if fiscal_year_id:
            query = query.filter(AccountingJournalEntry.fiscal_year_id == fiscal_year_id)

        if journal_code:
            query = query.filter(AccountingJournalEntry.journal_code == journal_code)

        if status_filter:
            query = query.filter(AccountingJournalEntry.status == status_filter)

        if period:
            query = query.filter(AccountingJournalEntry.period == period)

        if search:
            query = query.filter(
                or_(
                    AccountingJournalEntry.entry_number.ilike(f"%{search}%"),
                    JournalEntry.piece_number.ilike(f"%{search}%"),
                    JournalEntry.label.ilike(f"%{search}%")
                )
            )

        total = query.count()

        items = query.order_by(desc(AccountingJournalEntry.entry_date), desc(AccountingJournalEntry.entry_number)).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        return items, total

    def update_journal_entry(self, entry_id: UUID, data: JournalEntryUpdate) -> Optional[AccountingJournalEntry]:
        """Mettre à jour une écriture comptable."""
        entry = self.get_journal_entry(entry_id)
        if not entry:
            return None

        # Ne permettre la modification que si DRAFT
        if entry.status != EntryStatus.DRAFT:
            raise ValueError("Seules les écritures en brouillon peuvent être modifiées")

        # Si les lignes sont mises à jour, recalculer les totaux
        if data.lines is not None:
            # Supprimer les anciennes lignes
            self.db.query(AccountingJournalEntryLine).filter(
                AccountingJournalEntryLine.entry_id == entry_id
            ).delete()

            # Créer les nouvelles lignes
            for idx, line_data in enumerate(data.lines, start=1):
                line = AccountingJournalEntryLine(
                    tenant_id=self.tenant_id,
                    entry_id=entry.id,
                    line_number=idx,
                    **line_data.model_dump()
                )
                self.db.add(line)

            # Recalculer les totaux
            total_debit = sum(line.debit for line in data.lines)
            total_credit = sum(line.credit for line in data.lines)
            entry.total_debit = total_debit
            entry.total_credit = total_credit
            entry.is_balanced = (total_debit == total_credit)

        # Mettre à jour les autres champs
        for field, value in data.model_dump(exclude_unset=True, exclude={'lines'}).items():
            setattr(entry, field, value)

        self.db.commit()
        self.db.refresh(entry)
        return entry

    def post_journal_entry(self, entry_id: UUID, user_id: UUID) -> AccountingJournalEntry:
        """Comptabiliser une écriture (DRAFT → POSTED)."""
        entry = self.get_journal_entry(entry_id)
        if not entry:
            raise ValueError("Écriture non trouvée")

        if entry.status != EntryStatus.DRAFT:
            raise ValueError("Seules les écritures en brouillon peuvent être comptabilisées")

        if not entry.is_balanced:
            raise ValueError(
                f"L'écriture n'est pas équilibrée: débit={entry.total_debit}, crédit={entry.total_credit}"
            )

        entry.status = EntryStatus.POSTED
        entry.posting_date = datetime.datetime.utcnow()
        entry.posted_by = user_id
        entry.posted_at = datetime.datetime.utcnow()

        self.db.commit()
        self.db.refresh(entry)
        return entry

    def validate_journal_entry(self, entry_id: UUID, user_id: UUID) -> AccountingJournalEntry:
        """Valider définitivement une écriture (POSTED → VALIDATED)."""
        entry = self.get_journal_entry(entry_id)
        if not entry:
            raise ValueError("Écriture non trouvée")

        if entry.status != EntryStatus.POSTED:
            raise ValueError("Seules les écritures comptabilisées peuvent être validées")

        entry.status = EntryStatus.VALIDATED
        entry.validated_at = datetime.datetime.utcnow()
        entry.validated_by = user_id

        self.db.commit()
        self.db.refresh(entry)
        return entry

    def cancel_journal_entry(self, entry_id: UUID) -> AccountingJournalEntry:
        """Annuler une écriture."""
        entry = self.get_journal_entry(entry_id)
        if not entry:
            raise ValueError("Écriture non trouvée")

        if entry.status == EntryStatus.VALIDATED:
            raise ValueError("Les écritures validées ne peuvent pas être annulées")

        entry.status = EntryStatus.CANCELLED

        self.db.commit()
        self.db.refresh(entry)
        return entry

    # ========================================================================
    # REPORTS & ANALYTICS
    # ========================================================================

    def get_summary(self, fiscal_year_id: Optional[UUID] = None) -> AccountingSummary:
        """Obtenir le résumé comptable."""
        # Si pas d'exercice spécifié, utiliser l'exercice actif
        if not fiscal_year_id:
            fiscal_year = self.get_active_fiscal_year()
            if fiscal_year:
                fiscal_year_id = fiscal_year.id

        # Calculer les totaux par type de compte
        query = self.db.query(
            ChartOfAccounts.account_type,
            func.sum(JournalEntryLine.debit).label('total_debit'),
            func.sum(JournalEntryLine.credit).label('total_credit')
        ).join(
            JournalEntryLine,
            and_(
                ChartOfAccounts.account_number == AccountingJournalEntryLine.account_number,
                ChartOfAccounts.tenant_id == AccountingJournalEntryLine.tenant_id
            )
        ).join(
            JournalEntry,
            AccountingJournalEntryLine.entry_id == AccountingJournalEntry.id
        ).filter(
            ChartOfAccounts.tenant_id == self.tenant_id,
            AccountingJournalEntry.status.in_([EntryStatus.POSTED, EntryStatus.VALIDATED])
        )

        if fiscal_year_id:
            query = query.filter(AccountingJournalEntry.fiscal_year_id == fiscal_year_id)

        results = query.group_by(ChartOfAccounts.account_type).all()

        # Initialiser les totaux
        totals = {
            AccountType.ASSET: Decimal("0.00"),
            AccountType.LIABILITY: Decimal("0.00"),
            AccountType.EQUITY: Decimal("0.00"),
            AccountType.REVENUE: Decimal("0.00"),
            AccountType.EXPENSE: Decimal("0.00"),
        }

        # Calculer les soldes par type
        for account_type, total_debit, total_credit in results:
            if account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                # Comptes à solde débiteur
                totals[account_type] = (total_debit or Decimal("0.00")) - (total_credit or Decimal("0.00"))
            elif account_type in [AccountType.LIABILITY, AccountType.EQUITY, AccountType.REVENUE]:
                # Comptes à solde créditeur
                totals[account_type] = (total_credit or Decimal("0.00")) - (total_debit or Decimal("0.00"))

        # Calculer le résultat net
        net_income = totals[AccountType.REVENUE] - totals[AccountType.EXPENSE]

        return AccountingSummary(
            total_assets=totals[AccountType.ASSET],
            total_liabilities=totals[AccountType.LIABILITY],
            total_equity=totals[AccountType.EQUITY],
            revenue=totals[AccountType.REVENUE],
            expenses=totals[AccountType.EXPENSE],
            net_income=net_income,
            currency="EUR"
        )

    def get_ledger(
        self,
        account_number: Optional[str] = None,
        fiscal_year_id: Optional[UUID] = None,
        page: int = 1,
        per_page: int = 100
    ) -> Tuple[List[LedgerAccount], int]:
        """Obtenir le grand livre (par compte ou tous les comptes)."""
        query = self.db.query(
            ChartOfAccounts.account_number,
            ChartOfAccounts.account_label,
            func.sum(JournalEntryLine.debit).label('debit_total'),
            func.sum(JournalEntryLine.credit).label('credit_total')
        ).outerjoin(
            JournalEntryLine,
            and_(
                ChartOfAccounts.account_number == AccountingJournalEntryLine.account_number,
                ChartOfAccounts.tenant_id == AccountingJournalEntryLine.tenant_id
            )
        ).outerjoin(
            JournalEntry,
            AccountingJournalEntryLine.entry_id == AccountingJournalEntry.id
        ).filter(
            ChartOfAccounts.tenant_id == self.tenant_id,
            ChartOfAccounts.is_active == True
        )

        if account_number:
            query = query.filter(ChartOfAccounts.account_number == account_number)

        if fiscal_year_id:
            query = query.filter(AccountingJournalEntry.fiscal_year_id == fiscal_year_id)

        # Filtrer seulement les écritures validées
        query = query.filter(
            or_(
                AccountingJournalEntry.id.is_(None),  # Comptes sans mouvements
                AccountingJournalEntry.status.in_([EntryStatus.POSTED, EntryStatus.VALIDATED])
            )
        )

        query = query.group_by(
            ChartOfAccounts.account_number,
            ChartOfAccounts.account_label
        )

        total = query.count()

        results = query.order_by(ChartOfAccounts.account_number).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        # Convertir en LedgerAccount
        ledger_accounts = []
        for account_number, account_label, debit_total, credit_total in results:
            debit_total = debit_total or Decimal("0.00")
            credit_total = credit_total or Decimal("0.00")
            balance = debit_total - credit_total

            ledger_accounts.append(LedgerAccount(
                account_number=account_number,
                account_label=account_label,
                debit_total=debit_total,
                credit_total=credit_total,
                balance=balance,
                currency="EUR"
            ))

        return ledger_accounts, total

    def get_balance(
        self,
        fiscal_year_id: Optional[UUID] = None,
        period: Optional[str] = None,
        page: int = 1,
        per_page: int = 100
    ) -> Tuple[List[BalanceEntry], int]:
        """Obtenir la balance (avec ouverture, mouvements, clôture)."""
        # Pour chaque compte, calculer :
        # - Solde d'ouverture (depuis ChartOfAccounts)
        # - Mouvements de la période
        # - Solde de clôture

        query = self.db.query(ChartOfAccounts).filter(
            ChartOfAccounts.tenant_id == self.tenant_id,
            ChartOfAccounts.is_active == True
        )

        total = query.count()

        accounts = query.order_by(ChartOfAccounts.account_number).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        balance_entries = []

        for account in accounts:
            # Solde d'ouverture
            opening_debit = account.opening_balance_debit
            opening_credit = account.opening_balance_credit

            # Mouvements de la période
            movements_query = self.db.query(
                func.sum(JournalEntryLine.debit).label('period_debit'),
                func.sum(JournalEntryLine.credit).label('period_credit')
            ).join(
                JournalEntry,
                AccountingJournalEntryLine.entry_id == AccountingJournalEntry.id
            ).filter(
                AccountingJournalEntryLine.tenant_id == self.tenant_id,
                AccountingJournalEntryLine.account_number == account.account_number,
                AccountingJournalEntry.status.in_([EntryStatus.POSTED, EntryStatus.VALIDATED])
            )

            if fiscal_year_id:
                movements_query = movements_query.filter(AccountingJournalEntry.fiscal_year_id == fiscal_year_id)

            if period:
                movements_query = movements_query.filter(AccountingJournalEntry.period == period)

            result = movements_query.first()
            period_debit = result.period_debit or Decimal("0.00")
            period_credit = result.period_credit or Decimal("0.00")

            # Solde de clôture
            closing_debit = opening_debit + period_debit
            closing_credit = opening_credit + period_credit

            balance_entries.append(BalanceEntry(
                account_number=account.account_number,
                account_label=account.account_label,
                opening_debit=opening_debit,
                opening_credit=opening_credit,
                period_debit=period_debit,
                period_credit=period_credit,
                closing_debit=closing_debit,
                closing_credit=closing_credit
            ))

        return balance_entries, total

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _generate_entry_number(self, journal_code: str, entry_date: datetime.datetime) -> str:
        """Générer un numéro d'écriture unique (ex: VT-2024-001)."""
        year = entry_date.year

        # Compter les écritures existantes pour ce journal et cette année
        count = self.db.query(AccountingJournalEntry).filter(
            AccountingJournalEntry.tenant_id == self.tenant_id,
            AccountingJournalEntry.journal_code == journal_code,
            extract('year', AccountingJournalEntry.entry_date) == year
        ).count()

        next_number = count + 1
        return f"{journal_code}-{year}-{next_number:03d}"
