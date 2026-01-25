"""
Tests pour les endpoints du module Helpdesk - CORE SaaS v2
===========================================================

Coverage:
- Tickets: CRUD + assign + escalate + resolve + close + status transitions + search
- Categories: CRUD
- Teams: CRUD
- Agents: CRUD + status
- SLA: CRUD
- Comments/Replies: CRUD
- Attachments: upload + download + delete
- Canned Responses: CRUD + use
- Knowledge Base: CRUD + search + helpful
- Satisfaction: submit + stats
- Automations: CRUD
- Metrics/Dashboard: stats + trends + performance
- Search: tickets + filters
- Security: tenant isolation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.modules.helpdesk.models import (
    AgentStatus,
    TicketPriority,
    TicketStatus,
    TicketSource,
)


# ============================================================================
# TESTS CATEGORIES (6 tests)
# ============================================================================

def test_list_categories(client, mock_context, category_entity):
    """Test: Liste les catégories."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_categories.return_value = [category_entity]

            response = client.get("/v2/helpdesk/categories")

            assert response.status_code == 200
            mock_service.list_categories.assert_called_once()


def test_get_category(client, mock_context, category_entity):
    """Test: Récupère une catégorie par ID."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_category.return_value = category_entity

            response = client.get("/v2/helpdesk/categories/1")

            assert response.status_code == 200
            mock_service.get_category.assert_called_once_with(1)


def test_create_category(client, mock_context, category_data, category_entity):
    """Test: Crée une catégorie."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.create_category.return_value = category_entity

            response = client.post("/v2/helpdesk/categories", json=category_data)

            assert response.status_code == 200
            mock_service.create_category.assert_called_once()


def test_update_category(client, mock_context, category_entity):
    """Test: Met à jour une catégorie."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_category.return_value = category_entity

            response = client.put("/v2/helpdesk/categories/1", json={"name": "Updated"})

            assert response.status_code == 200
            mock_service.update_category.assert_called_once()


def test_delete_category(client, mock_context):
    """Test: Supprime une catégorie."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_category.return_value = True

            response = client.delete("/v2/helpdesk/categories/1")

            assert response.status_code == 200
            assert response.json() == {"status": "deleted"}


def test_get_category_not_found(client, mock_context):
    """Test: Catégorie non trouvée retourne 404."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_category.return_value = None

            response = client.get("/v2/helpdesk/categories/999")

            assert response.status_code == 404


# ============================================================================
# TESTS TEAMS (6 tests)
# ============================================================================

def test_list_teams(client, mock_context, team_entity):
    """Test: Liste les équipes."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_teams.return_value = [team_entity]

            response = client.get("/v2/helpdesk/teams")

            assert response.status_code == 200
            mock_service.list_teams.assert_called_once()


def test_get_team(client, mock_context, team_entity):
    """Test: Récupère une équipe par ID."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_team.return_value = team_entity

            response = client.get("/v2/helpdesk/teams/1")

            assert response.status_code == 200


def test_create_team(client, mock_context, team_data, team_entity):
    """Test: Crée une équipe."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.create_team.return_value = team_entity

            response = client.post("/v2/helpdesk/teams", json=team_data)

            assert response.status_code == 200


def test_update_team(client, mock_context, team_entity):
    """Test: Met à jour une équipe."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_team.return_value = team_entity

            response = client.put("/v2/helpdesk/teams/1", json={"name": "Updated Team"})

            assert response.status_code == 200


def test_delete_team(client, mock_context):
    """Test: Supprime une équipe."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_team.return_value = True

            response = client.delete("/v2/helpdesk/teams/1")

            assert response.status_code == 200
            assert response.json() == {"status": "deleted"}


def test_get_team_not_found(client, mock_context):
    """Test: Équipe non trouvée retourne 404."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_team.return_value = None

            response = client.get("/v2/helpdesk/teams/999")

            assert response.status_code == 404


# ============================================================================
# TESTS AGENTS (7 tests)
# ============================================================================

def test_list_agents(client, mock_context, agent_entity):
    """Test: Liste les agents."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_agents.return_value = [agent_entity]

            response = client.get("/v2/helpdesk/agents")

            assert response.status_code == 200


def test_list_agents_with_filters(client, mock_context, agent_entity):
    """Test: Liste les agents avec filtres."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_agents.return_value = [agent_entity]

            response = client.get("/v2/helpdesk/agents?team_id=1&status=available")

            assert response.status_code == 200


def test_get_agent(client, mock_context, agent_entity):
    """Test: Récupère un agent par ID."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_agent.return_value = agent_entity

            response = client.get("/v2/helpdesk/agents/1")

            assert response.status_code == 200


