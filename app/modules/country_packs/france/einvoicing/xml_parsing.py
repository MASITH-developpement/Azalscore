"""
AZALSCORE - E-Invoicing XML Parsing
Parsing des formats Factur-X (CII) et UBL
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import defusedxml.ElementTree as ET  # Sécurisé contre XXE attacks

from app.modules.country_packs.france.einvoicing_models import EInvoiceFormatDB


class XMLParsingError(Exception):
    """Erreur lors du parsing XML."""
    pass


class EInvoiceXMLParser:
    """
    Parser pour les formats de facture électronique.

    Supporte:
    - Factur-X (CII - Cross Industry Invoice)
    - UBL 2.1
    """

    # Namespaces Factur-X / CII
    CII_NAMESPACES = {
        'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
        'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
        'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100',
        'qdt': 'urn:un:unece:uncefact:data:standard:QualifiedDataType:100',
    }

    # Namespaces UBL
    UBL_NAMESPACES = {
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    }

    def parse(self, xml_content: str) -> dict[str, Any]:
        """
        Parse un XML de facture électronique.

        Args:
            xml_content: Contenu XML brut

        Returns:
            Dictionnaire avec les données extraites

        Raises:
            XMLParsingError: Si le parsing échoue
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise XMLParsingError(f"XML invalide: {e}")

        # Essayer Factur-X / CII d'abord
        result = self._parse_facturx(root)

        # Si pas de données trouvées, essayer UBL
        if not result.get("invoice_number"):
            result = self._parse_ubl(root)

        return result

    def detect_format(self, xml_content: str) -> EInvoiceFormatDB:
        """
        Détecte le format du XML.

        Args:
            xml_content: Contenu XML brut

        Returns:
            Format détecté (enum EInvoiceFormatDB)
        """
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

    def _parse_facturx(self, root) -> dict[str, Any]:
        """Parse un XML Factur-X (CII)."""
        ns = self.CII_NAMESPACES
        result: dict[str, Any] = {}

        # Header - ExchangedDocument
        header = root.find('.//rsm:ExchangedDocument', ns)
        if header is not None:
            # Numéro de facture
            id_elem = header.find('ram:ID', ns)
            if id_elem is not None:
                result["invoice_number"] = id_elem.text

            # Type de document
            type_elem = header.find('ram:TypeCode', ns)
            if type_elem is not None:
                result["invoice_type"] = type_elem.text

            # Date d'émission
            date_elem = header.find('.//ram:IssueDateTime/udt:DateTimeString', ns)
            if date_elem is not None:
                result["issue_date"] = self._parse_date(date_elem.text)

        # Transaction
        transaction = root.find('.//rsm:SupplyChainTradeTransaction', ns)
        if transaction is not None:
            self._parse_facturx_parties(transaction, result)
            self._parse_facturx_settlement(transaction, result)

        return result

    def _parse_facturx_parties(self, transaction, result: dict[str, Any]) -> None:
        """Parse les parties (vendeur/acheteur) Factur-X."""
        ns = self.CII_NAMESPACES

        # Vendeur
        seller = transaction.find('.//ram:SellerTradeParty', ns)
        if seller is not None:
            name = seller.find('ram:Name', ns)
            if name is not None:
                result["seller_name"] = name.text

            # SIRET
            siret = seller.find('.//ram:SpecifiedLegalOrganization/ram:ID', ns)
            if siret is not None:
                result["seller_siret"] = siret.text

            # TVA
            vat = seller.find('.//ram:SpecifiedTaxRegistration/ram:ID', ns)
            if vat is not None:
                result["seller_tva"] = vat.text

        # Acheteur
        buyer = transaction.find('.//ram:BuyerTradeParty', ns)
        if buyer is not None:
            name = buyer.find('ram:Name', ns)
            if name is not None:
                result["buyer_name"] = name.text

            siret = buyer.find('.//ram:SpecifiedLegalOrganization/ram:ID', ns)
            if siret is not None:
                result["buyer_siret"] = siret.text

            vat = buyer.find('.//ram:SpecifiedTaxRegistration/ram:ID', ns)
            if vat is not None:
                result["buyer_tva"] = vat.text

    def _parse_facturx_settlement(self, transaction, result: dict[str, Any]) -> None:
        """Parse les données de règlement Factur-X."""
        ns = self.CII_NAMESPACES

        settlement = transaction.find('.//ram:ApplicableHeaderTradeSettlement', ns)
        if settlement is None:
            return

        # Devise
        currency = settlement.find('ram:InvoiceCurrencyCode', ns)
        if currency is not None:
            result["currency"] = currency.text

        # Échéance
        due_date = settlement.find(
            './/ram:SpecifiedTradePaymentTerms/ram:DueDateDateTime/udt:DateTimeString', ns
        )
        if due_date is not None:
            result["due_date"] = self._parse_date(due_date.text)

        # Totaux
        totals = settlement.find('.//ram:SpecifiedTradeSettlementHeaderMonetarySummation', ns)
        if totals is not None:
            ht = totals.find('ram:TaxBasisTotalAmount', ns)
            if ht is not None:
                result["total_ht"] = float(ht.text)

            tva = totals.find('ram:TaxTotalAmount', ns)
            if tva is not None:
                result["total_tva"] = float(tva.text)

            ttc = totals.find('ram:GrandTotalAmount', ns)
            if ttc is not None:
                result["total_ttc"] = float(ttc.text)

    def _parse_ubl(self, root) -> dict[str, Any]:
        """Parse un XML UBL 2.1."""
        ns = self.UBL_NAMESPACES
        result: dict[str, Any] = {}

        # ID
        id_elem = root.find('.//cbc:ID', ns)
        if id_elem is not None:
            result["invoice_number"] = id_elem.text

        # Type
        type_elem = root.find('.//cbc:InvoiceTypeCode', ns)
        if type_elem is not None:
            result["invoice_type"] = type_elem.text

        # Dates
        date_elem = root.find('.//cbc:IssueDate', ns)
        if date_elem is not None:
            result["issue_date"] = self._parse_date(date_elem.text)

        due_elem = root.find('.//cbc:DueDate', ns)
        if due_elem is not None:
            result["due_date"] = self._parse_date(due_elem.text)

        # Devise
        currency_elem = root.find('.//cbc:DocumentCurrencyCode', ns)
        if currency_elem is not None:
            result["currency"] = currency_elem.text

        # Parties
        self._parse_ubl_parties(root, result)

        # Totaux
        self._parse_ubl_totals(root, result)

        return result

    def _parse_ubl_parties(self, root, result: dict[str, Any]) -> None:
        """Parse les parties UBL."""
        ns = self.UBL_NAMESPACES

        # Vendeur
        seller = root.find('.//cac:AccountingSupplierParty/cac:Party', ns)
        if seller is not None:
            name = seller.find('.//cac:PartyLegalEntity/cbc:RegistrationName', ns)
            if name is not None:
                result["seller_name"] = name.text

            siret = seller.find('.//cac:PartyLegalEntity/cbc:CompanyID', ns)
            if siret is not None:
                result["seller_siret"] = siret.text

            vat = seller.find('.//cac:PartyTaxScheme/cbc:CompanyID', ns)
            if vat is not None:
                result["seller_tva"] = vat.text

        # Acheteur
        buyer = root.find('.//cac:AccountingCustomerParty/cac:Party', ns)
        if buyer is not None:
            name = buyer.find('.//cac:PartyLegalEntity/cbc:RegistrationName', ns)
            if name is not None:
                result["buyer_name"] = name.text

            siret = buyer.find('.//cac:PartyLegalEntity/cbc:CompanyID', ns)
            if siret is not None:
                result["buyer_siret"] = siret.text

    def _parse_ubl_totals(self, root, result: dict[str, Any]) -> None:
        """Parse les totaux UBL."""
        ns = self.UBL_NAMESPACES

        total = root.find('.//cac:LegalMonetaryTotal', ns)
        if total is None:
            return

        ht = total.find('cbc:TaxExclusiveAmount', ns)
        if ht is not None:
            result["total_ht"] = float(ht.text)

        ttc = total.find('cbc:TaxInclusiveAmount', ns)
        if ttc is not None:
            result["total_ttc"] = float(ttc.text)

        if result.get("total_ht") and result.get("total_ttc"):
            result["total_tva"] = result["total_ttc"] - result["total_ht"]

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse une date depuis différents formats."""
        if not date_str:
            return None

        date_str = date_str[:10]  # Prendre les 10 premiers caractères

        formats = ["%Y%m%d", "%Y-%m-%d", "%d/%m/%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None


# Instance singleton
_xml_parser: EInvoiceXMLParser | None = None


def get_xml_parser() -> EInvoiceXMLParser:
    """Retourne l'instance singleton du parser XML."""
    global _xml_parser
    if _xml_parser is None:
        _xml_parser = EInvoiceXMLParser()
    return _xml_parser
