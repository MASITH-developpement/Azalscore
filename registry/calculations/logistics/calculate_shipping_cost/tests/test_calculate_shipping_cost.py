"""
Tests du sous-programme calculate_shipping_cost

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateShippingCost:
    """Tests du sous-programme calculate_shipping_cost"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "weight_kg": 100.0,
            "distance_km": 100.0,
            "shipping_method": "test_value",
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "shipping_cost" in result
        assert "estimated_days" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "weight_kg": 100.0,
            "distance_km": 100.0,
            "shipping_method": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "weight_kg": "test",
            "distance_km": "test",
            "shipping_method": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
