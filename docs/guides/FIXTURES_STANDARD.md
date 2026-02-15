# Fixtures Standardisées - CORE SaaS v2

> Guide de référence pour les fixtures de test harmonisées

**Statut**: HARMONISATION COMPLÈTE ✅
**Date**: 2026-02-13
**Version**: 2.0

---

## Principe Fondamental

Toutes les fixtures de base sont définies dans `app/conftest.py` (conftest global).
Les conftest.py des modules **ne doivent PAS redéfinir** ces fixtures.

---

## Fixtures Globales (app/conftest.py)

### Constantes

```python
TEST_TENANT_ID = "tenant-test-001"
TEST_USER_ID = "12345678-1234-1234-1234-123456789001"
TEST_USER_UUID = UUID(TEST_USER_ID)
```

### Fixtures Héritées Automatiquement

| Fixture | Type | Description |
|---------|------|-------------|
| `tenant_id` | `str` | ID du tenant de test = `"tenant-test-001"` |
| `user_id` | `str` | ID utilisateur (string UUID) |
| `user_uuid` | `UUID` | ID utilisateur (objet UUID) |
| `db_session` | `Session` | Session SQLAlchemy (SQLite in-memory) |
| `test_db_session` | `Session` | Alias pour db_session |
| `test_client` | `TestClient` | Client FastAPI avec headers auto-injectés |
| `mock_auth_global` | `dict` | Mock authentification (autouse=True) |
| `saas_context` | `SaaSContext` | Contexte SaaS mock avec ADMIN role |
| `mock_user` | `MockUser` | Objet utilisateur mock |

### test_client (Important!)

Le `test_client` du conftest global **injecte automatiquement** les headers:
- `X-Tenant-ID: tenant-test-001`
- `Authorization: Bearer mock-jwt-{user_id}`

**Ne pas créer de nouveau TestClient dans les modules!**

---

## Conftest Module Standard

Chaque module doit avoir un conftest.py qui:
1. **NE redéfinit PAS** les fixtures globales
2. **Ajoute** des alias de compatibilité
3. **Définit** les fixtures spécifiques au domaine

### Template Conftest Module

```python
"""
Fixtures pour les tests {Module} v2

Hérite des fixtures globales de app/conftest.py.
"""

import pytest
from datetime import datetime
from uuid import uuid4


# ============================================================================
# FIXTURES HÉRITÉES DU CONFTEST GLOBAL
# ============================================================================
# Les fixtures suivantes sont héritées de app/conftest.py:
# - tenant_id, user_id, user_uuid
# - db_session, test_db_session
# - test_client (avec headers auto-injectés)
# - mock_auth_global (autouse=True)
# - saas_context


@pytest.fixture
def client(test_client):
    """
    Alias pour test_client (compatibilité avec anciens tests).

    Le test_client du conftest global ajoute déjà les headers requis.
    """
    return test_client


@pytest.fixture
def auth_headers(tenant_id):
    """Headers d'authentification avec tenant ID."""
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": tenant_id
    }


# ============================================================================
# FIXTURES SPÉCIFIQUES AU MODULE
# ============================================================================

@pytest.fixture
def sample_entity(db_session, tenant_id):
    """Fixture pour une entité de test."""
    entity = Entity(
        id=uuid4(),
        tenant_id=tenant_id,
        # ... autres champs
    )
    db_session.add(entity)
    db_session.commit()
    db_session.refresh(entity)
    return entity
```

---

## Erreurs Courantes à Éviter

### 1. Redéfinition de tenant_id/user_id

**MAUVAIS:**
```python
@pytest.fixture
def tenant_id():
    return "mon-tenant"  # Conflit avec global!

@pytest.fixture
def user_id():
    return "user-test-001"  # String invalide, pas UUID!
```

**BON:**
```python
# Ne pas définir - hérité du conftest global
# tenant_id = "tenant-test-001" (automatique)
# user_id = UUID valide (automatique)
```

### 2. Mock SaaSContext avec autouse=True

