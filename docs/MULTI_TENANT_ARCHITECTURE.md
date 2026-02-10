# 🏢 AZALSCORE - Architecture Multi-Tenant Production

## Concept

**1 Entreprise cliente = 1 Tenant isolé**

```
┌─────────────────────────────────────────────────────────────┐
│                    AZALSCORE SaaS                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │   Tenant    │  │   Tenant    │  │   Tenant    │   ...  │
│   │ acme-corp   │  │ dupont-sa   │  │ martin-sarl │        │
│   ├─────────────┤  ├─────────────┤  ├─────────────┤        │
│   │ 5 users     │  │ 12 users    │  │ 3 users     │        │
│   │ Plan Pro    │  │ Plan Ent.   │  │ Plan Start  │        │
│   │ CRM, Compta │  │ Tous modules│  │ CRM basique │        │
│   └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│   ════════════════════════════════════════════════════      │
│   │         ISOLATION STRICTE DES DONNÉES            │      │
│   ════════════════════════════════════════════════════      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Flux d'inscription

```
1. Visiteur arrive sur azalscore.com
                ↓
2. Clique "Essai gratuit"
                ↓
3. Formulaire d'inscription:
   - Nom entreprise: "Acme Corporation"
   - Email entreprise
   - Infos admin
                ↓
4. Création automatique:
   - tenant_id: "acme-corporation" (slug unique)
   - Espace isolé dans la DB
   - Admin avec mot de passe
   - Trial 14 jours activé
   - Modules selon plan
                ↓
5. Email de bienvenue
                ↓
6. Redirection vers /login?tenant=acme-corporation
```

---

## Génération du tenant_id

| Nom entreprise | tenant_id généré |
|----------------|------------------|
| Acme Corporation | `acme-corporation` |
| L'Épicerie du Coin | `lepicerie-du-coin` |
| SAS DUPONT & Fils | `sas-dupont-fils` |
| 株式会社テスト | `tenant-a1b2c3d4` (fallback) |
| Acme Corp (doublon) | `acme-corp-2` |

**Règles:**
- Minuscules
- Accents supprimés
- Caractères spéciaux supprimés
- Espaces → tirets
- Maximum 40 caractères
- Suffixe numérique si doublon

---

## Isolation des données

### Au niveau base de données

Chaque table métier a une colonne `tenant_id`:

```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,  -- ← Isolation
    name VARCHAR(255),
    ...
    CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

-- Index pour performance
CREATE INDEX idx_clients_tenant ON clients(tenant_id);
```

### Au niveau applicatif

```python
# Middleware automatique - CHAQUE requête
class TenantMiddleware:
    async def dispatch(self, request, call_next):
        tenant_id = request.headers.get("X-Tenant-ID")
        
        # Injecter dans le contexte
        request.state.tenant_id = tenant_id
        
        # Toutes les queries sont filtrées automatiquement
        return await call_next(request)

# Dans les services
def get_clients(db, tenant_id):
    return db.query(Client).filter(
        Client.tenant_id == tenant_id  # ← TOUJOURS filtré
    ).all()
```

### Au niveau JWT

```json
{
  "sub": "user-uuid",
  "tenant_id": "acme-corporation",  // ← Inclus dans le token
  "role": "admin",
  "exp": 1234567890
}
```

**Double vérification:**
1. `tenant_id` dans le header X-Tenant-ID
2. `tenant_id` dans le JWT
3. Les deux doivent correspondre → sinon 403

---

## Plans et limites

| Plan | Users | Stockage | Modules | Prix |
|------|-------|----------|---------|------|
| **Starter** | 5 | 10 Go | CRM, Compta basique | 49€/mois |
| **Professional** | 25 | 50 Go | Tous modules métier | 149€/mois |
| **Enterprise** | ∞ | 500 Go | + IA + BI | 499€/mois |

### Vérifications automatiques

```python
# Avant création d'utilisateur
@app.post("/users")
def create_user(tenant: Tenant = Depends(get_tenant_with_status)):
    # Vérifie automatiquement:
    # - Tenant actif (pas suspendu)
    # - Trial non expiré
    # - Limite users non atteinte
    ...

