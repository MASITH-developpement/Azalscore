"""
Tests du sous-programme calculate_sales_growth_rate

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateSalesGrowthRate:
    """Tests du sous-programme calculate_sales_growth_rate"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "current_period_sales": 100.0,
            "previous_period_sales": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "growth_rate" in result
        assert "growth_percentage" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "current_period_sales": 100.0,
            "previous_period_sales": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "current_period_sales": "test",
            "previous_period_sales": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
