# CHARTE CORE AZALSCORE
## Protection du Noyau Système - Document Sacré

**Version:** 1.0.0
**Statut:** DOCUMENT CRITIQUE - SACRÉ
**Date:** 2026-01-05
**Classification:** CONFIDENTIEL - OPPOSABLE
**Référence:** AZALS-GOV-01-v1.0.0

---

## 1. OBJECTIF

Cette charte définit le **Core AZALSCORE** : son périmètre exact, ses règles de protection absolue, et les procédures exceptionnelles permettant sa modification.

**RÈGLE FONDAMENTALE:**
```
LE CORE EST SACRÉ ET INTOUCHABLE.
AUCUNE MODIFICATION N'EST AUTORISÉE SANS PROCÉDURE EXCEPTIONNELLE VALIDÉE.
```

---

## 2. PÉRIMÈTRE

### 2.1 Applicabilité
Cette charte s'applique à :
- Tout fichier situé dans le périmètre Core
- Tout développeur (humain ou IA)
- Tout processus de CI/CD
- Toute opération de maintenance

### 2.2 Hiérarchie
Cette charte est subordonnée uniquement à `00_charte_generale_azalscore.md` et prévaut sur toutes les autres chartes.

---

## 3. DÉFINITION DU CORE

### 3.1 Composants du Core

Le Core AZALSCORE comprend **exclusivement** les éléments suivants :

```
app/core/
├── __init__.py          # Initialisation Core
├── config.py            # Configuration système
├── database.py          # Connexion et engine DB
├── models.py            # Modèles fondamentaux
├── types.py             # Types universels
├── security.py          # Authentification JWT
├── middleware.py        # Middleware tenant/sécurité
├── dependencies.py      # Injections de dépendances
├── security_middleware.py # Rate limiting, headers
└── audit.py             # Journalisation système
```

### 3.2 Fonctions Core Protégées

| Fonction | Fichier | Criticité |
|----------|---------|-----------|
| Authentification JWT | `security.py` | MAXIMALE |
| Validation Tenant | `middleware.py` | MAXIMALE |
| Connexion DB | `database.py` | MAXIMALE |
| Configuration | `config.py` | HAUTE |
| Modèles Base | `models.py` | HAUTE |
| Audit Journal | `audit.py` | HAUTE |
| Types Universels | `types.py` | MOYENNE |
| Dépendances | `dependencies.py` | MOYENNE |

### 3.3 APIs Core Protégées

```
/auth/*           # Authentification
/health           # Health check
/metrics          # Métriques système
/items/*          # CRUD de base (exemple)
```

---

## 4. PRINCIPES FONDAMENTAUX

### 4.1 Indépendance Absolue
```
RÈGLE: Le Core ne dépend d'AUCUN module.

Le Core doit pouvoir fonctionner de manière autonome,
sans qu'aucun module métier ne soit installé.

Imports autorisés dans le Core:
✅ Bibliothèques Python standard
✅ Dépendances tierces (FastAPI, SQLAlchemy, etc.)
✅ Autres fichiers du Core

Imports INTERDITS dans le Core:
❌ app/modules/*
❌ app/api/* (sauf exceptions documentées)
❌ Tout code métier
```

### 4.2 Dépendance Unidirectionnelle
```
RÈGLE: Les modules dépendent du Core, JAMAIS l'inverse.

         ┌─────────────┐
         │    CORE     │ ← Indépendant
         └──────┬──────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌───────┐  ┌───────┐  ┌───────┐
│Module │  │Module │  │Module │ ← Dépendent du Core
│   A   │  │   B   │  │   C   │
└───────┘  └───────┘  └───────┘
```

### 4.3 Stabilité Contractuelle
```
RÈGLE: Les interfaces du Core sont des contrats stables.

- Les signatures de fonctions Core ne changent pas
- Les schémas de données Core sont versionnés
- Les breaking changes suivent un cycle de dépréciation
```

---

## 5. RÈGLES DE PROTECTION

### 5.1 Interdiction de Modification Directe

**INTERDICTION ABSOLUE** de :
- Modifier un fichier Core sans procédure
- Ajouter des dépendances vers les modules
- Changer les signatures des fonctions exposées
- Modifier les schémas de données Core
- Désactiver les mécanismes de sécurité
- Contourner la validation tenant

