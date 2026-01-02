#!/bin/bash
# Script de test manuel pour déclencher RED sur la trésorerie

echo "🔴 Test déclenchement RED - Trésorerie"
echo "=================================================="
echo ""

# Variables (à adapter avec vos credentials réels)
TENANT_ID="${TENANT_ID:-tenant-demo}"
EMAIL="${EMAIL:-admin@azals.fr}"
PASSWORD="${PASSWORD:-votre_mot_de_passe}"
BASE_URL="https://azalscore.onrender.com"

echo "Configuration:"
echo "  Tenant: $TENANT_ID"
echo "  Email: $EMAIL"
echo "  URL: $BASE_URL"
echo ""

# 1. Connexion
echo "1️⃣  Connexion..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Erreur de connexion"
  echo "$LOGIN_RESPONSE" | jq . 2>/dev/null || echo "$LOGIN_RESPONSE"
  echo ""
  echo "💡 Pour créer un utilisateur de test :"
  echo "   1. Allez sur $BASE_URL"
  echo "   2. Créez un compte avec tenant-id: $TENANT_ID"
  exit 1
fi

echo "✅ Connecté - Token obtenu"
echo ""

# 2. Créer prévision en DEFICIT
echo "2️⃣  Création prévision avec DEFICIT..."
echo "   Solde actuel: 5 000€"
echo "   Entrées prévues: 2 000€"
echo "   Sorties prévues: 15 000€"
echo "   → Prévision J+30: -8 000€ 🔴"
echo ""

FORECAST_RESPONSE=$(curl -s -X POST "$BASE_URL/treasury/forecast" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "opening_balance": 5000,
    "inflows": 2000,
    "outflows": 15000
  }')

echo "$FORECAST_RESPONSE" | jq . 2>/dev/null || echo "$FORECAST_RESPONSE"
echo ""

# 3. Vérifier le statut RED
echo "3️⃣  Vérification GET /treasury/latest..."
LATEST_RESPONSE=$(curl -s -X GET "$BASE_URL/treasury/latest" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "$LATEST_RESPONSE" | jq . 2>/dev/null || echo "$LATEST_RESPONSE"
echo ""

RED_TRIGGERED=$(echo "$LATEST_RESPONSE" | grep -o '"red_triggered":[^,}]*' | cut -d':' -f2)

if [ "$RED_TRIGGERED" = "true" ]; then
  echo "🔴 ALERTE ROUGE DÉCLENCHÉE !"
  echo ""
  echo "Vérifications à faire :"
  echo "  ✓ Cockpit affiche UNIQUEMENT la trésorerie"
  echo "  ✓ Bouton 'Consulter le rapport RED' visible"
  echo "  ✓ Workflow de validation en 3 étapes activé"
  echo "  ✓ Les autres modules (🟠🟢) sont masqués"
else
  echo "⚠️  RED non déclenché"
fi

echo ""
echo "=================================================="
echo "👉 Accédez au cockpit: $BASE_URL/dashboard"
echo "👉 Page trésorerie: $BASE_URL/treasury"
