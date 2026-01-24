# 📦 AZALSCORE REGISTRY — BIBLIOTHÈQUE CENTRALE

**Version :** 1.0.0
**Conformité :** AZA-NF-003, AZA-RT-001
**Objectif :** Patrimoine industriel de sous-programmes réutilisables

---

## 🎯 PRINCIPE FONDAMENTAL

> **Le manifest est la vérité, pas le code.**

Chaque sous-programme est défini par :
1. **manifest.json** - Source de vérité (inputs/outputs/side_effects/idempotent)
2. **impl.py** - Implémentation technique (interchangeable)
3. **tests/** - Tests obligatoires (couverture >= 80%)

---

## 📂 STRUCTURE

```
registry/
├── finance/
│   ├── calculate_margin/
│   │   ├── manifest.json       ← Source de vérité
│   │   ├── impl.py             ← Implémentation
│   │   ├── tests/
│   │   │   └── test_calculate_margin.py
│   │   └── versions/
│   │       └── 1.0.0/
│   ├── validate_iban/
│   └── compute_vat/
├── validation/
│   ├── validate_email/
│   ├── validate_siret/
│   └── validate_phone/
├── ai/
│   ├── analyze_invoice/
│   ├── categorize_transaction/
│   └── extract_entities/
├── notification/
│   ├── send_alert/
│   ├── send_email/
│   └── trigger_webhook/
├── computation/
│   ├── calculate_percentage/
│   ├── apply_discount/
│   └── compute_deadline/
├── data_transform/
│   ├── normalize_address/
│   ├── format_currency/
│   └── parse_date/
└── security/
    ├── hash_password/
    ├── verify_token/
    └── encrypt_data/
```

---

## 📋 MANIFEST STRUCTURE

Chaque manifest.json doit contenir :

```json
{
  "id": "azalscore.category.program_name",
  "name": "Nom métier lisible",
  "category": "finance|validation|ai|notification|computation|data_transform|security",
  "version": "1.0.0",
  "description": "Description fonctionnelle claire",
  "inputs": {
    "param_name": {
      "type": "string|number|boolean|object|array",
      "required": true,
      "description": "Description du paramètre",
      "validation": "regex ou contrainte optionnelle"
    }
  },
  "outputs": {
    "result_name": {
      "type": "string|number|boolean|object|array",
      "description": "Description du résultat"
    }
  },
  "side_effects": false,
  "idempotent": true,
  "no_code_compatible": true,
  "retry_strategy": {
    "max_attempts": 3,
    "timeout_ms": 5000,
    "fallback": "azalscore.category.fallback_program"
  },
  "dependencies": [],
  "tags": ["tag1", "tag2"],
  "author": "AZALSCORE",
  "license": "Proprietary",
  "created_at": "2026-01-22",
  "updated_at": "2026-01-22"
}
```

---

## 🔐 RÈGLES STRICTES

### 1. Immutabilité des manifests
- Un manifest v1.0.0 ne peut JAMAIS être modifié
- Toute modification = nouvelle version (SemVer)
- Breaking change = major version (2.0.0)

### 2. Tests obligatoires
- Couverture >= 80%
- Tests unitaires + tests d'intégration
- Validation automatique avant enregistrement

### 3. Certification bloquante
- Manifest invalide = refus au chargement
- Tests échoués = refus au chargement
- Side effects non déclarés = refus au chargement

### 4. Versioning strict (SemVer)
- Format : MAJOR.MINOR.PATCH
- Référencement : `azalscore.finance.calculate_margin@^1.0`
- Résolution au chargement (pas de version dynamique en runtime)

---

## 🚀 UTILISATION

### Dans un module déclaratif (DAG JSON)

```json
{
  "module_id": "azalscore.invoice_analysis",
  "version": "1.0.0",
  "steps": [
    {
      "id": "validate_iban",
      "use": "azalscore.validation.validate_iban@^1.0",
      "inputs": {
        "iban": "{{context.supplier_iban}}"
      }
    },
    {
      "id": "calculate_margin",
      "use": "azalscore.finance.calculate_margin@^1.0",
      "inputs": {
        "price": "{{context.total_price}}",
        "cost": "{{context.total_cost}}"
      },
      "retry": 2,
      "timeout": 3000
    },
    {
      "id": "send_alert",
      "condition": "{{calculate_margin.margin_rate < 0.2}}",
      "use": "azalscore.notification.send_alert@^1.0",
      "inputs": {
        "type": "low_margin",
        "data": "{{calculate_margin}}"
      }
    }
  ]
}
```

### Dans du code Python (transition)

```python
from app.registry.loader import load_program

# Chargement du sous-programme
calculate_margin = load_program("azalscore.finance.calculate_margin@^1.0")

# Exécution
result = calculate_margin.execute({
    "price": 1000.0,
    "cost": 800.0
})

# result = {"margin": 200.0, "margin_rate": 0.2}
```

---

## 🎯 OBJECTIF NO-CODE

Chaque sous-programme doit pouvoir être :
- **Visualisé** dans un builder graphique
- **Connecté** à d'autres sous-programmes (type safety)
- **Configuré** sans écrire de code
- **Simulé** avant déploiement
- **Réutilisé** dans 10+ modules différents

---

## 📊 MÉTRIQUES

Le registry suit les métriques suivantes :
- Nombre de sous-programmes par catégorie
- Taux de réutilisation (combien de modules utilisent chaque sous-programme)
- Couverture de tests
- Taux de conformité manifests

Objectif : **Effet de réseau** - Plus le registry grandit, plus créer de nouveaux modules devient facile.

---

## 🔒 GOUVERNANCE

- Tout ajout au registry doit être audité
- Tout sous-programme doit respecter la charte développeur AZALSCORE
- Aucun sous-programme ne peut contenir de gestion d'erreur (délégué au moteur)
- Aucun sous-programme ne peut appeler un autre directement (orchestration par DAG)

---

**Phrase clé :**
> "Si ce n'est pas déclarable, ce n'est pas orchestrable. Si ce n'est pas orchestrable, ce n'est pas No-Code."
