"""
AZALS MODULE M9 - Modèles Projets
=================================

Modèles SQLAlchemy pour la gestion de projets.
"""

import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Date,
    ForeignKey, Numeric, Text, Enum, Float, JSON, Index
)
from app.core.types import UniversalUUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class ProjectStatus(str, enum.Enum):
    """Statut du projet."""
    DRAFT = "draft"
    PLANNING = "planning"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ProjectPriority(str, enum.Enum):
    """Priorité du projet."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, enum.Enum):
    """Statut de la tâche."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    """Priorité de la tâche."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MilestoneStatus(str, enum.Enum):
    """Statut du jalon."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    MISSED = "missed"
    CANCELLED = "cancelled"


class RiskStatus(str, enum.Enum):
    """Statut du risque."""
    IDENTIFIED = "identified"
    ANALYZING = "analyzing"
    MITIGATING = "mitigating"
    MONITORING = "monitoring"
    OCCURRED = "occurred"
    CLOSED = "closed"


class RiskImpact(str, enum.Enum):
    """Impact du risque."""
    NEGLIGIBLE = "negligible"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


class RiskProbability(str, enum.Enum):
    """Probabilité du risque."""
    RARE = "rare"
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    ALMOST_CERTAIN = "almost_certain"


class IssueStatus(str, enum.Enum):
    """Statut du problème."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"
    WONT_FIX = "wont_fix"


class IssuePriority(str, enum.Enum):
    """Priorité du problème."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TeamMemberRole(str, enum.Enum):
    """Rôle dans l'équipe projet."""
    PROJECT_MANAGER = "project_manager"
    TEAM_LEAD = "team_lead"
    MEMBER = "member"
    STAKEHOLDER = "stakeholder"
    CONSULTANT = "consultant"
    OBSERVER = "observer"


class TimeEntryStatus(str, enum.Enum):
    """Statut de la saisie de temps."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExpenseStatus(str, enum.Enum):
    """Statut de la dépense."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class BudgetType(str, enum.Enum):
    """Type de budget."""
    CAPEX = "capex"
    OPEX = "opex"
    MIXED = "mixed"


# ============================================================================
# MODÈLES
# ============================================================================

