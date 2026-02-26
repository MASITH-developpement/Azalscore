"""
AZALS - Service E-Invoicing France 2026
========================================

Service métier pour la facturation électronique.
Intégration complète avec les données financières et comptables du tenant.
"""
from __future__ import annotations


import asyncio
import hashlib
import logging
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.modules.country_packs.france.pdp_client import (
    PDPClientFactory,
    PDPConfig,
    PDPProvider,
    PDPInvoiceResponse,
    LifecycleStatus,
)
from app.modules.country_packs.france.einvoicing_webhooks import (
    WebhookNotificationService,
    get_webhook_service,
)

from app.modules.commercial.models import CommercialDocument, Customer, DocumentLine, DocumentType
from app.modules.country_packs.france.e_invoicing import (
    EInvoiceService as FacturXGenerator,
    EInvoiceDocument,
    EInvoiceParty as FacturXParty,
    EInvoiceLine as FacturXLine,
    EInvoiceType,
)
from app.modules.country_packs.france.einvoicing_models import (
    CompanySizeType,
    EInvoiceDirection,
    EInvoiceFormatDB,
    EInvoiceLifecycleEvent,
    EInvoiceRecord,
    EInvoiceStats,
    EInvoiceStatusDB,
    EReportingSubmission,
    PDPProviderType,
    TenantPDPConfig,
)
from app.modules.country_packs.france.einvoicing_schemas import (
    BulkGenerateRequest,
    BulkGenerateResponse,
    BulkSubmitRequest,
    BulkSubmitResponse,
    CompanySizeType as SchemaSizeType,
    EInvoiceCreateFromSource,
    EInvoiceCreateManual,
    EInvoiceDashboard,
    EInvoiceDetailResponse,
    EInvoiceDirection as SchemaDirection,
    EInvoiceFilter,
    EInvoiceFormat,
    EInvoiceParty,
    EInvoiceResponse,
    EInvoiceStatsResponse,
    EInvoiceStatsSummary,
    EInvoiceStatus,
    EInvoiceStatusUpdate,
    EInvoiceSubmitResponse,
    EReportingCreate,
    EReportingResponse,
    EReportingSubmitResponse,
    LifecycleEventCreate,
    LifecycleEventResponse,
    PDPConfigCreate,
    PDPConfigResponse,
    PDPConfigUpdate,
    PDPProviderType as SchemaProviderType,
    ValidationResult,
)
from app.modules.finance.models import JournalEntry
from app.modules.purchases.models import LegacyPurchaseInvoice, PurchaseSupplier

logger = logging.getLogger(__name__)


