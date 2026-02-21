# Agent A: Développement Complet Modules A-I

**Projet:** AZALSCORE ERP SaaS Multi-tenant
**Territoire:** Modules commençant par A à I (48 modules)
**Chemin base:** `/home/ubuntu/azalscore/`

---

## RÈGLES FONDAMENTALES (NON NÉGOCIABLES)

```
┌─────────────────────────────────────────────────────────────────┐
│  VÉRITÉ ABSOLUE - CORRECTION IMMÉDIATE - RÉFÉRENCE TECHNIQUE    │
│  SÉCURITÉ MAXIMALE - MULTI-TENANT STRICT - NE RIEN CASSER       │
└─────────────────────────────────────────────────────────────────┘
```

### Vérité et Qualité
1. **PAS DE MENSONGE** - Si tu ne sais pas, dis-le. Jamais de "j'ai fait" sans avoir fait.
2. **PAS DE REPORT** - Corrige immédiatement. Pas de "TODO", "à faire plus tard", "à améliorer".
3. **RÉFÉRENCE TECHNIQUE** - Code niveau expert. Un CTO doit pouvoir auditer sans trouver de faille.
4. **TESTS RÉELS** - Tests qui passent vraiment. Exécute pytest et montre les résultats.

### Multi-tenant et Sécurité
5. **ISOLATION TENANT** - `tenant_id` sur TOUTES les entités. `_base_query()` TOUJOURS filtré.
6. **SOFT DELETE** - `is_deleted`, `deleted_at`, `deleted_by` sur toutes les entités.
7. **AUDIT COMPLET** - `created_at`, `created_by`, `updated_at`, `updated_by` partout.
8. **VERSION** - Champ `version` pour optimistic locking.
9. **PERMISSIONS** - `require_permission()` sur chaque endpoint.

### Fonctionnalité
10. **CRUD COMPLET** - Create, Read, Update, Delete, Restore, List avec pagination.
11. **AUTOCOMPLETE** - Debounce 300ms, cache, navigation clavier, ARIA.
12. **BULK** - Opérations en masse (create, update, delete) avec rapport d'erreurs.
13. **IMPORT/EXPORT** - JSON, CSV minimum.
14. **FILTRES AVANCÉS** - Multi-critères, tri multi-colonnes, pagination cursor.

### Code Quality
15. **PEP8** - Respect strict des conventions Python.
16. **TYPE HINTS** - Typage complet sur toutes les fonctions.
17. **DOCSTRINGS** - Documentation des classes et méthodes publiques.
18. **NO MAGIC** - Pas de valeurs magiques, utiliser des constantes.

---

## TES 48 MODULES

### Priorité HAUTE (GAPs - faire en premier)

| # | Module | Priorité |
|---|--------|----------|
| 1 | approval | **GAP-083** |
| 2 | expense | **GAP-084** |
| 3 | fieldservice | **GAP-081** |
| 4 | forecasting | **GAP-076** |
| 5 | integration | **GAP-086** |

### Priorité Standard (ordre alphabétique après)

| # | Module | # | Module |
|---|--------|---|--------|
| 6 | accounting | 27 | email |
| 7 | ai_assistant | 28 | enrichment |
| 8 | appointments | 29 | esignature |
| 9 | assets | 30 | events |
| 10 | audit | 31 | expenses |
| 11 | autoconfig | 32 | field_service |
| 12 | automated_accounting | 33 | finance |
| 13 | backup | 34 | fleet |
| 14 | bi | 35 | gamification |
| 15 | broadcast | 36 | gateway |
| 16 | budget | 37 | guardian |
| 17 | cache | 38 | helpdesk |
| 18 | commercial | 39 | hr |
| 19 | commissions | 40 | hr_vault |
| 20 | complaints | 41 | i18n |
| 21 | compliance | 42 | iam |
| 22 | consolidation | 43 | integrations |
| 23 | contacts | 44 | interventions |
| 24 | contracts | 45 | - |
| 25 | country_packs | 46 | - |
| 26 | currency | 47 | - |
| - | dashboards | 48 | dataexchange |
| - | documents | - | ecommerce |

---

## STRUCTURE COMPLÈTE PAR MODULE

### Backend: `/app/modules/[nom_module]/`

```
/app/modules/[nom_module]/
├── __init__.py              # Exports publics
├── models.py                # Modèles SQLAlchemy
├── schemas.py               # Schémas Pydantic
├── repository.py            # Accès données
├── service.py               # Logique métier
├── router.py                # Routes CRUD + autocomplete
├── router_bulk.py           # Routes bulk operations
├── router_export.py         # Routes import/export
├── exceptions.py            # Exceptions métier
├── filters.py               # Classes de filtres
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_models.py
    ├── test_repository.py
    ├── test_service.py
    └── test_security.py     # Tests isolation tenant
```

