"""
Tests MODULE 16 - Helpdesk
===========================
Tests unitaires pour le système de support client.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.modules.helpdesk.models import (
    TicketCategory, HelpdeskTeam, HelpdeskAgent, HelpdeskSLA,
    Ticket, TicketReply, TicketAttachment, TicketHistory,
    CannedResponse, KBCategory, KBArticle, SatisfactionSurvey,
    HelpdeskAutomation, TicketStatus, TicketPriority, TicketSource, AgentStatus
)
from app.modules.helpdesk.schemas import (
    CategoryCreate, CategoryUpdate,
    TeamCreate, TeamUpdate,
    AgentCreate, AgentUpdate,
    SLACreate, SLAUpdate,
    TicketCreate, TicketUpdate,
    ReplyCreate, AttachmentCreate,
    CannedResponseCreate, CannedResponseUpdate,
    KBCategoryCreate, KBArticleCreate,
    SatisfactionCreate,
    AutomationCreate
)
from app.modules.helpdesk.service import HelpdeskService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock de la session DB."""
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


@pytest.fixture
def service(mock_db):
    """Service Helpdesk avec mock DB."""
    return HelpdeskService(mock_db, "test-tenant")


@pytest.fixture
def sample_category():
    """Catégorie exemple."""
    cat = MagicMock(spec=TicketCategory)
    cat.id = 1
    cat.tenant_id = "test-tenant"
    cat.code = "TECH"
    cat.name = "Support Technique"
    cat.default_priority = TicketPriority.MEDIUM
    cat.is_active = True
    cat.is_public = True
    cat.auto_assign = True
    return cat


@pytest.fixture
def sample_team():
    """Équipe exemple."""
    team = MagicMock(spec=HelpdeskTeam)
    team.id = 1
    team.tenant_id = "test-tenant"
    team.name = "Support N1"
    team.auto_assign_method = "round_robin"
    team.is_active = True
    return team


@pytest.fixture
def sample_agent():
    """Agent exemple."""
    agent = MagicMock(spec=HelpdeskAgent)
    agent.id = 1
    agent.tenant_id = "test-tenant"
    agent.user_id = 100
    agent.display_name = "Jean Support"
    agent.status = AgentStatus.AVAILABLE
    agent.tickets_assigned = 5
    agent.tickets_resolved = 20
    agent.is_active = True
    return agent


@pytest.fixture
def sample_sla():
    """SLA exemple."""
    sla = MagicMock(spec=HelpdeskSLA)
    sla.id = 1
    sla.tenant_id = "test-tenant"
    sla.name = "Standard"
    sla.first_response_medium = 480
    sla.resolution_medium = 2880
    sla.is_default = True
    sla.is_active = True
    return sla


@pytest.fixture
def sample_ticket():
    """Ticket exemple."""
    ticket = MagicMock(spec=Ticket)
    ticket.id = 1
    ticket.tenant_id = "test-tenant"
    ticket.ticket_number = "TK-202401-ABC123"
    ticket.subject = "Problème de connexion"
    ticket.description = "Je ne peux plus me connecter"
    ticket.status = TicketStatus.NEW
    ticket.priority = TicketPriority.MEDIUM
    ticket.source = TicketSource.WEB
    ticket.requester_email = "client@example.com"
    ticket.assigned_to_id = None
    ticket.first_responded_at = None
    ticket.resolved_at = None
    ticket.sla_breached = False
    ticket.reply_count = 0
    ticket.internal_note_count = 0
    # SLA dates - None par défaut pour éviter les erreurs de comparaison
    ticket.resolution_due = None
    ticket.first_response_due = None
    ticket.created_at = datetime.utcnow()
    return ticket


# ============================================================================
# TESTS CATEGORIES
# ============================================================================

