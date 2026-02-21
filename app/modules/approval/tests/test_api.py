"""
Tests d'intégration API - Module Approval Workflow (GAP-083)

Tests des endpoints HTTP avec TestClient FastAPI.
"""
import pytest
from uuid import uuid4
from datetime import date, timedelta


class TestWorkflowAPI:
    """Tests API Workflow."""

    def test_create_workflow(self, test_client):
        """Créer un workflow."""
        data = {
            "code": f"WF-EXP-{uuid4().hex[:6]}",
            "name": "Approbation notes de frais",
            "description": "Workflow d'approbation des notes de frais",
            "approval_type": "expense_report",
            "steps": [
                {
                    "name": "Manager",
                    "step_type": "single",
                    "approvers": [{"type": "manager"}],
                    "timeout_hours": 48
                },
                {
                    "name": "DAF",
                    "step_type": "single",
                    "approvers": [{"type": "role", "role": "DAF"}],
                    "conditions": [{"field": "amount", "operator": "greater_than", "value": 500}]
                }
            ]
        }
        response = test_client.post("/approval/workflows", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["code"].startswith("WF-EXP")
        assert len(result["steps"]) == 2

    def test_list_workflows(self, test_client):
        """Lister les workflows."""
        response = test_client.get("/approval/workflows")
        assert response.status_code == 200
        result = response.json()
        assert "items" in result

    def test_get_workflow_by_id(self, test_client, workflow_id: str):
        """Récupérer un workflow par ID."""
        response = test_client.get(f"/approval/workflows/{workflow_id}")
        assert response.status_code == 200

    def test_activate_workflow(self, test_client, workflow_id: str):
        """Activer un workflow."""
        response = test_client.post(f"/approval/workflows/{workflow_id}/activate")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "active"

    def test_deactivate_workflow(self, test_client, workflow_id: str):
        """Désactiver un workflow."""
        response = test_client.post(f"/approval/workflows/{workflow_id}/deactivate")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "inactive"

    def test_add_step(self, test_client, workflow_id: str):
        """Ajouter une étape à un workflow."""
        data = {
            "name": "Nouvelle étape",
            "step_type": "single",
            "approvers": [{"type": "user", "user_id": str(uuid4())}]
        }
        response = test_client.post(f"/approval/workflows/{workflow_id}/steps", json=data)
        assert response.status_code == 201


class TestApprovalRequestAPI:
    """Tests API Approval Request."""

    def test_create_request(self, test_client, workflow_id: str):
        """Créer une demande d'approbation."""
        data = {
            "workflow_id": workflow_id,
            "entity_type": "expense_report",
            "entity_id": str(uuid4()),
            "entity_description": "Note de frais janvier 2026",
            "amount": "450.00"
        }
        response = test_client.post("/approval/requests", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["status"] == "draft"
        assert "request_number" in result

    def test_list_requests(self, test_client):
        """Lister les demandes."""
        response = test_client.get("/approval/requests")
        assert response.status_code == 200
        result = response.json()
        assert "items" in result

    def test_submit_request(self, test_client, request_id: str):
        """Soumettre une demande."""
        response = test_client.post(f"/approval/requests/{request_id}/submit")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] in ["pending", "in_progress"]

    def test_approve_request(self, test_client, request_id: str):
        """Approuver une demande."""
        data = {"comments": "Approuvé"}
        response = test_client.post(f"/approval/requests/{request_id}/approve", json=data)
        assert response.status_code == 200

    def test_reject_request(self, test_client, request_id: str):
        """Rejeter une demande."""
        data = {"comments": "Montant trop élevé"}
        response = test_client.post(f"/approval/requests/{request_id}/reject", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "rejected"

    def test_get_pending_requests(self, test_client):
        """Récupérer les demandes en attente pour l'utilisateur courant."""
        response = test_client.get("/approval/requests/pending")
        assert response.status_code == 200

    def test_get_request_history(self, test_client, request_id: str):
        """Récupérer l'historique d'une demande."""
        response = test_client.get(f"/approval/requests/{request_id}/history")
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)


class TestDelegationAPI:
    """Tests API Delegation."""

    def test_create_delegation(self, test_client):
        """Créer une délégation."""
        data = {
            "delegate_id": str(uuid4()),
            "delegate_name": "Marie Dupont",
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=14)),
            "approval_types": ["expense_report", "leave_request"],
            "reason": "Congés annuels"
        }
        response = test_client.post("/approval/delegations", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["is_active"] is True

    def test_list_delegations(self, test_client):
        """Lister les délégations."""
        response = test_client.get("/approval/delegations")
        assert response.status_code == 200

    def test_revoke_delegation(self, test_client, delegation_id: str):
        """Révoquer une délégation."""
        response = test_client.post(f"/approval/delegations/{delegation_id}/revoke")
        assert response.status_code == 200
        result = response.json()
        assert result["is_active"] is False

    def test_get_my_delegations(self, test_client):
        """Récupérer mes délégations actives."""
        response = test_client.get("/approval/delegations/my")
        assert response.status_code == 200

    def test_get_delegated_to_me(self, test_client):
        """Récupérer les délégations reçues."""
        response = test_client.get("/approval/delegations/received")
        assert response.status_code == 200


class TestWorkflowMatching:
    """Tests matching de workflow."""

    def test_find_matching_workflow(self, test_client):
        """Trouver le workflow applicable."""
        params = {
            "approval_type": "expense_report",
            "amount": "300.00"
        }
        response = test_client.get("/approval/workflows/match", params=params)
        assert response.status_code in [200, 404]  # 404 si aucun workflow actif
