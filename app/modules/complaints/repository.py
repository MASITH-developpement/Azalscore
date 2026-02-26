"""
AZALS MODULE - Complaints Repository
=====================================

Repository pour l'acces aux donnees des reclamations avec isolation tenant.
Utilise le pattern BaseRepository d'AZALSCORE.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.repository import BaseRepository

from .models import (
    Complaint,
    ComplaintAction,
    ComplaintAgent,
    ComplaintAttachment,
    ComplaintAutomationRule,
    ComplaintCategoryConfig,
    ComplaintEscalation,
    ComplaintExchange,
    ComplaintHistory,
    ComplaintMetrics,
    ComplaintPriority,
    ComplaintSLAPolicy,
    ComplaintStatus,
    ComplaintTeam,
    ComplaintTemplate,
    ComplaintCategory,
    ComplaintChannel,
)

logger = logging.getLogger(__name__)


# ============================================================================
# COMPLAINT REPOSITORY
# ============================================================================

class ComplaintRepository(BaseRepository[Complaint]):
    """Repository pour les reclamations."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, Complaint, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(Complaint).filter(
            Complaint.tenant_id == self.tenant_id,
            Complaint.is_deleted == False  # noqa: E712
        )

    def get_by_reference(self, reference: str) -> Complaint | None:
        """Recupere une reclamation par reference."""
        return self._base_query().filter(
            Complaint.reference == reference
        ).first()

    def get_with_details(self, id: UUID) -> Complaint | None:
        """Recupere une reclamation avec toutes ses relations."""
        return self._base_query().options(
            joinedload(Complaint.category_config),
            joinedload(Complaint.team),
            joinedload(Complaint.assigned_agent),
            joinedload(Complaint.exchanges),
            joinedload(Complaint.attachments),
            joinedload(Complaint.actions),
            joinedload(Complaint.escalations),
        ).filter(Complaint.id == id).first()

    def search(
        self,
        query: str | None = None,
        status: list[ComplaintStatus] | None = None,
        priority: list[ComplaintPriority] | None = None,
        category: list[ComplaintCategory] | None = None,
        channel: list[ComplaintChannel] | None = None,
        team_id: UUID | None = None,
        assigned_to_id: UUID | None = None,
        customer_id: UUID | None = None,
        customer_email: str | None = None,
        order_id: UUID | None = None,
        sla_breached: bool | None = None,
        sla_at_risk: bool | None = None,
        escalated: bool | None = None,
        has_compensation: bool | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        tags: list[str] | None = None,
        skip: int = 0,
        limit: int = 50,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> tuple[list[Complaint], int]:
        """Recherche avancee de reclamations."""
        q = self._base_query()

        # Recherche textuelle
        if query:
            search_term = f"%{query}%"
            q = q.filter(
                or_(
                    Complaint.reference.ilike(search_term),
                    Complaint.subject.ilike(search_term),
                    Complaint.description.ilike(search_term),
                    Complaint.customer_name.ilike(search_term),
                    Complaint.customer_email.ilike(search_term),
                    Complaint.order_reference.ilike(search_term),
                )
            )

        # Filtres
        if status:
            q = q.filter(Complaint.status.in_(status))
        if priority:
            q = q.filter(Complaint.priority.in_(priority))
        if category:
            q = q.filter(Complaint.category.in_(category))
        if channel:
            q = q.filter(Complaint.channel.in_(channel))
        if team_id:
            q = q.filter(Complaint.team_id == team_id)
        if assigned_to_id:
            q = q.filter(Complaint.assigned_to_id == assigned_to_id)
        if customer_id:
            q = q.filter(Complaint.customer_id == customer_id)
        if customer_email:
            q = q.filter(Complaint.customer_email == customer_email)
        if order_id:
            q = q.filter(Complaint.order_id == order_id)
        if sla_breached is not None:
            q = q.filter(Complaint.resolution_breached == sla_breached)
        if sla_at_risk:
            now = datetime.utcnow()
            risk_threshold = now + timedelta(hours=4)
            q = q.filter(
                and_(
                    Complaint.resolution_due <= risk_threshold,
                    Complaint.resolution_breached == False,  # noqa: E712
                    Complaint.status.not_in([
                        ComplaintStatus.RESOLVED,
                        ComplaintStatus.CLOSED,
                        ComplaintStatus.CANCELLED
                    ])
                )
            )
        if escalated:
            q = q.filter(Complaint.escalation_count > 0)
        if has_compensation is not None:
            if has_compensation:
                q = q.filter(Complaint.compensation_amount > 0)
            else:
                q = q.filter(
                    or_(
                        Complaint.compensation_amount.is_(None),
                        Complaint.compensation_amount == 0
                    )
                )
        if date_from:
            q = q.filter(Complaint.created_at >= date_from)
        if date_to:
            q = q.filter(Complaint.created_at <= date_to)
        if tags:
            # Recherche dans le champ JSON tags
            for tag in tags:
                q = q.filter(Complaint.tags.contains([tag]))

        # Comptage total
        total = q.count()

        # Tri
        order_column = getattr(Complaint, order_by, Complaint.created_at)
        if order_desc:
            q = q.order_by(order_column.desc())
        else:
            q = q.order_by(order_column.asc())

        # Pagination
        items = q.offset(skip).limit(limit).all()

        return items, total

    def get_by_customer(
        self,
        customer_id: UUID | None = None,
        customer_email: str | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Complaint], int]:
        """Recupere les reclamations d'un client."""
        q = self._base_query()

        if customer_id:
            q = q.filter(Complaint.customer_id == customer_id)
        elif customer_email:
            q = q.filter(Complaint.customer_email == customer_email)
        else:
            return [], 0

        total = q.count()
        items = q.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()

        return items, total

    def get_pending_sla_breach(self, hours_before: int = 4) -> list[Complaint]:
        """Recupere les reclamations proches du depassement SLA."""
        threshold = datetime.utcnow() + timedelta(hours=hours_before)

        return self._base_query().filter(
            Complaint.resolution_due <= threshold,
            Complaint.resolution_breached == False,  # noqa: E712
            Complaint.status.not_in([
                ComplaintStatus.RESOLVED,
                ComplaintStatus.CLOSED,
                ComplaintStatus.CANCELLED
            ])
        ).all()

    def get_unassigned(self, team_id: UUID | None = None) -> list[Complaint]:
        """Recupere les reclamations non assignees."""
        q = self._base_query().filter(
            Complaint.assigned_to_id.is_(None),
            Complaint.status.in_([ComplaintStatus.NEW, ComplaintStatus.ACKNOWLEDGED])
        )

        if team_id:
            q = q.filter(Complaint.team_id == team_id)

        return q.order_by(Complaint.priority.desc(), Complaint.created_at.asc()).all()

    def get_stats(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        team_id: UUID | None = None,
        agent_id: UUID | None = None
    ) -> dict[str, Any]:
        """Calcule les statistiques des reclamations."""
        q = self._base_query()

        if date_from:
            q = q.filter(Complaint.created_at >= date_from)
        if date_to:
            q = q.filter(Complaint.created_at <= date_to)
        if team_id:
            q = q.filter(Complaint.team_id == team_id)
        if agent_id:
            q = q.filter(Complaint.assigned_to_id == agent_id)

        total = q.count()

        # Par statut
        status_counts = {}
        for status in ComplaintStatus:
            count = q.filter(Complaint.status == status).count()
            status_counts[status.value] = count

        # SLA
        sla_breached = q.filter(Complaint.resolution_breached == True).count()  # noqa: E712

        # Temps moyen de resolution
        resolved = q.filter(Complaint.resolved_at.isnot(None)).all()
        if resolved:
            resolution_times = [
                (c.resolved_at - c.created_at).total_seconds() / 3600
                for c in resolved
                if c.resolved_at
            ]
            avg_resolution_hours = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        else:
            avg_resolution_hours = 0

        return {
            "total": total,
            "by_status": status_counts,
            "sla_breached": sla_breached,
            "avg_resolution_hours": round(avg_resolution_hours, 2),
            "resolution_rate": round(status_counts.get("resolved", 0) / total * 100, 2) if total > 0 else 0
        }

    def generate_reference(self) -> str:
        """Genere une reference unique."""
        year = datetime.utcnow().year
        prefix = f"REC-{year}-"

        # Compter les reclamations de l'annee
        count = self.db.query(Complaint).filter(
            Complaint.tenant_id == self.tenant_id,
            Complaint.reference.like(f"{prefix}%")
        ).count()

        return f"{prefix}{count + 1:06d}"


