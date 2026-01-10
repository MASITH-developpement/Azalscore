#!/bin/bash
# ============================================================
# AZALS - Script de demarrage PRODUCTION
# ============================================================
#
# Ce script garantit que le reset UUID est IMPOSSIBLE
# en production.
#
# SECURITE :
# - AZALS_ENV = prod (obligatoire)
# - DB_AUTO_RESET_ON_VIOLATION = false (force)
# - Tout reset est BLOQUE
#
# USAGE :
#   ./scripts/run_prod.sh
#
# ============================================================

set -e

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo ""
echo "========================================"
echo -e "${RED}AZALS PRODUCTION MODE${NC}"
echo "========================================"

# SECURITE : Forcer les variables de production
export AZALS_ENV=prod
export DB_AUTO_RESET_ON_VIOLATION=false
export DB_STRICT_UUID=true

# Verifier qu'aucune variable dangereuse n'est definie
if [ "$AZALS_DB_RESET_UUID" = "true" ]; then
    echo -e "${RED}[FATAL] AZALS_DB_RESET_UUID=true INTERDIT en production${NC}"
    echo "Supprimez cette variable et relancez."
    exit 1
fi

echo -e "AZALS_ENV                    : ${RED}$AZALS_ENV${NC}"
echo -e "DB_AUTO_RESET_ON_VIOLATION   : $DB_AUTO_RESET_ON_VIOLATION"
echo -e "DB_STRICT_UUID               : $DB_STRICT_UUID"
echo ""
echo "========================================"
echo -e "${RED}UUID RESET : BLOQUE${NC}"
echo "========================================"
echo ""

# Lancer Uvicorn en mode production (sans reload)
echo "[START] Demarrage Uvicorn (production)..."
echo ""

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
