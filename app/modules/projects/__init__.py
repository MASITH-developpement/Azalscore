"""
AZALS MODULE M9 - Gestion de Projets
====================================

Module complet de gestion de projets (Project Management).

Fonctionnalités:
- Projets avec phases et jalons
- Tâches avec dépendances et assignations
- Équipes projet et rôles
- Gestion des risques
- Suivi des problèmes/issues
- Gestion du temps (timesheet)
- Suivi budgétaire et dépenses
- Documents projet
- Templates de projets
- KPIs et dashboard

Architecture:
- Multi-tenant strict (tenant_id sur toutes les tables)
- Permissions granulaires
- Audit trail complet
- Intégration HR pour les ressources
"""

from .models import (
    # Enums
    ProjectStatus, ProjectPriority, TaskStatus, TaskPriority,
    MilestoneStatus, RiskStatus, RiskImpact, RiskProbability,
    IssueStatus, IssuePriority, TeamMemberRole, TimeEntryStatus,
    ExpenseStatus, BudgetType,
    # Models
    Project, ProjectPhase, ProjectTask, TaskDependency,
    ProjectMilestone, ProjectTeamMember, ProjectRisk,
    ProjectIssue, ProjectTimeEntry, ProjectExpense,
    ProjectDocument, ProjectBudget, BudgetLine,
    ProjectTemplate, ProjectComment, ProjectKPI
)

from .schemas import (
    # Project
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectList, ProjectSummary,
    # Phase
    PhaseCreate, PhaseUpdate, PhaseResponse,
    # Task
    TaskCreate, TaskUpdate, TaskResponse, TaskList, TaskDependencyCreate,
    # Milestone
    MilestoneCreate, MilestoneUpdate, MilestoneResponse,
    # Team
    TeamMemberCreate, TeamMemberUpdate, TeamMemberResponse,
    # Risk
    RiskCreate, RiskUpdate, RiskResponse, RiskList,
    # Issue
    IssueCreate, IssueUpdate, IssueResponse, IssueList,
    # Time
    TimeEntryCreate, TimeEntryUpdate, TimeEntryResponse, TimeEntryList,
    # Expense
    ExpenseCreate, ExpenseUpdate, ExpenseResponse,
    # Document
    DocumentCreate, DocumentResponse,
    # Budget
    BudgetCreate, BudgetUpdate, BudgetResponse, BudgetLineCreate,
    # Template
    TemplateCreate, TemplateResponse,
    # Comment
    CommentCreate, CommentResponse,
    # Dashboard
    ProjectDashboard, ProjectStats, BurndownData
)

from .service import get_projects_service

__all__ = [
    # Enums
    "ProjectStatus", "ProjectPriority", "TaskStatus", "TaskPriority",
    "MilestoneStatus", "RiskStatus", "RiskImpact", "RiskProbability",
    "IssueStatus", "IssuePriority", "TeamMemberRole", "TimeEntryStatus",
    "ExpenseStatus", "BudgetType",
    # Models
    "Project", "ProjectPhase", "ProjectTask", "TaskDependency",
    "ProjectMilestone", "ProjectTeamMember", "ProjectRisk",
    "ProjectIssue", "ProjectTimeEntry", "ProjectExpense",
    "ProjectDocument", "ProjectBudget", "BudgetLine",
    "ProjectTemplate", "ProjectComment", "ProjectKPI",
    # Schemas
    "ProjectCreate", "ProjectUpdate", "ProjectResponse", "ProjectList", "ProjectSummary",
    "PhaseCreate", "PhaseUpdate", "PhaseResponse",
    "TaskCreate", "TaskUpdate", "TaskResponse", "TaskList", "TaskDependencyCreate",
    "MilestoneCreate", "MilestoneUpdate", "MilestoneResponse",
    "TeamMemberCreate", "TeamMemberUpdate", "TeamMemberResponse",
    "RiskCreate", "RiskUpdate", "RiskResponse", "RiskList",
    "IssueCreate", "IssueUpdate", "IssueResponse", "IssueList",
    "TimeEntryCreate", "TimeEntryUpdate", "TimeEntryResponse", "TimeEntryList",
    "ExpenseCreate", "ExpenseUpdate", "ExpenseResponse",
    "DocumentCreate", "DocumentResponse",
    "BudgetCreate", "BudgetUpdate", "BudgetResponse", "BudgetLineCreate",
    "TemplateCreate", "TemplateResponse",
    "CommentCreate", "CommentResponse",
    "ProjectDashboard", "ProjectStats", "BurndownData",
    # Service
    "get_projects_service",
]
