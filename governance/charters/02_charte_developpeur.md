# CHARTE DÉVELOPPEUR AZALSCORE
## Standards et Obligations de Développement

**Version:** 1.0.0
**Statut:** DOCUMENT NORMATIF
**Date:** 2026-01-05
**Classification:** PUBLIC - OPPOSABLE
**Référence:** AZALS-GOV-02-v1.0.0

---

## 1. OBJECTIF

Cette charte définit les règles, standards et obligations que tout développeur (humain ou IA) doit respecter lors de contributions au projet AZALSCORE.

---

## 2. PÉRIMÈTRE

### 2.1 Applicabilité
- Développeurs backend Python
- Développeurs frontend
- IA générant du code (Claude, GPT, etc.)
- Contributeurs externes
- Équipes de maintenance

### 2.2 Exclusions
- Modifications du Core (voir Charte 01)
- Décisions architecturales majeures (voir Charte 08)

---

## 3. PRINCIPES DE DÉVELOPPEMENT

### 3.1 Backend-First
```
RÈGLE: Le backend est la source de vérité.
- Toute logique métier dans le backend
- Validation côté serveur obligatoire
- Le frontend ne décide jamais
```

### 3.2 API-First
```
RÈGLE: L'API précède l'implémentation.
- Définir le contrat OpenAPI d'abord
- Implémenter ensuite
- Documenter automatiquement
```

### 3.3 Test-Driven
```
RÈGLE: Les tests guident le développement.
- Tests unitaires obligatoires
- Tests d'intégration pour les API
- Couverture minimum : 80%
```

---

## 4. STANDARDS TECHNIQUES

### 4.1 Python Backend

```python
# ✅ BONNES PRATIQUES

# Type hints obligatoires
def get_user(user_id: int, tenant_id: str) -> Optional[User]:
    pass

# Docstrings pour fonctions publiques
def calculate_total(items: List[Item]) -> Decimal:
    """
    Calcule le total des items.

    Args:
        items: Liste des items à totaliser

    Returns:
        Total en Decimal
    """
    pass

# Validation Pydantic
class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    tenant_id: str

# Gestion d'erreurs explicite
try:
    result = service.process(data)
except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
except PermissionError as e:
    raise HTTPException(status_code=403, detail=str(e))
```

### 4.2 Structure des Modules

```
app/modules/{module_name}/
├── __init__.py       # Exports publics
├── models.py         # Modèles SQLAlchemy
├── schemas.py        # Schémas Pydantic
├── service.py        # Logique métier
├── router.py         # Endpoints FastAPI
└── GOVERNANCE.md     # Charte du module (OBLIGATOIRE)
```

### 4.3 Conventions de Nommage

| Élément | Convention | Exemple |
|---------|------------|---------|
| Modules | snake_case | `field_service` |
| Classes | PascalCase | `InvoiceService` |
| Fonctions | snake_case | `calculate_total` |
| Variables | snake_case | `user_count` |
| Constantes | UPPER_SNAKE | `MAX_RETRY_COUNT` |
| Endpoints | kebab-case | `/invoices/{id}/line-items` |

---

## 5. RÈGLES OBLIGATOIRES

### 5.1 Sécurité

| Règle | Description |
|-------|-------------|
| R-SEC-01 | Jamais de secrets dans le code |
| R-SEC-02 | Validation de toutes les entrées |
| R-SEC-03 | Échapper les sorties (XSS) |
| R-SEC-04 | Requêtes paramétrées (SQL injection) |
| R-SEC-05 | Vérification tenant_id systématique |

### 5.2 Qualité

| Règle | Description |
|-------|-------------|
| R-QUA-01 | Lint (ruff/flake8) sans erreur |
| R-QUA-02 | Type checking (mypy) sans erreur |
| R-QUA-03 | Tests passants avant merge |
| R-QUA-04 | Documentation à jour |
| R-QUA-05 | Pas de code mort |

### 5.3 Performance

| Règle | Description |
|-------|-------------|
| R-PERF-01 | Éviter les N+1 queries |
| R-PERF-02 | Pagination obligatoire sur les listes |
| R-PERF-03 | Index sur les colonnes filtrées |
| R-PERF-04 | Timeout sur les appels externes |
| R-PERF-05 | Cache quand pertinent |

---

## 6. INTERDICTIONS

### 6.1 Interdictions Absolues

```python
# ❌ INTERDIT - Secrets en dur
API_KEY = "sk-1234567890"

# ❌ INTERDIT - SQL brut non paramétré
query = f"SELECT * FROM users WHERE id = {user_id}"

# ❌ INTERDIT - Ignorer le tenant_id
def get_all_invoices():  # Manque tenant_id !
    return db.query(Invoice).all()

# ❌ INTERDIT - Catch-all silencieux
try:
    do_something()
except:
    pass

# ❌ INTERDIT - Logique métier dans le router
@router.post("/invoices")
def create_invoice(data: InvoiceCreate):
    # ❌ Calculs métier ici = INTERDIT
    total = sum(item.price * item.qty for item in data.items)
    tax = total * 0.20
    # ...
```

### 6.2 Interdictions Core

- ❌ Modifier `app/core/*` sans procédure
- ❌ Importer des modules dans le Core
- ❌ Contourner l'authentification
- ❌ Désactiver l'audit

