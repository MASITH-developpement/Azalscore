#!/bin/sh
# ==============================================================================
# AZALSCORE - Script de Sauvegarde Automatique
# ==============================================================================
# Execute quotidiennement par cron
# Sauvegarde: PostgreSQL + fichiers critiques
# Retention: configurable via BACKUP_RETENTION_DAYS
# ==============================================================================

set -e

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date '+%Y-%m-%d_%H%M%S')
BACKUP_FILE="${BACKUP_DIR}/${TIMESTAMP}.sql.gz"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "=== Debut de la sauvegarde ==="

# Verification de l'espace disque
DISK_FREE=$(df -m "${BACKUP_DIR}" | awk 'NR==2 {print $4}')
if [ "${DISK_FREE}" -lt 500 ]; then
    log "ERREUR: Espace disque insuffisant (${DISK_FREE}MB < 500MB)"
    exit 1
fi

# Sauvegarde PostgreSQL
log "Export de la base de donnees..."
export PGPASSWORD="${POSTGRES_PASSWORD}"
pg_dump -h postgres -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${BACKUP_FILE}"

# Verification de la sauvegarde
if [ ! -s "${BACKUP_FILE}" ]; then
    log "ERREUR: Fichier de sauvegarde vide ou inexistant"
    exit 1
fi

BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
log "Sauvegarde creee: ${BACKUP_FILE} (${BACKUP_SIZE})"

# Verification d'integrite
log "Verification d'integrite..."
if ! gunzip -t "${BACKUP_FILE}" 2>/dev/null; then
    log "ERREUR: Archive corrompue"
    rm -f "${BACKUP_FILE}"
    exit 1
fi

# Calcul du checksum
CHECKSUM=$(sha256sum "${BACKUP_FILE}" | cut -d' ' -f1)
echo "${CHECKSUM}" > "${BACKUP_FILE}.sha256"
log "Checksum SHA256: ${CHECKSUM}"

# Rotation des anciennes sauvegardes
log "Nettoyage des sauvegardes de plus de ${RETENTION_DAYS} jours..."
DELETED=$(find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
find "${BACKUP_DIR}" -name "*.sha256" -mtime +${RETENTION_DAYS} -delete

if [ "${DELETED}" -gt 0 ]; then
    log "Sauvegardes supprimees: ${DELETED}"
fi

# Liste des sauvegardes restantes
BACKUP_COUNT=$(ls -1 "${BACKUP_DIR}"/*.sql.gz 2>/dev/null | wc -l)
log "Sauvegardes disponibles: ${BACKUP_COUNT}"

log "=== Sauvegarde terminee avec succes ==="

# Sortie pour monitoring
echo "backup_success{database=\"${POSTGRES_DB}\"} 1"
echo "backup_size_bytes{database=\"${POSTGRES_DB}\"} $(stat -f%z "${BACKUP_FILE}" 2>/dev/null || stat -c%s "${BACKUP_FILE}")"
echo "backup_count{database=\"${POSTGRES_DB}\"} ${BACKUP_COUNT}"
