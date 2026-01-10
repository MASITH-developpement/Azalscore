#!/bin/bash
# ============================================================
# AZALS - Script de demarrage PRODUCTION
# ============================================================
#
# Ce script garantit un demarrage SECURISE en production.
#
# INTERDICTIONS ABSOLUES :
# - DEBUG = true
# - DB_AUTO_RESET_ON_VIOLATION = true
# - AZALS_DB_RESET_UUID = true
# - Version "-dev" dans AZALS_VERSION
#
# OBLIGATIONS :
# - AZALS_ENV = prod
# - Version "-prod" obligatoire
# - Tous les secrets configures
#
# USAGE :
#   ./scripts/run_prod.sh
#
# ============================================================

set -e

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "========================================"
echo -e "${RED}AZALS PRODUCTION MODE${NC}"
echo "========================================"

# ============================================================
# VERIFICATION DE LA VERSION
# ============================================================

VERSION_FILE="app/core/version.py"
VERSION="unknown"

if [ -f "$VERSION_FILE" ]; then
    VERSION=$(grep -oP 'AZALS_VERSION\s*=\s*"\K[^"]+' "$VERSION_FILE" 2>/dev/null || echo "unknown")
fi

echo -e "VERSION : ${CYAN}${VERSION}${NC}"

# SECURITE: Refuser les versions "-dev" en production
if [[ "$VERSION" == *"-dev"* ]]; then
    echo ""
    echo -e "${RED}========================================"
    echo "[FATAL] VERSION '-dev' INTERDITE EN PRODUCTION"
    echo "========================================${NC}"
    echo ""
    echo -e "Version detectee : ${RED}${VERSION}${NC}"
    echo ""
    echo "La production requiert une version '-prod'."
    echo ""
    echo "Solutions:"
    echo "  1. Modifiez app/core/version.py"
    echo "  2. Changez AZALS_VERSION en 'X.Y.Z-prod'"
    echo "  3. Relancez ./scripts/run_prod.sh"
    echo ""
    echo "========================================"
    exit 1
fi

# ============================================================
# DETECTION ET BLOCAGE DES VARIABLES DANGEREUSES
# ============================================================

FATAL_ERROR=0

# Verifier DEBUG
if [ "$DEBUG" = "true" ] || [ "$DEBUG" = "1" ] || [ "$DEBUG" = "yes" ]; then
    echo ""
    echo -e "${RED}[FATAL] DEBUG=${DEBUG} INTERDIT en production${NC}"
    FATAL_ERROR=1
fi

# Verifier DB_AUTO_RESET_ON_VIOLATION
if [ "$DB_AUTO_RESET_ON_VIOLATION" = "true" ] || [ "$DB_AUTO_RESET_ON_VIOLATION" = "1" ]; then
    echo ""
    echo -e "${RED}[FATAL] DB_AUTO_RESET_ON_VIOLATION=${DB_AUTO_RESET_ON_VIOLATION} INTERDIT en production${NC}"
    FATAL_ERROR=1
fi

# Verifier AZALS_DB_RESET_UUID
if [ "$AZALS_DB_RESET_UUID" = "true" ] || [ "$AZALS_DB_RESET_UUID" = "1" ]; then
    echo ""
    echo -e "${RED}[FATAL] AZALS_DB_RESET_UUID=${AZALS_DB_RESET_UUID} INTERDIT en production${NC}"
    FATAL_ERROR=1
fi

# Verifier DB_RESET_UUID (variable alternative)
if [ "$DB_RESET_UUID" = "true" ] || [ "$DB_RESET_UUID" = "1" ]; then
    echo ""
    echo -e "${RED}[FATAL] DB_RESET_UUID=${DB_RESET_UUID} INTERDIT en production${NC}"
    FATAL_ERROR=1
fi

# Si erreur fatale detectee, arreter
if [ $FATAL_ERROR -eq 1 ]; then
    echo ""
    echo -e "${RED}========================================"
    echo "[FATAL] CONFIGURATION DANGEREUSE DETECTEE"
    echo "========================================${NC}"
    echo ""
    echo "Supprimez les variables dangereuses et relancez."
    echo ""
    echo "Variables interdites en production:"
    echo "  - DEBUG=true"
    echo "  - DB_AUTO_RESET_ON_VIOLATION=true"
    echo "  - AZALS_DB_RESET_UUID=true"
    echo "  - DB_RESET_UUID=true"
    echo ""
    echo "========================================"
    exit 1
fi

# ============================================================
# FORCER LA CONFIGURATION PRODUCTION
# ============================================================

# SECURITE : Forcer les variables de production
export AZALS_ENV=prod
export DB_AUTO_RESET_ON_VIOLATION=false
export DB_STRICT_UUID=true
export DEBUG=false

# Desactiver explicitement les modes dangereux
unset AZALS_DB_RESET_UUID
unset DB_RESET_UUID

echo ""
echo "========================================"
echo -e "${GREEN}CONFIGURATION SECURISEE${NC}"
echo "========================================"
echo -e "AZALS_ENV                    : ${RED}$AZALS_ENV${NC}"
echo -e "DB_AUTO_RESET_ON_VIOLATION   : ${GREEN}false${NC} (force)"
echo -e "DB_STRICT_UUID               : ${GREEN}true${NC}"
echo -e "DEBUG                        : ${GREEN}false${NC} (force)"
echo ""

# ============================================================
# VERIFICATION DES SECRETS (AVERTISSEMENT)
# ============================================================

WARN_COUNT=0

if [ -z "$SECRET_KEY" ]; then
    echo -e "${YELLOW}[WARN] SECRET_KEY non defini dans l'environnement${NC}"
    WARN_COUNT=$((WARN_COUNT + 1))
fi

if [ -z "$BOOTSTRAP_SECRET" ]; then
    echo -e "${YELLOW}[WARN] BOOTSTRAP_SECRET non defini dans l'environnement${NC}"
    WARN_COUNT=$((WARN_COUNT + 1))
fi

if [ -z "$ENCRYPTION_KEY" ]; then
    echo -e "${YELLOW}[WARN] ENCRYPTION_KEY non defini dans l'environnement${NC}"
    WARN_COUNT=$((WARN_COUNT + 1))
fi

if [ -z "$CORS_ORIGINS" ]; then
    echo -e "${YELLOW}[WARN] CORS_ORIGINS non defini dans l'environnement${NC}"
    WARN_COUNT=$((WARN_COUNT + 1))
fi

if [ $WARN_COUNT -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}[WARN] ${WARN_COUNT} secrets potentiellement manquants${NC}"
    echo -e "${YELLOW}[WARN] Verifiez votre fichier .env ou vos variables d'environnement${NC}"
    echo ""
fi

# ============================================================
# AFFICHAGE FINAL
# ============================================================

echo "========================================"
echo -e "${RED}UUID RESET : BLOQUE${NC}"
echo -e "${RED}DEBUG      : BLOQUE${NC}"
echo -e "${RED}AUTO-RESET : BLOQUE${NC}"
echo "========================================"
echo ""

# ============================================================
# DEMARRAGE
# ============================================================

echo "[START] Demarrage Uvicorn (production)..."
echo ""

# Mode production: pas de reload, 4 workers
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
