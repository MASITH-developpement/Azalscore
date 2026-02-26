"""
AZALSCORE NMI Payment Provider
==============================

Provider pour l'intégration avec NMI (Network Merchants Inc) Payment Gateway.
Gère les paiements par carte, les remboursements, et les webhooks.

NMI est un gateway de paiement US utilisé pour:
- Transactions par carte (sale, auth, capture, void, refund)
- Paiements ACH
- Tokenisation (Customer Vault)
- Webhooks temps réel

Usage:
    from app.modules.finance.providers import NMIProvider

    provider = NMIProvider(
        tenant_id="tenant-123",
        api_key="your_security_key",
        sandbox=True,
    )

    # Traiter un paiement
    result = await provider.process_payment(
        amount=5000,  # 50.00 EUR en centimes
        card_number="4111111111111111",
        exp_month="12",
        exp_year="2025",
        cvv="123",
    )
"""

import hashlib
import hmac
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from urllib.parse import parse_qs

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
# ENUMS NMI
# =============================================================================


class NMITransactionType(str, Enum):
    """Types de transactions NMI."""

    SALE = "sale"  # Autorisation + capture immédiate
    AUTH = "auth"  # Autorisation seule
    CAPTURE = "capture"  # Capture d'une auth
    VOID = "void"  # Annulation
    REFUND = "refund"  # Remboursement
    CREDIT = "credit"  # Crédit sans transaction originale
    VALIDATE = "validate"  # Validation carte sans charge


class NMIPaymentType(str, Enum):
    """Types de paiement NMI."""

    CREDITCARD = "creditcard"
    CHECK = "check"  # ACH


class NMIResponseCode(int, Enum):
    """Codes de réponse NMI."""

    APPROVED = 1
    DECLINED = 2
    ERROR = 3


class NMIAVSResponse(str, Enum):
    """Réponses AVS (Address Verification System)."""

    MATCH = "Y"  # Address and ZIP match
    ADDRESS_MATCH = "A"  # Address match, ZIP no match
    ZIP_MATCH = "Z"  # ZIP match, address no match
    NO_MATCH = "N"  # No match
    NOT_AVAILABLE = "U"  # AVS not available
    NOT_SUPPORTED = "S"  # AVS not supported


class NMICVVResponse(str, Enum):
    """Réponses CVV."""

    MATCH = "M"
    NO_MATCH = "N"
    NOT_PROCESSED = "P"
    NOT_PRESENT = "S"
    UNAVAILABLE = "U"


# =============================================================================
# SCHEMAS PYDANTIC - REQUESTS
# =============================================================================


class NMIPaymentRequest(BaseModel):
    """Requête de paiement NMI."""

    # Montant en centimes
    amount: int = Field(..., gt=0, description="Montant en centimes")
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")

    # Carte
    card_number: str = Field(..., min_length=13, max_length=19)
    exp_month: str = Field(..., pattern=r"^\d{2}$")
    exp_year: str = Field(..., pattern=r"^\d{2,4}$")
    cvv: Optional[str] = Field(default=None, pattern=r"^\d{3,4}$")

    # Référence
    order_id: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, max_length=255)

    # Billing
    billing_first_name: Optional[str] = Field(default=None, max_length=50)
    billing_last_name: Optional[str] = Field(default=None, max_length=50)
    billing_address: Optional[str] = Field(default=None, max_length=100)
    billing_city: Optional[str] = Field(default=None, max_length=50)
    billing_state: Optional[str] = Field(default=None, max_length=50)
    billing_zip: Optional[str] = Field(default=None, max_length=20)
    billing_country: Optional[str] = Field(default=None, max_length=2)
    billing_email: Optional[str] = Field(default=None, max_length=100)
    billing_phone: Optional[str] = Field(default=None, max_length=20)

    @field_validator("card_number")
    @classmethod
    def validate_card_number(cls, v: str) -> str:
        """Valide et nettoie le numéro de carte."""
        # Retirer espaces et tirets
        cleaned = v.replace(" ", "").replace("-", "")

        if not cleaned.isdigit():
            raise ValueError("Le numéro de carte doit contenir uniquement des chiffres")

        if len(cleaned) < 13 or len(cleaned) > 19:
            raise ValueError("Numéro de carte invalide")

        # Validation Luhn
        if not cls._luhn_check(cleaned):
            raise ValueError("Numéro de carte invalide (checksum)")

        return cleaned

    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        """Algorithme de Luhn pour validation carte."""
        digits = [int(d) for d in card_number]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(divmod(d * 2, 10))
        return checksum % 10 == 0

    @field_validator("exp_year")
    @classmethod
    def normalize_exp_year(cls, v: str) -> str:
        """Normalise l'année d'expiration (2 digits)."""
        if len(v) == 4:
            return v[2:]
        return v


