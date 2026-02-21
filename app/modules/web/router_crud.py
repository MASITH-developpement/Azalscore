"""
AZALS MODULE WEB - Router Unifié
================================
Router unifié compatible v1/v2 via double enregistrement.
Utilise get_context() de app.core.compat pour l'isolation tenant.

Endpoints pour la gestion des composants web transverses.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

from .models import MenuType, PageType, ThemeMode, WidgetSize, WidgetType
from .schemas import (
    ComponentCreate,
    ComponentResponse,
    CustomPageCreate,
    CustomPageResponse,
    DashboardCreate,
    DashboardResponse,
    MenuItemCreate,
    MenuItemResponse,
    MenuTreeNode,
    PaginatedComponentsResponse,
    PaginatedDashboardsResponse,
    PaginatedPagesResponse,
    PaginatedThemesResponse,
    PaginatedWidgetsResponse,
    ShortcutCreate,
    ShortcutResponse,
    ThemeCreate,
    ThemeResponse,
    ThemeUpdate,
    UIConfigResponse,
    UserPreferenceCreate,
    UserPreferenceResponse,
    WidgetCreate,
    WidgetResponse,
)
from .service import WebService

router = APIRouter(prefix="/web", tags=["Web"])

# ============================================================================
# FACTORY SERVICE
# ============================================================================

def get_web_service(db: Session, tenant_id: str, user_id: str) -> WebService:
    """Factory pour créer un service Web avec SaaSContext."""
    return WebService(db, tenant_id, user_id)

# ============================================================================
# THEMES
# ============================================================================

@router.post("/themes", response_model=ThemeResponse, status_code=status.HTTP_201_CREATED)
async def create_theme(
    data: ThemeCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Crée un nouveau thème."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    try:
        theme = service.create_theme(
            code=data.code,
            name=data.name,
            mode=data.mode or ThemeMode.LIGHT,
            primary_color=data.primary_color or "#1976D2",
            secondary_color=data.secondary_color or "#424242",
            accent_color=data.accent_color,
            background_color=data.background_color,
            text_color=data.text_color,
            created_by=int(context.user_id) if context.user_id else None
        )
        return theme
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/themes", response_model=PaginatedThemesResponse)
async def list_themes(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(50, ge=1, le=100, description="Nombre maximum d'éléments"),
    include_inactive: bool = Query(False, description="Inclure inactifs"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Liste les thèmes disponibles."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    # Convertir include_inactive en is_active
    is_active = None if include_inactive else True

    themes, total = service.list_themes(
        skip=skip,
        limit=limit,
        is_active=is_active
    )

    return {
        "items": themes,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/themes/default", response_model=ThemeResponse)
async def get_default_theme(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupère le thème par défaut."""
    service = get_web_service(db, context.tenant_id, context.user_id)
    theme = service.get_default_theme()

    if not theme:
        raise HTTPException(status_code=404, detail="Aucun thème par défaut")

    return theme

