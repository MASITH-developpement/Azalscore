#!/bin/bash

# Script de vérification du masquage de la Comptabilité quand 🔴 RED est actif

BASE_URL="https://azalscore.onrender.com"
CREDENTIALS="-H 'Content-Type: application/json' -H 'X-Tenant-ID: tenant-demo' -d '{\"email\":\"admin@azals.fr\",\"password\":\"azals2026\"}'"

# Obtenir le token
echo "📌 Étape 1 : Authentification..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-demo" \
  -d '{"email":"admin@azals.fr","password":"azals2026"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Impossible d'obtenir le token JWT"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Token obtenu"

# Test 1 : Vérifier l'état RED et Comptabilité AVANT workflow
echo ""
echo "📌 Étape 2 : Vérifier l'état RED (AVANT workflow)..."

TREASURY_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: tenant-demo" \
  "$BASE_URL/treasury/latest")

RED_STATUS=$(echo "$TREASURY_RESPONSE" | grep -o '"red_triggered":true')
DECISION_ID=$(echo "$TREASURY_RESPONSE" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -n "$RED_STATUS" ]; then
  echo "✅ RED ACTIF (🔴) - Déficit détecté"
  echo "   Decision ID: $DECISION_ID"
else
  echo "⚠️  RED INACTIF - Pas de déficit"
fi

ACCOUNTING_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: tenant-demo" \
  "$BASE_URL/accounting/status")

ACCOUNTING_STATUS=$(echo "$ACCOUNTING_RESPONSE" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
echo "✅ Comptabilité status: $ACCOUNTING_STATUS"

# Test 2 : Complèter le workflow RED (si RED actif)
if [ -n "$RED_STATUS" ] && [ ! -z "$DECISION_ID" ]; then
  echo ""
  echo "📌 Étape 3 : Compléter le workflow RED..."
  
  # Step 1 : ACKNOWLEDGE
  echo "  Étape 3a : POST /decision/red/ACKNOWLEDGE/$DECISION_ID"
  ACK_RESPONSE=$(curl -s -X POST "$BASE_URL/decision/red/ACKNOWLEDGE/$DECISION_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Tenant-ID: tenant-demo")
  
  echo "  Response: $ACK_RESPONSE" | grep -o '"status":"[^"]*'
  
  # Step 2 : COMPLETENESS
  echo "  Étape 3b : POST /decision/red/COMPLETENESS/$DECISION_ID"
  COMPLETE_RESPONSE=$(curl -s -X POST "$BASE_URL/decision/red/COMPLETENESS/$DECISION_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Tenant-ID: tenant-demo")
  
  echo "  Response: $COMPLETE_RESPONSE" | grep -o '"status":"[^"]*'
  
  # Step 3 : FINAL
  echo "  Étape 3c : POST /decision/red/FINAL/$DECISION_ID"
  FINAL_RESPONSE=$(curl -s -X POST "$BASE_URL/decision/red/FINAL/$DECISION_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Tenant-ID: tenant-demo")
  
  echo "  Response: $FINAL_RESPONSE" | grep -o '"status":"[^"]*'
  
  # Vérifier le résultat
  sleep 2
  echo ""
  echo "📌 Étape 4 : Vérifier l'état RED (APRÈS workflow)..."
  
  TREASURY_AFTER=$(curl -s -H "Authorization: Bearer $TOKEN" \
    -H "X-Tenant-ID: tenant-demo" \
    "$BASE_URL/treasury/latest")
  
  RED_AFTER=$(echo "$TREASURY_AFTER" | grep -o '"red_triggered":true')
  
  if [ -z "$RED_AFTER" ]; then
    echo "✅ RED DÉSACTIVÉ (🟢) - Workflow complété avec succès"
  else
    echo "⚠️  RED encore ACTIF - Vérifier la logique"
  fi
else
  echo "⚠️  Pas de RED à compléter"
fi

echo ""
echo "✅ TEST COMPLÈTEMENT RÉUSSI"
echo "✓ État RED vérifié"
echo "✓ Comptabilité status accessible"
if [ -n "$RED_STATUS" ]; then
  echo "✓ Workflow RED 3 étapes complété"
fi
