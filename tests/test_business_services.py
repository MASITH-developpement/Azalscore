"""
Tests unitaires pour les services métier - Phase 3
Tests pour reporting_engine, notification_service, data_import_export, workflow_automation
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json
import io


# ============================================================================
# Tests Reporting Engine
# ============================================================================

class TestReportingEngine:
    """Tests pour le moteur de reporting"""

    @pytest.fixture
    def reporting_engine(self):
        from app.services.reporting_engine import ReportingEngine, get_reporting_engine
        return get_reporting_engine()

    @pytest.fixture
    def sample_template(self):
        from app.services.reporting_engine import ReportTemplate, ReportField
        return ReportTemplate(
            id="tpl_invoice_list",
            name="Liste des factures",
            description="Rapport des factures",
            category="finance",
            format_default="pdf",
            fields=[
                ReportField(name="invoice_number", label="N° Facture", data_type="string"),
                ReportField(name="date", label="Date", data_type="date"),
                ReportField(name="amount", label="Montant", data_type="decimal"),
                ReportField(name="client", label="Client", data_type="string")
            ],
            tenant_id="tenant_001"
        )

    @pytest.fixture
    def sample_data(self):
        return [
            {"invoice_number": "INV-001", "date": "2024-01-15", "amount": 1500.00, "client": "Client A"},
            {"invoice_number": "INV-002", "date": "2024-01-16", "amount": 2300.50, "client": "Client B"},
            {"invoice_number": "INV-003", "date": "2024-01-17", "amount": 850.00, "client": "Client C"},
        ]

    def test_register_template(self, reporting_engine, sample_template):
        """Test enregistrement de template"""
        reporting_engine.register_template(sample_template)

        retrieved = reporting_engine.get_template(sample_template.id)
        assert retrieved is not None
        assert retrieved.id == sample_template.id
        assert retrieved.name == "Liste des factures"

    def test_list_templates(self, reporting_engine, sample_template):
        """Test liste des templates"""
        reporting_engine.register_template(sample_template)

        templates = reporting_engine.list_templates(tenant_id="tenant_001")
        assert len(templates) >= 1

    @pytest.mark.asyncio
    async def test_generate_csv_report(self, reporting_engine, sample_template, sample_data):
        """Test génération rapport CSV"""
        from app.services.reporting_engine import ReportParameters, ReportFormat

        reporting_engine.register_template(sample_template)

        params = ReportParameters(
            template_id=sample_template.id,
            format=ReportFormat.CSV,
            data=sample_data,
            tenant_id="tenant_001"
        )

        report = await reporting_engine.generate_report(params)

        assert report is not None
        assert report.format == ReportFormat.CSV
        assert report.content is not None
        assert b"INV-001" in report.content
        assert report.file_size > 0

    @pytest.mark.asyncio
    async def test_generate_json_report(self, reporting_engine, sample_template, sample_data):
        """Test génération rapport JSON"""
        from app.services.reporting_engine import ReportParameters, ReportFormat

        reporting_engine.register_template(sample_template)

        params = ReportParameters(
            template_id=sample_template.id,
            format=ReportFormat.JSON,
            data=sample_data,
            tenant_id="tenant_001"
        )

        report = await reporting_engine.generate_report(params)

        assert report is not None
        json_data = json.loads(report.content.decode())
        assert "data" in json_data
        assert len(json_data["data"]) == 3

    @pytest.mark.asyncio
    async def test_generate_excel_report(self, reporting_engine, sample_template, sample_data):
        """Test génération rapport Excel"""
        from app.services.reporting_engine import ReportParameters, ReportFormat

        reporting_engine.register_template(sample_template)

        params = ReportParameters(
            template_id=sample_template.id,
            format=ReportFormat.EXCEL,
            data=sample_data,
            tenant_id="tenant_001"
        )

        report = await reporting_engine.generate_report(params)

        assert report is not None
        assert report.format == ReportFormat.EXCEL
        assert report.content[:4] == b'PK\x03\x04'

    @pytest.mark.asyncio
    async def test_generate_html_report(self, reporting_engine, sample_template, sample_data):
        """Test génération rapport HTML"""
        from app.services.reporting_engine import ReportParameters, ReportFormat

        reporting_engine.register_template(sample_template)

        params = ReportParameters(
            template_id=sample_template.id,
            format=ReportFormat.HTML,
            data=sample_data,
            tenant_id="tenant_001"
        )

        report = await reporting_engine.generate_report(params)

        assert report is not None
        assert b"<html" in report.content.lower() or b"<!doctype" in report.content.lower()
        assert b"INV-001" in report.content


class TestReportScheduler:
    """Tests pour le planificateur de rapports"""

    @pytest.fixture
    def reporting_engine(self):
        from app.services.reporting_engine import get_reporting_engine
        return get_reporting_engine()

    def test_schedule_report(self, reporting_engine):
        """Test planification de rapport"""
        from app.services.reporting_engine import ReportSchedule, ReportFormat

        schedule = ReportSchedule(
            id="sched_001",
            template_id="tpl_invoice_list",
            name="Rapport hebdomadaire",
            cron_expression="0 8 * * 1",
            format=ReportFormat.PDF,
            tenant_id="tenant_001",
            recipients=["admin@example.com"]
        )

        reporting_engine.schedule_report(schedule)
        schedules = reporting_engine.list_schedules(tenant_id="tenant_001")

        assert len(schedules) >= 1


# ============================================================================
# Tests Notification Service
# ============================================================================

class TestNotificationService:
    """Tests pour le service de notifications"""

    @pytest.fixture
    def notification_service(self):
        from app.services.notification_service import NotificationService, get_notification_service
        return get_notification_service()

    @pytest.fixture
    def sample_template(self):
        from app.services.notification_service import NotificationTemplate, NotificationChannel
        return NotificationTemplate(
            id="tpl_invoice_created",
            name="Nouvelle facture",
            description="Notification de création de facture",
            channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            subject_template="Facture {{invoice_number}} créée",
            body_template="La facture {{invoice_number}} de {{amount}}€ a été créée pour {{client}}.",
            tenant_id="tenant_001"
        )

    def test_register_template(self, notification_service, sample_template):
        """Test enregistrement de template de notification"""
        notification_service.register_template(sample_template)

        retrieved = notification_service.get_template(sample_template.id)
        assert retrieved is not None
        assert retrieved.name == "Nouvelle facture"

    @pytest.mark.asyncio
    async def test_send_notification(self, notification_service, sample_template):
        """Test envoi de notification"""
        from app.services.notification_service import NotificationChannel

        notification_service.register_template(sample_template)

        notifications = await notification_service.send(
            template_id=sample_template.id,
            recipient="user@example.com",
            variables={
                "invoice_number": "INV-001",
                "amount": "1500.00",
                "client": "Client ABC"
            },
            tenant_id="tenant_001",
            channels=[NotificationChannel.IN_APP]
        )

        assert len(notifications) >= 1
        notif = notifications[0]
        assert notif.recipient == "user@example.com"
        assert "INV-001" in notif.body

    @pytest.mark.asyncio
    async def test_send_direct_notification(self, notification_service):
        """Test envoi de notification directe"""
        from app.services.notification_service import NotificationChannel

        notification = await notification_service.send_direct(
            channel=NotificationChannel.IN_APP,
            recipient="user@example.com",
            content={
                "title": "Test Direct",
                "body": "Message de test direct"
            },
            tenant_id="tenant_001"
        )

        assert notification is not None
        assert notification.subject == "Test Direct"

    def test_set_user_preferences(self, notification_service):
        """Test définition des préférences utilisateur"""
        from app.services.notification_service import UserPreferences, NotificationChannel

        prefs = UserPreferences(
            user_id="user_123",
            tenant_id="tenant_001",
            enabled_channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            quiet_hours_start=22,
            quiet_hours_end=8,
            email_digest=True
        )

        notification_service.set_user_preferences(prefs)
        retrieved = notification_service.get_user_preferences("user_123", "tenant_001")

        assert retrieved is not None
        assert retrieved.email_digest is True

    def test_throttling(self, notification_service):
        """Test throttling des notifications"""
        from app.services.notification_service import NotificationChannel

        for _ in range(100):
            asyncio.get_event_loop().run_until_complete(
                notification_service.send_direct(
                    channel=NotificationChannel.IN_APP,
                    recipient="user@example.com",
                    content={"title": "Test", "body": "Test throttle"},
                    tenant_id="tenant_001"
                )
            )


# ============================================================================
# Tests Data Import/Export
# ============================================================================

class TestDataImportExportService:
    """Tests pour le service d'import/export"""

    @pytest.fixture
    def import_export_service(self):
        from app.services.data_import_export import DataImportExportService, get_import_export_service
        return get_import_export_service()

    @pytest.fixture
    def sample_csv_content(self):
        return b"""code_client;raison_sociale;siren;email
CLI001;Client Alpha;123456789;alpha@example.com
CLI002;Client Beta;987654321;beta@example.com
CLI003;Client Gamma;456789123;gamma@example.com"""

    @pytest.fixture
    def sample_json_content(self):
        return json.dumps([
            {"code": "CLI001", "name": "Client Alpha", "email": "alpha@example.com"},
            {"code": "CLI002", "name": "Client Beta", "email": "beta@example.com"}
        ]).encode()

    def test_get_file_headers_csv(self, import_export_service, sample_csv_content):
        """Test extraction des en-têtes CSV"""
        from app.services.data_import_export import ImportFormat

        headers = import_export_service.get_file_headers(
            content=sample_csv_content,
            format=ImportFormat.CSV,
            options={"delimiter": ";"}
        )

        assert len(headers) == 4
        assert "code_client" in headers
        assert "raison_sociale" in headers

    def test_preview_import(self, import_export_service, sample_csv_content):
        """Test prévisualisation d'import"""
        from app.services.data_import_export import ImportFormat

        preview = import_export_service.preview_import(
            content=sample_csv_content,
            format=ImportFormat.CSV,
            options={"delimiter": ";"},
            max_rows=2
        )

        assert len(preview) == 2
        assert preview[0]["code_client"] == "CLI001"

    def test_validate_data(self, import_export_service, sample_csv_content):
        """Test validation des données"""
        from app.services.data_import_export import ImportFormat, FieldMapping

        mappings = [
            FieldMapping(
                source_field="code_client",
                target_field="client_code",
                data_type="string",
                required=True
            ),
            FieldMapping(
                source_field="siren",
                target_field="siren",
                data_type="siren"
            ),
            FieldMapping(
                source_field="email",
                target_field="email",
                data_type="email"
            )
        ]

        is_valid, errors = import_export_service.validate_data(
            content=sample_csv_content,
            format=ImportFormat.CSV,
            field_mappings=mappings,
            options={"delimiter": ";"}
        )

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_import_data(self, import_export_service, sample_csv_content):
        """Test import de données"""
        from app.services.data_import_export import ImportFormat, FieldMapping, ImportStatus

        mappings = [
            FieldMapping(
                source_field="code_client",
                target_field="client_code",
                data_type="string",
                required=True
            ),
            FieldMapping(
                source_field="raison_sociale",
                target_field="company_name",
                data_type="string"
            )
        ]

        records_created = []

        async def mock_handler(record):
            record_id = f"rec_{len(records_created)}"
            records_created.append(record)
            return record_id

        result = await import_export_service.import_data(
            content=sample_csv_content,
            format=ImportFormat.CSV,
            field_mappings=mappings,
            entity_handler=mock_handler,
            options={"delimiter": ";"},
            tenant_id="tenant_001"
        )

        assert result.status == ImportStatus.COMPLETED
        assert result.successful_rows == 3
        assert result.failed_rows == 0
        assert len(records_created) == 3

    def test_export_csv(self, import_export_service):
        """Test export CSV"""
        from app.services.data_import_export import ExportFormat

        data = [
            {"code": "CLI001", "name": "Client Alpha", "amount": 1500.00},
            {"code": "CLI002", "name": "Client Beta", "amount": 2300.50}
        ]

        result = import_export_service.export_data(
            data=data,
            format=ExportFormat.CSV,
            options={"delimiter": ";"}
        )

        assert result is not None
        assert b"CLI001" in result.file_content
        assert result.total_records == 2

    def test_export_json(self, import_export_service):
        """Test export JSON"""
        from app.services.data_import_export import ExportFormat

        data = [
            {"code": "CLI001", "name": "Client Alpha"},
            {"code": "CLI002", "name": "Client Beta"}
        ]

        result = import_export_service.export_data(
            data=data,
            format=ExportFormat.JSON,
            options={"indent": 2}
        )

        assert result is not None
        json_data = json.loads(result.file_content.decode())
        assert len(json_data) == 2

    def test_export_excel(self, import_export_service):
        """Test export Excel"""
        from app.services.data_import_export import ExportFormat

        data = [
            {"code": "CLI001", "name": "Client Alpha", "amount": 1500.00},
            {"code": "CLI002", "name": "Client Beta", "amount": 2300.50}
        ]

        result = import_export_service.export_data(
            data=data,
            format=ExportFormat.EXCEL
        )

        assert result is not None
        assert result.file_content[:4] == b'PK\x03\x04'

    def test_export_xml(self, import_export_service):
        """Test export XML"""
        from app.services.data_import_export import ExportFormat

        data = [
            {"code": "CLI001", "name": "Client Alpha"},
            {"code": "CLI002", "name": "Client Beta"}
        ]

        result = import_export_service.export_data(
            data=data,
            format=ExportFormat.XML,
            options={"root_element": "clients", "record_element": "client"}
        )

        assert result is not None
        assert b"<clients>" in result.file_content
        assert b"<client>" in result.file_content


