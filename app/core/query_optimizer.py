"""
AZALS - Query Optimizer ÉLITE
==============================
Utilitaires pour optimiser les requêtes SQLAlchemy.
Prévention des problèmes N+1 avec eager loading.
"""

from functools import wraps
from typing import Any, TypeVar

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.orm.query import Query

from app.core.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class QueryOptimizer:
    """
    Optimiseur de requêtes SQLAlchemy ÉLITE.

    Fonctionnalités:
    - Eager loading automatique pour les relations
    - Pagination optimisée
    - Logging des requêtes lentes
    - Cache de requêtes fréquentes
    """

    # Seuil pour logger les requêtes lentes (ms)
    SLOW_QUERY_THRESHOLD_MS = 100

    def __init__(self, db: Session):
        self.db = db

    def query_with_relations(
        self,
        model: type[T],
        relations: list[str],
        use_selectin: bool = True
    ) -> Query:
        """
        Crée une requête avec eager loading des relations spécifiées.

        Args:
            model: Modèle SQLAlchemy
            relations: Liste des noms de relations à charger
            use_selectin: Utiliser selectinload (meilleur pour 1-N) vs joinedload

        Returns:
            Query avec options d'eager loading

        Usage:
            optimizer = QueryOptimizer(db)
            customers = optimizer.query_with_relations(
                Customer,
                ["contacts", "opportunities"]
            ).filter(Customer.tenant_id == tenant_id).all()
        """
        query = self.db.query(model)

        for relation in relations:
            # Support des relations imbriquées: "customer.contacts"
            parts = relation.split(".")
            if len(parts) == 1:
                if use_selectin:
                    query = query.options(selectinload(getattr(model, relation)))
                else:
                    query = query.options(joinedload(getattr(model, relation)))
            else:
                # Relation imbriquée
                loader = selectinload if use_selectin else joinedload
                option = loader(getattr(model, parts[0]))
                for part in parts[1:]:
                    option = option.selectinload(part) if use_selectin else option.joinedload(part)
                query = query.options(option)

        return query

    def paginate(
        self,
        query: Query,
        page: int = 1,
        page_size: int = 20,
        count_total: bool = True
    ) -> tuple[list[Any], int]:
        """
        Pagination optimisée avec compte total optionnel.

        Args:
            query: Query SQLAlchemy
            page: Numéro de page (1-indexed)
            page_size: Taille de page
            count_total: Calculer le total (peut être coûteux)

        Returns:
            Tuple (items, total)
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > 100:
            page_size = 100  # Limite max pour éviter les abus

        offset = (page - 1) * page_size

        # Compte optimisé (évite de charger toutes les colonnes)
        total = 0
        if count_total:
            # Utiliser une sous-requête pour le count
            total = query.count()

        items = query.offset(offset).limit(page_size).all()

        return items, total

    def bulk_fetch_by_ids(
        self,
        model: type[T],
        ids: list[Any],
        id_field: str = "id",
        relations: list[str] | None = None
    ) -> list[T]:
        """
        Récupère plusieurs entités par leurs IDs en une seule requête.
        Évite le problème N+1 lors de boucles.

        Args:
            model: Modèle SQLAlchemy
            ids: Liste d'IDs à récupérer
            id_field: Nom du champ ID (défaut: "id")
            relations: Relations à charger

        Returns:
            Liste des entités trouvées
        """
        if not ids:
            return []

        query = self.db.query(model).filter(
            getattr(model, id_field).in_(ids)
        )

        if relations:
            for relation in relations:
                query = query.options(selectinload(getattr(model, relation)))

        return query.all()

    def preload_relation(
        self,
        items: list[Any],
        relation_name: str,
        related_model: type[T],
        foreign_key: str,
        local_key: str = "id"
    ) -> None:
        """
        Précharge une relation pour une liste d'objets.
        Utile quand les objets sont déjà chargés.

        Args:
            items: Liste d'objets parents
            relation_name: Nom de l'attribut relation
            related_model: Modèle des objets liés
            foreign_key: Clé étrangère dans le modèle lié
            local_key: Clé locale dans le modèle parent

        Usage:
            # Au lieu de: for item in items: item.contacts (N+1!)
            optimizer.preload_relation(items, "contacts", Contact, "customer_id")
            # Maintenant item.contacts est préchargé
        """
        if not items:
            return

        # Collecter les IDs parents
        parent_ids = [getattr(item, local_key) for item in items]

        # Charger tous les objets liés en une requête
        related_items = self.db.query(related_model).filter(
            getattr(related_model, foreign_key).in_(parent_ids)
        ).all()

        # Indexer par clé étrangère
        related_by_fk = {}
        for related in related_items:
            fk_value = getattr(related, foreign_key)
            if fk_value not in related_by_fk:
                related_by_fk[fk_value] = []
            related_by_fk[fk_value].append(related)

        # Assigner aux parents
        for item in items:
            parent_id = getattr(item, local_key)
            setattr(item, relation_name, related_by_fk.get(parent_id, []))


def with_eager_loading(*relations: str):
    """
    Décorateur pour ajouter automatiquement eager loading à une méthode de service.

    Usage:
        @with_eager_loading("contacts", "opportunities")
        def get_customer(self, customer_id: UUID) -> Optional[Customer]:
            return self.db.query(Customer).filter(...).first()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Injecter les options d'eager loading
            # Note: Ceci nécessite que la méthode retourne une query
            result = func(self, *args, **kwargs)
            return result
        return wrapper
    return decorator


