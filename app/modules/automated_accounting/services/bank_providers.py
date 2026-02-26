"""
AZALSCORE - Providers Bancaires Multi-Banques
==============================================

Intégrations bancaires pour la synchronisation des comptes et transactions.

Providers supportés:
- Bridge (Budget Insight) - 350+ banques FR/EU
- Plaid - 11,000+ institutions US/EU
- Nordigen (GoCardless) - Open Banking EU gratuit
- Tink - 3,400+ banques EU
- Mock - Tests et développement

Références:
- DSP2 (PSD2) - Directive Services de Paiement
- Open Banking API Standards
"""
from __future__ import annotations


import hashlib
import hmac
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# TYPES COMMUNS
# ============================================================================

class BankAccountType(str, Enum):
    """Types de comptes bancaires."""
    CHECKING = "checking"       # Compte courant
    SAVINGS = "savings"         # Compte épargne
    CREDIT = "credit"          # Carte de crédit
    LOAN = "loan"              # Prêt
    INVESTMENT = "investment"  # Compte titres
    OTHER = "other"


class TransactionType(str, Enum):
    """Types de transactions."""
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"


class TransactionCategory(str, Enum):
    """Catégories de transactions (pour auto-catégorisation)."""
    INCOME = "income"
    SALARY = "salary"
    RENT = "rent"
    UTILITIES = "utilities"
    TELECOM = "telecom"
    INSURANCE = "insurance"
    TRANSPORT = "transport"
    FOOD = "food"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    HEALTH = "health"
    TAXES = "taxes"
    TRANSFER = "transfer"
    BANK_FEES = "bank_fees"
    OTHER = "other"


@dataclass
class BankAccount:
    """Compte bancaire synchronisé."""
    account_id: str
    name: str
    type: BankAccountType
    balance: Decimal
    available_balance: Optional[Decimal] = None
    currency: str = "EUR"
    iban: Optional[str] = None
    iban_masked: Optional[str] = None
    bic: Optional[str] = None
    account_number_masked: Optional[str] = None
    last_sync: Optional[datetime] = None


@dataclass
class BankTransaction:
    """Transaction bancaire."""
    transaction_id: str
    account_id: str
    date: date
    value_date: Optional[date] = None
    amount: Decimal = Decimal("0")
    currency: str = "EUR"
    description: str = ""
    clean_description: Optional[str] = None
    merchant_name: Optional[str] = None
    category: Optional[TransactionCategory] = None
    type: TransactionType = TransactionType.DEBIT
    pending: bool = False
    metadata: dict = None


@dataclass
class ConnectionResult:
    """Résultat de création de connexion."""
    connection_id: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    consent_expires_at: Optional[datetime] = None
    status: str = "active"
    institution_name: str = ""


# ============================================================================
# INTERFACE PROVIDER
# ============================================================================

class BankProvider(ABC):
    """Interface abstraite pour les providers bancaires."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nom du provider."""
        pass

    @property
    @abstractmethod
    def supported_countries(self) -> list[str]:
        """Pays supportés (codes ISO)."""
        pass

    @abstractmethod
    async def create_connection(
        self,
        institution_id: str,
        redirect_url: str = None,
        **kwargs
    ) -> ConnectionResult:
        """Crée une connexion à une institution bancaire."""
        pass

    @abstractmethod
    async def get_accounts(self, access_token: str) -> list[BankAccount]:
        """Récupère les comptes liés à une connexion."""
        pass

    @abstractmethod
    async def get_transactions(
        self,
        access_token: str,
        account_id: str,
        start_date: date,
        end_date: date
    ) -> list[BankTransaction]:
        """Récupère les transactions d'un compte."""
        pass

    @abstractmethod
    async def get_balance(self, access_token: str, account_id: str) -> dict:
        """Récupère le solde d'un compte."""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> ConnectionResult:
        """Rafraîchit le token d'accès."""
        pass

    async def list_institutions(self, country: str = "FR") -> list[dict]:
        """Liste les institutions disponibles."""
        return []


# ============================================================================
# PROVIDER: BRIDGE (Budget Insight)
# ============================================================================

