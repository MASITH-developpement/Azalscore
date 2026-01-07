# PROMPT DE CORRECTION - AZALSCORE ERP

## Instructions pour l'assistant IA

Tu es un expert en débogage Python et FastAPI. Applique les corrections suivantes au projet Azalscore dans l'ordre de priorité indiqué. Pour chaque correction, effectue la modification et confirme le changement.

---

## CORRECTIONS P0 (CRITIQUES) - À faire en premier

### Correction 1: scheduler.py - Nom de table incorrect

**Fichier:** `app/services/scheduler.py`

**Modification 1 - Ligne 77:**
Remplacer:
```python
DELETE FROM red_workflow_steps
```
Par:
```python
DELETE FROM red_decision_workflows
```

**Modification 2 - Ligne 99:**
Remplacer:
```python
"user_id": 1,
```
Par:
```python
"user_id": 0,  # ID système réservé
```

---

### Correction 2: treasury.py - Type Python incompatible

**Fichier:** `app/api/treasury.py`

**Modification - Ligne 71:**
Ajouter en haut du fichier (après les imports existants):
```python
from typing import Optional
```

Remplacer ligne 71:
```python
def get_latest_treasury_forecast(...) -> ForecastResponse | None:
```
Par:
```python
def get_latest_treasury_forecast(...) -> Optional[ForecastResponse]:
```

---

### Correction 3: red_workflow.py - Type Python incompatible

**Fichier:** `app/services/red_workflow.py`

**Modification - Ligne 72:**
Ajouter en haut du fichier (après les imports existants):
```python
from typing import List
```

Remplacer ligne 72:
```python
def _get_completed_steps(self, decision_id: int) -> list[RedWorkflowStep]:
```
Par:
```python
def _get_completed_steps(self, decision_id: int) -> List[RedWorkflowStep]:
```

---

### Correction 4: auth.py - Response model incompatible

**Fichier:** `app/api/auth.py`

**Modification 1 - Ligne 14:**
Modifier l'import typing:
```python
from typing import Dict, List, Optional, Union
```

**Modification 2 - Ligne 269:**
Remplacer:
```python
@router.post("/login", response_model=TokenResponse)
```
Par:
```python
@router.post("/login", response_model=Union[TokenResponse, LoginResponseWith2FA])
```

**Modification 3 - Ligne 384:**
Remplacer:
```python
get_client_ip(request)
```
Par:
```python
client_ip = get_client_ip(request)
auth_rate_limiter.check_register_rate(client_ip)
```

---

## CORRECTIONS P1 (MAJEURS) - À faire ensuite

### Correction 5: security.py - ValueError non géré

**Fichier:** `app/core/security.py`

**Modification - Lignes 24-26:**
Remplacer:
```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)
```
Par:
```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, TypeError):
        return False
```

**Modification - Lignes 34-37:**
Remplacer:
```python
def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')
```
Par:
```python
def get_password_hash(password: str) -> str:
    try:
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except (ValueError, TypeError) as e:
        raise ValueError(f"Password hashing failed: {e}")
```

---

### Correction 6: dependencies.py - Conversion int sans protection

**Fichier:** `app/core/dependencies.py`

**Modification - Lignes 82-84:**
Remplacer:
```python
# Charger l'utilisateur depuis la DB
user = db.query(User).filter(User.id == int(user_id)).first()
```
Par:
```python
# Charger l'utilisateur depuis la DB
try:
    uid = int(user_id)
except (ValueError, TypeError):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid user identifier in token"
    )
user = db.query(User).filter(User.id == uid).first()
```

---

### Correction 7: two_factor.py - datetime.utcnow() déprécié

**Fichier:** `app/core/two_factor.py`

**Modification 1 - Ligne 12:**
Remplacer:
```python
from datetime import datetime
```
Par:
```python
from datetime import datetime, timezone
```

**Modification 2 - Ligne 126:**
Remplacer:
```python
user.totp_verified_at = datetime.utcnow()
```
Par:
```python
user.totp_verified_at = datetime.now(timezone.utc)
```

---

### Correction 8: accounting.py - Exception silencieuse

**Fichier:** `app/api/accounting.py`

**Modification - Lignes 103-111:**
Remplacer:
```python
except Exception:
    return AccountingStatusResponse(
        entries_up_to_date=True,
        last_closure_date=None,
        pending_entries_count=0,
        days_since_closure=None,
        status='🟢'
    )
```
Par:
```python
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Error fetching accounting status: {e}")
    return AccountingStatusResponse(
        entries_up_to_date=False,
        last_closure_date=None,
        pending_entries_count=-1,
        days_since_closure=None,
        status='⚠️'  # Status dégradé en cas d'erreur
    )
```

---

### Correction 9: hr.py - Ligne inutile

**Fichier:** `app/api/hr.py`

**Modification - Ligne 54:**
Supprimer la ligne:
```python
next_month_start + timedelta(days=5)
```

---

## CORRECTIONS P2 (MINEURS) - Optionnel

### Correction 10: predictions.py - Prefix dupliqué

**Fichier:** `app/api/predictions.py`

**Modification - Ligne 25:**
Remplacer:
```python
router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])
```
Par:
```python
router = APIRouter(prefix="/predictions", tags=["predictions"])
```

**Modification - Déplacer import:**
Supprimer ligne 280: `import random`
Ajouter en haut du fichier: `import random`

---

## VÉRIFICATIONS POST-CORRECTION

Après avoir appliqué toutes les corrections, exécute ces vérifications:

1. **Vérification syntaxe:**
```bash
python -m py_compile app/main.py
find app -name "*.py" -exec python -m py_compile {} \;
```

2. **Test imports:**
```bash
python -c "from app.main import app; print('Import OK')"
```

3. **Test types (si mypy disponible):**
```bash
python -m mypy app/ --ignore-missing-imports
```

---

## RÉSUMÉ DES FICHIERS MODIFIÉS

| Fichier | Nombre de modifications |
|---------|------------------------|
| `app/services/scheduler.py` | 2 |
| `app/api/treasury.py` | 2 |
| `app/services/red_workflow.py` | 2 |
| `app/api/auth.py` | 3 |
| `app/core/security.py` | 2 |
| `app/core/dependencies.py` | 1 |
| `app/core/two_factor.py` | 2 |
| `app/api/accounting.py` | 1 |
| `app/api/hr.py` | 1 |
| `app/api/predictions.py` | 2 |

**Total: 18 modifications dans 10 fichiers**

---

## COMMIT SUGGÉRÉ

```bash
git add -A
git commit -m "fix: corrections critiques pour mise en production

- fix(scheduler): correction nom table red_decision_workflows
- fix(api): types Python compatibles < 3.10 (Optional, List)
- fix(auth): response_model Union pour support 2FA
- fix(auth): rate limiting sur endpoint bootstrap
- fix(security): gestion ValueError bcrypt
- fix(dependencies): validation int user_id
- fix(two_factor): datetime.now(timezone.utc)
- fix(accounting): log erreurs au lieu de masquer
- fix(hr): suppression ligne morte
- fix(predictions): correction prefix API"
```

---

**FIN DU PROMPT DE CORRECTION**
