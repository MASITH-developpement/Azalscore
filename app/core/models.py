"""
AZALS - Modèles SQLAlchemy Multi-Tenant
Isolation stricte par tenant_id - AUCUNE fuite inter-tenant possible
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Index, Integer, Numeric, String, Text, func

from app.core.types import UniversalUUID
from app.db import Base


class UserRole(str, enum.Enum):
    """
    Rôles utilisateurs.
    Chaque rôle a des capacités différentes.
    """
    SUPERADMIN = "SUPERADMIN"  # Accès plateforme complet (bootstrap only)
    DIRIGEANT = "DIRIGEANT"    # Accès complet tenant
    ADMIN = "ADMIN"            # Administration système
    DAF = "DAF"                # Directeur Administratif et Financier
    COMPTABLE = "COMPTABLE"    # Comptabilité
    COMMERCIAL = "COMMERCIAL"  # Ventes et clients
    EMPLOYE = "EMPLOYE"        # Accès limité


class DecisionLevel(str, enum.Enum):
    """
    Niveaux de classification décisionnelle AZALS.
    GREEN : Opération normale
    ORANGE : Vigilance accrue
    RED : IRRÉVERSIBLE - bloque toute action automatique
    """
    GREEN = "GREEN"
    ORANGE = "ORANGE"
    RED = "RED"


class RedWorkflowStep(str, enum.Enum):
    """
    Étapes obligatoires du workflow de validation RED.
    Ordre strict : ACKNOWLEDGE → COMPLETENESS → FINAL
    Aucun retour arrière possible.
    """
    ACKNOWLEDGE = "ACKNOWLEDGE"
    COMPLETENESS = "COMPLETENESS"
    FINAL = "FINAL"


class TenantMixin:
    """
    Mixin obligatoire pour tous les modèles métier.
    Garantit la présence de tenant_id dans chaque table.
    """
    tenant_id = Column(String(255), nullable=False, index=True)


class User(Base, TenantMixin):
    """
    Modèle utilisateur avec authentification + 2FA.
    Un utilisateur est TOUJOURS lié à un tenant.
    L'accès à un endpoint nécessite JWT + X-Tenant-ID cohérent.
    ÉLITE: Support 2FA TOTP obligatoire en production.
    """
    __tablename__ = "users"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    # SÉCURITÉ P1-5: unique=False car l'unicité est par (tenant_id, email)
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.DIRIGEANT)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 2FA TOTP (ÉLITE)
    totp_secret = Column(String(32), nullable=True)  # Secret TOTP encodé base32
    totp_enabled = Column(Integer, default=0, nullable=False)  # 0=disabled, 1=enabled
    totp_verified_at = Column(DateTime, nullable=True)  # Date première vérification
    backup_codes = Column(Text, nullable=True)  # Codes de secours JSON

    # Gestion du mot de passe
    must_change_password = Column(Integer, default=0, nullable=False)  # 1=doit changer au prochain login
    password_changed_at = Column(DateTime, nullable=True)  # Date du dernier changement

    # Préférences UI
    default_view = Column(String(50), nullable=True)  # Vue par défaut après connexion (cockpit, admin, saisie, etc.)

    # SÉCURITÉ P1-5: Contrainte unique composite (tenant_id, email)
    # Permet le même email dans des tenants différents
    __table_args__ = (
        Index('idx_users_tenant_id', 'tenant_id'),
        Index('idx_users_email', 'email'),
        Index('idx_users_tenant_email', 'tenant_id', 'email', unique=True),
    )


class CoreAuditJournal(Base, TenantMixin):
    """
    Journal APPEND-ONLY inaltérable.
    - Écriture uniquement (INSERT)
    - UPDATE et DELETE interdits par triggers DB
    - Horodatage automatique côté DB
    - Trace toute action critique : tenant_id + user_id + action + détails
    """
    __tablename__ = "core_audit_journal"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (
        Index('idx_core_audit_tenant_id', 'tenant_id'),
        Index('idx_core_audit_user_id', 'user_id'),
        Index('idx_core_audit_tenant_user', 'tenant_id', 'user_id'),
        Index('idx_core_audit_created_at', 'created_at'),
    )


class Item(Base, TenantMixin):
    """
    Modèle exemple : Items métier avec isolation par tenant.
    Chaque item appartient à UN SEUL tenant.
    """
    __tablename__ = "items"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Index composite pour optimiser les requêtes par tenant
    __table_args__ = (
        Index('idx_items_tenant_id', 'tenant_id'),
        Index('idx_items_tenant_created', 'tenant_id', 'created_at'),
    )


class Decision(Base, TenantMixin):
    """
    Décisions AZALS : classification décisionnelle critique.
    - GREEN : Opération normale
    - ORANGE : Vigilance accrue
    - RED : IRRÉVERSIBLE - bloque toute action automatique

    Règle fondamentale : RED ne peut JAMAIS être rétrogradé.
    Chaque RED est automatiquement journalisé.
    """
    __tablename__ = "decisions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(255), nullable=False)
    entity_id = Column(String(255), nullable=False)
    level = Column(Enum(DecisionLevel), nullable=False)
    reason = Column(Text, nullable=False)
    # Alias pour compatibilité scheduler
    decision_reason = Column(Text, nullable=True)
    # Validation RED workflow
    is_fully_validated = Column(Integer, default=0, nullable=False)  # 0=False, 1=True
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_decisions_tenant_id', 'tenant_id'),
        Index('idx_decisions_entity', 'tenant_id', 'entity_type', 'entity_id'),
        Index('idx_decisions_level', 'level'),
        Index('idx_decisions_validated', 'level', 'is_fully_validated'),
    )


class RedDecisionWorkflow(Base, TenantMixin):
    """
    Workflow de validation DIRIGEANT pour décisions RED.
    ORDRE STRICT OBLIGATOIRE :
    1) ACKNOWLEDGE : Accusé de lecture des risques
    2) COMPLETENESS : Confirmation de complétude des informations
    3) FINAL : Confirmation finale explicite

    Règles :
    - Chaque étape ne peut être validée qu'UNE seule fois
    - Les étapes doivent être dans l'ordre strict
    - Seul le rôle DIRIGEANT peut valider
    - Chaque validation est journalisée
    - AUCUN retour arrière possible
    """
    __tablename__ = "red_decision_workflows"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    decision_id = Column(UniversalUUID(), nullable=False, index=True)
    step = Column(Enum(RedWorkflowStep), nullable=False)
    user_id = Column(UniversalUUID(), nullable=False)
    confirmed_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (
        Index('idx_red_workflow_tenant', 'tenant_id'),
        Index('idx_red_workflow_decision', 'decision_id'),
        Index('idx_red_workflow_decision_step', 'decision_id', 'step'),
    )


class RedDecisionReport(Base, TenantMixin):
    """
    Rapport 🔴 AZALS - IMMUTABLE.
    Généré AUTOMATIQUEMENT lors de la validation finale d'une décision RED.

    Règles d'immutabilité :
    - Créé UNIQUEMENT lors de l'étape FINAL du workflow RED
    - AUCUNE modification possible (aucun UPDATE)
    - AUCUNE suppression possible (aucun DELETE)
    - Un rapport par décision RED validée
    - Contient un snapshot complet des données décisionnelles

    Contenu obligatoire :
    - decision_id : Identifiant de la décision RED
    - decision_reason : Motif du RED
    - trigger_data : Snapshot JSON des données déclenchantes
    - validated_at : Date/heure validation finale
    - validator_id : Identité du DIRIGEANT validateur
    - journal_references : Liste des IDs d'entrées journal liées
    """
    __tablename__ = "red_decision_reports"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    decision_id = Column(UniversalUUID(), nullable=False, unique=True, index=True)
    decision_reason = Column(Text, nullable=False)
    trigger_data = Column(Text, nullable=False)
    validated_at = Column(DateTime, nullable=False)
    validator_id = Column(UniversalUUID(), nullable=False)
    journal_references = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (
        Index('idx_report_tenant', 'tenant_id'),
        Index('idx_report_decision', 'decision_id'),
    )


class TreasuryForecast(Base, TenantMixin):
    """
    Prévisions de trésorerie.

    Règle critique :
    - forecast_balance < 0 → décision RED automatique
    - forecast_balance = opening_balance + inflows - outflows
    """
    __tablename__ = "treasury_forecasts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=True)
    opening_balance = Column(Numeric(20, 2), nullable=False)
    inflows = Column(Numeric(20, 2), nullable=False)
    outflows = Column(Numeric(20, 2), nullable=False)
    forecast_balance = Column(Numeric(20, 2), nullable=False)
    red_triggered = Column(String(1), default='0')
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (
        Index('idx_treasury_tenant', 'tenant_id'),
        Index('idx_treasury_created', 'created_at'),
        Index('idx_treasury_red', 'tenant_id', 'red_triggered'),
    )


class UIEvent(Base, TenantMixin):
    """
    Événements UI pour audit trail et analytics décisionnel.

    Capture les interactions utilisateur pour :
    - Analyse comportement utilisateurs (module BI)
    - Optimisation UX décisionnel
    - Tracking adoption modules
    - Audit trail complet

    Données alimentent le module BI pour dashboards dirigeants.
    """
    __tablename__ = "ui_events"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    component = Column(String(200), nullable=True)
    action = Column(String(200), nullable=True)
    target = Column(String(500), nullable=True)
    event_data = Column(Text, nullable=True)  # JSON serialized (renamed from metadata)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_ui_events_tenant_type', 'tenant_id', 'event_type'),
        Index('idx_ui_events_tenant_user', 'tenant_id', 'user_id'),
        Index('idx_ui_events_timestamp', 'timestamp'),
    )


# Re-export JournalEntry pour compatibilité avec les tests existants
from app.modules.finance.models import JournalEntry, JournalEntryLine  # noqa: E402

__all__ = [
    'Base', 'TenantMixin', 'User', 'UserRole', 'DecisionLevel', 'RedWorkflowStep',
    'CoreAuditJournal', 'Item', 'Decision', 'RedDecisionWorkflow', 'RedDecisionReport',
    'TreasuryForecast', 'UIEvent', 'JournalEntry', 'JournalEntryLine'
]
