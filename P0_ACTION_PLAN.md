# AZALSCORE - Plan d'Action P0 (Bloquants Critiques)

**Date:** 2026-01-23
**Version:** 1.0.0
**Durée totale estimée:** 8-12 semaines
**Équipe requise:** 2-3 développeurs seniors

---

## 📋 RÉSUMÉ EXÉCUTIF

**Objectif:** Résoudre les 10 bloquants critiques (P0) empêchant la mise en production sécurisée d'AZALSCORE.

**Priorité absolue:** Ces tâches sont **BLOQUANTES** pour production avec clients payants.

**Ordre d'exécution:** Parallélisable quand possible, séquentiel quand dépendances.

---

## 🎯 ORDRE DE PRIORITÉ

### Vague 1 (Semaines 1-3) - Sécurité Fondamentale
1. Secrets Management (Vault)
2. Multi-Tenant Validation
3. Rate Limiting par Tenant

### Vague 2 (Semaines 4-6) - Fiabilité Infrastructure
4. Migration Rollback Strategy
5. Backup & Disaster Recovery
6. Alerting & Monitoring

### Vague 3 (Semaines 7-9) - Qualité Code & Sécurité Client
7. Try/Catch Refactoring
8. localStorage → httpOnly Cookies
9. Tests Security & Quality

### Vague 4 (Semaines 10-12) - Validation Finale
10. Audit Sécurité Externe
11. Load Testing
12. Production Readiness Review

---

## 🔴 P0-1: SECRETS MANAGEMENT (VAULT)

### Problème Actuel
```bash
# .env (DANGEREUX):
DATABASE_URL=postgresql://user:password@host/db
SECRET_KEY=my-super-secret-key-32-chars
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
ENCRYPTION_KEY=fernet-key-base64

# Risques:
- Secrets en clair dans fichiers
- Pas de rotation
- Pas d'audit accès secrets
- Breach = game over
```

### Plan d'Action

#### Étape 1.1: Choisir Solution Vault (1 jour)

**Options:**

| Solution | Coût | Complexité | SaaS |
|----------|------|------------|------|
| **HashiCorp Vault** | Free tier | Haute | Self-hosted |
| **AWS Secrets Manager** | $0.40/secret/mois | Moyenne | ✅ |
| **GCP Secret Manager** | $0.06/secret/mois | Moyenne | ✅ |
| **Azure Key Vault** | $0.03/secret | Moyenne | ✅ |

**Recommandation:** AWS Secrets Manager (si déjà sur AWS) ou HashiCorp Vault (vendor-neutral)

**Décision requise:** Choix à faire par équipe DevOps

#### Étape 1.2: Setup Vault (2-3 jours)

**Si AWS Secrets Manager:**

```bash
# 1. Créer secrets dans AWS
aws secretsmanager create-secret \
  --name azalscore/prod/database-url \
  --secret-string "postgresql://..."

aws secretsmanager create-secret \
  --name azalscore/prod/secret-key \
  --secret-string "..." \
  --tags Key=Environment,Value=production

# 2. IAM Role pour application
aws iam create-role \
  --role-name AzalscoreAppRole \
  --assume-role-policy-document file://trust-policy.json

# 3. Policy permettant lecture secrets
aws iam put-role-policy \
  --role-name AzalscoreAppRole \
  --policy-name SecretsReadPolicy \
  --policy-document file://secrets-policy.json
```

**Si HashiCorp Vault:**

```bash
# 1. Install Vault
docker run -d --name=vault -p 8200:8200 \
  vault:latest server -dev

# 2. Initialize & Unseal
vault operator init
vault operator unseal [key1]
vault operator unseal [key2]
vault operator unseal [key3]

# 3. Enable secrets engine
vault secrets enable -path=azalscore kv-v2

# 4. Write secrets
vault kv put azalscore/prod/database \
  url="postgresql://..."
```

#### Étape 1.3: Code Integration (3-4 jours)

```python
# app/core/secrets.py (NOUVEAU)
from typing import Optional
import boto3
from botocore.exceptions import ClientError
import os
from functools import lru_cache

class SecretsManager:
    def __init__(self):
        if os.getenv("SECRETS_BACKEND") == "aws":
            self.client = boto3.client('secretsmanager')
            self.backend = "aws"
        elif os.getenv("SECRETS_BACKEND") == "vault":
            import hvac
            self.client = hvac.Client(url=os.getenv("VAULT_ADDR"))
            self.client.token = os.getenv("VAULT_TOKEN")
            self.backend = "vault"
        else:
            raise ValueError("SECRETS_BACKEND must be 'aws' or 'vault'")

    @lru_cache(maxsize=128)
    def get_secret(self, secret_name: str) -> str:
        """
        Retrieve secret from vault with caching.
        Cache TTL = 5 minutes (adjust based on rotation frequency)
        """
        try:
            if self.backend == "aws":
                response = self.client.get_secret_value(SecretId=secret_name)
                return response['SecretString']

            elif self.backend == "vault":
                secret = self.client.secrets.kv.v2.read_secret_version(
                    path=secret_name
                )
                return secret['data']['data']['value']

        except ClientError as e:
            # Log error to audit trail
            print(f"Failed to retrieve secret {secret_name}: {e}")
            raise

    def invalidate_cache(self):
        """Clear cache after secret rotation"""
        self.get_secret.cache_clear()

# Singleton instance
secrets_manager = SecretsManager()

# Helper function
def get_secret(name: str) -> str:
    return secrets_manager.get_secret(name)
```

