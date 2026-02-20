# Référentiel Mémoire AZALSCORE

## Règles de Travail

### Méthodologie Obligatoire

1. **Toujours lire les logs backend en premier** - Avant toute modification, consulter les logs Docker pour comprendre le vrai problème.

2. **Demander avant de prendre une décision** - Ne jamais supposer ce que l'utilisateur veut. Poser la question.

3. **Ne jamais supposer sans vérifier** - Toute hypothèse doit être vérifiée AVANT d'engager une modification.

4. **Expliquer ce que tu fais** - Communiquer clairement chaque action entreprise.

---

## Leçons Apprises

### 2026-02-20 - Incident Bouton Supprimer Fournisseur

**Problème:** Un simple bouton supprimer a pris des heures à corriger.

**Causes des pertes de temps:**
- Supposition incorrecte sur le CSRF (le backend exempte déjà les Bearer tokens)
- Routes RBAC manquantes pour `/purchases/...` (seules `/v1/purchases/...` étaient configurées)
- Confusion soft delete vs hard delete sans demander à l'utilisateur
- Tests CLI impossibles car `/api/v1/auth/login` n'était pas dans les routes RBAC publiques

**Ce qui aurait dû être fait:**
- Lire les logs immédiatement pour voir "401 Unauthorized" et comprendre que c'était un problème RBAC
- Demander si l'utilisateur voulait un soft ou hard delete
- Ne pas ajouter de code CSRF sans vérifier si c'était nécessaire

---

## Configuration Technique

### Routes API

**IMPORTANT: V1 ne fonctionne plus**

- Les routes `/v1/...` ne sont plus utilisées par le frontend
- Le frontend utilise les routes sans préfixe: `/purchases/...`, `/auth/...`, etc.
- Toute nouvelle route doit être ajoutée SANS le préfixe `/v1/`

### RBAC

- Les routes doivent être ajoutées dans `/app/modules/iam/rbac_middleware.py`
- Format: `("METHOD", r"/path/pattern/?$"): RoutePermission(Module.XXX, Action.YYY)`
- Les routes publiques sont dans `PUBLIC_ROUTES`

### Suppression Fournisseurs

- Hard delete activé (suppression définitive de la base)
- Filtre `is_active=True` par défaut sur la liste
