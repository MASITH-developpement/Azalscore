# PROMPTS DE DÉVELOPPEMENT MODULES AZALSCORE

**Date:** 2026-02-20
**Version:** 1.0
**Objectif:** Rendre chaque module 100% fonctionnel, production-ready

---

## RÈGLES FONDAMENTALES (NON NÉGOCIABLES)

```
┌─────────────────────────────────────────────────────────────────┐
│  1. VÉRITÉ ABSOLUE                                              │
│     - Pas de mensonge, jamais                                   │
│     - Pas de bullshit ni de promesses non tenables              │
│     - Préférer une mauvaise note à une note truquée             │
│     - Si quelque chose ne fonctionne pas, le dire clairement    │
│                                                                 │
│  2. CORRECTION IMMÉDIATE                                        │
│     - Pas de report de correction                               │
│     - Corriger maintenant, pas plus tard                        │
│     - Approfondir les recherches avant de coder                 │
│     - Tester chaque modification                                │
│                                                                 │
│  3. RÉFÉRENCE TECHNIQUE                                         │
│     - Code sera vérifié par experts et ingénieurs               │
│     - Doit être parfait, pas "acceptable"                       │
│     - Pas de suppositions ni d'inventions                       │
│     - Que des faits et améliorations prouvées                   │
│                                                                 │
│  4. SÉCURITÉ & MULTI-TENANT                                     │
│     - JAMAIS réduire la sécurité existante                      │
│     - JAMAIS compromettre l'isolation multi-tenant              │
│     - Améliorer uniquement, jamais dégrader                     │
│     - Chaque entité DOIT avoir tenant_id                        │
│                                                                 │
│  5. NE PAS CASSER L'EXISTANT                                    │
│     - Vérifier les dépendances avant modification               │
│     - Tests de non-régression obligatoires                      │
│     - Backup mental du code avant modification                  │
└─────────────────────────────────────────────────────────────────┘
```

---

# PROMPT 1: DÉVELOPPEMENT BACKEND MODULE COMPLET

## À copier et utiliser pour chaque module backend

```markdown
# MISSION: Développement Backend Module [NOM_MODULE]

## CONTEXTE

Tu travailles sur AZALSCORE, un ERP SaaS multi-tenant de référence technique.
Le code sera audité par des experts et ingénieurs. Il doit être PARFAIT.

**Module à développer:** [NOM_MODULE]
**Chemin:** /home/ubuntu/azalscore/app/modules/[nom_module]/
**Référence architecture:** /home/ubuntu/azalscore/memoire.md

## RÈGLES ABSOLUES

1. **VÉRITÉ** - Pas de mensonge. Si tu ne sais pas, dis-le. Si ça ne marche pas, dis-le.
2. **IMMÉDIAT** - Corrige MAINTENANT chaque erreur trouvée. Pas de "je ferai plus tard".
3. **PERFECTION** - Code de référence technique. Pas de raccourcis.
4. **SÉCURITÉ** - Ne JAMAIS réduire la sécurité. Améliorer uniquement.
5. **MULTI-TENANT** - tenant_id OBLIGATOIRE sur chaque entité. Isolation totale.
6. **TESTS** - Teste chaque modification. Pas de code non vérifié.

## ÉTAPES OBLIGATOIRES

### PHASE 1: ANALYSE (Ne pas sauter)

1. **Lire le code existant du module**
   ```bash
   # Lire service.py existant
   cat /home/ubuntu/azalscore/app/modules/[nom_module]/service.py

   # Lire __init__.py existant
   cat /home/ubuntu/azalscore/app/modules/[nom_module]/__init__.py

   # Lister tous les fichiers du module
   ls -la /home/ubuntu/azalscore/app/modules/[nom_module]/
   ```

2. **Identifier ce qui existe déjà**
   - Quels fichiers existent?
   - Quelles fonctionnalités sont implémentées?
   - Quelles fonctionnalités manquent?
   - Y a-t-il des erreurs dans le code existant?

3. **Vérifier les dépendances**
   ```bash
   # Qui importe ce module?
   grep -r "from.*[nom_module]" /home/ubuntu/azalscore/app/ --include="*.py"

   # Quels modules ce module importe?
   grep -r "^from\|^import" /home/ubuntu/azalscore/app/modules/[nom_module]/
   ```

4. **Documenter l'état actuel** (être HONNÊTE)
   - Ce qui fonctionne: [LISTE]
   - Ce qui ne fonctionne pas: [LISTE]
   - Ce qui manque: [LISTE]
   - Erreurs trouvées: [LISTE]

### PHASE 2: ARCHITECTURE BACKEND

Structure OBLIGATOIRE du module:

```
/app/modules/[nom_module]/
├── __init__.py          # Exports publics
├── service.py           # Logique métier (classe Service)
├── models.py            # Modèles SQLAlchemy (si DB)
├── schemas.py           # Schémas Pydantic (validation)
├── router.py            # Routes FastAPI
├── dependencies.py      # Dépendances injection
├── exceptions.py        # Exceptions métier
├── constants.py         # Constantes (optionnel)
└── tests/
    ├── __init__.py
    ├── test_service.py
    ├── test_router.py
    └── conftest.py
