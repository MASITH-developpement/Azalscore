#!/bin/bash
#
# AZALSCORE - Generation des Screenshots Documentation
#
# Ce script demarre les serveurs necessaires et genere les captures
# d'ecran pour la documentation de vente.
#
# Usage: ./scripts/generate-screenshots.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SCREENSHOTS_DIR="$PROJECT_ROOT/docs/screenshots"

echo "============================================"
echo " AZALSCORE - Generation Screenshots"
echo "============================================"

# Creer le dossier screenshots
mkdir -p "$SCREENSHOTS_DIR"

# Verifier les pre-requis
echo ""
echo "[1/5] Verification des pre-requis..."

if ! command -v npx &> /dev/null; then
    echo "ERREUR: npx non trouve. Installer Node.js >= 18"
    exit 1
fi

# Aller dans le dossier frontend
cd "$PROJECT_ROOT/frontend"

# Installer les dependances Playwright si necessaire
echo ""
echo "[2/5] Installation Playwright browsers..."
npx playwright install chromium --with-deps 2>/dev/null || true

# Variables d'environnement pour les tests
export TEST_USER_EMAIL="${TEST_USER_EMAIL:-admin@demo.azalscore.com}"
export TEST_USER_PASSWORD="${TEST_USER_PASSWORD:-demo123}"
export BASE_URL="${BASE_URL:-http://localhost:5173}"

# Demarrer le backend si non actif
echo ""
echo "[3/5] Verification backend..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Demarrage du backend..."
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    sleep 5
    cd "$PROJECT_ROOT/frontend"
else
    echo "Backend deja actif"
    BACKEND_PID=""
fi

# Demarrer le frontend si non actif
echo ""
echo "[4/5] Verification frontend..."
if ! curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "Demarrage du frontend..."
    npm run dev &
    FRONTEND_PID=$!
    sleep 10
else
    echo "Frontend deja actif"
    FRONTEND_PID=""
fi

# Executer les tests de screenshots
echo ""
echo "[5/5] Generation des screenshots..."
npx playwright test screenshots-docs.spec.ts --project=chromium --reporter=list

# Arreter les serveurs demarres par ce script
if [ -n "$BACKEND_PID" ]; then
    echo "Arret du backend (PID: $BACKEND_PID)"
    kill $BACKEND_PID 2>/dev/null || true
fi

if [ -n "$FRONTEND_PID" ]; then
    echo "Arret du frontend (PID: $FRONTEND_PID)"
    kill $FRONTEND_PID 2>/dev/null || true
fi

echo ""
echo "============================================"
echo " Screenshots generes dans: $SCREENSHOTS_DIR"
echo "============================================"
echo ""
ls -la "$SCREENSHOTS_DIR"
