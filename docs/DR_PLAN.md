# AZALSCORE - Plan de Reprise d'Activite (DR Plan)

**Version:** 1.0.0
**Date:** 2026-01-23
**Classification:** CONFIDENTIEL
**Conformite:** AZA-NF-053 (Continuite d'activite)

---

## 1. OBJECTIFS RPO/RTO

### 1.1 Recovery Point Objective (RPO)

| Niveau | RPO | Description |
|--------|-----|-------------|
| **CRITIQUE** | 1 heure | Donnees transactionnelles (factures, paiements) |
| **HAUTE** | 4 heures | Donnees operationnelles (clients, produits) |
| **MOYENNE** | 24 heures | Donnees analytiques, logs, rapports |
| **BASSE** | 7 jours | Configurations, templates |

**RPO Global:** 1 heure (aligne sur le niveau le plus critique)

### 1.2 Recovery Time Objective (RTO)

| Scenario | RTO | Description |
|----------|-----|-------------|
| **Incident mineur** | 15 minutes | Restart service, failover automatique |
| **Incident majeur** | 1 heure | Restore depuis backup recent |
| **Catastrophe** | 4 heures | Restore complet sur infrastructure secondaire |
| **Perte datacenter** | 8 heures | Activation site DR distant |

**RTO Global:** 4 heures (scenario majeur)

---

## 2. STRATEGIE DE BACKUP

### 2.1 Types de Backups

| Type | Frequence | Retention | Chiffrement |
|------|-----------|-----------|-------------|
| **Full** | Quotidien (02:00 UTC) | 30 jours | AES-256 (GPG) |
| **Incremental** | Toutes les heures | 7 jours | AES-256 (GPG) |
| **WAL Archiving** | Continu | 7 jours | AES-256 (GPG) |
| **Schema-only** | Hebdomadaire | 90 jours | AES-256 (GPG) |

### 2.2 Emplacements de Stockage

| Emplacement | Type | Usage |
|-------------|------|-------|
| **Local** | /var/backups/azalscore | Backups rapides, 7 jours |
| **S3 Primary** | s3://azals-backups-eu-west-1 | Stockage principal, 30 jours |
| **S3 DR** | s3://azals-backups-us-east-1 | Copie cross-region, 30 jours |
| **Glacier** | Archive longue duree | Retention 1 an |

### 2.3 Chiffrement des Backups

```bash
# Configuration requise
export BACKUP_ENCRYPTION_KEY=/etc/azals/backup-public.gpg
# OU
export BACKUP_PASSPHRASE="<passphrase-securisee-32-chars>"

# Execution backup chiffre
./scripts/backup/backup_database.sh --full
```

**IMPORTANT:** Les cles de chiffrement doivent etre stockees dans Vault ou AWS Secrets Manager, JAMAIS dans le code.

---

## 3. PROCEDURES DE RESTAURATION

### 3.1 Restauration Standard

```bash
# 1. Lister les backups disponibles
./scripts/backup/restore_database.sh --list

# 2. Test de restauration (dry-run)
./scripts/backup/restore_database.sh --dry-run backup_file.sql.gz.gpg

# 3. Restauration effective
export BACKUP_PASSPHRASE="<passphrase>"
./scripts/backup/restore_database.sh backup_file.sql.gz.gpg
```

### 3.2 Point-in-Time Recovery (PITR)

```bash
# Restaurer a un point precis dans le temps
pg_restore --target-time="2026-01-23 14:30:00" \
    --target-action=promote \
    -d azalscore backup_base.tar

# Appliquer les WAL jusqu'au point desire
pg_wal_replay --end-time="2026-01-23 14:30:00"
```

### 3.3 Restauration Cross-Region (DR)

```bash
# 1. Telecharger le backup depuis S3 DR
aws s3 cp s3://azals-backups-us-east-1/latest.sql.gz.gpg /tmp/

# 2. Dechiffrer et restaurer
export BACKUP_PASSPHRASE="<passphrase>"
./scripts/backup/restore_database.sh /tmp/latest.sql.gz.gpg
```

---

## 4. SCENARIOS DE SINISTRE

### 4.1 Scenario A: Corruption de donnees

**Symptomes:** Donnees incoherentes, erreurs d'integrite

**Actions:**
1. Identifier l'etendue de la corruption
2. Arreter les ecritures (mode maintenance)
3. Restaurer depuis le dernier backup valide
4. Rejouer les transactions WAL jusqu'au point de corruption
5. Valider l'integrite des donnees
6. Reprendre les operations

**RTO estime:** 1 heure

### 4.2 Scenario B: Panne infrastructure

**Symptomes:** Services inaccessibles, erreurs de connexion DB

**Actions:**
1. Diagnostiquer la panne (network, compute, storage)
2. Activer le failover automatique si disponible
3. Sinon, provisionner nouvelle infrastructure
4. Restaurer depuis S3
5. Mettre a jour DNS/load balancer
6. Valider les services

**RTO estime:** 2 heures

### 4.3 Scenario C: Incident de securite (ransomware)

**Symptomes:** Fichiers chiffres, demande de rancon

**Actions:**
1. **ISOLER** immediatement tous les systemes
2. Ne PAS payer la rancon
3. Provisionner infrastructure isolee
4. Restaurer depuis backup S3 cross-region (non affecte)
5. Analyser forensique pour identifier le vecteur
6. Patcher et renforcer avant remise en production
7. Notifier les autorites (CNIL si donnees personnelles)

**RTO estime:** 8 heures

### 4.4 Scenario D: Perte datacenter

**Symptomes:** Indisponibilite complete du site primaire

**Actions:**
1. Activer le plan DR cross-region
2. Provisionner infrastructure sur region secondaire
3. Restaurer depuis S3 cross-region
4. Configurer DNS failover
5. Notifier les utilisateurs
6. Operer en mode degrade si necessaire

**RTO estime:** 4-8 heures

---

## 5. TESTS DE DR

### 5.1 Calendrier des Tests

| Test | Frequence | Dernier | Prochain |
|------|-----------|---------|----------|
| Restore backup | Mensuel | - | - |
| Failover DB | Trimestriel | - | - |
| DR complet | Semestriel | - | - |
| Tabletop exercise | Annuel | - | - |

### 5.2 Checklist Test de Restore

- [ ] Telecharger un backup recent
- [ ] Verifier l'integrite du fichier (checksum)
- [ ] Dechiffrer le backup
- [ ] Restaurer sur environnement de test
- [ ] Valider l'integrite des donnees
- [ ] Tester les fonctionnalites critiques
- [ ] Documenter les resultats
- [ ] Mettre a jour les procedures si necessaire

### 5.3 Metriques de Succes

| Metrique | Cible | Tolerance |
|----------|-------|-----------|
| Temps de restore | < 1h | +15 min |
| Integrite donnees | 100% | 0% perte |
| Services operationnels | 100% | 95% minimum |
| Transactions perdues | 0 (RPO) | < 1h |

---

## 6. CONTACTS D'URGENCE

### 6.1 Equipe Interne

| Role | Contact | Telephone |
|------|---------|-----------|
| **On-call SRE** | Rotation PagerDuty | +33 X XX XX XX XX |
| **DBA** | dba@azals.io | +33 X XX XX XX XX |
| **CTO** | cto@azals.io | +33 X XX XX XX XX |
| **RSSI** | rssi@azals.io | +33 X XX XX XX XX |

### 6.2 Fournisseurs

| Service | Contact | SLA |
|---------|---------|-----|
| **Hebergeur** | support@provider.com | 24/7, 15 min response |
| **AWS** | AWS Support (Business) | 24/7, 1h response |
| **DNS** | Cloudflare | 24/7 |

### 6.3 Escalade

1. **Niveau 1 (0-15 min):** On-call SRE
2. **Niveau 2 (15-30 min):** DBA + Tech Lead
3. **Niveau 3 (30-60 min):** CTO + RSSI
4. **Niveau 4 (> 1h):** Direction Generale

---

## 7. DOCUMENTATION ASSOCIEE

| Document | Emplacement |
|----------|-------------|
| Runbooks operationnels | /docs/runbooks/ |
| Architecture technique | /docs/architecture.md |
| Procedures de securite | /docs/security/ |
| Scripts de backup | /scripts/backup/ |
| Configuration monitoring | /infra/prometheus/ |

---

## 8. HISTORIQUE DES REVISIONS

| Version | Date | Auteur | Changements |
|---------|------|--------|-------------|
| 1.0.0 | 2026-01-23 | Claude Code | Creation initiale |

---

**Document approuve par:**
- [ ] CTO
- [ ] RSSI
- [ ] DPO

**Prochaine revision:** 2026-07-23 (semestrielle)
