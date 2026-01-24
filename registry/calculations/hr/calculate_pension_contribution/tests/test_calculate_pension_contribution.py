"""
Tests du sous-programme calculate_pension_contribution

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculatePensionContribution:
    """Tests du sous-programme calculate_pension_contribution"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "gross_salary": 100.0,
            "contribution_rate": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "employee_contribution" in result
        assert "employer_contribution" in result
        assert "total_contribution" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "gross_salary": 100.0,
            "contribution_rate": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "gross_salary": "test",
            "contribution_rate": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
