"""
AZALS MODULE T7 - Modèles Web Transverse
========================================

Modèles SQLAlchemy pour la configuration web.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.types import JSON, UniversalUUID
from app.db import Base

# ============================================================================
# ENUMS
# ============================================================================

class ThemeMode(str, PyEnum):
    """Modes de thème"""
    LIGHT = "LIGHT"
    DARK = "DARK"
    SYSTEM = "SYSTEM"
    HIGH_CONTRAST = "HIGH_CONTRAST"


class UIStyle(str, PyEnum):
    """Styles visuels de l'interface"""
    CLASSIC = "CLASSIC"
    MODERN = "MODERN"
    GLASS = "GLASS"


class WidgetType(str, PyEnum):
    """Types de widgets"""
    KPI = "KPI"
    CHART = "CHART"
    TABLE = "TABLE"
    LIST = "LIST"
    CALENDAR = "CALENDAR"
    MAP = "MAP"
    GAUGE = "GAUGE"
    TIMELINE = "TIMELINE"
    CUSTOM = "CUSTOM"


class WidgetSize(str, PyEnum):
    """Tailles de widgets"""
    SMALL = "SMALL"      # 1x1
    MEDIUM = "MEDIUM"    # 2x1
    LARGE = "LARGE"      # 2x2
    WIDE = "WIDE"        # 4x1
    TALL = "TALL"        # 1x2
    FULL = "FULL"        # 4x2


class ComponentCategory(str, PyEnum):
    """Catégories de composants"""
    LAYOUT = "LAYOUT"
    NAVIGATION = "NAVIGATION"
    FORMS = "FORMS"
    DATA_DISPLAY = "DATA_DISPLAY"
    FEEDBACK = "FEEDBACK"
    CHARTS = "CHARTS"
    ACTIONS = "ACTIONS"


class MenuType(str, PyEnum):
    """Types de menu"""
    MAIN = "MAIN"
    SIDEBAR = "SIDEBAR"
    TOOLBAR = "TOOLBAR"
    CONTEXT = "CONTEXT"
    FOOTER = "FOOTER"


class PageType(str, PyEnum):
    """Types de pages"""
    DASHBOARD = "DASHBOARD"
    LIST = "LIST"
    FORM = "FORM"
    DETAIL = "DETAIL"
    REPORT = "REPORT"
    CUSTOM = "CUSTOM"


# ============================================================================
# MODÈLE: THÈME
# ============================================================================

class Theme(Base):
    """Configuration de thème"""
    __tablename__ = "web_themes"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    code: Mapped[str | None] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Mode de base
    mode: Mapped[str | None] = mapped_column(Enum(ThemeMode), default=ThemeMode.LIGHT)

    # Couleurs principales
    primary_color: Mapped[str | None] = mapped_column(String(20), default="#1976D2")
    secondary_color: Mapped[str | None] = mapped_column(String(20), default="#424242")
    accent_color: Mapped[str | None] = mapped_column(String(20), default="#82B1FF")
    error_color: Mapped[str | None] = mapped_column(String(20), default="#FF5252")
    warning_color: Mapped[str | None] = mapped_column(String(20), default="#FB8C00")
    success_color: Mapped[str | None] = mapped_column(String(20), default="#4CAF50")
    info_color: Mapped[str | None] = mapped_column(String(20), default="#2196F3")

    # Couleurs de fond
    background_color: Mapped[str | None] = mapped_column(String(20), default="#FFFFFF")
    surface_color: Mapped[str | None] = mapped_column(String(20), default="#FAFAFA")
    card_color: Mapped[str | None] = mapped_column(String(20), default="#FFFFFF")

    # Couleurs de texte
    text_primary: Mapped[str | None] = mapped_column(String(20), default="#212121")
    text_secondary: Mapped[str | None] = mapped_column(String(20), default="#757575")
    text_disabled: Mapped[str | None] = mapped_column(String(20), default="#9E9E9E")

    # Typographie
    font_family: Mapped[str | None] = mapped_column(String(200), default="'Roboto', sans-serif")
    font_size_base: Mapped[str | None] = mapped_column(String(10), default="14px")

    # Bordures et ombres
    border_radius: Mapped[str | None] = mapped_column(String(10), default="4px")
    box_shadow: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Configuration complète (JSON)
    full_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # État
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_system: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index("ix_web_themes_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_web_themes_tenant_default", "tenant_id", "is_default"),
    )


