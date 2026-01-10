#!/bin/bash
# ============================================================
# AZALS - Script de demarrage DEVELOPPEMENT
# ============================================================
#
# Ce script demarre l'application en mode developpement.
#
# SECURITE :
# - AZALS_ENV = dev (force)
# - REFUSE de s'executer sur la branche 'main'
# - Active DB_AUTO_RESET_ON_VIOLATION pour faciliter le dev
#
# USAGE :
#   ./scripts/run_dev.sh
#   ./scripts/run_dev.sh --no-reset  (sans auto-reset UUID)
#
# ============================================================

set -e

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================================
# VERIFICATION DE LA BRANCHE GIT
# ============================================================

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

echo ""
echo "========================================"
echo -e "${CYAN}AZALS DEVELOPPEMENT MODE${NC}"
echo "========================================"
echo -e "Branche Git : ${CYAN}${CURRENT_BRANCH}${NC}"
echo "========================================"

# SECURITE: Refuser l'execution sur la branche 'main'
if [ "$CURRENT_BRANCH" = "main" ]; then
    echo ""
    echo -e "${RED}========================================"
    echo "[FATAL] EXECUTION INTERDITE SUR MAIN"
    echo "========================================${NC}"
    echo ""
    echo -e "${RED}Le mode developpement ne peut PAS s'executer"
    echo -e "sur la branche 'main' (production).${NC}"
    echo ""
    echo "Solutions:"
    echo "  1. Basculez sur la branche develop:"
    echo "     git checkout develop"
    echo ""
    echo "  2. Creez une nouvelle branche de feature:"
    echo "     git checkout -b feature/ma-feature"
    echo ""
    echo "  3. Pour la production, utilisez:"
    echo "     ./scripts/run_prod.sh"
    echo ""
    echo "========================================"
    exit 1
fi

# ============================================================
# CONFIGURATION DEVELOPPEMENT
# ============================================================

# Forcer l'environnement dev
export AZALS_ENV=dev
export DB_STRICT_UUID=true

# Activer l'auto-reset UUID par defaut (desactivable via --no-reset)
if [ "$1" = "--no-reset" ]; then
    export DB_AUTO_RESET_ON_VIOLATION=false
    echo -e "DB_AUTO_RESET_ON_VIOLATION : ${YELLOW}false${NC} (--no-reset)"
else
    export DB_AUTO_RESET_ON_VIOLATION=true
    echo -e "DB_AUTO_RESET_ON_VIOLATION : ${GREEN}true${NC}"
fi

echo -e "AZALS_ENV                  : ${GREEN}$AZALS_ENV${NC}"
echo -e "DB_STRICT_UUID             : $DB_STRICT_UUID"
echo ""

# ============================================================
# VERIFICATION DE LA VERSION
# ============================================================

# Verifier que la version est bien "-dev"
VERSION_FILE="app/core/version.py"
if [ -f "$VERSION_FILE" ]; then
    VERSION=$(grep -oP 'AZALS_VERSION\s*=\s*"\K[^"]+' "$VERSION_FILE" 2>/dev/null || echo "unknown")
    if [[ "$VERSION" == *"-prod"* ]]; then
        echo -e "${YELLOW}[WARN] Version '${VERSION}' detectee sur branche dev${NC}"
        echo -e "${YELLOW}[WARN] Mode pre-production/release${NC}"
    else
        echo -e "VERSION                    : ${GREEN}${VERSION}${NC}"
    fi
fi

echo ""
echo "========================================"
echo -e "${GREEN}UUID STRICT MODE : ENABLED${NC}"
echo "========================================"
echo ""

# ============================================================
# DEMARRAGE
# ============================================================

echo "[START] Demarrage Uvicorn (developpement)..."
echo ""

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