class BridgeProvider(BankProvider):
    """
    Provider Bridge (Budget Insight / Bankin').

    Leader français de l'agrégation bancaire.
    350+ banques FR/EU, certifié ACPR.

    API Docs: https://docs.bridgeapi.io/
    """

    BASE_URL = "https://api.bridgeapi.io/v2"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        sandbox: bool = False,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.sandbox = sandbox
        if sandbox:
            self.BASE_URL = "https://api.bridgeapi.io/v2/sandbox"

    @property
    def provider_name(self) -> str:
        return "bridge"

    @property
    def supported_countries(self) -> list[str]:
        return ["FR", "ES", "DE", "GB", "IT", "BE", "NL", "PT"]

    async def _request(
        self,
        method: str,
        endpoint: str,
        access_token: str = None,
        data: dict = None,
    ) -> dict:
        """Effectue une requête à l'API Bridge."""
        import httpx

        headers = {
            "Bridge-Version": "2021-06-01",
            "Client-Id": self.client_id,
            "Client-Secret": self.client_secret,
            "Content-Type": "application/json",
        }

        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        url = f"{self.BASE_URL}{endpoint}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(url, headers=headers, params=data)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Méthode HTTP non supportée: {method}")

            response.raise_for_status()
            return response.json()

    async def create_connection(
        self,
        institution_id: str,
        redirect_url: str = None,
        user_email: str = None,
        **kwargs
    ) -> ConnectionResult:
        """
        Crée une connexion Bridge.

        Retourne une URL de redirection pour le parcours utilisateur.
        """
        data = {
            "bank_id": int(institution_id),
        }

        if user_email:
            data["email"] = user_email

        if redirect_url:
            data["redirect_url"] = redirect_url

        result = await self._request("POST", "/connect/items/add", data=data)

        return ConnectionResult(
            connection_id=str(result.get("item_id", "")),
            access_token=result.get("access_token", ""),
            refresh_token=result.get("refresh_token"),
            expires_at=datetime.utcnow() + timedelta(days=90),
            status="pending_user_action",
            institution_name=result.get("bank", {}).get("name", ""),
        )

    async def get_accounts(self, access_token: str) -> list[BankAccount]:
        """Récupère les comptes Bridge."""
        result = await self._request("GET", "/accounts", access_token=access_token)

        accounts = []
        for acc in result.get("resources", []):
            account_type = self._map_account_type(acc.get("type", ""))

            accounts.append(BankAccount(
                account_id=str(acc["id"]),
                name=acc.get("name", ""),
                type=account_type,
                balance=Decimal(str(acc.get("balance", 0))),
                currency=acc.get("currency_code", "EUR"),
                iban=acc.get("iban"),
                iban_masked=self._mask_iban(acc.get("iban")),
                last_sync=datetime.fromisoformat(acc["updated_at"]) if acc.get("updated_at") else None,
            ))

        return accounts

    async def get_transactions(
        self,
        access_token: str,
        account_id: str,
        start_date: date,
        end_date: date
    ) -> list[BankTransaction]:
        """Récupère les transactions Bridge."""
        params = {
            "account_id": account_id,
            "since": start_date.isoformat(),
            "until": end_date.isoformat(),
            "limit": 500,
        }

        result = await self._request(
            "GET", "/transactions", access_token=access_token, data=params
        )

        transactions = []
        for txn in result.get("resources", []):
            amount = Decimal(str(txn.get("amount", 0)))

            transactions.append(BankTransaction(
                transaction_id=str(txn["id"]),
                account_id=account_id,
                date=date.fromisoformat(txn["date"]),
                value_date=date.fromisoformat(txn["value_date"]) if txn.get("value_date") else None,
                amount=abs(amount),
                currency=txn.get("currency_code", "EUR"),
                description=txn.get("raw_description", ""),
                clean_description=txn.get("description", ""),
                category=self._map_category(txn.get("category_id")),
                type=TransactionType.CREDIT if amount > 0 else TransactionType.DEBIT,
                pending=txn.get("is_future", False),
            ))

        return transactions

    async def get_balance(self, access_token: str, account_id: str) -> dict:
        """Récupère le solde d'un compte Bridge."""
        result = await self._request(
            "GET", f"/accounts/{account_id}", access_token=access_token
        )

        return {
            "current": Decimal(str(result.get("balance", 0))),
            "available": None,
            "currency": result.get("currency_code", "EUR"),
            "updated_at": result.get("updated_at"),
        }

    async def refresh_token(self, refresh_token: str) -> ConnectionResult:
        """Rafraîchit le token Bridge."""
        result = await self._request(
            "POST", "/connect/items/refresh",
            data={"refresh_token": refresh_token}
        )

        return ConnectionResult(
            connection_id=str(result.get("item_id", "")),
            access_token=result.get("access_token", ""),
            refresh_token=result.get("refresh_token"),
            expires_at=datetime.utcnow() + timedelta(days=90),
            status="active",
        )

    async def list_institutions(self, country: str = "FR") -> list[dict]:
        """Liste les banques disponibles."""
        result = await self._request(
            "GET", "/banks",
            data={"country": country}
        )

        return [
            {
                "id": str(bank["id"]),
                "name": bank["name"],
                "country": bank.get("country_code", country),
                "logo_url": bank.get("logo_url"),
                "form_fields": bank.get("form", []),
            }
            for bank in result.get("resources", [])
        ]

    def _map_account_type(self, bridge_type: str) -> BankAccountType:
        """Mappe le type de compte Bridge."""
        mapping = {
            "checking": BankAccountType.CHECKING,
            "savings": BankAccountType.SAVINGS,
            "brokerage": BankAccountType.INVESTMENT,
            "card": BankAccountType.CREDIT,
            "loan": BankAccountType.LOAN,
        }
        return mapping.get(bridge_type, BankAccountType.OTHER)

    def _map_category(self, category_id: int) -> TransactionCategory:
        """Mappe la catégorie Bridge."""
        # Catégories Bridge simplifiées
        mapping = {
            1: TransactionCategory.INCOME,
            2: TransactionCategory.SALARY,
            10: TransactionCategory.RENT,
            20: TransactionCategory.UTILITIES,
            30: TransactionCategory.TRANSPORT,
            40: TransactionCategory.FOOD,
            50: TransactionCategory.SHOPPING,
            60: TransactionCategory.HEALTH,
            70: TransactionCategory.TAXES,
            80: TransactionCategory.TRANSFER,
        }
        return mapping.get(category_id, TransactionCategory.OTHER)

    def _mask_iban(self, iban: str) -> str:
        """Masque un IBAN."""
        if not iban or len(iban) < 10:
            return iban
        return f"{iban[:4]} **** **** {iban[-4:]}"