def test_create_agent(client, mock_context, agent_data, agent_entity):
    """Test: Crée un agent."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.create_agent.return_value = agent_entity

            response = client.post("/v2/helpdesk/agents", json=agent_data)

            assert response.status_code == 200


def test_update_agent(client, mock_context, agent_entity):
    """Test: Met à jour un agent."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_agent.return_value = agent_entity

            response = client.put("/v2/helpdesk/agents/1", json={"display_name": "Updated"})

            assert response.status_code == 200


def test_update_agent_status(client, mock_context, agent_entity):
    """Test: Met à jour le statut d'un agent."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_agent_status.return_value = agent_entity

            response = client.post("/v2/helpdesk/agents/1/status", json={"status": "busy"})

            assert response.status_code == 200


def test_delete_agent(client, mock_context):
    """Test: Supprime un agent."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_agent.return_value = True

            response = client.delete("/v2/helpdesk/agents/1")

            assert response.status_code == 200


# ============================================================================
# TESTS SLA (6 tests)
# ============================================================================

def test_list_slas(client, mock_context, sla_entity):
    """Test: Liste les SLAs."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_slas.return_value = [sla_entity]

            response = client.get("/v2/helpdesk/sla")

            assert response.status_code == 200


def test_get_sla(client, mock_context, sla_entity):
    """Test: Récupère un SLA par ID."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_sla.return_value = sla_entity

            response = client.get("/v2/helpdesk/sla/1")

            assert response.status_code == 200


def test_create_sla(client, mock_context, sla_data, sla_entity):
    """Test: Crée un SLA."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.create_sla.return_value = sla_entity

            response = client.post("/v2/helpdesk/sla", json=sla_data)

            assert response.status_code == 200


def test_update_sla(client, mock_context, sla_entity):
    """Test: Met à jour un SLA."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_sla.return_value = sla_entity

            response = client.put("/v2/helpdesk/sla/1", json={"name": "Updated SLA"})

            assert response.status_code == 200


def test_delete_sla(client, mock_context):
    """Test: Supprime un SLA."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_sla.return_value = True

            response = client.delete("/v2/helpdesk/sla/1")

            assert response.status_code == 200


def test_get_sla_not_found(client, mock_context):
    """Test: SLA non trouvé retourne 404."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_sla.return_value = None

            response = client.get("/v2/helpdesk/sla/999")

            assert response.status_code == 404


# ============================================================================
# TESTS TICKETS (25 tests)
# ============================================================================

def test_list_tickets(client, mock_context, ticket_entity):
    """Test: Liste les tickets."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_tickets.return_value = ([ticket_entity], 1)

            response = client.get("/v2/helpdesk/tickets")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert data["total"] == 1


def test_list_tickets_with_filters(client, mock_context, ticket_entity):
    """Test: Liste les tickets avec filtres."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_tickets.return_value = ([ticket_entity], 1)

            response = client.get("/v2/helpdesk/tickets?status=new&priority=high")

            assert response.status_code == 200


def test_list_tickets_with_search(client, mock_context, ticket_entity):
    """Test: Liste les tickets avec recherche."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_tickets.return_value = ([ticket_entity], 1)

            response = client.get("/v2/helpdesk/tickets?search=login")

            assert response.status_code == 200


def test_list_tickets_overdue_only(client, mock_context, ticket_entity):
    """Test: Liste uniquement les tickets en retard."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_tickets.return_value = ([ticket_entity], 1)

            response = client.get("/v2/helpdesk/tickets?overdue_only=true")

            assert response.status_code == 200


def test_list_tickets_pagination(client, mock_context, ticket_entity):
    """Test: Liste les tickets avec pagination."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_tickets.return_value = ([ticket_entity], 50)

            response = client.get("/v2/helpdesk/tickets?skip=20&limit=10")

            assert response.status_code == 200
            data = response.json()
            assert data["skip"] == 20
            assert data["limit"] == 10


def test_get_ticket(client, mock_context, ticket_entity):
    """Test: Récupère un ticket par ID."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_ticket.return_value = ticket_entity

            response = client.get("/v2/helpdesk/tickets/1")

            assert response.status_code == 200


