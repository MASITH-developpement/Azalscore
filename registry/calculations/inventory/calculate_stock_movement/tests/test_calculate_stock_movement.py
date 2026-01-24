"""
Tests du sous-programme calculate_stock_movement

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateStockMovement:
    """Tests du sous-programme calculate_stock_movement"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "initial_stock": 100.0,
            "entries": [],
            "exits": [],
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "final_stock" in result
        assert "total_entries" in result
        assert "total_exits" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "initial_stock": 100.0,
            "entries": "test_value",
            "exits": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "initial_stock": "test",
            "entries": "test",
            "exits": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
