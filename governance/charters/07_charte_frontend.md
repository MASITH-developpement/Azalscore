# CHARTE FRONTEND AZALSCORE
## Interface Utilisateur Déclarative

**Version:** 1.0.0
**Statut:** DOCUMENT NORMATIF
**Date:** 2026-01-05
**Classification:** PUBLIC - OPPOSABLE
**Référence:** AZALS-GOV-07-v1.0.0

---

## 1. OBJECTIF

Cette charte définit les règles de conception et développement des interfaces utilisateur AZALSCORE, garantissant une séparation stricte entre présentation et logique métier.

**PRINCIPE FONDAMENTAL:**
```
LE FRONTEND EST UNE PROJECTION VISUELLE DES API.
IL NE CONTIENT AUCUNE LOGIQUE MÉTIER.
IL EST REMPLAÇABLE SANS IMPACT SUR LE SYSTÈME.
```

---

## 2. PÉRIMÈTRE

- Interfaces web (SPA, PWA)
- Applications mobiles
- Dashboards et tableaux de bord
- Portails clients
- Interfaces d'administration

---

## 3. PRINCIPES FONDAMENTAUX

### 3.1 Frontend Déclaratif

```
RÈGLE: Le frontend déclare CE QUI doit être affiché,
       pas COMMENT le calculer.

Le frontend:
✅ Affiche les données reçues de l'API
✅ Envoie les actions utilisateur à l'API
✅ Gère l'état de l'interface (loading, erreurs)
✅ Applique les styles et l'ergonomie

Le frontend NE:
❌ Calcule pas de totaux
❌ Valide pas de règles métier
❌ Décide pas des permissions
❌ Stocke pas de données sensibles
```

### 3.2 API-Driven

```
RÈGLE: Toute donnée vient de l'API, toute action passe par l'API.

# ✅ Correct
const invoices = await api.get('/invoices');

# ❌ Interdit - Calcul côté client
const total = invoices.reduce((sum, inv) => sum + inv.amount, 0);
// Le total doit venir de l'API !
```

### 3.3 UI Jetable

```
RÈGLE: Le frontend peut être remplacé sans toucher au backend.

Implications:
- Aucune logique métier dans le frontend
- Aucune donnée persistante côté client
- API = contrat stable, UI = implémentation variable
```

---

## 4. ARCHITECTURE

### 4.1 Séparation des Responsabilités

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    PRÉSENTATION                        │  │
│  │  Composants UI, Styles, Animations, Responsive        │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   ÉTAT LOCAL                           │  │
│  │  Loading states, Form values, UI toggles              │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  COMMUNICATION API                     │  │
│  │  Fetch, Cache, Mutations, Error handling              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/HTTPS
                              │ OpenAPI Contract
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         BACKEND                              │
│              (Toute la logique métier ici)                  │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Stack Recommandée

```
AZALSCORE UI actuelle:
- HTML5 / CSS3 vanilla
- JavaScript ES6+
- Pas de framework lourd

Alternatives acceptables:
- React / Vue / Svelte
- TypeScript recommandé
- Tailwind / CSS Modules

Interdit:
- jQuery (obsolète)
- Logique métier dans composants
- State management complexe pour données métier
```

---

## 5. RÈGLES OBLIGATOIRES

### 5.1 Zéro Logique Métier

```javascript
// ❌ INTERDIT - Logique métier côté client
function calculateInvoiceTotal(items) {
  const subtotal = items.reduce((sum, item) => sum + item.price * item.qty, 0);
  const tax = subtotal * 0.20;
  return subtotal + tax;
}

// ✅ CORRECT - Demander à l'API
async function getInvoiceTotal(invoiceId) {
  const response = await api.get(`/invoices/${invoiceId}`);
  return response.data.total; // Calculé par le backend
}
```

### 5.2 Validation Côté Serveur

