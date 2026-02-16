"""
Configuration de Sécurité AZALSCORE
===================================

Configuration centralisée pour tous les paramètres de sécurité.
À adapter selon l'environnement (dev, staging, production).
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Environment(str, Enum):
    """Environnements supportés"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class SessionConfig:
    """Configuration des sessions"""
    # Durée de vie des tokens
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Limite de sessions concurrentes par utilisateur
    max_concurrent_sessions: int = 5

    # Timeout d'inactivité (minutes)
    idle_timeout_minutes: int = 30

    # Rotation automatique des refresh tokens
    enable_token_rotation: bool = True

    # Store de sessions (memory, redis)
    session_store_type: str = "redis"
    redis_url: Optional[str] = None

    # Détection de hijacking
    enable_hijack_detection: bool = True

    def __post_init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")


@dataclass
class MFAConfig:
    """Configuration MFA"""
    # Méthodes MFA activées
    enable_totp: bool = True
    enable_webauthn: bool = True
    enable_sms_otp: bool = False  # Désactivé par défaut (moins sécurisé)
    enable_email_otp: bool = True

    # TOTP
    totp_issuer: str = "AZALSCORE"
    totp_digits: int = 6
    totp_interval: int = 30
    totp_valid_window: int = 1  # Accepte ±1 intervalle

    # Codes de secours
    backup_codes_count: int = 10

    # MFA adaptatif
    enable_adaptive_mfa: bool = True
    risk_threshold_low: int = 30
    risk_threshold_medium: int = 60
    risk_threshold_high: int = 80

    # Confiance des appareils
    device_trust_duration_days: int = 30
    max_trusted_devices: int = 10


@dataclass
class EncryptionConfig:
    """Configuration du chiffrement"""
    # Algorithme par défaut
    default_algorithm: str = "AES-256-GCM"

    # Rotation des clés
    key_rotation_days: int = 90
    enable_auto_rotation: bool = True

    # HSM (optionnel)
    use_hsm: bool = False
    hsm_provider: str = "software"  # software, aws_kms, azure_keyvault
    aws_kms_key_id: Optional[str] = None

    # Tokenisation
    enable_tokenization: bool = True
    token_vault_encryption: bool = True


@dataclass
class AuditConfig:
    """Configuration de l'audit trail"""
    # Rétention des logs
    retention_days: int = 365 * 7  # 7 ans pour conformité fiscale

    # Catégories à auditer
    audit_authentication: bool = True
    audit_authorization: bool = True
    audit_data_access: bool = True
    audit_data_modification: bool = True
    audit_configuration: bool = True
    audit_security: bool = True

    # Intégration SIEM
    enable_siem: bool = True
    siem_provider: str = "elasticsearch"  # splunk, elasticsearch, datadog, syslog

    # Configuration Elasticsearch
    elasticsearch_hosts: list = field(default_factory=lambda: ["https://localhost:9200"])
    elasticsearch_index_prefix: str = "azalscore-audit"

    # Configuration Splunk
    splunk_hec_url: Optional[str] = None
    splunk_hec_token: Optional[str] = None

    # Configuration Syslog
    syslog_host: str = "localhost"
    syslog_port: int = 514
    syslog_protocol: str = "tcp"
    syslog_tls: bool = True

    # Alertes temps réel
    enable_threat_detection: bool = True
    brute_force_threshold: int = 5  # Tentatives avant alerte
    brute_force_window_minutes: int = 15


@dataclass
class PasswordConfig:
    """Configuration des mots de passe"""
    # Longueur minimale
    min_length: int = 12

    # Complexité requise
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special: bool = True

    # Historique
    password_history_count: int = 12  # Ne peut pas réutiliser les 12 derniers

    # Expiration
    password_expire_days: int = 90
    password_warning_days: int = 14

    # Verrouillage
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 30

    # Algorithme de hachage
    hash_algorithm: str = "argon2"
    argon2_time_cost: int = 3
    argon2_memory_cost: int = 65536
    argon2_parallelism: int = 4


@dataclass
class CORSConfig:
    """Configuration CORS"""
    allowed_origins: list = field(default_factory=lambda: [
        "https://app.azalscore.com",
        "https://admin.azalscore.com"
    ])
    allowed_methods: list = field(default_factory=lambda: [
        "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"
    ])
    allowed_headers: list = field(default_factory=lambda: [
        "Authorization", "Content-Type", "X-Request-ID", "X-Tenant-ID"
    ])
    allow_credentials: bool = True
    max_age: int = 86400  # 24 heures


@dataclass
class RateLimitConfig:
    """Configuration du rate limiting"""
    # Limites par défaut
    requests_per_minute: int = 100
    requests_per_hour: int = 1000

    # Limites par endpoint sensible
    auth_requests_per_minute: int = 10
    api_key_requests_per_minute: int = 1000
    export_requests_per_hour: int = 10

    # Limites par tenant
    tenant_requests_per_minute: int = 1000
    tenant_requests_per_hour: int = 10000


