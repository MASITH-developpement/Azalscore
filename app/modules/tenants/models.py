"""
AZALS MODULE T9 - Modèles Tenants
==================================

Modèles SQLAlchemy pour la gestion des tenants.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.types import JSON, UniversalUUID
from app.db import Base

# ============================================================================
# ENUMS
# ============================================================================

class TenantStatus(str, enum.Enum):
    """Statuts de tenant."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"
    TRIAL = "TRIAL"


class TenantEnvironment(str, enum.Enum):
    """Environnements de déploiement."""
    BETA = "beta"
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"


class SubscriptionPlan(str, enum.Enum):
    """Plans d'abonnement."""
    STARTER = "STARTER"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"
    CUSTOM = "CUSTOM"


class BillingCycle(str, enum.Enum):
    """Cycles de facturation."""
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


class ModuleStatus(str, enum.Enum):
    """Statuts de module."""
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    PENDING = "PENDING"


class InvitationStatus(str, enum.Enum):
    """Statuts d'invitation tenant."""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


# ============================================================================
# MODÈLES
# ============================================================================

class Tenant(Base):
    """Tenant (client) de la plateforme."""
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Informations entreprise
    name: Mapped[str | None] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(255))
    siret: Mapped[str | None] = mapped_column(String(20))
    vat_number: Mapped[str | None] = mapped_column(String(30))

    # Adresse
    address_line1: Mapped[str | None] = mapped_column(String(255))
    address_line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str | None] = mapped_column(String(2), default="FR")

    # Contact
    email: Mapped[str | None] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    website: Mapped[str | None] = mapped_column(String(255))

    # Statut et plan
    status: Mapped[str | None] = mapped_column(Enum(TenantStatus), default=TenantStatus.PENDING)
    plan: Mapped[str | None] = mapped_column(Enum(SubscriptionPlan), default=SubscriptionPlan.STARTER)

    # Environnement (beta, production, staging, development)
    environment: Mapped[str | None] = mapped_column(
        Enum(TenantEnvironment),
        default=TenantEnvironment.PRODUCTION,
        nullable=False
    )

    # Configuration
    timezone: Mapped[str | None] = mapped_column(String(50), default="Europe/Paris")
    language: Mapped[str | None] = mapped_column(String(5), default="fr")
    currency: Mapped[str | None] = mapped_column(String(3), default="EUR")
    date_format: Mapped[str | None] = mapped_column(String(20), default="DD/MM/YYYY")

    # Limites
    max_users: Mapped[int | None] = mapped_column(Integer, default=5)
    max_storage_gb: Mapped[int | None] = mapped_column(Integer, default=10)
    storage_used_gb: Mapped[float | None] = mapped_column(Float, default=0)

    # Branding
    logo_url: Mapped[str | None] = mapped_column(String(500))
    primary_color: Mapped[str | None] = mapped_column(String(7), default="#1976D2")
    secondary_color: Mapped[str | None] = mapped_column(String(7), default="#424242")

    # Fonctionnalités
    features: Mapped[dict | None] = mapped_column(JSON)  # {"feature1": true, "feature2": false}

    # Données supplémentaires
    extra_data: Mapped[dict | None] = mapped_column(JSON)

    # Dates
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime)
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[str | None] = mapped_column(String(100))


class TenantSubscription(Base):
    """Abonnement d'un tenant."""
    __tablename__ = "tenant_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Plan
    plan: Mapped[str | None] = mapped_column(Enum(SubscriptionPlan), nullable=False)
    billing_cycle: Mapped[str | None] = mapped_column(Enum(BillingCycle), default=BillingCycle.MONTHLY)

    # Prix
    price_monthly: Mapped[float | None] = mapped_column(Float)
    price_yearly: Mapped[float | None] = mapped_column(Float)
    discount_percent: Mapped[float | None] = mapped_column(Float, default=0)

    # Période
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime)
    next_billing_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Statut
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_trial: Mapped[bool | None] = mapped_column(Boolean, default=False)
    auto_renew: Mapped[bool | None] = mapped_column(Boolean, default=True)

    # Paiement
    payment_method: Mapped[str | None] = mapped_column(String(50))
    last_payment_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_payment_amount: Mapped[float | None] = mapped_column(Float)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TenantModule(Base):
    """Module activé pour un tenant."""
    __tablename__ = "tenant_modules"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Module
    module_code: Mapped[str | None] = mapped_column(String(10), nullable=False)
    module_name: Mapped[str | None] = mapped_column(String(100))
    module_version: Mapped[str | None] = mapped_column(String(20))

    # Statut
    status: Mapped[str | None] = mapped_column(Enum(ModuleStatus), default=ModuleStatus.ACTIVE)

    # Configuration
    config: Mapped[dict | None] = mapped_column(JSON)
    limits: Mapped[dict | None] = mapped_column(JSON)  # {"max_records": 1000}

    # Dates
    activated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TenantInvitation(Base):
    """Invitation à rejoindre un tenant."""
    __tablename__ = "tenant_invitations"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)

    # Invitation
    token: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=False, index=True)

    # Tenant cible (nouveau ou existant)
    tenant_id: Mapped[str | None] = mapped_column(String(50))
    tenant_name: Mapped[str | None] = mapped_column(String(255))
    plan: Mapped[str | None] = mapped_column(Enum(SubscriptionPlan))

    # Rôle proposé
    proposed_role: Mapped[str | None] = mapped_column(String(50), default="TENANT_ADMIN")

    # Statut
    status: Mapped[str | None] = mapped_column(Enum(InvitationStatus), default=InvitationStatus.PENDING)

    # Dates
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[str | None] = mapped_column(String(100))


