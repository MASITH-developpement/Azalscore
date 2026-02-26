"""
AZALS - CRUDRouter: Générateur automatique d'endpoints CRUD
=============================================================

Élimine le boilerplate répétitif en générant automatiquement les 5 endpoints
CRUD standards (Create, Read, Update, Delete, List) pour chaque ressource.

AVANTAGES:
- Réduit ~80 lignes de code par ressource à ~10 lignes
- Garantit la sécurité tenant automatiquement (via get_context)
- Standardise la gestion d'erreurs et les codes HTTP
- Documentation OpenAPI auto-générée

USAGE:
    from app.core.base_router import CRUDRouter

    # Génère automatiquement POST, GET, PUT, DELETE, LIST
    customers_router = CRUDRouter.create_crud_router(
        service_class=CustomerService,
        resource_name="customer",
        plural_name="customers",
        create_schema=CustomerCreate,
        update_schema=CustomerUpdate,
        response_schema=CustomerResponse,
        tags=["Commercial - Clients"]
    )

    # Ajouter au router principal
    router = APIRouter(prefix="/commercial")
    router.include_router(customers_router)

    # Ajouter des endpoints métier personnalisés si nécessaire
    @customers_router.post("/{id}/send-email")
    async def send_email(id: UUID, ...):
        ...

Conformité: AZA-NF-007
"""
from __future__ import annotations


import logging
from typing import Any, Callable, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.compat import get_context
from app.core.database import get_db
from app.core.saas_context import SaaSContext
from app.core.pagination import PaginatedResponse

logger = logging.getLogger(__name__)

# Type variables
T = TypeVar('T')  # Model type
CreateSchema = TypeVar('CreateSchema', bound=BaseModel)
UpdateSchema = TypeVar('UpdateSchema', bound=BaseModel)
ResponseSchema = TypeVar('ResponseSchema', bound=BaseModel)