**MAUVAIS:**
```python
@pytest.fixture(autouse=True)
def mock_saas_context(monkeypatch):
    # Conflit avec mock_auth_global global!
```

**BON:**
```python
# Ne pas définir - mock_auth_global global gère ça
# Si besoin d'un contexte spécifique:
@pytest.fixture
def mock_dirigeant_context(tenant_id):
    return SaaSContext(
        tenant_id=tenant_id,
        role=UserRole.DIRIGEANT,
        # ...
    )
```

### 3. Création d'un nouveau TestClient

**MAUVAIS:**
```python
@pytest.fixture
def client():
    return TestClient(app)  # Pas de headers, pas de DB mock!
```

**BON:**
```python
@pytest.fixture
def client(test_client):
    return test_client  # Hérite tout du global
```

---

## Fixtures de Compatibilité Obligatoires

Pour la rétrocompatibilité, chaque module DOIT définir:

```python
@pytest.fixture
def client(test_client):
    """Alias pour test_client."""
    return test_client

@pytest.fixture
def auth_headers(tenant_id):
    """Headers d'authentification."""
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": tenant_id
    }
```

---

## Fixtures Optionnelles de Compatibilité

Si le module utilise ces noms:

```python
@pytest.fixture
def mock_saas_context(saas_context):
    """Alias pour saas_context du conftest global."""
    return saas_context

@pytest.fixture
def mock_context(saas_context):
    """Alias pour saas_context (helpdesk style)."""
    return saas_context
```

---

## Modules Harmonisés

| Module | Statut | Notes |
|--------|--------|-------|
| iam | ✅ | Reference implementation |
| commercial | ✅ | Corrigé |
| accounting | ✅ | Corrigé |
| inventory | ✅ | Corrigé |
| hr | ✅ | Corrigé |
| finance | ✅ | Corrigé |
| tenants | ✅ | Corrigé |
| helpdesk | ✅ | Corrigé (mock_context alias) |
| projects | ✅ | Corrigé |
| procurement | ✅ | Corrigé |
| purchases | ✅ | Corrigé |
| audit | ✅ | Corrigé |
| ai_assistant | ✅ | Corrigé |
| autoconfig | ✅ | Corrigé |
| automated_accounting | ✅ | Corrigé |
| bi | ✅ | Corrigé |
| backup | ✅ | Corrigé |
| broadcast | ✅ | Corrigé |
| country_packs | ✅ | Corrigé |
| ecommerce | ✅ | Corrigé |
| email | ✅ | Corrigé |
| field_service | ✅ | Corrigé |
| guardian | ✅ | Corrigé |
| maintenance | ✅ | Corrigé |
| production | ✅ | Corrigé |
| qc | ✅ | Corrigé |
| pos | ✅ | Corrigé |
| subscriptions | ✅ | Corrigé |
| treasury | ✅ | Corrigé |
| triggers | ✅ | Corrigé |
| compliance | ✅ | Corrigé |
| interventions | ✅ | Corrigé |
| marketplace | ✅ | Corrigé |
| mobile | ✅ | Corrigé |
| quality | ✅ | Corrigé |
| stripe_integration | ✅ | Corrigé |
| web | ✅ | Corrigé |
| website | ✅ | Corrigé |

---

## Vérification Rapide

Pour vérifier qu'un conftest.py est conforme:

1. **Pas de** `@pytest.fixture(autouse=True) def mock_saas_context`
2. **Pas de** redéfinition de `tenant_id`, `user_id`
3. **Présence de** `client(test_client)` alias
4. **Présence de** `auth_headers(tenant_id)` fixture
5. **Imports minimaux** (pas de TestClient, pas de app import)

---

## Commande de Test

```bash
# Tester un module corrigé
pytest app/modules/iam/tests/ -v

# Tester tous les modules
pytest app/modules/*/tests/ -v

# Vérifier collection
pytest app/modules/*/tests/ --collect-only
```

---

**Dernière mise à jour**: 2026-02-13
