#!/bin/bash
#
# Script de test manuel de l'API Comptabilité
# Usage: ./test_accounting_api.sh <API_URL> <TOKEN> [TENANT]
#

API_URL="${1:-https://azalscore.onrender.com}"
TOKEN="${2:-}"
TENANT="${3:-tenant-demo}"

if [ -z "$TOKEN" ]; then
    echo "❌ Erreur: TOKEN requis"
    echo "Usage: $0 <API_URL> <TOKEN> [TENANT]"
    echo ""
    echo "Exemple:"
    echo "  export TOKEN='eyJ0eXAiOiJKV1QiLCJhbGc...' "
    echo "  $0 https://azalscore.onrender.com \$TOKEN tenant-demo"
    exit 1
fi

echo "=========================================="
echo "Test API Comptabilité"
echo "=========================================="
echo "API URL:  $API_URL"
echo "Tenant:   $TENANT"
echo "Token:    ${TOKEN:0:20}..."
echo ""

# Test 1: Ping l'endpoint
echo "📡 Test 1: Appel GET /accounting/status"
echo ""

response=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Tenant-ID: $TENANT" \
    -H "Content-Type: application/json" \
    "$API_URL/accounting/status")

http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -n -1)

echo "Status HTTP: $http_code"
echo ""
echo "Réponse JSON:"
echo "$body" | jq '.' 2>/dev/null || echo "$body"
echo ""

# Analyse
if [ "$http_code" = "200" ]; then
    echo "✅ Endpoint accessible"
    
    # Extraire les champs
    status=$(echo "$body" | jq -r '.status' 2>/dev/null)
    entries_up=$(echo "$body" | jq -r '.entries_up_to_date' 2>/dev/null)
    pending=$(echo "$body" | jq -r '.pending_entries_count' 2>/dev/null)
    closure=$(echo "$body" | jq -r '.last_closure_date' 2>/dev/null)
    days=$(echo "$body" | jq -r '.days_since_closure' 2>/dev/null)
    
    echo ""
    echo "Analyse des données:"
    echo "  Status:                  $status"
    echo "  Entries up to date:      $entries_up"
    echo "  Pending entries (7j):    $pending"
    echo "  Last closure date:       $closure"
    echo "  Days since closure:      $days"
    
    # Vérifications
    echo ""
    echo "Vérifications:"
    
    if [[ "$status" == "🟢" || "$status" == "🟠" ]]; then
        echo "  ✅ Status est valide: $status"
    else
        echo "  ❌ Status invalide: $status (doit être 🟢 ou 🟠)"
    fi
    
    if [[ "$status" != "🔴" ]]; then
        echo "  ✅ Status ne contient pas 🔴 (correct)"
    else
        echo "  ❌ Status contient 🔴 (interdit pour Comptabilité)"
    fi
    
    if [[ "$entries_up" == "true" || "$entries_up" == "false" ]]; then
        echo "  ✅ entries_up_to_date est booléen"
    else
        echo "  ❌ entries_up_to_date invalide: $entries_up"
    fi
    
    if [[ "$pending" =~ ^[0-9]+$ ]]; then
        echo "  ✅ pending_entries_count est un nombre: $pending"
    else
        echo "  ❌ pending_entries_count invalide: $pending"
    fi
    
elif [ "$http_code" = "401" ]; then
    echo "❌ Non authentifié (401)"
    echo "   Vérifiez que le TOKEN est valide"
elif [ "$http_code" = "422" ]; then
    echo "❌ Erreur de validation (422)"
    echo "   Vérifiez que X-Tenant-ID est correct"
else
    echo "❌ Erreur HTTP: $http_code"
fi

echo ""
echo "=========================================="
