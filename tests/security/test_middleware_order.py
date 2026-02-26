"""
AZALS - Tests d'ordre des middleware de sécurité
=================================================

P1 SÉCURITÉ: Vérifie que les middleware sont dans le bon ordre.
L'ordre est CRITIQUE pour la sécurité:
1. CORS (premier à s'exécuter - gère OPTIONS preflight)
2. Guardian (logging)
3. TenantMiddleware (extraction X-Tenant-ID)
4. CoreAuthMiddleware (JWT auth - APRÈS tenant)
5. RBAC (contrôle d'accès)
6. ... autres middleware

IMPORTANT: Si TenantMiddleware s'exécute APRÈS CoreAuthMiddleware,
les tokens JWT pourraient être validés sans contexte tenant,
créant une faille de sécurité multi-tenant.
"""
import pytest
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.middleware import TenantMiddleware
from app.core.core_auth_middleware import CoreAuthMiddleware


class TestMiddlewareOrder:
    """Tests d'intégrité de l'ordre des middleware."""

    def test_middleware_classes_exist(self):
        """Vérifie que les classes middleware existent."""
        assert TenantMiddleware is not None
        assert CoreAuthMiddleware is not None

    def test_tenant_before_auth_in_main(self):
        """
        P1 SÉCURITÉ CRITIQUE: Vérifie que TenantMiddleware s'exécute AVANT CoreAuthMiddleware.

        Dans Starlette, les middleware ajoutés EN DERNIER s'exécutent EN PREMIER.
        Donc TenantMiddleware doit être ajouté APRÈS CoreAuthMiddleware dans le code.

        Ordre d'ajout dans main.py (inverse de l'exécution):
        - CoreAuthMiddleware ajouté (line ~621)
        - TenantMiddleware ajouté (line ~625) <- APRÈS, donc s'exécute AVANT

        Cela garantit que request.state.tenant_id est disponible pour CoreAuthMiddleware.
        """
        import re
        from pathlib import Path

        main_path = Path(__file__).parent.parent.parent / "app" / "main.py"
        assert main_path.exists(), f"main.py not found at {main_path}"

        content = main_path.read_text()

        # Trouver les lignes où les middleware sont ajoutés
        # Regex pour capturer le nom du middleware et sa position relative
        core_auth_match = re.search(
            r'app\.add_middleware\(CoreAuthMiddleware\)',
            content
        )
        tenant_match = re.search(
            r'app\.add_middleware\(TenantMiddleware\)',
            content
        )

        assert core_auth_match is not None, "CoreAuthMiddleware not found in main.py"
        assert tenant_match is not None, "TenantMiddleware not found in main.py"

        # Position dans le fichier (début du match)
        core_auth_pos = core_auth_match.start()
        tenant_pos = tenant_match.start()

        # SÉCURITÉ CRITIQUE: TenantMiddleware doit être ajouté APRÈS CoreAuthMiddleware
        # Car en Starlette, le dernier ajouté s'exécute en premier
        # Donc Tenant (ajouté après) → s'exécute avant Auth
        assert tenant_pos > core_auth_pos, (
            "VIOLATION SÉCURITÉ P1: TenantMiddleware DOIT être ajouté APRÈS "
            "CoreAuthMiddleware dans main.py pour s'exécuter AVANT. "
            f"Position CoreAuth: {core_auth_pos}, Position Tenant: {tenant_pos}"
        )

    def test_middleware_order_comment_exists(self):
        """Vérifie que le commentaire d'ordre des middleware existe dans main.py."""
        from pathlib import Path

        main_path = Path(__file__).parent.parent.parent / "app" / "main.py"
        content = main_path.read_text()

        # Vérifie la présence du commentaire explicatif
        assert "Middleware stack" in content or "middleware" in content.lower(), (
            "Le commentaire d'ordre des middleware est manquant dans main.py"
        )

        # Vérifie la mention de l'ordre inverse de Starlette
        assert "INVERSE" in content or "inverse" in content, (
            "Le commentaire sur l'ordre inverse de Starlette est manquant"
        )

    def test_rbac_after_auth(self):
        """
        Vérifie que RBACMiddleware s'exécute APRÈS CoreAuthMiddleware.

        RBAC a besoin du contexte d'authentification pour vérifier les permissions.
        """
        from pathlib import Path

        main_path = Path(__file__).parent.parent.parent / "app" / "main.py"
        content = main_path.read_text()

        # Trouver les positions
        import re

        rbac_match = re.search(r'app\.add_middleware\(RBACMiddleware\)', content)
        core_auth_match = re.search(r'app\.add_middleware\(CoreAuthMiddleware\)', content)

        assert rbac_match is not None, "RBACMiddleware not found in main.py"
        assert core_auth_match is not None, "CoreAuthMiddleware not found in main.py"

        rbac_pos = rbac_match.start()
        core_auth_pos = core_auth_match.start()

        # RBAC doit être ajouté AVANT CoreAuth pour s'exécuter APRÈS
        assert rbac_pos < core_auth_pos, (
            "VIOLATION: RBACMiddleware doit être ajouté AVANT CoreAuthMiddleware "
            "pour s'exécuter APRÈS (avoir accès au contexte d'auth)"
        )


