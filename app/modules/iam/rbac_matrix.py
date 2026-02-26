"""
AZALSCORE - MATRICE RBAC BÊTA
==============================

Matrice de contrôle d'accès basé sur les rôles (RBAC) pour la version bêta.
Définit 5 rôles standards avec leurs permissions granulaires par module.

RÔLES STANDARDS:
- super_admin : Créateur / système - invisible en bêta
- admin       : Administrateur de l'organisation
- manager     : Responsable d'équipe / service
- user        : Utilisateur standard
- readonly    : Consultation uniquement

RÈGLES FONDAMENTALES:
- deny-by-default : Tout accès non explicitement autorisé est refusé
- isolation tenant : Aucune donnée cross-tenant accessible
- super_admin seul peut modifier les rôles et paramètres de sécurité
- admin ne peut jamais modifier ses propres droits
"""
from __future__ import annotations


import functools
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# DÉFINITION DES RÔLES STANDARDS
# ============================================================================

class StandardRole(str, Enum):
    """Rôles standards AZALSCORE Bêta."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    READONLY = "readonly"


# Niveau hiérarchique des rôles (0 = plus élevé)
ROLE_HIERARCHY: dict[StandardRole, int] = {
    StandardRole.SUPER_ADMIN: 0,
    StandardRole.ADMIN: 1,
    StandardRole.MANAGER: 2,
    StandardRole.USER: 3,
    StandardRole.READONLY: 4,
}


# ============================================================================
# DÉFINITION DES MODULES
# ============================================================================

class Module(str, Enum):
    """Modules principaux AZALSCORE."""
    USERS = "users"           # Utilisateurs & Rôles
    ORGANIZATION = "org"      # Organisation / Société
    CLIENTS = "clients"       # Clients / Contacts
    BILLING = "billing"       # Facturation / Devis / Paiements
    PROJECTS = "projects"     # Projets / Activités
    REPORTING = "reporting"   # Reporting / KPI
    SETTINGS = "settings"     # Paramètres / Configuration
    SECURITY = "security"     # Sécurité système
    AUDIT = "audit"           # Logs d'audit


# ============================================================================
# DÉFINITION DES ACTIONS
# ============================================================================

class Action(str, Enum):
    """Actions CRUD + spéciales."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    # Actions spéciales
    EXPORT = "export"
    VALIDATE = "validate"
    ASSIGN = "assign"
    ADMIN = "admin"


# ============================================================================
# TYPES DE RESTRICTION
# ============================================================================

class Restriction(str, Enum):
    """Types de restriction d'accès."""
    FULL = "full"             # Accès complet
    LIMITED = "limited"       # Accès limité (voir contexte)
    OWN_DATA = "own_data"     # Ses propres données uniquement
    TEAM_DATA = "team_data"   # Données de son équipe
    NONE = "none"             # Aucun accès


@dataclass
class Permission:
    """Définition d'une permission avec sa restriction."""
    allowed: bool
    restriction: Restriction = Restriction.FULL
    description: str = ""

    def __bool__(self):
        return self.allowed


# ============================================================================
# MATRICE D'ACCÈS PRINCIPALE
# ============================================================================

# Raccourcis pour la lisibilité
FULL = Permission(True, Restriction.FULL)
LIMITED = Permission(True, Restriction.LIMITED)
OWN = Permission(True, Restriction.OWN_DATA)
TEAM = Permission(True, Restriction.TEAM_DATA)
DENY = Permission(False, Restriction.NONE)


