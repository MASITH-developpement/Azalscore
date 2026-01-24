"""
Tests du sous-programme calculate_economic_order_quantity

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateEconomicOrderQuantity:
    """Tests du sous-programme calculate_economic_order_quantity"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "annual_demand": 100.0,
            "ordering_cost": 100.0,
            "holding_cost": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "eoq" in result
        assert "total_cost" in result
        assert "orders_per_year" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "annual_demand": 100.0,
            "ordering_cost": 100.0,
            "holding_cost": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "annual_demand": "test",
            "ordering_cost": "test",
            "holding_cost": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
