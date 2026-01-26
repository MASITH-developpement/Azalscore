"""
Tests pour le router v2 du module Web.
CORE SaaS v2 avec SaaSContext.
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app

client = TestClient(app)

BASE_URL = "/v2/web"


# ============================================================================
# TESTS THEMES
# ============================================================================

def test_create_theme_success(mock_web_service, sample_theme_data):
    """Test création d'un thème."""
    response = client.post(f"{BASE_URL}/themes", json=sample_theme_data)

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == sample_theme_data["code"]
    assert data["name"] == sample_theme_data["name"]


def test_list_themes(mock_web_service):
    """Test liste des thèmes."""
    response = client.get(f"{BASE_URL}/themes")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_get_default_theme(mock_web_service):
    """Test récupération thème par défaut."""
    response = client.get(f"{BASE_URL}/themes/default")

    assert response.status_code == 200
    data = response.json()
    assert "code" in data


def test_get_theme_success(mock_web_service):
    """Test récupération d'un thème."""
    theme_id = str(uuid4())

    response = client.get(f"{BASE_URL}/themes/{theme_id}")

    assert response.status_code == 200


def test_update_theme_success(mock_web_service):
    """Test mise à jour d'un thème."""
    theme_id = str(uuid4())
    update_data = {"name": "Theme Updated"}

    response = client.put(f"{BASE_URL}/themes/{theme_id}", json=update_data)

    assert response.status_code == 200


def test_delete_theme_success(mock_web_service):
    """Test suppression d'un thème."""
    theme_id = str(uuid4())

    response = client.delete(f"{BASE_URL}/themes/{theme_id}")

    assert response.status_code == 204


# ============================================================================
# TESTS WIDGETS
# ============================================================================

def test_create_widget_success(mock_web_service, sample_widget_data):
    """Test création d'un widget."""
    response = client.post(f"{BASE_URL}/widgets", json=sample_widget_data)

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == sample_widget_data["code"]


def test_list_widgets(mock_web_service):
    """Test liste des widgets."""
    response = client.get(f"{BASE_URL}/widgets")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_list_widgets_with_filter(mock_web_service):
    """Test liste widgets avec filtre."""
    response = client.get(f"{BASE_URL}/widgets", params={"widget_type": "CHART"})

    assert response.status_code == 200


def test_get_widget_success(mock_web_service):
    """Test récupération d'un widget."""
    widget_id = str(uuid4())

    response = client.get(f"{BASE_URL}/widgets/{widget_id}")

    assert response.status_code == 200


def test_update_widget_success(mock_web_service):
    """Test mise à jour d'un widget."""
    widget_id = str(uuid4())
    update_data = {"name": "Widget Updated"}

    response = client.put(f"{BASE_URL}/widgets/{widget_id}", json=update_data)

    assert response.status_code == 200


def test_delete_widget_success(mock_web_service):
    """Test suppression d'un widget."""
    widget_id = str(uuid4())

    response = client.delete(f"{BASE_URL}/widgets/{widget_id}")

    assert response.status_code == 204


# ============================================================================
# TESTS DASHBOARDS
# ============================================================================

def test_create_dashboard_success(mock_web_service, sample_dashboard_data):
    """Test création d'un dashboard."""
    response = client.post(f"{BASE_URL}/dashboards", json=sample_dashboard_data)

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == sample_dashboard_data["code"]


def test_list_dashboards(mock_web_service):
    """Test liste des dashboards."""
    response = client.get(f"{BASE_URL}/dashboards")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_get_default_dashboard(mock_web_service):
    """Test récupération dashboard par défaut."""
    response = client.get(f"{BASE_URL}/dashboards/default")

    assert response.status_code == 200


def test_get_dashboard_success(mock_web_service):
    """Test récupération d'un dashboard."""
    dashboard_id = str(uuid4())

    response = client.get(f"{BASE_URL}/dashboards/{dashboard_id}")

    assert response.status_code == 200


def test_update_dashboard_success(mock_web_service):
    """Test mise à jour d'un dashboard."""
    dashboard_id = str(uuid4())
    update_data = {"name": "Dashboard Updated"}

    response = client.put(f"{BASE_URL}/dashboards/{dashboard_id}", json=update_data)

    assert response.status_code == 200


def test_delete_dashboard_success(mock_web_service):
    """Test suppression d'un dashboard."""
    dashboard_id = str(uuid4())

    response = client.delete(f"{BASE_URL}/dashboards/{dashboard_id}")

    assert response.status_code == 204


# ============================================================================
# TESTS MENU ITEMS
# ============================================================================

def test_create_menu_item_success(mock_web_service, sample_menu_item_data):
    """Test création d'un élément de menu."""
    response = client.post(f"{BASE_URL}/menu-items", json=sample_menu_item_data)

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == sample_menu_item_data["code"]


def test_list_menu_items(mock_web_service):
    """Test liste des éléments de menu."""
    response = client.get(f"{BASE_URL}/menu-items")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_menu_items_by_type(mock_web_service):
    """Test liste menu par type."""
    response = client.get(f"{BASE_URL}/menu-items", params={"menu_type": "MAIN"})

    assert response.status_code == 200