### 5.2 Actions Interdites par Composant

| Composant | Actions Interdites |
|-----------|-------------------|
| `security.py` | Modifier l'algorithme JWT, réduire l'expiration, désactiver la validation |
| `middleware.py` | Bypasser la validation tenant, ajouter des exceptions non documentées |
| `database.py` | Modifier l'engine, changer la stratégie de connexion |
| `config.py` | Supprimer des validations, accepter des valeurs dangereuses |
| `models.py` | Supprimer des champs obligatoires, modifier TenantMixin |
| `audit.py` | Désactiver la journalisation, permettre la modification des logs |

### 5.3 Surveillance Automatique

```python
# Contrôles automatiques sur le Core
CORE_PROTECTION_RULES = {
    "no_module_imports": True,      # Aucun import depuis modules/
    "signature_stability": True,     # Signatures fonctions inchangées
    "security_tests": True,          # Tests sécurité obligatoires
    "audit_enabled": True,           # Audit toujours actif
    "tenant_validation": True,       # Validation tenant obligatoire
}
```

---

## 6. PROCÉDURE DE MODIFICATION EXCEPTIONNELLE

### 6.1 Conditions Préalables

Une modification du Core n'est envisageable QUE si :

1. **Criticité avérée** : Bug de sécurité, faille critique, ou impossibilité technique
2. **Absence d'alternative** : Aucune solution hors Core n'est viable
3. **Impact minimal** : La modification est la plus petite possible
4. **Réversibilité** : Un rollback est possible

### 6.2 Processus Obligatoire

```
ÉTAPE 1: DEMANDE EXPOSÉE
─────────────────────────
- Document écrit détaillant :
  • Problème rencontré
  • Justification de la modification Core
  • Alternatives envisagées et rejetées
  • Impact sur le système
  • Plan de tests
  • Plan de rollback

ÉTAPE 2: VALIDATION GOUVERNANCE
───────────────────────────────
- Revue par au moins 2 responsables
- Validation écrite et datée
- Délai minimum de réflexion : 24h

ÉTAPE 3: IMPLÉMENTATION CONTRÔLÉE
─────────────────────────────────
- Branche dédiée (core/fix-xxx)
- Tests exhaustifs obligatoires
- Revue de code par expert sécurité
- Documentation mise à jour

ÉTAPE 4: DÉPLOIEMENT GRADUEL
────────────────────────────
- Environnement de staging d'abord
- Période d'observation : 48h minimum
- Monitoring renforcé
- Rollback prêt

ÉTAPE 5: CLÔTURE ET TRAÇABILITÉ
───────────────────────────────
- Rapport post-modification
- Mise à jour du changelog Core
- Archivage de la demande
- Communication aux parties prenantes
```

### 6.3 Template de Demande

```markdown
# DEMANDE DE MODIFICATION CORE

**Date:** YYYY-MM-DD
**Demandeur:** [Nom/Équipe]
**Criticité:** [CRITIQUE/HAUTE/MOYENNE]

## Problème
[Description détaillée du problème]

## Fichier(s) Core concerné(s)
- [ ] app/core/xxx.py

## Modification proposée
[Description technique précise]

## Justification
[Pourquoi le Core doit être modifié]

## Alternatives rejetées
1. [Alternative 1] - Raison du rejet
2. [Alternative 2] - Raison du rejet

## Impact
- Sécurité: [OUI/NON] - Détails
- Performance: [OUI/NON] - Détails
- Compatibilité: [OUI/NON] - Détails

## Plan de tests
[Liste des tests à exécuter]

## Plan de rollback
[Procédure de retour arrière]

## Validations
- [ ] Responsable 1: _______ Date: _______
- [ ] Responsable 2: _______ Date: _______
```

---

## 7. VERSIONING DU CORE

### 7.1 Schéma de Version
```
CORE-X.Y.Z

X = Version majeure (breaking changes)
Y = Version mineure (nouvelles fonctionnalités compatibles)
Z = Patch (corrections de bugs)
```

### 7.2 Règles de Versioning