```python
# app/core/config.py (MODIFIER)
from pydantic_settings import BaseSettings
from app.core.secrets import get_secret
import os

class Settings(BaseSettings):

    @property
    def database_url(self) -> str:
        if os.getenv("ENV") == "prod":
            return get_secret("azalscore/prod/database-url")
        return os.getenv("DATABASE_URL", "postgresql://localhost/azals_dev")

    @property
    def secret_key(self) -> str:
        if os.getenv("ENV") == "prod":
            return get_secret("azalscore/prod/secret-key")
        return os.getenv("SECRET_KEY", "dev-secret-key-not-secure")

    @property
    def stripe_secret_key(self) -> str:
        if os.getenv("ENV") == "prod":
            return get_secret("azalscore/prod/stripe-secret-key")
        return os.getenv("STRIPE_SECRET_KEY", "sk_test_...")

    # ... autres secrets

settings = Settings()
```

#### Étape 1.4: Migration Secrets (1 jour)

```bash
# Script de migration
#!/bin/bash
# scripts/migrate-secrets-to-vault.sh

set -e

echo "Migrating secrets to AWS Secrets Manager..."

# Database
aws secretsmanager create-secret \
  --name azalscore/prod/database-url \
  --secret-string "$PROD_DATABASE_URL"

# Secret Key
aws secretsmanager create-secret \
  --name azalscore/prod/secret-key \
  --secret-string "$PROD_SECRET_KEY"

# Stripe
aws secretsmanager create-secret \
  --name azalscore/prod/stripe-secret-key \
  --secret-string "$PROD_STRIPE_SECRET_KEY"

# Encryption Key
aws secretsmanager create-secret \
  --name azalscore/prod/encryption-key \
  --secret-string "$PROD_ENCRYPTION_KEY"

echo "✅ Secrets migrated successfully"
echo "⚠️  DELETE .env file and rotate all secrets!"
```

#### Étape 1.5: Rotation Strategy (2 jours)

```python
# scripts/rotate-secrets.py
import boto3
import secrets
import string
from datetime import datetime

def generate_secret_key(length: int = 64) -> str:
    """Generate cryptographically secure secret"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def rotate_secret(secret_name: str, new_value: str):
    """Rotate secret with version tracking"""
    client = boto3.client('secretsmanager')

    # Update secret
    response = client.update_secret(
        SecretId=secret_name,
        SecretString=new_value,
        Description=f"Rotated on {datetime.utcnow().isoformat()}"
    )

    # Invalidate cache
    from app.core.secrets import secrets_manager
    secrets_manager.invalidate_cache()

    print(f"✅ Rotated {secret_name}, version: {response['VersionId']}")

# Rotation schedule (run monthly via cron)
def rotate_all_secrets():
    secrets_to_rotate = [
        "azalscore/prod/secret-key",
        # Add other secrets that can be rotated
        # DON'T rotate database password without coordination
    ]

    for secret_name in secrets_to_rotate:
        new_value = generate_secret_key()
        rotate_secret(secret_name, new_value)
```

**Cron job (monthly rotation):**
```bash
# crontab -e
0 2 1 * * /usr/bin/python /app/scripts/rotate-secrets.py
```

#### Étape 1.6: Audit Logging (1 jour)

```python
# app/core/secrets.py (AJOUTER)
import logging
from app.services.journal import log_audit

def get_secret(name: str) -> str:
    # Log access to audit trail
    log_audit(
        action="SECRET_ACCESS",
        entity_type="secret",
        entity_id=name,
        details={"timestamp": datetime.utcnow().isoformat()}
    )

    return secrets_manager.get_secret(name)
```

### Tests de Validation

```python
# tests/core/test_secrets.py
import pytest
from unittest.mock import patch, MagicMock

def test_get_secret_from_aws():
    with patch('boto3.client') as mock_boto:
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            'SecretString': 'test-secret-value'
        }
        mock_boto.return_value = mock_client

        from app.core.secrets import get_secret
        result = get_secret("test/secret")

        assert result == 'test-secret-value'
        mock_client.get_secret_value.assert_called_once()

def test_secret_cache():
    """Verify secrets are cached"""
    with patch('boto3.client') as mock_boto:
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            'SecretString': 'cached-value'
        }
        mock_boto.return_value = mock_client

        from app.core.secrets import get_secret

        # First call
        result1 = get_secret("test/secret")
        # Second call (should use cache)
        result2 = get_secret("test/secret")

        # Only called once due to cache
        assert mock_client.get_secret_value.call_count == 1
        assert result1 == result2
```

### Critères de Succès

- ✅ Aucun secret en clair dans .env
- ✅ Tous secrets en vault (AWS/HashiCorp)
- ✅ Rotation mensuelle automatisée
- ✅ Audit trail accès secrets
- ✅ Tests unitaires passent
- ✅ .env.example seulement (pas .env en Git)

### Temps Estimé: **2 semaines**

### Ressources: 1 DevOps + 1 Backend Dev

---

## 🔴 P0-2: MULTI-TENANT VALIDATION RUNTIME

### Problème Actuel

```python
# Code actuel (DANGEREUX):
def get_invoice(invoice_id: str, tenant_id: str):
    # Assume tenant_id est valide
    return db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.tenant_id == tenant_id
    ).first()  # ← Retourne None si tenant invalide (silencieux)

# Risques:
- Manipulation header X-Tenant-ID
- Tenant supprimé = données orphelines
- Pas de vérification existence tenant
- Fuite de données potentielle
```

### Plan d'Action

#### Étape 2.1: Créer Table Tenants (1 jour)

```python
# alembic/versions/20260124_001_create_tenants_table.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=False,
                  server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  onupdate=sa.text('now()')),
        sa.Column('settings', postgresql.JSONB, server_default='{}'),
        sa.Column('max_users', sa.Integer, server_default='10'),
        sa.Column('max_storage_gb', sa.Integer, server_default='5'),
    )

    # Indexes
    op.create_index('idx_tenants_status', 'tenants', ['status'])
    op.create_index('idx_tenants_created', 'tenants', ['created_at'])

def downgrade():
    op.drop_table('tenants')
```

