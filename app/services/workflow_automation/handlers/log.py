"""
AZALSCORE - Workflow Automation Log Handler
Handler pour la journalisation
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from ..types import ActionConfig
from .base import ActionHandler

logger = logging.getLogger(__name__)


class LogHandler(ActionHandler):
    """Handler pour la journalisation"""

    async def execute(
        self,
        action: ActionConfig,
        context: dict,
        variables: dict
    ) -> tuple[Any, Optional[str]]:
        params = action.parameters
        level = params.get("level", "INFO")
        message = self._resolve_value(params.get("message", ""), variables)

        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[Workflow] {message}")

        return {"logged": message, "level": level}, None
