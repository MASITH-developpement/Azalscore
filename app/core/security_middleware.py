"""
AZALS - Security Middleware Production
======================================
CORS, Rate Limiting, Security Headers, Request Validation.

SÉCURITÉ: Utilise build_error_response du module Guardian pour garantir
          qu'aucune erreur ne provoque de crash, même sans fichiers HTML.
"""

import logging
import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Import de la fonction SAFE de gestion des erreurs
# Note: Utilise error_response.py au lieu de middleware.py pour éviter les imports circulaires
from app.modules.guardian.error_response import (
    ErrorType,
    build_error_response,
)

# ============================================================================
# CONFIGURATION CORS
# ============================================================================

def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS pour l'application.
    PRODUCTION: Utilise CORS_ORIGINS depuis la configuration (OBLIGATOIRE).
    DÉVELOPPEMENT: Autorise toutes les origines.
    """
    settings = get_settings()

    # PRODUCTION: CORS restrictif OBLIGATOIRE
    if not settings.cors_origins:
        raise ValueError(
            "CORS_ORIGINS est OBLIGATOIRE en production. "
            "Ex: CORS_ORIGINS=https://app.votre-domaine.com"
        )

    # Parser les origines depuis la config
    origins = [origin.strip() for origin in settings.cors_origins.split(",")]

    # Validation: pas de wildcard en production
    if "*" in origins:
        raise ValueError("CORS_ORIGINS=* est INTERDIT en production")

    # Validation: pas de localhost en production
    for origin in origins:
        if "localhost" in origin.lower() or "127.0.0.1" in origin:
            raise ValueError(f"localhost interdit dans CORS_ORIGINS en production: {origin}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,  # Autorisé avec origines spécifiques
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Tenant-ID", "X-Request-ID"],
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
        max_age=3600,
    )
    logger.info(
        "[CORS] Configuration restrictive activée",
        extra={"origins": origins, "credentials": True}
    )


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting par IP et par tenant.
    Protection contre les abus et DoS.
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 100,
        requests_per_minute_per_tenant: int = 500,
        burst_multiplier: float = 1.5,
        excluded_paths: set[str] | None = None
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_minute_per_tenant = requests_per_minute_per_tenant
        self.burst_limit = int(requests_per_minute * burst_multiplier)

        # Stockage des compteurs (en mémoire - utiliser Redis en production distribuée)
        self._ip_requests: dict[str, list] = defaultdict(list)
        self._tenant_requests: dict[str, list] = defaultdict(list)

        # Paths exclus du rate limiting
        self.excluded_paths = excluded_paths or {
            "/health",
            "/health/live",
            "/health/ready",
            "/metrics",
        }

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip paths exclus
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Identification
        client_ip = self._get_client_ip(request)
        tenant_id = request.headers.get("X-Tenant-ID", "anonymous")

        # Nettoyage des anciennes entrées (> 1 minute)
        current_time = time.time()
        self._cleanup_old_requests(client_ip, tenant_id, current_time)

        # Vérification limite par IP
        ip_count = len(self._ip_requests[client_ip])
        if ip_count >= self.burst_limit:
            logger.warning(
                "[RATE_LIMIT] IP rate limit dépassé — requête bloquée",
                extra={
                    "client_ip": client_ip,
                    "tenant_id": tenant_id,
                    "path": request.url.path,
                    "ip_count": ip_count,
                    "burst_limit": self.burst_limit,
                    "consequence": "429_response"
                }
            )
            return self._rate_limit_response(
                request, "IP rate limit exceeded", self.requests_per_minute
            )

        # Vérification limite par tenant
        tenant_count = len(self._tenant_requests[tenant_id])
        if tenant_count >= self.requests_per_minute_per_tenant:
            logger.warning(
                "[RATE_LIMIT] Tenant rate limit dépassé — requête bloquée",
                extra={
                    "client_ip": client_ip,
                    "tenant_id": tenant_id,
                    "path": request.url.path,
                    "tenant_count": tenant_count,
                    "tenant_limit": self.requests_per_minute_per_tenant,
                    "consequence": "429_response"
                }
            )
            return self._rate_limit_response(
                request, "Tenant rate limit exceeded", self.requests_per_minute_per_tenant
            )

        # Enregistrement de la requête
        self._ip_requests[client_ip].append(current_time)
        self._tenant_requests[tenant_id].append(current_time)

        # Exécution de la requête
        response = await call_next(request)

        # Ajout des headers rate limit
        remaining = self.requests_per_minute - ip_count - 1
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(current_time) + 60)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extrait l'IP client, en tenant compte des proxies."""
        # X-Forwarded-For pour les proxies/load balancers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # X-Real-IP (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # IP directe
        if request.client:
            return request.client.host

        return "unknown"

    def _cleanup_old_requests(
        self, client_ip: str, tenant_id: str, current_time: float
    ):
        """Supprime les requêtes de plus d'une minute."""
        cutoff = current_time - 60

        self._ip_requests[client_ip] = [
            t for t in self._ip_requests[client_ip] if t > cutoff
        ]
        self._tenant_requests[tenant_id] = [
            t for t in self._tenant_requests[tenant_id] if t > cutoff
        ]

    def _rate_limit_response(
        self, request: Request, message: str, limit: int
    ) -> Response:
        """Retourne une réponse 429 Too Many Requests de manière SAFE."""
        response = build_error_response(
            status_code=429,
            error_type=ErrorType.RATE_LIMIT,
            message=message,
            html_path="frontend/errors/429.html",
            extra_data={"limit": limit}
        )
        # Ajouter les headers spécifiques au rate limiting
        response.headers["Retry-After"] = "60"
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = "0"
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        return response


