"""
Configuration pytest pour AZALS.
Configure l'environnement de test avant l'import des modules.
"""

import os
import sys

# Configurer les variables d'environnement AVANT tout import
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("ENVIRONMENT", "test")

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
