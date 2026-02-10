# MIGRATION DES ENDPOINTS VERS CORE SaaS
## Phase 2 - Simplification Authentification/Autorisation

---

## 🎯 Objectif

Migrer tous les endpoints pour utiliser `get_saas_context()` au lieu de `get_current_user()` + `get_tenant_id()`.

**Bénéfices :**
- ✅ Point d'entrée UNIQUE pour auth (CORE.authenticate())
- ✅ Contexte immuable (SaaSContext) au lieu de User mutable
- ✅ Permissions vérifiées via CORE.authorize()
- ✅ Audit automatique via CORE
- ✅ Code plus simple et lisible

---

## 📋 Pattern de Migration

### ❌ AVANT (Ancien Pattern)

```python
from app.core.dependencies import get_current_user, get_tenant_id
from app.core.models import User

@router.get("/customers")
def list_customers(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    # Vérification manuelle des permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.COMMERCIAL]:
        raise HTTPException(
            status_code=403,
            detail="Permission denied"
        )

    # Vérifier module actif manuellement (souvent oublié !)
    # ...

    # Logique métier
    service = get_commercial_service(db, tenant_id)
    customers = service.list_customers(user_id=current_user.id)

    return customers
```

**Problèmes :**
- 🔴 Vérification permissions manuelle et répétitive
- 🔴 Risque d'oublier de vérifier module actif
- 🔴 Pas d'audit automatique
- 🔴 Code verbeux
- 🔴 Logique auth dispersée dans les endpoints

---

### ✅ APRÈS (Nouveau Pattern avec CORE)

#### Option 1 : Utiliser `get_saas_context()` + vérifications manuelles

```python
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
from app.core.saas_core import get_saas_core, SaaSCore

@router.get("/customers")
def list_customers(
    context: SaaSContext = Depends(get_saas_context),
    core: SaaSCore = Depends(get_saas_core),
    db: Session = Depends(get_db)
):
    # Vérification permission via CORE
    if not core.authorize(context, "commercial.customer.list"):
        raise HTTPException(403, detail="Permission denied")

    # Vérification module actif via CORE
    if not core.is_module_active(context, "commercial"):
        raise HTTPException(403, detail="Module not active")

    # Logique métier
    service = get_commercial_service(db, context.tenant_id)
    customers = service.list_customers(user_id=context.user_id)

    return customers
```

**Avantages :**
- ✅ Contexte immuable
- ✅ Vérifications centralisées via CORE
- ✅ Audit automatique (via CORE.authenticate)
- ✅ Plus explicite

---

#### Option 2 : Utiliser `require_permission()` + `require_module_active()` (RECOMMANDÉ)

```python
from app.core.dependencies_v2 import (
    get_saas_context,
    require_permission,
    require_module_active
)
from app.core.saas_context import SaaSContext

@router.get("/customers")
def list_customers(
    context: SaaSContext = Depends(get_saas_context),
    _perm: None = Depends(require_permission("commercial.customer.list")),
    _module: None = Depends(require_module_active("commercial")),
    db: Session = Depends(get_db)
):
    # Permissions et module actif déjà vérifiés par les dependencies !
    # Aucune vérification manuelle nécessaire

    # Logique métier pure
    service = get_commercial_service(db, context.tenant_id)
    customers = service.list_customers(user_id=context.user_id)

    return customers
```

**Avantages :**
- ✅ Code ultra-concis
- ✅ Déclaratif (permissions dans la signature)
- ✅ Impossible d'oublier les vérifications
- ✅ Auto-documenté (on voit les permissions requises)

---

#### Option 3 : Utiliser `CORE.execute()` (FUTUR - Phase 4)

```python
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
from app.core.saas_core import get_saas_core, SaaSCore

@router.get("/customers")
async def list_customers(
    context: SaaSContext = Depends(get_saas_context),
    core: SaaSCore = Depends(get_saas_core)
):
    # Tout est centralisé dans CORE.execute()
    # Vérifie : module actif + permission + audit + exécution
    result = await core.execute(
        action="commercial.customer.list",
        context=context
    )

    if not result.success:
        raise HTTPException(400, detail=result.error)

    return result.data
```

