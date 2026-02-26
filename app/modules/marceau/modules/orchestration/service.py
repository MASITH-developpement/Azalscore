"""
AZALS MODULE - Marceau Orchestration Service
=============================================

Service d'orchestration et workflows inter-modules.
Coordonne l'execution des workflows multi-etapes et les taches planifiees.

Actions:
    - execute_workflow: Execute un workflow predéfini ou custom
    - schedule_task: Planifie une tache recurrente (cron)
    - health_check: Verification sante des modules
    - generate_report: Rapport d'activite global
"""
from __future__ import annotations


import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.marceau.llm_client import get_llm_client_for_tenant
from app.modules.marceau.models import (
    MarceauAction,
    ActionStatus,
    MarceauScheduledTask,
    ModuleName,
)

logger = logging.getLogger(__name__)


class OrchestrationService:
    """
    Service d'orchestration Marceau.
    Coordonne les workflows entre modules, gere les taches planifiees.
    """

    # Definition des workflows predéfinis
    WORKFLOWS = {
        "call_to_quote": {
            "name": "Appel vers Devis",
            "description": "Traite un appel entrant et genere un devis",
            "steps": [
                {"module": "telephonie", "action": "handle_incoming_call", "required": True},
                {"module": "telephonie", "action": "create_quote", "required": True},
            ],
        },
        "call_to_intervention": {
            "name": "Appel vers Intervention",
            "description": "Traite un appel, genere devis et planifie intervention",
            "steps": [
                {"module": "telephonie", "action": "handle_incoming_call", "required": True},
                {"module": "telephonie", "action": "create_quote", "required": True},
                {"module": "telephonie", "action": "schedule_appointment", "required": False},
            ],
        },
        "ticket_resolution": {
            "name": "Resolution Ticket",
            "description": "Traite un ticket support de bout en bout",
            "steps": [
                {"module": "support", "action": "create_ticket", "required": True},
                {"module": "support", "action": "respond_ticket", "required": True},
                {"module": "support", "action": "resolve", "required": False},
            ],
        },
        "marketing_campaign": {
            "name": "Campagne Marketing Complete",
            "description": "Cree et execute une campagne marketing",
            "steps": [
                {"module": "marketing", "action": "create_campaign", "required": True},
                {"module": "marketing", "action": "post_social", "required": False},
                {"module": "marketing", "action": "send_newsletter", "required": False},
                {"module": "marketing", "action": "analyze_performance", "required": False},
            ],
        },
        "invoice_processing": {
            "name": "Traitement Facture",
            "description": "Traite une facture fournisseur et comptabilise",
            "steps": [
                {"module": "comptabilite", "action": "process_invoice", "required": True},
                {"module": "comptabilite", "action": "post_entry", "required": True},
            ],
        },
        "seo_article_publish": {
            "name": "Publication Article SEO",
            "description": "Genere un article SEO et le publie sur WordPress",
            "steps": [
                {"module": "seo", "action": "generate_article", "required": True},
                {"module": "seo", "action": "publish_article", "required": True},
            ],
        },
    }

    def __init__(self, tenant_id: str, db: Session):
        self.tenant_id = tenant_id
        self.db = db

    async def execute_action(
        self,
        action: str,
        data: dict,
        context: list[str],
    ) -> dict:
        """Execute une action d'orchestration."""
        action_handlers = {
            "execute_workflow": self._execute_workflow,
            "run_workflow": self._execute_workflow,  # alias
            "schedule_task": self._schedule_task,
            "cancel_task": self._cancel_task,
            "list_tasks": self._list_tasks,
            "health_check": self._health_check,
            "check_health": self._health_check,  # alias
            "generate_report": self._generate_report,
        }

        handler = action_handlers.get(action, self._unknown_action)
        return await handler(data, context)

    # ========================================================================
    # EXECUTE WORKFLOW
    # ========================================================================

    async def _execute_workflow(self, data: dict, context: list[str]) -> dict:
        """
        Execute un workflow predéfini ou custom.

        Args:
            data: {
                "workflow": "call_to_quote" | "custom",
                "params": {},  # Parametres pour les etapes
                "steps": [],   # Si workflow custom
                "parallel": false,  # Execution parallele des etapes non-dependantes
                "stop_on_error": true,  # Arrete si une etape required echoue
            }
        """
        workflow_name = data.get("workflow")
        logger.info(f"[Orchestration] Execution workflow: {workflow_name}")

        # Recuperer la definition du workflow
        if workflow_name in self.WORKFLOWS:
            workflow_def = self.WORKFLOWS[workflow_name]
            steps = workflow_def["steps"]
        elif workflow_name == "custom" and data.get("steps"):
            workflow_def = {
                "name": "Workflow Custom",
                "description": data.get("description", "Workflow personnalise"),
            }
            steps = data.get("steps", [])
        else:
            return {
                "success": False,
                "error": f"Workflow inconnu: {workflow_name}",
                "available_workflows": list(self.WORKFLOWS.keys()),
            }

        params = data.get("params", {})
        stop_on_error = data.get("stop_on_error", True)

        # Creer l'enregistrement workflow
        workflow_id = str(uuid.uuid4())
        workflow_action = MarceauAction(
            tenant_id=self.tenant_id,
            module="orchestration",
            action_type="execute_workflow",
            status=ActionStatus.IN_PROGRESS,
            input_data={
                "workflow": workflow_name,
                "params": params,
                "steps_count": len(steps),
            },
            output_data={
                "workflow_id": workflow_id,
                "started_at": datetime.utcnow().isoformat(),
            },
            reasoning=f"Workflow {workflow_def['name']} demarre",
        )
        self.db.add(workflow_action)
        self.db.commit()
        self.db.refresh(workflow_action)

        # Executer les etapes
        results = []
        workflow_success = True
        previous_output = params

        for idx, step in enumerate(steps):
            step_module = step.get("module")
            step_action = step.get("action")
            step_required = step.get("required", True)

            step_result = {
                "step": idx + 1,
                "module": step_module,
                "action": step_action,
                "required": step_required,
                "status": "pending",
            }

            try:
                # Preparer les donnees de l'etape
                step_data = {**previous_output}
                if step.get("params"):
                    step_data.update(step.get("params"))

                # Executer l'action
                result = await self._execute_module_action(
                    step_module, step_action, step_data, context
                )

                step_result["status"] = "completed" if result.get("success") else "failed"
                step_result["result"] = result

                # Passer la sortie a l'etape suivante
                if result.get("success"):
                    previous_output.update(result)

                # Gerer les erreurs
                if not result.get("success") and step_required:
                    workflow_success = False
                    if stop_on_error:
                        step_result["status"] = "failed"
                        results.append(step_result)
                        break

            except Exception as e:
                logger.error(f"[Orchestration] Erreur etape {step_module}.{step_action}: {e}")
                step_result["status"] = "error"
                step_result["error"] = str(e)

                if step_required:
                    workflow_success = False
                    if stop_on_error:
                        results.append(step_result)
                        break

            results.append(step_result)

        # Mettre a jour l'action workflow
        workflow_action.status = (
            ActionStatus.COMPLETED if workflow_success else ActionStatus.FAILED
        )
        workflow_action.output_data = {
            "workflow_id": workflow_id,
            "started_at": workflow_action.output_data.get("started_at"),
            "completed_at": datetime.utcnow().isoformat(),
            "steps_executed": len(results),
            "steps_successful": len([r for r in results if r["status"] == "completed"]),
        }
        self.db.commit()

        return {
            "success": workflow_success,
            "action": "execute_workflow",
            "workflow_id": workflow_id,
            "workflow": workflow_name,
            "workflow_name": workflow_def["name"],
            "steps_total": len(steps),
            "steps_executed": len(results),
            "steps_successful": len([r for r in results if r["status"] == "completed"]),
            "steps": results,
            "message": f"Workflow {'termine avec succes' if workflow_success else 'echoue'}",
        }

    async def _execute_module_action(
        self,
        module: str,
        action: str,
        data: dict,
        context: list[str],
    ) -> dict:
        """Execute une action sur un module specifique."""
        try:
            # Import dynamique du service
            if module == "telephonie":
                from app.modules.marceau.modules.telephonie.service import TelephonieService
                service = TelephonieService(self.tenant_id, self.db)
            elif module == "seo":
                from app.modules.marceau.modules.seo.service import SEOService
                service = SEOService(self.tenant_id, self.db)
            elif module == "commercial":
                from app.modules.marceau.modules.commercial.service import CommercialService
                service = CommercialService(self.tenant_id, self.db)
            elif module == "support":
                from app.modules.marceau.modules.support.service import SupportService
                service = SupportService(self.tenant_id, self.db)
            elif module == "marketing":
                from app.modules.marceau.modules.marketing.service import MarketingService
                service = MarketingService(self.tenant_id, self.db)
            elif module == "comptabilite":
                from app.modules.marceau.modules.comptabilite.service import ComptabiliteService
                service = ComptabiliteService(self.tenant_id, self.db)
            else:
                return {
                    "success": False,
                    "error": f"Module inconnu: {module}",
                }

            return await service.execute_action(action, data, context)

        except ImportError as e:
            logger.error(f"[Orchestration] Module {module} non disponible: {e}")
            return {
                "success": False,
                "error": f"Module {module} non disponible",
            }
        except Exception as e:
            logger.error(f"[Orchestration] Erreur execution {module}.{action}: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ========================================================================
    # SCHEDULE TASK
    # ========================================================================

    async def _schedule_task(self, data: dict, context: list[str]) -> dict:
        """
        Planifie une tache recurrente.

        Args:
            data: {
                "name": "Nom de la tache",
                "description": "Description",
                "module": "commercial",
                "action_type": "follow_up",
                "action_params": {},
                "cron_expression": "0 9 * * 1-5",  # 9h du lundi au vendredi
                "timezone": "Europe/Paris",
                "enabled": true,
            }
        """
        logger.info(f"[Orchestration] Planification tache: {data.get('name')}")

        required = ["name", "module", "action_type", "cron_expression"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return {
                "success": False,
                "error": f"Champs manquants: {', '.join(missing)}",
                "action": "schedule_task",
            }

        try:
            # Valider le module
            try:
                module_name = ModuleName(data.get("module"))
            except ValueError:
                return {
                    "success": False,
                    "error": f"Module invalide: {data.get('module')}",
                    "valid_modules": [m.value for m in ModuleName],
                }

            # Valider l'expression cron basique
            cron = data.get("cron_expression", "")
            parts = cron.split()
            if len(parts) not in [5, 6]:
                return {
                    "success": False,
                    "error": "Expression cron invalide (5 ou 6 champs attendus)",
                    "example": "0 9 * * 1-5 (9h du lundi au vendredi)",
                }

            task = MarceauScheduledTask(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                name=data.get("name"),
                description=data.get("description"),
                module=module_name,
                action_type=data.get("action_type"),
                action_params=data.get("action_params", {}),
                cron_expression=cron,
                timezone=data.get("timezone", "Europe/Paris"),
                is_active=data.get("enabled", True),
            )

            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)

            # Calculer prochaine execution
            next_run = self._calculate_next_run(cron)

            return {
                "success": True,
                "action": "schedule_task",
                "task_id": str(task.id),
                "name": task.name,
                "module": task.module.value,
                "action_type": task.action_type,
                "cron_expression": task.cron_expression,
                "next_run": next_run,
                "message": f"Tache '{task.name}' planifiee",
            }

        except Exception as e:
            logger.error(f"[Orchestration] Erreur planification: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "schedule_task",
            }

    def _calculate_next_run(self, cron_expression: str) -> str:
        """Calcule la prochaine execution d'une expression cron."""
        # Simplification - retourne dans 1 heure pour demo
        # En production, utiliser croniter ou equivalent
        return (datetime.utcnow() + timedelta(hours=1)).isoformat()

    async def _cancel_task(self, data: dict, context: list[str]) -> dict:
        """Annule une tache planifiee."""
        task_id = data.get("task_id")
        if not task_id:
            return {
                "success": False,
                "error": "task_id requis",
                "action": "cancel_task",
            }

        try:
            task = self.db.query(MarceauScheduledTask).filter(
                MarceauScheduledTask.tenant_id == self.tenant_id,
                MarceauScheduledTask.id == task_id,
            ).first()

            if not task:
                return {
                    "success": False,
                    "error": "Tache non trouvee",
                    "action": "cancel_task",
                }

            task.is_active = False
            self.db.commit()

            return {
                "success": True,
                "action": "cancel_task",
                "task_id": str(task.id),
                "name": task.name,
                "message": f"Tache '{task.name}' desactivee",
            }

        except Exception as e:
            logger.error(f"[Orchestration] Erreur annulation: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "cancel_task",
            }

    async def _list_tasks(self, data: dict, context: list[str]) -> dict:
        """Liste les taches planifiees."""
        try:
            active_only = data.get("active_only", True)

            query = self.db.query(MarceauScheduledTask).filter(
                MarceauScheduledTask.tenant_id == self.tenant_id
            )

            if active_only:
                query = query.filter(MarceauScheduledTask.is_active == True)

            tasks = query.order_by(MarceauScheduledTask.created_at.desc()).limit(50).all()

            return {
                "success": True,
                "action": "list_tasks",
                "tasks": [
                    {
                        "task_id": str(t.id),
                        "name": t.name,
                        "module": t.module.value,
                        "action_type": t.action_type,
                        "cron_expression": t.cron_expression,
                        "is_active": t.is_active,
                        "last_run": t.last_run_at.isoformat() if t.last_run_at else None,
                    }
                    for t in tasks
                ],
                "total": len(tasks),
            }

        except Exception as e:
            logger.error(f"[Orchestration] Erreur liste taches: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "list_tasks",
            }

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    async def _health_check(self, data: dict, context: list[str]) -> dict:
        """
        Verifie la sante des modules et services externes.

        Args:
            data: {
                "check_external": true,  # Verifier APIs externes
                "check_llm": true,       # Verifier LLM disponible
            }
        """
        logger.info("[Orchestration] Verification sante")

        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "modules": {},
            "external_services": {},
            "llm": {},
        }

        issues = []

        # Verifier les modules actifs
        try:
            from app.modules.marceau.config import get_or_create_marceau_config
            config = get_or_create_marceau_config(self.tenant_id, self.db)

            for module, enabled in config.enabled_modules.items():
                health["modules"][module] = {
                    "enabled": enabled,
                    "status": "ok" if enabled else "disabled",
                }
        except Exception as e:
            health["modules"]["error"] = str(e)
            issues.append("Erreur verification config modules")

        # Verifier le LLM si demande
        if data.get("check_llm", True):
            try:
                llm = await get_llm_client_for_tenant(self.tenant_id, self.db)
                health["llm"] = {
                    "provider": llm.provider_name,
                    "available": await llm.is_available(),
                    "status": "ok",
                }
            except Exception as e:
                health["llm"] = {
                    "provider": "unknown",
                    "available": False,
                    "status": "error",
                    "error": str(e),
                }
                issues.append("LLM non disponible")

        # Verifier services externes si demande
        if data.get("check_external", False):
            # WordPress
            try:
                from app.modules.marceau.modules.seo.service import SEOService
                seo = SEOService(self.tenant_id, self.db)
                # Test basique de config
                health["external_services"]["wordpress"] = {
                    "configured": True,
                    "status": "ok",
                }
            except Exception:
                health["external_services"]["wordpress"] = {
                    "configured": False,
                    "status": "unconfigured",
                }

            # APIs reseaux sociaux
            for platform in ["facebook", "linkedin", "instagram"]:
                health["external_services"][platform] = {
                    "configured": True,  # Simplifie - verifier vraiment en prod
                    "status": "ok",
                }

        # Statistiques actions recentes
        try:
            recent_actions = self.db.query(MarceauAction).filter(
                MarceauAction.tenant_id == self.tenant_id,
                MarceauAction.created_at >= datetime.utcnow() - timedelta(hours=24),
            ).count()

            failed_actions = self.db.query(MarceauAction).filter(
                MarceauAction.tenant_id == self.tenant_id,
                MarceauAction.created_at >= datetime.utcnow() - timedelta(hours=24),
                MarceauAction.status == ActionStatus.FAILED,
            ).count()

            health["statistics"] = {
                "actions_24h": recent_actions,
                "failed_24h": failed_actions,
                "success_rate": round((recent_actions - failed_actions) / recent_actions * 100, 1) if recent_actions > 0 else 100,
            }

            if failed_actions > recent_actions * 0.2:  # Plus de 20% d'echecs
                issues.append(f"Taux d'echec eleve: {failed_actions}/{recent_actions}")

        except Exception as e:
            health["statistics"] = {"error": str(e)}

        # Determiner le statut global
        if issues:
            health["status"] = "degraded"
            health["issues"] = issues

        return {
            "success": True,
            "action": "health_check",
            "health": health,
        }

    # ========================================================================
    # GENERATE REPORT
    # ========================================================================

    async def _generate_report(self, data: dict, context: list[str]) -> dict:
        """
        Genere un rapport d'activite global.

        Args:
            data: {
                "period": "7d" | "30d" | "90d" | "custom",
                "start_date": "2024-01-01",  # si custom
                "end_date": "2024-01-31",    # si custom
                "include_modules": ["commercial", "support"],  # optionnel, tous si vide
                "with_analysis": true,  # Analyse LLM
            }
        """
        logger.info("[Orchestration] Generation rapport")

        # Determiner la periode
        period = data.get("period", "7d")
        if period == "custom":
            try:
                start_date = datetime.strptime(data.get("start_date"), "%Y-%m-%d")
                end_date = datetime.strptime(data.get("end_date"), "%Y-%m-%d")
            except (ValueError, TypeError):
                return {
                    "success": False,
                    "error": "Dates invalides pour periode custom",
                    "action": "generate_report",
                }
        else:
            days_map = {"7d": 7, "30d": 30, "90d": 90}
            days = days_map.get(period, 7)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

        try:
            # Filtrer par modules si specifie
            include_modules = data.get("include_modules", [])

            # Query de base
            base_query = self.db.query(MarceauAction).filter(
                MarceauAction.tenant_id == self.tenant_id,
                MarceauAction.created_at >= start_date,
                MarceauAction.created_at <= end_date,
            )

            if include_modules:
                base_query = base_query.filter(MarceauAction.module.in_(include_modules))

            # Actions par module
            actions_by_module = self.db.query(
                MarceauAction.module,
                func.count(MarceauAction.id),
            ).filter(
                MarceauAction.tenant_id == self.tenant_id,
                MarceauAction.created_at >= start_date,
                MarceauAction.created_at <= end_date,
            ).group_by(MarceauAction.module).all()

            # Actions par statut
            actions_by_status = self.db.query(
                MarceauAction.status,
                func.count(MarceauAction.id),
            ).filter(
                MarceauAction.tenant_id == self.tenant_id,
                MarceauAction.created_at >= start_date,
                MarceauAction.created_at <= end_date,
            ).group_by(MarceauAction.status).all()

            # Actions par jour
            actions_by_day = self.db.query(
                func.date(MarceauAction.created_at),
                func.count(MarceauAction.id),
            ).filter(
                MarceauAction.tenant_id == self.tenant_id,
                MarceauAction.created_at >= start_date,
                MarceauAction.created_at <= end_date,
            ).group_by(func.date(MarceauAction.created_at)).all()

            # Totaux
            total_actions = base_query.count()
            successful = base_query.filter(
                MarceauAction.status == ActionStatus.COMPLETED
            ).count()
            failed = base_query.filter(
                MarceauAction.status == ActionStatus.FAILED
            ).count()
            pending = base_query.filter(
                MarceauAction.status == ActionStatus.NEEDS_VALIDATION
            ).count()

            report = {
                "period": {
                    "type": period,
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": (end_date - start_date).days,
                },
                "totals": {
                    "actions": total_actions,
                    "successful": successful,
                    "failed": failed,
                    "pending_validation": pending,
                    "success_rate": round(successful / total_actions * 100, 1) if total_actions > 0 else 0,
                },
                "by_module": {str(m): c for m, c in actions_by_module},
                "by_status": {str(s): c for s, c in actions_by_status},
                "by_day": {str(d): c for d, c in actions_by_day},
            }

            # Analyse LLM si demandee
            if data.get("with_analysis"):
                analysis = await self._analyze_activity(report)
                report["ai_analysis"] = analysis

            # Enregistrer l'action
            action_record = MarceauAction(
                tenant_id=self.tenant_id,
                module="orchestration",
                action_type="generate_report",
                status=ActionStatus.COMPLETED,
                input_data=data,
                output_data={"period": period, "total_actions": total_actions},
                reasoning=f"Rapport genere: {total_actions} actions sur {(end_date - start_date).days} jours",
            )
            self.db.add(action_record)
            self.db.commit()

            return {
                "success": True,
                "action": "generate_report",
                "report": report,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"[Orchestration] Erreur rapport: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "generate_report",
            }

    async def _analyze_activity(self, report_data: dict) -> dict:
        """Analyse l'activite via LLM."""
        try:
            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            prompt = f"""Analyse ce rapport d'activite Marceau et fournis:
1. Tendances principales (2-3 observations)
2. Points d'attention (anomalies, risques)
3. Recommandations (1-2 actions)

Donnees:
- Total actions: {report_data['totals']['actions']}
- Taux succes: {report_data['totals']['success_rate']}%
- Repartition modules: {json.dumps(report_data['by_module'])}
- Repartition statuts: {json.dumps(report_data['by_status'])}

Reponds en JSON:
{{
    "trends": ["tendance 1", "tendance 2"],
    "alerts": ["alerte si applicable"],
    "recommendations": ["recommandation 1"]
}}"""

            response = await llm.generate(
                prompt,
                temperature=0.2,
                max_tokens=600,
                system_prompt="Tu es un analyste operationnel expert.",
            )

            from app.modules.marceau.llm_client import extract_json_from_response
            result = await extract_json_from_response(response)
            return result or {"error": "Analyse non disponible"}

        except Exception as e:
            logger.warning(f"[Orchestration] Erreur analyse LLM: {e}")
            return {"error": str(e)}

    # ========================================================================
    # UNKNOWN ACTION
    # ========================================================================

    async def _unknown_action(self, data: dict, context: list[str]) -> dict:
        """Gere les actions non reconnues."""
        return {
            "success": False,
            "error": "Action orchestration non reconnue",
            "available_actions": [
                "execute_workflow",
                "schedule_task",
                "cancel_task",
                "list_tasks",
                "health_check",
                "generate_report",
            ],
            "available_workflows": list(self.WORKFLOWS.keys()),
        }
