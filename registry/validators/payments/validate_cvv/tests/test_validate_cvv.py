"""
Tests du sous-programme validate_cvv

Couverture cible : >= 80%
"""

import pytest
from registry.validators.payments.validate_cvv.impl import execute


class TestValidateCvv:
    """Tests du sous-programme validate_cvv"""

    def test_valid_3_digit_cvv(self):
        """Test CVV 3 chiffres valide"""
        result = execute({"cvv": "123"})
        assert result["is_valid"] is True

    def test_valid_4_digit_cvv(self):
        """Test CVV 4 chiffres valide (Amex)"""
        result = execute({"cvv": "1234"})
        assert result["is_valid"] is True

    def test_valid_cvv_with_card_type_visa(self):
        """Test CVV avec type de carte Visa (3 chiffres)"""
        result = execute({"cvv": "123", "card_type": "visa"})
        assert result["is_valid"] is True

    def test_valid_cvv_with_card_type_amex(self):
        """Test CVV avec type de carte Amex (4 chiffres)"""
        result = execute({"cvv": "1234", "card_type": "amex"})
        assert result["is_valid"] is True

    def test_invalid_amex_cvv_3_digits(self):
        """Test CVV Amex invalide (3 chiffres au lieu de 4)"""
        result = execute({"cvv": "123", "card_type": "amex"})
        assert result["is_valid"] is False

    def test_invalid_visa_cvv_4_digits(self):
        """Test CVV Visa invalide (4 chiffres au lieu de 3)"""
        result = execute({"cvv": "1234", "card_type": "visa"})
        assert result["is_valid"] is False

    def test_empty_cvv(self):
        """Test CVV vide"""
        result = execute({"cvv": ""})
        assert result["is_valid"] is False
        assert "error" in result

    def test_non_numeric_cvv(self):
        """Test CVV avec caractères non numériques"""
        result = execute({"cvv": "12A"})
        assert result["is_valid"] is False

    def test_cvv_too_short(self):
        """Test CVV trop court"""
        result = execute({"cvv": "12"})
        assert result["is_valid"] is False

    def test_cvv_too_long(self):
        """Test CVV trop long"""
        result = execute({"cvv": "12345"})
        assert result["is_valid"] is False

    def test_cvv_with_spaces(self):
        """Test CVV avec espaces (doit être nettoyé)"""
        result = execute({"cvv": " 123 "})
        assert result["is_valid"] is True

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {"cvv": "123"}

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {"cvv": "123"}
        inputs_copy = inputs.copy()

        execute(inputs)

        assert inputs == inputs_copy
