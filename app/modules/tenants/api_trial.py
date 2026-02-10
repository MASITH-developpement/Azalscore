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
    TrialPromoCodeRequest,
    TrialPromoResponse,
    TrialRegistrationCreate,
    TrialRegistrationResponse,
    TrialRegistrationStatus,
)
from fastapi.responses import HTMLResponse
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
    "/resend-verification",
    response_model=dict,
    summary="Renvoyer l'email de vérification",
    description="""
    Renvoie l'email de vérification pour une inscription en cours.
    Limité à 3 envois par inscription.
    """,
)
def resend_verification_email(
    data: dict,
    db: Session = Depends(get_db),
) -> dict:
    """Renvoyer l'email de vérification."""
    registration_id = data.get("registration_id")
    if not registration_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="registration_id requis",
        )

    service = TrialRegistrationService(db)

    try:
        service.resend_verification_email(registration_id)
        return {"success": True, "message": "Email de vérification renvoyé."}
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


@router.post(
    "/apply-promo",
    response_model=TrialPromoResponse,
    summary="Demander un accès via code promo",
    description="""
    Soumet une demande d'accès gratuit via code promo.

    Un email est envoyé à l'administrateur pour approbation.
    Le demandeur sera notifié par email de la décision.
    """,
)
def apply_promo_code(
    data: TrialPromoCodeRequest,
    db: Session = Depends(get_db),
) -> TrialPromoResponse:
    """Demander un accès via code promo."""
    service = TrialRegistrationService(db)

    try:
        result = service.complete_with_promo(
            registration_id=data.registration_id,
            promo_code=data.promo_code,
        )

        return TrialPromoResponse(
            status=result["status"],
            message=result["message"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/promo-approve/{token}",
    response_class=HTMLResponse,
    summary="Approuver une demande de code promo",
    description="Endpoint appelé par l'admin pour approuver une demande.",
)
def approve_promo(
    token: str,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Approuver une demande de code promo."""
    service = TrialRegistrationService(db)

    try:
        result = service.approve_promo_request(token)
        return HTMLResponse(content=f"""
        <html>
        <head>
            <title>Demande approuvée - AZALSCORE</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f0fdf4; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                h1 {{ color: #22c55e; }}
                p {{ color: #333; line-height: 1.6; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✓ Demande approuvée</h1>
                <p>Le compte pour <strong>{result['tenant_name']}</strong> a été créé.</p>
                <p>Un email avec les identifiants a été envoyé à <strong>{result['admin_email']}</strong>.</p>
            </div>
        </body>
        </html>
        """, status_code=200)
    except ValueError as e:
        return HTMLResponse(content=f"""
        <html>
        <head>
            <title>Erreur - AZALSCORE</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #fef2f2; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                h1 {{ color: #ef4444; }}
                p {{ color: #333; line-height: 1.6; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✗ Erreur</h1>
                <p>{str(e)}</p>
            </div>
        </body>
        </html>
        """, status_code=400)


@router.get(
    "/promo-reject/{token}",
    response_class=HTMLResponse,
    summary="Refuser une demande de code promo",
    description="Endpoint appelé par l'admin pour refuser une demande.",
)
def reject_promo(
    token: str,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Refuser une demande de code promo."""
    service = TrialRegistrationService(db)

    try:
        result = service.reject_promo_request(token)
        return HTMLResponse(content=f"""
        <html>
        <head>
            <title>Demande refusée - AZALSCORE</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #fff7ed; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                h1 {{ color: #f97316; }}
                p {{ color: #333; line-height: 1.6; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Demande refusée</h1>
                <p>{result['message']}</p>
                <p>Le demandeur a été notifié par email.</p>
            </div>
        </body>
        </html>
        """, status_code=200)
    except ValueError as e:
        return HTMLResponse(content=f"""
        <html>
        <head>
            <title>Erreur - AZALSCORE</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #fef2f2; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                h1 {{ color: #ef4444; }}
                p {{ color: #333; line-height: 1.6; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✗ Erreur</h1>
                <p>{str(e)}</p>
            </div>
        </body>
        </html>
        """, status_code=400)


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

    now = datetime.utcnow()
    # Handle both timezone-aware and naive datetimes from DB
    if registration.expires_at:
        expires_at = registration.expires_at
        if expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)
        is_expired = expires_at < now
    else:
        is_expired = False

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
