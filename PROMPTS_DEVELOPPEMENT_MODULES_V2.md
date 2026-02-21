# PROMPTS DE DÉVELOPPEMENT MODULES AZALSCORE - V2 COMPLET

**Date:** 2026-02-20
**Version:** 2.0 - ÉDITION COMPLÈTE
**Objectif:** Modules 100% fonctionnels, production-ready, avec TOUTES les fonctionnalités

---

## RÈGLES FONDAMENTALES (NON NÉGOCIABLES)

```
┌─────────────────────────────────────────────────────────────────┐
│  VÉRITÉ ABSOLUE - CORRECTION IMMÉDIATE - RÉFÉRENCE TECHNIQUE    │
│  SÉCURITÉ MAXIMALE - MULTI-TENANT STRICT - NE RIEN CASSER       │
└─────────────────────────────────────────────────────────────────┘
```

---

# PROMPT 1: BACKEND MODULE COMPLET (V2)

```markdown
# MISSION: Développement Backend Module [NOM_MODULE] - ÉDITION COMPLÈTE

## CONTEXTE

AZALSCORE = ERP SaaS multi-tenant de référence technique.
Code audité par experts. DOIT être PARFAIT.

**Module:** [NOM_MODULE]
**Chemin:** /home/ubuntu/azalscore/app/modules/[nom_module]/

## RÈGLES NON NÉGOCIABLES

1. VÉRITÉ - Pas de mensonge, jamais
2. IMMÉDIAT - Corriger maintenant, pas plus tard
3. PERFECTION - Code de référence
4. SÉCURITÉ - Jamais réduire
5. MULTI-TENANT - Isolation totale
6. TESTS - Tout tester

---

## STRUCTURE COMPLÈTE DU MODULE

```
/app/modules/[nom_module]/
├── __init__.py              # Exports publics
├── models.py                # Modèles SQLAlchemy
├── schemas.py               # Schémas Pydantic (validation)
├── service.py               # Logique métier principale
├── repository.py            # Accès données (queries)
├── router.py                # Routes API CRUD
├── router_search.py         # Routes recherche/autocomplete
├── router_bulk.py           # Routes opérations bulk
├── router_export.py         # Routes import/export
├── dependencies.py          # Injection dépendances
├── exceptions.py            # Exceptions métier
├── validators.py            # Validateurs custom
├── filters.py               # Filtres avancés
├── events.py                # Événements/hooks
├── cache.py                 # Stratégie cache
├── constants.py             # Constantes
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_models.py
    ├── test_service.py
    ├── test_repository.py
    ├── test_router.py
    ├── test_search.py
    ├── test_bulk.py
    ├── test_security.py     # Tests isolation tenant
    └── test_integration.py
```

---

## PHASE 1: MODÈLES COMPLETS (models.py)

```python
"""
Modèles SQLAlchemy [NOM_MODULE]
- Multi-tenant obligatoire
- Soft delete
- Audit complet
- Versioning
- Relations avec cascade
"""
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    event, Numeric, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship, validates, backref
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid

from app.core.database import Base
from app.core.mixins import (
    AuditMixin,
    SoftDeleteMixin,
    VersionMixin,
    TenantMixin
)


class [NomEntite]Status(str, Enum):
    """Statuts avec transitions validées"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

    @classmethod
    def allowed_transitions(cls):
        return {
            cls.DRAFT: [cls.ACTIVE, cls.ARCHIVED],
            cls.ACTIVE: [cls.INACTIVE, cls.ARCHIVED],
            cls.INACTIVE: [cls.ACTIVE, cls.ARCHIVED],
            cls.ARCHIVED: []  # Terminal state
        }


class [NomEntite](Base, TenantMixin, AuditMixin, SoftDeleteMixin, VersionMixin):
    """
    Modèle [NomEntite]

    Hérite de:
    - TenantMixin: tenant_id obligatoire + filtrage
    - AuditMixin: created_at, updated_at, created_by, updated_by
    - SoftDeleteMixin: deleted_at, deleted_by, is_deleted
    - VersionMixin: version pour optimistic locking
    """
    __tablename__ = "[nom_entites]"

    # === Identifiants ===
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), nullable=False)  # Code unique par tenant

    # === Champs métier ===
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        SQLEnum([NomEntite]Status),
        default=[NomEntite]Status.DRAFT,
        nullable=False
    )

    # === Champs numériques avec précision ===
    amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    quantity = Column(Integer, default=0)

    # === Dates métier ===
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # === JSON pour flexibilité ===
    metadata = Column(JSONB, default=dict)
    tags = Column(ARRAY(String), default=list)

    # === Relations (exemple) ===
    # Parent
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey('[nom_entites].id', ondelete='SET NULL'),
        nullable=True
    )
    parent = relationship(
        '[NomEntite]',
        remote_side='[NomEntite].id',
        backref=backref('children', lazy='dynamic')
    )

    # Relation vers autre module
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey('categories.id', ondelete='RESTRICT'),
        nullable=True
    )
    category = relationship('Category', back_populates='[nom_entites]')

    # === Contraintes ===
    __table_args__ = (
        # Index multi-tenant OBLIGATOIRE
        Index('ix_[nom_entites]_tenant_id', 'tenant_id'),
        Index('ix_[nom_entites]_tenant_code', 'tenant_id', 'code'),
        Index('ix_[nom_entites]_tenant_status', 'tenant_id', 'status'),
        Index('ix_[nom_entites]_tenant_name', 'tenant_id', 'name'),

        # Index pour soft delete
        Index('ix_[nom_entites]_tenant_active', 'tenant_id', 'is_deleted'),

        # Index pour recherche full-text (PostgreSQL)
        Index(
            'ix_[nom_entites]_search',
            'tenant_id',
            postgresql_using='gin',
            postgresql_ops={'name': 'gin_trgm_ops'}
        ),

        # Unicité code par tenant
        UniqueConstraint('tenant_id', 'code', name='uq_[nom_entites]_tenant_code'),

        # Check constraints
        CheckConstraint('amount >= 0', name='ck_[nom_entites]_amount_positive'),
        CheckConstraint(
            'end_date IS NULL OR start_date IS NULL OR end_date >= start_date',
            name='ck_[nom_entites]_dates_valid'
        ),
    )

    # === Validateurs ===
    @validates('code')
    def validate_code(self, key, value):
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    @validates('status')
    def validate_status_transition(self, key, new_status):
        if self.status is not None:
            allowed = [NomEntite]Status.allowed_transitions().get(self.status, [])
            if new_status not in allowed and new_status != self.status:
                raise ValueError(
                    f"Invalid transition from {self.status} to {new_status}"
                )
        return new_status

    # === Propriétés calculées ===
    @hybrid_property
    def is_active(self) -> bool:
        return self.status == [NomEntite]Status.ACTIVE and not self.is_deleted

    @hybrid_property
    def display_name(self) -> str:
        return f"[{self.code}] {self.name}"

    # === Méthodes ===
    def can_delete(self) -> tuple[bool, str]:
        """Vérifie si l'entité peut être supprimée"""
        if self.status == [NomEntite]Status.ACTIVE:
            return False, "Cannot delete active entity"
        if self.children.count() > 0:
            return False, "Cannot delete entity with children"
        return True, ""

    def to_search_dict(self) -> dict:
        """Données pour indexation recherche"""
        return {
            "id": str(self.id),
            "code": self.code,
            "name": self.name,
            "status": self.status.value,
            "tags": self.tags or [],
        }

    def __repr__(self):
        return f"<[NomEntite] {self.code}: {self.name}>"


# === Event listeners ===
@event.listens_for([NomEntite], 'before_insert')
def before_insert(mapper, connection, target):
    """Avant insertion: générer code si absent"""
    if not target.code:
        # Auto-generate code
        prefix = "[PRE]"
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        target.code = f"{prefix}-{timestamp}"


@event.listens_for([NomEntite], 'before_update')
def before_update(mapper, connection, target):
    """Avant mise à jour: incrémenter version"""
    target.version += 1
