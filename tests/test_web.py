"""
AZALS MODULE T7 - Tests Web Transverse
======================================

Tests unitaires pour le module de composants web.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
import json

# Import des modèles
from app.modules.web.models import (
    Theme, Widget, Dashboard, MenuItem, UIComponent,
    UserUIPreference, Shortcut, CustomPage,
    ThemeMode, WidgetType, WidgetSize, ComponentCategory,
    MenuType, PageType
)

# Import des schémas
from app.modules.web.schemas import (
    ThemeCreate, ThemeUpdate, ThemeResponse,
    WidgetCreate, WidgetResponse,
    DashboardCreate, DashboardResponse,
    MenuItemCreate, MenuItemResponse,
    UserPreferenceCreate, UserPreferenceResponse,
    ShortcutCreate, ShortcutResponse,
    CustomPageCreate, CustomPageResponse,
    ComponentCreate, ComponentResponse,
    ThemeModeEnum, WidgetTypeEnum, WidgetSizeEnum,
    ComponentCategoryEnum, MenuTypeEnum, PageTypeEnum
)

# Import du service
from app.modules.web.service import WebService, get_web_service


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock de la session DB."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


@pytest.fixture
def tenant_id():
    """ID tenant de test."""
    return "test-tenant-001"


@pytest.fixture
def web_service(mock_db, tenant_id):
    """Service web initialisé."""
    return WebService(mock_db, tenant_id)


@pytest.fixture
def sample_theme():
    """Thème de test."""
    theme = MagicMock(spec=Theme)
    theme.id = 1
    theme.tenant_id = "test-tenant-001"
    theme.code = "custom-light"
    theme.name = "Thème Personnalisé"
    theme.mode = ThemeMode.LIGHT
    theme.primary_color = "#1976D2"
    theme.is_active = True
    theme.is_default = False
    theme.is_system = False
    theme.created_at = datetime.utcnow()
    theme.updated_at = datetime.utcnow()
    return theme


@pytest.fixture
def sample_widget():
    """Widget de test."""
    widget = MagicMock(spec=Widget)
    widget.id = 1
    widget.tenant_id = "test-tenant-001"
    widget.code = "kpi-custom"
    widget.name = "KPI Personnalisé"
    widget.widget_type = WidgetType.KPI
    widget.default_size = WidgetSize.MEDIUM
    widget.is_active = True
    widget.is_system = False
    return widget


@pytest.fixture
def sample_dashboard():
    """Dashboard de test."""
    dashboard = MagicMock(spec=Dashboard)
    dashboard.id = 1
    dashboard.tenant_id = "test-tenant-001"
    dashboard.code = "main-dashboard"
    dashboard.name = "Dashboard Principal"
    dashboard.page_type = PageType.DASHBOARD
    dashboard.layout_type = "grid"
    dashboard.columns = 4
    dashboard.is_active = True
    dashboard.is_default = True
    return dashboard


# ============================================================================
# TESTS ENUMS
# ============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_theme_mode_values(self):
        """Vérifier les valeurs ThemeMode."""
        assert ThemeMode.LIGHT.value == "LIGHT"
        assert ThemeMode.DARK.value == "DARK"
        assert ThemeMode.SYSTEM.value == "SYSTEM"
        assert ThemeMode.HIGH_CONTRAST.value == "HIGH_CONTRAST"

    def test_widget_type_values(self):
        """Vérifier les valeurs WidgetType."""
        assert WidgetType.KPI.value == "KPI"
        assert WidgetType.CHART.value == "CHART"
        assert WidgetType.TABLE.value == "TABLE"
        assert WidgetType.CALENDAR.value == "CALENDAR"
        assert WidgetType.GAUGE.value == "GAUGE"

    def test_widget_size_values(self):
        """Vérifier les valeurs WidgetSize."""
        assert WidgetSize.SMALL.value == "SMALL"
        assert WidgetSize.MEDIUM.value == "MEDIUM"
        assert WidgetSize.LARGE.value == "LARGE"
        assert WidgetSize.WIDE.value == "WIDE"
        assert WidgetSize.FULL.value == "FULL"

    def test_component_category_values(self):
        """Vérifier les valeurs ComponentCategory."""
        assert ComponentCategory.LAYOUT.value == "LAYOUT"
        assert ComponentCategory.NAVIGATION.value == "NAVIGATION"
        assert ComponentCategory.FORMS.value == "FORMS"
        assert ComponentCategory.CHARTS.value == "CHARTS"

    def test_menu_type_values(self):
        """Vérifier les valeurs MenuType."""
        assert MenuType.MAIN.value == "MAIN"
        assert MenuType.SIDEBAR.value == "SIDEBAR"
        assert MenuType.TOOLBAR.value == "TOOLBAR"

    def test_page_type_values(self):
        """Vérifier les valeurs PageType."""
        assert PageType.DASHBOARD.value == "DASHBOARD"
        assert PageType.LIST.value == "LIST"
        assert PageType.FORM.value == "FORM"
        assert PageType.CUSTOM.value == "CUSTOM"


# ============================================================================
# TESTS MODÈLES
# ============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_theme_creation(self):
        """Tester la création d'un thème."""
        theme = Theme(
            tenant_id="tenant-001",
            code="my-theme",
            name="Mon Thème",
            mode=ThemeMode.DARK,
            primary_color="#FF0000"
        )
        assert theme.code == "my-theme"
        assert theme.mode == ThemeMode.DARK
        assert theme.is_active == True

    def test_widget_creation(self):
        """Tester la création d'un widget."""
        widget = Widget(
            tenant_id="tenant-001",
            code="my-widget",
            name="Mon Widget",
            widget_type=WidgetType.CHART,
            default_size=WidgetSize.LARGE
        )
        assert widget.code == "my-widget"
        assert widget.widget_type == WidgetType.CHART
        assert widget.default_size == WidgetSize.LARGE

    def test_dashboard_creation(self):
        """Tester la création d'un dashboard."""
        dashboard = Dashboard(
            tenant_id="tenant-001",
            code="my-dashboard",
            name="Mon Dashboard",
            page_type=PageType.DASHBOARD,
            columns=3
        )
        assert dashboard.code == "my-dashboard"
        assert dashboard.columns == 3
        assert dashboard.is_default == False

    def test_menu_item_creation(self):
        """Tester la création d'un élément de menu."""
        item = MenuItem(
            tenant_id="tenant-001",
            code="menu-home",
            label="Accueil",
            menu_type=MenuType.MAIN,
            route="/",
            icon="home"
        )
        assert item.code == "menu-home"
        assert item.menu_type == MenuType.MAIN
        assert item.icon == "home"

    def test_ui_component_creation(self):
        """Tester la création d'un composant UI."""
        component = UIComponent(
            tenant_id="tenant-001",
            code="button-primary",
            name="Bouton Principal",
            category=ComponentCategory.ACTIONS
        )
        assert component.code == "button-primary"
        assert component.category == ComponentCategory.ACTIONS

    def test_user_preference_creation(self):
        """Tester la création de préférences."""
        pref = UserUIPreference(
            tenant_id="tenant-001",
            user_id=42,
            theme_mode=ThemeMode.DARK,
            sidebar_collapsed=True
        )
        assert pref.user_id == 42
        assert pref.theme_mode == ThemeMode.DARK
        assert pref.sidebar_collapsed == True


