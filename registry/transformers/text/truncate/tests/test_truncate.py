"""
Tests du sous-programme truncate

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestTruncate:
    """Tests du sous-programme truncate"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "value": "test_value",
            "max_length": 100.0,
            "suffix": "test_value",
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "truncated_value" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "value": "test_value",
            "max_length": 100.0,
            "suffix": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "value": "test",
            "max_length": "test",
            "suffix": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