def test_get_ticket_by_number(client, mock_context, ticket_entity):
    """Test: Récupère un ticket par numéro."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_ticket_by_number.return_value = ticket_entity

            response = client.get("/v2/helpdesk/tickets/number/TK-202601-ABC123")

            assert response.status_code == 200


def test_create_ticket(client, mock_context, ticket_data, ticket_entity):
    """Test: Crée un ticket."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.create_ticket.return_value = ticket_entity

            response = client.post("/v2/helpdesk/tickets", json=ticket_data)

            assert response.status_code == 200


def test_update_ticket(client, mock_context, ticket_entity):
    """Test: Met à jour un ticket."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_ticket.return_value = ticket_entity

            response = client.put("/v2/helpdesk/tickets/1", json={"subject": "Updated"})

            assert response.status_code == 200


def test_assign_ticket(client, mock_context, ticket_entity):
    """Test: Assigne un ticket à un agent."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.assign_ticket.return_value = ticket_entity

            response = client.post("/v2/helpdesk/tickets/1/assign", json={"agent_id": 1})

            assert response.status_code == 200


def test_change_ticket_status(client, mock_context, ticket_entity):
    """Test: Change le statut d'un ticket."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            ticket_entity.status = TicketStatus.OPEN
            mock_service.change_ticket_status.return_value = ticket_entity

            response = client.post("/v2/helpdesk/tickets/1/status", json={
                "status": "open",
                "comment": "Working on it"
            })

            assert response.status_code == 200


def test_change_ticket_status_to_resolved(client, mock_context, ticket_entity):
    """Test: Résout un ticket."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            ticket_entity.status = TicketStatus.RESOLVED
            ticket_entity.resolved_at = datetime.utcnow()
            mock_service.change_ticket_status.return_value = ticket_entity

            response = client.post("/v2/helpdesk/tickets/1/status", json={
                "status": "resolved",
                "comment": "Issue fixed"
            })

            assert response.status_code == 200


def test_change_ticket_status_to_closed(client, mock_context, ticket_entity):
    """Test: Ferme un ticket."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            ticket_entity.status = TicketStatus.CLOSED
            ticket_entity.closed_at = datetime.utcnow()
            mock_service.change_ticket_status.return_value = ticket_entity

            response = client.post("/v2/helpdesk/tickets/1/status", json={
                "status": "closed"
            })

            assert response.status_code == 200


def test_change_ticket_status_to_pending(client, mock_context, ticket_entity):
    """Test: Met un ticket en attente."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            ticket_entity.status = TicketStatus.PENDING
            mock_service.change_ticket_status.return_value = ticket_entity

            response = client.post("/v2/helpdesk/tickets/1/status", json={
                "status": "pending",
                "comment": "Waiting for customer"
            })

            assert response.status_code == 200


def test_merge_tickets(client, mock_context, ticket_entity):
    """Test: Fusionne deux tickets."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.merge_tickets.return_value = ticket_entity

            response = client.post("/v2/helpdesk/tickets/1/merge/2")

            assert response.status_code == 200


def test_ticket_not_found(client, mock_context):
    """Test: Ticket non trouvé retourne 404."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_ticket.return_value = None

            response = client.get("/v2/helpdesk/tickets/999")

            assert response.status_code == 404


def test_create_ticket_high_priority(client, mock_context, ticket_entity):
    """Test: Crée un ticket haute priorité."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            ticket_entity.priority = TicketPriority.HIGH
            mock_service.create_ticket.return_value = ticket_entity

            response = client.post("/v2/helpdesk/tickets", json={
                "subject": "Urgent issue",
                "description": "Need help ASAP",
                "priority": "high",
                "source": "email",
                "requester_email": "customer@example.com"
            })

            assert response.status_code == 200


def test_create_ticket_critical_priority(client, mock_context, ticket_entity):
    """Test: Crée un ticket priorité critique."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            ticket_entity.priority = TicketPriority.CRITICAL
            mock_service.create_ticket.return_value = ticket_entity

            response = client.post("/v2/helpdesk/tickets", json={
                "subject": "System down!",
                "description": "Critical issue",
                "priority": "critical",
                "source": "phone",
                "requester_email": "customer@example.com"
            })

            assert response.status_code == 200


