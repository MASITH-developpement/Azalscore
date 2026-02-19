"""
AZALS - Module Synchronisation Bancaire - Service
==================================================
Service de gestion des synchronisations bancaires avec multi-providers.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload

from app.core.encryption import decrypt_value, encrypt_value

from .models import (
    BankAccount,
    BankConnection,
    BankProvider,
    BankSyncLog,
    BankTransaction,
    ConnectionStatus,
    SyncStatus,
    TransactionStatus,
)
from .schemas import (
    BankAccountResponse,
    BankAccountUpdate,
    BankConnectionCreate,
    BankConnectionListResponse,
    BankConnectionResponse,
    BankConnectionUpdate,
    BankingStats,
    BankTransactionListResponse,
    BankTransactionResponse,
    SyncConnectionResponse,
)

logger = logging.getLogger(__name__)


class BankingSyncService:
    """Service pour la gestion des synchronisations bancaires."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    # =========================================================================
    # CONNEXIONS BANCAIRES
    # =========================================================================

    def create_connection(
        self,
        provider: BankProvider,
        authorization_code: str,
        redirect_uri: str = None
    ) -> BankConnection:
        """
        Crée une connexion bancaire après OAuth2 flow.
        
        Args:
            provider: Provider utilisé
            authorization_code: Code d'autorisation OAuth2
            redirect_uri: URI de redirection
            
        Returns:
            Connexion créée
        """
        # Échanger le code contre un token via le provider
        provider_service = self._get_provider(provider)
        provider_data = provider_service.exchange_authorization_code(
            authorization_code,
            redirect_uri
        )
        
        # Créer la connexion
        connection = BankConnection(
            tenant_id=self.tenant_id,
            provider=provider,
            provider_connection_id=provider_data.get("connection_id"),
            provider_user_id=provider_data.get("user_id"),
            bank_name=provider_data.get("bank_name", "Banque"),
            bank_code=provider_data.get("bank_code"),
            bank_logo_url=provider_data.get("bank_logo_url"),
            status=ConnectionStatus.ACTIVE,
            access_token_encrypted=encrypt_value(provider_data.get("access_token")),
            refresh_token_encrypted=encrypt_value(provider_data.get("refresh_token")) if provider_data.get("refresh_token") else None,
            auto_sync=True,
            sync_frequency_hours=24,
            created_by=self.user_id,
            last_sync_at=None,
            next_sync_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)
        
        # Déclencher une première synchronisation
        self.sync_connection(str(connection.id))
        
        return connection

    def get_connection(self, connection_id: str) -> Optional[BankConnection]:
        """Récupère une connexion bancaire."""
        return self.db.query(BankConnection).filter(
            and_(
                BankConnection.id == connection_id,
                BankConnection.tenant_id == self.tenant_id
            )
        ).options(
            joinedload(BankConnection.accounts)
        ).first()

    def list_connections(
        self,
        status: Optional[ConnectionStatus] = None
    ) -> BankConnectionListResponse:
        """Liste les connexions bancaires."""
        query = self.db.query(BankConnection).filter(
            BankConnection.tenant_id == self.tenant_id
        )
        
        if status:
            query = query.filter(BankConnection.status == status)
        
        connections = query.order_by(BankConnection.created_at.desc()).all()
        
        return BankConnectionListResponse(
            connections=[BankConnectionResponse.model_validate(c) for c in connections],
            total=len(connections)
        )

    def update_connection(
        self,
        connection_id: str,
        data: BankConnectionUpdate
    ) -> Optional[BankConnection]:
        """Met à jour une connexion bancaire."""
        connection = self.get_connection(connection_id)
        if not connection:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(connection, field, value)
        
        connection.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(connection)
        
        return connection

    def delete_connection(self, connection_id: str) -> bool:
        """Supprime une connexion bancaire."""
        connection = self.get_connection(connection_id)
        if not connection:
            return False
        
        # Marquer comme supprimée plutôt que supprimer réellement
        connection.status = ConnectionStatus.DELETED
        connection.is_active = False
        self.db.commit()
        
        return True

    # =========================================================================
    # SYNCHRONISATION
    # =========================================================================

    def sync_connection(
        self,
        connection_id: str,
        force: bool = False,
        days_back: int = 90
    ) -> SyncConnectionResponse:
        """
        Synchronise une connexion bancaire.
        
        Args:
            connection_id: ID de la connexion
            force: Forcer la sync même si récente
            days_back: Nombre de jours en arrière
            
        Returns:
            Résultat de la synchronisation
        """
        connection = self.get_connection(connection_id)
        if not connection:
            return SyncConnectionResponse(
                success=False,
                connection_id=uuid.UUID(connection_id),
                message="Connexion non trouvée"
            )
        
        if connection.status != ConnectionStatus.ACTIVE:
            return SyncConnectionResponse(
                success=False,
                connection_id=connection.id,
                message=f"Connexion non active (statut: {connection.status})"
            )
        
        # Créer un log de synchronisation
        sync_log = BankSyncLog(
            connection_id=connection.id,
            tenant_id=self.tenant_id,
            status=SyncStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
            triggered_by="manual" if force else "auto",
            triggered_by_user=self.user_id
        )
        self.db.add(sync_log)
        self.db.commit()
        
        try:
            # Synchroniser avec le provider
            provider = self._get_provider(connection.provider)
            
            # Décrypter les tokens
            access_token = decrypt_value(connection.access_token_encrypted) if connection.access_token_encrypted else None
            
            # Récupérer les comptes et transactions
            sync_result = provider.sync_accounts_and_transactions(
                connection_id=connection.provider_connection_id,
                access_token=access_token,
                days_back=days_back
            )
            
            # Mettre à jour les comptes
            accounts_synced = 0
            for account_data in sync_result.get("accounts", []):
                self._upsert_account(connection, account_data)
                accounts_synced += 1
            
            # Mettre à jour les transactions
            transactions_imported = 0
            for tx_data in sync_result.get("transactions", []):
                if self._import_transaction(connection, tx_data):
                    transactions_imported += 1
            
            # Mettre à jour le log de succès
            sync_log.status = SyncStatus.SUCCESS
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = int((sync_log.completed_at - sync_log.started_at).total_seconds())
            sync_log.accounts_synced = accounts_synced
            sync_log.transactions_imported = transactions_imported
            
            # Mettre à jour la connexion
            connection.last_sync_at = datetime.utcnow()
            connection.last_sync_status = SyncStatus.SUCCESS
            connection.next_sync_at = datetime.utcnow() + timedelta(hours=connection.sync_frequency_hours)
            
            self.db.commit()
            
            return SyncConnectionResponse(
                success=True,
                connection_id=connection.id,
                sync_log_id=sync_log.id,
                message="Synchronisation réussie",
                accounts_synced=accounts_synced,
                transactions_imported=transactions_imported
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation {connection_id}: {str(e)}")
            
            sync_log.status = SyncStatus.FAILED
            sync_log.completed_at = datetime.utcnow()
            sync_log.error_message = str(e)
            
            connection.last_sync_status = SyncStatus.FAILED
            
            self.db.commit()
            
            return SyncConnectionResponse(
                success=False,
                connection_id=connection.id,
                sync_log_id=sync_log.id,
                message=f"Erreur: {str(e)}"
            )

    # =========================================================================
    # COMPTES ET TRANSACTIONS
    # =========================================================================

    def list_accounts(self, connection_id: Optional[str] = None) -> list[BankAccountResponse]:
        """Liste les comptes bancaires."""
        query = self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id
        )
        
        if connection_id:
            query = query.filter(BankAccount.connection_id == connection_id)
        
        accounts = query.all()
        return [BankAccountResponse.model_validate(a) for a in accounts]

    def list_transactions(
        self,
        account_id: Optional[str] = None,
        status: Optional[TransactionStatus] = None,
        page: int = 1,
        page_size: int = 50
    ) -> BankTransactionListResponse:
        """Liste les transactions bancaires."""
        query = self.db.query(BankTransaction).filter(
            BankTransaction.tenant_id == self.tenant_id
        )
        
        if account_id:
            query = query.filter(BankTransaction.account_id == account_id)
        if status:
            query = query.filter(BankTransaction.status == status)
        
        total = query.count()
        transactions = query.order_by(
            BankTransaction.transaction_date.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        return BankTransactionListResponse(
            transactions=[BankTransactionResponse.model_validate(t) for t in transactions],
            total=total,
            page=page,
            page_size=page_size
        )

    def get_stats(self) -> BankingStats:
        """Récupère les statistiques bancaires."""
        total_connections = self.db.query(BankConnection).filter(
            BankConnection.tenant_id == self.tenant_id
        ).count()
        
        active_connections = self.db.query(BankConnection).filter(
            and_(
                BankConnection.tenant_id == self.tenant_id,
                BankConnection.status == ConnectionStatus.ACTIVE
            )
        ).count()
        
        total_accounts = self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id
        ).count()
        
        total_transactions = self.db.query(BankTransaction).filter(
            BankTransaction.tenant_id == self.tenant_id
        ).count()
        
        pending_transactions = self.db.query(BankTransaction).filter(
            and_(
                BankTransaction.tenant_id == self.tenant_id,
                BankTransaction.status == TransactionStatus.PENDING
            )
        ).count()
        
        matched_transactions = self.db.query(BankTransaction).filter(
            and_(
                BankTransaction.tenant_id == self.tenant_id,
                BankTransaction.status == TransactionStatus.MATCHED
            )
        ).count()
        
        last_sync = self.db.query(func.max(BankConnection.last_sync_at)).filter(
            BankConnection.tenant_id == self.tenant_id
        ).scalar()
        
        return BankingStats(
            total_connections=total_connections,
            active_connections=active_connections,
            total_accounts=total_accounts,
            total_transactions=total_transactions,
            pending_transactions=pending_transactions,
            matched_transactions=matched_transactions,
            last_sync_at=last_sync
        )

    # =========================================================================
    # HELPERS PRIVÉS
    # =========================================================================

    def _get_provider(self, provider: BankProvider):
        """Récupère une instance du provider."""
        if provider == BankProvider.BUDGET_INSIGHT:
            from .providers.budget_insight import BudgetInsightProvider
            return BudgetInsightProvider(self.db, self.tenant_id)
        elif provider == BankProvider.BRIDGE:
            from .providers.bridge import BridgeProvider
            return BridgeProvider(self.db, self.tenant_id)
        else:
            raise ValueError(f"Provider non supporté: {provider}")

    def _upsert_account(self, connection: BankConnection, account_data: dict):
        """Crée ou met à jour un compte bancaire."""
        account = self.db.query(BankAccount).filter(
            BankAccount.provider_account_id == account_data["provider_account_id"]
        ).first()
        
        if account:
            # Mettre à jour
            account.account_name = account_data.get("account_name", account.account_name)
            account.balance = account_data.get("balance")
            account.balance_date = datetime.utcnow()
            account.updated_at = datetime.utcnow()
        else:
            # Créer
            account = BankAccount(
                connection_id=connection.id,
                tenant_id=self.tenant_id,
                provider_account_id=account_data["provider_account_id"],
                account_name=account_data["account_name"],
                account_number=account_data.get("account_number"),
                account_type=account_data.get("account_type"),
                currency=account_data.get("currency", "EUR"),
                balance=account_data.get("balance"),
                balance_date=datetime.utcnow()
            )
            self.db.add(account)
        
        self.db.flush()
        return account

    def _import_transaction(self, connection: BankConnection, tx_data: dict) -> bool:
        """Importe une transaction bancaire."""
        # Vérifier si existe déjà
        existing = self.db.query(BankTransaction).filter(
            BankTransaction.provider_transaction_id == tx_data["provider_transaction_id"]
        ).first()
        
        if existing:
            return False  # Déjà importée
        
        # Récupérer le compte
        account = self.db.query(BankAccount).filter(
            BankAccount.provider_account_id == tx_data["account_id"]
        ).first()
        
        if not account:
            logger.warning(f"Account {tx_data['account_id']} not found for transaction")
            return False
        
        # Créer la transaction
        transaction = BankTransaction(
            account_id=account.id,
            tenant_id=self.tenant_id,
            provider_transaction_id=tx_data["provider_transaction_id"],
            transaction_date=tx_data["transaction_date"],
            value_date=tx_data.get("value_date"),
            amount=tx_data["amount"],
            currency=tx_data.get("currency", "EUR"),
            description=tx_data["description"],
            original_description=tx_data.get("original_description"),
            category=tx_data.get("category"),
            counterparty_name=tx_data.get("counterparty_name"),
            counterparty_iban=tx_data.get("counterparty_iban"),
            status=TransactionStatus.PENDING
        )
        
        self.db.add(transaction)
        return True
