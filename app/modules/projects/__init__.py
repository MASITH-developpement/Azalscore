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
    BudgetLine,
    BudgetType,
    ExpenseStatus,
    IssuePriority,
    IssueStatus,
    MilestoneStatus,
    # Models
    Project,
    ProjectBudget,
    ProjectComment,
    ProjectDocument,
    ProjectExpense,
    ProjectIssue,
    ProjectKPI,
    ProjectMilestone,
    ProjectPhase,
    ProjectPriority,
    ProjectRisk,
    # Enums
    ProjectStatus,
    ProjectTask,
    ProjectTeamMember,
    ProjectTemplate,
    ProjectTimeEntry,
    RiskImpact,
    RiskProbability,
    RiskStatus,
    TaskDependency,
    TaskPriority,
    TaskStatus,
    TeamMemberRole,
    TimeEntryStatus,
)
from .schemas import (
    # Budget
    BudgetCreate,
    BudgetLineCreate,
    BudgetResponse,
    BudgetUpdate,
    BurndownData,
    # Comment
    CommentCreate,
    CommentResponse,
    # Document
    DocumentCreate,
    DocumentResponse,
    # Expense
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
    # Issue
    IssueCreate,
    IssueList,
    IssueResponse,
    IssueUpdate,
    # Milestone
    MilestoneCreate,
    MilestoneResponse,
    MilestoneUpdate,
    # Phase
    PhaseCreate,
    PhaseResponse,
    PhaseUpdate,
    # Project
    ProjectCreate,
    # Dashboard
    ProjectDashboard,
    ProjectList,
    ProjectResponse,
    ProjectStats,
    ProjectSummary,
    ProjectUpdate,
    # Risk
    RiskCreate,
    RiskList,
    RiskResponse,
    RiskUpdate,
    # Task
    TaskCreate,
    TaskDependencyCreate,
    TaskList,
    TaskResponse,
    TaskUpdate,
    # Team
    TeamMemberCreate,
    TeamMemberResponse,
    TeamMemberUpdate,
    # Template
    TemplateCreate,
    TemplateResponse,
    # Time
    TimeEntryCreate,
    TimeEntryList,
    TimeEntryResponse,
    TimeEntryUpdate,
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
