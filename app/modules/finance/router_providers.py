"""
AZALSCORE Finance Providers Router V3
=====================================

Endpoints REST pour les providers finance (Swan, NMI, Defacto, Solaris).

Endpoints:
- GET  /v3/finance/providers/swan/accounts - Lister les comptes Swan
- GET  /v3/finance/providers/swan/transactions - Lister les transactions Swan
- POST /v3/finance/providers/swan/transfers - Créer un virement Swan

- POST /v3/finance/providers/nmi/payments - Traiter un paiement carte NMI
- POST /v3/finance/providers/nmi/authorize - Autoriser un paiement
- POST /v3/finance/providers/nmi/capture - Capturer un paiement
- POST /v3/finance/providers/nmi/void - Annuler une autorisation
- POST /v3/finance/providers/nmi/refund - Rembourser un paiement
- POST /v3/finance/providers/nmi/vault/customers - Créer un client vault
- POST /v3/finance/providers/nmi/vault/customers/{customer_id}/charge - Facturer un client vault

- POST /v3/finance/providers/defacto/borrowers - Créer un emprunteur
- POST /v3/finance/providers/defacto/eligibility - Vérifier l'éligibilité
- POST /v3/finance/providers/defacto/invoices - Créer une facture
- POST /v3/finance/providers/defacto/loans - Créer un prêt
- POST /v3/finance/providers/defacto/loans/{loan_id}/validate - Valider un prêt

- POST /v3/finance/providers/solaris/businesses - Créer une entreprise
- POST /v3/finance/providers/solaris/accounts - Créer un compte
- POST /v3/finance/providers/solaris/overdrafts - Demander un découvert
- POST /v3/finance/providers/solaris/transfers - Créer un virement

- GET  /v3/finance/providers/health - Health check providers
"""
from __future__ import annotations


import logging
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import SaaSContext
from app.core.dependencies_v2 import get_saas_context

from .providers.base import FinanceProviderType, FinanceErrorCode
from .providers.registry import FinanceProviderRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3/finance/providers", tags=["Finance Providers"])


# =============================================================================
# SCHEMAS COMMUNS
# =============================================================================


class ProviderResponse(BaseModel):
    """Réponse standard des providers."""

    success: bool
    provider: str
    data: Optional[dict] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


class TransferRequest(BaseModel):
    """Requête de virement bancaire."""

    source_account_id: str = Field(..., description="ID du compte source")
    beneficiary_iban: str = Field(..., description="IBAN du bénéficiaire")
    beneficiary_name: str = Field(..., description="Nom du bénéficiaire")
    amount: Decimal = Field(..., gt=0, description="Montant en centimes")
    currency: str = Field(default="EUR", description="Devise")
    reference: Optional[str] = Field(None, description="Référence du virement")
    label: Optional[str] = Field(None, description="Libellé")


class PaymentRequest(BaseModel):
    """Requête de paiement carte."""

    amount: Decimal = Field(..., gt=0, description="Montant en centimes")
    currency: str = Field(default="EUR", description="Devise")
    card_number: str = Field(..., min_length=13, max_length=19)
    expiry_month: str = Field(..., pattern=r"^\d{2}$")
    expiry_year: str = Field(..., pattern=r"^\d{2}$")
    cvv: str = Field(..., min_length=3, max_length=4)
    cardholder_name: Optional[str] = None
    description: Optional[str] = None
    order_id: Optional[str] = None


class AuthorizeRequest(BaseModel):
    """Requête d'autorisation carte."""

    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="EUR")
    card_number: str = Field(..., min_length=13, max_length=19)
    expiry_month: str = Field(..., pattern=r"^\d{2}$")
    expiry_year: str = Field(..., pattern=r"^\d{2}$")
    cvv: str = Field(..., min_length=3, max_length=4)
    cardholder_name: Optional[str] = None


class CaptureRequest(BaseModel):
    """Requête de capture."""

    transaction_id: str = Field(..., description="ID de la transaction à capturer")
    amount: Optional[Decimal] = Field(None, description="Montant partiel (optionnel)")


class VoidRequest(BaseModel):
    """Requête d'annulation."""

    transaction_id: str = Field(..., description="ID de la transaction à annuler")