# Matrice complète: ROLE -> MODULE -> ACTION -> Permission
RBAC_MATRIX: dict[StandardRole, dict[Module, dict[Action, Permission]]] = {

    # =========================================================================
    # SUPER_ADMIN - Accès total (invisible en bêta)
    # =========================================================================
    StandardRole.SUPER_ADMIN: {
        Module.USERS: {
            Action.READ: FULL,
            Action.CREATE: FULL,
            Action.UPDATE: FULL,
            Action.DELETE: FULL,
            Action.ASSIGN: FULL,  # Modifier les rôles
        },
        Module.ORGANIZATION: {
            Action.READ: FULL,
            Action.UPDATE: FULL,
            Action.ADMIN: FULL,  # Paramètres sensibles
        },
        Module.CLIENTS: {
            Action.READ: FULL,
            Action.CREATE: FULL,
            Action.UPDATE: FULL,
            Action.DELETE: FULL,
        },
        Module.BILLING: {
            Action.READ: FULL,
            Action.CREATE: FULL,
            Action.UPDATE: FULL,
            Action.DELETE: FULL,
            Action.VALIDATE: FULL,
        },
        Module.PROJECTS: {
            Action.READ: FULL,
            Action.CREATE: FULL,
            Action.UPDATE: FULL,
            Action.DELETE: FULL,
        },
        Module.REPORTING: {
            Action.READ: FULL,
            Action.EXPORT: FULL,
        },
        Module.SETTINGS: {
            Action.READ: FULL,
            Action.UPDATE: FULL,
        },
        Module.SECURITY: {
            Action.READ: FULL,
            Action.UPDATE: FULL,
            Action.ADMIN: FULL,
        },
        Module.AUDIT: {
            Action.READ: FULL,
            Action.EXPORT: FULL,
        },
    },

    # =========================================================================
    # ADMIN - Administrateur organisation
    # =========================================================================
    StandardRole.ADMIN: {
        Module.USERS: {
            Action.READ: FULL,
            Action.CREATE: FULL,
            Action.UPDATE: FULL,
            Action.DELETE: LIMITED,  # Ne peut pas supprimer super_admin
            Action.ASSIGN: DENY,     # Ne peut PAS modifier les rôles
        },
        Module.ORGANIZATION: {
            Action.READ: FULL,
            Action.UPDATE: FULL,
            Action.ADMIN: DENY,      # Pas de paramètres sensibles
        },
        Module.CLIENTS: {
            Action.READ: FULL,
            Action.CREATE: FULL,
            Action.UPDATE: FULL,
            Action.DELETE: FULL,
        },
        Module.BILLING: {
            Action.READ: FULL,
            Action.CREATE: FULL,
            Action.UPDATE: FULL,
            Action.DELETE: LIMITED,  # Audit obligatoire
            Action.VALIDATE: FULL,
        },
        Module.PROJECTS: {
            Action.READ: FULL,
            Action.CREATE: FULL,
            Action.UPDATE: FULL,
            Action.DELETE: LIMITED,  # Audit obligatoire
        },
        Module.REPORTING: {
            Action.READ: FULL,
            Action.EXPORT: DENY,     # Pas d'export
        },
        Module.SETTINGS: {
            Action.READ: FULL,
            Action.UPDATE: DENY,     # Pas de modification
        },
        Module.SECURITY: {
            Action.READ: DENY,
            Action.UPDATE: DENY,
            Action.ADMIN: DENY,
        },
        Module.AUDIT: {
            Action.READ: DENY,       # Pas d'accès aux logs système
            Action.EXPORT: DENY,
        },
    },

    # =========================================================================
    # MANAGER - Responsable d'équipe
    # =========================================================================
    StandardRole.MANAGER: {
        Module.USERS: {
            Action.READ: DENY,
            Action.CREATE: DENY,
            Action.UPDATE: DENY,
            Action.DELETE: DENY,
            Action.ASSIGN: DENY,
        },
        Module.ORGANIZATION: {
            Action.READ: FULL,
            Action.UPDATE: DENY,
            Action.ADMIN: DENY,
        },
        Module.CLIENTS: {
            Action.READ: FULL,
            Action.CREATE: FULL,
            Action.UPDATE: FULL,
            Action.DELETE: DENY,
        },
        Module.BILLING: {
            Action.READ: FULL,
            Action.CREATE: FULL,
            Action.UPDATE: DENY,
            Action.DELETE: DENY,
            Action.VALIDATE: DENY,
        },
        Module.PROJECTS: {
            Action.READ: FULL,
            Action.CREATE: FULL,
            Action.UPDATE: FULL,
            Action.DELETE: DENY,
        },
        Module.REPORTING: {
            Action.READ: TEAM,       # Données équipe uniquement
            Action.EXPORT: DENY,
        },
        Module.SETTINGS: {
            Action.READ: DENY,
            Action.UPDATE: DENY,
        },
        Module.SECURITY: {
            Action.READ: DENY,
            Action.UPDATE: DENY,
            Action.ADMIN: DENY,
        },
        Module.AUDIT: {
            Action.READ: DENY,
            Action.EXPORT: DENY,
        },
    },

    # =========================================================================
    # USER - Utilisateur standard
    # =========================================================================
    StandardRole.USER: {
        Module.USERS: {
            Action.READ: DENY,
            Action.CREATE: DENY,
            Action.UPDATE: DENY,
            Action.DELETE: DENY,
            Action.ASSIGN: DENY,
        },
        Module.ORGANIZATION: {
            Action.READ: FULL,
            Action.UPDATE: DENY,
            Action.ADMIN: DENY,
        },
        Module.CLIENTS: {
            Action.READ: FULL,
            Action.CREATE: LIMITED,  # Création limitée
            Action.UPDATE: OWN,      # Ses données uniquement
            Action.DELETE: DENY,
        },
        Module.BILLING: {
            Action.READ: OWN,        # Restreint à ses données
            Action.CREATE: DENY,
            Action.UPDATE: DENY,
            Action.DELETE: DENY,
            Action.VALIDATE: DENY,
        },
        Module.PROJECTS: {
            Action.READ: FULL,
            Action.CREATE: DENY,
            Action.UPDATE: OWN,      # Projets assignés uniquement
            Action.DELETE: DENY,
        },
        Module.REPORTING: {
            Action.READ: OWN,        # Données personnelles uniquement
            Action.EXPORT: DENY,
        },
        Module.SETTINGS: {
            Action.READ: DENY,
            Action.UPDATE: DENY,
        },
        Module.SECURITY: {
            Action.READ: DENY,
            Action.UPDATE: DENY,
            Action.ADMIN: DENY,
        },
        Module.AUDIT: {
            Action.READ: DENY,
            Action.EXPORT: DENY,
        },
    },

    # =========================================================================
    # READONLY - Consultation uniquement
    # =========================================================================
    StandardRole.READONLY: {
        Module.USERS: {
            Action.READ: DENY,
            Action.CREATE: DENY,
            Action.UPDATE: DENY,
            Action.DELETE: DENY,
            Action.ASSIGN: DENY,
        },
        Module.ORGANIZATION: {
            Action.READ: FULL,
            Action.UPDATE: DENY,
            Action.ADMIN: DENY,
        },
        Module.CLIENTS: {
            Action.READ: FULL,
            Action.CREATE: DENY,
            Action.UPDATE: DENY,
            Action.DELETE: DENY,
        },
        Module.BILLING: {
            Action.READ: FULL,
            Action.CREATE: DENY,
            Action.UPDATE: DENY,
            Action.DELETE: DENY,
            Action.VALIDATE: DENY,
        },
        Module.PROJECTS: {
            Action.READ: FULL,
            Action.CREATE: DENY,
            Action.UPDATE: DENY,
            Action.DELETE: DENY,
        },
        Module.REPORTING: {
            Action.READ: LIMITED,    # Lecture limitée
            Action.EXPORT: DENY,
        },
        Module.SETTINGS: {
            Action.READ: DENY,
            Action.UPDATE: DENY,
        },
        Module.SECURITY: {
            Action.READ: DENY,
            Action.UPDATE: DENY,
            Action.ADMIN: DENY,
        },
        Module.AUDIT: {
            Action.READ: DENY,
            Action.EXPORT: DENY,
        },
    },
}


