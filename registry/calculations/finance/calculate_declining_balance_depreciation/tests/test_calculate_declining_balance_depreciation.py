"""
Tests du sous-programme calculate_declining_balance_depreciation

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateDecliningBalanceDepreciation:
    """Tests du sous-programme calculate_declining_balance_depreciation"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "asset_cost": 100.0,
            "rate": 100.0,
            "years_elapsed": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "current_year_depreciation" in result
        assert "accumulated_depreciation" in result
        assert "book_value" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "asset_cost": 100.0,
            "rate": 100.0,
            "years_elapsed": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "asset_cost": "test",
            "rate": "test",
            "years_elapsed": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