class Project(Base):
    """Projet."""
    __tablename__ = "projects"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Classification
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False)
    priority = Column(Enum(ProjectPriority), default=ProjectPriority.MEDIUM, nullable=False)
    category = Column(String(100))
    tags = Column(JSON, default=list)

    # Dates
    planned_start_date = Column(Date)
    planned_end_date = Column(Date)
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)

    # Responsables
    project_manager_id = Column(UniversalUUID())
    sponsor_id = Column(UniversalUUID())
    customer_id = Column(UniversalUUID())  # Lien vers client commercial

    # Budget
    budget_type = Column(Enum(BudgetType))
    planned_budget = Column(Numeric(15, 2), default=0)
    actual_cost = Column(Numeric(15, 2), default=0)
    currency = Column(String(3), default="EUR")

    # Effort
    planned_hours = Column(Float, default=0)
    actual_hours = Column(Float, default=0)

    # Progression
    progress_percent = Column(Float, default=0)  # 0-100
    health_status = Column(String(20))  # green, yellow, red

    # Hiérarchie
    parent_project_id = Column(UniversalUUID(), ForeignKey("projects.id"))
    template_id = Column(UniversalUUID(), ForeignKey("project_templates.id"))

    # Paramètres
    is_billable = Column(Boolean, default=False)
    billing_rate = Column(Numeric(10, 2))
    allow_overtime = Column(Boolean, default=True)
    require_time_approval = Column(Boolean, default=True)
    settings = Column(JSON, default=dict)

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    archived_at = Column(DateTime)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relations
    phases = relationship("ProjectPhase", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("ProjectTask", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("ProjectMilestone", back_populates="project", cascade="all, delete-orphan")
    team_members = relationship("ProjectTeamMember", back_populates="project", cascade="all, delete-orphan")
    risks = relationship("ProjectRisk", back_populates="project", cascade="all, delete-orphan")
    issues = relationship("ProjectIssue", back_populates="project", cascade="all, delete-orphan")
    time_entries = relationship("ProjectTimeEntry", back_populates="project", cascade="all, delete-orphan")
    expenses = relationship("ProjectExpense", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("ProjectDocument", back_populates="project", cascade="all, delete-orphan")
    budgets = relationship("ProjectBudget", back_populates="project", cascade="all, delete-orphan")
    comments = relationship("ProjectComment", back_populates="project", cascade="all, delete-orphan")
    kpis = relationship("ProjectKPI", back_populates="project", cascade="all, delete-orphan")
    children = relationship("Project", backref="parent", remote_side=[id])

    __table_args__ = (
        Index("ix_projects_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_projects_tenant_status", "tenant_id", "status"),
        Index("ix_projects_manager", "tenant_id", "project_manager_id"),
    )


class ProjectPhase(Base):
    """Phase de projet."""
    __tablename__ = "project_phases"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    project_id = Column(UniversalUUID(), ForeignKey("projects.id"), nullable=False)

    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    order = Column(Integer, default=0)
    color = Column(String(20))

    # Dates
    planned_start_date = Column(Date)
    planned_end_date = Column(Date)
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)

    # Progression
    progress_percent = Column(Float, default=0)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)

    # Effort
    planned_hours = Column(Float, default=0)
    actual_hours = Column(Float, default=0)

    # Budget
    planned_budget = Column(Numeric(15, 2), default=0)
    actual_cost = Column(Numeric(15, 2), default=0)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    project = relationship("Project", back_populates="phases")
    tasks = relationship("ProjectTask", back_populates="phase")

    __table_args__ = (
        Index("ix_project_phases_project", "project_id"),
    )


class ProjectTask(Base):
    """Tâche de projet."""
    __tablename__ = "project_tasks"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    project_id = Column(UniversalUUID(), ForeignKey("projects.id"), nullable=False)
    phase_id = Column(UniversalUUID(), ForeignKey("project_phases.id"))
    parent_task_id = Column(UniversalUUID(), ForeignKey("project_tasks.id"))

    # Identification
    code = Column(String(50))
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Classification
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    task_type = Column(String(50))  # development, design, testing, etc.
    tags = Column(JSON, default=list)

    # Dates
    planned_start_date = Column(Date)
    planned_end_date = Column(Date)
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)
    due_date = Column(Date)

    # Assignation
    assignee_id = Column(UniversalUUID())  # Utilisateur assigné
    reporter_id = Column(UniversalUUID())  # Qui a créé la tâche

    # Effort
    estimated_hours = Column(Float, default=0)
    actual_hours = Column(Float, default=0)
    remaining_hours = Column(Float, default=0)

    # Progression
    progress_percent = Column(Float, default=0)  # 0-100

    # Hiérarchie
    order = Column(Integer, default=0)
    wbs_code = Column(String(50))  # Work Breakdown Structure

    # Options
    is_milestone = Column(Boolean, default=False)
    is_critical = Column(Boolean, default=False)
    is_billable = Column(Boolean, default=True)

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)

    # Relations
    project = relationship("Project", back_populates="tasks")
    phase = relationship("ProjectPhase", back_populates="tasks")
    children = relationship("ProjectTask", backref="parent", remote_side=[id])
    time_entries = relationship("ProjectTimeEntry", back_populates="task")
    comments = relationship("ProjectComment", back_populates="task")

    # Dépendances (predecessors)
    predecessors = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.successor_id",
        back_populates="successor"
    )
    successors = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.predecessor_id",
        back_populates="predecessor"
    )

    __table_args__ = (
        Index("ix_project_tasks_project", "project_id"),
        Index("ix_project_tasks_phase", "phase_id"),
        Index("ix_project_tasks_assignee", "tenant_id", "assignee_id"),
        Index("ix_project_tasks_status", "tenant_id", "status"),
    )


class TaskDependency(Base):
    """Dépendance entre tâches."""
    __tablename__ = "task_dependencies"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    predecessor_id = Column(UniversalUUID(), ForeignKey("project_tasks.id"), nullable=False)
    successor_id = Column(UniversalUUID(), ForeignKey("project_tasks.id"), nullable=False)

    dependency_type = Column(String(10), default="FS")  # FS, FF, SS, SF
    lag_days = Column(Integer, default=0)  # Délai entre tâches

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    predecessor = relationship("ProjectTask", foreign_keys=[predecessor_id], back_populates="successors")
    successor = relationship("ProjectTask", foreign_keys=[successor_id], back_populates="predecessors")

    __table_args__ = (
        Index("ix_task_deps_predecessor", "predecessor_id"),
        Index("ix_task_deps_successor", "successor_id"),
    )


