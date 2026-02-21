"""
AZALS MODULE GATEWAY - Router API
===================================

Endpoints REST pour le module Gateway.
Documentation OpenAPI auto-generee.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.compat import get_context
from app.core.database import get_db
from app.core.pagination import PaginatedResponse
from app.core.saas_context import SaaSContext

from .models import (
    EndpointType,
    HttpMethod,
    PlanTier,
    QuotaPeriod,
    WebhookEventType,
    WebhookStatus,
)
from .schemas import (
    ApiKeyCreateSchema,
    ApiKeyCreatedResponseSchema,
    ApiKeyResponseSchema,
    ApiKeyRevokeSchema,
    ApiKeyUpdateSchema,
    ApiPlanCreateSchema,
    ApiPlanResponseSchema,
    ApiPlanUpdateSchema,
    CircuitBreakerStatusSchema,
    EndpointCreateSchema,
    EndpointResponseSchema,
    EndpointUpdateSchema,
    GatewayDashboardSchema,
    GatewayStatsSchema,
    MetricsQuerySchema,
    MetricsResponseSchema,
    OAuthClientCreateSchema,
    OAuthClientCreatedResponseSchema,
    OAuthClientResponseSchema,
    OAuthTokenRequestSchema,
    OAuthTokenResponseSchema,
    OpenApiGenerationRequestSchema,
    OpenApiSpecResponseSchema,
    QuotaUsageResponseSchema,
    RateLimitStatusSchema,
    RequestLogResponseSchema,
    TransformationCreateSchema,
    TransformationResponseSchema,
    TransformationUpdateSchema,
    WebhookCreateSchema,
    WebhookDeliveryResponseSchema,
    WebhookResponseSchema,
    WebhookTestResponseSchema,
    WebhookTestSchema,
    WebhookUpdateSchema,
)
from .service import GatewayService, create_gateway_service

router = APIRouter(prefix="/gateway", tags=["API Gateway"])


def get_gateway_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
) -> GatewayService:
    """Factory pour le service Gateway."""
    return create_gateway_service(db, context)


# ============================================================================
# API PLANS
# ============================================================================

@router.post(
    "/plans",
    response_model=ApiPlanResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Creer un plan API",
    description="Cree un nouveau plan API avec quotas et tarification."
)
async def create_plan(
    data: ApiPlanCreateSchema,
    service: GatewayService = Depends(get_gateway_service)
):
    """Cree un plan API."""
    result = service.create_plan(data)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if result.error_code == "DUPLICATE" else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error
        )
    return result.data


@router.get(
    "/plans",
    response_model=PaginatedResponse[ApiPlanResponseSchema],
    summary="Lister les plans API"
)
async def list_plans(
    tier: Optional[PlanTier] = Query(None, description="Filtrer par niveau"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: GatewayService = Depends(get_gateway_service)
):
    """Liste les plans API."""
    result = service.list_plans(tier, page, page_size)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    plans, total = result.data
    pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=plans,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )


@router.get(
    "/plans/{plan_id}",
    response_model=ApiPlanResponseSchema,
    summary="Recuperer un plan API"
)
async def get_plan(
    plan_id: UUID,
    service: GatewayService = Depends(get_gateway_service)
):
    """Recupere un plan par ID."""
    result = service.get_plan(plan_id)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.error)
    return result.data


@router.put(
    "/plans/{plan_id}",
    response_model=ApiPlanResponseSchema,
    summary="Mettre a jour un plan API"
)
async def update_plan(
    plan_id: UUID,
    data: ApiPlanUpdateSchema,
    service: GatewayService = Depends(get_gateway_service)
):
    """Met a jour un plan."""
    result = service.update_plan(plan_id, data)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if result.error_code == "NOT_FOUND" else status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )
    return result.data


@router.delete(
    "/plans/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un plan API"
)
async def delete_plan(
    plan_id: UUID,
    service: GatewayService = Depends(get_gateway_service)
):
    """Supprime un plan (soft delete)."""
    result = service.delete_plan(plan_id)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if result.error_code == "NOT_FOUND" else status.HTTP_409_CONFLICT,
            detail=result.error
        )
    return None


# ============================================================================
# API KEYS
# ============================================================================

@router.post(
    "/keys",
    response_model=ApiKeyCreatedResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Creer une cle API",
    description="Cree une nouvelle cle API. La cle complete n'est affichee qu'une seule fois."
)
async def create_api_key(
    data: ApiKeyCreateSchema,
    service: GatewayService = Depends(get_gateway_service)
):
    """Cree une cle API."""
    result = service.create_api_key(data)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.error)

    api_key, full_key = result.data
    return ApiKeyCreatedResponseSchema(
        **ApiKeyResponseSchema.model_validate(api_key).model_dump(),
        api_key=full_key
    )


@router.get(
    "/keys",
    response_model=PaginatedResponse[ApiKeyResponseSchema],
    summary="Lister les cles API"
)
async def list_api_keys(
    client_id: Optional[str] = Query(None, description="Filtrer par client"),
    user_id: Optional[UUID] = Query(None, description="Filtrer par utilisateur"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: GatewayService = Depends(get_gateway_service)
):
    """Liste les cles API."""
    result = service.list_api_keys(client_id, user_id, page, page_size)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    keys, total = result.data
    pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=keys,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )


@router.get(
    "/keys/{key_id}",
    response_model=ApiKeyResponseSchema,
    summary="Recuperer une cle API"
)
async def get_api_key(
    key_id: UUID,
    service: GatewayService = Depends(get_gateway_service)
):
    """Recupere une cle par ID."""
    result = service.get_api_key(key_id)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.error)
    return result.data


@router.put(
    "/keys/{key_id}",
    response_model=ApiKeyResponseSchema,
    summary="Mettre a jour une cle API"
)
async def update_api_key(
    key_id: UUID,
    data: ApiKeyUpdateSchema,
    service: GatewayService = Depends(get_gateway_service)
):
    """Met a jour une cle."""
    result = service.update_api_key(key_id, data)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if result.error_code == "NOT_FOUND" else status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )
    return result.data


@router.post(
    "/keys/{key_id}/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoquer une cle API"
)
async def revoke_api_key(
    key_id: UUID,
    data: ApiKeyRevokeSchema = ApiKeyRevokeSchema(),
    service: GatewayService = Depends(get_gateway_service)
):
    """Revoque une cle API."""
    result = service.revoke_api_key(key_id, data.reason)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.error)
    return None


@router.get(
    "/keys/{key_id}/quota",
    response_model=List[QuotaUsageResponseSchema],
    summary="Recuperer l'utilisation des quotas"
)
async def get_key_quota(
    key_id: UUID,
    service: GatewayService = Depends(get_gateway_service)
):
    """Recupere l'utilisation des quotas pour une cle."""
    key_result = service.get_api_key(key_id)
    if not key_result.success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=key_result.error)

    plan_result = service.get_plan(key_result.data.plan_id)
    if not plan_result.success:
        raise HTTPException(status_code=500, detail="Plan not found")

    quota_result = service.check_quota(key_result.data, plan_result.data)
    if not quota_result.success:
        # Quota depasse mais on retourne quand meme les infos
        pass

    quotas = quota_result.data if quota_result.success else {}

    response = []
    for period, quota in quotas.items():
        remaining = max(0, quota.requests_limit - quota.requests_count)
        usage_pct = (quota.requests_count / quota.requests_limit * 100) if quota.requests_limit > 0 else 0

        response.append(QuotaUsageResponseSchema(
            period=period,
            period_start=quota.period_start,
            period_end=quota.period_end,
            requests_count=quota.requests_count,
            requests_limit=quota.requests_limit,
            requests_remaining=remaining,
            usage_percentage=round(usage_pct, 2),
            bytes_in=quota.bytes_in,
            bytes_out=quota.bytes_out,
            error_count=quota.error_count,
            is_exceeded=quota.is_exceeded,
            exceeded_at=quota.exceeded_at,
            overage_count=quota.overage_count,
            overage_amount=quota.overage_amount
        ))

    return response


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/endpoints",
    response_model=EndpointResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Creer un endpoint"
)
async def create_endpoint(
    data: EndpointCreateSchema,
    service: GatewayService = Depends(get_gateway_service)
):
    """Cree un endpoint."""
    result = service.create_endpoint(data)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.error)
    return result.data


