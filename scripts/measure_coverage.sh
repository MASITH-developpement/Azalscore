#!/bin/bash
# Script pour mesurer le coverage des tests backend CORE SaaS v2
# Usage: ./scripts/measure_coverage.sh [module]

set -e

echo "╔═══════════════════════════════════════════════════════╗"
echo "║  📊 AZALSCORE Coverage Measurement - Backend v2       ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Vérifier si un module spécifique est demandé
if [ -n "$1" ]; then
    MODULE=$1
    echo "📦 Module: $MODULE"
    echo ""

    # Vérifier que le module existe
    if [ ! -d "app/modules/$MODULE/tests" ]; then
        echo -e "${RED}❌ Module $MODULE n'a pas de tests${NC}"
        exit 1
    fi

    # Lancer les tests avec coverage pour ce module
    echo "🧪 Lancement des tests..."
    pytest app/modules/$MODULE/tests/ \
        -v \
        --cov=app/modules/$MODULE \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-report=xml

    echo ""
    echo -e "${GREEN}✅ Coverage généré pour $MODULE${NC}"
    echo "📄 Rapport HTML: htmlcov/index.html"
    echo "📄 Rapport XML: coverage.xml"

else
    # Lancer tous les tests des modules migrés
    echo "📦 Modules: TOUS (Phase 2.2)"
    echo ""

    MODULES="iam,tenants,audit,inventory,production,projects,finance,commercial,hr,guardian"

    echo "🧪 Lancement des tests..."
    pytest app/modules/{$MODULES}/tests/ \
        -v \
        --cov=app/modules \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-report=xml

    echo ""
    echo -e "${GREEN}✅ Coverage généré pour tous les modules${NC}"
    echo "📄 Rapport HTML: htmlcov/index.html"
    echo "📄 Rapport XML: coverage.xml"

    # Vérifier le seuil de coverage
    echo ""
    echo "📊 Vérification seuil de coverage (≥50%)..."

    if pytest app/modules/{$MODULES}/tests/ \
        --cov=app/modules \
        --cov-fail-under=50 \
        --quiet 2>/dev/null; then
        echo -e "${GREEN}✅ Coverage ≥50% - PASS${NC}"
    else
        echo -e "${YELLOW}⚠️  Coverage <50% - À améliorer${NC}"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Pour ouvrir le rapport HTML:"
echo "   xdg-open htmlcov/index.html  # Linux"
echo "   open htmlcov/index.html      # macOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
