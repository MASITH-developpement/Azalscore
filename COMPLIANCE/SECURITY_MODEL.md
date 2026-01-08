# AZALSCORE - Modèle de Sécurité
## COMPLIANCE/SECURITY_MODEL.md

**Version**: 1.0
**Date**: 2026-01-08
**Classification**: Document interne - Confidentiel

---

## 1. VUE D'ENSEMBLE

AZALSCORE est un ERP SaaS multi-tenant conçu avec une approche **Security by Design**. Ce document décrit l'architecture de sécurité et les mesures de protection implémentées.

---

## 2. ARCHITECTURE DE SÉCURITÉ

### 2.1 Défense en Profondeur

```
                    ┌─────────────────────────────┐
                    │     COUCHE RÉSEAU           │
                    │  - TLS 1.3 (HTTPS)          │
                    │  - HSTS (1 an)              │
                    │  - DDoS Protection          │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │   COUCHE APPLICATION        │
                    │  - Rate Limiting            │
                    │  - Security Headers (OWASP) │
                    │  - Input Validation         │
                    │  - CORS Restrictif          │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │   COUCHE AUTHENTIFICATION   │
                    │  - JWT (HS256, 30min TTL)   │
                    │  - 2FA TOTP obligatoire     │
                    │  - Refresh tokens (7j)      │
                    │  - Rate limiting auth       │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │   COUCHE AUTORISATION       │
                    │  - RBAC 5 rôles             │
                    │  - Deny by default          │
                    │  - Multi-tenant isolation   │
                    │  - Triple validation tenant │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │   COUCHE DONNÉES            │
                    │  - AES-256 au repos         │
                    │  - Bcrypt (mots de passe)   │
                    │  - Audit journal immutable  │
                    │  - Hash chaîné (intégrité)  │
                    └─────────────────────────────┘
```

---

## 3. AUTHENTIFICATION

### 3.1 Mécanismes

| Mécanisme | Implémentation | Force |
|-----------|----------------|-------|
| Mot de passe | bcrypt (auto-salt) | Fort |
| Token session | JWT HS256 | Fort |
| 2FA | TOTP (Google Auth compatible) | Fort |
| Backup codes | 10 codes x 8 caractères | Fort |

### 3.2 Protection Brute Force

```
Tentative 1-5  : Autorisé
Tentative 6+   : Blocage IP 1 minute
Échecs 5+      : Blocage compte 15 minutes
```

### 3.3 Token Lifecycle

```
Access Token  : 30 minutes TTL
Refresh Token : 7 jours TTL
2FA Pending   : 5 minutes TTL
```

---

## 4. AUTORISATION (RBAC)

### 4.1 Matrice des Rôles

| Rôle | Niveau | Capacités |
|------|--------|-----------|
| super_admin | 0 | Accès total système (invisible UI) |
| admin | 1 | Administration organisation |
| manager | 2 | Gestion équipe |
| user | 3 | Opérations standard |
| readonly | 4 | Consultation uniquement |

### 4.2 Modules Protégés

- USERS : Gestion utilisateurs
- ORGANIZATION : Configuration société
- CLIENTS : CRM / Contacts
- BILLING : Facturation / Paiements
- PROJECTS : Projets / Tâches
- REPORTING : KPI / Exports
- SETTINGS : Paramètres
- SECURITY : Configuration sécurité
- AUDIT : Journal d'audit

### 4.3 Principe Deny by Default

```python
# Route non configurée dans RBAC = 403 INTERDIT
# Sauf routes explicitement publiques
```

---

## 5. ISOLATION MULTI-TENANT

### 5.1 Architecture

```
Tenant A ─────┐
              │
Tenant B ─────┼───► API Gateway ───► tenant_id validation
              │         │
Tenant C ─────┘         │
                        ▼
                   ┌─────────┐
                   │   DB    │  ← Toutes tables ont tenant_id
                   └─────────┘
```

### 5.2 Triple Validation

1. **Middleware** : Valide X-Tenant-ID header
2. **JWT** : Contient tenant_id, vérifié contre header
3. **Database** : Toutes requêtes filtrées par tenant_id

### 5.3 Garanties

