# Migration Maintenance vers CORE SaaS v2

## Statut: ✅ MIGRÉ

**Date de migration:** 2026-01-26

## Résumé

Le module Maintenance (GMAO) a été migré vers l'architecture CORE SaaS v2, permettant une isolation multi-tenant robuste et un audit trail automatique.

## Modifications apportées

### 1. Service (`service.py`)
- **Ligne 62:** Constructor modifié pour rendre `user_id` optionnel
  ```python
  # Avant:
  def __init__(self, db: Session, tenant_id: int, user_id: int):

  # Après:
  def __init__(self, db: Session, tenant_id: int, user_id: int = None):
  ```
- Le service accepte toujours des `int` pour `tenant_id` et `user_id`

### 2. Router v2 (`router_v2.py`)
- **34 endpoints** migrés vers l'architecture v2
- **Prefix:** `/v2/maintenance`
- **Tags:** `["Maintenance v2 - CORE SaaS"]`
- Utilise `get_saas_context()` au lieu de `get_current_user()`
- Factory avec conversion `str` → `int`:
  ```python
  def get_maintenance_service(
      db: Session = Depends(get_db),
      context: SaaSContext = Depends(get_saas_context)
  ) -> MaintenanceService:
      return MaintenanceService(db, int(context.tenant_id), int(context.user_id))
  ```

### 3. Tests (`tests/`)
- **60 tests** créés pour couvrir tous les endpoints
- Fichiers:
  - `tests/__init__.py`
  - `tests/conftest.py` (fixtures mock avec tenant_id="123", user_id="456")
  - `tests/test_router_v2.py` (60 tests unitaires)

## Détails des endpoints

### Assets (5 endpoints)
- `POST /v2/maintenance/assets` - Créer un actif
- `GET /v2/maintenance/assets` - Lister les actifs
- `GET /v2/maintenance/assets/{asset_id}` - Récupérer un actif
- `PUT /v2/maintenance/assets/{asset_id}` - Mettre à jour un actif
- `DELETE /v2/maintenance/assets/{asset_id}` - Supprimer un actif

### Meters (2 endpoints)
- `POST /v2/maintenance/assets/{asset_id}/meters` - Créer un compteur
- `POST /v2/maintenance/meters/{meter_id}/readings` - Enregistrer un relevé

### Maintenance Plans (4 endpoints)
- `POST /v2/maintenance/plans` - Créer un plan
- `GET /v2/maintenance/plans` - Lister les plans
- `GET /v2/maintenance/plans/{plan_id}` - Récupérer un plan
- `PUT /v2/maintenance/plans/{plan_id}` - Mettre à jour un plan

### Work Orders (9 endpoints)
- `POST /v2/maintenance/work-orders` - Créer un ordre
- `GET /v2/maintenance/work-orders` - Lister les ordres
- `GET /v2/maintenance/work-orders/{wo_id}` - Récupérer un ordre
- `PUT /v2/maintenance/work-orders/{wo_id}` - Mettre à jour un ordre
- `POST /v2/maintenance/work-orders/{wo_id}/start` - Démarrer un ordre
- `POST /v2/maintenance/work-orders/{wo_id}/complete` - Terminer un ordre
- `POST /v2/maintenance/work-orders/{wo_id}/labor` - Ajouter main d'œuvre
- `POST /v2/maintenance/work-orders/{wo_id}/parts` - Ajouter une pièce

### Failures (4 endpoints)
- `POST /v2/maintenance/failures` - Enregistrer une panne
- `GET /v2/maintenance/failures` - Lister les pannes
- `GET /v2/maintenance/failures/{failure_id}` - Récupérer une panne
- `PUT /v2/maintenance/failures/{failure_id}` - Mettre à jour une panne

### Spare Parts (4 endpoints)
- `POST /v2/maintenance/spare-parts` - Créer une pièce
- `GET /v2/maintenance/spare-parts` - Lister les pièces
- `GET /v2/maintenance/spare-parts/{part_id}` - Récupérer une pièce
- `PUT /v2/maintenance/spare-parts/{part_id}` - Mettre à jour une pièce

### Part Requests (2 endpoints)
- `POST /v2/maintenance/part-requests` - Créer une demande
- `GET /v2/maintenance/part-requests` - Lister les demandes

### Contracts (4 endpoints)
- `POST /v2/maintenance/contracts` - Créer un contrat
- `GET /v2/maintenance/contracts` - Lister les contrats
- `GET /v2/maintenance/contracts/{contract_id}` - Récupérer un contrat
- `PUT /v2/maintenance/contracts/{contract_id}` - Mettre à jour un contrat

### Dashboard (1 endpoint)
- `GET /v2/maintenance/dashboard` - Obtenir le tableau de bord

## Tests

### Couverture des tests
- **60 tests unitaires** créés
- Couverture complète des 34 endpoints
- Tests de succès et d'échec (404, 400)
- Tests avec filtres et paramètres

### Exécution des tests
```bash
# Tous les tests du module
pytest app/modules/maintenance/tests/

# Tests spécifiques
pytest app/modules/maintenance/tests/test_router_v2.py

# Avec couverture
pytest app/modules/maintenance/tests/ --cov=app.modules.maintenance
```

## Architecture v2

### Avant (v1)
```python
@router.get("/assets")
async def list_assets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = MaintenanceService(db, current_user.tenant_id, current_user.id)
    return service.list_assets()
```

### Après (v2)
```python
@router.get("/assets")
async def list_assets(
    service: MaintenanceService = Depends(get_maintenance_service)
):
    assets, total = service.list_assets()
    return PaginatedAssetResponse(items=assets, total=total)
```

## Avantages de la migration

1. **Isolation tenant automatique**: Plus besoin de passer manuellement le tenant_id
2. **Audit trail**: Traçabilité automatique via context.user_id
3. **Code plus propre**: Moins de dépendances explicites dans les endpoints
4. **Type-safe**: SaaSContext garantit la présence des champs requis
5. **Testabilité**: Mocks simplifiés avec override de dépendances
6. **Conversion flexible**: Le service reste compatible avec les types int

## Fichiers modifiés/créés

```
app/modules/maintenance/
├── service.py (modifié)
├── router_v2.py (créé)
├── MIGRATION_V2.md (créé)
└── tests/
    ├── __init__.py (créé)
    ├── conftest.py (créé)
    └── test_router_v2.py (créé)
```

## Compatibilité

- ✅ Router v1 (`router.py`) reste inchangé et fonctionnel
- ✅ Service compatible avec v1 et v2 (user_id optionnel)
- ✅ Pas de breaking changes pour les clients existants
- ✅ Migration progressive possible

## Prochaines étapes

1. Déployer le router_v2 en production
2. Tester les endpoints v2 avec des clients pilotes
3. Migrer progressivement les clients de v1 vers v2
4. Déprécier et retirer v1 après période de transition

## Notes techniques

- **Tenant ID**: String dans SaaSContext, converti en int pour le service
- **User ID**: String dans SaaSContext, converti en int pour le service
- **Status codes**: Utilisation des constantes `status.HTTP_*` de FastAPI
- **Validation**: Pydantic schemas inchangés, compatibles v1/v2
