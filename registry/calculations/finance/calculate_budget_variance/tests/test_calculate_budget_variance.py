"""
Tests du sous-programme calculate_budget_variance

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateBudgetVariance:
    """Tests du sous-programme calculate_budget_variance"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "budgeted_amount": 100.0,
            "actual_amount": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "variance" in result
        assert "variance_percentage" in result
        assert "is_favorable" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "budgeted_amount": 100.0,
            "actual_amount": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "budgeted_amount": "test",
            "actual_amount": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
