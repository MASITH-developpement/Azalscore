"""
Tests pour la configuration Marceau.
"""

import pytest
from unittest.mock import MagicMock

from app.modules.marceau.config import (
    DEFAULT_ENABLED_MODULES,
    DEFAULT_AUTONOMY_LEVELS,
    get_or_create_marceau_config,
    is_module_enabled,
    get_autonomy_level,
    requires_validation,
)
from app.modules.marceau.models import MarceauConfig


class TestMarceauConfig:
    """Tests de configuration Marceau."""

    def test_default_enabled_modules(self):
        """Verifie les modules actives par defaut."""
        assert DEFAULT_ENABLED_MODULES["telephonie"] is True
        assert DEFAULT_ENABLED_MODULES["marketing"] is False
        assert DEFAULT_ENABLED_MODULES["seo"] is False

    def test_default_autonomy_levels(self):
        """Verifie les niveaux d'autonomie par defaut."""
        for module, level in DEFAULT_AUTONOMY_LEVELS.items():
            assert level == 100, f"Module {module} devrait etre a 100%"

    def test_is_module_enabled_with_config(self):
        """Test is_module_enabled avec config."""
        config = MagicMock(spec=MarceauConfig)
        config.enabled_modules = {"telephonie": True, "marketing": False}

        assert is_module_enabled(config, "telephonie") is True
        assert is_module_enabled(config, "marketing") is False
        assert is_module_enabled(config, "unknown") is False

    def test_is_module_enabled_without_config(self):
        """Test is_module_enabled sans config."""
        assert is_module_enabled(None, "telephonie") is False

    def test_get_autonomy_level(self):
        """Test get_autonomy_level."""
        config = MagicMock(spec=MarceauConfig)
        config.autonomy_levels = {"telephonie": 80, "marketing": 50}

        assert get_autonomy_level(config, "telephonie") == 80
        assert get_autonomy_level(config, "marketing") == 50
        assert get_autonomy_level(config, "unknown") == 100  # Default

    def test_requires_validation_full_autonomy(self):
        """Test requires_validation avec autonomie a 100%."""
        config = MagicMock(spec=MarceauConfig)
        config.autonomy_levels = {"telephonie": 100}

        # Jamais de validation si autonomie a 100%
        assert requires_validation(config, "telephonie", 1.0) is False
        assert requires_validation(config, "telephonie", 0.5) is False
        assert requires_validation(config, "telephonie", 0.1) is False

    def test_requires_validation_no_autonomy(self):
        """Test requires_validation avec autonomie a 0%."""
        config = MagicMock(spec=MarceauConfig)
        config.autonomy_levels = {"telephonie": 0}

        # Toujours validation si autonomie a 0%
        assert requires_validation(config, "telephonie", 1.0) is True
        assert requires_validation(config, "telephonie", 0.5) is True

    def test_requires_validation_partial_autonomy(self):
        """Test requires_validation avec autonomie partielle."""
        config = MagicMock(spec=MarceauConfig)
        config.autonomy_levels = {"telephonie": 70}

        # Confiance 90% > autonomie 70% -> pas de validation
        assert requires_validation(config, "telephonie", 0.9) is False

        # Confiance 50% < autonomie 70% -> validation requise
        assert requires_validation(config, "telephonie", 0.5) is True
