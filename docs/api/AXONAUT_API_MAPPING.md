# Mapping API Axonaut ↔ AzalScore

**Version** : 1.0  
**Date** : 13 février 2026  
**Public** : Équipes techniques, Développeurs, Intégrateurs

---

## 📋 Introduction

Ce document fournit le mapping complet des endpoints API entre Axonaut et AzalScore pour faciliter :
- La migration des intégrations existantes
- Le développement de nouvelles intégrations
- La compréhension des équivalences fonctionnelles

### Format du Document

Chaque section suit le format :
- **Endpoint Axonaut** : `METHOD /path/axonaut`
- **Endpoint AzalScore** : `METHOD /path/azalscore`
- **Compatibilité** : ✅ Compatible / ⚠️ Différences / 🔄 Transformation requise
- **Notes** : Différences de structure, champs additionnels, etc.

---

## 1. Authentification

### Axonaut
```http
POST https://api.axonaut.com/v2/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}
```

### AzalScore
```http
POST https://api.azalscore.com/v1/iam/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password",
  "tenant_id": "tenant-uuid"  // NOUVEAU: Multi-tenant
}
```

**Compatibilité** : 🔄 Transformation requise  
**Notes** : 
- AzalScore requiert `tenant_id` (multi-tenant natif)
- Token JWT avec expiration différente (24h vs 8h Axonaut)
- Refresh token disponible

---

## 2. CRM - Clients

### 2.1 Liste des Clients

#### Axonaut
```http
GET /api/v2/customers?page=1&per_page=50
```

#### AzalScore
```http
GET /v2/commercial/customers?page=1&page_size=50
```

**Compatibilité** : ✅ Compatible  
**Mapping réponse** :
```javascript
// Axonaut → AzalScore
{
  "id": customer_id,           // String → UUID
  "name": name,                // Identique
  "email": email,              // Identique  
  "phone": phone,              // Identique
  "company": company_name,     // company → company_name
  "vat_number": tax_id,        // vat_number → tax_id
  // NOUVEAU dans AzalScore
  "customer_type": "CUSTOMER", // Enum (PROSPECT, CUSTOMER, VIP, etc.)
  "tags": [],                  // Tags personnalisables
  "custom_fields": {}          // Champs personnalisés
}
```

### 2.2 Créer un Client

#### Axonaut
```http
POST /api/v2/customers
```

#### AzalScore  
```http
POST /v2/commercial/customers
```

**Compatibilité** : ✅ Compatible  
**Différences** :
- AzalScore accepte champs additionnels : `customer_type`, `tags`, `custom_fields`
- Validation email stricte dans AzalScore

### 2.3 Mettre à Jour un Client

#### Axonaut
```http
PUT /api/v2/customers/{id}
```

#### AzalScore
```http
PATCH /v2/commercial/customers/{id}
```

**Compatibilité** : ⚠️ Différences  
**Notes** : 
- AzalScore utilise PATCH (partiel) au lieu de PUT (complet)
- Champs non fournis ne sont pas modifiés

---

## 3. CRM - Opportunités

### 3.1 Liste des Opportunités

#### Axonaut
```http
GET /api/v2/opportunities
```

#### AzalScore
```http
GET /v2/commercial/opportunities
```

**Compatibilité** : ✅ Compatible  
**Mapping statuts** :
```javascript
// Axonaut → AzalScore
"new" → "NEW"
"qualified" → "QUALIFIED"
"proposal" → "PROPOSAL"
"negotiation" → "NEGOTIATION"
"won" → "WON"
"lost" → "LOST"
```

**Champs additionnels AzalScore** :
- `probability` : Probabilité de gagner (0-100%)
- `competitors` : Concurrents identifiés
- `ai_score` : Score IA de qualification

---

## 4. Facturation - Devis

### 4.1 Liste des Devis

#### Axonaut
```http
GET /api/v2/quotes
```

#### AzalScore
```http
GET /v2/commercial/documents?type=QUOTE
```

**Compatibilité** : 🔄 Transformation requise  
**Notes** : 
- AzalScore utilise un endpoint unifié `documents` avec filtrage par `type`
- Types disponibles : QUOTE, ORDER, INVOICE, CREDIT_NOTE, PROFORMA, DELIVERY

### 4.2 Créer un Devis

