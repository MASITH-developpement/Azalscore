"""
Tests pour le module Finance Approval Workflows.

Coverage:
- Service: règles, demandes, approbations, délégations
- Router: tous les endpoints
- Validation: multi-niveau, escalade, délégation
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.modules.finance.approval.service import (
    ApprovalWorkflowService,
    ApprovalRequest,
    ApprovalRule,
    ApprovalLevel,
    ApprovalAction,
    ApprovalStatus,
    DocumentType,
    ActionType,
    Delegation,
    DefaultApprovalRules,
)
from app.modules.finance.approval.router import router


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def db_session():
    """Session de base de données mockée."""
    return MagicMock()


@pytest.fixture
def tenant_id():
    """ID tenant de test."""
    return "tenant-approval-test-123"


@pytest.fixture
def service(db_session, tenant_id):
    """Service d'approbation."""
    return ApprovalWorkflowService(db=db_session, tenant_id=tenant_id)


@pytest.fixture
def app(service, tenant_id):
    """Application FastAPI de test."""
    from app.core.saas_context import SaaSContext

    test_app = FastAPI()
    test_app.include_router(router)

    def override_service():
        return service

    def override_context():
        return SaaSContext(tenant_id=tenant_id)

    from app.modules.finance.approval.router import (
        get_approval_service,
        get_saas_context,
    )

    test_app.dependency_overrides[get_approval_service] = override_service
    test_app.dependency_overrides[get_saas_context] = override_context

    return test_app


@pytest.fixture
def client(app):
    """Client de test."""
    return TestClient(app)


# =============================================================================
# TESTS SERVICE - INITIALIZATION
# =============================================================================


class TestServiceInit:
    """Tests d'initialisation du service."""

    def test_init_with_tenant_id(self, db_session, tenant_id):
        """Service s'initialise avec tenant_id."""
        service = ApprovalWorkflowService(db=db_session, tenant_id=tenant_id)
        assert service.tenant_id == tenant_id

    def test_init_requires_tenant_id(self, db_session):
        """Service requiert tenant_id."""
        with pytest.raises(ValueError, match="tenant_id est requis"):
            ApprovalWorkflowService(db=db_session, tenant_id="")

    def test_init_creates_default_rules(self, service):
        """Les règles par défaut sont créées."""
        assert len(service._rules) > 0


# =============================================================================
# TESTS SERVICE - RULES
# =============================================================================


class TestRules:
    """Tests de gestion des règles."""

    @pytest.mark.asyncio
    async def test_create_rule(self, service):
        """Création d'une règle."""
        rule = await service.create_rule(
            name="Test Rule",
            document_type=DocumentType.INVOICE,
            levels=[
                {"name": "Manager", "approvers": ["user-1"]},
                {"name": "Director", "approvers": ["user-2"]},
            ],
            min_amount=Decimal("5000"),
        )

        assert rule.name == "Test Rule"
        assert rule.document_type == DocumentType.INVOICE
        assert len(rule.levels) == 2

    @pytest.mark.asyncio
    async def test_get_rule(self, service):
        """Récupération d'une règle."""
        created = await service.create_rule(
            name="Get Test",
            document_type=DocumentType.PAYMENT,
            levels=[{"name": "Approver", "approvers": []}],
        )

        rule = await service.get_rule(created.id)
        assert rule is not None
        assert rule.id == created.id

    @pytest.mark.asyncio
    async def test_list_rules(self, service):
        """Liste des règles."""
        rules = await service.list_rules()
        assert len(rules) > 0

    @pytest.mark.asyncio
    async def test_list_rules_by_type(self, service):
        """Filtrage par type."""
        await service.create_rule(
            name="Invoice Rule",
            document_type=DocumentType.INVOICE,
            levels=[{"name": "L1", "approvers": []}],
        )

        rules = await service.list_rules(document_type=DocumentType.INVOICE)
        assert all(r.document_type == DocumentType.INVOICE for r in rules)

    @pytest.mark.asyncio
    async def test_update_rule(self, service):
        """Mise à jour d'une règle."""
        created = await service.create_rule(
            name="To Update",
            document_type=DocumentType.EXPENSE,
            levels=[{"name": "L1", "approvers": []}],
        )

        updated = await service.update_rule(
            created.id,
            name="Updated Rule",
            priority=100,
        )

        assert updated.name == "Updated Rule"
        assert updated.priority == 100

    @pytest.mark.asyncio
    async def test_delete_rule(self, service):
        """Suppression d'une règle."""
        created = await service.create_rule(
            name="To Delete",
            document_type=DocumentType.REFUND,
            levels=[{"name": "L1", "approvers": []}],
        )

        success = await service.delete_rule(created.id)
        assert success

        rule = await service.get_rule(created.id)
        assert rule is None


