# CHARTE DONNÉES AZALSCORE
## Propriété, Cycle de Vie et Protection des Données

**Version:** 1.0.0
**Statut:** DOCUMENT NORMATIF
**Date:** 2026-01-05
**Classification:** CONFIDENTIEL - OPPOSABLE
**Référence:** AZALS-GOV-10-v1.0.0

---

## 1. OBJECTIF

Cette charte définit les règles de propriété, de gestion du cycle de vie, et de protection des données dans AZALSCORE.

---

## 2. PÉRIMÈTRE

- Données métier (factures, clients, produits...)
- Données utilisateur (comptes, préférences)
- Données système (logs, configurations)
- Données IA (modèles, prédictions)

---

## 3. PROPRIÉTÉ DES DONNÉES

### 3.1 Principe Fondamental

```
RÈGLE ABSOLUE: Le client est propriétaire de ses données métier.

- Les données métier appartiennent au client (tenant)
- AZALSCORE est dépositaire, pas propriétaire
- Le client peut exporter ses données à tout moment
- Le client peut demander la suppression de ses données
```

### 3.2 Classification

| Type | Propriétaire | Exemple |
|------|--------------|---------|
| Données Métier | Client (Tenant) | Factures, clients, produits |
| Données Utilisateur | Client (Tenant) | Comptes, préférences |
| Données Système | AZALSCORE | Logs, métriques |
| Données IA | AZALSCORE | Modèles ML |
| Données Audit | Partagé | Journaux d'audit |

---

## 4. CYCLE DE VIE

### 4.1 Phases

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ CRÉATION│───▶│  USAGE  │───▶│ARCHIVAGE│───▶│ PURGE   │───▶│SUPPRIMÉ │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

### 4.2 Durées de Rétention

| Type de Donnée | Usage Actif | Archivage | Purge |
|----------------|-------------|-----------|-------|
| Factures | 2 ans | 10 ans | Après archivage légal |
| Clients | Durée relation | 3 ans post-relation | Après archivage |
| Logs système | 90 jours | 1 an | Après archivage |
| Logs sécurité | 1 an | 5 ans | Jamais (audit) |
| Données IA | Variable | - | Selon modèle |

### 4.3 Règles de Rétention

```python
RETENTION_RULES = {
    "invoice": {
        "active": "2 years",
        "archive": "10 years",
        "legal_requirement": "Code de commerce"
    },
    "customer": {
        "active": "relationship_duration",
        "archive": "3 years post_relationship",
        "legal_requirement": "RGPD"
    },
    "audit_log": {
        "active": "forever",
        "archive": "never",
        "legal_requirement": "Compliance"
    }
}
```

---

## 5. DONNÉES SYSTÈME vs MÉTIER

### 5.1 Données Système

```
Définition: Données nécessaires au fonctionnement du système.

Exemples:
- Configuration système
- Métriques de performance
- Logs techniques
- États des jobs
- Cache

Caractéristiques:
- Propriété AZALSCORE
- Non exportables par le client
- Rétention courte
- Pas de données personnelles
```

### 5.2 Données Métier

```
Définition: Données créées par l'activité du client.

Exemples:
- Factures, devis, commandes
- Clients, fournisseurs
- Produits, stocks
- Écritures comptables
- Documents

Caractéristiques:
- Propriété client
- Exportables à tout moment
- Rétention selon obligations légales
- Peuvent contenir données personnelles
```

---

## 6. DONNÉES SENSIBLES

### 6.1 Classification

| Niveau | Description | Exemples | Traitement |
|--------|-------------|----------|------------|
| CRITIQUE | Données hautement sensibles | Mots de passe, secrets | Chiffrement + accès restreint |
| HAUTE | Données personnelles sensibles | RIB, santé | Chiffrement + audit |
| MOYENNE | Données personnelles | Email, téléphone | Pseudonymisation possible |
| BASSE | Données métier standard | Factures, produits | Protection standard |

### 6.2 Traitement par Niveau

```python
DATA_HANDLING = {
    "CRITIQUE": {
        "encryption": "AES-256",
        "access": "minimal",
        "logging": "all_access",
        "retention": "minimal"
    },
    "HAUTE": {
        "encryption": "AES-256",
        "access": "role_based",
        "logging": "all_access",
        "retention": "legal_minimum"
    },
    "MOYENNE": {
        "encryption": "at_rest",
        "access": "tenant_scoped",
        "logging": "modifications",
        "retention": "business_need"
    },
    "BASSE": {
        "encryption": "at_rest",
        "access": "tenant_scoped",
        "logging": "standard",
        "retention": "business_need"
    }
}
```

---

## 7. ARCHIVAGE

### 7.1 Critères d'Archivage

```
Une donnée est archivée quand:
- Elle n'est plus en usage actif
- La période d'usage actif est terminée
- Elle doit être conservée pour raison légale
- Le client demande l'archivage
```

