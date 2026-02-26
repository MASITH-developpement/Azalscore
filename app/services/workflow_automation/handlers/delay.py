"""
AZALSCORE - Workflow Automation Delay Handler
Handler pour les délais d'exécution
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Optional

from ..types import ActionConfig
from .base import ActionHandler


class DelayHandler(ActionHandler):
    """Handler pour les délais"""

    # Délai maximum en secondes (5 minutes)
    MAX_DELAY_SECONDS = 300

    async def execute(
        self,
        action: ActionConfig,
        context: dict,
        variables: dict
    ) -> tuple[Any, Optional[str]]:
        params = action.parameters
        delay_seconds = params.get("delay_seconds", 0)
        delay_until = params.get("delay_until")

        if delay_until:
            target_time = datetime.fromisoformat(delay_until)
            delay_seconds = (target_time - datetime.utcnow()).total_seconds()
            delay_seconds = max(0, delay_seconds)

        # Limiter le délai maximum
        actual_delay = min(delay_seconds, self.MAX_DELAY_SECONDS)
        await asyncio.sleep(actual_delay)

        return {"delayed_seconds": actual_delay}, None
