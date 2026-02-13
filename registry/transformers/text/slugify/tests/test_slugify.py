"""
Tests du sous-programme slugify

Couverture cible : >= 80%
"""

import pytest
from registry.transformers.text.slugify.impl import execute, validate_inputs


class TestSlugify:
    """Tests du sous-programme slugify"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        inputs = {"value": "test_value"}
        result = execute(inputs)

        assert result is not None
        assert isinstance(result, dict)
        assert "slug" in result
        assert result["slug"] == "test-value"

    def test_french_accents(self):
        """Test conversion des accents français"""
        inputs = {"value": "ERP Décisionnel PME"}
        result = execute(inputs)

        assert result["slug"] == "erp-decisionnel-pme"
        assert result["was_truncated"] is False

    def test_apostrophe_handling(self):
        """Test gestion des apostrophes"""
        inputs = {"value": "L'année 2026 sera décisive"}
        result = execute(inputs)

        assert "lannee" in result["slug"]
        assert "2026" in result["slug"]
        assert "'" not in result["slug"]

    def test_special_characters(self):
        """Test suppression caractères spéciaux"""
        inputs = {"value": "Cockpit BI: 10 KPIs Essentiels!"}
        result = execute(inputs)

        assert result["slug"] == "cockpit-bi-10-kpis-essentiels"
        assert ":" not in result["slug"]
        assert "!" not in result["slug"]

    def test_truncation(self):
        """Test troncature à la longueur max"""
        inputs = {
            "value": "Un titre très très très long qui dépasse la limite de caractères autorisée",
            "max_length": 30
        }
        result = execute(inputs)

        assert result["was_truncated"] is True
        assert len(result["slug"]) <= 30
        # Doit couper au dernier tiret pour ne pas avoir de mot coupé
        assert not result["slug"].endswith("-")

    def test_custom_separator(self):
        """Test avec séparateur personnalisé"""
        inputs = {"value": "Test avec underscore", "separator": "_"}
        result = execute(inputs)

        assert result["slug"] == "test_avec_underscore"

    def test_empty_value(self):
        """Test valeur vide"""
        inputs = {"value": ""}
        result = execute(inputs)

        assert result["slug"] == ""
        assert result["original_length"] == 0
        assert result["was_truncated"] is False

    def test_none_value(self):
        """Test valeur None"""
        inputs = {"value": None}
        result = execute(inputs)

        assert result["slug"] == ""

    def test_multiple_spaces(self):
        """Test espaces multiples"""
        inputs = {"value": "Test   avec   plusieurs   espaces"}
        result = execute(inputs)

        assert "--" not in result["slug"]
        assert result["slug"] == "test-avec-plusieurs-espaces"

    def test_leading_trailing_spaces(self):
        """Test espaces début/fin"""
        inputs = {"value": "  Test  "}
        result = execute(inputs)

        assert result["slug"] == "test"
        assert not result["slug"].startswith("-")
        assert not result["slug"].endswith("-")

    def test_numbers(self):
        """Test conservation des chiffres"""
        inputs = {"value": "Version 2.0 - Release 2026"}
        result = execute(inputs)

        assert "2" in result["slug"]
        assert "2026" in result["slug"]

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {"value": "Test d'idempotence français"}

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {"value": "test", "max_length": 50}
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy


class TestValidateInputs:
    """Tests de validation des inputs"""

    def test_valid_inputs(self):
        """Test inputs valides"""
        inputs = {"value": "test"}
        result = validate_inputs(inputs)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_missing_value(self):
        """Test champ value manquant"""
        inputs = {}
        result = validate_inputs(inputs)

        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_invalid_max_length(self):
        """Test max_length invalide"""
        inputs = {"value": "test", "max_length": -1}
        result = validate_inputs(inputs)

        assert result["valid"] is False

    def test_invalid_separator(self):
        """Test separator invalide"""
        inputs = {"value": "test", "separator": "--"}
        result = validate_inputs(inputs)

        assert result["valid"] is False