### 7.2 Processus d'Archivage

```
1. IDENTIFICATION
   └── Données éligibles à l'archivage

2. PRÉPARATION
   └── Extraction des données
   └── Vérification intégrité

3. TRANSFERT
   └── Stockage archive (cold storage)
   └── Chiffrement obligatoire

4. VÉRIFICATION
   └── Confirmation transfert
   └── Test de restauration

5. NETTOYAGE
   └── Suppression données actives
   └── Conservation métadonnées

6. DOCUMENTATION
   └── Registre d'archivage
   └── Durée de rétention
```

### 7.3 Accès aux Archives

```
RÈGLE: Les archives sont accessibles sur demande justifiée.

Procédure:
1. Demande formelle avec justification
2. Validation par responsable données
3. Extraction sécurisée
4. Journalisation de l'accès
5. Remise sécurisée
```

---

## 8. PURGE

### 8.1 Critères de Purge

```
Une donnée est purgée quand:
- La durée de rétention est expirée
- Le client demande la suppression (droit à l'oubli)
- La donnée n'a plus de valeur légale ou métier
- Le tenant est supprimé
```

### 8.2 Processus de Purge

```
1. ÉLIGIBILITÉ
   └── Vérification durée de rétention expirée
   └── Vérification absence d'obligation légale

2. VALIDATION
   └── Approbation responsable données
   └── Pour données client: confirmation client

3. EXÉCUTION
   └── Suppression sécurisée
   └── Effacement physique (pas juste logique)

4. VÉRIFICATION
   └── Confirmation suppression
   └── Vérification backups

5. DOCUMENTATION
   └── Certificat de destruction
   └── Registre des purges
```

### 8.3 Données Non Purgeables

```
RÈGLE: Certaines données ne peuvent JAMAIS être purgées.

- Logs d'audit sécurité
- Rapports RED validés
- Preuves d'incidents
- Données sous obligation légale en cours
```

---

## 9. USAGE IA

### 9.1 Données Utilisables par l'IA

| Catégorie | Usage IA | Condition |
|-----------|----------|-----------|
| Données agrégées | OUI | Anonymisées |
| Tendances métier | OUI | Sans identification |
| Données individuelles | LIMITÉ | Avec consentement |
| Données sensibles | NON | Interdit |

### 9.2 Règles IA

```
RÈGLES:

1. L'IA n'accède PAS aux données brutes sensibles
2. L'IA utilise des données anonymisées/agrégées
3. L'IA ne stocke pas de données personnelles
4. Toute utilisation IA est journalisée
5. Le client peut refuser l'usage IA de ses données
```

---

## 10. EXPORT ET PORTABILITÉ

### 10.1 Droit à l'Export

```
RÈGLE: Le client peut exporter ses données à tout moment.

Formats disponibles:
- JSON (standard)
- CSV (tableaux)
- XML (compatible)
- SQL (technique)
```

### 10.2 Processus d'Export

```python
# API d'export
POST /api/tenant/{tenant_id}/export
{
    "format": "json",
    "scope": "all",  # ou liste de modules
    "include_archives": false,
    "anonymize_personal": false
}

# Réponse
{
    "export_id": "uuid",
    "status": "processing",
    "estimated_time": "15 minutes",
    "download_url": null  # Disponible une fois prêt
}
```

### 10.3 Réversibilité

```
RÈGLE: Le client peut récupérer ses données pour changer de système.

Garanties:
- Export complet possible
- Formats standards et ouverts
- Documentation des schémas
- Assistance à la migration
```

---

## 11. PROTECTION

### 11.1 Chiffrement

| État | Méthode | Clé |
|------|---------|-----|
| Au repos (at rest) | AES-256 | KMS |
| En transit | TLS 1.3 | Certificat |
| Archives | AES-256 | Clé archivage |
| Backups | AES-256 | Clé backup |

### 11.2 Accès

```
RÈGLE: Moindre privilège pour l'accès aux données.

- Accès selon rôle
- Filtrage par tenant obligatoire
- Journalisation des accès
- Revue périodique des droits
```

### 11.3 Intégrité

```
RÈGLE: L'intégrité des données est garantie.

Mesures:
- Checksums sur données critiques
- Journalisation des modifications
- Détection d'altération
- Backups réguliers
```

---

## 12. CONSÉQUENCES DU NON-RESPECT

| Violation | Conséquence |
|-----------|-------------|
| Accès non autorisé | Incident sécurité |
| Purge sans validation | Récupération + audit |
| Export non tracé | Investigation |
| Données non chiffrées | Correction immédiate |

---

*Document généré et validé le 2026-01-05*
*Classification: CONFIDENTIEL - OPPOSABLE*
*Référence: AZALS-GOV-10-v1.0.0*

**LES DONNÉES DU CLIENT APPARTIENNENT AU CLIENT.**