| Type de modification | Incrémentation |
|---------------------|----------------|
| Correction de bug sécurité | Z (patch) |
| Nouvelle fonction (rétrocompatible) | Y (mineure) |
| Changement de signature | X (majeure) |
| Suppression de fonction | X (majeure) |

### 7.3 Historique Obligatoire

Tout changement Core est documenté dans :
```
/governance/CORE_CHANGELOG.md
```

---

## 8. TESTS OBLIGATOIRES DU CORE

### 8.1 Couverture Minimale
```
Couverture de code Core : 90% minimum
Tests de sécurité : 100% des fonctions critiques
Tests d'intégration : Tous les endpoints Core
```

### 8.2 Tests Automatiques CI/CD

```yaml
# Vérifications automatiques sur chaque PR touchant le Core
core_protection:
  - no_module_imports      # Vérifie l'absence d'imports modules
  - signature_unchanged    # Vérifie la stabilité des signatures
  - security_tests_pass    # Tests de sécurité passent
  - coverage_90_percent    # Couverture ≥ 90%
  - audit_enabled          # Audit non désactivé
```

---

## 9. INTERDICTIONS ABSOLUES

### 9.1 Modifications Interdites Sans Exception

| Action | Raison |
|--------|--------|
| Supprimer `TenantMixin` | Casse l'isolation multi-tenant |
| Désactiver JWT validation | Faille de sécurité critique |
| Importer depuis `app/modules/` | Viole l'indépendance Core |
| Modifier `SECRET_KEY` validation | Risque de secrets faibles |
| Supprimer audit logging | Perte de traçabilité |
| Réduire JWT expiration < 5min | Dégradation UX injustifiée |

### 9.2 Patterns Interdits dans le Core

```python
# ❌ INTERDIT - Import de module
from app.modules.finance import something

# ❌ INTERDIT - Logique métier
def calculate_invoice_total():
    pass

# ❌ INTERDIT - Dépendance conditionnelle à un module
if module_finance_installed:
    do_something()

# ❌ INTERDIT - Hardcoded secrets
SECRET_KEY = "my-secret-key"

# ❌ INTERDIT - Désactivation sécurité
SKIP_AUTH = True
```

---

## 10. CONSÉQUENCES DU NON-RESPECT

### 10.1 Pour le Code
- **Rejet automatique** de tout commit modifiant le Core sans procédure
- **Revert immédiat** si modification non autorisée détectée
- **Audit de sécurité** obligatoire post-incident

### 10.2 Pour les Contributeurs
- **Avertissement** documenté pour première infraction
- **Restriction d'accès** au Core pour récidive
- **Exclusion** du projet pour violation grave

### 10.3 Pour le Système
- **Incident de sécurité** déclaré
- **Gel des déploiements** jusqu'à résolution
- **Communication** aux utilisateurs si impact

---

## 11. ANNEXES

### 11.1 Liste des Fichiers Core (Exhaustive)

```
app/core/
├── __init__.py              [PROTÉGÉ]
├── config.py                [CRITIQUE]
├── database.py              [CRITIQUE]
├── models.py                [CRITIQUE]
├── types.py                 [PROTÉGÉ]
├── security.py              [CRITIQUE]
├── middleware.py            [CRITIQUE]
├── dependencies.py          [PROTÉGÉ]
├── security_middleware.py   [CRITIQUE]
└── audit.py                 [CRITIQUE]
```

### 11.2 Contacts Gouvernance Core

Pour toute question relative au Core :
- Canal : #azalscore-core-governance
- Email : core-governance@azalscore.io

---

## 12. ENGAGEMENT

En contribuant au projet AZALSCORE, tout développeur (humain ou IA) s'engage à :

1. **Respecter** l'intégrité du Core
2. **Suivre** la procédure de modification exceptionnelle
3. **Signaler** toute tentative de contournement
4. **Maintenir** l'indépendance Core/Modules

---

*Document généré et validé le 2026-01-05*
*Classification: CONFIDENTIEL - OPPOSABLE*
*Référence: AZALS-GOV-01-v1.0.0*

**LE CORE EST SACRÉ. LE CORE EST INTOUCHABLE.**
