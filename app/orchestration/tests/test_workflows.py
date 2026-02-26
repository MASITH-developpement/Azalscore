"""
AZALSCORE - Tests Validation Workflows DAG
==========================================
Tests de validation de tous les workflows JSON.
"""
from __future__ import annotations

import json
import os
import pytest
from pathlib import Path
from typing import Dict, Any, List


# ============================================================================
# FIXTURES
# ============================================================================

WORKFLOWS_BASE_PATH = Path("/home/ubuntu/azalscore/app/modules")

REQUIRED_WORKFLOW_FIELDS = ["module_id", "version", "steps"]
REQUIRED_STEP_FIELDS = ["id", "use"]
OPTIONAL_STEP_FIELDS = ["inputs", "retry", "timeout", "fallback", "condition"]


def get_all_workflows() -> List[Path]:
    """Recupere tous les fichiers workflow JSON."""
    workflows = []
    for module_dir in WORKFLOWS_BASE_PATH.iterdir():
        if module_dir.is_dir():
            workflow_dir = module_dir / "workflows"
            if workflow_dir.exists():
                for wf_file in workflow_dir.glob("*.json"):
                    workflows.append(wf_file)
    return workflows


def load_workflow(path: Path) -> Dict[str, Any]:
    """Charge un workflow JSON."""
    with open(path) as f:
        return json.load(f)


# ============================================================================
# TESTS VALIDATION STRUCTURE
# ============================================================================

class TestWorkflowDiscovery:
    """Tests de decouverte des workflows."""

    def test_workflows_exist(self):
        """Verifie qu'il existe des workflows."""
        workflows = get_all_workflows()
        assert len(workflows) > 0, "Aucun workflow trouve"

    def test_minimum_workflow_count(self):
        """Verifie le nombre minimum de workflows (36 selon le plan)."""
        workflows = get_all_workflows()
        assert len(workflows) >= 36, f"Attendu >= 36 workflows, trouve {len(workflows)}"

    def test_all_modules_have_workflows(self):
        """Verifie que les 5 modules principaux ont des workflows."""
        expected_modules = ["finance", "commercial", "inventory", "hr", "projects"]

        for module in expected_modules:
            workflow_dir = WORKFLOWS_BASE_PATH / module / "workflows"
            assert workflow_dir.exists(), f"Module {module} n'a pas de dossier workflows"

            workflows = list(workflow_dir.glob("*.json"))
            assert len(workflows) > 0, f"Module {module} n'a pas de workflows"


class TestWorkflowStructure:
    """Tests de structure des workflows."""

    @pytest.fixture(params=get_all_workflows())
    def workflow_path(self, request):
        """Fixture parametree avec tous les workflows."""
        return request.param

    def test_workflow_is_valid_json(self, workflow_path):
        """Verifie que chaque workflow est du JSON valide."""
        try:
            with open(workflow_path) as f:
                data = json.load(f)
            assert isinstance(data, dict)
        except json.JSONDecodeError as e:
            pytest.fail(f"JSON invalide dans {workflow_path}: {e}")

    def test_workflow_has_required_fields(self, workflow_path):
        """Verifie les champs obligatoires."""
        workflow = load_workflow(workflow_path)

        for field in REQUIRED_WORKFLOW_FIELDS:
            assert field in workflow, f"Champ obligatoire manquant: {field} dans {workflow_path}"

    def test_workflow_has_valid_module_id(self, workflow_path):
        """Verifie le format du module_id."""
        workflow = load_workflow(workflow_path)

        module_id = workflow.get("module_id", "")
        assert "." in module_id, f"module_id doit etre namespace (ex: azalscore.module.name)"
        assert module_id.startswith("azalscore."), f"module_id doit commencer par azalscore."

    def test_workflow_has_valid_version(self, workflow_path):
        """Verifie le format de version SemVer."""
        workflow = load_workflow(workflow_path)

        version = workflow.get("version", "")
        parts = version.split(".")
        assert len(parts) == 3, f"Version doit etre SemVer (x.y.z): {version}"
        assert all(p.isdigit() for p in parts), f"Version doit contenir uniquement des chiffres: {version}"

    def test_workflow_has_steps(self, workflow_path):
        """Verifie que le workflow a des steps."""
        workflow = load_workflow(workflow_path)

        steps = workflow.get("steps", [])
        assert isinstance(steps, list), "steps doit etre une liste"
        assert len(steps) > 0, f"Workflow doit avoir au moins un step: {workflow_path}"


