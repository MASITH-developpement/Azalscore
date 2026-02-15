# Guide de Contribution - AZALSCORE

## Workflow Git

### Branches

| Branch | Description | Protection |
|--------|-------------|------------|
| `main` | Production stable | Protected: 2 reviewers, CI pass |
| `develop` | Integration | Protected: 1 reviewer, CI pass |
| `feature/*` | Nouvelles fonctionnalites | - |
| `fix/*` | Corrections de bugs | - |
| `hotfix/*` | Corrections urgentes prod | - |
| `audit/*` | Audits securite | - |

### Workflow standard

```bash
# 1. Creer une branche depuis develop
git checkout develop
git pull origin develop
git checkout -b feature/ma-fonctionnalite

# 2. Developper avec commits atomiques
git add -p
git commit -m "feat(module): description courte"

# 3. Push et creer PR
git push -u origin feature/ma-fonctionnalite
# Creer PR via GitHub
```

### Convention de commits

Format: `<type>(<scope>): <description>`

Types:
- `feat`: Nouvelle fonctionnalite
- `fix`: Correction de bug
- `refactor`: Refactoring sans changement fonctionnel
- `docs`: Documentation
- `test`: Ajout/modification de tests
- `chore`: Maintenance, config
- `security`: Correction de securite
- `perf`: Amelioration de performance

Exemples:
```
feat(accounting): add journal entry validation
fix(iam): resolve token refresh race condition
security(auth): implement rate limiting on login
refactor(core): extract base service class
```

## Standards de code

### Python

```python
# Utiliser les type hints
def get_user(user_id: UUID, db: Session) -> Optional[User]:
    ...

# Docstrings pour fonctions publiques
def calculate_tax(amount: Decimal, rate: Decimal) -> Decimal:
    """
    Calcule le montant de taxe.

    Args:
        amount: Montant HT
        rate: Taux de taxe (ex: 0.20 pour 20%)

    Returns:
        Montant de la taxe

    Raises:
        ValueError: Si rate < 0 ou > 1
    """
    ...

# Gestion d'erreurs explicite
try:
    result = service.process(data)
except ValidationError as e:
    logger.warning(f"Validation failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

### Securite

```python
# JAMAIS: SQL par concatenation
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # VULNERABLE

# TOUJOURS: Queries parametrees
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# JAMAIS: Secrets hardcodes
API_KEY = "sk_live_xxxxx"  # INTERDIT

# TOUJOURS: Variables d'environnement
API_KEY = os.getenv("API_KEY")

# TOUJOURS: Verifier tenant isolation
def get_items(self) -> List[Item]:
    return self.db.query(Item).filter(
        Item.tenant_id == self.tenant_id  # OBLIGATOIRE
    ).all()
```

## Process de review

### Avant de soumettre

1. **Lancer les checks locaux**
   ```bash
   # Pre-commit hooks
   pre-commit run --all-files

   # Tests
   pytest tests/ -v

   # Coverage
   pytest --cov=app --cov-fail-under=70
   ```

2. **Verifier la PR**
   - Taille raisonnable (< 500 lignes)
   - Description claire
   - Issue liee
   - Checklist remplie

### Criteres de review

| Priorite | Critere | Bloquant |
|----------|---------|----------|
| P0 | Vulnerabilite securite | Oui |
| P0 | Fuite de donnees possible | Oui |
| P0 | Violation tenant isolation | Oui |
| P1 | Tests manquants | Oui |
| P1 | Breaking change non documente | Oui |
| P2 | Code non conforme aux standards | Non |
| P2 | Documentation manquante | Non |
| P3 | Suggestions d'amelioration | Non |

### Temps de review attendu

- PRs < 100 lignes: 1 jour ouvre
- PRs 100-300 lignes: 2 jours ouvres
- PRs > 300 lignes: Diviser la PR

## Tests

### Structure

```
tests/
  test_<module>_service.py    # Tests unitaires service
  test_<module>_router.py     # Tests API
  test_<module>_models.py     # Tests models
  integration/
    test_<scenario>.py        # Tests integration
  e2e/
    test_<flow>.py            # Tests end-to-end
```

### Conventions

```python
# Nommage: test_<fonction>_<scenario>_<resultat_attendu>
def test_create_user_with_valid_data_returns_user():
    ...

def test_create_user_with_duplicate_email_raises_400():
    ...

def test_get_user_without_auth_returns_401():
    ...
```

## Contact

- **Questions techniques**: #dev-backend (Slack)
- **Securite**: security@azals.io
- **Urgences prod**: #incidents (Slack)