```python
# app/models/tenant.py (NOUVEAU)
from sqlalchemy import Column, String, Integer, DateTime, Enum
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base
import enum

class TenantStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    status = Column(Enum(TenantStatus), nullable=False, default=TenantStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    settings = Column(JSONB, default={})
    max_users = Column(Integer, default=10)
    max_storage_gb = Column(Integer, default=5)
```

#### Étape 2.2: Ajouter Foreign Keys (2-3 jours)

```python
# alembic/versions/20260124_002_add_tenant_fk.py
def upgrade():
    # Ajouter FK à TOUTES les tables avec tenant_id

    tables_with_tenant_id = [
        'users', 'invoices', 'quotes', 'customers',
        'products', 'orders', 'interventions',
        # ... 40+ autres tables
    ]

    for table_name in tables_with_tenant_id:
        # Supprimer données orphelines d'abord
        op.execute(f"""
            DELETE FROM {table_name}
            WHERE tenant_id NOT IN (SELECT id FROM tenants)
        """)

        # Ajouter FK constraint
        op.create_foreign_key(
            f'fk_{table_name}_tenant_id',
            table_name, 'tenants',
            ['tenant_id'], ['id'],
            ondelete='CASCADE'  # Cascade deletion
        )

def downgrade():
    for table_name in tables_with_tenant_id:
        op.drop_constraint(f'fk_{table_name}_tenant_id', table_name)
```

**⚠️ ATTENTION:** Migration potentiellement longue (40+ tables)
- Exécuter en heures creuses
- Backup DB avant migration
- Test sur staging d'abord

#### Étape 2.3: Tenant Validation Middleware (2 jours)

```python
# app/middleware/tenant_validation.py (NOUVEAU)
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.models.tenant import Tenant, TenantStatus
from app.core.database import get_db
from functools import lru_cache
import time

# Cache tenant validation (5 minutes)
TENANT_CACHE = {}
CACHE_TTL = 300  # 5 minutes

@lru_cache(maxsize=1000)
def is_tenant_valid(tenant_id: str, db) -> bool:
    """
    Validate tenant exists and is active.
    Cached for performance.
    """
    cache_key = f"tenant:{tenant_id}"
    cached = TENANT_CACHE.get(cache_key)

    if cached and (time.time() - cached['timestamp']) < CACHE_TTL:
        return cached['valid']

    # Query DB
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    valid = tenant is not None and tenant.status == TenantStatus.ACTIVE

    # Cache result
    TENANT_CACHE[cache_key] = {
        'valid': valid,
        'timestamp': time.time()
    }

    return valid

class TenantValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip validation pour endpoints publics
        public_paths = ['/health', '/docs', '/openapi.json', '/auth/login']
        if request.url.path in public_paths:
            return await call_next(request)

        # Extract tenant_id from header
        tenant_id = request.headers.get('X-Tenant-ID')

        if not tenant_id:
            raise HTTPException(
                status_code=400,
                detail="Missing X-Tenant-ID header"
            )

        # Validate tenant
        db = next(get_db())
        try:
            if not is_tenant_valid(tenant_id, db):
                raise HTTPException(
                    status_code=403,
                    detail=f"Invalid or inactive tenant: {tenant_id}"
                )
        finally:
            db.close()

        # Attach tenant to request state
        request.state.tenant_id = tenant_id
        request.state.tenant_validated = True

        return await call_next(request)
```

```python
# app/main.py (MODIFIER)
from app.middleware.tenant_validation import TenantValidationMiddleware

app = FastAPI()

# Add middleware (AVANT TenantMiddleware existant)
app.add_middleware(TenantValidationMiddleware)
```

#### Étape 2.4: Helper Function Sécurisée (1 jour)

```python
# app/core/tenant.py (NOUVEAU)
from fastapi import Request, HTTPException

def get_validated_tenant_id(request: Request) -> str:
    """
    Get tenant_id from request, garantissant qu'il a été validé.
    Utiliser dans TOUS les endpoints.
    """
    if not hasattr(request.state, 'tenant_validated'):
        raise HTTPException(
            status_code=500,
            detail="Tenant validation middleware not executed"
        )

    if not request.state.tenant_validated:
        raise HTTPException(
            status_code=403,
            detail="Tenant validation failed"
        )

    return request.state.tenant_id
```

```python
# Utilisation dans endpoints (EXEMPLE):
from fastapi import APIRouter, Depends, Request
from app.core.tenant import get_validated_tenant_id

router = APIRouter()

@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    # Tenant déjà validé par middleware
    tenant_id = get_validated_tenant_id(request)

    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.tenant_id == tenant_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return invoice
```

#### Étape 2.5: Cascade Deletion Strategy (1 jour)

```python
# app/services/tenant_service.py (NOUVEAU)
from app.models.tenant import Tenant, TenantStatus
from sqlalchemy.orm import Session

def soft_delete_tenant(tenant_id: str, db: Session):
    """
    Soft delete: Marquer tenant comme DELETED
    Données conservées mais inaccessibles
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise ValueError(f"Tenant {tenant_id} not found")

    # Soft delete
    tenant.status = TenantStatus.DELETED
    db.commit()

    # Invalider cache
    from app.middleware.tenant_validation import TENANT_CACHE
    TENANT_CACHE.pop(f"tenant:{tenant_id}", None)

    # Log audit
    from app.services.journal import log_audit
    log_audit(
        action="TENANT_DELETED",
        entity_type="tenant",
        entity_id=tenant_id,
        details={"soft_delete": True}
    )

def hard_delete_tenant(tenant_id: str, db: Session):
    """
    Hard delete: Suppression CASCADE de toutes les données
    ⚠️ IRREVERSIBLE - Utiliser avec EXTREME précaution
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise ValueError(f"Tenant {tenant_id} not found")

    # Log avant suppression
    from app.services.journal import log_audit
    log_audit(
        action="TENANT_HARD_DELETE",
        entity_type="tenant",
        entity_id=tenant_id,
        details={"warning": "CASCADE deletion of all data"}
    )

    # Hard delete (CASCADE via FK)
    db.delete(tenant)
    db.commit()

    # Invalider cache
    from app.middleware.tenant_validation import TENANT_CACHE
    TENANT_CACHE.pop(f"tenant:{tenant_id}", None)
```

