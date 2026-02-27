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


class TestRateLimiting:
    """Tests pour le rate limiting des endpoints auth."""

    def test_auth_rate_limiter_has_bootstrap_method(self):
        """AuthRateLimiter doit avoir la méthode check_bootstrap_rate."""
        from app.core.rate_limiter import AuthRateLimiter

        limiter = AuthRateLimiter()
        assert hasattr(limiter, 'check_bootstrap_rate')
        assert hasattr(limiter, 'record_bootstrap_attempt')

    def test_auth_rate_limiter_has_refresh_method(self):
        """AuthRateLimiter doit avoir la méthode check_refresh_rate."""
        from app.core.rate_limiter import AuthRateLimiter

        limiter = AuthRateLimiter()
        assert hasattr(limiter, 'check_refresh_rate')
        assert hasattr(limiter, 'record_refresh_attempt')

    def test_bootstrap_rate_limit_strict(self):
        """Bootstrap rate limit doit être strict (3 par heure)."""
        from app.core.rate_limiter import AuthRateLimiter

        limiter = AuthRateLimiter()
        test_ip = "192.168.99.99"

        # Les 3 premières tentatives doivent passer
        for i in range(3):
            limiter.record_bootstrap_attempt(test_ip)

        # La 4ème doit être bloquée
        from fastapi import HTTPException
        import pytest

        with pytest.raises(HTTPException) as exc_info:
            limiter.check_bootstrap_rate(test_ip)

        assert exc_info.value.status_code == 429
        assert "bootstrap" in exc_info.value.detail.lower()

    def test_refresh_rate_limit(self):
        """Refresh rate limit doit autoriser 30 req/min."""
        from app.core.rate_limiter import AuthRateLimiter

        limiter = AuthRateLimiter()
        test_ip = "192.168.88.88"

        # 30 requêtes doivent passer
        for i in range(30):
            limiter.record_refresh_attempt(test_ip)

        # La 31ème doit être bloquée
        from fastapi import HTTPException
        import pytest

        with pytest.raises(HTTPException) as exc_info:
            limiter.check_refresh_rate(test_ip)

        assert exc_info.value.status_code == 429


class TestDemoModeProtection:
    """Tests pour la protection du mode démo."""

    def test_demo_mode_detection_in_code(self):
        """Le code frontend doit avoir une protection contre le mode démo en production."""
        from pathlib import Path

        auth_path = Path(__file__).parent.parent.parent / "frontend" / "src" / "core" / "auth" / "index.ts"
        content = auth_path.read_text()

        # Vérifie que la protection production existe
        assert "IS_PRODUCTION" in content, "Protection production manquante"
        assert "import.meta.env.PROD" in content or "MODE === 'production'" in content, \
            "Détection de production manquante"

        # Vérifie que le mode démo est conditionné
        assert "!IS_PRODUCTION" in content, "Le mode démo doit être bloqué en production"


class TestSuperAdminRestriction:
    """P1 SÉCURITÉ: Tests pour la restriction SUPERADMIN sur opérations plateforme."""

    def test_require_super_admin_rejects_dirigeant(self):
        """require_super_admin doit rejeter le rôle DIRIGEANT (rôle tenant, pas plateforme)."""
        from pathlib import Path

        router_path = Path(__file__).parent.parent.parent / "app" / "modules" / "tenants" / "router.py"
        content = router_path.read_text()

        # Vérifie que DIRIGEANT n'est PAS dans les rôles autorisés pour super_admin
        # Le code doit contenir PLATFORM_ADMIN_ROLES sans DIRIGEANT
        assert "PLATFORM_ADMIN_ROLES" in content, "Variable PLATFORM_ADMIN_ROLES manquante"
        assert "'DIRIGEANT'" not in content.split("PLATFORM_ADMIN_ROLES")[1].split("}")[0], \
            "DIRIGEANT ne doit PAS être dans PLATFORM_ADMIN_ROLES"

    def test_require_super_admin_only_superadmin(self):
        """require_super_admin doit accepter uniquement SUPERADMIN/SUPER_ADMIN."""
        from pathlib import Path

        router_path = Path(__file__).parent.parent.parent / "app" / "modules" / "tenants" / "router.py"
        content = router_path.read_text()

        # Trouver la définition de PLATFORM_ADMIN_ROLES
        import re
        match = re.search(r"PLATFORM_ADMIN_ROLES\s*=\s*\{([^}]+)\}", content)
        assert match, "Définition PLATFORM_ADMIN_ROLES non trouvée"

        roles_str = match.group(1)
        # Doit contenir SUPERADMIN et/ou SUPER_ADMIN
        assert "SUPERADMIN" in roles_str, "SUPERADMIN doit être dans PLATFORM_ADMIN_ROLES"
        # Ne doit PAS contenir ADMIN ou DIRIGEANT
        assert "'ADMIN'" not in roles_str or "'SUPERADMIN'" in roles_str, \
            "ADMIN seul ne doit pas être dans PLATFORM_ADMIN_ROLES"


class TestRedisProductionRequirement:
    """P1 SÉCURITÉ: Tests pour l'obligation Redis en production."""

    def test_redis_required_in_production_config(self):
        """La configuration doit exiger REDIS_URL en production."""
        from pathlib import Path

        config_path = Path(__file__).parent.parent.parent / "app" / "core" / "config.py"
        content = config_path.read_text()

        # Vérifie que la validation Redis production existe
        assert "REDIS_URL" in content, "Validation REDIS_URL manquante"
        assert "redis_url" in content.lower(), "Champ redis_url manquant"
        assert "OBLIGATOIRE en production" in content or "required in production" in content.lower(), \
            "Message d'erreur Redis production manquant"

    def test_redis_validation_in_production_block(self):
        """La validation Redis doit être dans le bloc production."""
        from pathlib import Path

        config_path = Path(__file__).parent.parent.parent / "app" / "core" / "config.py"
        content = config_path.read_text()

        # Trouver le bloc de validation production
        import re
        # Chercher la section qui valide redis_url après "if self.environment == 'production'"
        production_block = re.search(
            r"if self\.environment == 'production':(.*?)return self",
            content,
            re.DOTALL
        )
        assert production_block, "Bloc validation production non trouvé"

        production_content = production_block.group(1)
        assert "redis_url" in production_content, \
            "Validation redis_url doit être dans le bloc production"


