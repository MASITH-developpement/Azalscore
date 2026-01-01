"""
AZALS - Endpoint exemple protégé par JWT + Tenant
Démonstration de l'utilisation de get_current_user
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.models import User, Item
from app.core.dependencies import get_current_user
from app.core.database import get_db
from app.api.items import ItemResponse


router = APIRouter(prefix="/me", tags=["protected"])


@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    """
    Endpoint protégé : profil utilisateur.
    Nécessite JWT valide + X-Tenant-ID cohérent.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "tenant_id": current_user.tenant_id,
        "role": current_user.role.value,
        "is_active": current_user.is_active
    }


@router.get("/items", response_model=List[ItemResponse])
def get_my_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint protégé : liste les items du tenant de l'utilisateur.
    Double sécurité :
    1. JWT valide + cohérence tenant (get_current_user)
    2. Filtrage SQL par tenant_id
    """
    items = db.query(Item).filter(
        Item.tenant_id == current_user.tenant_id
    ).all()
    
    return items
