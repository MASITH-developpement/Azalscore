"""
AZALSCORE - Workflow Automation Module
=======================================
Automatisation des processus métier avec workflows configurables.

Structure modulaire refactorisée depuis workflow_automation.py (2,079 lignes)
vers une architecture avec séparation des responsabilités.

Modules:
- types: Enums et dataclasses
- handlers: Handlers d'actions (email, notification, http, script, etc.)
- evaluator: Évaluateur de conditions
- engine: Moteur d'exécution principal
- builder: Builder DSL pour workflows
- templates: Templates prédéfinis

@module workflow_automation
"""
from .types import (
    WorkflowStatus,
    ExecutionStatus,
    TriggerType,
    ActionType,
    ConditionOperator,
    ApprovalStatus,
    WorkflowVariable,
    Condition,
    ConditionGroup,
    TriggerConfig,
    ActionConfig,
    ApprovalConfig,
    WorkflowDefinition,
    ActionResult,
    ApprovalRequest,
    WorkflowExecution,
    ScheduledWorkflow,
)
from .handlers import (
    ActionHandler,
    SendEmailHandler,
    SendNotificationHandler,
    UpdateRecordHandler,
    CreateRecordHandler,
    HttpRequestHandler,
    ExecuteScriptHandler,
    DelayHandler,
    SafeExpressionEvaluator,
    SetVariableHandler,
    LogHandler,
)
from .evaluator import ConditionEvaluator
from .engine import WorkflowEngine, get_workflow_engine
from .builder import WorkflowBuilder
from .templates import (
    create_invoice_approval_workflow,
    create_expense_report_workflow,
    create_customer_onboarding_workflow,
    create_purchase_order_workflow,
    create_contract_renewal_workflow,
)


__all__ = [
    # Types / Enums
    "WorkflowStatus",
    "ExecutionStatus",
    "TriggerType",
    "ActionType",
    "ConditionOperator",
    "ApprovalStatus",
    # Data Classes
    "WorkflowVariable",
    "Condition",
    "ConditionGroup",
    "TriggerConfig",
    "ActionConfig",
    "ApprovalConfig",
    "WorkflowDefinition",
    "ActionResult",
    "ApprovalRequest",
    "WorkflowExecution",
    "ScheduledWorkflow",
    # Handlers
    "ActionHandler",
    "SendEmailHandler",
    "SendNotificationHandler",
    "UpdateRecordHandler",
    "CreateRecordHandler",
    "HttpRequestHandler",
    "ExecuteScriptHandler",
    "DelayHandler",
    "SafeExpressionEvaluator",
    "SetVariableHandler",
    "LogHandler",
    # Evaluator
    "ConditionEvaluator",
    # Engine
    "WorkflowEngine",
    "get_workflow_engine",
    # Builder
    "WorkflowBuilder",
    # Templates
    "create_invoice_approval_workflow",
    "create_expense_report_workflow",
    "create_customer_onboarding_workflow",
    "create_purchase_order_workflow",
    "create_contract_renewal_workflow",
]
