"""
AZALS - Security Middleware Production
======================================
CORS, Rate Limiting, Security Headers, Request Validation.
"""

import time
from collections import defaultdict
from typing import Callable, Dict, Optional, Set
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import get_settings


# ============================================================================
# CONFIGURATION CORS
# ============================================================================

def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS pour l'application.
    En production, utilisez une liste d'origins autorisées.
    """
    settings = get_settings()

    # Parse origins depuis config (séparées par virgules)
    if settings.cors_origins:
        origins = [o.strip() for o in settings.cors_origins.split(",")]
    else:
        # Defaut developpement - A REMPLACER en production!
        origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:4173",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:4173",
            "http://127.0.0.1:8080",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Tenant-ID",
            "X-Request-ID",
            "X-Trace-ID",
        ],
        expose_headers=[
            "X-Request-ID",
            "X-Trace-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
        max_age=3600,  # Cache preflight pendant 1 heure
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
        excluded_paths: Optional[Set[str]] = None
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_minute_per_tenant = requests_per_minute_per_tenant
        self.burst_limit = int(requests_per_minute * burst_multiplier)

        # Stockage des compteurs (en mémoire - utiliser Redis en production distribuée)
        self._ip_requests: Dict[str, list] = defaultdict(list)
        self._tenant_requests: Dict[str, list] = defaultdict(list)

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
            return self._rate_limit_response(
                request, "IP rate limit exceeded", self.requests_per_minute
            )

        # Vérification limite par tenant
        tenant_count = len(self._tenant_requests[tenant_id])
        if tenant_count >= self.requests_per_minute_per_tenant:
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
        """Retourne une réponse 429 Too Many Requests."""
        return Response(
            content=f'{{"detail": "{message}", "limit": {limit}}}',
            status_code=429,
            media_type="application/json",
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + 60),
            }
        )


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

        # Content Security Policy RENFORCÉ
        # Note: unsafe-inline nécessaire pour Swagger UI en dev, retiré en prod
        if settings.is_production:
            # CSP strict en production (pas d'inline)
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
        else:
            # CSP permissif en dev (pour Swagger UI)
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
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

        # HSTS (Strict Transport Security) - ACTIVÉ en production
        if settings.is_production:
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
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request body too large. Max: {self.MAX_CONTENT_LENGTH} bytes"
                    )
            except ValueError:
                pass

        # Vérification Content-Type pour les requêtes avec body
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("Content-Type", "")
            base_content_type = content_type.split(";")[0].strip().lower()

            if base_content_type and base_content_type not in self.ALLOWED_CONTENT_TYPES:
                # Autoriser si pas de body ou body vide
                if content_length and int(content_length) > 0:
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail=f"Unsupported content type: {base_content_type}"
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

    def __init__(self, app, blocked_ips: Optional[Set[str]] = None):
        super().__init__(app)
        self.blocked_ips: Set[str] = blocked_ips or set()
        self._violation_counts: Dict[str, int] = defaultdict(int)
        self._auto_block_threshold = 10  # Bloque après 10 violations

    async def dispatch(self, request: Request, call_next: Callable):
        client_ip = self._get_client_ip(request)

        # Vérifier si IP bloquée
        if client_ip in self.blocked_ips:
            return Response(
                content='{"detail": "Access denied"}',
                status_code=403,
                media_type="application/json"
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
