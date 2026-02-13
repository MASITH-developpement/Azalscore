"""
Fixtures pour les tests du module Helpdesk - CORE SaaS v2

Hérite des fixtures globales de app/conftest.py.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from app.core.saas_context import SaaSContext
from app.modules.helpdesk.models import (
    AgentStatus,
    TicketPriority,
    TicketStatus,
    TicketSource,
)


# ============================================================================
# FIXTURES HÉRITÉES DU CONFTEST GLOBAL
# ============================================================================
# Les fixtures suivantes sont héritées de app/conftest.py:
# - tenant_id, user_id, user_uuid
# - db_session, test_db_session
# - test_client (avec headers auto-injectés)
# - mock_auth_global (autouse=True)
# - saas_context


@pytest.fixture
def client(test_client):
    """
    Alias pour test_client (compatibilité avec anciens tests).

    Le test_client du conftest global ajoute déjà les headers requis.
    """
    return test_client


@pytest.fixture
def auth_headers(tenant_id):
    """Headers d'authentification avec tenant ID."""
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": tenant_id
    }


@pytest.fixture
def mock_context(saas_context):
    """
    Mock SaaSContext pour les tests (alias pour compatibilité).

    Utilise le saas_context du conftest global.
    """
    return saas_context


# ============================================================================
# FIXTURES DATA - CATEGORIES
# ============================================================================

@pytest.fixture
def category_data():
    """Données pour créer une catégorie."""
    return {
        "name": "Technical Support",
        "slug": "technical-support",
        "description": "Issues techniques",
        "is_active": True,
        "is_public": True,
        "sort_order": 1,
        "default_priority": TicketPriority.MEDIUM,
        "auto_assign": True,
    }


@pytest.fixture
def category_entity():
    """Entité catégorie complète."""
    category = MagicMock()
    category.id = 1
    category.tenant_id = "test-tenant-123"
    category.name = "Technical Support"
    category.slug = "technical-support"
    category.description = "Issues techniques"
    category.is_active = True
    category.is_public = True
    category.sort_order = 1
    category.parent_id = None
    category.default_priority = TicketPriority.MEDIUM
    category.default_team_id = None
    category.sla_id = None
    category.auto_assign = True
    category.created_at = datetime.utcnow()
    category.updated_at = datetime.utcnow()
    return category


# ============================================================================
# FIXTURES DATA - TEAMS
# ============================================================================

@pytest.fixture
def team_data():
    """Données pour créer une équipe."""
    return {
        "name": "Support Team",
        "description": "Équipe de support principal",
        "email": "support@example.com",
        "is_active": True,
        "auto_assign_method": "round_robin",
    }


@pytest.fixture
def team_entity():
    """Entité équipe complète."""
    team = MagicMock()
    team.id = 1
    team.tenant_id = "test-tenant-123"
    team.name = "Support Team"
    team.description = "Équipe de support principal"
    team.email = "support@example.com"
    team.is_active = True
    team.auto_assign_method = "round_robin"
    team.default_sla_id = None
    team.created_at = datetime.utcnow()
    team.updated_at = datetime.utcnow()
    return team


# ============================================================================
# FIXTURES DATA - AGENTS
# ============================================================================

@pytest.fixture
def agent_data():
    """Données pour créer un agent."""
    return {
        "user_id": 123,
        "team_id": 1,
        "display_name": "John Doe",
        "email": "john@example.com",
        "is_active": True,
        "status": AgentStatus.AVAILABLE,
    }


@pytest.fixture
def agent_entity():
    """Entité agent complète."""
    agent = MagicMock()
    agent.id = 1
    agent.tenant_id = "test-tenant-123"
    agent.user_id = 123
    agent.team_id = 1
    agent.display_name = "John Doe"
    agent.email = "john@example.com"
    agent.is_active = True
    agent.status = AgentStatus.AVAILABLE
    agent.tickets_assigned = 5
    agent.tickets_resolved = 3
    agent.avg_resolution_time = Decimal("120.50")
    agent.satisfaction_score = Decimal("4.5")
    agent.last_seen = datetime.utcnow()
    agent.created_at = datetime.utcnow()
    agent.updated_at = datetime.utcnow()
    return agent


# ============================================================================
# FIXTURES DATA - SLA
# ============================================================================

