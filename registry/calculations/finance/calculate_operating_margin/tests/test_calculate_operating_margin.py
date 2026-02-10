"""
Tests du sous-programme calculate_operating_margin

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateOperatingMargin:
    """Tests du sous-programme calculate_operating_margin"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "operating_income": 100.0,
            "revenue": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "operating_margin" in result
        assert "operating_margin_rate" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "operating_income": 100.0,
            "revenue": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "operating_income": "test",
            "revenue": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
