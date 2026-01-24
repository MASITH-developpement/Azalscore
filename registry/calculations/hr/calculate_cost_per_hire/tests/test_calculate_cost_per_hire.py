"""
Tests du sous-programme calculate_cost_per_hire

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateCostPerHire:
    """Tests du sous-programme calculate_cost_per_hire"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "recruitment_costs": [],
            "number_of_hires": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "cost_per_hire" in result
        assert "total_cost" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "recruitment_costs": "test_value",
            "number_of_hires": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "recruitment_costs": "test",
            "number_of_hires": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
