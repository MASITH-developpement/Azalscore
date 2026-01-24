"""
THÉO — API
==========

WebSocket et REST endpoints pour Théo.
"""

from app.theo.api.websocket import theo_router, TheoWebSocketManager
from app.theo.api.rest import theo_rest_router

__all__ = [
    "theo_router",
    "theo_rest_router",
    "TheoWebSocketManager",
]
