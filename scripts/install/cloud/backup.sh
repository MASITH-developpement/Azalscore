#!/bin/bash
# ============================================================================
# AZALSCORE - Script de sauvegarde PostgreSQL
# ============================================================================
# Ce script crée des sauvegardes automatiques de la base de données

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS=7
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/azals_${DATE}.sql.gz"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Démarrage de la sauvegarde..."

# Créer le répertoire de backup si nécessaire
mkdir -p "${BACKUP_DIR}"

# Créer la sauvegarde
pg_dump \
    -h "${POSTGRES_HOST:-postgres}" \
    -U "${POSTGRES_USER:-azals_user}" \
    -d "${POSTGRES_DB:-azals}" \
    --format=custom \
    --compress=9 \
    --no-owner \
    --no-privileges \
    | gzip > "${BACKUP_FILE}"

# Vérifier la sauvegarde
if [[ -f "${BACKUP_FILE}" ]]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sauvegarde créée: ${BACKUP_FILE} (${SIZE})"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERREUR: Échec de la sauvegarde"
    exit 1
fi

# Supprimer les anciennes sauvegardes
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Nettoyage des sauvegardes > ${RETENTION_DAYS} jours..."
find "${BACKUP_DIR}" -name "azals_*.sql.gz" -mtime +"${RETENTION_DAYS}" -delete

# Lister les sauvegardes restantes
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sauvegardes disponibles:"
ls -lh "${BACKUP_DIR}"/azals_*.sql.gz 2>/dev/null || echo "  (aucune)"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sauvegarde terminée"
