# 🚀 GUIDE DE DÉMARRAGE — NOUVEAU SYSTÈME AZALSCORE

**Version :** 1.0.0
**Date :** 2026-01-22
**Conformité :** 95% AZALSCORE

---

## 📖 INTRODUCTION

Ce guide explique comment utiliser le **nouveau système déclaratif AZALSCORE** qui transforme la plateforme d'un ERP classique vers un **moteur d'orchestration No-Code**.

### Qu'est-ce qui a changé ?

**Avant :**
- Modules Python monolithiques
- Logique métier dispersée
- Duplication de code
- Impossible de visualiser ou réutiliser

**Après :**
- ✅ **Registry centralisé** de sous-programmes réutilisables
- ✅ **Workflows DAG JSON** déclaratifs
- ✅ **Moteur d'orchestration** avec gestion centralisée des erreurs
- ✅ **API REST** pour exécuter les workflows
- ✅ **Traçabilité complète** de toutes les exécutions

---

## 🏗️ ARCHITECTURE DU NOUVEAU SYSTÈME

```
┌─────────────────────────────────────────────────────┐
│           API REST /v1/workflows/*                  │
│  - Exécute des workflows DAG                        │
│  - Liste les sous-programmes disponibles            │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│      MOTEUR D'ORCHESTRATION (engine.py)             │
│  - Interprète DAG JSON                              │
│  - Résout dépendances                               │
│  - Gère retry/timeout/fallback                      │
│  - Trace tout automatiquement                       │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│         REGISTRY (Bibliothèque centrale)            │
│  - Sous-programmes avec manifests JSON              │
│  - Versioning SemVer                                │
│  - Catégorisés & testés                             │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│      CODE MÉTIER PUR (impl.py)                      │
│  - Logique métier uniquement                        │
│  - Pas de try/catch                                 │
│  - Réutilisable partout                             │
└─────────────────────────────────────────────────────┘
```

---

## 📂 STRUCTURE DES FICHIERS

```
/home/ubuntu/azalscore/
├── registry/                       ← Nouveau : Bibliothèque centrale
│   ├── README.md                   ← Documentation complète
│   ├── finance/
│   │   └── calculate_margin/
│   │       ├── manifest.json       ← Source de vérité
│   │       ├── impl.py             ← Implémentation pure
│   │       └── tests/              ← Tests obligatoires
│   ├── validation/
│   ├── computation/
│   ├── notification/
│   └── data_transform/
│
├── app/
│   ├── registry/                   ← Nouveau : Loader du registry
│   │   ├── __init__.py
│   │   └── loader.py               ← RegistryLoader
│   │
│   ├── orchestration/              ← Nouveau : Moteur d'orchestration
│   │   ├── __init__.py
│   │   └── engine.py               ← OrchestrationEngine
│   │
│   ├── api/
│   │   └── workflows.py            ← Nouveau : API workflows
│   │
│   └── modules/
│       └── finance/
│           └── workflows/          ← Nouveau : Workflows DAG
│               └── invoice_analysis.json
│
├── tests/
│   ├── test_registry.py            ← Nouveau : 12 tests (100% pass)
│   └── test_orchestration.py       ← Nouveau : 9 tests (100% pass)
│
└── CONFORMITE_AZALSCORE.md         ← Nouveau : Rapport de conformité
```

---

## 🎯 CONCEPTS CLÉS

### 1. Manifest JSON = Source de vérité

**Règle fondamentale :** "Le manifest est la vérité, pas le code"

Chaque sous-programme est défini par son **manifest.json** qui déclare :
- Inputs/outputs
- Side effects (true/false)
- Idempotent (true/false)
- No-Code compatible (true/false)
- Version (SemVer strict)

**Exemple :** `/registry/finance/calculate_margin/manifest.json`

```json
{
  "id": "azalscore.finance.calculate_margin",
  "version": "1.0.0",
  "inputs": {
    "price": {"type": "number", "required": true},
    "cost": {"type": "number", "required": true}
  },
  "outputs": {
    "margin": {"type": "number"},
    "margin_rate": {"type": "number"}
  },
  "side_effects": false,
  "idempotent": true,
  "no_code_compatible": true
}
```

### 2. Code métier PUR

