"""
AZALS - Accounting Router Unified
=================================

Re-exports the main accounting router for v3 API compatibility.
"""

from app.modules.accounting.router_crud import router

__all__ = ["router"]
