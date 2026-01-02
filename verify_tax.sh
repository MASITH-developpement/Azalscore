#!/bin/bash

echo "════════════════════════════════════════════════════════"
echo "🔍 VÉRIFICATION FISCALITÉ - PROMPT 16"
echo "════════════════════════════════════════════════════════"

ERRORS=0

# 1. Backend API
echo ""
echo "1️⃣ Backend API Fiscalité"

if [ -f "app/api/tax.py" ]; then
    echo "   ✅ app/api/tax.py existe"
else
    echo "   ❌ app/api/tax.py MANQUANT"
    ((ERRORS++))
fi

if grep -q "from app.api.tax import router as tax_router" app/main.py; then
    echo "   ✅ Import tax_router dans main.py"
else
    echo "   ❌ Import tax_router MANQUANT"
    ((ERRORS++))
fi

if grep -q "app.include_router(tax_router)" app/main.py; then
    echo "   ✅ tax_router enregistré"
else
    echo "   ❌ tax_router NON enregistré"
    ((ERRORS++))
fi

# 2. Template HTML
echo ""
echo "2️⃣ Template HTML taxCardTemplate"

if grep -q 'id="taxCardTemplate"' ui/dashboard.html; then
    echo "   ✅ taxCardTemplate existe"
else
    echo "   ❌ taxCardTemplate MANQUANT"
    ((ERRORS++))
fi

TAX_TEMPLATE_SELECTORS=(
    ".status-indicator"
    ".metric-value"
    ".metric-label"
    ".tax-vat-status"
    ".tax-corporate-status"
    ".card-error"
)

for sel in "${TAX_TEMPLATE_SELECTORS[@]}"; do
    if grep -A30 'id="taxCardTemplate"' ui/dashboard.html | grep -q "class=\"${sel#.}\""; then
        echo "   ✅ $sel dans template"
    else
        echo "   ⚠️  $sel MANQUE dans template"
        ((ERRORS++))
    fi
done

# 3. Fonction createTaxCard
echo ""
echo "3️⃣ createTaxCard vs taxCardTemplate"

for sel in "${TAX_TEMPLATE_SELECTORS[@]}"; do
    if grep -A50 "function createTaxCard" ui/app.js | grep -q "querySelector('$sel')"; then
        echo "   ✅ $sel utilisé dans createTaxCard"
    else
        echo "   ⚠️  $sel NON utilisé (peut être optionnel)"
    fi
done

# 4. Fonction loadTaxData
echo ""
echo "4️⃣ Fonction loadTaxData"

if grep -q "async function loadTaxData()" ui/app.js; then
    echo "   ✅ loadTaxData() définie"
else
    echo "   ❌ loadTaxData() MANQUANTE"
    ((ERRORS++))
fi

if grep -A20 "async function loadTaxData()" ui/app.js | grep -q "authenticatedFetch.*tax/status"; then
    echo "   ✅ Appel API /tax/status"
else
    echo "   ❌ Appel API /tax/status MANQUANT"
    ((ERRORS++))
fi

# 5. buildTaxModule
echo ""
echo "5️⃣ Fonction buildTaxModule"

if grep -q "function buildTaxModule(data)" ui/app.js; then
    echo "   ✅ buildTaxModule(data) avec paramètre"
else
    echo "   ❌ buildTaxModule sans paramètre data"
    ((ERRORS++))
fi

if grep -A30 "function buildTaxModule" ui/app.js | grep -q "createTaxCard(data, status)"; then
    echo "   ✅ createTaxCard appelée avec data et status"
else
    echo "   ⚠️  createTaxCard signature incorrecte"
    ((ERRORS++))
fi

# 6. Intégration dans buildCockpit
echo ""
echo "6️⃣ Intégration dans buildCockpit"

if grep -q "const \[journalData, treasuryData, accountingData, taxData\]" ui/app.js; then
    echo "   ✅ taxData dans Promise.all"
else
    echo "   ❌ taxData NON chargée"
    ((ERRORS++))
fi

if grep -q "loadTaxData()" ui/app.js; then
    echo "   ✅ loadTaxData() appelée"
else
    echo "   ❌ loadTaxData() NON appelée"
    ((ERRORS++))
fi

if grep -q "buildTaxModule(taxData)" ui/app.js; then
    echo "   ✅ buildTaxModule(taxData) avec données"
else
    echo "   ❌ buildTaxModule sans taxData"
    ((ERRORS++))
fi

# 7. Priorités et domaines
echo ""
echo "7️⃣ Règles de priorité"

if grep -A40 "function buildTaxModule" ui/app.js | grep -q "domainPriority: 2"; then
    echo "   ✅ Domaine Fiscal : priorité 2 (correct)"
else
    echo "   ⚠️  Priorité domaine Fiscal incorrecte"
fi

if grep -A40 "function buildTaxModule" ui/app.js | grep -q "priority = 0.*Critique"; then
    echo "   ✅ 🔴 Fiscal = priorité 0 (critique)"
else
    echo "   ⚠️  Priorité 🔴 Fiscal incorrecte"
    ((ERRORS++))
fi

# 8. Gestion d'erreurs
echo ""
echo "8️⃣ Gestion d'erreurs"

ERROR_TYPES=("access_denied" "api_unavailable" "api_error")
for err in "${ERROR_TYPES[@]}"; do
    if grep -A50 "async function loadTaxData" ui/app.js | grep -q "$err"; then
        echo "   ✅ Erreur $err gérée"
    else
        echo "   ⚠️  Erreur $err NON gérée"
    fi
done

echo ""
echo "════════════════════════════════════════════════════════"

if [ $ERRORS -eq 0 ]; then
    echo "✅ FISCALITÉ INTÉGRÉE - TOUTES VÉRIFICATIONS OK"
    exit 0
else
    echo "❌ $ERRORS ERREUR(S) CRITIQUE(S)"
    exit 1
fi