class NMIRefundRequest(BaseModel):
    """Requête de remboursement NMI."""

    transaction_id: str = Field(..., description="ID transaction originale")
    amount: Optional[int] = Field(
        default=None, gt=0, description="Montant partiel en centimes (None = total)"
    )
    reason: Optional[str] = Field(default=None, max_length=255)


class NMICaptureRequest(BaseModel):
    """Requête de capture NMI."""

    transaction_id: str = Field(..., description="ID de l'autorisation")
    amount: Optional[int] = Field(
        default=None, gt=0, description="Montant à capturer (None = montant original)"
    )


class NMIVoidRequest(BaseModel):
    """Requête d'annulation NMI."""

    transaction_id: str = Field(..., description="ID transaction à annuler")


class NMICustomerVaultRequest(BaseModel):
    """Requête pour Customer Vault (tokenisation)."""

    # Carte
    card_number: str = Field(..., min_length=13, max_length=19)
    exp_month: str = Field(..., pattern=r"^\d{2}$")
    exp_year: str = Field(..., pattern=r"^\d{2,4}$")

    # Client
    customer_id: Optional[str] = Field(default=None, max_length=50)
    first_name: Optional[str] = Field(default=None, max_length=50)
    last_name: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)


# =============================================================================
# SCHEMAS PYDANTIC - RESPONSES
# =============================================================================


class NMITransactionResponse(BaseModel):
    """Réponse de transaction NMI."""

    transaction_id: str
    response_code: int
    response_text: str
    auth_code: Optional[str] = None
    avs_response: Optional[str] = None
    cvv_response: Optional[str] = None

    # Montants
    amount: Decimal
    currency: str = "USD"

    # Card info
    card_type: Optional[str] = None
    card_last_four: Optional[str] = None

    # Metadata
    order_id: Optional[str] = None
    processor_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_approved(self) -> bool:
        """Transaction approuvée."""
        return self.response_code == NMIResponseCode.APPROVED

    @property
    def is_declined(self) -> bool:
        """Transaction refusée."""
        return self.response_code == NMIResponseCode.DECLINED


class NMIVaultResponse(BaseModel):
    """Réponse Customer Vault."""

    customer_vault_id: str
    response_code: int
    response_text: str
    card_type: Optional[str] = None
    card_last_four: Optional[str] = None


# =============================================================================
# NMI PROVIDER
# =============================================================================