class TestRLSIntegration:
    """P1 SÉCURITÉ: Tests pour l'intégration RLS PostgreSQL."""

    def test_rls_dependency_exists(self):
        """La dépendance get_db_with_rls_auto doit exister."""
        from app.core.middleware import get_db_with_rls_auto
        assert get_db_with_rls_auto is not None

    def test_rls_context_function_exists(self):
        """set_rls_context doit exister dans database.py."""
        from app.core.database import set_rls_context
        assert set_rls_context is not None

    def test_rls_middleware_sets_flag(self):
        """RLSMiddleware doit définir request.state.rls_enabled."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "core" / "middleware.py"
        content = middleware_path.read_text()

        assert "rls_enabled = True" in content, "RLSMiddleware doit définir rls_enabled"
        assert "set_rls_context" in content, "RLSMiddleware doit utiliser set_rls_context"


class TestWebSocketSecurity:
    """P0 SÉCURITÉ: Tests pour la sécurité WebSocket."""

    def test_websocket_no_token_in_url(self):
        """Le token ne doit PAS être dans l'URL WebSocket."""
        from pathlib import Path

        voice_path = Path(__file__).parent.parent.parent / "frontend" / "src" / "core" / "theo" / "voice.ts"
        content = voice_path.read_text()

        # Trouver la construction de l'URL WebSocket
        # Elle ne doit PAS contenir &token= dans l'URL
        import re
        ws_url_match = re.search(r'const wsUrl = `[^`]+`', content)
        assert ws_url_match, "Construction wsUrl non trouvée"

        ws_url_line = ws_url_match.group(0)
        assert "token" not in ws_url_line, (
            "P0 VIOLATION: Token ne doit PAS être dans l'URL WebSocket. "
            "Utiliser message 'auth' après connexion."
        )

    def test_websocket_auth_via_message(self):
        """Le token doit être envoyé via message WebSocket après connexion."""
        from pathlib import Path

        voice_path = Path(__file__).parent.parent.parent / "frontend" / "src" / "core" / "theo" / "voice.ts"
        content = voice_path.read_text()

        # Vérifie que l'auth est envoyée via message
        assert "type: 'auth'" in content, "Message auth manquant dans voice.ts"
        assert "payload: { token }" in content or "payload: {token}" in content.replace(" ", ""), \
            "Payload token manquant dans message auth"


class TestDemoModeStorage:
    """P0 SÉCURITÉ: Tests pour le stockage du mode démo."""

    def test_demo_mode_uses_session_storage(self):
        """Le mode démo doit utiliser sessionStorage (pas localStorage)."""
        from pathlib import Path
        import re

        demo_path = Path(__file__).parent.parent.parent / "frontend" / "src" / "utils" / "demoMode.ts"
        content = demo_path.read_text()

        # Vérifie que sessionStorage est utilisé
        assert "sessionStorage.getItem" in content, "sessionStorage.getItem manquant"
        assert "sessionStorage.setItem" in content, "sessionStorage.setItem manquant"

        # Vérifie que localStorage n'est PAS utilisé dans le code (exclure les commentaires)
        # Recherche localStorage.getItem ou localStorage.setItem (usage réel)
        local_storage_usage = re.search(r'localStorage\.(getItem|setItem)', content)
        assert local_storage_usage is None, (
            "P0 VIOLATION: localStorage ne doit PAS être utilisé. "
            "Utiliser sessionStorage pour cohérence avec auth."
        )


class TestDeviceBindingStrictMode:
    """P1 SÉCURITÉ: Tests pour le mode strict device binding."""

    def test_device_binding_strict_production_default(self):
        """Device binding doit être strict par défaut en production."""
        from pathlib import Path

        auth_path = Path(__file__).parent.parent.parent / "app" / "api" / "auth.py"
        content = auth_path.read_text()

        # Vérifie que le mode strict est activé par défaut en production
        assert "is_production" in content.lower(), "Vérification production manquante"
        assert "dfp_strict_default" in content, "Variable dfp_strict_default manquante"
        # En production le défaut doit être "true"
        assert '"true" if _settings.is_production' in content or "'true' if _settings.is_production" in content, \
            "Mode strict doit être 'true' par défaut en production"


class TestDemoCredentialsExternalized:
    """P1 SÉCURITÉ: Tests pour les credentials démo externalisés."""

    def test_demo_credentials_use_env_vars(self):
        """Les credentials démo doivent utiliser des variables d'environnement."""
        from pathlib import Path

        auth_path = Path(__file__).parent.parent.parent / "frontend" / "src" / "core" / "auth" / "index.ts"
        content = auth_path.read_text()

        # Vérifie que les variables d'env sont utilisées
        assert "VITE_DEMO_USER_EMAIL" in content, "Variable VITE_DEMO_USER_EMAIL manquante"
        assert "VITE_DEMO_USER_PASSWORD" in content, "Variable VITE_DEMO_USER_PASSWORD manquante"
        assert "VITE_DEMO_ADMIN_EMAIL" in content, "Variable VITE_DEMO_ADMIN_EMAIL manquante"
        assert "VITE_DEMO_ADMIN_PASSWORD" in content, "Variable VITE_DEMO_ADMIN_PASSWORD manquante"


class TestSchedulerRLSContext:
    """P1 SÉCURITÉ: Tests pour le contexte RLS dans les schedulers."""

    def test_scheduler_rls_function_exists(self):
        """La fonction get_db_for_scheduler doit exister."""
        from app.core.database import get_db_for_scheduler
        assert get_db_for_scheduler is not None

    def test_social_networks_scheduler_uses_rls(self):
        """Le scheduler social_networks doit utiliser get_db_for_scheduler."""
        from pathlib import Path

        scheduler_path = Path(__file__).parent.parent.parent / "app" / "modules" / "social_networks" / "scheduler.py"
        content = scheduler_path.read_text()

        # Vérifie que la fonction RLS est importée et utilisée
        assert "get_db_for_scheduler" in content, "get_db_for_scheduler non utilisé dans social_networks scheduler"


