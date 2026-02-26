"""
AZALSCORE - E-Invoicing Lifecycle Management
Gestion du cycle de vie et des événements des factures électroniques
"""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.modules.country_packs.france.einvoicing_models import (
    EInvoiceDirection,
    EInvoiceLifecycleEvent,
    EInvoiceRecord,
    EInvoiceStats,
    EInvoiceStatusDB,
    EReportingSubmission,
)

logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    Gestionnaire du cycle de vie des factures électroniques.

    Gère:
    - Événements lifecycle
    - Statistiques
    """

    def __init__(self, db: Session, tenant_id: str) -> None:
        self.db = db
        self.tenant_id = tenant_id

    def add_event(
        self,
        einvoice: EInvoiceRecord,
        status: str,
        actor: str | None = None,
        source: str | None = None,
        message: str | None = None,
        details: dict[str, Any] | None = None
    ) -> EInvoiceLifecycleEvent:
        """
        Ajoute un événement au cycle de vie.

        Args:
            einvoice: Facture électronique
            status: Nouveau statut
            actor: Acteur de l'action
            source: Source de l'événement
            message: Message descriptif
            details: Détails additionnels

        Returns:
            EInvoiceLifecycleEvent créé
        """
        event = EInvoiceLifecycleEvent(
            tenant_id=self.tenant_id,
            einvoice_id=einvoice.id,
            status=status,
            timestamp=datetime.utcnow(),
            actor=actor,
            message=message,
            source=source,
            details=details or {}
        )
        self.db.add(event)
        self.db.commit()
        return event

    def update_stats(self, einvoice: EInvoiceRecord, field: str) -> None:
        """
        Met à jour les statistiques.

        Args:
            einvoice: Facture électronique
            field: Champ de statistique à incrémenter
        """
        period = einvoice.issue_date.strftime("%Y-%m")

        stats = self.db.query(EInvoiceStats).filter(
            EInvoiceStats.tenant_id == self.tenant_id,
            EInvoiceStats.period == period
        ).first()

        if not stats:
            stats = EInvoiceStats(
                tenant_id=self.tenant_id,
                period=period
            )
            self.db.add(stats)

        current_value = getattr(stats, field, 0) or 0
        setattr(stats, field, current_value + 1)

        # Mettre à jour les montants
        if einvoice.direction == EInvoiceDirection.OUTBOUND:
            stats.outbound_amount_ttc = (
                (stats.outbound_amount_ttc or Decimal("0")) + einvoice.total_ttc
            )
        else:
            stats.inbound_amount_ttc = (
                (stats.inbound_amount_ttc or Decimal("0")) + einvoice.total_ttc
            )

        self.db.commit()

    def update_stats_on_status_change(
        self,
        einvoice: EInvoiceRecord,
        old_status: EInvoiceStatusDB,
        new_status: EInvoiceStatusDB
    ) -> None:
        """
        Met à jour les stats sur changement de statut.

        Args:
            einvoice: Facture électronique
            old_status: Ancien statut
            new_status: Nouveau statut
        """
        period = einvoice.issue_date.strftime("%Y-%m")

        stats = self.db.query(EInvoiceStats).filter(
            EInvoiceStats.tenant_id == self.tenant_id,
            EInvoiceStats.period == period
        ).first()

        if not stats:
            return

        direction = "outbound" if einvoice.direction == EInvoiceDirection.OUTBOUND else "inbound"

        status_field_map = {
            EInvoiceStatusDB.SENT: f"{direction}_sent",
            EInvoiceStatusDB.DELIVERED: f"{direction}_delivered",
            EInvoiceStatusDB.ACCEPTED: f"{direction}_accepted",
            EInvoiceStatusDB.REFUSED: f"{direction}_refused",
            EInvoiceStatusDB.ERROR: f"{direction}_errors",
        }

        if new_status in status_field_map:
            field = status_field_map[new_status]
            if hasattr(stats, field):
                current = getattr(stats, field, 0) or 0
                setattr(stats, field, current + 1)
                self.db.commit()

    def update_ereporting_stats(self, submission: EReportingSubmission) -> None:
        """
        Met à jour les stats e-reporting.

        Args:
            submission: Soumission e-reporting
        """
        stats = self.db.query(EInvoiceStats).filter(
            EInvoiceStats.tenant_id == self.tenant_id,
            EInvoiceStats.period == submission.period
        ).first()

        if not stats:
            stats = EInvoiceStats(
                tenant_id=self.tenant_id,
                period=submission.period
            )
            self.db.add(stats)

        stats.ereporting_submitted = (stats.ereporting_submitted or 0) + 1
        stats.ereporting_amount = (
            (stats.ereporting_amount or Decimal("0")) + submission.total_ttc
        )

        self.db.commit()
