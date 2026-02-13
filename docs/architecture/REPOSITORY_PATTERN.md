# Pattern Repository - AZALSCORE

## Principe

Couche d'abstraction entre logique metier (services/routers) et acces donnees (SQLAlchemy).

```
Controller/Router (FastAPI)
         |
    Service Layer
         |
    Repository  <-- BaseRepository (tenant_id auto + QueryOptimizer)
         |
    SQLAlchemy ORM
         |
    PostgreSQL (RLS tenant_id)
```

## Avantages

| Avantage | Description |
|----------|-------------|
| **Testabilite** | Mock repository facile (pas besoin mock DB) |
| **Maintenabilite** | Queries centralisees (pas dispersees dans les routers) |
| **Securite** | tenant_id automatique (isolation garantie) |
| **Performance** | QueryOptimizer integre (evite N+1 queries) |
| **Coherence** | API uniforme pour tous les modeles |

## Fichiers

```
app/core/repository.py              # BaseRepository generique
app/modules/contacts/repository.py  # POC ContactRepository
```

## Usage

### Exemple basique

```python
from app.modules.contacts.repository import ContactRepository
from app.core.dependencies import get_saas_context
from sqlalchemy.orm import Session
from fastapi import Depends

@router.get("/contacts")
async def list_contacts(
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    repo = ContactRepository(db, ctx.tenant_id)

    # tenant_id automatique, pagination, QueryOptimizer
    contacts, total = repo.list_active(skip=0, limit=20)

    return {"items": contacts, "total": total}
```

### Avec eager loading (evite N+1)

```python
@router.get("/contacts/{contact_id}")
async def get_contact(
    contact_id: UUID,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    repo = ContactRepository(db, ctx.tenant_id)

    # Charge persons et addresses en 1 seule query
    contact = repo.get_with_details(contact_id)

    if not contact:
        raise HTTPException(404, "Contact not found")

    return contact
```

### Recherche metier

```python
@router.get("/contacts/search")
async def search_contacts(
    q: str,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    repo = ContactRepository(db, ctx.tenant_id)

    # Recherche floue par nom
    results = repo.search_by_name(q, limit=50)

    return results
```

### Creation avec tenant automatique

```python
@router.post("/contacts")
async def create_contact(
    data: ContactCreate,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    repo = ContactRepository(db, ctx.tenant_id)

    # tenant_id injecte automatiquement
    contact = UnifiedContact(**data.dict())
    contact = repo.create(contact)

    return contact
```

## API BaseRepository

| Methode | Description |
|---------|-------------|
| `get_by_id(id, relations?)` | Recupere par ID avec eager loading optionnel |
| `list_all(skip, limit, filters?, relations?, order_by?)` | Liste paginee avec filtres |
| `create(entity)` | Cree avec tenant_id automatique |
| `update(entity)` | Met a jour |
| `delete(id, soft=True)` | Supprime (soft delete par defaut) |
| `exists(id)` | Verifie existence |
| `count(filters?)` | Compte avec filtres |
| `bulk_create(entities)` | Creation en batch |

## Tests

### Mock repository (pas besoin DB)

```python
from unittest.mock import MagicMock

class MockContactRepository:
    def __init__(self, db, tenant_id):
        self.tenant_id = tenant_id
        self._contacts = []

    def list_active(self, skip=0, limit=100, relations=None):
        return self._contacts, len(self._contacts)

    def get_by_id(self, id, relations=None):
        return next((c for c in self._contacts if c.id == id), None)


def test_list_contacts():
    repo = MockContactRepository(None, "test-tenant")
    repo._contacts = [MagicMock(id=1, name="Contact A")]

    contacts, total = repo.list_active()

    assert total == 1
    assert contacts[0].name == "Contact A"
```

### Test integration

```python
def test_repository_tenant_isolation(db_session):
    """Verifie que le repository filtre par tenant"""
    repo_a = ContactRepository(db_session, "tenant-a")
    repo_b = ContactRepository(db_session, "tenant-b")

    # Creer contact tenant-a
    contact = UnifiedContact(name="Test", code="CONT-2024-0001")
    repo_a.create(contact)

    # tenant-b ne doit pas voir
    result = repo_b.get_by_id(contact.id)
    assert result is None
```

## Roadmap

- [x] **POC Contacts** : `app/modules/contacts/repository.py`
- [ ] Generaliser aux modules : subscriptions, audit, guardian
- [ ] Ajouter cache Redis via `@cached` sur methodes list_*
- [ ] Metriques performance par repository
- [ ] Logging structure des queries lentes

## Migration Progressive

**Ne PAS tout migrer d'un coup.** Strategie :

1. Utiliser BaseRepository pour **nouveaux endpoints uniquement**
2. Migrer endpoints existants **au fil de l'eau** (lors de refactoring)
3. Mesurer gains performance (QueryOptimizer + cache)
4. Documenter patterns specifiques par module

## Conformite

- **AZA-NF-002** : Architecture modulaire
- **AZA-NF-007** : Isolation tenant obligatoire
- **AZA-BE-001** : Queries optimisees (N+1 interdit)
