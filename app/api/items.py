"""
AZALS - Endpoints Items Multi-Tenant
CRUD sécurisé avec isolation stricte par tenant_id
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.models import Item
from app.core.dependencies import get_tenant_id
from app.core.database import get_db


router = APIRouter(prefix="/items", tags=["items"])


# ===== SCHÉMAS PYDANTIC =====

class ItemCreate(BaseModel):
    """Schéma de création d'un item. tenant_id injecté automatiquement."""
    name: str
    description: Optional[str] = None


class ItemResponse(BaseModel):
    """Schéma de réponse. Inclut tenant_id pour traçabilité."""
    id: int
    tenant_id: str
    name: str
    description: Optional[str]
    
    model_config = {"from_attributes": True}


# ===== ENDPOINTS CRUD =====

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item_data: ItemCreate,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Crée un item pour le tenant courant.
    Le tenant_id est injecté automatiquement depuis X-Tenant-ID.
    AUCUNE possibilité de créer pour un autre tenant.
    """
    # Création de l'item avec tenant_id forcé
    db_item = Item(
        tenant_id=tenant_id,  # Forcé depuis le header validé
        name=item_data.name,
        description=item_data.description
    )
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item


@router.get("/", response_model=List[ItemResponse])
def list_items(
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Liste UNIQUEMENT les items du tenant courant.
    Filtrage strict par tenant_id : isolation totale.
    """
    items = db.query(Item).filter(Item.tenant_id == tenant_id).all()
    return items


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Récupère un item par ID.
    Vérifie que l'item appartient au tenant courant.
    404 si item inexistant OU appartient à un autre tenant.
    """
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.tenant_id == tenant_id  # Double vérification obligatoire
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found or access denied"
        )
    
    return item


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item_data: ItemCreate,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Met à jour un item du tenant courant.
    Impossible de modifier un item d'un autre tenant.
    """
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.tenant_id == tenant_id  # Validation tenant obligatoire
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found or access denied"
        )
    
    # Mise à jour des champs
    item.name = item_data.name
    item.description = item_data.description
    
    db.commit()
    db.refresh(item)
    
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Supprime un item du tenant courant.
    Impossible de supprimer un item d'un autre tenant.
    """
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.tenant_id == tenant_id  # Validation tenant obligatoire
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found or access denied"
        )
    
    db.delete(item)
    db.commit()
    
    return None