class RefundRequest(BaseModel):
    """Requête de remboursement."""

    transaction_id: str = Field(..., description="ID de la transaction à rembourser")
    amount: Optional[Decimal] = Field(None, description="Montant partiel (optionnel)")


class VaultCustomerRequest(BaseModel):
    """Requête création client vault."""

    customer_id: str = Field(..., description="ID client interne")
    card_number: str = Field(..., min_length=13, max_length=19)
    expiry_month: str = Field(..., pattern=r"^\d{2}$")
    expiry_year: str = Field(..., pattern=r"^\d{2}$")


class VaultChargeRequest(BaseModel):
    """Requête facturation client vault."""

    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="EUR")
    description: Optional[str] = None


class BorrowerRequest(BaseModel):
    """Requête création emprunteur Defacto."""

    company_name: str = Field(..., min_length=1)
    siren: str = Field(..., pattern=r"^\d{9}$")
    email: str = Field(...)
    phone: Optional[str] = None
    address_line1: str = Field(...)
    postal_code: str = Field(...)
    city: str = Field(...)
    country: str = Field(default="FR")
    legal_representative_first_name: str = Field(...)
    legal_representative_last_name: str = Field(...)
    legal_representative_email: str = Field(...)


class EligibilityRequest(BaseModel):
    """Requête vérification éligibilité Defacto."""

    borrower_id: str = Field(...)
    amount: Decimal = Field(..., gt=0)
    duration_months: int = Field(..., ge=1, le=36)


class InvoiceRequest(BaseModel):
    """Requête création facture Defacto."""

    borrower_id: str = Field(...)
    invoice_number: str = Field(...)
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="EUR")
    issue_date: date = Field(...)
    due_date: date = Field(...)
    debtor_name: str = Field(...)
    debtor_siren: Optional[str] = None


class LoanRequest(BaseModel):
    """Requête création prêt Defacto."""

    borrower_id: str = Field(...)
    invoice_ids: list[str] = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    duration_months: int = Field(..., ge=1, le=36)


class BusinessRequest(BaseModel):
    """Requête création entreprise Solaris."""

    name: str = Field(..., min_length=1)
    legal_form: str = Field(..., description="SAS, SARL, etc.")
    registration_number: str = Field(..., description="SIREN/SIRET")
    address_line: str = Field(...)
    postal_code: str = Field(...)
    city: str = Field(...)
    country: str = Field(default="DE")
    industry: Optional[str] = None
    website: Optional[str] = None


class AccountRequest(BaseModel):
    """Requête création compte Solaris."""

    business_id: str = Field(...)
    account_type: str = Field(default="CHECKING")
    currency: str = Field(default="EUR")
    purpose: Optional[str] = None


class OverdraftRequest(BaseModel):
    """Requête découvert Solaris."""

    account_id: str = Field(...)
    amount: Decimal = Field(..., gt=0)
    duration_days: int = Field(..., ge=1, le=365)
    purpose: str = Field(...)


class SolarisTransferRequest(BaseModel):
    """Requête virement Solaris."""

    account_id: str = Field(...)
    recipient_iban: str = Field(...)
    recipient_name: str = Field(...)
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="EUR")
    reference: Optional[str] = None


# =============================================================================
# DEPENDENCIES
# =============================================================================