- ❌ Aucun accès cross-tenant possible
- ❌ Mismatch JWT/Header = 403
- ❌ Création pour autre tenant = Ignoré, créé pour son propre tenant
- ✅ Logs d'audit isolés par tenant

---

## 6. CHIFFREMENT

### 6.1 En Transit

| Protocole | Configuration |
|-----------|---------------|
| TLS | Version 1.2+ (1.3 recommandé) |
| HSTS | max-age=31536000; includeSubDomains; preload |
| Certificats | Let's Encrypt / AWS ACM |

### 6.2 Au Repos

| Type | Algorithme | Fichier |
|------|------------|---------|
| Colonnes sensibles | AES-256 (Fernet) | `app/core/encryption.py` |
| Mots de passe | bcrypt (auto-rounds) | `app/core/security.py` |
| Secrets TOTP | Base32 encodé | `app/core/two_factor.py` |

### 6.3 Gestion des Clés

```
ENCRYPTION_KEY : Variable d'environnement
SECRET_KEY     : Variable d'environnement
BOOTSTRAP_SECRET : Variable d'environnement

JAMAIS dans le code source.
Rotation : Procédure documentée (voir INCIDENT_PLAN.md)
```

---

## 7. AUDIT ET TRAÇABILITÉ

### 7.1 Journal d'Audit

| Caractéristique | Valeur |
|-----------------|--------|
| Type | Append-only |
| Modification | Interdite (triggers SQL) |
| Suppression | Interdite (triggers SQL) |
| Intégrité | Hash chaîné SHA-256 |
| Horodatage | Server-side (non modifiable) |

### 7.2 Événements Journalisés

- Connexions / Déconnexions
- Modifications de données
- Erreurs de sécurité
- Décisions RED
- Actions administratives

### 7.3 Vérification Intégrité

```sql
SELECT * FROM verify_journal_integrity('tenant-id');
-- Retourne: is_valid, broken_at_id, expected_hash, actual_hash
```

---

## 8. PROTECTION APPLICATIVE

### 8.1 Security Headers (OWASP)

```http
Content-Security-Policy: default-src 'self'; script-src 'self'; ...
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), ...
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

### 8.2 Rate Limiting

| Endpoint | Limite |
|----------|--------|
| Général | 100 req/min/IP |
| Auth | 5 req/min/IP |
| Register | 3 req/5min/IP |

### 8.3 Validation des Entrées

- Payload max : 10 MB
- Content-Type : JSON, form-data, urlencoded
- Paramètres : Validation Pydantic stricte

---

## 9. VULNÉRABILITÉS OWASP TOP 10

| # | Vulnérabilité | Protection |
|---|---------------|------------|
| A01 | Broken Access Control | RBAC + Triple validation tenant |
| A02 | Cryptographic Failures | AES-256, TLS 1.3, bcrypt |
| A03 | Injection | SQLAlchemy ORM, paramétrage |
| A04 | Insecure Design | Security by Design |
| A05 | Security Misconfiguration | Config stricte, validation env |
| A06 | Vulnerable Components | Dépendances auditées |
| A07 | Auth Failures | JWT + 2FA + Rate limiting |
| A08 | Software/Data Integrity | Hash chaîné audit |
| A09 | Security Logging | Journal append-only |
| A10 | SSRF | Validation URLs stricte |

---

## 10. CONFORMITÉ

### 10.1 RGPD / CNIL

- Chiffrement des données personnelles
- Droit à l'effacement (suppression logique)
- Export des données (JSON)
- Journal d'accès aux données
- Consentement explicite

### 10.2 Audit

- Logs conservés 3 ans minimum
- Intégrité vérifiable
- Non-répudiation (hash chaîné)

---

## 11. CONTACTS SÉCURITÉ

| Rôle | Email |
|------|-------|
| Responsable Sécurité | security@azalscore.com |
| Incident Response | incident@azalscore.com |
| Bug Bounty | bugbounty@azalscore.com |

---

## 12. HISTORIQUE

| Version | Date | Auteur | Changements |
|---------|------|--------|-------------|
| 1.0 | 2026-01-08 | Système | Création initiale |
