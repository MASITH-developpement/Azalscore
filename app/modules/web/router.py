"""
AZALS MODULE T7 - Router API Web Transverse
============================================

Points d'entrée REST pour la gestion des composants web.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user_and_tenant

from .service import get_web_service
from .models import (
    ThemeMode, WidgetType, WidgetSize, ComponentCategory,
    MenuType, PageType
)
from .schemas import (
    # Thèmes
    ThemeCreate, ThemeUpdate, ThemeResponse, PaginatedThemesResponse,
    ThemeModeEnum,
    # Widgets
    WidgetCreate, WidgetUpdate, WidgetResponse, PaginatedWidgetsResponse,
    WidgetTypeEnum, DashboardCreate, DashboardUpdate, DashboardResponse, PaginatedDashboardsResponse,
    # Menus
    MenuItemCreate, MenuItemUpdate, MenuItemResponse, MenuTreeNode,
    MenuTypeEnum,
    # Préférences
    UserPreferenceCreate, UserPreferenceResponse,
    # Raccourcis
    ShortcutCreate, ShortcutResponse,
    # Pages
    CustomPageCreate, CustomPageResponse, PaginatedPagesResponse,
    PageTypeEnum,
    # Composants
    ComponentCreate, ComponentResponse, PaginatedComponentsResponse,
    ComponentCategoryEnum,
    # Config
    UIConfigResponse
)

router = APIRouter(prefix="/web", tags=["Web"])


# ============================================================================
# THÈMES
# ============================================================================

@router.post("/themes", response_model=ThemeResponse, status_code=status.HTTP_201_CREATED)
async def create_theme(
    theme: ThemeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Créer un nouveau thème."""
    service = get_web_service(db, current_user["tenant_id"])

    existing = service.get_theme_by_code(theme.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Thème avec code '{theme.code}' existe déjà"
        )

    return service.create_theme(
        **theme.model_dump(),
        created_by=current_user["user_id"]
    )


