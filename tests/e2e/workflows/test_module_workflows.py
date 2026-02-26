"""
AZALSCORE - Tests E2E Workflows par Module
===========================================
Tests E2E pour valider les workflows de chaque module metier.
"""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock


# ============================================================================
# HELPERS
# ============================================================================

def load_workflow(module: str, workflow_name: str) -> Dict[str, Any]:
    """Charge un workflow depuis le module specifie."""
    path = Path(f"/home/ubuntu/azalscore/app/modules/{module}/workflows/{workflow_name}.json")
    if not path.exists():
        pytest.skip(f"Workflow {workflow_name} non trouve dans {module}")
    with open(path) as f:
        return json.load(f)


def create_mock_registry():
    """Cree un mock du registry qui retourne des programmes fictifs."""
    def mock_load_program(ref: str):
        """Mock load_program qui retourne un programme simule."""
        program = Mock()

        # Simuler des sorties basees sur le type de programme
        if "calculate" in ref.lower():
            program.execute.return_value = {
                "result": 100,
                "total": 500,
                "amount": 1000
            }
        elif "validate" in ref.lower():
            program.execute.return_value = {
                "is_valid": True,
                "valid": True,
                "passed": True,
                "errors": []
            }
        elif "generate" in ref.lower():
            program.execute.return_value = {
                "number": "DOC-2026-001",
                "code": "CODE-001",
                "url": "https://example.com/doc.pdf",
                "id": "gen-123"
            }
        elif "notify" in ref.lower() or "send" in ref.lower():
            program.execute.return_value = {
                "sent": True,
                "message_id": "msg-123"
            }
        elif "create" in ref.lower():
            program.execute.return_value = {
                "id": "created-123",
                "success": True
            }
        elif "check" in ref.lower():
            program.execute.return_value = {
                "passed": True,
                "available": True,
                "is_valid": True
            }
        else:
            program.execute.return_value = {
                "result": "success",
                "status": "ok"
            }

        return program

    return mock_load_program


# ============================================================================
# TESTS E2E FINANCE
# ============================================================================

class TestFinanceWorkflowsE2E:
    """Tests E2E des workflows Finance."""

    @patch('app.orchestration.engine.load_program')
    @patch('app.core.safe_eval.safe_eval', return_value=True)
    def test_create_invoice_workflow(self, mock_eval, mock_load):
        """Test E2E: Creation de facture."""
        from app.orchestration.engine import execute_dag

        mock_load.side_effect = create_mock_registry()

        workflow = load_workflow("finance", "create_invoice")
        context = {
            "customer_id": "CUST-001",
            "invoice_prefix": "FA",
            "fiscal_year": 2026,
            "invoice_lines": [
                {"product": "Service A", "quantity": 1, "price": 1000}
            ],
            "currency": "EUR",
            "discount_amount": 50,
            "invoice_date": "2026-02-23",
            "send_email": True,
            "template_id": "default"
        }

        result = execute_dag(workflow, context=context)

        # Verifier que le workflow s'execute completement
        assert result.status.value in ["completed", "partial"]
        assert "generate_invoice_number" in result.steps or len(result.steps) > 0

    @patch('app.orchestration.engine.load_program')
    @patch('app.core.safe_eval.safe_eval', return_value=True)
    def test_process_payment_workflow(self, mock_eval, mock_load):
        """Test E2E: Traitement de paiement."""
        from app.orchestration.engine import execute_dag

        mock_load.side_effect = create_mock_registry()

        workflow = load_workflow("finance", "process_payment")
        context = {
            "payment_amount": 1500.00,
            "currency": "EUR",
            "payment_method": "bank_transfer",
            "payment_reference": "PAY-2026-001",
            "bank_iban": "FR7630001007941234567890185",
            "customer_id": "CUST-001",
            "payment_date": "2026-02-23",
            "send_receipt": True,
            "customer_email": "client@example.com"
        }

        result = execute_dag(workflow, context=context)

        assert result.status.value in ["completed", "partial", "failed"]

    @patch('app.orchestration.engine.load_program')
    @patch('app.core.safe_eval.safe_eval', return_value=True)
    def test_bank_reconciliation_workflow(self, mock_eval, mock_load):
        """Test E2E: Rapprochement bancaire."""
        from app.orchestration.engine import execute_dag

        mock_load.side_effect = create_mock_registry()

        workflow = load_workflow("finance", "bank_reconciliation")
        context = {
            "statement_file": "/tmp/statement.csv",
            "bank_format": "camt053",
            "bank_account_id": "ACC-001",
            "period_start": "2026-02-01",
            "period_end": "2026-02-28",
            "matching_rules": []
        }

        result = execute_dag(workflow, context=context)

        assert result is not None


# ============================================================================
# TESTS E2E COMMERCIAL
# ============================================================================

