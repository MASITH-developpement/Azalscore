"""
EXEMPLE D'UTILISATION DU CRUD ROUTER
=====================================

Ce fichier montre comment utiliser CRUDRouter pour réduire le boilerplate.

AVANT: ~80 lignes par ressource CRUD
APRÈS: ~10 lignes par ressource CRUD
"""

# =============================================================================
# AVANT (Pattern actuel - 80+ lignes de boilerplate)
# =============================================================================

"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.compat import get_context
from app.core.database import get_db
from app.core.saas_context import SaaSContext

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    service = ProductService(db, context)
    result = service.create(data)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@router.get("", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    service = ProductService(db, context)
    return service.list(page=page, page_size=page_size)


@router.get("/{id}", response_model=ProductResponse)
async def get_product(
    id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    service = ProductService(db, context)
    result = service.get_or_fail(id)
    if not result.success:
        raise HTTPException(status_code=404, detail=result.error)
    return result.data


@router.put("/{id}", response_model=ProductResponse)
async def update_product(
    id: UUID,
    data: ProductUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    service = ProductService(db, context)
    result = service.update(id, data)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    service = ProductService(db, context)
    result = service.delete(id)
    if not result.success:
        raise HTTPException(status_code=404, detail=result.error)

# Total: ~80 lignes de code répétitif!
"""


# =============================================================================
# APRÈS (Avec CRUDRouter - 10 lignes!)
# =============================================================================

from fastapi import APIRouter, Depends
from uuid import UUID

from app.core.base_router import CRUDRouter, create_simple_crud
from app.core.compat import get_context
from app.core.database import get_db
from app.core.saas_context import SaaSContext

# Imports du module (supposés existants)
# from .service import ProductService
# from .schemas import ProductCreate, ProductUpdate, ProductResponse


# -----------------------------------------------------------------------------
# Méthode 1: CRUDRouter standard
# -----------------------------------------------------------------------------

# products_router = CRUDRouter.create_crud_router(
#     service_class=ProductService,
#     resource_name="product",
#     plural_name="products",
#     create_schema=ProductCreate,
#     update_schema=ProductUpdate,
#     response_schema=ProductResponse,
#     tags=["Inventory - Products"]
# )

# C'est tout! Les 5 endpoints sont créés automatiquement:
# - POST   /products           → Créer
# - GET    /products           → Lister (avec pagination)
# - GET    /products/{id}      → Récupérer
# - PUT    /products/{id}      → Modifier
# - DELETE /products/{id}      → Supprimer


# -----------------------------------------------------------------------------
# Méthode 2: Raccourci encore plus simple
# -----------------------------------------------------------------------------

# products_router = create_simple_crud(
#     ProductService,
#     "product",  # Le pluriel "products" est généré automatiquement
#     ProductCreate,
#     ProductUpdate,
#     ProductResponse
# )


# -----------------------------------------------------------------------------
# Méthode 3: Avec options personnalisées
# -----------------------------------------------------------------------------

# products_router = CRUDRouter.create_crud_router(
#     service_class=ProductService,
#     resource_name="product",
#     plural_name="products",
#     create_schema=ProductCreate,
#     update_schema=ProductUpdate,
#     response_schema=ProductResponse,
#     tags=["Inventory - Products"],
#     include_delete=False,  # Pas de suppression (audit trail)
#     soft_delete=True,      # Soft delete par défaut
# )


# -----------------------------------------------------------------------------
# Ajouter des endpoints métier personnalisés
# -----------------------------------------------------------------------------

# # Après avoir créé le CRUD de base, on peut ajouter des endpoints spécifiques
# @products_router.post("/{id}/duplicate", response_model=ProductResponse)
# async def duplicate_product(
#     id: UUID,
#     context: SaaSContext = Depends(get_context),
#     db = Depends(get_db)
# ):
#     """Endpoint métier personnalisé: dupliquer un produit."""
#     service = ProductService(db, context)
#     return service.duplicate(id)
#
# @products_router.post("/{id}/archive", status_code=204)
# async def archive_product(
#     id: UUID,
#     context: SaaSContext = Depends(get_context),
#     db = Depends(get_db)
# ):
#     """Archiver un produit (au lieu de le supprimer)."""
#     service = ProductService(db, context)
#     service.archive(id)


# -----------------------------------------------------------------------------
# Intégration dans un router principal
# -----------------------------------------------------------------------------

# # Dans votre module router_unified.py:
# router = APIRouter(prefix="/inventory", tags=["Inventory"])
#
# # Inclure le CRUD auto-généré
# router.include_router(products_router)
#
# # Le router expose maintenant:
# # POST   /inventory/products
# # GET    /inventory/products
# # GET    /inventory/products/{id}
# # PUT    /inventory/products/{id}
# # DELETE /inventory/products/{id}
# # POST   /inventory/products/{id}/duplicate (personnalisé)
# # POST   /inventory/products/{id}/archive   (personnalisé)


# =============================================================================
# COMPARAISON
# =============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AVANT vs APRÈS                                    │
├─────────────────────────┬───────────────────────────────────────────────────┤
│ AVANT (Manuel)          │ APRÈS (CRUDRouter)                                │
├─────────────────────────┼───────────────────────────────────────────────────┤
│ 80+ lignes par ressource│ 10 lignes par ressource                          │
│ Copier-coller           │ Généré automatiquement                           │
│ Gestion erreurs manuelle│ Gestion erreurs standardisée                     │
│ Oubli possible sécurité │ Sécurité tenant garantie                         │
│ Documentation manuelle  │ Documentation OpenAPI auto                       │
│ Tests à écrire          │ Tests génériques possibles                       │
└─────────────────────────┴───────────────────────────────────────────────────┘

GAIN: -87% de code boilerplate
"""
