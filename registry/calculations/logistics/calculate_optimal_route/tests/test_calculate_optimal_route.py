"""
Tests du sous-programme calculate_optimal_route

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateOptimalRoute:
    """Tests du sous-programme calculate_optimal_route"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "stops": [],
            "start_location": {},
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "route" in result
        assert "total_distance_km" in result
        assert "estimated_time_minutes" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "stops": "test_value",
            "start_location": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "stops": "test",
            "start_location": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