@router.get("/themes/{theme_id}", response_model=ThemeResponse)
async def get_theme(
    theme_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupère un thème par ID."""
    service = get_web_service(db, context.tenant_id, context.user_id)
    theme = service.get_theme(int(theme_id))

    if not theme:
        raise HTTPException(status_code=404, detail="Thème non trouvé")

    return theme

@router.put("/themes/{theme_id}", response_model=ThemeResponse)
async def update_theme(
    theme_id: UUID,
    data: ThemeUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Met à jour un thème."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    try:
        update_data = data.model_dump(exclude_unset=True)
        theme = service.update_theme(int(theme_id), **update_data)
        return theme
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/themes/{theme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_theme(
    theme_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Supprime un thème."""
    service = get_web_service(db, context.tenant_id, context.user_id)
    success = service.delete_theme(int(theme_id))

    if not success:
        raise HTTPException(status_code=404, detail="Thème non trouvé")

    return None

# ============================================================================
# WIDGETS
# ============================================================================

@router.post("/widgets", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
async def create_widget(
    data: WidgetCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Crée un nouveau widget."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    try:
        widget = service.create_widget(
            code=data.code,
            name=data.name,
            widget_type=data.widget_type,
            config=data.config or {},
            size=data.size or WidgetSize.MEDIUM,
            created_by=int(context.user_id) if context.user_id else None,
            description=data.description,
            data_source=data.data_source,
            refresh_interval_seconds=data.refresh_interval_seconds
        )
        return widget
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/widgets", response_model=PaginatedWidgetsResponse)
async def list_widgets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    widget_type: WidgetType | None = Query(None, description="Filtrer par type"),
    include_inactive: bool = Query(False),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Liste les widgets disponibles."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    # Convertir include_inactive en is_active
    is_active = None if include_inactive else True

    widgets, total = service.list_widgets(
        skip=skip,
        limit=limit,
        widget_type=widget_type,
        is_active=is_active
    )

    return {
        "items": widgets,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/widgets/{widget_id}", response_model=WidgetResponse)
async def get_widget(
    widget_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupère un widget par ID."""
    service = get_web_service(db, context.tenant_id, context.user_id)
    widget = service.get_widget(int(widget_id))

    if not widget:
        raise HTTPException(status_code=404, detail="Widget non trouvé")

    return widget

@router.put("/widgets/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    widget_id: UUID,
    data: dict,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Met à jour un widget."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    try:
        widget = service.update_widget(int(widget_id), **data)
        return widget
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    widget_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Supprime un widget."""
    service = get_web_service(db, context.tenant_id, context.user_id)
    success = service.delete_widget(int(widget_id))

    if not success:
        raise HTTPException(status_code=404, detail="Widget non trouvé")

    return None

# ============================================================================
# DASHBOARDS
# ============================================================================

@router.post("/dashboards", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    data: DashboardCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Crée un nouveau dashboard."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    try:
        dashboard = service.create_dashboard(
            code=data.code,
            name=data.name,
            layout=data.layout or {},
            created_by=int(context.user_id) if context.user_id else None,
            description=data.description,
            widget_ids=data.widget_ids
        )
        return dashboard
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/dashboards", response_model=PaginatedDashboardsResponse)
async def list_dashboards(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Liste les dashboards."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    # Convertir include_inactive en is_active
    is_active = None if include_inactive else True

    dashboards, total = service.list_dashboards(
        skip=skip,
        limit=limit,
        is_active=is_active
    )

    return {
        "items": dashboards,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/dashboards/default", response_model=DashboardResponse)
async def get_default_dashboard(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupère le dashboard par défaut."""
    service = get_web_service(db, context.tenant_id, context.user_id)
    dashboard = service.get_default_dashboard()

    if not dashboard:
        raise HTTPException(status_code=404, detail="Aucun dashboard par défaut")

    return dashboard

@router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupère un dashboard par ID."""
    service = get_web_service(db, context.tenant_id, context.user_id)
    dashboard = service.get_dashboard(int(dashboard_id))

    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard non trouvé")

    return dashboard

@router.put("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: UUID,
    data: dict,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Met à jour un dashboard."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    try:
        dashboard = service.update_dashboard(int(dashboard_id), **data)
        return dashboard
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/dashboards/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Supprime un dashboard."""
    service = get_web_service(db, context.tenant_id, context.user_id)
    success = service.delete_dashboard(int(dashboard_id))

    if not success:
        raise HTTPException(status_code=404, detail="Dashboard non trouvé")

    return None

# ============================================================================
# MENU ITEMS
# ============================================================================

@router.post("/menu-items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    data: MenuItemCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Crée un élément de menu."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    try:
        menu_item = service.create_menu_item(
            menu_type=data.menu_type,
            code=data.code,
            label=data.label,
            created_by=int(context.user_id) if context.user_id else None,
            parent_id=int(data.parent_id) if data.parent_id else None,
            route=data.route,
            icon=data.icon,
            order=data.order or 0,
            is_visible=data.is_visible if data.is_visible is not None else True
        )
        return menu_item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/menu-items", response_model=List[MenuItemResponse])
async def list_menu_items(
    menu_type: MenuType | None = Query(None, description="Type de menu"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Liste les éléments de menu."""
    service = get_web_service(db, context.tenant_id, context.user_id)
    menu_items = service.list_menu_items(menu_type=menu_type)
    return menu_items

@router.get("/menu-tree", response_model=List[MenuTreeNode])
async def get_menu_tree(
    menu_type: MenuType = Query(..., description="Type de menu"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupère l'arbre du menu."""
    service = get_web_service(db, context.tenant_id, context.user_id)
    tree = service.get_menu_tree(menu_type)
    return tree

@router.put("/menu-items/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    item_id: UUID,
    data: dict,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Met à jour un élément de menu."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    try:
        menu_item = service.update_menu_item(int(item_id), **data)
        return menu_item
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/menu-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(
    item_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Supprime un élément de menu."""
    service = get_web_service(db, context.tenant_id, context.user_id)
    success = service.delete_menu_item(int(item_id))

    if not success:
        raise HTTPException(status_code=404, detail="Élément de menu non trouvé")

    return None

# ============================================================================
# USER PREFERENCES
# ============================================================================

@router.get("/preferences", response_model=UserPreferenceResponse)
async def get_user_preferences(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupère les préférences de l'utilisateur courant."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    if not context.user_id:
        raise HTTPException(status_code=401, detail="Utilisateur non authentifié")

    preferences = service.get_user_preferences(context.user_id)

    if preferences is None:
        # Créer des préférences par défaut si aucune n'existe
        preferences = service.set_user_preferences(context.user_id)

    return preferences

@router.put("/preferences", response_model=UserPreferenceResponse)
async def update_user_preferences(
    data: UserPreferenceCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Met à jour les préférences de l'utilisateur courant."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    if not context.user_id:
        raise HTTPException(status_code=401, detail="Utilisateur non authentifié")

    update_data = data.model_dump(exclude_unset=True)
    preferences = service.update_user_preferences(context.user_id, **update_data)
    return preferences

# ============================================================================
# CONFIG
# ============================================================================

@router.get("/config", response_model=UIConfigResponse)
async def get_ui_config(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupère la configuration UI globale."""
    service = get_web_service(db, context.tenant_id, context.user_id)
    config = service.get_ui_config()
    return config

# ============================================================================
# SHORTCUTS
# ============================================================================

@router.post("/shortcuts", response_model=ShortcutResponse, status_code=status.HTTP_201_CREATED)
async def create_shortcut(
    data: ShortcutCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Crée un raccourci utilisateur."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    if not context.user_id:
        raise HTTPException(status_code=401, detail="Utilisateur non authentifié")

    try:
        shortcut = service.create_shortcut(
            user_id=int(context.user_id),
            label=data.label,
            route=data.route,
            icon=data.icon,
            order=data.order or 0
        )
        return shortcut
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/shortcuts", response_model=List[ShortcutResponse])
async def list_user_shortcuts(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Liste les raccourcis de l'utilisateur courant."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    if not context.user_id:
        raise HTTPException(status_code=401, detail="Utilisateur non authentifié")

    shortcuts = service.get_user_shortcuts(int(context.user_id))
    return shortcuts

# ============================================================================
# CUSTOM PAGES
# ============================================================================

@router.post("/pages", response_model=CustomPageResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    data: CustomPageCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Crée une page personnalisée."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    try:
        page = service.create_page(
            title=data.title,
            slug=data.slug,
            page_type=data.page_type,
            content=data.content or {},
            created_by=int(context.user_id) if context.user_id else None,
            meta_description=data.meta_description,
            meta_keywords=data.meta_keywords
        )
        return page
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/pages", response_model=PaginatedPagesResponse)
async def list_pages(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    page_type: PageType | None = Query(None),
    published_only: bool = Query(False),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Liste les pages personnalisées."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    pages = service.list_pages(
        skip=skip,
        limit=limit,
        page_type=page_type,
        published_only=published_only
    )

    total = service.count_pages(page_type=page_type, published_only=published_only)

    return {
        "items": pages,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/pages/{page_id}", response_model=CustomPageResponse)
async def get_page(
    page_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupère une page par ID."""
    service = get_web_service(db, context.tenant_id, context.user_id)
    page = service.get_custom_page(int(page_id))

    if not page:
        raise HTTPException(status_code=404, detail="Page non trouvée")

    return page

@router.get("/pages/slug/{slug}", response_model=CustomPageResponse)
async def get_page_by_slug(
    slug: str,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupère une page par slug."""
    service = get_web_service(db, context.tenant_id, context.user_id)
    page = service.get_custom_page_by_slug(slug)

    if not page:
        raise HTTPException(status_code=404, detail="Page non trouvée")

    return page

@router.post("/pages/{page_id}/publish", response_model=CustomPageResponse)
async def publish_page(
    page_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Publie une page."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    try:
        page = service.publish_page(
            int(page_id),
            published_by=int(context.user_id) if context.user_id else None
        )
        return page
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ============================================================================
# UI COMPONENTS
# ============================================================================

@router.post("/components", response_model=ComponentResponse, status_code=status.HTTP_201_CREATED)
async def create_component(
    data: ComponentCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Crée un composant UI réutilisable."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    try:
        component = service.create_component(
            code=data.code,
            name=data.name,
            category=data.category,
            template=data.template or {},
            created_by=int(context.user_id) if context.user_id else None,
            description=data.description,
            props_schema=data.props_schema
        )
        return component
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/components", response_model=PaginatedComponentsResponse)
async def list_components(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: str | None = Query(None),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Liste les composants UI."""
    service = get_web_service(db, context.tenant_id, context.user_id)

    components = service.list_components(
        skip=skip,
        limit=limit,
        category=category
    )

    total = service.count_components(category=category)

    return {
        "items": components,
        "total": total,
        "skip": skip,
        "limit": limit
    }