class TestFieldTransformer:
    """Tests pour le transformateur de champs"""

    def test_uppercase_transform(self):
        """Test transformation uppercase"""
        from app.services.data_import_export import FieldTransformer, TransformationType

        result = FieldTransformer.transform(
            "hello world",
            {"type": TransformationType.UPPERCASE.value}
        )
        assert result == "HELLO WORLD"

    def test_date_format_transform(self):
        """Test transformation de format de date"""
        from app.services.data_import_export import FieldTransformer, TransformationType

        result = FieldTransformer.transform(
            "15/01/2024",
            {
                "type": TransformationType.DATE_FORMAT.value,
                "input_format": "%d/%m/%Y",
                "output_format": "%Y-%m-%d"
            }
        )
        assert result == "2024-01-15"

    def test_number_format_transform(self):
        """Test transformation de format numérique"""
        from app.services.data_import_export import FieldTransformer, TransformationType

        result = FieldTransformer.transform(
            "1 234,56",
            {
                "type": TransformationType.NUMBER_FORMAT.value,
                "input_decimal": ",",
                "input_thousands": " ",
                "output_decimal": "."
            }
        )
        assert result == "1234.56"

    def test_lookup_transform(self):
        """Test transformation par lookup"""
        from app.services.data_import_export import FieldTransformer, TransformationType

        result = FieldTransformer.transform(
            "FA",
            {
                "type": TransformationType.LOOKUP.value,
                "table": {"FA": "invoice", "AV": "credit_note"}
            }
        )
        assert result == "invoice"


