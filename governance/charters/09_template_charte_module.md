# TEMPLATE CHARTE MODULE AZALSCORE
## GOVERNANCE.md - Structure Obligatoire

**Version:** 1.0.0
**Statut:** TEMPLATE OFFICIEL
**Date:** 2026-01-05
**Classification:** PUBLIC - OBLIGATOIRE
**Référence:** AZALS-GOV-09-v1.0.0

---

## INSTRUCTIONS

Ce template définit la structure obligatoire du fichier `GOVERNANCE.md` que **chaque module AZALSCORE doit contenir**.

Un module sans ce fichier ne peut pas être mergé dans le projet.

---

## TEMPLATE À COPIER

```markdown
# GOVERNANCE - Module {NOM_MODULE}

**Version:** X.Y.Z
**Date:** YYYY-MM-DD
**Responsable:** {Équipe/Personne}
**Statut:** DRAFT | ACTIVE | DEPRECATED | REMOVED

---

## 1. IDENTITÉ

| Attribut | Valeur |
|----------|--------|
| Nom technique | `{nom_module}` |
| Chemin | `app/modules/{nom_module}/` |
| Version | X.Y.Z |
| Date création | YYYY-MM-DD |
| Dernière modification | YYYY-MM-DD |

---

## 2. OBJECTIF

{Description claire et concise de l'objectif du module en 2-3 phrases.}

**Mission:** {Une phrase définissant la mission principale}

---

## 3. PÉRIMÈTRE

### 3.1 Fonctionnalités Incluses

- {Fonctionnalité 1}
- {Fonctionnalité 2}
- {Fonctionnalité 3}

### 3.2 Fonctionnalités Explicitement Exclues

- {Ce que le module ne fait PAS 1}
- {Ce que le module ne fait PAS 2}

### 3.3 Limites

- {Limite technique ou fonctionnelle 1}
- {Limite technique ou fonctionnelle 2}

---

## 4. DONNÉES

### 4.1 Entités Gérées

| Entité | Table | Description |
|--------|-------|-------------|
| {Entité1} | `{table_name}` | {Description} |
| {Entité2} | `{table_name}` | {Description} |

### 4.2 Données Sensibles

| Donnée | Niveau | Traitement |
|--------|--------|------------|
| {Donnée1} | {HAUTE/MOYENNE/BASSE} | {Chiffrement, anonymisation...} |

### 4.3 Rétention

| Type de donnée | Durée | Action fin de vie |
|----------------|-------|-------------------|
| {Type1} | {Durée} | {Archivage/Suppression} |

---

## 5. APIs EXPOSÉES

### 5.1 Endpoints

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| GET | `/{module}/` | Liste des {entités} | JWT |
| POST | `/{module}/` | Créer {entité} | JWT |
| GET | `/{module}/{id}` | Détail {entité} | JWT |
| PUT | `/{module}/{id}` | Modifier {entité} | JWT |
| DELETE | `/{module}/{id}` | Supprimer {entité} | JWT |

### 5.2 Schémas

Référence OpenAPI: `/docs#{module}`

---

## 6. DÉPENDANCES

### 6.1 Dépendances Autorisées

| Dépendance | Type | Raison |
|------------|------|--------|
| Core | Obligatoire | Auth, DB, Models |
| {Lib externe} | Optionnelle | {Raison} |

### 6.2 Dépendances Interdites

| Interdit | Raison |
|----------|--------|
| Autres modules | Isolation module |
| Accès DB direct | Sécurité |

---

## 7. SÉCURITÉ

### 7.1 Permissions Requises

| Action | Permission | Rôle minimum |
|--------|------------|--------------|
| Lecture | `{module}.read` | USER |
| Création | `{module}.create` | USER |
| Modification | `{module}.update` | MANAGER |
| Suppression | `{module}.delete` | ADMIN |

### 7.2 Règles Spécifiques

- {Règle sécurité 1}
- {Règle sécurité 2}

### 7.3 Données Tenant

```
ISOLATION: Toutes les données sont filtrées par tenant_id.
AUCUN accès cross-tenant possible.
```

---

## 8. INTELLIGENCE ARTIFICIELLE

### 8.1 IA Autorisée

| Aspect | Valeur |
|--------|--------|
| IA activée | OUI / NON |
| Type | Prédiction / Suggestion / Analyse |
| Module IA | `ai_assistant` |

### 8.2 Rôle de l'IA

{Description du rôle de l'IA dans ce module}

### 8.3 Limites IA

- {Limite 1: ce que l'IA ne peut PAS faire}
- {Limite 2}

### 8.4 Données Accessibles à l'IA

| Donnée | Accès |
|--------|-------|
| {Donnée1} | Lecture |
| {Donnée2} | Interdit |

---

## 9. ACTIONS CRITIQUES

### 9.1 Actions Nécessitant Validation

| Action | Niveau | Validateur |
|--------|--------|------------|
| {Action1} | L2 | Manager |
| {Action2} | L3 | Dirigeant |

### 9.2 Déclencheurs RED

| Condition | Action |
|-----------|--------|
| {Condition1} | Alerte RED |
| {Condition2} | Alerte ORANGE |

---

## 10. INSTALLATION / DÉSINSTALLATION

### 10.1 Installation

```python
# app/main.py
from app.modules.{nom_module}.router import router as {module}_router
app.include_router({module}_router)
```

### 10.2 Désinstallation

**Impact:**
- {Impact 1}
- {Impact 2}

**Données:**
- {Ce qui advient des données}

**Procédure:**
1. {Étape 1}
2. {Étape 2}
3. {Étape 3}

---

## 11. COMPATIBILITÉ

### 11.1 Version AZALSCORE

| Version Module | Version AZALSCORE Min | Max |
|----------------|----------------------|-----|
| 1.x | 7.0.0 | - |

### 11.2 Changelog

| Version | Date | Changements |
|---------|------|-------------|
| 1.0.0 | YYYY-MM-DD | Version initiale |

---

## 12. CONFORMITÉ CHARTES

### 12.1 Chartes Applicables

- [x] 00_charte_generale_azalscore.md
- [x] 01_charte_core_azalscore.md (pas de modification Core)
- [x] 02_charte_developpeur.md
- [x] 03_charte_modules.md
- [x] 05_charte_ia.md (si IA)
- [x] 06_charte_securite_conformite.md

### 12.2 Dérogations

| Charte | Article | Dérogation | Justification |
|--------|---------|------------|---------------|
| - | - | Aucune | - |

---

## 13. CONTACTS

| Rôle | Contact |
|------|---------|
| Responsable module | {email/slack} |
| Support technique | {canal} |

---

## 14. HISTORIQUE

| Date | Auteur | Modification |
|------|--------|--------------|
| YYYY-MM-DD | {Auteur} | Création |

---

*Fin du template GOVERNANCE.md*
```

---

## CHECKLIST VALIDATION

Avant de merger un module, vérifier :

- [ ] Fichier GOVERNANCE.md présent
- [ ] Toutes les sections remplies
- [ ] Objectif clair et délimité
- [ ] Périmètre explicite (inclus ET exclus)
- [ ] APIs documentées
- [ ] Dépendances = Core uniquement
- [ ] Sécurité définie
- [ ] IA encadrée (si applicable)
- [ ] Actions critiques identifiées
- [ ] Procédure désinstallation
- [ ] Conformité chartes attestée

---

*Document généré et validé le 2026-01-05*
*Classification: PUBLIC - OBLIGATOIRE*
*Référence: AZALS-GOV-09-v1.0.0*
