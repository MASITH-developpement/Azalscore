"""
CORE SaaS - Middleware d'Authentification Unifié
=================================================

Middleware qui utilise CORE.authenticate() pour authentifier les requêtes.

REMPLACE:
- app/core/auth_middleware.py (ancien middleware JWT)

WORKFLOW:
1. Extrait le token JWT de l'header Authorization
2. Extrait le tenant_id de request.state (injecté par TenantMiddleware)
3. Appelle CORE.authenticate(token, tenant_id) pour créer SaaSContext
4. Injecte SaaSContext dans request.state pour les endpoints

AVANTAGES:
- Point d'entrée unique pour l'authentification (CORE)
- Aucune duplication de logique
- Contexte immuable (SaaSContext) au lieu de User mutable
- Audit automatique
- Gestion d'erreurs unifiée
"""

import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import SessionLocal
from app.core.logging_config import get_logger
from app.core.saas_core import SaaSCore

logger = get_logger(__name__)


class CoreAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware d'authentification utilisant CORE SaaS.

    Parse le token JWT et crée un SaaSContext via CORE.authenticate().

    Ne bloque PAS les requêtes sans token - laisse les endpoints
    gérer l'autorisation via get_saas_context().
    """

    async def dispatch(self, request: Request, call_next):
        """
        Traite chaque requête.

        Si un token valide est présent:
        - Crée SaaSContext via CORE.authenticate()
        - Injecte dans request.state.saas_context

        Si pas de token ou token invalide:
        - Continue sans authentification
        - Les endpoints protégés rejetteront la requête via get_saas_context()
        """
        path = request.url.path

        # Ignorer les OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extraire le token de l'header Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # Pas de token - continuer sans authentification
            logger.debug(f"[CoreAuthMiddleware] No token for {path}")
            return await call_next(request)

        token = auth_header.split(" ", 1)[1]

        # Vérifier si tenant_id est disponible (injecté par TenantMiddleware)
        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            # Pas de tenant_id - impossible d'authentifier
            # (TenantMiddleware devrait avoir injecté tenant_id)
            logger.warning(f"[CoreAuthMiddleware] Missing tenant_id for {path}")
            return await call_next(request)

        # Extraire informations de requête pour audit trail
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "")
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # Authentifier via CORE
        db = SessionLocal()
        try:
            core = SaaSCore(db)

            result = core.authenticate(
                token=token,
                tenant_id=tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                correlation_id=correlation_id,
            )

            if result.success:
                # Authentification réussie - injecter SaaSContext
                saas_context = result.data
                request.state.saas_context = saas_context

                # Injection pour compatibilité avec ancien code
                request.state.user_id = saas_context.user_id
                request.state.role = saas_context.role

                logger.debug(
                    f"[CoreAuthMiddleware] Authenticated {saas_context.user_id} "
                    f"for tenant {tenant_id} (role: {saas_context.role.value})"
                )
            else:
                # Authentification échouée - continuer sans contexte
                logger.warning(
                    f"[CoreAuthMiddleware] Authentication failed for {path}: "
                    f"{result.error} ({result.error_code})"
                )

        except Exception as e:
            logger.error(f"[CoreAuthMiddleware] Error during authentication: {e}", exc_info=True)
        finally:
            db.close()

        return await call_next(request)
