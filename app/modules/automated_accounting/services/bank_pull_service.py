"""
AZALS MODULE M2A - Service Banque Mode PULL
============================================

Service d'intégration bancaire en mode PULL (à la demande).
JAMAIS de webhooks - la banque est interrogée uniquement quand l'utilisateur en a besoin.

Déclencheurs de synchronisation:
- Ouverture du dashboard dirigeant
- Avant génération d'un rapport
- À la demande explicite de l'utilisateur
"""

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.encryption import decrypt_value, encrypt_value

from ..models import (
    BankConnection,
    BankConnectionStatus,
    BankSyncSession,
    ReconciliationStatusAuto,
    SyncedBankAccount,
    SyncedTransaction,
    SyncStatus,
    SyncType,
)

logger = logging.getLogger(__name__)


# ============================================================================
# BANK PROVIDER INTERFACE
# ============================================================================

class BankProvider(ABC):
    """Interface abstraite pour les providers bancaires (Plaid, Bridge, etc.)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nom du provider."""
        pass

    @abstractmethod
    def create_connection(self, institution_id: str, **kwargs) -> dict[str, Any]:
        """Crée une connexion à une institution bancaire.

        Returns:
            Dict avec connection_id, access_token, etc.
        """
        pass

    @abstractmethod
    def get_accounts(self, access_token: str) -> list[dict[str, Any]]:
        """Récupère les comptes liés à une connexion.

        Returns:
            Liste des comptes avec leurs informations.
        """
        pass

    @abstractmethod
    def get_transactions(
        self,
        access_token: str,
        account_id: str,
        start_date: date,
        end_date: date
    ) -> list[dict[str, Any]]:
        """Récupère les transactions d'un compte.

        Returns:
            Liste des transactions.
        """
        pass

    @abstractmethod
    def get_balances(self, access_token: str, account_id: str) -> dict[str, Any]:
        """Récupère les soldes d'un compte.

        Returns:
            Dict avec current, available, limit.
        """
        pass

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Rafraîchit le token d'accès.

        Returns:
            Dict avec new_access_token, new_refresh_token, expires_at.
        """
        pass


# ============================================================================
# MOCK BANK PROVIDER (Pour tests et développement)
# ============================================================================

class MockBankProvider(BankProvider):
    """Provider bancaire simulé pour les tests."""

    @property
    def provider_name(self) -> str:
        return "mock"

    def create_connection(self, institution_id: str, **kwargs) -> dict[str, Any]:
        return {
            "connection_id": f"mock_conn_{uuid.uuid4().hex[:8]}",
            "access_token": f"mock_access_{uuid.uuid4().hex}",
            "refresh_token": f"mock_refresh_{uuid.uuid4().hex}",
            "expires_at": datetime.utcnow() + timedelta(days=90),
        }

    def get_accounts(self, access_token: str) -> list[dict[str, Any]]:
        return [
            {
                "account_id": "mock_acc_001",
                "name": "Compte Courant Professionnel",
                "type": "checking",
                "number_masked": "****1234",
                "iban_masked": "FR76 **** **** **** **** **** 123",
                "currency": "EUR",
            },
            {
                "account_id": "mock_acc_002",
                "name": "Compte Épargne Entreprise",
                "type": "savings",
                "number_masked": "****5678",
                "iban_masked": "FR76 **** **** **** **** **** 456",
                "currency": "EUR",
            },
        ]

    def get_transactions(
        self,
        access_token: str,
        account_id: str,
        start_date: date,
        end_date: date
    ) -> list[dict[str, Any]]:
        # Génère des transactions fictives
        transactions = []
        current_date = start_date

        sample_merchants = [
            ("AMAZON EU", "Shopping", -89.99),
            ("ORANGE SA", "Telecom", -45.00),
            ("VIREMENT RECU CLIENT", "Income", 1500.00),
            ("LOYER BUREAU", "Rent", -800.00),
            ("CARREFOUR", "Supplies", -67.50),
            ("SNCF", "Transport", -125.00),
            ("EDF", "Utilities", -156.78),
            ("PAIEMENT CB RESTAURANT", "Food", -45.90),
        ]

        i = 0
        while current_date <= end_date:
            merchant = sample_merchants[i % len(sample_merchants)]
            transactions.append({
                "transaction_id": f"mock_txn_{uuid.uuid4().hex[:8]}",
                "date": current_date.isoformat(),
                "value_date": current_date.isoformat(),
                "amount": merchant[2],
                "currency": "EUR",
                "description": merchant[0],
                "merchant_name": merchant[0].split()[0],
                "category": merchant[1],
            })
            current_date += timedelta(days=2)
            i += 1

        return transactions

    def get_balances(self, access_token: str, account_id: str) -> dict[str, Any]:
        return {
            "current": Decimal("15432.67"),
            "available": Decimal("15000.00"),
            "limit": None,
            "currency": "EUR",
            "updated_at": datetime.utcnow().isoformat(),
        }

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        return {
            "access_token": f"mock_access_{uuid.uuid4().hex}",
            "refresh_token": f"mock_refresh_{uuid.uuid4().hex}",
            "expires_at": datetime.utcnow() + timedelta(days=90),
        }


# ============================================================================
# BANK PULL SERVICE
# ============================================================================

class BankPullService:
    """Service de synchronisation bancaire en mode PULL.

    La synchronisation est déclenchée uniquement:
    - À l'ouverture du dashboard
    - Avant génération de rapports
    - À la demande de l'utilisateur

    JAMAIS de webhooks ou push depuis la banque.
    """

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2
        self._providers: dict[str, BankProvider] = {}
        self._init_providers()

    def _init_providers(self):
        """Initialise les providers bancaires disponibles."""
        # Toujours avoir le mock pour les tests
        self._providers["mock"] = MockBankProvider()

        # TODO: Ajouter les vrais providers (Plaid, Bridge, Nordigen)
        # self._providers["plaid"] = PlaidProvider()
        # self._providers["bridge"] = BridgeProvider()

    def get_provider(self, name: str) -> BankProvider:
        """Obtient un provider bancaire."""
        if name not in self._providers:
            raise ValueError(f"Provider {name} not available")
        return self._providers[name]

    # =========================================================================
    # GESTION DES CONNEXIONS
    # =========================================================================

    def create_connection(
        self,
        provider: str,
        institution_id: str,
        institution_name: str,
        created_by: UUID,
        institution_logo_url: str | None = None
    ) -> BankConnection:
        """Crée une nouvelle connexion bancaire.

        Args:
            provider: Nom du provider (plaid, bridge, etc.)
            institution_id: ID de l'institution chez le provider
            institution_name: Nom de la banque
            created_by: ID de l'utilisateur
            institution_logo_url: URL du logo

        Returns:
            BankConnection créée
        """
        bank_provider = self.get_provider(provider)

        # Appel au provider pour créer la connexion
        connection_data = bank_provider.create_connection(institution_id)

        # Chiffrer les tokens bancaires (données sensibles PCI-DSS)
        access_token_enc = encrypt_value(connection_data["access_token"])
        refresh_token_enc = None
        if connection_data.get("refresh_token"):
            refresh_token_enc = encrypt_value(connection_data["refresh_token"])

        connection = BankConnection(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            institution_id=institution_id,
            institution_name=institution_name,
            institution_logo_url=institution_logo_url,
            provider=provider,
            connection_id=connection_data["connection_id"],
            status=BankConnectionStatus.ACTIVE,
            access_token_encrypted=access_token_enc,
            refresh_token_encrypted=refresh_token_enc,
            token_expires_at=connection_data.get("expires_at"),
            consent_expires_at=connection_data.get("consent_expires_at"),
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)

        # Synchronise les comptes disponibles
        self._sync_accounts(connection)

        logger.info("Bank connection created: %s (%s)", connection.id, institution_name)

        return connection

    def get_connections(self) -> list[BankConnection]:
        """Récupère toutes les connexions bancaires du tenant."""
        return self.db.query(BankConnection).filter(
            BankConnection.tenant_id == self.tenant_id
        ).all()

    def get_connection(self, connection_id: UUID) -> BankConnection | None:
        """Récupère une connexion spécifique."""
        return self.db.query(BankConnection).filter(
            BankConnection.id == connection_id,
            BankConnection.tenant_id == self.tenant_id
        ).first()

    def delete_connection(self, connection_id: UUID):
        """Supprime une connexion bancaire."""
        connection = self.get_connection(connection_id)
        if connection:
            self.db.delete(connection)
            self.db.commit()
            logger.info("Bank connection deleted: %s", connection_id)

    def _get_decrypted_access_token(self, connection: BankConnection) -> str:
        """Déchiffre et retourne l'access token d'une connexion."""
        if not connection.access_token_encrypted:
            raise ValueError("Pas de token d'accès pour cette connexion")
        return decrypt_value(connection.access_token_encrypted)

    def _get_decrypted_refresh_token(self, connection: BankConnection) -> str | None:
        """Déchiffre et retourne le refresh token d'une connexion."""
        if not connection.refresh_token_encrypted:
            return None
        return decrypt_value(connection.refresh_token_encrypted)

    def _sync_accounts(self, connection: BankConnection):
        """Synchronise les comptes d'une connexion."""
        provider = self.get_provider(connection.provider)
        # Déchiffrer le token avant utilisation
        decrypted_token = self._get_decrypted_access_token(connection)
        accounts_data = provider.get_accounts(decrypted_token)

        for account_data in accounts_data:
            existing = self.db.query(SyncedBankAccount).filter(
                SyncedBankAccount.tenant_id == self.tenant_id,
                SyncedBankAccount.connection_id == connection.id,
                SyncedBankAccount.external_account_id == account_data["account_id"]
            ).first()

            if existing:
                # Mise à jour
                existing.account_name = account_data["name"]
                existing.account_type = account_data.get("type")
                existing.updated_at = datetime.utcnow()
            else:
                # Création
                synced_account = SyncedBankAccount(
                    id=uuid.uuid4(),
                    tenant_id=self.tenant_id,
                    connection_id=connection.id,
                    external_account_id=account_data["account_id"],
                    account_name=account_data["name"],
                    account_number_masked=account_data.get("number_masked"),
                    iban_masked=account_data.get("iban_masked"),
                    account_type=account_data.get("type"),
                    balance_currency=account_data.get("currency", "EUR"),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(synced_account)

        # Met à jour la liste des comptes liés dans la connexion
        connection.linked_accounts = [
            {"id": a["account_id"], "name": a["name"], "type": a.get("type")}
            for a in accounts_data
        ]

        self.db.commit()

    # =========================================================================
    # SYNCHRONISATION (MODE PULL)
    # =========================================================================

    def sync_all(
        self,
        triggered_by: UUID | None = None,
        sync_type: SyncType = SyncType.MANUAL,
        days_back: int = 30
    ) -> list[BankSyncSession]:
        """Synchronise toutes les connexions actives.

        Args:
            triggered_by: ID de l'utilisateur qui déclenche
            sync_type: Type de synchronisation
            days_back: Nombre de jours à synchroniser

        Returns:
            Liste des sessions de synchronisation
        """
        connections = self.db.query(BankConnection).filter(
            BankConnection.tenant_id == self.tenant_id,
            BankConnection.status == BankConnectionStatus.ACTIVE
        ).all()

        sessions = []
        for connection in connections:
            session = self.sync_connection(
                connection_id=connection.id,
                triggered_by=triggered_by,
                sync_type=sync_type,
                days_back=days_back
            )
            sessions.append(session)

        return sessions

    def sync_connection(
        self,
        connection_id: UUID,
        triggered_by: UUID | None = None,
        sync_type: SyncType = SyncType.MANUAL,
        days_back: int = 30,
        start_date: date | None = None,
        end_date: date | None = None
    ) -> BankSyncSession:
        """Synchronise une connexion bancaire spécifique.

        Args:
            connection_id: ID de la connexion
            triggered_by: ID de l'utilisateur
            sync_type: Type de synchronisation
            days_back: Jours en arrière si pas de dates spécifiées
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)

        Returns:
            BankSyncSession avec les résultats
        """
        connection = self.get_connection(connection_id)
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")

        # Vérifie et rafraîchit le token si nécessaire
        self._ensure_valid_token(connection)

        # Dates de synchronisation
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=days_back)

        # Crée la session de sync
        session = BankSyncSession(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            connection_id=connection_id,
            sync_type=sync_type,
            triggered_by=triggered_by,
            status=SyncStatus.IN_PROGRESS,
            sync_from_date=start_date,
            sync_to_date=end_date,
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        self.db.add(session)
        self.db.commit()

        provider = self.get_provider(connection.provider)

        # Synchronise chaque compte
        accounts = self.db.query(SyncedBankAccount).filter(
            SyncedBankAccount.connection_id == connection_id,
            SyncedBankAccount.is_sync_enabled
        ).all()

        for account in accounts:
            self._sync_account_data(
                provider, connection, account, start_date, end_date, session
            )

        # Finalise la session
        session.status = SyncStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        session.duration_ms = int(
            (session.completed_at - session.started_at).total_seconds() * 1000
        )

        # Met à jour la connexion
        connection.last_sync_at = datetime.utcnow()
        connection.last_sync_status = "SUCCESS"

        self.db.commit()
        self.db.refresh(session)

        return session

    def _sync_account_data(
        self,
        provider: BankProvider,
        connection: BankConnection,
        account: SyncedBankAccount,
        start_date: date,
        end_date: date,
        session: BankSyncSession
    ):
        """Synchronise les données d'un compte."""
        # Déchiffrer le token avant utilisation
        decrypted_token = self._get_decrypted_access_token(connection)

        # Récupère les soldes
        balances = provider.get_balances(
            decrypted_token,
            account.external_account_id
        )

        account.balance_current = Decimal(str(balances.get("current", 0)))
        account.balance_available = Decimal(str(balances.get("available", 0)))
        account.balance_limit = Decimal(str(balances.get("limit", 0))) if balances.get("limit") else None
        account.balance_updated_at = datetime.utcnow()

        session.accounts_synced = (session.accounts_synced or 0) + 1

        # Récupère les transactions
        transactions = provider.get_transactions(
            decrypted_token,
            account.external_account_id,
            start_date,
            end_date
        )

        session.transactions_fetched = (session.transactions_fetched or 0) + len(transactions)

        for txn_data in transactions:
            existing = self.db.query(SyncedTransaction).filter(
                SyncedTransaction.tenant_id == self.tenant_id,
                SyncedTransaction.synced_account_id == account.id,
                SyncedTransaction.external_transaction_id == txn_data["transaction_id"]
            ).first()

            if existing:
                # Mise à jour si nécessaire
                if existing.amount != Decimal(str(txn_data["amount"])):
                    existing.amount = Decimal(str(txn_data["amount"]))
                    existing.updated_at = datetime.utcnow()
                    session.transactions_updated = (session.transactions_updated or 0) + 1
            else:
                # Nouvelle transaction
                transaction = SyncedTransaction(
                    id=uuid.uuid4(),
                    tenant_id=self.tenant_id,
                    synced_account_id=account.id,
                    external_transaction_id=txn_data["transaction_id"],
                    transaction_date=date.fromisoformat(txn_data["date"]),
                    value_date=date.fromisoformat(txn_data["value_date"]) if txn_data.get("value_date") else None,
                    amount=Decimal(str(txn_data["amount"])),
                    currency=txn_data.get("currency", "EUR"),
                    description=txn_data.get("description"),
                    merchant_name=txn_data.get("merchant_name"),
                    merchant_category=txn_data.get("category"),
                    reconciliation_status=ReconciliationStatusAuto.PENDING,
                    raw_data=txn_data,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(transaction)
                session.transactions_new = (session.transactions_new or 0) + 1

        # Met à jour les dates de transaction du compte
        if transactions:
            dates = [date.fromisoformat(t["date"]) for t in transactions]
            account.last_transaction_date = max(dates)
            if not account.oldest_transaction_date:
                account.oldest_transaction_date = min(dates)

    def _ensure_valid_token(self, connection: BankConnection):
        """Vérifie et rafraîchit le token si nécessaire."""
        if connection.token_expires_at and connection.token_expires_at < datetime.utcnow():
            if connection.refresh_token_encrypted:
                provider = self.get_provider(connection.provider)
                # Déchiffrer le refresh token avant utilisation
                decrypted_refresh = self._get_decrypted_refresh_token(connection)
                new_tokens = provider.refresh_token(decrypted_refresh)

                # Chiffrer les nouveaux tokens avant stockage
                connection.access_token_encrypted = encrypt_value(new_tokens["access_token"])
                if new_tokens.get("refresh_token"):
                    connection.refresh_token_encrypted = encrypt_value(new_tokens["refresh_token"])
                connection.token_expires_at = new_tokens.get("expires_at")
                connection.status = BankConnectionStatus.ACTIVE

                self.db.commit()
                logger.info("Token refreshed for connection %s", connection.id)
            else:
                connection.status = BankConnectionStatus.EXPIRED
                self.db.commit()
                raise ValueError("Token expired and no refresh token available")

    # =========================================================================
    # REQUÊTES
    # =========================================================================

    def get_synced_accounts(
        self,
        connection_id: UUID | None = None
    ) -> list[SyncedBankAccount]:
        """Récupère les comptes synchronisés."""
        query = self.db.query(SyncedBankAccount).filter(
            SyncedBankAccount.tenant_id == self.tenant_id
        )

        if connection_id:
            query = query.filter(SyncedBankAccount.connection_id == connection_id)

        return query.all()

    def get_transactions(
        self,
        account_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        reconciliation_status: ReconciliationStatusAuto | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list[SyncedTransaction], int]:
        """Récupère les transactions synchronisées.

        Returns:
            Tuple[List[SyncedTransaction], int]: (transactions, total)
        """
        query = self.db.query(SyncedTransaction).filter(
            SyncedTransaction.tenant_id == self.tenant_id
        )

        if account_id:
            query = query.filter(SyncedTransaction.synced_account_id == account_id)

        if start_date:
            query = query.filter(SyncedTransaction.transaction_date >= start_date)

        if end_date:
            query = query.filter(SyncedTransaction.transaction_date <= end_date)

        if reconciliation_status:
            query = query.filter(SyncedTransaction.reconciliation_status == reconciliation_status)

        total = query.count()

        transactions = query.order_by(
            SyncedTransaction.transaction_date.desc()
        ).offset(offset).limit(limit).all()

        return transactions, total

    def get_total_balance(self) -> dict[str, Any]:
        """Calcule le solde total de tous les comptes.

        Returns:
            Dict avec total, par devise, fraîcheur
        """
        accounts = self.get_synced_accounts()

        total_by_currency = {}
        oldest_update = None

        for account in accounts:
            currency = account.balance_currency or "EUR"
            if currency not in total_by_currency:
                total_by_currency[currency] = Decimal("0")

            if account.balance_current:
                total_by_currency[currency] += account.balance_current

            if account.balance_updated_at:
                if oldest_update is None or account.balance_updated_at < oldest_update:
                    oldest_update = account.balance_updated_at

        # Calcul de la fraîcheur (0-100)
        freshness_score = Decimal("100")
        if oldest_update:
            age_hours = (datetime.utcnow() - oldest_update).total_seconds() / 3600
            if age_hours > 24:
                freshness_score = Decimal("50")
            elif age_hours > 12:
                freshness_score = Decimal("70")
            elif age_hours > 6:
                freshness_score = Decimal("85")
            elif age_hours > 1:
                freshness_score = Decimal("95")

        return {
            "total_by_currency": total_by_currency,
            "total_eur": total_by_currency.get("EUR", Decimal("0")),
            "last_updated": oldest_update,
            "freshness_score": freshness_score,
            "accounts_count": len(accounts),
        }

    def get_sync_history(
        self,
        connection_id: UUID | None = None,
        limit: int = 10
    ) -> list[BankSyncSession]:
        """Récupère l'historique des synchronisations."""
        query = self.db.query(BankSyncSession).filter(
            BankSyncSession.tenant_id == self.tenant_id
        )

        if connection_id:
            query = query.filter(BankSyncSession.connection_id == connection_id)

        return query.order_by(
            BankSyncSession.created_at.desc()
        ).limit(limit).all()

    def get_unreconciled_transactions(self, limit: int = 100) -> list[SyncedTransaction]:
        """Récupère les transactions non rapprochées."""
        return self.db.query(SyncedTransaction).filter(
            SyncedTransaction.tenant_id == self.tenant_id,
            SyncedTransaction.reconciliation_status == ReconciliationStatusAuto.PENDING
        ).order_by(
            SyncedTransaction.transaction_date.desc()
        ).limit(limit).all()