async def get_provider_registry(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> FinanceProviderRegistry:
    """Dépendance pour obtenir le registry des providers."""
    return FinanceProviderRegistry(tenant_id=context.tenant_id, db=db)


def handle_provider_result(result, provider_name: str) -> ProviderResponse:
    """Convertit un FinanceResult en ProviderResponse."""
    if result.success:
        return ProviderResponse(
            success=True,
            provider=provider_name,
            data=result.data if isinstance(result.data, dict) else {"result": result.data},
        )
    else:
        return ProviderResponse(
            success=False,
            provider=provider_name,
            error=result.error.message if result.error else "Unknown error",
            error_code=result.error.code.value if result.error else None,
        )


# =============================================================================
# SWAN ENDPOINTS
# =============================================================================


@router.get(
    "/swan/accounts",
    response_model=ProviderResponse,
    summary="Lister les comptes Swan",
    description="Récupère la liste des comptes bancaires via Swan.",
)
async def list_swan_accounts(
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Liste les comptes Swan du tenant."""
    provider = await registry.get_provider(FinanceProviderType.SWAN)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider Swan non configuré pour ce tenant",
        )

    result = await provider.get_accounts()
    return handle_provider_result(result, "swan")


@router.get(
    "/swan/transactions",
    response_model=ProviderResponse,
    summary="Lister les transactions Swan",
    description="Récupère les transactions d'un compte Swan.",
)
async def list_swan_transactions(
    account_id: str = Query(..., description="ID du compte Swan"),
    limit: int = Query(50, ge=1, le=500),
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Liste les transactions d'un compte Swan."""
    provider = await registry.get_provider(FinanceProviderType.SWAN)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider Swan non configuré",
        )

    result = await provider.get_transactions(account_id=account_id, limit=limit)
    return handle_provider_result(result, "swan")


@router.post(
    "/swan/transfers",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un virement Swan",
    description="Initie un virement SEPA via Swan.",
)
async def create_swan_transfer(
    data: TransferRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Crée un virement via Swan."""
    provider = await registry.get_provider(FinanceProviderType.SWAN)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider Swan non configuré",
        )

    result = await provider.create_transfer(
        source_account_id=data.source_account_id,
        beneficiary_iban=data.beneficiary_iban,
        beneficiary_name=data.beneficiary_name,
        amount=int(data.amount),  # En centimes
        currency=data.currency,
        reference=data.reference,
        label=data.label,
    )
    return handle_provider_result(result, "swan")


# =============================================================================
# NMI ENDPOINTS
# =============================================================================


@router.post(
    "/nmi/payments",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Traiter un paiement NMI",
    description="Effectue une transaction sale (auth + capture) via NMI.",
)
async def process_nmi_payment(
    data: PaymentRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Traite un paiement carte via NMI."""
    provider = await registry.get_provider(FinanceProviderType.NMI)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider NMI non configuré",
        )

    result = await provider.process_payment(
        amount=int(data.amount),
        currency=data.currency,
        card_number=data.card_number,
        expiry_month=data.expiry_month,
        expiry_year=data.expiry_year,
        cvv=data.cvv,
        cardholder_name=data.cardholder_name,
        description=data.description,
        order_id=data.order_id,
    )
    return handle_provider_result(result, "nmi")


@router.post(
    "/nmi/authorize",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Autoriser un paiement NMI",
    description="Autorise un paiement carte (sans capture).",
)
async def authorize_nmi_payment(
    data: AuthorizeRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Autorise un paiement via NMI."""
    provider = await registry.get_provider(FinanceProviderType.NMI)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider NMI non configuré",
        )

    result = await provider.authorize(
        amount=int(data.amount),
        currency=data.currency,
        card_number=data.card_number,
        expiry_month=data.expiry_month,
        expiry_year=data.expiry_year,
        cvv=data.cvv,
        cardholder_name=data.cardholder_name,
    )
    return handle_provider_result(result, "nmi")


@router.post(
    "/nmi/capture",
    response_model=ProviderResponse,
    summary="Capturer un paiement NMI",
    description="Capture une autorisation existante.",
)
async def capture_nmi_payment(
    data: CaptureRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Capture une autorisation NMI."""
    provider = await registry.get_provider(FinanceProviderType.NMI)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider NMI non configuré",
        )

    result = await provider.capture(
        transaction_id=data.transaction_id,
        amount=int(data.amount) if data.amount else None,
    )
    return handle_provider_result(result, "nmi")


@router.post(
    "/nmi/void",
    response_model=ProviderResponse,
    summary="Annuler une autorisation NMI",
    description="Annule une autorisation non capturée.",
)
async def void_nmi_payment(
    data: VoidRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Annule une autorisation NMI."""
    provider = await registry.get_provider(FinanceProviderType.NMI)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider NMI non configuré",
        )

    result = await provider.void(transaction_id=data.transaction_id)
    return handle_provider_result(result, "nmi")


@router.post(
    "/nmi/refund",
    response_model=ProviderResponse,
    summary="Rembourser un paiement NMI",
    description="Rembourse un paiement capturé.",
)
async def refund_nmi_payment(
    data: RefundRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Rembourse un paiement NMI."""
    provider = await registry.get_provider(FinanceProviderType.NMI)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider NMI non configuré",
        )

    result = await provider.refund(
        transaction_id=data.transaction_id,
        amount=int(data.amount) if data.amount else None,
    )
    return handle_provider_result(result, "nmi")


@router.post(
    "/nmi/vault/customers",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un client vault NMI",
    description="Stocke une carte de manière sécurisée (vault).",
)
async def create_nmi_vault_customer(
    data: VaultCustomerRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Crée un client vault NMI."""
    provider = await registry.get_provider(FinanceProviderType.NMI)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider NMI non configuré",
        )

    result = await provider.create_vault_customer(
        customer_id=data.customer_id,
        card_number=data.card_number,
        expiry_month=data.expiry_month,
        expiry_year=data.expiry_year,
    )
    return handle_provider_result(result, "nmi")


@router.post(
    "/nmi/vault/customers/{customer_vault_id}/charge",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Facturer un client vault NMI",
    description="Facture un client avec sa carte enregistrée.",
)
async def charge_nmi_vault_customer(
    customer_vault_id: str,
    data: VaultChargeRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Facture un client vault NMI."""
    provider = await registry.get_provider(FinanceProviderType.NMI)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider NMI non configuré",
        )

    result = await provider.charge_vault_customer(
        customer_vault_id=customer_vault_id,
        amount=int(data.amount),
        currency=data.currency,
        description=data.description,
    )
    return handle_provider_result(result, "nmi")


# =============================================================================
# DEFACTO ENDPOINTS
# =============================================================================


@router.post(
    "/defacto/borrowers",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un emprunteur Defacto",
    description="Enregistre une entreprise comme emprunteur potentiel.",
)
async def create_defacto_borrower(
    data: BorrowerRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Crée un emprunteur Defacto."""
    provider = await registry.get_provider(FinanceProviderType.DEFACTO)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider Defacto non configuré",
        )

    result = await provider.create_borrower(
        company_name=data.company_name,
        siren=data.siren,
        email=data.email,
        phone=data.phone,
        address_line1=data.address_line1,
        postal_code=data.postal_code,
        city=data.city,
        country=data.country,
        legal_representative_first_name=data.legal_representative_first_name,
        legal_representative_last_name=data.legal_representative_last_name,
        legal_representative_email=data.legal_representative_email,
    )
    return handle_provider_result(result, "defacto")


@router.post(
    "/defacto/eligibility",
    response_model=ProviderResponse,
    summary="Vérifier l'éligibilité Defacto",
    description="Vérifie si un emprunteur est éligible à un financement.",
)
async def check_defacto_eligibility(
    data: EligibilityRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Vérifie l'éligibilité Defacto."""
    provider = await registry.get_provider(FinanceProviderType.DEFACTO)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider Defacto non configuré",
        )

    result = await provider.check_eligibility(
        borrower_id=data.borrower_id,
        amount=int(data.amount),
        duration_months=data.duration_months,
    )
    return handle_provider_result(result, "defacto")


@router.post(
    "/defacto/invoices",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une facture Defacto",
    description="Enregistre une facture pour financement potentiel.",
)
async def create_defacto_invoice(
    data: InvoiceRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Crée une facture Defacto."""
    provider = await registry.get_provider(FinanceProviderType.DEFACTO)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider Defacto non configuré",
        )

    result = await provider.create_invoice(
        borrower_id=data.borrower_id,
        invoice_number=data.invoice_number,
        amount=int(data.amount),
        currency=data.currency,
        issue_date=data.issue_date,
        due_date=data.due_date,
        debtor_name=data.debtor_name,
        debtor_siren=data.debtor_siren,
    )
    return handle_provider_result(result, "defacto")


@router.post(
    "/defacto/loans",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un prêt Defacto",
    description="Crée une demande de prêt basée sur des factures.",
)
async def create_defacto_loan(
    data: LoanRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Crée un prêt Defacto."""
    provider = await registry.get_provider(FinanceProviderType.DEFACTO)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider Defacto non configuré",
        )

    result = await provider.create_loan(
        borrower_id=data.borrower_id,
        invoice_ids=data.invoice_ids,
        amount=int(data.amount),
        duration_months=data.duration_months,
    )
    return handle_provider_result(result, "defacto")


@router.post(
    "/defacto/loans/{loan_id}/validate",
    response_model=ProviderResponse,
    summary="Valider un prêt Defacto",
    description="Valide et active un prêt Defacto.",
)
async def validate_defacto_loan(
    loan_id: str,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Valide un prêt Defacto."""
    provider = await registry.get_provider(FinanceProviderType.DEFACTO)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider Defacto non configuré",
        )

    result = await provider.validate_loan(loan_id=loan_id)
    return handle_provider_result(result, "defacto")


# =============================================================================
# SOLARIS ENDPOINTS
# =============================================================================


@router.post(
    "/solaris/businesses",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une entreprise Solaris",
    description="Enregistre une entreprise sur Solaris Bank.",
)
async def create_solaris_business(
    data: BusinessRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Crée une entreprise Solaris."""
    provider = await registry.get_provider(FinanceProviderType.SOLARIS)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider Solaris non configuré",
        )

    result = await provider.create_business(
        name=data.name,
        legal_form=data.legal_form,
        registration_number=data.registration_number,
        address_line=data.address_line,
        postal_code=data.postal_code,
        city=data.city,
        country=data.country,
        industry=data.industry,
        website=data.website,
    )
    return handle_provider_result(result, "solaris")


@router.post(
    "/solaris/accounts",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte Solaris",
    description="Ouvre un compte bancaire Solaris pour une entreprise.",
)
async def create_solaris_account(
    data: AccountRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Crée un compte Solaris."""
    provider = await registry.get_provider(FinanceProviderType.SOLARIS)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider Solaris non configuré",
        )

    result = await provider.create_account(
        business_id=data.business_id,
        account_type=data.account_type,
        currency=data.currency,
        purpose=data.purpose,
    )
    return handle_provider_result(result, "solaris")


@router.post(
    "/solaris/overdrafts",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Demander un découvert Solaris",
    description="Soumet une demande de découvert autorisé.",
)
async def create_solaris_overdraft(
    data: OverdraftRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Crée une demande de découvert Solaris."""
    provider = await registry.get_provider(FinanceProviderType.SOLARIS)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider Solaris non configuré",
        )

    result = await provider.create_overdraft_application(
        account_id=data.account_id,
        amount=int(data.amount),
        duration_days=data.duration_days,
        purpose=data.purpose,
    )
    return handle_provider_result(result, "solaris")


@router.post(
    "/solaris/transfers",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un virement Solaris",
    description="Initie un virement SEPA via Solaris Bank.",
)
async def create_solaris_transfer(
    data: SolarisTransferRequest,
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Crée un virement Solaris."""
    provider = await registry.get_provider(FinanceProviderType.SOLARIS)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider Solaris non configuré",
        )

    result = await provider.create_transfer(
        account_id=data.account_id,
        recipient_iban=data.recipient_iban,
        recipient_name=data.recipient_name,
        amount=int(data.amount),
        currency=data.currency,
        reference=data.reference,
    )
    return handle_provider_result(result, "solaris")


# =============================================================================
# HEALTH CHECK
# =============================================================================


@router.get(
    "/health",
    summary="Health check providers",
    description="Vérifie l'état des providers finance.",
)
async def health_check(
    registry: FinanceProviderRegistry = Depends(get_provider_registry),
):
    """Health check pour les providers finance."""
    providers_status = {}

    for provider_type in FinanceProviderType:
        try:
            provider = await registry.get_provider(provider_type)
            providers_status[provider_type.value] = "configured" if provider else "not_configured"
        except Exception as e:
            providers_status[provider_type.value] = f"error: {str(e)}"

    return {
        "status": "healthy",
        "service": "finance-providers",
        "providers": providers_status,
    }