# ============================================================================
# RÈGLES TRANSVERSALES DE SÉCURITÉ
# ============================================================================

class SecurityRules:
    """
    Règles de sécurité transversales obligatoires.
    Ces règles s'appliquent AVANT la matrice RBAC.
    """

    @staticmethod
    def can_modify_roles(actor_role: StandardRole) -> bool:
        """Seul super_admin peut modifier les rôles."""
        return actor_role == StandardRole.SUPER_ADMIN

    @staticmethod
    def can_modify_security(actor_role: StandardRole) -> bool:
        """Seul super_admin peut modifier la sécurité."""
        return actor_role == StandardRole.SUPER_ADMIN

    @staticmethod
    def can_access_system_logs(actor_role: StandardRole) -> bool:
        """Seul super_admin peut accéder aux logs système."""
        return actor_role == StandardRole.SUPER_ADMIN

    @staticmethod
    def can_disable_protections(actor_role: StandardRole) -> bool:
        """Seul super_admin peut désactiver des protections."""
        return actor_role == StandardRole.SUPER_ADMIN

    @staticmethod
    def can_modify_own_rights(actor_role: StandardRole, is_self: bool) -> bool:
        """
        Un admin ne peut jamais modifier ses propres droits.
        Seul super_admin peut s'auto-modifier.
        """
        if actor_role == StandardRole.SUPER_ADMIN:
            return True
        if is_self and actor_role == StandardRole.ADMIN:
            return False
        return False

    @staticmethod
    def can_delete_user(
        actor_role: StandardRole,
        target_role: StandardRole
    ) -> bool:
        """
        Vérifie si un acteur peut supprimer un utilisateur.
        - super_admin peut supprimer n'importe qui
        - admin peut supprimer sauf super_admin
        - autres ne peuvent pas supprimer
        """
        if actor_role == StandardRole.SUPER_ADMIN:
            return True
        if actor_role == StandardRole.ADMIN:
            return target_role != StandardRole.SUPER_ADMIN
        return False

    @staticmethod
    def is_role_higher_or_equal(role1: StandardRole, role2: StandardRole) -> bool:
        """Vérifie si role1 est hiérarchiquement >= role2."""
        return ROLE_HIERARCHY[role1] <= ROLE_HIERARCHY[role2]


