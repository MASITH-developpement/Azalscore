#!/bin/bash
# Script de vérification de la migration POS v2

echo "=========================================="
echo "VERIFICATION MIGRATION POS v2"
echo "=========================================="
echo ""

echo "1. Structure des fichiers"
echo "------------------------"
ls -lh app/modules/pos/ | grep -E "(router_v2|tests|MIGRATION)"
echo ""

echo "2. Contenu du dossier tests"
echo "-------------------------"
ls -lh app/modules/pos/tests/
echo ""

echo "3. Nombre d'endpoints dans router_v2.py"
echo "-------------------------------------"
echo -n "Total: "
grep -E "^@router\.(get|post|patch|delete)" app/modules/pos/router_v2.py | wc -l
echo ""

echo "4. Détail des endpoints par catégorie"
echo "-----------------------------------"
echo -n "Stores: "
grep -E "^@router\..*/stores" app/modules/pos/router_v2.py | wc -l
echo -n "Terminals: "
grep -E "^@router\..*/terminals" app/modules/pos/router_v2.py | wc -l
echo -n "Users: "
grep -E "^@router\..*/users" app/modules/pos/router_v2.py | wc -l
echo -n "Sessions: "
grep -E "^@router\..*/sessions" app/modules/pos/router_v2.py | wc -l
echo -n "Transactions: "
grep -E "^@router\..*/transactions" app/modules/pos/router_v2.py | wc -l
echo -n "Hold: "
grep -E "^@router\..*/hold" app/modules/pos/router_v2.py | wc -l
echo -n "Cash Movements: "
grep -E "^@router\..*/cash-movements" app/modules/pos/router_v2.py | wc -l
echo -n "Quick Keys: "
grep -E "^@router\..*/quick-keys" app/modules/pos/router_v2.py | wc -l
echo -n "Reports: "
grep -E "^@router\..*/reports" app/modules/pos/router_v2.py | wc -l
echo -n "Dashboard: "
grep -E "^@router\..*/dashboard" app/modules/pos/router_v2.py | wc -l
echo ""

echo "5. Collection des tests"
echo "---------------------"
python3 -m pytest app/modules/pos/tests/ --collect-only -q 2>&1 | tail -3
echo ""

echo "6. Vérification du service.py"
echo "---------------------------"
echo -n "user_id dans __init__: "
grep -c "user_id: str = None" app/modules/pos/service.py
echo -n "self.user_id assigné: "
grep -c "self.user_id = user_id" app/modules/pos/service.py
echo ""

echo "7. Vérification imports SaaSContext"
echo "---------------------------------"
echo -n "Import get_saas_context: "
grep -c "from app.core.dependencies_v2 import get_saas_context" app/modules/pos/router_v2.py
echo -n "Import SaaSContext: "
grep -c "from app.core.saas_context import SaaSContext" app/modules/pos/router_v2.py
echo ""

echo "8. Statistiques de code"
echo "--------------------"
wc -l app/modules/pos/router_v2.py app/modules/pos/service.py app/modules/pos/tests/*.py | tail -1
echo ""

echo "=========================================="
echo "VERIFICATION TERMINÉE"
echo "=========================================="
echo ""
echo "Pour exécuter les tests:"
echo "  python3 -m pytest app/modules/pos/tests/ -v"
echo ""
echo "Pour voir le résumé de migration:"
echo "  cat app/modules/pos/MIGRATION_V2_SUMMARY.md"
