"""
Configuration pytest et fixtures pour les tests Web.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.core.saas_context import SaaSContext, UserRole


@pytest.fixture
def tenant_id():
    """ID du tenant de test."""
    return "tenant-test-001"


@pytest.fixture
def user_id():
    """ID de l'utilisateur de test."""
    return "user-test-001"


@pytest.fixture(autouse=True)
def mock_saas_context(monkeypatch, tenant_id, user_id):
    """Mock get_saas_context pour tous les tests."""
    def mock_get_context():
        return SaaSContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=UserRole.ADMIN,
            permissions={"web.*"},
            scope="tenant",
            session_id="session-test",
            ip_address="127.0.0.1",
            user_agent="pytest",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

    from app.modules.web import router_v2
    monkeypatch.setattr(router_v2, "get_saas_context", mock_get_context)

    return mock_get_context


@pytest.fixture
def mock_web_service(monkeypatch, tenant_id, user_id):
    """Mock du service Web."""
    from app.modules.web.models import ThemeMode, WidgetSize, WidgetType, MenuType

    class MockWebService:
        def __init__(self, db, tenant_id, user_id=None):
            self.db = db
            self.tenant_id = tenant_id
            self.user_id = user_id

        # Themes
        def create_theme(self, **kwargs):
            return {
                "id": str(uuid4()),
                "tenant_id": self.tenant_id,
                "code": kwargs.get("code"),
                "name": kwargs.get("name"),
                "mode": kwargs.get("mode", ThemeMode.LIGHT),
                "primary_color": kwargs.get("primary_color", "#1976D2"),
                "is_active": True,
                "created_at": datetime.utcnow()
            }

        def list_themes(self, **kwargs):
            return [{"id": str(uuid4()), "code": f"THEME-{i}", "name": f"Theme {i}"} for i in range(1, 4)]

        def count_themes(self, **kwargs):
            return 3

        def get_default_theme(self):
            return {"id": str(uuid4()), "code": "DEFAULT", "name": "Default Theme"}

        def get_theme(self, theme_id):
            return {"id": str(uuid4()), "code": "THEME-1", "name": "Theme 1"}

        def update_theme(self, theme_id, **kwargs):
            theme = self.get_theme(theme_id)
            theme.update(kwargs)
            return theme

        def delete_theme(self, theme_id):
            return True

        # Widgets
        def create_widget(self, **kwargs):
            return {
                "id": str(uuid4()),
                "tenant_id": self.tenant_id,
                "code": kwargs.get("code"),
                "name": kwargs.get("name"),
                "widget_type": kwargs.get("widget_type"),
                "size": kwargs.get("size", WidgetSize.MEDIUM),
                "is_active": True
            }

        def list_widgets(self, **kwargs):
            return [{"id": str(uuid4()), "code": f"WDG-{i}", "name": f"Widget {i}"} for i in range(1, 4)]

        def count_widgets(self, **kwargs):
            return 3

        def get_widget(self, widget_id):
            return {"id": str(uuid4()), "code": "WDG-1", "name": "Widget 1"}

        def update_widget(self, widget_id, **kwargs):
            return self.get_widget(widget_id)

        def delete_widget(self, widget_id):
            return True

        # Dashboards
        def create_dashboard(self, **kwargs):
            return {
                "id": str(uuid4()),
                "tenant_id": self.tenant_id,
                "code": kwargs.get("code"),
                "name": kwargs.get("name"),
                "layout": kwargs.get("layout", {})
            }

        def list_dashboards(self, **kwargs):
            return [{"id": str(uuid4()), "code": f"DASH-{i}", "name": f"Dashboard {i}"} for i in range(1, 3)]

        def count_dashboards(self, **kwargs):
            return 2

        def get_default_dashboard(self):
            return {"id": str(uuid4()), "code": "DEFAULT", "name": "Default Dashboard"}

        def get_dashboard(self, dashboard_id):
            return {"id": str(uuid4()), "code": "DASH-1", "name": "Dashboard 1"}

        def update_dashboard(self, dashboard_id, **kwargs):
            return self.get_dashboard(dashboard_id)

        def delete_dashboard(self, dashboard_id):
            return True

        # Menu Items
        def create_menu_item(self, **kwargs):
            return {
                "id": str(uuid4()),
                "tenant_id": self.tenant_id,
                "menu_type": kwargs.get("menu_type"),
                "code": kwargs.get("code"),
                "label": kwargs.get("label"),
                "route": kwargs.get("route")
            }

        def list_menu_items(self, **kwargs):
            return [{"id": str(uuid4()), "code": f"MENU-{i}", "label": f"Menu {i}"} for i in range(1, 4)]

        def get_menu_tree(self, menu_type):
            return [{"id": str(uuid4()), "code": "MENU-1", "label": "Menu 1", "children": []}]

        def update_menu_item(self, item_id, **kwargs):
            return {"id": item_id, "code": "MENU-1", "label": kwargs.get("label", "Menu 1")}

        def delete_menu_item(self, item_id):
            return True

        # Preferences
        def get_user_preferences(self, user_id):
            return {
                "id": str(uuid4()),
                "user_id": user_id,
                "theme_id": None,
                "language": "fr",
                "timezone": "Europe/Paris"
            }

        def update_user_preferences(self, user_id, **kwargs):
            prefs = self.get_user_preferences(user_id)
            prefs.update(kwargs)
            return prefs

        # Config
        def get_ui_config(self):
            return {
                "app_name": "AZALS",
                "logo_url": "/logo.png",
                "features": {"dark_mode": True}
            }

        # Shortcuts
        def create_shortcut(self, **kwargs):
            return {
                "id": str(uuid4()),
                "user_id": kwargs.get("user_id"),
                "label": kwargs.get("label"),
                "route": kwargs.get("route")
            }

        def get_user_shortcuts(self, user_id):
            return [{"id": str(uuid4()), "label": f"Shortcut {i}", "route": f"/page{i}"} for i in range(1, 3)]

        # Pages
        def create_page(self, **kwargs):
            return {
                "id": str(uuid4()),
                "tenant_id": self.tenant_id,
                "title": kwargs.get("title"),
                "slug": kwargs.get("slug"),
                "page_type": kwargs.get("page_type"),
                "is_published": False
            }

        def list_pages(self, **kwargs):
            return [{"id": str(uuid4()), "title": f"Page {i}", "slug": f"page-{i}"} for i in range(1, 3)]

        def count_pages(self, **kwargs):
            return 2

        def get_page(self, page_id):
            return {"id": str(uuid4()), "title": "Page 1", "slug": "page-1"}

        def get_page_by_slug(self, slug):
            return {"id": str(uuid4()), "title": "Page 1", "slug": slug}

        def publish_page(self, page_id, **kwargs):
            page = self.get_page(page_id)
            page["is_published"] = True
            page["published_at"] = datetime.utcnow()
            return page

        # Components
        def create_component(self, **kwargs):
            return {
                "id": str(uuid4()),
                "tenant_id": self.tenant_id,
                "code": kwargs.get("code"),
                "name": kwargs.get("name"),
                "category": kwargs.get("category")
            }

        def list_components(self, **kwargs):
            return [{"id": str(uuid4()), "code": f"CMP-{i}", "name": f"Component {i}"} for i in range(1, 3)]

        def count_components(self, **kwargs):
            return 2

    from app.modules.web import router_v2

    def mock_get_service(db, tenant_id, user_id):
        return MockWebService(db, tenant_id, user_id)

    monkeypatch.setattr(router_v2, "get_web_service", mock_get_service)

    return MockWebService(None, tenant_id, user_id)


# Fixtures données de test
@pytest.fixture
def sample_theme_data():
    return {
        "code": "THEME-CUSTOM",
        "name": "Theme Custom",
        "mode": "LIGHT",
        "primary_color": "#2196F3"
    }


@pytest.fixture
def sample_widget_data():
    return {
        "code": "WDG-STATS",
        "name": "Widget Stats",
        "widget_type": "CHART",
        "size": "MEDIUM",
        "config": {"chart_type": "bar"}
    }


@pytest.fixture
def sample_dashboard_data():
    return {
        "code": "DASH-CUSTOM",
        "name": "Dashboard Custom",
        "layout": {"columns": 12}
    }


@pytest.fixture
def sample_menu_item_data():
    return {
        "menu_type": "MAIN",
        "code": "MENU-CUSTOM",
        "label": "Menu Custom",
        "route": "/custom"
    }


@pytest.fixture
def sample_page_data():
    return {
        "title": "Page Custom",
        "slug": "page-custom",
        "page_type": "STATIC",
        "content": {"blocks": []}
    }


@pytest.fixture
def sample_component_data():
    return {
        "code": "CMP-CUSTOM",
        "name": "Component Custom",
        "category": "LAYOUT",
        "template": {}
    }
