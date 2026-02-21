"""
Tests de sécurité multi-tenant - Module Approval Workflow (GAP-083)

CRITIQUE: Ces tests vérifient l'isolation entre tenants.
Un échec = faille de sécurité majeure.
"""
import pytest
from uuid import uuid4, UUID
from datetime import date, timedelta
from decimal import Decimal

from app.modules.approval.models import (
    WorkflowStatus, RequestStatus, ApprovalType, ActionType
)
from app.modules.approval.repository import (
    WorkflowRepository, ApprovalRequestRepository, DelegationRepository
)


class TestWorkflowTenantIsolation:
    """Tests isolation tenant pour Workflow."""

    def test_cannot_access_other_tenant_workflow(
        self, db_session, tenant_a_id, tenant_b_id, workflow_tenant_b
    ):
        """CRITIQUE: Tenant A ne peut pas voir les workflows de tenant B."""
        repo_a = WorkflowRepository(db_session, tenant_a_id)
        result = repo_a.get_by_id(workflow_tenant_b.id)
        assert result is None, "FAILLE SECURITE: Accès cross-tenant détecté!"

    def test_cannot_list_other_tenant_workflows(
        self, db_session, tenant_a_id, tenant_b_id, workflow_tenant_a, workflow_tenant_b
    ):
        """CRITIQUE: Liste ne retourne que les workflows du tenant courant."""
        repo_a = WorkflowRepository(db_session, tenant_a_id)
        items, total = repo_a.list()

        wf_ids = [w.id for w in items]
        assert workflow_tenant_a.id in wf_ids, "Workflow du tenant A manquant"
        assert workflow_tenant_b.id not in wf_ids, "FAILLE: Workflow tenant B visible!"

    def test_code_uniqueness_per_tenant(
        self, db_session, tenant_a_id, tenant_b_id, workflow_tenant_a, workflow_tenant_b
    ):
        """Les codes sont uniques par tenant, pas globalement."""
        repo_a = WorkflowRepository(db_session, tenant_a_id)
        repo_b = WorkflowRepository(db_session, tenant_b_id)

        assert repo_a.code_exists(workflow_tenant_a.code) is True
        assert repo_b.code_exists(workflow_tenant_a.code) is False

    def test_find_matching_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, workflow_tenant_a, workflow_tenant_b
    ):
        """find_matching ne retourne que les workflows du tenant courant."""
        repo_a = WorkflowRepository(db_session, tenant_a_id)

        # Même type que workflow_tenant_b mais dans tenant A
        result = repo_a.find_matching(ApprovalType.PURCHASE_ORDER, Decimal("1000"))
        assert result is None or result.tenant_id == tenant_a_id

    def test_autocomplete_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, workflow_tenant_a, workflow_tenant_b
    ):
        """Autocomplete ne retourne que les workflows du tenant courant."""
        repo_a = WorkflowRepository(db_session, tenant_a_id)
        results = repo_a.autocomplete("WF")

        codes = [r["code"] for r in results]
        assert workflow_tenant_a.code in codes
        assert workflow_tenant_b.code not in codes


class TestApprovalRequestTenantIsolation:
    """Tests isolation tenant pour ApprovalRequest."""

    def test_cannot_access_other_tenant_request(
        self, db_session, tenant_a_id, tenant_b_id, request_tenant_b
    ):
        """CRITIQUE: Tenant A ne peut pas voir les demandes de tenant B."""
        repo_a = ApprovalRequestRepository(db_session, tenant_a_id)
        result = repo_a.get_by_id(request_tenant_b.id)
        assert result is None, "FAILLE SECURITE: Accès cross-tenant détecté!"

    def test_cannot_list_other_tenant_requests(
        self, db_session, tenant_a_id, tenant_b_id, request_tenant_a, request_tenant_b
    ):
        """CRITIQUE: Liste ne retourne que les demandes du tenant courant."""
        repo_a = ApprovalRequestRepository(db_session, tenant_a_id)
        items, total = repo_a.list()

        req_ids = [r.id for r in items]
        assert request_tenant_a.id in req_ids, "Demande du tenant A manquante"
        assert request_tenant_b.id not in req_ids, "FAILLE: Demande tenant B visible!"

    def test_get_pending_for_user_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, request_tenant_a, request_tenant_b, approver_id
    ):
        """get_pending_for_user respecte l'isolation tenant."""
        repo_a = ApprovalRequestRepository(db_session, tenant_a_id)
        pending = repo_a.get_pending_for_user(approver_id)

        req_ids = [r.id for r in pending]
        assert request_tenant_b.id not in req_ids

    def test_get_by_entity_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, request_tenant_a
    ):
        """get_by_entity respecte l'isolation tenant."""
        repo_b = ApprovalRequestRepository(db_session, tenant_b_id)
        results = repo_b.get_by_entity(request_tenant_a.entity_type, request_tenant_a.entity_id)

        assert len(results) == 0, "FAILLE: Demande d'un autre tenant visible!"

    def test_request_number_uniqueness_per_tenant(
        self, db_session, tenant_a_id, tenant_b_id, request_tenant_a
    ):
        """Les numéros de demande sont uniques par tenant."""
        repo_a = ApprovalRequestRepository(db_session, tenant_a_id)
        repo_b = ApprovalRequestRepository(db_session, tenant_b_id)

        result_a = repo_a.get_by_number(request_tenant_a.request_number)
        result_b = repo_b.get_by_number(request_tenant_a.request_number)

        assert result_a is not None
        assert result_b is None


