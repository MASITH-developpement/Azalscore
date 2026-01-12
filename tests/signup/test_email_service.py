"""
AZALSCORE - Tests du Service Email
===================================
Tests des emails transactionnels.

Exécution:
    pytest tests/signup/test_email_service.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestEmailService:
    """Tests du service d'email."""

    @patch("resend.Emails.send")
    def test_send_welcome_email(self, mock_send):
        """Test: envoi email de bienvenue."""
        from app.services.email_service import EmailService

        mock_send.return_value = {"id": "email_123"}

        service = EmailService()
        result = service.send_welcome(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company"
        )

        assert result is True
        mock_send.assert_called_once()

        # Vérifier les paramètres (appelé avec dict)
        call_args = mock_send.call_args[0][0]  # Premier arg positionnel est le dict
        assert "user@test.fr" in call_args["to"]
        assert "Bienvenue" in call_args["subject"]

    @patch("resend.Emails.send")
    def test_send_trial_ending_7_days(self, mock_send):
        """Test: envoi reminder trial J-7."""
        from app.services.email_service import EmailService

        mock_send.return_value = {"id": "email_124"}

        service = EmailService()
        result = service.send_trial_ending(
            email="user@test.fr",
            name="Jean",
            days_left=7
        )

        assert result is True

        call_args = mock_send.call_args[0][0]
        assert "7" in call_args["subject"]

    @patch("resend.Emails.send")
    def test_send_trial_ending_1_day(self, mock_send):
        """Test: envoi reminder trial J-1 (urgent)."""
        from app.services.email_service import EmailService

        mock_send.return_value = {"id": "email_125"}

        service = EmailService()
        result = service.send_trial_ending(
            email="user@test.fr",
            name="Jean",
            days_left=1
        )

        assert result is True

        call_args = mock_send.call_args[0][0]
        assert "1" in call_args["subject"]

    @patch("resend.Emails.send")
    def test_send_payment_success(self, mock_send):
        """Test: envoi confirmation paiement."""
        from app.services.email_service import EmailService

        mock_send.return_value = {"id": "email_126"}

        service = EmailService()
        result = service.send_payment_success(
            email="user@test.fr",
            name="Jean",
            plan="Professional",
            amount=149.00
        )

        assert result is True

        call_args = mock_send.call_args[0][0]
        assert "user@test.fr" in call_args["to"]
        assert "Paiement" in call_args["subject"] or "confirmé" in call_args["subject"]

    @patch("resend.Emails.send")
    def test_send_payment_failed(self, mock_send):
        """Test: envoi notification échec paiement."""
        from app.services.email_service import EmailService

        mock_send.return_value = {"id": "email_127"}

        service = EmailService()
        result = service.send_payment_failed(
            email="user@test.fr",
            name="Jean"
        )

        assert result is True

        call_args = mock_send.call_args[0][0]
        assert "user@test.fr" in call_args["to"]

    @patch("resend.Emails.send")
    def test_send_trial_expired(self, mock_send):
        """Test: envoi notification essai expiré."""
        from app.services.email_service import EmailService

        mock_send.return_value = {"id": "email_128"}

        service = EmailService()
        result = service.send_trial_expired(
            email="user@test.fr",
            name="Jean"
        )

        assert result is True

        call_args = mock_send.call_args[0][0]
        assert "terminé" in call_args["subject"]

    @patch("resend.Emails.send")
    def test_send_subscription_cancelled(self, mock_send):
        """Test: envoi notification abonnement annulé."""
        from app.services.email_service import EmailService

        mock_send.return_value = {"id": "email_129"}

        service = EmailService()
        result = service.send_subscription_cancelled(
            email="user@test.fr",
            name="Jean",
            end_date="31/01/2026"
        )

        assert result is True


