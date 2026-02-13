# AZALSCORE - Architecture Sécurité Multi-Tenant

**Version:** 1.0.0
**Date:** 2026-02-10
**Classification:** CONFIDENTIEL - ARCHITECTURE

---

## 1. Principe Fondamental

```
RÈGLE ABSOLUE: Les données d'un tenant ne doivent JAMAIS être accessibles
par un autre tenant. L'isolation est garantie à CHAQUE couche du système.
```

---

## 2. Architecture d'Isolation

### 2.1 Couches de Protection

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT (Frontend)                       │
│  Header: X-Tenant-ID: tenant_xxx                            │
│  Header: Authorization: Bearer <JWT avec tenant_id>          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    COUCHE 1: MIDDLEWARE                      │
│  TenantMiddleware: Valide X-Tenant-ID                       │
│  CoreAuthMiddleware: Vérifie JWT.tenant_id == X-Tenant-ID   │
│  RBACMiddleware: Vérifie permissions tenant-scoped          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    COUCHE 2: ENDPOINTS                       │
│  get_current_user(): Vérifie user.tenant_id == request      │
│  get_tenant_id(): Injecte tenant_id validé                  │
│  get_tenant_db(): Active RLS + injecte contexte             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    COUCHE 3: SERVICES                        │
│  @enforce_tenant_isolation: Vérifie service.tenant_id       │
│  Toutes les requêtes: .filter(tenant_id == self.tenant_id)  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    COUCHE 4: DATABASE                        │
│  Row Level Security (RLS): Filtre automatique par tenant    │
│  Index: (tenant_id, ...) sur toutes les tables             │
│  Contrainte: tenant_id NOT NULL sur toutes les tables       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Defense in Depth

Chaque couche est indépendante. Si une couche échoue, les autres protègent:

| Couche | Protection | Si échoue... |
|--------|------------|--------------|
| Middleware | Valide headers | Endpoint vérifie aussi |
| Endpoint | Vérifie JWT | Service vérifie aussi |
| Service | Filtre requêtes | RLS filtre aussi |
| Database | RLS auto-filtre | Dernière ligne de défense |

---

## 3. Implémentation

### 3.1 Middleware Tenant

```python
# app/core/middleware.py
class TenantMiddleware:
    async def dispatch(self, request: Request, call_next):
        tenant_id = request.headers.get("X-Tenant-ID")

        if not tenant_id:
            raise HTTPException(401, "Missing X-Tenant-ID")

        # Valider format tenant_id
        if not self.is_valid_tenant_id(tenant_id):
            raise HTTPException(400, "Invalid tenant ID format")

        # Injecter dans request.state
        request.state.tenant_id = tenant_id

        return await call_next(request)
```

### 3.2 Dépendance Endpoint

```python
# app/core/dependencies.py
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
) -> User:
    payload = decode_access_token(credentials.credentials)

    # CRITIQUE: Vérifier cohérence tenant JWT vs Header
    if payload["tenant_id"] != tenant_id:
        raise HTTPException(403, "Tenant mismatch")

    user = db.query(User).filter(User.id == payload["sub"]).first()

    # CRITIQUE: Vérifier cohérence tenant User vs Header
    if user.tenant_id != tenant_id:
        raise HTTPException(403, "Tenant mismatch")

    return user
```

### 3.3 Décorateur Service

```python
# app/core/dependencies.py
def enforce_tenant_isolation(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'tenant_id') or not self.tenant_id:
            raise TenantIsolationError("tenant_id required")
        return func(self, *args, **kwargs)
    return wrapper

# Usage dans un service
class InvoiceService:
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    @enforce_tenant_isolation
    def get_invoices(self):
        return self.db.query(Invoice).filter(
            Invoice.tenant_id == self.tenant_id  # OBLIGATOIRE
        ).all()
```

### 3.4 Row Level Security (PostgreSQL)

```sql
-- Activer RLS sur toutes les tables
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

-- Politique de filtrage
CREATE POLICY tenant_isolation ON invoices
    USING (tenant_id = current_setting('app.current_tenant')::text);

-- Le contexte est défini à chaque connexion
SET app.current_tenant = 'tenant_xxx';
```

```python
# app/core/database.py
def set_rls_context(db: Session, tenant_id: str):
    """Active le contexte RLS pour la session."""
    db.execute(text(f"SET app.current_tenant = :tenant_id"),
               {"tenant_id": tenant_id})
```

---

## 4. Patterns Obligatoires

### 4.1 Pattern CORRECT