@pytest.fixture
def sla_data():
    """Données pour créer un SLA."""
    return {
        "name": "Standard SLA",
        "description": "SLA standard",
        "is_active": True,
        "is_default": True,
        "first_response_critical": 30,
        "first_response_urgent": 60,
        "first_response_high": 120,
        "first_response_medium": 240,
        "first_response_low": 480,
        "resolution_critical": 120,
        "resolution_urgent": 240,
        "resolution_high": 480,
        "resolution_medium": 1440,
        "resolution_low": 2880,
    }


@pytest.fixture
def sla_entity():
    """Entité SLA complète."""
    sla = MagicMock()
    sla.id = 1
    sla.tenant_id = "test-tenant-123"
    sla.name = "Standard SLA"
    sla.description = "SLA standard"
    sla.is_active = True
    sla.is_default = True
    sla.first_response_critical = 30
    sla.first_response_urgent = 60
    sla.first_response_high = 120
    sla.first_response_medium = 240
    sla.first_response_low = 480
    sla.resolution_critical = 120
    sla.resolution_urgent = 240
    sla.resolution_high = 480
    sla.resolution_medium = 1440
    sla.resolution_low = 2880
    sla.created_at = datetime.utcnow()
    sla.updated_at = datetime.utcnow()
    return sla


# ============================================================================
# FIXTURES DATA - TICKETS
# ============================================================================

@pytest.fixture
def ticket_data():
    """Données pour créer un ticket."""
    return {
        "subject": "Cannot login to application",
        "description": "I get an error when trying to login",
        "priority": TicketPriority.HIGH,
        "source": TicketSource.EMAIL,
        "category_id": 1,
        "requester_name": "Jane Smith",
        "requester_email": "jane@customer.com",
        "requester_phone": "+1234567890",
    }


@pytest.fixture
def ticket_entity():
    """Entité ticket complète."""
    ticket = MagicMock()
    ticket.id = 1
    ticket.tenant_id = "test-tenant-123"
    ticket.ticket_number = "TK-202601-ABC123"
    ticket.subject = "Cannot login to application"
    ticket.description = "I get an error when trying to login"
    ticket.status = TicketStatus.NEW
    ticket.priority = TicketPriority.HIGH
    ticket.source = TicketSource.EMAIL
    ticket.category_id = 1
    ticket.team_id = 1
    ticket.sla_id = 1
    ticket.assigned_to_id = 1
    ticket.requester_id = None
    ticket.requester_name = "Jane Smith"
    ticket.requester_email = "jane@customer.com"
    ticket.requester_phone = "+1234567890"
    ticket.company_id = None
    ticket.first_response_due = datetime.utcnow() + timedelta(hours=2)
    ticket.resolution_due = datetime.utcnow() + timedelta(hours=8)
    ticket.first_responded_at = None
    ticket.resolved_at = None
    ticket.closed_at = None
    ticket.sla_breached = False
    ticket.satisfaction_rating = None
    ticket.reply_count = 0
    ticket.internal_note_count = 0
    ticket.tags = ["login", "error"]
    ticket.custom_fields = {}
    ticket.merged_into_id = None
    ticket.created_at = datetime.utcnow()
    ticket.updated_at = datetime.utcnow()
    return ticket


# ============================================================================
# FIXTURES DATA - REPLIES
# ============================================================================

@pytest.fixture
def reply_data():
    """Données pour créer une réponse."""
    return {
        "body": "Thank you for contacting us. We are looking into your issue.",
        "body_html": "<p>Thank you for contacting us. We are looking into your issue.</p>",
        "is_internal": False,
        "cc_emails": [],
        "bcc_emails": [],
    }


@pytest.fixture
def reply_entity():
    """Entité réponse complète."""
    reply = MagicMock()
    reply.id = 1
    reply.tenant_id = "test-tenant-123"
    reply.ticket_id = 1
    reply.body = "Thank you for contacting us. We are looking into your issue."
    reply.body_html = "<p>Thank you for contacting us. We are looking into your issue.</p>"
    reply.is_internal = False
    reply.is_first_response = True
    reply.author_type = "agent"
    reply.author_id = 1
    reply.author_name = "John Doe"
    reply.author_email = "john@example.com"
    reply.cc_emails = []
    reply.bcc_emails = []
    reply.created_at = datetime.utcnow()
    return reply


# ============================================================================
# FIXTURES DATA - ATTACHMENTS
# ============================================================================

