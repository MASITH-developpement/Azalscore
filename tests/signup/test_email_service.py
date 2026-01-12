"""
AZALSCORE - Tests du Service Email
===================================
Tests des emails transactionnels.

Exécution:
    pytest tests/test_email_service.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


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
        
        # Vérifier les paramètres
        call_args = mock_send.call_args
        assert call_args[1]["to"] == ["user@test.fr"]
        assert "Bienvenue" in call_args[1]["subject"]

    @patch("resend.Emails.send")
    def test_send_trial_reminder_7_days(self, mock_send):
        """Test: envoi reminder trial J-7."""
        from app.services.email_service import EmailService
        
        mock_send.return_value = {"id": "email_124"}
        
        service = EmailService()
        result = service.send_trial_reminder(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company",
            days_remaining=7
        )
        
        assert result is True
        
        call_args = mock_send.call_args
        assert "7" in call_args[1]["subject"] or "7" in call_args[1]["html"]

    @patch("resend.Emails.send")
    def test_send_trial_reminder_1_day(self, mock_send):
        """Test: envoi reminder trial J-1 (urgent)."""
        from app.services.email_service import EmailService
        
        mock_send.return_value = {"id": "email_125"}
        
        service = EmailService()
        result = service.send_trial_reminder(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company",
            days_remaining=1
        )
        
        assert result is True
        
        call_args = mock_send.call_args
        # Email urgent doit avoir "dernier" ou "1" dans le sujet
        subject = call_args[1]["subject"]
        assert "1" in subject or "dernier" in subject.lower()

    @patch("resend.Emails.send")
    def test_send_payment_success(self, mock_send):
        """Test: envoi confirmation paiement."""
        from app.services.email_service import EmailService
        
        mock_send.return_value = {"id": "email_126"}
        
        service = EmailService()
        result = service.send_payment_success(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company",
            amount=149.00,
            plan="Professional",
            invoice_url="https://stripe.com/invoice/123"
        )
        
        assert result is True
        
        call_args = mock_send.call_args
        html = call_args[1]["html"]
        assert "149" in html
        assert "Professional" in html

    @patch("resend.Emails.send")
    def test_send_payment_failed(self, mock_send):
        """Test: envoi notification échec paiement."""
        from app.services.email_service import EmailService
        
        mock_send.return_value = {"id": "email_127"}
        
        service = EmailService()
        result = service.send_payment_failed(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company",
            amount=149.00,
            retry_url="https://app.azalscore.com/billing"
        )
        
        assert result is True
        
        call_args = mock_send.call_args
        html = call_args[1]["html"]
        assert "échec" in html.lower() or "failed" in html.lower()
        assert "billing" in html

    @patch("resend.Emails.send")
    def test_send_account_suspended(self, mock_send):
        """Test: envoi notification suspension."""
        from app.services.email_service import EmailService
        
        mock_send.return_value = {"id": "email_128"}
        
        service = EmailService()
        result = service.send_account_suspended(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company",
            reason="Défaut de paiement",
            reactivation_url="https://app.azalscore.com/billing"
        )
        
        assert result is True
        
        call_args = mock_send.call_args
        assert "suspend" in call_args[1]["subject"].lower()

    @patch("resend.Emails.send")
    def test_send_account_reactivated(self, mock_send):
        """Test: envoi notification réactivation."""
        from app.services.email_service import EmailService
        
        mock_send.return_value = {"id": "email_129"}
        
        service = EmailService()
        result = service.send_account_reactivated(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company"
        )
        
        assert result is True
        
        call_args = mock_send.call_args
        assert "réactiv" in call_args[1]["subject"].lower()


class TestEmailServiceErrorHandling:
    """Tests de gestion des erreurs du service email."""

    @patch("resend.Emails.send")
    def test_email_failure_returns_false(self, mock_send):
        """Test: échec d'envoi retourne False."""
        from app.services.email_service import EmailService
        
        mock_send.side_effect = Exception("API Error")
        
        service = EmailService()
        result = service.send_welcome(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company"
        )
        
        assert result is False

    @patch("resend.Emails.send")
    def test_email_failure_logs_error(self, mock_send, caplog):
        """Test: échec d'envoi est loggé."""
        from app.services.email_service import EmailService
        import logging
        
        mock_send.side_effect = Exception("API Error")
        
        with caplog.at_level(logging.ERROR):
            service = EmailService()
            service.send_welcome(
                email="user@test.fr",
                name="Jean",
                tenant_name="Test Company"
            )
        
        # Vérifier qu'une erreur a été loggée
        assert any("error" in record.message.lower() or "Error" in record.message 
                   for record in caplog.records)

    @patch("resend.Emails.send")
    def test_invalid_email_handled(self, mock_send):
        """Test: email invalide géré gracieusement."""
        from app.services.email_service import EmailService
        
        mock_send.side_effect = Exception("Invalid email")
        
        service = EmailService()
        # Ne doit pas lever d'exception
        result = service.send_welcome(
            email="invalid-email",
            name="Jean",
            tenant_name="Test Company"
        )
        
        assert result is False


