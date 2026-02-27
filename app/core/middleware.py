"""
AZALS - Middleware Multi-Tenant
Validation stricte du header X-Tenant-ID pour TOUTES les requêtes
Exception : /health (monitoring public)

SÉCURITÉ P0: Utilise build_error_response du module Guardian pour garantir
             qu'aucune erreur ne provoque de crash, même sans fichiers HTML.

SÉCURITÉ P2: Support RLS PostgreSQL automatique via contexte de session.
"""

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Import de la fonction SAFE de gestion des erreurs
# Note: Utilise error_response.py au lieu de middleware.py pour éviter les imports circulaires
from app.modules.guardian.error_response import (
    ErrorType,
    build_error_response,
)

logger = logging.getLogger(__name__)


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

    # P1 SÉCURITÉ: Liste des tenant_ids réservés/interdits
    # Ces noms pourraient entrer en conflit avec des routes ou fonctionnalités internes
    RESERVED_TENANT_IDS = {
        # Noms système
        "admin", "administrator", "root", "system", "api", "internal",
        "platform", "superadmin", "super-admin", "super_admin",
        # Noms potentiellement confus
        "null", "none", "undefined", "void", "test", "demo",
        "default", "public", "private", "global", "local",
        # Préfixes internes
        "_internal", "_system", "_admin", "_platform", "_test",
        "__internal__", "__system__", "__admin__",
        # Routes réservées
        "health", "metrics", "docs", "api", "auth", "v1", "v2", "v3",
        "static", "assets", "webhooks", "ws", "websocket",
    }

    @staticmethod
    def _is_valid_tenant_id(tenant_id: str) -> bool:
        """
        Valide le format du tenant_id.
        Accepte : lettres, chiffres, tirets, underscores
        Longueur : 3-255 caractères (P1 SÉCURITÉ: min 3 pour éviter IDs triviaux)
        """
        # P1 SÉCURITÉ: Longueur minimale 3 pour éviter tenant_ids comme "a", "1", etc.
        if not tenant_id or len(tenant_id) < 3 or len(tenant_id) > 255:
            return False

        # P1 SÉCURITÉ: Vérifier que ce n'est pas un nom réservé
        if tenant_id.lower() in TenantMiddleware.RESERVED_TENANT_IDS:
            return False

        # P1 SÉCURITÉ: Interdire les tenant_ids commençant par _ ou - (réservés internes)
        if tenant_id.startswith('_') or tenant_id.startswith('-'):
            return False

        # Validation alphanumérique + tirets + underscores uniquement
        return all(c.isalnum() or c in ['-', '_'] for c in tenant_id)


# =============================================================================
# RLS MIDDLEWARE (P2 SÉCURITÉ)
# =============================================================================

class RLSMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour activer automatiquement le Row-Level Security PostgreSQL.

    P1 SÉCURITÉ: Ce middleware définit la variable de session PostgreSQL
    `app.current_tenant_id` pour que les politiques RLS filtrent automatiquement
    les données par tenant.

    IMPORTANT: Requiert que les politiques RLS soient créées en base de données.
    Voir: migrations/rls_policies.sql

    NOTE: Le middleware prépare le contexte, mais l'application effective du RLS
    se fait via la dépendance get_db_with_rls_auto() qui lit request.state.tenant_id.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Active le contexte RLS pour chaque requête avec tenant_id.
        """
        tenant_id = getattr(request.state, 'tenant_id', None)

        if tenant_id:
            # Marquer que RLS doit être activé
            request.state.rls_enabled = True
            logger.debug("[RLS] Context prepared for tenant: %s", tenant_id)

        response = await call_next(request)
        return response


def get_rls_tenant_id(request: Request) -> str | None:
    """
    Récupère le tenant_id depuis request.state pour application RLS.

    Usage dans les dépendances FastAPI:
        @router.get("/items")
        async def get_items(
            request: Request,
            db: Session = Depends(get_db)
        ):
            tenant_id = get_rls_tenant_id(request)
            if tenant_id:
                set_rls_context(db, tenant_id)
            ...
    """
    return getattr(request.state, 'tenant_id', None)


# =============================================================================
# RLS DATABASE DEPENDENCY (P1 SÉCURITÉ)
# =============================================================================

from typing import Generator
from sqlalchemy.orm import Session


def get_db_with_rls_auto(request: Request) -> Generator[Session, None, None]:
    """
    P1 SÉCURITÉ: Dépendance FastAPI qui applique automatiquement le contexte RLS.

    Cette dépendance:
    1. Crée une session de base de données
    2. Lit le tenant_id depuis request.state (injecté par TenantMiddleware)
    3. Exécute SET LOCAL app.current_tenant_id pour activer RLS PostgreSQL
    4. Retourne la session avec RLS actif

    Usage:
        @router.get("/items")
        async def get_items(
            db: Session = Depends(get_db_with_rls_auto)
        ):
            # Toutes les requêtes sont automatiquement filtrées par RLS
            return db.query(Item).all()

    NOTE: Requiert que les politiques RLS soient configurées en PostgreSQL.
    Voir: migrations/rls_policies.sql
    """
    from app.core.database import SessionLocal, set_rls_context

    db = SessionLocal()
    try:
        tenant_id = getattr(request.state, 'tenant_id', None)
        if tenant_id:
            set_rls_context(db, tenant_id)
            logger.debug("[RLS] PostgreSQL context set: tenant_id=%s", tenant_id)
        yield db
    finally:
        db.close()
