"""
Tests du sous-programme calculate_margin

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateMargin:
    """Tests du calcul de marge"""

    def test_margin_positive(self):
        """Test avec marge positive"""
        result = execute({
            "price": 1000.0,
            "cost": 800.0
        })

        assert result["margin"] == 200.0
        assert result["margin_rate"] == 0.2
        assert result["margin_percentage"] == 20.0

    def test_margin_negative(self):
        """Test avec marge négative (perte)"""
        result = execute({
            "price": 800.0,
            "cost": 1000.0
        })

        assert result["margin"] == -200.0
        assert result["margin_rate"] == -0.25
        assert result["margin_percentage"] == -25.0

    def test_margin_zero(self):
        """Test avec marge nulle (prix = coût)"""
        result = execute({
            "price": 1000.0,
            "cost": 1000.0
        })

        assert result["margin"] == 0.0
        assert result["margin_rate"] == 0.0
        assert result["margin_percentage"] == 0.0

    def test_price_zero(self):
        """Test avec prix nul (cas limite)"""
        result = execute({
            "price": 0.0,
            "cost": 100.0
        })

        assert result["margin"] == -100.0
        assert result["margin_rate"] == 0.0  # Division par zéro évitée
        assert result["margin_percentage"] == 0.0

    def test_cost_zero(self):
        """Test avec coût nul (marge = 100%)"""
        result = execute({
            "price": 1000.0,
            "cost": 0.0
        })

        assert result["margin"] == 1000.0
        assert result["margin_rate"] == 1.0
        assert result["margin_percentage"] == 100.0

    def test_decimal_precision(self):
        """Test de la précision des décimales"""
        result = execute({
            "price": 123.456,
            "cost": 78.912
        })

        # Vérification arrondi à 2 décimales pour margin
        assert result["margin"] == 44.54
        # Vérification arrondi à 4 décimales pour margin_rate
        assert result["margin_rate"] == 0.3608
        # Vérification arrondi à 2 décimales pour margin_percentage
        assert result["margin_percentage"] == 36.08

    def test_large_numbers(self):
        """Test avec de grands nombres"""
        result = execute({
            "price": 1_000_000.0,
            "cost": 750_000.0
        })

        assert result["margin"] == 250_000.0
        assert result["margin_rate"] == 0.25
        assert result["margin_percentage"] == 25.0

    def test_small_numbers(self):
        """Test avec de petits nombres"""
        result = execute({
            "price": 0.50,
            "cost": 0.30
        })

        assert result["margin"] == 0.20
        assert result["margin_rate"] == 0.4
        assert result["margin_percentage"] == 40.0

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {"price": 1000.0, "cost": 800.0}

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects(self):
        """Test absence d'effets de bord"""
        inputs = {"price": 1000.0, "cost": 800.0}
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
