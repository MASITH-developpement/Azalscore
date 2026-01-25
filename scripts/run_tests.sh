#!/bin/bash
# Script pour lancer rapidement les tests backend CORE SaaS v2
# Usage: ./scripts/run_tests.sh [module] [options]

set -e

echo "╔═══════════════════════════════════════════════════════╗"
echo "║  🧪 AZALSCORE Tests Runner - Backend v2               ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Options par défaut
VERBOSE="-v"
FAIL_FAST=""
PARALLEL=""

# Parser les arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -q|--quiet)
            VERBOSE=""
            shift
            ;;
        -x|--fail-fast)
            FAIL_FAST="-x"
            shift
            ;;
        -n|--parallel)
            PARALLEL="-n auto"
            shift
            ;;
        -*)
            echo "Option inconnue: $1"
            exit 1
            ;;
        *)
            MODULE=$1
            shift
            ;;
    esac
done

# Si un module spécifique est demandé
if [ -n "$MODULE" ]; then
    echo -e "${BLUE}📦 Module: $MODULE${NC}"
    echo ""

    # Vérifier que le module existe
    if [ ! -d "app/modules/$MODULE/tests" ]; then
        echo -e "${RED}❌ Module $MODULE n'a pas de tests${NC}"
        exit 1
    fi

    # Lancer les tests
    echo "🧪 Lancement des tests..."
    echo ""

    pytest app/modules/$MODULE/tests/ \
        $VERBOSE \
        $FAIL_FAST \
        $PARALLEL

    echo ""
    echo -e "${GREEN}✅ Tests terminés pour $MODULE${NC}"

else
    # Lancer tous les tests des modules migrés
    echo -e "${BLUE}📦 Modules: TOUS (Phase 2.2)${NC}"
    echo ""

    MODULES="iam tenants audit inventory production projects finance commercial hr guardian"

    echo "🧪 Lancement des tests..."
    echo ""

    # Lancer module par module pour un meilleur affichage
    FAILED_MODULES=()
    PASSED_MODULES=()

    for mod in $MODULES; do
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${YELLOW}Testing: $mod${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        if pytest app/modules/$mod/tests/ $VERBOSE $FAIL_FAST $PARALLEL 2>/dev/null; then
            PASSED_MODULES+=($mod)
            echo -e "${GREEN}✅ $mod: PASSED${NC}"
        else
            FAILED_MODULES+=($mod)
            echo -e "${RED}❌ $mod: FAILED${NC}"
        fi
        echo ""
    done

    # Résumé
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 RÉSUMÉ"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${GREEN}✅ Modules passés (${#PASSED_MODULES[@]}):${NC}"
    for mod in "${PASSED_MODULES[@]}"; do
        echo "   • $mod"
    done
    echo ""

    if [ ${#FAILED_MODULES[@]} -gt 0 ]; then
        echo -e "${RED}❌ Modules échoués (${#FAILED_MODULES[@]}):${NC}"
        for mod in "${FAILED_MODULES[@]}"; do
            echo "   • $mod"
        done
        echo ""
        exit 1
    else
        echo -e "${GREEN}🎉 Tous les tests sont passés!${NC}"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Options disponibles:"
echo "   -q, --quiet      : Mode silencieux"
echo "   -x, --fail-fast  : Arrêter au premier échec"
echo "   -n, --parallel   : Lancer en parallèle (pytest-xdist requis)"
echo ""
echo "💡 Exemples:"
echo "   ./scripts/run_tests.sh              # Tous les modules"
echo "   ./scripts/run_tests.sh iam          # Module IAM seulement"
echo "   ./scripts/run_tests.sh iam -x       # IAM avec fail-fast"
echo "   ./scripts/run_tests.sh -n           # Tous en parallèle"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