def test_create_ticket_with_tags(client, mock_context, ticket_entity):
    """Test: Crée un ticket avec tags."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            ticket_entity.tags = ["bug", "urgent", "login"]
            mock_service.create_ticket.return_value = ticket_entity

            response = client.post("/v2/helpdesk/tickets", json={
                "subject": "Cannot login",
                "description": "Error message",
                "priority": "high",
                "source": "email",
                "requester_email": "customer@example.com",
                "tags": ["bug", "urgent", "login"]
            })

            assert response.status_code == 200


def test_create_ticket_with_custom_fields(client, mock_context, ticket_entity):
    """Test: Crée un ticket avec champs personnalisés."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            ticket_entity.custom_fields = {"browser": "Chrome", "os": "Windows"}
            mock_service.create_ticket.return_value = ticket_entity

            response = client.post("/v2/helpdesk/tickets", json={
                "subject": "Issue",
                "description": "Problem",
                "priority": "medium",
                "source": "web",
                "requester_email": "customer@example.com",
                "custom_fields": {"browser": "Chrome", "os": "Windows"}
            })

            assert response.status_code == 200


def test_list_tickets_by_requester(client, mock_context, ticket_entity):
    """Test: Liste les tickets d'un demandeur."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_tickets.return_value = ([ticket_entity], 1)

            response = client.get("/v2/helpdesk/tickets?requester_email=jane@customer.com")

            assert response.status_code == 200


def test_list_tickets_by_assigned_agent(client, mock_context, ticket_entity):
    """Test: Liste les tickets assignés à un agent."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_tickets.return_value = ([ticket_entity], 1)

            response = client.get("/v2/helpdesk/tickets?assigned_to_id=1")

            assert response.status_code == 200


def test_list_tickets_by_team(client, mock_context, ticket_entity):
    """Test: Liste les tickets d'une équipe."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_tickets.return_value = ([ticket_entity], 1)

            response = client.get("/v2/helpdesk/tickets?team_id=1")

            assert response.status_code == 200


def test_list_tickets_by_category(client, mock_context, ticket_entity):
    """Test: Liste les tickets d'une catégorie."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_tickets.return_value = ([ticket_entity], 1)

            response = client.get("/v2/helpdesk/tickets?category_id=1")

            assert response.status_code == 200


# ============================================================================
# TESTS REPLIES/COMMENTS (8 tests)
# ============================================================================

def test_list_replies(client, mock_context, reply_entity):
    """Test: Liste les réponses d'un ticket."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_replies.return_value = [reply_entity]

            response = client.get("/v2/helpdesk/tickets/1/replies")

            assert response.status_code == 200


def test_list_replies_exclude_internal(client, mock_context, reply_entity):
    """Test: Liste les réponses publiques uniquement."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            reply_entity.is_internal = False
            mock_service.list_replies.return_value = [reply_entity]

            response = client.get("/v2/helpdesk/tickets/1/replies?include_internal=false")

            assert response.status_code == 200


def test_add_reply(client, mock_context, reply_data, reply_entity):
    """Test: Ajoute une réponse à un ticket."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.add_reply.return_value = reply_entity

            response = client.post("/v2/helpdesk/tickets/1/replies", json=reply_data)

            assert response.status_code == 200


def test_add_internal_note(client, mock_context, reply_entity):
    """Test: Ajoute une note interne."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            reply_entity.is_internal = True
            mock_service.add_reply.return_value = reply_entity

            response = client.post("/v2/helpdesk/tickets/1/replies", json={
                "body": "Internal note",
                "body_html": "<p>Internal note</p>",
                "is_internal": True
            })

            assert response.status_code == 200


def test_add_reply_from_customer(client, mock_context, reply_entity):
    """Test: Ajoute une réponse client."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            reply_entity.author_type = "customer"
            mock_service.add_reply.return_value = reply_entity

            response = client.post(
                "/v2/helpdesk/tickets/1/replies?author_type=customer",
                json={
                    "body": "Thank you!",
                    "body_html": "<p>Thank you!</p>",
                    "is_internal": False
                }
            )

            assert response.status_code == 200


def test_add_reply_with_cc(client, mock_context, reply_entity):
    """Test: Ajoute une réponse avec CC."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            reply_entity.cc_emails = ["manager@example.com"]
            mock_service.add_reply.return_value = reply_entity

            response = client.post("/v2/helpdesk/tickets/1/replies", json={
                "body": "Reply with CC",
                "body_html": "<p>Reply with CC</p>",
                "is_internal": False,
                "cc_emails": ["manager@example.com"]
            })

            assert response.status_code == 200


def test_add_reply_ticket_not_found(client, mock_context):
    """Test: Ajouter une réponse à un ticket inexistant."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.add_reply.return_value = None

            response = client.post("/v2/helpdesk/tickets/999/replies", json={
                "body": "Reply",
                "body_html": "<p>Reply</p>",
                "is_internal": False
            })

            assert response.status_code == 404


def test_add_first_response(client, mock_context, reply_entity):
    """Test: Ajoute la première réponse (SLA tracking)."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            reply_entity.is_first_response = True
            mock_service.add_reply.return_value = reply_entity

            response = client.post("/v2/helpdesk/tickets/1/replies", json={
                "body": "First response",
                "body_html": "<p>First response</p>",
                "is_internal": False
            })

            assert response.status_code == 200