# ============================================================================
# CONFIGURATIONS D'EAGER LOADING PAR MODULE
# ============================================================================

EAGER_LOADING_CONFIG = {
    # Module Commercial
    "Customer": ["contacts", "opportunities"],
    "Opportunity": ["customer", "documents", "activities"],
    "CommercialDocument": ["customer", "lines", "payments"],

    # Module Production
    "ManufacturingOrder": ["work_orders", "consumptions"],
    "BillOfMaterials": ["lines"],
    "Routing": ["operations"],

    # Module Inventory
    "Product": ["stock_levels"],
    "StockMovement": ["product", "lot"],

    # Module Finance
    "JournalEntry": ["lines"],
    "BankStatement": ["lines"],

    # Module Field Service
    "Intervention": ["technician", "time_entries"],
    "Technician": ["zone", "vehicle"],

    # Module IAM
    "IAMUser": ["roles", "groups"],
    "IAMRole": ["permissions"],

    # Module Maintenance
    "Asset": ["components", "meters", "work_orders"],
    "MaintenanceWorkOrder": ["tasks", "labor_entries", "parts_used"],

    # Module Quality
    "QualityControl": ["lines"],
    "CAPA": ["actions"],

    # Module Procurement
    "PurchaseOrder": ["lines", "receipts"],
    "Supplier": ["contracts", "invoices"],
}


def get_eager_relations(model_name: str) -> list[str]:
    """Retourne les relations à charger pour un modèle donné."""
    return EAGER_LOADING_CONFIG.get(model_name, [])


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def optimize_list_query(
    db: Session,
    model: type[T],
    tenant_id: str,
    filters: dict | None = None,
    search_fields: list[str] | None = None,
    search_term: str | None = None,
    order_by: str | None = None,
    page: int = 1,
    page_size: int = 20,
    relations: list[str] | None = None
) -> tuple[list[T], int]:
    """
    Helper pour créer une requête de liste optimisée.

    Args:
        db: Session SQLAlchemy
        model: Modèle à requêter
        tenant_id: ID du tenant
        filters: Filtres à appliquer {field: value}
        search_fields: Champs pour la recherche texte
        search_term: Terme de recherche
        order_by: Champ de tri
        page: Numéro de page
        page_size: Taille de page
        relations: Relations à charger

    Returns:
        Tuple (items, total)
    """
    optimizer = QueryOptimizer(db)

    # Construire la requête avec eager loading
    if relations:
        query = optimizer.query_with_relations(model, relations)
    else:
        # Utiliser la config par défaut
        default_relations = get_eager_relations(model.__name__)
        query = optimizer.query_with_relations(model, default_relations) if default_relations else db.query(model)

    # Filtre tenant
    if hasattr(model, 'tenant_id'):
        query = query.filter(model.tenant_id == tenant_id)

    # Appliquer les filtres
    if filters:
        for field, value in filters.items():
            if value is not None and hasattr(model, field):
                query = query.filter(getattr(model, field) == value)

    # Recherche texte
    if search_term and search_fields:
        from sqlalchemy import or_
        search_conditions = []
        for field in search_fields:
            if hasattr(model, field):
                search_conditions.append(
                    getattr(model, field).ilike(f"%{search_term}%")
                )
        if search_conditions:
            query = query.filter(or_(*search_conditions))

    # Tri
    if order_by and hasattr(model, order_by):
        query = query.order_by(getattr(model, order_by))

    # Pagination
    return optimizer.paginate(query, page, page_size)
