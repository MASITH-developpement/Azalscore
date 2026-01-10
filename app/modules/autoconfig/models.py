"""
AZALS MODULE T1 - Modèles Configuration Automatique
====================================================

Modèles SQLAlchemy pour la configuration automatique par fonction.
MIGRATED: All PKs and FKs use UUID for PostgreSQL compatibility.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db import Base
from app.core.types import UniversalUUID
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional

# ============================================================================
# ENUMS
# ============================================================================

class ProfileLevel(str, enum.Enum):
    """Niveaux hiérarchiques des profils."""
    EXECUTIVE = "EXECUTIVE"      # Niveau 0-2: Direction générale
    DIRECTOR = "DIRECTOR"        # Niveau 3: Directeurs
    MANAGER = "MANAGER"          # Niveau 4: Responsables/Managers
    SPECIALIST = "SPECIALIST"    # Niveau 5: Spécialistes
    OPERATOR = "OPERATOR"        # Niveau 6: Opérateurs
    EXTERNAL = "EXTERNAL"        # Niveau 7: Externes (consultants, stagiaires)


class OverrideType(str, enum.Enum):
    """Types d'override (ajustement)."""
    EXECUTIVE = "EXECUTIVE"      # Override dirigeant
    IT_ADMIN = "IT_ADMIN"        # Override RSI/IT
    TEMPORARY = "TEMPORARY"      # Permission temporaire
    EMERGENCY = "EMERGENCY"      # Accès d'urgence


class OverrideStatus(str, enum.Enum):
    """Statut d'un override."""
    PENDING = "PENDING"          # En attente d'approbation
    APPROVED = "APPROVED"        # Approuvé
    REJECTED = "REJECTED"        # Rejeté
    EXPIRED = "EXPIRED"          # Expiré
    REVOKED = "REVOKED"          # Révoqué manuellement


class OnboardingStatus(str, enum.Enum):
    """Statut d'onboarding."""
    PENDING = "PENDING"          # En attente
    IN_PROGRESS = "IN_PROGRESS"  # En cours
    COMPLETED = "COMPLETED"      # Terminé
    FAILED = "FAILED"            # Échec


class OffboardingStatus(str, enum.Enum):
    """Statut d'offboarding."""
    SCHEDULED = "SCHEDULED"      # Planifié
    IN_PROGRESS = "IN_PROGRESS"  # En cours
    COMPLETED = "COMPLETED"      # Terminé


# ============================================================================
# MODÈLES PRINCIPAUX
# ============================================================================

class JobProfile(Base):
    """
    Profil métier définissant les droits par défaut.
    Mapping: titre/fonction → rôles → permissions → modules.
    """
    __tablename__ = "autoconfig_job_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    # Identification
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Niveau hiérarchique
    level: Mapped[Optional[str]] = mapped_column(Enum(ProfileLevel), nullable=False)
    hierarchy_order: Mapped[int] = mapped_column(Integer, default=5)  # 0=top, 10=bottom

    # Critères de matching
    title_patterns: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: ["Directeur*", "Director*"]
    department_patterns: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: ["Finance", "Comptabilité"]

    # Configuration automatique
    default_roles: Mapped[str] = mapped_column(Text)  # JSON: ["COMPTABLE", "AUDITEUR"]
    default_permissions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: permissions additionnelles
    default_modules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: ["treasury", "accounting"]

    # Sécurité
    max_data_access_level: Mapped[int] = mapped_column(Integer, default=5)  # 0=all, 5=own
    requires_mfa: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_training: Mapped[bool] = mapped_column(Boolean, default=True)

    # Configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=100)  # Plus bas = plus prioritaire

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_job_profile_code'),
        Index('idx_job_profiles_tenant', 'tenant_id'),
        Index('idx_job_profiles_level', 'level'),
        Index('idx_job_profiles_priority', 'priority'),
    )


class ProfileAssignment(Base):
    """
    Attribution d'un profil à un utilisateur.
    Historique complet des attributions.
    """
    __tablename__ = "autoconfig_profile_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    # Relation
    user_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False, index=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey('autoconfig_job_profiles.id'), nullable=False)

    # Contexte d'attribution
    job_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # Titre au moment de l'attribution
    department: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    manager_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    # Statut
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_auto: Mapped[bool] = mapped_column(Boolean, default=True)  # Attribution automatique vs manuelle

    # Audit
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assigned_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)  # NULL si automatique
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)
    revocation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relation
    profile = relationship("JobProfile")

    __table_args__ = (
        Index('idx_profile_assignments_tenant', 'tenant_id'),
        Index('idx_profile_assignments_user', 'user_id'),
        Index('idx_profile_assignments_active', 'tenant_id', 'is_active'),
    )


