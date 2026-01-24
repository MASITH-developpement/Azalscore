"""
Tests du Registry AZALSCORE

Vérifie le chargement et la validation des sous-programmes
"""

import pytest
from pathlib import Path

from app.registry.loader import (
    RegistryLoader,
    load_program,
    list_programs,
    ManifestValidationError,
    ProgramNotFoundError
)


class TestRegistryLoader:
    """Tests du loader du registry"""

    def test_registry_scan(self):
        """Test du scan du registry"""
        loader = RegistryLoader()

        # Le registry doit contenir au moins les sous-programmes créés
        programs = list_programs()

        # On devrait avoir au moins 4 sous-programmes
        assert len(programs) >= 4, f"Expected at least 4 programs, got {len(programs)}"

        # Vérifier que nos sous-programmes sont présents
        program_ids = [p["id"] for p in programs]

        expected_programs = [
            "azalscore.finance.calculate_margin",
            "azalscore.validation.validate_iban",
            "azalscore.computation.calculate_vat",
            "azalscore.notification.send_alert"
        ]

        for expected in expected_programs:
            assert any(expected in pid for pid in program_ids), \
                f"Program {expected} not found in registry"

    def test_load_calculate_margin(self):
        """Test du chargement du sous-programme calculate_margin"""
        program = load_program("azalscore.finance.calculate_margin")

        assert program is not None
        assert program.program_id == "azalscore.finance.calculate_margin"
        assert program.version == "1.0.0"
        assert program.category == "finance"
        assert program.is_idempotent is True
        assert program.has_side_effects is False
        assert program.is_no_code_compatible is True

    def test_execute_calculate_margin(self):
        """Test de l'exécution de calculate_margin"""
        program = load_program("azalscore.finance.calculate_margin")

        result = program.execute({
            "price": 1000.0,
            "cost": 800.0
        })

        assert result["margin"] == 200.0
        assert result["margin_rate"] == 0.2
        assert result["margin_percentage"] == 20.0

    def test_execute_validate_iban_valid(self):
        """Test de validation d'un IBAN valide"""
        program = load_program("azalscore.validation.validate_iban")

        # IBAN français valide
        result = program.execute({
            "iban": "FR14 2004 1010 0505 0001 3M02 606"
        })

        assert result["is_valid"] is True
        assert result["country_code"] == "FR"
        assert result["error"] is None
        assert "FR1420041010050500013M02606" in result["normalized_iban"]

    def test_execute_validate_iban_invalid(self):
        """Test de validation d'un IBAN invalide"""
        program = load_program("azalscore.validation.validate_iban")

        result = program.execute({
            "iban": "FR00 0000 0000 0000 0000 0000 000"
        })

        assert result["is_valid"] is False
        assert result["error"] is not None

    def test_execute_calculate_vat(self):
        """Test du calcul de TVA"""
        program = load_program("azalscore.computation.calculate_vat")

        result = program.execute({
            "amount_ht": 1000.0,
            "vat_rate": 0.20
        })

        assert result["amount_ht"] == 1000.0
        assert result["vat_amount"] == 200.0
        assert result["amount_ttc"] == 1200.0
        assert result["vat_rate_percentage"] == 20.0

    def test_program_not_found(self):
        """Test d'erreur pour un sous-programme inexistant"""
        with pytest.raises(ProgramNotFoundError):
            load_program("azalscore.nonexistent.program")

    def test_manifest_required_fields(self):
        """Test de validation des champs obligatoires du manifest"""
        program = load_program("azalscore.finance.calculate_margin")

        manifest = program.manifest

        # Vérifier les champs obligatoires
        required_fields = [
            "id", "name", "category", "version", "description",
            "inputs", "outputs", "side_effects", "idempotent",
            "no_code_compatible"
        ]

        for field in required_fields:
            assert field in manifest, f"Field {field} missing in manifest"

    def test_list_programs_by_category(self):
        """Test du filtrage par catégorie"""
        finance_programs = list_programs(category="finance")

        assert len(finance_programs) >= 1
        assert all(p["category"] == "finance" for p in finance_programs)

    def test_list_programs_no_code_only(self):
        """Test du filtrage No-Code uniquement"""
        no_code_programs = list_programs(no_code_only=True)

        assert len(no_code_programs) >= 4
        assert all(p["no_code_compatible"] is True for p in no_code_programs)

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        program = load_program("azalscore.finance.calculate_margin")

        inputs = {"price": 1000.0, "cost": 800.0}

        result1 = program.execute(inputs)
        result2 = program.execute(inputs)
        result3 = program.execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        program = load_program("azalscore.finance.calculate_margin")

        inputs = {"price": 1000.0, "cost": 800.0}
        inputs_copy = inputs.copy()

        program.execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
