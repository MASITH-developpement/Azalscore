"""
AZALS - Configuration sécurisée
Validation des variables d'environnement avec Pydantic
"""

from functools import lru_cache
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuration applicative.
    Toutes les valeurs sensibles proviennent de variables d'environnement.
    """
    
    database_url: str = Field(
        default="sqlite:///./azals.db",
        description="URL de connexion PostgreSQL ou SQLite"
    )
    app_name: str = "AZALS"
    debug: bool = False
    secret_key: str = Field(
        default="dev-secret-key-CHANGE-IN-PRODUCTION",
        min_length=32,
        description="Clé secrète pour la sécurité (min 32 caractères)"
    )
    
    # Configuration pool de connexions DB
    db_pool_size: int = Field(default=5, ge=1, le=100)
    db_max_overflow: int = Field(default=10, ge=0, le=100)
    
    # CORS (optionnel)
    cors_origins: Optional[str] = Field(default=None, description="Origins CORS séparées par des virgules")
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Valide que l'URL de la base de données est au format PostgreSQL."""
        if not v.startswith(('postgresql://', 'postgresql+psycopg2://')):
            raise ValueError('DATABASE_URL doit commencer par postgresql://')
        if 'CHANGEME' in v:
            raise ValueError('DATABASE_URL contient un placeholder non remplacé')
        return v
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Valide la robustesse de la clé secrète."""
        if len(v) < 32:
            raise ValueError('SECRET_KEY doit contenir au moins 32 caractères')
        if 'CHANGEME' in v:
            raise ValueError('SECRET_KEY contient un placeholder non remplacé')
        return v

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """
    Retourne la configuration en cache.
    Le cache évite de relire les variables à chaque appel.
    """
    return Settings()


# Instance globale de settings pour compatibilité
settings = Settings()
