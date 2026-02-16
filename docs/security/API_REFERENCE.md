# AZALSCORE API Reference

Documentation de référence des APIs de sécurité et des services métier.

## Table des matières

1. [Authentification](#authentification)
2. [Sessions](#sessions)
3. [MFA](#mfa)
4. [Audit](#audit)
5. [Import/Export](#importexport)
6. [Workflows](#workflows)
7. [Notifications](#notifications)
8. [Reporting](#reporting)

---

## Authentification

### Créer une session

```http
POST /api/v1/auth/session
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "********",
  "tenant_id": "tenant_001",
  "mfa_code": "123456"  // Optionnel si MFA requis
}
```

**Réponse**:
```json
{
  "session_id": "sess_abc123",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "rt_xyz789...",
  "expires_in": 900,
  "token_type": "Bearer",
  "mfa_required": false
}
```

### Rafraîchir le token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "rt_xyz789..."
}
```

**Réponse**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "rt_new123...",
  "expires_in": 900
}
```

### Déconnexion

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

---

## Sessions

### Lister les sessions actives

```http
GET /api/v1/sessions
Authorization: Bearer <access_token>
```

**Réponse**:
```json
{
  "sessions": [
    {
      "id": "sess_abc123",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2024-01-15T10:00:00Z",
      "last_activity": "2024-01-15T14:30:00Z",
      "is_current": true
    }
  ]
}
```

### Révoquer une session

```http
DELETE /api/v1/sessions/{session_id}
Authorization: Bearer <access_token>
```

---

## MFA

### Configurer TOTP

```http
POST /api/v1/mfa/totp/setup
Authorization: Bearer <access_token>
```

**Réponse**:
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,...",
  "backup_codes": [
    "ABCD-1234-EFGH",
    "IJKL-5678-MNOP"
  ]
}
```

### Activer TOTP

```http
POST /api/v1/mfa/totp/activate
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "code": "123456"
}
```

### Vérifier MFA

```http
POST /api/v1/mfa/verify
Content-Type: application/json

{
  "user_id": "user_123",
  "code": "123456",
  "method": "totp"
}
```

**Réponse**:
```json
{
  "success": true,
  "method": "totp",
  "verified_at": "2024-01-15T10:05:00Z"
}
```

### Lister les méthodes MFA

```http
GET /api/v1/mfa/methods
Authorization: Bearer <access_token>
```

**Réponse**:
```json
{
  "methods": [
    {
      "type": "totp",
      "enabled": true,
      "configured_at": "2024-01-01T00:00:00Z"
    },
    {
      "type": "backup_codes",
      "enabled": true,
      "remaining_codes": 8
    }
  ]
}
```

---

## Audit

### Journaliser un événement

```http
POST /api/v1/audit/events
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "category": "data_access",
  "action": "view_invoice",
  "description": "Consultation facture FA-2024-001",
  "target": {
    "entity_type": "invoice",
    "entity_id": "FA-2024-001"
  },
  "context": {
    "reason": "client_request"
  }
}
```

### Rechercher des événements

```http
GET /api/v1/audit/events?category=authentication&start_date=2024-01-01&limit=100
Authorization: Bearer <access_token>
```

**Paramètres**:
| Paramètre | Type | Description |
|-----------|------|-------------|
| category | string | Catégorie d'événement |
| action | string | Action spécifique |
| start_date | datetime | Date de début |
| end_date | datetime | Date de fin |
| user_id | string | Filtrer par utilisateur |
| limit | integer | Nombre max de résultats |
| offset | integer | Offset pour pagination |

**Réponse**:
```json
{
  "events": [
    {
      "id": "evt_abc123",
      "timestamp": "2024-01-15T10:00:00Z",
      "category": "authentication",
      "action": "login_success",
      "description": "Connexion réussie",
      "actor": {
        "user_id": "user_123",
        "ip_address": "192.168.1.100"
      },
      "severity": "info",
      "hash_chain": "a1b2c3..."
    }
  ],
  "total": 1,
  "has_more": false
}
```

### Vérifier l'intégrité

```http
POST /api/v1/audit/verify-integrity
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "category": "authentication",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

**Réponse**:
```json
{
  "valid": true,
  "events_verified": 1500,
  "verification_time_ms": 234
}
```

---

## Import/Export

### Prévisualiser un import

```http
POST /api/v1/import/preview
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <fichier>
format: csv
delimiter: ;
max_rows: 10
```

**Réponse**:
```json
{
  "headers": ["code", "nom", "montant"],
  "preview_rows": [
    {"code": "CLI001", "nom": "Alpha", "montant": "1500"}
  ],
  "total_rows_estimated": 100
}
```

### Valider un import

```http
POST /api/v1/import/validate
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "file_id": "file_abc123",
  "format": "csv",
  "mappings": [
    {
      "source_field": "code",
      "target_field": "client_code",
      "data_type": "string",
      "required": true
    },
    {
      "source_field": "montant",
      "target_field": "amount",
      "data_type": "decimal"
    }
  ]
}
```

**Réponse**:
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    {
      "row": 5,
      "field": "montant",
      "message": "Valeur vide, sera ignorée"
    }
  ]
}
```

### Lancer un import

```http
POST /api/v1/import/execute
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "file_id": "file_abc123",
  "template_id": "client_import",
  "options": {
    "stop_on_error": false,
    "batch_size": 500
  }
}
```

**Réponse**:
```json
{
  "import_id": "imp_xyz789",
  "status": "processing",
  "progress_url": "/api/v1/import/imp_xyz789/progress"
}
```

### Exporter des données

```http
POST /api/v1/export
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "entity_type": "invoices",
  "format": "excel",
  "filters": {
    "date_from": "2024-01-01",
    "date_to": "2024-01-31",
    "status": "paid"
  },
  "columns": ["number", "date", "client", "amount"]
}
```

**Réponse**:
```json
{
  "export_id": "exp_abc123",
  "status": "ready",
  "download_url": "/api/v1/export/exp_abc123/download",
  "file_size": 45678,
  "expires_at": "2024-01-16T10:00:00Z"
}
```

### Export FEC (conformité fiscale)

```http
POST /api/v1/export/fec
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "fiscal_year": 2024,
  "siren": "123456789"
}
```

---

## Workflows

### Lister les workflows

```http
GET /api/v1/workflows
Authorization: Bearer <access_token>
```

**Réponse**:
```json
{
  "workflows": [
    {
      "id": "wf_invoice_approval",
      "name": "Approbation Factures",
      "status": "active",
      "version": 2,
      "triggers": ["event:invoice.created"]
    }
  ]
}
```

### Déclencher un workflow

```http
POST /api/v1/workflows/{workflow_id}/trigger
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "entity_type": "invoice",
  "entity_id": "INV-2024-001",
  "input_variables": {
    "priority": "high"
  }
}
```

**Réponse**:
```json
{
  "execution_id": "exec_abc123",
  "workflow_id": "wf_invoice_approval",
  "status": "running"
}
```

### Statut d'exécution

```http
GET /api/v1/workflows/executions/{execution_id}
Authorization: Bearer <access_token>
```

**Réponse**:
```json
{
  "id": "exec_abc123",
  "workflow_id": "wf_invoice_approval",
  "status": "waiting",
  "current_action": "approval_step",
  "started_at": "2024-01-15T10:00:00Z",
  "action_results": [
    {
      "action_id": "notify_manager",
      "status": "completed",
      "duration_ms": 150
    }
  ]
}
```

### Approbations en attente

```http
GET /api/v1/workflows/approvals/pending
Authorization: Bearer <access_token>
```

**Réponse**:
```json
{
  "approvals": [
    {
      "id": "apr_xyz789",
      "workflow_name": "Approbation Factures",
      "entity_type": "invoice",
      "entity_id": "INV-2024-001",
      "entity_summary": "Facture 2500€ - Client ABC",
      "created_at": "2024-01-15T10:00:00Z",
      "expires_at": "2024-01-17T10:00:00Z"
    }
  ]
}
```

### Traiter une approbation

```http
POST /api/v1/workflows/approvals/{approval_id}/decide
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "approved": true,
  "comment": "Validé après vérification"
}
```

---

## Notifications

### Envoyer une notification

```http
POST /api/v1/notifications/send
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "template_id": "invoice_created",
  "recipient": "user@example.com",
  "variables": {
    "invoice_number": "INV-2024-001",
    "amount": "1500.00"
  },
  "channels": ["email", "in_app"]
}
```

### Lister les notifications

```http
GET /api/v1/notifications?unread_only=true
Authorization: Bearer <access_token>
```

**Réponse**:
```json
{
  "notifications": [
    {
      "id": "notif_abc123",
      "title": "Nouvelle facture",
      "body": "La facture INV-2024-001 a été créée",
      "channel": "in_app",
      "read": false,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "unread_count": 5
}
```

### Marquer comme lu

```http
PATCH /api/v1/notifications/{notification_id}/read
Authorization: Bearer <access_token>
```

### Préférences utilisateur

```http
GET /api/v1/notifications/preferences
Authorization: Bearer <access_token>
```

```http
PUT /api/v1/notifications/preferences
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "enabled_channels": ["email", "in_app"],
  "quiet_hours": {
    "start": 22,
    "end": 8
  },
  "category_preferences": {
    "marketing": false,
    "security": true
  }
}
```

---

## Reporting

### Lister les templates de rapport

```http
GET /api/v1/reports/templates
Authorization: Bearer <access_token>
```

### Générer un rapport

```http
POST /api/v1/reports/generate
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "template_id": "monthly_sales",
  "format": "pdf",
  "parameters": {
    "month": "2024-01",
    "include_charts": true
  }
}
```

**Réponse**:
```json
{
  "report_id": "rpt_abc123",
  "status": "generating",
  "estimated_time_seconds": 30
}
```

### Télécharger un rapport

```http
GET /api/v1/reports/{report_id}/download
Authorization: Bearer <access_token>
```

### Planifier un rapport

```http
POST /api/v1/reports/schedules
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "template_id": "weekly_summary",
  "name": "Rapport hebdomadaire",
  "cron": "0 8 * * 1",
  "format": "pdf",
  "recipients": ["team@example.com"],
  "parameters": {}
}
```

---

## Codes d'erreur

| Code | Description |
|------|-------------|
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Non autorisé |
| 404 | Ressource non trouvée |
| 409 | Conflit (ex: session déjà révoquée) |
| 422 | Données non valides |
| 429 | Trop de requêtes (rate limit) |
| 500 | Erreur serveur |

## Rate Limiting

- **Par utilisateur**: 100 requêtes/minute
- **Par tenant**: 1000 requêtes/minute
- **Export/Import**: 10 requêtes/minute

Headers de réponse:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312800
```
