"""
AZALS - Web Service (v2 - CRUDRouter Compatible)
=====================================================

Service compatible avec BaseService et CRUDRouter.
Migration automatique depuis service.py.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.base_service import BaseService
from app.core.saas_context import Result, SaaSContext

from app.modules.web.models import (
    Theme,
    Widget,
    WebDashboard,
    MenuItem,
    UIComponent,
    UserUIPreference,
    Shortcut,
    CustomPage,
)
from app.modules.web.schemas import (
    ComponentCreate,
    ComponentResponse,
    CustomPageCreate,
    CustomPageResponse,
    CustomPageUpdate,
    DashboardBase,
    DashboardCreate,
    DashboardResponse,
    DashboardUpdate,
    MenuItemBase,
    MenuItemCreate,
    MenuItemResponse,
    MenuItemUpdate,
    PaginatedComponentsResponse,
    PaginatedDashboardsResponse,
    PaginatedPagesResponse,
    PaginatedThemesResponse,
    PaginatedWidgetsResponse,
    ShortcutCreate,
    ShortcutResponse,
    ThemeBase,
    ThemeCreate,
    ThemeResponse,
    ThemeUpdate,
    UIConfigResponse,
    UserPreferenceCreate,
    UserPreferenceResponse,
    WidgetBase,
    WidgetCreate,
    WidgetResponse,
    WidgetUpdate,
)

logger = logging.getLogger(__name__)



class ThemeService(BaseService[Theme, Any, Any]):
    """Service CRUD pour theme."""

    model = Theme

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Theme]
    # - get_or_fail(id) -> Result[Theme]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Theme]
    # - update(id, data) -> Result[Theme]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class WidgetService(BaseService[Widget, Any, Any]):
    """Service CRUD pour widget."""

    model = Widget

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Widget]
    # - get_or_fail(id) -> Result[Widget]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Widget]
    # - update(id, data) -> Result[Widget]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class WebDashboardService(BaseService[WebDashboard, Any, Any]):
    """Service CRUD pour webdashboard."""

    model = WebDashboard

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[WebDashboard]
    # - get_or_fail(id) -> Result[WebDashboard]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[WebDashboard]
    # - update(id, data) -> Result[WebDashboard]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class MenuItemService(BaseService[MenuItem, Any, Any]):
    """Service CRUD pour menuitem."""

    model = MenuItem

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[MenuItem]
    # - get_or_fail(id) -> Result[MenuItem]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[MenuItem]
    # - update(id, data) -> Result[MenuItem]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class UIComponentService(BaseService[UIComponent, Any, Any]):
    """Service CRUD pour uicomponent."""

    model = UIComponent

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[UIComponent]
    # - get_or_fail(id) -> Result[UIComponent]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[UIComponent]
    # - update(id, data) -> Result[UIComponent]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class UserUIPreferenceService(BaseService[UserUIPreference, Any, Any]):
    """Service CRUD pour useruipreference."""

    model = UserUIPreference

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[UserUIPreference]
    # - get_or_fail(id) -> Result[UserUIPreference]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[UserUIPreference]
    # - update(id, data) -> Result[UserUIPreference]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ShortcutService(BaseService[Shortcut, Any, Any]):
    """Service CRUD pour shortcut."""

    model = Shortcut

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Shortcut]
    # - get_or_fail(id) -> Result[Shortcut]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Shortcut]
    # - update(id, data) -> Result[Shortcut]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class CustomPageService(BaseService[CustomPage, Any, Any]):
    """Service CRUD pour custompage."""

    model = CustomPage

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[CustomPage]
    # - get_or_fail(id) -> Result[CustomPage]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[CustomPage]
    # - update(id, data) -> Result[CustomPage]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques

