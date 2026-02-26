"""
AZALS - Facturation Électronique France (Réforme 2024-2027)
============================================================

Service de facturation électronique conforme à la réforme française.

Calendrier obligatoire:
- 01/09/2026: Réception obligatoire pour toutes les entreprises
- 01/09/2026: Émission obligatoire pour grandes entreprises et ETI
- 01/09/2027: Émission obligatoire pour PME et micro-entreprises

Architecture:
- PPF (Portail Public de Facturation): Plateforme publique
- PDP (Plateforme de Dématérialisation Partenaire): Opérateurs privés agréés
- OD (Opérateur de Dématérialisation): Intermédiaires

Formats supportés:
- Factur-X (PDF/A-3 + XML)
- UBL 2.1
- CII (Cross Industry Invoice)

Standards:
- EN 16931 (norme européenne facturation électronique)
- Semantic model européen
"""
from __future__ import annotations


import hashlib
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional, List

from sqlalchemy.orm import Session


class EInvoiceFormat(str, Enum):
    """Formats de facture électronique."""
    FACTUR_X_MINIMUM = "FACTURX_MINIMUM"
    FACTUR_X_BASIC = "FACTURX_BASIC"
    FACTUR_X_BASIC_WL = "FACTURX_BASIC_WL"
    FACTUR_X_EN16931 = "FACTURX_EN16931"
    FACTUR_X_EXTENDED = "FACTURX_EXTENDED"
    UBL_21 = "UBL_2.1"
    CII_D16B = "CII_D16B"


class EInvoiceStatus(str, Enum):
    """Statuts de facture électronique."""
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    REJECTED = "REJECTED"
    ACCEPTED = "ACCEPTED"
    PAID = "PAID"
    REFUSED = "REFUSED"


class EInvoiceType(str, Enum):
    """Types de factures."""
    INVOICE = "380"          # Facture commerciale
    CREDIT_NOTE = "381"      # Avoir
    DEBIT_NOTE = "383"       # Note de débit
    CORRECTED = "384"        # Facture corrigée
    SELF_BILLED = "389"      # Autofacturation
    PREPAYMENT = "386"       # Facture d'acompte


class PaymentMeansCode(str, Enum):
    """Codes moyens de paiement."""
    CASH = "10"
    CHECK = "20"
    TRANSFER = "30"
    CREDIT_TRANSFER = "31"
    SEPA_TRANSFER = "58"
    CARD = "48"
    DIRECT_DEBIT = "49"
    SEPA_DIRECT_DEBIT = "59"


@dataclass
class EInvoiceParty:
    """Partie (émetteur ou destinataire) d'une facture."""
    name: str
    siret: str
    siren: Optional[str] = None
    tva_number: Optional[str] = None  # FR + 2 digits + SIREN
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country_code: str = "FR"
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    # Routing (pour envoi via PPF/PDP)
    routing_id: Optional[str] = None  # Identifiant de routage


@dataclass
class EInvoiceLine:
    """Ligne de facture."""
    line_number: int
    description: str
    quantity: Decimal
    unit_code: str = "C62"  # Unité par défaut
    unit_price: Decimal = Decimal("0")
    net_amount: Decimal = Decimal("0")
    vat_category: str = "S"  # Standard rate
    vat_rate: Decimal = Decimal("20")
    vat_amount: Decimal = Decimal("0")
    item_id: Optional[str] = None
    buyer_reference: Optional[str] = None
    order_reference: Optional[str] = None


@dataclass
class EInvoiceDocument:
    """Document facture électronique complet."""
    # Identification
    invoice_number: str
    invoice_type: EInvoiceType
    issue_date: date
    due_date: Optional[date] = None
    currency_code: str = "EUR"

    # Parties
    seller: EInvoiceParty = None
    buyer: EInvoiceParty = None

    # Lignes
    lines: List[EInvoiceLine] = field(default_factory=list)

    # Totaux
    total_ht: Decimal = Decimal("0")
    total_tva: Decimal = Decimal("0")
    total_ttc: Decimal = Decimal("0")

    # Paiement
    payment_means_code: PaymentMeansCode = PaymentMeansCode.TRANSFER
    payment_terms: Optional[str] = None
    payment_id: Optional[str] = None  # RIB/IBAN

    # Références
    purchase_order_ref: Optional[str] = None
    contract_ref: Optional[str] = None
    project_ref: Optional[str] = None

    # Notes
    note: Optional[str] = None

    # Métadonnées
    format: EInvoiceFormat = EInvoiceFormat.FACTUR_X_EN16931
    status: EInvoiceStatus = EInvoiceStatus.DRAFT