# ============================================================================
# TESTS SCHÉMAS
# ============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_theme_create_schema(self):
        """Tester le schéma de création thème."""
        data = ThemeCreate(
            code="new-theme",
            name="Nouveau Thème",
            mode=ThemeModeEnum.DARK,
            primary_color="#FF5500"
        )
        assert data.code == "new-theme"
        assert data.mode == ThemeModeEnum.DARK

    def test_widget_create_schema(self):
        """Tester le schéma de création widget."""
        data = WidgetCreate(
            code="new-widget",
            name="Nouveau Widget",
            widget_type=WidgetTypeEnum.KPI,
            default_size=WidgetSizeEnum.MEDIUM,
            refresh_interval=30
        )
        assert data.code == "new-widget"
        assert data.widget_type == WidgetTypeEnum.KPI
        assert data.refresh_interval == 30

    def test_dashboard_create_schema(self):
        """Tester le schéma de création dashboard."""
        data = DashboardCreate(
            code="new-dashboard",
            name="Nouveau Dashboard",
            page_type=PageTypeEnum.DASHBOARD,
            columns=4,
            is_public=True
        )
        assert data.code == "new-dashboard"
        assert data.columns == 4
        assert data.is_public == True

    def test_menu_item_create_schema(self):
        """Tester le schéma de création menu."""
        data = MenuItemCreate(
            code="menu-item",
            label="Item",
            menu_type=MenuTypeEnum.MAIN,
            route="/test",
            sort_order=10
        )
        assert data.code == "menu-item"
        assert data.sort_order == 10

    def test_user_preference_create_schema(self):
        """Tester le schéma de préférences."""
        data = UserPreferenceCreate(
            theme_mode=ThemeModeEnum.SYSTEM,
            sidebar_collapsed=False,
            table_page_size=50,
            language="en"
        )
        assert data.theme_mode == ThemeModeEnum.SYSTEM
        assert data.table_page_size == 50
        assert data.language == "en"