### Frontend: `/frontend/src/features/[nom-module]/`

```
/frontend/src/features/[nom-module]/
├── index.ts
├── types.ts
├── api.ts
├── hooks/
│   ├── index.ts
│   ├── use[NomModule].ts
│   ├── use[NomModule]Mutations.ts
│   └── use[NomModule]Autocomplete.ts
├── components/
│   ├── index.ts
│   ├── [NomModule]List.tsx
│   ├── [NomModule]Form.tsx
│   ├── [NomModule]Detail.tsx
│   ├── [NomModule]Autocomplete.tsx
│   ├── [NomModule]Filters.tsx
│   └── [NomModule]BulkActions.tsx
└── pages/
    └── [NomModule]Page.tsx
```

---

## TEMPLATES BACKEND

### models.py

```python
"""
Modèles SQLAlchemy [NOM_MODULE]
- Multi-tenant obligatoire
- Soft delete
- Audit complet
- Versioning
"""
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    Numeric, Enum as SQLEnum, event
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship, validates, backref
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid

from app.core.database import Base


class [NomEntite]Status(str, Enum):
    """Statuts avec transitions validées"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

    @classmethod
    def allowed_transitions(cls) -> dict:
        return {
            cls.DRAFT: [cls.ACTIVE, cls.ARCHIVED],
            cls.ACTIVE: [cls.INACTIVE, cls.ARCHIVED],
            cls.INACTIVE: [cls.ACTIVE, cls.ARCHIVED],
            cls.ARCHIVED: []  # État terminal
        }


class [NomEntite](Base):
    """
    Modèle principal [NomEntite]

    Champs obligatoires:
    - tenant_id: Isolation multi-tenant
    - is_deleted, deleted_at, deleted_by: Soft delete
    - created_at, created_by, updated_at, updated_by: Audit
    - version: Optimistic locking
    """
    __tablename__ = "[nom_entites]"

    # === OBLIGATOIRE: Identifiants ===
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    code = Column(String(50), nullable=False)

    # === Champs métier ===
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        SQLEnum([NomEntite]Status),
        default=[NomEntite]Status.DRAFT,
        nullable=False
    )

    # === Champs numériques ===
    amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    quantity = Column(Integer, default=0)

    # === Dates métier ===
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # === Flexibilité ===
    tags = Column(ARRAY(String), default=list)
    metadata = Column(JSONB, default=dict)

    # === Relations ===
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

    # === OBLIGATOIRE: Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # === OBLIGATOIRE: Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)

    # === OBLIGATOIRE: Version ===
    version = Column(Integer, default=1, nullable=False)

    # === Contraintes ===
    __table_args__ = (
        Index('ix_[nom]_tenant', 'tenant_id'),
        Index('ix_[nom]_tenant_code', 'tenant_id', 'code'),
        Index('ix_[nom]_tenant_status', 'tenant_id', 'status'),
        Index('ix_[nom]_tenant_deleted', 'tenant_id', 'is_deleted'),
        UniqueConstraint('tenant_id', 'code', name='uq_[nom]_tenant_code'),
        CheckConstraint('amount >= 0', name='ck_[nom]_amount_positive'),
        CheckConstraint(
            'end_date IS NULL OR start_date IS NULL OR end_date >= start_date',
            name='ck_[nom]_dates_valid'
        ),
    )

    # === Validateurs ===
    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    @validates('status')
    def validate_status_transition(self, key: str, new_status: [NomEntite]Status) -> [NomEntite]Status:
        if self.status is not None and new_status != self.status:
            allowed = [NomEntite]Status.allowed_transitions().get(self.status, [])
            if new_status not in allowed:
                raise ValueError(f"Invalid transition from {self.status} to {new_status}")
        return new_status

    # === Propriétés ===
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
        if hasattr(self, 'children') and self.children.count() > 0:
            return False, "Cannot delete entity with children"
        return True, ""

    def __repr__(self) -> str:
        return f"<[NomEntite] {self.code}: {self.name}>"


# === Event listeners ===
@event.listens_for([NomEntite], 'before_update')
def before_update(mapper, connection, target):
    """Incrémenter version avant mise à jour"""
    target.version += 1
```

### schemas.py

