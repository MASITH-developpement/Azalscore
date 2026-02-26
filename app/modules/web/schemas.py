"""
AZALS MODULE T7 - Schémas Pydantic Web Transverse
=================================================

Schémas de validation pour les API du module Web.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS
# ============================================================================

class ThemeModeEnum(str, Enum):
    LIGHT = "LIGHT"
    DARK = "DARK"
    SYSTEM = "SYSTEM"
    HIGH_CONTRAST = "HIGH_CONTRAST"


class UIStyleEnum(str, Enum):
    """Style visuel de l'interface: classique, moderne ou glass"""
    CLASSIC = "CLASSIC"
    MODERN = "MODERN"
    GLASS = "GLASS"


class WidgetTypeEnum(str, Enum):
    KPI = "KPI"
    CHART = "CHART"
    TABLE = "TABLE"
    LIST = "LIST"
    CALENDAR = "CALENDAR"
    MAP = "MAP"
    GAUGE = "GAUGE"
    TIMELINE = "TIMELINE"
    CUSTOM = "CUSTOM"


class WidgetSizeEnum(str, Enum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
    WIDE = "WIDE"
    TALL = "TALL"
    FULL = "FULL"


class ComponentCategoryEnum(str, Enum):
    LAYOUT = "LAYOUT"
    NAVIGATION = "NAVIGATION"
    FORMS = "FORMS"
    DATA_DISPLAY = "DATA_DISPLAY"
    FEEDBACK = "FEEDBACK"
    CHARTS = "CHARTS"
    ACTIONS = "ACTIONS"


class MenuTypeEnum(str, Enum):
    MAIN = "MAIN"
    SIDEBAR = "SIDEBAR"
    TOOLBAR = "TOOLBAR"
    CONTEXT = "CONTEXT"
    FOOTER = "FOOTER"


class PageTypeEnum(str, Enum):
    DASHBOARD = "DASHBOARD"
    LIST = "LIST"
    FORM = "FORM"
    DETAIL = "DETAIL"
    REPORT = "REPORT"
    CUSTOM = "CUSTOM"


# ============================================================================
# THÈMES
# ============================================================================

class ThemeBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    mode: ThemeModeEnum = ThemeModeEnum.LIGHT
    primary_color: str = "#1976D2"
    secondary_color: str = "#424242"
    accent_color: str = "#82B1FF"
    error_color: str = "#FF5252"
    warning_color: str = "#FB8C00"
    success_color: str = "#4CAF50"
    info_color: str = "#2196F3"
    background_color: str = "#FFFFFF"
    surface_color: str = "#FAFAFA"
    text_primary: str = "#212121"
    text_secondary: str = "#757575"
    font_family: str = "'Roboto', sans-serif"


class ThemeCreate(ThemeBase):
    is_default: bool = False


class ThemeUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    mode: ThemeModeEnum | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    accent_color: str | None = None
    background_color: str | None = None
    text_primary: str | None = None
    font_family: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class ThemeResponse(ThemeBase):
    id: int
    is_active: bool
    is_default: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# WIDGETS
# ============================================================================

class WidgetBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    widget_type: WidgetTypeEnum
    default_size: WidgetSizeEnum = WidgetSizeEnum.MEDIUM


class WidgetCreate(WidgetBase):
    data_source: str | None = None
    data_query: dict[str, Any] | None = None
    display_config: dict[str, Any] | None = None
    chart_config: dict[str, Any] | None = None
    refresh_interval: int = 60
    required_permission: str | None = None


class WidgetUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    default_size: WidgetSizeEnum | None = None
    data_source: str | None = None
    data_query: dict[str, Any] | None = None
    display_config: dict[str, Any] | None = None
    chart_config: dict[str, Any] | None = None
    refresh_interval: int | None = None
    is_active: bool | None = None


class WidgetResponse(WidgetBase):
    id: int
    data_source: str | None = None
    data_query: dict[str, Any] | None = None
    display_config: dict[str, Any] | None = None
    chart_config: dict[str, Any] | None = None
    refresh_interval: int
    required_permission: str | None = None
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("data_query", "display_config", "chart_config", mode="before")
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception as e:
                logger.warning(
                    "[WEB_SCHEMA] Échec parsing JSON champ widget",
                    extra={"value_preview": repr(v)[:100], "error": str(e)[:200], "consequence": "raw_value_kept"}
                )
                return v
        return v


# ============================================================================
# DASHBOARDS
# ============================================================================

class DashboardBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    page_type: PageTypeEnum = PageTypeEnum.DASHBOARD
    layout_type: str = "grid"
    columns: int = Field(4, ge=1, le=12)


class WidgetPosition(BaseModel):
    widget_id: int
    x: int = 0
    y: int = 0
    width: int = 1
    height: int = 1


class DashboardCreate(DashboardBase):
    widgets_config: list[WidgetPosition] | None = None
    default_filters: dict[str, Any] | None = None
    is_default: bool = False
    is_public: bool = False


class DashboardUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    layout_type: str | None = None
    columns: int | None = Field(None, ge=1, le=12)
    widgets_config: list[WidgetPosition] | None = None
    default_filters: dict[str, Any] | None = None
    is_default: bool | None = None
    is_public: bool | None = None
    is_active: bool | None = None


class DashboardResponse(DashboardBase):
    id: int
    widgets_config: list[dict[str, Any]] | None = None
    default_filters: dict[str, Any] | None = None
    is_active: bool
    is_default: bool
    is_public: bool
    owner_id: int | None = None
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("widgets_config", "default_filters", mode="before")
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception as e:
                logger.warning(
                    "[WEB_SCHEMA] Échec parsing JSON dashboard config",
                    extra={"value_preview": repr(v)[:100], "error": str(e)[:200], "consequence": "raw_value_kept"}
                )
                return v
        return v


# ============================================================================
# MENUS
# ============================================================================

class MenuItemBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    label: str = Field(..., min_length=1, max_length=200)
    icon: str | None = None
    route: str | None = None
    menu_type: MenuTypeEnum = MenuTypeEnum.MAIN


class MenuItemCreate(MenuItemBase):
    parent_id: int | None = None
    sort_order: int = 0
    external_url: str | None = None
    target: str = "_self"
    required_permission: str | None = None
    is_separator: bool = False


class MenuItemUpdate(BaseModel):
    label: str | None = Field(None, min_length=1, max_length=200)
    icon: str | None = None
    route: str | None = None
    parent_id: int | None = None
    sort_order: int | None = None
    external_url: str | None = None
    required_permission: str | None = None
    is_active: bool | None = None
    is_separator: bool | None = None


class MenuItemResponse(MenuItemBase):
    id: int
    parent_id: int | None = None
    sort_order: int
    external_url: str | None = None
    target: str
    required_permission: str | None = None
    is_active: bool
    is_separator: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MenuTreeNode(BaseModel):
    id: int
    code: str
    label: str
    icon: str | None = None
    route: str | None = None
    is_separator: bool = False
    children: list[MenuTreeNode] = []


# Résoudre les références circulaires pour MenuTreeNode
MenuTreeNode.model_rebuild()


# ============================================================================
# PRÉFÉRENCES UTILISATEUR
# ============================================================================

class UserPreferenceCreate(BaseModel):
    theme_id: int | None = None
    theme_mode: ThemeModeEnum = ThemeModeEnum.SYSTEM
    ui_style: UIStyleEnum = UIStyleEnum.CLASSIC
    sidebar_collapsed: bool = False
    sidebar_mini: bool = False
    toolbar_dense: bool = False
    default_dashboard_id: int | None = None
    table_density: str = "default"
    table_page_size: int = 25
    font_size: str = "medium"
    high_contrast: bool = False
    reduced_motion: bool = False
    language: str = "fr"
    date_format: str = "DD/MM/YYYY"
    time_format: str = "24h"
    timezone: str = "Europe/Paris"
    show_tooltips: bool = True
    sound_enabled: bool = True
    desktop_notifications: bool = False


class UserPreferenceResponse(BaseModel):
    id: str  # UUID as string
    user_id: str  # UUID as string
    theme_id: str | None = None  # UUID as string
    theme_mode: ThemeModeEnum
    ui_style: UIStyleEnum = UIStyleEnum.CLASSIC
    sidebar_collapsed: bool
    sidebar_mini: bool
    toolbar_dense: bool
    default_dashboard_id: str | None = None  # UUID as string
    table_density: str
    table_page_size: int
    font_size: str
    high_contrast: bool
    reduced_motion: bool
    language: str
    date_format: str
    time_format: str
    timezone: str
    show_tooltips: bool
    sound_enabled: bool
    desktop_notifications: bool
    custom_shortcuts: dict[str, Any] | None = None
    favorite_widgets: list[str] | None = None  # UUIDs as strings
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "user_id", "theme_id", "default_dashboard_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convertit les UUIDs en strings."""
        if v is None:
            return None
        return str(v)

    @field_validator("ui_style", mode="before")
    @classmethod
    def default_ui_style(cls, v):
        """Retourne CLASSIC si ui_style est None (pour les enregistrements existants)."""
        if v is None:
            return UIStyleEnum.CLASSIC
        return v

    @field_validator("custom_shortcuts", "favorite_widgets", mode="before")
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception as e:
                logger.warning(
                    "[WEB_SCHEMA] Échec parsing JSON préférences utilisateur",
                    extra={"value_preview": repr(v)[:100], "error": str(e)[:200], "consequence": "raw_value_kept"}
                )
                return v
        return v


# ============================================================================
# RACCOURCIS
# ============================================================================

class ShortcutCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    key_combination: str = Field(..., min_length=1, max_length=100)
    action_type: str = Field(..., min_length=2, max_length=50)
    action_value: str | None = None
    context: str = "global"


class ShortcutResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None
    key_combination: str
    action_type: str
    action_value: str | None = None
    context: str
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PAGES PERSONNALISÉES
# ============================================================================

class CustomPageCreate(BaseModel):
    slug: str = Field(..., min_length=2, max_length=100)
    title: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    page_type: PageTypeEnum = PageTypeEnum.CUSTOM
    content: str | None = None
    template: str | None = None
    layout: str = "default"
    show_sidebar: bool = True
    show_toolbar: bool = True
    meta_title: str | None = None
    meta_description: str | None = None
    required_permission: str | None = None


class CustomPageUpdate(BaseModel):
    title: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    content: str | None = None
    template: str | None = None
    layout: str | None = None
    show_sidebar: bool | None = None
    show_toolbar: bool | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    required_permission: str | None = None
    is_active: bool | None = None


class CustomPageResponse(BaseModel):
    id: int
    slug: str
    title: str
    description: str | None = None
    page_type: PageTypeEnum
    content: str | None = None
    template: str | None = None
    layout: str
    show_sidebar: bool
    show_toolbar: bool
    meta_title: str | None = None
    meta_description: str | None = None
    required_permission: str | None = None
    is_active: bool
    is_published: bool
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# COMPOSANTS UI
# ============================================================================

class ComponentCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    category: ComponentCategoryEnum
    props_schema: dict[str, Any] | None = None
    default_props: dict[str, Any] | None = None
    template: str | None = None
    styles: str | None = None


class ComponentResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None
    category: ComponentCategoryEnum
    props_schema: dict[str, Any] | None = None
    default_props: dict[str, Any] | None = None
    template: str | None = None
    styles: str | None = None
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("props_schema", "default_props", mode="before")
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception as e:
                logger.warning(
                    "[WEB_SCHEMA] Échec parsing JSON props composant",
                    extra={"value_preview": repr(v)[:100], "error": str(e)[:200], "consequence": "raw_value_kept"}
                )
                return v
        return v


# ============================================================================
# CONFIG UI COMPLÈTE
# ============================================================================

class UIConfigResponse(BaseModel):
    theme: dict[str, Any] | None = None
    preferences: dict[str, Any] = {}
    menu: list[dict[str, Any]] = []
    shortcuts: list[dict[str, str]] = []


# ============================================================================
# LISTES PAGINÉES
# ============================================================================

class PaginatedThemesResponse(BaseModel):
    items: list[ThemeResponse]
    total: int
    skip: int
    limit: int


class PaginatedWidgetsResponse(BaseModel):
    items: list[WidgetResponse]
    total: int
    skip: int
    limit: int


class PaginatedDashboardsResponse(BaseModel):
    items: list[DashboardResponse]
    total: int
    skip: int
    limit: int


class PaginatedPagesResponse(BaseModel):
    items: list[CustomPageResponse]
    total: int
    skip: int
    limit: int


class PaginatedComponentsResponse(BaseModel):
    items: list[ComponentResponse]
    total: int
    skip: int
    limit: int
