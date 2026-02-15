"""
AZALS - Security Middleware Production
======================================
CORS, Rate Limiting, Security Headers, Request Validation.

SÉCURITÉ: Utilise build_error_response du module Guardian pour garantir
          qu'aucune erreur ne provoque de crash, même sans fichiers HTML.

ARCHITECTURE:
- Rate limiting distribué via Redis (avec fallback mémoire)
- Headers de sécurité OWASP
- Validation des requêtes entrantes
- Blocklist IP avec auto-block
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
from app.core.rate_limit import (
    RateLimiter,
    check_ip_rate_limit,
    check_tenant_rate_limit,
    check_endpoint_rate_limit,
)

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

def _is_ip_address(host: str) -> bool:
    """Vérifie si une chaîne est une adresse IP (IPv4 ou IPv6)."""
    import re
    # Pattern IPv4
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    # Pattern IPv6 simplifié (couvre les cas courants)
    ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$'

    return bool(re.match(ipv4_pattern, host) or re.match(ipv6_pattern, host))


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS pour l'application.
    PRODUCTION: Utilise CORS_ORIGINS depuis la configuration (OBLIGATOIRE).
    DÉVELOPPEMENT: Autorise toutes les origines.

    SÉCURITÉ:
    - Interdit les wildcards (*)
    - Interdit localhost/127.0.0.1
    - Interdit les adresses IP (utiliser des noms de domaine)
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

    # Validation stricte de chaque origine
    for origin in origins:
        # Validation: pas de localhost
        if "localhost" in origin.lower() or "127.0.0.1" in origin:
            raise ValueError(f"localhost interdit dans CORS_ORIGINS en production: {origin}")

        # SÉCURITÉ: Validation - pas d'adresses IP (seulement des noms de domaine)
        try:
            from urllib.parse import urlparse
            parsed = urlparse(origin)
            host = parsed.hostname or ""

            if _is_ip_address(host):
                raise ValueError(
                    f"SÉCURITÉ: Adresse IP interdite dans CORS_ORIGINS: {origin}. "
                    f"Utilisez un nom de domaine (ex: https://app.example.com)"
                )

            # Validation: protocole HTTPS obligatoire
            if parsed.scheme != "https":
                raise ValueError(
                    f"SÉCURITÉ: Protocole HTTPS obligatoire dans CORS_ORIGINS: {origin}. "
                    f"Remplacez {parsed.scheme}:// par https://"
                )
        except ValueError:
            raise
        except Exception as e:
            logger.warning(f"[CORS] Impossible de parser l'origine {origin}: {e}")

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

    ARCHITECTURE:
    - Utilise Redis via RateLimiter pour rate limiting distribué
    - Fallback automatique en mémoire si Redis indisponible
    - Double vérification: limite par IP + limite par tenant
    - Rate limiting spécifique pour endpoints sensibles (/auth/login)
    """

    # Endpoints sensibles avec limites réduites (brute-force protection)
    SENSITIVE_ENDPOINTS = {
        "/auth/login": 10,      # 10 tentatives/minute
        "/auth/register": 5,    # 5 inscriptions/minute
        "/auth/reset-password": 5,
        "/api/v2/auth/login": 10,
        "/api/v2/auth/register": 5,
    }

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

        # Paths exclus du rate limiting
        self.excluded_paths = excluded_paths or {
            "/health",
            "/health/live",
            "/health/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

        # Log du backend utilisé
        rate_limiter = RateLimiter.get_instance()
        logger.info(
            "[RATE_LIMIT] Middleware initialisé",
            extra={
                "backend": "redis" if rate_limiter.is_redis_available() else "memory",
                "ip_limit": requests_per_minute,
                "tenant_limit": requests_per_minute_per_tenant,
                "burst_limit": self.burst_limit
            }
        )

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip paths exclus
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Identification
        client_ip = self._get_client_ip(request)
        tenant_id = request.headers.get("X-Tenant-ID", "anonymous")
        path = request.url.path

        # 1. Vérification endpoints sensibles (brute-force protection)
        if path in self.SENSITIVE_ENDPOINTS:
            endpoint_limit = self.SENSITIVE_ENDPOINTS[path]
            endpoint_result = check_endpoint_rate_limit(
                ip=client_ip,
                endpoint=path,
                limit=endpoint_limit,
                window=60
            )
            if not endpoint_result.allowed:
                logger.warning(
                    "[RATE_LIMIT] Endpoint sensible rate limit dépassé",
                    extra={
                        "client_ip": client_ip,
                        "tenant_id": tenant_id,
                        "path": path,
                        "current": endpoint_result.current_count,
                        "limit": endpoint_limit,
                        "consequence": "429_response"
                    }
                )
                return self._rate_limit_response(
                    request,
                    f"Rate limit exceeded for {path}",
                    endpoint_limit,
                    endpoint_result.retry_after
                )

        # 2. Vérification limite par IP
        ip_result = check_ip_rate_limit(
            ip=client_ip,
            limit=self.burst_limit,
            window=60
        )
        if not ip_result.allowed:
            logger.warning(
                "[RATE_LIMIT] IP rate limit dépassé — requête bloquée",
                extra={
                    "client_ip": client_ip,
                    "tenant_id": tenant_id,
                    "path": path,
                    "current": ip_result.current_count,
                    "burst_limit": self.burst_limit,
                    "consequence": "429_response"
                }
            )
            return self._rate_limit_response(
                request,
                "IP rate limit exceeded",
                self.requests_per_minute,
                ip_result.retry_after
            )

        # 3. Vérification limite par tenant
        tenant_result = check_tenant_rate_limit(
            tenant_id=tenant_id,
            limit=self.requests_per_minute_per_tenant,
            window=60
        )
        if not tenant_result.allowed:
            logger.warning(
                "[RATE_LIMIT] Tenant rate limit dépassé — requête bloquée",
                extra={
                    "client_ip": client_ip,
                    "tenant_id": tenant_id,
                    "path": path,
                    "current": tenant_result.current_count,
                    "tenant_limit": self.requests_per_minute_per_tenant,
                    "consequence": "429_response"
                }
            )
            return self._rate_limit_response(
                request,
                "Tenant rate limit exceeded",
                self.requests_per_minute_per_tenant,
                tenant_result.retry_after
            )

        # Exécution de la requête
        response = await call_next(request)

        # Ajout des headers rate limit (basés sur IP)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(ip_result.remaining)
        response.headers["X-RateLimit-Reset"] = str(ip_result.reset_at)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Extrait l'IP client de manière SÉCURISÉE.

        SÉCURITÉ: Les headers X-Forwarded-For et X-Real-IP peuvent être forgés
        par des attaquants. On ne fait confiance à ces headers QUE si:
        1. TRUSTED_PROXIES est configuré
        2. L'IP directe du client est dans la liste des proxies de confiance

        Configuration via variable d'environnement:
        TRUSTED_PROXIES=10.0.0.0/8,172.16.0.0/12,192.168.0.0/16
        """
        import ipaddress
        import os

        # IP directe (toujours fiable)
        direct_ip = request.client.host if request.client else None

        if not direct_ip:
            return "unknown"

        # Récupérer les proxies de confiance depuis la configuration
        trusted_proxies_str = os.getenv("TRUSTED_PROXIES", "")

        # Si aucun proxy de confiance configuré, utiliser l'IP directe uniquement
        if not trusted_proxies_str:
            # En production sans config, on ne fait PAS confiance aux headers proxy
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                logger.warning(
                    "[SECURITY] X-Forwarded-For ignoré - TRUSTED_PROXIES non configuré",
                    extra={
                        "direct_ip": direct_ip,
                        "x_forwarded_for": forwarded[:100],
                        "consequence": "using_direct_ip"
                    }
                )
            return direct_ip

        # Parser les réseaux de confiance
        try:
            trusted_networks = []
            for cidr in trusted_proxies_str.split(","):
                cidr = cidr.strip()
                if cidr:
                    trusted_networks.append(ipaddress.ip_network(cidr, strict=False))
        except ValueError as e:
            logger.error(
                "[SECURITY] TRUSTED_PROXIES invalide: %s",
                str(e),
                extra={"trusted_proxies": trusted_proxies_str}
            )
            return direct_ip

        # Vérifier si l'IP directe vient d'un proxy de confiance
        try:
            direct_ip_obj = ipaddress.ip_address(direct_ip)
            is_trusted_proxy = any(
                direct_ip_obj in network for network in trusted_networks
            )
        except ValueError:
            # IP invalide
            return direct_ip

        if not is_trusted_proxy:
            # L'IP directe n'est PAS un proxy de confiance - ignorer les headers
            return direct_ip

        # L'IP vient d'un proxy de confiance - on peut lire X-Forwarded-For
        # SÉCURITÉ: Prendre la DERNIÈRE IP non-proxy dans la chaîne
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ips = [ip.strip() for ip in forwarded.split(",")]
            # Parcourir de droite à gauche pour trouver la première IP non-proxy
            for ip in reversed(ips):
                try:
                    ip_obj = ipaddress.ip_address(ip)
                    if not any(ip_obj in network for network in trusted_networks):
                        return ip
                except ValueError:
                    continue
            # Toutes les IPs sont des proxies - prendre la première
            return ips[0] if ips else direct_ip

        # X-Real-IP (nginx) - seulement si venant d'un proxy de confiance
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        return direct_ip

    def _rate_limit_response(
        self, request: Request, message: str, limit: int, retry_after: int = 60
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
        response.headers["Retry-After"] = str(retry_after)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = "0"
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + retry_after)
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
