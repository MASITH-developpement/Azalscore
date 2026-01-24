"""
Tests du sous-programme calculate_churn_rate

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestCalculateChurnRate:
    """Tests du sous-programme calculate_churn_rate"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "customers_start": 100.0,
            "customers_lost": 100.0,
            "period_days": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "churn_rate" in result
        assert "retention_rate" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "customers_start": 100.0,
            "customers_lost": 100.0,
            "period_days": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "customers_start": "test",
            "customers_lost": "test",
            "period_days": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