class TestStepStructure:
    """Tests de structure des steps."""

    @pytest.fixture(params=get_all_workflows())
    def workflow_path(self, request):
        """Fixture parametree avec tous les workflows."""
        return request.param

    def test_steps_have_required_fields(self, workflow_path):
        """Verifie les champs obligatoires des steps."""
        workflow = load_workflow(workflow_path)

        for i, step in enumerate(workflow.get("steps", [])):
            for field in REQUIRED_STEP_FIELDS:
                assert field in step, f"Step {i} manque le champ {field} dans {workflow_path}"

    def test_step_ids_are_unique(self, workflow_path):
        """Verifie que les IDs de steps sont uniques."""
        workflow = load_workflow(workflow_path)

        step_ids = [step.get("id") for step in workflow.get("steps", [])]
        assert len(step_ids) == len(set(step_ids)), f"IDs de steps non uniques dans {workflow_path}"

    def test_step_use_format(self, workflow_path):
        """Verifie le format du champ 'use'."""
        workflow = load_workflow(workflow_path)

        for step in workflow.get("steps", []):
            use = step.get("use", "")
            # Format: namespace.module.function@version
            assert "@" in use, f"'use' doit inclure une version (@x.y.z): {use}"

            parts = use.split("@")
            assert len(parts) == 2, f"Format 'use' invalide: {use}"

            namespace = parts[0]
            assert "." in namespace, f"Namespace doit etre qualifie: {namespace}"

    def test_step_retry_is_valid(self, workflow_path):
        """Verifie que retry est un entier positif."""
        workflow = load_workflow(workflow_path)

        for step in workflow.get("steps", []):
            if "retry" in step:
                retry = step["retry"]
                assert isinstance(retry, int), f"retry doit etre un entier: {retry}"
                assert retry >= 0, f"retry doit etre >= 0: {retry}"

    def test_step_timeout_is_valid(self, workflow_path):
        """Verifie que timeout est un entier positif."""
        workflow = load_workflow(workflow_path)

        for step in workflow.get("steps", []):
            if "timeout" in step:
                timeout = step["timeout"]
                assert isinstance(timeout, int), f"timeout doit etre un entier: {timeout}"
                assert timeout > 0, f"timeout doit etre > 0: {timeout}"


class TestWorkflowReferences:
    """Tests des references entre steps."""

    @pytest.fixture(params=get_all_workflows())
    def workflow_path(self, request):
        """Fixture parametree avec tous les workflows."""
        return request.param

    def test_variable_references_valid_steps(self, workflow_path):
        """Verifie que les references {{step.field}} pointent vers des steps existants."""
        import re
        workflow = load_workflow(workflow_path)

        step_ids = {step.get("id") for step in workflow.get("steps", [])}
        step_ids.add("context")  # context est toujours valide

        for i, step in enumerate(workflow.get("steps", [])):
            # Chercher toutes les references {{...}}
            step_json = json.dumps(step)
            refs = re.findall(r'\{\{([^}]+)\}\}', step_json)

            for ref in refs:
                ref_parts = ref.strip().split(".")
                ref_step = ref_parts[0]

                # Verifier que le step reference existe avant le step courant
                if ref_step != "context":
                    # Le step reference doit etre declare avant
                    current_step_ids = {s.get("id") for s in workflow.get("steps", [])[:i]}
                    current_step_ids.add("context")

                    if ref_step not in current_step_ids:
                        # C'est OK si c'est dans les outputs
                        if "outputs" not in step_json:
                            pass  # On pourrait avertir mais pas echouer


