"""
AZALS - Projects Service (v2 - CRUDRouter Compatible)
==========================================================

Service compatible avec BaseService et CRUDRouter.
Migration automatique depuis service.py.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.base_service import BaseService
from app.core.saas_context import Result, SaaSContext

from app.modules.projects.models import (
    Project,
    ProjectPhase,
    ProjectTask,
    TaskDependency,
    ProjectMilestone,
    ProjectTeamMember,
    ProjectRisk,
    ProjectIssue,
    ProjectTimeEntry,
    ProjectExpense,
    ProjectDocument,
    ProjectBudget,
    ProjectProjectBudgetLine,
    ProjectTemplate,
    ProjectComment,
    ProjectKPI,
)
from app.modules.projects.schemas import (
    BudgetBase,
    BudgetCreate,
    ProjectBudgetLineCreate,
    ProjectBudgetLineResponse,
    BudgetResponse,
    BudgetUpdate,
    CommentBase,
    CommentCreate,
    CommentResponse,
    DocumentBase,
    DocumentCreate,
    DocumentResponse,
    ExpenseBase,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
    IssueBase,
    IssueCreate,
    IssueResponse,
    IssueUpdate,
    MilestoneBase,
    MilestoneCreate,
    MilestoneResponse,
    MilestoneUpdate,
    PhaseBase,
    PhaseCreate,
    PhaseResponse,
    PhaseUpdate,
    ProjectBase,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    RiskBase,
    RiskCreate,
    RiskResponse,
    RiskUpdate,
    TaskBase,
    TaskCreate,
    TaskDependencyCreate,
    TaskResponse,
    TaskUpdate,
    TeamMemberBase,
    TeamMemberCreate,
    TeamMemberResponse,
    TeamMemberUpdate,
    TemplateBase,
    TemplateCreate,
    TemplateResponse,
    TimeEntryBase,
    TimeEntryCreate,
    TimeEntryResponse,
    TimeEntryUpdate,
)

logger = logging.getLogger(__name__)



class ProjectService(BaseService[Project, Any, Any]):
    """Service CRUD pour project."""

    model = Project

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Project]
    # - get_or_fail(id) -> Result[Project]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Project]
    # - update(id, data) -> Result[Project]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ProjectPhaseService(BaseService[ProjectPhase, Any, Any]):
    """Service CRUD pour projectphase."""

    model = ProjectPhase

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ProjectPhase]
    # - get_or_fail(id) -> Result[ProjectPhase]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ProjectPhase]
    # - update(id, data) -> Result[ProjectPhase]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ProjectTaskService(BaseService[ProjectTask, Any, Any]):
    """Service CRUD pour projecttask."""

    model = ProjectTask

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ProjectTask]
    # - get_or_fail(id) -> Result[ProjectTask]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ProjectTask]
    # - update(id, data) -> Result[ProjectTask]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class TaskDependencyService(BaseService[TaskDependency, Any, Any]):
    """Service CRUD pour taskdependency."""

    model = TaskDependency

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[TaskDependency]
    # - get_or_fail(id) -> Result[TaskDependency]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[TaskDependency]
    # - update(id, data) -> Result[TaskDependency]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ProjectMilestoneService(BaseService[ProjectMilestone, Any, Any]):
    """Service CRUD pour projectmilestone."""

    model = ProjectMilestone

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ProjectMilestone]
    # - get_or_fail(id) -> Result[ProjectMilestone]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ProjectMilestone]
    # - update(id, data) -> Result[ProjectMilestone]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ProjectTeamMemberService(BaseService[ProjectTeamMember, Any, Any]):
    """Service CRUD pour projectteammember."""

    model = ProjectTeamMember

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ProjectTeamMember]
    # - get_or_fail(id) -> Result[ProjectTeamMember]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ProjectTeamMember]
    # - update(id, data) -> Result[ProjectTeamMember]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ProjectRiskService(BaseService[ProjectRisk, Any, Any]):
    """Service CRUD pour projectrisk."""

    model = ProjectRisk

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ProjectRisk]
    # - get_or_fail(id) -> Result[ProjectRisk]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ProjectRisk]
    # - update(id, data) -> Result[ProjectRisk]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ProjectIssueService(BaseService[ProjectIssue, Any, Any]):
    """Service CRUD pour projectissue."""

    model = ProjectIssue

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ProjectIssue]
    # - get_or_fail(id) -> Result[ProjectIssue]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ProjectIssue]
    # - update(id, data) -> Result[ProjectIssue]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ProjectTimeEntryService(BaseService[ProjectTimeEntry, Any, Any]):
    """Service CRUD pour projecttimeentry."""

    model = ProjectTimeEntry

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ProjectTimeEntry]
    # - get_or_fail(id) -> Result[ProjectTimeEntry]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ProjectTimeEntry]
    # - update(id, data) -> Result[ProjectTimeEntry]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ProjectExpenseService(BaseService[ProjectExpense, Any, Any]):
    """Service CRUD pour projectexpense."""

    model = ProjectExpense

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ProjectExpense]
    # - get_or_fail(id) -> Result[ProjectExpense]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ProjectExpense]
    # - update(id, data) -> Result[ProjectExpense]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ProjectDocumentService(BaseService[ProjectDocument, Any, Any]):
    """Service CRUD pour projectdocument."""

    model = ProjectDocument

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ProjectDocument]
    # - get_or_fail(id) -> Result[ProjectDocument]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ProjectDocument]
    # - update(id, data) -> Result[ProjectDocument]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ProjectBudgetService(BaseService[ProjectBudget, Any, Any]):
    """Service CRUD pour projectbudget."""

    model = ProjectBudget

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ProjectBudget]
    # - get_or_fail(id) -> Result[ProjectBudget]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ProjectBudget]
    # - update(id, data) -> Result[ProjectBudget]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ProjectBudgetLineService(BaseService[ProjectBudgetLine, Any, Any]):
    """Service CRUD pour budgetline."""

    model = ProjectBudgetLine

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ProjectBudgetLine]
    # - get_or_fail(id) -> Result[ProjectBudgetLine]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ProjectBudgetLine]
    # - update(id, data) -> Result[ProjectBudgetLine]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ProjectTemplateService(BaseService[ProjectTemplate, Any, Any]):
    """Service CRUD pour projecttemplate."""

    model = ProjectTemplate

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ProjectTemplate]
    # - get_or_fail(id) -> Result[ProjectTemplate]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ProjectTemplate]
    # - update(id, data) -> Result[ProjectTemplate]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ProjectCommentService(BaseService[ProjectComment, Any, Any]):
    """Service CRUD pour projectcomment."""

    model = ProjectComment

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ProjectComment]
    # - get_or_fail(id) -> Result[ProjectComment]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ProjectComment]
    # - update(id, data) -> Result[ProjectComment]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ProjectKPIService(BaseService[ProjectKPI, Any, Any]):
    """Service CRUD pour projectkpi."""

    model = ProjectKPI

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ProjectKPI]
    # - get_or_fail(id) -> Result[ProjectKPI]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ProjectKPI]
    # - update(id, data) -> Result[ProjectKPI]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques

