"""
AZALS - Routines Communes
=========================
Fonctions et classes reutilisables pour eviter la duplication de code.

ROUTINES DISPONIBLES:
---------------------
1. require_entity() - Verification existence entite avec 404 automatique
2. TenantRepository - Repository de base avec filtrage tenant automatique
3. CRUDMixin - Mixin pour operations CRUD standardisees
4. update_model() - Mise a jour dynamique de modeles
5. handle_service_errors() - Decorateur gestion erreurs service
6. ServiceFactory - Factory d'injection de services

ATTENTION: Ne pas creer de boucles infinies!
- Ne jamais appeler une routine depuis elle-meme
- Ne pas creer de dependances circulaires entre routines

Usage:
    from app.core.routines import require_entity, TenantRepository, handle_service_errors
"""
from __future__ import annotations


import json
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Generic, Optional, Type, TypeVar

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Type variable pour les modeles generiques
T = TypeVar('T')
ModelType = TypeVar('ModelType')


# =============================================================================
# ROUTINE 1: REQUIRE_ENTITY - Verification existence avec 404 automatique
# =============================================================================
# Remplace le pattern:
#   if not entity:
#       raise HTTPException(status_code=404, detail="Entity not found")
# =============================================================================

def require_entity(
    entity: Optional[T],
    entity_name: str,
    entity_id: Any = None,
    status_code: int = 404
) -> T:
    """
    Verifie qu'une entite existe, sinon leve HTTPException 404.

    Args:
        entity: L'entite a verifier (peut etre None)
        entity_name: Nom de l'entite pour le message d'erreur
        entity_id: ID optionnel pour message plus precis
        status_code: Code HTTP a retourner (defaut 404)

    Returns:
        L'entite si elle existe

    Raises:
        HTTPException: Si l'entite est None

    Example:
        # Avant:
        trigger = service.get_trigger(trigger_id)
        if not trigger:
            raise HTTPException(status_code=404, detail="Trigger non trouve")

        # Apres:
        trigger = require_entity(service.get_trigger(trigger_id), "Trigger", trigger_id)
    """
    if entity is None:
        detail = f"{entity_name} non trouve"
        if entity_id is not None:
            detail = f"{entity_name} avec id={entity_id} non trouve"
        logger.warning("[REQUIRE_ENTITY] %s", detail)
        raise HTTPException(status_code=status_code, detail=detail)
    return entity


def require_entities(
    entities: list,
    entity_name: str,
    allow_empty: bool = False
) -> list:
    """
    Verifie qu'une liste d'entites n'est pas None/vide.

    Args:
        entities: Liste d'entites
        entity_name: Nom pour le message d'erreur
        allow_empty: Si True, autorise liste vide (defaut False)

    Returns:
        La liste si valide

    Raises:
        HTTPException: Si la liste est None ou vide (si allow_empty=False)
    """
    if entities is None:
        raise HTTPException(
            status_code=404,
            detail=f"Aucun {entity_name} trouve"
        )
    if not allow_empty and len(entities) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Aucun {entity_name} trouve"
        )
    return entities


# =============================================================================
# ROUTINE 2: TENANT_REPOSITORY - Repository avec filtrage tenant automatique
# =============================================================================
# Remplace le pattern:
#   self.db.query(Model).filter(Model.tenant_id == self.tenant_id)
# =============================================================================

