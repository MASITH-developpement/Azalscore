"""
AZALS MODULE - Odoo Import - Mapper
====================================

Mapping des champs Odoo vers les modeles AZALSCORE.
Gere les transformations et conversions de donnees.
"""

import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

logger = logging.getLogger(__name__)


class OdooMapper:
    """
    Mappeur de champs Odoo vers AZALSCORE.

    Gere:
    - Mapping des champs simples
    - Transformations de valeurs
    - Resolution des relations (Many2one, etc.)
    - Valeurs par defaut
    """

    def __init__(
        self,
        custom_mappings: Optional[Dict[str, Dict[str, str]]] = None,
        countries_cache: Optional[Dict[int, str]] = None,
        categories_cache: Optional[Dict[int, str]] = None,
        uom_cache: Optional[Dict[int, str]] = None,
    ):
        """
        Initialise le mapper.

        Args:
            custom_mappings: Mappings personnalises par modele
            countries_cache: Cache {odoo_id: country_code}
            categories_cache: Cache {odoo_id: category_name}
            uom_cache: Cache {odoo_id: uom_name}
        """
        self.custom_mappings = custom_mappings or {}
        self.countries_cache = countries_cache or {}
        self.categories_cache = categories_cache or {}
        self.uom_cache = uom_cache or {}

    # =========================================================================
    # MAPPINGS PAR DEFAUT
    # =========================================================================

    DEFAULT_PRODUCT_MAPPING = {
        # Identification
        "name": "name",
        "default_code": "code",  # code produit interne
        "description": "description",
        "description_sale": "description",  # fallback

        # Codes
        "barcode": "barcode",

        # Prix
        "list_price": "sale_price",
        "standard_price": "standard_cost",

        # Flags
        "sale_ok": "is_sellable",
        "purchase_ok": "is_purchasable",
        "active": "is_active",

        # Dimensions
        "weight": "weight_kg",
        "volume": "volume_m3",

        # Type
        "type": "_type_transform",  # Necessite transformation
    }

    DEFAULT_CONTACT_MAPPING = {
        # Identification
        "name": "name",
        "ref": "code",

        # Contact
        "email": "email",
        "phone": "phone",
        "mobile": "mobile",
        "website": "website",

        # Adresse
        "street": "address_line1",
        "street2": "address_line2",
        "city": "city",
        "zip": "postal_code",
        "country_id": "_country_transform",

        # Informations legales
        "vat": "tax_id",

        # Type
        "is_company": "_entity_type_transform",

        # Flags
        "active": "is_active",
    }

    DEFAULT_SUPPLIER_MAPPING = {
        # Herite de contact + champs specifiques fournisseur
        **DEFAULT_CONTACT_MAPPING,
        "supplier_rank": "_supplier_rank_transform",
        "property_supplier_payment_term_id": "payment_term_days",
    }

    DEFAULT_PURCHASE_ORDER_MAPPING = {
        "name": "order_number",
        "date_order": "order_date",
        "partner_id": "supplier_id",
        "date_planned": "expected_date",
        "amount_total": "total_amount",
        "amount_untaxed": "subtotal_amount",
        "amount_tax": "tax_amount",
        "state": "status",
        "notes": "notes",
    }

    # =========================================================================
    # MAPPINGS COMPTABILITE
    # =========================================================================

    DEFAULT_ACCOUNT_MAPPING = {
        # Plan comptable (account.account)
        "code": "account_number",
        "name": "account_label",
        "account_type": "_account_type_transform",
    }

    DEFAULT_JOURNAL_MAPPING = {
        # Journaux comptables (account.journal)
        "code": "journal_code",
        "name": "journal_label",
        "type": "journal_type",
    }

    DEFAULT_MOVE_MAPPING = {
        # Ecritures comptables - en-tete (account.move)
        "name": "entry_number",
        "ref": "piece_number",
        "date": "entry_date",
        "journal_id": "_journal_transform",
        "state": "_move_state_transform",
    }

    DEFAULT_MOVE_LINE_MAPPING = {
        # Lignes d'ecritures (account.move.line)
        "account_id": "_account_line_transform",
        "name": "label",
        "debit": "debit",
        "credit": "credit",
        "date": "entry_date",
        "partner_id": "_partner_transform",
        "ref": "ref",
    }

    # =========================================================================
    # METHODES DE MAPPING
    # =========================================================================

    def get_mapping(self, odoo_model: str) -> Dict[str, str]:
        """
        Retourne le mapping pour un modele Odoo.

        Args:
            odoo_model: Nom du modele Odoo

        Returns:
            Dictionnaire de mapping {champ_odoo: champ_azals}
        """
        # Mapping personnalise en priorite
        if odoo_model in self.custom_mappings:
            return {**self._get_default_mapping(odoo_model), **self.custom_mappings[odoo_model]}
        return self._get_default_mapping(odoo_model)

    def _get_default_mapping(self, odoo_model: str) -> Dict[str, str]:
        """Retourne le mapping par defaut pour un modele."""
        mappings = {
            "product.product": self.DEFAULT_PRODUCT_MAPPING,
            "product.template": self.DEFAULT_PRODUCT_MAPPING,
            "res.partner": self.DEFAULT_CONTACT_MAPPING,
            "purchase.order": self.DEFAULT_PURCHASE_ORDER_MAPPING,
            "account.account": self.DEFAULT_ACCOUNT_MAPPING,
            "account.journal": self.DEFAULT_JOURNAL_MAPPING,
            "account.move": self.DEFAULT_MOVE_MAPPING,
            "account.move.line": self.DEFAULT_MOVE_LINE_MAPPING,
        }
        return mappings.get(odoo_model, {})

    def get_odoo_fields(self, odoo_model: str) -> List[str]:
        """
        Retourne la liste des champs Odoo a recuperer.

        Args:
            odoo_model: Nom du modele Odoo

        Returns:
            Liste des noms de champs
        """
        mapping = self.get_mapping(odoo_model)
        fields = list(mapping.keys())

        # Ajouter les champs techniques
        fields.extend(['id', 'write_date', 'create_date'])

        # Champs specifiques par modele
        if odoo_model in ('product.product', 'product.template'):
            fields.extend(['categ_id', 'uom_id', 'taxes_id', 'qty_available'])
        elif odoo_model == 'res.partner':
            fields.extend(['customer_rank', 'supplier_rank', 'company_type', 'parent_id'])
        elif odoo_model == 'purchase.order':
            fields.extend(['order_line', 'partner_id', 'currency_id'])
        elif odoo_model == 'account.account':
            fields.extend(['account_type', 'reconcile', 'deprecated'])
        elif odoo_model == 'account.journal':
            fields.extend(['type', 'default_account_id'])
        elif odoo_model == 'account.move':
            fields.extend(['move_type', 'currency_id', 'amount_total', 'line_ids', 'partner_id'])
        elif odoo_model == 'account.move.line':
            fields.extend(['move_id', 'currency_id', 'balance', 'amount_currency'])

        return list(set(fields))

    def map_record(
        self,
        odoo_model: str,
        odoo_record: Dict[str, Any],
        tenant_id: str,
    ) -> Dict[str, Any]:
        """
        Mappe un enregistrement Odoo vers AZALSCORE.

        Args:
            odoo_model: Nom du modele Odoo
            odoo_record: Donnees Odoo brutes
            tenant_id: ID du tenant

        Returns:
            Dictionnaire avec les donnees mappees pour AZALSCORE
        """
        mapping = self.get_mapping(odoo_model)
        result = {"tenant_id": tenant_id}

        for odoo_field, azals_field in mapping.items():
            value = odoo_record.get(odoo_field)

            # Ignorer les valeurs None ou False (Odoo utilise False pour null)
            if value is None or value is False:
                continue

            # Transformation speciale
            if azals_field.startswith("_") and azals_field.endswith("_transform"):
                transform_result = self._apply_transform(
                    azals_field, value, odoo_record, odoo_model
                )
                if transform_result:
                    result.update(transform_result)
            else:
                # Conversion simple
                result[azals_field] = self._convert_value(value, azals_field)

        # Ajouter les metadonnees Odoo
        result["_odoo_id"] = odoo_record.get("id")
        result["_odoo_model"] = odoo_model

        # Traitement specifique par modele
        if odoo_model in ("product.product", "product.template"):
            result = self._post_process_product(result, odoo_record)
        elif odoo_model == "res.partner":
            result = self._post_process_contact(result, odoo_record)

        return result

    def map_records(
        self,
        odoo_model: str,
        odoo_records: List[Dict[str, Any]],
        tenant_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Mappe plusieurs enregistrements Odoo.

        Args:
            odoo_model: Nom du modele Odoo
            odoo_records: Liste des donnees Odoo
            tenant_id: ID du tenant

        Returns:
            Liste des enregistrements mappes
        """
        return [
            self.map_record(odoo_model, record, tenant_id)
            for record in odoo_records
        ]

    # =========================================================================
    # TRANSFORMATIONS
    # =========================================================================

    def _apply_transform(
        self,
        transform_name: str,
        value: Any,
        record: Dict[str, Any],
        model: str,
    ) -> Optional[Dict[str, Any]]:
        """Applique une transformation speciale."""

        if transform_name == "_type_transform":
            return self._transform_product_type(value)

        elif transform_name == "_country_transform":
            return self._transform_country(value)

        elif transform_name == "_entity_type_transform":
            return self._transform_entity_type(value)

        elif transform_name == "_supplier_rank_transform":
            return self._transform_supplier_rank(value)

        elif transform_name == "_account_type_transform":
            return self._transform_account_type(value)

        elif transform_name == "_journal_transform":
            return self._transform_journal(value)

        elif transform_name == "_move_state_transform":
            return self._transform_move_state(value)

        elif transform_name == "_account_line_transform":
            return self._transform_account_line(value)

        elif transform_name == "_partner_transform":
            return self._transform_partner(value)

        return None

    def _transform_product_type(self, odoo_type: str) -> Dict[str, str]:
        """Transforme le type de produit Odoo vers AZALSCORE."""
        type_mapping = {
            "consu": "CONSUMABLE",
            "product": "STOCKABLE",
            "service": "SERVICE",
        }
        return {"type": type_mapping.get(odoo_type, "STOCKABLE")}

    def _transform_country(self, country_value: Any) -> Dict[str, str]:
        """Transforme l'ID pays Odoo vers un code pays."""
        if isinstance(country_value, (list, tuple)) and len(country_value) >= 2:
            # Format Odoo: [id, "Nom du pays"]
            country_id = country_value[0]
            if country_id in self.countries_cache:
                return {"country": self.countries_cache[country_id]}
            # Essayer d'extraire le code du nom
            country_name = country_value[1]
            return {"country": self._guess_country_code(country_name)}
        return {}

    def _transform_entity_type(self, is_company: bool) -> Dict[str, str]:
        """Transforme is_company vers entity_type."""
        return {"entity_type": "COMPANY" if is_company else "INDIVIDUAL"}

    def _transform_supplier_rank(self, rank: int) -> Dict[str, Any]:
        """Transforme supplier_rank en indicateur fournisseur."""
        return {"is_supplier": rank > 0}

    def _guess_country_code(self, country_name: str) -> str:
        """Devine le code pays a partir du nom."""
        common_countries = {
            "france": "FR",
            "belgique": "BE",
            "belgium": "BE",
            "suisse": "CH",
            "switzerland": "CH",
            "allemagne": "DE",
            "germany": "DE",
            "espagne": "ES",
            "spain": "ES",
            "italie": "IT",
            "italy": "IT",
            "royaume-uni": "GB",
            "united kingdom": "GB",
            "etats-unis": "US",
            "united states": "US",
            "canada": "CA",
            "luxembourg": "LU",
            "pays-bas": "NL",
            "netherlands": "NL",
            "portugal": "PT",
        }
        return common_countries.get(country_name.lower(), "FR")

    def _transform_account_type(self, odoo_type: str) -> Dict[str, str]:
        """Transforme le type de compte Odoo vers AZALSCORE AccountType."""
        # Mapping Odoo 17+ account_type vers AZALS AccountType
        type_mapping = {
            # Actifs
            "asset_receivable": "ASSET",
            "asset_cash": "ASSET",
            "asset_current": "ASSET",
            "asset_non_current": "ASSET",
            "asset_prepayments": "ASSET",
            "asset_fixed": "ASSET",
            # Passifs
            "liability_payable": "LIABILITY",
            "liability_credit_card": "LIABILITY",
            "liability_current": "LIABILITY",
            "liability_non_current": "LIABILITY",
            # Capitaux propres
            "equity": "EQUITY",
            "equity_unaffected": "EQUITY",
            # Produits
            "income": "REVENUE",
            "income_other": "REVENUE",
            # Charges
            "expense": "EXPENSE",
            "expense_depreciation": "EXPENSE",
            "expense_direct_cost": "EXPENSE",
            # Hors bilan
            "off_balance": "SPECIAL",
        }
        return {"account_type": type_mapping.get(odoo_type, "ASSET")}

    def _transform_journal(self, journal_value: Any) -> Dict[str, Any]:
        """Transforme l'ID journal Odoo vers code et libelle."""
        if isinstance(journal_value, (list, tuple)) and len(journal_value) >= 2:
            return {
                "_odoo_journal_id": journal_value[0],
                "journal_code": str(journal_value[0]),  # Temporaire, sera resolu
                "journal_label": journal_value[1],
            }
        return {}

    def _transform_move_state(self, state: str) -> Dict[str, str]:
        """Transforme l'etat Odoo vers AZALS EntryStatus."""
        state_mapping = {
            "draft": "DRAFT",
            "posted": "POSTED",
            "cancel": "CANCELLED",
        }
        return {"status": state_mapping.get(state, "DRAFT")}

    def _transform_account_line(self, account_value: Any) -> Dict[str, Any]:
        """Transforme l'ID compte Odoo vers numero et libelle."""
        if isinstance(account_value, (list, tuple)) and len(account_value) >= 2:
            return {
                "_odoo_account_id": account_value[0],
                "account_number": str(account_value[0]),  # Temporaire
                "account_label": account_value[1],
            }
        return {}

    def _transform_partner(self, partner_value: Any) -> Dict[str, Any]:
        """Transforme l'ID partenaire Odoo vers code auxiliaire."""
        if isinstance(partner_value, (list, tuple)) and len(partner_value) >= 2:
            return {
                "_odoo_partner_id": partner_value[0],
                "auxiliary_code": f"ODOO-{partner_value[0]}",
            }
        return {}

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def _convert_value(self, value: Any, field_name: str) -> Any:
        """Convertit une valeur Odoo vers le type AZALSCORE."""

        # Dates
        if isinstance(value, str) and self._looks_like_datetime(value):
            return self._parse_datetime(value)

        # Decimaux pour les champs prix/quantite
        decimal_fields = {
            "sale_price", "standard_cost", "average_cost", "unit_price",
            "cost_price", "weight_kg", "volume_m3", "quantity",
            "total_amount", "subtotal_amount", "tax_amount",
        }
        if field_name in decimal_fields:
            return self._to_decimal(value)

        # Many2one -> extraire l'ID ou le nom
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            # Format Odoo: [id, "Nom"]
            return value[0]  # Retourner l'ID

        # Booleens
        if isinstance(value, bool):
            return value

        return value

    def _looks_like_datetime(self, value: str) -> bool:
        """Verifie si une chaine ressemble a une date/datetime."""
        patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$',  # YYYY-MM-DD HH:MM:SS
        ]
        return any(re.match(p, value) for p in patterns)

    def _parse_datetime(self, value: str) -> datetime:
        """Parse une datetime Odoo."""
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return datetime.utcnow()

    def _to_decimal(self, value: Any) -> Decimal:
        """Convertit en Decimal."""
        if value is None or value is False:
            return Decimal("0")
        try:
            return Decimal(str(value))
        except Exception:
            return Decimal("0")

    # =========================================================================
    # POST-PROCESSING
    # =========================================================================

    def _post_process_product(
        self,
        mapped: Dict[str, Any],
        odoo_record: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Post-traitement pour les produits."""

        # Generer un code si absent
        if not mapped.get("code"):
            odoo_id = odoo_record.get("id", 0)
            mapped["code"] = f"ODOO-{odoo_id}"

        # SKU = code par defaut
        if not mapped.get("sku") and mapped.get("code"):
            mapped["sku"] = mapped["code"]

        # Categorie
        categ = odoo_record.get("categ_id")
        if isinstance(categ, (list, tuple)) and len(categ) >= 2:
            mapped["_odoo_category_id"] = categ[0]
            mapped["_odoo_category_name"] = categ[1]

        # Unite de mesure
        uom = odoo_record.get("uom_id")
        if isinstance(uom, (list, tuple)) and len(uom) >= 2:
            mapped["unit"] = self._normalize_uom(uom[1])

        # Statut
        if mapped.get("is_active", True):
            mapped["status"] = "ACTIVE"
        else:
            mapped["status"] = "DISCONTINUED"

        return mapped

    def _post_process_contact(
        self,
        mapped: Dict[str, Any],
        odoo_record: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Post-traitement pour les contacts."""

        # Determiner les types de relation
        relation_types = []
        customer_rank = odoo_record.get("customer_rank", 0)
        supplier_rank = odoo_record.get("supplier_rank", 0)

        if customer_rank > 0:
            relation_types.append("CUSTOMER")
        if supplier_rank > 0:
            relation_types.append("SUPPLIER")
        if not relation_types:
            relation_types.append("PROSPECT")

        mapped["relation_types"] = relation_types

        # Generer un code si absent
        if not mapped.get("code"):
            odoo_id = odoo_record.get("id", 0)
            prefix = "FOUR" if "SUPPLIER" in relation_types else "CLI"
            mapped["code"] = f"{prefix}-ODOO-{odoo_id}"

        # Nom legal = nom si societe
        if mapped.get("entity_type") == "COMPANY" and not mapped.get("legal_name"):
            mapped["legal_name"] = mapped.get("name")

        return mapped

    def _normalize_uom(self, uom_name: str) -> str:
        """Normalise le nom d'unite de mesure."""
        uom_mapping = {
            "unit(s)": "UNIT",
            "units": "UNIT",
            "unit": "UNIT",
            "piece": "UNIT",
            "pieces": "UNIT",
            "pcs": "UNIT",
            "kg": "KG",
            "kilogram": "KG",
            "g": "G",
            "gram": "G",
            "l": "L",
            "liter": "L",
            "litre": "L",
            "m": "M",
            "meter": "M",
            "metre": "M",
            "cm": "CM",
            "mm": "MM",
            "m2": "M2",
            "m3": "M3",
            "hour": "H",
            "hours": "H",
            "day": "DAY",
            "days": "DAY",
        }
        normalized = uom_name.lower().strip()
        return uom_mapping.get(normalized, "UNIT")

    # =========================================================================
    # DETECTION DE DOUBLONS
    # =========================================================================

    def get_duplicate_key(self, odoo_model: str, mapped_record: Dict[str, Any]) -> Tuple[str, Any]:
        """
        Retourne la cle de deduplication pour un enregistrement.

        Args:
            odoo_model: Modele Odoo
            mapped_record: Enregistrement mappe

        Returns:
            Tuple (nom_champ, valeur) pour rechercher les doublons
        """
        if odoo_model in ("product.product", "product.template"):
            # Deduplication par code ou barcode
            if mapped_record.get("code"):
                return ("code", mapped_record["code"])
            if mapped_record.get("barcode"):
                return ("barcode", mapped_record["barcode"])
            if mapped_record.get("sku"):
                return ("sku", mapped_record["sku"])

        elif odoo_model == "res.partner":
            # Deduplication par email ou tax_id (SIRET/TVA)
            if mapped_record.get("email"):
                return ("email", mapped_record["email"])
            if mapped_record.get("tax_id"):
                return ("tax_id", mapped_record["tax_id"])
            if mapped_record.get("registration_number"):
                return ("registration_number", mapped_record["registration_number"])

        # Fallback: pas de deduplication (creation systematique)
        return (None, None)
