#!/bin/bash

echo "════════════════════════════════════════════════════════"
echo "❄️  VÉRIFICATION GEL CORE AZALS"
echo "════════════════════════════════════════════════════════"

ERRORS=0
WARNINGS=0

# 1. Documentation README_CORE_AZALS.md
echo ""
echo "1️⃣ Documentation CORE"

if [ -f "README_CORE_AZALS.md" ]; then
    echo "   ✅ README_CORE_AZALS.md créé"
    
    # Vérifier sections obligatoires
    SECTIONS=(
        "Philosophie AZALS"
        "Architecture du cockpit"
        "Système de priorisation"
        "Règles de priorisation strictes"
        "Pattern 🔴"
        "Souveraineté du dirigeant"
        "Ce qui est figé vs ce qui peut évoluer"
        "Justification des choix"
    )
    
    for section in "${SECTIONS[@]}"; do
        if grep -q "$section" README_CORE_AZALS.md; then
            echo "   ✅ Section '$section' présente"
        else
            echo "   ⚠️  Section '$section' manquante"
            ((WARNINGS++))
        fi
    done
    
else
    echo "   ❌ README_CORE_AZALS.md MANQUANT"
    ((ERRORS++))
fi

# 2. Commentaires protection CORE dans app.js
echo ""
echo "2️⃣ Commentaires protection dans app.js"

if grep -q "CORE AZALS V1.0 — FIGÉ" ui/app.js; then
    echo "   ✅ En-tête CORE AZALS présent"
else
    echo "   ⚠️  En-tête CORE AZALS manquant"
    ((WARNINGS++))
fi

if grep -q "CORE AZALS — NE PAS MODIFIER SANS DÉCISION D'ARCHITECTURE" ui/app.js; then
    echo "   ✅ Commentaire protection DOMAIN_PRIORITY"
else
    echo "   ⚠️  Protection DOMAIN_PRIORITY manquante"
    ((WARNINGS++))
fi

if grep -q "CORE AZALS — PRIORISATION TRANSVERSE (FIGÉE)" ui/app.js; then
    echo "   ✅ Commentaire protection priorisation transverse"
else
    echo "   ⚠️  Protection priorisation transverse manquante"
    ((WARNINGS++))
fi

# 3. Constantes critiques
echo ""
echo "3️⃣ Constantes critiques CORE"

if grep -q "const DOMAIN_PRIORITY" ui/app.js; then
    echo "   ✅ DOMAIN_PRIORITY déclaré"
    
    # Vérifier ordre
    if grep -A6 "const DOMAIN_PRIORITY" ui/app.js | grep -q "'treasury': 1" && \
       grep -A6 "const DOMAIN_PRIORITY" ui/app.js | grep -q "'legal': 2" && \
       grep -A6 "const DOMAIN_PRIORITY" ui/app.js | grep -q "'tax': 3" && \
       grep -A6 "const DOMAIN_PRIORITY" ui/app.js | grep -q "'hr': 4" && \
       grep -A6 "const DOMAIN_PRIORITY" ui/app.js | grep -q "'accounting': 5"; then
        echo "   ✅ Ordre priorité correct (1-5)"
    else
        echo "   ❌ Ordre priorité INCORRECT"
        ((ERRORS++))
    fi
else
    echo "   ❌ DOMAIN_PRIORITY MANQUANT"
    ((ERRORS++))
fi

# 4. Fonctions CORE
echo ""
echo "4️⃣ Fonctions CORE"

CORE_FUNCTIONS=(
    "async function collectStates()"
    "function resolvePriority(states)"
    "function renderCockpit(priority, states)"
)

for func in "${CORE_FUNCTIONS[@]}"; do
    if grep -q "$func" ui/app.js; then
        echo "   ✅ $func présente"
    else
        echo "   ❌ $func MANQUANTE"
        ((ERRORS++))
    fi
done

# 5. Règles de priorisation
echo ""
echo "5️⃣ Règles de priorisation"

RULES=(
    "REGLE_CRITIQUE_UNIQUE"
    "REGLE_TENSION_MULTIPLE"
    "REGLE_NORMAL_COMPLET"
)

