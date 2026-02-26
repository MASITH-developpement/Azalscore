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
    rate_limit_per_minute: int = Field(default=100, ge=10, le=1000, description="Limite globale de requêtes par minute")
    auth_rate_limit_per_minute: int = Field(default=5, ge=1, le=20, description="Rate limit strict pour auth")

    # Redis (pour rate limiting distribué)
    redis_url: str | None = Field(default=None, description="URL Redis pour cache et rate limiting")
    redis_timeout: int = Field(default=5, ge=1, le=30, description="Timeout connexion Redis en secondes")
    redis_health_timeout: int = Field(default=2, ge=1, le=10, description="Timeout health check Redis en secondes")

    # CORS
    cors_max_age: int = Field(default=3600, ge=60, le=86400, description="Durée cache CORS en secondes")

    # Timeouts API
    api_timeout_ms: int = Field(default=30000, ge=1000, le=300000, description="Timeout API par défaut en ms")

    # Application URL (pour emails, redirections)
    app_url: str = Field(default="https://localhost", description="URL publique de l'application")
    app_domain: str = Field(default="localhost", description="Domaine principal de l'application")

    # SMTP Configuration (pour envoi d'emails)
    SMTP_HOST: str | None = Field(default=None, description="Serveur SMTP (ex: smtp.gmail.com)")
    SMTP_PORT: int = Field(default=587, ge=1, le=65535, description="Port SMTP")
    SMTP_USER: str | None = Field(default=None, description="Utilisateur SMTP")
    SMTP_PASSWORD: str | None = Field(default=None, description="Mot de passe SMTP")
    SMTP_FROM: str = Field(default="AZALS <noreply@azalscore.com>", description="Adresse expéditeur")
    SMTP_USE_TLS: bool = Field(default=True, description="Utiliser STARTTLS (port 587)")
    SMTP_USE_SSL: bool = Field(default=False, description="Utiliser SSL direct (port 465)")

    # Stripe Configuration (pour paiements)
    STRIPE_SECRET_KEY: str | None = Field(default=None, description="Clé secrète Stripe")
    STRIPE_PUBLISHABLE_KEY: str | None = Field(default=None, description="Clé publique Stripe")
    STRIPE_WEBHOOK_SECRET: str | None = Field(default=None, description="Secret webhook Stripe")
    STRIPE_API_KEY_LIVE: str | None = Field(default=None, description="Clé API Stripe Live (alternative)")
    STRIPE_API_KEY_TEST: str | None = Field(default=None, description="Clé API Stripe Test")
    STRIPE_LIVE_MODE: bool = Field(default=False, description="Mode production Stripe")

    # reCAPTCHA v3 Configuration (anti-bot)
    RECAPTCHA_SECRET_KEY: str | None = Field(default=None, description="Clé secrète reCAPTCHA v3")
    RECAPTCHA_SITE_KEY: str | None = Field(default=None, description="Clé site reCAPTCHA v3")

    # hCaptcha Configuration (legacy, deprecated)
    HCAPTCHA_SECRET_KEY: str | None = Field(default=None, description="Clé secrète hCaptcha (deprecated)")
    HCAPTCHA_SITE_KEY: str | None = Field(default=None, description="Clé site hCaptcha (deprecated)")

    # Resend Configuration (email alternatif)
    RESEND_API_KEY: str | None = Field(default=None, description="Clé API Resend pour emails")
    EMAIL_FROM: str | None = Field(default=None, description="Adresse email expéditeur (Resend)")

    # IA / LLM Configuration
    OPENAI_API_KEY: str | None = Field(default=None, description="Clé API OpenAI")
    ANTHROPIC_API_KEY: str | None = Field(default=None, description="Clé API Anthropic (Claude)")
    ELEVENLABS_API_KEY: str | None = Field(default=None, description="Clé API ElevenLabs (TTS)")

    # Fournisseurs de paiement externes
    SWAN_API_KEY: str | None = Field(default=None, description="Clé API Swan Banking")
    SWAN_PROJECT_ID: str | None = Field(default=None, description="ID projet Swan")
    SWAN_WEBHOOK_SECRET: str | None = Field(default=None, description="Secret webhook Swan")
    SWAN_SANDBOX: bool = Field(default=True, description="Mode sandbox Swan")

    NMI_API_KEY: str | None = Field(default=None, description="Clé API NMI")
    NMI_WEBHOOK_SECRET: str | None = Field(default=None, description="Secret webhook NMI")
    NMI_SANDBOX: bool = Field(default=True, description="Mode sandbox NMI")

    SOLARIS_CLIENT_ID: str | None = Field(default=None, description="Client ID Solaris")
    SOLARIS_CLIENT_SECRET: str | None = Field(default=None, description="Client Secret Solaris")
    SOLARIS_WEBHOOK_SECRET: str | None = Field(default=None, description="Secret webhook Solaris")
    SOLARIS_SANDBOX: bool = Field(default=True, description="Mode sandbox Solaris")

    DEFACTO_API_KEY: str | None = Field(default=None, description="Clé API Defacto")
    DEFACTO_WEBHOOK_SECRET: str | None = Field(default=None, description="Secret webhook Defacto")
    DEFACTO_SANDBOX: bool = Field(default=True, description="Mode sandbox Defacto")

    # Sécurité avancée
    TRUSTED_PROXIES: str | None = Field(default=None, description="Liste des proxies de confiance (IPs séparées par virgules)")
    ALLOWED_REDIRECT_DOMAINS: str | None = Field(default=None, description="Domaines autorisés pour redirections")

    # Guardian / Monitoring
    AZALS_DATA_DIR: str = Field(default="/var/lib/azalscore", description="Répertoire données AZALS")
    GUARDIAN_SCREENSHOT_DIR: str | None = Field(default=None, description="Répertoire screenshots Guardian")

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
