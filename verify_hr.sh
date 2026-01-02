#!/bin/bash

echo "════════════════════════════════════════════════════════"
echo "🔍 VÉRIFICATION RH - PROMPT 17"
echo "════════════════════════════════════════════════════════"

ERRORS=0

# 1. Backend API
echo ""
echo "1️⃣ Backend API RH"

if [ -f "app/api/hr.py" ]; then
    echo "   ✅ app/api/hr.py existe"
else
    echo "   ❌ app/api/hr.py MANQUANT"
    ((ERRORS++))
fi

if grep -q "from app.api.hr import router as hr_router" app/main.py; then
    echo "   ✅ Import hr_router dans main.py"
else
    echo "   ❌ Import hr_router MANQUANT"
    ((ERRORS++))
fi

if grep -q "app.include_router(hr_router)" app/main.py; then
    echo "   ✅ hr_router enregistré"
else
    echo "   ❌ hr_router NON enregistré"
    ((ERRORS++))
fi

# 2. Template HTML
echo ""
echo "2️⃣ Template HTML hrCardTemplate"

if grep -q 'id="hrCardTemplate"' ui/dashboard.html; then
    echo "   ✅ hrCardTemplate existe"
else
    echo "   ❌ hrCardTemplate MANQUANT"
    ((ERRORS++))
fi

HR_TEMPLATE_SELECTORS=(
    ".status-indicator"
    ".metric-value"
    ".metric-label"
    ".hr-payroll-status"
    ".hr-absences-count"
    ".card-error"
)

for sel in "${HR_TEMPLATE_SELECTORS[@]}"; do
    if grep -A30 'id="hrCardTemplate"' ui/dashboard.html | grep -q "class=\"${sel#.}\""; then
        echo "   ✅ $sel dans template"
    else
        echo "   ⚠️  $sel MANQUE dans template"
        ((ERRORS++))
    fi
done

# 3. Fonction createHRCard
echo ""
echo "3️⃣ createHRCard vs hrCardTemplate"

if grep -q "function createHRCard(data, status)" ui/app.js; then
    echo "   ✅ createHRCard(data, status) avec paramètres"
else
    echo "   ❌ createHRCard sans data/status"
    ((ERRORS++))
fi

for sel in "${HR_TEMPLATE_SELECTORS[@]}"; do
    if grep -A60 "function createHRCard" ui/app.js | grep -q "querySelector('$sel')"; then
        echo "   ✅ $sel utilisé dans createHRCard"
    else
        echo "   ⚠️  $sel NON utilisé (peut être optionnel)"
    fi
done

# 4. Fonction loadHRData
echo ""
echo "4️⃣ Fonction loadHRData"

if grep -q "async function loadHRData()" ui/app.js; then
    echo "   ✅ loadHRData() définie"
else
    echo "   ❌ loadHRData() MANQUANTE"
    ((ERRORS++))
fi

if grep -A20 "async function loadHRData()" ui/app.js | grep -q "authenticatedFetch.*hr/status"; then
    echo "   ✅ Appel API /hr/status"
else
    echo "   ❌ Appel API /hr/status MANQUANT"
    ((ERRORS++))
fi

# 5. buildHRModule
echo ""
echo "5️⃣ Fonction buildHRModule"

if grep -q "function buildHRModule(data)" ui/app.js; then
    echo "   ✅ buildHRModule(data) avec paramètre"
else
    echo "   ❌ buildHRModule sans paramètre data"
    ((ERRORS++))
fi

if grep -A40 "function buildHRModule" ui/app.js | grep -q "createHRCard(data, status)"; then
    echo "   ✅ createHRCard appelée avec data et status"
else
    echo "   ⚠️  createHRCard signature incorrecte"
    ((ERRORS++))
fi

# 6. Intégration dans buildCockpit
echo ""
echo "6️⃣ Intégration dans buildCockpit"

if grep -q "hrData.*=.*await Promise\.all" ui/app.js; then
    echo "   ✅ hrData dans Promise.all"
else
    echo "   ❌ hrData NON chargée"
    ((ERRORS++))
fi

if grep -q "loadHRData()" ui/app.js; then
    echo "   ✅ loadHRData() appelée"
else
    echo "   ❌ loadHRData() NON appelée"
    ((ERRORS++))
fi

if grep -q "buildHRModule(hrData)" ui/app.js; then
    echo "   ✅ buildHRModule(hrData) avec données"
else
    echo "   ❌ buildHRModule sans hrData"
    ((ERRORS++))
fi

# 7. Priorités et domaines
echo ""
echo "7️⃣ Règles de priorité"

if grep -A5 "buildHRModule(hrData)" ui/app.js | grep -q "domainPriority: 3"; then
    echo "   ✅ Domaine Social : priorité 3 (correct)"
else
    echo "   ⚠️  Priorité domaine Social incorrecte"
    ((ERRORS++))
fi

if grep -A40 "function buildHRModule" ui/app.js | grep -q "priority = 0.*Critique"; then
    echo "   ✅ 🔴 RH = priorité 0 (critique)"
else
    echo "   ⚠️  Priorité 🔴 RH incorrecte"
    ((ERRORS++))
fi

# 8. Gestion d'erreurs
echo ""
echo "8️⃣ Gestion d'erreurs"

ERROR_TYPES=("access_denied" "api_unavailable" "api_error")
for err in "${ERROR_TYPES[@]}"; do
    if grep -A50 "async function loadHRData" ui/app.js | grep -q "$err"; then
        echo "   ✅ Erreur $err gérée"
    else
        echo "   ⚠️  Erreur $err NON gérée"
    fi
done

# 9. Confidentialité
echo ""
echo "9️⃣ Confidentialité des données"

if grep -A10 'id="hrCardTemplate"' ui/dashboard.html | grep -q "Aucune info nominative"; then
    echo "   ✅ Mention confidentialité dans bulle d'aide"
else
    echo "   ⚠️  Mention confidentialité absente"
fi

if grep -q "Données anonymisées" ui/dashboard.html; then
    echo "   ✅ Mention anonymisation présente"
else
    echo "   ⚠️  Mention anonymisation absente"
fi

echo ""
echo "════════════════════════════════════════════════════════"

if [ $ERRORS -eq 0 ]; then
    echo "✅ MODULE RH INTÉGRÉ - TOUTES VÉRIFICATIONS OK"
    exit 0
else
    echo "❌ $ERRORS ERREUR(S) CRITIQUE(S)"
    exit 1
fi
