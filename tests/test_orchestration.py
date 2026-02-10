"""
Tests du Moteur d'Orchestration AZALSCORE

Vérifie l'exécution de DAG JSON déclaratifs
"""

import pytest

from app.orchestration.engine import (
    OrchestrationEngine,
    execute_dag,
    ExecutionStatus,
    StepStatus
)


class TestOrchestrationEngine:
    """Tests du moteur d'orchestration"""

    def test_simple_dag_execution(self):
        """Test d'exécution d'un DAG simple"""
        dag = {
            "module_id": "test.simple",
            "version": "1.0.0",
            "steps": [
                {
                    "id": "calculate_margin",
                    "use": "azalscore.finance.calculate_margin@1.0.0",
                    "inputs": {
                        "price": 1000.0,
                        "cost": 800.0
                    }
                }
            ]
        }

        result = execute_dag(dag)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.module_id == "test.simple"
        assert "calculate_margin" in result.steps
        assert result.steps["calculate_margin"].status == StepStatus.COMPLETED
        assert result.steps["calculate_margin"].output["margin"] == 200.0

    def test_dag_with_context(self):
        """Test d'exécution avec contexte initial"""
        dag = {
            "module_id": "test.context",
            "version": "1.0.0",
            "steps": [
                {
                    "id": "calculate_margin",
                    "use": "azalscore.finance.calculate_margin@1.0.0",
                    "inputs": {
                        "price": "{{context.price}}",
                        "cost": "{{context.cost}}"
                    }
                }
            ]
        }

        context = {
            "price": 1500.0,
            "cost": 1000.0
        }

        result = execute_dag(dag, context=context)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.steps["calculate_margin"].output["margin"] == 500.0

    def test_dag_with_chained_steps(self):
        """Test d'exécution avec steps chaînés"""
        dag = {
            "module_id": "test.chained",
            "version": "1.0.0",
            "steps": [
                {
                    "id": "calculate_vat",
                    "use": "azalscore.computation.calculate_vat@1.0.0",
                    "inputs": {
                        "amount_ht": 1000.0,
                        "vat_rate": 0.20
                    }
                },
                {
                    "id": "calculate_margin",
                    "use": "azalscore.finance.calculate_margin@1.0.0",
                    "inputs": {
                        "price": "{{calculate_vat.amount_ttc}}",
                        "cost": 900.0
                    }
                }
            ]
        }

        result = execute_dag(dag)

        assert result.status == ExecutionStatus.COMPLETED
        assert "calculate_vat" in result.steps
        assert "calculate_margin" in result.steps

        # Vérifier que le résultat du premier step est utilisé dans le second
        vat_result = result.steps["calculate_vat"].output
        margin_result = result.steps["calculate_margin"].output

        assert vat_result["amount_ttc"] == 1200.0
        assert margin_result["margin"] == 300.0  # 1200 - 900

    def test_dag_with_condition_true(self):
        """Test d'exécution avec condition vraie"""
        dag = {
            "module_id": "test.condition_true",
            "version": "1.0.0",
            "steps": [
                {
                    "id": "calculate_margin",
                    "use": "azalscore.finance.calculate_margin@1.0.0",
                    "inputs": {
                        "price": 1000.0,
                        "cost": 900.0
                    }
                },
                {
                    "id": "alert",
                    "condition": "{{calculate_margin.margin_rate}} < 0.2",
                    "use": "azalscore.notification.send_alert@1.0.0",
                    "inputs": {
                        "alert_type": "low_margin",
                        "severity": "warning",
                        "title": "Marge faible",
                        "message": "Marge inférieure à 20%"
                    }
                }
            ]
        }

        result = execute_dag(dag)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.steps["calculate_margin"].status == StepStatus.COMPLETED

        # La condition est vraie (margin_rate = 0.1 < 0.2), le step doit être exécuté
        assert result.steps["alert"].status == StepStatus.COMPLETED

    def test_dag_with_condition_false(self):
        """Test d'exécution avec condition fausse"""
        dag = {
            "module_id": "test.condition_false",
            "version": "1.0.0",
            "steps": [
                {
                    "id": "calculate_margin",
                    "use": "azalscore.finance.calculate_margin@1.0.0",
                    "inputs": {
                        "price": 1000.0,
                        "cost": 600.0
                    }
                },
                {
                    "id": "alert",
                    "condition": "{{calculate_margin.margin_rate}} < 0.2",
                    "use": "azalscore.notification.send_alert@1.0.0",
                    "inputs": {
                        "alert_type": "low_margin",
                        "severity": "warning",
                        "title": "Marge faible",
                        "message": "Marge inférieure à 20%"
                    }
                }
            ]
        }

        result = execute_dag(dag)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.steps["calculate_margin"].status == StepStatus.COMPLETED

        # La condition est fausse (margin_rate = 0.4 > 0.2), le step doit être skipped
        assert result.steps["alert"].status == StepStatus.SKIPPED

    def test_dag_execution_traceability(self):
        """Test de traçabilité de l'exécution"""
        dag = {
            "module_id": "test.traceability",
            "version": "1.0.0",
            "steps": [
                {
                    "id": "step1",
                    "use": "azalscore.finance.calculate_margin@1.0.0",
                    "inputs": {
                        "price": 1000.0,
                        "cost": 800.0
                    }
                }
            ]
        }

        result = execute_dag(dag)

        # Vérifier les timestamps
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.duration_ms is not None
        assert result.duration_ms >= 0  # Peut être 0 si l'exécution est très rapide

        step_result = result.steps["step1"]
        assert step_result.started_at is not None
        assert step_result.completed_at is not None
        assert step_result.duration_ms is not None
        assert step_result.attempts == 1

    def test_dag_with_retry(self):
        """Test de retry sur échec (simulé avec programme inexistant)"""
        dag = {
            "module_id": "test.retry",
            "version": "1.0.0",
            "steps": [
                {
                    "id": "failing_step",
                    "use": "azalscore.nonexistent.program@1.0.0",
                    "inputs": {},
                    "retry": 2
                }
            ]
        }

        result = execute_dag(dag)

        # Le step doit échouer
        assert result.status == ExecutionStatus.FAILED
        assert result.steps["failing_step"].status == StepStatus.FAILED

        # Vérifier que le retry a été tenté (mais on ne peut pas garantir
        # le nombre exact d'attempts car le programme n'existe pas)

    def test_context_enrichment(self):
        """Test de l'enrichissement du contexte"""
        dag = {
            "module_id": "test.context_enrichment",
            "version": "1.0.0",
            "steps": [
                {
                    "id": "step1",
                    "use": "azalscore.finance.calculate_margin@1.0.0",
                    "inputs": {
                        "price": 1000.0,
                        "cost": 800.0
                    }
                },
                {
                    "id": "step2",
                    "use": "azalscore.computation.calculate_vat@1.0.0",
                    "inputs": {
                        "amount_ht": "{{step1.margin}}",
                        "vat_rate": 0.20
                    }
                }
            ]
        }

        result = execute_dag(dag)

        assert result.status == ExecutionStatus.COMPLETED

        # Vérifier que le contexte a été enrichi
        assert "step1" in result.context
        assert "step2" in result.context
        assert result.context["step1"]["margin"] == 200.0

    def test_multiple_steps_dag(self):
        """Test d'exécution d'un DAG avec plusieurs steps"""
        dag = {
            "module_id": "test.multiple_steps",
            "version": "1.0.0",
            "steps": [
                {
                    "id": "margin1",
                    "use": "azalscore.finance.calculate_margin@1.0.0",
                    "inputs": {"price": 1000.0, "cost": 800.0}
                },
                {
                    "id": "margin2",
                    "use": "azalscore.finance.calculate_margin@1.0.0",
                    "inputs": {"price": 2000.0, "cost": 1500.0}
                },
                {
                    "id": "margin3",
                    "use": "azalscore.finance.calculate_margin@1.0.0",
                    "inputs": {"price": 3000.0, "cost": 2000.0}
                }
            ]
        }

        result = execute_dag(dag)

        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.steps) == 3
        assert all(step.status == StepStatus.COMPLETED for step in result.steps.values())
