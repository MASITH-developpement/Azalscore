"""
AZALS MODULE - ACCOUNTING: Service
===================================

Logique métier pour la gestion comptable.
"""
from __future__ import annotations


import datetime
import logging
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, extract, func, or_
from sqlalchemy.orm import Session, selectinload

from app.core.query_optimizer import QueryOptimizer
from app.core.cache import get_cache, cache_key_tenant, CacheTTL, invalidate_cache

logger = logging.getLogger(__name__)

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
    AccountingStatus,
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
        self._optimizer = QueryOptimizer(db)
        self._cache = get_cache()

    # ========================================================================
    # CACHE HELPERS
    # ========================================================================

    def _cache_key(self, suffix: str) -> str:
        """Génère une clé de cache scopée par tenant."""
        return cache_key_tenant(self.tenant_id, "accounting", suffix)

    def invalidate_accounting_cache(self) -> None:
        """Invalide le cache comptable après modifications."""
        invalidate_cache(f"tenant:{self.tenant_id}:accounting:*")

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
            AccountingFiscalYear.is_active == True
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

        items = query.order_by(desc(AccountingFiscalYear.start_date)).offset(
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
        logger.info(
            "Closing fiscal year | tenant=%s user=%s fiscal_year_id=%s",
            self.tenant_id, user_id, fiscal_year_id
        )
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
        logger.info(
            "Fiscal year closed | fiscal_year_id=%s code=%s",
            fiscal_year.id, fiscal_year.code
        )
        return fiscal_year

    # ========================================================================
    # CHART OF ACCOUNTS
    # ========================================================================

    def create_account(self, data: ChartOfAccountsCreate, user_id: UUID) -> ChartOfAccounts:
        """Créer un compte comptable."""
        logger.info(
            "Creating chart of accounts | tenant=%s user=%s account_number=%s account_label=%s",
            self.tenant_id, user_id, data.account_number, data.account_label
        )
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
        logger.info(
            "Chart of accounts created | account_id=%s account_number=%s",
            account.id, account.account_number
        )
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

        logger.info(
            "Creating journal entry | tenant=%s user=%s entry_number=%s debit=%s credit=%s",
            self.tenant_id, user_id, entry_number, total_debit, total_credit
        )

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
        logger.info("Journal entry created | entry_id=%s entry_number=%s", entry.id, entry.entry_number)
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
                    AccountingJournalEntry.piece_number.ilike(f"%{search}%"),
                    AccountingJournalEntry.label.ilike(f"%{search}%")
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
            # SÉCURITÉ: Toujours filtrer par tenant_id
            self.db.query(AccountingJournalEntryLine).filter(
                AccountingJournalEntryLine.tenant_id == self.tenant_id,
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
        logger.info(
            "Posting journal entry | tenant=%s user=%s entry_id=%s",
            self.tenant_id, user_id, entry_id
        )
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
        logger.info(
            "Journal entry posted | entry_id=%s entry_number=%s debit=%s credit=%s",
            entry.id, entry.entry_number, entry.total_debit, entry.total_credit
        )
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
            func.sum(AccountingJournalEntryLine.debit).label('total_debit'),
            func.sum(AccountingJournalEntryLine.credit).label('total_credit')
        ).join(
            AccountingJournalEntryLine,
            and_(
                ChartOfAccounts.account_number == AccountingJournalEntryLine.account_number,
                ChartOfAccounts.tenant_id == AccountingJournalEntryLine.tenant_id
            )
        ).join(
            AccountingJournalEntry,
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

    def get_status(self) -> AccountingStatus:
        """Obtenir le statut de la comptabilité pour monitoring."""
        from datetime import date, timedelta

        # Compter les écritures en attente (DRAFT ou PENDING)
        pending_count = self.db.query(AccountingJournalEntry).filter(
            AccountingJournalEntry.tenant_id == self.tenant_id,
            AccountingJournalEntry.status.in_([EntryStatus.DRAFT, EntryStatus.PENDING])
        ).count()

        # Trouver la dernière clôture
        last_closed_year = self.db.query(AccountingFiscalYear).filter(
            AccountingFiscalYear.tenant_id == self.tenant_id,
            AccountingFiscalYear.status == FiscalYearStatus.CLOSED
        ).order_by(desc(AccountingFiscalYear.closed_at)).first()

        last_closure_date = None
        days_since_closure = None

        if last_closed_year and last_closed_year.closed_at:
            last_closure_date = last_closed_year.closed_at.date()
            days_since_closure = (date.today() - last_closure_date).days

        # Vérifier si les écritures sont à jour (moins de 5 en attente)
        entries_up_to_date = pending_count <= 5

        # Déterminer le statut visuel
        # 🟢 = tout va bien (écritures à jour et clôture récente < 45 jours)
        # 🟠 = attention (écritures en retard ou clôture > 45 jours)
        if entries_up_to_date and (days_since_closure is None or days_since_closure < 45):
            status = "🟢"
        else:
            status = "🟠"

        return AccountingStatus(
            status=status,
            entries_up_to_date=entries_up_to_date,
            last_closure_date=last_closure_date,
            pending_entries_count=pending_count,
            days_since_closure=days_since_closure
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
            func.sum(AccountingJournalEntryLine.debit).label('debit_total'),
            func.sum(AccountingJournalEntryLine.credit).label('credit_total')
        ).outerjoin(
            AccountingJournalEntryLine,
            and_(
                ChartOfAccounts.account_number == AccountingJournalEntryLine.account_number,
                ChartOfAccounts.tenant_id == AccountingJournalEntryLine.tenant_id
            )
        ).outerjoin(
            AccountingJournalEntry,
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
        """
        Obtenir la balance (avec ouverture, mouvements, clôture).

        PERFORMANCE:
        1. Cache Redis avec TTL 60s (CacheTTL.SHORT)
        2. GROUP BY pour éviter N+1 queries
        Avant: 1 + N requêtes (N = nombre de comptes) + 0 cache
        Après: 0 requêtes (cache hit) ou 2 requêtes (cache miss)
        """
        # Générer la clé de cache avec les paramètres
        cache_suffix = f"balance:{fiscal_year_id or 'all'}:{period or 'all'}:{page}:{per_page}"
        cache_key = self._cache_key(cache_suffix)

        # Vérifier le cache
        if self._cache:
            cached = self._cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for balance: {cache_key}")
                return cached['entries'], cached['total']

        # 1. Récupérer les comptes actifs (paginés)
        query = self.db.query(ChartOfAccounts).filter(
            ChartOfAccounts.tenant_id == self.tenant_id,
            ChartOfAccounts.is_active == True
        )

        total = query.count()

        accounts = query.order_by(ChartOfAccounts.account_number).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        if not accounts:
            return [], total

        # 2. PERFORMANCE: Une seule requête GROUP BY pour TOUS les mouvements
        account_numbers = [a.account_number for a in accounts]

        movements_query = self.db.query(
            AccountingJournalEntryLine.account_number,
            func.sum(AccountingJournalEntryLine.debit).label('period_debit'),
            func.sum(AccountingJournalEntryLine.credit).label('period_credit')
        ).join(
            AccountingJournalEntry,
            AccountingJournalEntryLine.entry_id == AccountingJournalEntry.id
        ).filter(
            AccountingJournalEntryLine.tenant_id == self.tenant_id,
            AccountingJournalEntryLine.account_number.in_(account_numbers),
            AccountingJournalEntry.status.in_([EntryStatus.POSTED, EntryStatus.VALIDATED])
        )

        if fiscal_year_id:
            movements_query = movements_query.filter(
                AccountingJournalEntry.fiscal_year_id == fiscal_year_id
            )

        if period:
            movements_query = movements_query.filter(
                AccountingJournalEntry.period == period
            )

        # GROUP BY account_number pour agréger en une seule requête
        movements_query = movements_query.group_by(
            AccountingJournalEntryLine.account_number
        )

        # 3. Construire un dictionnaire account_number -> (debit, credit)
        movements_map: dict[str, tuple[Decimal, Decimal]] = {}
        for row in movements_query.all():
            movements_map[row.account_number] = (
                row.period_debit or Decimal("0.00"),
                row.period_credit or Decimal("0.00")
            )

        # 4. Construire les entrées de balance (lookup O(1) au lieu de query)
        balance_entries = []
        for account in accounts:
            opening_debit = account.opening_balance_debit or Decimal("0.00")
            opening_credit = account.opening_balance_credit or Decimal("0.00")

            # Lookup dans le dictionnaire au lieu de query
            period_debit, period_credit = movements_map.get(
                account.account_number,
                (Decimal("0.00"), Decimal("0.00"))
            )

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

        # 5. Mettre en cache avec TTL court (60s)
        if self._cache:
            self._cache.set(
                cache_key,
                {'entries': balance_entries, 'total': total},
                ttl=CacheTTL.SHORT
            )
            logger.debug(f"Cache SET for balance: {cache_key}")

        return balance_entries, total

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _generate_entry_number(self, journal_code: str, entry_date: datetime.datetime) -> str:
        """Générer un numéro d'écriture unique (ex: PC-2024-00001)."""
        from app.core.sequences import SequenceGenerator
        seq = SequenceGenerator(self.db, self.tenant_id)
        return seq.next_reference("PIECE_COMPTABLE")
