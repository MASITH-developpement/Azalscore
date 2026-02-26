"""
AZALS MODULE - CURRENCY: Router API
====================================

Endpoints REST pour la gestion multi-devises.
"""
from __future__ import annotations


import math
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .models import RateSource, RateType, GainLossType, RevaluationStatus
from .schemas import (
    # Currency
    CurrencyCreate, CurrencyUpdate, CurrencyResponse,
    CurrencyList, CurrencyListItem, CurrencyFilters,
    # Rates
    ExchangeRateCreate, ExchangeRateUpdate, ExchangeRateResponse,
    ExchangeRateList, ExchangeRateListItem, ExchangeRateFilters,
    RateHistoryResponse, BulkRateUpdateRequest, BulkRateUpdateResponse,
    RateFetchRequest, RateFetchResult,
    # Conversion
    ConversionRequest, ConversionResult,
    MultiConversionRequest, MultiConversionResult,
    # Config
    CurrencyConfigCreate, CurrencyConfigUpdate, CurrencyConfigResponse,
    # Gain/Loss
    ExchangeGainLossResponse, ExchangeGainLossList, ExchangeGainLossSummary,
    GainLossFilters,
    # Revaluation
    RevaluationCreate, RevaluationResponse, RevaluationPreview,
    # Alerts
    RateAlertResponse,
    # Common
    AutocompleteResponse, AutocompleteItem
)
from .service import CurrencyService, create_currency_service
from .exceptions import (
    CurrencyNotFoundError, CurrencyAlreadyExistsError, CurrencyDisabledError,
    ExchangeRateNotFoundError, InvalidExchangeRateError,
    RateAPIError, RateToleranceExceededError
)


router = APIRouter(prefix="/currencies", tags=["Currencies"])


# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_currency_service(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
) -> CurrencyService:
    """Dependency pour obtenir le service currency."""
    return create_currency_service(db, str(current_user.tenant_id))


# ============================================================================
# CURRENCIES
# ============================================================================

@router.get("", response_model=CurrencyList)
async def list_currencies(
    search: Optional[str] = Query(None, min_length=1),
    is_enabled: Optional[bool] = Query(None),
    is_major: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.read"))
):
    """Lister les devises."""
    filters = CurrencyFilters(
        search=search,
        is_enabled=is_enabled,
        is_major=is_major
    )
    items, total = service.currency_repo.list(filters, page, page_size)

    return CurrencyList(
        items=[CurrencyListItem(
            id=c.id,
            code=c.code,
            name=c.name,
            symbol=c.symbol,
            decimals=c.decimals,
            is_enabled=c.is_enabled,
            is_default=c.is_default,
            is_reporting=c.is_reporting,
            is_major=c.is_major,
            status=c.status
        ) for c in items],
        total=total
    )


@router.get("/enabled", response_model=List[CurrencyListItem])
async def list_enabled_currencies(
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.read"))
):
    """Lister les devises actives."""
    currencies = service.list_currencies(enabled_only=True)
    return [CurrencyListItem(
        id=c.id,
        code=c.code,
        name=c.name,
        symbol=c.symbol,
        decimals=c.decimals,
        is_enabled=c.is_enabled,
        is_default=c.is_default,
        is_reporting=c.is_reporting,
        is_major=c.is_major,
        status=c.status
    ) for c in currencies]


@router.get("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_currencies(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.read"))
):
    """Autocomplete devises."""
    results = service.currency_repo.autocomplete(q, limit)
    return AutocompleteResponse(items=[AutocompleteItem(**r) for r in results])


@router.get("/default", response_model=CurrencyResponse)
async def get_default_currency(
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.read"))
):
    """Obtenir la devise par defaut."""
    try:
        currency = service.get_default_currency()
        return currency
    except CurrencyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/reporting", response_model=CurrencyResponse)
async def get_reporting_currency(
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.read"))
):
    """Obtenir la devise de reporting."""
    currency = service.get_reporting_currency()
    return currency


@router.get("/{code}", response_model=CurrencyResponse)
async def get_currency(
    code: str,
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.read"))
):
    """Obtenir une devise par code."""
    try:
        currency = service.get_currency(code)
        return currency
    except CurrencyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=CurrencyResponse, status_code=status.HTTP_201_CREATED)
async def create_currency(
    data: CurrencyCreate,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.create"))
):
    """Creer une devise."""
    try:
        currency = service.create_currency(
            code=data.code,
            name=data.name,
            symbol=data.symbol,
            decimals=data.decimals,
            created_by=current_user.id,
            **data.model_dump(exclude={"code", "name", "symbol", "decimals"})
        )
        return currency
    except CurrencyAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/{code}", response_model=CurrencyResponse)
