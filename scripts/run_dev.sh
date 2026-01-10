#!/bin/bash
set -e

# ========================================
# AZALS - MODE DEVELOPPEMENT
# BASE UUID VALIDÉE
# ========================================

export AZALS_ENV=dev
export DB_STRICT_UUID=true

echo "========================================"
echo "AZALS DEV MODE"
echo "UUID STRICT MODE : ENABLED"
echo "========================================"

uvicorn app.main:app --host 0.0.0.0 --port 8000
