"""
AZALS MODULE T7 - Schémas Pydantic Web Transverse
=================================================

Schémas de validation pour les API du module Web.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator
import json


# ============================================================================
# ENUMS
# ============================================================================

class ThemeModeEnum(str, Enum):
    LIGHT = "LIGHT"
    DARK = "DARK"
    SYSTEM = "SYSTEM"
    HIGH_CONTRAST = "HIGH_CONTRAST"


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
    description: Optional[str] = None
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
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    mode: Optional[ThemeModeEnum] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_color: Optional[str] = None
    text_primary: Optional[str] = None
    font_family: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class ThemeResponse(ThemeBase):
    id: int
    is_active: bool
    is_default: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# WIDGETS
# ============================================================================

class WidgetBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    widget_type: WidgetTypeEnum
    default_size: WidgetSizeEnum = WidgetSizeEnum.MEDIUM


class WidgetCreate(WidgetBase):
    data_source: Optional[str] = None
    data_query: Optional[Dict[str, Any]] = None
    display_config: Optional[Dict[str, Any]] = None
    chart_config: Optional[Dict[str, Any]] = None
    refresh_interval: int = 60
    required_permission: Optional[str] = None


class WidgetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    default_size: Optional[WidgetSizeEnum] = None
    data_source: Optional[str] = None
    data_query: Optional[Dict[str, Any]] = None
    display_config: Optional[Dict[str, Any]] = None
    chart_config: Optional[Dict[str, Any]] = None
    refresh_interval: Optional[int] = None
    is_active: Optional[bool] = None


class WidgetResponse(WidgetBase):
    id: int
    data_source: Optional[str] = None
    data_query: Optional[Dict[str, Any]] = None
    display_config: Optional[Dict[str, Any]] = None
    chart_config: Optional[Dict[str, Any]] = None
    refresh_interval: int
    required_permission: Optional[str] = None
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

    @field_validator("data_query", "display_config", "chart_config", mode="before")
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return v
        return v


# ============================================================================
# DASHBOARDS
# ============================================================================

class DashboardBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
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
    widgets_config: Optional[List[WidgetPosition]] = None
    default_filters: Optional[Dict[str, Any]] = None
    is_default: bool = False
    is_public: bool = False


class DashboardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    layout_type: Optional[str] = None
    columns: Optional[int] = Field(None, ge=1, le=12)
    widgets_config: Optional[List[WidgetPosition]] = None
    default_filters: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class DashboardResponse(DashboardBase):
    id: int
    widgets_config: Optional[List[Dict[str, Any]]] = None
    default_filters: Optional[Dict[str, Any]] = None
    is_active: bool
    is_default: bool
    is_public: bool
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

    @field_validator("widgets_config", "default_filters", mode="before")
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return v
        return v


# ============================================================================
# MENUS
# ============================================================================

class MenuItemBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    label: str = Field(..., min_length=1, max_length=200)
    icon: Optional[str] = None
    route: Optional[str] = None
    menu_type: MenuTypeEnum = MenuTypeEnum.MAIN


class MenuItemCreate(MenuItemBase):
    parent_id: Optional[int] = None
    sort_order: int = 0
    external_url: Optional[str] = None
    target: str = "_self"
    required_permission: Optional[str] = None
    is_separator: bool = False


class MenuItemUpdate(BaseModel):
    label: Optional[str] = Field(None, min_length=1, max_length=200)
    icon: Optional[str] = None
    route: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    external_url: Optional[str] = None
    required_permission: Optional[str] = None
    is_active: Optional[bool] = None
    is_separator: Optional[bool] = None


class MenuItemResponse(MenuItemBase):
    id: int
    parent_id: Optional[int] = None
    sort_order: int
    external_url: Optional[str] = None
    target: str
    required_permission: Optional[str] = None
    is_active: bool
    is_separator: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MenuTreeNode(BaseModel):
    id: int
    code: str
    label: str
    icon: Optional[str] = None
    route: Optional[str] = None
    is_separator: bool = False
    children: List["MenuTreeNode"] = []


# ============================================================================
# PRÉFÉRENCES UTILISATEUR
# ============================================================================

class UserPreferenceCreate(BaseModel):
    theme_id: Optional[int] = None
    theme_mode: ThemeModeEnum = ThemeModeEnum.SYSTEM
    sidebar_collapsed: bool = False
    sidebar_mini: bool = False
    toolbar_dense: bool = False
    default_dashboard_id: Optional[int] = None
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
    id: int
    user_id: int
    theme_id: Optional[int] = None
    theme_mode: ThemeModeEnum
    sidebar_collapsed: bool
    sidebar_mini: bool
    toolbar_dense: bool
    default_dashboard_id: Optional[int] = None
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
    custom_shortcuts: Optional[Dict[str, Any]] = None
    favorite_widgets: Optional[List[int]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_validator("custom_shortcuts", "favorite_widgets", mode="before")
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return v
        return v


# ============================================================================
# RACCOURCIS
# ============================================================================

class ShortcutCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    key_combination: str = Field(..., min_length=1, max_length=100)
    action_type: str = Field(..., min_length=2, max_length=50)
    action_value: Optional[str] = None
    context: str = "global"


class ShortcutResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    key_combination: str
    action_type: str
    action_value: Optional[str] = None
    context: str
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PAGES PERSONNALISÉES
# ============================================================================

class CustomPageCreate(BaseModel):
    slug: str = Field(..., min_length=2, max_length=100)
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    page_type: PageTypeEnum = PageTypeEnum.CUSTOM
    content: Optional[str] = None
    template: Optional[str] = None
    layout: str = "default"
    show_sidebar: bool = True
    show_toolbar: bool = True
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    required_permission: Optional[str] = None


class CustomPageUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = None
    template: Optional[str] = None
    layout: Optional[str] = None
    show_sidebar: Optional[bool] = None
    show_toolbar: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    required_permission: Optional[str] = None
    is_active: Optional[bool] = None


class CustomPageResponse(BaseModel):
    id: int
    slug: str
    title: str
    description: Optional[str] = None
    page_type: PageTypeEnum
    content: Optional[str] = None
    template: Optional[str] = None
    layout: str
    show_sidebar: bool
    show_toolbar: bool
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    required_permission: Optional[str] = None
    is_active: bool
    is_published: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# COMPOSANTS UI
# ============================================================================

class ComponentCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    category: ComponentCategoryEnum
    props_schema: Optional[Dict[str, Any]] = None
    default_props: Optional[Dict[str, Any]] = None
    template: Optional[str] = None
    styles: Optional[str] = None


class ComponentResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    category: ComponentCategoryEnum
    props_schema: Optional[Dict[str, Any]] = None
    default_props: Optional[Dict[str, Any]] = None
    template: Optional[str] = None
    styles: Optional[str] = None
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

    @field_validator("props_schema", "default_props", mode="before")
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return v
        return v


# ============================================================================
# CONFIG UI COMPLÈTE
# ============================================================================

class UIConfigResponse(BaseModel):
    theme: Optional[Dict[str, Any]] = None
    preferences: Dict[str, Any] = {}
    menu: List[Dict[str, Any]] = []
    shortcuts: List[Dict[str, str]] = []


# ============================================================================
# LISTES PAGINÉES
# ============================================================================

class PaginatedThemesResponse(BaseModel):
    items: List[ThemeResponse]
    total: int
    skip: int
    limit: int


class PaginatedWidgetsResponse(BaseModel):
    items: List[WidgetResponse]
    total: int
    skip: int
    limit: int


class PaginatedDashboardsResponse(BaseModel):
    items: List[DashboardResponse]
    total: int
    skip: int
    limit: int


class PaginatedPagesResponse(BaseModel):
    items: List[CustomPageResponse]
    total: int
    skip: int
    limit: int


class PaginatedComponentsResponse(BaseModel):
    items: List[ComponentResponse]
    total: int
    skip: int
    limit: int
