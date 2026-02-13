"""
Tests du sous-programme decompress_json

Couverture cible : >= 80%
"""

import pytest
from registry.transformers.compression.decompress_json.impl import execute


class TestDecompressJson:
    """Tests du sous-programme decompress_json"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "compressed": "test_value",
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "data" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {
            "compressed": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {
            "compressed": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
