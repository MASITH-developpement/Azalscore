"""
Conftest for automated_accounting tests.
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def mock_tesseract():
    """Mock TesseractEngine to avoid pytesseract dependency."""
    with patch(
        "app.modules.automated_accounting.services.ocr_service.TesseractEngine._check_tesseract",
        return_value=False
    ):
        yield


@pytest.fixture(autouse=True)
def mock_tesseract_init():
    """Patch TesseractEngine init to avoid pytesseract import."""
    # Patch the entire class to be a mock
    mock_engine = MagicMock()
    mock_engine.engine_name = "tesseract"
    mock_engine.engine_version = "5.0.0"
    mock_engine._tesseract_available = False
    mock_engine.extract_text.return_value = ("", 0.0)

    with patch(
        "app.modules.automated_accounting.services.ocr_service.TesseractEngine",
        return_value=mock_engine
    ):
        yield mock_engine
