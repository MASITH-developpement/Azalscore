#!/bin/bash
#
# Script de vérification de l'intégration Comptabilité au cockpit
#

echo "=========================================="
echo "Vérification: Intégration Comptabilité"
echo "=========================================="

# Couleurs pour l'affichage
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Token et tenant (à remplacer avec vos vraies valeurs)
TOKEN="${AZALS_TOKEN:-}"
TENANT="tenant-demo"
API_URL="${AZALS_API_URL:-https://azalscore.onrender.com}"

# Compteur de tests
TESTS_PASSED=0
TESTS_FAILED=0

# Fonction pour tester un cas
test_case() {
    local name=$1
    local expected=$2
    
    echo -n "🧪 Test: $name ... "
}

# Fonction pour marquer un test comme réussi
pass() {
    echo -e "${GREEN}✅ PASS${NC}"
    ((TESTS_PASSED++))
}

# Fonction pour marquer un test comme échoué
fail() {
    local reason=$1
    echo -e "${RED}❌ FAIL${NC} ($reason)"
    ((TESTS_FAILED++))
}

echo ""
echo "=== 1. Vérification du Backend ==="

# Test 1: L'endpoint /accounting/status existe
test_case "Endpoint /accounting/status accessible"
if [ -z "$TOKEN" ]; then
    echo -e "${YELLOW}⚠️  SKIP (pas de TOKEN)${NC}"
else
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $TOKEN" \
        -H "X-Tenant-ID: $TENANT" \
        "$API_URL/accounting/status")
    
    if [ "$response" = "200" ]; then
        pass
    else
        fail "HTTP $response"
    fi
fi

# Test 2: La structure de réponse est valide
test_case "Réponse API contient tous les champs requis"
if [ -z "$TOKEN" ]; then
    echo -e "${YELLOW}⚠️  SKIP (pas de TOKEN)${NC}"
else
    response=$(curl -s \
        -H "Authorization: Bearer $TOKEN" \
        -H "X-Tenant-ID: $TENANT" \
        "$API_URL/accounting/status")
    
    has_status=$(echo "$response" | grep -q '"status"' && echo 1 || echo 0)
    has_entries=$(echo "$response" | grep -q '"entries_up_to_date"' && echo 1 || echo 0)
    has_pending=$(echo "$response" | grep -q '"pending_entries_count"' && echo 1 || echo 0)
    has_closure=$(echo "$response" | grep -q '"last_closure_date"' && echo 1 || echo 0)
    has_days=$(echo "$response" | grep -q '"days_since_closure"' && echo 1 || echo 0)
    
    if [ "$has_status" = "1" ] && [ "$has_entries" = "1" ] && [ "$has_pending" = "1" ] && [ "$has_closure" = "1" ] && [ "$has_days" = "1" ]; then
        pass
    else
        fail "Champs manquants"
    fi
fi

# Test 3: Le statut est 🟢 ou 🟠 (jamais 🔴)
test_case "Statut Comptabilité ne contient jamais 🔴"
if [ -z "$TOKEN" ]; then
    echo -e "${YELLOW}⚠️  SKIP (pas de TOKEN)${NC}"
else
    response=$(curl -s \
        -H "Authorization: Bearer $TOKEN" \
        -H "X-Tenant-ID: $TENANT" \
        "$API_URL/accounting/status")
    
    status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    
    if [ "$status" = "🟢" ] || [ "$status" = "🟠" ]; then
        pass
    elif [ "$status" = "🔴" ]; then
        fail "Status contient 🔴 (interdit pour Comptabilité)"
    else
        fail "Status inconnu: $status"
    fi
fi

echo ""
echo "=== 2. Vérification du Frontend ==="

# Test 4: Le template accountingCardTemplate existe en HTML
test_case "Template accountingCardTemplate existe dans dashboard.html"
if grep -q 'id="accountingCardTemplate"' /workspaces/Azalscore/ui/dashboard.html; then
    pass
else
    fail "Template non trouvé"
fi

# Test 5: Les sélecteurs CSS requis existent dans le template
test_case "Sélecteurs CSS requis dans accountingCardTemplate"
template_content=$(sed -n '/<template id="accountingCardTemplate">/,/<\/template>/p' /workspaces/Azalscore/ui/dashboard.html)

has_entries_status=$(echo "$template_content" | grep -q 'entries-status' && echo 1 || echo 0)
has_closure_date=$(echo "$template_content" | grep -q 'closure-date' && echo 1 || echo 0)
has_card_error=$(echo "$template_content" | grep -q 'card-error' && echo 1 || echo 0)

if [ "$has_entries_status" = "1" ] && [ "$has_closure_date" = "1" ] && [ "$has_card_error" = "1" ]; then
    pass
else
    fail "Sélecteurs manquants (entries-status=$has_entries_status, closure-date=$has_closure_date, card-error=$has_card_error)"
fi

# Test 6: La fonction loadAccountingData() existe dans app.js
test_case "Fonction loadAccountingData() définie en JS"
if grep -q 'function loadAccountingData()' /workspaces/Azalscore/ui/app.js; then
    pass
else
    fail "Fonction non trouvée"
fi

# Test 7: La fonction createAccountingCard() existe dans app.js
test_case "Fonction createAccountingCard() définie en JS"
if grep -q 'function createAccountingCard(data, status)' /workspaces/Azalscore/ui/app.js; then
    pass
else
    fail "Fonction non trouvée"
fi

# Test 8: La fonction buildAccountingModule() existe dans app.js
test_case "Fonction buildAccountingModule() définie en JS"
if grep -q 'function buildAccountingModule(data)' /workspaces/Azalscore/ui/app.js; then
    pass
else
    fail "Fonction non trouvée"
fi

# Test 9: loadAccountingData() est appelée dans Promise.all
test_case "loadAccountingData() appelée dans Promise.all de initDashboard()"
if grep -q 'const \[journalData, treasuryData, accountingData\]' /workspaces/Azalscore/ui/app.js; then
    pass
else
    fail "Promise.all non trouvé ou incorrect"
fi

# Test 10: buildAccountingModule() est appelée dans createDashboard()
test_case "buildAccountingModule() appelée dans createDashboard()"
if grep -q 'buildAccountingModule(journalData)' /workspaces/Azalscore/ui/app.js; then
    pass
else
    fail "Appel non trouvé"
fi

echo ""
echo "=== 3. Vérification de l'intégration ==="

# Test 11: Les routes sont enregistrées dans main.py
test_case "Route accounting enregistrée dans main.py"
if grep -q 'app.include_router(accounting_router)' /workspaces/Azalscore/app/main.py; then
    pass
else
    fail "Route non enregistrée"
fi

# Test 12: Le modèle JournalEntry est importé dans accounting.py
test_case "Modèle JournalEntry importé dans accounting.py"
if grep -q 'from app.core.models import.*JournalEntry' /workspaces/Azalscore/app/api/accounting.py; then
    pass
else
    fail "Import manquant"
fi

echo ""
echo "=== RÉSULTATS ==="
echo -e "✅ Tests réussis: ${GREEN}$TESTS_PASSED${NC}"
echo -e "❌ Tests échoués:  ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ Tous les tests sont passés!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ $TESTS_FAILED test(s) ont échoué.${NC}"
    exit 1
fi
