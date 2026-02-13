"""
Tests du sous-programme validate_right_to_erasure

Couverture cible : >= 80%
"""

import pytest
from registry.validators.compliance.validate_right_to_erasure.impl import execute


class TestValidateRightToErasure:
    """Tests du sous-programme validate_right_to_erasure"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "request": {},
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "is_valid" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {
            "request": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {
            "request": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
