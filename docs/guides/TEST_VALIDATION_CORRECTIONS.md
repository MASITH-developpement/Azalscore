# GUIDE DE TEST - VALIDATION CORRECTIONS P0/P1
## Tests Manuels Post-Corrections AZALSCORE

**Date:** 2026-01-23
**Corrections appliquées:** P0-002, P0-001, P1-001
**Commits:** `51e383e` + `e7923df`
**Durée estimée:** 30 minutes

---

## 🎯 OBJECTIF

Valider que les 3 bugs critiques sont corrigés:
- ✅ P0-002: Création/modification utilisateurs
- ✅ P0-001: Dashboard admin
- ✅ P1-001: Lancer backup manuel

---

## 🚀 PRÉ-REQUIS

### 1. Démarrer les serveurs

#### Backend
```bash
cd /home/ubuntu/azalscore
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Attendu:** Serveur démarre sur `http://localhost:8000`

#### Frontend
```bash
cd /home/ubuntu/azalscore/frontend
npm run dev
```

**Attendu:** Serveur démarre sur `http://localhost:5173`

### 2. Connexion Admin

```
1. Ouvrir http://localhost:5173/login
2. Se connecter avec compte admin/superadmin
3. Naviguer vers /admin
```

---

## 🧪 TESTS VALIDATION

### ✅ TEST 1 : Création Utilisateur (P0-002)

**Bug corrigé:** `POST /v1/admin/users` → `POST /v1/iam/users`

#### Étapes
```
1. Aller sur http://localhost:5173/admin
2. Cliquer sur l'onglet "Users" ou "Utilisateurs"
3. Cliquer sur bouton "Créer utilisateur" / "Add User" / "+"
4. Remplir le formulaire:
   - Email: test-corrections@example.com
   - Nom: Test Corrections P0-002
   - Mot de passe: Test123!
   - Rôle: USER ou ADMIN
5. Soumettre le formulaire
6. Ouvrir DevTools (F12) → Onglet Network
```

#### Résultats Attendus
```
✅ Status: 201 Created (PAS 404 Not Found)
✅ UI: Utilisateur apparaît dans la liste immédiatement
✅ UI: Message de succès "Utilisateur créé avec succès"
✅ Network: Requête POST /v1/iam/users → 201
✅ Console: Aucune erreur
```

#### Résultats Avant Correction (référence)
```
❌ Status: 404 Not Found
❌ UI: Erreur affichée "Impossible de créer l'utilisateur"
❌ Network: POST /v1/admin/users → 404
❌ Console: Error 404 sur /v1/admin/users
```

#### Si Test Échoue
```
- Vérifier que backend tourne sur port 8000
- Vérifier que frontend appelle bien /v1/iam/users (pas /v1/admin/users)
- Vérifier logs backend pour erreur interne
- Rollback: cp frontend/src/modules/admin/index.tsx.backup-* frontend/src/modules/admin/index.tsx
```

---

### ✅ TEST 2 : Modification Statut Utilisateur (P0-002)

**Bug corrigé:** `PATCH /v1/admin/users/{id}` → `PATCH /v1/iam/users/{id}`

#### Étapes
```
1. Dans la liste des utilisateurs (page /admin)
2. Sélectionner l'utilisateur créé au Test 1
3. Cliquer sur toggle "Activer/Désactiver" OU bouton "Modifier"
4. Changer le statut (actif → inactif ou inverse)
5. Confirmer l'action
6. Observer DevTools Network
```

#### Résultats Attendus
```
✅ Status: 200 OK (PAS 404 Not Found)
✅ UI: Statut change visuellement (badge devient gris/vert)
✅ UI: Message "Statut modifié avec succès"
✅ Network: PATCH /v1/iam/users/{user_id} → 200
✅ Console: Aucune erreur
```

#### Résultats Avant Correction (référence)
```
❌ Status: 404 Not Found
❌ UI: Erreur "Impossible de modifier le statut"
❌ Network: PATCH /v1/admin/users/{id} → 404
```

#### Si Test Échoue
```
- Vérifier user_id valide (doit être UUID ou string)
- Vérifier permissions RBAC user courant
- Vérifier logs backend
```

---

### ✅ TEST 3 : Dashboard Admin Affiche Métriques (P0-001)

**Bug corrigé:** `GET /v1/admin/dashboard` → `GET /v1/cockpit/dashboard`

#### Étapes
```
1. Aller sur http://localhost:5173/admin (page principale)
2. Observer la section "Dashboard" / "Statistiques" en haut
3. Noter les valeurs affichées:
   - Total utilisateurs
   - Utilisateurs actifs
   - Total tenants
   - Autres métriques
4. Ouvrir DevTools Network
5. Rafraîchir la page (F5)
```

