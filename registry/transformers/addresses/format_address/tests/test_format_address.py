"""
Tests du sous-programme format_address

Couverture cible : >= 80%
"""

import pytest
from registry.transformers.addresses.format_address.impl import execute


class TestFormatAddress:
    """Tests du sous-programme format_address"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "street": "test_value",
            "postal_code": "test_value",
            "city": "test_value",
            "country": "test_value",
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "formatted_address" in result
        assert "one_line" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {
            "street": "test_value",
            "postal_code": "test_value",
            "city": "test_value",
            "country": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {
            "street": "test",
            "postal_code": "test",
            "city": "test",
            "country": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
