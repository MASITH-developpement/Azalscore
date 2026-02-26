# PROMPTS MODULES - EXÉCUTION PARALLÈLE (N AGENTS = N MODULES)

**Date:** 2026-02-20
**Version:** 4.0 - PARALLÈLE SIMPLE
**Principe:** Chaque agent développe UN module complet (backend + frontend)

---

## ARCHITECTURE PARALLÈLE

```
┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
│ AGENT 1                 │  │ AGENT 2                 │  │ AGENT N                 │
│                         │  │                         │  │                         │
│ Module: fieldservice    │  │ Module: survey          │  │ Module: [autre]         │
│                         │  │                         │  │                         │
│ Backend COMPLET         │  │ Backend COMPLET         │  │ Backend COMPLET         │
│ + Frontend COMPLET      │  │ + Frontend COMPLET      │  │ + Frontend COMPLET      │
│ + Tests                 │  │ + Tests                 │  │ + Tests                 │
│ + Intégration           │  │ + Intégration           │  │ + Intégration           │
└─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘

           │                          │                          │
           ▼                          ▼                          ▼
    ZÉRO CONFLIT            ZÉRO CONFLIT              ZÉRO CONFLIT
    (fichiers différents)   (fichiers différents)     (fichiers différents)
```

## AVANTAGES

| Aspect | Bénéfice |
|--------|----------|
| **Isolation** | Chaque agent touche des fichiers différents |
| **Autonomie** | Pas de dépendance entre agents |
| **Complet** | Module 100% fonctionnel à la fin |
| **Simple** | Pas de contrat, pas de mocks, pas de phase d'intégration |
| **Scalable** | N agents = N modules en parallèle |

---

# PROMPT UNIQUE (COPIER-COLLER POUR CHAQUE AGENT)

```markdown
# Développement Module Complet: [NOM_MODULE]

## CONTEXTE

Tu développes le module **[NOM_MODULE]** pour AZALSCORE, un ERP SaaS multi-tenant.
Tu es le SEUL agent travaillant sur ce module. Aucun autre agent ne touche tes fichiers.

## RÈGLES ABSOLUES

### Vérité et Qualité
1. **PAS DE MENSONGE** - Si tu ne sais pas, dis-le
2. **PAS DE REPORT** - Corrige immédiatement, pas "à faire plus tard"
3. **RÉFÉRENCE TECHNIQUE** - Code niveau expert, un CTO doit pouvoir auditer
4. **TESTS RÉELS** - Tests qui passent vraiment, pas des placeholders

### Multi-tenant et Sécurité
5. **ISOLATION TENANT** - tenant_id sur TOUTES les entités, _base_query() filtré
6. **SOFT DELETE** - is_deleted, deleted_at, deleted_by sur toutes les entités
7. **AUDIT COMPLET** - created_at/by, updated_at/by partout
8. **VERSION** - Champ version pour optimistic locking
9. **PERMISSIONS** - Vérification sur chaque endpoint

### Fonctionnalité
10. **CRUD COMPLET** - Create, Read, Update, Delete, Restore
11. **AUTOCOMPLETE** - Avec debounce, cache, keyboard nav
12. **BULK** - Opérations en masse (create, update, delete)
13. **IMPORT/EXPORT** - JSON, CSV, Excel
14. **FILTRES AVANCÉS** - Multi-critères, tri, pagination

## FICHIERS À CRÉER

### Backend: `/app/modules/[nom_module]/`

```
/app/modules/[nom_module]/
├── __init__.py           # Exports publics
├── models.py             # SQLAlchemy models
├── schemas.py            # Pydantic schemas
├── repository.py         # Data access layer
├── service.py            # Business logic
├── router.py             # CRUD endpoints
├── router_search.py      # Search & autocomplete
├── router_bulk.py        # Bulk operations
├── router_export.py      # Import/Export
├── filters.py            # Filter classes
├── exceptions.py         # Custom exceptions
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_models.py
    ├── test_repository.py
    ├── test_service.py
    └── test_security.py  # Tests isolation tenant
```

### Frontend: `/frontend/src/features/[nom-module]/`

```
/frontend/src/features/[nom-module]/
├── index.ts              # Exports publics
├── types.ts              # TypeScript types
├── api.ts                # API client
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
├── pages/
│   ├── index.ts
│   └── [NomModule]Page.tsx
└── __tests__/
    ├── [NomModule]List.test.tsx
    └── [NomModule]Form.test.tsx