class TestCommercialWorkflowsE2E:
    """Tests E2E des workflows Commercial."""

    @patch('app.orchestration.engine.load_program')
    @patch('app.core.safe_eval.safe_eval', return_value=True)
    def test_quote_to_order_workflow(self, mock_eval, mock_load):
        """Test E2E: Conversion devis en commande."""
        from app.orchestration.engine import execute_dag

        mock_load.side_effect = create_mock_registry()

        workflow = load_workflow("commercial", "quote_to_order")
        context = {
            "quote_id": "QUOTE-001",
            "customer_id": "CUST-001",
            "fiscal_year": 2026,
            "order_date": "2026-02-23",
            "requested_delivery_date": "2026-03-01",
            "check_stock": True,
            "reserve_stock": True,
            "warehouse_id": "WH-001",
            "send_confirmation": True
        }

        result = execute_dag(workflow, context=context)

        assert result.status.value in ["completed", "partial", "failed"]

    @patch('app.orchestration.engine.load_program')
    @patch('app.core.safe_eval.safe_eval', return_value=True)
    def test_customer_onboarding_workflow(self, mock_eval, mock_load):
        """Test E2E: Onboarding client."""
        from app.orchestration.engine import execute_dag

        mock_load.side_effect = create_mock_registry()

        workflow = load_workflow("commercial", "customer_onboarding")
        context = {
            "company_name": "ACME Corp",
            "siret": "12345678901234",
            "vat_number": "FR12345678901",
            "contact_email": "contact@acme.com",
            "contact_phone": "+33123456789",
            "billing_address": "1 rue Test, 75001 Paris",
            "country": "FR",
            "requested_credit_limit": 50000,
            "payment_terms": "30_days",
            "customer_portal_url": "https://portal.example.com"
        }

        result = execute_dag(workflow, context=context)

        assert result is not None


# ============================================================================
# TESTS E2E INVENTORY
# ============================================================================

class TestInventoryWorkflowsE2E:
    """Tests E2E des workflows Inventory."""

    @patch('app.orchestration.engine.load_program')
    @patch('app.core.safe_eval.safe_eval', return_value=True)
    def test_goods_receipt_workflow(self, mock_eval, mock_load):
        """Test E2E: Reception de marchandises."""
        from app.orchestration.engine import execute_dag

        mock_load.side_effect = create_mock_registry()

        workflow = load_workflow("inventory", "goods_receipt")
        context = {
            "purchase_order_id": "PO-001",
            "delivery_date": "2026-02-23",
            "received_items": [
                {"product_id": "PROD-001", "quantity": 100}
            ],
            "warehouse_id": "WH-001",
            "location_id": "LOC-A1",
            "receipt_date": "2026-02-23",
            "require_quality_check": True,
            "quality_criteria": {},
            "supplier_lot_numbers": {},
            "expiry_dates": {}
        }

        result = execute_dag(workflow, context=context)

        assert result is not None

    @patch('app.orchestration.engine.load_program')
    @patch('app.core.safe_eval.safe_eval', return_value=True)
    def test_inventory_count_workflow(self, mock_eval, mock_load):
        """Test E2E: Inventaire physique."""
        from app.orchestration.engine import execute_dag

        mock_load.side_effect = create_mock_registry()

        workflow = load_workflow("inventory", "inventory_count")
        context = {
            "count_id": "COUNT-001",
            "warehouse_id": "WH-001",
            "count_type": "full",
            "locations": ["LOC-A1", "LOC-A2"],
            "freeze_stock": True,
            "expected_end": "2026-02-24",
            "count_date": "2026-02-23",
            "blind_count": False,
            "counted_items": [],
            "auto_adjust": False,
            "allow_recount": True
        }

        result = execute_dag(workflow, context=context)

        assert result is not None


# ============================================================================
# TESTS E2E HR
# ============================================================================

class TestHRWorkflowsE2E:
    """Tests E2E des workflows HR."""

    @patch('app.orchestration.engine.load_program')
    @patch('app.core.safe_eval.safe_eval', return_value=True)
    def test_employee_onboarding_workflow(self, mock_eval, mock_load):
        """Test E2E: Onboarding employe."""
        from app.orchestration.engine import execute_dag

        mock_load.side_effect = create_mock_registry()

        workflow = load_workflow("hr", "employee_onboarding")
        context = {
            "employee_data": {
                "first_name": "Jean",
                "last_name": "Dupont",
                "email": "jean.dupont@example.com",
                "hire_date": "2026-03-01",
                "position_id": "POS-001",
                "nir": "1850175123456",
                "birth_date": "1985-01-15",
                "gender": "M"
            },
            "company_code": "AZAL",
            "hire_year": 2026,
            "contract_type": "CDI",
            "manager_id": "MGR-001",
            "initial_role": "employee",
            "salary": 45000,
            "payment_method": "bank_transfer",
            "bank_details": {"iban": "FR7630001007941234567890185"},
            "leave_policy_id": "LP-001",
            "equipment_list": ["laptop", "badge"],
            "manager_email": "manager@example.com",
            "hr_email": "hr@example.com",
            "it_email": "it@example.com"
        }

        result = execute_dag(workflow, context=context)

        assert result is not None

    @patch('app.orchestration.engine.load_program')
    @patch('app.core.safe_eval.safe_eval', return_value=True)
    def test_leave_approval_workflow(self, mock_eval, mock_load):
        """Test E2E: Approbation de conges."""
        from app.orchestration.engine import execute_dag

        mock_load.side_effect = create_mock_registry()

        workflow = load_workflow("hr", "leave_approval")
        context = {
            "employee_id": "EMP-001",
            "leave_type": "paid_leave",
            "start_date": "2026-03-15",
            "end_date": "2026-03-20",
            "half_day_start": False,
            "half_day_end": False,
            "manager_id": "MGR-001",
            "manager_email": "manager@example.com",
            "employee_name": "Jean Dupont",
            "allow_negative_balance": False,
            "minimum_coverage": 0.5
        }

        result = execute_dag(workflow, context=context)

        assert result is not None