class NMIProvider(BaseFinanceProvider):
    """
    Provider pour NMI Payment Gateway.

    Fonctionnalités:
    - Paiements par carte (sale, auth, capture)
    - Remboursements et annulations
    - Customer Vault (tokenisation)
    - Webhooks temps réel
    - Mode sandbox pour tests

    Configuration:
        api_key: Security Key du compte NMI
        sandbox: True pour environnement de test
    """

    PROVIDER_NAME = "nmi"
    PROVIDER_TYPE = FinanceProviderType.NMI

    # URLs NMI
    SANDBOX_URL = "https://sandbox.nmi.com/api/transact.php"
    PRODUCTION_URL = "https://secure.networkmerchants.com/api/transact.php"

    QUERY_SANDBOX_URL = "https://sandbox.nmi.com/api/query.php"
    QUERY_PRODUCTION_URL = "https://secure.networkmerchants.com/api/query.php"

    def __init__(
        self,
        tenant_id: str,
        api_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        sandbox: bool = True,
    ):
        """
        Initialise le provider NMI.

        Args:
            tenant_id: ID du tenant (OBLIGATOIRE)
            api_key: Security Key NMI
            webhook_secret: Secret pour vérification webhooks
            sandbox: Mode sandbox (défaut: True)
        """
        super().__init__(
            tenant_id=tenant_id,
            api_key=api_key,
            sandbox=sandbox,
        )

        self.webhook_secret = webhook_secret

        # URL selon l'environnement
        self.BASE_URL = self.SANDBOX_URL if sandbox else self.PRODUCTION_URL
        self.QUERY_URL = self.QUERY_SANDBOX_URL if sandbox else self.QUERY_PRODUCTION_URL

        self._logger.info(
            f"NMIProvider initialisé",
            extra={"sandbox": sandbox, "has_webhook_secret": bool(webhook_secret)},
        )

    # =========================================================================
    # TRANSACTIONS
    # =========================================================================

    async def process_payment(
        self,
        amount: int,
        card_number: str,
        exp_month: str,
        exp_year: str,
        cvv: Optional[str] = None,
        currency: str = "USD",
        order_id: Optional[str] = None,
        description: Optional[str] = None,
        billing_first_name: Optional[str] = None,
        billing_last_name: Optional[str] = None,
        billing_address: Optional[str] = None,
        billing_city: Optional[str] = None,
        billing_state: Optional[str] = None,
        billing_zip: Optional[str] = None,
        billing_country: Optional[str] = None,
        billing_email: Optional[str] = None,
    ) -> FinanceResult[NMITransactionResponse]:
        """
        Traite un paiement par carte (sale = auth + capture).

        Args:
            amount: Montant en centimes
            card_number: Numéro de carte
            exp_month: Mois d'expiration (MM)
            exp_year: Année d'expiration (YY ou YYYY)
            cvv: Code CVV
            currency: Devise (défaut: USD)
            order_id: ID de commande externe
            description: Description du paiement
            billing_*: Informations de facturation

        Returns:
            FinanceResult avec la réponse de transaction
        """
        # Valider la requête
        try:
            request = NMIPaymentRequest(
                amount=amount,
                currency=currency,
                card_number=card_number,
                exp_month=exp_month,
                exp_year=exp_year,
                cvv=cvv,
                order_id=order_id,
                description=description,
                billing_first_name=billing_first_name,
                billing_last_name=billing_last_name,
                billing_address=billing_address,
                billing_city=billing_city,
                billing_state=billing_state,
                billing_zip=billing_zip,
                billing_country=billing_country,
                billing_email=billing_email,
            )
        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_REQUEST,
                    message=str(e),
                ),
                provider=self.PROVIDER_NAME,
            )

        return await self._execute_transaction(NMITransactionType.SALE, request)

    async def authorize(
        self,
        amount: int,
        card_number: str,
        exp_month: str,
        exp_year: str,
        cvv: Optional[str] = None,
        **kwargs,
    ) -> FinanceResult[NMITransactionResponse]:
        """
        Autorisation seule (sans capture).

        Utile pour les réservations où le montant final peut varier.
        La capture doit être faite séparément.

        Args:
            amount: Montant en centimes
            card_number: Numéro de carte
            exp_month: Mois d'expiration
            exp_year: Année d'expiration
            cvv: Code CVV
            **kwargs: Autres paramètres (billing_*, order_id, etc.)

        Returns:
            FinanceResult avec la réponse (contient transaction_id pour capture)
        """
        try:
            request = NMIPaymentRequest(
                amount=amount,
                card_number=card_number,
                exp_month=exp_month,
                exp_year=exp_year,
                cvv=cvv,
                **kwargs,
            )
        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_REQUEST,
                    message=str(e),
                ),
                provider=self.PROVIDER_NAME,
            )

        return await self._execute_transaction(NMITransactionType.AUTH, request)

    async def capture(
        self,
        transaction_id: str,
        amount: Optional[int] = None,
    ) -> FinanceResult[NMITransactionResponse]:
        """
        Capture une autorisation existante.

        Args:
            transaction_id: ID de l'autorisation
            amount: Montant à capturer (None = montant original)

        Returns:
            FinanceResult avec la réponse de capture
        """
        try:
            request = NMICaptureRequest(
                transaction_id=transaction_id,
                amount=amount,
            )
        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_REQUEST,
                    message=str(e),
                ),
                provider=self.PROVIDER_NAME,
            )

        # Préparer les données
        data = {
            "security_key": self.api_key,
            "type": NMITransactionType.CAPTURE.value,
            "transactionid": request.transaction_id,
        }

        if request.amount:
            data["amount"] = f"{request.amount / 100:.2f}"

        return await self._post_transaction(data)

    async def void(
        self,
        transaction_id: str,
    ) -> FinanceResult[NMITransactionResponse]:
        """
        Annule une transaction (avant règlement).

        Args:
            transaction_id: ID de la transaction à annuler

        Returns:
            FinanceResult avec la réponse d'annulation
        """
        data = {
            "security_key": self.api_key,
            "type": NMITransactionType.VOID.value,
            "transactionid": transaction_id,
        }

        return await self._post_transaction(data)

    async def refund(
        self,
        transaction_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> FinanceResult[NMITransactionResponse]:
        """
        Rembourse une transaction (après règlement).

        Args:
            transaction_id: ID de la transaction originale
            amount: Montant à rembourser (None = total)
            reason: Raison du remboursement

        Returns:
            FinanceResult avec la réponse de remboursement
        """
        try:
            request = NMIRefundRequest(
                transaction_id=transaction_id,
                amount=amount,
                reason=reason,
            )
        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_REQUEST,
                    message=str(e),
                ),
                provider=self.PROVIDER_NAME,
            )

        data = {
            "security_key": self.api_key,
            "type": NMITransactionType.REFUND.value,
            "transactionid": request.transaction_id,
        }

        if request.amount:
            data["amount"] = f"{request.amount / 100:.2f}"

        return await self._post_transaction(data)

    async def get_transaction(
        self,
        transaction_id: str,
    ) -> FinanceResult[NMITransactionResponse]:
        """
        Récupère les détails d'une transaction.

        Args:
            transaction_id: ID de la transaction

        Returns:
            FinanceResult avec les détails de la transaction
        """
        data = {
            "security_key": self.api_key,
            "transaction_id": transaction_id,
        }

        try:
            response = await (await self._get_client()).post(
                self.QUERY_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                return FinanceResult.fail(
                    error=FinanceError(
                        code=FinanceErrorCode.SERVICE_UNAVAILABLE,
                        message=f"HTTP {response.status_code}",
                        details={"body": response.text[:500]},
                    ),
                    provider=self.PROVIDER_NAME,
                )

            # Parser la réponse XML
            # NMI renvoie du XML pour les queries
            transaction_data = self._parse_query_response(response.text, transaction_id)

            if not transaction_data:
                return FinanceResult.fail(
                    error=FinanceError(
                        code=FinanceErrorCode.NOT_FOUND,
                        message=f"Transaction {transaction_id} non trouvée",
                    ),
                    provider=self.PROVIDER_NAME,
                )

            return FinanceResult.ok(
                data=transaction_data,
                provider=self.PROVIDER_NAME,
            )

        except Exception as e:
            self._logger.error(f"Erreur query transaction: {e}")
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INTERNAL_ERROR,
                    message=str(e),
                ),
                provider=self.PROVIDER_NAME,
            )

    # =========================================================================
    # CUSTOMER VAULT (Tokenisation)
    # =========================================================================

    async def create_vault_customer(
        self,
        card_number: str,
        exp_month: str,
        exp_year: str,
        customer_id: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> FinanceResult[NMIVaultResponse]:
        """
        Ajoute une carte au Customer Vault (tokenisation).

        Args:
            card_number: Numéro de carte
            exp_month: Mois d'expiration
            exp_year: Année d'expiration
            customer_id: ID client externe
            first_name: Prénom
            last_name: Nom
            email: Email

        Returns:
            FinanceResult avec le customer_vault_id (token)
        """
        data = {
            "security_key": self.api_key,
            "customer_vault": "add_customer",
            "ccnumber": card_number.replace(" ", "").replace("-", ""),
            "ccexp": f"{exp_month}{exp_year[-2:] if len(exp_year) == 4 else exp_year}",
        }

        if customer_id:
            data["customer_vault_id"] = customer_id
        if first_name:
            data["first_name"] = first_name
        if last_name:
            data["last_name"] = last_name
        if email:
            data["email"] = email

        try:
            response = await (await self._get_client()).post(
                self.BASE_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            result = self._parse_response(response.text)

            if result.get("response") == "1":
                return FinanceResult.ok(
                    data=NMIVaultResponse(
                        customer_vault_id=result.get("customer_vault_id", ""),
                        response_code=int(result.get("response", 0)),
                        response_text=result.get("responsetext", ""),
                        card_type=result.get("cc_type"),
                        card_last_four=card_number[-4:],
                    ),
                    provider=self.PROVIDER_NAME,
                )
            else:
                return FinanceResult.fail(
                    error=FinanceError(
                        code=FinanceErrorCode.SERVICE_UNAVAILABLE,
                        message=result.get("responsetext", "Unknown error"),
                        details=result,
                    ),
                    provider=self.PROVIDER_NAME,
                )

        except Exception as e:
            self._logger.error(f"Erreur création vault: {e}")
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INTERNAL_ERROR,
                    message=str(e),
                ),
                provider=self.PROVIDER_NAME,
            )

    async def charge_vault_customer(
        self,
        customer_vault_id: str,
        amount: int,
        order_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> FinanceResult[NMITransactionResponse]:
        """
        Débite un client du Customer Vault (carte tokenisée).

        Args:
            customer_vault_id: Token du client
            amount: Montant en centimes
            order_id: ID commande
            description: Description

        Returns:
            FinanceResult avec la réponse de transaction
        """
        data = {
            "security_key": self.api_key,
            "type": "sale",
            "customer_vault_id": customer_vault_id,
            "amount": f"{amount / 100:.2f}",
        }

        if order_id:
            data["orderid"] = order_id
        if description:
            data["orderdescription"] = description

        return await self._post_transaction(data)

    async def delete_vault_customer(
        self,
        customer_vault_id: str,
    ) -> FinanceResult[dict]:
        """
        Supprime un client du Customer Vault.

        Args:
            customer_vault_id: Token à supprimer

        Returns:
            FinanceResult confirmant la suppression
        """
        data = {
            "security_key": self.api_key,
            "customer_vault": "delete_customer",
            "customer_vault_id": customer_vault_id,
        }

        try:
            response = await (await self._get_client()).post(
                self.BASE_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            result = self._parse_response(response.text)

            if result.get("response") == "1":
                return FinanceResult.ok(
                    data={"deleted": True, "customer_vault_id": customer_vault_id},
                    provider=self.PROVIDER_NAME,
                )
            else:
                return FinanceResult.fail(
                    error=FinanceError(
                        code=FinanceErrorCode.SERVICE_UNAVAILABLE,
                        message=result.get("responsetext", "Unknown error"),
                    ),
                    provider=self.PROVIDER_NAME,
                )

        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INTERNAL_ERROR,
                    message=str(e),
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
    ) -> bool:
        """
        Vérifie la signature d'un webhook NMI.

        Args:
            payload: Corps brut de la requête
            signature: Signature du header X-Nmi-Signature

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
        Parse un événement webhook NMI.

        Args:
            payload: Données du webhook

        Returns:
            WebhookEvent normalisé
        """
        # Mapping des types d'événements NMI
        event_type_mapping = {
            "transaction.sale.success": WebhookEventType.PAYMENT_CAPTURED,
            "transaction.sale.failure": WebhookEventType.TRANSACTION_FAILED,
            "transaction.auth.success": WebhookEventType.PAYMENT_INITIATED,
            "transaction.refund.success": WebhookEventType.PAYMENT_REFUNDED,
            "transaction.void.success": WebhookEventType.TRANSACTION_FAILED,
            "chargeback.created": WebhookEventType.TRANSACTION_FAILED,
        }

        nmi_event_type = payload.get("event_type", payload.get("type", ""))
        event_type = event_type_mapping.get(
            nmi_event_type, WebhookEventType.PAYMENT_INITIATED
        )

        # Parse timestamp
        timestamp_str = payload.get("timestamp", datetime.utcnow().isoformat())
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1] + "+00:00"

        return WebhookEvent(
            id=payload.get("event_id", payload.get("id", "")),
            type=event_type,
            provider=FinanceProviderType.NMI,
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
        # NMI n'a pas d'endpoint de health check
        # On fait une validation de carte avec montant 0
        data = {
            "security_key": self.api_key,
            "type": "validate",
            "ccnumber": "4111111111111111",
            "ccexp": "1225",
        }

        try:
            response = await (await self._get_client()).post(
                self.BASE_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            result = self._parse_response(response.text)

            # response=1 = success, response=2 = declined, response=3 = error
            if result.get("response") in ["1", "2"]:
                return FinanceResult.ok(
                    data={
                        "status": "healthy",
                        "provider": self.PROVIDER_NAME,
                        "sandbox": self.sandbox,
                        "response": result.get("responsetext"),
                    },
                    provider=self.PROVIDER_NAME,
                )
            else:
                return FinanceResult.fail(
                    error=FinanceError(
                        code=FinanceErrorCode.SERVICE_UNAVAILABLE,
                        message=result.get("responsetext", "Health check failed"),
                    ),
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
        Récupère les informations du compte marchand NMI.

        NMI ne fournit pas d'endpoint pour récupérer les infos du compte.
        On retourne les informations de configuration connues.

        Returns:
            FinanceResult avec les infos du compte
        """
        return FinanceResult.ok(
            data={
                "provider": self.PROVIDER_NAME,
                "sandbox": self.sandbox,
                "tenant_id": self.tenant_id,
                "has_api_key": bool(self.api_key),
                "has_webhook_secret": bool(self.webhook_secret),
                "base_url": self.BASE_URL,
            },
            provider=self.PROVIDER_NAME,
        )

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    async def _execute_transaction(
        self,
        transaction_type: NMITransactionType,
        request: NMIPaymentRequest,
    ) -> FinanceResult[NMITransactionResponse]:
        """Exécute une transaction de paiement."""
        # Convertir montant en format NMI (dollars.cents)
        amount_str = f"{request.amount / 100:.2f}"

        data = {
            "security_key": self.api_key,
            "type": transaction_type.value,
            "amount": amount_str,
            "ccnumber": request.card_number,
            "ccexp": f"{request.exp_month}{request.exp_year}",
            "currency": request.currency,
        }

        if request.cvv:
            data["cvv"] = request.cvv
        if request.order_id:
            data["orderid"] = request.order_id
        if request.description:
            data["orderdescription"] = request.description

        # Billing info
        if request.billing_first_name:
            data["first_name"] = request.billing_first_name
        if request.billing_last_name:
            data["last_name"] = request.billing_last_name
        if request.billing_address:
            data["address1"] = request.billing_address
        if request.billing_city:
            data["city"] = request.billing_city
        if request.billing_state:
            data["state"] = request.billing_state
        if request.billing_zip:
            data["zip"] = request.billing_zip
        if request.billing_country:
            data["country"] = request.billing_country
        if request.billing_email:
            data["email"] = request.billing_email

        return await self._post_transaction(data)

    async def _post_transaction(
        self,
        data: dict,
    ) -> FinanceResult[NMITransactionResponse]:
        """Envoie une transaction à NMI."""
        try:
            response = await (await self._get_client()).post(
                self.BASE_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                return FinanceResult.fail(
                    error=FinanceError(
                        code=FinanceErrorCode.SERVICE_UNAVAILABLE,
                        message=f"HTTP {response.status_code}",
                        details={"body": response.text[:500]},
                    ),
                    provider=self.PROVIDER_NAME,
                )

            result = self._parse_response(response.text)

            # Log transaction
            self._logger.info(
                "Transaction NMI",
                extra={
                    "transaction_id": result.get("transactionid"),
                    "response": result.get("response"),
                    "response_text": result.get("responsetext"),
                    "type": data.get("type"),
                },
            )

            # Créer la réponse
            response_code = int(result.get("response", 3))
            amount_str = data.get("amount", "0")

            transaction = NMITransactionResponse(
                transaction_id=result.get("transactionid", ""),
                response_code=response_code,
                response_text=result.get("responsetext", ""),
                auth_code=result.get("authcode"),
                avs_response=result.get("avsresponse"),
                cvv_response=result.get("cvvresponse"),
                amount=Decimal(amount_str) if amount_str else Decimal("0"),
                card_type=result.get("cc_type"),
                card_last_four=data.get("ccnumber", "")[-4:] if data.get("ccnumber") else None,
                order_id=result.get("orderid"),
                processor_id=result.get("processor_id"),
            )

            if response_code == NMIResponseCode.APPROVED:
                return FinanceResult.ok(
                    data=transaction,
                    provider=self.PROVIDER_NAME,
                )
            elif response_code == NMIResponseCode.DECLINED:
                return FinanceResult.fail(
                    error=FinanceError(
                        code=FinanceErrorCode.TRANSACTION_REJECTED,
                        message=result.get("responsetext", "Transaction declined"),
                        details={
                            "transaction_id": transaction.transaction_id,
                            "avs_response": transaction.avs_response,
                            "cvv_response": transaction.cvv_response,
                        },
                    ),
                    provider=self.PROVIDER_NAME,
                )
            else:
                return FinanceResult.fail(
                    error=FinanceError(
                        code=FinanceErrorCode.SERVICE_UNAVAILABLE,
                        message=result.get("responsetext", "Transaction error"),
                        details=result,
                    ),
                    provider=self.PROVIDER_NAME,
                )

        except Exception as e:
            self._logger.error(f"Erreur transaction NMI: {e}")
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INTERNAL_ERROR,
                    message=str(e),
                ),
                provider=self.PROVIDER_NAME,
            )

    def _parse_response(self, response_text: str) -> dict:
        """Parse la réponse NMI (query string format)."""
        result = {}
        for pair in response_text.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                result[key] = value
        return result

    def _parse_query_response(
        self,
        xml_text: str,
        transaction_id: str,
    ) -> Optional[NMITransactionResponse]:
        """Parse la réponse XML du Query API."""
        # NMI renvoie du XML simple, on parse basiquement
        import re

        try:
            # Extraire les valeurs
            def extract(tag: str) -> Optional[str]:
                match = re.search(f"<{tag}>(.+?)</{tag}>", xml_text)
                return match.group(1) if match else None

            tid = extract("transaction_id")
            if not tid or tid != transaction_id:
                return None

            return NMITransactionResponse(
                transaction_id=tid,
                response_code=int(extract("condition") or 0),
                response_text=extract("action_type") or "",
                auth_code=extract("authorization_code"),
                amount=Decimal(extract("amount") or "0"),
                card_type=extract("cc_type"),
                order_id=extract("order_id"),
            )

        except Exception as e:
            self._logger.error(f"Erreur parsing query response: {e}")
            return None