@router.get("/themes", response_model=PaginatedThemesResponse)
async def list_themes(
    mode: Optional[ThemeModeEnum] = None,
    is_active: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Lister les thèmes."""
    service = get_web_service(db, current_user["tenant_id"])
    items, total = service.list_themes(
        mode=ThemeMode(mode.value) if mode else None,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/themes/default", response_model=ThemeResponse)
async def get_default_theme(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Récupérer le thème par défaut."""
    service = get_web_service(db, current_user["tenant_id"])
    theme = service.get_default_theme()
    if not theme:
        raise HTTPException(status_code=404, detail="Aucun thème par défaut")
    return theme


@router.get("/themes/{theme_id}", response_model=ThemeResponse)
async def get_theme(
    theme_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Récupérer un thème par ID."""
    service = get_web_service(db, current_user["tenant_id"])
    theme = service.get_theme(theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail="Thème non trouvé")
    return theme


@router.put("/themes/{theme_id}", response_model=ThemeResponse)
async def update_theme(
    theme_id: int,
    updates: ThemeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Mettre à jour un thème."""
    service = get_web_service(db, current_user["tenant_id"])
    theme = service.update_theme(theme_id, **updates.model_dump(exclude_unset=True))
    if not theme:
        raise HTTPException(status_code=404, detail="Thème non trouvé")
    return theme


@router.delete("/themes/{theme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_theme(
    theme_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Supprimer un thème."""
    service = get_web_service(db, current_user["tenant_id"])
    if not service.delete_theme(theme_id):
        raise HTTPException(status_code=404, detail="Thème non trouvé ou non supprimable")


# ============================================================================
# WIDGETS
# ============================================================================

@router.post("/widgets", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
async def create_widget(
    widget: WidgetCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Créer un nouveau widget."""
    service = get_web_service(db, current_user["tenant_id"])
    return service.create_widget(
        code=widget.code,
        name=widget.name,
        widget_type=WidgetType(widget.widget_type.value),
        default_size=WidgetSize(widget.default_size.value),
        data_source=widget.data_source,
        data_query=widget.data_query,
        display_config=widget.display_config,
        created_by=current_user["user_id"]
    )


@router.get("/widgets", response_model=PaginatedWidgetsResponse)
async def list_widgets(
    widget_type: Optional[WidgetTypeEnum] = None,
    is_active: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Lister les widgets."""
    service = get_web_service(db, current_user["tenant_id"])
    items, total = service.list_widgets(
        widget_type=WidgetType(widget_type.value) if widget_type else None,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/widgets/{widget_id}", response_model=WidgetResponse)
async def get_widget(
    widget_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Récupérer un widget par ID."""
    service = get_web_service(db, current_user["tenant_id"])
    widget = service.get_widget(widget_id)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget non trouvé")
    return widget


@router.put("/widgets/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    widget_id: int,
    updates: WidgetUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Mettre à jour un widget."""
    service = get_web_service(db, current_user["tenant_id"])
    widget = service.update_widget(widget_id, **updates.model_dump(exclude_unset=True))
    if not widget:
        raise HTTPException(status_code=404, detail="Widget non trouvé")
    return widget


@router.delete("/widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    widget_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Supprimer un widget."""
    service = get_web_service(db, current_user["tenant_id"])
    if not service.delete_widget(widget_id):
        raise HTTPException(status_code=404, detail="Widget non trouvé ou système")


# ============================================================================
# DASHBOARDS
# ============================================================================

@router.post("/dashboards", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard: DashboardCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Créer un nouveau dashboard."""
    service = get_web_service(db, current_user["tenant_id"])

    widgets_config = None
    if dashboard.widgets_config:
        widgets_config = [w.model_dump() for w in dashboard.widgets_config]

    return service.create_dashboard(
        code=dashboard.code,
        name=dashboard.name,
        page_type=PageType(dashboard.page_type.value),
        layout_type=dashboard.layout_type,
        columns=dashboard.columns,
        widgets_config=widgets_config,
        is_default=dashboard.is_default,
        is_public=dashboard.is_public,
        owner_id=current_user["user_id"],
        created_by=current_user["user_id"]
    )


@router.get("/dashboards", response_model=PaginatedDashboardsResponse)
async def list_dashboards(
    is_public: Optional[bool] = None,
    is_active: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Lister les dashboards."""
    service = get_web_service(db, current_user["tenant_id"])
    items, total = service.list_dashboards(
        owner_id=current_user["user_id"],
        is_public=is_public,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/dashboards/default", response_model=DashboardResponse)
async def get_default_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Récupérer le dashboard par défaut."""
    service = get_web_service(db, current_user["tenant_id"])
    dashboard = service.get_default_dashboard()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Aucun dashboard par défaut")
    return dashboard


@router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Récupérer un dashboard par ID."""
    service = get_web_service(db, current_user["tenant_id"])
    dashboard = service.get_dashboard(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard non trouvé")
    return dashboard


@router.put("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: int,
    updates: DashboardUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Mettre à jour un dashboard."""
    service = get_web_service(db, current_user["tenant_id"])

    update_dict = updates.model_dump(exclude_unset=True)
    if "widgets_config" in update_dict and update_dict["widgets_config"]:
        update_dict["widgets_config"] = [w.model_dump() if hasattr(w, 'model_dump') else w for w in update_dict["widgets_config"]]

    dashboard = service.update_dashboard(dashboard_id, **update_dict)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard non trouvé")
    return dashboard


@router.delete("/dashboards/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Supprimer un dashboard."""
    service = get_web_service(db, current_user["tenant_id"])
    if not service.delete_dashboard(dashboard_id):
        raise HTTPException(status_code=404, detail="Dashboard non trouvé ou par défaut")


# ============================================================================
# MENUS
# ============================================================================

@router.post("/menu-items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    item: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Créer un élément de menu."""
    service = get_web_service(db, current_user["tenant_id"])
    return service.create_menu_item(
        code=item.code,
        label=item.label,
        menu_type=MenuType(item.menu_type.value),
        icon=item.icon,
        route=item.route,
        parent_id=item.parent_id,
        sort_order=item.sort_order,
        external_url=item.external_url,
        target=item.target,
        required_permission=item.required_permission,
        is_separator=item.is_separator
    )


@router.get("/menu-items", response_model=List[MenuItemResponse])
async def list_menu_items(
    menu_type: MenuTypeEnum = MenuTypeEnum.MAIN,
    parent_id: Optional[int] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Lister les éléments de menu."""
    service = get_web_service(db, current_user["tenant_id"])
    return service.list_menu_items(
        menu_type=MenuType(menu_type.value),
        parent_id=parent_id,
        is_active=is_active
    )


@router.get("/menu-tree", response_model=List[MenuTreeNode])
async def get_menu_tree(
    menu_type: MenuTypeEnum = MenuTypeEnum.MAIN,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Récupérer l'arbre de menu complet."""
    service = get_web_service(db, current_user["tenant_id"])
    return service.get_menu_tree(MenuType(menu_type.value))


@router.put("/menu-items/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    item_id: int,
    updates: MenuItemUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Mettre à jour un élément de menu."""
    service = get_web_service(db, current_user["tenant_id"])
    item = service.update_menu_item(item_id, **updates.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Élément non trouvé")
    return item


@router.delete("/menu-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Supprimer un élément de menu."""
    service = get_web_service(db, current_user["tenant_id"])
    if not service.delete_menu_item(item_id):
        raise HTTPException(status_code=404, detail="Élément non trouvé")


# ============================================================================
# PRÉFÉRENCES UTILISATEUR
# ============================================================================

@router.get("/preferences", response_model=UserPreferenceResponse)
async def get_my_preferences(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Récupérer mes préférences UI."""
    service = get_web_service(db, current_user["tenant_id"])
    prefs = service.get_user_preferences(current_user["user_id"])
    if not prefs:
        prefs = service.set_user_preferences(current_user["user_id"])
    return prefs


@router.put("/preferences", response_model=UserPreferenceResponse)
async def update_my_preferences(
    preferences: UserPreferenceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Mettre à jour mes préférences UI."""
    service = get_web_service(db, current_user["tenant_id"])

    pref_dict = preferences.model_dump()
    if pref_dict.get("theme_mode"):
        pref_dict["theme_mode"] = ThemeMode(pref_dict["theme_mode"].value)

    return service.set_user_preferences(current_user["user_id"], **pref_dict)


@router.get("/config", response_model=UIConfigResponse)
async def get_ui_config(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Récupérer la configuration UI complète."""
    service = get_web_service(db, current_user["tenant_id"])
    return service.get_ui_config(current_user["user_id"])


# ============================================================================
# RACCOURCIS
# ============================================================================

@router.post("/shortcuts", response_model=ShortcutResponse, status_code=status.HTTP_201_CREATED)
async def create_shortcut(
    shortcut: ShortcutCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Créer un raccourci clavier."""
    service = get_web_service(db, current_user["tenant_id"])
    return service.create_shortcut(**shortcut.model_dump())


@router.get("/shortcuts", response_model=List[ShortcutResponse])
async def list_shortcuts(
    context: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Lister les raccourcis clavier."""
    service = get_web_service(db, current_user["tenant_id"])
    return service.list_shortcuts(context=context, is_active=is_active)


# ============================================================================
# PAGES PERSONNALISÉES
# ============================================================================

@router.post("/pages", response_model=CustomPageResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_page(
    page: CustomPageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Créer une page personnalisée."""
    service = get_web_service(db, current_user["tenant_id"])

    existing = service.get_custom_page_by_slug(page.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Page avec slug '{page.slug}' existe déjà"
        )

    return service.create_custom_page(
        **page.model_dump(),
        created_by=current_user["user_id"]
    )


@router.get("/pages", response_model=PaginatedPagesResponse)
async def list_custom_pages(
    page_type: Optional[PageTypeEnum] = None,
    is_published: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Lister les pages personnalisées."""
    service = get_web_service(db, current_user["tenant_id"])
    items, total = service.list_custom_pages(
        page_type=PageType(page_type.value) if page_type else None,
        is_published=is_published,
        skip=skip,
        limit=limit
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/pages/{page_id}", response_model=CustomPageResponse)
async def get_custom_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Récupérer une page par ID."""
    service = get_web_service(db, current_user["tenant_id"])
    page = service.get_custom_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page non trouvée")
    return page


@router.get("/pages/slug/{slug}", response_model=CustomPageResponse)
async def get_custom_page_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Récupérer une page par slug."""
    service = get_web_service(db, current_user["tenant_id"])
    page = service.get_custom_page_by_slug(slug)
    if not page:
        raise HTTPException(status_code=404, detail="Page non trouvée")
    return page


@router.post("/pages/{page_id}/publish", response_model=CustomPageResponse)
async def publish_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Publier une page."""
    service = get_web_service(db, current_user["tenant_id"])
    page = service.publish_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page non trouvée")
    return page


# ============================================================================
# COMPOSANTS UI
# ============================================================================

@router.post("/components", response_model=ComponentResponse, status_code=status.HTTP_201_CREATED)
async def create_component(
    component: ComponentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Créer un composant UI."""
    service = get_web_service(db, current_user["tenant_id"])
    return service.create_component(
        code=component.code,
        name=component.name,
        category=ComponentCategory(component.category.value),
        props_schema=component.props_schema,
        default_props=component.default_props,
        template=component.template,
        created_by=current_user["user_id"]
    )


@router.get("/components", response_model=PaginatedComponentsResponse)
async def list_components(
    category: Optional[ComponentCategoryEnum] = None,
    is_active: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_and_tenant)
):
    """Lister les composants UI."""
    service = get_web_service(db, current_user["tenant_id"])
    items, total = service.list_components(
        category=ComponentCategory(category.value) if category else None,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}
