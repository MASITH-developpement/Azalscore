"""
Tests du sous-programme calculate_unit_cost

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateUnitCost:
    """Tests du sous-programme calculate_unit_cost"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "material_cost": 100.0,
            "labor_cost": 100.0,
            "overhead_cost": 100.0,
            "quantity": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "unit_cost" in result
        assert "breakdown" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "material_cost": 100.0,
            "labor_cost": 100.0,
            "overhead_cost": 100.0,
            "quantity": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "material_cost": "test",
            "labor_cost": "test",
            "overhead_cost": "test",
            "quantity": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