# =============================================================================
# TESTS SERVICE - APPROVAL REQUESTS
# =============================================================================


class TestApprovalRequests:
    """Tests des demandes d'approbation."""

    @pytest.mark.asyncio
    async def test_create_request(self, service):
        """Création d'une demande."""
        request = await service.create_approval_request(
            document_type=DocumentType.INVOICE,
            document_id="inv-001",
            document_reference="FAC-2026-001",
            amount=Decimal("5000"),
            description="Facture fournisseur",
            requestor_id="user-123",
            requestor_name="John Doe",
        )

        assert request.document_type == DocumentType.INVOICE
        assert request.amount == Decimal("5000")
        assert request.status == ApprovalStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_request(self, service):
        """Récupération d'une demande."""
        created = await service.create_approval_request(
            document_type=DocumentType.PAYMENT,
            document_id="pay-001",
            document_reference="PAY-001",
            amount=Decimal("1000"),
            description="Paiement",
            requestor_id="user-1",
        )

        request = await service.get_request(created.id)
        assert request is not None
        assert request.id == created.id

    @pytest.mark.asyncio
    async def test_list_requests(self, service):
        """Liste des demandes."""
        await service.create_approval_request(
            document_type=DocumentType.EXPENSE,
            document_id="exp-001",
            document_reference="EXP-001",
            amount=Decimal("500"),
            description="Note de frais",
            requestor_id="user-1",
        )

        requests = await service.list_requests()
        assert len(requests) >= 1

    @pytest.mark.asyncio
    async def test_list_requests_by_status(self, service):
        """Filtrage par statut."""
        requests = await service.list_requests(status=ApprovalStatus.PENDING)
        assert all(r.status == ApprovalStatus.PENDING for r in requests)


# =============================================================================
# TESTS SERVICE - APPROVAL ACTIONS
# =============================================================================


class TestApprovalActions:
    """Tests des actions d'approbation."""

    @pytest.mark.asyncio
    async def test_approve_request(self, service):
        """Approbation d'une demande."""
        # Créer une règle avec approbateur
        await service.create_rule(
            name="Test Approve",
            document_type=DocumentType.INVOICE,
            levels=[{"name": "L1", "approvers": ["approver-1"]}],
            max_amount=Decimal("1000"),
            priority=100,
        )

        request = await service.create_approval_request(
            document_type=DocumentType.INVOICE,
            document_id="inv-approve",
            document_reference="INV-APPROVE",
            amount=Decimal("500"),
            description="To approve",
            requestor_id="user-1",
        )

        result = await service.approve(
            request_id=request.id,
            approver_id="approver-1",
            approver_name="Approver One",
            comment="Approved",
        )

        assert result is not None
        assert result.status == ApprovalStatus.APPROVED
        assert "approver-1" in result.approved_by

    @pytest.mark.asyncio
    async def test_reject_request(self, service):
        """Rejet d'une demande."""
        await service.create_rule(
            name="Test Reject",
            document_type=DocumentType.PAYMENT,
            levels=[{"name": "L1", "approvers": ["rejector-1"]}],
            priority=100,
        )

        request = await service.create_approval_request(
            document_type=DocumentType.PAYMENT,
            document_id="pay-reject",
            document_reference="PAY-REJECT",
            amount=Decimal("500"),
            description="To reject",
            requestor_id="user-1",
        )

        result = await service.reject(
            request_id=request.id,
            rejector_id="rejector-1",
            reason="Budget insuffisant",
        )

        assert result is not None
        assert result.status == ApprovalStatus.REJECTED
        assert result.rejected_by == "rejector-1"

    @pytest.mark.asyncio
    async def test_add_comment(self, service):
        """Ajout de commentaire."""
        request = await service.create_approval_request(
            document_type=DocumentType.EXPENSE,
            document_id="exp-comment",
            document_reference="EXP-COMMENT",
            amount=Decimal("100"),
            description="For comment",
            requestor_id="user-1",
        )

        result = await service.add_comment(
            request_id=request.id,
            user_id="commenter-1",
            comment="Question sur ce montant",
        )

        assert result is not None
        assert len(result.actions) == 1
        assert result.actions[0].action_type == ActionType.COMMENT

    @pytest.mark.asyncio
    async def test_escalate_request(self, service):
        """Escalade d'une demande."""
        await service.create_rule(
            name="Multi Level",
            document_type=DocumentType.CONTRACT,
            levels=[
                {"name": "L1", "approvers": ["l1-approver"]},
                {"name": "L2", "approvers": ["l2-approver"]},
            ],
            priority=100,
        )

        request = await service.create_approval_request(
            document_type=DocumentType.CONTRACT,
            document_id="contract-001",
            document_reference="CTR-001",
            amount=Decimal("10000"),
            description="Contract",
            requestor_id="user-1",
        )

        result = await service.escalate(
            request_id=request.id,
            escalator_id="l1-approver",
            reason="Requires higher approval",
        )

        assert result is not None
        assert result.current_level == 2

    @pytest.mark.asyncio
    async def test_cancel_request(self, service):
        """Annulation d'une demande."""
        request = await service.create_approval_request(
            document_type=DocumentType.PURCHASE_ORDER,
            document_id="po-cancel",
            document_reference="PO-CANCEL",
            amount=Decimal("2000"),
            description="To cancel",
            requestor_id="user-cancel",
        )

        result = await service.cancel(
            request_id=request.id,
            user_id="user-cancel",
            reason="No longer needed",
        )

        assert result is not None
        assert result.status == ApprovalStatus.CANCELLED


