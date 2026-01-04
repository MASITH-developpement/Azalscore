"""
AZALS - Modèles SQLAlchemy
Multi-tenant strict
"""

from app.models.base import TenantMixin
from app.models.resource import Resource
# Tenant is now in app.modules.tenants.models

__all__ = ["TenantMixin", "Resource"]
