"""
Tests du sous-programme calculate_leave_entitlement

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateLeaveEntitlement:
    """Tests du sous-programme calculate_leave_entitlement"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "months_worked": 100.0,
            "annual_leave_days": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "entitlement_days" in result
        assert "accrued_days" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "months_worked": 100.0,
            "annual_leave_days": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "months_worked": "test",
            "annual_leave_days": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
