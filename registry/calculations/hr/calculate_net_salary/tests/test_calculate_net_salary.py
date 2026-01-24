"""
Tests du sous-programme calculate_net_salary

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateNetSalary:
    """Tests du sous-programme calculate_net_salary"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "gross_salary": 100.0,
            "social_charges": [],
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "net_salary" in result
        assert "total_deductions" in result
        assert "deduction_breakdown" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "gross_salary": 100.0,
            "social_charges": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "gross_salary": "test",
            "social_charges": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
