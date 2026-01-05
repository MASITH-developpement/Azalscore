# CHARTE SÉCURITÉ ET CONFORMITÉ AZALSCORE
## Protection des Données et Conformité Réglementaire

**Version:** 1.0.0
**Statut:** DOCUMENT CRITIQUE
**Date:** 2026-01-05
**Classification:** CONFIDENTIEL - OPPOSABLE
**Référence:** AZALS-GOV-06-v1.0.0

---

## 1. OBJECTIF

Cette charte définit les exigences de sécurité, les mesures de protection, et les obligations de conformité réglementaire pour AZALSCORE.

---

## 2. PÉRIMÈTRE

- Infrastructure et hébergement
- Code applicatif
- Données utilisateurs et métier
- Accès et authentification
- Communications
- Conformité RGPD et réglementaire

---

## 3. PRINCIPES DE SÉCURITÉ

### 3.1 Security by Design

```
RÈGLE: La sécurité est native, pas additionnelle.

- Intégrée dès la conception
- Validée à chaque étape
- Testée en continu
- Auditée régulièrement
```

### 3.2 Defense in Depth

```
┌─────────────────────────────────────────────────────┐
│                    PÉRIMÈTRE                         │
│  ┌───────────────────────────────────────────────┐  │
│  │               RÉSEAU (Firewall)                │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │          APPLICATION (WAF)               │  │  │
│  │  │  ┌───────────────────────────────────┐  │  │  │
│  │  │  │      AUTHENTIFICATION (JWT)        │  │  │  │
│  │  │  │  ┌─────────────────────────────┐  │  │  │  │
│  │  │  │  │   AUTORISATION (RBAC)       │  │  │  │  │
│  │  │  │  │  ┌───────────────────────┐  │  │  │  │  │
│  │  │  │  │  │   DONNÉES (Chiffré)   │  │  │  │  │  │
│  │  │  │  │  └───────────────────────┘  │  │  │  │  │
│  │  │  │  └─────────────────────────────┘  │  │  │  │
│  │  │  └───────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 3.3 Zero Trust

```
RÈGLE: Ne jamais faire confiance, toujours vérifier.

- Chaque requête est authentifiée
- Chaque action est autorisée
- Chaque donnée est validée
- Aucune confiance implicite
```

### 3.4 Moindre Privilège

```
RÈGLE: Accès minimum nécessaire.

- Utilisateur : droits strictement nécessaires
- Service : permissions minimales
- API : endpoints restreints
- Base de données : accès limité
```

---

## 4. AUTHENTIFICATION

### 4.1 JWT (JSON Web Token)

```python
# Configuration obligatoire
JWT_CONFIG = {
    "algorithm": "HS256",
    "expire_minutes": 30,        # 30 minutes max
    "refresh_expire_days": 7,    # 7 jours max
    "issuer": "azalscore",
    "audience": "azalscore-api"
}
```

### 4.2 Validation Token

```python
# Validations obligatoires
def validate_token(token: str) -> TokenPayload:
    # 1. Signature valide
    # 2. Non expiré
    # 3. Issuer correct
    # 4. Audience correcte
    # 5. tenant_id présent
    # 6. user_id présent
```

### 4.3 2FA (Two-Factor Authentication)

```
RÈGLE: 2FA obligatoire en production pour les rôles critiques.

Méthodes supportées:
- TOTP (Google Authenticator, Authy)
- Codes de secours (backup codes)