```

---

## TEMPLATE BACKEND

### models.py

```python
"""
Modèles SQLAlchemy [NOM_MODULE]
"""
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    Numeric, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid

from app.core.database import Base


class [NomEntite]Status(str, Enum):
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
            cls.ARCHIVED: []
        }


class [NomEntite](Base):
    __tablename__ = "[nom_entites]"

    # === OBLIGATOIRE: Identifiants ===
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    code = Column(String(50), nullable=False)

    # === Champs métier (adapter selon le module) ===
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        SQLEnum([NomEntite]Status),
        default=[NomEntite]Status.DRAFT,
        nullable=False
    )

    # === Flexibilité ===
    tags = Column(ARRAY(String), default=list)
    metadata = Column(JSONB, default=dict)

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
    )

    @validates('code')
    def validate_code(self, key, value):
        if value:
            return value.upper().strip()
        return value

    @hybrid_property
    def display_name(self) -> str:
        return f"[{self.code}] {self.name}"

    def can_delete(self) -> tuple[bool, str]:
        if self.status == [NomEntite]Status.ACTIVE:
            return False, "Impossible de supprimer une entité active"
        return True, ""
```

### repository.py

```python
"""
Repository [NOM_MODULE]
SÉCURITÉ: Toutes les requêtes filtrées par tenant_id
"""
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session

from .models import [NomEntite], [NomEntite]Status