class TestDelegationTenantIsolation:
    """Tests isolation tenant pour Delegation."""

    def test_cannot_access_other_tenant_delegation(
        self, db_session, tenant_a_id, tenant_b_id, delegation_tenant_a
    ):
        """CRITIQUE: Tenant B ne peut pas voir les délégations de tenant A."""
        repo_b = DelegationRepository(db_session, tenant_b_id)
        result = repo_b.get_by_id(delegation_tenant_a.id)
        assert result is None, "FAILLE SECURITE: Accès cross-tenant détecté!"

    def test_get_active_for_delegator_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, delegation_tenant_a, approver_id
    ):
        """get_active_for_delegator respecte l'isolation tenant."""
        repo_b = DelegationRepository(db_session, tenant_b_id)
        delegations = repo_b.get_active_for_delegator(approver_id)

        assert len(delegations) == 0

    def test_find_delegator_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, delegation_tenant_a
    ):
        """find_delegator respecte l'isolation tenant."""
        repo_b = DelegationRepository(db_session, tenant_b_id)
        result = repo_b.find_delegator(
            delegation_tenant_a.delegate_id,
            ApprovalType.EXPENSE_REPORT
        )

        assert result is None


class TestSoftDeleteIsolation:
    """Tests soft delete avec isolation tenant."""

    def test_soft_deleted_workflow_hidden_by_default(
        self, db_session, tenant_a_id, user_id, workflow_tenant_a
    ):
        """Workflow soft-deleted n'apparaît pas par défaut."""
        repo = WorkflowRepository(db_session, tenant_a_id)
        repo.soft_delete(workflow_tenant_a, user_id)

        result = repo.get_by_id(workflow_tenant_a.id)
        assert result is None

    def test_soft_deleted_visible_with_include_deleted(
        self, db_session, tenant_a_id, user_id, workflow_tenant_a
    ):
        """Workflow soft-deleted visible avec include_deleted=True."""
        repo = WorkflowRepository(db_session, tenant_a_id)
        repo.soft_delete(workflow_tenant_a, user_id)

        repo_with_deleted = WorkflowRepository(db_session, tenant_a_id, include_deleted=True)
        result = repo_with_deleted.get_by_id(workflow_tenant_a.id)
        assert result is not None
        assert result.is_deleted is True

    def test_soft_deleted_other_tenant_still_hidden(
        self, db_session, tenant_a_id, tenant_b_id, user_id, workflow_tenant_b
    ):
        """Workflow soft-deleted d'un autre tenant reste invisible."""
        repo_b = WorkflowRepository(db_session, tenant_b_id)
        repo_b.soft_delete(workflow_tenant_b, user_id)

        repo_a_with_deleted = WorkflowRepository(db_session, tenant_a_id, include_deleted=True)
        result = repo_a_with_deleted.get_by_id(workflow_tenant_b.id)
        assert result is None


class TestWorkflowActivation:
    """Tests d'activation de workflow."""

    def test_cannot_activate_empty_workflow(
        self, db_session, tenant_a_id, user_id
    ):
        """Impossible d'activer un workflow sans étapes."""
        repo = WorkflowRepository(db_session, tenant_a_id)

        workflow = repo.create({
            "code": "WF-EMPTY",
            "name": "Workflow Vide",
            "approval_type": ApprovalType.CUSTOM.value,
            "steps": []
        }, user_id)

        with pytest.raises(ValueError, match="at least one step"):
            repo.activate(workflow, user_id)

    def test_activate_workflow_with_steps(
        self, db_session, tenant_a_id, user_id, workflow_tenant_a
    ):
        """Workflow avec étapes peut être activé."""
        repo = WorkflowRepository(db_session, tenant_a_id)

        # Désactiver d'abord
        repo.deactivate(workflow_tenant_a, user_id)
        assert workflow_tenant_a.status == WorkflowStatus.INACTIVE.value

        # Réactiver
        repo.activate(workflow_tenant_a, user_id)
        assert workflow_tenant_a.status == WorkflowStatus.ACTIVE.value


class TestApprovalActions:
    """Tests des actions d'approbation."""

    def test_add_action_records_correctly(
        self, db_session, tenant_a_id, request_tenant_a, approver_id
    ):
        """Les actions sont correctement enregistrées."""
        repo = ApprovalRequestRepository(db_session, tenant_a_id)

        step_id = UUID(request_tenant_a.step_statuses[0]["step_id"])
        action = repo.add_action(
            request_tenant_a,
            step_id,
            approver_id,
            "Manager",
            ActionType.APPROVE,
            "Approuvé sans réserve",
            ip_address="192.168.1.1"
        )

        assert action.request_id == request_tenant_a.id
        assert action.approver_id == approver_id
        assert action.action_type == ActionType.APPROVE.value
        assert action.comments == "Approuvé sans réserve"
        assert action.ip_address == "192.168.1.1"

    def test_submit_request_activates_first_step(
        self, db_session, tenant_a_id, user_id, workflow_tenant_a
    ):
        """La soumission active la première étape."""
        repo = ApprovalRequestRepository(db_session, tenant_a_id)

        request = repo.create({
            "workflow_id": workflow_tenant_a.id,
            "requester_id": user_id,
            "requester_name": "Test User",
            "entity_type": "expense_report",
            "entity_id": uuid4(),
            "status": RequestStatus.DRAFT.value,
            "step_statuses": [{
                "step_id": str(workflow_tenant_a.steps[0].id),
                "step_name": "Step 1",
                "status": "pending",
                "required_approvals": 1,
                "received_approvals": 0,
                "pending_approvers": []
            }]
        }, user_id)

        submitted = repo.submit(request)

        assert submitted.status == RequestStatus.IN_PROGRESS.value
        assert submitted.submitted_at is not None
        assert submitted.step_statuses[0]["status"] == "in_progress"
