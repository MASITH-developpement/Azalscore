"""
Tests du sous-programme calculate_project_cost

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateProjectCost:
    """Tests du sous-programme calculate_project_cost"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "tasks": [],
            "resources": [],
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "total_cost" in result
        assert "labor_cost" in result
        assert "material_cost" in result
        assert "overhead_cost" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "tasks": "test_value",
            "resources": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "tasks": "test",
            "resources": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
