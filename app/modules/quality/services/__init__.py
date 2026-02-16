"""
AZALS MODULE M7 - Quality Services
===================================

Sous-services modulaires pour la gestion de la qualité.
"""

from .base import BaseQualityService
from .non_conformance import NonConformanceService
from .control_template import ControlTemplateService
from .control import ControlService
from .audit import AuditService
from .capa import CAPAService
from .claim import ClaimService
from .certification import CertificationService
from .indicator import IndicatorService
from .dashboard import DashboardService

__all__ = [
    "BaseQualityService",
    "NonConformanceService",
    "ControlTemplateService",
    "ControlService",
    "AuditService",
    "CAPAService",
    "ClaimService",
    "CertificationService",
    "IndicatorService",
    "DashboardService",
]
