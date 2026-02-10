# AZALSCORE AI Orchestration System

## Architecture Implémentée

```
Interface graphique azalscore.com
        ⇅
THEO (LLM souverain - Interface humaine)
        ↓
Orchestrateur AZALSCORE (rôles, règles, journal)
        ↓
Modules IA internes:
├── ChatGPT (Architecte cognitif - IA-R7)
├── Claude (Expert technique - IA-R6)
└── Guardian (Sécurité & conformité - IA-R8)
```

## Fichiers Créés

| Fichier | Description |
|---------|-------------|
| `app/ai/__init__.py` | Point d'entrée du module AI |
| `app/ai/roles.py` | Définition des rôles IA (AIRole) |
| `app/ai/audit.py` | Système d'audit et journalisation |
| `app/ai/guardian.py` | Module de sécurité Guardian |
| `app/ai/theo.py` | Interface Theo (LLM souverain) |
| `app/ai/orchestrator.py` | Orchestrateur central |
| `app/ai/auth.py` | Authentification MFA |
| `app/ai/config.py` | Configuration centrale |
| `app/ai/api.py` | Routes API REST |
| `tests/test_ai_orchestration.py` | Tests unitaires (22 tests) |

## Composants

### THEO (Interface Humaine)

- **Seule interface exposée aux utilisateurs**
- Analyse les intentions utilisateur
- Demande des clarifications si nécessaire
- Orchestre les appels aux modules internes
- Synthétise les réponses

```python
from app.ai.theo import get_theo

theo = get_theo()
session_id = theo.start_session(user_id="user-123")
response = theo.process_input(session_id, "Créer une facture")
```

### GUARDIAN (Sécurité)

- **Actif en permanence sur tous les flux**
- Valide toutes les requêtes avant exécution
- Bloque les contenus dangereux
- Gère le rate limiting
- Alerte le cockpit humain

```python
from app.ai.guardian import get_guardian

guardian = get_guardian()
result = guardian.validate_request(
    session_id="...",
    user_id="...",
    action="execute",
    target_module="finance",
    role=AIRole.CLAUDE_REASONING,
    input_data={...}
)
```

### Orchestrateur

- **Coordonne tous les modules IA**
- Applique la règle: 1 appel = 1 rôle
- Gère les validations croisées
- Escalade vers l'humain si divergence

```python
from app.ai.orchestrator import get_ai_orchestrator, AICallRequest, AIModule, AIRole

orchestrator = get_ai_orchestrator()
result = orchestrator.call(AICallRequest(
    session_id="...",
    module=AIModule.CLAUDE,
    role=AIRole.CLAUDE_REASONING,
    input_data={"question": "..."}
))
```

### Authentification

- **MFA obligatoire pour admin/owner**
- Sessions à durée limitée
- Rate limiting sur les tentatives

```python
from app.ai.auth import get_auth_manager

auth = get_auth_manager()
session = auth.authenticate_password("owner", "password")
if session and session.metadata.get("mfa_pending"):
    session = auth.verify_mfa_code(session.session_id, "123456")
```

## API Endpoints

### Theo (Public)

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/ai/theo/start` | POST | Démarrer une session |
| `/api/v1/ai/theo/chat` | POST | Envoyer un message |
| `/api/v1/ai/theo/confirm` | POST | Confirmer une intention |
| `/api/v1/ai/theo/history/{session_id}` | GET | Historique |
| `/api/v1/ai/theo/end/{session_id}` | POST | Terminer la session |

### Auth

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/ai/auth/login` | POST | Connexion (facteur 1) |
| `/api/v1/ai/auth/mfa` | POST | Vérification MFA |
| `/api/v1/ai/auth/logout` | POST | Déconnexion |

### Admin (Protégé)

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/ai/admin/alerts` | GET | Alertes Guardian |
| `/api/v1/ai/admin/alerts/{id}/acknowledge` | POST | Acquitter alerte |
| `/api/v1/ai/admin/audit/report` | GET | Rapport d'audit |
| `/api/v1/ai/admin/sessions` | GET | Sessions actives |

### Status

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/ai/status` | GET | Statut du système |

## Rôles IA Définis

### Theo (IA-R5)
- `THEO_DIALOGUE` - Dialogue avec l'humain
- `THEO_CLARIFICATION` - Questions de clarification
- `THEO_ORCHESTRATION` - Orchestration des appels
- `THEO_SYNTHESIS` - Synthèse des réponses

### ChatGPT (IA-R7)
- `GPT_STRUCTURE` - Structuration d'intention
- `GPT_DECOMPOSE` - Découpage cognitif
- `GPT_REFORMULATE` - Reformulation neutre

### Claude (IA-R6)
- `CLAUDE_REASONING` - Raisonnement technique
- `CLAUDE_DEBUG` - Débogage
- `CLAUDE_CODE_ANALYSIS` - Analyse de code
- `CLAUDE_PEDAGOGY` - Explications pédagogiques

### Guardian (IA-R8)
- `GUARDIAN_VALIDATE` - Validation de conformité
- `GUARDIAN_AUDIT` - Audit des flux
- `GUARDIAN_BLOCK` - Blocage des dérives
- `GUARDIAN_ALERT` - Alertes cockpit

## Configuration

Variables d'environnement:

```bash
# Clés API
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Configuration owner
AZALSCORE_OWNER_PASSWORD_HASH=sha256_hash_here

# Limites
AZALSCORE_AI_CALLS_PER_MINUTE=60
AZALSCORE_AI_CALLS_PER_HOUR=500

# Sessions
AZALSCORE_SESSION_HOURS=2
AZALSCORE_MFA_VALIDITY_MINUTES=10
```

## Principes Respectés

1. **Theo est l'unique interface** - Aucune autre IA n'a d'interface humaine
2. **1 appel = 1 rôle** - Aucun module appelé sans rôle explicite
3. **Guardian transversal** - Actif sur tous les flux
4. **Auditabilité totale** - Tout est tracé
5. **Décision humaine finale** - Escalade en cas de divergence
6. **MFA pour privilèges élevés** - Admin/Owner requiert 2 facteurs

## Conformité AZALSCORE

| Norme | Description | Implémenté |
|-------|-------------|------------|
| AZA-IA-001 | IA gouvernée | ✅ |
| AZA-IA-005 | Fallback IA | ✅ |
| AZA-SEC-002 | Authentification | ✅ |
| AZA-SEC-003 | Autorisation | ✅ |
| AZA-NF-009 | Auditabilité | ✅ |
| AZA-API-003 | API versionnée | ✅ |

## Tests

```bash
# Exécuter les tests
source venv/bin/activate
python -m pytest tests/test_ai_orchestration.py -v

# Résultat: 22 passed
```