# ============================================================================
# MODÈLE: WIDGET
# ============================================================================

class Widget(Base):
    """Définition de widget"""
    __tablename__ = "web_widgets"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    code: Mapped[str | None] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Type et taille
    widget_type: Mapped[str | None] = mapped_column(Enum(WidgetType), nullable=False)
    default_size: Mapped[str | None] = mapped_column(Enum(WidgetSize), default=WidgetSize.MEDIUM)

    # Source de données
    data_source: Mapped[str | None] = mapped_column(String(200), nullable=True)  # Endpoint API
    data_query: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Requête/filtres
    refresh_interval: Mapped[int | None] = mapped_column(Integer, default=60)  # Secondes

    # Configuration affichage
    display_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Options d'affichage
    chart_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Pour CHART type

    # Permissions
    required_permission: Mapped[str | None] = mapped_column(String(100), nullable=True)
    visible_roles: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # État
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index("ix_web_widgets_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_web_widgets_tenant_type", "tenant_id", "widget_type"),
    )


# ============================================================================
# MODÈLE: DASHBOARD
# ============================================================================

class WebDashboard(Base):
    """Configuration de dashboard (distinct de bi.Dashboard)"""
    __tablename__ = "web_dashboards"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    code: Mapped[str | None] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Type et layout
    page_type: Mapped[str | None] = mapped_column(Enum(PageType), default=PageType.DASHBOARD)
    layout_type: Mapped[str | None] = mapped_column(String(50), default="grid")  # grid, flex, masonry
    columns: Mapped[int | None] = mapped_column(Integer, default=4)

    # Widgets (ordre et position)
    widgets_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # [{widget_id, position, size}]

    # Filtres par défaut
    default_filters: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    date_range: Mapped[str | None] = mapped_column(String(50), nullable=True)  # last_7_days, etc.

    # Permissions
    visible_roles: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    editable_roles: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # État
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index("ix_web_dashboards_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_web_dashboards_tenant_default", "tenant_id", "is_default"),
        Index("ix_web_dashboards_owner", "tenant_id", "owner_id"),
    )


# ============================================================================
# MODÈLE: MENU
# ============================================================================

class MenuItem(Base):
    """Élément de menu"""
    __tablename__ = "web_menu_items"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Type de menu
    menu_type: Mapped[str | None] = mapped_column(Enum(MenuType), default=MenuType.MAIN)

    # Identification
    code: Mapped[str | None] = mapped_column(String(50), nullable=False)
    label: Mapped[str | None] = mapped_column(String(200), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Navigation
    route: Mapped[str | None] = mapped_column(String(500), nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    target: Mapped[str | None] = mapped_column(String(20), default="_self")

    # Hiérarchie
    parent_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("web_menu_items.id"), nullable=True)
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)

    # Permissions
    required_permission: Mapped[str | None] = mapped_column(String(100), nullable=True)
    visible_roles: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Badge (notification)
    badge_source: Mapped[str | None] = mapped_column(String(200), nullable=True)  # Endpoint API pour badge
    badge_color: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # État
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_separator: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_expanded: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_web_menu_tenant_type", "tenant_id", "menu_type"),
        Index("ix_web_menu_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_web_menu_parent", "tenant_id", "parent_id"),
    )


# ============================================================================
# MODÈLE: COMPOSANT UI
# ============================================================================

class UIComponent(Base):
    """Composant UI réutilisable"""
    __tablename__ = "web_ui_components"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    code: Mapped[str | None] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Catégorie
    category: Mapped[str | None] = mapped_column(Enum(ComponentCategory), nullable=False)

    # Configuration
    props_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Schéma des propriétés
    default_props: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Valeurs par défaut
    template: Mapped[str | None] = mapped_column(Text, nullable=True)  # Template HTML/Vue

    # Styles
    styles: Mapped[str | None] = mapped_column(Text, nullable=True)  # CSS personnalisé
    css_classes: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Classes CSS

    # État
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index("ix_web_components_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_web_components_tenant_category", "tenant_id", "category"),
    )