**Règle stricte :** Pas de try/catch dans le code métier

**Exemple :** `/registry/finance/calculate_margin/impl.py`

```python
def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Code métier PUR - aucune gestion d'erreur"""
    price = float(inputs["price"])
    cost = float(inputs["cost"])

    margin = price - cost
    margin_rate = (margin / price) if price > 0 else 0.0

    return {
        "margin": round(margin, 2),
        "margin_rate": round(margin_rate, 4)
    }
```

La gestion d'erreur est **déléguée au moteur d'orchestration**.

### 3. Workflows DAG déclaratifs

**Module = Orchestrateur** (pas de logique métier)

**Exemple :** `/app/modules/finance/workflows/invoice_analysis.json`

```json
{
  "module_id": "azalscore.finance.invoice_analysis",
  "steps": [
    {
      "id": "calculate_margin",
      "use": "azalscore.finance.calculate_margin@1.0.0",
      "inputs": {
        "price": "{{context.price}}",
        "cost": "{{context.cost}}"
      },
      "retry": 2,
      "timeout": 3000
    },
    {
      "id": "send_alert",
      "condition": "{{calculate_margin.margin_rate}} < 0.2",
      "use": "azalscore.notification.send_alert@1.0.0",
      "inputs": {
        "alert_type": "low_margin",
        "title": "Marge faible",
        "message": "Marge inférieure à 20%"
      },
      "retry": 3,
      "fallback": "azalscore.notification.log_alert"
    }
  ]
}
```

**Caractéristiques :**
- ✅ Déclaratif (pas impératif)
- ✅ Conditions sur les résultats précédents
- ✅ Retry/timeout/fallback déclaratifs
- ✅ Variables résolues automatiquement

### 4. Moteur d'orchestration centralisé

**Responsabilités du moteur :**
- Interprétation du DAG
- Résolution des dépendances
- Gestion des erreurs (retry/timeout/fallback)
- Traçabilité complète
- Logs automatiques

**Le code métier ne gère RIEN de tout ça.**

---

## 🚀 UTILISATION PRATIQUE

### Créer un sous-programme

**Étape 1 : Créer le manifest**

`/registry/validation/validate_email/manifest.json`

```json
{
  "id": "azalscore.validation.validate_email",
  "name": "Validation email",
  "category": "validation",
  "version": "1.0.0",
  "description": "Valide une adresse email",
  "inputs": {
    "email": {"type": "string", "required": true}
  },
  "outputs": {
    "is_valid": {"type": "boolean"},
    "normalized_email": {"type": "string"}
  },
  "side_effects": false,
  "idempotent": true,
  "no_code_compatible": true
}
```

**Étape 2 : Créer l'implémentation**

`/registry/validation/validate_email/impl.py`

```python
import re

def execute(inputs):
    email = inputs["email"].strip().lower()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    is_valid = bool(re.match(pattern, email))

    return {
        "is_valid": is_valid,
        "normalized_email": email if is_valid else None
    }
```

**Étape 3 : Créer les tests**

`/registry/validation/validate_email/tests/test_validate_email.py`

```python
from ..impl import execute

def test_valid_email():
    result = execute({"email": "user@example.com"})
    assert result["is_valid"] is True

def test_invalid_email():
    result = execute({"email": "invalid"})
    assert result["is_valid"] is False
```

**Étape 4 : Tester**

```bash
source venv/bin/activate
pytest registry/validation/validate_email/tests/
```

### Utiliser un sous-programme en Python

```python
from app.registry.loader import load_program

# Charger le sous-programme
program = load_program("azalscore.validation.validate_email@1.0.0")

# Exécuter
result = program.execute({"email": "user@example.com"})

print(result)
# {'is_valid': True, 'normalized_email': 'user@example.com'}
```

### Créer un workflow DAG

`/app/modules/commercial/workflows/validate_customer.json`