```

### PHASE 3: IMPLÉMENTATION

#### 3.1 Models (models.py)

```python
"""
Modèles SQLAlchemy pour [NOM_MODULE]
Multi-tenant: Chaque modèle DOIT avoir tenant_id
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class [NomEntite](Base):
    __tablename__ = "[nom_entites]"

    # Identifiants - TOUJOURS UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # MULTI-TENANT OBLIGATOIRE
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Champs métier
    # ...

    # Audit - TOUJOURS présent
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Index composite OBLIGATOIRE pour multi-tenant
    __table_args__ = (
        Index('ix_[nom_entites]_tenant_id', 'tenant_id'),
        Index('ix_[nom_entites]_tenant_[champ]', 'tenant_id', '[champ]'),
    )
```

#### 3.2 Schemas (schemas.py)

```python
"""
Schémas Pydantic pour validation [NOM_MODULE]
Validation stricte, pas de données invalides
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class [NomEntite]Status(str, Enum):
    """Énumération typée"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class [NomEntite]Base(BaseModel):
    """Schéma de base - champs communs"""
    # Champs avec validation
    name: str = Field(..., min_length=1, max_length=255)

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Le nom ne peut pas être vide')
        return v.strip()


class [NomEntite]Create([NomEntite]Base):
    """Schéma création - pas d'ID"""
    pass


class [NomEntite]Update(BaseModel):
    """Schéma mise à jour - tous champs optionnels"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class [NomEntite]Response([NomEntite]Base):
    """Schéma réponse - inclut ID et audit"""
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class [NomEntite]List(BaseModel):
    """Schéma liste paginée"""
    items: List[[NomEntite]Response]
    total: int
    page: int
    page_size: int
    pages: int
```

#### 3.3 Service (service.py)

```python
"""
Service [NOM_MODULE] - Logique métier
RÈGLE: Toute requête DOIT filtrer par tenant_id
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import [NomEntite]
from .schemas import [NomEntite]Create, [NomEntite]Update
from .exceptions import [NomEntite]NotFoundError, [NomEntite]ValidationError