### Tests de Validation

```python
# tests/middleware/test_tenant_validation.py
import pytest
from fastapi.testclient import TestClient

def test_missing_tenant_header(client: TestClient):
    response = client.get("/invoices/123")
    assert response.status_code == 400
    assert "Missing X-Tenant-ID" in response.json()['detail']

def test_invalid_tenant(client: TestClient, db_session):
    response = client.get(
        "/invoices/123",
        headers={"X-Tenant-ID": "invalid-tenant-id"}
    )
    assert response.status_code == 403
    assert "Invalid or inactive tenant" in response.json()['detail']

def test_deleted_tenant(client: TestClient, db_session):
    # Create tenant
    tenant = Tenant(id="test-tenant", status=TenantStatus.DELETED)
    db_session.add(tenant)
    db_session.commit()

    response = client.get(
        "/invoices/123",
        headers={"X-Tenant-ID": "test-tenant"}
    )
    assert response.status_code == 403

def test_valid_tenant(client: TestClient, db_session, sample_invoice):
    # Create active tenant
    tenant = Tenant(id="active-tenant", status=TenantStatus.ACTIVE)
    db_session.add(tenant)
    db_session.commit()

    response = client.get(
        f"/invoices/{sample_invoice.id}",
        headers={"X-Tenant-ID": "active-tenant"}
    )
    assert response.status_code == 200
```

### Critères de Succès

- ✅ Table `tenants` créée
- ✅ Foreign keys sur TOUTES les tables
- ✅ Middleware validation active
- ✅ Cache validation (performance)
- ✅ Soft delete implémenté
- ✅ Tests unitaires + intégration passent
- ✅ Aucune requête sans validation tenant

### Temps Estimé: **2 semaines**

### Ressources: 1 Backend Dev Senior

---

## 🔴 P0-3: RATE LIMITING PAR TENANT

### Problème Actuel

```python
# Configuration actuelle:
- 100 req/min GLOBAL (tous tenants confondus)
- 5 req/min pour /auth/* GLOBAL
- Un tenant peut consommer tous les quotas
- DoS facile
```

### Plan d'Action

#### Étape 3.1: Install Redis Rate Limiter (1 jour)

```python
# requirements.txt (AJOUTER)
slowapi==0.1.9
redis==5.0.1
```

```python
# app/core/rate_limit.py (NOUVEAU)
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
import redis
from typing import Callable

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

def get_tenant_key(request: Request) -> str:
    """
    Key function pour rate limiting par tenant.
    Format: tenant:{tenant_id}
    """
    tenant_id = request.headers.get("X-Tenant-ID", "anonymous")
    return f"tenant:{tenant_id}"

# Limiter configuré pour rate limit par tenant
limiter = Limiter(
    key_func=get_tenant_key,
    storage_uri=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379"
)
```

#### Étape 3.2: Configurer Limits par Endpoint (2 jours)

```python
# app/api/rate_limits.py (NOUVEAU)
from dataclasses import dataclass

@dataclass
class RateLimitConfig:
    endpoint_type: str
    limit: str  # Format: "X/period" (e.g., "100/minute")
    burst: int  # Burst allowance

# Configuration par type d'endpoint
RATE_LIMITS = {
    # Auth endpoints (strict)
    "auth_login": RateLimitConfig("auth", "5/minute", burst=2),
    "auth_register": RateLimitConfig("auth", "3/hour", burst=1),
    "auth_2fa": RateLimitConfig("auth", "10/minute", burst=3),

    # Read operations (permissif)
    "read": RateLimitConfig("read", "1000/minute", burst=100),

    # Write operations (modéré)
    "write": RateLimitConfig("write", "500/minute", burst=50),

    # Heavy operations (strict)
    "reports": RateLimitConfig("heavy", "10/minute", burst=2),
    "exports": RateLimitConfig("heavy", "20/hour", burst=5),

    # API webhooks (très strict)
    "webhook": RateLimitConfig("webhook", "100/minute", burst=10),
}
```

```python
# Utilisation dans routes (EXEMPLE):
from fastapi import APIRouter
from app.core.rate_limit import limiter
from app.api.rate_limits import RATE_LIMITS

router = APIRouter()

@router.post("/auth/login")
@limiter.limit(RATE_LIMITS["auth_login"].limit)
async def login(request: Request, credentials: LoginSchema):
    # Login logic
    pass

@router.get("/invoices")
@limiter.limit(RATE_LIMITS["read"].limit)
async def list_invoices(request: Request):
    # List logic
    pass

@router.post("/invoices")
@limiter.limit(RATE_LIMITS["write"].limit)
async def create_invoice(request: Request, invoice: InvoiceSchema):
    # Create logic
    pass

@router.get("/reports/monthly")
@limiter.limit(RATE_LIMITS["reports"].limit)
async def monthly_report(request: Request):
    # Heavy computation
    pass
```

#### Étape 3.3: Backoff Exponentiel (1 jour)

```python
# app/middleware/rate_limit_backoff.py (NOUVEAU)
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
import redis

redis_client = redis.Redis(decode_responses=True)

class ExponentialBackoffMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        tenant_id = request.headers.get("X-Tenant-ID", "anonymous")
        backoff_key = f"backoff:{tenant_id}"

        # Check if tenant is in backoff
        backoff_until = redis_client.get(backoff_key)

        if backoff_until:
            backoff_until = float(backoff_until)
            if time.time() < backoff_until:
                retry_after = int(backoff_until - time.time())
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Retry after {retry_after}s",
                    headers={"Retry-After": str(retry_after)}
                )

        response = await call_next(request)

        # Si rate limit dépassé (429), activer backoff
        if response.status_code == 429:
            # Incrémenter backoff
            violation_count_key = f"violations:{tenant_id}"
            violations = redis_client.incr(violation_count_key)
            redis_client.expire(violation_count_key, 3600)  # Reset après 1h

            # Backoff exponentiel: 2^violations secondes
            backoff_seconds = min(2 ** violations, 3600)  # Max 1h
            backoff_until = time.time() + backoff_seconds

            redis_client.setex(backoff_key, backoff_seconds, backoff_until)

            response.headers["Retry-After"] = str(backoff_seconds)

        return response
```

