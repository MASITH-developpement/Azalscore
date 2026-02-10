"""
Tests du sous-programme calculate_project_duration

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateProjectDuration:
    """Tests du sous-programme calculate_project_duration"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "tasks": [],
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "total_duration" in result
        assert "critical_path" in result
        assert "earliest_start" in result
        assert "latest_finish" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "tasks": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "tasks": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