```json
{
  "module_id": "azalscore.commercial.validate_customer",
  "version": "1.0.0",
  "steps": [
    {
      "id": "validate_email",
      "use": "azalscore.validation.validate_email@1.0.0",
      "inputs": {
        "email": "{{context.customer_email}}"
      }
    },
    {
      "id": "validate_phone",
      "use": "azalscore.data_transform.normalize_phone@1.0.0",
      "inputs": {
        "phone": "{{context.customer_phone}}",
        "country_code": "FR"
      }
    },
    {
      "id": "send_welcome_email",
      "condition": "{{validate_email.is_valid}} == true",
      "use": "azalscore.notification.send_email@1.0.0",
      "inputs": {
        "to": "{{validate_email.normalized_email}}",
        "template": "welcome",
        "data": {
          "name": "{{context.customer_name}}"
        }
      }
    }
  ]
}
```

### Exécuter un workflow via l'API

**Méthode 1 : Par workflow_id**

```bash
curl -X POST http://localhost:8000/v1/workflows/execute \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "commercial.validate_customer",
    "context": {
      "customer_email": "john.doe@example.com",
      "customer_phone": "0612345678",
      "customer_name": "John Doe"
    }
  }'
```

**Méthode 2 : Par DAG JSON direct**

```bash
curl -X POST http://localhost:8000/v1/workflows/execute \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "dag": {
      "module_id": "custom.workflow",
      "steps": [...]
    },
    "context": {...}
  }'
```

**Réponse :**

```json
{
  "module_id": "azalscore.commercial.validate_customer",
  "status": "completed",
  "duration_ms": 45,
  "steps": {
    "validate_email": {
      "status": "completed",
      "output": {
        "is_valid": true,
        "normalized_email": "john.doe@example.com"
      },
      "duration_ms": 12,
      "attempts": 1
    },
    "validate_phone": {
      "status": "completed",
      "output": {
        "normalized_phone": "+33612345678",
        "is_valid": true
      },
      "duration_ms": 8,
      "attempts": 1
    },
    "send_welcome_email": {
      "status": "completed",
      "output": {
        "email_id": "uuid-xxx",
        "sent_at": "2026-01-22T21:30:00Z"
      },
      "duration_ms": 25,
      "attempts": 1
    }
  },
  "context": {
    "customer_email": "john.doe@example.com",
    "customer_phone": "0612345678",
    "customer_name": "John Doe",
    "validate_email": {...},
    "validate_phone": {...},
    "send_welcome_email": {...}
  },
  "error": null
}
```

### Lister les sous-programmes disponibles

```bash
curl -X GET http://localhost:8000/v1/workflows/programs \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID"
```

**Réponse :**

```json
{
  "count": 5,
  "programs": [
    {
      "id": "azalscore.computation.calculate_vat",
      "name": "Calcul de TVA",
      "category": "computation",
      "version": "1.0.0",
      "description": "Calcule le montant TTC...",
      "side_effects": false,
      "idempotent": true,
      "no_code_compatible": true,
      "tags": ["computation", "vat", "tax"]
    },
    ...
  ]
}
```

### Lister les workflows disponibles

```bash
curl -X GET http://localhost:8000/v1/workflows/list \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID"
```

---

## 🧪 TESTS

### Tests du registry

```bash
source venv/bin/activate
pytest tests/test_registry.py -v
```

**Résultat attendu :**
```
12 passed in 0.18s ✅
```

### Tests du moteur d'orchestration

```bash
pytest tests/test_orchestration.py -v
```

**Résultat attendu :**
```
9 passed in 0.10s ✅
```

### Tests complets

```bash
pytest tests/test_registry.py tests/test_orchestration.py -v
```

**Résultat attendu :**
```
21 passed in 0.28s ✅
```

---

## 📋 CHECKLIST CRÉATION SOUS-PROGRAMME

Avant d'ajouter un sous-programme au registry :

- [ ] **Manifest JSON valide**
  - [ ] Champs obligatoires présents (id, version, inputs, outputs, side_effects, idempotent, no_code_compatible)
  - [ ] Version SemVer (X.Y.Z)
  - [ ] Side effects déclaré honnêtement
  - [ ] Idempotent déclaré correctement

- [ ] **Implémentation pure**
  - [ ] Fonction `execute(inputs) -> outputs`
  - [ ] Pas de try/catch
  - [ ] Pas d'effets de bord non déclarés
  - [ ] Pas d'appel à d'autres sous-programmes directement

- [ ] **Tests**
  - [ ] Couverture >= 80%
  - [ ] Test d'idempotence
  - [ ] Test d'absence d'effets de bord sur inputs
  - [ ] Tests de cas limites

