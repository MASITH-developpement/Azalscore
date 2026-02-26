"""
AZALSCORE - E-Invoicing Submission
Soumission des factures électroniques aux PDP
"""
from __future__ import annotations

import concurrent.futures
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.modules.country_packs.france.einvoicing_models import (
    EInvoiceDirection,
    EInvoiceRecord,
    EInvoiceStatusDB,
    TenantPDPConfig,
)
from app.modules.country_packs.france.einvoicing_schemas import (
    BulkGenerateRequest,
    BulkGenerateResponse,
    BulkSubmitRequest,
    BulkSubmitResponse,
    EInvoiceCreateFromSource,
    EInvoiceStatus,
    EInvoiceSubmitResponse,
)
from app.modules.country_packs.france.e_invoicing import (
    EInvoiceDocument,
    EInvoiceLine as FacturXLine,
    EInvoiceParty as FacturXParty,
    EInvoiceType,
)
from app.modules.country_packs.france.pdp_client import (
    PDPClientFactory,
    PDPConfig,
    PDPInvoiceResponse,
    PDPProvider,
)

if TYPE_CHECKING:
    from .lifecycle import LifecycleManager
    from .generation import EInvoiceGenerator

logger = logging.getLogger(__name__)


class EInvoiceSubmitter:
    """
    Gestionnaire de soumission des factures électroniques aux PDP.

    Gère:
    - Soumission individuelle
    - Soumission en masse
    - Génération en masse
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        lifecycle_manager: "LifecycleManager",
        generator: "EInvoiceGenerator"
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.lifecycle_manager = lifecycle_manager
        self.generator = generator

    def submit_einvoice(
        self,
        einvoice: EInvoiceRecord,
        pdp_config: TenantPDPConfig,
        submitted_by: uuid.UUID | None = None
    ) -> EInvoiceSubmitResponse:
        """
        Soumet une facture au PDP.

        Args:
            einvoice: Facture à soumettre
            pdp_config: Configuration PDP
            submitted_by: UUID de l'utilisateur

        Returns:
            EInvoiceSubmitResponse

        Raises:
            ValueError: Si la facture n'est pas valide
        """
        if not einvoice.is_valid:
            raise ValueError("Facture non valide, impossible de soumettre")

        if einvoice.status not in (
            EInvoiceStatusDB.DRAFT,
            EInvoiceStatusDB.VALIDATED,
            EInvoiceStatusDB.ERROR
        ):
            raise ValueError(f"Statut incompatible pour soumission: {einvoice.status}")

        # Générer un transaction_id
        transaction_id = f"TXN-{self.tenant_id[:8]}-{uuid.uuid4().hex[:12]}"
        einvoice.transaction_id = transaction_id

        try:
            # Construire la config pour le client PDP
            pdp_client_config = self._build_pdp_client_config(pdp_config)

            # Reconstruire le document pour l'envoi
            doc = self._rebuild_document_from_einvoice(einvoice)

            # Soumettre au PDP
            pdp_response = self._submit_to_pdp_sync(
                pdp_client_config, doc, einvoice.xml_content
            )

            if pdp_response.success:
                einvoice.status = EInvoiceStatusDB.SENT
                einvoice.submission_date = datetime.utcnow()
                einvoice.ppf_id = pdp_response.ppf_id
                einvoice.pdp_id = pdp_response.pdp_id
                einvoice.last_error = None

                self.db.commit()
                self.db.refresh(einvoice)

                # Ajouter événements lifecycle depuis la réponse PDP
                for event in pdp_response.lifecycle_events:
                    self.lifecycle_manager.add_event(
                        einvoice,
                        status=event.status.value if hasattr(event.status, 'value') else str(event.status),
                        actor=event.actor,
                        source="PDP",
                        message=event.message
                    )

                # Mettre à jour les stats
                self.lifecycle_manager.update_stats(einvoice, "outbound_sent")

                return EInvoiceSubmitResponse(
                    einvoice_id=einvoice.id,
                    transaction_id=einvoice.transaction_id,
                    ppf_id=einvoice.ppf_id,
                    pdp_id=einvoice.pdp_id,
                    status=EInvoiceStatus(einvoice.status.value),
                    message=pdp_response.message or "Facture soumise avec succès",
                    submitted_at=einvoice.submission_date
                )
            else:
                raise ValueError(pdp_response.message or "Erreur PDP inconnue")

        except Exception as e:
            einvoice.status = EInvoiceStatusDB.ERROR
            einvoice.last_error = str(e)
            einvoice.error_count = (einvoice.error_count or 0) + 1
            self.db.commit()

            self.lifecycle_manager.add_event(
                einvoice,
                status="ERROR",
                actor=str(submitted_by) if submitted_by else "SYSTEM",
                source="PDP",
                message=f"Erreur de soumission: {str(e)}"
            )

            raise

    def _build_pdp_client_config(self, pdp_config: TenantPDPConfig) -> PDPConfig:
        """Construit la configuration pour le client PDP."""
        return PDPConfig(
            provider=PDPProvider(
                pdp_config.provider.value
                if hasattr(pdp_config.provider, 'value')
                else pdp_config.provider
            ),
            api_url=pdp_config.api_url,
            client_id=pdp_config.client_id or "",
            client_secret=pdp_config.client_secret or "",
            token_url=pdp_config.token_url,
            scope=pdp_config.scope,
            certificate_path=pdp_config.certificate_ref,
            private_key_path=pdp_config.private_key_ref,
            test_mode=pdp_config.test_mode,
            timeout=pdp_config.timeout_seconds or 30,
            retry_count=pdp_config.retry_count or 3,
            siret=pdp_config.siret,
            siren=pdp_config.siren,
            tva_number=pdp_config.tva_number,
            webhook_url=pdp_config.webhook_url,
            webhook_secret=pdp_config.webhook_secret,
        )

    def _submit_to_pdp_sync(
        self,
        config: PDPConfig,
        doc: EInvoiceDocument,
        xml_content: str | None
    ) -> PDPInvoiceResponse:
        """
        Soumet la facture au PDP de manière synchrone.

        Utilise un thread séparé pour exécuter l'appel async aux clients PDP.
        """
        def run_async():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                client = PDPClientFactory.create(config)
                return loop.run_until_complete(
                    self._submit_to_pdp_async(client, doc, xml_content)
                )
            finally:
                loop.close()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            return future.result(timeout=config.timeout + 10)

    async def _submit_to_pdp_async(
        self,
        client,
        doc: EInvoiceDocument,
        xml_content: str | None
    ) -> PDPInvoiceResponse:
        """Soumet la facture au PDP de manière async."""
        async with client:
            return await client.submit_invoice(
                doc,
                xml_content or "",
                None  # PDF optionnel
            )

    def _rebuild_document_from_einvoice(self, einvoice: EInvoiceRecord) -> EInvoiceDocument:
        """Reconstruit un EInvoiceDocument depuis un enregistrement."""
        # Créer les parties
        seller = FacturXParty(
            name=einvoice.seller_name or "",
            siret=einvoice.seller_siret or "",
            tva_number=einvoice.seller_tva,
        )

        buyer = FacturXParty(
            name=einvoice.buyer_name or "",
            siret=einvoice.buyer_siret or "",
            tva_number=einvoice.buyer_tva,
            routing_id=einvoice.buyer_routing_id,
        )

        # Recréer les lignes depuis vat_breakdown
        lines = []
        vat_breakdown = einvoice.vat_breakdown or {}
        line_num = 1
        for rate_str, amount in vat_breakdown.items():
            rate = Decimal(str(rate_str))
            vat_amount = Decimal(str(amount))
            ht_amount = vat_amount * Decimal("100") / rate if rate > 0 else Decimal("0")

            lines.append(FacturXLine(
                line_number=line_num,
                description=f"Ligne facture (TVA {rate}%)",
                quantity=Decimal("1"),
                unit_price=ht_amount,
                net_amount=ht_amount,
                vat_rate=rate,
                vat_amount=vat_amount,
            ))
            line_num += 1

        # Si pas de lignes, créer une ligne par défaut
        if not lines:
            lines.append(FacturXLine(
                line_number=1,
                description="Ligne facture",
                quantity=Decimal("1"),
                unit_price=einvoice.total_ht or Decimal("0"),
                net_amount=einvoice.total_ht or Decimal("0"),
                vat_rate=Decimal("20"),
                vat_amount=einvoice.total_tva or Decimal("0"),
            ))

        # Déterminer le type de facture
        invoice_type = EInvoiceType.INVOICE
        if einvoice.invoice_type == "381":
            invoice_type = EInvoiceType.CREDIT_NOTE
        elif einvoice.invoice_type:
            try:
                invoice_type = EInvoiceType(einvoice.invoice_type)
            except ValueError:
                pass

        return EInvoiceDocument(
            invoice_number=einvoice.invoice_number,
            invoice_type=invoice_type,
            issue_date=einvoice.issue_date,
            due_date=einvoice.due_date,
            currency_code=einvoice.currency or "EUR",
            seller=seller,
            buyer=buyer,
            lines=lines,
            total_ht=einvoice.total_ht or Decimal("0"),
            total_tva=einvoice.total_tva or Decimal("0"),
            total_ttc=einvoice.total_ttc or Decimal("0"),
        )

    def bulk_submit(
        self,
        data: BulkSubmitRequest,
        get_einvoice_func,
        get_pdp_config_func,
        submitted_by: uuid.UUID | None = None
    ) -> BulkSubmitResponse:
        """Soumission en masse."""
        results = []
        submitted = 0
        failed = 0

        for einvoice_id in data.einvoice_ids:
            try:
                einvoice = get_einvoice_func(einvoice_id)
                if not einvoice:
                    raise ValueError(f"Facture non trouvée: {einvoice_id}")

                pdp_config = None
                if einvoice.pdp_config_id:
                    pdp_config = get_pdp_config_func(einvoice.pdp_config_id)
                else:
                    pdp_config = get_pdp_config_func(None)

                if not pdp_config:
                    raise ValueError("Aucune configuration PDP disponible")

                response = self.submit_einvoice(einvoice, pdp_config, submitted_by)
                results.append({
                    "einvoice_id": str(einvoice_id),
                    "status": "submitted",
                    "transaction_id": response.transaction_id
                })
                submitted += 1
            except Exception as e:
                results.append({
                    "einvoice_id": str(einvoice_id),
                    "status": "failed",
                    "error": str(e)
                })
                failed += 1

        return BulkSubmitResponse(
            total=len(data.einvoice_ids),
            submitted=submitted,
            failed=failed,
            results=results
        )

    def bulk_generate(
        self,
        data: BulkGenerateRequest,
        get_pdp_config_func,
        created_by: uuid.UUID | None = None
    ) -> BulkGenerateResponse:
        """Génération en masse depuis documents sources."""
        einvoice_ids = []
        errors = []
        generated = 0
        failed = 0

        pdp_config = None
        if data.pdp_config_id:
            pdp_config = get_pdp_config_func(data.pdp_config_id)
        else:
            pdp_config = get_pdp_config_func(None)

        for source_id in data.source_ids:
            try:
                create_data = EInvoiceCreateFromSource(
                    source_type=data.source_type,
                    source_id=source_id,
                    format=data.format,
                    pdp_config_id=data.pdp_config_id
                )
                einvoice = self.generator.create_from_source(
                    create_data, pdp_config, created_by
                )
                einvoice_ids.append(einvoice.id)
                generated += 1
            except Exception as e:
                errors.append({
                    "source_id": str(source_id),
                    "error": str(e)
                })
                failed += 1

        return BulkGenerateResponse(
            total=len(data.source_ids),
            generated=generated,
            failed=failed,
            einvoice_ids=einvoice_ids,
            errors=errors
        )
