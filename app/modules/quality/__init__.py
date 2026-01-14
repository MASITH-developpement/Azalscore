"""
AZALS ERP - Module M7: Qualité (Quality Management)
===================================================

Module de gestion de la qualité pour l'ERP AZALS.
Gère les contrôles qualité, non-conformités, audits et actions correctives.

Fonctionnalités:
- Gestion des non-conformités (NC)
- Contrôles qualité (réception, production, expédition)
- Audits qualité (internes et externes)
- Plans d'actions correctives/préventives (CAPA)
- Gestion des réclamations clients
- Indicateurs qualité (KPIs)
- Gestion des certifications et normes
- Documentation qualité

Auteur: AZALS Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__module_code__ = "M7"
__module_name__ = "Qualité - Quality Management"
__dependencies__ = ["T0", "T5", "M5", "M6"]

from app.modules.quality.models import (
    CAPA,
    AuditFinding,
    AuditStatus,
    AuditType,
    CAPAAction,
    CAPAStatus,
    CAPAType,
    Certification,
    CertificationAudit,
    ClaimAction,
    ClaimStatus,
    ControlResult,
    ControlStatus,
    ControlType,
    CustomerClaim,
    IndicatorMeasurement,
    NonConformance,
    NonConformanceAction,
    NonConformanceSeverity,
    NonConformanceStatus,
    NonConformanceType,
    QualityAudit,
    QualityControl,
    QualityControlLine,
    QualityControlTemplate,
    QualityControlTemplateItem,
    QualityIndicator,
)

__all__ = [
    # Enums
    "NonConformanceType",
    "NonConformanceStatus",
    "NonConformanceSeverity",
    "ControlType",
    "ControlStatus",
    "ControlResult",
    "AuditType",
    "AuditStatus",
    "CAPAType",
    "CAPAStatus",
    "ClaimStatus",
    # Models
    "NonConformance",
    "NonConformanceAction",
    "QualityControl",
    "QualityControlLine",
    "QualityControlTemplate",
    "QualityControlTemplateItem",
    "QualityAudit",
    "AuditFinding",
    "CAPA",
    "CAPAAction",
    "CustomerClaim",
    "ClaimAction",
    "QualityIndicator",
    "IndicatorMeasurement",
    "Certification",
    "CertificationAudit",
]
