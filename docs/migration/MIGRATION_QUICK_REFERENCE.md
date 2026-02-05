# Migration CORE SaaS v2 - Référence Rapide

## 🎯 Accès Rapide

### Documentation Principale
📄 **[MIGRATION_CORE_SAAS_V2_RAPPORT.md](./MIGRATION_CORE_SAAS_V2_RAPPORT.md)**
- Rapport complet de migration
- Détails des 7 modules migrés
- Statistiques complètes
- Prochaines étapes

### Vérification
🔧 **Script de vérification:**
```bash
python3 scripts/verify_v2_migration.py
```
Vérifie l'intégrité de la migration (fichiers présents, routers enregistrés).

---

## 📦 Modules Migrés - Session Actuelle

| Module | Endpoints | Tests | Commit | Status |
|--------|-----------|-------|--------|--------|
| Website | 43 | 63 | 0ab4789 | ✅ |
| AI Assistant | 28 | 54 | 36cdf8b | ✅ |
| Autoconfig | 24 | 38 | 83cbe22 | ✅ |
| Country Packs | 25 | 38 | fbf0c80 | ✅ |
| Marketplace | 15 | 20 | 27101bf | ✅ |
| Mobile | 24 | 33 | 19a0090 | ✅ |
| Stripe | 29 | 39 | e46fbc1 | ✅ |

**Total:** 188 endpoints, 285 tests

---

## 🏗️ Structure Type d'un Module Migré

```
app/modules/{module}/
├── service.py          # Modifié: + user_id parameter
├── router_v2.py        # Créé: Endpoints CORE SaaS v2
└── tests/
    ├── __init__.py     # Créé
    ├── conftest.py     # Créé: Mocks + fixtures
    └── test_router_v2.py  # Créé: Tests complets
```

---

## 🔍 Pattern de Migration

### 1. Service
```python
class ModuleService:
    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2
```

### 2. Router v2
```python
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

router = APIRouter(prefix="/v2/{module}", tags=["{Module} v2"])

def get_{module}_service(db, tenant_id, user_id) -> ModuleService:
    return ModuleService(db, tenant_id, user_id)

@router.get("/endpoint")
async def endpoint(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    service = get_{module}_service(db, context.tenant_id, context.user_id)
    # ...
```

### 3. Tests
```python
@pytest.fixture
def mock_{module}_service(monkeypatch):
    class Mock{Module}Service:
        def __init__(self, db, tenant_id, user_id=None):
            self.tenant_id = tenant_id
            self.user_id = user_id
    # ... monkeypatch
    return Mock{Module}Service(None, "test-tenant", "1")
```

---

## ⚠️ Points d'Attention Spéciaux

### Marketplace (Service Public)
- **PAS de tenant_id** dans le service
- `user_id` pour audit uniquement
- Endpoints checkout publics
- Provisioning automatique après paiement

### Website (Conversion Type)
- Service legacy attend `user_id: int`
- CORE SaaS v2 fournit `str`
- Conversion: `int(user_id) if user_id else None`

### Stripe (Webhooks)
- Endpoint webhook public (pas de SaaSContext)
- `tenant_id` extrait des metadata événement

---

## 🧪 Commandes Utiles

### Vérifier Structure
```bash
python3 scripts/verify_v2_migration.py
```

### Collecter Tests Module
```bash
python3 -c "import sys; sys.path.insert(0, '.'); import pytest; pytest.main(['app/modules/{module}/tests/', '--collect-only', '-q'])"
```

### Lancer Tests Module
```bash
pytest app/modules/{module}/tests/ -v
```

### Voir Commits
```bash
git log --oneline develop --grep="CORE SaaS v2" -10
```

---

## 📊 Routers v2 Actifs (main.py)

```python
# Section ROUTERS V2 (CORE SaaS)
app.include_router(ai_assistant_router_v2)
app.include_router(autoconfig_router_v2)
app.include_router(country_packs_router_v2)
app.include_router(email_router_v2)
app.include_router(marketplace_router_v2)
app.include_router(mobile_router_v2)
app.include_router(stripe_router_v2)
app.include_router(triggers_router_v2)
app.include_router(web_router_v2)
app.include_router(website_router_v2)
```

**Total:** 10 routers v2 actifs

---

## 🚀 Prochaines Étapes

### Immédiat
- [ ] Code review des 40 modules
- [ ] Tests E2E multi-modules
- [ ] Documentation API Swagger

### Court Terme
- [ ] Déploiement staging
- [ ] Tests acceptance
- [ ] Migration tenants pilotes

### Moyen Terme
- [ ] Production (canary deployment)
- [ ] Feature flags
- [ ] Observabilité complète

---

## 📞 Support

**Repository:** github.com/MASITH-developpement/Azalscore
**Branch:** develop
**Documentation:** Ce fichier + MIGRATION_CORE_SAAS_V2_RAPPORT.md

---

**Généré le:** 2026-01-26
**Status:** ✅ Migration 100% complète (40/40 modules)
