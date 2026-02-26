"""
AZALSCORE - Tests Moteur d'Orchestration
=========================================
Tests unitaires pour le moteur d'orchestration DAG.
"""
from __future__ import annotations

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from app.orchestration.engine import (
    OrchestrationEngine,
    ExecutionResult,
    StepResult,
    StepStatus,
    ExecutionStatus,
    execute_dag,
    get_engine,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def engine():
    """Instance du moteur d'orchestration."""
    return OrchestrationEngine()


@pytest.fixture
def simple_dag():
    """DAG simple avec un seul step."""
    return {
        "module_id": "test.simple_dag",
        "version": "1.0.0",
        "steps": [
            {
                "id": "step1",
                "use": "test.calculator.add@1.0.0",
                "inputs": {
                    "a": 10,
                    "b": 20
                }
            }
        ]
    }


@pytest.fixture
def multi_step_dag():
    """DAG avec plusieurs steps et dependances."""
    return {
        "module_id": "test.multi_step",
        "version": "1.0.0",
        "steps": [
            {
                "id": "calculate",
                "use": "test.calculator.multiply@1.0.0",
                "inputs": {
                    "a": "{{context.price}}",
                    "b": "{{context.quantity}}"
                }
            },
            {
                "id": "apply_discount",
                "use": "test.calculator.subtract@1.0.0",
                "inputs": {
                    "value": "{{calculate.result}}",
                    "discount": "{{context.discount}}"
                }
            }
        ]
    }


@pytest.fixture
def conditional_dag():
    """DAG avec conditions."""
    return {
        "module_id": "test.conditional",
        "version": "1.0.0",
        "steps": [
            {
                "id": "check_value",
                "use": "test.validator.check@1.0.0",
                "inputs": {
                    "value": "{{context.amount}}"
                }
            },
            {
                "id": "high_value_action",
                "condition": "{{check_value.is_high}} == True",
                "use": "test.action.high@1.0.0",
                "inputs": {}
            },
            {
                "id": "low_value_action",
                "condition": "{{check_value.is_high}} == False",
                "use": "test.action.low@1.0.0",
                "inputs": {}
            }
        ]
    }


@pytest.fixture
def retry_dag():
    """DAG avec retry et fallback."""
    return {
        "module_id": "test.retry",
        "version": "1.0.0",
        "steps": [
            {
                "id": "unstable_step",
                "use": "test.unstable.operation@1.0.0",
                "inputs": {},
                "retry": 3,
                "timeout": 5000,
                "fallback": "test.stable.fallback@1.0.0"
            }
        ]
    }


# ============================================================================
# TESTS UNITAIRES - ENGINE
# ============================================================================

class TestOrchestrationEngine:
    """Tests du moteur d'orchestration."""

    def test_engine_initialization(self, engine):
        """Test initialisation du moteur."""
        assert engine is not None
        assert isinstance(engine.execution_trace, list)
        assert len(engine.execution_trace) == 0

    def test_singleton_pattern(self):
        """Test pattern singleton."""
        engine1 = get_engine()
        engine2 = get_engine()
        assert engine1 is engine2

    @patch('app.orchestration.engine.load_program')
    def test_execute_simple_dag(self, mock_load, engine, simple_dag):
        """Test execution d'un DAG simple."""
        # Mock du programme
        mock_program = Mock()
        mock_program.execute.return_value = {"result": 30}
        mock_load.return_value = mock_program

        result = engine.execute_dag(simple_dag, context={})

        assert result.status == ExecutionStatus.COMPLETED
        assert result.module_id == "test.simple_dag"
        assert "step1" in result.steps
        assert result.steps["step1"].status == StepStatus.COMPLETED
        assert result.steps["step1"].output == {"result": 30}

    @patch('app.orchestration.engine.load_program')
    def test_execute_with_context(self, mock_load, engine, multi_step_dag):
        """Test execution avec contexte."""
        # Mock des programmes
        mock_multiply = Mock()
        mock_multiply.execute.return_value = {"result": 500}

        mock_subtract = Mock()
        mock_subtract.execute.return_value = {"result": 450}

        mock_load.side_effect = [mock_multiply, mock_subtract]

        context = {
            "price": 100,
            "quantity": 5,
            "discount": 50
        }

        result = engine.execute_dag(multi_step_dag, context=context)

        assert result.status == ExecutionStatus.COMPLETED
        assert "calculate" in result.steps
        assert "apply_discount" in result.steps

    @patch('app.orchestration.engine.load_program')
    def test_step_failure_stops_execution(self, mock_load, engine, simple_dag):
        """Test qu'un echec arrete l'execution."""
        mock_program = Mock()
        mock_program.execute.side_effect = Exception("Test error")
        mock_load.return_value = mock_program

        result = engine.execute_dag(simple_dag, context={})

        assert result.status == ExecutionStatus.FAILED
        assert result.error is not None
        assert "Test error" in result.error

    def test_missing_program_fails(self, engine, simple_dag):
        """Test qu'un programme manquant echoue."""
        # Sans mock, le programme ne sera pas trouve
        result = engine.execute_dag(simple_dag, context={})

        assert result.status == ExecutionStatus.FAILED
        assert "step1" in result.steps
        assert result.steps["step1"].status == StepStatus.FAILED


class TestVariableResolution:
    """Tests de resolution des variables."""

    def test_resolve_context_variable(self, engine):
        """Test resolution variable context."""
        template = "{{context.price}}"
        context = {"price": 100}

        result = engine._resolve_variables(template, context)

        assert result == "100"

    def test_resolve_step_variable(self, engine):
        """Test resolution variable step."""
        template = "{{calculate.result}}"
        context = {"calculate": {"result": 500}}

        result = engine._resolve_variables(template, context)

        assert result == "500"

    def test_resolve_nested_variable(self, engine):
        """Test resolution variable imbriquee."""
        template = "{{step1.data.value}}"
        context = {"step1": {"data": {"value": 42}}}

        result = engine._resolve_variables(template, context)

        assert result == "42"

    def test_resolve_multiple_variables(self, engine):
        """Test resolution de plusieurs variables."""
        template = "Total: {{context.qty}} x {{context.price}}"
        context = {"qty": 5, "price": 10}

        result = engine._resolve_variables(template, context)

        assert result == "Total: 5 x 10"

    def test_resolve_missing_variable(self, engine):
        """Test variable manquante."""
        template = "{{context.missing}}"
        context = {}

        result = engine._resolve_variables(template, context)

        # La variable n'est pas remplacee
        assert "{{context.missing}}" in result


class TestConditionEvaluation:
    """Tests de l'evaluation des conditions."""

    @patch('app.core.safe_eval.safe_eval')
    def test_condition_true(self, mock_safe_eval, engine):
        """Test condition vraie."""
        mock_safe_eval.return_value = True
        context = {"check": {"value": 100}}

        result = engine._evaluate_condition(
            "{{check.value}} > 50",
            context
        )

        assert result is True

    @patch('app.core.safe_eval.safe_eval')
    def test_condition_false(self, mock_safe_eval, engine):
        """Test condition fausse."""
        mock_safe_eval.return_value = False
        context = {"check": {"value": 10}}

        result = engine._evaluate_condition(
            "{{check.value}} > 50",
            context
        )

        assert result is False

    def test_condition_invalid_returns_false(self, engine):
        """Test condition invalide retourne False."""
        result = engine._evaluate_condition(
            "invalid condition $$$$",
            {}
        )

        assert result is False


class TestRetryMechanism:
    """Tests du mecanisme de retry."""

    @patch('app.orchestration.engine.load_program')
    @patch('app.orchestration.engine.time.sleep')
    def test_retry_on_failure(self, mock_sleep, mock_load, engine, retry_dag):
        """Test retry apres echec."""
        mock_program = Mock()
        # Echoue 2 fois, reussit la 3eme
        mock_program.execute.side_effect = [
            Exception("Fail 1"),
            Exception("Fail 2"),
            {"result": "success"}
        ]
        mock_load.return_value = mock_program

        result = engine.execute_dag(retry_dag, context={})

        assert result.status == ExecutionStatus.COMPLETED
        assert result.steps["unstable_step"].attempts == 3

    @patch('app.orchestration.engine.load_program')
    @patch('app.orchestration.engine.time.sleep')
    def test_fallback_after_all_retries_fail(self, mock_sleep, mock_load, engine, retry_dag):
        """Test fallback apres echec de tous les retries."""
        mock_main = Mock()
        mock_main.execute.side_effect = Exception("Always fails")

        mock_fallback = Mock()
        mock_fallback.execute.return_value = {"result": "fallback_success"}

        mock_load.side_effect = [mock_main, mock_fallback]

        result = engine.execute_dag(retry_dag, context={})

        assert result.status == ExecutionStatus.COMPLETED
        assert result.steps["unstable_step"].output == {"result": "fallback_success"}


class TestInputResolution:
    """Tests de resolution des inputs."""

    def test_resolve_simple_inputs(self, engine):
        """Test resolution inputs simples."""
        inputs = {
            "price": "{{context.price}}",
            "quantity": 5
        }
        context = {"price": 100}

        result = engine._resolve_inputs(inputs, context)

        assert result["price"] == "100"
        assert result["quantity"] == 5

    def test_resolve_nested_inputs(self, engine):
        """Test resolution inputs imbriques."""
        inputs = {
            "data": {
                "value": "{{context.value}}",
                "fixed": 42
            }
        }
        context = {"value": 100}

        result = engine._resolve_inputs(inputs, context)

        assert result["data"]["value"] == "100"
        assert result["data"]["fixed"] == 42

    def test_resolve_list_inputs(self, engine):
        """Test resolution inputs liste."""
        inputs = {
            "values": ["{{context.a}}", "{{context.b}}", "fixed"]
        }
        context = {"a": 10, "b": 20}

        result = engine._resolve_inputs(inputs, context)

        assert result["values"] == ["10", "20", "fixed"]


# ============================================================================
# TESTS INTEGRATION
# ============================================================================

class TestDAGExecution:
    """Tests d'integration d'execution de DAG."""

    @patch('app.orchestration.engine.load_program')
    def test_full_dag_execution(self, mock_load, engine):
        """Test execution complete d'un DAG."""
        # Setup mocks
        programs = {
            "test.step1@1.0.0": Mock(execute=Mock(return_value={"value": 100})),
            "test.step2@1.0.0": Mock(execute=Mock(return_value={"value": 200})),
            "test.step3@1.0.0": Mock(execute=Mock(return_value={"total": 300})),
        }
        mock_load.side_effect = lambda ref: programs.get(ref, Mock())

        dag = {
            "module_id": "test.full_dag",
            "version": "1.0.0",
            "steps": [
                {"id": "step1", "use": "test.step1@1.0.0", "inputs": {}},
                {"id": "step2", "use": "test.step2@1.0.0", "inputs": {}},
                {
                    "id": "step3",
                    "use": "test.step3@1.0.0",
                    "inputs": {
                        "a": "{{step1.value}}",
                        "b": "{{step2.value}}"
                    }
                }
            ]
        }

        result = engine.execute_dag(dag, context={})

        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.steps) == 3
        assert all(s.status == StepStatus.COMPLETED for s in result.steps.values())

    @patch('app.orchestration.engine.load_program')
    @patch('app.core.safe_eval.safe_eval')
    def test_conditional_execution(self, mock_safe_eval, mock_load, engine):
        """Test execution conditionnelle."""
        mock_program = Mock()
        mock_program.execute.return_value = {"is_high": True}
        mock_load.return_value = mock_program

        # True pour high_value, False pour low_value
        mock_safe_eval.side_effect = [True, False]

        dag = {
            "module_id": "test.conditional",
            "version": "1.0.0",
            "steps": [
                {
                    "id": "check",
                    "use": "test.check@1.0.0",
                    "inputs": {}
                },
                {
                    "id": "high_action",
                    "condition": "{{check.is_high}} == True",
                    "use": "test.high@1.0.0",
                    "inputs": {}
                },
                {
                    "id": "low_action",
                    "condition": "{{check.is_high}} == False",
                    "use": "test.low@1.0.0",
                    "inputs": {}
                }
            ]
        }

        result = engine.execute_dag(dag, context={})

        assert result.steps["high_action"].status == StepStatus.COMPLETED
        assert result.steps["low_action"].status == StepStatus.SKIPPED