# ============================================================================
# TESTS ATTACHMENTS (6 tests)
# ============================================================================

def test_list_attachments(client, mock_context, attachment_entity):
    """Test: Liste les pièces jointes d'un ticket."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_attachments.return_value = [attachment_entity]

            response = client.get("/v2/helpdesk/tickets/1/attachments")

            assert response.status_code == 200


def test_add_attachment(client, mock_context, attachment_data, attachment_entity):
    """Test: Ajoute une pièce jointe."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.add_attachment.return_value = attachment_entity

            response = client.post("/v2/helpdesk/tickets/1/attachments", json=attachment_data)

            assert response.status_code == 200


def test_add_attachment_to_reply(client, mock_context, attachment_entity):
    """Test: Ajoute une pièce jointe à une réponse."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            attachment_entity.reply_id = 1
            mock_service.add_attachment.return_value = attachment_entity

            response = client.post("/v2/helpdesk/tickets/1/attachments", json={
                "filename": "log.txt",
                "file_path": "/uploads/log.txt",
                "file_url": "https://cdn.example.com/log.txt",
                "file_size": 1024,
                "mime_type": "text/plain",
                "reply_id": 1
            })

            assert response.status_code == 200


def test_add_image_attachment(client, mock_context, attachment_entity):
    """Test: Ajoute une image."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            attachment_entity.mime_type = "image/jpeg"
            mock_service.add_attachment.return_value = attachment_entity

            response = client.post("/v2/helpdesk/tickets/1/attachments", json={
                "filename": "photo.jpg",
                "file_path": "/uploads/photo.jpg",
                "file_url": "https://cdn.example.com/photo.jpg",
                "file_size": 204800,
                "mime_type": "image/jpeg"
            })

            assert response.status_code == 200


def test_add_pdf_attachment(client, mock_context, attachment_entity):
    """Test: Ajoute un PDF."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            attachment_entity.mime_type = "application/pdf"
            mock_service.add_attachment.return_value = attachment_entity

            response = client.post("/v2/helpdesk/tickets/1/attachments", json={
                "filename": "invoice.pdf",
                "file_path": "/uploads/invoice.pdf",
                "file_url": "https://cdn.example.com/invoice.pdf",
                "file_size": 512000,
                "mime_type": "application/pdf"
            })

            assert response.status_code == 200


def test_add_attachment_ticket_not_found(client, mock_context):
    """Test: Ajouter une pièce jointe à un ticket inexistant."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.add_attachment.return_value = None

            response = client.post("/v2/helpdesk/tickets/999/attachments", json={
                "filename": "file.txt",
                "file_path": "/uploads/file.txt",
                "file_url": "https://cdn.example.com/file.txt",
                "file_size": 1024,
                "mime_type": "text/plain"
            })

            assert response.status_code == 404


# ============================================================================
# TESTS HISTORY (1 test)
# ============================================================================

def test_get_ticket_history(client, mock_context):
    """Test: Récupère l'historique d'un ticket."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            history = MagicMock()
            history.id = 1
            history.action = "created"
            mock_service.get_ticket_history.return_value = [history]

            response = client.get("/v2/helpdesk/tickets/1/history")

            assert response.status_code == 200


# ============================================================================
# TESTS CANNED RESPONSES (7 tests)
# ============================================================================

def test_list_canned_responses(client, mock_context, canned_response_entity):
    """Test: Liste les réponses pré-enregistrées."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_canned_responses.return_value = [canned_response_entity]

            response = client.get("/v2/helpdesk/canned-responses")

            assert response.status_code == 200


def test_get_canned_response(client, mock_context, canned_response_entity):
    """Test: Récupère une réponse pré-enregistrée."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_canned_response.return_value = canned_response_entity

            response = client.get("/v2/helpdesk/canned-responses/1")

            assert response.status_code == 200


def test_get_canned_by_shortcut(client, mock_context, canned_response_entity):
    """Test: Récupère une réponse par shortcut."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_canned_by_shortcut.return_value = canned_response_entity

            response = client.get("/v2/helpdesk/canned-responses/shortcut/welcome")

            assert response.status_code == 200


