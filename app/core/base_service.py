"""
AZALS - BaseService Pattern
============================
Classe de base pour tous les services métier.
Unifie l'accès aux données via BaseRepository et standardise les réponses.

Conformité : AZA-NF-003
"""

from __future__ import annotations

import logging
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any, Callable
from uuid import UUID
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.repository import BaseRepository
from app.core.saas_context import SaaSContext, Result
from app.core.pagination import PaginatedResponse, PaginationParams

logger = logging.getLogger(__name__)

# Type variables pour généricité
T = TypeVar('T')  # Type du modèle ORM
CreateSchema = TypeVar('CreateSchema', bound=BaseModel)  # Schéma de création
UpdateSchema = TypeVar('UpdateSchema', bound=BaseModel)  # Schéma de mise à jour
ResponseSchema = TypeVar('ResponseSchema', bound=BaseModel)  # Schéma de réponse


class BaseService(Generic[T, CreateSchema, UpdateSchema]):
    """
    Service de base avec patterns standardisés.

    Avantages:
    - Accès données centralisé via BaseRepository
    - Isolation tenant automatique
    - Pagination standardisée (PaginatedResponse)
    - Gestion d'erreurs explicite (Result)
    - Logging structuré intégré

    Usage:
        class AccountingService(BaseService[AccountingFiscalYear, FiscalYearCreate, FiscalYearUpdate]):
            model = AccountingFiscalYear

            def create(self, data: FiscalYearCreate) -> Result[AccountingFiscalYear]:
                # Validation métier
                if data.end_date <= data.start_date:
                    return Result.fail("La date de fin doit être postérieure")

                # Utiliser le repo hérité
                entity = AccountingFiscalYear(**data.model_dump())
                return Result.ok(self.repo.create(entity))
    """

    # À définir dans les sous-classes
    model: Type[T] = None

    def __init__(self, db: Session, context: SaaSContext):
        """
        Initialise le service.

        Args:
            db: Session SQLAlchemy
            context: Contexte SaaS (tenant, user, permissions)
        """
        if self.model is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define 'model' class attribute"
            )

        self.db = db
        self.context = context
        self.tenant_id = context.tenant_id
        self.user_id = context.user_id
        self._repo: Optional[BaseRepository[T]] = None

        # Logger avec contexte
        self._logger = logging.LoggerAdapter(
            logger,
            extra={
                "service": self.__class__.__name__,
                "tenant_id": self.tenant_id,
                "user_id": str(self.user_id),
            }
        )

    @property
    def repo(self) -> BaseRepository[T]:
        """Lazy-load du repository."""
        if self._repo is None:
            self._repo = BaseRepository(self.db, self.model, self.tenant_id)
        return self._repo

    # =========================================================================
    # CRUD Operations (à surcharger pour logique métier)
    # =========================================================================

    def get(self, id: UUID, relations: Optional[List[str]] = None) -> Optional[T]:
        """
        Récupère une entité par ID.

        Args:
            id: UUID de l'entité
            relations: Relations à eager-load

        Returns:
            Entité ou None
        """
        return self.repo.get_by_id(id, relations=relations)

    def get_or_fail(self, id: UUID, relations: Optional[List[str]] = None) -> Result[T]:
        """
        Récupère une entité ou retourne une erreur.

        Args:
            id: UUID de l'entité
            relations: Relations à eager-load

        Returns:
            Result avec l'entité ou erreur
        """
        entity = self.get(id, relations)
        if entity is None:
            return Result.fail(
                f"{self.model.__name__} non trouvé: {id}",
                error_code="NOT_FOUND"
            )
        return Result.ok(entity)

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        relations: Optional[List[str]] = None,
        order_by: Optional[str] = None
    ) -> PaginatedResponse[T]:
        """
        Liste les entités avec pagination.

        Args:
            page: Numéro de page (1-indexed)
            page_size: Taille de page (max 100)
            filters: Filtres {field: value}
            relations: Relations à eager-load
            order_by: Champ de tri

        Returns:
            PaginatedResponse avec items et métadonnées
        """
        # Sécurité: limiter la taille max
        page_size = min(page_size, 100)
        skip = (page - 1) * page_size

        items, total = self.repo.list_all(
            skip=skip,
            limit=page_size,
            filters=filters,
            relations=relations,
            order_by=order_by
        )

        pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )

    def create(self, data: CreateSchema) -> Result[T]:
        """
        Crée une entité. À surcharger pour validation métier.

        Args:
            data: Schéma de création Pydantic

        Returns:
            Result avec l'entité créée ou erreur
        """
        try:
            entity = self.model(
                tenant_id=self.tenant_id,
                created_by=self.user_id,
                **data.model_dump()
            )
            created = self.repo.create(entity)

            self._logger.info(
                f"{self.model.__name__} created",
                extra={"entity_id": str(created.id)}
            )

            return Result.ok(created)

        except Exception as e:
            self._logger.error(f"Create failed: {e}")
            return Result.fail(str(e), error_code="CREATE_FAILED")

    def update(self, id: UUID, data: UpdateSchema) -> Result[T]:
        """
        Met à jour une entité. À surcharger pour validation métier.

        Args:
            id: UUID de l'entité
            data: Schéma de mise à jour Pydantic

        Returns:
            Result avec l'entité mise à jour ou erreur
        """
        entity = self.get(id)
        if entity is None:
            return Result.fail(
                f"{self.model.__name__} non trouvé: {id}",
                error_code="NOT_FOUND"
            )

        try:
            # Mise à jour des champs fournis uniquement
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(entity, field):
                    setattr(entity, field, value)

            # Marquer le modificateur si le champ existe
            if hasattr(entity, 'updated_by'):
                entity.updated_by = self.user_id

            updated = self.repo.update(entity)

            self._logger.info(
                f"{self.model.__name__} updated",
                extra={"entity_id": str(id)}
            )

            return Result.ok(updated)

        except Exception as e:
            self._logger.error(f"Update failed: {e}")
            return Result.fail(str(e), error_code="UPDATE_FAILED")

    def delete(self, id: UUID, soft: bool = True) -> Result[bool]:
        """
        Supprime une entité.

        Args:
            id: UUID de l'entité
            soft: Si True, soft delete (marque deleted_at)

        Returns:
            Result avec True si supprimé
        """
        success = self.repo.delete(id, soft=soft)

        if not success:
            return Result.fail(
                f"{self.model.__name__} non trouvé: {id}",
                error_code="NOT_FOUND"
            )

        self._logger.info(
            f"{self.model.__name__} {'soft ' if soft else ''}deleted",
            extra={"entity_id": str(id)}
        )

        return Result.ok(True)

    # =========================================================================
    # Helpers
    # =========================================================================

    def exists(self, id: UUID) -> bool:
        """Vérifie si une entité existe."""
        return self.repo.exists(id)

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Compte les entités avec filtres optionnels."""
        return self.repo.count(filters)

    def check_permission(self, permission: str) -> Result[bool]:
        """
        Vérifie si le contexte a une permission.

        Args:
            permission: Format "module.resource.action"

        Returns:
            Result.ok(True) si autorisé, Result.fail sinon
        """
        if self.context.has_permission(permission):
            return Result.ok(True)

        return Result.fail(
            f"Permission refusée: {permission}",
            error_code="PERMISSION_DENIED"
        )

    def require_permission(self, permission: str) -> None:
        """
        Vérifie une permission et lève une exception si non autorisé.

        Args:
            permission: Format "module.resource.action"

        Raises:
            PermissionError: Si non autorisé
        """
        result = self.check_permission(permission)
        if not result.success:
            raise PermissionError(result.error)

    def log_action(
        self,
        action: str,
        entity_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log une action métier pour audit.

        Args:
            action: Nom de l'action (ex: "create", "approve", "close")
            entity_id: ID de l'entité concernée
            details: Détails supplémentaires
        """
        extra = {
            "action": action,
            "model": self.model.__name__,
        }
        if entity_id:
            extra["entity_id"] = str(entity_id)
        if details:
            extra["details"] = details

        self._logger.info(f"Action: {action}", extra=extra)