class TenantEInvoicingService:
    """
    Service e-invoicing multi-tenant.

    Gère toutes les opérations de facturation électronique pour un tenant :
    - Configuration PDP
    - Génération de factures électroniques depuis les documents commerciaux
    - Soumission aux PDP/PPF
    - Suivi du cycle de vie
    - E-reporting B2C
    - Statistiques
    """

    def __init__(self, db: Session, tenant_id: str) -> None:
        self.db: Session = db
        self.tenant_id: str = tenant_id
        self._facturx_generator: FacturXGenerator | None = None

    @property
    def facturx_generator(self) -> FacturXGenerator:
        """Lazy-load du générateur Factur-X."""
        if self._facturx_generator is None:
            self._facturx_generator = FacturXGenerator(self.db, self.tenant_id)
        return self._facturx_generator

    # =========================================================================
    # CONFIGURATION PDP
    # =========================================================================

    def list_pdp_configs(
        self,
        active_only: bool = True,
        provider: SchemaProviderType | None = None
    ) -> list[TenantPDPConfig]:
        """Liste les configurations PDP du tenant."""
        query = self.db.query(TenantPDPConfig).filter(
            TenantPDPConfig.tenant_id == self.tenant_id
        )

        if active_only:
            query = query.filter(TenantPDPConfig.is_active == True)

        if provider:
            query = query.filter(
                TenantPDPConfig.provider == PDPProviderType(provider.value)
            )

        return query.order_by(TenantPDPConfig.is_default.desc()).all()

    def get_pdp_config(self, config_id: uuid.UUID) -> TenantPDPConfig | None:
        """Récupère une configuration PDP."""
        return self.db.query(TenantPDPConfig).filter(
            TenantPDPConfig.id == config_id,
            TenantPDPConfig.tenant_id == self.tenant_id
        ).first()

    def get_default_pdp_config(self) -> TenantPDPConfig | None:
        """Récupère la configuration PDP par défaut."""
        return self.db.query(TenantPDPConfig).filter(
            TenantPDPConfig.tenant_id == self.tenant_id,
            TenantPDPConfig.is_default == True,
            TenantPDPConfig.is_active == True
        ).first()

    def create_pdp_config(
        self,
        data: PDPConfigCreate,
        created_by: uuid.UUID | None = None
    ) -> TenantPDPConfig:
        """Crée une configuration PDP."""
        # Si c'est la config par défaut, désactiver les autres
        if data.is_default:
            self._clear_default_pdp()

        config = TenantPDPConfig(
            tenant_id=self.tenant_id,
            provider=data.provider.value,  # Utiliser directement la valeur string
            name=data.name,
            description=data.description,
            api_url=data.api_url,
            token_url=data.token_url,
            client_id=data.client_id,
            client_secret=data.client_secret,
            scope=data.scope,
            certificate_ref=data.certificate_ref,
            private_key_ref=data.private_key_ref,
            siret=data.siret,
            siren=data.siren,
            tva_number=data.tva_number,
            company_size=data.company_size.value,  # Utiliser directement la valeur string
            is_active=data.is_active,
            is_default=data.is_default,
            test_mode=data.test_mode,
            timeout_seconds=data.timeout_seconds,
            retry_count=data.retry_count,
            webhook_url=data.webhook_url,
            webhook_secret=data.webhook_secret,
            preferred_format=data.preferred_format.value,  # Utiliser directement la valeur string
            generate_pdf=data.generate_pdf,
            provider_options=data.provider_options,
            custom_endpoints=data.custom_endpoints,
            created_by=created_by
        )

        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        logger.info(f"PDP config created: {config.id} for tenant {self.tenant_id}")
        return config

    def update_pdp_config(
        self,
        config_id: uuid.UUID,
        data: PDPConfigUpdate
    ) -> TenantPDPConfig | None:
        """Met à jour une configuration PDP."""
        config = self.get_pdp_config(config_id)
        if not config:
            return None

        # Gestion du flag default
        if data.is_default is True and not config.is_default:
            self._clear_default_pdp()

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "provider" and value:
                value = PDPProviderType(value.value)
            elif field == "company_size" and value:
                value = CompanySizeType(value.value)
            elif field == "preferred_format" and value:
                value = EInvoiceFormatDB(value.value)
            setattr(config, field, value)

        config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(config)

        return config

    def delete_pdp_config(self, config_id: uuid.UUID) -> bool:
        """Supprime une configuration PDP (soft delete)."""
        config = self.get_pdp_config(config_id)
        if not config:
            return False

        # Vérifier s'il y a des factures liées
        has_invoices = self.db.query(EInvoiceRecord).filter(
            EInvoiceRecord.pdp_config_id == config_id
        ).first() is not None

        if has_invoices:
            # Soft delete
            config.is_active = False
            config.is_default = False
        else:
            # Hard delete
            self.db.delete(config)

        self.db.commit()
        return True

    def _clear_default_pdp(self) -> None:
        """Retire le flag default de toutes les configs."""
        self.db.query(TenantPDPConfig).filter(
            TenantPDPConfig.tenant_id == self.tenant_id,
            TenantPDPConfig.is_default == True
        ).update({"is_default": False})

    # =========================================================================
    # GÉNÉRATION E-INVOICE DEPUIS DOCUMENTS
    # =========================================================================

    def create_einvoice_from_source(
        self,
        data: EInvoiceCreateFromSource,
        created_by: uuid.UUID | None = None
    ) -> EInvoiceRecord:
        """
        Crée une facture électronique depuis un document existant.

        Supporte:
        - INVOICE/CREDIT_NOTE: depuis CommercialDocument
        - PURCHASE_INVOICE: depuis LegacyPurchaseInvoice
        """
        pdp_config = None
        if data.pdp_config_id:
            pdp_config = self.get_pdp_config(data.pdp_config_id)
        else:
            pdp_config = self.get_default_pdp_config()

        if data.source_type in ("INVOICE", "CREDIT_NOTE"):
            return self._create_from_commercial_document(
                data, pdp_config, created_by
            )
        elif data.source_type == "PURCHASE_INVOICE":
            return self._create_from_purchase_invoice(
                data, pdp_config, created_by
            )
        else:
            raise ValueError(f"Source type non supporté: {data.source_type}")

    def _create_from_commercial_document(
        self,
        data: EInvoiceCreateFromSource,
        pdp_config: TenantPDPConfig | None,
        created_by: uuid.UUID | None
    ) -> EInvoiceRecord:
        """Crée e-invoice depuis CommercialDocument."""
        doc = self.db.query(CommercialDocument).options(
            joinedload(CommercialDocument.customer),
            joinedload(CommercialDocument.lines)
        ).filter(
            CommercialDocument.id == data.source_id,
            CommercialDocument.tenant_id == self.tenant_id
        ).first()

        if not doc:
            raise ValueError(f"Document non trouvé: {data.source_id}")

        # Vérifier le type
        expected_type = DocumentType.INVOICE if data.source_type == "INVOICE" else DocumentType.CREDIT_NOTE
        if doc.type != expected_type:
            raise ValueError(f"Type de document incompatible: {doc.type}")

        # Construire les parties
        seller = self._build_seller_from_tenant(pdp_config)
        buyer = self._build_buyer_from_customer(doc.customer)

        # Calculer les totaux TVA
        vat_breakdown = self._calculate_vat_breakdown(doc.lines)

        # Générer le XML Factur-X
        invoice_data = self._build_invoice_data(
            doc, seller, buyer, vat_breakdown, data.format
        )
        xml_content = self.facturx_generator.generate_xml(invoice_data)
        xml_hash = hashlib.sha256(xml_content.encode()).hexdigest()

        # Valider
        validation = self.facturx_generator.validate_xml(xml_content)

        # Créer l'enregistrement
        einvoice = EInvoiceRecord(
            tenant_id=self.tenant_id,
            pdp_config_id=pdp_config.id if pdp_config else None,
            direction=EInvoiceDirection.OUTBOUND,
            invoice_number=doc.number,
            invoice_type="380" if data.source_type == "INVOICE" else "381",
            format=EInvoiceFormatDB(data.format.value),
            source_invoice_id=doc.id,
            source_type=data.source_type,
            issue_date=doc.date,
            due_date=doc.due_date,
            seller_siret=seller.siret,
            seller_name=seller.name,
            seller_tva=seller.vat_number,
            buyer_siret=buyer.siret,
            buyer_name=buyer.name,
            buyer_tva=buyer.vat_number,
            buyer_routing_id=buyer.routing_id,
            currency=doc.currency,
            total_ht=doc.subtotal,
            total_tva=doc.tax_amount,
            total_ttc=doc.total,
            vat_breakdown=vat_breakdown,
            status=EInvoiceStatusDB.DRAFT,
            xml_content=xml_content,
            xml_hash=xml_hash,
            validation_errors=validation.get("errors", []),
            validation_warnings=validation.get("warnings", []),
            is_valid=validation.get("is_valid", False),
            extra_data=data.metadata,
            created_by=created_by
        )

        self.db.add(einvoice)
        self.db.commit()
        self.db.refresh(einvoice)

        # Ajouter événement lifecycle
        self._add_lifecycle_event(
            einvoice,
            status="CREATED",
            actor=str(created_by) if created_by else "SYSTEM",
            source="SYSTEM",
            message=f"Facture électronique créée depuis {data.source_type}"
        )

        # Auto-submit si demandé
        if data.auto_submit and einvoice.is_valid:
            self.submit_einvoice(einvoice.id, created_by)

        return einvoice

    def _create_from_purchase_invoice(
        self,
        data: EInvoiceCreateFromSource,
        pdp_config: TenantPDPConfig | None,
        created_by: uuid.UUID | None
    ) -> EInvoiceRecord:
        """Crée e-invoice depuis facture d'achat (INBOUND)."""
        invoice = self.db.query(LegacyPurchaseInvoice).options(
            joinedload(LegacyPurchaseInvoice.supplier),
            joinedload(LegacyPurchaseInvoice.lines)
        ).filter(
            LegacyPurchaseInvoice.id == data.source_id,
            LegacyPurchaseInvoice.tenant_id == self.tenant_id
        ).first()

        if not invoice:
            raise ValueError(f"Facture d'achat non trouvée: {data.source_id}")

        # Construire les parties
        buyer = self._build_seller_from_tenant(pdp_config)  # Nous sommes l'acheteur
        seller = self._build_seller_from_supplier(invoice.supplier)

        # Calculer TVA
        vat_breakdown = self._calculate_vat_breakdown_purchase(invoice.lines)

        einvoice = EInvoiceRecord(
            tenant_id=self.tenant_id,
            pdp_config_id=pdp_config.id if pdp_config else None,
            direction=EInvoiceDirection.INBOUND,
            invoice_number=invoice.number,
            invoice_type="380",
            format=EInvoiceFormatDB(data.format.value),
            source_invoice_id=invoice.id,
            source_type="PURCHASE_INVOICE",
            issue_date=invoice.invoice_date.date() if invoice.invoice_date else date.today(),
            due_date=invoice.due_date.date() if invoice.due_date else None,
            seller_siret=seller.siret,
            seller_name=seller.name,
            seller_tva=seller.vat_number,
            buyer_siret=buyer.siret,
            buyer_name=buyer.name,
            buyer_tva=buyer.vat_number,
            currency=invoice.currency,
            total_ht=invoice.total_ht,
            total_tva=invoice.total_tax,
            total_ttc=invoice.total_ttc,
            vat_breakdown=vat_breakdown,
            status=EInvoiceStatusDB.RECEIVED,
            is_valid=True,  # Facture reçue considérée valide
            reception_date=datetime.utcnow(),
            extra_data=data.metadata,
            created_by=created_by
        )

        self.db.add(einvoice)
        self.db.commit()
        self.db.refresh(einvoice)

        self._add_lifecycle_event(
            einvoice,
            status="RECEIVED",
            actor=str(created_by) if created_by else "SYSTEM",
            source="SYSTEM",
            message="Facture fournisseur enregistrée"
        )

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

        # Calculer les totaux
        total_ht = Decimal("0")
        total_tva = Decimal("0")
        vat_breakdown: dict[str, Decimal] = {}

        for line in data.lines:
            line_ht = line.quantity * line.unit_price * (1 - line.discount_percent / 100)
            line_tva = line_ht * line.vat_rate / 100
            total_ht += line_ht
            total_tva += line_tva

            rate_key = str(line.vat_rate)
            vat_breakdown[rate_key] = vat_breakdown.get(rate_key, Decimal("0")) + line_tva

        total_ttc = total_ht + total_tva

        # Préparer les données pour le générateur Factur-X
        invoice_data = {
            "invoice_number": data.invoice_number,
            "type": data.invoice_type,
            "issue_date": data.issue_date,
            "due_date": data.due_date,
            "seller_name": data.seller.name,
            "seller_siret": data.seller.siret,
            "seller_tva": data.seller.vat_number,
            "seller_address": data.seller.address_line1,
            "seller_postal_code": data.seller.postal_code,
            "seller_city": data.seller.city,
            "buyer_name": data.buyer.name,
            "buyer_siret": data.buyer.siret,
            "buyer_tva": data.buyer.vat_number,
            "buyer_address": data.buyer.address_line1,
            "buyer_postal_code": data.buyer.postal_code,
            "buyer_city": data.buyer.city,
            "lines": [
                {
                    "description": line.description,
                    "quantity": float(line.quantity),
                    "unit_price": float(line.unit_price),
                    "vat_rate": float(line.vat_rate),
                    "net_amount": float(line.quantity * line.unit_price * (1 - line.discount_percent / 100)),
                    "vat_amount": float(line.quantity * line.unit_price * (1 - line.discount_percent / 100) * line.vat_rate / 100)
                }
                for line in data.lines
            ],
            "total_ht": float(total_ht),
            "total_tva": float(total_tva),
            "total_ttc": float(total_ttc),
            "payment_means": data.payment_means_code or "30",
            "note": data.notes
        }

        # Créer le document et générer le XML
        doc = self.facturx_generator.create_einvoice(invoice_data)
        xml_content = self.facturx_generator.generate_facturx_xml(doc)
        xml_hash = hashlib.sha256(xml_content.encode()).hexdigest()
        validation = self.facturx_generator.validate_einvoice(doc)

        einvoice = EInvoiceRecord(
            tenant_id=self.tenant_id,
            pdp_config_id=pdp_config.id if pdp_config else None,
            direction=EInvoiceDirection(data.direction.value),
            invoice_number=data.invoice_number,
            invoice_type=data.invoice_type,
            format=EInvoiceFormatDB(data.format.value),
            issue_date=data.issue_date,
            due_date=data.due_date,
            seller_siret=data.seller.siret,
            seller_name=data.seller.name,
            seller_tva=data.seller.vat_number,
            buyer_siret=data.buyer.siret,
            buyer_name=data.buyer.name,
            buyer_tva=data.buyer.vat_number,
            buyer_routing_id=data.buyer.routing_id,
            currency=data.currency,
            total_ht=total_ht,
            total_tva=total_tva,
            total_ttc=total_ttc,
            vat_breakdown={str(k): float(v) for k, v in vat_breakdown.items()},
            status=EInvoiceStatusDB.DRAFT,
            xml_content=xml_content,
            xml_hash=xml_hash,
            validation_errors=validation.get("errors", []),
            validation_warnings=validation.get("warnings", []),
            is_valid=validation.get("is_valid", False),
            extra_data=data.metadata,
            created_by=created_by
        )

        self.db.add(einvoice)
        self.db.commit()
        self.db.refresh(einvoice)

        self._add_lifecycle_event(
            einvoice,
            status="CREATED",
            actor=str(created_by) if created_by else "SYSTEM",
            source="MANUAL",
            message="Facture électronique créée manuellement"
        )

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

        if not einvoice.is_valid:
            raise ValueError("Facture non valide, impossible de soumettre")

        if einvoice.status not in (EInvoiceStatusDB.DRAFT, EInvoiceStatusDB.VALIDATED, EInvoiceStatusDB.ERROR):
            raise ValueError(f"Statut incompatible pour soumission: {einvoice.status}")

        pdp_config_db = None
        if einvoice.pdp_config_id:
            pdp_config_db = self.get_pdp_config(einvoice.pdp_config_id)
        else:
            pdp_config_db = self.get_default_pdp_config()

        if not pdp_config_db:
            raise ValueError("Aucune configuration PDP disponible")

        # Générer un transaction_id
        transaction_id = f"TXN-{self.tenant_id[:8]}-{uuid.uuid4().hex[:12]}"
        einvoice.transaction_id = transaction_id

        try:
            # Construire la config pour le client PDP
            pdp_client_config = PDPConfig(
                provider=PDPProvider(pdp_config_db.provider.value if hasattr(pdp_config_db.provider, 'value') else pdp_config_db.provider),
                api_url=pdp_config_db.api_url,
                client_id=pdp_config_db.client_id or "",
                client_secret=pdp_config_db.client_secret or "",
                token_url=pdp_config_db.token_url,
                scope=pdp_config_db.scope,
                certificate_path=pdp_config_db.certificate_ref,
                private_key_path=pdp_config_db.private_key_ref,
                test_mode=pdp_config_db.test_mode,
                timeout=pdp_config_db.timeout_seconds or 30,
                retry_count=pdp_config_db.retry_count or 3,
                siret=pdp_config_db.siret,
                siren=pdp_config_db.siren,
                tva_number=pdp_config_db.tva_number,
                webhook_url=pdp_config_db.webhook_url,
                webhook_secret=pdp_config_db.webhook_secret,
            )

            # Reconstruire le document pour l'envoi
            doc = self._rebuild_document_from_einvoice(einvoice)

            # Soumettre au PDP (sync pour mode test, async pour production)
            pdp_response = self._submit_to_pdp_sync(pdp_client_config, doc, einvoice.xml_content)

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
                    self._add_lifecycle_event(
                        einvoice,
                        status=event.status.value if hasattr(event.status, 'value') else str(event.status),
                        actor=event.actor,
                        source="PDP",
                        message=event.message
                    )

                # Mettre à jour les stats
                self._update_stats(einvoice, "outbound_sent")

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

            self._add_lifecycle_event(
                einvoice,
                status="ERROR",
                actor=str(submitted_by) if submitted_by else "SYSTEM",
                source="PDP",
                message=f"Erreur de soumission: {str(e)}"
            )

            raise

    def _submit_to_pdp_sync(
        self,
        config: PDPConfig,
        doc: EInvoiceDocument,
        xml_content: str | None
    ) -> PDPInvoiceResponse:
        """
        Soumet la facture au PDP de manière synchrone.

        Utilise un thread séparé pour exécuter l'appel async aux clients PDP.
        Les clients PDP gèrent eux-mêmes le mode test/production.
        """
        import concurrent.futures

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

    def bulk_submit(
        self,
        data: BulkSubmitRequest,
        submitted_by: uuid.UUID | None = None
    ) -> BulkSubmitResponse:
        """Soumission en masse."""
        results = []
        submitted = 0
        failed = 0

        for einvoice_id in data.einvoice_ids:
            try:
                response = self.submit_einvoice(einvoice_id, submitted_by)
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
        created_by: uuid.UUID | None = None
    ) -> BulkGenerateResponse:
        """Génération en masse depuis documents sources."""
        einvoice_ids = []
        errors = []
        generated = 0
        failed = 0

        for source_id in data.source_ids:
            try:
                create_data = EInvoiceCreateFromSource(
                    source_type=data.source_type,
                    source_id=source_id,
                    format=data.format,
                    pdp_config_id=data.pdp_config_id
                )
                einvoice = self.create_einvoice_from_source(create_data, created_by)
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

    # =========================================================================
    # GESTION DES FACTURES
    # =========================================================================

    def get_einvoice(self, einvoice_id: uuid.UUID) -> EInvoiceRecord | None:
        """Récupère une facture électronique."""
        return self.db.query(EInvoiceRecord).filter(
            EInvoiceRecord.id == einvoice_id,
            EInvoiceRecord.tenant_id == self.tenant_id
        ).first()

    def get_einvoice_detail(self, einvoice_id: uuid.UUID) -> EInvoiceRecord | None:
        """Récupère une facture avec ses événements."""
        return self.db.query(EInvoiceRecord).options(
            joinedload(EInvoiceRecord.lifecycle_events),
            joinedload(EInvoiceRecord.pdp_config)
        ).filter(
            EInvoiceRecord.id == einvoice_id,
            EInvoiceRecord.tenant_id == self.tenant_id
        ).first()

    def list_einvoices(
        self,
        filters: EInvoiceFilter | None = None,
        page: int = 1,
        page_size: int = 25
    ) -> tuple[list[EInvoiceRecord], int]:
        """Liste les factures électroniques avec filtres."""
        query = self.db.query(EInvoiceRecord).filter(
            EInvoiceRecord.tenant_id == self.tenant_id
        )

        if filters:
            if filters.direction:
                query = query.filter(
                    EInvoiceRecord.direction == EInvoiceDirection(filters.direction.value)
                )
            if filters.status:
                query = query.filter(
                    EInvoiceRecord.status == EInvoiceStatusDB(filters.status.value)
                )
            if filters.format:
                query = query.filter(
                    EInvoiceRecord.format == EInvoiceFormatDB(filters.format.value)
                )
            if filters.pdp_config_id:
                query = query.filter(
                    EInvoiceRecord.pdp_config_id == filters.pdp_config_id
                )
            if filters.date_from:
                query = query.filter(EInvoiceRecord.issue_date >= filters.date_from)
            if filters.date_to:
                query = query.filter(EInvoiceRecord.issue_date <= filters.date_to)
            if filters.seller_siret:
                query = query.filter(EInvoiceRecord.seller_siret == filters.seller_siret)
            if filters.buyer_siret:
                query = query.filter(EInvoiceRecord.buyer_siret == filters.buyer_siret)
            if filters.source_type:
                query = query.filter(EInvoiceRecord.source_type == filters.source_type)
            if filters.has_errors is True:
                query = query.filter(EInvoiceRecord.error_count > 0)
            elif filters.has_errors is False:
                query = query.filter(
                    or_(EInvoiceRecord.error_count == 0, EInvoiceRecord.error_count.is_(None))
                )
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        EInvoiceRecord.invoice_number.ilike(search_term),
                        EInvoiceRecord.seller_name.ilike(search_term),
                        EInvoiceRecord.buyer_name.ilike(search_term),
                        EInvoiceRecord.ppf_id.ilike(search_term),
                        EInvoiceRecord.pdp_id.ilike(search_term)
                    )
                )

        total = query.count()

        items = query.order_by(
            EInvoiceRecord.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return items, total

    def update_einvoice_status(
        self,
        einvoice_id: uuid.UUID,
        data: EInvoiceStatusUpdate
    ) -> EInvoiceRecord | None:
        """Met à jour le statut d'une facture."""
        einvoice = self.get_einvoice(einvoice_id)
        if not einvoice:
            return None

        old_status = einvoice.status
        einvoice.status = EInvoiceStatusDB(data.status.value)

        if data.lifecycle_status:
            einvoice.lifecycle_status = data.lifecycle_status

        einvoice.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(einvoice)

        self._add_lifecycle_event(
            einvoice,
            status=data.status.value,
            actor=data.actor,
            source=data.source or "MANUAL",
            message=data.message or f"Statut mis à jour: {old_status} -> {data.status}"
        )

        # Mettre à jour les stats
        self._update_stats_on_status_change(einvoice, old_status, einvoice.status)

        # Envoyer notification webhook (async background)
        self._trigger_webhook_notification(
            einvoice,
            old_status,
            einvoice.status,
            data.message
        )

        return einvoice

    def _trigger_webhook_notification(
        self,
        einvoice: EInvoiceRecord,
        old_status: EInvoiceStatusDB | None,
        new_status: EInvoiceStatusDB,
        message: str | None = None
    ) -> None:
        """
        Déclenche une notification webhook de manière asynchrone.

        Utilise un thread séparé pour ne pas bloquer la requête principale.
        """
        import concurrent.futures

        def run_async_notification():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self._send_webhook_notification(einvoice, old_status, new_status, message)
                )
            except Exception as e:
                logger.warning(f"Erreur notification webhook: {e}")
            finally:
                loop.close()

        # Exécuter en background pour ne pas bloquer
        try:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            executor.submit(run_async_notification)
        except Exception as e:
            logger.warning(f"Impossible de lancer notification webhook: {e}")

    async def _send_webhook_notification(
        self,
        einvoice: EInvoiceRecord,
        old_status: EInvoiceStatusDB | None,
        new_status: EInvoiceStatusDB,
        message: str | None = None
    ) -> list[dict[str, Any]]:
        """Envoie les notifications webhook."""
        webhook_service = get_webhook_service(self.db)
        async with webhook_service:
            results = await webhook_service.notify_status_change(
                einvoice=einvoice,
                old_status=old_status,
                new_status=new_status,
                message=message
            )
            for result in results:
                if result.get("success"):
                    logger.info(f"Webhook envoyé: {result.get('url')}")
                else:
                    logger.warning(f"Échec webhook: {result.get('url')} - {result.get('error')}")
            return results

    def validate_einvoice(self, einvoice_id: uuid.UUID) -> ValidationResult:
        """Valide une facture électronique."""
        einvoice = self.get_einvoice(einvoice_id)
        if not einvoice:
            raise ValueError(f"Facture non trouvée: {einvoice_id}")

        # Reconstruire le document pour validation
        doc = self._rebuild_document_from_einvoice(einvoice)
        validation = self.facturx_generator.validate_einvoice(doc)

        einvoice.validation_errors = validation.get("errors", [])
        einvoice.validation_warnings = validation.get("warnings", [])
        einvoice.is_valid = validation.get("valid", False)  # Note: "valid" not "is_valid"

        if einvoice.is_valid and einvoice.status == EInvoiceStatusDB.DRAFT:
            einvoice.status = EInvoiceStatusDB.VALIDATED

        self.db.commit()
        self.db.refresh(einvoice)

        return ValidationResult(
            is_valid=einvoice.is_valid,
            errors=einvoice.validation_errors,
            warnings=einvoice.validation_warnings,
            profile=validation.get("profile"),
            format=EInvoiceFormat(einvoice.format.value) if einvoice.format else None
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

        # Recréer les lignes depuis vat_breakdown si pas d'autres données
        lines = []
        vat_breakdown = einvoice.vat_breakdown or {}
        line_num = 1
        for rate_str, amount in vat_breakdown.items():
            rate = Decimal(str(rate_str))
            vat_amount = Decimal(str(amount))
            # Estimer le montant HT pour cette ligne
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
        invoice_type = EInvoiceType.INVOICE  # Par défaut
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

    def submit_ereporting(
        self,
        ereporting_id: uuid.UUID,
        submitted_by: uuid.UUID | None = None
    ) -> EReportingSubmitResponse:
        """Soumet l'e-reporting au PPF."""
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
        self._update_ereporting_stats(submission)

        return EReportingSubmitResponse(
            ereporting_id=submission.id,
            submission_id=submission.submission_id,
            ppf_reference=submission.ppf_reference,
            status=submission.status,
            message="E-reporting soumis avec succès",
            submitted_at=submission.submitted_at
        )

    def list_ereporting(
        self,
        period: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 25
    ) -> tuple[list[EReportingSubmission], int]:
        """Liste les soumissions e-reporting."""
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

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def get_stats(self, period: str | None = None) -> EInvoiceStatsResponse | None:
        """Récupère les statistiques pour une période."""
        if not period:
            period = date.today().strftime("%Y-%m")

        stats = self.db.query(EInvoiceStats).filter(
            EInvoiceStats.tenant_id == self.tenant_id,
            EInvoiceStats.period == period
        ).first()

        if not stats:
            return None

        return EInvoiceStatsResponse.model_validate(stats)

    def get_stats_summary(self) -> EInvoiceStatsSummary:
        """Récupère le résumé des statistiques."""
        today = date.today()
        current_period = today.strftime("%Y-%m")

        # Mois précédent
        if today.month == 1:
            prev_period = f"{today.year - 1}-12"
        else:
            prev_period = f"{today.year}-{today.month - 1:02d}"

        current_stats = self.get_stats(current_period)
        previous_stats = self.get_stats(prev_period)

        # Calcul YTD
        ytd_stats = self.db.query(
            func.sum(EInvoiceStats.outbound_total).label("outbound_total"),
            func.sum(EInvoiceStats.inbound_total).label("inbound_total"),
            func.sum(EInvoiceStats.outbound_amount_ttc).label("outbound_amount"),
            func.sum(EInvoiceStats.inbound_amount_ttc).label("inbound_amount"),
        ).filter(
            EInvoiceStats.tenant_id == self.tenant_id,
            EInvoiceStats.period.like(f"{today.year}-%")
        ).first()

        return EInvoiceStatsSummary(
            current_month=current_stats,
            previous_month=previous_stats,
            year_to_date={
                "outbound_total": ytd_stats.outbound_total or 0,
                "inbound_total": ytd_stats.inbound_total or 0,
                "outbound_amount": ytd_stats.outbound_amount or Decimal("0"),
                "inbound_amount": ytd_stats.inbound_amount or Decimal("0"),
            }
        )

    def get_dashboard(self) -> EInvoiceDashboard:
        """Récupère les données du dashboard."""
        # Configs
        active_configs = self.list_pdp_configs(active_only=True)
        default_config = self.get_default_pdp_config()

        # Stats du mois
        today = date.today()
        current_period = today.strftime("%Y-%m")
        first_of_month = today.replace(day=1)

        outbound_count = self.db.query(func.count(EInvoiceRecord.id)).filter(
            EInvoiceRecord.tenant_id == self.tenant_id,
            EInvoiceRecord.direction == EInvoiceDirection.OUTBOUND,
            EInvoiceRecord.issue_date >= first_of_month
        ).scalar() or 0

        inbound_count = self.db.query(func.count(EInvoiceRecord.id)).filter(
            EInvoiceRecord.tenant_id == self.tenant_id,
            EInvoiceRecord.direction == EInvoiceDirection.INBOUND,
            EInvoiceRecord.issue_date >= first_of_month
        ).scalar() or 0

        pending_count = self.db.query(func.count(EInvoiceRecord.id)).filter(
            EInvoiceRecord.tenant_id == self.tenant_id,
            EInvoiceRecord.status.in_([EInvoiceStatusDB.DRAFT, EInvoiceStatusDB.VALIDATED])
        ).scalar() or 0

        errors_count = self.db.query(func.count(EInvoiceRecord.id)).filter(
            EInvoiceRecord.tenant_id == self.tenant_id,
            EInvoiceRecord.status == EInvoiceStatusDB.ERROR
        ).scalar() or 0

        # Récentes
        recent_outbound = self.db.query(EInvoiceRecord).filter(
            EInvoiceRecord.tenant_id == self.tenant_id,
            EInvoiceRecord.direction == EInvoiceDirection.OUTBOUND
        ).order_by(EInvoiceRecord.created_at.desc()).limit(5).all()

        recent_inbound = self.db.query(EInvoiceRecord).filter(
            EInvoiceRecord.tenant_id == self.tenant_id,
            EInvoiceRecord.direction == EInvoiceDirection.INBOUND
        ).order_by(EInvoiceRecord.created_at.desc()).limit(5).all()

        recent_errors = self.db.query(EInvoiceRecord).filter(
            EInvoiceRecord.tenant_id == self.tenant_id,
            EInvoiceRecord.status == EInvoiceStatusDB.ERROR
        ).order_by(EInvoiceRecord.updated_at.desc()).limit(5).all()

        # E-reporting
        ereporting_pending = self.db.query(func.count(EReportingSubmission.id)).filter(
            EReportingSubmission.tenant_id == self.tenant_id,
            EReportingSubmission.status == "DRAFT"
        ).scalar() or 0

        current_ereporting = self.db.query(EReportingSubmission).filter(
            EReportingSubmission.tenant_id == self.tenant_id,
            EReportingSubmission.period == current_period
        ).first()

        # Alertes
        alerts = []
        if not default_config:
            alerts.append("Aucune configuration PDP par défaut")
        if errors_count > 0:
            alerts.append(f"{errors_count} facture(s) en erreur")
        if pending_count > 10:
            alerts.append(f"{pending_count} factures en attente de soumission")

        return EInvoiceDashboard(
            active_pdp_configs=len(active_configs),
            default_pdp=PDPConfigResponse.model_validate(default_config) if default_config else None,
            outbound_this_month=outbound_count,
            inbound_this_month=inbound_count,
            pending_actions=pending_count,
            errors_count=errors_count,
            recent_outbound=[EInvoiceResponse.model_validate(e) for e in recent_outbound],
            recent_inbound=[EInvoiceResponse.model_validate(e) for e in recent_inbound],
            recent_errors=[EInvoiceResponse.model_validate(e) for e in recent_errors],
            ereporting_pending=ereporting_pending,
            ereporting_current_period=EReportingResponse.model_validate(current_ereporting) if current_ereporting else None,
            alerts=alerts
        )

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

        # Trouver la facture
        einvoice = None
        if payload.get("ppf_id"):
            einvoice = self.db.query(EInvoiceRecord).filter(
                EInvoiceRecord.tenant_id == self.tenant_id,
                EInvoiceRecord.ppf_id == payload["ppf_id"]
            ).first()
        elif payload.get("pdp_id"):
            einvoice = self.db.query(EInvoiceRecord).filter(
                EInvoiceRecord.tenant_id == self.tenant_id,
                EInvoiceRecord.pdp_id == payload["pdp_id"]
            ).first()
        elif payload.get("invoice_id"):
            einvoice = self.db.query(EInvoiceRecord).filter(
                EInvoiceRecord.tenant_id == self.tenant_id,
                EInvoiceRecord.transaction_id == payload["invoice_id"]
            ).first()

        if not einvoice:
            return {"error": "Facture non trouvée", "payload": payload}

        # Mettre à jour le statut
        event_type = payload.get("event_type", "").upper()
        new_status = None

        status_mapping = {
            "DEPOSITED": EInvoiceStatusDB.SENT,
            "TRANSMITTED": EInvoiceStatusDB.DELIVERED,
            "RECEIVED": EInvoiceStatusDB.RECEIVED,
            "ACCEPTED": EInvoiceStatusDB.ACCEPTED,
            "REFUSED": EInvoiceStatusDB.REFUSED,
            "PAID": EInvoiceStatusDB.PAID,
            "CANCELLED": EInvoiceStatusDB.CANCELLED,
            "ERROR": EInvoiceStatusDB.ERROR,
        }

        if event_type in status_mapping:
            old_status = einvoice.status
            new_status = status_mapping[event_type]
            einvoice.status = new_status
            einvoice.lifecycle_status = payload.get("lifecycle_status")
            einvoice.updated_at = datetime.utcnow()

            self.db.commit()

            self._add_lifecycle_event(
                einvoice,
                status=event_type,
                actor=payload.get("actor"),
                source="WEBHOOK",
                message=payload.get("message"),
                details=payload.get("details", {})
            )

            self._update_stats_on_status_change(einvoice, old_status, new_status)

        return {
            "processed": True,
            "einvoice_id": str(einvoice.id),
            "new_status": new_status.value if new_status else None
        }

    # =========================================================================
    # HELPERS PRIVÉS
    # =========================================================================

    def _build_seller_from_tenant(
        self,
        pdp_config: TenantPDPConfig | None
    ) -> EInvoiceParty:
        """Construit les infos vendeur depuis config tenant."""
        # NOTE: Phase 2 - Récupérer depuis configuration tenant globale
        return EInvoiceParty(
            name=pdp_config.name if pdp_config else "Entreprise",
            siret=pdp_config.siret if pdp_config else None,
            siren=pdp_config.siren if pdp_config else None,
            vat_number=pdp_config.tva_number if pdp_config else None,
            country_code="FR"
        )

    def _build_buyer_from_customer(self, customer: Customer) -> EInvoiceParty:
        """Construit les infos acheteur depuis Customer."""
        return EInvoiceParty(
            name=customer.name,
            siret=customer.registration_number,
            vat_number=customer.tax_id,
            address_line1=customer.address_line1,
            address_line2=customer.address_line2,
            city=customer.city,
            postal_code=customer.postal_code,
            country_code=customer.country_code or "FR",
            email=customer.email,
            phone=customer.phone
        )

    def _build_seller_from_supplier(self, supplier: PurchaseSupplier) -> EInvoiceParty:
        """Construit les infos vendeur depuis Supplier."""
        return EInvoiceParty(
            name=supplier.name,
            siret=supplier.tax_id,  # SIRET dans tax_id
            vat_number=supplier.tax_id,
            address_line1=supplier.address,
            city=supplier.city,
            postal_code=supplier.postal_code,
            country_code=supplier.country or "FR",
            email=supplier.email,
            phone=supplier.phone
        )

    def _calculate_vat_breakdown(
        self,
        lines: list[DocumentLine]
    ) -> dict[str, float]:
        """Calcule la ventilation TVA depuis DocumentLine."""
        breakdown: dict[str, Decimal] = {}
        for line in lines:
            rate = line.tax_rate or 20.0
            rate_key = f"{rate:.2f}"
            breakdown[rate_key] = breakdown.get(rate_key, Decimal("0")) + (line.tax_amount or Decimal("0"))
        return {k: float(v) for k, v in breakdown.items()}

    def _calculate_vat_breakdown_purchase(
        self,
        lines
    ) -> dict[str, float]:
        """Calcule la ventilation TVA depuis PurchaseInvoiceLine."""
        breakdown: dict[str, Decimal] = {}
        for line in lines:
            rate = line.tax_rate or Decimal("20")
            rate_key = f"{rate:.2f}"
            breakdown[rate_key] = breakdown.get(rate_key, Decimal("0")) + (line.tax_amount or Decimal("0"))
        return {k: float(v) for k, v in breakdown.items()}

    def _build_invoice_data(
        self,
        doc: CommercialDocument,
        seller: EInvoiceParty,
        buyer: EInvoiceParty,
        vat_breakdown: dict[str, float],
        format: EInvoiceFormat
    ) -> dict[str, Any]:
        """Construit les données pour génération XML."""
        lines_data = []
        for line in doc.lines:
            lines_data.append({
                "description": line.description,
                "quantity": float(line.quantity or 1),
                "unit": line.unit or "C62",
                "unit_price": float(line.unit_price or 0),
                "discount_percent": float(line.discount_percent or 0),
                "vat_rate": float(line.tax_rate or 20),
                "vat_category": "S",
                "subtotal": float(line.subtotal or 0),
                "tax_amount": float(line.tax_amount or 0),
                "total": float(line.total or 0)
            })

        return {
            "number": doc.number,
            "type_code": "380" if doc.type == DocumentType.INVOICE else "381",
            "issue_date": doc.date,
            "due_date": doc.due_date,
            "currency": doc.currency,
            "profile": format.value,
            "seller": seller.model_dump(),
            "buyer": buyer.model_dump(),
            "lines": lines_data,
            "total_ht": float(doc.subtotal or 0),
            "total_tva": float(doc.tax_amount or 0),
            "total_ttc": float(doc.total or 0),
            "vat_breakdown": vat_breakdown
        }

    def _add_lifecycle_event(
        self,
        einvoice: EInvoiceRecord,
        status: str,
        actor: str | None = None,
        source: str | None = None,
        message: str | None = None,
        details: dict[str, Any] | None = None
    ):
        """Ajoute un événement au cycle de vie."""
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

    def _update_stats(self, einvoice: EInvoiceRecord, field: str) -> None:
        """Met à jour les statistiques."""
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
            stats.outbound_amount_ttc = (stats.outbound_amount_ttc or Decimal("0")) + einvoice.total_ttc
        else:
            stats.inbound_amount_ttc = (stats.inbound_amount_ttc or Decimal("0")) + einvoice.total_ttc

        self.db.commit()

    def _update_stats_on_status_change(
        self,
        einvoice: EInvoiceRecord,
        old_status: EInvoiceStatusDB,
        new_status: EInvoiceStatusDB
    ) -> None:
        """Met à jour les stats sur changement de statut."""
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

    def _update_ereporting_stats(self, submission: EReportingSubmission) -> None:
        """Met à jour les stats e-reporting."""
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
        stats.ereporting_amount = (stats.ereporting_amount or Decimal("0")) + submission.total_ttc

        self.db.commit()


    # =========================================================================
    # RÉCEPTION FACTURES ENTRANTES (INBOUND)
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
        """
        Reçoit et enregistre une facture entrante depuis XML Factur-X.

        Parse le XML, valide et crée l'enregistrement.
        Retourne le record créé et le résultat de validation.
        """
        import base64
        import defusedxml.ElementTree as ET  # Sécurisé contre XXE attacks

        # Parser le XML
        try:
            parsed_data = self._parse_facturx_xml(xml_content)
        except Exception as e:
            raise ValueError(f"Erreur parsing XML: {str(e)}")

        # Déterminer le format depuis le XML
        format_detected = self._detect_xml_format(xml_content)

        # Calculer le hash
        xml_hash = hashlib.sha256(xml_content.encode()).hexdigest()

        # Créer le PDP config par défaut si besoin
        pdp_config = self.get_default_pdp_config()

        # Créer l'enregistrement
        einvoice = EInvoiceRecord(
            tenant_id=self.tenant_id,
            pdp_config_id=pdp_config.id if pdp_config else None,
            direction=EInvoiceDirection.INBOUND,
            invoice_number=parsed_data.get("invoice_number", f"INB-{uuid.uuid4().hex[:8]}"),
            invoice_type=parsed_data.get("invoice_type", "380"),
            format=format_detected,
            ppf_id=ppf_id,
            pdp_id=pdp_id,
            issue_date=parsed_data.get("issue_date", date.today()),
            due_date=parsed_data.get("due_date"),
            reception_date=datetime.utcnow(),
            seller_siret=parsed_data.get("seller_siret"),
            seller_name=parsed_data.get("seller_name"),
            seller_tva=parsed_data.get("seller_tva"),
            buyer_siret=parsed_data.get("buyer_siret"),
            buyer_name=parsed_data.get("buyer_name"),
            buyer_tva=parsed_data.get("buyer_tva"),
            currency=parsed_data.get("currency", "EUR"),
            total_ht=Decimal(str(parsed_data.get("total_ht", 0))),
            total_tva=Decimal(str(parsed_data.get("total_tva", 0))),
            total_ttc=Decimal(str(parsed_data.get("total_ttc", 0))),
            vat_breakdown=parsed_data.get("vat_breakdown", {}),
            status=EInvoiceStatusDB.RECEIVED,
            xml_content=xml_content,
            xml_hash=xml_hash,
            is_valid=True,
            extra_data=metadata or {},
            created_by=received_by
        )

        # Stocker le PDF si fourni
        if pdf_base64:
            einvoice.pdf_storage_ref = f"inbound/{self.tenant_id}/{einvoice.id}.pdf"
            # NOTE: Phase 2 - Sauvegarder PDF via storage_service

        self.db.add(einvoice)
        self.db.commit()
        self.db.refresh(einvoice)

        # Ajouter événement lifecycle
        self._add_lifecycle_event(
            einvoice,
            status="RECEIVED",
            actor=source_pdp or "EXTERNAL",
            source="PDP" if source_pdp else "MANUAL",
            message=f"Facture reçue depuis {source_pdp or 'source externe'}",
            details={"ppf_id": ppf_id, "pdp_id": pdp_id}
        )

        # Valider la facture
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "profile": format_detected.value
        }

        # Mettre à jour les stats
        self._update_stats(einvoice, "inbound_total")

        return einvoice, validation_result

    def receive_inbound_parsed(
        self,
        data: dict[str, Any],
        received_by: uuid.UUID | None = None
    ) -> tuple[EInvoiceRecord, dict[str, Any]]:
        """
        Reçoit une facture entrante avec données déjà parsées.

        Utilisé quand le parsing a déjà été fait (ex: par le PDP).
        """
        from app.modules.country_packs.france.einvoicing_schemas import EInvoiceFormat

        pdp_config = self.get_default_pdp_config()

        # Calculer hash si XML fourni
        xml_hash = None
        if data.get("xml_content"):
            xml_hash = hashlib.sha256(data["xml_content"].encode()).hexdigest()

        # Calculer les totaux si pas fournis
        total_ht = Decimal(str(data.get("total_ht", 0)))
        total_tva = Decimal(str(data.get("total_tva", 0)))
        total_ttc = Decimal(str(data.get("total_ttc", total_ht + total_tva)))

        einvoice = EInvoiceRecord(
            tenant_id=self.tenant_id,
            pdp_config_id=pdp_config.id if pdp_config else None,
            direction=EInvoiceDirection.INBOUND,
            invoice_number=data.get("invoice_number", f"INB-{uuid.uuid4().hex[:8]}"),
            invoice_type=data.get("invoice_type", "380"),
            format=EInvoiceFormatDB(data.get("format", EInvoiceFormat.FACTURX_EN16931).value),
            ppf_id=data.get("ppf_id"),
            pdp_id=data.get("pdp_id"),
            issue_date=data.get("issue_date", date.today()),
            due_date=data.get("due_date"),
            reception_date=data.get("received_at") or datetime.utcnow(),
            seller_siret=data.get("seller", {}).get("siret"),
            seller_name=data.get("seller", {}).get("name"),
            seller_tva=data.get("seller", {}).get("vat_number"),
            buyer_siret=data.get("buyer", {}).get("siret"),
            buyer_name=data.get("buyer", {}).get("name"),
            buyer_tva=data.get("buyer", {}).get("vat_number"),
            currency=data.get("currency", "EUR"),
            total_ht=total_ht,
            total_tva=total_tva,
            total_ttc=total_ttc,
            vat_breakdown=data.get("vat_breakdown", {}),
            status=EInvoiceStatusDB.RECEIVED,
            xml_content=data.get("xml_content"),
            xml_hash=xml_hash,
            is_valid=True,
            extra_data=data.get("metadata", {}),
            created_by=received_by
        )

        self.db.add(einvoice)
        self.db.commit()
        self.db.refresh(einvoice)

        self._add_lifecycle_event(
            einvoice,
            status="RECEIVED",
            actor=data.get("source_pdp", "EXTERNAL"),
            source="PDP" if data.get("source_pdp") else "MANUAL",
            message="Facture entrante enregistrée"
        )

        self._update_stats(einvoice, "inbound_total")

        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "profile": einvoice.format.value
        }

        return einvoice, validation_result

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

        if einvoice.direction != EInvoiceDirection.INBOUND:
            raise ValueError("Cette méthode est réservée aux factures entrantes")

        if einvoice.status not in (EInvoiceStatusDB.RECEIVED, EInvoiceStatusDB.VALIDATED):
            raise ValueError(f"Statut incompatible: {einvoice.status}")

        old_status = einvoice.status
        einvoice.status = EInvoiceStatusDB.ACCEPTED
        einvoice.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(einvoice)

        self._add_lifecycle_event(
            einvoice,
            status="ACCEPTED",
            actor=str(accepted_by) if accepted_by else "SYSTEM",
            source="MANUAL",
            message=message or "Facture acceptée"
        )

        self._update_stats_on_status_change(einvoice, old_status, EInvoiceStatusDB.ACCEPTED)

        # Notification webhook
        self._trigger_webhook_notification(einvoice, old_status, EInvoiceStatusDB.ACCEPTED, message)

        return einvoice

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

        if einvoice.direction != EInvoiceDirection.INBOUND:
            raise ValueError("Cette méthode est réservée aux factures entrantes")

        if einvoice.status not in (EInvoiceStatusDB.RECEIVED, EInvoiceStatusDB.VALIDATED):
            raise ValueError(f"Statut incompatible: {einvoice.status}")

        old_status = einvoice.status
        einvoice.status = EInvoiceStatusDB.REFUSED
        einvoice.last_error = reason
        einvoice.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(einvoice)

        self._add_lifecycle_event(
            einvoice,
            status="REFUSED",
            actor=str(refused_by) if refused_by else "SYSTEM",
            source="MANUAL",
            message=reason or "Facture refusée"
        )

        self._update_stats_on_status_change(einvoice, old_status, EInvoiceStatusDB.REFUSED)

        # Notification webhook
        self._trigger_webhook_notification(einvoice, old_status, EInvoiceStatusDB.REFUSED, reason)

        return einvoice

    def _parse_facturx_xml(self, xml_content: str) -> dict[str, Any]:
        """Parse un XML Factur-X et extrait les données clés."""
        import defusedxml.ElementTree as ET  # Sécurisé contre XXE attacks

        # Namespaces Factur-X / CII
        namespaces = {
            'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
            'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
            'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100',
            'qdt': 'urn:un:unece:uncefact:data:standard:QualifiedDataType:100',
        }

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"XML invalide: {e}")

        result: dict[str, Any] = {}

        # Essayer le format Factur-X / CII
        header = root.find('.//rsm:ExchangedDocument', namespaces)
        if header is not None:
            # Numéro de facture
            id_elem = header.find('ram:ID', namespaces)
            if id_elem is not None:
                result["invoice_number"] = id_elem.text

            # Type de document
            type_elem = header.find('ram:TypeCode', namespaces)
            if type_elem is not None:
                result["invoice_type"] = type_elem.text

            # Date d'émission
            date_elem = header.find('.//ram:IssueDateTime/udt:DateTimeString', namespaces)
            if date_elem is not None:
                try:
                    result["issue_date"] = datetime.strptime(date_elem.text[:10], "%Y%m%d").date()
                except (ValueError, TypeError):
                    try:
                        result["issue_date"] = datetime.strptime(date_elem.text[:10], "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        pass

        # Transaction
        transaction = root.find('.//rsm:SupplyChainTradeTransaction', namespaces)
        if transaction is not None:
            # Vendeur
            seller = transaction.find('.//ram:SellerTradeParty', namespaces)
            if seller is not None:
                name = seller.find('ram:Name', namespaces)
                if name is not None:
                    result["seller_name"] = name.text

                # SIRET
                siret = seller.find('.//ram:SpecifiedLegalOrganization/ram:ID', namespaces)
                if siret is not None:
                    result["seller_siret"] = siret.text

                # TVA
                vat = seller.find('.//ram:SpecifiedTaxRegistration/ram:ID', namespaces)
                if vat is not None:
                    result["seller_tva"] = vat.text

            # Acheteur
            buyer = transaction.find('.//ram:BuyerTradeParty', namespaces)
            if buyer is not None:
                name = buyer.find('ram:Name', namespaces)
                if name is not None:
                    result["buyer_name"] = name.text

                siret = buyer.find('.//ram:SpecifiedLegalOrganization/ram:ID', namespaces)
                if siret is not None:
                    result["buyer_siret"] = siret.text

                vat = buyer.find('.//ram:SpecifiedTaxRegistration/ram:ID', namespaces)
                if vat is not None:
                    result["buyer_tva"] = vat.text

            # Montants
            settlement = transaction.find('.//ram:ApplicableHeaderTradeSettlement', namespaces)
            if settlement is not None:
                # Devise
                currency = settlement.find('ram:InvoiceCurrencyCode', namespaces)
                if currency is not None:
                    result["currency"] = currency.text

                # Échéance
                due_date = settlement.find('.//ram:SpecifiedTradePaymentTerms/ram:DueDateDateTime/udt:DateTimeString', namespaces)
                if due_date is not None:
                    try:
                        result["due_date"] = datetime.strptime(due_date.text[:10], "%Y%m%d").date()
                    except (ValueError, TypeError):
                        pass

                # Totaux
                totals = settlement.find('.//ram:SpecifiedTradeSettlementHeaderMonetarySummation', namespaces)
                if totals is not None:
                    ht = totals.find('ram:TaxBasisTotalAmount', namespaces)
                    if ht is not None:
                        result["total_ht"] = float(ht.text)

                    tva = totals.find('ram:TaxTotalAmount', namespaces)
                    if tva is not None:
                        result["total_tva"] = float(tva.text)

                    ttc = totals.find('ram:GrandTotalAmount', namespaces)
                    if ttc is not None:
                        result["total_ttc"] = float(ttc.text)

        # Si pas de données trouvées, essayer format UBL
        if not result.get("invoice_number"):
            result = self._parse_ubl_xml(root)

        return result

    def _parse_ubl_xml(self, root) -> dict[str, Any]:
        """Parse un XML UBL."""
        namespaces = {
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        }

        result: dict[str, Any] = {}

        # ID
        id_elem = root.find('.//cbc:ID', namespaces)
        if id_elem is not None:
            result["invoice_number"] = id_elem.text

        # Type
        type_elem = root.find('.//cbc:InvoiceTypeCode', namespaces)
        if type_elem is not None:
            result["invoice_type"] = type_elem.text

        # Date
        date_elem = root.find('.//cbc:IssueDate', namespaces)
        if date_elem is not None:
            try:
                result["issue_date"] = datetime.strptime(date_elem.text, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

        # Due date
        due_elem = root.find('.//cbc:DueDate', namespaces)
        if due_elem is not None:
            try:
                result["due_date"] = datetime.strptime(due_elem.text, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

        # Devise
        currency_elem = root.find('.//cbc:DocumentCurrencyCode', namespaces)
        if currency_elem is not None:
            result["currency"] = currency_elem.text

        # Vendeur
        seller = root.find('.//cac:AccountingSupplierParty/cac:Party', namespaces)
        if seller is not None:
            name = seller.find('.//cac:PartyLegalEntity/cbc:RegistrationName', namespaces)
            if name is not None:
                result["seller_name"] = name.text

            siret = seller.find('.//cac:PartyLegalEntity/cbc:CompanyID', namespaces)
            if siret is not None:
                result["seller_siret"] = siret.text

            vat = seller.find('.//cac:PartyTaxScheme/cbc:CompanyID', namespaces)
            if vat is not None:
                result["seller_tva"] = vat.text

        # Acheteur
        buyer = root.find('.//cac:AccountingCustomerParty/cac:Party', namespaces)
        if buyer is not None:
            name = buyer.find('.//cac:PartyLegalEntity/cbc:RegistrationName', namespaces)
            if name is not None:
                result["buyer_name"] = name.text

            siret = buyer.find('.//cac:PartyLegalEntity/cbc:CompanyID', namespaces)
            if siret is not None:
                result["buyer_siret"] = siret.text

        # Totaux
        total = root.find('.//cac:LegalMonetaryTotal', namespaces)
        if total is not None:
            ht = total.find('cbc:TaxExclusiveAmount', namespaces)
            if ht is not None:
                result["total_ht"] = float(ht.text)

            ttc = total.find('cbc:TaxInclusiveAmount', namespaces)
            if ttc is not None:
                result["total_ttc"] = float(ttc.text)

            if result.get("total_ht") and result.get("total_ttc"):
                result["total_tva"] = result["total_ttc"] - result["total_ht"]

        return result

    def _detect_xml_format(self, xml_content: str) -> EInvoiceFormatDB:
        """Détecte le format du XML (Factur-X profile ou UBL)."""
        if "CrossIndustryInvoice" in xml_content:
            if "EXTENDED" in xml_content or "urn:factur-x.eu:1p0:extended" in xml_content:
                return EInvoiceFormatDB.FACTURX_EXTENDED
            elif "BASIC" in xml_content or "urn:factur-x.eu:1p0:basic" in xml_content:
                return EInvoiceFormatDB.FACTURX_BASIC
            elif "MINIMUM" in xml_content or "urn:factur-x.eu:1p0:minimum" in xml_content:
                return EInvoiceFormatDB.FACTURX_MINIMUM
            else:
                return EInvoiceFormatDB.FACTURX_EN16931
        elif "urn:oasis:names:specification:ubl" in xml_content:
            return EInvoiceFormatDB.UBL_21
        elif "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice" in xml_content:
            return EInvoiceFormatDB.CII_D16B
        else:
            return EInvoiceFormatDB.FACTURX_EN16931


def get_einvoicing_service(db: Session, tenant_id: str) -> TenantEInvoicingService:
    """Factory pour le service e-invoicing."""
    return TenantEInvoicingService(db, tenant_id)
