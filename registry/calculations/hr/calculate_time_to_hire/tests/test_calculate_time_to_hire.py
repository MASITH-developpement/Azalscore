"""
Tests du sous-programme calculate_time_to_hire

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateTimeToHire:
    """Tests du sous-programme calculate_time_to_hire"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "posting_date": "test_value",
            "hire_date": "test_value",
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "days_to_hire" in result
        assert "weeks_to_hire" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "posting_date": "test_value",
            "hire_date": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "posting_date": "test",
            "hire_date": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
