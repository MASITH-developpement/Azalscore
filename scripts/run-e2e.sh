#!/bin/bash
#
# AZALSCORE - Run E2E Tests
#
# Usage:
#   ./scripts/run-e2e.sh              # Run all tests
#   ./scripts/run-e2e.sh smoke        # Run smoke tests only (fast)
#   ./scripts/run-e2e.sh critical     # Run critical tests
#   ./scripts/run-e2e.sh ui           # Run with UI (headed)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

cd "$FRONTEND_DIR"

# Mode
MODE="${1:-all}"

# Configuration
export BASE_URL="${BASE_URL:-https://azalscore.com}"
export TEST_TENANT="${TEST_TENANT:-masith}"
export TEST_USER="${TEST_USER:-contact@masith.fr}"
export TEST_PASSWORD="${TEST_PASSWORD:-Azals2026!}"

echo "============================================"
echo " AZALSCORE E2E Tests"
echo "============================================"
echo " URL: $BASE_URL"
echo " Mode: $MODE"
echo "============================================"
echo ""

case "$MODE" in
  smoke)
    echo "[1/1] Running smoke tests..."
    npx playwright test --project=smoke
    ;;

  critical)
    echo "[1/2] Running setup..."
    npx playwright test --project=setup

    echo "[2/2] Running critical tests..."
    npx playwright test critical.spec.ts --project=chromium
    ;;

  ui)
    echo "Running with UI..."
    npx playwright test --ui
    ;;

  fast)
    echo "[1/1] Running critical tests only (no setup)..."
    npx playwright test critical.spec.ts --project=smoke
    ;;

  all|*)
    echo "[1/3] Running setup..."
    npx playwright test --project=setup

    echo "[2/3] Running critical tests..."
    npx playwright test critical.spec.ts --project=chromium

    echo "[3/3] Running full suite..."
    npx playwright test --project=chromium --ignore-pattern="**/screenshots-docs.spec.ts"
    ;;
esac

echo ""
echo "============================================"
echo " Tests complete!"
echo "============================================"
echo ""
echo "View report: npx playwright show-report"