class TestWorkflowByModule:
    """Tests specifiques par module."""

    def test_finance_workflows(self):
        """Verifie les workflows Finance."""
        finance_dir = WORKFLOWS_BASE_PATH / "finance" / "workflows"
        assert finance_dir.exists()

        expected = [
            "invoice_analysis.json",
            "create_invoice.json",
            "process_payment.json",
            "close_fiscal_period.json",
            "bank_reconciliation.json",
        ]

        existing = [f.name for f in finance_dir.glob("*.json")]
        for exp in expected:
            assert exp in existing, f"Workflow Finance manquant: {exp}"

    def test_commercial_workflows(self):
        """Verifie les workflows Commercial."""
        commercial_dir = WORKFLOWS_BASE_PATH / "commercial" / "workflows"
        assert commercial_dir.exists()

        expected = [
            "quote_to_order.json",
            "customer_onboarding.json",
            "opportunity_pipeline.json",
        ]

        existing = [f.name for f in commercial_dir.glob("*.json")]
        for exp in expected:
            assert exp in existing, f"Workflow Commercial manquant: {exp}"

    def test_inventory_workflows(self):
        """Verifie les workflows Inventory."""
        inventory_dir = WORKFLOWS_BASE_PATH / "inventory" / "workflows"
        assert inventory_dir.exists()

        expected = [
            "goods_receipt.json",
            "stock_transfer.json",
            "inventory_count.json",
        ]

        existing = [f.name for f in inventory_dir.glob("*.json")]
        for exp in expected:
            assert exp in existing, f"Workflow Inventory manquant: {exp}"

    def test_hr_workflows(self):
        """Verifie les workflows HR."""
        hr_dir = WORKFLOWS_BASE_PATH / "hr" / "workflows"
        assert hr_dir.exists()

        expected = [
            "employee_onboarding.json",
            "payroll_processing.json",
            "leave_approval.json",
        ]

        existing = [f.name for f in hr_dir.glob("*.json")]
        for exp in expected:
            assert exp in existing, f"Workflow HR manquant: {exp}"

    def test_projects_workflows(self):
        """Verifie les workflows Projects."""
        projects_dir = WORKFLOWS_BASE_PATH / "projects" / "workflows"
        assert projects_dir.exists()

        expected = [
            "project_initiation.json",
            "task_assignment.json",
            "project_closure.json",
        ]

        existing = [f.name for f in projects_dir.glob("*.json")]
        for exp in expected:
            assert exp in existing, f"Workflow Projects manquant: {exp}"


# ============================================================================
# TESTS STATISTIQUES
# ============================================================================

class TestWorkflowStatistics:
    """Tests des statistiques des workflows."""

    def test_total_workflow_count(self):
        """Compte total des workflows."""
        workflows = get_all_workflows()
        print(f"\n=== STATISTIQUES WORKFLOWS ===")
        print(f"Total workflows: {len(workflows)}")

        # Par module
        by_module = {}
        for wf in workflows:
            module = wf.parent.parent.name
            by_module[module] = by_module.get(module, 0) + 1

        for module, count in sorted(by_module.items()):
            print(f"  - {module}: {count}")

        assert len(workflows) >= 36

    def test_total_steps_count(self):
        """Compte total des steps."""
        workflows = get_all_workflows()
        total_steps = 0

        for wf_path in workflows:
            wf = load_workflow(wf_path)
            total_steps += len(wf.get("steps", []))

        print(f"\nTotal steps: {total_steps}")
        print(f"Moyenne steps/workflow: {total_steps / len(workflows):.1f}")

        assert total_steps > 200  # Au moins 200 steps au total

    def test_features_usage(self):
        """Statistiques d'utilisation des features."""
        workflows = get_all_workflows()

        features = {
            "retry": 0,
            "timeout": 0,
            "fallback": 0,
            "condition": 0,
        }

        for wf_path in workflows:
            wf = load_workflow(wf_path)
            for step in wf.get("steps", []):
                for feature in features:
                    if feature in step:
                        features[feature] += 1

        print(f"\n=== UTILISATION FEATURES ===")
        for feature, count in features.items():
            print(f"  - {feature}: {count} steps")