class [NomModule]Service:
    """
    Service de gestion [NOM_MODULE]

    SÉCURITÉ:
    - Toutes les méthodes reçoivent tenant_id
    - Toutes les requêtes filtrent par tenant_id
    - Jamais d'accès cross-tenant
    """

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant OBLIGATOIRE"""
        return self.db.query([NomEntite]).filter(
            [NomEntite].tenant_id == self.tenant_id
        )

    def get(self, id: UUID) -> Optional[[NomEntite]]:
        """
        Récupérer une entité par ID
        SÉCURITÉ: Filtre par tenant_id
        """
        return self._base_query().filter([NomEntite].id == id).first()

    def get_or_404(self, id: UUID) -> [NomEntite]:
        """Récupérer ou lever exception"""
        entity = self.get(id)
        if not entity:
            raise [NomEntite]NotFoundError(f"[NomEntite] {id} non trouvé")
        return entity

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> tuple[List[[NomEntite]], int]:
        """
        Lister avec pagination
        Retourne (items, total)
        """
        query = self._base_query()

        # Appliquer filtres
        for key, value in filters.items():
            if value is not None and hasattr([NomEntite], key):
                query = query.filter(getattr([NomEntite], key) == value)

        total = query.count()
        items = query.offset(skip).limit(limit).all()

        return items, total

    def create(
        self,
        data: [NomEntite]Create,
        created_by: Optional[UUID] = None
    ) -> [NomEntite]:
        """
        Créer une entité
        SÉCURITÉ: tenant_id injecté automatiquement
        """
        entity = [NomEntite](
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data.model_dump()
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(
        self,
        id: UUID,
        data: [NomEntite]Update,
        updated_by: Optional[UUID] = None
    ) -> [NomEntite]:
        """
        Mettre à jour une entité
        SÉCURITÉ: Vérifie que l'entité appartient au tenant
        """
        entity = self.get_or_404(id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(entity, key, value)

        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, id: UUID) -> bool:
        """
        Supprimer une entité
        SÉCURITÉ: Vérifie que l'entité appartient au tenant
        """
        entity = self.get_or_404(id)
        self.db.delete(entity)
        self.db.commit()
        return True
```

#### 3.4 Router (router.py)

```python
"""
Routes API [NOM_MODULE]
SÉCURITÉ: Authentification et autorisation sur chaque route
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    [NomEntite]List
)
from .exceptions import [NomEntite]NotFoundError


router = APIRouter(
    prefix="/[nom-module]",
    tags=["[NOM_MODULE]"]
)


def get_service(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> [NomModule]Service:
    """Injection du service avec tenant_id de l'utilisateur"""
    return [NomModule]Service(db, current_user.tenant_id)


@router.get(
    "/",
    response_model=[NomEntite]List,
    summary="Lister les [entités]",
    dependencies=[Depends(require_permission("[nom_module].view"))]
)
async def list_[entites](
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: [NomModule]Service = Depends(get_service)
):
    """
    Liste paginée des [entités]

    - **page**: Numéro de page (défaut: 1)
    - **page_size**: Taille de page (défaut: 20, max: 100)
    """
    skip = (page - 1) * page_size
    items, total = service.list(skip=skip, limit=page_size)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.get(
    "/{id}",
    response_model=[NomEntite]Response,
    summary="Obtenir une [entité]",
    dependencies=[Depends(require_permission("[nom_module].view"))]
)
async def get_[entite](
    id: UUID,
    service: [NomModule]Service = Depends(get_service)
):
    """Récupérer une [entité] par son ID"""
    try:
        return service.get_or_404(id)
    except [NomEntite]NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/",
    response_model=[NomEntite]Response,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une [entité]",
    dependencies=[Depends(require_permission("[nom_module].create"))]
)
async def create_[entite](
    data: [NomEntite]Create,
    service: [NomModule]Service = Depends(get_service),
    current_user = Depends(get_current_user)
):
    """Créer une nouvelle [entité]"""
    return service.create(data, created_by=current_user.id)


@router.put(
    "/{id}",
    response_model=[NomEntite]Response,
    summary="Modifier une [entité]",
    dependencies=[Depends(require_permission("[nom_module].edit"))]
)
async def update_[entite](
    id: UUID,
    data: [NomEntite]Update,
    service: [NomModule]Service = Depends(get_service),
    current_user = Depends(get_current_user)
):
    """Mettre à jour une [entité]"""
    try:
        return service.update(id, data, updated_by=current_user.id)
    except [NomEntite]NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une [entité]",
    dependencies=[Depends(require_permission("[nom_module].delete"))]
)
async def delete_[entite](
    id: UUID,
    service: [NomModule]Service = Depends(get_service)
):
    """Supprimer une [entité]"""
    try:
        service.delete(id)
    except [NomEntite]NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