# ============================================================================
# TEAM REPOSITORY
# ============================================================================

class TeamRepository(BaseRepository[ComplaintTeam]):
    """Repository pour les equipes."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, ComplaintTeam, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(ComplaintTeam).filter(
            ComplaintTeam.tenant_id == self.tenant_id,
            ComplaintTeam.deleted_at.is_(None)
        )

    def get_active(self) -> list[ComplaintTeam]:
        """Recupere les equipes actives."""
        return self._base_query().filter(
            ComplaintTeam.is_active == True  # noqa: E712
        ).order_by(ComplaintTeam.name).all()

    def get_with_members(self, id: UUID) -> ComplaintTeam | None:
        """Recupere une equipe avec ses membres."""
        return self._base_query().options(
            joinedload(ComplaintTeam.members)
        ).filter(ComplaintTeam.id == id).first()


# ============================================================================
# AGENT REPOSITORY
# ============================================================================

class AgentRepository(BaseRepository[ComplaintAgent]):
    """Repository pour les agents."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, ComplaintAgent, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(ComplaintAgent).filter(
            ComplaintAgent.tenant_id == self.tenant_id,
            ComplaintAgent.deleted_at.is_(None)
        )

    def get_by_user_id(self, user_id: UUID) -> ComplaintAgent | None:
        """Recupere un agent par user_id."""
        return self._base_query().filter(
            ComplaintAgent.user_id == user_id
        ).first()

    def get_available(self, team_id: UUID | None = None) -> list[ComplaintAgent]:
        """Recupere les agents disponibles."""
        q = self._base_query().filter(
            ComplaintAgent.is_active == True,  # noqa: E712
            ComplaintAgent.is_available == True  # noqa: E712
        )

        if team_id:
            q = q.filter(ComplaintAgent.team_id == team_id)

        return q.order_by(ComplaintAgent.current_load.asc()).all()

    def get_least_busy(self, team_id: UUID | None = None) -> ComplaintAgent | None:
        """Recupere l'agent le moins charge."""
        agents = self.get_available(team_id)
        if not agents:
            return None

        return min(agents, key=lambda a: a.current_load)

    def get_by_skill(self, skill: str, team_id: UUID | None = None) -> list[ComplaintAgent]:
        """Recupere les agents ayant une competence specifique."""
        q = self._base_query().filter(
            ComplaintAgent.is_active == True,  # noqa: E712
            ComplaintAgent.skills.contains([skill])
        )

        if team_id:
            q = q.filter(ComplaintAgent.team_id == team_id)

        return q.all()

    def update_load(self, agent_id: UUID, delta: int) -> ComplaintAgent | None:
        """Met a jour la charge d'un agent."""
        agent = self.get_by_id(agent_id)
        if agent:
            agent.current_load = max(0, agent.current_load + delta)
            if delta > 0:
                agent.last_assigned_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(agent)
        return agent


