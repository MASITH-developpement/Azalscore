#!/bin/bash

# ==========================================
# AZALS - TESTS INTÉGRATION TRÉSORERIE
# ==========================================

# Configuration
API_URL="https://azalscore.onrender.com"
TOKEN=""  # À remplir après login
TENANT_ID="default"

echo "📋 GUIDE DE TEST - INTÉGRATION TRÉSORERIE"
echo "=========================================="
echo ""

# ==========================================
# ÉTAPE 1 : CONNEXION
# ==========================================

echo "1️⃣ CONNEXION"
echo "-------------"
echo "Commande:"
echo "curl -X POST $API_URL/auth/login \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -H 'X-Tenant-ID: $TENANT_ID' \\"
echo "  -d '{\"email\":\"test@example.com\",\"password\":\"test123\"}'"
echo ""
echo "➡️ Copier le access_token dans TOKEN ci-dessus"
echo ""

# ==========================================
# ÉTAPE 2 : TEST CAS NORMAL (🟢)
# ==========================================

echo "2️⃣ TEST CAS NORMAL (🟢)"
echo "------------------------"
echo "Solde : 50 000€ | Entrées : 10 000€ | Sorties : 5 000€"
echo "Prévision : 55 000€ | État : 🟢"
echo ""
echo "Commande:"
echo "curl -X POST $API_URL/treasury/forecast \\"
echo "  -H 'Authorization: Bearer \$TOKEN' \\"
echo "  -H 'X-Tenant-ID: $TENANT_ID' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"opening_balance\":50000,\"inflows\":10000,\"outflows\":5000}'"
echo ""
echo "✅ Résultat attendu:"
echo "   - Carte visible en zoneNormal"
echo "   - Statut 🟢"
echo "   - Solde actuel : 50 000 €"
echo "   - Prévision J+30 : 55 000 € (vert)"
echo "   - Pas de bouton 'Examiner la décision'"
echo ""
read -p "Appuyer sur Entrée pour continuer..."

# ==========================================
# ÉTAPE 3 : TEST CAS TENSION (🟠)
# ==========================================

echo ""
echo "3️⃣ TEST CAS TENSION (🟠)"
echo "-------------------------"
echo "Solde : 5 000€ | Entrées : 2 000€ | Sorties : 1 000€"
echo "Prévision : 6 000€ | État : 🟠"
echo ""
echo "Commande:"
echo "curl -X POST $API_URL/treasury/forecast \\"
echo "  -H 'Authorization: Bearer \$TOKEN' \\"
echo "  -H 'X-Tenant-ID: $TENANT_ID' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"opening_balance\":5000,\"inflows\":2000,\"outflows\":1000}'"
echo ""
echo "✅ Résultat attendu:"
echo "   - Carte visible en zoneTension"
echo "   - Statut 🟠"
echo "   - Solde actuel : 5 000 €"
echo "   - Prévision J+30 : 6 000 € (vert)"
echo "   - Bordure orange"
echo "   - Pas de bouton 'Examiner la décision'"
echo ""
read -p "Appuyer sur Entrée pour continuer..."

# ==========================================
# ÉTAPE 4 : TEST CAS CRITIQUE (🔴)
# ==========================================

echo ""
echo "4️⃣ TEST CAS CRITIQUE (🔴)"
echo "--------------------------"
echo "Solde : 5 000€ | Entrées : 2 000€ | Sorties : 10 000€"
echo "Prévision : -3 000€ | État : 🔴"
echo ""
echo "Commande:"
echo "curl -X POST $API_URL/treasury/forecast \\"
echo "  -H 'Authorization: Bearer \$TOKEN' \\"
echo "  -H 'X-Tenant-ID: $TENANT_ID' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"opening_balance\":5000,\"inflows\":2000,\"outflows\":10000}'"
echo ""
echo "✅ Résultat attendu:"
echo "   - UNIQUEMENT zoneCritical visible"
echo "   - Vue immersive (cockpit-critical-view)"
echo "   - Métrique principale : 3 000 € (déficit)"
echo "   - Détails : Solde 5 000€ | Entrées +2 000€ | Sorties -10 000€"
echo "   - Bouton '📊 Consulter le rapport RED'"
echo "   - Toutes les autres zones MASQUÉES"
echo "   - Message : 'Aucune autre information affichée'"
echo ""
read -p "Appuyer sur Entrée pour continuer..."

# ==========================================
# ÉTAPE 5 : VÉRIFIER GET /treasury/latest
# ==========================================

echo ""
echo "5️⃣ VÉRIFIER DERNIÈRE PRÉVISION"
echo "--------------------------------"
echo "Commande:"
echo "curl $API_URL/treasury/latest \\"
echo "  -H 'Authorization: Bearer \$TOKEN' \\"
echo "  -H 'X-Tenant-ID: $TENANT_ID'"
echo ""
echo "✅ Résultat attendu:"
echo "   - Retourne le dernier forecast créé"
echo "   - Structure JSON : id, opening_balance, inflows, outflows, forecast_balance, red_triggered, created_at"
echo "   - red_triggered = true si forecast_balance < 0"
echo ""
read -p "Appuyer sur Entrée pour continuer..."

