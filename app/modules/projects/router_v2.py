"""
AZALS MODULE PROJECTS - Router API v2 (CORE SaaS)
==================================================

✅ MIGRÉ CORE SaaS Phase 2.2
- Utilise get_saas_context() au lieu de get_current_user()
- Isolation tenant automatique via context.tenant_id
- Audit trail automatique via context.user_id

API REST pour la gestion de projets.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

from .models import (
    ExpenseStatus,
    IssuePriority,
    IssueStatus,
    ProjectPriority,
    ProjectStatus,
    RiskStatus,
    TaskPriority,
    TaskStatus,
    TimeEntryStatus,
)
from .schemas import (
    BudgetCreate,
    BudgetResponse,
    CommentCreate,
    CommentResponse,
    DocumentCreate,
    DocumentResponse,
    ExpenseCreate,
    ExpenseResponse,
    IssueCreate,
    IssueResponse,
    IssueUpdate,
    MilestoneCreate,
    MilestoneResponse,
    MilestoneUpdate,
    PhaseCreate,
    PhaseResponse,
    PhaseUpdate,
    ProjectCreate,
    ProjectDashboard,
    ProjectList,
    ProjectResponse,
    ProjectStats,
    ProjectUpdate,
    RiskCreate,
    RiskResponse,
    RiskUpdate,
    TaskCreate,
    TaskList,
    TaskResponse,
    TaskUpdate,
    TeamMemberCreate,
    TeamMemberResponse,
    TeamMemberUpdate,
    TemplateCreate,
    TemplateResponse,
    TimeEntryCreate,
    TimeEntryList,
    TimeEntryResponse,
)
from .service import ProjectsService, get_projects_service

router = APIRouter(prefix="/projects", tags=["M9 - Projets"])


# ============================================================================
# SERVICE DEPENDENCY v2
# ============================================================================

def get_service_v2(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
) -> ProjectsService:
    """✅ MIGRÉ CORE SaaS: Utilise context.tenant_id et context.user_id"""
    return get_projects_service(db, context.tenant_id, context.user_id)


# ============================================================================
# PROJETS
# ============================================================================

@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.create_project(data, created_by=context.user_id)


@router.get("", response_model=ProjectList)
async def list_projects(
    status: ProjectStatus | None = None,
    priority: ProjectPriority | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister les projets"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    projects, total = service.list_projects(
        status=status,
        priority=priority,
        search=search,
        page=page,
        page_size=page_size
    )
    return ProjectList(projects=projects, total=total, page=page, page_size=page_size)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Récupérer un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Mettre à jour un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.update_project(project_id, data, updated_by=context.user_id)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Supprimer un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    service.delete_project(project_id, deleted_by=context.user_id)
    return None


@router.post("/{project_id}/refresh-progress", response_model=ProjectResponse)
async def refresh_project_progress(
    project_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Recalculer la progression du projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.refresh_project_progress(project_id)


@router.get("/{project_id}/dashboard", response_model=ProjectDashboard)
async def get_project_dashboard(
    project_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Récupérer le dashboard d'un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.get_project_dashboard(project_id)


@router.get("/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(
    project_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Récupérer les statistiques d'un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.get_project_stats(project_id)


# ============================================================================
# PHASES
# ============================================================================

@router.post("/{project_id}/phases", response_model=PhaseResponse, status_code=201)
async def create_phase(
    project_id: UUID,
    data: PhaseCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer une phase"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.create_phase(project_id, data, created_by=context.user_id)


@router.get("/{project_id}/phases", response_model=list[PhaseResponse])
async def list_phases(
    project_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister les phases d'un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.list_phases(project_id)


@router.put("/phases/{phase_id}", response_model=PhaseResponse)
async def update_phase(
    phase_id: UUID,
    data: PhaseUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Mettre à jour une phase"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.update_phase(phase_id, data, updated_by=context.user_id)


@router.delete("/phases/{phase_id}", status_code=204)
async def delete_phase(
    phase_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Supprimer une phase"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    service.delete_phase(phase_id, deleted_by=context.user_id)
    return None


# ============================================================================
# TÂCHES
# ============================================================================

@router.post("/{project_id}/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    project_id: UUID,
    data: TaskCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer une tâche"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.create_task(project_id, data, created_by=context.user_id)


@router.get("/{project_id}/tasks", response_model=TaskList)
async def list_tasks(
    project_id: UUID,
    phase_id: UUID | None = None,
    assigned_to: UUID | None = None,
    status: TaskStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister les tâches d'un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    tasks, total = service.list_tasks(
        project_id=project_id,
        phase_id=phase_id,
        assigned_to=assigned_to,
        status=status,
        page=page,
        page_size=page_size
    )
    return TaskList(tasks=tasks, total=total, page=page, page_size=page_size)


@router.get("/tasks/my", response_model=list[TaskResponse])
async def list_my_tasks(
    status: TaskStatus | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister mes tâches"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.list_my_tasks(user_id=context.user_id, status=status)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Récupérer une tâche"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Mettre à jour une tâche"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.update_task(task_id, data, updated_by=context.user_id)


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Supprimer une tâche"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    service.delete_task(task_id, deleted_by=context.user_id)
    return None


# ============================================================================
# JALONS (MILESTONES)
# ============================================================================

@router.post("/{project_id}/milestones", response_model=MilestoneResponse, status_code=201)
async def create_milestone(
    project_id: UUID,
    data: MilestoneCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer un jalon"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.create_milestone(project_id, data, created_by=context.user_id)


@router.get("/{project_id}/milestones", response_model=list[MilestoneResponse])
async def list_milestones(
    project_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister les jalons d'un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.list_milestones(project_id)


@router.put("/milestones/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    milestone_id: UUID,
    data: MilestoneUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Mettre à jour un jalon"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.update_milestone(milestone_id, data, updated_by=context.user_id)


# ============================================================================
# ÉQUIPE
# ============================================================================

@router.post("/{project_id}/team", response_model=TeamMemberResponse, status_code=201)
async def add_team_member(
    project_id: UUID,
    data: TeamMemberCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Ajouter un membre à l'équipe"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.add_team_member(project_id, data, added_by=context.user_id)


@router.get("/{project_id}/team", response_model=list[TeamMemberResponse])
async def list_team_members(
    project_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister l'équipe d'un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.list_team_members(project_id)


@router.put("/team/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(
    member_id: UUID,
    data: TeamMemberUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Mettre à jour un membre d'équipe"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.update_team_member(member_id, data, updated_by=context.user_id)


@router.delete("/team/{member_id}", status_code=204)
async def remove_team_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Retirer un membre de l'équipe"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    service.remove_team_member(member_id, removed_by=context.user_id)
    return None


# ============================================================================
# RISQUES
# ============================================================================

@router.post("/{project_id}/risks", response_model=RiskResponse, status_code=201)
async def create_risk(
    project_id: UUID,
    data: RiskCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer un risque"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.create_risk(project_id, data, created_by=context.user_id)


@router.get("/{project_id}/risks", response_model=list[RiskResponse])
async def list_risks(
    project_id: UUID,
    status: RiskStatus | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister les risques d'un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.list_risks(project_id, status=status)


@router.put("/risks/{risk_id}", response_model=RiskResponse)
async def update_risk(
    risk_id: UUID,
    data: RiskUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Mettre à jour un risque"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.update_risk(risk_id, data, updated_by=context.user_id)


# ============================================================================
# PROBLÈMES (ISSUES)
# ============================================================================

@router.post("/{project_id}/issues", response_model=IssueResponse, status_code=201)
async def create_issue(
    project_id: UUID,
    data: IssueCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer un problème"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.create_issue(project_id, data, created_by=context.user_id)


@router.get("/{project_id}/issues", response_model=list[IssueResponse])
async def list_issues(
    project_id: UUID,
    status: IssueStatus | None = None,
    priority: IssuePriority | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister les problèmes d'un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.list_issues(project_id, status=status, priority=priority)


@router.put("/issues/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: UUID,
    data: IssueUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Mettre à jour un problème"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.update_issue(issue_id, data, updated_by=context.user_id)


# ============================================================================
# TEMPS
# ============================================================================

@router.post("/{project_id}/time", response_model=TimeEntryResponse, status_code=201)
async def create_time_entry(
    project_id: UUID,
    data: TimeEntryCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer une saisie de temps"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.create_time_entry(project_id, data, user_id=context.user_id)


@router.get("/{project_id}/time", response_model=TimeEntryList)
async def list_time_entries(
    project_id: UUID,
    user_id: UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister les saisies de temps"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    entries, total = service.list_time_entries(
        project_id=project_id,
        user_id=user_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )
    return TimeEntryList(entries=entries, total=total, page=page, page_size=page_size)


@router.post("/time/{entry_id}/submit", response_model=TimeEntryResponse)
async def submit_time_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Soumettre une saisie de temps"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.submit_time_entry(entry_id)


@router.post("/time/{entry_id}/approve", response_model=TimeEntryResponse)
async def approve_time_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Approuver une saisie de temps"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.approve_time_entry(entry_id, approved_by=context.user_id)


@router.post("/time/{entry_id}/reject", response_model=TimeEntryResponse)
async def reject_time_entry(
    entry_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Rejeter une saisie de temps"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.reject_time_entry(entry_id, reason, rejected_by=context.user_id)


# ============================================================================
# DÉPENSES
# ============================================================================

@router.post("/{project_id}/expenses", response_model=ExpenseResponse, status_code=201)
async def create_expense(
    project_id: UUID,
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer une dépense"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.create_expense(project_id, data, user_id=context.user_id)


@router.get("/{project_id}/expenses", response_model=list[ExpenseResponse])
async def list_expenses(
    project_id: UUID,
    status: ExpenseStatus | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister les dépenses d'un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.list_expenses(project_id, status=status)


@router.post("/expenses/{expense_id}/approve", response_model=ExpenseResponse)
async def approve_expense(
    expense_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Approuver une dépense"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.approve_expense(expense_id, approved_by=context.user_id)


# ============================================================================
# DOCUMENTS
# ============================================================================

@router.post("/{project_id}/documents", response_model=DocumentResponse, status_code=201)
async def create_document(
    project_id: UUID,
    data: DocumentCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer un document"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.create_document(project_id, data, uploaded_by=context.user_id)


@router.get("/{project_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    project_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister les documents d'un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.list_documents(project_id)


# ============================================================================
# BUDGETS
# ============================================================================

@router.post("/{project_id}/budgets", response_model=BudgetResponse, status_code=201)
async def create_budget(
    project_id: UUID,
    data: BudgetCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer un budget"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.create_budget(project_id, data, created_by=context.user_id)


@router.get("/{project_id}/budgets", response_model=list[BudgetResponse])
async def list_budgets(
    project_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister les budgets d'un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.list_budgets(project_id)


@router.post("/budgets/{budget_id}/approve", response_model=BudgetResponse)
async def approve_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Approuver un budget"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.approve_budget(budget_id, approved_by=context.user_id)


# ============================================================================
# MODÈLES (TEMPLATES)
# ============================================================================

@router.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(
    data: TemplateCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer un modèle de projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.create_template(data, created_by=context.user_id)


@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister les modèles de projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.list_templates()


@router.post("/from-template/{template_id}", response_model=ProjectResponse, status_code=201)
async def create_project_from_template(
    template_id: UUID,
    project_name: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer un projet depuis un modèle"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.create_from_template(template_id, project_name, created_by=context.user_id)


# ============================================================================
# COMMENTAIRES
# ============================================================================

@router.post("/{project_id}/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    project_id: UUID,
    data: CommentCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer un commentaire"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.create_comment(project_id, data, user_id=context.user_id)


@router.get("/{project_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    project_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister les commentaires d'un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    return service.list_comments(project_id)


# ============================================================================
# KPIs
# ============================================================================

@router.post("/{project_id}/kpis/calculate")
async def calculate_project_kpis(
    project_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Calculer les KPIs d'un projet"""
    service = get_projects_service(db, context.tenant_id, context.user_id)
    kpis = service.calculate_project_kpis(project_id)
    return kpis
