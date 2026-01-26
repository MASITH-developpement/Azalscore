"""
AZALS - Endpoint exemple protégé par JWT + Tenant (MIGRÉ CORE SaaS)
====================================================================
Démonstration de l'utilisation de get_saas_context

✅ MIGRÉ vers CORE SaaS (Phase 2.2):
- Utilise get_saas_context() au lieu de get_current_user()
- SaaSContext fournit: tenant_id, user_id, role, permissions
- Audit automatique via CoreAuthMiddleware
- Exemple de migration réussie
"""


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.items import ItemResponse
from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
from app.core.models import Item, User

router = APIRouter(prefix="/me", tags=["protected"])


@router.get("/profile")
def get_profile(context: SaaSContext = Depends(get_saas_context)):
    """
    Endpoint protégé : profil utilisateur.
    Nécessite JWT valide + X-Tenant-ID cohérent.

    ✅ MIGRÉ CORE SaaS:
    - Utilise SaaSContext au lieu de User
    - Accès direct à user_id, tenant_id, role via context
    - Audit automatique via CORE.authenticate()

    NOTE: email n'est plus dans SaaSContext (ne contient que ce qui est dans le JWT).
    Si besoin de l'email, charger User depuis la DB avec context.user_id.
    """
    return {
        "id": context.user_id,
        "tenant_id": context.tenant_id,
        "role": context.role.value,
        "scope": context.scope.value,
        "permissions_count": len(context.permissions),
        # NOTE: Pour récupérer l'email, il faut charger User depuis DB si besoin
        # email: Voir exemple dans get_profile_full() ci-dessous
    }


@router.get("/profile/full")
def get_profile_full(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Profil complet avec données DB (email, etc.).

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour charger User si besoin de données DB
    - SaaSContext ne contient que ce qui est dans le JWT
    """
    # Charger User depuis DB pour infos complètes
    user = db.query(User).filter(
        User.id == context.user_id,
        User.tenant_id == context.tenant_id
    ).first()

    if not user:
        # Ne devrait jamais arriver (user authentifié par CORE)
        return {"error": "User not found"}

    return {
        "id": user.id,
        "email": user.email,
        "tenant_id": user.tenant_id,
        "role": user.role.value,
        "is_active": user.is_active,
        "totp_enabled": user.totp_enabled,
        # Infos SaaSContext
        "context": {
            "scope": context.scope.value,
            "permissions_count": len(context.permissions),
            "ip_address": context.ip_address,
            "correlation_id": context.correlation_id,
        }
    }


@router.get("/items", response_model=list[ItemResponse])
def get_my_items(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Endpoint protégé : liste les items du tenant de l'utilisateur.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id au lieu de current_user.tenant_id
    - Double sécurité :
      1. JWT valide + cohérence tenant (CORE.authenticate via CoreAuthMiddleware)
      2. Filtrage SQL par context.tenant_id
    """
    items = db.query(Item).filter(
        Item.tenant_id == context.tenant_id
    ).all()

    return items


@router.get("/context")
def get_context_info(context: SaaSContext = Depends(get_saas_context)):
    """
    Endpoint de démo : affiche le SaaSContext complet.

    Utile pour comprendre ce que contient le contexte après authentification.
    """
    return {
        "tenant_id": context.tenant_id,
        "user_id": str(context.user_id),
        "role": context.role.value,
        "scope": context.scope.value,
        "permissions": list(context.permissions)[:10],  # Premiers 10 pour lisibilité
        "permissions_count": len(context.permissions),
        "is_creator": context.is_creator,
        "is_dirigeant": context.is_dirigeant,
        "is_admin": context.is_admin,
        "audit_info": {
            "ip_address": context.ip_address,
            "user_agent": context.user_agent,
            "correlation_id": context.correlation_id,
            "timestamp": context.timestamp.isoformat(),
        }
    }
