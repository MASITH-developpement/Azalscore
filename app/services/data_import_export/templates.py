"""
AZALSCORE - Data Import/Export Templates
Templates d'import prédéfinis
"""
from __future__ import annotations

from .types import ImportFormat, ImportTemplate, FieldMapping


def get_fec_import_template() -> ImportTemplate:
    """Template d'import FEC"""
    return ImportTemplate(
        id="fec_import",
        name="Import FEC",
        description="Import du Fichier des Écritures Comptables (format légal)",
        format=ImportFormat.FEC,
        target_entity="accounting_entry",
        field_mappings=[
            FieldMapping(
                source_field="JournalCode",
                target_field="journal_code",
                data_type="string",
                required=True,
                validation_rules=[{"type": "length", "min": 1, "max": 10}]
            ),
            FieldMapping(
                source_field="JournalLib",
                target_field="journal_label",
                data_type="string",
                required=True
            ),
            FieldMapping(
                source_field="EcritureNum",
                target_field="entry_number",
                data_type="string",
                required=True
            ),
            FieldMapping(
                source_field="EcritureDate",
                target_field="entry_date",
                data_type="date",
                required=True,
                transformations=[{
                    "type": "date_format",
                    "input_format": "%Y%m%d",
                    "output_format": "%Y-%m-%d"
                }]
            ),
            FieldMapping(
                source_field="CompteNum",
                target_field="account_number",
                data_type="string",
                required=True
            ),
            FieldMapping(
                source_field="CompteLib",
                target_field="account_label",
                data_type="string",
                required=True
            ),
            FieldMapping(
                source_field="CompAuxNum",
                target_field="auxiliary_account",
                data_type="string"
            ),
            FieldMapping(
                source_field="CompAuxLib",
                target_field="auxiliary_label",
                data_type="string"
            ),
            FieldMapping(
                source_field="PieceRef",
                target_field="document_reference",
                data_type="string"
            ),
            FieldMapping(
                source_field="PieceDate",
                target_field="document_date",
                data_type="date",
                transformations=[{
                    "type": "date_format",
                    "input_format": "%Y%m%d",
                    "output_format": "%Y-%m-%d"
                }]
            ),
            FieldMapping(
                source_field="EcritureLib",
                target_field="entry_label",
                data_type="string"
            ),
            FieldMapping(
                source_field="Debit",
                target_field="debit",
                data_type="decimal",
                required=True,
                transformations=[{
                    "type": "number_format",
                    "input_decimal": ",",
                    "output_decimal": "."
                }]
            ),
            FieldMapping(
                source_field="Credit",
                target_field="credit",
                data_type="decimal",
                required=True,
                transformations=[{
                    "type": "number_format",
                    "input_decimal": ",",
                    "output_decimal": "."
                }]
            ),
            FieldMapping(
                source_field="EcritureLet",
                target_field="lettering",
                data_type="string"
            ),
            FieldMapping(
                source_field="DateLet",
                target_field="lettering_date",
                data_type="date",
                transformations=[{
                    "type": "date_format",
                    "input_format": "%Y%m%d",
                    "output_format": "%Y-%m-%d"
                }]
            ),
            FieldMapping(
                source_field="ValidDate",
                target_field="validation_date",
                data_type="date",
                transformations=[{
                    "type": "date_format",
                    "input_format": "%Y%m%d",
                    "output_format": "%Y-%m-%d"
                }]
            ),
            FieldMapping(
                source_field="Montantdevise",
                target_field="currency_amount",
                data_type="decimal",
                transformations=[{
                    "type": "number_format",
                    "input_decimal": ",",
                    "output_decimal": "."
                }]
            ),
            FieldMapping(
                source_field="Idevise",
                target_field="currency_code",
                data_type="string"
            ),
        ],
        options={
            "delimiter": "\t",
            "encoding": "utf-8"
        }
    )