```python
"""
Schémas Pydantic [NOM_MODULE]
- Validation stricte
- Types correspondant exactement au frontend
"""
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class [NomEntite]Status(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


# === Base ===
class [NomEntite]Base(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=5000)
    status: [NomEntite]Status = Field(default=[NomEntite]Status.DRAFT)
    amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    quantity: Optional[int] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    parent_id: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v

    @model_validator(mode='after')
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError('end_date must be after start_date')
        return self


class [NomEntite]Create([NomEntite]Base):
    """Création - name obligatoire"""
    pass


class [NomEntite]Update(BaseModel):
    """Mise à jour - tous champs optionnels"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    status: Optional[[NomEntite]Status] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    parent_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


# === Réponses ===
class [NomEntite]Response([NomEntite]Base):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    version: int = 1


class [NomEntite]ListItem(BaseModel):
    """Item léger pour les listes"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    status: [NomEntite]Status
    amount: Optional[Decimal] = None
    created_at: datetime


class [NomEntite]List(BaseModel):
    """Réponse paginée"""
    items: List[[NomEntite]ListItem]
    total: int
    page: int
    page_size: int
    pages: int


# === Autocomplete ===
class AutocompleteItem(BaseModel):
    id: str
    code: str
    name: str
    label: str  # "[CODE] Name"


class AutocompleteResponse(BaseModel):
    items: List[AutocompleteItem]


# === Bulk ===
class BulkCreateRequest(BaseModel):
    items: List[[NomEntite]Create] = Field(..., min_length=1, max_length=1000)


class BulkUpdateRequest(BaseModel):
    ids: List[UUID] = Field(..., min_length=1, max_length=1000)
    data: [NomEntite]Update


class BulkDeleteRequest(BaseModel):
    ids: List[UUID] = Field(..., min_length=1, max_length=1000)
    hard: bool = False


class BulkResult(BaseModel):
    success: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# === Filtres ===
class [NomEntite]Filters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    status: Optional[List[[NomEntite]Status]] = None
    tags: Optional[List[str]] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
```

### repository.py

```python
"""
Repository [NOM_MODULE]
- CRITIQUE: Toutes les requêtes filtrées par tenant_id
- Optimisations et cache
"""
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session

from .models import [NomEntite], [NomEntite]Status
from .schemas import [NomEntite]Filters


class [NomEntite]Repository:
    """
    Repository avec isolation tenant obligatoire.

    SÉCURITÉ: _base_query() filtre TOUJOURS par tenant_id
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

    def _base_query(self):
        """
        CRITIQUE: Point d'entrée unique pour toutes les requêtes.
        TOUJOURS filtrer par tenant_id.
        """
        query = self.db.query([NomEntite]).filter(
            [NomEntite].tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter([NomEntite].is_deleted == False)
        return query

    # === READ ===
    def get_by_id(self, id: UUID) -> Optional[[NomEntite]]:
        return self._base_query().filter([NomEntite].id == id).first()

    def get_by_code(self, code: str) -> Optional[[NomEntite]]:
        return self._base_query().filter(
            [NomEntite].code == code.upper()
        ).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter([NomEntite].id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter([NomEntite].code == code.upper())
        if exclude_id:
            query = query.filter([NomEntite].id != exclude_id)
        return query.count() > 0

    # === LIST ===
    def list(
        self,
        filters: [NomEntite]Filters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[[NomEntite]], int]:
        query = self._base_query()

        if filters:
            query = self._apply_filters(query, filters)

        total = query.count()

        # Tri
        sort_col = getattr([NomEntite], sort_by, [NomEntite].created_at)
        query = query.order_by(
            desc(sort_col) if sort_dir == "desc" else asc(sort_col)
        )

        # Pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def _apply_filters(self, query, filters: [NomEntite]Filters):
        """Applique les filtres à la requête"""
        if filters.search:
            term = f"%{filters.search}%"
            query = query.filter(or_(
                [NomEntite].name.ilike(term),
                [NomEntite].code.ilike(term),
                [NomEntite].description.ilike(term)
            ))

        if filters.status:
            query = query.filter([NomEntite].status.in_(filters.status))

        if filters.tags:
            query = query.filter([NomEntite].tags.overlap(filters.tags))

        if filters.date_from:
            query = query.filter([NomEntite].created_at >= filters.date_from)

        if filters.date_to:
            query = query.filter([NomEntite].created_at <= filters.date_to)

        if filters.amount_min is not None:
            query = query.filter([NomEntite].amount >= filters.amount_min)

        if filters.amount_max is not None:
            query = query.filter([NomEntite].amount <= filters.amount_max)

        return query

    # === AUTOCOMPLETE ===
    def autocomplete(
        self,
        prefix: str,
        field: str = "name",
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Autocomplete avec format standardisé.
        Retourne uniquement les entités actives.
        """
        if len(prefix) < 2:
            return []

        query = self._base_query().filter(
            [NomEntite].status == [NomEntite]Status.ACTIVE
        )

        if field == "code":
            query = query.filter([NomEntite].code.ilike(f"{prefix}%"))
        else:
            query = query.filter(or_(
                [NomEntite].name.ilike(f"{prefix}%"),
                [NomEntite].code.ilike(f"{prefix}%")
            ))

        results = query.order_by([NomEntite].name).limit(limit).all()

        return [
            {
                "id": str(item.id),
                "code": item.code,
                "name": item.name,
                "label": f"[{item.code}] {item.name}"
            }
            for item in results
        ]

    # === CREATE ===
    def create(self, data: Dict[str, Any], created_by: UUID = None) -> [NomEntite]:
        entity = [NomEntite](
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    # === UPDATE ===
    def update(
        self,
        entity: [NomEntite],
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> [NomEntite]:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    # === DELETE ===
    def soft_delete(self, entity: [NomEntite], deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def hard_delete(self, entity: [NomEntite]) -> bool:
        self.db.delete(entity)
        self.db.commit()
        return True

    def restore(self, entity: [NomEntite]) -> [NomEntite]:
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        self.db.commit()
        self.db.refresh(entity)
        return entity

    # === BULK ===
    def bulk_create(
        self,
        items: List[Dict[str, Any]],
        created_by: UUID = None
    ) -> int:
        now = datetime.utcnow()
        for item in items:
            item["tenant_id"] = self.tenant_id
            item["created_at"] = now
            item["created_by"] = created_by
        self.db.bulk_insert_mappings([NomEntite], items)
        self.db.commit()
        return len(items)

    def bulk_update(
        self,
        ids: List[UUID],
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> int:
        data["updated_at"] = datetime.utcnow()
        data["updated_by"] = updated_by
        result = self._base_query().filter(
            [NomEntite].id.in_(ids)
        ).update(data, synchronize_session=False)
        self.db.commit()
        return result

    def bulk_delete(
        self,
        ids: List[UUID],
        deleted_by: UUID = None,
        hard: bool = False
    ) -> int:
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
        return result

    # === STATS ===
    def get_stats(self) -> Dict[str, Any]:
        base = self._base_query()
        total = base.count()
        by_status = {}
        for status in [NomEntite]Status:
            by_status[status.value] = base.filter(
                [NomEntite].status == status
            ).count()
        return {
            "total": total,
            "by_status": by_status
        }
```