@dataclass
class TLSConfig:
    """Configuration TLS"""
    # Version minimale
    min_version: str = "TLSv1.2"

    # Cipher suites autorisées (ordre de préférence)
    cipher_suites: list = field(default_factory=lambda: [
        "TLS_AES_256_GCM_SHA384",
        "TLS_CHACHA20_POLY1305_SHA256",
        "TLS_AES_128_GCM_SHA256",
        "ECDHE-ECDSA-AES256-GCM-SHA384",
        "ECDHE-RSA-AES256-GCM-SHA384",
    ])

    # HSTS
    enable_hsts: bool = True
    hsts_max_age: int = 31536000  # 1 an
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True


@dataclass
class HeadersConfig:
    """Configuration des headers de sécurité"""
    # Content Security Policy
    csp_default_src: str = "'self'"
    csp_script_src: str = "'self'"
    csp_style_src: str = "'self' 'unsafe-inline'"
    csp_img_src: str = "'self' data: https:"
    csp_frame_ancestors: str = "'none'"

    # Autres headers
    x_content_type_options: str = "nosniff"
    x_frame_options: str = "DENY"
    x_xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "geolocation=(), microphone=(), camera=()"


@dataclass
class DisasterRecoveryConfig:
    """Configuration Disaster Recovery"""
    # Objectifs de récupération par défaut
    default_rpo_minutes: int = 15
    default_rto_minutes: int = 60

    # Réplication
    enable_replication: bool = True
    replication_mode: str = "async"  # sync, async
    primary_region: str = "eu-west-1"
    dr_regions: list = field(default_factory=lambda: ["eu-central-1"])

    # Backups
    backup_frequency_hours: int = 1
    backup_retention_days: int = 30
    enable_pitr: bool = True
    pitr_retention_days: int = 7

    # Tests DR
    dr_test_frequency_days: int = 30
    enable_auto_dr_tests: bool = True


@dataclass
class ComplianceConfig:
    """Configuration conformité"""
    # Réglementations activées
    enable_rgpd: bool = True
    enable_nf525: bool = True
    enable_pci_dss: bool = False
    enable_iso27001: bool = True

    # RGPD
    data_retention_years: int = 10
    enable_data_portability: bool = True
    enable_right_to_erasure: bool = True
    dpo_email: str = "dpo@azalscore.com"

    # NF525
    enable_hash_chain: bool = True
    fec_export_enabled: bool = True

    # Audit
    compliance_audit_frequency_days: int = 90


@dataclass
class SecurityConfig:
    """Configuration de sécurité globale"""
    environment: Environment = Environment.PRODUCTION

    # Sous-configurations
    session: SessionConfig = field(default_factory=SessionConfig)
    mfa: MFAConfig = field(default_factory=MFAConfig)
    encryption: EncryptionConfig = field(default_factory=EncryptionConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    password: PasswordConfig = field(default_factory=PasswordConfig)
    cors: CORSConfig = field(default_factory=CORSConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    tls: TLSConfig = field(default_factory=TLSConfig)
    headers: HeadersConfig = field(default_factory=HeadersConfig)
    disaster_recovery: DisasterRecoveryConfig = field(default_factory=DisasterRecoveryConfig)
    compliance: ComplianceConfig = field(default_factory=ComplianceConfig)

    @classmethod
    def for_environment(cls, env: str) -> "SecurityConfig":
        """Crée une configuration adaptée à l'environnement"""
        environment = Environment(env.lower())
        config = cls(environment=environment)

        if environment == Environment.DEVELOPMENT:
            # Paramètres assouplis pour le développement
            config.session.access_token_expire_minutes = 60
            config.session.session_store_type = "memory"
            config.mfa.enable_adaptive_mfa = False
            config.audit.enable_siem = False
            config.cors.allowed_origins = ["http://localhost:3000", "http://localhost:8000"]
            config.rate_limit.requests_per_minute = 1000

        elif environment == Environment.STAGING:
            # Paramètres intermédiaires
            config.session.access_token_expire_minutes = 30
            config.cors.allowed_origins.append("https://staging.azalscore.com")

        # Production utilise les valeurs par défaut (les plus strictes)

        return config


# Configuration globale
_security_config: Optional[SecurityConfig] = None


def get_security_config() -> SecurityConfig:
    """Retourne la configuration de sécurité"""
    global _security_config
    if _security_config is None:
        env = os.getenv("ENVIRONMENT", "production")
        _security_config = SecurityConfig.for_environment(env)
    return _security_config


def init_security_config(env: str = None) -> SecurityConfig:
    """Initialise la configuration de sécurité"""
    global _security_config
    env = env or os.getenv("ENVIRONMENT", "production")
    _security_config = SecurityConfig.for_environment(env)
    return _security_config
