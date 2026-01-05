# CHARTE IA AZALSCORE
## Encadrement de l'Intelligence Artificielle

**Version:** 1.0.0
**Statut:** DOCUMENT CRITIQUE
**Date:** 2026-01-05
**Classification:** PUBLIC - OPPOSABLE
**Référence:** AZALS-GOV-05-v1.0.0

---

## 1. OBJECTIF

Cette charte définit le rôle, les limites et l'encadrement de toute intelligence artificielle interagissant avec AZALSCORE, qu'elle soit intégrée au système ou externe (Claude, GPT, etc.).

**PRINCIPE FONDAMENTAL:**
```
L'IA EST UN ASSISTANT ET UN ANALYSTE.
L'IA N'EST JAMAIS UNE AUTORITÉ DÉCISIONNELLE.
L'HUMAIN RESTE MAÎTRE DE TOUTES LES DÉCISIONS CRITIQUES.
```

---

## 2. PÉRIMÈTRE

### 2.1 Types d'IA Concernés

| Type | Description | Exemple |
|------|-------------|---------|
| IA Intégrée | Module IA AZALSCORE | `ai_assistant/` |
| IA Générative | LLM pour code/texte | Claude, GPT |
| IA Prédictive | ML pour prévisions | Module BI/Prédictions |
| IA Externe | Services tiers | API OpenAI |

### 2.2 Applicabilité

Cette charte s'applique à :
- Tout code IA dans AZALSCORE
- Toute IA générant du code pour AZALSCORE
- Toute IA accédant aux données AZALSCORE
- Toute IA proposant des actions

---

## 3. RÔLE DE L'IA

### 3.1 Rôles Autorisés

| Rôle | Description | Exemple |
|------|-------------|---------|
| **ASSISTANT** | Aide à la saisie, suggestions | Autocomplétion, templates |
| **ANALYSTE** | Analyse de données, rapports | Tableaux de bord, tendances |
| **PRÉDICTEUR** | Prévisions basées sur historique | Trésorerie prévisionnelle |
| **DÉTECTEUR** | Anomalies, fraudes potentielles | Alertes automatiques |
| **GÉNÉRATEUR** | Création de contenu/code | Documentation, tests |

### 3.2 Rôles INTERDITS

| Rôle Interdit | Raison |
|---------------|--------|
| **DÉCIDEUR** | L'humain décide |
| **EXÉCUTEUR FINANCIER** | Risque financier |
| **MODIFICATEUR CORE** | Sécurité système |
| **SUPPRESSEUR** | Irréversibilité |
| **VALIDATEUR** | Responsabilité humaine |

---

## 4. INTERDICTIONS ABSOLUES

### 4.1 Actions Interdites

```
❌ INTERDICTIONS FORMELLES:

1. Prendre une décision financière autonome
   - Aucun paiement sans validation humaine
   - Aucune écriture comptable auto-validée
   - Aucun engagement contractuel

2. Modifier le Core AZALSCORE
   - Aucune modification de app/core/*
   - Aucun contournement de sécurité
   - Aucune désactivation d'audit

3. Supprimer des données
   - Aucune suppression définitive
   - Aucun effacement de logs
   - Aucune purge non validée

4. Accéder à des données interdites
   - Pas de cross-tenant
   - Pas de données non autorisées
   - Pas de secrets/credentials

5. Opérer sans traçabilité
   - Toute action est journalisée
   - Aucun mode "silencieux"
   - Audit complet obligatoire
```

### 4.2 Données Interdites

| Catégorie | Accès IA |
|-----------|----------|
| Mots de passe | ❌ INTERDIT |
| Tokens JWT | ❌ INTERDIT |
| Secrets API | ❌ INTERDIT |
| Données autres tenants | ❌ INTERDIT |
| Logs d'audit | ❌ LECTURE SEULE |
| Données personnelles sensibles | ⚠️ RESTREINT |

---

## 5. RÈGLES OBLIGATOIRES

### 5.1 Journalisation

```python
# OBLIGATOIRE: Toute action IA est journalisée
@log_ai_action
def ai_suggest_invoice_amount(context: AIContext) -> Suggestion:
    """
    Logs automatiques:
    - Timestamp
    - User ID
    - Tenant ID
    - Action
    - Input (anonymisé)
    - Output
    - Confidence
    - Decision: SUGGESTION (pas EXECUTION)
    """
    pass
```

### 5.2 Validation Humaine

```python
# OBLIGATOIRE: Actions critiques = validation humaine
class AIAction:
    requires_human_validation: bool = True  # Par défaut

    CRITICAL_ACTIONS = [
        "financial_transaction",
        "data_deletion",
        "user_creation",
        "permission_change",
        "system_configuration"
    ]
```

### 5.3 Réversibilité

```
RÈGLE: Toute action IA doit être réversible.

- Suggestions peuvent être ignorées
- Prédictions peuvent être écartées
- Détections peuvent être marquées faux-positif
- Aucune action irréversible autonome
```

### 5.4 Explicabilité

```python
# OBLIGATOIRE: L'IA explique ses recommandations
class AIRecommendation:
    suggestion: str
    confidence: float  # 0.0 - 1.0
    reasoning: str     # Explication compréhensible
    data_sources: List[str]  # D'où vient l'analyse
    limitations: List[str]   # Ce que l'IA ne sait pas
```

---

## 6. ARCHITECTURE IA

### 6.1 Isolation