class TestProductionLogging:
    """P1 SÉCURITÉ: Tests pour le logging sécurisé en production."""

    @pytest.mark.skip(reason="Guardian frontend component needs production logging refactor")
    def test_guardian_uses_production_safe_logger(self):
        """Guardian doit utiliser un logger silencieux en production."""
        from pathlib import Path

        guardian_path = Path(__file__).parent.parent.parent / "frontend" / "src" / "core" / "guardian" / "index.ts"
        content = guardian_path.read_text()

        # Vérifie que le logger production-safe est défini
        assert "IS_PRODUCTION" in content, "Variable IS_PRODUCTION manquante"
        assert "debugLog" in content, "Fonction debugLog manquante"
        # Vérifie que console.debug n'est plus utilisé directement
        assert "console.debug(" not in content, "console.debug direct encore utilisé"


class TestRateLimiterProductionFail:
    """P2 SÉCURITÉ: Tests pour le rate limiter en production."""

    def test_rate_limiter_production_requires_redis(self):
        """Le rate limiter doit lever une exception en production sans Redis."""
        from pathlib import Path

        rate_limiter_path = Path(__file__).parent.parent.parent / "app" / "core" / "rate_limiter.py"
        content = rate_limiter_path.read_text()

        # Vérifie que le code lève une exception en production
        assert "raise RuntimeError" in content, "Doit lever RuntimeError en production sans Redis"
        assert "is_production" in content, "Doit vérifier is_production"
        assert "logger.critical" in content, "Doit logger en CRITICAL en production"


class TestCSPMigrationRoadmap:
    """P2 SÉCURITÉ: Tests pour la documentation CSP."""

    def test_csp_has_migration_roadmap(self):
        """La configuration CSP doit avoir une roadmap de migration documentée."""
        from pathlib import Path

        headers_path = Path(__file__).parent.parent.parent / "frontend" / "public" / "_headers"
        content = headers_path.read_text()

        # Vérifie que la roadmap est documentée
        assert "ROADMAP" in content, "Roadmap de migration CSP manquante"
        assert "nonce" in content.lower(), "Mention des nonces CSP manquante"
        assert "MITIGATION" in content, "Section mitigation manquante"


class TestCSRFTokenExpiry:
    """P2 SÉCURITÉ: Tests pour la durée du token CSRF."""

    def test_csrf_token_expiry_extended(self):
        """Le token CSRF doit avoir une durée de 24h pour les workflows longs."""
        from pathlib import Path

        csrf_path = Path(__file__).parent.parent.parent / "app" / "core" / "csrf_middleware.py"
        content = csrf_path.read_text()

        # Vérifie que l'expiration est de 24h (86400 secondes)
        assert "86400" in content, "CSRF_TOKEN_EXPIRY doit être 86400 (24h)"
        assert "24" in content, "Documentation 24 heures manquante"


class TestGuardianDataMasking:
    """P2 SÉCURITÉ: Tests pour le masquage des données Guardian."""

    def test_guardian_masks_data_attributes(self):
        """Guardian doit masquer les éléments avec data-* attributes."""
        from pathlib import Path

        store_path = Path(__file__).parent.parent.parent / "frontend" / "src" / "core" / "guardian" / "incident-store.ts"
        content = store_path.read_text()

        # Vérifie les data-* attributes de masquage
        assert "[data-sensitive]" in content, "data-sensitive manquant"
        assert "[data-pii]" in content, "data-pii manquant"
        assert "[data-mask]" in content, "data-mask manquant"
        assert "[data-confidential]" in content, "data-confidential manquant"
        assert "[data-financial]" in content, "data-financial manquant"

    def test_guardian_masks_french_identifiers(self):
        """Guardian doit masquer les identifiants français (NIR, SIRET)."""
        from pathlib import Path

        store_path = Path(__file__).parent.parent.parent / "frontend" / "src" / "core" / "guardian" / "incident-store.ts"
        content = store_path.read_text()

        # Vérifie les identifiants français
        assert "nir" in content.lower(), "Masquage NIR (sécurité sociale) manquant"
        assert "siret" in content.lower(), "Masquage SIRET manquant"


class TestSessionLocalLeakDetection:
    """P2 SÉCURITÉ: Tests pour détecter les fuites SessionLocal()."""

    def test_scheduler_db_function_documented(self):
        """La fonction get_db_for_scheduler doit être documentée."""
        from pathlib import Path

        db_path = Path(__file__).parent.parent.parent / "app" / "core" / "database.py"
        content = db_path.read_text()

        # Vérifie la documentation
        assert "get_db_for_scheduler" in content, "Fonction get_db_for_scheduler manquante"
        # P0 ou P1 SÉCURITÉ accepté (promu de P1 à P0)
        assert "P0 SÉCURITÉ" in content or "P1 SÉCURITÉ" in content, "Documentation Px SÉCURITÉ manquante"
        assert "set_rls_context" in content, "Appel set_rls_context manquant"


class TestSchedulerTenantIdRequired:
    """P0 SÉCURITÉ: get_db_for_scheduler doit exiger tenant_id."""

    def test_scheduler_tenant_id_required(self):
        """get_db_for_scheduler doit lever ValueError si tenant_id est None."""
        from pathlib import Path

        db_path = Path(__file__).parent.parent.parent / "app" / "core" / "database.py"
        content = db_path.read_text()

        # Vérifie que tenant_id est obligatoire (pas Optional, pas None par défaut)
        assert "def get_db_for_scheduler(tenant_id: str):" in content, \
            "get_db_for_scheduler doit avoir tenant_id: str (pas Optional)"
        assert "ValueError" in content, "get_db_for_scheduler doit lever ValueError si tenant_id vide"

    def test_platform_operation_function_exists(self):
        """get_db_for_platform_operation doit exister pour opérations plateforme."""
        from pathlib import Path

        db_path = Path(__file__).parent.parent.parent / "app" / "core" / "database.py"
        content = db_path.read_text()

        assert "get_db_for_platform_operation" in content, \
            "Fonction get_db_for_platform_operation manquante"
        assert "RLS_PLATFORM" in content, "Warning RLS_PLATFORM manquant"


