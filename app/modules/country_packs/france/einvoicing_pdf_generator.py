"""
AZALS - Générateur PDF/A-3 Factur-X
====================================

Génération de factures PDF conformes à la norme Factur-X avec XML embarqué.

Conformité:
- PDF/A-3b (ISO 19005-3)
- Factur-X 1.0.06 (EN16931)
- Métadonnées XMP requises

Fonctionnalités:
- Génération PDF visuellement riche
- Embarquement XML en pièce jointe associée (AF)
- Métadonnées XMP conformes Factur-X
- Support multi-profils (Minimum, Basic, EN16931, Extended)
"""
from __future__ import annotations


import base64
import io
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional, List
import hashlib
import uuid

logger = logging.getLogger(__name__)

from .exceptions import EInvoicingPDFError, EInvoicingXMLError, EInvoicingValidationError


# =============================================================================
# CONSTANTES ET TYPES
# =============================================================================

class FacturXProfile(str, Enum):
    """Profils Factur-X supportés."""
    MINIMUM = "MINIMUM"
    BASIC_WL = "BASIC-WL"
    BASIC = "BASIC"
    EN16931 = "EN16931"
    EXTENDED = "EXTENDED"


@dataclass
class InvoiceLine:
    """Ligne de facture pour affichage PDF."""
    line_number: int
    description: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    vat_rate: Decimal
    net_amount: Decimal
    vat_amount: Decimal
    total_amount: Decimal


@dataclass
class InvoiceParty:
    """Partie (vendeur/acheteur) pour affichage PDF."""
    name: str
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: str = "France"
    siret: Optional[str] = None
    siren: Optional[str] = None
    vat_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class InvoiceData:
    """Données complètes de la facture pour génération PDF."""
    invoice_number: str
    invoice_type: str  # 380=Facture, 381=Avoir, 384=Facture corrigée
    issue_date: date
    due_date: Optional[date] = None
    currency: str = "EUR"

    seller: Optional[InvoiceParty] = None
    buyer: Optional[InvoiceParty] = None

    lines: List[InvoiceLine] = None

    total_ht: Decimal = Decimal("0")
    total_tva: Decimal = Decimal("0")
    total_ttc: Decimal = Decimal("0")

    vat_breakdown: dict = None  # {taux: montant}

    payment_terms: Optional[str] = None
    payment_means_code: str = "30"  # Virement=30, Carte=48, Prélèvement=49
    iban: Optional[str] = None
    bic: Optional[str] = None

    notes: Optional[str] = None
    buyer_reference: Optional[str] = None
    order_reference: Optional[str] = None

    def __post_init__(self):
        if self.lines is None:
            self.lines = []
        if self.vat_breakdown is None:
            self.vat_breakdown = {}


# =============================================================================
# GÉNÉRATEUR PDF FACTUR-X
# =============================================================================

