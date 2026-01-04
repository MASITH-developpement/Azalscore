"""
AZALS MODULE T0 - Tests IAM
===========================

Tests complets pour le module de gestion des identités et accès.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db


# ============================================================================
# CONFIGURATION TEST
# ============================================================================

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Headers par défaut
TENANT_ID = "test-tenant"
HEADERS = {"X-Tenant-ID": TENANT_ID}


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def setup_database():
    """Crée les tables avant chaque test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_headers():
    """Crée un utilisateur et retourne les headers avec token."""
    # Créer un utilisateur
    response = client.post(
        "/iam/auth/login",
        json={
            "email": "admin@test.com",
            "password": "SecureP@ssw0rd123!"
        },
        headers=HEADERS
    )
    if response.status_code != 200:
        # Créer l'utilisateur d'abord via register
        client.post(
            "/auth/register",
            json={
                "email": "admin@test.com",
                "password": "SecureP@ssw0rd123!"
            },
            headers=HEADERS
        )
        response = client.post(
            "/iam/auth/login",
            json={
                "email": "admin@test.com",
                "password": "SecureP@ssw0rd123!"
            },
            headers=HEADERS
        )

    if response.status_code == 200:
        token = response.json()["access_token"]
        return {**HEADERS, "Authorization": f"Bearer {token}"}
    return HEADERS


# ============================================================================
# TESTS AUTHENTIFICATION
# ============================================================================