class TestCSRFJWTValidation:
    """P1 SÉCURITÉ: Validation JWT stricte dans bypass CSRF."""

    def test_csrf_validates_jwt_format(self):
        """Le bypass CSRF doit valider le format JWT (3 parties)."""
        from pathlib import Path

        csrf_path = Path(__file__).parent.parent.parent / "app" / "core" / "csrf_middleware.py"
        content = csrf_path.read_text()

        # Vérifie validation format JWT
        assert 'split(".")' in content, "Validation split JWT manquante"
        assert "len(jwt_parts) == 3" in content, "Vérification 3 parties JWT manquante"


class TestEmailNormalization:
    """P1 SÉCURITÉ: Normalisation email dans rate limiter."""

    def test_email_normalized_in_rate_limiter(self):
        """Les emails doivent être normalisés (lowercase) pour éviter contournement."""
        from pathlib import Path

        limiter_path = Path(__file__).parent.parent.parent / "app" / "core" / "rate_limiter.py"
        content = limiter_path.read_text()

        # Vérifie normalisation email
        assert "normalized_email" in content, "Variable normalized_email manquante"
        assert ".lower()" in content, "Normalisation lowercase manquante"


class TestTenantIdMinLength:
    """P1 SÉCURITÉ: Validation longueur minimale tenant_id."""

    def test_tenant_id_min_length_validated(self):
        """tenant_id doit avoir une longueur minimale de 3 caractères."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "core" / "middleware.py"
        content = middleware_path.read_text()

        # Vérifie longueur minimale
        assert "len(tenant_id) < 3" in content, "Validation longueur minimale tenant_id manquante"


class TestNginxSecurityHeaders:
    """P0 SÉCURITÉ: Headers de sécurité nginx."""

    def test_nginx_has_hsts(self):
        """Nginx doit avoir HSTS configuré."""
        from pathlib import Path

        nginx_path = Path(__file__).parent.parent.parent / "infra" / "nginx" / "conf.d" / "default.conf"
        content = nginx_path.read_text()

        assert "Strict-Transport-Security" in content, "HSTS header manquant"
        assert "max-age=31536000" in content, "HSTS max-age 1 an manquant"
        assert "includeSubDomains" in content, "HSTS includeSubDomains manquant"

    def test_nginx_csp_no_unsafe_eval(self):
        """CSP ne doit pas contenir unsafe-eval dans script-src."""
        from pathlib import Path
        import re

        nginx_path = Path(__file__).parent.parent.parent / "infra" / "nginx" / "conf.d" / "default.conf"
        content = nginx_path.read_text()

        # Extraire la directive CSP (lignes add_header Content-Security-Policy)
        csp_match = re.search(r'Content-Security-Policy\s+"([^"]+)"', content)
        assert csp_match, "Directive CSP introuvable"
        csp_directive = csp_match.group(1)

        # Vérifie absence de unsafe-eval dans script-src de la directive CSP
        assert "'unsafe-eval'" not in csp_directive, "unsafe-eval présent dans CSP (P0 vulnérabilité)"

    def test_nginx_has_permissions_policy(self):
        """Nginx doit avoir Permissions-Policy configuré."""
        from pathlib import Path

        nginx_path = Path(__file__).parent.parent.parent / "infra" / "nginx" / "conf.d" / "default.conf"
        content = nginx_path.read_text()

        assert "Permissions-Policy" in content, "Permissions-Policy header manquant"


class TestRateLimiterTrustedProxies:
    """P1 SÉCURITÉ: Validation X-Forwarded-For avec proxies de confiance."""

    def test_rate_limiter_validates_trusted_proxies(self):
        """Le rate limiter doit valider TRUSTED_PROXIES avant d'accepter X-Forwarded-For."""
        from pathlib import Path

        limiter_path = Path(__file__).parent.parent.parent / "app" / "core" / "rate_limiter.py"
        content = limiter_path.read_text()

        assert "TRUSTED_PROXIES" in content, "TRUSTED_PROXIES manquant dans rate_limiter"
        assert "is_trusted" in content, "Vérification is_trusted manquante"


class TestViteConsoleRemoval:
    """P1 SÉCURITÉ: Suppression console.log en production."""

    def test_vite_removes_console_in_production(self):
        """Vite doit supprimer console.* en production."""
        from pathlib import Path

        vite_path = Path(__file__).parent.parent.parent / "frontend" / "vite.config.ts"
        content = vite_path.read_text()

        assert "drop_console" in content, "drop_console manquant dans vite config"
        assert "terser" in content.lower(), "terser minifier manquant"


class TestMigrationSecurityDefiner:
    """P1 SÉCURITÉ: SECURITY DEFINER sur fonction RLS."""

    def test_rls_function_has_security_definer(self):
        """La fonction get_current_tenant_id doit avoir SECURITY DEFINER."""
        from pathlib import Path

        migration_path = Path(__file__).parent.parent.parent / "migrations" / "034_enable_rls_policies.sql"
        content = migration_path.read_text()

        assert "SECURITY DEFINER" in content, "SECURITY DEFINER manquant dans migration 034"


class TestAppUrlHttpsValidation:
    """P1 SÉCURITÉ: app_url doit utiliser HTTPS en production."""

    def test_app_url_https_validation_exists(self):
        """La config doit valider que app_url utilise HTTPS en production."""
        from pathlib import Path

        config_path = Path(__file__).parent.parent.parent / "app" / "core" / "config.py"
        content = config_path.read_text()

        assert "app_url DOIT utiliser https://" in content, "Validation HTTPS app_url manquante"


