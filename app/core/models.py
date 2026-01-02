"""
AZALS - Modèles SQLAlchemy Multi-Tenant
Isolation stricte par tenant_id - AUCUNE fuite inter-tenant possible
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Index, Enum, func
import enum
from app.core.database import Base


class UserRole(str, enum.Enum):
    """
    Rôles utilisateurs.
    Un seul rôle pour l'instant : DIRIGEANT.
    """
    DIRIGEANT = "DIRIGEANT"


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
    Modèle utilisateur avec authentification.
    Un utilisateur est TOUJOURS lié à un tenant.
    L'accès à un endpoint nécessite JWT + X-Tenant-ID cohérent.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.DIRIGEANT)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Index pour optimisation
    __table_args__ = (
        Index('idx_users_tenant_id', 'tenant_id'),
        Index('idx_users_email', 'email'),
        Index('idx_users_tenant_email', 'tenant_id', 'email'),
    )


class JournalEntry(Base, TenantMixin):
    """
    Journal APPEND-ONLY inaltérable.
    - Écriture uniquement (INSERT)
    - UPDATE et DELETE interdits par triggers DB
    - Horodatage automatique côté DB
    - Trace toute action critique : tenant_id + user_id + action + détails
    """
    __tablename__ = "journal_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    action = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    
    __table_args__ = (
        Index('idx_journal_tenant_id', 'tenant_id'),
        Index('idx_journal_user_id', 'user_id'),
        Index('idx_journal_tenant_user', 'tenant_id', 'user_id'),
        Index('idx_journal_created_at', 'created_at'),
    )


class Item(Base, TenantMixin):
    """
    Modèle exemple : Items métier avec isolation par tenant.
    Chaque item appartient à UN SEUL tenant.
    """
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
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
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(255), nullable=False)
    entity_id = Column(String(255), nullable=False)
    level = Column(Enum(DecisionLevel), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    
    __table_args__ = (
        Index('idx_decisions_tenant_id', 'tenant_id'),
        Index('idx_decisions_entity', 'tenant_id', 'entity_type', 'entity_id'),
        Index('idx_decisions_level', 'level'),
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
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    decision_id = Column(Integer, nullable=False, index=True)
    step = Column(Enum(RedWorkflowStep), nullable=False)
    user_id = Column(Integer, nullable=False)
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
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    decision_id = Column(Integer, nullable=False, unique=True, index=True)
    decision_reason = Column(Text, nullable=False)
    trigger_data = Column(Text, nullable=False)
    validated_at = Column(DateTime, nullable=False)
    validator_id = Column(Integer, nullable=False)
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
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, nullable=True)  # Nullable pour compatibilité données existantes
    opening_balance = Column(Integer, nullable=False)
    inflows = Column(Integer, nullable=False)
    outflows = Column(Integer, nullable=False)
    forecast_balance = Column(Integer, nullable=False)
    red_triggered = Column(Integer, default=0)  # 0 = False, 1 = True (compatibilité SQLite)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    
    __table_args__ = (
        Index('idx_treasury_tenant', 'tenant_id'),
        Index('idx_treasury_created', 'created_at'),
        Index('idx_treasury_red', 'tenant_id', 'red_triggered'),
    )