@pytest.fixture
def attachment_data():
    """Données pour créer une pièce jointe."""
    return {
        "filename": "screenshot.png",
        "file_path": "/uploads/tickets/screenshot.png",
        "file_url": "https://cdn.example.com/screenshot.png",
        "file_size": 102400,
        "mime_type": "image/png",
        "reply_id": None,
    }


@pytest.fixture
def attachment_entity():
    """Entité pièce jointe complète."""
    attachment = MagicMock()
    attachment.id = 1
    attachment.tenant_id = "test-tenant-123"
    attachment.ticket_id = 1
    attachment.reply_id = None
    attachment.filename = "screenshot.png"
    attachment.file_path = "/uploads/tickets/screenshot.png"
    attachment.file_url = "https://cdn.example.com/screenshot.png"
    attachment.file_size = 102400
    attachment.mime_type = "image/png"
    attachment.uploaded_by_id = 1
    attachment.created_at = datetime.utcnow()
    return attachment


# ============================================================================
# FIXTURES DATA - CANNED RESPONSES
# ============================================================================

@pytest.fixture
def canned_response_data():
    """Données pour créer une réponse pré-enregistrée."""
    return {
        "title": "Welcome Response",
        "shortcut": "welcome",
        "body": "Thank you for contacting us!",
        "body_html": "<p>Thank you for contacting us!</p>",
        "category": "greetings",
        "scope": "global",
        "is_active": True,
    }


@pytest.fixture
def canned_response_entity():
    """Entité réponse pré-enregistrée complète."""
    response = MagicMock()
    response.id = 1
    response.tenant_id = "test-tenant-123"
    response.title = "Welcome Response"
    response.shortcut = "welcome"
    response.body = "Thank you for contacting us!"
    response.body_html = "<p>Thank you for contacting us!</p>"
    response.category = "greetings"
    response.scope = "global"
    response.team_id = None
    response.agent_id = None
    response.usage_count = 10
    response.is_active = True
    response.created_at = datetime.utcnow()
    response.updated_at = datetime.utcnow()
    return response


# ============================================================================
# FIXTURES DATA - KNOWLEDGE BASE
# ============================================================================

@pytest.fixture
def kb_category_data():
    """Données pour créer une catégorie KB."""
    return {
        "name": "Getting Started",
        "slug": "getting-started",
        "description": "Articles pour démarrer",
        "is_active": True,
        "is_public": True,
        "sort_order": 1,
    }


@pytest.fixture
def kb_category_entity():
    """Entité catégorie KB complète."""
    category = MagicMock()
    category.id = 1
    category.tenant_id = "test-tenant-123"
    category.name = "Getting Started"
    category.slug = "getting-started"
    category.description = "Articles pour démarrer"
    category.is_active = True
    category.is_public = True
    category.parent_id = None
    category.sort_order = 1
    category.icon = "book"
    category.created_at = datetime.utcnow()
    category.updated_at = datetime.utcnow()
    return category


@pytest.fixture
def kb_article_data():
    """Données pour créer un article KB."""
    return {
        "title": "How to reset your password",
        "slug": "how-to-reset-password",
        "body": "Follow these steps to reset your password...",
        "body_html": "<p>Follow these steps to reset your password...</p>",
        "category_id": 1,
        "status": "published",
        "is_public": True,
        "is_featured": False,
        "tags": ["password", "security"],
    }


@pytest.fixture
def kb_article_entity():
    """Entité article KB complète."""
    article = MagicMock()
    article.id = 1
    article.tenant_id = "test-tenant-123"
    article.category_id = 1
    article.title = "How to reset your password"
    article.slug = "how-to-reset-password"
    article.body = "Follow these steps to reset your password..."
    article.body_html = "<p>Follow these steps to reset your password...</p>"
    article.status = "published"
    article.is_public = True
    article.is_featured = False
    article.author_id = 1
    article.author_name = "John Doe"
    article.view_count = 150
    article.helpful_count = 45
    article.not_helpful_count = 5
    article.tags = ["password", "security"]
    article.published_at = datetime.utcnow()
    article.created_at = datetime.utcnow()
    article.updated_at = datetime.utcnow()
    return article


# ============================================================================
# FIXTURES DATA - SATISFACTION
# ============================================================================

@pytest.fixture
def satisfaction_data():
    """Données pour créer une enquête de satisfaction."""
    return {
        "ticket_id": 1,
        "rating": 5,
        "feedback": "Excellent support!",
        "customer_email": "jane@customer.com",
    }