# ============================================================================
# PROVIDER: NORDIGEN (GoCardless Open Banking)
# ============================================================================

class NordigenProvider(BankProvider):
    """
    Provider Nordigen (GoCardless Bank Account Data).

    Open Banking gratuit pour l'UE (PSD2).
    2,300+ banques EU.

    API Docs: https://nordigen.com/en/docs/
    """

    BASE_URL = "https://ob.nordigen.com/api/v2"

    def __init__(
        self,
        secret_id: str,
        secret_key: str,
    ):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self._access_token = None
        self._token_expires = None

    @property
    def provider_name(self) -> str:
        return "nordigen"

    @property
    def supported_countries(self) -> list[str]:
        return [
            "FR", "DE", "GB", "ES", "IT", "NL", "BE", "PT", "AT", "CH",
            "SE", "NO", "DK", "FI", "IE", "PL", "CZ", "HU", "RO", "BG"
        ]

    async def _get_access_token(self) -> str:
        """Obtient un token d'accès Nordigen."""
        if self._access_token and self._token_expires and datetime.utcnow() < self._token_expires:
            return self._access_token

        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/token/new/",
                json={
                    "secret_id": self.secret_id,
                    "secret_key": self.secret_key,
                }
            )
            response.raise_for_status()
            data = response.json()

            self._access_token = data["access"]
            self._token_expires = datetime.utcnow() + timedelta(seconds=data.get("access_expires", 86400))

            return self._access_token

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict = None,
    ) -> dict:
        """Effectue une requête à l'API Nordigen."""
        import httpx

        token = await self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        url = f"{self.BASE_URL}{endpoint}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(url, headers=headers, params=data)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Méthode HTTP non supportée: {method}")

            response.raise_for_status()
            return response.json()

    async def create_connection(
        self,
        institution_id: str,
        redirect_url: str = None,
        reference: str = None,
        **kwargs
    ) -> ConnectionResult:
        """
        Crée une connexion Nordigen via requisition.

        1. Créer un end user agreement
        2. Créer une requisition
        3. Rediriger l'utilisateur vers la banque
        """
        # Créer l'agreement (consentement)
        agreement = await self._request("POST", "/agreements/enduser/", data={
            "institution_id": institution_id,
            "max_historical_days": 90,
            "access_valid_for_days": 90,
            "access_scope": ["balances", "details", "transactions"],
        })

        # Créer la requisition
        requisition = await self._request("POST", "/requisitions/", data={
            "redirect": redirect_url or "https://app.azalscore.com/callback",
            "institution_id": institution_id,
            "reference": reference or str(uuid.uuid4()),
            "agreement": agreement["id"],
            "user_language": "FR",
        })

        return ConnectionResult(
            connection_id=requisition["id"],
            access_token=requisition["id"],  # La requisition sert de token
            expires_at=datetime.utcnow() + timedelta(days=90),
            consent_expires_at=datetime.utcnow() + timedelta(days=90),
            status="pending_user_action",
            institution_name="",
        )

    async def get_accounts(self, access_token: str) -> list[BankAccount]:
        """Récupère les comptes via Nordigen."""
        # access_token = requisition_id dans Nordigen
        requisition = await self._request("GET", f"/requisitions/{access_token}/")

        accounts = []
        for account_id in requisition.get("accounts", []):
            # Récupérer les détails du compte
            details = await self._request("GET", f"/accounts/{account_id}/details/")
            balances = await self._request("GET", f"/accounts/{account_id}/balances/")

            acc_details = details.get("account", {})
            balance_info = balances.get("balances", [{}])[0]

            accounts.append(BankAccount(
                account_id=account_id,
                name=acc_details.get("name", acc_details.get("product", "Compte")),
                type=self._map_account_type(acc_details.get("cashAccountType", "")),
                balance=Decimal(str(balance_info.get("balanceAmount", {}).get("amount", 0))),
                currency=acc_details.get("currency", "EUR"),
                iban=acc_details.get("iban"),
                iban_masked=self._mask_iban(acc_details.get("iban")),
                bic=acc_details.get("bic"),
            ))

        return accounts

    async def get_transactions(
        self,
        access_token: str,
        account_id: str,
        start_date: date,
        end_date: date
    ) -> list[BankTransaction]:
        """Récupère les transactions Nordigen."""
        result = await self._request(
            "GET",
            f"/accounts/{account_id}/transactions/",
            data={
                "date_from": start_date.isoformat(),
                "date_to": end_date.isoformat(),
            }
        )

        transactions = []
        for txn in result.get("transactions", {}).get("booked", []):
            amount = Decimal(str(txn.get("transactionAmount", {}).get("amount", 0)))

            transactions.append(BankTransaction(
                transaction_id=txn.get("transactionId", txn.get("internalTransactionId", str(uuid.uuid4()))),
                account_id=account_id,
                date=date.fromisoformat(txn.get("bookingDate", txn.get("valueDate", ""))),
                value_date=date.fromisoformat(txn["valueDate"]) if txn.get("valueDate") else None,
                amount=abs(amount),
                currency=txn.get("transactionAmount", {}).get("currency", "EUR"),
                description=txn.get("remittanceInformationUnstructured", ""),
                clean_description=txn.get("remittanceInformationStructured", ""),
                merchant_name=txn.get("creditorName") or txn.get("debtorName"),
                type=TransactionType.CREDIT if amount > 0 else TransactionType.DEBIT,
                pending=False,
            ))

        # Transactions en attente
        for txn in result.get("transactions", {}).get("pending", []):
            amount = Decimal(str(txn.get("transactionAmount", {}).get("amount", 0)))

            transactions.append(BankTransaction(
                transaction_id=txn.get("transactionId", str(uuid.uuid4())),
                account_id=account_id,
                date=date.fromisoformat(txn.get("bookingDate", date.today().isoformat())),
                amount=abs(amount),
                currency=txn.get("transactionAmount", {}).get("currency", "EUR"),
                description=txn.get("remittanceInformationUnstructured", ""),
                type=TransactionType.CREDIT if amount > 0 else TransactionType.DEBIT,
                pending=True,
            ))

        return transactions

    async def get_balance(self, access_token: str, account_id: str) -> dict:
        """Récupère le solde Nordigen."""
        result = await self._request("GET", f"/accounts/{account_id}/balances/")

        balances = result.get("balances", [])
        current = Decimal("0")
        available = None

        for bal in balances:
            amount = Decimal(str(bal.get("balanceAmount", {}).get("amount", 0)))
            if bal.get("balanceType") == "interimAvailable":
                available = amount
            elif bal.get("balanceType") in ["closingBooked", "expected"]:
                current = amount

        return {
            "current": current,
            "available": available,
            "currency": balances[0].get("balanceAmount", {}).get("currency", "EUR") if balances else "EUR",
        }

    async def refresh_token(self, refresh_token: str) -> ConnectionResult:
        """Nordigen n'utilise pas de refresh token classique."""
        # Vérifier si la requisition est toujours valide
        requisition = await self._request("GET", f"/requisitions/{refresh_token}/")

        return ConnectionResult(
            connection_id=requisition["id"],
            access_token=requisition["id"],
            status=requisition.get("status", "LN"),
        )

    async def list_institutions(self, country: str = "FR") -> list[dict]:
        """Liste les banques disponibles."""
        result = await self._request(
            "GET",
            "/institutions/",
            data={"country": country}
        )

        return [
            {
                "id": inst["id"],
                "name": inst["name"],
                "country": country,
                "logo_url": inst.get("logo"),
                "bic": inst.get("bic"),
                "transaction_total_days": inst.get("transaction_total_days", 90),
            }
            for inst in result
        ]

    def _map_account_type(self, nordigen_type: str) -> BankAccountType:
        """Mappe le type de compte Nordigen."""
        mapping = {
            "CACC": BankAccountType.CHECKING,
            "SVGS": BankAccountType.SAVINGS,
            "CARD": BankAccountType.CREDIT,
            "LOAN": BankAccountType.LOAN,
        }
        return mapping.get(nordigen_type, BankAccountType.OTHER)

    def _mask_iban(self, iban: str) -> str:
        """Masque un IBAN."""
        if not iban or len(iban) < 10:
            return iban
        return f"{iban[:4]} **** **** {iban[-4:]}"