```python
# ✅ CORRECT - Toujours filtrer par tenant_id
def get_items(self) -> List[Item]:
    return self.db.query(Item).filter(
        Item.tenant_id == self.tenant_id
    ).all()

# ✅ CORRECT - Avec décorateur
@enforce_tenant_isolation
def get_items(self) -> List[Item]:
    return self.db.query(Item).filter(
        Item.tenant_id == self.tenant_id
    ).all()
```

### 4.2 Pattern INTERDIT

```python
# ❌ INTERDIT - Pas de filtre tenant_id
def get_all_items(self) -> List[Item]:
    return self.db.query(Item).all()  # DANGER!

# ❌ INTERDIT - Filtre dynamique contournable
def get_items(self, tenant_override=None) -> List[Item]:
    tenant = tenant_override or self.tenant_id  # DANGER!
    return self.db.query(Item).filter(...).all()

# ❌ INTERDIT - SQL brut sans paramètre
def get_items(self):
    query = f"SELECT * FROM items WHERE tenant_id = '{self.tenant_id}'"  # SQL INJECTION!
    return self.db.execute(query).fetchall()
```

---

## 5. Vérification et Audit

### 5.1 Script de Scan

```bash
# Scanner le code pour violations potentielles
python scripts/security/scan_tenant_isolation.py --strict

# Résultat attendu en CI/CD
✅ AUCUNE VIOLATION DÉTECTÉE
   Fichiers analysés: 150
   Score: 100/100
```

### 5.2 Tests Automatisés

```bash
# Tests d'isolation tenant
pytest tests/integration/test_tenant_isolation.py -v

# Tests de sécurité
pytest tests/security/test_security_real.py -v
```

### 5.3 Audit Manuel

| Vérification | Fréquence | Responsable |
|--------------|-----------|-------------|
| Scan code tenant_id | Chaque PR | CI/CD |
| Tests isolation | Chaque PR | CI/CD |
| Revue manuelle | Mensuel | Équipe sécurité |
| Pentest externe | Annuel | Prestataire |

---

## 6. Gestion des Exceptions

### 6.1 Endpoints Sans Tenant

Certains endpoints légitimes n'ont pas de tenant_id:

```python
# Exemples d'endpoints exemptés
TENANT_EXEMPT_ROUTES = [
    "/health",           # Health check
    "/metrics",          # Prometheus metrics
    "/auth/login",       # Connexion (avant tenant connu)
    "/auth/register",    # Inscription
    "/docs",             # Documentation API
]
```

### 6.2 Marqueur d'Exemption

```python
# Pour les requêtes internes légitimes sans tenant
# UTILISER AVEC EXTRÊME PRUDENCE

# ✅ Commentaire explicite
# TENANT_EXEMPT: Cette requête agrège des stats système, pas de données tenant
stats = db.query(func.count(User.id)).scalar()

# ✅ Fonction dédiée avec audit
@audit_tenant_exempt(reason="System stats aggregation")
def get_system_stats():
    ...
```

---

## 7. Réponses aux Incidents

### 7.1 Si Fuite de Données Détectée

1. **IMMÉDIAT (<5 min)**
   - Bloquer l'accès au tenant concerné
   - Notifier l'équipe sécurité

2. **COURT TERME (<1h)**
   - Analyser les logs d'audit
   - Identifier l'étendue de la fuite
   - Préparer la communication

3. **SUIVI**
   - Post-mortem complet
   - Correction du code
   - Notification RGPD si applicable

### 7.2 Codes d'Erreur

| Situation | Code HTTP | Message |
|-----------|-----------|---------|
| Données autre tenant | 404 | "Resource not found" |
| JWT/Header mismatch | 403 | "Tenant mismatch" |
| tenant_id manquant | 401 | "Missing X-Tenant-ID" |

**IMPORTANT:** Retourner 404 pour les données d'autres tenants, pas 403.
Un 403 révèle que la ressource existe, ce qui est une fuite d'information.

---

## 8. Checklist Développeur

Avant chaque PR touchant aux données:

- [ ] Toutes les requêtes filtrent par `tenant_id`
- [ ] Le décorateur `@enforce_tenant_isolation` est utilisé
- [ ] Pas de SQL brut avec interpolation de chaînes
- [ ] Pas de paramètre `tenant_override` dans les fonctions
- [ ] Tests d'isolation passent
- [ ] Scan `scan_tenant_isolation.py` clean

---

*Document de gouvernance AZALSCORE*
*Classification: CONFIDENTIEL - ARCHITECTURE*
