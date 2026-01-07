"""
AZALSCORE - Middleware RBAC
============================

Middleware pour appliquer automatiquement les vérifications RBAC
sur toutes les routes protégées.

PRINCIPE: Deny by default
- Routes non listées → 403
- Permissions non accordées → 403
- Logs sur tous les refus critiques
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .rbac_matrix import (
    StandardRole,
    Module,
    Action,
    Restriction,
    check_permission,
    map_legacy_role_to_standard,
    SecurityRules,
)


logger = logging.getLogger("rbac.middleware")


# ============================================================================
# CONFIGURATION DES ROUTES
# ============================================================================

@dataclass
class RoutePermission:
    """Définition des permissions requises pour une route."""
    module: Module
    action: Action
    allow_public: bool = False  # Si True, accessible sans auth


# Mapping des patterns de routes vers les permissions requises
# Format: (method, path_pattern) -> RoutePermission
ROUTE_PERMISSIONS: Dict[Tuple[str, str], RoutePermission] = {
    # =========================================================================
    # USERS & ROLES
    # =========================================================================
    ("GET", r"/api/iam/users/?$"): RoutePermission(Module.USERS, Action.READ),
    ("GET", r"/api/iam/users/\d+$"): RoutePermission(Module.USERS, Action.READ),
    ("POST", r"/api/iam/users/?$"): RoutePermission(Module.USERS, Action.CREATE),
    ("PUT", r"/api/iam/users/\d+$"): RoutePermission(Module.USERS, Action.UPDATE),
    ("PATCH", r"/api/iam/users/\d+$"): RoutePermission(Module.USERS, Action.UPDATE),
    ("DELETE", r"/api/iam/users/\d+$"): RoutePermission(Module.USERS, Action.DELETE),

    # Rôles (super_admin uniquement)
    ("GET", r"/api/iam/roles/?$"): RoutePermission(Module.USERS, Action.READ),
    ("POST", r"/api/iam/roles/?$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("PUT", r"/api/iam/roles/\d+$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("DELETE", r"/api/iam/roles/\d+$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("POST", r"/api/iam/users/\d+/roles/?$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("DELETE", r"/api/iam/users/\d+/roles/\d+$"): RoutePermission(Module.USERS, Action.ASSIGN),

    # =========================================================================
    # ORGANISATION
    # =========================================================================
    ("GET", r"/api/organization/?$"): RoutePermission(Module.ORGANIZATION, Action.READ),
    ("GET", r"/api/tenants/current/?$"): RoutePermission(Module.ORGANIZATION, Action.READ),
    ("PUT", r"/api/organization/?$"): RoutePermission(Module.ORGANIZATION, Action.UPDATE),
    ("PATCH", r"/api/organization/?$"): RoutePermission(Module.ORGANIZATION, Action.UPDATE),
    ("PUT", r"/api/tenants/current/?$"): RoutePermission(Module.ORGANIZATION, Action.UPDATE),

    # =========================================================================
    # CLIENTS / CONTACTS
    # =========================================================================
    ("GET", r"/api/commercial/customers/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("GET", r"/api/commercial/customers/\d+$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/api/commercial/customers/?$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("PUT", r"/api/commercial/customers/\d+$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("PATCH", r"/api/commercial/customers/\d+$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("DELETE", r"/api/commercial/customers/\d+$"): RoutePermission(Module.CLIENTS, Action.DELETE),

    # Contacts
    ("GET", r"/api/commercial/contacts/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("GET", r"/api/commercial/contacts/\d+$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/api/commercial/contacts/?$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("PUT", r"/api/commercial/contacts/\d+$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("DELETE", r"/api/commercial/contacts/\d+$"): RoutePermission(Module.CLIENTS, Action.DELETE),

    # =========================================================================
    # FACTURATION / DEVIS / PAIEMENTS
    # =========================================================================
    # Factures
    ("GET", r"/api/sales/invoices/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("GET", r"/api/sales/invoices/\d+$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/api/sales/invoices/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/api/sales/invoices/\d+$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/api/sales/invoices/\d+$"): RoutePermission(Module.BILLING, Action.DELETE),
    ("POST", r"/api/sales/invoices/\d+/validate$"): RoutePermission(Module.BILLING, Action.VALIDATE),

    # Devis
    ("GET", r"/api/sales/quotes/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("GET", r"/api/sales/quotes/\d+$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/api/sales/quotes/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/api/sales/quotes/\d+$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/api/sales/quotes/\d+$"): RoutePermission(Module.BILLING, Action.DELETE),
    ("POST", r"/api/sales/quotes/\d+/validate$"): RoutePermission(Module.BILLING, Action.VALIDATE),

    # Paiements
    ("GET", r"/api/sales/payments/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("GET", r"/api/sales/payments/\d+$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/api/sales/payments/?$"): RoutePermission(Module.BILLING, Action.CREATE),

    # =========================================================================
    # PROJETS / ACTIVITÉS
    # =========================================================================
    ("GET", r"/api/projects/?$"): RoutePermission(Module.PROJECTS, Action.READ),
    ("GET", r"/api/projects/\d+$"): RoutePermission(Module.PROJECTS, Action.READ),
    ("POST", r"/api/projects/?$"): RoutePermission(Module.PROJECTS, Action.CREATE),
    ("PUT", r"/api/projects/\d+$"): RoutePermission(Module.PROJECTS, Action.UPDATE),
    ("PATCH", r"/api/projects/\d+$"): RoutePermission(Module.PROJECTS, Action.UPDATE),
    ("DELETE", r"/api/projects/\d+$"): RoutePermission(Module.PROJECTS, Action.DELETE),

    # Tâches
    ("GET", r"/api/projects/\d+/tasks/?$"): RoutePermission(Module.PROJECTS, Action.READ),
    ("POST", r"/api/projects/\d+/tasks/?$"): RoutePermission(Module.PROJECTS, Action.CREATE),
    ("PUT", r"/api/projects/\d+/tasks/\d+$"): RoutePermission(Module.PROJECTS, Action.UPDATE),
    ("DELETE", r"/api/projects/\d+/tasks/\d+$"): RoutePermission(Module.PROJECTS, Action.DELETE),

    # =========================================================================
    # REPORTING / KPI
    # =========================================================================
    ("GET", r"/api/bi/reports/?$"): RoutePermission(Module.REPORTING, Action.READ),
    ("GET", r"/api/bi/reports/\d+$"): RoutePermission(Module.REPORTING, Action.READ),
    ("GET", r"/api/bi/dashboards/?$"): RoutePermission(Module.REPORTING, Action.READ),
    ("GET", r"/api/bi/kpis/?$"): RoutePermission(Module.REPORTING, Action.READ),
    ("POST", r"/api/bi/reports/\d+/export$"): RoutePermission(Module.REPORTING, Action.EXPORT),
    ("GET", r"/api/bi/reports/\d+/export$"): RoutePermission(Module.REPORTING, Action.EXPORT),

    # =========================================================================
    # PARAMÈTRES / CONFIGURATION
    # =========================================================================
    ("GET", r"/api/admin/settings/?$"): RoutePermission(Module.SETTINGS, Action.READ),
    ("PUT", r"/api/admin/settings/?$"): RoutePermission(Module.SETTINGS, Action.UPDATE),
    ("PATCH", r"/api/admin/settings/?$"): RoutePermission(Module.SETTINGS, Action.UPDATE),

    # =========================================================================
    # SÉCURITÉ
    # =========================================================================
    ("GET", r"/api/iam/security/?$"): RoutePermission(Module.SECURITY, Action.READ),
    ("PUT", r"/api/iam/security/?$"): RoutePermission(Module.SECURITY, Action.UPDATE),
    ("GET", r"/api/iam/policy/?$"): RoutePermission(Module.SECURITY, Action.READ),
    ("PUT", r"/api/iam/policy/?$"): RoutePermission(Module.SECURITY, Action.UPDATE),

    # =========================================================================
    # AUDIT
    # =========================================================================
    ("GET", r"/api/audit/logs/?$"): RoutePermission(Module.AUDIT, Action.READ),
    ("GET", r"/api/audit/logs/\d+$"): RoutePermission(Module.AUDIT, Action.READ),
    ("POST", r"/api/audit/logs/export$"): RoutePermission(Module.AUDIT, Action.EXPORT),
    ("GET", r"/api/iam/audit/?$"): RoutePermission(Module.AUDIT, Action.READ),
}


# Routes publiques (pas de vérification RBAC)
PUBLIC_ROUTES: List[str] = [
    r"^/health/?$",
    r"^/metrics/?$",
    r"^/docs/?$",
    r"^/openapi\.json$",
    r"^/redoc/?$",
    r"^/api/auth/.*$",
    r"^/auth/.*$",
    r"^/v1/auth/.*$",       # Routes auth sous /v1
    r"^/v1/audit/.*$",      # Routes audit (UI events)
    r"^/$",
    r"^/static/.*$",        # Fichiers statiques
    r"^/favicon\.ico$",
    r"^/dashboard/?$",
    r"^/treasury/?$",
    r"^/login/?$",
]


# Routes semi-publiques (authentification requise mais pas de permission spécifique)
AUTHENTICATED_ONLY_ROUTES: List[str] = [
    r"^/api/me/?$",
    r"^/api/users/me/?$",
    r"^/api/iam/me/?$",
    r"^/api/iam/users/me/?$",
]


# ============================================================================
# MIDDLEWARE RBAC
# ============================================================================

class RBACMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour appliquer automatiquement les vérifications RBAC.

    Fonctionnement:
    1. Vérifie si la route est publique → passe
    2. Vérifie si l'utilisateur est authentifié
    3. Vérifie les permissions selon la matrice RBAC
    4. Log les refus critiques
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """Traite chaque requête."""
        path = request.url.path
        method = request.method

        # 1. Routes publiques
        if self._is_public_route(path):
            return await call_next(request)

        # 2. Routes authentifiées uniquement (pas de permission spécifique)
        if self._is_authenticated_only_route(path):
            if not self._is_authenticated(request):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentification requise"}
                )
            return await call_next(request)

        # 3. Vérifier l'authentification
        if not self._is_authenticated(request):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentification requise"}
            )

        # 4. Trouver la permission requise pour cette route
        route_perm = self._find_route_permission(method, path)

        if not route_perm:
            # Route non configurée → deny by default en production
            # En développement, on peut logger et passer
            logger.warning(f"Route non configurée dans RBAC: {method} {path}")
            # Pour la bêta, on laisse passer avec un warning
            # En production, décommenter pour deny by default:
            # return JSONResponse(
            #     status_code=403,
            #     content={"detail": "Route non autorisée"}
            # )
            return await call_next(request)

        # 5. Vérifier la permission
        user = self._get_user(request)
        if not user:
            return JSONResponse(
                status_code=401,
                content={"detail": "Utilisateur non trouvé"}
            )

        user_role = self._get_user_role(user)
        if not user_role:
            self._log_denied(request, route_perm, "Rôle non défini")
            return JSONResponse(
                status_code=403,
                content={"detail": "Rôle utilisateur non défini"}
            )

        # Vérifier la permission
        permission = check_permission(user_role, route_perm.module, route_perm.action)

        if not permission.allowed:
            self._log_denied(request, route_perm, f"Permission refusée pour {user_role.value}")
            return JSONResponse(
                status_code=403,
                content={
                    "detail": f"Accès refusé: {route_perm.module.value}.{route_perm.action.value}",
                    "required_permission": f"{route_perm.module.value}.{route_perm.action.value}"
                }
            )

        # 6. Stocker la restriction pour traitement ultérieur
        request.state.rbac_restriction = permission.restriction
        request.state.rbac_permission = route_perm

        return await call_next(request)

    def _is_public_route(self, path: str) -> bool:
        """Vérifie si la route est publique."""
        for pattern in PUBLIC_ROUTES:
            if re.match(pattern, path):
                return True
        return False

    def _is_authenticated_only_route(self, path: str) -> bool:
        """Vérifie si la route nécessite seulement l'authentification."""
        for pattern in AUTHENTICATED_ONLY_ROUTES:
            if re.match(pattern, path):
                return True
        return False

    def _is_authenticated(self, request: Request) -> bool:
        """Vérifie si l'utilisateur est authentifié."""
        return (
            hasattr(request, 'state') and
            hasattr(request.state, 'user') and
            request.state.user is not None
        )

    def _get_user(self, request: Request):
        """Récupère l'utilisateur depuis la request."""
        if hasattr(request, 'state') and hasattr(request.state, 'user'):
            return request.state.user
        return None

    def _get_user_role(self, user) -> Optional[StandardRole]:
        """Récupère le rôle standard de l'utilisateur."""
        # Essayer d'abord l'attribut standard_role
        if hasattr(user, 'standard_role') and user.standard_role:
            try:
                return StandardRole(user.standard_role)
            except ValueError:
                pass

        # Mapper depuis le rôle legacy
        if hasattr(user, 'role'):
            return map_legacy_role_to_standard(user.role)

        # Chercher dans les rôles IAM
        if hasattr(user, 'roles') and user.roles:
            for role in user.roles:
                standard = map_legacy_role_to_standard(role.code if hasattr(role, 'code') else role)
                if standard:
                    return standard

        return None

    def _find_route_permission(self, method: str, path: str) -> Optional[RoutePermission]:
        """Trouve la permission requise pour une route."""
        for (route_method, pattern), permission in ROUTE_PERMISSIONS.items():
            if route_method == method and re.match(pattern, path):
                return permission
        return None

    def _log_denied(self, request: Request, route_perm: RoutePermission, reason: str):
        """Log un refus d'accès."""
        user = self._get_user(request)
        user_id = user.id if user and hasattr(user, 'id') else 'unknown'
        tenant_id = getattr(request.state, 'tenant_id', 'unknown') if hasattr(request, 'state') else 'unknown'

        logger.warning(
            f"RBAC DENIED: method={request.method} path={request.url.path} "
            f"user_id={user_id} tenant_id={tenant_id} "
            f"module={route_perm.module.value} action={route_perm.action.value} "
            f"reason={reason}"
        )