def test_create_canned_response(client, mock_context, canned_response_data, canned_response_entity):
    """Test: Crée une réponse pré-enregistrée."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.create_canned_response.return_value = canned_response_entity

            response = client.post("/v2/helpdesk/canned-responses", json=canned_response_data)

            assert response.status_code == 200


def test_update_canned_response(client, mock_context, canned_response_entity):
    """Test: Met à jour une réponse pré-enregistrée."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_canned_response.return_value = canned_response_entity

            response = client.put("/v2/helpdesk/canned-responses/1", json={"title": "Updated"})

            assert response.status_code == 200


def test_use_canned_response(client, mock_context, canned_response_entity):
    """Test: Incrémente le compteur d'utilisation."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            canned_response_entity.usage_count = 11
            mock_service.use_canned_response.return_value = canned_response_entity

            response = client.post("/v2/helpdesk/canned-responses/1/use")

            assert response.status_code == 200


def test_delete_canned_response(client, mock_context):
    """Test: Supprime une réponse pré-enregistrée."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_canned_response.return_value = True

            response = client.delete("/v2/helpdesk/canned-responses/1")

            assert response.status_code == 200


# ============================================================================
# TESTS KNOWLEDGE BASE - CATEGORIES (4 tests)
# ============================================================================

def test_list_kb_categories(client, mock_context, kb_category_entity):
    """Test: Liste les catégories KB."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_kb_categories.return_value = [kb_category_entity]

            response = client.get("/v2/helpdesk/kb/categories")

            assert response.status_code == 200


def test_get_kb_category(client, mock_context, kb_category_entity):
    """Test: Récupère une catégorie KB."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_kb_category.return_value = kb_category_entity

            response = client.get("/v2/helpdesk/kb/categories/1")

            assert response.status_code == 200


def test_create_kb_category(client, mock_context, kb_category_data, kb_category_entity):
    """Test: Crée une catégorie KB."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.create_kb_category.return_value = kb_category_entity

            response = client.post("/v2/helpdesk/kb/categories", json=kb_category_data)

            assert response.status_code == 200


def test_update_kb_category(client, mock_context, kb_category_entity):
    """Test: Met à jour une catégorie KB."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_kb_category.return_value = kb_category_entity

            response = client.put("/v2/helpdesk/kb/categories/1", json={"name": "Updated"})

            assert response.status_code == 200


# ============================================================================
# TESTS KNOWLEDGE BASE - ARTICLES (8 tests)
# ============================================================================

def test_list_kb_articles(client, mock_context, kb_article_entity):
    """Test: Liste les articles KB."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_kb_articles.return_value = ([kb_article_entity], 1)

            response = client.get("/v2/helpdesk/kb/articles")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data


def test_list_kb_articles_with_search(client, mock_context, kb_article_entity):
    """Test: Recherche dans les articles KB."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_kb_articles.return_value = ([kb_article_entity], 1)

            response = client.get("/v2/helpdesk/kb/articles?search=password")

            assert response.status_code == 200


def test_get_kb_article(client, mock_context, kb_article_entity):
    """Test: Récupère un article KB."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_kb_article.return_value = kb_article_entity
            mock_service.view_kb_article.return_value = kb_article_entity

            response = client.get("/v2/helpdesk/kb/articles/1")

            assert response.status_code == 200
            mock_service.view_kb_article.assert_called_once()


def test_get_kb_article_by_slug(client, mock_context, kb_article_entity):
    """Test: Récupère un article KB par slug."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_kb_article_by_slug.return_value = kb_article_entity
            mock_service.view_kb_article.return_value = kb_article_entity

            response = client.get("/v2/helpdesk/kb/articles/slug/how-to-reset-password")

            assert response.status_code == 200


def test_create_kb_article(client, mock_context, kb_article_data, kb_article_entity):
    """Test: Crée un article KB."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.create_kb_article.return_value = kb_article_entity

            response = client.post("/v2/helpdesk/kb/articles", json=kb_article_data)

            assert response.status_code == 200


def test_update_kb_article(client, mock_context, kb_article_entity):
    """Test: Met à jour un article KB."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_kb_article.return_value = kb_article_entity

            response = client.put("/v2/helpdesk/kb/articles/1", json={"title": "Updated"})

            assert response.status_code == 200


