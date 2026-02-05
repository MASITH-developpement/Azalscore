# AZALSCORE - Guide des Routines Developpeur

Ce document decrit les routines reutilisables centralisees dans `app/core/routines.py`.
Ces routines eliminent la duplication de code et standardisent les operations communes.

---

## Table des Matieres

1. [require_entity](#1-require_entity)
2. [TenantRepository](#2-tenantrepository)
3. [CRUDMixin](#3-crudmixin)
4. [update_model](#4-update_model)
5. [handle_service_errors](#5-handle_service_errors)
6. [ServiceFactory](#6-servicefactory)
7. [paginate](#7-paginate)
8. [Validateurs](#8-validateurs)
9. [Exemples d'Integration](#9-exemples-dintegration)
10. [Bonnes Pratiques](#10-bonnes-pratiques)

---

## 1. require_entity

**But**: Verifier qu'une entite existe, sinon lever une HTTPException 404.

**Avant** (657 occurrences dans le code):
```python
incident = db.query(Incident).filter(Incident.id == incident_id).first()
if not incident:
    raise HTTPException(status_code=404, detail="Incident not found")
```

**Apres**:
```python
from app.core.routines import require_entity

incident = db.query(Incident).filter(Incident.id == incident_id).first()
incident = require_entity(incident, "Incident", incident_id)
```

**Signature**:
```python
def require_entity(
    entity: T | None,
    entity_name: str,
    entity_id: Any = None,
    status_code: int = 404
) -> T
```

**Parametres**:
| Parametre | Type | Description |
|-----------|------|-------------|
| entity | T \| None | L'entite a verifier |
| entity_name | str | Nom pour le message d'erreur |
| entity_id | Any | ID optionnel pour le message |
| status_code | int | Code HTTP (defaut: 404) |

---

## 2. TenantRepository

**But**: Encapsuler toutes les requetes filtrees par tenant_id.

**Avant** (1881 occurrences):
```python
def get_all_users(self, db: Session) -> list[User]:
    return db.query(User).filter(User.tenant_id == self.tenant_id).all()

def get_user(self, db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(
        User.tenant_id == self.tenant_id,
        User.id == user_id
    ).first()
```

**Apres**:
```python
from app.core.routines import TenantRepository

class UserRepository(TenantRepository[User]):
    model = User

# Usage
repo = UserRepository(db, tenant_id)
users = repo.all()
user = repo.get(user_id)
active_users = repo.filter(User.is_active == True)
```

**Methodes Disponibles**:
| Methode | Description |
|---------|-------------|
| `query()` | Retourne query filtree par tenant |
| `all()` | Retourne toutes les entites du tenant |
| `get(id)` | Retourne une entite par ID |
| `get_or_404(id, name)` | Retourne ou leve 404 |
| `filter(*conditions)` | Filtre avec conditions supplementaires |
| `exists(id)` | Verifie si l'entite existe |
| `count()` | Compte les entites |

---

## 3. CRUDMixin

**But**: Standardiser les operations Create/Read/Update/Delete.

**Avant** (1881+ occurrences):
```python
def create_user(self, db: Session, user: User) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user(self, db: Session, user: User) -> User:
    db.commit()
    db.refresh(user)
    return user

def delete_user(self, db: Session, user: User) -> bool:
    db.delete(user)
    db.commit()
    return True
```

**Apres**:
```python
from app.core.routines import CRUDMixin

class UserService(CRUDMixin):
    pass

# Usage
service = UserService(db)
user = service.create(new_user)
user = service.update(user)
service.delete(user)
```

**Methodes**:
| Methode | Description |
|---------|-------------|
| `create(entity)` | Add + commit + refresh |
| `update(entity)` | Commit + refresh |
| `delete(entity)` | Delete + commit |
| `bulk_create(entities)` | Creation en masse |

---

## 4. update_model

**But**: Mettre a jour dynamiquement les champs d'un modele depuis un schema Pydantic.

**Avant** (20+ occurrences):
```python
update_data = data.model_dump(exclude_unset=True)
for field, value in update_data.items():
    if field not in ["id", "tenant_id", "created_at"]:
        if hasattr(incident, field):
            if field == "assigned_to_id" and value:
                value = UUID(value) if isinstance(value, str) else value
            setattr(incident, field, value)
```

**Apres**:
```python
from app.core.routines import update_model

update_model(
    incident,
    data,
    exclude_fields=["id", "tenant_id", "created_at"],
    serializers={"assigned_to_id": lambda v: UUID(v) if isinstance(v, str) else v}
)
```

**Signature**:
```python
def update_model(
    model_instance: Any,
    update_data: BaseModel | dict,
    exclude_fields: list[str] | None = None,
    serializers: dict[str, Callable] | None = None
) -> Any
```

**Parametres**:
| Parametre | Type | Description |
|-----------|------|-------------|
| model_instance | Any | Instance SQLAlchemy a modifier |
| update_data | BaseModel \| dict | Donnees de mise a jour |
| exclude_fields | list[str] | Champs a ignorer |
| serializers | dict[str, Callable] | Transformations par champ |

---

## 5. handle_service_errors

**But**: Decorateur pour gerer les exceptions de service de maniere uniforme.

**Avant** (200+ occurrences):
```python
@router.post("/incidents")
def create_incident(...):
    try:
        return service.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
```

**Apres**:
```python
from app.core.routines import handle_service_errors

@router.post("/incidents")
@handle_service_errors({
    ValueError: 400,
    PermissionError: 403
})
def create_incident(...):
    return service.create(data)
```

**Signature**:
```python
def handle_service_errors(
    exception_map: dict[type, int] | None = None,
    default_status: int = 400,
    log_errors: bool = True
) -> Callable
```

**Map d'Exceptions par Defaut**:
```python
{
    ValueError: 400,
    PermissionError: 403,
    KeyError: 404,
    IntegrityError: 409
}
```

---

## 6. ServiceFactory

**But**: Injection standardisee des services dans les endpoints.

**Avant** (781 occurrences):
```python
@router.get("/incidents")
def get_incidents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = IncidentService(db, current_user.tenant_id)
    return service.get_all()
```

**Apres**:
```python
from app.core.routines import ServiceFactory

factory = ServiceFactory()

@router.get("/incidents")
def get_incidents(
    service: IncidentService = Depends(factory.get(IncidentService))
):
    return service.get_all()
```

**Methodes**:
| Methode | Description |
|---------|-------------|
| `get(ServiceClass)` | Retourne un Depends pour le service |
| `register(ServiceClass, factory_fn)` | Enregistre une factory custom |

---

## 7. paginate

**But**: Pagination standardisee des resultats.

**Avant**:
```python
skip = (page - 1) * page_size
items = query.offset(skip).limit(page_size).all()
total = query.count()
return {
    "items": items,
    "total": total,
    "page": page,
    "page_size": page_size,
    "pages": (total + page_size - 1) // page_size
}
```

**Apres**:
```python
from app.core.routines import paginate

result = paginate(query, page=1, page_size=25)
# Retourne: {"items": [...], "total": N, "page": 1, "page_size": 25, "pages": M}
```

**Signature**:
```python
def paginate(
    query: Query,
    page: int = 1,
    page_size: int = 25,
    max_page_size: int = 100
) -> dict
```

---

## 8. Validateurs

### validate_uuid

**But**: Valider et convertir une chaine en UUID.

```python
from app.core.routines import validate_uuid

uuid_obj = validate_uuid("550e8400-e29b-41d4-a716-446655440000", "incident_id")
# Leve ValueError si invalide
```

### validate_enum

**But**: Valider qu'une valeur appartient a un Enum.

```python
from app.core.routines import validate_enum

status = validate_enum("open", IncidentStatus, "status")
# Retourne IncidentStatus.open ou leve ValueError
```

---

## 9. Exemples d'Integration

### Exemple Complet: Service d'Incidents

```python
from app.core.routines import (
    TenantRepository, CRUDMixin, require_entity,
    update_model, handle_service_errors, paginate
)

class IncidentRepository(TenantRepository[Incident]):
    model = Incident

    def get_open(self) -> list[Incident]:
        return self.filter(Incident.status == "open")

class IncidentService(CRUDMixin):
    def __init__(self, db: Session, tenant_id: UUID):
        super().__init__(db)
        self.repo = IncidentRepository(db, tenant_id)

    def get_all(self, page: int = 1) -> dict:
        return paginate(self.repo.query(), page=page)

    def get_by_id(self, incident_id: UUID) -> Incident:
        incident = self.repo.get(incident_id)
        return require_entity(incident, "Incident", incident_id)

    def update_incident(self, incident_id: UUID, data: IncidentUpdate) -> Incident:
        incident = self.get_by_id(incident_id)
        update_model(incident, data, exclude_fields=["id", "tenant_id"])
        return self.update(incident)
```

### Exemple Complet: Endpoint API

```python
from app.core.routines import ServiceFactory, handle_service_errors

factory = ServiceFactory()

@router.get("/incidents")
@handle_service_errors()
def list_incidents(
    page: int = Query(1, ge=1),
    service: IncidentService = Depends(factory.get(IncidentService))
):
    return service.get_all(page=page)

@router.get("/incidents/{incident_id}")
@handle_service_errors()
def get_incident(
    incident_id: UUID,
    service: IncidentService = Depends(factory.get(IncidentService))
):
    return service.get_by_id(incident_id)

@router.patch("/incidents/{incident_id}")
@handle_service_errors()
def update_incident(
    incident_id: UUID,
    data: IncidentUpdate,
    service: IncidentService = Depends(factory.get(IncidentService))
):
    return service.update_incident(incident_id, data)
```

---

## 10. Bonnes Pratiques

### DO - A Faire

1. **Toujours utiliser `require_entity`** pour les verifications 404
2. **Heriter de `TenantRepository`** pour toutes les requetes multi-tenant
3. **Utiliser `CRUDMixin`** pour les operations de base de donnees
4. **Appliquer `@handle_service_errors`** sur tous les endpoints
5. **Utiliser `update_model`** avec `exclude_fields` pour proteger les champs sensibles

### DON'T - A Eviter

1. **Ne pas ecrire `if not entity: raise HTTPException(404)`** - utiliser `require_entity`
2. **Ne pas filtrer manuellement par tenant_id** - utiliser `TenantRepository`
3. **Ne pas dupliquer db.add/commit/refresh** - utiliser `CRUDMixin`
4. **Ne pas iterer sur model_dump() manuellement** - utiliser `update_model`
5. **Ne pas ecrire de try/except pour chaque endpoint** - utiliser `@handle_service_errors`

### Prevention des Boucles Infinies

**ATTENTION**: Ne jamais appeler une routine depuis elle-meme ou creer de dependances circulaires.

```python
# DANGEREUX - Boucle potentielle
class BadRepository(TenantRepository[User]):
    def get(self, id):
        return self.get(id)  # Appelle soi-meme!

# CORRECT
class GoodRepository(TenantRepository[User]):
    def get(self, id):
        return super().get(id)  # Appelle la methode parente
```

---

## Imports Recommandes

```python
# Import standard pour un service
from app.core.routines import (
    require_entity,
    TenantRepository,
    CRUDMixin,
    update_model,
    handle_service_errors,
    ServiceFactory,
    paginate,
    validate_uuid,
    validate_enum
)
```

---

## Migration Progressive

Pour migrer le code existant vers les routines:

1. **Phase 1**: Remplacer les patterns 404 par `require_entity`
2. **Phase 2**: Creer des Repositories heritant de `TenantRepository`
3. **Phase 3**: Faire heriter les Services de `CRUDMixin`
4. **Phase 4**: Appliquer `@handle_service_errors` aux endpoints
5. **Phase 5**: Utiliser `ServiceFactory` pour l'injection

**Important**: Tester chaque phase avant de passer a la suivante.

---

*Document genere le 2026-01-21 - AZALSCORE v0.3.0*
