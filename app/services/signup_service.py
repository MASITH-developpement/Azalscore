"""
AZALS - Service de Signup Production Multi-Tenant
===================================================
Gère l'inscription de nouvelles entreprises (tenants).

Chaque entreprise cliente = 1 Tenant isolé
- tenant_id généré depuis le nom de l'entreprise (slug)
- Admin créé automatiquement
- Trial de 14 jours
- Modules de base activés selon le plan
"""

import re
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.logging_config import get_logger
from app.core.security import get_password_hash as hash_password
from app.core.models import User
from app.modules.tenants.models import (
    Tenant, TenantSubscription, TenantModule, TenantSettings, TenantOnboarding,
    TenantStatus, SubscriptionPlan, BillingCycle, ModuleStatus
)

logger = get_logger(__name__)


# ============================================================================
# CONFIGURATION DES PLANS
# ============================================================================

PLAN_CONFIG = {
    "STARTER": {
        "max_users": 5,
        "max_storage_gb": 10,
        "modules": ["T0", "M1", "M2"],  # IAM, Commercial, Finance (basique)
        "price_monthly": 49,
        "price_yearly": 490,
    },
    "PROFESSIONAL": {
        "max_users": 25,
        "max_storage_gb": 50,
        "modules": [
            "T0", "T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9",
            "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"
        ],
        "price_monthly": 149,
        "price_yearly": 1490,
    },
    "ENTERPRISE": {
        "max_users": -1,  # Illimité
        "max_storage_gb": 500,
        "modules": "ALL",
        "price_monthly": 499,
        "price_yearly": 4990,
    },
}

# Modules disponibles
ALL_MODULES = [
    # Technique
    "T0",  # IAM
    "T1",  # AutoConfig
    "T2",  # Triggers
    "T3",  # Audit
    "T4",  # QC
    "T5",  # Country Packs
    "T6",  # Broadcast
    "T7",  # Web
    "T8",  # Website
    "T9",  # Tenants
    # Métier
    "M1",  # Commercial (CRM, Ventes)
    "M2",  # Finance (Compta, Trésorerie)
    "M3",  # HR
    "M4",  # Procurement
    "M5",  # Inventory
    "M6",  # Production
    "M7",  # Quality
    "M8",  # Maintenance
    # Premium
    "AI",  # AI Assistant
    "BI",  # Business Intelligence
]