class ProjectMilestone(Base):
    """Jalon de projet."""
    __tablename__ = "project_milestones"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    project_id = Column(UniversalUUID(), ForeignKey("projects.id"), nullable=False)
    phase_id = Column(UniversalUUID(), ForeignKey("project_phases.id"))

    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Dates
    target_date = Column(Date, nullable=False)
    actual_date = Column(Date)

    # Statut
    status = Column(Enum(MilestoneStatus), default=MilestoneStatus.PENDING, nullable=False)

    # Importance
    is_key_milestone = Column(Boolean, default=False)
    is_customer_visible = Column(Boolean, default=True)

    # Délivrables
    deliverables = Column(JSON, default=list)  # Liste des livrables attendus
    acceptance_criteria = Column(Text)

    # Validation
    validated_by = Column(UniversalUUID())
    validated_at = Column(DateTime)
    validation_notes = Column(Text)

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    project = relationship("Project", back_populates="milestones")

    __table_args__ = (
        Index("ix_project_milestones_project", "project_id"),
        Index("ix_project_milestones_date", "tenant_id", "target_date"),
    )


class ProjectTeamMember(Base):
    """Membre de l'équipe projet."""
    __tablename__ = "project_team_members"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    project_id = Column(UniversalUUID(), ForeignKey("projects.id"), nullable=False)

    # Membre
    user_id = Column(UniversalUUID(), nullable=False)  # Lien vers utilisateur
    employee_id = Column(UniversalUUID())  # Lien vers employé RH

    # Rôle
    role = Column(Enum(TeamMemberRole), default=TeamMemberRole.MEMBER, nullable=False)
    role_description = Column(String(255))

    # Allocation
    allocation_percent = Column(Float, default=100)  # % de temps alloué
    start_date = Column(Date)
    end_date = Column(Date)

    # Tarification
    hourly_rate = Column(Numeric(10, 2))
    daily_rate = Column(Numeric(10, 2))
    is_billable = Column(Boolean, default=True)

    # Permissions projet
    can_log_time = Column(Boolean, default=True)
    can_view_budget = Column(Boolean, default=False)
    can_manage_tasks = Column(Boolean, default=False)
    can_approve_time = Column(Boolean, default=False)

    # Notifications
    notify_on_task = Column(Boolean, default=True)
    notify_on_milestone = Column(Boolean, default=True)
    notify_on_issue = Column(Boolean, default=True)

    # Métadonnées
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    project = relationship("Project", back_populates="team_members")

    __table_args__ = (
        Index("ix_project_team_project", "project_id"),
        Index("ix_project_team_user", "tenant_id", "user_id"),
        Index("ix_project_team_unique", "project_id", "user_id", unique=True),
    )


class ProjectRisk(Base):
    """Risque projet."""
    __tablename__ = "project_risks"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    project_id = Column(UniversalUUID(), ForeignKey("projects.id"), nullable=False)

    # Identification
    code = Column(String(50))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # technical, schedule, budget, resources, etc.

    # Évaluation
    status = Column(Enum(RiskStatus), default=RiskStatus.IDENTIFIED, nullable=False)
    probability = Column(Enum(RiskProbability), nullable=False)
    impact = Column(Enum(RiskImpact), nullable=False)
    risk_score = Column(Float)  # Calculé: probability * impact

    # Impact financier estimé
    estimated_impact_min = Column(Numeric(15, 2))
    estimated_impact_max = Column(Numeric(15, 2))

    # Dates
    identified_date = Column(Date, default=date.today)
    review_date = Column(Date)  # Prochaine revue
    occurred_date = Column(Date)
    closed_date = Column(Date)

    # Responsable
    owner_id = Column(UniversalUUID())  # Responsable du risque

    # Réponse au risque
    response_strategy = Column(String(50))  # avoid, mitigate, transfer, accept
    mitigation_plan = Column(Text)
    contingency_plan = Column(Text)

    # Déclencheurs
    triggers = Column(JSON, default=list)  # Signes avant-coureurs

    # Suivi
    monitoring_notes = Column(Text)
    last_review_date = Column(Date)
    last_reviewed_by = Column(UniversalUUID())

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    project = relationship("Project", back_populates="risks")

    __table_args__ = (
        Index("ix_project_risks_project", "project_id"),
        Index("ix_project_risks_status", "tenant_id", "status"),
    )


