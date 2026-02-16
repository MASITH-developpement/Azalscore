"""
Tests pour la configuration de sécurité
"""

import pytest
import os


class TestSecurityConfig:
    """Tests pour SecurityConfig"""

    def test_default_config_creation(self):
        """Test création de la config par défaut"""
        from config.security import SecurityConfig, Environment

        config = SecurityConfig()

        assert config.environment == Environment.PRODUCTION
        assert config.session.access_token_expire_minutes == 15
        assert config.mfa.enable_totp is True
        assert config.encryption.default_algorithm == "AES-256-GCM"

    def test_development_config(self):
        """Test configuration développement"""
        from config.security import SecurityConfig, Environment

        config = SecurityConfig.for_environment("development")

        assert config.environment == Environment.DEVELOPMENT
        assert config.session.access_token_expire_minutes == 60
        assert config.session.session_store_type == "memory"
        assert config.mfa.enable_adaptive_mfa is False

    def test_staging_config(self):
        """Test configuration staging"""
        from config.security import SecurityConfig, Environment

        config = SecurityConfig.for_environment("staging")

        assert config.environment == Environment.STAGING
        assert config.session.access_token_expire_minutes == 30
        assert "https://staging.azalscore.com" in config.cors.allowed_origins

    def test_production_config(self):
        """Test configuration production"""
        from config.security import SecurityConfig, Environment

        config = SecurityConfig.for_environment("production")

        assert config.environment == Environment.PRODUCTION
        assert config.session.access_token_expire_minutes == 15
        assert config.audit.enable_siem is True
        assert config.compliance.enable_nf525 is True

    def test_password_config_security(self):
        """Test que la config mot de passe est sécurisée"""
        from config.security import SecurityConfig

        config = SecurityConfig()

        assert config.password.min_length >= 12
        assert config.password.require_uppercase is True
        assert config.password.require_lowercase is True
        assert config.password.require_digits is True
        assert config.password.require_special is True
        assert config.password.password_history_count >= 10

    def test_session_config_security(self):
        """Test que la config session est sécurisée"""
        from config.security import SecurityConfig

        config = SecurityConfig()

        assert config.session.access_token_expire_minutes <= 30
        assert config.session.enable_token_rotation is True
        assert config.session.enable_hijack_detection is True
        assert config.session.max_concurrent_sessions <= 10

    def test_tls_config_security(self):
        """Test que la config TLS est sécurisée"""
        from config.security import SecurityConfig

        config = SecurityConfig()

        assert config.tls.min_version in ("TLSv1.2", "TLSv1.3")
        assert config.tls.enable_hsts is True
        assert config.tls.hsts_max_age >= 31536000

    def test_audit_config_compliance(self):
        """Test que la config audit est conforme"""
        from config.security import SecurityConfig

        config = SecurityConfig()

        # 7 ans de rétention pour conformité fiscale française
        assert config.audit.retention_days >= 365 * 7
        assert config.audit.audit_authentication is True
        assert config.audit.audit_data_modification is True
        assert config.audit.enable_threat_detection is True

    def test_get_security_config(self):
        """Test fonction get_security_config"""
        from config.security import get_security_config, init_security_config

        # Initialiser pour le test
        init_security_config("development")
        config = get_security_config()

        assert config is not None
        assert config.environment.value == "development"

    def test_compliance_config(self):
        """Test configuration conformité"""
        from config.security import SecurityConfig

        config = SecurityConfig()

        assert config.compliance.enable_rgpd is True
        assert config.compliance.enable_nf525 is True
        assert config.compliance.data_retention_years >= 10
        assert config.compliance.enable_hash_chain is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
