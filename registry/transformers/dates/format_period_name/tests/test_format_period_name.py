"""
Tests du sous-programme format_period_name

Couverture cible : >= 80%
"""

import pytest
from registry.transformers.dates.format_period_name.impl import execute


class TestFormatPeriodName:
    """Tests du sous-programme format_period_name"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "date": "test_value",
            "period_number": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "period_name" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {
            "date": "test_value",
            "period_number": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {
            "date": "test",
            "period_number": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
