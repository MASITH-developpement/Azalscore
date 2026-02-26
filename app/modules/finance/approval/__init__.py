"""
AZALSCORE Finance Approval Workflows
=====================================

Module de validation et workflows d'approbation.

Fonctionnalités:
- Workflows d'approbation configurables
- Niveaux d'approbation multiples
- Délégation de pouvoir
- Historique d'approbation
- Notifications

Usage:
    from app.modules.finance.approval import ApprovalWorkflowService

    service = ApprovalWorkflowService(db, tenant_id)
    request = await service.create_approval_request(document_type, document_id, amount)
    await service.approve(request.id, approver_id)
"""

from .service import (
    ApprovalWorkflowService,
    ApprovalRequest,
    ApprovalRule,
    ApprovalLevel,
    ApprovalAction,
    ApprovalStatus,
    DocumentType,
)
from .router import router as approval_router

__all__ = [
    "ApprovalWorkflowService",
    "ApprovalRequest",
    "ApprovalRule",
    "ApprovalLevel",
    "ApprovalAction",
    "ApprovalStatus",
    "DocumentType",
    "approval_router",
]
