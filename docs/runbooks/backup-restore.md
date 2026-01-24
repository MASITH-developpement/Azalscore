# Runbook: Backup et Restore

## Vue d'ensemble

| Type | Fréquence | Rétention | Chiffrement |
|------|-----------|-----------|-------------|
| Full backup | Quotidien (3h) | 30 jours | AES-256 |
| WAL archiving | Continu | 7 jours | AES-256 |
| Config backup | Hebdomadaire | 90 jours | GPG |

**RPO:** 1 heure (Point-in-Time Recovery)
**RTO:** 4 heures (restauration complète)

---

## Procédure de backup manuel

### Backup complet chiffré

```bash
# Variables d'environnement requises
export BACKUP_PASSPHRASE="<VOTRE_PASSPHRASE_32_CHARS>"
export BACKUP_DIR="/var/backups/azalscore"

# Exécuter le backup
/home/ubuntu/azalscore/scripts/backup/backup_database.sh

# Vérifier le backup
ls -la $BACKUP_DIR/
gpg --list-packets $BACKUP_DIR/azalscore_*.sql.gz.gpg | head -5
```

### Backup WAL pour PITR

```bash
# Vérifier l'archivage WAL
ls -la /var/lib/postgresql/*/main/pg_wal/archive_status/

# Forcer un checkpoint et archivage
sudo -u postgres psql -c "CHECKPOINT; SELECT pg_switch_wal();"
```

---

## Procédure de restore

### Restore complet depuis backup chiffré

```bash
# 1. Arrêter l'application
sudo systemctl stop azalscore

# 2. Arrêter PostgreSQL
sudo systemctl stop postgresql

# 3. Déchiffrer le backup
export BACKUP_PASSPHRASE="<VOTRE_PASSPHRASE>"
BACKUP_FILE="/var/backups/azalscore/azalscore_20260123_030000.sql.gz.gpg"

gpg --batch --yes --passphrase "$BACKUP_PASSPHRASE" \
    --decrypt "$BACKUP_FILE" | gunzip > /tmp/restore.sql

# 4. Recréer la base de données
sudo systemctl start postgresql
sudo -u postgres dropdb azalscore --if-exists
sudo -u postgres createdb azalscore

# 5. Restaurer
sudo -u postgres psql azalscore < /tmp/restore.sql

# 6. Vérifier l'intégrité
sudo -u postgres psql -d azalscore -c "
SELECT schemaname, tablename, n_live_tup
FROM pg_stat_user_tables ORDER BY n_live_tup DESC LIMIT 10;"

# 7. Redémarrer l'application
sudo systemctl start azalscore

# 8. Nettoyer
rm /tmp/restore.sql
```

### Point-in-Time Recovery (PITR)

Pour restaurer à un instant précis (ex: avant une erreur):

```bash
# 1. Arrêter PostgreSQL
sudo systemctl stop postgresql

# 2. Sauvegarder les données actuelles
sudo mv /var/lib/postgresql/*/main /var/lib/postgresql/*/main.old

# 3. Restaurer depuis le dernier backup base
sudo -u postgres pg_basebackup -D /var/lib/postgresql/*/main -Fp -P

# 4. Configurer le recovery
cat > /var/lib/postgresql/*/main/postgresql.auto.conf << EOF
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '2026-01-23 14:30:00'
recovery_target_action = 'promote'
EOF

# 5. Créer le signal de recovery
touch /var/lib/postgresql/*/main/recovery.signal

# 6. Démarrer PostgreSQL (recovery automatique)
sudo systemctl start postgresql

# 7. Vérifier les logs
tail -f /var/log/postgresql/postgresql-*-main.log
```

---

## Restore partiel (table unique)

