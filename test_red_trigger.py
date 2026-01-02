#!/usr/bin/env python3
"""
Script de test pour déclencher un point rouge 🔴 sur la trésorerie
Crée une prévision avec forecast_balance négatif
"""

import requests
import json

# Configuration
BASE_URL = "https://azalscore.onrender.com"
TENANT_ID = "tenant-demo"
EMAIL = "user@demo.com"
PASSWORD = "demo123"

def main():
    print("🔴 Test déclenchement RED - Trésorerie")
    print("=" * 50)
    
    # 1. Connexion
    print("\n1. Connexion...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        headers={"X-Tenant-ID": TENANT_ID, "Content-Type": "application/json"},
        json={"email": EMAIL, "password": PASSWORD}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Erreur connexion: {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json()["access_token"]
    print(f"✅ Connecté - Token: {token[:20]}...")
    
    # 2. Créer une prévision en DEFICIT (red_triggered)
    print("\n2. Création prévision en DEFICIT...")
    headers = {
        "X-Tenant-ID": TENANT_ID,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Scénario 🔴: Déficit anticipé
    forecast_data = {
        "opening_balance": 5000.0,      # Solde actuel: 5 000€
        "inflows": 2000.0,              # Entrées prévues: 2 000€
        "outflows": 15000.0             # Sorties prévues: 15 000€
    }
    # forecast_balance = 5000 + 2000 - 15000 = -8000€ → 🔴 RED
    
    forecast_response = requests.post(
        f"{BASE_URL}/treasury/forecast",
        headers=headers,
        json=forecast_data
    )
    
    if forecast_response.status_code != 200:
        print(f"❌ Erreur création prévision: {forecast_response.status_code}")
        print(forecast_response.text)
        return
    
    result = forecast_response.json()
    print(f"✅ Prévision créée - ID: {result['id']}")
    print(f"   Solde actuel: {result['opening_balance']}€")
    print(f"   Entrées: +{result['inflows']}€")
    print(f"   Sorties: -{result['outflows']}€")
    print(f"   Prévision J+30: {result['forecast_balance']}€")
    print(f"   RED déclenché: {result['red_triggered']}")
    
    if result['red_triggered']:
        print("\n🔴 ALERTE ROUGE DÉCLENCHÉE")
        print("   → Le cockpit doit afficher UNIQUEMENT la trésorerie")
        print("   → Bouton 'Consulter le rapport RED' visible")
        print("   → Workflow de validation en 3 étapes activé")
    else:
        print("\n⚠️  RED non déclenché - forecast_balance positif")
    
    # 3. Vérifier la récupération
    print("\n3. Vérification GET /treasury/latest...")
    latest_response = requests.get(
        f"{BASE_URL}/treasury/latest",
        headers=headers
    )
    
    if latest_response.status_code == 200:
        latest = latest_response.json()
        print(f"✅ Données récupérées")
        print(f"   Status: {'🔴' if latest['red_triggered'] else '🟢'}")
        print(f"   Balance: {latest['forecast_balance']}€")
    else:
        print(f"❌ Erreur: {latest_response.status_code}")
    
    print("\n" + "=" * 50)
    print("Test terminé !")
    print(f"\n👉 Accédez au cockpit: {BASE_URL}/dashboard")
    print(f"👉 Page trésorerie: {BASE_URL}/treasury")

if __name__ == "__main__":
    main()
