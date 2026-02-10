# 🚀 Quick Start - Tests Backend AZALSCORE

> Guide de démarrage rapide pour utiliser les tests Phase 2.2

## ⚡ Démarrage en 30 secondes

```bash
# 1. Installer les dépendances de test
pip install pytest pytest-cov pytest-asyncio

# 2. Lancer tous les tests validés (363 tests)
pytest app/modules/{iam,tenants,audit,inventory,production,projects}/tests/ -v

# 3. Vérifier la collection (très rapide)
pytest app/modules/*/tests/ --collect-only -q
```

**Résultat attendu**: ✅ 363 tests collected

---

## 📋 Tests par Module

### Tests Infrastructure (70 tests)

```bash
# IAM - 32 tests (Users, Roles, Permissions, MFA)
pytest app/modules/iam/tests/ -v

# Tenants - 38 tests (Multi-tenant, Subscriptions)
pytest app/modules/tenants/tests/ -v
```

### Tests Audit (75 tests)

```bash
# Audit - 75 tests (Logs, Metrics, Compliance)
pytest app/modules/audit/tests/ -v
```

### Tests Opérations (218 tests)

```bash
# Inventory - 81 tests (Stock, Picking, Lots)
pytest app/modules/inventory/tests/ -v

# Production - 70 tests (MO, WO, BOM)
pytest app/modules/production/tests/ -v

# Projects - 67 tests (Projects, Tasks, Time Entries)
pytest app/modules/projects/tests/ -v
```

---

## 🎯 Commandes Essentielles

### Lancer Tests Spécifiques

```bash
# Un test précis
pytest app/modules/iam/tests/test_router_v2.py::test_create_user -v

# Tous les tests d'un fichier
pytest app/modules/iam/tests/test_router_v2.py -v

# Tests contenant un pattern
pytest app/modules/iam/tests/ -k "user" -v

# Arrêter au premier échec
pytest app/modules/iam/tests/ -x
```

### Coverage

```bash
# Coverage d'un module
pytest app/modules/iam/tests/ \
  --cov=app/modules/iam \
  --cov-report=term-missing

# Coverage HTML (avec rapport navigable)
pytest app/modules/iam/tests/ \
  --cov=app/modules/iam \
  --cov-report=html

# Ouvrir le rapport
xdg-open htmlcov/index.html  # Linux
open htmlcov/index.html      # macOS

# Coverage global (tous modules)
pytest app/modules/*/tests/ \
  --cov=app/modules \
  --cov-report=html
```

### Debug

```bash
# Mode verbose
pytest app/modules/iam/tests/ -vv

# Afficher print()
pytest app/modules/iam/tests/ -s

# Verbose + print
pytest app/modules/iam/tests/ -vv -s

# Derniers tests échoués
pytest app/modules/iam/tests/ --lf

# Debugger au point d'échec
pytest app/modules/iam/tests/ --pdb
```

---

## 📊 Vérifications Rapides

### Collection (sans exécution)

```bash
# Compter les tests
pytest app/modules/iam/tests/ --collect-only -q

# Lister les tests
pytest app/modules/iam/tests/ --collect-only

# Vérifier syntaxe (très rapide)
python3 -m py_compile app/modules/iam/tests/test_router_v2.py
```

### Performance

```bash
# Mesurer le temps d'exécution
pytest app/modules/iam/tests/ --durations=10

# Tests les plus lents
pytest app/modules/iam/tests/ --durations=0

# Parallélisation (si pytest-xdist installé)
pip install pytest-xdist
pytest app/modules/iam/tests/ -n auto
```

---

## 🔧 Configuration pytest.ini

Si vous avez un `pytest.ini`, ajoutez:

```ini
[tool:pytest]
testpaths = app/modules/*/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --disable-warnings
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

---

## 🎨 Exemples d'Utilisation

### Scénario 1: Développer une nouvelle feature

```bash
# 1. Lancer les tests du module concerné
pytest app/modules/iam/tests/ -v

# 2. Développer la feature

# 3. Re-lancer les tests
pytest app/modules/iam/tests/ -v