for rule in "${RULES[@]}"; do
    if grep -q "$rule" ui/app.js; then
        echo "   ✅ $rule implémentée"
    else
        echo "   ❌ $rule MANQUANTE"
        ((ERRORS++))
    fi
done

# 6. Documentation dans README
echo ""
echo "6️⃣ Contenu documentation"

if [ -f "README_CORE_AZALS.md" ]; then
    # Vérifier ordre priorité documenté
    if grep -q "Financier > Juridique > Fiscal > RH > Comptabilité" README_CORE_AZALS.md; then
        echo "   ✅ Ordre priorité documenté"
    else
        echo "   ⚠️  Ordre priorité non documenté"
        ((WARNINGS++))
    fi
    
    # Vérifier règle absolue
    if grep -q "Un seul 🔴 visible à la fois" README_CORE_AZALS.md; then
        echo "   ✅ Règle absolue documentée"
    else
        echo "   ⚠️  Règle absolue non documentée"
        ((WARNINGS++))
    fi
    
    # Vérifier justifications
    if grep -q "Justification des choix" README_CORE_AZALS.md; then
        echo "   ✅ Justifications présentes"
    else
        echo "   ⚠️  Justifications manquantes"
        ((WARNINGS++))
    fi
    
    # Vérifier section figé/évolutif
    if grep -q "CE QUI EST FIGÉ" README_CORE_AZALS.md && \
       grep -q "CE QUI PEUT ÉVOLUER" README_CORE_AZALS.md; then
        echo "   ✅ Distinction figé/évolutif documentée"
    else
        echo "   ⚠️  Distinction figé/évolutif manquante"
        ((WARNINGS++))
    fi
fi

# 7. Intégrité syntaxe
echo ""
echo "7️⃣ Intégrité syntaxe"

if node -c ui/app.js 2>/dev/null; then
    echo "   ✅ Syntaxe JavaScript valide"
else
    echo "   ❌ ERREURS DE SYNTAXE"
    node -c ui/app.js
    ((ERRORS++))
fi

# 8. Aucune modification fonctionnelle
echo ""
echo "8️⃣ Aucune modification fonctionnelle"

# Vérifier que seuls app.js et README ont été modifiés
if git diff --cached --name-only 2>/dev/null | grep -v "ui/app.js" | grep -v "README_CORE_AZALS.md" | grep -v "verify_core_freeze.sh" | grep -q .; then
    echo "   ⚠️  Fichiers supplémentaires modifiés détectés"
    git diff --cached --name-only | grep -v "ui/app.js" | grep -v "README_CORE_AZALS.md" | grep -v "verify_core_freeze.sh"
    ((WARNINGS++))
else
    echo "   ✅ Seuls app.js et README_CORE_AZALS.md modifiés"
fi

# 9. Longueur documentation
echo ""
echo "9️⃣ Qualité documentation"

if [ -f "README_CORE_AZALS.md" ]; then
    LINES=$(wc -l < README_CORE_AZALS.md)
    if [ $LINES -gt 500 ]; then
        echo "   ✅ Documentation complète ($LINES lignes)"
    else
        echo "   ⚠️  Documentation courte ($LINES lignes)"
        ((WARNINGS++))
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ CORE AZALS GELÉ ET DOCUMENTÉ - PARFAIT"
    echo ""
    echo "📚 Documentation : /README_CORE_AZALS.md"
    echo "🔒 Protection code : Commentaires CORE AZALS dans app.js"
    echo "🎯 Prochaine étape : Commit et gel de version"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "✅ CORE AZALS GELÉ AVEC $WARNINGS AVERTISSEMENT(S)"
    echo ""
    echo "⚠️  Points à améliorer (non bloquants) :"
    echo "   - Vérifier les sections manquantes"
    echo "   - Compléter la documentation"
    exit 0
else
    echo "❌ $ERRORS ERREUR(S) CRITIQUE(S) + $WARNINGS AVERTISSEMENT(S)"
    echo ""
    echo "🔧 Actions requises :"
    echo "   - Corriger les erreurs critiques"
    echo "   - Vérifier l'intégrité du CORE"
    exit 1
fi