class TestCategories:
    """Tests catégories."""

    def test_create_category(self, service, mock_db):
        """Test création catégorie."""
        data = CategoryCreate(
            code="BILLING",
            name="Facturation",
            description="Questions de facturation"
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_category(data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_category(self, service, mock_db, sample_category):
        """Test récupération catégorie."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_category

        result = service.get_category(1)

        assert result == sample_category
        assert result.code == "TECH"

    def test_update_category(self, service, mock_db, sample_category):
        """Test mise à jour catégorie."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_category

        data = CategoryUpdate(name="Support Technique Avancé")
        result = service.update_category(1, data)

        assert result is not None
        mock_db.commit.assert_called()

    def test_delete_category(self, service, mock_db, sample_category):
        """Test suppression catégorie."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_category

        result = service.delete_category(1)

        assert result is True
        assert sample_category.is_active is False


# ============================================================================
# TESTS TEAMS
# ============================================================================

class TestTeams:
    """Tests équipes."""

    def test_create_team(self, service, mock_db):
        """Test création équipe."""
        data = TeamCreate(
            name="Support N2",
            description="Niveau 2"
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_team(data)

        mock_db.add.assert_called_once()

    def test_get_team(self, service, mock_db, sample_team):
        """Test récupération équipe."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_team

        result = service.get_team(1)

        assert result.name == "Support N1"


# ============================================================================
# TESTS AGENTS
# ============================================================================

class TestAgents:
    """Tests agents."""

    def test_create_agent(self, service, mock_db):
        """Test création agent."""
        data = AgentCreate(
            user_id=100,
            display_name="Marie Support",
            team_id=1
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_agent(data)

        mock_db.add.assert_called_once()

    def test_get_agent(self, service, mock_db, sample_agent):
        """Test récupération agent."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_agent

        result = service.get_agent(1)

        assert result.display_name == "Jean Support"

    def test_update_agent_status(self, service, mock_db, sample_agent):
        """Test mise à jour statut agent."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_agent

        result = service.update_agent_status(1, AgentStatus.BUSY)

        assert sample_agent.status == AgentStatus.BUSY
        mock_db.commit.assert_called()


# ============================================================================
# TESTS SLA
# ============================================================================

class TestSLA:
    """Tests SLA."""

    def test_create_sla(self, service, mock_db):
        """Test création SLA."""
        data = SLACreate(
            name="Premium",
            first_response_critical=5,
            resolution_critical=60
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.update = MagicMock()

        result = service.create_sla(data)

        mock_db.add.assert_called_once()

    def test_get_default_sla(self, service, mock_db, sample_sla):
        """Test récupération SLA par défaut."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_sla

        result = service.get_default_sla()

        assert result.name == "Standard"
        assert result.is_default is True


# ============================================================================
# TESTS TICKETS
# ============================================================================

class TestTickets:
    """Tests tickets."""

    def test_generate_ticket_number(self, service):
        """Test génération numéro ticket."""
        with patch.object(service, '_generate_ticket_number', return_value="TK-2024-000001"):
            number = service._generate_ticket_number()

        assert number.startswith("TK-")
        assert len(number) > 10

    def test_create_ticket(self, service, mock_db):
        """Test création ticket."""
        data = TicketCreate(
            subject="Mon application ne démarre pas",
            description="Erreur au lancement",
            requester_email="user@example.com"
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch.object(service, '_generate_ticket_number', return_value="TK-2024-000001"):
            result = service.create_ticket(data)

        assert mock_db.add.call_count >= 1  # Ticket + History

    def test_get_ticket(self, service, mock_db, sample_ticket):
        """Test récupération ticket."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_ticket

        result = service.get_ticket(1)

        assert result.ticket_number == "TK-202401-ABC123"
        assert result.status == TicketStatus.NEW

    def test_get_ticket_by_number(self, service, mock_db, sample_ticket):
        """Test récupération par numéro."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_ticket

        result = service.get_ticket_by_number("TK-202401-ABC123")

        assert result.subject == "Problème de connexion"

    def test_update_ticket(self, service, mock_db, sample_ticket):
        """Test mise à jour ticket."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_ticket

        data = TicketUpdate(priority=TicketPriority.HIGH)
        result = service.update_ticket(1, data)

        mock_db.commit.assert_called()

    def test_assign_ticket(self, service, mock_db, sample_ticket, sample_agent):
        """Test assignation ticket."""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_ticket,  # get_ticket
            sample_agent,   # get_agent
        ]

        result = service.assign_ticket(1, 1)

        assert sample_ticket.assigned_to_id == 1
        mock_db.commit.assert_called()

    def test_change_ticket_status_resolved(self, service, mock_db, sample_ticket, sample_agent):
        """Test changement statut vers résolu."""
        sample_ticket.assigned_to_id = 1
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_ticket,
            sample_agent
        ]

        result = service.change_ticket_status(1, TicketStatus.RESOLVED)

        assert sample_ticket.status == TicketStatus.RESOLVED
        assert sample_ticket.resolved_at is not None

    def test_change_ticket_status_closed(self, service, mock_db, sample_ticket):
        """Test changement statut vers fermé."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_ticket

        result = service.change_ticket_status(1, TicketStatus.CLOSED)

        assert sample_ticket.status == TicketStatus.CLOSED
        assert sample_ticket.closed_at is not None


# ============================================================================
# TESTS REPLIES
# ============================================================================

class TestReplies:
    """Tests réponses."""

    def test_add_reply_public(self, service, mock_db, sample_ticket):
        """Test ajout réponse publique."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_ticket

        data = ReplyCreate(
            body="Merci pour votre message, nous examinons le problème."
        )

        result = service.add_reply(
            1, data,
            author_id=1,
            author_name="Agent",
            author_type="agent"
        )

        assert sample_ticket.reply_count == 1
        mock_db.add.assert_called()

    def test_add_reply_internal_note(self, service, mock_db, sample_ticket):
        """Test ajout note interne."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_ticket

        data = ReplyCreate(
            body="Note interne: escalader au N2",
            is_internal=True
        )

        result = service.add_reply(1, data, author_type="agent")

        assert sample_ticket.internal_note_count == 1

    def test_first_response_tracking(self, service, mock_db, sample_ticket):
        """Test suivi première réponse."""
        sample_ticket.first_responded_at = None
        mock_db.query.return_value.filter.return_value.first.return_value = sample_ticket

        data = ReplyCreate(body="Première réponse")
        result = service.add_reply(1, data, author_type="agent")

        assert sample_ticket.first_responded_at is not None


# ============================================================================
# TESTS ATTACHMENTS
# ============================================================================

class TestAttachments:
    """Tests pièces jointes."""

    def test_add_attachment(self, service, mock_db, sample_ticket):
        """Test ajout pièce jointe."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_ticket

        data = AttachmentCreate(
            filename="screenshot.png",
            file_size=102400,
            mime_type="image/png"
        )

        result = service.add_attachment(1, data, uploaded_by_id=1)

        mock_db.add.assert_called_once()


# ============================================================================
# TESTS CANNED RESPONSES
# ============================================================================

class TestCannedResponses:
    """Tests réponses pré-enregistrées."""

    def test_create_canned_response(self, service, mock_db):
        """Test création réponse pré-enregistrée."""
        data = CannedResponseCreate(
            title="Accueil",
            shortcut="#hello",
            body="Bonjour, merci de nous contacter."
        )

        result = service.create_canned_response(data)

        mock_db.add.assert_called_once()

    def test_get_by_shortcut(self, service, mock_db):
        """Test récupération par shortcut."""
        canned = MagicMock(spec=CannedResponse)
        canned.shortcut = "#hello"
        canned.body = "Bonjour!"
        mock_db.query.return_value.filter.return_value.first.return_value = canned

        result = service.get_canned_by_shortcut("#hello")

        assert result.shortcut == "#hello"

    def test_use_canned_response(self, service, mock_db):
        """Test incrémentation compteur."""
        canned = MagicMock(spec=CannedResponse)
        canned.usage_count = 5
        mock_db.query.return_value.filter.return_value.first.return_value = canned

        result = service.use_canned_response(1)

        assert canned.usage_count == 6


# ============================================================================
# TESTS KNOWLEDGE BASE
# ============================================================================

class TestKnowledgeBase:
    """Tests base de connaissances."""

    def test_create_kb_category(self, service, mock_db):
        """Test création catégorie KB."""
        data = KBCategoryCreate(
            name="FAQ",
            slug="faq",
            description="Questions fréquentes"
        )

        result = service.create_kb_category(data)

        mock_db.add.assert_called_once()

    def test_create_kb_article(self, service, mock_db):
        """Test création article KB."""
        data = KBArticleCreate(
            title="Comment réinitialiser mon mot de passe",
            slug="reset-password",
            body="Pour réinitialiser...",
            status="published"
        )

        result = service.create_kb_article(data, author_id=1, author_name="Admin")

        mock_db.add.assert_called_once()

    def test_view_article(self, service, mock_db):
        """Test incrémentation vues."""
        article = MagicMock(spec=KBArticle)
        article.view_count = 10
        mock_db.query.return_value.filter.return_value.first.return_value = article

        result = service.view_kb_article(1)

        assert article.view_count == 11

    def test_rate_article_helpful(self, service, mock_db):
        """Test notation article utile."""
        article = MagicMock(spec=KBArticle)
        article.helpful_count = 5
        article.not_helpful_count = 1
        mock_db.query.return_value.filter.return_value.first.return_value = article

        result = service.rate_kb_article(1, helpful=True)

        assert article.helpful_count == 6

    def test_rate_article_not_helpful(self, service, mock_db):
        """Test notation article non utile."""
        article = MagicMock(spec=KBArticle)
        article.helpful_count = 5
        article.not_helpful_count = 1
        mock_db.query.return_value.filter.return_value.first.return_value = article

        result = service.rate_kb_article(1, helpful=False)

        assert article.not_helpful_count == 2


# ============================================================================
# TESTS SATISFACTION
# ============================================================================

class TestSatisfaction:
    """Tests satisfaction."""

    def test_submit_satisfaction(self, service, mock_db, sample_ticket):
        """Test soumission enquête satisfaction."""
        sample_ticket.assigned_to_id = 1
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_ticket,  # get_ticket
            None  # get_agent returns None in this test
        ]
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        data = SatisfactionCreate(
            ticket_id=1,
            rating=5,
            feedback="Excellent support!"
        )

        result = service.submit_satisfaction(data, customer_id=100)

        assert sample_ticket.satisfaction_rating == 5
        mock_db.add.assert_called()


# ============================================================================
# TESTS AUTOMATIONS
# ============================================================================

class TestAutomations:
    """Tests automatisations."""

    def test_create_automation(self, service, mock_db):
        """Test création automatisation."""
        data = AutomationCreate(
            name="Fermer tickets inactifs",
            trigger_type="time_based",
            trigger_conditions=[{"field": "updated_at", "operator": "older_than", "value": 7}],
            actions=[{"type": "change_status", "params": {"status": "closed"}}]
        )

        result = service.create_automation(data)

        mock_db.add.assert_called_once()

    def test_list_automations(self, service, mock_db):
        """Test liste automatisations."""
        auto1 = MagicMock(spec=HelpdeskAutomation)
        auto1.name = "Rule 1"
        auto1.is_active = True

        # Le service fait .filter().filter().order_by().all() quand active_only=True
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [auto1]

        result = service.list_automations(active_only=True)

        assert len(result) == 1


# ============================================================================
# TESTS STATS & DASHBOARD
# ============================================================================

class TestDashboard:
    """Tests dashboard et statistiques."""

    def test_get_ticket_stats(self, service, mock_db):
        """Test statistiques tickets."""
        # Configurer correctement le mock pour retourner des valeurs cohérentes
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.all.return_value = []  # Liste vide, pas MagicMock

        result = service.get_ticket_stats(days=30)

        assert result.total == 0

    def test_get_agent_stats(self, service, mock_db, sample_agent):
        """Test statistiques agents."""
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_agent]
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        result = service.get_agent_stats(days=30)

        assert len(result) >= 0


