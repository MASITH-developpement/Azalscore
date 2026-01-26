"""
AZALS - Endpoints Items Multi-Tenant ÉLITE (MIGRÉ CORE SaaS)
=============================================================
CRUD sécurisé avec isolation stricte par tenant_id.
Pagination standardisée pour performance.

✅ MIGRÉ vers CORE SaaS (Phase 2.2):
- Utilise get_saas_context() au lieu de get_tenant_id()
- Prêt pour permissions granulaires si besoin futur
- Exemple de migration réussie
"""


from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
from app.core.models import Item
from app.core.pagination import PaginationParams, get_pagination_params, paginate_query

router = APIRouter(prefix="/items", tags=["items"])


# ===== SCHÉMAS PYDANTIC =====

class ItemCreate(BaseModel):
    """Schéma de création d'un item. tenant_id injecté automatiquement."""
    name: str
    description: str | None = None


class ItemResponse(BaseModel):
    """Schéma de réponse. Inclut tenant_id pour traçabilité."""
    id: int
    tenant_id: str
    name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)


class PaginatedItemsResponse(BaseModel):
    """Réponse paginée pour liste d'items."""
    items: list[ItemResponse]
    total: int | None = None
    page: int
    page_size: int
    pages: int | None = None
    has_next: bool
    has_prev: bool


# ===== ENDPOINTS CRUD =====

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item_data: ItemCreate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Crée un item pour le tenant courant.

    ✅ MIGRÉ CORE SaaS:
    - Utilise SaaSContext (tenant_id + user_id + role + permissions)
    - AUCUNE possibilité de créer pour un autre tenant
    """
    # Création de l'item avec tenant_id depuis SaaSContext
    db_item = Item(
        tenant_id=context.tenant_id,  # Depuis SaaSContext authentifié
        name=item_data.name,
        description=item_data.description
    )

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


@router.get("/", response_model=PaginatedItemsResponse)
def list_items(
    context: SaaSContext = Depends(get_saas_context),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db)
):
    """
    Liste UNIQUEMENT les items du tenant courant.
    Filtrage strict par tenant_id : isolation totale.
    PAGINÉ: Utiliser skip/limit pour performances optimales.

    ✅ MIGRÉ CORE SaaS: Utilise context.tenant_id depuis SaaSContext

    Paramètres:
    - skip: Nombre d'éléments à sauter (défaut: 0)
    - limit: Nombre d'éléments par page (défaut: 50, max: 500)
    - include_total: Inclure le comptage total (défaut: true)
    """
    # Query de base avec filtre tenant
    query = db.query(Item).filter(Item.tenant_id == context.tenant_id).order_by(Item.id)

    # Appliquer la pagination
    result = paginate_query(query, pagination)

    return PaginatedItemsResponse(
        items=[ItemResponse.model_validate(item) for item in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
        has_next=result.has_next,
        has_prev=result.has_prev
    )


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère un item par ID.
    Vérifie que l'item appartient au tenant courant.
    404 si item inexistant OU appartient à un autre tenant.

    ✅ MIGRÉ CORE SaaS: Utilise context.tenant_id
    """
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.tenant_id == context.tenant_id  # Double vérification obligatoire
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
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Met à jour un item du tenant courant.
    Impossible de modifier un item d'un autre tenant.

    ✅ MIGRÉ CORE SaaS: Utilise context.tenant_id
    """
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.tenant_id == context.tenant_id  # Validation tenant obligatoire
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
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Supprime un item du tenant courant.
    Impossible de supprimer un item d'un autre tenant.

    ✅ MIGRÉ CORE SaaS: Utilise context.tenant_id
    """
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.tenant_id == context.tenant_id  # Validation tenant obligatoire
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found or access denied"
        )

    db.delete(item)
    db.commit()

    return None