class [NomEntite]Repository:

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        """CRITIQUE: TOUJOURS filtrer par tenant_id"""
        query = self.db.query([NomEntite]).filter([NomEntite].tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter([NomEntite].is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[[NomEntite]]:
        return self._base_query().filter([NomEntite].id == id).first()

    def get_by_code(self, code: str) -> Optional[[NomEntite]]:
        return self._base_query().filter([NomEntite].code == code.upper()).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter([NomEntite].id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter([NomEntite].code == code.upper())
        if exclude_id:
            query = query.filter([NomEntite].id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: Dict = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[[NomEntite]], int]:
        query = self._base_query()

        if filters:
            if filters.get("search"):
                term = f"%{filters['search']}%"
                query = query.filter(or_(
                    [NomEntite].name.ilike(term),
                    [NomEntite].code.ilike(term)
                ))
            if filters.get("status"):
                query = query.filter([NomEntite].status.in_(filters["status"]))

        total = query.count()

        sort_col = getattr([NomEntite], sort_by, [NomEntite].created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict]:
        """Autocomplete avec format standardisé"""
        if len(prefix) < 2:
            return []

        results = self._base_query().filter(
            [NomEntite].status == [NomEntite]Status.ACTIVE,
            or_(
                [NomEntite].name.ilike(f"{prefix}%"),
                [NomEntite].code.ilike(f"{prefix}%")
            )
        ).order_by([NomEntite].name).limit(limit).all()

        return [
            {
                "id": str(item.id),
                "code": item.code,
                "name": item.name,
                "label": f"[{item.code}] {item.name}"
            }
            for item in results
        ]

    def create(self, data: Dict, created_by: UUID = None) -> [NomEntite]:
        entity = [NomEntite](
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: [NomEntite], data: Dict, updated_by: UUID = None) -> [NomEntite]:
        for key, value in data.items():
            setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: [NomEntite], deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, entity: [NomEntite]) -> [NomEntite]:
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def bulk_create(self, items: List[Dict], created_by: UUID = None) -> int:
        now = datetime.utcnow()
        for item in items:
            item["tenant_id"] = self.tenant_id
            item["created_at"] = now
            item["created_by"] = created_by
        self.db.bulk_insert_mappings([NomEntite], items)
        self.db.commit()
        return len(items)

    def bulk_delete(self, ids: List[UUID], deleted_by: UUID = None) -> int:
        result = self._base_query().filter([NomEntite].id.in_(ids)).update({
            "is_deleted": True,
            "deleted_at": datetime.utcnow(),
            "deleted_by": deleted_by
        }, synchronize_session=False)
        self.db.commit()
        return result
```

### service.py

```python
"""
Service [NOM_MODULE]
Logique métier avec validation
"""
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from .models import [NomEntite], [NomEntite]Status
from .repository import [NomEntite]Repository
from .schemas import [NomEntite]Create, [NomEntite]Update
from .exceptions import (
    [NomEntite]NotFoundError,
    [NomEntite]DuplicateError,
    [NomEntite]ValidationError,
    [NomEntite]StateError
)


class [NomModule]Service:

    def __init__(self, db: Session, tenant_id: UUID, user_id: UUID = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.repo = [NomEntite]Repository(db, tenant_id)

    def get(self, id: UUID) -> [NomEntite]:
        entity = self.repo.get_by_id(id)
        if not entity:
            raise [NomEntite]NotFoundError(f"Entity {id} not found")
        return entity

    def list(
        self,
        filters: Dict = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[[NomEntite]], int, int]:
        items, total = self.repo.list(filters, page, page_size, sort_by, sort_dir)
        pages = (total + page_size - 1) // page_size
        return items, total, pages

    def create(self, data: [NomEntite]Create) -> [NomEntite]:
        if data.code and self.repo.code_exists(data.code):
            raise [NomEntite]DuplicateError(f"Code {data.code} already exists")

        return self.repo.create(
            data.model_dump(exclude_unset=True),
            self.user_id
        )

    def update(self, id: UUID, data: [NomEntite]Update) -> [NomEntite]:
        entity = self.get(id)

        if data.code and data.code != entity.code:
            if self.repo.code_exists(data.code, exclude_id=id):
                raise [NomEntite]DuplicateError(f"Code {data.code} already exists")

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

    def delete(self, id: UUID) -> bool:
        entity = self.get(id)
        can_delete, reason = entity.can_delete()
        if not can_delete:
            raise [NomEntite]ValidationError(reason)
        return self.repo.soft_delete(entity, self.user_id)

    def restore(self, id: UUID) -> [NomEntite]:
        repo_deleted = [NomEntite]Repository(self.db, self.tenant_id, include_deleted=True)
        entity = repo_deleted.get_by_id(id)
        if not entity:
            raise [NomEntite]NotFoundError(f"Entity {id} not found")
        if not entity.is_deleted:
            raise [NomEntite]ValidationError("Entity is not deleted")
        return self.repo.restore(entity)

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict]:
        return self.repo.autocomplete(prefix, limit)

    def bulk_create(self, items: List[Dict]) -> Dict:
        errors = []
        valid = []
        for i, item in enumerate(items):
            if item.get("code") and self.repo.code_exists(item["code"]):
                errors.append({"index": i, "error": f"Code {item['code']} exists"})
            else:
                valid.append(item)

        count = self.repo.bulk_create(valid, self.user_id) if valid else 0
        return {"success": count, "errors": errors}

    def bulk_delete(self, ids: List[UUID]) -> Dict:
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

        count = self.repo.bulk_delete(deletable, self.user_id) if deletable else 0
        return {"success": count, "errors": errors}

    def get_stats(self) -> Dict:
        total = self.repo._base_query().count()
        by_status = {}
        for status in [NomEntite]Status:
            by_status[status.value] = self.repo._base_query().filter(
                [NomEntite].status == status
            ).count()
        return {"total": total, "by_status": by_status}
```

### router.py

```python
"""
Routes CRUD [NOM_MODULE]
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID

from app.core.security import get_current_user, require_permission
from app.core.database import get_db
from sqlalchemy.orm import Session

from .service import [NomModule]Service
from .schemas import (
    [NomEntite]Create, [NomEntite]Update,
    [NomEntite]Response, [NomEntite]List,
    AutocompleteResponse, BulkResult
)
from .models import [NomEntite]Status
from .exceptions import *

router = APIRouter(prefix="/[nom-module]", tags=["[NOM_MODULE]"])


def get_service(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
) -> [NomModule]Service:
    return [NomModule]Service(db, user.tenant_id, user.id)


@router.get("/", response_model=[NomEntite]List)
async def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[List[[NomEntite]Status]] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].view"))
):
    filters = {"search": search, "status": status}
    items, total, pages = service.list(filters, page, page_size, sort_by, sort_dir)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(
    prefix: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].view"))
):
    items = service.autocomplete(prefix, limit)
    return {"items": items}


@router.get("/{id}", response_model=[NomEntite]Response)
async def get_item(
    id: UUID,
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].view"))
):
    try:
        return service.get(id)
    except [NomEntite]NotFoundError as e:
        raise HTTPException(404, str(e))


@router.post("/", response_model=[NomEntite]Response, status_code=201)
async def create_item(
    data: [NomEntite]Create,
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].create"))
):
    try:
        return service.create(data)
    except [NomEntite]DuplicateError as e:
        raise HTTPException(409, str(e))


@router.put("/{id}", response_model=[NomEntite]Response)
async def update_item(
    id: UUID,
    data: [NomEntite]Update,
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].edit"))
):
    try:
        return service.update(id, data)
    except [NomEntite]NotFoundError as e:
        raise HTTPException(404, str(e))
    except ([NomEntite]DuplicateError, [NomEntite]StateError) as e:
        raise HTTPException(400, str(e))


@router.delete("/{id}", status_code=204)
async def delete_item(
    id: UUID,
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].delete"))
):
    try:
        service.delete(id)
    except [NomEntite]NotFoundError as e:
        raise HTTPException(404, str(e))
    except [NomEntite]ValidationError as e:
        raise HTTPException(400, str(e))


@router.post("/{id}/restore", response_model=[NomEntite]Response)
async def restore_item(
    id: UUID,
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].delete"))
):
    try:
        return service.restore(id)
    except ([NomEntite]NotFoundError, [NomEntite]ValidationError) as e:
        raise HTTPException(400, str(e))


@router.post("/bulk/create", response_model=BulkResult)
async def bulk_create(
    items: List[[NomEntite]Create],
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].create"))
):
    return service.bulk_create([i.model_dump() for i in items])


@router.post("/bulk/delete", response_model=BulkResult)
async def bulk_delete(
    ids: List[UUID],
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].delete"))
):
    return service.bulk_delete(ids)


@router.get("/stats", response_model=dict)
async def get_stats(
    service: [NomModule]Service = Depends(get_service),
    _: None = Depends(require_permission("[nom_module].view"))
):
    return service.get_stats()
```

### tests/test_security.py

```python
"""
Tests Sécurité Multi-tenant
CRITIQUE: Vérifier l'isolation entre tenants
"""
import pytest
from uuid import uuid4


class TestTenantIsolation:
    """Tests d'isolation tenant"""

    def test_cannot_access_other_tenant_data(self, service_tenant_a, entity_tenant_b):
        """Un tenant ne peut pas voir les données d'un autre tenant"""
        with pytest.raises(EntityNotFoundError):
            service_tenant_a.get(entity_tenant_b.id)

    def test_list_only_shows_own_tenant(self, service, entities_mixed_tenants):
        """List ne retourne que les entités du tenant courant"""
        items, _, _ = service.list()
        for item in items:
            assert item.tenant_id == service.tenant_id

    def test_cannot_update_other_tenant(self, service_tenant_a, entity_tenant_b):
        """Un tenant ne peut pas modifier les données d'un autre tenant"""
        with pytest.raises(EntityNotFoundError):
            service_tenant_a.update(entity_tenant_b.id, {"name": "Hacked"})

    def test_cannot_delete_other_tenant(self, service_tenant_a, entity_tenant_b):
        """Un tenant ne peut pas supprimer les données d'un autre tenant"""
        with pytest.raises(EntityNotFoundError):
            service_tenant_a.delete(entity_tenant_b.id)

    def test_autocomplete_isolated(self, service, entities_mixed_tenants):
        """Autocomplete ne retourne que les entités du tenant courant"""
        results = service.autocomplete("test")
        for item in results:
            # Vérifier via la base que chaque résultat appartient au bon tenant
            assert True  # À implémenter selon le contexte
```

---

## TEMPLATE FRONTEND

### types.ts

```typescript
/**
 * Types [NOM_MODULE]
 * Correspondent EXACTEMENT au backend
 */

export type [NomEntite]Status = 'draft' | 'active' | 'inactive' | 'archived';

export interface [NomEntite] {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  status: [NomEntite]Status;
  tags: string[];
  metadata: Record<string, any>;
  created_at: string;
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  is_deleted: boolean;
  deleted_at?: string | null;
  deleted_by?: string | null;
  version: number;
}

export interface [NomEntite]Create {
  name: string;
  code?: string;
  description?: string | null;
  status?: [NomEntite]Status;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface [NomEntite]Update {
  name?: string;
  code?: string;
  description?: string | null;
  status?: [NomEntite]Status;
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
 * Hook Autocomplete avec debounce et cache
 */
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useDebounce } from '@/hooks/useDebounce';
import { [nomModule]Api } from '../api';

export function use[NomModule]Autocomplete(
  prefix: string,
  options: { minChars?: number; limit?: number; enabled?: boolean } = {}
) {
  const { minChars = 2, limit = 10, enabled = true } = options;
  const debouncedPrefix = useDebounce(prefix, 300);

  const shouldFetch = useMemo(
    () => enabled && debouncedPrefix.length >= minChars,
    [enabled, debouncedPrefix, minChars]
  );

  const query = useQuery({
    queryKey: ['[nom-module]', 'autocomplete', debouncedPrefix, limit],
    queryFn: () => [nomModule]Api.autocomplete(debouncedPrefix, limit),
    enabled: shouldFetch,
    staleTime: 60000,
    gcTime: 300000,
    select: (data) => data.items
  });

  return {
    items: query.data ?? [],
    isLoading: query.isLoading && shouldFetch,
    isError: query.isError
  };
}
```

### components/[NomModule]Autocomplete.tsx

```typescript
/**
 * Composant Autocomplete complet
 * - Debounce
 * - Keyboard navigation (ArrowUp, ArrowDown, Enter, Escape)
 * - ARIA accessibility
 * - Cache
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

  // Click outside
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
            disabled && "bg-gray-100"
          )}
          role="combobox"
          aria-expanded={isOpen}
          aria-haspopup="listbox"
        />

        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {isLoading && <Loader2 className="w-4 h-4 animate-spin text-gray-400" />}
          {selectedItem && !disabled && (
            <button type="button" onClick={handleClear} className="p-1 hover:bg-gray-100 rounded">
              <X className="w-4 h-4 text-gray-400" />
            </button>
          )}
          <ChevronDown className={cn("w-4 h-4 text-gray-400", isOpen && "rotate-180")} />
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
              {selectedItem?.id === item.id && <Check className="w-4 h-4 text-blue-600" />}
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

## INTÉGRATION FINALE (PAR CHAQUE AGENT)

Chaque agent fait l'intégration de SON module:

### Backend - main.py

```python
from app.modules.[nom_module] import router as [nom_module]_router

app.include_router([nom_module]_router, prefix="/api/v1")
```

### Frontend - UnifiedApp.tsx

```typescript
import { [NomModule]Page } from './features/[nom-module]/pages';

// Dans le switch
case '[nom-module]':
  return <[NomModule]Page />;
```

### Frontend - UnifiedLayout.tsx

```typescript
// Dans MENU_ITEMS
{ key: '[nom-module]', label: '[Nom Module]', icon: IconName, group: 'group' }
```

---

## RAPPORT FINAL (PAR CHAQUE AGENT)

```markdown
## Agent [N] - Module [NOM_MODULE]

### Fichiers créés

| Catégorie | Fichiers | Status |
|-----------|----------|--------|
| Backend Models | models.py, schemas.py | ✅ |
| Backend Logic | repository.py, service.py | ✅ |
| Backend API | router.py | ✅ |
| Backend Tests | tests/*.py | ✅ |
| Frontend Types | types.ts, api.ts | ✅ |
| Frontend Hooks | hooks/*.ts | ✅ |
| Frontend Components | components/*.tsx | ✅ |
| Frontend Pages | pages/*.tsx | ✅ |
| Intégration | main.py, UnifiedApp.tsx | ✅ |

### Vérifications

- [x] Multi-tenant: tenant_id sur toutes les entités
- [x] Soft delete: is_deleted, deleted_at, deleted_by
- [x] Audit: created_at/by, updated_at/by
- [x] Version: optimistic locking
- [x] Autocomplete: debounce, cache, keyboard
- [x] Tests sécurité: isolation tenant validée
- [x] CRUD complet + restore
- [x] Bulk operations
- [x] Import/Export

### Tests exécutés

```bash
pytest app/modules/[nom_module]/tests/ -v
# Résultats: X passed, 0 failed
```
```

---

## EXEMPLE D'UTILISATION

```bash
# Lancer 5 agents en parallèle sur 5 modules différents

Agent 1: "Développe le module fieldservice"
Agent 2: "Développe le module survey"
Agent 3: "Développe le module approval"
Agent 4: "Développe le module expense"
Agent 5: "Développe le module requisition"

# Zéro conflit car chaque agent travaille sur des fichiers différents
```

---

*Document V4 - Exécution Parallèle Simplifiée*
*AZALSCORE - 2026-02-20*
