#!/bin/bash
# Script de déploiement AZALS sur Fly.io

echo "🚀 Déploiement AZALS sur Fly.io..."

# Vérifier que flyctl est installé
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl n'est pas installé"
    echo "📦 Installation de flyctl..."
    curl -L https://fly.io/install.sh | sh
    export PATH="$HOME/.fly/bin:$PATH"
fi

# Déployer
echo "📤 Déploiement en cours..."
flyctl deploy --remote-only --app azalscore-wlm15q

echo "✅ Déploiement terminé!"
echo "🌐 Application disponible sur: https://azalscore-wlm15q.fly.dev"