#### 3.5 Exceptions (exceptions.py)

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


class [NomEntite]ValidationError([NomModule]Error):
    """Erreur de validation"""
    pass


class [NomEntite]PermissionError([NomModule]Error):
    """Erreur de permission"""
    pass
```

#### 3.6 Tests (tests/test_service.py)

```python
"""
Tests unitaires service [NOM_MODULE]
OBLIGATOIRE: Tester isolation multi-tenant
"""
import pytest
from uuid import uuid4
from unittest.mock import Mock, MagicMock

from ..service import [NomModule]Service
from ..schemas import [NomEntite]Create, [NomEntite]Update
from ..exceptions import [NomEntite]NotFoundError


class Test[NomModule]Service:
    """Tests du service [NOM_MODULE]"""

    @pytest.fixture
    def tenant_id(self):
        return uuid4()

    @pytest.fixture
    def other_tenant_id(self):
        return uuid4()

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db, tenant_id):
        return [NomModule]Service(mock_db, tenant_id)

    def test_create_sets_tenant_id(self, service, tenant_id):
        """Vérifier que create injecte le tenant_id"""
        data = [NomEntite]Create(name="Test")
        # ... test implementation

    def test_list_filters_by_tenant(self, service, tenant_id):
        """Vérifier que list filtre par tenant_id"""
        # ... test implementation

    def test_cannot_access_other_tenant_data(self, service, other_tenant_id):
        """SÉCURITÉ: Impossible d'accéder aux données d'un autre tenant"""
        # ... test implementation
```

### PHASE 4: INTÉGRATION

1. **Enregistrer le router dans main.py**
   ```python
   from app.modules.[nom_module].router import router as [nom_module]_router
   app.include_router([nom_module]_router, prefix="/api/v1")
   ```

2. **Enregistrer dans modules_registry.py**
   ```python
   MODULES = {
       # ...
       "[nom_module]": {
           "name": "[Nom Module]",
           "description": "Description du module",
           "icon": "icon-name",
           "group": "group_name"
       }
   }
   ```

3. **Créer migration Alembic** (si nouveaux modèles)
   ```bash
   alembic revision --autogenerate -m "Add [nom_module] tables"
   alembic upgrade head
   ```

### PHASE 5: VÉRIFICATION FINALE

Checklist OBLIGATOIRE avant de considérer le module terminé:

- [ ] **Code**
  - [ ] Tous les fichiers créés/modifiés
  - [ ] Type hints sur toutes les fonctions
  - [ ] Docstrings sur classes et méthodes publiques
  - [ ] Pas de code dupliqué
  - [ ] Gestion des exceptions

- [ ] **Multi-tenant**
  - [ ] tenant_id sur tous les modèles
  - [ ] Index incluant tenant_id
  - [ ] Filtre tenant_id sur toutes les requêtes
  - [ ] Test d'isolation cross-tenant

- [ ] **Sécurité**
  - [ ] Authentification sur toutes les routes
  - [ ] Permissions vérifiées
  - [ ] Validation des entrées (Pydantic)
  - [ ] Pas d'injection possible
  - [ ] Audit des actions

- [ ] **Tests**
  - [ ] Tests unitaires service
  - [ ] Tests API router
  - [ ] Tests d'isolation tenant
  - [ ] Tous les tests passent

- [ ] **Intégration**
  - [ ] Router enregistré
  - [ ] Module dans registry
  - [ ] Migration créée et appliquée
  - [ ] Documentation OpenAPI générée

## RAPPORT FINAL

À la fin du développement, fournir:

```markdown
## Rapport Module [NOM_MODULE]

### État
- [ ] Complet et fonctionnel
- [ ] Partiel (préciser ce qui manque)
- [ ] Non fonctionnel (préciser les problèmes)