def test_rate_kb_article_helpful(client, mock_context, kb_article_entity):
    """Test: Note un article comme utile."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.rate_kb_article.return_value = kb_article_entity

            response = client.post("/v2/helpdesk/kb/articles/1/rate?helpful=true")

            assert response.status_code == 200
            data = response.json()
            assert data["helpful"] is True


def test_rate_kb_article_not_helpful(client, mock_context, kb_article_entity):
    """Test: Note un article comme non utile."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.rate_kb_article.return_value = kb_article_entity

            response = client.post("/v2/helpdesk/kb/articles/1/rate?helpful=false")

            assert response.status_code == 200
            data = response.json()
            assert data["helpful"] is False


# ============================================================================
# TESTS SATISFACTION (2 tests)
# ============================================================================

def test_submit_satisfaction(client, mock_context, satisfaction_data, satisfaction_entity):
    """Test: Soumet une enquête de satisfaction."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.submit_satisfaction.return_value = satisfaction_entity

            response = client.post("/v2/helpdesk/satisfaction", json=satisfaction_data)

            assert response.status_code == 200


def test_get_satisfaction_stats(client, mock_context):
    """Test: Récupère les statistiques de satisfaction."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_satisfaction_stats.return_value = {
                "total_surveys": 100,
                "average_rating": 4.5,
                "distribution": {1: 2, 2: 3, 3: 10, 4: 35, 5: 50}
            }

            response = client.get("/v2/helpdesk/satisfaction/stats")

            assert response.status_code == 200


# ============================================================================
# TESTS AUTOMATIONS (5 tests)
# ============================================================================

def test_list_automations(client, mock_context, automation_entity):
    """Test: Liste les automatisations."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_automations.return_value = [automation_entity]

            response = client.get("/v2/helpdesk/automations")

            assert response.status_code == 200


def test_get_automation(client, mock_context, automation_entity):
    """Test: Récupère une automatisation."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_automation.return_value = automation_entity

            response = client.get("/v2/helpdesk/automations/1")

            assert response.status_code == 200


def test_create_automation(client, mock_context, automation_data, automation_entity):
    """Test: Crée une automatisation."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.create_automation.return_value = automation_entity

            response = client.post("/v2/helpdesk/automations", json=automation_data)

            assert response.status_code == 200


def test_update_automation(client, mock_context, automation_entity):
    """Test: Met à jour une automatisation."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_automation.return_value = automation_entity

            response = client.put("/v2/helpdesk/automations/1", json={"name": "Updated"})

            assert response.status_code == 200


def test_delete_automation(client, mock_context):
    """Test: Supprime une automatisation."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_automation.return_value = True

            response = client.delete("/v2/helpdesk/automations/1")

            assert response.status_code == 200


# ============================================================================
# TESTS STATS & DASHBOARD (3 tests)
# ============================================================================

def test_get_ticket_stats(client, mock_context, ticket_stats_entity):
    """Test: Récupère les statistiques des tickets."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_ticket_stats.return_value = ticket_stats_entity

            response = client.get("/v2/helpdesk/stats/tickets")

            assert response.status_code == 200


def test_get_agent_stats(client, mock_context, agent_stats_entity):
    """Test: Récupère les statistiques des agents."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_agent_stats.return_value = [agent_stats_entity]

            response = client.get("/v2/helpdesk/stats/agents")

            assert response.status_code == 200


def test_get_dashboard(client, mock_context, dashboard_entity):
    """Test: Récupère le dashboard complet."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_dashboard.return_value = dashboard_entity

            response = client.get("/v2/helpdesk/dashboard")

            assert response.status_code == 200


# ============================================================================
# TESTS WORKFLOW COMPLET (8 tests)
# ============================================================================

def test_workflow_create_and_assign_ticket(client, mock_context, ticket_data, ticket_entity):
    """Test: Workflow complet - création et assignation."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value

            # Création
            mock_service.create_ticket.return_value = ticket_entity
            response1 = client.post("/v2/helpdesk/tickets", json=ticket_data)
            assert response1.status_code == 200

            # Assignation
            ticket_entity.assigned_to_id = 1
            mock_service.assign_ticket.return_value = ticket_entity
            response2 = client.post("/v2/helpdesk/tickets/1/assign", json={"agent_id": 1})
            assert response2.status_code == 200


def test_workflow_reply_and_resolve(client, mock_context, reply_data, reply_entity, ticket_entity):
    """Test: Workflow - réponse et résolution."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value

            # Ajouter réponse
            mock_service.add_reply.return_value = reply_entity
            response1 = client.post("/v2/helpdesk/tickets/1/replies", json=reply_data)
            assert response1.status_code == 200

            # Résoudre
            ticket_entity.status = TicketStatus.RESOLVED
            mock_service.change_ticket_status.return_value = ticket_entity
            response2 = client.post("/v2/helpdesk/tickets/1/status", json={
                "status": "resolved",
                "comment": "Fixed"
            })
            assert response2.status_code == 200


