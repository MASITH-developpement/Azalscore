"""
AZALS - Module d'authentification
=================================

Re-export des fonctions d'authentification depuis dependencies.py
pour compatibilité avec les imports existants.
"""

from app.core.dependencies import (
    get_current_user,
    get_tenant_id,
    get_tenant_db,
    get_current_user_and_tenant
)

__all__ = [
    "get_current_user",
    "get_tenant_id",
    "get_tenant_db",
    "get_current_user_and_tenant"
]