### service.py

```python
"""
Service [NOM_MODULE]
- Logique métier
- Validation des règles
- Orchestration
"""
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from .models import [NomEntite], [NomEntite]Status
from .repository import [NomEntite]Repository
from .schemas import [NomEntite]Create, [NomEntite]Update, [NomEntite]Filters
from .exceptions import (
    [NomEntite]NotFoundError,
    [NomEntite]DuplicateError,
    [NomEntite]ValidationError,
    [NomEntite]StateError
)


class [NomModule]Service:
    """
    Service métier pour [NomModule].
    Encapsule toute la logique métier.
    """

    def __init__(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID = None
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.repo = [NomEntite]Repository(db, tenant_id)

    # === READ ===
    def get(self, id: UUID) -> [NomEntite]:
        """Récupère une entité par ID"""
        entity = self.repo.get_by_id(id)
        if not entity:
            raise [NomEntite]NotFoundError(f"Entity {id} not found")
        return entity

    def get_by_code(self, code: str) -> [NomEntite]:
        """Récupère une entité par code"""
        entity = self.repo.get_by_code(code)
        if not entity:
            raise [NomEntite]NotFoundError(f"Entity code={code} not found")
        return entity

    def list(
        self,
        filters: [NomEntite]Filters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[[NomEntite]], int, int]:
        """Liste paginée avec filtres"""
        items, total = self.repo.list(filters, page, page_size, sort_by, sort_dir)
        pages = (total + page_size - 1) // page_size
        return items, total, pages

    # === CREATE ===
    def create(self, data: [NomEntite]Create) -> [NomEntite]:
        """Crée une nouvelle entité"""
        # Vérifier unicité code
        if data.code and self.repo.code_exists(data.code):
            raise [NomEntite]DuplicateError(f"Code {data.code} already exists")

        return self.repo.create(
            data.model_dump(exclude_unset=True),
            self.user_id
        )

    # === UPDATE ===
    def update(self, id: UUID, data: [NomEntite]Update) -> [NomEntite]:
        """Met à jour une entité"""
        entity = self.get(id)

        # Vérifier unicité code si changé
        if data.code and data.code != entity.code:
            if self.repo.code_exists(data.code, exclude_id=id):
                raise [NomEntite]DuplicateError(f"Code {data.code} already exists")

        # Valider transition de statut
        if data.status and data.status != entity.status:
            allowed = [NomEntite]Status.allowed_transitions().get(entity.status, [])
            if data.status not in allowed:
                raise [NomEntite]StateError(
                    f"Transition {entity.status} -> {data.status} not allowed"
                )

        return self.repo.update(
            entity,
            data.model_dump(exclude_unset=True),
            self.user_id
        )

    # === DELETE ===
    def delete(self, id: UUID, hard: bool = False) -> bool:
        """Supprime une entité (soft par défaut)"""
        entity = self.get(id)

        can_delete, reason = entity.can_delete()
        if not can_delete:
            raise [NomEntite]ValidationError(reason)

        if hard:
            return self.repo.hard_delete(entity)
        return self.repo.soft_delete(entity, self.user_id)

    def restore(self, id: UUID) -> [NomEntite]:
        """Restaure une entité supprimée"""
        repo_deleted = [NomEntite]Repository(
            self.db, self.tenant_id, include_deleted=True
        )
        entity = repo_deleted.get_by_id(id)

        if not entity:
            raise [NomEntite]NotFoundError(f"Entity {id} not found")
        if not entity.is_deleted:
            raise [NomEntite]ValidationError("Entity is not deleted")

        return self.repo.restore(entity)

    # === AUTOCOMPLETE ===
    def autocomplete(
        self,
        prefix: str,
        field: str = "name",
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Autocomplete pour les sélecteurs"""
        return self.repo.autocomplete(prefix, field, limit)

    # === BULK ===
    def bulk_create(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Création en masse avec rapport d'erreurs"""
        errors = []
        valid = []

        for i, item in enumerate(items):
            if item.get("code") and self.repo.code_exists(item["code"]):
                errors.append({
                    "index": i,
                    "error": f"Code {item['code']} already exists"
                })
            else:
                valid.append(item)

        count = self.repo.bulk_create(valid, self.user_id) if valid else 0
        return {"success": count, "errors": errors}

    def bulk_update(
        self,
        ids: List[UUID],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mise à jour en masse"""
        existing = [id for id in ids if self.repo.exists(id)]
        missing = [str(id) for id in ids if id not in existing]

        count = 0
        if existing:
            count = self.repo.bulk_update(existing, data, self.user_id)

        errors = [{"id": id, "error": "Not found"} for id in missing]
        return {"success": count, "errors": errors}

    def bulk_delete(
        self,
        ids: List[UUID],
        hard: bool = False
    ) -> Dict[str, Any]:
        """Suppression en masse"""
        deletable = []
        errors = []

        for id in ids:
            try:
                entity = self.get(id)
                can, reason = entity.can_delete()
                if can:
                    deletable.append(id)
                else:
                    errors.append({"id": str(id), "error": reason})
            except [NomEntite]NotFoundError:
                errors.append({"id": str(id), "error": "Not found"})

        count = 0
        if deletable:
            count = self.repo.bulk_delete(deletable, self.user_id, hard)

        return {"success": count, "errors": errors}

    # === STATS ===
    def get_stats(self) -> Dict[str, Any]:
        """Statistiques du module"""
        return self.repo.get_stats()
```