**Avantages :**
- ✅ Pattern ultime : tout passe par CORE
- ✅ Endpoint réduit au minimum
- ✅ Logique métier dans executor (séparée de l'endpoint)
- ⚠️ Nécessite création d'executors (Phase 4)

---

## 🔄 Guide de Migration Étape par Étape

### Étape 1 : Identifier les Endpoints à Migrer

```bash
# Lister tous les endpoints utilisant get_current_user
grep -r "get_current_user" app/api/*.py app/modules/*/router.py
```

### Étape 2 : Migrer un Endpoint

1. **Remplacer les imports**
   ```python
   # AVANT
   from app.core.dependencies import get_current_user, get_tenant_id
   from app.core.models import User

   # APRÈS
   from app.core.dependencies_v2 import (
       get_saas_context,
       require_permission,
       require_module_active
   )
   from app.core.saas_context import SaaSContext
   ```

2. **Remplacer la signature**
   ```python
   # AVANT
   def my_endpoint(
       current_user: User = Depends(get_current_user),
       tenant_id: str = Depends(get_tenant_id),
       db: Session = Depends(get_db)
   ):

   # APRÈS
   def my_endpoint(
       context: SaaSContext = Depends(get_saas_context),
       _perm: None = Depends(require_permission("module.resource.action")),
       _module: None = Depends(require_module_active("module")),
       db: Session = Depends(get_db)
   ):
   ```

3. **Remplacer les usages**
   ```python
   # AVANT
   current_user.id → context.user_id
   current_user.role → context.role
   tenant_id → context.tenant_id

   # Vérification permission manuelle → Utiliser require_permission()
   # Vérification module manuelle → Utiliser require_module_active()
   ```

4. **Supprimer les vérifications manuelles**
   ```python
   # AVANT - À SUPPRIMER
   if current_user.role not in [UserRole.ADMIN]:
       raise HTTPException(403)

   # APRÈS - Remplacé par dependency
   _perm: None = Depends(require_permission("module.resource.action"))
   ```

### Étape 3 : Tester l'Endpoint

```bash
# Lancer les tests unitaires de l'endpoint
pytest tests/test_module.py::test_my_endpoint -v

# Tester manuellement avec curl
curl -X GET "http://localhost:8000/v1/customers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: $TENANT_ID"
```

---

## 📊 Matrice de Migration par Module

| Module | Endpoints Total | Migrés | Statut | Notes |
|--------|----------------|--------|--------|-------|
| auth | 12 | 0 | ⏳ TODO | Priority 1 - Endpoints login/register |
| commercial | 24 | 0 | ⏳ TODO | Priority 2 |
| invoicing | 18 | 0 | ⏳ TODO | Priority 2 |
| treasury | 8 | 0 | ⏳ TODO | Priority 3 |
| accounting | 15 | 0 | ⏳ TODO | Priority 3 |
| hr | 12 | 0 | ⏳ TODO | Priority 4 |
| iam | 10 | 0 | ⏳ TODO | Priority 1 - Gestion users/roles |
| ... | ... | ... | ... | ... |

**Total : ~150-200 endpoints à migrer**

---

## 🧪 Tests de Migration

### Test Pattern AVANT/APRÈS

```python
# tests/test_migration.py

def test_old_pattern_still_works():
    """Test que l'ancien pattern fonctionne encore (compatibilité)."""
    # TODO: À supprimer une fois migration complète
    pass

def test_new_pattern_with_saas_context():
    """Test nouveau pattern avec SaaSContext."""
    context = SaaSContext(
        tenant_id="TEST",
        user_id=uuid.uuid4(),
        role=UserRole.ADMIN,
        permissions={"commercial.customer.list"},
    )

    # Vérifier que l'endpoint accepte SaaSContext
    response = client.get(
        "/v1/customers",
        headers={
            "Authorization": f"Bearer {create_token(context.user_id)}",
            "X-Tenant-ID": context.tenant_id
        }
    )

    assert response.status_code == 200

def test_permission_denied_with_saas_context():
    """Test refus permission avec SaaSContext."""
    context = SaaSContext(
        tenant_id="TEST",
        user_id=uuid.uuid4(),
        role=UserRole.EMPLOYE,  # Pas de permission
        permissions=set(),
    )

    response = client.get(
        "/v1/customers",
        headers={
            "Authorization": f"Bearer {create_token(context.user_id)}",
            "X-Tenant-ID": context.tenant_id
        }
    )

    assert response.status_code == 403
    assert "Permission denied" in response.json()["detail"]
```

---

## 📈 Progression de la Migration

### Phase 2.1 : Endpoints Critiques (Semaine 1)
- [ ] /auth/login
- [ ] /auth/register
- [ ] /auth/bootstrap
- [ ] /v1/users (IAM)
- [ ] /v1/tenants

### Phase 2.2 : Modules Métier Core (Semaine 2-3)
- [ ] Commercial (24 endpoints)
- [ ] Invoicing (18 endpoints)
- [ ] Treasury (8 endpoints)
- [ ] Accounting (15 endpoints)

### Phase 2.3 : Autres Modules (Semaine 4)
- [ ] HR (12 endpoints)
- [ ] Inventory (10 endpoints)
- [ ] Projects (8 endpoints)
- [ ] Quality (6 endpoints)
- [ ] ... (autres modules)

---

## ⚠️ Points d'Attention

### 1. Compatibilité Temporaire

Pendant la migration, les deux patterns coexistent :
- Ancien : `get_current_user()` + `get_tenant_id()` (DÉPRÉCIÉ)
- Nouveau : `get_saas_context()` (RECOMMANDÉ)

**Ne PAS mélanger les deux dans le même endpoint !**

### 2. Tests à Mettre à Jour

Tous les tests utilisant `get_current_user` mock doivent être mis à jour pour utiliser `get_saas_context` mock :

```python
# AVANT
@pytest.fixture
def mock_current_user():
    return User(id=uuid.uuid4(), tenant_id="TEST", role=UserRole.ADMIN)

# APRÈS
@pytest.fixture
def mock_saas_context():
    return SaaSContext(
        tenant_id="TEST",
        user_id=uuid.uuid4(),
        role=UserRole.ADMIN,
        permissions={"*"}
    )
```

### 3. Performance

Le nouveau pattern a un overhead minimal :
- CoreAuthMiddleware crée SaaSContext une fois par requête
- SaaSContext est immuable (frozen dataclass) → très rapide
- Pas de requête DB supplémentaire (déjà fait dans authenticate)

### 4. Rollback

Si problème critique, rollback possible en 2 étapes :
1. Reverter `app/main.py` pour utiliser `AuthMiddleware`
2. Reverter imports dans endpoints migrés

---

## 📚 Ressources

- **Code CORE** : `app/core/saas_core.py`
- **Dependencies v2** : `app/core/dependencies_v2.py`
- **SaaSContext** : `app/core/saas_context.py`
- **Tests CORE** : `tests/core/test_saas_core.py`
- **Plan complet** : `REFACTOR_SAAS_SIMPLIFICATION.md`

---

## ✅ Checklist Migration d'un Endpoint

- [ ] Remplacer imports (`get_current_user` → `get_saas_context`)
- [ ] Mettre à jour signature fonction
- [ ] Ajouter `require_permission()` si besoin
- [ ] Ajouter `require_module_active()` si besoin
- [ ] Remplacer usages (`current_user.id` → `context.user_id`)
- [ ] Supprimer vérifications manuelles permissions
- [ ] Mettre à jour tests unitaires
- [ ] Tester manuellement l'endpoint
- [ ] Vérifier que l'audit fonctionne (CoreAuditJournal)
- [ ] Documenter la migration (ce fichier)

---

**Status : Phase 2 - Migration en cours**

Dernière mise à jour : 2026-01-25
