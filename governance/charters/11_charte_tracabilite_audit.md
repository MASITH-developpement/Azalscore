# CHARTE TRAÇABILITÉ ET AUDIT AZALSCORE
## Journalisation et Auditabilité Totale

**Version:** 1.0.0
**Statut:** DOCUMENT NORMATIF
**Date:** 2026-01-05
**Classification:** CONFIDENTIEL - OPPOSABLE
**Référence:** AZALS-GOV-11-v1.0.0

---

## 1. OBJECTIF

Cette charte définit les exigences de traçabilité, les mécanismes de journalisation, et les règles d'audit pour AZALSCORE.

**PRINCIPE FONDAMENTAL:**
```
TOUTE ACTION EST TRACÉE.
RIEN NE SE PERD, RIEN NE S'EFFACE.
L'AUDIT EST POSSIBLE À TOUT MOMENT.
```

---

## 2. PÉRIMÈTRE

- Actions utilisateur
- Actions système
- Propositions et actions IA
- Modifications de données
- Accès et authentification
- Incidents et alertes

---

## 3. PRINCIPES DE TRAÇABILITÉ

### 3.1 Traçabilité Totale

```
RÈGLE: Chaque action répond aux questions:
- QUI a fait l'action ?
- QUOI a été fait ?
- QUAND l'action a été faite ?
- OÙ dans le système ?
- POURQUOI (contexte) ?
- COMMENT (détails techniques) ?
```

### 3.2 Inviolabilité

```
RÈGLE: Les traces sont INVIOLABLES.

- Append-only : ajout uniquement
- Pas de modification possible
- Pas de suppression possible
- Horodatage serveur certifié
- Signature numérique si applicable
```

### 3.3 Disponibilité

```
RÈGLE: Les traces sont accessibles pour audit.

- Consultation autorisée aux personnes habilitées
- Export possible sur demande justifiée
- Rétention suffisante pour obligations légales
- Recherche et filtrage performants
```

---

## 4. TYPES DE JOURNAUX

### 4.1 Journal d'Audit Métier

```json
{
  "type": "BUSINESS_AUDIT",
  "timestamp": "2026-01-05T12:00:00.000Z",
  "tenant_id": "tenant-123",
  "user_id": 42,
  "user_email": "user@example.com",
  "action": "INVOICE_CREATED",
  "entity_type": "Invoice",
  "entity_id": "inv-789",
  "details": {
    "invoice_number": "INV-2026-001",
    "amount": 1500.00,
    "customer_id": 15
  },
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "trace_id": "uuid-trace"
}
```

### 4.2 Journal de Sécurité

```json
{
  "type": "SECURITY_LOG",
  "timestamp": "2026-01-05T12:00:00.000Z",
  "event": "AUTH_SUCCESS",
  "severity": "INFO",
  "tenant_id": "tenant-123",
  "user_id": 42,
  "ip_address": "192.168.1.1",
  "details": {
    "method": "password",
    "2fa_used": true
  },
  "geo_location": "Paris, FR"
}
```

### 4.3 Journal Système

```json
{
  "type": "SYSTEM_LOG",
  "timestamp": "2026-01-05T12:00:00.000Z",
  "level": "ERROR",
  "service": "payment-processor",
  "message": "Payment gateway timeout",
  "details": {
    "gateway": "stripe",
    "timeout_ms": 30000,
    "retry_count": 3
  },
  "trace_id": "uuid-trace"
}
```

### 4.4 Journal IA

```json
{
  "type": "AI_LOG",
  "timestamp": "2026-01-05T12:00:00.000Z",
  "tenant_id": "tenant-123",
  "ai_system": "treasury_predictor",
  "action": "PREDICTION_GENERATED",
  "input_summary": "30 days forecast request",
  "output": {
    "prediction": 15000,
    "confidence": 0.85,
    "model_version": "1.2.0"
  },
  "human_validation": null,
  "executed": false
}
```

---

## 5. ÉVÉNEMENTS À JOURNALISER

### 5.1 Obligatoires (CRITIQUE)

| Catégorie | Événements |
|-----------|------------|
| Authentification | Login, Logout, Échec auth, 2FA |
| Autorisation | Accès refusé, Changement permission |
| Données sensibles | Création, Modification, Suppression, Export |
| Actions financières | Paiement, Facture, Engagement |
| Alertes RED | Déclenchement, Validation, Résolution |
| Système | Démarrage, Arrêt, Configuration |
| IA | Toute action, Toute suggestion |

### 5.2 Recommandés

| Catégorie | Événements |
|-----------|------------|
| Navigation | Pages visitées (agrégé) |
| Recherche | Requêtes (anonymisé) |
| Performance | Temps de réponse |
| Erreurs | Exceptions non critiques |

### 5.3 Matrice de Journalisation

| Action | Audit | Sécurité | Système | IA |
|--------|-------|----------|---------|-----|
| Login réussi | | ✅ | | |
| Login échoué | | ✅ | | |
| Créer facture | ✅ | | | |
| Modifier client | ✅ | | | |
| Supprimer donnée | ✅ | ✅ | | |
| Erreur système | | | ✅ | |
| Prédiction IA | | | | ✅ |
| RED déclenché | ✅ | ✅ | | |

---

## 6. STRUCTURE DU JOURNAL

### 6.1 Champs Obligatoires

```python
REQUIRED_FIELDS = {
    "timestamp": "ISO 8601 UTC",
    "type": "BUSINESS_AUDIT | SECURITY_LOG | SYSTEM_LOG | AI_LOG",
    "tenant_id": "string (si applicable)",
    "trace_id": "UUID de corrélation"
}
```

