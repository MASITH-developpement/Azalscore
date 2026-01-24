"""
Tests du sous-programme calculate_demand_forecast

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateDemandForecast:
    """Tests du sous-programme calculate_demand_forecast"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "historical_sales": [],
            "periods_ahead": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "forecast" in result
        assert "method" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "historical_sales": "test_value",
            "periods_ahead": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "historical_sales": "test",
            "periods_ahead": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
