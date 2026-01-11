"""
AZALS - Modèles SQLAlchemy
Multi-tenant strict
"""

from app.models.base import TenantMixin
from app.models.resource import Resource
from app.models.system_settings import SystemSettings
# Tenant is now in app.modules.tenants.models

__all__ = ["TenantMixin", "Resource", "SystemSettings"]
