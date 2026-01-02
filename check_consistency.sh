#!/bin/bash
# Script de vérification des incohérences de casse
# À exécuter avant chaque commit/déploiement

echo "🔍 VÉRIFICATION COHÉRENCE CASSE - AZALS"
echo "========================================"
echo ""

ERRORS=0

# 1. Vérifier workflow steps (backend MAJUSCULES, frontend doit correspondre)
echo "1️⃣ Workflow Steps"
BACKEND_STEPS=$(grep -r "ACKNOWLEDGE\|COMPLETENESS\|FINAL" app/core/models.py | grep -c "class RedWorkflowStep")
FRONTEND_STEPS=$(grep -c "id: 'ACKNOWLEDGE'\|id: 'COMPLETENESS'\|id: 'FINAL'" ui/app.js)

if [ "$FRONTEND_STEPS" -eq 3 ]; then
    echo "   ✅ Frontend: 3 étapes en MAJUSCULES détectées"
else
    echo "   ❌ Frontend: Incohérence détectée ($FRONTEND_STEPS/3)"
    ERRORS=$((ERRORS + 1))
fi

# 2. Vérifier red_triggered (snake_case partout)
echo ""
echo "2️⃣ red_triggered (snake_case requis)"
CAMELCASE=$(grep -r "redTriggered" ui/app.js app/ 2>/dev/null | wc -l)
if [ "$CAMELCASE" -eq 0 ]; then
    echo "   ✅ Aucun redTriggered (camelCase) trouvé"
else
    echo "   ❌ $CAMELCASE occurrences de redTriggered trouvées"
    grep -rn "redTriggered" ui/app.js app/ 2>/dev/null
    ERRORS=$((ERRORS + 1))
fi

# 3. Vérifier tenant_id vs tenantId
echo ""
echo "3️⃣ tenant_id cohérence"
BACKEND_TENANT=$(grep -rc "tenant_id" app/ | grep -v ":0" | wc -l)
FRONTEND_TENANT_SNAKE=$(grep -c "tenant_id" ui/app.js)
FRONTEND_TENANT_CAMEL=$(grep -c "tenantId" ui/app.js)

echo "   Backend: $BACKEND_TENANT fichiers avec tenant_id"
echo "   Frontend: $FRONTEND_TENANT_SNAKE tenant_id, $FRONTEND_TENANT_CAMEL tenantId"

if [ "$FRONTEND_TENANT_CAMEL" -gt 0 ] && [ "$FRONTEND_TENANT_SNAKE" -gt 0 ]; then
    echo "   ⚠️  Mix snake_case/camelCase dans frontend (acceptable en JS)"
fi

# 4. Vérifier décisions GREEN/ORANGE/RED
echo ""
echo "4️⃣ Niveaux de décision"
BACKEND_LEVELS=$(grep -r "class DecisionLevel" app/core/models.py -A 5 | grep -c "GREEN\|ORANGE\|RED")
if [ "$BACKEND_LEVELS" -ge 3 ]; then
    echo "   ✅ Backend: GREEN, ORANGE, RED définis"
else
    echo "   ❌ Backend: Niveaux incomplets"
    ERRORS=$((ERRORS + 1))
fi

# 5. Vérifier endpoints API (/auth, /treasury, etc.)
echo ""
echo "5️⃣ Endpoints API (minuscules requis)"
UPPERCASE_ENDPOINTS=$(grep -r "router = APIRouter(prefix=" app/api/ | grep -v "prefix=\"/" | wc -l)
if [ "$UPPERCASE_ENDPOINTS" -eq 0 ]; then
    echo "   ✅ Tous les prefixes commencent par /"
else
    echo "   ❌ $UPPERCASE_ENDPOINTS endpoints sans / initial"
    grep -rn "router = APIRouter(prefix=" app/api/ | grep -v "prefix=\"/"
    ERRORS=$((ERRORS + 1))
fi

# 6. Vérifier cohérence des réponses API
echo ""
echo "6️⃣ Modèles Pydantic Response"
RESPONSE_MODELS=$(grep -rc "class.*Response" app/api/ | grep -v ":0" | wc -l)
echo "   $RESPONSE_MODELS fichiers avec modèles Response définis"

# 7. Vérifier imports cohérents
echo ""
echo "7️⃣ Structure imports"
RELATIVE_IMPORTS=$(grep -r "from \.\." app/ | wc -l)
ABSOLUTE_IMPORTS=$(grep -r "from app\." app/ | wc -l)
echo "   Imports relatifs: $RELATIVE_IMPORTS"
echo "   Imports absolus: $ABSOLUTE_IMPORTS"

if [ "$ABSOLUTE_IMPORTS" -gt "$RELATIVE_IMPORTS" ]; then
    echo "   ✅ Majorité imports absolus (recommandé)"
else
    echo "   ⚠️  Préférer imports absolus (from app.core...)"
fi

echo ""
echo "========================================"
if [ "$ERRORS" -eq 0 ]; then
    echo "✅ SUCCÈS: Aucune incohérence détectée"
    exit 0
else
    echo "❌ ÉCHEC: $ERRORS incohérence(s) détectée(s)"
    exit 1
fi