# =============================================================================
# TESTS SERVICE - DELEGATIONS
# =============================================================================


class TestDelegations:
    """Tests des délégations."""

    @pytest.mark.asyncio
    async def test_create_delegation(self, service):
        """Création d'une délégation."""
        delegation = await service.create_delegation(
            delegator_id="manager-1",
            delegator_name="Manager One",
            delegate_id="assistant-1",
            delegate_name="Assistant One",
            document_types=[DocumentType.EXPENSE, DocumentType.INVOICE],
            max_amount=Decimal("5000"),
            reason="Vacation",
        )

        assert delegation.delegator_id == "manager-1"
        assert delegation.delegate_id == "assistant-1"
        assert len(delegation.document_types) == 2

    @pytest.mark.asyncio
    async def test_list_delegations(self, service):
        """Liste des délégations."""
        await service.create_delegation(
            delegator_id="d1",
            delegator_name="D1",
            delegate_id="d2",
            delegate_name="D2",
            document_types=[DocumentType.INVOICE],
        )

        delegations = await service.list_delegations()
        assert len(delegations) >= 1

    @pytest.mark.asyncio
    async def test_revoke_delegation(self, service):
        """Révocation d'une délégation."""
        delegation = await service.create_delegation(
            delegator_id="to-revoke",
            delegator_name="To Revoke",
            delegate_id="delegate",
            delegate_name="Delegate",
            document_types=[DocumentType.PAYMENT],
        )

        success = await service.revoke_delegation(delegation.id)
        assert success

        delegations = await service.list_delegations(
            delegator_id="to-revoke",
            active_only=True,
        )
        assert len(delegations) == 0

    @pytest.mark.asyncio
    async def test_approve_with_delegation(self, service):
        """Approbation via délégation."""
        # Créer délégation
        await service.create_delegation(
            delegator_id="original-approver",
            delegator_name="Original",
            delegate_id="delegate-approver",
            delegate_name="Delegate",
            document_types=[DocumentType.INVOICE],
        )

        # Créer règle avec original-approver
        await service.create_rule(
            name="Delegation Test",
            document_type=DocumentType.INVOICE,
            levels=[{"name": "L1", "approvers": ["original-approver"]}],
            max_amount=Decimal("500"),
            priority=200,
        )

        request = await service.create_approval_request(
            document_type=DocumentType.INVOICE,
            document_id="inv-delegate",
            document_reference="INV-DELEGATE",
            amount=Decimal("100"),
            description="Via delegation",
            requestor_id="user-1",
        )

        # Le délégué peut approuver
        result = await service.approve(
            request_id=request.id,
            approver_id="delegate-approver",
        )

        assert result is not None
        assert result.status == ApprovalStatus.APPROVED


# =============================================================================
# TESTS SERVICE - STATISTICS
# =============================================================================


class TestStatistics:
    """Tests des statistiques."""

    @pytest.mark.asyncio
    async def test_get_stats(self, service):
        """Statistiques globales."""
        stats = await service.get_stats()

        assert hasattr(stats, "total_requests")
        assert hasattr(stats, "approval_rate")
        assert hasattr(stats, "by_document_type")

    @pytest.mark.asyncio
    async def test_get_user_stats(self, service):
        """Statistiques utilisateur."""
        stats = await service.get_user_stats("user-123")

        assert "user_id" in stats
        assert "approved_count" in stats
        assert "pending_count" in stats


# =============================================================================
# TESTS ROUTER
# =============================================================================


