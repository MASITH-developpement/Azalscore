"""
AZALSCORE Defacto Finance Provider
==================================

Provider pour l'intégration avec Defacto (affacturage et financement B2B).
Gère les demandes de financement, la gestion des créances, et les remboursements.

Defacto est une plateforme de financement B2B spécialisée dans:
- Financement de factures (affacturage)
- Financement de stocks
- Lignes de crédit
- Remboursements flexibles

Usage:
    from app.modules.finance.providers import DefactoProvider

    provider = DefactoProvider(
        tenant_id="tenant-123",
        api_key="your_api_key",
        sandbox=True,
    )

    # Vérifier l'éligibilité
    result = await provider.check_eligibility(
        company_id="123456789",
        company_name="Mon Entreprise",
    )

    # Créer une demande de financement
    result = await provider.create_loan(
        borrower_id="bor_123",
        amount=50000,
        invoices=["inv_001", "inv_002"],
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
# ENUMS DEFACTO
# =============================================================================


class DefactoBorrowerStatus(str, Enum):
    """Statuts d'un emprunteur Defacto."""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REJECTED = "rejected"
    CLOSED = "closed"


class DefactoLoanStatus(str, Enum):
    """Statuts d'un prêt Defacto."""

    DRAFT = "draft"
    PENDING_VALIDATION = "pending_validation"
    VALIDATED = "validated"
    FUNDED = "funded"
    REPAYING = "repaying"
    REPAID = "repaid"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


class DefactoInvoiceStatus(str, Enum):
    """Statuts d'une facture Defacto."""

    PENDING = "pending"
    VALIDATED = "validated"
    FINANCED = "financed"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class DefactoFinancingType(str, Enum):
    """Types de financement Defacto."""

    INVOICE_FINANCING = "invoice_financing"  # Affacturage
    STOCK_FINANCING = "stock_financing"  # Financement de stock
    CREDIT_LINE = "credit_line"  # Ligne de crédit
    SUPPLIER_DISCOUNT = "supplier_discount"  # Remise fournisseur


# =============================================================================
# SCHEMAS PYDANTIC - REQUESTS
# =============================================================================


class DefactoBorrowerRequest(BaseModel):
    """Requête de création d'emprunteur Defacto."""

    # Identité entreprise
    company_name: str = Field(..., min_length=2, max_length=200)
    company_id: str = Field(..., description="SIREN/SIRET ou numéro d'immatriculation")
    country: str = Field(default="FR", pattern=r"^[A-Z]{2}$")

    # Contact
    contact_email: str = Field(..., max_length=100)
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    contact_first_name: Optional[str] = Field(default=None, max_length=50)
    contact_last_name: Optional[str] = Field(default=None, max_length=50)

    # Adresse
    address_line1: Optional[str] = Field(default=None, max_length=200)
    address_city: Optional[str] = Field(default=None, max_length=100)
    address_postal_code: Optional[str] = Field(default=None, max_length=20)

    # Données financières
    annual_revenue: Optional[int] = Field(default=None, ge=0)
    bank_account_iban: Optional[str] = Field(default=None, max_length=34)

    @field_validator("company_id")
    @classmethod
    def validate_company_id(cls, v: str) -> str:
        """Valide et nettoie le numéro d'identification."""
        cleaned = v.replace(" ", "").replace("-", "")
        if len(cleaned) < 9:
            raise ValueError("Numéro d'identification invalide")
        return cleaned


class DefactoInvoiceRequest(BaseModel):
    """Requête d'ajout de facture Defacto."""

    # Identification
    external_id: str = Field(..., max_length=50, description="ID facture dans votre système")
    invoice_number: str = Field(..., max_length=50)

    # Montants (en centimes)
    amount_cents: int = Field(..., gt=0, description="Montant TTC en centimes")
    currency: str = Field(default="EUR", pattern=r"^[A-Z]{3}$")

    # Dates
    issue_date: date = Field(..., description="Date d'émission")
    due_date: date = Field(..., description="Date d'échéance")

    # Débiteur (client de la facture)
    debtor_name: str = Field(..., min_length=2, max_length=200)
    debtor_company_id: Optional[str] = Field(default=None, max_length=20)
    debtor_email: Optional[str] = Field(default=None, max_length=100)

    # Document
    document_url: Optional[str] = Field(default=None, description="URL du PDF de la facture")

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: date, info) -> date:
        """Vérifie que la date d'échéance est après la date d'émission."""
        issue_date = info.data.get("issue_date")
        if issue_date and v < issue_date:
            raise ValueError("La date d'échéance doit être après la date d'émission")
        return v


