"""
Tests du sous-programme generate_download_link

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class TestGenerateDownloadLink:
    """Tests du sous-programme generate_download_link"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {
            "file_id": "test_value",
            "expiry_hours": 100.0,
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)

        assert "download_url" in result
        assert "expires_at" in result

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{
            "file_id": "test_value",
            "expiry_hours": 100.0,
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{
            "file_id": "test",
            "expiry_hours": "test",
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