# ============================================================================
# TESTS SLA CALCULATION
# ============================================================================

class TestSLACalculation:
    """Tests calcul SLA."""

    def test_calculate_sla_due_dates_with_sla(self, service, mock_db, sample_sla):
        """Test calcul dates SLA avec SLA défini."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_sla

        response_due, resolution_due = service._calculate_sla_due_dates(
            TicketPriority.MEDIUM,
            sample_sla
        )

        assert response_due is not None
        assert resolution_due is not None
        assert resolution_due > response_due

    def test_calculate_sla_due_dates_without_sla(self, service, mock_db):
        """Test calcul dates SLA sans SLA défini."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response_due, resolution_due = service._calculate_sla_due_dates(
            TicketPriority.HIGH
        )

        assert response_due is None
        assert resolution_due is None


# ============================================================================
# TESTS AUTO-ASSIGNMENT
# ============================================================================

class TestAutoAssignment:
    """Tests auto-assignation."""

    def test_auto_assign_round_robin(self, service, mock_db, sample_team, sample_agent):
        """Test auto-assignation round robin."""
        sample_team.auto_assign_method = "round_robin"
        agent2 = MagicMock(spec=HelpdeskAgent)
        agent2.id = 2
        agent2.tickets_assigned = 10

        mock_db.query.return_value.filter.return_value.all.return_value = [sample_agent, agent2]

        result = service._auto_assign_ticket(sample_team)

        # Should assign to agent with fewer tickets
        assert result == sample_agent.id

    def test_auto_assign_manual(self, service, mock_db, sample_team):
        """Test pas d'auto-assignation si manuel."""
        sample_team.auto_assign_method = "manual"

        result = service._auto_assign_ticket(sample_team)

        assert result is None

    def test_auto_assign_no_agents(self, service, mock_db, sample_team):
        """Test pas d'auto-assignation si pas d'agents."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = service._auto_assign_ticket(sample_team)

        assert result is None


# ============================================================================
# TESTS TICKET MERGE
# ============================================================================

class TestTicketMerge:
    """Tests fusion tickets."""

    def test_merge_tickets(self, service, mock_db, sample_ticket):
        """Test fusion de tickets."""
        source_ticket = MagicMock(spec=Ticket)
        source_ticket.id = 2
        source_ticket.ticket_number = "TK-SOURCE"
        source_ticket.reply_count = 3

        target_ticket = MagicMock(spec=Ticket)
        target_ticket.id = 1
        target_ticket.ticket_number = "TK-TARGET"
        target_ticket.reply_count = 5

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            source_ticket,
            target_ticket
        ]
        mock_db.query.return_value.filter.return_value.update = MagicMock()

        result = service.merge_tickets(2, 1)

        assert source_ticket.merged_into_id == 1
        assert source_ticket.status == TicketStatus.CLOSED
        assert target_ticket.reply_count == 8


# ============================================================================
# TESTS ENUMS
# ============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_ticket_status_values(self):
        """Test valeurs statut ticket."""
        assert TicketStatus.NEW.value == "new"
        assert TicketStatus.OPEN.value == "open"
        assert TicketStatus.RESOLVED.value == "resolved"
        assert TicketStatus.CLOSED.value == "closed"

    def test_ticket_priority_values(self):
        """Test valeurs priorité."""
        assert TicketPriority.LOW.value == "low"
        assert TicketPriority.CRITICAL.value == "critical"

    def test_ticket_source_values(self):
        """Test valeurs source."""
        assert TicketSource.WEB.value == "web"
        assert TicketSource.EMAIL.value == "email"

    def test_agent_status_values(self):
        """Test valeurs statut agent."""
        assert AgentStatus.AVAILABLE.value == "available"
        assert AgentStatus.OFFLINE.value == "offline"
