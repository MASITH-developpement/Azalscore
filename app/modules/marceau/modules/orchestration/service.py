"""
AZALS MODULE - Marceau Orchestration Service
=============================================

Service d'orchestration et workflows inter-modules.
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.modules.marceau.models import ActionStatus, MarceauAction, ModuleName

logger = logging.getLogger(__name__)


class OrchestrationService:
    """
    Service d'orchestration Marceau.
    Coordonne les workflows entre modules, gere les taches planifiees.
    """

    def __init__(self, tenant_id: str, db: Session):
        self.tenant_id = tenant_id
        self.db = db

    async def execute_action(
        self,
        action: str,
        data: dict,
        context: list[str]
    ) -> dict:
        """Execute une action d'orchestration."""
        action_handlers = {
            "run_workflow": self._run_workflow,
            "schedule_task": self._schedule_task,
            "check_health": self._check_health,
            "generate_report": self._generate_report,
        }

        handler = action_handlers.get(action, self._unknown_action)
        return await handler(data, context)

    async def _run_workflow(self, data: dict, context: list[str]) -> dict:
        """
        Execute un workflow predéfini.

        Workflows disponibles:
        - call_to_quote: Appel -> Devis
        - call_to_intervention: Appel -> Devis -> Intervention
        - marketing_campaign: Creation campagne -> Publication -> Analyse
        """
        workflow_name = data.get("workflow")

        workflows = {
            "call_to_quote": self._workflow_call_to_quote,
            "call_to_intervention": self._workflow_call_to_intervention,
            "marketing_campaign": self._workflow_marketing_campaign,
        }

        if workflow_name not in workflows:
            return {
                "success": False,
                "error": f"Workflow inconnu: {workflow_name}",
                "available_workflows": list(workflows.keys())
            }

        return await workflows[workflow_name](data, context)

    async def _workflow_call_to_quote(self, data: dict, context: list[str]) -> dict:
        """Workflow: Appel -> Devis."""
        steps = [
            {"module": "telephonie", "action": "handle_incoming_call"},
            {"module": "telephonie", "action": "create_quote"},
        ]

        results = []
        for step in steps:
            result = {
                "step": f"{step['module']}.{step['action']}",
                "status": "pending",
            }
            results.append(result)

        return {
            "success": True,
            "workflow": "call_to_quote",
            "steps": results,
            "message": "Workflow demarre",
        }

    async def _workflow_call_to_intervention(self, data: dict, context: list[str]) -> dict:
        """Workflow: Appel -> Devis -> Intervention."""
        steps = [
            {"module": "telephonie", "action": "handle_incoming_call"},
            {"module": "telephonie", "action": "create_quote"},
            {"module": "telephonie", "action": "schedule_appointment"},
        ]

        results = []
        for step in steps:
            result = {
                "step": f"{step['module']}.{step['action']}",
                "status": "pending",
            }
            results.append(result)

        return {
            "success": True,
            "workflow": "call_to_intervention",
            "steps": results,
            "message": "Workflow demarre",
        }

    async def _workflow_marketing_campaign(self, data: dict, context: list[str]) -> dict:
        """Workflow: Marketing campagne."""
        return {
            "success": False,
            "error": "Workflow marketing non implemente - Phase 2",
            "workflow": "marketing_campaign",
        }

    async def _schedule_task(self, data: dict, context: list[str]) -> dict:
        """Planifie une tache cron."""
        from app.modules.marceau.models import MarceauScheduledTask

        task = MarceauScheduledTask(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            name=data.get("name", "Tache planifiee"),
            description=data.get("description"),
            module=ModuleName(data.get("module", "orchestration")),
            action_type=data.get("action_type", "unknown"),
            action_params=data.get("action_params", {}),
            cron_expression=data.get("cron_expression", "0 9 * * 1-5"),
            timezone=data.get("timezone", "Europe/Paris"),
            is_active=True,
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        return {
            "success": True,
            "task_id": str(task.id),
            "name": task.name,
            "cron_expression": task.cron_expression,
            "message": "Tache planifiee creee",
        }

    async def _check_health(self, data: dict, context: list[str]) -> dict:
        """Verifie la sante des modules."""
        from app.modules.marceau.config import get_or_create_marceau_config

        config = get_or_create_marceau_config(self.tenant_id, self.db)

        health = {
            "status": "healthy",
            "modules": {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        for module, enabled in config.enabled_modules.items():
            health["modules"][module] = {
                "enabled": enabled,
                "status": "ok" if enabled else "disabled",
            }

        return {
            "success": True,
            "health": health,
        }

    async def _generate_report(self, data: dict, context: list[str]) -> dict:
        """Genere un rapport d'activite."""
        from sqlalchemy import func
        from datetime import timedelta

        days = data.get("days", 7)
        start_date = datetime.utcnow() - timedelta(days=days)

        # Compter actions par module
        actions_by_module = self.db.query(
            MarceauAction.module,
            func.count(MarceauAction.id)
        ).filter(
            MarceauAction.tenant_id == self.tenant_id,
            MarceauAction.created_at >= start_date
        ).group_by(MarceauAction.module).all()

        # Compter par statut
        actions_by_status = self.db.query(
            MarceauAction.status,
            func.count(MarceauAction.id)
        ).filter(
            MarceauAction.tenant_id == self.tenant_id,
            MarceauAction.created_at >= start_date
        ).group_by(MarceauAction.status).all()

        return {
            "success": True,
            "report": {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "actions_by_module": {str(m): c for m, c in actions_by_module},
                "actions_by_status": {str(s): c for s, c in actions_by_status},
            }
        }

    async def _unknown_action(self, data: dict, context: list[str]) -> dict:
        return {
            "success": False,
            "error": "Action non reconnue",
            "module": "orchestration"
        }