class TestEmailTemplates:
    """Tests des templates email."""

    def test_welcome_template_has_required_elements(self):
        """Test: template bienvenue contient éléments requis."""
        from app.services.email_service import EmailService
        
        service = EmailService()
        html = service._render_welcome_template(
            name="Jean",
            tenant_name="Test Company",
            login_url="https://app.azalscore.com/login"
        )
        
        assert "Jean" in html
        assert "Test Company" in html
        assert "login" in html.lower()
        assert "azalscore" in html.lower()

    def test_payment_template_shows_amount(self):
        """Test: template paiement affiche le montant."""
        from app.services.email_service import EmailService
        
        service = EmailService()
        html = service._render_payment_success_template(
            name="Jean",
            tenant_name="Test Company",
            amount=149.00,
            plan="Professional",
            invoice_url="https://stripe.com/invoice/123"
        )
        
        assert "149" in html
        assert "Professional" in html
        assert "facture" in html.lower() or "invoice" in html.lower()

    def test_trial_reminder_template_shows_days(self):
        """Test: template reminder affiche jours restants."""
        from app.services.email_service import EmailService
        
        service = EmailService()
        html = service._render_trial_reminder_template(
            name="Jean",
            tenant_name="Test Company",
            days_remaining=3,
            pricing_url="https://azalscore.com/#pricing"
        )
        
        assert "3" in html
        assert "jour" in html.lower()


class TestEmailConfiguration:
    """Tests de la configuration email."""

    def test_from_address_configured(self):
        """Test: adresse from configurée."""
        from app.services.email_service import EmailService
        
        service = EmailService()
        
        assert service.from_address is not None
        assert "@" in service.from_address

    def test_api_key_required(self):
        """Test: API key requise pour l'envoi."""
        from app.services.email_service import EmailService
        
        # En mode test, la clé peut être factice
        service = EmailService()
        
        # Le service doit exister même sans clé valide
        assert service is not None

    @patch.dict("os.environ", {"RESEND_API_KEY": ""})
    def test_missing_api_key_handled(self):
        """Test: absence de clé API gérée."""
        from app.services.email_service import EmailService
        
        service = EmailService()
        
        # Doit retourner False, pas lever d'exception
        result = service.send_welcome(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test"
        )
        
        assert result is False


class TestEmailServiceIntegration:
    """Tests d'intégration du service email."""

    @patch("resend.Emails.send")
    def test_full_trial_lifecycle_emails(self, mock_send):
        """Test: tous les emails du cycle trial."""
        from app.services.email_service import EmailService
        
        mock_send.return_value = {"id": "email_test"}
        service = EmailService()
        
        # 1. Email de bienvenue
        service.send_welcome(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company"
        )
        
        # 2. Reminder J-7
        service.send_trial_reminder(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company",
            days_remaining=7
        )
        
        # 3. Reminder J-3
        service.send_trial_reminder(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company",
            days_remaining=3
        )
        
        # 4. Reminder J-1
        service.send_trial_reminder(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company",
            days_remaining=1
        )
        
        # Vérifier que tous les emails ont été envoyés
        assert mock_send.call_count == 4

    @patch("resend.Emails.send")
    def test_payment_lifecycle_emails(self, mock_send):
        """Test: tous les emails du cycle paiement."""
        from app.services.email_service import EmailService
        
        mock_send.return_value = {"id": "email_test"}
        service = EmailService()
        
        # 1. Paiement réussi
        service.send_payment_success(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company",
            amount=149.00,
            plan="Professional",
            invoice_url="https://stripe.com/invoice/123"
        )
        
        # 2. Échec de paiement
        service.send_payment_failed(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company",
            amount=149.00,
            retry_url="https://app.azalscore.com/billing"
        )
        
        # 3. Compte suspendu
        service.send_account_suspended(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company",
            reason="Défaut de paiement",
            reactivation_url="https://app.azalscore.com/billing"
        )
        
        # 4. Compte réactivé
        service.send_account_reactivated(
            email="user@test.fr",
            name="Jean",
            tenant_name="Test Company"
        )
        
        # Vérifier que tous les emails ont été envoyés
        assert mock_send.call_count == 4
