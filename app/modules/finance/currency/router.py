"""
AZALSCORE Finance Currency Router V3
=====================================

Endpoints REST pour la gestion des devises.

Endpoints:
- GET  /v3/finance/currency/rate - Obtenir un taux de change
- GET  /v3/finance/currency/rates - Obtenir tous les taux
- POST /v3/finance/currency/convert - Convertir un montant
- POST /v3/finance/currency/convert-batch - Conversions par lot
- POST /v3/finance/currency/rate - Définir un taux manuel
- GET  /v3/finance/currency/currencies - Liste des devises
- GET  /v3/finance/currency/currency/{code} - Infos d'une devise
- GET  /v3/finance/currency/health - Health check
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import SaaSContext
from app.core.dependencies_v2 import get_saas_context

from .service import (
    CurrencyService,
    ExchangeRate,
    RateSource,
    SupportedCurrencies,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3/finance/currency", tags=["Finance Currency"])


# =============================================================================
# SCHEMAS
# =============================================================================


class ExchangeRateResponse(BaseModel):
    """Taux de change."""

    id: str
    base_currency: str
    target_currency: str
    rate: Decimal
    inverse_rate: Decimal
    date: str
    source: str


class ConversionRequest(BaseModel):
    """Requête de conversion."""

    amount: Decimal = Field(..., description="Montant à convertir")
    from_currency: str = Field(..., min_length=3, max_length=3, description="Devise source (ex: EUR)")
    to_currency: str = Field(..., min_length=3, max_length=3, description="Devise cible (ex: USD)")
    rate_date: Optional[str] = Field(None, description="Date du taux (YYYY-MM-DD)")


class ConversionResponse(BaseModel):
    """Résultat de conversion."""

    success: bool
    source_amount: Optional[Decimal] = None
    source_currency: Optional[str] = None
    target_amount: Optional[Decimal] = None
    target_currency: Optional[str] = None
    rate_used: Optional[Decimal] = None
    rate_date: Optional[str] = None
    rate_source: Optional[str] = None
    error: Optional[str] = None


class BatchConversionRequest(BaseModel):
    """Requête de conversion par lot."""

    conversions: list[ConversionRequest]


class BatchConversionResponse(BaseModel):
    """Réponse de conversion par lot."""

    total: int
    successful: int
    failed: int
    results: list[ConversionResponse] = Field(default_factory=list)


class ManualRateRequest(BaseModel):
    """Requête de taux manuel."""

    from_currency: str = Field(..., min_length=3, max_length=3)
    to_currency: str = Field(..., min_length=3, max_length=3)
    rate: Decimal = Field(..., gt=0)
    rate_date: Optional[str] = None


class CurrencyInfo(BaseModel):
    """Informations devise."""

    code: str
    name: str
    symbol: str
    decimals: int


class CurrencyListResponse(BaseModel):
    """Liste des devises."""

    total: int
    currencies: list[CurrencyInfo] = Field(default_factory=list)


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_currency_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> CurrencyService:
    """Dépendance pour obtenir le service de devises."""
    return CurrencyService(db=db, tenant_id=context.tenant_id)


# =============================================================================
# HELPERS
# =============================================================================


def rate_to_response(rate: ExchangeRate) -> ExchangeRateResponse:
    """Convertit un ExchangeRate en réponse."""
    return ExchangeRateResponse(
        id=rate.id,
        base_currency=rate.base_currency,
        target_currency=rate.target_currency,
        rate=rate.rate,
        inverse_rate=rate.inverse_rate,
        date=rate.date.isoformat(),
        source=rate.source.value,
    )


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get(
    "/rate",
    response_model=ExchangeRateResponse,
    summary="Obtenir un taux de change",
    description="Retourne le taux de change entre deux devises.",
)
async def get_rate(
    from_currency: str = Query(..., min_length=3, max_length=3, description="Devise source"),
    to_currency: str = Query(..., min_length=3, max_length=3, description="Devise cible"),
    rate_date: Optional[str] = Query(None, description="Date du taux (YYYY-MM-DD)"),
    service: CurrencyService = Depends(get_currency_service),
):
    """
    Récupère le taux de change entre deux devises.

    Sources de taux (par priorité):
    1. Cache local
    2. API Banque Centrale Européenne
    3. Taux de fallback intégrés
    """
    parsed_date = None
    if rate_date:
        try:
            parsed_date = date.fromisoformat(rate_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format de date invalide. Utilisez YYYY-MM-DD",
            )

    rate = await service.get_rate(
        from_currency.upper(),
        to_currency.upper(),
        parsed_date,
    )

    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Taux non disponible pour {from_currency}/{to_currency}",
        )

    return rate_to_response(rate)


@router.get(
    "/rates",
    response_model=list[ExchangeRateResponse],
    summary="Obtenir tous les taux de change",
    description="Retourne tous les taux de change pour une date donnée.",
)
async def get_rates(
    rate_date: Optional[str] = Query(None, description="Date des taux (YYYY-MM-DD)"),
    currencies: Optional[str] = Query(None, description="Liste de devises (séparées par virgule)"),
    service: CurrencyService = Depends(get_currency_service),
):
    """
    Récupère tous les taux de change par rapport à l'EUR.

    Paramètres:
    - **rate_date**: Date des taux (défaut: aujourd'hui)
    - **currencies**: Filtrer par devises (ex: USD,GBP,CHF)
    """
    parsed_date = date.today()
    if rate_date:
        try:
            parsed_date = date.fromisoformat(rate_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format de date invalide. Utilisez YYYY-MM-DD",
            )

    currency_list = None
    if currencies:
        currency_list = [c.strip().upper() for c in currencies.split(",")]

    rates = await service.get_rates_for_date(parsed_date, currency_list)
    return [rate_to_response(r) for r in rates]


@router.post(
    "/convert",
    response_model=ConversionResponse,
    summary="Convertir un montant",
    description="Convertit un montant d'une devise à une autre.",
)
async def convert_amount(
    request: ConversionRequest,
    service: CurrencyService = Depends(get_currency_service),
):
    """
    Convertit un montant entre deux devises.

    Utilise le taux de change du jour ou de la date spécifiée.
    L'arrondi est effectué selon le nombre de décimales de la devise cible.
    """
    parsed_date = None
    if request.rate_date:
        try:
            parsed_date = date.fromisoformat(request.rate_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format de date invalide. Utilisez YYYY-MM-DD",
            )

    result = await service.convert(
        amount=request.amount,
        from_currency=request.from_currency.upper(),
        to_currency=request.to_currency.upper(),
        rate_date=parsed_date,
    )

    if not result.success:
        return ConversionResponse(
            success=False,
            error=result.error,
        )

    conv = result.conversion
    return ConversionResponse(
        success=True,
        source_amount=conv.source_amount,
        source_currency=conv.source_currency,
        target_amount=conv.target_amount,
        target_currency=conv.target_currency,
        rate_used=conv.rate_used,
        rate_date=conv.rate_date.isoformat(),
        rate_source=conv.rate_source.value,
    )


@router.post(
    "/convert-batch",
    response_model=BatchConversionResponse,
    summary="Conversions par lot",
    description="Convertit plusieurs montants en une seule requête.",
)
async def convert_batch(
    request: BatchConversionRequest,
    service: CurrencyService = Depends(get_currency_service),
):
    """
    Convertit un lot de montants.

    Utile pour traiter plusieurs conversions simultanément.
    """
    conversions_data = []
    for conv in request.conversions:
        parsed_date = None
        if conv.rate_date:
            try:
                parsed_date = date.fromisoformat(conv.rate_date)
            except ValueError:
                pass

        conversions_data.append({
            "amount": conv.amount,
            "from_currency": conv.from_currency.upper(),
            "to_currency": conv.to_currency.upper(),
            "rate_date": parsed_date,
        })

    results = await service.convert_batch(conversions_data)

    responses = []
    successful = 0
    failed = 0

    for result in results:
        if result.success and result.conversion:
            conv = result.conversion
            responses.append(ConversionResponse(
                success=True,
                source_amount=conv.source_amount,
                source_currency=conv.source_currency,
                target_amount=conv.target_amount,
                target_currency=conv.target_currency,
                rate_used=conv.rate_used,
                rate_date=conv.rate_date.isoformat(),
                rate_source=conv.rate_source.value,
            ))
            successful += 1
        else:
            responses.append(ConversionResponse(
                success=False,
                error=result.error,
            ))
            failed += 1

    return BatchConversionResponse(
        total=len(results),
        successful=successful,
        failed=failed,
        results=responses,
    )


@router.post(
    "/rate",
    response_model=ExchangeRateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Définir un taux manuel",
    description="Définit un taux de change manuel.",
)
async def set_manual_rate(
    request: ManualRateRequest,
    service: CurrencyService = Depends(get_currency_service),
):
    """
    Définit un taux de change manuel.

    Ce taux sera utilisé en priorité pour les conversions.
    Utile pour les devises exotiques ou les taux négociés.
    """
    parsed_date = None
    if request.rate_date:
        try:
            parsed_date = date.fromisoformat(request.rate_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format de date invalide. Utilisez YYYY-MM-DD",
            )

    rate = await service.set_manual_rate(
        from_currency=request.from_currency.upper(),
        to_currency=request.to_currency.upper(),
        rate=request.rate,
        rate_date=parsed_date,
    )

    return rate_to_response(rate)


@router.get(
    "/currencies",
    response_model=CurrencyListResponse,
    summary="Liste des devises supportées",
    description="Retourne la liste de toutes les devises supportées.",
)
async def list_currencies(
    service: CurrencyService = Depends(get_currency_service),
):
    """
    Retourne la liste des devises supportées.

    Chaque devise inclut:
    - Code ISO 4217 (ex: EUR, USD)
    - Nom complet
    - Symbole
    - Nombre de décimales
    """
    currencies = service.get_supported_currencies()
    return CurrencyListResponse(
        total=len(currencies),
        currencies=[CurrencyInfo(**c) for c in currencies],
    )


@router.get(
    "/currency/{code}",
    response_model=CurrencyInfo,
    summary="Informations d'une devise",
    description="Retourne les informations d'une devise spécifique.",
)
async def get_currency_info(
    code: str,
    service: CurrencyService = Depends(get_currency_service),
):
    """
    Retourne les informations détaillées d'une devise.
    """
    info = service.get_currency_info(code.upper())

    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Devise non trouvée: {code}",
        )

    return CurrencyInfo(**info)


@router.get(
    "/format",
    summary="Formater un montant",
    description="Formate un montant avec sa devise.",
)
async def format_amount(
    amount: Decimal = Query(..., description="Montant à formater"),
    currency: str = Query(..., min_length=3, max_length=3, description="Code devise"),
    include_symbol: bool = Query(True, description="Inclure le symbole"),
    service: CurrencyService = Depends(get_currency_service),
):
    """
    Formate un montant selon les conventions de sa devise.

    Exemple: 1234.56 EUR -> €1234.56
    """
    formatted = service.format_amount(amount, currency.upper(), include_symbol)
    return {
        "amount": amount,
        "currency": currency.upper(),
        "formatted": formatted,
    }


@router.get(
    "/health",
    summary="Health check devises",
    description="Vérifie que le service de devises est fonctionnel.",
)
async def health_check():
    """Health check pour le service de devises."""
    return {
        "status": "healthy",
        "service": "finance-currency",
        "base_currency": "EUR",
        "supported_currencies": len(SupportedCurrencies.CURRENCIES),
        "features": [
            "ecb_rates",
            "manual_rates",
            "conversion",
            "batch_conversion",
            "exchange_gain_loss",
            "rate_caching",
        ],
        "rate_sources": ["ecb", "manual", "fallback"],
    }
