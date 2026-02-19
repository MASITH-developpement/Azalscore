"""
AZALSCORE Solaris Bank Provider
===============================

Provider pour l'intégration avec Solaris Bank (Banking-as-a-Service).
Gère les comptes bancaires, overdrafts, et services de crédit B2B.

Solaris Bank est une plateforme BaaS allemande spécialisée dans:
- Comptes courants (DE, FR, IT, ES IBANs)
- Overdrafts business
- Cartes de débit
- Services de crédit

Usage:
    from app.modules.finance.providers import SolarisProvider

    provider = SolarisProvider(
        tenant_id="tenant-123",
        client_id="your_client_id",
        client_secret="your_client_secret",
        sandbox=True,
    )

    # Créer une demande d'overdraft
    result = await provider.create_overdraft_application(
        business_id="bus_123",
        account_iban="DE89370400440532013000",
        requested_limit_cents=5000000,
    )
"""

import hashlib
import hmac
import logging
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field, field_validator

from .base import (
    BaseFinanceProvider,
    FinanceError,
    FinanceErrorCode,
    FinanceProviderType,
    FinanceResult,
    WebhookEvent,
    WebhookEventType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS SOLARIS
# =============================================================================


class SolarisAccountStatus(str, Enum):
    """Statuts d'un compte Solaris."""

    ACTIVE = "active"
    BLOCKED = "blocked"
    CLOSED = "closed"
    PENDING = "pending"


class SolarisAccountType(str, Enum):
    """Types de comptes Solaris."""

    CURRENT = "current"
    SAVINGS = "savings"


class SolarisOverdraftStatus(str, Enum):
    """Statuts d'une application overdraft."""

    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SolarisBusinessType(str, Enum):
    """Types d'entreprises Solaris."""

    SOLE_PROPRIETOR = "sole_proprietor"
    FREELANCER = "freelancer"
    LIMITED_COMPANY = "limited_company"
    PARTNERSHIP = "partnership"
    OTHER = "other"


class SolarisCountry(str, Enum):
    """Pays supportés pour les IBANs."""

    DE = "DE"  # Allemagne
    FR = "FR"  # France
    IT = "IT"  # Italie
    ES = "ES"  # Espagne


# =============================================================================
# SCHEMAS PYDANTIC - REQUESTS
# =============================================================================


class SolarisBusinessRequest(BaseModel):
    """Requête de création d'entreprise Solaris."""

    # Identité
    name: str = Field(..., min_length=2, max_length=200)
    legal_form: SolarisBusinessType = Field(...)
    registration_number: str = Field(..., max_length=50)
    tax_id: Optional[str] = Field(default=None, max_length=20)

    # Adresse
    address_line1: str = Field(..., max_length=200)
    address_city: str = Field(..., max_length=100)
    address_postal_code: str = Field(..., max_length=20)
    address_country: SolarisCountry = Field(default=SolarisCountry.DE)

    # Contact
    contact_email: str = Field(..., max_length=100)
    contact_phone: Optional[str] = Field(default=None, max_length=20)

    # Données financières
    annual_revenue_cents: Optional[int] = Field(default=None, ge=0)
    industry_code: Optional[str] = Field(default=None, max_length=10)


class SolarisAccountRequest(BaseModel):
    """Requête de création de compte Solaris."""

    business_id: str = Field(..., description="ID de l'entreprise")
    account_type: SolarisAccountType = Field(default=SolarisAccountType.CURRENT)
    currency: str = Field(default="EUR", pattern=r"^[A-Z]{3}$")
    iban_country: SolarisCountry = Field(default=SolarisCountry.DE)

    # Référence externe
    external_reference: Optional[str] = Field(default=None, max_length=100)


class SolarisOverdraftApplicationRequest(BaseModel):
    """Requête de demande d'overdraft Solaris."""

    business_id: str = Field(..., description="ID de l'entreprise")
    account_iban: str = Field(..., max_length=34)

    # Montant demandé (en centimes)
    requested_limit_cents: int = Field(..., gt=0, le=50000000)  # Max 500k EUR
    currency: str = Field(default="EUR", pattern=r"^[A-Z]{3}$")

    # Justification
    purpose: Optional[str] = Field(default=None, max_length=500)

    # Documents KYC
    identification_id: Optional[str] = Field(default=None)

    @field_validator("account_iban")
    @classmethod
    def validate_iban(cls, v: str) -> str:
        """Valide et nettoie l'IBAN."""
        cleaned = v.replace(" ", "").replace("-", "").upper()
        if len(cleaned) < 15 or len(cleaned) > 34:
            raise ValueError("IBAN invalide")
        return cleaned


class SolarisTransferRequest(BaseModel):
    """Requête de virement SEPA Solaris."""

    # Compte source
    account_id: str = Field(...)

    # Montant
    amount_cents: int = Field(..., gt=0)
    currency: str = Field(default="EUR", pattern=r"^[A-Z]{3}$")

    # Bénéficiaire
    recipient_name: str = Field(..., min_length=2, max_length=100)
    recipient_iban: str = Field(..., max_length=34)
    recipient_bic: Optional[str] = Field(default=None, max_length=11)

    # Référence
    reference: Optional[str] = Field(default=None, max_length=140)
    end_to_end_id: Optional[str] = Field(default=None, max_length=35)

    @field_validator("recipient_iban")
    @classmethod
    def validate_recipient_iban(cls, v: str) -> str:
        """Valide et nettoie l'IBAN du bénéficiaire."""
        cleaned = v.replace(" ", "").replace("-", "").upper()
        if len(cleaned) < 15 or len(cleaned) > 34:
            raise ValueError("IBAN bénéficiaire invalide")
        return cleaned


# =============================================================================
# SCHEMAS PYDANTIC - RESPONSES
# =============================================================================


class SolarisBusinessResponse(BaseModel):
    """Réponse entreprise Solaris."""

    id: str
    name: str
    legal_form: SolarisBusinessType
    registration_number: str

    # Adresse
    address_line1: str
    address_city: str
    address_postal_code: str
    address_country: str

    # Statut
    status: str

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None


class SolarisAccountResponse(BaseModel):
    """Réponse compte Solaris."""

    id: str
    business_id: str
    iban: str
    bic: str
    account_type: SolarisAccountType
    status: SolarisAccountStatus

    # Soldes (en centimes)
    balance_cents: int
    available_balance_cents: int
    currency: str

    # Overdraft
    overdraft_limit_cents: Optional[int] = None
    overdraft_used_cents: Optional[int] = None

    # Timestamps
    created_at: datetime
    closed_at: Optional[datetime] = None


class SolarisOverdraftResponse(BaseModel):
    """Réponse overdraft Solaris."""

    id: str
    business_id: str
    account_iban: str
    status: SolarisOverdraftStatus

    # Montants
    requested_limit_cents: int
    approved_limit_cents: Optional[int] = None
    used_amount_cents: int = 0
    currency: str

    # Conditions
    interest_rate: Optional[Decimal] = None
    fee_cents: Optional[int] = None

    # Dates
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None

    # Timestamps
    created_at: datetime
    approved_at: Optional[datetime] = None


class SolarisTransferResponse(BaseModel):
    """Réponse virement Solaris."""

    id: str
    account_id: str
    status: str

    # Montant
    amount_cents: int
    currency: str

    # Bénéficiaire
    recipient_name: str
    recipient_iban: str

    # Référence
    reference: Optional[str] = None
    end_to_end_id: Optional[str] = None

    # Timestamps
    created_at: datetime
    executed_at: Optional[datetime] = None


# =============================================================================
# SOLARIS PROVIDER
# =============================================================================


class SolarisProvider(BaseFinanceProvider):
    """
    Provider pour Solaris Bank (Banking-as-a-Service).

    Fonctionnalités:
    - Gestion des entreprises (onboarding B2B)
    - Comptes courants multi-pays
    - Overdrafts business
    - Virements SEPA
    - Webhooks temps réel

    Configuration:
        client_id: Client ID OAuth2
        client_secret: Client Secret OAuth2 (utilisé comme api_key)
        sandbox: True pour environnement de test
    """

    PROVIDER_NAME = "solaris"
    PROVIDER_TYPE = FinanceProviderType.SOLARIS

    # URLs Solaris
    SANDBOX_URL = "https://api.sandbox.solaris-sandbox.de"
    PRODUCTION_URL = "https://api.solaris.de"

    # OAuth2
    TOKEN_ENDPOINT = "/oauth/token"

    def __init__(
        self,
        tenant_id: str,
        api_key: Optional[str] = None,  # client_secret
        client_id: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        sandbox: bool = True,
    ):
        """
        Initialise le provider Solaris.

        Args:
            tenant_id: ID du tenant (OBLIGATOIRE)
            api_key: Client Secret OAuth2
            client_id: Client ID OAuth2
            webhook_secret: Secret pour vérification webhooks
            sandbox: Mode sandbox (défaut: True)
        """
        super().__init__(
            tenant_id=tenant_id,
            api_key=api_key,  # client_secret
            sandbox=sandbox,
        )

        self.client_id = client_id
        self.webhook_secret = webhook_secret
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

        # URL selon l'environnement
        self.BASE_URL = self.SANDBOX_URL if sandbox else self.PRODUCTION_URL

        self._logger.info(
            f"SolarisProvider initialisé",
            extra={"sandbox": sandbox, "has_client_id": bool(client_id)},
        )

    def _get_default_headers(self) -> dict[str, str]:
        """Retourne les headers par défaut pour Solaris."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"AZALSCORE/{self.PROVIDER_NAME}",
            "X-Tenant-ID": self.tenant_id,
        }

        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        return headers

    async def _ensure_token(self) -> bool:
        """
        S'assure qu'un token OAuth2 valide est disponible.

        Returns:
            True si token valide, False sinon
        """
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at:
                return True

        if not self.client_id or not self.api_key:
            self._logger.error("client_id et api_key requis pour OAuth2")
            return False

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.BASE_URL}{self.TOKEN_ENDPOINT}",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.api_key,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                data = response.json()
                self._access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                self._token_expires_at = datetime.utcnow() + \
                    __import__("datetime").timedelta(seconds=expires_in - 60)
                return True
            else:
                self._logger.error(f"Échec obtention token: {response.status_code}")
                return False

        except Exception as e:
            self._logger.error(f"Erreur OAuth2: {e}")
            return False

    # =========================================================================
    # ENTREPRISES (BUSINESSES)
    # =========================================================================

    async def create_business(
        self,
        name: str,
        legal_form: SolarisBusinessType,
        registration_number: str,
        address_line1: str,
        address_city: str,
        address_postal_code: str,
        contact_email: str,
        address_country: SolarisCountry = SolarisCountry.DE,
        tax_id: Optional[str] = None,
        contact_phone: Optional[str] = None,
        annual_revenue_cents: Optional[int] = None,
        industry_code: Optional[str] = None,
    ) -> FinanceResult[SolarisBusinessResponse]:
        """
        Crée une nouvelle entreprise (onboarding B2B).

        Args:
            name: Nom de l'entreprise
            legal_form: Forme juridique
            registration_number: Numéro d'immatriculation
            address_*: Adresse
            contact_email: Email de contact
            tax_id: Numéro TVA
            contact_phone: Téléphone
            annual_revenue_cents: CA annuel en centimes
            industry_code: Code NAF/NACE

        Returns:
            FinanceResult avec les données de l'entreprise
        """
        try:
            request = SolarisBusinessRequest(
                name=name,
                legal_form=legal_form,
                registration_number=registration_number,
                address_line1=address_line1,
                address_city=address_city,
                address_postal_code=address_postal_code,
                address_country=address_country,
                contact_email=contact_email,
                tax_id=tax_id,
                contact_phone=contact_phone,
                annual_revenue_cents=annual_revenue_cents,
                industry_code=industry_code,
            )
        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_REQUEST,
                    message=str(e),
                ),
                provider=self.PROVIDER_NAME,
            )

        if not await self._ensure_token():
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_API_KEY,
                    message="Échec authentification OAuth2",
                ),
                provider=self.PROVIDER_NAME,
            )

        return await self._request(
            method="POST",
            endpoint="/v1/businesses",
            json_data=request.model_dump(exclude_none=True),
        )

    async def get_business(
        self,
        business_id: str,
    ) -> FinanceResult[SolarisBusinessResponse]:
        """
        Récupère les informations d'une entreprise.

        Args:
            business_id: ID de l'entreprise

        Returns:
            FinanceResult avec les données de l'entreprise
        """
        if not await self._ensure_token():
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_API_KEY,
                    message="Échec authentification OAuth2",
                ),
                provider=self.PROVIDER_NAME,
            )

        return await self._request(
            method="GET",
            endpoint=f"/v1/businesses/{business_id}",
        )

    # =========================================================================
    # COMPTES (ACCOUNTS)
    # =========================================================================

    async def create_account(
        self,
        business_id: str,
        account_type: SolarisAccountType = SolarisAccountType.CURRENT,
        currency: str = "EUR",
        iban_country: SolarisCountry = SolarisCountry.DE,
        external_reference: Optional[str] = None,
    ) -> FinanceResult[SolarisAccountResponse]:
        """
        Crée un compte bancaire pour une entreprise.

        Args:
            business_id: ID de l'entreprise
            account_type: Type de compte
            currency: Devise
            iban_country: Pays de l'IBAN (DE, FR, IT, ES)
            external_reference: Référence externe

        Returns:
            FinanceResult avec les données du compte
        """
        try:
            request = SolarisAccountRequest(
                business_id=business_id,
                account_type=account_type,
                currency=currency,
                iban_country=iban_country,
                external_reference=external_reference,
            )
        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_REQUEST,
                    message=str(e),
                ),
                provider=self.PROVIDER_NAME,
            )

        if not await self._ensure_token():
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_API_KEY,
                    message="Échec authentification OAuth2",
                ),
                provider=self.PROVIDER_NAME,
            )

        return await self._request(
            method="POST",
            endpoint="/v1/accounts",
            json_data=request.model_dump(exclude_none=True),
        )

    async def get_account(
        self,
        account_id: str,
    ) -> FinanceResult[SolarisAccountResponse]:
        """
        Récupère les informations d'un compte.

        Args:
            account_id: ID du compte

        Returns:
            FinanceResult avec les données du compte
        """
        if not await self._ensure_token():
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_API_KEY,
                    message="Échec authentification OAuth2",
                ),
                provider=self.PROVIDER_NAME,
            )

        return await self._request(
            method="GET",
            endpoint=f"/v1/accounts/{account_id}",
        )

    async def get_accounts(
        self,
        business_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> FinanceResult[list[SolarisAccountResponse]]:
        """
        Liste les comptes d'une entreprise.

        Args:
            business_id: ID de l'entreprise
            limit: Nombre max de résultats
            offset: Décalage

        Returns:
            FinanceResult avec la liste des comptes
        """
        if not await self._ensure_token():
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_API_KEY,
                    message="Échec authentification OAuth2",
                ),
                provider=self.PROVIDER_NAME,
            )

        return await self._request(
            method="GET",
            endpoint="/v1/accounts",
            params={
                "business_id": business_id,
                "page[size]": limit,
                "page[number]": offset // limit if limit > 0 else 0,
            },
        )

    async def get_account_balance(
        self,
        account_id: str,
    ) -> FinanceResult[dict]:
        """
        Récupère le solde d'un compte.

        Args:
            account_id: ID du compte

        Returns:
            FinanceResult avec les soldes
        """
        result = await self.get_account(account_id)
        if not result.success:
            return result

        account = result.data
        return FinanceResult.ok(
            data={
                "account_id": account_id,
                "balance_cents": account.get("balance_cents", 0) if isinstance(account, dict) else 0,
                "available_balance_cents": account.get("available_balance_cents", 0) if isinstance(account, dict) else 0,
                "currency": account.get("currency", "EUR") if isinstance(account, dict) else "EUR",
                "overdraft_limit_cents": account.get("overdraft_limit_cents") if isinstance(account, dict) else None,
                "overdraft_used_cents": account.get("overdraft_used_cents") if isinstance(account, dict) else None,
            },
            provider=self.PROVIDER_NAME,
        )

    # =========================================================================
    # OVERDRAFTS
    # =========================================================================

    async def create_overdraft_application(
        self,
        business_id: str,
        account_iban: str,
        requested_limit_cents: int,
        currency: str = "EUR",
        purpose: Optional[str] = None,
        identification_id: Optional[str] = None,
    ) -> FinanceResult[SolarisOverdraftResponse]:
        """
        Crée une demande d'overdraft.

        Args:
            business_id: ID de l'entreprise
            account_iban: IBAN du compte
            requested_limit_cents: Limite demandée en centimes
            currency: Devise
            purpose: Motif de la demande
            identification_id: ID de vérification KYC

        Returns:
            FinanceResult avec les données de l'overdraft
        """
        try:
            request = SolarisOverdraftApplicationRequest(
                business_id=business_id,
                account_iban=account_iban,
                requested_limit_cents=requested_limit_cents,
                currency=currency,
                purpose=purpose,
                identification_id=identification_id,
            )
        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_REQUEST,
                    message=str(e),
                ),
                provider=self.PROVIDER_NAME,
            )

        if not await self._ensure_token():
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_API_KEY,
                    message="Échec authentification OAuth2",
                ),
                provider=self.PROVIDER_NAME,
            )

        return await self._request(
            method="POST",
            endpoint="/v1/overdraft_applications",
            json_data=request.model_dump(exclude_none=True),
        )

    async def get_overdraft(
        self,
        overdraft_id: str,
    ) -> FinanceResult[SolarisOverdraftResponse]:
        """
        Récupère les détails d'un overdraft.

        Args:
            overdraft_id: ID de l'overdraft

        Returns:
            FinanceResult avec les données de l'overdraft
        """
        if not await self._ensure_token():
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_API_KEY,
                    message="Échec authentification OAuth2",
                ),
                provider=self.PROVIDER_NAME,
            )

        return await self._request(
            method="GET",
            endpoint=f"/v1/overdraft_applications/{overdraft_id}",
        )

    async def get_overdrafts(
        self,
        business_id: str,
        status: Optional[SolarisOverdraftStatus] = None,
    ) -> FinanceResult[list[SolarisOverdraftResponse]]:
        """
        Liste les overdrafts d'une entreprise.

        Args:
            business_id: ID de l'entreprise
            status: Filtrer par statut

        Returns:
            FinanceResult avec la liste des overdrafts
        """
        if not await self._ensure_token():
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_API_KEY,
                    message="Échec authentification OAuth2",
                ),
                provider=self.PROVIDER_NAME,
            )

        params = {"business_id": business_id}
        if status:
            params["status"] = status.value

        return await self._request(
            method="GET",
            endpoint="/v1/overdraft_applications",
            params=params,
        )

    # =========================================================================
    # VIREMENTS (TRANSFERS)
    # =========================================================================

    async def create_transfer(
        self,
        account_id: str,
        amount_cents: int,
        recipient_name: str,
        recipient_iban: str,
        currency: str = "EUR",
        recipient_bic: Optional[str] = None,
        reference: Optional[str] = None,
        end_to_end_id: Optional[str] = None,
    ) -> FinanceResult[SolarisTransferResponse]:
        """
        Crée un virement SEPA.

        Args:
            account_id: ID du compte source
            amount_cents: Montant en centimes
            recipient_name: Nom du bénéficiaire
            recipient_iban: IBAN du bénéficiaire
            currency: Devise
            recipient_bic: BIC du bénéficiaire
            reference: Référence/motif
            end_to_end_id: ID de bout en bout

        Returns:
            FinanceResult avec les données du virement
        """
        try:
            request = SolarisTransferRequest(
                account_id=account_id,
                amount_cents=amount_cents,
                recipient_name=recipient_name,
                recipient_iban=recipient_iban,
                currency=currency,
                recipient_bic=recipient_bic,
                reference=reference,
                end_to_end_id=end_to_end_id,
            )
        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_REQUEST,
                    message=str(e),
                ),
                provider=self.PROVIDER_NAME,
            )

        if not await self._ensure_token():
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_API_KEY,
                    message="Échec authentification OAuth2",
                ),
                provider=self.PROVIDER_NAME,
            )

        return await self._request(
            method="POST",
            endpoint="/v1/sepa_credit_transfers",
            json_data=request.model_dump(exclude_none=True),
        )

    async def get_transfer(
        self,
        transfer_id: str,
    ) -> FinanceResult[SolarisTransferResponse]:
        """
        Récupère les détails d'un virement.

        Args:
            transfer_id: ID du virement

        Returns:
            FinanceResult avec les données du virement
        """
        if not await self._ensure_token():
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_API_KEY,
                    message="Échec authentification OAuth2",
                ),
                provider=self.PROVIDER_NAME,
            )

        return await self._request(
            method="GET",
            endpoint=f"/v1/sepa_credit_transfers/{transfer_id}",
        )

    # =========================================================================
    # WEBHOOKS
    # =========================================================================

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """
        Vérifie la signature d'un webhook Solaris.

        Args:
            payload: Corps brut de la requête
            signature: Signature du header X-Solaris-Signature

        Returns:
            True si signature valide
        """
        if not self.webhook_secret:
            self._logger.warning("Pas de webhook_secret configuré")
            return False

        try:
            expected = hmac.new(
                self.webhook_secret.encode(),
                payload,
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(expected, signature)

        except Exception as e:
            self._logger.error(f"Erreur vérification webhook: {e}")
            return False

    def parse_webhook_event(self, payload: dict) -> WebhookEvent:
        """
        Parse un événement webhook Solaris.

        Args:
            payload: Données du webhook

        Returns:
            WebhookEvent normalisé
        """
        # Mapping des types d'événements Solaris
        event_type_mapping = {
            "account.created": WebhookEventType.ACCOUNT_CREATED,
            "account.updated": WebhookEventType.ACCOUNT_UPDATED,
            "account.blocked": WebhookEventType.ACCOUNT_UPDATED,
            "account.closed": WebhookEventType.ACCOUNT_CLOSED,
            "overdraft.approved": WebhookEventType.PAYMENT_AUTHORIZED,
            "overdraft.rejected": WebhookEventType.TRANSACTION_FAILED,
            "overdraft.activated": WebhookEventType.PAYMENT_CAPTURED,
            "overdraft.expired": WebhookEventType.TRANSACTION_FAILED,
            "transfer.created": WebhookEventType.TRANSACTION_CREATED,
            "transfer.executed": WebhookEventType.TRANSACTION_COMPLETED,
            "transfer.failed": WebhookEventType.TRANSACTION_FAILED,
            "booking.created": WebhookEventType.TRANSACTION_CREATED,
        }

        solaris_event_type = payload.get("event_type", payload.get("type", ""))
        event_type = event_type_mapping.get(
            solaris_event_type, WebhookEventType.TRANSACTION_CREATED
        )

        # Parse timestamp
        timestamp_str = payload.get("timestamp", datetime.utcnow().isoformat())
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1] + "+00:00"

        return WebhookEvent(
            id=payload.get("event_id", payload.get("id", "")),
            type=event_type,
            provider=FinanceProviderType.SOLARIS,
            tenant_id=self.tenant_id,
            payload=payload.get("data", payload),
            raw_payload=str(payload),
            timestamp=datetime.fromisoformat(timestamp_str),
        )

    # =========================================================================
    # BASE CLASS IMPLEMENTATIONS
    # =========================================================================

    async def health_check(self) -> FinanceResult[dict]:
        """
        Vérifie que le provider est fonctionnel.

        Returns:
            FinanceResult avec le statut
        """
        try:
            # Tente d'obtenir un token OAuth2
            if await self._ensure_token():
                return FinanceResult.ok(
                    data={
                        "status": "healthy",
                        "provider": self.PROVIDER_NAME,
                        "sandbox": self.sandbox,
                        "authenticated": True,
                    },
                    provider=self.PROVIDER_NAME,
                )
            else:
                return FinanceResult.ok(
                    data={
                        "status": "degraded",
                        "provider": self.PROVIDER_NAME,
                        "sandbox": self.sandbox,
                        "authenticated": False,
                        "message": "OAuth2 authentication failed",
                    },
                    provider=self.PROVIDER_NAME,
                )

        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.CONNECTION_ERROR,
                    message=str(e),
                ),
                provider=self.PROVIDER_NAME,
            )

    async def get_account_info(self) -> FinanceResult[dict]:
        """
        Récupère les informations du compte Solaris.

        Returns:
            FinanceResult avec les infos du compte
        """
        return FinanceResult.ok(
            data={
                "provider": self.PROVIDER_NAME,
                "sandbox": self.sandbox,
                "tenant_id": self.tenant_id,
                "has_client_id": bool(self.client_id),
                "has_client_secret": bool(self.api_key),
                "has_webhook_secret": bool(self.webhook_secret),
                "base_url": self.BASE_URL,
                "authenticated": bool(self._access_token),
            },
            provider=self.PROVIDER_NAME,
        )