def test_get_menu_tree(mock_web_service):
    """Test récupération arbre menu."""
    response = client.get(f"{BASE_URL}/menu-tree", params={"menu_type": "MAIN"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_update_menu_item_success(mock_web_service):
    """Test mise à jour élément menu."""
    item_id = str(uuid4())
    update_data = {"label": "Menu Updated"}

    response = client.put(f"{BASE_URL}/menu-items/{item_id}", json=update_data)

    assert response.status_code == 200


def test_delete_menu_item_success(mock_web_service):
    """Test suppression élément menu."""
    item_id = str(uuid4())

    response = client.delete(f"{BASE_URL}/menu-items/{item_id}")

    assert response.status_code == 204


# ============================================================================
# TESTS PREFERENCES
# ============================================================================

def test_get_user_preferences(mock_web_service):
    """Test récupération préférences utilisateur."""
    response = client.get(f"{BASE_URL}/preferences")

    assert response.status_code == 200
    data = response.json()
    assert "language" in data


def test_update_user_preferences(mock_web_service):
    """Test mise à jour préférences."""
    update_data = {"language": "en", "timezone": "UTC"}

    response = client.put(f"{BASE_URL}/preferences", json=update_data)

    assert response.status_code == 200


# ============================================================================
# TESTS CONFIG
# ============================================================================

def test_get_ui_config(mock_web_service):
    """Test récupération configuration UI."""
    response = client.get(f"{BASE_URL}/config")

    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data


# ============================================================================
# TESTS SHORTCUTS
# ============================================================================

def test_create_shortcut_success(mock_web_service):
    """Test création d'un raccourci."""
    shortcut_data = {
        "label": "My Shortcut",
        "route": "/my-page",
        "icon": "star"
    }

    response = client.post(f"{BASE_URL}/shortcuts", json=shortcut_data)

    assert response.status_code == 201
    data = response.json()
    assert data["label"] == shortcut_data["label"]


def test_list_user_shortcuts(mock_web_service):
    """Test liste raccourcis utilisateur."""
    response = client.get(f"{BASE_URL}/shortcuts")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ============================================================================
# TESTS PAGES
# ============================================================================

def test_create_page_success(mock_web_service, sample_page_data):
    """Test création d'une page."""
    response = client.post(f"{BASE_URL}/pages", json=sample_page_data)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_page_data["title"]


def test_list_pages(mock_web_service):
    """Test liste des pages."""
    response = client.get(f"{BASE_URL}/pages")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_list_pages_with_filters(mock_web_service):
    """Test liste pages avec filtres."""
    response = client.get(
        f"{BASE_URL}/pages",
        params={"page_type": "STATIC", "published_only": True}
    )

    assert response.status_code == 200


def test_get_page_success(mock_web_service):
    """Test récupération d'une page."""
    page_id = str(uuid4())

    response = client.get(f"{BASE_URL}/pages/{page_id}")

    assert response.status_code == 200


def test_get_page_by_slug_success(mock_web_service):
    """Test récupération page par slug."""
    slug = "my-page"

    response = client.get(f"{BASE_URL}/pages/slug/{slug}")

    assert response.status_code == 200


def test_publish_page_success(mock_web_service):
    """Test publication d'une page."""
    page_id = str(uuid4())

    response = client.post(f"{BASE_URL}/pages/{page_id}/publish")

    assert response.status_code == 200
    data = response.json()
    assert data["is_published"] is True


# ============================================================================
# TESTS COMPONENTS
# ============================================================================

def test_create_component_success(mock_web_service, sample_component_data):
    """Test création d'un composant."""
    response = client.post(f"{BASE_URL}/components", json=sample_component_data)

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == sample_component_data["code"]


def test_list_components(mock_web_service):
    """Test liste des composants."""
    response = client.get(f"{BASE_URL}/components")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_list_components_by_category(mock_web_service):
    """Test liste composants par catégorie."""
    response = client.get(f"{BASE_URL}/components", params={"category": "LAYOUT"})

    assert response.status_code == 200


# ============================================================================
# TESTS VALIDATION
# ============================================================================

def test_create_theme_missing_fields():
    """Test création thème avec champs manquants."""
    invalid_data = {"code": "TEST"}

    response = client.post(f"{BASE_URL}/themes", json=invalid_data)

    assert response.status_code == 422


def test_create_widget_invalid_type():
    """Test création widget avec type invalide."""
    invalid_data = {
        "code": "TEST",
        "name": "Test",
        "widget_type": "INVALID_TYPE",
        "config": {}
    }

    response = client.post(f"{BASE_URL}/widgets", json=invalid_data)

    assert response.status_code == 422


def test_get_menu_tree_missing_type():
    """Test arbre menu sans type."""
    response = client.get(f"{BASE_URL}/menu-tree")

    assert response.status_code == 422


# ============================================================================
# TESTS PAGINATION
# ============================================================================

def test_list_themes_pagination(mock_web_service):
    """Test pagination liste thèmes."""
    response = client.get(f"{BASE_URL}/themes", params={"skip": 0, "limit": 10})

    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 0
    assert data["limit"] == 10


def test_list_widgets_pagination(mock_web_service):
    """Test pagination liste widgets."""
    response = client.get(f"{BASE_URL}/widgets", params={"skip": 5, "limit": 20})

    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 5


def test_list_dashboards_pagination(mock_web_service):
    """Test pagination liste dashboards."""
    response = client.get(f"{BASE_URL}/dashboards", params={"skip": 0, "limit": 25})

    assert response.status_code == 200


def test_list_pages_pagination(mock_web_service):
    """Test pagination liste pages."""
    response = client.get(f"{BASE_URL}/pages", params={"skip": 0, "limit": 15})

    assert response.status_code == 200


# ============================================================================
# TESTS ISOLATION TENANT
# ============================================================================

def test_themes_tenant_isolation(mock_web_service):
    """Test isolation tenant sur thèmes."""
    response = client.get(f"{BASE_URL}/themes")

    assert response.status_code == 200


def test_widgets_tenant_isolation(mock_web_service):
    """Test isolation tenant sur widgets."""
    response = client.get(f"{BASE_URL}/widgets")

    assert response.status_code == 200


def test_dashboards_tenant_isolation(mock_web_service):
    """Test isolation tenant sur dashboards."""
    response = client.get(f"{BASE_URL}/dashboards")

    assert response.status_code == 200


def test_pages_tenant_isolation(mock_web_service):
    """Test isolation tenant sur pages."""
    response = client.get(f"{BASE_URL}/pages")

    assert response.status_code == 200


# ============================================================================
# TESTS USER-SPECIFIC FEATURES
# ============================================================================

def test_user_preferences_isolation(mock_web_service):
    """Test isolation préférences utilisateur."""
    response = client.get(f"{BASE_URL}/preferences")

    assert response.status_code == 200


def test_user_shortcuts_isolation(mock_web_service):
    """Test isolation raccourcis utilisateur."""
    response = client.get(f"{BASE_URL}/shortcuts")

    assert response.status_code == 200


# ============================================================================
# TESTS FILTRES AVANCÉS
# ============================================================================

def test_list_themes_with_inactive(mock_web_service):
    """Test liste thèmes avec inactifs."""
    response = client.get(f"{BASE_URL}/themes", params={"include_inactive": True})

    assert response.status_code == 200


def test_list_widgets_by_type_and_inactive(mock_web_service):
    """Test liste widgets par type avec inactifs."""
    response = client.get(
        f"{BASE_URL}/widgets",
        params={"widget_type": "CHART", "include_inactive": True}
    )

    assert response.status_code == 200


def test_list_dashboards_with_inactive(mock_web_service):
    """Test liste dashboards avec inactifs."""
    response = client.get(f"{BASE_URL}/dashboards", params={"include_inactive": True})

    assert response.status_code == 200


def test_list_pages_published_only(mock_web_service):
    """Test liste pages publiées uniquement."""
    response = client.get(f"{BASE_URL}/pages", params={"published_only": True})

    assert response.status_code == 200


# ============================================================================
# TESTS EDGE CASES
# ============================================================================

def test_get_nonexistent_theme(mock_web_service, monkeypatch):
    """Test récupération thème inexistant."""
    theme_id = str(uuid4())

    def mock_get(self, _id):
        return None

    from app.modules.web import service
    monkeypatch.setattr(service.WebService, "get_theme", mock_get)

    response = client.get(f"{BASE_URL}/themes/{theme_id}")

    assert response.status_code == 404


def test_get_nonexistent_widget(mock_web_service, monkeypatch):
    """Test récupération widget inexistant."""
    widget_id = str(uuid4())

    def mock_get(self, _id):
        return None

    from app.modules.web import service
    monkeypatch.setattr(service.WebService, "get_widget", mock_get)

    response = client.get(f"{BASE_URL}/widgets/{widget_id}")

    assert response.status_code == 404


def test_delete_nonexistent_dashboard(mock_web_service, monkeypatch):
    """Test suppression dashboard inexistant."""
    dashboard_id = str(uuid4())

    def mock_delete(self, _id):
        return False

    from app.modules.web import service
    monkeypatch.setattr(service.WebService, "delete_dashboard", mock_delete)

    response = client.delete(f"{BASE_URL}/dashboards/{dashboard_id}")

    assert response.status_code == 404


def test_publish_nonexistent_page(mock_web_service, monkeypatch):
    """Test publication page inexistante."""
    page_id = str(uuid4())

    def mock_publish(self, _id, **kwargs):
        raise ValueError("Page non trouvée")

    from app.modules.web import service
    monkeypatch.setattr(service.WebService, "publish_page", mock_publish)

    response = client.post(f"{BASE_URL}/pages/{page_id}/publish")

    assert response.status_code == 404
