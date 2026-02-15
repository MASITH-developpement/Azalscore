"""
Tests du sous-programme validate_barcode

Couverture cible : >= 80%
"""

import pytest
from registry.validators.inventory.validate_barcode.impl import execute


class TestValidateBarcode:
    """Tests du sous-programme validate_barcode"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "barcode": "test_value",
            "type": "test_value",
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "is_valid" in result
        assert "normalized_barcode" in result
        assert "checksum" in result
        assert "error" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {
            "barcode": "test_value",
            "type": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {
            "barcode": "test",
            "type": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