class DefactoLoanRequest(BaseModel):
    """Requête de création de prêt Defacto."""

    borrower_id: str = Field(..., description="ID de l'emprunteur")
    financing_type: DefactoFinancingType = Field(
        default=DefactoFinancingType.INVOICE_FINANCING
    )

    # Montant demandé (en centimes)
    amount_cents: int = Field(..., gt=0, description="Montant demandé en centimes")
    currency: str = Field(default="EUR", pattern=r"^[A-Z]{3}$")

    # Factures à financer
    invoice_ids: list[str] = Field(default_factory=list)

    # Conditions
    repayment_term_days: Optional[int] = Field(default=None, ge=1, le=365)

    # Référence externe
    external_reference: Optional[str] = Field(default=None, max_length=100)


# =============================================================================
# SCHEMAS PYDANTIC - RESPONSES
# =============================================================================


class DefactoBorrowerResponse(BaseModel):
    """Réponse emprunteur Defacto."""

    id: str
    company_name: str
    company_id: str
    status: DefactoBorrowerStatus
    country: str

    # Limites
    credit_limit_cents: Optional[int] = None
    available_credit_cents: Optional[int] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None


class DefactoInvoiceResponse(BaseModel):
    """Réponse facture Defacto."""

    id: str
    external_id: str
    invoice_number: str
    status: DefactoInvoiceStatus

    # Montants
    amount_cents: int
    financed_amount_cents: Optional[int] = None
    currency: str

    # Dates
    issue_date: date
    due_date: date

    # Débiteur
    debtor_name: str

    # Timestamps
    created_at: datetime
    financed_at: Optional[datetime] = None


class DefactoLoanResponse(BaseModel):
    """Réponse prêt Defacto."""

    id: str
    borrower_id: str
    status: DefactoLoanStatus
    financing_type: DefactoFinancingType

    # Montants
    amount_cents: int
    funded_amount_cents: Optional[int] = None
    repaid_amount_cents: int = 0
    currency: str

    # Conditions
    interest_rate: Optional[Decimal] = None
    fee_cents: Optional[int] = None
    repayment_term_days: Optional[int] = None

    # Factures liées
    invoice_ids: list[str] = Field(default_factory=list)

    # Dates
    funded_at: Optional[datetime] = None
    repayment_due_date: Optional[date] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None


class DefactoEligibilityResponse(BaseModel):
    """Réponse d'éligibilité Defacto."""

    eligible: bool
    company_id: str
    company_name: Optional[str] = None

    # Limites proposées
    max_credit_limit_cents: Optional[int] = None
    suggested_products: list[str] = Field(default_factory=list)

    # Raison du refus
    rejection_reason: Optional[str] = None


# =============================================================================
# DEFACTO PROVIDER
# =============================================================================