@router.get(
    "/endpoints",
    response_model=PaginatedResponse[EndpointResponseSchema],
    summary="Lister les endpoints"
)
async def list_endpoints(
    endpoint_type: Optional[EndpointType] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: GatewayService = Depends(get_gateway_service)
):
    """Liste les endpoints."""
    result = service.list_endpoints(endpoint_type, page, page_size)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    endpoints, total = result.data
    pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=endpoints,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )


@router.get(
    "/endpoints/{endpoint_id}",
    response_model=EndpointResponseSchema,
    summary="Recuperer un endpoint"
)
async def get_endpoint(
    endpoint_id: UUID,
    service: GatewayService = Depends(get_gateway_service)
):
    """Recupere un endpoint."""
    result = service.get_endpoint(endpoint_id)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.error)
    return result.data


@router.put(
    "/endpoints/{endpoint_id}",
    response_model=EndpointResponseSchema,
    summary="Mettre a jour un endpoint"
)
async def update_endpoint(
    endpoint_id: UUID,
    data: EndpointUpdateSchema,
    service: GatewayService = Depends(get_gateway_service)
):
    """Met a jour un endpoint."""
    result = service.update_endpoint(endpoint_id, data)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if result.error_code == "NOT_FOUND" else status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )
    return result.data


@router.delete(
    "/endpoints/{endpoint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un endpoint"
)
async def delete_endpoint(
    endpoint_id: UUID,
    service: GatewayService = Depends(get_gateway_service)
):
    """Supprime un endpoint."""
    result = service.delete_endpoint(endpoint_id)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.error)
    return None