# ============================================================================
# FONCTIONS DE VÉRIFICATION DES PERMISSIONS
# ============================================================================

def check_permission(
    role: StandardRole,
    module: Module,
    action: Action
) -> Permission:
    """
    Vérifie si un rôle a la permission pour une action sur un module.

    Args:
        role: Le rôle de l'utilisateur
        module: Le module concerné
        action: L'action à effectuer

    Returns:
        Permission avec allowed=True/False et restriction associée
    """
    # Deny by default
    if role not in RBAC_MATRIX:
        return DENY

    role_perms = RBAC_MATRIX[role]
    if module not in role_perms:
        return DENY

    module_perms = role_perms[module]
    if action not in module_perms:
        return DENY

    return module_perms[action]


def has_permission(
    role: StandardRole,
    module: Module,
    action: Action
) -> bool:
    """Vérifie simplement si la permission est accordée (bool)."""
    return check_permission(role, module, action).allowed


def get_all_permissions(role: StandardRole) -> dict[str, dict[str, bool]]:
    """
    Retourne toutes les permissions d'un rôle sous forme de dict.
    Format: {module: {action: allowed}}
    """
    result = {}
    if role not in RBAC_MATRIX:
        return result

    for module, actions in RBAC_MATRIX[role].items():
        result[module.value] = {}
        for action, perm in actions.items():
            result[module.value][action.value] = perm.allowed

    return result


def get_allowed_actions(role: StandardRole, module: Module) -> list[Action]:
    """Retourne la liste des actions autorisées pour un rôle sur un module."""
    allowed = []
    if role not in RBAC_MATRIX:
        return allowed

    if module not in RBAC_MATRIX[role]:
        return allowed

    for action, perm in RBAC_MATRIX[role][module].items():
        if perm.allowed:
            allowed.append(action)

    return allowed


# ============================================================================
# PERMISSIONS CODES (pour compatibilité avec le système existant)
# ============================================================================