### Fichiers créés/modifiés
| Fichier | Action | Lignes |
|---------|--------|--------|
| ... | ... | ... |

### Fonctionnalités implémentées
- [x] Liste des fonctionnalités
- [ ] Fonctionnalités manquantes

### Tests
- Passés: X/Y
- Échoués: Z (détailler)

### Problèmes connus
- (Être HONNÊTE, lister TOUS les problèmes)

### Recommandations
- (Améliorations futures si nécessaire)
```
```

---

# PROMPT 2: INTÉGRATION FRONTEND & CONNEXION COMPLÈTE

## À copier et utiliser pour connecter chaque module au frontend

```markdown
# MISSION: Intégration Frontend Module [NOM_MODULE]

## CONTEXTE

Tu connectes le module backend [NOM_MODULE] au frontend React d'AZALSCORE.
L'objectif: Module 100% fonctionnel, utilisable en production.

**Module:** [NOM_MODULE]
**Backend:** /home/ubuntu/azalscore/app/modules/[nom_module]/
**Frontend:** /home/ubuntu/azalscore/frontend/src/

## RÈGLES ABSOLUES

1. **VÉRITÉ** - Si l'API ne fonctionne pas, le dire. Pas de fake.
2. **CONNEXION RÉELLE** - Appels API réels, pas de données mockées en production.
3. **UX PARFAITE** - Loading states, erreurs, succès, tout doit être géré.
4. **RESPONSIVE** - Fonctionne sur desktop, tablet, mobile.
5. **ACCESSIBILITÉ** - ARIA labels, navigation clavier, contraste.

## ÉTAPES OBLIGATOIRES

### PHASE 1: VÉRIFICATION BACKEND

Avant de coder le frontend, VÉRIFIER que le backend fonctionne:

```bash
# 1. Vérifier que le serveur tourne
curl http://localhost:8000/health

# 2. Obtenir un token (remplacer credentials)
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"password"}' \
  | jq -r '.access_token')

# 3. Tester l'endpoint du module
curl http://localhost:8000/api/v1/[nom-module]/ \
  -H "Authorization: Bearer $TOKEN"

# 4. Documenter le résultat HONNÊTEMENT
# - API fonctionne: OUI/NON
# - Réponse reçue: [STRUCTURE]
# - Erreurs: [LISTE]
```

**SI LE BACKEND NE FONCTIONNE PAS:**
- STOP - Ne pas continuer
- Documenter les erreurs
- Corriger le backend d'abord
- Revenir à ce prompt ensuite

### PHASE 2: STRUCTURE FRONTEND

```
/frontend/src/
├── features/[nom-module]/
│   ├── index.ts                 # Exports
│   ├── api.ts                   # Appels API
│   ├── types.ts                 # Types TypeScript
│   ├── hooks/
│   │   ├── use[NomModule].ts    # Hook principal
│   │   └── use[NomModule]Mutations.ts
│   ├── components/
│   │   ├── [NomModule]List.tsx
│   │   ├── [NomModule]Form.tsx
│   │   ├── [NomModule]Detail.tsx
│   │   └── [NomModule]Card.tsx
│   └── pages/
│       ├── [NomModule]Page.tsx
│       └── [NomModule]DetailPage.tsx
```

### PHASE 3: IMPLÉMENTATION

#### 3.1 Types (types.ts)

```typescript
/**
 * Types TypeScript pour [NOM_MODULE]
 * DOIT correspondre exactement aux schemas Pydantic backend
 */

export interface [NomEntite] {
  id: string;
  tenant_id: string;
  // Champs métier - CORRESPONDRE AU BACKEND
  name: string;
  // ...
  created_at: string;
  updated_at: string | null;
}

export interface [NomEntite]Create {
  name: string;
  // Champs requis pour création
}

export interface [NomEntite]Update {
  name?: string;
  // Champs optionnels pour mise à jour
}

