# AZALS - Authentification JWT

## Vue d'ensemble

Système d'authentification **JWT (JSON Web Token)** avec validation stricte de la **cohérence tenant**.

## Architecture

### Composants

1. **Security Layer** (`app/core/security.py`)
   - Hashing bcrypt des mots de passe
   - Création et validation des JWT
   - Secret key: `AZALS_SECRET_KEY_CHANGE_IN_PRODUCTION_USE_ENV_VAR`
   - Algorithme: HS256
   - Expiration: 30 minutes

2. **User Model** (`app/core/models.py`)
   - Table `users` avec colonnes:
     - `id` (PK)
     - `email` (unique par tenant)
     - `password_hash` (bcrypt)
     - `tenant_id` (FK vers tenant)
     - `role` (ENUM: DIRIGEANT)
     - `is_active` (0/1)
     - `created_at`, `updated_at`

3. **Auth Endpoints** (`app/api/auth.py`)
   - `POST /auth/register` - Inscription (DIRIGEANT uniquement)
   - `POST /auth/login` - Connexion avec JWT

4. **Dependencies** (`app/core/dependencies.py`)
   - `get_current_user()` - Validation JWT + cohérence tenant

5. **Protected Endpoints** (`app/api/protected.py`)
   - `GET /me/profile` - Profil utilisateur
   - `GET /me/items` - Items du tenant de l'utilisateur

## Flux d'authentification

### 1. Inscription

```bash
POST /auth/register
Headers:
  X-Tenant-ID: tenant-1
  Content-Type: application/json
Body:
  {
    "email": "dirigeant@example.com",
    "password": "SecurePassword123"
  }
```

**Validation:**
- Email unique dans le tenant
- Password hashé avec bcrypt
- Rôle DIRIGEANT assigné automatiquement
- Utilisateur actif par défaut

**Réponse:**
```json
{
  "id": 1,
  "email": "dirigeant@example.com",
  "tenant_id": "tenant-1",
  "role": "DIRIGEANT",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 2. Connexion

```bash
POST /auth/login
Headers:
  X-Tenant-ID: tenant-1
  Content-Type: application/json
Body:
  {
    "email": "dirigeant@example.com",
    "password": "SecurePassword123"
  }
```

**Validation:**
- Email existe dans le tenant
- Password valide (bcrypt.checkpw)
- Utilisateur actif

**Réponse:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "tenant_id": "tenant-1",
  "role": "DIRIGEANT"
}
```

**JWT Payload:**
```json
{
  "sub": "1",
  "tenant_id": "tenant-1",
  "role": "DIRIGEANT",
  "exp": 1705318200
}
```

### 3. Accès aux endpoints protégés

```bash
GET /me/profile
Headers:
  X-Tenant-ID: tenant-1
  Authorization: Bearer <token>
```

**Validation (get_current_user):**
1. JWT présent et valide
2. JWT non expiré
3. Utilisateur existe en DB
4. **Cohérence tenant:** `JWT.tenant_id == X-Tenant-ID`

**Réponse:**
```json
{
  "id": 1,
  "email": "dirigeant@example.com",
  "tenant_id": "tenant-1",
  "role": "DIRIGEANT",
  "is_active": true
}
```

## Sécurité

### Validation multi-niveau

1. **Middleware** (`TenantMiddleware`)
   - Valide `X-Tenant-ID` présent (sauf `/health`, `/docs`)
   - Endpoints publics: `/health`, `/docs`, `/openapi.json`

2. **Dependencies** (`get_current_user`)
   - Valide JWT signé et non expiré
   - Charge utilisateur depuis DB
   - **CRITIQUE:** Vérifie `JWT.tenant_id == X-Tenant-ID`

3. **Database**
   - Index composite: `(tenant_id, email)`
   - Contrainte unique: email par tenant
   - Isolation tenant au niveau SQL

### Scénarios de refus

| Scénario | Code | Message |
|----------|------|---------|
| Sans JWT | 403 | "Not authenticated" |
| JWT invalide | 401 | "Invalid or expired token" |
| JWT expiré | 401 | "Invalid or expired token" |
| Tenant incohérent | 403 | "Tenant ID mismatch. Access denied." |
| Utilisateur inexistant | 401 | "Invalid or expired token" |
| Sans X-Tenant-ID | 401 | "Missing X-Tenant-ID header" |

