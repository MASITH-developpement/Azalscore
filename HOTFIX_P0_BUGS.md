# HOTFIX - BUGS P0 CRITIQUES AZALSCORE
## Corrections Urgentes Avant Production

**Date:** 2026-01-23
**Bugs identifiés:** 3 bugs P0 bloquants
**Effort total:** 35 minutes (corrections critiques)

---

## 🚨 P0-002 : CRUD Utilisateurs Non Fonctionnel

### Symptômes
- Bouton "Créer utilisateur" → Erreur 404
- Toggle "Activer/Désactiver utilisateur" → Erreur 404
- Console: `POST /v1/admin/users 404 Not Found`
- Console: `PATCH /v1/admin/users/{id} 404 Not Found`

### Cause Racine
Frontend appelle endpoints `/v1/admin/users/*` qui N'EXISTENT PAS.
Backend expose uniquement `/v1/iam/users/*` (IAM router).

### Impact
**BLOQUANT** - Administrateurs ne peuvent PAS gérer les utilisateurs (création/modification impossible).

### Correction - 5 MINUTES ⚡

**Fichier:** `/home/ubuntu/azalscore/frontend/src/modules/admin/index.tsx`

#### Fix 1 - Création utilisateur (ligne 301)
```typescript
// AVANT (ligne 301)
const useCreateUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<User> & { password: string }) => {
      return api.post('/v1/admin/users', data).then(r => r.data);
      //            ^^^^^^^^^^^^^^^^ ERREUR ICI
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
  });
};

// APRÈS (correction)
const useCreateUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<User> & { password: string }) => {
      return api.post('/v1/iam/users', data).then(r => r.data);
      //            ^^^^^^^^^^^^^^ CORRIGÉ
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
  });
};
```

#### Fix 2 - Modification statut utilisateur (ligne 311)
```typescript
// AVANT (ligne 311)
const useUpdateUserStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch(`/v1/admin/users/${id}`, { status }).then(r => r.data);
      //                ^^^^^^^^^^^^^^^^^^ ERREUR ICI
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'user'] });
    }
  });
};

// APRÈS (correction)
const useUpdateUserStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch(`/v1/iam/users/${id}`, { status }).then(r => r.data);
      //                ^^^^^^^^^^^^^^^ CORRIGÉ
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'user'] });
    }
  });
};
```

### Commandes de correction
```bash
cd /home/ubuntu/azalscore/frontend

# Backup
cp src/modules/admin/index.tsx src/modules/admin/index.tsx.backup

# Correction automatique via sed
sed -i "301s|/v1/admin/users|/v1/iam/users|" src/modules/admin/index.tsx
sed -i "311s|/v1/admin/users|/v1/iam/users|" src/modules/admin/index.tsx

# Vérification
grep -n "api.post('/v1/iam/users'" src/modules/admin/index.tsx  # doit afficher ligne 301
grep -n "api.patch(\`/v1/iam/users/" src/modules/admin/index.tsx  # doit afficher ligne 311

# Test
npm run dev
# → Tester création utilisateur via interface admin
```

### Validation
1. ✅ Créer un utilisateur → Status 201 Created (au lieu de 404)
2. ✅ Modifier statut utilisateur → Status 200 OK (au lieu de 404)
3. ✅ Console: Aucune erreur 404 sur `/v1/admin/users`

---

## 🚨 P0-001 : Dashboard Admin Retourne Toujours 0

### Symptômes
- Dashboard admin affiche TOUJOURS:
  - Total utilisateurs: 0
  - Utilisateurs actifs: 0
  - Total tenants: 0
  - Toutes métriques à zéro
- Console: `GET /v1/admin/dashboard 404 Not Found` (erreur silencieuse)

### Cause Racine
Frontend appelle `/v1/admin/dashboard`, backend expose `/v1/cockpit/dashboard`.
Header `X-Silent-Error: true` masque l'erreur 404 → fallback valeurs par défaut (0).