class TenantRepository(Generic[ModelType]):
    """
    Repository de base avec filtrage automatique par tenant_id.

    Garantit l'isolation multi-tenant sur toutes les operations.

    Example:
        class ProductRepository(TenantRepository[Product]):
            def __init__(self, db: Session, tenant_id: str):
                super().__init__(db, tenant_id, Product)

            def get_active_products(self):
                return self.query().filter(Product.is_active == True).all()

        # Usage
        repo = ProductRepository(db, tenant_id)
        product = repo.get_by_id(product_id)  # Filtre tenant automatique
    """

    def __init__(self, db: Session, tenant_id: str, model_class: Type[ModelType]):
        """
        Initialise le repository.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant pour le filtrage
            model_class: Classe du modele SQLAlchemy
        """
        self.db = db
        self.tenant_id = tenant_id
        self.model = model_class

    def query(self):
        """
        Retourne une query pre-filtree par tenant_id.

        Returns:
            Query SQLAlchemy avec filtre tenant applique
        """
        return self.db.query(self.model).filter(
            self.model.tenant_id == self.tenant_id
        )

    def get_by_id(self, entity_id: Any) -> Optional[ModelType]:
        """
        Recupere une entite par ID avec filtre tenant.

        Args:
            entity_id: ID de l'entite

        Returns:
            L'entite ou None si non trouvee
        """
        return self.query().filter(self.model.id == entity_id).first()

    def get_by_id_or_404(self, entity_id: Any, entity_name: str = None) -> ModelType:
        """
        Recupere une entite par ID ou leve 404.

        Args:
            entity_id: ID de l'entite
            entity_name: Nom pour le message d'erreur (optionnel)

        Returns:
            L'entite

        Raises:
            HTTPException 404 si non trouvee
        """
        entity = self.get_by_id(entity_id)
        name = entity_name or self.model.__name__
        return require_entity(entity, name, entity_id)

    def list_all(
        self,
        skip: int = 0,
        limit: int = 50,
        order_by: Any = None
    ) -> list[ModelType]:
        """
        Liste toutes les entites du tenant avec pagination.

        Args:
            skip: Nombre d'elements a sauter
            limit: Nombre max d'elements (defaut 50)
            order_by: Colonne de tri optionnelle

        Returns:
            Liste des entites
        """
        query = self.query()
        if order_by is not None:
            query = query.order_by(order_by)
        return query.offset(skip).limit(limit).all()

    def count(self) -> int:
        """Compte le nombre d'entites du tenant."""
        return self.query().count()

    def exists(self, entity_id: Any) -> bool:
        """Verifie si une entite existe."""
        return self.get_by_id(entity_id) is not None


# =============================================================================
# ROUTINE 3: CRUD_MIXIN - Operations CRUD standardisees
# =============================================================================
# Remplace les patterns:
#   self.db.add(entity); self.db.commit(); self.db.refresh(entity)
#   self.db.delete(entity); self.db.commit()
# =============================================================================

class CRUDMixin:
    """
    Mixin fournissant les operations CRUD standardisees.

    A utiliser avec TenantRepository ou tout service avec self.db.

    Example:
        class ProductService(TenantRepository[Product], CRUDMixin):
            def create_product(self, data: ProductCreate) -> Product:
                product = Product(
                    tenant_id=self.tenant_id,
                    name=data.name,
                    price=data.price
                )
                return self.create(product)  # Herite de CRUDMixin
    """

    db: Session  # Doit etre defini par la classe parente
    tenant_id: str  # Doit etre defini par la classe parente

    def create(self, entity: T) -> T:
        """
        Cree une entite (add + commit + refresh).

        Args:
            entity: Instance du modele a creer

        Returns:
            L'entite creee avec son ID
        """
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        logger.debug("[CRUD] Created %s id=%s", type(entity).__name__, entity.id)
        return entity

    def update(self, entity: T) -> T:
        """
        Met a jour une entite (commit + refresh).

        Args:
            entity: Instance du modele modifiee

        Returns:
            L'entite mise a jour
        """
        self.db.commit()
        self.db.refresh(entity)
        logger.debug("[CRUD] Updated %s id=%s", type(entity).__name__, entity.id)
        return entity

    def delete(self, entity: T) -> bool:
        """
        Supprime une entite.

        Args:
            entity: Instance du modele a supprimer

        Returns:
            True si supprime
        """
        entity_id = entity.id
        entity_type = type(entity).__name__
        self.db.delete(entity)
        self.db.commit()
        logger.debug("[CRUD] Deleted %s id=%s", entity_type, entity_id)
        return True

    def soft_delete(self, entity: T, field: str = "is_deleted") -> T:
        """
        Suppression logique (marque comme supprime).

        Args:
            entity: Instance du modele
            field: Nom du champ booleen (defaut "is_deleted")

        Returns:
            L'entite mise a jour
        """
        if hasattr(entity, field):
            setattr(entity, field, True)
            return self.update(entity)
        raise ValueError(f"Le modele n'a pas de champ '{field}'")

    @contextmanager
    def persist(self, entity: T):
        """
        Context manager pour creation avec rollback automatique sur erreur.

        Example:
            with self.persist(new_product) as product:
                # Modifications additionnelles
                pass
            # Automatiquement commit et refresh
        """
        try:
            self.db.add(entity)
            yield entity
            self.db.commit()
            self.db.refresh(entity)
        except Exception as e:
            logger.error(
                "[CRUD_PERSIST] Échec persistance entité — rollback",
                extra={"error": str(e)[:300], "consequence": "transaction_rolled_back"}
            )
            self.db.rollback()
            raise


# =============================================================================
# ROUTINE 4: UPDATE_MODEL - Mise a jour dynamique de modeles
# =============================================================================
# Remplace le pattern:
#   for field, value in data.model_dump(exclude_unset=True).items():
#       setattr(model, field, value)
# =============================================================================