```

---

## PHASE 2: REPOSITORY (repository.py)

```python
"""
Repository [NOM_MODULE]
- Accès données avec isolation tenant
- Queries optimisées
- Cache intégré
- Recherche avancée
"""
from typing import List, Optional, Tuple, Any, Dict
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import and_, or_, func, text, desc, asc
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.dialects.postgresql import insert

from .models import [NomEntite], [NomEntite]Status
from .filters import [NomEntite]Filter
from .cache import [NomModule]Cache


class [NomEntite]Repository:
    """
    Repository avec:
    - Isolation multi-tenant automatique
    - Soft delete transparent
    - Cache intégré
    - Queries optimisées
    """

    def __init__(
        self,
        db: Session,
        tenant_id: UUID,
        include_deleted: bool = False
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted
        self.cache = [NomModule]Cache(tenant_id)

    def _base_query(self):
        """
        Query de base avec filtres obligatoires
        SÉCURITÉ: Toujours filtrer par tenant_id
        """
        query = self.db.query([NomEntite]).filter(
            [NomEntite].tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter([NomEntite].is_deleted == False)
        return query

    # === CRUD de base ===

    def get_by_id(
        self,
        id: UUID,
        load_relations: List[str] = None
    ) -> Optional[[NomEntite]]:
        """Récupérer par ID avec relations optionnelles"""
        # Check cache first
        cached = self.cache.get(f"entity:{id}")
        if cached:
            return cached

        query = self._base_query().filter([NomEntite].id == id)

        if load_relations:
            for rel in load_relations:
                query = query.options(joinedload(getattr([NomEntite], rel)))

        result = query.first()

        if result:
            self.cache.set(f"entity:{id}", result, ttl=300)

        return result

    def get_by_code(self, code: str) -> Optional[[NomEntite]]:
        """Récupérer par code (unique par tenant)"""
        return self._base_query().filter(
            [NomEntite].code == code.upper()
        ).first()

    def exists(self, id: UUID) -> bool:
        """Vérifier existence"""
        return self._base_query().filter(
            [NomEntite].id == id
        ).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        """Vérifier si code existe déjà"""
        query = self._base_query().filter([NomEntite].code == code.upper())
        if exclude_id:
            query = query.filter([NomEntite].id != exclude_id)
        return query.count() > 0

    # === Liste et pagination ===

    def list(
        self,
        filters: [NomEntite]Filter = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[[NomEntite]], int]:
        """
        Liste paginée avec filtres
        Retourne (items, total)
        """
        query = self._base_query()

        # Appliquer filtres
        if filters:
            query = self._apply_filters(query, filters)

        # Count total
        total = query.count()

        # Sorting
        sort_column = getattr([NomEntite], sort_by, [NomEntite].created_at)
        if sort_dir == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def list_cursor(
        self,
        cursor: Optional[str] = None,
        limit: int = 20,
        filters: [NomEntite]Filter = None
    ) -> Tuple[List[[NomEntite]], Optional[str]]:
        """
        Pagination par cursor (plus performant pour grandes listes)
        Retourne (items, next_cursor)
        """
        query = self._base_query()

        if filters:
            query = self._apply_filters(query, filters)

        if cursor:
            # Decode cursor (format: created_at:id)
            cursor_date, cursor_id = cursor.split(":")
            query = query.filter(
                or_(
                    [NomEntite].created_at < datetime.fromisoformat(cursor_date),
                    and_(
                        [NomEntite].created_at == datetime.fromisoformat(cursor_date),
                        [NomEntite].id < UUID(cursor_id)
                    )
                )
            )

        query = query.order_by(
            desc([NomEntite].created_at),
            desc([NomEntite].id)
        )

        items = query.limit(limit + 1).all()

        # Determine next cursor
        next_cursor = None
        if len(items) > limit:
            items = items[:limit]
            last = items[-1]
            next_cursor = f"{last.created_at.isoformat()}:{last.id}"

        return items, next_cursor

    def _apply_filters(self, query, filters: [NomEntite]Filter):
        """Appliquer filtres dynamiquement"""
        if filters.status:
            if isinstance(filters.status, list):
                query = query.filter([NomEntite].status.in_(filters.status))
            else:
                query = query.filter([NomEntite].status == filters.status)

        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    [NomEntite].name.ilike(search_term),
                    [NomEntite].code.ilike(search_term),
                    [NomEntite].description.ilike(search_term)
                )
            )

        if filters.tags:
            query = query.filter([NomEntite].tags.overlap(filters.tags))

        if filters.category_id:
            query = query.filter([NomEntite].category_id == filters.category_id)

        if filters.date_from:
            query = query.filter([NomEntite].created_at >= filters.date_from)

        if filters.date_to:
            query = query.filter([NomEntite].created_at <= filters.date_to)

        if filters.amount_min is not None:
            query = query.filter([NomEntite].amount >= filters.amount_min)

        if filters.amount_max is not None:
            query = query.filter([NomEntite].amount <= filters.amount_max)

        return query

    # === Recherche et autocomplete ===

    def search(
        self,
        query_text: str,
        limit: int = 10,
        status: List[[NomEntite]Status] = None
    ) -> List[[NomEntite]]:
        """
        Recherche full-text optimisée
        Utilise trigram pour fuzzy matching
        """
        query = self._base_query()

        if status:
            query = query.filter([NomEntite].status.in_(status))

        # Recherche avec ranking
        search_term = query_text.strip()

        query = query.filter(
            or_(
                [NomEntite].name.ilike(f"%{search_term}%"),
                [NomEntite].code.ilike(f"%{search_term}%"),
                func.similarity([NomEntite].name, search_term) > 0.3
            )
        ).order_by(
            # Exact match first
            desc([NomEntite].code == search_term.upper()),
            desc([NomEntite].name.ilike(f"{search_term}%")),
            # Then by similarity
            desc(func.similarity([NomEntite].name, search_term))
        ).limit(limit)

        return query.all()

    def autocomplete(
        self,
        prefix: str,
        field: str = "name",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Autocomplete rapide pour formulaires
        Retourne format léger: [{id, code, name, label}]
        """
        if len(prefix) < 2:
            return []

        # Check cache
        cache_key = f"autocomplete:{field}:{prefix}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        query = self._base_query().filter(
            [NomEntite].status == [NomEntite]Status.ACTIVE
        )

        if field == "name":
            query = query.filter([NomEntite].name.ilike(f"{prefix}%"))
        elif field == "code":
            query = query.filter([NomEntite].code.ilike(f"{prefix}%"))
        else:
            query = query.filter(
                or_(
                    [NomEntite].name.ilike(f"{prefix}%"),
                    [NomEntite].code.ilike(f"{prefix}%")
                )
            )

        results = query.order_by([NomEntite].name).limit(limit).all()

        output = [
            {
                "id": str(item.id),
                "code": item.code,
                "name": item.name,
                "label": item.display_name
            }
            for item in results
        ]

        self.cache.set(cache_key, output, ttl=60)
        return output

    # === Opérations Bulk ===

    def bulk_create(
        self,
        items: List[Dict[str, Any]],
        created_by: UUID = None
    ) -> List[[NomEntite]]:
        """
        Création en masse optimisée
        Utilise INSERT ... ON CONFLICT pour upsert
        """
        now = datetime.utcnow()

        for item in items:
            item["tenant_id"] = self.tenant_id
            item["created_at"] = now
            item["updated_at"] = now
            if created_by:
                item["created_by"] = created_by

        stmt = insert([NomEntite].__table__).values(items)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=['tenant_id', 'code']
        )

        self.db.execute(stmt)
        self.db.commit()

        # Invalider cache
        self.cache.invalidate_pattern("list:*")

        return self.list(page_size=len(items))[0]

    def bulk_update(
        self,
        ids: List[UUID],
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> int:
        """
        Mise à jour en masse
        Retourne nombre de lignes affectées
        """
        data["updated_at"] = datetime.utcnow()
        if updated_by:
            data["updated_by"] = updated_by

        result = self._base_query().filter(
            [NomEntite].id.in_(ids)
        ).update(data, synchronize_session=False)

        self.db.commit()

        # Invalider cache
        for id in ids:
            self.cache.delete(f"entity:{id}")
        self.cache.invalidate_pattern("list:*")

        return result

    def bulk_delete(
        self,
        ids: List[UUID],
        deleted_by: UUID = None,
        hard: bool = False
    ) -> int:
        """
        Suppression en masse
        - Soft delete par défaut
        - Hard delete si explicitement demandé
        """
        if hard:
            result = self._base_query().filter(
                [NomEntite].id.in_(ids)
            ).delete(synchronize_session=False)
        else:
            result = self._base_query().filter(
                [NomEntite].id.in_(ids)
            ).update({
                "is_deleted": True,
                "deleted_at": datetime.utcnow(),
                "deleted_by": deleted_by
            }, synchronize_session=False)

        self.db.commit()

        # Invalider cache
        for id in ids:
            self.cache.delete(f"entity:{id}")
        self.cache.invalidate_pattern("list:*")

        return result

    # === Statistiques ===

    def get_stats(self) -> Dict[str, Any]:
        """Statistiques du module pour ce tenant"""
        base = self._base_query()

        total = base.count()
        by_status = dict(
            base.with_entities(
                [NomEntite].status,
                func.count([NomEntite].id)
            ).group_by([NomEntite].status).all()
        )

        return {
            "total": total,
            "by_status": {s.value: c for s, c in by_status.items()},
            "active": by_status.get([NomEntite]Status.ACTIVE, 0),
            "draft": by_status.get([NomEntite]Status.DRAFT, 0),
        }

    # === Export ===

    def export_all(
        self,
        filters: [NomEntite]Filter = None,
        format: str = "dict"
    ) -> List[Dict[str, Any]]:
        """
        Export toutes les données (pour CSV, Excel, etc.)
        ATTENTION: Peut être lourd - utiliser avec précaution
        """
        query = self._base_query()

        if filters:
            query = self._apply_filters(query, filters)

        items = query.all()

        if format == "dict":
            return [
                {
                    "id": str(item.id),
                    "code": item.code,
                    "name": item.name,
                    "status": item.status.value,
                    "amount": float(item.amount) if item.amount else 0,
                    "created_at": item.created_at.isoformat(),
                    # ... autres champs
                }
                for item in items
            ]

        return items
```

---

## PHASE 3: SERVICE COMPLET (service.py)

```python
"""
Service [NOM_MODULE] - Logique métier complète
"""
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from .models import [NomEntite], [NomEntite]Status
from .repository import [NomEntite]Repository
from .schemas import (
    [NomEntite]Create,
    [NomEntite]Update,
    [NomEntite]BulkCreate,
    [NomEntite]BulkUpdate
)
from .filters import [NomEntite]Filter
from .exceptions import (
    [NomEntite]NotFoundError,
    [NomEntite]ValidationError,
    [NomEntite]DuplicateError,
    [NomEntite]StateError
)
from .events import [NomModule]Events
from app.core.audit import audit_log


class [NomModule]Service:
    """
    Service métier avec:
    - Validation complète
    - Événements/hooks
    - Audit automatique
    - Gestion des erreurs
    """

    def __init__(
        self,
        db: Session,
        tenant_id: UUID,
        current_user_id: UUID = None
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self.repo = [NomEntite]Repository(db, tenant_id)
        self.events = [NomModule]Events()

    # === CRUD ===

    def get(self, id: UUID) -> [NomEntite]:
        """Récupérer ou lever exception"""
        entity = self.repo.get_by_id(id)
        if not entity:
            raise [NomEntite]NotFoundError(f"[NomEntite] {id} non trouvé")
        return entity

    def get_by_code(self, code: str) -> [NomEntite]:
        """Récupérer par code ou lever exception"""
        entity = self.repo.get_by_code(code)
        if not entity:
            raise [NomEntite]NotFoundError(f"[NomEntite] code={code} non trouvé")
        return entity

    def list(
        self,
        filters: [NomEntite]Filter = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[[NomEntite]], int, int]:
        """
        Liste paginée
        Retourne: (items, total, pages)
        """
        items, total = self.repo.list(
            filters=filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir
        )
        pages = (total + page_size - 1) // page_size
        return items, total, pages

    def create(self, data: [NomEntite]Create) -> [NomEntite]:
        """
        Créer avec validation complète
        """
        # Vérifier unicité code
        if data.code and self.repo.code_exists(data.code):
            raise [NomEntite]DuplicateError(f"Code {data.code} existe déjà")

        # Événement avant création
        self.events.before_create(data)

        # Créer l'entité
        entity = [NomEntite](
            tenant_id=self.tenant_id,
            created_by=self.current_user_id,
            **data.model_dump(exclude_unset=True)
        )

        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)

        # Événement après création
        self.events.after_create(entity)

        # Audit
        audit_log(
            tenant_id=self.tenant_id,
            user_id=self.current_user_id,
            action="create",
            entity_type="[nom_entite]",
            entity_id=entity.id,
            new_data=data.model_dump()
        )

        return entity

    def update(self, id: UUID, data: [NomEntite]Update) -> [NomEntite]:
        """
        Mettre à jour avec validation
        """
        entity = self.get(id)
        old_data = entity.to_dict() if hasattr(entity, 'to_dict') else {}

        # Vérifier unicité code si changé
        if data.code and data.code != entity.code:
            if self.repo.code_exists(data.code, exclude_id=id):
                raise [NomEntite]DuplicateError(f"Code {data.code} existe déjà")

        # Vérifier transition de statut
        if data.status and data.status != entity.status:
            allowed = [NomEntite]Status.allowed_transitions().get(entity.status, [])
            if data.status not in allowed:
                raise [NomEntite]StateError(
                    f"Transition {entity.status} -> {data.status} non autorisée"
                )

        # Événement avant mise à jour
        self.events.before_update(entity, data)

        # Appliquer les modifications
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(entity, key, value)

        entity.updated_by = self.current_user_id
        entity.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(entity)

        # Événement après mise à jour
        self.events.after_update(entity)

        # Audit
        audit_log(
            tenant_id=self.tenant_id,
            user_id=self.current_user_id,
            action="update",
            entity_type="[nom_entite]",
            entity_id=entity.id,
            old_data=old_data,
            new_data=update_data
        )

        return entity

    def delete(self, id: UUID, hard: bool = False) -> bool:
        """
        Supprimer (soft delete par défaut)
        """
        entity = self.get(id)

        # Vérifier si suppression possible
        can_delete, reason = entity.can_delete()
        if not can_delete:
            raise [NomEntite]ValidationError(reason)

        # Événement avant suppression
        self.events.before_delete(entity)

        if hard:
            self.db.delete(entity)
        else:
            entity.is_deleted = True
            entity.deleted_at = datetime.utcnow()
            entity.deleted_by = self.current_user_id

        self.db.commit()

        # Événement après suppression
        self.events.after_delete(id)

        # Audit
        audit_log(
            tenant_id=self.tenant_id,
            user_id=self.current_user_id,
            action="delete",
            entity_type="[nom_entite]",
            entity_id=id
        )

        return True

    def restore(self, id: UUID) -> [NomEntite]:
        """Restaurer une entité soft-deleted"""
        # Utiliser repo avec include_deleted
        repo_with_deleted = [NomEntite]Repository(
            self.db, self.tenant_id, include_deleted=True
        )
        entity = repo_with_deleted.get_by_id(id)

        if not entity:
            raise [NomEntite]NotFoundError(f"[NomEntite] {id} non trouvé")

        if not entity.is_deleted:
            raise [NomEntite]ValidationError("L'entité n'est pas supprimée")

        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        entity.updated_by = self.current_user_id

        self.db.commit()
        self.db.refresh(entity)

        # Audit
        audit_log(
            tenant_id=self.tenant_id,
            user_id=self.current_user_id,
            action="restore",
            entity_type="[nom_entite]",
            entity_id=id
        )

        return entity

    # === Recherche et autocomplete ===

    def search(
        self,
        query: str,
        limit: int = 10,
        status: List[[NomEntite]Status] = None
    ) -> List[[NomEntite]]:
        """Recherche full-text"""
        return self.repo.search(query, limit, status)

    def autocomplete(
        self,
        prefix: str,
        field: str = "name",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Autocomplete pour formulaires"""
        return self.repo.autocomplete(prefix, field, limit)

    # === Opérations Bulk ===

    def bulk_create(self, data: [NomEntite]BulkCreate) -> Dict[str, Any]:
        """
        Création en masse
        Retourne: {created: int, errors: list}
        """
        errors = []
        valid_items = []

        for i, item in enumerate(data.items):
            # Validation
            if item.code and self.repo.code_exists(item.code):
                errors.append({
                    "index": i,
                    "code": item.code,
                    "error": "Code déjà existant"
                })
                continue

            valid_items.append(item.model_dump())

        if valid_items:
            self.repo.bulk_create(valid_items, self.current_user_id)

        # Audit
        audit_log(
            tenant_id=self.tenant_id,
            user_id=self.current_user_id,
            action="bulk_create",
            entity_type="[nom_entite]",
            details={"count": len(valid_items), "errors": len(errors)}
        )

        return {
            "created": len(valid_items),
            "errors": errors
        }

    def bulk_update(self, data: [NomEntite]BulkUpdate) -> Dict[str, Any]:
        """
        Mise à jour en masse
        """
        # Vérifier que tous les IDs existent
        existing_ids = set()
        for id in data.ids:
            if self.repo.exists(id):
                existing_ids.add(id)

        missing_ids = set(data.ids) - existing_ids

        if existing_ids:
            count = self.repo.bulk_update(
                list(existing_ids),
                data.data.model_dump(exclude_unset=True),
                self.current_user_id
            )
        else:
            count = 0

        # Audit
        audit_log(
            tenant_id=self.tenant_id,
            user_id=self.current_user_id,
            action="bulk_update",
            entity_type="[nom_entite]",
            details={"updated": count, "missing": list(missing_ids)}
        )

        return {
            "updated": count,
            "missing": list(missing_ids)
        }

    def bulk_delete(
        self,
        ids: List[UUID],
        hard: bool = False
    ) -> Dict[str, Any]:
        """
        Suppression en masse
        """
        # Vérifier chaque entité
        deletable = []
        errors = []

        for id in ids:
            try:
                entity = self.get(id)
                can_delete, reason = entity.can_delete()
                if can_delete:
                    deletable.append(id)
                else:
                    errors.append({"id": str(id), "error": reason})
            except [NomEntite]NotFoundError:
                errors.append({"id": str(id), "error": "Non trouvé"})

        count = 0
        if deletable:
            count = self.repo.bulk_delete(deletable, self.current_user_id, hard)

        # Audit
        audit_log(
            tenant_id=self.tenant_id,
            user_id=self.current_user_id,
            action="bulk_delete",
            entity_type="[nom_entite]",
            details={"deleted": count, "errors": errors}
        )

        return {
            "deleted": count,
            "errors": errors
        }

    # === Import/Export ===

    def import_data(
        self,
        data: List[Dict[str, Any]],
        mode: str = "create"  # create, update, upsert
    ) -> Dict[str, Any]:
        """
        Import de données
        mode: create (erreur si existe), update (erreur si n'existe pas), upsert
        """
        created = 0
        updated = 0
        errors = []

        for i, row in enumerate(data):
            try:
                code = row.get("code")
                existing = self.repo.get_by_code(code) if code else None

                if mode == "create":
                    if existing:
                        errors.append({"row": i, "error": f"Code {code} existe déjà"})
                        continue
                    self.create([NomEntite]Create(**row))
                    created += 1

                elif mode == "update":
                    if not existing:
                        errors.append({"row": i, "error": f"Code {code} non trouvé"})
                        continue
                    self.update(existing.id, [NomEntite]Update(**row))
                    updated += 1

                elif mode == "upsert":
                    if existing:
                        self.update(existing.id, [NomEntite]Update(**row))
                        updated += 1
                    else:
                        self.create([NomEntite]Create(**row))
                        created += 1

            except Exception as e:
                errors.append({"row": i, "error": str(e)})

        return {
            "created": created,
            "updated": updated,
            "errors": errors
        }

    def export_data(
        self,
        filters: [NomEntite]Filter = None,
        format: str = "dict"
    ) -> List[Dict[str, Any]]:
        """Export des données"""
        return self.repo.export_all(filters, format)

    # === Statistiques ===

    def get_stats(self) -> Dict[str, Any]:
        """Statistiques du module"""
        return self.repo.get_stats()
```

---

## PHASE 4: SCHEMAS COMPLETS (schemas.py)

```python
"""
Schémas Pydantic [NOM_MODULE]
- Validation stricte
- Messages d'erreur clairs
- Serialisation optimisée
"""
from pydantic import (
    BaseModel, Field, validator, root_validator,
    ConfigDict, field_validator, model_validator
)
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from .models import [NomEntite]Status


# === Enums pour l'API ===

class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


# === Schémas de base ===

class [NomEntite]Base(BaseModel):
    """Champs communs avec validation"""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nom de l'entité"
    )

    code: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        pattern=r'^[A-Z0-9\-_]+$',
        description="Code unique (auto-généré si absent)"
    )

    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Description détaillée"
    )

    status: [NomEntite]Status = Field(
        default=[NomEntite]Status.DRAFT,
        description="Statut de l'entité"
    )

    amount: Optional[Decimal] = Field(
        None,
        ge=0,
        decimal_places=2,
        description="Montant (positif ou nul)"
    )

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    category_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None

    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Le nom ne peut pas être vide')
        return v.strip()

    @field_validator('code')
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.upper().strip()
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        # Nettoyer et dédupliquer
        return list(set(tag.strip().lower() for tag in v if tag.strip()))

    @model_validator(mode='after')
    def validate_dates(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError('La date de fin doit être après la date de début')
        return self


class [NomEntite]Create([NomEntite]Base):
    """Schéma création"""
    pass


class [NomEntite]Update(BaseModel):
    """Schéma mise à jour - tous les champs optionnels"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[[NomEntite]Status] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    category_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('Le nom ne peut pas être vide')
        return v.strip() if v else v


class [NomEntite]Response([NomEntite]Base):
    """Schéma réponse complète"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID

    # Audit
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    # Soft delete
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    # Version
    version: int = 1

    # Relations (optionnelles, chargées à la demande)
    category: Optional[Dict[str, Any]] = None
    parent: Optional[Dict[str, Any]] = None


class [NomEntite]ListItem(BaseModel):
    """Schéma liste légère (sans relations)"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    status: [NomEntite]Status
    amount: Optional[Decimal] = None
    created_at: datetime
    is_deleted: bool = False


class [NomEntite]List(BaseModel):
    """Réponse liste paginée"""

    items: List[[NomEntite]ListItem]
    total: int
    page: int
    page_size: int
    pages: int


class [NomEntite]CursorList(BaseModel):
    """Réponse liste avec cursor"""

    items: List[[NomEntite]ListItem]
    next_cursor: Optional[str] = None
    has_more: bool = False


# === Autocomplete ===

class AutocompleteItem(BaseModel):
    """Item pour autocomplete"""

    id: str
    code: str
    name: str
    label: str  # Display: "[CODE] Name"


class AutocompleteResponse(BaseModel):
    """Réponse autocomplete"""

    items: List[AutocompleteItem]


# === Filtres ===

class [NomEntite]FilterParams(BaseModel):
    """Paramètres de filtrage"""

    search: Optional[str] = Field(None, min_length=2, description="Recherche texte")
    status: Optional[List[[NomEntite]Status]] = None
    category_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    include_deleted: bool = False


class [NomEntite]SortParams(BaseModel):
    """Paramètres de tri"""

    sort_by: str = Field(default="created_at")
    sort_dir: SortDirection = Field(default=SortDirection.DESC)

    @field_validator('sort_by')
    @classmethod
    def validate_sort_field(cls, v: str) -> str:
        allowed = ['name', 'code', 'status', 'amount', 'created_at', 'updated_at']
        if v not in allowed:
            raise ValueError(f'Champ de tri invalide. Autorisés: {allowed}')
        return v


# === Bulk operations ===

class [NomEntite]BulkCreate(BaseModel):
    """Création en masse"""

    items: List[[NomEntite]Create] = Field(..., min_length=1, max_length=1000)


class [NomEntite]BulkUpdate(BaseModel):
    """Mise à jour en masse"""

    ids: List[UUID] = Field(..., min_length=1, max_length=1000)
    data: [NomEntite]Update


class [NomEntite]BulkDelete(BaseModel):
    """Suppression en masse"""

    ids: List[UUID] = Field(..., min_length=1, max_length=1000)
    hard: bool = Field(default=False, description="Suppression définitive")


class BulkOperationResult(BaseModel):
    """Résultat opération bulk"""

    success: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# === Import/Export ===

class ImportRequest(BaseModel):
    """Requête import"""

    data: List[Dict[str, Any]]
    mode: str = Field(
        default="create",
        pattern=r'^(create|update|upsert)$'
    )


class ImportResult(BaseModel):
    """Résultat import"""

    created: int = 0
    updated: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# === Statistiques ===

class [NomEntite]Stats(BaseModel):
    """Statistiques"""

    total: int
    by_status: Dict[str, int]
    active: int
    draft: int
```

---

## PHASE 5: ROUTERS COMPLETS

### router.py - CRUD principal

```python
"""
Routes API CRUD [NOM_MODULE]
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Optional
from uuid import UUID

from app.core.security import get_current_user, require_permission
from app.core.database import get_db
from sqlalchemy.orm import Session

from .service import [NomModule]Service
from .schemas import *
from .filters import [NomEntite]Filter
from .exceptions import *


router = APIRouter(prefix="/[nom-module]", tags=["[NOM_MODULE]"])


def get_service(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> [NomModule]Service:
    return [NomModule]Service(db, current_user.tenant_id, current_user.id)


# === CRUD ===

@router.get(
    "/",
    response_model=[NomEntite]List,
    summary="Lister",
    dependencies=[Depends(require_permission("[nom_module].view"))]
)
async def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[List[[NomEntite]Status]] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    service: [NomModule]Service = Depends(get_service)
):
    filters = [NomEntite]Filter(search=search, status=status)
    items, total, pages = service.list(
        filters=filters,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


@router.get(
    "/{id}",
    response_model=[NomEntite]Response,
    summary="Détail",
    dependencies=[Depends(require_permission("[nom_module].view"))]
)
async def get_item(
    id: UUID = Path(...),
    service: [NomModule]Service = Depends(get_service)
):
    try:
        return service.get(id)
    except [NomEntite]NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/",
    response_model=[NomEntite]Response,
    status_code=status.HTTP_201_CREATED,
    summary="Créer",
    dependencies=[Depends(require_permission("[nom_module].create"))]
)
async def create_item(
    data: [NomEntite]Create,
    service: [NomModule]Service = Depends(get_service)
):
    try:
        return service.create(data)
    except [NomEntite]DuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except [NomEntite]ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/{id}",
    response_model=[NomEntite]Response,
    summary="Modifier",
    dependencies=[Depends(require_permission("[nom_module].edit"))]
)
async def update_item(
    id: UUID,
    data: [NomEntite]Update,
    service: [NomModule]Service = Depends(get_service)
):
    try:
        return service.update(id, data)
    except [NomEntite]NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ([NomEntite]DuplicateError, [NomEntite]StateError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer",
    dependencies=[Depends(require_permission("[nom_module].delete"))]
)
async def delete_item(
    id: UUID,
    hard: bool = Query(False),
    service: [NomModule]Service = Depends(get_service)
):
    try:
        service.delete(id, hard=hard)
    except [NomEntite]NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except [NomEntite]ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{id}/restore",
    response_model=[NomEntite]Response,
    summary="Restaurer",
    dependencies=[Depends(require_permission("[nom_module].delete"))]
)
async def restore_item(
    id: UUID,
    service: [NomModule]Service = Depends(get_service)
):
    try:
        return service.restore(id)
    except ([NomEntite]NotFoundError, [NomEntite]ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### router_search.py - Recherche et autocomplete

```python
"""
Routes recherche et autocomplete [NOM_MODULE]
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from app.core.security import get_current_user, require_permission

from .service import [NomModule]Service
from .schemas import AutocompleteResponse, [NomEntite]ListItem
from .models import [NomEntite]Status


router = APIRouter(prefix="/[nom-module]", tags=["[NOM_MODULE] - Recherche"])


@router.get(
    "/search",
    response_model=List[[NomEntite]ListItem],
    summary="Recherche full-text",
    dependencies=[Depends(require_permission("[nom_module].view"))]
)
async def search(
    q: str = Query(..., min_length=2, description="Terme de recherche"),
    limit: int = Query(10, ge=1, le=50),
    status: Optional[List[[NomEntite]Status]] = Query(None),
    service: [NomModule]Service = Depends(get_service)
):
    """
    Recherche full-text avec fuzzy matching
    """
    return service.search(q, limit, status)


@router.get(
    "/autocomplete",
    response_model=AutocompleteResponse,
    summary="Autocomplete",
    dependencies=[Depends(require_permission("[nom_module].view"))]
)
async def autocomplete(
    prefix: str = Query(..., min_length=2, description="Préfixe"),
    field: str = Query("name", pattern="^(name|code|all)$"),
    limit: int = Query(10, ge=1, le=20),
    service: [NomModule]Service = Depends(get_service)
):
    """
    Autocomplete rapide pour formulaires
    Retourne format léger optimisé
    """
    items = service.autocomplete(prefix, field, limit)
    return {"items": items}


@router.get(
    "/lookup/{code}",
    response_model=[NomEntite]Response,
    summary="Lookup par code",
    dependencies=[Depends(require_permission("[nom_module].view"))]
)
async def lookup_by_code(
    code: str,
    service: [NomModule]Service = Depends(get_service)
):
    """
    Recherche exacte par code
    """
    return service.get_by_code(code)
```

### router_bulk.py - Opérations en masse

```python
"""
Routes opérations bulk [NOM_MODULE]
"""
from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID

from app.core.security import get_current_user, require_permission

from .service import [NomModule]Service
from .schemas import (
    [NomEntite]BulkCreate,
    [NomEntite]BulkUpdate,
    [NomEntite]BulkDelete,
    BulkOperationResult
)


router = APIRouter(prefix="/[nom-module]/bulk", tags=["[NOM_MODULE] - Bulk"])


@router.post(
    "/create",
    response_model=BulkOperationResult,
    summary="Création en masse",
    dependencies=[Depends(require_permission("[nom_module].create"))]
)
async def bulk_create(
    data: [NomEntite]BulkCreate,
    service: [NomModule]Service = Depends(get_service)
):
    """
    Créer plusieurs entités en une requête
    Maximum: 1000 items
    """
    result = service.bulk_create(data)
    return {"success": result["created"], "errors": result["errors"]}


@router.post(
    "/update",
    response_model=BulkOperationResult,
    summary="Mise à jour en masse",
    dependencies=[Depends(require_permission("[nom_module].edit"))]
)
async def bulk_update(
    data: [NomEntite]BulkUpdate,
    service: [NomModule]Service = Depends(get_service)
):
    """
    Mettre à jour plusieurs entités avec les mêmes valeurs
    """
    result = service.bulk_update(data)
    return {"success": result["updated"], "errors": result.get("missing", [])}


@router.post(
    "/delete",
    response_model=BulkOperationResult,
    summary="Suppression en masse",
    dependencies=[Depends(require_permission("[nom_module].delete"))]
)
async def bulk_delete(
    data: [NomEntite]BulkDelete,
    service: [NomModule]Service = Depends(get_service)
):
    """
    Supprimer plusieurs entités
    """
    result = service.bulk_delete(data.ids, data.hard)
    return {"success": result["deleted"], "errors": result["errors"]}
```

### router_export.py - Import/Export

```python
"""
Routes import/export [NOM_MODULE]
"""
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
import csv
import io

from app.core.security import get_current_user, require_permission

from .service import [NomModule]Service
from .schemas import ImportRequest, ImportResult, [NomEntite]FilterParams


router = APIRouter(prefix="/[nom-module]", tags=["[NOM_MODULE] - Import/Export"])


@router.post(
    "/import",
    response_model=ImportResult,
    summary="Importer données",
    dependencies=[Depends(require_permission("[nom_module].create"))]
)
async def import_data(
    data: ImportRequest,
    service: [NomModule]Service = Depends(get_service)
):
    """
    Import de données JSON
    Modes: create, update, upsert
    """
    return service.import_data(data.data, data.mode)


@router.post(
    "/import/csv",
    response_model=ImportResult,
    summary="Importer CSV",
    dependencies=[Depends(require_permission("[nom_module].create"))]
)
async def import_csv(
    file: UploadFile = File(...),
    mode: str = "create",
    service: [NomModule]Service = Depends(get_service)
):
    """
    Import depuis fichier CSV
    """
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
    data = list(reader)
    return service.import_data(data, mode)


@router.get(
    "/export",
    summary="Exporter données",
    dependencies=[Depends(require_permission("[nom_module].view"))]
)
async def export_data(
    format: str = "csv",
    filters: [NomEntite]FilterParams = Depends(),
    service: [NomModule]Service = Depends(get_service)
):
    """
    Export des données
    Formats: csv, json
    """
    data = service.export_data(filters)

    if format == "csv":
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=[nom_module]_export.csv"}
        )

    return data


@router.get(
    "/stats",
    summary="Statistiques",
    dependencies=[Depends(require_permission("[nom_module].view"))]
)
async def get_stats(
    service: [NomModule]Service = Depends(get_service)
):
    """
    Statistiques du module
    """
    return service.get_stats()
```

---

## PHASE 6: TESTS COMPLETS

```python
# tests/test_security.py
"""
Tests de sécurité et isolation multi-tenant
CRITIQUES - Doivent tous passer
"""
import pytest
from uuid import uuid4

from ..service import [NomModule]Service
from ..schemas import [NomEntite]Create


class TestMultiTenantIsolation:
    """Tests isolation entre tenants"""

    def test_cannot_read_other_tenant_data(self, db, tenant_a, tenant_b):
        """CRITIQUE: Un tenant ne peut pas lire les données d'un autre"""
        # Créer avec tenant A
        service_a = [NomModule]Service(db, tenant_a.id)
        entity = service_a.create([NomEntite]Create(name="Secret A"))

        # Essayer de lire avec tenant B
        service_b = [NomModule]Service(db, tenant_b.id)
        result = service_b.repo.get_by_id(entity.id)

        assert result is None  # DOIT être None

    def test_cannot_update_other_tenant_data(self, db, tenant_a, tenant_b):
        """CRITIQUE: Un tenant ne peut pas modifier les données d'un autre"""
        service_a = [NomModule]Service(db, tenant_a.id)
        entity = service_a.create([NomEntite]Create(name="Original"))

        service_b = [NomModule]Service(db, tenant_b.id)

        with pytest.raises([NomEntite]NotFoundError):
            service_b.update(entity.id, [NomEntite]Update(name="Hacked"))

    def test_cannot_delete_other_tenant_data(self, db, tenant_a, tenant_b):
        """CRITIQUE: Un tenant ne peut pas supprimer les données d'un autre"""
        service_a = [NomModule]Service(db, tenant_a.id)
        entity = service_a.create([NomEntite]Create(name="To Keep"))

        service_b = [NomModule]Service(db, tenant_b.id)

        with pytest.raises([NomEntite]NotFoundError):
            service_b.delete(entity.id)

        # Vérifier que l'entité existe toujours
        assert service_a.get(entity.id) is not None

    def test_list_only_returns_own_tenant_data(self, db, tenant_a, tenant_b):
        """Les listes ne retournent que les données du tenant"""
        service_a = [NomModule]Service(db, tenant_a.id)
        service_b = [NomModule]Service(db, tenant_b.id)

        # Créer données dans chaque tenant
        service_a.create([NomEntite]Create(name="Tenant A Item"))
        service_b.create([NomEntite]Create(name="Tenant B Item"))

        # Lister tenant A
        items_a, _, _ = service_a.list()

        # Vérifier qu'aucun item de B n'est présent
        for item in items_a:
            assert item.tenant_id == tenant_a.id

    def test_search_respects_tenant_isolation(self, db, tenant_a, tenant_b):
        """La recherche respecte l'isolation tenant"""
        service_a = [NomModule]Service(db, tenant_a.id)
        service_b = [NomModule]Service(db, tenant_b.id)

        # Même nom dans les deux tenants
        service_a.create([NomEntite]Create(name="UniqueSearch123"))
        service_b.create([NomEntite]Create(name="UniqueSearch123"))

        # Recherche tenant A
        results = service_a.search("UniqueSearch123")

        assert len(results) == 1
        assert results[0].tenant_id == tenant_a.id
```

---

Ceci est la **PARTIE 1** du prompt. Voir la **PARTIE 2** pour le frontend complet.
```

---

# PROMPT 2: FRONTEND COMPLET AVEC AUTOCOMPLÉTION

## À copier dans la suite du fichier

```markdown
# MISSION: Intégration Frontend [NOM_MODULE] - ÉDITION COMPLÈTE

## STRUCTURE FRONTEND COMPLÈTE

```
/frontend/src/features/[nom-module]/
├── index.ts
├── types.ts
├── api.ts
├── hooks/
│   ├── index.ts
│   ├── use[NomModule].ts
│   ├── use[NomModule]Mutations.ts
│   ├── use[NomModule]Search.ts
│   └── use[NomModule]Autocomplete.ts
├── components/
│   ├── index.ts
│   ├── [NomModule]List.tsx
│   ├── [NomModule]Table.tsx
│   ├── [NomModule]Form.tsx
│   ├── [NomModule]Detail.tsx
│   ├── [NomModule]Card.tsx
│   ├── [NomModule]Filters.tsx
│   ├── [NomModule]Search.tsx
│   ├── [NomModule]Autocomplete.tsx
│   ├── [NomModule]BulkActions.tsx
│   ├── [NomModule]Import.tsx
│   └── [NomModule]Export.tsx
├── pages/
│   ├── index.ts
│   ├── [NomModule]Page.tsx
│   └── [NomModule]DetailPage.tsx
└── utils/
    ├── index.ts
    ├── validators.ts
    └── formatters.ts
```

---

## COMPOSANT AUTOCOMPLETE COMPLET

```typescript
// components/[NomModule]Autocomplete.tsx
/**
 * Composant Autocomplete avec:
 * - Debounce pour performance
 * - Cache des résultats
 * - Gestion clavier complète
 * - Accessibilité ARIA
 * - Loading et erreur states
 */
import { useState, useRef, useEffect, useCallback, forwardRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2, X, ChevronDown, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useDebounce } from '@/hooks/useDebounce';
import { [nomModule]Api } from '../api';
import type { AutocompleteItem } from '../types';

interface Props {
  value?: string | null;
  onChange: (value: string | null, item?: AutocompleteItem) => void;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
  label?: string;
  required?: boolean;
  className?: string;
  // Options de recherche
  minChars?: number;
  maxResults?: number;
  searchField?: 'name' | 'code' | 'all';
  // Filtres additionnels
  filterFn?: (item: AutocompleteItem) => boolean;
  // Callbacks
  onFocus?: () => void;
  onBlur?: () => void;
}

export const [NomModule]Autocomplete = forwardRef<HTMLInputElement, Props>(({
  value,
  onChange,
  placeholder = "Rechercher...",
  disabled = false,
  error,
  label,
  required = false,
  className,
  minChars = 2,
  maxResults = 10,
  searchField = 'all',
  filterFn,
  onFocus,
  onBlur
}, ref) => {
  // State
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [selectedItem, setSelectedItem] = useState<AutocompleteItem | null>(null);

  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Debounce input
  const debouncedSearch = useDebounce(inputValue, 300);

  // Query pour autocomplete
  const {
    data: suggestions = [],
    isLoading,
    isError
  } = useQuery({
    queryKey: ['[nom-module]', 'autocomplete', debouncedSearch, searchField],
    queryFn: () => [nomModule]Api.autocomplete(debouncedSearch, searchField, maxResults),
    enabled: debouncedSearch.length >= minChars && isOpen,
    staleTime: 60000, // Cache 1 minute
    select: (data) => {
      let items = data.items;
      if (filterFn) {
        items = items.filter(filterFn);
      }
      return items;
    }
  });

  // Charger item initial si value fournie
  useEffect(() => {
    if (value && !selectedItem) {
      [nomModule]Api.get(value).then(item => {
        setSelectedItem({
          id: item.id,
          code: item.code,
          name: item.name,
          label: `[${item.code}] ${item.name}`
        });
        setInputValue(item.name);
      }).catch(() => {
        // Item non trouvé, reset
        onChange(null);
      });
    }
  }, [value]);

  // Gestion clavier
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (disabled) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setHighlightedIndex(prev =>
            prev < suggestions.length - 1 ? prev + 1 : 0
          );
        }
        break;

      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev =>
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        break;

      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && suggestions[highlightedIndex]) {
          handleSelect(suggestions[highlightedIndex]);
        }
        break;

      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        setHighlightedIndex(-1);
        break;

      case 'Tab':
        setIsOpen(false);
        break;
    }
  }, [isOpen, suggestions, highlightedIndex, disabled]);

  // Sélection item
  const handleSelect = useCallback((item: AutocompleteItem) => {
    setSelectedItem(item);
    setInputValue(item.name);
    setIsOpen(false);
    setHighlightedIndex(-1);
    onChange(item.id, item);
  }, [onChange]);

  // Clear
  const handleClear = useCallback(() => {
    setSelectedItem(null);
    setInputValue('');
    onChange(null);
    setIsOpen(false);
  }, [onChange]);

  // Click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Scroll highlighted into view
  useEffect(() => {
    if (highlightedIndex >= 0 && listRef.current) {
      const item = listRef.current.children[highlightedIndex] as HTMLElement;
      item?.scrollIntoView({ block: 'nearest' });
    }
  }, [highlightedIndex]);

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {/* Label */}
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      {/* Input container */}
      <div className="relative">
        <input
          ref={ref}
          type="text"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            setIsOpen(true);
            setHighlightedIndex(-1);
            if (!e.target.value) {
              handleClear();
            }
          }}
          onFocus={() => {
            setIsOpen(true);
            onFocus?.();
          }}
          onBlur={() => {
            onBlur?.();
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            "w-full px-3 py-2 pr-10 border rounded-md",
            "focus:outline-none focus:ring-2 focus:ring-blue-500",
            error && "border-red-500",
            disabled && "bg-gray-100 cursor-not-allowed"
          )}
          role="combobox"
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          aria-autocomplete="list"
          aria-controls="autocomplete-list"
          aria-activedescendant={
            highlightedIndex >= 0 ? `option-${highlightedIndex}` : undefined
          }
        />

        {/* Icons */}
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {isLoading && (
            <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
          )}
          {selectedItem && !disabled && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1 hover:bg-gray-100 rounded"
              aria-label="Effacer la sélection"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          )}
          <ChevronDown className={cn(
            "w-4 h-4 text-gray-400 transition-transform",
            isOpen && "rotate-180"
          )} />
        </div>
      </div>

      {/* Error message */}
      {error && (
        <p className="mt-1 text-sm text-red-500">{error}</p>
      )}

      {/* Dropdown */}
      {isOpen && (
        <ul
          ref={listRef}
          id="autocomplete-list"
          role="listbox"
          className={cn(
            "absolute z-50 w-full mt-1 bg-white border rounded-md shadow-lg",
            "max-h-60 overflow-auto"
          )}
        >
          {/* Loading state */}
          {isLoading && inputValue.length >= minChars && (
            <li className="px-3 py-2 text-gray-500 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Recherche en cours...
            </li>
          )}

          {/* Error state */}
          {isError && (
            <li className="px-3 py-2 text-red-500">
              Erreur lors de la recherche
            </li>
          )}

          {/* No results */}
          {!isLoading && !isError && inputValue.length >= minChars && suggestions.length === 0 && (
            <li className="px-3 py-2 text-gray-500">
              Aucun résultat trouvé
            </li>
          )}

          {/* Min chars hint */}
          {inputValue.length > 0 && inputValue.length < minChars && (
            <li className="px-3 py-2 text-gray-500">
              Tapez au moins {minChars} caractères
            </li>
          )}

          {/* Results */}
          {suggestions.map((item, index) => (
            <li
              key={item.id}
              id={`option-${index}`}
              role="option"
              aria-selected={highlightedIndex === index}
              onClick={() => handleSelect(item)}
              onMouseEnter={() => setHighlightedIndex(index)}
              className={cn(
                "px-3 py-2 cursor-pointer flex items-center justify-between",
                highlightedIndex === index && "bg-blue-50",
                selectedItem?.id === item.id && "bg-blue-100"
              )}
            >
              <div>
                <span className="font-medium">{item.name}</span>
                <span className="text-gray-500 text-sm ml-2">[{item.code}]</span>
              </div>
              {selectedItem?.id === item.id && (
                <Check className="w-4 h-4 text-blue-600" />
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
});

[NomModule]Autocomplete.displayName = '[NomModule]Autocomplete';
```

---

## FORMULAIRE COMPLET AVEC VALIDATION

```typescript
// components/[NomModule]Form.tsx
/**
 * Formulaire complet avec:
 * - Validation temps réel
 * - Autocomplete pour relations
 * - Gestion erreurs serveur
 * - Loading states
 * - Mode création/édition
 */
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { use[NomModule], use[NomModule]Mutations } from '../hooks';
import { [NomModule]Autocomplete } from './[NomModule]Autocomplete';
import { CategoryAutocomplete } from '@/features/categories/components/CategoryAutocomplete';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';
import { DatePicker } from '@/components/ui/date-picker';
import { toast } from '@/components/ui/toast';

// Schema de validation Zod
const formSchema = z.object({
  name: z.string()
    .min(1, 'Le nom est requis')
    .max(255, 'Maximum 255 caractères'),
  code: z.string()
    .min(2, 'Minimum 2 caractères')
    .max(50, 'Maximum 50 caractères')
    .regex(/^[A-Z0-9\-_]+$/, 'Uniquement lettres majuscules, chiffres, - et _')
    .optional()
    .nullable(),
  description: z.string()
    .max(2000, 'Maximum 2000 caractères')
    .optional()
    .nullable(),
  status: z.enum(['draft', 'active', 'inactive', 'archived']),
  amount: z.number()
    .min(0, 'Le montant doit être positif')
    .optional()
    .nullable(),
  start_date: z.date().optional().nullable(),
  end_date: z.date().optional().nullable(),
  category_id: z.string().uuid().optional().nullable(),
  parent_id: z.string().uuid().optional().nullable(),
  tags: z.array(z.string()).default([]),
}).refine(data => {
  if (data.start_date && data.end_date) {
    return data.end_date >= data.start_date;
  }
  return true;
}, {
  message: 'La date de fin doit être après la date de début',
  path: ['end_date']
});

type FormData = z.infer<typeof formSchema>;

interface Props {
  id?: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function [NomModule]Form({ id, onSuccess, onCancel }: Props) {
  const isEdit = !!id;

  // Charger données existantes
  const { data: existing, isLoading: isLoadingExisting } = use[NomModule](id);

  // Mutations
  const { create, update } = use[NomModule]Mutations();

  // Form
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      code: '',
      description: '',
      status: 'draft',
      amount: null,
      start_date: null,
      end_date: null,
      category_id: null,
      parent_id: null,
      tags: []
    }
  });

  const { register, control, handleSubmit, reset, setError, formState: { errors, isSubmitting } } = form;

  // Charger valeurs existantes
  useEffect(() => {
    if (existing) {
      reset({
        name: existing.name,
        code: existing.code,
        description: existing.description,
        status: existing.status,
        amount: existing.amount,
        start_date: existing.start_date ? new Date(existing.start_date) : null,
        end_date: existing.end_date ? new Date(existing.end_date) : null,
        category_id: existing.category_id,
        parent_id: existing.parent_id,
        tags: existing.tags || []
      });
    }
  }, [existing, reset]);

  // Submit
  const onSubmit = async (data: FormData) => {
    try {
      if (isEdit) {
        await update.mutateAsync({ id, data });
        toast.success('Modifications enregistrées');
      } else {
        await create.mutateAsync(data);
        toast.success('Créé avec succès');
      }
      onSuccess?.();
    } catch (error: any) {
      // Gérer erreurs serveur
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;

        // Erreur de champ spécifique
        if (typeof detail === 'string') {
          if (detail.includes('code')) {
            setError('code', { message: detail });
          } else {
            toast.error(detail);
          }
        }

        // Erreurs de validation multiples
        if (Array.isArray(detail)) {
          detail.forEach((err: any) => {
            if (err.loc && err.msg) {
              const field = err.loc[err.loc.length - 1];
              setError(field as any, { message: err.msg });
            }
          });
        }
      } else {
        toast.error('Une erreur est survenue');
      }
    }
  };

  if (isEdit && isLoadingExisting) {
    return <div className="p-4">Chargement...</div>;
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Nom */}
      <div>
        <label className="block text-sm font-medium mb-1">
          Nom <span className="text-red-500">*</span>
        </label>
        <Input
          {...register('name')}
          placeholder="Nom de l'entité"
          error={errors.name?.message}
        />
      </div>

      {/* Code */}
      <div>
        <label className="block text-sm font-medium mb-1">
          Code
        </label>
        <Input
          {...register('code')}
          placeholder="CODE-AUTO"
          className="uppercase"
          error={errors.code?.message}
        />
        <p className="text-xs text-gray-500 mt-1">
          Laissez vide pour génération automatique
        </p>
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium mb-1">
          Description
        </label>
        <Textarea
          {...register('description')}
          placeholder="Description détaillée..."
          rows={3}
          error={errors.description?.message}
        />
      </div>

      {/* Statut */}
      <div>
        <label className="block text-sm font-medium mb-1">
          Statut
        </label>
        <Controller
          name="status"
          control={control}
          render={({ field }) => (
            <Select {...field} error={errors.status?.message}>
              <option value="draft">Brouillon</option>
              <option value="active">Actif</option>
              <option value="inactive">Inactif</option>
              <option value="archived">Archivé</option>
            </Select>
          )}
        />
      </div>

      {/* Montant */}
      <div>
        <label className="block text-sm font-medium mb-1">
          Montant
        </label>
        <Input
          type="number"
          step="0.01"
          min="0"
          {...register('amount', { valueAsNumber: true })}
          placeholder="0.00"
          error={errors.amount?.message}
        />
      </div>

      {/* Dates */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">
            Date début
          </label>
          <Controller
            name="start_date"
            control={control}
            render={({ field }) => (
              <DatePicker
                value={field.value}
                onChange={field.onChange}
                error={errors.start_date?.message}
              />
            )}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">
            Date fin
          </label>
          <Controller
            name="end_date"
            control={control}
            render={({ field }) => (
              <DatePicker
                value={field.value}
                onChange={field.onChange}
                error={errors.end_date?.message}
              />
            )}
          />
        </div>
      </div>

      {/* Catégorie - Autocomplete */}
      <div>
        <Controller
          name="category_id"
          control={control}
          render={({ field }) => (
            <CategoryAutocomplete
              value={field.value}
              onChange={field.onChange}
              label="Catégorie"
              placeholder="Rechercher une catégorie..."
              error={errors.category_id?.message}
            />
          )}
        />
      </div>

      {/* Parent - Autocomplete (même module) */}
      <div>
        <Controller
          name="parent_id"
          control={control}
          render={({ field }) => (
            <[NomModule]Autocomplete
              value={field.value}
              onChange={field.onChange}
              label="Parent"
              placeholder="Rechercher un parent..."
              error={errors.parent_id?.message}
              // Exclure l'élément courant (éviter auto-référence)
              filterFn={id ? (item) => item.id !== id : undefined}
            />
          )}
        />
      </div>

      {/* Tags */}
      <div>
        <label className="block text-sm font-medium mb-1">
          Tags
        </label>
        <Controller
          name="tags"
          control={control}
          render={({ field }) => (
            <TagInput
              value={field.value}
              onChange={field.onChange}
              placeholder="Ajouter des tags..."
            />
          )}
        />
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Annuler
        </Button>
        <Button
          type="submit"
          loading={isSubmitting}
        >
          {isEdit ? 'Enregistrer' : 'Créer'}
        </Button>
      </div>
    </form>
  );
}
```

---

## CHECKLIST FINALE

```
┌─────────────────────────────────────────────────────────────────┐
│               MODULE 100% COMPLET - CHECKLIST                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ BACKEND                                                         │
│ ├─ [x] Models avec tenant_id, soft delete, audit, version      │
│ ├─ [x] Repository avec cache, search, bulk                     │
│ ├─ [x] Service avec validation, events, audit                  │
│ ├─ [x] Schemas avec validation Pydantic complète               │
│ ├─ [x] Router CRUD avec permissions                            │
│ ├─ [x] Router search avec autocomplete                         │
│ ├─ [x] Router bulk avec create/update/delete                   │
│ ├─ [x] Router export avec import/export/stats                  │
│ └─ [x] Tests isolation multi-tenant                            │
│                                                                 │
│ FRONTEND                                                        │
│ ├─ [x] Types correspondant exactement au backend               │
│ ├─ [x] API client complet (CRUD + search + bulk)               │
│ ├─ [x] Hooks React Query avec cache                            │
│ ├─ [x] Autocomplete avec debounce et cache                     │
│ ├─ [x] Formulaire avec validation Zod                          │
│ ├─ [x] Liste avec filtres et pagination                        │
│ ├─ [x] Gestion tous les états (loading, error, empty)          │
│ ├─ [x] Accessibilité ARIA                                      │
│ └─ [x] Responsive                                              │
│                                                                 │
│ FONCTIONNALITÉS                                                 │
│ ├─ [x] CRUD complet                                            │
│ ├─ [x] Recherche full-text                                     │
│ ├─ [x] Autocomplete performant                                 │
│ ├─ [x] Filtres avancés                                         │
│ ├─ [x] Pagination offset + cursor                              │
│ ├─ [x] Soft delete + restore                                   │
│ ├─ [x] Bulk operations                                         │
│ ├─ [x] Import/Export                                           │
│ ├─ [x] Statistiques                                            │
│ └─ [x] Audit trail                                             │
│                                                                 │
│ SÉCURITÉ                                                        │
│ ├─ [x] Isolation tenant sur toutes les queries                 │
│ ├─ [x] Permissions sur toutes les routes                       │
│ ├─ [x] Validation entrées complète                             │
│ ├─ [x] Tests d'isolation cross-tenant                          │
│ └─ [x] Audit des actions sensibles                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

*Document V2 - Édition complète pour modules 100% fonctionnels*
*AZALSCORE - 2026-02-20*
```
