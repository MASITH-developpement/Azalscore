"""
OBSOLÈTE - REMPLACÉ PAR core_auth_middleware.py
================================================

Ce fichier est maintenant obsolète et sera supprimé dans une future version.

MIGRATION:
- Ancien: AuthMiddleware (ce fichier)
- Nouveau: CoreAuthMiddleware (app/core/core_auth_middleware.py)

Le nouveau middleware utilise CORE.authenticate() pour éviter la duplication
de logique d'authentification.

RAISON DE LA MIGRATION:
- Centralisation de toute la logique d'authentification dans CORE
- Évite la duplication (parsing JWT, chargement user, vérification tenant)
- Utilise SaaSContext immuable au lieu de User mutable
- Audit automatique via CORE

VOIR:
- app/core/core_auth_middleware.py
- app/core/saas_core.py
- REFACTOR_SAAS_SIMPLIFICATION.md (Phase 2)
"""

# Ce fichier ne doit plus être importé.
# L'import de AuthMiddleware lèvera une erreur pour forcer la migration.

raise ImportError(
    "AuthMiddleware is obsolete. "
    "Use CoreAuthMiddleware from app.core.core_auth_middleware instead. "
    "See REFACTOR_SAAS_SIMPLIFICATION.md Phase 2 for migration guide."
)
