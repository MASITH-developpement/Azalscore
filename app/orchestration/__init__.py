"""
Moteur d'orchestration AZALSCORE

Interprète les DAG JSON, résout les dépendances, exécute les sous-programmes,
gère retry/timeout/fallback de manière déclarative.

Conformité : AZA-NF-003, Architecture cible
Règle : "Aucune logique de gestion d'erreur dans le code métier"
"""

from .engine import OrchestrationEngine, execute_dag, ExecutionResult

__all__ = ["OrchestrationEngine", "execute_dag", "ExecutionResult"]
