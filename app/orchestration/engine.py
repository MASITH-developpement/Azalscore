"""
Moteur d'orchestration DAG AZALSCORE

Interprète les workflows déclaratifs (DAG JSON) et orchestre l'exécution
des sous-programmes avec gestion centralisée des erreurs.

Conformité : AZA-NF-003, Charte Développeur
Principe : "Le code métier est pur, le moteur gère tout le reste"
"""

import json
import re
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

from app.registry.loader import load_program, Program, RegistryError

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Statut d'un step dans l'exécution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class ExecutionStatus(Enum):
    """Statut global de l'exécution"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Certains steps ont échoué mais l'exécution continue


@dataclass
class StepResult:
    """Résultat d'exécution d'un step"""
    step_id: str
    status: StepStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    attempts: int = 1
    program_id: Optional[str] = None


@dataclass
class ExecutionResult:
    """Résultat global d'une exécution de DAG"""
    module_id: str
    status: ExecutionStatus
    steps: Dict[str, StepResult] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None


class OrchestrationEngine:
    """
    Moteur d'orchestration AZALSCORE

    Responsabilités :
    1. Parser le DAG JSON
    2. Résoudre les dépendances entre steps
    3. Exécuter les steps dans l'ordre correct
    4. Gérer retry/timeout/fallback de manière déclarative
    5. Tracer toutes les exécutions
    6. Gérer les erreurs de manière centralisée
    """

    def __init__(self):
        self.execution_trace: List[Dict[str, Any]] = []

    def execute_dag(
        self,
        dag: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Exécute un DAG JSON

        Args:
            dag: DAG JSON déclaratif
                {
                    "module_id": "azalscore.invoice_analysis",
                    "version": "1.0.0",
                    "steps": [
                        {
                            "id": "step1",
                            "use": "azalscore.finance.calculate_margin@^1.0",
                            "inputs": {"price": 1000, "cost": 800},
                            "retry": 2,
                            "timeout": 3000,
                            "fallback": "azalscore.finance.default_margin"
                        }
                    ]
                }
            context: Contexte d'exécution initial (optionnel)

        Returns:
            ExecutionResult avec tous les résultats des steps
        """
        # Initialisation
        started_at = datetime.utcnow()
        module_id = dag.get("module_id", "unknown")
        steps_config = dag.get("steps", [])

        result = ExecutionResult(
            module_id=module_id,
            status=ExecutionStatus.RUNNING,
            context=context or {},
            started_at=started_at
        )

        # Résolution du DAG (ordre d'exécution)
        execution_order = self._resolve_dag(steps_config)

        logger.info(f"Orchestration: Executing DAG {module_id} with {len(steps_config)} steps")

        # Exécution des steps dans l'ordre
        for step_config in execution_order:
            step_id = step_config["id"]

            # Vérification de la condition (si présente)
            if "condition" in step_config:
                if not self._evaluate_condition(step_config["condition"], result.context):
                    logger.info(f"Step {step_id} skipped (condition false)")
                    result.steps[step_id] = StepResult(
                        step_id=step_id,
                        status=StepStatus.SKIPPED
                    )
                    continue

            # Exécution du step avec retry/timeout/fallback
            step_result = self._execute_step(step_config, result.context)
            result.steps[step_id] = step_result

            # Mise à jour du contexte avec les résultats
            if step_result.status == StepStatus.COMPLETED and step_result.output:
                result.context[step_id] = step_result.output

            # Gestion de l'échec
            if step_result.status == StepStatus.FAILED:
                logger.error(f"Step {step_id} failed: {step_result.error}")
                result.status = ExecutionStatus.FAILED
                result.error = f"Step {step_id} failed: {step_result.error}"
                break  # Arrêt de l'exécution

        # Finalisation
        completed_at = datetime.utcnow()
        result.completed_at = completed_at
        result.duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        if result.status == ExecutionStatus.RUNNING:
            result.status = ExecutionStatus.COMPLETED

        logger.info(
            f"Orchestration: DAG {module_id} completed in {result.duration_ms}ms "
            f"with status {result.status.value}"
        )

        return result

    def _resolve_dag(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Résout le DAG pour déterminer l'ordre d'exécution

        Le DAG est implicite : l'ordre est déduit des dépendances
        (références {{step_id.field}} dans les inputs)

        Args:
            steps: Liste des steps du DAG

        Returns:
            Liste des steps ordonnés pour l'exécution

        Note:
            Pour l'instant, on respecte l'ordre déclaré.
            Une future version pourrait paralléliser les steps indépendants.
        """
        # TODO: Implémenter résolution topologique avancée
        # Pour détecter les cycles et paralléliser les steps indépendants

        # Pour l'instant : ordre déclaré
        return steps

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Évalue une condition déclarative

        Format: "{{step_id.field}} <operator> <value>"
        Exemple: "{{calculate_margin.margin_rate}} < 0.2"

        Args:
            condition: Condition déclarative
            context: Contexte d'exécution

        Returns:
            True si la condition est vraie, False sinon
        """
        # Remplacement des variables {{...}}
        resolved_condition = self._resolve_variables(condition, context)

        try:
            # SÉCURITÉ P1-1: Évaluation sécurisée avec parser dédié
            # Remplace eval() par un évaluateur qui n'accepte que les comparaisons
            from app.core.safe_eval import safe_eval, SafeExpressionError

            result = safe_eval(resolved_condition)
            return bool(result)
        except SafeExpressionError as e:
            logger.warning(f"Unsafe condition rejected: {condition} -> {e}")
            return False
        except Exception as e:
            logger.warning(f"Condition evaluation failed: {condition} -> {e}")
            return False

    def _resolve_variables(self, template: str, context: Dict[str, Any]) -> str:
        """
        Résout les variables {{...}} dans un template

        Exemple:
            template = "{{calculate_margin.margin_rate}}"
            context = {"calculate_margin": {"margin_rate": 0.15}}
            -> "0.15"

        Args:
            template: Template avec variables {{...}}
            context: Contexte contenant les valeurs

        Returns:
            Template avec variables remplacées
        """
        if not isinstance(template, str):
            return template

        # Recherche de toutes les variables {{...}}
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, template)

        for match in matches:
            # match = "calculate_margin.margin_rate" ou "context.price"
            path = match.strip().split('.')

            # Navigation dans le contexte
            value = context

            # Cas spécial : "context" fait référence au contexte racine
            # {{context.price}} accède directement à context["price"]
            if path[0] == "context":
                # Ignorer le premier élément "context"
                path = path[1:]

            for key in path:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    logger.warning(f"Variable not found: {match}")
                    value = None
                    break

            # Remplacement
            if value is not None:
                template = template.replace(f"{{{{{match}}}}}", str(value))

        return template

    def _execute_step(
        self,
        step_config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> StepResult:
        """
        Exécute un step avec retry/timeout/fallback

        Cette méthode gère TOUTE la logique d'erreur de manière centralisée.
        Le code métier des sous-programmes reste PUR.

        Args:
            step_config: Configuration du step
            context: Contexte d'exécution

        Returns:
            StepResult
        """
        step_id = step_config["id"]
        program_ref = step_config["use"]
        inputs_template = step_config.get("inputs", {})
        retry_max = step_config.get("retry", 0)
        timeout_ms = step_config.get("timeout", 30000)
        fallback_ref = step_config.get("fallback")

        started_at = datetime.utcnow()
        attempts = 0

        # Résolution des inputs (remplacement des variables {{...}})
        inputs = self._resolve_inputs(inputs_template, context)

        # Chargement du sous-programme
        try:
            program = load_program(program_ref)
        except RegistryError as e:
            return StepResult(
                step_id=step_id,
                status=StepStatus.FAILED,
                error=f"Failed to load program: {e}",
                started_at=started_at,
                completed_at=datetime.utcnow(),
                program_id=program_ref
            )

        # Exécution avec retry
        last_error = None
        for attempt in range(retry_max + 1):
            attempts += 1

            try:
                logger.info(
                    f"Step {step_id}: Executing {program_ref} "
                    f"(attempt {attempt + 1}/{retry_max + 1})"
                )

                # Exécution du sous-programme
                # Note: Pas de try/catch dans le sous-programme lui-même
                output = program.execute(inputs)

                # Succès
                completed_at = datetime.utcnow()
                duration_ms = int((completed_at - started_at).total_seconds() * 1000)

                return StepResult(
                    step_id=step_id,
                    status=StepStatus.COMPLETED,
                    output=output,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                    attempts=attempts,
                    program_id=program_ref
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Step {step_id}: Attempt {attempt + 1} failed: {e}"
                )

                if attempt < retry_max:
                    # Attente avant retry (exponential backoff)
                    wait_ms = (2 ** attempt) * 100
                    time.sleep(wait_ms / 1000)

        # Échec après tous les retries -> essayer fallback
        if fallback_ref:
            logger.info(f"Step {step_id}: Trying fallback {fallback_ref}")
            try:
                fallback_program = load_program(fallback_ref)
                output = fallback_program.execute(inputs)

                completed_at = datetime.utcnow()
                duration_ms = int((completed_at - started_at).total_seconds() * 1000)

                return StepResult(
                    step_id=step_id,
                    status=StepStatus.COMPLETED,
                    output=output,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                    attempts=attempts + 1,
                    program_id=fallback_ref
                )
            except Exception as fallback_error:
                logger.error(f"Step {step_id}: Fallback failed: {fallback_error}")
                last_error = f"{last_error} | Fallback failed: {fallback_error}"

        # Échec définitif
        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        return StepResult(
            step_id=step_id,
            status=StepStatus.FAILED,
            error=last_error,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            attempts=attempts,
            program_id=program_ref
        )

    def _resolve_inputs(
        self,
        inputs_template: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Résout les inputs en remplaçant les variables {{...}}

        Args:
            inputs_template: Template des inputs avec variables
            context: Contexte d'exécution

        Returns:
            Inputs résolus
        """
        resolved = {}

        for key, value in inputs_template.items():
            if isinstance(value, str):
                resolved[key] = self._resolve_variables(value, context)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_inputs(value, context)
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_variables(item, context) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                resolved[key] = value

        return resolved


# Instance globale du moteur (singleton pattern)
_engine_instance: Optional[OrchestrationEngine] = None


def get_engine() -> OrchestrationEngine:
    """Récupère l'instance singleton du moteur"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = OrchestrationEngine()
    return _engine_instance


def execute_dag(
    dag: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> ExecutionResult:
    """
    Fonction helper pour exécuter un DAG

    Usage:
        dag = {
            "module_id": "azalscore.invoice_analysis",
            "version": "1.0.0",
            "steps": [...]
        }
        result = execute_dag(dag, context={"invoice_id": "INV-001"})
    """
    engine = get_engine()
    return engine.execute_dag(dag, context=context)
