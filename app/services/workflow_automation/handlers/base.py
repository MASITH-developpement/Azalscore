"""
AZALSCORE - Workflow Automation Base Handler
Classe de base et utilitaires pour les handlers d'actions
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from ..types import ActionConfig


class ActionHandler(ABC):
    """Classe de base pour les handlers d'actions"""

    @abstractmethod
    async def execute(
        self,
        action: ActionConfig,
        context: dict,
        variables: dict
    ) -> tuple[Any, Optional[str]]:
        """
        Exécute l'action et retourne (output, error).

        Args:
            action: Configuration de l'action
            context: Contexte d'exécution
            variables: Variables du workflow

        Returns:
            Tuple (output, error_message)
        """
        pass

    def _resolve_value(self, value: Any, variables: dict) -> Any:
        """Résout les variables dans une valeur."""
        if isinstance(value, str):
            for var_name, var_value in variables.items():
                value = value.replace(f"${{{var_name}}}", str(var_value))
                value = value.replace(f"${{variables.{var_name}}}", str(var_value))
        return value

    def _resolve_dict(self, d: dict, variables: dict) -> dict:
        """Résout les variables dans un dictionnaire."""
        return {k: self._resolve_value(v, variables) for k, v in d.items()}

    def _resolve_list(self, value: list, variables: dict) -> list:
        """Résout les variables dans une liste."""
        return [self._resolve_value(v, variables) for v in value]
