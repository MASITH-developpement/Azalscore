# AZALSCORE - SCOPE_LOCK.md
## GEL DU PÉRIMÈTRE - Version Bêta Fermée

**Date de gel**: 2026-01-08
**Version**: 1.0-BETA
**Responsable**: Architecture Production

---

## PRINCIPE DIRECTEUR ABSOLU

> **AUCUNE NOUVELLE FONCTIONNALITÉ N'EST AUTORISÉE EN DEHORS DE CE PÉRIMÈTRE**
>
> Toute demande de nouvelle feature doit être :
> 1. Documentée dans FEATURE_REQUESTS.md
> 2. Évaluée après la sortie de la version stable
> 3. Approuvée par le responsable produit

---

## PÉRIMÈTRE BÊTA FERMÉ - GELÉ

### MODULE ACTIF : SOCLE TECHNIQUE (T0-CORE)

Le SEUL module autorisé pour implémentation/activation en bêta :

| Composant | Statut | Priorité |
|-----------|--------|----------|
| Authentification JWT | ACTIF | CRITIQUE |
| Multi-tenant strict | ACTIF | CRITIQUE |
| RBAC (5 rôles) | ACTIF | CRITIQUE |
| 2FA TOTP | ACTIF | HAUTE |
| Audit Journal (append-only) | ACTIF | CRITIQUE |
| Rate Limiting | ACTIF | HAUTE |
| Health Checks | ACTIF | HAUTE |
| Configuration sécurisée | ACTIF | CRITIQUE |

### MODULES MÉTIER - ÉTAT GELÉ

Tous les modules métier sont **PRÉPARÉS** mais **NON ACTIVÉS** :

| Module | Code | Lignes Service | État |
|--------|------|----------------|------|
| IAM | T0 | 1498 | PRÉPARÉ - Non activé |
| AutoConfig | T1 | 851 | PRÉPARÉ - Non activé |
| Triggers | T2 | 922 | PRÉPARÉ - Non activé |
| Audit | T3 | 1137 | PRÉPARÉ - Non activé |
| QC | T4 | 1164 | PRÉPARÉ - Non activé |
| Country Packs | T5 | 801 | PRÉPARÉ - Non activé |
| Broadcast | T6 | 918 | PRÉPARÉ - Non activé |
| Web | T7 | 745 | PRÉPARÉ - Non activé |
| Website | T8 | 1061 | PRÉPARÉ - Non activé |
| Tenants | T9 | 724 | PRÉPARÉ - Non activé |
| Commercial/CRM | M1 | 988 | PRÉPARÉ - Non activé |
| Finance | M2 | 1208 | PRÉPARÉ - Non activé |
| HR | M3 | 1089 | PRÉPARÉ - Non activé |
| Procurement | M4 | 931 | PRÉPARÉ - Non activé |
| Inventory | M5 | 1206 | PRÉPARÉ - Non activé |
| Production | M6 | 1047 | PRÉPARÉ - Non activé |
| Quality | M7 | 1714 | PRÉPARÉ - Non activé |
| Maintenance | M8 | 1033 | PRÉPARÉ - Non activé |
| Projects | M9 | 1453 | PRÉPARÉ - Non activé |
| BI | M10 | 1247 | PRÉPARÉ - Non activé |
| Compliance | M11 | 1140 | PRÉPARÉ - Non activé |
| E-Commerce | M12 | 1539 | PRÉPARÉ - Non activé |
| POS | M13 | 1419 | PRÉPARÉ - Non activé |
| Subscriptions | M14 | 1390 | PRÉPARÉ - Non activé |
| Stripe | M15 | 1019 | PRÉPARÉ - Non activé |
| Helpdesk | M16 | 1475 | PRÉPARÉ - Non activé |
| Field Service | M17 | 1260 | PRÉPARÉ - Non activé |
| Mobile | M18 | 739 | PRÉPARÉ - Non activé |
| AI Assistant | - | 1075 | PRÉPARÉ - Non activé |
| Guardian | - | 1396 | PRÉPARÉ - Non activé |

---

## CLASSIFICATION DES FONCTIONNALITÉS

### 🟢 FONCTIONNEL (Code complet + Tests)

| Fonctionnalité | Fichier Principal | Preuves |
|---------------|-------------------|---------|
| JWT Authentication | `app/core/security.py` | Tests: test_auth.py |
| Password Hashing (bcrypt) | `app/core/security.py` | Limite 72 bytes respectée |
| Multi-tenant Middleware | `app/core/middleware.py` | Validation X-Tenant-ID |
| Dépendances FastAPI | `app/core/dependencies.py` | Triple validation tenant |
| 2FA TOTP | `app/core/two_factor.py` | 303 lignes, codes backup |
| RBAC Matrix | `app/modules/iam/rbac_matrix.py` | 819 lignes, 5 rôles |
| Audit Journal SQL Triggers | `migrations/003_journal.sql` | UPDATE/DELETE bloqués |
| Configuration Validation | `app/core/config.py` | Secrets obligatoires prod |
| Health Checks K8s | `app/core/health.py` | /health, /health/db |