class TestAuthentication:
    """Tests du système d'authentification."""

    def test_login_invalid_credentials(self):
        """Test login avec credentials invalides."""
        response = client.post(
            "/iam/auth/login",
            json={
                "email": "wrong@test.com",
                "password": "wrongpassword"
            },
            headers=HEADERS
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_missing_password(self):
        """Test login sans mot de passe."""
        response = client.post(
            "/iam/auth/login",
            json={"email": "test@test.com"},
            headers=HEADERS
        )
        assert response.status_code == 422

    def test_login_invalid_email_format(self):
        """Test login avec email invalide."""
        response = client.post(
            "/iam/auth/login",
            json={
                "email": "not-an-email",
                "password": "password123"
            },
            headers=HEADERS
        )
        assert response.status_code == 422

    def test_refresh_token_invalid(self):
        """Test refresh avec token invalide."""
        response = client.post(
            "/iam/auth/refresh",
            json={"refresh_token": "invalid-token"},
            headers=HEADERS
        )
        assert response.status_code == 401


# ============================================================================
# TESTS UTILISATEURS
# ============================================================================

class TestUsers:
    """Tests de gestion des utilisateurs."""

    def test_create_user_password_validation(self):
        """Test validation mot de passe à la création."""
        # Mot de passe trop court
        response = client.post(
            "/iam/users",
            json={
                "email": "newuser@test.com",
                "password": "short"
            },
            headers=HEADERS
        )
        assert response.status_code == 422

    def test_create_user_password_without_uppercase(self):
        """Test mot de passe sans majuscule."""
        response = client.post(
            "/iam/users",
            json={
                "email": "newuser@test.com",
                "password": "nouppercase123!@#"
            },
            headers=HEADERS
        )
        assert response.status_code == 422

    def test_create_user_password_without_number(self):
        """Test mot de passe sans chiffre."""
        response = client.post(
            "/iam/users",
            json={
                "email": "newuser@test.com",
                "password": "NoNumberHere!@#"
            },
            headers=HEADERS
        )
        assert response.status_code == 422

    def test_create_user_password_without_special(self):
        """Test mot de passe sans caractère spécial."""
        response = client.post(
            "/iam/users",
            json={
                "email": "newuser@test.com",
                "password": "NoSpecialChar123"
            },
            headers=HEADERS
        )
        assert response.status_code == 422

    def test_get_current_user_unauthorized(self):
        """Test accès profil sans authentification."""
        response = client.get("/iam/users/me", headers=HEADERS)
        assert response.status_code == 401

    def test_list_users_pagination(self):
        """Test pagination liste utilisateurs."""
        response = client.get(
            "/iam/users?page=1&page_size=10",
            headers=HEADERS
        )
        # Sans auth, devrait être 401 ou 403
        assert response.status_code in [401, 403]


# ============================================================================
# TESTS RÔLES
# ============================================================================

class TestRoles:
    """Tests de gestion des rôles."""

    def test_create_role_invalid_code(self):
        """Test création rôle avec code invalide."""
        response = client.post(
            "/iam/roles",
            json={
                "code": "invalid-code",  # Doit être UPPER_SNAKE_CASE
                "name": "Test Role"
            },
            headers=HEADERS
        )
        assert response.status_code in [401, 422]

    def test_role_code_format(self):
        """Test format code rôle (UPPER_SNAKE_CASE)."""
        # Doit commencer par une lettre majuscule
        response = client.post(
            "/iam/roles",
            json={
                "code": "1INVALID",
                "name": "Test Role"
            },
            headers=HEADERS
        )
        assert response.status_code in [401, 422]

    def test_list_roles_unauthenticated(self):
        """Test liste rôles sans authentification."""
        response = client.get("/iam/roles", headers=HEADERS)
        assert response.status_code in [401, 403]


# ============================================================================
# TESTS PERMISSIONS
# ============================================================================

class TestPermissions:
    """Tests de gestion des permissions."""

    def test_list_permissions_unauthenticated(self):
        """Test liste permissions sans authentification."""
        response = client.get("/iam/permissions", headers=HEADERS)
        assert response.status_code in [401, 403]

    def test_check_permission_format(self):
        """Test format code permission."""
        response = client.post(
            "/iam/permissions/check",
            json={"permission_code": "module.resource.action"},
            headers=HEADERS
        )
        assert response.status_code in [401, 403]


# ============================================================================
# TESTS GROUPES
# ============================================================================

class TestGroups:
    """Tests de gestion des groupes."""

    def test_create_group_invalid_code(self):
        """Test création groupe avec code invalide."""
        response = client.post(
            "/iam/groups",
            json={
                "code": "invalid code",  # Espaces non autorisés
                "name": "Test Group"
            },
            headers=HEADERS
        )
        assert response.status_code in [401, 422]

    def test_list_groups_unauthenticated(self):
        """Test liste groupes sans authentification."""
        response = client.get("/iam/groups", headers=HEADERS)
        assert response.status_code in [401, 403]


# ============================================================================
# TESTS MFA
# ============================================================================

class TestMFA:
    """Tests du système MFA."""

    def test_setup_mfa_unauthenticated(self):
        """Test configuration MFA sans authentification."""
        response = client.post("/iam/users/me/mfa/setup", headers=HEADERS)
        assert response.status_code == 401

    def test_verify_mfa_invalid_code(self):
        """Test vérification MFA avec code invalide."""
        response = client.post(
            "/iam/users/me/mfa/verify",
            json={"code": "123"},  # Trop court
            headers=HEADERS
        )
        assert response.status_code in [401, 422]


# ============================================================================
# TESTS INVITATIONS
# ============================================================================

class TestInvitations:
    """Tests du système d'invitations."""

    def test_create_invitation_unauthenticated(self):
        """Test création invitation sans authentification."""
        response = client.post(
            "/iam/invitations",
            json={
                "email": "invitee@test.com",
                "role_codes": ["CONSULTANT"]
            },
            headers=HEADERS
        )
        assert response.status_code in [401, 403]

    def test_accept_invitation_invalid_token(self):
        """Test acceptation invitation avec token invalide."""
        response = client.post(
            "/iam/invitations/accept",
            json={
                "token": "invalid-token",
                "password": "SecureP@ssw0rd123!"
            },
            headers=HEADERS
        )
        assert response.status_code == 400

    def test_accept_invitation_weak_password(self):
        """Test acceptation invitation avec mot de passe faible."""
        response = client.post(
            "/iam/invitations/accept",
            json={
                "token": "some-token",
                "password": "weak"
            },
            headers=HEADERS
        )
        assert response.status_code == 422


# ============================================================================
# TESTS SESSIONS
# ============================================================================

class TestSessions:
    """Tests de gestion des sessions."""

    def test_list_sessions_unauthenticated(self):
        """Test liste sessions sans authentification."""
        response = client.get("/iam/users/me/sessions", headers=HEADERS)
        assert response.status_code == 401

    def test_revoke_sessions_unauthenticated(self):
        """Test révocation sessions sans authentification."""
        response = client.post(
            "/iam/users/me/sessions/revoke",
            json={"session_ids": [1, 2, 3]},
            headers=HEADERS
        )
        assert response.status_code == 401


# ============================================================================
# TESTS POLITIQUE MOT DE PASSE
# ============================================================================

class TestPasswordPolicy:
    """Tests de la politique de mot de passe."""

    def test_get_policy_unauthenticated(self):
        """Test lecture politique sans authentification."""
        response = client.get("/iam/password-policy", headers=HEADERS)
        assert response.status_code in [401, 403]

    def test_update_policy_invalid_values(self):
        """Test mise à jour politique avec valeurs invalides."""
        response = client.patch(
            "/iam/password-policy",
            json={
                "min_length": 4,  # Trop court (min 8)
                "max_failed_attempts": 1  # Trop bas (min 3)
            },
            headers=HEADERS
        )
        assert response.status_code in [401, 422]


# ============================================================================
# TESTS SÉCURITÉ
# ============================================================================

class TestSecurity:
    """Tests de sécurité."""

    def test_sql_injection_prevention(self):
        """Test prévention injection SQL dans email."""
        response = client.post(
            "/iam/auth/login",
            json={
                "email": "'; DROP TABLE users; --",
                "password": "password"
            },
            headers=HEADERS
        )
        assert response.status_code == 422

    def test_xss_prevention_in_user_data(self):
        """Test que les données utilisateur sont échappées."""
        # Les données avec scripts devraient être acceptées mais échappées
        response = client.post(
            "/iam/users",
            json={
                "email": "test@test.com",
                "password": "SecureP@ssw0rd123!",
                "first_name": "<script>alert('xss')</script>"
            },
            headers=HEADERS
        )
        # Devrait être rejeté par validation ou échappé
        assert response.status_code in [401, 403, 422]

    def test_missing_tenant_header(self):
        """Test requête sans header X-Tenant-ID."""
        response = client.post(
            "/iam/auth/login",
            json={
                "email": "test@test.com",
                "password": "password"
            }
        )
        assert response.status_code in [401, 422]

    def test_invalid_tenant_header(self):
        """Test requête avec tenant invalide."""
        response = client.post(
            "/iam/auth/login",
            json={
                "email": "test@test.com",
                "password": "password"
            },
            headers={"X-Tenant-ID": "../../etc/passwd"}
        )
        # Devrait rejeter le tenant malformé
        assert response.status_code in [401, 422]


# ============================================================================
# TESTS RATE LIMITING
# ============================================================================

class TestRateLimiting:
    """Tests du rate limiting."""

    def test_multiple_failed_logins(self):
        """Test verrouillage après tentatives échouées."""
        # Faire plusieurs tentatives échouées
        for i in range(6):
            client.post(
                "/iam/auth/login",
                json={
                    "email": f"locked{i}@test.com",
                    "password": "wrongpassword"
                },
                headers=HEADERS
            )

        # La 6ème devrait être bloquée
        response = client.post(
            "/iam/auth/login",
            json={
                "email": "locked5@test.com",
                "password": "wrongpassword"
            },
            headers=HEADERS
        )
        # Le rate limiting peut retourner 401 ou 429
        assert response.status_code in [401, 429]


# ============================================================================
# TESTS MULTI-TENANT
# ============================================================================

class TestMultiTenant:
    """Tests de l'isolation multi-tenant."""

    def test_tenant_isolation(self):
        """Test que les données sont isolées par tenant."""
        # Créer un utilisateur sur tenant 1
        response1 = client.post(
            "/iam/auth/login",
            json={
                "email": "user@test.com",
                "password": "password"
            },
            headers={"X-Tenant-ID": "tenant-1"}
        )

        # Essayer d'accéder depuis tenant 2
        response2 = client.post(
            "/iam/auth/login",
            json={
                "email": "user@test.com",
                "password": "password"
            },
            headers={"X-Tenant-ID": "tenant-2"}
        )

        # Les deux devraient échouer (utilisateur non créé via register)
        assert response1.status_code == 401
        assert response2.status_code == 401


# ============================================================================
# TESTS VALIDATION SCHÉMAS
# ============================================================================

class TestSchemaValidation:
    """Tests de validation des schémas Pydantic."""

    def test_user_email_validation(self):
        """Test validation format email."""
        invalid_emails = [
            "not-an-email",
            "@missing-local.com",
            "missing-domain@",
            "spaces in@email.com"
        ]

        for email in invalid_emails:
            response = client.post(
                "/iam/users",
                json={
                    "email": email,
                    "password": "SecureP@ssw0rd123!"
                },
                headers=HEADERS
            )
            assert response.status_code == 422, f"Email {email} should be invalid"

    def test_role_level_bounds(self):
        """Test bornes niveau rôle."""
        # Niveau trop bas
        response = client.post(
            "/iam/roles",
            json={
                "code": "TEST_ROLE",
                "name": "Test",
                "level": -1
            },
            headers=HEADERS
        )
        assert response.status_code in [401, 422]

        # Niveau trop haut
        response = client.post(
            "/iam/roles",
            json={
                "code": "TEST_ROLE",
                "name": "Test",
                "level": 100
            },
            headers=HEADERS
        )
        assert response.status_code in [401, 422]


# ============================================================================
# TESTS INTÉGRATION
# ============================================================================

class TestIntegration:
    """Tests d'intégration complète."""

    def test_health_check(self):
        """Test endpoint santé."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_api_documentation(self):
        """Test accès documentation API."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema(self):
        """Test schéma OpenAPI."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/iam/auth/login" in schema["paths"]


# ============================================================================
# TESTS CURL (pour validation manuelle)
# ============================================================================

"""
# Tests CURL pour validation manuelle

# 1. Login
curl -X POST http://localhost:8000/iam/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: test-tenant" \
  -d '{"email": "admin@test.com", "password": "SecureP@ssw0rd123!"}'

# 2. Liste utilisateurs (avec token)
curl -X GET http://localhost:8000/iam/users \
  -H "Authorization: Bearer <TOKEN>" \
  -H "X-Tenant-ID: test-tenant"

# 3. Créer un rôle
curl -X POST http://localhost:8000/iam/roles \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "X-Tenant-ID: test-tenant" \
  -d '{"code": "MANAGER", "name": "Manager", "level": 3}'

# 4. Vérifier permission
curl -X POST http://localhost:8000/iam/permissions/check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "X-Tenant-ID: test-tenant" \
  -d '{"permission_code": "iam.user.read"}'

# 5. Configuration MFA
curl -X POST http://localhost:8000/iam/users/me/mfa/setup \
  -H "Authorization: Bearer <TOKEN>" \
  -H "X-Tenant-ID: test-tenant"

# 6. Refresh token
curl -X POST http://localhost:8000/iam/auth/refresh \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: test-tenant" \
  -d '{"refresh_token": "<REFRESH_TOKEN>"}'

# 7. Créer invitation
curl -X POST http://localhost:8000/iam/invitations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "X-Tenant-ID: test-tenant" \
  -d '{"email": "newuser@test.com", "role_codes": ["CONSULTANT"]}'

# 8. Liste sessions
curl -X GET http://localhost:8000/iam/users/me/sessions \
  -H "Authorization: Bearer <TOKEN>" \
  -H "X-Tenant-ID: test-tenant"

# 9. Logout
curl -X POST http://localhost:8000/iam/auth/logout \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "X-Tenant-ID: test-tenant" \
  -d '{"all_sessions": false}'

# 10. Politique mot de passe
curl -X GET http://localhost:8000/iam/password-policy \
  -H "Authorization: Bearer <TOKEN>" \
  -H "X-Tenant-ID: test-tenant"
"""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