## Tests

### Coverage

**10 tests d'authentification** (`tests/test_auth.py`):

1. ✅ `test_register_creates_user_with_tenant` - Inscription OK
2. ✅ `test_register_rejects_duplicate_email` - Email unique
3. ✅ `test_login_returns_jwt_with_tenant_info` - Login OK
4. ✅ `test_login_fails_with_wrong_password` - Mauvais mot de passe
5. ✅ `test_login_fails_with_unknown_email` - Email inconnu
6. ✅ `test_protected_endpoint_rejects_without_jwt` - Sans JWT
7. ✅ `test_protected_endpoint_rejects_invalid_jwt` - JWT invalide
8. ✅ `test_user_cannot_access_other_tenant_with_jwt` - Autre tenant
9. ✅ `test_jwt_tenant_coherence_validation` - Cohérence tenant
10. ✅ `test_user_can_access_own_tenant_with_valid_jwt` - Accès OK

### Exécution

```bash
docker-compose exec api pytest tests/test_auth.py -v
```

## Migration DB

**Fichier:** `migrations/002_auth.sql`

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'DIRIGEANT',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE UNIQUE INDEX idx_users_email_tenant ON users(tenant_id, email);
```

**Application:**
```bash
docker-compose exec postgres psql -U azals_user -d azals_db -f /migrations/002_auth.sql
```

## Dépendances

```
python-jose[cryptography]==3.3.0  # JWT
bcrypt==4.1.2                     # Hashing
pydantic[email]==2.5.3            # EmailStr validation
```

## Configuration

### Variables d'environnement recommandées

```env
# Production: CHANGER IMPÉRATIVEMENT
JWT_SECRET_KEY="<random-256-bit-key>"
JWT_ALGORITHM="HS256"
JWT_EXPIRE_MINUTES=30

# Base de données
DATABASE_URL="postgresql://user:pass@host/db"
```

### Génération secret key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Exemples d'utilisation

### Curl

```bash
# 1. Inscription
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-1" \
  -d '{"email":"user@example.com","password":"Pass123"}'

# 2. Connexion
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-1" \
  -d '{"email":"user@example.com","password":"Pass123"}' \
  | jq -r '.access_token')

# 3. Accès protégé
curl -X GET http://localhost:8000/me/profile \
  -H "X-Tenant-ID: tenant-1" \
  -H "Authorization: Bearer $TOKEN"
```

### Python

```python
import httpx

# 1. Login
response = httpx.post(
    "http://localhost:8000/auth/login",
    json={"email": "user@example.com", "password": "Pass123"},
    headers={"X-Tenant-ID": "tenant-1"}
)
token = response.json()["access_token"]

# 2. Requête protégée
profile = httpx.get(
    "http://localhost:8000/me/profile",
    headers={
        "X-Tenant-ID": "tenant-1",
        "Authorization": f"Bearer {token}"
    }
)
print(profile.json())
```

## Points d'attention

### ⚠️ Production

1. **SECRET_KEY**: Changer la clé par défaut avec une clé aléatoire 256-bit
2. **HTTPS**: Utiliser HTTPS en production (JWT sensibles)
3. **Expiration**: Adapter la durée selon les besoins (actuellement 30min)
4. **Rate limiting**: Ajouter throttling sur `/auth/login` (brute-force)
5. **Refresh tokens**: Implémenter si sessions longues requises

### ✅ Sécurité appliquée

- ✅ Bcrypt pour hashing (coût 12 rounds par défaut)
- ✅ JWT signés avec HMAC-SHA256
- ✅ Validation cohérence tenant à chaque requête
- ✅ Isolation DB par tenant
- ✅ Email unique par tenant
- ✅ Utilisateurs inactifs refusés
- ✅ Expiration tokens après 30min

## Roadmap

### Features potentielles

- [ ] Refresh tokens
- [ ] Rate limiting login
- [ ] 2FA (TOTP)
- [ ] Rôles supplémentaires (ADMIN, USER)
- [ ] Permissions granulaires
- [ ] Logs d'authentification
- [ ] Reset mot de passe (email)
- [ ] Blacklist tokens révoqués

---

**Version:** 1.0  
**Date:** 2024-01-15  
**Status:** Production Ready ✅