class ProjectIssue(Base):
    """Problème/Issue projet."""
    __tablename__ = "project_issues"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    project_id = Column(UniversalUUID(), ForeignKey("projects.id"), nullable=False)
    task_id = Column(UniversalUUID(), ForeignKey("project_tasks.id"))

    # Identification
    code = Column(String(50))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # bug, change request, question, etc.

    # Statut
    status = Column(Enum(IssueStatus), default=IssueStatus.OPEN, nullable=False)
    priority = Column(Enum(IssuePriority), default=IssuePriority.MEDIUM, nullable=False)

    # Personnes impliquées
    reporter_id = Column(UniversalUUID())
    assignee_id = Column(UniversalUUID())

    # Dates
    reported_date = Column(Date, default=date.today)
    due_date = Column(Date)
    resolved_date = Column(Date)
    closed_date = Column(Date)

    # Impact
    impact_description = Column(Text)
    affected_areas = Column(JSON, default=list)

    # Résolution
    resolution = Column(Text)
    resolution_type = Column(String(50))  # fixed, won't fix, duplicate, by design

    # Escalade
    is_escalated = Column(Boolean, default=False)
    escalated_to_id = Column(UniversalUUID())
    escalation_date = Column(DateTime)
    escalation_reason = Column(Text)

    # Lien avec risque
    related_risk_id = Column(UniversalUUID(), ForeignKey("project_risks.id"))

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    project = relationship("Project", back_populates="issues")

    __table_args__ = (
        Index("ix_project_issues_project", "project_id"),
        Index("ix_project_issues_status", "tenant_id", "status"),
        Index("ix_project_issues_assignee", "tenant_id", "assignee_id"),
    )


class ProjectTimeEntry(Base):
    """Saisie de temps projet."""
    __tablename__ = "project_time_entries"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    project_id = Column(UniversalUUID(), ForeignKey("projects.id"), nullable=False)
    task_id = Column(UniversalUUID(), ForeignKey("project_tasks.id"))

    # Utilisateur
    user_id = Column(UniversalUUID(), nullable=False)
    employee_id = Column(UniversalUUID())

    # Date et durée
    date = Column(Date, nullable=False)
    hours = Column(Float, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)

    # Description
    description = Column(Text)
    activity_type = Column(String(50))  # development, meeting, review, etc.

    # Statut
    status = Column(Enum(TimeEntryStatus), default=TimeEntryStatus.DRAFT, nullable=False)

    # Facturation
    is_billable = Column(Boolean, default=True)
    billing_rate = Column(Numeric(10, 2))
    billing_amount = Column(Numeric(15, 2))  # hours * rate
    is_invoiced = Column(Boolean, default=False)
    invoice_id = Column(UniversalUUID())

    # Approbation
    approved_by = Column(UniversalUUID())
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)

    # Overtime
    is_overtime = Column(Boolean, default=False)
    overtime_rate = Column(Float, default=1.5)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    project = relationship("Project", back_populates="time_entries")
    task = relationship("ProjectTask", back_populates="time_entries")

    __table_args__ = (
        Index("ix_project_time_project", "project_id"),
        Index("ix_project_time_user", "tenant_id", "user_id"),
        Index("ix_project_time_date", "tenant_id", "date"),
        Index("ix_project_time_status", "tenant_id", "status"),
    )


class ProjectExpense(Base):
    """Dépense projet."""
    __tablename__ = "project_expenses"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    project_id = Column(UniversalUUID(), ForeignKey("projects.id"), nullable=False)
    task_id = Column(UniversalUUID(), ForeignKey("project_tasks.id"))
    budget_line_id = Column(UniversalUUID(), ForeignKey("project_budget_lines.id"))

    # Identification
    reference = Column(String(100))
    description = Column(Text, nullable=False)
    category = Column(String(100))  # travel, equipment, software, etc.

    # Montant
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    quantity = Column(Float, default=1)
    unit_price = Column(Numeric(15, 2))

    # Dates
    expense_date = Column(Date, nullable=False)
    due_date = Column(Date)
    paid_date = Column(Date)

    # Statut
    status = Column(Enum(ExpenseStatus), default=ExpenseStatus.DRAFT, nullable=False)

    # Personne
    submitted_by = Column(UniversalUUID())
    vendor = Column(String(255))  # Fournisseur

    # Approbation
    approved_by = Column(UniversalUUID())
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)

    # Facturation
    is_billable = Column(Boolean, default=True)
    is_invoiced = Column(Boolean, default=False)
    invoice_id = Column(UniversalUUID())

    # Pièces jointes
    receipt_url = Column(String(500))
    attachments = Column(JSON, default=list)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    project = relationship("Project", back_populates="expenses")

    __table_args__ = (
        Index("ix_project_expenses_project", "project_id"),
        Index("ix_project_expenses_status", "tenant_id", "status"),
    )