Rôles nécessitant 2FA:
- DIRIGEANT
- ADMIN
- Tout rôle avec accès financier
```

### 4.4 Protection Brute Force

```python
BRUTE_FORCE_PROTECTION = {
    "max_attempts": 5,           # 5 tentatives max
    "lockout_duration": 900,     # 15 minutes de blocage
    "progressive_delay": True,   # Délai croissant
}
```

---

## 5. AUTORISATION

### 5.1 RBAC (Role-Based Access Control)

```python
# Rôles standards
ROLES = {
    "DIRIGEANT": {
        "description": "Accès total, validation RED",
        "permissions": ["*"]
    },
    "MANAGER": {
        "description": "Gestion équipe et opérations",
        "permissions": ["module.*", "reports.read"]
    },
    "USER": {
        "description": "Utilisateur standard",
        "permissions": ["module.read", "module.create"]
    },
    "READONLY": {
        "description": "Consultation uniquement",
        "permissions": ["*.read"]
    }
}
```

### 5.2 Vérification Permissions

```python
# OBLIGATOIRE sur chaque endpoint protégé
@router.get("/invoices")
async def list_invoices(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    # 1. User authentifié (JWT valide)
    # 2. Permission vérifiée
    # 3. Tenant validé
    # 4. Données filtrées par tenant
```

---

## 6. ISOLATION MULTI-TENANT

### 6.1 Règle Fondamentale

```
RÈGLE ABSOLUE: Aucune donnée ne peut fuiter entre tenants.

- Chaque requête porte un X-Tenant-ID
- Chaque query filtre par tenant_id
- Aucun accès cross-tenant possible
- Violation = Incident de sécurité
```

### 6.2 Implémentation

```python
# OBLIGATOIRE - Modèle avec TenantMixin
class Invoice(Base, TenantMixin):
    __tablename__ = "invoices"
    tenant_id = Column(String, nullable=False, index=True)
    # ...

# OBLIGATOIRE - Service avec filtrage tenant
def get_invoices(self, tenant_id: str) -> List[Invoice]:
    return self.db.query(Invoice).filter(
        Invoice.tenant_id == tenant_id  # TOUJOURS
    ).all()
```

### 6.3 Tests Obligatoires

```python
def test_tenant_isolation():
    """
    Vérifie qu'un tenant A ne peut JAMAIS
    accéder aux données d'un tenant B
    """
    # Créer donnée tenant A
    # Tenter accès avec tenant B
    # Assertion: 404 ou liste vide
```

---

## 7. PROTECTION DES DONNÉES

### 7.1 Données au Repos

```
Chiffrement obligatoire:
- Base de données: AES-256
- Backups: Chiffrés
- Fichiers sensibles: Chiffrés
- Secrets: Vault/KMS
```

### 7.2 Données en Transit

```
HTTPS obligatoire:
- TLS 1.3 minimum
- Certificats valides
- HSTS activé
- Pas de mixed content
```

### 7.3 Données Sensibles

| Type | Traitement |
|------|------------|
| Mots de passe | bcrypt, jamais en clair |
| Tokens | Hashés ou chiffrés |
| Données personnelles | RGPD, minimisation |
| Données financières | Chiffrées, auditées |

---

## 8. GESTION DES SECRETS

### 8.1 Règle Absolue

```
❌ INTERDIT: Secrets dans le code

# ❌ JAMAIS
API_KEY = "sk-1234567890"
DATABASE_URL = "postgresql://user:password@host/db"

# ✅ TOUJOURS
API_KEY = os.environ.get("API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")
```

### 8.2 Stockage Secrets

```
Méthodes autorisées:
✅ Variables d'environnement
✅ Vault (HashiCorp, AWS Secrets Manager)
✅ Fichiers .env (dev uniquement, gitignored)

Méthodes interdites:
❌ Code source
❌ Fichiers versionnés
❌ Logs
❌ Messages d'erreur
```

### 8.3 Rotation

```
Rotation obligatoire:
- JWT Secret: 90 jours
- API Keys: 180 jours
- Passwords DB: 90 jours
- Certificats: Avant expiration
```

---

## 9. HEADERS DE SÉCURITÉ

### 9.1 Headers Obligatoires

```python
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=()"
}
```

### 9.2 CORS

```python
CORS_CONFIG = {
    "allow_origins": ["https://app.azalscore.io"],  # Pas de *
    "allow_methods": ["GET", "POST", "PUT", "DELETE"],
    "allow_headers": ["Authorization", "X-Tenant-ID"],
    "allow_credentials": True,
    "max_age": 600
}
```

---

## 10. PROTECTION APPLICATIVE

### 10.1 Injection SQL

```python
# ❌ INTERDIT
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ OBLIGATOIRE - Paramétré
query = "SELECT * FROM users WHERE id = :user_id"
result = db.execute(query, {"user_id": user_id})

# ✅ RECOMMANDÉ - ORM
user = db.query(User).filter(User.id == user_id).first()
```

### 10.2 XSS (Cross-Site Scripting)

```python
# Échapper toutes les sorties
from markupsafe import escape

