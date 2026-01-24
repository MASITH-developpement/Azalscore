"""
AZALS MODULE - TREASURY: Service
=================================

Logique métier pour la gestion de la trésorerie.
"""

import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from .models import BankAccount, BankTransaction, TransactionType
from .schemas import (
    BankAccountCreate,
    BankAccountUpdate,
    BankTransactionCreate,
    BankTransactionUpdate,
    ForecastData,
    ReconciliationRequest,
    TreasurySummary,
)


class TreasuryService:
    """Service pour la gestion de la trésorerie."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # BANK ACCOUNTS
    # ========================================================================

    def create_account(self, data: BankAccountCreate, user_id: UUID) -> BankAccount:
        """Créer un compte bancaire."""
        # Vérifier que l'IBAN est unique
        existing = self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankAccount.iban == data.iban
        ).first()

        if existing:
            raise ValueError(f"Un compte avec l'IBAN {data.iban} existe déjà")

        # Si code fourni, vérifier unicité
        if data.code:
            existing_code = self.db.query(BankAccount).filter(
                BankAccount.tenant_id == self.tenant_id,
                BankAccount.code == data.code
            ).first()

            if existing_code:
                raise ValueError(f"Un compte avec le code {data.code} existe déjà")

        # Si c'est le compte par défaut, désactiver l'ancien
        if data.is_default:
            self.db.query(BankAccount).filter(
                BankAccount.tenant_id == self.tenant_id,
                BankAccount.is_default == True
            ).update({"is_default": False})

        account = BankAccount(
            tenant_id=self.tenant_id,
            created_by=user_id,
            available_balance=data.balance,  # Initialement, disponible = balance
            **data.model_dump()
        )

        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)

        # Calculer les compteurs
        account.transactions_count = 0
        account.unreconciled_count = 0

        return account

    def get_account(self, account_id: UUID) -> Optional[BankAccount]:
        """Récupérer un compte bancaire."""
        account = self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankAccount.id == account_id
        ).first()

        if account:
            # Calculer les compteurs
            account.transactions_count = self.db.query(BankTransaction).filter(
                BankTransaction.account_id == account_id
            ).count()

            account.unreconciled_count = self.db.query(BankTransaction).filter(
                BankTransaction.account_id == account_id,
                BankTransaction.reconciled == False
            ).count()

        return account

    def list_accounts(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[BankAccount], int]:
        """Lister les comptes bancaires."""
        query = self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id
        )

        if is_active is not None:
            query = query.filter(BankAccount.is_active == is_active)

        total = query.count()

        items = query.order_by(desc(BankAccount.is_default), BankAccount.name).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        # Calculer les compteurs pour chaque compte
        for account in items:
            account.transactions_count = self.db.query(BankTransaction).filter(
                BankTransaction.account_id == account.id
            ).count()

            account.unreconciled_count = self.db.query(BankTransaction).filter(
                BankTransaction.account_id == account.id,
                BankTransaction.reconciled == False
            ).count()

        return items, total

    def update_account(self, account_id: UUID, data: BankAccountUpdate) -> Optional[BankAccount]:
        """Mettre à jour un compte bancaire."""
        account = self.get_account(account_id)
        if not account:
            return None

        # Si on passe en compte par défaut, désactiver l'ancien
        if data.is_default and not account.is_default:
            self.db.query(BankAccount).filter(
                BankAccount.tenant_id == self.tenant_id,
                BankAccount.is_default == True
            ).update({"is_default": False})

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(account, field, value)

        self.db.commit()
        self.db.refresh(account)
        return account

    def delete_account(self, account_id: UUID) -> bool:
        """Supprimer un compte bancaire (soft delete)."""
        account = self.get_account(account_id)
        if not account:
            return False

        # Vérifier qu'il n'y a pas de transactions
        transactions_count = self.db.query(BankTransaction).filter(
            BankTransaction.account_id == account_id
        ).count()

        if transactions_count > 0:
            raise ValueError(
                f"Impossible de supprimer un compte avec {transactions_count} transaction(s)"
            )

        account.is_active = False
        self.db.commit()
        return True

    # ========================================================================
    # TRANSACTIONS
    # ========================================================================

    def create_transaction(self, data: BankTransactionCreate) -> BankTransaction:
        """Créer une transaction bancaire."""
        # Vérifier que le compte existe
        account = self.get_account(data.account_id)
        if not account:
            raise ValueError("Compte bancaire non trouvé")

        transaction = BankTransaction(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )

        self.db.add(transaction)

        # Mettre à jour le solde du compte
        if transaction.type == TransactionType.CREDIT:
            account.balance += transaction.amount
            account.available_balance = (account.available_balance or account.balance) + transaction.amount
        else:  # DEBIT
            account.balance -= transaction.amount
            account.available_balance = (account.available_balance or account.balance) - transaction.amount

        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def get_transaction(self, transaction_id: UUID) -> Optional[BankTransaction]:
        """Récupérer une transaction bancaire."""
        return self.db.query(BankTransaction).filter(
            BankTransaction.tenant_id == self.tenant_id,
            BankTransaction.id == transaction_id
        ).first()

    def list_transactions(
        self,
        account_id: Optional[UUID] = None,
        transaction_type: Optional[TransactionType] = None,
        reconciled: Optional[bool] = None,
        page: int = 1,
        per_page: int = 25
    ) -> Tuple[List[BankTransaction], int]:
        """Lister les transactions bancaires."""
        query = self.db.query(BankTransaction).filter(
            BankTransaction.tenant_id == self.tenant_id
        )

        if account_id:
            query = query.filter(BankTransaction.account_id == account_id)

        if transaction_type:
            query = query.filter(BankTransaction.type == transaction_type)

        if reconciled is not None:
            query = query.filter(BankTransaction.reconciled == reconciled)

        total = query.count()

        items = query.order_by(desc(BankTransaction.date), desc(BankTransaction.created_at)).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        return items, total

    def update_transaction(self, transaction_id: UUID, data: BankTransactionUpdate) -> Optional[BankTransaction]:
        """Mettre à jour une transaction bancaire."""
        transaction = self.get_transaction(transaction_id)
        if not transaction:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(transaction, field, value)

        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def reconcile_transaction(
        self,
        transaction_id: UUID,
        reconciliation: ReconciliationRequest,
        user_id: UUID
    ) -> BankTransaction:
        """Rapprocher une transaction avec un document."""
        transaction = self.get_transaction(transaction_id)
        if not transaction:
            raise ValueError("Transaction non trouvée")

        if transaction.reconciled:
            raise ValueError("Cette transaction est déjà rapprochée")

        transaction.reconciled = True
        transaction.reconciled_at = datetime.datetime.utcnow()
        transaction.reconciled_by = user_id
        transaction.linked_document_type = reconciliation.document_type
        transaction.linked_document_id = reconciliation.document_id

        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def unreconcile_transaction(self, transaction_id: UUID) -> BankTransaction:
        """Annuler le rapprochement d'une transaction."""
        transaction = self.get_transaction(transaction_id)
        if not transaction:
            raise ValueError("Transaction non trouvée")

        if not transaction.reconciled:
            raise ValueError("Cette transaction n'est pas rapprochée")

        transaction.reconciled = False
        transaction.reconciled_at = None
        transaction.reconciled_by = None
        transaction.linked_document_type = None
        transaction.linked_document_id = None

        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    # ========================================================================
    # DASHBOARD & ANALYTICS
    # ========================================================================

    def get_summary(self) -> TreasurySummary:
        """Obtenir le résumé de trésorerie."""
        # Récupérer tous les comptes actifs
        accounts_query = self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankAccount.is_active == True
        )

        accounts = accounts_query.all()

        # Calculer les compteurs pour chaque compte
        for account in accounts:
            account.transactions_count = self.db.query(BankTransaction).filter(
                BankTransaction.account_id == account.id
            ).count()

            account.unreconciled_count = self.db.query(BankTransaction).filter(
                BankTransaction.account_id == account.id,
                BankTransaction.reconciled == False
            ).count()

        # Calculer les totaux
        result = self.db.query(
            func.sum(BankAccount.balance).label('total_balance'),
            func.sum(BankAccount.pending_in).label('total_pending_in'),
            func.sum(BankAccount.pending_out).label('total_pending_out')
        ).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankAccount.is_active == True
        ).first()

        total_balance = result.total_balance or Decimal("0.00")
        total_pending_in = result.total_pending_in or Decimal("0.00")
        total_pending_out = result.total_pending_out or Decimal("0.00")

        # Calculer les prévisions
        forecast_7d = total_balance + total_pending_in - total_pending_out
        forecast_30d = total_balance + total_pending_in - total_pending_out  # Simplifié pour le moment

        return TreasurySummary(
            total_balance=total_balance,
            total_pending_in=total_pending_in,
            total_pending_out=total_pending_out,
            forecast_7d=forecast_7d,
            forecast_30d=forecast_30d,
            accounts=accounts
        )

    def get_forecast(self, days: int = 30) -> List[ForecastData]:
        """Obtenir les prévisions de trésorerie."""
        summary = self.get_summary()

        # Générer les prévisions jour par jour
        # (Pour une version complète, il faudrait analyser les factures à échéance, etc.)
        forecast = []
        current_date = datetime.date.today()
        current_balance = summary.total_balance

        for i in range(days):
            date = current_date + datetime.timedelta(days=i)

            # Calculer les encaissements et décaissements prévus pour ce jour
            # (Simplifié : répartition uniforme des pending_in/pending_out)
            daily_pending_in = summary.total_pending_in / days if days > 0 else Decimal("0.00")
            daily_pending_out = summary.total_pending_out / days if days > 0 else Decimal("0.00")

            projected_balance = current_balance + (daily_pending_in * (i + 1)) - (daily_pending_out * (i + 1))

            forecast.append(ForecastData(
                date=date,
                projected_balance=projected_balance,
                pending_in=daily_pending_in,
                pending_out=daily_pending_out
            ))

        return forecast