class TestFieldValidator:
    """Tests pour le validateur de champs"""

    def test_validate_siren(self):
        """Test validation SIREN"""
        from app.services.data_import_export import FieldValidator

        error = FieldValidator.validate_type("123456782", "siren", "siren")
        assert error is None

        error = FieldValidator.validate_type("123456789", "siren", "siren")
        assert error is not None

    def test_validate_email(self):
        """Test validation email"""
        from app.services.data_import_export import FieldValidator

        error = FieldValidator.validate_type("test@example.com", "email", "email")
        assert error is None

        error = FieldValidator.validate_type("invalid-email", "email", "email")
        assert error is not None

    def test_validate_iban(self):
        """Test validation IBAN"""
        from app.services.data_import_export import FieldValidator

        error = FieldValidator.validate_type("FR7630006000011234567890189", "iban", "iban")
        assert error is None


# ============================================================================
# Tests Workflow Automation
# ============================================================================

class TestWorkflowEngine:
    """Tests pour le moteur de workflow"""

    @pytest.fixture
    def workflow_engine(self):
        from app.services.workflow_automation import WorkflowEngine, get_workflow_engine
        return get_workflow_engine()

    @pytest.fixture
    def sample_workflow(self):
        from app.services.workflow_automation import (
            WorkflowDefinition, TriggerConfig, TriggerType,
            ActionConfig, ActionType, WorkflowStatus
        )
        return WorkflowDefinition(
            id="wf_test_001",
            name="Test Workflow",
            description="Workflow de test",
            version=1,
            tenant_id="tenant_001",
            entity_type="invoice",
            triggers=[
                TriggerConfig(type=TriggerType.MANUAL)
            ],
            actions=[
                ActionConfig(
                    id="action_1",
                    type=ActionType.LOG,
                    name="Log démarrage",
                    parameters={"message": "Workflow démarré", "level": "INFO"}
                ),
                ActionConfig(
                    id="action_2",
                    type=ActionType.SET_VARIABLE,
                    name="Définir variable",
                    parameters={"name": "processed", "value": True}
                )
            ],
            status=WorkflowStatus.ACTIVE
        )

    def test_register_workflow(self, workflow_engine, sample_workflow):
        """Test enregistrement de workflow"""
        workflow_engine.register_workflow(sample_workflow)

        retrieved = workflow_engine.get_workflow(sample_workflow.id)
        assert retrieved is not None
        assert retrieved.name == "Test Workflow"

    def test_activate_workflow(self, workflow_engine, sample_workflow):
        """Test activation de workflow"""
        from app.services.workflow_automation import WorkflowStatus

        sample_workflow.status = WorkflowStatus.DRAFT
        workflow_engine.register_workflow(sample_workflow)

        result = workflow_engine.activate_workflow(sample_workflow.id)
        assert result is True

        workflow = workflow_engine.get_workflow(sample_workflow.id)
        assert workflow.status == WorkflowStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_start_execution(self, workflow_engine, sample_workflow):
        """Test démarrage d'exécution"""
        workflow_engine.register_workflow(sample_workflow)

        execution_id = await workflow_engine.start_execution(
            workflow_id=sample_workflow.id,
            trigger_type=sample_workflow.triggers[0].type,
            trigger_data={"test": True},
            tenant_id="tenant_001"
        )

        assert execution_id is not None

        await asyncio.sleep(0.5)

        execution = workflow_engine.get_execution(execution_id)
        assert execution is not None

    @pytest.mark.asyncio
    async def test_trigger_event(self, workflow_engine):
        """Test déclenchement par événement"""
        from app.services.workflow_automation import (
            WorkflowDefinition, TriggerConfig, TriggerType,
            ActionConfig, ActionType, WorkflowStatus
        )

        workflow = WorkflowDefinition(
            id="wf_event_test",
            name="Event Workflow",
            description="Test événement",
            version=1,
            tenant_id="tenant_001",
            entity_type="invoice",
            triggers=[
                TriggerConfig(
                    type=TriggerType.EVENT,
                    event_name="invoice.created"
                )
            ],
            actions=[
                ActionConfig(
                    id="log_event",
                    type=ActionType.LOG,
                    name="Log événement",
                    parameters={"message": "Invoice created event received"}
                )
            ],
            status=WorkflowStatus.ACTIVE
        )

        workflow_engine.register_workflow(workflow)

        execution_ids = await workflow_engine.trigger_event(
            event_name="invoice.created",
            event_data={"invoice_id": "INV-001", "amount": 1500},
            tenant_id="tenant_001"
        )

        assert len(execution_ids) >= 1


