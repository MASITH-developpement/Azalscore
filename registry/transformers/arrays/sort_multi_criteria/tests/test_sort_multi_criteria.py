"""
Tests du sous-programme sort_multi_criteria

Couverture cible : >= 80%
"""

import pytest
from registry.transformers.arrays.sort_multi_criteria.impl import execute


class TestSortMultiCriteria:
    """Tests du sous-programme sort_multi_criteria"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "items": [],
            "criteria": [],
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "sorted" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {
            "items": "test_value",
            "criteria": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {
            "items": "test",
            "criteria": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
