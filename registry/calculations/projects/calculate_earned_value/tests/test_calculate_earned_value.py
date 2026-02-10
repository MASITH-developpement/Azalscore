"""
Tests du sous-programme calculate_earned_value

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateEarnedValue:
    """Tests du sous-programme calculate_earned_value"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "planned_value": 100.0,
            "earned_value": 100.0,
            "actual_cost": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "cost_variance" in result
        assert "schedule_variance" in result
        assert "cpi" in result
        assert "spi" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "planned_value": 100.0,
            "earned_value": 100.0,
            "actual_cost": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "planned_value": "test",
            "earned_value": "test",
            "actual_cost": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