```python
# app/main.py (AJOUTER)
from app.middleware.rate_limit_backoff import ExponentialBackoffMiddleware

app.add_middleware(ExponentialBackoffMiddleware)
```

#### Étape 3.4: Quotas par Tenant (2 jours)

```python
# app/models/tenant.py (MODIFIER)
class Tenant(Base):
    # ... champs existants

    # Quotas par tenant (configurable)
    quota_requests_per_day = Column(Integer, default=100000)
    quota_storage_gb = Column(Integer, default=5)
    quota_users = Column(Integer, default=10)

    # Tracking usage
    usage_requests_today = Column(Integer, default=0)
    usage_storage_gb = Column(Float, default=0.0)
    usage_users_count = Column(Integer, default=0)

    # Reset quotas daily
    quota_reset_at = Column(DateTime(timezone=True))
```

```python
# app/middleware/quota_enforcement.py (NOUVEAU)
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.models.tenant import Tenant
from app.core.database import get_db
from datetime import datetime, timedelta

class QuotaEnforcementMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        tenant_id = request.headers.get("X-Tenant-ID")

        if not tenant_id:
            return await call_next(request)

        db = next(get_db())
        try:
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

            if not tenant:
                return await call_next(request)

            # Reset quotas si nécessaire
            if tenant.quota_reset_at < datetime.utcnow():
                tenant.usage_requests_today = 0
                tenant.quota_reset_at = datetime.utcnow() + timedelta(days=1)
                db.commit()

            # Check quotas
            if tenant.usage_requests_today >= tenant.quota_requests_per_day:
                raise HTTPException(
                    status_code=429,
                    detail=f"Daily request quota exceeded ({tenant.quota_requests_per_day} requests/day)"
                )

            # Increment usage
            tenant.usage_requests_today += 1
            db.commit()

        finally:
            db.close()

        return await call_next(request)
```

#### Étape 3.5: Monitoring & Alerting (1 jour)

```python
# app/services/quota_monitor.py (NOUVEAU)
from app.models.tenant import Tenant
from app.core.database import get_db
from typing import List, Dict

def get_tenants_approaching_quota(threshold: float = 0.8) -> List[Dict]:
    """
    Identifier tenants approchant leurs quotas.
    Threshold = 0.8 = 80% du quota
    """
    db = next(get_db())

    tenants = db.query(Tenant).filter(
        Tenant.status == "active"
    ).all()

    at_risk = []

    for tenant in tenants:
        usage_pct = tenant.usage_requests_today / tenant.quota_requests_per_day

        if usage_pct >= threshold:
            at_risk.append({
                "tenant_id": tenant.id,
                "tenant_name": tenant.name,
                "usage_pct": usage_pct * 100,
                "requests_today": tenant.usage_requests_today,
                "quota": tenant.quota_requests_per_day
            })

    return at_risk

# Scheduled task (APScheduler)
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('interval', hours=1)
def check_quota_alerts():
    """Run every hour"""
    at_risk = get_tenants_approaching_quota(threshold=0.8)

    if at_risk:
        # Send alert (email, Slack, etc.)
        from app.services.email import send_alert_email
        send_alert_email(
            subject="Tenants Approaching Quota",
            body=f"{len(at_risk)} tenants at 80%+ quota:\n{at_risk}"
        )

scheduler.start()
```

### Tests de Validation

```python
# tests/middleware/test_rate_limit.py
import pytest
from fastapi.testclient import TestClient
import time

def test_rate_limit_per_tenant(client: TestClient):
    """Chaque tenant a son propre quota"""
    # Tenant A - 5 requests OK
    for i in range(5):
        response = client.post(
            "/auth/login",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"email": "test@example.com", "password": "pass"}
        )
        assert response.status_code in [200, 401]  # Login peut échouer, mais pas rate limited

    # 6ème request = rate limited
    response = client.post(
        "/auth/login",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"email": "test@example.com", "password": "pass"}
    )
    assert response.status_code == 429

    # Tenant B - NON affecté par quota de Tenant A
    response = client.post(
        "/auth/login",
        headers={"X-Tenant-ID": "tenant-b"},
        json={"email": "test@example.com", "password": "pass"}
    )
    assert response.status_code in [200, 401]  # Pas rate limited

def test_exponential_backoff(client: TestClient):
    """Backoff augmente exponentiellement"""
    tenant_id = "backoff-test"

    # Déclencher rate limit 3 fois
    for violation in range(3):
        for i in range(6):  # Dépasser limite
            client.post(
                "/auth/login",
                headers={"X-Tenant-ID": tenant_id},
                json={"email": "test@example.com", "password": "pass"}
            )

        # Check backoff header
        response = client.post(
            "/auth/login",
            headers={"X-Tenant-ID": tenant_id},
            json={"email": "test@example.com", "password": "pass"}
        )

        retry_after = int(response.headers.get("Retry-After", 0))
        expected_backoff = 2 ** (violation + 1)

        assert retry_after >= expected_backoff

def test_daily_quota_enforcement(client: TestClient, db_session):
    """Quota journalier respecté"""
    tenant = Tenant(
        id="quota-test",
        quota_requests_per_day=10,
        usage_requests_today=9
    )
    db_session.add(tenant)
    db_session.commit()

    # 1 request OK (9 + 1 = 10)
    response = client.get(
        "/invoices",
        headers={"X-Tenant-ID": "quota-test"}
    )
    assert response.status_code == 200

    # Next request = quota exceeded
    response = client.get(
        "/invoices",
        headers={"X-Tenant-ID": "quota-test"}
    )
    assert response.status_code == 429
    assert "Daily request quota exceeded" in response.json()['detail']
```