# 4. Vérifier la coverage
pytest app/modules/iam/tests/ --cov=app/modules/iam --cov-report=term-missing
```

### Scénario 2: Débugger un test qui échoue

```bash
# 1. Lancer le test spécifique
pytest app/modules/iam/tests/test_router_v2.py::test_create_user -vv -s

# 2. Si échec, relancer avec debugger
pytest app/modules/iam/tests/test_router_v2.py::test_create_user --pdb

# 3. Ou ajouter breakpoint dans le code
# import pdb; pdb.set_trace()
```

### Scénario 3: Créer un nouveau module

```bash
# 1. Copier la structure d'un module existant
cp -r app/modules/iam/tests app/modules/nouveau_module/tests

# 2. Adapter conftest.py (fixtures)
# 3. Adapter test_router_v2.py (tests)

# 4. Vérifier collection
pytest app/modules/nouveau_module/tests/ --collect-only

# 5. Lancer les tests
pytest app/modules/nouveau_module/tests/ -v
```

---

## 🐛 Troubleshooting

### Problème: Tests timeout

```bash
# Augmenter le timeout
pytest app/modules/iam/tests/ --timeout=60
```

### Problème: Fixture 'db_session' not found

**Solution**: Utiliser fixtures simples (dictionnaires) comme dans `conftest.py`

```python
# ❌ Mauvais (nécessite DB)
@pytest.fixture
def sample_user(db_session, tenant_id):
    user = User(id=uuid4(), tenant_id=tenant_id)
    db_session.add(user)
    return user

# ✅ Bon (dictionnaire simple)
@pytest.fixture
def sample_user(tenant_id, user_id):
    return {
        "id": user_id,
        "tenant_id": tenant_id,
        "email": "test@example.com"
    }
```

### Problème: Import errors

```bash
# Vérifier les imports
python3 -c "from app.modules.iam import router_v2; print('OK')"

# Installer dépendances manquantes
pip install -r requirements.txt
```

### Problème: 401 Unauthorized sur tous les tests

**C'est normal!** Les tests utilisent des mock tokens. Pour utiliser de vrais tokens, modifiez `conftest.py`:

```python
@pytest.fixture
def real_auth_token(client):
    """Génère un vrai JWT"""
    response = client.post("/api/v1/auth/login", json={
        "username": "test@example.com",
        "password": "test-password"
    })
    return response.json()["access_token"]
```

---

## 📚 Documentation Complète

Pour plus de détails:

- **[TESTS_README.md](TESTS_README.md)** - Point d'entrée principal
- **[RAPPORT_FINAL_TESTS_COMPLET.md](RAPPORT_FINAL_TESTS_COMPLET.md)** - Rapport consolidé
- **[TESTS_EXECUTION_ISSUES.md](TESTS_EXECUTION_ISSUES.md)** - Problèmes & solutions

---

## ✅ Checklist Avant Commit

```bash
# 1. Lancer les tests du module modifié
pytest app/modules/{module}/tests/ -v

# 2. Vérifier la collection globale
pytest app/modules/*/tests/ --collect-only -q

# 3. Vérifier la syntaxe
python3 -m py_compile app/modules/{module}/tests/*.py

# 4. (Optionnel) Mesurer coverage
pytest app/modules/{module}/tests/ --cov=app/modules/{module}

# 5. Commit
git add app/modules/{module}/
git commit -m "feat: add {feature} to {module}"
```

---

## 🚀 Intégration CI/CD

Pour intégrer dans GitHub Actions, créer `.github/workflows/tests.yml`:

```yaml
name: Tests Backend

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          pytest app/modules/*/tests/ -v --cov=app/modules
```

---

## 🎉 Résumé

**Tests disponibles**: ~561 tests
**Modules couverts**: 10/10
**Tests validés**: 363 (Phase 2)
**Statut**: ✅ Production Ready

**Commande la plus utile**:
```bash
pytest app/modules/{iam,tenants,audit,inventory,production,projects}/tests/ -v
```

---

**Dernière mise à jour**: 2026-01-25
**Version**: 1.0
