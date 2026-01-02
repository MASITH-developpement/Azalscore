#!/bin/bash

echo "════════════════════════════════════════════════════════"
echo "🔍 VÉRIFICATION PRIORISATION TRANSVERSE"
echo "════════════════════════════════════════════════════════"

ERRORS=0

# 1. Structure des constantes
echo ""
echo "1️⃣ Constantes de priorisation"

if grep -q "const DOMAIN_PRIORITY" ui/app.js; then
    echo "   ✅ DOMAIN_PRIORITY défini"
else
    echo "   ❌ DOMAIN_PRIORITY MANQUANT"
    ((ERRORS++))
fi

# Vérifier ordre strict
if grep -A6 "const DOMAIN_PRIORITY" ui/app.js | grep -q "'treasury': 1" && \
   grep -A6 "const DOMAIN_PRIORITY" ui/app.js | grep -q "'legal': 2" && \
   grep -A6 "const DOMAIN_PRIORITY" ui/app.js | grep -q "'tax': 3" && \
   grep -A6 "const DOMAIN_PRIORITY" ui/app.js | grep -q "'hr': 4" && \
   grep -A6 "const DOMAIN_PRIORITY" ui/app.js | grep -q "'accounting': 5"; then
    echo "   ✅ Ordre priorité: Trésorerie(1) > Juridique(2) > Fiscalité(3) > RH(4) > Comptabilité(5)"
else
    echo "   ❌ Ordre priorité INCORRECT"
    ((ERRORS++))
fi

# 2. Journalisation
echo ""
echo "2️⃣ Journalisation"

if grep -q "const cockpitLog" ui/app.js; then
    echo "   ✅ cockpitLog déclaré"
else
    echo "   ❌ cockpitLog MANQUANT"
    ((ERRORS++))
fi

if grep -q "function logPriorityDecision" ui/app.js; then
    echo "   ✅ logPriorityDecision() définie"
else
    echo "   ❌ logPriorityDecision() MANQUANTE"
    ((ERRORS++))
fi

# 3. Fonction collectStates
echo ""
echo "3️⃣ collectStates()"

if grep -q "async function collectStates()" ui/app.js; then
    echo "   ✅ collectStates() définie"
else
    echo "   ❌ collectStates() MANQUANTE"
    ((ERRORS++))
fi

# Vérifier gestion erreurs pour chaque module
MODULES=("treasury" "accounting" "legal" "tax" "hr")
for mod in "${MODULES[@]}"; do
    if grep -A100 "async function collectStates" ui/app.js | grep -q "states.$mod.error = error.message"; then
        echo "   ✅ Gestion erreur $mod (fallback 🟠)"
    else
        echo "   ⚠️  Gestion erreur $mod manquante"
    fi
done

# 4. Fonction resolvePriority
echo ""
echo "4️⃣ resolvePriority()"

if grep -q "function resolvePriority(states)" ui/app.js; then
    echo "   ✅ resolvePriority() définie"
else
    echo "   ❌ resolvePriority() MANQUANTE"
    ((ERRORS++))
fi

# Vérifier règles
if grep -A50 "function resolvePriority" ui/app.js | grep -q "REGLE_CRITIQUE_UNIQUE"; then
    echo "   ✅ RÈGLE 1: Critique unique"
else
    echo "   ❌ RÈGLE 1 MANQUANTE"
    ((ERRORS++))
fi

if grep -A100 "function resolvePriority" ui/app.js | grep -q "REGLE_TENSION_MULTIPLE"; then
    echo "   ✅ RÈGLE 2: Tension multiple"
else
    echo "   ❌ RÈGLE 2 MANQUANTE"
    ((ERRORS++))
fi

if grep -A150 "function resolvePriority" ui/app.js | grep -q "REGLE_NORMAL_COMPLET"; then
    echo "   ✅ RÈGLE 3: Normal complet"
else
    echo "   ❌ RÈGLE 3 MANQUANTE"
    ((ERRORS++))
fi

# 5. Fonction renderCockpit
echo ""
echo "5️⃣ renderCockpit()"

if grep -q "function renderCockpit(priority, states)" ui/app.js; then
    echo "   ✅ renderCockpit() définie avec paramètres"
else
    echo "   ❌ renderCockpit() MANQUANTE"
    ((ERRORS++))
fi

# Vérifier 3 modes
if grep -A200 "function renderCockpit" ui/app.js | grep -q "priority.mode === 'critical'"; then
    echo "   ✅ Mode critique géré"
else
    echo "   ❌ Mode critique NON géré"
    ((ERRORS++))
fi

if grep -A250 "function renderCockpit" ui/app.js | grep -q "priority.mode === 'tension'"; then
    echo "   ✅ Mode tension géré"
else
    echo "   ❌ Mode tension NON géré"
    ((ERRORS++))
fi

# 6. Intégration buildCockpit
echo ""
echo "6️⃣ Intégration dans buildCockpit()"

if grep -A20 "async function buildCockpit" ui/app.js | grep -q "const states = await collectStates()"; then
    echo "   ✅ collectStates() appelée"
else
    echo "   ❌ collectStates() NON appelée"
    ((ERRORS++))
fi

if grep -A25 "async function buildCockpit" ui/app.js | grep -q "const priority = resolvePriority(states)"; then
    echo "   ✅ resolvePriority() appelée"
else
    echo "   ❌ resolvePriority() NON appelée"
    ((ERRORS++))
fi

if grep -A30 "async function buildCockpit" ui/app.js | grep -q "renderCockpit(priority, states)"; then
    echo "   ✅ renderCockpit() appelée"
else
    echo "   ❌ renderCockpit() NON appelée"
    ((ERRORS++))
fi

# 7. Commentaires explicites
echo ""
echo "7️⃣ Commentaires et documentation"

if grep -q "RÈGLE ABSOLUE : Un seul 🔴 visible à la fois" ui/app.js; then
    echo "   ✅ Documentation règle absolue"
else
    echo "   ⚠️  Documentation règle absente"
fi

if grep -q "ORDRE : Trésorerie > Juridique > Fiscalité > RH > Comptabilité" ui/app.js; then
    echo "   ✅ Documentation ordre priorité"
else
    echo "   ⚠️  Documentation ordre absente"
fi

# 8. Syntaxe JavaScript
echo ""
echo "8️⃣ Validation syntaxe JavaScript"

if command -v node &> /dev/null; then
    if node -c ui/app.js 2>/dev/null; then
        echo "   ✅ Syntaxe JavaScript valide"
    else
        echo "   ❌ ERREURS DE SYNTAXE JavaScript"
        node -c ui/app.js
        ((ERRORS++))
    fi
else
    echo "   ⚠️  Node.js non disponible (skip validation syntaxe)"
fi

echo ""
echo "════════════════════════════════════════════════════════"

if [ $ERRORS -eq 0 ]; then
    echo "✅ PRIORISATION TRANSVERSE INTÉGRÉE - OK"
    exit 0
else
    echo "❌ $ERRORS ERREUR(S) CRITIQUE(S)"
    exit 1
fi