# ============================================================================
# CATEGORY CONFIG REPOSITORY
# ============================================================================

class CategoryConfigRepository(BaseRepository[ComplaintCategoryConfig]):
    """Repository pour les configurations de categories."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, ComplaintCategoryConfig, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(ComplaintCategoryConfig).filter(
            ComplaintCategoryConfig.tenant_id == self.tenant_id,
            ComplaintCategoryConfig.deleted_at.is_(None)
        )

    def get_by_code(self, code: str) -> ComplaintCategoryConfig | None:
        """Recupere une categorie par code."""
        return self._base_query().filter(
            ComplaintCategoryConfig.code == code
        ).first()

    def get_active(self, public_only: bool = False) -> list[ComplaintCategoryConfig]:
        """Recupere les categories actives."""
        q = self._base_query().filter(
            ComplaintCategoryConfig.is_active == True  # noqa: E712
        )

        if public_only:
            q = q.filter(ComplaintCategoryConfig.is_public == True)  # noqa: E712

        return q.order_by(ComplaintCategoryConfig.sort_order, ComplaintCategoryConfig.name).all()

    def get_children(self, parent_id: UUID) -> list[ComplaintCategoryConfig]:
        """Recupere les sous-categories."""
        return self._base_query().filter(
            ComplaintCategoryConfig.parent_id == parent_id,
            ComplaintCategoryConfig.is_active == True  # noqa: E712
        ).order_by(ComplaintCategoryConfig.sort_order).all()


# ============================================================================
# SLA POLICY REPOSITORY
# ============================================================================

class SLAPolicyRepository(BaseRepository[ComplaintSLAPolicy]):
    """Repository pour les politiques SLA."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, ComplaintSLAPolicy, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(ComplaintSLAPolicy).filter(
            ComplaintSLAPolicy.tenant_id == self.tenant_id,
            ComplaintSLAPolicy.deleted_at.is_(None)
        )

    def get_default(self) -> ComplaintSLAPolicy | None:
        """Recupere la politique SLA par defaut."""
        return self._base_query().filter(
            ComplaintSLAPolicy.is_default == True,  # noqa: E712
            ComplaintSLAPolicy.is_active == True  # noqa: E712
        ).first()

    def get_active(self) -> list[ComplaintSLAPolicy]:
        """Recupere les politiques SLA actives."""
        return self._base_query().filter(
            ComplaintSLAPolicy.is_active == True  # noqa: E712
        ).order_by(ComplaintSLAPolicy.name).all()


