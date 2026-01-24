"""
Tests du sous-programme calculate_straight_line_depreciation

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateStraightLineDepreciation:
    """Tests du sous-programme calculate_straight_line_depreciation"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "asset_cost": 100.0,
            "salvage_value": 100.0,
            "useful_life_years": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "annual_depreciation" in result
        assert "monthly_depreciation" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "asset_cost": 100.0,
            "salvage_value": 100.0,
            "useful_life_years": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "asset_cost": "test",
            "salvage_value": "test",
            "useful_life_years": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
