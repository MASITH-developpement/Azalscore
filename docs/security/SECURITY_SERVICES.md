# Services de Sécurité AZALSCORE

Documentation technique des services de sécurité implémentés dans le cadre de l'audit de sécurité Phase 2.

## Table des matières

1. [Audit Trail Service](#audit-trail-service)
2. [Encryption Advanced](#encryption-advanced)
3. [MFA Advanced](#mfa-advanced)
4. [Session Management](#session-management)
5. [Disaster Recovery](#disaster-recovery)

---

## Audit Trail Service

**Fichier**: `app/core/audit_trail.py`

### Description

Service de journalisation d'audit avec chaîne de hash pour l'intégrité, intégration SIEM et détection de menaces en temps réel.

### Caractéristiques

- **Chaîne de hash SHA-256**: Chaque événement est lié au précédent par son hash, garantissant l'intégrité
- **Intégration SIEM**: Support Splunk HEC, Elasticsearch, Datadog, QRadar, Syslog RFC 5424
- **Détection de menaces**: Règles de détection pour brute force, escalade de privilèges, impossible travel

### Utilisation

```python
from app.core.audit_trail import get_audit_service

audit_service = get_audit_service()

# Journaliser un événement
event = await audit_service.log_event(
    category="authentication",
    action="login_success",
    description="Connexion utilisateur réussie",
    tenant_id="tenant_001",
    actor={
        "user_id": "user_123",
        "email": "user@example.com",
        "ip_address": "192.168.1.100"
    },
    target={
        "entity_type": "user",
        "entity_id": "user_123"
    }
)

# Rechercher des événements
events = await audit_service.search_events(
    tenant_id="tenant_001",
    categories=["authentication"],
    start_date=datetime(2024, 1, 1),
    limit=100
)

# Vérifier l'intégrité de la chaîne
is_valid, errors = audit_service.verify_chain_integrity(
    tenant_id="tenant_001",
    category=AuditCategory.AUTHENTICATION,
    events=events
)
```

### Catégories d'audit

| Catégorie | Description |
|-----------|-------------|
| `authentication` | Connexions, déconnexions, échecs d'auth |
| `authorization` | Accès autorisés/refusés |
| `data_access` | Lecture de données sensibles |
| `data_modification` | Création, modification, suppression |
| `configuration` | Changements de configuration |
| `security` | Événements de sécurité |
| `compliance` | Événements de conformité |

### Configuration SIEM

```python
# Splunk HEC
exporter = SplunkExporter(
    hec_url="https://splunk.example.com:8088/services/collector",
    hec_token="your-hec-token",
    index="azalscore_audit"
)

# Elasticsearch
exporter = ElasticsearchExporter(
    hosts=["https://es.example.com:9200"],
    index_prefix="azalscore-audit",
    api_key="your-api-key"
)

# Syslog RFC 5424
exporter = SyslogExporter(
    host="syslog.example.com",
    port=514,
    protocol="tcp",
    tls=True
)
```

---

## Encryption Advanced

**Fichier**: `app/core/encryption_advanced.py`

### Description

Service de chiffrement avancé avec gestion des clés (KMS), chiffrement d'enveloppe (Envelope Encryption), support HSM et tokenisation.

### Architecture

```
┌─────────────────────────────────────────────┐
│                Application                   │
├─────────────────────────────────────────────┤
│          Envelope Encryption Service         │
│    ┌───────────┐        ┌───────────────┐   │
│    │    DEK    │◄──────►│      KEK      │   │
│    │(Data Key) │        │(Master Key)   │   │
│    └───────────┘        └───────────────┘   │
├─────────────────────────────────────────────┤
│           Key Management Service             │
│    ┌───────────┐        ┌───────────────┐   │
│    │  Local    │        │   AWS KMS     │   │
│    │  Storage  │        │   (Optional)  │   │
│    └───────────┘        └───────────────┘   │
└─────────────────────────────────────────────┘
```

### Utilisation

```python
from app.core.encryption_advanced import (
    get_kms, get_envelope_encryption, TokenizationService
)

# Génération de clé
kms = get_kms()
key = kms.generate_key(
    key_type="data_encryption",
    algorithm="AES-256-GCM",
    tenant_id="tenant_001",
    expires_days=365
)

# Chiffrement d'enveloppe
envelope = get_envelope_encryption()
encrypted = envelope.encrypt(
    plaintext=b"Données sensibles",
    tenant_id="tenant_001",
    context={"document_type": "invoice"}
)

decrypted = envelope.decrypt(encrypted, tenant_id="tenant_001")

# Tokenisation (PCI-DSS)
tokenizer = TokenizationService()
token = tokenizer.tokenize(
    value="4111111111111111",
    data_type="credit_card",
    tenant_id="tenant_001"
)
original = tokenizer.detokenize(token, "tenant_001")

# Rotation de clé
new_key = kms.rotate_key(key.id, keep_old_for_decryption=True)
```

### Algorithmes supportés

| Algorithme | Usage | Taille clé |
|------------|-------|------------|
| AES-256-GCM | Chiffrement données | 256 bits |
| AES-256-CBC | Chiffrement fichiers | 256 bits |
| RSA-2048 | Chiffrement clés | 2048 bits |
| RSA-4096 | Chiffrement clés (haute sécurité) | 4096 bits |
| ChaCha20-Poly1305 | Alternative AES | 256 bits |

### Types de données tokenisables

- `credit_card`: Numéros de carte bancaire
- `iban`: Numéros IBAN
- `ssn`: Numéros de sécurité sociale
- `phone`: Numéros de téléphone
- `email`: Adresses email
- `generic`: Données génériques

---

## MFA Advanced

**Fichier**: `app/core/mfa_advanced.py`

### Description

Authentification multi-facteurs complète avec TOTP, WebAuthn/FIDO2, SMS/Email OTP, MFA adaptatif basé sur le risque et gestion de confiance des appareils.

### Méthodes supportées

| Méthode | Description | Sécurité |
|---------|-------------|----------|
| TOTP | Time-based OTP (Google Authenticator) | Haute |
| WebAuthn | Clés de sécurité FIDO2 | Très haute |
| SMS OTP | Code par SMS | Moyenne |
| Email OTP | Code par email | Moyenne |
| Backup Codes | Codes de secours | Urgence |

### Utilisation

```python
from app.core.mfa_advanced import MFAService

mfa = MFAService()

# Configuration TOTP
setup = mfa.setup_totp(
    user_id="user_123",
    tenant_id="tenant_001",
    email="user@example.com"
)
# setup contient: secret, qr_code, backup_codes

# Vérification de code
result = mfa.verify_code(
    user_id="user_123",
    tenant_id="tenant_001",
    code="123456",
    method="totp"
)

if result.success:
    print("MFA validé")

# Évaluation du risque (MFA adaptatif)
mfa_required, risk = mfa.is_mfa_required(
    user_id="user_123",
    tenant_id="tenant_001",
    user_roles=["user"],
    context={
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0",
        "device_id": "device_abc",
        "geolocation": {"country": "FR", "city": "Paris"}
    }
)
```

### MFA Adaptatif

Le MFA adaptatif évalue le risque en fonction de plusieurs facteurs:

```
Score de risque = Σ(facteur × poids)

Facteurs:
- Nouvel appareil: +30
- Nouvelle localisation: +25
- Impossible travel: +50
- Heure inhabituelle: +15
- Échecs récents: +10/échec
- VPN/Proxy détecté: +20
```

### Trust Levels

| Niveau | Description | Durée |
|--------|-------------|-------|
| `full` | Appareil pleinement approuvé | 30 jours |
| `limited` | Appareil partiellement approuvé | 7 jours |
| `temporary` | Appareil temporaire | 24 heures |

---

## Session Management

**Fichier**: `app/core/session_management.py`

### Description

Gestion complète des sessions avec Refresh Token Rotation (RTR), détection de hijacking, limite de sessions concurrentes et gestion des clés API.

### Caractéristiques

- **Refresh Token Rotation**: Nouveau token à chaque refresh
- **Détection de hijacking**: Surveillance des anomalies
- **Sessions concurrentes**: Limite configurable par utilisateur
- **API Keys**: Gestion sécurisée des clés API avec scopes

### Utilisation

```python
from app.core.session_management import get_session_service, APIKeyService

# Création de session
session_service = get_session_service()
session, access_token, refresh_token = session_service.create_session(
    user_id="user_123",
    tenant_id="tenant_001",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0",
    roles=["user", "admin"],
    mfa_verified=True
)

# Validation de session
valid_session = session_service.validate_session(session.id)

# Rafraîchissement (avec rotation)
new_access, new_refresh, session, error = session_service.refresh_session(
    refresh_token=refresh_token,
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0"
)

# Révocation
session_service.revoke_session(session.id, reason="user_logout")

# Clés API
api_service = APIKeyService()
key_value, api_key = api_service.create_api_key(
    name="Integration Key",
    tenant_id="tenant_001",
    user_id="user_123",
    scopes=["read:invoices", "write:invoices"],
    expires_in_days=90
)
```

### Configuration des sessions

| Paramètre | Valeur par défaut | Description |
|-----------|-------------------|-------------|
| `access_token_ttl` | 15 minutes | Durée de vie access token |
| `refresh_token_ttl` | 7 jours | Durée de vie refresh token |
| `max_sessions_per_user` | 5 | Sessions concurrentes max |
| `session_idle_timeout` | 30 minutes | Timeout d'inactivité |

### Scopes API

```
read:*         - Lecture toutes ressources
write:*        - Écriture toutes ressources
read:invoices  - Lecture factures
write:invoices - Écriture factures
admin:*        - Administration complète
```

---

## Disaster Recovery

**Fichier**: `app/core/disaster_recovery.py`

### Description

Service de récupération après sinistre avec réplication cross-région, Point-In-Time Recovery (PITR), gestion RPO/RTO et tests DR automatisés.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Primary Region (eu-west-1)                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Database   │  │   Storage   │  │   Recovery Points   │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
└─────────┼────────────────┼─────────────────────┼─────────────┘
          │                │                     │
          ▼                ▼                     ▼
     ┌────────────────────────────────────────────────────────┐
     │              Replication Service (Async/Sync)          │
     └────────────────────────┬───────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  DR Region 1    │ │  DR Region 2    │ │  DR Region 3    │
│  (eu-central-1) │ │  (us-east-1)    │ │  (ap-southeast) │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Utilisation

```python
from app.core.disaster_recovery import get_dr_service

dr_service = get_dr_service()

# Définir les objectifs de récupération
dr_service.set_recovery_objectives(
    tenant_id="tenant_001",
    rpo_minutes=15,      # Perte de données max: 15 min
    rto_minutes=60,      # Temps de récupération: 1h
    tier="gold"
)

# Créer un point de récupération
point = await dr_service.create_recovery_point(
    tenant_id="tenant_001",
    point_type="full",
    data_source="database",
    metadata={"reason": "pre_deployment"}
)

# Restaurer à un point
operation = await dr_service.restore_to_point(
    tenant_id="tenant_001",
    point_id=point.id,
    target_environment="staging"
)

# Failover
failover = await dr_service.perform_failover(
    tenant_id="tenant_001",
    target_region="eu-central-1",
    mode="planned"  # ou "emergency"
)

# Test DR
test_result = await dr_service.run_dr_test(
    tenant_id="tenant_001",
    test_type="full_recovery",
    target_region="eu-central-1"
)
```

### Tiers de service

| Tier | RPO | RTO | Réplication | Coût relatif |
|------|-----|-----|-------------|--------------|
| Bronze | 4h | 24h | Async, 1 région | 1x |
| Silver | 1h | 4h | Async, 2 régions | 2x |
| Gold | 15min | 1h | Sync, 2 régions | 4x |
| Platinum | 1min | 15min | Sync, 3 régions | 8x |

### Types de test DR

| Type | Description | Durée |
|------|-------------|-------|
| `connectivity` | Test de connectivité réseau | ~1 min |
| `failover_simulation` | Simulation de basculement | ~5 min |
| `data_integrity` | Vérification intégrité données | ~10 min |
| `full_recovery` | Test de récupération complète | ~30 min |

---

## Conformité

### NF525

- Chaîne de hash SHA-256 pour intégrité des logs
- Horodatage sécurisé des événements
- Export FEC conforme

### RGPD

- Chiffrement des données personnelles
- Tokenisation pour minimisation
- Journalisation des accès aux données

### ISO 27001

- Gestion des clés de chiffrement
- Contrôle d'accès multi-facteurs
- Plan de continuité d'activité