@router.get(
    "/endpoints/{endpoint_id}/circuit-breaker",
    response_model=CircuitBreakerStatusSchema,
    summary="Statut du circuit breaker"
)
async def get_circuit_breaker_status(
    endpoint_id: UUID,
    service: GatewayService = Depends(get_gateway_service)
):
    """Recupere le statut du circuit breaker."""
    endpoint_result = service.get_endpoint(endpoint_id)
    if not endpoint_result.success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=endpoint_result.error)

    cb = service.get_circuit_state(endpoint_result.data)

    return CircuitBreakerStatusSchema(
        endpoint_id=endpoint_id,
        state=cb.state,
        failure_count=cb.failure_count,
        success_count=cb.success_count,
        failure_threshold=cb.failure_threshold,
        success_threshold=cb.success_threshold,
        last_failure_at=cb.last_failure_at,
        last_success_at=cb.last_success_at,
        opened_at=cb.opened_at,
        half_opened_at=cb.half_opened_at,
        closed_at=cb.closed_at,
        timeout_seconds=cb.timeout_seconds
    )


@router.post(
    "/endpoints/{endpoint_id}/circuit-breaker/reset",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset du circuit breaker"
)
async def reset_circuit_breaker(
    endpoint_id: UUID,
    service: GatewayService = Depends(get_gateway_service)
):
    """Reset le circuit breaker (force CLOSED)."""
    endpoint_result = service.get_endpoint(endpoint_id)
    if not endpoint_result.success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=endpoint_result.error)

    cb = service.get_circuit_state(endpoint_result.data)
    from .models import CircuitState
    cb.state = CircuitState.CLOSED
    cb.failure_count = 0
    cb.success_count = 0
    cb.closed_at = datetime.utcnow()
    service.db.commit()

    return None


# ============================================================================
# TRANSFORMATIONS
# ============================================================================

@router.post(
    "/transformations",
    response_model=TransformationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Creer une transformation"
)
async def create_transformation(
    data: TransformationCreateSchema,
    service: GatewayService = Depends(get_gateway_service)
):
    """Cree une transformation."""
    result = service.create_transformation(data)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.error)
    return result.data


@router.get(
    "/transformations",
    response_model=List[TransformationResponseSchema],
    summary="Lister les transformations"
)
async def list_transformations(
    service: GatewayService = Depends(get_gateway_service)
):
    """Liste les transformations."""
    transforms = service._transform_repo.list_active()
    return transforms


# ============================================================================
# WEBHOOKS
# ============================================================================

@router.post(
    "/webhooks",
    response_model=WebhookResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Creer un webhook"
)
async def create_webhook(
    data: WebhookCreateSchema,
    service: GatewayService = Depends(get_gateway_service)
):
    """Cree un webhook."""
    result = service.create_webhook(data)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.error)
    return result.data


@router.get(
    "/webhooks",
    response_model=PaginatedResponse[WebhookResponseSchema],
    summary="Lister les webhooks"
)
async def list_webhooks(
    status_filter: Optional[WebhookStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: GatewayService = Depends(get_gateway_service)
):
    """Liste les webhooks."""
    result = service.list_webhooks(status_filter, page, page_size)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    webhooks, total = result.data
    pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=webhooks,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )


