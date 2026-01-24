"""
Tests du sous-programme calculate_absence_duration

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateAbsenceDuration:
    """Tests du sous-programme calculate_absence_duration"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "start_date": "test_value",
            "end_date": "test_value",
            "include_weekends": True,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "absence_days" in result
        assert "working_days" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "start_date": "test_value",
            "end_date": "test_value",
            "include_weekends": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "start_date": "test",
            "end_date": "test",
            "include_weekends": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
