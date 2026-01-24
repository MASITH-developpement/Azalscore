"""
Tests du sous-programme calculate_customer_acquisition_cost

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateCustomerAcquisitionCost:
    """Tests du sous-programme calculate_customer_acquisition_cost"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "marketing_cost": 100.0,
            "sales_cost": 100.0,
            "new_customers": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "cac" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "marketing_cost": 100.0,
            "sales_cost": 100.0,
            "new_customers": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "marketing_cost": "test",
            "sales_cost": "test",
            "new_customers": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
