"""
AZALS - Service Email Transactionnel
=====================================
Utilise Resend pour l'envoi d'emails.
pip install resend
"""

import os
from datetime import datetime

try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EmailService:
    """Service d'envoi d'emails transactionnels."""

    def __init__(self):
        if RESEND_AVAILABLE:
            resend.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("EMAIL_FROM", "noreply@azalscore.com")
        self.from_name = "AZALSCORE"
        self.app_url = os.getenv("APP_URL", "https://app.azalscore.com")

    def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: str | None = None
    ) -> bool:
        """Envoyer un email."""
        if not RESEND_AVAILABLE:
            logger.warning("[EMAIL] Resend non disponible")
            return False

        try:
            resend.Emails.send({
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to],
                "subject": subject,
                "html": html,
                "text": text or ""
            })
            logger.info(f"[EMAIL] Envoyé à {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"[EMAIL] Erreur: {e}")
            return False

    def _base_template(self, content: str) -> str:
        """Template de base pour tous les emails."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #f8f9fa;
                    margin: 0;
                    padding: 40px 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 16px;
                    padding: 40px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #6366f1;
                    margin-bottom: 32px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                .logo span {{ color: #6366f1; }}
                h1 {{
                    color: #1a1a2e;
                    font-size: 28px;
                    margin: 0 0 16px 0;
                    line-height: 1.3;
                }}
                p {{
                    color: #4a4a4a;
                    line-height: 1.7;
                    margin: 0 0 16px 0;
                }}
                .btn {{
                    display: inline-block;
                    padding: 14px 28px;
                    background: linear-gradient(135deg, #6366f1, #8b5cf6);
                    color: white !important;
                    text-decoration: none;
                    border-radius: 10px;
                    font-weight: 600;
                    margin: 24px 0;
                }}
                .btn:hover {{ opacity: 0.9; }}
                .box {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 12px;
                    margin: 20px 0;
                }}
                .box p {{ margin: 8px 0; }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 24px;
                    border-top: 1px solid #eee;
                    color: #888;
                    font-size: 14px;
                }}
                .footer a {{ color: #6366f1; text-decoration: none; }}
                ul {{ color: #4a4a4a; line-height: 2; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo"><span>◆</span> AZALSCORE</div>
                {content}
                <div class="footer">
                    <p>Besoin d'aide ? <a href="mailto:support@azalscore.com">Contactez-nous</a></p>
                    <p style="margin-top: 16px;">© {datetime.now().year} AZALSCORE - L'ERP nouvelle génération</p>
                </div>
            </div>
        </body>
        </html>
        """

    # ========================================================================
    # TEMPLATES D'EMAILS
    # ========================================================================

    def send_welcome(self, email: str, name: str, tenant_name: str) -> bool:
        """Email de bienvenue après inscription."""
        content = f"""
        <h1>Bienvenue {name} !</h1>
        <p>Votre compte <strong>{tenant_name}</strong> est maintenant actif.</p>
        <p>Vous bénéficiez de <strong>14 jours d'essai gratuit</strong> avec accès à toutes les fonctionnalités.</p>
        <p>Voici les prochaines étapes :</p>
        <ul>
            <li>Configurez les informations de votre entreprise</li>
            <li>Invitez vos collaborateurs</li>
            <li>Importez vos données existantes</li>
        </ul>
        <a href="{self.app_url}/onboarding" class="btn">Commencer la configuration →</a>
        """
        return self.send_email(
            to=email,
            subject=f"Bienvenue sur AZALSCORE, {name} !",
            html=self._base_template(content)
        )

    def send_trial_ending(self, email: str, name: str, days_left: int) -> bool:
        """Email de rappel fin d'essai."""
        urgency = "⏰" if days_left <= 3 else "📅"
        content = f"""
        <h1>{urgency} Votre essai se termine bientôt</h1>
        <p>Bonjour {name},</p>
        <p>Il vous reste <strong>{days_left} jour{"s" if days_left > 1 else ""}</strong> pour profiter de votre essai gratuit AZALSCORE.</p>
        <p>Pour continuer à utiliser votre ERP sans interruption, passez à un abonnement dès maintenant :</p>
        <a href="{self.app_url}/billing/upgrade" class="btn">Choisir mon plan →</a>
        <p style="color: #888; font-size: 14px; margin-top: 24px;">
            Des questions ? Répondez à cet email, nous sommes là pour vous aider.
        </p>
        """
        return self.send_email(
            to=email,
            subject=f"⏰ Plus que {days_left} jours d'essai AZALSCORE",
            html=self._base_template(content)
        )

    def send_trial_expired(self, email: str, name: str) -> bool:
        """Email de fin d'essai."""
        content = f"""
        <h1>Votre essai est terminé</h1>
        <p>Bonjour {name},</p>
        <p>Votre période d'essai AZALSCORE est arrivée à son terme.</p>
        <p>Vos données sont conservées pendant <strong>30 jours</strong>. Pour y accéder à nouveau, souscrivez un abonnement :</p>
        <a href="{self.app_url}/billing/upgrade" class="btn">Réactiver mon compte →</a>
        <p style="color: #888; font-size: 14px; margin-top: 24px;">
            Besoin de plus de temps pour évaluer ? Contactez-nous, nous pouvons prolonger votre essai.
        </p>
        """
        return self.send_email(
            to=email,
            subject="Votre essai AZALSCORE est terminé",
            html=self._base_template(content)
        )

    def send_payment_success(
        self,
        email: str,
        name: str,
        plan: str,
        amount: float
    ) -> bool:
        """Email de confirmation de paiement."""
        content = f"""
        <h1 style="color: #10b981;">✓ Paiement confirmé</h1>
        <p>Bonjour {name},</p>
        <p>Nous confirmons la réception de votre paiement :</p>
        <div class="box">
            <p><strong>Plan :</strong> {plan}</p>
            <p><strong>Montant :</strong> {amount:.2f} €</p>
            <p><strong>Date :</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
        </div>
        <p>Votre facture est disponible dans votre espace client.</p>
        <a href="{self.app_url}/billing/invoices" class="btn">Voir mes factures →</a>
        """
        return self.send_email(
            to=email,
            subject="✅ Paiement confirmé - AZALSCORE",
            html=self._base_template(content)
        )

    def send_payment_failed(self, email: str, name: str) -> bool:
        """Email d'échec de paiement."""
        content = f"""
        <h1 style="color: #ef4444;">⚠️ Problème de paiement</h1>
        <p>Bonjour {name},</p>
        <p>Nous n'avons pas pu traiter votre paiement. Cela peut arriver pour plusieurs raisons :</p>
        <ul>
            <li>Carte expirée ou fonds insuffisants</li>
            <li>Limite de transaction atteinte</li>
            <li>Problème technique temporaire</li>
        </ul>
        <p>Pour éviter toute interruption de service, veuillez mettre à jour vos informations de paiement :</p>
        <a href="{self.app_url}/billing/payment-method" class="btn">Mettre à jour ma carte →</a>
        <p style="color: #888; font-size: 14px; margin-top: 24px;">
            Si le problème persiste, contactez votre banque ou notre support.
        </p>
        """
        return self.send_email(
            to=email,
            subject="⚠️ Échec de paiement - AZALSCORE",
            html=self._base_template(content)
        )

    def send_subscription_cancelled(self, email: str, name: str, end_date: str) -> bool:
        """Email de confirmation d'annulation."""
        content = f"""
        <h1>Abonnement annulé</h1>
        <p>Bonjour {name},</p>
        <p>Comme demandé, votre abonnement AZALSCORE a été annulé.</p>
        <p>Vous conservez l'accès à toutes les fonctionnalités jusqu'au <strong>{end_date}</strong>.</p>
        <p>Vos données seront conservées 30 jours après cette date, puis supprimées définitivement.</p>
        <p style="margin-top: 24px;">Nous espérons vous revoir bientôt !</p>
        <a href="{self.app_url}/billing/reactivate" class="btn">Réactiver mon abonnement →</a>
        """
        return self.send_email(
            to=email,
            subject="Confirmation d'annulation - AZALSCORE",
            html=self._base_template(content)
        )

    def send_invitation(
        self,
        email: str,
        inviter_name: str,
        tenant_name: str,
        invite_url: str
    ) -> bool:
        """Email d'invitation à rejoindre un tenant."""
        content = f"""
        <h1>Vous êtes invité(e) !</h1>
        <p><strong>{inviter_name}</strong> vous invite à rejoindre <strong>{tenant_name}</strong> sur AZALSCORE.</p>
        <p>AZALSCORE est une solution ERP complète pour gérer votre entreprise : ventes, comptabilité, RH, production...</p>
        <a href="{invite_url}" class="btn">Accepter l'invitation →</a>
        <p style="color: #888; font-size: 14px; margin-top: 24px;">
            Ce lien est valable 7 jours. Si vous n'êtes pas concerné(e) par cet email, ignorez-le simplement.
        </p>
        """
        return self.send_email(
            to=email,
            subject=f"{inviter_name} vous invite sur AZALSCORE",
            html=self._base_template(content)
        )

    def send_password_reset(self, email: str, name: str, reset_url: str) -> bool:
        """Email de réinitialisation de mot de passe."""
        content = f"""
        <h1>Réinitialisation du mot de passe</h1>
        <p>Bonjour {name},</p>
        <p>Vous avez demandé à réinitialiser votre mot de passe AZALSCORE.</p>
        <p>Cliquez sur le bouton ci-dessous pour choisir un nouveau mot de passe :</p>
        <a href="{reset_url}" class="btn">Réinitialiser mon mot de passe →</a>
        <p style="color: #888; font-size: 14px; margin-top: 24px;">
            Ce lien expire dans 1 heure. Si vous n'avez pas fait cette demande, ignorez cet email.
        </p>
        """
        return self.send_email(
            to=email,
            subject="Réinitialisation de votre mot de passe AZALSCORE",
            html=self._base_template(content)
        )

    def send_2fa_enabled(self, email: str, name: str) -> bool:
        """Email de confirmation d'activation 2FA."""
        content = f"""
        <h1 style="color: #10b981;">✓ Double authentification activée</h1>
        <p>Bonjour {name},</p>
        <p>La double authentification (2FA) a été activée sur votre compte AZALSCORE.</p>
        <p>Vous devrez désormais saisir un code de votre application d'authentification en plus de votre mot de passe.</p>
        <div class="box">
            <p><strong>⚠️ Important :</strong> Conservez vos codes de récupération en lieu sûr. Ils vous permettront d'accéder à votre compte si vous perdez votre téléphone.</p>
        </div>
        <p style="color: #888; font-size: 14px; margin-top: 24px;">
            Si vous n'êtes pas à l'origine de cette action, contactez immédiatement notre support.
        </p>
        """
        return self.send_email(
            to=email,
            subject="🔐 Double authentification activée - AZALSCORE",
            html=self._base_template(content)
        )


# Singleton
_email_service = None

def get_email_service() -> EmailService:
    """Récupérer l'instance du service email."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