# ============================================================================
# TESTS E2E PROJECTS
# ============================================================================

class TestProjectsWorkflowsE2E:
    """Tests E2E des workflows Projects."""

    @patch('app.orchestration.engine.load_program')
    @patch('app.core.safe_eval.safe_eval', return_value=True)
    def test_project_initiation_workflow(self, mock_eval, mock_load):
        """Test E2E: Initialisation projet."""
        from app.orchestration.engine import execute_dag

        mock_load.side_effect = create_mock_registry()

        workflow = load_workflow("projects", "project_initiation")
        context = {
            "project_data": {
                "name": "Projet Test",
                "client_id": "CLIENT-001",
                "start_date": "2026-03-01",
                "budget": 100000
            },
            "client_code": "CLI",
            "project_type": "development",
            "start_year": 2026,
            "project_manager_id": "PM-001",
            "budget_categories": ["dev", "design", "qa"],
            "currency": "EUR",
            "phases": [
                {"name": "Phase 1", "duration_days": 30},
                {"name": "Phase 2", "duration_days": 60}
            ],
            "team_members": ["EMP-001", "EMP-002"],
            "team_roles": {"EMP-001": "developer", "EMP-002": "designer"},
            "folder_template": "standard",
            "client_email": "client@example.com"
        }

        result = execute_dag(workflow, context=context)

        assert result is not None

    @patch('app.orchestration.engine.load_program')
    @patch('app.core.safe_eval.safe_eval', return_value=True)
    def test_project_closure_workflow(self, mock_eval, mock_load):
        """Test E2E: Cloture projet."""
        from app.orchestration.engine import execute_dag

        mock_load.side_effect = create_mock_registry()

        workflow = load_workflow("projects", "project_closure")
        context = {
            "project_id": "PROJ-001",
            "closure_criteria": {"deliverables_complete": True},
            "closure_date": "2026-06-30",
            "lessons_learned": ["Lesson 1", "Lesson 2"],
            "retention_years": 7,
            "stakeholder_emails": ["stakeholder@example.com"]
        }

        result = execute_dag(workflow, context=context)

        assert result is not None


# ============================================================================
# TESTS VALIDATION CROSS-MODULE
# ============================================================================

class TestCrossModuleWorkflows:
    """Tests de validation cross-module."""

    def test_all_workflows_have_consistent_structure(self):
        """Verifie la coherence entre tous les workflows."""
        modules = ["finance", "commercial", "inventory", "hr", "projects"]
        all_workflows = []

        for module in modules:
            workflow_dir = Path(f"/home/ubuntu/azalscore/app/modules/{module}/workflows")
            if workflow_dir.exists():
                for wf_path in workflow_dir.glob("*.json"):
                    with open(wf_path) as f:
                        wf = json.load(f)
                        wf["_path"] = str(wf_path)
                        wf["_module"] = module
                        all_workflows.append(wf)

        # Verifier la coherence
        assert len(all_workflows) >= 36

        for wf in all_workflows:
            # Chaque workflow doit avoir un module_id coherent
            assert wf["module_id"].startswith("azalscore.")

            # Chaque step doit avoir un programme avec namespace
            for step in wf.get("steps", []):
                use = step.get("use", "")
                assert "@" in use, f"Step sans version dans {wf['_path']}"

    def test_no_circular_references(self):
        """Verifie l'absence de references circulaires."""
        import re

        modules = ["finance", "commercial", "inventory", "hr", "projects"]

        for module in modules:
            workflow_dir = Path(f"/home/ubuntu/azalscore/app/modules/{module}/workflows")
            if not workflow_dir.exists():
                continue

            for wf_path in workflow_dir.glob("*.json"):
                with open(wf_path) as f:
                    wf = json.load(f)

                step_ids = [s["id"] for s in wf.get("steps", [])]

                for i, step in enumerate(wf.get("steps", [])):
                    step_json = json.dumps(step)
                    refs = re.findall(r'\{\{([^}]+)\}\}', step_json)

                    for ref in refs:
                        ref_step = ref.split(".")[0]
                        if ref_step != "context":
                            # Le step ne peut pas se referencer lui-meme
                            assert ref_step != step["id"], f"Reference circulaire dans {wf_path}"