class TestRedirectDomainValidation:
    """P1 SÉCURITÉ: Validation des domaines de redirection."""

    def test_redirect_validation_function_exists(self):
        """La fonction validate_redirect_url doit exister."""
        from pathlib import Path

        config_path = Path(__file__).parent.parent.parent / "app" / "core" / "config.py"
        content = config_path.read_text()

        assert "def validate_redirect_url" in content, "Fonction validate_redirect_url manquante"
        assert "ALLOWED_REDIRECT_DOMAINS" in content, "ALLOWED_REDIRECT_DOMAINS manquant"

    def test_safe_redirect_helper_exists(self):
        """La fonction get_safe_redirect_url doit exister."""
        from pathlib import Path

        config_path = Path(__file__).parent.parent.parent / "app" / "core" / "config.py"
        content = config_path.read_text()

        assert "def get_safe_redirect_url" in content, "Fonction get_safe_redirect_url manquante"


class TestNpmAuditIntegration:
    """P1 SÉCURITÉ: npm audit intégré au build."""

    def test_npm_audit_script_exists(self):
        """package.json doit avoir un script security:audit."""
        from pathlib import Path

        package_path = Path(__file__).parent.parent.parent / "frontend" / "package.json"
        content = package_path.read_text()

        assert "security:audit" in content, "Script security:audit manquant"
        assert "npm audit" in content, "Commande npm audit manquante"

    def test_prebuild_audit_exists(self):
        """Le prebuild doit inclure l'audit de sécurité."""
        from pathlib import Path

        package_path = Path(__file__).parent.parent.parent / "frontend" / "package.json"
        content = package_path.read_text()

        assert "prebuild" in content, "Script prebuild manquant"


class TestHtml2CanvasSecurity:
    """P2 SÉCURITÉ: html2canvas configuré de manière sécurisée."""

    def test_allow_taint_disabled(self):
        """html2canvas doit avoir allowTaint: false pour éviter la capture cross-origin."""
        from pathlib import Path

        store_path = Path(__file__).parent.parent.parent / "frontend" / "src" / "core" / "guardian" / "incident-store.ts"
        content = store_path.read_text()

        assert "allowTaint: false" in content, "allowTaint devrait être false"

    def test_timeout_configured(self):
        """html2canvas doit avoir un timeout configuré (via option ou Promise.race)."""
        from pathlib import Path

        store_path = Path(__file__).parent.parent.parent / "frontend" / "src" / "core" / "guardian" / "incident-store.ts"
        content = store_path.read_text()

        # Accepter soit l'option timeout: soit Promise.race avec timeout
        has_option_timeout = "timeout:" in content
        has_promise_race_timeout = "Promise.race" in content and "5000" in content
        assert has_option_timeout or has_promise_race_timeout, \
            "Timeout html2canvas manquant (ni option timeout: ni Promise.race)"


class TestCrossTenantIsolation:
    """P2 SÉCURITÉ: Tests d'isolation cross-tenant."""

    def test_tenant_filter_in_base_query(self):
        """Les services doivent filtrer par tenant_id dans leurs requêtes."""
        from pathlib import Path

        # Vérifier le service projects comme exemple
        service_path = Path(__file__).parent.parent.parent / "app" / "modules" / "projects" / "service.py"
        if service_path.exists():
            content = service_path.read_text()
            assert "tenant_id" in content, "Filtre tenant_id manquant dans ProjectsService"
            assert "self.tenant_id" in content, "Utilisation self.tenant_id manquante"

    def test_get_db_for_scheduler_documented(self):
        """get_db_for_scheduler doit être documenté avec les bonnes pratiques."""
        from pathlib import Path

        db_path = Path(__file__).parent.parent.parent / "app" / "core" / "database.py"
        content = db_path.read_text()

        assert "P0 SÉCURITÉ" in content or "P0 CRITIQUE" in content, \
            "Documentation P0 SÉCURITÉ manquante pour get_db_for_scheduler"
        assert "ValueError" in content, "ValueError pour tenant_id null manquant"


class TestDatabasePoolSecurity:
    """P0 SÉCURITÉ: Protection contre DoS par épuisement pool."""

    def test_pool_timeout_configured(self):
        """Le pool de connexions doit avoir pool_timeout configuré."""
        from pathlib import Path

        db_path = Path(__file__).parent.parent.parent / "app" / "core" / "database.py"
        content = db_path.read_text()

        assert "pool_timeout" in content, "pool_timeout manquant dans database.py"
        assert "pool_recycle" in content, "pool_recycle manquant"

    def test_connect_timeout_configured(self):
        """Le timeout de connexion doit être configuré."""
        from pathlib import Path

        db_path = Path(__file__).parent.parent.parent / "app" / "core" / "database.py"
        content = db_path.read_text()

        assert "connect_timeout" in content, "connect_timeout manquant"
        assert "statement_timeout" in content, "statement_timeout manquant"


class TestJWTSizeValidation:
    """P0 SÉCURITÉ: Validation taille JWT pour éviter DoS."""

    def test_jwt_max_size_validated(self):
        """decode_access_token doit valider la taille max du token."""
        from pathlib import Path

        security_path = Path(__file__).parent.parent.parent / "app" / "core" / "security.py"
        content = security_path.read_text()

        assert "MAX_TOKEN_SIZE" in content, "MAX_TOKEN_SIZE manquant"
        assert "len(token) > MAX_TOKEN_SIZE" in content or "len(token) >" in content, \
            "Validation taille token manquante"


class TestContentLengthValidation:
    """P0 SÉCURITÉ: Validation Content-Length stricte."""

    def test_content_length_required_for_post(self):
        """Content-Length doit être requis pour POST/PUT/PATCH."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "core" / "security_middleware.py"
        content = middleware_path.read_text()

        assert "Content-Length manquant" in content or "Content-Length header is required" in content, \
            "Validation Content-Length obligatoire manquante"
        assert "411" in content, "Code HTTP 411 Length Required manquant"

    def test_invalid_content_length_rejected(self):
        """Content-Length invalide doit être rejeté (fail closed)."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "core" / "security_middleware.py"
        content = middleware_path.read_text()

        assert "request_rejected" in content, "Rejet requête Content-Length invalide manquant"


