"""
AZALSCORE ERP - Module DASHBOARDS
==================================
Endpoints API REST.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.compat import get_context
from app.core.database import get_db
from app.core.saas_context import SaaSContext

from .models import DashboardType, AlertStatus, ExportFormat
from .schemas import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardFilters,
    WidgetCreate,
    WidgetUpdate,
    WidgetResponse,
    WidgetLayoutUpdate,
    WidgetDataResponse,
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceResponse,
    DataQueryCreate,
    DataQueryUpdate,
    DataQueryResponse,
    DataQueryExecuteRequest,
    DataQueryExecuteResponse,
    DashboardShareCreate,
    DashboardShareUpdate,
    DashboardShareResponse,
    DashboardFavoriteCreate,
    DashboardFavoriteUpdate,
    DashboardFavoriteResponse,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    AlertResponse,
    AlertAcknowledge,
    AlertResolve,
    AlertSnooze,
    ExportRequest,
    ExportResponse,
    ScheduledReportCreate,
    ScheduledReportUpdate,
    ScheduledReportResponse,
    UserPreferenceUpdate,
    UserPreferenceResponse,
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
)
from .service import DashboardService


# ============================================================================
# ROUTER PRINCIPAL
# ============================================================================

router = APIRouter(prefix="/dashboards", tags=["Dashboards"])


def get_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
) -> DashboardService:
    """Factory pour le service."""
    return DashboardService(db, context)


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/overview")
async def get_overview(service: DashboardService = Depends(get_service)):
    """Vue d'ensemble du module dashboards."""
    result = service.get_overview()
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@router.get("")
async def list_dashboards(
    search: Optional[str] = None,
    dashboard_type: Optional[DashboardType] = None,
    owner_id: Optional[UUID] = None,
    is_shared: Optional[bool] = None,
    is_public: Optional[bool] = None,
    is_template: Optional[bool] = None,
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: DashboardService = Depends(get_service)
):
    """Liste les dashboards."""
    filters = DashboardFilters(
        search=search,
        dashboard_type=dashboard_type,
        owner_id=owner_id,
        is_shared=is_shared,
        is_public=is_public,
        is_template=is_template,
        category=category
    )
    result = service.list_dashboards(filters, page, page_size, sort_by, sort_dir)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@router.get("/me")
async def get_my_dashboards(service: DashboardService = Depends(get_service)):
    """Mes dashboards."""
    result = service.get_my_dashboards()
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return [DashboardResponse.model_validate(d).model_dump() for d in result.data]


@router.get("/recent")
async def get_recent_dashboards(
    limit: int = Query(5, ge=1, le=20),
    service: DashboardService = Depends(get_service)
):
    """Dashboards recemment vus."""
    result = service.get_recent_dashboards(limit)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return [DashboardResponse.model_validate(d).model_dump() for d in result.data]


@router.get("/default")
async def get_default_dashboard(service: DashboardService = Depends(get_service)):
    """Dashboard par defaut."""
    result = service.get_default_dashboard()
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    if result.data:
        return DashboardResponse.model_validate(result.data).model_dump()
    return None


