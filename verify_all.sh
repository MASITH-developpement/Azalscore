#!/bin/bash

echo "════════════════════════════════════════════════════════"
echo "🔍 VÉRIFICATION COMPLÈTE - Templates vs Functions"
echo "════════════════════════════════════════════════════════"

ERRORS=0

# 1. Vérifier TOUS les templates utilisés dans app.js
echo ""
echo "1️⃣ Templates HTML référencés dans app.js"

TEMPLATES=(
    "treasuryCardTemplate"
    "accountingCardTemplate"
    "taxCardTemplate"
    "hrCardTemplate"
)

for tpl in "${TEMPLATES[@]}"; do
    if grep -q "id=\"$tpl\"" ui/dashboard.html; then
        echo "   ✅ $tpl existe"
    else
        echo "   ❌ $tpl MANQUANT"
        ((ERRORS++))
    fi
done

# 2. Vérifier createTreasuryCard vs treasuryCardTemplate
echo ""
echo "2️⃣ createTreasuryCard vs treasuryCardTemplate"

TREASURY_SELECTORS=(
    ".status-indicator"
    ".metric-value"
    ".metric-label"
    ".metric-small-value"
    ".card-error"
)

for sel in "${TREASURY_SELECTORS[@]}"; do
    # Vérifier que le sélecteur est utilisé dans createTreasuryCard
    if grep -q "querySelector('$sel')" ui/app.js; then
        # Vérifier qu'il existe dans le template
        if grep -A20 'id="treasuryCardTemplate"' ui/dashboard.html | grep -q "class=\"${sel#.}\""; then
            echo "   ✅ $sel: utilisé ET existe"
        else
            echo "   ⚠️  $sel: utilisé mais MANQUE dans template"
            ((ERRORS++))
        fi
    fi
done

# 3. Vérifier createAccountingCard vs accountingCardTemplate
echo ""
echo "3️⃣ createAccountingCard vs accountingCardTemplate"

ACCOUNTING_SELECTORS=(
    ".status-indicator"
    ".entries-status"
    ".metric-small-value"
)

for sel in "${ACCOUNTING_SELECTORS[@]}"; do
    if grep -q "querySelector('$sel')" ui/app.js; then
        if grep -A20 'id="accountingCardTemplate"' ui/dashboard.html | grep -q "class=\"${sel#.}\""; then
            echo "   ✅ $sel: utilisé ET existe"
        else
            echo "   ⚠️  $sel: utilisé mais MANQUE dans template"
            ((ERRORS++))
        fi
    fi
done

# 4. Vérifier les fonctions load*Data
echo ""
echo "4️⃣ Fonctions de chargement"

LOAD_FUNCTIONS=(
    "loadTreasuryData"
    "loadAccountingData"
    "loadJournalData"
)

for func in "${LOAD_FUNCTIONS[@]}"; do
    if grep -q "async function $func()" ui/app.js; then
        echo "   ✅ $func() définie"
    else
        echo "   ❌ $func() MANQUANTE"
        ((ERRORS++))
    fi
done

# 5. Vérifier les fonctions build*Module
echo ""
echo "5️⃣ Fonctions de construction"

BUILD_FUNCTIONS=(
    "buildTreasuryModule"
    "buildAccountingModule"
    "buildTaxModule"
    "buildHRModule"
)

for func in "${BUILD_FUNCTIONS[@]}"; do
    if grep -q "function $func(" ui/app.js; then
        echo "   ✅ $func() définie"
    else
        echo "   ❌ $func() MANQUANTE"
        ((ERRORS++))
    fi
done

# 6. Vérifier les appels dans buildCockpit
echo ""
echo "6️⃣ Appels dans buildCockpit()"

if grep -q "const treasuryData = await loadTreasuryData()" ui/app.js; then
    echo "   ✅ loadTreasuryData() appelée"
else
    echo "   ❌ loadTreasuryData() NON appelée"
    ((ERRORS++))
fi

if grep -q "const accountingData = await loadAccountingData()" ui/app.js; then
    echo "   ✅ loadAccountingData() appelée"
else
    echo "   ❌ loadAccountingData() NON appelée"
    ((ERRORS++))
fi

if grep -q "buildAccountingModule(accountingData)" ui/app.js; then
    echo "   ✅ buildAccountingModule(accountingData) - paramètre OK"
else
    echo "   ❌ buildAccountingModule paramètre INCORRECT"
    ((ERRORS++))
fi

# 7. Vérifier les endpoints API
echo ""
echo "7️⃣ Endpoints API utilisés"

API_ENDPOINTS=(
    "/treasury/latest"
    "/accounting/status"
)

for endpoint in "${API_ENDPOINTS[@]}"; do
    if grep -q "authenticatedFetch('$endpoint')" ui/app.js; then
        echo "   ✅ $endpoint appelé"
    else
        echo "   ⚠️  $endpoint NON appelé"
    fi
done

echo ""
echo "════════════════════════════════════════════════════════"

if [ $ERRORS -eq 0 ]; then
    echo "✅ TOUTES LES VÉRIFICATIONS PASSÉES"
    exit 0
else
    echo "❌ $ERRORS ERREUR(S) DÉTECTÉE(S)"
    exit 1
fi