### router.py

```python
"""
Routes API [NOM_MODULE]
- CRUD complet
- Autocomplete
- Permissions vérifiées
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID

from app.core.security import get_current_user, require_permission
from app.core.database import get_db
from sqlalchemy.orm import Session

from .service import [NomModule]Service
from .schemas import (
    [NomEntite]Create,
    [NomEntite]Update,
    [NomEntite]Response,
    [NomEntite]List,
    [NomEntite]Filters,
    AutocompleteResponse,
    BulkCreateRequest,
    BulkUpdateRequest,
    BulkDeleteRequest,
    BulkResult
)
from .models import [NomEntite]Status
from .exceptions import (
    [NomEntite]NotFoundError,
    [NomEntite]DuplicateError,
    [NomEntite]ValidationError,
    [NomEntite]StateError
)

router = APIRouter(prefix="/[nom-module]", tags=["[NOM_MODULE]"])


def get_service(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
) -> [NomModule]Service:
    return [NomModule]Service(db, user.tenant_id, user.id)


# === LIST ===
@router.get("/", response_model=[NomEntite]List)
async def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[List[[NomEntite]Status]] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].view"))
):
    """Liste paginée avec filtres"""
    filters = [NomEntite]Filters(search=search, status=status)
    items, total, pages = service.list(filters, page, page_size, sort_by, sort_dir)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


# === AUTOCOMPLETE ===
@router.get("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(
    prefix: str = Query(..., min_length=2),
    field: str = Query("name", pattern="^(name|code)$"),
    limit: int = Query(10, ge=1, le=50),
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].view"))
):
    """Autocomplete pour sélecteurs"""
    items = service.autocomplete(prefix, field, limit)
    return {"items": items}


# === GET ===
@router.get("/{id}", response_model=[NomEntite]Response)
async def get_item(
    id: UUID,
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].view"))
):
    """Récupère une entité par ID"""
    try:
        return service.get(id)
    except [NomEntite]NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# === CREATE ===
@router.post("/", response_model=[NomEntite]Response, status_code=201)
async def create_item(
    data: [NomEntite]Create,
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].create"))
):
    """Crée une nouvelle entité"""
    try:
        return service.create(data)
    except [NomEntite]DuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


# === UPDATE ===
@router.put("/{id}", response_model=[NomEntite]Response)
async def update_item(
    id: UUID,
    data: [NomEntite]Update,
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].edit"))
):
    """Met à jour une entité"""
    try:
        return service.update(id, data)
    except [NomEntite]NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ([NomEntite]DuplicateError, [NomEntite]StateError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# === DELETE ===
@router.delete("/{id}", status_code=204)
async def delete_item(
    id: UUID,
    hard: bool = Query(False),
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].delete"))
):
    """Supprime une entité"""
    try:
        service.delete(id, hard)
    except [NomEntite]NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except [NomEntite]ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# === RESTORE ===
@router.post("/{id}/restore", response_model=[NomEntite]Response)
async def restore_item(
    id: UUID,
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].delete"))
):
    """Restaure une entité supprimée"""
    try:
        return service.restore(id)
    except ([NomEntite]NotFoundError, [NomEntite]ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# === BULK ===
@router.post("/bulk/create", response_model=BulkResult)
async def bulk_create(
    request: BulkCreateRequest,
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].create"))
):
    """Création en masse"""
    return service.bulk_create([i.model_dump() for i in request.items])


@router.post("/bulk/update", response_model=BulkResult)
async def bulk_update(
    request: BulkUpdateRequest,
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].edit"))
):
    """Mise à jour en masse"""
    return service.bulk_update(request.ids, request.data.model_dump(exclude_unset=True))


@router.post("/bulk/delete", response_model=BulkResult)
async def bulk_delete(
    request: BulkDeleteRequest,
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].delete"))
):
    """Suppression en masse"""
    return service.bulk_delete(request.ids, request.hard)


# === STATS ===
@router.get("/stats", response_model=dict)
async def get_stats(
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].view"))
):
    """Statistiques du module"""
    return service.get_stats()
```