def update_model(
    model_instance: T,
    update_data: Dict[str, Any],
    exclude_fields: set = None,
    serializers: Dict[str, Callable] = None
) -> T:
    """
    Met a jour un modele avec des donnees dynamiques.

    Args:
        model_instance: Instance SQLAlchemy a mettre a jour
        update_data: Dictionnaire des champs a mettre a jour
        exclude_fields: Set de champs a ignorer (ex: {"id", "tenant_id"})
        serializers: Dict de fonctions de serialisation par champ

    Returns:
        Le modele mis a jour

    Example:
        # Avant:
        for field, value in data.model_dump(exclude_unset=True).items():
            if field == 'available_variables' and value:
                value = json.dumps(value)
            setattr(template, field, value)

        # Apres:
        update_model(
            template,
            data.model_dump(exclude_unset=True),
            exclude_fields={"id", "tenant_id"},
            serializers={"available_variables": json.dumps}
        )
    """
    exclude_fields = exclude_fields or {"id", "tenant_id", "created_at"}
    serializers = serializers or {}

    updated_fields = []
    for field, value in update_data.items():
        # Ignorer les champs exclus
        if field in exclude_fields:
            continue

        # Ignorer si le modele n'a pas ce champ
        if not hasattr(model_instance, field):
            continue

        # Ignorer les valeurs None (sauf si explicitement voulu)
        if value is None:
            continue

        # Appliquer le serializer si defini
        if field in serializers and value is not None:
            value = serializers[field](value)

        setattr(model_instance, field, value)
        updated_fields.append(field)

    if updated_fields:
        logger.debug("[UPDATE_MODEL] Updated fields: %s", updated_fields)

    return model_instance


def update_model_from_schema(
    model_instance: T,
    schema,
    exclude_fields: set = None,
    serializers: Dict[str, Callable] = None
) -> T:
    """
    Met a jour un modele depuis un schema Pydantic.

    Args:
        model_instance: Instance SQLAlchemy
        schema: Schema Pydantic avec les nouvelles valeurs
        exclude_fields: Champs a ignorer
        serializers: Fonctions de serialisation

    Returns:
        Le modele mis a jour

    Example:
        update_model_from_schema(
            product,
            product_update_schema,
            serializers={"metadata": json.dumps}
        )
    """
    return update_model(
        model_instance,
        schema.model_dump(exclude_unset=True),
        exclude_fields,
        serializers
    )


# =============================================================================
# ROUTINE 5: HANDLE_SERVICE_ERRORS - Decorateur gestion erreurs
# =============================================================================
# Remplace le pattern:
#   try:
#       result = service.do_something()
#   except ValueError as e:
#       raise HTTPException(status_code=400, detail=str(e))
# =============================================================================

def handle_service_errors(
    exception_map: Dict[Type[Exception], int] = None,
    default_status: int = 400,
    log_errors: bool = True
):
    """
    Decorateur pour convertir les exceptions service en HTTPException.

    Args:
        exception_map: Mapping exception -> code HTTP
        default_status: Code par defaut pour exceptions non mappees
        log_errors: Si True, log les erreurs (defaut True)

    Example:
        @router.post("/triggers")
        @handle_service_errors({
            ValueError: 400,
            KeyError: 404,
            PermissionError: 403
        })
        async def create_trigger(data: TriggerCreate):
            return service.create_trigger(data)
    """
    default_map = {
        ValueError: 400,
        KeyError: 404,
        PermissionError: 403,
        FileNotFoundError: 404,
    }

    final_map = {**default_map, **(exception_map or {})}

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTPException as-is
                raise
            except Exception as e:
                status_code = final_map.get(type(e), default_status)
                if log_errors:
                    logger.warning(
                        "[SERVICE_ERROR] %s: %s", type(e).__name__, e,
                        extra={"status_code": status_code}
                    )
                raise HTTPException(status_code=status_code, detail=str(e))

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                status_code = final_map.get(type(e), default_status)
                if log_errors:
                    logger.warning(
                        "[SERVICE_ERROR] %s: %s", type(e).__name__, e,
                        extra={"status_code": status_code}
                    )
                raise HTTPException(status_code=status_code, detail=str(e))

        # Detecter si la fonction est async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# =============================================================================
# ROUTINE 6: SERVICE_FACTORY - Factory injection services
# =============================================================================
# Remplace le pattern repete dans chaque router:
#   def get_service(db: Session = Depends(get_db)):
#       tenant_id = request.state.tenant_id
#       return MyService(db, tenant_id)
# =============================================================================