export interface [NomEntite]ListResponse {
  items: [NomEntite][];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface [NomEntite]Filters {
  page?: number;
  page_size?: number;
  // Filtres spécifiques
}
```

#### 3.2 API (api.ts)

```typescript
/**
 * Appels API [NOM_MODULE]
 * Utilise le client API configuré avec interceptors
 */
import { apiClient } from '@/lib/api-client';
import type {
  [NomEntite],
  [NomEntite]Create,
  [NomEntite]Update,
  [NomEntite]ListResponse,
  [NomEntite]Filters
} from './types';

const BASE_URL = '/api/v1/[nom-module]';

export const [nomModule]Api = {
  /**
   * Liste paginée
   */
  list: async (filters?: [NomEntite]Filters): Promise<[NomEntite]ListResponse> => {
    const params = new URLSearchParams();
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.page_size) params.set('page_size', String(filters.page_size));

    const response = await apiClient.get(`${BASE_URL}/?${params}`);
    return response.data;
  },

  /**
   * Obtenir par ID
   */
  get: async (id: string): Promise<[NomEntite]> => {
    const response = await apiClient.get(`${BASE_URL}/${id}`);
    return response.data;
  },

  /**
   * Créer
   */
  create: async (data: [NomEntite]Create): Promise<[NomEntite]> => {
    const response = await apiClient.post(BASE_URL, data);
    return response.data;
  },

  /**
   * Mettre à jour
   */
  update: async (id: string, data: [NomEntite]Update): Promise<[NomEntite]> => {
    const response = await apiClient.put(`${BASE_URL}/${id}`, data);
    return response.data;
  },

  /**
   * Supprimer
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/${id}`);
  }
};
```

#### 3.3 Hooks (hooks/use[NomModule].ts)

```typescript
/**
 * Hook React Query pour [NOM_MODULE]
 * Gère cache, loading, erreurs automatiquement
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { [nomModule]Api } from '../api';
import type { [NomEntite]Filters, [NomEntite]Create, [NomEntite]Update } from '../types';
import { toast } from '@/components/ui/toast';

const QUERY_KEY = '[nom-module]';

export function use[NomModule]List(filters?: [NomEntite]Filters) {
  return useQuery({
    queryKey: [QUERY_KEY, 'list', filters],
    queryFn: () => [nomModule]Api.list(filters),
    staleTime: 30000, // 30 secondes
  });
}

export function use[NomModule](id: string) {
  return useQuery({
    queryKey: [QUERY_KEY, 'detail', id],
    queryFn: () => [nomModule]Api.get(id),
    enabled: !!id,
  });
}

export function use[NomModule]Mutations() {
  const queryClient = useQueryClient();

  const create = useMutation({
    mutationFn: (data: [NomEntite]Create) => [nomModule]Api.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      toast.success('[Entité] créée avec succès');
    },
    onError: (error: Error) => {
      toast.error(`Erreur: ${error.message}`);
    }
  });

  const update = useMutation({
    mutationFn: ({ id, data }: { id: string; data: [NomEntite]Update }) =>
      [nomModule]Api.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      toast.success('[Entité] mise à jour');
    },
    onError: (error: Error) => {
      toast.error(`Erreur: ${error.message}`);
    }
  });

  const remove = useMutation({
    mutationFn: (id: string) => [nomModule]Api.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      toast.success('[Entité] supprimée');
    },
    onError: (error: Error) => {
      toast.error(`Erreur: ${error.message}`);
    }
  });

  return { create, update, remove };
}
```

#### 3.4 Composants

```typescript
// components/[NomModule]List.tsx
/**
 * Liste des [entités] avec pagination
 * DOIT gérer: loading, erreur, vide, données
 */
import { use[NomModule]List } from '../hooks/use[NomModule]';
import { Loader, AlertCircle } from 'lucide-react';

interface Props {
  filters?: [NomEntite]Filters;
  onSelect?: (item: [NomEntite]) => void;
}

export function [NomModule]List({ filters, onSelect }: Props) {
  const { data, isLoading, isError, error } = use[NomModule]List(filters);

  // État: Chargement
  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader className="w-6 h-6 animate-spin" />
        <span className="ml-2">Chargement...</span>
      </div>
    );
  }

  // État: Erreur
  if (isError) {
    return (
      <div className="flex items-center justify-center p-8 text-red-600">
        <AlertCircle className="w-6 h-6" />
        <span className="ml-2">Erreur: {error?.message}</span>
      </div>
    );
  }

  // État: Vide
  if (!data?.items?.length) {
    return (
      <div className="text-center p-8 text-gray-500">
        Aucune donnée disponible
      </div>
    );
  }

  // État: Données
  return (
    <div className="space-y-4">
      {data.items.map((item) => (
        <div
          key={item.id}
          onClick={() => onSelect?.(item)}
          className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
        >
          <h3 className="font-medium">{item.name}</h3>
          {/* Autres champs */}
        </div>
      ))}

      {/* Pagination */}
      <div className="flex justify-between items-center pt-4">
        <span className="text-sm text-gray-500">
          {data.total} résultat(s)
        </span>
        <div className="flex gap-2">
          {/* Boutons pagination */}
        </div>
      </div>
    </div>
  );
}
```

#### 3.5 Page principale

```typescript
// pages/[NomModule]Page.tsx
/**
 * Page principale du module [NOM_MODULE]
 * Intègre liste, création, filtres
 */