async def update_currency(
    code: str,
    data: CurrencyUpdate,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.update"))
):
    """Mettre a jour une devise."""
    try:
        currency = service.get_currency(code)
        updated = service.currency_repo.update(
            currency,
            data.model_dump(exclude_unset=True),
            current_user.id
        )
        return updated
    except CurrencyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{code}/enable", response_model=CurrencyResponse)
async def enable_currency(
    code: str,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.update"))
):
    """Activer une devise."""
    try:
        currency = service.enable_currency(code, current_user.id)
        return currency
    except CurrencyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{code}/disable", response_model=CurrencyResponse)
async def disable_currency(
    code: str,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.update"))
):
    """Desactiver une devise."""
    try:
        currency = service.disable_currency(code, current_user.id)
        return currency
    except CurrencyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{code}/set-default", response_model=CurrencyResponse)
async def set_default_currency(
    code: str,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.admin"))
):
    """Definir comme devise par defaut."""
    try:
        currency = service.set_default_currency(code, current_user.id)
        return currency
    except CurrencyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{code}/set-reporting", response_model=CurrencyResponse)
async def set_reporting_currency(
    code: str,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.admin"))
):
    """Definir comme devise de reporting."""
    try:
        currency = service.set_reporting_currency(code, current_user.id)
        return currency
    except CurrencyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/initialize", status_code=status.HTTP_201_CREATED)
async def initialize_currencies(
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.admin"))
):
    """Initialiser les devises ISO 4217."""
    created = service.initialize_iso_currencies(current_user.id)
    return {"message": f"{created} devises creees"}


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_currency(
    code: str,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.delete"))
):
    """Supprimer une devise (soft delete)."""
    try:
        currency = service.get_currency(code)
        service.currency_repo.soft_delete(currency, current_user.id)
    except CurrencyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# EXCHANGE RATES
# ============================================================================