class ProjectDocument(Base):
    """Document projet."""
    __tablename__ = "project_documents"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    project_id = Column(UniversalUUID(), ForeignKey("projects.id"), nullable=False)

    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # contract, specification, report, etc.

    # Fichier
    file_name = Column(String(255))
    file_url = Column(String(500))
    file_size = Column(Integer)
    file_type = Column(String(100))

    # Versioning
    version = Column(String(20), default="1.0")
    is_latest = Column(Boolean, default=True)
    previous_version_id = Column(UniversalUUID())

    # Accès
    is_public = Column(Boolean, default=False)  # Visible par le client
    access_level = Column(String(50), default="team")  # team, managers, all

    # Métadonnées
    uploaded_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = Column(JSON, default=list)

    # Relations
    project = relationship("Project", back_populates="documents")

    __table_args__ = (
        Index("ix_project_documents_project", "project_id"),
        Index("ix_project_documents_category", "tenant_id", "category"),
    )


class ProjectBudget(Base):
    """Budget projet."""
    __tablename__ = "project_budgets"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    project_id = Column(UniversalUUID(), ForeignKey("projects.id"), nullable=False)

    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    fiscal_year = Column(String(4))
    version = Column(String(20), default="1.0")

    # Type
    budget_type = Column(Enum(BudgetType), default=BudgetType.MIXED)

    # Montants
    total_budget = Column(Numeric(15, 2), default=0)
    total_committed = Column(Numeric(15, 2), default=0)  # Engagé
    total_actual = Column(Numeric(15, 2), default=0)  # Réalisé
    total_forecast = Column(Numeric(15, 2), default=0)  # Prévisionnel
    currency = Column(String(3), default="EUR")

    # Statut
    is_approved = Column(Boolean, default=False)
    approved_by = Column(UniversalUUID())
    approved_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)

    # Dates
    start_date = Column(Date)
    end_date = Column(Date)

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    project = relationship("Project", back_populates="budgets")
    lines = relationship("BudgetLine", back_populates="budget", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_project_budgets_project", "project_id"),
    )


class BudgetLine(Base):
    """Ligne de budget."""
    __tablename__ = "project_budget_lines"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    budget_id = Column(UniversalUUID(), ForeignKey("project_budgets.id"), nullable=False)
    phase_id = Column(UniversalUUID(), ForeignKey("project_phases.id"))

    # Identification
    code = Column(String(50))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # labor, materials, equipment, etc.

    # Montants
    budget_amount = Column(Numeric(15, 2), default=0)
    committed_amount = Column(Numeric(15, 2), default=0)
    actual_amount = Column(Numeric(15, 2), default=0)
    forecast_amount = Column(Numeric(15, 2), default=0)

    # Quantités (optionnel)
    quantity = Column(Float)
    unit = Column(String(20))
    unit_price = Column(Numeric(15, 2))

    # Hiérarchie
    order = Column(Integer, default=0)
    parent_line_id = Column(UniversalUUID(), ForeignKey("project_budget_lines.id"))

    # Compte comptable
    account_code = Column(String(20))  # Lien vers plan comptable

    # Métadonnées
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    budget = relationship("ProjectBudget", back_populates="lines")
    children = relationship("BudgetLine", backref="parent", remote_side=[id])

    __table_args__ = (
        Index("ix_budget_lines_budget", "budget_id"),
    )


