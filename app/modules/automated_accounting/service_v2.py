"""
AZALS - Automated Accounting Service (v2 - CRUDRouter Compatible)
===================================================================

Service compatible avec BaseService et CRUDRouter.
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.base_service import BaseService
from app.core.saas_context import Result, SaaSContext

from app.modules.automated_accounting.models import (
    AccountingDocument,
    OCRResult,
    AIClassification,
    AutoEntry,
    BankConnection,
    SyncedBankAccount,
    SyncedTransaction,
)
from app.modules.automated_accounting.schemas import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
)

logger = logging.getLogger(__name__)


class AccountingDocumentService(BaseService[AccountingDocument, Any, Any]):
    """Service CRUD pour les documents comptables."""

    model = AccountingDocument

    # Les methodes CRUD sont heritees de BaseService:
    # - get(id) -> Optional[AccountingDocument]
    # - get_or_fail(id) -> Result[AccountingDocument]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[AccountingDocument]
    # - update(id, data) -> Result[AccountingDocument]
    # - delete(id, soft) -> Result[bool]

    def list_pending_validation(self) -> List[AccountingDocument]:
        """Liste les documents en attente de validation."""
        from app.modules.automated_accounting.models import DocumentStatus
        return (
            self.db.query(AccountingDocument)
            .filter(
                AccountingDocument.tenant_id == self.tenant_id,
                AccountingDocument.status == DocumentStatus.PENDING_VALIDATION,
            )
            .order_by(AccountingDocument.created_at.desc())
            .all()
        )

    def validate_document(self, document_id: UUID, validator_id: UUID, notes: str = None) -> Result[AccountingDocument]:
        """Valide un document."""
        result = self.get_or_fail(document_id)
        if not result.success:
            return result

        doc = result.data
        from app.modules.automated_accounting.models import DocumentStatus
        doc.status = DocumentStatus.VALIDATED
        doc.validated_by = validator_id
        doc.validated_at = datetime.utcnow()
        if notes:
            doc.validation_notes = notes

        self.db.commit()
        self.db.refresh(doc)
        return Result.ok(doc)


class BankConnectionService(BaseService[BankConnection, Any, Any]):
    """Service CRUD pour les connexions bancaires."""

    model = BankConnection

    def list_active(self) -> List[BankConnection]:
        """Liste les connexions bancaires actives."""
        from app.modules.automated_accounting.models import BankConnectionStatus
        return (
            self.db.query(BankConnection)
            .filter(
                BankConnection.tenant_id == self.tenant_id,
                BankConnection.status == BankConnectionStatus.ACTIVE,
            )
            .all()
        )


class SyncedTransactionService(BaseService[SyncedTransaction, Any, Any]):
    """Service CRUD pour les transactions synchronisees."""

    model = SyncedTransaction

    def list_unreconciled(self) -> List[SyncedTransaction]:
        """Liste les transactions non rapprochees."""
        from app.modules.automated_accounting.models import ReconciliationStatusAuto
        return (
            self.db.query(SyncedTransaction)
            .filter(
                SyncedTransaction.tenant_id == self.tenant_id,
                SyncedTransaction.reconciliation_status == ReconciliationStatusAuto.UNMATCHED,
            )
            .all()
        )