def get_client_import_template() -> ImportTemplate:
    """Template d'import clients"""
    return ImportTemplate(
        id="client_import",
        name="Import Clients",
        description="Import de la base clients (CSV/Excel)",
        format=ImportFormat.CSV,
        target_entity="client",
        field_mappings=[
            FieldMapping(
                source_field="code_client",
                target_field="client_code",
                data_type="string",
                required=True,
                transformations=[{"type": "uppercase"}, {"type": "trim"}]
            ),
            FieldMapping(
                source_field="raison_sociale",
                target_field="company_name",
                data_type="string",
                required=True,
                transformations=[{"type": "trim"}]
            ),
            FieldMapping(
                source_field="siren",
                target_field="siren",
                data_type="siren",
                validation_rules=[{"type": "length", "min": 9, "max": 9}]
            ),
            FieldMapping(
                source_field="siret",
                target_field="siret",
                data_type="siret",
                validation_rules=[{"type": "length", "min": 14, "max": 14}]
            ),
            FieldMapping(
                source_field="tva_intra",
                target_field="vat_number",
                data_type="string",
                transformations=[{"type": "uppercase"}]
            ),
            FieldMapping(
                source_field="adresse",
                target_field="address_line1",
                data_type="string"
            ),
            FieldMapping(
                source_field="code_postal",
                target_field="postal_code",
                data_type="string"
            ),
            FieldMapping(
                source_field="ville",
                target_field="city",
                data_type="string",
                transformations=[{"type": "uppercase"}]
            ),
            FieldMapping(
                source_field="pays",
                target_field="country",
                data_type="string",
                default_value="FR"
            ),
            FieldMapping(
                source_field="telephone",
                target_field="phone",
                data_type="string"
            ),
            FieldMapping(
                source_field="email",
                target_field="email",
                data_type="email"
            ),
            FieldMapping(
                source_field="iban",
                target_field="iban",
                data_type="iban"
            ),
            FieldMapping(
                source_field="conditions_paiement",
                target_field="payment_terms_days",
                data_type="integer",
                default_value=30
            ),
        ],
        options={
            "delimiter": ";",
            "encoding": "utf-8",
            "has_header": True
        }
    )


def get_invoice_import_template() -> ImportTemplate:
    """Template d'import factures"""
    return ImportTemplate(
        id="invoice_import",
        name="Import Factures",
        description="Import des factures fournisseurs/clients",
        format=ImportFormat.CSV,
        target_entity="invoice",
        field_mappings=[
            FieldMapping(
                source_field="numero_facture",
                target_field="invoice_number",
                data_type="string",
                required=True
            ),
            FieldMapping(
                source_field="date_facture",
                target_field="invoice_date",
                data_type="date",
                required=True
            ),
            FieldMapping(
                source_field="date_echeance",
                target_field="due_date",
                data_type="date"
            ),
            FieldMapping(
                source_field="code_tiers",
                target_field="partner_code",
                data_type="string",
                required=True
            ),
            FieldMapping(
                source_field="type",
                target_field="invoice_type",
                data_type="string",
                required=True,
                validation_rules=[{
                    "type": "enum",
                    "values": ["FA", "AV", "FC", "AC"]
                }],
                transformations=[{
                    "type": "lookup",
                    "table": {"FA": "invoice", "AV": "credit_note", "FC": "supplier_invoice", "AC": "supplier_credit"}
                }]
            ),
            FieldMapping(
                source_field="montant_ht",
                target_field="amount_untaxed",
                data_type="decimal",
                required=True,
                transformations=[{
                    "type": "number_format",
                    "input_decimal": ","
                }]
            ),
            FieldMapping(
                source_field="montant_tva",
                target_field="tax_amount",
                data_type="decimal",
                transformations=[{
                    "type": "number_format",
                    "input_decimal": ","
                }]
            ),
            FieldMapping(
                source_field="montant_ttc",
                target_field="amount_total",
                data_type="decimal",
                required=True,
                transformations=[{
                    "type": "number_format",
                    "input_decimal": ","
                }]
            ),
            FieldMapping(
                source_field="devise",
                target_field="currency",
                data_type="string",
                default_value="EUR"
            ),
            FieldMapping(
                source_field="reference",
                target_field="reference",
                data_type="string"
            ),
        ],
        options={
            "delimiter": ";",
            "encoding": "utf-8",
            "has_header": True
        }
    )