### 🟠 PARTIEL (Code présent, tests insuffisants)

| Fonctionnalité | Problème | Action Requise |
|---------------|----------|----------------|
| Rate Limiting | Code présent mais Redis optionnel | Tester avec Redis |
| RBAC Middleware | Matrice OK, application variable | Auditer tous les endpoints |
| Session Management | JWT stateless, pas de révocation | Implémenter blacklist |
| Metrics Prometheus | Code présent | Valider dashboard Grafana |

### 🔴 NON IMPLÉMENTÉ (CRITIQUE)

| Fonctionnalité | Impact | Priorité |
|---------------|--------|----------|
| **Chiffrement AES-256 au repos** | Données sensibles en clair | BLOQUANT |
| **Rotation de clés** | Risque si clé compromise | HAUTE |
| **Hash chaîné journal audit** | Intégrité non prouvable | HAUTE |
| **Test injection SQL** | Vulnérabilité potentielle | HAUTE |
| **Test élévation privilèges** | Faille sécurité | HAUTE |
| **Test accès inter-tenant** | Fuite données | BLOQUANT |

---

## RÈGLES DE GEL (NON NÉGOCIABLES)

### 1. INTERDIT

- ❌ Ajouter de nouvelles features
- ❌ Modifier l'architecture core
- ❌ Activer un nouveau module métier
- ❌ Changer les schémas DB en production
- ❌ Modifier la matrice RBAC sans audit
- ❌ Supprimer des validations de sécurité

### 2. AUTORISÉ

- ✅ Corriger des bugs de sécurité
- ✅ Ajouter des tests manquants
- ✅ Améliorer la documentation
- ✅ Corriger des erreurs de typage
- ✅ Optimiser les performances (sans changement fonctionnel)
- ✅ Renforcer la validation des entrées

### 3. REQUIERT APPROBATION

- ⚠️ Mise à jour des dépendances
- ⚠️ Modification des migrations
- ⚠️ Changement de configuration production
- ⚠️ Ajout d'endpoints API

---

## SÉQUENCE D'ACTIVATION DES MODULES

```
PHASE ACTUELLE: SOCLE TECHNIQUE
       ↓
[PASS] → IAM (T0)
       ↓
[PASS] → Commercial (M1)
       ↓
[PASS] → Finance (M2)
       ↓
[PASS] → Autres modules...
```

**RÈGLE STRICTE**: Un module suivant ne peut être activé que si :
1. Le module précédent a passé 100% des critères de validation
2. Un rapport PASS a été généré
3. Les tests d'intégration sont OK
4. La documentation est à jour

---

## CRITÈRES DE VALIDATION SOCLE TECHNIQUE

Pour passer à l'activation du module IAM (T0), le socle doit valider :

| Critère | Statut | Commentaire |
|---------|--------|-------------|
| Auth JWT fonctionnel | ✅ PASS | Code et tests présents |
| Multi-tenant isolation | ⚠️ À TESTER | Tests inter-tenant requis |
| 2FA opérationnel | ✅ PASS | TOTP + backup codes |
| Audit append-only | ✅ PASS | Triggers SQL |
| Config sécurisée | ✅ PASS | Validation stricte |
| Rate limiting | ⚠️ PARTIEL | Tester avec charge |
| AES-256 au repos | ❌ FAIL | Non implémenté |
| Tests sécurité | ❌ FAIL | Injection, XSS, etc. |
| Documentation | ⚠️ PARTIEL | À compléter |

---

## SIGNATURES

| Rôle | Nom | Date | Signature |
|------|-----|------|-----------|
| Responsable Technique | [À REMPLIR] | 2026-01-08 | __________ |
| Responsable Sécurité | [À REMPLIR] | 2026-01-08 | __________ |
| Responsable Produit | [À REMPLIR] | 2026-01-08 | __________ |

---

## HISTORIQUE DES MODIFICATIONS

| Date | Auteur | Modification |
|------|--------|--------------|
| 2026-01-08 | Système | Création initiale - Gel du périmètre |

---

**⚠️ AVERTISSEMENT**: Ce document est CONTRAIGNANT. Toute violation du gel de périmètre doit être documentée et justifiée par écrit avec approbation du responsable produit.