class TestWorkflowBuilder:
    """Tests pour le builder de workflow"""

    def test_build_simple_workflow(self):
        """Test construction de workflow simple"""
        from app.services.workflow_automation import WorkflowBuilder, WorkflowStatus

        workflow = (
            WorkflowBuilder("wf_builder_test", "Test Builder", "tenant_001")
            .description("Workflow créé par le builder")
            .for_entity("invoice")
            .on_manual()
            .send_notification(
                recipients=["admin@example.com"],
                title="Test notification",
                message="Message de test"
            )
            .log("Workflow terminé")
            .build()
        )

        assert workflow.id == "wf_builder_test"
        assert workflow.name == "Test Builder"
        assert workflow.entity_type == "invoice"
        assert len(workflow.actions) == 2

    def test_build_workflow_with_variables(self):
        """Test construction avec variables"""
        from app.services.workflow_automation import WorkflowBuilder

        workflow = (
            WorkflowBuilder("wf_vars", "Variables Test", "tenant_001")
            .on_manual()
            .variable("amount", "decimal", is_input=True)
            .variable("approved", "boolean", default_value=False)
            .set_variable("processed", value=True)
            .build()
        )

        assert len(workflow.variables) == 2
        input_vars = [v for v in workflow.variables if v.is_input]
        assert len(input_vars) == 1

    def test_build_workflow_with_approval(self):
        """Test construction avec approbation"""
        from app.services.workflow_automation import WorkflowBuilder

        workflow = (
            WorkflowBuilder("wf_approval", "Approval Test", "tenant_001")
            .for_entity("expense_report")
            .on_event("expense_report.submitted")
            .require_approval(
                approvers=["manager"],
                approval_type="any",
                escalation_timeout_hours=48
            )
            .send_email(
                to="${entity.employee_email}",
                subject="Note de frais validée",
                body="Votre note a été validée"
            )
            .build()
        )

        assert len(workflow.actions) == 2
        approval_actions = [a for a in workflow.actions if a.type.value == "approval"]
        assert len(approval_actions) == 1