### exceptions.py

```python
"""
Exceptions métier [NOM_MODULE]
"""


class [NomModule]Error(Exception):
    """Exception de base du module"""
    pass


class [NomEntite]NotFoundError([NomModule]Error):
    """Entité non trouvée"""
    pass


class [NomEntite]DuplicateError([NomModule]Error):
    """Code ou entité déjà existante"""
    pass


class [NomEntite]ValidationError([NomModule]Error):
    """Erreur de validation métier"""
    pass


class [NomEntite]StateError([NomModule]Error):
    """Transition d'état invalide"""
    pass
```

### tests/test_security.py

```python
"""
Tests Sécurité Multi-tenant
CRITIQUE: Vérifier l'isolation entre tenants
"""
import pytest
from uuid import uuid4

from ..service import [NomModule]Service
from ..exceptions import [NomEntite]NotFoundError


class TestTenantIsolation:
    """Tests d'isolation tenant - CRITIQUES"""

    def test_cannot_access_other_tenant_data(
        self,
        db_session,
        tenant_a_id,
        tenant_b_id,
        entity_tenant_b
    ):
        """Un tenant ne peut pas voir les données d'un autre tenant"""
        service_a = [NomModule]Service(db_session, tenant_a_id)

        with pytest.raises([NomEntite]NotFoundError):
            service_a.get(entity_tenant_b.id)

    def test_list_only_shows_own_tenant(
        self,
        db_session,
        tenant_a_id,
        entities_mixed_tenants
    ):
        """List ne retourne que les entités du tenant courant"""
        service = [NomModule]Service(db_session, tenant_a_id)
        items, _, _ = service.list()

        for item in items:
            assert item.tenant_id == tenant_a_id

    def test_cannot_update_other_tenant(
        self,
        db_session,
        tenant_a_id,
        entity_tenant_b
    ):
        """Un tenant ne peut pas modifier les données d'un autre tenant"""
        service_a = [NomModule]Service(db_session, tenant_a_id)

        with pytest.raises([NomEntite]NotFoundError):
            service_a.update(entity_tenant_b.id, {"name": "Hacked"})

    def test_cannot_delete_other_tenant(
        self,
        db_session,
        tenant_a_id,
        entity_tenant_b
    ):
        """Un tenant ne peut pas supprimer les données d'un autre tenant"""
        service_a = [NomModule]Service(db_session, tenant_a_id)

        with pytest.raises([NomEntite]NotFoundError):
            service_a.delete(entity_tenant_b.id)

    def test_autocomplete_isolated(
        self,
        db_session,
        tenant_a_id,
        tenant_b_id,
        entities_mixed_tenants
    ):
        """Autocomplete ne retourne que les entités du tenant courant"""
        service_a = [NomModule]Service(db_session, tenant_a_id)
        results = service_a.autocomplete("test")

        # Vérifier que tous les résultats appartiennent au tenant A
        for item in results:
            entity = service_a.get(item["id"])
            assert entity.tenant_id == tenant_a_id

    def test_bulk_operations_isolated(
        self,
        db_session,
        tenant_a_id,
        entity_tenant_b
    ):
        """Les opérations bulk ne peuvent pas affecter d'autres tenants"""
        service_a = [NomModule]Service(db_session, tenant_a_id)

        # Tenter de supprimer une entité d'un autre tenant
        result = service_a.bulk_delete([entity_tenant_b.id])

        assert result["success"] == 0
        assert len(result["errors"]) == 1
        assert "Not found" in result["errors"][0]["error"]
```