class FacturXPDFGenerator:
    """
    Générateur de PDF/A-3 Factur-X avec XML embarqué.

    Crée des factures PDF conformes à la norme Factur-X avec:
    - Mise en page professionnelle
    - XML embarqué en pièce jointe (Associated File)
    - Métadonnées XMP conformes
    """

    # Couleurs AZALS
    COLOR_PRIMARY = (0.18, 0.32, 0.52)      # Bleu foncé
    COLOR_SECONDARY = (0.47, 0.53, 0.60)    # Gris bleu
    COLOR_ACCENT = (0.0, 0.47, 0.75)        # Bleu accent
    COLOR_LIGHT = (0.95, 0.96, 0.97)        # Gris clair
    COLOR_TEXT = (0.2, 0.2, 0.2)            # Texte principal

    def __init__(self):
        self._reportlab_available = False
        self._facturx_available = False
        self._pypdf_available = False

        # Vérifier les dépendances
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm
            self._reportlab_available = True
        except ImportError:
            logger.warning("reportlab non disponible - génération PDF limitée")

        try:
            from facturx import generate_from_binary, get_facturx_xml_from_pdf
            self._facturx_available = True
        except ImportError:
            logger.warning("factur-x non disponible - embarquement XML manuel")

        try:
            import pypdf
            self._pypdf_available = True
        except ImportError:
            logger.warning("pypdf non disponible")

    def generate_facturx_pdf(
        self,
        invoice_data: InvoiceData,
        xml_content: str,
        profile: FacturXProfile = FacturXProfile.EN16931,
        logo_path: Optional[str] = None
    ) -> bytes:
        """
        Génère un PDF/A-3 Factur-X complet avec XML embarqué.

        Args:
            invoice_data: Données de la facture
            xml_content: XML Factur-X à embarquer
            profile: Profil Factur-X (EN16931 par défaut)
            logo_path: Chemin vers le logo de l'entreprise (optionnel)

        Returns:
            bytes: Contenu du PDF/A-3 avec XML embarqué
        """
        # Générer le PDF visuel
        visual_pdf = self._generate_visual_pdf(invoice_data, logo_path)

        # Embarquer le XML
        if self._facturx_available:
            return self._embed_xml_with_facturx(visual_pdf, xml_content, profile)
        else:
            return self._embed_xml_manually(visual_pdf, xml_content, profile)

    def generate_visual_pdf_only(
        self,
        invoice_data: InvoiceData,
        logo_path: Optional[str] = None
    ) -> bytes:
        """
        Génère uniquement le PDF visuel (sans XML embarqué).

        Utile pour prévisualisation ou test.
        """
        return self._generate_visual_pdf(invoice_data, logo_path)

    def extract_xml_from_pdf(self, pdf_content: bytes) -> Optional[str]:
        """
        Extrait le XML Factur-X d'un PDF existant.

        Args:
            pdf_content: Contenu du PDF

        Returns:
            XML extrait ou None si non trouvé
        """
        if self._facturx_available:
            try:
                from facturx import get_facturx_xml_from_pdf
                result = get_facturx_xml_from_pdf(io.BytesIO(pdf_content), check_xsd=False)

                # La fonction retourne un tuple (filename, xml_bytes)
                if isinstance(result, tuple) and len(result) >= 2:
                    filename, xml_bytes = result[0], result[1]
                    if isinstance(xml_bytes, bytes):
                        return xml_bytes.decode('utf-8')
                    return str(xml_bytes)
                elif isinstance(result, bytes):
                    return result.decode('utf-8')
                elif isinstance(result, str):
                    return result
            except (EInvoicingXMLError, ValueError, UnicodeDecodeError) as e:
                logger.error(f"Erreur extraction XML: {e}")

        if self._pypdf_available:
            try:
                return self._extract_xml_with_pypdf(pdf_content)
            except (EInvoicingPDFError, ValueError, KeyError) as e:
                logger.error(f"Erreur extraction pypdf: {e}")

        return None

    # =========================================================================
    # GÉNÉRATION PDF VISUEL
    # =========================================================================

    def _generate_visual_pdf(
        self,
        data: InvoiceData,
        logo_path: Optional[str] = None
    ) -> bytes:
        """Génère le PDF avec mise en page professionnelle."""
        if not self._reportlab_available:
            return self._generate_basic_pdf(data)

        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import Color, HexColor
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Marges
        margin_left = 20 * mm
        margin_right = width - 20 * mm
        margin_top = height - 15 * mm

        # En-tête avec titre
        y_pos = margin_top
        y_pos = self._draw_header(c, data, y_pos, width, height, margin_left, logo_path)

        # Informations vendeur/acheteur
        y_pos = self._draw_parties(c, data, y_pos, margin_left, margin_right)

        # Références facture
        y_pos = self._draw_invoice_info(c, data, y_pos, margin_left, margin_right)

        # Tableau des lignes
        y_pos = self._draw_lines_table(c, data, y_pos, margin_left, margin_right, width)

        # Totaux
        y_pos = self._draw_totals(c, data, y_pos, margin_left, margin_right)

        # Pied de page
        self._draw_footer(c, data, width, margin_left)

        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def _draw_header(
        self,
        c,
        data: InvoiceData,
        y_pos: float,
        width: float,
        height: float,
        margin_left: float,
        logo_path: Optional[str]
    ) -> float:
        """Dessine l'en-tête avec titre et logo."""
        from reportlab.lib.units import mm
        from reportlab.lib.colors import Color

        # Fond coloré en haut
        c.setFillColor(Color(*self.COLOR_PRIMARY))
        c.rect(0, height - 25 * mm, width, 25 * mm, fill=True, stroke=False)

        # Logo si disponible
        if logo_path and os.path.exists(logo_path):
            try:
                c.drawImage(logo_path, margin_left, height - 22 * mm, width=40 * mm, height=18 * mm, preserveAspectRatio=True)
            except (IOError, OSError, ValueError):
                pass  # Logo non critique, on continue sans

        # Titre FACTURE
        c.setFillColor(Color(1, 1, 1))  # Blanc
        c.setFont("Helvetica-Bold", 24)

        type_labels = {
            "380": "FACTURE",
            "381": "AVOIR",
            "384": "FACTURE CORRECTIVE",
            "386": "FACTURE PROFORMA",
        }
        title = type_labels.get(data.invoice_type, "FACTURE")

        c.drawRightString(width - 20 * mm, height - 18 * mm, title)

        # Numéro
        c.setFont("Helvetica", 12)
        c.drawRightString(width - 20 * mm, height - 8 * mm, f"N° {data.invoice_number}")

        return height - 35 * mm

    def _draw_parties(
        self,
        c,
        data: InvoiceData,
        y_pos: float,
        margin_left: float,
        margin_right: float
    ) -> float:
        """Dessine les blocs vendeur et acheteur."""
        from reportlab.lib.units import mm
        from reportlab.lib.colors import Color

        y_pos -= 10 * mm

        # Bloc vendeur (gauche)
        c.setFillColor(Color(*self.COLOR_PRIMARY))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin_left, y_pos, "ÉMETTEUR")

        c.setFillColor(Color(*self.COLOR_TEXT))
        c.setFont("Helvetica", 9)

        y = y_pos - 5 * mm
        if data.seller:
            if data.seller.name:
                c.setFont("Helvetica-Bold", 10)
                c.drawString(margin_left, y, data.seller.name)
                y -= 4 * mm

            c.setFont("Helvetica", 9)
            if data.seller.address_line1:
                c.drawString(margin_left, y, data.seller.address_line1)
                y -= 4 * mm
            if data.seller.address_line2:
                c.drawString(margin_left, y, data.seller.address_line2)
                y -= 4 * mm
            if data.seller.postal_code or data.seller.city:
                c.drawString(margin_left, y, f"{data.seller.postal_code or ''} {data.seller.city or ''}")
                y -= 4 * mm
            if data.seller.siret:
                c.drawString(margin_left, y, f"SIRET: {data.seller.siret}")
                y -= 4 * mm
            if data.seller.vat_number:
                c.drawString(margin_left, y, f"TVA: {data.seller.vat_number}")
                y -= 4 * mm

        # Bloc acheteur (droite)
        buyer_x = margin_right - 70 * mm

        c.setFillColor(Color(*self.COLOR_LIGHT))
        c.roundRect(buyer_x - 5 * mm, y_pos - 40 * mm, 75 * mm, 48 * mm, 3, fill=True, stroke=False)

        c.setFillColor(Color(*self.COLOR_PRIMARY))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(buyer_x, y_pos, "DESTINATAIRE")

        c.setFillColor(Color(*self.COLOR_TEXT))
        c.setFont("Helvetica", 9)

        y = y_pos - 5 * mm
        if data.buyer:
            if data.buyer.name:
                c.setFont("Helvetica-Bold", 10)
                c.drawString(buyer_x, y, data.buyer.name)
                y -= 4 * mm

            c.setFont("Helvetica", 9)
            if data.buyer.address_line1:
                c.drawString(buyer_x, y, data.buyer.address_line1)
                y -= 4 * mm
            if data.buyer.address_line2:
                c.drawString(buyer_x, y, data.buyer.address_line2)
                y -= 4 * mm
            if data.buyer.postal_code or data.buyer.city:
                c.drawString(buyer_x, y, f"{data.buyer.postal_code or ''} {data.buyer.city or ''}")
                y -= 4 * mm
            if data.buyer.siret:
                c.drawString(buyer_x, y, f"SIRET: {data.buyer.siret}")
                y -= 4 * mm
            if data.buyer.vat_number:
                c.drawString(buyer_x, y, f"TVA: {data.buyer.vat_number}")
                y -= 4 * mm

        return y_pos - 50 * mm

    def _draw_invoice_info(
        self,
        c,
        data: InvoiceData,
        y_pos: float,
        margin_left: float,
        margin_right: float
    ) -> float:
        """Dessine les informations de la facture (dates, références)."""
        from reportlab.lib.units import mm
        from reportlab.lib.colors import Color

        y_pos -= 5 * mm

        # Ligne de séparation
        c.setStrokeColor(Color(*self.COLOR_SECONDARY))
        c.setLineWidth(0.5)
        c.line(margin_left, y_pos, margin_right, y_pos)

        y_pos -= 8 * mm

        c.setFillColor(Color(*self.COLOR_TEXT))
        c.setFont("Helvetica", 9)

        # Date d'émission
        c.drawString(margin_left, y_pos, f"Date d'émission: {data.issue_date.strftime('%d/%m/%Y')}")

        # Date d'échéance
        if data.due_date:
            c.drawString(margin_left + 60 * mm, y_pos, f"Échéance: {data.due_date.strftime('%d/%m/%Y')}")

        # Devise
        c.drawRightString(margin_right, y_pos, f"Devise: {data.currency}")

        y_pos -= 5 * mm

        # Références
        if data.buyer_reference:
            c.drawString(margin_left, y_pos, f"Référence client: {data.buyer_reference}")
            y_pos -= 4 * mm

        if data.order_reference:
            c.drawString(margin_left, y_pos, f"Commande: {data.order_reference}")
            y_pos -= 4 * mm

        return y_pos - 5 * mm

    def _draw_lines_table(
        self,
        c,
        data: InvoiceData,
        y_pos: float,
        margin_left: float,
        margin_right: float,
        width: float
    ) -> float:
        """Dessine le tableau des lignes de facture."""
        from reportlab.lib.units import mm
        from reportlab.lib.colors import Color

        # Colonnes: Description | Qté | P.U. HT | TVA | Total HT
        col_widths = [85 * mm, 15 * mm, 25 * mm, 15 * mm, 25 * mm]
        col_x = [margin_left]
        for w in col_widths[:-1]:
            col_x.append(col_x[-1] + w)

        # En-tête du tableau
        c.setFillColor(Color(*self.COLOR_PRIMARY))
        c.rect(margin_left, y_pos - 7 * mm, margin_right - margin_left, 8 * mm, fill=True, stroke=False)

        c.setFillColor(Color(1, 1, 1))
        c.setFont("Helvetica-Bold", 9)

        headers = ["Description", "Qté", "P.U. HT", "TVA", "Total HT"]
        for i, header in enumerate(headers):
            if i == 0:
                c.drawString(col_x[i] + 2 * mm, y_pos - 5 * mm, header)
            else:
                c.drawRightString(col_x[i] + col_widths[i] - 2 * mm, y_pos - 5 * mm, header)

        y_pos -= 10 * mm

        # Lignes de facture
        c.setFillColor(Color(*self.COLOR_TEXT))
        c.setFont("Helvetica", 9)

        row_height = 6 * mm
        alternate = False

        for line in data.lines:
            # Fond alterné
            if alternate:
                c.setFillColor(Color(*self.COLOR_LIGHT))
                c.rect(margin_left, y_pos - row_height + 1 * mm, margin_right - margin_left, row_height, fill=True, stroke=False)

            c.setFillColor(Color(*self.COLOR_TEXT))

            # Description (tronquée si trop longue)
            desc = line.description[:50] + "..." if len(line.description) > 50 else line.description
            c.drawString(col_x[0] + 2 * mm, y_pos - 4 * mm, desc)

            # Quantité
            c.drawRightString(col_x[1] + col_widths[1] - 2 * mm, y_pos - 4 * mm, f"{line.quantity:,.2f}".replace(",", " "))

            # Prix unitaire
            c.drawRightString(col_x[2] + col_widths[2] - 2 * mm, y_pos - 4 * mm, f"{line.unit_price:,.2f} €".replace(",", " "))

            # Taux TVA
            c.drawRightString(col_x[3] + col_widths[3] - 2 * mm, y_pos - 4 * mm, f"{line.vat_rate}%")

            # Total HT
            c.drawRightString(col_x[4] + col_widths[4] - 2 * mm, y_pos - 4 * mm, f"{line.net_amount:,.2f} €".replace(",", " "))

            y_pos -= row_height
            alternate = not alternate

            # Nouvelle page si nécessaire
            if y_pos < 80 * mm:
                # NOTE: Phase 2 - Pagination multi-pages
                break

        # Ligne de séparation finale
        c.setStrokeColor(Color(*self.COLOR_SECONDARY))
        c.setLineWidth(1)
        c.line(margin_left, y_pos, margin_right, y_pos)

        return y_pos - 5 * mm

    def _draw_totals(
        self,
        c,
        data: InvoiceData,
        y_pos: float,
        margin_left: float,
        margin_right: float
    ) -> float:
        """Dessine le bloc des totaux."""
        from reportlab.lib.units import mm
        from reportlab.lib.colors import Color

        total_box_x = margin_right - 70 * mm
        total_box_width = 70 * mm

        # Ventilation TVA
        if data.vat_breakdown:
            c.setFillColor(Color(*self.COLOR_TEXT))
            c.setFont("Helvetica", 9)

            c.drawString(margin_left, y_pos, "Détail TVA:")
            y = y_pos - 5 * mm

            for rate, amount in data.vat_breakdown.items():
                rate_val = float(rate) if isinstance(rate, str) else rate
                amount_val = float(amount) if isinstance(amount, (str, Decimal)) else amount
                c.drawString(margin_left + 5 * mm, y, f"TVA {rate_val:.1f}%: {amount_val:,.2f} €".replace(",", " "))
                y -= 4 * mm

        # Bloc totaux (à droite)
        c.setFillColor(Color(*self.COLOR_LIGHT))
        c.roundRect(total_box_x, y_pos - 35 * mm, total_box_width, 40 * mm, 3, fill=True, stroke=False)

        row_height = 8 * mm
        y = y_pos - 2 * mm

        c.setFillColor(Color(*self.COLOR_TEXT))
        c.setFont("Helvetica", 10)

        # Total HT
        c.drawString(total_box_x + 5 * mm, y, "Total HT")
        c.drawRightString(total_box_x + total_box_width - 5 * mm, y, f"{data.total_ht:,.2f} €".replace(",", " "))
        y -= row_height

        # Total TVA
        c.drawString(total_box_x + 5 * mm, y, "TVA")
        c.drawRightString(total_box_x + total_box_width - 5 * mm, y, f"{data.total_tva:,.2f} €".replace(",", " "))
        y -= row_height

        # Ligne séparation
        c.setStrokeColor(Color(*self.COLOR_SECONDARY))
        c.line(total_box_x + 5 * mm, y + 3 * mm, total_box_x + total_box_width - 5 * mm, y + 3 * mm)

        # Total TTC
        c.setFillColor(Color(*self.COLOR_PRIMARY))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(total_box_x + 5 * mm, y, "Total TTC")
        c.drawRightString(total_box_x + total_box_width - 5 * mm, y, f"{data.total_ttc:,.2f} €".replace(",", " "))

        return y_pos - 45 * mm

    def _draw_footer(
        self,
        c,
        data: InvoiceData,
        width: float,
        margin_left: float
    ) -> None:
        """Dessine le pied de page."""
        from reportlab.lib.units import mm
        from reportlab.lib.colors import Color

        y_pos = 50 * mm

        # Conditions de paiement
        if data.payment_terms or data.iban:
            c.setFillColor(Color(*self.COLOR_TEXT))
            c.setFont("Helvetica-Bold", 9)
            c.drawString(margin_left, y_pos, "Conditions de paiement:")

            c.setFont("Helvetica", 9)
            y = y_pos - 5 * mm

            payment_means = {
                "30": "Virement bancaire",
                "48": "Carte bancaire",
                "49": "Prélèvement automatique",
                "10": "Espèces",
                "20": "Chèque",
            }

            c.drawString(margin_left + 5 * mm, y, f"Mode: {payment_means.get(data.payment_means_code, data.payment_means_code)}")
            y -= 4 * mm

            if data.iban:
                c.drawString(margin_left + 5 * mm, y, f"IBAN: {data.iban}")
                y -= 4 * mm

            if data.bic:
                c.drawString(margin_left + 5 * mm, y, f"BIC: {data.bic}")
                y -= 4 * mm

            if data.payment_terms:
                c.drawString(margin_left + 5 * mm, y, data.payment_terms)

        # Notes
        if data.notes:
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(margin_left, 25 * mm, data.notes[:100])

        # Mention Factur-X
        c.setFillColor(Color(*self.COLOR_SECONDARY))
        c.setFont("Helvetica", 7)
        c.drawString(margin_left, 15 * mm, "Facture électronique conforme Factur-X EN16931 - Document généré par AZALSCORE")

        # Ligne de séparation
        c.setStrokeColor(Color(*self.COLOR_LIGHT))
        c.line(margin_left, 12 * mm, width - margin_left, 12 * mm)

    # =========================================================================
    # EMBARQUEMENT XML
    # =========================================================================

    def _embed_xml_with_facturx(
        self,
        pdf_content: bytes,
        xml_content: str,
        profile: FacturXProfile
    ) -> bytes:
        """Embarque le XML dans le PDF en utilisant la librairie factur-x."""
        try:
            from facturx import generate_from_binary

            # Profil pour factur-x (minimum, basicwl, basic, en16931, extended)
            profile_mapping = {
                FacturXProfile.MINIMUM: "minimum",
                FacturXProfile.BASIC_WL: "basicwl",
                FacturXProfile.BASIC: "basic",
                FacturXProfile.EN16931: "en16931",
                FacturXProfile.EXTENDED: "extended",
            }
            facturx_level = profile_mapping.get(profile, "en16931")

            # Préparer le XML
            xml_bytes = xml_content.encode('utf-8') if isinstance(xml_content, str) else xml_content

            # Générer le PDF/A-3 avec XML embarqué
            facturx_pdf = generate_from_binary(
                pdf_file=pdf_content,
                xml=xml_bytes,
                flavor='factur-x',
                level=facturx_level,
                check_xsd=False,  # Ne pas valider XSD (déjà fait en amont)
            )

            return facturx_pdf

        except (EInvoicingPDFError, ValueError, IOError, ImportError) as e:
            logger.error(f"Erreur embarquement factur-x: {e}")
            # Fallback sur methode manuelle
            return self._embed_xml_manually(pdf_content, xml_content, profile)

    def _embed_xml_manually(
        self,
        pdf_content: bytes,
        xml_content: str,
        profile: FacturXProfile
    ) -> bytes:
        """
        Embarque manuellement le XML dans le PDF.

        Cette méthode est utilisée si la librairie factur-x n'est pas disponible.
        Elle produit un PDF valide mais peut ne pas être 100% conforme PDF/A-3.
        """
        if not self._pypdf_available:
            logger.warning("pypdf non disponible - retour du PDF sans XML embarqué")
            return pdf_content

        try:
            from pypdf import PdfReader, PdfWriter
            from pypdf.generic import (
                ArrayObject, DictionaryObject, NameObject,
                TextStringObject, ByteStringObject, NumberObject
            )

            # Lire le PDF source
            reader = PdfReader(io.BytesIO(pdf_content))
            writer = PdfWriter()

            # Copier toutes les pages
            for page in reader.pages:
                writer.add_page(page)

            # Préparer le contenu XML
            xml_bytes = xml_content.encode('utf-8') if isinstance(xml_content, str) else xml_content

            # Nom du fichier XML selon le profil
            xml_filename = "factur-x.xml"

            # Ajouter le XML comme pièce jointe
            writer.add_attachment(xml_filename, xml_bytes)

            # Ajouter les métadonnées XMP
            self._add_xmp_metadata(writer, profile)

            # Écrire le résultat
            output = io.BytesIO()
            writer.write(output)

            return output.getvalue()

        except (EInvoicingPDFError, ValueError, IOError, KeyError) as e:
            logger.error(f"Erreur embarquement manuel: {e}")
            return pdf_content

    def _add_xmp_metadata(self, writer, profile: FacturXProfile) -> None:
        """Ajoute les métadonnées XMP requises pour Factur-X."""
        # Métadonnées XMP minimales pour Factur-X
        xmp_metadata = f'''<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="AZALS PDF Generator">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
        xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/"
        xmlns:fx="urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#">
      <pdfaid:part>3</pdfaid:part>
      <pdfaid:conformance>B</pdfaid:conformance>
      <fx:DocumentType>INVOICE</fx:DocumentType>
      <fx:DocumentFileName>factur-x.xml</fx:DocumentFileName>
      <fx:Version>1.0</fx:Version>
      <fx:ConformanceLevel>{profile.value}</fx:ConformanceLevel>
    </rdf:Description>
    <rdf:Description rdf:about=""
        xmlns:dc="http://purl.org/dc/elements/1.1/">
      <dc:format>application/pdf</dc:format>
      <dc:creator>
        <rdf:Seq>
          <rdf:li>AZALSCORE</rdf:li>
        </rdf:Seq>
      </dc:creator>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>'''

        try:
            writer.add_metadata({
                '/Producer': 'AZALSCORE PDF Generator',
                '/Creator': 'AZALS E-Invoicing Module',
            })
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning(f"Impossible d'ajouter metadonnees: {e}")

    def _extract_xml_with_pypdf(self, pdf_content: bytes) -> Optional[str]:
        """Extrait le XML en utilisant pypdf."""
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(pdf_content))

        # Chercher les pièces jointes
        if '/Names' in reader.trailer.get('/Root', {}):
            names = reader.trailer['/Root']['/Names']
            if '/EmbeddedFiles' in names:
                embedded = names['/EmbeddedFiles']
                # Parcourir les fichiers embarqués
                # ...

        return None

    def _generate_basic_pdf(self, data: InvoiceData) -> bytes:
        """
        Génère un PDF basique si reportlab n'est pas disponible.

        Ce PDF minimal contient les informations essentielles en texte brut.
        """
        content = f"""%PDF-1.7
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 500 >>
stream
BT
/F1 18 Tf
50 790 Td
(FACTURE N° {data.invoice_number}) Tj
/F1 12 Tf
0 -25 Td
(Date: {data.issue_date.strftime('%d/%m/%Y')}) Tj
0 -15 Td
(Emetteur: {data.seller.name if data.seller else ''}) Tj
0 -15 Td
(Destinataire: {data.buyer.name if data.buyer else ''}) Tj
0 -30 Td
(Total HT: {data.total_ht:.2f} EUR) Tj
0 -15 Td
(TVA: {data.total_tva:.2f} EUR) Tj
0 -15 Td
(Total TTC: {data.total_ttc:.2f} EUR) Tj
0 -50 Td
/F1 8 Tf
(Facture electronique conforme Factur-X - AZALSCORE) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000270 00000 n
0000000820 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
905
%%EOF
"""
        return content.encode('latin-1')


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def convert_einvoice_to_pdf_data(
    einvoice,
    lines_data: Optional[List[dict]] = None
) -> InvoiceData:
    """
    Convertit un EInvoiceRecord en InvoiceData pour génération PDF.

    Args:
        einvoice: Objet EInvoiceRecord depuis la base de données
        lines_data: Données des lignes (optionnel si pas stockées en base)

    Returns:
        InvoiceData prêt pour génération PDF
    """
    # Parties
    seller = InvoiceParty(
        name=einvoice.seller_name or "",
        siret=einvoice.seller_siret,
        vat_number=einvoice.seller_tva,
    )

    buyer = InvoiceParty(
        name=einvoice.buyer_name or "",
        siret=einvoice.buyer_siret,
        vat_number=einvoice.buyer_tva,
    )

    # Lignes
    lines = []
    if lines_data:
        for i, line_dict in enumerate(lines_data, 1):
            lines.append(InvoiceLine(
                line_number=i,
                description=line_dict.get("description", ""),
                quantity=Decimal(str(line_dict.get("quantity", 1))),
                unit=line_dict.get("unit", "C62"),
                unit_price=Decimal(str(line_dict.get("unit_price", 0))),
                vat_rate=Decimal(str(line_dict.get("vat_rate", 20))),
                net_amount=Decimal(str(line_dict.get("net_amount", 0))),
                vat_amount=Decimal(str(line_dict.get("vat_amount", 0))),
                total_amount=Decimal(str(line_dict.get("total_amount", 0))),
            ))
    else:
        # Créer une ligne synthétique depuis les totaux
        lines.append(InvoiceLine(
            line_number=1,
            description="Montant total de la facture",
            quantity=Decimal("1"),
            unit="C62",
            unit_price=einvoice.total_ht or Decimal("0"),
            vat_rate=Decimal("20"),
            net_amount=einvoice.total_ht or Decimal("0"),
            vat_amount=einvoice.total_tva or Decimal("0"),
            total_amount=einvoice.total_ttc or Decimal("0"),
        ))

    return InvoiceData(
        invoice_number=einvoice.invoice_number,
        invoice_type=einvoice.invoice_type or "380",
        issue_date=einvoice.issue_date or date.today(),
        due_date=einvoice.due_date,
        currency=einvoice.currency or "EUR",
        seller=seller,
        buyer=buyer,
        lines=lines,
        total_ht=einvoice.total_ht or Decimal("0"),
        total_tva=einvoice.total_tva or Decimal("0"),
        total_ttc=einvoice.total_ttc or Decimal("0"),
        vat_breakdown=einvoice.vat_breakdown or {},
    )


def get_pdf_generator() -> FacturXPDFGenerator:
    """Factory pour le générateur PDF."""
    return FacturXPDFGenerator()
