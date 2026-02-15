"""
Tests du sous-programme convert_currency

Couverture cible : >= 80%
"""

import pytest
from registry.transformers.numbers.convert_currency.impl import execute


class TestConvertCurrency:
    """Tests du sous-programme convert_currency"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "amount": 100.0,
            "from_currency": "test_value",
            "to_currency": "test_value",
            "exchange_rate": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "converted_amount" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {
            "amount": 100.0,
            "from_currency": "test_value",
            "to_currency": "test_value",
            "exchange_rate": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {
            "amount": "test",
            "from_currency": "test",
            "to_currency": "test",
            "exchange_rate": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
