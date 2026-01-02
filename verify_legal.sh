#!/bin/bash

echo "════════════════════════════════════════════════════════"
echo "🔍 VÉRIFICATION JURIDIQUE - PROMPT 18"
echo "════════════════════════════════════════════════════════"

ERRORS=0

# 1. Backend API
echo ""
echo "1️⃣ Backend API Juridique"

if [ -f "app/api/legal.py" ]; then
    echo "   ✅ app/api/legal.py existe"
else
    echo "   ❌ app/api/legal.py MANQUANT"
    ((ERRORS++))
fi

if grep -q "from app.api.legal import router as legal_router" app/main.py; then
    echo "   ✅ Import legal_router dans main.py"
else
    echo "   ❌ Import legal_router MANQUANT"
    ((ERRORS++))
fi

if grep -q "app.include_router(legal_router)" app/main.py; then
    echo "   ✅ legal_router enregistré"
else
    echo "   ❌ legal_router NON enregistré"
    ((ERRORS++))
fi

# 2. Template HTML
echo ""
echo "2️⃣ Template HTML legalCardTemplate"

if grep -q 'id="legalCardTemplate"' ui/dashboard.html; then
    echo "   ✅ legalCardTemplate existe"
else
    echo "   ❌ legalCardTemplate MANQUANT"
    ((ERRORS++))
fi

LEGAL_TEMPLATE_SELECTORS=(
    ".status-indicator"
    ".metric-value"
    ".metric-label"
    ".legal-contracts-count"
    ".legal-risks-count"
    ".card-error"
)

for sel in "${LEGAL_TEMPLATE_SELECTORS[@]}"; do
    if grep -A30 'id="legalCardTemplate"' ui/dashboard.html | grep -q "class=\"${sel#.}\""; then
        echo "   ✅ $sel dans template"
    else
        echo "   ⚠️  $sel MANQUE dans template"
        ((ERRORS++))
    fi
done

# 3. Fonction createLegalCard
echo ""
echo "3️⃣ createLegalCard vs legalCardTemplate"

if grep -q "function createLegalCard(data, status)" ui/app.js; then
    echo "   ✅ createLegalCard(data, status) avec paramètres"
else
    echo "   ❌ createLegalCard sans data/status"
    ((ERRORS++))
fi

# 4. Fonction loadLegalData
echo ""
echo "4️⃣ Fonction loadLegalData"

if grep -q "async function loadLegalData()" ui/app.js; then
    echo "   ✅ loadLegalData() définie"
else
    echo "   ❌ loadLegalData() MANQUANTE"
    ((ERRORS++))
fi

if grep -A20 "async function loadLegalData()" ui/app.js | grep -q "authenticatedFetch.*legal/status"; then
    echo "   ✅ Appel API /legal/status"
else
    echo "   ❌ Appel API /legal/status MANQUANT"
    ((ERRORS++))
fi

# 5. buildLegalModule
echo ""
echo "5️⃣ Fonction buildLegalModule"

if grep -q "function buildLegalModule(data)" ui/app.js; then
    echo "   ✅ buildLegalModule(data) avec paramètre"
else
    echo "   ❌ buildLegalModule sans paramètre data"
    ((ERRORS++))
fi

# 6. Intégration dans buildCockpit
echo ""
echo "6️⃣ Intégration dans buildCockpit"

if grep -q "legalData.*=.*await Promise\.all" ui/app.js; then
    echo "   ✅ legalData dans Promise.all"
else
    echo "   ❌ legalData NON chargée"
    ((ERRORS++))
fi

if grep -q "loadLegalData()" ui/app.js; then
    echo "   ✅ loadLegalData() appelée"
else
    echo "   ❌ loadLegalData() NON appelée"
    ((ERRORS++))
fi

if grep -q "buildLegalModule(legalData)" ui/app.js; then
    echo "   ✅ buildLegalModule(legalData) avec données"
else
    echo "   ❌ buildLegalModule sans legalData"
    ((ERRORS++))
fi

# 7. Priorités et domaines
echo ""
echo "7️⃣ Règles de priorité"

if grep -A5 "buildLegalModule(legalData)" ui/app.js | grep -q "domainPriority: 1"; then
    echo "   ✅ Domaine Juridique : priorité 1 (correct)"
else
    echo "   ⚠️  Priorité domaine Juridique incorrecte"
    ((ERRORS++))
fi

if grep -A40 "function buildLegalModule" ui/app.js | grep -q "priority = 0.*Critique"; then
    echo "   ✅ 🔴 Juridique = priorité 0 (critique)"
else
    echo "   ⚠️  Priorité 🔴 Juridique incorrecte"
    ((ERRORS++))
fi

# 8. Gestion d'erreurs
echo ""
echo "8️⃣ Gestion d'erreurs"

ERROR_TYPES=("access_denied" "api_unavailable" "api_error")
for err in "${ERROR_TYPES[@]}"; do
    if grep -A50 "async function loadLegalData" ui/app.js | grep -q "$err"; then
        echo "   ✅ Erreur $err gérée"
    else
        echo "   ⚠️  Erreur $err NON gérée"
    fi
done

echo ""
echo "════════════════════════════════════════════════════════"

if [ $ERRORS -eq 0 ]; then
    echo "✅ MODULE JURIDIQUE INTÉGRÉ - TOUTES VÉRIFICATIONS OK"
    exit 0
else
    echo "❌ $ERRORS ERREUR(S) CRITIQUE(S)"
    exit 1
fi
