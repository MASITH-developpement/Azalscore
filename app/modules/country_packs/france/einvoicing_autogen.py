"""
AZALS - Auto-génération Intelligente E-Invoicing
=================================================

Service d'auto-complétion et de génération automatique pour la facturation
électronique. Minimise l'intervention humaine en proposant des valeurs
calculées et des textes suggérés.

Fonctionnalités:
- Auto-détection du format de facture approprié
- Proposition de textes standards
- Calcul automatique des totaux et TVA
- Détection du PDP approprié selon le destinataire
- Validation automatique avant soumission
- Suggestions basées sur l'historique
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TypedDict
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# TYPES ET STRUCTURES
# =============================================================================

class AutogenConfidence(str, Enum):
    """Niveau de confiance de la suggestion."""
    HIGH = "HIGH"          # >90% - peut être validé automatiquement
    MEDIUM = "MEDIUM"      # 70-90% - proposition forte
    LOW = "LOW"            # <70% - suggestion à vérifier
    MANUAL = "MANUAL"      # Intervention manuelle requise


class DocumentContext(str, Enum):
    """Contexte du document pour adapter les propositions."""
    B2B_DOMESTIC = "B2B_DOMESTIC"      # B2B France
    B2B_INTRA_EU = "B2B_INTRA_EU"      # B2B intra-communautaire
    B2B_EXPORT = "B2B_EXPORT"          # B2B export hors UE
    B2G = "B2G"                        # Business to Government
    B2C = "B2C"                        # Business to Consumer


class VATCategory(str, Enum):
    """Catégorie TVA pour auto-détection."""
    STANDARD = "S"      # Taux standard (20%)
    REDUCED = "AA"      # Taux réduit (5.5%, 10%)
    SUPER_REDUCED = "K" # Taux super-réduit (2.1%)
    ZERO = "Z"          # Taux zéro (0%)
    EXEMPT = "E"        # Exonéré
    REVERSE_CHARGE = "AE"  # Autoliquidation


@dataclass
class AutogenSuggestion:
    """Suggestion auto-générée."""
    field_name: str
    suggested_value: Any
    confidence: AutogenConfidence
    reason: str
    alternatives: List[Any] = field(default_factory=list)
    source: str = "SYSTEM"


@dataclass
class AutogenResult:
    """Résultat de l'auto-génération."""
    suggestions: List[AutogenSuggestion]
    auto_filled: Dict[str, Any]
    warnings: List[str]
    requires_validation: List[str]
    ready_for_submission: bool
    confidence_score: float  # 0-100


class PartyInfo(TypedDict, total=False):
    """Informations sur une partie (vendeur/acheteur)."""
    name: str
    siret: str
    siren: str
    vat_number: str
    address_line1: str
    address_line2: str
    city: str
    postal_code: str
    country_code: str
    routing_id: str
    email: str
    phone: str


class LineItemInfo(TypedDict, total=False):
    """Informations sur une ligne de facture."""
    description: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    discount_percent: Decimal
    vat_rate: Decimal
    vat_category: str
    item_code: str


# =============================================================================
# TEMPLATES DE TEXTES
# =============================================================================

