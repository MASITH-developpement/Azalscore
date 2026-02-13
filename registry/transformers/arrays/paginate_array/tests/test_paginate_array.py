"""
Tests du sous-programme paginate_array

Couverture cible : >= 80%
"""

import pytest
from registry.transformers.arrays.paginate_array.impl import execute


class TestPaginateArray:
    """Tests du sous-programme paginate_array"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "items": [],
            "page": 100.0,
            "page_size": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "items" in result
        assert "total_items" in result
        assert "total_pages" in result
        assert "current_page" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {
            "items": "test_value",
            "page": 100.0,
            "page_size": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {
            "items": "test",
            "page": "test",
            "page_size": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
