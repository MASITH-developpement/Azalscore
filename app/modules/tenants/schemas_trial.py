"""
AZALS MODULE T9 - Schémas Trial Registration
=============================================

Schémas Pydantic pour l'inscription à l'essai gratuit.
"""

import re
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ============================================================================
# CONSTANTES
# ============================================================================

COUNTRY_CHOICES = [
    ("FR", "France"),
    ("BE", "Belgique"),
    ("CH", "Suisse"),
    ("LU", "Luxembourg"),
    ("MC", "Monaco"),
    ("CA", "Canada"),
]

LANGUAGE_CHOICES = [
    ("fr", "Français"),
]

REVENUE_RANGE_CHOICES = [
    ("0-50k", "0 - 50 000 €"),
    ("50k-100k", "50 000 - 100 000 €"),
    ("100k-250k", "100 000 - 250 000 €"),
    ("250k-500k", "250 000 - 500 000 €"),
    ("500k-1m", "500 000 - 1 000 000 €"),
    ("1m-5m", "1 000 000 - 5 000 000 €"),
    ("5m+", "Plus de 5 000 000 €"),
]


# ============================================================================
# REQUÊTES
# ============================================================================

class TrialRegistrationCreate(BaseModel):
    """Création d'une inscription d'essai (étapes 1-4 combinées)."""

    # Informations personnelles (étape 1)
    first_name: str = Field(..., min_length=1, max_length=100, description="Prénom")
    last_name: str = Field(..., min_length=1, max_length=100, description="Nom")
    email: EmailStr = Field(..., description="Email professionnel")
    phone: str | None = Field(None, max_length=50, description="Téléphone fixe")
    mobile: str | None = Field(None, max_length=50, description="Téléphone portable")

    # Informations entreprise (étape 2)
    company_name: str = Field(..., min_length=1, max_length=255, description="Raison sociale")
    address_line1: str = Field(..., min_length=1, max_length=255, description="Adresse ligne 1")
    address_line2: str | None = Field(None, max_length=255, description="Adresse ligne 2")
    postal_code: str = Field(..., min_length=1, max_length=20, description="Code postal")
    city: str = Field(..., min_length=1, max_length=100, description="Ville")
    country: str = Field(default="FR", max_length=2, description="Pays (code ISO)")
    language: str = Field(default="fr", max_length=5, description="Langue")
    activity: str | None = Field(None, max_length=255, description="Activité de l'entreprise")
    revenue_range: str | None = Field(None, max_length=50, description="Tranche de chiffre d'affaires")
    max_users: int = Field(default=5, ge=1, le=5, description="Nombre d'utilisateurs (max 5 en essai)")
    siret: str | None = Field(None, max_length=20, description="Numéro SIRET")

    # Acceptations (étape 4)
    cgv_accepted: bool = Field(..., description="Acceptation des CGV")
    cgu_accepted: bool = Field(..., description="Acceptation des CGU")

    # CAPTCHA (étape 4)
    captcha_token: str = Field(..., min_length=1, description="Token hCaptcha")

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("cgv_accepted", "cgu_accepted")
    @classmethod
    def must_be_accepted(cls, v: bool, info) -> bool:
        if not v:
            field_name = "CGV" if info.field_name == "cgv_accepted" else "CGU"
            raise ValueError(f"Vous devez accepter les {field_name}")
        return v

    @field_validator("siret")
    @classmethod
    def validate_siret(cls, v: str | None) -> str | None:
        if v is None:
            return v
        # Supprimer les espaces
        v = v.replace(" ", "")
        if not re.match(r"^\d{14}$", v):
            raise ValueError("Le SIRET doit contenir exactement 14 chiffres")
        return v

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        valid_countries = [c[0] for c in COUNTRY_CHOICES]
        if v not in valid_countries:
            raise ValueError(f"Pays invalide. Valeurs autorisées: {', '.join(valid_countries)}")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        valid_languages = [l[0] for l in LANGUAGE_CHOICES]
        if v not in valid_languages:
            raise ValueError(f"Langue invalide. Valeurs autorisées: {', '.join(valid_languages)}")
        return v


class TrialEmailVerification(BaseModel):
    """Vérification de l'email."""
    token: str = Field(..., min_length=1, description="Token de vérification email")


class TrialPaymentSetupRequest(BaseModel):
    """Demande de configuration du paiement."""
    registration_id: str = Field(..., description="ID de l'inscription")


class TrialCompleteRequest(BaseModel):
    """Finalisation de l'inscription après paiement."""
    registration_id: str = Field(..., description="ID de l'inscription")
    setup_intent_id: str = Field(..., description="ID du SetupIntent Stripe")


# ============================================================================
# RÉPONSES
# ============================================================================

class TrialRegistrationResponse(BaseModel):
    """Réponse après création d'inscription."""
    registration_id: str
    email: str
    email_sent: bool = True
    expires_at: datetime
    message: str = "Un email de vérification a été envoyé à votre adresse."

    model_config = ConfigDict(from_attributes=True)


class TrialEmailVerificationResponse(BaseModel):
    """Réponse après vérification email."""
    verified: bool
    registration_id: str
    message: str = "Email vérifié avec succès."


class TrialPaymentSetupResponse(BaseModel):
    """Réponse avec les informations Stripe pour le paiement."""
    client_secret: str
    setup_intent_id: str
    publishable_key: str
    customer_id: str


class TrialCompleteResponse(BaseModel):
    """Réponse après finalisation de l'inscription."""
    success: bool = True
    tenant_id: str
    tenant_name: str
    admin_email: str
    temporary_password: str
    login_url: str
    trial_ends_at: datetime
    message: str = "Votre compte a été créé avec succès !"


class TrialPricingPlan(BaseModel):
    """Détail d'un plan tarifaire."""
    name: str
    code: str
    monthly_price: Decimal
    yearly_price: Decimal
    currency: str = "EUR"
    max_users: int
    max_storage_gb: int
    features: list[str]
    is_popular: bool = False


class TrialPricingResponse(BaseModel):
    """Informations de tarification pour l'affichage."""
    trial_days: int = 30
    plans: list[TrialPricingPlan]
    currency: str = "EUR"
    vat_included: bool = False
    message: str = "Essai gratuit de 30 jours, sans engagement."


class TrialRegistrationStatus(BaseModel):
    """Statut d'une inscription."""
    registration_id: str
    status: str
    email: str
    email_verified: bool
    captcha_verified: bool
    payment_setup_complete: bool
    expires_at: datetime
    is_expired: bool

    model_config = ConfigDict(from_attributes=True)