# ============================================================================
# EXCHANGE REPOSITORY
# ============================================================================

class ExchangeRepository(BaseRepository[ComplaintExchange]):
    """Repository pour les echanges."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, ComplaintExchange, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(ComplaintExchange).filter(
            ComplaintExchange.tenant_id == self.tenant_id,
            ComplaintExchange.deleted_at.is_(None)
        )

    def get_by_complaint(
        self,
        complaint_id: UUID,
        include_internal: bool = True
    ) -> list[ComplaintExchange]:
        """Recupere les echanges d'une reclamation."""
        q = self._base_query().filter(
            ComplaintExchange.complaint_id == complaint_id
        )

        if not include_internal:
            q = q.filter(ComplaintExchange.is_internal == False)  # noqa: E712

        return q.order_by(ComplaintExchange.created_at.asc()).all()

    def get_first_response(self, complaint_id: UUID) -> ComplaintExchange | None:
        """Recupere la premiere reponse d'une reclamation."""
        return self._base_query().filter(
            ComplaintExchange.complaint_id == complaint_id,
            ComplaintExchange.is_first_response == True  # noqa: E712
        ).first()


# ============================================================================
# ATTACHMENT REPOSITORY
# ============================================================================

class AttachmentRepository(BaseRepository[ComplaintAttachment]):
    """Repository pour les pieces jointes."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, ComplaintAttachment, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(ComplaintAttachment).filter(
            ComplaintAttachment.tenant_id == self.tenant_id,
            ComplaintAttachment.deleted_at.is_(None)
        )

    def get_by_complaint(self, complaint_id: UUID) -> list[ComplaintAttachment]:
        """Recupere les pieces jointes d'une reclamation."""
        return self._base_query().filter(
            ComplaintAttachment.complaint_id == complaint_id
        ).order_by(ComplaintAttachment.created_at.desc()).all()


# ============================================================================
# ACTION REPOSITORY
# ============================================================================

class ActionRepository(BaseRepository[ComplaintAction]):
    """Repository pour les actions."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, ComplaintAction, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(ComplaintAction).filter(
            ComplaintAction.tenant_id == self.tenant_id,
            ComplaintAction.deleted_at.is_(None)
        )

    def get_by_complaint(self, complaint_id: UUID) -> list[ComplaintAction]:
        """Recupere les actions d'une reclamation."""
        return self._base_query().filter(
            ComplaintAction.complaint_id == complaint_id
        ).order_by(ComplaintAction.created_at.desc()).all()

    def get_pending(
        self,
        agent_id: UUID | None = None,
        include_overdue: bool = True
    ) -> list[ComplaintAction]:
        """Recupere les actions en attente."""
        q = self._base_query().filter(
            ComplaintAction.status.in_(["pending", "in_progress"])
        )

        if agent_id:
            q = q.filter(ComplaintAction.assigned_to_id == agent_id)

        if include_overdue:
            q = q.order_by(ComplaintAction.due_date.asc().nullslast())
        else:
            now = datetime.utcnow()
            q = q.filter(
                or_(
                    ComplaintAction.due_date.is_(None),
                    ComplaintAction.due_date >= now
                )
            )

        return q.all()

    def get_overdue(self) -> list[ComplaintAction]:
        """Recupere les actions en retard."""
        now = datetime.utcnow()
        return self._base_query().filter(
            ComplaintAction.due_date < now,
            ComplaintAction.status.in_(["pending", "in_progress"])
        ).order_by(ComplaintAction.due_date.asc()).all()