#### Axonaut
```http
POST /api/v2/quotes
{
  "customer_id": "123",
  "date": "2026-02-13",
  "validity_days": 30,
  "lines": [
    {
      "product_id": "prod_1",
      "quantity": 2,
      "unit_price": 100,
      "discount_percent": 10
    }
  ]
}
```

#### AzalScore
```http
POST /v2/commercial/documents
{
  "document_type": "QUOTE",
  "customer_id": "uuid-customer",
  "document_date": "2026-02-13",
  "valid_until": "2026-03-15",  // Date calculée ou fournie
  "lines": [
    {
      "product_id": "uuid-product",
      "quantity": 2,
      "unit_price": 100.00,
      "discount_amount": 20.00,  // ou discount_percent: 10
      "tax_rate": 20.0           // NOUVEAU: TVA par ligne
    }
  ]
}
```

**Compatibilité** : 🔄 Transformation requise  
**Différences** :
- `validity_days` → calcul de `valid_until`
- Support TVA par ligne (multi-taux)
- UUIDs au lieu de IDs numériques

### 4.3 Convertir Devis en Facture

#### Axonaut
```http
POST /api/v2/quotes/{id}/convert_to_invoice
```

#### AzalScore
```http
POST /v2/commercial/documents/{id}/convert
{
  "target_type": "INVOICE"
}
```

**Compatibilité** : ⚠️ Différences  
**Notes** : AzalScore permet conversion vers plusieurs types (ORDER, INVOICE, etc.)

---

## 5. Facturation - Factures

### 5.1 Liste des Factures

#### Axonaut
```http
GET /api/v2/invoices?status=unpaid
```

#### AzalScore
```http
GET /v2/commercial/documents?type=INVOICE&status=SENT
```

**Mapping statuts** :
```javascript
// Axonaut → AzalScore
"draft" → "DRAFT"
"sent" → "SENT"
"paid" → "PAID"
"partially_paid" → "SENT" (avec paiements partiels)
"overdue" → "SENT" (avec due_date < today)
"cancelled" → "CANCELLED"
```

### 5.2 Enregistrer un Paiement

#### Axonaut
```http
POST /api/v2/invoices/{id}/payments
{
  "amount": 1000,
  "date": "2026-02-13",
  "method": "bank_transfer"
}
```

#### AzalScore
```http
POST /v2/commercial/documents/{id}/payments
{
  "amount": 1000.00,
  "payment_date": "2026-02-13",
  "payment_method": "BANK_TRANSFER",
  "reference": "VIR-123456"      // NOUVEAU: Référence paiement
}
```

**Compatibilité** : ✅ Compatible  
**Méthodes paiement** : `BANK_TRANSFER`, `CHECK`, `CREDIT_CARD`, `CASH`, `DIRECT_DEBIT`, `PAYPAL`, `OTHER`

### 5.3 Envoyer Facture par Email

#### Axonaut
```http
POST /api/v2/invoices/{id}/send
{
  "email": "client@example.com",
  "subject": "Votre facture",
  "message": "..."
}
```

#### AzalScore
```http
POST /v2/commercial/documents/{id}/send
{
  "to_email": "client@example.com",
  "subject": "Votre facture",
  "message": "...",
  "send_copy_to_accounting": true,  // NOUVEAU
  "attach_pdf": true                 // NOUVEAU
}
```

**Compatibilité** : ✅ Compatible  
**Nouveautés AzalScore** :
- Copie automatique service comptable
- Tracking ouverture email
- Possibilité d'inclure lien de paiement

---

## 6. Facturation - Avoirs

### 6.1 Créer un Avoir

#### Axonaut
```http
POST /api/v2/credit_notes
{
  "invoice_id": "inv_123",
  "reason": "Produit défectueux",
  "lines": [...]
}
```

#### AzalScore
```http
POST /v2/commercial/documents
{
  "document_type": "CREDIT_NOTE",
  "reference_document_id": "uuid-invoice",
  "reason": "Produit défectueux",
  "lines": [...]
}
```

**Compatibilité** : 🔄 Transformation requise  
**Notes** : Utilise l'endpoint documents unifié avec `reference_document_id`

---

## 7. Produits & Catalogue

### 7.1 Liste des Produits

#### Axonaut
```http
GET /api/v2/products
```

