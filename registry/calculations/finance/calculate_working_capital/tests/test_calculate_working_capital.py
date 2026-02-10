"""
Tests du sous-programme calculate_working_capital

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateWorkingCapital:
    """Tests du sous-programme calculate_working_capital"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "current_assets": 100.0,
            "current_liabilities": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "working_capital" in result
        assert "wc_days" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "current_assets": 100.0,
            "current_liabilities": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "current_assets": "test",
            "current_liabilities": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
