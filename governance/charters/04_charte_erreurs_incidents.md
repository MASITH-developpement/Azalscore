# CHARTE ERREURS ET INCIDENTS AZALSCORE
## Gestion Normalisée des Erreurs et Incidents

**Version:** 1.0.0
**Statut:** DOCUMENT NORMATIF
**Date:** 2026-01-05
**Classification:** PUBLIC - OPPOSABLE
**Référence:** AZALS-GOV-04-v1.0.0

---

## 1. OBJECTIF

Cette charte définit la typologie des erreurs, les codes normalisés, les procédures de gestion des incidents, et le système d'alertes RED/ORANGE/GREEN.

---

## 2. PÉRIMÈTRE

- Toutes les erreurs applicatives
- Tous les incidents système
- Toutes les alertes métier
- Tous les logs et traces

---

## 3. TYPOLOGIE DES ERREURS

### 3.1 Catégories

| Catégorie | Préfixe | Description |
|-----------|---------|-------------|
| Validation | VAL | Erreur de validation des données |
| Authentification | AUTH | Erreur d'authentification |
| Autorisation | PERM | Erreur de permission |
| Tenant | TENANT | Erreur liée au tenant |
| Métier | BIZ | Erreur de logique métier |
| Technique | TECH | Erreur technique système |
| Sécurité | SEC | Incident de sécurité |
| IA | AI | Erreur liée à l'IA |

### 3.2 Niveaux de Sévérité

| Niveau | Code | Impact | Action |
|--------|------|--------|--------|
| CRITIQUE | 1 | Système inutilisable | Intervention immédiate |
| HAUTE | 2 | Fonctionnalité majeure KO | Intervention < 1h |
| MOYENNE | 3 | Fonctionnalité dégradée | Intervention < 4h |
| BASSE | 4 | Impact mineur | Planification normale |
| INFO | 5 | Information | Aucune action |

---

## 4. CODES D'ERREUR NORMALISÉS

### 4.1 Format

```
AZALS-{CATEGORIE}-{MODULE}-{NUMERO}

Exemples:
AZALS-VAL-FIN-001   # Validation Finance #001
AZALS-AUTH-CORE-002 # Authentification Core #002
AZALS-BIZ-COM-015   # Métier Commercial #015
```

### 4.2 Codes Core

| Code | Description |
|------|-------------|
| AZALS-AUTH-CORE-001 | Token JWT invalide |
| AZALS-AUTH-CORE-002 | Token JWT expiré |
| AZALS-AUTH-CORE-003 | Credentials invalides |
| AZALS-AUTH-CORE-004 | 2FA requis |
| AZALS-AUTH-CORE-005 | 2FA invalide |
| AZALS-PERM-CORE-001 | Permission insuffisante |
| AZALS-PERM-CORE-002 | Rôle non autorisé |
| AZALS-TENANT-CORE-001 | Tenant ID manquant |
| AZALS-TENANT-CORE-002 | Tenant ID invalide |
| AZALS-TENANT-CORE-003 | Accès cross-tenant bloqué |

### 4.3 Codes Métier (par module)

```python
# Finance
AZALS-BIZ-FIN-001  # Solde insuffisant
AZALS-BIZ-FIN-002  # Période fiscale clôturée
AZALS-BIZ-FIN-003  # Écriture déséquilibrée

# Commercial
AZALS-BIZ-COM-001  # Devis expiré
AZALS-BIZ-COM-002  # Stock insuffisant
AZALS-BIZ-COM-003  # Client bloqué

# HR
AZALS-BIZ-HR-001   # Employé non trouvé
AZALS-BIZ-HR-002   # Congés insuffisants
AZALS-BIZ-HR-003   # Période paie clôturée
```

---

## 5. FORMAT DES MESSAGES D'ERREUR

### 5.1 Structure Standard

```json
{
  "error": {
    "code": "AZALS-VAL-FIN-001",
    "message": "Le montant doit être positif",
    "severity": "MOYENNE",
    "timestamp": "2026-01-05T12:00:00Z",
    "trace_id": "550e8400-e29b-41d4-a716-446655440000",
    "details": {
      "field": "amount",
      "value": -100,
      "expected": "number > 0"
    },
    "help_url": "https://docs.azalscore.io/errors/AZALS-VAL-FIN-001"
  }
}
```

### 5.2 Messages Utilisateur vs Technique

```python
# Message utilisateur (affiché)
user_message = "Le montant saisi n'est pas valide. Veuillez entrer un nombre positif."

# Message technique (logs)
tech_message = "ValidationError: field='amount' value=-100 constraint='gt:0' schema='InvoiceCreate'"
```

### 5.3 Règle d'Or

```
RÈGLE: Jamais d'information sensible dans les messages utilisateur.

❌ "Erreur SQL: SELECT * FROM users WHERE password = 'xxx'"
✅ "Une erreur technique est survenue. Référence: AZALS-TECH-001"
```

---

## 6. SYSTÈME RED / ORANGE / GREEN

### 6.1 Définitions

| État | Signification | Déclencheur |
|------|---------------|-------------|
| 🔴 RED | CRITIQUE - Blocage | Trésorerie négative, Fraude détectée, Faille sécurité |
| 🟠 ORANGE | ATTENTION - Surveillance | Seuil dépassé, Anomalie détectée, Performance dégradée |
| 🟢 GREEN | NORMAL | Fonctionnement nominal |

