"""
AZALS MODULE 16 - Helpdesk Service
===================================
Logique métier pour le système de support client.
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from .models import (
    AgentStatus,
    CannedResponse,
    HelpdeskAgent,
    HelpdeskAutomation,
    HelpdeskSLA,
    HelpdeskTeam,
    KBArticle,
    KBCategory,
    SatisfactionSurvey,
    Ticket,
    TicketAttachment,
    TicketCategory,
    TicketHistory,
    TicketPriority,
    TicketReply,
    TicketSource,
    TicketStatus,
)
from .schemas import (
    AgentCreate,
    AgentStats,
    AgentUpdate,
    AttachmentCreate,
    AutomationCreate,
    AutomationUpdate,
    CannedResponseCreate,
    CannedResponseUpdate,
    CategoryCreate,
    CategoryUpdate,
    HelpdeskDashboard,
    KBArticleCreate,
    KBArticleUpdate,
    KBCategoryCreate,
    KBCategoryUpdate,
    ReplyCreate,
    SatisfactionCreate,
    SLACreate,
    SLAUpdate,
    TeamCreate,
    TeamUpdate,
    TicketCreate,
    TicketStats,
    TicketUpdate,
)


class HelpdeskService:
    """Service Helpdesk."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2

    # ========================================================================
    # CATEGORIES
    # ========================================================================

    def list_categories(
        self,
        active_only: bool = True,
        public_only: bool = False,
        parent_id: int | None = None
    ) -> list[TicketCategory]:
        """Liste des catégories."""
        query = self.db.query(TicketCategory).filter(
            TicketCategory.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.filter(TicketCategory.is_active)
        if public_only:
            query = query.filter(TicketCategory.is_public)
        if parent_id is not None:
            query = query.filter(TicketCategory.parent_id == parent_id)
        else:
            query = query.filter(TicketCategory.parent_id is None)
        return query.order_by(TicketCategory.sort_order).all()

    def get_category(self, category_id: int) -> TicketCategory | None:
        """Récupère une catégorie."""
        return self.db.query(TicketCategory).filter(
            TicketCategory.id == category_id,
            TicketCategory.tenant_id == self.tenant_id
        ).first()

    def create_category(self, data: CategoryCreate) -> TicketCategory:
        """Crée une catégorie."""
        category = TicketCategory(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update_category(self, category_id: int, data: CategoryUpdate) -> TicketCategory | None:
        """Met à jour une catégorie."""
        category = self.get_category(category_id)
        if not category:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(category, key, value)
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, category_id: int) -> bool:
        """Supprime une catégorie."""
        category = self.get_category(category_id)
        if not category:
            return False
        category.is_active = False
        self.db.commit()
        return True

    # ========================================================================
    # TEAMS
    # ========================================================================

    def list_teams(self, active_only: bool = True) -> list[HelpdeskTeam]:
        """Liste des équipes."""
        query = self.db.query(HelpdeskTeam).filter(
            HelpdeskTeam.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.filter(HelpdeskTeam.is_active)
        return query.all()

    def get_team(self, team_id: int) -> HelpdeskTeam | None:
        """Récupère une équipe."""
        return self.db.query(HelpdeskTeam).filter(
            HelpdeskTeam.id == team_id,
            HelpdeskTeam.tenant_id == self.tenant_id
        ).first()

    def create_team(self, data: TeamCreate) -> HelpdeskTeam:
        """Crée une équipe."""
        team = HelpdeskTeam(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team

    def update_team(self, team_id: int, data: TeamUpdate) -> HelpdeskTeam | None:
        """Met à jour une équipe."""
        team = self.get_team(team_id)
        if not team:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(team, key, value)
        self.db.commit()
        self.db.refresh(team)
        return team

    def delete_team(self, team_id: int) -> bool:
        """Supprime une équipe."""
        team = self.get_team(team_id)
        if not team:
            return False
        team.is_active = False
        self.db.commit()
        return True

    # ========================================================================
    # AGENTS
    # ========================================================================

    def list_agents(
        self,
        active_only: bool = True,
        team_id: int | None = None,
        status: AgentStatus | None = None
    ) -> list[HelpdeskAgent]:
        """Liste des agents."""
        query = self.db.query(HelpdeskAgent).filter(
            HelpdeskAgent.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.filter(HelpdeskAgent.is_active)
        if team_id:
            query = query.filter(HelpdeskAgent.team_id == team_id)
        if status:
            query = query.filter(HelpdeskAgent.status == status)
        return query.all()

    def get_agent(self, agent_id: int) -> HelpdeskAgent | None:
        """Récupère un agent."""
        return self.db.query(HelpdeskAgent).filter(
            HelpdeskAgent.id == agent_id,
            HelpdeskAgent.tenant_id == self.tenant_id
        ).first()

    def get_agent_by_user(self, user_id: int) -> HelpdeskAgent | None:
        """Récupère agent par user_id."""
        return self.db.query(HelpdeskAgent).filter(
            HelpdeskAgent.user_id == user_id,
            HelpdeskAgent.tenant_id == self.tenant_id
        ).first()

    def create_agent(self, data: AgentCreate) -> HelpdeskAgent:
        """Crée un agent."""
        agent = HelpdeskAgent(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def update_agent(self, agent_id: int, data: AgentUpdate) -> HelpdeskAgent | None:
        """Met à jour un agent."""
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(agent, key, value)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def update_agent_status(self, agent_id: int, status: AgentStatus) -> HelpdeskAgent | None:
        """Met à jour le statut d'un agent."""
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        agent.status = status
        agent.last_seen = datetime.utcnow()
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def delete_agent(self, agent_id: int) -> bool:
        """Supprime un agent."""
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        agent.is_active = False
        self.db.commit()
        return True

    # ========================================================================
    # SLA
    # ========================================================================

    def list_slas(self, active_only: bool = True) -> list[HelpdeskSLA]:
        """Liste des SLAs."""
        query = self.db.query(HelpdeskSLA).filter(
            HelpdeskSLA.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.filter(HelpdeskSLA.is_active)
        return query.all()

    def get_sla(self, sla_id: int) -> HelpdeskSLA | None:
        """Récupère un SLA."""
        return self.db.query(HelpdeskSLA).filter(
            HelpdeskSLA.id == sla_id,
            HelpdeskSLA.tenant_id == self.tenant_id
        ).first()

    def get_default_sla(self) -> HelpdeskSLA | None:
        """Récupère le SLA par défaut."""
        return self.db.query(HelpdeskSLA).filter(
            HelpdeskSLA.tenant_id == self.tenant_id,
            HelpdeskSLA.is_default,
            HelpdeskSLA.is_active
        ).first()

    def create_sla(self, data: SLACreate) -> HelpdeskSLA:
        """Crée un SLA."""
        # Si default, retirer les autres
        if data.is_default:
            self.db.query(HelpdeskSLA).filter(
                HelpdeskSLA.tenant_id == self.tenant_id,
                HelpdeskSLA.is_default
            ).update({"is_default": False})

        sla = HelpdeskSLA(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(sla)
        self.db.commit()
        self.db.refresh(sla)
        return sla

    def update_sla(self, sla_id: int, data: SLAUpdate) -> HelpdeskSLA | None:
        """Met à jour un SLA."""
        sla = self.get_sla(sla_id)
        if not sla:
            return None

        # Si on définit comme default
        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("is_default"):
            self.db.query(HelpdeskSLA).filter(
                HelpdeskSLA.tenant_id == self.tenant_id,
                HelpdeskSLA.is_default,
                HelpdeskSLA.id != sla_id
            ).update({"is_default": False})

        for key, value in update_data.items():
            setattr(sla, key, value)
        self.db.commit()
        self.db.refresh(sla)
        return sla

    def delete_sla(self, sla_id: int) -> bool:
        """Supprime un SLA."""
        sla = self.get_sla(sla_id)
        if not sla:
            return False
        sla.is_active = False
        self.db.commit()
        return True

    # ========================================================================
    # TICKETS
    # ========================================================================

    def _generate_ticket_number(self) -> str:
        """Génère un numéro de ticket unique."""
        prefix = datetime.utcnow().strftime("%Y%m")
        suffix = str(uuid.uuid4().hex[:6]).upper()
        return f"TK-{prefix}-{suffix}"

    def _calculate_sla_due_dates(
        self,
        priority: TicketPriority,
        sla: HelpdeskSLA | None = None
    ) -> tuple[datetime | None, datetime | None]:
        """Calcule les dates dues SLA."""
        if not sla:
            sla = self.get_default_sla()
        if not sla:
            return None, None

        now = datetime.utcnow()

        # Temps de première réponse
        response_times = {
            TicketPriority.LOW: sla.first_response_low,
            TicketPriority.MEDIUM: sla.first_response_medium,
            TicketPriority.HIGH: sla.first_response_high,
            TicketPriority.URGENT: sla.first_response_urgent,
            TicketPriority.CRITICAL: sla.first_response_critical,
        }

        # Temps de résolution
        resolution_times = {
            TicketPriority.LOW: sla.resolution_low,
            TicketPriority.MEDIUM: sla.resolution_medium,
            TicketPriority.HIGH: sla.resolution_high,
            TicketPriority.URGENT: sla.resolution_urgent,
            TicketPriority.CRITICAL: sla.resolution_critical,
        }

        response_due = now + timedelta(minutes=response_times.get(priority, 480))
        resolution_due = now + timedelta(minutes=resolution_times.get(priority, 2880))

        return response_due, resolution_due

    def _auto_assign_ticket(self, team: HelpdeskTeam) -> int | None:
        """Auto-assigne un ticket selon la méthode de l'équipe."""
        if not team or team.auto_assign_method == "manual":
            return None

        # Récupérer les agents disponibles de l'équipe
        agents = self.db.query(HelpdeskAgent).filter(
            HelpdeskAgent.tenant_id == self.tenant_id,
            HelpdeskAgent.team_id == team.id,
            HelpdeskAgent.is_active,
            HelpdeskAgent.status.in_([AgentStatus.AVAILABLE, AgentStatus.BUSY])
        ).all()

        if not agents:
            return None

        if team.auto_assign_method == "round_robin":
            # Prendre l'agent avec le moins de tickets assignés
            agents.sort(key=lambda a: a.tickets_assigned)
            return agents[0].id
        elif team.auto_assign_method == "least_busy":
            # Prendre l'agent avec le moins de tickets ouverts
            for agent in agents:
                agent._open_tickets = self.db.query(Ticket).filter(
                    Ticket.assigned_to_id == agent.id,
                    Ticket.status.in_([TicketStatus.NEW, TicketStatus.OPEN, TicketStatus.PENDING])
                ).count()
            agents.sort(key=lambda a: a._open_tickets)
            return agents[0].id
        elif team.auto_assign_method == "random":
            import random
            return random.choice(agents).id

        return None

    def list_tickets(
        self,
        status: TicketStatus | None = None,
        priority: TicketPriority | None = None,
        category_id: int | None = None,
        team_id: int | None = None,
        assigned_to_id: int | None = None,
        requester_id: int | None = None,
        requester_email: str | None = None,
        overdue_only: bool = False,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Ticket], int]:
        """Liste des tickets avec filtres."""
        query = self.db.query(Ticket).filter(
            Ticket.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(Ticket.status == status)
        if priority:
            query = query.filter(Ticket.priority == priority)
        if category_id:
            query = query.filter(Ticket.category_id == category_id)
        if team_id:
            query = query.filter(Ticket.team_id == team_id)
        if assigned_to_id:
            query = query.filter(Ticket.assigned_to_id == assigned_to_id)
        if requester_id:
            query = query.filter(Ticket.requester_id == requester_id)
        if requester_email:
            query = query.filter(Ticket.requester_email == requester_email)
        if overdue_only:
            now = datetime.utcnow()
            query = query.filter(
                or_(
                    and_(Ticket.first_response_due < now, Ticket.first_responded_at is None),
                    and_(Ticket.resolution_due < now, Ticket.resolved_at is None)
                )
            )
        if search:
            query = query.filter(
                or_(
                    Ticket.subject.ilike(f"%{search}%"),
                    Ticket.ticket_number.ilike(f"%{search}%"),
                    Ticket.requester_email.ilike(f"%{search}%")
                )
            )

        total = query.count()
        tickets = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()

        return tickets, total

    def get_ticket(self, ticket_id: int) -> Ticket | None:
        """Récupère un ticket."""
        return self.db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.tenant_id == self.tenant_id
        ).first()

    def get_ticket_by_number(self, ticket_number: str) -> Ticket | None:
        """Récupère un ticket par numéro."""
        return self.db.query(Ticket).filter(
            Ticket.ticket_number == ticket_number,
            Ticket.tenant_id == self.tenant_id
        ).first()

    def create_ticket(
        self,
        data: TicketCreate,
        actor_id: int | None = None,
        actor_name: str | None = None,
        actor_type: str = "customer"
    ) -> Ticket:
        """Crée un ticket."""
        # Déterminer la catégorie et récupérer les defaults
        category = None
        if data.category_id:
            category = self.get_category(data.category_id)

        # Déterminer l'équipe
        team_id = data.team_id
        if not team_id and category and category.default_team_id:
            team_id = category.default_team_id

        team = self.get_team(team_id) if team_id else None

        # Déterminer le SLA
        sla_id = None
        if category and category.sla_id:
            sla_id = category.sla_id
        elif team and team.default_sla_id:
            sla_id = team.default_sla_id

        sla = self.get_sla(sla_id) if sla_id else self.get_default_sla()

        # Calculer les dates SLA
        priority = data.priority
        if not priority and category:
            priority = category.default_priority

        first_response_due, resolution_due = self._calculate_sla_due_dates(priority, sla)

        # Auto-assignation
        assigned_to_id = data.assigned_to_id
        if not assigned_to_id and category and category.auto_assign and team:
            assigned_to_id = self._auto_assign_ticket(team)

        # Créer le ticket
        ticket = Ticket(
            tenant_id=self.tenant_id,
            ticket_number=self._generate_ticket_number(),
            subject=data.subject,
            description=data.description,
            category_id=data.category_id,
            team_id=team_id,
            sla_id=sla.id if sla else None,
            priority=priority,
            source=data.source,
            status=TicketStatus.NEW,
            requester_id=data.requester_id,
            requester_name=data.requester_name,
            requester_email=data.requester_email,
            requester_phone=data.requester_phone,
            company_id=data.company_id,
            assigned_to_id=assigned_to_id,
            first_response_due=first_response_due,
            resolution_due=resolution_due,
            tags=data.tags,
            custom_fields=data.custom_fields
        )
        self.db.add(ticket)
        self.db.flush()

        # Historique création
        history = TicketHistory(
            tenant_id=self.tenant_id,
            ticket_id=ticket.id,
            action="created",
            actor_type=actor_type,
            actor_id=actor_id,
            actor_name=actor_name
        )
        self.db.add(history)

        # Incrémenter compteur agent si assigné
        if assigned_to_id:
            agent = self.get_agent(assigned_to_id)
            if agent:
                agent.tickets_assigned += 1

            # Historique assignation
            assign_history = TicketHistory(
                tenant_id=self.tenant_id,
                ticket_id=ticket.id,
                action="assigned",
                field_name="assigned_to_id",
                new_value=str(assigned_to_id),
                actor_type="system",
                actor_name="Auto-assignation"
            )
            self.db.add(assign_history)

        self.db.commit()
        self.db.refresh(ticket)

        return ticket

    def update_ticket(
        self,
        ticket_id: int,
        data: TicketUpdate,
        actor_id: int | None = None,
        actor_name: str | None = None,
        actor_type: str = "agent"
    ) -> Ticket | None:
        """Met à jour un ticket."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            old_value = getattr(ticket, key)
            if old_value != value:
                setattr(ticket, key, value)

                # Historique
                history = TicketHistory(
                    tenant_id=self.tenant_id,
                    ticket_id=ticket.id,
                    action="updated",
                    field_name=key,
                    old_value=str(old_value) if old_value else None,
                    new_value=str(value) if value else None,
                    actor_type=actor_type,
                    actor_id=actor_id,
                    actor_name=actor_name
                )
                self.db.add(history)

        ticket.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(ticket)

        return ticket

    def assign_ticket(
        self,
        ticket_id: int,
        agent_id: int,
        actor_id: int | None = None,
        actor_name: str | None = None
    ) -> Ticket | None:
        """Assigne un ticket à un agent."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None

        agent = self.get_agent(agent_id)
        if not agent:
            return None

        old_agent_id = ticket.assigned_to_id
        ticket.assigned_to_id = agent_id
        ticket.updated_at = datetime.utcnow()

        # Si premier assignement et statut NEW, passer à OPEN
        if ticket.status == TicketStatus.NEW:
            ticket.status = TicketStatus.OPEN

        # Mettre à jour les compteurs
        if old_agent_id:
            old_agent = self.get_agent(old_agent_id)
            if old_agent and old_agent.tickets_assigned > 0:
                old_agent.tickets_assigned -= 1

        agent.tickets_assigned += 1

        # Historique
        history = TicketHistory(
            tenant_id=self.tenant_id,
            ticket_id=ticket.id,
            action="assigned",
            field_name="assigned_to_id",
            old_value=str(old_agent_id) if old_agent_id else None,
            new_value=str(agent_id),
            actor_type="agent",
            actor_id=actor_id,
            actor_name=actor_name
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(ticket)

        return ticket

    def change_ticket_status(
        self,
        ticket_id: int,
        new_status: TicketStatus,
        comment: str | None = None,
        actor_id: int | None = None,
        actor_name: str | None = None,
        actor_type: str = "agent"
    ) -> Ticket | None:
        """Change le statut d'un ticket."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None

        old_status = ticket.status
        ticket.status = new_status
        ticket.updated_at = datetime.utcnow()

        # Gérer les dates spéciales
        if new_status == TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.utcnow()
            # Vérifier SLA
            if ticket.resolution_due and ticket.resolved_at > ticket.resolution_due:
                ticket.sla_breached = True
            # Incrémenter compteur agent
            if ticket.assigned_to_id:
                agent = self.get_agent(ticket.assigned_to_id)
                if agent:
                    agent.tickets_resolved += 1

        elif new_status == TicketStatus.CLOSED:
            ticket.closed_at = datetime.utcnow()

        # Historique
        history = TicketHistory(
            tenant_id=self.tenant_id,
            ticket_id=ticket.id,
            action="status_changed",
            field_name="status",
            old_value=old_status.value,
            new_value=new_status.value,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_name=actor_name
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(ticket)

        return ticket

    def merge_tickets(
        self,
        source_ticket_id: int,
        target_ticket_id: int,
        actor_id: int | None = None,
        actor_name: str | None = None
    ) -> Ticket | None:
        """Fusionne un ticket dans un autre."""
        source = self.get_ticket(source_ticket_id)
        target = self.get_ticket(target_ticket_id)

        if not source or not target:
            return None

        # Déplacer les réponses
        self.db.query(TicketReply).filter(
            TicketReply.ticket_id == source.id
        ).update({"ticket_id": target.id})

        # Déplacer les pièces jointes
        self.db.query(TicketAttachment).filter(
            TicketAttachment.ticket_id == source.id
        ).update({"ticket_id": target.id})

        # Marquer le source comme fusionné
        source.merged_into_id = target.id
        source.status = TicketStatus.CLOSED
        source.closed_at = datetime.utcnow()

        # Mettre à jour les compteurs
        target.reply_count += source.reply_count

        # Historiques
        source_history = TicketHistory(
            tenant_id=self.tenant_id,
            ticket_id=source.id,
            action="merged",
            new_value=f"Merged into {target.ticket_number}",
            actor_type="agent",
            actor_id=actor_id,
            actor_name=actor_name
        )
        target_history = TicketHistory(
            tenant_id=self.tenant_id,
            ticket_id=target.id,
            action="merged",
            new_value=f"Merged from {source.ticket_number}",
            actor_type="agent",
            actor_id=actor_id,
            actor_name=actor_name
        )
        self.db.add(source_history)
        self.db.add(target_history)

        self.db.commit()
        self.db.refresh(target)

        return target

    # ========================================================================
    # REPLIES
    # ========================================================================

    def list_replies(self, ticket_id: int, include_internal: bool = True) -> list[TicketReply]:
        """Liste les réponses d'un ticket."""
        query = self.db.query(TicketReply).filter(
            TicketReply.ticket_id == ticket_id,
            TicketReply.tenant_id == self.tenant_id
        )
        if not include_internal:
            query = query.filter(not TicketReply.is_internal)
        return query.order_by(TicketReply.created_at.asc()).all()

    def add_reply(
        self,
        ticket_id: int,
        data: ReplyCreate,
        author_id: int | None = None,
        author_name: str | None = None,
        author_email: str | None = None,
        author_type: str = "agent"
    ) -> TicketReply | None:
        """Ajoute une réponse à un ticket."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None

        # Vérifier si c'est la première réponse
        is_first = not ticket.first_responded_at and author_type == "agent" and not data.is_internal

        reply = TicketReply(
            tenant_id=self.tenant_id,
            ticket_id=ticket_id,
            body=data.body,
            body_html=data.body_html,
            is_internal=data.is_internal,
            is_first_response=is_first,
            author_type=author_type,
            author_id=author_id,
            author_name=author_name,
            author_email=author_email,
            cc_emails=data.cc_emails,
            bcc_emails=data.bcc_emails
        )
        self.db.add(reply)

        # Mettre à jour le ticket
        if data.is_internal:
            ticket.internal_note_count += 1
        else:
            ticket.reply_count += 1

        # Si première réponse agent
        if is_first:
            ticket.first_responded_at = datetime.utcnow()
            # Vérifier SLA première réponse
            if ticket.first_response_due and ticket.first_responded_at > ticket.first_response_due:
                ticket.sla_breached = True

        # Si réponse client et statut pending, repasser à open
        if author_type == "customer" and ticket.status == TicketStatus.PENDING:
            ticket.status = TicketStatus.OPEN

        ticket.updated_at = datetime.utcnow()

        # Historique
        action = "note_added" if data.is_internal else "reply_added"
        history = TicketHistory(
            tenant_id=self.tenant_id,
            ticket_id=ticket_id,
            action=action,
            actor_type=author_type,
            actor_id=author_id,
            actor_name=author_name
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(reply)

        return reply

    # ========================================================================
    # ATTACHMENTS
    # ========================================================================

    def add_attachment(
        self,
        ticket_id: int,
        data: AttachmentCreate,
        uploaded_by_id: int | None = None
    ) -> TicketAttachment | None:
        """Ajoute une pièce jointe."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None

        attachment = TicketAttachment(
            tenant_id=self.tenant_id,
            ticket_id=ticket_id,
            reply_id=data.reply_id,
            filename=data.filename,
            file_path=data.file_path,
            file_url=data.file_url,
            file_size=data.file_size,
            mime_type=data.mime_type,
            uploaded_by_id=uploaded_by_id
        )
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)

        return attachment

    def list_attachments(self, ticket_id: int) -> list[TicketAttachment]:
        """Liste les pièces jointes d'un ticket."""
        return self.db.query(TicketAttachment).filter(
            TicketAttachment.ticket_id == ticket_id,
            TicketAttachment.tenant_id == self.tenant_id
        ).all()

    # ========================================================================
    # HISTORY
    # ========================================================================

    def get_ticket_history(self, ticket_id: int) -> list[TicketHistory]:
        """Récupère l'historique d'un ticket."""
        return self.db.query(TicketHistory).filter(
            TicketHistory.ticket_id == ticket_id,
            TicketHistory.tenant_id == self.tenant_id
        ).order_by(TicketHistory.created_at.desc()).all()

    # ========================================================================
    # CANNED RESPONSES
    # ========================================================================

    def list_canned_responses(
        self,
        team_id: int | None = None,
        agent_id: int | None = None,
        category: str | None = None,
        search: str | None = None
    ) -> list[CannedResponse]:
        """Liste les réponses pré-enregistrées."""
        query = self.db.query(CannedResponse).filter(
            CannedResponse.tenant_id == self.tenant_id,
            CannedResponse.is_active
        )

        # Scope: global OU team OU personnel
        scope_filters = [CannedResponse.scope == "global"]
        if team_id:
            scope_filters.append(
                and_(CannedResponse.scope == "team", CannedResponse.team_id == team_id)
            )
        if agent_id:
            scope_filters.append(
                and_(CannedResponse.scope == "personal", CannedResponse.agent_id == agent_id)
            )
        query = query.filter(or_(*scope_filters))

        if category:
            query = query.filter(CannedResponse.category == category)
        if search:
            query = query.filter(
                or_(
                    CannedResponse.title.ilike(f"%{search}%"),
                    CannedResponse.shortcut.ilike(f"%{search}%")
                )
            )

        return query.order_by(CannedResponse.usage_count.desc()).all()

    def get_canned_response(self, response_id: int) -> CannedResponse | None:
        """Récupère une réponse pré-enregistrée."""
        return self.db.query(CannedResponse).filter(
            CannedResponse.id == response_id,
            CannedResponse.tenant_id == self.tenant_id
        ).first()

    def get_canned_by_shortcut(self, shortcut: str) -> CannedResponse | None:
        """Récupère par shortcut."""
        return self.db.query(CannedResponse).filter(
            CannedResponse.shortcut == shortcut,
            CannedResponse.tenant_id == self.tenant_id,
            CannedResponse.is_active
        ).first()

    def create_canned_response(
        self,
        data: CannedResponseCreate,
        agent_id: int | None = None
    ) -> CannedResponse:
        """Crée une réponse pré-enregistrée."""
        response = CannedResponse(
            tenant_id=self.tenant_id,
            agent_id=agent_id if data.scope == "personal" else None,
            **data.model_dump()
        )
        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)
        return response

    def update_canned_response(
        self,
        response_id: int,
        data: CannedResponseUpdate
    ) -> CannedResponse | None:
        """Met à jour une réponse pré-enregistrée."""
        response = self.get_canned_response(response_id)
        if not response:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(response, key, value)
        self.db.commit()
        self.db.refresh(response)
        return response

    def use_canned_response(self, response_id: int) -> CannedResponse | None:
        """Incrémente le compteur d'utilisation."""
        response = self.get_canned_response(response_id)
        if not response:
            return None
        response.usage_count += 1
        self.db.commit()
        return response

    def delete_canned_response(self, response_id: int) -> bool:
        """Supprime une réponse pré-enregistrée."""
        response = self.get_canned_response(response_id)
        if not response:
            return False
        response.is_active = False
        self.db.commit()
        return True

    # ========================================================================
    # KNOWLEDGE BASE
    # ========================================================================

    def list_kb_categories(
        self,
        parent_id: int | None = None,
        public_only: bool = False
    ) -> list[KBCategory]:
        """Liste les catégories KB."""
        query = self.db.query(KBCategory).filter(
            KBCategory.tenant_id == self.tenant_id,
            KBCategory.is_active
        )
        if public_only:
            query = query.filter(KBCategory.is_public)
        if parent_id is not None:
            query = query.filter(KBCategory.parent_id == parent_id)
        else:
            query = query.filter(KBCategory.parent_id is None)
        return query.order_by(KBCategory.sort_order).all()

    def get_kb_category(self, category_id: int) -> KBCategory | None:
        """Récupère une catégorie KB."""
        return self.db.query(KBCategory).filter(
            KBCategory.id == category_id,
            KBCategory.tenant_id == self.tenant_id
        ).first()

    def create_kb_category(self, data: KBCategoryCreate) -> KBCategory:
        """Crée une catégorie KB."""
        category = KBCategory(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update_kb_category(
        self,
        category_id: int,
        data: KBCategoryUpdate
    ) -> KBCategory | None:
        """Met à jour une catégorie KB."""
        category = self.get_kb_category(category_id)
        if not category:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(category, key, value)
        self.db.commit()
        self.db.refresh(category)
        return category

    def list_kb_articles(
        self,
        category_id: int | None = None,
        status: str | None = None,
        public_only: bool = False,
        featured_only: bool = False,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[KBArticle], int]:
        """Liste les articles KB."""
        query = self.db.query(KBArticle).filter(
            KBArticle.tenant_id == self.tenant_id
        )

        if category_id:
            query = query.filter(KBArticle.category_id == category_id)
        if status:
            query = query.filter(KBArticle.status == status)
        if public_only:
            query = query.filter(
                KBArticle.is_public,
                KBArticle.status == "published"
            )
        if featured_only:
            query = query.filter(KBArticle.is_featured)
        if search:
            query = query.filter(
                or_(
                    KBArticle.title.ilike(f"%{search}%"),
                    KBArticle.body.ilike(f"%{search}%")
                )
            )

        total = query.count()
        articles = query.order_by(
            KBArticle.is_featured.desc(),
            KBArticle.view_count.desc()
        ).offset(skip).limit(limit).all()

        return articles, total

    def get_kb_article(self, article_id: int) -> KBArticle | None:
        """Récupère un article KB."""
        return self.db.query(KBArticle).filter(
            KBArticle.id == article_id,
            KBArticle.tenant_id == self.tenant_id
        ).first()

    def get_kb_article_by_slug(self, slug: str) -> KBArticle | None:
        """Récupère un article par slug."""
        return self.db.query(KBArticle).filter(
            KBArticle.slug == slug,
            KBArticle.tenant_id == self.tenant_id
        ).first()

    def create_kb_article(
        self,
        data: KBArticleCreate,
        author_id: int | None = None,
        author_name: str | None = None
    ) -> KBArticle:
        """Crée un article KB."""
        article = KBArticle(
            tenant_id=self.tenant_id,
            author_id=author_id,
            author_name=author_name,
            **data.model_dump()
        )
        if data.status == "published":
            article.published_at = datetime.utcnow()
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        return article

    def update_kb_article(
        self,
        article_id: int,
        data: KBArticleUpdate
    ) -> KBArticle | None:
        """Met à jour un article KB."""
        article = self.get_kb_article(article_id)
        if not article:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Gérer la publication
        if update_data.get("status") == "published" and not article.published_at:
            article.published_at = datetime.utcnow()

        for key, value in update_data.items():
            setattr(article, key, value)

        self.db.commit()
        self.db.refresh(article)
        return article

    def view_kb_article(self, article_id: int) -> KBArticle | None:
        """Incrémente le compteur de vues."""
        article = self.get_kb_article(article_id)
        if not article:
            return None
        article.view_count += 1
        self.db.commit()
        return article

    def rate_kb_article(self, article_id: int, helpful: bool) -> KBArticle | None:
        """Note un article (utile/pas utile)."""
        article = self.get_kb_article(article_id)
        if not article:
            return None
        if helpful:
            article.helpful_count += 1
        else:
            article.not_helpful_count += 1
        self.db.commit()
        return article

    # ========================================================================
    # SATISFACTION
    # ========================================================================

    def submit_satisfaction(
        self,
        data: SatisfactionCreate,
        customer_id: int | None = None
    ) -> SatisfactionSurvey | None:
        """Soumet une enquête de satisfaction."""
        ticket = self.get_ticket(data.ticket_id)
        if not ticket:
            return None

        survey = SatisfactionSurvey(
            tenant_id=self.tenant_id,
            ticket_id=data.ticket_id,
            rating=data.rating,
            feedback=data.feedback,
            customer_id=customer_id,
            customer_email=data.customer_email,
            agent_id=ticket.assigned_to_id
        )
        self.db.add(survey)

        # Mettre à jour le ticket
        ticket.satisfaction_rating = data.rating

        # Mettre à jour les stats de l'agent
        if ticket.assigned_to_id:
            agent = self.get_agent(ticket.assigned_to_id)
            if agent:
                # Recalculer la moyenne
                total_surveys = self.db.query(SatisfactionSurvey).filter(
                    SatisfactionSurvey.agent_id == agent.id
                ).count()
                if total_surveys > 0:
                    avg = self.db.query(func.avg(SatisfactionSurvey.rating)).filter(
                        SatisfactionSurvey.agent_id == agent.id
                    ).scalar()
                    agent.satisfaction_score = Decimal(str(round(avg, 2)))

        self.db.commit()
        self.db.refresh(survey)

        return survey

    def get_satisfaction_stats(
        self,
        agent_id: int | None = None,
        days: int = 30
    ) -> dict[str, Any]:
        """Statistiques de satisfaction."""
        since = datetime.utcnow() - timedelta(days=days)

        query = self.db.query(SatisfactionSurvey).filter(
            SatisfactionSurvey.tenant_id == self.tenant_id,
            SatisfactionSurvey.created_at >= since
        )

        if agent_id:
            query = query.filter(SatisfactionSurvey.agent_id == agent_id)

        surveys = query.all()

        if not surveys:
            return {
                "total_surveys": 0,
                "average_rating": 0,
                "distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }

        total = len(surveys)
        avg = sum(s.rating for s in surveys) / total
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for s in surveys:
            distribution[s.rating] += 1

        return {
            "total_surveys": total,
            "average_rating": round(avg, 2),
            "distribution": distribution
        }

    # ========================================================================
    # AUTOMATIONS
    # ========================================================================

    def list_automations(self, active_only: bool = True) -> list[HelpdeskAutomation]:
        """Liste les automatisations."""
        query = self.db.query(HelpdeskAutomation).filter(
            HelpdeskAutomation.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.filter(HelpdeskAutomation.is_active)
        return query.order_by(HelpdeskAutomation.priority.desc()).all()

    def get_automation(self, automation_id: int) -> HelpdeskAutomation | None:
        """Récupère une automatisation."""
        return self.db.query(HelpdeskAutomation).filter(
            HelpdeskAutomation.id == automation_id,
            HelpdeskAutomation.tenant_id == self.tenant_id
        ).first()

    def create_automation(self, data: AutomationCreate) -> HelpdeskAutomation:
        """Crée une automatisation."""
        automation = HelpdeskAutomation(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(automation)
        self.db.commit()
        self.db.refresh(automation)
        return automation

    def update_automation(
        self,
        automation_id: int,
        data: AutomationUpdate
    ) -> HelpdeskAutomation | None:
        """Met à jour une automatisation."""
        automation = self.get_automation(automation_id)
        if not automation:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(automation, key, value)
        self.db.commit()
        self.db.refresh(automation)
        return automation

    def delete_automation(self, automation_id: int) -> bool:
        """Supprime une automatisation."""
        automation = self.get_automation(automation_id)
        if not automation:
            return False
        automation.is_active = False
        self.db.commit()
        return True

    # ========================================================================
    # DASHBOARD & STATS
    # ========================================================================

    def get_ticket_stats(self, days: int = 30) -> TicketStats:
        """Statistiques des tickets."""
        since = datetime.utcnow() - timedelta(days=days)
        now = datetime.utcnow()

        base_query = self.db.query(Ticket).filter(
            Ticket.tenant_id == self.tenant_id,
            Ticket.created_at >= since
        )

        total = base_query.count()

        # Par statut
        status_counts = {}
        for status in TicketStatus:
            count = base_query.filter(Ticket.status == status).count()
            status_counts[status.value] = count

        # Overdue
        overdue = base_query.filter(
            or_(
                and_(Ticket.first_response_due < now, Ticket.first_responded_at is None),
                and_(Ticket.resolution_due < now, Ticket.resolved_at is None)
            ),
            Ticket.status.notin_([TicketStatus.RESOLVED, TicketStatus.CLOSED])
        ).count()

        # SLA stats
        resolved_tickets = base_query.filter(Ticket.resolved_at is not None).all()

        avg_resolution = 0
        response_sla_met = 0
        resolution_sla_met = 0

        if resolved_tickets:
            total_resolution_time = 0
            response_met_count = 0
            resolution_met_count = 0

            for t in resolved_tickets:
                # Temps de résolution
                if t.resolved_at and t.created_at:
                    delta = (t.resolved_at - t.created_at).total_seconds() / 60
                    total_resolution_time += delta

                # SLA première réponse
                if t.first_response_due and t.first_responded_at:
                    if t.first_responded_at <= t.first_response_due:
                        response_met_count += 1

                # SLA résolution
                if t.resolution_due and t.resolved_at and t.resolved_at <= t.resolution_due:
                    resolution_met_count += 1

            avg_resolution = total_resolution_time / len(resolved_tickets)
            response_sla_met = (response_met_count / len(resolved_tickets)) * 100
            resolution_sla_met = (resolution_met_count / len(resolved_tickets)) * 100

        return TicketStats(
            total=total,
            new=status_counts.get("new", 0),
            open=status_counts.get("open", 0),
            pending=status_counts.get("pending", 0),
            on_hold=status_counts.get("on_hold", 0),
            resolved=status_counts.get("resolved", 0),
            closed=status_counts.get("closed", 0),
            overdue=overdue,
            avg_resolution_time=round(avg_resolution, 2),
            first_response_sla_met=round(response_sla_met, 2),
            resolution_sla_met=round(resolution_sla_met, 2)
        )

    def get_agent_stats(self, days: int = 30) -> list[AgentStats]:
        """Statistiques par agent."""
        agents = self.list_agents(active_only=True)
        since = datetime.utcnow() - timedelta(days=days)

        stats = []
        for agent in agents:
            # Tickets assignés dans la période
            assigned = self.db.query(Ticket).filter(
                Ticket.tenant_id == self.tenant_id,
                Ticket.assigned_to_id == agent.id,
                Ticket.created_at >= since
            ).count()

            # Tickets résolus
            resolved = self.db.query(Ticket).filter(
                Ticket.tenant_id == self.tenant_id,
                Ticket.assigned_to_id == agent.id,
                Ticket.resolved_at >= since
            ).count()

            stats.append(AgentStats(
                agent_id=agent.id,
                agent_name=agent.display_name,
                tickets_assigned=assigned,
                tickets_resolved=resolved,
                avg_resolution_time=float(agent.avg_resolution_time),
                satisfaction_score=float(agent.satisfaction_score),
                response_rate=round((resolved / assigned * 100) if assigned > 0 else 0, 2)
            ))

        return stats

    def get_dashboard(self, days: int = 30) -> HelpdeskDashboard:
        """Dashboard complet."""
        ticket_stats = self.get_ticket_stats(days)
        agent_stats = self.get_agent_stats(days)

        since = datetime.utcnow() - timedelta(days=days)

        # Par priorité
        priority_counts = {}
        for priority in TicketPriority:
            count = self.db.query(Ticket).filter(
                Ticket.tenant_id == self.tenant_id,
                Ticket.priority == priority,
                Ticket.created_at >= since
            ).count()
            priority_counts[priority.value] = count

        # Par catégorie
        category_counts = {}
        categories = self.list_categories()
        for cat in categories:
            count = self.db.query(Ticket).filter(
                Ticket.tenant_id == self.tenant_id,
                Ticket.category_id == cat.id,
                Ticket.created_at >= since
            ).count()
            category_counts[cat.name] = count

        # Par source
        source_counts = {}
        for source in TicketSource:
            count = self.db.query(Ticket).filter(
                Ticket.tenant_id == self.tenant_id,
                Ticket.source == source,
                Ticket.created_at >= since
            ).count()
            source_counts[source.value] = count

        # Tickets récents
        recent_tickets, _ = self.list_tickets(limit=10)

        return HelpdeskDashboard(
            ticket_stats=ticket_stats,
            agent_stats=agent_stats,
            tickets_by_priority=priority_counts,
            tickets_by_category=category_counts,
            tickets_by_source=source_counts,
            recent_tickets=recent_tickets,
            sla_performance={
                "first_response": ticket_stats.first_response_sla_met,
                "resolution": ticket_stats.resolution_sla_met
            }
        )
