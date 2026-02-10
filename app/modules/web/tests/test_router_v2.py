"""
Tests pour le router v2 du module Web.
CORE SaaS v2 avec SaaSContext.
"""

import pytest
from uuid import uuid4



BASE_URL = "/v2/web"


# ============================================================================
# TESTS THEMES
# ============================================================================

def test_create_theme_success(test_client, mock_web_service, sample_theme_data):
    """Test création d'un thème."""
    response = test_client.post(f"{BASE_URL}/themes", json=sample_theme_data)

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == sample_theme_data["code"]
    assert data["name"] == sample_theme_data["name"]


def test_list_themes(test_client):
    """Test liste des thèmes."""
    response = test_client.get(f"{BASE_URL}/themes")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_get_default_theme(test_client):
    """Test récupération thème par défaut."""
    response = test_client.get(f"{BASE_URL}/themes/default")

    assert response.status_code == 200
    data = response.json()
    assert "code" in data


def test_get_theme_success(test_client):
    """Test récupération d'un thème."""
    theme_id = str(uuid4())

    response = test_client.get(f"{BASE_URL}/themes/{theme_id}")

    assert response.status_code == 200


def test_update_theme_success(test_client):
    """Test mise à jour d'un thème."""
    theme_id = str(uuid4())
    update_data = {"name": "Theme Updated"}

    response = test_client.put(f"{BASE_URL}/themes/{theme_id}", json=update_data)

    assert response.status_code == 200


def test_delete_theme_success(test_client):
    """Test suppression d'un thème."""
    theme_id = str(uuid4())

    response = test_client.delete(f"{BASE_URL}/themes/{theme_id}")

    assert response.status_code == 204


# ============================================================================
# TESTS WIDGETS
# ============================================================================

def test_create_widget_success(test_client, mock_web_service, sample_widget_data):
    """Test création d'un widget."""
    response = test_client.post(f"{BASE_URL}/widgets", json=sample_widget_data)

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == sample_widget_data["code"]


def test_list_widgets(test_client):
    """Test liste des widgets."""
    response = test_client.get(f"{BASE_URL}/widgets")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_list_widgets_with_filter(test_client):
    """Test liste widgets avec filtre."""
    response = test_client.get(f"{BASE_URL}/widgets", params={"widget_type": "CHART"})

    assert response.status_code == 200


def test_get_widget_success(test_client):
    """Test récupération d'un widget."""
    widget_id = str(uuid4())

    response = test_client.get(f"{BASE_URL}/widgets/{widget_id}")

    assert response.status_code == 200


def test_update_widget_success(test_client):
    """Test mise à jour d'un widget."""
    widget_id = str(uuid4())
    update_data = {"name": "Widget Updated"}

    response = test_client.put(f"{BASE_URL}/widgets/{widget_id}", json=update_data)

    assert response.status_code == 200


def test_delete_widget_success(test_client):
    """Test suppression d'un widget."""
    widget_id = str(uuid4())

    response = test_client.delete(f"{BASE_URL}/widgets/{widget_id}")

    assert response.status_code == 204


# ============================================================================
# TESTS DASHBOARDS
# ============================================================================

def test_create_dashboard_success(test_client, mock_web_service, sample_dashboard_data):
    """Test création d'un dashboard."""
    response = test_client.post(f"{BASE_URL}/dashboards", json=sample_dashboard_data)

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == sample_dashboard_data["code"]


def test_list_dashboards(test_client):
    """Test liste des dashboards."""
    response = test_client.get(f"{BASE_URL}/dashboards")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_get_default_dashboard(test_client):
    """Test récupération dashboard par défaut."""
    response = test_client.get(f"{BASE_URL}/dashboards/default")

    assert response.status_code == 200


def test_get_dashboard_success(test_client):
    """Test récupération d'un dashboard."""
    dashboard_id = str(uuid4())

    response = test_client.get(f"{BASE_URL}/dashboards/{dashboard_id}")

    assert response.status_code == 200


def test_update_dashboard_success(test_client):
    """Test mise à jour d'un dashboard."""
    dashboard_id = str(uuid4())
    update_data = {"name": "Dashboard Updated"}

    response = test_client.put(f"{BASE_URL}/dashboards/{dashboard_id}", json=update_data)

    assert response.status_code == 200


def test_delete_dashboard_success(test_client):
    """Test suppression d'un dashboard."""
    dashboard_id = str(uuid4())

    response = test_client.delete(f"{BASE_URL}/dashboards/{dashboard_id}")

    assert response.status_code == 204


# ============================================================================
# TESTS MENU ITEMS
# ============================================================================

def test_create_menu_item_success(test_client, mock_web_service, sample_menu_item_data):
    """Test création d'un élément de menu."""
    response = test_client.post(f"{BASE_URL}/menu-items", json=sample_menu_item_data)

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == sample_menu_item_data["code"]


def test_list_menu_items(test_client):
    """Test liste des éléments de menu."""
    response = test_client.get(f"{BASE_URL}/menu-items")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_menu_items_by_type(test_client):
    """Test liste menu par type."""
    response = test_client.get(f"{BASE_URL}/menu-items", params={"menu_type": "MAIN"})

    assert response.status_code == 200