### Impact
**BLOQUANT** - Administrateurs voient un dashboard vide, impossible de monitorer le système.

### Correction - 30 MINUTES

**Option A (Rapide) - Aligner frontend sur backend**

**Fichier:** `/home/ubuntu/azalscore/frontend/src/modules/admin/index.tsx`

```typescript
// AVANT (ligne ~110)
const useDashboard = () => {
  return useQuery({
    queryKey: ['admin', 'dashboard'],
    queryFn: async () => {
      try {
        return await api.get<AdminDashboard>('/v1/admin/dashboard', {
          //                                 ^^^^^^^^^^^^^^^^^^^^ ERREUR
          headers: { 'X-Silent-Error': 'true' }
        }).then(r => r.data);
      } catch {
        return {
          total_users: 0,
          active_users: 0,
          // ... fallback à 0
        };
      }
    },
    retry: false
  });
};

// APRÈS (correction)
const useDashboard = () => {
  return useQuery({
    queryKey: ['admin', 'dashboard'],
    queryFn: async () => {
      try {
        return await api.get<AdminDashboard>('/v1/cockpit/dashboard', {
          //                                 ^^^^^^^^^^^^^^^^^^^^^^ CORRIGÉ
          headers: { 'X-Silent-Error': 'true' }
        }).then(r => r.data);
      } catch {
        return {
          total_users: 0,
          active_users: 0,
          // ... fallback si vraie erreur
        };
      }
    },
    retry: false
  });
};
```

**Commandes:**
```bash
cd /home/ubuntu/azalscore/frontend

# Trouver la ligne exacte
grep -n "api.get.*'/v1/admin/dashboard'" src/modules/admin/index.tsx

# Corriger (remplacer {LINE} par le numéro de ligne trouvé)
sed -i "{LINE}s|/v1/admin/dashboard|/v1/cockpit/dashboard|" src/modules/admin/index.tsx

# Vérification
grep -n "/v1/cockpit/dashboard" src/modules/admin/index.tsx

# Test
npm run dev
# → Dashboard doit afficher les vraies métriques
```

**Option B (Propre) - Créer endpoint dédié admin**

Si le dashboard cockpit et admin doivent avoir des métriques différentes:

**Fichier:** `/home/ubuntu/azalscore/app/api/admin.py` (nouveau fichier)

```python
"""
AZALS - Endpoints Administration Système
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User, UserRole
from app.api.cockpit import get_cockpit_dashboard  # Réutiliser logique

router = APIRouter(prefix="/admin", tags=["Administration"])

@router.get("/dashboard")
async def get_admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dashboard admin avec métriques système."""
    # Réutiliser dashboard cockpit (ou logique différente si besoin)
    return await get_cockpit_dashboard(request, db, current_user)
```

**Enregistrement dans main.py:**
```python
# /home/ubuntu/azalscore/app/main.py (ligne ~25)
from app.api.admin import router as admin_router

# (ligne ~600)
api_v1.include_router(admin_router)  # Ajouter cette ligne
```

**Effort:** 2h si logique admin spécifique requise.

### Validation
1. ✅ Dashboard affiche vraies métriques (pas des 0)
2. ✅ Console: `GET /v1/cockpit/dashboard 200 OK` (ou `/v1/admin/dashboard` si option B)
3. ✅ Total users > 0, total tenants > 0

---

## 🟡 P1-001 : Endpoint "Lancer Backup" Manquant

### Symptômes
- Bouton "Lancer backup" visible dans UI
- Clic → Erreur 404
- Console: `POST /v1/backup/{id}/run 404 Not Found`

### Cause Racine
Frontend appelle `POST /v1/backup/{id}/run`, endpoint n'existe PAS dans backend.

### Impact
Feature secondaire mais UX confuse (bouton cliquable qui ne fait rien).

### Options de Correction

#### Option A - Retirer le bouton (15 min)
Si feature pas prête pour production:

**Fichier:** `/home/ubuntu/azalscore/frontend/src/modules/admin/index.tsx`

```typescript
// AVANT (ligne ~320)
const useRunBackup = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/v1/backup/${id}/run`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'backups'] })
  });
};

// APRÈS - Commenter le hook
/*
const useRunBackup = () => {
  // Feature désactivée temporairement
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      throw new Error('Feature non disponible');
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'backups'] })
  });
};
*/
```

Puis retirer le bouton de l'UI (chercher où `useRunBackup` est utilisé).

#### Option B - Implémenter l'endpoint (4h)
Si feature doit fonctionner:

**Fichier:** `/home/ubuntu/azalscore/app/modules/backup/router.py`

```python
# Ajouter après ligne 138 (après DELETE /{backup_id})

@router.post("/{backup_id}/run", response_model=BackupResponse)
def run_backup(
    backup_id: str,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Lancer une sauvegarde existante (re-run)."""
    # Récupérer backup existant
    backup = service.get_backup(backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Sauvegarde non trouvée")

    # Créer une nouvelle sauvegarde basée sur la config existante
    new_backup_data = BackupCreate(
        name=f"{backup.name} (re-run)",
        description=f"Re-exécution de {backup_id}",
        backup_type=backup.backup_type,
        include_tables=backup.include_tables,
        exclude_tables=backup.exclude_tables
    )

    return service.create_backup(
        new_backup_data,
        triggered_by=current_user.email or "api"
    )
```

**Effort:** 4h (implémentation + tests + validation)

### Décision requise
Product Owner doit choisir: retirer feature (15 min) ou implémenter (4h)?

---

## 📝 CHECKLIST DE DÉPLOIEMENT

### Avant corrections
- [x] Bugs identifiés et documentés
- [x] Fichiers affectés listés
- [x] Corrections détaillées
- [ ] Backup des fichiers originaux

### Corrections critiques
- [ ] **P0-002:** Fix CRUD users (5 min)
- [ ] **P0-001:** Fix dashboard admin (30 min)
- [ ] Décision P1-001 backup (PO)

### Validation post-correction
- [ ] Tests manuels:
  - [ ] Créer utilisateur via /admin
  - [ ] Modifier statut utilisateur
  - [ ] Dashboard affiche vraies métriques
- [ ] Tests automatiques (si disponibles):
  - [ ] `npm run test`
  - [ ] Tests E2E admin module
- [ ] Logs propres:
  - [ ] Aucune erreur 404 sur `/v1/admin/*`
  - [ ] Console frontend sans erreurs

### Déploiement
- [ ] Commit corrections:
  ```bash
  git add frontend/src/modules/admin/index.tsx
  git commit -m "fix(admin): Corriger endpoints CRUD users et dashboard (P0-002, P0-001)"
  ```
- [ ] Push + déploiement staging
- [ ] Tests smoke staging
- [ ] Déploiement production

---

## 🎯 TIMELINE RECOMMANDÉE

| Timing | Tâche | Durée |
|--------|-------|-------|
| **Immédiat** | Fix P0-002 CRUD users | 5 min |
| **+10 min** | Test manuel création user | 5 min |
| **+15 min** | Fix P0-001 dashboard | 30 min |
| **+45 min** | Test manuel dashboard | 10 min |
| **+55 min** | Décision P1-001 backup | 15 min |
| **+1h10** | Commit + push staging | 10 min |
| **+1h20** | Tests smoke staging | 20 min |
| **Total** | **1h40** | (corrections critiques) |

---

## 📞 CONTACT

**Questions techniques:** Se référer à `/home/ubuntu/azalscore/AZALSCORE_FUNCTIONAL_AUDIT.md`

**Bugs additionnels:** 25+ modules métier non testés, audit en cours (Phase 3).

---

**🚨 ACTION REQUISE: Corriger P0-002 et P0-001 AVANT tout déploiement production.**