### 6.2 Champs Contextuels

```python
CONTEXTUAL_FIELDS = {
    "user_id": "int (si authentifié)",
    "ip_address": "string",
    "user_agent": "string",
    "action": "string descriptif",
    "entity_type": "string (si entité)",
    "entity_id": "string (si entité)",
    "details": "object JSON",
    "severity": "CRITICAL | ERROR | WARNING | INFO | DEBUG"
}
```

---

## 7. STOCKAGE

### 7.1 Base de Données Audit

```sql
CREATE TABLE core_audit_journal (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    type VARCHAR(50) NOT NULL,
    tenant_id VARCHAR(255),
    user_id INTEGER,
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(255),
    entity_id VARCHAR(255),
    details JSONB,
    ip_address VARCHAR(45),
    trace_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RÈGLE: Pas de UPDATE ni DELETE sur cette table
-- Enforced par trigger ou permissions DB
```

### 7.2 Rétention

| Type de Log | Rétention Active | Archive | Total |
|-------------|------------------|---------|-------|
| Audit métier | 2 ans | 8 ans | 10 ans |
| Sécurité | 1 an | 4 ans | 5 ans |
| Système | 90 jours | 1 an | ~15 mois |
| IA | 1 an | 2 ans | 3 ans |
| RED | Permanent | - | Illimité |

### 7.3 Protection

```
MESURES DE PROTECTION:

1. Chiffrement au repos (AES-256)
2. Accès restreint (RBAC)
3. Pas de modification possible (append-only)
4. Backups réguliers et testés
5. Réplication géographique (si critique)
```

---

## 8. AUDIT

### 8.1 Types d'Audit

| Type | Fréquence | Périmètre | Auditeur |
|------|-----------|-----------|----------|
| Continu | Temps réel | Alertes automatiques | Système |
| Périodique | Mensuel | Revue des accès | Sécurité |
| Annuel | Annuel | Conformité complète | Externe |
| Ad-hoc | Sur demande | Investigation | Variable |

### 8.2 Capacités d'Audit

```
L'AUDIT PERMET DE:

✅ Reconstituer l'historique d'une entité
✅ Identifier qui a fait quoi et quand
✅ Tracer une session utilisateur complète
✅ Analyser les patterns d'usage
✅ Détecter les anomalies
✅ Prouver la conformité
✅ Investiguer un incident
```

### 8.3 Outils d'Audit

```python
# API d'audit
GET /audit/search
    ?tenant_id=xxx
    &user_id=42
    &action=INVOICE_CREATED
    &date_from=2026-01-01
    &date_to=2026-01-31
    &entity_type=Invoice
    &entity_id=inv-789

# Réponse paginée avec tous les événements correspondants
```

---

## 9. REJEU HISTORIQUE

### 9.1 Principe

```
RÈGLE: L'état d'une entité peut être reconstruit à tout moment passé.

Le journal permet de:
- Voir l'état à une date donnée
- Comprendre l'évolution dans le temps
- Identifier les modifications
- Restaurer si nécessaire
```

### 9.2 Implémentation

```python
def get_entity_state_at(entity_type: str, entity_id: str, at_date: datetime):
    """
    Reconstruit l'état d'une entité à une date donnée
    en rejouant les événements du journal.
    """
    events = audit_log.query(
        entity_type=entity_type,
        entity_id=entity_id,
        timestamp__lte=at_date
    ).order_by('timestamp')

    state = {}
    for event in events:
        apply_event(state, event)

    return state
```

---

## 10. ALERTES ET MONITORING

### 10.1 Alertes Automatiques

| Condition | Action |
|-----------|--------|
| 5 échecs auth en 5min | Alerte sécurité |
| Accès données sensibles | Notification |
| Export massif | Notification manager |
| Pattern anormal | Investigation IA |

### 10.2 Dashboards

```
DASHBOARDS DISPONIBLES:

- Activité par tenant
- Connexions et sécurité
- Actions critiques
- Erreurs système
- Activité IA
- Conformité RGPD
```

---

## 11. ACCÈS AUX JOURNAUX

### 11.1 Qui Peut Accéder

| Rôle | Accès | Périmètre |
|------|-------|-----------|
| Admin Système | Complet | Tous tenants (technique) |
| Admin Tenant | Limité | Son tenant uniquement |
| Auditeur | Lecture | Selon mission |
| Dirigeant | Lecture | Son tenant |
| Utilisateur | Aucun | Pas d'accès direct |

### 11.2 Procédure d'Accès

```
POUR ACCÉDER AUX JOURNAUX:

1. Demande formelle avec justification
2. Validation par responsable
3. Accès limité dans le temps
4. Journalisation de l'accès au journal (méta-audit)
5. Révocation automatique après délai
```

---

## 12. INTERDICTIONS

### 12.1 Absolues

- ❌ Modifier un enregistrement de journal
- ❌ Supprimer un enregistrement de journal
- ❌ Désactiver la journalisation
- ❌ Accéder aux journaux sans autorisation
- ❌ Contourner la traçabilité

### 12.2 Conséquences

| Violation | Conséquence |
|-----------|-------------|
| Modification journal | Incident critique + investigation |
| Suppression journal | Incident critique + sanctions |
| Désactivation | Blocage système + alerte |
| Accès non autorisé | Révocation + audit |

---

*Document généré et validé le 2026-01-05*
*Classification: CONFIDENTIEL - OPPOSABLE*
*Référence: AZALS-GOV-11-v1.0.0*

**TOUT EST TRACÉ, RIEN N'EST OUBLIÉ.**