class DefactoProvider(BaseFinanceProvider):
    """
    Provider pour Defacto (affacturage et financement B2B).

    Fonctionnalités:
    - Onboarding des emprunteurs
    - Gestion des factures
    - Demandes de financement
    - Suivi des remboursements
    - Webhooks temps réel

    Configuration:
        api_key: API Key Defacto
        sandbox: True pour environnement de test
    """

    PROVIDER_NAME = "defacto"
    PROVIDER_TYPE = FinanceProviderType.DEFACTO

    # URLs Defacto
    SANDBOX_URL = "https://api-sandbox.getdefacto.com"
    PRODUCTION_URL = "https://api.getdefacto.com"

    def __init__(
        self,
        tenant_id: str,
        api_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        sandbox: bool = True,
    ):
        """
        Initialise le provider Defacto.

        Args:
            tenant_id: ID du tenant (OBLIGATOIRE)
            api_key: API Key Defacto
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

        self._logger.info(
            f"DefactoProvider initialisé",
            extra={"sandbox": sandbox, "has_webhook_secret": bool(webhook_secret)},
        )

    def _get_default_headers(self) -> dict[str, str]:
        """Retourne les headers par défaut pour Defacto."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"AZALSCORE/{self.PROVIDER_NAME}",
            "X-Tenant-ID": self.tenant_id,
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    # =========================================================================
    # EMPRUNTEURS (BORROWERS)
    # =========================================================================

    async def create_borrower(
        self,
        company_name: str,
        company_id: str,
        contact_email: str,
        country: str = "FR",
        contact_phone: Optional[str] = None,
        contact_first_name: Optional[str] = None,
        contact_last_name: Optional[str] = None,
        address_line1: Optional[str] = None,
        address_city: Optional[str] = None,
        address_postal_code: Optional[str] = None,
        annual_revenue: Optional[int] = None,
        bank_account_iban: Optional[str] = None,
    ) -> FinanceResult[DefactoBorrowerResponse]:
        """
        Crée un nouvel emprunteur (onboarding).

        Args:
            company_name: Nom de l'entreprise
            company_id: SIREN/SIRET
            contact_email: Email de contact
            country: Code pays ISO (défaut: FR)
            contact_phone: Téléphone
            contact_first_name: Prénom du contact
            contact_last_name: Nom du contact
            address_*: Adresse
            annual_revenue: CA annuel en centimes
            bank_account_iban: IBAN du compte

        Returns:
            FinanceResult avec les données de l'emprunteur
        """
        try:
            request = DefactoBorrowerRequest(
                company_name=company_name,
                company_id=company_id,
                contact_email=contact_email,
                country=country,
                contact_phone=contact_phone,
                contact_first_name=contact_first_name,
                contact_last_name=contact_last_name,
                address_line1=address_line1,
                address_city=address_city,
                address_postal_code=address_postal_code,
                annual_revenue=annual_revenue,
                bank_account_iban=bank_account_iban,
            )
        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_REQUEST,
                    message=str(e),
                ),
                provider=self.PROVIDER_NAME,
            )

        return await self._request(
            method="POST",
            endpoint="/borrowers",
            json_data=request.model_dump(exclude_none=True),
        )

    async def get_borrower(
        self,
        borrower_id: str,
    ) -> FinanceResult[DefactoBorrowerResponse]:
        """
        Récupère les informations d'un emprunteur.

        Args:
            borrower_id: ID de l'emprunteur

        Returns:
            FinanceResult avec les données de l'emprunteur
        """
        return await self._request(
            method="GET",
            endpoint=f"/borrower/{borrower_id}",
        )

    async def check_eligibility(
        self,
        company_id: str,
        company_name: Optional[str] = None,
        country: str = "FR",
    ) -> FinanceResult[DefactoEligibilityResponse]:
        """
        Vérifie l'éligibilité d'une entreprise au financement.

        Args:
            company_id: SIREN/SIRET
            company_name: Nom de l'entreprise (optionnel)
            country: Code pays

        Returns:
            FinanceResult avec le statut d'éligibilité
        """
        data = {
            "company_id": company_id.replace(" ", "").replace("-", ""),
            "country": country,
        }
        if company_name:
            data["company_name"] = company_name

        return await self._request(
            method="POST",
            endpoint="/eligibility/borrower",
            json_data=data,
        )

    async def get_credit_lines(
        self,
        borrower_id: str,
    ) -> FinanceResult[dict]:
        """
        Récupère les lignes de crédit disponibles.

        Args:
            borrower_id: ID de l'emprunteur

        Returns:
            FinanceResult avec les lignes de crédit
        """
        return await self._request(
            method="GET",
            endpoint=f"/borrower/{borrower_id}/financial-products",
        )

    # =========================================================================
    # FACTURES (INVOICES)
    # =========================================================================

    async def create_invoice(
        self,
        borrower_id: str,
        external_id: str,
        invoice_number: str,
        amount_cents: int,
        issue_date: date,
        due_date: date,
        debtor_name: str,
        currency: str = "EUR",
        debtor_company_id: Optional[str] = None,
        debtor_email: Optional[str] = None,
        document_url: Optional[str] = None,
    ) -> FinanceResult[DefactoInvoiceResponse]:
        """
        Ajoute une facture à financer.

        Args:
            borrower_id: ID de l'emprunteur
            external_id: ID de la facture dans votre système
            invoice_number: Numéro de facture
            amount_cents: Montant TTC en centimes
            issue_date: Date d'émission
            due_date: Date d'échéance
            debtor_name: Nom du débiteur (client)
            currency: Devise (défaut: EUR)
            debtor_company_id: SIREN du débiteur
            debtor_email: Email du débiteur
            document_url: URL du PDF

        Returns:
            FinanceResult avec les données de la facture
        """
        try:
            request = DefactoInvoiceRequest(
                external_id=external_id,
                invoice_number=invoice_number,
                amount_cents=amount_cents,
                currency=currency,
                issue_date=issue_date,
                due_date=due_date,
                debtor_name=debtor_name,
                debtor_company_id=debtor_company_id,
                debtor_email=debtor_email,
                document_url=document_url,
            )
        except Exception as e:
            return FinanceResult.fail(
                error=FinanceError(
                    code=FinanceErrorCode.INVALID_REQUEST,
                    message=str(e),
                ),
                provider=self.PROVIDER_NAME,
            )

        return await self._request(
            method="POST",
            endpoint="/invoices",
            json_data={
                "borrower_id": borrower_id,
                **request.model_dump(exclude_none=True, mode="json"),
            },
        )

    async def get_invoices(
        self,
        borrower_id: str,
        status: Optional[DefactoInvoiceStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> FinanceResult[list[DefactoInvoiceResponse]]:
        """
        Liste les factures d'un emprunteur.

        Args:
            borrower_id: ID de l'emprunteur
            status: Filtrer par statut
            limit: Nombre max de résultats
            offset: Décalage pour pagination

        Returns:
            FinanceResult avec la liste des factures
        """
        params = {
            "borrower_id": borrower_id,
            "limit": limit,
            "offset": offset,
        }
        if status:
            params["status"] = status.value

        return await self._request(
            method="GET",
            endpoint="/invoices",
            params=params,
        )

    async def get_invoice(
        self,
        invoice_id: str,
    ) -> FinanceResult[DefactoInvoiceResponse]:
        """
        Récupère les détails d'une facture.

        Args:
            invoice_id: ID de la facture

        Returns:
            FinanceResult avec les données de la facture
        """
        return await self._request(
            method="GET",
            endpoint=f"/invoice/{invoice_id}",
        )

    async def delete_invoice(
        self,
        invoice_id: str,
    ) -> FinanceResult[dict]:
        """
        Supprime une facture (si non financée).

        Args:
            invoice_id: ID de la facture

        Returns:
            FinanceResult confirmant la suppression
        """
        result = await self._request(
            method="DELETE",
            endpoint=f"/invoice/{invoice_id}",
        )

        if result.success:
            return FinanceResult.ok(
                data={"deleted": True, "invoice_id": invoice_id},
                provider=self.PROVIDER_NAME,
            )
        return result

    # =========================================================================
    # PRÊTS (LOANS)
    # =========================================================================

    async def create_loan(
        self,
        borrower_id: str,
        amount_cents: int,
        invoice_ids: list[str],
        financing_type: DefactoFinancingType = DefactoFinancingType.INVOICE_FINANCING,
        currency: str = "EUR",
        repayment_term_days: Optional[int] = None,
        external_reference: Optional[str] = None,
    ) -> FinanceResult[DefactoLoanResponse]:
        """
        Crée une demande de prêt/financement.

        Args:
            borrower_id: ID de l'emprunteur
            amount_cents: Montant demandé en centimes
            invoice_ids: Liste des factures à financer
            financing_type: Type de financement
            currency: Devise (défaut: EUR)
            repayment_term_days: Durée de remboursement en jours
            external_reference: Référence externe

        Returns:
            FinanceResult avec les données du prêt
        """
        try:
            request = DefactoLoanRequest(
                borrower_id=borrower_id,
                amount_cents=amount_cents,
                invoice_ids=invoice_ids,
                financing_type=financing_type,
                currency=currency,
                repayment_term_days=repayment_term_days,
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

        return await self._request(
            method="POST",
            endpoint="/loans",
            json_data=request.model_dump(exclude_none=True),
        )

    async def get_loans(
        self,
        borrower_id: str,
        status: Optional[DefactoLoanStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> FinanceResult[list[DefactoLoanResponse]]:
        """
        Liste les prêts d'un emprunteur.

        Args:
            borrower_id: ID de l'emprunteur
            status: Filtrer par statut
            limit: Nombre max de résultats
            offset: Décalage pour pagination

        Returns:
            FinanceResult avec la liste des prêts
        """
        params = {
            "borrower_id": borrower_id,
            "limit": limit,
            "offset": offset,
        }
        if status:
            params["status"] = status.value

        return await self._request(
            method="GET",
            endpoint="/loans",
            params=params,
        )

    async def get_loan(
        self,
        loan_id: str,
    ) -> FinanceResult[DefactoLoanResponse]:
        """
        Récupère les détails d'un prêt.

        Args:
            loan_id: ID du prêt

        Returns:
            FinanceResult avec les données du prêt
        """
        return await self._request(
            method="GET",
            endpoint=f"/loan/{loan_id}",
        )

    async def validate_loan(
        self,
        loan_id: str,
    ) -> FinanceResult[DefactoLoanResponse]:
        """
        Valide et active un prêt.

        Args:
            loan_id: ID du prêt

        Returns:
            FinanceResult avec le prêt validé
        """
        return await self._request(
            method="POST",
            endpoint=f"/loan/{loan_id}/validate",
        )

    async def cancel_loan(
        self,
        loan_id: str,
        reason: Optional[str] = None,
    ) -> FinanceResult[DefactoLoanResponse]:
        """
        Annule un prêt.

        Args:
            loan_id: ID du prêt
            reason: Raison de l'annulation

        Returns:
            FinanceResult avec le prêt annulé
        """
        data = {}
        if reason:
            data["cancellation_reason"] = reason

        return await self._request(
            method="POST",
            endpoint=f"/loan/{loan_id}/cancel",
            json_data=data if data else None,
        )

    # =========================================================================
    # PAIEMENTS & REMBOURSEMENTS
    # =========================================================================

    async def get_payments(
        self,
        borrower_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> FinanceResult[list[dict]]:
        """
        Liste les paiements d'un emprunteur.

        Args:
            borrower_id: ID de l'emprunteur
            limit: Nombre max de résultats
            offset: Décalage

        Returns:
            FinanceResult avec la liste des paiements
        """
        return await self._request(
            method="GET",
            endpoint="/payments",
            params={
                "borrower_id": borrower_id,
                "limit": limit,
                "offset": offset,
            },
        )

    async def get_installments(
        self,
        loan_id: str,
    ) -> FinanceResult[list[dict]]:
        """
        Récupère les échéances d'un prêt.

        Args:
            loan_id: ID du prêt

        Returns:
            FinanceResult avec les échéances
        """
        return await self._request(
            method="GET",
            endpoint="/installments",
            params={"loan_id": loan_id},
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
        Vérifie la signature d'un webhook Defacto.

        Args:
            payload: Corps brut de la requête
            signature: Signature du header X-Defacto-Signature

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
        Parse un événement webhook Defacto.

        Args:
            payload: Données du webhook

        Returns:
            WebhookEvent normalisé
        """
        # Mapping des types d'événements Defacto
        event_type_mapping = {
            "borrower.created": WebhookEventType.ACCOUNT_CREATED,
            "borrower.updated": WebhookEventType.ACCOUNT_UPDATED,
            "borrower.activated": WebhookEventType.ACCOUNT_UPDATED,
            "loan.created": WebhookEventType.TRANSACTION_CREATED,
            "loan.validated": WebhookEventType.PAYMENT_AUTHORIZED,
            "loan.funded": WebhookEventType.PAYMENT_CAPTURED,
            "loan.repaid": WebhookEventType.TRANSACTION_COMPLETED,
            "loan.defaulted": WebhookEventType.TRANSACTION_FAILED,
            "loan.cancelled": WebhookEventType.TRANSACTION_FAILED,
            "invoice.financed": WebhookEventType.PAYMENT_CAPTURED,
            "invoice.paid": WebhookEventType.TRANSACTION_COMPLETED,
            "payment.received": WebhookEventType.PAYMENT_CAPTURED,
        }

        defacto_event_type = payload.get("event_type", payload.get("type", ""))
        event_type = event_type_mapping.get(
            defacto_event_type, WebhookEventType.TRANSACTION_CREATED
        )

        # Parse timestamp
        timestamp_str = payload.get("timestamp", datetime.utcnow().isoformat())
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1] + "+00:00"

        return WebhookEvent(
            id=payload.get("event_id", payload.get("id", "")),
            type=event_type,
            provider=FinanceProviderType.DEFACTO,
            tenant_id=self.tenant_id,
            payload=payload.get("data", payload),
            raw_payload=str(payload),
            timestamp=datetime.fromisoformat(timestamp_str),
        )

    async def subscribe_webhook(
        self,
        url: str,
        events: list[str],
    ) -> FinanceResult[dict]:
        """
        S'abonne à des événements webhook.

        Args:
            url: URL de réception des webhooks
            events: Liste des types d'événements

        Returns:
            FinanceResult avec l'ID de la souscription
        """
        return await self._request(
            method="POST",
            endpoint="/webhooks",
            json_data={
                "url": url,
                "events": events,
            },
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
            # Defacto: on tente un appel simple
            client = await self._get_client()
            response = await client.get(
                f"{self.BASE_URL}/health",
                headers=self._get_default_headers(),
            )

            if response.status_code in [200, 401, 403]:
                # 401/403 = API accessible mais auth requise
                return FinanceResult.ok(
                    data={
                        "status": "healthy",
                        "provider": self.PROVIDER_NAME,
                        "sandbox": self.sandbox,
                    },
                    provider=self.PROVIDER_NAME,
                )
            else:
                return FinanceResult.fail(
                    error=FinanceError(
                        code=FinanceErrorCode.SERVICE_UNAVAILABLE,
                        message=f"API returned {response.status_code}",
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
        Récupère les informations du compte Defacto.

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