### 6.3 Interdictions Architecturales

- ❌ Dépendances circulaires entre modules
- ❌ Appels directs entre modules (utiliser événements)
- ❌ État global mutable
- ❌ Logique métier dans le frontend

---

## 7. GESTION DES ERREURS

### 7.1 Codes d'Erreur Standards

```python
# Structure d'erreur AZALSCORE
{
    "error": {
        "code": "AZALS-MOD-001",      # Code unique
        "message": "Message utilisateur", # Compréhensible
        "details": {},                 # Détails techniques (dev only)
        "timestamp": "2026-01-05T...",
        "trace_id": "uuid"             # Pour corrélation logs
    }
}
```

### 7.2 Hiérarchie des Exceptions

```python
# Exceptions AZALSCORE
class AzalsException(Exception):
    """Base exception AZALSCORE"""
    code: str = "AZALS-000"

class ValidationException(AzalsException):
    """Erreur de validation"""
    code: str = "AZALS-VAL-001"

class PermissionException(AzalsException):
    """Erreur de permission"""
    code: str = "AZALS-PERM-001"

class TenantException(AzalsException):
    """Erreur tenant"""
    code: str = "AZALS-TENANT-001"
```

---

## 8. DOCUMENTATION

### 8.1 Code Auto-Documenté

```python
def create_invoice(
    tenant_id: str,
    customer_id: int,
    items: List[InvoiceItemCreate],
    due_date: Optional[date] = None
) -> Invoice:
    """
    Crée une nouvelle facture pour un client.

    Args:
        tenant_id: Identifiant du tenant
        customer_id: ID du client facturé
        items: Liste des lignes de facture
        due_date: Date d'échéance (défaut: +30 jours)

    Returns:
        Invoice: La facture créée

    Raises:
        ValidationException: Si les données sont invalides
        PermissionException: Si pas de droits sur le client

    Example:
        >>> invoice = create_invoice("tenant-1", 42, items)
        >>> print(invoice.number)
        "INV-2026-0001"
    """
```

### 8.2 OpenAPI Obligatoire

```python
@router.post(
    "/invoices",
    response_model=InvoiceResponse,
    status_code=201,
    summary="Créer une facture",
    description="Crée une nouvelle facture pour le tenant courant",
    responses={
        201: {"description": "Facture créée"},
        400: {"description": "Données invalides"},
        403: {"description": "Permission refusée"},
    }
)
def create_invoice(...):
    pass
```

---

## 9. TESTS

### 9.1 Structure des Tests

```
tests/
├── conftest.py           # Fixtures communes
├── test_auth.py          # Tests authentification
├── test_health.py        # Tests health check
├── test_{module}.py      # Tests par module
└── integration/
    └── test_e2e.py       # Tests end-to-end
```

### 9.2 Couverture Minimale

| Composant | Couverture Minimale |
|-----------|---------------------|
| Core | 90% |
| Services | 85% |
| Routers | 80% |
| Modèles | 70% |
| Global | 80% |

### 9.3 Tests Obligatoires

```python
# Tout endpoint doit avoir :
def test_endpoint_success():
    """Test cas nominal"""

def test_endpoint_validation_error():
    """Test validation entrée"""

def test_endpoint_unauthorized():
    """Test sans authentification"""

def test_endpoint_forbidden():
    """Test sans permission"""

def test_endpoint_tenant_isolation():
    """Test isolation tenant"""
```

---

## 10. GIT ET CI/CD

### 10.1 Branches

```
main                 # Production - protégée
├── develop          # Développement
├── feature/*        # Nouvelles fonctionnalités
├── fix/*            # Corrections
├── hotfix/*         # Corrections urgentes
└── release/*        # Préparation release
```

### 10.2 Commits

```
Format: <type>(<scope>): <description>

Types:
- feat: Nouvelle fonctionnalité
- fix: Correction de bug
- docs: Documentation
- refactor: Refactoring
- test: Ajout de tests
- chore: Maintenance

Exemples:
feat(invoice): add PDF export
fix(auth): correct JWT expiration
docs(api): update OpenAPI specs
```

### 10.3 Pull Requests

Checklist obligatoire :
- [ ] Tests passants
- [ ] Lint sans erreur
- [ ] Documentation à jour
- [ ] Pas de secrets
- [ ] Review approuvée
- [ ] Charte module présente (si nouveau module)

---

## 11. CONSÉQUENCES DU NON-RESPECT

### 11.1 Automatiques
- Rejet du merge par CI/CD
- Notification à l'équipe
- Blocage du déploiement

### 11.2 Manuelles
- Revue de code obligatoire
- Formation si récurrence
- Restriction d'accès si grave

---

## 12. CHECKLIST DÉVELOPPEUR

Avant chaque commit :
- [ ] Code lint propre
- [ ] Tests passants
- [ ] Pas de secrets
- [ ] Documentation à jour
- [ ] tenant_id vérifié
- [ ] Erreurs gérées
- [ ] Logs appropriés

---

*Document généré et validé le 2026-01-05*
*Classification: PUBLIC - OPPOSABLE*
*Référence: AZALS-GOV-02-v1.0.0*
