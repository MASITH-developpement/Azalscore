"""
AZALS - Utilitaires de Pagination ÉLITE
=========================================
Pagination standardisée avec métadonnées complètes.
Optimisé pour performance avec count optionnel.
"""

from typing import TypeVar, Generic, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from fastapi import Query
from sqlalchemy.orm import Query as SQLQuery
from math import ceil


T = TypeVar('T')


class PaginationParams(BaseModel):
    """Paramètres de pagination standardisés."""
    skip: int = Field(default=0, ge=0, description="Nombre d'éléments à sauter")
    limit: int = Field(default=50, ge=1, le=500, description="Nombre d'éléments par page")
    include_total: bool = Field(default=True, description="Inclure le total (coûteux sur grandes tables)")

    @property
    def page(self) -> int:
        """Numéro de page calculé (1-indexed)."""
        return (self.skip // self.limit) + 1 if self.limit > 0 else 1


class PaginatedResponse(BaseModel, Generic[T]):
    """Réponse paginée standardisée."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: List[T]
    total: Optional[int] = None
    page: int
    page_size: int
    pages: Optional[int] = None
    has_next: bool
    has_prev: bool


def get_pagination_params(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(50, ge=1, le=500, description="Nombre d'éléments par page (max 500)"),
    include_total: bool = Query(True, description="Inclure le total (peut ralentir sur grandes tables)")
) -> PaginationParams:
    """
    Dépendance FastAPI pour récupérer les paramètres de pagination.

    Utilisation:
        @router.get("/items")
        def list_items(pagination: PaginationParams = Depends(get_pagination_params)):
            ...
    """
    return PaginationParams(skip=skip, limit=limit, include_total=include_total)


def paginate_query(
    query: SQLQuery,
    pagination: PaginationParams,
    serializer: Optional[callable] = None
) -> PaginatedResponse:
    """
    Applique la pagination à une query SQLAlchemy.

    Args:
        query: Query SQLAlchemy à paginer
        pagination: Paramètres de pagination
        serializer: Fonction optionnelle pour sérialiser les résultats

    Returns:
        PaginatedResponse avec les items et métadonnées
    """
    total = None
    pages = None

    # Count optionnel (évite count() sur très grandes tables)
    if pagination.include_total:
        total = query.count()
        pages = ceil(total / pagination.limit) if pagination.limit > 0 else 1

    # Récupérer les items avec offset/limit
    items = query.offset(pagination.skip).limit(pagination.limit).all()

    # Sérialisation optionnelle
    if serializer:
        items = [serializer(item) for item in items]

    # Calcul has_next/has_prev
    has_prev = pagination.skip > 0
    if total is not None:
        has_next = (pagination.skip + pagination.limit) < total
    else:
        # Si pas de total, on vérifie si on a reçu le max d'items
        has_next = len(items) == pagination.limit

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.limit,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )


def paginate_list(
    items: List[Any],
    pagination: PaginationParams,
    serializer: Optional[callable] = None
) -> PaginatedResponse:
    """
    Pagine une liste Python (pour données en mémoire).

    Args:
        items: Liste à paginer
        pagination: Paramètres de pagination
        serializer: Fonction optionnelle pour sérialiser les résultats

    Returns:
        PaginatedResponse avec les items paginés
    """
    total = len(items)
    pages = ceil(total / pagination.limit) if pagination.limit > 0 else 1

    # Slice de la liste
    start = pagination.skip
    end = start + pagination.limit
    paginated_items = items[start:end]

    # Sérialisation optionnelle
    if serializer:
        paginated_items = [serializer(item) for item in paginated_items]

    return PaginatedResponse(
        items=paginated_items,
        total=total,
        page=pagination.page,
        page_size=pagination.limit,
        pages=pages,
        has_next=end < total,
        has_prev=start > 0
    )


# Constantes pour limites par type d'endpoint
class PaginationLimits:
    """Limites de pagination par type d'endpoint."""
    DEFAULT = 50
    SMALL = 20      # Pour sous-ressources (comments, attachments)
    MEDIUM = 100    # Pour listes principales
    LARGE = 200     # Pour exports/rapports
    MAX = 500       # Maximum absolu


# Helper pour créer des réponses de pagination personnalisées
def create_pagination_response(
    items: List[Any],
    total: Optional[int],
    skip: int,
    limit: int
) -> dict:
    """
    Crée une réponse de pagination standard (dict).
    Pour les cas où PaginatedResponse n'est pas souhaité.
    """
    page = (skip // limit) + 1 if limit > 0 else 1
    pages = ceil(total / limit) if total and limit > 0 else None

    has_prev = skip > 0
    has_next = (total is not None and (skip + limit) < total) or (total is None and len(items) == limit)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": limit,
        "pages": pages,
        "has_next": has_next,
        "has_prev": has_prev
    }
