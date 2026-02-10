"""
Tests du sous-programme calculate_training_cost

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateTrainingCost:
    """Tests du sous-programme calculate_training_cost"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "training_fees": 100.0,
            "employee_hours": 100.0,
            "hourly_rate": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "total_cost" in result
        assert "direct_cost" in result
        assert "indirect_cost" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "training_fees": 100.0,
            "employee_hours": 100.0,
            "hourly_rate": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "training_fees": "test",
            "employee_hours": "test",
            "hourly_rate": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