class ServiceFactory:
    """
    Factory pour injection standardisee de services.

    Example:
        # Definition
        factory = ServiceFactory(TriggerService)

        # Usage dans router
        @router.get("/triggers")
        def list_triggers(service: TriggerService = Depends(factory)):
            return service.list_triggers()
    """

    def __init__(
        self,
        service_class: Type[T],
        require_user: bool = False,
        require_tenant: bool = True
    ):
        """
        Configure la factory.

        Args:
            service_class: Classe du service a instancier
            require_user: Si True, injecte aussi current_user
            require_tenant: Si True, requiert tenant_id (defaut True)
        """
        self.service_class = service_class
        self.require_user = require_user
        self.require_tenant = require_tenant

    def __call__(
        self,
        request: Request,
        db: Session = Depends(get_db)
    ) -> T:
        """
        Cree une instance du service.

        Note: Les imports sont faits ici pour eviter les imports circulaires.
        """
        kwargs = {"db": db}

        # Ajouter tenant_id si requis
        if self.require_tenant:
            if hasattr(request.state, "tenant_id"):
                kwargs["tenant_id"] = request.state.tenant_id
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Tenant ID requis"
                )

        # Ajouter user_id si requis
        if self.require_user:
            # Note: Ceci necessite que l'auth soit deja passee
            user = getattr(request.state, "user", None)
            if user:
                kwargs["user_id"] = user.id

        return self.service_class(**kwargs)


def create_service_dependency(
    service_class: Type[T],
    require_user: bool = False
) -> Callable:
    """
    Cree une dependance FastAPI pour un service.

    Args:
        service_class: Classe du service
        require_user: Si True, requiert authentification

    Returns:
        Fonction de dependance FastAPI

    Example:
        get_trigger_service = create_service_dependency(TriggerService)

        @router.get("/triggers")
        def list_triggers(service = Depends(get_trigger_service)):
            return service.list_all()
    """
    def dependency(
        request: Request,
        db: Session = Depends(get_db)
    ) -> T:
        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            raise HTTPException(status_code=401, detail="Tenant ID requis")

        kwargs = {"db": db, "tenant_id": tenant_id}

        if require_user:
            user = getattr(request.state, "user", None)
            if user:
                kwargs["user_id"] = user.id

        return service_class(**kwargs)

    return dependency


# =============================================================================
# ROUTINE 7: PAGINATION - Pagination standardisee
# =============================================================================

def paginate(
    query,
    page: int = 1,
    page_size: int = 25,
    max_page_size: int = 100
) -> Dict[str, Any]:
    """
    Applique la pagination a une query et retourne le resultat formate.

    Args:
        query: Query SQLAlchemy
        page: Numero de page (1-indexed)
        page_size: Taille de page
        max_page_size: Taille max autorisee

    Returns:
        Dict avec items, total, page, page_size, pages

    Example:
        result = paginate(
            service.query().filter(Product.active == True),
            page=2,
            page_size=10
        )
        # Returns: {"items": [...], "total": 100, "page": 2, "page_size": 10, "pages": 10}
    """
    # Limiter page_size
    page_size = min(page_size, max_page_size)
    page = max(1, page)

    # Compter le total
    total = query.count()

    # Calculer le nombre de pages
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    # Recuperer les items
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


# =============================================================================
# ROUTINE 8: VALIDATION HELPERS
# =============================================================================

def validate_uuid(value: str, field_name: str = "ID") -> str:
    """
    Valide qu'une string est un UUID valide.

    Args:
        value: String a valider
        field_name: Nom du champ pour le message d'erreur

    Returns:
        La valeur si valide

    Raises:
        HTTPException 400 si invalide
    """
    import uuid
    try:
        uuid.UUID(value)
        return value
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} invalide: doit etre un UUID"
        )


def validate_enum(value: Any, enum_class: Type, field_name: str = "valeur") -> Any:
    """
    Valide qu'une valeur appartient a un enum.

    Args:
        value: Valeur a valider
        enum_class: Classe Enum
        field_name: Nom du champ pour le message d'erreur

    Returns:
        La valeur si valide

    Raises:
        HTTPException 400 si invalide
    """
    try:
        if isinstance(value, str):
            return enum_class(value)
        return value
    except ValueError:
        valid_values = [e.value for e in enum_class]
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} invalide. Valeurs acceptees: {valid_values}"
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Routine 1
    "require_entity",
    "require_entities",
    # Routine 2
    "TenantRepository",
    # Routine 3
    "CRUDMixin",
    # Routine 4
    "update_model",
    "update_model_from_schema",
    # Routine 5
    "handle_service_errors",
    # Routine 6
    "ServiceFactory",
    "create_service_dependency",
    # Routine 7
    "paginate",
    # Routine 8
    "validate_uuid",
    "validate_enum",
]