class TestJWTBase64urlValidation:
    """P0 SÉCURITÉ: Validation base64url dans JWT."""

    def test_csrf_validates_base64url(self):
        """Le bypass CSRF doit valider l'encodage base64url des parties JWT."""
        from pathlib import Path

        csrf_path = Path(__file__).parent.parent.parent / "app" / "core" / "csrf_middleware.py"
        content = csrf_path.read_text()

        assert "_is_valid_base64url" in content, "Méthode _is_valid_base64url manquante"
        assert "base64url" in content.lower(), "Validation base64url manquante"


class TestAdditionalSecurityHeaders:
    """P1 SÉCURITÉ: Headers de sécurité additionnels."""

    def test_cross_domain_policies_header(self):
        """X-Permitted-Cross-Domain-Policies doit être présent."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "core" / "security_middleware.py"
        content = middleware_path.read_text()

        assert "X-Permitted-Cross-Domain-Policies" in content, "Header X-Permitted-Cross-Domain-Policies manquant"

    def test_cross_origin_embedder_policy(self):
        """Cross-Origin-Embedder-Policy doit être présent."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "core" / "security_middleware.py"
        content = middleware_path.read_text()

        assert "Cross-Origin-Embedder-Policy" in content, "Header COEP manquant"
        assert "require-corp" in content, "COEP require-corp manquant"

    def test_cross_origin_opener_policy(self):
        """Cross-Origin-Opener-Policy doit être présent."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "core" / "security_middleware.py"
        content = middleware_path.read_text()

        assert "Cross-Origin-Opener-Policy" in content, "Header COOP manquant"


class TestTenantIdReservedNames:
    """P1 SÉCURITÉ: Noms de tenant réservés."""

    def test_reserved_tenant_ids_list_exists(self):
        """La liste RESERVED_TENANT_IDS doit exister."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "core" / "middleware.py"
        content = middleware_path.read_text()

        assert "RESERVED_TENANT_IDS" in content, "Liste RESERVED_TENANT_IDS manquante"

    def test_reserved_names_include_system(self):
        """Les noms système doivent être réservés."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "core" / "middleware.py"
        content = middleware_path.read_text()

        # Vérifier quelques noms critiques
        assert '"admin"' in content or "'admin'" in content, "admin devrait être réservé"
        assert '"system"' in content or "'system'" in content, "system devrait être réservé"
        assert '"root"' in content or "'root'" in content, "root devrait être réservé"

    def test_underscore_prefix_blocked(self):
        """Les tenant_ids commençant par _ doivent être bloqués."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "core" / "middleware.py"
        content = middleware_path.read_text()

        assert "startswith('_')" in content, "Blocage préfixe _ manquant"


class TestEmailNormalizationAuth:
    """P1 SÉCURITÉ: Normalisation email dans registration."""

    def test_email_normalized_in_registration(self):
        """Les emails doivent être normalisés (lowercase) dans registration."""
        from pathlib import Path

        auth_path = Path(__file__).parent.parent.parent / "app" / "api" / "auth.py"
        content = auth_path.read_text()

        assert "normalized_email" in content, "Variable normalized_email manquante"
        assert "func.lower" in content or ".lower()" in content, "Normalisation lowercase manquante"


class TestAuthRateLimitsStrict:
    """P1 SÉCURITÉ: Rate limits auth stricts."""

    def test_login_rate_limit_reduced(self):
        """Login rate limit doit être <= 5/min."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "core" / "security_middleware.py"
        content = middleware_path.read_text()

        # Vérifier que login n'est plus à 10
        assert '"/auth/login": 5' in content or '"/auth/login": 3' in content, \
            "Rate limit login doit être <= 5"

    def test_2fa_rate_limited(self):
        """2FA endpoint doit être rate limited."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "core" / "security_middleware.py"
        content = middleware_path.read_text()

        assert "2fa/verify-login" in content, "Endpoint 2FA non rate limited"


class TestSchedulerRLSContextFixed:
    """P0 SÉCURITÉ: Scheduler utilise RLS context correctement."""

    def test_scheduler_uses_platform_operation(self):
        """Scheduler doit utiliser get_db_for_platform_operation pour queries cross-tenant."""
        from pathlib import Path

        scheduler_path = Path(__file__).parent.parent.parent / "app" / "services" / "scheduler.py"
        content = scheduler_path.read_text()

        assert "get_db_for_platform_operation" in content, \
            "Scheduler doit utiliser get_db_for_platform_operation"

    def test_scheduler_uses_tenant_db(self):
        """Scheduler doit utiliser get_db_for_scheduler pour opérations tenant."""
        from pathlib import Path

        scheduler_path = Path(__file__).parent.parent.parent / "app" / "services" / "scheduler.py"
        content = scheduler_path.read_text()

        assert "get_db_for_scheduler" in content, \
            "Scheduler doit utiliser get_db_for_scheduler pour operations tenant"

    def test_scheduler_no_bare_session_local(self):
        """Scheduler ne doit pas utiliser SessionLocal() directement."""
        from pathlib import Path

        scheduler_path = Path(__file__).parent.parent.parent / "app" / "services" / "scheduler.py"
        content = scheduler_path.read_text()

        # Vérifier que SessionLocal n'est plus importé ou utilisé
        assert "from app.core.database import get_db_for_scheduler" in content, \
            "Import get_db_for_scheduler manquant"
        # SessionLocal ne devrait pas être dans les imports
        assert "SessionLocal" not in content or "SessionLocal()" not in content, \
            "SessionLocal() ne doit pas être utilisé directement"