@router.get(
    "/webhooks/{webhook_id}",
    response_model=WebhookResponseSchema,
    summary="Recuperer un webhook"
)
async def get_webhook(
    webhook_id: UUID,
    service: GatewayService = Depends(get_gateway_service)
):
    """Recupere un webhook."""
    result = service.get_webhook(webhook_id)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.error)
    return result.data


@router.put(
    "/webhooks/{webhook_id}",
    response_model=WebhookResponseSchema,
    summary="Mettre a jour un webhook"
)
async def update_webhook(
    webhook_id: UUID,
    data: WebhookUpdateSchema,
    service: GatewayService = Depends(get_gateway_service)
):
    """Met a jour un webhook."""
    result = service.update_webhook(webhook_id, data)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if result.error_code == "NOT_FOUND" else status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )
    return result.data


@router.delete(
    "/webhooks/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un webhook"
)
async def delete_webhook(
    webhook_id: UUID,
    service: GatewayService = Depends(get_gateway_service)
):
    """Supprime un webhook."""
    result = service.delete_webhook(webhook_id)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.error)
    return None


@router.post(
    "/webhooks/{webhook_id}/test",
    response_model=WebhookTestResponseSchema,
    summary="Tester un webhook"
)
async def test_webhook(
    webhook_id: UUID,
    data: WebhookTestSchema,
    service: GatewayService = Depends(get_gateway_service)
):
    """Teste un webhook avec des donnees d'exemple."""
    result = await service.test_webhook(webhook_id, data.event_type, data.sample_data)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.error)
    return WebhookTestResponseSchema(**result.data)


@router.get(
    "/webhooks/{webhook_id}/deliveries",
    response_model=PaginatedResponse[WebhookDeliveryResponseSchema],
    summary="Lister les livraisons d'un webhook"
)
async def list_webhook_deliveries(
    webhook_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: GatewayService = Depends(get_gateway_service)
):
    """Liste les livraisons d'un webhook."""
    skip = (page - 1) * page_size
    deliveries, total = service._delivery_repo.list_by_webhook(webhook_id, skip, page_size)
    pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=deliveries,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )


@router.post(
    "/webhooks/{webhook_id}/deliveries/{delivery_id}/retry",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Relancer une livraison"
)
async def retry_webhook_delivery(
    webhook_id: UUID,
    delivery_id: UUID,
    service: GatewayService = Depends(get_gateway_service)
):
    """Relance une livraison de webhook."""
    result = await service.send_webhook_delivery(delivery_id)
    if not result.success:
        # On accepte quand meme - sera retry
        pass
    return {"status": "accepted", "delivery_id": str(delivery_id)}


# ============================================================================
# LOGS ET METRIQUES
# ============================================================================

@router.get(
    "/logs",
    response_model=PaginatedResponse[RequestLogResponseSchema],
    summary="Lister les logs de requetes"
)
async def list_request_logs(
    api_key_id: Optional[UUID] = Query(None),
    path: Optional[str] = Query(None),
    status_code: Optional[int] = Query(None),
    since: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: GatewayService = Depends(get_gateway_service)
):
    """Liste les logs de requetes."""
    result = service.get_request_logs(api_key_id, path, status_code, since, page, page_size)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    logs, total = result.data
    pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=logs,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )


@router.get(
    "/metrics",
    response_model=List[MetricsResponseSchema],
    summary="Recuperer les metriques"
)
async def get_metrics(
    period_type: str = Query("hour", pattern=r'^(hour|day|week|month)$'),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    api_key_id: Optional[UUID] = Query(None),
    endpoint_id: Optional[UUID] = Query(None),
    service: GatewayService = Depends(get_gateway_service)
):
    """Recupere les metriques."""
    result = service.get_metrics(period_type, start_time, end_time, api_key_id, endpoint_id)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    metrics = []
    for m in result.data:
        success_rate = (m.successful_requests / m.total_requests * 100) if m.total_requests > 0 else 100
        error_rate = (m.failed_requests / m.total_requests * 100) if m.total_requests > 0 else 0

        metrics.append(MetricsResponseSchema(
            period_type=m.period_type,
            period_start=m.period_start,
            period_end=m.period_end,
            total_requests=m.total_requests,
            successful_requests=m.successful_requests,
            failed_requests=m.failed_requests,
            throttled_requests=m.throttled_requests,
            cached_requests=m.cached_requests,
            success_rate=round(success_rate, 2),
            error_rate=round(error_rate, 2),
            avg_response_time=float(m.avg_response_time),
            min_response_time=m.min_response_time,
            max_response_time=m.max_response_time,
            p50_response_time=m.p50_response_time,
            p95_response_time=m.p95_response_time,
            p99_response_time=m.p99_response_time,
            total_bytes_in=m.total_bytes_in,
            total_bytes_out=m.total_bytes_out,
            error_4xx_count=m.error_4xx_count,
            error_5xx_count=m.error_5xx_count,
            requests_by_status=m.requests_by_status,
            requests_by_endpoint=m.requests_by_endpoint,
            requests_by_method=m.requests_by_method
        ))

    return metrics


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get(
    "/dashboard",
    response_model=GatewayDashboardSchema,
    summary="Dashboard du gateway"
)
async def get_dashboard(
    service: GatewayService = Depends(get_gateway_service)
):
    """Recupere les donnees du dashboard."""
    stats_result = service.get_dashboard_stats()
    if not stats_result.success:
        raise HTTPException(status_code=500, detail=stats_result.error)

    logs_result = service.get_request_logs(page=1, page_size=10)
    recent_requests = logs_result.data[0] if logs_result.success else []

    # Top endpoints
    from datetime import timedelta
    since_24h = datetime.utcnow() - timedelta(hours=24)
    top_endpoints = service._log_repo.get_top_endpoints(since_24h, limit=10)

    # Quota alerts
    quota_alerts = []  # A implementer

    # Webhook failures
    failed_deliveries = service._delivery_repo.list_failed_recent(hours=24)

    return GatewayDashboardSchema(
        stats=GatewayStatsSchema(**stats_result.data),
        recent_requests=[RequestLogResponseSchema.model_validate(r) for r in recent_requests],
        top_endpoints=top_endpoints,
        quota_alerts=quota_alerts,
        webhook_failures=[WebhookDeliveryResponseSchema.model_validate(d) for d in failed_deliveries[:10]]
    )


# ============================================================================
# OPENAPI GENERATION
# ============================================================================

@router.post(
    "/openapi/generate",
    response_model=OpenApiSpecResponseSchema,
    summary="Generer une specification OpenAPI"
)
async def generate_openapi(
    data: OpenApiGenerationRequestSchema = OpenApiGenerationRequestSchema(),
    service: GatewayService = Depends(get_gateway_service)
):
    """Genere une specification OpenAPI."""
    result = service.generate_openapi_spec(
        title=data.title,
        version=data.version,
        description=data.description,
        include_deprecated=data.include_deprecated,
        endpoint_ids=data.endpoint_ids
    )
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return result.data


@router.get(
    "/openapi.json",
    summary="Specification OpenAPI (JSON)"
)
async def get_openapi_json(
    include_deprecated: bool = Query(False),
    service: GatewayService = Depends(get_gateway_service)
):
    """Retourne la specification OpenAPI en JSON."""
    result = service.generate_openapi_spec(include_deprecated=include_deprecated)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return Response(
        content=__import__('json').dumps(result.data, indent=2),
        media_type="application/json"
    )


# ============================================================================
# VALIDATION API KEY (pour middleware externe)
# ============================================================================

@router.post(
    "/validate",
    summary="Valider une cle API",
    description="Endpoint interne pour valider une cle API."
)
async def validate_api_key(
    request: Request,
    service: GatewayService = Depends(get_gateway_service)
):
    """Valide une cle API pour le middleware."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )

    result = service.validate_api_key(api_key)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.error
        )

    key = result.data
    plan_result = service.get_plan(key.plan_id)

    return {
        "valid": True,
        "key_id": str(key.id),
        "plan_id": str(key.plan_id),
        "tier": plan_result.data.tier.value if plan_result.success else None,
        "scopes": key.scopes,
        "rate_limit": plan_result.data.requests_per_minute if plan_result.success else None
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get(
    "/health",
    summary="Health check du module Gateway"
)
async def health_check(
    service: GatewayService = Depends(get_gateway_service)
):
    """Verifie la sante du module Gateway."""
    try:
        # Verifier la connexion DB
        service._plan_repo.count_active()

        return {
            "status": "healthy",
            "module": "gateway",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "module": "gateway",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