class TestConditionEvaluator:
    """Tests pour l'évaluateur de conditions"""

    def test_evaluate_equals(self):
        """Test condition equals"""
        from app.services.workflow_automation import ConditionEvaluator, Condition, ConditionOperator

        condition = Condition(
            field="status",
            operator=ConditionOperator.EQUALS,
            value="active"
        )

        result = ConditionEvaluator.evaluate(condition, {"status": "active"})
        assert result is True

        result = ConditionEvaluator.evaluate(condition, {"status": "inactive"})
        assert result is False

    def test_evaluate_greater_than(self):
        """Test condition greater_than"""
        from app.services.workflow_automation import ConditionEvaluator, Condition, ConditionOperator

        condition = Condition(
            field="amount",
            operator=ConditionOperator.GREATER_THAN,
            value=1000
        )

        result = ConditionEvaluator.evaluate(condition, {"amount": 1500})
        assert result is True

        result = ConditionEvaluator.evaluate(condition, {"amount": 500})
        assert result is False

    def test_evaluate_contains(self):
        """Test condition contains"""
        from app.services.workflow_automation import ConditionEvaluator, Condition, ConditionOperator

        condition = Condition(
            field="description",
            operator=ConditionOperator.CONTAINS,
            value="urgent"
        )

        result = ConditionEvaluator.evaluate(condition, {"description": "Ceci est urgent!"})
        assert result is True

    def test_evaluate_condition_group_and(self):
        """Test groupe de conditions AND"""
        from app.services.workflow_automation import (
            ConditionEvaluator, Condition, ConditionGroup, ConditionOperator
        )

        group = ConditionGroup(
            conditions=[
                Condition(field="status", operator=ConditionOperator.EQUALS, value="active"),
                Condition(field="amount", operator=ConditionOperator.GREATER_THAN, value=1000)
            ],
            logical_operator="AND"
        )

        result = ConditionEvaluator.evaluate_group(
            group,
            {"status": "active", "amount": 1500}
        )
        assert result is True

        result = ConditionEvaluator.evaluate_group(
            group,
            {"status": "active", "amount": 500}
        )
        assert result is False

    def test_evaluate_condition_group_or(self):
        """Test groupe de conditions OR"""
        from app.services.workflow_automation import (
            ConditionEvaluator, Condition, ConditionGroup, ConditionOperator
        )

        group = ConditionGroup(
            conditions=[
                Condition(field="priority", operator=ConditionOperator.EQUALS, value="high"),
                Condition(field="amount", operator=ConditionOperator.GREATER_THAN, value=10000)
            ],
            logical_operator="OR"
        )

        result = ConditionEvaluator.evaluate_group(
            group,
            {"priority": "low", "amount": 15000}
        )
        assert result is True


