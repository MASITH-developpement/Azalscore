#!/bin/bash
set -e

echo "🚀 Démarrage complet Azalscore ERP + Site Web"
echo "=============================================="

command -v docker >/dev/null 2>&1 || { echo "❌ Docker non installé"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js non installé"; exit 1; }

echo "📦 Démarrage du backend..."
docker-compose up -d postgres api

echo "⏳ Attente de l'API..."
sleep 5

echo "🔄 Exécution des migrations..."
docker-compose exec -T api alembic upgrade head || echo "⚠️ Migrations déjà à jour"

echo "🎨 Démarrage du frontend..."
cd frontend
npm install --silent 2>/dev/null || npm install
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Azalscore démarré avec succès !"
echo "========================================"
echo "🌐 Site Web:      http://localhost:5173"
echo "🔧 API:           http://localhost:80"
echo "📚 Documentation: http://localhost:80/api/v2/auth/docs"
echo "========================================"
echo "Appuyez sur Ctrl+C pour arrêter"

trap "kill $FRONTEND_PID 2>/dev/null; docker-compose down" EXIT

wait