import { useState } from 'react';
import { [NomModule]List } from '../components/[NomModule]List';
import { [NomModule]Form } from '../components/[NomModule]Form';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

export function [NomModule]Page() {
  const [showForm, setShowForm] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  return (
    <div className="container mx-auto py-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">[Nom Module]</h1>
        <Button onClick={() => setShowForm(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Nouveau
        </Button>
      </div>

      {/* Liste */}
      <[NomModule]List
        onSelect={(item) => setSelectedId(item.id)}
      />

      {/* Modal création/édition */}
      {showForm && (
        <[NomModule]Form
          id={selectedId}
          onClose={() => {
            setShowForm(false);
            setSelectedId(null);
          }}
        />
      )}
    </div>
  );
}
```

### PHASE 4: INTÉGRATION MENU

1. **Ajouter au UnifiedLayout.tsx**
   ```typescript
   // Dans MENU_ITEMS
   {
     key: '[nom-module]',
     label: '[Nom Module]',
     icon: IconName,
     group: 'group_name'
   }
   ```

2. **Ajouter la route dans UnifiedApp.tsx**
   ```typescript
   // Import
   import { [NomModule]Page } from './features/[nom-module]/pages/[NomModule]Page';

   // Route
   case '[nom-module]':
     return <[NomModule]Page />;
   ```

### PHASE 5: TESTS E2E

```typescript
// tests/e2e/[nom-module].spec.ts
import { test, expect } from '@playwright/test';

test.describe('[NOM_MODULE]', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'admin@test.com');
    await page.fill('[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('affiche la liste', async ({ page }) => {
    await page.goto('/[nom-module]');
    await expect(page.locator('h1')).toContainText('[Nom Module]');
  });

  test('peut créer une nouvelle entrée', async ({ page }) => {
    await page.goto('/[nom-module]');
    await page.click('button:has-text("Nouveau")');
    await page.fill('[name="name"]', 'Test Entry');
    await page.click('button:has-text("Enregistrer")');
    await expect(page.locator('.toast-success')).toBeVisible();
  });
});
```

### PHASE 6: VÉRIFICATION FINALE

- [ ] **Connexion API**
  - [ ] Liste fonctionne
  - [ ] Création fonctionne
  - [ ] Modification fonctionne
  - [ ] Suppression fonctionne
  - [ ] Erreurs gérées proprement

- [ ] **UI/UX**
  - [ ] Loading states présents
  - [ ] Messages d'erreur clairs
  - [ ] Messages de succès
  - [ ] Responsive (mobile, tablet, desktop)
  - [ ] Accessibilité (ARIA, keyboard)

- [ ] **Intégration**
  - [ ] Menu fonctionnel
  - [ ] Navigation fonctionne
  - [ ] Permissions respectées
  - [ ] Pas de régression autres modules

## RAPPORT FINAL

```markdown
## Rapport Intégration Frontend [NOM_MODULE]

