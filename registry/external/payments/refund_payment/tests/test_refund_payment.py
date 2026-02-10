"""
Tests du sous-programme refund_payment

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestRefundPayment:
    """Tests du sous-programme refund_payment"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "payment_intent_id": "test_value",
            "amount": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "refund_id" in result
        assert "status" in result
        assert "amount_refunded" in result
        assert "error" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "payment_intent_id": "test_value",
            "amount": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "payment_intent_id": "test",
            "amount": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