# =============================================================================
# Service spécialisé avec schéma de réponse
# =============================================================================

class CRUDService(BaseService[T, CreateSchema, UpdateSchema]):
    """
    Extension de BaseService avec serialisation automatique.

    Usage avec schéma de réponse:
        class AccountingService(CRUDService[AccountingFiscalYear, FiscalYearCreate, FiscalYearUpdate]):
            model = AccountingFiscalYear
            response_schema = FiscalYearResponse
    """

    response_schema: Type[ResponseSchema] = None

    def to_response(self, entity: T) -> ResponseSchema:
        """
        Convertit une entité ORM en schéma de réponse.

        Args:
            entity: Entité ORM

        Returns:
            Schéma Pydantic de réponse
        """
        if self.response_schema is None:
            return entity  # Pas de conversion si pas de schéma

        return self.response_schema.model_validate(entity)

    def to_response_list(self, entities: List[T]) -> List[ResponseSchema]:
        """Convertit une liste d'entités."""
        return [self.to_response(e) for e in entities]

    def list_with_response(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        relations: Optional[List[str]] = None,
        order_by: Optional[str] = None
    ) -> PaginatedResponse[ResponseSchema]:
        """
        Liste avec conversion automatique en schéma de réponse.
        """
        result = self.list(page, page_size, filters, relations, order_by)

        if self.response_schema:
            result.items = self.to_response_list(result.items)

        return result
