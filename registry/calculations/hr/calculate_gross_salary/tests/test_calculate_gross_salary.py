"""
Tests du sous-programme calculate_gross_salary

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateGrossSalary:
    """Tests du sous-programme calculate_gross_salary"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "base_salary": 100.0,
            "hours_worked": 100.0,
            "overtime_hours": 100.0,
            "bonuses": [],
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "gross_salary" in result
        assert "base_amount" in result
        assert "overtime_amount" in result
        assert "bonus_amount" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "base_salary": 100.0,
            "hours_worked": 100.0,
            "overtime_hours": 100.0,
            "bonuses": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "base_salary": "test",
            "hours_worked": "test",
            "overtime_hours": "test",
            "bonuses": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
