"""
AZALSCORE Finance Provider - Swan
=================================

Provider pour l'intégration avec Swan.io (Open Banking / Agrégation Bancaire).

Swan.io fournit:
- Comptes bancaires IBAN français
- Virements SEPA (SCT)
- Prélèvements SEPA (SDD)
- Cartes virtuelles et physiques
- API Open Banking PSD2

Documentation: https://docs.swan.io/

Multi-tenant: OUI - Chaque requête filtrée par tenant_id
Sécurité: OAuth2 + API Key + Webhook signature HMAC-SHA256
"""
from __future__ import annotations


import hashlib
import hmac
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .base import (
    BaseFinanceProvider,
    FinanceProviderType,
    FinanceResult,
    FinanceError,
    FinanceErrorCode,
    WebhookEvent,
    WebhookEventType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS SWAN
# =============================================================================

class SwanAccountStatus(str, Enum):
    """Statuts de compte Swan."""
    OPENING = "Opening"
    OPENED = "Opened"
    SUSPENDED = "Suspended"
    CLOSING = "Closing"
    CLOSED = "Closed"


class SwanAccountType(str, Enum):
    """Types de compte Swan."""
    PAYMENT = "PaymentAccount"
    VIRTUAL_IBAN = "VirtualIbanAccount"


class SwanTransactionStatus(str, Enum):
    """Statuts de transaction Swan."""
    PENDING = "Pending"
    BOOKED = "Booked"
    REJECTED = "Rejected"
    CANCELED = "Canceled"
    RELEASED = "Released"


class SwanTransactionType(str, Enum):
    """Types de transaction Swan."""
    SEPA_CREDIT_TRANSFER_IN = "SepaCreditTransferIn"
    SEPA_CREDIT_TRANSFER_OUT = "SepaCreditTransferOut"
    SEPA_DIRECT_DEBIT_IN = "SepaDirectDebitIn"
    SEPA_DIRECT_DEBIT_OUT = "SepaDirectDebitOut"
    CARD_TRANSACTION = "CardTransaction"
    INTERNAL_TRANSFER = "InternalTransfer"
    FEE = "Fee"
    INTEREST = "Interest"


class SwanPaymentStatus(str, Enum):
    """Statuts de paiement Swan."""
    INITIATED = "Initiated"
    CONSENT_PENDING = "ConsentPending"
    REJECTED = "Rejected"
    RELEASED = "Released"


# =============================================================================
# SCHEMAS PYDANTIC - REQUEST
# =============================================================================

class SwanCreateAccountRequest(BaseModel):
    """Requête de création de compte Swan."""
    name: str = Field(..., min_length=1, max_length=100, description="Nom du compte")
    account_type: SwanAccountType = Field(
        default=SwanAccountType.PAYMENT,
        description="Type de compte"
    )
    language: str = Field(default="fr", pattern=r"^[a-z]{2}$")

    class Config:
        use_enum_values = True


class SwanTransferRequest(BaseModel):
    """Requête de virement SEPA."""
    amount: int = Field(..., gt=0, description="Montant en centimes")
    currency: str = Field(default="EUR", pattern=r"^[A-Z]{3}$")
    creditor_name: str = Field(..., min_length=1, max_length=70)
    creditor_iban: str = Field(..., min_length=14, max_length=34)
    reference: Optional[str] = Field(None, max_length=140)
    label: Optional[str] = Field(None, max_length=140)

    @field_validator("creditor_iban")
    @classmethod
    def validate_iban(cls, v: str) -> str:
        """Valide le format IBAN."""
        v = v.replace(" ", "").upper()
        if not v.isalnum():
            raise ValueError("IBAN invalide: caractères non alphanumériques")
        if len(v) < 14 or len(v) > 34:
            raise ValueError("IBAN invalide: longueur incorrecte")
        return v


class SwanListTransactionsRequest(BaseModel):
    """Requête de liste des transactions."""
    account_id: str = Field(..., description="ID du compte Swan")
    first: int = Field(default=20, ge=1, le=100, description="Nombre de résultats")
    after: Optional[str] = Field(None, description="Curseur de pagination")
    status: Optional[SwanTransactionStatus] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


# =============================================================================
# SCHEMAS PYDANTIC - RESPONSE
# =============================================================================

class SwanAccountResponse(BaseModel):
    """Réponse compte Swan."""
    id: str
    name: str
    status: SwanAccountStatus
    iban: str
    bic: str
    currency: str = "EUR"
    balance_available: int = Field(description="Solde disponible en centimes")
    balance_booked: int = Field(description="Solde comptable en centimes")
    balance_pending: int = Field(default=0, description="Solde en attente")
    holder_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class SwanTransactionResponse(BaseModel):
    """Réponse transaction Swan."""
    id: str
    status: SwanTransactionStatus
    type: SwanTransactionType
    amount: int = Field(description="Montant en centimes (positif ou négatif)")
    currency: str = "EUR"
    reference: Optional[str] = None
    label: Optional[str] = None
    counterparty_name: Optional[str] = None
    counterparty_iban: Optional[str] = None
    execution_date: Optional[datetime] = None
    booking_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        use_enum_values = True


class SwanTransferResponse(BaseModel):
    """Réponse virement Swan."""
    id: str
    status: SwanPaymentStatus
    amount: int
    currency: str = "EUR"
    creditor_name: str
    creditor_iban: str
    reference: Optional[str] = None
    consent_url: Optional[str] = Field(
        None,
        description="URL de consentement SCA si nécessaire"
    )
    created_at: datetime

    class Config:
        use_enum_values = True


class SwanWebhookPayload(BaseModel):
    """Payload webhook Swan."""
    event_id: str
    event_type: str
    resource_id: str
    project_id: str
    timestamp: datetime
    data: dict[str, Any]


# =============================================================================
# PROVIDER SWAN
# =============================================================================

class SwanProvider(BaseFinanceProvider):
    """
    Provider Swan pour agrégation bancaire et open banking.

    Fonctionnalités:
    - Gestion des comptes bancaires
    - Virements SEPA (SCT)
    - Liste des transactions
    - Cartes virtuelles
    - Webhooks temps réel

    Usage:
        async with SwanProvider(tenant_id="tenant-001", api_key="sk_...") as swan:
            # Liste des comptes
            result = await swan.get_accounts()
            if result.success:
                for account in result.data:
                    print(f"{account.name}: {account.balance_available / 100}€")

            # Virement
            transfer = await swan.create_transfer(
                account_id="acc_123",
                request=SwanTransferRequest(
                    amount=10000,  # 100.00€
                    creditor_name="Jean Dupont",
                    creditor_iban="FR7630001007941234567890185",
                )
            )
    """

    PROVIDER_NAME = "swan"
    PROVIDER_TYPE = FinanceProviderType.SWAN
    BASE_URL = "https://api.swan.io"
    SANDBOX_URL = "https://api.sandbox.swan.io"
    API_VERSION = "v1"

    # Configuration spécifique Swan
    DEFAULT_TIMEOUT = 30.0
    MAX_RETRIES = 3

    def __init__(
        self,
        tenant_id: str,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        sandbox: bool = False,
        timeout: Optional[float] = None,
    ):
        """
        Initialise le provider Swan.

        Args:
            tenant_id: ID du tenant (OBLIGATOIRE)
            api_key: Clé API Swan (Bearer token)
            project_id: ID du projet Swan
            webhook_secret: Secret pour validation webhooks
            sandbox: Utiliser l'environnement sandbox
            timeout: Timeout custom
        """
        super().__init__(
            tenant_id=tenant_id,
            api_key=api_key,
            sandbox=sandbox,
            timeout=timeout,
        )
        self.project_id = project_id
        self.webhook_secret = webhook_secret

    def _get_base_url(self) -> str:
        """Retourne l'URL de base (sandbox ou production)."""
        return self.SANDBOX_URL if self.sandbox else self.BASE_URL

    # =========================================================================
    # HEALTH CHECK
    # =========================================================================

    async def health_check(self) -> FinanceResult[dict]:
        """
        Vérifie la connectivité avec Swan.

        Returns:
            FinanceResult avec status de santé
        """
        result = await self._request("GET", "/")

        if result.success:
            return FinanceResult.ok(
                data={
                    "provider": self.PROVIDER_NAME,
                    "status": "healthy",
                    "sandbox": self.sandbox,
                    "api_version": self.API_VERSION,
                },
                provider=self.PROVIDER_NAME,
                response_time_ms=result.response_time_ms,
            )

        return result

    async def get_account_info(self) -> FinanceResult[dict]:
        """
        Récupère les informations du projet Swan.

        Returns:
            FinanceResult avec infos projet
        """
        return await self._request("GET", f"/projects/{self.project_id}")

    # =========================================================================
    # COMPTES
    # =========================================================================

    async def get_accounts(
        self,
        first: int = 20,
        after: Optional[str] = None,
        status: Optional[SwanAccountStatus] = None,
    ) -> FinanceResult[list[SwanAccountResponse]]:
        """
        Liste les comptes bancaires du projet.

        Args:
            first: Nombre de résultats (max 100)
            after: Curseur de pagination
            status: Filtrer par statut

        Returns:
            FinanceResult avec liste de comptes
        """
        # Vérifier le cache
        cache_key = self._cache_key("accounts", first, after or "", status or "")
        cached = await self._get_cached(cache_key)
        if cached:
            accounts = [SwanAccountResponse(**a) for a in cached["accounts"]]
            return FinanceResult.ok(
                data=accounts,
                provider=self.PROVIDER_NAME,
                cached=True,
                total_count=cached.get("total_count"),
                has_more=cached.get("has_more", False),
            )

        # Construire les paramètres
        params = {"first": first}
        if after:
            params["after"] = after
        if status:
            params["status"] = status.value

        # Requête API
        result = await self._request("GET", "/accounts", params=params)

        if not result.success:
            return result

        # Parser la réponse
        try:
            data = result.data
            accounts_data = data.get("accounts", data.get("edges", []))

            # Swan utilise GraphQL-like pagination
            if isinstance(accounts_data, list) and accounts_data and "node" in accounts_data[0]:
                accounts = [
                    SwanAccountResponse(**self._map_account(edge["node"]))
                    for edge in accounts_data
                ]
            else:
                accounts = [
                    SwanAccountResponse(**self._map_account(acc))
                    for acc in (accounts_data if isinstance(accounts_data, list) else [accounts_data])
                ]

            page_info = data.get("pageInfo", {})
            has_more = page_info.get("hasNextPage", False)
            total_count = data.get("totalCount")

            # Mettre en cache
            await self._set_cached(cache_key, {
                "accounts": [a.model_dump() for a in accounts],
                "total_count": total_count,
                "has_more": has_more,
            })

            return FinanceResult.ok(
                data=accounts,
                provider=self.PROVIDER_NAME,
                request_id=result.request_id,
                response_time_ms=result.response_time_ms,
                total_count=total_count,
                has_more=has_more,
            )

        except Exception as e:
            self._logger.error(f"Erreur parsing comptes Swan: {e}")
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INTERNAL_ERROR,
                    message=f"Erreur parsing réponse: {str(e)}",
                ),
                provider=self.PROVIDER_NAME,
                request_id=result.request_id,
            )

    async def get_account(self, account_id: str) -> FinanceResult[SwanAccountResponse]:
        """
        Récupère un compte par son ID.

        Args:
            account_id: ID du compte Swan

        Returns:
            FinanceResult avec le compte
        """
        result = await self._request("GET", f"/accounts/{account_id}")

        if not result.success:
            return result

        try:
            account = SwanAccountResponse(**self._map_account(result.data))
            return FinanceResult.ok(
                data=account,
                provider=self.PROVIDER_NAME,
                request_id=result.request_id,
                response_time_ms=result.response_time_ms,
            )
        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INTERNAL_ERROR,
                    message=f"Erreur parsing compte: {str(e)}",
                ),
                provider=self.PROVIDER_NAME,
            )

    async def get_account_balance(self, account_id: str) -> FinanceResult[dict]:
        """
        Récupère le solde d'un compte.

        Args:
            account_id: ID du compte Swan

        Returns:
            FinanceResult avec soldes
        """
        result = await self.get_account(account_id)

        if not result.success:
            return result

        account = result.data
        return FinanceResult.ok(
            data={
                "available": account.balance_available,
                "booked": account.balance_booked,
                "pending": account.balance_pending,
                "currency": account.currency,
                "formatted_available": f"{account.balance_available / 100:.2f} {account.currency}",
                "formatted_booked": f"{account.balance_booked / 100:.2f} {account.currency}",
            },
            provider=self.PROVIDER_NAME,
            request_id=result.request_id,
            response_time_ms=result.response_time_ms,
        )

    def _map_account(self, data: dict) -> dict:
        """Mappe les données Swan vers SwanAccountResponse."""
        return {
            "id": data.get("id"),
            "name": data.get("name", data.get("label", "")),
            "status": data.get("status", "Opened"),
            "iban": data.get("IBAN", data.get("iban", "")),
            "bic": data.get("BIC", data.get("bic", "SABORFRP")),
            "currency": data.get("currency", "EUR"),
            "balance_available": data.get("availableBalance", {}).get("value", 0)
                if isinstance(data.get("availableBalance"), dict)
                else data.get("balanceAvailable", 0),
            "balance_booked": data.get("bookedBalance", {}).get("value", 0)
                if isinstance(data.get("bookedBalance"), dict)
                else data.get("balanceBooked", 0),
            "balance_pending": data.get("pendingBalance", {}).get("value", 0)
                if isinstance(data.get("pendingBalance"), dict)
                else data.get("balancePending", 0),
            "holder_name": data.get("holder", {}).get("name", "")
                if isinstance(data.get("holder"), dict)
                else data.get("holderName", ""),
            "created_at": data.get("createdAt", datetime.utcnow().isoformat()),
            "updated_at": data.get("updatedAt"),
        }

    # =========================================================================
    # TRANSACTIONS
    # =========================================================================

    async def get_transactions(
        self,
        account_id: str,
        first: int = 20,
        after: Optional[str] = None,
        status: Optional[SwanTransactionStatus] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> FinanceResult[list[SwanTransactionResponse]]:
        """
        Liste les transactions d'un compte.

        Args:
            account_id: ID du compte Swan
            first: Nombre de résultats (max 100)
            after: Curseur de pagination
            status: Filtrer par statut
            from_date: Date de début
            to_date: Date de fin

        Returns:
            FinanceResult avec liste de transactions
        """
        params = {
            "first": first,
            "accountId": account_id,
        }

        if after:
            params["after"] = after
        if status:
            params["status"] = status.value
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()

        result = await self._request(
            "GET",
            f"/accounts/{account_id}/transactions",
            params=params
        )

        if not result.success:
            return result

        try:
            data = result.data
            transactions_data = data.get("transactions", data.get("edges", []))

            if isinstance(transactions_data, list) and transactions_data and "node" in transactions_data[0]:
                transactions = [
                    SwanTransactionResponse(**self._map_transaction(edge["node"]))
                    for edge in transactions_data
                ]
            else:
                transactions = [
                    SwanTransactionResponse(**self._map_transaction(tx))
                    for tx in (transactions_data if isinstance(transactions_data, list) else [transactions_data])
                ]

            page_info = data.get("pageInfo", {})
            has_more = page_info.get("hasNextPage", False)
            total_count = data.get("totalCount")

            return FinanceResult.ok(
                data=transactions,
                provider=self.PROVIDER_NAME,
                request_id=result.request_id,
                response_time_ms=result.response_time_ms,
                total_count=total_count,
                has_more=has_more,
            )

        except Exception as e:
            self._logger.error(f"Erreur parsing transactions Swan: {e}")
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INTERNAL_ERROR,
                    message=f"Erreur parsing réponse: {str(e)}",
                ),
                provider=self.PROVIDER_NAME,
            )

    async def get_transaction(
        self,
        account_id: str,
        transaction_id: str
    ) -> FinanceResult[SwanTransactionResponse]:
        """
        Récupère une transaction par son ID.

        Args:
            account_id: ID du compte Swan
            transaction_id: ID de la transaction

        Returns:
            FinanceResult avec la transaction
        """
        result = await self._request(
            "GET",
            f"/accounts/{account_id}/transactions/{transaction_id}"
        )

        if not result.success:
            return result

        try:
            transaction = SwanTransactionResponse(**self._map_transaction(result.data))
            return FinanceResult.ok(
                data=transaction,
                provider=self.PROVIDER_NAME,
                request_id=result.request_id,
                response_time_ms=result.response_time_ms,
            )
        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INTERNAL_ERROR,
                    message=f"Erreur parsing transaction: {str(e)}",
                ),
                provider=self.PROVIDER_NAME,
            )

    def _map_transaction(self, data: dict) -> dict:
        """Mappe les données Swan vers SwanTransactionResponse."""
        # Déterminer le montant (positif ou négatif selon le type)
        amount = data.get("amount", {})
        if isinstance(amount, dict):
            amount_value = amount.get("value", 0)
        else:
            amount_value = amount or 0

        return {
            "id": data.get("id"),
            "status": data.get("status", "Booked"),
            "type": data.get("type", data.get("__typename", "SepaCreditTransferIn")),
            "amount": amount_value,
            "currency": data.get("currency", "EUR"),
            "reference": data.get("reference"),
            "label": data.get("label", data.get("description")),
            "counterparty_name": data.get("counterparty", {}).get("name")
                if isinstance(data.get("counterparty"), dict)
                else data.get("counterpartyName"),
            "counterparty_iban": data.get("counterparty", {}).get("IBAN")
                if isinstance(data.get("counterparty"), dict)
                else data.get("counterpartyIban"),
            "execution_date": data.get("executionDate"),
            "booking_date": data.get("bookingDate"),
            "created_at": data.get("createdAt", datetime.utcnow().isoformat()),
        }

    # =========================================================================
    # VIREMENTS
    # =========================================================================

    async def create_transfer(
        self,
        account_id: str,
        request: SwanTransferRequest,
    ) -> FinanceResult[SwanTransferResponse]:
        """
        Crée un virement SEPA (SCT).

        Args:
            account_id: ID du compte débiteur
            request: Détails du virement

        Returns:
            FinanceResult avec le virement créé
        """
        payload = {
            "accountId": account_id,
            "amount": {
                "value": request.amount,
                "currency": request.currency,
            },
            "creditor": {
                "name": request.creditor_name,
                "IBAN": request.creditor_iban,
            },
        }

        if request.reference:
            payload["reference"] = request.reference
        if request.label:
            payload["label"] = request.label

        result = await self._request(
            "POST",
            "/payments/credit-transfers",
            json_data=payload,
        )

        if not result.success:
            return result

        try:
            data = result.data
            transfer = SwanTransferResponse(
                id=data.get("id"),
                status=data.get("status", "Initiated"),
                amount=request.amount,
                currency=request.currency,
                creditor_name=request.creditor_name,
                creditor_iban=request.creditor_iban,
                reference=request.reference,
                consent_url=data.get("consentUrl"),
                created_at=data.get("createdAt", datetime.utcnow()),
            )

            self._logger.info(
                f"Virement créé: {transfer.id} -> {request.creditor_name} ({request.amount / 100}€)",
                extra={
                    "transfer_id": transfer.id,
                    "amount": request.amount,
                    "creditor": request.creditor_name,
                }
            )

            return FinanceResult.ok(
                data=transfer,
                provider=self.PROVIDER_NAME,
                request_id=result.request_id,
                response_time_ms=result.response_time_ms,
            )

        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INTERNAL_ERROR,
                    message=f"Erreur création virement: {str(e)}",
                ),
                provider=self.PROVIDER_NAME,
            )

    async def get_transfer(self, transfer_id: str) -> FinanceResult[SwanTransferResponse]:
        """
        Récupère le statut d'un virement.

        Args:
            transfer_id: ID du virement

        Returns:
            FinanceResult avec le virement
        """
        result = await self._request("GET", f"/payments/{transfer_id}")

        if not result.success:
            return result

        try:
            data = result.data
            transfer = SwanTransferResponse(
                id=data.get("id"),
                status=data.get("status"),
                amount=data.get("amount", {}).get("value", 0),
                currency=data.get("amount", {}).get("currency", "EUR"),
                creditor_name=data.get("creditor", {}).get("name", ""),
                creditor_iban=data.get("creditor", {}).get("IBAN", ""),
                reference=data.get("reference"),
                consent_url=data.get("consentUrl"),
                created_at=data.get("createdAt", datetime.utcnow()),
            )

            return FinanceResult.ok(
                data=transfer,
                provider=self.PROVIDER_NAME,
                request_id=result.request_id,
                response_time_ms=result.response_time_ms,
            )
        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INTERNAL_ERROR,
                    message=f"Erreur récupération virement: {str(e)}",
                ),
                provider=self.PROVIDER_NAME,
            )

    # =========================================================================
    # WEBHOOKS
    # =========================================================================

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None,
    ) -> bool:
        """
        Vérifie la signature HMAC-SHA256 d'un webhook Swan.

        Args:
            payload: Corps brut du webhook
            signature: Signature fournie dans le header
            timestamp: Timestamp du webhook (optionnel)

        Returns:
            True si la signature est valide
        """
        if not self.webhook_secret:
            self._logger.warning("Webhook secret non configuré")
            return False

        try:
            # Swan utilise HMAC-SHA256
            if timestamp:
                signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            else:
                signed_payload = payload.decode("utf-8")

            expected_signature = hmac.new(
                self.webhook_secret.encode("utf-8"),
                signed_payload.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            # Comparaison sécurisée (timing-safe)
            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            self._logger.error(f"Erreur vérification signature webhook: {e}")
            return False

    def parse_webhook_event(self, payload: dict) -> WebhookEvent:
        """
        Parse un payload webhook Swan.

        Args:
            payload: Données JSON du webhook

        Returns:
            WebhookEvent structuré
        """
        # Mapper les types d'événements Swan vers WebhookEventType
        event_type_mapping = {
            "Transaction.Booked": WebhookEventType.TRANSACTION_COMPLETED,
            "Transaction.Pending": WebhookEventType.TRANSACTION_PENDING,
            "Transaction.Rejected": WebhookEventType.TRANSACTION_FAILED,
            "Payment.Initiated": WebhookEventType.PAYMENT_INITIATED,
            "Payment.Released": WebhookEventType.PAYMENT_CAPTURED,
            "Payment.Rejected": WebhookEventType.TRANSACTION_FAILED,
            "Account.Opened": WebhookEventType.ACCOUNT_CREATED,
            "Account.Closed": WebhookEventType.ACCOUNT_CLOSED,
            "Account.Updated": WebhookEventType.ACCOUNT_UPDATED,
        }

        swan_event_type = payload.get("eventType", "")
        event_type = event_type_mapping.get(
            swan_event_type,
            WebhookEventType.TRANSACTION_CREATED
        )

        # Parse timestamp (handle ISO 8601 'Z' suffix)
        timestamp_str = payload.get("timestamp", datetime.utcnow().isoformat())
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1] + "+00:00"

        return WebhookEvent(
            id=payload.get("eventId", ""),
            type=event_type,
            provider=FinanceProviderType.SWAN,
            tenant_id=self.tenant_id,
            payload=payload.get("data", payload),
            raw_payload=str(payload),
            timestamp=datetime.fromisoformat(timestamp_str),
        )

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    async def sync_transactions(
        self,
        account_id: str,
        since: Optional[datetime] = None,
    ) -> FinanceResult[dict]:
        """
        Synchronise toutes les transactions depuis une date.

        Utile pour la réconciliation bancaire.

        Args:
            account_id: ID du compte
            since: Date de début (défaut: 30 jours)

        Returns:
            FinanceResult avec statistiques de sync
        """
        from datetime import timedelta

        if not since:
            since = datetime.utcnow() - timedelta(days=30)

        all_transactions = []
        cursor = None
        total_fetched = 0

        while True:
            result = await self.get_transactions(
                account_id=account_id,
                first=100,
                after=cursor,
                from_date=since,
            )

            if not result.success:
                return result

            all_transactions.extend(result.data)
            total_fetched += len(result.data)

            if not result.has_more:
                break

            # Extraire le curseur de la dernière transaction
            if result.data:
                cursor = result.data[-1].id

        return FinanceResult.ok(
            data={
                "account_id": account_id,
                "transactions_count": len(all_transactions),
                "since": since.isoformat(),
                "transactions": [t.model_dump() for t in all_transactions],
            },
            provider=self.PROVIDER_NAME,
        )