class CRUDRouter:
    """
    Générateur d'endpoints CRUD standardisés.

    Élimine le boilerplate répétitif tout en garantissant:
    - Sécurité multi-tenant (via SaaSContext)
    - Gestion d'erreurs cohérente
    - Pagination standardisée
    - Documentation OpenAPI auto-générée
    """

    # Mapping error_code → HTTP status
    ERROR_STATUS_MAP = {
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "DUPLICATE": status.HTTP_409_CONFLICT,
        "CONFLICT": status.HTTP_409_CONFLICT,
        "INVALID": status.HTTP_400_BAD_REQUEST,
        "VALIDATION": status.HTTP_400_BAD_REQUEST,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "PERMISSION_DENIED": status.HTTP_403_FORBIDDEN,
        "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
    }

    @classmethod
    def create_crud_router(
        cls,
        service_class: Type[Any],
        resource_name: str,
        plural_name: str,
        create_schema: Type[CreateSchema],
        update_schema: Type[UpdateSchema],
        response_schema: Type[ResponseSchema],
        prefix: str = "",
        tags: Optional[List[str]] = None,
        list_filters: Optional[List[str]] = None,
        include_create: bool = True,
        include_read: bool = True,
        include_update: bool = True,
        include_delete: bool = True,
        include_list: bool = True,
        soft_delete: bool = True,
        service_factory: Optional[Callable] = None,
    ) -> APIRouter:
        """
        Génère automatiquement les 5 endpoints CRUD standards.

        Args:
            service_class: Classe du service (doit hériter BaseService)
            resource_name: Nom singulier de la ressource (ex: "customer")
            plural_name: Nom pluriel de la ressource (ex: "customers")
            create_schema: Schéma Pydantic pour la création
            update_schema: Schéma Pydantic pour la mise à jour
            response_schema: Schéma Pydantic pour la réponse
            prefix: Préfixe optionnel des routes (ex: "/admin")
            tags: Tags OpenAPI pour la documentation
            list_filters: Champs de filtrage pour le LIST (optionnel)
            include_create: Inclure l'endpoint POST (défaut: True)
            include_read: Inclure l'endpoint GET /{id} (défaut: True)
            include_update: Inclure l'endpoint PUT /{id} (défaut: True)
            include_delete: Inclure l'endpoint DELETE /{id} (défaut: True)
            include_list: Inclure l'endpoint GET / (défaut: True)
            soft_delete: Utiliser soft delete (défaut: True)
            service_factory: Factory custom pour créer le service (optionnel)

        Returns:
            APIRouter avec les endpoints CRUD configurés

        Example:
            # Minimal
            router = CRUDRouter.create_crud_router(
                CustomerService,
                "customer", "customers",
                CustomerCreate, CustomerUpdate, CustomerResponse
            )

            # Avec options
            router = CRUDRouter.create_crud_router(
                CustomerService,
                "customer", "customers",
                CustomerCreate, CustomerUpdate, CustomerResponse,
                tags=["Commercial"],
                include_delete=False,  # Pas de suppression
                soft_delete=True
            )
        """
        # Créer le router
        router_prefix = f"{prefix}/{plural_name}" if prefix else f"/{plural_name}"
        router = APIRouter(
            prefix=router_prefix,
            tags=tags or [resource_name.replace("_", " ").title()]
        )

        # Factory de service par défaut
        def default_service_factory(db: Session, context: SaaSContext):
            return service_class(db, context)

        factory = service_factory or default_service_factory

        # Helper pour mapper les erreurs
        def handle_result_error(result) -> None:
            """Lève une HTTPException si le Result est en échec."""
            if not result.success:
                error_code = result.error_code or "INVALID"
                http_status = cls.ERROR_STATUS_MAP.get(
                    error_code,
                    status.HTTP_400_BAD_REQUEST
                )
                raise HTTPException(
                    status_code=http_status,
                    detail=result.error
                )

        # =====================================================================
        # CREATE - POST /
        # =====================================================================
        if include_create:
            @router.post(
                "",
                response_model=response_schema,
                status_code=status.HTTP_201_CREATED,
                summary=f"Créer un {resource_name}",
                description=f"Crée une nouvelle ressource {resource_name}."
            )
            async def create(
                data: create_schema,
                context: SaaSContext = Depends(get_context),
                db: Session = Depends(get_db)
            ):
                """Créer une nouvelle ressource."""
                service = factory(db, context)
                result = service.create(data)
                handle_result_error(result)

                logger.info(
                    f"[CRUD] {resource_name} created",
                    extra={
                        "tenant_id": context.tenant_id,
                        "user_id": str(context.user_id),
                        "resource": resource_name,
                        "entity_id": str(result.data.id) if hasattr(result.data, 'id') else None
                    }
                )

                return result.data

        # =====================================================================
        # READ - GET /{id}
        # =====================================================================
        if include_read:
            @router.get(
                "/{id}",
                response_model=response_schema,
                summary=f"Récupérer un {resource_name}",
                description=f"Récupère les détails d'un {resource_name} par son ID."
            )
            async def get(
                id: UUID,
                context: SaaSContext = Depends(get_context),
                db: Session = Depends(get_db)
            ):
                """Récupérer une ressource par ID."""
                service = factory(db, context)
                result = service.get_or_fail(id)
                handle_result_error(result)
                return result.data

        # =====================================================================
        # LIST - GET /
        # =====================================================================
        if include_list:
            @router.get(
                "",
                response_model=PaginatedResponse[response_schema],
                summary=f"Lister les {plural_name}",
                description=f"Liste les {plural_name} avec pagination."
            )
            async def list_items(
                page: int = Query(1, ge=1, description="Numéro de page"),
                page_size: int = Query(20, ge=1, le=100, description="Taille de page"),
                is_active: Optional[bool] = Query(None, description="Filtrer par statut actif"),
                search: Optional[str] = Query(None, description="Recherche textuelle"),
                context: SaaSContext = Depends(get_context),
                db: Session = Depends(get_db)
            ):
                """Lister les ressources avec pagination."""
                service = factory(db, context)

                # Construire les filtres
                filters = {}
                if is_active is not None:
                    filters["is_active"] = is_active

                # Appeler le service
                result = service.list(
                    page=page,
                    page_size=page_size,
                    filters=filters if filters else None
                )

                return result

        # =====================================================================
        # UPDATE - PUT /{id}
        # =====================================================================
        if include_update:
            @router.put(
                "/{id}",
                response_model=response_schema,
                summary=f"Mettre à jour un {resource_name}",
                description=f"Met à jour un {resource_name} existant."
            )
            async def update(
                id: UUID,
                data: update_schema,
                context: SaaSContext = Depends(get_context),
                db: Session = Depends(get_db)
            ):
                """Mettre à jour une ressource."""
                service = factory(db, context)
                result = service.update(id, data)
                handle_result_error(result)

                logger.info(
                    f"[CRUD] {resource_name} updated",
                    extra={
                        "tenant_id": context.tenant_id,
                        "user_id": str(context.user_id),
                        "resource": resource_name,
                        "entity_id": str(id)
                    }
                )

                return result.data

        # =====================================================================
        # DELETE - DELETE /{id}
        # =====================================================================
        if include_delete:
            @router.delete(
                "/{id}",
                status_code=status.HTTP_204_NO_CONTENT,
                summary=f"Supprimer un {resource_name}",
                description=f"Supprime un {resource_name} (soft delete par défaut)."
            )
            async def delete(
                id: UUID,
                context: SaaSContext = Depends(get_context),
                db: Session = Depends(get_db)
            ):
                """Supprimer une ressource."""
                service = factory(db, context)
                result = service.delete(id, soft=soft_delete)
                handle_result_error(result)

                logger.info(
                    f"[CRUD] {resource_name} {'soft ' if soft_delete else ''}deleted",
                    extra={
                        "tenant_id": context.tenant_id,
                        "user_id": str(context.user_id),
                        "resource": resource_name,
                        "entity_id": str(id)
                    }
                )

                return None

        return router

    @classmethod
    def create_nested_crud_router(
        cls,
        parent_resource: str,
        parent_id_param: str,
        service_class: Type[Any],
        resource_name: str,
        plural_name: str,
        create_schema: Type[CreateSchema],
        update_schema: Type[UpdateSchema],
        response_schema: Type[ResponseSchema],
        tags: Optional[List[str]] = None,
    ) -> APIRouter:
        """
        Génère des endpoints CRUD pour une ressource imbriquée.

        Exemple: /customers/{customer_id}/contacts

        Args:
            parent_resource: Nom de la ressource parente (ex: "customer")
            parent_id_param: Nom du paramètre ID parent (ex: "customer_id")
            service_class: Classe du service
            resource_name: Nom de la sous-ressource (ex: "contact")
            plural_name: Nom pluriel (ex: "contacts")
            create_schema, update_schema, response_schema: Schémas Pydantic
            tags: Tags OpenAPI

        Returns:
            APIRouter pour les sous-ressources

        Example:
            contacts_router = CRUDRouter.create_nested_crud_router(
                parent_resource="customer",
                parent_id_param="customer_id",
                service_class=ContactService,
                resource_name="contact",
                plural_name="contacts",
                create_schema=ContactCreate,
                update_schema=ContactUpdate,
                response_schema=ContactResponse
            )
        """
        router = APIRouter(
            prefix=f"/{{{parent_id_param}}}/{plural_name}",
            tags=tags or [f"{parent_resource.title()} - {resource_name.title()}"]
        )

        # Les endpoints sont similaires mais reçoivent le parent_id
        # Implémenter selon les besoins spécifiques

        @router.get(
            "",
            response_model=PaginatedResponse[response_schema],
            summary=f"Lister les {plural_name} d'un {parent_resource}"
        )
        async def list_nested(
            parent_id: UUID,  # Sera extrait via le path parameter
            page: int = Query(1, ge=1),
            page_size: int = Query(20, ge=1, le=100),
            context: SaaSContext = Depends(get_context),
            db: Session = Depends(get_db)
        ):
            service = service_class(db, context)
            return service.list(
                page=page,
                page_size=page_size,
                filters={f"{parent_resource}_id": parent_id}
            )

        return router


