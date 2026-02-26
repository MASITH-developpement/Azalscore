"""
AZALSCORE - IAM Routers Package
Sous-routers pour le module IAM
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .roles import router as roles_router
from .permissions import router as permissions_router
from .groups import router as groups_router
from .mfa import router as mfa_router
from .invitations import router as invitations_router
from .sessions import router as sessions_router
from .policy import router as policy_router


def create_iam_router() -> APIRouter:
    """Crée le router IAM avec tous les sous-routers."""
    router = APIRouter(prefix="/iam", tags=["iam"])

    # Inclure tous les sous-routers
    router.include_router(auth_router)
    router.include_router(users_router)
    router.include_router(roles_router)
    router.include_router(permissions_router)
    router.include_router(groups_router)
    router.include_router(mfa_router)
    router.include_router(invitations_router)
    router.include_router(sessions_router)
    router.include_router(policy_router)

    return router


__all__ = [
    "create_iam_router",
    "auth_router",
    "users_router",
    "roles_router",
    "permissions_router",
    "groups_router",
    "mfa_router",
    "invitations_router",
    "sessions_router",
    "policy_router",
]