# Avant accès à un module
@app.get("/production/orders")
def list_orders(tenant: Tenant = Depends(get_tenant_with_status)):
    # Vérifie que le module M6 (Production) est activé
    ...
```

---

## Endpoints publics

| Endpoint | Description |
|----------|-------------|
| `POST /signup` | Inscription nouvelle entreprise |
| `GET /signup/check-email?email=x` | Vérifier disponibilité email |
| `GET /signup/check-company?name=x` | Vérifier disponibilité nom |
| `GET /signup/plans` | Liste des plans disponibles |
| `POST /auth/login` | Connexion |
| `POST /webhooks/stripe` | Webhooks Stripe |

---

## Cycle de vie d'un tenant

```
PENDING → TRIAL → ACTIVE → (SUSPENDED) → CANCELLED
   │         │        │          │
   │         │        │          └── Impayé / Annulation
   │         │        │
   │         │        └── Paiement reçu
   │         │
   │         └── 14 jours d'essai
   │
   └── Inscription créée
```

### Blocages automatiques

| Statut | Accès API | Message |
|--------|-----------|---------|
| `TRIAL` (valide) | ✅ | - |
| `TRIAL` (expiré) | ❌ | "Essai terminé, souscrivez" |
| `ACTIVE` | ✅ | - |
| `SUSPENDED` | ❌ | "Paiement requis" |
| `CANCELLED` | ❌ | "Compte annulé" |

---

## Exemple complet

### 1. Inscription
```bash
POST /signup
{
  "company_name": "Boulangerie Martin",
  "company_email": "contact@boulangerie-martin.fr",
  "admin_email": "pierre@boulangerie-martin.fr",
  "admin_password": "SecurePass123!",
  "admin_first_name": "Pierre",
  "admin_last_name": "Martin",
  "plan": "STARTER",
  "accept_terms": true,
  "accept_privacy": true
}

# Réponse
{
  "success": true,
  "tenant_id": "boulangerie-martin",
  "trial_ends_at": "2025-01-26T14:30:00Z",
  "login_url": "/login?tenant=boulangerie-martin"
}
```

### 2. Connexion
```bash
POST /auth/login
X-Tenant-ID: boulangerie-martin
{
  "email": "pierre@boulangerie-martin.fr",
  "password": "SecurePass123!"
}

# Réponse
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### 3. Utilisation API
```bash
GET /v1/clients
Authorization: Bearer eyJ...
X-Tenant-ID: boulangerie-martin

# Retourne UNIQUEMENT les clients de boulangerie-martin
```

---

## Supervision multi-tenant (Super Admin)

Endpoint réservé aux super_admin AZALSCORE:

```bash
GET /v1/admin/tenants
Authorization: Bearer <super_admin_token>

# Liste tous les tenants de la plateforme
{
  "tenants": [
    {"tenant_id": "boulangerie-martin", "status": "TRIAL", "plan": "STARTER"},
    {"tenant_id": "acme-corp", "status": "ACTIVE", "plan": "PROFESSIONAL"},
    ...
  ],
  "stats": {
    "total": 150,
    "active": 120,
    "trial": 25,
    "suspended": 5
  }
}
```

---

## Résumé

| Aspect | Implémentation |
|--------|----------------|
| Isolation données | `tenant_id` sur chaque table |
| Authentification | JWT avec `tenant_id` |
| Autorisation | RBAC 5 niveaux par tenant |
| Inscription | Formulaire public → tenant auto |
| Nommage tenant | Slug du nom entreprise |
| Limites | Vérifiées en temps réel |
| Blocage impayé | Middleware automatique |
| Audit | Par tenant, append-only |

**✅ PRÊT POUR PRODUCTION MULTI-TENANT**
