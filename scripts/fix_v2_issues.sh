#!/bin/bash
# Fix Critical Issues - v2 Router Patterns
# ==========================================
# Corrige les imports et prefix dans les router_v2.py

echo "🔧 Correction des Issues Critiques v2"
echo "======================================"
echo ""

# Modules avec issues identifiés par le code review
MODULES=(
    "automated_accounting"
    "bi"
    "commercial"
    "ecommerce"
    "finance"
    "guardian"
    "helpdesk"
    "hr"
    "iam"
    "inventory"
    "marketplace"
    "production"
    "projects"
    "tenants"
)

fixed_count=0

for module in "${MODULES[@]}"; do
    router_file="app/modules/$module/router_v2.py"

    if [ ! -f "$router_file" ]; then
        echo "⏭️  $module: router_v2.py non trouvé"
        continue
    fi

    echo "🔍 $module..."

    # Fix 1: Import get_saas_context depuis dependencies_v2
    if grep -q "from app.core.saas_context import.*get_saas_context" "$router_file"; then
        echo "   ✏️  Correction import get_saas_context"

        # Remplacer l'import combiné par deux imports séparés
        sed -i 's/from app.core.saas_context import SaaSContext, get_saas_context/from app.core.dependencies_v2 import get_saas_context\nfrom app.core.saas_context import SaaSContext/' "$router_file"

        ((fixed_count++))
    fi

    # Fix 2: Prefix /v2/ manquant
    if grep -q 'prefix="/' "$router_file" && ! grep -q 'prefix="/v2/' "$router_file"; then
        echo "   ✏️  Correction prefix /v2/"

        # Ajouter /v2 au prefix existant
        sed -i 's|prefix="/|prefix="/v2/|' "$router_file"

        ((fixed_count++))
    fi
done

echo ""
echo "======================================"
echo "✅ $fixed_count corrections appliquées"
echo ""
