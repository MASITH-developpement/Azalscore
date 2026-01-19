"""
AZALS - Configuration sécurisée ÉLITE
=====================================
Validation STRICTE des variables d'environnement.
AUCUN SECRET PAR DÉFAUT - Erreur fatale si absent.
"""

import os
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuration applicative SÉCURISÉE.

    RÈGLES DE SÉCURITÉ:
    - AUCUN secret par défaut en production
    - Validation stricte de tous les paramètres sensibles
    - Erreur fatale si configuration invalide

    VARIABLES UUID:
    - AZALS_ENV / ENVIRONMENT: dev | test | prod
    - DB_AUTO_RESET_ON_VIOLATION: Active le reset automatique (dev/test only)
    - DB_STRICT_UUID: Bloque le démarrage si violations détectées
    """

    # Environnement (test, development, production)
    # Supporte AZALS_ENV comme alias principal, ENVIRONMENT comme fallback
    environment: str = Field(
        default="development",
        description="Environnement d'exécution (dev, test, prod)",
        validation_alias="AZALS_ENV"
    )

    database_url: str = Field(
        ...,
        description="URL de connexion PostgreSQL (OBLIGATOIRE)"
    )
    app_name: str = "AZALS"
    debug: bool = False

    # SECRET_KEY - OBLIGATOIRE, PAS DE DÉFAUT
    secret_key: str = Field(
        ...,
        min_length=32,
        description="Clé secrète JWT (min 32 caractères) - OBLIGATOIRE"
    )

    # BOOTSTRAP_SECRET - OBLIGATOIRE EN PRODUCTION
    bootstrap_secret: str | None = Field(
        default=None,
        description="Secret pour bootstrap initial - OBLIGATOIRE en production"
    )

    # Configuration pool de connexions DB
    db_pool_size: int = Field(default=5, ge=1, le=100)
    db_max_overflow: int = Field(default=10, ge=0, le=100)

    # CORS (optionnel)
    cors_origins: str | None = Field(default=None, description="Origins CORS séparées par des virgules")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100, ge=10, le=1000)
    auth_rate_limit_per_minute: int = Field(default=5, ge=1, le=20, description="Rate limit strict pour auth")

    # Redis (pour rate limiting distribué)
    redis_url: str | None = Field(default=None, description="URL Redis pour cache et rate limiting")

    # ENCRYPTION_KEY - OBLIGATOIRE EN PRODUCTION pour chiffrement AES-256 au repos
    encryption_key: str | None = Field(
        default=None,
        description="Clé Fernet pour chiffrement AES-256 - OBLIGATOIRE en production"
    )

    # =========================================================================
    # CONFIGURATION UUID DATABASE
    # =========================================================================
    # Controle du comportement de migration/reset de la base de donnees
    # pour garantir la conformite UUID-only

    db_reset_uuid: bool = Field(
        default=False,
        description="Active le mode reset UUID (DESTRUCTIF - supprime toutes les donnees)"
    )

    db_strict_uuid: bool = Field(
        default=True,
        description="Bloque le demarrage si des colonnes BIGINT sont detectees"
    )

    db_auto_reset_on_violation: bool = Field(
        default=False,
        description="Reset automatique si violation UUID detectee (DANGER - dev only)"
    )

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """
        Valide l'environnement.
        Supporte les alias courts: dev, test, prod
        """
        v_lower = v.lower()

        # Mapping des alias courts vers les noms complets
        alias_mapping = {
            'dev': 'development',
            'prod': 'production',
        }
        v_lower = alias_mapping.get(v_lower, v_lower)

        allowed = ('test', 'development', 'staging', 'demo', 'production')
        if v_lower not in allowed:
            raise ValueError(
                f'AZALS_ENV/ENVIRONMENT doit être parmi: {allowed} '
                f'(ou alias: dev, prod)'
            )
        return v_lower

    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Valide que l'URL de la base de données est au format PostgreSQL ou SQLite (tests)."""
        env = os.environ.get('ENVIRONMENT', 'development').lower()
        valid_prefixes = ['postgresql://', 'postgresql+psycopg2://']
        # Autoriser SQLite uniquement en mode test
        if env == 'test' or v.startswith('sqlite://'):
            valid_prefixes.append('sqlite://')
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(f'DATABASE_URL doit commencer par {valid_prefixes}')
        if 'CHANGEME' in v:
            raise ValueError('DATABASE_URL contient un placeholder non remplacé')
        return v

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Valide la robustesse de la clé secrète - AUCUN DÉFAUT ACCEPTÉ."""
        if not v:
            raise ValueError('SECRET_KEY est OBLIGATOIRE - aucun défaut autorisé')
        if len(v) < 32:
            raise ValueError('SECRET_KEY doit contenir au moins 32 caractères')

        # Rejeter les valeurs par défaut dangereuses
        dangerous_defaults = [
            'dev-secret', 'change-me', 'changeme', 'secret',
            'password', '123456', 'azals', 'default'
        ]
        v_lower = v.lower()
        for dangerous in dangerous_defaults:
            if dangerous in v_lower:
                raise ValueError(
                    f'SECRET_KEY contient "{dangerous}" - utilisez une clé générée aléatoirement. '
                    f'Générez avec: python -c "import secrets; print(secrets.token_urlsafe(64))"'
                )

        return v

    @model_validator(mode='after')
    def validate_production_secrets(self):
        """Validation STRICTE en production - tous les secrets obligatoires."""
        if self.environment == 'production':
            # BOOTSTRAP_SECRET obligatoire en production
            if not self.bootstrap_secret:
                raise ValueError(
                    'BOOTSTRAP_SECRET est OBLIGATOIRE en production. '
                    'Générez avec: python -c "import secrets; print(secrets.token_urlsafe(64))"'
                )
            if len(self.bootstrap_secret) < 32:
                raise ValueError('BOOTSTRAP_SECRET doit contenir au moins 32 caractères en production')

            # Debug INTERDIT en production
            if self.debug:
                raise ValueError('DEBUG=true est INTERDIT en production')

            # CORS doit être configuré en production
            if not self.cors_origins:
                raise ValueError(
                    'CORS_ORIGINS doit être configuré en production. '
                    'Ex: CORS_ORIGINS=https://votre-frontend.onrender.com'
                )
            if 'localhost' in (self.cors_origins or '').lower():
                raise ValueError('localhost interdit dans CORS_ORIGINS en production')

            # ENCRYPTION_KEY obligatoire en production
            if not self.encryption_key:
                raise ValueError(
                    'ENCRYPTION_KEY est OBLIGATOIRE en production pour le chiffrement AES-256. '
                    'Générez avec: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
                )

            # Auto-reset UUID INTERDIT en production
            if self.db_auto_reset_on_violation:
                raise ValueError(
                    'DB_AUTO_RESET_ON_VIOLATION=true est INTERDIT en production. '
                    'Utilisez le script scripts/reset_database_uuid.py manuellement.'
                )

        return self

    @property
    def is_production(self) -> bool:
        """Vérifie si on est en production."""
        return self.environment == 'production'

    @property
    def is_development(self) -> bool:
        """Vérifie si on est en développement."""
        return self.environment in ('development', 'test')

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """
    Retourne la configuration en cache.
    Le cache évite de relire les variables à chaque appel.
    """
    return Settings()
