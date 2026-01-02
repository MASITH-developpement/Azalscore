#!/usr/bin/env bash
# Render build script
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Appliquer les migrations SQL automatiquement
echo "🔄 Application des migrations SQL..."
python3 run_migrations.py || echo "⚠️ Migrations déjà appliquées ou erreur non bloquante"
