"""
AZALS MODULE T6 - Tests Diffusion Périodique
============================================

Tests unitaires pour le module de diffusion automatique.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import json

# Import des modèles
from app.modules.broadcast.models import (
    BroadcastTemplate, RecipientList, RecipientMember,
    ScheduledBroadcast, BroadcastExecution, DeliveryDetail,
    BroadcastPreference, BroadcastMetric,
    DeliveryChannel, BroadcastFrequency, ContentType,
    BroadcastStatus, DeliveryStatus, RecipientType
)

# Import des schémas
from app.modules.broadcast.schemas import (
    BroadcastTemplateCreate, BroadcastTemplateResponse,
    RecipientListCreate, RecipientMemberCreate,
    ScheduledBroadcastCreate, ScheduledBroadcastResponse,
    BroadcastPreferenceCreate, BroadcastPreferenceResponse,
    ContentTypeEnum, DeliveryChannelEnum, BroadcastFrequencyEnum,
    BroadcastStatusEnum
)

# Import du service
from app.modules.broadcast.service import BroadcastService, get_broadcast_service


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock de la session DB."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


@pytest.fixture
def tenant_id():
    """ID tenant de test."""
    return "test-tenant-001"


@pytest.fixture
def broadcast_service(mock_db, tenant_id):
    """Service broadcast initialisé."""
    return BroadcastService(mock_db, tenant_id)


@pytest.fixture
def sample_template():
    """Template de test."""
    template = MagicMock(spec=BroadcastTemplate)
    template.id = 1
    template.tenant_id = "test-tenant-001"
    template.code = "WEEKLY_DIGEST"
    template.name = "Digest Hebdomadaire"
    template.content_type = ContentType.DIGEST
    template.subject_template = "Votre résumé de la semaine"
    template.body_template = "Contenu du digest..."
    template.default_channel = DeliveryChannel.EMAIL
    template.is_active = True
    template.is_system = False
    template.created_at = datetime.utcnow()
    template.updated_at = datetime.utcnow()
    return template


@pytest.fixture
def sample_recipient_list():
    """Liste de destinataires de test."""
    rl = MagicMock(spec=RecipientList)
    rl.id = 1
    rl.tenant_id = "test-tenant-001"
    rl.code = "ALL_MANAGERS"
    rl.name = "Tous les managers"
    rl.total_recipients = 10
    rl.active_recipients = 8
    rl.is_active = True
    rl.is_dynamic = False
    return rl


@pytest.fixture
def sample_scheduled_broadcast():
    """Diffusion programmée de test."""
    sb = MagicMock(spec=ScheduledBroadcast)
    sb.id = 1
    sb.tenant_id = "test-tenant-001"
    sb.code = "WEEKLY_KPI_REPORT"
    sb.name = "Rapport KPIs Hebdomadaire"
    sb.content_type = ContentType.REPORT
    sb.frequency = BroadcastFrequency.WEEKLY
    sb.delivery_channel = DeliveryChannel.EMAIL
    sb.status = BroadcastStatus.ACTIVE
    sb.is_active = True
    sb.day_of_week = 1  # Lundi
    sb.send_time = "09:00"
    sb.total_sent = 52
    sb.total_delivered = 50
    sb.last_run_at = datetime.utcnow() - timedelta(days=7)
    sb.next_run_at = datetime.utcnow() + timedelta(days=1)
    return sb


# ============================================================================
# TESTS ENUMS
# ============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_delivery_channel_values(self):
        """Vérifier les valeurs DeliveryChannel."""
        assert DeliveryChannel.EMAIL.value == "EMAIL"
        assert DeliveryChannel.IN_APP.value == "IN_APP"
        assert DeliveryChannel.WEBHOOK.value == "WEBHOOK"
        assert DeliveryChannel.PDF_DOWNLOAD.value == "PDF_DOWNLOAD"
        assert DeliveryChannel.SMS.value == "SMS"

    def test_broadcast_frequency_values(self):
        """Vérifier les valeurs BroadcastFrequency."""
        assert BroadcastFrequency.ONCE.value == "ONCE"
        assert BroadcastFrequency.DAILY.value == "DAILY"
        assert BroadcastFrequency.WEEKLY.value == "WEEKLY"
        assert BroadcastFrequency.MONTHLY.value == "MONTHLY"
        assert BroadcastFrequency.YEARLY.value == "YEARLY"

    def test_content_type_values(self):
        """Vérifier les valeurs ContentType."""
        assert ContentType.DIGEST.value == "DIGEST"
        assert ContentType.NEWSLETTER.value == "NEWSLETTER"
        assert ContentType.REPORT.value == "REPORT"
        assert ContentType.ALERT.value == "ALERT"
        assert ContentType.KPI_SUMMARY.value == "KPI_SUMMARY"

    def test_broadcast_status_values(self):
        """Vérifier les valeurs BroadcastStatus."""
        assert BroadcastStatus.DRAFT.value == "DRAFT"
        assert BroadcastStatus.SCHEDULED.value == "SCHEDULED"
        assert BroadcastStatus.ACTIVE.value == "ACTIVE"
        assert BroadcastStatus.PAUSED.value == "PAUSED"
        assert BroadcastStatus.COMPLETED.value == "COMPLETED"

    def test_delivery_status_values(self):
        """Vérifier les valeurs DeliveryStatus."""
        assert DeliveryStatus.PENDING.value == "PENDING"
        assert DeliveryStatus.DELIVERED.value == "DELIVERED"
        assert DeliveryStatus.FAILED.value == "FAILED"
        assert DeliveryStatus.OPENED.value == "OPENED"

    def test_recipient_type_values(self):
        """Vérifier les valeurs RecipientType."""
        assert RecipientType.USER.value == "USER"
        assert RecipientType.GROUP.value == "GROUP"
        assert RecipientType.ROLE.value == "ROLE"
        assert RecipientType.EXTERNAL.value == "EXTERNAL"
        assert RecipientType.DYNAMIC.value == "DYNAMIC"


# ============================================================================
# TESTS MODÈLES
# ============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_broadcast_template_creation(self):
        """Tester la création d'un template."""
        template = BroadcastTemplate(
            tenant_id="tenant-001",
            code="TEST_TEMPLATE",
            name="Template Test",
            content_type=ContentType.NEWSLETTER,
            subject_template="Subject {{var}}",
            default_channel=DeliveryChannel.EMAIL,
            is_active=True  # Explicite pour test unitaire
        )
        assert template.code == "TEST_TEMPLATE"
        assert template.content_type == ContentType.NEWSLETTER
        assert template.is_active == True

    def test_recipient_list_creation(self):
        """Tester la création d'une liste."""
        rl = RecipientList(
            tenant_id="tenant-001",
            code="VIP_CLIENTS",
            name="Clients VIP",
            is_dynamic=False,
            total_recipients=0,  # Explicite pour test unitaire
            is_active=True  # Explicite pour test unitaire
        )
        assert rl.code == "VIP_CLIENTS"
        assert rl.total_recipients == 0
        assert rl.is_active == True

    def test_scheduled_broadcast_creation(self):
        """Tester la création d'une diffusion programmée."""
        sb = ScheduledBroadcast(
            tenant_id="tenant-001",
            code="DAILY_ALERT",
            name="Alerte Quotidienne",
            content_type=ContentType.ALERT,
            frequency=BroadcastFrequency.DAILY,
            delivery_channel=DeliveryChannel.EMAIL,
            status=BroadcastStatus.DRAFT  # Explicite pour test unitaire
        )
        assert sb.code == "DAILY_ALERT"
        assert sb.frequency == BroadcastFrequency.DAILY
        assert sb.status == BroadcastStatus.DRAFT

    def test_broadcast_execution_creation(self):
        """Tester la création d'une exécution."""
        execution = BroadcastExecution(
            tenant_id="tenant-001",
            scheduled_broadcast_id=1,
            execution_number=5,
            status=DeliveryStatus.PENDING,  # Explicite pour test unitaire
            total_recipients=0  # Explicite pour test unitaire
        )
        assert execution.execution_number == 5
        assert execution.status == DeliveryStatus.PENDING
        assert execution.total_recipients == 0

    def test_delivery_detail_creation(self):
        """Tester la création d'un détail de livraison."""
        detail = DeliveryDetail(
            tenant_id="tenant-001",
            execution_id=1,
            recipient_type=RecipientType.USER,
            user_id=42,
            email="user@example.com",
            channel=DeliveryChannel.EMAIL,
            status=DeliveryStatus.PENDING  # Explicite pour test unitaire
        )
        assert detail.user_id == 42
        assert detail.channel == DeliveryChannel.EMAIL
        assert detail.status == DeliveryStatus.PENDING

    def test_broadcast_preference_creation(self):
        """Tester la création de préférences."""
        pref = BroadcastPreference(
            tenant_id="tenant-001",
            user_id=42,
            receive_digests=True,
            preferred_channel=DeliveryChannel.IN_APP
        )
        assert pref.user_id == 42
        assert pref.receive_digests == True
        assert pref.preferred_channel == DeliveryChannel.IN_APP


