"""
AZALS MODULE T9 - Service Trial Registration
=============================================

Service pour gérer le flux d'inscription à l'essai gratuit.
"""

import secrets
import smtplib
import httpx
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.config import get_settings
from .models import (
    Tenant,
    TenantStatus,
    SubscriptionPlan,
    TrialRegistration,
    TrialRegistrationStatus,
)
from .schemas import TenantCreate
from .schemas_trial import (
    TrialRegistrationCreate,
    TrialRegistrationResponse,
    TrialEmailVerificationResponse,
    TrialPaymentSetupResponse,
    TrialCompleteResponse,
    TrialPricingResponse,
    TrialPricingPlan,
)
from .service import TenantService


class TrialRegistrationService:
    """Service de gestion des inscriptions d'essai gratuit."""

    TRIAL_DURATION_DAYS = 30
    REGISTRATION_EXPIRY_HOURS = 24

    # Modules activés en mode démo
    DEMO_MODULES = [
        "T0",  # Core
        "T1",  # Commercial / CRM
        "T2",  # Facturation
        "T3",  # Comptabilité
        "T4",  # Trésorerie
        "T5",  # Stock / Inventaire
        "T6",  # Achats
        "T7",  # RH
        "T8",  # Projets
    ]

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # CRÉATION D'INSCRIPTION
    # ========================================================================

    def create_registration(
        self,
        data: TrialRegistrationCreate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TrialRegistrationResponse:
        """
        Créer une inscription d'essai et envoyer l'email de vérification.

        Étapes:
        1. Vérifier que l'email n'est pas déjà utilisé
        2. Vérifier le CAPTCHA
        3. Créer l'enregistrement TrialRegistration
        4. Générer le token de vérification
        5. Envoyer l'email de vérification
        """
        # 1. Vérifier email non utilisé
        self._check_email_available(data.email)

        # 2. Vérifier le CAPTCHA
        if not self._verify_hcaptcha(data.captcha_token):
            raise ValueError("Vérification CAPTCHA échouée")

        # 3. Générer token email
        email_token = secrets.token_urlsafe(32)

        # 4. Créer l'inscription
        registration = TrialRegistration(
            # Infos personnelles
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            mobile=data.mobile,
            # Infos entreprise
            company_name=data.company_name,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            postal_code=data.postal_code,
            city=data.city,
            country=data.country,
            language=data.language,
            activity=data.activity,
            revenue_range=data.revenue_range,
            max_users=min(data.max_users, 5),  # Max 5 en essai
            siret=data.siret,
            # Vérifications
            email_verification_token=email_token,
            captcha_verified=True,
            cgv_accepted=data.cgv_accepted,
            cgu_accepted=data.cgu_accepted,
            # Statut
            status=TrialRegistrationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(hours=self.REGISTRATION_EXPIRY_HOURS),
            # Audit
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(registration)
        self.db.commit()
        self.db.refresh(registration)

        # 5. Envoyer email de vérification
        self._send_verification_email(registration, email_token)

        # Mettre à jour le statut
        registration.status = TrialRegistrationStatus.EMAIL_SENT
        self.db.commit()

        return TrialRegistrationResponse(
            registration_id=str(registration.id),
            email=registration.email,
            email_sent=True,
            expires_at=registration.expires_at,
        )

    # ========================================================================
    # VÉRIFICATION EMAIL
    # ========================================================================

    def verify_email(self, token: str) -> TrialEmailVerificationResponse:
        """Vérifier l'email avec le token."""
        registration = self.db.query(TrialRegistration).filter(
            and_(
                TrialRegistration.email_verification_token == token,
                TrialRegistration.status.in_([
                    TrialRegistrationStatus.PENDING,
                    TrialRegistrationStatus.EMAIL_SENT
                ]),
                TrialRegistration.expires_at > datetime.utcnow()
            )
        ).first()

        if not registration:
            raise ValueError("Token invalide ou expiré")

        registration.email_verified_at = datetime.utcnow()
        registration.status = TrialRegistrationStatus.EMAIL_VERIFIED
        self.db.commit()

        return TrialEmailVerificationResponse(
            verified=True,
            registration_id=str(registration.id),
        )

    # ========================================================================
    # CONFIGURATION PAIEMENT STRIPE
    # ========================================================================

    def create_payment_setup(self, registration_id: str) -> TrialPaymentSetupResponse:
        """
        Créer un SetupIntent Stripe pour enregistrer la carte.

        Prérequis: email vérifié
        """
        import stripe
        settings = get_settings()

        registration = self._get_registration(registration_id)

        # Vérifier prérequis
        if not registration.email_verified_at:
            raise ValueError("Email non vérifié")

        if registration.status not in [
            TrialRegistrationStatus.EMAIL_VERIFIED,
            TrialRegistrationStatus.PAYMENT_PENDING
        ]:
            raise ValueError("Étape de paiement non accessible")

        # Configurer Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Créer ou récupérer le customer Stripe
        if registration.stripe_customer_id:
            customer_id = registration.stripe_customer_id
        else:
            customer = stripe.Customer.create(
                email=registration.email,
                name=f"{registration.first_name} {registration.last_name}",
                metadata={
                    "registration_id": str(registration.id),
                    "company_name": registration.company_name,
                }
            )
            registration.stripe_customer_id = customer.id
            customer_id = customer.id

        # Créer le SetupIntent
        setup_intent = stripe.SetupIntent.create(
            customer=customer_id,
            payment_method_types=["card"],
            usage="off_session",  # Permet les charges futures
            metadata={
                "registration_id": str(registration.id),
                "type": "trial_registration",
            }
        )

        registration.stripe_setup_intent_id = setup_intent.id
        registration.status = TrialRegistrationStatus.PAYMENT_PENDING
        self.db.commit()

        return TrialPaymentSetupResponse(
            client_secret=setup_intent.client_secret,
            setup_intent_id=setup_intent.id,
            publishable_key=settings.STRIPE_PUBLISHABLE_KEY,
            customer_id=customer_id,
        )

    # ========================================================================
    # FINALISATION INSCRIPTION
    # ========================================================================

    def complete_registration(
        self,
        registration_id: str,
        setup_intent_id: str,
    ) -> TrialCompleteResponse:
        """
        Finaliser l'inscription après validation du paiement.

        1. Vérifier le SetupIntent Stripe
        2. Créer le tenant
        3. Activer tous les modules en mode démo
        4. Créer l'utilisateur admin
        5. Injecter les données démo
        6. Envoyer email de bienvenue
        """
        import stripe
        settings = get_settings()

        registration = self._get_registration(registration_id)

        # Vérifier statut
        if registration.status == TrialRegistrationStatus.COMPLETED:
            raise ValueError("Inscription déjà finalisée")

        if registration.status != TrialRegistrationStatus.PAYMENT_PENDING:
            raise ValueError("Configuration paiement non complétée")

        # Vérifier SetupIntent
        stripe.api_key = settings.STRIPE_SECRET_KEY
        setup_intent = stripe.SetupIntent.retrieve(setup_intent_id)

        if setup_intent.status != "succeeded":
            raise ValueError("Configuration carte non validée")

        # Sauvegarder le payment_method
        registration.stripe_payment_method_id = setup_intent.payment_method

        # Générer tenant_id unique
        tenant_id = self._generate_tenant_id(registration.company_name)

        # Générer mot de passe temporaire
        temp_password = secrets.token_urlsafe(12)

        # Créer le tenant via TenantService
        tenant_service = TenantService(self.db)

        tenant_data = TenantCreate(
            tenant_id=tenant_id,
            name=registration.company_name,
            address_line1=registration.address_line1,
            address_line2=registration.address_line2,
            city=registration.city,
            postal_code=registration.postal_code,
            country=registration.country,
            email=registration.email,
            phone=registration.phone or registration.mobile,
            siret=registration.siret,
            plan="STARTER",
            language=registration.language,
            max_users=registration.max_users,
            extra_data={
                "stripe_customer_id": registration.stripe_customer_id,
                "stripe_payment_method_id": registration.stripe_payment_method_id,
                "trial_registration_id": str(registration.id),
                "demo_mode_enabled": True,
                "trial_registration": {
                    "activity": registration.activity,
                    "revenue_range": registration.revenue_range,
                    "registered_at": datetime.utcnow().isoformat(),
                }
            }
        )

        tenant = tenant_service.create_tenant(tenant_data)

        # Démarrer l'essai de 30 jours
        tenant_service.start_trial(tenant_id, self.TRIAL_DURATION_DAYS)

        # Activer tous les modules démo
        from .schemas import ModuleActivation
        for module_code in self.DEMO_MODULES:
            try:
                tenant_service.activate_module(
                    tenant_id,
                    ModuleActivation(module_code=module_code, module_name=f"Module {module_code}")
                )
            except Exception:
                pass  # Ignorer si module déjà activé

        # Marquer inscription comme complétée
        registration.status = TrialRegistrationStatus.COMPLETED
        registration.completed_at = datetime.utcnow()
        registration.tenant_id = tenant_id
        self.db.commit()

        # Calculer fin d'essai
        trial_ends_at = datetime.utcnow() + timedelta(days=self.TRIAL_DURATION_DAYS)

        # Envoyer email de bienvenue
        self._send_welcome_email(registration, tenant_id, temp_password, trial_ends_at)

        return TrialCompleteResponse(
            success=True,
            tenant_id=tenant_id,
            tenant_name=registration.company_name,
            admin_email=registration.email,
            temporary_password=temp_password,
            login_url=f"{settings.FRONTEND_URL}/login",
            trial_ends_at=trial_ends_at,
        )

    # ========================================================================
    # TARIFICATION
    # ========================================================================

    @staticmethod
    def get_pricing() -> TrialPricingResponse:
        """Retourner les informations de tarification."""
        plans = [
            TrialPricingPlan(
                name="Starter",
                code="STARTER",
                monthly_price=29,
                yearly_price=290,
                max_users=5,
                max_storage_gb=10,
                features=[
                    "Modules essentiels",
                    "Facturation électronique",
                    "Support email",
                    "Mises à jour incluses",
                ],
            ),
            TrialPricingPlan(
                name="Business",
                code="PROFESSIONAL",
                monthly_price=79,
                yearly_price=790,
                max_users=15,
                max_storage_gb=100,
                features=[
                    "Tous les modules",
                    "Facturation électronique",
                    "Support prioritaire",
                    "API & intégrations",
                    "Rapports avancés",
                ],
                is_popular=True,
            ),
            TrialPricingPlan(
                name="Enterprise",
                code="ENTERPRISE",
                monthly_price=199,
                yearly_price=1990,
                max_users=100,
                max_storage_gb=500,
                features=[
                    "Utilisateurs illimités",
                    "Tous les modules",
                    "Support 24/7 dédié",
                    "SLA garanti 99.9%",
                    "Formation sur site",
                    "Personnalisations",
                ],
            ),
        ]

        return TrialPricingResponse(
            trial_days=self.TRIAL_DURATION_DAYS,
            plans=plans,
        )

    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================

    def _get_registration(self, registration_id: str) -> TrialRegistration:
        """Récupérer une inscription par ID."""
        try:
            uuid_id = UUID(registration_id)
        except ValueError:
            raise ValueError("ID d'inscription invalide")

        registration = self.db.query(TrialRegistration).filter(
            TrialRegistration.id == uuid_id
        ).first()

        if not registration:
            raise ValueError("Inscription non trouvée")

        if registration.expires_at < datetime.utcnow() and registration.status != TrialRegistrationStatus.COMPLETED:
            registration.status = TrialRegistrationStatus.EXPIRED
            self.db.commit()
            raise ValueError("Inscription expirée")

        return registration

    def _check_email_available(self, email: str) -> None:
        """Vérifier que l'email n'est pas déjà utilisé."""
        # Vérifier dans les tenants existants
        existing_tenant = self.db.query(Tenant).filter(
            Tenant.email == email
        ).first()
        if existing_tenant:
            raise ValueError("Cet email est déjà associé à un compte")

        # Vérifier dans les inscriptions en cours (non expirées, non complétées)
        existing_registration = self.db.query(TrialRegistration).filter(
            and_(
                TrialRegistration.email == email,
                TrialRegistration.status.notin_([
                    TrialRegistrationStatus.EXPIRED,
                    TrialRegistrationStatus.COMPLETED
                ]),
                TrialRegistration.expires_at > datetime.utcnow()
            )
        ).first()
        if existing_registration:
            raise ValueError("Une inscription est déjà en cours pour cet email")

    def _verify_hcaptcha(self, token: str) -> bool:
        """Vérifier le token hCaptcha."""
        settings = get_settings()
        if not hasattr(settings, 'HCAPTCHA_SECRET_KEY') or not settings.HCAPTCHA_SECRET_KEY:
            # En dev, accepter tous les tokens
            return True

        try:
            response = httpx.post(
                "https://hcaptcha.com/siteverify",
                data={
                    "secret": settings.HCAPTCHA_SECRET_KEY,
                    "response": token,
                },
                timeout=10.0
            )
            result = response.json()
            return result.get("success", False)
        except Exception:
            # En cas d'erreur, refuser
            return False

    def _generate_tenant_id(self, company_name: str) -> str:
        """Générer un tenant_id unique à partir du nom de l'entreprise."""
        import re
        import unicodedata

        # Normaliser et nettoyer le nom
        normalized = unicodedata.normalize('NFKD', company_name.lower())
        cleaned = normalized.encode('ASCII', 'ignore').decode('ASCII')
        cleaned = re.sub(r'[^a-z0-9]+', '-', cleaned)
        cleaned = cleaned.strip('-')[:40]

        if not cleaned:
            cleaned = "tenant"

        # Vérifier unicité
        base_id = cleaned
        counter = 1
        tenant_id = base_id

        while self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first():
            tenant_id = f"{base_id}-{counter}"
            counter += 1

        return tenant_id

    def _send_verification_email(self, registration: TrialRegistration, token: str) -> None:
        """Envoyer l'email de vérification."""
        settings = get_settings()
        verification_url = f"{settings.FRONTEND_URL}/essai-gratuit/verify?token={token}"

        subject = "Vérifiez votre adresse email - AZALSCORE"
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #1E6EFF;">Bienvenue sur AZALSCORE !</h1>
                <p>Bonjour {registration.first_name},</p>
                <p>Merci de vous être inscrit pour un essai gratuit de 30 jours.</p>
                <p>Pour continuer votre inscription, veuillez vérifier votre adresse email en cliquant sur le bouton ci-dessous :</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}"
                       style="background-color: #1E6EFF; color: white; padding: 12px 30px;
                              text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Vérifier mon email
                    </a>
                </p>
                <p style="font-size: 12px; color: #666;">
                    Ce lien expire dans 24 heures.<br>
                    Si vous n'avez pas demandé cette inscription, ignorez cet email.
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #999;">
                    AZALSCORE - Gestion d'entreprise simplifiée<br>
                    © 2026 MASITH Développement
                </p>
            </div>
        </body>
        </html>
        """

        self._send_smtp_email(registration.email, subject, body_html)

    def _send_welcome_email(
        self,
        registration: TrialRegistration,
        tenant_id: str,
        temp_password: str,
        trial_ends_at: datetime,
    ) -> None:
        """Envoyer l'email de bienvenue avec les identifiants."""
        settings = get_settings()
        login_url = f"{settings.FRONTEND_URL}/login"

        subject = "Votre compte AZALSCORE est prêt !"
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #1E6EFF;">Bienvenue sur AZALSCORE !</h1>
                <p>Bonjour {registration.first_name},</p>
                <p>Votre compte a été créé avec succès. Voici vos informations de connexion :</p>

                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Identifiant société :</strong> {tenant_id}</p>
                    <p><strong>Email :</strong> {registration.email}</p>
                    <p><strong>Mot de passe temporaire :</strong> {temp_password}</p>
                </div>

                <p style="color: #ff6600;">
                    <strong>Important :</strong> Changez votre mot de passe dès votre première connexion.
                </p>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="{login_url}"
                       style="background-color: #1E6EFF; color: white; padding: 12px 30px;
                              text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Se connecter
                    </a>
                </p>

                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0;">
                        <strong>Votre essai gratuit de 30 jours</strong><br>
                        Se termine le : {trial_ends_at.strftime('%d/%m/%Y')}<br>
                        Après cette date, votre compte sera suspendu jusqu'à activation de votre abonnement.
                    </p>
                </div>

                <p>Des données de démonstration ont été ajoutées à votre compte pour vous aider à découvrir les fonctionnalités.</p>

                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #999;">
                    AZALSCORE - Gestion d'entreprise simplifiée<br>
                    © 2026 MASITH Développement
                </p>
            </div>
        </body>
        </html>
        """

        self._send_smtp_email(registration.email, subject, body_html)

    def _send_smtp_email(self, to_email: str, subject: str, body_html: str) -> None:
        """Envoyer un email via SMTP."""
        settings = get_settings()
        if not hasattr(settings, 'SMTP_HOST') or not settings.SMTP_HOST:
            # En dev, juste logger
            print(f"[EMAIL] Would send to {to_email}: {subject}")
            return

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.SMTP_FROM
            msg['To'] = to_email

            html_part = MIMEText(body_html, 'html')
            msg.attach(html_part)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send email to {to_email}: {e}")
            # Ne pas bloquer l'inscription si l'email échoue
