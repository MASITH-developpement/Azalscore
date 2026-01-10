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

# ============================================================
# AZALS - Script de demarrage PRODUCTION
# UUID STRICT - AUCUN RESET POSSIBLE
# ============================================================

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo ""
echo "========================================"
echo -e "${RED}AZALS PRODUCTION MODE${NC}"
echo "========================================"

# -------- SECURITE ABSOLUE --------

# Base obligatoire
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}[FATAL] DATABASE_URL non definie${NC}"
    echo "Impossible de demarrer AZALS en production sans base."
    exit 1
fi

# Interdictions formelles
if [ "$AZALS_DB_RESET_UUID" = "true" ]; then
    echo -e "${RED}[FATAL] AZALS_DB_RESET_UUID=true INTERDIT en production${NC}"
    exit 1
fi

if [ "$DB_STRICT_UUID" = "false" ]; then
    echo -e "${RED}[FATAL] DB_STRICT_UUID=false INTERDIT en production${NC}"
    exit 1
fi

# -------- VARIABLES FORCEES --------
export AZALS_ENV=prod
export DEBUG=false
export DB_AUTO_RESET_ON_VIOLATION=false
export DB_STRICT_UUID=true

# -------- LOGS --------
echo -e "AZALS_ENV                    : ${RED}$AZALS_ENV${NC}"
echo -e "DB_AUTO_RESET_ON_VIOLATION   : $DB_AUTO_RESET_ON_VIOLATION"
echo -e "DB_STRICT_UUID               : $DB_STRICT_UUID"
echo ""
echo "========================================"
echo -e "${RED}UUID RESET : BLOQUE DEFINITIVEMENT${NC}"
echo "========================================"
echo ""

# -------- DEMARRAGE --------
if [ "$DEBUG" = "true" ]; then
    echo -e "${RED}[FATAL] DEBUG=true INTERDIT en production${NC}"
    exit 1
fi

echo "[START] Demarrage Uvicorn (production)..."
echo ""

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