def generate_permission_code(module: Module, action: Action) -> str:
    """Génère un code de permission au format module.action."""
    return f"{module.value}.{action.value}"


# Mapping des permissions standards vers codes existants
PERMISSION_CODE_MAPPING: dict[str, str] = {
    # Users & Roles
    "users.read": "iam.user.read",
    "users.create": "iam.user.create",
    "users.update": "iam.user.update",
    "users.delete": "iam.user.delete",
    "users.assign": "iam.role.assign",

    # Organization
    "org.read": "admin.tenant.read",
    "org.update": "admin.tenant.update",
    "org.admin": "admin.settings.update",

    # Clients
    "clients.read": "commercial.customers.read",
    "clients.create": "commercial.customers.create",
    "clients.update": "commercial.customers.update",
    "clients.delete": "commercial.customers.delete",

    # Billing
    "billing.read": "sales.invoice.read",
    "billing.create": "sales.invoice.create",
    "billing.update": "sales.invoice.update",
    "billing.delete": "sales.invoice.delete",
    "billing.validate": "sales.invoice.validate",

    # Projects
    "projects.read": "projects.read",
    "projects.create": "projects.create",
    "projects.update": "projects.update",
    "projects.delete": "projects.delete",

    # Reporting
    "reporting.read": "bi.reports.read",
    "reporting.export": "bi.reports.export",

    # Settings
    "settings.read": "admin.settings.read",
    "settings.update": "admin.settings.update",

    # Security
    "security.read": "iam.audit.read",
    "security.update": "iam.policy.update",
    "security.admin": "iam.user.admin",

    # Audit
    "audit.read": "audit.logs.read",
    "audit.export": "audit.logs.export",
}


def get_legacy_permission_code(module: Module, action: Action) -> str | None:
    """Convertit une permission standard en code legacy."""
    key = f"{module.value}.{action.value}"
    return PERMISSION_CODE_MAPPING.get(key)


# ============================================================================
# RÔLE → PERMISSIONS LEGACY (pour seeding)
# ============================================================================

def get_legacy_permissions_for_role(role: StandardRole) -> list[str]:
    """
    Génère la liste des codes de permission legacy pour un rôle.
    Utilisé pour initialiser la base de données.
    """
    permissions = []

    if role not in RBAC_MATRIX:
        return permissions

    for module, actions in RBAC_MATRIX[role].items():
        for action, perm in actions.items():
            if perm.allowed:
                legacy_code = get_legacy_permission_code(module, action)
                if legacy_code:
                    permissions.append(legacy_code)

    return permissions


# ============================================================================
# EXPORT POUR SEEDING DB
# ============================================================================

STANDARD_ROLES_CONFIG = [
    {
        "code": "super_admin",
        "name": "Super Administrateur",
        "description": "Accès total au système - Invisible en bêta",
        "level": 0,
        "is_system": True,
        "is_assignable": False,  # Non assignable manuellement
    },
    {
        "code": "admin",
        "name": "Administrateur",
        "description": "Administrateur de l'organisation",
        "level": 1,
        "is_system": True,
        "is_assignable": True,
    },
    {
        "code": "manager",
        "name": "Responsable",
        "description": "Responsable d'équipe ou de service",
        "level": 2,
        "is_system": True,
        "is_assignable": True,
    },
    {
        "code": "user",
        "name": "Utilisateur",
        "description": "Utilisateur standard avec accès limité",
        "level": 3,
        "is_system": True,
        "is_assignable": True,
    },
    {
        "code": "readonly",
        "name": "Consultation",
        "description": "Accès en lecture seule",
        "level": 4,
        "is_system": True,
        "is_assignable": True,
    },
]


# ============================================================================
# DÉCORATEUR DE PERMISSION
# ============================================================================