### Critères de Succès

- ✅ Rate limiting par tenant (pas global)
- ✅ Limits différenciées par endpoint
- ✅ Backoff exponentiel implémenté
- ✅ Quotas journaliers par tenant
- ✅ Monitoring quotas (alerting)
- ✅ Tests isolation tenants passent
- ✅ Redis configuré et scalable

### Temps Estimé: **1.5 semaines**

### Ressources: 1 Backend Dev

---

## 🔴 P0-4: MIGRATION ROLLBACK STRATEGY

### Problème Actuel

```python
# Migrations Alembic:
- 9 migrations existantes
- Aucun test downgrade()
- Aucune procédure rollback documentée
- Migration échoue = système down
```

### Plan d'Action

#### Étape 4.1: Tester TOUTES les Migrations (3 jours)

```bash
# scripts/test-migrations.sh (NOUVEAU)
#!/bin/bash
set -e

echo "Testing all Alembic migrations (up + down)..."

# 1. Backup production DB structure
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME --schema-only > backup_schema.sql

# 2. Create test database
createdb azalscore_migration_test

# 3. Test migrations forward
echo "Testing upgrade..."
alembic upgrade head

# 4. Test migrations backward (CRITICAL)
echo "Testing downgrade..."
alembic downgrade base

# 5. Test upgrade again
echo "Testing re-upgrade..."
alembic upgrade head

# 6. Compare schemas
pg_dump -h $DB_HOST -U $DB_USER -d azalscore_migration_test --schema-only > test_schema.sql
diff backup_schema.sql test_schema.sql

# 7. Cleanup
dropdb azalscore_migration_test

echo "✅ All migrations tested successfully"
```

**CI/CD Integration:**
```yaml
# .github/workflows/test-migrations.yml
name: Test Database Migrations

on:
  pull_request:
    paths:
      - 'alembic/versions/**'

jobs:
  test-migrations:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Test migrations
        run: |
          chmod +x scripts/test-migrations.sh
          ./scripts/test-migrations.sh
```

#### Étape 4.2: Vérifier downgrade() de TOUTES les Migrations (2-3 jours)

```python
# Audit chaque migration:
# alembic/versions/*.py

def downgrade():
    # ❌ MAL - Empty downgrade
    pass

    # ✅ BIEN - Reverse operations
    op.drop_table('tenants')
    op.drop_constraint('fk_users_tenant_id', 'users')
```

**Script d'audit:**
```python
# scripts/audit-migrations.py
import os
import re

def audit_migration(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # Check if downgrade() is empty
    downgrade_match = re.search(
        r'def downgrade\(\):.*?(?=\ndef|\Z)',
        content,
        re.DOTALL
    )

    if downgrade_match:
        downgrade_body = downgrade_match.group(0)

        # Check if only contains 'pass'
        if 'pass' in downgrade_body and downgrade_body.count('\n') < 5:
            print(f"⚠️  {file_path}: Empty downgrade()")
            return False

    return True

# Audit all migrations
migrations_dir = 'alembic/versions'
empty_downgrades = []

for filename in os.listdir(migrations_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(migrations_dir, filename)
        if not audit_migration(filepath):
            empty_downgrades.append(filename)

if empty_downgrades:
    print(f"\n❌ {len(empty_downgrades)} migrations avec downgrade vide:")
    for migration in empty_downgrades:
        print(f"  - {migration}")
    exit(1)
else:
    print("✅ Toutes les migrations ont downgrade() implémenté")
```

#### Étape 4.3: Backup Automatique Avant Migration (1 jour)

```python
# scripts/safe-migrate.sh (NOUVEAU)
#!/bin/bash
set -e

echo "🔒 Safe Migration Script avec Backup Automatique"

# 1. Configuration
BACKUP_DIR="./backups/migrations"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_before_migration_$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR

# 2. Backup DB AVANT migration
echo "📦 Creating backup: $BACKUP_FILE"
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -F c -f $BACKUP_FILE

# Vérifier backup
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup failed!"
    exit 1
fi

BACKUP_SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE")
echo "✅ Backup created: $(($BACKUP_SIZE / 1024 / 1024))MB"

# 3. Dry-run migration (si possible)
echo "🧪 Testing migration (dry-run)..."
alembic upgrade head --sql > migration_preview.sql
echo "Preview saved to: migration_preview.sql"

# 4. Demander confirmation
read -p "Continue with migration? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Migration cancelled"
    exit 0
fi

# 5. Exécuter migration
echo "🚀 Running migration..."
alembic upgrade head

# 6. Vérifier succès
if [ $? -eq 0 ]; then
    echo "✅ Migration successful"
    echo "📦 Backup available at: $BACKUP_FILE"
else
    echo "❌ Migration failed!"
    echo "📦 Restore from backup: pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME $BACKUP_FILE"
    exit 1
fi

# 7. Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
echo "🧹 Cleaned up backups older than 30 days"
```

#### Étape 4.4: Blue-Green Deployment pour Migrations (3-4 jours)

```yaml
# docker-compose.blue-green.yml
version: '3.8'

services:
  # Production actuelle (BLUE)
  api-blue:
    image: azalscore-api:current
    environment:
      - DATABASE_URL=postgresql://user:pass@db/azalscore
      - MIGRATION_MODE=false
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Nouvelle version avec migration (GREEN)
  api-green:
    image: azalscore-api:new-version
    environment:
      - DATABASE_URL=postgresql://user:pass@db/azalscore
      - MIGRATION_MODE=true  # Run migrations on startup
    ports:
      - "8001:8000"  # Different port
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Load balancer (switch blue → green)
  nginx:
    image: nginx:latest
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
    depends_on:
      - api-blue
      - api-green
```

