#!/bin/bash

echo "═══════════════════════════════════════════════════════════"
echo "�� VÉRIFICATION PRÉ-DÉPLOIEMENT"
echo "═══════════════════════════════════════════════════════════"
echo ""

ERRORS=0

# 1. Vérifier les imports Python
echo "1️⃣ Imports Python"
export DATABASE_URL="postgresql://test:test@localhost/test"

if python3 -c "from app.main import app" 2>/dev/null; then
    echo "   ✅ app.main imports OK"
else
    echo "   ❌ app.main imports FAILED"
    ((ERRORS++))
fi

if python3 -c "from app.core.security import create_access_token" 2>/dev/null; then
    echo "   ✅ app.core.security imports OK"
else
    echo "   ❌ app.core.security imports FAILED"
    ((ERRORS++))
fi

if python3 -c "from app.api.accounting import router" 2>/dev/null; then
    echo "   ✅ app.api.accounting imports OK"
else
    echo "   ❌ app.api.accounting imports FAILED"
    ((ERRORS++))
fi

# 2. Vérifier les routes enregistrées
echo ""
echo "2️⃣ Routes Backend"

ROUTES=(
    "auth_router"
    "accounting_router"
    "treasury_router"
    "journal_router"
    "decision_router"
)

for route in "${ROUTES[@]}"; do
    if grep -q "include_router($route)" app/main.py; then
        echo "   ✅ $route enregistré"
    else
        echo "   ❌ $route manquant"
        ((ERRORS++))
    fi
done

# 3. Vérifier les fichiers UI
echo ""
echo "3️⃣ Fichiers UI"

UI_FILES=(
    "ui/dashboard.html"
    "ui/app.js"
    "ui/styles.css"
)

for file in "${UI_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file existe"
    else
        echo "   ❌ $file manquant"
        ((ERRORS++))
    fi
done

# 4. Vérifier buildAccountingModule
echo ""
echo "4️⃣ Fix buildAccountingModule"

if grep -q "buildAccountingModule(accountingData)" ui/app.js; then
    echo "   ✅ buildAccountingModule utilise accountingData"
else
    echo "   ❌ buildAccountingModule utilise journalData (BUG!)"
    ((ERRORS++))
fi

# 5. Vérifier le template Comptabilité
echo ""
echo "5️⃣ Template Comptabilité"

if grep -q 'id="accountingCardTemplate"' ui/dashboard.html; then
    echo "   ✅ accountingCardTemplate présent"
else
    echo "   ❌ accountingCardTemplate manquant"
    ((ERRORS++))
fi

# 6. Vérifier les classes CSS
echo ""
echo "6️⃣ Classes CSS"

if grep -q ".card-success" ui/styles.css; then
    echo "   ✅ .card-success présente"
else
    echo "   ❌ .card-success manquante"
    ((ERRORS++))
fi

if grep -q ".card-warning" ui/styles.css; then
    echo "   ✅ .card-warning présente"
else
    echo "   ❌ .card-warning manquante"
    ((ERRORS++))
fi

# 7. Vérifier requirements.txt
echo ""
echo "7️⃣ Dépendances"

if [ -f "requirements.txt" ]; then
    echo "   ✅ requirements.txt existe"
    
    DEPS=("fastapi" "sqlalchemy" "apscheduler")
    for dep in "${DEPS[@]}"; do
        if grep -qi "$dep" requirements.txt; then
            echo "   ✅ $dep présent"
        else
            echo "   ⚠️  $dep manquant"
        fi
    done
else
    echo "   ❌ requirements.txt manquant"
    ((ERRORS++))
fi

# Résultat
echo ""
echo "═══════════════════════════════════════════════════════════"

if [ $ERRORS -eq 0 ]; then
    echo "✅ PRÊT POUR DÉPLOIEMENT"
    echo "   Tous les checks sont au vert"
    exit 0
else
    echo "❌ $ERRORS ERREUR(S) DÉTECTÉE(S)"
    echo "   Corriger avant de déployer"
    exit 1
fi