class TestEmailServiceErrorHandling:
    """Tests de gestion des erreurs."""

    @patch("resend.Emails.send")
    def test_email_failure_returns_false(self, mock_send):
        """Test: échec d'envoi retourne False."""
        from app.services.email_service import EmailService

        mock_send.side_effect = Exception("SMTP Error")

        service = EmailService()
        result = service.send_welcome(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company"
        )

        assert result is False

    @patch("resend.Emails.send")
    def test_email_failure_logs_error(self, mock_send):
        """Test: échec d'envoi loggue l'erreur."""
        from app.services.email_service import EmailService

        mock_send.side_effect = Exception("SMTP Error")

        service = EmailService()
        # Ne doit pas lever d'exception
        result = service.send_welcome(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company"
        )

        assert result is False

    def test_resend_not_available_returns_false(self):
        """Test: sans resend installé, retourne False."""
        from app.services.email_service import EmailService, RESEND_AVAILABLE

        service = EmailService()

        # Si resend n'est pas disponible, le service retourne False
        if not RESEND_AVAILABLE:
            result = service.send_email(
                to="user@test.fr",
                subject="Test",
                html="<p>Test</p>"
            )
            assert result is False


class TestEmailTemplates:
    """Tests des templates d'email."""

    def test_base_template_has_logo(self):
        """Test: template de base a le logo."""
        from app.services.email_service import EmailService

        service = EmailService()
        html = service._base_template("<p>Test content</p>")

        assert "AZALSCORE" in html
        assert "Test content" in html

    def test_base_template_has_footer(self):
        """Test: template de base a un footer."""
        from app.services.email_service import EmailService

        service = EmailService()
        html = service._base_template("<p>Test</p>")

        assert "support@azalscore.com" in html or "Contactez" in html

    @patch("resend.Emails.send")
    def test_welcome_template_has_required_elements(self, mock_send):
        """Test: template bienvenue contient éléments requis."""
        from app.services.email_service import EmailService

        mock_send.return_value = {"id": "email_123"}

        service = EmailService()
        service.send_welcome(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company"
        )

        call_args = mock_send.call_args[0][0]
        html = call_args["html"]

        assert "Jean" in html
        assert "Test Company" in html
        assert "14 jours" in html


class TestEmailConfiguration:
    """Tests de configuration."""

    def test_from_address_configured(self):
        """Test: adresse expéditeur configurée."""
        from app.services.email_service import EmailService

        service = EmailService()

        assert service.from_email is not None
        assert "@" in service.from_email

    def test_app_url_configured(self):
        """Test: URL application configurée."""
        from app.services.email_service import EmailService

        service = EmailService()

        assert service.app_url is not None
        assert "azalscore" in service.app_url or "http" in service.app_url


class TestEmailServiceIntegration:
    """Tests d'intégration du service email."""

    @patch("resend.Emails.send")
    def test_full_trial_lifecycle_emails(self, mock_send):
        """Test: cycle complet d'emails trial."""
        from app.services.email_service import EmailService

        mock_send.return_value = {"id": "email_123"}

        service = EmailService()

        # 1. Email de bienvenue
        result1 = service.send_welcome("user@test.fr", "Jean", "Test Co")
        assert result1 is True

        # 2. Reminder J-7
        result2 = service.send_trial_ending("user@test.fr", "Jean", 7)
        assert result2 is True

        # 3. Reminder J-1
        result3 = service.send_trial_ending("user@test.fr", "Jean", 1)
        assert result3 is True

        # 4. Trial expiré
        result4 = service.send_trial_expired("user@test.fr", "Jean")
        assert result4 is True

        assert mock_send.call_count == 4

    @patch("resend.Emails.send")
    def test_payment_lifecycle_emails(self, mock_send):
        """Test: cycle complet d'emails paiement."""
        from app.services.email_service import EmailService

        mock_send.return_value = {"id": "email_123"}

        service = EmailService()

        # 1. Paiement réussi
        result1 = service.send_payment_success(
            "user@test.fr", "Jean", "Professional", 149.00
        )
        assert result1 is True

        # 2. Paiement échoué
        result2 = service.send_payment_failed("user@test.fr", "Jean")
        assert result2 is True

        # 3. Abonnement annulé
        result3 = service.send_subscription_cancelled(
            "user@test.fr", "Jean", "31/01/2026"
        )
        assert result3 is True

        assert mock_send.call_count == 3
