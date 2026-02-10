# 🚀 Guide CI/CD - Tests Backend CORE SaaS v2

**Date**: 2026-01-25
**Version**: 1.0
**Modules couverts**: 10 modules (iam, tenants, audit, inventory, production, projects, finance, commercial, hr, guardian)

---

## 📋 Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Configuration CI/CD](#configuration-cicd)
3. [Scripts Locaux](#scripts-locaux)
4. [Utilisation Quotidienne](#utilisation-quotidienne)
5. [Seuils et Métriques](#seuils-et-métriques)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Vue d'Ensemble

Le CI/CD AZALSCORE teste automatiquement:
- ✅ **10 modules** backend CORE SaaS v2
- ✅ **~561 tests** au total (363 validés Phase 2)
- ✅ **Coverage ≥50%** requis
- ✅ **Lint & Type checking** automatiques
- ✅ **Rapports de test** générés

---

## 🔧 Configuration CI/CD

### Fichiers Créés

```
.github/workflows/
└── tests-backend-core-saas.yml    # Workflow principal

pytest.ini                          # Configuration pytest
.coveragerc                         # Configuration coverage

scripts/
├── run_tests.sh                    # Lancer tests localement
└── measure_coverage.sh             # Mesurer coverage localement
```

### Workflow GitHub Actions

**Fichier**: `.github/workflows/tests-backend-core-saas.yml`

**Déclenché sur**:
- Push sur `develop` ou `main`
- Pull Request vers `develop` ou `main`
- Modifications de:
  - `app/modules/*/router_v2.py`
  - `app/modules/*/tests/**`
  - `app/core/saas_*.py`
  - `app/core/dependencies_v2.py`

**Jobs exécutés**:

1. **test-modules** (matrice)
   - Teste chaque module individuellement
   - Génère coverage par module
   - Upload coverage vers Codecov
   - Upload résultats tests

2. **coverage-report**
   - Génère rapport coverage global
   - Vérifie seuil ≥50%
   - Upload rapport HTML
   - Commente PR avec coverage

3. **lint**
   - Ruff (linting)
   - MyPy (type checking)

4. **test-summary**
   - Agrège tous les résultats
   - Publie résumé dans PR

---

## 🛠️ Scripts Locaux

### 1. Lancer les Tests

**Tous les modules**:
```bash
./scripts/run_tests.sh
```

**Un module spécifique**:
```bash
./scripts/run_tests.sh iam
```

**Options**:
```bash
./scripts/run_tests.sh -q              # Mode silencieux
./scripts/run_tests.sh -x              # Arrêter au premier échec
./scripts/run_tests.sh -n              # Parallèle (pytest-xdist requis)
./scripts/run_tests.sh iam -x          # IAM avec fail-fast
```

**Sortie exemple**:
```
╔═══════════════════════════════════════════════════════╗
║  🧪 AZALSCORE Tests Runner - Backend v2               ║
╚═══════════════════════════════════════════════════════╝

📦 Modules: TOUS (Phase 2.2)

🧪 Lancement des tests...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Testing: iam
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ iam: PASSED
...

📊 RÉSUMÉ
✅ Modules passés (10):
   • iam
   • tenants
   ...
🎉 Tous les tests sont passés!
```

---

### 2. Mesurer le Coverage

**Tous les modules**:
```bash
./scripts/measure_coverage.sh
```

**Un module spécifique**:
```bash
./scripts/measure_coverage.sh iam
```

**Sortie exemple**:
```
╔═══════════════════════════════════════════════════════╗
║  📊 AZALSCORE Coverage Measurement - Backend v2       ║
╚═══════════════════════════════════════════════════════╝

📦 Module: iam

🧪 Lancement des tests...
...

✅ Coverage généré pour iam
📄 Rapport HTML: htmlcov/index.html
📄 Rapport XML: coverage.xml

📊 Vérification seuil de coverage (≥50%)...
✅ Coverage ≥50% - PASS
```

**Ouvrir le rapport HTML**:
```bash
# Linux
xdg-open htmlcov/index.html

# macOS
open htmlcov/index.html

# Windows
start htmlcov/index.html
```

---

## 👨‍💻 Utilisation Quotidienne

### Workflow Développeur

**1. Développer une feature**:
```bash
# Créer branche
git checkout -b feature/nouvelle-feature

# Développer...
# Écrire tests...
```

**2. Tester localement**:
```bash
# Lancer tests du module modifié
./scripts/run_tests.sh iam -x

# Vérifier coverage
./scripts/measure_coverage.sh iam
```

**3. Commit et push**:
```bash
git add .
git commit -m "feat(iam): add nouvelle feature"
git push origin feature/nouvelle-feature
```

**4. CI/CD automatique**:
- Tests lancés automatiquement
- Résultats visibles dans la PR
- Blocage si tests échouent

**5. Merger après validation**:
```bash
# CI/CD ✅ green
git checkout develop
git merge feature/nouvelle-feature
git push origin develop
```

---

### Pre-commit Hook (Recommandé)

Créer `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Pre-commit hook pour AZALSCORE

echo "🧪 Lancement tests pré-commit..."

# Détecter modules modifiés
MODIFIED_MODULES=$(git diff --cached --name-only | \
    grep "app/modules/.*/.*\.py" | \
    sed 's|app/modules/\([^/]*\)/.*|\1|' | \
    sort -u)

if [ -z "$MODIFIED_MODULES" ]; then
    echo "✅ Aucun module modifié"
    exit 0
fi

echo "📦 Modules modifiés: $MODIFIED_MODULES"

# Tester chaque module modifié
for mod in $MODIFIED_MODULES; do
    if [ -d "app/modules/$mod/tests" ]; then
        echo "🧪 Testing $mod..."
        if ! pytest app/modules/$mod/tests/ -q; then
            echo "❌ Tests échoués pour $mod"
            exit 1
        fi
    fi
done

echo "✅ Tous les tests pré-commit passés"
exit 0
```

Rendre exécutable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## 📊 Seuils et Métriques

### Seuils de Coverage

| Niveau | Seuil | Statut |
|--------|-------|--------|
| **Global** | ≥50% | ✅ Requis (CI/CD bloque si <50%) |
| **Recommandé** | ≥65% | 🎯 Objectif |
| **Excellent** | ≥80% | 🌟 Best practice |

### Par Module

Modules Phase 2 (validés):
- **IAM**: Target ≥60%
- **Tenants**: Target ≥60%
- **Audit**: Target ≥65%
- **Inventory**: Target ≥70%
- **Production**: Target ≥70%
- **Projects**: Target ≥65%

### Temps d'Exécution

**Local** (sans parallélisation):
- Un module: ~5-10 secondes
- Tous modules: ~1-2 minutes

**CI/CD** (avec parallélisation):
- Matrice de modules: ~2-3 minutes
- Coverage global: ~1 minute
- **Total pipeline**: ~3-5 minutes

---

## 🔍 Métriques Reportées

### Dans les Pull Requests

Le bot GitHub commente automatiquement avec:
```
📊 Coverage Report

Module      Coverage    Lines    Missing
─────────────────────────────────────────
iam         72.5%       400      110
tenants     68.3%       520      165
audit       75.2%       680      169
...

Global      71.2%      5240     1508

✅ Coverage ≥50% - PASS
```

### Artefacts Générés

Pour chaque run CI/CD:
- `test-results-{module}.xml` - Résultats JUnit
- `coverage.xml` - Rapport Codecov
- `coverage-html-report/` - Rapport HTML navigable

**Télécharger artefacts**:
- Dans GitHub Actions > Run > Artifacts

---

## 🚨 Troubleshooting

### Tests Échouent Localement

**1. Vérifier dépendances**:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio
```

**2. Vérifier imports**:
```bash
python3 -c "from app.modules.iam import router_v2; print('OK')"
```

**3. Vérifier fixtures**:
```bash
pytest app/modules/iam/tests/ --collect-only
```

**4. Mode debug**:
```bash
pytest app/modules/iam/tests/test_router_v2.py::test_create_user -vv -s
```

---

### Coverage Trop Bas

**1. Identifier zones non couvertes**:
```bash
./scripts/measure_coverage.sh iam
xdg-open htmlcov/index.html
```

**2. Ajouter tests manquants**:
- Edge cases
- Error handling
- Workflows complets

**3. Re-mesurer**:
```bash
./scripts/measure_coverage.sh iam
```

---

### CI/CD Échoue mais Local OK

**1. Vérifier versions Python**:
```bash
# Local
python --version

# CI/CD utilise Python 3.10
```

**2. Vérifier variables d'environnement**:
- Secrets GitHub configurés?
- Tokens Codecov OK?

**3. Vérifier paths**:
```yaml
# Workflow déclenché sur bons paths?
paths:
  - 'app/modules/*/router_v2.py'
  - 'app/modules/*/tests/**'
```

---

### Linter Échoue

**1. Lancer Ruff localement**:
```bash
pip install ruff
ruff check app/modules/iam/router_v2.py
```

**2. Auto-fix**:
```bash
ruff check --fix app/modules/iam/router_v2.py
```

**3. MyPy**:
```bash
pip install mypy
mypy app/modules/iam/router_v2.py --ignore-missing-imports
```

---

## 📚 Ressources

### Documentation

- **Tests Backend**: `TESTS_README.md`
- **Quick Start**: `TESTS_QUICK_START.md`
- **Rapport Phase 2.2**: `RAPPORT_FINAL_TESTS_COMPLET.md`

### Commandes Utiles

```bash
# Lister tous les tests
pytest app/modules/*/tests/ --collect-only -q

# Tests d'un module avec coverage
pytest app/modules/iam/tests/ --cov=app/modules/iam --cov-report=term-missing

# Tests parallèles (plus rapide)
pip install pytest-xdist
pytest app/modules/*/tests/ -n auto

# Tests avec markers
pytest app/modules/iam/tests/ -m "not slow"

# Derniers tests échoués
pytest --lf
```

### Liens Externes

- **Pytest**: https://docs.pytest.org/
- **Coverage.py**: https://coverage.readthedocs.io/
- **GitHub Actions**: https://docs.github.com/actions
- **Codecov**: https://docs.codecov.com/

---

## ✅ Checklist Validation CI/CD

Avant de merger une PR:

- [ ] Tous les tests passent (✅ green dans PR)
- [ ] Coverage ≥50% global
- [ ] Aucune régression de coverage
- [ ] Linter passe (Ruff)
- [ ] Type checking passe (MyPy)
- [ ] Tests locaux OK
- [ ] Pre-commit hook installé

---

## 🎯 Prochaines Améliorations

### Court Terme

- [ ] Augmenter seuil coverage à 65%
- [ ] Ajouter tests E2E
- [ ] Configurer notifications Slack

### Moyen Terme

- [ ] Tests de performance
- [ ] Tests de charge
- [ ] Security scanning (Bandit)

### Long Terme

- [ ] Déploiement automatique
- [ ] Rollback automatique si tests échouent
- [ ] Monitoring post-déploiement

---

**Créé le**: 2026-01-25
**Auteur**: Claude Opus 4.5
**Version**: 1.0
**Statut**: ✅ Opérationnel
