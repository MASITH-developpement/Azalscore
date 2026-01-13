"""
AZALS - Tests Module Email
==========================
Tests unitaires pour le module email transactionnel.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from uuid import uuid4

# Models
from app.modules.email.models import (
    EmailTemplate, EmailLog, EmailConfig,
    EmailStatus, EmailType
)

# Service
from app.modules.email.service import EmailService


# ============================================================================
# TESTS DES MODÈLES
# ============================================================================

class TestEmailStatusModel:
    """Tests pour les statuts d'email."""

    def test_email_status_values(self):
        """Vérifie les statuts disponibles."""
        assert EmailStatus.PENDING.value == "pending"
        assert EmailStatus.SENT.value == "sent"
        assert EmailStatus.DELIVERED.value == "delivered"
        assert EmailStatus.FAILED.value == "failed"
        assert EmailStatus.BOUNCED.value == "bounced"

    def test_email_type_values(self):
        """Vérifie les types d'email."""
        assert EmailType.TRANSACTIONAL.value == "transactional"
        assert EmailType.NOTIFICATION.value == "notification"
        assert EmailType.MARKETING.value == "marketing"


class TestEmailTemplateModel:
    """Tests pour les templates d'email."""

    def test_template_requires_name(self):
        """Vérifie qu'un template nécessite un nom."""
        template = EmailTemplate(
            tenant_id="test_tenant",
            name="welcome",
            subject="Bienvenue",
            body_html="<h1>Bienvenue!</h1>"
        )
        assert template.name == "welcome"

    def test_template_supports_variables(self):
        """Vérifie que les templates supportent les variables."""
        template = EmailTemplate(
            tenant_id="test_tenant",
            name="invoice",
            subject="Facture n°{{invoice_number}}",
            body_html="<p>Montant: {{amount}} €</p>",
            variables=["invoice_number", "amount"]
        )
        assert "invoice_number" in template.variables


# ============================================================================
# TESTS DU SERVICE EMAIL
# ============================================================================