class TestMiddlewareSecurity:
    """Tests de sécurité des middleware."""

    def test_tenant_middleware_rejects_missing_header(self):
        """TenantMiddleware doit rejeter les requêtes sans X-Tenant-ID (hors public paths)."""
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.add_middleware(TenantMiddleware)

        @app.get("/protected")
        def protected():
            return {"status": "ok"}

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/protected")

        # Doit retourner 401 sans X-Tenant-ID
        assert response.status_code == 401, (
            f"Expected 401 without X-Tenant-ID, got {response.status_code}"
        )

    def test_tenant_middleware_accepts_valid_tenant(self):
        """TenantMiddleware doit accepter les requêtes avec X-Tenant-ID valide."""
        from starlette.testclient import TestClient
        from fastapi import FastAPI, Request

        app = FastAPI()
        app.add_middleware(TenantMiddleware)

        @app.get("/protected")
        def protected(request: Request):
            return {"tenant_id": request.state.tenant_id}

        client = TestClient(app)
        response = client.get(
            "/protected",
            headers={"X-Tenant-ID": "test-tenant-123"}
        )

        assert response.status_code == 200
        assert response.json()["tenant_id"] == "test-tenant-123"

    def test_tenant_middleware_public_paths_bypass(self):
        """TenantMiddleware doit autoriser les paths publics sans X-Tenant-ID."""
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.add_middleware(TenantMiddleware)

        @app.get("/health")
        def health():
            return {"status": "healthy"}

        client = TestClient(app)
        response = client.get("/health")

        # /health est un path public, doit passer sans X-Tenant-ID
        assert response.status_code == 200

    def test_tenant_id_validation_rejects_injection(self):
        """TenantMiddleware doit rejeter les tenant_id malveillants."""
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.add_middleware(TenantMiddleware)

        @app.get("/protected")
        def protected():
            return {"status": "ok"}

        client = TestClient(app, raise_server_exceptions=False)

        # Tentatives d'injection
        malicious_ids = [
            "tenant'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "tenant\x00null",
        ]

        for malicious_id in malicious_ids:
            response = client.get(
                "/protected",
                headers={"X-Tenant-ID": malicious_id}
            )
            assert response.status_code == 400, (
                f"Should reject malicious tenant_id: {malicious_id}"
            )


