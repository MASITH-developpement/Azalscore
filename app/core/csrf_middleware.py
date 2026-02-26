"""
AZALS - CSRF Protection Middleware
==================================

Protection contre les attaques Cross-Site Request Forgery.
Vérifie le token CSRF pour toutes les requêtes modifiantes (POST, PUT, DELETE, PATCH).

Usage:
    from app.core.csrf_middleware import CSRFMiddleware, generate_csrf_token

    app.add_middleware(CSRFMiddleware)

    # Dans un endpoint pour générer le token
    @router.get("/csrf-token")
    def get_csrf_token(request: Request):
        return {"csrf_token": generate_csrf_token(request)}
"""
from __future__ import annotations


import hashlib
import hmac
import logging
import secrets
import time
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Durée de validité du token CSRF (1 heure)
CSRF_TOKEN_EXPIRY = 3600

# Méthodes HTTP qui modifient les données (nécessitent CSRF)
UNSAFE_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

# Endpoints exemptés de la validation CSRF
CSRF_EXEMPT_PATHS = {
    # Auth endpoints (utilisent leur propre mécanisme)
    "/auth/login",
    "/auth/register",
    "/auth/logout",
    "/auth/refresh",
    "/auth/2fa/verify-login",
    "/v1/auth/login",
    "/v1/auth/register",
    "/v1/auth/logout",
    "/v1/auth/refresh",
    "/v1/auth/2fa/verify-login",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/logout",
    "/api/v1/auth/refresh",
    "/api/v1/auth/2fa/verify-login",
    # Health checks
    "/health",
    "/health/live",
    "/health/ready",
    # Webhooks (authentifiés différemment)
    "/webhooks/",
    "/api/webhooks/",
    # Metrics endpoints (internal use)
    "/metrics/test-ai",
    "/metrics/test-website",
    "/metrics/update-tenants",
    "/metrics/update-users",
    "/metrics/reset",
    "/metrics/update-marketing",
    "/api/metrics/test-ai",
    "/api/metrics/test-website",
    "/api/metrics/update-tenants",
    "/api/metrics/update-users",
    "/api/metrics/reset",
    "/api/metrics/update-marketing",
    # Admin Social Networks endpoints (internal use)
    "/admin/social-networks/",
    "/v1/admin/social-networks/",
    "/api/v1/admin/social-networks/",
}


def _get_csrf_secret() -> str:
    """Récupère le secret CSRF depuis les settings."""
    import os
    try:
        from app.core.config import get_settings
        settings = get_settings()
        return getattr(settings, 'csrf_secret', None) or settings.secret_key
    except Exception as e:
        # SÉCURITÉ: En production, JAMAIS de fallback - lever une exception
        env = os.getenv("ENVIRONMENT", os.getenv("AZALS_ENV", "development"))
        if env == "production":
            logger.error(
                "[CSRF_CONFIG] CRITICAL: Impossible de charger le secret CSRF en production",
                extra={"error": str(e)[:200]}
            )
            raise RuntimeError(
                "CSRF secret configuration mandatory in production. "
                "Set CSRF_SECRET or SECRET_KEY environment variable."
            )
        # Fallback UNIQUEMENT pour tests/développement
        logger.warning(
            "[CSRF_CONFIG] Échec chargement secret CSRF depuis settings (env=%s)",
            env,
            extra={"error": str(e)[:200], "consequence": "fallback_secret_used"}
        )
        return "csrf-secret-fallback-not-for-production"


def generate_csrf_token(request: Request) -> str:
    """
    Génère un token CSRF sécurisé.

    Le token inclut:
    - Un nonce aléatoire
    - Un timestamp pour expiration
    - Une signature HMAC

    Args:
        request: FastAPI Request object

    Returns:
        Token CSRF encodé
    """
    secret = _get_csrf_secret()
    nonce = secrets.token_hex(16)
    timestamp = str(int(time.time()))

    # Créer la signature
    message = f"{nonce}:{timestamp}"
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    # Token format: nonce:timestamp:signature
    token = f"{nonce}:{timestamp}:{signature}"

    return token