class TestExecutionResult:
    """Tests de ExecutionResult."""

    def test_execution_result_timing(self, engine):
        """Test que les timings sont calcules."""
        with patch('app.orchestration.engine.load_program') as mock_load:
            mock_program = Mock()
            mock_program.execute.return_value = {}
            mock_load.return_value = mock_program

            dag = {
                "module_id": "test.timing",
                "version": "1.0.0",
                "steps": [{"id": "step1", "use": "test.op@1.0.0", "inputs": {}}]
            }

            result = engine.execute_dag(dag, context={})

            assert result.started_at is not None
            assert result.completed_at is not None
            assert result.duration_ms is not None
            assert result.duration_ms >= 0


# ============================================================================
# TESTS HELPER FUNCTION
# ============================================================================

class TestExecuteDAGHelper:
    """Tests de la fonction helper execute_dag."""

    @patch('app.orchestration.engine.load_program')
    def test_execute_dag_helper(self, mock_load):
        """Test fonction helper."""
        mock_program = Mock()
        mock_program.execute.return_value = {"result": "ok"}
        mock_load.return_value = mock_program

        dag = {
            "module_id": "test.helper",
            "version": "1.0.0",
            "steps": [{"id": "step1", "use": "test.op@1.0.0", "inputs": {}}]
        }

        result = execute_dag(dag, context={"key": "value"})

        assert result is not None
        assert result.status == ExecutionStatus.COMPLETED
