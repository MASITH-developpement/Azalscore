"""
AZALSCORE - E-Invoicing Service
Service principal orchestrant les modules e-invoicing
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.modules.country_packs.france.einvoicing_models import (
    EInvoiceRecord,
    EReportingSubmission,
    TenantPDPConfig,
)
from app.modules.country_packs.france.einvoicing_schemas import (
    BulkGenerateRequest,
    BulkGenerateResponse,
    BulkSubmitRequest,
    BulkSubmitResponse,
    EInvoiceCreateFromSource,
    BulkSubmitRequest,
    EInvoiceCreateManual,
    EInvoiceDashboard,
    EInvoiceFilter,
    EInvoiceStatsResponse,
    EInvoiceStatsSummary,
    EInvoiceStatusUpdate,
    EInvoiceSubmitResponse,
    EReportingCreate,
    EReportingSubmitResponse,
    PDPConfigCreate,
    PDPConfigUpdate,
    PDPProviderType as SchemaProviderType,
    ValidationResult,
)

from .ereporting import EReportingManager
from .generation import EInvoiceGenerator
from .inbound import InboundInvoiceHandler
from .lifecycle import LifecycleManager
from .management import EInvoiceManager
from .pdp_config import PDPConfigManager
from .stats import EInvoiceStatsManager
from .submission import EInvoiceSubmitter
from .webhooks import WebhookHandler


class TenantEInvoicingService:
    """
    Service e-invoicing multi-tenant.

    Orchestre toutes les opérations de facturation électronique pour un tenant:
    - Configuration PDP
    - Génération de factures électroniques
    - Soumission aux PDP/PPF
    - Suivi du cycle de vie
    - E-reporting B2C
    - Statistiques
    """

    def __init__(self, db: Session, tenant_id: str) -> None:
        self.db = db
        self.tenant_id = tenant_id

        # Initialiser les managers
        self._pdp_config_manager = PDPConfigManager(db, tenant_id)
        self._lifecycle_manager = LifecycleManager(db, tenant_id)
        self._webhook_handler = WebhookHandler(db, tenant_id, self._lifecycle_manager)
        self._generator = EInvoiceGenerator(db, tenant_id, self._lifecycle_manager)
        self._submitter = EInvoiceSubmitter(
            db, tenant_id, self._lifecycle_manager, self._generator
        )
        self._manager = EInvoiceManager(
            db, tenant_id, self._lifecycle_manager, self._webhook_handler
        )
        self._ereporting_manager = EReportingManager(db, tenant_id, self._lifecycle_manager)
        self._stats_manager = EInvoiceStatsManager(db, tenant_id, self._pdp_config_manager)
        self._inbound_handler = InboundInvoiceHandler(
            db, tenant_id, self._lifecycle_manager, self._webhook_handler
        )

    # =========================================================================
    # CONFIGURATION PDP
    # =========================================================================

    def list_pdp_configs(
        self,
        active_only: bool = True,
        provider: SchemaProviderType | None = None
    ) -> list[TenantPDPConfig]:
        """Liste les configurations PDP du tenant."""
        return self._pdp_config_manager.list_configs(active_only, provider)

    def get_pdp_config(self, config_id: uuid.UUID) -> TenantPDPConfig | None:
        """Récupère une configuration PDP."""
        return self._pdp_config_manager.get_config(config_id)

    def get_default_pdp_config(self) -> TenantPDPConfig | None:
        """Récupère la configuration PDP par défaut."""
        return self._pdp_config_manager.get_default_config()

    def create_pdp_config(
        self,
        data: PDPConfigCreate,
        created_by: uuid.UUID | None = None
    ) -> TenantPDPConfig:
        """Crée une configuration PDP."""
        return self._pdp_config_manager.create_config(data, created_by)

    def update_pdp_config(
        self,
        config_id: uuid.UUID,
        data: PDPConfigUpdate
    ) -> TenantPDPConfig | None:
        """Met à jour une configuration PDP."""
        return self._pdp_config_manager.update_config(config_id, data)

    def delete_pdp_config(self, config_id: uuid.UUID) -> bool:
        """Supprime une configuration PDP."""
        return self._pdp_config_manager.delete_config(config_id)

    # =========================================================================
    # GÉNÉRATION E-INVOICE
    # =========================================================================

    def create_einvoice_from_source(
        self,
        data: EInvoiceCreateFromSource,
        created_by: uuid.UUID | None = None
    ) -> EInvoiceRecord:
        """Crée une facture électronique depuis un document existant."""
        pdp_config = None
        if data.pdp_config_id:
            pdp_config = self.get_pdp_config(data.pdp_config_id)
        else:
            pdp_config = self.get_default_pdp_config()

        einvoice = self._generator.create_from_source(data, pdp_config, created_by)

        # Auto-submit si demandé
        if data.auto_submit and einvoice.is_valid:
            self.submit_einvoice(einvoice.id, created_by)

        return einvoice

    def create_einvoice_manual(
        self,
        data: EInvoiceCreateManual,
        created_by: uuid.UUID | None = None
    ) -> EInvoiceRecord:
        """Crée une facture électronique manuellement."""
        pdp_config = None
        if data.pdp_config_id:
            pdp_config = self.get_pdp_config(data.pdp_config_id)
        else:
            pdp_config = self.get_default_pdp_config()

        einvoice = self._generator.create_manual(data, pdp_config, created_by)

        # Auto-submit si demandé
        if data.auto_submit and einvoice.is_valid:
            self.submit_einvoice(einvoice.id, created_by)

        return einvoice

    # =========================================================================
    # SOUMISSION PDP
    # =========================================================================

    def submit_einvoice(
        self,
        einvoice_id: uuid.UUID,
        submitted_by: uuid.UUID | None = None
    ) -> EInvoiceSubmitResponse:
        """Soumet une facture au PDP."""
        einvoice = self.get_einvoice(einvoice_id)
        if not einvoice:
            raise ValueError(f"Facture non trouvée: {einvoice_id}")

        pdp_config = None
        if einvoice.pdp_config_id:
            pdp_config = self.get_pdp_config(einvoice.pdp_config_id)
        else:
            pdp_config = self.get_default_pdp_config()

        if not pdp_config:
            raise ValueError("Aucune configuration PDP disponible")

        return self._submitter.submit_einvoice(einvoice, pdp_config, submitted_by)

    def bulk_submit(
        self,
        data: BulkSubmitRequest,
        submitted_by: uuid.UUID | None = None
    ) -> BulkSubmitResponse:
        """Soumission en masse."""
        return self._submitter.bulk_submit(
            data,
            self.get_einvoice,
            lambda config_id: self.get_pdp_config(config_id) if config_id else self.get_default_pdp_config(),
            submitted_by
        )

    def bulk_generate(
        self,
        data: BulkGenerateRequest,
        created_by: uuid.UUID | None = None
    ) -> BulkGenerateResponse:
        """Génération en masse depuis documents sources."""
        return self._submitter.bulk_generate(
            data,
            lambda config_id: self.get_pdp_config(config_id) if config_id else self.get_default_pdp_config(),
            created_by
        )

    # =========================================================================
    # GESTION DES FACTURES
    # =========================================================================

    def get_einvoice(self, einvoice_id: uuid.UUID) -> EInvoiceRecord | None:
        """Récupère une facture électronique."""
        return self._manager.get_einvoice(einvoice_id)

    def get_einvoice_detail(self, einvoice_id: uuid.UUID) -> EInvoiceRecord | None:
        """Récupère une facture avec ses événements."""
        return self._manager.get_einvoice_detail(einvoice_id)

    def list_einvoices(
        self,
        filters: EInvoiceFilter | None = None,
        page: int = 1,
        page_size: int = 25
    ) -> tuple[list[EInvoiceRecord], int]:
        """Liste les factures électroniques avec filtres."""
        return self._manager.list_einvoices(filters, page, page_size)

    def update_einvoice_status(
        self,
        einvoice_id: uuid.UUID,
        data: EInvoiceStatusUpdate
    ) -> EInvoiceRecord | None:
        """Met à jour le statut d'une facture."""
        return self._manager.update_einvoice_status(einvoice_id, data)

    def validate_einvoice(self, einvoice_id: uuid.UUID) -> ValidationResult:
        """Valide une facture électronique."""
        return self._manager.validate_einvoice(einvoice_id)

    # =========================================================================
    # E-REPORTING
    # =========================================================================

    def create_ereporting(
        self,
        data: EReportingCreate,
        created_by: uuid.UUID | None = None
    ) -> EReportingSubmission:
        """Crée une soumission e-reporting."""
        pdp_config = None
        if data.pdp_config_id:
            pdp_config = self.get_pdp_config(data.pdp_config_id)
        else:
            pdp_config = self.get_default_pdp_config()

        return self._ereporting_manager.create(data, pdp_config, created_by)

    def submit_ereporting(
        self,
        ereporting_id: uuid.UUID,
        submitted_by: uuid.UUID | None = None
    ) -> EReportingSubmitResponse:
        """Soumet l'e-reporting au PPF."""
        return self._ereporting_manager.submit(ereporting_id, submitted_by)

    def list_ereporting(
        self,
        period: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 25
    ) -> tuple[list[EReportingSubmission], int]:
        """Liste les soumissions e-reporting."""
        return self._ereporting_manager.list(period, status, page, page_size)

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def get_stats(self, period: str | None = None) -> EInvoiceStatsResponse | None:
        """Récupère les statistiques pour une période."""
        return self._stats_manager.get_stats(period)

    def get_stats_summary(self) -> EInvoiceStatsSummary:
        """Récupère le résumé des statistiques."""
        return self._stats_manager.get_stats_summary()

    def get_dashboard(self) -> EInvoiceDashboard:
        """Récupère les données du dashboard."""
        return self._stats_manager.get_dashboard()

    # =========================================================================
    # WEBHOOK PROCESSING
    # =========================================================================

    def process_webhook(
        self,
        pdp_config_id: uuid.UUID,
        payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Traite un webhook PDP."""
        pdp_config = self.get_pdp_config(pdp_config_id)
        if not pdp_config:
            return {"error": "Configuration PDP non trouvée"}

        return self._webhook_handler.process_webhook(pdp_config, payload)

    # =========================================================================
    # RÉCEPTION FACTURES ENTRANTES
    # =========================================================================

    def receive_inbound_xml(
        self,
        xml_content: str,
        source_pdp: str | None = None,
        ppf_id: str | None = None,
        pdp_id: str | None = None,
        pdf_base64: str | None = None,
        received_by: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None
    ) -> tuple[EInvoiceRecord, dict[str, Any]]:
        """Reçoit et enregistre une facture entrante depuis XML."""
        pdp_config = self.get_default_pdp_config()
        return self._inbound_handler.receive_inbound_xml(
            xml_content, pdp_config, source_pdp, ppf_id, pdp_id,
            pdf_base64, received_by, metadata
        )

    def receive_inbound_parsed(
        self,
        data: dict[str, Any],
        received_by: uuid.UUID | None = None
    ) -> tuple[EInvoiceRecord, dict[str, Any]]:
        """Reçoit une facture entrante avec données déjà parsées."""
        pdp_config = self.get_default_pdp_config()
        return self._inbound_handler.receive_inbound_parsed(data, pdp_config, received_by)

    def accept_inbound_invoice(
        self,
        einvoice_id: uuid.UUID,
        accepted_by: uuid.UUID | None = None,
        message: str | None = None
    ) -> EInvoiceRecord:
        """Accepte une facture entrante."""
        einvoice = self.get_einvoice(einvoice_id)
        if not einvoice:
            raise ValueError(f"Facture non trouvée: {einvoice_id}")
        return self._inbound_handler.accept_inbound_invoice(einvoice, accepted_by, message)

    def refuse_inbound_invoice(
        self,
        einvoice_id: uuid.UUID,
        refused_by: uuid.UUID | None = None,
        reason: str | None = None
    ) -> EInvoiceRecord:
        """Refuse une facture entrante."""
        einvoice = self.get_einvoice(einvoice_id)
        if not einvoice:
            raise ValueError(f"Facture non trouvée: {einvoice_id}")
        return self._inbound_handler.refuse_inbound_invoice(einvoice, refused_by, reason)


def get_einvoicing_service(db: Session, tenant_id: str) -> TenantEInvoicingService:
    """Factory pour le service e-invoicing."""
    return TenantEInvoicingService(db, tenant_id)