# ❌ INTERDIT
return f"<div>{user_input}</div>"

# ✅ OBLIGATOIRE
return f"<div>{escape(user_input)}</div>"
```

### 10.3 CSRF

```
Protection CSRF:
- Tokens CSRF sur formulaires
- SameSite cookies
- Vérification Origin/Referer
```

---

## 11. JOURNALISATION SÉCURITÉ

### 11.1 Événements à Logger

| Événement | Niveau | Rétention |
|-----------|--------|-----------|
| Login réussi | INFO | 90 jours |
| Login échoué | WARNING | 180 jours |
| Accès refusé | WARNING | 180 jours |
| Modification permission | INFO | 1 an |
| Tentative cross-tenant | CRITICAL | Permanent |
| Modification Core | CRITICAL | Permanent |

### 11.2 Format

```json
{
  "timestamp": "2026-01-05T12:00:00Z",
  "level": "WARNING",
  "event": "AUTH_FAILED",
  "ip": "192.168.1.1",
  "user_email": "user@example.com",
  "tenant_id": "tenant-123",
  "details": "Invalid password",
  "trace_id": "uuid"
}
```

### 11.3 Inviolabilité

```
RÈGLE: Les logs de sécurité sont INVIOLABLES.

- Append-only (pas de modification)
- Pas de suppression
- Horodatage serveur
- Signature si possible
```

---

## 12. CONFORMITÉ RGPD

### 12.1 Principes

| Principe | Application |
|----------|-------------|
| Licéité | Consentement ou intérêt légitime |
| Minimisation | Collecter le strict nécessaire |
| Exactitude | Données à jour |
| Limitation | Durée de conservation définie |
| Intégrité | Protection contre altération |
| Responsabilité | Prouver la conformité |

### 12.2 Droits des Personnes

```
Droits à implémenter:
- Droit d'accès (export données)
- Droit de rectification
- Droit à l'effacement
- Droit à la portabilité
- Droit d'opposition
```

### 12.3 Registre des Traitements

```markdown
# Traitement: Gestion des utilisateurs

- Finalité: Authentification et autorisation
- Base légale: Exécution du contrat
- Données: Email, nom, rôle
- Destinataires: Système interne uniquement
- Durée: Durée du contrat + 3 ans
- Mesures: Chiffrement, accès restreint
```

---

## 13. AUDIT DE SÉCURITÉ

### 13.1 Audits Réguliers

| Type | Fréquence |
|------|-----------|
| Scan vulnérabilités | Hebdomadaire |
| Pentest | Annuel |
| Revue code sécurité | Par release |
| Audit conformité | Annuel |

### 13.2 Checklist Sécurité

```markdown
## Avant Déploiement

- [ ] Secrets externalisés
- [ ] HTTPS configuré
- [ ] Headers sécurité actifs
- [ ] Rate limiting actif
- [ ] Logs sécurité actifs
- [ ] Backups chiffrés
- [ ] Tests sécurité passants
```

---

## 14. INCIDENT DE SÉCURITÉ

### 14.1 Classification

| Niveau | Description | SLA |
|--------|-------------|-----|
| CRITIQUE | Fuite données, accès non autorisé | 1h |
| HAUTE | Vulnérabilité exploitable | 4h |
| MOYENNE | Vulnérabilité potentielle | 24h |
| BASSE | Amélioration sécurité | Planifié |

### 14.2 Procédure

```
1. DÉTECTION → Alerte immédiate
2. CONFINEMENT → Isolation si nécessaire
3. INVESTIGATION → Analyse impact
4. ÉRADICATION → Correction
5. RÉCUPÉRATION → Retour à la normale
6. POST-MORTEM → Rapport + amélioration
```

---

## 15. CONSÉQUENCES DU NON-RESPECT

| Violation | Conséquence |
|-----------|-------------|
| Secret dans le code | Rejet + rotation immédiate |
| Accès cross-tenant | Incident critique |
| Log désactivé | Blocage déploiement |
| Données non chiffrées | Correction obligatoire |

---

*Document généré et validé le 2026-01-05*
*Classification: CONFIDENTIEL - OPPOSABLE*
*Référence: AZALS-GOV-06-v1.0.0*
