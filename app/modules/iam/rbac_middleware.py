"""
AZALSCORE - Middleware RBAC
============================

Middleware pour appliquer automatiquement les vérifications RBAC
sur toutes les routes protégées.

PRINCIPE: Deny by default
- Routes non listées → 403
- Permissions non accordées → 403
- Logs sur tous les refus critiques

SÉCURITÉ: Utilise build_error_response du module Guardian pour garantir
          qu'aucune erreur ne provoque de crash, même sans fichiers HTML.
"""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Import de la fonction SAFE de gestion des erreurs
# Note: Utilise error_response.py au lieu de middleware.py pour éviter les imports circulaires
from app.modules.guardian.error_response import (
    ErrorType,
    build_error_response,
)

from .rbac_matrix import (
    Action,
    Module,
    StandardRole,
    check_permission,
    map_legacy_role_to_standard,
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
ROUTE_PERMISSIONS: dict[tuple[str, str], RoutePermission] = {
    # =========================================================================
    # USERS & ROLES (legacy /api/iam/ routes)
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
    # USERS & ROLES (v1 routes - current API)
    # =========================================================================
    ("GET", r"/v1/iam/users/?$"): RoutePermission(Module.USERS, Action.READ),
    ("GET", r"/v1/iam/users/[0-9a-fA-F-]+$"): RoutePermission(Module.USERS, Action.READ),
    ("POST", r"/v1/iam/users/?$"): RoutePermission(Module.USERS, Action.CREATE),
    ("PUT", r"/v1/iam/users/[0-9a-fA-F-]+$"): RoutePermission(Module.USERS, Action.UPDATE),
    ("PATCH", r"/v1/iam/users/[0-9a-fA-F-]+$"): RoutePermission(Module.USERS, Action.UPDATE),
    ("DELETE", r"/v1/iam/users/[0-9a-fA-F-]+$"): RoutePermission(Module.USERS, Action.DELETE),

    # Rôles v1
    ("GET", r"/v1/iam/roles/?$"): RoutePermission(Module.USERS, Action.READ),
    ("GET", r"/v1/iam/roles/[0-9a-fA-F-]+$"): RoutePermission(Module.USERS, Action.READ),
    ("POST", r"/v1/iam/roles/?$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("PUT", r"/v1/iam/roles/[0-9a-fA-F-]+$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("DELETE", r"/v1/iam/roles/[0-9a-fA-F-]+$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("POST", r"/v1/iam/users/[0-9a-fA-F-]+/roles/?$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("DELETE", r"/v1/iam/users/[0-9a-fA-F-]+/roles/[0-9a-fA-F-]+$"): RoutePermission(Module.USERS, Action.ASSIGN),

    # Permissions v1
    ("GET", r"/v1/iam/permissions/?$"): RoutePermission(Module.USERS, Action.READ),
    ("POST", r"/v1/iam/permissions/check/?$"): RoutePermission(Module.USERS, Action.READ),
    ("GET", r"/v1/iam/users/[0-9a-fA-F-]+/permissions/?$"): RoutePermission(Module.USERS, Action.READ),

    # =========================================================================
    # ORGANISATION
    # =========================================================================
    ("GET", r"/api/organization/?$"): RoutePermission(Module.ORGANIZATION, Action.READ),
    ("GET", r"/api/tenants/current/?$"): RoutePermission(Module.ORGANIZATION, Action.READ),
    ("PUT", r"/api/organization/?$"): RoutePermission(Module.ORGANIZATION, Action.UPDATE),
    ("PATCH", r"/api/organization/?$"): RoutePermission(Module.ORGANIZATION, Action.UPDATE),
    ("PUT", r"/api/tenants/current/?$"): RoutePermission(Module.ORGANIZATION, Action.UPDATE),

    # =========================================================================
    # CLIENTS / CONTACTS (routes /api/v1/commercial avec UUIDs)
    # =========================================================================
    ("GET", r"/api/v1/commercial/customers/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("GET", r"/api/v1/commercial/customers/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/api/v1/commercial/customers/?$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("PUT", r"/api/v1/commercial/customers/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("PATCH", r"/api/v1/commercial/customers/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("DELETE", r"/api/v1/commercial/customers/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.DELETE),
    ("POST", r"/api/v1/commercial/customers/[0-9a-fA-F-]+/convert$"): RoutePermission(Module.CLIENTS, Action.UPDATE),

    # Contacts
    ("GET", r"/api/v1/commercial/contacts/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("GET", r"/api/v1/commercial/contacts/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("GET", r"/api/v1/commercial/customers/[0-9a-fA-F-]+/contacts/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/api/v1/commercial/contacts/?$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("PUT", r"/api/v1/commercial/contacts/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("DELETE", r"/api/v1/commercial/contacts/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.DELETE),

    # Opportunités
    ("GET", r"/api/v1/commercial/opportunities/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("GET", r"/api/v1/commercial/opportunities/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/api/v1/commercial/opportunities/?$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("PUT", r"/api/v1/commercial/opportunities/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("POST", r"/api/v1/commercial/opportunities/[0-9a-fA-F-]+/win$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("POST", r"/api/v1/commercial/opportunities/[0-9a-fA-F-]+/lose$"): RoutePermission(Module.CLIENTS, Action.UPDATE),

    # Documents commerciaux (devis, commandes, factures)
    ("GET", r"/api/v1/commercial/documents/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("GET", r"/api/v1/commercial/documents/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/api/v1/commercial/documents/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/api/v1/commercial/documents/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("POST", r"/api/v1/commercial/documents/[0-9a-fA-F-]+/validate$"): RoutePermission(Module.BILLING, Action.VALIDATE),
    ("POST", r"/api/v1/commercial/documents/[0-9a-fA-F-]+/send$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("POST", r"/api/v1/commercial/documents/[0-9a-fA-F-]+/lines$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/api/v1/commercial/lines/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("POST", r"/api/v1/commercial/quotes/[0-9a-fA-F-]+/convert$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("POST", r"/api/v1/commercial/orders/[0-9a-fA-F-]+/invoice$"): RoutePermission(Module.BILLING, Action.CREATE),

    # Paiements
    ("GET", r"/api/v1/commercial/documents/[0-9a-fA-F-]+/payments/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/api/v1/commercial/payments/?$"): RoutePermission(Module.BILLING, Action.CREATE),

    # Activités
    ("GET", r"/api/v1/commercial/activities/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/api/v1/commercial/activities/?$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("POST", r"/api/v1/commercial/activities/[0-9a-fA-F-]+/complete$"): RoutePermission(Module.CLIENTS, Action.UPDATE),

    # Pipeline
    ("GET", r"/api/v1/commercial/pipeline/stages/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/api/v1/commercial/pipeline/stages/?$"): RoutePermission(Module.SETTINGS, Action.UPDATE),
    ("GET", r"/api/v1/commercial/pipeline/stats/?$"): RoutePermission(Module.REPORTING, Action.READ),

    # Produits
    ("GET", r"/api/v1/commercial/products/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("GET", r"/api/v1/commercial/products/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/api/v1/commercial/products/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/api/v1/commercial/products/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.UPDATE),

    # Dashboard commercial
    ("GET", r"/api/v1/commercial/dashboard/?$"): RoutePermission(Module.REPORTING, Action.READ),

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

    # =========================================================================
    # IAM OPERATIONS SENSIBLES (v1 routes)
    # =========================================================================
    ("POST", r"/v1/iam/roles/assign/?$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("POST", r"/v1/iam/roles/revoke/?$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("PUT", r"/v1/iam/users/[0-9a-fA-F-]+/permissions/?$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("POST", r"/v1/iam/users/[0-9a-fA-F-]+/lock/?$"): RoutePermission(Module.SECURITY, Action.UPDATE),
    ("POST", r"/v1/iam/users/[0-9a-fA-F-]+/unlock/?$"): RoutePermission(Module.SECURITY, Action.UPDATE),
    ("GET", r"/v1/iam/capabilities/modules/?$"): RoutePermission(Module.USERS, Action.READ),
    ("GET", r"/v1/iam/groups/?$"): RoutePermission(Module.USERS, Action.READ),
    ("POST", r"/v1/iam/groups/?$"): RoutePermission(Module.USERS, Action.CREATE),
    ("POST", r"/v1/iam/groups/[0-9a-fA-F-]+/members/?$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("DELETE", r"/v1/iam/groups/[0-9a-fA-F-]+/members/?$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("GET", r"/v1/iam/password-policy/?$"): RoutePermission(Module.SECURITY, Action.READ),
    ("PATCH", r"/v1/iam/password-policy/?$"): RoutePermission(Module.SECURITY, Action.UPDATE),

    # =========================================================================
    # ADMIN (v1 routes)
    # =========================================================================
    ("GET", r"/v1/admin/dashboard/?$"): RoutePermission(Module.REPORTING, Action.READ),
    ("GET", r"/v1/admin/users/?$"): RoutePermission(Module.USERS, Action.READ),
    ("GET", r"/v1/admin/users/[0-9a-fA-F-]+$"): RoutePermission(Module.USERS, Action.READ),
    ("GET", r"/v1/admin/roles/?$"): RoutePermission(Module.USERS, Action.READ),
    ("GET", r"/v1/admin/stats/?$"): RoutePermission(Module.REPORTING, Action.READ),
    ("GET", r"/v1/admin/sequences/?$"): RoutePermission(Module.SETTINGS, Action.READ),
    ("GET", r"/v1/admin/sequences/entity-types/?$"): RoutePermission(Module.SETTINGS, Action.READ),
    ("GET", r"/v1/admin/sequences/[a-zA-Z_]+$"): RoutePermission(Module.SETTINGS, Action.READ),
    ("PUT", r"/v1/admin/sequences/[a-zA-Z_]+$"): RoutePermission(Module.SETTINGS, Action.UPDATE),
    ("POST", r"/v1/admin/sequences/[a-zA-Z_]+/reset/?$"): RoutePermission(Module.SETTINGS, Action.UPDATE),

    # =========================================================================
    # BACKUP (v1 routes) - SECURITE CRITIQUE
    # =========================================================================
    ("GET", r"/v1/backup/?$"): RoutePermission(Module.SECURITY, Action.READ),
    ("GET", r"/v1/backup/config/?$"): RoutePermission(Module.SECURITY, Action.READ),
    ("GET", r"/v1/backup/dashboard/stats/?$"): RoutePermission(Module.SECURITY, Action.READ),
    ("GET", r"/v1/backup/[0-9a-fA-F-]+$"): RoutePermission(Module.SECURITY, Action.READ),
    ("POST", r"/v1/backup/?$"): RoutePermission(Module.SECURITY, Action.ADMIN),
    ("POST", r"/v1/backup/config/?$"): RoutePermission(Module.SECURITY, Action.ADMIN),
    ("PATCH", r"/v1/backup/config/?$"): RoutePermission(Module.SECURITY, Action.ADMIN),
    ("POST", r"/v1/backup/restore/?$"): RoutePermission(Module.SECURITY, Action.ADMIN),
    ("POST", r"/v1/backup/[0-9a-fA-F-]+/run/?$"): RoutePermission(Module.SECURITY, Action.ADMIN),
    ("DELETE", r"/v1/backup/[0-9a-fA-F-]+$"): RoutePermission(Module.SECURITY, Action.ADMIN),

    # =========================================================================
    # TENANTS (v1 routes) - SECURITE CRITIQUE
    # =========================================================================
    ("GET", r"/v1/tenants/?$"): RoutePermission(Module.ORGANIZATION, Action.READ),
    ("GET", r"/v1/tenants/[0-9a-fA-F-]+$"): RoutePermission(Module.ORGANIZATION, Action.READ),
    ("POST", r"/v1/tenants/?$"): RoutePermission(Module.ORGANIZATION, Action.ADMIN),
    ("PUT", r"/v1/tenants/[0-9a-fA-F-]+$"): RoutePermission(Module.ORGANIZATION, Action.UPDATE),
    ("PATCH", r"/v1/tenants/[0-9a-fA-F-]+$"): RoutePermission(Module.ORGANIZATION, Action.UPDATE),
    ("DELETE", r"/v1/tenants/[0-9a-fA-F-]+$"): RoutePermission(Module.ORGANIZATION, Action.ADMIN),
    ("POST", r"/v1/tenants/[0-9a-fA-F-]+/modules/[a-zA-Z_]+$"): RoutePermission(Module.ORGANIZATION, Action.UPDATE),
    ("DELETE", r"/v1/tenants/[0-9a-fA-F-]+/modules/[a-zA-Z_]+$"): RoutePermission(Module.ORGANIZATION, Action.UPDATE),

    # =========================================================================
    # COMMERCIAL (v1 routes - sans /api prefix)
    # =========================================================================
    ("GET", r"/v1/commercial/customers/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("GET", r"/v1/commercial/customers/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/v1/commercial/customers/?$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("PUT", r"/v1/commercial/customers/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("DELETE", r"/v1/commercial/customers/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.DELETE),
    ("GET", r"/v1/commercial/contacts/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("GET", r"/v1/commercial/contacts/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/v1/commercial/contacts/?$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("PUT", r"/v1/commercial/contacts/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("DELETE", r"/v1/commercial/contacts/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.DELETE),
    ("GET", r"/v1/commercial/documents/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("GET", r"/v1/commercial/documents/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v1/commercial/documents/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/v1/commercial/documents/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/v1/commercial/documents/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.DELETE),
    ("POST", r"/v1/commercial/documents/[0-9a-fA-F-]+/validate/?$"): RoutePermission(Module.BILLING, Action.VALIDATE),
    ("POST", r"/v1/commercial/payments/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("GET", r"/v1/commercial/dashboard/?$"): RoutePermission(Module.REPORTING, Action.READ),
    ("GET", r"/v1/commercial/activities/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/v1/commercial/activities/?$"): RoutePermission(Module.CLIENTS, Action.CREATE),

    # =========================================================================
    # STRIPE / PAIEMENTS (v1 routes) - SECURITE CRITIQUE
    # =========================================================================
    ("GET", r"/v1/stripe/config/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("GET", r"/v1/stripe/dashboard/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("GET", r"/v1/stripe/customers/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("GET", r"/v1/stripe/customers/[0-9a-zA-Z_-]+$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v1/stripe/customers/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("GET", r"/v1/stripe/payment-intents/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v1/stripe/payment-intents/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("POST", r"/v1/stripe/checkout-sessions/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("GET", r"/v1/stripe/checkout-sessions/[0-9a-zA-Z_-]+$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v1/stripe/refunds/?$"): RoutePermission(Module.BILLING, Action.ADMIN),
    ("DELETE", r"/v1/stripe/payment-methods/[0-9a-zA-Z_-]+$"): RoutePermission(Module.BILLING, Action.DELETE),

    # =========================================================================
    # INVOICING (v1 routes)
    # =========================================================================
    ("GET", r"/v1/invoicing/invoices/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("GET", r"/v1/invoicing/invoices/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v1/invoicing/invoices/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("POST", r"/v1/invoicing/invoices/[0-9a-fA-F-]+/send/?$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("GET", r"/v1/invoicing/quotes/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("GET", r"/v1/invoicing/quotes/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v1/invoicing/quotes/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("DELETE", r"/v1/invoicing/quotes/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.DELETE),
    ("GET", r"/v1/invoicing/credits/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v1/invoicing/credits/?$"): RoutePermission(Module.BILLING, Action.CREATE),

    # =========================================================================
    # PURCHASES / PROCUREMENT (v1 et v2 routes)
    # =========================================================================
    ("GET", r"/v1/purchases/suppliers/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("GET", r"/v1/purchases/suppliers/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/v1/purchases/suppliers/?$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("PUT", r"/v1/purchases/suppliers/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("DELETE", r"/v1/purchases/suppliers/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.DELETE),
    ("GET", r"/v1/purchases/orders/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("GET", r"/v1/purchases/orders/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v1/purchases/orders/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/v1/purchases/orders/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/v1/purchases/orders/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.DELETE),
    ("POST", r"/v1/purchases/orders/[0-9a-fA-F-]+/validate/?$"): RoutePermission(Module.BILLING, Action.VALIDATE),
    ("GET", r"/v1/purchases/invoices/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("GET", r"/v1/purchases/invoices/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v1/purchases/invoices/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("DELETE", r"/v1/purchases/invoices/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.DELETE),
    ("POST", r"/v1/purchases/invoices/[0-9a-fA-F-]+/validate/?$"): RoutePermission(Module.BILLING, Action.VALIDATE),
    ("GET", r"/v1/purchases/summary/?$"): RoutePermission(Module.REPORTING, Action.READ),

    # Procurement (same as purchases but different prefix)
    ("GET", r"/v1/procurement/suppliers/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/v1/procurement/suppliers/?$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("GET", r"/v1/procurement/orders/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v1/procurement/orders/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("DELETE", r"/v1/procurement/orders/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.DELETE),
    ("GET", r"/v1/procurement/invoices/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v1/procurement/invoices/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("DELETE", r"/v1/procurement/invoices/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.DELETE),
    ("POST", r"/v1/procurement/payments/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("GET", r"/v1/procurement/dashboard/?$"): RoutePermission(Module.REPORTING, Action.READ),

    # =========================================================================
    # FINANCE / TREASURY / ACCOUNTING (v1 routes)
    # =========================================================================
    ("GET", r"/v1/finance/.*$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v1/finance/.*$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/v1/finance/.*$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/v1/finance/.*$"): RoutePermission(Module.BILLING, Action.DELETE),
    ("GET", r"/v1/treasury/.*$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v1/treasury/.*$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/v1/treasury/.*$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/v1/treasury/.*$"): RoutePermission(Module.BILLING, Action.DELETE),
    ("GET", r"/v1/accounting/.*$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v1/accounting/.*$"): RoutePermission(Module.BILLING, Action.CREATE),

    # =========================================================================
    # API V2 - ROUTES CORE SAAS (mirrored from v1 with same permissions)
    # =========================================================================
    # Stripe v2
    ("GET", r"/v2/stripe/.*$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v2/stripe/.*$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("DELETE", r"/v2/stripe/.*$"): RoutePermission(Module.BILLING, Action.DELETE),

    # Subscriptions v2
    ("GET", r"/v2/subscriptions/.*$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v2/subscriptions/.*$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/v2/subscriptions/.*$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("PATCH", r"/v2/subscriptions/.*$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/v2/subscriptions/.*$"): RoutePermission(Module.BILLING, Action.DELETE),

    # HR v2
    ("GET", r"/v2/hr/.*$"): RoutePermission(Module.USERS, Action.READ),
    ("POST", r"/v2/hr/.*$"): RoutePermission(Module.USERS, Action.CREATE),
    ("PUT", r"/v2/hr/.*$"): RoutePermission(Module.USERS, Action.UPDATE),
    ("PATCH", r"/v2/hr/.*$"): RoutePermission(Module.USERS, Action.UPDATE),
    ("DELETE", r"/v2/hr/.*$"): RoutePermission(Module.USERS, Action.DELETE),

    # Quality v2
    ("GET", r"/v2/quality/.*$"): RoutePermission(Module.PROJECTS, Action.READ),
    ("POST", r"/v2/quality/.*$"): RoutePermission(Module.PROJECTS, Action.CREATE),
    ("PUT", r"/v2/quality/.*$"): RoutePermission(Module.PROJECTS, Action.UPDATE),
    ("DELETE", r"/v2/quality/.*$"): RoutePermission(Module.PROJECTS, Action.DELETE),

    # Contacts v2
    ("GET", r"/v2/contacts/.*$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/v2/contacts/.*$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("PUT", r"/v2/contacts/.*$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("PATCH", r"/v2/contacts/.*$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("DELETE", r"/v2/contacts/.*$"): RoutePermission(Module.CLIENTS, Action.DELETE),

    # Interventions v2
    ("GET", r"/v2/interventions/.*$"): RoutePermission(Module.PROJECTS, Action.READ),
    ("POST", r"/v2/interventions/.*$"): RoutePermission(Module.PROJECTS, Action.CREATE),
    ("PUT", r"/v2/interventions/.*$"): RoutePermission(Module.PROJECTS, Action.UPDATE),
    ("DELETE", r"/v2/interventions/.*$"): RoutePermission(Module.PROJECTS, Action.DELETE),

    # Marketplace v2
    ("GET", r"/v2/marketplace/.*$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v2/marketplace/.*$"): RoutePermission(Module.BILLING, Action.CREATE),

    # Mobile v2
    ("GET", r"/v2/mobile/.*$"): RoutePermission(Module.SETTINGS, Action.READ),
    ("POST", r"/v2/mobile/.*$"): RoutePermission(Module.SETTINGS, Action.UPDATE),
    ("DELETE", r"/v2/mobile/.*$"): RoutePermission(Module.SETTINGS, Action.DELETE),

    # AI v2
    ("GET", r"/v2/ai/.*$"): RoutePermission(Module.REPORTING, Action.READ),
    ("POST", r"/v2/ai/.*$"): RoutePermission(Module.REPORTING, Action.CREATE),
    ("DELETE", r"/v2/ai/.*$"): RoutePermission(Module.REPORTING, Action.DELETE),

    # Email v2
    ("GET", r"/v2/email/.*$"): RoutePermission(Module.SETTINGS, Action.READ),
    ("POST", r"/v2/email/.*$"): RoutePermission(Module.SETTINGS, Action.UPDATE),
    ("PATCH", r"/v2/email/.*$"): RoutePermission(Module.SETTINGS, Action.UPDATE),

    # Triggers v2
    ("GET", r"/v2/triggers/.*$"): RoutePermission(Module.SETTINGS, Action.READ),
    ("POST", r"/v2/triggers/.*$"): RoutePermission(Module.SETTINGS, Action.CREATE),
    ("PUT", r"/v2/triggers/.*$"): RoutePermission(Module.SETTINGS, Action.UPDATE),
    ("DELETE", r"/v2/triggers/.*$"): RoutePermission(Module.SETTINGS, Action.DELETE),

    # Web/Website v2
    ("GET", r"/v2/web/.*$"): RoutePermission(Module.SETTINGS, Action.READ),
    ("POST", r"/v2/web/.*$"): RoutePermission(Module.SETTINGS, Action.CREATE),
    ("PUT", r"/v2/web/.*$"): RoutePermission(Module.SETTINGS, Action.UPDATE),
    ("DELETE", r"/v2/web/.*$"): RoutePermission(Module.SETTINGS, Action.DELETE),
    ("GET", r"/v2/website/.*$"): RoutePermission(Module.SETTINGS, Action.READ),
    ("POST", r"/v2/website/.*$"): RoutePermission(Module.SETTINGS, Action.CREATE),
    ("PUT", r"/v2/website/.*$"): RoutePermission(Module.SETTINGS, Action.UPDATE),
    ("DELETE", r"/v2/website/.*$"): RoutePermission(Module.SETTINGS, Action.DELETE),

    # Country Packs v2
    ("GET", r"/v2/country-packs/.*$"): RoutePermission(Module.SETTINGS, Action.READ),
    ("POST", r"/v2/country-packs/.*$"): RoutePermission(Module.SETTINGS, Action.CREATE),
    ("PUT", r"/v2/country-packs/.*$"): RoutePermission(Module.SETTINGS, Action.UPDATE),

    # Autoconfig v2
    ("GET", r"/v2/autoconfig/.*$"): RoutePermission(Module.SETTINGS, Action.READ),
    ("POST", r"/v2/autoconfig/.*$"): RoutePermission(Module.SETTINGS, Action.UPDATE),
    ("PUT", r"/v2/autoconfig/.*$"): RoutePermission(Module.SETTINGS, Action.UPDATE),
    ("DELETE", r"/v2/autoconfig/.*$"): RoutePermission(Module.SETTINGS, Action.DELETE),

    # =========================================================================
    # API V2 - MODULES ADDITIONNELS (24 modules migrés)
    # =========================================================================

    # IAM v2 - SECURITE CRITIQUE
    ("GET", r"/v2/iam/users/?$"): RoutePermission(Module.USERS, Action.READ),
    ("GET", r"/v2/iam/users/[0-9a-fA-F-]+$"): RoutePermission(Module.USERS, Action.READ),
    ("POST", r"/v2/iam/users/?$"): RoutePermission(Module.USERS, Action.CREATE),
    ("PUT", r"/v2/iam/users/[0-9a-fA-F-]+$"): RoutePermission(Module.USERS, Action.UPDATE),
    ("DELETE", r"/v2/iam/users/[0-9a-fA-F-]+$"): RoutePermission(Module.USERS, Action.DELETE),
    ("GET", r"/v2/iam/roles/?$"): RoutePermission(Module.USERS, Action.READ),
    ("POST", r"/v2/iam/roles/?$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("PUT", r"/v2/iam/roles/[0-9a-fA-F-]+$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("DELETE", r"/v2/iam/roles/[0-9a-fA-F-]+$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("POST", r"/v2/iam/roles/assign/?$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("POST", r"/v2/iam/roles/revoke/?$"): RoutePermission(Module.USERS, Action.ASSIGN),
    ("POST", r"/v2/iam/users/[0-9a-fA-F-]+/lock/?$"): RoutePermission(Module.SECURITY, Action.UPDATE),
    ("POST", r"/v2/iam/users/[0-9a-fA-F-]+/unlock/?$"): RoutePermission(Module.SECURITY, Action.UPDATE),

    # Backup v2 - SECURITE CRITIQUE
    ("GET", r"/v2/backup/?$"): RoutePermission(Module.SECURITY, Action.READ),
    ("GET", r"/v2/backup/[0-9a-fA-F-]+$"): RoutePermission(Module.SECURITY, Action.READ),
    ("POST", r"/v2/backup/?$"): RoutePermission(Module.SECURITY, Action.ADMIN),
    ("POST", r"/v2/backup/restore/?$"): RoutePermission(Module.SECURITY, Action.ADMIN),
    ("DELETE", r"/v2/backup/[0-9a-fA-F-]+$"): RoutePermission(Module.SECURITY, Action.ADMIN),

    # Tenants v2 - SECURITE CRITIQUE
    ("GET", r"/v2/tenants/?$"): RoutePermission(Module.ORGANIZATION, Action.READ),
    ("GET", r"/v2/tenants/[0-9a-fA-F-]+$"): RoutePermission(Module.ORGANIZATION, Action.READ),
    ("POST", r"/v2/tenants/?$"): RoutePermission(Module.ORGANIZATION, Action.ADMIN),
    ("PUT", r"/v2/tenants/[0-9a-fA-F-]+$"): RoutePermission(Module.ORGANIZATION, Action.UPDATE),
    ("DELETE", r"/v2/tenants/[0-9a-fA-F-]+$"): RoutePermission(Module.ORGANIZATION, Action.ADMIN),

    # Guardian v2
    ("GET", r"/v2/guardian/.*$"): RoutePermission(Module.SECURITY, Action.READ),
    ("POST", r"/v2/guardian/.*$"): RoutePermission(Module.SECURITY, Action.UPDATE),

    # Accounting v2
    ("GET", r"/v2/accounting/.*$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v2/accounting/.*$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/v2/accounting/.*$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/v2/accounting/.*$"): RoutePermission(Module.BILLING, Action.DELETE),

    # Finance v2
    ("GET", r"/v2/finance/.*$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v2/finance/.*$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/v2/finance/.*$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/v2/finance/.*$"): RoutePermission(Module.BILLING, Action.DELETE),

    # Treasury v2
    ("GET", r"/v2/treasury/.*$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v2/treasury/.*$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/v2/treasury/.*$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/v2/treasury/.*$"): RoutePermission(Module.BILLING, Action.DELETE),

    # Procurement v2
    ("GET", r"/v2/procurement/.*$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v2/procurement/.*$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/v2/procurement/.*$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/v2/procurement/.*$"): RoutePermission(Module.BILLING, Action.DELETE),

    # Purchases v2
    ("GET", r"/v2/purchases/.*$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v2/purchases/.*$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/v2/purchases/.*$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/v2/purchases/.*$"): RoutePermission(Module.BILLING, Action.DELETE),

    # POS v2
    ("GET", r"/v2/pos/.*$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v2/pos/.*$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/v2/pos/.*$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/v2/pos/.*$"): RoutePermission(Module.BILLING, Action.DELETE),

    # Ecommerce v2
    ("GET", r"/v2/ecommerce/.*$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v2/ecommerce/.*$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/v2/ecommerce/.*$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/v2/ecommerce/.*$"): RoutePermission(Module.BILLING, Action.DELETE),

    # Inventory v2
    ("GET", r"/v2/inventory/.*$"): RoutePermission(Module.PROJECTS, Action.READ),
    ("POST", r"/v2/inventory/.*$"): RoutePermission(Module.PROJECTS, Action.CREATE),
    ("PUT", r"/v2/inventory/.*$"): RoutePermission(Module.PROJECTS, Action.UPDATE),
    ("DELETE", r"/v2/inventory/.*$"): RoutePermission(Module.PROJECTS, Action.DELETE),

    # Production v2
    ("GET", r"/v2/production/.*$"): RoutePermission(Module.PROJECTS, Action.READ),
    ("POST", r"/v2/production/.*$"): RoutePermission(Module.PROJECTS, Action.CREATE),
    ("PUT", r"/v2/production/.*$"): RoutePermission(Module.PROJECTS, Action.UPDATE),
    ("DELETE", r"/v2/production/.*$"): RoutePermission(Module.PROJECTS, Action.DELETE),

    # Projects v2
    ("GET", r"/v2/projects/.*$"): RoutePermission(Module.PROJECTS, Action.READ),
    ("POST", r"/v2/projects/.*$"): RoutePermission(Module.PROJECTS, Action.CREATE),
    ("PUT", r"/v2/projects/.*$"): RoutePermission(Module.PROJECTS, Action.UPDATE),
    ("DELETE", r"/v2/projects/.*$"): RoutePermission(Module.PROJECTS, Action.DELETE),

    # Maintenance v2
    ("GET", r"/v2/maintenance/.*$"): RoutePermission(Module.PROJECTS, Action.READ),
    ("POST", r"/v2/maintenance/.*$"): RoutePermission(Module.PROJECTS, Action.CREATE),
    ("PUT", r"/v2/maintenance/.*$"): RoutePermission(Module.PROJECTS, Action.UPDATE),
    ("DELETE", r"/v2/maintenance/.*$"): RoutePermission(Module.PROJECTS, Action.DELETE),

    # Field-Service v2
    ("GET", r"/v2/field-service/.*$"): RoutePermission(Module.PROJECTS, Action.READ),
    ("POST", r"/v2/field-service/.*$"): RoutePermission(Module.PROJECTS, Action.CREATE),
    ("PUT", r"/v2/field-service/.*$"): RoutePermission(Module.PROJECTS, Action.UPDATE),
    ("DELETE", r"/v2/field-service/.*$"): RoutePermission(Module.PROJECTS, Action.DELETE),

    # Helpdesk v2
    ("GET", r"/v2/helpdesk/.*$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/v2/helpdesk/.*$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("PUT", r"/v2/helpdesk/.*$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("DELETE", r"/v2/helpdesk/.*$"): RoutePermission(Module.CLIENTS, Action.DELETE),

    # Commercial v2
    ("GET", r"/v2/commercial/.*$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/v2/commercial/.*$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("PUT", r"/v2/commercial/.*$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("DELETE", r"/v2/commercial/.*$"): RoutePermission(Module.CLIENTS, Action.DELETE),

    # Audit v2
    ("GET", r"/v2/audit/.*$"): RoutePermission(Module.AUDIT, Action.READ),
    ("POST", r"/v2/audit/.*$"): RoutePermission(Module.AUDIT, Action.CREATE),

    # BI v2
    ("GET", r"/v2/bi/.*$"): RoutePermission(Module.REPORTING, Action.READ),
    ("POST", r"/v2/bi/.*$"): RoutePermission(Module.REPORTING, Action.CREATE),
    ("PUT", r"/v2/bi/.*$"): RoutePermission(Module.REPORTING, Action.UPDATE),
    ("DELETE", r"/v2/bi/.*$"): RoutePermission(Module.REPORTING, Action.DELETE),

    # Broadcast v2
    ("GET", r"/v2/broadcast/.*$"): RoutePermission(Module.SETTINGS, Action.READ),
    ("POST", r"/v2/broadcast/.*$"): RoutePermission(Module.SETTINGS, Action.CREATE),
    ("PUT", r"/v2/broadcast/.*$"): RoutePermission(Module.SETTINGS, Action.UPDATE),
    ("DELETE", r"/v2/broadcast/.*$"): RoutePermission(Module.SETTINGS, Action.DELETE),

    # Compliance v2
    ("GET", r"/v2/compliance/.*$"): RoutePermission(Module.AUDIT, Action.READ),
    ("POST", r"/v2/compliance/.*$"): RoutePermission(Module.AUDIT, Action.CREATE),
    ("PUT", r"/v2/compliance/.*$"): RoutePermission(Module.AUDIT, Action.UPDATE),

    # QC v2
    ("GET", r"/v2/qc/.*$"): RoutePermission(Module.PROJECTS, Action.READ),
    ("POST", r"/v2/qc/.*$"): RoutePermission(Module.PROJECTS, Action.CREATE),
    ("PUT", r"/v2/qc/.*$"): RoutePermission(Module.PROJECTS, Action.UPDATE),
    ("DELETE", r"/v2/qc/.*$"): RoutePermission(Module.PROJECTS, Action.DELETE),

    # Automated Accounting v2
    ("GET", r"/v2/automated-accounting/.*$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v2/automated-accounting/.*$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/v2/automated-accounting/.*$"): RoutePermission(Module.BILLING, Action.UPDATE),

    # Invoicing v2 (Devis, Factures, Avoirs)
    ("GET", r"/v2/invoicing/quotes/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("GET", r"/v2/invoicing/quotes/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v2/invoicing/quotes/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("PUT", r"/v2/invoicing/quotes/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("DELETE", r"/v2/invoicing/quotes/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.DELETE),
    ("POST", r"/v2/invoicing/quotes/[0-9a-fA-F-]+/send/?$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("GET", r"/v2/invoicing/invoices/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("GET", r"/v2/invoicing/invoices/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v2/invoicing/invoices/?$"): RoutePermission(Module.BILLING, Action.CREATE),
    ("DELETE", r"/v2/invoicing/invoices/[0-9a-fA-F-]+$"): RoutePermission(Module.BILLING, Action.DELETE),
    ("POST", r"/v2/invoicing/invoices/[0-9a-fA-F-]+/send/?$"): RoutePermission(Module.BILLING, Action.UPDATE),
    ("GET", r"/v2/invoicing/credits/?$"): RoutePermission(Module.BILLING, Action.READ),
    ("POST", r"/v2/invoicing/credits/?$"): RoutePermission(Module.BILLING, Action.CREATE),

    # Cockpit v2 (Tableau de bord dirigeant)
    ("GET", r"/v2/cockpit/dashboard/?$"): RoutePermission(Module.REPORTING, Action.READ),
    ("GET", r"/v2/cockpit/decisions/?$"): RoutePermission(Module.REPORTING, Action.READ),
    ("POST", r"/v2/cockpit/alerts/[0-9a-zA-Z_-]+/acknowledge/?$"): RoutePermission(Module.REPORTING, Action.UPDATE),

    # Partners v2 (Clients, Fournisseurs, Contacts)
    ("GET", r"/v2/partners/clients/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("GET", r"/v2/partners/clients/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/v2/partners/clients/?$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("PUT", r"/v2/partners/clients/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("DELETE", r"/v2/partners/clients/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.DELETE),
    ("GET", r"/v2/partners/suppliers/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("GET", r"/v2/partners/suppliers/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/v2/partners/suppliers/?$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("PUT", r"/v2/partners/suppliers/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("DELETE", r"/v2/partners/suppliers/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.DELETE),
    ("GET", r"/v2/partners/contacts/?$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("GET", r"/v2/partners/contacts/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.READ),
    ("POST", r"/v2/partners/contacts/?$"): RoutePermission(Module.CLIENTS, Action.CREATE),
    ("PUT", r"/v2/partners/contacts/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.UPDATE),
    ("DELETE", r"/v2/partners/contacts/[0-9a-fA-F-]+$"): RoutePermission(Module.CLIENTS, Action.DELETE),

    # Decision v2 (Classification decisionnelle)
    ("POST", r"/v2/decision/classify/?$"): RoutePermission(Module.ORGANIZATION, Action.UPDATE),
    ("GET", r"/v2/decision/status/[^/]+/[^/]+$"): RoutePermission(Module.ORGANIZATION, Action.READ),

    # Branding v2 (Configuration visuelle tenant)
    ("GET", r"/v2/branding/?$"): RoutePermission(Module.SETTINGS, Action.READ),
    ("POST", r"/v2/branding/favicon/?$"): RoutePermission(Module.SETTINGS, Action.UPDATE),
    ("POST", r"/v2/branding/logo/?$"): RoutePermission(Module.SETTINGS, Action.UPDATE),
    ("DELETE", r"/v2/branding/favicon/?$"): RoutePermission(Module.SETTINGS, Action.UPDATE),
    ("DELETE", r"/v2/branding/logo/?$"): RoutePermission(Module.SETTINGS, Action.UPDATE),
}


# Routes publiques (pas de vérification RBAC)
PUBLIC_ROUTES: list[str] = [
    r"^/health(/.*)?$",     # /health and all subpaths like /health/ready, /health/live
    r"^/metrics(/.*)?$",    # /metrics and all subpaths like /metrics/json
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
    r"^/api/v2/public/.*$", # Routes publiques API v2 (trial, website, etc.)
]


# Routes semi-publiques (authentification requise mais pas de permission spécifique)
# SECURITE: Eviter les wildcards qui bypssent les permissions granulaires
AUTHENTICATED_ONLY_ROUTES: list[str] = [
    # Profil utilisateur courant (lecture seule de ses propres infos)
    r"^/api/me/?$",
    r"^/api/users/me/?$",
    r"^/api/iam/me/?$",
    r"^/api/iam/users/me/?$",
    r"^/v1/iam/users/me/?$",
    r"^/v1/iam/me/?$",
    r"^/v1/me/.*$",
    # Cockpit dashboard (lecture seule)
    r"^/v1/cockpit/dashboard/?$",
    r"^/v1/cockpit/decisions/?$",
    # Notifications (lecture seule)
    r"^/v1/notifications/?$",
    # Modules disponibles (lecture seule)
    r"^/v1/modules/?$",
    # Tenant courant (lecture seule)
    r"^/v1/tenant/current/?$",
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

        # 1. Routes publiques → passer sans vérification
        if self._is_public_route(path):
            return await call_next(request)

        # 2. Routes authentifiées uniquement (pas de permission spécifique)
        if self._is_authenticated_only_route(path):
            if not self._is_authenticated(request):
                return build_error_response(
                    status_code=401,
                    error_type=ErrorType.AUTHENTICATION,
                    message="Authentification requise",
                    html_path="frontend/errors/401.html"
                )
            return await call_next(request)

        # 3. Trouver la permission requise pour cette route
        # IMPORTANT: Faire ceci AVANT la vérification d'auth pour le mode bêta
        route_perm = self._find_route_permission(method, path)

        if not route_perm:
            # Route non configurée dans RBAC → passer en mode bêta
            # Les endpoints gèrent leur propre authentification via get_current_user
            # En production, activer deny-by-default ci-dessous:
            # logger.warning("Route non configurée dans RBAC: %s %s", method, path)
            # return JSONResponse(
            #     status_code=403,
            #     content={"detail": "Route non autorisée"}
            # )
            return await call_next(request)

        # 4. Route configurée → Vérifier l'authentification
        if not self._is_authenticated(request):
            return build_error_response(
                status_code=401,
                error_type=ErrorType.AUTHENTICATION,
                message="Authentification requise",
                html_path="frontend/errors/401.html"
            )

        # 5. Vérifier la permission
        user = self._get_user(request)
        if not user:
            return build_error_response(
                status_code=401,
                error_type=ErrorType.AUTHENTICATION,
                message="Utilisateur non trouvé",
                html_path="frontend/errors/401.html"
            )

        user_role = self._get_user_role(user)
        if not user_role:
            self._log_denied(request, route_perm, "Rôle non défini")
            return build_error_response(
                status_code=403,
                error_type=ErrorType.AUTHORIZATION,
                message="Rôle utilisateur non défini",
                html_path="frontend/errors/403.html"
            )

        # Vérifier la permission
        permission = check_permission(user_role, route_perm.module, route_perm.action)

        if not permission.allowed:
            self._log_denied(request, route_perm, f"Permission refusée pour {user_role.value}")
            return build_error_response(
                status_code=403,
                error_type=ErrorType.AUTHORIZATION,
                message=f"Accès refusé: {route_perm.module.value}.{route_perm.action.value}",
                html_path="frontend/errors/403.html",
                extra_data={
                    "required_permission": f"{route_perm.module.value}.{route_perm.action.value}"
                }
            )

        # 6. Stocker la restriction pour traitement ultérieur
        request.state.rbac_restriction = permission.restriction
        request.state.rbac_permission = route_perm

        return await call_next(request)

    def _is_public_route(self, path: str) -> bool:
        """Vérifie si la route est publique."""
        return any(re.match(pattern, path) for pattern in PUBLIC_ROUTES)

    def _is_authenticated_only_route(self, path: str) -> bool:
        """Vérifie si la route nécessite seulement l'authentification."""
        return any(re.match(pattern, path) for pattern in AUTHENTICATED_ONLY_ROUTES)

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

    def _get_user_role(self, user) -> StandardRole | None:
        """Récupère le rôle standard de l'utilisateur."""
        # Essayer d'abord l'attribut standard_role
        if hasattr(user, 'standard_role') and user.standard_role:
            try:
                return StandardRole(user.standard_role)
            except ValueError as e:
                logger.warning(
                    "[RBAC_MW] Rôle standard_role invalide, fallback legacy",
                    extra={"standard_role": user.standard_role, "error": str(e)[:200], "consequence": "fallback_legacy_role"}
                )

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

    def _find_route_permission(self, method: str, path: str) -> RoutePermission | None:
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
            "RBAC DENIED: method=%s path=%s "
            "user_id=%s tenant_id=%s "
            "module=%s action=%s "
            "reason=%s",
            request.method, request.url.path, user_id, tenant_id, route_perm.module.value, route_perm.action.value, reason
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
