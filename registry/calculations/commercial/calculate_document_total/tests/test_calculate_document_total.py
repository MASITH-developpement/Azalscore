"""
Tests du sous-programme calculate_document_total

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateDocumentTotal:
    """Tests du sous-programme calculate_document_total"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "lines": [],
            "global_discount": 100.0,
            "shipping_cost": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "subtotal_ht" in result
        assert "total_discount" in result
        assert "total_ht" in result
        assert "total_vat" in result
        assert "total_ttc" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "lines": "test_value",
            "global_discount": 100.0,
            "shipping_cost": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "lines": "test",
            "global_discount": "test",
            "shipping_cost": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
