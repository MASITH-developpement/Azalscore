# AUDIT SECRETS ET CREDENTIALS - AZALSCORE
**Date:** 2026-02-17
**Auditeur:** Claude Code
**Statut:** COMPLETÉ

---

## RÉSUMÉ EXÉCUTIF

| Catégorie | Statut |
|-----------|--------|
| Fichiers .env trackés | ✅ OK - Seulement templates |
| Secrets dans code Python | ⚠️ 2 ISSUES |
| Secrets dans config | ⚠️ 1 ISSUE |
| Historique Git | ✅ OK - Pas de secrets |
| .gitignore | ✅ OK - Bien configuré |

**Score global:** 🟡 **ATTENTION REQUISE** (3 issues mineures)

---

## FINDINGS

### 🔴 ISSUE #1 - Password hardcodé dans script (MOYENNE)

**Fichier:** `scripts/fix_admin_password.py:59`
```python
admin_password = "admin123"
```

**Risque:** Script de dev avec mot de passe faible hardcodé
**Recommandation:**
- Lire le mot de passe depuis variable d'environnement
- Ou demander le mot de passe en input interactif

**Fix suggéré:**
```python
admin_password = os.environ.get("ADMIN_PASSWORD") or input("Enter admin password: ")
```

---

### 🟡 ISSUE #2 - Credentials DB dans script (BASSE)

**Fichier:** `scripts/provision_masith_tenant.py:36`
```python
url = "postgresql://azals_user:azals_password@localhost:5432/azals"
```

**Risque:** Credentials de développement hardcodés
**Recommandation:** Utiliser `os.environ.get("DATABASE_URL")`

---

### 🟡 ISSUE #3 - Placeholder SMTP password (BASSE)

**Fichier:** `infra/alertmanager/alertmanager.yml:17`
```yaml
smtp_auth_password: 'CHANGE_ME'
```

**Risque:** Placeholder pourrait être oublié en production
**Recommandation:** Utiliser variable d'environnement `${SMTP_PASSWORD}`

---

## POINTS POSITIFS

### ✅ .gitignore correctement configuré
```
.env
.env.*
.env.local
.env.production
secrets/
```

### ✅ Fichiers .env sensibles NON trackés
- `.env.production` (contient vrais secrets) → **NON VERSIONNÉ** ✅
- `.env.local` (contient clés API) → **NON VERSIONNÉ** ✅

### ✅ Historique Git propre
- Aucune clé API OpenAI/Anthropic trouvée
- Aucun mot de passe de production trouvé
- Variables utilisent `${VAR}` (références env)

### ✅ Templates sécurisés
- `.env.example` - Placeholders uniquement
- `.env.production.template` - Variables sans valeurs

---

## SECRETS LOCAUX DÉTECTÉS (NON VERSIONNÉS)

⚠️ **Ces fichiers existent localement mais ne sont PAS dans le repo:**

| Fichier | Secrets |
|---------|---------|
| `.env.production` | POSTGRES_PASSWORD, SECRET_KEY, BOOTSTRAP_SECRET |
| `.env.local` | OPENAI_API_KEY, ANTHROPIC_API_KEY, GRAFANA_PASSWORD, ENCRYPTION_KEY |

**Action:** Ces fichiers sont correctement exclus du versioning.

---

## RECOMMANDATIONS

### Priorité HAUTE
1. [ ] Corriger `scripts/fix_admin_password.py` - utiliser env var
2. [ ] Corriger `scripts/provision_masith_tenant.py` - utiliser DATABASE_URL

### Priorité MOYENNE
3. [ ] Installer `detect-secrets` dans CI/CD pour prévention
4. [ ] Ajouter pre-commit hook pour bloquer commits avec secrets

### Priorité BASSE
5. [ ] Remplacer placeholder alertmanager par env var
6. [ ] Documenter rotation des secrets

---

## COMMANDES DE VÉRIFICATION

```bash
# Scanner avec detect-secrets (si installé)
detect-secrets scan --all-files

# Vérifier fichiers .env trackés
git ls-files | grep -E "\.env"

# Scanner historique pour pattern secret
git log -p --all -S "sk-" --oneline | head -20
```

---

## CONCLUSION

L'audit révèle que la configuration de sécurité est **globalement correcte**:
- Les secrets de production ne sont pas versionnés
- Le .gitignore est bien configuré
- L'historique Git est propre

**3 corrections mineures** sont nécessaires dans les scripts de développement.

---
*Rapport généré automatiquement - Phase 0 Tâche #97*