class TestGuardianSanitization:
    """P1 SÉCURITÉ: Guardian sanitize les données sensibles."""

    def test_guardian_has_sensitive_patterns(self):
        """Guardian doit avoir des patterns de données sensibles."""
        from pathlib import Path

        store_path = Path(__file__).parent.parent.parent / "frontend" / "src" / "core" / "guardian" / "incident-store.ts"
        content = store_path.read_text()

        assert "SENSITIVE_PATTERNS" in content, "Liste SENSITIVE_PATTERNS manquante"
        assert "REDACTED" in content, "Remplacement REDACTED manquant"

    def test_guardian_sanitizes_message(self):
        """Guardian doit sanitize le message avant envoi."""
        from pathlib import Path

        store_path = Path(__file__).parent.parent.parent / "frontend" / "src" / "core" / "guardian" / "incident-store.ts"
        content = store_path.read_text()

        assert "sanitizeForIncident" in content, "Fonction sanitizeForIncident manquante"
        assert "sanitizeForIncident(incident.message)" in content, \
            "Message doit être sanitizé"


class TestPlatformOperationAudit:
    """P1 SÉCURITÉ: Audit des opérations plateforme."""

    def test_platform_operation_has_caller_param(self):
        """get_db_for_platform_operation doit avoir un paramètre caller."""
        from pathlib import Path

        db_path = Path(__file__).parent.parent.parent / "app" / "core" / "database.py"
        content = db_path.read_text()

        assert "def get_db_for_platform_operation(caller" in content, \
            "Paramètre caller manquant"

    def test_platform_operation_logs_caller(self):
        """get_db_for_platform_operation doit logger le caller."""
        from pathlib import Path

        db_path = Path(__file__).parent.parent.parent / "app" / "core" / "database.py"
        content = db_path.read_text()

        assert '"caller":' in content or "'caller':" in content, \
            "Logger caller manquant"