class SignupError(Exception):
    """Erreur lors du signup."""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class SignupService:
    """Service de signup pour nouvelles entreprises avec validations de sécurité."""

    # Regex pour validation email (RFC 5322 simplifié)
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    # Configuration des mots de passe
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGIT = True
    PASSWORD_REQUIRE_SPECIAL = True

    # Caractères spéciaux autorisés
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    def __init__(self, db: Session):
        self.db = db

    def _validate_email(self, email: str) -> bool:
        """Valide le format d'une adresse email."""
        if not email or len(email) > 254:
            return False
        return bool(self.EMAIL_PATTERN.match(email))

    def _validate_password(self, password: str) -> tuple[bool, str]:
        """
        Valide la complexité d'un mot de passe.

        Returns:
            Tuple (is_valid, error_message)
        """
        if len(password) < self.PASSWORD_MIN_LENGTH:
            return False, f"Le mot de passe doit contenir au moins {self.PASSWORD_MIN_LENGTH} caractères"

        if self.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return False, "Le mot de passe doit contenir au moins une majuscule"

        if self.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            return False, "Le mot de passe doit contenir au moins une minuscule"

        if self.PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
            return False, "Le mot de passe doit contenir au moins un chiffre"

        if self.PASSWORD_REQUIRE_SPECIAL and not any(c in self.SPECIAL_CHARS for c in password):
            return False, f"Le mot de passe doit contenir au moins un caractère spécial ({self.SPECIAL_CHARS})"

        return True, ""

    def _validate_siret(self, siret: str) -> bool:
        """
        Valide un numéro SIRET français (14 chiffres, algorithme de Luhn).
        """
        if not siret:
            return True  # SIRET est optionnel

        # Nettoyer (enlever espaces)
        siret_clean = re.sub(r'\s', '', siret)

        # Doit contenir exactement 14 chiffres
        if not re.match(r'^\d{14}$', siret_clean):
            return False

        # Algorithme de Luhn
        total = 0
        for i, char in enumerate(siret_clean):
            digit = int(char)
            if i % 2 == 0:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit

        return total % 10 == 0

    def signup(
        self,
        # Entreprise
        company_name: str,
        company_email: str,
        # Admin
        admin_email: str,
        admin_password: str,
        admin_first_name: str,
        admin_last_name: str,
        # Options avec valeurs par défaut
        country: str = "FR",
        siret: Optional[str] = None,
        admin_phone: Optional[str] = None,
        plan: str = "PROFESSIONAL",  # Plan par défaut pour le trial
        referral_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Inscrire une nouvelle entreprise.
        
        Crée:
        - Le tenant (entreprise)
        - L'utilisateur admin
        - L'abonnement trial
        - Les modules selon le plan
        - L'onboarding
        
        Returns:
            {
                "tenant_id": "acme-corp",
                "tenant": Tenant,
                "admin_user": User,
                "trial_ends_at": datetime,
                "login_url": "/login",
            }
        """
        # 1. Valider les entrées (SÉCURITÉ)

        # Valider les emails
        if not self._validate_email(admin_email):
            raise SignupError("INVALID_EMAIL", "Format d'email administrateur invalide")

        if not self._validate_email(company_email):
            raise SignupError("INVALID_EMAIL", "Format d'email entreprise invalide")

        # Valider le mot de passe
        is_valid, password_error = self._validate_password(admin_password)
        if not is_valid:
            raise SignupError("WEAK_PASSWORD", password_error)

        # Valider le SIRET si fourni
        if siret and not self._validate_siret(siret):
            raise SignupError("INVALID_SIRET", "Format de SIRET invalide")

        # Valider le nom de l'entreprise
        if not company_name or len(company_name.strip()) < 2:
            raise SignupError("INVALID_COMPANY_NAME", "Le nom de l'entreprise est trop court")

        if len(company_name) > 200:
            raise SignupError("INVALID_COMPANY_NAME", "Le nom de l'entreprise est trop long")

        # 2. Générer le tenant_id depuis le nom de l'entreprise
        tenant_id = self._generate_tenant_id(company_name)

        # 3. Vérifier que l'email n'existe pas déjà
        # SÉCURITÉ: Message générique pour éviter l'énumération d'utilisateurs
        existing_user = self.db.query(User).filter(
            User.email == admin_email
        ).first()
        if existing_user:
            raise SignupError("SIGNUP_FAILED", "Impossible de créer le compte. Veuillez réessayer ou contacter le support.")

        # 4. Vérifier que le tenant n'existe pas
        # SÉCURITÉ: Message générique pour éviter l'énumération d'entreprises
        existing_tenant = self.db.query(Tenant).filter(
            or_(
                Tenant.tenant_id == tenant_id,
                Tenant.email == company_email
            )
        ).first()
        if existing_tenant:
            raise SignupError("SIGNUP_FAILED", "Impossible de créer le compte. Veuillez réessayer ou contacter le support.")

        # 5. Valider le plan
        plan_upper = plan.upper()
        if plan_upper not in PLAN_CONFIG:
            plan_upper = "PROFESSIONAL"
        
        plan_config = PLAN_CONFIG[plan_upper]
        
        # 5. Créer le tenant
        trial_ends_at = datetime.utcnow() + timedelta(days=14)
        
        tenant = Tenant(
            tenant_id=tenant_id,
            name=company_name,
            legal_name=company_name,
            email=company_email,
            country=country,
            siret=siret,
            status=TenantStatus.TRIAL,
            plan=SubscriptionPlan[plan_upper],
            trial_ends_at=trial_ends_at,
            activated_at=datetime.utcnow(),
            max_users=plan_config["max_users"],
            max_storage_gb=plan_config["max_storage_gb"],
            timezone="Europe/Paris",
            language="fr",
            currency="EUR",
            features={
                "referral_code": referral_code,
                "signup_plan": plan_upper,
            },
        )
        self.db.add(tenant)
        self.db.flush()  # Pour avoir l'ID
        
        logger.info(f"[SIGNUP] Tenant créé: {tenant_id} ({company_name})")
        
        # 6. Créer l'utilisateur admin
        # Note: Le modèle User n'a pas first_name/last_name, on utilise les champs existants
        admin_user = User(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            email=admin_email,
            password_hash=hash_password(admin_password),
            role="ADMIN",  # Enum UserRole
            is_active=1,  # Integer pour SQLite
            created_at=datetime.utcnow(),
        )
        self.db.add(admin_user)
        
        logger.info(f"[SIGNUP] Admin créé: {admin_email} pour {tenant_id}")
        
        # 7. Créer l'abonnement trial
        subscription = TenantSubscription(
            tenant_id=tenant_id,
            plan=SubscriptionPlan[plan_upper],
            billing_cycle=BillingCycle.MONTHLY,
            price_monthly=plan_config["price_monthly"],
            price_yearly=plan_config["price_yearly"],
            starts_at=datetime.utcnow(),
            ends_at=trial_ends_at,
            is_active=True,
            is_trial=True,
            auto_renew=False,
        )
        self.db.add(subscription)
        
        # 8. Activer les modules selon le plan
        modules_to_activate = plan_config["modules"]
        if modules_to_activate == "ALL":
            modules_to_activate = ALL_MODULES
        
        for module_code in modules_to_activate:
            module = TenantModule(
                tenant_id=tenant_id,
                module_code=module_code,
                module_name=self._get_module_name(module_code),
                status=ModuleStatus.ACTIVE,
                activated_at=datetime.utcnow(),
            )
            self.db.add(module)
        
        # 9. Créer les settings par défaut
        settings = TenantSettings(
            tenant_id=tenant_id,
            two_factor_required=False,
            session_timeout_minutes=30,
            notify_admin_on_signup=True,
            auto_backup_enabled=True,
        )
        self.db.add(settings)
        
        # 10. Créer l'onboarding
        onboarding = TenantOnboarding(
            tenant_id=tenant_id,
            company_info_completed=True,
            admin_created=True,
            progress_percent=28,
            current_step="users",
        )
        self.db.add(onboarding)
        
        # 11. Commit tout
        self.db.commit()
        self.db.refresh(tenant)
        self.db.refresh(admin_user)
        
        logger.info(f"[SIGNUP] Signup complet: {tenant_id} - Trial jusqu'au {trial_ends_at}")
        
        return {
            "tenant_id": tenant_id,
            "tenant": tenant,
            "admin_user": admin_user,
            "trial_ends_at": trial_ends_at,
            "modules_activated": modules_to_activate,
            "login_url": f"/login?tenant={tenant_id}",
            "onboarding_url": f"/onboarding",
        }

    def _generate_tenant_id(self, company_name: str) -> str:
        """
        Générer un tenant_id unique depuis le nom de l'entreprise.
        
        "Acme Corporation SAS" → "acme-corporation"
        "L'Épicerie du Coin" → "lepicerie-du-coin"
        
        Si déjà pris, ajoute un suffixe: "acme-corporation-2"
        """
        # Normaliser : minuscules, enlever accents
        import unicodedata
        normalized = unicodedata.normalize('NFKD', company_name.lower())
        normalized = normalized.encode('ascii', 'ignore').decode('ascii')
        
        # Garder seulement lettres, chiffres, espaces
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        
        # Remplacer espaces par tirets
        slug = re.sub(r'\s+', '-', normalized.strip())
        
        # Limiter la longueur
        slug = slug[:40]
        
        # Enlever tirets en début/fin
        slug = slug.strip('-')
        
        # Si vide, générer un ID aléatoire
        if not slug:
            slug = f"tenant-{secrets.token_hex(4)}"
        
        # Vérifier unicité
        base_slug = slug
        counter = 1
        while self.db.query(Tenant).filter(Tenant.tenant_id == slug).first():
            counter += 1
            slug = f"{base_slug}-{counter}"
        
        return slug

    def _get_module_name(self, code: str) -> str:
        """Retourner le nom lisible d'un module."""
        names = {
            "T0": "IAM - Gestion des accès",
            "T1": "AutoConfig",
            "T2": "Triggers",
            "T3": "Audit",
            "T4": "Contrôle Qualité",
            "T5": "Country Packs",
            "T6": "Broadcast",
            "T7": "Web",
            "T8": "Website",
            "T9": "Tenants",
            "M1": "Commercial - CRM & Ventes",
            "M2": "Finance - Comptabilité",
            "M3": "Ressources Humaines",
            "M4": "Achats",
            "M5": "Stocks",
            "M6": "Production",
            "M7": "Qualité",
            "M8": "Maintenance",
            "AI": "Assistant IA",
            "BI": "Business Intelligence",
        }
        return names.get(code, f"Module {code}")

    def check_email_available(self, email: str) -> bool:
        """
        Vérifier si un email est disponible.

        SÉCURITÉ: Cette méthode peut être utilisée pour l'énumération d'utilisateurs.
        Elle devrait être protégée par un rate limiting côté API.
        """
        # Valider le format d'abord
        if not self._validate_email(email):
            return False  # Format invalide = non disponible

        return not self.db.query(User).filter(User.email == email).first()

    def check_company_available(self, name: str) -> bool:
        """
        Vérifier si un nom d'entreprise est disponible.

        SÉCURITÉ: Cette méthode peut être utilisée pour l'énumération d'entreprises.
        Elle devrait être protégée par un rate limiting côté API.
        """
        if not name or len(name.strip()) < 2:
            return False

        # Générer le slug de base (sans suffixe d'unicité)
        base_slug = self._generate_base_slug(name)
        # Si le slug de base ou une variante existe déjà, considérer comme pris
        return not self.db.query(Tenant).filter(
            Tenant.tenant_id.like(f"{base_slug}%")
        ).first()

    def _generate_base_slug(self, company_name: str) -> str:
        """Générer un slug de base depuis le nom d'entreprise (sans suffixe d'unicité)."""
        import unicodedata
        normalized = unicodedata.normalize('NFKD', company_name.lower())
        normalized = normalized.encode('ascii', 'ignore').decode('ascii')
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        slug = re.sub(r'\s+', '-', normalized.strip())
        slug = slug[:40]
        slug = slug.strip('-')
        if not slug:
            slug = "tenant"
        return slug


# ============================================================================
# API ENDPOINTS (à ajouter dans un router)
# ============================================================================

"""
Exemple d'utilisation dans un router FastAPI:

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.services.signup_service import SignupService, SignupError

router = APIRouter(prefix="/signup", tags=["Signup"])

class SignupRequest(BaseModel):
    company_name: str
    company_email: EmailStr
    admin_email: EmailStr
    admin_password: str
    admin_first_name: str
    admin_last_name: str
    country: str = "FR"
    plan: str = "PROFESSIONAL"

@router.post("/")
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    service = SignupService(db)
    try:
        result = service.signup(
            company_name=data.company_name,
            company_email=data.company_email,
            admin_email=data.admin_email,
            admin_password=data.admin_password,
            admin_first_name=data.admin_first_name,
            admin_last_name=data.admin_last_name,
            country=data.country,
            plan=data.plan,
        )
        
        # Envoyer email de bienvenue
        from app.services.email_service import get_email_service
        email_service = get_email_service()
        email_service.send_welcome(
            email=data.admin_email,
            name=data.admin_first_name,
            tenant_name=data.company_name,
        )
        
        return {
            "success": True,
            "tenant_id": result["tenant_id"],
            "trial_ends_at": result["trial_ends_at"].isoformat(),
            "login_url": result["login_url"],
        }
        
    except SignupError as e:
        raise HTTPException(status_code=400, detail={"code": e.code, "message": e.message})

@router.get("/check-email")
def check_email(email: str, db: Session = Depends(get_db)):
    service = SignupService(db)
    return {"available": service.check_email_available(email)}

@router.get("/check-company")
def check_company(name: str, db: Session = Depends(get_db)):
    service = SignupService(db)
    return {"available": service.check_company_available(name)}
"""
