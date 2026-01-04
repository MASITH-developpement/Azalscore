"""
AZALS MODULE T7 - Modèles Web Transverse
========================================

Modèles SQLAlchemy pour la configuration web.
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, Enum, Index, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class ThemeMode(str, PyEnum):
    """Modes de thème"""
    LIGHT = "LIGHT"
    DARK = "DARK"
    SYSTEM = "SYSTEM"
    HIGH_CONTRAST = "HIGH_CONTRAST"


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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Mode de base
    mode = Column(Enum(ThemeMode), default=ThemeMode.LIGHT)

    # Couleurs principales
    primary_color = Column(String(20), default="#1976D2")
    secondary_color = Column(String(20), default="#424242")
    accent_color = Column(String(20), default="#82B1FF")
    error_color = Column(String(20), default="#FF5252")
    warning_color = Column(String(20), default="#FB8C00")
    success_color = Column(String(20), default="#4CAF50")
    info_color = Column(String(20), default="#2196F3")

    # Couleurs de fond
    background_color = Column(String(20), default="#FFFFFF")
    surface_color = Column(String(20), default="#FAFAFA")
    card_color = Column(String(20), default="#FFFFFF")

    # Couleurs de texte
    text_primary = Column(String(20), default="#212121")
    text_secondary = Column(String(20), default="#757575")
    text_disabled = Column(String(20), default="#9E9E9E")

    # Typographie
    font_family = Column(String(200), default="'Roboto', sans-serif")
    font_size_base = Column(String(10), default="14px")

    # Bordures et ombres
    border_radius = Column(String(10), default="4px")
    box_shadow = Column(String(200), nullable=True)

    # Configuration complète (JSON)
    full_config = Column(JSON, nullable=True)

    # État
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Type et taille
    widget_type = Column(Enum(WidgetType), nullable=False)
    default_size = Column(Enum(WidgetSize), default=WidgetSize.MEDIUM)

    # Source de données
    data_source = Column(String(200), nullable=True)  # Endpoint API
    data_query = Column(JSON, nullable=True)  # Requête/filtres
    refresh_interval = Column(Integer, default=60)  # Secondes

    # Configuration affichage
    display_config = Column(JSON, nullable=True)  # Options d'affichage
    chart_config = Column(JSON, nullable=True)  # Pour CHART type

    # Permissions
    required_permission = Column(String(100), nullable=True)
    visible_roles = Column(JSON, nullable=True)

    # État
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Type et layout
    page_type = Column(Enum(PageType), default=PageType.DASHBOARD)
    layout_type = Column(String(50), default="grid")  # grid, flex, masonry
    columns = Column(Integer, default=4)

    # Widgets (ordre et position)
    widgets_config = Column(JSON, nullable=True)  # [{widget_id, position, size}]

    # Filtres par défaut
    default_filters = Column(JSON, nullable=True)
    date_range = Column(String(50), nullable=True)  # last_7_days, etc.

    # Permissions
    visible_roles = Column(JSON, nullable=True)
    editable_roles = Column(JSON, nullable=True)

    # État
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)
    owner_id = Column(Integer, nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Type de menu
    menu_type = Column(Enum(MenuType), default=MenuType.MAIN)

    # Identification
    code = Column(String(50), nullable=False)
    label = Column(String(200), nullable=False)
    icon = Column(String(100), nullable=True)

    # Navigation
    route = Column(String(500), nullable=True)
    external_url = Column(String(500), nullable=True)
    target = Column(String(20), default="_self")

    # Hiérarchie
    parent_id = Column(Integer, ForeignKey("web_menu_items.id"), nullable=True)
    sort_order = Column(Integer, default=0)

    # Permissions
    required_permission = Column(String(100), nullable=True)
    visible_roles = Column(JSON, nullable=True)

    # Badge (notification)
    badge_source = Column(String(200), nullable=True)  # Endpoint API pour badge
    badge_color = Column(String(20), nullable=True)

    # État
    is_active = Column(Boolean, default=True)
    is_separator = Column(Boolean, default=False)
    is_expanded = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Catégorie
    category = Column(Enum(ComponentCategory), nullable=False)

    # Configuration
    props_schema = Column(JSON, nullable=True)  # Schéma des propriétés
    default_props = Column(JSON, nullable=True)  # Valeurs par défaut
    template = Column(Text, nullable=True)  # Template HTML/Vue

    # Styles
    styles = Column(Text, nullable=True)  # CSS personnalisé
    css_classes = Column(JSON, nullable=True)  # Classes CSS

    # État
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, nullable=False)

    # Thème
    theme_id = Column(Integer, ForeignKey("web_themes.id"), nullable=True)
    theme_mode = Column(Enum(ThemeMode), default=ThemeMode.SYSTEM)

    # Layout
    sidebar_collapsed = Column(Boolean, default=False)
    sidebar_mini = Column(Boolean, default=False)
    toolbar_dense = Column(Boolean, default=False)

    # Dashboard
    default_dashboard_id = Column(Integer, ForeignKey("web_dashboards.id"), nullable=True)
    dashboard_auto_refresh = Column(Boolean, default=True)

    # Table preferences
    table_density = Column(String(20), default="default")  # compact, default, comfortable
    table_page_size = Column(Integer, default=25)

    # Accessibilité
    font_size = Column(String(20), default="medium")  # small, medium, large
    high_contrast = Column(Boolean, default=False)
    reduced_motion = Column(Boolean, default=False)

    # Langue et région
    language = Column(String(5), default="fr")
    date_format = Column(String(20), default="DD/MM/YYYY")
    time_format = Column(String(20), default="24h")
    timezone = Column(String(50), default="Europe/Paris")

    # Notifications UI
    show_tooltips = Column(Boolean, default=True)
    sound_enabled = Column(Boolean, default=True)
    desktop_notifications = Column(Boolean, default=False)

    # Raccourcis personnalisés
    custom_shortcuts = Column(JSON, nullable=True)

    # Widgets favoris
    favorite_widgets = Column(JSON, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_web_user_prefs_tenant_user", "tenant_id", "user_id", unique=True),
    )


# ============================================================================
# MODÈLE: RACCOURCI CLAVIER
# ============================================================================

class Shortcut(Base):
    """Raccourci clavier"""
    __tablename__ = "web_shortcuts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Combinaison de touches
    key_combination = Column(String(100), nullable=False)  # Ex: "Ctrl+Shift+N"
    key_code = Column(String(50), nullable=True)  # Code technique

    # Action
    action_type = Column(String(50), nullable=False)  # navigate, execute, toggle
    action_value = Column(String(500), nullable=True)  # Route ou commande

    # Contexte
    context = Column(String(100), default="global")  # global, dashboard, form, etc.

    # État
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    slug = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Type et contenu
    page_type = Column(Enum(PageType), default=PageType.CUSTOM)
    content = Column(Text, nullable=True)  # HTML/Markdown
    template = Column(String(100), nullable=True)  # Template à utiliser
    data_source = Column(String(200), nullable=True)

    # Layout
    layout = Column(String(50), default="default")
    show_sidebar = Column(Boolean, default=True)
    show_toolbar = Column(Boolean, default=True)

    # SEO
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(String(500), nullable=True)

    # Permissions
    required_permission = Column(String(100), nullable=True)
    visible_roles = Column(JSON, nullable=True)

    # État
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_web_pages_tenant_slug", "tenant_id", "slug", unique=True),
        Index("ix_web_pages_tenant_type", "tenant_id", "page_type"),
    )
