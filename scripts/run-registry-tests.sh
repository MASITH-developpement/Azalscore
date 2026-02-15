#!/bin/bash
#
# AZALSCORE - Run All Registry Tests
#
# Ce script execute tous les tests du registry (validators + transformers)
# individuellement pour eviter les conflits d'import pytest.
#
# Usage: ./scripts/run-registry-tests.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"
source venv/bin/activate

echo "============================================"
echo " AZALSCORE - Registry Tests"
echo "============================================"
echo ""

# Compteurs
validator_pass=0
validator_fail=0
transformer_pass=0
transformer_fail=0

# Test des validators
echo "[1/2] Testing validators..."
for f in $(find registry/validators -name "test_*.py" 2>/dev/null); do
  if python -m pytest "$f" -q --tb=no 2>/dev/null; then
    ((validator_pass++))
  else
    ((validator_fail++))
    echo "  FAIL: $f"
  fi
done
echo "  Validators: $validator_pass passed, $validator_fail failed"
echo ""

# Test des transformers
echo "[2/2] Testing transformers..."
for f in $(find registry/transformers -name "test_*.py" 2>/dev/null); do
  if python -m pytest "$f" -q --tb=no 2>/dev/null; then
    ((transformer_pass++))
  else
    ((transformer_fail++))
    echo "  FAIL: $f"
  fi
done
echo "  Transformers: $transformer_pass passed, $transformer_fail failed"
echo ""

# Resume
total_pass=$((validator_pass + transformer_pass))
total_fail=$((validator_fail + transformer_fail))

echo "============================================"
echo " RESULTS"
echo "============================================"
echo " Validators:   $validator_pass passed, $validator_fail failed"
echo " Transformers: $transformer_pass passed, $transformer_fail failed"
echo " TOTAL:        $total_pass passed, $total_fail failed"
echo "============================================"

if [ $total_fail -gt 0 ]; then
  exit 1
fi