@router.get("/rates", response_model=ExchangeRateList)
async def list_rates(
    base: Optional[str] = Query(None, min_length=3, max_length=3),
    quote: Optional[str] = Query(None, min_length=3, max_length=3),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    rate_type: Optional[RateType] = Query(None),
    source: Optional[RateSource] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.rate.read"))
):
    """Lister les taux de change."""
    filters = ExchangeRateFilters(
        base_currency=base,
        quote_currency=quote,
        date_from=date_from,
        date_to=date_to,
        rate_type=rate_type,
        source=source
    )
    items, total = service.rate_repo.list(filters, page, page_size)

    return ExchangeRateList(
        items=[ExchangeRateListItem(
            id=r.id,
            base_currency_code=r.base_currency_code,
            quote_currency_code=r.quote_currency_code,
            rate=r.rate,
            rate_date=r.rate_date,
            rate_type=RateType(r.rate_type),
            source=RateSource(r.source),
            is_manual=r.is_manual
        ) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/rates/{base}/{quote}", response_model=ExchangeRateResponse)
async def get_rate(
    base: str,
    quote: str,
    rate_date: Optional[date] = Query(None),
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.rate.read"))
):
    """Obtenir un taux de change."""
    rate = service.get_rate(base, quote, rate_date)
    if not rate:
        raise HTTPException(
            status_code=404,
            detail=f"Taux de change non trouve: {base}/{quote}"
        )
    return rate


@router.get("/rates/{base}/{quote}/history", response_model=RateHistoryResponse)
async def get_rate_history(
    base: str,
    quote: str,
    start_date: date = Query(...),
    end_date: Optional[date] = Query(None),
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.rate.read"))
):
    """Historique d'un taux de change."""
    end_date = end_date or date.today()
    history = service.get_rate_history(base, quote, start_date, end_date)

    if history:
        rates = [h.rate for h in history]
        avg_rate = sum(rates) / len(rates)
        min_rate = min(rates)
        max_rate = max(rates)
    else:
        avg_rate = min_rate = max_rate = None

    return RateHistoryResponse(
        base_currency=base.upper(),
        quote_currency=quote.upper(),
        start_date=start_date,
        end_date=end_date,
        history=history,
        average_rate=avg_rate,
        min_rate=min_rate,
        max_rate=max_rate
    )


@router.post("/rates", response_model=ExchangeRateResponse, status_code=status.HTTP_201_CREATED)
async def create_rate(
    data: ExchangeRateCreate,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.rate.create"))
):
    """Creer un taux de change."""
    try:
        rate = service.set_rate(
            base=data.base_currency_code,
            quote=data.quote_currency_code,
            rate=data.rate,
            rate_date=data.rate_date,
            rate_type=data.rate_type,
            source=data.source,
            created_by=current_user.id
        )
        return rate
    except (InvalidExchangeRateError, RateToleranceExceededError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CurrencyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/rates/{rate_id}", response_model=ExchangeRateResponse)
async def update_rate(
    rate_id: UUID,
    data: ExchangeRateUpdate,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.rate.update"))
):
    """Mettre a jour un taux de change."""
    rate = service.rate_repo.get_by_id(rate_id)
    if not rate:
        raise HTTPException(status_code=404, detail="Taux non trouve")

    try:
        updated = service.rate_repo.update(
            rate,
            data.model_dump(exclude_unset=True),
            current_user.id
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rates/bulk", response_model=BulkRateUpdateResponse)
async def bulk_update_rates(
    data: BulkRateUpdateRequest,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.rate.create"))
):
    """Mise a jour en masse des taux."""
    created = 0
    updated = 0
    errors = []

    for rate_data in data.rates:
        try:
            existing = service.rate_repo.get_rate_exact_date(
                rate_data.base_currency_code,
                rate_data.quote_currency_code,
                rate_data.rate_date
            )

            if existing:
                if data.overwrite_existing:
                    service.rate_repo.update(existing, {"rate": rate_data.rate}, current_user.id)
                    updated += 1
            else:
                service.set_rate(
                    rate_data.base_currency_code,
                    rate_data.quote_currency_code,
                    rate_data.rate,
                    rate_data.rate_date,
                    rate_data.rate_type,
                    data.source,
                    current_user.id
                )
                created += 1
        except Exception as e:
            errors.append({
                "pair": f"{rate_data.base_currency_code}/{rate_data.quote_currency_code}",
                "error": str(e)
            })

    return BulkRateUpdateResponse(created=created, updated=updated, errors=errors)


@router.post("/rates/fetch", response_model=RateFetchResult)
async def fetch_rates(
    data: RateFetchRequest,
    background_tasks: BackgroundTasks,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.rate.fetch"))
):
    """Recuperer les taux depuis une source externe."""
    import asyncio

    try:
        if data.source == RateSource.ECB:
            rates_saved = asyncio.get_event_loop().run_until_complete(
                service.fetch_rates_from_ecb(data.rate_date, current_user.id)
            )
        else:
            config = service.get_config()
            api_key = config.api_keys.get(data.source.value)
            if not api_key:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cle API non configuree pour {data.source.value}"
                )

            if data.source == RateSource.OPENEXCHANGE:
                rates_saved = asyncio.get_event_loop().run_until_complete(
                    service.fetch_rates_from_openexchange(
                        api_key, data.base_currency, data.rate_date, current_user.id
                    )
                )
            elif data.source == RateSource.FIXER:
                rates_saved = asyncio.get_event_loop().run_until_complete(
                    service.fetch_rates_from_fixer(
                        api_key, data.base_currency, data.currencies, data.rate_date, current_user.id
                    )
                )
            else:
                raise HTTPException(status_code=400, detail="Source non supportee")

        return RateFetchResult(
            source=data.source,
            fetch_date=datetime.utcnow(),
            rate_date=data.rate_date or date.today(),
            rates_fetched=rates_saved,
            rates_saved=rates_saved,
            errors=[]
        )

    except RateAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/rates/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate(
    rate_id: UUID,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.rate.delete"))
):
    """Supprimer un taux de change."""
    rate = service.rate_repo.get_by_id(rate_id)
    if not rate:
        raise HTTPException(status_code=404, detail="Taux non trouve")
    service.rate_repo.soft_delete(rate, current_user.id)


# ============================================================================
# CONVERSION
# ============================================================================

@router.post("/convert", response_model=ConversionResult)
async def convert_amount(
    data: ConversionRequest,
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.convert"))
):
    """Convertir un montant."""
    try:
        result = service.convert(
            amount=data.amount,
            from_currency=data.from_currency,
            to_currency=data.to_currency,
            rate_date=data.rate_date,
            rate_type=data.rate_type
        )
        return result
    except ExchangeRateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/convert/multiple", response_model=MultiConversionResult)
async def convert_multiple_amounts(
    data: MultiConversionRequest,
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.convert"))
):
    """Convertir plusieurs montants."""
    try:
        conversions, total = service.convert_multiple(
            data.amounts,
            data.target_currency,
            data.rate_date
        )
        return MultiConversionResult(
            conversions=conversions,
            total_in_target=total,
            target_currency=data.target_currency
        )
    except ExchangeRateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# CONFIGURATION
# ============================================================================

@router.get("/config", response_model=CurrencyConfigResponse)
async def get_config(
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.config.read"))
):
    """Obtenir la configuration."""
    return service.get_config()


@router.put("/config", response_model=CurrencyConfigResponse)
async def update_config(
    data: CurrencyConfigUpdate,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.config.update"))
):
    """Mettre a jour la configuration."""
    config = service.update_config(data.model_dump(exclude_unset=True), current_user.id)
    return config


# ============================================================================
# GAINS/PERTES DE CHANGE
# ============================================================================

@router.get("/gains-losses", response_model=ExchangeGainLossList)
async def list_gains_losses(
    gain_loss_type: Optional[GainLossType] = Query(None),
    document_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    is_posted: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.gainloss.read"))
):
    """Lister les gains/pertes de change."""
    filters = GainLossFilters(
        gain_loss_type=gain_loss_type,
        document_type=document_type,
        date_from=date_from,
        date_to=date_to,
        is_posted=is_posted
    )
    items, total = service.gain_loss_repo.list(filters, page, page_size)

    return ExchangeGainLossList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/gains-losses/summary", response_model=ExchangeGainLossSummary)
async def get_gains_losses_summary(
    start_date: date = Query(...),
    end_date: date = Query(...),
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.gainloss.read"))
):
    """Resume des gains/pertes de change."""
    return service.get_gain_loss_summary(start_date, end_date)


# ============================================================================
# REEVALUATION
# ============================================================================

@router.get("/revaluations", response_model=List[RevaluationResponse])
async def list_revaluations(
    status: Optional[RevaluationStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.revaluation.read"))
):
    """Lister les reevaluations."""
    items, _ = service.revaluation_repo.list(page, page_size, status)
    return items


@router.get("/revaluations/{revaluation_id}", response_model=RevaluationResponse)
async def get_revaluation(
    revaluation_id: UUID,
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.revaluation.read"))
):
    """Obtenir une reevaluation."""
    revaluation = service.revaluation_repo.get_by_id(revaluation_id)
    if not revaluation:
        raise HTTPException(status_code=404, detail="Reevaluation non trouvee")
    return revaluation


@router.post("/revaluations/preview", response_model=RevaluationPreview)
async def preview_revaluation(
    revaluation_date: date = Query(...),
    currencies: Optional[List[str]] = Query(None),
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.revaluation.create"))
):
    """Apercu d'une reevaluation."""
    return service.preview_revaluation(revaluation_date, currencies)


@router.post("/revaluations", response_model=RevaluationResponse, status_code=status.HTTP_201_CREATED)
async def create_revaluation(
    data: RevaluationCreate,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.revaluation.create"))
):
    """Creer une reevaluation."""
    try:
        revaluation = service.create_revaluation(
            name=data.name,
            revaluation_date=data.revaluation_date,
            period=data.period,
            currencies=data.currencies_to_revalue,
            created_by=current_user.id
        )
        return revaluation
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/revaluations/{revaluation_id}/post", response_model=RevaluationResponse)
async def post_revaluation(
    revaluation_id: UUID,
    journal_entry_id: UUID = Query(...),
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.revaluation.post"))
):
    """Comptabiliser une reevaluation."""
    try:
        revaluation = service.post_revaluation(
            revaluation_id, journal_entry_id, current_user.id
        )
        return revaluation
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/revaluations/{revaluation_id}/cancel", response_model=RevaluationResponse)
async def cancel_revaluation(
    revaluation_id: UUID,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.revaluation.cancel"))
):
    """Annuler une reevaluation."""
    revaluation = service.revaluation_repo.get_by_id(revaluation_id)
    if not revaluation:
        raise HTTPException(status_code=404, detail="Reevaluation non trouvee")

    return service.revaluation_repo.cancel(revaluation, current_user.id)


# ============================================================================
# ALERTS
# ============================================================================

@router.get("/alerts", response_model=List[RateAlertResponse])
async def list_alerts(
    unread_only: bool = Query(False),
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.alert.read"))
):
    """Lister les alertes de taux."""
    if unread_only:
        return service.alert_repo.list_unread()
    return service.alert_repo.list_unacknowledged()


@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: UUID,
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.alert.read"))
):
    """Marquer une alerte comme lue."""
    alert = service.alert_repo.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvee")
    service.alert_repo.mark_read(alert)
    return {"status": "ok"}


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    service: CurrencyService = Depends(get_currency_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("currency.alert.acknowledge"))
):
    """Acquitter une alerte."""
    alert = service.alert_repo.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvee")
    service.alert_repo.acknowledge(alert, current_user.id)
    return {"status": "ok"}


@router.post("/alerts/mark-all-read")
async def mark_all_alerts_read(
    service: CurrencyService = Depends(get_currency_service),
    _: None = Depends(require_permission("currency.alert.read"))
):
    """Marquer toutes les alertes comme lues."""
    count = service.alert_repo.mark_all_read()
    return {"marked_read": count}
