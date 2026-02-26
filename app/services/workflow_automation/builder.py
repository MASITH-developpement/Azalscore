"""
AZALSCORE - Workflow Automation Builder
Builder DSL pour créer des workflows de manière fluide
"""
from __future__ import annotations

from typing import Any, Optional

from .types import (
    ActionConfig,
    ActionType,
    Condition,
    ConditionGroup,
    ConditionOperator,
    TriggerConfig,
    TriggerType,
    WorkflowDefinition,
    WorkflowStatus,
    WorkflowVariable,
)


class WorkflowBuilder:
    """Builder pour créer des workflows de manière fluide."""

    def __init__(self, workflow_id: str, name: str, tenant_id: str):
        self._workflow_id = workflow_id
        self._name = name
        self._tenant_id = tenant_id
        self._description = ""
        self._entity_type: Optional[str] = None
        self._triggers: list[TriggerConfig] = []
        self._actions: list[ActionConfig] = []
        self._variables: list[WorkflowVariable] = []
        self._action_counter = 0

    def description(self, desc: str) -> "WorkflowBuilder":
        """Définit la description."""
        self._description = desc
        return self

    def for_entity(self, entity_type: str) -> "WorkflowBuilder":
        """Définit le type d'entité."""
        self._entity_type = entity_type
        return self

    def on_event(
        self,
        event_name: str,
        conditions: list[dict] = None
    ) -> "WorkflowBuilder":
        """Ajoute un déclencheur sur événement."""
        condition_group = None
        if conditions:
            condition_group = ConditionGroup(
                conditions=[
                    Condition(
                        field=c["field"],
                        operator=ConditionOperator(c["operator"]),
                        value=c["value"]
                    )
                    for c in conditions
                ]
            )

        self._triggers.append(TriggerConfig(
            type=TriggerType.EVENT,
            event_name=event_name,
            conditions=condition_group
        ))
        return self

    def on_schedule(self, schedule: str) -> "WorkflowBuilder":
        """Ajoute un déclencheur planifié."""
        self._triggers.append(TriggerConfig(
            type=TriggerType.SCHEDULED,
            schedule=schedule
        ))
        return self

    def on_manual(self) -> "WorkflowBuilder":
        """Ajoute un déclencheur manuel."""
        self._triggers.append(TriggerConfig(type=TriggerType.MANUAL))
        return self

    def variable(
        self,
        name: str,
        data_type: str = "string",
        default_value: Any = None,
        is_input: bool = False,
        is_output: bool = False
    ) -> "WorkflowBuilder":
        """Ajoute une variable."""
        self._variables.append(WorkflowVariable(
            name=name,
            value=default_value,
            data_type=data_type,
            is_input=is_input,
            is_output=is_output
        ))
        return self

    def _next_action_id(self) -> str:
        """Génère un ID d'action unique."""
        self._action_counter += 1
        return f"action_{self._action_counter}"

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        **kwargs
    ) -> "WorkflowBuilder":
        """Ajoute une action d'envoi d'email."""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.SEND_EMAIL,
            name="Envoi email",
            parameters={"to": to, "subject": subject, "body": body, **kwargs}
        )
        self._actions.append(action)
        return self

    def send_notification(
        self,
        recipients: list[str],
        title: str,
        message: str,
        channels: list[str] = None
    ) -> "WorkflowBuilder":
        """Ajoute une action de notification."""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.SEND_NOTIFICATION,
            name="Notification",
            parameters={
                "recipients": recipients,
                "title": title,
                "message": message,
                "channels": channels or ["in_app"]
            }
        )
        self._actions.append(action)
        return self

    def update_record(
        self,
        entity_type: str,
        entity_id: str,
        updates: dict
    ) -> "WorkflowBuilder":
        """Ajoute une action de mise à jour."""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.UPDATE_RECORD,
            name=f"Mise à jour {entity_type}",
            parameters={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "updates": updates
            }
        )
        self._actions.append(action)
        return self

    def create_record(
        self,
        entity_type: str,
        data: dict
    ) -> "WorkflowBuilder":
        """Ajoute une action de création."""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.CREATE_RECORD,
            name=f"Création {entity_type}",
            parameters={"entity_type": entity_type, "data": data}
        )
        self._actions.append(action)
        return self

    def require_approval(
        self,
        approvers: list[str],
        approval_type: str = "any",
        **kwargs
    ) -> "WorkflowBuilder":
        """Ajoute une étape d'approbation."""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.APPROVAL,
            name="Approbation requise",
            parameters={
                "approvers": approvers,
                "approval_type": approval_type,
                **kwargs
            }
        )
        self._actions.append(action)
        return self

    def delay(self, seconds: int = 0, until: str = None) -> "WorkflowBuilder":
        """Ajoute un délai."""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.DELAY,
            name="Délai",
            parameters={"delay_seconds": seconds, "delay_until": until}
        )
        self._actions.append(action)
        return self

    def set_variable(
        self,
        name: str,
        value: Any = None,
        expression: str = None
    ) -> "WorkflowBuilder":
        """Ajoute une action de définition de variable."""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.SET_VARIABLE,
            name=f"Définir {name}",
            parameters={"name": name, "value": value, "expression": expression}
        )
        self._actions.append(action)
        return self

    def log(self, message: str, level: str = "INFO") -> "WorkflowBuilder":
        """Ajoute une action de log."""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.LOG,
            name="Log",
            parameters={"message": message, "level": level}
        )
        self._actions.append(action)
        return self

    def http_request(
        self,
        url: str,
        method: str = "GET",
        headers: dict = None,
        body: Any = None
    ) -> "WorkflowBuilder":
        """Ajoute une requête HTTP."""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.HTTP_REQUEST,
            name=f"HTTP {method}",
            parameters={
                "url": url,
                "method": method,
                "headers": headers or {},
                "body": body
            }
        )
        self._actions.append(action)
        return self

    def execute_script(self, script: str) -> "WorkflowBuilder":
        """Ajoute une exécution de script."""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.EXECUTE_SCRIPT,
            name="Script",
            parameters={"script": script}
        )
        self._actions.append(action)
        return self

    def call_workflow(
        self,
        workflow_id: str,
        input_mapping: dict = None,
        wait_completion: bool = True
    ) -> "WorkflowBuilder":
        """Ajoute un appel à un sous-workflow."""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.CALL_WORKFLOW,
            name=f"Appel {workflow_id}",
            parameters={
                "workflow_id": workflow_id,
                "input_mapping": input_mapping or {},
                "wait_completion": wait_completion
            }
        )
        self._actions.append(action)
        return self

    def build(self) -> WorkflowDefinition:
        """Construit le workflow."""
        # Chaîner les actions automatiquement
        for i, action in enumerate(self._actions[:-1]):
            if not action.next_action_id:
                action.next_action_id = self._actions[i + 1].id

        return WorkflowDefinition(
            id=self._workflow_id,
            name=self._name,
            description=self._description,
            version=1,
            tenant_id=self._tenant_id,
            entity_type=self._entity_type,
            triggers=self._triggers,
            actions=self._actions,
            variables=self._variables,
            status=WorkflowStatus.DRAFT
        )
