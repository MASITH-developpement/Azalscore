"""
AZALS MODULE M9 - Router Projets
================================

API REST pour la gestion de projets.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User

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
from .service import get_projects_service

router = APIRouter(prefix="/api/v1/projects", tags=["Projets (Project Management)"])


# ============================================================================
# PROJETS
# ============================================================================

@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un nouveau projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    return service.create_project(data)


@router.get("", response_model=ProjectList)
def list_projects(
    status: ProjectStatus | None = None,
    priority: ProjectPriority | None = None,
    project_manager_id: UUID | None = None,
    customer_id: UUID | None = None,
    category: str | None = None,
    is_active: bool = True,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les projets."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    projects, total = service.list_projects(
        status, priority, project_manager_id, customer_id,
        category, is_active, search, skip, limit
    )
    return {"items": projects, "total": total, "page": skip // limit + 1, "page_size": limit}


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    project = service.update_project(project_id, data)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archiver un projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    if not service.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Projet non trouvé")


@router.post("/{project_id}/refresh-progress", response_model=ProjectResponse)
def refresh_project_progress(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recalculer la progression du projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    project = service.update_project_progress(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return project


@router.get("/{project_id}/dashboard", response_model=ProjectDashboard)
def get_project_dashboard(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir le dashboard du projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    dashboard = service.get_dashboard(project_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return dashboard


@router.get("/{project_id}/stats", response_model=ProjectStats)
def get_project_stats(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir les statistiques du projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    stats = service.get_project_stats(project_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return stats


# ============================================================================
# PHASES
# ============================================================================

@router.post("/{project_id}/phases", response_model=PhaseResponse, status_code=201)
def create_phase(
    project_id: UUID,
    data: PhaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une phase."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return service.create_phase(project_id, data)


@router.get("/{project_id}/phases", response_model=list[PhaseResponse])
def get_phases(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les phases d'un projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    return service.get_phases(project_id)


@router.put("/phases/{phase_id}", response_model=PhaseResponse)
def update_phase(
    phase_id: UUID,
    data: PhaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour une phase."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    phase = service.update_phase(phase_id, data)
    if not phase:
        raise HTTPException(status_code=404, detail="Phase non trouvée")
    return phase


@router.delete("/phases/{phase_id}", status_code=204)
def delete_phase(
    phase_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer une phase."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    if not service.delete_phase(phase_id):
        raise HTTPException(status_code=404, detail="Phase non trouvée")


# ============================================================================
# TÂCHES
# ============================================================================

@router.post("/{project_id}/tasks", response_model=TaskResponse, status_code=201)
def create_task(
    project_id: UUID,
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une tâche."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return service.create_task(project_id, data)


@router.get("/{project_id}/tasks", response_model=TaskList)
def list_project_tasks(
    project_id: UUID,
    phase_id: UUID | None = None,
    assignee_id: UUID | None = None,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    is_overdue: bool = False,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les tâches d'un projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    tasks, total = service.list_tasks(
        project_id, phase_id, assignee_id, status, priority, is_overdue, search, skip, limit
    )
    return {"items": tasks, "total": total, "page": skip // limit + 1, "page_size": limit}


@router.get("/tasks/my", response_model=list[TaskResponse])
def get_my_tasks(
    status: TaskStatus | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer mes tâches."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    return service.get_my_tasks(status, limit)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une tâche."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: UUID,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour une tâche."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    task = service.update_task(task_id, data)
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return task


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer une tâche."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    if not service.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Tâche non trouvée")


# ============================================================================
# JALONS
# ============================================================================

@router.post("/{project_id}/milestones", response_model=MilestoneResponse, status_code=201)
def create_milestone(
    project_id: UUID,
    data: MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un jalon."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return service.create_milestone(project_id, data)


@router.get("/{project_id}/milestones", response_model=list[MilestoneResponse])
def get_milestones(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les jalons d'un projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    return service.get_milestones(project_id)


@router.put("/milestones/{milestone_id}", response_model=MilestoneResponse)
def update_milestone(
    milestone_id: UUID,
    data: MilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un jalon."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    milestone = service.update_milestone(milestone_id, data)
    if not milestone:
        raise HTTPException(status_code=404, detail="Jalon non trouvé")
    return milestone


# ============================================================================
# ÉQUIPE
# ============================================================================

@router.post("/{project_id}/team", response_model=TeamMemberResponse, status_code=201)
def add_team_member(
    project_id: UUID,
    data: TeamMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ajouter un membre à l'équipe."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return service.add_team_member(project_id, data)


@router.get("/{project_id}/team", response_model=list[TeamMemberResponse])
def get_team_members(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer l'équipe d'un projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    return service.get_team_members(project_id)


@router.put("/team/{member_id}", response_model=TeamMemberResponse)
def update_team_member(
    member_id: UUID,
    data: TeamMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un membre."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    member = service.update_team_member(member_id, data)
    if not member:
        raise HTTPException(status_code=404, detail="Membre non trouvé")
    return member


@router.delete("/team/{member_id}", status_code=204)
def remove_team_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retirer un membre de l'équipe."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    if not service.remove_team_member(member_id):
        raise HTTPException(status_code=404, detail="Membre non trouvé")


# ============================================================================
# RISQUES
# ============================================================================

@router.post("/{project_id}/risks", response_model=RiskResponse, status_code=201)
def create_risk(
    project_id: UUID,
    data: RiskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un risque."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return service.create_risk(project_id, data)


@router.get("/{project_id}/risks", response_model=list[RiskResponse])
def get_risks(
    project_id: UUID,
    status: RiskStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les risques d'un projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    return service.get_risks(project_id, status)


@router.put("/risks/{risk_id}", response_model=RiskResponse)
def update_risk(
    risk_id: UUID,
    data: RiskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un risque."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    risk = service.update_risk(risk_id, data)
    if not risk:
        raise HTTPException(status_code=404, detail="Risque non trouvé")
    return risk


# ============================================================================
# ISSUES
# ============================================================================

@router.post("/{project_id}/issues", response_model=IssueResponse, status_code=201)
def create_issue(
    project_id: UUID,
    data: IssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une issue."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return service.create_issue(project_id, data)


@router.get("/{project_id}/issues", response_model=list[IssueResponse])
def get_issues(
    project_id: UUID,
    status: IssueStatus | None = None,
    priority: IssuePriority | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les issues d'un projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    return service.get_issues(project_id, status, priority)


@router.put("/issues/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_id: UUID,
    data: IssueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour une issue."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    issue = service.update_issue(issue_id, data)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue non trouvée")
    return issue


# ============================================================================
# TIME ENTRIES
# ============================================================================

@router.post("/{project_id}/time", response_model=TimeEntryResponse, status_code=201)
def create_time_entry(
    project_id: UUID,
    data: TimeEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une saisie de temps."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return service.create_time_entry(project_id, data)


@router.get("/{project_id}/time", response_model=TimeEntryList)
def get_time_entries(
    project_id: UUID,
    task_id: UUID | None = None,
    user_id: UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    status: TimeEntryStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les saisies de temps."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    entries, total, total_hours, billable_hours = service.get_time_entries(
        project_id, task_id, user_id, start_date, end_date, status, skip, limit
    )
    return {
        "items": entries,
        "total": total,
        "total_hours": total_hours,
        "billable_hours": billable_hours
    }


@router.post("/time/{entry_id}/submit", response_model=TimeEntryResponse)
def submit_time_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soumettre une saisie pour approbation."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    entry = service.submit_time_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Saisie non trouvée")
    return entry


@router.post("/time/{entry_id}/approve", response_model=TimeEntryResponse)
def approve_time_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approuver une saisie de temps."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    entry = service.approve_time_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Saisie non trouvée")
    return entry


@router.post("/time/{entry_id}/reject", response_model=TimeEntryResponse)
def reject_time_entry(
    entry_id: UUID,
    reason: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rejeter une saisie de temps."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    entry = service.reject_time_entry(entry_id, reason)
    if not entry:
        raise HTTPException(status_code=404, detail="Saisie non trouvée")
    return entry


# ============================================================================
# EXPENSES
# ============================================================================

@router.post("/{project_id}/expenses", response_model=ExpenseResponse, status_code=201)
def create_expense(
    project_id: UUID,
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une dépense."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return service.create_expense(project_id, data)


@router.get("/{project_id}/expenses", response_model=list[ExpenseResponse])
def get_expenses(
    project_id: UUID,
    status: ExpenseStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les dépenses d'un projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    return service.get_expenses(project_id, status)


@router.post("/expenses/{expense_id}/approve", response_model=ExpenseResponse)
def approve_expense(
    expense_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approuver une dépense."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    expense = service.approve_expense(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Dépense non trouvée")
    return expense


# ============================================================================
# DOCUMENTS
# ============================================================================

@router.post("/{project_id}/documents", response_model=DocumentResponse, status_code=201)
def create_document(
    project_id: UUID,
    data: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un document."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return service.create_document(project_id, data)


@router.get("/{project_id}/documents", response_model=list[DocumentResponse])
def get_documents(
    project_id: UUID,
    category: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les documents d'un projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    return service.get_documents(project_id, category)


# ============================================================================
# BUDGET
# ============================================================================

@router.post("/{project_id}/budgets", response_model=BudgetResponse, status_code=201)
def create_budget(
    project_id: UUID,
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un budget."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return service.create_budget(project_id, data)


@router.get("/{project_id}/budgets", response_model=list[BudgetResponse])
def get_budgets(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les budgets d'un projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    return service.get_budgets(project_id)


@router.post("/budgets/{budget_id}/approve", response_model=BudgetResponse)
def approve_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approuver un budget."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    budget = service.approve_budget(budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget non trouvé")
    return budget


# ============================================================================
# TEMPLATES
# ============================================================================

@router.post("/templates", response_model=TemplateResponse, status_code=201)
def create_template(
    data: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un template de projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    return service.create_template(data)


@router.get("/templates", response_model=list[TemplateResponse])
def get_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les templates."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    return service.get_templates()


@router.post("/from-template/{template_id}", response_model=ProjectResponse, status_code=201)
def create_project_from_template(
    template_id: UUID,
    code: str = Query(..., min_length=1),
    name: str = Query(..., min_length=1),
    start_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un projet depuis un template."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    try:
        return service.create_project_from_template(template_id, code, name, start_date)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# COMMENTS
# ============================================================================

@router.post("/{project_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(
    project_id: UUID,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un commentaire."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return service.create_comment(project_id, data)


@router.get("/{project_id}/comments", response_model=list[CommentResponse])
def get_comments(
    project_id: UUID,
    task_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les commentaires."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    return service.get_comments(project_id, task_id)


# ============================================================================
# KPIs
# ============================================================================

@router.post("/{project_id}/kpis/calculate")
def calculate_kpis(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculer les KPIs du projet."""
    service = get_projects_service(db, current_user.tenant_id, current_user.id)
    kpi = service.calculate_kpis(project_id)
    if not kpi:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return {"message": "KPIs calculés", "kpi_id": str(kpi.id)}
