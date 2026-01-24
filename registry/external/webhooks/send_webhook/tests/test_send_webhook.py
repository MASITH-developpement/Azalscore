"""
Tests du sous-programme send_webhook

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestSendWebhook:
    """Tests du sous-programme send_webhook"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "url": "test_value",
            "payload": {},
            "headers": {},
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "status_code" in result
        assert "response" in result
        assert "error" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "url": "test_value",
            "payload": "test_value",
            "headers": "test_value",
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "url": "test",
            "payload": "test",
            "headers": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