# ============================================================================
# TESTS SERVICE - THÈMES
# ============================================================================

class TestServiceThemes:
    """Tests du service - Thèmes."""

    def test_create_theme(self, web_service, mock_db):
        """Tester la création d'un thème."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = web_service.create_theme(
            code="test-theme",
            name="Test Thème",
            mode=ThemeMode.LIGHT,
            created_by=1
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    def test_get_theme(self, web_service, mock_db, sample_theme):
        """Tester la récupération d'un thème."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_theme

        result = web_service.get_theme(1)

        assert result is not None
        assert result.code == "custom-light"

    def test_get_default_theme(self, web_service, mock_db, sample_theme):
        """Tester la récupération du thème par défaut."""
        sample_theme.is_default = True
        mock_db.query.return_value.filter.return_value.first.return_value = sample_theme

        result = web_service.get_default_theme()

        assert result is not None

    def test_list_themes(self, web_service, mock_db, sample_theme):
        """Tester le listing des thèmes."""
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_theme]

        items, total = web_service.list_themes()

        assert total == 1

    def test_delete_theme(self, web_service, mock_db, sample_theme):
        """Tester la suppression d'un thème."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_theme

        result = web_service.delete_theme(1)

        assert result == True
        mock_db.delete.assert_called_once()


# ============================================================================
# TESTS SERVICE - WIDGETS
# ============================================================================

class TestServiceWidgets:
    """Tests du service - Widgets."""

    def test_create_widget(self, web_service, mock_db):
        """Tester la création d'un widget."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = web_service.create_widget(
            code="test-widget",
            name="Test Widget",
            widget_type=WidgetType.KPI,
            created_by=1
        )

        mock_db.add.assert_called_once()

    def test_get_widget(self, web_service, mock_db, sample_widget):
        """Tester la récupération d'un widget."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_widget

        result = web_service.get_widget(1)

        assert result is not None
        assert result.widget_type == WidgetType.KPI

    def test_list_widgets(self, web_service, mock_db, sample_widget):
        """Tester le listing des widgets."""
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_widget]

        items, total = web_service.list_widgets()

        assert total == 5


# ============================================================================
# TESTS SERVICE - DASHBOARDS
# ============================================================================

class TestServiceDashboards:
    """Tests du service - Dashboards."""

    def test_create_dashboard(self, web_service, mock_db):
        """Tester la création d'un dashboard."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = web_service.create_dashboard(
            code="test-dashboard",
            name="Test Dashboard",
            owner_id=1,
            created_by=1
        )

        mock_db.add.assert_called_once()

    def test_get_dashboard(self, web_service, mock_db, sample_dashboard):
        """Tester la récupération d'un dashboard."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_dashboard

        result = web_service.get_dashboard(1)

        assert result is not None
        assert result.columns == 4

    def test_get_default_dashboard(self, web_service, mock_db, sample_dashboard):
        """Tester la récupération du dashboard par défaut."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_dashboard

        result = web_service.get_default_dashboard()

        assert result is not None


# ============================================================================
# TESTS SERVICE - MENUS
# ============================================================================

class TestServiceMenus:
    """Tests du service - Menus."""

    def test_create_menu_item(self, web_service, mock_db):
        """Tester la création d'un élément de menu."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = web_service.create_menu_item(
            code="test-menu",
            label="Test Menu",
            route="/test"
        )

        mock_db.add.assert_called_once()

    def test_list_menu_items(self, web_service, mock_db):
        """Tester le listing des éléments de menu."""
        mock_item = MagicMock(spec=MenuItem)
        mock_item.id = 1
        mock_item.code = "home"
        mock_item.label = "Accueil"

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_item]

        result = web_service.list_menu_items()

        assert len(result) == 1

    def test_get_menu_tree(self, web_service, mock_db):
        """Tester la récupération de l'arbre de menu."""
        mock_item = MagicMock(spec=MenuItem)
        mock_item.id = 1
        mock_item.code = "home"
        mock_item.label = "Accueil"
        mock_item.icon = "home"
        mock_item.route = "/"
        mock_item.parent_id = None
        mock_item.is_separator = False

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_item]

        result = web_service.get_menu_tree()

        assert len(result) == 1
        assert result[0]["code"] == "home"