---

## TEMPLATES FRONTEND

### types.ts

```typescript
/**
 * Types [NOM_MODULE]
 * DOIVENT correspondre EXACTEMENT au backend
 */

export type [NomEntite]Status = 'draft' | 'active' | 'inactive' | 'archived';

export interface [NomEntite] {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  status: [NomEntite]Status;
  amount?: number | null;
  quantity?: number | null;
  start_date?: string | null;
  end_date?: string | null;
  parent_id?: string | null;
  tags: string[];
  metadata: Record<string, any>;
  // Audit
  created_at: string;
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  // Soft delete
  is_deleted: boolean;
  deleted_at?: string | null;
  deleted_by?: string | null;
  // Version
  version: number;
}

export interface [NomEntite]Create {
  name: string;
  code?: string;
  description?: string | null;
  status?: [NomEntite]Status;
  amount?: number | null;
  quantity?: number | null;
  start_date?: string | null;
  end_date?: string | null;
  parent_id?: string | null;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface [NomEntite]Update {
  name?: string;
  code?: string;
  description?: string | null;
  status?: [NomEntite]Status;
  amount?: number | null;
  quantity?: number | null;
  start_date?: string | null;
  end_date?: string | null;
  parent_id?: string | null;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface [NomEntite]ListResponse {
  items: [NomEntite][];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface AutocompleteItem {
  id: string;
  code: string;
  name: string;
  label: string;
}

export interface BulkResult {
  success: number;
  errors: Array<{ id?: string; index?: number; error: string }>;
}

export interface [NomEntite]Filters {
  search?: string;
  status?: [NomEntite]Status[];
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_dir?: 'asc' | 'desc';
}
```

### hooks/use[NomModule]Autocomplete.ts

```typescript
/**
 * Hook Autocomplete
 * - Debounce 300ms
 * - Cache React Query
 * - Min 2 caractères
 */
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useDebounce } from '@/hooks/useDebounce';
import { [nomModule]Api } from '../api';
import type { AutocompleteItem } from '../types';

interface UseAutocompleteOptions {
  minChars?: number;
  limit?: number;
  field?: 'name' | 'code';
  enabled?: boolean;
}

export function use[NomModule]Autocomplete(
  prefix: string,
  options: UseAutocompleteOptions = {}
) {
  const {
    minChars = 2,
    limit = 10,
    field = 'name',
    enabled = true
  } = options;

  // Debounce 300ms
  const debouncedPrefix = useDebounce(prefix, 300);

  const shouldFetch = useMemo(
    () => enabled && debouncedPrefix.length >= minChars,
    [enabled, debouncedPrefix, minChars]
  );

  const query = useQuery({
    queryKey: ['[nom-module]', 'autocomplete', debouncedPrefix, field, limit],
    queryFn: () => [nomModule]Api.autocomplete(debouncedPrefix, field, limit),
    enabled: shouldFetch,
    staleTime: 60000,  // 1 minute
    gcTime: 300000,    // 5 minutes
    select: (data) => data.items
  });

  return {
    items: query.data ?? [],
    isLoading: query.isLoading && shouldFetch,
    isError: query.isError,
    error: query.error
  };
}
```

### components/[NomModule]Autocomplete.tsx