#### Résultats Attendus
```
✅ Total utilisateurs: > 0 (PAS 0)
✅ Utilisateurs actifs: > 0 (PAS 0)
✅ Total tenants: ≥ 1 (PAS 0)
✅ Autres métriques: Valeurs réalistes (pas tout à 0)
✅ Network: GET /v1/cockpit/dashboard → 200 OK
✅ Response body: Contient vraies données
✅ Console: Aucune erreur 404
```

#### Résultats Avant Correction (référence)
```
❌ Total utilisateurs: 0
❌ Utilisateurs actifs: 0
❌ Total tenants: 0
❌ Toutes métriques: 0
❌ Network: GET /v1/admin/dashboard → 404 (silencieuse)
❌ Fallback activé → valeurs par défaut (0)
```

#### Si Test Échoue
```
- Vérifier que cockpit router est enregistré dans main.py
- Vérifier que endpoint /v1/cockpit/dashboard existe
- Vérifier logs backend pour erreur SQL
- Test alternatif: curl http://localhost:8000/v1/cockpit/dashboard
```

---

### ✅ TEST 4 : Lancer Backup Manuel (P1-001)

**Bug corrigé:** Endpoint `POST /v1/backup/{backup_id}/run` implémenté

#### Pré-requis
```
1. Créer une configuration backup (si pas déjà fait):
   - Aller sur /admin → onglet "Backups"
   - Créer config backup avec paramètres par défaut

2. Créer au moins 1 backup existant:
   - Cliquer "Créer backup" → Backup ID: xxx-yyy-zzz
```

#### Étapes
```
1. Dans la liste des backups (/admin → Backups)
2. Sélectionner un backup existant (status: COMPLETED ou PENDING)
3. Cliquer sur bouton "Lancer backup" / "Run" / icône play ▶️
4. Confirmer l'action si popup
5. Observer DevTools Network
6. Attendre quelques secondes
7. Rafraîchir la liste des backups
```

#### Résultats Attendus
```
✅ Status: 201 Created (PAS 404 Not Found)
✅ UI: Message "Backup lancé avec succès"
✅ UI: Un nouveau backup apparaît dans la liste (status: PENDING ou IN_PROGRESS)
✅ Network: POST /v1/backup/{backup_id}/run → 201
✅ Response body: Contient le nouveau backup créé
✅ Nouveau backup: Note contient "Re-exécution de {ref}"
✅ Console: Aucune erreur
```

#### Résultats Avant Correction (référence)
```
❌ Status: 404 Not Found
❌ UI: Erreur "Impossible de lancer le backup"
❌ Network: POST /v1/backup/{id}/run → 404
❌ Bouton cliquable mais ne fait rien
```

#### Si Test Échoue
```
- Vérifier que backup_id existe et est valide UUID
- Vérifier permissions backup.create
- Vérifier que service.create_backup fonctionne
- Test alternatif: curl -X POST http://localhost:8000/v1/backup/{id}/run
```

---

### ✅ TEST 5 : Console Globale Propre

