"""
AZALS MODULE M9 - Service Projets
=================================

Logique métier pour la gestion de projets.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from .models import (
    BudgetLine,
    ExpenseStatus,
    IssuePriority,
    IssueStatus,
    MilestoneStatus,
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
    TimeEntryStatus,
)
from .schemas import (
    BudgetCreate,
    CommentCreate,
    DocumentCreate,
    ExpenseCreate,
    IssueCreate,
    IssueUpdate,
    MilestoneCreate,
    MilestoneUpdate,
    PhaseCreate,
    PhaseUpdate,
    ProjectCreate,
    ProjectStats,
    ProjectUpdate,
    RiskCreate,
    RiskUpdate,
    TaskCreate,
    TaskDependencyCreate,
    TaskUpdate,
    TeamMemberCreate,
    TeamMemberUpdate,
    TemplateCreate,
    TimeEntryCreate,
)


class ProjectsService:
    """Service de gestion des projets."""

    def __init__(self, db: Session, tenant_id: str, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    # ========================================================================
    # PROJETS
    # ========================================================================

    def create_project(self, data: ProjectCreate) -> Project:
        """Créer un projet."""
        # Auto-générer le code si non fourni
        from app.core.sequences import SequenceGenerator
        code = data.code
        if not code:
            seq = SequenceGenerator(self.db, self.tenant_id)
            code = seq.next_reference("PROJET")

        project = Project(
            tenant_id=self.tenant_id,
            code=code,
            name=data.name,
            description=data.description,
            category=data.category,
            tags=data.tags,
            priority=data.priority,
            planned_start_date=data.planned_start_date,
            planned_end_date=data.planned_end_date,
            project_manager_id=data.project_manager_id,
            sponsor_id=data.sponsor_id,
            customer_id=data.customer_id,
            budget_type=data.budget_type,
            planned_budget=data.planned_budget,
            currency=data.currency,
            planned_hours=data.planned_hours,
            is_billable=data.is_billable,
            billing_rate=data.billing_rate,
            parent_project_id=data.parent_project_id,
            template_id=data.template_id,
            settings=data.settings,
            created_by=self.user_id
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project(self, project_id: UUID) -> Project | None:
        """Récupérer un projet."""
        return self.db.query(Project).filter(
            and_(
                Project.id == project_id,
                Project.tenant_id == self.tenant_id
            )
        ).first()

    def list_projects(
        self,
        status: ProjectStatus | None = None,
        priority: ProjectPriority | None = None,
        project_manager_id: UUID | None = None,
        customer_id: UUID | None = None,
        category: str | None = None,
        is_active: bool = True,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Project], int]:
        """Lister les projets."""
        query = self.db.query(Project).filter(
            Project.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(Project.status == status)
        if priority:
            query = query.filter(Project.priority == priority)
        if project_manager_id:
            query = query.filter(Project.project_manager_id == project_manager_id)
        if customer_id:
            query = query.filter(Project.customer_id == customer_id)
        if category:
            query = query.filter(Project.category == category)
        if is_active is not None:
            query = query.filter(Project.is_active == is_active)
        if search:
            query = query.filter(
                or_(
                    Project.code.ilike(f"%{search}%"),
                    Project.name.ilike(f"%{search}%")
                )
            )

        total = query.count()
        projects = query.order_by(desc(Project.created_at)).offset(skip).limit(limit).all()
        return projects, total

    def update_project(self, project_id: UUID, data: ProjectUpdate) -> Project | None:
        """Mettre à jour un projet."""
        project = self.get_project(project_id)
        if not project:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)

        # Mise à jour automatique des dates selon le statut
        if data.status == ProjectStatus.IN_PROGRESS and not project.actual_start_date:
            project.actual_start_date = date.today()
        elif data.status == ProjectStatus.COMPLETED and not project.actual_end_date:
            project.actual_end_date = date.today()
            project.completed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project_id: UUID) -> bool:
        """Supprimer un projet (soft delete)."""
        project = self.get_project(project_id)
        if not project:
            return False
        project.is_active = False
        project.archived_at = datetime.utcnow()
        self.db.commit()
        return True

    def update_project_progress(self, project_id: UUID) -> Project:
        """Recalculer la progression du projet."""
        project = self.get_project(project_id)
        if not project:
            return None

        # Calculer depuis les tâches
        tasks = self.db.query(ProjectTask).filter(
            and_(
                ProjectTask.project_id == project_id,
                ProjectTask.tenant_id == self.tenant_id
            )
        ).all()

        if tasks:
            total_weight = sum(t.estimated_hours or 1 for t in tasks)
            completed_weight = sum(
                (t.estimated_hours or 1) * (t.progress_percent / 100)
                for t in tasks
            )
            project.progress_percent = (completed_weight / total_weight) * 100 if total_weight > 0 else 0

        # Calculer les heures actuelles
        project.actual_hours = sum(t.actual_hours or 0 for t in tasks)

        # Calculer les coûts
        expenses = self.db.query(func.sum(ProjectExpense.amount)).filter(
            and_(
                ProjectExpense.project_id == project_id,
                ProjectExpense.tenant_id == self.tenant_id,
                ProjectExpense.status == ExpenseStatus.APPROVED
            )
        ).scalar() or Decimal("0")

        time_cost = self.db.query(func.sum(ProjectTimeEntry.billing_amount)).filter(
            and_(
                ProjectTimeEntry.project_id == project_id,
                ProjectTimeEntry.tenant_id == self.tenant_id,
                ProjectTimeEntry.status == TimeEntryStatus.APPROVED
            )
        ).scalar() or Decimal("0")

        project.actual_cost = expenses + time_cost

        # Déterminer la santé du projet
        project.health_status = self._calculate_health_status(project)

        self.db.commit()
        self.db.refresh(project)
        return project

    def _calculate_health_status(self, project: Project) -> str:
        """Calculer le statut de santé du projet."""
        issues = []

        # Vérifier le budget
        if project.planned_budget and project.actual_cost > project.planned_budget:
            issues.append("over_budget")
        elif project.planned_budget and project.actual_cost > project.planned_budget * Decimal("0.9"):
            issues.append("budget_warning")

        # Vérifier les délais
        if project.planned_end_date and project.planned_end_date < date.today():
            if project.status not in [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]:
                issues.append("overdue")
        elif project.planned_end_date:
            days_remaining = (project.planned_end_date - date.today()).days
            if days_remaining < 7 and project.progress_percent < 80:
                issues.append("schedule_warning")

        if "over_budget" in issues or "overdue" in issues:
            return "red"
        elif issues:
            return "yellow"
        return "green"

    # ========================================================================
    # PHASES
    # ========================================================================

    def create_phase(self, project_id: UUID, data: PhaseCreate) -> ProjectPhase:
        """Créer une phase."""
        phase = ProjectPhase(
            tenant_id=self.tenant_id,
            project_id=project_id,
            name=data.name,
            description=data.description,
            order=data.order,
            color=data.color,
            planned_start_date=data.planned_start_date,
            planned_end_date=data.planned_end_date,
            planned_hours=data.planned_hours,
            planned_budget=data.planned_budget
        )
        self.db.add(phase)
        self.db.commit()
        self.db.refresh(phase)
        return phase

    def get_phases(self, project_id: UUID) -> list[ProjectPhase]:
        """Récupérer les phases d'un projet."""
        return self.db.query(ProjectPhase).filter(
            and_(
                ProjectPhase.project_id == project_id,
                ProjectPhase.tenant_id == self.tenant_id
            )
        ).order_by(ProjectPhase.order).all()

    def update_phase(self, phase_id: UUID, data: PhaseUpdate) -> ProjectPhase | None:
        """Mettre à jour une phase."""
        phase = self.db.query(ProjectPhase).filter(
            and_(
                ProjectPhase.id == phase_id,
                ProjectPhase.tenant_id == self.tenant_id
            )
        ).first()
        if not phase:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(phase, key, value)

        self.db.commit()
        self.db.refresh(phase)
        return phase

    def delete_phase(self, phase_id: UUID) -> bool:
        """Supprimer une phase."""
        phase = self.db.query(ProjectPhase).filter(
            and_(
                ProjectPhase.id == phase_id,
                ProjectPhase.tenant_id == self.tenant_id
            )
        ).first()
        if not phase:
            return False
        self.db.delete(phase)
        self.db.commit()
        return True

    # ========================================================================
    # TÂCHES
    # ========================================================================

    def create_task(self, project_id: UUID, data: TaskCreate) -> ProjectTask:
        """Créer une tâche."""
        task = ProjectTask(
            tenant_id=self.tenant_id,
            project_id=project_id,
            phase_id=data.phase_id,
            parent_task_id=data.parent_task_id,
            code=data.code,
            name=data.name,
            description=data.description,
            task_type=data.task_type,
            tags=data.tags,
            priority=data.priority,
            planned_start_date=data.planned_start_date,
            planned_end_date=data.planned_end_date,
            due_date=data.due_date,
            assignee_id=data.assignee_id,
            estimated_hours=data.estimated_hours,
            remaining_hours=data.estimated_hours,
            order=data.order,
            wbs_code=data.wbs_code,
            is_milestone=data.is_milestone,
            is_critical=data.is_critical,
            is_billable=data.is_billable,
            reporter_id=self.user_id,
            created_by=self.user_id
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        # Créer les dépendances
        for dep in data.dependencies:
            self._create_dependency(task.id, dep)

        return task

    def _create_dependency(self, successor_id: UUID, data: TaskDependencyCreate) -> TaskDependency:
        """Créer une dépendance entre tâches."""
        dep = TaskDependency(
            tenant_id=self.tenant_id,
            predecessor_id=data.predecessor_id,
            successor_id=successor_id,
            dependency_type=data.dependency_type,
            lag_days=data.lag_days
        )
        self.db.add(dep)
        self.db.commit()
        return dep

    def get_task(self, task_id: UUID) -> ProjectTask | None:
        """Récupérer une tâche."""
        return self.db.query(ProjectTask).filter(
            and_(
                ProjectTask.id == task_id,
                ProjectTask.tenant_id == self.tenant_id
            )
        ).first()

    def list_tasks(
        self,
        project_id: UUID | None = None,
        phase_id: UUID | None = None,
        assignee_id: UUID | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        is_overdue: bool = False,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[ProjectTask], int]:
        """Lister les tâches."""
        query = self.db.query(ProjectTask).filter(
            ProjectTask.tenant_id == self.tenant_id
        )

        if project_id:
            query = query.filter(ProjectTask.project_id == project_id)
        if phase_id:
            query = query.filter(ProjectTask.phase_id == phase_id)
        if assignee_id:
            query = query.filter(ProjectTask.assignee_id == assignee_id)
        if status:
            query = query.filter(ProjectTask.status == status)
        if priority:
            query = query.filter(ProjectTask.priority == priority)
        if is_overdue:
            query = query.filter(
                and_(
                    ProjectTask.due_date < date.today(),
                    ProjectTask.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED])
                )
            )
        if search:
            query = query.filter(
                or_(
                    ProjectTask.code.ilike(f"%{search}%"),
                    ProjectTask.name.ilike(f"%{search}%")
                )
            )

        total = query.count()
        tasks = query.order_by(ProjectTask.order).offset(skip).limit(limit).all()
        return tasks, total

    def update_task(self, task_id: UUID, data: TaskUpdate) -> ProjectTask | None:
        """Mettre à jour une tâche."""
        task = self.get_task(task_id)
        if not task:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)

        # Mise à jour automatique des dates selon le statut
        if data.status == TaskStatus.IN_PROGRESS and not task.actual_start_date:
            task.actual_start_date = date.today()
        elif data.status == TaskStatus.COMPLETED:
            task.actual_end_date = date.today()
            task.completed_at = datetime.utcnow()
            task.progress_percent = 100
            task.remaining_hours = 0

        self.db.commit()
        self.db.refresh(task)

        # Recalculer la progression du projet
        self.update_project_progress(task.project_id)

        return task

    def delete_task(self, task_id: UUID) -> bool:
        """Supprimer une tâche."""
        task = self.get_task(task_id)
        if not task:
            return False
        self.db.delete(task)
        self.db.commit()
        return True

    def get_my_tasks(
        self,
        status: TaskStatus | None = None,
        limit: int = 50
    ) -> list[ProjectTask]:
        """Récupérer mes tâches."""
        query = self.db.query(ProjectTask).filter(
            and_(
                ProjectTask.tenant_id == self.tenant_id,
                ProjectTask.assignee_id == self.user_id
            )
        )
        if status:
            query = query.filter(ProjectTask.status == status)
        else:
            query = query.filter(
                ProjectTask.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED])
            )
        return query.order_by(ProjectTask.due_date).limit(limit).all()

    # ========================================================================
    # JALONS
    # ========================================================================

    def create_milestone(self, project_id: UUID, data: MilestoneCreate) -> ProjectMilestone:
        """Créer un jalon."""
        milestone = ProjectMilestone(
            tenant_id=self.tenant_id,
            project_id=project_id,
            phase_id=data.phase_id,
            name=data.name,
            description=data.description,
            target_date=data.target_date,
            is_key_milestone=data.is_key_milestone,
            is_customer_visible=data.is_customer_visible,
            deliverables=data.deliverables,
            acceptance_criteria=data.acceptance_criteria,
            created_by=self.user_id
        )
        self.db.add(milestone)
        self.db.commit()
        self.db.refresh(milestone)
        return milestone

    def get_milestones(self, project_id: UUID) -> list[ProjectMilestone]:
        """Récupérer les jalons d'un projet."""
        return self.db.query(ProjectMilestone).filter(
            and_(
                ProjectMilestone.project_id == project_id,
                ProjectMilestone.tenant_id == self.tenant_id
            )
        ).order_by(ProjectMilestone.target_date).all()

    def update_milestone(self, milestone_id: UUID, data: MilestoneUpdate) -> ProjectMilestone | None:
        """Mettre à jour un jalon."""
        milestone = self.db.query(ProjectMilestone).filter(
            and_(
                ProjectMilestone.id == milestone_id,
                ProjectMilestone.tenant_id == self.tenant_id
            )
        ).first()
        if not milestone:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(milestone, key, value)

        # Si marqué comme atteint
        if data.status == MilestoneStatus.ACHIEVED:
            milestone.actual_date = date.today()
            milestone.validated_by = self.user_id
            milestone.validated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(milestone)
        return milestone

    # ========================================================================
    # ÉQUIPE
    # ========================================================================

    def add_team_member(self, project_id: UUID, data: TeamMemberCreate) -> ProjectTeamMember:
        """Ajouter un membre à l'équipe."""
        member = ProjectTeamMember(
            tenant_id=self.tenant_id,
            project_id=project_id,
            user_id=data.user_id,
            employee_id=data.employee_id,
            role=data.role,
            role_description=data.role_description,
            allocation_percent=data.allocation_percent,
            start_date=data.start_date,
            end_date=data.end_date,
            hourly_rate=data.hourly_rate,
            daily_rate=data.daily_rate,
            is_billable=data.is_billable,
            can_log_time=data.can_log_time,
            can_view_budget=data.can_view_budget,
            can_manage_tasks=data.can_manage_tasks,
            can_approve_time=data.can_approve_time
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def get_team_members(self, project_id: UUID) -> list[ProjectTeamMember]:
        """Récupérer l'équipe d'un projet."""
        return self.db.query(ProjectTeamMember).filter(
            and_(
                ProjectTeamMember.project_id == project_id,
                ProjectTeamMember.tenant_id == self.tenant_id,
                ProjectTeamMember.is_active
            )
        ).all()

    def update_team_member(self, member_id: UUID, data: TeamMemberUpdate) -> ProjectTeamMember | None:
        """Mettre à jour un membre."""
        member = self.db.query(ProjectTeamMember).filter(
            and_(
                ProjectTeamMember.id == member_id,
                ProjectTeamMember.tenant_id == self.tenant_id
            )
        ).first()
        if not member:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(member, key, value)

        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_team_member(self, member_id: UUID) -> bool:
        """Retirer un membre de l'équipe."""
        member = self.db.query(ProjectTeamMember).filter(
            and_(
                ProjectTeamMember.id == member_id,
                ProjectTeamMember.tenant_id == self.tenant_id
            )
        ).first()
        if not member:
            return False
        member.is_active = False
        member.end_date = date.today()
        self.db.commit()
        return True

    # ========================================================================
    # RISQUES
    # ========================================================================

    def create_risk(self, project_id: UUID, data: RiskCreate) -> ProjectRisk:
        """Créer un risque."""
        # Calculer le score de risque
        probability_scores = {
            RiskProbability.RARE: 1,
            RiskProbability.UNLIKELY: 2,
            RiskProbability.POSSIBLE: 3,
            RiskProbability.LIKELY: 4,
            RiskProbability.ALMOST_CERTAIN: 5
        }
        impact_scores = {
            RiskImpact.NEGLIGIBLE: 1,
            RiskImpact.MINOR: 2,
            RiskImpact.MODERATE: 3,
            RiskImpact.MAJOR: 4,
            RiskImpact.CRITICAL: 5
        }
        risk_score = probability_scores[data.probability] * impact_scores[data.impact]

        risk = ProjectRisk(
            tenant_id=self.tenant_id,
            project_id=project_id,
            code=data.code,
            title=data.title,
            description=data.description,
            category=data.category,
            probability=data.probability,
            impact=data.impact,
            risk_score=risk_score,
            owner_id=data.owner_id,
            response_strategy=data.response_strategy,
            mitigation_plan=data.mitigation_plan,
            contingency_plan=data.contingency_plan,
            triggers=data.triggers,
            estimated_impact_min=data.estimated_impact_min,
            estimated_impact_max=data.estimated_impact_max,
            review_date=data.review_date,
            created_by=self.user_id
        )
        self.db.add(risk)
        self.db.commit()
        self.db.refresh(risk)
        return risk

    def get_risks(
        self,
        project_id: UUID,
        status: RiskStatus | None = None
    ) -> list[ProjectRisk]:
        """Récupérer les risques d'un projet."""
        query = self.db.query(ProjectRisk).filter(
            and_(
                ProjectRisk.project_id == project_id,
                ProjectRisk.tenant_id == self.tenant_id
            )
        )
        if status:
            query = query.filter(ProjectRisk.status == status)
        return query.order_by(desc(ProjectRisk.risk_score)).all()

    def update_risk(self, risk_id: UUID, data: RiskUpdate) -> ProjectRisk | None:
        """Mettre à jour un risque."""
        risk = self.db.query(ProjectRisk).filter(
            and_(
                ProjectRisk.id == risk_id,
                ProjectRisk.tenant_id == self.tenant_id
            )
        ).first()
        if not risk:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Recalculer le score si probabilité ou impact changé
        if 'probability' in update_data or 'impact' in update_data:
            probability_scores = {
                RiskProbability.RARE: 1,
                RiskProbability.UNLIKELY: 2,
                RiskProbability.POSSIBLE: 3,
                RiskProbability.LIKELY: 4,
                RiskProbability.ALMOST_CERTAIN: 5
            }
            impact_scores = {
                RiskImpact.NEGLIGIBLE: 1,
                RiskImpact.MINOR: 2,
                RiskImpact.MODERATE: 3,
                RiskImpact.MAJOR: 4,
                RiskImpact.CRITICAL: 5
            }
            prob = update_data.get('probability', risk.probability)
            imp = update_data.get('impact', risk.impact)
            update_data['risk_score'] = probability_scores[prob] * impact_scores[imp]

        for key, value in update_data.items():
            setattr(risk, key, value)

        # Dates automatiques selon statut
        if data.status == RiskStatus.OCCURRED:
            risk.occurred_date = date.today()
        elif data.status == RiskStatus.CLOSED:
            risk.closed_date = date.today()

        self.db.commit()
        self.db.refresh(risk)
        return risk

    # ========================================================================
    # ISSUES
    # ========================================================================

    def create_issue(self, project_id: UUID, data: IssueCreate) -> ProjectIssue:
        """Créer une issue."""
        issue = ProjectIssue(
            tenant_id=self.tenant_id,
            project_id=project_id,
            task_id=data.task_id,
            code=data.code,
            title=data.title,
            description=data.description,
            category=data.category,
            priority=data.priority,
            assignee_id=data.assignee_id,
            due_date=data.due_date,
            impact_description=data.impact_description,
            affected_areas=data.affected_areas,
            related_risk_id=data.related_risk_id,
            reporter_id=self.user_id,
            created_by=self.user_id
        )
        self.db.add(issue)
        self.db.commit()
        self.db.refresh(issue)
        return issue

    def get_issues(
        self,
        project_id: UUID,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None
    ) -> list[ProjectIssue]:
        """Récupérer les issues d'un projet."""
        query = self.db.query(ProjectIssue).filter(
            and_(
                ProjectIssue.project_id == project_id,
                ProjectIssue.tenant_id == self.tenant_id
            )
        )
        if status:
            query = query.filter(ProjectIssue.status == status)
        if priority:
            query = query.filter(ProjectIssue.priority == priority)
        return query.order_by(desc(ProjectIssue.created_at)).all()

    def update_issue(self, issue_id: UUID, data: IssueUpdate) -> ProjectIssue | None:
        """Mettre à jour une issue."""
        issue = self.db.query(ProjectIssue).filter(
            and_(
                ProjectIssue.id == issue_id,
                ProjectIssue.tenant_id == self.tenant_id
            )
        ).first()
        if not issue:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(issue, key, value)

        # Dates automatiques selon statut
        if data.status == IssueStatus.RESOLVED:
            issue.resolved_date = date.today()
        elif data.status == IssueStatus.CLOSED:
            issue.closed_date = date.today()

        self.db.commit()
        self.db.refresh(issue)
        return issue

    # ========================================================================
    # TIME ENTRIES
    # ========================================================================

    def create_time_entry(self, project_id: UUID, data: TimeEntryCreate) -> ProjectTimeEntry:
        """Créer une saisie de temps."""
        # Récupérer le taux de facturation
        billing_rate = None
        billing_amount = None
        if data.is_billable:
            project = self.get_project(project_id)
            if project and project.billing_rate:
                billing_rate = project.billing_rate
                billing_amount = billing_rate * Decimal(str(data.hours))

        entry = ProjectTimeEntry(
            tenant_id=self.tenant_id,
            project_id=project_id,
            task_id=data.task_id,
            user_id=self.user_id,
            date=data.entry_date,
            hours=data.hours,
            start_time=data.start_time,
            end_time=data.end_time,
            description=data.description,
            activity_type=data.activity_type,
            is_billable=data.is_billable,
            billing_rate=billing_rate,
            billing_amount=billing_amount,
            is_overtime=data.is_overtime
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)

        # Mettre à jour les heures de la tâche
        if data.task_id:
            self._update_task_hours(data.task_id)

        return entry

    def _update_task_hours(self, task_id: UUID):
        """Mettre à jour les heures d'une tâche."""
        task = self.get_task(task_id)
        if task:
            total_hours = self.db.query(func.sum(ProjectTimeEntry.hours)).filter(
                and_(
                    ProjectTimeEntry.task_id == task_id,
                    ProjectTimeEntry.tenant_id == self.tenant_id
                )
            ).scalar() or 0
            task.actual_hours = float(total_hours)
            task.remaining_hours = max(0, (task.estimated_hours or 0) - task.actual_hours)
            self.db.commit()

    def get_time_entries(
        self,
        project_id: UUID | None = None,
        task_id: UUID | None = None,
        user_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        status: TimeEntryStatus | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[ProjectTimeEntry], int, float, float]:
        """Récupérer les saisies de temps."""
        query = self.db.query(ProjectTimeEntry).filter(
            ProjectTimeEntry.tenant_id == self.tenant_id
        )

        if project_id:
            query = query.filter(ProjectTimeEntry.project_id == project_id)
        if task_id:
            query = query.filter(ProjectTimeEntry.task_id == task_id)
        if user_id:
            query = query.filter(ProjectTimeEntry.user_id == user_id)
        if start_date:
            query = query.filter(ProjectTimeEntry.date >= start_date)
        if end_date:
            query = query.filter(ProjectTimeEntry.date <= end_date)
        if status:
            query = query.filter(ProjectTimeEntry.status == status)

        total = query.count()
        total_hours = query.with_entities(func.sum(ProjectTimeEntry.hours)).scalar() or 0
        billable_hours = query.filter(
            ProjectTimeEntry.is_billable
        ).with_entities(func.sum(ProjectTimeEntry.hours)).scalar() or 0

        entries = query.order_by(desc(ProjectTimeEntry.date)).offset(skip).limit(limit).all()
        return entries, total, float(total_hours), float(billable_hours)

    def submit_time_entry(self, entry_id: UUID) -> ProjectTimeEntry | None:
        """Soumettre une saisie pour approbation."""
        entry = self.db.query(ProjectTimeEntry).filter(
            and_(
                ProjectTimeEntry.id == entry_id,
                ProjectTimeEntry.tenant_id == self.tenant_id,
                ProjectTimeEntry.user_id == self.user_id
            )
        ).first()
        if not entry:
            return None
        entry.status = TimeEntryStatus.SUBMITTED
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def approve_time_entry(self, entry_id: UUID) -> ProjectTimeEntry | None:
        """Approuver une saisie de temps."""
        entry = self.db.query(ProjectTimeEntry).filter(
            and_(
                ProjectTimeEntry.id == entry_id,
                ProjectTimeEntry.tenant_id == self.tenant_id
            )
        ).first()
        if not entry:
            return None
        entry.status = TimeEntryStatus.APPROVED
        entry.approved_by = self.user_id
        entry.approved_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def reject_time_entry(self, entry_id: UUID, reason: str) -> ProjectTimeEntry | None:
        """Rejeter une saisie de temps."""
        entry = self.db.query(ProjectTimeEntry).filter(
            and_(
                ProjectTimeEntry.id == entry_id,
                ProjectTimeEntry.tenant_id == self.tenant_id
            )
        ).first()
        if not entry:
            return None
        entry.status = TimeEntryStatus.REJECTED
        entry.rejection_reason = reason
        self.db.commit()
        self.db.refresh(entry)
        return entry

    # ========================================================================
    # EXPENSES
    # ========================================================================

    def create_expense(self, project_id: UUID, data: ExpenseCreate) -> ProjectExpense:
        """Créer une dépense."""
        expense = ProjectExpense(
            tenant_id=self.tenant_id,
            project_id=project_id,
            task_id=data.task_id,
            budget_line_id=data.budget_line_id,
            reference=data.reference,
            description=data.description,
            category=data.category,
            amount=data.amount,
            currency=data.currency,
            quantity=data.quantity,
            unit_price=data.unit_price,
            expense_date=data.expense_date,
            vendor=data.vendor,
            is_billable=data.is_billable,
            receipt_url=data.receipt_url,
            attachments=data.attachments,
            submitted_by=self.user_id
        )
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def get_expenses(
        self,
        project_id: UUID,
        status: ExpenseStatus | None = None
    ) -> list[ProjectExpense]:
        """Récupérer les dépenses d'un projet."""
        query = self.db.query(ProjectExpense).filter(
            and_(
                ProjectExpense.project_id == project_id,
                ProjectExpense.tenant_id == self.tenant_id
            )
        )
        if status:
            query = query.filter(ProjectExpense.status == status)
        return query.order_by(desc(ProjectExpense.expense_date)).all()

    def approve_expense(self, expense_id: UUID) -> ProjectExpense | None:
        """Approuver une dépense."""
        expense = self.db.query(ProjectExpense).filter(
            and_(
                ProjectExpense.id == expense_id,
                ProjectExpense.tenant_id == self.tenant_id
            )
        ).first()
        if not expense:
            return None
        expense.status = ExpenseStatus.APPROVED
        expense.approved_by = self.user_id
        expense.approved_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(expense)

        # Mettre à jour le projet
        self.update_project_progress(expense.project_id)
        return expense

    # ========================================================================
    # DOCUMENTS
    # ========================================================================

    def create_document(self, project_id: UUID, data: DocumentCreate) -> ProjectDocument:
        """Créer un document."""
        doc = ProjectDocument(
            tenant_id=self.tenant_id,
            project_id=project_id,
            name=data.name,
            description=data.description,
            category=data.category,
            file_name=data.file_name,
            file_url=data.file_url,
            file_size=data.file_size,
            file_type=data.file_type,
            version=data.version,
            is_public=data.is_public,
            access_level=data.access_level,
            tags=data.tags,
            uploaded_by=self.user_id
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_documents(self, project_id: UUID, category: str | None = None) -> list[ProjectDocument]:
        """Récupérer les documents d'un projet."""
        query = self.db.query(ProjectDocument).filter(
            and_(
                ProjectDocument.project_id == project_id,
                ProjectDocument.tenant_id == self.tenant_id,
                ProjectDocument.is_latest
            )
        )
        if category:
            query = query.filter(ProjectDocument.category == category)
        return query.order_by(desc(ProjectDocument.created_at)).all()

    # ========================================================================
    # BUDGET
    # ========================================================================

    def create_budget(self, project_id: UUID, data: BudgetCreate) -> ProjectBudget:
        """Créer un budget."""
        budget = ProjectBudget(
            tenant_id=self.tenant_id,
            project_id=project_id,
            name=data.name,
            description=data.description,
            fiscal_year=data.fiscal_year,
            budget_type=data.budget_type,
            total_budget=data.total_budget,
            currency=data.currency,
            start_date=data.start_date,
            end_date=data.end_date,
            created_by=self.user_id
        )
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)

        # Créer les lignes de budget
        for line_data in data.lines:
            line = BudgetLine(
                tenant_id=self.tenant_id,
                budget_id=budget.id,
                phase_id=line_data.phase_id,
                code=line_data.code,
                name=line_data.name,
                description=line_data.description,
                category=line_data.category,
                budget_amount=line_data.budget_amount,
                quantity=line_data.quantity,
                unit=line_data.unit,
                unit_price=line_data.unit_price,
                order=line_data.order,
                parent_line_id=line_data.parent_line_id,
                account_code=line_data.account_code
            )
            self.db.add(line)

        self.db.commit()
        self.db.refresh(budget)
        return budget

    def get_budgets(self, project_id: UUID) -> list[ProjectBudget]:
        """Récupérer les budgets d'un projet."""
        return self.db.query(ProjectBudget).filter(
            and_(
                ProjectBudget.project_id == project_id,
                ProjectBudget.tenant_id == self.tenant_id,
                ProjectBudget.is_active
            )
        ).all()

    def approve_budget(self, budget_id: UUID) -> ProjectBudget | None:
        """Approuver un budget."""
        budget = self.db.query(ProjectBudget).filter(
            and_(
                ProjectBudget.id == budget_id,
                ProjectBudget.tenant_id == self.tenant_id
            )
        ).first()
        if not budget:
            return None
        budget.is_approved = True
        budget.approved_by = self.user_id
        budget.approved_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(budget)
        return budget

    # ========================================================================
    # TEMPLATES
    # ========================================================================

    def create_template(self, data: TemplateCreate) -> ProjectTemplate:
        """Créer un template de projet."""
        template = ProjectTemplate(
            tenant_id=self.tenant_id,
            name=data.name,
            description=data.description,
            category=data.category,
            default_priority=data.default_priority,
            default_budget_type=data.default_budget_type,
            estimated_duration_days=data.estimated_duration_days,
            phases_template=data.phases_template,
            tasks_template=data.tasks_template,
            milestones_template=data.milestones_template,
            risks_template=data.risks_template,
            roles_template=data.roles_template,
            budget_template=data.budget_template,
            checklist=data.checklist,
            settings=data.settings,
            is_public=data.is_public,
            created_by=self.user_id
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_templates(self) -> list[ProjectTemplate]:
        """Récupérer les templates."""
        return self.db.query(ProjectTemplate).filter(
            and_(
                or_(
                    ProjectTemplate.tenant_id == self.tenant_id,
                    ProjectTemplate.is_public
                ),
                ProjectTemplate.is_active
            )
        ).all()

    def create_project_from_template(
        self,
        template_id: UUID,
        code: str,
        name: str,
        start_date: date | None = None
    ) -> Project:
        """Créer un projet depuis un template."""
        # SÉCURITÉ: Filtrer par tenant_id
        template = self.db.query(ProjectTemplate).filter(
            ProjectTemplate.tenant_id == self.tenant_id,
            ProjectTemplate.id == template_id
        ).first()
        if not template:
            raise ValueError("Template not found")

        # Créer le projet
        project = Project(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            priority=template.default_priority,
            budget_type=template.default_budget_type,
            template_id=template_id,
            planned_start_date=start_date or date.today(),
            settings=template.settings,
            created_by=self.user_id
        )

        if template.estimated_duration_days and start_date:
            project.planned_end_date = start_date + timedelta(days=template.estimated_duration_days)

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        # Créer les phases
        phase_mapping = {}
        for phase_data in template.phases_template:
            phase = ProjectPhase(
                tenant_id=self.tenant_id,
                project_id=project.id,
                name=phase_data.get('name'),
                description=phase_data.get('description'),
                order=phase_data.get('order', 0),
                color=phase_data.get('color')
            )
            self.db.add(phase)
            self.db.commit()
            self.db.refresh(phase)
            phase_mapping[phase_data.get('name')] = phase.id

        # Créer les tâches
        for task_data in template.tasks_template:
            task = ProjectTask(
                tenant_id=self.tenant_id,
                project_id=project.id,
                phase_id=phase_mapping.get(task_data.get('phase')),
                name=task_data.get('name'),
                description=task_data.get('description'),
                estimated_hours=task_data.get('estimated_hours', 0),
                order=task_data.get('order', 0),
                created_by=self.user_id
            )
            self.db.add(task)

        # Créer les jalons
        for ms_data in template.milestones_template:
            ms = ProjectMilestone(
                tenant_id=self.tenant_id,
                project_id=project.id,
                name=ms_data.get('name'),
                description=ms_data.get('description'),
                target_date=date.today() + timedelta(days=ms_data.get('offset_days', 0)),
                is_key_milestone=ms_data.get('is_key', False),
                created_by=self.user_id
            )
            self.db.add(ms)

        # Créer les risques types
        for risk_data in template.risks_template:
            risk = ProjectRisk(
                tenant_id=self.tenant_id,
                project_id=project.id,
                title=risk_data.get('title'),
                description=risk_data.get('description'),
                category=risk_data.get('category'),
                probability=RiskProbability(risk_data.get('probability', 'possible')),
                impact=RiskImpact(risk_data.get('impact', 'moderate')),
                response_strategy=risk_data.get('response_strategy'),
                mitigation_plan=risk_data.get('mitigation_plan'),
                created_by=self.user_id
            )
            self.db.add(risk)

        self.db.commit()
        self.db.refresh(project)
        return project

    # ========================================================================
    # COMMENTS
    # ========================================================================

    def create_comment(self, project_id: UUID, data: CommentCreate) -> ProjectComment:
        """Créer un commentaire."""
        comment = ProjectComment(
            tenant_id=self.tenant_id,
            project_id=project_id,
            task_id=data.task_id,
            content=data.content,
            comment_type=data.comment_type,
            parent_comment_id=data.parent_comment_id,
            mentions=data.mentions,
            attachments=data.attachments,
            is_internal=data.is_internal,
            author_id=self.user_id
        )
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def get_comments(
        self,
        project_id: UUID,
        task_id: UUID | None = None
    ) -> list[ProjectComment]:
        """Récupérer les commentaires."""
        query = self.db.query(ProjectComment).filter(
            and_(
                ProjectComment.project_id == project_id,
                ProjectComment.tenant_id == self.tenant_id
            )
        )
        if task_id:
            query = query.filter(ProjectComment.task_id == task_id)
        return query.order_by(ProjectComment.created_at).all()

    # ========================================================================
    # KPIs ET DASHBOARD
    # ========================================================================

    def calculate_kpis(self, project_id: UUID) -> ProjectKPI:
        """Calculer et enregistrer les KPIs du projet."""
        project = self.get_project(project_id)
        if not project:
            return None

        today = date.today()

        # Récupérer les données
        tasks = self.db.query(ProjectTask).filter(
            and_(
                ProjectTask.project_id == project_id,
                ProjectTask.tenant_id == self.tenant_id
            )
        ).all()

        risks = self.get_risks(project_id)
        issues = self.get_issues(project_id)

        # Calculer les métriques
        kpi = ProjectKPI(
            tenant_id=self.tenant_id,
            project_id=project_id,
            kpi_date=today,
            # Tasks
            tasks_total=len(tasks),
            tasks_completed=len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            tasks_in_progress=len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS]),
            tasks_blocked=len([t for t in tasks if t.status == TaskStatus.BLOCKED]),
            # Effort
            hours_planned=sum(t.estimated_hours or 0 for t in tasks),
            hours_actual=sum(t.actual_hours or 0 for t in tasks),
            hours_remaining=sum(t.remaining_hours or 0 for t in tasks),
            # Risks
            risks_total=len(risks),
            risks_open=len([r for r in risks if r.status not in [RiskStatus.CLOSED]]),
            risks_high=len([r for r in risks if r.risk_score and r.risk_score >= 15]),
            # Issues
            issues_total=len(issues),
            issues_open=len([i for i in issues if i.status not in [IssueStatus.CLOSED, IssueStatus.RESOLVED]]),
            issues_critical=len([i for i in issues if i.priority == IssuePriority.CRITICAL]),
            # EVM (Earned Value Management)
            planned_value=project.planned_budget,
            actual_cost=project.actual_cost,
            calculated_by=self.user_id
        )

        # Calculer la valeur acquise (EV) basée sur la progression
        if project.planned_budget:
            kpi.earned_value = project.planned_budget * Decimal(str(project.progress_percent / 100))
            # Variances
            kpi.schedule_variance = kpi.earned_value - kpi.planned_value
            kpi.cost_variance = kpi.earned_value - kpi.actual_cost
            # Indices
            if kpi.planned_value and kpi.planned_value > 0:
                kpi.schedule_performance_index = float(kpi.earned_value / kpi.planned_value)
            if kpi.actual_cost and kpi.actual_cost > 0:
                kpi.cost_performance_index = float(kpi.earned_value / kpi.actual_cost)

        self.db.add(kpi)
        self.db.commit()
        self.db.refresh(kpi)
        return kpi

    def get_project_stats(self, project_id: UUID) -> ProjectStats:
        """Obtenir les statistiques d'un projet."""
        project = self.get_project(project_id)
        if not project:
            return None

        tasks = self.db.query(ProjectTask).filter(
            and_(
                ProjectTask.project_id == project_id,
                ProjectTask.tenant_id == self.tenant_id
            )
        ).all()

        milestones = self.get_milestones(project_id)
        risks = self.get_risks(project_id)
        issues = self.get_issues(project_id)
        team = self.get_team_members(project_id)

        today = date.today()

        return ProjectStats(
            tasks_total=len(tasks),
            tasks_completed=len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            tasks_in_progress=len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS]),
            tasks_blocked=len([t for t in tasks if t.status == TaskStatus.BLOCKED]),
            tasks_overdue=len([t for t in tasks if t.due_date and t.due_date < today and t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]]),
            milestones_total=len(milestones),
            milestones_achieved=len([m for m in milestones if m.status == MilestoneStatus.ACHIEVED]),
            milestones_overdue=len([m for m in milestones if m.target_date < today and m.status == MilestoneStatus.PENDING]),
            risks_total=len(risks),
            risks_open=len([r for r in risks if r.status != RiskStatus.CLOSED]),
            risks_high=len([r for r in risks if r.risk_score and r.risk_score >= 15]),
            issues_total=len(issues),
            issues_open=len([i for i in issues if i.status not in [IssueStatus.CLOSED, IssueStatus.RESOLVED]]),
            issues_critical=len([i for i in issues if i.priority == IssuePriority.CRITICAL]),
            team_size=len(team),
            hours_planned=sum(t.estimated_hours or 0 for t in tasks),
            hours_actual=sum(t.actual_hours or 0 for t in tasks),
            hours_remaining=sum(t.remaining_hours or 0 for t in tasks),
            budget_planned=project.planned_budget or Decimal("0"),
            budget_actual=project.actual_cost or Decimal("0"),
            budget_remaining=(project.planned_budget or Decimal("0")) - (project.actual_cost or Decimal("0"))
        )

    def get_dashboard(self, project_id: UUID) -> dict[str, Any]:
        """Obtenir le dashboard complet d'un projet."""
        project = self.get_project(project_id)
        if not project:
            return None

        stats = self.get_project_stats(project_id)

        # Tâches récentes
        recent_tasks, _, _, _ = self.list_tasks(
            project_id=project_id,
            status=TaskStatus.IN_PROGRESS,
            limit=5
        )

        # Jalons à venir
        upcoming_milestones = self.db.query(ProjectMilestone).filter(
            and_(
                ProjectMilestone.project_id == project_id,
                ProjectMilestone.tenant_id == self.tenant_id,
                ProjectMilestone.status == MilestoneStatus.PENDING,
                ProjectMilestone.target_date >= date.today()
            )
        ).order_by(ProjectMilestone.target_date).limit(5).all()

        # Risques élevés
        high_risks = self.db.query(ProjectRisk).filter(
            and_(
                ProjectRisk.project_id == project_id,
                ProjectRisk.tenant_id == self.tenant_id,
                ProjectRisk.status != RiskStatus.CLOSED,
                ProjectRisk.risk_score >= 12
            )
        ).order_by(desc(ProjectRisk.risk_score)).limit(5).all()

        # Issues ouvertes
        open_issues = self.db.query(ProjectIssue).filter(
            and_(
                ProjectIssue.project_id == project_id,
                ProjectIssue.tenant_id == self.tenant_id,
                ProjectIssue.status.in_([IssueStatus.OPEN, IssueStatus.IN_PROGRESS])
            )
        ).order_by(desc(ProjectIssue.priority)).limit(5).all()

        return {
            "project": project,
            "stats": stats,
            "recent_tasks": recent_tasks,
            "upcoming_milestones": upcoming_milestones,
            "high_risks": high_risks,
            "open_issues": open_issues,
            "health_indicators": {
                "schedule": project.health_status,
                "budget": "green" if project.actual_cost <= (project.planned_budget or Decimal("999999999")) else "red",
                "scope": "green" if stats.tasks_blocked == 0 else "yellow",
                "risks": "red" if stats.risks_high > 2 else ("yellow" if stats.risks_high > 0 else "green")
            }
        }


def get_projects_service(db: Session, tenant_id: str, user_id: UUID) -> ProjectsService:
    """Factory pour le service projets."""
    return ProjectsService(db, tenant_id, user_id)