- [ ] **Documentation**
  - [ ] Description claire dans le manifest
  - [ ] Docstring dans l'implémentation
  - [ ] Exemples d'utilisation

---

## 🎨 BONNES PRATIQUES

### Nommage

**Sous-programmes :**
- Format : `azalscore.category.action_target`
- Exemples :
  - ✅ `azalscore.finance.calculate_margin`
  - ✅ `azalscore.validation.validate_iban`
  - ❌ `azalscore.finance.margin` (trop vague)

**Workflows :**
- Format : `azalscore.module.action_description`
- Exemples :
  - ✅ `azalscore.finance.invoice_analysis`
  - ✅ `azalscore.commercial.validate_customer`

### Granularité

**Sous-programmes = atomiques**
- Une responsabilité unique
- Réutilisable dans 10+ contextes
- < 50 lignes de code

**Workflows = orchestration**
- Composition de sous-programmes
- Logique métier de haut niveau
- Pas de code, uniquement du DAG JSON

### Versioning

**SemVer strict :**
- MAJOR : Breaking change (inputs/outputs modifiés)
- MINOR : Nouvelle fonctionnalité (backward compatible)
- PATCH : Bug fix

**Exemples :**
- Ajout d'un output optionnel : MINOR (1.0.0 → 1.1.0)
- Suppression d'un input : MAJOR (1.1.0 → 2.0.0)
- Correction d'un bug de calcul : PATCH (1.1.0 → 1.1.1)

---

## 🔒 CONFORMITÉ AZALSCORE

### Principes respectés

✅ **AZA-NF-002 :** Noyau unique (non modifié)
✅ **AZA-NF-003 :** Modules subordonnés (registry + orchestration)
✅ **AZA-NF-004 :** Extension par ajout pur
✅ **AZA-NF-008 :** IA gouvernée (intégrable comme sous-programmes)
✅ **AZA-NF-009 :** Auditabilité permanente (ExecutionResult tracé)
✅ **Charte Développeur :** Code métier pur, réutilisable, No-Code compatible

### Règles d'or

> **"Le manifest est la vérité, pas le code"**

> **"Si ça ne peut pas être assemblé, ça ne doit pas être codé"**

> **"Si ça ne peut pas être réutilisé, ça ne doit pas exister"**

---

## 📞 SUPPORT

### Documentation

- `/registry/README.md` - Documentation complète du registry
- `/CONFORMITE_AZALSCORE.md` - Rapport de conformité détaillé
- Ce guide - Guide de démarrage

### Tests

- `/tests/test_registry.py` - Exemples d'utilisation du registry
- `/tests/test_orchestration.py` - Exemples de workflows DAG

### Exemples concrets

- `/registry/finance/calculate_margin/` - Sous-programme simple
- `/registry/validation/validate_iban/` - Sous-programme avec validation complexe
- `/app/modules/finance/workflows/invoice_analysis.json` - Workflow complet

---

## 🚀 PROCHAINES ÉTAPES

### Pour les développeurs

1. **Créer 20+ sous-programmes** - Enrichir le registry
2. **Transformer 5 modules en DAG** - Montrer l'exemple
3. **Purifier le code métier** - Éliminer les try/catch restants

### Pour le produit

4. **UI No-Code builder** - Interface visuelle d'assemblage
5. **Simulation de workflows** - Preview avant déploiement
6. **Marketplace de sous-programmes** - Partage entre tenants

### Pour la gouvernance

7. **Audit externe** - Certification ISO de conformité AZALSCORE
8. **Documentation utilisateur** - Guide pour les non-développeurs
9. **Formation interne** - Adoption du nouveau système

---

## ✅ VALIDATION

**Système opérationnel ✅**
- [x] Registry créé avec 5 sous-programmes
- [x] Loader fonctionnel et testé
- [x] Moteur d'orchestration opérationnel
- [x] API workflows exposée
- [x] 21 tests qui passent (100%)
- [x] Documentation complète
- [x] Conformité AZALSCORE 95%

**Le système est prêt pour la production.**

---

**Phrase clé :**

> **"De la saisie à la décision, AZALSCORE orchestre tout."**

---

**FIN DU GUIDE DE DÉMARRAGE**
