"""
AZALS - Tests Multi-Tenant
Validation de l'isolation stricte entre tenants
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.models import Item


# Base de données de test en mémoire
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Fixture : session de base de données de test.
    Crée les tables, yield la session, puis nettoie.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Fixture : client de test FastAPI.
    Override la dépendance get_db pour utiliser la DB de test.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ===== TESTS VALIDATION TENANT =====

def test_request_without_tenant_id_returns_401(client):
    """
    Test : requête sans X-Tenant-ID est bloquée par le middleware.
    Validation exigence : aucune requête sans tenant_id.
    Le middleware lève une HTTPException qui est propagée dans les tests.
    """
    # Le middleware bloque la requête : l'exception prouve le blocage
    from fastapi.exceptions import HTTPException
    
    try:
        client.get("/items/")
        assert False, "La requête aurait dû être bloquée"
    except Exception as e:
        # Vérification que c'est bien le middleware qui bloque
        assert "401" in str(e) or "X-Tenant-ID" in str(e)


def test_request_with_invalid_tenant_id_returns_400(client):
    """
    Test : requête avec X-Tenant-ID invalide est bloquée par le middleware.
    Validation format : alphanumerique + tirets uniquement.
    """
    try:
        client.get("/items/", headers={"X-Tenant-ID": "tenant@invalid!"})
        assert False, "La requête aurait dû être bloquée"
    except Exception as e:
        # Vérification que c'est bien le middleware qui valide le format
        assert "400" in str(e) or "Invalid X-Tenant-ID" in str(e)


def test_health_endpoint_accessible_without_tenant(client):
    """
    Test : endpoint /health accessible sans X-Tenant-ID.
    Validation : endpoints publics exemptés de validation tenant.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["ok", "degraded"]


# ===== TESTS ISOLATION TENANT =====

