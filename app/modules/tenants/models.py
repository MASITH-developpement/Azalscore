"""
AZALS MODULE T9 - Modèles Tenants
==================================

Modèles SQLAlchemy pour la gestion des tenants.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text

from app.db import Base
from app.core.types import JSON, UniversalUUID
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

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
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Informations entreprise
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(255))
    siret: Mapped[Optional[str]] = mapped_column(String(20))
    vat_number: Mapped[Optional[str]] = mapped_column(String(30))

    # Adresse
    address_line1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[Optional[str]] = mapped_column(String(2), default="FR")

    # Contact
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    website: Mapped[Optional[str]] = mapped_column(String(255))

    # Statut et plan
    status: Mapped[Optional[str]] = mapped_column(Enum(TenantStatus), default=TenantStatus.PENDING)
    plan: Mapped[Optional[str]] = mapped_column(Enum(SubscriptionPlan), default=SubscriptionPlan.STARTER)

    # Environnement (beta, production, staging, development)
    environment: Mapped[Optional[str]] = mapped_column(
        Enum(TenantEnvironment),
        default=TenantEnvironment.PRODUCTION,
        nullable=False
    )

    # Configuration
    timezone: Mapped[Optional[str]] = mapped_column(String(50), default="Europe/Paris")
    language: Mapped[Optional[str]] = mapped_column(String(5), default="fr")
    currency: Mapped[Optional[str]] = mapped_column(String(3), default="EUR")
    date_format: Mapped[Optional[str]] = mapped_column(String(20), default="DD/MM/YYYY")

    # Limites
    max_users: Mapped[Optional[int]] = mapped_column(Integer, default=5)
    max_storage_gb: Mapped[Optional[int]] = mapped_column(Integer, default=10)
    storage_used_gb: Mapped[Optional[float]] = mapped_column(Float, default=0)

    # Branding
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    primary_color: Mapped[Optional[str]] = mapped_column(String(7), default="#1976D2")
    secondary_color: Mapped[Optional[str]] = mapped_column(String(7), default="#424242")

    # Fonctionnalités
    features: Mapped[Optional[dict]] = mapped_column(JSON)  # {"feature1": true, "feature2": false}

    # Données supplémentaires
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON)

    # Dates
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    suspended_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(100))


class TenantSubscription(Base):
    """Abonnement d'un tenant."""
    __tablename__ = "tenant_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Plan
    plan: Mapped[Optional[str]] = mapped_column(Enum(SubscriptionPlan), nullable=False)
    billing_cycle: Mapped[Optional[str]] = mapped_column(Enum(BillingCycle), default=BillingCycle.MONTHLY)

    # Prix
    price_monthly: Mapped[Optional[float]] = mapped_column(Float)
    price_yearly: Mapped[Optional[float]] = mapped_column(Float)
    discount_percent: Mapped[Optional[float]] = mapped_column(Float, default=0)

    # Période
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_billing_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Statut
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    is_trial: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    auto_renew: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    # Paiement
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    last_payment_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_payment_amount: Mapped[Optional[float]] = mapped_column(Float)

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TenantModule(Base):
    """Module activé pour un tenant."""
    __tablename__ = "tenant_modules"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Module
    module_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=False)
    module_name: Mapped[Optional[str]] = mapped_column(String(100))
    module_version: Mapped[Optional[str]] = mapped_column(String(20))

    # Statut
    status: Mapped[Optional[str]] = mapped_column(Enum(ModuleStatus), default=ModuleStatus.ACTIVE)

    # Configuration
    config: Mapped[Optional[dict]] = mapped_column(JSON)
    limits: Mapped[Optional[dict]] = mapped_column(JSON)  # {"max_records": 1000}

    # Dates
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TenantInvitation(Base):
    """Invitation à rejoindre un tenant."""
    __tablename__ = "tenant_invitations"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)

    # Invitation
    token: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    # Tenant cible (nouveau ou existant)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50))
    tenant_name: Mapped[Optional[str]] = mapped_column(String(255))
    plan: Mapped[Optional[str]] = mapped_column(Enum(SubscriptionPlan))

    # Rôle proposé
    proposed_role: Mapped[Optional[str]] = mapped_column(String(50), default="TENANT_ADMIN")

    # Statut
    status: Mapped[Optional[str]] = mapped_column(Enum(InvitationStatus), default=InvitationStatus.PENDING)

    # Dates
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(100))


class TenantUsage(Base):
    """Utilisation des ressources par tenant."""
    __tablename__ = "tenant_usage"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Période
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    period: Mapped[Optional[str]] = mapped_column(String(20), default="daily")

    # Utilisateurs
    active_users: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    total_users: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    new_users: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Stockage
    storage_used_gb: Mapped[Optional[float]] = mapped_column(Float, default=0)
    files_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # API
    api_calls: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    api_errors: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Modules
    module_usage: Mapped[Optional[dict]] = mapped_column(JSON)  # {"M1": 100, "M2": 50}

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)


class TenantEvent(Base):
    """Événements tenant (audit)."""
    __tablename__ = "tenant_events"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Événement
    event_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)
    event_data: Mapped[Optional[dict]] = mapped_column(JSON)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Acteur
    actor_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    actor_email: Mapped[Optional[str]] = mapped_column(String(255))
    actor_ip: Mapped[Optional[str]] = mapped_column(String(50))

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)


class TenantSettings(Base):
    """Paramètres avancés du tenant."""
    __tablename__ = "tenant_settings"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, unique=True, index=True)

    # Sécurité
    two_factor_required: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    session_timeout_minutes: Mapped[Optional[int]] = mapped_column(Integer, default=30)
    password_expiry_days: Mapped[Optional[int]] = mapped_column(Integer, default=90)
    ip_whitelist: Mapped[Optional[dict]] = mapped_column(JSON)

    # Notifications
    notify_admin_on_signup: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    notify_admin_on_error: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    daily_digest_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    # Intégrations
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500))
    api_rate_limit: Mapped[Optional[int]] = mapped_column(Integer, default=1000)

    # Backup
    auto_backup_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    backup_retention_days: Mapped[Optional[int]] = mapped_column(Integer, default=30)

    # Custom
    custom_settings: Mapped[Optional[dict]] = mapped_column(JSON)

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TenantOnboarding(Base):
    """Progression de l'onboarding tenant."""
    __tablename__ = "tenant_onboarding"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, unique=True, index=True)

    # Étapes complétées
    company_info_completed: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    admin_created: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    users_invited: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    modules_configured: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    country_pack_selected: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    first_data_imported: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    training_completed: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Progression
    progress_percent: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    current_step: Mapped[Optional[str]] = mapped_column(String(50), default="company_info")

    # Dates
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Audit
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