# ==========================================
# ÉTAPE 6 : TEST ERREUR API INDISPONIBLE
# ==========================================

echo ""
echo "6️⃣ TEST ERREUR API INDISPONIBLE"
echo "---------------------------------"
echo "Actions:"
echo "1. Arrêter le backend (ou déconnecter la DB)"
echo "2. Rafraîchir le dashboard"
echo ""
echo "✅ Résultat attendu:"
echo "   - Carte visible en zoneNormal"
echo "   - Statut ⚪"
echo "   - card-error visible"
echo "   - Fond jaune (#fef3c7)"
echo "   - Message : '⚠️ Service indisponible'"
echo "   - Sous-message : 'L'API Trésorerie ne répond pas. Réessayez...'"
echo ""
read -p "Appuyer sur Entrée pour continuer..."

# ==========================================
# ÉTAPE 7 : TEST ACCÈS REFUSÉ
# ==========================================

echo ""
echo "7️⃣ TEST ACCÈS REFUSÉ"
echo "---------------------"
echo "Actions:"
echo "1. Utiliser un token invalide ou expiré"
echo "2. Rafraîchir le dashboard"
echo ""
echo "✅ Résultat attendu:"
echo "   - Redirection vers page de login (401)"
echo "   OU (si géré avant logout) :"
echo "   - Carte visible en zoneNormal"
echo "   - Statut ⚪"
echo "   - card-error visible"
echo "   - Fond rouge (#fee2e2)"
echo "   - Message : '🔒 Accès refusé'"
echo "   - Sous-message : 'Vous n'avez pas les droits...'"
echo ""
read -p "Appuyer sur Entrée pour continuer..."

# ==========================================
# ÉTAPE 8 : TEST AUCUNE DONNÉE
# ==========================================

echo ""
echo "8️⃣ TEST AUCUNE DONNÉE"
echo "----------------------"
echo "Actions:"
echo "1. Créer un nouveau tenant"
echo "2. Se connecter avec ce tenant"
echo "3. Accéder au dashboard (sans créer de forecast)"
echo ""
echo "✅ Résultat attendu:"
echo "   - Carte visible en zoneNormal"
echo "   - Statut 🟢"
echo "   - Valeurs : '—'"
echo "   - card-error visible"
echo "   - Message : 'Aucune donnée de trésorerie disponible'"
echo ""
read -p "Appuyer sur Entrée pour continuer..."

# ==========================================
# ÉTAPE 9 : TEST BULLE D'AIDE
# ==========================================

echo ""
echo "9️⃣ TEST BULLE D'AIDE"
echo "---------------------"
echo "Actions:"
echo "1. Survoler l'icône ⓘ à côté de 'Trésorerie'"
echo ""
echo "✅ Résultat attendu:"
echo "   - Bulle apparaît sous l'icône"
echo "   - Fond bleu nuit (#1a2332)"
echo "   - Texte blanc"
echo "   - Contenu : '🟢 Solde > 10 000€ • 🟠 Solde < 10 000€ • 🔴 Prévision négative. La prévision J+30 intègre les encaissements et décaissements prévus.'"
echo ""
read -p "Appuyer sur Entrée pour continuer..."

# ==========================================
# ÉTAPE 10 : TEST BOUTON RAPPORT RED
# ==========================================

echo ""
echo "🔟 TEST BOUTON RAPPORT RED"
echo "---------------------------"
echo "Prérequis : Avoir un forecast 🔴 (forecast_balance < 0)"
echo ""
echo "Actions:"
echo "1. Cliquer sur '📊 Consulter le rapport RED'"
echo ""
echo "✅ Résultat attendu:"
echo "   - Modal s'ouvre"
echo "   - Fond sombre avec overlay"
echo "   - Titre : '⚠ Alerte Trésorerie'"
echo "   - Déficit en rouge"
echo "   - Détails : Solde, Prévision, Entrées, Sorties"
echo "   - Liste options de financement"
echo "   - Boutons : 'Contacter un expert' + 'Fermer'"
echo ""

# ==========================================
# RÉSUMÉ FINAL
# ==========================================

echo ""
echo "=========================================="
echo "✅ CHECKLIST VALIDATION COMPLÈTE"
echo "=========================================="
echo ""
echo "[ ] 1. Cas 🟢 : Carte en zoneNormal"
echo "[ ] 2. Cas 🟠 : Carte en zoneTension"
echo "[ ] 3. Cas 🔴 : Vue exclusive en zoneCritical"
echo "[ ] 4. Pattern 🔴 : Toutes zones masquées sauf critical"
echo "[ ] 5. GET /treasury/latest fonctionne"
echo "[ ] 6. Erreur API indisponible affichée (fond jaune)"
echo "[ ] 7. Erreur accès refusé gérée"
echo "[ ] 8. Aucune donnée : message clair"
echo "[ ] 9. Bulle d'aide fonctionnelle"
echo "[ ] 10. Bouton rapport RED ouvre modal"
echo "[ ] 11. Design intact (0 modification styles.css)"
echo "[ ] 12. Données réelles affichées correctement"
echo ""
echo "=========================================="
echo "🎯 FIN DES TESTS"
echo "=========================================="