```typescript
/**
 * Composant Autocomplete complet
 * - Debounce intégré
 * - Navigation clavier (ArrowUp, ArrowDown, Enter, Escape)
 * - Accessibilité ARIA
 * - Affichage état chargement
 */
import { useState, useRef, useEffect, useCallback, forwardRef } from 'react';
import { Loader2, X, ChevronDown, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { use[NomModule]Autocomplete } from '../hooks/use[NomModule]Autocomplete';
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
}

export const [NomModule]Autocomplete = forwardRef<HTMLInputElement, Props>(({
  value,
  onChange,
  placeholder = "Rechercher...",
  disabled = false,
  error,
  label,
  required = false,
  className
}, ref) => {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [selectedItem, setSelectedItem] = useState<AutocompleteItem | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { items, isLoading } = use[NomModule]Autocomplete(inputValue, {
    enabled: isOpen
  });

  // Navigation clavier
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (disabled) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) setIsOpen(true);
        else setHighlightedIndex(i => (i < items.length - 1 ? i + 1 : 0));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(i => (i > 0 ? i - 1 : items.length - 1));
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && items[highlightedIndex]) {
          handleSelect(items[highlightedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setHighlightedIndex(-1);
        break;
    }
  }, [isOpen, items, highlightedIndex, disabled]);

  const handleSelect = useCallback((item: AutocompleteItem) => {
    setSelectedItem(item);
    setInputValue(item.name);
    setIsOpen(false);
    setHighlightedIndex(-1);
    onChange(item.id, item);
  }, [onChange]);

  const handleClear = useCallback(() => {
    setSelectedItem(null);
    setInputValue('');
    onChange(null);
  }, [onChange]);

  // Fermer au clic extérieur
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      <div className="relative">
        <input
          ref={ref}
          type="text"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            setIsOpen(true);
            setHighlightedIndex(-1);
            if (!e.target.value) handleClear();
          }}
          onFocus={() => setIsOpen(true)}
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
        />

        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {isLoading && <Loader2 className="w-4 h-4 animate-spin text-gray-400" />}
          {selectedItem && !disabled && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1 hover:bg-gray-100 rounded"
              aria-label="Effacer"
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

      {error && <p className="mt-1 text-sm text-red-500">{error}</p>}

      {isOpen && (
        <ul
          role="listbox"
          className="absolute z-50 w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-auto"
        >
          {isLoading && inputValue.length >= 2 && (
            <li className="px-3 py-2 text-gray-500 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Recherche...
            </li>
          )}

          {!isLoading && inputValue.length >= 2 && items.length === 0 && (
            <li className="px-3 py-2 text-gray-500">Aucun résultat</li>
          )}

          {inputValue.length > 0 && inputValue.length < 2 && (
            <li className="px-3 py-2 text-gray-500">Min 2 caractères</li>
          )}

          {items.map((item, index) => (
            <li
              key={item.id}
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

## INTÉGRATION

### main.py

```python
# === SECTION AGENT A - NE PAS MODIFIER SI AGENT B ===
from app.modules.[nom_module] import router as [nom_module]_router
app.include_router([nom_module]_router, prefix="/api/v1")
# === FIN SECTION AGENT A ===
```

### UnifiedApp.tsx

```typescript
// === SECTION AGENT A ===
import { [NomModule]Page } from './features/[nom-module]/pages';

// Dans le switch
case '[nom-module]':
  return <[NomModule]Page />;
// === FIN SECTION AGENT A ===
```

---

## TERRITOIRE INTERDIT

**NE TOUCHE JAMAIS** aux modules suivants (Agent B):
inventory, knowledge, loyalty, maintenance, manufacturing, marceau,
marketplace, mobile, notifications, odoo_import, pos, procurement,
production, projects, purchases, qc, quality, referral, rental,
requisition, resources, rfq, risk, scheduler, search, shipping,
signatures, sla, social_networks, storage, stripe_integration,
subscriptions, survey, surveys, templates, tenants, timesheet,
timetracking, training, treasury, triggers, visitor, warranty,
web, webhooks, website, workflows

---

## RAPPORT FINAL

```markdown
# Rapport Agent A - Modules A-I

## Résumé
- Modules traités: X/48
- Complets: X
- Partiels: X
- Erreurs: X

## Détail

| Module | Backend | Frontend | Tests | Intégration |
|--------|---------|----------|-------|-------------|
| approval | ✅ | ✅ | ✅ | ✅ |
| ... | | | | |

## Tests exécutés
```bash
pytest app/modules/[nom]/tests/ -v
# Résultats
```

## Problèmes
- [Liste]

## Actions requises
- [Liste]
```

---

*Agent A - AZALSCORE - 2026-02-20*