```bash
# scripts/blue-green-deploy.sh
#!/bin/bash
set -e

echo "🔵🟢 Blue-Green Deployment with Migration"

# 1. Deploy GREEN (nouvelle version)
echo "Starting GREEN deployment..."
docker-compose -f docker-compose.blue-green.yml up -d api-green

# 2. Wait for GREEN health check
echo "Waiting for GREEN to be healthy..."
for i in {1..30}; do
    if curl -f http://localhost:8001/health; then
        echo "✅ GREEN is healthy"
        break
    fi
    sleep 2
done

# 3. Run smoke tests on GREEN
echo "Running smoke tests on GREEN..."
pytest tests/smoke/ --base-url=http://localhost:8001

if [ $? -ne 0 ]; then
    echo "❌ Smoke tests failed on GREEN"
    echo "Rolling back..."
    docker-compose -f docker-compose.blue-green.yml stop api-green
    exit 1
fi

# 4. Switch traffic BLUE → GREEN (nginx config)
echo "Switching traffic to GREEN..."
sed -i 's/proxy_pass.*api-blue/proxy_pass http://api-green/' nginx.conf
docker-compose -f docker-compose.blue-green.yml exec nginx nginx -s reload

# 5. Monitor for 5 minutes
echo "Monitoring GREEN for 5 minutes..."
sleep 300

# 6. Check error rate
ERROR_RATE=$(curl http://localhost:8001/metrics | grep error_rate | awk '{print $2}')
if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
    echo "❌ Error rate too high: $ERROR_RATE"
    echo "Rolling back to BLUE..."
    sed -i 's/proxy_pass.*api-green/proxy_pass http://api-blue/' nginx.conf
    docker-compose -f docker-compose.blue-green.yml exec nginx nginx -s reload
    exit 1
fi

# 7. Success - Shutdown BLUE
echo "✅ GREEN deployment successful"
docker-compose -f docker-compose.blue-green.yml stop api-blue

echo "🎉 Deployment complete"
```

#### Étape 4.5: Rollback Procedure Documentée (1 jour)