#### AzalScore
```http
GET /v2/commercial/products
```

**Compatibilité** : ✅ Compatible  
**Champs additionnels AzalScore** :
- `variants` : Variantes produit (taille, couleur, etc.)
- `stock_managed` : Gestion stock activée
- `stock_quantity` : Quantité en stock
- `stock_alert_threshold` : Seuil alerte stock

### 7.2 Créer un Produit

#### Axonaut
```http
POST /api/v2/products
{
  "name": "Produit A",
  "price": 100,
  "tax_rate": 20
}
```

#### AzalScore
```http
POST /v2/commercial/products
{
  "name": "Produit A",
  "unit_price": 100.00,
  "tax_rate": 20.0,
  "currency": "EUR",              // NOUVEAU
  "category": "electronics",      // NOUVEAU
  "sku": "PROD-A-001"            // NOUVEAU
}
```

**Compatibilité** : ✅ Compatible

---

## 8. Trésorerie & Banque

### 8.1 Comptes Bancaires

#### Axonaut
```http
GET /api/v2/bank_accounts
```

#### AzalScore
```http
GET /v2/finance/accounts?type=BANK
```

**Compatibilité** : ⚠️ Différences  
**Notes** : AzalScore utilise un endpoint unifié pour tous types de comptes

### 8.2 Relevés Bancaires (NOUVEAU AzalScore)

#### AzalScore Uniquement
```http
GET /v1/banking-sync/transactions
```

**Fonctionnalité exclusive** : Synchronisation automatique avec la banque

### 8.3 Rapprochement Bancaire

#### Axonaut
```http
POST /api/v2/bank_reconciliation
{
  "transaction_id": "tx_123",
  "invoice_id": "inv_456"
}
```

#### AzalScore
```http
POST /v2/finance/bank-statements/reconcile
{
  "statement_line_id": "uuid-line",
  "entry_id": "uuid-entry",
  "confidence_score": 0.95        // NOUVEAU: Score IA
}
```

**Compatibilité** : 🔄 Transformation requise

---

## 9. Comptabilité

### 9.1 Plan Comptable

#### Axonaut
```http
GET /api/v2/chart_of_accounts
```

#### AzalScore
```http
GET /v2/finance/accounts
```

**Compatibilité** : ✅ Compatible  
**Mapping comptes** :
```javascript
{
  "code": account_code,          // Ex: "411000"
  "name": account_name,          // Ex: "Clients"
  "type": account_type,          // ASSET, LIABILITY, INCOME, EXPENSE, EQUITY
  "currency": "EUR"              // NOUVEAU
}
```

### 9.2 Écritures Comptables

#### Axonaut
```http
POST /api/v2/journal_entries
{
  "date": "2026-02-13",
  "lines": [
    {"account": "411000", "debit": 1200},
    {"account": "707000", "credit": 1000},
    {"account": "445710", "credit": 200}
  ]
}
```

#### AzalScore
```http
POST /v2/finance/entries
{
  "entry_date": "2026-02-13",
  "fiscal_year": "2026",
  "journal_code": "VT",
  "lines": [
    {"account_id": "uuid", "debit": 1200.00},
    {"account_id": "uuid", "credit": 1000.00},
    {"account_id": "uuid", "credit": 200.00}
  ]
}
```

**Compatibilité** : 🔄 Transformation requise  
**Différences** :
- AzalScore utilise UUIDs pour les comptes
- Journal code requis
- Fiscal year explicite

### 9.3 Export FEC

#### Axonaut
```http
GET /api/v2/export/fec?year=2026
```

#### AzalScore
```http
GET /v2/accounting/export/fec?fiscal_year=2026
```

**Compatibilité** : ✅ Compatible  
**Format** : TXT pipe-delimited conforme DGFiP

---

## 10. RH - Employés

### 10.1 Liste des Employés

#### Axonaut
```http
GET /api/v2/employees
```

#### AzalScore
```http
GET /v2/hr/employees
```

**Compatibilité** : ✅ Compatible

### 10.2 Congés

#### Axonaut
```http
GET /api/v2/leaves
POST /api/v2/leaves
```

#### AzalScore
```http
GET /v2/hr/leaves
POST /v2/hr/leaves
```

**Compatibilité** : ✅ Compatible  
**Nouveauté AzalScore** : Workflow validation automatique configurable