def validate_csrf_token(token: str) -> tuple[bool, str]:
    """
    Valide un token CSRF.

    Args:
        token: Token CSRF à valider

    Returns:
        (is_valid, error_message)
    """
    if not token:
        return False, "Missing CSRF token"

    try:
        parts = token.split(":")
        if len(parts) != 3:
            return False, "Invalid CSRF token format"

        nonce, timestamp, signature = parts

        # Vérifier l'expiration
        token_time = int(timestamp)
        if time.time() - token_time > CSRF_TOKEN_EXPIRY:
            return False, "CSRF token expired"

        # Vérifier la signature
        secret = _get_csrf_secret()
        message = f"{nonce}:{timestamp}"
        expected_signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            return False, "Invalid CSRF token signature"

        return True, ""

    except (ValueError, TypeError) as e:
        return False, f"CSRF token validation error: {e}"


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware de protection CSRF.

    Vérifie la présence et validité du token CSRF pour toutes
    les requêtes modifiantes (POST, PUT, DELETE, PATCH).

    Le token peut être fourni via:
    - Header X-CSRF-Token
    - Form field _csrf_token
    """

    def __init__(self, app, enforce: bool = True):
        """
        Args:
            app: Application FastAPI
            enforce: Si False, log les erreurs mais ne bloque pas (mode audit)
        """
        super().__init__(app)
        self.enforce = enforce

    async def dispatch(self, request: Request, call_next):
        """Intercepte les requêtes et vérifie le CSRF."""

        # Bypass pour méthodes sûres
        if request.method not in UNSAFE_METHODS:
            return await call_next(request)

        # Bypass pour endpoints exemptés
        path = request.url.path
        if any(path.startswith(exempt) for exempt in CSRF_EXEMPT_PATHS):
            return await call_next(request)

        # Bypass si API token (authentification Bearer)
        # SÉCURITÉ: Les requêtes avec Bearer token sont protégées contre CSRF car:
        # 1. Les tokens JWT sont stockés côté client (localStorage/sessionStorage)
        # 2. JavaScript cross-origin ne peut pas accéder à ces storages (Same-Origin Policy)
        # 3. Le token doit être explicitement ajouté au header Authorization
        # 4. Contrairement aux cookies, les tokens ne sont PAS envoyés automatiquement
        # Référence: OWASP - "CSRF tokens are not needed for APIs that use bearer tokens"
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Validation supplémentaire: vérifier que le token a un format valide
            token_parts = auth_header.split(" ", 1)
            if len(token_parts) == 2 and len(token_parts[1]) > 20:
                # Token présent et de longueur minimale (JWT = ~100+ chars)
                return await call_next(request)
            else:
                # Token malformé - ne pas bypasser CSRF
                logger.warning(
                    "[CSRF] Bearer token malformé détecté",
                    extra={"path": path, "method": request.method}
                )

        # Extraire le token CSRF
        csrf_token = self._get_csrf_token(request)

        # Valider le token
        is_valid, error = validate_csrf_token(csrf_token)

        if not is_valid:
            logger.warning(
                "[CSRF] Validation failed: %s | "
                "Path: %s | Method: %s | "
                "IP: %s",
                error, path, request.method, request.client.host if request.client else 'unknown'
            )

            if self.enforce:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "CSRF validation failed",
                        "detail": error,
                        "code": "CSRF_INVALID"
                    }
                )

        return await call_next(request)

    def _get_csrf_token(self, request: Request) -> Optional[str]:
        """Extrait le token CSRF de la requête."""
        # D'abord vérifier le header
        token = request.headers.get("X-CSRF-Token")
        if token:
            return token

        # Ensuite vérifier X-XSRF-Token (Angular)
        token = request.headers.get("X-XSRF-Token")
        if token:
            return token

        return None


def setup_csrf_middleware(app, enforce: bool = True):
    """
    Configure le middleware CSRF sur l'application.

    Args:
        app: Application FastAPI
        enforce: Si True, bloque les requêtes invalides.
                 Si False, mode audit (log seulement).
    """
    app.add_middleware(CSRFMiddleware, enforce=enforce)
    logger.info("[CSRF] Middleware configured (enforce=%s)", enforce)


__all__ = [
    "CSRFMiddleware",
    "generate_csrf_token",
    "validate_csrf_token",
    "setup_csrf_middleware",
]