class TestDeviceBinding:
    """Tests pour le device binding des refresh tokens."""

    def test_compute_device_fingerprint_consistency(self):
        """Le fingerprint doit être consistant pour les mêmes entrées."""
        from app.core.security import compute_device_fingerprint

        ip = "192.168.1.1"
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"

        fp1 = compute_device_fingerprint(ip, ua)
        fp2 = compute_device_fingerprint(ip, ua)

        assert fp1 == fp2, "Fingerprint should be consistent"
        assert len(fp1) == 16, "Fingerprint should be 16 chars"

    def test_compute_device_fingerprint_varies_with_ip(self):
        """Le fingerprint doit varier si l'IP change."""
        from app.core.security import compute_device_fingerprint

        ua = "Mozilla/5.0"

        fp1 = compute_device_fingerprint("192.168.1.1", ua)
        fp2 = compute_device_fingerprint("10.0.0.1", ua)

        assert fp1 != fp2, "Fingerprint should vary with different IP"

    def test_compute_device_fingerprint_varies_with_ua(self):
        """Le fingerprint doit varier si le User-Agent change."""
        from app.core.security import compute_device_fingerprint

        ip = "192.168.1.1"

        fp1 = compute_device_fingerprint(ip, "Chrome/120")
        fp2 = compute_device_fingerprint(ip, "Firefox/121")

        assert fp1 != fp2, "Fingerprint should vary with different User-Agent"

    def test_verify_device_fingerprint_match(self):
        """Doit accepter quand le fingerprint correspond."""
        from app.core.security import verify_device_fingerprint

        valid, reason = verify_device_fingerprint("abcd1234abcd1234", "abcd1234abcd1234")
        assert valid is True
        assert "vérifié" in reason.lower() or "verified" in reason.lower()

    def test_verify_device_fingerprint_mismatch(self):
        """Doit rejeter quand le fingerprint ne correspond pas."""
        from app.core.security import verify_device_fingerprint

        valid, reason = verify_device_fingerprint("abcd1234abcd1234", "different12345678")
        assert valid is False
        assert "mismatch" in reason.lower() or "theft" in reason.lower()

    def test_verify_device_fingerprint_legacy_token(self):
        """Doit accepter les tokens legacy sans fingerprint (mode non-strict)."""
        from app.core.security import verify_device_fingerprint

        valid, reason = verify_device_fingerprint(None, "abcd1234abcd1234", strict=False)
        assert valid is True
        assert "legacy" in reason.lower()

    def test_verify_device_fingerprint_strict_rejects_legacy(self):
        """Doit rejeter les tokens legacy en mode strict."""
        from app.core.security import verify_device_fingerprint

        valid, reason = verify_device_fingerprint(None, "abcd1234abcd1234", strict=True)
        assert valid is False


class TestPasswordValidation:
    """Tests pour la validation des mots de passe backend."""

    def test_password_validator_rejects_weak(self):
        """Doit rejeter les mots de passe faibles."""
        from app.core.password_validator import validate_password

        weak_passwords = [
            "short",           # Trop court
            "nouppercase123!", # Pas de majuscule
            "NOLOWERCASE123!", # Pas de minuscule
            "NoDigitsHere!",   # Pas de chiffre
            "NoSpecial123",    # Pas de caractère spécial
            "password123!A",   # Pattern faible
            "qwerty123!A",     # Séquence clavier
        ]

        for pwd in weak_passwords:
            result = validate_password(pwd)
            assert not result.is_valid, f"Should reject weak password: {pwd}"

    def test_password_validator_accepts_strong(self):
        """Doit accepter les mots de passe forts."""
        from app.core.password_validator import validate_password

        strong_passwords = [
            "SecureP@ss2024!",
            "MyStr0ng#Pass!",
            "C0mpl3x&Valid!",
        ]

        for pwd in strong_passwords:
            result = validate_password(pwd)
            assert result.is_valid, f"Should accept strong password: {pwd}, errors: {result.errors}"

    def test_password_validator_or_raise(self):
        """validate_password_or_raise doit lever ValueError si invalide."""
        from app.core.password_validator import validate_password_or_raise
        import pytest

        with pytest.raises(ValueError):
            validate_password_or_raise("weak")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