class TestRouter:
    """Tests des endpoints."""

    def test_list_rules(self, client):
        """GET /rules."""
        response = client.get("/v3/finance/approval/rules")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_rule(self, client):
        """POST /rules."""
        response = client.post(
            "/v3/finance/approval/rules",
            json={
                "name": "Router Test Rule",
                "document_type": "invoice",
                "levels": [
                    {"name": "Level 1", "approvers": ["user-1"]},
                ],
                "min_amount": "1000",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Router Test Rule"

    def test_get_rule(self, client):
        """GET /rules/{id}."""
        # Créer d'abord
        create_response = client.post(
            "/v3/finance/approval/rules",
            json={
                "name": "Get Rule",
                "document_type": "payment",
                "levels": [{"name": "L1", "approvers": []}],
            }
        )
        rule_id = create_response.json()["id"]

        response = client.get(f"/v3/finance/approval/rules/{rule_id}")

        assert response.status_code == 200
        assert response.json()["id"] == rule_id

    def test_update_rule(self, client):
        """PUT /rules/{id}."""
        create_response = client.post(
            "/v3/finance/approval/rules",
            json={
                "name": "To Update",
                "document_type": "expense",
                "levels": [{"name": "L1", "approvers": []}],
            }
        )
        rule_id = create_response.json()["id"]

        response = client.put(
            f"/v3/finance/approval/rules/{rule_id}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    def test_delete_rule(self, client):
        """DELETE /rules/{id}."""
        create_response = client.post(
            "/v3/finance/approval/rules",
            json={
                "name": "To Delete",
                "document_type": "refund",
                "levels": [{"name": "L1", "approvers": []}],
            }
        )
        rule_id = create_response.json()["id"]

        response = client.delete(f"/v3/finance/approval/rules/{rule_id}")

        assert response.status_code == 200
        assert response.json()["success"]

    def test_list_requests(self, client):
        """GET /requests."""
        response = client.get("/v3/finance/approval/requests")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_request(self, client):
        """POST /requests."""
        response = client.post(
            "/v3/finance/approval/requests",
            json={
                "document_type": "invoice",
                "document_id": "inv-router-001",
                "document_reference": "FAC-ROUTER-001",
                "amount": "2500.00",
                "description": "Router test invoice",
                "requestor_id": "user-router",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["document_reference"] == "FAC-ROUTER-001"

    def test_approve_request(self, client):
        """POST /requests/{id}/approve."""
        # Créer demande
        create_response = client.post(
            "/v3/finance/approval/requests",
            json={
                "document_type": "expense",
                "document_id": "exp-approve",
                "document_reference": "EXP-APPROVE",
                "amount": "100.00",
                "description": "To approve",
                "requestor_id": "user-1",
            }
        )
        request_id = create_response.json()["id"]

        # Pas d'approbateur défini, donc pas autorisé
        response = client.post(
            f"/v3/finance/approval/requests/{request_id}/approve",
            json={
                "approver_id": "random-user",
            }
        )

        # Peut retourner 400 si pas autorisé
        assert response.status_code in [200, 400]

    def test_reject_request(self, client):
        """POST /requests/{id}/reject."""
        create_response = client.post(
            "/v3/finance/approval/requests",
            json={
                "document_type": "payment",
                "document_id": "pay-reject",
                "document_reference": "PAY-REJECT",
                "amount": "500.00",
                "description": "To reject",
                "requestor_id": "user-1",
            }
        )
        request_id = create_response.json()["id"]

        response = client.post(
            f"/v3/finance/approval/requests/{request_id}/reject",
            json={
                "rejector_id": "rejector-1",
                "reason": "Not approved",
            }
        )

        # Peut retourner 400 si pas autorisé
        assert response.status_code in [200, 400]

    def test_cancel_request(self, client):
        """POST /requests/{id}/cancel."""
        create_response = client.post(
            "/v3/finance/approval/requests",
            json={
                "document_type": "purchase_order",
                "document_id": "po-cancel",
                "document_reference": "PO-CANCEL",
                "amount": "1000.00",
                "description": "To cancel",
                "requestor_id": "canceller-1",
            }
        )
        request_id = create_response.json()["id"]

        response = client.post(
            f"/v3/finance/approval/requests/{request_id}/cancel",
            json={"user_id": "canceller-1"},
        )

        assert response.status_code == 200

    def test_add_comment(self, client):
        """POST /requests/{id}/comment."""
        create_response = client.post(
            "/v3/finance/approval/requests",
            json={
                "document_type": "contract",
                "document_id": "ctr-comment",
                "document_reference": "CTR-COMMENT",
                "amount": "5000.00",
                "description": "For comment",
                "requestor_id": "user-1",
            }
        )
        request_id = create_response.json()["id"]

        response = client.post(
            f"/v3/finance/approval/requests/{request_id}/comment",
            json={
                "user_id": "commenter-1",
                "comment": "Need more info",
            }
        )

        assert response.status_code == 200

    def test_get_pending(self, client):
        """GET /pending."""
        response = client.get(
            "/v3/finance/approval/pending",
            params={"user_id": "user-123"},
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_delegations(self, client):
        """GET /delegations."""
        response = client.get("/v3/finance/approval/delegations")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_delegation(self, client):
        """POST /delegations."""
        response = client.post(
            "/v3/finance/approval/delegations",
            json={
                "delegator_id": "d1",
                "delegator_name": "Delegator One",
                "delegate_id": "d2",
                "delegate_name": "Delegate Two",
                "document_types": ["invoice", "expense"],
                "max_amount": "10000",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["delegator_id"] == "d1"

    def test_revoke_delegation(self, client):
        """DELETE /delegations/{id}."""
        create_response = client.post(
            "/v3/finance/approval/delegations",
            json={
                "delegator_id": "to-revoke",
                "delegator_name": "To Revoke",
                "delegate_id": "delegate",
                "delegate_name": "Delegate",
                "document_types": ["payment"],
            }
        )
        delegation_id = create_response.json()["id"]

        response = client.delete(f"/v3/finance/approval/delegations/{delegation_id}")

        assert response.status_code == 200
        assert response.json()["success"]

    def test_get_stats(self, client):
        """GET /stats."""
        response = client.get("/v3/finance/approval/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data

    def test_get_user_stats(self, client):
        """GET /stats/user/{id}."""
        response = client.get("/v3/finance/approval/stats/user/user-123")

        assert response.status_code == 200
        assert "user_id" in response.json()

    def test_health_check(self, client):
        """GET /health."""
        response = client.get("/v3/finance/approval/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


# =============================================================================
# TESTS ENUMS
# =============================================================================


class TestEnums:
    """Tests des enums."""

    def test_document_type_values(self):
        """Valeurs de DocumentType."""
        assert DocumentType.INVOICE.value == "invoice"
        assert DocumentType.PAYMENT.value == "payment"
        assert DocumentType.EXPENSE.value == "expense"

    def test_approval_status_values(self):
        """Valeurs de ApprovalStatus."""
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"

    def test_action_type_values(self):
        """Valeurs de ActionType."""
        assert ActionType.APPROVE.value == "approve"
        assert ActionType.REJECT.value == "reject"
        assert ActionType.ESCALATE.value == "escalate"


# =============================================================================
# TESTS DEFAULT RULES
# =============================================================================


class TestDefaultRules:
    """Tests des règles par défaut."""

    def test_get_default_rules(self, tenant_id):
        """Récupération des règles par défaut."""
        rules = DefaultApprovalRules.get_default_rules(tenant_id)

        assert len(rules) >= 4
        assert all(r.tenant_id == tenant_id for r in rules)

    def test_invoice_rules_by_amount(self, tenant_id):
        """Règles factures par montant."""
        rules = DefaultApprovalRules.get_default_rules(tenant_id)
        invoice_rules = [r for r in rules if r.document_type == DocumentType.INVOICE]

        assert len(invoice_rules) >= 2


# =============================================================================
# TESTS DATACLASSES
# =============================================================================


class TestDataClasses:
    """Tests des dataclasses."""

    def test_approval_request_properties(self, tenant_id):
        """Propriétés ApprovalRequest."""
        request = ApprovalRequest(
            id="req-1",
            tenant_id=tenant_id,
            document_type=DocumentType.INVOICE,
            document_id="doc-1",
            document_reference="REF-1",
            amount=Decimal("1000"),
            currency="EUR",
            description="Test",
            requestor_id="user-1",
            current_level=2,
            total_levels=3,
        )

        assert request.is_pending
        assert request.approval_progress == "2/3"

    def test_approval_level_creation(self):
        """Création ApprovalLevel."""
        level = ApprovalLevel(
            level=1,
            name="Manager",
            approvers=["user-1", "user-2"],
            min_approvers=1,
        )

        assert level.can_delegate
        assert level.can_escalate

    def test_delegation_creation(self, tenant_id):
        """Création Delegation."""
        delegation = Delegation(
            id="del-1",
            tenant_id=tenant_id,
            delegator_id="d1",
            delegator_name="Delegator",
            delegate_id="d2",
            delegate_name="Delegate",
            document_types=[DocumentType.INVOICE],
        )

        assert delegation.is_active
        assert delegation.end_date is None
