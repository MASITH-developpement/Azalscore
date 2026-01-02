#!/bin/bash

echo "════════════════════════════════════════════════════════"
echo "🧪 VÉRIFICATION MODE TEST AZALS"
echo "════════════════════════════════════════════════════════"

ERRORS=0

# 1. Flag et constantes
echo ""
echo "1️⃣ Flag et constantes de test"

if grep -q "const AZALS_TEST_MODE = true" ui/app.js; then
    echo "   ✅ AZALS_TEST_MODE défini et activé"
else
    echo "   ❌ AZALS_TEST_MODE MANQUANT ou désactivé"
    ((ERRORS++))
fi

if grep -q "const AZALS_FORCED_STATES" ui/app.js; then
    echo "   ✅ AZALS_FORCED_STATES déclaré"
else
    echo "   ❌ AZALS_FORCED_STATES MANQUANT"
    ((ERRORS++))
fi

# 2. Fonctions de test
echo ""
echo "2️⃣ Fonctions mode test"

if grep -q "function azalsForceState(moduleId, state)" ui/app.js; then
    echo "   ✅ azalsForceState() définie"
else
    echo "   ❌ azalsForceState() MANQUANTE"
    ((ERRORS++))
fi

if grep -q "function initAzalsTestPanel()" ui/app.js; then
    echo "   ✅ initAzalsTestPanel() définie"
else
    echo "   ❌ initAzalsTestPanel() MANQUANTE"
    ((ERRORS++))
fi

# 3. Panneau HTML
echo ""
echo "3️⃣ Panneau HTML de test"

if grep -q 'id="azalsTestPanel"' ui/dashboard.html; then
    echo "   ✅ Panneau azalsTestPanel dans HTML"
else
    echo "   ❌ Panneau MANQUANT dans HTML"
    ((ERRORS++))
fi

# Vérifier les 5 selects
MODULES=("treasury" "legal" "tax" "hr" "accounting")
for mod in "${MODULES[@]}"; do
    if grep -q "id=\"azalsTest_${mod}\"" ui/dashboard.html; then
        echo "   ✅ Select $mod présent"
    else
        echo "   ⚠️  Select $mod MANQUANT"
    fi
done

# 4. Intégration dans collectStates
echo ""
echo "4️⃣ Intégration collectStates()"

if grep -A100 "async function collectStates()" ui/app.js | grep -q "AZALS_TEST_MODE"; then
    echo "   ✅ Vérification AZALS_TEST_MODE dans collectStates()"
else
    echo "   ❌ Pas de vérification AZALS_TEST_MODE"
    ((ERRORS++))
fi

if grep -A100 "async function collectStates()" ui/app.js | grep -q "AZALS_FORCED_STATES"; then
    echo "   ✅ Utilisation AZALS_FORCED_STATES"
else
    echo "   ❌ AZALS_FORCED_STATES non utilisé"
    ((ERRORS++))
fi

# 5. Intégration dans initDashboard
echo ""
echo "5️⃣ Initialisation dashboard"

if grep -A20 "async function initDashboard()" ui/app.js | grep -q "initAzalsTestPanel()"; then
    echo "   ✅ initAzalsTestPanel() appelée dans initDashboard()"
else
    echo "   ❌ initAzalsTestPanel() NON appelée"
    ((ERRORS++))
fi

# 6. Commentaires et documentation
echo ""
echo "6️⃣ Documentation"

if grep -q "MODE TEST AZALS (TEMPORAIRE)" ui/app.js; then
    echo "   ✅ Documentation mode test"
else
    echo "   ⚠️  Documentation absente"
fi

if grep -q "DÉSACTIVATION : mettre à false" ui/app.js || grep -q "DÉSACTIVER" ui/app.js; then
    echo "   ✅ Instructions de désactivation"
else
    echo "   ⚠️  Instructions de désactivation absentes"
fi

# 7. Syntaxe JavaScript
echo ""
echo "7️⃣ Validation syntaxe"

if node -c ui/app.js 2>/dev/null; then
    echo "   ✅ Syntaxe JavaScript valide"
else
    echo "   ❌ ERREURS DE SYNTAXE"
    node -c ui/app.js
    ((ERRORS++))
fi

# 8. Aucune modification backend
echo ""
echo "8️⃣ Isolation frontend"

if ! git diff --cached app/ 2>/dev/null | grep -q "^+"; then
    echo "   ✅ Aucune modification backend détectée"
else
    echo "   ⚠️  Modifications backend détectées"
fi

echo ""
echo "════════════════════════════════════════════════════════"

if [ $ERRORS -eq 0 ]; then
    echo "✅ MODE TEST AZALS INTÉGRÉ - PRÊT À TESTER"
    echo ""
    echo "📋 Instructions d'utilisation:"
    echo "   1. Ouvrir /dashboard dans le navigateur"
    echo "   2. Le panneau de test apparaît en bas à droite"
    echo "   3. Sélectionner les états souhaités (🔴🟠🟢)"
    echo "   4. Observer la priorisation en temps réel"
    echo ""
    echo "🔧 Désactivation:"
    echo "   Modifier dans ui/app.js : AZALS_TEST_MODE = false"
    exit 0
else
    echo "❌ $ERRORS ERREUR(S) CRITIQUE(S)"
    exit 1
fi