**Validation:** Aucune erreur 404 sur /v1/admin/*

#### Étapes
```
1. Ouvrir DevTools (F12)
2. Onglet Console
3. Effacer la console (Ctrl+L)
4. Naviguer vers /admin
5. Cliquer sur différents onglets (Users, Roles, Tenants, Backups)
6. Effectuer quelques actions (créer, modifier, voir détails)
7. Observer les erreurs dans la console
```

#### Résultats Attendus
```
✅ Console: AUCUNE erreur 404 sur /v1/admin/users
✅ Console: AUCUNE erreur 404 sur /v1/admin/dashboard
✅ Console: AUCUNE erreur 404 sur /v1/backup/{id}/run
✅ Requêtes réussies vers:
   - /v1/iam/users (GET, POST, PATCH)
   - /v1/iam/roles (GET)
   - /v1/cockpit/dashboard (GET)
   - /v1/tenants (GET)
   - /v1/backup/* (GET, POST)
```

#### Si Erreurs Détectées
```
- Noter l'URL exacte de l'erreur 404
- Vérifier si endpoint existe dans backend
- Vérifier frontend appelle bon endpoint
- Créer issue si nouveau bug découvert
```

---

## 📊 TABLEAU RÉCAPITULATIF

| Test | Avant | Après | Status |
|------|-------|-------|--------|
| Créer user | ❌ 404 | ✅ 201 | [ ] À TESTER |
| Modifier user | ❌ 404 | ✅ 200 | [ ] À TESTER |
| Dashboard | ❌ Tout à 0 | ✅ Vraies métriques | [ ] À TESTER |
| Lancer backup | ❌ 404 | ✅ 201 | [ ] À TESTER |
| Console propre | ❌ Erreurs 404 | ✅ Pas d'erreurs | [ ] À TESTER |

**Instructions:** Cocher chaque test après validation ✅

---

## 🔍 TESTS AVANCÉS (OPTIONNEL)

### Test 6 : API Directe (cURL)

Si UI pose problème, tester endpoints directement:

```bash
# 1. Login pour obtenir token
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "your_password"
  }'

# Copier le access_token

# 2. Tester création user
curl -X POST http://localhost:8000/v1/iam/users \
  -H "Authorization: Bearer {TOKEN}" \
  -H "X-Tenant-ID: your-tenant" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "api-test@example.com",
    "name": "API Test User",
    "password": "Test123!",
    "role_code": "USER"
  }'

# Attendu: 201 Created

# 3. Tester dashboard
curl http://localhost:8000/v1/cockpit/dashboard \
  -H "Authorization: Bearer {TOKEN}" \
  -H "X-Tenant-ID: your-tenant"

# Attendu: 200 OK + JSON avec métriques

# 4. Tester run backup (remplacer {backup_id})
curl -X POST http://localhost:8000/v1/backup/{backup_id}/run \
  -H "Authorization: Bearer {TOKEN}" \
  -H "X-Tenant-ID: your-tenant"

# Attendu: 201 Created + JSON nouveau backup
```

---

## ✅ VALIDATION FINALE

### Critères de Succès (TOUS doivent passer)

- [ ] Test 1: Création user → 201 Created
- [ ] Test 2: Modification user → 200 OK
- [ ] Test 3: Dashboard → Métriques > 0
- [ ] Test 4: Lancer backup → 201 Created
- [ ] Test 5: Console → Aucune erreur 404
- [ ] Aucun crash backend pendant les tests
- [ ] Aucune régression sur autres features

### Si TOUS les tests passent ✅

```bash
# 1. Push vers origin
git push origin develop

# 2. (Optionnel) Merge vers main
git checkout main
git merge develop
git push origin main

# 3. Déploiement staging
# → Suivre workflow habituel

# 4. Tests smoke staging (même checklist)

# 5. Déploiement production (si staging OK)
```

### Si UN OU PLUSIEURS tests échouent ❌

```bash
# 1. Noter quel test échoue
# 2. Investiguer logs backend/frontend
# 3. Rollback si nécessaire:

# Rollback frontend (P0-002, P0-001)
cp frontend/src/modules/admin/index.tsx.backup-20260123-215221 \
   frontend/src/modules/admin/index.tsx
git add frontend/src/modules/admin/index.tsx
git commit -m "revert: Rollback corrections admin"

# Rollback backend (P1-001)
git revert e7923df
# Ou éditer manuellement app/modules/backup/router.py

# 4. Analyser le problème
# 5. Recorriger
# 6. Re-tester
```

---

## 📝 RAPPORT DE TEST

**À remplir après tests:**

### Environnement
- Backend version: _____
- Frontend version: _____
- Node version: _____
- Python version: _____
- OS: _____
- Date: 2026-01-23
- Testeur: _____

### Résultats

| Test | Résultat | Notes |
|------|----------|-------|
| Test 1 - Créer user | [ ] OK [ ] KO | |
| Test 2 - Modifier user | [ ] OK [ ] KO | |
| Test 3 - Dashboard | [ ] OK [ ] KO | |
| Test 4 - Lancer backup | [ ] OK [ ] KO | |
| Test 5 - Console | [ ] OK [ ] KO | |

### Bugs Additionnels Découverts

```
(Si bugs trouvés pendant tests, les noter ici)
```

### Décision

[ ] ✅ TOUS TESTS OK → GO pour déploiement
[ ] ❌ TESTS KO → Rollback requis
[ ] ⚠️ TESTS PARTIELS → Décision à prendre

---

## 🚀 APRÈS VALIDATION

### Si GO Déploiement

1. **Documentation mise à jour:**
   - Mettre à jour AZALSCORE_FUNCTIONAL_AUDIT.md
   - Marquer P0-002, P0-001, P1-001 comme RESOLVED
   - Mettre à jour verdict: NO-GO → GO CONDITIONNEL

2. **Communication équipe:**
   - Annoncer corrections appliquées
   - Bugs P0/P1 résolus
   - Prêt pour staging

3. **Phase 3:**
   - Démarrer audit modules métier
   - Tester Partners, Invoicing, Treasury, etc.
   - Durée: 2 semaines

---

## 📞 SUPPORT

**Problème pendant tests ?**
- Backend crash: Voir logs dans `/home/ubuntu/azalscore/logs/`
- Frontend erreur: DevTools Console + Network tab
- Questions: Consulter AZALSCORE_FUNCTIONAL_AUDIT.md

**Contacts:**
- Tech Lead: [à compléter]
- QA Lead: [à compléter]
- On-call: [à compléter]

---

**Créé le:** 2026-01-23
**Par:** QA Lead (Audit Fonctionnel)
**Version:** 1.0
**Statut:** PRÊT POUR TESTS

**🎯 Bon courage pour les tests ! 🚀**