@router.get("/home")
async def get_home_dashboard(service: DashboardService = Depends(get_service)):
    """Dashboard accueil."""
    result = service.get_home_dashboard()
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    if result.data:
        return DashboardResponse.model_validate(result.data).model_dump()
    return None


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    data: DashboardCreate,
    service: DashboardService = Depends(get_service)
):
    """Cree un dashboard."""
    result = service.create_dashboard(data)
    if not result.success:
        if result.error_code == "CONFLICT":
            raise HTTPException(status_code=409, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DashboardResponse.model_validate(result.data).model_dump()


@router.get("/{dashboard_id}")
async def get_dashboard(
    dashboard_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Recupere un dashboard."""
    result = service.get_dashboard(dashboard_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DashboardResponse.model_validate(result.data).model_dump()


@router.put("/{dashboard_id}")
async def update_dashboard(
    dashboard_id: UUID,
    data: DashboardUpdate,
    service: DashboardService = Depends(get_service)
):
    """Met a jour un dashboard."""
    result = service.update_dashboard(dashboard_id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DashboardResponse.model_validate(result.data).model_dump()


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: UUID,
    hard: bool = Query(False),
    service: DashboardService = Depends(get_service)
):
    """Supprime un dashboard."""
    result = service.delete_dashboard(dashboard_id, hard)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return None


@router.post("/{dashboard_id}/restore")
async def restore_dashboard(
    dashboard_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Restaure un dashboard supprime."""
    result = service.restore_dashboard(dashboard_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DashboardResponse.model_validate(result.data).model_dump()


@router.post("/{dashboard_id}/duplicate")
async def duplicate_dashboard(
    dashboard_id: UUID,
    new_code: str = Query(..., min_length=2, max_length=50),
    new_name: str = Query(..., min_length=1, max_length=200),
    service: DashboardService = Depends(get_service)
):
    """Duplique un dashboard."""
    result = service.duplicate_dashboard(dashboard_id, new_code, new_name)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "CONFLICT":
            raise HTTPException(status_code=409, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DashboardResponse.model_validate(result.data).model_dump()


@router.get("/{dashboard_id}/stats")
async def get_dashboard_stats(
    dashboard_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Statistiques d'un dashboard."""
    result = service.get_dashboard_stats(dashboard_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


# ============================================================================
# WIDGET ENDPOINTS
# ============================================================================

@router.get("/{dashboard_id}/widgets")
async def get_dashboard_widgets(
    dashboard_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Widgets d'un dashboard."""
    result = service.get_dashboard_widgets(dashboard_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return [WidgetResponse.model_validate(w).model_dump() for w in result.data]


@router.post("/{dashboard_id}/widgets", status_code=status.HTTP_201_CREATED)
async def add_widget(
    dashboard_id: UUID,
    data: WidgetCreate,
    service: DashboardService = Depends(get_service)
):
    """Ajoute un widget."""
    result = service.add_widget(dashboard_id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return WidgetResponse.model_validate(result.data).model_dump()


@router.put("/{dashboard_id}/layout")
async def update_layout(
    dashboard_id: UUID,
    data: WidgetLayoutUpdate,
    service: DashboardService = Depends(get_service)
):
    """Met a jour le layout."""
    result = service.update_layout(dashboard_id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return {"success": True}


# Widget individuel
widgets_router = APIRouter(prefix="/widgets", tags=["Dashboards - Widgets"])


@widgets_router.get("/{widget_id}")
async def get_widget(
    widget_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Recupere un widget."""
    result = service.get_widget(widget_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return WidgetResponse.model_validate(result.data).model_dump()


@widgets_router.put("/{widget_id}")
async def update_widget(
    widget_id: UUID,
    data: WidgetUpdate,
    service: DashboardService = Depends(get_service)
):
    """Met a jour un widget."""
    result = service.update_widget(widget_id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return WidgetResponse.model_validate(result.data).model_dump()


@widgets_router.delete("/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    widget_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Supprime un widget."""
    result = service.delete_widget(widget_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return None


@widgets_router.get("/{widget_id}/data")
async def get_widget_data(
    widget_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Donnees d'un widget."""
    result = service.get_widget_data(widget_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return result.data.model_dump()


@widgets_router.post("/{widget_id}/refresh")
async def refresh_widget(
    widget_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Rafraichit un widget."""
    result = service.refresh_widget(widget_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return result.data.model_dump()


# ============================================================================
# DATA SOURCE ENDPOINTS
# ============================================================================

datasources_router = APIRouter(prefix="/data-sources", tags=["Dashboards - Data Sources"])


@datasources_router.get("")
async def list_data_sources(
    source_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: DashboardService = Depends(get_service)
):
    """Liste les sources de donnees."""
    result = service.list_data_sources(source_type, page, page_size)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@datasources_router.post("", status_code=status.HTTP_201_CREATED)
async def create_data_source(
    data: DataSourceCreate,
    service: DashboardService = Depends(get_service)
):
    """Cree une source de donnees."""
    result = service.create_data_source(data)
    if not result.success:
        if result.error_code == "CONFLICT":
            raise HTTPException(status_code=409, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DataSourceResponse.model_validate(result.data).model_dump()


@datasources_router.get("/{source_id}")
async def get_data_source(
    source_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Recupere une source de donnees."""
    result = service.get_data_source(source_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DataSourceResponse.model_validate(result.data).model_dump()


@datasources_router.put("/{source_id}")
async def update_data_source(
    source_id: UUID,
    data: DataSourceUpdate,
    service: DashboardService = Depends(get_service)
):
    """Met a jour une source de donnees."""
    result = service.update_data_source(source_id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DataSourceResponse.model_validate(result.data).model_dump()


@datasources_router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_source(
    source_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Supprime une source de donnees."""
    result = service.delete_data_source(source_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return None


@datasources_router.post("/{source_id}/test")
async def test_data_source(
    source_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Teste une source de donnees."""
    result = service.test_data_source_connection(source_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@datasources_router.post("/{source_id}/sync")
async def sync_data_source(
    source_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Synchronise une source de donnees."""
    result = service.sync_data_source(source_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


# ============================================================================
# DATA QUERY ENDPOINTS
# ============================================================================

queries_router = APIRouter(prefix="/queries", tags=["Dashboards - Queries"])


@queries_router.get("")
async def list_data_queries(
    data_source_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: DashboardService = Depends(get_service)
):
    """Liste les requetes."""
    result = service.list_data_queries(data_source_id, page, page_size)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@queries_router.post("", status_code=status.HTTP_201_CREATED)
async def create_data_query(
    data: DataQueryCreate,
    service: DashboardService = Depends(get_service)
):
    """Cree une requete."""
    result = service.create_data_query(data)
    if not result.success:
        if result.error_code == "CONFLICT":
            raise HTTPException(status_code=409, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DataQueryResponse.model_validate(result.data).model_dump()


@queries_router.get("/{query_id}")
async def get_data_query(
    query_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Recupere une requete."""
    result = service.get_data_query(query_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DataQueryResponse.model_validate(result.data).model_dump()


@queries_router.put("/{query_id}")
async def update_data_query(
    query_id: UUID,
    data: DataQueryUpdate,
    service: DashboardService = Depends(get_service)
):
    """Met a jour une requete."""
    result = service.update_data_query(query_id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DataQueryResponse.model_validate(result.data).model_dump()


@queries_router.delete("/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_query(
    query_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Supprime une requete."""
    result = service.delete_data_query(query_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return None


@queries_router.post("/{query_id}/execute")
async def execute_data_query(
    query_id: UUID,
    request: DataQueryExecuteRequest,
    service: DashboardService = Depends(get_service)
):
    """Execute une requete."""
    result = service.execute_data_query(query_id, request)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return result.data.model_dump()


# ============================================================================
# SHARE ENDPOINTS
# ============================================================================

@router.get("/{dashboard_id}/shares")
async def get_dashboard_shares(
    dashboard_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Partages d'un dashboard."""
    result = service.get_dashboard_shares(dashboard_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return [DashboardShareResponse.model_validate(s).model_dump() for s in result.data]


@router.post("/{dashboard_id}/share", status_code=status.HTTP_201_CREATED)
async def share_dashboard(
    dashboard_id: UUID,
    data: DashboardShareCreate,
    service: DashboardService = Depends(get_service)
):
    """Partage un dashboard."""
    result = service.share_dashboard(dashboard_id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DashboardShareResponse.model_validate(result.data).model_dump()


shares_router = APIRouter(prefix="/shares", tags=["Dashboards - Shares"])


@shares_router.get("/link/{share_link}")
async def get_share_by_link(
    share_link: str,
    password: Optional[str] = None,
    service: DashboardService = Depends(get_service)
):
    """Accede a un dashboard via lien de partage."""
    result = service.get_share_by_link(share_link, password)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code in ["EXPIRED", "LIMIT_REACHED"]:
            raise HTTPException(status_code=410, detail=result.error)
        if result.error_code in ["PASSWORD_REQUIRED", "INVALID_PASSWORD"]:
            raise HTTPException(status_code=401, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DashboardShareResponse.model_validate(result.data).model_dump()


@shares_router.put("/{share_id}")
async def update_share(
    share_id: UUID,
    data: DashboardShareUpdate,
    service: DashboardService = Depends(get_service)
):
    """Met a jour un partage."""
    result = service.update_share(share_id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DashboardShareResponse.model_validate(result.data).model_dump()


@shares_router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share(
    share_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Revoque un partage."""
    result = service.revoke_share(share_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return None


# ============================================================================
# FAVORITES ENDPOINTS
# ============================================================================

favorites_router = APIRouter(prefix="/favorites", tags=["Dashboards - Favorites"])


@favorites_router.get("")
async def get_favorites(
    folder: Optional[str] = None,
    service: DashboardService = Depends(get_service)
):
    """Mes favoris."""
    result = service.get_favorites(folder)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return [DashboardFavoriteResponse.model_validate(f).model_dump() for f in result.data]


@favorites_router.post("", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    data: DashboardFavoriteCreate,
    service: DashboardService = Depends(get_service)
):
    """Ajoute un favori."""
    result = service.add_favorite(data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "CONFLICT":
            raise HTTPException(status_code=409, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DashboardFavoriteResponse.model_validate(result.data).model_dump()


@favorites_router.put("/{favorite_id}")
async def update_favorite(
    favorite_id: UUID,
    data: DashboardFavoriteUpdate,
    service: DashboardService = Depends(get_service)
):
    """Met a jour un favori."""
    result = service.update_favorite(favorite_id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return DashboardFavoriteResponse.model_validate(result.data).model_dump()


@favorites_router.delete("/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    favorite_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Supprime un favori."""
    result = service.remove_favorite(favorite_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return None


@favorites_router.post("/toggle/{dashboard_id}")
async def toggle_favorite(
    dashboard_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Bascule favori."""
    result = service.toggle_favorite(dashboard_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return {"is_favorite": result.data}


# ============================================================================
# ALERTS ENDPOINTS
# ============================================================================

alerts_router = APIRouter(prefix="/alerts", tags=["Dashboards - Alerts"])


@alerts_router.get("/summary")
async def get_alert_summary(service: DashboardService = Depends(get_service)):
    """Resume des alertes."""
    result = service.get_alert_summary()
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@alerts_router.get("/active")
async def get_active_alerts(service: DashboardService = Depends(get_service)):
    """Alertes actives."""
    result = service.get_active_alerts()
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return [AlertResponse.model_validate(a).model_dump() for a in result.data]


@alerts_router.get("")
async def list_alerts(
    status: Optional[AlertStatus] = None,
    dashboard_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: DashboardService = Depends(get_service)
):
    """Liste les alertes."""
    result = service.get_alerts(status, dashboard_id, page, page_size)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@alerts_router.get("/{alert_id}")
async def get_alert(
    alert_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Recupere une alerte."""
    result = service.get_alert(alert_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return AlertResponse.model_validate(result.data).model_dump()


@alerts_router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    data: AlertAcknowledge,
    service: DashboardService = Depends(get_service)
):
    """Acquitte une alerte."""
    result = service.acknowledge_alert(alert_id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return AlertResponse.model_validate(result.data).model_dump()


@alerts_router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    data: AlertResolve,
    service: DashboardService = Depends(get_service)
):
    """Resout une alerte."""
    result = service.resolve_alert(alert_id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "ALREADY_RESOLVED":
            raise HTTPException(status_code=409, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return AlertResponse.model_validate(result.data).model_dump()


@alerts_router.post("/{alert_id}/snooze")
async def snooze_alert(
    alert_id: UUID,
    data: AlertSnooze,
    service: DashboardService = Depends(get_service)
):
    """Met une alerte en pause."""
    result = service.snooze_alert(alert_id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return AlertResponse.model_validate(result.data).model_dump()


# Alert Rules
alert_rules_router = APIRouter(prefix="/alert-rules", tags=["Dashboards - Alert Rules"])


@alert_rules_router.get("")
async def get_alert_rules(
    dashboard_id: Optional[UUID] = None,
    widget_id: Optional[UUID] = None,
    service: DashboardService = Depends(get_service)
):
    """Liste les regles d'alerte."""
    result = service.get_alert_rules(dashboard_id, widget_id)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return [AlertRuleResponse.model_validate(r).model_dump() for r in result.data]


@alert_rules_router.post("", status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    data: AlertRuleCreate,
    service: DashboardService = Depends(get_service)
):
    """Cree une regle d'alerte."""
    result = service.create_alert_rule(data)
    if not result.success:
        if result.error_code == "CONFLICT":
            raise HTTPException(status_code=409, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return AlertRuleResponse.model_validate(result.data).model_dump()


@alert_rules_router.get("/{rule_id}")
async def get_alert_rule(
    rule_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Recupere une regle d'alerte."""
    result = service.get_alert_rule(rule_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return AlertRuleResponse.model_validate(result.data).model_dump()


@alert_rules_router.put("/{rule_id}")
async def update_alert_rule(
    rule_id: UUID,
    data: AlertRuleUpdate,
    service: DashboardService = Depends(get_service)
):
    """Met a jour une regle d'alerte."""
    result = service.update_alert_rule(rule_id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return AlertRuleResponse.model_validate(result.data).model_dump()


@alert_rules_router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Supprime une regle d'alerte."""
    result = service.delete_alert_rule(rule_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return None


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

exports_router = APIRouter(prefix="/exports", tags=["Dashboards - Exports"])


@exports_router.get("/me")
async def get_my_exports(
    limit: int = Query(20, ge=1, le=100),
    service: DashboardService = Depends(get_service)
):
    """Mes exports."""
    result = service.get_my_exports(limit)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return [ExportResponse.model_validate(e).model_dump() for e in result.data]


@exports_router.get("/{export_id}")
async def get_export(
    export_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Recupere un export."""
    result = service.get_export(export_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return ExportResponse.model_validate(result.data).model_dump()


@exports_router.get("/{export_id}/download")
async def download_export(
    export_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Telecharge un export."""
    result = service.download_export(export_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        if result.error_code == "NOT_READY":
            raise HTTPException(status_code=425, detail=result.error)
        if result.error_code == "EXPIRED":
            raise HTTPException(status_code=410, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@router.post("/{dashboard_id}/export", status_code=status.HTTP_201_CREATED)
async def export_dashboard(
    dashboard_id: UUID,
    request: ExportRequest,
    service: DashboardService = Depends(get_service)
):
    """Exporte un dashboard."""
    result = service.export_dashboard(dashboard_id, request)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return ExportResponse.model_validate(result.data).model_dump()


@widgets_router.post("/{widget_id}/export", status_code=status.HTTP_201_CREATED)
async def export_widget(
    widget_id: UUID,
    request: ExportRequest,
    service: DashboardService = Depends(get_service)
):
    """Exporte un widget."""
    result = service.export_widget(widget_id, request)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return ExportResponse.model_validate(result.data).model_dump()


# ============================================================================
# SCHEDULED REPORTS ENDPOINTS
# ============================================================================

scheduled_router = APIRouter(prefix="/scheduled-reports", tags=["Dashboards - Scheduled Reports"])


@scheduled_router.get("")
async def get_scheduled_reports(
    dashboard_id: Optional[UUID] = None,
    service: DashboardService = Depends(get_service)
):
    """Liste les rapports planifies."""
    result = service.get_scheduled_reports(dashboard_id)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return [ScheduledReportResponse.model_validate(r).model_dump() for r in result.data]


@scheduled_router.post("", status_code=status.HTTP_201_CREATED)
async def create_scheduled_report(
    data: ScheduledReportCreate,
    service: DashboardService = Depends(get_service)
):
    """Cree un rapport planifie."""
    result = service.create_scheduled_report(data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "CONFLICT":
            raise HTTPException(status_code=409, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return ScheduledReportResponse.model_validate(result.data).model_dump()


@scheduled_router.get("/{report_id}")
async def get_scheduled_report(
    report_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Recupere un rapport planifie."""
    result = service.get_scheduled_report(report_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return ScheduledReportResponse.model_validate(result.data).model_dump()


@scheduled_router.put("/{report_id}")
async def update_scheduled_report(
    report_id: UUID,
    data: ScheduledReportUpdate,
    service: DashboardService = Depends(get_service)
):
    """Met a jour un rapport planifie."""
    result = service.update_scheduled_report(report_id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return ScheduledReportResponse.model_validate(result.data).model_dump()


@scheduled_router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_report(
    report_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Supprime un rapport planifie."""
    result = service.delete_scheduled_report(report_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return None


@scheduled_router.post("/{report_id}/run")
async def run_scheduled_report(
    report_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Execute immediatement un rapport planifie."""
    result = service.run_scheduled_report_now(report_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return ExportResponse.model_validate(result.data).model_dump()


# ============================================================================
# PREFERENCES ENDPOINTS
# ============================================================================

preferences_router = APIRouter(prefix="/preferences", tags=["Dashboards - Preferences"])


@preferences_router.get("")
async def get_preferences(service: DashboardService = Depends(get_service)):
    """Mes preferences."""
    result = service.get_user_preferences()
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return UserPreferenceResponse.model_validate(result.data).model_dump()


@preferences_router.put("")
async def update_preferences(
    data: UserPreferenceUpdate,
    service: DashboardService = Depends(get_service)
):
    """Met a jour mes preferences."""
    result = service.update_user_preferences(data)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return UserPreferenceResponse.model_validate(result.data).model_dump()


@preferences_router.post("/default/{dashboard_id}")
async def set_default_dashboard(
    dashboard_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Definit le dashboard par defaut."""
    result = service.set_default_dashboard(dashboard_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return {"success": True}


@preferences_router.post("/home/{dashboard_id}")
async def set_home_dashboard(
    dashboard_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Definit le dashboard accueil."""
    result = service.set_home_dashboard(dashboard_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return {"success": True}


# ============================================================================
# TEMPLATES ENDPOINTS
# ============================================================================

templates_router = APIRouter(prefix="/templates", tags=["Dashboards - Templates"])


@templates_router.get("")
async def list_templates(
    dashboard_type: Optional[DashboardType] = None,
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: DashboardService = Depends(get_service)
):
    """Liste les templates."""
    result = service.list_templates(dashboard_type, category, page, page_size)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@templates_router.post("", status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    service: DashboardService = Depends(get_service)
):
    """Cree un template."""
    result = service.create_template(data)
    if not result.success:
        if result.error_code == "CONFLICT":
            raise HTTPException(status_code=409, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return TemplateResponse.model_validate(result.data).model_dump()


@templates_router.post("/from-dashboard/{dashboard_id}", status_code=status.HTTP_201_CREATED)
async def create_template_from_dashboard(
    dashboard_id: UUID,
    code: str = Query(..., min_length=2, max_length=50),
    name: str = Query(..., min_length=1, max_length=200),
    description: Optional[str] = None,
    service: DashboardService = Depends(get_service)
):
    """Cree un template depuis un dashboard."""
    result = service.create_template_from_dashboard(dashboard_id, code, name, description)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        if result.error_code == "CONFLICT":
            raise HTTPException(status_code=409, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return TemplateResponse.model_validate(result.data).model_dump()


@templates_router.get("/{template_id}")
async def get_template(
    template_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Recupere un template."""
    result = service.get_template(template_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return TemplateResponse.model_validate(result.data).model_dump()


@templates_router.put("/{template_id}")
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    service: DashboardService = Depends(get_service)
):
    """Met a jour un template."""
    result = service.update_template(template_id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return TemplateResponse.model_validate(result.data).model_dump()


@templates_router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    service: DashboardService = Depends(get_service)
):
    """Supprime un template."""
    result = service.delete_template(template_id)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return None


# ============================================================================
# INCLURE LES SUB-ROUTERS
# ============================================================================

router.include_router(widgets_router)
router.include_router(datasources_router)
router.include_router(queries_router)
router.include_router(shares_router)
router.include_router(favorites_router)
router.include_router(alerts_router)
router.include_router(alert_rules_router)
router.include_router(exports_router)
router.include_router(scheduled_router)
router.include_router(preferences_router)
router.include_router(templates_router)
