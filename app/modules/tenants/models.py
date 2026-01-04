"""
AZALS MODULE T9 - Modèles Tenants
==================================

Modèles SQLAlchemy pour la gestion des tenants.
"""

import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Enum, JSON, Float
)
from sqlalchemy.orm import relationship
from app.core.database import Base


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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), unique=True, nullable=False, index=True)

    # Informations entreprise
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255))
    siret = Column(String(20))
    vat_number = Column(String(30))

    # Adresse
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(2), default="FR")

    # Contact
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    website = Column(String(255))

    # Statut et plan
    status = Column(Enum(TenantStatus), default=TenantStatus.PENDING)
    plan = Column(Enum(SubscriptionPlan), default=SubscriptionPlan.STARTER)

    # Configuration
    timezone = Column(String(50), default="Europe/Paris")
    language = Column(String(5), default="fr")
    currency = Column(String(3), default="EUR")
    date_format = Column(String(20), default="DD/MM/YYYY")

    # Limites
    max_users = Column(Integer, default=5)
    max_storage_gb = Column(Integer, default=10)
    storage_used_gb = Column(Float, default=0)

    # Branding
    logo_url = Column(String(500))
    primary_color = Column(String(7), default="#1976D2")
    secondary_color = Column(String(7), default="#424242")

    # Fonctionnalités
    features = Column(JSON)  # {"feature1": true, "feature2": false}

    # Données supplémentaires
    metadata = Column(JSON)

    # Dates
    trial_ends_at = Column(DateTime)
    activated_at = Column(DateTime)
    suspended_at = Column(DateTime)
    cancelled_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))


class TenantSubscription(Base):
    """Abonnement d'un tenant."""
    __tablename__ = "tenant_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Plan
    plan = Column(Enum(SubscriptionPlan), nullable=False)
    billing_cycle = Column(Enum(BillingCycle), default=BillingCycle.MONTHLY)

    # Prix
    price_monthly = Column(Float)
    price_yearly = Column(Float)
    discount_percent = Column(Float, default=0)

    # Période
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime)
    next_billing_at = Column(DateTime)

    # Statut
    is_active = Column(Boolean, default=True)
    is_trial = Column(Boolean, default=False)
    auto_renew = Column(Boolean, default=True)

    # Paiement
    payment_method = Column(String(50))
    last_payment_at = Column(DateTime)
    last_payment_amount = Column(Float)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TenantModule(Base):
    """Module activé pour un tenant."""
    __tablename__ = "tenant_modules"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Module
    module_code = Column(String(10), nullable=False)
    module_name = Column(String(100))
    module_version = Column(String(20))

    # Statut
    status = Column(Enum(ModuleStatus), default=ModuleStatus.ACTIVE)

    # Configuration
    config = Column(JSON)
    limits = Column(JSON)  # {"max_records": 1000}

    # Dates
    activated_at = Column(DateTime, default=datetime.utcnow)
    deactivated_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TenantInvitation(Base):
    """Invitation à rejoindre un tenant."""
    __tablename__ = "tenant_invitations"

    id = Column(Integer, primary_key=True, index=True)

    # Invitation
    token = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), nullable=False, index=True)

    # Tenant cible (nouveau ou existant)
    tenant_id = Column(String(50))
    tenant_name = Column(String(255))
    plan = Column(Enum(SubscriptionPlan))

    # Rôle proposé
    proposed_role = Column(String(50), default="TENANT_ADMIN")

    # Statut
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING)

    # Dates
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))


class TenantUsage(Base):
    """Utilisation des ressources par tenant."""
    __tablename__ = "tenant_usage"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Période
    date = Column(DateTime, nullable=False, index=True)
    period = Column(String(20), default="daily")

    # Utilisateurs
    active_users = Column(Integer, default=0)
    total_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)

    # Stockage
    storage_used_gb = Column(Float, default=0)
    files_count = Column(Integer, default=0)

    # API
    api_calls = Column(Integer, default=0)
    api_errors = Column(Integer, default=0)

    # Modules
    module_usage = Column(JSON)  # {"M1": 100, "M2": 50}

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)


class TenantEvent(Base):
    """Événements tenant (audit)."""
    __tablename__ = "tenant_events"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Événement
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSON)
    description = Column(Text)

    # Acteur
    actor_id = Column(Integer)
    actor_email = Column(String(255))
    actor_ip = Column(String(50))

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)


class TenantSettings(Base):
    """Paramètres avancés du tenant."""
    __tablename__ = "tenant_settings"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, unique=True, index=True)

    # Sécurité
    two_factor_required = Column(Boolean, default=False)
    session_timeout_minutes = Column(Integer, default=30)
    password_expiry_days = Column(Integer, default=90)
    ip_whitelist = Column(JSON)

    # Notifications
    notify_admin_on_signup = Column(Boolean, default=True)
    notify_admin_on_error = Column(Boolean, default=True)
    daily_digest_enabled = Column(Boolean, default=True)

    # Intégrations
    webhook_url = Column(String(500))
    api_rate_limit = Column(Integer, default=1000)

    # Backup
    auto_backup_enabled = Column(Boolean, default=True)
    backup_retention_days = Column(Integer, default=30)

    # Custom
    custom_settings = Column(JSON)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TenantOnboarding(Base):
    """Progression de l'onboarding tenant."""
    __tablename__ = "tenant_onboarding"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, unique=True, index=True)

    # Étapes complétées
    company_info_completed = Column(Boolean, default=False)
    admin_created = Column(Boolean, default=False)
    users_invited = Column(Boolean, default=False)
    modules_configured = Column(Boolean, default=False)
    country_pack_selected = Column(Boolean, default=False)
    first_data_imported = Column(Boolean, default=False)
    training_completed = Column(Boolean, default=False)

    # Progression
    progress_percent = Column(Integer, default=0)
    current_step = Column(String(50), default="company_info")

    # Dates
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Audit
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
