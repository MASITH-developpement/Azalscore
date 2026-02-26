"""
AZALSCORE - FEC Exporter
Exporter FEC (Fichier des Écritures Comptables)
"""
from __future__ import annotations

import io
from datetime import datetime, date
from decimal import Decimal

from .base import BaseExporter


class FECExporter(BaseExporter):
    """Exporter FEC (Fichier des Écritures Comptables)"""

    FEC_COLUMNS = [
        "JournalCode", "JournalLib", "EcritureNum", "EcritureDate",
        "CompteNum", "CompteLib", "CompAuxNum", "CompAuxLib",
        "PieceRef", "PieceDate", "EcritureLib", "Debit", "Credit",
        "EcritureLet", "DateLet", "ValidDate", "Montantdevise", "Idevise"
    ]

    def export(self, data: list[dict], options: dict) -> bytes:
        encoding = options.get("encoding", "iso-8859-1")
        delimiter = "\t"
        siren = options.get("siren", "")
        fiscal_year_end = options.get("fiscal_year_end", "")

        if siren and fiscal_year_end:
            filename = f"{siren}FEC{fiscal_year_end}"
        else:
            filename = "FEC"

        output = io.StringIO()

        output.write(delimiter.join(self.FEC_COLUMNS) + "\n")

        for record in data:
            row = []
            for col in self.FEC_COLUMNS:
                value = record.get(col, "")

                if col in ("EcritureDate", "PieceDate", "DateLet", "ValidDate"):
                    if isinstance(value, (date, datetime)):
                        value = value.strftime("%Y%m%d")
                    elif value and isinstance(value, str):
                        for fmt in ["%Y-%m-%d", "%d/%m/%Y"]:
                            try:
                                value = datetime.strptime(value, fmt).strftime("%Y%m%d")
                                break
                            except ValueError:
                                continue

                if col in ("Debit", "Credit", "Montantdevise"):
                    if isinstance(value, (int, float, Decimal)):
                        value = f"{Decimal(str(value)):.2f}".replace(".", ",")
                    elif not value:
                        value = "0,00"

                row.append(str(value) if value is not None else "")

            output.write(delimiter.join(row) + "\n")

        return output.getvalue().encode(encoding)
