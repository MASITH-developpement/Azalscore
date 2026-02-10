"""
Tests du sous-programme calculate_overtime_pay

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateOvertimePay:
    """Tests du sous-programme calculate_overtime_pay"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "hourly_rate": 100.0,
            "overtime_hours": 100.0,
            "overtime_rate": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "overtime_amount" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "hourly_rate": 100.0,
            "overtime_hours": 100.0,
            "overtime_rate": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "hourly_rate": "test",
            "overtime_hours": "test",
            "overtime_rate": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