# ============================================================================
# ESCALATION REPOSITORY
# ============================================================================

class EscalationRepository(BaseRepository[ComplaintEscalation]):
    """Repository pour les escalades."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, ComplaintEscalation, tenant_id)

    def get_by_complaint(self, complaint_id: UUID) -> list[ComplaintEscalation]:
        """Recupere les escalades d'une reclamation."""
        return self.db.query(ComplaintEscalation).filter(
            ComplaintEscalation.tenant_id == self.tenant_id,
            ComplaintEscalation.complaint_id == complaint_id
        ).order_by(ComplaintEscalation.created_at.desc()).all()


# ============================================================================
# HISTORY REPOSITORY
# ============================================================================

class HistoryRepository(BaseRepository[ComplaintHistory]):
    """Repository pour l'historique."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, ComplaintHistory, tenant_id)

    def get_by_complaint(self, complaint_id: UUID) -> list[ComplaintHistory]:
        """Recupere l'historique d'une reclamation."""
        return self.db.query(ComplaintHistory).filter(
            ComplaintHistory.tenant_id == self.tenant_id,
            ComplaintHistory.complaint_id == complaint_id
        ).order_by(ComplaintHistory.created_at.desc()).all()

    def add_entry(
        self,
        complaint_id: UUID,
        action: str,
        field_name: str | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
        actor_type: str = "user",
        actor_id: UUID | None = None,
        actor_name: str | None = None,
        actor_ip: str | None = None,
        context: dict | None = None
    ) -> ComplaintHistory:
        """Ajoute une entree d'historique."""
        entry = ComplaintHistory(
            tenant_id=self.tenant_id,
            complaint_id=complaint_id,
            action=action,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_ip=actor_ip,
            context=context
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry


# ============================================================================
# TEMPLATE REPOSITORY
# ============================================================================

class TemplateRepository(BaseRepository[ComplaintTemplate]):
    """Repository pour les modeles de reponse."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, ComplaintTemplate, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(ComplaintTemplate).filter(
            ComplaintTemplate.tenant_id == self.tenant_id,
            ComplaintTemplate.deleted_at.is_(None)
        )

    def get_by_code(self, code: str) -> ComplaintTemplate | None:
        """Recupere un modele par code."""
        return self._base_query().filter(
            ComplaintTemplate.code == code
        ).first()

    def get_active(
        self,
        category: ComplaintCategory | None = None,
        template_type: str | None = None,
        team_id: UUID | None = None,
        owner_id: UUID | None = None,
        search: str | None = None
    ) -> list[ComplaintTemplate]:
        """Recupere les modeles actifs."""
        q = self._base_query().filter(
            ComplaintTemplate.is_active == True  # noqa: E712
        )

        if category:
            q = q.filter(ComplaintTemplate.category == category)
        if template_type:
            q = q.filter(ComplaintTemplate.template_type == template_type)
        if team_id:
            q = q.filter(
                or_(
                    ComplaintTemplate.scope == "global",
                    and_(
                        ComplaintTemplate.scope == "team",
                        ComplaintTemplate.team_id == team_id
                    )
                )
            )
        if owner_id:
            q = q.filter(
                or_(
                    ComplaintTemplate.scope.in_(["global", "team"]),
                    and_(
                        ComplaintTemplate.scope == "personal",
                        ComplaintTemplate.owner_id == owner_id
                    )
                )
            )
        if search:
            search_term = f"%{search}%"
            q = q.filter(
                or_(
                    ComplaintTemplate.name.ilike(search_term),
                    ComplaintTemplate.code.ilike(search_term),
                    ComplaintTemplate.body.ilike(search_term)
                )
            )

        return q.order_by(ComplaintTemplate.usage_count.desc(), ComplaintTemplate.name).all()

    def increment_usage(self, template_id: UUID) -> ComplaintTemplate | None:
        """Incremente le compteur d'utilisation."""
        template = self.get_by_id(template_id)
        if template:
            template.usage_count += 1
            template.last_used_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(template)
        return template


# ============================================================================
# AUTOMATION RULE REPOSITORY
# ============================================================================

class AutomationRuleRepository(BaseRepository[ComplaintAutomationRule]):
    """Repository pour les regles d'automatisation."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, ComplaintAutomationRule, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(ComplaintAutomationRule).filter(
            ComplaintAutomationRule.tenant_id == self.tenant_id,
            ComplaintAutomationRule.deleted_at.is_(None)
        )

    def get_by_trigger(self, trigger_event: str) -> list[ComplaintAutomationRule]:
        """Recupere les regles par type de declencheur."""
        return self._base_query().filter(
            ComplaintAutomationRule.trigger_event == trigger_event,
            ComplaintAutomationRule.is_active == True  # noqa: E712
        ).order_by(ComplaintAutomationRule.priority.desc()).all()

    def get_active(self) -> list[ComplaintAutomationRule]:
        """Recupere les regles actives."""
        return self._base_query().filter(
            ComplaintAutomationRule.is_active == True  # noqa: E712
        ).order_by(ComplaintAutomationRule.priority.desc()).all()

    def increment_execution(
        self,
        rule_id: UUID,
        error: str | None = None
    ) -> ComplaintAutomationRule | None:
        """Met a jour les statistiques d'execution."""
        rule = self.get_by_id(rule_id)
        if rule:
            rule.execution_count += 1
            rule.last_executed_at = datetime.utcnow()
            if error:
                rule.last_error = error
            self.db.commit()
            self.db.refresh(rule)
        return rule


# ============================================================================
# METRICS REPOSITORY
# ============================================================================

class MetricsRepository(BaseRepository[ComplaintMetrics]):
    """Repository pour les metriques."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, ComplaintMetrics, tenant_id)

    def get_by_period(
        self,
        period_type: str,
        date_from: datetime,
        date_to: datetime,
        team_id: UUID | None = None,
        agent_id: UUID | None = None
    ) -> list[ComplaintMetrics]:
        """Recupere les metriques par periode."""
        q = self.db.query(ComplaintMetrics).filter(
            ComplaintMetrics.tenant_id == self.tenant_id,
            ComplaintMetrics.period_type == period_type,
            ComplaintMetrics.metric_date >= date_from,
            ComplaintMetrics.metric_date <= date_to
        )

        if team_id:
            q = q.filter(ComplaintMetrics.team_id == team_id)
        if agent_id:
            q = q.filter(ComplaintMetrics.agent_id == agent_id)

        return q.order_by(ComplaintMetrics.metric_date.asc()).all()

    def upsert_daily(
        self,
        metric_date: datetime,
        data: dict[str, Any],
        team_id: UUID | None = None,
        agent_id: UUID | None = None,
        category: ComplaintCategory | None = None,
        channel: ComplaintChannel | None = None
    ) -> ComplaintMetrics:
        """Met a jour ou cree les metriques du jour."""
        # Chercher l'entree existante
        q = self.db.query(ComplaintMetrics).filter(
            ComplaintMetrics.tenant_id == self.tenant_id,
            ComplaintMetrics.period_type == "daily",
            func.date(ComplaintMetrics.metric_date) == metric_date.date()
        )

        if team_id:
            q = q.filter(ComplaintMetrics.team_id == team_id)
        else:
            q = q.filter(ComplaintMetrics.team_id.is_(None))

        if agent_id:
            q = q.filter(ComplaintMetrics.agent_id == agent_id)
        else:
            q = q.filter(ComplaintMetrics.agent_id.is_(None))

        if category:
            q = q.filter(ComplaintMetrics.category == category)
        else:
            q = q.filter(ComplaintMetrics.category.is_(None))

        if channel:
            q = q.filter(ComplaintMetrics.channel == channel)
        else:
            q = q.filter(ComplaintMetrics.channel.is_(None))

        existing = q.first()

        if existing:
            # Mise a jour
            for key, value in data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Creation
            metrics = ComplaintMetrics(
                tenant_id=self.tenant_id,
                metric_date=metric_date,
                period_type="daily",
                team_id=team_id,
                agent_id=agent_id,
                category=category,
                channel=channel,
                **data
            )
            self.db.add(metrics)
            self.db.commit()
            self.db.refresh(metrics)
            return metrics