```
┌─────────────────────────────────────────────────┐
│                  AZALSCORE                       │
│  ┌───────────────────────────────────────────┐  │
│  │              CORE (PROTÉGÉ)                │  │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐        │  │
│  │  │Auth │ │Perm │ │Audit│ │ DB  │        │  │
│  │  └─────┘ └─────┘ └─────┘ └─────┘        │  │
│  └───────────────────────────────────────────┘  │
│                      ▲                          │
│                      │ LECTURE SEULE            │
│  ┌───────────────────┴───────────────────────┐  │
│  │           MODULE IA (SANDBOX)              │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────────┐ │  │
│  │  │Prédiction│ │Détection│ │Recommandation│ │  │
│  │  └─────────┘ └─────────┘ └─────────────┘ │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### 6.2 Permissions IA

```python
AI_PERMISSIONS = {
    "core": {
        "read": False,   # Pas d'accès direct
        "write": False,  # JAMAIS
    },
    "modules": {
        "read": True,    # Données métier autorisées
        "write": False,  # Suggestions seulement
    },
    "audit": {
        "read": True,    # Pour analyse
        "write": True,   # Ses propres logs
    }
}
```

---

## 7. RÉVOCABILITÉ

### 7.1 Principe

```
RÈGLE: L'IA est révocable à tout moment, sans préavis.

Un administrateur peut :
- Désactiver l'IA globalement
- Désactiver l'IA par module
- Révoquer les droits d'une IA externe
- Annuler des suggestions en masse
```

### 7.2 Procédure de Révocation

```
1. DÉCISION
   └── Admin décide de révoquer l'IA

2. DÉSACTIVATION
   └── Kill switch activé (< 1 seconde)

3. ISOLATION
   └── IA coupée de toutes les données

4. AUDIT
   └── Revue des actions passées

5. RAPPORT
   └── Documentation de l'incident
```

### 7.3 Kill Switch

```python
# Implémentation obligatoire
class AIKillSwitch:
    @staticmethod
    def deactivate_all():
        """Désactive TOUTE l'IA immédiatement"""
        settings.AI_ENABLED = False
        cache.set("ai_killswitch", True)
        notify_admins("AI deactivated")
        log_security_event("AI_KILLSWITCH_ACTIVATED")
```

---

## 8. LIMITES TECHNIQUES

### 8.1 Rate Limiting

| Action | Limite |
|--------|--------|
| Suggestions par minute | 60 |
| Analyses par heure | 100 |
| Prédictions par jour | 1000 |
| Tokens API externes | Budget défini |

### 8.2 Timeout

```python
AI_TIMEOUTS = {
    "suggestion": 5,      # 5 secondes max
    "analysis": 30,       # 30 secondes max
    "prediction": 60,     # 1 minute max
    "batch_job": 3600,    # 1 heure max
}
```

### 8.3 Fallback

```
RÈGLE: Le système fonctionne SANS IA.

Si l'IA échoue :
- Le système continue normalement
- Les fonctionnalités restent disponibles
- L'utilisateur est notifié
- Aucune dégradation critique
```

---

## 9. IA GÉNÉRATIVE (CODE)

### 9.1 Règles pour Claude/GPT

Quand une IA génère du code AZALSCORE :

```
OBLIGATIONS:
✅ Respecter toutes les chartes
✅ Ne jamais modifier le Core
✅ Inclure les tests
✅ Documenter le code
✅ Vérifier la sécurité
✅ Respecter l'isolation tenant

INTERDICTIONS:
❌ Hardcoder des secrets
❌ Créer des backdoors
❌ Ignorer les validations
❌ Bypasser l'authentification
❌ Accéder cross-tenant
```

### 9.2 Revue Obligatoire

```
Tout code généré par IA DOIT être:
1. Revu par un humain
2. Testé automatiquement
3. Validé par CI/CD
4. Approuvé avant merge
```

---

## 10. AUDIT IA

### 10.1 Logs Obligatoires

```json
{
  "ai_action_log": {
    "timestamp": "2026-01-05T12:00:00Z",
    "ai_system": "azalscore_predictor",
    "ai_version": "1.0.0",
    "tenant_id": "tenant-123",
    "user_id": 42,
    "action": "treasury_prediction",
    "input_hash": "sha256:...",
    "output": {
      "prediction": 15000,
      "confidence": 0.85
    },
    "human_validation": null,
    "executed": false
  }
}
```

### 10.2 Métriques

| Métrique | Description |
|----------|-------------|
| Précision | % prédictions correctes |
| Adoption | % suggestions acceptées |
| Faux positifs | Alertes non pertinentes |
| Temps réponse | Latence moyenne |

---

## 11. CONSÉQUENCES DU NON-RESPECT

### 11.1 Pour l'IA Intégrée

| Violation | Conséquence |
|-----------|-------------|
| Action non journalisée | Désactivation module |
| Accès données interdites | Révocation immédiate |
| Action financière autonome | Kill switch + audit |
| Modification Core | Incident sécurité |

### 11.2 Pour l'IA Générative

| Violation | Conséquence |
|-----------|-------------|
| Code non conforme | Rejet automatique |
| Secret hardcodé | Revue sécurité |
| Bypass sécurité | Exclusion contribution |

---

## 12. ENGAGEMENT IA

Toute IA interagissant avec AZALSCORE s'engage à :

1. **Assister** sans décider
2. **Analyser** sans exécuter
3. **Suggérer** sans imposer
4. **Tracer** toutes ses actions
5. **Accepter** la révocation

---

*Document généré et validé le 2026-01-05*
*Classification: PUBLIC - OPPOSABLE*
*Référence: AZALS-GOV-05-v1.0.0*

**L'IA PROPOSE, L'HUMAIN DISPOSE.**
