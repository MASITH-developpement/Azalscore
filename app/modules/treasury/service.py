"""
AZALS MODULE - TREASURY: Service
=================================

Service métier pour la gestion de trésorerie.

ARCHITECTURE:
- Utilise les modèles BankAccount et BankTransaction depuis finance/models.py
- Isolation multi-tenant stricte via tenant_id
- Audit trail complet via user_id

CONFORMITÉ:
- AZA-NF-003: Module subordonné au noyau
- AZA-SEC-001: Isolation tenant obligatoire
- AZA-BE-003: Contrat backend obligatoire

Auteur: AZALSCORE Team
Version: 2.0.0
Dernière mise à jour: 2026-02-16
"""
from __future__ import annotations


from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session, selectinload

from app.core.query_optimizer import QueryOptimizer
from app.core.cache import get_cache, cache_key_tenant, CacheTTL, invalidate_cache
from app.modules.finance.models import BankAccount, BankTransaction, BankTransactionType

from .models import AccountType, TransactionType
from .schemas import (
    AccountSummary,
    BankAccountCreate,
    BankAccountResponse,
    BankAccountUpdate,
    BankTransactionCreate,
    BankTransactionResponse,
    BankTransactionUpdate,
    ForecastData,
    PaginatedBankAccounts,
    PaginatedBankTransactions,
    ReconciliationRequest,
    TreasurySummary,
)
from .exceptions import TreasuryCacheError
from pydantic import ValidationError
from json import JSONDecodeError