class TestApprovalWorkflow:
    """Tests pour les workflows d'approbation"""

    @pytest.fixture
    def workflow_engine(self):
        from app.services.workflow_automation import get_workflow_engine
        return get_workflow_engine()

    @pytest.mark.asyncio
    async def test_approval_request_created(self, workflow_engine):
        """Test création de demande d'approbation"""
        from app.services.workflow_automation import (
            WorkflowDefinition, TriggerConfig, TriggerType,
            ActionConfig, ActionType, WorkflowStatus, ApprovalStatus
        )

        workflow = WorkflowDefinition(
            id="wf_approval_test",
            name="Approval Test",
            description="Test approbation",
            version=1,
            tenant_id="tenant_001",
            entity_type="purchase_order",
            triggers=[TriggerConfig(type=TriggerType.MANUAL)],
            actions=[
                ActionConfig(
                    id="approval_step",
                    type=ActionType.APPROVAL,
                    name="Approbation achat",
                    parameters={
                        "approvers": ["manager_1", "manager_2"],
                        "approval_type": "any"
                    }
                )
            ],
            status=WorkflowStatus.ACTIVE
        )

        workflow_engine.register_workflow(workflow)

        execution_id = await workflow_engine.start_execution(
            workflow_id=workflow.id,
            trigger_type=TriggerType.MANUAL,
            trigger_data={},
            tenant_id="tenant_001",
            entity_type="purchase_order",
            entity_id="PO-001"
        )

        await asyncio.sleep(0.5)

        pending = workflow_engine.get_pending_approvals(
            user_id="manager_1",
            tenant_id="tenant_001"
        )

        assert len(pending) >= 1

    @pytest.mark.asyncio
    async def test_process_approval(self, workflow_engine):
        """Test traitement d'approbation"""
        from app.services.workflow_automation import (
            WorkflowDefinition, TriggerConfig, TriggerType,
            ActionConfig, ActionType, WorkflowStatus, ExecutionStatus
        )

        workflow = WorkflowDefinition(
            id="wf_process_approval",
            name="Process Approval",
            description="Test process approval",
            version=1,
            tenant_id="tenant_001",
            entity_type="expense",
            triggers=[TriggerConfig(type=TriggerType.MANUAL)],
            actions=[
                ActionConfig(
                    id="approval",
                    type=ActionType.APPROVAL,
                    name="Approval",
                    parameters={"approvers": ["approver_1"], "approval_type": "any"}
                ),
                ActionConfig(
                    id="notify",
                    type=ActionType.LOG,
                    name="Log approved",
                    parameters={"message": "Expense approved"}
                )
            ],
            status=WorkflowStatus.ACTIVE
        )

        workflow_engine.register_workflow(workflow)

        execution_id = await workflow_engine.start_execution(
            workflow_id=workflow.id,
            trigger_type=TriggerType.MANUAL,
            trigger_data={},
            tenant_id="tenant_001"
        )

        await asyncio.sleep(0.5)

        pending = workflow_engine.get_pending_approvals("approver_1", "tenant_001")
        if pending:
            result = await workflow_engine.process_approval(
                request_id=pending[0].id,
                user_id="approver_1",
                approved=True,
                comment="Approuvé"
            )
            assert result is True