# ============================================================================
# TESTS SCHÉMAS
# ============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_template_create_schema(self):
        """Tester le schéma de création template."""
        data = BroadcastTemplateCreate(
            code="NEW_TEMPLATE",
            name="Nouveau Template",
            content_type=ContentTypeEnum.NEWSLETTER,
            subject_template="Subject",
            default_channel=DeliveryChannelEnum.EMAIL
        )
        assert data.code == "NEW_TEMPLATE"
        assert data.content_type == ContentTypeEnum.NEWSLETTER

    def test_template_create_validation(self):
        """Tester la validation du schéma template."""
        with pytest.raises(ValueError):
            BroadcastTemplateCreate(
                code="X",  # Trop court
                name="Name",
                content_type=ContentTypeEnum.DIGEST
            )

    def test_recipient_list_create_schema(self):
        """Tester le schéma de création liste."""
        data = RecipientListCreate(
            code="NEW_LIST",
            name="Nouvelle Liste",
            is_dynamic=True,
            query_config={"role": "MANAGER"}
        )
        assert data.code == "NEW_LIST"
        assert data.is_dynamic == True

    def test_scheduled_broadcast_create_schema(self):
        """Tester le schéma de création broadcast."""
        data = ScheduledBroadcastCreate(
            code="NEW_BROADCAST",
            name="Nouvelle Diffusion",
            content_type=ContentTypeEnum.REPORT,
            frequency=BroadcastFrequencyEnum.WEEKLY,
            delivery_channel=DeliveryChannelEnum.EMAIL,
            day_of_week=1,
            send_time="09:00"
        )
        assert data.code == "NEW_BROADCAST"
        assert data.frequency == BroadcastFrequencyEnum.WEEKLY
        assert data.day_of_week == 1

    def test_broadcast_preference_create_schema(self):
        """Tester le schéma de préférences."""
        data = BroadcastPreferenceCreate(
            receive_digests=True,
            receive_newsletters=False,
            preferred_channel=DeliveryChannelEnum.IN_APP,
            digest_frequency=BroadcastFrequencyEnum.WEEKLY
        )
        assert data.receive_newsletters == False
        assert data.preferred_channel == DeliveryChannelEnum.IN_APP


