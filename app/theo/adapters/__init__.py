"""
THÉO — Adapters AZALSCORE
==========================

Adapters pour connecter Théo aux modules métier AZALSCORE.
Chaque adapter encapsule un module et expose des actions vocales.
"""

from app.theo.adapters.base import (
    BaseAdapter,
    AdapterAction,
    AdapterResult,
    ActionStatus
)
from app.theo.adapters.commercial import CommercialAdapter
from app.theo.adapters.treasury import TreasuryAdapter
from app.theo.adapters.navigation import NavigationAdapter

__all__ = [
    "BaseAdapter",
    "AdapterAction",
    "AdapterResult",
    "ActionStatus",
    "CommercialAdapter",
    "TreasuryAdapter",
    "NavigationAdapter",
]
