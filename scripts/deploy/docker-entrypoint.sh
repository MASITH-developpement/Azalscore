#!/bin/bash
# AZALS - Docker Entrypoint Production
# ====================================
# Script d'entrée pour le conteneur Docker production.
# Exécute l'initialisation puis démarre l'application.

set -e

echo "========================================"
echo "  AZALSCORE - Démarrage Production"
echo "========================================"

# Attendre que la base de données soit prête
echo "[INIT] Attente de la base de données..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if python -c "
from sqlalchemy import create_engine, text
import os
engine = create_engine(os.environ.get('DATABASE_URL'))
with engine.connect() as conn:
    conn.execute(text('SELECT 1'))
" 2>/dev/null; then
        echo "[INIT] Base de données connectée"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "[INIT] Tentative $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "[ERROR] Impossible de se connecter à la base de données"
    exit 1
fi

# Exécuter l'initialisation (migrations + seed)
echo "[INIT] Initialisation de l'application..."
python scripts/deploy/init_production.py || {
    echo "[WARNING] Erreur lors de l'initialisation, mais on continue..."
}

# Démarrer l'application
echo "[INIT] Démarrage de Gunicorn..."
exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-4} \
    --threads ${GUNICORN_THREADS:-2} \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --capture-output