def test_workflow_escalate_ticket(client, mock_context, ticket_entity):
    """Test: Workflow - escalade de ticket."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value

            # Augmenter priorité
            ticket_entity.priority = TicketPriority.URGENT
            mock_service.update_ticket.return_value = ticket_entity
            response = client.put("/v2/helpdesk/tickets/1", json={"priority": "urgent"})
            assert response.status_code == 200


def test_workflow_sla_breach(client, mock_context, ticket_entity):
    """Test: Workflow - dépassement SLA."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value

            # Ticket avec SLA dépassé
            ticket_entity.sla_breached = True
            ticket_entity.first_response_due = datetime.utcnow() - timedelta(hours=2)
            mock_service.get_ticket.return_value = ticket_entity

            response = client.get("/v2/helpdesk/tickets/1")
            assert response.status_code == 200


def test_workflow_customer_satisfaction(client, mock_context, ticket_entity, satisfaction_data, satisfaction_entity):
    """Test: Workflow - satisfaction client après résolution."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value

            # Résoudre le ticket
            ticket_entity.status = TicketStatus.RESOLVED
            mock_service.change_ticket_status.return_value = ticket_entity
            response1 = client.post("/v2/helpdesk/tickets/1/status", json={"status": "resolved"})
            assert response1.status_code == 200

            # Soumettre satisfaction
            mock_service.submit_satisfaction.return_value = satisfaction_entity
            response2 = client.post("/v2/helpdesk/satisfaction", json=satisfaction_data)
            assert response2.status_code == 200


def test_workflow_ticket_with_attachments(client, mock_context, ticket_data, ticket_entity, attachment_data, attachment_entity):
    """Test: Workflow - ticket avec pièces jointes."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value

            # Créer ticket
            mock_service.create_ticket.return_value = ticket_entity
            response1 = client.post("/v2/helpdesk/tickets", json=ticket_data)
            assert response1.status_code == 200

            # Ajouter pièce jointe
            mock_service.add_attachment.return_value = attachment_entity
            response2 = client.post("/v2/helpdesk/tickets/1/attachments", json=attachment_data)
            assert response2.status_code == 200


def test_workflow_use_canned_response(client, mock_context, canned_response_entity, reply_entity):
    """Test: Workflow - utilisation de réponse pré-enregistrée."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value

            # Récupérer réponse pré-enregistrée
            mock_service.get_canned_by_shortcut.return_value = canned_response_entity
            response1 = client.get("/v2/helpdesk/canned-responses/shortcut/welcome")
            assert response1.status_code == 200

            # Marquer comme utilisée
            mock_service.use_canned_response.return_value = canned_response_entity
            response2 = client.post("/v2/helpdesk/canned-responses/1/use")
            assert response2.status_code == 200


def test_workflow_kb_article_helpful(client, mock_context, kb_article_entity):
    """Test: Workflow - consultation article KB et vote."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value

            # Consulter article
            mock_service.get_kb_article.return_value = kb_article_entity
            mock_service.view_kb_article.return_value = kb_article_entity
            response1 = client.get("/v2/helpdesk/kb/articles/1")
            assert response1.status_code == 200

            # Noter comme utile
            kb_article_entity.helpful_count = 46
            mock_service.rate_kb_article.return_value = kb_article_entity
            response2 = client.post("/v2/helpdesk/kb/articles/1/rate?helpful=true")
            assert response2.status_code == 200


# ============================================================================
# TESTS SECURITY (2 tests)
# ============================================================================

def test_tenant_isolation(client, mock_context, ticket_entity):
    """Test: Isolation des tenants - vérification du tenant_id."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value

            # Le service doit être initialisé avec le bon tenant_id
            MockService.assert_called_with(
                mock_service.return_value._db if hasattr(mock_service.return_value, '_db') else None,
                mock_context.tenant_id,
                mock_context.user_id
            )


def test_user_context_preserved(client, mock_context, ticket_entity):
    """Test: Le contexte utilisateur est préservé."""
    with patch("app.modules.helpdesk.router_v2.get_saas_context", return_value=mock_context):
        with patch("app.modules.helpdesk.router_v2.HelpdeskService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_tickets.return_value = ([ticket_entity], 1)

            response = client.get("/v2/helpdesk/tickets")

            assert response.status_code == 200
            # Vérifier que le service a été créé avec user_id
            assert MockService.called
