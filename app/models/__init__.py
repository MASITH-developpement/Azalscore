"""
AZALS - Modèles SQLAlchemy
Multi-tenant strict
"""

from app.models.base import TenantMixin
from app.models.resource import Resource
from app.models.system_settings import SystemSettings

# Website Tracking Models
from app.models.website_visitor import WebsiteVisitor
from app.models.website_lead import WebsiteLead, LeadSource, LeadStatus
from app.models.demo_request import DemoRequest

# Tenant is now in app.modules.tenants.models

__all__ = [
    "TenantMixin",
    "Resource",
    "SystemSettings",
    "WebsiteVisitor",
    "WebsiteLead",
    "LeadSource",
    "LeadStatus",
    "DemoRequest",
]