```javascript
// ❌ INTERDIT - Validation métier côté client
function validateInvoice(invoice) {
  if (invoice.amount > customer.creditLimit) {
    throw new Error("Limite de crédit dépassée");
  }
}

// ✅ CORRECT - Validation UX basique + serveur
function validateForm(data) {
  // Validation UX seulement (format, requis)
  if (!data.email) return { error: "Email requis" };
  if (!data.email.includes('@')) return { error: "Email invalide" };

  // La vraie validation est côté serveur
  return { valid: true };
}
```

### 5.3 Permissions via API

```javascript
// ❌ INTERDIT - Gérer les permissions côté client
if (user.role === 'ADMIN') {
  showDeleteButton();
}

// ✅ CORRECT - L'API dit ce qui est permis
const { data: permissions } = await api.get('/me/permissions');
if (permissions.canDelete) {
  showDeleteButton();
}

// ✅ ENCORE MIEUX - L'API retourne les actions disponibles
const { data: invoice } = await api.get(`/invoices/${id}`);
// invoice.actions = ['view', 'edit', 'delete'] ou ['view'] selon permissions
```

---

## 6. COMMUNICATION API

### 6.1 Consommation OpenAPI

```javascript
// Utiliser le schéma OpenAPI pour générer les types/clients
// Exemple avec openapi-typescript-codegen

import { InvoicesService } from './generated/api';

const invoices = await InvoicesService.listInvoices({
  tenantId: currentTenant,
  page: 1,
  pageSize: 20
});
```

### 6.2 Gestion des Headers

```javascript
// OBLIGATOIRE - Headers sur chaque requête
const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

apiClient.interceptors.request.use(config => {
  // JWT Token
  config.headers['Authorization'] = `Bearer ${getToken()}`;
  // Tenant ID
  config.headers['X-Tenant-ID'] = getCurrentTenant();
  return config;
});
```

### 6.3 Gestion des Erreurs

```javascript
// Gestion centralisée des erreurs API
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token expiré → redirect login
      redirectToLogin();
    }
    if (error.response?.status === 403) {
      // Permission refusée
      showError("Accès non autorisé");
    }
    if (error.response?.status === 400) {
      // Erreur validation → afficher message
      showValidationErrors(error.response.data);
    }
    return Promise.reject(error);
  }
);
```

---

## 7. ÉTAT ET DONNÉES

### 7.1 Données Autorisées Côté Client

| Type | Stockage | Exemple |
|------|----------|---------|
| Token JWT | Memory / HttpOnly Cookie | Auth token |
| Tenant ID | Memory | Contexte actuel |
| Préférences UI | LocalStorage | Theme, langue |
| Cache API | Memory (court terme) | Liste factures |
| État formulaire | State local | Champs en cours |

### 7.2 Données INTERDITES Côté Client

| Type | Raison |
|------|--------|
| Mot de passe | Sécurité |
| Données autres tenants | Isolation |
| Secrets API | Sécurité |
| Logique de calcul | Intégrité |
| Règles métier | Cohérence |

### 7.3 Cache

```javascript
// Cache court terme acceptable
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes max

// Invalider le cache sur mutation
async function createInvoice(data) {
  await api.post('/invoices', data);
  invalidateCache('invoices'); // Force refresh
}
```

---

## 8. UI ENGINE

### 8.1 Concept

```
RECOMMANDATION: Utiliser un UI Engine générique.

L'API peut retourner:
- Les données à afficher
- Les champs du formulaire
- Les actions disponibles
- Les validations côté client

Le frontend se contente de rendre ce que l'API décrit.
```

### 8.2 Exemple

```json
// API Response avec métadonnées UI
{
  "data": {
    "id": 1,
    "number": "INV-2026-001",
    "amount": 1500.00
  },
  "ui": {
    "title": "Facture INV-2026-001",
    "actions": [
      {"id": "edit", "label": "Modifier", "enabled": true},
      {"id": "delete", "label": "Supprimer", "enabled": false, "reason": "Facture payée"},
      {"id": "pdf", "label": "Exporter PDF", "enabled": true}
    ],
    "fields": [
      {"name": "number", "label": "Numéro", "readonly": true},
      {"name": "amount", "label": "Montant", "type": "currency"}
    ]
  }
}
```

---

## 9. ACCESSIBILITÉ