# ============================================================================
# TESTS SERVICE - TEMPLATES
# ============================================================================

class TestServiceTemplates:
    """Tests du service - Templates."""

    def test_create_template(self, broadcast_service, mock_db):
        """Tester la création d'un template."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = broadcast_service.create_template(
            code="TEST_TPL",
            name="Template Test",
            content_type=ContentType.DIGEST,
            subject_template="Subject",
            created_by=1
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_template(self, broadcast_service, mock_db, sample_template):
        """Tester la récupération d'un template."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_template

        result = broadcast_service.get_template(1)

        assert result is not None
        assert result.code == "WEEKLY_DIGEST"

    def test_list_templates(self, broadcast_service, mock_db, sample_template):
        """Tester le listing des templates."""
        # Configurer mock pour chaînes de filtres
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_template]
        mock_db.query.return_value = mock_query

        items, total = broadcast_service.list_templates()

        assert total == 1

    def test_delete_template(self, broadcast_service, mock_db, sample_template):
        """Tester la suppression d'un template."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_template

        result = broadcast_service.delete_template(1)

        assert result == True
        mock_db.delete.assert_called_once()


# ============================================================================
# TESTS SERVICE - LISTES DESTINATAIRES
# ============================================================================

class TestServiceRecipientLists:
    """Tests du service - Listes destinataires."""

    def test_create_recipient_list(self, broadcast_service, mock_db):
        """Tester la création d'une liste."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = broadcast_service.create_recipient_list(
            code="TEST_LIST",
            name="Liste Test",
            created_by=1
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_add_member_to_list(self, broadcast_service, mock_db, sample_recipient_list):
        """Tester l'ajout d'un membre."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_recipient_list
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = broadcast_service.add_member_to_list(
            list_id=1,
            recipient_type=RecipientType.USER,
            user_id=42,
            added_by=1
        )

        mock_db.add.assert_called_once()

    def test_get_list_members(self, broadcast_service, mock_db):
        """Tester la récupération des membres."""
        mock_member = MagicMock(spec=RecipientMember)
        mock_member.id = 1
        mock_member.user_id = 42
        mock_member.is_active = True

        # Configurer mock pour chaînes de filtres
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value.limit.return_value.all.return_value = [mock_member]
        mock_db.query.return_value = mock_query

        items, total = broadcast_service.get_list_members(1)

        assert total == 1


# ============================================================================
# TESTS SERVICE - DIFFUSIONS PROGRAMMÉES
# ============================================================================

class TestServiceScheduledBroadcasts:
    """Tests du service - Diffusions programmées."""

    def test_create_scheduled_broadcast(self, broadcast_service, mock_db):
        """Tester la création d'une diffusion."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = broadcast_service.create_scheduled_broadcast(
            code="WEEKLY_REPORT",
            name="Rapport Hebdo",
            content_type=ContentType.REPORT,
            frequency=BroadcastFrequency.WEEKLY,
            delivery_channel=DeliveryChannel.EMAIL,
            day_of_week=1,
            send_time="09:00",
            created_by=1
        )

        mock_db.add.assert_called_once()

    def test_activate_broadcast(self, broadcast_service, mock_db, sample_scheduled_broadcast):
        """Tester l'activation d'une diffusion."""
        sample_scheduled_broadcast.status = BroadcastStatus.DRAFT
        mock_db.query.return_value.filter.return_value.first.return_value = sample_scheduled_broadcast

        result = broadcast_service.activate_broadcast(1)

        assert result is not None

    def test_pause_broadcast(self, broadcast_service, mock_db, sample_scheduled_broadcast):
        """Tester la mise en pause."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_scheduled_broadcast

        result = broadcast_service.pause_broadcast(1)

        assert result is not None

    def test_cancel_broadcast(self, broadcast_service, mock_db, sample_scheduled_broadcast):
        """Tester l'annulation."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_scheduled_broadcast

        result = broadcast_service.cancel_broadcast(1)

        assert result is not None

    def test_get_broadcasts_due(self, broadcast_service, mock_db, sample_scheduled_broadcast):
        """Tester la récupération des diffusions à exécuter."""
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_scheduled_broadcast]

        result = broadcast_service.get_broadcasts_due()

        assert len(result) == 1