@pytest.fixture
def satisfaction_entity():
    """Entité enquête de satisfaction complète."""
    survey = MagicMock()
    survey.id = 1
    survey.tenant_id = "test-tenant-123"
    survey.ticket_id = 1
    survey.rating = 5
    survey.feedback = "Excellent support!"
    survey.customer_id = None
    survey.customer_email = "jane@customer.com"
    survey.agent_id = 1
    survey.created_at = datetime.utcnow()
    return survey


# ============================================================================
# FIXTURES DATA - AUTOMATIONS
# ============================================================================

@pytest.fixture
def automation_data():
    """Données pour créer une automatisation."""
    return {
        "name": "Auto-close resolved tickets",
        "description": "Close tickets after 7 days in resolved status",
        "trigger_event": "ticket_resolved",
        "conditions": {"days_in_resolved": 7},
        "actions": {"change_status": "closed"},
        "is_active": True,
        "priority": 10,
    }


@pytest.fixture
def automation_entity():
    """Entité automatisation complète."""
    automation = MagicMock()
    automation.id = 1
    automation.tenant_id = "test-tenant-123"
    automation.name = "Auto-close resolved tickets"
    automation.description = "Close tickets after 7 days in resolved status"
    automation.trigger_event = "ticket_resolved"
    automation.conditions = {"days_in_resolved": 7}
    automation.actions = {"change_status": "closed"}
    automation.is_active = True
    automation.priority = 10
    automation.execution_count = 42
    automation.last_executed_at = datetime.utcnow()
    automation.created_at = datetime.utcnow()
    automation.updated_at = datetime.utcnow()
    return automation


# ============================================================================
# FIXTURES DATA - STATS
# ============================================================================

@pytest.fixture
def ticket_stats_entity():
    """Entité statistiques de tickets complète."""
    from app.modules.helpdesk.schemas import TicketStats

    return TicketStats(
        total=100,
        new=15,
        open=35,
        pending=10,
        on_hold=5,
        resolved=25,
        closed=10,
        overdue=8,
        avg_resolution_time=125.5,
        first_response_sla_met=92.5,
        resolution_sla_met=88.3
    )


@pytest.fixture
def agent_stats_entity():
    """Entité statistiques d'agent complète."""
    from app.modules.helpdesk.schemas import AgentStats

    return AgentStats(
        agent_id=1,
        agent_name="John Doe",
        tickets_assigned=50,
        tickets_resolved=45,
        avg_resolution_time=120.5,
        satisfaction_score=4.5,
        response_rate=90.0
    )


@pytest.fixture
def dashboard_entity(ticket_stats_entity, agent_stats_entity, ticket_entity):
    """Entité dashboard complète."""
    from app.modules.helpdesk.schemas import HelpdeskDashboard

    return HelpdeskDashboard(
        ticket_stats=ticket_stats_entity,
        agent_stats=[agent_stats_entity],
        tickets_by_priority={
            "low": 10,
            "medium": 40,
            "high": 30,
            "urgent": 15,
            "critical": 5
        },
        tickets_by_category={
            "Technical Support": 60,
            "Billing": 20,
            "General": 20
        },
        tickets_by_source={
            "email": 50,
            "web": 30,
            "phone": 15,
            "chat": 5
        },
        recent_tickets=[ticket_entity] * 10,
        sla_performance={
            "first_response": 92.5,
            "resolution": 88.3
        }
    )


# ============================================================================
# HELPER ASSERTIONS
# ============================================================================

def assert_ticket_response(ticket, expected_subject=None):
    """Helper pour vérifier une réponse ticket."""
    assert ticket is not None
    assert hasattr(ticket, "id")
    assert hasattr(ticket, "ticket_number")
    assert hasattr(ticket, "status")
    assert hasattr(ticket, "priority")
    if expected_subject:
        assert ticket.subject == expected_subject


def assert_category_response(category, expected_name=None):
    """Helper pour vérifier une réponse catégorie."""
    assert category is not None
    assert hasattr(category, "id")
    assert hasattr(category, "name")
    assert hasattr(category, "slug")
    if expected_name:
        assert category.name == expected_name


def assert_agent_response(agent, expected_name=None):
    """Helper pour vérifier une réponse agent."""
    assert agent is not None
    assert hasattr(agent, "id")
    assert hasattr(agent, "display_name")
    assert hasattr(agent, "status")
    if expected_name:
        assert agent.display_name == expected_name