---

## 11. Achats - Fournisseurs

### 11.1 Liste Fournisseurs

#### Axonaut
```http
GET /api/v2/suppliers
```

#### AzalScore
```http
GET /v2/purchases/suppliers
```

**Compatibilité** : ✅ Compatible

### 11.2 Commandes Fournisseurs

#### Axonaut
```http
GET /api/v2/purchase_orders
POST /api/v2/purchase_orders
```

#### AzalScore
```http
GET /v2/purchases/orders
POST /v2/purchases/orders
```

**Compatibilité** : ✅ Compatible  
**Nouveauté** : Workflow validation multi-niveaux

---

## 12. Stock & Inventaire

### 12.1 Mouvements de Stock

#### Axonaut
```http
POST /api/v2/stock_movements
{
  "product_id": "prod_123",
  "quantity": 10,
  "type": "in"  // in ou out
}
```

#### AzalScore
```http
POST /v2/inventory/movements
{
  "product_id": "uuid-product",
  "quantity": 10,
  "movement_type": "IN",  // IN, OUT, TRANSFER, ADJUSTMENT
  "location_id": "uuid-location",  // NOUVEAU: Multi-dépôts
  "reason": "purchase_receipt"
}
```

**Compatibilité** : ⚠️ Différences  
**Nouveauté** : Support multi-dépôts

---

## 13. Webhooks

### 13.1 Configuration Webhooks

#### Axonaut
```http
POST /api/v2/webhooks
{
  "url": "https://your-app.com/webhook",
  "events": ["invoice.created", "payment.received"]
}
```

#### AzalScore
```http
POST /v1/webhooks/subscriptions
{
  "url": "https://your-app.com/webhook",
  "events": ["document.created", "payment.received"],
  "secret": "your-webhook-secret",  // NOUVEAU: Signature HMAC
  "active": true
}
```

**Compatibilité** : ⚠️ Différences  
**Sécurité AzalScore** : Signature HMAC-SHA256 de tous les webhooks

### 13.2 Format Webhooks

#### Axonaut
```json
{
  "event": "invoice.created",
  "data": {
    "id": "inv_123",
    ...
  }
}
```

#### AzalScore
```json
{
  "event": "document.created",
  "timestamp": "2026-02-13T10:30:00Z",
  "tenant_id": "uuid",
  "data": {
    "id": "uuid",
    "document_type": "INVOICE",
    ...
  },
  "signature": "sha256=..."  // HMAC signature
}
```

---

## 14. Nouveautés Exclusives AzalScore

### 14.1 Signature Électronique

```http
# Créer demande signature
POST /v1/esignature/requests
{
  "document_id": "uuid-invoice",
  "document_type": "INVOICE",
  "signers": [
    {
      "email": "client@example.com",
      "first_name": "Jean",
      "last_name": "Dupont"
    }
  ],
  "provider": "YOUSIGN"
}

# Envoyer pour signature
POST /v1/esignature/requests/{id}/send
```

### 14.2 Synchronisation Bancaire

```http
# Connecter un compte bancaire
POST /v1/banking-sync/initiate
{
  "provider": "BUDGET_INSIGHT",
  "bank_code": "BNP",
  "redirect_uri": "https://your-app.com/callback"
}

# Synchroniser transactions
POST /v1/banking-sync/sync/{connection_id}
{
  "force": false,
  "days_back": 90
}
```

### 14.3 Rappels Automatiques

```http
# Configurer rappels
POST /v1/notifications/reminders/config
{
  "enabled": true,
  "reminder_days": [7, 15, 30],
  "auto_send": true
}

# Envoyer rappel manuel
POST /v1/notifications/reminders/send
{
  "invoice_id": "uuid",
  "force": false
}
```

### 14.4 Assistant IA (Theo)

```http
# Conversation avec Theo
POST /v1/ai/chat
{
  "message": "Crée une facture pour le client Acme Corp",
  "context": {
    "module": "commercial"
  }
}
```

---

## 15. Pagination & Filtrage

### Format Pagination

#### Axonaut
```http
GET /api/v2/customers?page=2&per_page=50
```

#### AzalScore
```http
GET /v2/commercial/customers?page=2&page_size=50
```