# ============================================================================
# MODÈLE: PRÉFÉRENCES UI UTILISATEUR
# ============================================================================

class UserUIPreference(Base):
    """Préférences interface utilisateur"""
    __tablename__ = "web_user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False)

    # Thème
    theme_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("web_themes.id"), nullable=True)
    theme_mode: Mapped[str | None] = mapped_column(Enum(ThemeMode), default=ThemeMode.SYSTEM)
    ui_style: Mapped[str | None] = mapped_column(Enum(UIStyle), default=UIStyle.CLASSIC)

    # Layout
    sidebar_collapsed: Mapped[bool | None] = mapped_column(Boolean, default=False)
    sidebar_mini: Mapped[bool | None] = mapped_column(Boolean, default=False)
    toolbar_dense: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Dashboard
    default_dashboard_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("web_dashboards.id"), nullable=True)
    dashboard_auto_refresh: Mapped[bool | None] = mapped_column(Boolean, default=True)

    # Table preferences
    table_density: Mapped[str | None] = mapped_column(String(20), default="default")  # compact, default, comfortable
    table_page_size: Mapped[int | None] = mapped_column(Integer, default=25)

    # Accessibilité
    font_size: Mapped[str | None] = mapped_column(String(20), default="medium")  # small, medium, large
    high_contrast: Mapped[bool | None] = mapped_column(Boolean, default=False)
    reduced_motion: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Langue et région
    language: Mapped[str | None] = mapped_column(String(5), default="fr")
    date_format: Mapped[str | None] = mapped_column(String(20), default="DD/MM/YYYY")
    time_format: Mapped[str | None] = mapped_column(String(20), default="24h")
    timezone: Mapped[str | None] = mapped_column(String(50), default="Europe/Paris")

    # Notifications UI
    show_tooltips: Mapped[bool | None] = mapped_column(Boolean, default=True)
    sound_enabled: Mapped[bool | None] = mapped_column(Boolean, default=True)
    desktop_notifications: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Raccourcis personnalisés
    custom_shortcuts: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Widgets favoris
    favorite_widgets: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_web_user_prefs_tenant_user", "tenant_id", "user_id", unique=True),
    )


# ============================================================================
# MODÈLE: RACCOURCI CLAVIER
# ============================================================================

class Shortcut(Base):
    """Raccourci clavier"""
    __tablename__ = "web_shortcuts"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    code: Mapped[str | None] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Combinaison de touches
    key_combination: Mapped[str | None] = mapped_column(String(100), nullable=False)  # Ex: "Ctrl+Shift+N"
    key_code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Code technique

    # Action
    action_type: Mapped[str | None] = mapped_column(String(50), nullable=False)  # navigate, execute, toggle
    action_value: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Route ou commande

    # Contexte
    context: Mapped[str | None] = mapped_column(String(100), default="global")  # global, dashboard, form, etc.

    # État
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_web_shortcuts_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_web_shortcuts_tenant_context", "tenant_id", "context"),
    )


# ============================================================================
# MODÈLE: PAGE PERSONNALISÉE
# ============================================================================

class CustomPage(Base):
    """Page personnalisée"""
    __tablename__ = "web_custom_pages"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    slug: Mapped[str | None] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Type et contenu
    page_type: Mapped[str | None] = mapped_column(Enum(PageType), default=PageType.CUSTOM)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # HTML/Markdown
    template: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Template à utiliser
    data_source: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Layout
    layout: Mapped[str | None] = mapped_column(String(50), default="default")
    show_sidebar: Mapped[bool | None] = mapped_column(Boolean, default=True)
    show_toolbar: Mapped[bool | None] = mapped_column(Boolean, default=True)

    # SEO
    meta_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Permissions
    required_permission: Mapped[str | None] = mapped_column(String(100), nullable=True)
    visible_roles: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # État
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_published: Mapped[bool | None] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index("ix_web_pages_tenant_slug", "tenant_id", "slug", unique=True),
        Index("ix_web_pages_tenant_type", "tenant_id", "page_type"),
    )