```bash
# 1. Extraire la table du backup
gunzip -c backup.sql.gz | grep -A 1000000 "COPY table_name" | \
    grep -B 1000000 "^\\\." > /tmp/table_data.sql

# 2. Restaurer dans une table temporaire
sudo -u postgres psql -d azalscore -c "
CREATE TABLE table_name_restore (LIKE table_name INCLUDING ALL);"

sudo -u postgres psql -d azalscore < /tmp/table_data.sql

# 3. Vérifier et merger les données
sudo -u postgres psql -d azalscore -c "
SELECT count(*) FROM table_name_restore;"
```

---

## Vérification des backups

### Test de restore hebdomadaire

```bash
#!/bin/bash
# Script de test restore automatique (à planifier via cron)

set -e

# Sélectionner le dernier backup
LATEST_BACKUP=$(ls -t /var/backups/azalscore/*.gpg | head -1)

# Restaurer dans une DB de test
export BACKUP_PASSPHRASE="$BACKUP_PASSPHRASE"
gpg --batch --yes --passphrase "$BACKUP_PASSPHRASE" \
    --decrypt "$LATEST_BACKUP" | gunzip > /tmp/test_restore.sql

sudo -u postgres dropdb azalscore_test --if-exists
sudo -u postgres createdb azalscore_test
sudo -u postgres psql azalscore_test < /tmp/test_restore.sql

# Vérifier l'intégrité
TABLES=$(sudo -u postgres psql -t -d azalscore_test -c "
SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")

if [ "$TABLES" -gt 50 ]; then
    echo "SUCCESS: Backup restore test passed ($TABLES tables)"
    # Envoyer notification success
else
    echo "FAILURE: Only $TABLES tables restored"
    # Envoyer alerte
fi

# Nettoyer
sudo -u postgres dropdb azalscore_test
rm /tmp/test_restore.sql
```

---

## Alerte: BackupFailed

**Sévérité:** SEV2
**Trigger:** Backup quotidien échoué

### Diagnostic

```bash
# Vérifier les logs du backup
tail -100 /var/log/azalscore/backup.log

# Vérifier l'espace disque
df -h /var/backups

# Vérifier les permissions
ls -la /var/backups/azalscore/
```

### Résolution

```bash
# Cas 1: Espace disque insuffisant
find /var/backups/azalscore -name "*.gpg" -mtime +30 -delete

# Cas 2: Erreur PostgreSQL
sudo systemctl status postgresql
sudo -u postgres pg_isready

# Cas 3: Erreur de chiffrement
# Vérifier que BACKUP_PASSPHRASE est définie
env | grep BACKUP

# Relancer le backup manuellement
/home/ubuntu/azalscore/scripts/backup/backup_database.sh
```

---

## Rotation des backups

### Politique de rétention

| Type | Rétention | Emplacement |
|------|-----------|-------------|
| Quotidien | 7 jours | Local |
| Hebdomadaire | 30 jours | Local + S3 |
| Mensuel | 1 an | S3 Glacier |

### Script de rotation

```bash
#!/bin/bash
# /etc/cron.daily/backup-rotation

BACKUP_DIR="/var/backups/azalscore"

# Supprimer les backups de plus de 30 jours
find $BACKUP_DIR -name "*.gpg" -mtime +30 -delete

# Garder un backup par semaine pour le mois précédent
# (logique plus complexe pour production)

# Sync vers S3 (hebdomadaire)
if [ $(date +%u) -eq 7 ]; then
    aws s3 sync $BACKUP_DIR s3://azalscore-backups/weekly/ \
        --exclude "*" --include "*.gpg"
fi

echo "$(date): Backup rotation completed" >> /var/log/azalscore/backup.log
```

---

## Checklist restore d'urgence

- [ ] Identifier le backup à restaurer (date/heure)
- [ ] Vérifier l'intégrité du fichier backup
- [ ] Notifier les utilisateurs (maintenance)
- [ ] Arrêter l'application
- [ ] Sauvegarder l'état actuel (même corrompu)
- [ ] Effectuer la restauration
- [ ] Vérifier l'intégrité des données
- [ ] Tester les fonctionnalités critiques
- [ ] Redémarrer l'application
- [ ] Notifier la fin de maintenance
- [ ] Post-mortem si perte de données
