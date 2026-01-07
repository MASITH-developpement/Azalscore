# MATRICE RÔLES × MODULES – AZALSCORE (BÊTA)

## 🔐 Rôles standards

| Rôle | Description |
|------|-------------|
| `super_admin` | Créateur / système – invisible en bêta |
| `admin` | Administrateur de l'organisation |
| `manager` | Responsable d'équipe / service |
| `user` | Utilisateur standard |
| `readonly` | Consultation uniquement |

## 📦 Modules principaux

Les modules listés correspondent au socle ERP AZALSCORE.

| Module | Description |
|--------|-------------|
| `users` | Utilisateurs & Rôles |
| `org` | Organisation / Société |
| `clients` | Clients / Contacts |
| `billing` | Facturation / Devis / Paiements |
| `projects` | Projets / Activités |
| `reporting` | Reporting / KPI |
| `settings` | Paramètres / Configuration |
| `security` | Sécurité système |
| `audit` | Logs d'audit |

## 📊 MATRICE D'ACCÈS (CRUD)

### 🧑‍💼 Utilisateurs & Rôles (`users`)

| Action | super_admin | admin | manager | user | readonly |
|--------|-------------|-------|---------|------|----------|
| Voir utilisateurs | ✅ | ✅ | ❌ | ❌ | ❌ |
| Créer utilisateur | ✅ | ✅ | ❌ | ❌ | ❌ |
| Modifier utilisateur | ✅ | ✅ | ❌ | ❌ | ❌ |
| Supprimer utilisateur | ✅ | ⚠️ (limité) | ❌ | ❌ | ❌ |
| Modifier rôles | ✅ | ❌ | ❌ | ❌ | ❌ |

> ⚠️ `admin` ne peut jamais modifier ses propres droits.

### 🏢 Organisation / Société (`org`)

| Action | super_admin | admin | manager | user | readonly |
|--------|-------------|-------|---------|------|----------|
| Voir organisation | ✅ | ✅ | ✅ | ✅ | ✅ |
| Modifier organisation | ✅ | ✅ | ❌ | ❌ | ❌ |
| Paramètres sensibles | ✅ | ❌ | ❌ | ❌ | ❌ |

### 📁 Clients / Contacts (`clients`)

| Action | super_admin | admin | manager | user | readonly |
|--------|-------------|-------|---------|------|----------|
| Voir | ✅ | ✅ | ✅ | ✅ | ✅ |
| Créer | ✅ | ✅ | ✅ | ⚠️ (limité) | ❌ |
| Modifier | ✅ | ✅ | ✅ | ⚠️ (ses données) | ❌ |
| Supprimer | ✅ | ✅ | ❌ | ❌ | ❌ |

### 💰 Facturation / Devis / Paiements (`billing`)

| Action | super_admin | admin | manager | user | readonly |
|--------|-------------|-------|---------|------|----------|
| Voir | ✅ | ✅ | ✅ | ⚠️ (restreint) | ✅ |
| Créer | ✅ | ✅ | ✅ | ❌ | ❌ |
| Modifier | ✅ | ✅ | ❌ | ❌ | ❌ |
| Supprimer | ✅ | ⚠️ (audit) | ❌ | ❌ | ❌ |
| Valider | ✅ | ✅ | ❌ | ❌ | ❌ |

### 📦 Projets / Activités (`projects`)

| Action | super_admin | admin | manager | user | readonly |
|--------|-------------|-------|---------|------|----------|
| Voir | ✅ | ✅ | ✅ | ✅ | ✅ |
| Créer | ✅ | ✅ | ✅ | ❌ | ❌ |
| Modifier | ✅ | ✅ | ✅ | ⚠️ (assigné) | ❌ |
| Supprimer | ✅ | ⚠️ | ❌ | ❌ | ❌ |

### 📈 Reporting / KPI (`reporting`)

| Action | super_admin | admin | manager | user | readonly |
|--------|-------------|-------|---------|------|----------|
| Voir | ✅ | ✅ | ⚠️ (équipe) | ⚠️ (personnel) | ⚠️ (limité) |
| Export | ✅ | ❌ | ❌ | ❌ | ❌ |