class ProjectTemplate(Base):
    """Template de projet."""
    __tablename__ = "project_templates"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))

    # Configuration par défaut
    default_priority = Column(Enum(ProjectPriority), default=ProjectPriority.MEDIUM)
    default_budget_type = Column(Enum(BudgetType))
    estimated_duration_days = Column(Integer)

    # Structure (phases, tâches prédéfinies)
    phases_template = Column(JSON, default=list)  # Liste des phases
    tasks_template = Column(JSON, default=list)  # Liste des tâches
    milestones_template = Column(JSON, default=list)  # Liste des jalons
    risks_template = Column(JSON, default=list)  # Risques typiques

    # Rôles requis
    roles_template = Column(JSON, default=list)  # Rôles d'équipe

    # Budget type
    budget_template = Column(JSON, default=list)  # Lignes de budget

    # Checklist
    checklist = Column(JSON, default=list)

    # Paramètres
    settings = Column(JSON, default=dict)

    # Statut
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)  # Visible par tous les tenants

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_project_templates_tenant", "tenant_id"),
    )


class ProjectComment(Base):
    """Commentaire sur projet/tâche."""
    __tablename__ = "project_comments"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    project_id = Column(UniversalUUID(), ForeignKey("projects.id"), nullable=False)
    task_id = Column(UniversalUUID(), ForeignKey("project_tasks.id"))

    # Contenu
    content = Column(Text, nullable=False)

    # Type
    comment_type = Column(String(50), default="comment")  # comment, update, note

    # Réponse
    parent_comment_id = Column(UniversalUUID(), ForeignKey("project_comments.id"))

    # Mentions
    mentions = Column(JSON, default=list)  # Liste des user_ids mentionnés

    # Attachments
    attachments = Column(JSON, default=list)

    # Visibility
    is_internal = Column(Boolean, default=True)  # False = visible par client

    # Métadonnées
    author_id = Column(UniversalUUID(), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_edited = Column(Boolean, default=False)

    # Relations
    project = relationship("Project", back_populates="comments")
    task = relationship("ProjectTask", back_populates="comments")
    replies = relationship("ProjectComment", backref="parent", remote_side=[id])

    __table_args__ = (
        Index("ix_project_comments_project", "project_id"),
        Index("ix_project_comments_task", "task_id"),
    )


class ProjectKPI(Base):
    """KPI projet."""
    __tablename__ = "project_kpis"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    project_id = Column(UniversalUUID(), ForeignKey("projects.id"), nullable=False)

    # Identification
    kpi_date = Column(Date, nullable=False)

    # Performance Planning
    planned_value = Column(Numeric(15, 2))  # Valeur planifiée (PV/BCWS)
    earned_value = Column(Numeric(15, 2))  # Valeur acquise (EV/BCWP)
    actual_cost = Column(Numeric(15, 2))  # Coût réel (AC/ACWP)

    # Indices
    schedule_variance = Column(Numeric(15, 2))  # SV = EV - PV
    cost_variance = Column(Numeric(15, 2))  # CV = EV - AC
    schedule_performance_index = Column(Float)  # SPI = EV / PV
    cost_performance_index = Column(Float)  # CPI = EV / AC

    # Estimations
    estimate_at_completion = Column(Numeric(15, 2))  # EAC
    estimate_to_complete = Column(Numeric(15, 2))  # ETC
    variance_at_completion = Column(Numeric(15, 2))  # VAC

    # Progression
    tasks_total = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    tasks_in_progress = Column(Integer, default=0)
    tasks_blocked = Column(Integer, default=0)

    # Effort
    hours_planned = Column(Float, default=0)
    hours_actual = Column(Float, default=0)
    hours_remaining = Column(Float, default=0)

    # Risques
    risks_total = Column(Integer, default=0)
    risks_open = Column(Integer, default=0)
    risks_high = Column(Integer, default=0)

    # Issues
    issues_total = Column(Integer, default=0)
    issues_open = Column(Integer, default=0)
    issues_critical = Column(Integer, default=0)

    # Qualité
    defects_found = Column(Integer, default=0)
    defects_fixed = Column(Integer, default=0)

    # Métadonnées
    calculated_at = Column(DateTime, default=datetime.utcnow)
    calculated_by = Column(UniversalUUID())

    # Relations
    project = relationship("Project", back_populates="kpis")

    __table_args__ = (
        Index("ix_project_kpis_project", "project_id"),
        Index("ix_project_kpis_date", "project_id", "kpi_date"),
    )