# ============================================================================
# SECURITY HEADERS
# ============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Ajoute les headers de sécurité ÉLITE recommandés OWASP.
    Protection contre XSS, clickjacking, MIME sniffing, etc.
    HSTS activé automatiquement en production.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        settings = get_settings()
        response = await call_next(request)

        # Content Security Policy RENFORCÉ — PRODUCTION STRICTE
        # Aucun unsafe-inline, aucun unsafe-eval
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "upgrade-insecure-requests"
        )

        # Prevent XSS
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (remplace Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=(), interest-cohort=()"
        )

        # HSTS (Strict Transport Security) - PRODUCTION
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Cache control pour TOUTES les API
        if not request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # Header pour identifier le serveur (masqué)
        response.headers["Server"] = "AZALS"

        return response


# ============================================================================
# REQUEST VALIDATION
# ============================================================================

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Validation des requêtes entrantes.
    Protection contre les payloads malveillants.
    """

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB max
    ALLOWED_CONTENT_TYPES = {
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data",
    }

    async def dispatch(self, request: Request, call_next: Callable):
        # Vérification taille du body
        content_length = request.headers.get("Content-Length")
        if content_length:
            try:
                if int(content_length) > self.MAX_CONTENT_LENGTH:
                    return build_error_response(
                        status_code=413,
                        error_type=ErrorType.VALIDATION,
                        message=f"Request body too large. Max: {self.MAX_CONTENT_LENGTH} bytes",
                        html_path="frontend/errors/413.html"
                    )
            except ValueError as e:
                logger.warning(
                    "[SECURITY_MW] Content-Length invalide, vérification taille ignorée",
                    extra={"content_length": content_length, "error": str(e)[:200], "consequence": "size_check_skipped"}
                )

        # Vérification Content-Type pour les requêtes avec body
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("Content-Type", "")
            base_content_type = content_type.split(";")[0].strip().lower()

            if base_content_type and base_content_type not in self.ALLOWED_CONTENT_TYPES:
                # Autoriser si pas de body ou body vide
                if content_length and int(content_length) > 0:
                    return build_error_response(
                        status_code=415,
                        error_type=ErrorType.VALIDATION,
                        message=f"Unsupported content type: {base_content_type}",
                        html_path="frontend/errors/415.html"
                    )

        return await call_next(request)


# ============================================================================
# IP BLOCKLIST (Protection DDoS basique)
# ============================================================================

class IPBlocklistMiddleware(BaseHTTPMiddleware):
    """
    Middleware de blocage d'IPs malveillantes.
    Configurable via fichier ou API admin.
    """

    def __init__(self, app, blocked_ips: set[str] | None = None):
        super().__init__(app)
        self.blocked_ips: set[str] = blocked_ips or set()
        self._violation_counts: dict[str, int] = defaultdict(int)
        self._auto_block_threshold = 10  # Bloque après 10 violations

    async def dispatch(self, request: Request, call_next: Callable):
        client_ip = self._get_client_ip(request)

        # Vérifier si IP bloquée
        if client_ip in self.blocked_ips:
            return build_error_response(
                status_code=403,
                error_type=ErrorType.AUTHORIZATION,
                message="Access denied",
                html_path="frontend/errors/403.html"
            )

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extrait l'IP client."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def block_ip(self, ip: str) -> None:
        """Ajoute une IP à la blocklist."""
        self.blocked_ips.add(ip)

    def unblock_ip(self, ip: str) -> None:
        """Retire une IP de la blocklist."""
        self.blocked_ips.discard(ip)

    def record_violation(self, ip: str) -> bool:
        """
        Enregistre une violation et bloque automatiquement si seuil atteint.
        Returns True si l'IP a été bloquée.
        """
        self._violation_counts[ip] += 1
        if self._violation_counts[ip] >= self._auto_block_threshold:
            self.block_ip(ip)
            logger.warning(
                "[IP_BLOCKLIST] IP auto-bloquée — seuil de violations atteint",
                extra={
                    "blocked_ip": ip,
                    "violation_count": self._violation_counts[ip],
                    "threshold": self._auto_block_threshold,
                    "consequence": "ip_permanently_blocked"
                }
            )
            return True
        return False


# ============================================================================
# SETUP COMPLET SÉCURITÉ
# ============================================================================

def setup_security(
    app: FastAPI,
    enable_rate_limit: bool = True,
    enable_security_headers: bool = True,
    enable_request_validation: bool = True,
    rate_limit_per_minute: int = 100
) -> None:
    """
    Configure tous les middlewares de sécurité.

    Args:
        app: Application FastAPI
        enable_rate_limit: Activer le rate limiting
        enable_security_headers: Activer les headers de sécurité
        enable_request_validation: Activer la validation des requêtes
        rate_limit_per_minute: Limite de requêtes par minute par IP
    """
    # CORS (doit être ajouté en premier pour les preflight)
    setup_cors(app)

    # Security Headers
    if enable_security_headers:
        app.add_middleware(SecurityHeadersMiddleware)

    # Request Validation
    if enable_request_validation:
        app.add_middleware(RequestValidationMiddleware)

    # Rate Limiting
    if enable_rate_limit:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=rate_limit_per_minute
        )