# ============================================================================
# PROVIDER: PLAID
# ============================================================================

class PlaidProvider(BankProvider):
    """
    Provider Plaid.

    Leader US/UK de l'agrégation bancaire.
    11,000+ institutions.

    API Docs: https://plaid.com/docs/
    """

    def __init__(
        self,
        client_id: str,
        secret: str,
        environment: str = "sandbox",  # sandbox, development, production
    ):
        self.client_id = client_id
        self.secret = secret
        self.environment = environment

        env_urls = {
            "sandbox": "https://sandbox.plaid.com",
            "development": "https://development.plaid.com",
            "production": "https://production.plaid.com",
        }
        self.BASE_URL = env_urls.get(environment, env_urls["sandbox"])

    @property
    def provider_name(self) -> str:
        return "plaid"

    @property
    def supported_countries(self) -> list[str]:
        return ["US", "CA", "GB", "IE", "FR", "ES", "NL"]

    async def _request(
        self,
        endpoint: str,
        data: dict = None,
    ) -> dict:
        """Effectue une requête à l'API Plaid."""
        import httpx

        payload = {
            "client_id": self.client_id,
            "secret": self.secret,
        }
        if data:
            payload.update(data)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}{endpoint}",
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def create_connection(
        self,
        institution_id: str,
        redirect_url: str = None,
        user_id: str = None,
        **kwargs
    ) -> ConnectionResult:
        """
        Crée une connexion Plaid via Link.

        Retourne un link_token pour initialiser Plaid Link.
        """
        result = await self._request("/link/token/create", {
            "user": {"client_user_id": user_id or str(uuid.uuid4())},
            "client_name": "AZALSCORE",
            "products": ["transactions"],
            "country_codes": ["FR", "GB", "US"],
            "language": "fr",
            "redirect_uri": redirect_url,
        })

        return ConnectionResult(
            connection_id="",
            access_token=result["link_token"],
            expires_at=datetime.fromisoformat(result["expiration"].replace("Z", "+00:00")),
            status="pending_link",
        )

    async def exchange_public_token(self, public_token: str) -> ConnectionResult:
        """Échange le public token contre un access token."""
        result = await self._request("/item/public_token/exchange", {
            "public_token": public_token,
        })

        return ConnectionResult(
            connection_id=result["item_id"],
            access_token=result["access_token"],
            status="active",
        )

    async def get_accounts(self, access_token: str) -> list[BankAccount]:
        """Récupère les comptes Plaid."""
        result = await self._request("/accounts/get", {
            "access_token": access_token,
        })

        accounts = []
        for acc in result.get("accounts", []):
            accounts.append(BankAccount(
                account_id=acc["account_id"],
                name=acc.get("name", acc.get("official_name", "")),
                type=self._map_account_type(acc.get("type", "")),
                balance=Decimal(str(acc.get("balances", {}).get("current", 0))),
                available_balance=Decimal(str(acc["balances"]["available"])) if acc.get("balances", {}).get("available") else None,
                currency=acc.get("balances", {}).get("iso_currency_code", "EUR"),
                account_number_masked=acc.get("mask"),
            ))

        return accounts

    async def get_transactions(
        self,
        access_token: str,
        account_id: str,
        start_date: date,
        end_date: date
    ) -> list[BankTransaction]:
        """Récupère les transactions Plaid."""
        result = await self._request("/transactions/get", {
            "access_token": access_token,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "options": {
                "account_ids": [account_id],
                "count": 500,
            },
        })

        transactions = []
        for txn in result.get("transactions", []):
            amount = Decimal(str(txn.get("amount", 0)))

            transactions.append(BankTransaction(
                transaction_id=txn["transaction_id"],
                account_id=txn["account_id"],
                date=date.fromisoformat(txn["date"]),
                value_date=date.fromisoformat(txn["authorized_date"]) if txn.get("authorized_date") else None,
                amount=abs(amount),
                currency=txn.get("iso_currency_code", "EUR"),
                description=txn.get("name", ""),
                clean_description=txn.get("merchant_name"),
                merchant_name=txn.get("merchant_name"),
                category=self._map_category(txn.get("category", [])),
                type=TransactionType.DEBIT if amount > 0 else TransactionType.CREDIT,
                pending=txn.get("pending", False),
            ))

        return transactions

    async def get_balance(self, access_token: str, account_id: str) -> dict:
        """Récupère le solde Plaid."""
        result = await self._request("/accounts/balance/get", {
            "access_token": access_token,
            "options": {"account_ids": [account_id]},
        })

        acc = result.get("accounts", [{}])[0]
        balances = acc.get("balances", {})

        return {
            "current": Decimal(str(balances.get("current", 0))),
            "available": Decimal(str(balances["available"])) if balances.get("available") else None,
            "currency": balances.get("iso_currency_code", "EUR"),
        }

    async def refresh_token(self, refresh_token: str) -> ConnectionResult:
        """Plaid n'utilise pas de refresh token classique."""
        # L'access_token Plaid n'expire pas
        return ConnectionResult(
            connection_id="",
            access_token=refresh_token,
            status="active",
        )

    def _map_account_type(self, plaid_type: str) -> BankAccountType:
        """Mappe le type de compte Plaid."""
        mapping = {
            "depository": BankAccountType.CHECKING,
            "credit": BankAccountType.CREDIT,
            "loan": BankAccountType.LOAN,
            "investment": BankAccountType.INVESTMENT,
        }
        return mapping.get(plaid_type, BankAccountType.OTHER)

    def _map_category(self, categories: list) -> TransactionCategory:
        """Mappe les catégories Plaid."""
        if not categories:
            return TransactionCategory.OTHER

        primary = categories[0].lower() if categories else ""

        mapping = {
            "income": TransactionCategory.INCOME,
            "transfer": TransactionCategory.TRANSFER,
            "food and drink": TransactionCategory.FOOD,
            "shops": TransactionCategory.SHOPPING,
            "travel": TransactionCategory.TRANSPORT,
            "payment": TransactionCategory.OTHER,
            "healthcare": TransactionCategory.HEALTH,
            "service": TransactionCategory.OTHER,
        }

        return mapping.get(primary, TransactionCategory.OTHER)


# ============================================================================
# REGISTRE DES PROVIDERS
# ============================================================================

class BankProviderRegistry:
    """Registre des providers bancaires disponibles."""

    _providers: dict[str, BankProvider] = {}

    @classmethod
    def register(cls, provider: BankProvider):
        """Enregistre un provider."""
        cls._providers[provider.provider_name] = provider
        logger.info(f"Provider bancaire enregistré: {provider.provider_name}")

    @classmethod
    def get(cls, name: str) -> Optional[BankProvider]:
        """Récupère un provider par nom."""
        return cls._providers.get(name)

    @classmethod
    def list_providers(cls) -> list[str]:
        """Liste les providers disponibles."""
        return list(cls._providers.keys())

    @classmethod
    def get_provider_for_country(cls, country: str) -> list[BankProvider]:
        """Récupère les providers supportant un pays."""
        return [
            p for p in cls._providers.values()
            if country in p.supported_countries
        ]
