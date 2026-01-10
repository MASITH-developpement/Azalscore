#!/bin/bash
# ============================================================
# AZALS - Script de demarrage DEV avec UUID AUTO-RESET
# ============================================================
#
# Ce script garantit que les variables d'environnement sont
# correctement definies AVANT le lancement d'Uvicorn.
#
# COMPORTEMENT :
# - Active le mode dev
# - Active le reset automatique UUID (une seule fois)
# - Demarre Uvicorn sur le port 8000
#
# SECURITE :
# - Ne peut PAS etre utilise en production
# - Le reset ne s'execute qu'UNE fois (sentinel file)
#
# USAGE :
#   ./scripts/run_dev.sh
#
# ============================================================

set -e

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "========================================"
echo -e "${GREEN}AZALS DEV MODE${NC}"
echo "========================================"

# Variables d'environnement UUID
export AZALS_ENV=dev
export DB_AUTO_RESET_ON_VIOLATION=true
export DB_STRICT_UUID=true

echo -e "AZALS_ENV                    : ${GREEN}$AZALS_ENV${NC}"
echo -e "DB_AUTO_RESET_ON_VIOLATION   : ${GREEN}$DB_AUTO_RESET_ON_VIOLATION${NC}"
echo -e "DB_STRICT_UUID               : ${GREEN}$DB_STRICT_UUID${NC}"
echo ""

# Verifier le fichier sentinel
SENTINEL_FILE=".uuid_reset_done"
if [ -f "$SENTINEL_FILE" ]; then
    echo -e "${YELLOW}[INFO] Reset UUID deja effectue (sentinel: $SENTINEL_FILE)${NC}"
    echo -e "${YELLOW}[INFO] Le reset ne sera pas relance${NC}"
    echo ""
    echo "Pour forcer un nouveau reset, supprimez le fichier sentinel :"
    echo "  rm $SENTINEL_FILE"
    echo ""
else
    echo -e "${GREEN}[INFO] Premier demarrage - reset UUID actif si violations detectees${NC}"
    echo ""
fi

echo "========================================"
echo -e "${GREEN}UUID AUTO RESET : ENABLED${NC}"
echo "========================================"
echo ""

# Lancer Uvicorn
echo "[START] Demarrage Uvicorn..."
echo ""

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
