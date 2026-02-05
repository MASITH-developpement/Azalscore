"""
API Workflows AZALSCORE

Permet d'exécuter des workflows DAG déclaratifs

Conformité : AZA-NF-003, Architecture cible
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
from pathlib import Path

logger = logging.getLogger(__name__)

from app.orchestration import execute_dag, ExecutionResult
from app.core.dependencies import get_current_user
from app.core.models import User

router = APIRouter(prefix="/v1/workflows", tags=["workflows"])


class WorkflowExecutionRequest(BaseModel):
    """Requête d'exécution de workflow"""
    workflow_id: Optional[str] = None
    dag: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class WorkflowExecutionResponse(BaseModel):
    """Réponse d'exécution de workflow"""
    module_id: str
    status: str
    duration_ms: int
    steps: Dict[str, Any]
    context: Dict[str, Any]
    error: Optional[str] = None


@router.post("/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    request: WorkflowExecutionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Exécute un workflow DAG

    Deux modes :
    1. Par workflow_id : charge le workflow depuis le filesystem
    2. Par dag JSON : exécute le DAG fourni directement

    Args:
        request: Requête avec workflow_id OU dag JSON
        current_user: Utilisateur authentifié

    Returns:
        Résultat d'exécution du workflow

    Raises:
        HTTPException: Si le workflow n'existe pas ou si l'exécution échoue
    """
    # Chargement du DAG
    dag = None

    if request.workflow_id:
        # Mode 1 : Chargement depuis filesystem
        # Format workflow_id : "finance.invoice_analysis"
        parts = request.workflow_id.split(".")
        if len(parts) != 2:
            raise HTTPException(
                status_code=400,
                detail="workflow_id doit être au format 'module.workflow_name'"
            )

        module_name, workflow_name = parts
        workflow_path = (
            Path(__file__).parent.parent / "modules" / module_name /
            "workflows" / f"{workflow_name}.json"
        )

        if not workflow_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{request.workflow_id}' non trouvé"
            )

        with open(workflow_path, 'r') as f:
            dag = json.load(f)

    elif request.dag:
        # Mode 2 : DAG fourni directement
        dag = request.dag

    else:
        raise HTTPException(
            status_code=400,
            detail="Vous devez fournir soit workflow_id soit dag"
        )

    # Enrichissement du contexte avec l'utilisateur
    context = request.context or {}
    context["user_id"] = str(current_user.id)
    context["tenant_id"] = str(current_user.tenant_id)

    # Exécution du DAG
    try:
        result = execute_dag(dag, context=context)

        # Transformation en réponse API
        return WorkflowExecutionResponse(
            module_id=result.module_id,
            status=result.status.value,
            duration_ms=result.duration_ms,
            steps={
                step_id: {
                    "status": step_result.status.value,
                    "output": step_result.output,
                    "error": step_result.error,
                    "duration_ms": step_result.duration_ms,
                    "attempts": step_result.attempts
                }
                for step_id, step_result in result.steps.items()
            },
            context=result.context,
            error=result.error
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'exécution du workflow : {str(e)}"
        )


@router.get("/list")
async def list_workflows(
    current_user: User = Depends(get_current_user)
):
    """
    Liste tous les workflows disponibles

    Returns:
        Liste des workflows par module
    """
    workflows = {}

    modules_path = Path(__file__).parent.parent / "modules"

    # Parcours de tous les modules
    for module_dir in modules_path.iterdir():
        if not module_dir.is_dir():
            continue

        workflows_dir = module_dir / "workflows"
        if not workflows_dir.exists():
            continue

        module_name = module_dir.name
        module_workflows = []

        # Parcours des workflows du module
        for workflow_file in workflows_dir.glob("*.json"):
            try:
                with open(workflow_file, 'r') as f:
                    dag = json.load(f)

                module_workflows.append({
                    "workflow_id": f"{module_name}.{workflow_file.stem}",
                    "module_id": dag.get("module_id"),
                    "version": dag.get("version"),
                    "description": dag.get("description"),
                    "steps_count": len(dag.get("steps", []))
                })
            except Exception as e:
                logger.warning(
                    "[WORKFLOWS] Erreur lecture fichier workflow DAG",
                    extra={
                        "workflow_file": str(workflow_file),
                        "module": module_name,
                        "error": str(e)[:300],
                        "consequence": "workflow_skipped"
                    }
                )
                continue

        if module_workflows:
            workflows[module_name] = module_workflows

    return workflows


@router.get("/programs")
async def list_programs(
    category: Optional[str] = None,
    no_code_only: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    Liste tous les sous-programmes du registry

    Args:
        category: Filtrer par catégorie (optionnel)
        no_code_only: Filtrer uniquement les sous-programmes No-Code compatibles

    Returns:
        Liste des sous-programmes disponibles
    """
    from app.registry.loader import list_programs as registry_list_programs

    programs = registry_list_programs(category=category, no_code_only=no_code_only)

    return {
        "count": len(programs),
        "programs": programs
    }
