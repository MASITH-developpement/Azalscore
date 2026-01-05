# CHARTE ÉVOLUTION ET COMPATIBILITÉ AZALSCORE
## Versioning, Migrations et Pérennité

**Version:** 1.0.0
**Statut:** DOCUMENT NORMATIF
**Date:** 2026-01-05
**Classification:** PUBLIC - OPPOSABLE
**Référence:** AZALS-GOV-13-v1.0.0

---

## 1. OBJECTIF

Cette charte définit les règles de versioning, de gestion des évolutions, de compatibilité, et de cycle de vie des versions AZALSCORE.

---

## 2. PÉRIMÈTRE

- Versioning du système et des modules
- Gestion des breaking changes
- Compatibilité ascendante
- Processus de migration
- Cycle de vie des versions (LTS, EOL)

---

## 3. VERSIONING

### 3.1 Schéma Sémantique

```
AZALSCORE X.Y.Z

X = Version MAJEURE
    - Breaking changes
    - Incompatibilités
    - Refonte architecturale

Y = Version MINEURE
    - Nouvelles fonctionnalités
    - Rétrocompatible
    - Ajouts sans casse

Z = Version PATCH
    - Corrections de bugs
    - Corrections de sécurité
    - Aucun changement fonctionnel
```

### 3.2 Exemples

| Version | Type | Description |
|---------|------|-------------|
| 7.0.0 → 8.0.0 | Majeure | Breaking change API |
| 7.0.0 → 7.1.0 | Mineure | Nouveau module ajouté |
| 7.0.0 → 7.0.1 | Patch | Bug fix sécurité |

### 3.3 Versioning des Modules

```
Module: module_name vX.Y.Z

Indépendant du versioning système mais avec:
- Compatibilité AZALSCORE minimum déclarée
- Changelog propre
- Cycle de vie propre
```

---

## 4. COMPATIBILITÉ

### 4.1 Compatibilité Ascendante

```
RÈGLE: Les versions mineures et patches sont rétrocompatibles.

Une mise à jour mineure ou patch:
✅ Ne casse pas les API existantes
✅ Ne supprime pas de fonctionnalités
✅ Ne modifie pas les signatures de fonctions
✅ Ne change pas les schémas de données
```

### 4.2 Breaking Changes

```
RÈGLE: Les breaking changes sont réservés aux versions majeures.

Un breaking change:
- Modifie une API existante
- Supprime une fonctionnalité
- Change un schéma de données
- Modifie un comportement établi
```

### 4.3 Matrice de Compatibilité

| De → Vers | Majeure | Mineure | Patch |
|-----------|---------|---------|-------|
| Breaking changes | ✅ Autorisé | ❌ Interdit | ❌ Interdit |
| Nouvelles features | ✅ | ✅ | ❌ |
| Bug fixes | ✅ | ✅ | ✅ |
| Migration requise | Oui | Non | Non |

---

## 5. DÉPRÉCIATION

### 5.1 Processus de Dépréciation

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: ANNONCE (Version N)                                │
│  - Fonctionnalité marquée "deprecated"                      │
│  - Warning dans les logs                                    │
│  - Documentation mise à jour                                │
│  - Alternative documentée                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Minimum 2 versions mineures
                              │ ou 6 mois
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: DÉPRÉCIATION ACTIVE (Version N+1)                  │
│  - Warnings plus visibles                                   │
│  - Emails aux utilisateurs concernés                        │
│  - Guide de migration fourni                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Version majeure suivante
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: SUPPRESSION (Version N+2 majeure)                  │
│  - Fonctionnalité supprimée                                 │
│  - Breaking change documenté                                │
│  - Support de migration disponible                          │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Délais Minimum

| Type | Délai avant suppression |
|------|------------------------|
| API publique | 12 mois ou 2 majeures |
| Fonctionnalité UI | 6 mois |
| Paramètre configuration | 6 mois |
| Module entier | 12 mois |

### 5.3 Marquage Dépréciation

```python
# Code
@deprecated(version="7.2.0", removal="8.0.0", alternative="new_function")
def old_function():
    pass

# Documentation
> **DEPRECATED** depuis v7.2.0
> Sera supprimé en v8.0.0
> Utilisez `new_function()` à la place.

# Log
WARNING: old_function is deprecated since v7.2.0 and will be removed in v8.0.0. Use new_function instead.
```

---

## 6. MIGRATIONS

### 6.1 Types de Migration

| Type | Automatique | Intervention |
|------|-------------|--------------|
| Schema DB (ajout) | Oui | Non |
| Schema DB (modification) | Partielle | Validation |
| Schema DB (suppression) | Non | Obligatoire |
| Configuration | Oui | Non |
| Données | Partielle | Validation |

### 6.2 Processus de Migration

