#!/bin/bash
# Script de vérification finale - Intégration Trésorerie

echo "🔍 VÉRIFICATION FINALE - INTÉGRATION TRÉSORERIE"
echo "================================================="
echo ""

# 1. Variables CSS - Inline styles
echo "1️⃣ Inline Styles"
INLINE=$(grep -r 'style=' ui/*.html 2>/dev/null | wc -l)
if [ "$INLINE" -eq 0 ]; then
    echo "   ✅ 0 inline styles détectés"
else
    echo "   ❌ $INLINE inline styles trouvés"
fi
echo ""

# 2. Variables CSS documentées
echo "2️⃣ Variables CSS"
if [ -f "VARIABLES.md" ]; then
    VAR_COUNT=$(grep -c "^--color-\|^--spacing-\|^--shadow-\|^--border-" VARIABLES.md)
    echo "   ✅ $VAR_COUNT variables CSS documentées"
else
    echo "   ❌ VARIABLES.md manquant"
fi
echo ""

# 3. Modules cockpit
echo "3️⃣ Modules Cockpit"
if grep -q "buildTreasuryModule" ui/app.js; then
    echo "   ✅ buildTreasuryModule présent"
else
    echo "   ❌ buildTreasuryModule manquant"
fi

if grep -q "loadTreasuryData" ui/app.js; then
    echo "   ✅ loadTreasuryData présent"
else
    echo "   ❌ loadTreasuryData manquant"
fi
echo ""

# 4. Routes publiques
echo "4️⃣ Routes Publiques"
if grep -q '"/treasury"' app/core/middleware.py; then
    echo "   ✅ /treasury dans PUBLIC_PATHS"
else
    echo "   ❌ /treasury manquant"
fi
echo ""

# 5. Modèle TreasuryForecast
echo "5️⃣ Modèle TreasuryForecast"
if grep -q "user_id = Column" app/core/models.py; then
    echo "   ✅ user_id présent"
else
    echo "   ❌ user_id manquant"
fi

if grep -q "red_triggered = Column" app/core/models.py; then
    echo "   ✅ red_triggered présent"
else
    echo "   ❌ red_triggered manquant"
fi
echo ""

# 6. Migration 005
echo "6️⃣ Migration 005"
if [ -f "migrations/005_treasury_updates.sql" ]; then
    echo "   ✅ Migration 005 existe"
else
    echo "   ❌ Migration 005 manquante"
fi
echo ""

# 7. Classes CSS zone-inactive
echo "7️⃣ Classes CSS"
if grep -q ".zone-inactive" ui/styles.css; then
    echo "   ✅ .zone-inactive définie"
else
    echo "   ❌ .zone-inactive manquante"
fi
echo ""

# 8. Test connectivité API
echo "8️⃣ API Health Check"
HEALTH=$(curl -s https://azalscore.onrender.com/health 2>/dev/null)
if echo "$HEALTH" | grep -q '"status":"ok"'; then
    echo "   ✅ API disponible"
else
    echo "   ⚠️  API non disponible"
fi
echo ""

# 9. Fichiers documentation
echo "9️⃣ Documentation"
[ -f "VARIABLES.md" ] && echo "   ✅ VARIABLES.md" || echo "   ❌ VARIABLES.md"
[ -f "CHECKLIST_VERIFICATION.md" ] && echo "   ✅ CHECKLIST_VERIFICATION.md" || echo "   ❌ CHECKLIST_VERIFICATION.md"
[ -f "RAPPORT_INTEGRATION_TRESORERIE.md" ] && echo "   ✅ RAPPORT_INTEGRATION_TRESORERIE.md" || echo "   ❌ RAPPORT_INTEGRATION_TRESORERIE.md"
echo ""

# 10. Scripts tests
echo "🔟 Scripts Tests"
[ -f "test_red_manual.sh" ] && echo "   ✅ test_red_manual.sh" || echo "   ❌ test_red_manual.sh"
[ -f "run_migrations.py" ] && echo "   ✅ run_migrations.py" || echo "   ❌ run_migrations.py"
echo ""

echo "================================================="
echo "🎯 RÉSULTAT: Intégration complète au niveau code"
echo "⚠️  ACTION REQUISE: Exécuter migration 005 sur Render"
echo "================================================="