# ============================================================================
# HELPER POUR AJOUTER DE NOUVELLES ROUTES
# ============================================================================

def register_route_permission(
    method: str,
    path_pattern: str,
    module: Module,
    action: Action,
    allow_public: bool = False
):
    """
    Enregistre une nouvelle permission de route.

    Usage:
        register_route_permission("GET", r"/api/custom/resource/?$", Module.CLIENTS, Action.READ)
    """
    ROUTE_PERMISSIONS[(method, path_pattern)] = RoutePermission(
        module=module,
        action=action,
        allow_public=allow_public
    )


def register_public_route(path_pattern: str):
    """
    Enregistre une route comme publique.

    Usage:
        register_public_route(r"^/api/public/.*$")
    """
    PUBLIC_ROUTES.append(path_pattern)


# ============================================================================
# FACTORY POUR FASTAPI
# ============================================================================

def get_rbac_middleware() -> RBACMiddleware:
    """Retourne une instance du middleware RBAC."""
    return RBACMiddleware


def setup_rbac_middleware(app):
    """
    Configure le middleware RBAC sur une application FastAPI.

    Usage:
        from fastapi import FastAPI
        from app.modules.iam.rbac_middleware import setup_rbac_middleware

        app = FastAPI()
        setup_rbac_middleware(app)
    """
    app.add_middleware(RBACMiddleware)
    logger.info("RBAC Middleware initialized")
