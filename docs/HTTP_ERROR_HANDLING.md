# AZALS - Gestion Centralisee des Erreurs HTTP

## Vue d'ensemble

Ce document decrit le systeme de gestion des erreurs HTTP mis en place pour AZALS.
Le systeme est **production-ready**, **tracable** et **compatible V0**.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        REQUETE CLIENT                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI MIDDLEWARE                           │
│  (CORS → Tenant → RBAC → Metrics → Compression → Guardian)     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXCEPTION HANDLERS                            │
│         (app/core/http_errors.py)                               │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │   401    │ │   403    │ │   404    │ │   500    │           │
│  │Unauth    │ │Forbidden │ │Not Found │ │Internal  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              REPONSE JSON STANDARDISEE                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Format de reponse JSON standardise

### 401 Unauthorized
```json
{
  "error": "unauthorized",
  "message": "Authentication required",
  "code": 401
}
```

### 403 Forbidden
```json
{
  "error": "forbidden",
  "message": "Access denied",
  "code": 403
}
```

### 404 Not Found
```json
{
  "error": "not_found",
  "message": "Resource not found",
  "code": 404,
  "path": "/requested/path"
}
```

### 422 Validation Error
```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "code": 422,
  "details": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "Unexpected server error",
  "code": 500,
  "trace_id": "a1b2c3d4"
}
```

---

## Tests curl

### Prerequis
```bash
# Variables d'environnement
export API_URL="http://localhost:8000"
export TENANT_ID="demo-tenant"
```

### Test 401 - Authentification requise
```bash
# Sans token JWT (route protegee)
curl -s -X GET "${API_URL}/v1/protected/me" \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -H "Content-Type: application/json" | jq

# Reponse attendue:
# {
#   "error": "unauthorized",
#   "message": "Authentication required",
#   "code": 401
# }
```

### Test 403 - Acces refuse
```bash
# Acces a une route admin sans role admin
curl -s -X GET "${API_URL}/v1/admin/users" \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -H "Authorization: Bearer <token_user_normal>" \
  -H "Content-Type: application/json" | jq

# Via route de test (dev uniquement)
curl -s -X GET "${API_URL}/test-errors/403" | jq

# Reponse attendue:
# {
#   "error": "forbidden",
#   "message": "Access denied",
#   "code": 403
# }
```

### Test 404 - Ressource non trouvee
```bash
# Route inexistante
curl -s -X GET "${API_URL}/v1/cette-route-nexiste-pas" \
  -H "X-Tenant-ID: ${TENANT_ID}" | jq

# Reponse attendue:
# {
#   "error": "not_found",
#   "message": "Resource not found",
#   "code": 404,
#   "path": "/v1/cette-route-nexiste-pas"
# }
```

### Test 422 - Erreur de validation
```bash
# Donnees invalides
curl -s -X POST "${API_URL}/auth/login" \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -H "Content-Type: application/json" \
  -d '{"email": "invalid"}' | jq

# Via route de test (dev uniquement) - appel sans parametres
curl -s -X GET "${API_URL}/test-errors/422" | jq

# Reponse attendue:
# {
#   "error": "validation_error",
#   "message": "Request validation failed",
#   "code": 422,
#   "details": [...]
# }
```

### Test 500 - Erreur serveur
```bash
# Via route de test (dev uniquement)
curl -s -X GET "${API_URL}/test-errors/500" | jq

# Reponse attendue:
# {
#   "error": "internal_error",
#   "message": "Unexpected server error",
#   "code": 500,
#   "trace_id": "xxxxxxxx"
# }
```

---

## Pages d'erreurs visuelles

Les pages d'erreurs HTML avec theme "vaisseau spatial" sont accessibles a:

| Code | URL | Theme |
|------|-----|-------|
| 401 | `/errors/401` | Cockpit verrouille |
| 403 | `/errors/403` | Zone interdite / Champ de force |
| 404 | `/errors/404` | Vaisseau perdu dans l'espace |
| 500 | `/errors/500` | Defaillance systeme / Explosion controlee |

### Test des pages d'erreurs
```bash
# Ouvrir dans un navigateur
open "${API_URL}/errors/401"
open "${API_URL}/errors/403"
open "${API_URL}/errors/404"
open "${API_URL}/errors/500"
```

---

## Integration Frontend