def require_permission(module: Module, action: Action):
    """
    Décorateur pour vérifier les permissions sur une route.

    Usage:
        @require_permission(Module.CLIENTS, Action.CREATE)
        async def create_client(request: Request):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Le request doit être dans args ou kwargs
            request = kwargs.get('request')
            if not request:
                for arg in args:
                    if hasattr(arg, 'state') and hasattr(arg.state, 'user'):
                        request = arg
                        break

            if not request or not hasattr(request, 'state'):
                from fastapi import HTTPException
                raise HTTPException(status_code=401, detail="Non authentifié")

            user = getattr(request.state, 'user', None)
            if not user:
                from fastapi import HTTPException
                raise HTTPException(status_code=401, detail="Non authentifié")

            # Récupérer le rôle standard de l'utilisateur
            user_role = getattr(user, 'standard_role', None)
            if not user_role:
                # Fallback: mapper depuis le rôle legacy
                user_role = map_legacy_role_to_standard(getattr(user, 'role', None))

            if not user_role:
                from fastapi import HTTPException
                raise HTTPException(status_code=403, detail="Rôle non défini")

            # Vérifier la permission
            permission = check_permission(user_role, module, action)

            if not permission.allowed:
                from fastapi import HTTPException
                # Log du refus
                _log_permission_denied(user, module, action)
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission refusée: {module.value}.{action.value}"
                )

            # Injecter la restriction dans la request pour traitement ultérieur
            request.state.permission_restriction = permission.restriction

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def _log_permission_denied(user, module: Module, action: Action):
    """Log les refus de permission critiques."""
    import logging
    logger = logging.getLogger("rbac.security")
    logger.warning(
        "RBAC DENIED: user=%s "
        "role=%s "
        "module=%s action=%s",
        getattr(user, 'id', 'unknown'), getattr(user, 'role', 'unknown'), module.value, action.value
    )


# ============================================================================
# MAPPING RÔLES LEGACY → STANDARD
# ============================================================================

LEGACY_ROLE_MAPPING = {
    # Rôles existants dans core/models.py
    "DIRIGEANT": StandardRole.ADMIN,
    "ADMIN": StandardRole.ADMIN,
    "DAF": StandardRole.MANAGER,
    "COMPTABLE": StandardRole.USER,
    "COMMERCIAL": StandardRole.USER,
    "EMPLOYE": StandardRole.READONLY,

    # Rôles IAM existants
    "SUPERADMIN": StandardRole.SUPER_ADMIN,  # Sans underscore (UserRole enum)
    "SUPER_ADMIN": StandardRole.SUPER_ADMIN,  # Avec underscore (legacy)
    "TENANT_ADMIN": StandardRole.ADMIN,
    "DRH": StandardRole.MANAGER,
    "RESPONSABLE_COMMERCIAL": StandardRole.MANAGER,
    "RESPONSABLE_ACHATS": StandardRole.MANAGER,
    "RESPONSABLE_PRODUCTION": StandardRole.MANAGER,
    "ACHETEUR": StandardRole.USER,
    "MAGASINIER": StandardRole.USER,
    "RH": StandardRole.USER,
    "CONSULTANT": StandardRole.READONLY,
    "AUDITEUR": StandardRole.READONLY,
}


def map_legacy_role_to_standard(legacy_role) -> StandardRole | None:
    """Convertit un rôle legacy en rôle standard."""
    if legacy_role is None:
        return None

    role_str = str(legacy_role)
    if hasattr(legacy_role, 'value'):
        role_str = legacy_role.value

    return LEGACY_ROLE_MAPPING.get(role_str.upper())


# ============================================================================
# VALIDATION MATRICE
# ============================================================================

def validate_matrix_completeness():
    """
    Valide que la matrice RBAC est complète.
    Lève une exception si des combinaisons manquent.
    """
    errors = []

    for role in StandardRole:
        if role not in RBAC_MATRIX:
            errors.append(f"Role {role.value} manquant dans la matrice")
            continue

        for module in Module:
            if module not in RBAC_MATRIX[role]:
                errors.append(f"Module {module.value} manquant pour rôle {role.value}")

    if errors:
        raise ValueError("Matrice RBAC incomplète:\n" + "\n".join(errors))

    return True


# Validation au chargement du module
validate_matrix_completeness()