class TenantUsage(Base):
    """Utilisation des ressources par tenant."""
    __tablename__ = "tenant_usage"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Période
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    period: Mapped[str | None] = mapped_column(String(20), default="daily")

    # Utilisateurs
    active_users: Mapped[int | None] = mapped_column(Integer, default=0)
    total_users: Mapped[int | None] = mapped_column(Integer, default=0)
    new_users: Mapped[int | None] = mapped_column(Integer, default=0)

    # Stockage
    storage_used_gb: Mapped[float | None] = mapped_column(Float, default=0)
    files_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # API
    api_calls: Mapped[int | None] = mapped_column(Integer, default=0)
    api_errors: Mapped[int | None] = mapped_column(Integer, default=0)

    # Modules
    module_usage: Mapped[dict | None] = mapped_column(JSON)  # {"M1": 100, "M2": 50}

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class TenantEvent(Base):
    """Événements tenant (audit)."""
    __tablename__ = "tenant_events"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Événement
    event_type: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    event_data: Mapped[dict | None] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(Text)

    # Acteur
    actor_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    actor_email: Mapped[str | None] = mapped_column(String(255))
    actor_ip: Mapped[str | None] = mapped_column(String(50))

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class TenantSettings(Base):
    """Paramètres avancés du tenant."""
    __tablename__ = "tenant_settings"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, unique=True, index=True)

    # Sécurité
    two_factor_required: Mapped[bool | None] = mapped_column(Boolean, default=False)
    session_timeout_minutes: Mapped[int | None] = mapped_column(Integer, default=30)
    password_expiry_days: Mapped[int | None] = mapped_column(Integer, default=90)
    ip_whitelist: Mapped[dict | None] = mapped_column(JSON)

    # Notifications
    notify_admin_on_signup: Mapped[bool | None] = mapped_column(Boolean, default=True)
    notify_admin_on_error: Mapped[bool | None] = mapped_column(Boolean, default=True)
    daily_digest_enabled: Mapped[bool | None] = mapped_column(Boolean, default=True)

    # Intégrations
    webhook_url: Mapped[str | None] = mapped_column(String(500))
    api_rate_limit: Mapped[int | None] = mapped_column(Integer, default=1000)

    # Backup
    auto_backup_enabled: Mapped[bool | None] = mapped_column(Boolean, default=True)
    backup_retention_days: Mapped[int | None] = mapped_column(Integer, default=30)

    # Custom
    custom_settings: Mapped[dict | None] = mapped_column(JSON)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TenantOnboarding(Base):
    """Progression de l'onboarding tenant."""
    __tablename__ = "tenant_onboarding"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, unique=True, index=True)

    # Étapes complétées
    company_info_completed: Mapped[bool | None] = mapped_column(Boolean, default=False)
    admin_created: Mapped[bool | None] = mapped_column(Boolean, default=False)
    users_invited: Mapped[bool | None] = mapped_column(Boolean, default=False)
    modules_configured: Mapped[bool | None] = mapped_column(Boolean, default=False)
    country_pack_selected: Mapped[bool | None] = mapped_column(Boolean, default=False)
    first_data_imported: Mapped[bool | None] = mapped_column(Boolean, default=False)
    training_completed: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Progression
    progress_percent: Mapped[int | None] = mapped_column(Integer, default=0)
    current_step: Mapped[str | None] = mapped_column(String(50), default="company_info")

    # Dates
    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Audit
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