**Réponse Axonaut** :
```json
{
  "data": [...],
  "page": 2,
  "per_page": 50,
  "total": 250
}
```

**Réponse AzalScore** :
```json
{
  "items": [...],
  "page": 2,
  "page_size": 50,
  "total": 250,
  "pages": 5
}
```

### Filtrage Avancé

AzalScore supporte filtrage avancé via query parameters :
```http
GET /v2/commercial/customers?
  name__icontains=acme&
  created_at__gte=2026-01-01&
  customer_type__in=CUSTOMER,VIP
```

Opérateurs disponibles :
- `__eq` : Égal
- `__ne` : Différent
- `__gt` : Supérieur
- `__gte` : Supérieur ou égal
- `__lt` : Inférieur
- `__lte` : Inférieur ou égal
- `__in` : Dans liste
- `__icontains` : Contient (insensible casse)

---

## 16. Authentification API

### Headers Requis

#### Axonaut
```http
Authorization: Bearer {api_token}
Content-Type: application/json
```

#### AzalScore
```http
Authorization: Bearer {jwt_token}
X-Tenant-ID: {tenant_uuid}
Content-Type: application/json
```

**Différence majeure** : AzalScore requiert `X-Tenant-ID` pour toutes les requêtes (multi-tenant)

### Rate Limiting

| Plateforme | Limite | Window | Header |
|------------|--------|--------|--------|
| Axonaut | 1000 req/h | 1 heure | `X-RateLimit-Remaining` |
| AzalScore | 5000 req/h | 1 heure | `X-RateLimit-Remaining` |

---

## 17. Codes Erreur HTTP

### Mapping Codes

| Code | Axonaut | AzalScore |
|------|---------|-----------|
| 400 | Requête invalide | Validation failed |
| 401 | Non authentifié | Unauthorized |
| 403 | Accès refusé | Forbidden (RBAC) |
| 404 | Non trouvé | Not found |
| 409 | Conflit | Conflict (ex: duplicate) |
| 422 | - | Unprocessable Entity (validation) |
| 429 | Rate limit | Rate limit exceeded |
| 500 | Erreur serveur | Internal server error |

### Format Erreur

#### Axonaut
```json
{
  "error": "Validation failed",
  "message": "Email is required"
}
```

#### AzalScore
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is required",
    "details": [
      {
        "field": "email",
        "error": "required"
      }
    ]
  }
}
```

---

## 18. SDK & Bibliothèques

### SDKs Officiels

| Langage | Axonaut | AzalScore |
|---------|---------|-----------|
| Python | ✅ | ✅ |
| JavaScript/Node | ✅ | ✅ |
| PHP | ✅ | ✅ |
| Ruby | ⚠️ Communauté | ✅ |
| Go | ❌ | ✅ |
| .NET | ❌ | ✅ |

### Exemple Python

```python
# Axonaut
from axonaut import AxonautClient
client = AxonautClient(api_key="...")
customers = client.customers.list()

# AzalScore
from azalscore import AzalScoreClient
client = AzalScoreClient(
    api_key="...",
    tenant_id="..."
)
customers = client.commercial.customers.list()
```

---

## 19. Checklist Migration API

- [ ] Remplacer base URL (`axonaut.com` → `azalscore.com`)
- [ ] Ajouter header `X-Tenant-ID` à toutes les requêtes
- [ ] Convertir IDs numériques en UUIDs
- [ ] Adapter format pagination (`per_page` → `page_size`)
- [ ] Mettre à jour noms de champs (voir mappings)
- [ ] Implémenter gestion UUIDs (génération/stockage)
- [ ] Tester tous les endpoints critiques
- [ ] Mettre à jour webhooks (URL + secret)
- [ ] Adapter gestion erreurs (nouveaux codes/formats)
- [ ] Profiter des nouvelles fonctionnalités (IA, synchro bancaire, etc.)

---

## 20. Support

### Documentation
- **API Reference** : https://api.azalscore.com/docs
- **Postman Collection** : Disponible à l'import
- **GraphQL Playground** : https://api.azalscore.com/graphql

### Contact Technique
- **Email** : api@azalscore.com
- **Discord** : discord.gg/azalscore-dev
- **GitHub** : github.com/azalscore

---

**AzalScore API Team**  
*API-First, Developer-Friendly* 🚀