### 9.1 Standards

```
OBLIGATOIRE: WCAG 2.1 niveau AA

- Navigation clavier complète
- Labels sur tous les inputs
- Contrastes suffisants
- Textes alternatifs images
- Annonces lecteur d'écran
```

### 9.2 Checklist

```markdown
- [ ] Tous les formulaires ont des labels
- [ ] Focus visible sur éléments interactifs
- [ ] Navigation possible au clavier
- [ ] Contrastes ≥ 4.5:1 (texte normal)
- [ ] Images ont des alt texts
- [ ] Erreurs annoncées aux lecteurs d'écran
```

---

## 10. PERFORMANCE

### 10.1 Métriques

| Métrique | Cible |
|----------|-------|
| First Contentful Paint | < 1.5s |
| Largest Contentful Paint | < 2.5s |
| Time to Interactive | < 3.5s |
| Cumulative Layout Shift | < 0.1 |

### 10.2 Bonnes Pratiques

```javascript
// Lazy loading des composants
const InvoiceDetail = lazy(() => import('./InvoiceDetail'));

// Pagination obligatoire
const { data } = await api.get('/invoices', {
  params: { page: 1, pageSize: 20 }
});

// Pas de données inutiles
// L'API retourne uniquement les champs nécessaires
```

---

## 11. SÉCURITÉ FRONTEND

### 11.1 XSS Prevention

```javascript
// ❌ INTERDIT - innerHTML avec données utilisateur
element.innerHTML = userInput;

// ✅ CORRECT - textContent ou échappement
element.textContent = userInput;

// Ou avec framework
<div>{escapeHtml(userInput)}</div>
```

### 11.2 Tokens

```javascript
// ❌ INTERDIT - Token dans localStorage (XSS vulnerable)
localStorage.setItem('token', jwt);

// ✅ PRÉFÉRÉ - HttpOnly Cookie (géré par le serveur)
// Ou en mémoire (perdu au refresh, plus sûr)
let token = null;
function setToken(t) { token = t; }
```

### 11.3 Secrets

```
RÈGLE: Aucun secret dans le code frontend.

❌ const API_KEY = "sk-xxxxx"
❌ const DB_PASSWORD = "xxx"

Le frontend n'a besoin d'aucun secret.
Toutes les opérations sensibles passent par le backend.
```

---

## 12. INTERDICTIONS

### 12.1 Absolues

- ❌ Logique métier (calculs, validations règles)
- ❌ Accès direct à la base de données
- ❌ Gestion des permissions sans API
- ❌ Stockage de secrets
- ❌ Appels API cross-tenant
- ❌ Contournement de l'authentification

### 12.2 Patterns Interdits

```javascript
// ❌ Calcul métier
const total = items.reduce(...);

// ❌ Règle métier
if (invoice.amount > 10000) requireApproval();

// ❌ Permission hardcodée
if (user.role === 'ADMIN') { ... }

// ❌ Accès autre tenant
api.get('/invoices', { headers: { 'X-Tenant-ID': 'autre-tenant' }});
```

---

## 13. TESTS

### 13.1 Types de Tests

| Type | Scope | Exemple |
|------|-------|---------|
| Unit | Composants isolés | Render button |
| Integration | Composants + API mock | Form submission |
| E2E | Parcours complet | Login → Create invoice |

### 13.2 Couverture

```
Couverture minimale:
- Composants critiques: 80%
- Parcours utilisateur: 100% des happy paths
- Gestion erreurs: 100% des cas d'erreur API
```

---

## 14. CONSÉQUENCES DU NON-RESPECT

| Violation | Conséquence |
|-----------|-------------|
| Logique métier | Refactoring obligatoire |
| Secret dans le code | Incident sécurité |
| Accès direct DB | Rejet immédiat |
| XSS vulnerability | Correction P0 |

---

*Document généré et validé le 2026-01-05*
*Classification: PUBLIC - OPPOSABLE*
*Référence: AZALS-GOV-07-v1.0.0*

**LE FRONTEND AFFICHE, LE BACKEND DÉCIDE.**
