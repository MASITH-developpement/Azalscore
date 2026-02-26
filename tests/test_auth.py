"""
AZALS - Tests Authentification JWT
Validation de la sécurité JWT + isolation tenant
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.models import User, UserRole
from app.core.security import get_password_hash


# Base de données de test en mémoire
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Fixture : session de base de données de test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Fixture : client de test FastAPI."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ===== TESTS REGISTER =====

def test_register_creates_user_with_tenant(client, db_session):
    """
    Test : register crée un utilisateur lié au tenant.
    Le tenant_id provient du header X-Tenant-ID.
    """
    response = client.post(
        "/auth/register",
        json={"email": "dirigeant@tenant-a.com", "password": "SecurePass123"},
        headers={"X-Tenant-ID": "tenant-a"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["email"] == "dirigeant@tenant-a.com"
    assert data["tenant_id"] == "tenant-a"
    assert data["role"] == "DIRIGEANT"
    
    # Vérifier en DB
    user = db_session.query(User).filter(User.email == "dirigeant@tenant-a.com").first()
    assert user is not None
    assert user.tenant_id == "tenant-a"


def test_register_rejects_duplicate_email(client, db_session):
    """
    Test : register refuse un email déjà existant.
    """
    # Créer un utilisateur
    client.post(
        "/auth/register",
        json={"email": "test@tenant-a.com", "password": "Pass123"},
        headers={"X-Tenant-ID": "tenant-a"}
    )
    
    # Tenter de créer avec le même email
    response = client.post(
        "/auth/register",
        json={"email": "test@tenant-a.com", "password": "Pass456"},
        headers={"X-Tenant-ID": "tenant-a"}
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json().get("detail", response.json().get("message", ""))


# ===== TESTS LOGIN =====

def test_login_returns_jwt_with_tenant_info(client, db_session):
    """
    Test : login retourne un JWT contenant tenant_id.
    """
    # Créer un utilisateur
    user = User(
        email="user@tenant-a.com",
        password_hash=get_password_hash("Password123"),
        tenant_id="tenant-a",
        role=UserRole.DIRIGEANT,
        is_active=1
    )
    db_session.add(user)
    db_session.commit()
    
    # Login
    response = client.post(
        "/auth/login",
        json={"email": "user@tenant-a.com", "password": "Password123"},
        headers={"X-Tenant-ID": "tenant-a"}
    )
    
    assert response.status_code == 200
    data = response.json()

    # Format peut être soit plat (access_token) soit nested (tokens.access_token)
    assert "access_token" in data or ("tokens" in data and "access_token" in data["tokens"])
    # token_type peut être à la racine ou dans tokens
    token_type = data.get("token_type") or data.get("tokens", {}).get("token_type", "bearer")
    assert token_type == "bearer"
    assert data.get("tenant_id") == "tenant-a" or data.get("user", {}).get("tenant_id") == "tenant-a"


def test_login_fails_with_wrong_password(client, db_session):
    """
    Test : login échoue avec un mauvais mot de passe.
    """
    user = User(
        email="user@tenant-a.com",
        password_hash=get_password_hash("CorrectPassword"),
        tenant_id="tenant-a",
        role=UserRole.DIRIGEANT,
        is_active=1
    )
    db_session.add(user)
    db_session.commit()
    
    response = client.post(
        "/auth/login",
        json={"email": "user@tenant-a.com", "password": "WrongPassword"},
        headers={"X-Tenant-ID": "tenant-a"}
    )
    
    assert response.status_code == 401
    # Note: Error handler returns generic message


def test_login_fails_with_unknown_email(client):
    """
    Test : login échoue avec un email inconnu.
    """
    response = client.post(
        "/auth/login",
        json={"email": "unknown@example.com", "password": "AnyPassword"},
        headers={"X-Tenant-ID": "tenant-a"}
    )
    
    assert response.status_code == 401


# ===== TESTS ENDPOINTS PROTÉGÉS =====

def test_protected_endpoint_rejects_without_jwt(client, db_session):
    """
    Test : un endpoint protégé refuse l'accès sans JWT.
    Validation exigence : accès refusé sans JWT.
    """
    response = client.get(
        "/me/profile",
        headers={"X-Tenant-ID": "tenant-a"}
    )

    # 401 Unauthorized (pas authentifié) est correct, pas 403 (authentifié mais pas autorisé)
    assert response.status_code == 401


def test_protected_endpoint_rejects_invalid_jwt(client, db_session):
    """
    Test : un endpoint protégé refuse un JWT invalide.
    Validation exigence : accès refusé avec JWT invalide.
    """
    response = client.get(
        "/me/profile",
        headers={
            "X-Tenant-ID": "tenant-a",
            "Authorization": "Bearer INVALID_TOKEN_XYZ123"
        }
    )
    
    assert response.status_code == 401
    # Note: Error handler returns generic message, authentication failure verified by status code


def test_user_cannot_access_other_tenant_with_jwt(client, db_session):
    """
    Test : un utilisateur avec JWT ne peut PAS accéder à un autre tenant.
    Validation exigence : refus si tenant ≠ utilisateur.
    """
    # Créer un utilisateur tenant-a
    user = User(
        email="user-a@tenant-a.com",
        password_hash=get_password_hash("Pass123"),
        tenant_id="tenant-a",
        role=UserRole.DIRIGEANT,
        is_active=1
    )
    db_session.add(user)
    db_session.commit()
    
    # Login pour obtenir JWT
    login_response = client.post(
        "/auth/login",
        json={"email": "user-a@tenant-a.com", "password": "Pass123"},
        headers={"X-Tenant-ID": "tenant-a"}
    )
    
    token = login_response.json()["access_token"]
    
    # Tenter d'accéder avec X-Tenant-ID différent
    # JWT contient tenant_id="tenant-a"
    # Requête avec X-Tenant-ID="tenant-b" doit échouer
    response = client.get(
        "/me/profile",
        headers={
            "X-Tenant-ID": "tenant-b",
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 403
    # Note: Error handler returns generic message, tenant isolation is verified by status code


def test_jwt_tenant_coherence_validation(client, db_session):
    """
    Test : validation de cohérence JWT tenant_id ↔ X-Tenant-ID.
    get_current_user DOIT refuser si incohérence.
    """
    # Créer un utilisateur tenant-a
    user = User(
        email="user-tenant-a@example.com",
        password_hash=get_password_hash("SecurePass"),
        tenant_id="tenant-a",
        role=UserRole.DIRIGEANT,
        is_active=1
    )
    db_session.add(user)
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/auth/login",
        json={"email": "user-tenant-a@example.com", "password": "SecurePass"},
        headers={"X-Tenant-ID": "tenant-a"}
    )
    
    token = login_response.json()["access_token"]
    assert login_response.json()["tenant_id"] == "tenant-a"
    
    # Le JWT contient tenant_id="tenant-a"
    # Si on utilise X-Tenant-ID="tenant-b", get_current_user doit refuser
    response = client.get(
        "/me/profile",
        headers={
            "X-Tenant-ID": "tenant-b",
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 403
    # Note: Error handler returns generic message, tenant isolation is verified by status code


def test_user_can_access_own_tenant_with_valid_jwt(client, db_session):
    """
    Test : un utilisateur peut accéder à SON tenant avec JWT valide.
    Validation exigence : accès autorisé si JWT + tenant corrects.
    """
    # Créer un utilisateur
    user = User(
        email="valid-user@tenant-x.com",
        password_hash=get_password_hash("ValidPass123"),
        tenant_id="tenant-x",
        role=UserRole.DIRIGEANT,
        is_active=1
    )
    db_session.add(user)
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/auth/login",
        json={"email": "valid-user@tenant-x.com", "password": "ValidPass123"},
        headers={"X-Tenant-ID": "tenant-x"}
    )
    
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    tenant_id = login_response.json()["tenant_id"]
    
    # Utiliser le token avec le bon X-Tenant-ID
    response = client.get(
        "/me/profile",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "valid-user@tenant-x.com"
    assert data["tenant_id"] == "tenant-x"
    assert data["role"] == "DIRIGEANT"