class TextTemplates:
    """Templates de textes standards pour les factures."""

    # Templates de mentions légales
    PAYMENT_TERMS: Dict[str, str] = {
        "NET_30": "Paiement à 30 jours date de facture",
        "NET_45": "Paiement à 45 jours fin de mois",
        "NET_60": "Paiement à 60 jours date de facture",
        "IMMEDIATE": "Paiement comptant",
        "END_OF_MONTH": "Paiement fin de mois",
    }

    LATE_PAYMENT: str = (
        "En cas de retard de paiement, une indemnité forfaitaire de 40€ pour frais de "
        "recouvrement sera due de plein droit, ainsi que des pénalités de retard au taux "
        "de {rate}% (taux BCE majoré de 10 points)."
    )

    VAT_EXEMPTION: Dict[str, str] = {
        "INTRA_EU": "TVA non applicable - Art. 262 ter I du CGI",
        "EXPORT": "Exonération de TVA - Art. 262-I du CGI",
        "REVERSE_CHARGE": "Autoliquidation de TVA par le preneur - Art. 283-2 du CGI",
        "FRANCHISE": "TVA non applicable - Art. 293 B du CGI (franchise en base)",
    }

    DELIVERY_TERMS: Dict[str, str] = {
        "EXW": "Départ usine (EXW)",
        "FCA": "Franco transporteur (FCA)",
        "DAP": "Rendu lieu de destination (DAP)",
        "DDP": "Rendu droits acquittés (DDP)",
    }

    # Templates de descriptions courantes
    SERVICE_DESCRIPTIONS: Dict[str, str] = {
        "consulting": "Prestation de conseil et accompagnement",
        "development": "Développement et maintenance informatique",
        "training": "Formation professionnelle",
        "support": "Support technique et assistance",
        "audit": "Audit et diagnostic",
        "maintenance": "Contrat de maintenance",
        "hosting": "Hébergement et infogérance",
        "license": "Licence d'utilisation logiciel",
    }

    @classmethod
    def get_payment_terms_text(cls, terms_code: str) -> str:
        """Retourne le texte des conditions de paiement."""
        return cls.PAYMENT_TERMS.get(terms_code, f"Paiement selon conditions convenues ({terms_code})")

    @classmethod
    def get_late_payment_text(cls, rate: float = 15.86) -> str:
        """Retourne le texte des pénalités de retard."""
        return cls.LATE_PAYMENT.format(rate=rate)

    @classmethod
    def get_vat_exemption_text(cls, exemption_type: str) -> str:
        """Retourne le texte d'exonération TVA."""
        return cls.VAT_EXEMPTION.get(exemption_type, "")


# =============================================================================
# SERVICE D'AUTO-GÉNÉRATION
# =============================================================================

