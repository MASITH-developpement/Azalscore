"""
AZALSCORE AI Configuration

Configuration centrale du système IA.
Toutes les configurations sont versionnées et traçables.

Conformité: AZA-NF-009, AZA-IA-002
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum


class Environment(Enum):
    """Environnements de déploiement"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class AIModuleConfig:
    """Configuration d'un module IA"""
    enabled: bool
    model: str
    max_tokens: int
    temperature: float
    timeout_ms: int
    rate_limit_per_minute: int


@dataclass
class GuardianConfig:
    """Configuration de Guardian"""
    enabled: bool
    block_dangerous_patterns: bool
    rate_limit_enabled: bool
    ai_calls_per_minute: int
    ai_calls_per_hour: int
    sensitive_operations_per_day: int
    auto_block_on_critical: bool


@dataclass
class AuthConfig:
    """Configuration d'authentification"""
    mfa_required_for_admin: bool
    mfa_required_for_owner: bool
    session_duration_hours: int
    mfa_code_validity_minutes: int
    max_failed_attempts: int
    lockout_duration_minutes: int


@dataclass
class AuditConfig:
    """Configuration d'audit"""
    enabled: bool
    log_directory: str
    retention_days: int
    log_sensitive_data: bool
    checksum_enabled: bool


class AIConfig:
    """
    Configuration globale du système IA AZALSCORE

    Centralise toutes les configurations pour:
    - Les modules IA (GPT, Claude)
    - Guardian (sécurité)
    - Authentification
    - Audit et journalisation
    """

    def __init__(self):
        self.environment = self._detect_environment()
        self._load_config()

    def _detect_environment(self) -> Environment:
        """Détecte l'environnement actuel"""
        env = os.getenv("AZALSCORE_ENV", "development").lower()
        return {
            "development": Environment.DEVELOPMENT,
            "staging": Environment.STAGING,
            "production": Environment.PRODUCTION
        }.get(env, Environment.DEVELOPMENT)

    def _load_config(self):
        """Charge la configuration selon l'environnement"""

        # Configuration GPT (Architecte Cognitif)
        self.gpt = AIModuleConfig(
            enabled=bool(os.getenv("OPENAI_API_KEY")),
            model=os.getenv("AZALSCORE_GPT_MODEL", "gpt-4o"),
            max_tokens=int(os.getenv("AZALSCORE_GPT_MAX_TOKENS", "2000")),
            temperature=float(os.getenv("AZALSCORE_GPT_TEMPERATURE", "0.3")),
            timeout_ms=int(os.getenv("AZALSCORE_GPT_TIMEOUT_MS", "30000")),
            rate_limit_per_minute=int(os.getenv("AZALSCORE_GPT_RATE_LIMIT", "30"))
        )

        # Configuration Claude (Expert Technique)
        self.claude = AIModuleConfig(
            enabled=bool(os.getenv("ANTHROPIC_API_KEY")),
            model=os.getenv("AZALSCORE_CLAUDE_MODEL", "claude-sonnet-4-20250514"),
            max_tokens=int(os.getenv("AZALSCORE_CLAUDE_MAX_TOKENS", "2000")),
            temperature=float(os.getenv("AZALSCORE_CLAUDE_TEMPERATURE", "0.3")),
            timeout_ms=int(os.getenv("AZALSCORE_CLAUDE_TIMEOUT_MS", "30000")),
            rate_limit_per_minute=int(os.getenv("AZALSCORE_CLAUDE_RATE_LIMIT", "30"))
        )

        # Configuration Guardian
        self.guardian = GuardianConfig(
            enabled=True,  # Toujours actif
            block_dangerous_patterns=True,
            rate_limit_enabled=True,
            ai_calls_per_minute=int(os.getenv("AZALSCORE_AI_CALLS_PER_MINUTE", "60")),
            ai_calls_per_hour=int(os.getenv("AZALSCORE_AI_CALLS_PER_HOUR", "500")),
            sensitive_operations_per_day=int(os.getenv("AZALSCORE_SENSITIVE_OPS_PER_DAY", "10")),
            auto_block_on_critical=True
        )

        # Configuration Auth
        self.auth = AuthConfig(
            mfa_required_for_admin=True,
            mfa_required_for_owner=True,
            session_duration_hours=int(os.getenv("AZALSCORE_SESSION_HOURS", "2")),
            mfa_code_validity_minutes=int(os.getenv("AZALSCORE_MFA_VALIDITY_MINUTES", "10")),
            max_failed_attempts=int(os.getenv("AZALSCORE_MAX_FAILED_ATTEMPTS", "5")),
            lockout_duration_minutes=int(os.getenv("AZALSCORE_LOCKOUT_MINUTES", "15"))
        )

        # Configuration Audit
        self.audit = AuditConfig(
            enabled=True,  # Toujours actif (conformité AZA-NF-009)
            log_directory=os.getenv("AZALSCORE_AUDIT_LOG_DIR", "/home/ubuntu/azalscore/logs/ai_audit"),
            retention_days=int(os.getenv("AZALSCORE_AUDIT_RETENTION_DAYS", "365")),
            log_sensitive_data=self.environment != Environment.PRODUCTION,
            checksum_enabled=True
        )

    def to_dict(self) -> Dict[str, Any]:
        """Exporte la configuration en dictionnaire (sans secrets)"""
        return {
            "environment": self.environment.value,
            "gpt": {
                "enabled": self.gpt.enabled,
                "model": self.gpt.model,
                "max_tokens": self.gpt.max_tokens,
                "timeout_ms": self.gpt.timeout_ms
            },
            "claude": {
                "enabled": self.claude.enabled,
                "model": self.claude.model,
                "max_tokens": self.claude.max_tokens,
                "timeout_ms": self.claude.timeout_ms
            },
            "guardian": {
                "enabled": self.guardian.enabled,
                "rate_limit_enabled": self.guardian.rate_limit_enabled,
                "ai_calls_per_minute": self.guardian.ai_calls_per_minute
            },
            "auth": {
                "mfa_required_for_admin": self.auth.mfa_required_for_admin,
                "session_duration_hours": self.auth.session_duration_hours
            },
            "audit": {
                "enabled": self.audit.enabled,
                "retention_days": self.audit.retention_days
            }
        }


# Instance singleton
_config_instance: Optional[AIConfig] = None


def get_ai_config() -> AIConfig:
    """Récupère l'instance singleton de la configuration"""
    global _config_instance
    if _config_instance is None:
        _config_instance = AIConfig()
    return _config_instance