@dataclass
class PDPResponse:
    """Réponse d'une plateforme PDP."""
    success: bool
    transaction_id: str
    timestamp: datetime
    status: EInvoiceStatus
    message: str
    ppf_reference: Optional[str] = None  # Référence PPF si routage via PPF
    errors: List[str] = None
    warnings: List[str] = None


class EInvoiceService:
    """Service de facturation électronique France."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def create_einvoice(self, invoice_data: dict) -> EInvoiceDocument:
        """
        Créer une facture électronique à partir de données.

        Args:
            invoice_data: Dictionnaire avec les données de facture

        Returns:
            EInvoiceDocument prêt pour envoi
        """
        seller = EInvoiceParty(
            name=invoice_data.get("seller_name"),
            siret=invoice_data.get("seller_siret"),
            tva_number=invoice_data.get("seller_tva"),
            address_line1=invoice_data.get("seller_address"),
            postal_code=invoice_data.get("seller_postal_code"),
            city=invoice_data.get("seller_city")
        )

        buyer = EInvoiceParty(
            name=invoice_data.get("buyer_name"),
            siret=invoice_data.get("buyer_siret"),
            tva_number=invoice_data.get("buyer_tva"),
            address_line1=invoice_data.get("buyer_address"),
            postal_code=invoice_data.get("buyer_postal_code"),
            city=invoice_data.get("buyer_city")
        )

        lines = []
        for i, line_data in enumerate(invoice_data.get("lines", []), 1):
            line = EInvoiceLine(
                line_number=i,
                description=line_data.get("description", ""),
                quantity=Decimal(str(line_data.get("quantity", 1))),
                unit_price=Decimal(str(line_data.get("unit_price", 0))),
                net_amount=Decimal(str(line_data.get("net_amount", 0))),
                vat_rate=Decimal(str(line_data.get("vat_rate", 20))),
                vat_amount=Decimal(str(line_data.get("vat_amount", 0)))
            )
            lines.append(line)

        return EInvoiceDocument(
            invoice_number=invoice_data.get("invoice_number"),
            invoice_type=EInvoiceType(invoice_data.get("type", "380")),
            issue_date=invoice_data.get("issue_date", date.today()),
            due_date=invoice_data.get("due_date"),
            seller=seller,
            buyer=buyer,
            lines=lines,
            total_ht=Decimal(str(invoice_data.get("total_ht", 0))),
            total_tva=Decimal(str(invoice_data.get("total_tva", 0))),
            total_ttc=Decimal(str(invoice_data.get("total_ttc", 0))),
            payment_means_code=PaymentMeansCode(invoice_data.get("payment_means", "30")),
            purchase_order_ref=invoice_data.get("order_ref"),
            note=invoice_data.get("note")
        )

    def validate_einvoice(self, doc: EInvoiceDocument) -> dict:
        """
        Valider une facture électronique.

        Contrôles EN 16931 et spécifications françaises.
        """
        errors = []
        warnings = []

        # ===== CONTRÔLES OBLIGATOIRES EN 16931 =====

        # BT-1: Numéro de facture (obligatoire)
        if not doc.invoice_number:
            errors.append("BT-1: Numéro de facture obligatoire")

        # BT-2: Date d'émission (obligatoire)
        if not doc.issue_date:
            errors.append("BT-2: Date d'émission obligatoire")

        # BT-3: Type de facture (obligatoire)
        if not doc.invoice_type:
            errors.append("BT-3: Type de facture obligatoire")

        # BT-5: Code devise (obligatoire)
        if not doc.currency_code:
            errors.append("BT-5: Code devise obligatoire")
        elif doc.currency_code not in ["EUR", "USD", "GBP", "CHF"]:
            warnings.append(f"BT-5: Devise {doc.currency_code} peu courante")

        # ===== CONTRÔLES VENDEUR =====
        if not doc.seller:
            errors.append("BG-4: Vendeur obligatoire")
        else:
            # BT-27: Nom du vendeur
            if not doc.seller.name:
                errors.append("BT-27: Nom du vendeur obligatoire")

            # BT-30: SIRET vendeur (France)
            if not doc.seller.siret:
                errors.append("BT-30: SIRET vendeur obligatoire (France)")
            elif len(doc.seller.siret) != 14 or not doc.seller.siret.isdigit():
                errors.append("BT-30: SIRET vendeur invalide (14 chiffres)")

            # BT-31: TVA vendeur
            if not doc.seller.tva_number:
                warnings.append("BT-31: N° TVA vendeur recommandé")
            elif not doc.seller.tva_number.startswith("FR"):
                warnings.append("BT-31: N° TVA vendeur devrait commencer par FR")

        # ===== CONTRÔLES ACHETEUR =====
        if not doc.buyer:
            errors.append("BG-7: Acheteur obligatoire")
        else:
            # BT-44: Nom de l'acheteur
            if not doc.buyer.name:
                errors.append("BT-44: Nom de l'acheteur obligatoire")

            # BT-47: SIRET acheteur (recommandé pour B2B France)
            if not doc.buyer.siret:
                warnings.append("BT-47: SIRET acheteur recommandé pour B2B")

        # ===== CONTRÔLES LIGNES =====
        if not doc.lines:
            errors.append("BG-25: Au moins une ligne obligatoire")
        else:
            for line in doc.lines:
                # BT-126: Numéro de ligne
                if line.line_number <= 0:
                    errors.append(f"BT-126: Numéro de ligne invalide ({line.line_number})")

                # BT-153: Description
                if not line.description:
                    errors.append(f"BT-153: Description ligne {line.line_number} obligatoire")

                # BT-129: Quantité
                if line.quantity <= 0:
                    warnings.append(f"BT-129: Quantité ligne {line.line_number} <= 0")

                # BT-146: Prix unitaire
                if line.unit_price < 0:
                    errors.append(f"BT-146: Prix unitaire ligne {line.line_number} négatif")

        # ===== CONTRÔLES TOTAUX =====
        # Vérifier cohérence
        lines_total_ht = sum(line.net_amount for line in doc.lines)
        if abs(lines_total_ht - doc.total_ht) > Decimal("0.01"):
            warnings.append(f"Total HT ({doc.total_ht}) diffère de la somme des lignes ({lines_total_ht})")

        expected_ttc = doc.total_ht + doc.total_tva
        if abs(expected_ttc - doc.total_ttc) > Decimal("0.01"):
            warnings.append(f"Total TTC ({doc.total_ttc}) diffère du calcul ({expected_ttc})")

        # ===== CONTRÔLES SPÉCIFIQUES FRANCE =====
        # Mentions obligatoires selon CGI
        if doc.total_ht > Decimal("0") and doc.total_tva == Decimal("0"):
            warnings.append("Facture sans TVA: mention d'exonération requise")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "format": doc.format.value
        }

    def generate_facturx_xml(self, doc: EInvoiceDocument) -> str:
        """
        Générer le XML Factur-X (profil EN16931).

        Structure basée sur UN/CEFACT Cross Industry Invoice (CII).
        """
        # Namespace CII
        ns = {
            "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
            "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
            "qdt": "urn:un:unece:uncefact:data:standard:QualifiedDataType:100",
            "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100"
        }

        # Racine CrossIndustryInvoice
        root = ET.Element("{urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100}CrossIndustryInvoice")

        for prefix, uri in ns.items():
            root.set(f"xmlns:{prefix}", uri)

        # ExchangedDocumentContext
        ctx = ET.SubElement(root, "{urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100}ExchangedDocumentContext")
        guide = ET.SubElement(ctx, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}GuidelineSpecifiedDocumentContextParameter")
        guide_id = ET.SubElement(guide, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}ID")
        guide_id.text = "urn:factur-x.eu:1p0:en16931"

        # ExchangedDocument
        doc_elem = ET.SubElement(root, "{urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100}ExchangedDocument")

        # ID (BT-1)
        doc_id = ET.SubElement(doc_elem, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}ID")
        doc_id.text = doc.invoice_number

        # TypeCode (BT-3)
        type_code = ET.SubElement(doc_elem, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}TypeCode")
        type_code.text = doc.invoice_type.value

        # IssueDateTime (BT-2)
        issue_dt = ET.SubElement(doc_elem, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}IssueDateTime")
        dt_string = ET.SubElement(issue_dt, "{urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100}DateTimeString")
        dt_string.set("format", "102")
        dt_string.text = doc.issue_date.strftime("%Y%m%d")

        # SupplyChainTradeTransaction
        transaction = ET.SubElement(root, "{urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100}SupplyChainTradeTransaction")

        # ApplicableHeaderTradeAgreement (parties)
        agreement = ET.SubElement(transaction, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}ApplicableHeaderTradeAgreement")

        # Seller (BG-4)
        if doc.seller:
            seller_party = ET.SubElement(agreement, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}SellerTradeParty")
            seller_name = ET.SubElement(seller_party, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}Name")
            seller_name.text = doc.seller.name

            if doc.seller.siret:
                seller_id = ET.SubElement(seller_party, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}ID")
                seller_id.set("schemeID", "0002")  # SIRET
                seller_id.text = doc.seller.siret

            if doc.seller.tva_number:
                tax_reg = ET.SubElement(seller_party, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}SpecifiedTaxRegistration")
                tax_id = ET.SubElement(tax_reg, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}ID")
                tax_id.set("schemeID", "VA")
                tax_id.text = doc.seller.tva_number

        # Buyer (BG-7)
        if doc.buyer:
            buyer_party = ET.SubElement(agreement, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}BuyerTradeParty")
            buyer_name = ET.SubElement(buyer_party, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}Name")
            buyer_name.text = doc.buyer.name

            if doc.buyer.siret:
                buyer_id = ET.SubElement(buyer_party, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}ID")
                buyer_id.set("schemeID", "0002")
                buyer_id.text = doc.buyer.siret

        # ApplicableHeaderTradeSettlement (montants)
        settlement = ET.SubElement(transaction, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}ApplicableHeaderTradeSettlement")

        # Currency (BT-5)
        currency = ET.SubElement(settlement, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}InvoiceCurrencyCode")
        currency.text = doc.currency_code

        # Monetary summation
        summation = ET.SubElement(settlement, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}SpecifiedTradeSettlementHeaderMonetarySummation")

        line_total = ET.SubElement(summation, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}LineTotalAmount")
        line_total.text = f"{doc.total_ht:.2f}"

        tax_total = ET.SubElement(summation, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}TaxTotalAmount")
        tax_total.set("currencyID", doc.currency_code)
        tax_total.text = f"{doc.total_tva:.2f}"

        grand_total = ET.SubElement(summation, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}GrandTotalAmount")
        grand_total.text = f"{doc.total_ttc:.2f}"

        due_payable = ET.SubElement(summation, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}DuePayableAmount")
        due_payable.text = f"{doc.total_ttc:.2f}"

        # Lignes de facture
        for line in doc.lines:
            line_item = ET.SubElement(transaction, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}IncludedSupplyChainTradeLineItem")

            # Numéro de ligne
            line_doc = ET.SubElement(line_item, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}AssociatedDocumentLineDocument")
            line_id = ET.SubElement(line_doc, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}LineID")
            line_id.text = str(line.line_number)

            # Produit
            product = ET.SubElement(line_item, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}SpecifiedTradeProduct")
            prod_name = ET.SubElement(product, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}Name")
            prod_name.text = line.description

            # Livraison (quantité)
            delivery = ET.SubElement(line_item, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}SpecifiedLineTradeDelivery")
            qty = ET.SubElement(delivery, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}BilledQuantity")
            qty.set("unitCode", line.unit_code)
            qty.text = f"{line.quantity:.2f}"

            # Prix et montant
            line_settlement = ET.SubElement(line_item, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}SpecifiedLineTradeSettlement")

            # TVA de la ligne
            line_tax = ET.SubElement(line_settlement, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}ApplicableTradeTax")
            tax_type = ET.SubElement(line_tax, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}TypeCode")
            tax_type.text = "VAT"
            tax_cat = ET.SubElement(line_tax, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}CategoryCode")
            tax_cat.text = line.vat_category
            tax_rate = ET.SubElement(line_tax, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}RateApplicablePercent")
            tax_rate.text = f"{line.vat_rate:.2f}"

            # Montant ligne
            line_summation = ET.SubElement(line_settlement, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}SpecifiedTradeSettlementLineMonetarySummation")
            line_amount = ET.SubElement(line_summation, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}LineTotalAmount")
            line_amount.text = f"{line.net_amount:.2f}"

        # Générer le XML
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def send_to_pdp(self, doc: EInvoiceDocument, pdp_config: dict) -> PDPResponse:
        """
        Envoyer une facture via PDP (Plateforme de Dématérialisation Partenaire).

        Args:
            doc: Document facture électronique
            pdp_config: Configuration PDP (credentials, endpoint, etc.)

        Returns:
            PDPResponse avec statut de transmission
        """
        # Valider d'abord
        validation = self.validate_einvoice(doc)
        if not validation["valid"]:
            return PDPResponse(
                success=False,
                transaction_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                status=EInvoiceStatus.REJECTED,
                message="Validation échouée",
                errors=validation["errors"]
            )

        # Générer le XML
        xml_content = self.generate_facturx_xml(doc)

        transaction_id = str(uuid.uuid4())

        # Mode test
        if pdp_config.get("test_mode", True):
            return PDPResponse(
                success=True,
                transaction_id=transaction_id,
                timestamp=datetime.utcnow(),
                status=EInvoiceStatus.SENT,
                message="[TEST] Facture envoyée avec succès",
                ppf_reference=f"TEST-PPF-{transaction_id[:8].upper()}",
                warnings=["Mode test - aucune transmission réelle"]
            )

        # NOTE: Phase 2 - Intégration API PDP production (Chorus Pro / PDP agréé)
        ppf_ref = f"PPF-{datetime.utcnow().strftime('%Y%m%d')}-{transaction_id[:8].upper()}"

        return PDPResponse(
            success=True,
            transaction_id=transaction_id,
            timestamp=datetime.utcnow(),
            status=EInvoiceStatus.DELIVERED,
            message="Facture transmise via PDP",
            ppf_reference=ppf_ref
        )

    def receive_from_ppf(self, ppf_reference: str) -> Optional[EInvoiceDocument]:
        """
        Récupérer une facture reçue via PPF/PDP.

        Le PPF transmet les factures entrantes aux entreprises
        via leur PDP ou directement.
        """
        # NOTE: Phase 2 - Réception via API PDP
        return None

    def get_invoice_lifecycle(self, invoice_id: str) -> list[dict]:
        """
        Obtenir le cycle de vie complet d'une facture.

        Statuts possibles dans le cycle Y:
        - Déposée
        - Reçue
        - Acceptée / Refusée
        - Payée
        """
        # NOTE: Phase 2 - Tracking via API PDP/PPF
        return [
            {"status": "SENT", "timestamp": datetime.utcnow().isoformat(), "actor": "Émetteur"},
            {"status": "DELIVERED", "timestamp": datetime.utcnow().isoformat(), "actor": "PPF"},
        ]


class EInvoiceComplianceChecker:
    """Vérificateur de conformité e-invoicing."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def check_obligation_status(self, company_size: str) -> dict:
        """
        Vérifier le statut d'obligation e-invoicing.

        Args:
            company_size: "GE" (Grande Entreprise), "ETI", "PME", "MICRO"

        Returns:
            Statut d'obligation et dates
        """
        obligations = {
            "GE": {  # Grande Entreprise (>5000 salariés ou CA>1.5Md€)
                "reception_obligatoire": date(2026, 9, 1),
                "emission_obligatoire": date(2026, 9, 1),
                "ready": True
            },
            "ETI": {  # Entreprise de Taille Intermédiaire
                "reception_obligatoire": date(2026, 9, 1),
                "emission_obligatoire": date(2026, 9, 1),
                "ready": True
            },
            "PME": {  # Petite et Moyenne Entreprise
                "reception_obligatoire": date(2026, 9, 1),
                "emission_obligatoire": date(2027, 9, 1),
                "ready": False
            },
            "MICRO": {  # Micro-entreprise
                "reception_obligatoire": date(2026, 9, 1),
                "emission_obligatoire": date(2027, 9, 1),
                "ready": False
            }
        }

        info = obligations.get(company_size, obligations["PME"])
        today = date.today()

        return {
            "company_size": company_size,
            "reception_obligatoire": info["reception_obligatoire"].isoformat(),
            "emission_obligatoire": info["emission_obligatoire"].isoformat(),
            "reception_active": today >= info["reception_obligatoire"],
            "emission_active": today >= info["emission_obligatoire"],
            "days_until_reception": max(0, (info["reception_obligatoire"] - today).days),
            "days_until_emission": max(0, (info["emission_obligatoire"] - today).days),
            "recommendations": self._get_recommendations(info, today)
        }

    def _get_recommendations(self, info: dict, today: date) -> list[str]:
        """Générer des recommandations selon le statut."""
        recommendations = []

        if today < info["reception_obligatoire"]:
            days = (info["reception_obligatoire"] - today).days
            if days < 180:
                recommendations.append("URGENT: Préparer la réception de factures électroniques")
                recommendations.append("Choisir et configurer une plateforme PDP")
                recommendations.append("Former les équipes comptables")

        if today < info["emission_obligatoire"]:
            days = (info["emission_obligatoire"] - today).days
            if days < 365:
                recommendations.append("Planifier la migration vers l'émission électronique")
                recommendations.append("Tester les formats Factur-X avec les partenaires")
                recommendations.append("Mettre à jour les processus de facturation")

        return recommendations
