"""
AZALS - Middleware Multi-Tenant
Validation stricte du header X-Tenant-ID pour TOUTES les requêtes
Exception : /health (monitoring public)

SÉCURITÉ: Utilise build_error_response du module Guardian pour garantir
          qu'aucune erreur ne provoque de crash, même sans fichiers HTML.
"""


from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Import de la fonction SAFE de gestion des erreurs
# Note: Utilise error_response.py au lieu de middleware.py pour éviter les imports circulaires
from app.modules.guardian.error_response import (
    ErrorType,
    build_error_response,
)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware de validation du tenant.
    Refuse toute requête sans X-Tenant-ID valide (hors endpoints publics).
    Injecte le tenant_id dans request.state pour usage par les endpoints.
    """

    # Endpoints publics exclus de la validation tenant
    # Note: /auth/login et /auth/bootstrap n'ont pas besoin de validation tenant
    # - login: recherche l'utilisateur par email et retourne son tenant_id
    # - bootstrap: crée le premier tenant et admin
    # - health/*: monitoring et Kubernetes probes
    # - metrics: Prometheus scraping
    PUBLIC_PATHS = {
        # Health & Monitoring
        "/health", "/health/live", "/health/ready", "/health/startup", "/health/db", "/health/redis",
        "/metrics", "/metrics/json",
        # Documentation
        "/docs", "/redoc", "/openapi.json",
        # Frontend pages
        "/", "/dashboard", "/treasury", "/static", "/favicon.ico", "/admin", "/login",
        # Auth routes (legacy)
        "/auth/login", "/auth/bootstrap", "/auth/register", "/auth/2fa/verify-login",
        # Auth routes (v1)
        "/v1/auth/login", "/v1/auth/bootstrap", "/v1/auth/register", "/v1/auth/2fa/verify-login",
        "/v1/auth/refresh", "/v1/auth/logout", "/v1/auth",
        # Audit routes (public for UI events without auth)
        "/v1/audit", "/v1/audit/ui-events",
        # Signup et webhooks (public - nouvelles inscriptions et Stripe)
        "/signup", "/webhooks",
        # AI Orchestration (public status + Theo interface)
        "/api/v1/ai/status", "/v1/ai/status",
        "/api/v1/ai/theo", "/v1/ai/theo",
        "/api/v1/ai/auth", "/v1/ai/auth",
        # Website Tracking (public for analytics without auth)
        "/api/v2/website/track-visit",
        "/api/v2/website/leads",
        "/api/v2/website/demo-requests",
        "/api/v2/website/contact",
        "/api/v2/website/analytics/summary",
        # Trial Registration (public for self-service signup)
        "/api/v2/public/trial",
    }

    async def dispatch(self, request: Request, call_next):
        """
        Intercepte chaque requete HTTP.
        Valide la presence et le format du tenant_id.
        """
        # OPTIONS preflight requests: bypass validation (CORS handles these)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Endpoints publics : bypass validation mais injecter tenant_id si present
        is_public_path = any(request.url.path == path or request.url.path.startswith(path + "/")
                            for path in self.PUBLIC_PATHS)

        # Extraction du header X-Tenant-ID
        tenant_id: str | None = request.headers.get("X-Tenant-ID")

        if is_public_path:
            # Pour les paths publics, injecter tenant_id si présent et valide
            if tenant_id and self._is_valid_tenant_id(tenant_id):
                request.state.tenant_id = tenant_id
            return await call_next(request)

        # Routes protégées : validation obligatoire
        if not tenant_id:
            return build_error_response(
                status_code=401,
                error_type=ErrorType.AUTHENTICATION,
                message="Missing X-Tenant-ID header. Multi-tenant isolation required.",
                html_path="frontend/errors/401.html"
            )

        # Validation : format du tenant_id (alphanumerique + tirets)
        if not self._is_valid_tenant_id(tenant_id):
            return build_error_response(
                status_code=400,
                error_type=ErrorType.VALIDATION,
                message="Invalid X-Tenant-ID format. Alphanumeric and hyphens only.",
                html_path="frontend/errors/400.html"
            )

        # Injection du tenant_id dans request.state
        request.state.tenant_id = tenant_id

        # Poursuite de la requête
        response = await call_next(request)
        return response

    @staticmethod
    def _is_valid_tenant_id(tenant_id: str) -> bool:
        """
        Valide le format du tenant_id.
        Accepte : lettres, chiffres, tirets, underscores
        Longueur : 1-255 caractères
        """
        if not tenant_id or len(tenant_id) > 255:
            return False

        # Validation alphanumérique + tirets + underscores uniquement
        return all(c.isalnum() or c in ['-', '_'] for c in tenant_id)