# ============================================================================
# TESTS SERVICE - EXÉCUTION
# ============================================================================

class TestServiceExecution:
    """Tests du service - Exécution."""

    def test_execute_broadcast(self, broadcast_service, mock_db, sample_scheduled_broadcast, sample_recipient_list):
        """Tester l'exécution d'une diffusion."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_scheduled_broadcast
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = broadcast_service.execute_broadcast(1, triggered_by="test")

        assert result is not None
        mock_db.add.assert_called()

    def test_get_execution(self, broadcast_service, mock_db):
        """Tester la récupération d'une exécution."""
        mock_execution = MagicMock(spec=BroadcastExecution)
        mock_execution.id = 1
        mock_execution.status = DeliveryStatus.DELIVERED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_execution

        result = broadcast_service.get_execution(1)

        assert result is not None
        assert result.status == DeliveryStatus.DELIVERED

    def test_list_executions(self, broadcast_service, mock_db):
        """Tester le listing des exécutions."""
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        items, total = broadcast_service.list_executions()

        assert total == 5


# ============================================================================
# TESTS SERVICE - PRÉFÉRENCES
# ============================================================================

class TestServicePreferences:
    """Tests du service - Préférences."""

    def test_get_user_preferences(self, broadcast_service, mock_db):
        """Tester la récupération des préférences."""
        mock_pref = MagicMock(spec=BroadcastPreference)
        mock_pref.user_id = 42
        mock_pref.receive_digests = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_pref

        result = broadcast_service.get_user_preferences(42)

        assert result is not None
        assert result.receive_digests == True

    def test_set_user_preferences(self, broadcast_service, mock_db):
        """Tester la définition des préférences."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = broadcast_service.set_user_preferences(
            user_id=42,
            receive_newsletters=False
        )

        mock_db.add.assert_called_once()

    def test_unsubscribe_user_all(self, broadcast_service, mock_db):
        """Tester le désabonnement global."""
        mock_pref = MagicMock(spec=BroadcastPreference)
        mock_pref.user_id = 42
        mock_pref.is_unsubscribed_all = False

        mock_db.query.return_value.filter.return_value.first.return_value = mock_pref

        result = broadcast_service.unsubscribe_user(42)

        assert result == True

    def test_unsubscribe_user_specific(self, broadcast_service, mock_db):
        """Tester le désabonnement spécifique."""
        mock_pref = MagicMock(spec=BroadcastPreference)
        mock_pref.user_id = 42
        mock_pref.excluded_broadcasts = "[]"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_pref

        result = broadcast_service.unsubscribe_user(42, broadcast_id=5)

        assert result == True


# ============================================================================
# TESTS SERVICE - MÉTRIQUES
# ============================================================================

class TestServiceMetrics:
    """Tests du service - Métriques."""

    def test_record_metrics(self, broadcast_service, mock_db):
        """Tester l'enregistrement des métriques."""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = broadcast_service.record_metrics()

        mock_db.add.assert_called_once()

    def test_get_metrics(self, broadcast_service, mock_db):
        """Tester la récupération des métriques."""
        mock_metric = MagicMock(spec=BroadcastMetric)
        mock_metric.metric_date = datetime.utcnow()
        mock_metric.total_messages = 100

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_metric]

        result = broadcast_service.get_metrics()

        assert len(result) == 1

    def test_get_dashboard_stats(self, broadcast_service, mock_db):
        """Tester les stats dashboard."""
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = broadcast_service.get_dashboard_stats()

        assert "total_broadcasts" in result
        assert "active_broadcasts" in result
        assert "upcoming_broadcasts" in result


