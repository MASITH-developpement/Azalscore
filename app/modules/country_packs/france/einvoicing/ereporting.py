"""
AZALSCORE - E-Invoicing E-Reporting
Gestion de l'e-reporting (transactions B2C)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.modules.country_packs.france.einvoicing_models import (
    EReportingSubmission,
    TenantPDPConfig,
)
from app.modules.country_packs.france.einvoicing_schemas import (
    EReportingCreate,
    EReportingSubmitResponse,
)

if TYPE_CHECKING:
    from .lifecycle import LifecycleManager

logger = logging.getLogger(__name__)


class EReportingManager:
    """
    Gestionnaire de l'e-reporting.

    L'e-reporting concerne les transactions B2C (business to consumer)
    qui ne sont pas soumises à la facturation électronique obligatoire.
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        lifecycle_manager: "LifecycleManager"
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.lifecycle_manager = lifecycle_manager

    def create(
        self,
        data: EReportingCreate,
        pdp_config: TenantPDPConfig | None,
        created_by: uuid.UUID | None = None
    ) -> EReportingSubmission:
        """
        Crée une soumission e-reporting.

        Args:
            data: Données de création
            pdp_config: Configuration PDP
            created_by: UUID de l'utilisateur créateur

        Returns:
            EReportingSubmission créé
        """
        # Calculer les totaux
        total_ht = Decimal("0")
        total_tva = Decimal("0")
        vat_breakdown: dict[str, Decimal] = {}

        for line in data.lines:
            total_ht += line.amount_ht
            total_tva += line.vat_amount

            rate_key = str(line.vat_rate)
            vat_breakdown[rate_key] = vat_breakdown.get(rate_key, Decimal("0")) + line.vat_amount

        submission = EReportingSubmission(
            tenant_id=self.tenant_id,
            pdp_config_id=pdp_config.id if pdp_config else None,
            period=data.period,
            reporting_type=data.reporting_type.value,
            total_ht=total_ht,
            total_tva=total_tva,
            total_ttc=total_ht + total_tva,
            transaction_count=len(data.lines),
            vat_breakdown={str(k): float(v) for k, v in vat_breakdown.items()},
            status="DRAFT",
            created_by=created_by
        )

        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)

        return submission

    def submit(
        self,
        ereporting_id: uuid.UUID,
        submitted_by: uuid.UUID | None = None
    ) -> EReportingSubmitResponse:
        """
        Soumet l'e-reporting au PPF.

        Args:
            ereporting_id: UUID de l'e-reporting
            submitted_by: UUID de l'utilisateur

        Returns:
            EReportingSubmitResponse

        Raises:
            ValueError: Si l'e-reporting n'est pas trouvé ou statut incompatible
        """
        submission = self.db.query(EReportingSubmission).filter(
            EReportingSubmission.id == ereporting_id,
            EReportingSubmission.tenant_id == self.tenant_id
        ).first()

        if not submission:
            raise ValueError(f"E-reporting non trouvé: {ereporting_id}")

        if submission.status not in ("DRAFT", "REJECTED"):
            raise ValueError(f"Statut incompatible: {submission.status}")

        # NOTE: Phase 2 - Intégration client PDP production
        submission.submission_id = f"EREP-{uuid.uuid4().hex[:16]}"
        submission.ppf_reference = f"PPF-EREP-{uuid.uuid4().hex[:12]}"
        submission.status = "SUBMITTED"
        submission.submitted_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(submission)

        # Mettre à jour les stats
        self.lifecycle_manager.update_ereporting_stats(submission)

        return EReportingSubmitResponse(
            ereporting_id=submission.id,
            submission_id=submission.submission_id,
            ppf_reference=submission.ppf_reference,
            status=submission.status,
            message="E-reporting soumis avec succès",
            submitted_at=submission.submitted_at
        )

    def list(
        self,
        period: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 25
    ) -> tuple[list[EReportingSubmission], int]:
        """
        Liste les soumissions e-reporting.

        Args:
            period: Filtrer par période (YYYY-MM)
            status: Filtrer par statut
            page: Page courante
            page_size: Taille de page

        Returns:
            Tuple (liste, total)
        """
        query = self.db.query(EReportingSubmission).filter(
            EReportingSubmission.tenant_id == self.tenant_id
        )

        if period:
            query = query.filter(EReportingSubmission.period == period)
        if status:
            query = query.filter(EReportingSubmission.status == status)

        total = query.count()
        items = query.order_by(
            EReportingSubmission.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return items, total

    def get(self, ereporting_id: uuid.UUID) -> EReportingSubmission | None:
        """
        Récupère un e-reporting par son ID.

        Args:
            ereporting_id: UUID de l'e-reporting

        Returns:
            EReportingSubmission ou None
        """
        return self.db.query(EReportingSubmission).filter(
            EReportingSubmission.id == ereporting_id,
            EReportingSubmission.tenant_id == self.tenant_id
        ).first()