class TreasuryService:
    """
    Service de gestion de trésorerie.

    Ce service fournit les opérations CRUD pour les comptes bancaires
    et transactions, ainsi que les fonctionnalités de prévision.

    SÉCURITÉ:
    - Toutes les requêtes sont filtrées par tenant_id
    - Aucune donnée cross-tenant n'est accessible

    Attributes:
        db: Session SQLAlchemy
        tenant_id: ID du tenant pour l'isolation
        user_id: ID de l'utilisateur pour l'audit
    """

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        """
        Initialise le service Treasury.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant (isolation multi-tenant)
            user_id: ID de l'utilisateur (pour audit trail)
        """
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self._optimizer = QueryOptimizer(db)
        self._cache = get_cache()

    # =========================================================================
    # CACHE HELPERS
    # =========================================================================

    def _cache_key(self, suffix: str) -> str:
        """Génère une clé de cache scopée par tenant."""
        return cache_key_tenant(self.tenant_id, "treasury", suffix)

    def invalidate_summary_cache(self) -> None:
        """
        Invalide le cache du summary.

        Doit être appelé après toute modification de compte ou transaction.
        """
        invalidate_cache(f"tenant:{self.tenant_id}:treasury:*")

    # =========================================================================
    # SUMMARY & FORECAST
    # =========================================================================

    def get_summary(self, use_cache: bool = True) -> TreasurySummary:
        """
        Obtenir le résumé de trésorerie.

        Calcule les totaux à partir des comptes bancaires réels.
        PERFORMANCE: Résultat mis en cache pendant 60 secondes (CacheTTL.SHORT).

        Args:
            use_cache: Si True, utilise le cache Redis (défaut: True)

        Returns:
            TreasurySummary avec les soldes agrégés
        """
        import json

        cache_key = self._cache_key("summary")

        # Check cache first
        if use_cache:
            cached = self._cache.get(cache_key)
            if cached:
                try:
                    return TreasurySummary.model_validate_json(cached)
                except (ValidationError, JSONDecodeError):
                    pass  # Cache invalide, recalculer

        # Récupérer tous les comptes actifs du tenant
        accounts = self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankAccount.is_active == True
        ).all()

        total_balance = Decimal("0.00")
        account_summaries = []

        for account in accounts:
            balance = Decimal(str(account.current_balance or 0))
            total_balance += balance

            account_summaries.append(AccountSummary(
                id=str(account.id),
                name=account.name,
                bank_name=account.bank_name or "",
                balance=balance,
                currency=account.currency or "EUR"
            ))

        # Calculer les transactions en attente (7 derniers jours)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        pending_query = self.db.query(
            func.sum(
                case(
                    (BankTransaction.type == BankTransactionType.CREDIT, BankTransaction.amount),
                    else_=Decimal("0")
                )
            ).label("pending_in"),
            func.sum(
                case(
                    (BankTransaction.type == BankTransactionType.DEBIT, BankTransaction.amount),
                    else_=Decimal("0")
                )
            ).label("pending_out")
        ).join(
            BankAccount, BankTransaction.bank_account_id == BankAccount.id
        ).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankTransaction.date >= seven_days_ago.date()
        ).first()

        pending_in = Decimal(str(pending_query.pending_in or 0)) if pending_query else Decimal("0.00")
        pending_out = Decimal(str(pending_query.pending_out or 0)) if pending_query else Decimal("0.00")

        result = TreasurySummary(
            total_balance=total_balance,
            total_pending_in=pending_in,
            total_pending_out=abs(pending_out),
            forecast_7d=total_balance + pending_in - abs(pending_out),
            forecast_30d=total_balance,  # Simplifié pour l'instant
            accounts=account_summaries
        )

        # Store in cache (60 seconds - données financières volatiles)
        if use_cache:
            try:
                self._cache.set(cache_key, result.model_dump_json(), CacheTTL.SHORT)
            except (ConnectionError, TimeoutError, TreasuryCacheError):
                pass  # Cache write failure is not critical

        return result

    def get_forecast(self, days: int = 30) -> List[ForecastData]:
        """
        Obtenir les prévisions de trésorerie.

        Génère une projection basée sur l'historique des transactions.

        Args:
            days: Nombre de jours de prévision (1-365)

        Returns:
            Liste de ForecastData avec les projections quotidiennes
        """
        # Solde actuel
        summary = self.get_summary()
        current_balance = summary.total_balance

        # Calculer la moyenne quotidienne des 30 derniers jours
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        avg_query = self.db.query(
            func.avg(BankTransaction.amount).label("avg_amount")
        ).join(
            BankAccount, BankTransaction.bank_account_id == BankAccount.id
        ).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankTransaction.date >= thirty_days_ago.date()
        ).first()

        daily_avg = Decimal(str(avg_query.avg_amount or 0)) if avg_query else Decimal("0.00")

        # Générer les prévisions
        forecasts = []
        running_balance = current_balance

        for i in range(days):
            forecast_date = datetime.utcnow().date() + timedelta(days=i + 1)
            running_balance += daily_avg

            forecasts.append(ForecastData(
                date=forecast_date,
                projected_balance=running_balance,
                confidence=max(0.5, 1.0 - (i * 0.02))  # Confiance décroissante
            ))

        return forecasts

    # =========================================================================
    # BANK ACCOUNTS - CRUD
    # =========================================================================

    def create_account(self, data: BankAccountCreate, created_by: UUID = None) -> BankAccountResponse:
        """
        Créer un nouveau compte bancaire.

        Args:
            data: Données du compte à créer
            created_by: ID de l'utilisateur créateur

        Returns:
            BankAccountResponse du compte créé

        Raises:
            ValueError: Si l'IBAN existe déjà pour ce tenant
        """
        # Vérifier unicité IBAN par tenant
        existing = self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankAccount.iban == data.iban
        ).first()

        if existing:
            raise ValueError(f"Un compte avec cet IBAN existe déjà: {data.iban}")

        # Si c'est le premier compte ou demandé par défaut, gérer is_default
        if data.is_default:
            self._clear_default_flag()

        account = BankAccount(
            tenant_id=self.tenant_id,
            name=data.name,
            bank_name=data.bank_name,
            iban=data.iban,
            bic=data.bic,
            account_number=data.account_number,
            initial_balance=data.balance,
            current_balance=data.balance,
            reconciled_balance=Decimal("0.00"),
            currency=data.currency,
            is_active=True,
            is_default=data.is_default,
            created_by=created_by or (UUID(self.user_id) if self.user_id else None),
        )

        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)

        # Invalider le cache après création
        self.invalidate_summary_cache()

        return self._to_account_response(account)

    def list_accounts(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        per_page: int = 20
    ) -> PaginatedBankAccounts:
        """
        Lister les comptes bancaires du tenant.

        PERFORMANCE:
        1. Eager loading des transactions via selectinload
        2. Préchargement des stats en bulk via GROUP BY (évite N+1)

        Args:
            is_active: Filtrer par statut actif
            page: Numéro de page (1-indexed)
            per_page: Nombre d'éléments par page

        Returns:
            PaginatedBankAccounts avec la liste et pagination
        """
        # PERFORMANCE: Eager loading pour éviter N+1 queries
        query = self.db.query(BankAccount).options(
            selectinload(BankAccount.transactions)
        ).filter(
            BankAccount.tenant_id == self.tenant_id
        )

        if is_active is not None:
            query = query.filter(BankAccount.is_active == is_active)

        # Compter total (sans eager loading)
        total = self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id
        ).count() if is_active is None else query.count()

        # Pagination
        offset = (page - 1) * per_page
        accounts = query.order_by(BankAccount.name).offset(offset).limit(per_page).all()

        # PERFORMANCE: Précharger les stats en bulk via GROUP BY
        # Évite 2N queries individuelles pour tx_count et unreconciled
        account_ids = [a.id for a in accounts]
        if account_ids:
            stats_query = self.db.query(
                BankTransaction.bank_account_id,
                func.count(BankTransaction.id).label('tx_count'),
                func.sum(
                    case(
                        (BankTransaction.entry_line_id == None, 1),
                        else_=0
                    )
                ).label('unreconciled')
            ).filter(
                BankTransaction.bank_account_id.in_(account_ids)
            ).group_by(
                BankTransaction.bank_account_id
            ).all()

            preloaded_stats = {
                row.bank_account_id: {
                    'tx_count': row.tx_count,
                    'unreconciled': row.unreconciled or 0
                }
                for row in stats_query
            }
        else:
            preloaded_stats = {}

        return PaginatedBankAccounts(
            items=[self._to_account_response(a, preloaded_stats) for a in accounts],
            total=total,
            page=page,
            per_page=per_page,
            pages=(total + per_page - 1) // per_page
        )

    def get_account(self, account_id: UUID) -> Optional[BankAccountResponse]:
        """
        Récupérer un compte bancaire par ID.

        Args:
            account_id: ID du compte

        Returns:
            BankAccountResponse ou None si non trouvé
        """
        account = self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankAccount.id == account_id
        ).first()

        if not account:
            return None

        return self._to_account_response(account)

    def update_account(self, account_id: UUID, data: BankAccountUpdate) -> Optional[BankAccountResponse]:
        """
        Mettre à jour un compte bancaire.

        Args:
            account_id: ID du compte
            data: Données de mise à jour

        Returns:
            BankAccountResponse mis à jour ou None si non trouvé
        """
        account = self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankAccount.id == account_id
        ).first()

        if not account:
            return None

        # Gérer le flag is_default
        if data.is_default is True:
            self._clear_default_flag()

        # Mettre à jour les champs non-None
        update_fields = data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            if hasattr(account, field):
                setattr(account, field, value)

        account.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(account)

        # Invalider le cache après mise à jour
        self.invalidate_summary_cache()

        return self._to_account_response(account)

    def delete_account(self, account_id: UUID, hard_delete: bool = False) -> bool:
        """
        Supprimer un compte bancaire (soft delete par défaut).

        Args:
            account_id: ID du compte
            hard_delete: Si True, suppression physique

        Returns:
            True si supprimé, False si non trouvé
        """
        account = self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankAccount.id == account_id
        ).first()

        if not account:
            return False

        if hard_delete:
            # Vérifier qu'il n'y a pas de transactions
            tx_count = self.db.query(BankTransaction).filter(
                BankTransaction.bank_account_id == account_id
            ).count()

            if tx_count > 0:
                raise ValueError(
                    f"Impossible de supprimer: {tx_count} transactions liées. "
                    "Utilisez soft delete ou supprimez d'abord les transactions."
                )

            self.db.delete(account)
        else:
            account.is_active = False
            account.updated_at = datetime.utcnow()

        self.db.commit()

        # Invalider le cache après suppression
        self.invalidate_summary_cache()

        return True

    # =========================================================================
    # BANK TRANSACTIONS - CRUD
    # =========================================================================

    def create_transaction(
        self,
        account_id: UUID,
        data: BankTransactionCreate,
        created_by: UUID = None
    ) -> BankTransactionResponse:
        """
        Créer une nouvelle transaction bancaire.

        Args:
            account_id: ID du compte bancaire
            data: Données de la transaction
            created_by: ID de l'utilisateur créateur

        Returns:
            BankTransactionResponse de la transaction créée

        Raises:
            ValueError: Si le compte n'existe pas
        """
        # Vérifier que le compte existe et appartient au tenant
        account = self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankAccount.id == account_id
        ).first()

        if not account:
            raise ValueError(f"Compte bancaire non trouvé: {account_id}")

        # Mapper le type
        tx_type = BankTransactionType.CREDIT if data.type == TransactionType.CREDIT else BankTransactionType.DEBIT

        transaction = BankTransaction(
            tenant_id=self.tenant_id,
            bank_account_id=account_id,
            type=tx_type,
            date=data.date,
            value_date=data.value_date or data.date,
            amount=data.amount if tx_type == BankTransactionType.CREDIT else -abs(data.amount),
            currency=data.currency or account.currency,
            label=data.label,
            reference=data.reference,
            partner_name=data.partner_name,
            category=data.category,
            created_by=created_by or (UUID(self.user_id) if self.user_id else None),
        )

        self.db.add(transaction)

        # Mettre à jour le solde du compte
        if tx_type == BankTransactionType.CREDIT:
            account.current_balance = (account.current_balance or 0) + data.amount
        else:
            account.current_balance = (account.current_balance or 0) - abs(data.amount)

        self.db.commit()
        self.db.refresh(transaction)

        # Invalider le cache après création de transaction
        self.invalidate_summary_cache()

        return self._to_transaction_response(transaction)

    def list_transactions(
        self,
        account_id: Optional[UUID] = None,
        type_filter: Optional[TransactionType] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 50
    ) -> PaginatedBankTransactions:
        """
        Lister les transactions bancaires.

        Args:
            account_id: Filtrer par compte
            type_filter: Filtrer par type (CREDIT/DEBIT)
            date_from: Date de début
            date_to: Date de fin
            page: Numéro de page
            per_page: Éléments par page

        Returns:
            PaginatedBankTransactions
        """
        query = self.db.query(BankTransaction).join(
            BankAccount, BankTransaction.bank_account_id == BankAccount.id
        ).filter(
            BankAccount.tenant_id == self.tenant_id
        )

        if account_id:
            query = query.filter(BankTransaction.bank_account_id == account_id)

        if type_filter:
            tx_type = BankTransactionType.CREDIT if type_filter == TransactionType.CREDIT else BankTransactionType.DEBIT
            query = query.filter(BankTransaction.type == tx_type)

        if date_from:
            query = query.filter(BankTransaction.date >= date_from.date())

        if date_to:
            query = query.filter(BankTransaction.date <= date_to.date())

        total = query.count()
        offset = (page - 1) * per_page

        transactions = query.order_by(
            BankTransaction.date.desc(),
            BankTransaction.created_at.desc()
        ).offset(offset).limit(per_page).all()

        return PaginatedBankTransactions(
            items=[self._to_transaction_response(t) for t in transactions],
            total=total,
            page=page,
            per_page=per_page,
            pages=(total + per_page - 1) // per_page
        )

    def get_transaction(self, transaction_id: UUID) -> Optional[BankTransactionResponse]:
        """Récupérer une transaction par ID."""
        transaction = self.db.query(BankTransaction).join(
            BankAccount, BankTransaction.bank_account_id == BankAccount.id
        ).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankTransaction.id == transaction_id
        ).first()

        if not transaction:
            return None

        return self._to_transaction_response(transaction)

    def update_transaction(
        self,
        transaction_id: UUID,
        data: BankTransactionUpdate
    ) -> Optional[BankTransactionResponse]:
        """Mettre à jour une transaction."""
        transaction = self.db.query(BankTransaction).join(
            BankAccount, BankTransaction.bank_account_id == BankAccount.id
        ).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankTransaction.id == transaction_id
        ).first()

        if not transaction:
            return None

        update_fields = data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            if hasattr(transaction, field) and field not in ("id", "tenant_id", "bank_account_id"):
                setattr(transaction, field, value)

        self.db.commit()
        self.db.refresh(transaction)

        # Invalider le cache après mise à jour de transaction
        self.invalidate_summary_cache()

        return self._to_transaction_response(transaction)

    def delete_transaction(self, transaction_id: UUID) -> bool:
        """Supprimer une transaction."""
        transaction = self.db.query(BankTransaction).join(
            BankAccount, BankTransaction.bank_account_id == BankAccount.id
        ).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankTransaction.id == transaction_id
        ).first()

        if not transaction:
            return False

        # Mettre à jour le solde du compte
        account = self.db.query(BankAccount).filter(
            BankAccount.id == transaction.bank_account_id
        ).first()

        if account:
            # Inverser l'effet de la transaction
            account.current_balance = (account.current_balance or 0) - transaction.amount

        self.db.delete(transaction)
        self.db.commit()

        # Invalider le cache après suppression de transaction
        self.invalidate_summary_cache()

        return True

    def reconcile_transaction(self, transaction_id: UUID, data: ReconciliationRequest) -> bool:
        """Marquer une transaction comme rapprochée."""
        transaction = self.db.query(BankTransaction).join(
            BankAccount, BankTransaction.bank_account_id == BankAccount.id
        ).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankTransaction.id == transaction_id
        ).first()

        if not transaction:
            return False

        # Le modèle BankTransaction n'a pas de champ reconciliation_status
        # On peut utiliser un champ category ou créer un lien avec journal_entry
        # Pour l'instant, on log l'action
        if data.entry_id:
            transaction.entry_line_id = data.entry_id

        self.db.commit()
        return True

    def unreconcile_transaction(self, transaction_id: UUID) -> bool:
        """Annuler le rapprochement d'une transaction."""
        transaction = self.db.query(BankTransaction).join(
            BankAccount, BankTransaction.bank_account_id == BankAccount.id
        ).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankTransaction.id == transaction_id
        ).first()

        if not transaction:
            return False

        transaction.entry_line_id = None
        self.db.commit()
        return True

    def list_transactions_by_account(
        self,
        account_id: UUID,
        page: int = 1,
        per_page: int = 50
    ) -> PaginatedBankTransactions:
        """Lister les transactions d'un compte spécifique."""
        return self.list_transactions(
            account_id=account_id,
            page=page,
            per_page=per_page
        )

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _clear_default_flag(self) -> None:
        """Retire le flag is_default de tous les comptes du tenant."""
        self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankAccount.is_default == True
        ).update({"is_default": False})

    def _to_account_response(
        self,
        account: BankAccount,
        preloaded_stats: dict | None = None
    ) -> BankAccountResponse:
        """
        Convertir un modèle BankAccount en réponse.

        PERFORMANCE: Utilise les données eager-loaded ou preloaded_stats
        pour éviter 2 queries par compte (N+1 problem).

        Args:
            account: Le compte bancaire
            preloaded_stats: Dict optionnel {account_id: {tx_count, unreconciled}}
                             pour éviter les requêtes individuelles

        Returns:
            BankAccountResponse
        """
        # PERFORMANCE: Utiliser les stats préchargées ou les transactions eager-loaded
        if preloaded_stats and account.id in preloaded_stats:
            stats = preloaded_stats[account.id]
            tx_count = stats['tx_count']
            unreconciled = stats['unreconciled']
        elif hasattr(account, 'transactions') and account.transactions is not None:
            # Utiliser les transactions eager-loaded (évite 2 queries)
            tx_count = len(account.transactions)
            unreconciled = sum(
                1 for tx in account.transactions
                if tx.entry_line_id is None
            )
        else:
            # Fallback: queries individuelles (cas non-optimisé)
            tx_count = self.db.query(BankTransaction).filter(
                BankTransaction.bank_account_id == account.id
            ).count()
            unreconciled = self.db.query(BankTransaction).filter(
                BankTransaction.bank_account_id == account.id,
                BankTransaction.entry_line_id == None
            ).count()

        return BankAccountResponse(
            id=account.id,
            tenant_id=account.tenant_id,
            code=account.account_number,
            name=account.name,
            bank_name=account.bank_name or "",
            iban=account.iban or "",
            bic=account.bic,
            account_number=account.account_number,
            account_type=AccountType.CURRENT,  # Mapping simplifié
            is_default=account.is_default or False,
            is_active=account.is_active,
            balance=Decimal(str(account.current_balance or 0)),
            available_balance=Decimal(str(account.current_balance or 0)),
            pending_in=Decimal("0.00"),  # À calculer si nécessaire
            pending_out=Decimal("0.00"),
            currency=account.currency or "EUR",
            transactions_count=tx_count,
            unreconciled_count=unreconciled,
            created_by=account.created_by,
            created_at=account.created_at or datetime.utcnow(),
            updated_at=account.updated_at or datetime.utcnow(),
        )

    def _to_transaction_response(self, tx: BankTransaction) -> BankTransactionResponse:
        """Convertir un modèle BankTransaction en réponse."""
        return BankTransactionResponse(
            id=tx.id,
            tenant_id=tx.tenant_id,
            bank_account_id=tx.bank_account_id,
            type=TransactionType.CREDIT if tx.type == BankTransactionType.CREDIT else TransactionType.DEBIT,
            date=tx.date,
            value_date=tx.value_date,
            amount=abs(Decimal(str(tx.amount))),
            currency=tx.currency or "EUR",
            label=tx.label,
            reference=tx.reference,
            partner_name=tx.partner_name,
            category=tx.category,
            is_reconciled=tx.entry_line_id is not None,
            entry_id=tx.entry_line_id,
            created_by=tx.created_by,
            created_at=tx.created_at or datetime.utcnow(),
        )