### Utilisation basique
```typescript
import { handleHttpError, wrapApiCall } from '@/core/error-handling';
import { api } from '@/core/api-client';

// Option 1: Wrapper automatique
const data = await wrapApiCall(
  () => api.get('/v1/endpoint'),
  { context: 'Chargement donnees' }
);

// Option 2: Gestion manuelle
try {
  const response = await api.get('/v1/endpoint');
} catch (error) {
  const statusCode = getErrorStatusCode(error);
  handleHttpError(statusCode, error.response?.data, {
    showNotification: true,
    redirectOnError: true
  });
}
```

### Redirection vers pages d'erreur
```typescript
import { redirectToErrorPage } from '@/core/error-handling';

// Rediriger vers la page 404
redirectToErrorPage(404);

// Rediriger vers la page 500 (avec trace_id dans la console)
redirectToErrorPage(500);
```

---

## Checklist Production

### Backend
- [x] Exception handlers enregistres globalement
- [x] Format JSON standardise pour toutes les erreurs
- [x] Logging structure avec niveaux appropries (INFO/WARNING/ERROR)
- [x] trace_id unique pour les erreurs 500
- [x] Pas de fuite d'information sensible
- [x] Headers de securite (WWW-Authenticate pour 401)
- [x] Compatible uvicorn/gunicorn

### Frontend
- [x] Parsing des erreurs standardisees
- [x] Notifications contextuelles
- [x] Redirections vers pages d'erreur
- [x] Gestion du refresh token sur 401

### Pages d'erreurs
- [x] Theme visuel coherent (vaisseau spatial)
- [x] Illustrations SVG optimisees
- [x] Fallback si image non chargee
- [x] Messages clairs et professionnels
- [x] Boutons d'action (retour accueil, reconnexion)
- [x] Responsive (mobile)
- [x] Pas de fuite d'information technique

### Tests
- [x] Tests curl pour chaque code d'erreur
- [x] Routes de test (dev uniquement)
- [x] Scenarios frontend documentes

---

## Fichiers modifies

| Fichier | Description |
|---------|-------------|
| `app/core/http_errors.py` | Module centralisee des exception handlers |
| `app/main.py` | Enregistrement des handlers + routes pages erreurs |
| `frontend/errors/401.html` | Page erreur 401 |
| `frontend/errors/403.html` | Page erreur 403 |
| `frontend/errors/404.html` | Page erreur 404 |
| `frontend/errors/500.html` | Page erreur 500 |
| `frontend/errors/assets/*.svg` | Illustrations theme spatial |
| `frontend/src/core/error-handling/index.ts` | Gestion erreurs frontend |
| `frontend/src/core/api-client/index.ts` | Parsing erreurs API |

---

## Exceptions personnalisees

Pour lever des erreurs avec le format standardise dans le code metier:

```python
from app.core.http_errors import (
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    InternalServerException
)

# Exemples d'utilisation
raise UnauthorizedException("Token invalide")
raise ForbiddenException("Acces refuse a cette ressource")
raise NotFoundException("Client non trouve")
raise InternalServerException("Erreur de calcul")
```

---

## Logging

Les erreurs sont loggees avec les informations suivantes:

| Champ | Description |
|-------|-------------|
| `path` | Chemin de la requete |
| `method` | Methode HTTP |
| `client_ip` | Adresse IP du client |
| `error_type` | Type d'erreur (unauthorized, forbidden, etc.) |
| `trace_id` | ID de trace (500 uniquement) |
| `tenant_id` | ID du tenant (si disponible) |
| `exception_type` | Type d'exception Python (500 uniquement) |
| `exception_message` | Message d'exception (500 uniquement, tronque) |

### Exemple de log 500
```json
{
  "level": "ERROR",
  "message": "Erreur 500: Division by zero",
  "path": "/v1/calculate",
  "method": "POST",
  "client_ip": "192.168.1.100",
  "error_type": "internal_error",
  "trace_id": "a1b2c3d4",
  "exception_type": "ZeroDivisionError",
  "exception_message": "division by zero",
  "tenant_id": "demo-tenant"
}
```

---

## Evolution V1

Ce systeme est concu pour evoluer vers V1 sans reecriture majeure:

1. **Ajout de nouveaux codes d'erreur**: Ajouter un handler dans `http_errors.py`
2. **Personnalisation par tenant**: Etendre les pages d'erreur avec le branding tenant
3. **Monitoring avance**: Integrer les trace_id avec un systeme de tracing (Jaeger, etc.)
4. **Rate limiting visuel**: Ajouter une page 429 avec countdown