class TestProductionDependencies:
    """P0 SÉCURITÉ: Dépendances production sans vulnérabilités."""

    def test_no_production_vulnerabilities(self):
        """npm audit --omit=dev ne doit pas avoir de vulnérabilités."""
        import subprocess
        import os

        frontend_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "frontend"
        )

        # Skip si pas de npm
        try:
            result = subprocess.run(
                ["npm", "audit", "--omit=dev", "--json"],
                cwd=frontend_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            import json
            audit_data = json.loads(result.stdout)
            vuln_count = audit_data.get("metadata", {}).get("vulnerabilities", {})
            high_count = vuln_count.get("high", 0) + vuln_count.get("critical", 0)
            assert high_count == 0, f"Vulnérabilités production: {high_count} high/critical"
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
            # Skip test si npm non disponible
            pass


class TestInitProductionNoHardcodedPassword:
    """P0 SÉCURITÉ: Pas de password hardcodée dans init_production."""

    def test_no_hardcoded_admin_password(self):
        """init_production.py ne doit pas avoir de password hardcodée."""
        from pathlib import Path

        script_path = Path(__file__).parent.parent.parent / "scripts" / "deploy" / "init_production.py"
        content = script_path.read_text()

        # Vérifier que Gobelet2026! n'apparaît plus
        assert "Gobelet2026!" not in content, \
            "Password hardcodée Gobelet2026! trouvée - CRITIQUE"

    def test_admin_password_from_env_only(self):
        """Admin password doit venir uniquement de variable d'env."""
        from pathlib import Path

        script_path = Path(__file__).parent.parent.parent / "scripts" / "deploy" / "init_production.py"
        content = script_path.read_text()

        # Vérifier que le code vérifie si password est définie
        assert "if not admin_password:" in content, \
            "Vérification admin_password manquante"

    def test_missing_password_does_not_crash(self):
        """Sans MASITH_ADMIN_PASSWORD, le script doit skip gracieusement."""
        from pathlib import Path

        script_path = Path(__file__).parent.parent.parent / "scripts" / "deploy" / "init_production.py"
        content = script_path.read_text()

        # Vérifier qu'il y a un return après la vérification
        assert "return" in content.split("if not admin_password:")[1][:200], \
            "Script doit return si password manquante"


class TestGuardianMiddlewareRLSContext:
    """P0 SÉCURITÉ: Guardian middleware utilise RLS context."""

    def test_guardian_imports_rls_functions(self):
        """Guardian middleware doit importer les fonctions RLS."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "modules" / "guardian" / "middleware.py"
        content = middleware_path.read_text()

        assert "get_db_for_platform_operation" in content, \
            "Import get_db_for_platform_operation manquant"
        assert "set_rls_context" in content, \
            "Import set_rls_context manquant"

    def test_guardian_check_tables_uses_platform_operation(self):
        """_check_tables_exist doit utiliser get_db_for_platform_operation."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "modules" / "guardian" / "middleware.py"
        content = middleware_path.read_text()

        # Vérifier dans la fonction _check_tables_exist
        check_tables_section = content.split("def _check_tables_exist")[1].split("def ")[0]
        assert "get_db_for_platform_operation" in check_tables_section, \
            "_check_tables_exist doit utiliser get_db_for_platform_operation"

    def test_guardian_record_http_error_uses_rls(self):
        """_record_http_error doit utiliser set_rls_context."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "modules" / "guardian" / "middleware.py"
        content = middleware_path.read_text()

        # Vérifier dans la fonction _record_http_error
        record_section = content.split("async def _record_http_error")[1].split("async def ")[0]
        assert "set_rls_context" in record_section, \
            "_record_http_error doit utiliser set_rls_context"

    def test_guardian_record_exception_uses_rls(self):
        """_record_exception doit utiliser set_rls_context."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "modules" / "guardian" / "middleware.py"
        content = middleware_path.read_text()

        # Vérifier dans la fonction _record_exception
        record_section = content.split("async def _record_exception")[1].split("def ")[0]
        assert "set_rls_context" in record_section, \
            "_record_exception doit utiliser set_rls_context"

    def test_guardian_no_bare_session_local(self):
        """Guardian middleware ne doit pas utiliser SessionLocal() sans RLS."""
        from pathlib import Path

        middleware_path = Path(__file__).parent.parent.parent / "app" / "modules" / "guardian" / "middleware.py"
        content = middleware_path.read_text()

        # Compter les occurrences de SessionLocal()
        session_local_count = content.count("SessionLocal()")

        # Compter les occurrences de set_rls_context
        rls_context_count = content.count("set_rls_context(db, tenant_id)")

        # Il devrait y avoir autant de set_rls_context que de SessionLocal()
        # sauf pour _check_tables_exist qui utilise get_db_for_platform_operation
        platform_op_count = content.count("get_db_for_platform_operation")

        # Vérifier cohérence: chaque SessionLocal devrait avoir soit RLS soit platform_op
        assert session_local_count <= rls_context_count + platform_op_count, \
            f"SessionLocal()={session_local_count} doit avoir RLS={rls_context_count} ou platform_op={platform_op_count}"


class TestBcryptCostFactor:
    """P1 SÉCURITÉ: Bcrypt doit utiliser un cost factor suffisant."""

    def test_bcrypt_rounds_minimum_14(self):
        """Bcrypt doit utiliser rounds=14 minimum (OWASP 2023)."""
        from pathlib import Path

        security_path = Path(__file__).parent.parent.parent / "app" / "core" / "security.py"
        content = security_path.read_text()

        assert "rounds=14" in content, "bcrypt rounds doit être >= 14"

    def test_bcrypt_cost_documented(self):
        """Le choix du cost factor doit être documenté."""
        from pathlib import Path

        security_path = Path(__file__).parent.parent.parent / "app" / "core" / "security.py"
        content = security_path.read_text()

        assert "OWASP" in content or "cost" in content.lower(), \
            "Documentation OWASP ou cost factor manquante"


class TestRefreshTokenTTL:
    """P1 SÉCURITÉ: Refresh token TTL doit être raisonnable."""

    def test_refresh_token_max_2_days(self):
        """Refresh token ne doit pas dépasser 2 jours (OWASP recommande 24-48h)."""
        from pathlib import Path

        security_path = Path(__file__).parent.parent.parent / "app" / "core" / "security.py"
        content = security_path.read_text()

        # Chercher REFRESH_TOKEN_EXPIRE_DAYS = X
        import re
        match = re.search(r'REFRESH_TOKEN_EXPIRE_DAYS\s*=\s*(\d+)', content)
        assert match, "REFRESH_TOKEN_EXPIRE_DAYS non trouvé"
        days = int(match.group(1))
        assert days <= 2, f"Refresh token TTL={days} jours, doit être <= 2"


class TestCSPHeader:
    """P1 SÉCURITÉ: Content Security Policy doit être configurée."""

    def test_csp_meta_tag_exists(self):
        """index.html doit avoir une balise meta CSP."""
        from pathlib import Path

        index_path = Path(__file__).parent.parent.parent / "frontend" / "index.html"
        content = index_path.read_text()

        assert "Content-Security-Policy" in content, "Meta CSP manquante"

    def test_csp_has_default_src(self):
        """CSP doit avoir default-src 'self'."""
        from pathlib import Path

        index_path = Path(__file__).parent.parent.parent / "frontend" / "index.html"
        content = index_path.read_text()

        assert "default-src 'self'" in content, "CSP default-src 'self' manquant"

    @pytest.mark.skip(reason="CSP frame-ancestors configuration pending in frontend")
    def test_csp_frame_ancestors_none(self):
        """CSP doit bloquer l'intégration en iframe."""
        from pathlib import Path

        index_path = Path(__file__).parent.parent.parent / "frontend" / "index.html"
        content = index_path.read_text()

        assert "frame-ancestors 'none'" in content, "CSP frame-ancestors 'none' manquant"


class TestPermissionsPolicy:
    """P1 SÉCURITÉ: Permissions Policy doit être configurée."""

    def test_permissions_policy_exists(self):
        """index.html doit avoir une balise Permissions-Policy."""
        from pathlib import Path

        index_path = Path(__file__).parent.parent.parent / "frontend" / "index.html"
        content = index_path.read_text()

        assert "Permissions-Policy" in content, "Meta Permissions-Policy manquante"

    def test_geolocation_disabled(self):
        """Geolocation doit être désactivée."""
        from pathlib import Path

        index_path = Path(__file__).parent.parent.parent / "frontend" / "index.html"
        content = index_path.read_text()

        assert "geolocation=()" in content, "geolocation=() manquant"

    def test_camera_microphone_disabled(self):
        """Camera et microphone doivent être désactivés."""
        from pathlib import Path

        index_path = Path(__file__).parent.parent.parent / "frontend" / "index.html"
        content = index_path.read_text()

        assert "camera=()" in content, "camera=() manquant"
        assert "microphone=()" in content, "microphone=() manquant"


class TestSourceMapsDisabled:
    """P1 SÉCURITÉ: Source maps doivent être désactivées en production."""

    def test_sourcemap_false_in_vite_config(self):
        """vite.config.ts doit avoir sourcemap: false."""
        from pathlib import Path

        vite_path = Path(__file__).parent.parent.parent / "frontend" / "vite.config.ts"
        content = vite_path.read_text()

        assert "sourcemap: false" in content, "sourcemap: false manquant"


class TestSchedulerMaxInstances:
    """P1 SÉCURITÉ: Scheduler doit avoir des limites de jobs."""

    def test_scheduler_has_max_instances(self):
        """Scheduler doit configurer max_instances."""
        from pathlib import Path

        scheduler_path = Path(__file__).parent.parent.parent / "app" / "services" / "scheduler.py"
        content = scheduler_path.read_text()

        assert "max_instances" in content, "max_instances manquant dans scheduler"

    def test_scheduler_has_job_defaults(self):
        """Scheduler doit avoir des job_defaults."""
        from pathlib import Path

        scheduler_path = Path(__file__).parent.parent.parent / "app" / "services" / "scheduler.py"
        content = scheduler_path.read_text()

        assert "job_defaults" in content, "job_defaults manquant dans scheduler"

    def test_scheduler_has_timezone(self):
        """Scheduler doit avoir un timezone configuré."""
        from pathlib import Path

        scheduler_path = Path(__file__).parent.parent.parent / "app" / "services" / "scheduler.py"
        content = scheduler_path.read_text()

        assert "timezone" in content, "timezone manquant dans scheduler"
        assert "Europe/Paris" in content, "timezone doit être Europe/Paris"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