# =============================================================================
# Helpers pour cas d'usage courants
# =============================================================================

def create_simple_crud(
    service_class: Type[Any],
    name: str,
    create_schema: Type[BaseModel],
    update_schema: Type[BaseModel],
    response_schema: Type[BaseModel],
    **kwargs
) -> APIRouter:
    """
    Raccourci pour créer un CRUD simple (singulier/pluriel auto).

    Usage:
        router = create_simple_crud(
            ProductService,
            "product",
            ProductCreate,
            ProductUpdate,
            ProductResponse
        )
    """
    # Pluriel simple (ajoute 's')
    plural = f"{name}s"

    return CRUDRouter.create_crud_router(
        service_class=service_class,
        resource_name=name,
        plural_name=plural,
        create_schema=create_schema,
        update_schema=update_schema,
        response_schema=response_schema,
        **kwargs
    )


def create_readonly_crud(
    service_class: Type[Any],
    name: str,
    plural: str,
    response_schema: Type[BaseModel],
    **kwargs
) -> APIRouter:
    """
    Crée un CRUD en lecture seule (GET et LIST uniquement).

    Usage:
        router = create_readonly_crud(
            AuditLogService,
            "audit_log",
            "audit_logs",
            AuditLogResponse
        )
    """
    # On passe des schémas vides pour create/update
    from pydantic import BaseModel as EmptySchema

    return CRUDRouter.create_crud_router(
        service_class=service_class,
        resource_name=name,
        plural_name=plural,
        create_schema=EmptySchema,
        update_schema=EmptySchema,
        response_schema=response_schema,
        include_create=False,
        include_update=False,
        include_delete=False,
        **kwargs
    )
