"""
AZALS MODULE T0 - GESTION DES UTILISATEURS & RÔLES (IAM)
=========================================================

Module enterprise complet pour la gestion des identités et accès.

Fonctionnalités:
- Gestion des utilisateurs (CRUD, profils, activation)
- Gestion des rôles (hiérarchie, permissions)
- Permissions granulaires (module.ressource.action)
- MATRICE RBAC BÊTA avec 5 rôles standards
- Groupes utilisateurs
- Sessions et tokens
- Séparation des pouvoirs
- Audit trail complet
- Rate limiting
- MFA/2FA (TOTP)

Architecture:
- models.py : Modèles SQLAlchemy
- schemas.py : Schémas Pydantic
- service.py : Logique métier
- router.py : Endpoints API
- permissions.py : Définitions permissions
- decorators.py : Décorateurs sécurité
- rbac_matrix.py : Matrice RBAC Bêta (5 rôles standards)
- rbac_service.py : Service RBAC centralisé
- rbac_middleware.py : Middleware RBAC automatique

Rôles Standards Bêta:
- super_admin : Accès total (invisible en bêta)
- admin : Administrateur organisation
- manager : Responsable équipe/service
- user : Utilisateur standard
- readonly : Consultation uniquement

Version: 1.1.0
Auteur: AZALS Team
Date: 2026-01-07
"""

__version__ = "1.1.0"
__module_code__ = "T0"
__module_name__ = "IAM - Gestion Utilisateurs & Rôles"

# Exports RBAC Matrix (sans dépendances externes)
from .rbac_matrix import (
    RBAC_MATRIX,
    ROLE_HIERARCHY,
    STANDARD_ROLES_CONFIG,
    Action,
    Module,
    Permission,
    Restriction,
    SecurityRules,
    StandardRole,
    check_permission,
    get_all_permissions,
    get_allowed_actions,
    has_permission,
    map_legacy_role_to_standard,
)
from .rbac_matrix import (
    require_permission as require_rbac_permission,
)

# Exports RBAC Service et Middleware (avec dépendances)
# Ces imports sont conditionnels pour éviter les erreurs si les dépendances ne sont pas installées
try:
    from .rbac_service import (
        RBACService,
        get_rbac_dependency,
        get_rbac_service,
    )
    _RBAC_SERVICE_AVAILABLE = True
except ImportError:
    _RBAC_SERVICE_AVAILABLE = False
    RBACService = None
    get_rbac_service = None
    get_rbac_dependency = None

try:
    from .rbac_middleware import (
        PUBLIC_ROUTES,
        ROUTE_PERMISSIONS,
        RBACMiddleware,
        register_public_route,
        register_route_permission,
        setup_rbac_middleware,
    )
    _RBAC_MIDDLEWARE_AVAILABLE = True
except ImportError:
    _RBAC_MIDDLEWARE_AVAILABLE = False
    RBACMiddleware = None
    setup_rbac_middleware = None
    register_route_permission = None
    register_public_route = None
    ROUTE_PERMISSIONS = {}
    PUBLIC_ROUTES = []

__all__ = [
    # Version
    "__version__",
    "__module_code__",
    "__module_name__",
    # RBAC Matrix
    "StandardRole",
    "Module",
    "Action",
    "Restriction",
    "Permission",
    "SecurityRules",
    "RBAC_MATRIX",
    "ROLE_HIERARCHY",
    "check_permission",
    "has_permission",
    "get_all_permissions",
    "get_allowed_actions",
    "map_legacy_role_to_standard",
    "require_rbac_permission",
    "STANDARD_ROLES_CONFIG",
    # RBAC Service
    "RBACService",
    "get_rbac_service",
    "get_rbac_dependency",
    # RBAC Middleware
    "RBACMiddleware",
    "setup_rbac_middleware",
    "register_route_permission",
    "register_public_route",
    "ROUTE_PERMISSIONS",
    "PUBLIC_ROUTES",
]
