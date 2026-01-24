"""
Tests du sous-programme calculate_burn_rate

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateBurnRate:
    """Tests du sous-programme calculate_burn_rate"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "total_budget": 100.0,
            "spent_to_date": 100.0,
            "days_elapsed": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "daily_burn_rate" in result
        assert "projected_completion_date" in result
        assert "budget_risk" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "total_budget": 100.0,
            "spent_to_date": 100.0,
            "days_elapsed": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "total_budget": "test",
            "spent_to_date": "test",
            "days_elapsed": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