def test_get_menu_tree(test_client):
    """Test récupération arbre menu."""
    response = test_client.get(f"{BASE_URL}/menu-tree", params={"menu_type": "MAIN"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_update_menu_item_success(test_client):
    """Test mise à jour élément menu."""
    item_id = str(uuid4())
    update_data = {"label": "Menu Updated"}

    response = test_client.put(f"{BASE_URL}/menu-items/{item_id}", json=update_data)

    assert response.status_code == 200


def test_delete_menu_item_success(test_client):
    """Test suppression élément menu."""
    item_id = str(uuid4())

    response = test_client.delete(f"{BASE_URL}/menu-items/{item_id}")

    assert response.status_code == 204


# ============================================================================
# TESTS PREFERENCES
# ============================================================================

def test_get_user_preferences(test_client):
    """Test récupération préférences utilisateur."""
    response = test_client.get(f"{BASE_URL}/preferences")

    assert response.status_code == 200
    data = response.json()
    assert "language" in data


def test_update_user_preferences(test_client):
    """Test mise à jour préférences."""
    update_data = {"language": "en", "timezone": "UTC"}

    response = test_client.put(f"{BASE_URL}/preferences", json=update_data)

    assert response.status_code == 200


# ============================================================================
# TESTS CONFIG
# ============================================================================

def test_get_ui_config(test_client):
    """Test récupération configuration UI."""
    response = test_client.get(f"{BASE_URL}/config")

    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data


# ============================================================================
# TESTS SHORTCUTS
# ============================================================================

def test_create_shortcut_success(test_client):
    """Test création d'un raccourci."""
    shortcut_data = {
        "label": "My Shortcut",
        "route": "/my-page",
        "icon": "star"
    }

    response = test_client.post(f"{BASE_URL}/shortcuts", json=shortcut_data)

    assert response.status_code == 201
    data = response.json()
    assert data["label"] == shortcut_data["label"]


def test_list_user_shortcuts(test_client):
    """Test liste raccourcis utilisateur."""
    response = test_client.get(f"{BASE_URL}/shortcuts")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ============================================================================
# TESTS PAGES
# ============================================================================

def test_create_page_success(test_client, mock_web_service, sample_page_data):
    """Test création d'une page."""
    response = test_client.post(f"{BASE_URL}/pages", json=sample_page_data)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_page_data["title"]


def test_list_pages(test_client):
    """Test liste des pages."""
    response = test_client.get(f"{BASE_URL}/pages")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_list_pages_with_filters(test_client):
    """Test liste pages avec filtres."""
    response = test_client.get(
        f"{BASE_URL}/pages",
        params={"page_type": "STATIC", "published_only": True}
    )

    assert response.status_code == 200


def test_get_page_success(test_client):
    """Test récupération d'une page."""
    page_id = str(uuid4())

    response = test_client.get(f"{BASE_URL}/pages/{page_id}")

    assert response.status_code == 200


def test_get_page_by_slug_success(test_client):
    """Test récupération page par slug."""
    slug = "my-page"

    response = test_client.get(f"{BASE_URL}/pages/slug/{slug}")

    assert response.status_code == 200


def test_publish_page_success(test_client):
    """Test publication d'une page."""
    page_id = str(uuid4())

    response = test_client.post(f"{BASE_URL}/pages/{page_id}/publish")

    assert response.status_code == 200
    data = response.json()
    assert data["is_published"] is True


# ============================================================================
# TESTS COMPONENTS
# ============================================================================

def test_create_component_success(test_client, mock_web_service, sample_component_data):
    """Test création d'un composant."""
    response = test_client.post(f"{BASE_URL}/components", json=sample_component_data)

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == sample_component_data["code"]


def test_list_components(test_client):
    """Test liste des composants."""
    response = test_client.get(f"{BASE_URL}/components")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_list_components_by_category(test_client):
    """Test liste composants par catégorie."""
    response = test_client.get(f"{BASE_URL}/components", params={"category": "LAYOUT"})

    assert response.status_code == 200


# ============================================================================
# TESTS VALIDATION
# ============================================================================

def test_create_theme_missing_fields(test_client):
    """Test création thème avec champs manquants."""
    invalid_data = {"code": "TEST"}

    response = test_client.post(f"{BASE_URL}/themes", json=invalid_data)

    assert response.status_code == 422


def test_create_widget_invalid_type(test_client):
    """Test création widget avec type invalide."""
    invalid_data = {
        "code": "TEST",
        "name": "Test",
        "widget_type": "INVALID_TYPE",
        "config": {}
    }

    response = test_client.post(f"{BASE_URL}/widgets", json=invalid_data)

    assert response.status_code == 422


def test_get_menu_tree_missing_type(test_client):
    """Test arbre menu sans type."""
    response = test_client.get(f"{BASE_URL}/menu-tree")

    assert response.status_code == 422


# ============================================================================
# TESTS PAGINATION
# ============================================================================

def test_list_themes_pagination(test_client):
    """Test pagination liste thèmes."""
    response = test_client.get(f"{BASE_URL}/themes", params={"skip": 0, "limit": 10})

    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 0
    assert data["limit"] == 10


def test_list_widgets_pagination(test_client):
    """Test pagination liste widgets."""
    response = test_client.get(f"{BASE_URL}/widgets", params={"skip": 5, "limit": 20})

    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 5


def test_list_dashboards_pagination(test_client):
    """Test pagination liste dashboards."""
    response = test_client.get(f"{BASE_URL}/dashboards", params={"skip": 0, "limit": 25})

    assert response.status_code == 200


def test_list_pages_pagination(test_client):
    """Test pagination liste pages."""
    response = test_client.get(f"{BASE_URL}/pages", params={"skip": 0, "limit": 15})

    assert response.status_code == 200


# ============================================================================
# TESTS ISOLATION TENANT
# ============================================================================

def test_themes_tenant_isolation(test_client):
    """Test isolation tenant sur thèmes."""
    response = test_client.get(f"{BASE_URL}/themes")

    assert response.status_code == 200


def test_widgets_tenant_isolation(test_client):
    """Test isolation tenant sur widgets."""
    response = test_client.get(f"{BASE_URL}/widgets")

    assert response.status_code == 200


def test_dashboards_tenant_isolation(test_client):
    """Test isolation tenant sur dashboards."""
    response = test_client.get(f"{BASE_URL}/dashboards")

    assert response.status_code == 200


def test_pages_tenant_isolation(test_client):
    """Test isolation tenant sur pages."""
    response = test_client.get(f"{BASE_URL}/pages")

    assert response.status_code == 200


# ============================================================================
# TESTS USER-SPECIFIC FEATURES
# ============================================================================

def test_user_preferences_isolation(test_client):
    """Test isolation préférences utilisateur."""
    response = test_client.get(f"{BASE_URL}/preferences")

    assert response.status_code == 200


def test_user_shortcuts_isolation(test_client):
    """Test isolation raccourcis utilisateur."""
    response = test_client.get(f"{BASE_URL}/shortcuts")

    assert response.status_code == 200


# ============================================================================
# TESTS FILTRES AVANCÉS
# ============================================================================

def test_list_themes_with_inactive(test_client):
    """Test liste thèmes avec inactifs."""
    response = test_client.get(f"{BASE_URL}/themes", params={"include_inactive": True})

    assert response.status_code == 200


def test_list_widgets_by_type_and_inactive(test_client):
    """Test liste widgets par type avec inactifs."""
    response = test_client.get(
        f"{BASE_URL}/widgets",
        params={"widget_type": "CHART", "include_inactive": True}
    )

    assert response.status_code == 200


def test_list_dashboards_with_inactive(test_client):
    """Test liste dashboards avec inactifs."""
    response = test_client.get(f"{BASE_URL}/dashboards", params={"include_inactive": True})

    assert response.status_code == 200


def test_list_pages_published_only(test_client):
    """Test liste pages publiées uniquement."""
    response = test_client.get(f"{BASE_URL}/pages", params={"published_only": True})

    assert response.status_code == 200


# ============================================================================
# TESTS EDGE CASES
# ============================================================================

def test_get_nonexistent_theme(test_client, mock_web_service, monkeypatch):
    """Test récupération thème inexistant."""
    theme_id = str(uuid4())

    def mock_get(self, _id):
        return None

    from app.modules.web import service
    monkeypatch.setattr(service.WebService, "get_theme", mock_get)

    response = test_client.get(f"{BASE_URL}/themes/{theme_id}")

    assert response.status_code == 404


def test_get_nonexistent_widget(test_client, mock_web_service, monkeypatch):
    """Test récupération widget inexistant."""
    widget_id = str(uuid4())

    def mock_get(self, _id):
        return None

    from app.modules.web import service
    monkeypatch.setattr(service.WebService, "get_widget", mock_get)

    response = test_client.get(f"{BASE_URL}/widgets/{widget_id}")

    assert response.status_code == 404


def test_delete_nonexistent_dashboard(test_client, mock_web_service, monkeypatch):
    """Test suppression dashboard inexistant."""
    dashboard_id = str(uuid4())

    def mock_delete(self, _id):
        return False

    from app.modules.web import service
    monkeypatch.setattr(service.WebService, "delete_dashboard", mock_delete)

    response = test_client.delete(f"{BASE_URL}/dashboards/{dashboard_id}")

    assert response.status_code == 404


def test_publish_nonexistent_page(test_client, mock_web_service, monkeypatch):
    """Test publication page inexistante."""
    page_id = str(uuid4())

    def mock_publish(self, _id, **kwargs):
        raise ValueError("Page non trouvée")

    from app.modules.web import service
    monkeypatch.setattr(service.WebService, "publish_page", mock_publish)

    response = test_client.post(f"{BASE_URL}/pages/{page_id}/publish")

    assert response.status_code == 404
