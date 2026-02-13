"""
Tests du sous-programme validate_discount_rate

Couverture cible : >= 80%
"""

import pytest
from registry.validators.data.validate_discount_rate.impl import execute


class TestValidateDiscountRate:
    """Tests du sous-programme validate_discount_rate"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "discount_rate": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "is_valid" in result
        assert "error" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {
            "discount_rate": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {
            "discount_rate": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
