"""
Module de Gestion des Réclamations Clients - GAP-038

Gestion complète:
- Enregistrement multi-canal
- Classification et priorisation automatique
- Workflow avec SLA et escalade
- Compensation et gestes commerciaux
- Analyse des causes racines
- Reporting et KPIs qualité

Conformité: ISO 10002, RGPD, Médiation consommation
"""

from .service import (
    # Énumérations
    ComplaintChannel,
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
    ResolutionType,
    EscalationLevel,
    SatisfactionRating,

    # Data classes
    Customer,
    ComplaintAttachment,
    ComplaintNote,
    ComplaintAction,
    Resolution,
    Escalation,
    SLAStatus,
    CustomerFeedback,
    Complaint,
    ComplaintTemplate,

    # Configuration
    DEFAULT_SLA_CONFIG,

    # Service
    ComplaintService,
    create_complaint_service,
)

__all__ = [
    "ComplaintChannel",
    "ComplaintCategory",
    "ComplaintPriority",
    "ComplaintStatus",
    "ResolutionType",
    "EscalationLevel",
    "SatisfactionRating",
    "Customer",
    "ComplaintAttachment",
    "ComplaintNote",
    "ComplaintAction",
    "Resolution",
    "Escalation",
    "SLAStatus",
    "CustomerFeedback",
    "Complaint",
    "ComplaintTemplate",
    "DEFAULT_SLA_CONFIG",
    "ComplaintService",
    "create_complaint_service",
]
