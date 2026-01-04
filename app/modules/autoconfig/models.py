"""
AZALS MODULE T1 - Modèles Configuration Automatique
====================================================

Modèles SQLAlchemy pour la configuration automatique par fonction.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Boolean, ForeignKey,
    Index, Enum, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Niveau hiérarchique
    level = Column(Enum(ProfileLevel), nullable=False)
    hierarchy_order = Column(Integer, default=5, nullable=False)  # 0=top, 10=bottom

    # Critères de matching
    title_patterns = Column(Text, nullable=True)  # JSON: ["Directeur*", "Director*"]
    department_patterns = Column(Text, nullable=True)  # JSON: ["Finance", "Comptabilité"]

    # Configuration automatique
    default_roles = Column(Text, nullable=False)  # JSON: ["COMPTABLE", "AUDITEUR"]
    default_permissions = Column(Text, nullable=True)  # JSON: permissions additionnelles
    default_modules = Column(Text, nullable=True)  # JSON: ["treasury", "accounting"]

    # Sécurité
    max_data_access_level = Column(Integer, default=5, nullable=False)  # 0=all, 5=own
    requires_mfa = Column(Boolean, default=False, nullable=False)
    requires_training = Column(Boolean, default=True, nullable=False)

    # Configuration
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)
    priority = Column(Integer, default=100, nullable=False)  # Plus bas = plus prioritaire

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Relation
    user_id = Column(Integer, nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey('autoconfig_job_profiles.id'), nullable=False)

    # Contexte d'attribution
    job_title = Column(String(200), nullable=True)  # Titre au moment de l'attribution
    department = Column(String(200), nullable=True)
    manager_id = Column(Integer, nullable=True)

    # Statut
    is_active = Column(Boolean, default=True, nullable=False)
    is_auto = Column(Boolean, default=True, nullable=False)  # Attribution automatique vs manuelle

    # Audit
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = Column(Integer, nullable=True)  # NULL si automatique
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(Integer, nullable=True)
    revocation_reason = Column(Text, nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Cible
    user_id = Column(Integer, nullable=False, index=True)

    # Type d'override
    override_type = Column(Enum(OverrideType), nullable=False)
    status = Column(Enum(OverrideStatus), default=OverrideStatus.PENDING, nullable=False)

    # Contenu de l'override
    added_roles = Column(Text, nullable=True)  # JSON: rôles ajoutés
    removed_roles = Column(Text, nullable=True)  # JSON: rôles retirés
    added_permissions = Column(Text, nullable=True)  # JSON: permissions ajoutées
    removed_permissions = Column(Text, nullable=True)  # JSON: permissions retirées
    added_modules = Column(Text, nullable=True)  # JSON: modules ajoutés
    removed_modules = Column(Text, nullable=True)  # JSON: modules retirés

    # Justification
    reason = Column(Text, nullable=False)
    business_justification = Column(Text, nullable=True)

    # Temporalité
    starts_at = Column(DateTime, nullable=True)  # NULL = immédiat
    expires_at = Column(DateTime, nullable=True)  # NULL = permanent

    # Workflow
    requested_by = Column(Integer, nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_by = Column(Integer, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_by = Column(Integer, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Application
    applied_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(Integer, nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Employé
    user_id = Column(Integer, nullable=True, index=True)  # NULL jusqu'à création
    email = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)

    # Poste
    job_title = Column(String(200), nullable=False)
    department = Column(String(200), nullable=True)
    manager_id = Column(Integer, nullable=True)
    start_date = Column(DateTime, nullable=False)

    # Profil détecté
    detected_profile_id = Column(Integer, ForeignKey('autoconfig_job_profiles.id'), nullable=True)
    profile_override = Column(Integer, nullable=True)  # Si override manuel

    # Statut
    status = Column(Enum(OnboardingStatus), default=OnboardingStatus.PENDING, nullable=False)

    # Étapes complétées (JSON)
    steps_completed = Column(Text, nullable=True)  # {"account_created": true, ...}

    # Notifications
    welcome_email_sent = Column(Boolean, default=False, nullable=False)
    manager_notified = Column(Boolean, default=False, nullable=False)
    it_notified = Column(Boolean, default=False, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=True)
    completed_at = Column(DateTime, nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Employé
    user_id = Column(Integer, nullable=False, index=True)

    # Départ
    departure_date = Column(DateTime, nullable=False)
    departure_type = Column(String(50), nullable=False)  # resignation, termination, end_of_contract

    # Transfert
    transfer_to_user_id = Column(Integer, nullable=True)  # Transfert responsabilités
    transfer_notes = Column(Text, nullable=True)

    # Statut
    status = Column(Enum(OffboardingStatus), default=OffboardingStatus.SCHEDULED, nullable=False)

    # Étapes (JSON)
    steps_completed = Column(Text, nullable=True)

    # Actions
    account_deactivated = Column(Boolean, default=False, nullable=False)
    access_revoked = Column(Boolean, default=False, nullable=False)
    data_archived = Column(Boolean, default=False, nullable=False)
    data_deleted = Column(Boolean, default=False, nullable=False)

    # Notifications
    manager_notified = Column(Boolean, default=False, nullable=False)
    it_notified = Column(Boolean, default=False, nullable=False)
    team_notified = Column(Boolean, default=False, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=True)
    completed_at = Column(DateTime, nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Condition (JSON)
    # Ex: {"field": "department", "operator": "equals", "value": "Finance"}
    condition = Column(Text, nullable=False)

    # Action (JSON)
    # Ex: {"action": "add_role", "role": "COMPTABLE"}
    action = Column(Text, nullable=False)

    # Configuration
    priority = Column(Integer, default=100, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Action
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)  # PROFILE, OVERRIDE, ONBOARDING, etc.
    entity_id = Column(Integer, nullable=True)

    # Cible
    user_id = Column(Integer, nullable=True)

    # Détails
    old_values = Column(Text, nullable=True)  # JSON
    new_values = Column(Text, nullable=True)  # JSON
    details = Column(Text, nullable=True)

    # Source
    source = Column(String(50), nullable=False)  # AUTO, MANUAL, SCHEDULED
    triggered_by = Column(Integer, nullable=True)

    # Résultat
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)

    __table_args__ = (
        Index('idx_autoconfig_logs_tenant', 'tenant_id'),
        Index('idx_autoconfig_logs_action', 'action'),
        Index('idx_autoconfig_logs_user', 'user_id'),
        Index('idx_autoconfig_logs_created', 'created_at'),
    )
