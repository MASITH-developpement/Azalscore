"""
Tests du sous-programme calculate_training_roi

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateTrainingRoi:
    """Tests du sous-programme calculate_training_roi"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "training_cost": 100.0,
            "productivity_gain": 100.0,
            "time_period_months": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "roi" in result
        assert "roi_percentage" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "training_cost": 100.0,
            "productivity_gain": 100.0,
            "time_period_months": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "training_cost": "test",
            "productivity_gain": "test",
            "time_period_months": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
