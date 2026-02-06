"""
AZALS MODULE T9 - API Trial Registration
==========================================

Endpoints publics pour l'inscription à l'essai gratuit.
Aucune authentification requise (PUBLIC_PATHS).
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.tenants.schemas_trial import (
    TrialCompleteRequest,
    TrialCompleteResponse,
    TrialEmailVerification,
    TrialEmailVerificationResponse,
    TrialPaymentSetupRequest,
    TrialPaymentSetupResponse,
    TrialPricingResponse,
    TrialRegistrationCreate,
    TrialRegistrationResponse,
    TrialRegistrationStatus,
)
from app.modules.tenants.service_trial import TrialRegistrationService

router = APIRouter(prefix="/api/v2/public/trial", tags=["Trial Registration"])


def get_client_info(request: Request) -> tuple[str, str]:
    """Extraire IP et User-Agent de la requête."""
    # Récupérer l'IP réelle (derrière proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else "unknown"

    user_agent = request.headers.get("User-Agent", "unknown")

    return ip_address, user_agent


@router.post(
    "/register",
    response_model=TrialRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une inscription d'essai",
    description="""
    Étape initiale de l'inscription à l'essai gratuit.

    Crée une inscription avec les informations personnelles et entreprise,
    valide le CAPTCHA, et envoie un email de vérification.

    L'inscription expire après 24 heures si l'email n'est pas vérifié.
    """,
)
def create_trial_registration(
    data: TrialRegistrationCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> TrialRegistrationResponse:
    """Créer une nouvelle inscription d'essai."""
    ip_address, user_agent = get_client_info(request)

    service = TrialRegistrationService(db)

    try:
        registration = service.create_registration(
            data=data,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return TrialRegistrationResponse(
            registration_id=str(registration.id),
            email=registration.email,
            email_sent=True,
            expires_at=registration.expires_at,
            message="Un email de vérification a été envoyé à votre adresse.",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur est survenue lors de l'inscription.",
        )


@router.post(
    "/verify-email",
    response_model=TrialEmailVerificationResponse,
    summary="Vérifier l'email",
    description="""
    Vérifie le token reçu par email.

    Le token est valide pendant 24 heures après la création de l'inscription.
    Une fois vérifié, l'utilisateur peut procéder au paiement.
    """,
)
def verify_trial_email(
    data: TrialEmailVerification,
    db: Session = Depends(get_db),
) -> TrialEmailVerificationResponse:
    """Vérifier le token email."""
    service = TrialRegistrationService(db)

    try:
        registration = service.verify_email(token=data.token)

        return TrialEmailVerificationResponse(
            verified=True,
            registration_id=str(registration.id),
            message="Email vérifié avec succès.",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/payment-setup",
    response_model=TrialPaymentSetupResponse,
    summary="Configurer le paiement",
    description="""
    Crée un SetupIntent Stripe pour enregistrer la carte bancaire.

    Aucun prélèvement n'est effectué (montant €0).
    La carte sera utilisée pour le paiement après la période d'essai
    si l'utilisateur choisit de continuer.

    Prérequis: l'email doit être vérifié.
    """,
)
def setup_trial_payment(
    data: TrialPaymentSetupRequest,
    db: Session = Depends(get_db),
) -> TrialPaymentSetupResponse:
    """Créer un SetupIntent Stripe."""
    service = TrialRegistrationService(db)

    try:
        result = service.create_payment_setup(
            registration_id=data.registration_id,
        )

        return TrialPaymentSetupResponse(
            client_secret=result["client_secret"],
            setup_intent_id=result["setup_intent_id"],
            publishable_key=result["publishable_key"],
            customer_id=result["customer_id"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/complete",
    response_model=TrialCompleteResponse,
    summary="Finaliser l'inscription",
    description="""
    Finalise l'inscription après confirmation du paiement Stripe.

    Crée le tenant avec tous les modules en mode démo,
    crée l'utilisateur administrateur avec un mot de passe temporaire,
    et envoie un email de bienvenue avec les identifiants.

    Prérequis:
    - Email vérifié
    - SetupIntent Stripe confirmé (carte enregistrée)
    """,
)
def complete_trial_registration(
    data: TrialCompleteRequest,
    db: Session = Depends(get_db),
) -> TrialCompleteResponse:
    """Finaliser l'inscription et créer le tenant."""
    service = TrialRegistrationService(db)

    try:
        result = service.complete_registration(
            registration_id=data.registration_id,
            setup_intent_id=data.setup_intent_id,
        )

        return TrialCompleteResponse(
            success=True,
            tenant_id=result["tenant_id"],
            tenant_name=result["tenant_name"],
            admin_email=result["admin_email"],
            temporary_password=result["temporary_password"],
            login_url=result["login_url"],
            trial_ends_at=result["trial_ends_at"],
            message="Votre compte a été créé avec succès !",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/pricing",
    response_model=TrialPricingResponse,
    summary="Obtenir les tarifs",
    description="""
    Retourne les informations de tarification pour affichage.

    Inclut les plans disponibles avec leurs prix mensuels et annuels,
    les fonctionnalités incluses, et les informations sur l'essai gratuit.
    """,
)
def get_trial_pricing() -> TrialPricingResponse:
    """Obtenir les informations de tarification."""
    # Pas besoin de DB pour les tarifs statiques
    return TrialRegistrationService.get_pricing()


@router.get(
    "/status/{registration_id}",
    response_model=TrialRegistrationStatus,
    summary="Statut de l'inscription",
    description="""
    Vérifie le statut actuel d'une inscription en cours.

    Permet au frontend de reprendre le flux si l'utilisateur
    revient sur la page après une interruption.
    """,
)
def get_registration_status(
    registration_id: str,
    db: Session = Depends(get_db),
) -> TrialRegistrationStatus:
    """Obtenir le statut d'une inscription."""
    from datetime import datetime, timezone
    from uuid import UUID

    from app.modules.tenants.models import TrialRegistration

    try:
        reg_uuid = UUID(registration_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID d'inscription invalide.",
        )

    registration = db.query(TrialRegistration).filter(
        TrialRegistration.id == reg_uuid
    ).first()

    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inscription non trouvée.",
        )

    now = datetime.now(timezone.utc)
    is_expired = registration.expires_at < now if registration.expires_at else False

    return TrialRegistrationStatus(
        registration_id=str(registration.id),
        status=registration.status.value,
        email=registration.email,
        email_verified=registration.email_verified_at is not None,
        captcha_verified=registration.captcha_verified,
        payment_setup_complete=registration.stripe_payment_method_id is not None,
        expires_at=registration.expires_at,
        is_expired=is_expired,
    )
