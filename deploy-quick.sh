#!/bin/bash
# AZALS - Deploiement rapide
# Usage: ./deploy-quick.sh [api|frontend|all]

set -e

TARGET=${1:-all}

echo "=== AZALS Quick Deploy ==="

if [[ "$TARGET" == "api" || "$TARGET" == "all" ]]; then
    echo "[1/2] Redemarrage API..."
    docker restart azals_api
    echo "     Attente API healthy..."
    sleep 10
    until docker ps --filter "name=azals_api" --format "{{.Status}}" | grep -q "healthy"; do
        sleep 2
    done
    echo "     API OK"
fi

if [[ "$TARGET" == "frontend" || "$TARGET" == "all" ]]; then
    echo "[2/2] Rebuild Frontend..."
    cd /home/ubuntu/azalscore/frontend
    npm run build --silent
    docker cp dist/. azals_frontend:/usr/share/nginx/html/
    docker restart azals_frontend
    echo "     Frontend OK"
fi

echo ""
echo "=== Deploiement termine ==="