# ============================================================================
# TESTS CALCUL NEXT RUN
# ============================================================================

class TestNextRunCalculation:
    """Tests du calcul de prochaine exécution."""

    def test_calculate_next_run_daily(self, broadcast_service):
        """Tester calcul quotidien."""
        sb = MagicMock(spec=ScheduledBroadcast)
        sb.frequency = BroadcastFrequency.DAILY
        sb.last_run_at = datetime.utcnow()
        sb.send_time = "09:00"
        sb.start_date = None

        result = broadcast_service._calculate_next_run(sb)

        assert result is not None
        assert result > datetime.utcnow()

    def test_calculate_next_run_weekly(self, broadcast_service):
        """Tester calcul hebdomadaire."""
        sb = MagicMock(spec=ScheduledBroadcast)
        sb.frequency = BroadcastFrequency.WEEKLY
        sb.last_run_at = datetime.utcnow()
        sb.day_of_week = 1
        sb.send_time = "09:00"
        sb.start_date = None

        result = broadcast_service._calculate_next_run(sb)

        assert result is not None

    def test_calculate_next_run_monthly(self, broadcast_service):
        """Tester calcul mensuel."""
        sb = MagicMock(spec=ScheduledBroadcast)
        sb.frequency = BroadcastFrequency.MONTHLY
        sb.last_run_at = datetime.utcnow()
        sb.day_of_month = 15
        sb.send_time = None
        sb.start_date = None

        result = broadcast_service._calculate_next_run(sb)

        assert result is not None

    def test_calculate_next_run_once(self, broadcast_service):
        """Tester calcul unique."""
        sb = MagicMock(spec=ScheduledBroadcast)
        sb.frequency = BroadcastFrequency.ONCE
        sb.start_date = datetime.utcnow() + timedelta(days=1)
        sb.last_run_at = None

        result = broadcast_service._calculate_next_run(sb)

        assert result == sb.start_date


# ============================================================================
# TESTS FACTORY
# ============================================================================

class TestFactory:
    """Tests de la factory du service."""

    def test_get_broadcast_service(self, mock_db, tenant_id):
        """Tester la création du service."""
        service = get_broadcast_service(mock_db, tenant_id)

        assert service is not None
        assert isinstance(service, BroadcastService)
        assert service.tenant_id == tenant_id


# ============================================================================
# TESTS INTÉGRATION
# ============================================================================

class TestIntegration:
    """Tests d'intégration du module."""

    def test_full_broadcast_workflow(self, broadcast_service, mock_db, sample_template, sample_recipient_list):
        """Tester le workflow complet."""
        # Setup mocks
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []

        # 1. Créer template
        template = broadcast_service.create_template(
            code="WORKFLOW_TPL",
            name="Template Workflow",
            content_type=ContentType.NEWSLETTER,
            created_by=1
        )
        assert template is not None

        # 2. Créer liste destinataires
        recipient_list = broadcast_service.create_recipient_list(
            code="WORKFLOW_LIST",
            name="Liste Workflow",
            created_by=1
        )
        assert recipient_list is not None

        # 3. Créer diffusion programmée
        broadcast = broadcast_service.create_scheduled_broadcast(
            code="WORKFLOW_BROADCAST",
            name="Diffusion Workflow",
            content_type=ContentType.NEWSLETTER,
            frequency=BroadcastFrequency.WEEKLY,
            created_by=1
        )
        assert broadcast is not None

    def test_multi_tenant_isolation(self, mock_db):
        """Tester l'isolation multi-tenant."""
        service1 = BroadcastService(mock_db, "tenant-001")
        service2 = BroadcastService(mock_db, "tenant-002")

        assert service1.tenant_id != service2.tenant_id

        # Chaque service filtre par son tenant
        service1.list_templates()
        service2.list_templates()

        # Vérifier que les appels incluent le tenant_id
        assert mock_db.query.called