# ============================================================================
# TESTS SERVICE - PRÉFÉRENCES
# ============================================================================

class TestServicePreferences:
    """Tests du service - Préférences."""

    def test_get_user_preferences(self, web_service, mock_db):
        """Tester la récupération des préférences."""
        mock_pref = MagicMock(spec=UserUIPreference)
        mock_pref.user_id = 42
        mock_pref.sidebar_collapsed = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_pref

        result = web_service.get_user_preferences(42)

        assert result is not None
        assert result.sidebar_collapsed == True

    def test_set_user_preferences(self, web_service, mock_db):
        """Tester la définition des préférences."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = web_service.set_user_preferences(
            user_id=42,
            sidebar_collapsed=True,
            table_page_size=50
        )

        mock_db.add.assert_called_once()


# ============================================================================
# TESTS SERVICE - UI CONFIG
# ============================================================================

class TestServiceUIConfig:
    """Tests du service - UI Config."""

    def test_get_ui_config(self, web_service, mock_db, sample_theme):
        """Tester la récupération de la config UI."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = web_service.get_ui_config(42)

        assert "theme" in result or result["theme"] is None
        assert "preferences" in result
        assert "menu" in result
        assert "shortcuts" in result


# ============================================================================
# TESTS SERVICE - RACCOURCIS
# ============================================================================

class TestServiceShortcuts:
    """Tests du service - Raccourcis."""

    def test_create_shortcut(self, web_service, mock_db):
        """Tester la création d'un raccourci."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = web_service.create_shortcut(
            code="test-shortcut",
            name="Test Shortcut",
            key_combination="Ctrl+T",
            action_type="navigate",
            action_value="/test"
        )

        mock_db.add.assert_called_once()

    def test_list_shortcuts(self, web_service, mock_db):
        """Tester le listing des raccourcis."""
        mock_shortcut = MagicMock(spec=Shortcut)
        mock_shortcut.code = "search"
        mock_shortcut.key_combination = "Ctrl+K"

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_shortcut]

        result = web_service.list_shortcuts()

        assert len(result) == 1


# ============================================================================
# TESTS SERVICE - PAGES
# ============================================================================

class TestServicePages:
    """Tests du service - Pages."""

    def test_create_custom_page(self, web_service, mock_db):
        """Tester la création d'une page."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = web_service.create_custom_page(
            slug="test-page",
            title="Test Page",
            content="<h1>Test</h1>",
            created_by=1
        )

        mock_db.add.assert_called_once()

    def test_publish_page(self, web_service, mock_db):
        """Tester la publication d'une page."""
        mock_page = MagicMock(spec=CustomPage)
        mock_page.id = 1
        mock_page.is_published = False

        mock_db.query.return_value.filter.return_value.first.return_value = mock_page

        result = web_service.publish_page(1)

        assert result is not None


# ============================================================================
# TESTS FACTORY
# ============================================================================

class TestFactory:
    """Tests de la factory du service."""

    def test_get_web_service(self, mock_db, tenant_id):
        """Tester la création du service."""
        service = get_web_service(mock_db, tenant_id)

        assert service is not None
        assert isinstance(service, WebService)
        assert service.tenant_id == tenant_id


# ============================================================================
# TESTS INTÉGRATION
# ============================================================================

class TestIntegration:
    """Tests d'intégration du module."""

    def test_multi_tenant_isolation(self, mock_db):
        """Tester l'isolation multi-tenant."""
        service1 = WebService(mock_db, "tenant-001")
        service2 = WebService(mock_db, "tenant-002")

        assert service1.tenant_id != service2.tenant_id

    def test_theme_and_preferences_workflow(self, web_service, mock_db, sample_theme):
        """Tester le workflow thème + préférences."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.update = MagicMock()

        # Créer un thème
        theme = web_service.create_theme(
            code="workflow-theme",
            name="Workflow Theme",
            is_default=True,
            created_by=1
        )

        # Définir les préférences
        prefs = web_service.set_user_preferences(
            user_id=42,
            theme_id=1
        )

        assert theme is not None
        assert prefs is not None