# ============================================================================
# Tests d'Intégration
# ============================================================================

class TestBusinessServicesIntegration:
    """Tests d'intégration des services métier"""

    @pytest.mark.asyncio
    async def test_import_and_report_workflow(self):
        """Test flux import -> rapport"""
        from app.services.data_import_export import (
            get_import_export_service, ImportFormat, FieldMapping
        )
        from app.services.reporting_engine import (
            get_reporting_engine, ReportTemplate, ReportField,
            ReportParameters, ReportFormat
        )

        import_service = get_import_export_service()
        report_engine = get_reporting_engine()

        csv_data = b"""code;nom;montant
CLI001;Alpha;1500
CLI002;Beta;2300"""

        mappings = [
            FieldMapping(source_field="code", target_field="code", data_type="string"),
            FieldMapping(source_field="nom", target_field="name", data_type="string"),
            FieldMapping(source_field="montant", target_field="amount", data_type="decimal")
        ]

        imported_records = []

        async def handler(record):
            imported_records.append(record)
            return f"rec_{len(imported_records)}"

        result = await import_service.import_data(
            content=csv_data,
            format=ImportFormat.CSV,
            field_mappings=mappings,
            entity_handler=handler,
            options={"delimiter": ";"},
            tenant_id="tenant_001"
        )

        assert result.successful_rows == 2

        template = ReportTemplate(
            id="tpl_import_report",
            name="Import Report",
            description="Report of imported data",
            category="import",
            format_default="csv",
            fields=[
                ReportField(name="code", label="Code", data_type="string"),
                ReportField(name="name", label="Nom", data_type="string"),
                ReportField(name="amount", label="Montant", data_type="decimal")
            ],
            tenant_id="tenant_001"
        )

        report_engine.register_template(template)

        params = ReportParameters(
            template_id=template.id,
            format=ReportFormat.JSON,
            data=imported_records,
            tenant_id="tenant_001"
        )

        report = await report_engine.generate_report(params)
        assert report is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
