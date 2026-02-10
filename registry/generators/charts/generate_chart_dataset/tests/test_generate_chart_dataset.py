"""
Tests du sous-programme generate_chart_dataset

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestGenerateChartDataset:
    """Tests du sous-programme generate_chart_dataset"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "data": [],
            "chart_type": "test_value",
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "dataset" in result
        assert "labels" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "data": "test_value",
            "chart_type": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "data": "test",
            "chart_type": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
