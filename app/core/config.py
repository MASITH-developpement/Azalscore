"""
AZALS - Configuration sécurisée
Validation des variables d'environnement avec Pydantic
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuration applicative.
    Toutes les valeurs sensibles proviennent de variables d'environnement.
    """
    
    database_url: str
    app_name: str = "AZALS"
    debug: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """
    Retourne la configuration en cache.
    Le cache évite de relire les variables à chaque appel.
    """
    return Settings()
