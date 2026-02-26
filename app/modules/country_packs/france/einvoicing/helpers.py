"""
AZALSCORE - E-Invoicing Helpers
Fonctions utilitaires pour la facturation électronique
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, TYPE_CHECKING

from app.modules.country_packs.france.einvoicing_schemas import EInvoiceParty

if TYPE_CHECKING:
    from app.modules.commercial.models import Customer, DocumentLine
    from app.modules.country_packs.france.einvoicing_models import TenantPDPConfig
    from app.modules.purchases.models import PurchaseSupplier


def build_seller_from_tenant(pdp_config: "TenantPDPConfig | None") -> EInvoiceParty:
    """
    Construit les infos vendeur depuis config tenant.

    Args:
        pdp_config: Configuration PDP du tenant

    Returns:
        EInvoiceParty avec les données vendeur
    """
    return EInvoiceParty(
        name=pdp_config.name if pdp_config else "Entreprise",
        siret=pdp_config.siret if pdp_config else None,
        siren=pdp_config.siren if pdp_config else None,
        vat_number=pdp_config.tva_number if pdp_config else None,
        country_code="FR"
    )


def build_buyer_from_customer(customer: "Customer") -> EInvoiceParty:
    """
    Construit les infos acheteur depuis Customer.

    Args:
        customer: Client commercial

    Returns:
        EInvoiceParty avec les données acheteur
    """
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


def build_seller_from_supplier(supplier: "PurchaseSupplier") -> EInvoiceParty:
    """
    Construit les infos vendeur depuis Supplier.

    Args:
        supplier: Fournisseur

    Returns:
        EInvoiceParty avec les données vendeur
    """
    return EInvoiceParty(
        name=supplier.name,
        siret=supplier.tax_id,
        vat_number=supplier.tax_id,
        address_line1=supplier.address,
        city=supplier.city,
        postal_code=supplier.postal_code,
        country_code=supplier.country or "FR",
        email=supplier.email,
        phone=supplier.phone
    )


def calculate_vat_breakdown(lines: list["DocumentLine"]) -> dict[str, float]:
    """
    Calcule la ventilation TVA depuis DocumentLine.

    Args:
        lines: Lignes de document

    Returns:
        Dictionnaire {taux: montant_tva}
    """
    breakdown: dict[str, Decimal] = {}
    for line in lines:
        rate = line.tax_rate or 20.0
        rate_key = f"{rate:.2f}"
        breakdown[rate_key] = breakdown.get(rate_key, Decimal("0")) + (line.tax_amount or Decimal("0"))
    return {k: float(v) for k, v in breakdown.items()}


def calculate_vat_breakdown_purchase(lines) -> dict[str, float]:
    """
    Calcule la ventilation TVA depuis PurchaseInvoiceLine.

    Args:
        lines: Lignes de facture d'achat

    Returns:
        Dictionnaire {taux: montant_tva}
    """
    breakdown: dict[str, Decimal] = {}
    for line in lines:
        rate = line.tax_rate or Decimal("20")
        rate_key = f"{rate:.2f}"
        breakdown[rate_key] = breakdown.get(rate_key, Decimal("0")) + (line.tax_amount or Decimal("0"))
    return {k: float(v) for k, v in breakdown.items()}


def build_invoice_data(
    doc,
    seller: EInvoiceParty,
    buyer: EInvoiceParty,
    vat_breakdown: dict[str, float],
    format_value: str
) -> dict[str, Any]:
    """
    Construit les données pour génération XML.

    Args:
        doc: CommercialDocument
        seller: Partie vendeur
        buyer: Partie acheteur
        vat_breakdown: Ventilation TVA
        format_value: Format de facture

    Returns:
        Dictionnaire de données pour le générateur
    """
    from app.modules.commercial.models import DocumentType

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
        "profile": format_value,
        "seller": seller.model_dump(),
        "buyer": buyer.model_dump(),
        "lines": lines_data,
        "total_ht": float(doc.subtotal or 0),
        "total_tva": float(doc.tax_amount or 0),
        "total_ttc": float(doc.total or 0),
        "vat_breakdown": vat_breakdown
    }