### ⚙️ Paramètres / Configuration (`settings`)

| Action | super_admin | admin | manager | user | readonly |
|--------|-------------|-------|---------|------|----------|
| Voir | ✅ | ✅ | ❌ | ❌ | ❌ |
| Modifier | ✅ | ❌ | ❌ | ❌ | ❌ |

### 🔒 Sécurité (`security`) et 📋 Audit (`audit`)

| Action | super_admin | admin | manager | user | readonly |
|--------|-------------|-------|---------|------|----------|
| Voir | ✅ | ❌ | ❌ | ❌ | ❌ |
| Modifier | ✅ | ❌ | ❌ | ❌ | ❌ |
| Export | ✅ | ❌ | ❌ | ❌ | ❌ |

## 🚫 RÈGLES TRANSVERSALES OBLIGATOIRES

### 🔒 Sécurité

**Aucun rôle ≠ `super_admin` ne peut :**
- Modifier les rôles
- Modifier la sécurité
- Accéder aux logs système
- Désactiver des protections

### 🧱 Isolation des données

Chaque utilisateur voit :
- Uniquement son organisation
- Uniquement ses projets / clients autorisés
- **Aucune donnée cross-tenant**

## 🧪 TESTS DE VALIDATION

Pour chaque module, les tests automatisés vérifient :

1. ✅ Test accès autorisé
2. ❌ Test accès refusé (403)
3. 🔗 Test URL directe
4. 🔢 Test modification ID
5. 🔌 Test API brute

**Exécution des tests :**
```bash
python -m pytest tests/test_rbac_matrix.py -v
```

**Résultat attendu : 101 tests passent**

## 🧠 IMPLÉMENTATION

### Architecture

```
app/modules/iam/
├── rbac_matrix.py      # Matrice RBAC et règles de sécurité
├── rbac_service.py     # Service centralisé de vérification
├── rbac_middleware.py  # Middleware automatique FastAPI
├── decorators.py       # Décorateurs @require_permission
└── __init__.py         # Exports du module
```

### Utilisation

#### 1. Décorateur de permission
```python
from app.modules.iam import require_rbac_permission, Module, Action

@require_rbac_permission(Module.CLIENTS, Action.CREATE)
async def create_client(request: Request):
    ...
```

#### 2. Service RBAC
```python
from app.modules.iam import RBACService, Module, Action

rbac = RBACService(db, tenant_id)
allowed, restriction, msg = rbac.check_access(user, Module.CLIENTS, Action.READ)
```

#### 3. Vérification programmatique
```python
from app.modules.iam import has_permission, StandardRole, Module, Action

if has_permission(StandardRole.MANAGER, Module.PROJECTS, Action.CREATE):
    # Autoriser la création
```

### Principes

1. **RBAC centralisé** - Une seule source de vérité
2. **Décorateurs/middlewares obligatoires** - Vérification automatique
3. **Permissions explicites par action** - Pas d'héritage implicite
4. **Deny-by-default** - Tout ce qui n'est pas autorisé est refusé
5. **Logs sur refus critiques** - Traçabilité des tentatives d'accès

## ✅ STATUT BÊTA

Si cette matrice est strictement respectée côté serveur, **AZALSCORE est conforme à une bêta ERP professionnelle**.

### Fichiers créés

| Fichier | Description |
|---------|-------------|
| `app/modules/iam/rbac_matrix.py` | Définition de la matrice (5 rôles, 9 modules) |
| `app/modules/iam/rbac_service.py` | Service centralisé de vérification |
| `app/modules/iam/rbac_middleware.py` | Middleware FastAPI automatique |
| `tests/test_rbac_matrix.py` | 101 tests de validation |
| `docs/RBAC_MATRIX_BETA.md` | Cette documentation |

### Mapping rôles legacy → standard

| Rôle legacy | Rôle standard |
|-------------|---------------|
| DIRIGEANT | admin |
| ADMIN | admin |
| DAF | manager |
| DRH | manager |
| COMPTABLE | user |
| COMMERCIAL | user |
| EMPLOYE | readonly |
| CONSULTANT | readonly |

---

*Document généré le 2026-01-07 - AZALSCORE v1.1.0*
