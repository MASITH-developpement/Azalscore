"""
Tests du sous-programme validate_credit_card

Couverture cible : >= 80%
"""

import pytest
from registry.validators.payments.validate_credit_card.impl import execute


class TestValidateCreditCard:
    """Tests du sous-programme validate_credit_card"""

    def test_valid_visa_card(self):
        """Test carte Visa valide"""
        result = execute({"card_number": "4111111111111111"})
        assert result["is_valid"] is True
        assert result["card_type"] == "visa"
        assert result["masked_number"] == "************1111"

    def test_valid_mastercard(self):
        """Test carte Mastercard valide"""
        result = execute({"card_number": "5500000000000004"})
        assert result["is_valid"] is True
        assert result["card_type"] == "mastercard"

    def test_valid_amex(self):
        """Test carte American Express valide"""
        result = execute({"card_number": "378282246310005"})
        assert result["is_valid"] is True
        assert result["card_type"] == "amex"

    def test_valid_discover(self):
        """Test carte Discover valide"""
        result = execute({"card_number": "6011111111111117"})
        assert result["is_valid"] is True
        assert result["card_type"] == "discover"

    def test_invalid_luhn(self):
        """Test numéro échouant la validation Luhn"""
        result = execute({"card_number": "4111111111111112"})
        assert result["is_valid"] is False

    def test_card_with_spaces(self):
        """Test carte avec espaces (format courant)"""
        result = execute({"card_number": "4111 1111 1111 1111"})
        assert result["is_valid"] is True
        assert result["card_type"] == "visa"

    def test_card_with_dashes(self):
        """Test carte avec tirets"""
        result = execute({"card_number": "4111-1111-1111-1111"})
        assert result["is_valid"] is True

    def test_empty_card_number(self):
        """Test numéro de carte vide"""
        result = execute({"card_number": ""})
        assert result["is_valid"] is False
        assert "error" in result

    def test_non_numeric_card(self):
        """Test numéro avec caractères non numériques"""
        result = execute({"card_number": "4111-XXXX-1111-1111"})
        assert result["is_valid"] is False

    def test_too_short_card(self):
        """Test numéro trop court"""
        result = execute({"card_number": "411111111111"})
        assert result["is_valid"] is False

    def test_too_long_card(self):
        """Test numéro trop long"""
        result = execute({"card_number": "41111111111111111111"})
        assert result["is_valid"] is False

    def test_masked_number_security(self):
        """Test que le numéro masqué ne révèle pas tout"""
        result = execute({"card_number": "4111111111111111"})
        # Seuls les 4 derniers chiffres doivent être visibles
        assert "4111" not in result["masked_number"][:12]
        assert result["masked_number"].endswith("1111")

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {"card_number": "4111111111111111"}

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {"card_number": "4111111111111111"}
        inputs_copy = inputs.copy()

        execute(inputs)

        assert inputs == inputs_copy