### État connexion Backend-Frontend
- [ ] Entièrement connecté et fonctionnel
- [ ] Partiellement connecté (détailler)
- [ ] Non connecté (détailler les erreurs)

### Endpoints testés
| Endpoint | Méthode | Status | Notes |
|----------|---------|--------|-------|
| /[nom-module]/ | GET | ✅/❌ | |
| /[nom-module]/ | POST | ✅/❌ | |
| /[nom-module]/{id} | GET | ✅/❌ | |
| /[nom-module]/{id} | PUT | ✅/❌ | |
| /[nom-module]/{id} | DELETE | ✅/❌ | |

### Fonctionnalités UI
- [x] Liste avec pagination
- [x] Formulaire création
- [ ] ... (être honnête)

### Problèmes rencontrés
- (LISTER TOUS LES PROBLÈMES - pas de mensonge)

### Screenshots/Preuves
- (Inclure si possible)
```
```

---

# ANNEXE: CHECKLIST QUALITÉ GLOBALE

## Avant de déclarer un module "terminé"

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHECKLIST FINALE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BACKEND                                                        │
│  ├─ [ ] Models avec tenant_id et indexes                       │
│  ├─ [ ] Schemas Pydantic avec validation                       │
│  ├─ [ ] Service avec isolation tenant                          │
│  ├─ [ ] Router avec auth et permissions                        │
│  ├─ [ ] Exceptions métier                                      │
│  ├─ [ ] Tests unitaires passent                                │
│  └─ [ ] Migration DB appliquée                                 │
│                                                                 │
│  FRONTEND                                                       │
│  ├─ [ ] Types correspondant au backend                         │
│  ├─ [ ] API client avec gestion erreurs                        │
│  ├─ [ ] Hooks React Query                                      │
│  ├─ [ ] Composants avec tous les états                         │
│  ├─ [ ] Page intégrée au menu                                  │
│  └─ [ ] Tests E2E passent                                      │
│                                                                 │
│  SÉCURITÉ                                                       │
│  ├─ [ ] Authentification vérifiée                              │
│  ├─ [ ] Permissions vérifiées                                  │
│  ├─ [ ] Isolation tenant testée                                │
│  ├─ [ ] Validation entrées complète                            │
│  └─ [ ] Pas de failles OWASP                                   │
│                                                                 │
│  QUALITÉ                                                        │
│  ├─ [ ] Code typé (Python + TypeScript)                        │
│  ├─ [ ] Docstrings/commentaires                                │
│  ├─ [ ] Pas de code mort                                       │
│  ├─ [ ] Pas de console.log/print debug                         │
│  └─ [ ] Lint clean                                             │
│                                                                 │
│  DOCUMENTATION                                                  │
│  ├─ [ ] OpenAPI/Swagger à jour                                 │
│  ├─ [ ] README module si complexe                              │
│  └─ [ ] Changelog mis à jour                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Principe de vérité

**À CHAQUE ÉTAPE**, se poser ces questions:

1. Est-ce que ça fonctionne VRAIMENT ou je SUPPOSE que ça fonctionne?
2. Ai-je TESTÉ ou je fais confiance au code?
3. Si un expert regarde ce code, sera-t-il impressionné ou consterné?
4. Est-ce que je serais fier de montrer ce code?
5. Y a-t-il des raccourcis que j'ai pris par facilité?

**SI LA RÉPONSE N'EST PAS SATISFAISANTE → CORRIGER MAINTENANT**

---

*Document créé le 2026-02-20 pour AZALSCORE*
*Objectif: Code de référence technique, vérifié par experts*
