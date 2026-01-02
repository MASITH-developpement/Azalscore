#!/bin/bash
#
# Script pour obtenir un token JWT et tester l'API Comptabilité
#

API_URL="${AZALS_API_URL:-https://azalscore.onrender.com}"
EMAIL="admin@azals.fr"
PASSWORD="azals2026"
TENANT="tenant-demo"

echo "=========================================="
echo "Comptabilité: Test API Render"
echo "=========================================="
echo "API URL: $API_URL"
echo ""

# Étape 1: Obtenir un token JWT
echo "📌 Étape 1: Authentification..."
echo ""

auth_response=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

echo "Réponse auth:"
echo "$auth_response" | jq '.' 2>/dev/null || echo "$auth_response"

token=$(echo "$auth_response" | jq -r '.access_token' 2>/dev/null)

if [ -z "$token" ] || [ "$token" = "null" ]; then
    echo ""
    echo "❌ Impossible d'obtenir un token"
    exit 1
fi

echo ""
echo "✅ Token obtenu: ${token:0:30}..."
echo ""

# Étape 2: Tester l'API Comptabilité
echo "📌 Étape 2: Appel API /accounting/status..."
echo ""

response=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $token" \
    -H "X-Tenant-ID: $TENANT" \
    "$API_URL/accounting/status")

http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -n -1)

echo "Status HTTP: $http_code"
echo ""
echo "Réponse API:"
echo "$body" | jq '.' 2>/dev/null || echo "$body"
echo ""

# Étape 3: Analyse des résultats
if [ "$http_code" = "200" ]; then
    echo "✅ Endpoint accessible"
    echo ""
    
    status=$(echo "$body" | jq -r '.status' 2>/dev/null)
    entries=$(echo "$body" | jq -r '.entries_up_to_date' 2>/dev/null)
    pending=$(echo "$body" | jq -r '.pending_entries_count' 2>/dev/null)
    closure=$(echo "$body" | jq -r '.last_closure_date' 2>/dev/null)
    days=$(echo "$body" | jq -r '.days_since_closure' 2>/dev/null)
    
    echo "Analyse:"
    echo "  Status:                  $status"
    echo "  Entries up to date:      $entries"
    echo "  Pending entries (7j):    $pending"
    echo "  Last closure date:       $closure"
    echo "  Days since closure:      $days"
    echo ""
    
    # Vérifications
    echo "Validations:"
    if [[ "$status" == "🟢" || "$status" == "🟠" ]]; then
        echo "  ✅ Status valide: $status"
    else
        echo "  ❌ Status invalide: $status"
    fi
    
    if [[ "$status" != "🔴" ]]; then
        echo "  ✅ Pas de 🔴 (correct)"
    else
        echo "  ❌ Status contient 🔴 (interdit)"
    fi
    
else
    echo "❌ Erreur HTTP: $http_code"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Test complété"