```
┌─────────────────────────────────────────────────────────────┐
│  1. PRÉPARATION                                              │
│     - Backup complet                                        │
│     - Test en environnement staging                         │
│     - Rollback plan documenté                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. VALIDATION                                               │
│     - Tests de migration passants                           │
│     - Performance acceptable                                │
│     - Données intègres                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. EXÉCUTION                                                │
│     - Fenêtre de maintenance                                │
│     - Migration appliquée                                   │
│     - Vérification post-migration                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. VALIDATION FINALE                                        │
│     - Tests fonctionnels                                    │
│     - Monitoring renforcé                                   │
│     - Communication aux utilisateurs                        │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Scripts de Migration

```python
# Structure standard
migrations/
├── 001_initial_schema.py
├── 002_add_user_fields.py
├── 003_create_invoices_table.py
└── ...

# Format
class Migration:
    version = "001"
    description = "Initial schema"

    def up(self):
        """Appliquer la migration"""
        pass

    def down(self):
        """Annuler la migration (rollback)"""
        pass
```

---

## 7. CYCLE DE VIE DES VERSIONS

### 7.1 Types de Release

| Type | Support | Durée |
|------|---------|-------|
| **LTS** (Long Term Support) | Complet | 3 ans |
| **Standard** | Complet | 1 an |
| **EOL** (End of Life) | Aucun | - |

### 7.2 Calendrier Type

```
Exemple pour AZALSCORE 7.x:

2024-01: v7.0.0 (LTS) - Release
2024-07: v7.1.0 - Mineure
2025-01: v7.2.0 - Mineure
2025-07: v8.0.0 - Nouvelle majeure
2026-01: v7.x → Support étendu
2027-01: v7.x → EOL
```

### 7.3 Politique de Support

| Phase | Durée | Inclus |
|-------|-------|--------|
| Support Actif | 18 mois | Bugs, sécurité, features |
| Support Étendu | 12 mois | Sécurité uniquement |
| EOL | - | Aucun support |

---

## 8. COMMUNICATION

### 8.1 Changelog

```markdown
# Changelog AZALSCORE

## [7.1.0] - 2026-01-15

### Added
- Module E-commerce (ecommerce/)
- Prédictions IA trésorerie

### Changed
- Amélioration performance requêtes finance

### Deprecated
- Fonction old_api_endpoint() (suppression v8.0.0)

### Fixed
- Bug #1234: Erreur calcul TVA

### Security
- CVE-2026-XXXX: Correction faille XSS
```

### 8.2 Release Notes

Publiées pour chaque version avec :
- Nouvelles fonctionnalités
- Corrections de bugs
- Changements de comportement
- Instructions de migration
- Dépréciations

### 8.3 Notifications

| Événement | Canal | Délai |
|-----------|-------|-------|
| Nouvelle version | Email + In-app | J |
| Dépréciation | Email | J-90 |
| EOL annoncé | Email | J-180 |
| Patch sécurité | Email urgent | J |

---

## 9. ENVIRONNEMENTS

### 9.1 Progression des Releases

```
Development → Staging → Production

- Development: dernière version, instable
- Staging: version candidate, tests
- Production: version stable validée
```

### 9.2 Politique de Mise à Jour

| Type | Staging | Production |
|------|---------|------------|
| Patch sécurité | Immédiat | < 24h |
| Patch bug | < 24h | < 72h |
| Mineure | < 1 semaine | < 2 semaines |
| Majeure | < 2 semaines | Planifié |

---

## 10. ROLLBACK

### 10.1 Capacité de Rollback

```
RÈGLE: Tout déploiement doit être réversible.

Prérequis:
- Backup avant migration
- Scripts de rollback testés
- Procédure documentée
- Décision en < 1h si problème
```

### 10.2 Procédure de Rollback

```
1. DÉCISION
   - Incident critique détecté
   - Validation responsable

2. COMMUNICATION
   - Notification équipe
   - Information utilisateurs

3. EXÉCUTION
   - Restauration version précédente
   - Rollback base de données si nécessaire

4. VÉRIFICATION
   - Tests fonctionnels
   - Confirmation stabilité

5. POST-MORTEM
   - Analyse de l'incident
   - Actions correctives
```

---

## 11. INTERDICTIONS

- ❌ Breaking change en version mineure ou patch
- ❌ Suppression sans période de dépréciation
- ❌ Migration sans backup préalable
- ❌ Déploiement production sans passage staging
- ❌ EOL sans préavis de 6 mois minimum

---

## 12. CONSÉQUENCES DU NON-RESPECT

| Violation | Conséquence |
|-----------|-------------|
| Breaking change non signalé | Revert immédiat |
| Suppression sans dépréciation | Restauration + communication |
| Migration sans backup | Incident de gouvernance |

---

*Document généré et validé le 2026-01-05*
*Classification: PUBLIC - OPPOSABLE*
*Référence: AZALS-GOV-13-v1.0.0*

**ÉVOLUER SANS CASSER.**