```markdown
# docs/ROLLBACK_PROCEDURE.md (NOUVEAU)

# 🔄 Rollback Procedure - AZALSCORE

## Cas 1: Migration Échoue (Détectée Immédiatement)

### Étape 1: Arrêter Déploiement
```bash
docker-compose stop api
```

### Étape 2: Restore Backup
```bash
# Trouver dernier backup
LATEST_BACKUP=$(ls -t backups/migrations/*.sql | head -1)

# Restore
pg_restore -h $DB_HOST -U $DB_USER \
  -d $DB_NAME --clean $LATEST_BACKUP
```

### Étape 3: Redémarrer Version Précédente
```bash
git checkout <previous-commit>
docker-compose up -d api
```

### Étape 4: Vérifier Santé
```bash
curl http://localhost:8000/health
```

---

## Cas 2: Migration Réussie Mais Bugs en Production

### Étape 1: Downgrade Migration
```bash
# Downgrade vers version précédente
alembic downgrade -1  # Une version

# Ou downgrade vers version spécifique
alembic downgrade <revision_id>
```

### Étape 2: Deploy Code Précédent
```bash
git checkout <previous-commit>
docker-compose up -d api
```

### Étape 3: Monitor
```bash
# Check logs
docker-compose logs -f api

# Check metrics
curl http://localhost:8000/metrics
```

---

## Cas 3: Blue-Green Rollback

### Étape 1: Switch Traffic GREEN → BLUE
```bash
# Update nginx config
sed -i 's/proxy_pass.*api-green/proxy_pass http://api-blue/' nginx.conf
docker-compose exec nginx nginx -s reload
```

### Étape 2: Verify BLUE Health
```bash
curl http://localhost:8000/health
```

### Étape 3: Shutdown GREEN
```bash
docker-compose stop api-green
```

---

## Temps de Rollback Cibles (RTO)

- **Migration échouée:** < 5 minutes
- **Bugs détectés:** < 15 minutes
- **Blue-Green switch:** < 1 minute

## Checklist Post-Rollback

- [ ] Service restauré et healthy
- [ ] Backup vérifié intact
- [ ] Users notifiés si downtime
- [ ] Post-mortem planifié
- [ ] Root cause analysée
- [ ] Fix planifié
```

### Tests de Validation

```python
# tests/migrations/test_all_migrations.py
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

def test_upgrade_downgrade_cycle():
    """Test full upgrade/downgrade cycle"""
    config = Config("alembic.ini")

    # Upgrade to head
    command.upgrade(config, "head")

    # Verify tables exist
    engine = create_engine(config.get_main_option("sqlalchemy.url"))
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "tenants" in tables
    assert "users" in tables

    # Downgrade to base
    command.downgrade(config, "base")

    # Verify tables removed
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "tenants" not in tables

    # Re-upgrade
    command.upgrade(config, "head")

    # Verify tables exist again
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "tenants" in tables

def test_migrations_idempotent():
    """Migrations can be run multiple times"""
    config = Config("alembic.ini")

    # Run twice
    command.upgrade(config, "head")
    command.upgrade(config, "head")  # Should not fail

    # Downgrade
    command.downgrade(config, "base")
    command.downgrade(config, "base")  # Should not fail
```

### Critères de Succès

- ✅ Tous downgrade() implémentés et testés
- ✅ Backup automatique avant migration
- ✅ Blue-green deployment fonctionnel
- ✅ Rollback procedure documentée
- ✅ Tests migrations en CI/CD
- ✅ RTO < 15 minutes
- ✅ Smoke tests automatisés

### Temps Estimé: **2-3 semaines**

### Ressources: 1 DevOps + 1 Backend Dev

---

## 🔴 P0-5 à P0-10: SOMMAIRE

Par souci de concision, voici un résumé des 5 bloquants restants. Document complet disponible dans fichiers annexes.

### P0-5: BACKUP & DISASTER RECOVERY (2 semaines)
- Backups automatiques journaliers (pg_dump)
- Tests recovery mensuels
- Région secondaire (multi-AZ)
- RTO < 4h, RPO < 1h
- DR plan documenté

### P0-6: ALERTING & MONITORING (1.5 semaines)
- PagerDuty/OpsGenie setup
- Alertes critiques (CPU, DB, errors)
- Runbooks incidents
- SLA 99.9% (43 min/mois downtime max)
- On-call rotation

### P0-7: TRY/CATCH REFACTORING (3 semaines)
- Refactorer 27 P1 business logic
- Centraliser dans Guardian
- ErrorMiddleware global
- Tests erreurs
- Lint rule interdisant try/except

### P0-8: localStorage → httpOnly COOKIES (1 semaine)
- JWT en httpOnly cookie
- SessionStorage temporaire
- Token blacklist server-side
- CSP strict
- Tests XSS

### P0-9: TESTS SECURITY & QUALITY (2 semaines)
- Mutation testing (PIT)
- OWASP Top 10 tests
- Pentest automatisé (OWASP ZAP)
- Tests de charge (Locust)
- Tests chaos (Chaos Monkey lite)

### P0-10: AUDIT SÉCURITÉ EXTERNE (1 semaine + attente)
- Pentest professionnel
- Code review externe
- Compliance RGPD
- Rapport vulnérabilités
- Plan remediation

---

## 📊 TIMELINE GLOBALE

### Vague 1: Sécurité Fondamentale (Semaines 1-3)
```
Semaine 1-2:  P0-1 Secrets Management
Semaine 2-3:  P0-2 Multi-Tenant Validation
Semaine 3:    P0-3 Rate Limiting
```

### Vague 2: Fiabilité Infrastructure (Semaines 4-6)
```
Semaine 4-6:  P0-4 Migration Rollback
Semaine 5-6:  P0-5 Backup & DR
Semaine 6:    P0-6 Alerting & Monitoring
```

### Vague 3: Qualité Code & Sécurité Client (Semaines 7-9)
```
Semaine 7-9:  P0-7 Try/Catch Refactoring
Semaine 8:    P0-8 localStorage → Cookies
Semaine 9:    P0-9 Tests Security & Quality
```

### Vague 4: Validation Finale (Semaines 10-12)
```
Semaine 10-11: P0-10 Audit Sécurité Externe
Semaine 11:    Load Testing
Semaine 12:    Production Readiness Review
```

---

## ✅ CRITÈRES DE SUCCÈS GLOBAUX

### Sécurité
- ✅ Aucun secret en clair
- ✅ Multi-tenant isolation garantie
- ✅ Rate limiting par tenant actif
- ✅ Pentest externe passé (score > 8/10)

### Fiabilité
- ✅ RTO < 4h, RPO < 1h
- ✅ Backups testés mensuellement
- ✅ Migrations rollback testées
- ✅ Alerting 24/7 configuré

### Qualité
- ✅ Try/catch centralisés (0 P1 restant)
- ✅ Tests mutation coverage > 80%
- ✅ Tests sécurité automatisés
- ✅ Load testing validé (1000 users)

### Production
- ✅ SLA 99.9% documenté
- ✅ Runbooks incidents complets
- ✅ On-call rotation en place
- ✅ **GO/NO-GO Production = GO** ✅

---

## 💰 BUDGET ESTIMÉ

### Ressources Humaines (12 semaines)

| Rôle | Temps | Coût Estimé |
|------|-------|-------------|
| DevOps Senior | 6 semaines | 30k€ |
| Backend Dev Senior | 12 semaines | 60k€ |
| Backend Dev Mid | 6 semaines | 24k€ |
| Security Auditor External | 1 semaine | 10k€ |
| **TOTAL** | | **124k€** |

### Infrastructure

| Service | Coût Mensuel |
|---------|--------------|
| AWS Secrets Manager | ~40€/mois |
| Backup Storage (S3) | ~100€/mois |
| DR Region (standby) | ~200€/mois |
| PagerDuty | ~50€/mois |
| Monitoring (Datadog/New Relic) | ~150€/mois |
| **TOTAL** | **~540€/mois** |

### Outils

| Outil | Coût One-Time |
|-------|---------------|
| Pentest externe | 10k€ |
| Load testing tools | Gratuit (Locust) |
| Chaos engineering | Gratuit (custom) |
| **TOTAL** | **10k€** |

### **BUDGET TOTAL: ~134k€**

---

## 🎯 RECOMMANDATION FINALE

### Option A: Full Speed (3 mois)
- Équipe de 3 devs fulltime
- Budget: 134k€
- Go-live: Mai 2026
- Risque: Moyen (rush)

### Option B: Prudent (4-5 mois)
- Équipe de 2 devs
- Budget: 110k€
- Go-live: Juin-Juillet 2026
- Risque: Faible (thorough)

### ⭐ RECOMMANDATION: Option B (Prudent)

**Rationale:**
- Sécurité critique = pas de rush
- Tests approfondis essentiels
- Audit externe nécessite temps
- Meilleur ROI long terme

---

## 📅 NEXT STEPS IMMÉDIATS

### Cette Semaine
1. ✅ Valider budget avec management
2. ✅ Recruter DevOps senior
3. ✅ Setup AWS/Vault account
4. ✅ Créer repos Git pour scripts
5. ✅ Planifier sprint 1

### Semaine Prochaine
6. ✅ Kickoff P0-1 (Secrets Management)
7. ✅ Setup staging environment
8. ✅ CI/CD pipeline migration tests
9. ✅ Documentation review
10. ✅ Stakeholder communication

---

**Document généré le 2026-01-23**
**Plan d'action opérationnel - Prêt à exécuter**
**Version: 1.0.0**
