"""
AZALS - Router Signup Production
=================================
Endpoints publics pour l'inscription de nouvelles entreprises.

Chaque entreprise = 1 Tenant isolé
Nom entreprise → tenant_id (slug unique)
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.services.signup_service import SignupService, SignupError

router = APIRouter(prefix="/signup", tags=["Signup"])
logger = get_logger(__name__)


# ============================================================================
# SCHEMAS
# ============================================================================

class SignupRequest(BaseModel):
    """Requête d'inscription d'une nouvelle entreprise."""
    
    # Entreprise
    company_name: str = Field(..., min_length=2, max_length=100, description="Nom de l'entreprise")
    company_email: EmailStr = Field(..., description="Email principal de l'entreprise")
    country: str = Field(default="FR", min_length=2, max_length=2, description="Code pays ISO")
    siret: Optional[str] = Field(default=None, max_length=20, description="SIRET (France)")
    
    # Admin
    admin_email: EmailStr = Field(..., description="Email de l'administrateur")
    admin_password: str = Field(..., min_length=8, description="Mot de passe (8 caractères min)")
    admin_first_name: str = Field(..., min_length=1, max_length=50, description="Prénom")
    admin_last_name: str = Field(..., min_length=1, max_length=50, description="Nom")
    admin_phone: Optional[str] = Field(default=None, max_length=20, description="Téléphone")
    
    # Options
    plan: str = Field(default="PROFESSIONAL", description="Plan choisi pour l'essai")
    referral_code: Optional[str] = Field(default=None, description="Code de parrainage")
    accept_terms: bool = Field(..., description="Acceptation des CGV")
    accept_privacy: bool = Field(..., description="Acceptation politique de confidentialité")

    @field_validator('company_name')
    @classmethod
    def validate_company_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Le nom de l\'entreprise doit contenir au moins 2 caractères')
        return v.strip()

    @field_validator('admin_password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        if not any(c.isupper() for c in v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        if not any(c.isdigit() for c in v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        return v

    @field_validator('accept_terms', 'accept_privacy')
    @classmethod
    def validate_acceptance(cls, v, info):
        if not v:
            field_name = "CGV" if info.field_name == "accept_terms" else "politique de confidentialité"
            raise ValueError(f'Vous devez accepter les {field_name}')
        return v


class SignupResponse(BaseModel):
    """Réponse après inscription réussie."""
    success: bool = True
    tenant_id: str
    company_name: str
    admin_email: str
    trial_ends_at: str
    login_url: str
    message: str


class CheckAvailabilityResponse(BaseModel):
    """Réponse de vérification de disponibilité."""
    available: bool
    suggestion: Optional[str] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    data: SignupRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Inscrire une nouvelle entreprise.
    
    Crée automatiquement:
    - Le tenant (espace isolé pour l'entreprise)
    - L'utilisateur administrateur
    - L'abonnement d'essai (14 jours)
    - Les modules selon le plan choisi
    
    **Aucune carte bancaire requise pour l'essai.**
    """
    # Log de la tentative
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"[SIGNUP] Tentative: {data.company_name} / {data.admin_email} depuis {client_ip}")
    
    service = SignupService(db)
    
    try:
        result = service.signup(
            company_name=data.company_name,
            company_email=data.company_email,
            country=data.country.upper(),
            siret=data.siret,
            admin_email=data.admin_email,
            admin_password=data.admin_password,
            admin_first_name=data.admin_first_name,
            admin_last_name=data.admin_last_name,
            admin_phone=data.admin_phone,
            plan=data.plan,
            referral_code=data.referral_code,
        )
        
        # Envoyer email de bienvenue
        try:
            from app.services.email_service import get_email_service
            email_service = get_email_service()
            email_service.send_welcome(
                email=data.admin_email,
                name=data.admin_first_name,
                tenant_name=data.company_name,
            )
            logger.info(f"[SIGNUP] Email de bienvenue envoyé à {data.admin_email}")
        except Exception as e:
            # Ne pas bloquer le signup si l'email échoue
            logger.error(f"[SIGNUP] Erreur envoi email: {e}")
        
        logger.info(f"[SIGNUP] Succès: {result['tenant_id']} créé")
        
        return SignupResponse(
            success=True,
            tenant_id=result["tenant_id"],
            company_name=data.company_name,
            admin_email=data.admin_email,
            trial_ends_at=result["trial_ends_at"].isoformat(),
            login_url=result["login_url"],
            message=f"Bienvenue ! Votre espace {data.company_name} est prêt. Essai gratuit de 14 jours activé.",
        )
        
    except SignupError as e:
        logger.warning(f"[SIGNUP] Erreur: {e.code} - {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message}
        )
    except Exception as e:
        logger.error(f"[SIGNUP] Erreur inattendue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "Une erreur est survenue. Réessayez."}
        )


@router.get("/check-email", response_model=CheckAvailabilityResponse)
async def check_email_availability(
    email: EmailStr,
    db: Session = Depends(get_db)
):
    """
    Vérifier si un email est disponible pour l'inscription.
    
    Utilisé pour la validation en temps réel dans le formulaire.
    """
    service = SignupService(db)
    available = service.check_email_available(email)
    
    return CheckAvailabilityResponse(
        available=available,
        suggestion="Cet email est déjà utilisé. Connectez-vous ou utilisez un autre email." if not available else None
    )


@router.get("/check-company", response_model=CheckAvailabilityResponse)
async def check_company_availability(
    name: str,
    db: Session = Depends(get_db)
):
    """
    Vérifier si un nom d'entreprise est disponible.
    
    Utilisé pour la validation en temps réel dans le formulaire.
    """
    if len(name.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nom doit contenir au moins 2 caractères"
        )
    
    service = SignupService(db)
    available = service.check_company_available(name)
    
    # Générer une suggestion si non disponible
    suggestion = None
    if not available:
        import secrets
        suggestion = f"{name} - {secrets.token_hex(2).upper()}"
    
    return CheckAvailabilityResponse(
        available=available,
        suggestion=suggestion
    )


@router.get("/plans")
async def get_available_plans():
    """
    Retourner les plans disponibles avec leurs caractéristiques.
    
    Utilisé pour afficher les options dans le formulaire d'inscription.
    """
    return {
        "plans": [
            {
                "id": "STARTER",
                "name": "Starter",
                "price_monthly": 49,
                "price_yearly": 490,
                "max_users": 5,
                "max_storage_gb": 10,
                "features": [
                    "CRM & Gestion commerciale",
                    "Comptabilité de base",
                    "5 utilisateurs",
                    "10 Go stockage",
                    "Support email",
                ],
                "recommended": False,
            },
            {
                "id": "PROFESSIONAL",
                "name": "Professional",
                "price_monthly": 149,
                "price_yearly": 1490,
                "max_users": 25,
                "max_storage_gb": 50,
                "features": [
                    "Tous les modules métier",
                    "RH, Production, Qualité",
                    "25 utilisateurs",
                    "50 Go stockage",
                    "Support prioritaire",
                    "Rapports avancés",
                ],
                "recommended": True,
            },
            {
                "id": "ENTERPRISE",
                "name": "Enterprise",
                "price_monthly": 499,
                "price_yearly": 4990,
                "max_users": -1,
                "max_storage_gb": 500,
                "features": [
                    "Utilisateurs illimités",
                    "Assistant IA",
                    "Business Intelligence",
                    "500 Go stockage",
                    "Support 24/7",
                    "Personnalisation",
                    "SLA garanti",
                ],
                "recommended": False,
            },
        ],
        "trial_days": 14,
        "currency": "EUR",
    }
