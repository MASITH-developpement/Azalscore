"""
Configuration pytest pour AZALS.
Configure l'environnement de test avant l'import des modules.
"""

import os
import sys

# Configurer les variables d'environnement AVANT tout import
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-key-minimum-32-characters-long-for-tests")
os.environ.setdefault("BOOTSTRAP_SECRET", "test-bootstrap-minimum-32-characters-here")
os.environ.setdefault("ENVIRONMENT", "test")

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture(scope="session", autouse=True)
def initialize_security_services():
    """Initialize security services for testing."""
    from app.core.session_management import initialize_session_services

    initialize_session_services(
        secret_key=os.environ.get("SECRET_KEY", "test-key-minimum-32-characters-long-for-tests"),
        session_store_type="memory",
        max_concurrent_sessions=5,
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
    )

    yield