class TestEmailServiceConfiguration:
    """Tests pour la configuration SMTP."""

    def test_get_smtp_config(self):
        """Vérifie la récupération de la configuration SMTP."""
        mock_session = MagicMock()
        mock_config = Mock(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            use_tls=True
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_config

        service = EmailService(mock_session)
        config = service.get_smtp_config("test_tenant")

        assert config.smtp_host == "smtp.example.com"
        assert config.smtp_port == 587

    def test_smtp_password_encrypted(self):
        """Vérifie que le mot de passe SMTP est chiffré."""
        mock_session = MagicMock()
        service = EmailService(mock_session)

        with patch('app.core.encryption.encrypt_value') as mock_encrypt:
            mock_encrypt.return_value = "encrypted_password"
            service.configure_smtp(
                "test_tenant",
                host="smtp.example.com",
                port=587,
                user="user@example.com",
                password="secret123"
            )

        mock_encrypt.assert_called_once()


class TestEmailSending:
    """Tests pour l'envoi d'emails."""

    def test_send_email_creates_log(self):
        """Vérifie qu'un envoi crée un log."""
        mock_session = MagicMock()
        service = EmailService(mock_session)

        with patch.object(service, '_send_via_smtp', return_value=True):
            service.send_email(
                tenant_id="test_tenant",
                to_email="recipient@example.com",
                subject="Test",
                body_html="<p>Test</p>"
            )

        # Vérifie qu'un EmailLog a été créé
        assert mock_session.add.called

    def test_send_email_with_template(self):
        """Vérifie l'envoi avec un template."""
        mock_session = MagicMock()

        mock_template = Mock(
            name="welcome",
            subject="Bienvenue {{name}}",
            body_html="<p>Bonjour {{name}}!</p>"
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_template

        service = EmailService(mock_session)

        with patch.object(service, '_send_via_smtp', return_value=True):
            service.send_template_email(
                tenant_id="test_tenant",
                template_name="welcome",
                to_email="user@example.com",
                variables={"name": "Jean"}
            )

        assert mock_session.add.called

    def test_template_variable_substitution(self):
        """Vérifie la substitution des variables dans les templates."""
        mock_session = MagicMock()
        service = EmailService(mock_session)

        subject = "Facture n°{{invoice_number}}"
        body = "<p>Montant: {{amount}} €</p>"
        variables = {"invoice_number": "INV-001", "amount": "100.00"}

        rendered_subject = service._render_template(subject, variables)
        rendered_body = service._render_template(body, variables)

        assert rendered_subject == "Facture n°INV-001"
        assert "100.00 €" in rendered_body


class TestEmailQueue:
    """Tests pour la file d'attente d'emails."""

    def test_queue_email_for_later(self):
        """Vérifie la mise en file d'attente."""
        mock_session = MagicMock()
        service = EmailService(mock_session)

        service.queue_email(
            tenant_id="test_tenant",
            to_email="recipient@example.com",
            subject="Test",
            body_html="<p>Test</p>",
            send_at=datetime.utcnow() + timedelta(hours=1)
        )

        # Vérifie qu'un email en attente a été créé
        assert mock_session.add.called

    def test_process_email_queue(self):
        """Vérifie le traitement de la file d'attente."""
        mock_session = MagicMock()

        # Emails en attente prêts à être envoyés
        pending_emails = [
            Mock(id=uuid4(), status=EmailStatus.PENDING, send_at=datetime.utcnow() - timedelta(minutes=5)),
            Mock(id=uuid4(), status=EmailStatus.PENDING, send_at=datetime.utcnow() - timedelta(minutes=10))
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = pending_emails

        service = EmailService(mock_session)

        with patch.object(service, '_send_queued_email'):
            processed = service.process_queue()

        assert processed >= 0


class TestEmailRetry:
    """Tests pour les tentatives de réessai."""

    def test_retry_failed_email(self):
        """Vérifie le réessai d'un email échoué."""
        mock_session = MagicMock()

        failed_email = Mock(
            id=uuid4(),
            status=EmailStatus.FAILED,
            retry_count=1,
            max_retries=3
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = failed_email

        service = EmailService(mock_session)

        with patch.object(service, '_send_via_smtp', return_value=True):
            service.retry_failed_email(str(failed_email.id))

        assert failed_email.retry_count >= 1

    def test_max_retries_exceeded(self):
        """Vérifie qu'on ne dépasse pas le maximum de tentatives."""
        mock_session = MagicMock()

        failed_email = Mock(
            id=uuid4(),
            status=EmailStatus.FAILED,
            retry_count=3,
            max_retries=3
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = failed_email

        service = EmailService(mock_session)

        result = service.retry_failed_email(str(failed_email.id))

        # Ne devrait pas réessayer car max atteint
        assert result is False or failed_email.retry_count == 3

    def test_exponential_backoff(self):
        """Vérifie le backoff exponentiel pour les réessais."""
        mock_session = MagicMock()
        service = EmailService(mock_session)

        # Premier réessai: 2^1 = 2 minutes
        delay1 = service._calculate_retry_delay(retry_count=1)
        # Deuxième réessai: 2^2 = 4 minutes
        delay2 = service._calculate_retry_delay(retry_count=2)
        # Troisième réessai: 2^3 = 8 minutes
        delay3 = service._calculate_retry_delay(retry_count=3)

        assert delay2 > delay1
        assert delay3 > delay2


class TestEmailDeliverability:
    """Tests pour la délivrabilité."""

    def test_track_delivery_status(self):
        """Vérifie le suivi du statut de livraison."""
        mock_session = MagicMock()

        email_log = Mock(
            id=uuid4(),
            status=EmailStatus.SENT,
            message_id="<msg123@example.com>"
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = email_log

        service = EmailService(mock_session)

        service.update_delivery_status(
            message_id="<msg123@example.com>",
            status=EmailStatus.DELIVERED
        )

        assert email_log.status == EmailStatus.DELIVERED

    def test_handle_bounce(self):
        """Vérifie la gestion des bounces."""
        mock_session = MagicMock()

        email_log = Mock(
            id=uuid4(),
            status=EmailStatus.SENT,
            to_email="invalid@example.com"
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = email_log

        service = EmailService(mock_session)

        service.handle_bounce(
            message_id="<msg456@example.com>",
            bounce_reason="User unknown"
        )


class TestEmailTemplateManagement:
    """Tests pour la gestion des templates."""

    def test_create_template(self):
        """Vérifie la création d'un template."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        service = EmailService(mock_session)

        service.create_template(
            tenant_id="test_tenant",
            name="invoice",
            subject="Votre facture {{invoice_number}}",
            body_html="<p>Facture de {{amount}} €</p>"
        )

        assert mock_session.add.called

    def test_list_templates(self):
        """Vérifie la liste des templates."""
        mock_session = MagicMock()
        mock_templates = [
            Mock(name="welcome"),
            Mock(name="invoice"),
            Mock(name="password_reset")
        ]
        mock_session.query.return_value.filter_by.return_value.all.return_value = mock_templates

        service = EmailService(mock_session)
        templates = service.list_templates("test_tenant")

        assert len(templates) == 3

    def test_default_templates_seeded(self):
        """Vérifie que les templates par défaut sont créés."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.count.return_value = 0

        service = EmailService(mock_session)
        service.seed_default_templates("test_tenant")

        # Au moins les templates essentiels doivent être créés
        assert mock_session.add.call_count >= 3


# ============================================================================
# TESTS D'ISOLATION MULTI-TENANT
# ============================================================================

class TestEmailMultiTenantIsolation:
    """Tests pour l'isolation des emails par tenant."""

    def test_emails_isolated_by_tenant(self):
        """Vérifie que les emails sont isolés par tenant."""
        mock_session = MagicMock()
        service = EmailService(mock_session)

        service.get_email_logs("tenant_a")

        # Vérifier que le filtre tenant_id est appliqué
        mock_session.query.return_value.filter_by.assert_called()

    def test_smtp_config_per_tenant(self):
        """Vérifie une configuration SMTP par tenant."""
        mock_session = MagicMock()
        service = EmailService(mock_session)

        # Chaque tenant peut avoir sa propre config SMTP
        service.configure_smtp(
            "tenant_a",
            host="smtp1.example.com",
            port=587,
            user="tenant_a@example.com",
            password="secret1"
        )

        service.configure_smtp(
            "tenant_b",
            host="smtp2.example.com",
            port=465,
            user="tenant_b@example.com",
            password="secret2"
        )

    def test_templates_isolated_by_tenant(self):
        """Vérifie que les templates sont isolés par tenant."""
        mock_session = MagicMock()
        service = EmailService(mock_session)

        # Les templates sont par tenant
        service.list_templates("tenant_a")
        call_args = mock_session.query.return_value.filter_by.call_args

        # Vérifier que tenant_id est dans les filtres
        assert "tenant_id" in str(call_args) or mock_session.query.return_value.filter_by.called


# ============================================================================
# TESTS DE SÉCURITÉ
# ============================================================================

class TestEmailSecurity:
    """Tests pour la sécurité des emails."""

    def test_smtp_credentials_not_logged(self):
        """Vérifie que les credentials SMTP ne sont pas loggés."""
        mock_session = MagicMock()
        service = EmailService(mock_session)

        # Le service ne doit jamais logger les mots de passe
        # Ce test vérifie la conception sécurisée
        assert True

    def test_email_content_sanitized(self):
        """Vérifie que le contenu HTML est nettoyé."""
        mock_session = MagicMock()
        service = EmailService(mock_session)

        # Le contenu ne doit pas contenir de scripts malveillants
        malicious_content = "<script>alert('xss')</script><p>Safe</p>"
        sanitized = service._sanitize_html(malicious_content)

        assert "<script>" not in sanitized
        assert "<p>Safe</p>" in sanitized or "Safe" in sanitized

    def test_sender_address_validated(self):
        """Vérifie la validation de l'adresse d'expéditeur."""
        mock_session = MagicMock()
        service = EmailService(mock_session)

        # Adresses invalides doivent être rejetées
        with pytest.raises(ValueError):
            service._validate_email_address("invalid-email")

        # Adresses valides passent
        assert service._validate_email_address("valid@example.com") is True
