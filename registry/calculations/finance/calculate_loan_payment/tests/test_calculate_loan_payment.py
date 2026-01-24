"""
Tests du sous-programme calculate_loan_payment

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateLoanPayment:
    """Tests du sous-programme calculate_loan_payment"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "principal": 100.0,
            "annual_rate": 100.0,
            "months": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "monthly_payment" in result
        assert "total_interest" in result
        assert "total_amount" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "principal": 100.0,
            "annual_rate": 100.0,
            "months": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "principal": "test",
            "annual_rate": "test",
            "months": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