class PermissionOverride(Base):
    """
    Ajustement de permissions (override).
    Permet aux dirigeants et RSI de modifier les droits.
    """
    __tablename__ = "autoconfig_permission_overrides"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    # Cible
    user_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False, index=True)

    # Type d'override
    override_type: Mapped[Optional[str]] = mapped_column(Enum(OverrideType), nullable=False)
    status: Mapped[Optional[str]] = mapped_column(Enum(OverrideStatus), default=OverrideStatus.PENDING, nullable=False)

    # Contenu de l'override
    added_roles: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: rôles ajoutés
    removed_roles: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: rôles retirés
    added_permissions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: permissions ajoutées
    removed_permissions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: permissions retirées
    added_modules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: modules ajoutés
    removed_modules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: modules retirés

    # Justification
    reason: Mapped[str] = mapped_column(Text)
    business_justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Temporalité
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # NULL = immédiat
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # NULL = permanent

    # Workflow
    requested_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejected_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Application
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index('idx_overrides_tenant', 'tenant_id'),
        Index('idx_overrides_user', 'user_id'),
        Index('idx_overrides_status', 'status'),
        Index('idx_overrides_expires', 'expires_at'),
    )


class OnboardingProcess(Base):
    """
    Processus d'onboarding pour un nouvel employé.
    Suivi complet de l'intégration.
    """
    __tablename__ = "autoconfig_onboarding"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    # Employé
    user_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True, index=True)  # NULL jusqu'à création
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Poste
    job_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    manager_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime)

    # Profil détecté
    detected_profile_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey('autoconfig_job_profiles.id'), nullable=True)
    profile_override: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)  # Si override manuel

    # Statut
    status: Mapped[Optional[str]] = mapped_column(Enum(OnboardingStatus), default=OnboardingStatus.PENDING, nullable=False)

    # Étapes complétées (JSON)
    steps_completed: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # {"account_created": true, ...}

    # Notifications
    welcome_email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    manager_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    it_notified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relation
    detected_profile = relationship("JobProfile")

    __table_args__ = (
        Index('idx_onboarding_tenant', 'tenant_id'),
        Index('idx_onboarding_status', 'status'),
        Index('idx_onboarding_start', 'start_date'),
    )


class OffboardingProcess(Base):
    """
    Processus d'offboarding pour un départ.
    Gestion de la révocation des accès.
    """
    __tablename__ = "autoconfig_offboarding"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    # Employé
    user_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False, index=True)

    # Départ
    departure_date: Mapped[datetime] = mapped_column(DateTime)
    departure_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)  # resignation, termination, end_of_contract

    # Transfert
    transfer_to_user_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)  # Transfert responsabilités
    transfer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Statut
    status: Mapped[Optional[str]] = mapped_column(Enum(OffboardingStatus), default=OffboardingStatus.SCHEDULED, nullable=False)

    # Étapes (JSON)
    steps_completed: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Actions
    account_deactivated: Mapped[bool] = mapped_column(Boolean, default=False)
    access_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    data_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    data_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Notifications
    manager_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    it_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    team_notified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_offboarding_tenant', 'tenant_id'),
        Index('idx_offboarding_status', 'status'),
        Index('idx_offboarding_departure', 'departure_date'),
    )


class AutoConfigRule(Base):
    """
    Règle de configuration automatique personnalisable.
    Permet de définir des règles métier spécifiques.
    """
    __tablename__ = "autoconfig_rules"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    # Identification
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Condition (JSON)
    # Ex: {"field": "department", "operator": "equals", "value": "Finance"}
    condition: Mapped[str] = mapped_column(Text)

    # Action (JSON)
    # Ex: {"action": "add_role", "role": "COMPTABLE"}
    action: Mapped[str] = mapped_column(Text)

    # Configuration
    priority: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_autoconfig_rule_code'),
        Index('idx_autoconfig_rules_tenant', 'tenant_id'),
        Index('idx_autoconfig_rules_priority', 'priority'),
    )


class AutoConfigLog(Base):
    """
    Log des actions de configuration automatique.
    Traçabilité complète des attributions et modifications.
    """
    __tablename__ = "autoconfig_logs"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    # Action
    action: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)  # PROFILE, OVERRIDE, ONBOARDING, etc.
    entity_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    # Cible
    user_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    # Détails
    old_values: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    new_values: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Source
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)  # AUTO, MANUAL, SCHEDULED
    triggered_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    # Résultat
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.current_timestamp(), nullable=False)

    __table_args__ = (
        Index('idx_autoconfig_logs_tenant', 'tenant_id'),
        Index('idx_autoconfig_logs_action', 'action'),
        Index('idx_autoconfig_logs_user', 'user_id'),
        Index('idx_autoconfig_logs_created', 'created_at'),
    )