### 6.2 Règles RED

```
RÈGLE ABSOLUE: Un état RED ne peut JAMAIS être rétrogradé automatiquement.

- Seule une validation HUMAINE peut lever un RED
- Chaque RED est journalisé définitivement
- Le workflow RED en 3 étapes est OBLIGATOIRE :
  1. ACKNOWLEDGE - Accusé de lecture
  2. COMPLETENESS - Confirmation des informations
  3. FINAL - Validation finale
```

### 6.3 Déclencheurs RED Automatiques

| Situation | Module | Action |
|-----------|--------|--------|
| Trésorerie prévisionnelle < 0 | Treasury | Blocage + Alerte |
| Tentative accès cross-tenant | Core | Blocage + Alerte |
| Échec auth répété (>5) | Auth | Blocage compte |
| Anomalie IA détectée | AI | Suspension IA |

### 6.4 Workflow de Résolution RED

```
┌─────────────────────────────────────────────────────────────┐
│                    🔴 ALERTE RED DÉCLENCHÉE                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 1: ACKNOWLEDGE                                        │
│ "J'ai pris connaissance de l'alerte et de ses implications" │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 2: COMPLETENESS                                       │
│ "J'ai vérifié que toutes les informations sont complètes"   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 3: FINAL                                              │
│ "Je valide la résolution de cette alerte RED"               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    🟢 ALERTE RED RÉSOLUE                     │
│           (Rapport immutable généré et archivé)             │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. GESTION DES INCIDENTS

### 7.1 Classification

| Niveau | Description | SLA Réponse | SLA Résolution |
|--------|-------------|-------------|----------------|
| P0 | Système down | 15 min | 2h |
| P1 | Fonctionnalité critique KO | 30 min | 4h |
| P2 | Fonctionnalité importante dégradée | 2h | 24h |
| P3 | Bug non bloquant | 24h | 1 semaine |
| P4 | Amélioration | Backlog | Planifié |

### 7.2 Processus Incident

```
1. DÉTECTION
   └── Monitoring / Utilisateur / IA

2. QUALIFICATION
   └── Niveau (P0-P4) + Catégorie + Impact

3. COMMUNICATION
   └── Parties prenantes informées

4. INVESTIGATION
   └── Analyse cause racine

5. RÉSOLUTION
   └── Fix + Tests + Déploiement

6. POST-MORTEM
   └── Rapport + Actions correctives
```

### 7.3 Template Incident

```markdown
# INCIDENT AZALSCORE

**ID:** INC-2026-XXXX
**Date:** YYYY-MM-DD HH:MM
**Niveau:** P0/P1/P2/P3/P4
**Statut:** OUVERT/EN COURS/RÉSOLU/CLÔTURÉ

## Description
{description de l'incident}

## Impact
- Utilisateurs affectés: {nombre}
- Fonctionnalités impactées: {liste}
- Durée: {temps}

## Timeline
- HH:MM - Détection
- HH:MM - Qualification
- HH:MM - Investigation
- HH:MM - Résolution
- HH:MM - Clôture

## Cause Racine
{analyse}

## Actions Correctives
- [ ] Action 1
- [ ] Action 2

## Leçons Apprises
{enseignements}
```

---

## 8. INTERDICTIONS

### 8.1 Erreurs Silencieuses

```python
# ❌ INTERDIT - Erreur silencieuse
try:
    process_payment()
except Exception:
    pass  # JAMAIS !

# ✅ OBLIGATOIRE - Erreur tracée
try:
    process_payment()
except PaymentError as e:
    logger.error(f"Payment failed: {e}", extra={"trace_id": trace_id})
    raise HTTPException(status_code=400, detail=str(e))
```

### 8.2 Messages Trompeurs

```python
# ❌ INTERDIT - Message trompeur
raise HTTPException(status_code=200, detail="Erreur interne")

# ✅ CORRECT - Message honnête
raise HTTPException(status_code=500, detail="Erreur serveur. Référence: XXX")
```

### 8.3 Masquage d'Incidents

- ❌ Modifier les logs après coup
- ❌ Ne pas déclarer un incident sécurité
- ❌ Rétrograder un RED sans validation humaine

---

## 9. JOURNALISATION

### 9.1 Niveaux de Log

| Niveau | Usage |
|--------|-------|
| CRITICAL | Erreur fatale système |
| ERROR | Erreur applicative |
| WARNING | Situation anormale |
| INFO | Événement métier |
| DEBUG | Détail technique (dev) |

### 9.2 Format Standard

```json
{
  "timestamp": "2026-01-05T12:00:00.000Z",
  "level": "ERROR",
  "logger": "app.modules.finance.service",
  "message": "Invoice creation failed",
  "trace_id": "uuid",
  "tenant_id": "tenant-123",
  "user_id": 42,
  "extra": {
    "invoice_data": "...",
    "error_code": "AZALS-BIZ-FIN-003"
  }
}
```

---

## 10. CONSÉQUENCES DU NON-RESPECT

| Violation | Conséquence |
|-----------|-------------|
| Erreur silencieuse | Correction immédiate obligatoire |
| RED non déclaré | Incident de gouvernance |
| Log falsifié | Exclusion du projet |
| Incident masqué | Sanctions graves |

---

*Document généré et validé le 2026-01-05*
*Classification: PUBLIC - OPPOSABLE*
*Référence: AZALS-GOV-04-v1.0.0*
