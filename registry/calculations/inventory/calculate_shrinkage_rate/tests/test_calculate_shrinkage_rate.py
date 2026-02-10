"""
Tests du sous-programme calculate_shrinkage_rate

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateShrinkageRate:
    """Tests du sous-programme calculate_shrinkage_rate"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "beginning_inventory": 100.0,
            "purchases": 100.0,
            "sales": 100.0,
            "ending_inventory": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "shrinkage" in result
        assert "shrinkage_rate" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "beginning_inventory": 100.0,
            "purchases": 100.0,
            "sales": 100.0,
            "ending_inventory": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "beginning_inventory": "test",
            "purchases": "test",
            "sales": "test",
            "ending_inventory": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
