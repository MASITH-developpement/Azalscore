# Migration CORE SaaS v2 - Module Broadcast

## Date de migration
2026-01-25

## Statut
✅ Migration complète

## Changements effectués

### 1. Service (service.py)

**Ligne 37-40**: Constructor mis à jour pour supporter user_id

```python
# Avant
def __init__(self, db: Session, tenant_id: str):
    self.db = db
    self.tenant_id = tenant_id

# Après
def __init__(self, db: Session, tenant_id: str, user_id: str = None):
    self.db = db
    self.tenant_id = tenant_id
    self.user_id = user_id
```

**Compatibilité**: Le paramètre `user_id` est optionnel, assurant la compatibilité avec v1.

### 2. Router v2 (router_v2.py)

**Nouveau fichier**: `router_v2.py` (570 lignes)

**Imports ajoutés**:
```python
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
```

**Factory pattern**:
```python
def get_broadcast_service(db: Session, tenant_id: str, user_id: str) -> BroadcastService:
    return BroadcastService(db, tenant_id, user_id)
```

**Configuration router**:
- Prefix: `/v2/broadcast`
- Tags: `["Broadcast v2 - CORE SaaS"]`
- 30 endpoints implémentés

### 3. Tests (tests/)

**Nouveaux fichiers**:
- `tests/__init__.py` (package marker)
- `tests/conftest.py` (359 lignes)
- `tests/test_router_v2.py` (775 lignes)

**Fixtures créées** (9):
- template_data
- recipient_list_data
- recipient_member_data
- broadcast_data
- execution_data
- delivery_detail_data
- preference_data
- metric_data
- dashboard_stats

**Mocks créés** (4):
- mock_broadcast_service
- mock_get_saas_context
- mock_get_broadcast_service
- client (TestClient)

**Tests implémentés**: 60 tests unitaires couvrant tous les endpoints

## Endpoints v2

### Templates (5)
- POST /v2/broadcast/templates
- GET /v2/broadcast/templates
- GET /v2/broadcast/templates/{template_id}
- PUT /v2/broadcast/templates/{template_id}
- DELETE /v2/broadcast/templates/{template_id}

### Recipient Lists (6)
- POST /v2/broadcast/recipient-lists
- GET /v2/broadcast/recipient-lists
- GET /v2/broadcast/recipient-lists/{list_id}
- POST /v2/broadcast/recipient-lists/{list_id}/members
- GET /v2/broadcast/recipient-lists/{list_id}/members
- DELETE /v2/broadcast/recipient-lists/{list_id}/members/{member_id}

### Scheduled Broadcasts (8)
- POST /v2/broadcast/scheduled
- GET /v2/broadcast/scheduled
- GET /v2/broadcast/scheduled/{broadcast_id}
- PUT /v2/broadcast/scheduled/{broadcast_id}
- POST /v2/broadcast/scheduled/{broadcast_id}/activate
- POST /v2/broadcast/scheduled/{broadcast_id}/pause
- POST /v2/broadcast/scheduled/{broadcast_id}/cancel
- POST /v2/broadcast/scheduled/{broadcast_id}/execute

### Executions (3)
- GET /v2/broadcast/executions
- GET /v2/broadcast/executions/{execution_id}
- GET /v2/broadcast/executions/{execution_id}/details

### Preferences (2)
- GET /v2/broadcast/preferences
- PUT /v2/broadcast/preferences

### Unsubscribe (1)
- POST /v2/broadcast/unsubscribe

### Metrics (2)
- GET /v2/broadcast/metrics
- POST /v2/broadcast/metrics/record

### Dashboard & Processing (3)
- GET /v2/broadcast/dashboard
- GET /v2/broadcast/due
- POST /v2/broadcast/process-due

## Pattern de signature

Tous les endpoints suivent ce pattern:

```python
@router.{method}("/{path}")
async def endpoint_name(
    # Path params
    id: int,
    # Body/Query params
    data: Schema,
    # Context (toujours en dernier)
    context: SaaSContext = Depends(get_saas_context)
):
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    result = service.method(...)
    return result
```

## Tests

### Exécuter les tests

```bash
# Tous les tests du module
pytest app/modules/broadcast/tests/

# Tests spécifiques
pytest app/modules/broadcast/tests/test_router_v2.py

# Avec couverture
pytest app/modules/broadcast/tests/ --cov=app.modules.broadcast.router_v2

# Verbose
pytest app/modules/broadcast/tests/ -v
```

### Structure des tests

Chaque endpoint a au minimum:
1. Test de succès (happy path)
2. Test d'erreur 404 (ressource non trouvée)
3. Test avec filtres/pagination (si applicable)
4. Test de validation (si applicable)

## Compatibilité

| Aspect | v1 | v2 | Compatible |
|--------|----|----|-----------|
| Service | ✅ | ✅ | ✅ Oui (user_id optionnel) |
| Router | ✅ `/broadcast` | ✅ `/v2/broadcast` | ✅ Coexistent |
| Schemas | ✅ | ✅ | ✅ Partagés |
| Models | ✅ | ✅ | ✅ Partagés |
| Tests | ❌ | ✅ | N/A |

## Checklist de migration

- [x] Modifier service.py (constructor)
- [x] Créer router_v2.py
- [x] Implémenter 30 endpoints
- [x] Créer tests/conftest.py
- [x] Créer tests/test_router_v2.py
- [x] Implémenter 60+ tests
- [x] Vérifier imports
- [x] Vérifier syntaxe
- [ ] Intégrer dans app.main
- [ ] Tests d'intégration
- [ ] Documentation API
- [ ] Migration des clients

## Notes

1. **user_id**: Le service stocke maintenant user_id pour tracking et audit
2. **SaaSContext**: Remplace get_current_user + get_db par un contexte unifié
3. **Factory**: get_broadcast_service() extrait le contexte et crée le service
4. **Coexistence**: v1 et v2 peuvent coexister pendant la période de migration
5. **Tests**: Utilisation de mocks pour isoler les tests du router

## Support

Pour questions ou problèmes:
- Vérifier ce document
- Consulter les tests pour exemples d'utilisation
- Comparer avec router.py (v1) pour différences