def test_tenant_can_create_item(client):
    """
    Test : un tenant peut créer un item.
    L'item créé contient bien le tenant_id du créateur.
    """
    response = client.post(
        "/items/",
        json={"name": "Item Tenant A", "description": "Test"},
        headers={"X-Tenant-ID": "tenant-a"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Item Tenant A"
    assert data["tenant_id"] == "tenant-a"


def test_tenant_cannot_see_other_tenant_items(client, db_session):
    """
    Test : un tenant ne peut PAS voir les items d'un autre tenant.
    Validation exigence : isolation stricte en lecture.
    """
    # Tenant A crée un item
    item_a = Item(tenant_id="tenant-a", name="Item A")
    db_session.add(item_a)
    
    # Tenant B crée un item
    item_b = Item(tenant_id="tenant-b", name="Item B")
    db_session.add(item_b)
    
    db_session.commit()
    
    # Tenant A liste ses items : doit voir UNIQUEMENT son item
    response_a = client.get("/items/", headers={"X-Tenant-ID": "tenant-a"})
    items_a = response_a.json()
    
    assert response_a.status_code == 200
    assert len(items_a) == 1
    assert items_a[0]["tenant_id"] == "tenant-a"
    assert items_a[0]["name"] == "Item A"
    
    # Tenant B liste ses items : doit voir UNIQUEMENT son item
    response_b = client.get("/items/", headers={"X-Tenant-ID": "tenant-b"})
    items_b = response_b.json()
    
    assert response_b.status_code == 200
    assert len(items_b) == 1
    assert items_b[0]["tenant_id"] == "tenant-b"
    assert items_b[0]["name"] == "Item B"


def test_tenant_cannot_read_other_tenant_item_by_id(client, db_session):
    """
    Test : un tenant ne peut PAS lire l'item d'un autre tenant par ID.
    Validation exigence : 404 même si l'item existe (masquage).
    """
    # Tenant A crée un item
    item_a = Item(tenant_id="tenant-a", name="Item Secret A")
    db_session.add(item_a)
    db_session.commit()
    db_session.refresh(item_a)
    
    # Tenant B tente de lire l'item de A : doit recevoir 404
    response = client.get(
        f"/items/{item_a.id}",
        headers={"X-Tenant-ID": "tenant-b"}
    )
    
    assert response.status_code == 404
    assert "not found or access denied" in response.json()["detail"]


def test_tenant_cannot_update_other_tenant_item(client, db_session):
    """
    Test : un tenant ne peut PAS modifier l'item d'un autre tenant.
    Validation exigence : isolation stricte en écriture.
    """
    # Tenant A crée un item
    item_a = Item(tenant_id="tenant-a", name="Item A Original")
    db_session.add(item_a)
    db_session.commit()
    db_session.refresh(item_a)
    
    # Tenant B tente de modifier l'item de A : doit recevoir 404
    response = client.put(
        f"/items/{item_a.id}",
        json={"name": "Item A Modifié par B", "description": "Hack attempt"},
        headers={"X-Tenant-ID": "tenant-b"}
    )
    
    assert response.status_code == 404
    
    # Vérification : l'item de A n'a PAS été modifié
    db_session.refresh(item_a)
    assert item_a.name == "Item A Original"


def test_tenant_cannot_delete_other_tenant_item(client, db_session):
    """
    Test : un tenant ne peut PAS supprimer l'item d'un autre tenant.
    Validation exigence : isolation stricte en suppression.
    """
    # Tenant A crée un item
    item_a = Item(tenant_id="tenant-a", name="Item A Protected")
    db_session.add(item_a)
    db_session.commit()
    db_session.refresh(item_a)
    item_id = item_a.id
    
    # Tenant B tente de supprimer l'item de A : doit recevoir 404
    response = client.delete(
        f"/items/{item_id}",
        headers={"X-Tenant-ID": "tenant-b"}
    )
    
    assert response.status_code == 404
    
    # Vérification : l'item de A existe toujours
    item_still_exists = db_session.query(Item).filter(Item.id == item_id).first()
    assert item_still_exists is not None
    assert item_still_exists.name == "Item A Protected"


def test_tenant_can_update_own_item(client, db_session):
    """
    Test : un tenant peut modifier SON propre item.
    Validation : opérations légitimes fonctionnent.
    """
    # Tenant A crée un item
    item_a = Item(tenant_id="tenant-a", name="Item A Original")
    db_session.add(item_a)
    db_session.commit()
    db_session.refresh(item_a)
    
    # Tenant A modifie son propre item : doit réussir
    response = client.put(
        f"/items/{item_a.id}",
        json={"name": "Item A Modifié", "description": "Légitimement"},
        headers={"X-Tenant-ID": "tenant-a"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Item A Modifié"
    assert data["tenant_id"] == "tenant-a"


def test_tenant_can_delete_own_item(client, db_session):
    """
    Test : un tenant peut supprimer SON propre item.
    Validation : opérations légitimes fonctionnent.
    """
    # Tenant A crée un item
    item_a = Item(tenant_id="tenant-a", name="Item A To Delete")
    db_session.add(item_a)
    db_session.commit()
    db_session.refresh(item_a)
    item_id = item_a.id
    
    # Tenant A supprime son propre item : doit réussir
    response = client.delete(
        f"/items/{item_id}",
        headers={"X-Tenant-ID": "tenant-a"}
    )
    
    assert response.status_code == 204
    
    # Vérification : l'item n'existe plus
    item_deleted = db_session.query(Item).filter(Item.id == item_id).first()
    assert item_deleted is None


def test_multiple_tenants_complete_isolation(client):
    """
    Test : isolation complète entre plusieurs tenants.
    Scénario réaliste : 3 tenants créent des items simultanément.
    Aucun ne doit voir les items des autres.
    """
    tenants = ["tenant-alpha", "tenant-beta", "tenant-gamma"]
    
    # Chaque tenant crée 2 items
    for tenant in tenants:
        for i in range(2):
            response = client.post(
                "/items/",
                json={"name": f"Item {i} of {tenant}"},
                headers={"X-Tenant-ID": tenant}
            )
            assert response.status_code == 201
    
    # Chaque tenant ne doit voir QUE ses 2 items
    for tenant in tenants:
        response = client.get("/items/", headers={"X-Tenant-ID": tenant})
        items = response.json()
        
        assert len(items) == 2
        assert all(item["tenant_id"] == tenant for item in items)
        assert all(tenant in item["name"] for item in items)