class EInvoiceAutogenService:
    """
    Service d'auto-génération pour la facturation électronique.

    Propose des valeurs et textes automatiquement en fonction du contexte,
    minimisant l'intervention humaine.
    """

    # Taux de TVA France 2026
    VAT_RATES_FR: Dict[str, Decimal] = {
        "standard": Decimal("20.00"),
        "intermediate": Decimal("10.00"),
        "reduced": Decimal("5.50"),
        "super_reduced": Decimal("2.10"),
        "zero": Decimal("0.00"),
    }

    # Mapping codes pays UE
    EU_COUNTRIES: set = {
        "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
        "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
        "NL", "PL", "PT", "RO", "SE", "SI", "SK"
    }

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id: str = tenant_id
        self._history_cache: Dict[str, Any] = {}

    # =========================================================================
    # DÉTECTION AUTOMATIQUE DU CONTEXTE
    # =========================================================================

    def detect_document_context(
        self,
        seller_country: str,
        buyer_country: str,
        buyer_siret: Optional[str] = None,
        buyer_vat: Optional[str] = None,
        is_public_entity: bool = False
    ) -> Tuple[DocumentContext, AutogenConfidence]:
        """
        Détecte automatiquement le contexte du document.

        Returns:
            Tuple[DocumentContext, AutogenConfidence]: Contexte et niveau de confiance
        """
        seller_country = seller_country.upper() if seller_country else "FR"
        buyer_country = buyer_country.upper() if buyer_country else "FR"

        # B2G: Entité publique
        if is_public_entity or (buyer_siret and buyer_siret.startswith("1")):
            return DocumentContext.B2G, AutogenConfidence.HIGH

        # Même pays (France)
        if seller_country == "FR" and buyer_country == "FR":
            if buyer_siret or buyer_vat:
                return DocumentContext.B2B_DOMESTIC, AutogenConfidence.HIGH
            else:
                return DocumentContext.B2C, AutogenConfidence.MEDIUM

        # Intra-UE
        if buyer_country in self.EU_COUNTRIES:
            if buyer_vat and self._validate_eu_vat_format(buyer_vat):
                return DocumentContext.B2B_INTRA_EU, AutogenConfidence.HIGH
            else:
                return DocumentContext.B2B_INTRA_EU, AutogenConfidence.MEDIUM

        # Export hors UE
        return DocumentContext.B2B_EXPORT, AutogenConfidence.HIGH

    def detect_vat_category(
        self,
        context: DocumentContext,
        product_type: Optional[str] = None,
        buyer_vat_valid: bool = True
    ) -> Tuple[VATCategory, Decimal, AutogenConfidence]:
        """
        Détecte automatiquement la catégorie TVA et le taux applicable.

        Returns:
            Tuple[VATCategory, Decimal, AutogenConfidence]: Catégorie, taux, confiance
        """
        # Intra-UE avec TVA valide → Exonération
        if context == DocumentContext.B2B_INTRA_EU and buyer_vat_valid:
            return VATCategory.EXEMPT, Decimal("0"), AutogenConfidence.HIGH

        # Export → Exonération
        if context == DocumentContext.B2B_EXPORT:
            return VATCategory.EXEMPT, Decimal("0"), AutogenConfidence.HIGH

        # B2G ou B2B France → Taux standard par défaut
        if context in (DocumentContext.B2G, DocumentContext.B2B_DOMESTIC):
            # Détection du taux selon le type de produit
            rate = self._detect_vat_rate_by_product(product_type)
            category = VATCategory.STANDARD if rate == Decimal("20") else VATCategory.REDUCED
            return category, rate, AutogenConfidence.MEDIUM

        # B2C → Taux standard
        return VATCategory.STANDARD, Decimal("20"), AutogenConfidence.MEDIUM

    def _detect_vat_rate_by_product(self, product_type: Optional[str]) -> Decimal:
        """Détecte le taux de TVA selon le type de produit."""
        if not product_type:
            return self.VAT_RATES_FR["standard"]

        product_lower = product_type.lower()

        # Taux super réduit (2.1%)
        super_reduced_keywords = ["médicament", "presse", "spectacle"]
        if any(kw in product_lower for kw in super_reduced_keywords):
            return self.VAT_RATES_FR["super_reduced"]

        # Taux réduit (5.5%)
        reduced_keywords = [
            "alimentaire", "nourriture", "livre", "energie", "gaz",
            "électricité", "chauffage", "travaux", "rénovation"
        ]
        if any(kw in product_lower for kw in reduced_keywords):
            return self.VAT_RATES_FR["reduced"]

        # Taux intermédiaire (10%)
        intermediate_keywords = [
            "transport", "hôtel", "hébergement", "restaurant",
            "médicament non remboursé", "bois"
        ]
        if any(kw in product_lower for kw in intermediate_keywords):
            return self.VAT_RATES_FR["intermediate"]

        return self.VAT_RATES_FR["standard"]

    # =========================================================================
    # AUTO-COMPLÉTION DES CHAMPS
    # =========================================================================

    def auto_complete_invoice(
        self,
        partial_data: Dict[str, Any],
        seller: PartyInfo,
        buyer: PartyInfo,
        lines: List[LineItemInfo]
    ) -> AutogenResult:
        """
        Auto-complète une facture avec toutes les valeurs manquantes.

        Args:
            partial_data: Données partiellement remplies
            seller: Informations vendeur
            buyer: Informations acheteur
            lines: Lignes de facture

        Returns:
            AutogenResult: Résultat avec suggestions et champs auto-remplis
        """
        suggestions: List[AutogenSuggestion] = []
        auto_filled: Dict[str, Any] = {}
        warnings: List[str] = []
        requires_validation: List[str] = []

        # 1. Détecter le contexte
        context, ctx_confidence = self.detect_document_context(
            seller.get("country_code", "FR"),
            buyer.get("country_code", "FR"),
            buyer.get("siret"),
            buyer.get("vat_number"),
            self._is_public_entity(buyer)
        )
        auto_filled["document_context"] = context.value

        # 2. Suggérer le format de facture
        format_suggestion = self._suggest_invoice_format(context, buyer)
        suggestions.append(format_suggestion)
        if format_suggestion.confidence == AutogenConfidence.HIGH:
            auto_filled["format"] = format_suggestion.suggested_value

        # 3. Auto-compléter les dates
        if "issue_date" not in partial_data:
            auto_filled["issue_date"] = date.today()
            suggestions.append(AutogenSuggestion(
                field_name="issue_date",
                suggested_value=date.today(),
                confidence=AutogenConfidence.HIGH,
                reason="Date du jour par défaut"
            ))

        if "due_date" not in partial_data:
            due_date = self._calculate_due_date(
                partial_data.get("issue_date", date.today()),
                partial_data.get("payment_terms", "NET_30")
            )
            auto_filled["due_date"] = due_date
            suggestions.append(AutogenSuggestion(
                field_name="due_date",
                suggested_value=due_date,
                confidence=AutogenConfidence.HIGH,
                reason=f"Calculée selon conditions de paiement"
            ))

        # 4. Auto-compléter les lignes
        completed_lines = []
        for i, line in enumerate(lines):
            completed_line, line_suggestions = self._auto_complete_line(
                line, context, i + 1
            )
            completed_lines.append(completed_line)
            suggestions.extend(line_suggestions)

        auto_filled["lines"] = completed_lines

        # 5. Calculer les totaux
        totals = self._calculate_totals(completed_lines)
        auto_filled.update(totals)

        # 6. Générer les mentions légales
        legal_mentions = self._generate_legal_mentions(
            context,
            partial_data.get("payment_terms", "NET_30"),
            totals.get("vat_breakdown", {})
        )
        auto_filled["legal_mentions"] = legal_mentions
        suggestions.append(AutogenSuggestion(
            field_name="legal_mentions",
            suggested_value=legal_mentions,
            confidence=AutogenConfidence.HIGH,
            reason="Mentions légales obligatoires générées automatiquement"
        ))

        # 7. Suggérer le PDP approprié
        pdp_suggestion = self._suggest_pdp(context, buyer)
        suggestions.append(pdp_suggestion)
        if pdp_suggestion.confidence == AutogenConfidence.HIGH:
            auto_filled["suggested_pdp"] = pdp_suggestion.suggested_value

        # 8. Valider la complétude
        missing_fields = self._check_completeness(auto_filled, context)
        if missing_fields:
            requires_validation.extend(missing_fields)
            warnings.append(f"Champs manquants: {', '.join(missing_fields)}")

        # 9. Calculer le score de confiance global
        confidence_score = self._calculate_confidence_score(suggestions)
        ready_for_submission = (
            confidence_score >= 80 and
            len(requires_validation) == 0 and
            len(warnings) == 0
        )

        return AutogenResult(
            suggestions=suggestions,
            auto_filled=auto_filled,
            warnings=warnings,
            requires_validation=requires_validation,
            ready_for_submission=ready_for_submission,
            confidence_score=confidence_score
        )

    def _auto_complete_line(
        self,
        line: LineItemInfo,
        context: DocumentContext,
        line_number: int
    ) -> Tuple[Dict[str, Any], List[AutogenSuggestion]]:
        """Auto-complète une ligne de facture."""
        suggestions: List[AutogenSuggestion] = []
        completed: Dict[str, Any] = dict(line)
        completed["line_number"] = line_number

        # Quantité par défaut
        if "quantity" not in line or line["quantity"] is None:
            completed["quantity"] = Decimal("1")
            suggestions.append(AutogenSuggestion(
                field_name=f"lines[{line_number}].quantity",
                suggested_value=Decimal("1"),
                confidence=AutogenConfidence.HIGH,
                reason="Quantité 1 par défaut"
            ))

        # Unité par défaut
        if "unit" not in line or not line["unit"]:
            completed["unit"] = "C62"  # Unité (UN/ECE)
            suggestions.append(AutogenSuggestion(
                field_name=f"lines[{line_number}].unit",
                suggested_value="C62",
                confidence=AutogenConfidence.MEDIUM,
                reason="Unité standard (pièce)",
                alternatives=["HUR", "DAY", "MON", "KGM", "MTR"]
            ))

        # Taux TVA
        if "vat_rate" not in line or line["vat_rate"] is None:
            vat_cat, vat_rate, confidence = self.detect_vat_category(
                context, line.get("description")
            )
            completed["vat_rate"] = vat_rate
            completed["vat_category"] = vat_cat.value
            suggestions.append(AutogenSuggestion(
                field_name=f"lines[{line_number}].vat_rate",
                suggested_value=vat_rate,
                confidence=confidence,
                reason=f"Taux TVA {vat_rate}% ({vat_cat.value})"
            ))

        # Remise par défaut
        if "discount_percent" not in line:
            completed["discount_percent"] = Decimal("0")

        # Calculer les sous-totaux (convertir en Decimal pour calculs précis)
        qty = Decimal(str(completed.get("quantity", 1)))
        price = Decimal(str(completed.get("unit_price", 0)))
        discount = Decimal(str(completed.get("discount_percent", 0)))
        vat_rate = Decimal(str(completed.get("vat_rate", 20)))

        subtotal_ht = qty * price * (Decimal("1") - discount / Decimal("100"))
        vat_amount = subtotal_ht * vat_rate / Decimal("100")
        total_ttc = subtotal_ht + vat_amount

        completed["subtotal_ht"] = subtotal_ht.quantize(Decimal("0.01"), ROUND_HALF_UP)
        completed["vat_amount"] = vat_amount.quantize(Decimal("0.01"), ROUND_HALF_UP)
        completed["total_ttc"] = total_ttc.quantize(Decimal("0.01"), ROUND_HALF_UP)

        return completed, suggestions

    def _calculate_totals(self, lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule tous les totaux de la facture."""
        total_ht = Decimal("0")
        total_vat = Decimal("0")
        vat_breakdown: Dict[str, Dict[str, Decimal]] = {}

        for line in lines:
            line_ht = line.get("subtotal_ht", Decimal("0"))
            line_vat = line.get("vat_amount", Decimal("0"))
            vat_rate = str(line.get("vat_rate", "20.00"))

            total_ht += line_ht
            total_vat += line_vat

            if vat_rate not in vat_breakdown:
                vat_breakdown[vat_rate] = {"base": Decimal("0"), "amount": Decimal("0")}
            vat_breakdown[vat_rate]["base"] += line_ht
            vat_breakdown[vat_rate]["amount"] += line_vat

        total_ttc = total_ht + total_vat

        return {
            "total_ht": total_ht.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "total_vat": total_vat.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "total_ttc": total_ttc.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "vat_breakdown": {
                rate: {
                    "base": data["base"].quantize(Decimal("0.01"), ROUND_HALF_UP),
                    "amount": data["amount"].quantize(Decimal("0.01"), ROUND_HALF_UP)
                }
                for rate, data in vat_breakdown.items()
            }
        }

    # =========================================================================
    # SUGGESTIONS DE TEXTE
    # =========================================================================

    def suggest_line_description(
        self,
        service_type: str,
        context: Optional[str] = None,
        client_history: Optional[List[str]] = None
    ) -> AutogenSuggestion:
        """
        Suggère une description pour une ligne de facture.

        Args:
            service_type: Type de service/produit
            context: Contexte additionnel
            client_history: Historique des descriptions utilisées

        Returns:
            AutogenSuggestion: Suggestion avec alternatives
        """
        # Template de base
        base_description = TextTemplates.SERVICE_DESCRIPTIONS.get(
            service_type.lower(),
            f"Prestation {service_type}"
        )

        # Enrichir avec le contexte
        if context:
            base_description = f"{base_description} - {context}"

        # Alternatives basées sur l'historique
        alternatives = []
        if client_history:
            alternatives = client_history[:3]

        # Suggestions génériques supplémentaires
        generic_alternatives = [
            f"{base_description} (forfait)",
            f"{base_description} - Période {date.today().strftime('%m/%Y')}",
            f"{base_description} selon devis",
        ]
        alternatives.extend([a for a in generic_alternatives if a not in alternatives])

        return AutogenSuggestion(
            field_name="description",
            suggested_value=base_description,
            confidence=AutogenConfidence.MEDIUM,
            reason="Description suggérée selon le type de service",
            alternatives=alternatives[:5]
        )

    def suggest_payment_reference(
        self,
        invoice_number: str,
        buyer_code: Optional[str] = None
    ) -> AutogenSuggestion:
        """Suggère une référence de paiement structurée."""
        # Format: INV-NUMERO-YYYYMM
        ref = f"INV-{invoice_number}-{date.today().strftime('%Y%m')}"

        if buyer_code:
            ref = f"{buyer_code}-{ref}"

        return AutogenSuggestion(
            field_name="payment_reference",
            suggested_value=ref,
            confidence=AutogenConfidence.HIGH,
            reason="Référence structurée pour suivi paiement"
        )

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _suggest_invoice_format(
        self,
        context: DocumentContext,
        buyer: PartyInfo
    ) -> AutogenSuggestion:
        """Suggère le format de facture approprié."""
        if context == DocumentContext.B2G:
            # Chorus Pro → UBL obligatoire
            return AutogenSuggestion(
                field_name="format",
                suggested_value="UBL_21",
                confidence=AutogenConfidence.HIGH,
                reason="Format UBL requis pour Chorus Pro (B2G)",
                alternatives=["FACTURX_EN16931"]
            )

        if context == DocumentContext.B2B_INTRA_EU:
            return AutogenSuggestion(
                field_name="format",
                suggested_value="FACTURX_EN16931",
                confidence=AutogenConfidence.HIGH,
                reason="Factur-X EN16931 pour échanges intra-UE"
            )

        # B2B France par défaut
        return AutogenSuggestion(
            field_name="format",
            suggested_value="FACTURX_EN16931",
            confidence=AutogenConfidence.HIGH,
            reason="Factur-X EN16931 - profil standard conforme",
            alternatives=["FACTURX_BASIC", "FACTURX_EXTENDED"]
        )

    def _suggest_pdp(
        self,
        context: DocumentContext,
        buyer: PartyInfo
    ) -> AutogenSuggestion:
        """Suggère le PDP approprié selon le destinataire."""
        if context == DocumentContext.B2G:
            return AutogenSuggestion(
                field_name="pdp_provider",
                suggested_value="CHORUS_PRO",
                confidence=AutogenConfidence.HIGH,
                reason="Chorus Pro obligatoire pour le secteur public"
            )

        # Vérifier si le destinataire a un PDP préféré (routing_id)
        routing_id = buyer.get("routing_id", "")
        if routing_id:
            # Détecter le PDP depuis le routing_id
            if "yooz" in routing_id.lower():
                return AutogenSuggestion(
                    field_name="pdp_provider",
                    suggested_value="YOOZ",
                    confidence=AutogenConfidence.HIGH,
                    reason="PDP Yooz détecté via routing_id"
                )

        # Par défaut → PPF
        return AutogenSuggestion(
            field_name="pdp_provider",
            suggested_value="PPF",
            confidence=AutogenConfidence.MEDIUM,
            reason="Portail Public de Facturation par défaut",
            alternatives=["YOOZ", "DOCAPOSTE", "SAGE"]
        )

    def _calculate_due_date(
        self,
        issue_date: date,
        payment_terms: str
    ) -> date:
        """Calcule la date d'échéance selon les conditions de paiement."""
        terms_days = {
            "IMMEDIATE": 0,
            "NET_15": 15,
            "NET_30": 30,
            "NET_45": 45,
            "NET_60": 60,
            "NET_90": 90,
        }

        days = terms_days.get(payment_terms, 30)

        if payment_terms == "END_OF_MONTH":
            # Fin du mois suivant
            next_month = issue_date.replace(day=28) + timedelta(days=4)
            return next_month.replace(day=1) - timedelta(days=1)

        return issue_date + timedelta(days=days)

    def _generate_legal_mentions(
        self,
        context: DocumentContext,
        payment_terms: str,
        vat_breakdown: Dict[str, Any]
    ) -> Dict[str, str]:
        """Génère les mentions légales obligatoires."""
        mentions: Dict[str, str] = {}

        # Conditions de paiement
        mentions["payment_terms"] = TextTemplates.get_payment_terms_text(payment_terms)

        # Pénalités de retard
        mentions["late_payment"] = TextTemplates.get_late_payment_text()

        # Mentions TVA
        if context == DocumentContext.B2B_INTRA_EU:
            mentions["vat_exemption"] = TextTemplates.get_vat_exemption_text("INTRA_EU")
        elif context == DocumentContext.B2B_EXPORT:
            mentions["vat_exemption"] = TextTemplates.get_vat_exemption_text("EXPORT")

        # Escompte
        mentions["early_payment"] = "Aucun escompte pour paiement anticipé"

        return mentions

    def _check_completeness(
        self,
        data: Dict[str, Any],
        context: DocumentContext
    ) -> List[str]:
        """Vérifie les champs manquants obligatoires."""
        required_fields = [
            "issue_date", "lines", "total_ht", "total_ttc"
        ]

        if context == DocumentContext.B2G:
            required_fields.extend(["buyer_siret", "service_code"])

        missing = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing.append(field)

        return missing

    def _calculate_confidence_score(
        self,
        suggestions: List[AutogenSuggestion]
    ) -> float:
        """Calcule le score de confiance global."""
        if not suggestions:
            return 100.0

        scores = {
            AutogenConfidence.HIGH: 100,
            AutogenConfidence.MEDIUM: 75,
            AutogenConfidence.LOW: 50,
            AutogenConfidence.MANUAL: 0
        }

        total = sum(scores[s.confidence] for s in suggestions)
        return total / len(suggestions)

    def _is_public_entity(self, party: PartyInfo) -> bool:
        """Détecte si le destinataire est une entité publique."""
        siret = party.get("siret") or ""
        name = (party.get("name") or "").lower()

        # SIRET commençant par 1 ou 2 → entité publique
        if siret and siret[0] in ("1", "2"):
            return True

        # Mots-clés dans le nom
        public_keywords = [
            "mairie", "commune", "département", "région", "préfecture",
            "ministère", "établissement public", "hôpital", "chu",
            "université", "école", "lycée", "collège", "trésor public"
        ]
        return any(kw in name for kw in public_keywords)

    def _validate_eu_vat_format(self, vat_number: str) -> bool:
        """Valide le format d'un numéro de TVA intra-communautaire."""
        if not vat_number or len(vat_number) < 4:
            return False

        # Format: 2 lettres pays + numéro
        country = vat_number[:2].upper()
        if country not in self.EU_COUNTRIES:
            return False

        # Validation basique du format
        patterns = {
            "FR": r"^FR[0-9A-Z]{2}[0-9]{9}$",
            "DE": r"^DE[0-9]{9}$",
            "ES": r"^ES[A-Z0-9][0-9]{7}[A-Z0-9]$",
            "IT": r"^IT[0-9]{11}$",
            "BE": r"^BE[0-9]{10}$",
        }

        pattern = patterns.get(country, r"^[A-Z]{2}[A-Z0-9]{2,12}$")
        return bool(re.match(pattern, vat_number.upper()))


# =============================================================================
# FACTORY
# =============================================================================

def get_autogen_service(tenant_id: str) -> EInvoiceAutogenService:
    """Factory pour le service d'auto-génération."""
    return EInvoiceAutogenService(tenant_id)
